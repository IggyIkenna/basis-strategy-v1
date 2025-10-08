"""
Data Availability Tracking System

Tracks what data has been downloaded for each date/time period to enable:
- Incremental downloads (avoid re-downloading existing data)
- Rate limit recovery (resume from where we left off)
- Data completeness monitoring
- Gap identification and filling

Creates manifest files that log data availability by date/time.
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import logging


class DataManifest:
    """
    Tracks data availability for a specific data source and time period.
    
    Features:
    - Logs available vs missing date/time periods
    - Enables incremental downloads
    - Provides gap analysis
    - Handles rate limit recovery
    """
    
    def __init__(self, data_source: str, asset: str, granularity: str, data_dir: str = "data"):
        self.data_source = data_source  # e.g., "coingecko_spot", "aavescan", "bybit_futures"
        self.asset = asset              # e.g., "ETH", "WETH", "ETHUSDT"
        self.granularity = granularity  # e.g., "1h", "1d", "1m", "8h"
        self.data_dir = Path(data_dir)
        
        # Create manifest directory
        self.manifest_dir = self.data_dir / "manifests"
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        
        # Manifest file path
        self.manifest_file = self.manifest_dir / f"{data_source}_{asset}_{granularity}_manifest.json"
        
        # Set up logging
        self.logger = logging.getLogger(f"manifest.{data_source}.{asset}")
        
        # Load existing manifest
        self.manifest_data = self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        """Load existing manifest or create new one."""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load manifest {self.manifest_file}: {e}")
        
        # Create new manifest
        return {
            'data_source': self.data_source,
            'asset': self.asset,
            'granularity': self.granularity,
            'created': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'available_periods': {},  # date -> {'status': 'available'|'missing', 'records': count, 'file': path}
            'download_attempts': [],  # List of download attempt records
            'metadata': {
                'total_periods_tracked': 0,
                'available_periods': 0,
                'missing_periods': 0,
                'last_gap_analysis': None
            }
        }
    
    def _save_manifest(self):
        """Save manifest to file."""
        self.manifest_data['last_updated'] = datetime.now().isoformat()
        
        try:
            with open(self.manifest_file, 'w') as f:
                json.dump(self.manifest_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save manifest: {e}")
    
    def log_download_attempt(self, start_date: str, end_date: str, success: bool, 
                           records_downloaded: int = 0, error: str = None):
        """
        Log a download attempt.
        
        Args:
            start_date: Start date of download attempt
            end_date: End date of download attempt
            success: Whether download succeeded
            records_downloaded: Number of records downloaded
            error: Error message if failed
        """
        attempt = {
            'timestamp': datetime.now().isoformat(),
            'start_date': start_date,
            'end_date': end_date,
            'success': success,
            'records_downloaded': records_downloaded,
            'error': error
        }
        
        self.manifest_data['download_attempts'].append(attempt)
        self._save_manifest()
        
        self.logger.info(f"Logged download attempt: {start_date} to {end_date} - {'SUCCESS' if success else 'FAILED'}")
    
    def mark_period_available(self, date_str: str, records: int, file_path: str):
        """
        Mark a specific date/time period as having data available.
        
        Args:
            date_str: Date string (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            records: Number of records for this period
            file_path: Path to file containing the data
        """
        self.manifest_data['available_periods'][date_str] = {
            'status': 'available',
            'records': records,
            'file': str(file_path),
            'logged_at': datetime.now().isoformat()
        }
        
        self._update_metadata()
        self._save_manifest()
    
    def mark_period_missing(self, date_str: str, reason: str = "No data available"):
        """
        Mark a specific date/time period as missing data.
        
        Args:
            date_str: Date string
            reason: Reason why data is missing
        """
        self.manifest_data['available_periods'][date_str] = {
            'status': 'missing',
            'reason': reason,
            'logged_at': datetime.now().isoformat()
        }
        
        self._update_metadata()
        self._save_manifest()
    
    def get_missing_periods(self, start_date: str, end_date: str) -> List[Tuple[str, str]]:
        """
        Get list of missing date periods within a range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of (start, end) tuples for missing periods
        """
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        # Generate expected periods based on granularity
        if self.granularity == '1h':
            expected_periods = pd.date_range(start=start_dt, end=end_dt, freq='H')
        elif self.granularity == '1d':
            expected_periods = pd.date_range(start=start_dt, end=end_dt, freq='D')
        elif self.granularity == '1m':
            expected_periods = pd.date_range(start=start_dt, end=end_dt, freq='T')
        elif self.granularity == '8h':
            expected_periods = pd.date_range(start=start_dt, end=end_dt, freq='8H')
        else:
            expected_periods = pd.date_range(start=start_dt, end=end_dt, freq='D')
        
        missing_periods = []
        current_missing_start = None
        
        for period in expected_periods:
            period_str = period.strftime('%Y-%m-%d %H:%M:%S') if self.granularity in ['1h', '1m', '8h'] else period.strftime('%Y-%m-%d')
            
            is_available = (
                period_str in self.manifest_data['available_periods'] and 
                self.manifest_data['available_periods'][period_str]['status'] == 'available'
            )
            
            if not is_available:
                if current_missing_start is None:
                    current_missing_start = period
            else:
                if current_missing_start is not None:
                    # End of missing period
                    missing_periods.append((
                        current_missing_start.strftime('%Y-%m-%d'),
                        (period - timedelta(days=1)).strftime('%Y-%m-%d')
                    ))
                    current_missing_start = None
        
        # Handle case where missing period extends to the end
        if current_missing_start is not None:
            missing_periods.append((
                current_missing_start.strftime('%Y-%m-%d'),
                end_dt.strftime('%Y-%m-%d')
            ))
        
        return missing_periods
    
    def analyze_from_csv_file(self, csv_file_path: str, timestamp_column: str = 'timestamp'):
        """
        Analyze an existing CSV file and update manifest with available periods.
        
        Args:
            csv_file_path: Path to CSV file
            timestamp_column: Name of timestamp column
        """
        try:
            df = pd.read_csv(csv_file_path)
            
            if timestamp_column not in df.columns:
                self.logger.error(f"Timestamp column '{timestamp_column}' not found in {csv_file_path}")
                return
            
            df[timestamp_column] = pd.to_datetime(df[timestamp_column])
            
            # Group by date (or hour, depending on granularity)
            if self.granularity == '1h':
                df['period'] = df[timestamp_column].dt.strftime('%Y-%m-%d %H:00:00')
            elif self.granularity == '1d':
                df['period'] = df[timestamp_column].dt.strftime('%Y-%m-%d')
            elif self.granularity == '1m':
                df['period'] = df[timestamp_column].dt.strftime('%Y-%m-%d %H:%M:00')
            else:
                df['period'] = df[timestamp_column].dt.strftime('%Y-%m-%d')
            
            # Count records per period
            period_counts = df['period'].value_counts()
            
            # Mark all periods as available
            for period, count in period_counts.items():
                self.mark_period_available(period, count, csv_file_path)
            
            self.logger.info(f"Analyzed {csv_file_path}: {len(period_counts)} periods marked as available")
            
        except Exception as e:
            self.logger.error(f"Failed to analyze CSV file {csv_file_path}: {e}")
    
    def _update_metadata(self):
        """Update manifest metadata."""
        available_count = sum(1 for p in self.manifest_data['available_periods'].values() if p['status'] == 'available')
        missing_count = sum(1 for p in self.manifest_data['available_periods'].values() if p['status'] == 'missing')
        
        self.manifest_data['metadata'].update({
            'total_periods_tracked': len(self.manifest_data['available_periods']),
            'available_periods': available_count,
            'missing_periods': missing_count,
            'last_gap_analysis': datetime.now().isoformat()
        })
    
    def get_coverage_report(self, start_date: str, end_date: str) -> Dict:
        """
        Generate coverage report for a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Coverage report dictionary
        """
        missing_periods = self.get_missing_periods(start_date, end_date)
        
        # Calculate total expected periods
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        if self.granularity == '1h':
            total_expected = int((end_dt - start_dt).total_seconds() / 3600)
        elif self.granularity == '1d':
            total_expected = (end_dt - start_dt).days
        elif self.granularity == '1m':
            total_expected = int((end_dt - start_dt).total_seconds() / 60)
        elif self.granularity == '8h':
            total_expected = int((end_dt - start_dt).total_seconds() / (8 * 3600))
        else:
            total_expected = (end_dt - start_dt).days
        
        available_periods = self.manifest_data['metadata']['available_periods']
        missing_periods_count = len(missing_periods)
        coverage_pct = (available_periods / total_expected) * 100 if total_expected > 0 else 0
        
        return {
            'data_source': self.data_source,
            'asset': self.asset,
            'granularity': self.granularity,
            'date_range': f"{start_date} to {end_date}",
            'total_expected_periods': total_expected,
            'available_periods': available_periods,
            'missing_periods_count': missing_periods_count,
            'coverage_percentage': coverage_pct,
            'missing_period_ranges': missing_periods,
            'last_updated': self.manifest_data['last_updated']
        }


class DataManifestManager:
    """
    Manages multiple data manifests across different sources and assets.
    
    Provides:
    - Centralized manifest management
    - Cross-source gap analysis
    - Incremental download coordination
    - Rate limit recovery
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.manifest_dir = self.data_dir / "manifests"
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        
        self.manifests = {}  # Cache of loaded manifests
        
        # Set up logging
        self.logger = logging.getLogger("manifest_manager")
        
        self.logger.info(f"DataManifestManager initialized: {self.manifest_dir}")
    
    def get_manifest(self, data_source: str, asset: str, granularity: str) -> DataManifest:
        """Get or create a manifest for a specific data source/asset combination."""
        key = f"{data_source}_{asset}_{granularity}"
        
        if key not in self.manifests:
            self.manifests[key] = DataManifest(data_source, asset, granularity, str(self.data_dir))
        
        return self.manifests[key]
    
    def analyze_existing_data_files(self, data_patterns: List[Dict]):
        """
        Analyze existing data files and update manifests.
        
        Args:
            data_patterns: List of dicts with 'pattern', 'data_source', 'asset', 'granularity', 'timestamp_column'
        """
        self.logger.info("🔍 Analyzing existing data files...")
        
        for pattern_config in data_patterns:
            pattern = pattern_config['pattern']
            data_source = pattern_config['data_source']
            asset = pattern_config['asset']
            granularity = pattern_config['granularity']
            timestamp_col = pattern_config.get('timestamp_column', 'timestamp')
            
            # Find matching files
            matching_files = list(self.data_dir.glob(pattern))
            
            for file_path in matching_files:
                if file_path.is_file() and file_path.suffix == '.csv':
                    manifest = self.get_manifest(data_source, asset, granularity)
                    manifest.analyze_from_csv_file(str(file_path), timestamp_col)
                    
                    self.logger.info(f"✅ Analyzed {file_path.name}")
    
    def get_incremental_download_plan(self, data_source: str, asset: str, granularity: str,
                                    start_date: str, end_date: str) -> List[Tuple[str, str]]:
        """
        Get list of date ranges that need to be downloaded.
        
        Args:
            data_source: Data source identifier
            asset: Asset identifier  
            granularity: Time granularity
            start_date: Requested start date
            end_date: Requested end date
            
        Returns:
            List of (start_date, end_date) tuples for missing periods
        """
        manifest = self.get_manifest(data_source, asset, granularity)
        missing_periods = manifest.get_missing_periods(start_date, end_date)
        
        if missing_periods:
            self.logger.info(f"📋 {data_source}/{asset}: {len(missing_periods)} missing periods to download")
            for start, end in missing_periods:
                self.logger.info(f"   📅 Missing: {start} to {end}")
        else:
            self.logger.info(f"✅ {data_source}/{asset}: No missing periods - data complete")
        
        return missing_periods
    
    def generate_comprehensive_report(self, start_date: str, end_date: str) -> Dict:
        """
        Generate comprehensive data availability report across all tracked sources.
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            Comprehensive coverage report
        """
        report = {
            'analysis_period': f"{start_date} to {end_date}",
            'generated_at': datetime.now().isoformat(),
            'sources': {},
            'summary': {
                'total_sources': 0,
                'fully_complete_sources': 0,
                'partially_complete_sources': 0,
                'missing_sources': 0,
                'overall_coverage_pct': 0.0
            }
        }
        
        total_coverage = 0
        source_count = 0
        
        for manifest in self.manifests.values():
            coverage_report = manifest.get_coverage_report(start_date, end_date)
            
            source_key = f"{coverage_report['data_source']}_{coverage_report['asset']}"
            report['sources'][source_key] = coverage_report
            
            coverage_pct = coverage_report['coverage_percentage']
            total_coverage += coverage_pct
            source_count += 1
            
            # Categorize completeness
            if coverage_pct >= 99:
                report['summary']['fully_complete_sources'] += 1
            elif coverage_pct >= 50:
                report['summary']['partially_complete_sources'] += 1
            else:
                report['summary']['missing_sources'] += 1
        
        report['summary']['total_sources'] = source_count
        report['summary']['overall_coverage_pct'] = total_coverage / source_count if source_count > 0 else 0
        
        return report
    
    def save_comprehensive_report(self, start_date: str, end_date: str, filename: str = None) -> Path:
        """Save comprehensive report to file."""
        if filename is None:
            filename = f"data_coverage_report_{start_date}_{end_date}.json"
        
        report = self.generate_comprehensive_report(start_date, end_date)
        report_path = self.manifest_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"💾 Comprehensive report saved: {report_path}")
        return report_path


