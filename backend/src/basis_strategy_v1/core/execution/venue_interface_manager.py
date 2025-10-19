"""
Venue Interface Manager

Routes Orders to execution interfaces only (not position interfaces).
No longer owns tight loop orchestration - PositionUpdateHandler is the only tight loop owner.

Reference: docs/specs/07_VENUE_INTERFACE_MANAGER.md
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 4
"""

import logging
import pandas as pd
import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from ..interfaces.venue_interface_factory import VenueInterfaceFactory
from ..interfaces.base_execution_interface import BaseExecutionInterface
from ...core.models.order import Order
from ...core.models.execution import ExecutionHandshake, ExecutionStatus

from ...core.errors.component_error import ComponentError

logger = logging.getLogger(__name__)

# Error codes for Venue Interface Manager
ERROR_CODES = {
    "VIM-001": "Venue routing failed",
    "VIM-002": "Unsupported instruction type",
    "VIM-003": "Venue interface not available",
    "VIM-004": "Credential validation failed",
    "VIM-005": "Venue interface initialization failed",
    "VIM-006": "Atomic chaining failed",
    "VIM-007": "Venue instruction execution failed",
    "VIM-008": "Position update failed",
    "VIM-009": "Reconciliation failed",
    "VIM-010": "Error handling failed",
    "VIM-011": "Venue interface dependency injection failed",
    "VIM-012": "Instruction validation failed",
    "VIM-013": "Venue routing failed",
}


