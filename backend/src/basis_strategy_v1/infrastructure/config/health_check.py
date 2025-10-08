"""
Configuration Health Check System

Ensures all components have read configuration and are in a healthy state.
Components must explicitly register that they have read config to be considered healthy.
"""

import time
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ComponentStatus(Enum):
    """Component health status."""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    NOT_INITIALIZED = "not_initialized"


@dataclass
class ComponentHealth:
    """Health status of a component."""
    name: str
    status: ComponentStatus
    last_config_read: Optional[float] = None
    config_version: Optional[str] = None
    error_message: Optional[str] = None
    dependencies: Set[str] = field(default_factory=set)


class ConfigHealthChecker:
    """Health checker for configuration-dependent components."""
    
    def __init__(self):
        self.components: Dict[str, ComponentHealth] = {}
        self.config_version = str(time.time())
        self.required_components = {
            'strategy_manager',
            'cex_execution_manager', 
            'onchain_execution_manager',
            'position_monitor',
            'exposure_monitor',
            'risk_monitor',
            'event_logger',
            'pnl_calculator',
            'data_provider'
        }
    
    def register_component(self, name: str, dependencies: List[str] = None):
        """Register a component that needs to read configuration."""
        if name not in self.components:
            self.components[name] = ComponentHealth(
                name=name,
                status=ComponentStatus.NOT_INITIALIZED,
                dependencies=set(dependencies or [])
            )
            logger.debug(f"Registered component: {name}")
    
    def mark_component_healthy(self, name: str, config_version: str = None):
        """Mark a component as healthy after reading configuration."""
        if name not in self.components:
            self.register_component(name)
        
        self.components[name].status = ComponentStatus.HEALTHY
        self.components[name].last_config_read = time.time()
        self.components[name].config_version = config_version or self.config_version
        self.components[name].error_message = None
        
        logger.debug(f"Component {name} marked as healthy")
    
    def mark_component_unhealthy(self, name: str, error_message: str):
        """Mark a component as unhealthy."""
        if name not in self.components:
            self.register_component(name)
        
        self.components[name].status = ComponentStatus.UNHEALTHY
        self.components[name].error_message = error_message
        
        logger.warning(f"Component {name} marked as unhealthy: {error_message}")
    
    def get_component_status(self, name: str) -> ComponentStatus:
        """Get the status of a specific component."""
        if name not in self.components:
            return ComponentStatus.UNKNOWN
        
        return self.components[name].status
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of all component health."""
        healthy_count = sum(1 for c in self.components.values() if c.status == ComponentStatus.HEALTHY)
        unhealthy_count = sum(1 for c in self.components.values() if c.status == ComponentStatus.UNHEALTHY)
        not_initialized_count = sum(1 for c in self.components.values() if c.status == ComponentStatus.NOT_INITIALIZED)
        
        return {
            'total_components': len(self.components),
            'required_components': len(self.required_components),
            'healthy_components': healthy_count,
            'unhealthy_components': unhealthy_count,
            'not_initialized_components': not_initialized_count,
            'missing_components': len(self.required_components - set(self.components.keys())),
            'overall_health': 'healthy' if unhealthy_count == 0 and not_initialized_count == 0 else 'unhealthy',
            'config_version': self.config_version,
            'components': {
                name: {
                    'status': comp.status.value,
                    'last_config_read': comp.last_config_read,
                    'config_version': comp.config_version,
                    'error_message': comp.error_message,
                    'dependencies': list(comp.dependencies)
                }
                for name, comp in self.components.items()
            }
        }
    
    def is_system_healthy(self) -> bool:
        """Check if the entire system is healthy."""
        summary = self.get_health_summary()
        
        # All required components must be healthy
        if summary['unhealthy_components'] > 0:
            return False
        
        if summary['not_initialized_components'] > 0:
            return False
        
        if summary['missing_components'] > 0:
            return False
        
        return True
    
    def get_unhealthy_components(self) -> List[str]:
        """Get list of unhealthy components."""
        return [
            name for name, comp in self.components.items()
            if comp.status == ComponentStatus.UNHEALTHY
        ]
    
    def get_not_initialized_components(self) -> List[str]:
        """Get list of not initialized components."""
        return [
            name for name, comp in self.components.items()
            if comp.status == ComponentStatus.NOT_INITIALIZED
        ]
    
    def get_missing_components(self) -> List[str]:
        """Get list of missing required components."""
        return list(self.required_components - set(self.components.keys()))
    
    def check_dependencies(self) -> Dict[str, List[str]]:
        """Check if component dependencies are satisfied."""
        dependency_issues = {}
        
        for name, comp in self.components.items():
            if comp.status != ComponentStatus.HEALTHY:
                continue
            
            missing_deps = []
            for dep in comp.dependencies:
                if dep not in self.components or self.components[dep].status != ComponentStatus.HEALTHY:
                    missing_deps.append(dep)
            
            if missing_deps:
                dependency_issues[name] = missing_deps
        
        return dependency_issues
    
    def force_config_reload(self):
        """Force all components to reload configuration."""
        logger.warning("🔄 Forcing configuration reload for all components...")
        
        self.config_version = str(time.time())
        
        # Mark all components as not initialized
        for comp in self.components.values():
            comp.status = ComponentStatus.NOT_INITIALIZED
            comp.last_config_read = None
            comp.config_version = None
            comp.error_message = None
        
        logger.warning("⚠️ All components must re-read configuration to be considered healthy")


# Global health checker instance
_health_checker: Optional[ConfigHealthChecker] = None


def get_health_checker() -> ConfigHealthChecker:
    """Get the global health checker instance."""
    global _health_checker
    
    if _health_checker is None:
        _health_checker = ConfigHealthChecker()
    
    return _health_checker


def register_component(name: str, dependencies: List[str] = None):
    """Register a component with the health checker."""
    checker = get_health_checker()
    checker.register_component(name, dependencies)


def mark_component_healthy(name: str, config_version: str = None):
    """Mark a component as healthy."""
    checker = get_health_checker()
    checker.mark_component_healthy(name, config_version)


def mark_component_unhealthy(name: str, error_message: str):
    """Mark a component as unhealthy."""
    checker = get_health_checker()
    checker.mark_component_unhealthy(name, error_message)


def is_system_healthy() -> bool:
    """Check if the entire system is healthy."""
    checker = get_health_checker()
    return checker.is_system_healthy()


def get_health_summary() -> Dict[str, Any]:
    """Get health summary."""
    checker = get_health_checker()
    return checker.get_health_summary()


def force_config_reload():
    """Force configuration reload."""
    checker = get_health_checker()
    checker.force_config_reload()
