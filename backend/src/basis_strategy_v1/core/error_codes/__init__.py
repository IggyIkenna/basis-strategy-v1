"""
Error Codes Module

Provides centralized error code management and structured error logging.
"""

from .error_code_registry import (
    ErrorCodeRegistry,
    ErrorCodeInfo,
    ErrorSeverity,
    error_code_registry,
    get_error_info,
    validate_error_code,
    get_component_error_codes
)

__all__ = [
    'ErrorCodeRegistry',
    'ErrorCodeInfo', 
    'ErrorSeverity',
    'error_code_registry',
    'get_error_info',
    'validate_error_code',
    'get_component_error_codes'
]


