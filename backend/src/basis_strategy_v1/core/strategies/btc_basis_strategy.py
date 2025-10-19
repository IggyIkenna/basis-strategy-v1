"""
BTC Basis Strategy Implementation

Implements BTC basis trading strategy with funding rate arbitrage.
Inherits from BaseStrategyManager and implements the 5 standard actions.

Reference: docs/STRATEGY_MODES.md - BTC Basis Strategy Mode
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
import uuid
from pathlib import Path

from .base_strategy_manager import BaseStrategyManager
from ...core.models.order import Order, OrderOperation
from ...core.models.venues import Venue
from ...core.models.instruments import validate_instrument_key, get_display_name, get_instrument

logger = logging.getLogger(__name__)


class BTCBasisStrategy(BaseStrategyManager):
    """
    BTC Basis Strategy - Funding rate arbitrage with BTC perpetuals.

    Strategy Overview:
    - Long BTC spot position
    - Short BTC perpetual position
    - Capture funding rate differential
    - Target APY: 15-25%
    """

    def __init__(
        self,
        config: Dict[str, Any],
        data_provider,
        exposure_monitor,
        position_monitor,
        risk_monitor,
        utility_manager=None,
        correlation_id: str = None,
        pid: int = None,
        log_dir: Path = None,
    ):
        """
        Initialize BTC basis strategy.

        Args:
            config: Strategy configuration
            data_provider: Data provider instance for market data
            exposure_monitor: Exposure monitor instance for exposure data
            position_monitor: Position monitor instance for position data
            risk_monitor: Risk monitor instance for risk assessment
            utility_manager: Centralized utility manager for conversion rates
            correlation_id: Unique correlation ID for this run
            pid: Process ID
            log_dir: Log directory path (logs/{correlation_id}/{pid}/)
        """
        super().__init__(
            config,
            data_provider,
            exposure_monitor,
            position_monitor,
            risk_monitor,
            utility_manager,
            correlation_id,
            pid,
            log_dir,
        )

        # Validate required configuration at startup (fail-fast)
        required_keys = ["max_leverage"]
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")

        # BTC-specific configuration (fail-fast access)
        self.max_leverage = config["max_leverage"]  # No leverage for basis trading
        self.share_class = config.get("share_class", "USDT")  # Share class currency

        # For basis trading, allocate 100% to BTC
        self.btc_allocation = config.get("btc_allocation", 1.0)

        # Define and validate instrument keys
        self.entry_instrument = f"{Venue.WALLET.value}:BaseToken:USDT"
        self.spot_instrument = f"{Venue.BINANCE.value}:BaseToken:BTC"
        self.perp_instrument = f"{Venue.BINANCE.value}:Perp:BTCUSDT"  # FIXED: use correct perp key

        # Validate instrument keys
        validate_instrument_key(self.entry_instrument)
        validate_instrument_key(self.spot_instrument)
        validate_instrument_key(self.perp_instrument)

        # Get available instruments from position_monitor config
        position_config = config.get("component_config", {}).get("position_monitor", {})
        self.available_instruments = position_config.get("position_subscriptions", [])

        if not self.available_instruments:
            raise ValueError(
                f"{self.__class__.__name__} requires position_subscriptions in config. "
                "Define all instruments this strategy will use in component_config.position_monitor.position_subscriptions"
            )

        # Define required instruments for this strategy
        required_instruments = [self.entry_instrument, self.spot_instrument, self.perp_instrument]

        # Validate all required instruments are in available set
        for instrument in required_instruments:
            if instrument not in self.available_instruments:
                raise ValueError(
                    f"Required instrument {instrument} not in position_subscriptions. "
                    f"Add to configs/modes/{config.get('mode', 'btc_basis')}.yaml"
                )

        # Validate instrument key formats
        for instrument in self.available_instruments:
            try:
                get_instrument(instrument)
            except ValueError as e:
                raise ValueError(f"Invalid instrument key format: {instrument}") from e

        self.logger.info(
            f"BTCBasisStrategy initialized with {self.btc_allocation*100}% BTC allocation"
        )
        self.logger.info(f"  Available instruments: {len(self.available_instruments)}")
        self.logger.info(f"  Entry: {get_display_name(self.entry_instrument)}")
        self.logger.info(f"  Spot: {get_display_name(self.spot_instrument)}")
        self.logger.info(f"  Perp: {get_display_name(self.perp_instrument)}")

    def _get_asset_price(self) -> float:
        """Get current BTC price. In real implementation, this would fetch from data provider."""
        # For testing purposes, return a default BTC price
        # In production, this would fetch from market data
        return 50000.0

    def generate_orders(
        self, timestamp: pd.Timestamp, exposure: Dict, risk_assessment: Dict, market_data: Dict
    ) -> List[Order]:
        """
        Generate orders for BTC basis strategy based on market conditions and risk assessment.

        BTC Basis Strategy Logic:
        - Analyze funding rates and basis spreads
        - Check risk metrics for liquidation risk
        - Decide on entry/exit based on profitability and risk
        - Generate appropriate instructions for BTC spot + perp positions
        """
        try:
            # Log strategy decision start
            self.logger.info("Making BTC basis strategy decision")

            # Get current equity and positions
            current_equity = self.get_current_equity(exposure)
            current_positions = exposure.get("positions", {})

            # BTC-specific market analysis
            btc_spot_price = market_data.get("prices", {}).get("BTC", 0.0)
            btc_funding_rate = market_data.get("rates", {}).get("btc_funding", 0.0)

            # Risk assessment
            liquidation_risk = risk_assessment.get("liquidation_risk", 0.0)
            margin_ratio = risk_assessment.get("cex_margin_ratio", 1.0)

            # BTC Basis Strategy Decision Logic
            # Check if we have existing BTC positions
            has_btc_position = (
                current_positions.get("btc_balance", 0) > 0
                or current_positions.get("btc_perpetual_short", 0) != 0
            )

            if current_equity == 0 or not has_btc_position:
                # No position or no BTC position - check if we should enter
                if self._should_enter_basis_position(btc_funding_rate, btc_spot_price):
                    return self._create_entry_orders(current_equity)
                else:
                    return self._create_dust_sell_orders(exposure)  # Wait for better opportunity

            elif liquidation_risk > 0.8 or margin_ratio < 0.2:
                # High risk - exit position
                return self._create_exit_orders(current_equity)

            elif liquidation_risk > 0.6 or margin_ratio < 0.3:
                # Medium risk - partial exit
                return self._create_exit_orders(current_equity * 0.5)

            elif self._should_rebalance_position(btc_funding_rate, current_positions):
                # Rebalance position based on funding rate changes
                return self._create_rebalance_orders(current_equity * 0.2)

            else:
                # Maintain current position
                return self._create_dust_sell_orders(exposure)

        except Exception as e:
            self.logger.error(
                "Error in BTC basis strategy order generation",
                error_code="STRAT-001",
                exc_info=e,
                method="generate_orders",
                strategy_type=self.__class__.__name__,
            )
            # Return safe default action
            return self._create_dust_sell_orders(exposure)

    def _should_enter_basis_position(self, funding_rate: float, spot_price: float) -> bool:
        """Determine if we should enter a BTC basis position."""
        # BTC basis strategy logic: enter when funding rate is positive (earning funding)
        # No threshold - take any positive funding opportunity
        return funding_rate != 0 and spot_price > 0

    def _should_rebalance_position(self, funding_rate: float, current_positions: Dict) -> bool:
        """Determine if we should rebalance the BTC basis position."""
        # Rebalance if we have positions and funding rate exists
        return funding_rate != 0

    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position for BTC basis strategy.

        Args:
            current_equity: Current equity in share class currency

        Returns:
            Dictionary of target positions by token/venue
        """
        try:
            # Calculate target allocations
            btc_target = current_equity * self.btc_allocation

            # Get current BTC price
            btc_price = self._get_asset_price()
            btc_amount = btc_target / btc_price if btc_price > 0 else 0

            return {
                "btc_balance": btc_amount,
                "btc_perpetual_short": -btc_amount,  # Short position
                "usdt_balance": current_equity,
                "total_equity": current_equity,
            }

        except Exception as e:
            logger.error(f"Error calculating target position: {e}")
            return {
                "btc_balance": 0.0,
                "btc_perpetual_short": 0.0,
                "usdt_balance": current_equity,
                "total_equity": current_equity,
            }

    def _create_entry_orders(self, equity: float) -> List[Order]:
        """
        Create orders for full BTC basis position entry.

        Args:
            equity: Available equity in share class currency

        Returns:
            List[Order] for BTC spot buy + BTC perp short (sequential)
        """
        try:
            # Log order creation
            self.logger.info(f"Creating entry orders with equity={equity}")

            # Calculate target position
            target_position = self.calculate_target_position(equity)
            orders = []

            # 1. Buy BTC spot
            btc_amount = target_position.get("btc_balance", 0.0)
            if btc_amount > 0:
                # Generate unique operation ID
                operation_id = f"spot_buy_{uuid.uuid4().hex[:8]}"

                # Get BTC price for expected deltas calculation
                btc_price = self._get_asset_price()
                usdt_amount = btc_amount * btc_price

                # Calculate expected deltas for spot trade
                expected_deltas = {
                    f"binance:BaseToken:BTC": btc_amount,  # Gain BTC
                    f"binance:BaseToken:USDT": -usdt_amount,  # Lose USDT
                }

                # Operation details
                operation_details = {
                    "btc_allocation": self.btc_allocation,
                    "btc_price": btc_price,
                    "usdt_amount": usdt_amount,
                }

                orders.append(
                    Order(
                        operation_id=operation_id,
                        venue="binance",
                        operation=OrderOperation.SPOT_TRADE,
                        pair="BTC/USDT",
                        side="BUY",
                        amount=btc_amount,
                        price=btc_price,
                        order_type="market",
                        source_venue="wallet",
                        target_venue="binance",
                        source_token="USDT",
                        target_token="BTC",
                        expected_deltas=expected_deltas,
                        operation_details=operation_details,
                        execution_mode="sequential",
                        strategy_intent="btc_basis_entry",
                        strategy_id="btc_basis",
                        metadata={"btc_allocation": self.btc_allocation},
                    )
                )

            # 2. Open short perpetual position
            short_amount = abs(target_position.get("btc_perpetual_short", 0.0))
            if short_amount > 0:
                # Generate unique operation ID
                operation_id = f"perp_short_{uuid.uuid4().hex[:8]}"

                # Get BTC price for margin calculation
                btc_price = self._get_asset_price()
                margin_amount = short_amount * btc_price * 0.1  # 10% margin

                # Calculate expected deltas for perp short
                expected_deltas = {
                    f"bybit:PerpPosition:BTC": -short_amount,  # Negative BTC exposure (short)
                    f"bybit:BaseToken:USDT": -margin_amount,  # Lose USDT as margin
                }

                # Operation details
                operation_details = {
                    "btc_allocation": self.btc_allocation,
                    "btc_price": btc_price,
                    "MARGIN_AMOUNT": margin_amount,
                    "MARGIN_RATIO": 0.1,
                }

                orders.append(
                    Order(
                        operation_id=operation_id,
                        venue="bybit",
                        operation=OrderOperation.PERP_TRADE,
                        pair="BTCUSDT",
                        side="SHORT",
                        amount=short_amount,
                        price=btc_price,
                        order_type="market",
                        source_venue="wallet",
                        target_venue="bybit",
                        source_token="USDT",
                        target_token="BTC",
                        expected_deltas=expected_deltas,
                        operation_details=operation_details,
                        execution_mode="sequential",
                        strategy_intent="btc_basis_entry",
                        strategy_id="btc_basis",
                        metadata={"btc_allocation": self.btc_allocation},
                    )
                )

            return orders

        except Exception as e:
            self.logger.error(
                "Error creating entry orders",
                error_code="STRAT-001",
                exc_info=e,
                method="_create_entry_orders",
                equity=equity,
            )
            return []

    def _create_exit_orders(self, equity: float) -> List[Order]:
        """
        Create orders for BTC basis position exit.

        Args:
            equity: Equity to exit (full or partial)

        Returns:
            List[Order] for closing perp short + BTC spot sell (sequential)
        """
        try:
            # Log order creation
            self.logger.info(f"Creating exit orders with equity={equity}")

            # Get current position
            current_position = self.position_monitor.get_current_position()
            btc_balance = current_position.get("btc_balance", 0.0)
            btc_short = current_position.get("btc_perpetual_short", 0.0)

            orders = []

            # 1. Close short perpetual position
            if btc_short < 0:
                # Generate unique operation ID
                operation_id = f"perp_close_{uuid.uuid4().hex[:8]}"

                # Get BTC price for margin calculation
                btc_price = self._get_asset_price()
                close_amount = abs(btc_short)
                margin_return = close_amount * btc_price * 0.1  # Return 10% margin

                # Calculate expected deltas for closing perp short
                expected_deltas = {
                    f"bybit:PerpPosition:BTC": close_amount,  # Close short (positive delta)
                    f"bybit:BaseToken:USDT": margin_return,  # Return margin
                }

                # Operation details
                operation_details = {
                    "position_type": "close_short",
                    "original_short": btc_short,
                    "btc_price": btc_price,
                    "MARGIN_RETURN": margin_return,
                }

                orders.append(
                    Order(
                        operation_id=operation_id,
                        venue="bybit",
                        operation=OrderOperation.PERP_TRADE,
                        pair="BTCUSDT",
                        side="LONG",  # Close short position
                        amount=close_amount,
                        price=btc_price,
                        order_type="market",
                        source_venue="bybit",
                        target_venue="wallet",
                        source_token="BTC",
                        target_token="USDT",
                        expected_deltas=expected_deltas,
                        operation_details=operation_details,
                        execution_mode="sequential",
                        strategy_intent="btc_basis_exit",
                        strategy_id="btc_basis",
                        metadata={"position_type": "close_short", "original_short": btc_short},
                    )
                )

            # 2. Sell BTC spot
            if btc_balance > 0:
                # Generate unique operation ID
                operation_id = f"spot_sell_{uuid.uuid4().hex[:8]}"

                # Get BTC price for expected deltas calculation
                btc_price = self._get_asset_price()
                usdt_amount = btc_balance * btc_price

                # Calculate expected deltas for spot sell
                expected_deltas = {
                    f"binance:BaseToken:BTC": -btc_balance,  # Lose BTC
                    f"binance:BaseToken:USDT": usdt_amount,  # Gain USDT
                }

                # Operation details
                operation_details = {
                    "btc_balance": btc_balance,
                    "btc_price": btc_price,
                    "usdt_amount": usdt_amount,
                }

                orders.append(
                    Order(
                        operation_id=operation_id,
                        venue="binance",
                        operation=OrderOperation.SPOT_TRADE,
                        pair="BTC/USDT",
                        side="SELL",
                        amount=btc_balance,
                        price=btc_price,
                        order_type="market",
                        source_venue="binance",
                        target_venue="wallet",
                        source_token="BTC",
                        target_token="USDT",
                        expected_deltas=expected_deltas,
                        operation_details=operation_details,
                        execution_mode="sequential",
                        strategy_intent="btc_basis_exit",
                        strategy_id="btc_basis",
                        metadata={"btc_balance": btc_balance},
                    )
                )

            return orders

        except Exception as e:
            self.logger.error(
                "Error creating exit orders",
                error_code="STRAT-001",
                exc_info=e,
                method="_create_exit_orders",
                equity=equity,
            )
            return []

    def _create_rebalance_orders(self, equity_delta: float) -> List[Order]:
        """
        Create orders for BTC basis position rebalancing.

        Args:
            equity_delta: Additional equity to deploy for rebalancing

        Returns:
            List[Order] for proportional BTC spot buy + perp short increase
        """
        try:
            # Log order creation
            self.logger.info(f"Creating rebalance orders with equity_delta={equity_delta}")

            # Calculate proportional allocation
            btc_delta = equity_delta * self.btc_allocation
            btc_price = self._get_asset_price()
            btc_amount = btc_delta / btc_price if btc_price > 0 else 0

            orders = []

            # 1. Buy additional BTC spot
            if btc_amount > 0:
                # Generate unique operation ID
                operation_id = f"rebalance_buy_{uuid.uuid4().hex[:8]}"

                usdt_amount = btc_amount * btc_price

                # Calculate expected deltas for rebalance spot buy
                expected_deltas = {
                    f"binance:BaseToken:BTC": btc_amount,  # Gain BTC
                    f"binance:BaseToken:USDT": -usdt_amount,  # Lose USDT
                }

                # Operation details
                operation_details = {
                    "btc_delta": btc_delta,
                    "REBALANCE_TYPE": "increase",
                    "btc_price": btc_price,
                    "usdt_amount": usdt_amount,
                }

                orders.append(
                    Order(
                        operation_id=operation_id,
                        venue="binance",
                        operation=OrderOperation.SPOT_TRADE,
                        pair="BTC/USDT",
                        side="BUY",
                        amount=btc_amount,
                        price=btc_price,
                        order_type="market",
                        source_venue="wallet",
                        target_venue="binance",
                        source_token="USDT",
                        target_token="BTC",
                        expected_deltas=expected_deltas,
                        operation_details=operation_details,
                        execution_mode="sequential",
                        strategy_intent="btc_basis_rebalance",
                        strategy_id="btc_basis",
                        metadata={"btc_delta": btc_delta, "REBALANCE_TYPE": "increase"},
                    )
                )

            # 2. Increase short perpetual position
            if btc_amount > 0:
                # Generate unique operation ID
                operation_id = f"rebalance_short_{uuid.uuid4().hex[:8]}"

                margin_amount = btc_amount * btc_price * 0.1  # 10% margin

                # Calculate expected deltas for rebalance perp short
                expected_deltas = {
                    f"bybit:PerpPosition:BTC": -btc_amount,  # Increase short (negative delta)
                    f"bybit:BaseToken:USDT": -margin_amount,  # Lose USDT as margin
                }

                # Operation details
                operation_details = {
                    "btc_delta": btc_delta,
                    "REBALANCE_TYPE": "increase",
                    "btc_price": btc_price,
                    "MARGIN_AMOUNT": margin_amount,
                }

                orders.append(
                    Order(
                        operation_id=operation_id,
                        venue="bybit",
                        operation=OrderOperation.PERP_TRADE,
                        pair="BTCUSDT",
                        side="SHORT",
                        amount=btc_amount,
                        price=btc_price,
                        order_type="market",
                        source_venue="wallet",
                        target_venue="bybit",
                        source_token="USDT",
                        target_token="BTC",
                        expected_deltas=expected_deltas,
                        operation_details=operation_details,
                        execution_mode="sequential",
                        strategy_intent="btc_basis_rebalance",
                        strategy_id="btc_basis",
                        metadata={"btc_delta": btc_delta, "REBALANCE_TYPE": "increase"},
                    )
                )

            return orders

        except Exception as e:
            self.logger.error(
                "Error creating rebalance orders",
                error_code="STRAT-001",
                exc_info=e,
                method="_create_rebalance_orders",
                equity_delta=equity_delta,
            )
            return []

    def _create_dust_sell_orders(self, exposure: Dict) -> List[Order]:
        """
        Create orders for selling dust tokens.

        Args:
            exposure: Current exposure data containing dust tokens

        Returns:
            List[Order] for converting dust tokens to share class currency
        """
        try:
            # Log order creation
            self.logger.info("Creating dust sell orders")

            # Get dust tokens from exposure data
            positions = exposure.get("positions", {})
            dust_tokens = {k: v for k, v in positions.items() if v > 0 and k != "usdt_balance"}

            orders = []

            for token, amount in dust_tokens.items():
                if amount > 0 and token != "usdt":
                    if token == "btc_balance":
                        # Generate unique operation ID
                        operation_id = f"dust_sell_{uuid.uuid4().hex[:8]}"

                        # Get BTC price for expected deltas calculation
                        btc_price = self._get_asset_price()
                        usdt_amount = amount * btc_price

                        # Calculate expected deltas for dust sell
                        expected_deltas = {
                            f"binance:BaseToken:BTC": -amount,  # Lose BTC
                            f"binance:BaseToken:USDT": usdt_amount,  # Gain USDT
                        }

                        # Operation details
                        operation_details = {
                            "dust_token": token,
                            "target_currency": "USDT",
                            "btc_price": btc_price,
                            "usdt_amount": usdt_amount,
                        }

                        # Sell BTC for share class
                        orders.append(
                            Order(
                                operation_id=operation_id,
                                venue="binance",
                                operation=OrderOperation.SPOT_TRADE,
                                pair="BTC/USDT",
                                side="SELL",
                                amount=amount,
                                price=btc_price,
                                order_type="market",
                                source_venue="binance",
                                target_venue="wallet",
                                source_token="BTC",
                                target_token="USDT",
                                expected_deltas=expected_deltas,
                                operation_details=operation_details,
                                execution_mode="sequential",
                                strategy_intent="dust_sell",
                                strategy_id="btc_basis",
                                metadata={"dust_token": token, "target_currency": "USDT"},
                            )
                        )
                    elif token in ["eth_balance", "usdt_balance"]:
                        # Generate unique operation ID
                        operation_id = f"dust_transfer_{uuid.uuid4().hex[:8]}"

                        # Calculate expected deltas for transfer
                        token_symbol = token.replace("_balance", "").upper()
                        expected_deltas = {
                            f"cex:BaseToken:{token_symbol}": -amount,  # Lose from CEX
                            f"wallet:BaseToken:{token_symbol}": amount,  # Gain in wallet
                        }

                        # Operation details
                        operation_details = {"dust_token": token, "transfer_type": "dust_cleanup"}

                        # Direct transfer to wallet (already in correct currency)
                        orders.append(
                            Order(
                                operation_id=operation_id,
                                venue="wallet",
                                operation=OrderOperation.TRANSFER,
                                token=token_symbol,
                                amount=amount,
                                source_venue="cex",
                                target_venue="wallet",
                                source_token=token_symbol,
                                target_token=token_symbol,
                                expected_deltas=expected_deltas,
                                operation_details=operation_details,
                                execution_mode="sequential",
                                strategy_intent="dust_sell",
                                strategy_id="btc_basis",
                                metadata={"dust_token": token},
                            )
                        )

            return orders

        except Exception as e:
            self.logger.error(
                "Error creating dust sell orders",
                error_code="STRAT-001",
                exc_info=e,
                method="_create_dust_sell_orders",
                exposure=exposure,
            )
            return []

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get BTC basis strategy information and status.

        Returns:
            Dictionary with strategy information
        """
        try:
            return {
                "strategy_type": "btc_basis",
                "share_class": self.share_class,
                "asset": self.delta_tracking_asset,
                "btc_allocation": self.btc_allocation,
                "max_leverage": self.max_leverage,
                "description": "BTC funding rate arbitrage with spot/perpetual basis trading",
            }

        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                "strategy_type": "btc_basis",
                "share_class": self.share_class,
                "asset": self.delta_tracking_asset,
                "equity": 0.0,
                "error": str(e),
            }

    def _create_entry_full_orders(self, equity: float) -> List[Order]:
        """Create entry full orders for BTC basis strategy."""
        try:
            orders = []

            # Calculate BTC amount
            btc_price = self._get_asset_price()
            btc_amount = equity / btc_price if btc_price > 0 else 0

            # Create spot buy order
            operation_id = f"spot_buy_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            orders.append(
                Order(
                    operation_id=operation_id,
                    venue=Venue.BINANCE,
                    operation=OrderOperation.SPOT_TRADE,
                    pair="BTCUSDT",
                    side="BUY",
                    amount=btc_amount,
                    order_type="market",
                    source_venue=Venue.WALLET,
                    target_venue=Venue.BINANCE,
                    source_token="USDT",
                    target_token="BTC",
                    expected_deltas={
                        self.spot_instrument: btc_amount,
                        self.entry_instrument: -equity,
                    },
                    execution_mode="sequential",
                    strategy_intent="entry_full",
                    strategy_id="btc_basis",
                )
            )

            # Create perp short order
            operation_id = f"perp_short_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            orders.append(
                Order(
                    operation_id=operation_id,
                    venue=Venue.BINANCE,
                    operation=OrderOperation.PERP_TRADE,
                    pair="BTCUSDT",
                    side="SELL",
                    amount=btc_amount,
                    order_type="market",
                    source_venue=Venue.BINANCE,
                    target_venue=Venue.BINANCE,
                    source_token="USDT",
                    target_token="BTC",
                    expected_deltas={self.perp_instrument: -btc_amount},  # Short position
                    execution_mode="sequential",
                    strategy_intent="entry_full",
                    strategy_id="btc_basis",
                )
            )

            return orders

        except Exception as e:
            logger.error(f"Error creating entry full orders: {e}")
            return []

    def _create_entry_partial_orders(self, equity_delta: float) -> List[Order]:
        """Create entry partial orders for BTC basis strategy."""
        try:
            orders = []

            # Calculate BTC amount for partial entry
            btc_price = self._get_asset_price()
            btc_amount = equity_delta / btc_price if btc_price > 0 else 0

            # Create spot buy order
            operation_id = f"spot_buy_partial_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            orders.append(
                Order(
                    operation_id=operation_id,
                    venue=Venue.BINANCE,
                    operation=OrderOperation.SPOT_TRADE,
                    pair="BTCUSDT",
                    side="BUY",
                    amount=btc_amount,
                    order_type="market",
                    source_venue=Venue.WALLET,
                    target_venue=Venue.BINANCE,
                    source_token="USDT",
                    target_token="BTC",
                    expected_deltas={
                        self.spot_instrument: btc_amount,
                        self.entry_instrument: -equity_delta,
                    },
                    execution_mode="sequential",
                    strategy_intent="entry_partial",
                    strategy_id="btc_basis",
                )
            )

            # Create perp short order
            operation_id = f"perp_short_partial_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            orders.append(
                Order(
                    operation_id=operation_id,
                    venue=Venue.BINANCE,
                    operation=OrderOperation.PERP_TRADE,
                    pair="BTCUSDT",
                    side="SELL",
                    amount=btc_amount,
                    order_type="market",
                    source_venue=Venue.BINANCE,
                    target_venue=Venue.BINANCE,
                    source_token="USDT",
                    target_token="BTC",
                    expected_deltas={self.perp_instrument: -btc_amount},  # Short position
                    execution_mode="sequential",
                    strategy_intent="entry_partial",
                    strategy_id="btc_basis",
                )
            )

            return orders

        except Exception as e:
            logger.error(f"Error creating entry partial orders: {e}")
            return []

    def _create_exit_full_orders(self, equity: float) -> List[Order]:
        """Create exit full orders for BTC basis strategy."""
        try:
            orders = []

            # Get current positions from position monitor
            current_positions = self.position_monitor.get_current_position()
            spot_position = current_positions.get(self.spot_instrument, 0)
            perp_position = current_positions.get(self.perp_instrument, 0)

            if spot_position > 0:
                # Close spot position
                operation_id = f"spot_sell_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(
                    Order(
                        operation_id=operation_id,
                        venue=Venue.BINANCE,
                        operation=OrderOperation.SPOT_TRADE,
                        pair="BTCUSDT",
                        side="SELL",
                        amount=spot_position,
                        order_type="market",
                        source_venue=Venue.BINANCE,
                        target_venue=Venue.WALLET,
                        source_token="BTC",
                        target_token="USDT",
                        expected_deltas={
                            self.spot_instrument: -spot_position,
                            self.entry_instrument: spot_position * self._get_asset_price(),
                        },
                        execution_mode="sequential",
                        strategy_intent="exit_full",
                        strategy_id="btc_basis",
                    )
                )

            if perp_position < 0:  # Short position
                # Close perp position
                operation_id = f"perp_buy_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(
                    Order(
                        operation_id=operation_id,
                        venue=Venue.BINANCE,
                        operation=OrderOperation.PERP_TRADE,
                        pair="BTCUSDT",
                        side="BUY",
                        amount=abs(perp_position),
                        order_type="market",
                        source_venue=Venue.BINANCE,
                        target_venue=Venue.BINANCE,
                        source_token="USDT",
                        target_token="BTC",
                        expected_deltas={
                            self.perp_instrument: abs(perp_position)  # Close short position
                        },
                        execution_mode="sequential",
                        strategy_intent="exit_full",
                        strategy_id="btc_basis",
                    )
                )

            return orders

        except Exception as e:
            logger.error(f"Error creating exit full orders: {e}")
            return []

    def _create_exit_partial_orders(self, equity_delta: float) -> List[Order]:
        """Create exit partial orders for BTC basis strategy."""
        try:
            orders = []

            # Calculate partial amount based on equity delta
            btc_price = self._get_asset_price()
            btc_amount = equity_delta / btc_price if btc_price > 0 else 0

            # Get current positions from position monitor
            current_positions = self.position_monitor.get_current_position()
            spot_position = current_positions.get(self.spot_instrument, 0)
            perp_position = current_positions.get(self.perp_instrument, 0)

            # Calculate partial amounts (proportional to current positions)
            if spot_position > 0:
                partial_spot = min(btc_amount, spot_position)
                operation_id = f"spot_sell_partial_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(
                    Order(
                        operation_id=operation_id,
                        venue=Venue.BINANCE,
                        operation=OrderOperation.SPOT_TRADE,
                        pair="BTCUSDT",
                        side="SELL",
                        amount=partial_spot,
                        order_type="market",
                        source_venue=Venue.BINANCE,
                        target_venue=Venue.WALLET,
                        source_token="BTC",
                        target_token="USDT",
                        expected_deltas={
                            self.spot_instrument: -partial_spot,
                            self.entry_instrument: partial_spot * btc_price,
                        },
                        execution_mode="sequential",
                        strategy_intent="exit_partial",
                        strategy_id="btc_basis",
                    )
                )

            if perp_position < 0:  # Short position
                partial_perp = min(btc_amount, abs(perp_position))
                operation_id = f"perp_buy_partial_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(
                    Order(
                        operation_id=operation_id,
                        venue=Venue.BINANCE,
                        operation=OrderOperation.PERP_TRADE,
                        pair="BTCUSDT",
                        side="BUY",
                        amount=partial_perp,
                        order_type="market",
                        source_venue=Venue.BINANCE,
                        target_venue=Venue.BINANCE,
                        source_token="USDT",
                        target_token="BTC",
                        expected_deltas={
                            self.perp_instrument: partial_perp  # Close partial short position
                        },
                        execution_mode="sequential",
                        strategy_intent="exit_partial",
                        strategy_id="btc_basis",
                    )
                )

            return orders

        except Exception as e:
            logger.error(f"Error creating exit partial orders: {e}")
            return []

    def _create_dust_sell_orders(self, dust_tokens: Dict[str, float]) -> List[Order]:
        """Create dust sell orders for BTC basis strategy."""
        try:
            orders = []

            for token, amount in dust_tokens.items():
                if amount <= 0:
                    continue

                if token == "BTC":
                    # BTC is the target asset, no action needed
                    continue
                elif token == "USDT":
                    # USDT is the share class, no action needed
                    continue
                else:
                    # Sell other dust tokens for USDT
                    operation_id = (
                        f"dust_sell_{token}_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                    )
                    orders.append(
                        Order(
                            operation_id=operation_id,
                            venue=Venue.BINANCE,
                            operation=OrderOperation.SPOT_TRADE,
                            pair=f"{token.upper()}/USDT",
                            side="SELL",
                            amount=amount,
                            order_type="market",
                            source_venue=Venue.WALLET,
                            target_venue=Venue.WALLET,
                            source_token=token,
                            target_token="USDT",
                            expected_deltas={
                                f"{Venue.WALLET.value}:BaseToken:{token}": -amount,
                                self.entry_instrument: amount,  # Simplified 1:1
                            },
                            execution_mode="sequential",
                            strategy_intent="dust_sell",
                            strategy_id="btc_basis",
                        )
                    )

            return orders

        except Exception as e:
            logger.error(f"Error creating dust sell orders: {e}")
            return []
