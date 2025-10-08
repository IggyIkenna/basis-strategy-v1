"""
AAVE Data Downloader - AaveScan Pro integration with hourly interpolation.

⚠️  IMPLEMENTATION STATUS: PLACEHOLDER - Waiting for AaveScan Pro API key
🔄 Ready for immediate integration once API key is available

Downloads and interpolates:
- Historical AAVE v3 lending/borrowing rates (daily → hourly interpolation)
- Reserve data (total supply/borrows for market impact modeling)
- Risk parameters (LTV, liquidation thresholds, caps) 
- Oracle pricing data (daily → hourly interpolation)
- Multi-chain support (Ethereum, Arbitrum, Optimism, Base)

🔄 HOURLY INTERPOLATION:
- Automatically interpolates all daily AAVE data to hourly granularity
- Uses linear interpolation for smooth backtesting data
- Creates separate hourly files with '_hourly' suffix
- Eliminates need for interpolation in downstream processors

Replaces old scripts:
- aave_market_analysis_vs_operational_assumptions.py
- simulate_aave_interest_rate.py (AAVE portions)
- Interpolation logic in process_peg_discount_data.py
"""

import asyncio
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List

# Add the backend source to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "backend" / "src"))

# Handle both standalone and module imports
try:
    from .clients.aavescan_client import AaveScanProClient
    from .base_downloader import BaseDownloader
except ImportError:
    # Standalone execution
    sys.path.append(str(Path(__file__).parent))
    from clients.aavescan_client import AaveScanProClient
    from base_downloader import BaseDownloader


