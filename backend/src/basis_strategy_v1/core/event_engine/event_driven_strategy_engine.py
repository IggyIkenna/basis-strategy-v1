"""
Event-Driven Strategy Engine using the component architecture.

This engine orchestrates all 9 components:
- Position Monitor (Core Component)
- Event Logger (Core Component)
- Exposure Monitor (Core Component)
- Risk Monitor (Core Component)
- P&L Calculator (Core Component)
- Strategy Manager (Execution Component)
- ExecutionManager (Execution Component)
- VenueInterfaceManager (Execution Component)
- Data Provider (Execution Component)
"""

import asyncio
import logging
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from pathlib import Path
import os
import uuid

# Import the new components
from ..components.position_monitor import PositionMonitor
from ...infrastructure.logging.domain_event_logger import DomainEventLogger
from ..components.exposure_monitor import ExposureMonitor
from ..components.risk_monitor import RiskMonitor
from ..components.pnl_monitor import PnLMonitor
from ..strategies.base_strategy_manager import BaseStrategyManager
from ..components.position_update_handler import PositionUpdateHandler
from ..execution.execution_manager import ExecutionManager
from ..execution.venue_interface_manager import VenueInterfaceManager
from ..interfaces.venue_interface_factory import VenueInterfaceFactory
from ...infrastructure.persistence.async_results_store import AsyncResultsStore
from ...core.utilities.utility_manager import UtilityManager
from ..health import (
    system_health_aggregator,
    PositionMonitorHealthChecker,
    DataProviderHealthChecker,
    RiskMonitorHealthChecker,
    EventLoggerHealthChecker,
)
from ...infrastructure.logging.log_directory_manager import LogDirectoryManager
from ...infrastructure.logging.structured_logger import StructuredLogger

logger = logging.getLogger(__name__)

# Create dedicated event engine logger
event_engine_logger = logging.getLogger("event_engine")
event_engine_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent.parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Create file handler for event engine logs
event_engine_handler = logging.FileHandler(logs_dir / "event_engine.log")
event_engine_handler.setLevel(logging.INFO)

# Create formatter
event_engine_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
event_engine_handler.setFormatter(event_engine_formatter)

# Add handler to logger
event_engine_logger.addHandler(event_engine_handler)


