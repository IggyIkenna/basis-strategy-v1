"""Health check endpoints."""

from fastapi import APIRouter, Depends, Request
from typing import Dict, Any, Optional
import psutil
from datetime import datetime
import structlog

from ...infrastructure.monitoring.health import HealthChecker
from ..models.responses import StandardResponse, HealthResponse
from ..dependencies import get_health_checker_async

logger = structlog.get_logger()
router = APIRouter()


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Basic health check",
    description="Basic health check - no authentication required"
)
async def basic_health() -> HealthResponse:
    """
    Basic health check - no authentication required.
    Used by Docker/Kubernetes for basic liveness checks.
    """
    # Get basic system info for the health check
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            components={
                "service": "basis-strategy-v1",
                "api": "operational",
                "system": "operational"
            },
            metrics={
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2)
            }
        )
    except Exception as e:
        logger.warning(f"Could not get system metrics: {e}")
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            components={
                "service": "basis-strategy-v1",
                "api": "operational"
            }
        )


"""Optional liveness endpoint removed for simplification."""


"""Optional readiness endpoint removed for simplification."""


@router.get(
    "/detailed",
    response_model=HealthResponse,
    summary="Detailed health check",
    description="Detailed health with Redis, data provider, and database status"
)
async def detailed_health(request: Request) -> HealthResponse:
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    try:
        logger.info(
            "Detailed health check requested",
            correlation_id=correlation_id
        )
        checker = await get_health_checker_async()
        detailed = await checker.get_detailed_health()
        metrics = {}
        if "system" in detailed:
            metrics.update(detailed["system"])
        if "process" in detailed:
            metrics.update(detailed["process"])
        if "performance" in detailed:
            metrics.update(detailed["performance"])
        if "uptime_seconds" in detailed:
            metrics["uptime_seconds"] = detailed["uptime_seconds"]
        # Include explicit data provider details for CSV troubleshooting
        if "data_provider_details" in detailed and detailed["data_provider_details"]:
            metrics["data_provider_details"] = detailed["data_provider_details"]

        return HealthResponse(
            status=detailed.get("status", "healthy"),
            timestamp=datetime.utcnow(),
            components=detailed.get("components", {
                "cache": "not_configured",
                "data_provider": "unknown",
                "database": "not_configured"
            }),
            metrics=metrics if metrics else None
        )
    except Exception as e:
        logger.error(
            "Detailed health check failed",
            correlation_id=correlation_id,
            error=str(e)
        )
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            components={"error": str(e)}
        )



