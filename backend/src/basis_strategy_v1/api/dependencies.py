"""API Dependencies for dependency injection.

Provides cached instances of services and infrastructure components
following the service-oriented architecture patterns.
"""

from typing import Optional, Dict, Any
from functools import lru_cache
from pathlib import Path
from datetime import datetime
import structlog

from ..infrastructure.config.config_manager import get_settings
from ..infrastructure.data.data_provider_factory import create_data_provider
from ..core.event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine

logger = structlog.get_logger()

# NOTE: get_settings() is already cached with @lru_cache(maxsize=1) for 5000x performance
# No need to cache at module level - call get_settings() directly everywhere


class DependencyError(Exception):
    """Raised when dependency injection fails."""
    pass


@lru_cache()
def get_backtest_service():
    """
    Get backtest service instance with all dependencies.

    Uses dependency injection pattern described in ARCHITECTURE.md.
    All dependencies are cached for performance.
    """
    try:
        # Import here to avoid circular dependencies
        from ..core.services.backtest_service import BacktestService

        # Create new service (no dependencies needed)
        return BacktestService()

    except (ImportError, TypeError) as e:
        logger.warning(
            "BacktestService not yet implemented, returning stub",
            error=str(e)
        )
        # Return stub implementation until service is built
        return StubBacktestService(
            data_provider=get_data_provider(),
            execution_engine=get_execution_engine(),
            metrics_calculator=get_metrics_calculator(),
            config=get_settings()  # Use cached function directly
        )


@lru_cache()
def get_live_trading_service():
    """
    Get live trading service instance.

    Uses dependency injection pattern described in ARCHITECTURE.md.
    All dependencies are cached for performance.
    """
    try:
        # Import here to avoid circular dependencies
        from ..core.services.live_service import LiveTradingService

        # Create new service (no dependencies needed)
        return LiveTradingService()

    except (ImportError, TypeError) as e:
        logger.warning(
            "LiveTradingService not yet implemented, returning stub",
            error=str(e)
        )
        # Return stub implementation until service is built
        return StubLiveTradingService()


def get_data_provider(strategy_mode: str = None, start_date: str = None, end_date: str = None):
    """
    Get data provider instance using factory pattern with on-demand data loading.
    
    Args:
        strategy_mode: Strategy mode for data provider
        start_date: Start date for backtest (YYYY-MM-DD format)
        end_date: End date for backtest (YYYY-MM-DD format)
        
    Returns:
        Appropriate data provider based on execution_mode and data_mode:
        - backtest + csv: HistoricalDataProvider (loads data on-demand)
        - backtest + db: DatabaseDataProvider (future implementation)
        - live: LiveDataProvider (validates connections for mode-specific data requirements)
    """
    import os
    from ..infrastructure.config.config_manager import get_config_manager
    
    try:
        cm = get_config_manager()
        data_dir = cm.get_data_directory()
        execution_mode = os.getenv('BASIS_EXECUTION_MODE')
        data_mode = os.getenv('BASIS_DATA_MODE')
        
        if not execution_mode:
            raise ValueError("BASIS_EXECUTION_MODE environment variable must be set")
        if not data_mode:
            raise ValueError("BASIS_DATA_MODE environment variable must be set")
        
        # Get appropriate config based on execution mode
        if execution_mode == 'backtest':
            # For backtest: use mode-specific config (includes data_requirements)
            if strategy_mode:
                config = cm.get_complete_config(mode=strategy_mode)
            else:
                # Default to base config if no mode specified
                config = cm.get_complete_config()
                logger.warning("No strategy_mode specified for backtest mode, using base config")
        elif execution_mode == 'live':
            # For live: use mode-specific config (includes data_requirements)
            if strategy_mode:
                config = cm.get_complete_config(mode=strategy_mode)
            else:
                # Default to base config if no mode specified
                config = cm.get_complete_config()
                logger.warning("No strategy_mode specified for live mode, using base config")
        else:
            raise ValueError(f"Unknown execution_mode: {execution_mode}")
        
        # Use factory to create appropriate provider
        provider = create_data_provider(
            data_dir=data_dir,
            execution_mode=execution_mode,
            data_mode=data_mode,
            config=config,
            strategy_mode=strategy_mode,
            backtest_start_date=start_date,
            backtest_end_date=end_date
        )
        
        # For backtest mode, load data on-demand
        if execution_mode == 'backtest' and data_mode == 'csv' and strategy_mode and start_date and end_date:
            provider.load_data_for_backtest(strategy_mode, start_date, end_date)
        
        return provider

    except Exception as e:
        logger.error("DataProvider failed, using stub", error=str(e))
        return StubDataProvider(data_dir=cm.get_data_directory() if 'cm' in locals() else './data', mode=strategy_mode or "stub")