class EventDrivenStrategyEngine:
    """
    Event-driven strategy engine using the new component architecture.

    This engine orchestrates all 9 components in a coordinated manner:
    1. Data Provider loads mode-specific data
    2. Position Monitor tracks balances
    3. Exposure Monitor calculates exposures
    4. Risk Monitor assesses risks
    5. P&L Calculator tracks performance
    6. Strategy Manager makes decisions
    7. ExecutionManager processes Orders and executes trades
    8. Event Logger records everything
    """

    def __init__(
        self,
        config: Dict[str, Any],
        execution_mode: str,
        data_provider,
        initial_capital: float,
        share_class: str,
        debug_mode: bool = False,
        correlation_id: str = None,
    ):
        """
        Initialize event engine with injected configuration and data.

        Phase 3: All parameters injected from API request, no defaults.

        Args:
            config: Strategy configuration (from API request via config_manager)
            execution_mode: 'backtest' or 'live' (from startup config)
            data_provider: Pre-loaded data provider with all data in memory
            initial_capital: Initial capital from API request (NO DEFAULT)
            share_class: Share class from API request (NO DEFAULT)
            debug_mode: Debug mode from API request (NO DEFAULT)
            correlation_id: Correlation ID from API request (NO DEFAULT)
        """
        self.config = config
        self.mode = config.get("mode")
        self.share_class = share_class
        self.initial_capital = initial_capital
        self.execution_mode = execution_mode
        self.data_provider = data_provider  # Pre-loaded data provider
        self.debug_mode = debug_mode
        # Generate correlation_id and pid for this run
        self.correlation_id = correlation_id or uuid.uuid4().hex
        self.pid = os.getpid()
        
        # Initialize equity curve data collection for backtest results
        self.equity_curve_data = []

        # Create log directory structure
        self.log_dir = LogDirectoryManager.create_run_logs(
            correlation_id=self.correlation_id,
            pid=self.pid,
            mode=self.mode,
            strategy=self.mode,  # or extract strategy name from config
            capital=self.initial_capital,
        )

        # Initialize structured logger for engine
        self.logger = StructuredLogger(
            component_name="EventDrivenStrategyEngine",
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
            engine=self,  # Pass self for timestamp access
        )

        self.health_status = "healthy"
        self.error_count = 0

        # Validate required parameters (FAIL FAST)
        if not self.mode:
            raise ValueError("Mode is required in config")

        if not initial_capital or initial_capital <= 0:
            raise ValueError(f"Invalid initial_capital: {initial_capital}. Must be > 0.")

        if share_class not in ["USDT", "ETH"]:
            raise ValueError(f"Invalid share_class: {share_class}. Must be 'USDT' or 'ETH'.")

        if not data_provider:
            raise ValueError("Data provider is required")

        # Create shared dependencies once (no more multiple UtilityManager instances!)
        self.utility_manager = UtilityManager(self.config, self.data_provider)
        self.venue_interface_factory = VenueInterfaceFactory()

        # Create all components directly with shared dependencies
        self.position_monitor = PositionMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            self.venue_interface_factory,
            self.execution_mode,
            self.initial_capital,
            self.share_class,
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
        )

        self.event_logger = DomainEventLogger(
            self.log_dir, 
            correlation_id=self.correlation_id, 
            pid=self.pid
        )

        self.exposure_monitor = ExposureMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
        )

        self.risk_monitor = RiskMonitor(
            self.config,
            self.data_provider,
            self.utility_manager,
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
        )

        self.pnl_monitor = PnLMonitor(
            self.config,
            self.share_class,
            self.initial_capital,
            data_provider=self.data_provider,
            utility_manager=self.utility_manager,
            position_monitor=self.position_monitor,
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
        )

        # Create venue interface manager (needs venue interface factory)
        self.venue_interface_manager = VenueInterfaceManager(
            self.config, 
            self.data_provider, 
            self.venue_interface_factory,
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir
        )

        # Create execution manager first (without position_update_handler to avoid circular dependency)
        self.execution_manager = ExecutionManager(
            execution_mode=self.execution_mode,
            config=self.config,
            venue_interface_manager=self.venue_interface_manager,
            position_update_handler=None,  # Will be set after PositionUpdateHandler is created
            data_provider=self.data_provider,
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
        )

        # Create position update handler (doesn't need execution_manager)
        self.position_update_handler = PositionUpdateHandler(
            self.config,
            self.data_provider,
            self.execution_mode,
            self.position_monitor,
            self.exposure_monitor,
            self.risk_monitor,
            self.pnl_monitor,
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
        )

        # Set the circular reference after both are created
        self.execution_manager.position_update_handler = self.position_update_handler

        # Create strategy manager (needs monitors and event engine reference)
        from ..strategies.strategy_factory import StrategyFactory

        self.strategy_manager = StrategyFactory.create_strategy(
            mode=self.config.get("mode"),  # FAIL FAST - no default
            config=self.config,
            data_provider=self.data_provider,
            exposure_monitor=self.exposure_monitor,
            position_monitor=self.position_monitor,
            risk_monitor=self.risk_monitor,
            utility_manager=self.utility_manager,
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
        )

        # Create results store
        self.results_store = AsyncResultsStore("results", self.execution_mode)

        # Validate component references (FAIL FAST)
        if not self.position_monitor:
            raise ValueError("Position monitor reference is required")
        if not self.event_logger:
            raise ValueError("Event logger reference is required")
        if not self.exposure_monitor:
            raise ValueError("Exposure monitor reference is required")
        if not self.risk_monitor:
            raise ValueError("Risk monitor reference is required")
        if not self.pnl_monitor:
            raise ValueError("P&L calculator reference is required")
        if not self.strategy_manager:
            raise ValueError("Strategy manager reference is required")
        if not self.results_store:
            raise ValueError("Results store reference is required")
        if not self.utility_manager:
            raise ValueError("Utility manager reference is required")
        if not self.execution_manager:
            raise ValueError("Execution manager reference is required")
        if not self.venue_interface_manager:
            raise ValueError("Venue interface manager reference is required")
        if not self.position_update_handler:
            raise ValueError("Position update handler reference is required")

        # Event loop state
        self.current_timestamp = None
        self.is_running = False

        # Register components with health system
        self._register_components_with_health_system()

        self.logger.info(
            f"EventDrivenStrategyEngine initialized: {self.mode} mode, {share_class} share class, {initial_capital} capital",
            mode=self.mode,
            share_class=share_class,
            initial_capital=initial_capital,
        )

        logger.info(
            f"EventDrivenStrategyEngine initialized: {self.mode} mode, {share_class} share class, {initial_capital} capital"
        )

    def _register_components_with_health_system(self):
        """Register all components with the health system for monitoring."""
        try:
            from ..health import (
                system_health_aggregator,
                PositionMonitorHealthChecker,
                DataProviderHealthChecker,
                RiskMonitorHealthChecker,
                EventLoggerHealthChecker,
                ExposureMonitorHealthChecker,
                PnLMonitorHealthChecker,
                StrategyManagerHealthChecker,
                ExecutionManagerHealthChecker,
            )

            # Register all core components
            system_health_aggregator.register_component(
                "position_monitor", PositionMonitorHealthChecker(self.position_monitor)
            )
            system_health_aggregator.register_component(
                "data_provider", DataProviderHealthChecker(self.data_provider)
            )
            system_health_aggregator.register_component(
                "exposure_monitor", ExposureMonitorHealthChecker(self.exposure_monitor)
            )
            system_health_aggregator.register_component(
                "risk_monitor", RiskMonitorHealthChecker(self.risk_monitor)
            )
            system_health_aggregator.register_component(
                "pnl_monitor", PnLMonitorHealthChecker(self.pnl_monitor)
            )
            system_health_aggregator.register_component(
                "strategy_manager", StrategyManagerHealthChecker(self.strategy_manager)
            )
            system_health_aggregator.register_component(
                "execution_manager", ExecutionManagerHealthChecker(self.execution_manager)
            )
            system_health_aggregator.register_component(
                "event_logger", EventLoggerHealthChecker(self.event_logger)
            )

            logger.info("All 8 main components registered with health system")
        except Exception as e:
            logger.error(f"Failed to register components with health system: {e}")

    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.error_count += 1
        error_code = f"EDSE_ERROR_{self.error_count:04d}"

        logger.error(
            f"Event Driven Strategy Engine error {error_code}: {str(error)}",
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

    async def run_backtest(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Run a complete backtest using all components.

        Args:
            start_date: Start date for backtest (YYYY-MM-DD) - REQUIRED
            end_date: End date for backtest (YYYY-MM-DD) - REQUIRED

        Returns:
            Dictionary containing backtest results

        Raises:
            ValueError: If start_date or end_date is not provided or invalid

        # Time-triggered workflow for backtest execution
        # Current Issue: Backtest execution loop needs to implement time-triggered workflow pattern
        # Required Changes:
        #   1. Implement simulated hourly data loop for backtest time triggers
        #   2. Execute full component chain on each time trigger
        #   3. Handle business logic (deposits, withdrawals, risk checks) in time-triggered workflow
        #   4. Implement reserve management, dust management, and equity tracking workflows
        # Reference: docs/WORKFLOW_GUIDE.md - Internal System Event Workflows section
        # Reference: docs/WORKFLOW_GUIDE.md - Time-Triggered Workflow (Primary) section
        # Status: PENDING
        """
        # Validate required parameters
        if not start_date:
            raise ValueError("start_date is required for backtest")
        if not end_date:
            raise ValueError("end_date is required for backtest")

        # Validate date format
        try:
            # Parse dates and handle timezone properly
            start_ts = pd.Timestamp(start_date)
            end_ts = pd.Timestamp(end_date)

            # If already timezone-aware, convert to UTC; otherwise localize to UTC
            if start_ts.tz is not None:
                start_dt = start_ts.tz_convert("UTC")
            else:
                start_dt = start_ts.tz_localize("UTC")

            if end_ts.tz is not None:
                end_dt = end_ts.tz_convert("UTC")
            else:
                end_dt = end_ts.tz_localize("UTC")
        except Exception as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD format. Error: {e}")

        # Validate date range
        if start_dt >= end_dt:
            raise ValueError(f"start_date ({start_date}) must be before end_date ({end_date})")

        logger.info(f"Starting backtest for {self.mode} mode from {start_date} to {end_date}")

        try:
            # Phase 3: Data provider is already loaded with all data at startup
            # No need to reload data - just verify it's available for the date range
            try:
                # Get data using canonical pattern
                data = self.data_provider.get_data(start_dt)
                test_snapshot = data["market_data"]
                if not test_snapshot or len(test_snapshot) <= 1:  # Only timestamp
                    raise ValueError(f"No market data available for start date {start_date}")
            except Exception as e:
                raise ValueError(
                    f"No data available for backtest date range {start_date} to {end_date}: {e}"
                )

            logger.info(f"Data loaded successfully for backtest")

            # Generate unique request ID for this backtest
            request_id = str(uuid.uuid4())

            # Start async results store
            await self.results_store.start()

            # Initialize results tracking (minimal for async storage)
            results = {"config": self.config, "start_date": start_date, "end_date": end_date}

            # Generate timestamps for backtest based on strategy mode
            # ML strategies use 5-minute intervals, others use hourly
            if self.mode in ["ml_btc_directional_usdt_margin", "ml_usdt_directional_usdt_margin"]:
                freq = "5min"  # 5-minute intervals for ML strategies
                logger.info("Using 5-minute intervals for ML strategy")
            else:
                freq = "H"  # Hourly intervals for traditional strategies
                logger.info("Using hourly intervals for traditional strategy")

            timestamps = pd.date_range(start=start_dt, end=end_dt, freq=freq, tz="UTC")

            logger.info(
                f"Running backtest for {len(timestamps)} timestamps from {start_date} to {end_date}"
            )

            # Run backtest loop with component orchestration
            # Note: Initial capital is handled automatically by Position Monitor on first position_refresh
            # See: docs/POSITION_MONITOR_REFACTOR_DESIGN.md - Phase 3: 2-Trigger System
            for timestamp in timestamps:
                try:
                    # Get market data snapshot for this timestamp using canonical pattern
                    data = self.data_provider.get_data(timestamp)
                    market_data = data["market_data"]
                except Exception as e:
                    logger.warning(f"Skipping timestamp {timestamp} due to missing data: {e}")
                    continue
                self._process_timestep(timestamp, market_data, request_id)
            # Save final results and event log
            final_results = self._calculate_final_results(results)
            await self.results_store.save_final_result(request_id, final_results)
            # Event logs are already saved to JSONL files by DomainEventLogger
            # await self.results_store.save_event_log(request_id, self.event_logger._get_all_events())

            # Stop async results store
            await self.results_store.stop()

            logger.info("Backtest completed successfully")
            return final_results

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            # Ensure results store is stopped even on error
            try:
                await self.results_store.stop()
            except Exception as stop_error:
                logger.error(f"Error stopping results store: {stop_error}")
            raise

    def _process_timestep(self, timestamp: pd.Timestamp, market_data: Dict, request_id: str):
        """
        Process a single timestep in the backtest - CORE EVENT BEHAVIOR.

        This is the critical orchestration method that coordinates all components
        for each timestamp in the backtest.
        """
        self.current_timestamp = timestamp

        try:
            # 1. Refresh positions (MODE-AGNOSTIC - called in BOTH backtest and live)
            # Ref: POSITION_MONITOR_REFACTOR_DESIGN.md - Symmetric triggers
            logger.info(f"Event Engine: Refreshing positions at timestep {timestamp}")
            position_snapshot = self.position_monitor.update_state(
                timestamp, "position_refresh", None  # Called in BOTH modes
            )
            logger.info(
                f"Event Engine: Position snapshot refreshed, {len(position_snapshot)} positions tracked"
            )

            # 2. Calculate current exposure using injected data provider
            exposure = self.exposure_monitor.calculate_exposure(
                timestamp=timestamp, position_snapshot=position_snapshot, market_data=market_data
            )
            logger.info(
                f"Event Engine: Exposure calculated - type: {type(exposure)}, keys: {list(exposure.keys()) if isinstance(exposure, dict) else 'Not a dict'}"
            )

            # ExposureMonitor handles its own domain event logging
            # No need to log here - component will log ExposureSnapshot

            # 3. Assess risk using injected config and data
            # Enable debug logging if debug mode is enabled
            if self.debug_mode:
                logger.info(f"Event Engine: Enabling Risk Monitor debug logging")
                self.risk_monitor.enable_debug_logging()

            logger.info(f"Event Engine: Calling Risk Monitor assess_risk")
            risk_assessment = self.risk_monitor.assess_risk(
                exposure_data=exposure, market_data=market_data, timestamp=timestamp
            )
            logger.info(f"Event Engine: Risk Monitor assess_risk completed")

            # RiskMonitor handles its own domain event logging
            # No need to log here - component will log RiskAssessment

            # 4. Generate strategy orders
            # P1 FIX: Remove PnL calculation before execution (line 493 removed)
            # Spec: WORKFLOW_REFACTOR_SPECIFICATION.md lines 456-466 - PnL calculated AFTER execution

            strategy_orders = self.strategy_manager.generate_orders(
                timestamp=timestamp,
                exposure=exposure,
                risk_assessment=risk_assessment,
                market_data=market_data,
                position_snapshot=position_snapshot,  # Add raw position data for strategy
            )

            # StrategyManager handles its own domain event logging
            # No need to log here - component will log StrategyDecision and OrderEvent

            # 5. Execute orders if any (via ExecutionManager orchestration)
            if strategy_orders:
                logger.info(
                    f"Event Engine: Strategy generated {len(strategy_orders)} orders to execute"
                )

                # Execute orders through ExecutionManager (handles orchestration + reconciliation)
                execution_result = self.execution_manager.process_orders(
                    timestamp=timestamp, orders=strategy_orders
                )
                logger.info(f"Event Engine: Execution completed with result: {execution_result}")

                # P1 FIX: Check execution success per WORKFLOW_REFACTOR_SPECIFICATION.md lines 276-286
                # execution_result is a List[Dict], check if any trades failed
                failed_trades = [
                    trade for trade in execution_result if not trade.get("success", True)
                ]
                if failed_trades:
                    self._handle_execution_failure(failed_trades, timestamp)
                    return  # Stop processing this timestep on failure
            else:
                logger.info(f"Event Engine: No orders to execute")

            # 6. Calculate P&L AFTER execution (with execution costs)
            # Spec: WORKFLOW_REFACTOR_SPECIFICATION.md lines 288-291, 456-466
            logger.info(f"Event Engine: Calculating P&L after execution with all costs")
            self.pnl_monitor.update_state(timestamp, "full_loop")
            pnl = self.pnl_monitor.get_latest_pnl()
            logger.info(f"Event Engine: P&L calculated successfully")
            if pnl and "BALANCE_BASED" in pnl:
                logger.info(
                    f"Event Engine: P&L pnl_cumulative: {pnl.get('BALANCE_BASED', {}).get('PNL_CUMULATIVE', 0)}"
                )
            else:
                logger.warning(f"Event Engine: P&L result missing 'BALANCE_BASED' key: {pnl}")

            # 7. Collect equity curve data for backtest results
            # Calculate current portfolio value for equity curve
            current_position = self.position_monitor.get_current_positions()
            current_exposure = self.exposure_monitor.calculate_exposure(
                timestamp=timestamp, position_snapshot=current_position, market_data=market_data
            )
            
            # Get current P&L to calculate net value
            current_pnl = self.pnl_monitor.get_latest_pnl()
            pnl_cumulative = current_pnl.get("BALANCE_BASED", {}).get("PNL_CUMULATIVE", 0.0)
            net_value = self.initial_capital + pnl_cumulative
            gross_value = current_exposure.get("total_exposure", net_value)
            
            # Collect equity curve data point
            equity_point = {
                "timestamp": timestamp.isoformat(),
                "net_value": net_value,
                "gross_value": gross_value,
                "positions": current_position.copy()  # Copy to avoid reference issues
            }
            self.equity_curve_data.append(equity_point)
            
            logger.debug(f"Event Engine: Collected equity curve point - timestamp: {timestamp}, net_value: {net_value}")

            # 8. Log events (async I/O - handled separately)
            # P0 FIX: Use strategy_orders instead of undefined strategy_decision
            self._log_timestep_event(timestamp, exposure, risk_assessment, pnl, strategy_orders)

            # 9. Store results (async I/O - handled separately)
            # P0 FIX: Use strategy_orders and remove undefined action parameter
            self._store_timestep_result(
                request_id, timestamp, exposure, risk_assessment, pnl, strategy_orders
            )

        except ValueError as e:
            # P2 FIX: More specific exception handling - fail fast on critical errors
            logger.error(f"ValueError processing timestep {timestamp}: {e}")
            self._log_error_event(timestamp, str(e))
            raise  # Propagate ValueError for fail-fast
        except KeyError as e:
            logger.error(f"KeyError processing timestep {timestamp}: {e}")
            self._log_error_event(timestamp, str(e))
            raise  # Propagate KeyError for fail-fast
        except Exception as e:
            # Log but continue for non-critical errors
            error_code = (
                "EVENT_ERROR_001"
                if "'list' object has no attribute 'get'" in str(e)
                else "EVENT_ERROR_002"
            )
            logger.warning(
                f"Non-critical error processing timestep {timestamp}: {e}",
                extra={"error_code": error_code},
            )
            self._log_error_event(timestamp, str(e))

    def _calculate_final_results(self, results: Dict) -> Dict[str, Any]:
        """Calculate final backtest results."""

        # Get current position and calculate exposure for P&L calculation
        current_position = self.position_monitor.get_current_positions()
        final_exposure = self.exposure_monitor.calculate_exposure(
            timestamp=self.current_timestamp,
            position_snapshot=current_position,
            market_data=self.data_provider.get_data(self.current_timestamp),
        )
        # Update P&L state with final exposure
        self.pnl_monitor.update_state(self.current_timestamp, "final_calculation")
        final_pnl = self.pnl_monitor.get_latest_pnl()

        # Calculate performance metrics
        initial_capital = self.initial_capital
        pnl_cumulative = final_pnl.get("BALANCE_BASED", {}).get("PNL_CUMULATIVE", 0.0)
        logger.info(
            f"Final results calculation - initial_capital: {initial_capital}, pnl_cumulative: {pnl_cumulative}"
        )
        logger.info(f"Final P&L structure: {final_pnl}")

        final_value = initial_capital + pnl_cumulative
        total_return = pnl_cumulative
        total_return_pct = (total_return / initial_capital) * 100 if initial_capital > 0 else 0

        # Event logs are already saved to JSONL files by DomainEventLogger
        all_events = []  # Legacy field, events are in JSONL files

        final_results = {
            "performance": {
                "total_return": total_return,
                "total_return_pct": total_return_pct,
                "initial_capital": initial_capital,
                "final_value": final_value,
                "equity_curve": self.equity_curve_data,  # Include equity curve data
            },
            "final_pnl": final_pnl,
            "final_position": current_position,
            "events": all_events,
            "config": self.config,
            "start_date": results["start_date"],
            "end_date": results["end_date"],
            "mode": self.mode,
            "share_class": self.share_class,
        }

        logger.info(
            f"Event Engine: Final results calculated - total_return: {total_return}, final_value: {final_value}"
        )
        return final_results

    async def run_live(self):
        """Run the strategy in live mode with 60-second position refresh cycle."""
        logger.info("Starting live strategy execution")
        self.is_running = True
        request_id = str(uuid.uuid4())

        try:
            # Start async results store
            await self.results_store.start()

            while self.is_running:
                # Get current market data using canonical pattern
                current_timestamp = pd.Timestamp.now(tz="UTC")
                data = self.data_provider.get_data(current_timestamp)
                current_data = data["market_data"]

                # Process timestep (includes position_refresh at start)
                # See: docs/POSITION_MONITOR_REFACTOR_DESIGN.md - Phase 3: 2-Trigger System
                self._process_timestep(current_timestamp, current_data, request_id)

                # Wait for next update cycle (60-second refresh)
                await asyncio.sleep(60)  # Update every minute

        except Exception as e:
            logger.error(f"Live execution failed: {e}")
            raise
        finally:
            self.is_running = False
            # Stop async results store
            try:
                await self.results_store.stop()
            except Exception as stop_error:
                logger.error(f"Error stopping results store: {stop_error}")

    def _stop(self):
        """Stop the live strategy execution."""
        self.is_running = False
        logger.info("Strategy execution stopped")

    def _get_current_timestamp(self) -> pd.Timestamp:
        """
        Get the current timestamp for ML strategies.

        Returns:
            Current timestamp (backtest: from loop, live: current time)
        """
        if self.execution_mode == "backtest":
            # In backtest mode, return the current timestamp from the loop
            if self.current_timestamp is not None:
                return self.current_timestamp
            else:
                # Fallback to current time if not in backtest loop
                return pd.Timestamp.now(tz="UTC")
        else:
            # In live mode, return current time
            return pd.Timestamp.now(tz="UTC")

    async def get_status(self) -> Dict[str, Any]:
        """Get current status of all components with health information."""
        # Get system health report
        health_report = await system_health_aggregator.get_system_health()

        return {
            "mode": self.mode,
            "share_class": self.share_class,
            "execution_mode": self.execution_mode,
            "initial_capital": self.config.get("initial_capital", 100000),
            "is_running": self.is_running,
            "current_timestamp": self.current_timestamp,
            "health": {
                "overall_status": health_report["status"],
                "timestamp": health_report["timestamp"],
                "summary": health_report["summary"],
                "components": health_report["components"],
            },
            "components": {
                "position_monitor": "active",
                "event_logger": "active",
                "exposure_monitor": "active",
                "risk_monitor": "active",
                "pnl_monitor": "active",
                "strategy_manager": "active",
                "cex_execution_interface": "active",
                "onchain_execution_interface": "active",
                "transfer_execution_interface": "active",
                "data_provider": "active",
            },
        }

    def _handle_execution_failure(self, execution_result: Dict, timestamp: pd.Timestamp) -> None:
        """
        Handle execution failure with logging and error escalation.

        P1 FIX: Implements execution failure handling per WORKFLOW_REFACTOR_SPECIFICATION.md lines 276-286

        Args:
            execution_result: Result dictionary from ExecutionManager.process_orders()
            timestamp: Current timestamp for logging
        """
        self.error_count += 1

        error_details = {
            "timestamp": timestamp,
            "execution_result": execution_result,
            "error_code": f"EXEC_FAILURE_{self.error_count:04d}",
        }

        logger.error(f"Execution failure: {error_details}", extra=error_details)

        # Update health status
        if self.error_count > 5:
            self.health_status = "degraded"
        if self.error_count > 10:
            self.health_status = "critical"
            self._trigger_system_failure(f"Too many execution failures: {self.error_count}")

        # Log error event
        self._log_error_event(timestamp, f"Execution failure: {execution_result}")

    def _trigger_system_failure(self, failure_reason: str) -> None:
        """
        Trigger system failure and restart via health/error systems.

        P1 FIX: Implements system failure trigger per WORKFLOW_REFACTOR_SPECIFICATION.md lines 397-411

        Args:
            failure_reason: Reason for system failure

        Raises:
            SystemExit: Always raises to trigger deployment restart
        """
        # Update health status to critical
        self.health_status = "critical"

        # Log critical error with structured logging
        logger.critical(
            f"SYSTEM FAILURE: {failure_reason}",
            extra={
                "error_code": "SYSTEM_FAILURE",
                "failure_reason": failure_reason,
                "component": self.__class__.__name__,
                "timestamp": pd.Timestamp.now(tz="UTC"),
                "execution_mode": self.execution_mode,
                "error_count": self.error_count,
            },
        )

        # Raise SystemExit to trigger deployment restart
        raise SystemExit(f"System failure: {failure_reason}")

    def _debug_print_position_monitor(self):
        """Print detailed position monitor state for debugging."""
        if not self.debug_mode:
            return

        logger.info("=" * 80)
        logger.info("🔍 DEBUG MODE - POSITION MONITOR STATE")
        logger.info("=" * 80)

        try:
            snapshot = self.position_monitor.get_current_positions()

            logger.info(f"📊 Position Monitor Snapshot:")
            logger.info(f"   Last Updated: {snapshot.get('last_updated', 'N/A')}")

            # Wallet balances
            logger.info(f"\n💰 Wallet Balances:")
            wallet = snapshot.get("wallet", {})
            for token, balance in wallet.items():
                if balance != 0:  # Only show non-zero balances
                    logger.info(f"   {token}: {balance:,.6f}")

            # CEX accounts
            logger.info(f"\n🏦 CEX Account Balances:")
            cex_accounts = snapshot.get("cex_accounts", {})
            for exchange, tokens in cex_accounts.items():
                logger.info(f"   {exchange.upper()}:")
                for token, balance in tokens.items():
                    if balance != 0:  # Only show non-zero balances
                        logger.info(f"     {token}: {balance:,.6f}")

            # Perpetual positions
            logger.info(f"\n📈 Perpetual Positions:")
            perp_positions = snapshot.get("perp_positions", {})
            for exchange, positions in perp_positions.items():
                if positions:  # Only show exchanges with positions
                    logger.info(f"   {exchange.upper()}:")
                    for instrument, position in positions.items():
                        logger.info(f"     {instrument}:")
                        logger.info(f"       Size: {position.get('size', 0):,.6f}")
                        logger.info(f"       Entry Price: {position.get('entry_price', 0):,.6f}")
                        logger.info(f"       Entry Time: {position.get('entry_timestamp', 'N/A')}")
                        logger.info(f"       Notional USD: ${position.get('notional_usd', 0):,.2f}")
                else:
                    logger.info(f"   {exchange.upper()}: No positions")

            logger.info("=" * 80)
            logger.info("🔍 END DEBUG MODE")
            logger.info("=" * 80 + "\n")

        except Exception as e:
            logger.error(f"\n❌ DEBUG ERROR: Failed to get position monitor state: {e}\n")

    def _log_timestep_event(
        self,
        timestamp: pd.Timestamp,
        exposure: Dict,
        risk_assessment: Dict,
        pnl: Dict,
        strategy_orders: List,
    ):
        """
        Log timestep event synchronously.

        Note: EventLogger.log_event() is synchronous for simplicity.
        See: docs/POSITION_MONITOR_REFACTOR_DESIGN.md - Phase 3: 2-Trigger System
        """
        try:
            # Log timestep completion using standard logger
            logger.info(f"Timestep processed: {timestamp}")
        except Exception as e:
            logger.error(f"Failed to log timestep event: {e}")

    def _store_timestep_result(
        self,
        request_id: str,
        timestamp: pd.Timestamp,
        exposure: Dict,
        risk_assessment: Dict,
        pnl: Dict,
        strategy_orders: List,
    ):
        """
        Store timestep result asynchronously (queued for background processing).

        Note: Results are queued and processed asynchronously by AsyncResultsStore worker.
        See: docs/specs/15_EVENT_DRIVEN_STRATEGY_ENGINE.md - Async Results Storage
        """
        try:
            # Queue result for async storage (non-blocking)
            import asyncio

            asyncio.create_task(
                self.results_store.save_timestep_result(
                    request_id=request_id,
                    timestamp=timestamp,
                    data={
                        "pnl": pnl,
                        "exposure": exposure,
                        "risk": risk_assessment,
                        "orders": strategy_orders,
                        "event_type": "TIMESTEP_PROCESSED",
                    },
                )
            )
        except Exception as e:
            logger.error(f"Failed to store timestep result: {e}")

    def _log_error_event(self, timestamp: pd.Timestamp, error_message: str):
        """
        Log error event synchronously.

        Note: EventLogger.log_event() is synchronous for simplicity.
        See: docs/POSITION_MONITOR_REFACTOR_DESIGN.md - Phase 3: 2-Trigger System
        """
        try:
            # Log error using standard logger
            logger.error(f"Error at {timestamp}: {error_message}")
        except Exception as e:
            logger.error(f"Failed to log error event: {e}")
