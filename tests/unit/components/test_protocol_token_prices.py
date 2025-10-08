#!/usr/bin/env python3
"""
Test protocol token price loading functionality.
"""

import pytest
import pandas as pd
from pathlib import Path
import sys
import os
from unittest.mock import patch

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider


class TestProtocolTokenPrices:
    """Test protocol token price loading and access."""
    
    @pytest.fixture
    def mock_data_provider(self):
        """Create a mock DataProvider with mocked data loading."""
        provider = DataProvider.__new__(DataProvider)
        provider.data_dir = Path('/workspace/data')
        provider.data = {}
        return provider
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', create=True)
    @patch('pandas.read_csv')
    def test_load_eigen_prices(self, mock_read_csv, mock_open, mock_exists, mock_data_provider):
        """Test loading EIGEN token prices."""
        # Mock pandas DataFrame for Uniswap (has 'close' column)
        mock_df_uniswap = pd.DataFrame({
            'timestamp': ['2024-01-01', '2024-01-02'],
            'close': [0.5, 0.6]
        })
        # Mock pandas DataFrame for Binance (has 'price' column)
        mock_df_binance = pd.DataFrame({
            'timestamp': ['2024-01-01', '2024-01-02'],
            'price': [0.5, 0.6]
        })
        
        # Mock read_csv to return different data based on file path
        def mock_read_csv_side_effect(file_path, **kwargs):
            if 'uniswap' in str(file_path):
                return mock_df_uniswap
            else:
                return mock_df_binance
        
        mock_read_csv.side_effect = mock_read_csv_side_effect
        
        provider = mock_data_provider
        
        # Load EIGEN prices
        provider._load_protocol_token_prices('eigen')
        
        # Verify data is loaded
        assert 'eigen_eth_price' in provider.data
        assert 'eigen_usdt_price' in provider.data
        
        # Verify data structure
        eigen_eth_data = provider.data['eigen_eth_price']
        eigen_usdt_data = provider.data['eigen_usdt_price']
        
        assert 'price' in eigen_eth_data.columns
        assert 'price' in eigen_usdt_data.columns
        assert len(eigen_eth_data) > 0
        assert len(eigen_usdt_data) > 0
        
        print("✅ EIGEN price loading works")
        print(f"   EIGEN/ETH records: {len(eigen_eth_data)}")
        print(f"   EIGEN/USDT records: {len(eigen_usdt_data)}")
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', create=True)
    @patch('pandas.read_csv')
    def test_load_ethfi_prices(self, mock_read_csv, mock_open, mock_exists, mock_data_provider):
        """Test loading ETHFI token prices."""
        # Mock pandas DataFrame for Uniswap (has 'close' column)
        mock_df_uniswap = pd.DataFrame({
            'timestamp': ['2024-01-01', '2024-01-02'],
            'close': [2.5, 2.6]
        })
        # Mock pandas DataFrame for Binance (has 'price' column)
        mock_df_binance = pd.DataFrame({
            'timestamp': ['2024-01-01', '2024-01-02'],
            'price': [2.5, 2.6]
        })
        
        # Mock read_csv to return different data based on file path
        def mock_read_csv_side_effect(file_path, **kwargs):
            if 'uniswap' in str(file_path):
                return mock_df_uniswap
            else:
                return mock_df_binance
        
        mock_read_csv.side_effect = mock_read_csv_side_effect
        
        provider = mock_data_provider
        
        # Load ETHFI prices
        provider._load_protocol_token_prices('ethfi')
        
        # Verify data is loaded
        assert 'ethfi_eth_price' in provider.data
        assert 'ethfi_usdt_price' in provider.data
        
        # Verify data structure
        ethfi_eth_data = provider.data['ethfi_eth_price']
        ethfi_usdt_data = provider.data['ethfi_usdt_price']
        
        assert 'price' in ethfi_eth_data.columns
        assert 'price' in ethfi_usdt_data.columns
        assert len(ethfi_eth_data) > 0
        assert len(ethfi_usdt_data) > 0
        
        print("✅ ETHFI price loading works")
        print(f"   ETHFI/ETH records: {len(ethfi_eth_data)}")
        print(f"   ETHFI/USDT records: {len(ethfi_usdt_data)}")
    
    def test_load_king_prices_placeholder(self, mock_data_provider):
        """Test loading KING token prices (placeholder)."""
        provider = mock_data_provider
        
        # Load KING prices (should warn but not fail)
        provider._load_protocol_token_prices('king')
        
        # Verify no data is loaded (placeholder)
        assert 'king_eth_price' not in provider.data
        assert 'king_usdt_price' not in provider.data
        
        print("✅ KING price loading handled correctly (placeholder)")
    
    def test_get_eigen_eth_price(self, mock_data_provider):
        """Test getting EIGEN/ETH price."""
        provider = mock_data_provider
        
        # Mock data directly
        provider.data = {
            'eigen_eth_price': pd.DataFrame({
                'price': [0.5, 0.6]
            }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02'], tz='UTC'))
        }
        
        # Test price access
        timestamp = pd.Timestamp('2024-01-01', tz='UTC')
        price = provider.get_protocol_token_price('eigen', timestamp, 'eth')
        
        # Verify price is reasonable
        assert isinstance(price, float)
        assert price > 0
        assert price < 1.0  # EIGEN/ETH should be less than 1
        
        print(f"✅ EIGEN/ETH price access: {price:.6f}")
    
    def test_get_eigen_usdt_price(self, mock_data_provider):
        """Test getting EIGEN/USDT price."""
        provider = mock_data_provider
        
        # Mock data directly
        provider.data = {
            'eigen_usdt_price': pd.DataFrame({
                'price': [1000.0, 1200.0]
            }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02'], tz='UTC'))
        }
        
        # Test price access
        timestamp = pd.Timestamp('2024-01-01', tz='UTC')
        price = provider.get_protocol_token_price('eigen', timestamp, 'usdt')
        
        # Verify price is reasonable
        assert isinstance(price, float)
        assert price > 0
        assert price < 2000.0  # EIGEN/USDT should be reasonable
        
        print(f"✅ EIGEN/USDT price access: {price:.6f}")
    
    def test_get_ethfi_eth_price(self, mock_data_provider):
        """Test getting ETHFI/ETH price."""
        provider = mock_data_provider
        
        # Mock data directly
        provider.data = {
            'ethfi_eth_price': pd.DataFrame({
                'price': [2.5, 2.6]
            }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02'], tz='UTC'))
        }
        
        # Test price access
        timestamp = pd.Timestamp('2024-01-01', tz='UTC')
        price = provider.get_protocol_token_price('ethfi', timestamp, 'eth')
        
        # Verify price is reasonable
        assert isinstance(price, float)
        assert price > 0
        assert price < 5.0  # ETHFI/ETH should be reasonable
        
        print(f"✅ ETHFI/ETH price access: {price:.6f}")
    
    def test_get_ethfi_usdt_price(self, mock_data_provider):
        """Test getting ETHFI/USDT price."""
        provider = mock_data_provider
        
        # Mock data directly
        provider.data = {
            'ethfi_usdt_price': pd.DataFrame({
                'price': [5000.0, 5200.0]
            }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02'], tz='UTC'))
        }
        
        # Test price access
        timestamp = pd.Timestamp('2024-01-01', tz='UTC')
        price = provider.get_protocol_token_price('ethfi', timestamp, 'usdt')
        
        # Verify price is reasonable
        assert isinstance(price, float)
        assert price > 0
        assert price < 10000.0  # ETHFI/USDT should be reasonable
        
        print(f"✅ ETHFI/USDT price access: {price:.6f}")
    
    def test_get_king_price_error(self, mock_data_provider):
        """Test getting KING price (should error)."""
        provider = mock_data_provider
        
        # Test KING price access (should raise error)
        timestamp = pd.Timestamp('2024-10-10 06:00:00', tz='UTC')
        
        with pytest.raises(ValueError, match="KING token price data not available"):
            provider.get_protocol_token_price('king', timestamp, 'eth')
        
        print("✅ KING price access correctly raises error")
    
    def test_get_protocol_token_price_invalid_token(self, mock_data_provider):
        """Test getting price for invalid token."""
        provider = mock_data_provider
        
        # Test invalid token
        timestamp = pd.Timestamp('2024-10-10 06:00:00', tz='UTC')
        
        with pytest.raises(ValueError, match="Unknown protocol token"):
            provider.get_protocol_token_price('invalid', timestamp, 'eth')
        
        print("✅ Invalid token correctly raises error")
    
    def test_get_protocol_token_price_invalid_price_type(self, mock_data_provider):
        """Test getting price with invalid price type."""
        provider = mock_data_provider
        
        # Mock data directly
        provider.data = {
            'eigen_eth_price': pd.DataFrame({
                'price': [0.5, 0.6]
            }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02'], tz='UTC'))
        }
        
        # Test invalid price type
        timestamp = pd.Timestamp('2024-10-10 06:00:00', tz='UTC')
        
        with pytest.raises(ValueError, match="Unknown price type"):
            provider.get_protocol_token_price('eigen', timestamp, 'invalid')
        
        print("✅ Invalid price type correctly raises error")
    
    def test_get_protocol_token_price_data_not_loaded(self, mock_data_provider):
        """Test getting price when data is not loaded."""
        provider = mock_data_provider
        
        # Don't load any data
        
        # Test price access (should raise error)
        timestamp = pd.Timestamp('2024-10-10 06:00:00', tz='UTC')
        
        with pytest.raises(ValueError, match="Protocol token price data not loaded"):
            provider.get_protocol_token_price('eigen', timestamp, 'eth')
        
        print("✅ Unloaded data correctly raises error")
    
    def test_protocol_token_price_timestamp_handling(self, mock_data_provider):
        """Test protocol token price timestamp handling."""
        provider = mock_data_provider
        
        # Mock data directly
        provider.data = {
            'eigen_eth_price': pd.DataFrame({
                'price': [0.5, 0.6, 0.7]
            }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02', '2024-01-03'], tz='UTC'))
        }
        
        # Test with different timestamps
        timestamps = [
            pd.Timestamp('2024-01-01', tz='UTC'),  # Start of data
            pd.Timestamp('2024-01-02', tz='UTC'),  # Middle of data
            pd.Timestamp('2024-01-03', tz='UTC'),  # End of data
        ]
        
        for timestamp in timestamps:
            price = provider.get_protocol_token_price('eigen', timestamp, 'eth')
            assert isinstance(price, float)
            assert price > 0
        
        print("✅ Protocol token price timestamp handling works")
    
    def test_protocol_token_price_data_requirements_mapping(self, mock_data_provider):
        """Test that protocol token prices are included in data requirements mapping."""
        provider = mock_data_provider
        
        # Mock data directly
        provider.data = {
            'eigen_eth_price': pd.DataFrame({'price': [0.5]}),
            'eigen_usdt_price': pd.DataFrame({'price': [1000.0]}),
            'ethfi_eth_price': pd.DataFrame({'price': [2.5]}),
            'ethfi_usdt_price': pd.DataFrame({'price': [5000.0]})
        }
        
        # Test data requirements validation
        config = type('Config', (), {
            'data_requirements': ['protocol_token_prices']
        })()
        
        provider.config = config
        provider.mode = 'test_mode'
        
        # Should not raise error (all required data is loaded)
        provider._validate_data_requirements()
        
        print("✅ Protocol token prices data requirements mapping works")


if __name__ == "__main__":
    # Run tests
    test_instance = TestProtocolTokenPrices()
    
    print("🧪 Testing Protocol Token Price Loading...")
    
    try:
        test_instance.test_load_eigen_prices()
        test_instance.test_load_ethfi_prices()
        test_instance.test_load_king_prices_placeholder()
        test_instance.test_get_eigen_eth_price()
        test_instance.test_get_eigen_usdt_price()
        test_instance.test_get_ethfi_eth_price()
        test_instance.test_get_ethfi_usdt_price()
        test_instance.test_get_king_price_error()
        test_instance.test_get_protocol_token_price_invalid_token()
        test_instance.test_get_protocol_token_price_invalid_price_type()
        test_instance.test_get_protocol_token_price_data_not_loaded()
        test_instance.test_protocol_token_price_timestamp_handling()
        test_instance.test_protocol_token_price_data_requirements_mapping()
        
        print("\n✅ All protocol token price tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()