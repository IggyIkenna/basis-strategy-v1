"""
Data Loading Quality Gate Tests

Comprehensive tests for data availability, completeness, and alignment
across all strategy modes to ensure all required data is available
before proceeding with implementation.
"""

import os
import sys
import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_path))


class DataAvailabilityChecker:
    """Comprehensive data availability checker for all strategy modes."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.market_data_dir = self.data_dir / "market_data"
        self.protocol_data_dir = self.data_dir / "protocol_data"
        self.blockchain_data_dir = self.data_dir / "blockchain_data"
        self.execution_costs_dir = self.data_dir / "execution_costs"
        self.manual_sources_dir = self.data_dir / "manual_sources"
        
        # Strategy data requirements
        self.strategy_data_requirements = {
            'pure_lending_usdt': {
                'protocols': ['aave_v3'],
                'assets': ['USDT', 'WETH'],
                'timeframes': ['1h', '1d'],
                'required_fields': ['apy', 'total_supply', 'total_borrow'],
                'data_types': ['aave_lending_rates', 'usdt_prices', 'eth_prices']
            },
            'btc_basis': {
                'venues': ['binance', 'bybit', 'okx'],
                'assets': ['BTC'],
                'timeframes': ['1h', '1d'],
                'required_fields': ['funding_rate', 'spot_price', 'futures_price'],
                'data_types': ['btc_prices', 'funding_rates', 'futures_ohlcv']
            },
            'eth_basis': {
                'venues': ['binance', 'bybit', 'okx'],
                'protocols': ['lido', 'etherfi'],
                'assets': ['ETH'],
                'timeframes': ['1h', '1d'],
                'required_fields': ['funding_rate', 'spot_price', 'futures_price', 'lst_apy'],
                'data_types': ['eth_prices', 'funding_rates', 'futures_ohlcv', 'lst_data']
            },
            'usdt_market_neutral': {
                'venues': ['binance', 'bybit', 'okx'],
                'protocols': ['aave_v3'],
                'assets': ['USDT', 'ETH'],
                'timeframes': ['1h', '1d'],
                'required_fields': ['funding_rate', 'spot_price', 'futures_price', 'apy'],
                'data_types': ['usdt_prices', 'eth_prices', 'funding_rates', 'futures_ohlcv', 'aave_lending_rates']
            }
        }
    
    def check_all_data_availability(self) -> Dict[str, Any]:
        """Check data availability for all strategy modes."""
        results = {
            'overall_status': 'PASS',
            'strategy_modes': {},
            'data_directories': {},
            'summary': {
                'total_strategies': len(self.strategy_data_requirements),
                'passed_strategies': 0,
                'failed_strategies': 0,
                'missing_data_types': [],
                'data_quality_issues': []
            }
        }
        
        # Check data directories
        results['data_directories'] = self._check_data_directories()
        
        # Check each strategy mode
        for strategy_name, requirements in self.strategy_data_requirements.items():
            strategy_result = self._check_strategy_data_availability(strategy_name, requirements)
            results['strategy_modes'][strategy_name] = strategy_result
            
            if strategy_result['status'] == 'PASS':
                results['summary']['passed_strategies'] += 1
            else:
                results['summary']['failed_strategies'] += 1
                results['summary']['missing_data_types'].extend(strategy_result['missing_data_types'])
        
        # Determine overall status
        if results['summary']['failed_strategies'] > 0:
            results['overall_status'] = 'FAIL'
        
        return results
    
    def _check_data_directories(self) -> Dict[str, Any]:
        """Check if all required data directories exist."""
        directories = {
            'market_data': self.market_data_dir,
            'protocol_data': self.protocol_data_dir,
            'blockchain_data': self.blockchain_data_dir,
            'execution_costs': self.execution_costs_dir,
            'manual_sources': self.manual_sources_dir
        }
        
        results = {}
        for name, path in directories.items():
            results[name] = {
                'exists': path.exists(),
                'path': str(path),
                'readable': path.exists() and os.access(path, os.R_OK),
                'file_count': len(list(path.glob('*'))) if path.exists() else 0
            }
        
        return results
    
    def _check_strategy_data_availability(self, strategy_name: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Check data availability for a specific strategy mode."""
        result = {
            'status': 'PASS',
            'missing_data_types': [],
            'data_quality_issues': [],
            'coverage_metrics': {},
            'details': {}
        }
        
        # Check each required data type
        for data_type in requirements['data_types']:
            data_availability = self._check_data_type_availability(data_type)
            result['details'][data_type] = data_availability
            
            if not data_availability['available']:
                result['status'] = 'FAIL'
                result['missing_data_types'].append(data_type)
            
            if data_availability['quality_issues']:
                result['data_quality_issues'].extend(data_availability['quality_issues'])
        
        # Calculate coverage metrics
        result['coverage_metrics'] = self._calculate_coverage_metrics(strategy_name, requirements)
        
        return result
    
    def _check_data_type_availability(self, data_type: str) -> Dict[str, Any]:
        """Check availability of a specific data type."""
        result = {
            'available': False,
            'files_found': [],
            'quality_issues': [],
            'coverage_period': None,
            'data_freshness': None
        }
        
        # Map data types to file patterns
        data_type_patterns = {
            'btc_prices': 'spot_prices/btc_usd/*',
            'eth_prices': 'spot_prices/eth_usd/*',
            'usdt_prices': 'spot_prices/btc_usd/*',  # BTC/USDT pairs contain USDT prices
            'usdc_prices': 'spot_prices/eth_usd/*',  # ETH/USDT pairs can be used for USDC reference
            'funding_rates': 'derivatives/funding_rates/*',
            'futures_ohlcv': 'derivatives/futures_ohlcv/*',
            'aave_lending_rates': 'protocol_data/aave/rates/*',
            'morpho_lending_rates': 'protocol_data/morpho/*',
            'lst_data': 'protocol_data/staking/**/*.csv'
        }
        
        if data_type not in data_type_patterns:
            result['quality_issues'].append(f"Unknown data type: {data_type}")
            return result
        
        pattern = data_type_patterns[data_type]
        
        # Try market data directory first
        if pattern.startswith('spot_prices/') or pattern.startswith('derivatives/'):
            files = list(self.market_data_dir.glob(pattern))
        elif pattern.startswith('protocol_data/aave/'):
            # Remove the protocol_data/ prefix for protocol data directory
            protocol_pattern = pattern.replace('protocol_data/', '')
            files = list(self.protocol_data_dir.glob(protocol_pattern))
        elif pattern.startswith('protocol_data/staking/'):
            # Remove the protocol_data/ prefix for protocol data directory
            protocol_pattern = pattern.replace('protocol_data/', '')
            files = list(self.protocol_data_dir.glob(protocol_pattern))
        else:
            # Try all directories
            files = list(self.market_data_dir.glob(pattern))
            if not files:
                files = list(self.protocol_data_dir.glob(pattern))
            if not files:
                files = list(self.blockchain_data_dir.glob(pattern))
            if not files:
                files = list(self.manual_sources_dir.glob(pattern))
        
        if files:
            result['available'] = True
            result['files_found'] = [str(f) for f in files]
            
            # Check data quality
            quality_issues = self._check_data_quality(files[0], data_type)
            result['quality_issues'] = quality_issues
            
            # Check coverage period
            result['coverage_period'] = self._check_data_coverage(files[0])
            
            # Check data freshness
            result['data_freshness'] = self._check_data_freshness(files[0])
        
        return result
    
    def _check_data_quality(self, file_path: Path, data_type: str) -> List[str]:
        """Check data quality for a specific file."""
        issues = []
        
        try:
            if file_path.suffix == '.csv':
                df = pd.read_csv(file_path)
                
                # Check for empty data
                if df.empty:
                    issues.append(f"Empty data file: {file_path.name}")
                
                # Check for missing values
                missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
                if missing_pct > 10:
                    issues.append(f"High missing data percentage: {missing_pct:.1f}%")
                
                # Check for required columns based on data type
                required_columns = self._get_required_columns(data_type)
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    issues.append(f"Missing required columns: {missing_columns}")
                
                # Check for duplicate timestamps
                if 'timestamp' in df.columns:
                    duplicates = df['timestamp'].duplicated().sum()
                    if duplicates > 0:
                        issues.append(f"Duplicate timestamps: {duplicates}")
            
            elif file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                if not data:
                    issues.append(f"Empty JSON file: {file_path.name}")
        
        except Exception as e:
            issues.append(f"Error reading file {file_path.name}: {str(e)}")
        
        return issues
    
    def _get_required_columns(self, data_type: str) -> List[str]:
        """Get required columns for a data type."""
        column_mapping = {
            'btc_prices': ['timestamp', 'price'],
            'eth_prices': ['timestamp', 'price'],
            'usdt_prices': ['timestamp', 'price'],
            'usdc_prices': ['timestamp', 'price'],
            'funding_rates': ['timestamp', 'funding_rate'],
            'futures_ohlcv': ['timestamp', 'open', 'high', 'low', 'close', 'volume'],
            'aave_lending_rates': ['timestamp', 'apy', 'total_supply'],
            'morpho_lending_rates': ['timestamp', 'apy', 'total_supply'],
            'lst_data': ['timestamp', 'apy', 'total_supply']
        }
        return column_mapping.get(data_type, ['timestamp'])
    
    def _check_data_coverage(self, file_path: Path) -> Dict[str, Any]:
        """Check data coverage period."""
        try:
            if file_path.suffix == '.csv':
                df = pd.read_csv(file_path)
                if 'timestamp' in df.columns:
                    timestamps = pd.to_datetime(df['timestamp'])
                    return {
                        'start_date': timestamps.min().isoformat(),
                        'end_date': timestamps.max().isoformat(),
                        'total_records': len(df),
                        'date_range_days': (timestamps.max() - timestamps.min()).days
                    }
        except Exception:
            pass
        
        return {
            'start_date': None,
            'end_date': None,
            'total_records': 0,
            'date_range_days': 0
        }
    
    def _check_data_freshness(self, file_path: Path) -> Dict[str, Any]:
        """Check data freshness."""
        try:
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            age_days = (datetime.now() - file_mtime).days
            
            return {
                'last_modified': file_mtime.isoformat(),
                'age_days': age_days,
                'is_fresh': age_days <= 7,  # Consider data fresh if less than 7 days old
                'freshness_status': 'FRESH' if age_days <= 7 else 'STALE'
            }
        except Exception:
            return {
                'last_modified': None,
                'age_days': None,
                'is_fresh': False,
                'freshness_status': 'UNKNOWN'
            }
    
    def _calculate_coverage_metrics(self, strategy_name: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate coverage metrics for a strategy."""
        return {
            'data_types_available': len([dt for dt in requirements['data_types'] if self._check_data_type_availability(dt)['available']]),
            'data_types_required': len(requirements['data_types']),
            'coverage_percentage': 0,  # Will be calculated based on available data types
            'assets_covered': len(requirements['assets']),
            'venues_covered': len(requirements.get('venues', [])),
            'protocols_covered': len(requirements.get('protocols', []))
        }


class TestDataLoadingQualityGate:
    """Test data loading quality gate for all strategy modes."""
    
    def setup_method(self):
        """Set up test environment."""
        self.data_checker = DataAvailabilityChecker()
    
    def test_data_directories_exist(self):
        """Test that all required data directories exist."""
        results = self.data_checker._check_data_directories()
        
        for dir_name, dir_info in results.items():
            assert dir_info['exists'], f"Data directory {dir_name} does not exist at {dir_info['path']}"
            assert dir_info['readable'], f"Data directory {dir_name} is not readable"
            assert dir_info['file_count'] > 0, f"Data directory {dir_name} is empty"
    
    def test_market_data_availability(self):
        """Test market data availability."""
        market_data_dir = self.data_checker.market_data_dir
        
        # Check for spot prices
        spot_prices_dir = market_data_dir / "spot_prices"
        assert spot_prices_dir.exists(), "Spot prices directory does not exist"
        
        # Check for BTC price data
        btc_dir = spot_prices_dir / "btc_usd"
        assert btc_dir.exists(), "BTC price directory does not exist"
        btc_files = list(btc_dir.glob("*.csv"))
        assert len(btc_files) > 0, "No BTC price CSV files found"
        
        # Check for ETH price data
        eth_dir = spot_prices_dir / "eth_usd"
        assert eth_dir.exists(), "ETH price directory does not exist"
        eth_files = list(eth_dir.glob("*.csv"))
        assert len(eth_files) > 0, "No ETH price CSV files found"
        
        # Check for derivatives data
        derivatives_dir = market_data_dir / "derivatives"
        assert derivatives_dir.exists(), "Derivatives directory does not exist"
        
        funding_rates_dir = derivatives_dir / "funding_rates"
        assert funding_rates_dir.exists(), "Funding rates directory does not exist"
        
        futures_ohlcv_dir = derivatives_dir / "futures_ohlcv"
        assert futures_ohlcv_dir.exists(), "Futures OHLCV directory does not exist"
    
    def test_protocol_data_availability(self):
        """Test protocol data availability."""
        protocol_data_dir = self.data_checker.protocol_data_dir
        
        # Check for AAVE data
        aave_dir = protocol_data_dir / "aave"
        assert aave_dir.exists(), "AAVE data directory does not exist"
        
        # Check for AAVE rates data
        aave_rates_dir = aave_dir / "rates"
        assert aave_rates_dir.exists(), "AAVE rates directory does not exist"
        aave_files = list(aave_rates_dir.glob("*.csv"))
        assert len(aave_files) > 0, "No AAVE CSV files found"
        
        # Check for staking data
        staking_dir = protocol_data_dir / "staking"
        assert staking_dir.exists(), "Staking data directory does not exist"
        
        # Check for staking CSV files in subdirectories
        staking_files = list(staking_dir.glob("**/*.csv"))
        assert len(staking_files) > 0, "No staking CSV files found"
    
    def test_blockchain_data_availability(self):
        """Test blockchain data availability."""
        blockchain_data_dir = self.data_checker.blockchain_data_dir
        
        # Check for gas data
        gas_files = list(blockchain_data_dir.glob("*gas*"))
        assert len(gas_files) > 0, "No gas data files found"
        
        # Check for gas prices directory
        gas_prices_dir = blockchain_data_dir / "gas_prices"
        assert gas_prices_dir.exists(), "Gas prices directory does not exist"
    
    def test_execution_costs_data_availability(self):
        """Test execution costs data availability."""
        execution_costs_dir = self.data_checker.execution_costs_dir
        
        # Check for execution cost files
        cost_files = list(execution_costs_dir.glob("*.json"))
        assert len(cost_files) > 0, "No execution cost JSON files found"
        
        # Check for lookup tables
        lookup_tables_dir = execution_costs_dir / "lookup_tables"
        assert lookup_tables_dir.exists(), "Lookup tables directory does not exist"
    
    def test_manual_sources_data_availability(self):
        """Test manual sources data availability."""
        manual_sources_dir = self.data_checker.manual_sources_dir
        
        # Check for AAVE parameters
        aave_params_dir = manual_sources_dir / "aave_params"
        assert aave_params_dir.exists(), "AAVE parameters directory does not exist"
        
        # Check for benchmark data
        benchmark_dir = manual_sources_dir / "benchmark_data"
        assert benchmark_dir.exists(), "Benchmark data directory does not exist"
    
    def test_pure_lending_usdt_data_requirements(self):
        """Test data requirements for pure lending strategy."""
        strategy_result = self.data_checker._check_strategy_data_availability(
            'pure_lending_usdt', 
            self.data_checker.strategy_data_requirements['pure_lending_usdt']
        )
        
        assert strategy_result['status'] == 'PASS', f"Pure lending data requirements not met: {strategy_result['missing_data_types']}"
        assert len(strategy_result['missing_data_types']) == 0, f"Missing data types: {strategy_result['missing_data_types']}"
    
    def test_btc_basis_data_requirements(self):
        """Test data requirements for BTC basis strategy."""
        strategy_result = self.data_checker._check_strategy_data_availability(
            'btc_basis', 
            self.data_checker.strategy_data_requirements['btc_basis']
        )
        
        assert strategy_result['status'] == 'PASS', f"BTC basis data requirements not met: {strategy_result['missing_data_types']}"
        assert len(strategy_result['missing_data_types']) == 0, f"Missing data types: {strategy_result['missing_data_types']}"
    
    def test_eth_basis_data_requirements(self):
        """Test data requirements for ETH basis strategy."""
        strategy_result = self.data_checker._check_strategy_data_availability(
            'eth_basis', 
            self.data_checker.strategy_data_requirements['eth_basis']
        )
        
        assert strategy_result['status'] == 'PASS', f"ETH basis data requirements not met: {strategy_result['missing_data_types']}"
        assert len(strategy_result['missing_data_types']) == 0, f"Missing data types: {strategy_result['missing_data_types']}"
    
    def test_usdt_market_neutral_data_requirements(self):
        """Test data requirements for USDT market neutral strategy."""
        strategy_result = self.data_checker._check_strategy_data_availability(
            'usdt_market_neutral', 
            self.data_checker.strategy_data_requirements['usdt_market_neutral']
        )
        
        assert strategy_result['status'] == 'PASS', f"USDT market neutral data requirements not met: {strategy_result['missing_data_types']}"
        assert len(strategy_result['missing_data_types']) == 0, f"Missing data types: {strategy_result['missing_data_types']}"
    
    def test_all_strategy_data_availability(self):
        """Test data availability for all strategy modes."""
        results = self.data_checker.check_all_data_availability()
        
        # Overall status should be PASS
        assert results['overall_status'] == 'PASS', f"Overall data availability check failed: {results['summary']}"
        
        # All strategies should pass
        assert results['summary']['failed_strategies'] == 0, f"Failed strategies: {results['summary']['failed_strategies']}"
        assert results['summary']['passed_strategies'] == results['summary']['total_strategies'], "Not all strategies passed"
    
    def test_data_quality_validation(self):
        """Test data quality validation."""
        # Test a specific data file for quality
        market_data_dir = self.data_checker.market_data_dir
        spot_prices_dir = market_data_dir / "spot_prices"
        
        if spot_prices_dir.exists():
            csv_files = list(spot_prices_dir.glob("*.csv"))
            if csv_files:
                test_file = csv_files[0]
                quality_issues = self.data_checker._check_data_quality(test_file, 'btc_prices')
                
                # Should not have critical quality issues
                critical_issues = [issue for issue in quality_issues if 'Empty data' in issue or 'Error reading' in issue]
                assert len(critical_issues) == 0, f"Critical data quality issues found: {critical_issues}"
    
    def test_data_freshness_validation(self):
        """Test data freshness validation."""
        # Test data freshness for recent files
        market_data_dir = self.data_checker.market_data_dir
        spot_prices_dir = market_data_dir / "spot_prices"
        
        if spot_prices_dir.exists():
            csv_files = list(spot_prices_dir.glob("*.csv"))
            if csv_files:
                test_file = csv_files[0]
                freshness = self.data_checker._check_data_freshness(test_file)
                
                # Data should be reasonably fresh (less than 30 days old)
                assert freshness['age_days'] is not None, "Could not determine data age"
                assert freshness['age_days'] < 30, f"Data is too old: {freshness['age_days']} days"
    
    def test_data_coverage_validation(self):
        """Test data coverage validation."""
        # Test data coverage for a specific file
        market_data_dir = self.data_checker.market_data_dir
        spot_prices_dir = market_data_dir / "spot_prices"
        
        if spot_prices_dir.exists():
            csv_files = list(spot_prices_dir.glob("*.csv"))
            if csv_files:
                test_file = csv_files[0]
                coverage = self.data_checker._check_data_coverage(test_file)
                
                # Should have reasonable data coverage
                assert coverage['total_records'] > 0, "No data records found"
                assert coverage['date_range_days'] > 0, "No date range found"


if __name__ == "__main__":
    pytest.main([__file__])
