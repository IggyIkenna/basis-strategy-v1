"""
Execution Manager Component - Order/ExecutionHandshake Processing

Processes List[Order] → List[ExecutionHandshake] through VenueInterfaceManager routing.
Orchestrates Order execution with reconciliation via PositionUpdateHandler.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 4
Reference: docs/specs/06_EXECUTION_MANAGER.md
"""

from typing import Dict, Any, List, Optional
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

from ...infrastructure.logging.structured_logger import StructuredLogger
from ...infrastructure.logging.domain_event_logger import DomainEventLogger
from ...core.errors.error_codes import ERROR_REGISTRY
from ...core.models.order import Order
from ...core.models.execution import ExecutionHandshake, ExecutionStatus
from ...core.models.domain_events import (
    OperationExecutionEvent,
    AtomicOperationGroupEvent,
    TightLoopExecutionEvent,
    ExecutionDeltaEvent,
)

logger = logging.getLogger(__name__)


class ExecutionManager:
    """Centralized execution manager for Order → ExecutionHandshake processing."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ExecutionManager, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        execution_mode: str,
        config: Dict[str, Any],
        venue_interface_manager=None,
        position_update_handler=None,
        data_provider=None,
        correlation_id: str = None,
        pid: int = None,
        log_dir: Path = None,
    ):
        """
        Initialize execution manager.

        Args:
            execution_mode: Execution mode ('backtest' or 'live')
            config: Configuration dictionary
            venue_interface_manager: Venue interface manager instance
            position_update_handler: Position update handler instance
            data_provider: Data provider instance
            correlation_id: Unique correlation ID for this run
            pid: Process ID
            log_dir: Log directory path (logs/{correlation_id}/{pid}/)
        """
        self.execution_mode = execution_mode
        self.config = config
        self.venue_interface_manager = venue_interface_manager
        self.position_update_handler = position_update_handler
        self.data_provider = data_provider

        # Get position subscriptions from config
        position_config = config.get("component_config", {}).get("position_monitor", {})
        self.position_subscriptions = position_config.get("position_subscriptions", [])

        logger.info(f"ExecutionManager subscribed to {len(self.position_subscriptions)} positions")

        # Initialize logging infrastructure
        self.correlation_id = correlation_id or "default"
        self.pid = pid or 0
        self.log_dir = log_dir or Path("logs/default/0")

        # Initialize structured logger
        self.logger = StructuredLogger(
            component_name=self.__class__.__name__,
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
        )

        # Initialize domain event logger
        self.domain_event_logger = DomainEventLogger(
            self.log_dir, 
            correlation_id=self.correlation_id, 
            pid=self.pid
        )

        # Execution configuration
        self.execution_timeout = (
            config.get("component_config", {})
            .get("execution_manager", {})
            .get("execution_timeout", 30)
        )
        self.max_retries = (
            config.get("component_config", {}).get("execution_manager", {}).get("max_retries", 3)
        )

        self.logger.info(f"ExecutionManager initialized in {execution_mode} mode")

    def process_orders(
        self, timestamp: pd.Timestamp, orders: List[Order]
    ) -> List[ExecutionHandshake]:
        """
        Process a list of orders and return execution handshakes.

        Args:
            timestamp: Current timestamp
            orders: List of orders to execute

        Returns:
            List[ExecutionHandshake]: List of execution results
        """
        try:
            self.logger.info(f"Processing {len(orders)} orders")

            if not orders:
                return []

            # Group orders by atomic groups
            atomic_groups = self._group_orders_by_atomic_id(orders)
            all_handshakes = []

            # Process each atomic group
            for atomic_group_id, group_orders in atomic_groups.items():
                if atomic_group_id:
                    # Process as atomic group
                    handshakes = self._process_atomic_group(
                        timestamp, group_orders, atomic_group_id
                    )
                else:
                    # Process individual orders
                    handshakes = []
                    for order in group_orders:
                        handshake = self._process_single_order(timestamp, order)
                        if handshake:
                            handshakes.append(handshake)

                all_handshakes.extend(handshakes)

            self.logger.info(
                f"Processed {len(orders)} orders, generated {len(all_handshakes)} handshakes"
            )
            return all_handshakes

        except Exception as e:
            self.logger.error(
                "Failed to process orders",
                error_code="EXEC-001",
                exc_info=e,
                orders_count=len(orders),
            )
            return []

    def _group_orders_by_atomic_id(self, orders: List[Order]) -> Dict[str, List[Order]]:
        """Group orders by atomic_group_id."""
        groups = {}

        for order in orders:
            atomic_id = order.atomic_group_id or "individual"
            if atomic_id not in groups:
                groups[atomic_id] = []
            groups[atomic_id].append(order)

        return groups

    def _process_single_order(
        self, timestamp: pd.Timestamp, order: Order
    ) -> Optional[ExecutionHandshake]:
        """Process a single order."""
        try:
            self.logger.info(f"Processing single order: {order.operation_id}")

            # Route to venue interface
            handshake = self.venue_interface_manager.route_to_venue(timestamp, order)

            if handshake:
                # Log operation execution event
                self._log_operation_execution(handshake, order, timestamp)

                # Log execution delta event
                self._log_execution_delta(handshake, order, timestamp)

                # Reconcile with position update handler
                reconciliation_success = self._reconcile_with_retry(timestamp, handshake, order)

                # Log tight loop execution event
                self._log_tight_loop_execution(order, handshake, reconciliation_success, timestamp)

            return handshake

        except Exception as e:
            self.logger.error(
                "Failed to process single order",
                error_code="EXEC-001",
                exc_info=e,
                order_id=order.operation_id,
            )
            return None

    def _process_atomic_group(
        self, timestamp: pd.Timestamp, orders: List[Order], atomic_group_id: str
    ) -> List[ExecutionHandshake]:
        """Process an atomic group of orders."""
        try:
            self.logger.info(
                f"Processing atomic group: {atomic_group_id} with {len(orders)} orders"
            )

            # Sort orders by sequence_in_group
            sorted_orders = sorted(orders, key=lambda o: o.sequence_in_group or 0)

            handshakes = []
            group_success = True

            # Process each order in sequence
            for order in sorted_orders:
                handshake = self._process_single_order(timestamp, order)
                if handshake:
                    handshakes.append(handshake)
                    if handshake.was_failed():
                        group_success = False
                        break
                else:
                    group_success = False
                    break

            # Log atomic group event
            self._log_atomic_group_execution(
                handshakes, orders, atomic_group_id, group_success, timestamp
            )

            return handshakes

        except Exception as e:
            self.logger.error(
                "Failed to process atomic group",
                error_code="EXEC-005",
                exc_info=e,
                atomic_group_id=atomic_group_id,
                orders_count=len(orders),
            )
            return []

    def _reconcile_with_retry(self, timestamp: pd.Timestamp, handshake: ExecutionHandshake, order: Order) -> bool:
        """Reconcile execution with position update handler."""
        try:
            if not self.position_update_handler:
                return True  # No reconciliation if no handler

            # Convert deltas to structured format
            structured_deltas = self._convert_deltas_to_structured_format(handshake.actual_deltas)

            # Attempt reconciliation with retries
            for attempt in range(self.max_retries):
                try:
                    # Call PositionUpdateHandler to apply execution deltas
                    result = self.position_update_handler._handle_execution_manager_trigger(
                        timestamp=timestamp, changes=structured_deltas
                    )
                    success = result.get('success', False)

                    if success:
                        return True

                    if attempt < self.max_retries - 1:
                        self.logger.warning(
                            f"Reconciliation attempt {attempt + 1} failed, retrying",
                            error_code="EXEC-003",
                            order_id=order.operation_id,
                            attempt=attempt + 1,
                        )

                except Exception as e:
                    self.logger.error(
                        f"Reconciliation attempt {attempt + 1} failed with exception",
                        error_code="EXEC-003",
                        exc_info=e,
                        order_id=order.operation_id,
                        attempt=attempt + 1,
                    )

            # All retries failed
            self.logger.error(
                "All reconciliation attempts failed",
                error_code="EXEC-003",
                order_id=order.operation_id,
                max_retries=self.max_retries,
            )
            return False

        except Exception as e:
            self.logger.error(
                "Failed to reconcile execution",
                error_code="EXEC-003",
                exc_info=e,
                order_id=order.operation_id,
            )
            return False

    def _convert_deltas_to_structured_format(
        self, deltas: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Convert simple deltas dict to structured format for reconciliation."""
        structured = []

        for instrument_key, delta_amount in deltas.items():
            structured.append(
                {
                    "instrument_key": instrument_key,
                    "delta_amount": delta_amount,
                    "source": "execution",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return structured

    def _log_operation_execution(
        self, handshake: ExecutionHandshake, order: Order, timestamp: pd.Timestamp
    ) -> None:
        """Log operation execution event."""
        try:
            # Convert deltas to structured format
            position_deltas = []
            for instrument_key, delta_amount in handshake.actual_deltas.items():
                position_deltas.append(
                    {
                        "instrument_key": instrument_key,
                        "delta_amount": delta_amount,
                        "source": order.operation.value if hasattr(order.operation, 'value') else str(order.operation),
                        "price": handshake.execution_details.get("executed_price", 0.0),
                        "fee": handshake.fee_amount,
                    }
                )

            # Create operation execution event
            event = OperationExecutionEvent(
                timestamp=timestamp.isoformat(),
                real_utc_time=datetime.now().isoformat(),
                correlation_id=self.correlation_id,
                pid=self.pid,
                operation_id=handshake.operation_id,
                order_id=order.operation_id,
                operation_type=order.operation.value if hasattr(order.operation, 'value') else str(order.operation),
                venue=order.venue,
                status=handshake.status.value if hasattr(handshake.status, 'value') else str(handshake.status),
                source_venue=order.source_venue,
                target_venue=order.target_venue,
                source_token=order.source_token,
                target_token=order.target_token,
                operation_details=order.operation_details,
                position_deltas=position_deltas,
                executed_amount=handshake.execution_details.get("executed_amount", order.amount),
                fee_amount=handshake.fee_amount,
                fee_currency=handshake.fee_currency,
                error_code=handshake.error_code,
                error_message=handshake.error_message,
                atomic_group_id=order.atomic_group_id,
                sequence_in_group=order.sequence_in_group,
                submitted_at=handshake.submitted_at,
                executed_at=handshake.executed_at,
                execution_time_ms=handshake.execution_details.get("execution_time_ms"),
                venue_metadata=handshake.venue_metadata,
                simulated=handshake.simulated,
                metadata={
                    "component": self.__class__.__name__,
                    "execution_mode": self.execution_mode,
                },
            )

            # Log the event
            self.domain_event_logger.log_operation_execution(event)

        except Exception as e:
            self.logger.error(
                "Failed to log operation execution",
                error_code="LOG-001",
                exc_info=e,
                operation_id=handshake.operation_id,
            )

    def _log_atomic_group_execution(
        self,
        handshakes: List[ExecutionHandshake],
        orders: List[Order],
        atomic_group_id: str,
        group_success: bool,
        timestamp: pd.Timestamp,
    ) -> None:
        """Log atomic group execution event."""
        try:
            # Create operation summaries
            operations = []
            for i, (handshake, order) in enumerate(zip(handshakes, orders)):
                operations.append(
                    {
                        "operation_id": handshake.operation_id,
                        "operation_type": order.operation.value if hasattr(order.operation, 'value') else str(order.operation),
                        "status": handshake.status.value if hasattr(handshake.status, 'value') else str(handshake.status),
                    }
                )

            # Calculate total gas fees (simplified)
            total_gas_fees = sum(h.fee_amount for h in handshakes)

            # Calculate execution time (simplified)
            execution_time_ms = sum(
                h.execution_details.get("execution_time_ms", 0) for h in handshakes
            )

            # Create atomic group event
            event = AtomicOperationGroupEvent(
                timestamp=timestamp.isoformat(),
                real_utc_time=datetime.now().isoformat(),
                correlation_id=self.correlation_id,
                pid=self.pid,
                atomic_group_id=atomic_group_id,
                total_operations=len(orders),
                operations=operations,
                group_status="completed" if group_success else "failed",
                total_gas_fees=total_gas_fees,
                execution_time_ms=execution_time_ms,
                rollback_triggered=not group_success,
                rollback_reason="Group execution failed" if not group_success else None,
                metadata={
                    "component": self.__class__.__name__,
                    "execution_mode": self.execution_mode,
                },
            )

            # Log the event
            self.domain_event_logger.log_atomic_group(event)

        except Exception as e:
            self.logger.error(
                "Failed to log atomic group execution",
                error_code="LOG-001",
                exc_info=e,
                atomic_group_id=atomic_group_id,
            )

    def _log_execution_delta(
        self, handshake: ExecutionHandshake, order: Order, timestamp: pd.Timestamp
    ) -> None:
        """Log execution delta event."""
        try:
            # Convert deltas to structured format
            deltas = []
            for instrument_key, delta_amount in handshake.actual_deltas.items():
                deltas.append(
                    {
                        "instrument_key": instrument_key,
                        "delta_amount": delta_amount,
                        "source": order.operation.value if hasattr(order.operation, 'value') else str(order.operation),
                        "price": handshake.execution_details.get("executed_price", 0.0),
                        "fee": handshake.fee_amount,
                    }
                )

            # Create execution delta event
            event = ExecutionDeltaEvent(
                timestamp=timestamp.isoformat(),
                real_utc_time=datetime.now().isoformat(),
                correlation_id=self.correlation_id,
                pid=self.pid,
                source_operation_id=handshake.operation_id,
                operation_type=order.operation.value if hasattr(order.operation, 'value') else str(order.operation),
                deltas=deltas,
                metadata={
                    "component": self.__class__.__name__,
                    "execution_mode": self.execution_mode,
                },
            )

            # Log the event
            self.domain_event_logger.log_execution_delta(event)

        except Exception as e:
            self.logger.error(
                "Failed to log execution delta",
                error_code="LOG-001",
                exc_info=e,
                operation_id=handshake.operation_id,
            )

    def _log_tight_loop_execution(
        self,
        order: Order,
        handshake: ExecutionHandshake,
        reconciliation_success: bool,
        timestamp: pd.Timestamp,
    ) -> None:
        """Log tight loop execution event."""
        try:
            # Calculate execution time (simplified)
            execution_time_ms = handshake.execution_details.get("execution_time_ms", 0)
            reconciliation_time_ms = 0  # Would need to track actual reconciliation time

            # Create tight loop execution event
            event = TightLoopExecutionEvent(
                timestamp=timestamp.isoformat(),
                real_utc_time=datetime.now().isoformat(),
                correlation_id=self.correlation_id,
                pid=self.pid,
                batch_id=f"batch_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                order_number=1,  # Would need to track order number in batch
                total_orders=1,  # Would need to track total orders in batch
                order_id=order.operation_id,
                operation_id=order.operation_id,
                execution_success=handshake.was_successful(),
                execution_status=handshake.status.value if hasattr(handshake.status, 'value') else str(handshake.status),
                reconciliation_success=reconciliation_success,
                reconciliation_attempts=1,  # Would need to track actual attempts
                retry_attempts=0,  # Would need to track retry attempts
                max_retries=self.max_retries,
                execution_time_ms=execution_time_ms,
                reconciliation_time_ms=reconciliation_time_ms,
                total_time_ms=execution_time_ms + reconciliation_time_ms,
                system_failure_triggered=not reconciliation_success,
                failure_reason="Reconciliation failed" if not reconciliation_success else None,
                metadata={
                    "component": self.__class__.__name__,
                    "execution_mode": self.execution_mode,
                },
            )

            # Log the event
            self.domain_event_logger.log_tight_loop_execution(event)

        except Exception as e:
            self.logger.error(
                "Failed to log tight loop execution",
                error_code="LOG-001",
                exc_info=e,
                order_id=order.operation_id,
            )

    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            "status": "healthy",
            "execution_mode": self.execution_mode,
            "execution_timeout": self.execution_timeout,
            "max_retries": self.max_retries,
            "component": self.__class__.__name__,
        }
    
    def _create_failed_handshake(self, order: Order, error_code: str, error_message: str) -> ExecutionHandshake:
        """
        Create a failed ExecutionHandshake for error handling.
        
        Args:
            order: Order that failed
            error_code: Error code for the failure
            error_message: Error message for the failure
            
        Returns:
            ExecutionHandshake: Failed execution handshake
        """
        return ExecutionHandshake(
            operation_id=order.operation_id,
            status=ExecutionStatus.FAILED,
            actual_deltas={},
            execution_details={},
            error_code=error_code,
            error_message=error_message,
            submitted_at=datetime.now(),
            simulated=True
        )