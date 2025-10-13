"""
Base Logging Interface for Standardized Component Logging

This module provides a standardized interface that integrates with the existing
EventLogger and StructuredLogger systems to provide consistent logging patterns
across all components without duplicating existing logging functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import os
from enum import Enum


class LogLevel(Enum):
    """Standardized log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    """Standardized event types for component events."""
    COMPONENT_INITIALIZATION = "component_initialization"
    COMPONENT_STARTUP = "component_startup"
    COMPONENT_SHUTDOWN = "component_shutdown"
    STATE_UPDATE = "state_update"
    CONFIGURATION_CHANGE = "configuration_change"
    ERROR_OCCURRED = "error_occurred"
    WARNING_OCCURRED = "warning_occurred"
    PERFORMANCE_METRIC = "performance_metric"
    BUSINESS_EVENT = "business_event"
    SYSTEM_EVENT = "system_event"


class BaseLoggingInterface(ABC):
    """
    Base interface for standardized component logging.
    
    All components should implement this interface to ensure consistent
    logging patterns across the system.
    """
    
    @abstractmethod
    def log_structured_event(
        self,
        timestamp: pd.Timestamp,
        event_type: EventType,
        level: LogLevel,
        message: str,
        component_name: str,
        data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log a structured event with standardized format.
        
        Parameters:
        - timestamp: Event timestamp
        - event_type: Type of event (from EventType enum)
        - level: Log level (from LogLevel enum)
        - message: Human-readable message
        - component_name: Name of the component logging the event
        - data: Optional structured data dictionary
        - correlation_id: Optional correlation ID for tracing
        """
        pass
    
    @abstractmethod
    def log_component_event(
        self,
        event_type: EventType,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        level: LogLevel = LogLevel.INFO
    ) -> None:
        """
        Log a component-specific event with automatic timestamp and component name.
        
        Parameters:
        - event_type: Type of event (from EventType enum)
        - message: Human-readable message
        - data: Optional structured data dictionary
        - level: Log level (defaults to INFO)
        """
        pass
    
    @abstractmethod
    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a performance metric.
        
        Parameters:
        - metric_name: Name of the metric
        - value: Metric value
        - unit: Unit of measurement
        - data: Optional additional context data
        """
        pass
    
    @abstractmethod
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log an error with standardized format.
        
        Parameters:
        - error: Exception object
        - context: Optional context data
        - correlation_id: Optional correlation ID for tracing
        """
        pass
    
    @abstractmethod
    def log_warning(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log a warning with standardized format.
        
        Parameters:
        - message: Warning message
        - data: Optional context data
        - correlation_id: Optional correlation ID for tracing
        """
        pass


class StandardizedLoggingMixin:
    """
    Mixin class that provides standardized logging methods for components.
    
    This mixin integrates with the existing EventLogger and StructuredLogger systems
    to provide consistent logging patterns without duplicating existing functionality.
    Components can inherit from this mixin to get standardized logging methods.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._component_name = self.__class__.__name__
        self._event_logger = None  # Will be set by dependency injection (existing EventLogger)
        self._structured_logger = None  # Will be set by dependency injection (existing StructuredLogger)
        self._log_level = self._get_log_level_from_env()
        self._debug_mode = self._get_debug_mode_from_env()
    
    def _get_log_level_from_env(self) -> LogLevel:
        """Get log level from environment variable."""
        log_level_str = os.getenv('BASIS_LOG_LEVEL', 'INFO').upper()
        try:
            return LogLevel(log_level_str)
        except ValueError:
            return LogLevel.INFO  # Default to INFO if invalid
    
    def _get_debug_mode_from_env(self) -> bool:
        """Get debug mode from environment variable."""
        debug_str = os.getenv('BASIS_DEBUG', 'false').lower()
        return debug_str in ('true', '1', 'yes', 'on')
    
    def set_loggers(self, event_logger=None, structured_logger=None):
        """Set the existing EventLogger and StructuredLogger instances."""
        self._event_logger = event_logger
        self._structured_logger = structured_logger
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if we should log based on environment log level."""
        # Define log level hierarchy
        level_hierarchy = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        
        # Always log if debug mode is enabled
        if self._debug_mode:
            return True
            
        # Check if the message level is at or above the configured log level
        return level_hierarchy.get(level, 1) >= level_hierarchy.get(self._log_level, 1)
    
    def log_structured_event(
        self,
        timestamp: pd.Timestamp,
        event_type: EventType,
        level: LogLevel,
        message: str,
        component_name: str,
        data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """Log a structured event using existing StructuredLogger."""
        if self._structured_logger:
            # Use existing structured logger
            self._structured_logger.log(
                level=level.value,
                message=message,
                component=component_name,
                event_type=event_type.value,
                correlation_id=correlation_id,
                metadata=data
            )
    
    def log_component_event(
        self,
        event_type: EventType,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        level: LogLevel = LogLevel.INFO
    ) -> None:
        """Log a component-specific event with automatic timestamp and component name."""
        # Check if we should log based on environment log level
        if not self._should_log(level):
            return
            
        if self._logger:
            self._logger.log_structured_event(
                timestamp=pd.Timestamp.now(),
                event_type=event_type,
                level=level,
                message=message,
                component_name=self._component_name,
                data=data
            )
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a performance metric."""
        # Performance metrics are typically INFO level
        if not self._should_log(LogLevel.INFO):
            return
            
        if self._logger:
            self._logger.log_structured_event(
                timestamp=pd.Timestamp.now(),
                event_type=EventType.PERFORMANCE_METRIC,
                level=LogLevel.INFO,
                message=f"Performance metric: {metric_name} = {value} {unit}",
                component_name=self._component_name,
                data={
                    'metric_name': metric_name,
                    'value': value,
                    'unit': unit,
                    **(data or {})
                }
            )
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """Log an error with standardized format and error codes."""
        # Errors should always be logged regardless of log level
        if self._structured_logger:
            # Extract error code if available (from ComponentError or similar)
            error_code = getattr(error, 'error_code', 'UNKNOWN_ERROR')
            
            self._structured_logger.log(
                level=LogLevel.ERROR.value,
                message=f"Error in {self._component_name}: {str(error)}",
                component=self._component_name,
                event_type=EventType.ERROR_OCCURRED.value,
                correlation_id=correlation_id,
                metadata={
                    'error_type': type(error).__name__,
                    'error_message': str(error),
                    'error_code': error_code,
                    **(context or {})
                }
            )
    
    def log_warning(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """Log a warning with standardized format."""
        # Check if we should log warnings based on log level
        if not self._should_log(LogLevel.WARNING):
            return
            
        if self._logger:
            self._logger.log_structured_event(
                timestamp=pd.Timestamp.now(),
                event_type=EventType.WARNING_OCCURRED,
                level=LogLevel.WARNING,
                message=f"Warning in {self._component_name}: {message}",
                component_name=self._component_name,
                data=data,
                correlation_id=correlation_id
            )
