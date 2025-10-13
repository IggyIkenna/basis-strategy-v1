"""
Unit Tests for Live Data Provider Component

Tests LiveDataProvider in isolation with mocked dependencies.
Focuses on real-time data retrieval, caching, and error handling.
"""

import pytest
import asyncio
import aiohttp
import os
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

# Import the component under test
from basis_strategy_v1.infrastructure.data.live_data_provider import (
    LiveDataProvider,
    LiveDataConfig,
    DataSource,
    ERROR_CODES
)


def create_mock_context_manager(mock_response):
    """Helper to create proper async context manager mock."""
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_response)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    return mock_context


class TestLiveDataProviderInitialization:
    """Test component initialization and configuration."""

    @pytest.fixture
    def mock_config(self):
        """Sample configuration dictionary."""
        return {
            'data_requirements': ['eth_prices', 'btc_prices', 'funding_rates'],
            'cache_ttl_seconds': 60,
            'max_retries': 3
        }

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables with API keys."""
        return {
            'BASIS_DEV__CEX__BINANCE_SPOT_API_KEY': 'test_binance_key',
            'BASIS_DEV__CEX__BINANCE_SPOT_SECRET': 'test_binance_secret',
            'BASIS_DEV__CEX__BINANCE_FUTURES_API_KEY': 'test_binance_futures_key',
            'BASIS_DEV__CEX__BINANCE_FUTURES_SECRET': 'test_binance_futures_secret',
            'BASIS_DEV__CEX__BYBIT_API_KEY': 'test_bybit_key',
            'BASIS_DEV__CEX__BYBIT_SECRET': 'test_bybit_secret',
            'BASIS_DEV__CEX__OKX_API_KEY': 'test_okx_key',
            'BASIS_DEV__CEX__OKX_SECRET': 'test_okx_secret',
            'BASIS_DEV__CEX__OKX_PASSPHRASE': 'test_okx_passphrase',
            'BASIS_DOWNLOADERS__ALCHEMY_API_KEY': 'test_alchemy_key',
            'BASIS_DOWNLOADERS__ETHERSCAN_API_KEY': 'test_etherscan_key',
            'BASIS_DEV__ALCHEMY__RPC_URL': 'https://eth-mainnet.g.alchemy.com/v2/test',
            'BASIS_CACHE__TTL__MARKET_DATA': '60',
            'BASIS_LIVE_DATA__MAX_RETRIES': '3',
            'BASIS_LIVE_DATA__TIMEOUT_SECONDS': '10'
        }

    def test_initialization_with_defaults(self):
        """Test basic initialization without parameters."""
        with patch.dict(os.environ, {}, clear=True):
            provider = LiveDataProvider()
            
            assert provider.config == {}
            assert provider.mode is None
            assert provider.redis_client is None
            assert provider.session is None
            assert isinstance(provider.live_config, LiveDataConfig)
            assert provider._price_cache == {}
            assert provider._rate_cache == {}
            assert provider._last_update == {}

    def test_initialization_with_config_and_mode(self, mock_config):
        """Test initialization with config and mode."""
        with patch.dict(os.environ, {}, clear=True):
            provider = LiveDataProvider(config=mock_config, mode='btc_basis')
            
            assert provider.config == mock_config
            assert provider.mode == 'btc_basis'
            assert provider.data_requirements == ['eth_prices', 'btc_prices', 'funding_rates']

    def test_singleton_pattern(self):
        """Test that singleton pattern returns same instance."""
        with patch.dict(os.environ, {}, clear=True):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            
            provider1 = LiveDataProvider()
            provider2 = LiveDataProvider()
            
            assert provider1 is provider2

    @patch.dict(os.environ, {
        'BASIS_DEV__CEX__BINANCE_SPOT_API_KEY': 'test_key',
        'BASIS_DEV__CEX__BINANCE_SPOT_SECRET': 'test_secret'
    })
    def test_load_live_config_from_env(self):
        """Test that live config is loaded from environment variables."""
        provider = LiveDataProvider()
        
        assert provider.live_config.binance_spot_api_key == 'test_key'
        assert provider.live_config.binance_spot_secret == 'test_secret'

    def test_load_data_requirements_for_mode(self, mock_config):
        """Test loading data requirements for specific mode."""
        with patch.dict(os.environ, {}, clear=True):
            provider = LiveDataProvider(config=mock_config, mode='eth_basis')
            
            assert provider.data_requirements == ['eth_prices', 'btc_prices', 'funding_rates']

    def test_load_data_requirements_no_mode(self):
        """Test defaults when no mode specified."""
        with patch.dict(os.environ, {}, clear=True):
            provider = LiveDataProvider()
            
            assert provider.data_requirements == ['eth_prices', 'gas_costs']

    def test_load_data_requirements_missing_config(self):
        """Test warning when data_requirements missing from config."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('basis_strategy_v1.infrastructure.data.live_data_provider.logger') as mock_logger:
                provider = LiveDataProvider(config={}, mode='test_mode')
                
                assert provider.data_requirements == []
                mock_logger.warning.assert_called()


