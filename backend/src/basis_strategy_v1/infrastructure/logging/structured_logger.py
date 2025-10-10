"""
Structured Logger

Provides structured logging for all system components with consistent formatting,
log levels, and integration with the Event Logger for strategy events.

Reference: docs/specs/08_EVENT_LOGGER.md - Event logger specification
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 10 (Health System Architecture)
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
import structlog

logger = logging.getLogger(__name__)


@dataclass
class LogEvent:
    """Structured log event."""
    timestamp: str
    level: str
    component: str
    message: str
    event_type: Optional[str] = None
    correlation_id: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class StructuredLogger:
    """Structured logger for system components."""
    
    def __init__(self, component_name: str, event_logger=None):
        self.component_name = component_name
        self.event_logger = event_logger
        self.correlation_id = None
        
        # Set up structured logging
        self.logger = structlog.get_logger(component_name)
        
        # Configure log levels
        self.log_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for request tracing."""
        self.correlation_id = correlation_id
    
    def _create_log_event(
        self,
        level: str,
        message: str,
        event_type: Optional[str] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LogEvent:
        """Create a structured log event."""
        return LogEvent(
            timestamp=datetime.now().isoformat(),
            level=level,
            component=self.component_name,
            message=message,
            event_type=event_type,
            correlation_id=self.correlation_id,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
    
    def _log_event(self, log_event: LogEvent):
        """Log the event using structured logging."""
        # Convert to dict for structured logging
        event_dict = log_event.to_dict()
        
        # Log using appropriate level
        level = self.log_levels.get(log_event.level, logging.INFO)
        
        if level == logging.DEBUG:
            self.logger.debug(log_event.message, **event_dict)
        elif level == logging.INFO:
            self.logger.info(log_event.message, **event_dict)
        elif level == logging.WARNING:
            self.logger.warning(log_event.message, **event_dict)
        elif level == logging.ERROR:
            self.logger.error(log_event.message, **event_dict)
        elif level == logging.CRITICAL:
            self.logger.critical(log_event.message, **event_dict)
        
        # Also send to event logger if available
        if self.event_logger:
            try:
                self.event_logger.log_event(
                    event_type=log_event.event_type or 'log',
                    level=log_event.level,
                    message=log_event.message,
                    metadata=event_dict
                )
            except Exception as e:
                # Don't let event logger errors break logging
                self.logger.error(f"Failed to log to event logger: {e}")
    
    def debug(self, message: str, event_type: Optional[str] = None, **kwargs):
        """Log debug message."""
        log_event = self._create_log_event(
            level='DEBUG',
            message=message,
            event_type=event_type,
            metadata=kwargs
        )
        self._log_event(log_event)
    
    def info(self, message: str, event_type: Optional[str] = None, **kwargs):
        """Log info message."""
        log_event = self._create_log_event(
            level='INFO',
            message=message,
            event_type=event_type,
            metadata=kwargs
        )
        self._log_event(log_event)
    
    def warning(self, message: str, event_type: Optional[str] = None, **kwargs):
        """Log warning message."""
        log_event = self._create_log_event(
            level='WARNING',
            message=message,
            event_type=event_type,
            metadata=kwargs
        )
        self._log_event(log_event)
    
    def error(self, message: str, event_type: Optional[str] = None, **kwargs):
        """Log error message."""
        log_event = self._create_log_event(
            level='ERROR',
            message=message,
            event_type=event_type,
            metadata=kwargs
        )
        self._log_event(log_event)
    
    def critical(self, message: str, event_type: Optional[str] = None, **kwargs):
        """Log critical message."""
        log_event = self._create_log_event(
            level='CRITICAL',
            message=message,
            event_type=event_type,
            metadata=kwargs
        )
        self._log_event(log_event)
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        **kwargs
    ):
        """Log performance metrics."""
        level = 'INFO' if success else 'WARNING'
        message = f"Performance: {operation} completed in {duration_ms:.2f}ms"
        
        log_event = self._create_log_event(
            level=level,
            message=message,
            event_type='performance',
            duration_ms=duration_ms,
            metadata={
                'operation': operation,
                'success': success,
                **kwargs
            }
        )
        self._log_event(log_event)
    
    def log_business_event(
        self,
        event_type: str,
        message: str,
        level: str = 'INFO',
        **kwargs
    ):
        """Log business event (strategy events, trades, etc.)."""
        log_event = self._create_log_event(
            level=level,
            message=message,
            event_type=event_type,
            metadata=kwargs
        )
        self._log_event(log_event)
    
    def log_component_health(
        self,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log component health status."""
        level = 'INFO' if status == 'healthy' else 'WARNING' if status == 'degraded' else 'ERROR'
        
        log_event = self._create_log_event(
            level=level,
            message=f"Health check: {message}",
            event_type='health',
            metadata={
                'status': status,
                'details': details or {}
            }
        )
        self._log_event(log_event)
    
    def log_data_event(
        self,
        operation: str,
        data_type: str,
        success: bool = True,
        **kwargs
    ):
        """Log data-related events."""
        level = 'INFO' if success else 'ERROR'
        message = f"Data {operation}: {data_type}"
        
        log_event = self._create_log_event(
            level=level,
            message=message,
            event_type='data',
            metadata={
                'operation': operation,
                'data_type': data_type,
                'success': success,
                **kwargs
            }
        )
        self._log_event(log_event)
    
    def log_strategy_event(
        self,
        strategy_name: str,
        event_type: str,
        message: str,
        level: str = 'INFO',
        **kwargs
    ):
        """Log strategy-specific events."""
        log_event = self._create_log_event(
            level=level,
            message=f"[{strategy_name}] {message}",
            event_type=f'strategy_{event_type}',
            metadata={
                'strategy_name': strategy_name,
                'strategy_event_type': event_type,
                **kwargs
            }
        )
        self._log_event(log_event)
    
    def log_event(
        self,
        level: str,
        message: str,
        event_type: str = 'log',
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Generic event logging method for compatibility."""
        # Merge kwargs into metadata
        if metadata is None:
            metadata = {}
        metadata.update(kwargs)
        
        log_event = self._create_log_event(
            level=level,
            message=message,
            event_type=event_type,
            metadata=metadata
        )
        self._log_event(log_event)


def get_structured_logger(component_name: str, event_logger=None) -> StructuredLogger:
    """Get a structured logger for a component."""
    return StructuredLogger(component_name, event_logger)


# Global logger instances for common components
_position_monitor_logger = None
_risk_monitor_logger = None
_strategy_manager_logger = None
_data_provider_logger = None
_execution_manager_logger = None


def get_position_monitor_logger(event_logger=None) -> StructuredLogger:
    """Get logger for Position Monitor component."""
    global _position_monitor_logger
    if _position_monitor_logger is None:
        _position_monitor_logger = get_structured_logger('position_monitor', event_logger)
    return _position_monitor_logger


def get_risk_monitor_logger(event_logger=None) -> StructuredLogger:
    """Get logger for Risk Monitor component."""
    global _risk_monitor_logger
    if _risk_monitor_logger is None:
        _risk_monitor_logger = get_structured_logger('risk_monitor', event_logger)
    return _risk_monitor_logger


def get_strategy_manager_logger(event_logger=None) -> StructuredLogger:
    """Get logger for Strategy Manager component."""
    global _strategy_manager_logger
    if _strategy_manager_logger is None:
        _strategy_manager_logger = get_structured_logger('strategy_manager', event_logger)
    return _strategy_manager_logger


def get_data_provider_logger(event_logger=None) -> StructuredLogger:
    """Get logger for Data Provider component."""
    global _data_provider_logger
    if _data_provider_logger is None:
        _data_provider_logger = get_structured_logger('data_provider', event_logger)
    return _data_provider_logger


def get_execution_manager_logger(event_logger=None) -> StructuredLogger:
    """Get logger for Execution Manager component."""
    global _execution_manager_logger
    if _execution_manager_logger is None:
        _execution_manager_logger = get_structured_logger('execution_manager', event_logger)
    return _execution_manager_logger