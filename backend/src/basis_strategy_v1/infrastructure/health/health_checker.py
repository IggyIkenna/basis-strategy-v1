"""
Unified Health Checker

Provides comprehensive health checking for all system components and dependencies.
Implements both basic and detailed health checks with component-specific status.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 10 (Health System Architecture)
Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-008 (Health System Unification)
"""

import os
import time
import psutil
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health status for a component or dependency."""
    name: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    message: str
    details: Dict[str, Any]
    last_check: datetime
    response_time_ms: Optional[float] = None


class ComponentHealthCheck:
    """Base class for component health checks."""
    
    def __init__(self, name: str):
        self.name = name
        self.last_check = None
        self.last_status = None
    
    def check_health(self) -> HealthStatus:
        """Check component health and return status."""
        start_time = time.time()
        
        try:
            status, message, details = self._perform_health_check()
            response_time = (time.time() - start_time) * 1000
            
            health_status = HealthStatus(
                name=self.name,
                status=status,
                message=message,
                details=details,
                last_check=datetime.now(),
                response_time_ms=response_time
            )
            
            self.last_check = health_status.last_check
            self.last_status = health_status
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return HealthStatus(
                name=self.name,
                status='unhealthy',
                message=f"Health check failed: {str(e)}",
                details={'error': str(e)},
                last_check=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def _perform_health_check(self) -> tuple[str, str, Dict[str, Any]]:
        """Override in subclasses to implement specific health checks."""
        return 'healthy', 'Component is healthy', {}


class SystemHealthCheck(ComponentHealthCheck):
    """System-level health check."""
    
    def _perform_health_check(self) -> tuple[str, str, Dict[str, Any]]:
        """Check system resources and basic functionality."""
        details = {}
        
        # Check memory usage
        memory = psutil.virtual_memory()
        details['memory'] = {
            'total_gb': round(memory.total / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'percent_used': memory.percent
        }
        
        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        details['cpu'] = {
            'percent_used': cpu_percent,
            'count': psutil.cpu_count()
        }
        
        # Check disk usage
        disk = psutil.disk_usage('/')
        details['disk'] = {
            'total_gb': round(disk.total / (1024**3), 2),
            'free_gb': round(disk.free / (1024**3), 2),
            'percent_used': round((disk.used / disk.total) * 100, 2)
        }
        
        # Determine overall status
        if memory.percent > 90 or cpu_percent > 90 or (disk.used / disk.total) > 0.9:
            return 'degraded', 'System resources are high', details
        elif memory.percent > 95 or cpu_percent > 95 or (disk.used / disk.total) > 0.95:
            return 'unhealthy', 'System resources are critically high', details
        else:
            return 'healthy', 'System is healthy', details


class DataProviderHealthCheck(ComponentHealthCheck):
    """Data provider health check."""
    
    def _perform_health_check(self) -> tuple[str, str, Dict[str, Any]]:
        """Check data provider connectivity and data freshness."""
        details = {}
        
        # Check if data directory exists and is accessible
        data_dir = os.getenv('BASIS_DATA_DIR', 'data')
        # Debug logging
        logger.debug(f"Data provider health check - BASIS_DATA_DIR: {os.getenv('BASIS_DATA_DIR')}, data_dir: {data_dir}")
        logger.debug(f"Current working directory: {os.getcwd()}")
        logger.debug(f"All BASIS_ env vars: {[k for k in os.environ.keys() if k.startswith('BASIS_')]}")
        # Resolve relative paths to absolute paths
        if not os.path.isabs(data_dir):
            data_dir = os.path.abspath(data_dir)
        logger.debug(f"Resolved data_dir: {data_dir}, exists: {os.path.exists(data_dir)}")
        
        if not os.path.exists(data_dir):
            return 'unhealthy', f'Data directory not found: {data_dir}', details
        
        if not os.access(data_dir, os.R_OK):
            return 'unhealthy', f'Data directory not readable: {data_dir}', details
        
        details['data_directory'] = data_dir
        details['data_mode'] = os.getenv('BASIS_DATA_MODE', 'unknown')
        
        # Check for recent data files (basic check)
        try:
            data_files = []
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    if file.endswith('.csv') or file.endswith('.json'):
                        file_path = os.path.join(root, file)
                        mtime = os.path.getmtime(file_path)
                        data_files.append({
                            'file': file,
                            'modified': datetime.fromtimestamp(mtime).isoformat(),
                            'age_hours': (time.time() - mtime) / 3600
                        })
            
            details['data_files'] = len(data_files)
            details['recent_files'] = len([f for f in data_files if f['age_hours'] < 24])
            
            # Check execution mode - backtest mode doesn't require recent data
            execution_mode = os.getenv('BASIS_EXECUTION_MODE', 'backtest')
            details['execution_mode'] = execution_mode
            
            if len(data_files) == 0:
                return 'unhealthy', 'No data files found', details
            elif execution_mode == 'backtest':
                # For backtest mode, any data files are acceptable
                return 'healthy', 'Data provider is healthy (backtest mode)', details
            elif len([f for f in data_files if f['age_hours'] < 24]) == 0:
                return 'degraded', 'No recent data files found', details
            else:
                return 'healthy', 'Data provider is healthy', details
                
        except Exception as e:
            return 'unhealthy', f'Error checking data files: {str(e)}', details


class ConfigHealthCheck(ComponentHealthCheck):
    """Configuration health check."""
    
    def _perform_health_check(self) -> tuple[str, str, Dict[str, Any]]:
        """Check configuration validity and completeness."""
        details = {}
        
        # Check required environment variables
        required_vars = [
            'BASIS_ENVIRONMENT', 'BASIS_DEPLOYMENT_MODE', 'BASIS_DATA_DIR',
            'BASIS_RESULTS_DIR', 'BASIS_DEBUG', 'BASIS_LOG_LEVEL',
            'BASIS_EXECUTION_MODE', 'BASIS_DATA_START_DATE', 'BASIS_DATA_END_DATE',
            'BASIS_API_PORT', 'BASIS_API_HOST', 'BASIS_DATA_MODE'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        details['required_variables'] = len(required_vars)
        details['missing_variables'] = len(missing_vars)
        details['missing_list'] = missing_vars
        
        if missing_vars:
            return 'unhealthy', f'Missing required environment variables: {missing_vars}', details
        
        # Check configuration files
        config_dir = 'configs'
        if not os.path.exists(config_dir):
            return 'unhealthy', f'Configuration directory not found: {config_dir}', details
        
        details['config_directory'] = config_dir
        details['environment'] = os.getenv('BASIS_ENVIRONMENT')
        details['execution_mode'] = os.getenv('BASIS_EXECUTION_MODE')
        
        return 'healthy', 'Configuration is valid', details


class HealthChecker:
    """Unified health checker for all system components."""
    
    def __init__(self):
        self.components: List[ComponentHealthCheck] = []
        self.dependencies: List[ComponentHealthCheck] = []
        self._register_default_components()
    
    def _register_default_components(self):
        """Register default system components."""
        self.components = [
            SystemHealthCheck('system'),
            DataProviderHealthCheck('data_provider'),
            ConfigHealthCheck('configuration')
        ]
    
    def register_component(self, component: ComponentHealthCheck):
        """Register a component for health checking."""
        self.components.append(component)
        logger.info(f"Registered health check component: {component.name}")
    
    def register_dependency(self, dependency: ComponentHealthCheck):
        """Register an external dependency for health checking."""
        self.dependencies.append(dependency)
        logger.info(f"Registered health check dependency: {dependency.name}")
    
    def check_health(self) -> Dict[str, Any]:
        """Perform basic health check."""
        logger.debug("Performing basic health check")
        
        start_time = time.time()
        component_statuses = []
        
        # Check all components
        for component in self.components:
            status = component.check_health()
            component_statuses.append({
                'name': status.name,
                'status': status.status,
                'message': status.message,
                'response_time_ms': status.response_time_ms
            })
        
        # Determine overall health
        unhealthy_count = len([s for s in component_statuses if s['status'] == 'unhealthy'])
        degraded_count = len([s for s in component_statuses if s['status'] == 'degraded'])
        
        if unhealthy_count > 0:
            overall_status = 'unhealthy'
        elif degraded_count > 0:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'service': 'basis-strategy-v1',
            'execution_mode': os.getenv('BASIS_EXECUTION_MODE', 'unknown'),
            'uptime_seconds': self._get_uptime(),
            'response_time_ms': response_time,
            'components': component_statuses,
            'summary': {
                'total_components': len(component_statuses),
                'healthy': len([s for s in component_statuses if s['status'] == 'healthy']),
                'degraded': degraded_count,
                'unhealthy': unhealthy_count
            }
        }
    
    def check_detailed_health(self) -> Dict[str, Any]:
        """Perform detailed health check with full component information."""
        logger.debug("Performing detailed health check")
        
        start_time = time.time()
        component_statuses = []
        dependency_statuses = []
        
        # Check all components
        for component in self.components:
            status = component.check_health()
            component_statuses.append({
                'name': status.name,
                'status': status.status,
                'message': status.message,
                'details': status.details,
                'last_check': status.last_check.isoformat(),
                'response_time_ms': status.response_time_ms
            })
        
        # Check all dependencies
        for dependency in self.dependencies:
            status = dependency.check_health()
            dependency_statuses.append({
                'name': status.name,
                'status': status.status,
                'message': status.message,
                'details': status.details,
                'last_check': status.last_check.isoformat(),
                'response_time_ms': status.response_time_ms
            })
        
        # Determine overall health
        all_statuses = component_statuses + dependency_statuses
        unhealthy_count = len([s for s in all_statuses if s['status'] == 'unhealthy'])
        degraded_count = len([s for s in all_statuses if s['status'] == 'degraded'])
        
        if unhealthy_count > 0:
            overall_status = 'unhealthy'
        elif degraded_count > 0:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'service': 'basis-strategy-v1',
            'execution_mode': os.getenv('BASIS_EXECUTION_MODE', 'unknown'),
            'uptime_seconds': self._get_uptime(),
            'response_time_ms': response_time,
            'components': component_statuses,
            'dependencies': dependency_statuses,
            'summary': {
                'total_components': len(component_statuses),
                'total_dependencies': len(dependency_statuses),
                'healthy': len([s for s in all_statuses if s['status'] == 'healthy']),
                'degraded': degraded_count,
                'unhealthy': unhealthy_count
            }
        }
    
    def _get_uptime(self) -> float:
        """Get system uptime in seconds."""
        try:
            return time.time() - psutil.boot_time()
        except:
            return 0.0


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def check_health() -> Dict[str, Any]:
    """Perform basic health check."""
    checker = get_health_checker()
    return checker.check_health()


def check_detailed_health() -> Dict[str, Any]:
    """Perform detailed health check."""
    checker = get_health_checker()
    return checker.check_detailed_health()