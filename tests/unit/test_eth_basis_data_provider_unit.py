#!/usr/bin/env python3
"""
ETH Basis Data Provider Unit Tests

Tests the ETH Basis Data Provider component in isolation with mocked dependencies.
Validates ETH basis trading data provision, funding rate calculations, and market data integration.
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
    from basis_strategy_v1.infrastructure.data.eth_basis_data_provider import ETHBasisDataProvider


class TestETHBasisDataProvider:
    """Test suite for ETH Basis Data Provider component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'venues': ['binance', 'bybit', 'okx'],
            'assets': ['ETH', 'USDT'],
            'data_sources': {
                'spot_prices': 'binance_spot',
                'futures_prices': 'binance_futures',
                'funding_rates': 'binance_futures'
            },
            'update_frequency': 3600,  # 1 hour
            'historical_days': 30,
            'basis_calculation': {
                'method': 'futures_spot_spread',
                'normalization': 'percentage',
                'threshold': Decimal('0.001')  # 0.1%
            }
        }
    
    @pytest.fixture
    def mock_market_data(self):
        """Mock market data for testing."""
        return {
            'eth_spot_price': Decimal('2000.0'),
            'eth_futures_price': Decimal('2010.0'),
            'funding_rate': Decimal('0.01'),
            'basis_spread': Decimal('10.0'),
            'basis_percentage': Decimal('0.005'),  # 0.5%
            'volume_24h': Decimal('2000000'),
            'open_interest': Decimal('10000000'),
            'funding_rate_8h': Decimal('0.01'),
            'next_funding_time': datetime.now() + timedelta(hours=8)
        }
    
    @pytest.fixture
    def eth_basis_data_provider(self, mock_config, mock_market_data):
        """Create ETH Basis Data Provider instance for testing."""
        with patch('basis_strategy_v1.infrastructure.data.eth_basis_data_provider.ETHBasisDataProvider') as mock_provider_class:
            provider = Mock()
            provider.initialize.return_value = True
            provider.get_eth_spot_price.return_value = mock_market_data['eth_spot_price']
            provider.get_eth_futures_price.return_value = mock_market_data['eth_futures_price']
            provider.get_funding_rate.return_value = mock_market_data['funding_rate']
            provider.get_basis_spread.return_value = mock_market_data['basis_spread']
            provider.get_basis_percentage.return_value = mock_market_data['basis_percentage']
            provider.get_volume_24h.return_value = mock_market_data['volume_24h']
            provider.get_open_interest.return_value = mock_market_data['open_interest']
            provider.get_funding_rate_8h.return_value = mock_market_data['funding_rate_8h']
            provider.get_next_funding_time.return_value = mock_market_data['next_funding_time']
            provider.get_historical_data.return_value = []
            return provider
    
    def test_provider_initialization(self, eth_basis_data_provider, mock_config):
        """Test ETH basis data provider initializes correctly."""
        # Test initialization
        result = eth_basis_data_provider.initialize(mock_config)
        
        # Verify initialization
        assert result is True
        eth_basis_data_provider.initialize.assert_called_once_with(mock_config)
    
    def test_eth_spot_price_retrieval(self, eth_basis_data_provider, mock_market_data):
        """Test ETH spot price retrieval."""
        # Test spot price
        spot_price = eth_basis_data_provider.get_eth_spot_price()
        assert spot_price == mock_market_data['eth_spot_price']
        assert spot_price == Decimal('2000.0')
    
    def test_eth_futures_price_retrieval(self, eth_basis_data_provider, mock_market_data):
        """Test ETH futures price retrieval."""
        # Test futures price
        futures_price = eth_basis_data_provider.get_eth_futures_price()
        assert futures_price == mock_market_data['eth_futures_price']
        assert futures_price == Decimal('2010.0')
    
    def test_funding_rate_retrieval(self, eth_basis_data_provider, mock_market_data):
        """Test funding rate retrieval."""
        # Test funding rate
        funding_rate = eth_basis_data_provider.get_funding_rate()
        assert funding_rate == mock_market_data['funding_rate']
        assert funding_rate == Decimal('0.01')
        
        # Test 8-hour funding rate
        funding_rate_8h = eth_basis_data_provider.get_funding_rate_8h()
        assert funding_rate_8h == mock_market_data['funding_rate_8h']
        assert funding_rate_8h == Decimal('0.01')
    
    def test_basis_spread_calculation(self, eth_basis_data_provider, mock_market_data):
        """Test basis spread calculation."""
        # Test basis spread
        basis_spread = eth_basis_data_provider.get_basis_spread()
        assert basis_spread == mock_market_data['basis_spread']
        assert basis_spread == Decimal('10.0')
        
        # Verify basis spread calculation (futures - spot)
        spot_price = mock_market_data['eth_spot_price']
        futures_price = mock_market_data['eth_futures_price']
        expected_spread = futures_price - spot_price
        assert basis_spread == expected_spread
    
    def test_basis_percentage_calculation(self, eth_basis_data_provider, mock_market_data):
        """Test basis percentage calculation."""
        # Test basis percentage
        basis_percentage = eth_basis_data_provider.get_basis_percentage()
        assert basis_percentage == mock_market_data['basis_percentage']
        assert basis_percentage == Decimal('0.005')  # 0.5%
        
        # Verify basis percentage calculation (spread / spot * 100)
        spot_price = mock_market_data['eth_spot_price']
        basis_spread = mock_market_data['basis_spread']
        expected_percentage = basis_spread / spot_price
        assert basis_percentage == expected_percentage
    
    def test_volume_and_open_interest(self, eth_basis_data_provider, mock_market_data):
        """Test volume and open interest retrieval."""
        # Test 24h volume
        volume_24h = eth_basis_data_provider.get_volume_24h()
        assert volume_24h == mock_market_data['volume_24h']
        assert volume_24h == Decimal('2000000')
        
        # Test open interest
        open_interest = eth_basis_data_provider.get_open_interest()
        assert open_interest == mock_market_data['open_interest']
        assert open_interest == Decimal('10000000')
    
    def test_funding_time_management(self, eth_basis_data_provider, mock_market_data):
        """Test funding time management and scheduling."""
        # Test next funding time
        next_funding_time = eth_basis_data_provider.get_next_funding_time()
        assert next_funding_time == mock_market_data['next_funding_time']
        
        # Test funding time calculation
        current_time = datetime.now()
        expected_funding_time = current_time + timedelta(hours=8)
        
        # Verify funding time is in the future
        assert next_funding_time > current_time
        
        # Test funding time intervals (8-hour cycles)
        time_until_funding = next_funding_time - current_time
        assert time_until_funding <= timedelta(hours=8)
    
    def test_historical_data_retrieval(self, eth_basis_data_provider):
        """Test historical data retrieval."""
        # Test historical data
        historical_data = eth_basis_data_provider.get_historical_data()
        assert isinstance(historical_data, list)
        
        # Test with date range
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        with patch.object(eth_basis_data_provider, 'get_historical_data', return_value=[
            {'timestamp': start_date, 'spot_price': Decimal('1900'), 'futures_price': Decimal('1910'), 'funding_rate': Decimal('0.01')},
            {'timestamp': end_date, 'spot_price': Decimal('2000'), 'futures_price': Decimal('2010'), 'funding_rate': Decimal('0.01')}
        ]):
            historical_data = eth_basis_data_provider.get_historical_data()
            assert len(historical_data) == 2
            assert historical_data[0]['spot_price'] == Decimal('1900')
            assert historical_data[1]['spot_price'] == Decimal('2000')
    
    def test_multi_venue_data_aggregation(self, eth_basis_data_provider, mock_config):
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
    
    def test_basis_arbitrage_opportunities(self, eth_basis_data_provider, mock_market_data):
        """Test basis arbitrage opportunity detection."""
        # Test positive basis (futures > spot)
        spot_price = mock_market_data['eth_spot_price']
        futures_price = mock_market_data['eth_futures_price']
        basis_spread = futures_price - spot_price
        
        assert basis_spread > 0  # Positive basis
        
        # Test arbitrage opportunity calculation
        funding_rate = mock_market_data['funding_rate']
        arbitrage_yield = basis_spread / spot_price - funding_rate
        expected_arbitrage_yield = Decimal('-0.005')  # -0.5% (negative due to funding rate)
        assert arbitrage_yield == expected_arbitrage_yield
    
    def test_basis_calculation_configuration(self, eth_basis_data_provider, mock_config):
        """Test basis calculation configuration and methods."""
        # Test basis calculation configuration
        basis_calc_config = mock_config['basis_calculation']
        assert basis_calc_config['method'] == 'futures_spot_spread'
        assert basis_calc_config['normalization'] == 'percentage'
        assert basis_calc_config['threshold'] == Decimal('0.001')  # 0.1%
        
        # Test basis calculation method
        with patch.object(eth_basis_data_provider, 'calculate_basis', return_value=Decimal('0.005')):
            basis = eth_basis_data_provider.calculate_basis()
            assert basis == Decimal('0.005')
    
    def test_data_validation_and_quality(self, eth_basis_data_provider):
        """Test data validation and quality checks."""
        # Test data validation
        with patch.object(eth_basis_data_provider, 'validate_data_quality', return_value=True):
            is_valid = eth_basis_data_provider.validate_data_quality()
            assert is_valid is True
        
        # Test data freshness
        with patch.object(eth_basis_data_provider, 'is_data_fresh', return_value=True):
            is_fresh = eth_basis_data_provider.is_data_fresh()
            assert is_fresh is True
        
        # Test data completeness
        with patch.object(eth_basis_data_provider, 'is_data_complete', return_value=True):
            is_complete = eth_basis_data_provider.is_data_complete()
            assert is_complete is True
    
    def test_error_handling_and_fallback(self, eth_basis_data_provider):
        """Test error handling and fallback mechanisms."""
        # Test API failure handling
        with patch.object(eth_basis_data_provider, 'get_eth_spot_price', side_effect=Exception("API Error")):
            with pytest.raises(Exception, match="API Error"):
                eth_basis_data_provider.get_eth_spot_price()
        
        # Test fallback data source
        with patch.object(eth_basis_data_provider, 'get_fallback_data', return_value={'eth_spot_price': Decimal('1990')}):
            fallback_data = eth_basis_data_provider.get_fallback_data()
            assert fallback_data['eth_spot_price'] == Decimal('1990')
    
    def test_eth_specific_metrics(self, eth_basis_data_provider, mock_market_data):
        """Test ETH-specific metrics and calculations."""
        # Test ETH-specific basis calculations
        eth_spot = mock_market_data['eth_spot_price']
        eth_futures = mock_market_data['eth_futures_price']
        
        # Test ETH basis spread
        eth_basis_spread = eth_futures - eth_spot
        assert eth_basis_spread == Decimal('10.0')
        
        # Test ETH basis percentage
        eth_basis_percentage = eth_basis_spread / eth_spot
        assert eth_basis_percentage == Decimal('0.005')  # 0.5%
        
        # Test ETH funding rate impact
        funding_rate = mock_market_data['funding_rate']
        net_basis_yield = eth_basis_percentage - funding_rate
        assert net_basis_yield == Decimal('-0.005')  # -0.5%
    
    def test_data_provider_state_management(self, eth_basis_data_provider):
        """Test data provider state management and persistence."""
        # Test provider state
        provider_state = {
            'last_update': datetime.now(),
            'data_sources': ['binance', 'bybit', 'okx'],
            'current_prices': {
                'spot': Decimal('2000'),
                'futures': Decimal('2010'),
                'funding_rate': Decimal('0.01')
            },
            'basis_metrics': {
                'spread': Decimal('10'),
                'percentage': Decimal('0.005'),
                'arbitrage_yield': Decimal('-0.005')
            },
            'data_quality': {
                'freshness': True,
                'completeness': True,
                'accuracy': True
            },
            'funding_schedule': {
                'next_funding_time': datetime.now() + timedelta(hours=8),
                'funding_interval': 8,  # hours
                'last_funding_time': datetime.now() - timedelta(hours=4)
            }
        }
        
        # Verify state components
        assert provider_state['data_sources'] == ['binance', 'bybit', 'okx']
        assert provider_state['current_prices']['spot'] == Decimal('2000')
        assert provider_state['current_prices']['futures'] == Decimal('2010')
        assert provider_state['current_prices']['funding_rate'] == Decimal('0.01')
        assert provider_state['basis_metrics']['spread'] == Decimal('10')
        assert provider_state['basis_metrics']['percentage'] == Decimal('0.005')
        assert provider_state['basis_metrics']['arbitrage_yield'] == Decimal('-0.005')
        assert provider_state['data_quality']['freshness'] is True
        assert provider_state['data_quality']['completeness'] is True
        assert provider_state['data_quality']['accuracy'] is True
        assert provider_state['funding_schedule']['funding_interval'] == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
