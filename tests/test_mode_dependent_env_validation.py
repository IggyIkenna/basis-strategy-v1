#!/usr/bin/env python3
"""
Mode-Dependent Environment Variable Validation Test

Tests that environment variable validation works correctly based on execution mode:
- Backtest mode: NO credentials required
- Live mode: Only current environment credentials required (dev/staging/prod)

Reference: docs/ENVIRONMENT_VARIABLES.md - Mode-Dependent Validation section
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from basis_strategy_v1.infrastructure.config.config_validator import ConfigValidator


class ModeDependentEnvValidator:
    """Test mode-dependent environment variable validation."""
    
    def __init__(self):
        self.results = {
            'backtest_mode_tests': {},
            'live_mode_tests': {},
            'errors': [],
            'warnings': []
        }
    
    def run_all_tests(self):
        """Run all mode-dependent validation tests."""
        print("🧪 Testing mode-dependent environment variable validation...")
        
        try:
            self._test_backtest_mode_no_credentials()
            self._test_live_mode_dev_credentials()
            self._test_live_mode_prod_credentials()
            self._test_live_mode_staging_credentials()
            self._test_invalid_execution_mode()
            self._generate_report()
        except Exception as e:
            print(f"❌ Test failed: {e}")
            self.results['errors'].append(f"Test execution failed: {e}")
            raise
    
    def _test_backtest_mode_no_credentials(self):
        """Test that backtest mode requires no credentials."""
        print("\n📋 Testing backtest mode (no credentials required)...")
        
        # Set up backtest environment
        test_env = {
            'BASIS_ENVIRONMENT': 'dev',
            'BASIS_EXECUTION_MODE': 'backtest',
            'BASIS_DEPLOYMENT_MODE': 'local',
            'BASIS_DATA_DIR': '/tmp/test_data',
            'BASIS_RESULTS_DIR': '/tmp/test_results',
            'BASIS_DEBUG': 'true',
            'BASIS_LOG_LEVEL': 'DEBUG',
            'BASIS_DATA_MODE': 'csv',
            'BASIS_DATA_START_DATE': '2024-01-01',
            'BASIS_DATA_END_DATE': '2024-12-31',
            'BASIS_API_PORT': '8001',
            'BASIS_API_HOST': 'localhost',
            'BASIS_API_CORS_ORIGINS': 'http://localhost:3000',
            'HEALTH_CHECK_INTERVAL': '30s',
            'HEALTH_CHECK_ENDPOINT': '/health',
            'DATA_LOAD_TIMEOUT': '300',
            'DATA_VALIDATION_STRICT': 'true',
            'DATA_CACHE_SIZE': '1000',
            'STRATEGY_MANAGER_TIMEOUT': '30',
            'STRATEGY_MANAGER_MAX_RETRIES': '3',
            'STRATEGY_FACTORY_TIMEOUT': '30',
            'STRATEGY_FACTORY_MAX_RETRIES': '3'
        }
        
        # Clear any existing credentials
        for key in list(os.environ.keys()):
            if key.startswith('BASIS_DEV__') or key.startswith('BASIS_PROD__') or key.startswith('BASIS_STAGING__'):
                del os.environ[key]
        
        # Set test environment
        for key, value in test_env.items():
            os.environ[key] = value
        
        try:
            validator = ConfigValidator()
            result = validator.validate_all()
            
            if result.is_valid:
                self.results['backtest_mode_tests']['no_credentials'] = {
                    'status': 'success',
                    'message': 'Backtest mode correctly requires no credentials'
                }
                print("✅ Backtest mode validation passed - no credentials required")
            else:
                self.results['backtest_mode_tests']['no_credentials'] = {
                    'status': 'error',
                    'message': f'Backtest mode incorrectly failed validation: {result.errors}'
                }
                self.results['errors'].append(f"Backtest mode validation failed: {result.errors}")
                print(f"❌ Backtest mode validation failed: {result.errors}")
        
        except Exception as e:
            self.results['backtest_mode_tests']['no_credentials'] = {
                'status': 'error',
                'message': f'Backtest mode validation exception: {e}'
            }
            self.results['errors'].append(f"Backtest mode validation exception: {e}")
            print(f"❌ Backtest mode validation exception: {e}")
    
    def _test_live_mode_dev_credentials(self):
        """Test that live mode with dev environment requires dev credentials."""
        print("\n📋 Testing live mode with dev environment (dev credentials required)...")
        
        # Set up live dev environment
        test_env = {
            'BASIS_ENVIRONMENT': 'dev',
            'BASIS_EXECUTION_MODE': 'live',
            'BASIS_DEPLOYMENT_MODE': 'local',
            'BASIS_DATA_DIR': '/tmp/test_data',
            'BASIS_RESULTS_DIR': '/tmp/test_results',
            'BASIS_DEBUG': 'true',
            'BASIS_LOG_LEVEL': 'DEBUG',
            'BASIS_DATA_MODE': 'csv',
            'BASIS_DATA_START_DATE': '2024-01-01',
            'BASIS_DATA_END_DATE': '2024-12-31',
            'BASIS_API_PORT': '8001',
            'BASIS_API_HOST': 'localhost',
            'BASIS_API_CORS_ORIGINS': 'http://localhost:3000',
            'HEALTH_CHECK_INTERVAL': '30s',
            'HEALTH_CHECK_ENDPOINT': '/health',
            'DATA_LOAD_TIMEOUT': '300',
            'DATA_VALIDATION_STRICT': 'true',
            'DATA_CACHE_SIZE': '1000',
            'STRATEGY_MANAGER_TIMEOUT': '30',
            'STRATEGY_MANAGER_MAX_RETRIES': '3',
            'STRATEGY_FACTORY_TIMEOUT': '30',
            'STRATEGY_FACTORY_MAX_RETRIES': '3'
        }
        
        # Clear all credentials first
        for key in list(os.environ.keys()):
            if key.startswith('BASIS_DEV__') or key.startswith('BASIS_PROD__') or key.startswith('BASIS_STAGING__'):
                del os.environ[key]
        
        # Set test environment
        for key, value in test_env.items():
            os.environ[key] = value
        
        # Test 1: No credentials (should fail)
        try:
            validator = ConfigValidator()
            result = validator.validate_all()
            
            if not result.is_valid and any('Missing required environment variable for live mode' in error for error in result.errors):
                self.results['live_mode_tests']['dev_no_credentials'] = {
                    'status': 'success',
                    'message': 'Live dev mode correctly requires dev credentials'
                }
                print("✅ Live dev mode correctly failed without credentials")
            else:
                self.results['live_mode_tests']['dev_no_credentials'] = {
                    'status': 'error',
                    'message': f'Live dev mode should have failed without credentials: {result.errors}'
                }
                self.results['errors'].append(f"Live dev mode should have failed without credentials: {result.errors}")
                print(f"❌ Live dev mode should have failed without credentials: {result.errors}")
        
        except Exception as e:
            self.results['live_mode_tests']['dev_no_credentials'] = {
                'status': 'error',
                'message': f'Live dev mode validation exception: {e}'
            }
            self.results['errors'].append(f"Live dev mode validation exception: {e}")
            print(f"❌ Live dev mode validation exception: {e}")
        
        # Test 2: With dev credentials (should pass)
        dev_credentials = {
            'BASIS_DEV__ALCHEMY__PRIVATE_KEY': 'test_private_key',
            'BASIS_DEV__ALCHEMY__WALLET_ADDRESS': '0x1234567890123456789012345678901234567890',
            'BASIS_DEV__ALCHEMY__RPC_URL': 'https://eth-sepolia.g.alchemy.com/v2/test',
            'BASIS_DEV__ALCHEMY__NETWORK': 'sepolia',
            'BASIS_DEV__ALCHEMY__CHAIN_ID': '11155111',
            'BASIS_DEV__CEX__BINANCE_SPOT_API_KEY': 'test_binance_spot_key',
            'BASIS_DEV__CEX__BINANCE_SPOT_SECRET': 'test_binance_spot_secret',
            'BASIS_DEV__CEX__BINANCE_FUTURES_API_KEY': 'test_binance_futures_key',
            'BASIS_DEV__CEX__BINANCE_FUTURES_SECRET': 'test_binance_futures_secret',
            'BASIS_DEV__CEX__BYBIT_API_KEY': 'test_bybit_key',
            'BASIS_DEV__CEX__BYBIT_SECRET': 'test_bybit_secret',
            'BASIS_DEV__CEX__OKX_API_KEY': 'test_okx_key',
            'BASIS_DEV__CEX__OKX_SECRET': 'test_okx_secret',
            'BASIS_DEV__CEX__OKX_PASSPHRASE': 'test_okx_passphrase'
        }
        
        for key, value in dev_credentials.items():
            os.environ[key] = value
        
        try:
            validator = ConfigValidator()
            result = validator.validate_all()
            
            if result.is_valid:
                self.results['live_mode_tests']['dev_with_credentials'] = {
                    'status': 'success',
                    'message': 'Live dev mode correctly passed with dev credentials'
                }
                print("✅ Live dev mode correctly passed with dev credentials")
            else:
                self.results['live_mode_tests']['dev_with_credentials'] = {
                    'status': 'error',
                    'message': f'Live dev mode failed with credentials: {result.errors}'
                }
                self.results['errors'].append(f"Live dev mode failed with credentials: {result.errors}")
                print(f"❌ Live dev mode failed with credentials: {result.errors}")
        
        except Exception as e:
            self.results['live_mode_tests']['dev_with_credentials'] = {
                'status': 'error',
                'message': f'Live dev mode validation exception: {e}'
            }
            self.results['errors'].append(f"Live dev mode validation exception: {e}")
            print(f"❌ Live dev mode validation exception: {e}")
    
    def _test_live_mode_prod_credentials(self):
        """Test that live mode with prod environment requires prod credentials."""
        print("\n📋 Testing live mode with prod environment (prod credentials required)...")
        
        # Set up live prod environment
        test_env = {
            'BASIS_ENVIRONMENT': 'prod',
            'BASIS_EXECUTION_MODE': 'live',
            'BASIS_DEPLOYMENT_MODE': 'local',
            'BASIS_DATA_DIR': '/tmp/test_data',
            'BASIS_RESULTS_DIR': '/tmp/test_results',
            'BASIS_DEBUG': 'false',
            'BASIS_LOG_LEVEL': 'INFO',
            'BASIS_DATA_MODE': 'csv',
            'BASIS_DATA_START_DATE': '2024-01-01',
            'BASIS_DATA_END_DATE': '2024-12-31',
            'BASIS_API_PORT': '8001',
            'BASIS_API_HOST': 'localhost',
            'BASIS_API_CORS_ORIGINS': 'http://localhost:3000',
            'HEALTH_CHECK_INTERVAL': '30s',
            'HEALTH_CHECK_ENDPOINT': '/health',
            'DATA_LOAD_TIMEOUT': '300',
            'DATA_VALIDATION_STRICT': 'true',
            'DATA_CACHE_SIZE': '1000',
            'STRATEGY_MANAGER_TIMEOUT': '30',
            'STRATEGY_MANAGER_MAX_RETRIES': '3',
            'STRATEGY_FACTORY_TIMEOUT': '30',
            'STRATEGY_FACTORY_MAX_RETRIES': '3'
        }
        
        # Clear all credentials first
        for key in list(os.environ.keys()):
            if key.startswith('BASIS_DEV__') or key.startswith('BASIS_PROD__') or key.startswith('BASIS_STAGING__'):
                del os.environ[key]
        
        # Set test environment
        for key, value in test_env.items():
            os.environ[key] = value
        
        # Test: With prod credentials (should pass)
        prod_credentials = {
            'BASIS_PROD__ALCHEMY__PRIVATE_KEY': 'test_private_key',
            'BASIS_PROD__ALCHEMY__WALLET_ADDRESS': '0x1234567890123456789012345678901234567890',
            'BASIS_PROD__ALCHEMY__RPC_URL': 'https://eth-mainnet.g.alchemy.com/v2/test',
            'BASIS_PROD__ALCHEMY__NETWORK': 'mainnet',
            'BASIS_PROD__ALCHEMY__CHAIN_ID': '1',
            'BASIS_PROD__CEX__BINANCE_SPOT_API_KEY': 'test_binance_spot_key',
            'BASIS_PROD__CEX__BINANCE_SPOT_SECRET': 'test_binance_spot_secret',
            'BASIS_PROD__CEX__BINANCE_FUTURES_API_KEY': 'test_binance_futures_key',
            'BASIS_PROD__CEX__BINANCE_FUTURES_SECRET': 'test_binance_futures_secret',
            'BASIS_PROD__CEX__BYBIT_API_KEY': 'test_bybit_key',
            'BASIS_PROD__CEX__BYBIT_SECRET': 'test_bybit_secret',
            'BASIS_PROD__CEX__OKX_API_KEY': 'test_okx_key',
            'BASIS_PROD__CEX__OKX_SECRET': 'test_okx_secret',
            'BASIS_PROD__CEX__OKX_PASSPHRASE': 'test_okx_passphrase'
        }
        
        for key, value in prod_credentials.items():
            os.environ[key] = value
        
        try:
            validator = ConfigValidator()
            result = validator.validate_all()
            
            if result.is_valid:
                self.results['live_mode_tests']['prod_with_credentials'] = {
                    'status': 'success',
                    'message': 'Live prod mode correctly passed with prod credentials'
                }
                print("✅ Live prod mode correctly passed with prod credentials")
            else:
                self.results['live_mode_tests']['prod_with_credentials'] = {
                    'status': 'error',
                    'message': f'Live prod mode failed with credentials: {result.errors}'
                }
                self.results['errors'].append(f"Live prod mode failed with credentials: {result.errors}")
                print(f"❌ Live prod mode failed with credentials: {result.errors}")
        
        except Exception as e:
            self.results['live_mode_tests']['prod_with_credentials'] = {
                'status': 'error',
                'message': f'Live prod mode validation exception: {e}'
            }
            self.results['errors'].append(f"Live prod mode validation exception: {e}")
            print(f"❌ Live prod mode validation exception: {e}")
    
    def _test_live_mode_staging_credentials(self):
        """Test that live mode with staging environment requires staging credentials."""
        print("\n📋 Testing live mode with staging environment (staging credentials required)...")
        
        # Set up live staging environment
        test_env = {
            'BASIS_ENVIRONMENT': 'staging',
            'BASIS_EXECUTION_MODE': 'live',
            'BASIS_DEPLOYMENT_MODE': 'local',
            'BASIS_DATA_DIR': '/tmp/test_data',
            'BASIS_RESULTS_DIR': '/tmp/test_results',
            'BASIS_DEBUG': 'false',
            'BASIS_LOG_LEVEL': 'INFO',
            'BASIS_DATA_MODE': 'csv',
            'BASIS_DATA_START_DATE': '2024-01-01',
            'BASIS_DATA_END_DATE': '2024-12-31',
            'BASIS_API_PORT': '8001',
            'BASIS_API_HOST': 'localhost',
            'BASIS_API_CORS_ORIGINS': 'http://localhost:3000',
            'HEALTH_CHECK_INTERVAL': '30s',
            'HEALTH_CHECK_ENDPOINT': '/health',
            'DATA_LOAD_TIMEOUT': '300',
            'DATA_VALIDATION_STRICT': 'true',
            'DATA_CACHE_SIZE': '1000',
            'STRATEGY_MANAGER_TIMEOUT': '30',
            'STRATEGY_MANAGER_MAX_RETRIES': '3',
            'STRATEGY_FACTORY_TIMEOUT': '30',
            'STRATEGY_FACTORY_MAX_RETRIES': '3'
        }
        
        # Clear all credentials first
        for key in list(os.environ.keys()):
            if key.startswith('BASIS_DEV__') or key.startswith('BASIS_PROD__') or key.startswith('BASIS_STAGING__'):
                del os.environ[key]
        
        # Set test environment
        for key, value in test_env.items():
            os.environ[key] = value
        
        # Test: With staging credentials (should pass)
        staging_credentials = {
            'BASIS_STAGING__ALCHEMY__PRIVATE_KEY': 'test_private_key',
            'BASIS_STAGING__ALCHEMY__WALLET_ADDRESS': '0x1234567890123456789012345678901234567890',
            'BASIS_STAGING__ALCHEMY__RPC_URL': 'https://eth-mainnet.g.alchemy.com/v2/test',
            'BASIS_STAGING__ALCHEMY__NETWORK': 'mainnet',
            'BASIS_STAGING__ALCHEMY__CHAIN_ID': '1',
            'BASIS_STAGING__CEX__BINANCE_SPOT_API_KEY': 'test_binance_spot_key',
            'BASIS_STAGING__CEX__BINANCE_SPOT_SECRET': 'test_binance_spot_secret',
            'BASIS_STAGING__CEX__BINANCE_FUTURES_API_KEY': 'test_binance_futures_key',
            'BASIS_STAGING__CEX__BINANCE_FUTURES_SECRET': 'test_binance_futures_secret',
            'BASIS_STAGING__CEX__BYBIT_API_KEY': 'test_bybit_key',
            'BASIS_STAGING__CEX__BYBIT_SECRET': 'test_bybit_secret',
            'BASIS_STAGING__CEX__OKX_API_KEY': 'test_okx_key',
            'BASIS_STAGING__CEX__OKX_SECRET': 'test_okx_secret',
            'BASIS_STAGING__CEX__OKX_PASSPHRASE': 'test_okx_passphrase'
        }
        
        for key, value in staging_credentials.items():
            os.environ[key] = value
        
        try:
            validator = ConfigValidator()
            result = validator.validate_all()
            
            if result.is_valid:
                self.results['live_mode_tests']['staging_with_credentials'] = {
                    'status': 'success',
                    'message': 'Live staging mode correctly passed with staging credentials'
                }
                print("✅ Live staging mode correctly passed with staging credentials")
            else:
                self.results['live_mode_tests']['staging_with_credentials'] = {
                    'status': 'error',
                    'message': f'Live staging mode failed with credentials: {result.errors}'
                }
                self.results['errors'].append(f"Live staging mode failed with credentials: {result.errors}")
                print(f"❌ Live staging mode failed with credentials: {result.errors}")
        
        except Exception as e:
            self.results['live_mode_tests']['staging_with_credentials'] = {
                'status': 'error',
                'message': f'Live staging mode validation exception: {e}'
            }
            self.results['errors'].append(f"Live staging mode validation exception: {e}")
            print(f"❌ Live staging mode validation exception: {e}")
    
    def _test_invalid_execution_mode(self):
        """Test that invalid execution mode fails validation."""
        print("\n📋 Testing invalid execution mode...")
        
        # Set up environment with invalid execution mode
        test_env = {
            'BASIS_ENVIRONMENT': 'dev',
            'BASIS_EXECUTION_MODE': 'invalid_mode',
            'BASIS_DEPLOYMENT_MODE': 'local',
            'BASIS_DATA_DIR': '/tmp/test_data',
            'BASIS_RESULTS_DIR': '/tmp/test_results',
            'BASIS_DEBUG': 'true',
            'BASIS_LOG_LEVEL': 'DEBUG',
            'BASIS_DATA_MODE': 'csv',
            'BASIS_DATA_START_DATE': '2024-01-01',
            'BASIS_DATA_END_DATE': '2024-12-31',
            'BASIS_API_PORT': '8001',
            'BASIS_API_HOST': 'localhost',
            'BASIS_API_CORS_ORIGINS': 'http://localhost:3000',
            'HEALTH_CHECK_INTERVAL': '30s',
            'HEALTH_CHECK_ENDPOINT': '/health',
            'DATA_LOAD_TIMEOUT': '300',
            'DATA_VALIDATION_STRICT': 'true',
            'DATA_CACHE_SIZE': '1000',
            'STRATEGY_MANAGER_TIMEOUT': '30',
            'STRATEGY_MANAGER_MAX_RETRIES': '3',
            'STRATEGY_FACTORY_TIMEOUT': '30',
            'STRATEGY_FACTORY_MAX_RETRIES': '3'
        }
        
        # Clear all credentials first
        for key in list(os.environ.keys()):
            if key.startswith('BASIS_DEV__') or key.startswith('BASIS_PROD__') or key.startswith('BASIS_STAGING__'):
                del os.environ[key]
        
        # Set test environment
        for key, value in test_env.items():
            os.environ[key] = value
        
        try:
            validator = ConfigValidator()
            result = validator.validate_all()
            
            if not result.is_valid and any('Invalid BASIS_EXECUTION_MODE' in error for error in result.errors):
                self.results['live_mode_tests']['invalid_execution_mode'] = {
                    'status': 'success',
                    'message': 'Invalid execution mode correctly failed validation'
                }
                print("✅ Invalid execution mode correctly failed validation")
            else:
                self.results['live_mode_tests']['invalid_execution_mode'] = {
                    'status': 'error',
                    'message': f'Invalid execution mode should have failed: {result.errors}'
                }
                self.results['errors'].append(f"Invalid execution mode should have failed: {result.errors}")
                print(f"❌ Invalid execution mode should have failed: {result.errors}")
        
        except Exception as e:
            self.results['live_mode_tests']['invalid_execution_mode'] = {
                'status': 'error',
                'message': f'Invalid execution mode validation exception: {e}'
            }
            self.results['errors'].append(f"Invalid execution mode validation exception: {e}")
            print(f"❌ Invalid execution mode validation exception: {e}")
    
    def _generate_report(self):
        """Generate test report."""
        print("\n📋 MODE-DEPENDENT ENVIRONMENT VALIDATION TEST REPORT")
        print("=" * 60)
        
        # Count results
        total_errors = len(self.results['errors'])
        total_warnings = len(self.results['warnings'])
        
        print(f"📊 Summary:")
        print(f"  Errors: {total_errors}")
        print(f"  Warnings: {total_warnings}")
        
        if total_errors > 0:
            print("❌ Some tests failed!")
            for error in self.results['errors']:
                print(f"  - {error}")
        else:
            print("✅ All tests passed!")
        
        # Detailed results
        print(f"\n📋 Backtest Mode Tests: {len(self.results['backtest_mode_tests'])} tests")
        for test_name, result in self.results['backtest_mode_tests'].items():
            status_icon = "✅" if result['status'] == 'success' else "❌"
            print(f"  {status_icon} {test_name}: {result['message']}")
        
        print(f"\n📋 Live Mode Tests: {len(self.results['live_mode_tests'])} tests")
        for test_name, result in self.results['live_mode_tests'].items():
            status_icon = "✅" if result['status'] == 'success' else "❌"
            print(f"  {status_icon} {test_name}: {result['message']}")
        
        if total_errors > 0:
            sys.exit(1)


def main():
    """Main function."""
    validator = ModeDependentEnvValidator()
    validator.run_all_tests()


if __name__ == "__main__":
    main()
