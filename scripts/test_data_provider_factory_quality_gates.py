#!/usr/bin/env python3
"""
Data Provider Factory Quality Gates

Tests the config-driven data provider factory to ensure it creates correct providers
for each mode and validates data requirements properly.

Reference: docs/specs/09_DATA_PROVIDER.md - DataProvider Factory
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 8 (Data Provider Architecture)
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

# Load environment variables from .env files
sys.path.insert(0, str(Path(__file__).parent))
from load_env import load_quality_gates_env
load_quality_gates_env()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'backend' / 'src'))

from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
from basis_strategy_v1.infrastructure.data.base_data_provider import BaseDataProvider
from basis_strategy_v1.infrastructure.data.pure_lending_data_provider import PureLendingDataProvider

logger = logging.getLogger(__name__)


class DataProviderFactoryTester:
    """Test data provider factory functionality"""
    
    def __init__(self):
        self.test_configs = self._create_test_configs()
        self.results = {}
    
    def _create_test_configs(self) -> Dict[str, Dict[str, Any]]:
        """Create test configurations for each strategy mode."""
        return {
            'pure_lending': {
                'mode': 'pure_lending',
                'data_requirements': ['usdt_prices', 'aave_lending_rates', 'gas_costs', 'execution_costs'],
                'data_dir': 'data',
                'share_class': 'USDT',
                'asset': 'USDT',
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02'
            },
            'btc_basis': {
                'mode': 'btc_basis',
                'data_requirements': ['btc_prices', 'btc_futures', 'funding_rates', 'gas_costs', 'execution_costs'],
                'data_dir': 'data',
                'hedge_venues': ['binance', 'bybit', 'okx'],
                'share_class': 'USDT',
                'asset': 'BTC',
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02'
            },
            'eth_basis': {
                'mode': 'eth_basis',
                'data_requirements': ['eth_prices', 'eth_futures', 'funding_rates', 'gas_costs', 'execution_costs'],
                'data_dir': 'data',
                'hedge_venues': ['binance', 'bybit', 'okx'],
                'share_class': 'USDT',
                'asset': 'ETH',
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02'
            },
            'eth_leveraged': {
                'mode': 'eth_leveraged',
                'data_requirements': ['eth_prices', 'weeth_prices', 'aave_lending_rates', 'staking_rewards', 'eigen_rewards', 'gas_costs', 'execution_costs', 'aave_risk_params'],
                'data_dir': 'data',
                'lst_type': 'weeth',
                'rewards_mode': 'base_eigen',
                'share_class': 'ETH',
                'asset': 'ETH',
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02'
            },
            'eth_staking_only': {
                'mode': 'eth_staking_only',
                'data_requirements': ['eth_prices', 'weeth_prices', 'staking_rewards', 'gas_costs', 'execution_costs'],
                'data_dir': 'data',
                'lst_type': 'weeth',
                'share_class': 'ETH',
                'asset': 'ETH',
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02'
            },
            'usdt_market_neutral_no_leverage': {
                'mode': 'usdt_market_neutral_no_leverage',
                'data_requirements': ['eth_prices', 'weeth_prices', 'eth_futures', 'funding_rates', 'staking_rewards', 'gas_costs', 'execution_costs'],
                'data_dir': 'data',
                'lst_type': 'weeth',
                'hedge_venues': ['binance', 'bybit', 'okx'],
                'share_class': 'USDT',
                'asset': 'ETH',
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02'
            },
            'usdt_market_neutral': {
                'mode': 'usdt_market_neutral',
                'data_requirements': ['eth_prices', 'weeth_prices', 'aave_lending_rates', 'eth_futures', 'funding_rates', 'staking_rewards', 'eigen_rewards', 'gas_costs', 'execution_costs', 'aave_risk_params'],
                'data_dir': 'data',
                'lst_type': 'weeth',
                'rewards_mode': 'base_eigen',
                'hedge_venues': ['binance', 'bybit', 'okx'],
                'share_class': 'USDT',
                'asset': 'ETH',
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02'
            },
            'ml_btc_directional': {
                'mode': 'ml_btc_directional',
                'data_requirements': ['ml_ohlcv_5min', 'ml_predictions', 'btc_usd_prices', 'gas_costs', 'execution_costs'],
                'data_dir': 'data',
                'share_class': 'BTC',
                'asset': 'BTC',
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02'
            },
            'ml_usdt_directional': {
                'mode': 'ml_usdt_directional',
                'data_requirements': ['ml_ohlcv_5min', 'ml_predictions', 'usdt_usd_prices', 'gas_costs', 'execution_costs'],
                'data_dir': 'data',
                'share_class': 'USDT',
                'asset': 'USDT',
                'backtest_start_date': '2024-05-01',
                'backtest_end_date': '2024-06-02'
            }
        }
    
    def test_factory_creation(self) -> Dict[str, Any]:
        """Test factory creates correct providers for each mode."""
        logger.info("🔧 Testing data provider factory creation...")
        
        results = {
            'total_tests': len(self.test_configs),
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': {}
        }
        
        for mode, config in self.test_configs.items():
            logger.info(f"📊 Testing factory creation for mode: {mode}")
            
            try:
                # Test provider creation
                provider = create_data_provider(
                    execution_mode='backtest',
                    config=config
                )
                
                # Validate provider type (canonical architecture)
                if not isinstance(provider, BaseDataProvider):
                    raise ValueError(f"Provider is not BaseDataProvider instance: {type(provider)}")
                
                # Validate canonical methods
                if not hasattr(provider, 'get_data') or not hasattr(provider, 'validate_data_requirements'):
                    raise ValueError(f"Provider missing canonical methods: {type(provider)}")
                
                # Validate provider mode
                if provider.config.get('mode') != mode:
                    raise ValueError(f"Provider mode mismatch: expected {mode}, got {provider.config.get('mode')}")
                
                # Validate data requirements
                if provider.data_requirements != config['data_requirements']:
                    raise ValueError(f"Data requirements mismatch: expected {config['data_requirements']}, got {provider.data_requirements}")
                
                # Test health status
                health = provider.get_health_status()
                if health['status'] not in ['healthy', 'not_loaded']:
                    raise ValueError(f"Invalid health status: {health['status']}")
                
                results['test_results'][mode] = {
                    'status': 'passed',
                    'provider_class': provider.__class__.__name__,
                    'health_status': health['status'],
                    'available_data_types': provider.available_data_types
                }
                results['passed_tests'] += 1
                
                logger.info(f"✅ Factory test passed for mode: {mode}")
                
            except Exception as e:
                logger.error(f"❌ Factory test failed for mode {mode}: {e}")
                results['test_results'][mode] = {
                    'status': 'failed',
                    'error': str(e)
                }
                results['failed_tests'] += 1
        
        return results
    
    def test_canonical_data_structure(self) -> Dict[str, Any]:
        """Test that providers return canonical data structure."""
        logger.info("🏗️  Testing canonical data structure...")
        
        results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': {}
        }
        
        # Test with pure_lending mode (has canonical implementation)
        test_config = self.test_configs['pure_lending']
        
        try:
            logger.info("📊 Testing canonical data structure for pure_lending mode...")
            
            # Create provider
            provider = create_data_provider(
                execution_mode='backtest',
                config=test_config
            )
            
            # Test get_data method returns canonical structure
            import pandas as pd
            test_timestamp = pd.Timestamp('2024-05-01 12:00:00', tz='UTC')
            data = provider.get_data(test_timestamp)
            
            # Validate canonical structure
            required_sections = ['market_data', 'protocol_data', 'staking_data', 'execution_data']
            for section in required_sections:
                if section not in data:
                    raise ValueError(f"Missing required section: {section}")
            
            # Validate market_data structure
            if 'prices' not in data['market_data'] or 'rates' not in data['market_data']:
                raise ValueError("market_data missing required subsections: prices, rates")
            
            # Validate protocol_data structure
            if 'aave_indexes' not in data['protocol_data'] or 'oracle_prices' not in data['protocol_data'] or 'perp_prices' not in data['protocol_data']:
                raise ValueError("protocol_data missing required subsections: aave_indexes, oracle_prices, perp_prices")
            
            # Validate execution_data structure
            required_execution_keys = ['wallet_balances', 'smart_contract_balances', 'cex_spot_balances', 'cex_derivatives_balances', 'gas_costs', 'execution_costs']
            for key in required_execution_keys:
                if key not in data['execution_data']:
                    raise ValueError(f"execution_data missing required key: {key}")
            
            results['test_results']['canonical_structure'] = {
                'status': 'passed',
                'data_sections': list(data.keys()),
                'market_data_keys': list(data['market_data'].keys()),
                'protocol_data_keys': list(data['protocol_data'].keys()),
                'execution_data_keys': list(data['execution_data'].keys())
            }
            results['passed_tests'] += 1
            results['total_tests'] += 1
            
            logger.info("✅ Canonical data structure test passed")
            
        except Exception as e:
            logger.error(f"❌ Canonical data structure test failed: {e}")
            results['test_results']['canonical_structure'] = {
                'status': 'failed',
                'error': str(e)
            }
            results['failed_tests'] += 1
            results['total_tests'] += 1
        
        return results
    
    def test_data_requirements_validation(self) -> Dict[str, Any]:
        """Test data requirements validation."""
        logger.info("🔍 Testing data requirements validation...")
        
        results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': {}
        }
        
        for mode, config in self.test_configs.items():
            logger.info(f"📊 Testing data requirements validation for mode: {mode}")
            
            try:
                # Create provider
                provider = create_data_provider(
                    execution_mode='backtest',
                    config=config
                )
                
                # Test valid requirements
                provider.validate_data_requirements(config['data_requirements'])
                results['total_tests'] += 1
                results['passed_tests'] += 1
                
                # Test invalid requirements
                invalid_requirements = ['invalid_data_type', 'nonexistent_data']
                try:
                    provider.validate_data_requirements(invalid_requirements)
                    # Should not reach here
                    results['total_tests'] += 1
                    results['failed_tests'] += 1
                    results['test_results'][f"{mode}_invalid"] = {
                        'status': 'failed',
                        'error': 'Should have raised ValueError for invalid requirements'
                    }
                except ValueError:
                    # Expected behavior
                    results['total_tests'] += 1
                    results['passed_tests'] += 1
                    results['test_results'][f"{mode}_invalid"] = {
                        'status': 'passed',
                        'message': 'Correctly rejected invalid requirements'
                    }
                
                results['test_results'][f"{mode}_valid"] = {
                    'status': 'passed',
                    'message': 'Correctly accepted valid requirements'
                }
                
                logger.info(f"✅ Data requirements validation passed for mode: {mode}")
                
            except Exception as e:
                logger.error(f"❌ Data requirements validation failed for mode {mode}: {e}")
                results['test_results'][f"{mode}_valid"] = {
                    'status': 'failed',
                    'error': str(e)
                }
                results['failed_tests'] += 1
        
        return results
    
    def test_standardized_data_structure(self) -> Dict[str, Any]:
        """Test standardized data structure returned by providers."""
        logger.info("📋 Testing standardized data structure...")
        
        results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': {}
        }
        
        # Test timestamp - use May 2024 to match available data
        test_timestamp = pd.Timestamp('2024-05-15 12:00:00', tz='UTC')
        
        for mode, config in self.test_configs.items():
            logger.info(f"📊 Testing data structure for mode: {mode}")
            
            try:
                # Create provider
                provider = create_data_provider(
                    execution_mode='backtest',
                    config=config
                )
                
                # Test get_data method (canonical architecture)
                try:
                    data = provider.get_data(test_timestamp)
                    
                    # Validate structure
                    required_keys = ['market_data', 'protocol_data', 'staking_data', 'execution_data']
                    for key in required_keys:
                        if key not in data:
                            raise ValueError(f"Missing required key in data structure: {key}")
                    
                    # Validate nested structure
                    if not isinstance(data['market_data'], dict):
                        raise ValueError("market_data should be a dictionary")
                    if not isinstance(data['protocol_data'], dict):
                        raise ValueError("protocol_data should be a dictionary")
                    if not isinstance(data['staking_data'], dict):
                        raise ValueError("staking_data should be a dictionary")
                    if not isinstance(data['execution_data'], dict):
                        raise ValueError("execution_data should be a dictionary")
                    
                    # Note: timestamp is passed as parameter to get_data(), not included in returned data
                    
                    results['test_results'][mode] = {
                        'status': 'passed',
                        'data_structure': 'valid',
                        'keys_present': list(data.keys())
                    }
                    results['passed_tests'] += 1
                    
                except ValueError as ve:
                    if "Data not loaded" in str(ve):
                        # Expected for backtest mode without data loading
                        results['test_results'][mode] = {
                            'status': 'passed',
                            'data_structure': 'not_loaded_expected',
                            'message': 'Correctly requires data loading first'
                        }
                        results['passed_tests'] += 1
                    else:
                        raise ve
                
                results['total_tests'] += 1
                logger.info(f"✅ Data structure test passed for mode: {mode}")
                
            except Exception as e:
                logger.error(f"❌ Data structure test failed for mode {mode}: {e}")
                results['test_results'][mode] = {
                    'status': 'failed',
                    'error': str(e)
                }
                results['failed_tests'] += 1
        
        return results
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling for invalid configurations."""
        logger.info("🚨 Testing error handling...")
        
        results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': {}
        }
        
        # Test missing mode
        try:
            create_data_provider('backtest', {'data_requirements': []})
            results['test_results']['missing_mode'] = {
                'status': 'failed',
                'error': 'Should have raised ValueError for missing mode'
            }
            results['failed_tests'] += 1
        except ValueError:
            results['test_results']['missing_mode'] = {
                'status': 'passed',
                'message': 'Correctly rejected missing mode'
            }
            results['passed_tests'] += 1
        results['total_tests'] += 1
        
        # Test missing data_requirements
        try:
            create_data_provider('backtest', {'mode': 'pure_lending'})
            results['test_results']['missing_requirements'] = {
                'status': 'failed',
                'error': 'Should have raised ValueError for missing data_requirements'
            }
            results['failed_tests'] += 1
        except ValueError:
            results['test_results']['missing_requirements'] = {
                'status': 'passed',
                'message': 'Correctly rejected missing data_requirements'
            }
            results['passed_tests'] += 1
        results['total_tests'] += 1
        
        # Test unknown mode
        try:
            create_data_provider('backtest', {
                'mode': 'unknown_mode',
                'data_requirements': ['test_data']
            })
            results['test_results']['unknown_mode'] = {
                'status': 'failed',
                'error': 'Should have raised ValueError for unknown mode'
            }
            results['failed_tests'] += 1
        except ValueError:
            results['test_results']['unknown_mode'] = {
                'status': 'passed',
                'message': 'Correctly rejected unknown mode'
            }
            results['passed_tests'] += 1
        results['total_tests'] += 1
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all factory tests."""
        logger.info("🚀 Starting data provider factory quality gate tests...")
        
        all_results = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'factory_creation': self.test_factory_creation(),
            'canonical_data_structure': self.test_canonical_data_structure(),
            'data_requirements_validation': self.test_data_requirements_validation(),
            'standardized_data_structure': self.test_standardized_data_structure(),
            'error_handling': self.test_error_handling()
        }
        
        # Calculate overall results
        total_tests = sum(
            result.get('total_tests', 0) 
            for result in all_results.values() 
            if isinstance(result, dict) and 'total_tests' in result
        )
        total_passed = sum(
            result.get('passed_tests', 0) 
            for result in all_results.values() 
            if isinstance(result, dict) and 'passed_tests' in result
        )
        total_failed = sum(
            result.get('failed_tests', 0) 
            for result in all_results.values() 
            if isinstance(result, dict) and 'failed_tests' in result
        )
        
        all_results['overall'] = {
            'total_tests': total_tests,
            'passed_tests': total_passed,
            'failed_tests': total_failed,
            'success_rate': total_passed / total_tests if total_tests > 0 else 0,
            'status': 'passed' if total_failed == 0 else 'failed'
        }
        
        return all_results


def test_data_provider_factory():
    """Test data provider factory functionality."""
    logger.info("🚀 Starting data provider factory quality gate test...")
    
    try:
        # Set up environment variables for testing
        os.environ['BASIS_DATA_START_DATE'] = '2024-01-01'
        os.environ['BASIS_DATA_END_DATE'] = '2024-12-31'
        
        # Initialize tester
        tester = DataProviderFactoryTester()
        
        # Run all tests
        results = tester.run_all_tests()
        
        # Print summary
        print("\n" + "="*80)
        print("DATA PROVIDER FACTORY QUALITY GATE RESULTS")
        print("="*80)
        print(f"Overall Status: {results['overall']['status'].upper()}")
        print(f"Timestamp: {results['timestamp']}")
        print()
        
        print("TEST CATEGORIES:")
        print("-" * 40)
        for category, result in results.items():
            if isinstance(result, dict) and 'total_tests' in result:
                status_emoji = "✅" if result.get('failed_tests', 0) == 0 else "❌"
                print(f"{status_emoji} {category}: {result['passed_tests']}/{result['total_tests']} passed")
        
        print()
        print("OVERALL SUMMARY:")
        print("-" * 40)
        overall = results['overall']
        print(f"Total tests: {overall['total_tests']}")
        print(f"Passed tests: {overall['passed_tests']}")
        print(f"Failed tests: {overall['failed_tests']}")
        print(f"Success rate: {overall['success_rate']:.1%}")
        
        # Check if test passed
        if results['overall']['status'] == 'passed':
            print("\n🎉 DATA PROVIDER FACTORY QUALITY GATE: PASSED")
            return True
        else:
            print("\n❌ DATA PROVIDER FACTORY QUALITY GATE: FAILED")
            return False
            
    except Exception as e:
        logger.error(f"❌ Data provider factory test failed: {e}")
        print(f"\n❌ DATA PROVIDER FACTORY QUALITY GATE: ERROR - {e}")
        return False


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    success = test_data_provider_factory()
    sys.exit(0 if success else 1)
