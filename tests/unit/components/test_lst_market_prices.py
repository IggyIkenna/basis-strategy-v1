#!/usr/bin/env python3
"""
Test LST market price loading functionality with proper mocking.
"""

import pytest
import pandas as pd
from pathlib import Path
import sys
import os
from unittest.mock import Mock, patch

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider


class TestLSTMarketPrices:
    """Test LST market price loading and access with proper mocking."""
    
    @pytest.fixture
    def mock_data_provider(self):
        """Create a mock DataProvider."""
        provider = DataProvider.__new__(DataProvider)
        provider.data_dir = Path('/workspace/data')
        provider.data = {}
        return provider
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', create=True)
    @patch('pandas.read_csv')
    def test_load_weeth_market_prices(self, mock_read_csv, mock_open, mock_exists, mock_data_provider):
        """Test loading weETH market prices from Curve data."""
        # Mock pandas DataFrame
        mock_df = pd.DataFrame({
            'timestamp': ['2024-01-01', '2024-01-02'],
            'price': [2000.0, 2100.0]
        })
        mock_read_csv.return_value = mock_df
        
        provider = mock_data_provider
        
        # Load weETH market prices
        provider._load_lst_market_prices('weeth')
        
        # Verify data is loaded
        assert 'weeth_market_price' in provider.data
        df = provider.data['weeth_market_price']
        
        # Verify data structure
        assert 'price' in df.columns
        assert len(df) == 2
        
        print("✅ weETH market prices loaded successfully")
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', create=True)
    @patch('pandas.read_csv')
    def test_load_wsteth_market_prices(self, mock_read_csv, mock_open, mock_exists, mock_data_provider):
        """Test loading wstETH market prices from Uniswap V3 data."""
        # Mock pandas DataFrame
        mock_df = pd.DataFrame({
            'timestamp': ['2024-01-01', '2024-01-02'],
            'price': [2000.0, 2100.0]
        })
        mock_read_csv.return_value = mock_df
        
        provider = mock_data_provider
        
        # Load wstETH market prices
        provider._load_lst_market_prices('wsteth')
        
        # Verify data is loaded
        assert 'wsteth_market_price' in provider.data
        df = provider.data['wsteth_market_price']
        
        # Verify data structure
        assert 'price' in df.columns
        assert len(df) == 2
        
        print("✅ wstETH market prices loaded successfully")
    
    def test_get_lst_market_price_access(self, mock_data_provider):
        """Test accessing LST market prices."""
        provider = mock_data_provider
        
        # Mock data with timestamp as index
        provider.data = {
            'weeth_market_price': pd.DataFrame({
                'price': [2000.0]
            }, index=pd.DatetimeIndex(['2024-01-01']))
        }
        
        # Test access method
        price_data = provider.get_lst_market_price('weeth', '2024-01-01')
        assert isinstance(price_data, (float, int))
        assert price_data == 2000.0
        
        print("✅ LST market price access works")
    
    def test_get_lst_market_price_not_found(self, mock_data_provider):
        """Test accessing non-existent LST market price."""
        provider = mock_data_provider
        provider.data = {}
        
        # Test access method for non-existent data
        with pytest.raises(KeyError, match="weeth_market_price"):
            provider.get_lst_market_price('weeth', '2024-01-01')
        
        print("✅ LST market price not found error handling works")
    
    def test_lst_market_price_data_quality(self, mock_data_provider):
        """Test LST market price data quality."""
        provider = mock_data_provider
        
        # Mock data with quality issues
        provider.data = {
            'weeth_market_price': pd.DataFrame({
                'price': [2000.0, 2100.0]
            }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02']))
        }
        
        # Test data quality
        price_data = provider.get_lst_market_price('weeth', '2024-01-01')
        
        # Verify reasonable price range
        assert price_data > 0
        assert price_data < 10000  # Reasonable upper bound
        
        print("✅ LST market price data quality checks passed")
    
    def test_lst_market_price_timestamp_handling(self, mock_data_provider):
        """Test LST market price timestamp handling."""
        provider = mock_data_provider
        
        # Mock data with timestamps
        provider.data = {
            'weeth_market_price': pd.DataFrame({
                'price': [2000.0, 2100.0]
            }, index=pd.DatetimeIndex(['2024-01-01 00:00:00', '2024-01-01 01:00:00']))
        }
        
        # Test timestamp handling
        price_data = provider.get_lst_market_price('weeth', '2024-01-01 00:00:00')
        
        # Verify we get a valid price
        assert isinstance(price_data, (float, int))
        assert price_data == 2000.0
        
        print("✅ LST market price timestamp handling works")
    
    def test_lst_market_price_error_handling(self, mock_data_provider):
        """Test error handling for LST market price loading."""
        with patch('pathlib.Path.exists', return_value=False):
            provider = mock_data_provider
            
            with pytest.raises(FileNotFoundError):
                provider._load_lst_market_prices('weeth')
        
        print("✅ LST market price error handling works")


if __name__ == "__main__":
    # Run tests
    test_instance = TestLSTMarketPrices()
    
    print("🧪 Testing LST Market Prices Loading...")
    
    try:
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', create=True), \
             patch('pandas.read_csv') as mock_read_csv:
            
            # Mock pandas DataFrame
            mock_df = pd.DataFrame({
                'timestamp': ['2024-01-01', '2024-01-02'],
                'price': [2000.0, 2100.0]
            })
            mock_read_csv.return_value = mock_df
            
            test_instance.test_load_weeth_market_prices()
            test_instance.test_load_wsteth_market_prices()
            test_instance.test_get_lst_market_price_access()
            test_instance.test_get_lst_market_price_not_found()
            test_instance.test_lst_market_price_data_quality()
            test_instance.test_lst_market_price_timestamp_handling()
            test_instance.test_lst_market_price_error_handling()
        
        print("\n✅ All LST market prices tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()