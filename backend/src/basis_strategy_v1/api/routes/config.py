"""Configuration API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
import structlog

from ..models.responses import StandardResponse
from ..dependencies import get_config_manager
from ...infrastructure.config.config_manager import ConfigManager

logger = structlog.get_logger()
router = APIRouter()


@router.get(
    "/",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Get system configuration",
    description="Get the current system configuration",
)
async def get_configuration(
    http_request: Request, config_manager: ConfigManager = Depends(get_config_manager)
) -> StandardResponse[Dict[str, Any]]:
    """Get the current system configuration."""
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")

    try:
        config = config_manager.get_complete_config()

        return StandardResponse(success=True, data=config, correlation_id=correlation_id)

    except Exception as e:
        logger.error(
            "Failed to get configuration",
            correlation_id=correlation_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@router.get(
    "/environment",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Get environment information",
    description="Get environment and deployment information",
)
async def get_environment_info(
    http_request: Request, config_manager: ConfigManager = Depends(get_config_manager)
) -> StandardResponse[Dict[str, Any]]:
    """Get environment and deployment information."""
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")

    try:
        import os

        environment_info = {
            "environment": os.getenv("BASIS_ENVIRONMENT", "unknown"),
            "deployment_mode": os.getenv("BASIS_DEPLOYMENT_MODE", "unknown"),
            "deployment_machine": os.getenv("BASIS_DEPLOYMENT_MACHINE", "unknown"),
            "execution_mode": os.getenv("BASIS_EXECUTION_MODE", "unknown"),
            "data_mode": os.getenv("BASIS_DATA_MODE", "unknown"),
            "debug": os.getenv("BASIS_DEBUG", "false").lower() == "true",
            "log_level": os.getenv("BASIS_LOG_LEVEL", "INFO"),
            "data_dir": os.getenv("BASIS_DATA_DIR", "data"),
            "results_dir": os.getenv("BASIS_RESULTS_DIR", "results"),
        }

        return StandardResponse(success=True, data=environment_info, correlation_id=correlation_id)

    except Exception as e:
        logger.error(
            "Failed to get environment info",
            correlation_id=correlation_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to get environment info: {str(e)}")


@router.get(
    "/status",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Get system status",
    description="Get overall system status and health",
)
async def get_system_status(
    http_request: Request, config_manager: ConfigManager = Depends(get_config_manager)
) -> StandardResponse[Dict[str, Any]]:
    """Get overall system status and health."""
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")

    try:
        import os
        import sys
        import platform

        system_status = {
            "status": "healthy",
            "environment": os.getenv("BASIS_ENVIRONMENT", "unknown"),
            "deployment_mode": os.getenv("BASIS_DEPLOYMENT_MODE", "unknown"),
            "python_version": sys.version,
            "platform": platform.platform(),
            "config_loaded": True,
            "services": {
                "config_manager": "healthy",
                "data_provider": "healthy",
                "strategy_engine": "healthy",
            },
        }

        return StandardResponse(success=True, data=system_status, correlation_id=correlation_id)

    except Exception as e:
        logger.error(
            "Failed to get system status",
            correlation_id=correlation_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")
