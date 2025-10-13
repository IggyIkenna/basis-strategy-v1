"""
New Event-Driven Strategy Engine using the new component architecture.

TODO-REFACTOR: SINGLETON PATTERN VIOLATION - See docs/REFERENCE_ARCHITECTURE_CANONICAL.md
ISSUE: This component may violate singleton pattern requirements:

1. SINGLETON PATTERN REQUIREMENTS:
   - All components must use singleton pattern correctly
   - Single instances across the system
   - Proper instance management and lifecycle

2. REQUIRED VERIFICATION:
   - Verify all 9 components use singleton pattern
   - Ensure proper instance management
   - Check for multiple instantiation issues

3. CANONICAL SOURCE:
   - docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Singleton Pattern
   - All components must be single instances

This engine wires together all 9 components:
- Position Monitor (Core Component)
- Event Logger (Core Component) 
- Exposure Monitor (Core Component)
- Risk Monitor (Core Component)
- P&L Calculator (Core Component)
- Strategy Manager (Execution Component)
- CEX Execution Manager (Execution Component)
- OnChain Execution Manager (Execution Component)
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
from ...infrastructure.logging.event_logger import EventLogger
from ..components.exposure_monitor import ExposureMonitor
from ..components.risk_monitor import RiskMonitor
from ..math.pnl_calculator import PnLCalculator
from ..strategies.base_strategy_manager import BaseStrategyManager
from ..components.position_update_handler import PositionUpdateHandler
# Legacy execution managers removed - using new execution interfaces instead
from ..interfaces.venue_interface_factory import VenueInterfaceFactory
from ...infrastructure.persistence.async_results_store import AsyncResultsStore
from ..health import (
    system_health_aggregator,
    PositionMonitorHealthChecker,
    DataProviderHealthChecker,
    RiskMonitorHealthChecker,
    EventLoggerHealthChecker
)
from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

logger = logging.getLogger(__name__)

# Create dedicated event engine logger
event_engine_logger = logging.getLogger('event_engine')
event_engine_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent.parent.parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Create file handler for event engine logs
event_engine_handler = logging.FileHandler(logs_dir / 'event_engine.log')
event_engine_handler.setLevel(logging.INFO)

# Create formatter
event_engine_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
event_engine_handler.setFormatter(event_engine_formatter)

# Add handler to logger
event_engine_logger.addHandler(event_engine_handler)


class EventDrivenStrategyEngine(StandardizedLoggingMixin):
    """
    Event-driven strategy engine using the new component architecture.
    
    This engine orchestrates all 9 components in a coordinated manner:
    1. Data Provider loads mode-specific data
    2. Position Monitor tracks balances
    3. Exposure Monitor calculates exposures
    4. Risk Monitor assesses risks
    5. P&L Calculator tracks performance
    6. Strategy Manager makes decisions
    7. Execution Managers execute trades
    8. Event Logger records everything
    """
    
    def __init__(self, 
                 config: Dict[str, Any], 
                 execution_mode: str, 
                 data_provider,
                 initial_capital: float,
                 share_class: str,
                 # Component references - following reference-based architecture
                 position_monitor=None,
                 event_logger=None,
                 exposure_monitor=None,
                 risk_monitor=None,
                 pnl_calculator=None,
                 strategy_manager=None,
                 position_update_handler=None,
                 results_store=None,
                 utility_manager=None,
                 debug_mode: bool = False):
        """
        Initialize event engine with injected configuration and data.
        
        Phase 3: All parameters injected from API request, no defaults.
        
        Args:
            config: Strategy configuration (from API request via config_manager)
            execution_mode: 'backtest' or 'live' (from startup config)
            data_provider: Pre-loaded data provider with all data in memory
            initial_capital: Initial capital from API request (NO DEFAULT)
            share_class: Share class from API request (NO DEFAULT)
        """
        self.config = config
        self.mode = config.get('mode')
        self.share_class = share_class
        self.initial_capital = initial_capital
        self.execution_mode = execution_mode
        self.data_provider = data_provider  # Pre-loaded data provider
        self.debug_mode = debug_mode
        self.health_status = "healthy"
        self.error_count = 0
        
        # Store component references - following reference-based architecture
        # Create components if not provided (for backtest service compatibility)
        
        # Initialize Execution Interface Factory first (required for Position Monitor)
        self.execution_interface_factory = self._create_execution_interface_factory()
        
        # Create components with proper dependency order
        self.position_monitor = position_monitor or self._create_position_monitor()
        self.event_logger = event_logger or self._create_event_logger()
        self.exposure_monitor = exposure_monitor or self._create_exposure_monitor()
        self.risk_monitor = risk_monitor or self._create_risk_monitor()
        self.pnl_calculator = pnl_calculator or self._create_pnl_calculator()
        self.strategy_manager = strategy_manager or self._create_strategy_manager()
        self.position_update_handler = position_update_handler or self._create_position_update_handler()
        self.results_store = results_store or self._create_results_store()
        self.utility_manager = utility_manager or self._create_utility_manager()
        
        # Validate required parameters (FAIL FAST)
        if not self.mode:
            raise ValueError("Mode is required in config")
        
        if not initial_capital or initial_capital <= 0:
            raise ValueError(f"Invalid initial_capital: {initial_capital}. Must be > 0.")
        
        if share_class not in ['USDT', 'ETH']:
            raise ValueError(f"Invalid share_class: {share_class}. Must be 'USDT' or 'ETH'.")
        
        if not data_provider:
            raise ValueError("Data provider is required")
        
        # Validate component references (FAIL FAST)
        if not self.position_monitor:
            raise ValueError("Position monitor reference is required")
        if not self.event_logger:
            raise ValueError("Event logger reference is required")
        if not self.exposure_monitor:
            raise ValueError("Exposure monitor reference is required")
        if not self.risk_monitor:
            raise ValueError("Risk monitor reference is required")
        if not self.pnl_calculator:
            raise ValueError("P&L calculator reference is required")
        if not self.strategy_manager:
            raise ValueError("Strategy manager reference is required")
        if not self.results_store:
            raise ValueError("Results store reference is required")
        if not self.utility_manager:
            raise ValueError("Utility manager reference is required")
        
        # Event loop state
        self.current_timestamp = None
        self.is_running = False
        
        logger.info(f"EventDrivenStrategyEngine initialized: {self.mode} mode, {share_class} share class, {initial_capital} capital")
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.error_count += 1
        error_code = f"EDSE_ERROR_{self.error_count:04d}"
        
        logger.error(f"Event Driven Strategy Engine error {error_code}: {str(error)}", extra={
            'error_code': error_code,
            'context': context,
            'execution_mode': self.execution_mode,
            'component': self.__class__.__name__
        })
        
        # Update health status based on error count
        if self.error_count > 10:
            self.health_status = "unhealthy"
        elif self.error_count > 5:
            self.health_status = "degraded"
    
    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            'status': self.health_status,
            'error_count': self.error_count,
            'mode': self.mode,
            'share_class': self.share_class,
            'execution_mode': self.execution_mode,
            'is_running': self.is_running,
            'component': self.__class__.__name__
        }

    def _process_config_driven_operations(self, operations: List[Dict]) -> List[Dict]:
        """Process operations based on configuration settings."""
        processed_operations = []
        for operation in operations:
            if self._validate_operation(operation):
                processed_operations.append(operation)
            else:
                self._handle_error(ValueError(f"Invalid operation: {operation}"), "config_driven_validation")
        return processed_operations
    
    def _validate_operation(self, operation: Dict) -> bool:
        """Validate operation against configuration."""
        required_fields = ['action', 'component', 'timestamp']
        return all(field in operation for field in required_fields)
    
    def _initialize_components(self):
        """
        Initialize all components with proper configuration and dependency tracking.
        
        Phase 3: Components initialized in dependency order with injected parameters.
        """
        # Health check functions now handled by unified health manager
        
        initialized_components = []
        
        try:
            # Component 1: Position Monitor (foundational - others depend on it)
            logger.info("Initializing Position Monitor...")
            self.position_monitor = PositionMonitor(
                config=self.config,
                data_provider=self.data_provider,
                utility_manager=self.utility_manager
            )
            # Component health now handled by unified health manager
            initialized_components.append('position_monitor')
            logger.info("✅ Position Monitor initialized successfully")
            
        except Exception as e:
            # Component health now handled by unified health manager
            logger.error(f"❌ Position Monitor initialization failed: {e}")
            raise ValueError(f"Position Monitor initialization failed: {e}")
        
        try:
            # Component 2: Event Logger
            logger.info("Initializing Event Logger...")
            self.event_logger = EventLogger(
                config=self.config,
                data_provider=self.data_provider,
                utility_manager=self.utility_manager
            )
            # Component health now handled by unified health manager
            initialized_components.append('event_logger')
            logger.info("✅ Event Logger initialized successfully")
            
        except Exception as e:
            # Component health now handled by unified health manager
            logger.error(f"❌ Event Logger initialization failed: {e}")
            raise ValueError(f"Event Logger initialization failed: {e}")
        
        try:
            # Component 3: Exposure Monitor (depends on position_monitor and data_provider)
            logger.info("Initializing Exposure Monitor...")
            self.exposure_monitor = ExposureMonitor(
                config=self.config,
                data_provider=self.data_provider,
                utility_manager=self.utility_manager
            )
            # Component health now handled by unified health manager
            initialized_components.append('exposure_monitor')
            logger.info("✅ Exposure Monitor initialized successfully")
            
        except Exception as e:
            # Component health now handled by unified health manager
            logger.error(f"❌ Exposure Monitor initialization failed: {e}")
            raise ValueError(f"Exposure Monitor initialization failed: {e}")
        
        try:
            # Component 4: Risk Monitor (depends on position_monitor, exposure_monitor, data_provider)
            logger.info("Initializing Risk Monitor...")
            self.risk_monitor = RiskMonitor(
                config=self.config,
                data_provider=self.data_provider,
                utility_manager=self.utility_manager
            )
            # Component health now handled by unified health manager
            initialized_components.append('risk_monitor')
            logger.info("✅ Risk Monitor initialized successfully")
            
        except Exception as e:
            # Component health now handled by unified health manager
            logger.error(f"❌ Risk Monitor initialization failed: {e}")
            raise ValueError(f"Risk Monitor initialization failed: {e}")
        
        try:
            # Component 5: P&L Calculator
            logger.info("Initializing P&L Calculator...")
            self.pnl_calculator = PnLCalculator(
                config=self.config,
                share_class=self.share_class,
                initial_capital=self.initial_capital,
                data_provider=self.data_provider,
                utility_manager=self.utility_manager
            )
            # Component health now handled by unified health manager
            initialized_components.append('pnl_calculator')
            logger.info("✅ P&L Calculator initialized successfully")
            
        except Exception as e:
            # Component health now handled by unified health manager
            logger.error(f"❌ P&L Calculator initialization failed: {e}")
            raise ValueError(f"P&L Calculator initialization failed: {e}")
        
        logger.info(f"✅ All core components initialized successfully: {initialized_components}")
        
        # Phase 3: Data provider is injected, not created here
        # self.data_provider is already set from constructor injection
        
        try:
            # Component 6: Strategy Manager (depends on exposure_monitor and risk_monitor)
            logger.info("Initializing Strategy Manager...")
            from ..strategies.strategy_factory import StrategyFactory
            self.strategy_manager = StrategyFactory.create_strategy(
                mode=self.config.get('mode', 'pure_lending'),
                config=self.config,
                risk_monitor=self.risk_monitor,
                position_monitor=self.position_monitor,
                event_engine=self
            )
            # Component health now handled by unified health manager
            initialized_components.append('strategy_manager')
            logger.info("✅ Strategy Manager initialized successfully")
            
        except Exception as e:
            # Component health now handled by unified health manager
            logger.error(f"❌ Strategy Manager initialization failed: {e}")
            raise ValueError(f"Strategy Manager initialization failed: {e}")
        # Create execution interfaces using factory
        self.execution_interfaces = VenueInterfaceFactory.create_all_venue_interfaces(
            execution_mode=self.execution_mode,
            config=self.config,
            data_provider=self.data_provider
        )
        
        # Set dependencies for execution interfaces
        VenueInterfaceFactory.set_venue_dependencies(
            interfaces=self.execution_interfaces,
            position_monitor=self.position_monitor,
            event_logger=self.event_logger,
            data_provider=self.data_provider
        )
        
        # Legacy execution managers removed - using new execution interfaces instead
        
        # Update cross-references
        self.exposure_monitor.data_provider = self.data_provider
        
        # Initialize Position Update Handler for tight loop management
        try:
            logger.info("Initializing Position Update Handler...")
            self.position_update_handler = PositionUpdateHandler(
                config=self.config,
                position_monitor=self.position_monitor,
                exposure_monitor=self.exposure_monitor,
                risk_monitor=self.risk_monitor,
                pnl_calculator=self.pnl_calculator,
                execution_mode=self.execution_mode
            )
            logger.info("✅ Position Update Handler initialized successfully")
        except Exception as e:
            logger.error(f"❌ Position Update Handler initialization failed: {e}")
            raise ValueError(f"Position Update Handler initialization failed: {e}")
        
        # Set Position Update Handler on execution interfaces
        self._set_position_update_handler_on_interfaces()
        
        # Register components with health check system
        self._register_health_checkers()
        
        logger.info("All components initialized successfully")
    
    def _set_position_update_handler_on_interfaces(self):
        """Set Position Update Handler on all execution interfaces for tight loop management."""
        try:
            # Set on CEX interface
            if 'cex' in self.execution_interfaces:
                self.execution_interfaces['cex'].position_update_handler = self.position_update_handler
                logger.info("Position Update Handler set on CEX interface")
            
            # Set on OnChain interface
            if 'onchain' in self.execution_interfaces:
                self.execution_interfaces['onchain'].position_update_handler = self.position_update_handler
                logger.info("Position Update Handler set on OnChain interface")
            
            # Set on Transfer interface
            if 'transfer' in self.execution_interfaces:
                self.execution_interfaces['transfer'].position_update_handler = self.position_update_handler
                logger.info("Position Update Handler set on Transfer interface")
            
            logger.info("Position Update Handler set on all execution interfaces")
            
        except Exception as e:
            logger.error(f"Failed to set Position Update Handler on interfaces: {e}")
            raise
    
    def _register_health_checkers(self):
        """Register all components with the unified health check system."""
        try:
            from ..health import unified_health_manager
            
            # Register core components
            unified_health_manager.register_component(
                "position_monitor", 
                PositionMonitorHealthChecker(self.position_monitor)
            )
            unified_health_manager.register_component(
                "data_provider", 
                DataProviderHealthChecker(self.data_provider)
            )
            unified_health_manager.register_component(
                "risk_monitor", 
                RiskMonitorHealthChecker(self.risk_monitor)
            )
            unified_health_manager.register_component(
                "event_logger", 
                EventLoggerHealthChecker(self.event_logger)
            )
            
            logger.info("Health checkers registered with unified health manager")
        except Exception as e:
            logger.error(f"Failed to register health checkers: {e}")
    
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
            
        # TODO: [WORKFLOW_TIME_TRIGGERED] - Implement time-triggered workflow for backtest execution
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
                start_dt = start_ts.tz_convert('UTC')
            else:
                start_dt = start_ts.tz_localize('UTC')
                
            if end_ts.tz is not None:
                end_dt = end_ts.tz_convert('UTC')
            else:
                end_dt = end_ts.tz_localize('UTC')
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
                test_snapshot = data['market_data']
                if not test_snapshot or len(test_snapshot) <= 1:  # Only timestamp
                    raise ValueError(f"No market data available for start date {start_date}")
            except Exception as e:
                raise ValueError(f"No data available for backtest date range {start_date} to {end_date}: {e}")
            
            logger.info(f"Data loaded successfully for backtest")
            
            # Generate unique request ID for this backtest
            request_id = str(uuid.uuid4())
            
            # Start async results store
            await self.results_store.start()
            
            # Initialize results tracking (minimal for async storage)
            results = {
                'config': self.config,
                'start_date': start_date,
                'end_date': end_date
            }
            
            # Generate timestamps for backtest based on strategy mode
            # ML strategies use 5-minute intervals, others use hourly
            if self.mode in ['ml_btc_directional', 'ml_usdt_directional']:
                freq = '5min'  # 5-minute intervals for ML strategies
                logger.info("Using 5-minute intervals for ML strategy")
            else:
                freq = 'H'  # Hourly intervals for traditional strategies
                logger.info("Using hourly intervals for traditional strategy")
            
            timestamps = pd.date_range(
                start=start_dt,
                end=end_dt,
                freq=freq,
                tz='UTC'
            )
            
            logger.info(f"Running backtest for {len(timestamps)} timestamps from {start_date} to {end_date}")
            
            # Run backtest loop with component orchestration
            for timestamp in timestamps:
                try:
                    # Get market data snapshot for this timestamp using canonical pattern
                    data = self.data_provider.get_data(timestamp)
                    market_data = data['market_data']
                    self._process_timestep(timestamp, market_data, request_id)
                except Exception as e:
                    logger.warning(f"Skipping timestamp {timestamp} due to missing data: {e}")
                    continue
            
            # Save final results and event log
            final_results = self._calculate_final_results(results)
            await self.results_store.save_final_result(request_id, final_results)
            await self.results_store.save_event_log(request_id, self.event_logger.get_all_events())
            
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
            # 1. Get current position snapshot
            logger.info(f"Event Engine: About to call position_monitor.get_current_positions() for timestep {timestamp}")
            position_snapshot = self.position_monitor.get_current_positions()
            logger.info(f"Event Engine: Position snapshot type = {type(position_snapshot)}, is None = {position_snapshot is None}")
            if position_snapshot is not None:
                logger.info(f"Event Engine: Position snapshot keys = {list(position_snapshot.keys())}")
                # Log wallet balance for debugging
                wallet = position_snapshot.get('wallet', {})
                logger.info(f"Event Engine: Wallet USDT balance = {wallet.get('USDT', 0)}")
                # Log CEX balances for debugging  
                cex_accounts = position_snapshot.get('cex_accounts', {})
                for venue, balances in cex_accounts.items():
                    if balances:
                        logger.info(f"Event Engine: {venue} balances = {balances}")
            
            # Debug: Log position snapshot for each timestep
            if self.debug_mode:
                self.position_monitor.log_position_snapshot(timestamp, "TIMESTEP_START")
            
            # 2. Calculate current exposure using injected data provider
            exposure = self.exposure_monitor.calculate_exposure(
                timestamp=timestamp,
                position_snapshot=position_snapshot,
                market_data={}  # TODO: Pass actual market data
            )
            logger.info(f"Event Engine: Exposure calculated - type: {type(exposure)}, keys: {list(exposure.keys()) if isinstance(exposure, dict) else 'Not a dict'}")
            
            # 3. Assess risk using injected config and data
            # Enable debug logging if debug mode is enabled
            if self.debug_mode:
                logger.info(f"Event Engine: Enabling Risk Monitor debug logging")
                self.risk_monitor.enable_debug_logging()
            
            logger.info(f"Event Engine: Calling Risk Monitor assess_risk")
            risk_assessment = self.risk_monitor.assess_risk(
                exposure_data=exposure,
                market_data=market_data
            )
            logger.info(f"Event Engine: Risk Monitor assess_risk completed")
            
            # 4. Calculate P&L using injected config
            logger.info(f"Event Engine: About to calculate P&L for timestamp {timestamp}")
            logger.info(f"Event Engine: P&L input - exposure type: {type(exposure)}, exposure value: {exposure}")
            try:
                pnl = self.pnl_calculator.get_current_pnl(
                    current_exposure=exposure,
                    timestamp=timestamp
                )
                logger.info(f"Event Engine: P&L calculated successfully")
                logger.info(f"Event Engine: P&L structure keys: {list(pnl.keys())}")
                if 'balance_based' in pnl:
                    logger.info(f"Event Engine: Balance-based P&L keys: {list(pnl['balance_based'].keys())}")
                    logger.info(f"Event Engine: P&L calculated - balance_based pnl_cumulative: {pnl.get('balance_based', {}).get('pnl_cumulative', 0)}")
                else:
                    logger.warning(f"Event Engine: P&L result missing 'balance_based' key: {pnl}")
            except Exception as e:
                logger.error(f"Event Engine: P&L calculation failed: {e}")
                # Create a default P&L structure to avoid downstream errors
                pnl = {
                    'balance_based': {'pnl_cumulative': 0.0, 'pnl_pct': 0.0},
                    'attribution': {'pnl_cumulative': 0.0},
                    'error': str(e)
                }
            
            # 5. Make strategy decision
            strategy_decision = self.strategy_manager.make_strategy_decision(
                current_exposure=exposure,
                risk_assessment=risk_assessment,
                config=self.config,
                market_data=market_data
            )
            
            # 6. Execute trades if needed (via execution interfaces)
            action = strategy_decision.get('action')
            logger.info(f"Event Engine: Strategy decision action = {action}")
            if action not in ['HOLD', 'MAINTAIN_NEUTRAL', 'NO_ACTION']:
                logger.info(f"Event Engine: Executing strategy decision: {strategy_decision}")
                self._execute_strategy_decision(strategy_decision, timestamp, market_data)
                
                # Note: Fast path balance updates are now handled in Strategy Manager after each instruction block
            else:
                logger.info(f"Event Engine: No action needed for {action}")
            
            # 7. Log events (async I/O - handled separately)
            self._log_timestep_event(timestamp, exposure, risk_assessment, pnl, strategy_decision)
            
            # 8. Store results (async I/O - handled separately)
            self._store_timestep_result(request_id, timestamp, exposure, risk_assessment, pnl, strategy_decision, action)
            
        except Exception as e:
            logger.error(f"Error processing timestep {timestamp}: {e}")
            # Log error event (async I/O - handled separately)
            self._log_error_event(timestamp, str(e))

    def _execute_strategy_decision(self, decision: Dict, timestamp: pd.Timestamp, market_data: Dict):
        """Execute a strategy decision by delegating to Strategy Manager."""
        action = decision.get('action')
        
        if action in ['MAINTAIN_NEUTRAL', 'HOLD', 'NO_ACTION']:
            # No execution needed - just maintain current position
            logger.debug(f"No execution needed for action: {action}")
        else:
            # Delegate all execution to Strategy Manager with market data
            # Note: Strategy Manager doesn't have execute_decision method yet
            # For now, just log the decision
            logger.info(f"Strategy decision to execute: {decision}")
            # TODO: Implement strategy execution when Strategy Manager is complete
    
    # REMOVED: Other legacy async methods that can be implemented later
    # _initialize_pure_lending_positions, _update_ausdt_balance,
    # execute_trade_with_interface, get_balance_with_interface, get_position_with_interface,
    # execute_transfer_with_interface - these are interface methods, not core orchestration
    
    def _calculate_final_results(self, results: Dict) -> Dict[str, Any]:
        """Calculate final backtest results."""
        
        # Get current position and calculate exposure for P&L calculation
        current_position = self.position_monitor.get_current_positions(self.current_timestamp)
        final_exposure = self.exposure_monitor.calculate_exposure(
            timestamp=self.current_timestamp,
            position_snapshot=current_position,
            market_data={}  # TODO: Pass actual market data
        )
        final_pnl = self.pnl_calculator.get_current_pnl(final_exposure, timestamp=self.current_timestamp)
        
        # Calculate performance metrics
        initial_capital = self.initial_capital
        pnl_cumulative = final_pnl.get('balance_based', {}).get('pnl_cumulative', 0.0)
        logger.info(f"Final results calculation - initial_capital: {initial_capital}, pnl_cumulative: {pnl_cumulative}")
        logger.info(f"Final P&L structure: {final_pnl}")
        
        final_value = initial_capital + pnl_cumulative
        total_return = pnl_cumulative
        total_return_pct = (total_return / initial_capital) * 100 if initial_capital > 0 else 0
        
        # Get all events
        all_events = self.event_logger.get_all_events()
        
        final_results = {
            'performance': {
                'total_return': total_return,
                'total_return_pct': total_return_pct,
                'initial_capital': initial_capital,
                'final_value': final_value
            },
            'final_pnl': final_pnl,
            'final_position': current_position,
            'events': all_events,
            'config': self.config,
            'start_date': results['start_date'],
            'end_date': results['end_date'],
            'mode': self.mode,
            'share_class': self.share_class
        }
        
        logger.info(f"Event Engine: Final results calculated - total_return: {total_return}, final_value: {final_value}")
        return final_results
    
    async def run_live(self):
        """Run the strategy in live mode."""
        logger.info("Starting live strategy execution")
        self.is_running = True
        
        try:
            while self.is_running:
                # Get current market data using canonical pattern
                current_timestamp = pd.Timestamp.now(tz='UTC')
                data = self.data_provider.get_data(current_timestamp)
                current_data = data['market_data']
                
                # Process current timestep
                await self._process_timestep(
                    current_timestamp,
                    current_data,
                    {}
                )
                
                # Wait for next update cycle
                await asyncio.sleep(60)  # Update every minute
                
        except Exception as e:
            logger.error(f"Live execution failed: {e}")
            raise
        finally:
            self.is_running = False
    
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
        if self.execution_mode == 'backtest':
            # In backtest mode, return the current timestamp from the loop
            if self.current_timestamp is not None:
                return self.current_timestamp
            else:
                # Fallback to current time if not in backtest loop
                return pd.Timestamp.now(tz='UTC')
        else:
            # In live mode, return current time
            return pd.Timestamp.now(tz='UTC')
    
    def _trigger_tight_loop(self):
        """
        Trigger tight loop execution reconciliation pattern.
        
        The tight loop ensures that each execution instruction is followed by
        position reconciliation before proceeding to the next instruction.
        
        Tight Loop = execution → position_monitor → reconciliation → next instruction
        """
        try:
            logger.info("Triggering tight loop reconciliation")
            
            # Get current position state
            if self.position_monitor:
                current_position = self.position_monitor.get_current_positions()
                logger.debug(f"Current position state: {current_position}")
            
            # Verify position reconciliation
            if self.position_monitor and hasattr(self.position_monitor, 'verify_reconciliation'):
                reconciliation_result = self.position_monitor.verify_reconciliation()
                if reconciliation_result.get('status') != 'success':
                    logger.warning(f"Position reconciliation failed: {reconciliation_result}")
                    return {'status': 'failed', 'reason': 'reconciliation_failed'}
            
            logger.info("Tight loop reconciliation completed successfully")
            return {'status': 'success', 'message': 'Tight loop reconciliation completed'}
            
        except Exception as e:
            logger.error(f"Tight loop reconciliation failed: {e}")
            return {'status': 'failed', 'reason': str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current status of all components with health information."""
        # Get system health report
        health_report = await system_health_aggregator.get_system_health()
        
        return {
            'mode': self.mode,
            'share_class': self.share_class,
            'execution_mode': self.execution_mode,
            'initial_capital': self.config.get('initial_capital', 100000),
            'is_running': self.is_running,
            'current_timestamp': self.current_timestamp,
            'health': {
                'overall_status': health_report['status'],
                'timestamp': health_report['timestamp'],
                'summary': health_report['summary'],
                'components': health_report['components']
            },
            'components': {
                'position_monitor': 'active',
                'event_logger': 'active',
                'exposure_monitor': 'active',
                'risk_monitor': 'active',
                'pnl_calculator': 'active',
                'strategy_manager': 'active',
                'cex_execution_interface': 'active',
                'onchain_execution_interface': 'active',
                'transfer_execution_interface': 'active',
                'data_provider': 'active'
            }
        }
    
    def _debug_print_position_monitor(self):
        """Print detailed position monitor state for debugging."""
        if not self.debug_mode:
            return
            
        print("\n" + "="*80)
        print("🔍 DEBUG MODE - POSITION MONITOR STATE")
        print("="*80)
        
        try:
            snapshot = self.position_monitor.get_current_positions()
            
            print(f"📊 Position Monitor Snapshot:")
            print(f"   Last Updated: {snapshot.get('last_updated', 'N/A')}")
            
            # Wallet balances
            print(f"\n💰 Wallet Balances:")
            wallet = snapshot.get('wallet', {})
            for token, balance in wallet.items():
                if balance != 0:  # Only show non-zero balances
                    print(f"   {token}: {balance:,.6f}")
            
            # CEX accounts
            print(f"\n🏦 CEX Account Balances:")
            cex_accounts = snapshot.get('cex_accounts', {})
            for exchange, tokens in cex_accounts.items():
                print(f"   {exchange.upper()}:")
                for token, balance in tokens.items():
                    if balance != 0:  # Only show non-zero balances
                        print(f"     {token}: {balance:,.6f}")
            
            # Perpetual positions
            print(f"\n📈 Perpetual Positions:")
            perp_positions = snapshot.get('perp_positions', {})
            for exchange, positions in perp_positions.items():
                if positions:  # Only show exchanges with positions
                    print(f"   {exchange.upper()}:")
                    for instrument, position in positions.items():
                        print(f"     {instrument}:")
                        print(f"       Size: {position.get('size', 0):,.6f}")
                        print(f"       Entry Price: {position.get('entry_price', 0):,.6f}")
                        print(f"       Entry Time: {position.get('entry_timestamp', 'N/A')}")
                        print(f"       Notional USD: ${position.get('notional_usd', 0):,.2f}")
                else:
                    print(f"   {exchange.upper()}: No positions")
            
            print("="*80)
            print("🔍 END DEBUG MODE")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"\n❌ DEBUG ERROR: Failed to get position monitor state: {e}\n")
    
    def _log_timestep_event(self, timestamp: pd.Timestamp, exposure: Dict, risk_assessment: Dict, pnl: Dict, strategy_decision: Dict):
        """Log timestep event asynchronously (I/O operation)."""
        try:
            # Schedule async logging (non-blocking)
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, schedule the coroutine
                asyncio.create_task(self.event_logger.log_event(
                    event_type='TIMESTEP_PROCESSED',
                    event_data={
                        'venue': 'system',
                        'token': None,
                        'exposure': exposure,
                        'risk': risk_assessment,
                        'pnl': pnl,
                        'decision': strategy_decision
                    },
                    timestamp=timestamp
                ))
            else:
                # If we're not in an async context, run it
                loop.run_until_complete(self.event_logger.log_event(
                    event_type='TIMESTEP_PROCESSED',
                    event_data={
                        'venue': 'system',
                        'token': None,
                        'exposure': exposure,
                        'risk': risk_assessment,
                        'pnl': pnl,
                        'decision': strategy_decision
                    },
                    timestamp=timestamp
                ))
        except Exception as e:
            logger.error(f"Failed to log timestep event: {e}")
    
    def _store_timestep_result(self, request_id: str, timestamp: pd.Timestamp, exposure: Dict, risk_assessment: Dict, pnl: Dict, strategy_decision: Dict, action: str):
        """Store timestep result asynchronously (I/O operation)."""
        try:
            # Schedule async storage (non-blocking)
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, schedule the coroutine
                asyncio.create_task(self.results_store.save_timestep_result(
                    request_id=request_id,
                    timestamp=timestamp,
                    data={
                        'pnl': pnl,
                        'exposure': exposure,
                        'risk': risk_assessment,
                        'decision': strategy_decision,
                        'event_type': 'TIMESTEP_PROCESSED'
                    }
                ))
            else:
                # If we're not in an async context, run it
                loop.run_until_complete(self.results_store.save_timestep_result(
                    request_id=request_id,
                    timestamp=timestamp,
                    data={
                        'pnl': pnl,
                        'exposure': exposure,
                        'risk': risk_assessment,
                        'decision': strategy_decision,
                        'event_type': 'TIMESTEP_PROCESSED'
                    }
                ))
        except Exception as e:
            logger.error(f"Failed to store timestep result: {e}")
    
    def _log_error_event(self, timestamp: pd.Timestamp, error_message: str):
        """Log error event asynchronously (I/O operation)."""
        try:
            # Schedule async logging (non-blocking)
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, schedule the coroutine
                asyncio.create_task(self.event_logger.log_event(
                    event_type='ERROR',
                    event_data={
                        'venue': 'system',
                        'token': None,
                        'error': error_message
                    },
                    timestamp=timestamp
                ))
            else:
                # If we're not in an async context, run it
                loop.run_until_complete(self.event_logger.log_event(
                    event_type='ERROR',
                    event_data={
                        'venue': 'system',
                        'token': None,
                        'error': error_message
                    },
                    timestamp=timestamp
                ))
        except Exception as e:
            logger.error(f"Failed to log error event: {e}")