class TestLiveDataConnectionValidation:
    """Test live data connection validation."""

    @pytest.fixture
    def provider_with_mocks(self):
        """Provider with mocked dependencies."""
        with patch.dict(os.environ, {}, clear=True):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider(
                config={'data_requirements': ['eth_prices', 'btc_prices', 'funding_rates']},
                mode='test_mode'
            )
            provider.session = MagicMock()
            return provider

    @pytest.mark.asyncio
    async def test_validate_connections_all_healthy(self, provider_with_mocks):
        """Test validation when all data sources pass."""
        provider = provider_with_mocks
        
        # Mock successful connection tests
        provider._test_eth_spot_connection = AsyncMock(return_value={'price': 3000.0})
        provider._test_btc_spot_connection = AsyncMock(return_value={'price': 50000.0})
        provider._test_funding_rate_connections = AsyncMock(return_value={'binance': {'rate': 0.01}})
        
        result = await provider.validate_live_data_connections()
        
        assert result['overall_status'] == 'healthy'
        assert result['mode'] == 'test_mode'
        assert len(result['connection_tests']) == 3
        assert result['errors'] == []

    @pytest.mark.asyncio
    async def test_validate_connections_partial_failure(self, provider_with_mocks):
        """Test validation when some sources fail."""
        provider = provider_with_mocks
        
        # Mock mixed results
        provider._test_eth_spot_connection = AsyncMock(return_value={'price': 3000.0})
        provider._test_btc_spot_connection = AsyncMock(side_effect=Exception("Connection failed"))
        provider._test_funding_rate_connections = AsyncMock(return_value={'binance': {'rate': 0.01}})
        
        result = await provider.validate_live_data_connections()
        
        assert result['overall_status'] == 'unhealthy'
        assert len(result['errors']) == 1
        assert 'btc_prices: Connection failed' in result['errors']

    @pytest.mark.asyncio
    async def test_validate_connections_unknown_requirement(self, provider_with_mocks):
        """Test validation with unknown data requirement."""
        provider = provider_with_mocks
        provider.data_requirements = ['unknown_data_type']
        
        result = await provider.validate_live_data_connections()
        
        assert result['overall_status'] == 'healthy'  # Unknown requirements don't fail
        assert len(result['warnings']) == 1
        assert 'Unknown data requirement: unknown_data_type' in result['warnings']

    @pytest.mark.asyncio
    async def test_connection_test_eth_spot(self, provider_with_mocks):
        """Test ETH spot price connection test."""
        provider = provider_with_mocks
        provider.get_spot_price = AsyncMock(return_value=3000.0)
        
        result = await provider._test_eth_spot_connection()
        
        assert result['price'] == 3000.0
        assert 'timestamp' in result

    @pytest.mark.asyncio
    async def test_connection_test_btc_spot(self, provider_with_mocks):
        """Test BTC spot price connection test."""
        provider = provider_with_mocks
        provider.get_spot_price = AsyncMock(return_value=50000.0)
        
        result = await provider._test_btc_spot_connection()
        
        assert result['price'] == 50000.0
        assert 'timestamp' in result

    @pytest.mark.asyncio
    async def test_connection_test_funding_rates(self, provider_with_mocks):
        """Test funding rate connections for all venues."""
        provider = provider_with_mocks
        provider.get_funding_rate = AsyncMock(return_value=0.01)
        
        result = await provider._test_funding_rate_connections()
        
        assert 'binance' in result
        assert 'bybit' in result
        assert 'okx' in result
        assert result['binance']['rate'] == 0.01

    @pytest.mark.asyncio
    async def test_connection_test_gas_price(self, provider_with_mocks):
        """Test gas price connection test."""
        provider = provider_with_mocks
        provider.get_gas_cost = AsyncMock(return_value=0.001)
        
        result = await provider._test_gas_price_connection()
        
        assert result['cost'] == 0.001
        assert 'timestamp' in result