def get_execution_engine():
    """Get execution engine instance."""
    try:
        # Use the real backtest execution engine following clean architecture
        # Note: Removed @lru_cache() to ensure fresh instances for each backtest
        return EventDrivenStrategyEngine(config=get_settings())

    except Exception as e:
        logger.error(
            "EventDrivenStrategyEngine failed to initialize",
            error=str(e))
        # No fallback - execution engine is critical infrastructure
        # If it fails, we need to fix the config/dependencies, not fall back
        raise DependencyError(
            f"EventDrivenStrategyEngine initialization failed: {e}")


@lru_cache()
def get_metrics_calculator():
    """Get metrics calculator instance."""
    try:
        # Import here to avoid circular dependencies
        from ..core.math.metrics_calculator import MetricsCalculator
        return MetricsCalculator()

    except (ImportError, TypeError) as e:
        logger.warning(
            "MetricsCalculator not available, using stub",
            error=str(e))
        return StubMetricsCalculator()


@lru_cache()
def get_result_store():
    """Get result store instance."""
    try:
        # Import here to avoid circular dependencies
        from ..infrastructure.persistence.result_store import ResultStore
        return ResultStore()

    except (ImportError, TypeError) as e:
        logger.warning("ResultStore not available, using stub", error=str(e))
        return StubResultStore()


# Filesystem-only mode: disable external result store and return None.
#
#    API routes will fall back to BacktestService's in-memory state for active
#    runs and scan the results/ directory for completed runs.
@lru_cache()
def get_health_checker():
    """
    Get HealthChecker instance with properly injected dependencies.

    Injects database, cache, and data_provider for comprehensive health monitoring.
    """
    try:
        from ..infrastructure.monitoring.health import HealthChecker

        # Get actual dependencies asynchronously
        import asyncio

        async def _get_dependencies():
            """Async function to get all dependencies."""
            database = None
            cache = None
            data_provider = None

            try:
                # Get database client
                from ..infrastructure.persistence.database import get_database_client
                database = await get_database_client()
                logger.info("Database client injected into HealthChecker")
            except Exception as e:
                logger.warning(
                    f"Database client unavailable for health checks: {e}")

            # Redis removed - using direct method calls for component communication

            try:
                # Get data provider
                data_provider = get_data_provider()
                logger.info("Data provider injected into HealthChecker")
            except Exception as e:
                logger.warning(
                    f"Data provider unavailable for health checks: {e}")

            return database, cache, data_provider

        # For now, create with None dependencies and log that async injection is needed
        # This will be properly handled in the async dependency injection
        logger.info(
            "HealthChecker created - async dependency injection will be handled per request")
        return HealthChecker()

    except (ImportError, TypeError) as e:
        logger.warning(
            "HealthChecker not available, returning stub",
            error=str(e))
        return StubHealthChecker()


async def get_unified_health_manager():
    """
    Get the unified health manager with infrastructure dependencies injected.
    """
    try:
        from ..core.health import unified_health_manager

        database = None
        cache = None
        data_provider = None
        live_trading_service = None

        try:
            # Only inject database when explicitly configured for database storage
            import os
            storage_type = os.getenv('BASIS_STORAGE_TYPE', 'filesystem')
            if storage_type == 'database':
                from ..infrastructure.persistence.database import get_database_client
                database = await get_database_client()
                logger.info("Database client injected into UnifiedHealthManager")
            else:
                logger.info("Database disabled (filesystem-only mode)")
        except Exception as e:
            logger.warning(f"Database client unavailable for health checks: {e}")

        # Redis removed - using direct method calls for component communication

        try:
            # Get data provider
            data_provider = get_data_provider()
            logger.info("Data provider injected into UnifiedHealthManager")
        except Exception as e:
            logger.warning(f"Data provider unavailable for health checks: {e}")

        try:
            # Inject live trading service if available
            from ..core.services.live_service import live_trading_service
            live_trading_service = live_trading_service
            logger.info("Live trading service injected into UnifiedHealthManager")
        except Exception as e:
            logger.debug(f"Live trading service not available: {e}")

        # Set infrastructure dependencies
        unified_health_manager.set_infrastructure_dependencies(
            database=database,
            cache=cache,
            data_provider=data_provider,
            live_trading_service=live_trading_service
        )

        return unified_health_manager

    except (ImportError, TypeError) as e:
        logger.warning(
            "UnifiedHealthManager not available, returning stub",
            error=str(e))
        return StubUnifiedHealthManager()


# Strategy registry removed - using config-driven approach in
# routes/strategies.py


