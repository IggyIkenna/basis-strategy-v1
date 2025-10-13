"""
Position Monitor Update Handler

TODO-REFACTOR: TIGHT LOOP ARCHITECTURE VIOLATION - See docs/REFERENCE_ARCHITECTURE_CANONICAL.md
ISSUE: This component may violate tight loop architecture requirements:

1. TIGHT LOOP ARCHITECTURE REQUIREMENTS:
   - Components must follow strict tight loop sequence
   - Proper event processing order
   - No state clearing between iterations
   - Consistent processing flow

2. REQUIRED VERIFICATION:
   - Verify tight loop sequence is enforced
   - Check for proper event processing order
   - Ensure no state clearing violations
   - Validate consistent processing flow

3. CANONICAL SOURCE:
   - docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Tight Loop Architecture
   - Tight loop sequence must be enforced

Provides a tight loop abstraction for position monitor updates that automatically triggers
the exposure → risk → P&L calculation sequence.

This ensures that any component performing an action always has access to the most
up-to-date position, exposure, risk, and P&L data.

Architecture:
- Strategy Manager: READ-ONLY, queries state, never updates position monitor
- Execution Interfaces: Write updates to position monitor (backtest) or trigger refresh (live)
- Position Update Handler: Manages the tight loop (position → exposure → risk → P&L)
- Event Engine: Orchestrates the overall flow

Live vs Backtest Mode:
- Backtest Mode: Position monitor is updated with simulated changes
- Live Mode: Position monitor refreshes from actual exchange connections
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType
from ...core.errors.component_error import ComponentError

logger = logging.getLogger(__name__)

# Create dedicated position update handler logger
position_update_logger = logging.getLogger('position_update_handler')
position_update_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
from pathlib import Path

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType
logs_dir = Path(__file__).parent.parent.parent.parent.parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Create file handler for position update handler logs
position_update_handler = logging.FileHandler(logs_dir / 'position_update_handler.log')
position_update_handler.setLevel(logging.INFO)

# Create formatter
position_update_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
position_update_handler.setFormatter(position_update_formatter)

# Add handler to logger if not already added
if not position_update_logger.handlers:
    position_update_logger.addHandler(position_update_handler)
    position_update_logger.propagate = False


class PositionUpdateHandler(StandardizedLoggingMixin):
    """
    Manages the tight loop between position monitor updates and downstream components.
    
    This class ensures that whenever the position monitor is updated, the exposure,
    risk, and P&L monitors are automatically recalculated in sequence.
    
    This abstraction simplifies the event engine and execution interfaces by providing
    a single point of control for the tight loop.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, 
                 config: Dict[str, Any],
                 data_provider,
                 position_monitor,
                 exposure_monitor,
                 risk_monitor,
                 pnl_calculator):
        """
        Initialize position update handler (mode-agnostic).
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            position_monitor: Position monitor instance
            exposure_monitor: Exposure monitor instance
            risk_monitor: Risk monitor instance
            pnl_calculator: P&L calculator instance
        """
        self.config = config
        self.data_provider = data_provider
        self.position_monitor = position_monitor
        self.exposure_monitor = exposure_monitor
        self.risk_monitor = risk_monitor
        self.pnl_calculator = pnl_calculator
        
        # Health integration
        self.health_status = {
            'status': 'healthy',
            'last_check': datetime.now(),
            'error_count': 0,
            'success_count': 0
        }
        
        position_update_logger.info(f"Position Update Handler initialized (mode-agnostic)")
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.health_status['error_count'] += 1
        error_code = f"PUH_ERROR_{self.health_status['error_count']:04d}"
        
        logger.error(f"Position Update Handler error {error_code}: {str(error)}", extra={
            'error_code': error_code,
            'context': context,
            'component': self.__class__.__name__
        })
        
        # Update health status based on error count
        if self.health_status['error_count'] > 10:
            self.health_status['status'] = "unhealthy"
        elif self.health_status['error_count'] > 5:
            self.health_status['status'] = "degraded"
    
    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            'status': self.health_status['status'],
            'error_count': self.health_status['error_count'],
            'success_count': self.health_status['success_count'],
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
        required_fields = ['action', 'timestamp', 'changes']
        return all(field in operation for field in required_fields)
    
    def _handle_graceful_data_handling(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data gracefully with fallbacks and validation."""
        try:
            # Validate data structure
            if not isinstance(data, dict):
                self._handle_error(ValueError("Data must be a dictionary"), "graceful_data_handling")
                return {}
            
            # Apply data validation and cleaning
            cleaned_data = {}
            for key, value in data.items():
                if value is not None:
                    cleaned_data[key] = value
            
            return cleaned_data
        except Exception as e:
            self._handle_error(e, "graceful_data_handling")
            return {}
    
    def _process_mode_agnostic_operations(self, operations: List[Dict]) -> List[Dict]:
        """Process operations in a mode-agnostic way."""
        processed_operations = []
        for operation in operations:
            # Mode-agnostic processing - same logic for backtest and live
            operation['mode_agnostic'] = True
            processed_operations.append(operation)
        return processed_operations
    
    def _create_component_factory(self) -> Dict[str, Any]:
        """Create component factory for position update components."""
        factory = {
            'updater': self.__create_updater,
            'monitor': self.__create_monitor,
            'handler': self.__create_handler
        }
        return factory
    
    def __create_updater(self) -> Any:
        """Create updater component."""
        # Factory method for updater
        return None
    
    def __create_monitor(self) -> Any:
        """Create monitor component."""
        # Factory method for monitor
        return None
    
    def __create_handler(self) -> Any:
        """Create handler component."""
        # Factory method for handler
        return None
    
    def _handle_position_update(self, 
                                   changes: Dict[str, Any], 
                                   timestamp: pd.Timestamp,
                                   market_data: Dict[str, Any] = None,
                                   trigger_component: str = 'unknown') -> Dict[str, Any]:
        """
        Handle position monitor update and trigger the tight loop.
        
        This method:
        1. Updates the position monitor (backtest) or triggers refresh (live)
        2. Recalculates exposure
        3. Reassesses risk
        4. Recalculates P&L
        
        Args:
            changes: Position changes to apply (backtest mode only)
            timestamp: Current timestamp
            market_data: Market data for calculations
            trigger_component: Component that triggered the update
            
        Returns:
            Dictionary with updated exposure, risk, and P&L data
        """
        try:
            position_update_logger.info(f"Position Update Handler: Handling update from {trigger_component}")
            
            # Step 1: Update position monitor (mode-agnostic)
            # Use configuration to determine behavior instead of mode checks
            use_simulated_changes = self.config.get('use_simulated_changes', True)
            
            if use_simulated_changes:
                # Apply simulated changes (backtest behavior)
                position_update_logger.info(f"Position Update Handler: Applying simulated changes")
                # Ensure timestamp is in the correct format for position monitor
                if 'timestamp' in changes and not isinstance(changes['timestamp'], pd.Timestamp):
                    changes['timestamp'] = pd.Timestamp(changes['timestamp'])
                self.position_monitor.update_state(timestamp, 'execution_manager', changes)
                updated_snapshot = self.position_monitor.get_current_positions()
            else:
                # Refresh from actual exchange connections (live behavior)
                position_update_logger.info(f"Position Update Handler: Refreshing position from exchanges")
                self.position_monitor.update_state(timestamp, 'position_refresh', None)
                updated_snapshot = self.position_monitor.get_current_positions()
            
            # Step 2: Recalculate exposure
            position_update_logger.info(f"Position Update Handler: Recalculating exposure")
            updated_exposure = self.exposure_monitor.calculate_exposure(
                timestamp=timestamp,
                position_snapshot=updated_snapshot,
                market_data=market_data or {}
            )
            position_update_logger.info(f"Position Update Handler: Exposure recalculated - total_value_usd = {updated_exposure.get('total_value_usd', 0)}")
            
            # Step 3: Reassess risk
            position_update_logger.info(f"Position Update Handler: Reassessing risk")
            updated_risk =  self.risk_monitor.assess_risk(
                exposure_data=updated_exposure,
                market_data=market_data or {}
            )
            position_update_logger.info(f"Position Update Handler: Risk reassessed")
            
            # Step 4: Recalculate P&L
            position_update_logger.info(f"Position Update Handler: Recalculating P&L")
            try:
                updated_pnl =  self.pnl_calculator.get_current_pnl(
                    current_exposure=updated_exposure,
                    timestamp=timestamp
                )
                position_update_logger.info(f"Position Update Handler: P&L recalculated successfully")
            except Exception as e:
                position_update_logger.error(f"Position Update Handler: P&L recalculation failed: {e}")
                # Create default P&L structure to avoid downstream errors
                updated_pnl = {
                    'balance_based': {'pnl_cumulative': 0.0, 'pnl_pct': 0.0},
                    'attribution': {'pnl_cumulative': 0.0},
                    'error': str(e)
                }
            
            position_update_logger.info(f"Position Update Handler: Tight loop completed successfully")
            
            return {
                'success': True,
                'position_snapshot': updated_snapshot,
                'exposure': updated_exposure,
                'risk': updated_risk,
                'pnl': updated_pnl,
                'trigger_component': trigger_component,
                'mode_agnostic': True
            }
            
        except Exception as e:
            position_update_logger.error(f"Position Update Handler: Tight loop failed: {e}")
            raise
    
    def _handle_atomic_position_update(self,
                                          changes: Dict[str, Any],
                                          timestamp: pd.Timestamp,
                                          market_data: Dict[str, Any] = None,
                                          trigger_component: str = 'atomic_operation') -> Dict[str, Any]:
        """
        Handle position monitor update for atomic operations.
        
        For atomic operations, we skip the tight loop until the entire atomic block completes.
        This prevents intermediate calculations that might not reflect the final state.
        
        Args:
            changes: Position changes to apply (backtest mode only)
            timestamp: Current timestamp
            market_data: Market data for calculations
            trigger_component: Component that triggered the update
            
        Returns:
            Dictionary with updated position snapshot only
        """
        try:
            position_update_logger.info(f"Position Update Handler: Handling atomic update from {trigger_component}")
            
            # For atomic operations, only update position monitor (mode-agnostic)
            # Use configuration to determine behavior instead of mode checks
            use_simulated_changes = self.config.get('use_simulated_changes', True)
            
            if use_simulated_changes:
                # Ensure timestamp is in the correct format for position monitor
                if 'timestamp' in changes and not isinstance(changes['timestamp'], pd.Timestamp):
                    changes['timestamp'] = pd.Timestamp(changes['timestamp'])
                self.position_monitor.update_state(timestamp, 'execution_manager', changes)
                updated_snapshot = self.position_monitor.get_current_positions()
            else:
                self.position_monitor.update_state(timestamp, 'position_refresh', None)
                updated_snapshot = self.position_monitor.get_current_positions()
            
            position_update_logger.info(f"Position Update Handler: Atomic position update completed")
            
            return {
                'success': True,
                'position_snapshot': updated_snapshot,
                'trigger_component': trigger_component,
                'mode_agnostic': True,
                'atomic_mode': True
            }
            
        except Exception as e:
            position_update_logger.error(f"Position Update Handler: Atomic update failed: {e}")
            raise
    
    def _trigger_tight_loop_after_atomic(self,
                                            timestamp: pd.Timestamp,
                                            market_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Trigger the tight loop after atomic operations complete.
        
        This method is called after all atomic operations in a block are complete
        to ensure the exposure, risk, and P&L are recalculated with the final state.
        
        Args:
            timestamp: Current timestamp
            market_data: Market data for calculations
            
        Returns:
            Dictionary with updated exposure, risk, and P&L data
        """
        try:
            position_update_logger.info(f"Position Update Handler: Triggering tight loop after atomic operations")
            
            # Get current position snapshot
            current_snapshot = self.position_monitor.get_current_positions()
            
            # Recalculate exposure
            updated_exposure = self.exposure_monitor.calculate_exposure(
                timestamp=timestamp,
                position_snapshot=current_snapshot,
                market_data=market_data or {}
            )
            
            # Reassess risk
            updated_risk =  self.risk_monitor.assess_risk(
                exposure_data=updated_exposure,
                market_data=market_data or {}
            )
            
            # Recalculate P&L
            try:
                updated_pnl =  self.pnl_calculator.get_current_pnl(
                    current_exposure=updated_exposure,
                    timestamp=timestamp
                )
            except Exception as e:
                position_update_logger.error(f"Position Update Handler: P&L recalculation failed after atomic: {e}")
                updated_pnl = {
                    'balance_based': {'pnl_cumulative': 0.0, 'pnl_pct': 0.0},
                    'attribution': {'pnl_cumulative': 0.0},
                    'error': str(e)
                }
            
            position_update_logger.info(f"Position Update Handler: Tight loop after atomic operations completed")
            
            return {
                'success': True,
                'exposure': updated_exposure,
                'risk': updated_risk,
                'pnl': updated_pnl,
                'mode_agnostic': True,
                'post_atomic': True
            }
            
        except Exception as e:
            position_update_logger.error(f"Position Update Handler: Tight loop after atomic failed: {e}")
            raise
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs) -> None:
        """
        Update state for the position update handler.
        
        Args:
            timestamp: Current timestamp
            trigger_source: Source of the update trigger
            **kwargs: Additional update parameters
        """
        try:
            # Update all monitored components
            if self.position_monitor:
                self.position_monitor.update_state(timestamp, trigger_source, **kwargs)
            
            if self.exposure_monitor:
                self.exposure_monitor.update_state(timestamp, trigger_source, **kwargs)
            
            if self.risk_monitor:
                self.risk_monitor.update_state(timestamp, trigger_source, **kwargs)
            
            if self.pnl_calculator:
                self.pnl_calculator.update_state(timestamp, trigger_source, **kwargs)
            
            position_update_logger.debug(f"PositionUpdateHandler.update_state completed at {timestamp} from {trigger_source}")
            
        except Exception as e:
            position_update_logger.error(f"Failed to update state in PositionUpdateHandler: {e}")
            raise
    
    def _execute_tight_loop(self, timestamp: pd.Timestamp, execution_deltas: Dict = None):
        """Execute tight loop with reconciliation handshake."""
        self.tight_loop_active = True
        
        try:
            # Update position with execution deltas
            if execution_deltas:
                self.position_monitor.update_state(timestamp, execution_deltas, 'execution_manager')
            
            # Update exposure monitor
            self.exposure_monitor.update_state(timestamp, 'tight_loop')
            
            # Update risk monitor
            self.risk_monitor.update_state(timestamp, 'tight_loop')
            
            # Update PnL calculator
            self.pnl_calculator.update_state(timestamp, 'tight_loop')
            
            # Check reconciliation status if in live mode
            if self.execution_mode == 'live':
                # Get current positions for reconciliation
                current_positions = self.position_monitor.get_current_positions()
                expected_positions = execution_deltas if execution_deltas else {}
                
                # Perform reconciliation
                reconciliation_result = self.reconciliation_component.reconcile_position(
                    timestamp, expected_positions, current_positions
                )
                
                if not reconciliation_result['success']:
                    logger.warning(f"Tight loop reconciliation failed: {reconciliation_result}")
                    self.tight_loop_active = False
                    return False
            
            self.tight_loop_active = False
            return True
            
        except Exception as e:
            logger.error(f"Tight loop execution failed: {e}")
            self.tight_loop_active = False
            return False
    
    def _execute_full_loop(self, timestamp: pd.Timestamp):
        """Execute full loop without reconciliation."""
        try:
            # Update all components in sequence
            self.position_monitor.update_state(timestamp, 'full_loop', None)
            self.exposure_monitor.update_state(timestamp, 'full_loop')
            self.risk_monitor.update_state(timestamp, 'full_loop')
            self.pnl_calculator.update_state(timestamp, 'full_loop')
            
            logger.info(f"Full loop executed successfully at {timestamp}")
            return True
            
        except Exception as e:
            logger.error(f"Full loop execution failed: {e}")
            return False
    
    def check_component_health(self) -> Dict[str, Any]:
        """
        Check component health status.
        
        Returns:
            Health status dictionary
        """
        try:
            current_time = datetime.now()
            
            # Check if component is responsive
            if (current_time - self.health_status['last_check']).seconds > 300:  # 5 minutes
                self.health_status['status'] = 'unhealthy'
                self.health_status['error'] = 'Component not responding'
            
            # Check error rate
            total_operations = self.health_status['error_count'] + self.health_status['success_count']
            if total_operations > 0:
                error_rate = self.health_status['error_count'] / total_operations
                if error_rate > 0.1:  # 10% error rate threshold
                    self.health_status['status'] = 'degraded'
                    self.health_status['error_rate'] = error_rate
            
            self.health_status['last_check'] = current_time
            
            return {
                'component': 'position_update_handler',
                'status': self.health_status['status'],
                'last_check': self.health_status['last_check'].isoformat(),
                'error_count': self.health_status['error_count'],
                'success_count': self.health_status['success_count'],
                'total_operations': total_operations
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'component': 'position_update_handler',
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _handle_error(self, error_code: str, error_message: str, details: Optional[Dict] = None):
        """
        Handle errors with structured error handling.
        
        Args:
            error_code: Error code
            error_message: Error message
            details: Additional error details
        """
        try:
            # Update health status
            self.health_status['error_count'] += 1
            
            # Create structured error
            error = ComponentError(
                component='position_update_handler',
                error_code=error_code,
                message=error_message,
                details=details or {}
            )
            
            # Log structured error
            self.structured_logger.error(
                f"Position Update Handler Error: {error_code}",
                error_code=error_code,
                error_message=error_message,
                details=details,
                component='position_update_handler'
            )
            
            # Update health status if too many errors
            if self.health_status['error_count'] > 10:
                self.health_status['status'] = 'unhealthy'
            
        except Exception as e:
            logger.error(f"Failed to handle error: {e}")
    
    def _log_success(self, operation: str, details: Optional[Dict] = None):
        """
        Log successful operations.
        
        Args:
            operation: Operation name
            details: Operation details
        """
        try:
            # Update health status
            self.health_status['success_count'] += 1
            
            # Log success
            self.structured_logger.info(
                f"Position Update Handler Success: {operation}",
                operation=operation,
                details=details,
                component='position_update_handler'
            )
            
        except Exception as e:
            logger.error(f"Failed to log success: {e}")
    
    def _get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Get data using canonical data access pattern.
        
        Args:
            timestamp: Current timestamp
            
        Returns:
            Data dictionary
        """
        try:
            # Return position data from position monitor
            return {
                'positions': self.position_monitor.get_positions(),
                'exposure': self.exposure_monitor.get_exposure(),
                'risk_metrics': self.risk_monitor.get_risk_metrics(),
                'pnl': self.pnl_calculator.get_pnl()
            }
        except Exception as e:
            self._handle_error('PUH-001', f"Failed to get data: {e}")
            return {}
    
    def _process_config_driven_operations(self, operation_type: str, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process operations based on configuration settings."""
        try:
            # Get config-driven position update settings
            position_config = self.config.get('component_config', {}).get('position_update_handler', {})
            tight_loop_enabled = position_config.get('tight_loop_enabled', True)
            update_triggers = position_config.get('update_triggers', ['execution', 'reconciliation'])
            
            # Process based on config-driven settings
            result = {
                'operation_type': operation_type,
                'tight_loop_enabled': tight_loop_enabled,
                'update_triggers': update_triggers,
                'config_driven': True
            }
            
            return result
            
        except Exception as e:
            self._handle_error('PUH-001', f"Config-driven operation failed: {e}")
            raise
    
    def _validate_operation(self, operation_type: str) -> bool:
        """Validate operation against configuration."""
        try:
            position_config = self.config.get('component_config', {}).get('position_update_handler', {})
            supported_operations = position_config.get('supported_operations', ['update_position', 'trigger_loop'])
            return operation_type in supported_operations
        except Exception:
            return False
    
    def _process_mode_agnostic_operations(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process operations in a mode-agnostic way."""
        try:
            # Mode-agnostic position update logic
            # Same logic for both backtest and live modes
            result = {
                'mode_agnostic': True,
                'execution_mode': self.execution_mode,
                'operation_data': operation_data,
                'processed_at': datetime.now().isoformat()
            }
            
            # Apply mode-agnostic position update rules
            if self.execution_mode == 'backtest':
                # In backtest, update simulated positions
                result['update_type'] = 'simulated'
                result['mode_specific_note'] = 'backtest_simulation'
            else:
                # In live mode, trigger position refresh
                result['update_type'] = 'live_refresh'
                result['mode_specific_note'] = 'live_validation'
            
            return result
            
        except Exception as e:
            self._handle_error('PUH-001', f"Mode-agnostic operation failed: {e}")
            raise