class AAVEDataDownloader(BaseDownloader):
    """
    AAVE protocol data downloader using AaveScan Pro with automatic hourly interpolation.
    
    🔄 PLACEHOLDER STATUS:
    - Structure complete and ready for API key
    - Will download comprehensive AAVE v3 data across multiple chains
    - Optimized for 2024-2025 historical backfill
    - CSV output compatible with existing backtest engine
    
    🔄 HOURLY INTERPOLATION FEATURES:
    - Automatically interpolates daily AAVE data to hourly granularity
    - Linear interpolation for smooth backtesting data
    - Handles rates, oracle prices, and reserve data
    - Creates separate hourly files with '_hourly' suffix
    - Eliminates need for interpolation in downstream processors
    
    ⚠️  WAITING FOR: AaveScan Pro Advanced Plan API key
    """
    
    def __init__(self, output_dir: str = "data/protocol_data/aave"):
        super().__init__("aave_data", output_dir)
        
        # Create subdirectories
        self.rates_dir = Path(output_dir) / "rates"
        self.oracle_dir = Path(output_dir) / "oracle"
        self.reserves_dir = Path(output_dir) / "reserves"
        self.rates_dir.mkdir(parents=True, exist_ok=True)
        self.oracle_dir.mkdir(parents=True, exist_ok=True)
        # Note: reserves_dir not created since it's not populated with files
        
        # Initialize AaveScan Pro client
        try:
            self.aavescan_client = AaveScanProClient(str(self.rates_dir))
            
            if self.aavescan_client.placeholder_mode:
                self.logger.warning("🔄 AaveScan client in placeholder mode - API key needed")
            else:
                self.logger.info("✅ AaveScan Pro client initialized with API key")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize AaveScan client: {e}")
            raise RuntimeError("AaveScan Pro client initialization failed")
    
    def _interpolate_to_hourly(self, df: pd.DataFrame, timestamp_col: str = 'timestamp', 
                              numeric_cols: List[str] = None) -> pd.DataFrame:
        """
        Interpolate daily AAVE data to hourly granularity using linear interpolation.
        
        Args:
            df: DataFrame with daily data
            timestamp_col: Name of timestamp column
            numeric_cols: List of numeric columns to interpolate (if None, auto-detect)
            
        Returns:
            DataFrame with hourly interpolated data
        """
        if df.empty:
            return df
        
        # Convert timestamp to datetime if it's not already
        if df[timestamp_col].dtype == 'int64':
            df = df.copy()
            df[timestamp_col] = pd.to_datetime(df[timestamp_col], unit='s')
        
        # Auto-detect numeric columns if not provided
        if numeric_cols is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            # Remove timestamp column if it's numeric
            if timestamp_col in numeric_cols:
                numeric_cols.remove(timestamp_col)
        
        # Create hourly timestamp range
        start_time = df[timestamp_col].min()
        end_time = df[timestamp_col].max()
        hourly_range = pd.date_range(start=start_time, end=end_time, freq='H')
        
        # Create hourly DataFrame
        df_hourly = pd.DataFrame({timestamp_col: hourly_range})
        
        # Merge with original data
        df_hourly = df_hourly.merge(df, on=timestamp_col, how='left')
        
        # Interpolate numeric columns
        for col in numeric_cols:
            if col in df_hourly.columns:
                df_hourly[col] = df_hourly[col].interpolate(method='linear')
        
        # Add date column for convenience
        df_hourly['date'] = df_hourly[timestamp_col].dt.strftime('%Y-%m-%d')
        
        return df_hourly
    
    def _interpolate_rates_data(self, file_path: Path) -> Path:
        """
        Interpolate AAVE rates data to hourly granularity using proper mathematical approach.
        
        Implements the correct method:
        1. Interpolate indices (liquidityIndex, variableBorrowIndex) between 24-hour periods
        2. Calculate hourly APY from index ratios between consecutive hours
        3. Convert to continuously compounded APR using natural logs
        4. Keep current rates as snapshots (already continuously compounded)
        5. Linearly interpolate totalVariableDebt and totalAToken
        6. Drop unused columns (stable rates/debt)
        
        Args:
            file_path: Path to the rates CSV file
            
        Returns:
            Path to the interpolated file
        """
        self.logger.info(f"🔄 Properly interpolating rates data: {file_path.name}")
        
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Convert timestamps
        if 'targetDate' in df.columns:
            df['timestamp'] = pd.to_datetime(df['targetDate'])
        else:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Convert numeric columns
        numeric_cols = [
            'liquidityIndex', 'currentLiquidityRate', 'variableBorrowIndex', 
            'currentVariableBorrowRate', 'totalAToken', 'totalVariableDebt', 'price'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Step 1: Create hourly timestamp range
        start_time = df['timestamp'].min()
        end_time = df['timestamp'].max()
        hourly_range = pd.date_range(start=start_time, end=end_time, freq='H')
        
        # Step 2: Create hourly DataFrame with interpolated indices
        df_hourly = pd.DataFrame({'timestamp': hourly_range})
        
        # Merge with original data
        df_hourly = df_hourly.merge(df[['timestamp', 'liquidityIndex', 'variableBorrowIndex']], 
                                    on='timestamp', how='left')
        
        # Interpolate indices (these are cumulative, so linear interpolation is appropriate)
        df_hourly['liquidityIndex'] = df_hourly['liquidityIndex'].interpolate(method='linear')
        df_hourly['variableBorrowIndex'] = df_hourly['variableBorrowIndex'].interpolate(method='linear')
        
        # Step 3: Calculate hourly APY from index ratios
        df_hourly['liquidity_growth_factor'] = df_hourly['liquidityIndex'] / df_hourly['liquidityIndex'].shift(1)
        df_hourly['borrow_growth_factor'] = df_hourly['variableBorrowIndex'] / df_hourly['variableBorrowIndex'].shift(1)
        
        # Calculate hourly APY (annualized from 1-hour period)
        df_hourly['liquidity_apy_hourly'] = (df_hourly['liquidity_growth_factor'] ** (365 * 24)) - 1
        df_hourly['borrow_apy_hourly'] = (df_hourly['borrow_growth_factor'] ** (365 * 24)) - 1
        
        # Convert to continuously compounded APR
        df_hourly['liquidity_ccr_hourly'] = np.log(1 + df_hourly['liquidity_apy_hourly'])
        df_hourly['borrow_ccr_hourly'] = np.log(1 + df_hourly['borrow_apy_hourly'])
        
        # Step 4: Add current rates as snapshots
        df_hourly = df_hourly.merge(df[['timestamp', 'currentLiquidityRate', 'currentVariableBorrowRate']], 
                                    on='timestamp', how='left')
        
        # Forward fill current rates (they represent the rate at that point in time)
        df_hourly['currentLiquidityRate'] = df_hourly['currentLiquidityRate'].ffill()
        df_hourly['currentVariableBorrowRate'] = df_hourly['currentVariableBorrowRate'].ffill()
        
        # Step 5: Interpolate debt and supply amounts
        df_hourly = df_hourly.merge(df[['timestamp', 'totalAToken', 'totalVariableDebt']], 
                                    on='timestamp', how='left')
        
        # Linear interpolation for debt and supply amounts
        df_hourly['totalAToken'] = df_hourly['totalAToken'].interpolate(method='linear')
        df_hourly['totalVariableDebt'] = df_hourly['totalVariableDebt'].interpolate(method='linear')
        
        # Calculate utilization rate
        df_hourly['utilization_rate'] = df_hourly['totalVariableDebt'] / df_hourly['totalAToken']
        
        # Step 6: Add other useful columns
        df_hourly = df_hourly.merge(df[['timestamp', 'price']], on='timestamp', how='left')
        df_hourly['price'] = df_hourly['price'].interpolate(method='linear')
        df_hourly['oracle_price_usd'] = df_hourly['price']
        
        # Add metadata
        df_hourly['date'] = df_hourly['timestamp'].dt.strftime('%Y-%m-%d')
        df_hourly['hour'] = df_hourly['timestamp'].dt.hour
        df_hourly['source'] = 'aave_hourly_interpolated'
        
        # Step 7: Create clean output (drop unused columns)
        output_columns = [
            'timestamp', 'date', 'hour',
            'liquidityIndex', 'variableBorrowIndex',
            'liquidity_growth_factor', 'borrow_growth_factor',
            'liquidity_apy_hourly', 'borrow_apy_hourly',
            'liquidity_ccr_hourly', 'borrow_ccr_hourly',
            'currentLiquidityRate', 'currentVariableBorrowRate',
            'totalAToken', 'totalVariableDebt', 'utilization_rate',
            'oracle_price_usd', 'source'
        ]
        
        df_clean = df_hourly[output_columns].copy()
        
        # Remove first row (NaN values from growth factor calculation)
        df_clean = df_clean.iloc[1:].reset_index(drop=True)
        
        # Create output filename with hourly suffix
        output_path = file_path.parent / f"{file_path.stem}_hourly{file_path.suffix}"
        
        # Save interpolated data
        df_clean.to_csv(output_path, index=False)
        
        original_records = len(df)
        hourly_records = len(df_clean)
        
        self.logger.info(f"✅ Properly interpolated {original_records} daily → {hourly_records} hourly records")
        self.logger.info(f"   • Interpolated indices between 24-hour periods")
        self.logger.info(f"   • Calculated hourly APY from index ratios")
        self.logger.info(f"   • Converted to continuously compounded APR")
        self.logger.info(f"   • Kept current rates as snapshots")
        self.logger.info(f"   • Linearly interpolated debt/supply amounts")
        self.logger.info(f"   • Dropped unused stable rate/debt columns")
        
        return output_path
    
    def _interpolate_oracle_data(self, file_path: Path) -> Path:
        """
        Interpolate AAVE oracle data to hourly granularity.
        
        Args:
            file_path: Path to the oracle CSV file
            
        Returns:
            Path to the interpolated file
        """
        self.logger.info(f"🔄 Interpolating oracle data: {file_path.name}")
        
        # Read the CSV file, skipping header comments
        df = pd.read_csv(file_path, comment='#')
        
        # Define numeric columns to interpolate
        numeric_cols = ['oracle_price_eth']
        
        # Filter to only existing columns
        numeric_cols = [col for col in numeric_cols if col in df.columns]
        
        # Interpolate to hourly
        df_hourly = self._interpolate_to_hourly(df, 'timestamp', numeric_cols)
        
        # Create output filename with hourly suffix
        output_path = file_path.parent / f"{file_path.stem}_hourly{file_path.suffix}"
        
        # Save interpolated data with original header comments
        with open(file_path, 'r') as f:
            header_lines = []
            for line in f:
                if line.startswith('#'):
                    header_lines.append(line.rstrip())
                else:
                    break
        
        with open(output_path, 'w') as f:
            for line in header_lines:
                f.write(line + '\n')
            df_hourly.to_csv(f, index=False)
        
        original_records = len(df)
        hourly_records = len(df_hourly)
        
        self.logger.info(f"✅ Interpolated {original_records} daily → {hourly_records} hourly records")
        
        return output_path
    
    def _interpolate_reserves_data(self, file_path: Path) -> Path:
        """
        Interpolate AAVE reserves data to hourly granularity.
        
        Args:
            file_path: Path to the reserves CSV file
            
        Returns:
            Path to the interpolated file
        """
        self.logger.info(f"🔄 Interpolating reserves data: {file_path.name}")
        
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Define numeric columns to interpolate (reserve sizes and utilization)
        numeric_cols = [
            'totalLiquidity', 'totalBorrows', 'utilizationRate',
            'availableLiquidity', 'borrowCap', 'supplyCap'
        ]
        
        # Filter to only existing columns
        numeric_cols = [col for col in numeric_cols if col in df.columns]
        
        # Interpolate to hourly
        df_hourly = self._interpolate_to_hourly(df, 'timestamp', numeric_cols)
        
        # Create output filename with hourly suffix
        output_path = file_path.parent / f"{file_path.stem}_hourly{file_path.suffix}"
        
        # Save interpolated data
        df_hourly.to_csv(output_path, index=False)
        
        original_records = len(df)
        hourly_records = len(df_hourly)
        
        self.logger.info(f"✅ Interpolated {original_records} daily → {hourly_records} hourly records")
        
        return output_path
    
    def _apply_hourly_interpolation(self, download_result: Dict) -> Dict:
        """
        Apply hourly interpolation to all downloaded AAVE data files.
        
        Args:
            download_result: Result from AaveScan client download
            
        Returns:
            Updated result with interpolation information
        """
        if download_result.get('placeholder_mode'):
            self.logger.warning("🔄 Skipping interpolation in placeholder mode")
            return download_result
        
        self.logger.info("🔄 Applying hourly interpolation to AAVE data...")
        
        interpolated_files = []
        total_original_records = 0
        total_hourly_records = 0
        
        # Process each downloaded file
        for download in download_result.get('downloads', []):
            if not download.get('success'):
                continue
            
            file_path = Path(download['output_file'])
            
            if not file_path.exists():
                self.logger.warning(f"⚠️ File not found: {file_path}")
                continue
            
            try:
                # Determine file type and apply appropriate interpolation
                if 'rates' in file_path.name:
                    interpolated_path = self._interpolate_rates_data(file_path)
                elif 'oracle' in file_path.name:
                    interpolated_path = self._interpolate_oracle_data(file_path)
                elif 'reserves' in file_path.name:
                    interpolated_path = self._interpolate_reserves_data(file_path)
                else:
                    # Default to rates interpolation for unknown types
                    interpolated_path = self._interpolate_rates_data(file_path)
                
                # Count records
                original_df = pd.read_csv(file_path)
                hourly_df = pd.read_csv(interpolated_path)
                
                interpolated_files.append({
                    'original_file': str(file_path),
                    'interpolated_file': str(interpolated_path),
                    'original_records': len(original_df),
                    'hourly_records': len(hourly_df),
                    'interpolation_ratio': len(hourly_df) / len(original_df)
                })
                
                total_original_records += len(original_df)
                total_hourly_records += len(hourly_df)
                
            except Exception as e:
                self.logger.error(f"❌ Failed to interpolate {file_path}: {e}")
        
        # Update download result with interpolation info
        download_result['interpolation_applied'] = True
        download_result['interpolated_files'] = interpolated_files
        download_result['total_original_records'] = total_original_records
        download_result['total_hourly_records'] = total_hourly_records
        download_result['interpolation_ratio'] = total_hourly_records / total_original_records if total_original_records > 0 else 0
        
        self.logger.info("=" * 70)
        self.logger.info("🎯 HOURLY INTERPOLATION COMPLETE!")
        self.logger.info("=" * 70)
        self.logger.info(f"📊 Files interpolated: {len(interpolated_files)}")
        self.logger.info(f"📈 Records: {total_original_records:,} daily → {total_hourly_records:,} hourly")
        self.logger.info(f"🔄 Interpolation ratio: {download_result['interpolation_ratio']:.1f}x")
        self.logger.info("=" * 70)
        
        return download_result
    
    async def download_data(self, start_date: str, end_date: str) -> Dict:
        """
        Download all AAVE protocol data.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Download results
        """
        if self.aavescan_client.placeholder_mode:
            self.logger.warning("=" * 70)
            self.logger.warning("🔄 AAVE DATA DOWNLOADER - PLACEHOLDER MODE")
            self.logger.warning("⚠️  Waiting for AaveScan Pro Advanced Plan API key")
            self.logger.warning("📋 This will download:")
            self.logger.warning("   • Historical AAVE v3 rates (supply/borrow APR)")
            self.logger.warning("   • Reserve sizes (total supply/borrows)")
            self.logger.warning("   • Risk parameters (LTV/LT/Bonus with timestamps)")
            self.logger.warning("   • Multi-chain data (Ethereum, Arbitrum, Optimism, Base)")
            self.logger.warning("   • 2024-2025 complete historical coverage")
            self.logger.warning("=" * 70)
        
        self.logger.info("🚀 Starting AAVE data download")
        self.logger.info(f"📅 Date range: {start_date} to {end_date}")
        
        try:
            # Download all AAVE data via AaveScan Pro
            result = await self.aavescan_client.download_all_aave_data(start_date, end_date)
            
            # Apply hourly interpolation to all downloaded data
            result = self._apply_hourly_interpolation(result)
            
            # Log summary
            successful = result.get('successful_downloads', 0)
            total = result.get('total_downloads', 0)
            records = result.get('total_hourly_records', result.get('total_records', 0))
            
            if result.get('placeholder_mode'):
                self.logger.warning("=" * 70)
                self.logger.warning("🔄 AAVE DATA DOWNLOAD - PLACEHOLDER COMPLETE")
                self.logger.warning("=" * 70)
                self.logger.warning(f"📊 Placeholder files created: {successful}/{total}")
                self.logger.warning(f"📈 Placeholder records: {records}")
                self.logger.warning("🔑 Ready for AaveScan Pro API key integration")
                self.logger.warning("💾 Files saved with '_PLACEHOLDER' suffix")
                self.logger.warning("=" * 70)
            else:
                self.logger.info("=" * 70)
                self.logger.info("🎯 AAVE DATA DOWNLOAD COMPLETE!")
                self.logger.info("=" * 70)
                self.logger.info(f"✅ Successful downloads: {successful}/{total}")
                self.logger.info(f"📊 Total hourly records: {records:,}")
                if result.get('interpolation_applied'):
                    original_records = result.get('total_original_records', 0)
                    self.logger.info(f"📈 Interpolated from {original_records:,} daily records")
                self.logger.info(f"💾 Output directory: {self.output_dir}")
                self.logger.info("=" * 70)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ AAVE data download failed: {e}")
            
            # Return error result
            return {
                'timestamp': datetime.now().isoformat(),
                'downloader': 'aave_data',
                'success': False,
                'error': str(e),
                'total_downloads': 0,
                'successful_downloads': 0,
                'total_records': 0
            }


async def main():
    """
    Main execution function for standalone script usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Download AAVE protocol data from AaveScan Pro")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=str, default="data/protocol_data/aave", help="Output directory")
    
    args = parser.parse_args()
    
    try:
        downloader = AAVEDataDownloader(args.output_dir)
        
        # Use provided dates or config defaults
        if args.start_date and args.end_date:
            start_date, end_date = args.start_date, args.end_date
        else:
            start_date, end_date = downloader.get_date_range()
            print(f"Using config defaults: {start_date} to {end_date}")
        
        # Run download
        result = await downloader.download_data(start_date, end_date)
        
        # Print summary
        if result.get('placeholder_mode'):
            print(f"\n🔄 PLACEHOLDER MODE: Structure created, waiting for API key")
            print(f"📁 Placeholder files: {args.output_dir}")
            print(f"🔑 Ready for AaveScan Pro API key integration")
        elif result['successful_downloads'] > 0:
            hourly_records = result.get('total_hourly_records', result.get('total_records', 0))
            print(f"\n🎉 SUCCESS! Downloaded and interpolated {hourly_records:,} AAVE hourly records")
            if result.get('interpolation_applied'):
                original_records = result.get('total_original_records', 0)
                print(f"📈 Interpolated from {original_records:,} daily records")
            print(f"📁 Output directory: {args.output_dir}")
        else:
            print(f"\n❌ FAILED! No AAVE data was downloaded successfully")
            if 'error' in result:
                print(f"💥 Error: {result['error']}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
