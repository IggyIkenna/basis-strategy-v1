#!/usr/bin/env python3
"""
Configuration Validation Quality Gates

Tests complete configuration loading from YAML files with full Pydantic validation
and fail-fast behavior for missing or invalid configuration fields.

Reference: .cursor/tasks/02_config_loading_validation.md
"""

import os
import sys
import tempfile
import shutil
import yaml
from pathlib import Path
from typing import Dict, Any
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from basis_strategy_v1.infrastructure.config.config_loader import (
    ConfigLoader, 
    ConfigurationValidationError
)
from basis_strategy_v1.infrastructure.config.models import (
    ModeConfig, VenueConfig, ShareClassConfig, ConfigurationSet,
    ConfigurationValidationError as ModelValidationError
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConfigValidationQualityGates:
    """Quality gates for configuration validation functionality."""
    
    def __init__(self):
        self.results = {
            'overall_status': 'PENDING',
            'gates_passed': 0,
            'gates_failed': 0,
            'gate_results': {},
            'summary': {},
            'timestamp': None
        }
        self.temp_dir = None
        self.original_cwd = None
    
    def run_all_quality_gates(self) -> Dict[str, Any]:
        """Run all quality gates and return comprehensive results."""
        logger.info("🚀 Starting Configuration Validation Quality Gates")
        logger.info("=" * 80)
        
        try:
            # Setup test environment
            self._setup_test_environment()
            
            # Run quality gates
            quality_gates = [
                ('QG1', 'Valid Configuration Loading', self._test_valid_config_loading),
                ('QG2', 'Pydantic Model Validation', self._test_pydantic_validation),
                ('QG3', 'Fail-Fast on Missing Files', self._test_fail_fast_missing_files),
                ('QG4', 'Fail-Fast on Invalid YAML', self._test_fail_fast_invalid_yaml),
                ('QG5', 'Fail-Fast on Missing Fields', self._test_fail_fast_missing_fields),
                ('QG6', 'Cross-Reference Validation', self._test_cross_reference_validation),
                ('QG7', 'Business Logic Validation', self._test_business_logic_validation),
                ('QG8', 'Integration Test', self._test_integration)
            ]
            
            for gate_id, gate_name, gate_test in quality_gates:
                logger.info(f"🔄 Running {gate_id}: {gate_name}")
                try:
                    result = gate_test()
                    self.results['gate_results'][gate_id] = {
                        'name': gate_name,
                        'status': 'PASS' if result else 'FAIL',
                        'details': result if isinstance(result, dict) else {}
                    }
                    if result:
                        self.results['gates_passed'] += 1
                        logger.info(f"✅ {gate_id}: {gate_name} - PASSED")
                    else:
                        self.results['gates_failed'] += 1
                        logger.error(f"❌ {gate_id}: {gate_name} - FAILED")
                except Exception as e:
                    self.results['gate_results'][gate_id] = {
                        'name': gate_name,
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    self.results['gates_failed'] += 1
                    logger.error(f"💥 {gate_id}: {gate_name} - ERROR: {e}")
            
            # Determine overall status
            total_gates = self.results['gates_passed'] + self.results['gates_failed']
            if self.results['gates_failed'] == 0:
                self.results['overall_status'] = 'PASS'
            else:
                self.results['overall_status'] = 'FAIL'
            
            self.results['summary'] = {
                'total_gates': total_gates,
                'passed': self.results['gates_passed'],
                'failed': self.results['gates_failed'],
                'pass_rate': (self.results['gates_passed'] / total_gates * 100) if total_gates > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"💥 Quality gates setup failed: {e}")
            self.results['overall_status'] = 'ERROR'
            self.results['error'] = str(e)
        
        finally:
            self._cleanup_test_environment()
        
        return self.results
    
    def _setup_test_environment(self):
        """Setup temporary test environment with test files."""
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp(prefix="config_test_")
        os.chdir(self.temp_dir)
        
        # Set environment variables for the test
        os.environ['BASIS_ENVIRONMENT'] = 'test'
        os.environ['BASIS_DEPLOYMENT_MODE'] = 'local'
        os.environ['BASIS_DEPLOYMENT_MACHINE'] = 'local_mac'
        os.environ['BASIS_DATA_DIR'] = '/test/data'
        os.environ['BASIS_DATA_MODE'] = 'csv'
        os.environ['BASIS_RESULTS_DIR'] = '/test/results'
        os.environ['BASIS_DEBUG'] = 'true'
        os.environ['BASIS_LOG_LEVEL'] = 'DEBUG'
        os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
        os.environ['BASIS_DATA_START_DATE'] = '2024-01-01'
        os.environ['BASIS_DATA_END_DATE'] = '2024-12-31'
        os.environ['HEALTH_CHECK_INTERVAL'] = '30s'
        os.environ['HEALTH_CHECK_ENDPOINT'] = '/health'
        os.environ['BASIS_API_PORT'] = '8001'
        os.environ['BASIS_API_HOST'] = '0.0.0.0'
        os.environ['BASIS_API_CORS_ORIGINS'] = 'http://localhost:3000'
        os.environ['APP_DOMAIN'] = 'localhost'
        os.environ['ACME_EMAIL'] = 'test@example.com'
        os.environ['HTTP_PORT'] = '80'
        os.environ['HTTPS_PORT'] = '443'
        
        # Create test config directories
        os.makedirs("configs/modes", exist_ok=True)
        os.makedirs("configs/venues", exist_ok=True)
        os.makedirs("configs/share_classes", exist_ok=True)
        
        # Create test configuration files
        self._create_test_config_files()
        
        logger.info(f"📁 Test environment setup: {self.temp_dir}")
    
    def _create_test_config_files(self):
        """Create test configuration files."""
        # Create test mode config
        mode_config = {
            'mode': 'test_mode',
            'lending_enabled': True,
            'staking_enabled': False,
            'basis_trade_enabled': False,
            'borrowing_enabled': False,
            'enable_market_impact': True,
            'share_class': 'USDT',
            'asset': 'USDT',
            'lst_type': None,
            'rewards_mode': 'base_only',
            'reserve_ratio': 0.1,
            'position_deviation_threshold': 0.02,
            'margin_ratio_target': 1.0,
            'target_apy': 0.05,
            'max_drawdown': 0.005,
            'time_throttle_interval': 60,
            'data_requirements': ['usdt_prices', 'aave_lending_rates']
        }
        
        with open("configs/modes/test_mode.yaml", "w") as f:
            yaml.dump(mode_config, f)
        
        # Create test venue config
        venue_config = {
            'venue': 'test_venue',
            'type': 'CEX',
            'network': 'testnet',
            'chain_id': 1,
            'min_trade_size': 10.0,
            'max_trade_size': 10000.0,
            'trading_fee': 0.001
        }
        
        with open("configs/venues/test_venue.yaml", "w") as f:
            yaml.dump(venue_config, f)
        
        # Create test share class config
        share_class_config = {
            'share_class': 'USDT',
            'type': 'stable',
            'base_currency': 'USDT',
            'supported_strategies': ['test_mode'],
            'leverage_supported': False,
            'target_apy_range': {'min': 0.03, 'max': 0.08},
            'max_drawdown_limit': 0.01
        }
        
        with open("configs/share_classes/test_share_class.yaml", "w") as f:
            yaml.dump(share_class_config, f)
    
    def _cleanup_test_environment(self):
        """Cleanup test environment."""
        if self.original_cwd:
            os.chdir(self.original_cwd)
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Clean up environment variables
        env_vars_to_remove = [
            'BASIS_ENVIRONMENT', 'BASIS_DEPLOYMENT_MODE', 'BASIS_DEPLOYMENT_MACHINE',
            'BASIS_DATA_DIR', 'BASIS_DATA_MODE', 'BASIS_RESULTS_DIR', 'BASIS_DEBUG',
            'BASIS_LOG_LEVEL', 'BASIS_EXECUTION_MODE', 'BASIS_DATA_START_DATE',
            'BASIS_DATA_END_DATE', 'HEALTH_CHECK_INTERVAL', 'HEALTH_CHECK_ENDPOINT',
            'BASIS_API_PORT', 'BASIS_API_HOST', 'BASIS_API_CORS_ORIGINS',
            'APP_DOMAIN', 'ACME_EMAIL', 'HTTP_PORT', 'HTTPS_PORT'
        ]
        
        for var in env_vars_to_remove:
            if var in os.environ:
                del os.environ[var]
    
    def _test_valid_config_loading(self) -> bool:
        """Test that valid configurations load correctly."""
        try:
            loader = ConfigLoader()
            
            # Test mode config loading
            mode_config = loader.get_mode_config('pure_lending')
            assert isinstance(mode_config, ModeConfig)
            assert mode_config.mode == 'pure_lending'
            assert mode_config.share_class == 'USDT'
            
            # Test venue config loading
            venue_config = loader.get_venue_config('binance')
            assert isinstance(venue_config, VenueConfig)
            assert venue_config.venue == 'binance'
            assert venue_config.type == 'cex'
            
            # Test share class config loading
            share_class_config = loader.get_share_class_config('usdt_stable')
            assert isinstance(share_class_config, ShareClassConfig)
            assert share_class_config.share_class == 'USDT'
            assert share_class_config.base_currency == 'USDT'
            
            return True
            
        except Exception as e:
            logger.error(f"Valid config loading test failed: {e}")
            return False
    
    def _test_pydantic_validation(self) -> bool:
        """Test that Pydantic validation works correctly."""
        try:
            # Test valid mode config
            valid_config = {
                'mode': 'pure_lending',
                'lending_enabled': True,
                'staking_enabled': False,
                'basis_trade_enabled': False,
                'borrowing_enabled': False,
                'enable_market_impact': True,
                'share_class': 'USDT',
                'asset': 'USDT',
                'lst_type': None,
                'rewards_mode': 'base_only',
                'reserve_ratio': 0.1,
                'position_deviation_threshold': 0.02,
                'margin_ratio_target': 1.0,
                'target_apy': 0.05,
                'max_drawdown': 0.005,
                'time_throttle_interval': 60,
                'data_requirements': ['usdt_prices']
            }
            
            mode_config = ModeConfig(**valid_config)
            assert mode_config.mode == 'pure_lending'
            
            # Test invalid mode config (should fail)
            invalid_config = valid_config.copy()
            invalid_config['share_class'] = 'INVALID'  # Invalid share class
            
            try:
                ModeConfig(**invalid_config)
                return False  # Should have failed
            except ModelValidationError:
                return True  # Expected failure
            
        except Exception as e:
            logger.error(f"Pydantic validation test failed: {e}")
            return False
    
    def _test_fail_fast_missing_files(self) -> bool:
        """Test that missing configuration files cause immediate failure."""
        try:
            # Remove a required config file
            os.remove("configs/modes/test_mode.yaml")
            
            # Test that loading fails
            try:
                ConfigLoader()
                return False  # Should have failed
            except ConfigurationValidationError as e:
                assert "not found" in str(e).lower() or "missing" in str(e).lower()
                return True
            
        except Exception as e:
            logger.error(f"Fail-fast missing files test failed: {e}")
            return False
    
    def _test_fail_fast_invalid_yaml(self) -> bool:
        """Test that invalid YAML files cause immediate failure."""
        try:
            # Create invalid YAML file
            with open("configs/modes/invalid.yaml", "w") as f:
                f.write("invalid: yaml: content: [")
            
            # Test that loading fails
            try:
                ConfigLoader()
                return False  # Should have failed
            except ConfigurationValidationError as e:
                return True
            
        except Exception as e:
            logger.error(f"Fail-fast invalid YAML test failed: {e}")
            return False
    
    def _test_fail_fast_missing_fields(self) -> bool:
        """Test that missing required fields cause immediate failure."""
        try:
            # Create config with missing required fields
            incomplete_config = {
                'mode': 'incomplete_mode',
                'lending_enabled': True,
                # Missing many required fields
            }
            
            with open("configs/modes/incomplete_mode.yaml", "w") as f:
                yaml.dump(incomplete_config, f)
            
            # Test that loading fails
            try:
                ConfigLoader()
                return False  # Should have failed
            except ConfigurationValidationError as e:
                return True
            
        except Exception as e:
            logger.error(f"Fail-fast missing fields test failed: {e}")
            return False
    
    def _test_cross_reference_validation(self) -> bool:
        """Test that cross-references between configurations are validated."""
        try:
            # Create mode config that references non-existent share class
            invalid_mode_config = {
                'mode': 'invalid_mode',
                'lending_enabled': True,
                'staking_enabled': False,
                'basis_trade_enabled': False,
                'borrowing_enabled': False,
                'enable_market_impact': True,
                'share_class': 'NONEXISTENT',  # Invalid share class reference
                'asset': 'USDT',
                'lst_type': None,
                'rewards_mode': 'base_only',
                'reserve_ratio': 0.1,
                'position_deviation_threshold': 0.02,
                'margin_ratio_target': 1.0,
                'target_apy': 0.05,
                'max_drawdown': 0.005,
                'time_throttle_interval': 60,
                'data_requirements': ['usdt_prices']
            }
            
            with open("configs/modes/invalid_mode.yaml", "w") as f:
                yaml.dump(invalid_mode_config, f)
            
            # Test that loading fails due to cross-reference validation
            try:
                ConfigLoader()
                return False  # Should have failed
            except ConfigurationValidationError as e:
                return True
            
        except Exception as e:
            logger.error(f"Cross-reference validation test failed: {e}")
            return False
    
    def _test_business_logic_validation(self) -> bool:
        """Test that business logic constraints are validated."""
        try:
            # Create mode config that violates business logic (ETH share class with basis trading)
            invalid_mode_config = {
                'mode': 'invalid_business_logic',
                'lending_enabled': True,
                'staking_enabled': False,
                'basis_trade_enabled': True,  # Invalid: basis trading enabled
                'borrowing_enabled': False,
                'enable_market_impact': True,
                'share_class': 'ETH',  # ETH share class cannot have basis trading
                'asset': 'ETH',
                'lst_type': None,
                'rewards_mode': 'base_only',
                'reserve_ratio': 0.1,
                'position_deviation_threshold': 0.02,
                'margin_ratio_target': 1.0,
                'target_apy': 0.05,
                'max_drawdown': 0.005,
                'time_throttle_interval': 60,
                'data_requirements': ['eth_prices']
            }
            
            with open("configs/modes/invalid_business_logic.yaml", "w") as f:
                yaml.dump(invalid_mode_config, f)
            
            # Create corresponding share class config
            share_class_config = {
                'share_class': 'ETH',
                'type': 'directional',
                'base_currency': 'ETH',
                'supported_strategies': ['invalid_business_logic'],
                'leverage_supported': False,
                'target_apy_range': {'min': 0.05, 'max': 0.15},
                'max_drawdown_limit': 0.02
            }
            
            with open("configs/share_classes/eth_share_class.yaml", "w") as f:
                yaml.dump(share_class_config, f)
            
            # Test that loading fails due to business logic validation
            try:
                ConfigLoader()
                return False  # Should have failed
            except ConfigurationValidationError as e:
                return True
            
        except Exception as e:
            logger.error(f"Business logic validation test failed: {e}")
            return False
    
    def _test_integration(self) -> bool:
        """Test integration with global loader functions."""
        try:
            loader = ConfigLoader()
            
            # Test getting all configurations
            all_modes = loader.get_all_mode_configs()
            assert len(all_modes) > 0
            
            all_venues = loader.get_all_venue_configs()
            assert len(all_venues) > 0
            
            all_share_classes = loader.get_all_share_class_configs()
            assert len(all_share_classes) > 0
            
            # Test getting Pydantic configuration set
            pydantic_config = loader.get_pydantic_config()
            assert isinstance(pydantic_config, ConfigurationSet)
            
            return True
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            return False


def main():
    """Main function to run quality gates."""
    quality_gates = ConfigValidationQualityGates()
    results = quality_gates.run_all_quality_gates()
    
    # Print results
    print("\n" + "=" * 80)
    print("🚦 CONFIGURATION VALIDATION QUALITY GATES RESULTS")
    print("=" * 80)
    
    print(f"Overall Status: {results['overall_status']}")
    print(f"Gates Passed: {results['gates_passed']}")
    print(f"Gates Failed: {results['gates_failed']}")
    
    if 'summary' in results:
        summary = results['summary']
        print(f"Pass Rate: {summary['pass_rate']:.1f}%")
    
    print("\nGate Results:")
    for gate_id, gate_result in results['gate_results'].items():
        status = gate_result['status']
        name = gate_result['name']
        print(f"  {gate_id}: {name} - {status}")
        if 'error' in gate_result:
            print(f"    Error: {gate_result['error']}")
    
    if results['overall_status'] == 'PASS':
        print("\n🎉 All configuration validation quality gates passed!")
        return 0
    else:
        print(f"\n❌ {results['gates_failed']} configuration validation quality gates failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())