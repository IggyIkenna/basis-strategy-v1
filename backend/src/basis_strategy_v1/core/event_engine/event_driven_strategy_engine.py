"""
New Event-Driven Strategy Engine using the new component architecture.

This engine wires together all 9 components:
- Position Monitor (Agent A)
- Event Logger (Agent A) 
- Exposure Monitor (Agent A)
- Risk Monitor (Agent A)
- P&L Calculator (Agent A)
- Strategy Manager (Agent B)
- CEX Execution Manager (Agent B)
- OnChain Execution Manager (Agent B)
- Data Provider (Agent B)
"""

import asyncio
import logging
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from pathlib import Path

# Import the new components
from ..strategies.components.position_monitor import PositionMonitor
from ..strategies.components.event_logger import EventLogger
from ..strategies.components.exposure_monitor import ExposureMonitor
from ..strategies.components.risk_monitor import RiskMonitor
from ..math.pnl_calculator import PnLCalculator
from ..strategies.components.strategy_manager import StrategyManager
from ..strategies.components.position_update_handler import PositionUpdateHandler
# Legacy execution managers removed - using new execution interfaces instead
from ..interfaces.execution_interface_factory import ExecutionInterfaceFactory
from ..health import (
    system_health_aggregator,
    PositionMonitorHealthChecker,
    DataProviderHealthChecker,
    RiskMonitorHealthChecker,
    EventLoggerHealthChecker
)

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
    7. Execution Managers execute trades
    8. Event Logger records everything
    """
    
    def __init__(self, 
                 config: Dict[str, Any], 
                 execution_mode: str, 
                 data_provider,
                 initial_capital: float,
                 share_class: str,
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
        
        # Initialize global market data utils with data provider
        from ..utils.market_data_utils import set_global_data_provider
        set_global_data_provider(data_provider)
        
        # Validate required parameters (FAIL FAST)
        if not self.mode:
            raise ValueError("Mode is required in config")
        
        if not initial_capital or initial_capital <= 0:
            raise ValueError(f"Invalid initial_capital: {initial_capital}. Must be > 0.")
        
        if share_class not in ['USDT', 'ETH']:
            raise ValueError(f"Invalid share_class: {share_class}. Must be 'USDT' or 'ETH'.")
        
        if not data_provider:
            raise ValueError("Data provider is required")
        
        # Initialize all components with proper dependency injection
        self._initialize_components()
        
        # Event loop state
        self.current_timestamp = None
        self.is_running = False
        
        logger.info(f"EventDrivenStrategyEngine initialized: {self.mode} mode, {share_class} share class, {initial_capital} capital")
    

    def _initialize_components(self):
        """
        Initialize all components with proper configuration and dependency tracking.
        
        Phase 3: Components initialized in dependency order with injected parameters.
        """
        from ...infrastructure.config.health_check import mark_component_healthy, mark_component_unhealthy
        
        initialized_components = []
        
        try:
            # Component 1: Position Monitor (foundational - others depend on it)
            logger.info("Initializing Position Monitor...")
            self.position_monitor = PositionMonitor(
                config=self.config,
                execution_mode=self.execution_mode,
                initial_capital=self.initial_capital,  # From API request
                share_class=self.share_class,  # From API request
                data_provider=self.data_provider,
                debug_mode=self.debug_mode
            )
            mark_component_healthy('position_monitor')
            initialized_components.append('position_monitor')
            logger.info("✅ Position Monitor initialized successfully")
            
        except Exception as e:
            mark_component_unhealthy('position_monitor', str(e))
            logger.error(f"❌ Position Monitor initialization failed: {e}")
            raise ValueError(f"Position Monitor initialization failed: {e}")
        
        try:
            # Component 2: Event Logger
            logger.info("Initializing Event Logger...")
            self.event_logger = EventLogger(
                execution_mode=self.execution_mode
            )
            mark_component_healthy('event_logger')
            initialized_components.append('event_logger')
            logger.info("✅ Event Logger initialized successfully")
            
        except Exception as e:
            mark_component_unhealthy('event_logger', str(e))
            # Mark downstream components as unhealthy
            for downstream in ['exposure_monitor', 'risk_monitor', 'pnl_calculator']:
                mark_component_unhealthy(downstream, f"Dependency event_logger failed: {e}")
            logger.error(f"❌ Event Logger initialization failed: {e}")
            raise ValueError(f"Event Logger initialization failed: {e}")
        
        try:
            # Component 3: Exposure Monitor (depends on position_monitor and data_provider)
            logger.info("Initializing Exposure Monitor...")
            self.exposure_monitor = ExposureMonitor(
                config=self.config,
                share_class=self.share_class,
                position_monitor=self.position_monitor,
                data_provider=self.data_provider,
                debug_mode=self.debug_mode
            )
            mark_component_healthy('exposure_monitor')
            initialized_components.append('exposure_monitor')
            logger.info("✅ Exposure Monitor initialized successfully")
            
        except Exception as e:
            mark_component_unhealthy('exposure_monitor', str(e))
            # Mark downstream components as unhealthy
            for downstream in ['risk_monitor', 'pnl_calculator']:
                mark_component_unhealthy(downstream, f"Dependency exposure_monitor failed: {e}")
            logger.error(f"❌ Exposure Monitor initialization failed: {e}")
            raise ValueError(f"Exposure Monitor initialization failed: {e}")
        
        try:
            # Component 4: Risk Monitor (depends on position_monitor, exposure_monitor, data_provider)
            logger.info("Initializing Risk Monitor...")
            self.risk_monitor = RiskMonitor(
                config=self.config,
                position_monitor=self.position_monitor,
                exposure_monitor=self.exposure_monitor,
                data_provider=self.data_provider,
                share_class=self.share_class,
                debug_mode=self.debug_mode
            )
            mark_component_healthy('risk_monitor')
            initialized_components.append('risk_monitor')
            logger.info("✅ Risk Monitor initialized successfully")
            
        except Exception as e:
            mark_component_unhealthy('risk_monitor', str(e))
            logger.error(f"❌ Risk Monitor initialization failed: {e}")
            raise ValueError(f"Risk Monitor initialization failed: {e}")
        
        try:
            # Component 5: P&L Calculator
            logger.info("Initializing P&L Calculator...")
            self.pnl_calculator = PnLCalculator(
                config=self.config,
                share_class=self.share_class,
                initial_capital=self.initial_capital  # From API request
            )
            # Inject data provider for funding rate lookups
            self.pnl_calculator.set_data_provider(self.data_provider)
            mark_component_healthy('pnl_calculator')
            initialized_components.append('pnl_calculator')
            logger.info("✅ P&L Calculator initialized successfully")
            
        except Exception as e:
            mark_component_unhealthy('pnl_calculator', str(e))
            logger.error(f"❌ P&L Calculator initialization failed: {e}")
            raise ValueError(f"P&L Calculator initialization failed: {e}")
        
        logger.info(f"✅ All core components initialized successfully: {initialized_components}")
        
        # Phase 3: Data provider is injected, not created here
        # self.data_provider is already set from constructor injection
        
        try:
            # Component 6: Strategy Manager (depends on exposure_monitor and risk_monitor)
            logger.info("Initializing Strategy Manager...")
            self.strategy_manager = StrategyManager(
                config=self.config,
                exposure_monitor=self.exposure_monitor,
                risk_monitor=self.risk_monitor
            )
            mark_component_healthy('strategy_manager')
            initialized_components.append('strategy_manager')
            logger.info("✅ Strategy Manager initialized successfully")
            
        except Exception as e:
            mark_component_unhealthy('strategy_manager', str(e))
            logger.error(f"❌ Strategy Manager initialization failed: {e}")
            raise ValueError(f"Strategy Manager initialization failed: {e}")
        # Create execution interfaces using factory
        self.execution_interfaces = ExecutionInterfaceFactory.create_all_interfaces(
            execution_mode=self.execution_mode,
            config=self.config,
            data_provider=self.data_provider
        )
        
        # Set dependencies for execution interfaces
        ExecutionInterfaceFactory.set_interface_dependencies(
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
        """Register all components with the health check system."""
        try:
            # Register core components
            system_health_aggregator.register_component(
                "position_monitor", 
                PositionMonitorHealthChecker(self.position_monitor)
            )
            system_health_aggregator.register_component(
                "data_provider", 
                DataProviderHealthChecker(self.data_provider)
            )
            system_health_aggregator.register_component(
                "risk_monitor", 
                RiskMonitorHealthChecker(self.risk_monitor)
            )
            system_health_aggregator.register_component(
                "event_logger", 
                EventLoggerHealthChecker(self.event_logger)
            )
            
            logger.info("Health checkers registered for all components")
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
                test_snapshot = self.data_provider.get_market_data_snapshot(start_dt)
                if not test_snapshot or len(test_snapshot) <= 1:  # Only timestamp
                    raise ValueError(f"No market data available for start date {start_date}")
            except Exception as e:
                raise ValueError(f"No data available for backtest date range {start_date} to {end_date}: {e}")
            
            logger.info(f"Data loaded successfully for backtest")
            
            # Initialize results tracking
            results = {
                'pnl_history': [],
                'events': [],
                'positions': [],
                'exposures': [],
                'risks': [],
                'config': self.config,
                'start_date': start_date,
                'end_date': end_date
            }
            
            # Generate hourly timestamps for backtest
            timestamps = pd.date_range(
                start=start_dt,
                end=end_dt,
                freq='H',
                tz='UTC'
            )
            
            logger.info(f"Running backtest for {len(timestamps)} timestamps from {start_date} to {end_date}")
            
            # Run backtest loop with component orchestration
            for timestamp in timestamps:
                try:
                    # Get market data snapshot for this timestamp
                    market_data = self.data_provider.get_market_data_snapshot(timestamp)
                    await self._process_timestep(timestamp, market_data, results)
                except Exception as e:
                    logger.warning(f"Skipping timestamp {timestamp} due to missing data: {e}")
                    continue
            
            # Calculate final results
            final_results = await self._calculate_final_results(results)
            
            logger.info("Backtest completed successfully")
            return final_results
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            raise
    
    async def _process_timestep(self, timestamp: pd.Timestamp, market_data: Dict, results: Dict):
        """
        Process a single timestep in the backtest - CORE EVENT BEHAVIOR.
        
        This is the critical orchestration method that coordinates all components
        for each timestamp in the backtest.
        """
        self.current_timestamp = timestamp
        
        try:
            # 1. Get current position snapshot
            logger.info(f"Event Engine: About to call position_monitor.get_snapshot() for timestep {timestamp}")
            position_snapshot = self.position_monitor.get_snapshot()
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
                market_data=market_data
            )
            logger.info(f"Event Engine: Exposure calculated - total_value_usd = {exposure.get('total_value_usd', 0)}")
            
            # 3. Assess risk using injected config and data
            # Enable debug logging if debug mode is enabled
            if self.debug_mode:
                logger.info(f"Event Engine: Enabling Risk Monitor debug logging")
                self.risk_monitor.enable_debug_logging()
            
            logger.info(f"Event Engine: Calling Risk Monitor assess_risk")
            risk_assessment = await self.risk_monitor.assess_risk(
                exposure_data=exposure,
                market_data=market_data
            )
            logger.info(f"Event Engine: Risk Monitor assess_risk completed")
            
            # 4. Calculate P&L using injected config
            logger.info(f"Event Engine: About to calculate P&L for timestamp {timestamp}")
            try:
                pnl = await self.pnl_calculator.calculate_pnl(
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
                await self._execute_strategy_decision(strategy_decision, timestamp, market_data)
                
                # Note: Fast path balance updates are now handled in Strategy Manager after each instruction block
            else:
                logger.info(f"Event Engine: No action needed for {action}")
            
            # 7. Log events
            await self.event_logger.log_event(
                timestamp=timestamp,
                event_type='TIMESTEP_PROCESSED',
                venue='system',
                token=None,
                data={
                    'exposure': exposure,
                    'risk': risk_assessment,
                    'pnl': pnl,
                    'decision': strategy_decision
                }
            )
            
            # 8. Store results
            results['pnl_history'].append({
                'timestamp': timestamp,
                'pnl': pnl
            })
            results['exposures'].append({
                'timestamp': timestamp,
                'exposure': exposure
            })
            results['risks'].append({
                'timestamp': timestamp,
                'risk': risk_assessment
            })
            results['events'].append({
                'timestamp': timestamp,
                'event_type': 'TIMESTEP_PROCESSED',
                'data': {
                    'exposure': exposure,
                    'risk': risk_assessment,
                    'pnl': pnl,
                    'decision': strategy_decision
                }
            })
            
        except Exception as e:
            logger.error(f"Error processing timestep {timestamp}: {e}")
            # Log error event
            await self.event_logger.log_event(
                timestamp=timestamp,
                event_type='ERROR',
                venue='system',
                token=None,
                data={'error': str(e)}
            )

    async def _execute_strategy_decision(self, decision: Dict, timestamp: pd.Timestamp, market_data: Dict):
        """Execute a strategy decision by delegating to Strategy Manager."""
        action = decision.get('action')
        
        if action in ['MAINTAIN_NEUTRAL', 'HOLD', 'NO_ACTION']:
            # No execution needed - just maintain current position
            logger.debug(f"No execution needed for action: {action}")
        else:
            # Delegate all execution to Strategy Manager with market data
            await self.strategy_manager.execute_decision(
                decision=decision,
                timestamp=timestamp,
                execution_interfaces=self.execution_interfaces,
                market_data=market_data
            )
    
    # REMOVED: Other legacy async methods that can be implemented later
    # _initialize_pure_lending_positions, _update_ausdt_balance,
    # execute_trade_with_interface, get_balance_with_interface, get_position_with_interface,
    # execute_transfer_with_interface - these are interface methods, not core orchestration
    
    async def _calculate_final_results(self, results: Dict) -> Dict[str, Any]:
        """Calculate final backtest results."""
        
        # Calculate performance metrics
        pnl_history = results['pnl_history']
        if not pnl_history:
            return {'error': 'No P&L data available'}
        
        initial_pnl = pnl_history[0]['pnl']['balance_based']['pnl_cumulative']
        final_pnl = pnl_history[-1]['pnl']['balance_based']['pnl_cumulative']
        total_return = final_pnl - initial_pnl
        
        # Get initial capital from config
        initial_capital = self.config.get('initial_capital', self.config.get('backtest', {}).get('initial_capital', 100000))
        total_return_pct = (total_return / initial_capital) * 100
        
        # Get all events
        all_events = self.event_logger.get_all_events()
        
        final_results = {
            'performance': {
                'total_return': total_return,
                'total_return_pct': total_return_pct,
                'initial_capital': initial_capital,
                'final_value': initial_capital + total_return
            },
            'pnl_history': pnl_history,
            'events': all_events,
            'exposures': results['exposures'],
            'risks': results['risks'],
            'config': self.config,
            'start_date': results['start_date'],
            'end_date': results['end_date'],
            'mode': self.mode,
            'share_class': self.share_class
        }
        
        logger.info(f"Event Engine: Final results calculated - total_return: {total_return}, final_value: {initial_capital + total_return}, pnl_history_length: {len(pnl_history)}")
        return final_results
    
    async def run_live(self):
        """Run the strategy in live mode."""
        logger.info("Starting live strategy execution")
        self.is_running = True
        
        try:
            while self.is_running:
                # Get current market data
                current_data = await self.data_provider.get_current_data()
                
                # Process current timestep
                await self._process_timestep(
                    pd.Timestamp.now(tz='UTC'),
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
    
    def stop(self):
        """Stop the live strategy execution."""
        self.is_running = False
        logger.info("Strategy execution stopped")
    
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
    
    def debug_print_position_monitor(self):
        """Print detailed position monitor state for debugging."""
        if not self.debug_mode:
            return
            
        print("\n" + "="*80)
        print("🔍 DEBUG MODE - POSITION MONITOR STATE")
        print("="*80)
        
        try:
            snapshot = self.position_monitor.get_snapshot()
            
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


# REMOVED: create_event_driven_strategy_engine convenience function
# Phase 3: EventDrivenStrategyEngine now requires injected parameters from API request:
# - config (from config_manager)
# - execution_mode (from startup config)  
# - data_provider (from data_provider_factory)
# - initial_capital (from API request)
# - share_class (from API request)
# Use direct constructor with proper dependency injection instead