# REMOVED: create_event_driven_strategy_engine convenience function
# Phase 3: EventDrivenStrategyEngine now requires injected parameters from API request:
# - config (from config_manager)
# - execution_mode (from startup config)  
# - data_provider (from data_provider_factory)
# - initial_capital (from API request)
# - share_class (from API request)
# Use direct constructor with proper dependency injection instead

    def _create_execution_interface_factory(self):
        """Create execution interface factory."""
        from ..interfaces.venue_interface_factory import VenueInterfaceFactory
        return VenueInterfaceFactory()
    
    def _create_position_monitor(self):
        """Create position monitor component."""
        from ..components.position_monitor import PositionMonitor
        from ...core.utilities.utility_manager import UtilityManager
        utility_manager = UtilityManager(self.config, self.data_provider)
        return PositionMonitor(
            self.config, 
            self.data_provider, 
            utility_manager, 
            self.execution_interface_factory
        )
    
    def _create_event_logger(self):
        """Create event logger component."""
        from ...infrastructure.logging.event_logger import EventLogger
        from ...core.utilities.utility_manager import UtilityManager
        utility_manager = UtilityManager(self.config, self.data_provider)
        return EventLogger(self.config, self.data_provider, utility_manager)
    
    def _create_exposure_monitor(self):
        """Create exposure monitor component."""
        from ..components.exposure_monitor import ExposureMonitor
        from ...core.utilities.utility_manager import UtilityManager
        utility_manager = UtilityManager(self.config, self.data_provider)
        return ExposureMonitor(self.config, self.data_provider, utility_manager)
    
    def _create_risk_monitor(self):
        """Create risk monitor component."""
        from ..components.risk_monitor import RiskMonitor
        from ...core.utilities.utility_manager import UtilityManager
        utility_manager = UtilityManager(self.config, self.data_provider)
        return RiskMonitor(self.config, self.data_provider, utility_manager)
    
    def _create_pnl_calculator(self):
        """Create P&L calculator component."""
        from ..math.pnl_calculator import PnLCalculator
        return PnLCalculator(self.config, self.share_class, self.initial_capital)
    
    def _create_strategy_manager(self):
        """Create strategy manager component."""
        from ..strategies.strategy_factory import StrategyFactory
        return StrategyFactory.create_strategy(
            mode=self.config.get('mode', 'pure_lending'),
            config=self.config,
            risk_monitor=self.risk_monitor,
            position_monitor=self.position_monitor,
            event_engine=self
        )
    
    def _create_position_update_handler(self):
        """Create position update handler component."""
        from ..components.position_update_handler import PositionUpdateHandler
        return PositionUpdateHandler(
            self.config,
            self.position_monitor,
            self.exposure_monitor,
            self.risk_monitor,
            self.pnl_calculator
        )
    
    def _create_results_store(self):
        """Create results store component."""
        from ...infrastructure.persistence.async_results_store import AsyncResultsStore
        return AsyncResultsStore("results", self.execution_mode)
    
    def _create_utility_manager(self):
        """Create utility manager component."""
        from ...core.utilities.utility_manager import UtilityManager
        return UtilityManager(self.config, self.data_provider)
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs) -> None:
        """
        Update state for all components.
        
        Args:
            timestamp: Current timestamp
            trigger_source: Source of the update trigger
            **kwargs: Additional update parameters
        """
        try:
            # Update all components with the new timestamp
            if self.position_monitor:
                self.position_monitor.update_state(timestamp, trigger_source, **kwargs)
            
            if self.event_logger:
                self.event_logger.update_state(timestamp, trigger_source, **kwargs)
            
            if self.exposure_monitor:
                self.exposure_monitor.update_state(timestamp, trigger_source, **kwargs)
            
            if self.risk_monitor:
                self.risk_monitor.update_state(timestamp, trigger_source, **kwargs)
            
            if self.pnl_calculator:
                self.pnl_calculator.update_state(timestamp, trigger_source, **kwargs)
            
            # Update execution interfaces
            if self.execution_interfaces:
                for interface_type, interface in self.execution_interfaces.items():
                    if interface and hasattr(interface, 'update_state'):
                        interface.update_state(timestamp, trigger_source, **kwargs)
            
            logger.debug(f"EventDrivenStrategyEngine.update_state completed at {timestamp} from {trigger_source}")
            
        except Exception as e:
            logger.error(f"Failed to update state in EventDrivenStrategyEngine: {e}")
            raise
    
    async def initialize_engine(self, config: Dict[str, Any], execution_mode: str) -> Dict[str, Any]:
        """
        Initialize all components in dependency order.
        
        Parameters:
        - config: Strategy configuration
        - execution_mode: Execution mode (backtest/live)
        
        Returns:
        - Dict: Initialization results with component status
        """
        try:
            logger.info(f"Initializing EventDrivenStrategyEngine in {execution_mode} mode")
            
            # Store configuration
            self.config = config
            self.execution_mode = execution_mode
            
            # Initialize components in dependency order
            initialization_results = {}
            
            # 1. Initialize Data Provider (shared)
            from ...infrastructure.data.base_data_provider import BaseDataProvider
            self.data_provider = BaseDataProvider(execution_mode, config)
            initialization_results['data_provider'] = 'initialized'
            
            # 2. Initialize Position Monitor (foundation)
            self.position_monitor = PositionMonitor(config, self.data_provider, None)
            initialization_results['position_monitor'] = 'initialized'
            
            # 3. Initialize Event Logger
            self.event_logger = EventLogger(config)
            initialization_results['event_logger'] = 'initialized'
            
            # 4. Initialize Exposure Monitor
            self.exposure_monitor = ExposureMonitor(config, self.data_provider, None)
            initialization_results['exposure_monitor'] = 'initialized'
            
            # 5. Initialize Risk Monitor
            self.risk_monitor = RiskMonitor(config, self.data_provider, None)
            initialization_results['risk_monitor'] = 'initialized'
            
            # 6. Initialize PnL Calculator
            self.pnl_calculator = PnLCalculator(config, None)
            initialization_results['pnl_calculator'] = 'initialized'
            
            # 7. Initialize Strategy Manager
            self.strategy_manager = BaseStrategyManager(config, self.data_provider, self.exposure_monitor, self.risk_monitor)
            initialization_results['strategy_manager'] = 'initialized'
            
            # 8. Initialize Position Update Handler
            self.position_update_handler = PositionUpdateHandler(
                config, self.position_monitor, self.exposure_monitor, 
                self.risk_monitor, self.pnl_calculator, execution_mode
            )
            initialization_results['position_update_handler'] = 'initialized'
            
            # 9. Initialize Execution Interfaces (if needed)
            # Note: Execution interfaces are initialized by VenueManager
            initialization_results['execution_interfaces'] = 'deferred'
            
            # Set initialization status
            self.initialized = True
            self.initialization_timestamp = pd.Timestamp.now(tz='UTC')
            
            logger.info(f"EventDrivenStrategyEngine initialized successfully with {len(initialization_results)} components")
            
            return {
                'success': True,
                'components_initialized': initialization_results,
                'execution_mode': execution_mode,
                'initialization_timestamp': self.initialization_timestamp
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize EventDrivenStrategyEngine: {e}")
            return {
                'success': False,
                'error': str(e),
                'components_initialized': initialization_results if 'initialization_results' in locals() else {}
            }