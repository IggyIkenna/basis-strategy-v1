"""Health check endpoints."""

from fastapi import APIRouter, Request
from typing import Dict, Any, Optional
import structlog
from datetime import datetime
import asyncio

from ...infrastructure.health.health_checker import get_health_checker
from ..models.responses import HealthResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Basic health check",
    description="Fast heartbeat check (< 50ms) - no authentication required",
)
async def basic_health() -> HealthResponse:
    """
    Fast heartbeat check (< 50ms) - no authentication required.
    Used by Docker/Kubernetes for basic liveness checks.
    """
    try:
        health_checker = get_health_checker()
        health_data = health_checker.check_health()

        # Convert components list to dict for HealthResponse model
        components_list = health_data.get("components", [])
        components_dict = {}
        for comp in components_list:
            components_dict[comp.get("name", "unknown")] = comp

        return HealthResponse(
            status=health_data["status"],
            timestamp=datetime.fromisoformat(health_data["timestamp"].replace("Z", "+00:00")),
            service=health_data.get("service"),
            execution_mode=health_data.get("execution_mode"),
            uptime_seconds=health_data.get("uptime_seconds"),
            system=health_data.get("system"),
            components=components_dict,
            summary=health_data.get("summary"),
        )
    except Exception as e:
        logger.error(f"Basic health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            service="basis-strategy-v1",
            error=str(e),
        )


@router.get(
    "/detailed",
    response_model=HealthResponse,
    summary="Detailed health check",
    description="Comprehensive health with all components, system metrics, and summary - no authentication required",
)
async def detailed_health(request: Request) -> HealthResponse:
    """
    Comprehensive health check - no authentication required.
    Returns all components (mode-filtered), system metrics, and summary.
    Includes live trading health when in live mode.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    try:
        logger.info("Detailed health check requested", correlation_id=correlation_id)

        health_checker = get_health_checker()
        health_data = health_checker.check_detailed_health()

        # Convert components list to dict for HealthResponse model
        components_list = health_data.get("components", [])
        components_dict = {}
        for comp in components_list:
            components_dict[comp.get("name", "unknown")] = comp

        return HealthResponse(
            status=health_data["status"],
            timestamp=datetime.fromisoformat(health_data["timestamp"].replace("Z", "+00:00")),
            service="basis-strategy-v1",
            execution_mode=health_data.get("execution_mode"),
            uptime_seconds=health_data.get("uptime_seconds"),
            system=health_data.get("system"),
            components=components_dict,
            summary=health_data.get("summary"),
        )
    except Exception as e:
        logger.error("Detailed health check failed", correlation_id=correlation_id, error=str(e))
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            service="basis-strategy-v1",
            error=str(e),
        )


@router.get(
    "/components",
    response_model=HealthResponse,
    summary="Component health check",
    description="Component-specific health check - no authentication required",
)
async def component_health(request: Request) -> HealthResponse:
    """
    Component-specific health check - no authentication required.
    Returns health status of individual components.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    try:
        logger.info("Component health check requested", correlation_id=correlation_id)

        health_checker = get_health_checker()
        health_data = health_checker.check_detailed_health()

        # Convert components list to dict for HealthResponse model
        components_list = health_data.get("components", [])
        components_dict = {}
        for comp in components_list:
            components_dict[comp.get("name", "unknown")] = comp

        return HealthResponse(
            status=health_data["status"],
            timestamp=datetime.fromisoformat(health_data["timestamp"].replace("Z", "+00:00")),
            service="basis-strategy-v1",
            execution_mode=health_data.get("execution_mode"),
            uptime_seconds=health_data.get("uptime_seconds"),
            system=health_data.get("system"),
            components=components_dict,
            summary=health_data.get("summary"),
        )
    except Exception as e:
        logger.error("Component health check failed", correlation_id=correlation_id, error=str(e))
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            service="basis-strategy-v1",
            error=str(e),
        )