class TestSpotPriceRetrieval:
    """Test spot price retrieval functionality."""

    @pytest.fixture
    def provider_with_session(self):
        """Provider with mocked session."""
        with patch.dict(os.environ, {
            'BASIS_DEV__CEX__BINANCE_SPOT_API_KEY': 'test_key',
            'BASIS_DEV__CEX__BINANCE_SPOT_SECRET': 'test_secret'
        }):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider()
            
            # Create proper mock session
            mock_session = MagicMock()
            provider.session = mock_session
            return provider

    @pytest.mark.asyncio
    async def test_get_spot_price_eth_success(self, provider_with_session):
        """Test successful ETH price retrieval."""
        provider = provider_with_session
        
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'price': '3000.50'})
        
        # Mock the context manager properly
        provider.session.get.return_value = create_mock_context_manager(mock_response)
        
        price = await provider.get_spot_price('ETH')
        
        assert price == 3000.50
        provider.session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_spot_price_btc_success(self, provider_with_session):
        """Test successful BTC price retrieval."""
        provider = provider_with_session
        
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'price': '50000.75'})
        
        # Mock the context manager properly
        provider.session.get.return_value = create_mock_context_manager(mock_response)
        
        price = await provider.get_spot_price('BTC')
        
        assert price == 50000.75

    @pytest.mark.asyncio
    async def test_get_spot_price_cached(self, provider_with_session):
        """Test that cached price is returned."""
        provider = provider_with_session
        
        # Pre-populate cache
        cache_key = "spot_price:ETH"
        await provider._set_cache(cache_key, {'price': 3000.0})
        
        price = await provider.get_spot_price('ETH')
        
        assert price == 3000.0
        # Should not call API when cached
        provider.session.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_spot_price_unknown_asset(self, provider_with_session):
        """Test ValueError for unknown asset."""
        provider = provider_with_session
        
        with pytest.raises(ValueError, match="Unknown asset for spot price: UNKNOWN"):
            await provider.get_spot_price('UNKNOWN')

    @pytest.mark.asyncio
    async def test_get_spot_price_binance_api_error(self, provider_with_session):
        """Test API error handling."""
        provider = provider_with_session
        
        # Mock API error
        mock_response = AsyncMock()
        mock_response.status = 500
        
        # Mock the context manager properly
        provider.session.get.return_value = create_mock_context_manager(mock_response)
        
        with pytest.raises(Exception, match="Binance API error: 500"):
            await provider.get_spot_price('ETH')

    @pytest.mark.asyncio
    async def test_get_spot_price_missing_api_key(self):
        """Test error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider()
            provider.session = MagicMock()
            
            with pytest.raises(ValueError, match="Binance spot API key not configured"):
                await provider.get_spot_price('ETH')


class TestFuturesPriceRetrieval:
    """Test futures price retrieval functionality."""

    @pytest.fixture
    def provider_with_futures_config(self):
        """Provider with futures API configuration."""
        with patch.dict(os.environ, {
            'BASIS_DEV__CEX__BINANCE_FUTURES_API_KEY': 'test_futures_key',
            'BASIS_DEV__CEX__BYBIT_API_KEY': 'test_bybit_key',
            'BASIS_DEV__CEX__OKX_API_KEY': 'test_okx_key'
        }):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider()
            provider.session = MagicMock()
            return provider

    @pytest.mark.asyncio
    async def test_get_futures_price_binance_success(self, provider_with_futures_config):
        """Test Binance futures price retrieval."""
        provider = provider_with_futures_config
        
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'price': '3001.25'})
        
        # Mock the context manager properly
        provider.session.get.return_value = create_mock_context_manager(mock_response)
        
        price = await provider.get_futures_price('ETH', 'binance')
        
        assert price == 3001.25

    @pytest.mark.asyncio
    async def test_get_futures_price_bybit_success(self, provider_with_futures_config):
        """Test Bybit futures price retrieval."""
        provider = provider_with_futures_config
        
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'retCode': 0,
            'result': {
                'list': [{'lastPrice': '3002.50'}]
            }
        })
        
        # Mock the context manager properly
        provider.session.get.return_value = create_mock_context_manager(mock_response)
        
        price = await provider.get_futures_price('ETH', 'bybit')
        
        assert price == 3002.50

    @pytest.mark.asyncio
    async def test_get_futures_price_okx_success(self, provider_with_futures_config):
        """Test OKX futures price retrieval."""
        provider = provider_with_futures_config
        
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'code': '0',
            'data': [{'last': '3003.75'}]
        })
        
        # Mock the context manager properly
        provider.session.get.return_value = create_mock_context_manager(mock_response)
        
        price = await provider.get_futures_price('ETH', 'okx')
        
        assert price == 3003.75

    @pytest.mark.asyncio
    async def test_get_futures_price_cached(self, provider_with_futures_config):
        """Test cached futures price."""
        provider = provider_with_futures_config
        
        # Pre-populate cache
        cache_key = "futures_price:ETH:binance"
        await provider._set_cache(cache_key, {'price': 3000.0})
        
        price = await provider.get_futures_price('ETH', 'binance')
        
        assert price == 3000.0
        provider.session.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_futures_price_unknown_venue(self, provider_with_futures_config):
        """Test ValueError for unknown venue."""
        provider = provider_with_futures_config
        
        with pytest.raises(ValueError, match="Unknown venue for futures price: unknown"):
            await provider.get_futures_price('ETH', 'unknown')

    @pytest.mark.asyncio
    async def test_get_futures_price_api_error(self, provider_with_futures_config):
        """Test API error handling."""
        provider = provider_with_futures_config
        
        # Mock API error
        mock_response = AsyncMock()
        mock_response.status = 500
        
        # Mock the context manager properly
        provider.session.get.return_value = create_mock_context_manager(mock_response)
        
        with pytest.raises(Exception, match="Binance futures API error: 500"):
            await provider.get_futures_price('ETH', 'binance')


class TestFundingRateRetrieval:
    """Test funding rate retrieval functionality."""

    @pytest.fixture
    def provider_with_funding_config(self):
        """Provider with funding rate API configuration."""
        with patch.dict(os.environ, {
            'BASIS_DEV__CEX__BINANCE_FUTURES_API_KEY': 'test_futures_key',
            'BASIS_DEV__CEX__BYBIT_API_KEY': 'test_bybit_key',
            'BASIS_DEV__CEX__OKX_API_KEY': 'test_okx_key'
        }):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider()
            provider.session = MagicMock()
            return provider

    @pytest.mark.asyncio
    async def test_get_funding_rate_binance_success(self, provider_with_funding_config):
        """Test Binance funding rate retrieval."""
        provider = provider_with_funding_config
        
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'lastFundingRate': '0.0001'})
        
        # Mock the context manager properly
        provider.session.get.return_value = create_mock_context_manager(mock_response)
        
        rate = await provider.get_funding_rate('ETH', 'binance')
        
        assert rate == 0.0001

    @pytest.mark.asyncio
    async def test_get_funding_rate_bybit_success(self, provider_with_funding_config):
        """Test Bybit funding rate retrieval."""
        provider = provider_with_funding_config
        
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'retCode': 0,
            'result': {
                'list': [{'fundingRate': '0.0002'}]
            }
        })
        
        # Mock the context manager properly
        provider.session.get.return_value = create_mock_context_manager(mock_response)
        
        rate = await provider.get_funding_rate('ETH', 'bybit')
        
        assert rate == 0.0002

    @pytest.mark.asyncio
    async def test_get_funding_rate_okx_success(self, provider_with_funding_config):
        """Test OKX funding rate retrieval."""
        provider = provider_with_funding_config
        
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'code': '0',
            'data': [{'fundingRate': '0.0003'}]
        })
        
        # Mock the context manager properly
        provider.session.get.return_value = create_mock_context_manager(mock_response)
        
        rate = await provider.get_funding_rate('ETH', 'okx')
        
        assert rate == 0.0003

    @pytest.mark.asyncio
    async def test_get_funding_rate_cached(self, provider_with_funding_config):
        """Test cached funding rate."""
        provider = provider_with_funding_config
        
        # Pre-populate cache
        cache_key = "funding_rate:ETH:binance"
        await provider._set_cache(cache_key, {'rate': 0.0001})
        
        rate = await provider.get_funding_rate('ETH', 'binance')
        
        assert rate == 0.0001
        provider.session.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_funding_rate_unknown_venue(self, provider_with_funding_config):
        """Test ValueError for unknown venue."""
        provider = provider_with_funding_config
        
        with pytest.raises(ValueError, match="Unknown venue for funding rate: unknown"):
            await provider.get_funding_rate('ETH', 'unknown')

    @pytest.mark.asyncio
    async def test_get_funding_rate_api_error(self, provider_with_funding_config):
        """Test API error handling."""
        provider = provider_with_funding_config
        
        # Mock API error
        mock_response = AsyncMock()
        mock_response.status = 500
        
        # Mock the context manager properly
        provider.session.get.return_value = create_mock_context_manager(mock_response)
        
        with pytest.raises(Exception, match="Binance funding rate API error: 500"):
            await provider.get_funding_rate('ETH', 'binance')


class TestDeFiProtocolData:
    """Test DeFi protocol data retrieval."""

    @pytest.fixture
    def provider_with_defi_config(self):
        """Provider with DeFi configuration."""
        with patch.dict(os.environ, {
            'BASIS_DOWNLOADERS__ALCHEMY_API_KEY': 'test_alchemy_key'
        }):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider()
            return provider

    @pytest.mark.asyncio
    async def test_get_aave_index_success(self, provider_with_defi_config):
        """Test AAVE index retrieval (placeholder)."""
        provider = provider_with_defi_config
        
        index = await provider.get_aave_index('USDC', 'liquidity')
        
        assert index == 1.0  # Placeholder value

    @pytest.mark.asyncio
    async def test_get_aave_index_cached(self, provider_with_defi_config):
        """Test cached AAVE index."""
        provider = provider_with_defi_config
        
        # Pre-populate cache
        cache_key = "aave_index:USDC:liquidity"
        await provider._set_cache(cache_key, {'index': 1.05})
        
        index = await provider.get_aave_index('USDC', 'liquidity')
        
        assert index == 1.05

    @pytest.mark.asyncio
    async def test_get_oracle_price_success(self, provider_with_defi_config):
        """Test oracle price retrieval (placeholder)."""
        provider = provider_with_defi_config
        
        price = await provider.get_oracle_price('stETH')
        
        assert price == 1.0  # Placeholder value

    @pytest.mark.asyncio
    async def test_get_oracle_price_cached(self, provider_with_defi_config):
        """Test cached oracle price."""
        provider = provider_with_defi_config
        
        # Pre-populate cache
        cache_key = "oracle_price:stETH"
        await provider._set_cache(cache_key, {'price': 1.02})
        
        price = await provider.get_oracle_price('stETH')
        
        assert price == 1.02

    @pytest.mark.asyncio
    async def test_get_lst_market_price_success(self, provider_with_defi_config):
        """Test LST market price (placeholder)."""
        provider = provider_with_defi_config
        
        price = await provider.get_lst_market_price('stETH')
        
        assert price == 1.0  # Placeholder value

    @pytest.mark.asyncio
    async def test_get_lst_market_price_cached(self, provider_with_defi_config):
        """Test cached LST market price."""
        provider = provider_with_defi_config
        
        # Pre-populate cache
        cache_key = "lst_market_price:stETH"
        await provider._set_cache(cache_key, {'price': 1.01})
        
        price = await provider.get_lst_market_price('stETH')
        
        assert price == 1.01


class TestGasCostRetrieval:
    """Test gas cost retrieval functionality."""

    @pytest.fixture
    def provider_with_gas_config(self):
        """Provider with gas price API configuration."""
        with patch.dict(os.environ, {
            'BASIS_DOWNLOADERS__ETHERSCAN_API_KEY': 'test_etherscan_key'
        }):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider()
            provider.session = MagicMock()
            return provider

    @pytest.mark.asyncio
    async def test_get_gas_cost_success(self, provider_with_gas_config):
        """Test gas cost from Etherscan."""
        provider = provider_with_gas_config
        
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'status': '1',
            'result': {
                'ProposeGasPrice': '20'
            }
        })
        
        # Mock the context manager properly
        provider.session.get.return_value = create_mock_context_manager(mock_response)
        
        cost = await provider.get_gas_cost('standard')
        
        assert cost == 20e-9  # Converted from gwei to ETH

    @pytest.mark.asyncio
    async def test_get_gas_cost_cached(self, provider_with_gas_config):
        """Test cached gas cost."""
        provider = provider_with_gas_config
        
        # Pre-populate cache
        cache_key = "gas_cost:standard"
        await provider._set_cache(cache_key, {'cost': 0.001})
        
        cost = await provider.get_gas_cost('standard')
        
        assert cost == 0.001
        provider.session.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_gas_cost_missing_api_key(self):
        """Test default value when API key missing."""
        with patch.dict(os.environ, {}, clear=True):
            provider = LiveDataProvider()
            provider.session = MagicMock()
            
            cost = await provider.get_gas_cost('standard')
            
            assert cost == 0.001  # Default value

    @pytest.mark.asyncio
    async def test_get_gas_cost_api_error(self, provider_with_gas_config):
        """Test API error handling."""
        provider = provider_with_gas_config
        
        # Mock API error
        mock_response = AsyncMock()
        mock_response.status = 500
        
        # Mock the context manager properly
        provider.session.get.return_value = create_mock_context_manager(mock_response)
        
        with pytest.raises(Exception, match="Etherscan gas API error: 500"):
            await provider.get_gas_cost('standard')


class TestMarketDataSnapshot:
    """Test market data snapshot functionality."""

    @pytest.fixture
    def provider_with_snapshot_mocks(self):
        """Provider with mocked data methods."""
        with patch.dict(os.environ, {
            'BASIS_DEV__CEX__BINANCE_SPOT_API_KEY': 'test_key',
            'BASIS_DEV__CEX__BINANCE_FUTURES_API_KEY': 'test_futures_key',
            'BASIS_DEV__CEX__BYBIT_API_KEY': 'test_bybit_key',
            'BASIS_DEV__CEX__OKX_API_KEY': 'test_okx_key',
            'BASIS_DOWNLOADERS__ETHERSCAN_API_KEY': 'test_etherscan_key'
        }):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider()
            provider.session = MagicMock()
            
            # Mock all data retrieval methods
            provider.get_spot_price = AsyncMock(side_effect=lambda asset: 3000.0 if asset == 'ETH' else 50000.0)
            provider.get_futures_price = AsyncMock(return_value=3001.0)
            provider.get_funding_rate = AsyncMock(return_value=0.0001)
            provider.get_gas_cost = AsyncMock(return_value=0.001)
            
            return provider

    @pytest.mark.asyncio
    async def test_get_market_data_snapshot_success(self, provider_with_snapshot_mocks):
        """Test successful market data snapshot."""
        provider = provider_with_snapshot_mocks
        
        snapshot = await provider.get_market_data_snapshot()
        
        assert 'timestamp' in snapshot
        assert snapshot['eth_usd_price'] == 3000.0
        assert snapshot['btc_usd_price'] == 50000.0
        assert snapshot['binance_eth_perp'] == 3001.0
        assert snapshot['bybit_eth_perp'] == 3001.0
        assert snapshot['okx_eth_perp'] == 3001.0
        assert snapshot['binance_funding_rate'] == 0.0001
        assert snapshot['bybit_funding_rate'] == 0.0001
        assert snapshot['okx_funding_rate'] == 0.0001
        assert snapshot['gas_price_gwei'] == 1000000.0  # 0.001 ETH * 1e9

    @pytest.mark.asyncio
    async def test_get_market_data_snapshot_partial_failure(self, provider_with_snapshot_mocks):
        """Test snapshot with some sources failing."""
        provider = provider_with_snapshot_mocks
        
        # Make some methods fail
        async def mock_spot_price(asset):
            if asset == 'ETH':
                raise Exception("API error")
            return 50000.0
        
        provider.get_spot_price = mock_spot_price
        
        snapshot = await provider.get_market_data_snapshot()
        
        assert snapshot['eth_usd_price'] is None
        assert snapshot['btc_usd_price'] == 50000.0

    @pytest.mark.asyncio
    async def test_get_market_data_snapshot_funding_rate_failure(self, provider_with_snapshot_mocks):
        """Test snapshot raises error for funding rate failure."""
        provider = provider_with_snapshot_mocks
        
        # Make funding rate fail
        provider.get_funding_rate = AsyncMock(side_effect=Exception("Funding rate API error"))
        
        with pytest.raises(ValueError, match="Failed to get binance funding rate data"):
            await provider.get_market_data_snapshot()

    @pytest.mark.asyncio
    async def test_get_market_data_snapshot_gas_cost_failure(self, provider_with_snapshot_mocks):
        """Test snapshot raises error for gas cost failure."""
        provider = provider_with_snapshot_mocks
        
        # Make gas cost fail
        provider.get_gas_cost = AsyncMock(side_effect=Exception("Gas cost API error"))
        
        with pytest.raises(ValueError, match="Failed to get gas cost data"):
            await provider.get_market_data_snapshot()


class TestCacheManagement:
    """Test cache management functionality."""

    @pytest.fixture
    def provider_with_cache(self):
        """Provider for cache testing."""
        with patch.dict(os.environ, {}, clear=True):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider()
            return provider

    @pytest.mark.asyncio
    async def test_cache_get_valid(self, provider_with_cache):
        """Test retrieving valid cached data."""
        provider = provider_with_cache
        
        # Set cache with current timestamp
        cache_key = "test_key"
        test_data = {'price': 3000.0}
        await provider._set_cache(cache_key, test_data)
        
        # Should return cached data
        cached_data = await provider._get_from_cache(cache_key)
        assert cached_data == test_data

    @pytest.mark.asyncio
    async def test_cache_get_expired(self, provider_with_cache):
        """Test expired cache returns None."""
        provider = provider_with_cache
        
        # Set cache with old timestamp
        cache_key = "test_key"
        test_data = {'price': 3000.0}
        provider._price_cache[cache_key] = test_data
        provider._last_update[cache_key] = datetime.now(timezone.utc) - timedelta(seconds=120)
        
        # Should return None for expired cache
        cached_data = await provider._get_from_cache(cache_key)
        assert cached_data is None

    @pytest.mark.asyncio
    async def test_cache_get_missing(self, provider_with_cache):
        """Test missing cache returns None."""
        provider = provider_with_cache
        
        cached_data = await provider._get_from_cache("missing_key")
        assert cached_data is None

    @pytest.mark.asyncio
    async def test_cache_set(self, provider_with_cache):
        """Test cache data is stored correctly."""
        provider = provider_with_cache
        
        cache_key = "test_key"
        test_data = {'price': 3000.0}
        
        await provider._set_cache(cache_key, test_data)
        
        assert provider._price_cache[cache_key] == test_data
        assert cache_key in provider._last_update

    @pytest.mark.asyncio
    async def test_clear_cache(self, provider_with_cache):
        """Test cache is cleared completely."""
        provider = provider_with_cache
        
        # Populate cache
        await provider._set_cache("key1", {'data': 1})
        await provider._set_cache("key2", {'data': 2})
        
        # Clear cache
        await provider.clear_cache()
        
        assert provider._price_cache == {}
        assert provider._last_update == {}


class TestAsyncContextManager:
    """Test async context manager functionality."""

    @pytest.mark.asyncio
    async def test_async_context_manager_session_creation(self):
        """Test session is created on enter."""
        with patch.dict(os.environ, {}, clear=True):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider()
            
            async with provider as p:
                assert p.session is not None
                assert isinstance(p.session, aiohttp.ClientSession)

    @pytest.mark.asyncio
    async def test_async_context_manager_session_cleanup(self):
        """Test session is closed on exit."""
        with patch.dict(os.environ, {}, clear=True):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider()
            
            async with provider as p:
                session = p.session
            
            # Session should be closed after context exit
            assert session.closed

    @pytest.mark.asyncio
    async def test_async_context_manager_with_error(self):
        """Test session is closed even with errors."""
        with patch.dict(os.environ, {}, clear=True):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider()
            
            try:
                async with provider as p:
                    session = p.session
                    raise Exception("Test error")
            except Exception:
                pass
            
            # Session should still be closed
            assert session.closed


class TestErrorHandling:
    """Test error handling functionality."""

    def test_error_codes_defined(self):
        """Test that all error codes are defined."""
        expected_codes = [
            'LIVE-001', 'LIVE-002', 'LIVE-003', 'LIVE-004', 'LIVE-005',
            'LIVE-006', 'LIVE-007', 'LIVE-008', 'LIVE-009', 'LIVE-010'
        ]
        
        for code in expected_codes:
            assert code in ERROR_CODES
            assert ERROR_CODES[code] is not None

    @pytest.mark.asyncio
    async def test_api_timeout_handling(self):
        """Test timeout errors are handled gracefully."""
        with patch.dict(os.environ, {
            'BASIS_DEV__CEX__BINANCE_SPOT_API_KEY': 'test_key'
        }):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider()
            
            # Mock timeout error
            provider.session = MagicMock()
            provider.session.get.side_effect = asyncio.TimeoutError("Request timeout")
            
            with pytest.raises(asyncio.TimeoutError):
                await provider.get_spot_price('ETH')

    @pytest.mark.asyncio
    async def test_network_connection_failure(self):
        """Test network connection failures."""
        with patch.dict(os.environ, {
            'BASIS_DEV__CEX__BINANCE_SPOT_API_KEY': 'test_key'
        }):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider()
            
            # Mock connection error
            provider.session = MagicMock()
            provider.session.get.side_effect = aiohttp.ClientConnectorError(
                Mock(), OSError("Connection failed")
            )
            
            with pytest.raises(aiohttp.ClientConnectorError):
                await provider.get_spot_price('ETH')

    @pytest.mark.asyncio
    async def test_api_rate_limit_handling(self):
        """Test rate limit errors are handled."""
        with patch.dict(os.environ, {
            'BASIS_DEV__CEX__BINANCE_SPOT_API_KEY': 'test_key'
        }):
            # Reset singleton for testing
            LiveDataProvider._instance = None
            provider = LiveDataProvider()
            
            # Mock rate limit error
            provider.session = MagicMock()
            mock_response = AsyncMock()
            mock_response.status = 429  # Too Many Requests
            
            # Mock the context manager properly
            provider.session.get.return_value = create_mock_context_manager(mock_response)
            
            with pytest.raises(Exception, match="Binance API error: 429"):
                await provider.get_spot_price('ETH')
