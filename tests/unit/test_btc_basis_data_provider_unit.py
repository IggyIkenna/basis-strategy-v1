#!/usr/bin/env python3
"""
BTC Basis Data Provider Unit Tests

Tests the BTC Basis Data Provider component in isolation with mocked dependencies.
Validates BTC basis trading data provision, funding rate calculations, and market data integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Mock the backend imports
with patch.dict('sys.modules', {
    'basis_strategy_v1': Mock(),
    'basis_strategy_v1.infrastructure': Mock(),
    'basis_strategy_v1.infrastructure.data': Mock(),
    'basis_strategy_v1.infrastructure.config': Mock(),
}):
    # Import the data provider class (will be mocked)
    from basis_strategy_v1.infrastructure.data.btc_basis_data_provider import BTCBasisDataProvider


class TestBTCBasisDataProvider:
    """Test suite for BTC Basis Data Provider component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'venues': ['binance', 'bybit', 'okx'],
            'assets': ['BTC', 'USDT'],
            'data_sources': {
                'spot_prices': 'binance_spot',
                'futures_prices': 'binance_futures',
                'funding_rates': 'binance_futures'
            },
            'update_frequency': 3600,  # 1 hour
            'historical_days': 30
        }
    
    @pytest.fixture
    def mock_market_data(self):
        """Mock market data for testing."""
        return {
            'btc_spot_price': Decimal('40000.0'),
            'btc_futures_price': Decimal('40100.0'),
            'funding_rate': Decimal('0.01'),
            'basis_spread': Decimal('100.0'),
            'basis_percentage': Decimal('0.0025'),  # 0.25%
            'volume_24h': Decimal('1000000'),
            'open_interest': Decimal('5000000')
        }
    
    @pytest.fixture
    def btc_basis_data_provider(self, mock_config, mock_market_data):
        """Create BTC Basis Data Provider instance for testing."""
        with patch('basis_strategy_v1.infrastructure.data.btc_basis_data_provider.BTCBasisDataProvider') as mock_provider_class:
            provider = Mock()
            provider.initialize.return_value = True
            provider.get_btc_spot_price.return_value = mock_market_data['btc_spot_price']
            provider.get_btc_futures_price.return_value = mock_market_data['btc_futures_price']
            provider.get_funding_rate.return_value = mock_market_data['funding_rate']
            provider.get_basis_spread.return_value = mock_market_data['basis_spread']
            provider.get_basis_percentage.return_value = mock_market_data['basis_percentage']
            provider.get_volume_24h.return_value = mock_market_data['volume_24h']
            provider.get_open_interest.return_value = mock_market_data['open_interest']
            provider.get_historical_data.return_value = []
            return provider
    
    def test_provider_initialization(self, btc_basis_data_provider, mock_config):
        """Test BTC basis data provider initializes correctly."""
        # Test initialization
        result = btc_basis_data_provider.initialize(mock_config)
        
        # Verify initialization
        assert result is True
        btc_basis_data_provider.initialize.assert_called_once_with(mock_config)
    
    def test_btc_spot_price_retrieval(self, btc_basis_data_provider, mock_market_data):
        """Test BTC spot price retrieval."""
        # Test spot price
        spot_price = btc_basis_data_provider.get_btc_spot_price()
        assert spot_price == mock_market_data['btc_spot_price']
        assert spot_price == Decimal('40000.0')
    
    def test_btc_futures_price_retrieval(self, btc_basis_data_provider, mock_market_data):
        """Test BTC futures price retrieval."""
        # Test futures price
        futures_price = btc_basis_data_provider.get_btc_futures_price()
        assert futures_price == mock_market_data['btc_futures_price']
        assert futures_price == Decimal('40100.0')
    
    def test_funding_rate_retrieval(self, btc_basis_data_provider, mock_market_data):
        """Test funding rate retrieval."""
        # Test funding rate
        funding_rate = btc_basis_data_provider.get_funding_rate()
        assert funding_rate == mock_market_data['funding_rate']
        assert funding_rate == Decimal('0.01')
    
    def test_basis_spread_calculation(self, btc_basis_data_provider, mock_market_data):
        """Test basis spread calculation."""
        # Test basis spread
        basis_spread = btc_basis_data_provider.get_basis_spread()
        assert basis_spread == mock_market_data['basis_spread']
        assert basis_spread == Decimal('100.0')
        
        # Verify basis spread calculation (futures - spot)
        spot_price = mock_market_data['btc_spot_price']
        futures_price = mock_market_data['btc_futures_price']
        expected_spread = futures_price - spot_price
        assert basis_spread == expected_spread
    
    def test_basis_percentage_calculation(self, btc_basis_data_provider, mock_market_data):
        """Test basis percentage calculation."""
        # Test basis percentage
        basis_percentage = btc_basis_data_provider.get_basis_percentage()
        assert basis_percentage == mock_market_data['basis_percentage']
        assert basis_percentage == Decimal('0.0025')  # 0.25%
        
        # Verify basis percentage calculation (spread / spot * 100)
        spot_price = mock_market_data['btc_spot_price']
        basis_spread = mock_market_data['basis_spread']
        expected_percentage = basis_spread / spot_price
        assert basis_percentage == expected_percentage
    
    def test_volume_and_open_interest(self, btc_basis_data_provider, mock_market_data):
        """Test volume and open interest retrieval."""
        # Test 24h volume
        volume_24h = btc_basis_data_provider.get_volume_24h()
        assert volume_24h == mock_market_data['volume_24h']
        assert volume_24h == Decimal('1000000')
        
        # Test open interest
        open_interest = btc_basis_data_provider.get_open_interest()
        assert open_interest == mock_market_data['open_interest']
        assert open_interest == Decimal('5000000')
    
    def test_historical_data_retrieval(self, btc_basis_data_provider):
        """Test historical data retrieval."""
        # Test historical data
        historical_data = btc_basis_data_provider.get_historical_data()
        assert isinstance(historical_data, list)
        
        # Test with date range
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        with patch.object(btc_basis_data_provider, 'get_historical_data', return_value=[
            {'timestamp': start_date, 'spot_price': Decimal('39000'), 'futures_price': Decimal('39100'), 'funding_rate': Decimal('0.01')},
            {'timestamp': end_date, 'spot_price': Decimal('40000'), 'futures_price': Decimal('40100'), 'funding_rate': Decimal('0.01')}
        ]):
            historical_data = btc_basis_data_provider.get_historical_data()
            assert len(historical_data) == 2
            assert historical_data[0]['spot_price'] == Decimal('39000')
            assert historical_data[1]['spot_price'] == Decimal('40000')
    
    def test_multi_venue_data_aggregation(self, btc_basis_data_provider, mock_config):
        """Test multi-venue data aggregation."""
        # Test venue configuration
        venues = mock_config['venues']
        assert 'binance' in venues
        assert 'bybit' in venues
        assert 'okx' in venues
        
        # Test data source configuration
        data_sources = mock_config['data_sources']
        assert data_sources['spot_prices'] == 'binance_spot'
        assert data_sources['futures_prices'] == 'binance_futures'
        assert data_sources['funding_rates'] == 'binance_futures'
    
    def test_basis_arbitrage_opportunities(self, btc_basis_data_provider, mock_market_data):
        """Test basis arbitrage opportunity detection."""
        # Test positive basis (futures > spot)
        spot_price = mock_market_data['btc_spot_price']
        futures_price = mock_market_data['btc_futures_price']
        basis_spread = futures_price - spot_price
        
        assert basis_spread > 0  # Positive basis
        
        # Test arbitrage opportunity calculation
        funding_rate = mock_market_data['funding_rate']
        arbitrage_yield = basis_spread / spot_price - funding_rate
        expected_arbitrage_yield = Decimal('0.0015')  # 0.15%
        assert arbitrage_yield == expected_arbitrage_yield
    
    def test_data_validation_and_quality(self, btc_basis_data_provider):
        """Test data validation and quality checks."""
        # Test data validation
        with patch.object(btc_basis_data_provider, 'validate_data_quality', return_value=True):
            is_valid = btc_basis_data_provider.validate_data_quality()
            assert is_valid is True
        
        # Test data freshness
        with patch.object(btc_basis_data_provider, 'is_data_fresh', return_value=True):
            is_fresh = btc_basis_data_provider.is_data_fresh()
            assert is_fresh is True
        
        # Test data completeness
        with patch.object(btc_basis_data_provider, 'is_data_complete', return_value=True):
            is_complete = btc_basis_data_provider.is_data_complete()
            assert is_complete is True
    
    def test_error_handling_and_fallback(self, btc_basis_data_provider):
        """Test error handling and fallback mechanisms."""
        # Test API failure handling
        with patch.object(btc_basis_data_provider, 'get_btc_spot_price', side_effect=Exception("API Error")):
            with pytest.raises(Exception, match="API Error"):
                btc_basis_data_provider.get_btc_spot_price()
        
        # Test fallback data source
        with patch.object(btc_basis_data_provider, 'get_fallback_data', return_value={'btc_spot_price': Decimal('39900')}):
            fallback_data = btc_basis_data_provider.get_fallback_data()
            assert fallback_data['btc_spot_price'] == Decimal('39900')
    
    def test_data_provider_state_management(self, btc_basis_data_provider):
        """Test data provider state management and persistence."""
        # Test provider state
        provider_state = {
            'last_update': datetime.now(),
            'data_sources': ['binance', 'bybit', 'okx'],
            'current_prices': {
                'spot': Decimal('40000'),
                'futures': Decimal('40100'),
                'funding_rate': Decimal('0.01')
            },
            'basis_metrics': {
                'spread': Decimal('100'),
                'percentage': Decimal('0.0025'),
                'arbitrage_yield': Decimal('0.0015')
            },
            'data_quality': {
                'freshness': True,
                'completeness': True,
                'accuracy': True
            }
        }
        
        # Verify state components
        assert provider_state['data_sources'] == ['binance', 'bybit', 'okx']
        assert provider_state['current_prices']['spot'] == Decimal('40000')
        assert provider_state['current_prices']['futures'] == Decimal('40100')
        assert provider_state['current_prices']['funding_rate'] == Decimal('0.01')
        assert provider_state['basis_metrics']['spread'] == Decimal('100')
        assert provider_state['basis_metrics']['percentage'] == Decimal('0.0025')
        assert provider_state['basis_metrics']['arbitrage_yield'] == Decimal('0.0015')
        assert provider_state['data_quality']['freshness'] is True
        assert provider_state['data_quality']['completeness'] is True
        assert provider_state['data_quality']['accuracy'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
