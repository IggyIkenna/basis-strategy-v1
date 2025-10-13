"""
Component Error - Structured error handling for components.
"""

from typing import Dict, Any, Optional


class ComponentError(Exception):
    """
    Structured error for component failures.
    
    Provides consistent error handling across all components with
    error codes, severity levels, and detailed context.
    """
    
    def __init__(
        self,
        component: str,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        severity: str = 'HIGH',
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize component error.
        
        Args:
            component: Component name that generated the error
            error_code: Unique error code (e.g., 'VM-001')
            message: Human-readable error message
            details: Additional error context
            severity: Error severity ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
            original_exception: Original exception that caused this error
        """
        self.component = component
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.severity = severity
        self.original_exception = original_exception
        
        # Create full error message
        full_message = f"[{component}:{error_code}] {message}"
        if self.details:
            full_message += f" | Details: {self.details}"
        
        super().__init__(full_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            'component': self.component,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'severity': self.severity,
            'original_exception': str(self.original_exception) if self.original_exception else None
        }
    
    def __str__(self) -> str:
        """String representation of the error."""
        return f"[{self.component}:{self.error_code}] {self.message}"
