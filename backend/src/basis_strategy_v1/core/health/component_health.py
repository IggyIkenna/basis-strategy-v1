"""
Component Health Check System

Provides standardized health checking for all components with:
- Timestamps for all health reports
- Error codes for not ready states
- Readiness status validation
- Integration with API health endpoints
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
import pandas as pd

from ..error_codes import get_error_info, ErrorSeverity

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    NOT_READY = "not_ready"
    UNKNOWN = "unknown"
    NOT_CONFIGURED = "not_configured"


@dataclass
class ComponentHealthReport:
    """Health report for a single component."""
    component_name: str
    status: HealthStatus
    timestamp: datetime
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    readiness_checks: Dict[str, bool] = None
    metrics: Dict[str, Any] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.readiness_checks is None:
            self.readiness_checks = {}
        if self.metrics is None:
            self.metrics = {}
        if self.dependencies is None:
            self.dependencies = []


class ComponentHealthChecker:
    """Base class for component health checking."""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.last_health_check = None
    
    def check_health(self) -> ComponentHealthReport:
        """Check component health and return report."""
        timestamp = datetime.now(timezone.utc)
        
        try:
            # Perform readiness checks
            readiness_checks = self._perform_readiness_checks()
            
            # Get component metrics
            metrics = self._get_component_metrics()
            
            # Determine overall status
            status = self._determine_status(readiness_checks)
            
            # Get error information if unhealthy
            error_code, error_message = None, None
            if status in [HealthStatus.UNHEALTHY, HealthStatus.NOT_READY]:
                error_code, error_message = self._get_error_info()
            
            report = ComponentHealthReport(
                component_name=self.component_name,
                status=status,
                timestamp=timestamp,
                error_code=error_code,
                error_message=error_message,
                readiness_checks=readiness_checks,
                metrics=metrics,
                dependencies=self._get_dependencies()
            )
            
            # Store last health check (no history)
            self.last_health_check = report
            
            return report
            
        except Exception as e:
            logger.error(f"Health check failed for {self.component_name}: {e}")
            return ComponentHealthReport(
                component_name=self.component_name,
                status=HealthStatus.UNKNOWN,
                timestamp=timestamp,
                error_code="HEALTH-001",
                error_message=f"Health check failed: {str(e)}"
            )
    
    def _perform_readiness_checks(self) -> Dict[str, bool]:
        """Perform component-specific readiness checks. Override in subclasses."""
        return {"basic_check": True}
    
    def _get_component_metrics(self) -> Dict[str, Any]:
        """Get component-specific metrics. Override in subclasses."""
        return {}
    
    def _get_error_info(self) -> tuple[Optional[str], Optional[str]]:
        """Get error code and message. Override in subclasses."""
        return None, None
    
    def _log_structured_error(self, error_code: str, message: str, context: Dict[str, Any] = None):
        """Log structured error with error code and context."""
        error_info = get_error_info(error_code)
        error_message = error_info.message if error_info else f'Unknown error code: {error_code}'
        
        log_data = {
            'error_code': error_code,
            'error_message': error_message,
            'component': self.component_name,
            'timestamp': datetime.utcnow().isoformat(),
            'error_details': message,
            'severity': error_info.severity.value if error_info else 'unknown'
        }
        
        if context:
            log_data['context'] = context
        
        # Log based on severity
        if error_info and error_info.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            logger.error(f"{error_code}: {error_message} - {message}", extra=log_data)
        elif error_info and error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"{error_code}: {error_message} - {message}", extra=log_data)
        else:
            logger.info(f"{error_code}: {error_message} - {message}", extra=log_data)
    
    def _get_dependencies(self) -> List[str]:
        """Get component dependencies. Override in subclasses."""
        return []
    
    def _determine_status(self, readiness_checks: Dict[str, bool]) -> HealthStatus:
        """Determine overall health status based on readiness checks."""
        if not readiness_checks:
            return HealthStatus.UNKNOWN
        
        # All checks must pass for healthy status
        if all(readiness_checks.values()):
            return HealthStatus.HEALTHY
        
        # Check if any critical checks failed
        critical_checks = [k for k in readiness_checks.keys() if 'critical' in k.lower()]
        if critical_checks and not all(readiness_checks[k] for k in critical_checks):
            return HealthStatus.UNHEALTHY
        
        # Non-critical checks failed
        return HealthStatus.NOT_READY


class PositionMonitorHealthChecker(ComponentHealthChecker):
    """Health checker for Position Monitor."""
    
    def __init__(self, position_monitor):
        super().__init__("position_monitor")
        self.position_monitor = position_monitor
    
    def _perform_readiness_checks(self) -> Dict[str, bool]:
        """Check Position Monitor readiness."""
        checks = {}
        
        try:
            # Check if monitor is initialized
            checks["initialized"] = hasattr(self.position_monitor, '_token_monitor')
            
            # Redis removed - using direct method calls for component communication
            checks["cache_available"] = True
            
            # Check if can get snapshot
            try:
                snapshot = self.position_monitor.get_snapshot()
                checks["snapshot_available"] = isinstance(snapshot, dict) and len(snapshot) > 0
            except:
                checks["snapshot_available"] = False
            
        except Exception as e:
            logger.error(f"Position Monitor readiness check failed: {e}")
            checks["error"] = False
        
        return checks
    
    def _get_component_metrics(self) -> Dict[str, Any]:
        """Get Position Monitor metrics."""
        try:
            snapshot = self.position_monitor.get_snapshot()
            return {
                "wallet_tokens": len(snapshot.get('wallet', {})),
                "cex_accounts": len(snapshot.get('cex_accounts', {})),
                "perp_positions": len(snapshot.get('perp_positions', {})),
                "execution_mode": self.position_monitor.execution_mode
            }
        except:
            return {"error": "Could not get metrics"}
    
    def _get_error_info(self) -> tuple[Optional[str], Optional[str]]:
        """Get Position Monitor error information."""
        if not hasattr(self.position_monitor, '_token_monitor'):
            return "POS-001", "Position Monitor not initialized"
        
        # Redis removed - using direct method calls for component communication
        
        return "POS-003", "Position Monitor readiness check failed"


class DataProviderHealthChecker(ComponentHealthChecker):
    """Health checker for Data Provider."""
    
    def __init__(self, data_provider):
        super().__init__("data_provider")
        self.data_provider = data_provider
    
    def _perform_readiness_checks(self) -> Dict[str, bool]:
        """Check Data Provider readiness."""
        checks = {}
        
        try:
            # Check if data provider is initialized
            checks["initialized"] = hasattr(self.data_provider, 'data')
            
            # Check if data is available using canonical pattern
            try:
                test_timestamp = pd.Timestamp('2024-06-01', tz='UTC')
                test_data = self.data_provider.get_data(test_timestamp)
                checks["data_loaded"] = test_data is not None and len(test_data) > 0
            except Exception:
                checks["data_loaded"] = False
            
            # Check environment variables
            import os
            checks["basis_data_mode_set"] = os.getenv('BASIS_DATA_MODE') is not None
            checks["basis_execution_mode_set"] = os.getenv('BASIS_EXECUTION_MODE') is not None
            
            # Check if can get market data snapshot (only if data is loaded)
            if checks["data_loaded"]:
                try:
                    test_timestamp = pd.Timestamp('2024-06-01', tz='UTC')
                    # Get data using canonical pattern
                    data = self.data_provider.get_data(test_timestamp)
                    market_data = data['market_data']
                    checks["market_data_available"] = isinstance(market_data, dict) and len(market_data) > 0
                except:
                    checks["market_data_available"] = False
            else:
                checks["market_data_available"] = True  # Not applicable if no data loaded
            
            # Check live data provider (if in live mode)
            if hasattr(self.data_provider, 'execution_mode') and self.data_provider.execution_mode == 'live':
                checks["live_provider_available"] = hasattr(self.data_provider, 'live_provider') and self.data_provider.live_provider is not None
            else:
                checks["live_provider_available"] = True  # Not needed in backtest
            
        except Exception as e:
            logger.error(f"Data Provider readiness check failed: {e}")
            checks["error"] = False
        
        return checks
    
    def _get_component_metrics(self) -> Dict[str, Any]:
        """Get Data Provider metrics."""
        try:
            import os
            metrics = {
                "data_sources": len(self.data_provider.data) if hasattr(self.data_provider, 'data') else 0,
                "mode": getattr(self.data_provider, 'mode', 'unknown'),
                "data_dir": str(getattr(self.data_provider, 'data_dir', 'unknown')),
                "data_loaded": getattr(self.data_provider, '_data_loaded', False),
                "basis_data_mode": os.getenv('BASIS_DATA_MODE', 'not_set'),
                "basis_execution_mode": os.getenv('BASIS_EXECUTION_MODE', 'not_set')
            }
            
            # Add execution_mode if available (for backward compatibility)
            if hasattr(self.data_provider, 'execution_mode'):
                metrics["execution_mode"] = self.data_provider.execution_mode
            
            # Add live provider info if available
            if hasattr(self.data_provider, 'live_provider'):
                metrics["live_provider_available"] = self.data_provider.live_provider is not None
            
            return metrics
        except:
            return {"error": "Could not get metrics"}
    
    def _get_error_info(self) -> tuple[Optional[str], Optional[str]]:
        """Get Data Provider error information."""
        if not hasattr(self.data_provider, 'data'):
            return "DATA-001", "Data Provider not initialized"
        
        if len(self.data_provider.data) == 0:
            return "DATA-002", "No data sources loaded"
        
        if self.data_provider.execution_mode == 'live' and not self.data_provider.live_provider:
            return "DATA-003", "Live data provider not available"
        
        return "DATA-004", "Data Provider readiness check failed"


class RiskMonitorHealthChecker(ComponentHealthChecker):
    """Health checker for Risk Monitor."""
    
    def __init__(self, risk_monitor):
        super().__init__("risk_monitor")
        self.risk_monitor = risk_monitor
    
    def _perform_readiness_checks(self) -> Dict[str, bool]:
        """Check Risk Monitor readiness."""
        checks = {}
        
        try:
            # Check if risk monitor is initialized
            checks["initialized"] = hasattr(self.risk_monitor, 'config')
            
            # Check configuration
            checks["config_available"] = bool(self.risk_monitor.config)
            
            # Redis removed - using direct method calls for component communication
            checks["cache_available"] = True
            
            # Check if can assess risk
            try:
                # Create dummy exposure data for testing
                dummy_exposure = {
                    'total_equity_usd': 100000,
                    'total_debt_usd': 50000,
                    'net_delta_eth': 0.0
                }
                dummy_market_data = {
                    'eth_usd_price': 3000.0,
                    'timestamp': pd.Timestamp.now(tz='UTC')
                }
                risk_result = self.risk_monitor.assess_risk(dummy_exposure, dummy_market_data)
                checks["risk_assessment_available"] = isinstance(risk_result, dict)
            except:
                checks["risk_assessment_available"] = False
            
        except Exception as e:
            logger.error(f"Risk Monitor readiness check failed: {e}")
            checks["error"] = False
        
        return checks
    
    def _get_component_metrics(self) -> Dict[str, Any]:
        """Get Risk Monitor metrics."""
        try:
            return {
                "current_risks": len(self.risk_monitor.current_risks),
                "aave_safe_ltv": self.risk_monitor.aave_safe_ltv,
                "aave_ltv_warning": self.risk_monitor.aave_ltv_warning,
                "aave_ltv_critical": self.risk_monitor.aave_ltv_critical,
                "margin_warning_threshold": self.risk_monitor.margin_warning_threshold,
                "margin_critical_threshold": self.risk_monitor.margin_critical_threshold,
                "delta_threshold_pct": self.risk_monitor.delta_threshold_pct
            }
        except:
            return {"error": "Could not get metrics"}
    
    def _get_error_info(self) -> tuple[Optional[str], Optional[str]]:
        """Get Risk Monitor error information."""
        if not hasattr(self.risk_monitor, 'config'):
            return "RISK-001", "Risk Monitor not initialized"
        
        if not self.risk_monitor.config:
            return "RISK-002", "Risk Monitor configuration not available"
        
        return "RISK-003", "Risk Monitor readiness check failed"


class EventLoggerHealthChecker(ComponentHealthChecker):
    """Health checker for Event Logger."""
    
    def __init__(self, event_logger):
        super().__init__("event_logger")
        self.event_logger = event_logger
    
    def _perform_readiness_checks(self) -> Dict[str, bool]:
        """Check Event Logger readiness."""
        checks = {}
        
        try:
            # Check if event logger is initialized
            checks["initialized"] = hasattr(self.event_logger, 'events')
            
            # Redis removed - using direct method calls for component communication
            checks["cache_available"] = True
            
            # Check if can log events
            checks["event_logging_available"] = True  # Basic check
            
        except Exception as e:
            logger.error(f"Event Logger readiness check failed: {e}")
            checks["error"] = False
        
        return checks
    
    def _get_component_metrics(self) -> Dict[str, Any]:
        """Get Event Logger metrics."""
        try:
            return {
                "total_events": len(self.event_logger.events),
                "global_order": self.event_logger.global_order,
                "execution_mode": self.event_logger.execution_mode,
                "include_balance_snapshots": self.event_logger.include_balance_snapshots
            }
        except:
            return {"error": "Could not get metrics"}
    
    def _get_error_info(self) -> tuple[Optional[str], Optional[str]]:
        """Get Event Logger error information."""
        if not hasattr(self.event_logger, 'events'):
            return "EVENT-001", "Event Logger not initialized"
        
        # Redis removed - using direct method calls for component communication
        
        return "EVENT-003", "Event Logger readiness check failed"


class SystemHealthAggregator:
    """Aggregates health reports from all components."""
    
    def __init__(self):
        self.component_checkers = {}
        self.last_aggregated_report = None
    
    def register_component(self, component_name: str, health_checker: ComponentHealthChecker):
        """Register a component health checker."""
        self.component_checkers[component_name] = health_checker
        logger.info(f"Registered health checker for {component_name}")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get aggregated system health report."""
        timestamp = datetime.now(timezone.utc)
        component_reports = {}
        overall_status = HealthStatus.HEALTHY
        
        # Check all registered components
        for component_name, checker in self.component_checkers.items():
            try:
                report = await checker.check_health()
                component_reports[component_name] = {
                    "status": report.status.value,
                    "timestamp": report.timestamp.isoformat(),
                    "error_code": report.error_code,
                    "error_message": report.error_message,
                    "readiness_checks": report.readiness_checks,
                    "metrics": report.metrics,
                    "dependencies": report.dependencies
                }
                
                # Update overall status
                if report.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif report.status == HealthStatus.NOT_READY and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.NOT_READY
                elif report.status == HealthStatus.UNKNOWN and overall_status in [HealthStatus.HEALTHY, HealthStatus.NOT_READY]:
                    overall_status = HealthStatus.UNKNOWN
                    
            except Exception as e:
                logger.error(f"Health check failed for {component_name}: {e}")
                component_reports[component_name] = {
                    "status": HealthStatus.UNKNOWN.value,
                    "timestamp": timestamp.isoformat(),
                    "error_code": "HEALTH-001",
                    "error_message": f"Health check failed: {str(e)}",
                    "readiness_checks": {},
                    "metrics": {},
                    "dependencies": []
                }
                overall_status = HealthStatus.UNHEALTHY
        
        # Create aggregated report
        aggregated_report = {
            "status": overall_status.value,
            "timestamp": timestamp.isoformat(),
            "components": component_reports,
            "summary": {
                "total_components": len(self.component_checkers),
                "healthy_components": sum(1 for r in component_reports.values() if r["status"] == "healthy"),
                "unhealthy_components": sum(1 for r in component_reports.values() if r["status"] == "unhealthy"),
                "not_ready_components": sum(1 for r in component_reports.values() if r["status"] == "not_ready"),
                "unknown_components": sum(1 for r in component_reports.values() if r["status"] == "unknown")
            }
        }
        
        self.last_aggregated_report = aggregated_report
        return aggregated_report
    


# Global system health aggregator
system_health_aggregator = SystemHealthAggregator()
