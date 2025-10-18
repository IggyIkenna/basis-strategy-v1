#!/usr/bin/env python3
"""
Comprehensive Data Validation Quality Gates

This script runs comprehensive data validation tests including:
- Data provider factory creation and functionality
- Critical data file existence and accessibility
- Data availability validation with gap checking
- Canonical data structure validation

Usage:
    python scripts/test_data_validation_quality_gates.py
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'backend' / 'src'))

from basis_strategy_v1.infrastructure.data.data_validator import DataValidator, DataProviderError
from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider

logger = logging.getLogger(__name__)


class ComprehensiveDataValidator:
    """Comprehensive data validation combining all data quality checks."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.project_root = project_root
        
        # Initialize validators
        self.data_validator = DataValidator(str(data_dir))
        
        # Strategy modes to test with their configs
        self.test_configs = self._create_test_configs()
        
        # Results tracking
        self.results = {
            'data_provider_factory': {'passed': 0, 'failed': 0, 'errors': []},
            'data_files': {'passed': 0, 'failed': 0, 'errors': []},
            'data_availability': {'passed': 0, 'failed': 0, 'errors': []},
            'canonical_structure': {'passed': 0, 'failed': 0, 'errors': []}
        }
    
    def _create_test_configs(self) -> Dict[str, Dict[str, Any]]:
        """Create test configurations for each strategy mode."""
        return {
            'pure_lending_usdt': {
                'mode': 'pure_lending_usdt',
                'data_type': 'defi',
                'data_dir': 'data',
                'share_class': 'USDT',
                'asset': 'USDT',
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02',
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
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02',
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
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02',
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
            'eth_leveraged': {
                'mode': 'eth_leveraged',
                'data_type': 'defi',
                'data_dir': 'data',
                'hedge_venues': ['binance', 'bybit', 'okx'],
                'share_class': 'ETH',
                'asset': 'ETH',
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02',
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
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02',
                'component_config': {
                    'position_monitor': {
                        'position_subscriptions': [
                            'binance:BaseToken:ETH',
                            'etherfi:LST:weETH',
                            'wallet:BaseToken:EIGEN',  # Dust token from KING unwrapping
                            'wallet:BaseToken:ETHFI'   # Dust token from KING unwrapping
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
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02',
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
            'ml_usdt_directional_usdt_margin': {
                'mode': 'ml_usdt_directional_usdt_margin',
                'data_type': 'cefi',
                'data_dir': 'data',
                'hedge_venues': ['binance', 'bybit', 'okx'],
                'share_class': 'USDT',
                'asset': 'USDT',
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02',
                'component_config': {
                    'position_monitor': {
                        'position_subscriptions': [
                            'binance:BaseToken:USDT',
                            'binance:Perp:USDTUSDT',
                            'bybit:Perp:USDTUSDT',
                            'okx:Perp:USDTUSDT'
                        ]
                    }
                }
            }
        }
    
    def validate_data_provider_factory(self) -> Dict[str, Any]:
        """Test data provider factory creation and functionality."""
        print("🔧 Testing data provider factory creation...")
        
        factory_results = {'passed': 0, 'failed': 0, 'errors': []}
        
        for mode, config in self.test_configs.items():
            try:
                print(f"  📊 Testing factory creation for mode: {mode}")
                
                # Create data provider with new 4-provider architecture
                data_type = config['data_type']
                provider = create_data_provider('backtest', data_type, config)
                
                # Test data requirements validation (already done in provider creation)
                # The provider.validate_data_requirements() is called during creation
                
                # Data loading is on-demand in new architecture
                
                # Test canonical data structure
                test_timestamp = pd.Timestamp('2024-06-01 12:00:00', tz='UTC')
                data = provider.get_data(test_timestamp)
                
                # Validate data structure
                self._validate_canonical_data_structure(data, mode)
                
                factory_results['passed'] += 1
                print(f"    ✅ Factory test passed for mode: {mode}")
                
            except Exception as e:
                factory_results['failed'] += 1
                factory_results['errors'].append(f"{mode}: {str(e)}")
                print(f"    ❌ Factory test failed for mode: {mode}: {e}")
        
        self.results['data_provider_factory'] = factory_results
        return factory_results
    
    def validate_data_files(self) -> Dict[str, Any]:
        """Validate critical data files exist and are accessible."""
        print("📁 Validating critical data files...")
        
        file_results = {'passed': 0, 'failed': 0, 'errors': []}
        
        # Check critical files that all modes need (using actual file paths)
        # Check critical files that all modes need (using actual file paths)
        critical_files = [
            'market_data/spot_prices/btc_usd/binance_BTCUSDT_1h_2024-01-01_2025-09-30.csv',
            'market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_2020-01-01_2025-09-26.csv',
            'market_data/derivatives/funding_rates/binance_BTCUSDT_funding_rates_2024-01-01_2025-09-30.csv',
            'ml_data/predictions/btc_predictions.csv',
            'ml_data/predictions/usdt_predictions.csv',
            'market_data/derivatives/futures_ohlcv/binance_BTCUSDT_perp_1h_2024-01-01_2025-09-30.csv',
            'execution_costs/execution_cost_simulation_results.csv',
            # Dust token files for seasonal rewards
            'market_data/spot_prices/protocol_tokens/binance_EIGENUSDT_1h_2024-10-05_2025-09-30.csv',
            'market_data/spot_prices/protocol_tokens/binance_ETHFIUSDT_1h_2024-06-01_2025-09-30.csv'
        ]
        
        for file_path in critical_files:
            try:
                full_path = self.data_dir / file_path
                print(f"    🔍 Checking: {full_path}")
                if full_path.exists():
                    with open(full_path, 'r') as f:
                        f.read(1)  # Try to read one character
                    
                    file_size = full_path.stat().st_size / (1024 * 1024)  # MB
                    print(f"    ✅ {file_path}: {file_size:.2f} MB")
                    file_results['passed'] += 1
                else:
                    print(f"    ❌ {file_path}: File not found at {full_path}")
                    file_results['failed'] += 1
                    file_results['errors'].append(f"Missing: {file_path}")
                    
            except Exception as e:
                print(f"    ❌ {file_path}: {e}")
                file_results['failed'] += 1
                file_results['errors'].append(f"Error accessing {file_path}: {e}")
        
        self.results['data_files'] = file_results
        return file_results
    
    def validate_data_availability(self) -> Dict[str, Any]:
        """Validate data availability by checking critical files exist."""
        print("📊 Validating data availability...")
        
        availability_results = {'passed': 0, 'failed': 0, 'errors': []}
        
        # Check critical files that all modes need (using actual file paths)
        # Check critical files that all modes need (using actual file paths)
        critical_files = [
            'market_data/spot_prices/btc_usd/binance_BTCUSDT_1h_2024-01-01_2025-09-30.csv',
            'market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_2020-01-01_2025-09-26.csv',
            'market_data/derivatives/funding_rates/binance_BTCUSDT_funding_rates_2024-01-01_2025-09-30.csv',
            'ml_data/predictions/btc_predictions.csv',
            'ml_data/predictions/usdt_predictions.csv',
            'market_data/derivatives/futures_ohlcv/binance_BTCUSDT_perp_1h_2024-01-01_2025-09-30.csv',
            'execution_costs/execution_cost_simulation_results.csv',
            # Dust token files for seasonal rewards
            'market_data/spot_prices/protocol_tokens/binance_EIGENUSDT_1h_2024-10-05_2025-09-30.csv',
            'market_data/spot_prices/protocol_tokens/binance_ETHFIUSDT_1h_2024-06-01_2025-09-30.csv'
        ]
        
        for file_path in critical_files:
            try:
                full_path = self.data_dir / file_path
                print(f"    🔍 Checking: {full_path}")
                if full_path.exists():
                    # Use data validator to check file validity
                    self.data_validator.validate_complete_file(full_path)
                    print(f"    ✅ {file_path}: Valid")
                    availability_results['passed'] += 1
                else:
                    print(f"    ❌ {file_path}: File not found at {full_path}")
                    availability_results['failed'] += 1
                    availability_results['errors'].append(f"Missing: {file_path}")
                    
            except DataProviderError as e:
                print(f"    ❌ {file_path}: {e}")
                availability_results['failed'] += 1
                availability_results['errors'].append(f"Error validating {file_path}: {e}")
            except Exception as e:
                print(f"    ❌ {file_path}: {e}")
                availability_results['failed'] += 1
                availability_results['errors'].append(f"Error accessing {file_path}: {e}")
        
        self.results['data_availability'] = availability_results
        return availability_results
    
    def validate_canonical_data_structure(self) -> Dict[str, Any]:
        """Validate canonical data structure for a representative mode."""
        print("🏗️  Testing canonical data structure...")
        
        structure_results = {'passed': 0, 'failed': 0, 'errors': []}
        
        try:
            # Test with pure_lending_usdt mode as representative
            config = self.test_configs['pure_lending_usdt']
            provider = create_data_provider('backtest', 'defi', config)
            
            test_timestamp = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
            data = provider.get_data(test_timestamp)
            
            # Validate canonical structure
            self._validate_canonical_data_structure(data, 'pure_lending_usdt')
            
            structure_results['passed'] += 1
            print("    ✅ Canonical data structure test passed")
            
        except Exception as e:
            structure_results['failed'] += 1
            structure_results['errors'].append(f"Canonical structure: {str(e)}")
            print(f"    ❌ Canonical data structure test failed: {e}")
        
        self.results['canonical_structure'] = structure_results
        return structure_results
    
    def _validate_canonical_data_structure(self, data: Dict[str, Any], mode: str) -> None:
        """Validate that data follows canonical structure."""
        required_sections = ['market_data', 'protocol_data', 'execution_data']
        
        for section in required_sections:
            if section not in data:
                raise ValueError(f"Missing required data section: {section}")
            
            if not isinstance(data[section], dict):
                raise ValueError(f"Data section {section} must be a dictionary")
        
        # Validate market_data structure
        market_data = data['market_data']
        if 'prices' not in market_data:
            raise ValueError("market_data must contain 'prices'")
        
        # Validate protocol_data structure
        protocol_data = data['protocol_data']
        if 'perp_prices' not in protocol_data:
            raise ValueError("protocol_data must contain 'perp_prices'")
        
        # Validate execution_data structure
        execution_data = data['execution_data']
        if 'gas_costs' not in execution_data or 'execution_costs' not in execution_data:
            raise ValueError("execution_data must contain 'gas_costs' and 'execution_costs'")
        
        # For ML modes, check for ml_data section
        if mode.startswith('ml_'):
            if 'ml_data' not in data:
                raise ValueError("Missing 'ml_data' section for ML mode")
            if 'predictions' not in data['ml_data']:
                raise ValueError("Missing 'predictions' in ml_data")
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("🚀 Starting comprehensive data validation quality gate test...")
        print("=" * 80)
        
        # Run all validation tests
        factory_results = self.validate_data_provider_factory()
        file_results = self.validate_data_files()
        availability_results = self.validate_data_availability()
        structure_results = self.validate_canonical_data_structure()
        
        # Calculate overall results
        total_tests = sum([
            factory_results['passed'] + factory_results['failed'],
            file_results['passed'] + file_results['failed'],
            availability_results['passed'] + availability_results['failed'],
            structure_results['passed'] + structure_results['failed']
        ])
        
        total_passed = sum([
            factory_results['passed'],
            file_results['passed'],
            availability_results['passed'],
            structure_results['passed']
        ])
        
        total_failed = sum([
            factory_results['failed'],
            file_results['failed'],
            availability_results['failed'],
            structure_results['failed']
        ])
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE DATA VALIDATION SUMMARY")
        print("=" * 80)
        print(f"🔧 Data Provider Factory: {factory_results['passed']}/{factory_results['passed'] + factory_results['failed']} passed")
        print(f"📁 Data Files: {file_results['passed']}/{file_results['passed'] + file_results['failed']} passed")
        print(f"📊 Data Availability: {availability_results['passed']}/{availability_results['passed'] + availability_results['failed']} passed")
        print(f"🏗️  Canonical Structure: {structure_results['passed']}/{structure_results['passed'] + structure_results['failed']} passed")
        print()
        print("📈 OVERALL SUMMARY:")
        print(f"  Total tests: {total_tests}")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_failed}")
        print(f"  Success rate: {success_rate:.1f}%")
        
        # Print errors
        all_errors = []
        for test_name, results in self.results.items():
            all_errors.extend(results['errors'])
        
        if all_errors:
            print("\n❌ ERRORS:")
            for error in all_errors:
                print(f"  - {error}")
        
        # Determine overall success
        if total_failed == 0:
            print("\n✅ SUCCESS: All comprehensive data validation quality gates passed!")
            return {'success': True, 'results': self.results}
        else:
            print(f"\n❌ FAILURE: {total_failed} comprehensive data validation quality gates failed!")
            return {'success': False, 'results': self.results}


def main():
    """Main entry point for the comprehensive data validation quality gate."""
    logging.basicConfig(level=logging.INFO)
    
    validator = ComprehensiveDataValidator()
    result = validator.run_comprehensive_validation()
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
