"""
Unified Health Manager

Centralized health monitoring and management system for all components.
Provides health checks, status monitoring, and error handling integration.

Reference: docs/specs/HEALTH_ERROR_SYSTEMS.md
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Health System Architecture
"""

from typing import Dict, List, Optional, Callable, Any
import pandas as pd
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import threading
import time

from ..errors.error_codes import ComponentError


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Component health information."""
    component_name: str
    status: HealthStatus
    last_check: datetime
    message: str
    details: Dict[str, Any]
    error_count: int = 0
    last_error: Optional[str] = None


class UnifiedHealthManager:
    """Unified health management system for all components."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict, execution_mode: str):
        """
        Initialize unified health manager.
        
        Args:
            config: Configuration dictionary (reference, never modified)
            execution_mode: 'backtest' or 'live' (from BASIS_EXECUTION_MODE)
        """
        # Store references (NEVER modified)
        self.config = config
        self.execution_mode = execution_mode
        
        # Component registry
        self._components: Dict[str, Callable] = {}
        self._component_health: Dict[str, ComponentHealth] = {}
        
        # Health monitoring settings
        self.health_check_interval = 30  # seconds
        self.health_check_timeout = 10  # seconds
        self.max_consecutive_failures = 3
        
        # Monitoring state
        self._monitoring_active = False
        self._monitoring_thread = None
        self._lock = threading.Lock()
        
        # System health state
        self.system_health_status = HealthStatus.UNKNOWN
        self.last_system_check = None
        self.system_error_count = 0
        
        logger.info(f"UnifiedHealthManager initialized in {execution_mode} mode")
    
    def register_component(self, component_name: str, health_checker: Callable[[], Dict[str, Any]]):
        """
        Register a component with the health manager.
        
        Args:
            component_name: Name of the component
            health_checker: Function that returns health status dictionary
        """
        with self._lock:
            self._components[component_name] = health_checker
            
            # Initialize component health
            self._component_health[component_name] = ComponentHealth(
                component_name=component_name,
                status=HealthStatus.UNKNOWN,
                last_check=datetime.now(),
                message="Component registered",
                details={}
            )
            
            logger.info(f"Registered component: {component_name}")
    
    def unregister_component(self, component_name: str):
        """Unregister a component from health monitoring."""
        with self._lock:
            if component_name in self._components:
                del self._components[component_name]
                del self._component_health[component_name]
                logger.info(f"Unregistered component: {component_name}")
    
    def get_component_health(self, component_name: str) -> Optional[ComponentHealth]:
        """Get health status for a specific component."""
        with self._lock:
            return self._component_health.get(component_name)
    
    def get_all_component_health(self) -> Dict[str, ComponentHealth]:
        """Get health status for all components."""
        with self._lock:
            return self._component_health.copy()
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        with self._lock:
            # Calculate system health based on component health
            component_statuses = [health.status for health in self._component_health.values()]
            
            if not component_statuses:
                self.system_health_status = HealthStatus.UNKNOWN
            elif all(status == HealthStatus.HEALTHY for status in component_statuses):
                self.system_health_status = HealthStatus.HEALTHY
            elif any(status == HealthStatus.UNHEALTHY for status in component_statuses):
                self.system_health_status = HealthStatus.UNHEALTHY
            else:
                self.system_health_status = HealthStatus.DEGRADED
            
            self.last_system_check = datetime.now()
            
            return {
                'system_status': self.system_health_status.value,
                'last_check': self.last_system_check.isoformat(),
                'component_count': len(self._component_health),
                'healthy_components': sum(1 for h in self._component_health.values() if h.status == HealthStatus.HEALTHY),
                'degraded_components': sum(1 for h in self._component_health.values() if h.status == HealthStatus.DEGRADED),
                'unhealthy_components': sum(1 for h in self._component_health.values() if h.status == HealthStatus.UNHEALTHY),
                'components': {
                    name: {
                        'status': health.status.value,
                        'last_check': health.last_check.isoformat(),
                        'message': health.message,
                        'error_count': health.error_count,
                        'last_error': health.last_error
                    }
                    for name, health in self._component_health.items()
                }
            }
    
    def check_component_health(self, component_name: str) -> ComponentHealth:
        """Check health for a specific component."""
        if component_name not in self._components:
            raise ComponentError(
                error_code='HEALTH-003',
                message=f'Component not registered: {component_name}',
                component='UnifiedHealthManager',
                severity='HIGH',
                details={'component_name': component_name}
            )
        
        try:
            # Get health checker function
            health_checker = self._components[component_name]
            
            # Perform health check with timeout
            start_time = time.time()
            health_data = health_checker()
            check_duration = time.time() - start_time
            
            # Parse health data
            status_str = health_data.get('status', 'unknown')
            message = health_data.get('message', 'Health check completed')
            details = health_data.get('details', {})
            
            # Convert status string to enum
            try:
                status = HealthStatus(status_str.lower())
            except ValueError:
                status = HealthStatus.UNKNOWN
                message = f"Invalid status: {status_str}"
            
            # Update component health
            with self._lock:
                component_health = self._component_health[component_name]
                component_health.status = status
                component_health.last_check = datetime.now()
                component_health.message = message
                component_health.details = details
                component_health.details['check_duration_ms'] = check_duration * 1000
                
                # Update error tracking
                if status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]:
                    component_health.error_count += 1
                    component_health.last_error = message
                else:
                    # Reset error count on successful check
                    component_health.error_count = 0
                    component_health.last_error = None
            
            logger.debug(f"Health check for {component_name}: {status.value} ({check_duration:.3f}s)")
            return component_health
            
        except Exception as e:
            # Handle health check failures
            with self._lock:
                component_health = self._component_health[component_name]
                component_health.status = HealthStatus.UNHEALTHY
                component_health.last_check = datetime.now()
                component_health.message = f"Health check failed: {str(e)}"
                component_health.error_count += 1
                component_health.last_error = str(e)
            
            logger.error(f"Health check failed for {component_name}: {e}")
            return component_health
    
    def check_all_components(self) -> Dict[str, ComponentHealth]:
        """Check health for all registered components."""
        results = {}
        
        for component_name in list(self._components.keys()):
            try:
                results[component_name] = self.check_component_health(component_name)
            except Exception as e:
                logger.error(f"Failed to check health for {component_name}: {e}")
                # Create unhealthy status for failed checks
                results[component_name] = ComponentHealth(
                    component_name=component_name,
                    status=HealthStatus.UNHEALTHY,
                    last_check=datetime.now(),
                    message=f"Health check failed: {str(e)}",
                    details={'error': str(e)},
                    error_count=1,
                    last_error=str(e)
                )
        
        return results
    
    def start_monitoring(self):
        """Start continuous health monitoring."""
        if self._monitoring_active:
            logger.warning("Health monitoring already active")
            return
        
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        logger.info("Health monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous health monitoring."""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("Health monitoring stopped")
    
    def _monitoring_loop(self):
        """Continuous health monitoring loop."""
        while self._monitoring_active:
            try:
                # Check all components
                self.check_all_components()
                
                # Update system health
                system_health = self.get_system_health()
                
                # Log system health status
                if system_health['system_status'] == 'unhealthy':
                    logger.warning(f"System health degraded: {system_health['unhealthy_components']} unhealthy components")
                elif system_health['system_status'] == 'degraded':
                    logger.info(f"System health degraded: {system_health['degraded_components']} degraded components")
                
                # Sleep until next check
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(self.health_check_interval)
    
    def report_error(self, component_name: str, error: ComponentError):
        """Report an error from a component."""
        with self._lock:
            if component_name in self._component_health:
                component_health = self._component_health[component_name]
                component_health.error_count += 1
                component_health.last_error = str(error)
                
                # Update status based on error severity
                if error.severity == "CRITICAL":
                    component_health.status = HealthStatus.UNHEALTHY
                elif error.severity == "HIGH":
                    component_health.status = HealthStatus.DEGRADED
                
                logger.warning(f"Error reported from {component_name}: {error.error_code} - {error.message}")
    
    def is_system_healthy(self) -> bool:
        """Check if the overall system is healthy."""
        system_health = self.get_system_health()
        return system_health['system_status'] == 'healthy'
    
    def get_unhealthy_components(self) -> List[str]:
        """Get list of unhealthy components."""
        with self._lock:
            return [
                name for name, health in self._component_health.items()
                if health.status == HealthStatus.UNHEALTHY
            ]
    
    def get_degraded_components(self) -> List[str]:
        """Get list of degraded components."""
        with self._lock:
            return [
                name for name, health in self._component_health.items()
                if health.status == HealthStatus.DEGRADED
            ]


# Global instance for dependency injection
unified_health_manager = None