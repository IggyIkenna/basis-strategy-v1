"""
Live CeFi Data Provider

Provides real-time data for CeFi/ML strategies in live mode.
Uses API clients with credential-based switching and ML service integration.

Key Principles:
- Real-time data from live APIs
- Credential-based venue switching (env vars)
- ML service integration for predictions
- Same interface as historical providers
- Standardized data structure
- Graceful degradation when APIs unavailable
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
import pandas as pd
import os

from ...core.models.instruments import instrument_key_to_price_key, instrument_key_to_oracle_pair

logger = logging.getLogger(__name__)


class LiveCeFiDataProvider:
    """Handles CeFi/ML strategies in live mode with real-time APIs + ML service."""

    def __init__(self, config: Dict[str, Any], ml_service):
        """
        Initialize live CeFi data provider.

        Args:
            config: Configuration dictionary with position_subscriptions
            ml_service: ML service instance for predictions
        """
        self.execution_mode = "live"
        self.data_type = "cefi"
        self.config = config
        self.position_subscriptions = config["component_config"]["position_monitor"][
            "position_subscriptions"
        ]
        self.ml_service = ml_service

        # Initialize API clients
        self.binance_client = self._init_binance()
        self.bybit_client = self._init_bybit()
        self.okx_client = self._init_okx()

        logger.info(
            f"LiveCeFiDataProvider initialized for {len(self.position_subscriptions)} positions"
        )

    def _init_binance(self) -> Optional[Dict]:
        """Initialize Binance client."""
        environment = os.getenv("BASIS_ENVIRONMENT", "dev")
        api_key = os.getenv(f"BASIS_{environment.upper()}__CEX__BINANCE_API_KEY")
        api_secret = os.getenv(f"BASIS_{environment.upper()}__CEX__BINANCE_API_SECRET")

        if api_key and api_secret:
            return {
                "api_key": api_key,
                "api_secret": api_secret,
                "base_url": "https://api.binance.com",
            }
        else:
            logger.warning("Binance API credentials not found")
            return None

    def _init_bybit(self) -> Optional[Dict]:
        """Initialize Bybit client."""
        api_key = os.getenv("BYBIT_API_KEY")
        api_secret = os.getenv("BYBIT_API_SECRET")

        if api_key and api_secret:
            return {
                "api_key": api_key,
                "api_secret": api_secret,
                "base_url": "https://api.bybit.com",
            }
        else:
            logger.warning("Bybit API credentials not found")
            return None

    def _init_okx(self) -> Optional[Dict]:
        """Initialize OKX client."""
        environment = os.getenv("BASIS_ENVIRONMENT", "dev")
        api_key = os.getenv(f"BASIS_{environment.upper()}__CEX__OKX_API_KEY")
        api_secret = os.getenv("OKX_API_SECRET")
        passphrase = os.getenv("OKX_PASSPHRASE")

        if api_key and api_secret and passphrase:
            return {
                "api_key": api_key,
                "api_secret": api_secret,
                "passphrase": passphrase,
                "base_url": "https://www.okx.com",
            }
        else:
            logger.warning("OKX API credentials not found")
            return None

    async def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Load live data with uppercase keys and ML predictions."""
        data = {
            "timestamp": timestamp,
            "market_data": {"prices": {}, "funding_rates": {}},
            "protocol_data": {
                "perp_prices": {},
                "aave_indexes": {},
                "oracle_prices": {},
                "market_prices": {},
                "staking_rewards": {},
            },
            "execution_data": {"gas_costs": {}, "execution_costs": {}},
            "ml_data": {"predictions": {}},
        }

        # Load prices with uppercase keys
        for instrument_key in self.position_subscriptions:
            venue, position_type, instrument = instrument_key.split(":")

            if position_type == "BaseToken":
                price = await self._fetch_spot_price(instrument, venue)
                data["market_data"]["prices"][instrument] = price  # BTC, ETH

            elif position_type == "Perp":
                price_key = instrument_key_to_price_key(instrument_key)
                perp_price = await self._fetch_perp_price(instrument, venue)
                data["protocol_data"]["perp_prices"][price_key] = perp_price  # BTC_binance

                funding_rate = await self._fetch_funding_rate(instrument, venue)
                data["market_data"]["funding_rates"][price_key] = funding_rate  # BTC_binance

        # Add real-time ML predictions
        try:
            ml_predictions = await self.ml_service.get_live_predictions(timestamp)
            data["ml_data"]["predictions"] = ml_predictions
        except Exception as e:
            logger.warning(f"Error getting live ML predictions: {e}")
            data["ml_data"]["predictions"] = {}

        return data

    async def _fetch_spot_price(self, instrument: str, venue: str) -> float:
        """Fetch spot price from venue API."""
        if venue == "binance" and self.binance_client:
            return await self._fetch_binance_spot_price(instrument)
        elif venue == "bybit" and self.bybit_client:
            return await self._fetch_bybit_spot_price(instrument)
        elif venue == "okx" and self.okx_client:
            return await self._fetch_okx_spot_price(instrument)
        else:
            raise ValueError(f"No API client available for venue: {venue}")

    async def _fetch_perp_price(self, base: str, venue: str) -> float:
        """Fetch perpetual price from venue API."""
        if venue == "binance" and self.binance_client:
            return await self._fetch_binance_perp_price(base)
        elif venue == "bybit" and self.bybit_client:
            return await self._fetch_bybit_perp_price(base)
        elif venue == "okx" and self.okx_client:
            return await self._fetch_okx_perp_price(base)
        else:
            raise ValueError(f"No API client available for venue: {venue}")

    async def _fetch_funding_rate(self, base: str, venue: str) -> float:
        """Fetch funding rate from venue API."""
        if venue == "binance" and self.binance_client:
            return await self._fetch_binance_funding_rate(base)
        elif venue == "bybit" and self.bybit_client:
            return await self._fetch_bybit_funding_rate(base)
        elif venue == "okx" and self.okx_client:
            return await self._fetch_okx_funding_rate(base)
        else:
            raise ValueError(f"No API client available for venue: {venue}")

    async def _fetch_gas_cost(self) -> float:
        """Fetch current gas cost."""
        # Implementation would call gas API
        # For now, return default value
        return 0.0

    def _extract_base_asset(self, instrument: str) -> str:
        """Extract base asset from perpetual instrument ID."""
        return instrument.replace("USDT", "").replace("USD", "").replace("PERP", "")

    # Placeholder API methods - would be implemented with actual API calls
    async def _fetch_binance_spot_price(self, instrument: str) -> float:
        """Fetch spot price from Binance API."""
        # Implementation would use binance client
        return 0.0

    async def _fetch_bybit_spot_price(self, instrument: str) -> float:
        """Fetch spot price from Bybit API."""
        return 0.0

    async def _fetch_okx_spot_price(self, instrument: str) -> float:
        """Fetch spot price from OKX API."""
        return 0.0

    async def _fetch_binance_perp_price(self, base: str) -> float:
        """Fetch perpetual price from Binance API."""
        return 0.0

    async def _fetch_bybit_perp_price(self, base: str) -> float:
        """Fetch perpetual price from Bybit API."""
        return 0.0

    async def _fetch_okx_perp_price(self, base: str) -> float:
        """Fetch perpetual price from OKX API."""
        return 0.0

    async def _fetch_binance_funding_rate(self, base: str) -> float:
        """Fetch funding rate from Binance API."""
        return 0.0

    async def _fetch_bybit_funding_rate(self, base: str) -> float:
        """Fetch funding rate from Bybit API."""
        return 0.0

    async def _fetch_okx_funding_rate(self, base: str) -> float:
        """Fetch funding rate from OKX API."""
        return 0.0
