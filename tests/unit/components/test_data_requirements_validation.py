#!/usr/bin/env python3
"""
Test data requirements validation functionality with proper mocking.
"""

import pytest
from pathlib import Path
import sys
import os
from unittest.mock import Mock, patch
import pandas as pd

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider


class TestDataRequirementsValidation:
    """Test data requirements validation with proper mocking."""
    
    @pytest.fixture
    def mock_data_provider(self):
        """Create a mock DataProvider with mocked data loading."""
        provider = DataProvider.__new__(DataProvider)
        provider.data_dir = Path('/workspace/data')
        provider.data = {}
        provider.mode = 'eth_leveraged'
        
        # Mock config with data requirements
        config = {
            'data_requirements': [
                'eth_prices',
                'weeth_prices', 
                'aave_lending_rates',
                'staking_rewards',
                'gas_costs',
                'execution_costs',
                'aave_risk_params',
                'lst_market_prices'
            ]
        }
        provider.config = type('Config', (), config)()
        
        return provider
    
    def test_validation_with_all_requirements_met(self, mock_data_provider):
        """Test validation when all required data is loaded."""
        provider = mock_data_provider
        
        # Mock the data loading by actually putting data into the provider
        provider.data = {
            'eth_spot_binance': pd.DataFrame({'price': [2000.0]}),
            'weeth_oracle': pd.DataFrame({'price': [2000.0]}),
            'weeth_rates': pd.DataFrame({'rate': [0.05]}),
            'weth_rates': pd.DataFrame({'rate': [0.05]}),
            'usdt_rates': pd.DataFrame({'rate': [0.05]}),
            'staking_yields': pd.DataFrame({'yield': [0.05]}),
            'gas_costs': pd.DataFrame({'cost': [0.01]}),
            'execution_costs': pd.DataFrame({'cost': [0.01]}),
            'weeth_market_price': pd.DataFrame({'price': [2000.0]}),
            'wsteth_market_price': pd.DataFrame({'price': [2000.0]})
        }
        provider.aave_risk_params = {'emode': {}, 'normal_mode': {}, 'metadata': {}}
        
        # Test validation - should pass
        result = provider._validate_data_requirements()
        assert result is True
        
        print("✅ Validation passed with all requirements met")
    
    def test_validation_with_missing_requirements(self, mock_data_provider):
        """Test validation when some required data is missing."""
        provider = mock_data_provider
        
        # Mock only some data (missing aave_risk_params and lst_market_prices)
        provider.data = {
            'eth_spot_binance': pd.DataFrame({'price': [2000.0]}),
            'weeth_oracle': pd.DataFrame({'price': [2000.0]}),
            'weeth_rates': pd.DataFrame({'rate': [0.05]}),
            'weth_rates': pd.DataFrame({'rate': [0.05]}),
            'usdt_rates': pd.DataFrame({'rate': [0.05]}),
            'staking_yields': pd.DataFrame({'yield': [0.05]}),
            'gas_costs': pd.DataFrame({'cost': [0.01]}),
            'execution_costs': pd.DataFrame({'cost': [0.01]})
            # Missing: aave_risk_params, lst_market_prices
        }
        
        # Test validation - should fail
        result = provider._validate_data_requirements()
        assert result is False
        
        print("✅ Validation failed with missing requirements")
    
    def test_validation_with_no_requirements(self, mock_data_provider):
        """Test validation when no data requirements are specified."""
        provider = mock_data_provider
        
        # Mock config with no data requirements
        config = {'data_requirements': []}
        provider.config = type('Config', (), config)()
        
        # Test validation - should pass
        result = provider._validate_data_requirements()
        assert result is True
        
        print("✅ Validation passed with no requirements")
    
    def test_validation_with_unknown_requirements(self, mock_data_provider):
        """Test validation with unknown data requirements."""
        provider = mock_data_provider
        
        # Mock config with unknown data requirements
        config = {
            'data_requirements': [
                'eth_prices',  # Valid
                'unknown_requirement'  # Invalid
            ]
        }
        provider.config = type('Config', (), config)()
        
        # Mock only the valid requirement
        provider.data = {
            'eth_spot_binance': pd.DataFrame({'price': [2000.0]})
        }
        
        # Test validation - should fail due to unknown requirement
        result = provider._validate_data_requirements()
        assert result is False
        
        print("✅ Validation failed with unknown requirements")
    
    def test_validation_with_list_requirements(self, mock_data_provider):
        """Test validation with list-based requirements (like aave_lending_rates)."""
        provider = mock_data_provider
        
        # Mock config with list-based requirements
        config = {
            'data_requirements': [
                'aave_lending_rates'  # Maps to ['weeth_rates', 'wsteth_rates', 'weth_rates', 'usdt_rates']
            ]
        }
        provider.config = type('Config', (), config)()
        
        # Mock loading one of the required rates (should be sufficient)
        provider.data = {
            'weeth_rates': pd.DataFrame({'rate': [0.05]})
        }
        
        # Test validation - should pass
        result = provider._validate_data_requirements()
        assert result is True
        
        print("✅ Validation passed with list requirements")
    
    def test_validation_with_missing_list_requirements(self, mock_data_provider):
        """Test validation when list-based requirements are missing."""
        provider = mock_data_provider
        
        # Mock config with list-based requirements
        config = {
            'data_requirements': [
                'aave_lending_rates'  # Maps to ['weeth_rates', 'wsteth_rates', 'weth_rates', 'usdt_rates']
            ]
        }
        provider.config = type('Config', (), config)()
        
        # Don't load any of the required rates
        
        # Test validation - should fail
        result = provider._validate_data_requirements()
        assert result is False
        
        print("✅ Validation failed with missing list requirements")
    
    def test_validation_integration_with_mode_loading(self, mock_data_provider):
        """Test validation integration with mode-based data loading."""
        provider = mock_data_provider
        
        # Mock all required data
        provider.data = {
            'eth_spot_binance': pd.DataFrame({'price': [2000.0]}),
            'weeth_oracle': pd.DataFrame({'price': [2000.0]}),
            'weeth_rates': pd.DataFrame({'rate': [0.05]}),
            'weth_rates': pd.DataFrame({'rate': [0.05]}),
            'usdt_rates': pd.DataFrame({'rate': [0.05]}),
            'staking_yields': pd.DataFrame({'yield': [0.05]}),
            'gas_costs': pd.DataFrame({'cost': [0.01]}),
            'execution_costs': pd.DataFrame({'cost': [0.01]}),
            'weeth_market_price': pd.DataFrame({'price': [2000.0]}),
            'wsteth_market_price': pd.DataFrame({'price': [2000.0]})
        }
        provider.aave_risk_params = {'emode': {}, 'normal_mode': {}, 'metadata': {}}
        
        # Test validation - should pass
        result = provider._validate_data_requirements()
        assert result is True
        
        print("✅ Validation passed with mode-based loading")


if __name__ == "__main__":
    # Run tests
    test_instance = TestDataRequirementsValidation()
    
    print("🧪 Testing Data Requirements Validation...")
    
    try:
        # Create mock provider
        mock_provider = test_instance.mock_data_provider()
        
        test_instance.test_validation_with_all_requirements_met(mock_provider)
        test_instance.test_validation_with_missing_requirements(mock_provider)
        test_instance.test_validation_with_no_requirements(mock_provider)
        test_instance.test_validation_with_unknown_requirements(mock_provider)
        test_instance.test_validation_with_list_requirements(mock_provider)
        test_instance.test_validation_with_missing_list_requirements(mock_provider)
        test_instance.test_validation_integration_with_mode_loading(mock_provider)
        
        print("\n✅ All data requirements validation tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()