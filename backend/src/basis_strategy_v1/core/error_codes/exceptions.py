"""
Component Error Exceptions

Structured error handling with error codes for all system components.
Provides consistent error handling across the entire system.

Reference: docs/specs/17_HEALTH_ERROR_SYSTEMS.md
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Health System Architecture
"""

from typing import Dict, Optional, Any
import traceback
import logging
from .error_code_registry import get_error_info, ErrorCodeInfo, ErrorSeverity

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

logger = logging.getLogger(__name__)


class ComponentError(Exception):
    """Structured component error with error code and context."""
    
    def __init__(self, error_code: str, message: str = None, component: str = None, 
                 severity: str = None, original_exception: Exception = None, **kwargs):
        """
        Initialize component error.
        
        Args:
            error_code: Error code (e.g., 'POS-001')
            message: Custom error message (optional)
            component: Component name (optional, will be inferred from error code)
            severity: Error severity (optional, will be inferred from error code)
            original_exception: Original exception that caused this error (optional)
            **kwargs: Additional context data
        """
        # Get error code information
        error_info = get_error_info(error_code)
        
        if error_info:
            self.error_code = error_code
            self.component = component or error_info.component
            self.severity = severity or error_info.severity.value
            self.description = error_info.description
            self.resolution = error_info.resolution
            
            # Use provided message or default from error code
            self.message = message or error_info.message
        else:
            # Fallback if error code not found
            self.error_code = error_code
            self.component = component or "Unknown"
            self.severity = severity or "HIGH"
            self.message = message or f"Unknown error: {error_code}"
            self.description = "Error code not found in registry"
            self.resolution = "Contact system administrator"
        
        # Store additional context
        self.context = kwargs
        self.original_exception = original_exception
        
        # Create the full error message
        full_message = f"{self.error_code}: {self.message}"
        if self.context:
            context_str = ", ".join([f"{k}={v}" for k, v in self.context.items()])
            full_message += f" ({context_str})"
        
        super().__init__(full_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            'error_code': self.error_code,
            'component': self.component,
            'severity': self.severity,
            'message': self.message,
            'description': self.description,
            'resolution': self.resolution,
            'context': self.context,
            'original_exception': str(self.original_exception) if self.original_exception else None,
            'traceback': traceback.format_exc() if self.original_exception else None
        }
    
    def log_error(self, logger_instance: Optional[logging.Logger] = None):
        """Log the error with appropriate level based on severity."""
        log_logger = logger_instance or logger
        
        if self.severity == "CRITICAL":
            log_logger.critical(f"{self.error_code}: {self.message}", extra=self.to_dict())
        elif self.severity == "HIGH":
            log_logger.error(f"{self.error_code}: {self.message}", extra=self.to_dict())
        elif self.severity == "MEDIUM":
            log_logger.warning(f"{self.error_code}: {self.message}", extra=self.to_dict())
        else:  # LOW
            log_logger.info(f"{self.error_code}: {self.message}", extra=self.to_dict())


class ValidationError(ComponentError):
    """Error for validation failures."""
    
    def __init__(self, error_code: str, message: str = None, **kwargs):
        super().__init__(error_code, message, severity="MEDIUM", **kwargs)


class ConfigurationError(ComponentError):
    """Error for configuration issues."""
    
    def __init__(self, error_code: str, message: str = None, **kwargs):
        super().__init__(error_code, message, severity="HIGH", **kwargs)


class ExecutionError(ComponentError):
    """Error for execution failures."""
    
    def __init__(self, error_code: str, message: str = None, **kwargs):
        super().__init__(error_code, message, severity="HIGH", **kwargs)


class DataError(ComponentError):
    """Error for data-related issues."""
    
    def __init__(self, error_code: str, message: str = None, **kwargs):
        super().__init__(error_code, message, severity="HIGH", **kwargs)


class HealthError(ComponentError):
    """Error for health system issues."""
    
    def __init__(self, error_code: str, message: str = None, **kwargs):
        super().__init__(error_code, message, severity="CRITICAL", **kwargs)


def create_component_error(error_code: str, message: str = None, **kwargs) -> ComponentError:
    """Factory function to create component errors."""
    return ComponentError(error_code, message, **kwargs)


def create_validation_error(error_code: str, message: str = None, **kwargs) -> ValidationError:
    """Factory function to create validation errors."""
    return ValidationError(error_code, message, **kwargs)


def create_configuration_error(error_code: str, message: str = None, **kwargs) -> ConfigurationError:
    """Factory function to create configuration errors."""
    return ConfigurationError(error_code, message, **kwargs)


def create_execution_error(error_code: str, message: str = None, **kwargs) -> ExecutionError:
    """Factory function to create execution errors."""
    return ExecutionError(error_code, message, **kwargs)


def create_data_error(error_code: str, message: str = None, **kwargs) -> DataError:
    """Factory function to create data errors."""
    return DataError(error_code, message, **kwargs)


def create_health_error(error_code: str, message: str = None, **kwargs) -> HealthError:
    """Factory function to create health errors."""
    return HealthError(error_code, message, **kwargs)
