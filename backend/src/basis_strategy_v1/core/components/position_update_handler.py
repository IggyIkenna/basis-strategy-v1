"""
Position Update Handler

Orchestrates the tight loop between position monitor updates and downstream components.
Performs actual reconciliation logic and coordinates the component chain.

Architecture:
- ExecutionManager: Orchestrates tight loop (Order → Execution → Reconciliation)
- PositionUpdateHandler: Owns reconciliation logic and performs actual reconciliation
- Position Monitor: Updates simulated and real positions with mode-specific triggers
- Component Chain: position → exposure → risk → pnl

Mode-Specific Behavior:
- Backtest Mode: Simulated positions = real positions (deep copy)
- Live Mode: Query real positions from venues, compare with simulated
- Reconciliation: Only in live mode (backtest always succeeds)

Reference: WORKFLOW_GUIDE.md - Tight Loop Architecture
"""

import logging
import pandas as pd
import os
import uuid
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from pathlib import Path

from ...infrastructure.logging.structured_logger import StructuredLogger
from ...infrastructure.logging.domain_event_logger import DomainEventLogger
from ...core.models.domain_events import ReconciliationEvent
from ...core.errors.error_codes import ERROR_REGISTRY
from ...core.errors.component_error import ComponentError

if TYPE_CHECKING:
    from .position_monitor import PositionMonitor
    from .exposure_monitor import ExposureMonitor
    from .risk_monitor import RiskMonitor
    from .pnl_monitor import PnLMonitor

logger = logging.getLogger(__name__)


