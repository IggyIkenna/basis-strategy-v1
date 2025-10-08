"""Prometheus metrics setup and collection."""

from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
import time
from typing import Callable, Any


# Define metrics
backtest_requests = Counter(
    'backtest_requests_total',
    'Total number of backtest requests',
    ['strategy', 'status']
)

backtest_duration = Histogram(
    'backtest_duration_seconds',
    'Backtest execution time',
    ['strategy'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 300.0)
)

active_backtests = Gauge(
    'active_backtests',
    'Number of currently running backtests'
)

api_requests = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_latency = Histogram(
    'api_latency_seconds',
    'API request latency',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

cache_operations = Counter(
    'cache_operations_total',
    'Cache operations',
    ['operation', 'result']  # operation: get/set, result: hit/miss
)

strategy_metrics = Gauge(
    'strategy_performance',
    'Strategy performance metrics',
    ['strategy', 'metric']  # metric: sharpe_ratio, total_return, etc.
)

system_info = Info(
    'system',
    'System information'
)


def setup_metrics():
    """Initialize metrics with system information."""
    import platform
    
    system_info.info({
        'version': '2.0.0',
        'python_version': platform.python_version(),
        'platform': platform.platform(),
        'node': platform.node()
    })


def track_request(endpoint: str, method: str = "GET"):
    """
    Decorator to track API requests.
    
    Args:
        endpoint: API endpoint
        method: HTTP method
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                api_requests.labels(method=method, endpoint=endpoint, status=status).inc()
                api_latency.labels(method=method, endpoint=endpoint).observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                api_requests.labels(method=method, endpoint=endpoint, status=status).inc()
                api_latency.labels(method=method, endpoint=endpoint).observe(duration)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def track_backtest(strategy: str):
    """
    Decorator to track backtest execution.
    
    Args:
        strategy: Strategy name
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            active_backtests.inc()
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "failure"
                raise
            finally:
                duration = time.time() - start_time
                active_backtests.dec()
                backtest_requests.labels(strategy=strategy, status=status).inc()
                backtest_duration.labels(strategy=strategy).observe(duration)
        
        return wrapper
    
    return decorator


def track_cache_operation(operation: str):
    """
    Track cache operations.
    
    Args:
        operation: Operation type (get, set, delete)
    """
    def track_result(hit: bool):
        """Track cache operation result."""
        result = "hit" if hit else "miss"
        cache_operations.labels(operation=operation, result=result).inc()
    
    return track_result


def record_strategy_metric(strategy: str, metric: str, value: float):
    """
    Record a strategy performance metric.
    
    Args:
        strategy: Strategy name
        metric: Metric name (sharpe_ratio, total_return, etc.)
        value: Metric value
    """
    strategy_metrics.labels(strategy=strategy, metric=metric).set(value)



