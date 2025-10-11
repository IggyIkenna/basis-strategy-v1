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
from datetime import datetime
import json
import os

from ....infrastructure.logging.structured_logger import get_structured_logger

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
        
        self.structured_logger.info(
            "EventLogger initialized",
            event_type="component_initialization",
            component="event_logger",
            mode="mode-agnostic"
        )
    
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
    
    def get_event_history(self) -> Dict[str, Any]:
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
    
    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all logged events."""
        return self.event_history