"""
Unified Health Manager

Consolidates infrastructure health, config health, and component health
into a single, mode-aware health checking system.

Features:
- Fast basic health check (< 50ms)
- Comprehensive detailed health check
- Mode-aware (backtest vs live)
- No health history (only last check timestamp)
- No caching (real-time checks)
- Excludes components not needed in current mode
- Preserves 200+ error codes system
"""

import asyncio
import psutil
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Set
import logging

from .component_health import (
    HealthStatus,
    ComponentHealthReport,
    ComponentHealthChecker,
    PositionMonitorHealthChecker,
    DataProviderHealthChecker,
    RiskMonitorHealthChecker,
    EventLoggerHealthChecker,
    system_health_aggregator
)

logger = logging.getLogger(__name__)


class UnifiedHealthManager:
    """Unified health manager that consolidates all health checking."""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.last_check_timestamp = None
        self.execution_mode = self._get_execution_mode()
        
        # Component checkers (will be registered by components)
        self.component_checkers: Dict[str, ComponentHealthChecker] = {}
        
        # Infrastructure dependencies (will be injected)
        self.database = None
        self.cache = None
        self.data_provider = None
        self.live_trading_service = None
    
    def _get_execution_mode(self) -> str:
        """Get current execution mode from environment."""
        import os
        return os.getenv('BASIS_EXECUTION_MODE', 'backtest')
    
    def register_component(self, component_name: str, health_checker: ComponentHealthChecker):
        """Register a component health checker."""
        self.component_checkers[component_name] = health_checker
        logger.debug(f"Registered health checker for {component_name}")
    
    def set_infrastructure_dependencies(self, database=None, cache=None, data_provider=None, live_trading_service=None):
        """Set infrastructure dependencies for health checking."""
        self.database = database
        self.cache = cache
        self.data_provider = data_provider
        self.live_trading_service = live_trading_service
    
    async def check_basic_health(self) -> Dict[str, Any]:
        """
        Fast heartbeat check (< 50ms).
        
        Returns:
            Basic health status with system metrics
        """
        start_time = time.perf_counter()
        
        try:
            # Get basic system metrics
            cpu_percent = psutil.cpu_percent(interval=0.01)  # Very fast check
            memory = psutil.virtual_memory()
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
            
            # Determine overall status (quick check)
            status = "healthy"  # Default to healthy unless critical issues
            
            # Quick infrastructure check (non-blocking)
            try:
                if self.cache and hasattr(self.cache, 'ping'):
                    await asyncio.wait_for(self.cache.ping(), timeout=0.01)
            except:
                # Cache issues don't affect basic health in backtest mode
                if self.execution_mode == 'live':
                    status = "degraded"
            
            self.last_check_timestamp = datetime.utcnow()
            
            return {
                "status": status,
                "timestamp": self.last_check_timestamp.isoformat(),
                "service": "basis-strategy-v1",
                "execution_mode": self.execution_mode,
                "uptime_seconds": uptime,
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Basic health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "basis-strategy-v1",
                "execution_mode": self.execution_mode,
                "error": str(e)
            }
        finally:
            elapsed = (time.perf_counter() - start_time) * 1000
            if elapsed > 50:
                logger.warning(f"Basic health check took {elapsed:.1f}ms (target: <50ms)")
    
    async def check_detailed_health(self) -> Dict[str, Any]:
        """
        Comprehensive health check.
        
        Returns:
            Detailed health status with all components, system metrics, and summary
        """
        timestamp = datetime.utcnow()
        
        try:
            # Get system metrics
            system_metrics = await self._get_system_metrics()
            
            # Get infrastructure health
            infrastructure_health = await self._check_infrastructure_health()
            
            # Get component health (mode-filtered)
            component_health = await self._check_component_health()
            
            # Get live trading health (if in live mode)
            live_trading_health = await self._check_live_trading_health()
            
            # Determine overall status
            overall_status = self._determine_overall_status(
                infrastructure_health, component_health, live_trading_health
            )
            
            # Create summary
            summary = self._create_health_summary(component_health)
            
            # Combine live trading health into components if present
            if live_trading_health:
                component_health["live_trading"] = live_trading_health
            
            self.last_check_timestamp = timestamp
            
            return {
                "status": overall_status,
                "timestamp": timestamp.isoformat(),
                "execution_mode": self.execution_mode,
                "components": component_health,
                "system": system_metrics,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Detailed health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": timestamp.isoformat(),
                "execution_mode": self.execution_mode,
                "error": str(e)
            }
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            
            # Get process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
                "process": {
                    "memory_mb": round(process_memory.rss / (1024**2), 2),
                    "threads": process.num_threads(),
                    "connections": len(process.connections(kind="inet"))
                }
            }
        except Exception as e:
            logger.warning(f"Could not get system metrics: {e}")
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds()
            }
    
    async def _check_infrastructure_health(self) -> Dict[str, str]:
        """Check infrastructure components (Redis, DB, data provider)."""
        infrastructure = {}
        
        # Check database
        if self.database:
            infrastructure["database"] = await self._check_database()
        else:
            infrastructure["database"] = "not_configured"
        
        # Check cache (Redis)
        if self.cache:
            infrastructure["cache"] = await self._check_cache()
        else:
            infrastructure["cache"] = "not_configured"
        
        # Check data provider
        if self.data_provider:
            infrastructure["data_provider"] = await self._check_data_provider()
        else:
            infrastructure["data_provider"] = "not_configured"
        
        return infrastructure
    
    async def _check_database(self) -> str:
        """Check database connectivity."""
        try:
            if hasattr(self.database, 'ping'):
                await self.database.ping()
                return 'healthy'
            elif hasattr(self.database, 'execute'):
                await self.database.execute("SELECT 1")
                return 'healthy'
            elif hasattr(self.database, 'connected'):
                return 'healthy' if self.database.connected else 'unhealthy'
            else:
                logger.warning("Database has no health check method")
                return 'unknown'
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return 'unhealthy'
    
    async def _check_cache(self) -> str:
        """Check cache (Redis) connectivity."""
        try:
            if hasattr(self.cache, 'enabled') and not self.cache.enabled:
                return 'not_configured'
            elif hasattr(self.cache, 'get_health_status'):
                health_status = await self.cache.get_health_status()
                if health_status.get('status') == 'healthy':
                    return 'healthy'
                elif health_status.get('status') == 'disabled':
                    return 'not_configured'
                else:
                    return 'unhealthy'
            elif hasattr(self.cache, 'ping'):
                await self.cache.ping()
                return 'healthy'
            elif hasattr(self.cache, 'get'):
                await self.cache.get("__health_check__")
                return 'healthy'
            else:
                logger.warning("Cache has no health check method")
                return 'unknown'
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return 'unhealthy'
    
    async def _check_data_provider(self) -> str:
        """Check data provider health."""
        try:
            if not self.data_provider:
                return "not_configured"
            
            # Check if data provider is initialized
            if not hasattr(self.data_provider, 'data'):
                return "unhealthy"
            
            # Check environment variables
            import os
            if not os.getenv('BASIS_DATA_MODE'):
                return "unhealthy"
            if not os.getenv('BASIS_EXECUTION_MODE'):
                return "unhealthy"
            
            # Check if data is loaded (new architecture: data loaded on-demand)
            if hasattr(self.data_provider, '_data_loaded'):
                if not self.data_provider._data_loaded:
                    return "not_ready"  # Provider is ready but no data loaded yet
            else:
                # Legacy check for backward compatibility
                if not self.data_provider.data:
                    return "not_ready"
            
            # Check if data provider can provide market data (only if data is loaded)
            if hasattr(self.data_provider, '_data_loaded') and self.data_provider._data_loaded:
                try:
                    test_timestamp = pd.Timestamp('2024-06-01', tz='UTC')
                    market_data = self.data_provider.get_market_data_snapshot(test_timestamp)
                    if not isinstance(market_data, dict) or len(market_data) == 0:
                        return "unhealthy"
                except Exception as e:
                    logger.warning(f"Data provider market data check failed: {e}")
                    return "unhealthy"
            
            return "healthy"
            
        except Exception as e:
            logger.warning(f"Data provider health check failed: {e}")
            return 'unhealthy'
    
    async def _check_component_health(self) -> Dict[str, Any]:
        """Check all registered component health (mode-filtered)."""
        component_health = {}
        
        # Define which components are relevant for each mode
        backtest_components = {
            'position_monitor', 'data_provider', 'risk_monitor', 'event_logger',
            'exposure_monitor', 'pnl_calculator', 'strategy_manager'
        }
        
        live_components = backtest_components | {
            'cex_execution_manager', 'onchain_execution_manager', 'live_data_provider'
        }
        
        # Filter components based on execution mode
        relevant_components = live_components if self.execution_mode == 'live' else backtest_components
        
        # Check each relevant component
        for component_name, checker in self.component_checkers.items():
            if component_name in relevant_components:
                try:
                    report = await checker.check_health()
                    component_health[component_name] = {
                        "status": report.status.value,
                        "timestamp": report.timestamp.isoformat(),
                        "error_code": report.error_code,
                        "error_message": report.error_message,
                        "readiness_checks": report.readiness_checks,
                        "metrics": report.metrics,
                        "dependencies": report.dependencies
                    }
                except Exception as e:
                    logger.error(f"Component health check failed for {component_name}: {e}")
                    component_health[component_name] = {
                        "status": "unknown",
                        "timestamp": datetime.utcnow().isoformat(),
                        "error_code": "HEALTH-001",
                        "error_message": f"Health check failed: {str(e)}",
                        "readiness_checks": {},
                        "metrics": {},
                        "dependencies": []
                    }
        
        return component_health
    
    async def _check_live_trading_health(self) -> Optional[Dict[str, Any]]:
        """Check live trading health (only in live mode)."""
        if self.execution_mode != 'live' or not self.live_trading_service:
            return None
        
        try:
            health = await self.live_trading_service.health_check()
            return {
                "status": "healthy" if health.get('unhealthy_strategies', 0) == 0 else "degraded",
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {
                    "total_strategies": health.get('total_strategies', 0),
                    "healthy_strategies": health.get('healthy_strategies', 0),
                    "unhealthy_strategies": health.get('unhealthy_strategies', 0)
                },
                "strategies": health.get('strategies', [])
            }
        except Exception as e:
            logger.error(f"Live trading health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def _determine_overall_status(self, infrastructure: Dict[str, str], components: Dict[str, Any], live_trading: Optional[Dict[str, Any]]) -> str:
        """Determine overall system status."""
        # Check infrastructure status
        infrastructure_statuses = list(infrastructure.values())
        if 'unhealthy' in infrastructure_statuses:
            return 'unhealthy'
        if 'unknown' in infrastructure_statuses:
            return 'degraded'
        
        # Check component status
        component_statuses = [comp.get('status', 'unknown') for comp in components.values()]
        if 'unhealthy' in component_statuses:
            return 'unhealthy'
        if 'unknown' in component_statuses or 'not_ready' in component_statuses:
            return 'degraded'
        
        # Check live trading status
        if live_trading and live_trading.get('status') == 'unhealthy':
            return 'unhealthy'
        if live_trading and live_trading.get('status') == 'degraded':
            return 'degraded'
        
        return 'healthy'
    
    def _create_health_summary(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Create health summary statistics."""
        total_components = len(components)
        healthy_components = sum(1 for comp in components.values() if comp.get('status') == 'healthy')
        unhealthy_components = sum(1 for comp in components.values() if comp.get('status') == 'unhealthy')
        not_ready_components = sum(1 for comp in components.values() if comp.get('status') == 'not_ready')
        unknown_components = sum(1 for comp in components.values() if comp.get('status') == 'unknown')
        
        return {
            "total_components": total_components,
            "healthy_components": healthy_components,
            "unhealthy_components": unhealthy_components,
            "not_ready_components": not_ready_components,
            "unknown_components": unknown_components
        }


# Global unified health manager instance
unified_health_manager = UnifiedHealthManager()
