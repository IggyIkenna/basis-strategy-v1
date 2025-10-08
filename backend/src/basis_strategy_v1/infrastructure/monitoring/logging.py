"""Structured logging setup."""

import structlog
import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime

from ...core.error_codes import get_error_info, ErrorSeverity


def setup_logging(log_level: str = "INFO", log_format: str = "json"):
    """
    Set up structured logging with structlog.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Output format (json or console)
    """
    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add appropriate renderer based on format
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (defaults to module name)
        
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


def log_context(**kwargs) -> Dict[str, Any]:
    """
    Create a logging context with additional fields.
    
    Args:
        **kwargs: Context fields to add
        
    Returns:
        Context dictionary
    """
    return structlog.contextvars.bind_contextvars(**kwargs)


def log_structured_error(
    error_code: str, 
    message: str, 
    component: str,
    context: Optional[Dict[str, Any]] = None,
    logger_name: str = None,
    include_stack_trace: bool = True
) -> None:
    """
    Log structured error with error code and context.
    
    Args:
        error_code: Error code (e.g., 'RISK-001')
        message: Error message
        component: Component name
        context: Additional context data
        logger_name: Logger name (defaults to component)
        include_stack_trace: Whether to include stack trace (default: True)
    """
    import traceback
    import sys
    
    error_info = get_error_info(error_code)
    error_message = error_info.message if error_info else f'Unknown error code: {error_code}'
    
    log_data = {
        'error_code': error_code,
        'error_message': error_message,
        'component': component,
        'timestamp': datetime.utcnow().isoformat(),
        'error_details': message,
        'severity': error_info.severity.value if error_info else 'unknown'
    }
    
    # Add stack trace if requested and available
    if include_stack_trace:
        try:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            if exc_traceback is not None:
                log_data['stack_trace'] = traceback.format_exc()
                log_data['exception_type'] = exc_type.__name__ if exc_type else None
                log_data['exception_message'] = str(exc_value) if exc_value else None
        except Exception:
            # If we can't get stack trace, continue without it
            pass
    
    if context:
        log_data['context'] = context
    
    # Get logger
    logger = logging.getLogger(logger_name or component)
    
    # Log based on severity
    if error_info and error_info.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
        logger.error(f"{error_code}: {error_message} - {message}", extra=log_data)
    elif error_info and error_info.severity == ErrorSeverity.MEDIUM:
        logger.warning(f"{error_code}: {error_message} - {message}", extra=log_data)
    else:
        logger.info(f"{error_code}: {error_message} - {message}", extra=log_data)


def log_exception_with_stack_trace(
    error_code: str,
    component: str,
    context: Optional[Dict[str, Any]] = None,
    logger_name: str = None
) -> None:
    """
    Log exception with full stack trace and context.
    
    Args:
        error_code: Error code (e.g., 'RISK-001')
        component: Component name
        context: Additional context data
        logger_name: Logger name (defaults to component)
    """
    import traceback
    import sys
    
    error_info = get_error_info(error_code)
    error_message = error_info.message if error_info else f'Unknown error code: {error_code}'
    
    # Get exception information
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    if exc_traceback is None:
        # No exception context, log as regular error
        log_structured_error(
            error_code=error_code,
            message=error_message,
            component=component,
            context=context,
            logger_name=logger_name,
            include_stack_trace=False
        )
        return
    
    log_data = {
        'error_code': error_code,
        'error_message': error_message,
        'component': component,
        'timestamp': datetime.utcnow().isoformat(),
        'severity': error_info.severity.value if error_info else 'unknown',
        'exception_type': exc_type.__name__,
        'exception_message': str(exc_value),
        'stack_trace': traceback.format_exc(),
        'traceback_lines': traceback.format_tb(exc_traceback)
    }
    
    if context:
        log_data['context'] = context
    
    # Get logger
    logger = logging.getLogger(logger_name or component)
    
    # Log based on severity
    if error_info and error_info.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
        logger.error(f"{error_code}: {error_message} - {exc_type.__name__}: {str(exc_value)}", extra=log_data)
    elif error_info and error_info.severity == ErrorSeverity.MEDIUM:
        logger.warning(f"{error_code}: {error_message} - {exc_type.__name__}: {str(exc_value)}", extra=log_data)
    else:
        logger.info(f"{error_code}: {error_message} - {exc_type.__name__}: {str(exc_value)}", extra=log_data)


def log_component_health(
    component: str,
    status: str,
    error_code: Optional[str] = None,
    metrics: Optional[Dict[str, Any]] = None,
    logger_name: str = None
) -> None:
    """
    Log component health status.
    
    Args:
        component: Component name
        status: Health status
        error_code: Error code if unhealthy
        metrics: Component metrics
        logger_name: Logger name (defaults to component)
    """
    log_data = {
        'component': component,
        'status': status,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if error_code:
        error_info = get_error_info(error_code)
        log_data.update({
            'error_code': error_code,
            'error_message': error_info.message if error_info else f'Unknown error code: {error_code}',
            'severity': error_info.severity.value if error_info else 'unknown'
        })
    
    if metrics:
        log_data['metrics'] = metrics
    
    logger = logging.getLogger(logger_name or component)
    
    if status == 'healthy':
        logger.info(f"Component {component} is healthy", extra=log_data)
    elif status in ['unhealthy', 'not_ready']:
        logger.warning(f"Component {component} is {status}", extra=log_data)
    else:
        logger.error(f"Component {component} status unknown: {status}", extra=log_data)



