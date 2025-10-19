"""
Pure Lending Strategy Implementation

This module implements the pure lending strategy using the base strategy manager
architecture with standardized 5-action interface.

Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
Reference: docs/STRATEGY_MODES.md - Pure Lending Strategy
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


class PureLendingETHStrategy(BaseStrategyManager):
    """Pure lending strategy implementation"""

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
        Initialize pure lending strategy.

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

        # Pure lending specific configuration
        self.lending_protocol = config.get("lending_protocol", "aave_v3")
        self.share_class = config.get("share_class", "ETH")  # Share class currency

        # For pure lending, allocate 100% to ETH
        self.eth_allocation = 1.0

        # Define and validate instrument keys
        self.entry_instrument = f"{Venue.WALLET.value}:BaseToken:ETH"
        self.lending_instrument = f"{Venue.AAVE_V3.value}:aToken:aWETH"

        # Validate instrument keys
        validate_instrument_key(self.entry_instrument)
        validate_instrument_key(self.lending_instrument)

        # Get available instruments from position_monitor config
        position_config = config.get("component_config", {}).get("position_monitor", {})
        self.available_instruments = position_config.get("position_subscriptions", [])

        if not self.available_instruments:
            raise ValueError(
                f"{self.__class__.__name__} requires position_subscriptions in config. "
                "Define all instruments this strategy will use in component_config.position_monitor.position_subscriptions"
            )

        # Define required instruments for this strategy
        required_instruments = [self.entry_instrument, self.lending_instrument]

        # Validate all required instruments are in available set
        for instrument in required_instruments:
            if instrument not in self.available_instruments:
                raise ValueError(
                    f"Required instrument {instrument} not in position_subscriptions. "
                    f"Add to configs/modes/{config.get('mode', 'pure_lending_eth')}.yaml"
                )

        # Pure lending doesn't use LTV (no borrowing/leverage)
        # LTV values are not applicable for pure lending strategies

        self.delta_tracking_asset = (
            config.get("component_config", {})
            .get("risk_monitor", {})
            .get("delta_tracking_asset", "ETH")
        )

        # Define lending venues for this strategy
        self.lending_venues = ["aave_v3"]  # AAVE only for pure lending

        self.logger.info(f"PureLendingETHStrategy initialized for {self.delta_tracking_asset}")
        self.logger.info(f"  Available instruments: {len(self.available_instruments)}")
        self.logger.info(f"  Entry: {get_display_name(self.entry_instrument)}")
        self.logger.info(f"  Lending: {get_display_name(self.lending_instrument)}")

    def _get_asset_price(self) -> float:
        """Get current ETH price for testing."""
        # In real implementation, this would get actual price from market data
        return 3000.0  # Mock ETH price

    def generate_orders(
        self,
        timestamp: pd.Timestamp,
        exposure: Dict,
        risk_assessment: Dict,
        market_data: Dict,
    ) -> List[Order]:
        """
        Generate orders for pure lending strategy.

        Note: pnl parameter is deprecated and unused.

        Pure Lending Strategy Logic:
        - Simple lending strategy - just supply USDT to AAVE
        - No complex trading decisions
        - Focus on maintaining lending position and managing risk
        """
        try:
            # Log strategy decision start
            self.logger.info(
                "Generating pure lending ETH strategy orders",
                strategy_type=self.__class__.__name__,
                timestamp=str(timestamp),
            )

            # Get current equity and positions
            current_equity = self.get_current_equity(exposure)
            current_positions = exposure.get("positions", {})

            # Pure lending strategy with position deviation logic
            # Check if we have ETH to lend and if position needs rebalancing

            # Get current lending positions
            current_lending = 0.0
            for venue in self.lending_venues:
                current_lending += current_positions.get(f"{venue}_eth_supply", 0.0)

            # Calculate target position
            target_position = self.calculate_target_position(current_equity)
            target_lending = target_position["supply"]

            # Calculate position deviation
            if target_lending > 0:
                position_deviation = abs(current_lending - target_lending) / target_lending
            else:
                position_deviation = 0.0

            # Get position deviation threshold from config
            deviation_threshold = self.strategy_config.get(
                "position_deviation_threshold", 0.02
            )  # 2% default

            # Pure Lending Strategy Decision Logic
            if current_equity == 0:
                # No equity - just handle dust
                return self._create_dust_sell_orders(exposure)

            elif current_equity > 0 and current_lending == 0:
                # Have equity but not lending - enter full position
                return self._create_entry_full_orders(current_equity)

            elif current_equity > 0 and position_deviation > deviation_threshold:
                # Position deviation too high - rebalance
                if current_lending < target_lending:
                    # Need to increase lending
                    return self._create_entry_partial_orders(target_lending - current_lending)
                else:
                    # Need to decrease lending
                    return self._create_exit_partial_orders(current_lending - target_lending)

            else:
                # Position is within tolerance - just handle dust
                return self._create_dust_sell_orders(exposure)

        except Exception as e:
            self.logger.error(
                "Error in pure lending ETH strategy order generation",
                error_code="STRAT-001",
                exc_info=e,
                method="generate_orders",
                strategy_type=self.__class__.__name__,
            )
            # Return safe default action
            return self._create_dust_sell_orders(exposure)

    def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
        """Calculate target position based on current equity"""
        try:
            # For pure lending, no borrowing - just supply the full equity
            target_supply = current_equity
            target_borrow = 0.0  # No borrowing in pure lending

            return {"supply": target_supply, "borrow": target_borrow, "equity": current_equity}
        except Exception as e:
            logger.error(f"Failed to calculate target position: {e}")
            return {"supply": 0.0, "borrow": 0.0, "equity": current_equity}

    def _create_entry_full_orders(self, equity: float) -> List[Order]:
        """Create orders for full position entry (initial setup or large deposits)"""
        try:
            # Log action start
            self.logger.info(
                f"Creating entry_full orders with equity={equity}",
                action="entry_full",
                equity=equity,
                strategy_type=self.__class__.__name__,
            )

            target_position = self.calculate_target_position(equity)
            orders = []

            # Create supply orders for each lending venue
            for venue in self.lending_venues:
                supply_amount = target_position["supply"] / len(self.lending_venues)
                if supply_amount > 0:
                    # Generate unique operation ID
                    operation_id = f"supply_{uuid.uuid4().hex[:8]}"

                    # Calculate expected deltas for supply operation
                    expected_deltas = {
                        self.entry_instrument: -supply_amount,  # Lose ETH
                        self.lending_instrument: supply_amount,  # Gain aETH (1:1 for now, will be updated with AAVE index)
                    }

                    # Get AAVE supply index if available from utility_manager
                    operation_details = {}
                    if self.utility_manager and hasattr(
                        self.utility_manager, "_get_aave_supply_index"
                    ):
                        try:
                            supply_index = self.utility_manager._get_aave_supply_index(
                                self.delta_tracking_asset, pd.Timestamp.now()
                            )
                            expected_deltas[self.lending_instrument] = supply_amount * supply_index
                            operation_details["aave_supply_index"] = supply_index
                        except Exception as e:
                            self.logger.warning(f"Failed to get AAVE supply index: {e}")

                    orders.append(
                        Order(
                            operation_id=operation_id,
                            venue=venue,
                            operation=OrderOperation.SUPPLY,
                            source_venue="wallet",
                            target_venue=venue,
                            source_token=self.delta_tracking_asset,
                            target_token=f"a{self.delta_tracking_asset}",
                            token_in=self.delta_tracking_asset,
                            token_out=f"a{self.delta_tracking_asset}",
                            amount=supply_amount,
                            expected_deltas=expected_deltas,
                            operation_details=operation_details,
                            execution_mode="sequential",
                            strategy_intent="entry_full",
                        )
                    )

            return orders

        except Exception as e:
            logger.error(f"Failed to create entry_full orders: {e}")
            return []

    def _create_entry_partial_orders(self, equity_delta: float) -> List[Order]:
        """Create orders for partial position entry (small deposits or PnL gains)"""
        try:
            # Scale up proportionally
            target_position = self.calculate_target_position(equity_delta)
            orders = []

            for venue in self.lending_venues:
                supply_amount = target_position["supply"] / len(self.lending_venues)
                if supply_amount > 0:
                    # Generate unique operation ID
                    operation_id = f"supply_{uuid.uuid4().hex[:8]}"

                    # Calculate expected deltas for supply operation
                    expected_deltas = {
                        f"{venue}:BaseToken:{self.delta_tracking_asset}": -supply_amount,  # Lose ETH
                        f"{venue}:BaseToken:a{self.delta_tracking_asset}": supply_amount,  # Gain aETH
                    }

                    # Get AAVE supply index if available
                    operation_details = {}
                    if self.utility_manager and hasattr(
                        self.utility_manager, "_get_aave_supply_index"
                    ):
                        try:
                            supply_index = self.utility_manager._get_aave_supply_index(
                                self.delta_tracking_asset, pd.Timestamp.now()
                            )
                            expected_deltas[self.lending_instrument] = supply_amount * supply_index
                            operation_details["aave_supply_index"] = supply_index
                        except Exception as e:
                            self.logger.warning(f"Failed to get AAVE supply index: {e}")

                    orders.append(
                        Order(
                            operation_id=operation_id,
                            venue=venue,
                            operation=OrderOperation.SUPPLY,
                            source_venue="wallet",
                            target_venue=venue,
                            source_token=self.delta_tracking_asset,
                            target_token=f"a{self.delta_tracking_asset}",
                            token_in=self.delta_tracking_asset,
                            token_out=f"a{self.delta_tracking_asset}",
                            amount=supply_amount,
                            expected_deltas=expected_deltas,
                            operation_details=operation_details,
                            execution_mode="sequential",
                            strategy_intent="entry_partial",
                        )
                    )

            return orders

        except Exception as e:
            logger.error(f"Failed to create entry_partial orders: {e}")
            return []

    def _create_exit_full_orders(self, equity: float) -> List[Order]:
        """Create orders for full position exit (withdrawals or risk override)"""
        try:
            # Get current position to determine exit amounts
            position_snapshot = self.position_monitor.get_position_snapshot()
            current_supply = position_snapshot.get("total_supply", 0.0)
            current_borrow = position_snapshot.get("total_borrow", 0.0)

            orders = []
            for venue in self.lending_venues:
                # Withdraw supply
                withdraw_amount = current_supply / len(self.lending_venues)
                if withdraw_amount > 0:
                    # Generate unique operation ID
                    operation_id = f"withdraw_{uuid.uuid4().hex[:8]}"

                    # Calculate expected deltas for withdraw operation
                    expected_deltas = {
                        self.lending_instrument: -withdraw_amount,  # Lose aETH
                        self.entry_instrument: withdraw_amount,  # Gain ETH
                    }

                    # Get AAVE supply index if available
                    operation_details = {}
                    if self.utility_manager and hasattr(
                        self.utility_manager, "_get_aave_supply_index"
                    ):
                        try:
                            supply_index = self.utility_manager._get_aave_supply_index(
                                self.delta_tracking_asset, pd.Timestamp.now()
                            )
                            expected_deltas[self.entry_instrument] = withdraw_amount * supply_index
                            operation_details["aave_supply_index"] = supply_index
                        except Exception as e:
                            self.logger.warning(f"Failed to get AAVE supply index: {e}")

                    orders.append(
                        Order(
                            operation_id=operation_id,
                            venue=venue,
                            operation=OrderOperation.WITHDRAW,
                            source_venue=venue,
                            target_venue="wallet",
                            source_token=f"a{self.delta_tracking_asset}",
                            target_token=self.delta_tracking_asset,
                            token_in=f"a{self.delta_tracking_asset}",
                            token_out=self.delta_tracking_asset,
                            amount=withdraw_amount,
                            expected_deltas=expected_deltas,
                            operation_details=operation_details,
                            execution_mode="sequential",
                            strategy_intent="exit_full",
                        )
                    )

            return orders

        except Exception as e:
            logger.error(f"Failed to create exit_full orders: {e}")
            return []

    def _create_exit_partial_orders(self, equity_delta: float) -> List[Order]:
        """Create orders for partial position exit (small withdrawals or risk reduction)"""
        try:
            # Scale down proportionally
            target_position = self.calculate_target_position(equity_delta)
            orders = []

            for venue in self.lending_venues:
                withdraw_amount = target_position["supply"] / len(self.lending_venues)
                if withdraw_amount > 0:
                    # Generate unique operation ID
                    operation_id = f"withdraw_{uuid.uuid4().hex[:8]}"

                    # Calculate expected deltas for withdraw operation
                    expected_deltas = {
                        self.lending_instrument: -withdraw_amount,  # Lose aETH
                        self.entry_instrument: withdraw_amount,  # Gain ETH
                    }

                    # Get AAVE supply index if available
                    operation_details = {}
                    if self.utility_manager and hasattr(
                        self.utility_manager, "_get_aave_supply_index"
                    ):
                        try:
                            supply_index = self.utility_manager._get_aave_supply_index(
                                self.delta_tracking_asset, pd.Timestamp.now()
                            )
                            expected_deltas[self.entry_instrument] = withdraw_amount * supply_index
                            operation_details["aave_supply_index"] = supply_index
                        except Exception as e:
                            self.logger.warning(f"Failed to get AAVE supply index: {e}")

                    orders.append(
                        Order(
                            operation_id=operation_id,
                            venue=venue,
                            operation=OrderOperation.WITHDRAW,
                            source_venue=venue,
                            target_venue="wallet",
                            source_token=f"a{self.delta_tracking_asset}",
                            target_token=self.delta_tracking_asset,
                            token_in=f"a{self.delta_tracking_asset}",
                            token_out=self.delta_tracking_asset,
                            amount=withdraw_amount,
                            expected_deltas=expected_deltas,
                            operation_details=operation_details,
                            execution_mode="sequential",
                            strategy_intent="exit_partial",
                        )
                    )

            return orders

        except Exception as e:
            logger.error(f"Failed to create exit_partial orders: {e}")
            return []

    def _create_dust_sell_orders(self, exposure_data: Dict) -> List[Order]:
        """Create orders to convert non-share-class tokens to share class currency"""
        try:
            dust_tokens = self.get_dust_tokens(exposure_data)
            orders = []

            for token, amount in dust_tokens.items():
                if token != self.delta_tracking_asset and amount > 0:
                    # Generate unique operation ID
                    operation_id = f"swap_{uuid.uuid4().hex[:8]}"

                    # For dust selling, we'd typically use a DEX or CEX
                    # This is a simplified example - in practice you'd route to appropriate venue
                    venue = Venue.UNISWAP  # Example DEX venue

                    # Calculate expected deltas for swap operation (simplified - would need actual price)
                    dust_instrument = f"{Venue.WALLET.value}:BaseToken:{token}"
                    expected_deltas = {
                        dust_instrument: -amount,  # Lose source token
                        self.entry_instrument: amount,  # Gain target token (simplified 1:1)
                    }

                    # Operation details for swap
                    operation_details = {
                        "swap_type": "dust_cleanup",
                        "source_token": token,
                        "target_token": self.delta_tracking_asset,
                    }

                    orders.append(
                        Order(
                            operation_id=operation_id,
                            venue=venue,
                            operation=OrderOperation.SWAP,
                            source_venue="wallet",
                            target_venue=venue,
                            source_token=token,
                            target_token=self.delta_tracking_asset,
                            token_in=token,
                            token_out=self.delta_tracking_asset,
                            amount=amount,
                            expected_deltas=expected_deltas,
                            operation_details=operation_details,
                            execution_mode="sequential",
                            strategy_intent="sell_dust",
                        )
                    )

            return orders

        except Exception as e:
            logger.error(f"Failed to create dust sell orders: {e}")
            return []
