"""
Mode-Agnostic Logging Interface

Provides mode-agnostic logging interface that works for both backtest and live modes.
Manages logging across all venues and provides generic logging logic.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/15_LOGGING_INTERFACE.md - Mode-agnostic logging management
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

class LoggingInterface:
    """Mode-agnostic logging interface that works for both backtest and live modes"""
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize logging interface.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
        """
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        
        # Logging tracking
        self.log_history = []
        self.logged_messages = {}
        
        # Logging configuration
        self.log_path = config.get('log_path', './logs')
        self.log_format = config.get('log_format', 'json')
        self.log_level = config.get('log_level', 'INFO')
        
        logger.info("LoggingInterface initialized (mode-agnostic)")
    
    async def log_message(self, level: str, message: str, context: Dict[str, Any], 
                         timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Log message regardless of mode (backtest or live).
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            context: Additional context data
            timestamp: Current timestamp
            
        Returns:
            Dictionary with logging result
        """
        try:
            # Validate log message
            validation_result = self._validate_log_message(level, message, context)
            if not validation_result['valid']:
                return {
                    'status': 'failed',
                    'error': validation_result['error'],
                    'timestamp': timestamp
                }
            
            # Create log record
            log_record = {
                'level': level,
                'message': message,
                'context': context,
                'timestamp': timestamp,
                'log_format': self.log_format
            }
            
            # Log message based on format
            if self.log_format == 'json':
                log_result = await self._log_message_json(log_record)
            elif self.log_format == 'csv':
                log_result = await self._log_message_csv(log_record)
            elif self.log_format == 'text':
                log_result = await self._log_message_text(log_record)
            else:
                return {
                    'status': 'failed',
                    'error': f"Unsupported log format: {self.log_format}",
                    'timestamp': timestamp
                }
            
            if log_result['success']:
                # Add to log history
                self.log_history.append(log_record)
                
                # Add to logged messages
                message_key = f"{level}_{timestamp.timestamp()}"
                self.logged_messages[message_key] = log_record
                
                logger.info(f"Successfully logged message: {level} - {message}")
            else:
                logger.error(f"Failed to log message: {level} - {message}: {log_result.get('error', 'Unknown error')}")
            
            return {
                'status': 'success' if log_result['success'] else 'failed',
                'timestamp': timestamp,
                'log_result': log_result
            }
            
        except Exception as e:
            logger.error(f"Error logging message: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_debug(self, message: str, context: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log debug message."""
        try:
            return await self.log_message('DEBUG', message, context, timestamp)
        except Exception as e:
            logger.error(f"Error logging debug message: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_info(self, message: str, context: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log info message."""
        try:
            return await self.log_message('INFO', message, context, timestamp)
        except Exception as e:
            logger.error(f"Error logging info message: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_warning(self, message: str, context: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log warning message."""
        try:
            return await self.log_message('WARNING', message, context, timestamp)
        except Exception as e:
            logger.error(f"Error logging warning message: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_error(self, message: str, context: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log error message."""
        try:
            return await self.log_message('ERROR', message, context, timestamp)
        except Exception as e:
            logger.error(f"Error logging error message: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_critical(self, message: str, context: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log critical message."""
        try:
            return await self.log_message('CRITICAL', message, context, timestamp)
        except Exception as e:
            logger.error(f"Error logging critical message: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_performance(self, performance_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log performance data."""
        try:
            return await self.log_message('PERFORMANCE', 'Performance metrics', performance_data, timestamp)
        except Exception as e:
            logger.error(f"Error logging performance data: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_metrics(self, metrics_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log metrics data."""
        try:
            return await self.log_message('METRICS', 'System metrics', metrics_data, timestamp)
        except Exception as e:
            logger.error(f"Error logging metrics data: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def log_audit(self, audit_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Log audit data."""
        try:
            return await self.log_message('AUDIT', 'Audit trail', audit_data, timestamp)
        except Exception as e:
            logger.error(f"Error logging audit data: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def get_log_history(self) -> Dict[str, Any]:
        """Get log history."""
        try:
            return {
                'log_history': self.log_history,
                'logged_messages_count': len(self.logged_messages),
                'log_path': self.log_path,
                'log_format': self.log_format,
                'log_level': self.log_level,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting log history: {e}")
            return {
                'log_history': [],
                'logged_messages_count': 0,
                'log_path': self.log_path,
                'log_format': self.log_format,
                'log_level': self.log_level,
                'mode_agnostic': True,
                'error': str(e)
            }
    
    def _validate_log_message(self, level: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate log message before logging."""
        try:
            # Check if level is valid
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'PERFORMANCE', 'METRICS', 'AUDIT']
            if level not in valid_levels:
                return {
                    'valid': False,
                    'error': f"Invalid log level: {level}"
                }
            
            # Check if message is provided
            if not message:
                return {
                    'valid': False,
                    'error': "Log message is required"
                }
            
            # Check if context is a dictionary
            if not isinstance(context, dict):
                return {
                    'valid': False,
                    'error': "Context must be a dictionary"
                }
            
            return {'valid': True}
        except Exception as e:
            logger.error(f"Error validating log message: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    async def _log_message_json(self, log_record: Dict[str, Any]) -> Dict[str, Any]:
        """Log message in JSON format."""
        try:
            # Create log directory if it doesn't exist
            os.makedirs(self.log_path, exist_ok=True)
            
            # Create filename
            timestamp = log_record['timestamp']
            filename = f"logs_{timestamp.strftime('%Y%m%d')}.json"
            filepath = os.path.join(self.log_path, filename)
            
            # Append log to file
            with open(filepath, 'a') as f:
                f.write(json.dumps(log_record, default=str) + '\n')
            
            return {
                'success': True,
                'filepath': filepath,
                'format': 'json'
            }
        except Exception as e:
            logger.error(f"Error logging message as JSON: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _log_message_csv(self, log_record: Dict[str, Any]) -> Dict[str, Any]:
        """Log message in CSV format."""
        try:
            # Create log directory if it doesn't exist
            os.makedirs(self.log_path, exist_ok=True)
            
            # Create filename
            timestamp = log_record['timestamp']
            filename = f"logs_{timestamp.strftime('%Y%m%d')}.csv"
            filepath = os.path.join(self.log_path, filename)
            
            # Convert log to CSV row
            csv_row = self._convert_log_to_csv_row(log_record)
            
            # Append log to file
            with open(filepath, 'a') as f:
                f.write(csv_row + '\n')
            
            return {
                'success': True,
                'filepath': filepath,
                'format': 'csv'
            }
        except Exception as e:
            logger.error(f"Error logging message as CSV: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _log_message_text(self, log_record: Dict[str, Any]) -> Dict[str, Any]:
        """Log message in text format."""
        try:
            # Create log directory if it doesn't exist
            os.makedirs(self.log_path, exist_ok=True)
            
            # Create filename
            timestamp = log_record['timestamp']
            filename = f"logs_{timestamp.strftime('%Y%m%d')}.txt"
            filepath = os.path.join(self.log_path, filename)
            
            # Convert log to text
            text_line = self._convert_log_to_text_line(log_record)
            
            # Append log to file
            with open(filepath, 'a') as f:
                f.write(text_line + '\n')
            
            return {
                'success': True,
                'filepath': filepath,
                'format': 'text'
            }
        except Exception as e:
            logger.error(f"Error logging message as text: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _convert_log_to_csv_row(self, log_record: Dict[str, Any]) -> str:
        """Convert log record to CSV row."""
        try:
            # Extract key fields
            timestamp = log_record['timestamp']
            level = log_record['level']
            message = log_record['message']
            context = log_record['context']
            
            # Create CSV row
            csv_row = f"{timestamp},{level},{message},{json.dumps(context)}"
            
            return csv_row
        except Exception as e:
            logger.error(f"Error converting log to CSV row: {e}")
            return f"{log_record.get('timestamp', '')},{log_record.get('level', '')},{log_record.get('message', '')},{}"
    
    def _convert_log_to_text_line(self, log_record: Dict[str, Any]) -> str:
        """Convert log record to text line."""
        try:
            # Extract key fields
            timestamp = log_record['timestamp']
            level = log_record['level']
            message = log_record['message']
            context = log_record['context']
            
            # Create text line
            text_line = f"[{timestamp}] {level}: {message} | Context: {json.dumps(context)}"
            
            return text_line
        except Exception as e:
            logger.error(f"Error converting log to text line: {e}")
            return f"[{log_record.get('timestamp', '')}] {log_record.get('level', '')}: {log_record.get('message', '')} | Context: {}"
