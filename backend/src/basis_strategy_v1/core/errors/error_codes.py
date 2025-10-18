"""
Error Code Registry and Component Error Exception

This module defines the static error code registry and ComponentError exception
for structured error handling across the system.

All error codes follow the format: {COMPONENT}-{NUMBER}
Example: EXP-001, EXEC-002, VEN-003

Reference: docs/ERROR_HANDLING_PATTERNS.md - Error Code Standards
Reference: docs/HEALTH_ERROR_SYSTEMS.md - Error Propagation
"""

from typing import Optional


# Static Error Code Registry
# Format: {COMPONENT}-{NUMBER}: Description
ERROR_REGISTRY = {
    # Position Monitor (POS-XXX)
    'POS-001': 'Position reconciliation mismatch',
    'POS-002': 'Invalid position delta',
    'POS-003': 'Position state unavailable',
    'POS-004': 'Position update failed',
    'POS-005': 'Position query timeout',
    
    # Exposure Monitor (EXP-XXX)
    'EXP-001': 'Exposure calculation failed',
    'EXP-002': 'Missing market data for exposure',
    'EXP-003': 'Position data unavailable',
    'EXP-004': 'Invalid exposure configuration',
    'EXP-005': 'Asset conversion failed',
    
    # Risk Monitor (RISK-XXX)
    'RISK-001': 'Health factor calculation failed',
    'RISK-002': 'LTV ratio exceeds threshold',
    'RISK-003': 'Margin call triggered',
    'RISK-004': 'Risk limit breach detected',
    'RISK-005': 'Liquidation threshold exceeded',
    'RISK-006': 'Risk assessment failed',
    
    # PnL Monitor (PNL-XXX)
    'PNL-001': 'PnL calculation failed',
    'PNL-002': 'Missing price data',
    'PNL-003': 'Historical data unavailable',
    'PNL-004': 'Attribution calculation failed',
    'PNL-005': 'Settlement calculation failed',
    
    # Execution Manager (EXEC-XXX)
    'EXEC-001': 'Order execution failed',
    'EXEC-002': 'Execution timeout',
    'EXEC-003': 'Tight loop reconciliation failed',
    'EXEC-004': 'System failure triggered',
    'EXEC-005': 'Atomic group execution failed',
    'EXEC-006': 'Retry limit exceeded',
    'EXEC-007': 'Invalid order parameters',
    'EXEC-008': 'Execution handshake validation failed',
    
    # Venue Interface Manager (VEN-XXX)
    'VEN-001': 'Venue routing failed',
    'VEN-002': 'Venue timeout',
    'VEN-003': 'Venue unavailable',
    'VEN-004': 'Venue interface not found',
    'VEN-005': 'Venue authentication failed',
    'VEN-006': 'Venue rate limit exceeded',
    
    # Event Logger (LOG-XXX)
    'LOG-001': 'Failed to write event file',
    'LOG-002': 'Event buffer overflow',
    'LOG-003': 'Log directory creation failed',
    'LOG-004': 'Event serialization failed',
    'LOG-005': 'Log file rotation failed',
    
    # Strategy Manager (STRAT-XXX)
    'STRAT-001': 'Strategy decision failed',
    'STRAT-002': 'Expected deltas calculation failed',
    'STRAT-003': 'Invalid order generated',
    'STRAT-004': 'Strategy initialization failed',
    'STRAT-005': 'Target position calculation failed',
    'STRAT-006': 'Market data unavailable for strategy',
    
    # Data Provider (DATA-XXX)
    'DATA-001': 'Data fetch failed',
    'DATA-002': 'Data validation failed',
    'DATA-003': 'Data source unavailable',
    'DATA-004': 'Historical data gap detected',
    'DATA-005': 'Price data missing',
    
    # Utility Manager (UTIL-XXX)
    'UTIL-001': 'Price conversion failed',
    'UTIL-002': 'Index fetch failed',
    'UTIL-003': 'Rate calculation failed',
    'UTIL-004': 'Token metadata unavailable',
    
    # Configuration (CONFIG-XXX)
    'CONFIG-001': 'Invalid mode configuration',
    'CONFIG-002': 'Missing required configuration',
    'CONFIG-003': 'Configuration validation failed',
    'CONFIG-004': 'Venue configuration invalid',
    
    # Engine (ENGINE-XXX)
    'ENGINE-001': 'Engine initialization failed',
    'ENGINE-002': 'Component initialization failed',
    'ENGINE-003': 'Engine state inconsistency',
    'ENGINE-004': 'Critical system error',
}


