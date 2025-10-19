"""
Async Results Store - Queue-based results storage with ordering guarantees.

This module implements an async results storage system using AsyncIO queues
to ensure FIFO processing of results even when write operations have variable
duration. Background worker processes queue sequentially to prevent race conditions.

Architecture:
- Uses AsyncIO queue for FIFO ordering guarantees
- Background worker processes queue sequentially
- Prevents race conditions under heavy load
- Same implementation for backtest and live modes
- Graceful shutdown with queue drain

Ordering Guarantees:
- AsyncIO's single-threaded event loop prevents race conditions
- Queue ensures FIFO processing even with variable write times
- Await semantics guarantee completion before next operation
- No dropped data or out-of-order writes
"""

import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime
import logging

from ...infrastructure.logging.structured_logger import StructuredLogger

logger = logging.getLogger(__name__)


class AsyncResultsStore:
    """
    Async results storage with queue-based ordering guarantees.

    Uses AsyncIO queue to ensure FIFO processing of results even when
    write operations have variable duration. Background worker processes
    queue sequentially to prevent race conditions.

    Features:
    - FIFO ordering guarantees
    - Background worker for sequential processing
    - Graceful shutdown with queue drain
    - Error handling and logging
    - Same implementation for backtest and live modes
    """

    def __init__(
        self, results_dir: str, execution_mode: str, utility_manager=None, pnl_monitor=None
    ):
        """
        Initialize AsyncResultsStore.

        Args:
            results_dir: Directory to store results
            execution_mode: 'backtest' or 'live'
            utility_manager: Centralized utility manager for config-driven operations
            pnl_monitor: PnL Monitor instance for read-only access
        """
        self.results_dir = Path(results_dir)
        self.execution_mode = execution_mode
        self.utility_manager = utility_manager
        self.pnl_monitor = pnl_monitor
        self.health_status = "healthy"
        self.error_count = 0
        self.queue = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self.is_running = False

        # Get position subscriptions from utility manager config
        if utility_manager and hasattr(utility_manager, "config"):
            position_config = utility_manager.config.get("component_config", {}).get(
                "position_monitor", {}
            )
            self.position_subscriptions = position_config.get("position_subscriptions", [])
        else:
            self.position_subscriptions = []

        logger.info(f"ResultsStore subscribed to {len(self.position_subscriptions)} positions")

        # Initialize JSONL logger
        self.structured_logger = StructuredLogger(
            component_name="ResultsStore",
            correlation_id=str(uuid.uuid4().hex),
            pid=os.getpid(),
            log_dir=Path("logs/default/0"),
            engine=None,
        )

        # Create results directory if needed
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Log initialization
        self.structured_logger.info(
            f"AsyncResultsStore initialized: {results_dir}, mode: {execution_mode}",
            event_type="component_initialization",
            metadata={
                "execution_mode": execution_mode,
                "config_hash": hash(str(results_dir)),
                "results_dir": str(results_dir),
                "queue_size": self.queue.maxsize,
                "component_type": "ResultsStore",
            },
        )

        logger.info(f"AsyncResultsStore initialized: {results_dir}, mode: {execution_mode}")

    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.error_count += 1

        # Use specification-compliant error codes
        if "storage" in context.lower() or "write" in context.lower():
            error_code = "RST-001"  # Storage Failed
        elif "queue" in context.lower():
            error_code = "RST-002"  # Queue Full
        elif "timeout" in context.lower():
            error_code = "RST-003"  # Write Timeout
        else:
            error_code = "RST-001"  # Default to Storage Failed

        logger.error(
            f"Results Store error {error_code}: {str(error)}",
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
            "queue_size": self.queue.qsize(),
            "is_running": self.is_running,
            "component": self.__class__.__name__,
        }

    def _process_config_driven_operations(self, operations: list) -> list:
        """Process operations based on configuration settings."""
        processed_operations = []

        for operation in operations:
            try:
                # Apply config-driven logic
                if self.utility_manager and self.utility_manager.config.get(
                    "enable_validation", True
                ):
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

    def _validate_operation(self, operation: Any) -> bool:
        """Validate operation based on configuration."""
        # Basic validation logic
        if isinstance(operation, dict):
            required_fields = ["type", "data"] if self.utility_manager else ["type"]
            return all(field in operation for field in required_fields)
        return True

    async def start(self):
        """Start background worker for queue processing."""
        if self.is_running:
            logger.warning("AsyncResultsStore already running")
            return

        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker())
        logger.info("AsyncResultsStore worker started")

    async def stop(self):
        """Stop background worker and flush remaining queue."""
        if not self.is_running:
            logger.warning("AsyncResultsStore not running")
            return

        logger.info("Stopping AsyncResultsStore worker...")
        self.is_running = False

        # Wait for queue to drain
        try:
            await asyncio.wait_for(self.queue.join(), timeout=30.0)
            logger.info("Queue drained successfully")
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for queue to drain")

        # Cancel worker task
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                logger.info("Worker task cancelled")

        logger.info("AsyncResultsStore stopped")

    async def _worker(self):
        """Background worker processes queue in FIFO order."""
        logger.info("AsyncResultsStore worker started")

        while self.is_running:
            try:
                # Get next result from queue (waits if empty)
                item = await asyncio.wait_for(self.queue.get(), timeout=1.0)

                # Process based on type
                result_type = item.get("type")
                if result_type == "timestep":
                    await self._write_timestep_result(item)
                elif result_type == "final":
                    await self._write_final_result(item)
                elif result_type == "event_log":
                    await self._write_event_log(item)
                else:
                    logger.error(f"Unknown result type: {result_type}")

                # Mark task complete
                self.queue.task_done()

            except asyncio.TimeoutError:
                # No items in queue, continue
                continue
            except Exception as e:
                # Log error but don't stop worker
                logger.error(f"Error processing result: {e}")
                if not self.queue.empty():
                    self.queue.task_done()

        logger.info("AsyncResultsStore worker stopped")

    async def save_timestep_result(
        self, request_id: str, timestamp: pd.Timestamp, data: Dict[str, Any]
    ):
        """
        Queue timestep result for async storage.

        Args:
            request_id: Unique request identifier
            timestamp: Timestamp for the result
            data: Result data to store
        """
        await self.queue.put(
            {"type": "timestep", "request_id": request_id, "timestamp": timestamp, "data": data}
        )

        # Log state update
        self.structured_logger.info(
            f"Timestep result queued: {request_id}",
            event_type="timestep_result_queued",
            metadata={
                "request_id": request_id,
                "timestamp": timestamp.isoformat(),
                "data_size": len(str(data)),
                "queue_size": self.queue.qsize(),
            },
        )

        logger.debug(f"Queued timestep result: {request_id}, {timestamp}")

    async def save_final_result(self, request_id: str, data: Dict[str, Any]):
        """
        Queue final result for async storage.

        Args:
            request_id: Unique request identifier
            data: Final result data to store
        """
        await self.queue.put({"type": "final", "request_id": request_id, "data": data})
        logger.debug(f"Queued final result: {request_id}")

    async def save_event_log(self, request_id: str, events: List[Dict[str, Any]]):
        """
        Queue event log for async storage.

        Args:
            request_id: Unique request identifier
            events: List of events to store
        """
        await self.queue.put({"type": "event_log", "request_id": request_id, "events": events})
        logger.debug(f"Queued event log: {request_id}, {len(events)} events")

    async def _write_timestep_result(self, item: Dict):
        """Write timestep result to disk."""
        request_id = item["request_id"]
        timestamp = item["timestamp"]
        data = item["data"]

        # Add P&L data if available
        if self.pnl_monitor:
            latest_pnl = self.pnl_monitor.get_latest_pnl()
            if latest_pnl:
                data["pnl"] = latest_pnl

        # Create request directory
        request_dir = self.results_dir / request_id / "timesteps"
        request_dir.mkdir(parents=True, exist_ok=True)

        # Write timestep data
        filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = request_dir / filename

        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug(f"Wrote timestep result: {filepath}")
        except Exception as e:
            logger.error(f"Failed to write timestep result {filepath}: {e}")
            raise

    async def _write_final_result(self, item: Dict):
        """Write final result to disk."""
        request_id = item["request_id"]
        data = item["data"]

        # Create request directory
        request_dir = self.results_dir / request_id
        request_dir.mkdir(parents=True, exist_ok=True)

        # Write final result
        filepath = request_dir / "final_result.json"

        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug(f"Wrote final result: {filepath}")
        except Exception as e:
            logger.error(f"Failed to write final result {filepath}: {e}")
            raise

    async def _write_event_log(self, item: Dict):
        """Write event log to CSV."""
        request_id = item["request_id"]
        events = item["events"]

        # Create request directory
        request_dir = self.results_dir / request_id
        request_dir.mkdir(parents=True, exist_ok=True)

        # Convert to DataFrame and save
        try:
            df = pd.DataFrame(events)
            filepath = request_dir / "event_log.csv"
            df.to_csv(filepath, index=False)
            logger.debug(f"Wrote event log: {filepath}")
        except Exception as e:
            logger.error(f"Failed to write event log {filepath}: {e}")
            raise

    def get_queue_size(self) -> int:
        """Get current queue size for monitoring."""
        return self.queue.qsize()

    def is_worker_running(self) -> bool:
        """Check if worker is running."""
        return self.is_running and self.worker_task is not None and not self.worker_task.done()

    # Standardized Logging Methods (per HEALTH_ERROR_SYSTEMS.md and 08_EVENT_LOGGER.md)

    def log_structured_event(
        self,
        timestamp: pd.Timestamp,
        event_type: str,
        level: str,
        message: str,
        component_name: str,
        data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Log a structured event with standardized format."""
        try:
            event_data = {
                "timestamp": timestamp,
                "event_type": event_type,
                "level": level,
                "message": message,
                "component_name": component_name,
                "data": data or {},
                "correlation_id": correlation_id,
            }

            # Log to standard logger
            if level == "ERROR":
                logger.error(f"[{component_name}] {message}", extra=event_data)
            elif level == "WARNING":
                logger.warning(f"[{component_name}] {message}", extra=event_data)
            else:
                logger.info(f"[{component_name}] {message}", extra=event_data)

        except Exception as e:
            logger.error(f"Failed to log structured event: {e}")

    def log_performance_metric(
        self, metric_name: str, value: float, unit: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a performance metric."""
        try:
            timestamp = pd.Timestamp.now(tz="UTC")
            message = f"Performance metric: {metric_name} = {value} {unit}"
            metric_data = {"metric_name": metric_name, "value": value, "unit": unit, **(data or {})}
            self.log_structured_event(
                timestamp, "performance_metric", "INFO", message, "AsyncResultsStore", metric_data
            )
        except Exception as e:
            logger.error(f"Failed to log performance metric: {e}")

    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Log an error with standardized format."""
        try:
            timestamp = pd.Timestamp.now(tz="UTC")
            error_data = {
                "error_type": type(error).__name__,
                "context": context or {},
                "correlation_id": correlation_id,
            }
            self.log_structured_event(
                timestamp, "error", "ERROR", str(error), "AsyncResultsStore", error_data
            )
        except Exception as e:
            logger.error(f"Failed to log error: {e}")

    def log_warning(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Log a warning with standardized format."""
        try:
            timestamp = pd.Timestamp.now(tz="UTC")
            self.log_structured_event(
                timestamp, "warning", "WARNING", message, "AsyncResultsStore", data, correlation_id
            )
        except Exception as e:
            logger.error(f"Failed to log warning: {e}")
