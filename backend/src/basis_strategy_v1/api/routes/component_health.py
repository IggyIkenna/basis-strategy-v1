"""
Component Health Check API Endpoints

Provides detailed health checking for all components with timestamps,
error codes, and readiness status validation.
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Dict, Any, Optional
import structlog
from datetime import datetime

from ...core.health import system_health_aggregator, HealthStatus
from ..models.responses import StandardResponse, HealthResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get(
    "/components",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Get detailed component health status",
    description="Get comprehensive health status for all registered components with timestamps and error codes"
)
async def get_component_health(request: Request) -> StandardResponse[Dict[str, Any]]:
    """
    Get detailed health status for all components.
    
    Returns:
        Comprehensive health report with:
        - Overall system status
        - Individual component status with timestamps
        - Error codes for unhealthy components
        - Readiness checks for each component
        - Component metrics and dependencies
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        logger.info(
            "Component health check requested",
            correlation_id=correlation_id
        )
        
        # Get system health report
        health_report = await system_health_aggregator.get_system_health()
        
        return StandardResponse(
            success=True,
            data=health_report,
            message="Component health status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(
            "Component health check failed",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Component health check failed: {str(e)}"
        )


@router.get(
    "/components/{component_name}",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Get health status for specific component",
    description="Get detailed health status for a specific component with history"
)
async def get_component_health_detail(
    component_name: str,
    request: Request,
    limit: int = 10
) -> StandardResponse[Dict[str, Any]]:
    """
    Get detailed health status for a specific component.
    
    Args:
        component_name: Name of the component to check
        limit: Number of historical health reports to return (default: 10)
        
    Returns:
        Component health status with history
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        logger.info(
            "Component health detail requested",
            correlation_id=correlation_id,
            component_name=component_name
        )
        
        # Get system health report
        system_health = await system_health_aggregator.get_system_health()
        
        # Check if component exists
        if component_name not in system_health['components']:
            raise HTTPException(
                status_code=404,
                detail=f"Component '{component_name}' not found"
            )
        
        # Get component health history
        health_history = system_health_aggregator.get_component_health_history(
            component_name, limit
        )
        
        component_data = {
            "current_status": system_health['components'][component_name],
            "health_history": health_history
        }
        
        return StandardResponse(
            success=True,
            data=component_data,
            message=f"Component health status for '{component_name}' retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Component health detail check failed",
            correlation_id=correlation_id,
            component_name=component_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Component health detail check failed: {str(e)}"
        )


@router.get(
    "/readiness",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Check system readiness",
    description="Check if all components are ready for operation"
)
async def check_system_readiness(request: Request) -> StandardResponse[Dict[str, Any]]:
    """
    Check if all components are ready for operation.
    
    Returns:
        Readiness status with details about which components are ready/not ready
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        logger.info(
            "System readiness check requested",
            correlation_id=correlation_id
        )
        
        # Get system health report
        health_report = await system_health_aggregator.get_system_health()
        
        # Analyze readiness
        ready_components = []
        not_ready_components = []
        unhealthy_components = []
        
        for component_name, component_data in health_report['components'].items():
            status = component_data['status']
            if status == 'healthy':
                ready_components.append(component_name)
            elif status == 'not_ready':
                not_ready_components.append(component_name)
            elif status == 'unhealthy':
                unhealthy_components.append(component_name)
        
        # Determine overall readiness
        is_ready = len(unhealthy_components) == 0 and len(not_ready_components) == 0
        
        readiness_data = {
            "is_ready": is_ready,
            "overall_status": health_report['status'],
            "timestamp": health_report['timestamp'],
            "ready_components": ready_components,
            "not_ready_components": not_ready_components,
            "unhealthy_components": unhealthy_components,
            "summary": health_report['summary']
        }
        
        return StandardResponse(
            success=True,
            data=readiness_data,
            message="System readiness status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(
            "System readiness check failed",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"System readiness check failed: {str(e)}"
        )


@router.get(
    "/errors",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Get component error summary",
    description="Get summary of all component errors with error codes"
)
async def get_component_errors(request: Request) -> StandardResponse[Dict[str, Any]]:
    """
    Get summary of all component errors.
    
    Returns:
        Summary of all component errors with error codes and messages
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        logger.info(
            "Component error summary requested",
            correlation_id=correlation_id
        )
        
        # Get system health report
        health_report = await system_health_aggregator.get_system_health()
        
        # Collect all errors
        errors = []
        for component_name, component_data in health_report['components'].items():
            if component_data['error_code']:
                errors.append({
                    "component": component_name,
                    "error_code": component_data['error_code'],
                    "error_message": component_data['error_message'],
                    "status": component_data['status'],
                    "timestamp": component_data['timestamp']
                })
        
        error_summary = {
            "total_errors": len(errors),
            "errors": errors,
            "timestamp": health_report['timestamp']
        }
        
        return StandardResponse(
            success=True,
            data=error_summary,
            message="Component error summary retrieved successfully"
        )
        
    except Exception as e:
        logger.error(
            "Component error summary failed",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Component error summary failed: {str(e)}"
        )
