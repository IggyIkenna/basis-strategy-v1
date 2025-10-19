"""
Base Execution Interface

Abstract base class for all execution interfaces.
Defines the contract that all execution implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from datetime import datetime, timezone
import logging

from ...core.models.order import Order
from ...core.models.execution import ExecutionHandshake

logger = logging.getLogger(__name__)


class BaseExecutionInterface(ABC):
    """
    Abstract base class for execution interfaces.

    Provides the contract that all execution implementations must follow,
    enabling seamless switching between backtest and live modes.
    """

    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        """
        Initialize execution interface.

        Args:
            execution_mode: 'backtest' or 'live'
            config: Configuration dictionary
        """
        self.execution_mode = execution_mode
        self.config = config
        self.position_monitor = None
        self.event_logger = None
        self.data_provider = None
        self.health_status = "healthy"
        self.error_count = 0

        logger.info(f"{self.__class__.__name__} initialized in {execution_mode} mode")

    def set_dependencies(self, position_monitor, event_logger, data_provider):
        """Set component dependencies."""
        self.position_monitor = position_monitor
        self.event_logger = event_logger
        self.data_provider = data_provider

    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.error_count += 1
        error_code = f"EXECUTION_ERROR_{self.error_count:04d}"

        logger.error(
            f"Execution error {error_code}: {str(error)}",
            extra={
                "error_code": error_code,
                "context": context,
                "execution_mode": self.execution_mode,
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
            "execution_mode": self.execution_mode,
            "component": self.__class__.__name__,
        }

    def _process_config_driven_operations(
        self, operations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process operations based on configuration settings."""
        processed_operations = []

        for operation in operations:
            try:
                # Apply config-driven logic
                if self.config.get("enable_validation", True):
                    # Validate operation based on config
                    if self._validate_operation(operation):
                        processed_operations.append(operation)
                    else:
                        logger.warning(f"Operation validation failed: {operation}")
                else:
                    processed_operations.append(operation)

            except Exception as e:
                self._handle_error(e, f"config_driven_operation_processing")

        return processed_operations

    def _validate_operation(self, operation: Dict[str, Any]) -> bool:
        """Validate operation based on configuration."""
        # Basic validation logic
        required_fields = self.config.get("required_operation_fields", ["type", "amount"])
        return all(field in operation for field in required_fields)

    @abstractmethod
    def execute_trade(self, order: Order) -> ExecutionHandshake:
        """
        Execute a trade order.

        Args:
            order: Order object containing trade details

        Returns:
            ExecutionHandshake: Execution result
        """
        pass

    @abstractmethod
    def get_balance(self, asset: str, venue: Optional[str] = None) -> float:
        """
        Get current balance for an asset.

        Args:
            asset: Asset symbol (e.g., 'ETH', 'USDT')
            venue: Venue name (for CEX) or None (for on-chain)

        Returns:
            Current balance
        """
        pass

    @abstractmethod
    def get_position(self, symbol: str, venue: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current position for a trading pair.

        Args:
            symbol: Trading pair symbol (e.g., 'ETH/USDT', 'ETHUSDT-PERP')
            venue: Venue name (for CEX) or None (for on-chain)

        Returns:
            Position information dictionary
        """
        pass

    @abstractmethod
    def cancel_all_orders(self, venue: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel all open orders.

        Args:
            venue: Venue name (for CEX) or None (for on-chain)

        Returns:
            Cancellation result dictionary
        """
        pass

    @abstractmethod
    def execute_transfer(self, order: Order) -> ExecutionHandshake:
        """
        Execute a cross-venue transfer.

        Args:
            order: Order object containing transfer details

        Returns:
            ExecutionHandshake: Transfer execution result
        """
        pass

    @abstractmethod
    def execute_borrow(self, order: Order) -> ExecutionHandshake:
        """
        Execute borrow action on OnChain protocol.

        Args:
            order: Order object containing borrow details

        Returns:
            ExecutionHandshake: Borrow execution result
        """
        pass

    @abstractmethod
    def execute_spot_trade(self, order: Order) -> ExecutionHandshake:
        """
        Execute spot trade on CEX.

        Args:
            order: Order object containing spot trade details

        Returns:
            ExecutionHandshake: Spot trade execution result
        """
        pass

    @abstractmethod
    def execute_supply(self, order: Order) -> ExecutionHandshake:
        """
        Execute supply action on OnChain protocol.

        Args:
            order: Order object containing supply details

        Returns:
            ExecutionHandshake: Supply execution result
        """
        pass

    @abstractmethod
    def execute_perp_trade(self, order: Order) -> ExecutionHandshake:
        """
        Execute perpetual trade on CEX.

        Args:
            order: Order object containing perp trade details

        Returns:
            ExecutionHandshake: Perp trade execution result
        """
        pass

    @abstractmethod
    def execute_swap(self, order: Order) -> ExecutionHandshake:
        """
        Execute token swap on DEX.

        Args:
            order: Order object containing swap details

        Returns:
            ExecutionHandshake: Swap execution result
        """
        pass

    def update_state(
        self, timestamp: pd.Timestamp, trigger_source: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Update component state with new data.

        Args:
            timestamp: Current timestamp from EventDrivenStrategyEngine
            trigger_source: Source component that triggered this update
            **kwargs: Additional parameters specific to component

        Returns:
            State update result dictionary
        """
        try:
            logger.info(f"{self.__class__.__name__}: Updating state from {trigger_source}")

            # Update internal state if needed
            self._update_internal_state(timestamp, trigger_source, **kwargs)

            return {
                "status": "success",
                "timestamp": timestamp,
                "trigger_source": trigger_source,
                "component": self.__class__.__name__,
            }

        except Exception as e:
            logger.error(f"{self.__class__.__name__}: Error in update_state: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": timestamp,
                "trigger_source": trigger_source,
                "component": self.__class__.__name__,
            }

    def _update_internal_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs):
        """Update internal component state."""
        # Override in subclasses if needed
        pass

    def get_position_interfaces(
        self, venues: List[str], execution_mode: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create position monitoring interfaces for multiple venues.

        Args:
            venues: List of venue names
            execution_mode: Execution mode ('backtest' or 'live')
            config: Configuration dictionary

        Returns:
            Dictionary of venue name to position interface instance
        """
        from .venue_interface_factory import VenueInterfaceFactory

        return VenueInterfaceFactory.get_venue_position_interfaces(venues, execution_mode, config)

    def create_position_interface(
        self, venue: str, execution_mode: str, config: Dict[str, Any]
    ) -> Any:
        """
        Create position monitoring interface for specific venue.

        Args:
            venue: Venue name
            execution_mode: Execution mode ('backtest' or 'live')
            config: Configuration dictionary

        Returns:
            Position interface instance
        """
        from .venue_interface_factory import VenueInterfaceFactory

        return VenueInterfaceFactory.create_venue_position_interface(venue, execution_mode, config)

    def _log_execution_event(self, event_type: str, details: Dict[str, Any]):
        """Log execution event."""
        if self.event_logger:
            self.event_logger.log_event(
                event_type=event_type,
                details=details,
                timestamp=datetime.now(timezone.utc),
                venue=details.get("venue", "system"),
                token=details.get("token", None),
            )

    def _update_position_monitor(self, changes: Dict[str, Any]):
        """Update position monitor with execution changes."""
        if self.position_monitor:
            # Format changes for position monitor
            formatted_changes = self._format_changes_for_position_monitor(changes)
            self.position_monitor.update_state(
                changes.get("timestamp", pd.Timestamp.now()),
                "execution_interface",
                **formatted_changes,
            )

    def _format_changes_for_position_monitor(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Format execution changes for position monitor."""
        operation = changes.get("operation", "UNKNOWN")

        if operation == "AAVE_SUPPLY":
            # AAVE supply: USDT → aUSDT conversion
            token_in = changes.get("token_in", "USDT")
            token_out = changes.get("token_out", "aUSDT")
            amount_in = changes.get("amount_in", 0)
            amount_out = changes.get("amount_out", 0)
            gas_cost = changes.get("gas_cost", 0)

            return {
                "timestamp": pd.Timestamp.now(tz="UTC"),
                "trigger": "AAVE_SUPPLY",
                "token_changes": [
                    {
                        "venue": "WALLET",
                        "token": token_in,
                        "delta": -amount_in,  # Remove USDT
                        "reason": "AAVE_SUPPLY_INPUT",
                    },
                    {
                        "venue": "WALLET",
                        "token": token_out,
                        "delta": +amount_out,  # Add aUSDT
                        "reason": "AAVE_SUPPLY_OUTPUT",
                    },
                    {
                        "venue": "WALLET",
                        "token": "ETH",
                        "delta": -gas_cost,  # Gas fee
                        "reason": "GAS_FEE",
                    },
                ],
                "derivative_changes": [],
            }
        else:
            # Generic operation
            token = changes.get("token", "ETH")
            amount = changes.get("amount", 0)
            gas_cost = changes.get("gas_cost", 0)

            return {
                "timestamp": pd.Timestamp.now(tz="UTC"),
                "trigger": operation,
                "token_changes": [
                    {"venue": "WALLET", "token": token, "delta": amount, "reason": operation},
                    {"venue": "WALLET", "token": "ETH", "delta": -gas_cost, "reason": "GAS_FEE"},
                ],
                "derivative_changes": [],
            }

    def _get_execution_cost(
        self, instruction: Dict[str, Any], market_data: Dict[str, Any]
    ) -> float:
        """Get execution cost for instruction."""
        try:
            logger.debug(
                f"Base Interface: _get_execution_cost called with instruction type: {type(instruction)}"
            )
            logger.debug(
                f"Base Interface: instruction keys: {list(instruction.keys()) if hasattr(instruction, 'keys') else 'Not a dict'}"
            )

            if self.data_provider:
                pair = instruction.get("pair", "")
                amount = instruction.get("amount", 0)
                venue = instruction.get("venue", "")
                trade_type = instruction.get("trade_type", "SPOT")
                eth_price = market_data.get("eth_usd_price", 0)
                notional = amount * eth_price

                logger.debug(
                    f"Base Interface: Getting execution cost using canonical pattern for pair={pair}, notional={notional}, venue={venue}, trade_type={trade_type}"
                )

                # Get data using canonical pattern
                data = self.data_provider.get_data(market_data.get("timestamp"))
                execution_costs = data["execution_data"]["execution_costs"]

                # Look for the specific execution cost
                cost_key = f"{pair}_{venue}_{trade_type}"
                if cost_key in execution_costs:
                    return execution_costs[cost_key]
                elif pair in execution_costs:
                    return execution_costs[pair]
                else:
                    return 0.0  # Default if not found
            return 0.0

        except Exception as e:
            logger.error(f"Base Interface: _get_execution_cost failed: {e}")
            logger.error(f"Base Interface: instruction: {instruction}")
            logger.error(
                f"Base Interface: market_data keys: {list(market_data.keys()) if hasattr(market_data, 'keys') else 'Not a dict'}"
            )
            raise

    def _get_gas_cost(self, operation: str, market_data: Dict[str, Any]) -> float:
        """Get gas cost for operation using canonical pattern."""
        if self.utility_manager:
            timestamp = market_data.get("timestamp")
            if timestamp is None:
                # Use current timestamp if not provided
                timestamp = pd.Timestamp.now(tz="UTC")

            # Use utility_manager for canonical gas cost access
            return self.utility_manager.get_gas_cost(operation, timestamp)
        return 0.001  # Default 0.001 ETH
