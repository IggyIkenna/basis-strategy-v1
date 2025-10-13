"""
Mode-Agnostic Event Logger

Provides mode-agnostic event logging that works for both backtest and live modes.
Manages event logging across all venues and provides generic logging logic.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/12_EVENT_LOGGER.md - Mode-agnostic event logging
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime, timedelta
import json
import os

from ..logging.structured_logger import get_structured_logger

logger = logging.getLogger(__name__)

class EventLogger:
    """Mode-agnostic event logger that works for both backtest and live modes"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize event logger.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
        """
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        self.health_status = "healthy"
        self.error_count = 0
        
        # Initialize structured logger
        self.structured_logger = get_structured_logger('event_logger')
        
        # Event tracking
        self.event_history = []
        self.logged_events = {}
        
        # Logging configuration (optional with fail-fast)
        if 'log_path' in config:
            self.log_path = config['log_path']
        else:
            self.log_path = './logs'  # Default only if not specified
            
        if 'log_format' in config:
            self.log_format = config['log_format']
        else:
            self.log_format = 'json'  # Default only if not specified
            
        if 'log_level' in config:
            self.log_level = config['log_level']
        else:
            self.log_level = 'INFO'  # Default only if not specified
        
        # Event logging configuration parameters
        self.event_categories = config.get('event_categories', {
            'data': ['data_loaded', 'data_updated', 'data_error'],
            'risk': ['risk_breach', 'risk_warning', 'risk_calculation'],
            'event': ['event_logged', 'event_filtered', 'event_exported'],
            'business': ['trade_executed', 'position_updated', 'strategy_decision']
        })
        
        self.event_logging_settings = config.get('event_logging_settings', {
            'buffer_size': 10000,
            'export_format': 'both',  # 'csv', 'json', or 'both'
            'async_logging': True,
            'compression': False
        })
        
        self.log_retention_policy = config.get('log_retention_policy', {
            'retention_days': 30,
            'max_file_size_mb': 100,
            'rotation_frequency': 'daily',
            'compression_after_days': 7
        })
        
        
        self.logging_requirements = config.get('logging_requirements', {
            'structured_logging': True,
            'correlation_ids': True,
            'performance_metrics': True,
            'error_tracking': True
        })
        
        self.event_filtering = config.get('event_filtering', {
            'filter_by_level': True,
            'filter_by_category': True,
            'exclude_patterns': [],
            'include_patterns': ['*']
        })
        
        self.structured_logger.info(
            "EventLogger initialized",
            event_type="component_initialization",
            component="event_logger",
            mode="mode-agnostic"
        )
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.error_count += 1
        error_code = f"EL_ERROR_{self.error_count:04d}"
        
        logger.error(f"Event Logger error {error_code}: {str(error)}", extra={
            'error_code': error_code,
            'context': context,
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
            'event_history_count': len(self.event_history),
            'logged_events_count': len(self.logged_events),
            'log_path': self.log_path,
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
        required_fields = ['event_type', 'timestamp', 'data']
        return all(field in operation for field in required_fields)
    
    async def log_event(self, event_type: str, event_data: Dict[str, Any], 
                       timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Log event regardless of mode (backtest or live).
        
        Args:
            event_type: Type of event to log
            event_data: Event data dictionary
            timestamp: Current timestamp
            
        Returns:
            Dictionary with logging result
        """
        try:
            # Validate event
            validation_result = self._validate_event(event_type, event_data)
            if not validation_result['valid']:
                return {
                    'status': 'failed',
                    'error': validation_result['error'],
                    'timestamp': timestamp
                }
            
            # Create event record
            event_record = {
                'event_type': event_type,
                'event_data': event_data,
                'timestamp': timestamp,
                'log_level': self.log_level
            }
            
            # Log event based on format
            if self.log_format == 'json':
                log_result = await self._log_event_json(event_record)
            elif self.log_format == 'csv':
                log_result = await self._log_event_csv(event_record)
            elif self.log_format == 'text':
                log_result = await self._log_event_text(event_record)
            else:
                return {
                    'status': 'failed',
                    'error': f"Unsupported log format: {self.log_format}",
                    'timestamp': timestamp
                }
            
            if log_result['success']:
                # Add to event history
                self.event_history.append(event_record)
                
                # Add to logged events
                event_key = f"{event_type}_{timestamp.timestamp()}"
                self.logged_events[event_key] = event_record
                
                logger.info(f"Successfully logged event: {event_type} at {timestamp}")
            else:
                logger.error(f"Failed to log event: {event_type} at {timestamp}: {log_result.get('error', 'Unknown error')}")
            
            return {
                'status': 'success' if log_result['success'] else 'failed',
                'timestamp': timestamp,
                'log_result': log_result
            }
            
        except Exception as e:
            logger.error(f"Error logging event: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_gas_fee(self, gas_fee_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log gas fee event."""
        try:
            return await self.log_event('gas_fee', gas_fee_data, timestamp)
        except Exception as e:
            logger.error(f"Error logging gas fee: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_stake(self, stake_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log stake event."""
        try:
            return await self.log_event('stake', stake_data, timestamp)
        except Exception as e:
            logger.error(f"Error logging stake: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_aave_supply(self, supply_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log AAVE supply event."""
        try:
            return await self.log_event('aave_supply', supply_data, timestamp)
        except Exception as e:
            logger.error(f"Error logging AAVE supply: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_aave_borrow(self, borrow_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log AAVE borrow event."""
        try:
            return await self.log_event('aave_borrow', borrow_data, timestamp)
        except Exception as e:
            logger.error(f"Error logging AAVE borrow: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_atomic_transaction(self, transaction_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log atomic transaction event."""
        try:
            return await self.log_event('atomic_transaction', transaction_data, timestamp)
        except Exception as e:
            logger.error(f"Error logging atomic transaction: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_perp_trade(self, trade_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log perpetual trade event."""
        try:
            return await self.log_event('perp_trade', trade_data, timestamp)
        except Exception as e:
            logger.error(f"Error logging perpetual trade: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_funding_payment(self, funding_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log funding payment event."""
        try:
            return await self.log_event('funding_payment', funding_data, timestamp)
        except Exception as e:
            logger.error(f"Error logging funding payment: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_venue_transfer(self, transfer_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log venue transfer event."""
        try:
            return await self.log_event('venue_transfer', transfer_data, timestamp)
        except Exception as e:
            logger.error(f"Error logging venue transfer: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_rebalance(self, rebalance_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log rebalance event."""
        try:
            return await self.log_event('rebalance', rebalance_data, timestamp)
        except Exception as e:
            logger.error(f"Error logging rebalance: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_risk_alert(self, risk_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log risk alert event."""
        try:
            return await self.log_event('risk_alert', risk_data, timestamp)
        except Exception as e:
            logger.error(f"Error logging risk alert: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_seasonal_reward_distribution(self, reward_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log seasonal reward distribution event."""
        try:
            return await self.log_event('seasonal_reward_distribution', reward_data, timestamp)
        except Exception as e:
            logger.error(f"Error logging seasonal reward distribution: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def update_event(self, event_key: str, update_data: Dict[str, Any], 
                          timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Update existing event."""
        try:
            # Check if event exists
            if event_key not in self.logged_events:
                return {
                    'status': 'failed',
                    'error': f"Event not found: {event_key}",
                    'timestamp': timestamp
                }
            
            # Update event
            self.logged_events[event_key].update(update_data)
            self.logged_events[event_key]['updated_at'] = timestamp
            
            # Log update event
            return await self.log_event('event_update', {
                'event_key': event_key,
                'update_data': update_data
            }, timestamp)
            
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def _get_event_history(self) -> Dict[str, Any]:
        """Get event history."""
        try:
            return {
                'event_history': self.event_history,
                'logged_events_count': len(self.logged_events),
                'log_path': self.log_path,
                'log_format': self.log_format,
                'log_level': self.log_level,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting event history: {e}")
            return {
                'event_history': [],
                'logged_events_count': 0,
                'log_path': self.log_path,
                'log_format': self.log_format,
                'log_level': self.log_level,
                'mode_agnostic': True,
                'error': str(e)
            }
    
    def _validate_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate event before logging."""
        try:
            # Check if event_type is provided
            if not event_type:
                return {
                    'valid': False,
                    'error': "Event type is required"
                }
            
            # Check if event_data is a dictionary
            if not isinstance(event_data, dict):
                return {
                    'valid': False,
                    'error': "Event data must be a dictionary"
                }
            
            # Check for required fields based on event type
            required_fields = self._get_required_fields(event_type)
            for field in required_fields:
                if field not in event_data:
                    return {
                        'valid': False,
                        'error': f"Missing required field for {event_type}: {field}"
                    }
            
            return {'valid': True}
        except Exception as e:
            logger.error(f"Error validating event: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _get_required_fields(self, event_type: str) -> List[str]:
        """Get required fields for event type."""
        try:
            # Define required fields for each event type
            required_fields_map = {
                'gas_fee': ['gas_used', 'gas_price', 'total_cost'],
                'stake': ['amount', 'venue', 'asset'],
                'aave_supply': ['amount', 'asset', 'venue'],
                'aave_borrow': ['amount', 'asset', 'venue'],
                'atomic_transaction': ['instructions', 'execution_id'],
                'perp_trade': ['amount', 'asset', 'venue', 'trade_type'],
                'funding_payment': ['amount', 'venue', 'symbol'],
                'venue_transfer': ['amount', 'asset', 'from_venue', 'to_venue'],
                'rebalance': ['rebalance_type', 'amount', 'asset'],
                'risk_alert': ['risk_level', 'risk_type', 'message'],
                'seasonal_reward_distribution': ['amount', 'asset', 'venue'],
                'event_update': ['event_key', 'update_data']
            }
            
            return required_fields_map.get(event_type, [])
        except Exception as e:
            logger.error(f"Error getting required fields for {event_type}: {e}")
            return []
    
    async def _log_event_json(self, event_record: Dict[str, Any]) -> Dict[str, Any]:
        """Log event in JSON format."""
        try:
            # Create log directory if it doesn't exist
            os.makedirs(self.log_path, exist_ok=True)
            
            # Create filename
            timestamp = event_record['timestamp']
            filename = f"events_{timestamp.strftime('%Y%m%d')}.json"
            filepath = os.path.join(self.log_path, filename)
            
            # Append event to file
            with open(filepath, 'a') as f:
                f.write(json.dumps(event_record, default=str) + '\n')
            
            return {
                'success': True,
                'filepath': filepath,
                'format': 'json'
            }
        except Exception as e:
            logger.error(f"Error logging event as JSON: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _log_event_csv(self, event_record: Dict[str, Any]) -> Dict[str, Any]:
        """Log event in CSV format."""
        try:
            # Create log directory if it doesn't exist
            os.makedirs(self.log_path, exist_ok=True)
            
            # Create filename
            timestamp = event_record['timestamp']
            filename = f"events_{timestamp.strftime('%Y%m%d')}.csv"
            filepath = os.path.join(self.log_path, filename)
            
            # Convert event to CSV row
            csv_row = self._convert_event_to_csv_row(event_record)
            
            # Append event to file
            with open(filepath, 'a') as f:
                f.write(csv_row + '\n')
            
            return {
                'success': True,
                'filepath': filepath,
                'format': 'csv'
            }
        except Exception as e:
            logger.error(f"Error logging event as CSV: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _log_event_text(self, event_record: Dict[str, Any]) -> Dict[str, Any]:
        """Log event in text format."""
        try:
            # Create log directory if it doesn't exist
            os.makedirs(self.log_path, exist_ok=True)
            
            # Create filename
            timestamp = event_record['timestamp']
            filename = f"events_{timestamp.strftime('%Y%m%d')}.txt"
            filepath = os.path.join(self.log_path, filename)
            
            # Convert event to text
            text_line = self._convert_event_to_text_line(event_record)
            
            # Append event to file
            with open(filepath, 'a') as f:
                f.write(text_line + '\n')
            
            return {
                'success': True,
                'filepath': filepath,
                'format': 'text'
            }
        except Exception as e:
            logger.error(f"Error logging event as text: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _convert_event_to_csv_row(self, event_record: Dict[str, Any]) -> str:
        """Convert event record to CSV row."""
        try:
            # Extract key fields
            timestamp = event_record['timestamp']
            event_type = event_record['event_type']
            event_data = event_record['event_data']
            
            # Create CSV row
            csv_row = f"{timestamp},{event_type},{json.dumps(event_data)}"
            
            return csv_row
        except Exception as e:
            logger.error(f"Error converting event to CSV row: {e}")
            return f"{event_record.get('timestamp', '')},{event_record.get('event_type', '')},"
    
    def _convert_event_to_text_line(self, event_record: Dict[str, Any]) -> str:
        """Convert event record to text line."""
        try:
            # Extract key fields
            timestamp = event_record['timestamp']
            event_type = event_record['event_type']
            event_data = event_record['event_data']
            
            # Create text line
            text_line = f"[{timestamp}] {event_type}: {json.dumps(event_data)}"
            
            return text_line
        except Exception as e:
            logger.error(f"Error converting event to text line: {e}")
            return f"[{event_record.get('timestamp', '')}] {event_record.get('event_type', '')}: "
    
    def _get_all_events(self) -> List[Dict[str, Any]]:
        """Get all logged events."""
        return self.event_history
    
    def get_events(self, event_type: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get events with optional filtering.
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return (optional)
            
        Returns:
            List of event dictionaries
        """
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.get('event_type') == event_type]
        
        if limit:
            events = events[-limit:]  # Get most recent events
        
        return events
    
    # Standardized Logging Methods (per 17_HEALTH_ERROR_SYSTEMS.md and 08_EVENT_LOGGER.md)
    
    def log_structured_event(self, timestamp: pd.Timestamp, event_type: str, level: str, message: str, component_name: str, data: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> None:
        """Log a structured event with standardized format."""
        try:
            event_data = {
                'timestamp': timestamp,
                'event_type': event_type,
                'level': level,
                'message': message,
                'component_name': component_name,
                'data': data or {},
                'correlation_id': correlation_id
            }
            
            self.structured_logger.log_structured_event(event_data)
            self.event_history.append(event_data)
            
        except Exception as e:
            logger.error(f"Failed to log structured event: {e}")
    
    def log_component_event(self, event_type: str, message: str, data: Optional[Dict[str, Any]] = None, level: str = 'INFO') -> None:
        """Log a component-specific event with automatic timestamp and component name."""
        try:
            timestamp = pd.Timestamp.now(tz='UTC')
            event_data = {
                'timestamp': timestamp,
                'event_type': event_type,
                'level': level,
                'message': message,
                'component_name': 'EventLogger',
                'data': data or {}
            }
            
            self.structured_logger.log_component_event(event_data)
            self.event_history.append(event_data)
            
        except Exception as e:
            logger.error(f"Failed to log component event: {e}")
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a performance metric."""
        try:
            timestamp = pd.Timestamp.now(tz='UTC')
            event_data = {
                'timestamp': timestamp,
                'event_type': 'performance_metric',
                'level': 'INFO',
                'message': f"Performance metric: {metric_name} = {value} {unit}",
                'component_name': 'EventLogger',
                'data': {
                    'metric_name': metric_name,
                    'value': value,
                    'unit': unit,
                    **(data or {})
                }
            }
            
            self.structured_logger.log_performance_metric(event_data)
            self.event_history.append(event_data)
            
        except Exception as e:
            logger.error(f"Failed to log performance metric: {e}")
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> None:
        """Log an error with standardized format."""
        try:
            timestamp = pd.Timestamp.now(tz='UTC')
            event_data = {
                'timestamp': timestamp,
                'event_type': 'error',
                'level': 'ERROR',
                'message': str(error),
                'component_name': 'EventLogger',
                'data': {
                    'error_type': type(error).__name__,
                    'context': context or {},
                    'correlation_id': correlation_id
                }
            }
            
            self.structured_logger.log_error(event_data)
            self.event_history.append(event_data)
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    def log_warning(self, message: str, data: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> None:
        """Log a warning with standardized format."""
        try:
            timestamp = pd.Timestamp.now(tz='UTC')
            event_data = {
                'timestamp': timestamp,
                'event_type': 'warning',
                'level': 'WARNING',
                'message': message,
                'component_name': 'EventLogger',
                'data': data or {},
                'correlation_id': correlation_id
            }
            
            self.structured_logger.log_warning(event_data)
            self.event_history.append(event_data)
            
        except Exception as e:
            logger.error(f"Failed to log warning: {e}")
    
    def log_event(self, timestamp: pd.Timestamp, event_type: str, component: str, data: Dict) -> None:
        """Log an event with global ordering."""
        try:
            event_data = {
                'timestamp': timestamp,
                'event_type': event_type,
                'component': component,
                'data': data
            }
            
            self.structured_logger.log_event(event_data)
            self.event_history.append(event_data)
            
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs) -> None:
        """
        Update component state (called by EventDrivenStrategyEngine).
        
        Args:
            timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
            trigger_source: 'full_loop' | 'tight_loop' | 'manual'
            **kwargs: Additional parameters
        """
        # Log state update event
        self.structured_logger.info(
            "EventLogger state updated",
            event_type="state_update",
            component="event_logger",
            trigger_source=trigger_source,
            timestamp=timestamp.isoformat()
        )
    
    def _should_log_event(self, event_type: str, details: Dict[str, Any]) -> bool:
        """Check if event should be logged based on filtering configuration."""
        if not self.event_filtering.get('filter_by_category', True):
            return True
        
        # Check include patterns
        include_patterns = self.event_filtering.get('include_patterns', ['*'])
        if not any(self._matches_pattern(event_type, pattern) for pattern in include_patterns):
            return False
        
        # Check exclude patterns
        exclude_patterns = self.event_filtering.get('exclude_patterns', [])
        if any(self._matches_pattern(event_type, pattern) for pattern in exclude_patterns):
            return False
        
        return True
    
    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if event type matches pattern."""
        if pattern == '*':
            return True
        return event_type.startswith(pattern.replace('*', ''))
    
    def _get_event_category(self, event_type: str) -> str:
        """Get event category based on event type."""
        for category, events in self.event_categories.items():
            if event_type in events:
                return category
        return 'unknown'
    
    def _apply_retention_policy(self):
        """Apply log retention policy to event history."""
        if not self.log_retention_policy.get('retention_days'):
            return
        
        retention_days = self.log_retention_policy['retention_days']
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        # Remove old events
        self.event_history = [
            event for event in self.event_history
            if event.get('timestamp', datetime.now(timezone.utc)) > cutoff_date
        ]
        
        # Remove old logged events
        self.logged_events = {
            event_id: event for event_id, event in self.logged_events.items()
            if event.get('timestamp', datetime.now(timezone.utc)) > cutoff_date
        }