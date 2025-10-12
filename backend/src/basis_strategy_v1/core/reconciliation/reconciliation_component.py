"""Reconciliation Component - Position state validation and reconciliation."""

import structlog
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

# ComponentError class for structured error handling
class ComponentError(Exception):
    """Structured error for component failures."""
    def __init__(self, error_code: str, message: str, component: str, severity: str = 'HIGH', original_exception=None):
        self.error_code = error_code
        self.component = component
        self.severity = severity
        self.original_exception = original_exception
        super().__init__(message)

logger = structlog.get_logger()


class ReconciliationComponent:
    """
    Validates Position Monitor's simulated position state against real position state,
    enabling execution manager to proceed only after successful reconciliation.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ReconciliationComponent, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict, execution_mode: str, position_monitor, event_logger=None, health_manager=None):
        """
        Initialize reconciliation component with references.
        
        Args:
            config: Configuration dictionary (reference, never modified)
            execution_mode: 'backtest' | 'live' (from BASIS_EXECUTION_MODE)
            position_monitor: PositionMonitor instance (reference)
            event_logger: EventLogger instance (optional reference)
            health_manager: UnifiedHealthManager instance (optional reference)
        """
        # Store references (NEVER modified)
        self.config = config
        self.execution_mode = execution_mode
        self.position_monitor = position_monitor
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
    
    def check_reconciliation(self, simulated_positions: Dict, real_positions: Dict) -> bool:
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
    
    def get_health_status(self) -> Dict:
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
        return self.get_health_status()
    
    def get_state_snapshot(self) -> Dict:
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