class ComponentError(Exception):
    """
    Exception for critical component errors that should stop execution.
    
    Use this exception for FAIL-FAST scenarios where the system cannot
    continue safely:
    - Invalid configuration at startup
    - Missing required dependencies
    - Critical resource unavailability
    - Data integrity violations
    
    For runtime errors that should be logged and handled gracefully,
    use structured logging instead:
        logger.error(
            "Error message",
            error_code="COMPONENT-XXX",
            exc_info=exception,
            extra={...}
        )
    
    Reference: docs/ERROR_HANDLING_PATTERNS.md - Raise vs Log Decision Tree
    
    Examples:
        # Fail-fast at initialization
        raise ComponentError(
            error_code='CONFIG-001',
            message='Invalid mode configuration: missing required field "share_class"',
            component='EventDrivenStrategyEngine',
            severity='CRITICAL'
        )
        
        # Runtime error - DON'T raise, LOG instead
        logger.error(
            "Exposure calculation failed",
            error_code="EXP-001",
            exc_info=e,
            extra={'asset': asset, 'severity': 'HIGH'}
        )
    """
    
    def __init__(
        self, 
        error_code: str, 
        message: str, 
        component: str, 
        severity: str,
        details: Optional[dict] = None
    ):
        """
        Initialize ComponentError.
        
        Args:
            error_code: Error code from ERROR_REGISTRY
            message: Detailed error message
            component: Component name where error occurred
            severity: Error severity ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
            details: Additional error details (optional)
        """
        self.error_code = error_code
        self.message = message
        self.component = component
        self.severity = severity
        self.details = details or {}
        
        # Validate error code exists in registry
        if error_code not in ERROR_REGISTRY:
            # Log warning but don't fail on invalid error code
            print(f"WARNING: Error code '{error_code}' not found in ERROR_REGISTRY")
        
        # Format exception message
        error_desc = ERROR_REGISTRY.get(error_code, "Unknown error")
        super().__init__(
            f"[{error_code}] {component} ({severity}): {message} | {error_desc}"
        )
    
    def to_dict(self) -> dict:
        """Convert error to dictionary for logging."""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'component': self.component,
            'severity': self.severity,
            'description': ERROR_REGISTRY.get(self.error_code, "Unknown error"),
            'details': self.details
        }


def get_error_description(error_code: str) -> str:
    """
    Get human-readable description for an error code.
    
    Args:
        error_code: Error code to look up
        
    Returns:
        Error description string
    """
    return ERROR_REGISTRY.get(error_code, f"Unknown error code: {error_code}")


def validate_error_code(error_code: str) -> bool:
    """
    Validate that an error code exists in the registry.
    
    Args:
        error_code: Error code to validate
        
    Returns:
        True if error code exists, False otherwise
    """
    return error_code in ERROR_REGISTRY


def get_component_error_codes(component_prefix: str) -> dict:
    """
    Get all error codes for a specific component.
    
    Args:
        component_prefix: Component prefix (e.g., 'EXP', 'RISK', 'EXEC')
        
    Returns:
        Dictionary of error codes for the component
    """
    return {
        code: desc 
        for code, desc in ERROR_REGISTRY.items() 
        if code.startswith(component_prefix + '-')
    }

