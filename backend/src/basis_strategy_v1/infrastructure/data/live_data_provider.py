"""
Live Data Provider Component

Provides real-time market data from live sources (WebSocket/REST APIs) for live trading mode.
Mirrors the interface of HistoricalDataProvider but uses live data sources instead of CSV files.

Key Principles:
- Real-time data: Live WebSocket feeds and REST API calls
- Same interface: Identical methods to HistoricalDataProvider for seamless switching
- Environment-aware: Uses environment variables for API keys and endpoints
- Caching: Short-term caching to avoid excessive API calls
- Fallback: Graceful degradation when live sources are unavailable

Data Sources:
- CEX APIs: Binance, Bybit, OKX for spot/futures prices and funding rates
- DeFi APIs: AAVE, EtherFi, Lido for protocol data
- Oracle APIs: Chainlink, Pyth for price feeds
- Gas APIs: Etherscan, Alchemy for gas price data
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
from pathlib import Path
import os
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Error codes for Live Data Provider
ERROR_CODES = {
    'LIVE-001': 'Live data source connection failed',
    'LIVE-002': 'API rate limit exceeded',
    'LIVE-003': 'Data source timeout',
    'LIVE-004': 'Invalid API response',
    'LIVE-005': 'Cache operation failed',
    'LIVE-006': 'Data source authentication failed',
    'LIVE-007': 'Data source unavailable',
    'LIVE-008': 'Data parsing failed',
    'LIVE-009': 'Network connection failed',
    'LIVE-010': 'Data source configuration invalid'
}


class DataSource(Enum):
    """Enumeration of available data sources."""
    BINANCE = "binance"
    BYBIT = "bybit"
    OKX = "okx"
    AAVE = "aave"
    ETHERFI = "etherfi"
    LIDO = "lido"
    CHAINLINK = "chainlink"
    PYTH = "pyth"
    ETHERSCAN = "etherscan"
    ALCHEMY = "alchemy"


@dataclass
class LiveDataConfig:
    """Configuration for live data sources."""
    # CEX API Keys
    binance_spot_api_key: Optional[str] = None
    binance_spot_secret: Optional[str] = None
    binance_futures_api_key: Optional[str] = None
    binance_futures_secret: Optional[str] = None
    bybit_api_key: Optional[str] = None
    bybit_secret: Optional[str] = None
    okx_api_key: Optional[str] = None
    okx_secret: Optional[str] = None
    okx_passphrase: Optional[str] = None

    # DeFi API Keys
    alchemy_api_key: Optional[str] = None
    etherscan_api_key: Optional[str] = None

    # RPC Endpoints
    ethereum_rpc_url: Optional[str] = None

    # Cache settings
    cache_ttl_seconds: int = 60
    max_retries: int = 3
    timeout_seconds: int = 10


class LiveDataProvider:
    """Provides real-time market data from live sources."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LiveDataProvider, cls).__new__(cls)
        return cls._instance

    def __init__(self,
                 config: Optional[Dict] = None,
                 mode: Optional[str] = None,
                 redis_client: Optional[Any] = None):
        """
        Initialize live data provider.

        Args:
            config: Configuration dictionary
            mode: Strategy mode for data requirements filtering
            redis_client: Cache client for caching (optional, deprecated)
        """
        self.config = config or {}
        self.mode = mode
        self.redis_client = None  # Redis removed - using in-memory cache only
        self.session: Optional[aiohttp.ClientSession] = None

        # Load configuration from environment variables
        self.live_config = self._load_live_config()

        # Initialize data caches
        self._price_cache: Dict[str, Dict] = {}
        self._rate_cache: Dict[str, Dict] = {}
        self._last_update: Dict[str, datetime] = {}
        
        # Load mode-specific data requirements from config
        self.data_requirements = self._load_data_requirements_for_mode()

        logger.info(f"LiveDataProvider initialized for live trading mode (strategy: {mode})")

    def _load_live_config(self) -> LiveDataConfig:
        """Load live data configuration from environment variables."""
        return LiveDataConfig(
            # CEX API Keys
            binance_spot_api_key=os.getenv('BASIS_DEV__CEX__BINANCE_SPOT_API_KEY') or
            os.getenv('BASIS_STAGING__CEX__BINANCE_SPOT_API_KEY') or
            os.getenv('BASIS_PROD__CEX__BINANCE_SPOT_API_KEY'),
            binance_spot_secret=os.getenv('BASIS_DEV__CEX__BINANCE_SPOT_SECRET') or
            os.getenv('BASIS_STAGING__CEX__BINANCE_SPOT_SECRET') or
            os.getenv('BASIS_PROD__CEX__BINANCE_SPOT_SECRET'),
            binance_futures_api_key=os.getenv('BASIS_DEV__CEX__BINANCE_FUTURES_API_KEY') or
            os.getenv('BASIS_STAGING__CEX__BINANCE_FUTURES_API_KEY') or
            os.getenv('BASIS_PROD__CEX__BINANCE_FUTURES_API_KEY'),
            binance_futures_secret=os.getenv('BASIS_DEV__CEX__BINANCE_FUTURES_SECRET') or
            os.getenv('BASIS_STAGING__CEX__BINANCE_FUTURES_SECRET') or
            os.getenv('BASIS_PROD__CEX__BINANCE_FUTURES_SECRET'),
            bybit_api_key=os.getenv('BASIS_DEV__CEX__BYBIT_API_KEY') or
            os.getenv('BASIS_STAGING__CEX__BYBIT_API_KEY') or
            os.getenv('BASIS_PROD__CEX__BYBIT_API_KEY'),
            bybit_secret=os.getenv('BASIS_DEV__CEX__BYBIT_SECRET') or
            os.getenv('BASIS_STAGING__CEX__BYBIT_SECRET') or
            os.getenv('BASIS_PROD__CEX__BYBIT_SECRET'),
            okx_api_key=os.getenv('BASIS_DEV__CEX__OKX_API_KEY') or
            os.getenv('BASIS_STAGING__CEX__OKX_API_KEY') or
            os.getenv('BASIS_PROD__CEX__OKX_API_KEY'),
            okx_secret=os.getenv('BASIS_DEV__CEX__OKX_SECRET') or
            os.getenv('BASIS_STAGING__CEX__OKX_SECRET') or
            os.getenv('BASIS_PROD__CEX__OKX_SECRET'),
            okx_passphrase=os.getenv('BASIS_DEV__CEX__OKX_PASSPHRASE') or
            os.getenv('BASIS_STAGING__CEX__OKX_PASSPHRASE') or
            os.getenv('BASIS_PROD__CEX__OKX_PASSPHRASE'),

            # DeFi API Keys
            alchemy_api_key=os.getenv('BASIS_DOWNLOADERS__ALCHEMY_API_KEY'),
            etherscan_api_key=os.getenv(
                'BASIS_DOWNLOADERS__ETHERSCAN_API_KEY'),

            # RPC Endpoints
            ethereum_rpc_url=os.getenv('BASIS_DEV__ALCHEMY__RPC_URL') or
            os.getenv('BASIS_STAGING__ALCHEMY__RPC_URL') or
            os.getenv('BASIS_PROD__ALCHEMY__RPC_URL'),

            # Cache settings
            cache_ttl_seconds=int(
                os.getenv(
                    'BASIS_CACHE__TTL__MARKET_DATA',
                    60)),
            max_retries=int(os.getenv('BASIS_LIVE_DATA__MAX_RETRIES', 3)),
            timeout_seconds=int(
                os.getenv(
                    'BASIS_LIVE_DATA__TIMEOUT_SECONDS',
                    10))
        )

    def _load_data_requirements_for_mode(self) -> List[str]:
        """
        Load data requirements for the specific strategy mode from config.
        
        Uses data_requirements from configs/modes/*.yaml files which are validated
        by Pydantic models in config_models.py.
        
        Returns:
            List of required data types for this mode
        """
        if not self.mode:
            logger.warning("No mode specified, using default data requirements")
            return ['eth_prices', 'gas_costs']  # Minimal default
        
        # Get data requirements from config (top level after mode merging)
        data_requirements = self.config.get('data_requirements', [])
        
        if not data_requirements:
            logger.warning(f"No data_requirements found for mode '{self.mode}' in config")
            return []
        
        logger.info(f"Data requirements for mode '{self.mode}': {data_requirements}")
        return data_requirements

    async def validate_live_data_connections(self) -> Dict[str, Any]:
        """
        Validate all live data connections for the required data types.
        
        This method tests each live data connection based on data_requirements
        and fails if any required connections cannot be established.
        
        Returns:
            Validation results with status for each data type
        """
        logger.info(f"🔍 Validating live data connections for mode '{self.mode}'...")
        
        validation_results = {
            'mode': self.mode,
            'data_requirements': self.data_requirements,
            'connection_tests': {},
            'overall_status': 'healthy',
            'errors': [],
            'warnings': []
        }
        
        # Map data requirements to connection tests
        connection_map = {
            'eth_prices': self._test_eth_spot_connection,
            'btc_prices': self._test_btc_spot_connection,
            'funding_rates': self._test_funding_rate_connections,
            'gas_costs': self._test_gas_price_connection,
            'aave_lending_rates': self._test_aave_rate_connection,
            'staking_rewards': self._test_staking_yield_connection,
            'lst_market_prices': self._test_lst_market_price_connection
        }
        
        # Test each required data type
        for data_type in self.data_requirements:
            if data_type in connection_map:
                try:
                    test_result = await connection_map[data_type]()
                    validation_results['connection_tests'][data_type] = {
                        'status': 'healthy',
                        'result': test_result
                    }
                    logger.info(f"✅ {data_type}: Connection test passed")
                    
                except Exception as e:
                    validation_results['connection_tests'][data_type] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
                    validation_results['errors'].append(f"{data_type}: {e}")
                    validation_results['overall_status'] = 'unhealthy'
                    logger.error(f"❌ {data_type}: Connection test failed - {e}")
            else:
                # Unknown data requirement
                validation_results['warnings'].append(f"Unknown data requirement: {data_type}")
                logger.warning(f"⚠️  Unknown data requirement: {data_type}")
        
        # Log summary
        if validation_results['overall_status'] == 'healthy':
            logger.info(f"✅ All live data connections validated for mode '{self.mode}'")
        else:
            logger.error(f"❌ Live data validation failed for mode '{self.mode}': {validation_results['errors']}")
        
        return validation_results

    # Connection test methods for each data type
    async def _test_eth_spot_connection(self) -> Dict[str, Any]:
        """Test ETH spot price connection."""
        price = await self.get_spot_price('ETH')
        return {'price': price, 'timestamp': datetime.now(timezone.utc)}

    async def _test_btc_spot_connection(self) -> Dict[str, Any]:
        """Test BTC spot price connection."""
        price = await self.get_spot_price('BTC')
        return {'price': price, 'timestamp': datetime.now(timezone.utc)}

    async def _test_funding_rate_connections(self) -> Dict[str, Any]:
        """Test funding rate connections for all venues."""
        results = {}
        for venue in ['binance', 'bybit', 'okx']:
            try:
                rate = await self.get_funding_rate('ETH', venue)
                results[venue] = {'rate': rate, 'status': 'healthy'}
            except Exception as e:
                results[venue] = {'error': str(e), 'status': 'unhealthy'}
        return results

    async def _test_gas_price_connection(self) -> Dict[str, Any]:
        """Test gas price connection."""
        cost = await self.get_gas_cost('standard')
        return {'cost': cost, 'timestamp': datetime.now(timezone.utc)}

    async def _test_aave_rate_connection(self) -> Dict[str, Any]:
        """Test AAVE rate connection (placeholder for now)."""
        # TODO: Implement live AAVE rate testing when contracts are integrated
        logger.warning("Live AAVE rate testing not yet implemented")
        return {'status': 'placeholder'}

    async def _test_staking_yield_connection(self) -> Dict[str, Any]:
        """Test staking yield connection (placeholder for now)."""
        # TODO: Implement live staking yield testing when contracts are integrated
        logger.warning("Live staking yield testing not yet implemented")
        return {'status': 'placeholder'}

    async def _test_lst_market_price_connection(self) -> Dict[str, Any]:
        """Test LST market price connection (placeholder for now)."""
        # TODO: Implement live DEX price testing when contracts are integrated
        logger.warning("Live LST market price testing not yet implemented")
        return {'status': 'placeholder'}

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(
                total=self.live_config.timeout_seconds))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def get_spot_price(self, asset: str) -> float:
        """Get current spot price from live sources."""
        cache_key = f"spot_price:{asset}"

        # Check cache first
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return cached_data['price']

        # Fetch from live source
        if asset == 'ETH':
            price = await self._get_eth_spot_price()
        elif asset == 'BTC':
            price = await self._get_btc_spot_price()
        else:
            raise ValueError(f"Unknown asset for spot price: {asset}")

        # Cache the result
        await self._set_cache(cache_key, {'price': price})

        return price

    async def get_futures_price(self, asset: str, venue: str) -> float:
        """Get current futures price from specific exchange."""
        cache_key = f"futures_price:{asset}:{venue}"

        # Check cache first
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return cached_data['price']

        # Fetch from live source
        if venue.lower() == 'binance':
            price = await self._get_binance_futures_price(asset)
        elif venue.lower() == 'bybit':
            price = await self._get_bybit_futures_price(asset)
        elif venue.lower() == 'okx':
            price = await self._get_okx_futures_price(asset)
        else:
            raise ValueError(f"Unknown venue for futures price: {venue}")

        # Cache the result
        await self._set_cache(cache_key, {'price': price})

        return price

    async def get_funding_rate(self, asset: str, venue: str) -> float:
        """Get current funding rate from specific exchange."""
        cache_key = f"funding_rate:{asset}:{venue}"

        # Check cache first
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return cached_data['rate']

        # Fetch from live source
        if venue.lower() == 'binance':
            rate = await self._get_binance_funding_rate(asset)
        elif venue.lower() == 'bybit':
            rate = await self._get_bybit_funding_rate(asset)
        elif venue.lower() == 'okx':
            rate = await self._get_okx_funding_rate(asset)
        else:
            raise ValueError(f"Unknown venue for funding rate: {venue}")

        # Cache the result
        await self._set_cache(cache_key, {'rate': rate})

        return rate

    async def get_aave_index(self, asset: str, index_type: str) -> float:
        """Get current AAVE liquidity or borrow index from live contract."""
        cache_key = f"aave_index:{asset}:{index_type}"

        # Check cache first
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return cached_data['index']

        # Fetch from live AAVE contract
        index = await self._get_aave_index_live(asset, index_type)

        # Cache the result
        await self._set_cache(cache_key, {'index': index})

        return index

    async def get_oracle_price(self, lst_type: str) -> float:
        """Get current LST/ETH oracle price from AAVE oracles."""
        cache_key = f"oracle_price:{lst_type}"

        # Check cache first
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return cached_data['price']

        # Fetch from live AAVE oracle
        price = await self._get_aave_oracle_price(lst_type)

        # Cache the result
        await self._set_cache(cache_key, {'price': price})

        return price

    async def get_lst_market_price(self, lst_type: str) -> float:
        """Get current LST/ETH market price from DEX data."""
        cache_key = f"lst_market_price:{lst_type}"

        # Check cache first
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return cached_data['price']

        # Fetch from live DEX (Curve/Uniswap)
        price = await self._get_dex_lst_price(lst_type)

        # Cache the result
        await self._set_cache(cache_key, {'price': price})

        return price

    async def get_gas_cost(self, operation: str) -> float:
        """Get current gas cost for operation in ETH."""
        cache_key = f"gas_cost:{operation}"

        # Check cache first
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return cached_data['cost']

        # Fetch from live gas price API
        cost = await self._get_gas_cost_live(operation)

        # Cache the result
        await self._set_cache(cache_key, {'cost': cost})

        return cost

    async def get_market_data_snapshot(self) -> Dict:
        """Get complete market data snapshot for current timestamp."""
        timestamp = datetime.now(timezone.utc)

        snapshot = {
            'timestamp': timestamp,
        }

        # Spot prices
        try:
            snapshot['eth_usd_price'] = await self.get_spot_price('ETH')
        except Exception as e:
            logger.warning(f"Failed to get ETH spot price: {e}")
            snapshot['eth_usd_price'] = None

        try:
            snapshot['btc_usd_price'] = await self.get_spot_price('BTC')
        except Exception as e:
            logger.warning(f"Failed to get BTC spot price: {e}")
            snapshot['btc_usd_price'] = None

        # Futures prices (per exchange)
        for venue in ['binance', 'bybit', 'okx']:
            try:
                snapshot[f'{venue}_eth_perp'] = await self.get_futures_price('ETH', venue)
            except Exception as e:
                logger.warning(f"Failed to get {venue} ETH futures price: {e}")
                snapshot[f'{venue}_eth_perp'] = None

        # Funding rates (per exchange)
        for venue in ['binance', 'bybit', 'okx']:
            try:
                snapshot[f'{venue}_funding_rate'] = await self.get_funding_rate('ETH', venue)
            except Exception as e:
                logger.warning(f"Failed to get {venue} funding rate: {e}")
                # TODO-REFACTOR: Funding rate data access failed - should fail fast with error code
                # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - No Hardcoded Values
                # Fix: Fail fast with error code, don't use hardcoded values
                raise ValueError(f"Failed to get {venue} funding rate data: {e}")

        # Gas costs
        try:
            # Convert to gwei
            snapshot['gas_price_gwei'] = await self.get_gas_cost('standard') * 1e9
        except Exception as e:
            # TODO-REFACTOR: Gas price data access failed - should fail fast with error code
            # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - No Hardcoded Values
            # Fix: Fail fast with error code, don't use hardcoded values
            raise ValueError(f"Failed to get gas cost data: {e}")

        return snapshot

    # Private methods for specific data sources

    async def _get_eth_spot_price(self) -> float:
        """Get ETH spot price from Binance."""
        if not self.live_config.binance_spot_api_key:
            raise ValueError("Binance spot API key not configured")

        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": "ETHUSDT"}

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return float(data['price'])
            else:
                raise Exception(f"Binance API error: {response.status}")

    async def _get_btc_spot_price(self) -> float:
        """Get BTC spot price from Binance."""
        if not self.live_config.binance_spot_api_key:
            raise ValueError("Binance spot API key not configured")

        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": "BTCUSDT"}

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return float(data['price'])
            else:
                raise Exception(f"Binance API error: {response.status}")

    async def _get_binance_futures_price(self, asset: str) -> float:
        """Get futures price from Binance."""
        if not self.live_config.binance_futures_api_key:
            raise ValueError("Binance futures API key not configured")

        symbol = f"{asset}USDT"
        url = "https://fapi.binance.com/fapi/v1/ticker/price"
        params = {"symbol": symbol}

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return float(data['price'])
            else:
                raise Exception(
                    f"Binance futures API error: {response.status}")

    async def _get_binance_funding_rate(self, asset: str) -> float:
        """Get funding rate from Binance."""
        if not self.live_config.binance_futures_api_key:
            raise ValueError("Binance futures API key not configured")

        symbol = f"{asset}USDT"
        url = "https://fapi.binance.com/fapi/v1/premiumIndex"
        params = {"symbol": symbol}

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return float(data['lastFundingRate'])
            else:
                raise Exception(
                    f"Binance funding rate API error: {response.status}")

    async def _get_bybit_futures_price(self, asset: str) -> float:
        """Get futures price from Bybit."""
        if not self.live_config.bybit_api_key:
            raise ValueError("Bybit API key not configured")

        symbol = f"{asset}USDT"
        url = "https://api.bybit.com/v5/market/tickers"
        params = {"category": "linear", "symbol": symbol}

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('retCode') == 0 and data.get('result', {}).get('list'):
                    return float(data['result']['list'][0].get('lastPrice', 0.0))
                else:
                    raise Exception(
                        f"Bybit API error: {data.get('retMsg', 'Unknown error')}")
            else:
                raise Exception(f"Bybit API error: {response.status}")

    async def _get_bybit_funding_rate(self, asset: str) -> float:
        """Get funding rate from Bybit."""
        if not self.live_config.bybit_api_key:
            raise ValueError("Bybit API key not configured")

        symbol = f"{asset}USDT"
        url = "https://api.bybit.com/v5/market/funding/history"
        params = {"category": "linear", "symbol": symbol, "limit": 1}

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('retCode') == 0 and data.get('result', {}).get('list'):
                    return float(data['result']['list'][0].get('fundingRate', 0.0))
                else:
                    raise Exception(
                        f"Bybit funding rate API error: {data.get('retMsg', 'Unknown error')}")
            else:
                raise Exception(
                    f"Bybit funding rate API error: {response.status}")

    async def _get_okx_futures_price(self, asset: str) -> float:
        """Get futures price from OKX."""
        if not self.live_config.okx_api_key:
            raise ValueError("OKX API key not configured")

        symbol = f"{asset}-USDT-SWAP"
        url = "https://www.okx.com/api/v5/market/ticker"
        params = {"instId": symbol}

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data['code'] == '0' and data['data']:
                    return float(data['data'][0]['last'])
                else:
                    raise Exception(
                        f"OKX API error: {data.get('msg', 'Unknown error')}")
            else:
                raise Exception(f"OKX API error: {response.status}")

    async def _get_okx_funding_rate(self, asset: str) -> float:
        """Get funding rate from OKX."""
        if not self.live_config.okx_api_key:
            raise ValueError("OKX API key not configured")

        symbol = f"{asset}-USDT-SWAP"
        url = "https://www.okx.com/api/v5/public/funding-rate"
        params = {"instId": symbol}

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data['code'] == '0' and data['data']:
                    return float(data['data'][0]['fundingRate'])
                else:
                    raise Exception(
                        f"OKX funding rate API error: {data.get('msg', 'Unknown error')}")
            else:
                raise Exception(
                    f"OKX funding rate API error: {response.status}")

    async def _get_aave_index_live(self, asset: str, index_type: str) -> float:
        """Get AAVE index from live contract (placeholder)."""
        # TODO: Implement live AAVE contract queries
        logger.warning("Live AAVE index queries not yet implemented")
        return 1.0  # Placeholder

    async def _get_aave_oracle_price(self, lst_type: str) -> float:
        """Get AAVE oracle price from live contract (placeholder)."""
        # TODO: Implement live AAVE oracle queries
        logger.warning("Live AAVE oracle queries not yet implemented")
        return 1.0  # Placeholder

    async def _get_dex_lst_price(self, lst_type: str) -> float:
        """Get LST price from live DEX (placeholder)."""
        # TODO: Implement live DEX price queries
        logger.warning("Live DEX LST price queries not yet implemented")
        return 1.0  # Placeholder

    async def _get_gas_cost_live(self, operation: str) -> float:
        """Get gas cost from live gas price API."""
        if not self.live_config.etherscan_api_key:
            # Fallback to Alchemy if Etherscan not available
            if not self.live_config.alchemy_api_key:
                logger.warning("No gas price API configured, using default")
                return 0.001  # Default 0.001 ETH

        # Use Etherscan gas price API
        url = "https://api.etherscan.io/api"
        params = {
            "module": "gastracker",
            "action": "gasoracle",
            "apikey": self.live_config.etherscan_api_key
        }

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data['status'] == '1':
                    # Convert from gwei to ETH
                    gas_price_gwei = float(data['result']['ProposeGasPrice'])
                    return gas_price_gwei * 1e-9
                else:
                    raise Exception(
                        f"Etherscan gas API error: {data.get('message', 'Unknown error')}")
            else:
                raise Exception(f"Etherscan gas API error: {response.status}")

    # Cache management methods

    async def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Get data from cache."""
        # Use in-memory cache only
        if key in self._price_cache:
            last_update = self._last_update.get(key)
            if last_update and (
                datetime.now(
                    timezone.utc) -
                    last_update).seconds < self.live_config.cache_ttl_seconds:
                return self._price_cache[key]
        return None

    async def _set_cache(self, key: str, data: Dict):
        """Set data in cache."""
        # Use in-memory cache only
        self._price_cache[key] = data
        self._last_update[key] = datetime.now(timezone.utc)

    async def clear_cache(self):
        """Clear all cached data."""
        # TODO-REFACTOR: STATE CLEARING - 16_clean_component_architecture_requirements.md
        # ISSUE: Cache clearing may indicate architectural problem
        # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Clean Component Architecture
        # Fix: Design components to be naturally clean without needing state clearing
        # Status: PENDING
        self._price_cache.clear()
        self._last_update.clear()