class PositionUpdateHandler:
    """
    Orchestrates the tight loop between position monitor updates and downstream components.
    Performs actual reconciliation logic and coordinates the component chain.
    
    This class serves as the tight loop owner, performing reconciliation between
    simulated and real positions with mode-specific behavior per WORKFLOW_GUIDE.md.
    
    Singleton Pattern: Ensures single instance across the application.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict, data_provider: Any, execution_mode: str,
                 position_monitor: 'PositionMonitor', exposure_monitor: 'ExposureMonitor',
                 risk_monitor: 'RiskMonitor', pnl_monitor: 'PnLMonitor',
                 correlation_id: str = None, pid: int = None, log_dir: Path = None):
        """
        Initialize position update handler.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            execution_mode: Execution mode ('backtest' or 'live')
            position_monitor: Position monitor instance
            exposure_monitor: Exposure monitor instance
            risk_monitor: Risk monitor instance
            pnl_monitor: P&L calculator instance
        """
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        self.position_monitor = position_monitor
        self.exposure_monitor = exposure_monitor
        self.risk_monitor = risk_monitor
        self.pnl_monitor = pnl_monitor
        
        # Initialize logging infrastructure first
        self.correlation_id = correlation_id or str(uuid.uuid4().hex)
        self.pid = pid or os.getpid()
        self.log_dir = log_dir
        
        # Initialize structured logger
        self.logger = StructuredLogger(
            component_name="PositionUpdateHandler",
            correlation_id=self.correlation_id,
            pid=self.pid,
            log_dir=self.log_dir,
            engine=None
        )
        
        # Get position subscriptions from config
        position_config = config.get('component_config', {}).get('position_monitor', {})
        self.position_subscriptions = position_config.get('position_subscriptions', [])
        
        self.logger.info(f"PositionUpdateHandler subscribed to {len(self.position_subscriptions)} positions")
        
        # Initialize component-specific state
        self.tight_loop_active = False
        self.current_loop_timestamp = None
        self.loop_execution_count = 0
        
        # Health integration
        self.health_status = {
            'status': 'healthy',
            'last_check': datetime.now(),
            'ERROR_COUNT': 0,
            'success_count': 0
        }
        
        # Initialize domain event logger
        self.domain_event_logger = DomainEventLogger(
            self.log_dir, 
            correlation_id=self.correlation_id, 
            pid=self.pid
        ) if self.log_dir else None
        
        self.logger.info(f"PositionUpdateHandler initialized (mode-agnostic)")
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.health_status['ERROR_COUNT'] += 1
        
        # Determine error code based on context
        if 'reconciliation' in context.lower():
            error_code = 'PUH-001'
        elif 'timeout' in context.lower():
            error_code = 'PUH-002'
        elif 'orchestration' in context.lower():
            error_code = 'PUH-003'
        else:
            error_code = f"PUH-ERROR_{self.health_status['ERROR_COUNT']:04d}"
        
        # Log structured error
        self.logger.error(str(error), error_code=error_code, exc_info=error)
        
        # Update health status based on error count
        if self.health_status.get('error_count', 0) > 10:
            self.health_status['status'] = "unhealthy"
        elif self.health_status.get('error_count', 0) > 5:
            self.health_status['status'] = "degraded"
        
        # Raise ComponentError
        raise ComponentError(
            error_code=error_code,
            message=f'PositionUpdateHandler failed: {str(error)}',
            component='PositionUpdateHandler',
            severity='HIGH',
            original_exception=error
        )
    
    def _log_reconciliation_event(
        self,
        trigger_source: str,
        reconciliation_type: str,
        success: bool,
        simulated_positions: Dict[str, float],
        real_positions: Dict[str, float],
        mismatches: List[Dict[str, Any]],
        retry_attempt: Optional[int] = None,
        max_retries: Optional[int] = None
    ) -> None:
        """Log reconciliation event."""
        if not self.log_dir or not self.domain_event_logger:
            return
        
        timestamp = datetime.now().isoformat()
        real_utc = datetime.now(timezone.utc).isoformat()
        
        event = ReconciliationEvent(
            timestamp=timestamp,
            real_utc_time=real_utc,
            correlation_id=self.correlation_id,
            pid=self.pid,
            trigger_source=trigger_source,
            reconciliation_type=reconciliation_type,
            success=success,
            simulated_positions=simulated_positions,
            real_positions=real_positions,
            mismatches=mismatches,
            retry_attempt=retry_attempt,
            max_retries=max_retries,
            metadata={}
        )
        
        self.domain_event_logger.log_reconciliation(event)
    
    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            'status': self.health_status['status'],
            'error_count': self.health_status['error_count'],
            'success_count': self.health_status['success_count'],
            'tight_loop_active': self.tight_loop_active,
            'loop_execution_count': self.loop_execution_count,
            'component': self.__class__.__name__
        }
    
    def handle_position_update(self, changes: Dict, timestamp: pd.Timestamp, 
                              market_data: Dict = None, trigger_component: str = 'unknown') -> Dict:
        """
        Handle position monitor update and trigger the tight loop.
        PUBLIC METHOD - main entry point for position updates.
        
        This method orchestrates the tight loop with 2-trigger system per WORKFLOW_GUIDE.md:
        1. execution_manager: Tight loop orchestration with execution deltas
        2. position_refresh: Periodic position refresh (60s interval)
        
        Args:
            changes: Position changes to apply (execution deltas)
            timestamp: Current timestamp
            market_data: Market data for calculations
            trigger_component: Component that triggered the update ('execution_manager' or 'position_refresh')
            
        Returns:
            Dictionary with updated exposure, risk, and P&L data
        """
        # Log component start
        self.logger.info(
            'Position update started',
            trigger_component=trigger_component,
            has_changes=bool(changes),
            execution_mode=self.execution_mode
        )
        
        try:
            # Update state tracking
            self.tight_loop_active = True
            self.current_loop_timestamp = timestamp
            self.loop_execution_count += 1
            
            # Route to appropriate trigger handler
            if trigger_component == 'execution_manager':
                result = self._handle_execution_manager_trigger(timestamp, changes)
            elif trigger_component == 'position_refresh':
                result = self._handle_position_refresh_trigger(timestamp)
            else:
                raise ComponentError(
                    error_code='PUH-001',
                    message=f'Unknown trigger_component: {trigger_component}. Must be execution_manager or position_refresh',
                    component='PositionUpdateHandler',
                    severity='HIGH'
                )
            
            # Log component success
            self.logger.info(
                'Position update completed successfully',
                trigger_component=trigger_component,
                execution_mode=self.execution_mode,
                loop_execution_count=self.loop_execution_count
            )
            
            return result
            
        except Exception as e:
            # Log component error
            self.logger.error(
                'Position update failed',
                trigger_component=trigger_component,
                error=str(e),
                exc_info=True
            )
            self._handle_error(e, f"handle_position_update_{trigger_component}")
            
        finally:
            self.tight_loop_active = False
    
    def _handle_execution_manager_trigger(self, timestamp: pd.Timestamp, changes: Dict) -> Dict:
        """Handle execution_manager trigger - tight loop orchestration with execution deltas."""
        if self.execution_mode == 'backtest':
            # Backtest: Apply deltas + copy simulated to real
            self.position_monitor.update_state(timestamp, 'execution_manager', changes)
            # Simulated = Real in backtest (deep copy)
            self.position_monitor.real_positions = self.position_monitor.simulated_positions.copy()
            reconciliation_result = {'success': True, 'type': 'backtest_simulation'}
        else:  # live mode
            # Live: Apply deltas + query real positions + reconcile
            self.position_monitor.update_state(timestamp, 'execution_manager', changes)
            self.position_monitor.update_state(timestamp, 'position_refresh', None)
            reconciliation_result = self._reconcile_positions()
        
        # Continue with component chain
        return self._orchestrate_component_chain(timestamp, reconciliation_result)
    
    def _handle_position_refresh_trigger(self, timestamp: pd.Timestamp) -> Dict:
        """Handle position_refresh trigger - periodic position refresh with automatic settlements."""
        if self.execution_mode == 'backtest':
            # Backtest: Apply automatic settlements (initial capital, funding, rewards, M2M PnL)
            self.position_monitor.update_state(timestamp, 'position_refresh', None)
            return {'success': True, 'type': 'backtest_settlements'}
        else:  # live mode
            # Live: Query real positions from venues (settlements handled by exchange)
            self.position_monitor.update_state(timestamp, 'position_refresh', None)
            return {'success': True, 'type': 'live_refresh'}
    
    def _orchestrate_component_chain(self, timestamp: pd.Timestamp, reconciliation_result: Dict, market_data: Dict = None) -> Dict:
        """Orchestrate the component chain: position → exposure → risk → pnl."""
        try:
            # Get current positions
            position_snapshot = self.position_monitor.get_current_positions()
            
            # Market data is not needed for tight loop reconciliation
            # It's only needed when ExposureMonitor/RiskMonitor/PnLMonitor need to calculate values
            # For now, skip market data in tight loop and let components handle it
            if market_data is None:
                market_data = {}  # Empty market data for tight loop execution
            
            # Step 1: Calculate exposure
            exposure = self.exposure_monitor.calculate_exposure(
                timestamp=timestamp,
                position_snapshot=position_snapshot,
                market_data=market_data
            )
            
            # Step 2: Assess risk
            risk = self.risk_monitor.assess_risk(
                timestamp=timestamp,
                exposure_data=exposure,
                market_data=market_data
            )
            
            # Step 3: Calculate P&L
            self.pnl_monitor.update_state(timestamp, "position_update")
            pnl = self.pnl_monitor.get_latest_pnl()
            
            return {
                'success': reconciliation_result['success'],
                'reconciliation_result': reconciliation_result,
                'position_snapshot': position_snapshot,
                'exposure': exposure,
                'risk': risk,
                'pnl': pnl,
                'execution_mode': self.execution_mode
            }
            
        except Exception as e:
            self._handle_error(e, "orchestration")
    
    def _reconcile_positions(self) -> Dict:
        """
        Reconcile simulated vs real positions with mode-specific behavior.
        
        Live Mode: Compare simulated vs real positions with tolerance checking
        Backtest Mode: Always succeeds (simulated = real)
        
        Returns:
            Dict: Reconciliation result with success/failure status
        """
        try:
            if self.execution_mode == 'backtest':
                # Backtest mode: Always return success (simulated = real)
                return {
                    'success': True,
                    'reconciliation_type': 'backtest_simulation',
                    'message': 'Backtest mode - simulated positions match real positions'
                }
            else:
                # Live mode: Compare simulated vs real with tolerance
                position_update_handler_config = self.config.get('component_config', {}).get('position_update_handler', {})
                tolerance = position_update_handler_config.get('reconciliation_tolerance', 0.01)
                mismatches = []
                
                # Get all unique assets from both simulated and real positions
                all_assets = set(self.position_monitor.simulated_positions.keys()) | set(self.position_monitor.real_positions.keys())
                
                for asset in all_assets:
                    sim_amount = self.position_monitor.simulated_positions.get(asset, {}).get('amount', 0)
                    real_amount = self.position_monitor.real_positions.get(asset, {}).get('amount', 0)
                    
                    difference = abs(sim_amount - real_amount)
                    if difference > tolerance:
                        mismatches.append({
                            'asset': asset,
                            'SIMULATED_AMOUNT': sim_amount,
                            'REAL_AMOUNT': real_amount,
                            'difference': difference,
                            'tolerance': tolerance
                        })
                
                if mismatches:
                    self.logger.warning(
                        f'Position reconciliation mismatches found: {len(mismatches)} mismatches',
                        mismatches=len(mismatches),
                        tolerance=tolerance,
                        error_code="PUH-001"
                    )
                    
                    # Log reconciliation event
                    self._log_reconciliation_event(
                        trigger_source="execution_manager",
                        reconciliation_type="live_mismatch",
                        success=False,
                        simulated_positions=self.position_monitor.simulated_positions,
                        real_positions=self.position_monitor.real_positions,
                        mismatches=mismatches
                    )
                    
                    return {
                        'success': False,
                        'reconciliation_type': 'live_mismatch',
                        'mismatches': mismatches,
                        'message': f'Found {len(mismatches)} position mismatches exceeding tolerance {tolerance}'
                    }
                else:
                    self.logger.info(
                        'Position reconciliation successful - all positions within tolerance',
                        tolerance=tolerance
                    )
                    
                    # Log reconciliation event
                    self._log_reconciliation_event(
                        trigger_source="execution_manager",
                        reconciliation_type="live_success",
                        success=True,
                        simulated_positions=self.position_monitor.simulated_positions,
                        real_positions=self.position_monitor.real_positions,
                        mismatches=[]
                    )
                    
                    return {
                        'success': True,
                        'reconciliation_type': 'live_success',
                        'message': 'All positions reconciled within tolerance'
                    }
                    
        except Exception as e:
            self._handle_error(e, "reconciliation")
    
    def execution_deltas(self, execution_handshake: Any) -> Dict[str, float]:
        """
        Extract execution deltas from ExecutionHandshake.
        
        Args:
            execution_handshake: ExecutionHandshake object
            
        Returns:
            Dict[str, float]: Position deltas from execution
        """
        try:
            if hasattr(execution_handshake, 'actual_deltas'):
                return execution_handshake.actual_deltas
            else:
                return {}
        except Exception as e:
            self._handle_error(e, "execution_deltas")
            return {}
    
    def actual_deltas(self, execution_handshake: Any) -> Dict[str, float]:
        """
        Extract actual deltas from ExecutionHandshake.
        
        Args:
            execution_handshake: ExecutionHandshake object
            
        Returns:
            Dict[str, float]: Actual position deltas from execution
        """
        try:
            if hasattr(execution_handshake, 'actual_deltas'):
                return execution_handshake.actual_deltas
            else:
                return {}
        except Exception as e:
            self._handle_error(e, "actual_deltas")
            return {}
    