class VenueInterfaceManager:
    """
    Routes Orders to execution interfaces only (not position interfaces).
    No longer owns tight loop orchestration.
    """

    def __init__(self, config: Dict[str, Any], data_provider, venue_interface_factory, correlation_id: str = None, pid: int = None, log_dir: Path = None):
        """
        Initialize venue interface manager.

        Args:
            config: Configuration dictionary (reference, never modified)
            data_provider: Data provider instance (reference)
            venue_interface_factory: Venue interface factory instance
            correlation_id: Optional correlation ID for this run
            pid: Optional process ID for this run
            log_dir: Optional log directory path
        """
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.venue_interface_factory = venue_interface_factory
        self.execution_mode = config.get("execution_mode", "backtest")

        # Initialize logging infrastructure
        self.correlation_id = correlation_id or str(uuid.uuid4().hex)
        self.pid = pid or os.getpid()
        self.log_dir = log_dir

        # Initialize structured logger
        from ...infrastructure.logging.structured_logger import StructuredLogger
        self.logger = StructuredLogger(
            component_name="VenueInterfaceManager",
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
            engine=None
        )

        # Health integration
        self.health_status = {
            "status": "healthy",
            "last_check": datetime.now(),
            "error_count": 0,
            "success_count": 0,
        }

        # Initialize venue credentials
        self._initialize_venue_credentials()

        # Initialize venue interfaces with credentials
        self.venue_interfaces = self._initialize_venue_interfaces()

        # Initialize component-specific state
        self.current_instruction = None
        self.routing_history = []
        self.instructions_routed = 0
        self.instructions_failed = 0
        self.instructions_succeeded = 0

        self.logger.info(f"VenueInterfaceManager initialized in {self.execution_mode} mode")

    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.health_status["error_count"] += 1
        error_code = f"VIM_ERROR_{self.health_status['error_count']:04d}"

        logger.error(
            f"Venue Interface Manager error {error_code}: {str(error)}",
            extra={
                "error_code": error_code,
                "context": context,
                "execution_mode": self.execution_mode,
                "component": self.__class__.__name__,
            },
        )

        # Update health status based on error count
        if self.health_status["error_count"] > 10:
            self.health_status["status"] = "unhealthy"
        elif self.health_status["error_count"] > 5:
            self.health_status["status"] = "degraded"

    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            "status": self.health_status["status"],
            "error_count": self.health_status["error_count"],
            "success_count": self.health_status["success_count"],
            "execution_mode": self.execution_mode,
            "instructions_routed": self.instructions_routed,
            "instructions_succeeded": self.instructions_succeeded,
            "component": self.__class__.__name__,
        }

    def _process_config_driven_operations(self, operations: List[Dict]) -> List[Dict]:
        """Process operations based on configuration settings."""
        processed_operations = []
        for operation in operations:
            if self._validate_operation(operation):
                processed_operations.append(operation)
            else:
                self._handle_error(
                    ValueError(f"Invalid operation: {operation}"), "config_driven_validation"
                )
        return processed_operations

    def _validate_operation(self, operation: Dict) -> bool:
        """Validate operation against configuration."""
        required_fields = ["action", "venue", "instruction"]
        return all(field in operation for field in required_fields)

    def _initialize_venue_credentials(self):
        """Initialize venue credentials based on environment."""
        self.venue_credentials = {}

        # Get environment from config or environment variable
        environment = self.config.get("environment", "dev")

        # Initialize credentials for each venue type
        self.venue_credentials["cex"] = self._get_cex_credentials(environment)
        self.venue_credentials["onchain"] = self._get_onchain_credentials(environment)
        self.venue_credentials["transfer"] = self._get_transfer_credentials(environment)

        logger.info(f"Initialized venue credentials for environment: {environment}")

    def _get_cex_credentials(self, environment: str) -> Dict[str, Any]:
        """Get CEX credentials for the given environment."""
        credentials = {}

        # Get CEX venues from config
        cex_venues = (
            self.config.get("component_config", {})
            .get("execution_interfaces", {})
            .get("CEX_VENUES", [])
        )

        for venue in cex_venues:
            venue_config = self.config.get("venue_config", {}).get(venue, {})
            credentials[venue] = {
                "api_key": venue_config.get(f"{environment}_api_key"),
                "secret_key": venue_config.get(f"{environment}_secret_key"),
                "testnet": venue_config.get("testnet", False),
            }

        return credentials

    def _get_onchain_credentials(self, environment: str) -> Dict[str, Any]:
        """Get OnChain credentials for the given environment."""
        credentials = {}

        # Get OnChain protocols from config
        onchain_protocols = (
            self.config.get("component_config", {})
            .get("execution_interfaces", {})
            .get("ONCHAIN_PROTOCOLS", [])
        )

        for protocol in onchain_protocols:
            protocol_config = self.config.get("venue_config", {}).get(protocol, {})
            credentials[protocol] = {
                "rpc_url": protocol_config.get(f"{environment}_rpc_url"),
                "private_key": protocol_config.get(f"{environment}_private_key"),
                "contract_address": protocol_config.get("contract_address"),
            }

        return credentials

    def _get_transfer_credentials(self, environment: str) -> Dict[str, Any]:
        """Get transfer credentials for the given environment."""
        credentials = {}

        # Get transfer types from config
        transfer_types = (
            self.config.get("component_config", {})
            .get("execution_interfaces", {})
            .get("transfer_types", [])
        )

        for transfer_type in transfer_types:
            transfer_config = self.config.get("venue_config", {}).get(transfer_type, {})
            credentials[transfer_type] = {
                "wallet_address": transfer_config.get(f"{environment}_wallet_address"),
                "private_key": transfer_config.get(f"{environment}_private_key"),
            }

        return credentials

    def _initialize_venue_interfaces(self) -> Dict[str, BaseExecutionInterface]:
        """Initialize venue interfaces with credentials."""
        interfaces = {}

        try:
            # Create CEX venue interfaces
            for venue, credentials in self.venue_credentials["cex"].items():
                if credentials.get("api_key") and credentials.get("secret_key"):
                    interfaces[f"cex_{venue}"] = VenueInterfaceFactory.create_venue_interface(
                        "cex", self.execution_mode, self.config, self.data_provider
                    )
                    self.logger.info(f"Created CEX venue interface for {venue}")

        except Exception as e:
            self.logger.error(f"Failed to create CEX venue interfaces: {e}")

        try:
            # Create OnChain venue interfaces
            for protocol, credentials in self.venue_credentials["onchain"].items():
                if credentials.get("rpc_url") and credentials.get("private_key"):
                    interfaces[
                        f"onchain_{protocol}"
                    ] = VenueInterfaceFactory.create_venue_interface(
                        "onchain", self.execution_mode, self.config, self.data_provider
                    )
                    self.logger.info(f"Created OnChain venue interface for {protocol}")

        except Exception as e:
            self.logger.error(f"Failed to create OnChain venue interfaces: {e}")

        # Create AAVE v3 backtest interface for pure lending strategies
        try:
            if self.execution_mode == "backtest":
                from ..interfaces.aave_backtest_execution_interface import AaveBacktestExecutionInterface
                interfaces["onchain_aave_v3"] = AaveBacktestExecutionInterface(
                    self.execution_mode, self.config, self.data_provider
                )
                self.logger.info("Created AAVE v3 backtest execution interface")
        except Exception as e:
            self.logger.error(f"Failed to create AAVE v3 backtest interface: {e}")

        try:
            # Create transfer venue interfaces
            for transfer_type, credentials in self.venue_credentials["transfer"].items():
                if credentials.get("wallet_address") and credentials.get("private_key"):
                    interfaces[
                        f"transfer_{transfer_type}"
                    ] = VenueInterfaceFactory.create_venue_interface(
                        "transfer", self.execution_mode, self.config, self.data_provider
                    )
                    self.logger.info(f"Created transfer venue interface for {transfer_type}")

        except Exception as e:
            self.logger.error(f"Failed to create transfer venue interfaces: {e}")

        return interfaces

    def route_to_venue(self, timestamp: pd.Timestamp, order: Order) -> ExecutionHandshake:
        """
        Route Order to appropriate execution interface.

        Args:
            order: Order object containing order details

        Returns:
            ExecutionHandshake: Execution result from venue
        """
        try:
            # Route to appropriate execution interface based on operation
            if order.operation == "transfer":
                return self._route_to_transfer(order)
            elif order.operation in ["supply", "borrow", "repay", "withdraw", "stake", "unstake"]:
                return self._route_to_onchain(order, timestamp)
            elif order.operation in ["spot_trade", "perp_trade"]:
                return self._route_to_cex(order)
            else:
                raise ValueError(f"Unknown order operation: {order.operation}")

        except Exception as e:
            self.instructions_failed += 1
            logger.error(f"Venue routing failed: {e}")
            # Return a failed ExecutionHandshake instead of raising
            return ExecutionHandshake(
                operation_id=order.operation_id,
                status=ExecutionStatus.FAILED,
                actual_deltas={},
                execution_details={},
                error_code="VEN-001",
                error_message=str(e),
                submitted_at=datetime.now(),
                simulated=self.execution_mode == "backtest",
            )

    def _route_to_transfer(self, order: Order) -> ExecutionHandshake:
        """Route wallet transfer order to transfer execution interface."""
        try:
            # Get transfer execution interface
            transfer_interface = self.venue_interfaces.get("transfer_wallet")
            if not transfer_interface:
                raise ValueError("Transfer execution interface not available")

            # Execute transfer
            result = transfer_interface.execute_transfer(order)

            # Update routing history
            self.routing_history.append(
                {
                    "timestamp": datetime.now(),
                    "order_type": "transfer",
                    "venue": order.venue,
                    "result": result,
                }
            )

            self.instructions_routed += 1
            self.instructions_succeeded += 1

            return result

        except Exception as e:
            self.instructions_failed += 1
            logger.error(f"Transfer routing failed: {e}")
            return ExecutionHandshake(
                operation_id=order.operation_id,
                status=ExecutionStatus.FAILED,
                actual_deltas={},
                execution_details={},
                error_code="VEN-001",
                error_message=str(e),
                submitted_at=datetime.now(),
                simulated=self.execution_mode == "backtest",
            )

    def _route_to_onchain(self, order: Order, timestamp: pd.Timestamp) -> ExecutionHandshake:
        """Route smart contract action order to onchain execution interface."""
        try:
            # Get onchain execution interface
            interface_key = f"onchain_{order.venue}"
            onchain_interface = self.venue_interfaces.get(interface_key)
            if not onchain_interface:
                raise ValueError(
                    f"OnChain execution interface not available for venue: {order.venue}"
                )

            # Execute smart contract action based on operation
            operation_str = order.operation.value if hasattr(order.operation, 'value') else str(order.operation)
            if operation_str == "supply":
                result = onchain_interface.execute_supply(order, timestamp)
            elif operation_str == "borrow":
                result = onchain_interface.execute_borrow(order)
            elif operation_str == "stake":
                result = onchain_interface.execute_stake(order)
            elif operation_str == "unstake":
                result = onchain_interface.execute_unstake(order)
            else:
                result = onchain_interface.execute_trade(order)

            # Update routing history
            self.routing_history.append(
                {
                    "timestamp": datetime.now(),
                    "order_type": "onchain",
                    "venue": order.venue,
                    "operation": order.operation.value if hasattr(order.operation, 'value') else str(order.operation),
                    "result": result,
                }
            )

            self.instructions_routed += 1
            self.instructions_succeeded += 1

            return result

        except Exception as e:
            self.instructions_failed += 1
            logger.error(f"OnChain routing failed: {e}")
            return ExecutionHandshake(
                operation_id=order.operation_id,
                status=ExecutionStatus.FAILED,
                actual_deltas={},
                execution_details={},
                error_code="VEN-002",
                error_message=str(e),
                submitted_at=datetime.now(),
                simulated=self.execution_mode == "backtest",
            )

    def _route_to_cex(self, order: Order) -> ExecutionHandshake:
        """Route CEX trade order to CEX execution interface."""
        try:
            # Get CEX execution interface
            interface_key = f"cex_{order.venue}"
            cex_interface = self.venue_interfaces.get(interface_key)
            if not cex_interface:
                raise ValueError(f"CEX execution interface not available for venue: {order.venue}")

            # Execute CEX trade based on operation
            operation_str = order.operation.value if hasattr(order.operation, 'value') else str(order.operation)
            if operation_str == "spot_trade":
                result = cex_interface.execute_spot_trade(order)
            elif operation_str == "perp_trade":
                result = cex_interface.execute_perp_trade(order)
            else:
                result = cex_interface.execute_trade(order)

            # Update routing history
            self.routing_history.append(
                {
                    "timestamp": datetime.now(),
                    "order_type": "cex",
                    "venue": order.venue,
                    "operation": order.operation.value if hasattr(order.operation, 'value') else str(order.operation),
                    "result": result,
                }
            )

            self.instructions_routed += 1
            self.instructions_succeeded += 1

            return result

        except Exception as e:
            self.instructions_failed += 1
            logger.error(f"CEX routing failed: {e}")
            return ExecutionHandshake(
                operation_id=order.operation_id,
                status=ExecutionStatus.FAILED,
                actual_deltas={},
                execution_details={},
                error_code="VEN-003",
                error_message=str(e),
                submitted_at=datetime.now(),
                simulated=self.execution_mode == "backtest",
            )

    def _get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        return {
            "instructions_routed": self.instructions_routed,
            "instructions_succeeded": self.instructions_succeeded,
            "instructions_failed": self.instructions_failed,
            "success_rate": self.instructions_succeeded / max(self.instructions_routed, 1),
            "available_interfaces": list(self.venue_interfaces.keys()),
            "routing_history_count": len(self.routing_history),
        }

    def _set_dependencies(self, position_monitor, event_logger, data_provider):
        """Set dependencies for all venue interfaces."""
        for interface in self.venue_interfaces.values():
            if hasattr(interface, "set_dependencies"):
                interface.set_dependencies(position_monitor, event_logger, data_provider)

        logger.info("Set dependencies for all venue interfaces")

    def update_state(
        self, timestamp: pd.Timestamp, trigger_source: str, order: Optional[Dict] = None
    ) -> Dict:
        """
        Main entry point for order routing.

        Args:
            timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
            trigger_source: 'execution_manager' | 'manual' | 'retry'
            order: Dict (optional) - order from Venue Manager

        Returns:
            Dict: Trade result
        """
        try:
            logger.info(f"VenueInterfaceManager: Updating state from {trigger_source}")

            if order:
                return self.route_to_venue(timestamp, order)
            else:
                return {"success": True, "message": "No order to process"}

        except Exception as e:
            logger.error(f"VenueInterfaceManager: Error in update_state: {e}")
            return {"success": False, "error": str(e), "trigger_source": trigger_source}
