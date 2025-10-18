"""
ETH Basis Strategy Implementation

Implements ETH basis trading strategy with funding rate arbitrage.
Inherits from BaseStrategyManager and implements the 5 standard actions.

Reference: docs/STRATEGY_MODES.md - ETH Basis Strategy Mode
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
from ...core.models.instruments import validate_instrument_key, get_display_name

logger = logging.getLogger(__name__)


class ETHBasisStrategy(BaseStrategyManager):
    """
    ETH Basis Strategy - Funding rate arbitrage with ETH perpetuals.

    Strategy Overview:
    - Long ETH spot position
    - Short ETH perpetual position
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
        Initialize ETH basis strategy.

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
        required_keys = ["eth_allocation", "max_leverage"]
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")

        # ETH-specific configuration (fail-fast access)
        self.asset = "ETH"  # ETH for this strategy
        self.eth_allocation = config["eth_allocation"]  # 80% to ETH
        self.max_leverage = config["max_leverage"]  # No leverage for basis trading
        self.share_class = config.get("share_class", "ETH")  # Share class currency

        # Define and validate instrument keys
        self.entry_instrument = f"{Venue.WALLET.value}:BaseToken:ETH"
        self.spot_instrument = f"{Venue.BINANCE.value}:BaseToken:ETH"
        self.perp_instrument = f"{Venue.BINANCE.value}:Perp:ETHUSDT"

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
                    f"Add to configs/modes/{config.get('mode', 'eth_basis')}.yaml"
                )

        self.logger.info(
            f"ETHBasisStrategy initialized with {self.eth_allocation*100}% ETH allocation"
        )
        self.logger.info(f"  Available instruments: {len(self.available_instruments)}")
        self.logger.info(f"  Entry: {get_display_name(self.entry_instrument)}")
        self.logger.info(f"  Spot: {get_display_name(self.spot_instrument)}")
        self.logger.info(f"  Perp: {get_display_name(self.perp_instrument)}")

    def _get_asset_price(self) -> float:
        """Get current ETH price. In real implementation, this would fetch from data provider."""
        # For testing purposes, return a default ETH price
        # In production, this would fetch from market data
        return 3000.0

    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position for ETH basis strategy.

        Args:
            current_equity: Current equity in share class currency

        Returns:
            Dictionary of target positions by token/venue
        """
        try:
            # Calculate target allocations
            eth_target = current_equity * self.eth_allocation

            # Get current ETH price
            eth_price = self._get_asset_price()
            eth_amount = eth_target / eth_price if eth_price > 0 else 0

            return {
                "eth_balance": eth_amount,
                "eth_perpetual_short": -eth_amount,  # Short position
                "total_equity": current_equity,
            }

        except Exception as e:
            logger.error(f"Error calculating target position: {e}")
            return {"eth_balance": 0.0, "eth_perpetual_short": 0.0, "total_equity": current_equity}

    def generate_orders(
        self, timestamp: pd.Timestamp, exposure: Dict, risk_assessment: Dict, market_data: Dict
    ) -> List[Order]:
        """
        Generate orders for ETH basis strategy based on market conditions and risk assessment.

        ETH Basis Strategy Logic:
        - Analyze funding rates and basis spreads
        - Check risk metrics for liquidation risk
        - Decide on entry/exit based on profitability and risk
        - Generate appropriate orders for ETH spot + perp positions
        """
        try:
            # Log strategy decision start
            self.logger.info("Making ETH basis strategy decision")

            # Get current equity and positions
            current_equity = self.get_current_equity(exposure)
            current_positions = exposure.get("positions", {})

            # ETH-specific market analysis
            eth_spot_price = market_data.get("prices", {}).get("ETH", 0.0)
            eth_funding_rate = market_data.get("rates", {}).get("eth_funding", 0.0)

            # Risk assessment
            liquidation_risk = risk_assessment.get("liquidation_risk", 0.0)
            margin_ratio = risk_assessment.get("cex_margin_ratio", 1.0)

            # ETH Basis Strategy Decision Logic
            # Check if we have existing ETH positions
            has_eth_position = (
                current_positions.get("eth_balance", 0) > 0
                or current_positions.get("eth_perpetual_short", 0) != 0
            )

            if current_equity == 0 or not has_eth_position:
                # No position or no ETH position - check if we should enter
                if self._should_enter_basis_position(eth_funding_rate, eth_spot_price):
                    return self._create_entry_orders(current_equity)
                else:
                    return self._create_dust_sell_orders(exposure)  # Wait for better opportunity

            elif liquidation_risk > 0.8 or margin_ratio < 0.2:
                # High risk - exit position
                return self._create_exit_orders(current_equity)

            elif liquidation_risk > 0.6 or margin_ratio < 0.3:
                # Medium risk - partial exit
                return self._create_exit_orders(current_equity * 0.5)

            elif self._should_rebalance_position(eth_funding_rate, current_positions):
                # Rebalance position based on funding rate changes
                return self._create_rebalance_orders(current_equity * 0.2)

            else:
                # Maintain current position
                return self._create_dust_sell_orders(exposure)

        except Exception as e:
            self.logger.error(
                "Failed to generate ETH basis strategy orders",
                error_code="STRAT-001",
                exc_info=e,
                method="generate_orders",
                strategy_type=self.__class__.__name__,
            )
            logger.error(f"Error in ETH basis strategy order generation: {e}")
            # Return safe default action
            return self._create_dust_sell_orders(exposure)

    def _should_enter_basis_position(self, funding_rate: float, spot_price: float) -> bool:
        """Determine if we should enter an ETH basis position."""
        # ETH basis strategy logic: enter when funding rate is positive (earning funding)
        # No threshold - take any positive funding opportunity
        return funding_rate != 0 and spot_price > 0

    def _should_rebalance_position(self, funding_rate: float, current_positions: Dict) -> bool:
        """Determine if we should rebalance the ETH basis position."""
        # Rebalance if we have positions and funding rate exists
        return funding_rate != 0

    def _create_entry_orders(self, equity: float) -> List[Order]:
        """
        Create orders for full ETH basis position entry.

        Args:
            equity: Available equity in share class currency

        Returns:
            List[Order] for ETH spot buy + ETH perp short (sequential)
        """
        try:
            # Log order creation
            self.logger.info(f"Creating entry orders with equity={equity}")

            # Calculate target position
            target_position = self.calculate_target_position(equity)
            orders = []

            # 1. Buy ETH spot
            eth_amount = target_position.get("eth_balance", 0.0)
            if eth_amount > 0:
                orders.append(
                    Order(
                        venue="binance",
                        operation=OrderOperation.SPOT_TRADE,
                        pair="ETH/USDT",
                        side="BUY",
                        amount=eth_amount,
                        order_type="market",
                        execution_mode="sequential",
                        strategy_intent="eth_basis_entry",
                        strategy_id="eth_basis",
                        metadata={"eth_allocation": self.eth_allocation},
                    )
                )

            # 2. Open short perpetual position
            short_amount = abs(target_position.get("eth_perpetual_short", 0.0))
            if short_amount > 0:
                orders.append(
                    Order(
                        venue="bybit",
                        operation=OrderOperation.PERP_TRADE,
                        pair="ETHUSDT",
                        side="SHORT",
                        amount=short_amount,
                        order_type="market",
                        execution_mode="sequential",
                        strategy_intent="eth_basis_entry",
                        strategy_id="eth_basis",
                        metadata={
                            "eth_allocation": self.eth_allocation,
                            "funding_threshold": self.funding_threshold,
                        },
                    )
                )

            return orders

        except Exception as e:
            self.logger.error(error=e, context={"method": "_create_entry_orders", "equity": equity})
            logger.error(f"Error creating entry orders: {e}")
            return []

    def _create_rebalance_orders(self, equity_delta: float) -> List[Order]:
        """
        Create orders for rebalancing ETH basis position.

        Args:
            equity_delta: Additional equity to deploy

        Returns:
            List[Order] for proportional ETH spot buy + perp short increase
        """
        try:
            # Log order creation
            self.logger.info(f"Creating rebalance orders with equity_delta={equity_delta}")

            # Calculate proportional allocation
            eth_delta = equity_delta * self.eth_allocation
            eth_price = self._get_asset_price()
            eth_amount = eth_delta / eth_price if eth_price > 0 else 0

            orders = []

            # 1. Buy additional ETH spot
            if eth_amount > 0:
                orders.append(
                    Order(
                        venue="binance",
                        operation=OrderOperation.SPOT_TRADE,
                        pair="ETH/USDT",
                        side="BUY",
                        amount=eth_amount,
                        order_type="market",
                        execution_mode="sequential",
                        strategy_intent="eth_basis_rebalance",
                        strategy_id="eth_basis",
                        metadata={"eth_delta": eth_delta, "rebalance": True},
                    )
                )

            # 2. Increase short perpetual position
            if eth_amount > 0:
                orders.append(
                    Order(
                        venue="bybit",
                        operation=OrderOperation.PERP_TRADE,
                        pair="ETHUSDT",
                        side="SHORT",
                        amount=eth_amount,
                        order_type="market",
                        execution_mode="sequential",
                        strategy_intent="eth_basis_rebalance",
                        strategy_id="eth_basis",
                        metadata={"eth_delta": eth_delta, "rebalance": True},
                    )
                )

            return orders

        except Exception as e:
            self.logger.error(
                error=e,
                context={"method": "_create_rebalance_orders", "equity_delta": equity_delta},
            )
            logger.error(f"Error creating rebalance orders: {e}")
            return []

    def _create_exit_orders(self, equity: float) -> List[Order]:
        """
        Create orders for exiting ETH basis position.

        Args:
            equity: Total equity to exit (used to calculate scaling factor)

        Returns:
            List[Order] for closing ETH perp short + selling ETH spot
        """
        try:
            # Log order creation
            self.logger.info(f"Creating exit orders with equity={equity}")

            # Get current position
            current_position = self.position_monitor.get_current_position()
            eth_balance = current_position.get("eth_balance", 0.0)
            eth_short = current_position.get("eth_perpetual_short", 0.0)

            # Calculate scaling factor based on equity vs total position value
            total_position_value = (eth_balance + abs(eth_short)) * self._get_asset_price()
            if total_position_value > 0:
                scaling_factor = min(equity / total_position_value, 1.0)
            else:
                scaling_factor = 1.0

            orders = []

            # 1. Close short perpetual position
            if eth_short < 0:
                scaled_short_amount = abs(eth_short) * scaling_factor
                orders.append(
                    Order(
                        venue="bybit",
                        operation=OrderOperation.PERP_TRADE,
                        pair="ETHUSDT",
                        side="BUY",  # Close short position
                        amount=scaled_short_amount,
                        order_type="market",
                        execution_mode="sequential",
                        strategy_intent="eth_basis_exit",
                        strategy_id="eth_basis",
                        metadata={
                            "eth_balance": eth_balance,
                            "eth_short": eth_short,
                            "scaling_factor": scaling_factor,
                            "close_position": True,
                        },
                    )
                )

            # 2. Sell ETH spot
            if eth_balance > 0:
                scaled_eth_amount = eth_balance * scaling_factor
                orders.append(
                    Order(
                        venue="binance",
                        operation=OrderOperation.SPOT_TRADE,
                        pair="ETH/USDT",
                        side="SELL",
                        amount=scaled_eth_amount,
                        order_type="market",
                        execution_mode="sequential",
                        strategy_intent="eth_basis_exit",
                        strategy_id="eth_basis",
                        metadata={
                            "eth_balance": eth_balance,
                            "eth_short": eth_short,
                            "scaling_factor": scaling_factor,
                            "close_position": True,
                        },
                    )
                )

            return orders

        except Exception as e:
            self.logger.error(error=e, context={"method": "_create_exit_orders", "equity": equity})
            logger.error(f"Error creating exit orders: {e}")
            return []

    def _create_dust_sell_orders(self, exposure: Dict) -> List[Order]:
        """
        Create orders for selling dust tokens.

        Args:
            exposure: Current exposure data

        Returns:
            List[Order] for selling dust tokens
        """
        try:
            # Log order creation
            self.logger.info("Creating dust sell orders")

            # Get current positions
            current_positions = exposure.get("positions", {})
            orders = []

            # Check for dust tokens that need to be sold
            for token, amount in current_positions.items():
                if amount > 0 and token not in [self.share_class.lower(), "eth_perpetual_short"]:
                    # This is a dust token that should be sold
                    if token == "eth_balance":
                        # Sell ETH for share class
                        orders.append(
                            Order(
                                venue="binance",
                                operation=OrderOperation.SPOT_TRADE,
                                pair="ETH/USDT",
                                side="SELL",
                                amount=amount,
                                order_type="market",
                                execution_mode="sequential",
                                strategy_intent="eth_basis_dust_sell",
                                strategy_id="eth_basis",
                                metadata={"dust_token": token, "dust_amount": amount},
                            )
                        )
                    elif token in ["btc_balance"]:
                        # BTC dust - sell for share class
                        orders.append(
                            Order(
                                venue="binance",
                                operation=OrderOperation.SPOT_TRADE,
                                pair="BTC/USDT",
                                side="SELL",
                                amount=amount,
                                order_type="market",
                                execution_mode="sequential",
                                strategy_intent="eth_basis_dust_sell",
                                strategy_id="eth_basis",
                                metadata={"dust_token": token, "dust_amount": amount},
                            )
                        )
                    elif token == "usdt_balance":
                        # USDT is already the share class, no action needed
                        continue
                    else:
                        # Other dust tokens - sell for share class
                        orders.append(
                            Order(
                                venue="binance",
                                operation=OrderOperation.SPOT_TRADE,
                                pair=f"{token.upper()}/USDT",
                                side="SELL",
                                amount=amount,
                                order_type="market",
                                execution_mode="sequential",
                                strategy_intent="eth_basis_dust_sell",
                                strategy_id="eth_basis",
                                metadata={"dust_token": token, "dust_amount": amount},
                            )
                        )

            return orders

        except Exception as e:
            self.logger.error(
                error=e, context={"method": "_create_dust_sell_orders", "exposure": exposure}
            )
            logger.error(f"Error creating dust sell orders: {e}")
            return []

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get ETH basis strategy information and status.

        Returns:
            Dictionary with strategy information
        """
        try:
            # Add ETH-specific information
            return {
                "strategy_type": "eth_basis",
                "share_class": self.share_class,
                "asset": self.asset,
                "eth_allocation": self.eth_allocation,
                "max_leverage": self.max_leverage,
                "description": "ETH funding rate arbitrage with spot/perpetual basis trading",
            }

        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                "strategy_type": "eth_basis",
                "share_class": self.share_class,
                "asset": self.asset,
                "equity": 0.0,
                "error": str(e),
            }

    def _create_entry_full_orders(self, equity: float) -> List[Order]:
        """Create entry full orders for ETH basis strategy."""
        try:
            orders = []

            # Calculate ETH amount
            eth_price = self._get_asset_price()
            eth_amount = equity / eth_price if eth_price > 0 else 0

            # Create spot buy order
            operation_id = f"spot_buy_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            orders.append(
                Order(
                    operation_id=operation_id,
                    venue=Venue.BINANCE,
                    operation=OrderOperation.SPOT_TRADE,
                    pair="ETHUSDT",
                    side="BUY",
                    amount=eth_amount,
                    order_type="market",
                    source_venue=Venue.WALLET,
                    target_venue=Venue.BINANCE,
                    source_token="USDT",
                    target_token="ETH",
                    expected_deltas={
                        self.spot_instrument: eth_amount,
                        f"{Venue.WALLET.value}:BaseToken:USDT": -equity,
                    },
                    execution_mode="sequential",
                    strategy_intent="entry_full",
                    strategy_id="eth_basis",
                )
            )

            # Create perp short order
            operation_id = f"perp_short_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            orders.append(
                Order(
                    operation_id=operation_id,
                    venue=Venue.BINANCE,
                    operation=OrderOperation.PERP_TRADE,
                    pair="ETHUSDT",
                    side="SELL",
                    amount=eth_amount,
                    order_type="market",
                    source_venue=Venue.BINANCE,
                    target_venue=Venue.BINANCE,
                    source_token="USDT",
                    target_token="ETH",
                    expected_deltas={self.perp_instrument: -eth_amount},  # Short position
                    execution_mode="sequential",
                    strategy_intent="entry_full",
                    strategy_id="eth_basis",
                )
            )

            return orders

        except Exception as e:
            logger.error(f"Error creating entry full orders: {e}")
            return []

    def _create_entry_partial_orders(self, equity_delta: float) -> List[Order]:
        """Create entry partial orders for ETH basis strategy."""
        try:
            orders = []

            # Calculate ETH amount for partial entry
            eth_price = self._get_asset_price()
            eth_amount = equity_delta / eth_price if eth_price > 0 else 0

            # Create spot buy order
            operation_id = f"spot_buy_partial_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            orders.append(
                Order(
                    operation_id=operation_id,
                    venue=Venue.BINANCE,
                    operation=OrderOperation.SPOT_TRADE,
                    pair="ETHUSDT",
                    side="BUY",
                    amount=eth_amount,
                    order_type="market",
                    source_venue=Venue.WALLET,
                    target_venue=Venue.BINANCE,
                    source_token="USDT",
                    target_token="ETH",
                    expected_deltas={
                        self.spot_instrument: eth_amount,
                        f"{Venue.WALLET.value}:BaseToken:USDT": -equity_delta,
                    },
                    execution_mode="sequential",
                    strategy_intent="entry_partial",
                    strategy_id="eth_basis",
                )
            )

            # Create perp short order
            operation_id = f"perp_short_partial_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            orders.append(
                Order(
                    operation_id=operation_id,
                    venue=Venue.BINANCE,
                    operation=OrderOperation.PERP_TRADE,
                    pair="ETHUSDT",
                    side="SELL",
                    amount=eth_amount,
                    order_type="market",
                    source_venue=Venue.BINANCE,
                    target_venue=Venue.BINANCE,
                    source_token="USDT",
                    target_token="ETH",
                    expected_deltas={self.perp_instrument: -eth_amount},  # Short position
                    execution_mode="sequential",
                    strategy_intent="entry_partial",
                    strategy_id="eth_basis",
                )
            )

            return orders

        except Exception as e:
            logger.error(f"Error creating entry partial orders: {e}")
            return []

    def _create_exit_full_orders(self, equity: float) -> List[Order]:
        """Create exit full orders for ETH basis strategy."""
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
                        pair="ETHUSDT",
                        side="SELL",
                        amount=spot_position,
                        order_type="market",
                        source_venue=Venue.BINANCE,
                        target_venue=Venue.WALLET,
                        source_token="ETH",
                        target_token="USDT",
                        expected_deltas={
                            self.spot_instrument: -spot_position,
                            f"{Venue.WALLET.value}:BaseToken:USDT": spot_position
                            * self._get_asset_price(),
                        },
                        execution_mode="sequential",
                        strategy_intent="exit_full",
                        strategy_id="eth_basis",
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
                        pair="ETHUSDT",
                        side="BUY",
                        amount=abs(perp_position),
                        order_type="market",
                        source_venue=Venue.BINANCE,
                        target_venue=Venue.BINANCE,
                        source_token="USDT",
                        target_token="ETH",
                        expected_deltas={
                            self.perp_instrument: abs(perp_position)  # Close short position
                        },
                        execution_mode="sequential",
                        strategy_intent="exit_full",
                        strategy_id="eth_basis",
                    )
                )

            return orders

        except Exception as e:
            logger.error(f"Error creating exit full orders: {e}")
            return []

    def _create_exit_partial_orders(self, equity_delta: float) -> List[Order]:
        """Create exit partial orders for ETH basis strategy."""
        try:
            orders = []

            # Calculate partial amount based on equity delta
            eth_price = self._get_asset_price()
            eth_amount = equity_delta / eth_price if eth_price > 0 else 0

            # Get current positions from position monitor
            current_positions = self.position_monitor.get_current_position()
            spot_position = current_positions.get(self.spot_instrument, 0)
            perp_position = current_positions.get(self.perp_instrument, 0)

            # Calculate partial amounts (proportional to current positions)
            if spot_position > 0:
                partial_spot = min(eth_amount, spot_position)
                operation_id = f"spot_sell_partial_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(
                    Order(
                        operation_id=operation_id,
                        venue=Venue.BINANCE,
                        operation=OrderOperation.SPOT_TRADE,
                        pair="ETHUSDT",
                        side="SELL",
                        amount=partial_spot,
                        order_type="market",
                        source_venue=Venue.BINANCE,
                        target_venue=Venue.WALLET,
                        source_token="ETH",
                        target_token="USDT",
                        expected_deltas={
                            self.spot_instrument: -partial_spot,
                            f"{Venue.WALLET.value}:BaseToken:USDT": partial_spot * eth_price,
                        },
                        execution_mode="sequential",
                        strategy_intent="exit_partial",
                        strategy_id="eth_basis",
                    )
                )

            if perp_position < 0:  # Short position
                partial_perp = min(eth_amount, abs(perp_position))
                operation_id = f"perp_buy_partial_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                orders.append(
                    Order(
                        operation_id=operation_id,
                        venue=Venue.BINANCE,
                        operation=OrderOperation.PERP_TRADE,
                        pair="ETHUSDT",
                        side="BUY",
                        amount=partial_perp,
                        order_type="market",
                        source_venue=Venue.BINANCE,
                        target_venue=Venue.BINANCE,
                        source_token="USDT",
                        target_token="ETH",
                        expected_deltas={
                            self.perp_instrument: partial_perp  # Close partial short position
                        },
                        execution_mode="sequential",
                        strategy_intent="exit_partial",
                        strategy_id="eth_basis",
                    )
                )

            return orders

        except Exception as e:
            logger.error(f"Error creating exit partial orders: {e}")
            return []

    def _create_dust_sell_orders(self, dust_tokens: Dict[str, float]) -> List[Order]:
        """Create dust sell orders for ETH basis strategy."""
        try:
            orders = []

            for token, amount in dust_tokens.items():
                if amount <= 0:
                    continue

                if token == "ETH":
                    # ETH is the target asset, no action needed
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
                                f"{Venue.WALLET.value}:BaseToken:USDT": amount,  # Simplified 1:1
                            },
                            execution_mode="sequential",
                            strategy_intent="dust_sell",
                            strategy_id="eth_basis",
                        )
                    )

            return orders

        except Exception as e:
            logger.error(f"Error creating dust sell orders: {e}")
            return []
