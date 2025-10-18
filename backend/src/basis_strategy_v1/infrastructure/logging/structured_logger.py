"""
Structured Logger

Provides structured logging for all system components with:
- Correlation ID and PID tracking
- Engine timestamp vs real UTC time
- Error codes and stack traces for ERROR/CRITICAL
- Component-specific log files in logs/{correlation_id}/{pid}/

Reference: docs/LOGGING_GUIDE.md - Structured Logging Patterns
Reference: docs/ERROR_HANDLING_PATTERNS.md - Error Code Standards
"""

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredLogger:
    """
    Structured logger for system components.
    
    Features:
    - Correlation ID tracking for request tracing
    - PID tracking for process identification
    - Engine timestamp (from EventDrivenStrategyEngine) vs real UTC time
    - Full stack traces for ERROR and CRITICAL levels
    - Error code support
    - Component-specific log files
    """
    
    def __init__(
        self,
        component_name: str,
        correlation_id: str,
        pid: int,
        log_dir: Path,
        engine=None
    ):
        """
        Initialize structured logger.
        
        Args:
            component_name: Name of the component using this logger
            correlation_id: Unique correlation ID for this run
            pid: Process ID
            log_dir: Log directory path (logs/{correlation_id}/{pid}/)
            engine: EventDrivenStrategyEngine instance (for timestamp access)
        """
        self.component_name = component_name
        self.correlation_id = correlation_id
        self.pid = pid
        self.log_dir = Path(log_dir)
        self.engine = engine
        
        # Create component log file
        self.log_file = self.log_dir / f"{component_name}.log"
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up Python logger for file output
        self._setup_file_logger()
    
    def _setup_file_logger(self):
        """Set up Python logger for component log file."""
        self.file_logger = logging.getLogger(f"{self.component_name}_{self.correlation_id}_{self.pid}")
        self.file_logger.setLevel(logging.DEBUG)
        self.file_logger.propagate = False
        
        # Avoid duplicate handlers
        if not self.file_logger.handlers:
            handler = logging.FileHandler(self.log_file)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.file_logger.addHandler(handler)
    
    def _get_timestamp_info(self) -> tuple:
        """
        Get both engine timestamp and real UTC time.
        
        Returns:
            Tuple of (engine_timestamp, real_utc_time)
            - engine_timestamp: Engine's current_timestamp (or real UTC if not available)
            - real_utc_time: Actual current UTC time
        """
        real_utc = datetime.now(timezone.utc).isoformat()
        engine_ts = None
        
        # Try to get engine timestamp
        if self.engine and hasattr(self.engine, 'current_timestamp'):
            try:
                engine_ts = self.engine.current_timestamp.isoformat()
            except:
                pass  # Use real UTC if engine timestamp fails
        
        # Use engine timestamp if available, otherwise use real UTC
        timestamp = engine_ts if engine_ts else real_utc
        
        return timestamp, real_utc
    
    def _create_log_dict(
        self,
        level: str,
        message: str,
        error_code: Optional[str] = None,
        exc_info: Optional[Exception] = None,
        **extra
    ) -> Dict[str, Any]:
        """
        Create structured log dictionary.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            error_code: Optional error code (from ERROR_REGISTRY)
            exc_info: Optional exception for stack trace capture
            **extra: Additional key-value pairs to include
            
        Returns:
            Structured log dictionary
        """
        timestamp, real_utc = self._get_timestamp_info()
        
        log_dict = {
            'timestamp': timestamp,
            'real_utc_time': real_utc,
            'level': level,
            'component': self.component_name,
            'message': message,
            'correlation_id': self.correlation_id,
            'pid': self.pid,
        }
        
        # Add error code if provided
        if error_code:
            log_dict['error_code'] = error_code
        
        # Add full stack trace for ERROR and CRITICAL levels
        if exc_info and level in ['ERROR', 'CRITICAL']:
            log_dict['stack_trace'] = traceback.format_exc()
            log_dict['exception_type'] = type(exc_info).__name__
            log_dict['exception_message'] = str(exc_info)
        
        # Add any extra fields
        if extra:
            log_dict.update(extra)
        
        return log_dict
    
    def _write_log(self, log_dict: Dict[str, Any]):
        """
        Write log to file.
        
        Args:
            log_dict: Structured log dictionary
        """
        level = log_dict['level']
        message = log_dict['message']
        
        # Format message with metadata for file output
        log_line = f"[{log_dict['correlation_id']}:{log_dict['pid']}] {message}"
        
        # Add error code if present
        if 'error_code' in log_dict:
            log_line = f"[{log_dict['error_code']}] {log_line}"
        
        # Write to file using appropriate level
        if level == 'DEBUG':
            self.file_logger.debug(log_line)
        elif level == 'INFO':
            self.file_logger.info(log_line)
        elif level == 'WARNING':
            self.file_logger.warning(log_line)
        elif level == 'ERROR':
            self.file_logger.error(log_line)
            # Write stack trace on separate lines for ERROR
            if 'stack_trace' in log_dict:
                for line in log_dict['stack_trace'].split('\n'):
                    if line.strip():
                        self.file_logger.error(f"  {line}")
        elif level == 'CRITICAL':
            self.file_logger.critical(log_line)
            # Write stack trace on separate lines for CRITICAL
            if 'stack_trace' in log_dict:
                for line in log_dict['stack_trace'].split('\n'):
                    if line.strip():
                        self.file_logger.critical(f"  {line}")
    
    def debug(self, message: str, **extra):
        """
        Log debug message.
        
        Args:
            message: Log message
            **extra: Additional context (metadata, etc.)
        """
        log_dict = self._create_log_dict('DEBUG', message, **extra)
        self._write_log(log_dict)
    
    def info(self, message: str, **extra):
        """
        Log info message.
        
        Args:
            message: Log message
            **extra: Additional context (metadata, etc.)
        """
        log_dict = self._create_log_dict('INFO', message, **extra)
        self._write_log(log_dict)
    
    def warning(self, message: str, error_code: Optional[str] = None, **extra):
        """
        Log warning message.
        
        Args:
            message: Log message
            error_code: Optional error code
            **extra: Additional context (metadata, etc.)
        """
        log_dict = self._create_log_dict('WARNING', message, error_code=error_code, **extra)
        self._write_log(log_dict)
    
    def error(
        self,
        message: str,
        error_code: Optional[str] = None,
        exc_info: Optional[Exception] = None,
        **extra
    ):
        """
        Log error message with full stack trace.
        
        Args:
            message: Log message
            error_code: Error code from ERROR_REGISTRY
            exc_info: Exception to capture stack trace
            **extra: Additional context (severity, operation, details, etc.)
        
        Example:
            logger.error(
                "Exposure calculation failed",
                error_code="EXP-001",
                exc_info=e,
                asset="BTC",
                severity="HIGH"
            )
        """
        log_dict = self._create_log_dict(
            'ERROR',
            message,
            error_code=error_code,
            exc_info=exc_info,
            **extra
        )
        self._write_log(log_dict)
    
    def critical(
        self,
        message: str,
        error_code: Optional[str] = None,
        exc_info: Optional[Exception] = None,
        **extra
    ):
        """
        Log critical message with full stack trace.
        
        Args:
            message: Log message
            error_code: Error code from ERROR_REGISTRY
            exc_info: Exception to capture stack trace
            **extra: Additional context (severity, operation, details, etc.)
        
        Example:
            logger.critical(
                "System failure triggered",
                error_code="EXEC-004",
                exc_info=e,
                operation="reconciliation",
                severity="CRITICAL"
            )
        """
        log_dict = self._create_log_dict(
            'CRITICAL',
            message,
            error_code=error_code,
            exc_info=exc_info,
            **extra
        )
        self._write_log(log_dict)
    
    def log_structured_error(
        self,
        error_code: str,
        message: str,
        component: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None
    ):
        """
        Log structured error with full context.
        
        This is the recommended pattern for structured error logging.
        
        Args:
            error_code: Error code from ERROR_REGISTRY
            message: Error message
            component: Component where error occurred
            operation: Operation that failed
            details: Additional error details
            exc_info: Exception to capture stack trace
        
        Example:
            logger.log_structured_error(
                error_code="EXP-001",
                message="Exposure calculation failed for BTC",
                component="ExposureMonitor",
                operation="calculate_exposure",
                details={"asset": "BTC", "positions": {...}},
                exc_info=e
            )
        """
        self.error(
            message,
            error_code=error_code,
            exc_info=exc_info,
            component=component,
            operation=operation,
            details=details or {}
        )
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        **extra
    ):
        """
        Log performance metrics.
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            **extra: Additional metrics
        """
        self.info(
            f"Performance: {operation} completed in {duration_ms:.2f}ms",
            operation=operation,
            duration_ms=duration_ms,
            **extra
        )
    
    def flush(self):
        """Flush all log handlers."""
        for handler in self.file_logger.handlers:
            handler.flush()
    
    def log_business_event(
        self,
        event_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        **extra
    ):
        """
        Log business events with structured data.
        
        Args:
            event_type: Type of business event (e.g., 'component_initialization', 'order_execution')
            message: Human-readable message
            metadata: Additional structured data
            **extra: Additional fields to include in log
        """
        log_data = {
            'event_type': event_type,
            'message': message,
            'metadata': metadata or {},
            **extra
        }
        
        self.info(f"Business Event: {event_type} - {message}", **log_data)


