"""
Health Check API Endpoints

Provides health check endpoints for load balancers and monitoring systems.
Implements both basic and detailed health checks.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 10 (Health System Architecture)
Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-008 (Health System Unification)
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from ..models import ApiResponse
from ...infrastructure.health.health_checker import check_health, check_detailed_health

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=ApiResponse[Dict[str, Any]])
async def basic_health():
    """
    Basic health check endpoint for load balancers.
    
    Returns simple health status without detailed component information.
    """
    try:
        logger.debug("Basic health check requested")
        
        health_data = check_health()
        
        return ApiResponse(
            success=True,
            data=health_data,
            message="Health check completed"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/health/detailed", response_model=ApiResponse[Dict[str, Any]])
async def detailed_health():
    """
    Detailed health check endpoint for monitoring systems.
    
    Returns comprehensive health information including component details.
    """
    try:
        logger.debug("Detailed health check requested")
        
        health_data = check_detailed_health()
        
        return ApiResponse(
            success=True,
            data=health_data,
            message="Detailed health check completed"
        )
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Detailed health check failed: {str(e)}"
        )


@router.get("/health/status")
async def health_status():
    """
    Simple status endpoint that returns just the health status.
    
    Useful for simple monitoring checks.
    """
    try:
        health_data = check_health()
        
        return {
            "status": health_data.get("status", "unknown"),
            "timestamp": health_data.get("timestamp"),
            "service": health_data.get("service", "basis-strategy-v1")
        }
        
    except Exception as e:
        logger.error(f"Health status check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": None,
            "service": "basis-strategy-v1",
            "error": str(e)
        }