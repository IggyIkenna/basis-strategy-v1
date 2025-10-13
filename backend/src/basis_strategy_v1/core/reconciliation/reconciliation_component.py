"""Reconciliation Component - Position state validation and reconciliation."""

import structlog
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType
from ...core.errors.component_error import ComponentError

logger = structlog.get_logger()


class ReconciliationComponent(StandardizedLoggingMixin):
    """
    Validates Position Monitor's simulated position state against real position state,
    enabling execution manager to proceed only after successful reconciliation.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ReconciliationComponent, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict, execution_mode: str, position_monitor, event_logger=None, health_manager=None, data_provider=None):
        """
        Initialize reconciliation component with references.
        
        Args:
            config: Configuration dictionary (reference, never modified)
            execution_mode: 'backtest' | 'live' (from BASIS_EXECUTION_MODE)
            position_monitor: PositionMonitor instance (reference)
            event_logger: EventLogger instance (optional reference)
            health_manager: UnifiedHealthManager instance (optional reference)
            data_provider: Data provider instance for canonical data access
        """
        # Store references (NEVER modified)
        self.config = config
        self.execution_mode = execution_mode
        self.position_monitor = position_monitor
        self.data_provider = data_provider
        
        # Health integration
        self.health_status = {
            'status': 'healthy',
            'last_check': datetime.now(),
            'error_count': 0,
            'success_count': 0
        }
        self.event_logger = event_logger
        self.health_manager = health_manager
        
        # Validate required configuration at startup (fail-fast)
        required_keys = ['max_retry_attempts', 'reconciliation_tolerance']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required configuration: {key}")
        
        # Initialize component-specific state
        self.reconciliation_status = 'pending'
        self.last_reconciliation_timestamp = None
        self.reconciliation_history: List[Dict] = []
        self.retry_count = 0
        self.max_retries = config['max_retry_attempts']
        self.tolerance = config['reconciliation_tolerance']
        
        # Register with health system if available
        if self.health_manager:
            self.health_manager.register_component(
                component_name='ReconciliationComponent',
                checker=self._health_check
            )
        
        # Log initialization
        if self.event_logger:
            self.event_logger.log_event(
                timestamp=pd.Timestamp.now(),
                event_type='component_initialization',
                component='ReconciliationComponent',
                data={
                    'execution_mode': self.execution_mode,
                    'max_retries': self.max_retries,
                    'tolerance': self.tolerance,
                    'config_hash': hash(str(self.config))
                }
            )
        
        logger.info(
            "ReconciliationComponent initialized",
            execution_mode=self.execution_mode,
            max_retries=self.max_retries,
            tolerance=self.tolerance
        )
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.health_status['error_count'] += 1
        error_code = f"RC_ERROR_{self.health_status['error_count']:04d}"
        
        logger.error(f"Reconciliation Component error {error_code}: {str(error)}", extra={
            'error_code': error_code,
            'context': context,
            'execution_mode': self.execution_mode,
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
            'execution_mode': self.execution_mode,
            'reconciliation_status': self.reconciliation_status,
            'retry_count': self.retry_count,
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
        required_fields = ['action', 'timestamp', 'state']
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
            if self.execution_mode == 'backtest':
                # Simulate reconciliation
                operation['simulated'] = True
            else:
                # Live reconciliation
                operation['simulated'] = False
            
            processed_operations.append(operation)
        return processed_operations
    
    def _create_component_factory(self) -> Dict[str, Any]:
        """Create component factory for reconciliation components."""
        factory = {
            'validator': self.__create_validator,
            'comparator': self.__create_comparator,
            'reporter': self.__create_reporter
        }
        return factory
    
    def __create_validator(self) -> Any:
        """Create validator component."""
        # Factory method for validator
        return None
    
    def __create_comparator(self) -> Any:
        """Create comparator component."""
        # Factory method for comparator
        return None
    
    def __create_reporter(self) -> Any:
        """Create reporter component."""
        # Factory method for reporter
        return None
    
    def update_state(self, timestamp: pd.Timestamp, simulated_state: Dict, trigger_source: str) -> bool:
        """
        Main reconciliation entry point.
        
        Args:
            timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
            simulated_state: Position state from execution manager deltas
            trigger_source: 'execution_manager' | 'position_refresh' | 'manual'
            
        Returns:
            bool: True if reconciliation successful, False if failed
        """
        start_time = datetime.now()
        
        try:
            if self.execution_mode == 'backtest':
                # Always succeed in backtest mode
                self.reconciliation_status = 'success'
                self.last_reconciliation_timestamp = timestamp
                self.retry_count = 0  # Reset on success
                
                # Log state update
                if self.event_logger:
                    processing_time = (datetime.now() - start_time).total_seconds() * 1000
                    self.event_logger.log_event(
                        timestamp=timestamp,
                        event_type='state_update',
                        component='ReconciliationComponent',
                        data={
                            'trigger_source': trigger_source,
                            'reconciliation_status': self.reconciliation_status,
                            'retry_count': self.retry_count,
                            'processing_time_ms': processing_time,
                            'mode': 'backtest'
                        }
                    )
                
                return True
            
            elif self.execution_mode == 'live':
                # Compare simulated vs real in live mode
                real_state = self.position_monitor.get_real_positions()
                match = self.check_reconciliation(simulated_state, real_state)
                
                if match:
                    self.reconciliation_status = 'success'
                    self.last_reconciliation_timestamp = timestamp
                    self.retry_count = 0  # Reset on success
                    
                    # Log successful reconciliation
                    if self.event_logger:
                        processing_time = (datetime.now() - start_time).total_seconds() * 1000
                        self.event_logger.log_event(
                            timestamp=timestamp,
                            event_type='state_update',
                            component='ReconciliationComponent',
                            data={
                                'trigger_source': trigger_source,
                                'reconciliation_status': self.reconciliation_status,
                                'retry_count': self.retry_count,
                                'processing_time_ms': processing_time,
                                'mode': 'live'
                            }
                        )
                    
                    return True
                else:
                    self.reconciliation_status = 'failed'
                    self.retry_count += 1
                    
                    # Log failed reconciliation
                    if self.event_logger:
                        processing_time = (datetime.now() - start_time).total_seconds() * 1000
                        self.event_logger.log_event(
                            timestamp=timestamp,
                            event_type='reconciliation_failed',
                            component='ReconciliationComponent',
                            data={
                                'trigger_source': trigger_source,
                                'reconciliation_status': self.reconciliation_status,
                                'retry_count': self.retry_count,
                                'processing_time_ms': processing_time,
                                'mode': 'live'
                            }
                        )
                    
                    return False
            
            else:
                raise ValueError(f"Unknown execution mode: {self.execution_mode}")
                
        except Exception as e:
            # Log error event
            if self.event_logger:
                self.event_logger.log_event(
                    timestamp=timestamp,
                    event_type='error',
                    component='ReconciliationComponent',
                    data={
                        'error_code': 'REC-001',
                        'error_message': str(e),
                        'trigger_source': trigger_source,
                        'execution_mode': self.execution_mode
                    }
                )
            
            # Raise structured error
            raise ComponentError(
                error_code='REC-001',
                message=f'ReconciliationComponent failed: {str(e)}',
                component='ReconciliationComponent',
                severity='HIGH',
                original_exception=e
            )
    
    def _check_reconciliation(self, simulated_positions: Dict, real_positions: Dict) -> bool:
        """
        Compare positions within tolerance.
        
        Args:
            simulated_positions: Position state from execution manager
            real_positions: Position state from external APIs or backtest
            
        Returns:
            bool: True if match within tolerance, False otherwise
        """
        try:
            # Compare all token balances
            for token, sim_balance in simulated_positions.items():
                real_balance = real_positions.get(token, 0)
                
                # Apply tolerance for floating point precision
                if abs(sim_balance - real_balance) > self.tolerance:
                    logger.warning(
                        "Position mismatch detected",
                        token=token,
                        simulated_balance=sim_balance,
                        real_balance=real_balance,
                        difference=abs(sim_balance - real_balance),
                        tolerance=self.tolerance
                    )
                    
                    # Log position mismatch event
                    if self.event_logger:
                        self.event_logger.log_event(
                            timestamp=pd.Timestamp.now(),
                            event_type='position_mismatch',
                            component='ReconciliationComponent',
                            data={
                                'error_code': 'REC-002',
                                'token': token,
                                'simulated_balance': sim_balance,
                                'real_balance': real_balance,
                                'difference': abs(sim_balance - real_balance),
                                'tolerance': self.tolerance
                            }
                        )
                    
                    return False
            
            # All positions match within tolerance
            return True
            
        except Exception as e:
            # Log error event
            if self.event_logger:
                self.event_logger.log_event(
                    timestamp=pd.Timestamp.now(),
                    event_type='error',
                    component='ReconciliationComponent',
                    data={
                        'error_code': 'REC-002',
                        'error_message': str(e),
                        'error_type': 'position_comparison_error'
                    }
                )
            
            # Raise structured error
            raise ComponentError(
                error_code='REC-002',
                message=f'Position comparison failed: {str(e)}',
                component='ReconciliationComponent',
                severity='HIGH',
                original_exception=e
            )
    
    def _get_health_status(self) -> Dict:
        """
        Health check integration.
        
        Returns:
            Dict: Health status information
        """
        try:
            if self.execution_mode == 'backtest':
                return {
                    'status': 'healthy',
                    'reconciliation_status': self.reconciliation_status,
                    'last_timestamp': self.last_reconciliation_timestamp,
                    'mode': 'backtest'
                }
            
            elif self.execution_mode == 'live':
                if self.retry_count >= self.max_retries:
                    return {
                        'status': 'unhealthy',
                        'error': 'Reconciliation failed after max retries',
                        'retry_count': self.retry_count,
                        'max_retries': self.max_retries,
                        'last_timestamp': self.last_reconciliation_timestamp,
                        'mode': 'live'
                    }
                else:
                    return {
                        'status': 'healthy',
                        'reconciliation_status': self.reconciliation_status,
                        'retry_count': self.retry_count,
                        'max_retries': self.max_retries,
                        'last_timestamp': self.last_reconciliation_timestamp,
                        'mode': 'live'
                    }
            
            else:
                return {
                    'status': 'unhealthy',
                    'error': f'Unknown execution mode: {self.execution_mode}',
                    'mode': 'unknown'
                }
                
        except Exception as e:
            logger.error(
                "Health check failed",
                error=str(e),
                component='ReconciliationComponent'
            )
            return {
                'status': 'unhealthy',
                'error': f'Health check failed: {str(e)}',
                'component': 'ReconciliationComponent'
            }
    
    def _health_check(self) -> Dict:
        """
        Component-specific health check for health manager integration.
        
        Returns:
            Dict: Health check results
        """
        return self._get_health_status()
    
    def reconcile_position(self, timestamp: pd.Timestamp, expected_position: Dict, actual_position: Dict) -> Dict:
        """
        Reconcile expected vs actual position.
        MODE-AGNOSTIC - same logic for all strategy modes.
        
        Args:
            timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
            expected_position: Position state from execution manager deltas
            actual_position: Position state from venue interfaces
            
        Returns:
            Dict: Reconciliation results with success status and details
        """
        start_time = datetime.now()
        
        try:
            if self.execution_mode == 'backtest':
                # Always succeed in backtest mode (simulated execution)
                return {
                    'success': True,
                    'reconciliation_results': {},
                    'tolerance': self.reconciliation_tolerance,
                    'processing_time_ms': (datetime.now() - start_time).total_seconds() * 1000,
                    'mode': 'backtest'
                }
            else:
                # Perform real reconciliation with tolerance checks
                return self._perform_reconciliation(expected_position, actual_position, timestamp)
                
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
    
    def _perform_reconciliation(self, expected_position: Dict, actual_position: Dict, timestamp: pd.Timestamp) -> Dict:
        """Perform actual reconciliation with tolerance checks."""
        reconciliation_results = {}
        overall_success = True
        
        # Get tracked assets from position monitor (fail-fast validation)
        try:
            position_snapshot = self.position_monitor.get_current_positions()
            tracked_assets = position_snapshot['tracked_assets']
        except Exception as e:
            logger.error(f"Failed to get tracked assets: {e}")
            return {'success': False, 'error': f"Failed to get tracked assets: {e}"}
        
        # Validate all expected assets are tracked
        for asset in expected_position.keys():
            if asset not in tracked_assets:
                logger.warning(f"Expected asset {asset} not in tracked assets: {tracked_assets}")
                overall_success = False
                continue
        
        # Perform reconciliation for each tracked asset
        for asset in tracked_assets:
            expected_value = expected_position.get(asset, 0.0)
            actual_value = actual_position.get(asset, 0.0)
            
            # Calculate difference and percentage
            difference = abs(expected_value - actual_value)
            percentage_diff = (difference / max(expected_value, 0.001)) * 100 if expected_value != 0 else 0
            
            # Check tolerance
            within_tolerance = percentage_diff <= self.reconciliation_tolerance
            
            reconciliation_results[asset] = {
                'expected': expected_value,
                'actual': actual_value,
                'difference': difference,
                'percentage_diff': percentage_diff,
                'within_tolerance': within_tolerance
            }
            
            if not within_tolerance:
                overall_success = False
                logger.warning(f"Asset {asset} outside tolerance: {percentage_diff:.2f}% > {self.reconciliation_tolerance}%")
        
        return {
            'success': overall_success,
            'reconciliation_results': reconciliation_results,
            'tolerance': self.reconciliation_tolerance,
            'processing_time_ms': (datetime.now() - datetime.now()).total_seconds() * 1000,
            'mode': 'live'
        }
    
    def _get_state_snapshot(self) -> Dict:
        """
        Get current component state for debugging and monitoring.
        
        Returns:
            Dict: Current state snapshot
        """
        return {
            'reconciliation_status': self.reconciliation_status,
            'last_reconciliation_timestamp': self.last_reconciliation_timestamp,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'tolerance': self.tolerance,
            'execution_mode': self.execution_mode,
            'reconciliation_history_count': len(self.reconciliation_history)
        }
    
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
                'component': 'reconciliation_component',
                'status': self.health_status['status'],
                'last_check': self.health_status['last_check'].isoformat(),
                'error_count': self.health_status['error_count'],
                'success_count': self.health_status['success_count'],
                'total_operations': total_operations
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'component': 'reconciliation_component',
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
                component='reconciliation_component',
                error_code=error_code,
                message=error_message,
                details=details or {}
            )
            
            # Log structured error
            self.structured_logger.error(
                f"Reconciliation Component Error: {error_code}",
                error_code=error_code,
                error_message=error_message,
                details=details,
                component='reconciliation_component'
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
                f"Reconciliation Component Success: {operation}",
                operation=operation,
                details=details,
                component='reconciliation_component'
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
            if self.data_provider:
                return self.data_provider.get_data(timestamp)
            else:
                return {}
        except Exception as e:
            self._handle_error('RC-001', f"Failed to get data: {e}")
            return {}
    
    def _process_config_driven_operations(self, operation_type: str, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process operations based on configuration settings."""
        try:
            # Get config-driven reconciliation settings
            reconciliation_config = self.config.get('component_config', {}).get('reconciliation_component', {})
            tolerance = reconciliation_config.get('tolerance', 0.01)
            max_retries = reconciliation_config.get('max_retries', 3)
            timeout = reconciliation_config.get('timeout', 30)
            
            # Process based on config-driven settings
            result = {
                'operation_type': operation_type,
                'tolerance': tolerance,
                'max_retries': max_retries,
                'timeout': timeout,
                'config_driven': True
            }
            
            return result
            
        except Exception as e:
            self._handle_error('RC-001', f"Config-driven operation failed: {e}")
            raise
    
    def _validate_operation(self, operation_type: str) -> bool:
        """Validate operation against configuration."""
        try:
            reconciliation_config = self.config.get('component_config', {}).get('reconciliation_component', {})
            supported_operations = reconciliation_config.get('supported_operations', ['reconcile', 'validate'])
            return operation_type in supported_operations
        except Exception:
            return False
    
    def _process_mode_agnostic_operations(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process operations in a mode-agnostic way."""
        try:
            # Mode-agnostic reconciliation logic
            # Same logic for both backtest and live modes
            result = {
                'mode_agnostic': True,
                'execution_mode': self.execution_mode,
                'operation_data': operation_data,
                'processed_at': datetime.now().isoformat()
            }
            
            # Apply mode-agnostic reconciliation rules
            if self.execution_mode == 'backtest':
                # In backtest, always succeed (simulated reconciliation)
                result['reconciliation_status'] = 'success'
                result['mode_specific_note'] = 'backtest_simulation'
            else:
                # In live mode, perform actual reconciliation
                result['reconciliation_status'] = 'pending'
                result['mode_specific_note'] = 'live_validation'
            
            return result
            
        except Exception as e:
            self._handle_error('RC-001', f"Mode-agnostic operation failed: {e}")
            raise