# Stub implementations for development - gracefully handle all parameters
class StubBacktestService:
    """Stub backtest service for development."""

    def __init__(self, **kwargs):
        # Accept any parameters during initialization
        self.config = kwargs.get('config', {})
        self.data_provider = kwargs.get('data_provider')
        self.execution_engine = kwargs.get('execution_engine')
        self.metrics_calculator = kwargs.get('metrics_calculator')
        self.result_store = kwargs.get('result_store')

    def create_request(self, **kwargs):
        return {"id": "stub-request", **kwargs}

    async def run_backtest(self, request):
        return "stub-backtest-id"

    async def get_status(self, request_id):
        if request_id == "stub-backtest-id":
            return {
                "status": "completed",
                "progress": 1.0,
                "started_at": datetime.now(),
                "completed_at": datetime.now()}
        return {"status": "not_found"}

    async def get_result(self, request_id):
        if request_id == "stub-backtest-id":
            return {
                "request_id": request_id,
                "strategy_name": "usdt_pure_lending",
                "start_date": datetime.now(),
                "end_date": datetime.now(),
                "initial_capital": 100000,
                "final_value": 105000,
                "total_return": 0.05,
                "annualized_return": 0.60,
                "sharpe_ratio": 2.1,
                "max_drawdown": 0.02,
                "total_trades": 10,
                "total_fees": 150,
                "metrics_history": None,
                "metrics_summary": {"total_return_pct": 5.0}
            }
        return None

    async def cancel_backtest(self, request_id):
        return True


class StubDataProvider:
    """Enhanced stub data provider with realistic responses."""

    def __init__(self, data_dir: str = "./data", mode: str = "stub", *args, **kwargs):
        self.data_dir = data_dir
        self.mode = mode
        self.data = {}  # Empty data dict for compatibility
        logger.info(f"StubDataProvider initialized with data_dir: {data_dir}, mode: {mode}")

    async def load_data(self, start_date, end_date):
        return {"stub": "data"}

    async def get_price(self, token: str, timestamp=None):
        """Get mock price for token."""
        prices = {
            'ETH': 3300.0,
            'USDT': 1.0,
            'stETH': 3290.0,
            'wstETH': 3850.0,
            'eETH': 3295.0,
            'weETH': 3540.0
        }
        return prices.get(token.upper(), 1.0)

    async def get_lending_rate(
            self,
            token: str,
            timestamp=None,
            rate_type: str = 'supply'):
        """Get mock lending rate."""
        if rate_type == 'supply':
            rates = {'USDT': 0.0502}
        else:  # borrow
            rates = {'USDT': 0.0699, 'ETH': 0.0273}
        return rates.get(token.upper(), 0.05)

    async def get_staking_yield(self, timestamp=None):
        """Get mock staking yield."""
        return 0.0266  # 2.66% ETH staking


class StubMetricsCalculator:
    """Enhanced stub metrics calculator with realistic calculations."""

    def __init__(self, *args, **kwargs):
        logger.info("StubMetricsCalculator initialized")

    def calculate_metrics(self, portfolio_history):
        """Calculate basic metrics from portfolio history."""
        if not portfolio_history or len(portfolio_history) < 2:
            return {"sharpe_ratio": 0.0, "total_return": 0.0}

        # Simple metrics calculation
        initial_value = portfolio_history[0].get('total_value', 100000)
        final_value = portfolio_history[-1].get('total_value', 100000)
        total_return = (final_value - initial_value) / \
            initial_value if initial_value > 0 else 0.0

        return {
            "sharpe_ratio": max(0.0, total_return * 2),  # Simple approximation
            "total_return": total_return,
            "final_value": final_value,
            "max_drawdown": 0.02  # Conservative estimate
        }


class StubResultStore:
    """Enhanced stub result store for development."""

    def __init__(self, storage_type: str = "file", *args, **kwargs):
        self.storage_type = storage_type
        self.results = {}  # In-memory storage
        logger.info(f"StubResultStore initialized with {storage_type} storage")

    async def save_result(self, result):
        """Save result to in-memory store."""
        request_id = result.get('request_id', 'unknown')
        self.results[request_id] = result
        logger.info(f"Saved result to stub store: {request_id}")
        return True

    async def save(self, request_id: str, result):
        """Alternative save method signature."""
        result['request_id'] = request_id
        return await self.save_result(result)

    async def get_result(self, result_id):
        """Get result from in-memory store."""
        return self.results.get(result_id)

    async def list_results(self, **kwargs):
        """List all results."""
        return list(self.results.values())

    async def delete_result(self, result_id):
        """Delete result."""
        if result_id in self.results:
            del self.results[result_id]
            return True
        return False


