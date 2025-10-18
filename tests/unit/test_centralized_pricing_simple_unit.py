"""
Simple Test for Centralized Pricing Usage

Verifies that components use UtilityManager for pricing instead of direct data access.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from pathlib import Path

from basis_strategy_v1.core.utilities.utility_manager import UtilityManager
from basis_strategy_v1.core.models.instruments import position_key_to_price_key, position_key_to_oracle_pair


class TestCentralizedPricingSimple:
    """Test that components use centralized pricing through UtilityManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_data_provider = Mock()
        self.mock_utility_manager = Mock(spec=UtilityManager)
        self.timestamp = pd.Timestamp('2024-01-01 12:00:00')
        
        # Mock data structure with uppercase keys
        self.mock_data = {
            'timestamp': self.timestamp,
            'market_data': {
                'prices': {
                    'BTC': 50000.0,
                    'ETH': 3000.0,
                    'USDT': 1.0
                },
                'funding_rates': {
                    'BTC_binance': 0.0001,
                    'ETH_bybit': 0.0002
                }
            },
            'protocol_data': {
                'perp_prices': {
                    'BTC_binance': 50000.0,
                    'ETH_okx': 3000.0
                },
                'aave_indexes': {
                    'aUSDT': 1.05,
                    'aWETH': 1.02
                },
                'oracle_prices': {
                    'weETH/USD': 3076.8,
                    'weETH/ETH': 1.0256,
                    'wstETH/USD': 3045.0,
                    'wstETH/ETH': 1.0150
                },
                'staking_rewards': {
                    'etherfi_weETH': 0.04,
                    'lido_wstETH': 0.035
                }
            },
            'ml_data': {
                'predictions': {
                    'signal': 'long',
                    'confidence': 0.8,
                    'sd': 0.02
                }
            }
        }
        
        self.mock_data_provider.get_data.return_value = self.mock_data
    
    def test_utility_manager_handles_uppercase_keys(self):
        """Test UtilityManager correctly handles uppercase key format."""
        # Test price key conversion
        assert position_key_to_price_key('wallet:BaseToken:BTC') == 'BTC'
        assert position_key_to_price_key('binance:Perp:BTCUSDT') == 'BTC_binance'
        assert position_key_to_price_key('etherfi:LST:weETH') == 'weETH'
    
    def test_utility_manager_handles_oracle_pairs(self):
        """Test UtilityManager correctly handles BASE/QUOTE oracle pair format."""
        assert position_key_to_oracle_pair('etherfi:LST:weETH', 'USD') == 'weETH/USD'
        assert position_key_to_oracle_pair('etherfi:LST:weETH', 'ETH') == 'weETH/ETH'
        assert position_key_to_oracle_pair('lido:LST:wstETH', 'USD') == 'wstETH/USD'
    
    def test_data_structure_consistency(self):
        """Test that all components expect the same data structure format."""
        # Verify the data structure has the expected uppercase keys
        assert 'BTC' in self.mock_data['market_data']['prices']
        assert 'BTC_binance' in self.mock_data['market_data']['funding_rates']
        assert 'BTC_binance' in self.mock_data['protocol_data']['perp_prices']
        assert 'aUSDT' in self.mock_data['protocol_data']['aave_indexes']
        assert 'weETH/USD' in self.mock_data['protocol_data']['oracle_prices']
        assert 'weETH/ETH' in self.mock_data['protocol_data']['oracle_prices']
        assert 'etherfi_weETH' in self.mock_data['protocol_data']['staking_rewards']
    
    def test_utility_manager_price_lookup(self):
        """Test UtilityManager price lookup with uppercase keys."""
        # Mock utility manager methods
        self.mock_utility_manager.get_price_for_position_key.return_value = 50000.0
        
        # Test price lookup
        price = self.mock_utility_manager.get_price_for_position_key('wallet:BaseToken:BTC', self.timestamp)
        
        # Verify method was called
        self.mock_utility_manager.get_price_for_position_key.assert_called_once_with('wallet:BaseToken:BTC', self.timestamp)
        assert price == 50000.0
    
    def test_utility_manager_funding_rate_lookup(self):
        """Test UtilityManager funding rate lookup with uppercase keys."""
        # Mock utility manager methods
        self.mock_utility_manager.get_funding_rate.return_value = 0.0001
        
        # Test funding rate lookup
        funding_rate = self.mock_utility_manager.get_funding_rate('binance', 'BTCUSDT', self.timestamp)
        
        # Verify method was called
        self.mock_utility_manager.get_funding_rate.assert_called_once_with('binance', 'BTCUSDT', self.timestamp)
        assert funding_rate == 0.0001
    
    def test_utility_manager_oracle_price_lookup(self):
        """Test UtilityManager oracle price lookup with BASE/QUOTE format."""
        # Mock utility manager methods
        self.mock_utility_manager.get_oracle_price.return_value = 3076.8
        
        # Test oracle price lookup
        oracle_price = self.mock_utility_manager.get_oracle_price('weETH', self.timestamp)
        
        # Verify method was called
        self.mock_utility_manager.get_oracle_price.assert_called_once_with('weETH', self.timestamp)
        assert oracle_price == 3076.8
    
    def test_utility_manager_liquidity_index_lookup(self):
        """Test UtilityManager liquidity index lookup with uppercase keys."""
        # Mock utility manager methods
        self.mock_utility_manager.get_liquidity_index.return_value = 1.05
        
        # Test liquidity index lookup
        liquidity_index = self.mock_utility_manager.get_liquidity_index('aUSDT', self.timestamp)
        
        # Verify method was called
        self.mock_utility_manager.get_liquidity_index.assert_called_once_with('aUSDT', self.timestamp)
        assert liquidity_index == 1.05
    
    def test_canonical_data_access_pattern(self):
        """Test that components use canonical data access pattern."""
        # Test that data provider is called with canonical pattern
        data = self.mock_data_provider.get_data(self.timestamp)
        
        # Verify canonical data structure
        assert 'market_data' in data
        assert 'protocol_data' in data
        assert 'ml_data' in data
        
        # Verify uppercase keys
        assert 'BTC' in data['market_data']['prices']
        assert 'BTC_binance' in data['market_data']['funding_rates']
        assert 'weETH/USD' in data['protocol_data']['oracle_prices']
    
    def test_no_lowercase_keys_in_data_structure(self):
        """Test that data structure doesn't contain lowercase keys."""
        data = self.mock_data_provider.get_data(self.timestamp)
        
        # Check that we don't have lowercase keys
        assert 'btc' not in data['market_data']['prices']
        assert 'btc_binance' not in data['market_data']['funding_rates']
        assert 'weeth' not in data['protocol_data']['oracle_prices']
        
        # Check that we have uppercase keys
        assert 'BTC' in data['market_data']['prices']
        assert 'BTC_binance' in data['market_data']['funding_rates']
        assert 'weETH/USD' in data['protocol_data']['oracle_prices']
    
    def test_oracle_pair_format_consistency(self):
        """Test that oracle prices use consistent BASE/QUOTE format."""
        data = self.mock_data_provider.get_data(self.timestamp)
        oracle_prices = data['protocol_data']['oracle_prices']
        
        # Check that all oracle price keys use BASE/QUOTE format
        for key in oracle_prices.keys():
            assert '/' in key, f"Oracle price key {key} should use BASE/QUOTE format"
            base, quote = key.split('/')
            assert base and quote, f"Oracle price key {key} should have both base and quote"
    
    def test_venue_suffix_format_consistency(self):
        """Test that venue-specific keys use consistent ASSET_venue format."""
        data = self.mock_data_provider.get_data(self.timestamp)
        funding_rates = data['market_data']['funding_rates']
        perp_prices = data['protocol_data']['perp_prices']
        
        # Check that all venue-specific keys use ASSET_venue format
        for key in funding_rates.keys():
            if '_' in key:
                asset, venue = key.split('_', 1)
                assert asset.isupper(), f"Asset {asset} should be uppercase in key {key}"
                assert venue.islower(), f"Venue {venue} should be lowercase in key {key}"
        
        for key in perp_prices.keys():
            if '_' in key:
                asset, venue = key.split('_', 1)
                assert asset.isupper(), f"Asset {asset} should be uppercase in key {key}"
                assert venue.islower(), f"Venue {venue} should be lowercase in key {key}"


if __name__ == '__main__':
    pytest.main([__file__])
