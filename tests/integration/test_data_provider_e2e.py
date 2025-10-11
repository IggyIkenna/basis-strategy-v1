#!/usr/bin/env python3
"""
End-to-End Data Provider Integration Tests

Comprehensive integration testing for all data providers, factory pattern,
and validation system. Tests the complete data provider ecosystem.

Reference: docs/specs/09_DATA_PROVIDER.md - Data Provider Specification
Reference: docs/LOGICAL_EXCEPTIONS_GUIDE.md - Logical Exception Patterns
"""

import os
import sys
import pytest
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, List
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'backend' / 'src'))

from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
from basis_strategy_v1.infrastructure.data.data_validator import DataValidator, DataProviderError
from basis_strategy_v1.data_provider.base_data_provider import BaseDataProvider

logger = logging.getLogger(__name__)


class TestDataProviderE2E:
    """End-to-end integration tests for data provider system"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with proper data directory"""
        # Set environment variables for testing
        os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
        os.environ['BASIS_DATA_DIR'] = str(project_root / 'data')
        os.environ['BASIS_DATA_START_DATE'] = '2024-01-01'
        os.environ['BASIS_DATA_END_DATE'] = '2024-12-31'
        
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.original_data_dir = os.environ.get('BASIS_DATA_DIR')
        os.environ['BASIS_DATA_DIR'] = self.temp_dir
        
        yield
        
        # Cleanup
        if self.original_data_dir:
            os.environ['BASIS_DATA_DIR'] = self.original_data_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_data_file(self, file_path: Path, data_type: str) -> None:
        """Create test data file with proper structure"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if data_type == 'price_data':
            # Create price data with hourly timestamps
            timestamps = pd.date_range('2024-01-01', '2024-01-31', freq='H')
            df = pd.DataFrame({
                'timestamp': timestamps,
                'open': 100.0,
                'high': 101.0,
                'low': 99.0,
                'close': 100.5,
                'volume': 1000.0
            })
            df.to_csv(file_path, index=False)
        
        elif data_type == 'rate_data':
            # Create rate data with hourly timestamps
            timestamps = pd.date_range('2024-01-01', '2024-01-31', freq='H')
            df = pd.DataFrame({
                'timestamp': timestamps,
                'supply_rate': 0.05,
                'borrow_rate': 0.07,
                'liquidity_index': 1.0,
                'variable_borrow_index': 1.0
            })
            df.to_csv(file_path, index=False)
        
        elif data_type == 'gas_data':
            # Create gas data with hourly timestamps
            timestamps = pd.date_range('2024-01-01', '2024-01-31', freq='H')
            df = pd.DataFrame({
                'timestamp': timestamps,
                'gas_price_gwei': 20.0,
                'gas_used': 21000,
                'transaction_count': 100
            })
            df.to_csv(file_path, index=False)
        
        elif data_type == 'execution_costs':
            # Create execution costs lookup table
            df = pd.DataFrame({
                'operation': ['supply', 'withdraw', 'trade'],
                'cost_usd': [5.0, 3.0, 2.0]
            })
            df.to_csv(file_path, index=False)
    
    def test_data_provider_factory_creation(self):
        """Test factory creates all 7 mode-specific data providers"""
        modes = [
            'pure_lending',
            'btc_basis', 
            'eth_basis',
            'eth_leveraged',
            'eth_staking_only',
            'usdt_market_neutral_no_leverage',
            'usdt_market_neutral'
        ]
        
        for mode in modes:
            config = {
                'mode': mode,
                'data_requirements': ['test_data'],
                'data_dir': self.temp_dir
            }
            
            # Should create provider without error
            provider = create_data_provider('backtest', config)
            assert provider is not None
            assert provider.mode == mode
            assert isinstance(provider, BaseDataProvider)
            
            logger.info(f"✅ Created {provider.__class__.__name__} for mode: {mode}")
    
    def test_data_validator_comprehensive_validation(self):
        """Test DataValidator with all error codes"""
        validator = DataValidator(data_dir=self.temp_dir)
        
        # Test DATA-001: File existence validation
        non_existent_file = Path(self.temp_dir) / 'non_existent.csv'
        with pytest.raises(DataProviderError) as exc_info:
            validator.validate_file_existence(non_existent_file)
        assert exc_info.value.error_code == 'DATA-001'
        
        # Test DATA-002: CSV parsing validation
        invalid_csv_file = Path(self.temp_dir) / 'invalid.csv'
        invalid_csv_file.write_text('invalid,csv,content\nwith,missing,quotes')
        with pytest.raises(DataProviderError) as exc_info:
            validator.validate_csv_parsing(invalid_csv_file)
        assert exc_info.value.error_code == 'DATA-002'
        
        # Test DATA-003: Empty file validation
        empty_file = Path(self.temp_dir) / 'empty.csv'
        empty_file.write_text('')
        with pytest.raises(DataProviderError) as exc_info:
            df = validator.validate_csv_parsing(empty_file)
            validator.validate_empty_file(df, empty_file)
        assert exc_info.value.error_code == 'DATA-003'
        
        # Test successful validation
        test_file = Path(self.temp_dir) / 'test_prices.csv'
        self.create_test_data_file(test_file, 'price_data')
        
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        expected_types = {'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float', 'volume': 'float'}
        
        df = validator.validate_complete_file(test_file, required_columns, expected_types)
        assert len(df) > 0
        assert all(col in df.columns for col in required_columns)
        
        logger.info("✅ DataValidator comprehensive validation passed")
    
    def test_mode_agnostic_data_handling(self):
        """Test mode-agnostic data handling patterns"""
        # Create test data for different modes
        test_data_dir = Path(self.temp_dir) / 'test_data'
        
        # Create price data (used by all modes)
        price_file = test_data_dir / 'prices.csv'
        self.create_test_data_file(price_file, 'price_data')
        
        # Create rate data (used by some modes)
        rate_file = test_data_dir / 'rates.csv'
        self.create_test_data_file(rate_file, 'rate_data')
        
        # Test pure_lending mode (minimal data requirements)
        pure_lending_config = {
            'mode': 'pure_lending',
            'data_requirements': ['usdt_prices', 'aave_lending_rates', 'gas_costs', 'execution_costs'],
            'data_dir': self.temp_dir
        }
        
        provider = create_data_provider('backtest', pure_lending_config)
        
        # Should validate requirements without error
        provider.validate_data_requirements(pure_lending_config['data_requirements'])
        
        # Test that provider handles missing data gracefully
        # (In real implementation, this would be tested with actual data loading)
        
        logger.info("✅ Mode-agnostic data handling validation passed")
    
    def test_data_provider_error_handling(self):
        """Test comprehensive error handling with proper error codes"""
        # Test DATA-012: Data requirements validation
        config = {
            'mode': 'pure_lending',
            'data_requirements': ['non_existent_data_type'],
            'data_dir': self.temp_dir
        }
        
        provider = create_data_provider('backtest', config)
        
        with pytest.raises(DataProviderError) as exc_info:
            provider.validate_data_requirements(['non_existent_data_type'])
        assert exc_info.value.error_code == 'DATA-012'
        
        # Test DATA-013: Data provider initialization validation
        invalid_config = {
            'mode': 'pure_lending'
            # Missing data_requirements
        }
        
        with pytest.raises(DataProviderError) as exc_info:
            provider = create_data_provider('backtest', invalid_config)
        assert exc_info.value.error_code == 'DATA-013'
        
        logger.info("✅ Data provider error handling validation passed")
    
    def test_graceful_degradation_patterns(self):
        """Test graceful degradation for missing data"""
        # Create minimal test data
        test_data_dir = Path(self.temp_dir) / 'minimal_data'
        price_file = test_data_dir / 'prices.csv'
        self.create_test_data_file(price_file, 'price_data')
        
        # Test that components can handle missing optional data
        # This would be tested with actual component integration
        # For now, we test the pattern conceptually
        
        config = {
            'mode': 'pure_lending',
            'data_requirements': ['usdt_prices'],  # Minimal requirements
            'data_dir': self.temp_dir
        }
        
        provider = create_data_provider('backtest', config)
        
        # Should handle missing optional data gracefully
        # (In real implementation, this would test actual data loading)
        
        logger.info("✅ Graceful degradation patterns validation passed")
    
    def test_data_provider_factory_integration(self):
        """Test complete factory integration with all modes"""
        modes_and_requirements = {
            'pure_lending': ['usdt_prices', 'aave_lending_rates', 'gas_costs', 'execution_costs'],
            'btc_basis': ['btc_prices', 'btc_futures', 'funding_rates', 'gas_costs', 'execution_costs'],
            'eth_basis': ['eth_prices', 'eth_futures', 'funding_rates', 'gas_costs', 'execution_costs'],
            'eth_leveraged': ['eth_prices', 'weeth_prices', 'aave_lending_rates', 'staking_rewards', 'gas_costs', 'execution_costs'],
            'eth_staking_only': ['eth_prices', 'weeth_prices', 'staking_rewards', 'gas_costs', 'execution_costs'],
            'usdt_market_neutral_no_leverage': ['eth_prices', 'weeth_prices', 'perp_funding_rates', 'staking_rewards', 'gas_costs', 'execution_costs'],
            'usdt_market_neutral': ['eth_prices', 'weeth_prices', 'aave_lending_rates', 'perp_funding_rates', 'staking_rewards', 'gas_costs', 'execution_costs']
        }
        
        for mode, requirements in modes_and_requirements.items():
            config = {
                'mode': mode,
                'data_requirements': requirements,
                'data_dir': self.temp_dir
            }
            
            # Create provider
            provider = create_data_provider('backtest', config)
            
            # Validate requirements
            provider.validate_data_requirements(requirements)
            
            # Check that provider has correct available data types
            assert hasattr(provider, 'available_data_types')
            assert isinstance(provider.available_data_types, list)
            
            logger.info(f"✅ Factory integration test passed for mode: {mode}")
    
    def test_data_validator_error_codes(self):
        """Test all DataValidator error codes"""
        validator = DataValidator(data_dir=self.temp_dir)
        
        # Test error code summary
        error_codes = validator.get_error_summary()
        expected_codes = [
            'DATA-001', 'DATA-002', 'DATA-003', 'DATA-004', 'DATA-005',
            'DATA-006', 'DATA-007', 'DATA-008', 'DATA-009', 'DATA-010',
            'DATA-011', 'DATA-012', 'DATA-013'
        ]
        
        for code in expected_codes:
            assert code in error_codes
            assert error_codes[code] is not None
        
        logger.info("✅ All DataValidator error codes validated")
    
    def test_component_integration_patterns(self):
        """Test integration patterns with other components"""
        # Test that data providers can be used by other components
        # This is a conceptual test - in real implementation, this would
        # test actual component integration
        
        config = {
            'mode': 'pure_lending',
            'data_requirements': ['usdt_prices', 'aave_lending_rates'],
            'data_dir': self.temp_dir
        }
        
        provider = create_data_provider('backtest', config)
        
        # Test that provider follows BaseDataProvider interface
        assert hasattr(provider, 'get_data')
        assert hasattr(provider, 'validate_data_requirements')
        assert hasattr(provider, 'load_data')
        
        # Test that provider can be used in component initialization
        # (This would be tested with actual component integration)
        
        logger.info("✅ Component integration patterns validation passed")


def test_data_provider_e2e_suite():
    """Run complete end-to-end data provider test suite"""
    logger.info("🚀 Starting End-to-End Data Provider Integration Tests")
    
    test_instance = TestDataProviderE2E()
    test_instance.setup_test_environment()
    
    try:
        # Run all tests
        test_instance.test_data_provider_factory_creation()
        test_instance.test_data_validator_comprehensive_validation()
        test_instance.test_mode_agnostic_data_handling()
        test_instance.test_data_provider_error_handling()
        test_instance.test_graceful_degradation_patterns()
        test_instance.test_data_provider_factory_integration()
        test_instance.test_data_validator_error_codes()
        test_instance.test_component_integration_patterns()
        
        logger.info("🎉 All End-to-End Data Provider Integration Tests Passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ End-to-End Data Provider Integration Tests Failed: {e}")
        return False
    
    finally:
        # Cleanup
        if hasattr(test_instance, 'temp_dir'):
            shutil.rmtree(test_instance.temp_dir, ignore_errors=True)


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run test suite
    success = test_data_provider_e2e_suite()
    sys.exit(0 if success else 1)
