#!/usr/bin/env python3
"""
Data Provider Quality Gates - Consolidated

Comprehensive tests for data provider functionality including:
- Factory pattern functionality
- Canonical access patterns
- Data loading and validation
- Environment variable validation
- Health checks

Consolidated from:
- test_data_provider_factory_quality_gates.py
- test_data_provider_canonical_access_quality_gates.py
- test_data_provider_canonical_access_quality_gates_simple.py
"""

import os
import sys
import asyncio
import pandas as pd
import re
import ast
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set, Tuple
import structlog

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

# Load environment variables
sys.path.insert(0, str(Path(__file__).parent))
from load_env import load_quality_gates_env
load_quality_gates_env()

logger = structlog.get_logger()

class DataProviderQualityGates:
    """Quality gates for data provider functionality validation."""
    
    def __init__(self):
        self.results = {}
        self.passed = 0
        self.failed = 0
        self.total = 0
        
        # Legacy methods to detect and remove
        self.legacy_methods = [
            'get_cex_derivatives_balances',
            'get_cex_spot_balances', 
            'get_current_data',
            'get_execution_cost',
            'get_funding_rate',
            'get_gas_cost',
            'get_liquidity_index',
            'get_market_data_snapshot',
            'get_market_price',
            'get_smart_contract_balances',
            'get_wallet_balances'
        ]
        
        # Canonical patterns to validate
        self.canonical_patterns = {
            'get_data_method': r'def get_data\(self, timestamp: pd\.Timestamp\)',
            'standardized_structure': r'return \{[^}]*timestamp[^}]*market_data[^}]*protocol_data[^}]*\}',
            'utility_manager_usage': r'self\.utility_manager\.get_',
            'no_direct_data_access': r'data_provider\.get_[^_]'
        }
        
        # Test configurations for different strategy modes
        self.test_configs = {
            'pure_lending_usdt': {
                'mode': 'pure_lending_usdt',
                'data_type': 'defi',
                'data_dir': 'data',
                'share_class': 'USDT',
                'asset': 'USDT',
                'backtest_start_date': '2024-05-15',
                'backtest_end_date': '2024-09-18',
                'component_config': {
                    'position_monitor': {
                        'position_subscriptions': [
                            'binance:BaseToken:USDT',
                            'aave:aToken:aUSDT',
                            'aave:debtToken:debtUSDT'
                        ]
                    }
                }
            },
            'btc_basis': {
                'mode': 'btc_basis',
                'data_type': 'defi',
                'data_dir': 'data',
                'hedge_venues': ['binance', 'bybit', 'okx'],
                'share_class': 'USDT',
                'asset': 'BTC',
                'backtest_start_date': '2024-05-15',
                'backtest_end_date': '2024-09-18',
                'component_config': {
                    'position_monitor': {
                        'position_subscriptions': [
                            'binance:BaseToken:BTC',
                            'binance:BaseToken:USDT',
                            'binance:Perp:BTCUSDT',
                            'bybit:Perp:BTCUSDT',
                            'okx:Perp:BTCUSDT'
                        ]
                    }
                }
            },
            'eth_basis': {
                'mode': 'eth_basis',
                'data_type': 'defi',
                'data_dir': 'data',
                'hedge_venues': ['binance', 'bybit', 'okx'],
                'share_class': 'ETH',
                'asset': 'ETH',
                'backtest_start_date': '2024-05-15',
                'backtest_end_date': '2024-09-18',
                'component_config': {
                    'position_monitor': {
                        'position_subscriptions': [
                            'binance:BaseToken:ETH',
                            'binance:Perp:ETHUSDT',
                            'bybit:Perp:ETHUSDT',
                            'okx:Perp:ETHUSDT'
                        ]
                    }
                }
            },
            'eth_staking_only': {
                'mode': 'eth_staking_only',
                'data_type': 'defi',
                'data_dir': 'data',
                'share_class': 'ETH',
                'asset': 'ETH',
                'backtest_start_date': '2024-05-15',
                'backtest_end_date': '2024-09-18',
                'component_config': {
                    'position_monitor': {
                        'position_subscriptions': [
                            'binance:BaseToken:ETH',
                            'etherfi:LST:weETH',
                            'lido:LST:wstETH',
                            'wallet:BaseToken:EIGEN',
                            'wallet:BaseToken:ETHFI'
                        ],
                        'settlement': {
                            'seasonal_rewards_enabled': True
                        }
                    }
                }
            },
            'ml_btc_directional_usdt_margin': {
                'mode': 'ml_btc_directional_usdt_margin',
                'data_type': 'cefi',
                'data_dir': 'data',
                'hedge_venues': ['binance', 'bybit', 'okx'],
                'share_class': 'USDT',
                'asset': 'BTC',
                'backtest_start_date': '2024-05-15',
                'backtest_end_date': '2024-09-18',
                'component_config': {
                    'position_monitor': {
                        'position_subscriptions': [
                            'binance:BaseToken:BTC',
                            'binance:BaseToken:USDT',
                            'binance:Perp:BTCUSDT',
                            'bybit:Perp:BTCUSDT',
                            'okx:Perp:BTCUSDT'
                        ]
                    }
                }
            }
        }
    
    def validate_environment_variables(self) -> Dict[str, Any]:
        """Validate required environment variables are set."""
        print("🔧 Testing environment variables...")
        
        required_vars = [
            'BASIS_DATA_START_DATE',
            'BASIS_DATA_END_DATE',
            'BASIS_DATA_DIR',
            'BASIS_EXECUTION_MODE'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"  ❌ Missing environment variables: {missing_vars}")
            return {'status': 'FAILED', 'missing_vars': missing_vars}
        else:
            print("  ✅ All required environment variables are set")
            return {'status': 'PASSED', 'missing_vars': []}
    
    def validate_factory_creation(self) -> Dict[str, Any]:
        """Test data provider factory creation for all modes."""
        print("🔧 Testing data provider factory creation...")
        
        try:
            from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
        except ImportError as e:
            print(f"  ❌ Cannot import data provider factory: {e}")
            return {'status': 'FAILED', 'error': str(e)}
        
        factory_results = {'passed': 0, 'failed': 0, 'errors': []}
        
        for mode_name, config in self.test_configs.items():
            try:
                print(f"  📊 Testing factory creation for mode: {mode_name}")
                
                # Create data provider
                provider = create_data_provider(
                    execution_mode='backtest',
                    data_type=config.get('data_type', 'defi'),
                    config=config
                )
                
                if provider is None:
                    raise ValueError(f"Factory returned None for mode {mode_name}")
                
                # Test basic functionality
                test_timestamp = pd.Timestamp('2024-06-01 12:00:00', tz='UTC')
                
                # Only test data loading if the timestamp is within the data range
                if (test_timestamp >= pd.Timestamp(config['backtest_start_date'], tz='UTC') and
                    test_timestamp <= pd.Timestamp(config['backtest_end_date'], tz='UTC')):
                    
                    data = provider.get_data(test_timestamp)
                    
                    # Validate canonical data structure
                    required_keys = ['timestamp', 'market_data', 'protocol_data']
                    for key in required_keys:
                        if key not in data:
                            raise ValueError(f"Missing required key: {key}")
                    
                    # Validate market_data structure
                    if 'prices' not in data['market_data']:
                        raise ValueError("Missing market_data.prices")
                    
                    print(f"    ✅ Factory test passed for mode: {mode_name}")
                    factory_results['passed'] += 1
                else:
                    print(f"    ⚠️  Skipping data test for {mode_name} (timestamp outside data range)")
                    factory_results['passed'] += 1
                    
            except Exception as e:
                error_msg = f"Factory test failed for mode {mode_name}: {e}"
                print(f"    ❌ {error_msg}")
                factory_results['failed'] += 1
                factory_results['errors'].append(error_msg)
        
        if factory_results['failed'] > 0:
            print(f"  ❌ Factory tests: {factory_results['passed']} passed, {factory_results['failed']} failed")
            return {'status': 'FAILED', 'results': factory_results}
        else:
            print(f"  ✅ Factory tests: {factory_results['passed']} passed, 0 failed")
            return {'status': 'PASSED', 'results': factory_results}
    
    def validate_canonical_access_patterns(self) -> Dict[str, Any]:
        """Validate canonical access patterns in data provider code."""
        print("🔧 Testing canonical access patterns...")
        
        # Files to check for canonical patterns
        data_provider_files = [
            'backend/src/basis_strategy_v1/infrastructure/data/historical_defi_data_provider.py',
            'backend/src/basis_strategy_v1/infrastructure/data/historical_cefi_data_provider.py',
            'backend/src/basis_strategy_v1/infrastructure/data/live_defi_data_provider.py',
            'backend/src/basis_strategy_v1/infrastructure/data/live_cefi_data_provider.py'
        ]
        
        pattern_results = {'passed': 0, 'failed': 0, 'errors': []}
        
        for file_path in data_provider_files:
            full_path = Path(__file__).parent.parent / file_path
            if not full_path.exists():
                continue
                
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                
                # Check for canonical get_data method
                if re.search(self.canonical_patterns['get_data_method'], content):
                    print(f"  ✅ {file_path}: Has canonical get_data method")
                    pattern_results['passed'] += 1
                else:
                    print(f"  ❌ {file_path}: Missing canonical get_data method")
                    pattern_results['failed'] += 1
                    pattern_results['errors'].append(f"{file_path}: Missing canonical get_data method")
                
                # Check for legacy methods (should not exist)
                legacy_found = []
                for legacy_method in self.legacy_methods:
                    if re.search(rf'def {legacy_method}\(', content):
                        legacy_found.append(legacy_method)
                
                if legacy_found:
                    print(f"  ⚠️  {file_path}: Found legacy methods: {legacy_found}")
                    pattern_results['failed'] += 1
                    pattern_results['errors'].append(f"{file_path}: Found legacy methods: {legacy_found}")
                else:
                    print(f"  ✅ {file_path}: No legacy methods found")
                    pattern_results['passed'] += 1
                    
            except Exception as e:
                error_msg = f"Error checking {file_path}: {e}"
                print(f"  ❌ {error_msg}")
                pattern_results['failed'] += 1
                pattern_results['errors'].append(error_msg)
        
        if pattern_results['failed'] > 0:
            print(f"  ❌ Pattern validation: {pattern_results['passed']} passed, {pattern_results['failed']} failed")
            return {'status': 'FAILED', 'results': pattern_results}
        else:
            print(f"  ✅ Pattern validation: {pattern_results['passed']} passed, 0 failed")
            return {'status': 'PASSED', 'results': pattern_results}
    
    def validate_data_loading_with_exceptions(self) -> Dict[str, Any]:
        """Validate data loading with proper exception handling for sparse data."""
        print("🔧 Testing data loading with exception handling...")
        
        try:
            from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
        except ImportError as e:
            print(f"  ❌ Cannot import data provider factory: {e}")
            return {'status': 'FAILED', 'error': str(e)}
        
        loading_results = {'passed': 0, 'failed': 0, 'errors': []}
        
        # Test with realistic data range
        test_timestamp = pd.Timestamp('2024-06-01 12:00:00', tz='UTC')
        
        for mode_name, config in self.test_configs.items():
            try:
                print(f"  📊 Testing data loading for mode: {mode_name}")
                
                provider = create_data_provider(
                    execution_mode='backtest',
                    data_type=config.get('data_type', 'defi'),
                    config=config
                )
                
                if provider is None:
                    raise ValueError(f"Factory returned None for mode {mode_name}")
                
                # Test data loading
                data = provider.get_data(test_timestamp)
                
                # Validate data structure
                if not isinstance(data, dict):
                    raise ValueError("Data should be a dictionary")
                
                if 'timestamp' not in data:
                    raise ValueError("Missing timestamp in data")
                
                if 'market_data' not in data:
                    raise ValueError("Missing market_data in data")
                
                if 'protocol_data' not in data:
                    raise ValueError("Missing protocol_data in data")
                
                # Check for sparse data handling (EIGEN, ETHFI)
                if mode_name == 'eth_staking_only':
                    # These tokens might not have data for the test timestamp
                    eigen_price = data['market_data']['prices'].get('EIGEN')
                    ethfi_price = data['market_data']['prices'].get('ETHFI')
                    
                    if eigen_price is None:
                        print(f"    ⚠️  EIGEN price not available (expected for {test_timestamp})")
                    if ethfi_price is None:
                        print(f"    ⚠️  ETHFI price not available (expected for {test_timestamp})")
                
                print(f"    ✅ Data loading test passed for mode: {mode_name}")
                loading_results['passed'] += 1
                
            except Exception as e:
                error_msg = f"Data loading test failed for mode {mode_name}: {e}"
                print(f"    ❌ {error_msg}")
                loading_results['failed'] += 1
                loading_results['errors'].append(error_msg)
        
        if loading_results['failed'] > 0:
            print(f"  ❌ Data loading tests: {loading_results['passed']} passed, {loading_results['failed']} failed")
            return {'status': 'FAILED', 'results': loading_results}
        else:
            print(f"  ✅ Data loading tests: {loading_results['passed']} passed, 0 failed")
            return {'status': 'PASSED', 'results': loading_results}
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all data provider quality gate checks."""
        print("🚀 Starting data provider quality gate test...")
        print("=" * 80)
        
        # Run all checks
        env_check = self.validate_environment_variables()
        factory_check = self.validate_factory_creation()
        pattern_check = self.validate_canonical_access_patterns()
        loading_check = self.validate_data_loading_with_exceptions()
        
        # Determine overall status
        all_passed = (
            env_check['status'] == 'PASSED' and
            factory_check['status'] == 'PASSED' and
            pattern_check['status'] == 'PASSED' and
            loading_check['status'] == 'PASSED'
        )
        
        # Print summary
        print("=" * 80)
        print("📊 DATA PROVIDER QUALITY GATE SUMMARY")
        print("=" * 80)
        print(f"🔧 Environment Variables: {env_check['status']}")
        print(f"🏭 Factory Creation: {factory_check['status']}")
        print(f"📋 Canonical Patterns: {pattern_check['status']}")
        print(f"📊 Data Loading: {loading_check['status']}")
        print(f"📈 Overall Status: {'PASSED' if all_passed else 'FAILED'}")
        
        if not all_passed:
            print("\n❌ FAILURE: Data provider quality gates failed!")
            return False
        else:
            print("\n✅ SUCCESS: All data provider quality gates passed!")
            return True


def main():
    """Main entry point for data provider quality gates."""
    gates = DataProviderQualityGates()
    success = gates.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
