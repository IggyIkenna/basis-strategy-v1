"""
Centralized Utility Manager

Provides centralized utility methods for all components to ensure consistent
data access and prevent duplication of utility methods across components.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
"""

from typing import Dict, Any, Optional
import logging
import pandas as pd
from datetime import datetime
from decimal import Decimal

from ..models.instruments import (
    instrument_key_to_price_key,
    instrument_key_to_oracle_pair,
    get_instrument_type_from_position_key,
    InstrumentType,
)

logger = logging.getLogger(__name__)


class UtilityManager:
    """Centralized utility methods for all components"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(UtilityManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, config: Dict[str, Any], data_provider):
        """
        Initialize utility manager.

        Args:
            config: Strategy configuration
            data_provider: Data provider instance
        """
        self.config = config
        self.data_provider = data_provider
        self.health_status = "healthy"
        self.error_count = 0

        logger.info("UtilityManager initialized")

    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.error_count += 1
        error_code = f"UTIL_ERROR_{self.error_count:04d}"

        logger.error(
            f"Utility Manager error {error_code}: {str(error)}",
            extra={
                "error_code": error_code,
                "context": context,
                "component": self.__class__.__name__,
            },
        )

        # Update health status based on error count
        if self.error_count > 10:
            self.health_status = "unhealthy"
        elif self.error_count > 5:
            self.health_status = "degraded"

    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            "status": self.health_status,
            "error_count": self.error_count,
            "component": self.__class__.__name__,
        }

    def get_instrument_type(self, instrument_key: str) -> str:
        """
        Get instrument type classification from position key.

        Maps position types to instrument classifications:
        - BaseToken, aToken, LST → 'asset'
        - debtToken → 'debt'
        - Perp → 'derivative'

        Args:
            instrument_key: Position key in format venue:position_type:symbol

        Returns:
            Instrument type: 'asset', 'debt', 'derivative', or 'unknown'
        """
        try:
            instrument_type = get_instrument_type_from_position_key(instrument_key)
            return instrument_type.value

        except Exception as e:
            logger.error(f"Error getting instrument type for {instrument_key}: {e}")
            return "unknown"

    def _validate_operation(self, operation: Any) -> bool:
        """Validate operation based on configuration."""
        # Basic validation logic
        if isinstance(operation, dict):
            required_fields = self.config.get("required_operation_fields", ["type"])
            return all(field in operation for field in required_fields)
        return True

    def get_liquidity_index(self, token: str, timestamp: pd.Timestamp) -> float:
        """Get AAVE liquidity index with uppercase key."""
        try:
            data = self.data_provider.get_data(timestamp)
            # Uppercase format: aUSDT, aWETH, debtWETH
            return data["protocol_data"]["aave_indexes"].get(token, 1.0)
        except Exception as e:
            logger.error(f"Error getting liquidity index for {token}: {e}")
            return 1.0

    def get_price_for_instrument_key(
        self, instrument_key: str, timestamp: pd.Timestamp, quote_currency: str = "USD"
    ) -> float:
        """
        Get price for any instrument with automatic currency conversion.
        This is the primary method for accessing market prices.

        Args:
            instrument_key: Instrument key in format venue:position_type:symbol
            timestamp: Timestamp for price lookup
            quote_currency: Desired quote currency ('USD', 'ETH', 'BTC')

        Returns:
            Price in specified quote currency
        """
        try:
            venue, position_type, instrument = instrument_key.split(":")
            data = self.data_provider.get_data(timestamp)

            if position_type == "BaseToken":
                # Direct uppercase lookup: BTC, ETH, USDT
                price = data["market_data"]["prices"].get(instrument, 1.0)

            elif position_type == "Perp":
                # Uppercase format: BTC_binance
                price_key = instrument_key_to_price_key(instrument_key)
                price = data["protocol_data"]["perp_prices"].get(price_key, 0.0)

            elif position_type == "aToken" or position_type == "debtToken":
                # Returns None to trigger liquidity index flow
                return None

            elif position_type == "LST":
                # For LST tokens, check if we need oracle or market pricing
                if venue in ["etherfi", "lido"]:
                    # Use oracle pricing for staking protocol venues
                    oracle_pair = instrument_key_to_oracle_pair(instrument_key, quote_currency)
                    price = data["protocol_data"]["oracle_prices"].get(oracle_pair, 0.0)
                else:
                    # Use market pricing for DEX/CEX venues
                    market_pair = f"{instrument}/{quote_currency}"
                    price = data["protocol_data"]["market_prices"].get(market_pair, 0.0)

            else:
                raise ValueError(f"Unknown position type: {position_type}")

            # Handle currency conversion if needed
            if quote_currency != "USD" and price and price > 0:
                if quote_currency == "ETH":
                    eth_price = data["market_data"]["prices"].get("ETH")
                    if eth_price and eth_price > 0:
                        price = price / eth_price
                elif quote_currency == "BTC":
                    btc_price = data["market_data"]["prices"].get("BTC")
                    if btc_price and btc_price > 0:
                        price = price / btc_price

            return float(price) if price else 0.0

        except Exception as e:
            logger.error(f"Error getting price for {instrument_key}: {e}")
            return 0.0

    def get_oracle_price(self, token: str, quote_currency: str, timestamp: pd.Timestamp) -> float:
        """
        Get AAVE oracle prices for LST tokens. Used for execution pricing (buy at oracle, sell at market).

        Args:
            token: LST token symbol (e.g., 'weETH', 'wstETH')
            quote_currency: Quote currency ('USD' or 'ETH')
            timestamp: Timestamp for oracle price lookup

        Returns:
            Oracle price in specified quote currency
        """
        try:
            data = self.data_provider.get_data(timestamp)
            oracle_pair = f"{token}/{quote_currency}"
            price = data["protocol_data"]["oracle_prices"].get(oracle_pair, 0.0)
            return float(price)
        except Exception as e:
            logger.error(f"Error getting oracle price for {token}/{quote_currency}: {e}")
            return 0.0

    def get_gas_cost(self, operation: str, timestamp: pd.Timestamp) -> float:
        """
        Get gas cost for operation using canonical pattern.

        Args:
            operation: Type of operation (e.g., 'standard', 'fast', 'slow')
            timestamp: Timestamp for gas cost data

        Returns:
            Gas cost in ETH
        """
        try:
            data = self.data_provider.get_data(timestamp)
            gas_costs = data.get("execution_data", {}).get("gas_costs", {})
            return gas_costs.get(operation, 0.0)
        except Exception as e:
            logger.error(f"Error getting gas cost for {operation}: {e}")
            return 0.0


    def _extract_base_asset(self, instrument: str) -> str:
        """Extract base asset from perpetual instrument ID."""
        # BTCUSDT → BTC
        # ETHUSDT → ETH
        return instrument.replace("USDT", "").replace("USD", "").replace("PERP", "")

    def convert_position_to_usd(
        self, instrument_key: str, amount: float, timestamp: pd.Timestamp
    ) -> float:
        """
        Convert position to USD using instrument_key convention.

        Args:
            instrument_key: Format "venue:position_type:instrument"
            amount: Position amount
            timestamp: Timestamp for conversion

        Returns:
            USD value
        """
        try:
            venue, position_type, instrument = instrument_key.split(":")

            # Handle special cases first
            if position_type in ["aToken", "debtToken"]:
                # Convert via liquidity index
                liquidity_index = self.get_liquidity_index(instrument, timestamp)

                # Handle division by zero
                if liquidity_index <= 0:
                    logger.warning(
                        f"Liquidity index for {instrument} is {liquidity_index}, using fallback conversion"
                    )
                    # Fallback: treat as underlying token directly
                    underlying_token = instrument[1:]  # aUSDT → USDT
                    underlying_price = self.get_price_for_instrument_key(
                        f"wallet:BaseToken:{underlying_token}", timestamp
                    )
                    return amount * underlying_price

                # In AAVE, aToken value = aToken amount × supply index
                # The supply index grows over time, increasing the value
                aToken_value = amount * liquidity_index
                underlying_token = instrument[1:]  # aUSDT → USDT
                underlying_price = self.get_price_for_instrument_key(
                    f"wallet:BaseToken:{underlying_token}", timestamp
                )
                return aToken_value * underlying_price

            # Get price using convention
            price = self.get_price_for_instrument_key(instrument_key, timestamp)

            # Handle missing price data
            if price is None or price <= 0:
                # Special handling for USDT - always assume $1.00
                if instrument == "USDT":
                    logger.debug(f"Using fallback USDT price of $1.00 for {instrument_key}")
                    return amount * 1.0
                else:
                    logger.warning(f"No valid price for {instrument_key}, returning 0.0")
                    return 0.0

            return amount * price

        except Exception as e:
            logger.error(f"Error converting position {instrument_key} to USD: {e}")
            return 0.0

    def convert_position_to_share_class(
        self, instrument_key: str, amount: float, share_class: str, timestamp: pd.Timestamp
    ) -> float:
        """Convert position to share class currency."""
        try:
            usd_value = self.convert_position_to_usd(instrument_key, amount, timestamp)

            if share_class == "USDT":
                return usd_value
            elif share_class == "ETH":
                eth_price = self.get_price_for_instrument_key("wallet:BaseToken:ETH", timestamp)
                return usd_value / eth_price if eth_price > 0 else 0.0
            else:
                raise ValueError(f"Unknown share class: {share_class}")

        except Exception as e:
            logger.error(f"Error converting position {instrument_key} to {share_class}: {e}")
            return 0.0

    def calculate_staking_rewards(
        self, instrument_key: str, amount: float, timestamp: pd.Timestamp
    ) -> Dict[str, float]:
        """
        Calculate staking rewards including seasonal distributions.

        Args:
            instrument_key: LST position key (e.g., "etherfi:LST:weETH")
            amount: LST position amount
            timestamp: Timestamp for calculation

        Returns:
            Dict with base_yield, seasonal_reward, total_yield
        """
        try:
            venue, position_type, instrument = instrument_key.split(":")

            if position_type != "LST":
                return {"base_yield": 0.0, "seasonal_reward": 0.0, "total_yield": 0.0}

            data = self.data_provider.get_data(timestamp)

            # Get base staking yield
            lst_key = instrument.lower()  # weETH → weeth
            base_apy = data["protocol_data"]["staking_rewards"].get(f"etherfi_{lst_key}_apy", 0.0)
            base_yield = amount * (base_apy / 365)  # Daily yield

            # Get seasonal rewards if enabled and applicable
            seasonal_reward = 0.0
            if instrument.upper() == "WEETH" and self.config.get("component_config", {}).get(
                "position_monitor", {}
            ).get("settlement", {}).get("seasonal_rewards_enabled", False):
                seasonal_data = data["protocol_data"]["seasonal_rewards"].get("ETHERFI_KING")
                if seasonal_data is not None and not seasonal_data.empty:
                    # Find matching period
                    period_data = seasonal_data[
                        (seasonal_data["PERIOD_START"] <= timestamp)
                        & (seasonal_data["PERIOD_END"] >= timestamp)
                    ]

                    if not period_data.empty:
                        # Calculate seasonal reward based on position size
                        weekly_reward_eth = period_data["weekly_reward_eth"].iloc[0]
                        daily_reward_eth = weekly_reward_eth / 7
                        seasonal_reward = daily_reward_eth * (
                            amount / 1.0
                        )  # Assume 1 ETH = 1 weETH for simplicity

            total_yield = base_yield + seasonal_reward

            return {
                "base_yield": base_yield,
                "seasonal_reward": seasonal_reward,
                "total_yield": total_yield,
            }

        except Exception as e:
            logger.error(f"Error calculating staking rewards for {instrument_key}: {e}")
            return {"base_yield": 0.0, "seasonal_reward": 0.0, "total_yield": 0.0}

    def convert_from_liquidity_index(
        self, amount: float, token: str, timestamp: pd.Timestamp
    ) -> float:
        """
        Convert from liquidity index (e.g., aUSDT to USDT).

        Args:
            amount: Amount of liquidity index token
            token: Liquidity index token symbol (e.g., 'aUSDT')
            timestamp: Timestamp for the conversion

        Returns:
            Underlying token amount
        """
        try:
            liquidity_index = self.get_liquidity_index(token, timestamp)
            return amount / liquidity_index
        except Exception as e:
            logger.error(f"Error converting from liquidity index {amount} {token}: {e}")
            return 0.0

    def get_share_class_from_mode(self, mode: str) -> str:
        """
        Get share class currency from mode configuration.

        Args:
            mode: Strategy mode name

        Returns:
            Share class currency ('USDT' or 'ETH')
        """
        try:
            # Get mode configuration
            mode_config = self.config.get("modes", {}).get(mode, {})
            share_class = mode_config.get("share_class", "USDT")

            # Validate share class
            if share_class not in ["USDT", "ETH"]:
                logger.warning(
                    f"Invalid share class {share_class} for mode {mode}, defaulting to USDT"
                )
                return "USDT"

            return share_class
        except Exception as e:
            logger.error(f"Error getting share class for mode {mode}: {e}")
            return "USDT"

    def get_asset_from_mode(self, mode: str) -> str:
        """
        Get asset from mode configuration.

        Args:
            mode: Strategy mode name

        Returns:
            Asset symbol (e.g., 'ETH', 'BTC', 'USDT')
        """
        try:
            # Get mode configuration
            mode_config = self.config.get("modes", {}).get(mode, {})
            asset = mode_config.get("asset", "ETH")

            return asset
        except Exception as e:
            logger.error(f"Error getting asset for mode {mode}: {e}")
            return "ETH"

    def get_lst_type_from_mode(self, mode: str) -> Optional[str]:
        """
        Get LST type from mode configuration.

        Args:
            mode: Strategy mode name

        Returns:
            LST type (e.g., 'lido', 'etherfi') or None
        """
        try:
            # Get mode configuration
            mode_config = self.config.get("modes", {}).get(mode, {})
            lst_type = mode_config.get("lst_type")

            return lst_type
        except Exception as e:
            logger.error(f"Error getting LST type for mode {mode}: {e}")
            return None

    def get_hedge_allocation_from_mode(self, mode: str) -> Optional[float]:
        """
        Get hedge allocation from mode configuration.

        Args:
            mode: Strategy mode name

        Returns:
            Hedge allocation ratio or None
        """
        try:
            # Get mode configuration - hedge_allocation is nested under component_config.strategy_manager.position_calculation
            mode_config = self.config.get("modes", {}).get(mode, {})
            hedge_allocation = (
                mode_config.get("component_config", {})
                .get("strategy_manager", {})
                .get("position_calculation", {})
                .get("HEDGE_ALLOCATION")
            )

            return hedge_allocation
        except Exception as e:
            logger.error(f"Error getting hedge allocation for mode {mode}: {e}")
            return None

    def calculate_total_usdt_balance(
        self, balances: Dict[str, float], timestamp: pd.Timestamp
    ) -> float:
        """
        Calculate total USDT equivalent balance from all token balances.

        Args:
            balances: Dictionary of token balances
            timestamp: Timestamp for price conversions

        Returns:
            Total USDT equivalent balance
        """
        try:
            total_usdt = 0.0

            for token, amount in balances.items():
                if amount > 0:
                    usdt_value = self.convert_to_usdt(amount, token, timestamp)
                    total_usdt += usdt_value

            return total_usdt
        except Exception as e:
            logger.error(f"Error calculating total USDT balance: {e}")
            return 0.0

    def calculate_total_share_class_balance(
        self, balances: Dict[str, float], share_class: str, timestamp: pd.Timestamp
    ) -> float:
        """
        Calculate total share class equivalent balance from all token balances.

        Args:
            balances: Dictionary of token balances
            share_class: Share class currency ('USDT' or 'ETH')
            timestamp: Timestamp for price conversions

        Returns:
            Total share class equivalent balance
        """
        try:
            total_share_class = 0.0

            for token, amount in balances.items():
                if amount > 0:
                    share_class_value = self.convert_to_share_class(
                        amount, token, share_class, timestamp
                    )
                    total_share_class += share_class_value

            return total_share_class
        except Exception as e:
            logger.error(f"Error calculating total {share_class} balance: {e}")
            return 0.0

    def get_venue_configs_from_mode(self, mode: str) -> Dict[str, Any]:
        """
        Get venue configurations from mode configuration.

        Args:
            mode: Strategy mode name

        Returns:
            Dictionary of venue configurations
        """
        try:
            # Get mode configuration
            mode_config = self.config.get("modes", {}).get(mode, {})
            venue_configs = mode_config.get("venue_configs", {})

            return venue_configs
        except Exception as e:
            logger.error(f"Error getting venue configs for mode {mode}: {e}")
            return {}

    def get_data_requirements_from_mode(self, mode: str) -> Dict[str, Any]:
        """
        Get data requirements from mode configuration.

        Args:
            mode: Strategy mode name

        Returns:
            Dictionary of data requirements
        """
        try:
            # Get mode configuration
            mode_config = self.config.get("modes", {}).get(mode, {})
            data_requirements = mode_config.get("data_requirements", {})

            return data_requirements
        except Exception as e:
            logger.error(f"Error getting data requirements for mode {mode}: {e}")
            return {}

    def is_token_liquidity_index(self, token: str) -> bool:
        """
        Check if a token is a liquidity index token (e.g., aUSDT, aETH).

        Args:
            token: Token symbol

        Returns:
            True if token is a liquidity index token
        """
        try:
            # Common liquidity index token patterns
            liquidity_index_patterns = ["a", "c", "v"]  # AAVE, Compound, Venus prefixes

            for pattern in liquidity_index_patterns:
                if token.startswith(pattern) and len(token) > 3:
                    return True

            return False
        except Exception as e:
            logger.error(f"Error checking if {token} is liquidity index: {e}")
            return False

    def get_underlying_token_from_liquidity_index(self, liquidity_index_token: str) -> str:
        """
        Get underlying token from liquidity index token.

        Args:
            liquidity_index_token: Liquidity index token symbol (e.g., 'aUSDT')

        Returns:
            Underlying token symbol (e.g., 'USDT')
        """
        try:
            # Remove common liquidity index prefixes
            prefixes_to_remove = ["a", "c", "v"]

            for prefix in prefixes_to_remove:
                if liquidity_index_token.startswith(prefix):
                    return liquidity_index_token[1:]  # Remove first character

            return liquidity_index_token
        except Exception as e:
            logger.error(f"Error getting underlying token from {liquidity_index_token}: {e}")
            return liquidity_index_token

    def calculate_total_positions(
        self, positions: Dict[str, float], timestamp: pd.Timestamp
    ) -> Dict[str, float]:
        """
        Calculate total positions from all position data.

        Args:
            positions: Dictionary of position data
            timestamp: Timestamp for calculations

        Returns:
            Dictionary of total positions
        """
        try:
            # For now, just return the positions as-is
            # In real implementation, this would aggregate positions by token
            return positions
        except Exception as e:
            logger.error(f"Error calculating total positions: {e}")
            return {}

    def calculate_total_exposures(
        self, positions: Dict[str, float], timestamp: pd.Timestamp
    ) -> Dict[str, float]:
        """
        Calculate total exposures from all position data.

        Args:
            positions: Dictionary of position data
            timestamp: Timestamp for calculations

        Returns:
            Dictionary of total exposures
        """
        try:
            # For now, just return the positions as exposures
            # In real implementation, this would calculate exposures differently
            return positions
        except Exception as e:
            logger.error(f"Error calculating total exposures: {e}")
            return {}

    # ========================================================================
    # POSITION MONITOR SUPPORT METHODS
    # ========================================================================

    def calculate_funding_payment(
        self, instrument_key: str, position_size: float, timestamp: pd.Timestamp
    ) -> float:
        """
        Calculate funding payment for perp position.

        Args:
            instrument_key: e.g., "binance:Perp:BTCUSDT"
            position_size: Position size in base units (negative = short)
            timestamp: Current timestamp

        Returns:
            Funding payment in USDT (positive = receive, negative = pay)
        """
        try:
            # Extract venue and symbol
            parts = instrument_key.split(":")
            if len(parts) < 3:
                logger.error(f"Invalid instrument_key format: {instrument_key}")
                return 0.0

            venue = parts[0]
            symbol = parts[2]

            # Get funding rate from data provider
            funding_rate = self._get_funding_rate(venue, symbol, timestamp)

            # Get mark price from data provider
            mark_price = self._get_mark_price(venue, symbol, timestamp)

            # Calculate position notional
            position_notional = abs(position_size) * mark_price

            # Calculate funding payment
            # Short position: receive if rate > 0, pay if rate < 0
            # Long position: pay if rate > 0, receive if rate < 0
            if position_size < 0:  # Short
                funding_payment = position_notional * funding_rate
            else:  # Long
                funding_payment = -position_notional * funding_rate

            return funding_payment

        except Exception as e:
            logger.error(f"Error calculating funding payment for {instrument_key}: {e}")
            return 0.0

    def calculate_staking_rewards(
        self, instrument_key: str, position_size: float, timestamp: pd.Timestamp
    ) -> float:
        """
        Calculate daily staking rewards for LST position.

        Args:
            instrument_key: e.g., "lido:BaseToken:stETH"
            position_size: Position size in token units
            timestamp: Current timestamp

        Returns:
            Daily rewards in same token units
        """
        try:
            # Extract protocol and token
            parts = instrument_key.split(":")
            if len(parts) < 3:
                logger.error(f"Invalid instrument_key format: {instrument_key}")
                return 0.0

            protocol = parts[0]
            token = parts[2]

            # Get APR from config or data provider
            annual_apr = self._get_staking_apr(protocol, token, timestamp)

            # Calculate daily rewards (APR / 365)
            daily_rate = annual_apr / 365.0
            daily_rewards = position_size * daily_rate

            return daily_rewards

        except Exception as e:
            logger.error(f"Error calculating staking rewards for {instrument_key}: {e}")
            return 0.0

    def convert_atoken_to_base(
        self, atoken_amount: float, token: str, timestamp: pd.Timestamp
    ) -> float:
        """
        Convert aToken amount to base token amount using supply index.

        Example: aWETH -> WETH

        Args:
            atoken_amount: Amount of aToken
            token: Base token symbol (e.g., "WETH")
            timestamp: Timestamp for index lookup

        Returns:
            Base token amount
        """
        try:
            supply_index = self._get_aave_supply_index(token, timestamp)
            return atoken_amount / supply_index
        except Exception as e:
            logger.error(f"Error converting aToken to base for {token}: {e}")
            return atoken_amount  # Fallback to 1:1

    def convert_debt_to_base(
        self, debt_amount: float, token: str, timestamp: pd.Timestamp
    ) -> float:
        """
        Convert debtToken amount to base token amount using borrow index.

        Example: debtUSDT -> USDT

        Args:
            debt_amount: Amount of debtToken
            token: Base token symbol (e.g., "USDT")
            timestamp: Timestamp for index lookup

        Returns:
            Base token amount
        """
        try:
            borrow_index = self._get_aave_borrow_index(token, timestamp)
            return debt_amount / borrow_index
        except Exception as e:
            logger.error(f"Error converting debt to base for {token}: {e}")
            return debt_amount  # Fallback to 1:1

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _get_funding_rate(self, venue: str, symbol: str, timestamp: pd.Timestamp) -> float:
        """Get funding rate with uppercase key."""
        try:
            data = self.data_provider.get_data(timestamp)
            funding_rates = data.get("market_data", {}).get("funding_rates", {})

            # Uppercase format: BTC_binance
            base = symbol.replace("USDT", "").replace("USD", "").replace("PERP", "")
            venue_key = f"{base}_{venue}"
            return funding_rates.get(venue_key, 0.0)
        except Exception as e:
            logger.error(f"Error getting funding rate for {venue}:{symbol}: {e}")
            return 0.0

    def _get_mark_price(self, venue: str, symbol: str, timestamp: pd.Timestamp) -> float:
        """Get mark price with uppercase key."""
        try:
            data = self.data_provider.get_data(timestamp)
            perp_prices = data.get("protocol_data", {}).get("perp_prices", {})

            # Uppercase format: BTC_binance
            base = symbol.replace("USDT", "").replace("USD", "").replace("PERP", "")
            venue_key = f"{base}_{venue}"
            return perp_prices.get(venue_key, 0.0)
        except Exception as e:
            logger.error(f"Error getting mark price for {venue}:{symbol}: {e}")
            return 0.0

    def _get_staking_apr(self, venue: str, token: str, timestamp: pd.Timestamp) -> float:
        """Get staking APR with uppercase key."""
        try:
            data = self.data_provider.get_data(timestamp)
            staking_rewards = data.get("protocol_data", {}).get("staking_rewards", {})

            # Uppercase format: etherfi_weETH, lido_wstETH
            protocol_key = f"{venue}_{token}"
            if protocol_key in staking_rewards:
                return staking_rewards[protocol_key]

            # Fallback to defaults
            default_aprs = {"etherfi": 0.04, "lido": 0.035}
            return default_aprs.get(venue, 0.03)
        except Exception as e:
            logger.error(f"Error getting staking APR for {venue}:{token}: {e}")
            return 0.03

    def _get_aave_supply_index(self, token: str, timestamp: pd.Timestamp) -> float:
        """Get Aave supply index for token."""
        try:
            # Try to get from data provider
            if self.data_provider:
                data = self.data_provider.get_data(timestamp)
                indices = data.get("market_data", {}).get("indices", {}).get("aave_supply", {})

                if token in indices:
                    return indices[token]

            # Fallback to 1.0 (1:1 conversion)
            return 1.0

        except Exception as e:
            logger.error(f"Error getting Aave supply index for {token}: {e}")
            return 1.0

    def _get_aave_borrow_index(self, token: str, timestamp: pd.Timestamp) -> float:
        """Get Aave borrow index for token."""
        try:
            # Try to get from data provider
            if self.data_provider:
                data = self.data_provider.get_data(timestamp)
                indices = data.get("market_data", {}).get("indices", {}).get("aave_borrow", {})

                if token in indices:
                    return indices[token]

            # Fallback to 1.0 (1:1 conversion)
            return 1.0

        except Exception as e:
            logger.error(f"Error getting Aave borrow index for {token}: {e}")
            return 1.0

    # ========================================================================
    # ADDITIONAL UTILITY METHODS FOR COMPLIANCE
    # ========================================================================

    def convert_to_usdt(self, amount: float, token: str, timestamp: pd.Timestamp) -> float:
        """
        Convert token amount to USDT equivalent.

        Args:
            amount: Token amount
            token: Token symbol
            timestamp: Timestamp for conversion

        Returns:
            USDT equivalent amount
        """
        try:
            if token == "USDT":
                return amount

            price = self.get_market_price(token, timestamp)
            return amount * price

        except Exception as e:
            logger.error(f"Error converting {amount} {token} to USDT: {e}")
            return 0.0

    def convert_to_share_class(
        self, amount: float, token: str, share_class: str, timestamp: pd.Timestamp
    ) -> float:
        """
        Convert token amount to share class currency.

        Args:
            amount: Token amount
            token: Token symbol
            share_class: Share class currency ('USDT' or 'ETH')
            timestamp: Timestamp for conversion

        Returns:
            Share class equivalent amount
        """
        try:
            if share_class == "USDT":
                return self.convert_to_usdt(amount, token, timestamp)
            elif share_class == "ETH":
                usdt_value = self.convert_to_usdt(amount, token, timestamp)
                eth_price = self.get_market_price("ETH", timestamp)
                return usdt_value / eth_price if eth_price > 0 else 0.0
            else:
                logger.error(f"Unknown share class: {share_class}")
                return 0.0

        except Exception as e:
            logger.error(f"Error converting {amount} {token} to {share_class}: {e}")
            return 0.0

    def calculate_dynamic_ltv_target(
        self, max_ltv: Decimal, max_stake_spread_move: Decimal
    ) -> Decimal:
        """
        Calculate dynamic LTV target with safety buffers.

        Args:
            max_ltv: Maximum LTV from AAVE risk parameters
            max_stake_spread_move: Maximum expected stake spread move

        Returns:
            Dynamic LTV target with safety buffers applied
        """
        try:
            # Calculate dynamic LTV target: max_ltv * (1 - max_stake_spread_move)
            dynamic_ltv = max_ltv * (Decimal("1") - max_stake_spread_move)

            # Ensure it's not negative (minimum 0% LTV)
            dynamic_ltv = max(dynamic_ltv, Decimal("0"))

            logger.debug(
                f"Calculated dynamic LTV target: {dynamic_ltv} (max_ltv: {max_ltv}, spread_move: {max_stake_spread_move})"
            )
            return dynamic_ltv

        except Exception as e:
            logger.error(f"Error calculating dynamic LTV target: {e}")
            return Decimal("0")

    def calculate_cex_target_margin(
        self, initial_margin: Decimal, max_underlying_move: Decimal
    ) -> Decimal:
        """
        Calculate CEX target maintenance margin with safety buffers.

        Args:
            initial_margin: Initial margin requirement from CEX
            max_underlying_move: Maximum expected underlying move

        Returns:
            Target maintenance margin with safety buffers applied
        """
        try:
            # Calculate target margin: initial_margin * (1 + max_underlying_move)
            target_margin = initial_margin * (Decimal("1") + max_underlying_move)

            # Ensure it's not above 100% (maximum 100% margin)
            target_margin = min(target_margin, Decimal("1"))

            logger.debug(
                f"Calculated CEX target margin: {target_margin} (initial: {initial_margin}, move: {max_underlying_move})"
            )
            return target_margin

        except Exception as e:
            logger.error(f"Error calculating CEX target margin: {e}")
            return initial_margin
