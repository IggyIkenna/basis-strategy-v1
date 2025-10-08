"""
Unit tests for LiveDataProvider

Tests the live data provider functionality for real-time data sources.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd
from datetime import datetime, timezone

# Add backend to path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.infrastructure.data.live_data_provider import LiveDataProvider, LiveDataConfig


class TestLiveDataProvider:
    """Test cases for LiveDataProvider."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'mode': 'eth_leveraged',
            'share_class': 'ETH',
            'execution_mode': 'live'
        }
    
    @pytest.fixture
    def live_provider(self, mock_config):
        """Create LiveDataProvider instance for testing."""
        with patch.dict(os.environ, {
            'BASIS_DEV__CEX__BINANCE_SPOT_API_KEY': 'test_key',
            'BASIS_DEV__CEX__BINANCE_SPOT_SECRET': 'test_secret',
            'BASIS_DOWNLOADERS__ALCHEMY_API_KEY': 'test_alchemy_key'
        }):
            return LiveDataProvider(config=mock_config)
    
    def test_live_config_loading(self, live_provider):
        """Test that live configuration is loaded correctly."""
        config = live_provider.live_config
        
        assert config.binance_spot_api_key == 'test_key'
        assert config.binance_spot_secret == 'test_secret'
        assert config.alchemy_api_key == 'test_alchemy_key'
        assert config.cache_ttl_seconds == 60  # Default value
        assert config.max_retries == 3  # Default value
        assert config.timeout_seconds == 10  # Default value
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, live_provider):
        """Test async context manager functionality."""
        async with live_provider as provider:
            assert provider.session is not None
            assert isinstance(provider.session, Mock)  # Will be mocked in real test
        
        # Session should be closed after context
        assert live_provider.session is None
    
    @pytest.mark.asyncio
    async def test_get_spot_price_eth(self, live_provider):
        """Test getting ETH spot price."""
        # Mock the HTTP response
        mock_response_data = {'price': '3500.50'}
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with live_provider:
                price = await live_provider.get_spot_price('ETH')
                assert price == 3500.50
    
    @pytest.mark.asyncio
    async def test_get_spot_price_btc(self, live_provider):
        """Test getting BTC spot price."""
        # Mock the HTTP response
        mock_response_data = {'price': '45000.75'}
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with live_provider:
                price = await live_provider.get_spot_price('BTC')
                assert price == 45000.75
    
    @pytest.mark.asyncio
    async def test_get_futures_price_binance(self, live_provider):
        """Test getting Binance futures price."""
        # Mock the HTTP response
        mock_response_data = {'price': '3501.25'}
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with live_provider:
                price = await live_provider.get_futures_price('ETH', 'binance')
                assert price == 3501.25
    
    @pytest.mark.asyncio
    async def test_get_funding_rate_binance(self, live_provider):
        """Test getting Binance funding rate."""
        # Mock the HTTP response
        mock_response_data = {'lastFundingRate': '0.0001'}
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with live_provider:
                rate = await live_provider.get_funding_rate('ETH', 'binance')
                assert rate == 0.0001
    
    @pytest.mark.asyncio
    async def test_get_market_data_snapshot(self, live_provider):
        """Test getting complete market data snapshot."""
        # Mock multiple HTTP responses
        mock_responses = [
            {'price': '3500.50'},  # ETH spot
            {'price': '45000.75'},  # BTC spot
            {'price': '3501.25'},  # ETH futures
            {'price': '3502.00'},  # ETH futures bybit
            {'price': '3503.00'},  # ETH futures okx
            {'lastFundingRate': '0.0001'},  # Funding rate
            {'lastFundingRate': '0.0002'},  # Funding rate bybit
            {'lastFundingRate': '0.0003'},  # Funding rate okx
        ]
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(side_effect=mock_responses)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Mock gas cost
            with patch.object(live_provider, '_get_gas_cost_live', return_value=0.001):
                async with live_provider:
                    snapshot = await live_provider.get_market_data_snapshot()
                    
                    assert 'timestamp' in snapshot
                    assert snapshot['eth_usd_price'] == 3500.50
                    assert snapshot['btc_usd_price'] == 45000.75
                    assert snapshot['binance_eth_perp'] == 3501.25
                    assert snapshot['bybit_eth_perp'] == 3502.00
                    assert snapshot['okx_eth_perp'] == 3503.00
                    assert snapshot['binance_funding_rate'] == 0.0001
                    assert snapshot['bybit_funding_rate'] == 0.0002
                    assert snapshot['okx_funding_rate'] == 0.0003
                    assert snapshot['gas_price_gwei'] == 1.0  # 0.001 ETH * 1e9
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, live_provider):
        """Test caching functionality."""
        # Mock the HTTP response
        mock_response_data = {'price': '3500.50'}
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with live_provider:
                # First call should make HTTP request
                price1 = await live_provider.get_spot_price('ETH')
                assert price1 == 3500.50
                assert mock_get.call_count == 1
                
                # Second call should use cache (no additional HTTP request)
                price2 = await live_provider.get_spot_price('ETH')
                assert price2 == 3500.50
                assert mock_get.call_count == 1  # No additional calls
    
    def test_invalid_asset_raises_error(self, live_provider):
        """Test that invalid asset raises ValueError."""
        with pytest.raises(ValueError, match="Unknown asset for spot price"):
            asyncio.run(live_provider.get_spot_price('INVALID'))
    
    def test_invalid_venue_raises_error(self, live_provider):
        """Test that invalid venue raises ValueError."""
        with pytest.raises(ValueError, match="Unknown venue for futures price"):
            asyncio.run(live_provider.get_futures_price('ETH', 'INVALID'))
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, live_provider):
        """Test API error handling."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500  # Server error
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with live_provider:
                with pytest.raises(Exception, match="Binance API error: 500"):
                    await live_provider.get_spot_price('ETH')
    
    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        # Create provider without API keys
        with patch.dict(os.environ, {}, clear=True):
            provider = LiveDataProvider()
            
            with pytest.raises(ValueError, match="Binance spot API key not configured"):
                asyncio.run(provider.get_spot_price('ETH'))


class TestLiveDataConfig:
    """Test cases for LiveDataConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = LiveDataConfig()
        
        assert config.cache_ttl_seconds == 60
        assert config.max_retries == 3
        assert config.timeout_seconds == 10
        assert config.binance_spot_api_key is None
        assert config.binance_spot_secret is None
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = LiveDataConfig(
            cache_ttl_seconds=120,
            max_retries=5,
            timeout_seconds=15,
            binance_spot_api_key='custom_key'
        )
        
        assert config.cache_ttl_seconds == 120
        assert config.max_retries == 5
        assert config.timeout_seconds == 15
        assert config.binance_spot_api_key == 'custom_key'
