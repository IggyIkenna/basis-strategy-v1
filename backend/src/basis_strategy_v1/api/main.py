"""FastAPI Main Application.

Creates and configures the FastAPI application according to the service-oriented
architecture described in ARCHITECTURE.md.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import structlog
import uvicorn
from contextlib import asynccontextmanager
from typing import Optional

from .routes import backtest, strategies, health, results, charts, live_trading, auth, capital
from .middleware.correlation import CorrelationMiddleware
from ..infrastructure.config.config_manager import get_settings
from ..infrastructure.config.config_validator import validate_configuration
from ..infrastructure.monitoring.metrics import setup_metrics
from ..infrastructure.monitoring.logging import setup_logging
import os
import sys

# Early core startup configuration validation - MUST happen before anything else
def validate_core_startup_config():
    """Validate core startup configuration before application starts."""
    # TODO: [ENV_VAR_VALIDATION] - Environment variable validation for quality gates
    # Current Issue: Missing environment-specific credential validation for live mode
    # Required Changes:
    #   1. Add validation for environment-specific venue credentials based on BASIS_ENVIRONMENT
    #   2. Add BASIS_EXECUTION_MODE validation (backtest requires NO credentials, live requires environment-specific credentials)
    #   3. Add quality gate validation for backtest mode (data provider initialization)
    #   4. Add quality gate validation for live mode (venue API health checks)
    # Reference: docs/ENVIRONMENT_VARIABLES.md - Environment Variable Validation Requirements section
    # Reference: docs/QUALITY_GATES.md - Backtest Mode Quality Gates
    # Reference: docs/QUALITY_GATES.md - Live Trading Quality Gates
    # Status: PENDING
    
    core_vars = [
        'BASIS_ENVIRONMENT',
        'BASIS_DEPLOYMENT_MODE', 
        'BASIS_DATA_DIR',
        'BASIS_RESULTS_DIR',
        'BASIS_DEBUG',
        'BASIS_LOG_LEVEL',
        'BASIS_EXECUTION_MODE',
        'BASIS_DATA_MODE',
        'BASIS_DATA_START_DATE',
        'BASIS_DATA_END_DATE',
        'BASIS_API_PORT',
        'BASIS_API_HOST',
        'DATA_LOAD_TIMEOUT',
        'DATA_VALIDATION_STRICT',
        'DATA_CACHE_SIZE',
        'STRATEGY_MANAGER_TIMEOUT',
        'STRATEGY_MANAGER_MAX_RETRIES',
        'STRATEGY_FACTORY_TIMEOUT',
        'STRATEGY_FACTORY_MAX_RETRIES'
    ]
    
    missing_vars = []
    for var in core_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ CRITICAL: Missing required environment variables: {', '.join(missing_vars)}")
        print("💡 Make sure to load environment variables from .env.dev or .env.prod")
        print("💡 Use: source .env.dev or platform.sh start")
        sys.exit(1)
    
    print(f"✅ Core startup configuration validated for {os.getenv('BASIS_ENVIRONMENT')} environment")

# Validate core startup configuration immediately
validate_core_startup_config()

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

# NOTE: get_settings() is already cached with @lru_cache(maxsize=1) for 5000x performance
# Call get_settings() directly where needed instead of caching at module level


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    try: 
        environment = os.getenv('BASIS_ENVIRONMENT')
    except Exception as e:
        logger.error(f"❌ Failed to get environment check there is a valid env file being loaded during deployment: {e}")
        raise RuntimeError(f"Failed to get environment check there is a valid env file being loaded during deployment: {e}")
    
    logger.info(
        "Starting Basis Strategy API", 
        environment=environment,
        version="2.0.0"
    )
    
    # Initialize metrics
    setup_metrics()
    
    # Initialize components (database, cache, etc.)
    # This is where we would initialize:
    # - Database connections
    # - Cache connections (in-memory only)  
    # - Data provider connections
    # - Monitoring systems
    try:
        # Phase 4: Load configuration and data at startup using new architecture
        from ..infrastructure.config.config_manager import get_config_manager
        from .dependencies import get_data_provider
        
        # Initialize config manager (already cached)
        config_manager = get_config_manager()
        execution_mode = os.getenv('BASIS_EXECUTION_MODE', 'unknown')
        data_mode = os.getenv('BASIS_DATA_MODE', 'unknown')
        logger.info(f"✅ Config manager initialized - execution mode: {execution_mode}, data mode: {data_mode}")
        
        # Data provider will be created on-demand during API calls
        # No data loading at startup - follows new architecture
        logger.info("✅ Data provider architecture ready (on-demand loading)")
        
        logger.info("🚀 API startup completed successfully with new architecture")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize with new architecture: {e}")
        # Fail fast - don't continue with broken setup
        raise RuntimeError(f"API startup failed: {e}")
    
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Basis Strategy API")
    # Cleanup connections and resources here


def create_application() -> FastAPI:
    """Create and configure FastAPI application.
    
    Follows the architecture patterns described in ARCHITECTURE.md:
    - Service-Engine separation
    - Interface-based design
    - Async services
    - Configuration caching
    - Type safety with Pydantic
    """
    # Use environment variables directly for core startup config
    debug_mode = os.getenv('BASIS_DEBUG')
    api_host = os.getenv('BASIS_API_HOST')
    api_port = int(os.getenv('BASIS_API_PORT'))
    log_level = os.getenv('BASIS_LOG_LEVEL')
    
    app = FastAPI(
        title="Basis Strategy API",
        description="DeFi Basis Trading Strategy Platform - Production-Ready API",
        version="2.0.0",
        docs_url="/docs" if debug_mode else None,
        redoc_url="/redoc" if debug_mode else None,
        lifespan=lifespan,
        openapi_tags=[
            {
                "name": "health",
                "description": "Health check endpoints for monitoring"
            },
            {
                "name": "auth",
                "description": "Authentication and user management"
            },
            {
                "name": "capital",
                "description": "Capital management (deposits and withdrawals)"
            },
            {
                "name": "strategies", 
                "description": "Strategy information and management"
            },
            {
                "name": "backtest",
                "description": "Backtest execution and management"
            },
            {
                "name": "live_trading",
                "description": "Live trading execution and management"
            },
            {
                "name": "results",
                "description": "Result retrieval (filesystem-only)"
            }
        ]
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3001", "null"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add correlation ID middleware for tracing
    app.add_middleware(CorrelationMiddleware)
    
    # Include routers with API versioning
    app.include_router(
        health.router,
        prefix="/health",
        tags=["health"]
    )
    app.include_router(
        auth.router,
        prefix="/api/v1/auth",
        tags=["auth"]
    )
    app.include_router(
        capital.router,
        prefix="/api/v1/capital",
        tags=["capital"]
    )
    app.include_router(
        backtest.router,
        prefix="/api/v1/backtest",
        tags=["backtest"]
    )
    app.include_router(
        live_trading.router,
        prefix="/api/v1/live",
        tags=["live_trading"]
    )
    app.include_router(
        strategies.router,
        prefix="/api/v1/strategies", 
        tags=["strategies"]
    )
    app.include_router(
        results.router,
        prefix="/api/v1/results",
        tags=["results"]
    )
    app.include_router(
        charts.router,
        prefix="/api/v1/results",
        tags=["charts"]
    )
    
    # Mount Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        
        logger.error(
            "Unhandled exception",
            correlation_id=correlation_id,
            exc_info=exc,
            path=request.url.path,
            method=request.method
        )
        
        # Check debug mode from environment variable
        debug_mode = os.getenv('BASIS_DEBUG', 'false').lower() == 'true'
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                    "details": str(exc) if debug_mode else None
                },
                "correlation_id": correlation_id
            }
        )
    
    # Root endpoint with API information
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        debug_mode = os.getenv('BASIS_DEBUG', 'false').lower() == 'true'
        return {
            "name": "Basis Strategy API",
            "version": "2.0.0",
            "description": "DeFi Basis Trading Strategy Platform",
            "status": "operational",
            "documentation": "/docs" if debug_mode else "Disabled in production",
            "health": "/health",
            "detailed_health": "/health/detailed",
            "metrics": "/metrics"
        }
    
    return app


# Create app instance
app = create_application()


def run(host: Optional[str] = None, port: Optional[int] = None):
    """Run the application with uvicorn."""
    # Use environment variables directly
    debug_mode = os.getenv('BASIS_DEBUG') == 'true'
    api_host = os.getenv('BASIS_API_HOST')
    api_port = int(os.getenv('BASIS_API_PORT'))
    log_level = os.getenv('BASIS_LOG_LEVEL')
    
    uvicorn.run(
        "basis_strategy_v1_v1.api.main:app",
        host=host or api_host,
        port=port or api_port,
        reload=debug_mode,
        access_log=debug_mode,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "structured": {
                    "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
                }
            },
            "handlers": {
                "default": {
                    "formatter": "structured" if not debug_mode else "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout"
                }
            },
            "root": {
                "level": log_level,
                "handlers": ["default"]
            }
        }
    )


if __name__ == "__main__":
    run()



