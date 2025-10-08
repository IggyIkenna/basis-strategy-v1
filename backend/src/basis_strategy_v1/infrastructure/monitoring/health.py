"""Health check implementation."""

import asyncio
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class HealthChecker:
    """Component-based health checking."""
    
    def __init__(self, database=None, cache=None, data_provider=None):
        """
        Initialize health checker with optional dependencies.
        
        Args:
            database: Database connection
            cache: Cache client
            data_provider: Data provider service
        """
        self.database = database
        self.cache = cache
        self.data_provider = data_provider
        self.start_time = datetime.utcnow()
    
    async def check_critical_components(self) -> bool:
        """
        Check critical components for readiness.
        
        Returns:
            True if all configured components are healthy or not_configured
            False if any component is unhealthy or unknown
        """
        component_statuses = await self.get_component_status()
        
        # Determine overall health based on component statuses
        for component, status in component_statuses.items():
            if status in ['unhealthy', 'unknown']:
                logger.warning(f"Critical component {component} is {status}")
                return False
        
        # All components are either healthy or not_configured
        healthy_components = [k for k, v in component_statuses.items() if v == 'healthy']
        if healthy_components:
            logger.debug(f"Healthy components: {healthy_components}")
        
        return True
    
    async def _check_database(self) -> str:
        """
        Check database connectivity.
        
        Returns:
            'healthy': Database is operational and can handle requests
            'unhealthy': Database is broken or unreachable
            'unknown': Cannot determine database status
        """
        try:
            if hasattr(self.database, 'ping'):
                # Redis-style ping
                await self.database.ping()
                return 'healthy'
            elif hasattr(self.database, 'execute'):
                # Database-style query
                await self.database.execute("SELECT 1")
                return 'healthy'
            elif hasattr(self.database, 'connected'):
                # Check connected status
                return 'healthy' if self.database.connected else 'unhealthy'
            else:
                # Cannot determine status - this is NOT healthy
                logger.warning("Database has no health check method - cannot determine status")
                return 'unknown'
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return 'unhealthy'
    
    async def _check_cache(self) -> str:
        """
        Check cache connectivity.
        
        Returns:
            'healthy': Cache is operational and can handle requests
            'unhealthy': Cache is broken or unreachable  
            'unknown': Cannot determine cache status
            'not_configured': Cache is intentionally disabled
        """
        try:
            if hasattr(self.cache, 'enabled') and not self.cache.enabled:
                # Cache is intentionally disabled
                return 'not_configured'
            elif hasattr(self.cache, 'get_health_status'):
                # Use RedisClient's built-in health check
                health_status = await self.cache.get_health_status()
                if health_status.get('status') == 'healthy':
                    return 'healthy'
                elif health_status.get('status') == 'disabled':
                    return 'not_configured'
                else:
                    return 'unhealthy'
            elif hasattr(self.cache, 'ping'):
                # Redis-style ping
                await self.cache.ping()
                return 'healthy'
            elif hasattr(self.cache, 'get'):
                # Try a simple get operation (should not error even if key doesn't exist)
                await self.cache.get("__health_check__")
                return 'healthy'
            else:
                # Cannot determine status
                logger.warning("Cache has no health check method - cannot determine status")
                return 'unknown'
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return 'unhealthy'
    
    async def _check_data_provider(self) -> str:
        """
        Check data provider connectivity.
        
        Returns:
            'healthy': Data provider has loaded ALL required data successfully
            'unhealthy': Data provider failed to load data or missing required data
            'unknown': Cannot determine data provider status
        """
        try:
            if self.data_provider:
                # Check if data provider has loaded data successfully
                if hasattr(self.data_provider, 'data_cache'):
                    # Check if data cache exists and has data
                    if not self.data_provider.data_cache:
                        logger.warning("Data provider cache is empty")
                        return 'unhealthy'
                    
                    # Define ALL required data types for healthy status
                    required_data_types = {
                        'funding_rates',
                        'lending_usdt', 'lending_usdc', 'lending_dai', 
                        'lending_weth', 'lending_wsteth', 'lending_weeth',
                        'steth_yields', 'eeth_yields',
                        'wsteth_swap_rates', 'weeth_swap_rates',
                        'spot_prices', 'futures_prices',
                        'benchmark'
                    }
                    
                    cache_keys = set(self.data_provider.data_cache.keys())
                    logger.debug(f"Data provider cache keys: {cache_keys}")
                    
                    # Check that ALL required data types are present and not empty
                    missing_data = []
                    empty_data = []
                    
                    for data_type in required_data_types:
                        if data_type not in cache_keys:
                            missing_data.append(data_type)
                        elif self.data_provider.data_cache[data_type].empty:
                            empty_data.append(data_type)
                    
                    if missing_data:
                        logger.warning(f"Data provider missing required data types: {missing_data}")
                        # Attach detail for API surface via metrics field in detailed endpoint
                        self._last_data_provider_details = {
                            'missing_data': missing_data,
                            'empty_data': empty_data
                        }
                        return 'unhealthy'
                    
                    if empty_data:
                        logger.warning(f"Data provider has empty data for: {empty_data}")
                        self._last_data_provider_details = {
                            'missing_data': missing_data,
                            'empty_data': empty_data
                        }
                        return 'unhealthy'
                    
                    # All required data is present and non-empty
                    logger.debug(f"Data provider healthy: all {len(required_data_types)} data types loaded")
                    self._last_data_provider_details = {
                        'missing_data': [],
                        'empty_data': []
                    }
                    return 'healthy'
                else:
                    # Data provider exists but no cache attribute - cannot determine status
                    logger.warning("Data provider has no data_cache attribute - cannot determine status")
                    return 'unknown'
            else:
                # This shouldn't happen if data_provider was injected, but handle gracefully
                return 'unknown'
        except Exception as e:
            logger.warning(f"Data provider health check failed: {e}")
            return 'unhealthy'
    
    async def get_component_status(self) -> Dict[str, str]:
        """
        Get status of all components.
        
        Returns:
            Dictionary of component statuses with proper health states:
            - 'healthy': Component is operational
            - 'unhealthy': Component is broken
            - 'unknown': Cannot determine status  
            - 'not_configured': Component intentionally not set up
        """
        status = {}
        
        # Check each component if it's configured
        if self.database:
            status["database"] = await self._check_database()
        else:
            status["database"] = "not_configured"
        
        if self.cache:
            status["cache"] = await self._check_cache()
        else:
            status["cache"] = "not_configured"
        
        if self.data_provider:
            status["data_provider"] = await self._check_data_provider()
        else:
            status["data_provider"] = "not_configured"
        
        return status
    
    async def get_detailed_health(self) -> Dict[str, Any]:
        """
        Get detailed health information including metrics.
        
        Returns:
            Detailed health status with performance metrics
        """
        # Get component status
        components = await self.get_component_status()
        
        # Calculate uptime
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        # Get process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Determine overall system status based on component health
        overall_status = self._determine_overall_status(components)
        # Include data provider details (missing/empty) if present
        details = getattr(self, '_last_data_provider_details', None)
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime,
            "components": components,
            "system": {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "percent": disk.percent
                }
            },
            "process": {
                "memory_mb": process_memory.rss / (1024**2),
                "threads": process.num_threads(),
                "connections": len(process.connections(kind="inet"))
            },
            "performance": await self._get_performance_metrics(),
            "data_provider_details": details
        }
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get real-time performance metrics from various sources."""
        try:
            # Get active backtests from BacktestService if available
            active_backtests_count = 0
            try:
                from ...api.dependencies import get_backtest_service
                backtest_service = get_backtest_service()
                if hasattr(backtest_service, 'running_backtests'):
                    active_backtests_count = len(backtest_service.running_backtests)
            except:
                # Fallback to Prometheus metrics
                try:
                    from ..monitoring.metrics import active_backtests
                    active_backtests_count = int(active_backtests._value._value)
                except:
                    active_backtests_count = 0
            
            # Calculate cache hit rate from Redis client if available
            cache_hit_rate = 0
            try:
                if self.cache and hasattr(self.cache, 'get_health_status'):
                    cache_health = await self.cache.get_health_status()
                    # Redis health status doesn't include hit rate, so we'll use cache operations
                    from ..monitoring.metrics import cache_operations
                    cache_hits = cache_operations.labels(operation="get", result="hit")._value._value
                    cache_misses = cache_operations.labels(operation="get", result="miss")._value._value
                    total_cache_ops = cache_hits + cache_misses
                    if total_cache_ops > 0:
                        cache_hit_rate = (cache_hits / total_cache_ops) * 100
            except:
                cache_hit_rate = 0
            
            # Get requests per second (simplified - would need time window in production)
            requests_per_second = 0
            try:
                from ..monitoring.metrics import api_requests
                # This is cumulative, not per-second - would need time-based calculation
                total_requests = sum(
                    metric._value._value 
                    for metric in api_requests._metrics.values()
                )
                # For now, return 0 as proper RPS needs time window tracking
                requests_per_second = 0
            except:
                requests_per_second = 0
            
            return {
                "requests_per_second": requests_per_second,
                "average_latency_ms": 0,  # Would need histogram analysis from api_latency
                "active_backtests": active_backtests_count,
                "cache_hit_rate": round(cache_hit_rate, 1)
            }
            
        except Exception as e:
            logger.warning(f"Could not get performance metrics: {e}")
            # Fallback to safe defaults
            return {
                "requests_per_second": 0,
                "average_latency_ms": 0,
                "active_backtests": 0,
                "cache_hit_rate": 0
            }

    async def _measure_latency(self, check_func) -> float:
        """Measure latency of a health check."""
        import time
        start = time.perf_counter()
        try:
            await check_func()
        except:
            pass
        return (time.perf_counter() - start) * 1000  # Convert to ms
    
    def _determine_overall_status(self, components: Dict[str, str]) -> str:
        """
        Determine overall system status based on component health.
        
        Args:
            components: Dictionary of component statuses
            
        Returns:
            Overall system status:
            - 'healthy': All components healthy or not_configured
            - 'degraded': Some components unhealthy but core functionality works
            - 'unhealthy': Critical components broken
            - 'unknown': Cannot determine system status
        """
        statuses = list(components.values())
        
        # Count different status types
        healthy_count = statuses.count('healthy')
        unhealthy_count = statuses.count('unhealthy')
        unknown_count = statuses.count('unknown')
        not_configured_count = statuses.count('not_configured')
        
        # If any component status is unknown, overall status is unknown
        if unknown_count > 0:
            return 'unknown'
        
        # If any component is unhealthy, system is degraded at minimum
        if unhealthy_count > 0:
            # If more than half of configured components are unhealthy, system is unhealthy
            configured_components = len(statuses) - not_configured_count
            if configured_components > 0 and unhealthy_count >= configured_components / 2:
                return 'unhealthy'
            else:
                return 'degraded'
        
        # If we have at least one healthy component, system is healthy
        if healthy_count > 0:
            return 'healthy'
        
        # All components are not_configured - system is still operational
        return 'healthy'



