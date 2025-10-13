"""
Error Code Registry

Centralized registry for all error codes across the system.
Provides structured error handling with component-specific error codes.

Reference: docs/specs/17_HEALTH_ERROR_SYSTEMS.md
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Health System Architecture
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class ErrorCodeInfo(StandardizedLoggingMixin):
    """Error code information structure."""
    code: str
    component: str
    severity: ErrorSeverity
    message: str
    description: str
    resolution: str
    category: str = "general"


class ErrorCodeRegistry(StandardizedLoggingMixin):
    """Centralized error code registry."""
    
    def __init__(self):
        """Initialize error code registry with all system error codes."""
        self._error_codes: Dict[str, ErrorCodeInfo] = {}
        self._initialize_error_codes()
    
    def _initialize_error_codes(self):
        """Initialize all error codes for the system."""
        
        # Position Monitor Error Codes (POS-001 to POS-099)
        self._register_error_codes([
            ErrorCodeInfo("POS-001", "PositionMonitor", ErrorSeverity.HIGH, 
                         "Position calculation failed", 
                         "Failed to calculate current positions from venue data",
                         "Check venue connections and data availability"),
            ErrorCodeInfo("POS-002", "PositionMonitor", ErrorSeverity.HIGH,
                         "Position validation failed",
                         "Position data failed validation checks",
                         "Verify position data integrity and venue responses"),
            ErrorCodeInfo("POS-003", "PositionMonitor", ErrorSeverity.CRITICAL,
                         "Position monitor initialization failed",
                         "Failed to initialize position monitoring system",
                         "Check configuration and venue credentials"),
        ])
        
        # Exposure Monitor Error Codes (EXP-001 to EXP-099)
        self._register_error_codes([
            ErrorCodeInfo("EXP-001", "ExposureMonitor", ErrorSeverity.HIGH,
                         "Exposure calculation failed",
                         "Failed to calculate exposure metrics",
                         "Check market data and position data availability"),
            ErrorCodeInfo("EXP-002", "ExposureMonitor", ErrorSeverity.MEDIUM,
                         "Exposure threshold exceeded",
                         "Exposure limits exceeded for one or more assets",
                         "Review exposure limits and rebalance if necessary"),
        ])
        
        # Risk Monitor Error Codes (RISK-001 to RISK-099)
        self._register_error_codes([
            ErrorCodeInfo("RISK-001", "RiskMonitor", ErrorSeverity.HIGH,
                         "Risk calculation failed",
                         "Failed to calculate risk metrics",
                         "Check market data and exposure data availability"),
            ErrorCodeInfo("RISK-002", "RiskMonitor", ErrorSeverity.CRITICAL,
                         "Risk limit exceeded",
                         "Risk limits exceeded - immediate action required",
                         "Reduce exposure or close positions immediately"),
        ])
        
        # PnL Calculator Error Codes (PNL-001 to PNL-099)
        self._register_error_codes([
            ErrorCodeInfo("PNL-001", "PnLCalculator", ErrorSeverity.HIGH,
                         "P&L calculation failed",
                         "Failed to calculate P&L metrics",
                         "Check exposure data and market data availability"),
            ErrorCodeInfo("PNL-002", "PnLCalculator", ErrorSeverity.MEDIUM,
                         "P&L reconciliation failed",
                         "P&L reconciliation between methods failed",
                         "Review calculation methods and data sources"),
        ])
        
        # Strategy Manager Error Codes (STRAT-001 to STRAT-099)
        self._register_error_codes([
            ErrorCodeInfo("STRAT-001", "StrategyManager", ErrorSeverity.HIGH,
                         "Strategy execution failed",
                         "Failed to execute strategy logic",
                         "Check strategy configuration and market conditions"),
            ErrorCodeInfo("STRAT-002", "StrategyManager", ErrorSeverity.MEDIUM,
                         "Strategy signal generation failed",
                         "Failed to generate trading signals",
                         "Review strategy parameters and market data"),
        ])
        
        # Venue Manager Error Codes (VM-001 to VM-099)
        self._register_error_codes([
            ErrorCodeInfo("VM-001", "VenueManager", ErrorSeverity.HIGH,
                         "Venue instruction failed",
                         "Failed to execute venue instructions",
                         "Check venue connections and instruction validity"),
            ErrorCodeInfo("VM-002", "VenueManager", ErrorSeverity.CRITICAL,
                         "Venue instruction timeout",
                         "Venue instruction timed out - status unknown",
                         "Check venue status and retry if safe"),
        ])
        
        # Venue Interface Manager Error Codes (VIM-001 to VIM-099)
        self._register_error_codes([
            ErrorCodeInfo("VIM-001", "VenueInterfaceManager", ErrorSeverity.HIGH,
                         "Venue routing failed",
                         "Failed to route instruction to appropriate venue",
                         "Check venue availability and routing configuration"),
            ErrorCodeInfo("VIM-002", "VenueInterfaceManager", ErrorSeverity.HIGH,
                         "Unsupported instruction type",
                         "Instruction type not supported by any venue",
                         "Check instruction type and venue capabilities"),
        ])
        
        # Event Logger Error Codes (EVENT-001 to EVENT-099)
        self._register_error_codes([
            ErrorCodeInfo("EVENT-001", "EventLogger", ErrorSeverity.MEDIUM,
                         "Event logging failed",
                         "Failed to log event to storage",
                         "Check log storage availability and permissions"),
            ErrorCodeInfo("EVENT-002", "EventLogger", ErrorSeverity.LOW,
                         "Event validation failed",
                         "Event data failed validation",
                         "Review event data format and requirements"),
        ])
        
        # Data Provider Error Codes (DATA-001 to DATA-099)
        self._register_error_codes([
            ErrorCodeInfo("DATA-001", "DataProvider", ErrorSeverity.HIGH,
                         "Data loading failed",
                         "Failed to load required data",
                         "Check data sources and network connectivity"),
            ErrorCodeInfo("DATA-002", "DataProvider", ErrorSeverity.MEDIUM,
                         "Data validation failed",
                         "Loaded data failed validation checks",
                         "Review data quality and validation rules"),
        ])
        
        # Reconciliation Component Error Codes (REC-001 to REC-099)
        self._register_error_codes([
            ErrorCodeInfo("REC-001", "ReconciliationComponent", ErrorSeverity.HIGH,
                         "Reconciliation failed",
                         "Failed to reconcile simulated vs real positions",
                         "Check position data and reconciliation logic"),
            ErrorCodeInfo("REC-002", "ReconciliationComponent", ErrorSeverity.HIGH,
                         "Position mismatch detected",
                         "Simulated and real positions don't match",
                         "Review execution results and position updates"),
            ErrorCodeInfo("REC-003", "ReconciliationComponent", ErrorSeverity.CRITICAL,
                         "Retry attempts exhausted",
                         "All retry attempts for reconciliation failed",
                         "Immediate action required - check system health"),
            ErrorCodeInfo("REC-004", "ReconciliationComponent", ErrorSeverity.HIGH,
                         "Unknown asset in reconciliation",
                         "Asset being reconciled is not in tracked assets",
                         "Add asset to track_assets config or fix asset name"),
        ])
        
        # Live Trading Service Error Codes (LTS-001 to LTS-099)
        self._register_error_codes([
            ErrorCodeInfo("LTS-001", "LiveTradingService", ErrorSeverity.CRITICAL,
                         "Live trading initialization failed",
                         "Failed to initialize live trading service",
                         "Check venue credentials and network connectivity"),
            ErrorCodeInfo("LTS-002", "LiveTradingService", ErrorSeverity.HIGH,
                         "Real-time data connection failed",
                         "Failed to establish real-time data connections",
                         "Check data provider connectivity and credentials"),
            ErrorCodeInfo("LTS-003", "LiveTradingService", ErrorSeverity.HIGH,
                         "Live execution failed",
                         "Failed to execute live trade",
                         "Check venue status and trade parameters"),
        ])
        
        # Health System Error Codes (HEALTH-001 to HEALTH-099)
        self._register_error_codes([
            ErrorCodeInfo("HEALTH-001", "HealthSystem", ErrorSeverity.CRITICAL,
                         "System health check failed",
                         "Critical system health check failed",
                         "Immediate system restart required"),
            ErrorCodeInfo("HEALTH-002", "HealthSystem", ErrorSeverity.HIGH,
                         "Component health degraded",
                         "Component health status degraded",
                         "Monitor component and restart if necessary"),
        ])
        
        # Configuration Error Codes (CONFIG-001 to CONFIG-099)
        self._register_error_codes([
            ErrorCodeInfo("CONFIG-001", "Configuration", ErrorSeverity.CRITICAL,
                         "Configuration validation failed",
                         "Configuration failed validation checks",
                         "Review and fix configuration parameters"),
            ErrorCodeInfo("CONFIG-002", "Configuration", ErrorSeverity.HIGH,
                         "Missing required configuration",
                         "Required configuration parameter missing",
                         "Add missing configuration parameter"),
        ])
        
        logger.info(f"Initialized error code registry with {len(self._error_codes)} error codes")
    
    def _register_error_codes(self, error_codes: List[ErrorCodeInfo]):
        """Register a list of error codes."""
        for error_code in error_codes:
            self._error_codes[error_code.code] = error_code
    
    def get_error_info(self, error_code: str) -> Optional[ErrorCodeInfo]:
        """Get error code information."""
        return self._error_codes.get(error_code)
    
    def get_errors_by_component(self, component: str) -> List[ErrorCodeInfo]:
        """Get all error codes for a specific component."""
        return [error for error in self._error_codes.values() if error.component == component]
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorCodeInfo]:
        """Get all error codes for a specific severity level."""
        return [error for error in self._error_codes.values() if error.severity == severity]
    
    def get_all_error_codes(self) -> Dict[str, ErrorCodeInfo]:
        """Get all registered error codes."""
        return self._error_codes.copy()
    
    def register_custom_error(self, error_code: ErrorCodeInfo):
        """Register a custom error code."""
        self._error_codes[error_code.code] = error_code
        logger.info(f"Registered custom error code: {error_code.code}")


# Global error code registry instance
_error_registry = ErrorCodeRegistry()


def get_error_info(error_code: str) -> Optional[ErrorCodeInfo]:
    """Get error code information from global registry."""
    return _error_registry.get_error_info(error_code)


def get_errors_by_component(component: str) -> List[ErrorCodeInfo]:
    """Get all error codes for a specific component."""
    return _error_registry.get_errors_by_component(component)


def get_errors_by_severity(severity: ErrorSeverity) -> List[ErrorCodeInfo]:
    """Get all error codes for a specific severity level."""
    return _error_registry.get_errors_by_severity(severity)


def register_custom_error(error_code: ErrorCodeInfo):
    """Register a custom error code."""
    _error_registry.register_custom_error(error_code)


def validate_error_code(error_code: str) -> bool:
    """Validate that an error code exists in the registry."""
    return error_code in _error_registry.get_all_error_codes()


# Export the registry instance for backward compatibility
error_code_registry = _error_registry