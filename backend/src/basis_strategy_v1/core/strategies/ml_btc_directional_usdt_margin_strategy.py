"""
ML BTC Directional Strategy Implementation

Implements ML-driven directional BTC trading strategy using 5-minute interval signals
to generate long/short positions. Uses machine learning predictions for entry/exit signals
while taking full directional BTC exposure. Uses unified Order/Trade system.

Reference: docs/specs/strategies/08_ML_BTC_DIRECTIONAL_STRATEGY.md
Reference: docs/STRATEGY_MODES.md - ML BTC Directional Strategy Mode
Reference: docs/specs/5B_BASE_STRATEGY_MANAGER.md - Component specification
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
import pandas as pd

from .base_strategy_manager import BaseStrategyManager
from ...core.models.order import Order, OrderOperation
from ...core.models.venues import Venue
from ...core.models.instruments import validate_instrument_key, get_display_name

logger = logging.getLogger(__name__)


class MLBTCDirectionalUSDTMarginStrategy(BaseStrategyManager):
    """
    ML BTC Directional Strategy - ML-driven directional BTC trading.

    Strategy Overview:
    - Uses ML predictions for entry/exit signals
    - Takes full directional BTC exposure
    - 5-minute interval signal processing
    - Stop-loss and take-profit management
    - Target APY: 20-40% (high risk, high reward)
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
        Initialize ML BTC directional strategy.

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

        # Store data provider for ML predictions
        self.data_provider = data_provider

        # Validate required configuration at startup (fail-fast)
        required_keys = [
            "signal_threshold",
            "max_position_size",
            "stop_loss_pct",
            "take_profit_pct",
        ]
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")

        # ML-specific configuration (fail-fast access)
        self.signal_threshold = config["signal_threshold"]  # 0.65 default
        self.max_position_size = config["max_position_size"]  # Max position size
        self.stop_loss_pct = config["stop_loss_pct"]  # Stop loss percentage
        self.take_profit_pct = config["take_profit_pct"]  # Take profit percentage
        self.share_class = config.get("share_class", "USDT")  # Share class currency
        self.delta_tracking_asset = (
            config.get("component_config", {})
            .get("risk_monitor", {})
            .get("delta_tracking_asset", "BTC")
        )

        # Define and validate instrument keys
        self.entry_instrument = f"{Venue.WALLET.value}:BaseToken:USDT"
        self.perp_instrument = f"{Venue.BINANCE.value}:Perp:BTCUSDT"

        # Validate instrument keys
        validate_instrument_key(self.entry_instrument)
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
        required_instruments = [self.entry_instrument, self.perp_instrument]

        # Validate all required instruments are in available set
        for instrument in required_instruments:
            if instrument not in self.available_instruments:
                raise ValueError(
                    f"Required instrument {instrument} not in position_subscriptions. "
                    f"Add to configs/modes/{config.get('mode', 'ml_btc_directional_usdt_margin')}.yaml"
                )

        # ML model state
        self.ml_model = None
        self.last_prediction = None
        self.last_signal = None

        logger.info(
            f"MLBTCDirectionalStrategy initialized with signal threshold: {self.signal_threshold}"
        )
        logger.info(f"  Available instruments: {len(self.available_instruments)}")
        logger.info(f"  Entry: {get_display_name(self.entry_instrument)}")
        logger.info(f"  Perp: {get_display_name(self.perp_instrument)}")

    def _get_asset_price(self) -> float:
        """Get current BTC price for testing."""
        # In real implementation, this would get actual price from market data
        return 50000.0  # Mock BTC price

    def _calculate_stop_loss_take_profit(
        self, entry_price: float, signal_data: Dict[str, Any], side: str
    ) -> Dict[str, Optional[float]]:
        """
        Calculate stop-loss and take-profit prices using standard deviation from ML signal.

        Args:
            entry_price: Entry price for the position
            signal_data: ML signal data containing 'sd' field (standard deviation)
            side: 'LONG' or 'SHORT'

        Returns:
            Dict with 'stop_loss' and 'take_profit' prices
        """
        try:
            # Get ML config
            ml_config = self.config.get("ml_config", {})
            take_profit_sd = ml_config.get("take_profit_sd", 2.0)
            stop_loss_sd = ml_config.get("stop_loss_sd", 2.0)
            sd_floor_bps = ml_config.get("sd_floor_bps", 10)  # 10 bps minimum
            sd_cap_bps = ml_config.get("sd_cap_bps", 1000)  # 10% maximum

            # Get standard deviation from ML signal
            raw_sd = signal_data.get("sd", 0.0)

            # Floor and cap the SD in basis points
            sd_bps = max(sd_floor_bps, min(raw_sd * 10000, sd_cap_bps))
            sd_decimal = sd_bps / 10000  # Convert back to decimal

            # Calculate price moves
            take_profit_move = entry_price * sd_decimal * take_profit_sd
            stop_loss_move = entry_price * sd_decimal * stop_loss_sd

            if side == "LONG":
                take_profit = entry_price + take_profit_move
                stop_loss = entry_price - stop_loss_move
            elif side == "SHORT":
                take_profit = entry_price - take_profit_move
                stop_loss = entry_price + stop_loss_move
            else:
                raise ValueError(f"Invalid side: {side}")

            return {
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "sd_used": sd_decimal,
                "tp_sd_multiplier": take_profit_sd,
                "sl_sd_multiplier": stop_loss_sd,
            }

        except Exception as e:
            logger.error(f"Error calculating SL/TP: {e}")
            return {"take_profit": None, "stop_loss": None}

    def make_strategy_decision(
        self,
        timestamp: pd.Timestamp,
        trigger_source: str,
        market_data: Dict,
        exposure_data: Dict,
        risk_assessment: Dict,
    ) -> List[Order]:
        """
        Make ML BTC directional strategy decision based on market conditions and ML predictions.

        Args:
            timestamp: Current timestamp
            trigger_source: What triggered this decision
            market_data: Current market data
            exposure_data: Current exposure data
            risk_assessment: Risk assessment data

        Returns:
            List of Order objects to execute
        """
        try:
            # Log strategy decision start
            self.logger.info("Making ML BTC directional strategy decision")

            # Get current equity and positions
            current_equity = exposure_data.get("total_exposure", 0.0)
            current_positions = exposure_data.get("positions", {})

            # Get ML predictions from data provider
            ml_predictions = self._get_ml_predictions(market_data)

            # BTC-specific market analysis
            btc_price = market_data.get("prices", {}).get("BTC", 0.0)
            btc_perp_price = market_data.get("prices", {}).get("BTC_PERP", 0.0)

            # Risk assessment
            liquidation_risk = risk_assessment.get("liquidation_risk", 0.0)
            margin_ratio = risk_assessment.get("cex_margin_ratio", 1.0)

            # ML BTC Directional Strategy Decision Logic
            if ml_predictions is None:
                # No ML predictions available - maintain current position
                return self._create_dust_sell_orders({})

            # Check risk management first
            if self._should_exit_for_risk_management(btc_price, current_positions, ml_predictions):
                return self._create_exit_full_orders(current_equity)

            # Check ML signal for entry/exit
            if ml_predictions["confidence"] > self.signal_threshold:
                signal = ml_predictions["signal"]

                if signal == "long" and not self._has_long_position(current_positions):
                    # Enter long position
                    return self._create_entry_full_orders(current_equity, signal)
                elif signal == "short" and not self._has_short_position(current_positions):
                    # Enter short position
                    return self._create_entry_full_orders(current_equity, signal)
                elif signal == "neutral" and self._has_any_position(current_positions):
                    # Exit position
                    return self._create_exit_full_orders(current_equity)

            # Default: maintain current position
            return self._create_dust_sell_orders({})

        except Exception as e:
            self.logger.error(
                "Error in generate_orders",
                error_code="GENERATE_ORDERS_ERROR",
                exc_info=e,
                method="generate_orders",
                strategy_type=self.__class__.__name__,
            )
            return []

    def _get_ml_predictions(self, market_data: Dict) -> Dict:
        """Get ML predictions from data provider."""
        try:
            if self.data_provider is None:
                return None

            # Get ML predictions from data provider using canonical pattern
            # This would be implemented based on the actual ML model integration
            if not self.utility_manager:
                raise ValueError("utility_manager is required but not provided")
            data = self.utility_manager.data_provider.get_data(pd.Timestamp.now())
            ml_predictions = data["ml_data"]["predictions"]["btc_directional"]

            if ml_predictions is None:
                return None

            return {
                "signal": ml_predictions.get("signal", "neutral"),
                "confidence": ml_predictions.get("confidence", 0.0),
                "sd": ml_predictions.get("sd", 0.02),  # Default 2% standard deviation
                "timestamp": ml_predictions.get("timestamp", 0),
            }

        except Exception as e:
            logger.error(f"Error getting ML predictions: {e}")
            return None

    def _get_ml_signal(self) -> Dict:
        """Get ML signal for testing - simplified interface."""
        try:
            # For testing, return a mock signal
            return {"signal": "LONG", "confidence": 0.8, "sd": 0.02}
        except Exception as e:
            logger.error(f"Error getting ML signal: {e}")
            return None

    def _get_asset_price(self) -> float:
        """Get current BTC price for testing."""
        # In real implementation, this would get actual price from market data
        return 45000.0  # Mock BTC price

    def _should_exit_for_risk_management(
        self, current_price: float, current_positions: Dict, ml_predictions: Dict
    ) -> bool:
        """Check if we should exit position for risk management."""
        try:
            current_position = current_positions.get("btc_perp_position", 0.0)

            if current_position == 0:
                return False

            # Calculate stop-loss and take-profit from standard deviation
            stop_loss, take_profit = self._calculate_sl_tp_levels(
                current_price,
                ml_predictions.get("sd", 0.02),
                ml_predictions.get("signal", "neutral"),
            )

            # Check stop-loss and take-profit
            if current_position > 0:  # Long position
                if current_price <= stop_loss:
                    return True
                if current_price >= take_profit:
                    return True
            elif current_position < 0:  # Short position
                if current_price >= stop_loss:
                    return True
                if current_price <= take_profit:
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking risk management: {e}")
            return False

    def _calculate_sl_tp_levels(self, current_price: float, sd: float, signal: str) -> tuple:
        """
        Calculate stop-loss and take-profit levels based on standard deviation.

        Args:
            current_price: Current BTC price
            sd: Standard deviation (as decimal, e.g., 0.02 for 2%)
            signal: Trading signal ('long', 'short', 'neutral')

        Returns:
            Tuple of (stop_loss, take_profit)
        """
        if signal == "long":
            stop_loss = current_price * (1 - 2 * sd)  # 2x SD stop loss
            take_profit = current_price * (1 + 3 * sd)  # 3x SD take profit
        elif signal == "short":
            stop_loss = current_price * (1 + 2 * sd)  # 2x SD stop loss
            take_profit = current_price * (1 - 3 * sd)  # 3x SD take profit
        else:  # neutral
            stop_loss = 0.0
            take_profit = 0.0

        return stop_loss, take_profit

    def _has_long_position(self, current_positions: Dict) -> bool:
        """Check if we have a long position."""
        return current_positions.get("btc_perp_position", 0.0) > 0

    def _has_short_position(self, current_positions: Dict) -> bool:
        """Check if we have a short position."""
        return current_positions.get("btc_perp_position", 0.0) < 0

    def _has_any_position(self, current_positions: Dict) -> bool:
        """Check if we have any position."""
        return current_positions.get("btc_perp_position", 0.0) != 0

    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """
        Calculate target position for ML BTC directional strategy.

        Args:
            current_equity: Current equity in share class currency

        Returns:
            Dictionary of target positions by token/venue
        """
        try:
            # For ML directional strategy, we use the full equity for directional exposure
            btc_target = current_equity * self.max_position_size

            return {"btc_perp_position": btc_target, "usdt_balance": current_equity - btc_target}

        except Exception as e:
            logger.error(f"Failed to calculate target position: {e}")
            return {"btc_perp_position": 0.0, "usdt_balance": current_equity}

    def _create_entry_full_orders(self, equity: float, signal: str) -> List[Order]:
        """
        Create entry full orders for ML BTC directional strategy.

        Args:
            equity: Available equity in share class currency
            signal: ML signal ('long' or 'short')

        Returns:
            List of Order objects for full entry
        """
        try:
            # Calculate target position
            target_position = self.calculate_target_position(equity)

            # Store signal for reference
            self.last_signal = signal

            # Calculate take profit and stop loss
            btc_price = self._get_asset_price()
            stop_loss, take_profit = self._calculate_sl_tp_levels(
                btc_price, 0.02, signal  # 2% standard deviation
            )

            # Create BTC perpetual order with risk management
            operation_id = f"perp_trade_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            order = Order(
                operation_id=operation_id,
                venue=Venue.BINANCE,
                operation=OrderOperation.PERP_TRADE,
                pair="BTCUSDT",
                side="LONG" if signal == "long" else "SHORT",
                amount=target_position["btc_perp_position"],
                price=btc_price,
                order_type="market",
                take_profit=take_profit,
                stop_loss=stop_loss,
                source_venue=Venue.BINANCE,
                target_venue=Venue.BINANCE,
                source_token="USDT",
                target_token="BTC",
                expected_deltas={
                    self.perp_instrument: (
                        target_position["btc_perp_position"]
                        if signal == "long"
                        else -target_position["btc_perp_position"]
                    )
                },
                execution_mode="sequential",
                strategy_intent="entry_full",
                strategy_id="ml_btc_directional",
                metadata={
                    "ml_signal": signal,
                    "confidence": 0.8,  # Would come from ML predictions
                    "signal_threshold": self.signal_threshold,
                },
            )

            return [order]

        except Exception as e:
            logger.error(f"Error creating entry full orders: {e}")
            return []

    def _create_entry_partial_orders(self, equity_delta: float, signal: str) -> List[Order]:
        """
        Create entry partial orders for ML BTC directional strategy.

        Args:
            equity_delta: Additional equity to deploy
            signal: ML signal ('long' or 'short')

        Returns:
            List of Order objects for partial entry
        """
        try:
            # Calculate partial position
            partial_position = equity_delta * self.max_position_size

            # Store signal for reference
            self.last_signal = signal

            # Calculate take profit and stop loss
            btc_price = self._get_asset_price()
            stop_loss, take_profit = self._calculate_sl_tp_levels(
                btc_price, 0.02, signal  # 2% standard deviation
            )

            # Create BTC perpetual order with risk management
            operation_id = f"perp_trade_partial_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            order = Order(
                operation_id=operation_id,
                venue=Venue.BINANCE,
                operation=OrderOperation.PERP_TRADE,
                pair="BTCUSDT",
                side="LONG" if signal == "long" else "SHORT",
                amount=partial_position,
                price=btc_price,
                order_type="market",
                take_profit=take_profit,
                stop_loss=stop_loss,
                source_venue=Venue.BINANCE,
                target_venue=Venue.BINANCE,
                source_token="USDT",
                target_token="BTC",
                expected_deltas={
                    self.perp_instrument: (
                        partial_position if signal == "long" else -partial_position
                    )
                },
                execution_mode="sequential",
                strategy_intent="entry_partial",
                strategy_id="ml_btc_directional",
                metadata={
                    "ml_signal": signal,
                    "confidence": 0.8,  # Would come from ML predictions
                    "signal_threshold": self.signal_threshold,
                },
            )

            return [order]

        except Exception as e:
            logger.error(f"Error creating entry partial orders: {e}")
            return []

    def _create_exit_full_orders(self, equity: float) -> List[Order]:
        """
        Create exit full orders for ML BTC directional strategy.

        Args:
            equity: Total equity to exit

        Returns:
            List of Order objects for full exit
        """
        try:
            # Get current position to determine close side
            current_position = self.position_monitor.get_current_position()
            btc_position = current_position.get("btc_perp_position", 0.0)

            if btc_position == 0:
                return []  # No position to close

            # Determine close side based on current position
            close_side = "SELL" if btc_position > 0 else "BUY"

            # Create close position order
            operation_id = f"perp_close_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            order = Order(
                operation_id=operation_id,
                venue=Venue.BINANCE,
                operation=OrderOperation.PERP_TRADE,
                pair="BTCUSDT",
                side=close_side,
                amount=abs(btc_position),
                order_type="market",
                source_venue=Venue.BINANCE,
                target_venue=Venue.BINANCE,
                source_token="USDT",
                target_token="BTC",
                expected_deltas={self.perp_instrument: -btc_position},  # Close position
                execution_mode="sequential",
                strategy_intent="exit_full",
                strategy_id="ml_btc_directional",
                metadata={"close_position": True, "original_position": btc_position},
            )

            return [order]

        except Exception as e:
            logger.error(f"Error creating exit full orders: {e}")
            return []

    def _create_exit_partial_orders(self, equity_delta: float) -> List[Order]:
        """
        Create exit partial orders for ML BTC directional strategy.

        Args:
            equity_delta: Equity to remove from position

        Returns:
            List of Order objects for partial exit
        """
        try:
            # Get current position to determine close side
            current_position = self.position_monitor.get_current_position()
            btc_position = current_position.get("btc_perp_position", 0.0)

            if btc_position == 0:
                return []  # No position to close

            # Calculate partial exit amount
            partial_exit = equity_delta * self.max_position_size
            partial_exit = min(partial_exit, abs(btc_position))  # Don't exceed current position

            # Determine close side based on current position
            close_side = "SELL" if btc_position > 0 else "BUY"

            # Create close position order
            operation_id = f"perp_close_partial_{int(pd.Timestamp.now().timestamp() * 1000000)}"
            order = Order(
                operation_id=operation_id,
                venue=Venue.BINANCE,
                operation=OrderOperation.PERP_TRADE,
                pair="BTCUSDT",
                side=close_side,
                amount=partial_exit,
                order_type="market",
                source_venue=Venue.BINANCE,
                target_venue=Venue.BINANCE,
                source_token="USDT",
                target_token="BTC",
                expected_deltas={
                    self.perp_instrument: -partial_exit if btc_position > 0 else partial_exit
                },
                execution_mode="sequential",
                strategy_intent="exit_partial",
                strategy_id="ml_btc_directional",
                metadata={
                    "close_position": True,
                    "partial_exit": True,
                    "original_position": btc_position,
                },
            )

            return [order]

        except Exception as e:
            logger.error(f"Error creating exit partial orders: {e}")
            return []

    def generate_orders(
        self,
        timestamp: pd.Timestamp,
        exposure: Dict,
        risk_assessment: Dict,
        pnl: Dict,
        market_data: Dict,
    ) -> List[Order]:
        """
        Generate orders for ML BTC directional strategy based on market conditions and ML predictions.

        Args:
            timestamp: Current timestamp
            exposure: Current exposure data
            risk_assessment: Risk assessment data
            pnl: Current PnL data (deprecated)
            market_data: Current market data

        Returns:
            List of Order objects to execute
        """
        try:
            # Log strategy decision start
            self.logger.info("Making ML BTC directional strategy decision")

            # Get current equity and positions
            current_equity = exposure.get("total_exposure", 0.0)
            current_positions = exposure.get("positions", {})

            # Get ML predictions from data provider
            ml_predictions = self._get_ml_predictions(market_data)

            # BTC-specific market analysis
            btc_price = market_data.get("prices", {}).get("BTC", 0.0)
            btc_perp_price = market_data.get("prices", {}).get("BTC_PERP", 0.0)

            # Risk assessment
            liquidation_risk = risk_assessment.get("liquidation_risk", 0.0)
            margin_ratio = risk_assessment.get("cex_margin_ratio", 1.0)

            # ML BTC Directional Strategy Decision Logic
            if ml_predictions is None:
                # No ML predictions available - maintain current position
                return self._create_dust_sell_orders({})

            # Check risk management first
            if self._should_exit_for_risk_management(btc_price, current_positions, ml_predictions):
                return self._create_exit_full_orders(current_equity)

            # Check ML signal for entry/exit
            if ml_predictions["confidence"] > self.signal_threshold:
                signal = ml_predictions["signal"]

                if signal == "long" and not self._has_long_position(current_positions):
                    # Enter long position
                    return self._create_entry_full_orders(current_equity, signal)
                elif signal == "short" and not self._has_short_position(current_positions):
                    # Enter short position
                    return self._create_entry_full_orders(current_equity, signal)
                elif signal == "exit" and (
                    self._has_long_position(current_positions)
                    or self._has_short_position(current_positions)
                ):
                    # Exit current position
                    return self._create_exit_full_orders(current_equity)
            else:
                # Low confidence - maintain current position or exit if risk is high
                if liquidation_risk > 0.8:  # High liquidation risk
                    return self._create_exit_full_orders(current_equity)
                else:
                    # Maintain current position
                    return self._create_dust_sell_orders({})

            # Default: maintain current position
            return self._create_dust_sell_orders({})

        except Exception as e:
            logger.error(f"Error in ML BTC directional strategy decision: {e}")
            return []

    def _create_dust_sell_orders(self, dust_tokens: Dict[str, float]) -> List[Order]:
        """
        Create dust sell orders for ML BTC directional strategy.

        Args:
            dust_tokens: Dictionary of dust tokens and amounts

        Returns:
            List of Order objects for dust selling
        """
        try:
            orders = []

            for token, amount in dust_tokens.items():
                if amount > 0 and token != "USDT":  # USDT is the target asset for USDT margin
                    # Sell dust tokens for USDT
                    operation_id = (
                        f"dust_sell_{token}_{int(pd.Timestamp.now().timestamp() * 1000000)}"
                    )
                    orders.append(
                        Order(
                            operation_id=operation_id,
                            venue=Venue.BINANCE,
                            operation=OrderOperation.SPOT_TRADE,
                            pair=f"{token}/USDT",
                            side="SELL",
                            amount=amount,
                            source_venue=Venue.BINANCE,
                            target_venue=Venue.BINANCE,
                            source_token=token,
                            target_token="USDT",
                            expected_deltas={
                                f"{Venue.BINANCE.value}:BaseToken:{token}": -amount,
                                f"{Venue.BINANCE.value}:BaseToken:USDT": amount
                                * 0.99,  # Assume 1% slippage
                            },
                            execution_mode="sequential",
                            strategy_intent="sell_dust",
                            strategy_id="ml_btc_directional",
                        )
                    )

            return orders

        except Exception as e:
            logger.error(f"Error creating dust sell orders: {e}")
            return []

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get ML BTC directional strategy information and status.

        Returns:
            Dictionary with strategy information
        """
        try:
            base_info = super().get_strategy_info()

            # Add ML BTC directional-specific information
            base_info.update(
                {
                    "strategy_type": "ml_btc_directional",
                    "signal_threshold": self.signal_threshold,
                    "max_position_size": self.max_position_size,
                    "stop_loss_pct": self.stop_loss_pct,
                    "take_profit_pct": self.take_profit_pct,
                    "description": "ML-driven directional BTC trading with 5-minute signals using unified_order_trade system",
                    "order_system": "unified_order_trade",
                    "risk_management": "take_profit_stop_loss",
                }
            )

            return base_info

        except Exception as e:
            logger.error(f"Error getting strategy info: {e}")
            return {
                "strategy_type": "ml_btc_directional",
                "mode": self.mode,
                "share_class": self.share_class,
                "asset": self.delta_tracking_asset,
                "equity": 0.0,
                "error": str(e),
            }
