#!/usr/bin/env python3
"""
Test AAVE risk parameters loading functionality with proper mocking.
"""

import pytest
import json
from pathlib import Path
import sys
import os
from unittest.mock import Mock, patch

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider


class TestAAVERiskParameters:
    """Test AAVE risk parameters loading and access with proper mocking."""
    
    @pytest.fixture
    def mock_risk_params(self):
        """Mock AAVE risk parameters data."""
        return {
            'emode': {
                'liquidation_thresholds': {'weETH_WETH': 0.95, 'wstETH_WETH': 0.93},
                'ltv_limits': {'weETH_WETH': 0.91, 'wstETH_WETH': 0.89},
                'liquidation_bonus': {'weETH_WETH': 0.05, 'wstETH_WETH': 0.05},
                'eligible_pairs': ['weETH_WETH', 'wstETH_WETH']
            },
                   'standard': {
                       'liquidation_thresholds': {'WETH': 0.85, 'wstETH': 0.80, 'weETH': 0.80, 'USDT': 0.90},
                       'ltv_limits': {'WETH': 0.80, 'wstETH': 0.75, 'weETH': 0.75, 'USDT': 0.85},
                       'liquidation_bonus': {'WETH': 0.05, 'wstETH': 0.05, 'weETH': 0.05, 'USDT': 0.05}
                   },
            'reserve_factors': {
                'weETH': 0.10,
                'wstETH': 0.10,
                'WETH': 0.10,
                'USDT': 0.10
            }
        }
    
    @pytest.fixture
    def mock_provider(self, mock_risk_params):
        """Create a mock DataProvider with mocked data loading."""
        with patch('builtins.open', create=True), \
             patch('json.load', return_value=mock_risk_params), \
             patch('pathlib.Path.exists', return_value=True):
            
            provider = DataProvider.__new__(DataProvider)
            provider.data_dir = Path('/workspace/data')
            provider.data = {}
            provider._load_aave_risk_parameters()
            return provider
    
    def test_load_aave_risk_parameters(self, mock_risk_params):
        """Test loading AAVE risk parameters from JSON."""
        with patch('builtins.open', create=True), \
             patch('json.load', return_value=mock_risk_params), \
             patch('pathlib.Path.exists', return_value=True):
            
            provider = DataProvider.__new__(DataProvider)
            provider.data_dir = Path('/workspace/data')
            provider.data = {}
            
            # Load AAVE risk parameters
            provider._load_aave_risk_parameters()
            
            # Verify data is loaded
            assert hasattr(provider, 'aave_risk_params')
            risk_params = provider.aave_risk_params
            
            # Verify structure
            assert 'emode' in risk_params
            assert 'normal_mode' in risk_params
            assert 'metadata' in risk_params
            
            print("✅ AAVE risk parameters loaded successfully")
    
    def test_get_aave_risk_params_access(self, mock_provider):
        """Test accessing AAVE risk parameters."""
        # Test access method
        risk_params = mock_provider.get_aave_risk_params()
        assert isinstance(risk_params, dict)
        
        print("✅ AAVE risk parameters access works")
    
    def test_emode_parameters(self, mock_provider):
        """Test eMode specific parameters."""
        risk_params = mock_provider.get_aave_risk_params()
        
        # Test eMode structure
        emode = risk_params['emode']
        assert 'liquidation_thresholds' in emode
        assert 'max_ltv_limits' in emode
        assert 'liquidation_bonus' in emode
        assert 'eligible_pairs' in emode
        
        # Test specific values for weETH_WETH pair
        weeth_pair = 'weETH_WETH'
        assert weeth_pair in emode['liquidation_thresholds']
        assert weeth_pair in emode['max_ltv_limits']
        assert weeth_pair in emode['liquidation_bonus']
        
        # Verify reasonable values
        ltv = emode['max_ltv_limits'][weeth_pair]
        liquidation_threshold = emode['liquidation_thresholds'][weeth_pair]
        liquidation_bonus = emode['liquidation_bonus'][weeth_pair]
        
        assert 0.8 <= ltv <= 1.0  # LTV should be between 80-100%
        assert 0.8 <= liquidation_threshold <= 1.0  # Liquidation threshold should be between 80-100%
        assert 0.0 <= liquidation_bonus <= 0.1  # Liquidation bonus should be between 0-10%
        
        print(f"✅ eMode parameters for {weeth_pair}:")
        print(f"   Max LTV: {ltv}")
        print(f"   Liquidation Threshold: {liquidation_threshold}")
        print(f"   Liquidation Bonus: {liquidation_bonus}")
    
    def test_wsteth_parameters(self, mock_provider):
        """Test wstETH specific parameters."""
        risk_params = mock_provider.get_aave_risk_params()
        
        # Test wstETH_WETH pair
        wsteth_pair = 'wstETH_WETH'
        emode = risk_params['emode']
        
        assert wsteth_pair in emode['liquidation_thresholds']
        assert wsteth_pair in emode['max_ltv_limits']
        assert wsteth_pair in emode['liquidation_bonus']
        
        # Verify reasonable values
        ltv = emode['max_ltv_limits'][wsteth_pair]
        liquidation_threshold = emode['liquidation_thresholds'][wsteth_pair]
        liquidation_bonus = emode['liquidation_bonus'][wsteth_pair]
        
        assert 0.8 <= ltv <= 1.0
        assert 0.8 <= liquidation_threshold <= 1.0
        assert 0.0 <= liquidation_bonus <= 0.1
        
        print(f"✅ eMode parameters for {wsteth_pair}:")
        print(f"   Max LTV: {ltv}")
        print(f"   Liquidation Threshold: {liquidation_threshold}")
        print(f"   Liquidation Bonus: {liquidation_bonus}")
    
    def test_normal_mode_parameters(self, mock_provider):
        """Test normal mode parameters."""
        risk_params = mock_provider.get_aave_risk_params()
        
        # Test normal mode structure
        normal_mode = risk_params['normal_mode']
        assert 'liquidation_thresholds' in normal_mode
        assert 'max_ltv_limits' in normal_mode
        
        # Test specific assets
        assert 'WETH' in normal_mode['liquidation_thresholds']
        assert 'wstETH' in normal_mode['liquidation_thresholds']
        assert 'weETH' in normal_mode['liquidation_thresholds']
        assert 'USDT' in normal_mode['liquidation_thresholds']
        
        print("✅ Normal mode parameters loaded successfully")
    
    def test_metadata(self, mock_provider):
        """Test metadata information."""
        risk_params = mock_provider.get_aave_risk_params()
        
        # Test metadata
        metadata = risk_params['metadata']
        assert 'created' in metadata
        assert 'source' in metadata
        assert 'description' in metadata
        assert 'version' in metadata
        
        print("✅ Metadata loaded successfully")
        print(f"   Version: {metadata['version']}")
        print(f"   Source: {metadata['source']}")
    
    def test_error_handling(self):
        """Test error handling for missing risk parameters."""
        provider = DataProvider.__new__(DataProvider)
        provider.data_dir = Path('/workspace/data')
        provider.data = {}
        
        # Test accessing without loading
        with pytest.raises(ValueError, match="AAVE risk parameters not loaded"):
            provider.get_aave_risk_params()
        
        print("✅ Error handling works correctly")
    
    def test_file_not_found_error(self):
        """Test error handling when risk parameters file is not found."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            provider = DataProvider.__new__(DataProvider)
            provider.data_dir = Path('/workspace/data')
            provider.data = {}
            
            with pytest.raises(FileNotFoundError):
                provider._load_aave_risk_parameters()
        
        print("✅ File not found error handling works correctly")


if __name__ == "__main__":
    # Run tests
    test_instance = TestAAVERiskParameters()
    
    print("🧪 Testing AAVE Risk Parameters Loading...")
    
    try:
        # Create mock data
        mock_risk_params = {
            'emode': {
                'liquidation_thresholds': {'weETH_WETH': 0.95, 'wstETH_WETH': 0.93},
                'max_ltv_limits': {'weETH_WETH': 0.91, 'wstETH_WETH': 0.89},
                'liquidation_bonus': {'weETH_WETH': 0.05, 'wstETH_WETH': 0.05},
                'eligible_pairs': ['weETH_WETH', 'wstETH_WETH']
            },
            'normal_mode': {
                'liquidation_thresholds': {'WETH': 0.85, 'wstETH': 0.80, 'weETH': 0.80, 'USDT': 0.90},
                'max_ltv_limits': {'WETH': 0.80, 'wstETH': 0.75, 'weETH': 0.75, 'USDT': 0.85}
            },
            'metadata': {
                'created': '2024-01-01',
                'source': 'AAVE V3',
                'description': 'AAVE V3 risk parameters',
                'version': '1.0'
            }
        }
        
        with patch('builtins.open', create=True), \
             patch('json.load', return_value=mock_risk_params):
            
            test_instance.test_load_aave_risk_parameters(mock_risk_params)
            test_instance.test_get_aave_risk_params_access(test_instance.mock_provider(mock_risk_params))
            test_instance.test_emode_parameters(test_instance.mock_provider(mock_risk_params))
            test_instance.test_wsteth_parameters(test_instance.mock_provider(mock_risk_params))
            test_instance.test_normal_mode_parameters(test_instance.mock_provider(mock_risk_params))
            test_instance.test_metadata(test_instance.mock_provider(mock_risk_params))
            test_instance.test_error_handling()
            test_instance.test_file_not_found_error()
        
        print("\n✅ All AAVE risk parameters tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()