class RateLimitRecoveryHandler:
    """
    Handles rate limit recovery by saving progress and resuming downloads.
    """
    
    def __init__(self, data_source: str, data_dir: str = "data"):
        self.data_source = data_source
        self.data_dir = Path(data_dir)
        self.recovery_dir = self.data_dir / "recovery"
        self.recovery_dir.mkdir(parents=True, exist_ok=True)
        
        self.recovery_file = self.recovery_dir / f"{data_source}_recovery_state.json"
        
        self.logger = logging.getLogger(f"recovery.{data_source}")
    
    def save_progress(self, current_asset: str, current_date: str, remaining_dates: List[str]):
        """Save current download progress for recovery."""
        state = {
            'data_source': self.data_source,
            'saved_at': datetime.now().isoformat(),
            'current_asset': current_asset,
            'current_date': current_date,
            'remaining_dates': remaining_dates,
            'recovery_reason': 'rate_limit_hit'
        }
        
        with open(self.recovery_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        self.logger.info(f"💾 Progress saved for recovery: {current_asset} at {current_date}")
    
    def load_recovery_state(self) -> Optional[Dict]:
        """Load saved recovery state."""
        if self.recovery_file.exists():
            try:
                with open(self.recovery_file, 'r') as f:
                    state = json.load(f)
                self.logger.info(f"🔄 Recovery state loaded: {state['current_asset']} at {state['current_date']}")
                return state
            except Exception as e:
                self.logger.error(f"Failed to load recovery state: {e}")
        
        return None
    
    def clear_recovery_state(self):
        """Clear recovery state after successful completion."""
        if self.recovery_file.exists():
            self.recovery_file.unlink()
            self.logger.info("✅ Recovery state cleared - download completed")


def create_data_patterns_config() -> List[Dict]:
    """
    Create configuration for analyzing existing data files.
    
    Returns:
        List of data pattern configurations
    """
    return [
        # Market data patterns
        {
            'pattern': 'market*/spot/*USDT_spot_1h_*.csv',
            'data_source': 'coingecko_spot',
            'asset': 'ETH',  # Will be extracted from filename
            'granularity': '1h',
            'timestamp_column': 'timestamp'
        },
        {
            'pattern': 'market*/futures/*USDT_futures_1m_*.csv',
            'data_source': 'bybit_futures',
            'asset': 'ETH',  # Will be extracted from filename
            'granularity': '1m',
            'timestamp_column': 'timestamp'
        },
        {
            'pattern': 'market*/futures/*_funding_rates_*.csv',
            'data_source': 'bybit_funding',
            'asset': 'ETH',  # Will be extracted from filename
            'granularity': '8h',
            'timestamp_column': 'funding_timestamp'
        },
        # AAVE data patterns
        {
            'pattern': 'lending*/aave_v3_*_WETH_rates_*.csv',
            'data_source': 'aavescan',
            'asset': 'WETH',
            'granularity': '1d',
            'timestamp_column': 'targetDate'
        },
        {
            'pattern': 'lending*/aave_v3_*_wstETH_rates_*.csv',
            'data_source': 'aavescan',
            'asset': 'wstETH',
            'granularity': '1d',
            'timestamp_column': 'targetDate'
        },
        # Gas data patterns
        {
            'pattern': 'gas*/ethereum_gas_prices_*.csv',
            'data_source': 'alchemy_gas',
            'asset': 'ETH',
            'granularity': '1h',
            'timestamp_column': 'timestamp'
        },
        # Restaking data patterns
        {
            'pattern': 'restaking*/eeth_base_apy_*.csv',
            'data_source': 'etherfi_restaking',
            'asset': 'eETH',
            'granularity': '1d',
            'timestamp_column': 'date'
        }
    ]


def main():
    """
    Main function for standalone manifest analysis.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze data availability and create manifests")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--start-date", type=str, default="2024-01-01", help="Analysis start date")
    parser.add_argument("--end-date", type=str, default="2025-09-18", help="Analysis end date")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        manager = DataManifestManager(args.data_dir)
        
        # Analyze existing data files
        patterns = create_data_patterns_config()
        manager.analyze_existing_data_files(patterns)
        
        # Generate comprehensive report
        report_path = manager.save_comprehensive_report(args.start_date, args.end_date)
        
        print(f"\n🎉 Data availability analysis complete!")
        print(f"📁 Manifests saved to: {manager.manifest_dir}")
        print(f"📊 Report saved to: {report_path}")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