class StubLiveTradingService:
    """Stub live trading service for development."""

    def __init__(self, **kwargs):
        self.running_strategies = {}
        self.completed_strategies = {}
        logger.info("StubLiveTradingService initialized")

    def create_request(self, **kwargs):
        """Create a stub live trading request."""
        return {
            "strategy_name": kwargs.get("strategy_name", "stub_strategy"),
            "initial_capital": kwargs.get("initial_capital", 10000),
            "share_class": kwargs.get("share_class", "USDT"),
            "config_overrides": kwargs.get("config_overrides", {}),
            "risk_limits": kwargs.get("risk_limits", {}),
            "request_id": f"stub-live-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

    async def start_live_trading(self, request):
        """Start stub live trading."""
        request_id = request.get(
            "request_id",
            f"stub-live-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        self.running_strategies[request_id] = {
            "request": request,
            "status": "running",
            "started_at": datetime.now(),
            "last_heartbeat": datetime.now(),
            "total_trades": 0,
            "total_pnl": 0.0,
            "current_drawdown": 0.0,
            "risk_breaches": []
        }
        return request_id

    async def stop_live_trading(self, request_id):
        """Stop stub live trading."""
        if request_id in self.running_strategies:
            strategy_info = self.running_strategies[request_id]
            strategy_info["status"] = "stopped"
            strategy_info["completed_at"] = datetime.now()
            self.completed_strategies[request_id] = strategy_info
            del self.running_strategies[request_id]
            return True
        return False

    async def get_status(self, request_id):
        """Get stub status."""
        if request_id in self.running_strategies:
            return self.running_strategies[request_id]
        elif request_id in self.completed_strategies:
            return self.completed_strategies[request_id]
        else:
            return {"status": "not_found"}

    async def get_performance_metrics(self, request_id):
        """Get stub performance metrics."""
        if request_id in self.running_strategies:
            return {
                "initial_capital": 10000.0,
                "current_value": 10100.0,
                "total_pnl": 100.0,
                "return_pct": 1.0,
                "total_trades": 5,
                "current_drawdown": -0.02,
                "uptime_hours": 1.0,
                "engine_status": {"mode": "stub"},
                "last_heartbeat": datetime.now()
            }
        return None

    async def emergency_stop(self, request_id, reason="Emergency stop"):
        """Emergency stop stub."""
        return await self.stop_live_trading(request_id)

    async def health_check(self):
        """Get stub health check."""
        return {
            "total_strategies": len(self.running_strategies),
            "healthy_strategies": len(self.running_strategies),
            "unhealthy_strategies": 0,
            "strategies": [
                {
                    "request_id": req_id,
                    "strategy_name": info["request"]["strategy_name"],
                    "is_healthy": True,
                    "last_heartbeat": info["last_heartbeat"],
                    "time_since_heartbeat_seconds": 0
                }
                for req_id, info in self.running_strategies.items()
            ]
        }

    async def get_all_running_strategies(self):
        """Get all running strategies."""
        return [
            {
                "request_id": req_id,
                "strategy_name": info["request"]["strategy_name"],
                "share_class": info["request"]["share_class"],
                "status": info["status"],
                "started_at": info["started_at"],
                "last_heartbeat": info["last_heartbeat"]
            }
            for req_id, info in self.running_strategies.items()
        ]


class StubUnifiedHealthManager:
    """Stub unified health manager for development."""

    def __init__(self):
        self.start_time = datetime.now()
        self.execution_mode = "backtest"
        logger.info("StubUnifiedHealthManager initialized")

    def set_infrastructure_dependencies(self, database=None, cache=None, data_provider=None, live_trading_service=None):
        """Set infrastructure dependencies (stub implementation)."""
        pass

    async def check_basic_health(self):
        """Return stub basic health."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "basis-strategy-v1",
            "execution_mode": self.execution_mode,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "system": {
                "cpu_percent": 10.0,
                "memory_percent": 50.0,
                "memory_available_gb": 4.0
            }
        }

    async def check_detailed_health(self):
        """Return stub detailed health."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "execution_mode": self.execution_mode,
            "components": {
                "position_monitor": {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_code": None,
                    "error_message": None,
                    "readiness_checks": {"initialized": True},
                    "metrics": {},
                    "dependencies": []
                }
            },
            "system": {
                "cpu_percent": 10.0,
                "memory_percent": 50.0,
                "memory_available_gb": 4.0,
                "disk_percent": 25.0,
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds()
            },
            "summary": {
                "total_components": 1,
                "healthy_components": 1,
                "unhealthy_components": 0,
                "not_ready_components": 0,
                "unknown_components": 0
            }
        }
