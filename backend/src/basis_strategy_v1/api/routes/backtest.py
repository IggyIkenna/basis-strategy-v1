"""Backtest API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from typing import Optional
import structlog

from ..models.requests import BacktestRequest
from ..models.responses import (
    StandardResponse,
    BacktestResponse,
    BacktestStatusResponse,
    BacktestResultResponse
)
from ..dependencies import get_backtest_service
from ...core.services.backtest_service import BacktestService

logger = structlog.get_logger()
router = APIRouter()


@router.get(
    "/list",
    response_model=StandardResponse[list],
    summary="List backtests",
    description="List all backtest executions"
)
async def list_backtests(
    http_request: Request,
    service: BacktestService = Depends(get_backtest_service)
) -> StandardResponse[list]:
    """
    List all backtest executions.
    """
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")
    
    try:
        backtests = await service.list_backtests()
        
        return StandardResponse(
            success=True,
            data=backtests
        )
        
    except Exception as e:
        logger.error(
            "Failed to list backtests",
            correlation_id=correlation_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to list backtests: {str(e)}")


@router.post(
    "/",
    response_model=StandardResponse[BacktestResponse],
    summary="Run a backtest",
    description="Submit a new backtest request for execution"
)
async def run_backtest(
    request: BacktestRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    service: BacktestService = Depends(get_backtest_service)
) -> StandardResponse[BacktestResponse]:
    """
    Run a backtest for the specified strategy and parameters.
    
    The backtest runs asynchronously and returns a request ID for tracking.
    
    # TODO: [WORKFLOW_STRATEGY_SELECTION] - Strategy mode selection via API parameter
    # Current Issue: Strategy mode is selected via strategy_name parameter in BacktestRequest
    # Required Changes:
    #   1. Validate strategy_name against available strategies in STRATEGY_MODES.md
    #   2. Route to appropriate venue clients based on strategy requirements
    #   3. Initialize venue clients based on environment configuration (dev/staging/prod)
    #   4. Implement time-triggered workflow for backtest execution
    # Reference: docs/WORKFLOW_GUIDE.md - Strategy Mode Selection & Venue Architecture Integration section
    # Reference: docs/VENUE_ARCHITECTURE.md - Venue-Based Execution
    # Status: PENDING
    """
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")
    
    try:
        logger.info(
            "Starting backtest",
            correlation_id=correlation_id,
            strategy_name=request.strategy_name,
            share_class=request.share_class.value,
            initial_capital=float(request.initial_capital)
        )
        
        # Convert Pydantic model to service request
        service_request = service.create_request(
            strategy_name=request.strategy_name,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            share_class=request.share_class.value,
            config_overrides=request.config_overrides or {},
            debug_mode=request.debug_mode
        )
        
        # Submit backtest
        request_id = await service.run_backtest(service_request, correlation_id)
        
        logger.info(
            "Backtest queued successfully",
            correlation_id=correlation_id,
            request_id=request_id
        )
        
        return StandardResponse(
            success=True,
            data=BacktestResponse(
                request_id=request_id,
                status="pending",
                strategy_name=request.strategy_name,
                estimated_time_seconds=30  # Could be calculated based on date range
            )
        )
        
    except ValueError as e:
        logger.error(
            "Invalid backtest request",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to start backtest",
            correlation_id=correlation_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to start backtest: {str(e)}")


@router.get(
    "/{request_id}/status",
    response_model=StandardResponse[BacktestStatusResponse],
    summary="Get backtest status",
    description="Check the status of a running backtest"
)
async def get_backtest_status(
    request_id: str,
    http_request: Request,
    service: BacktestService = Depends(get_backtest_service)
) -> StandardResponse[BacktestStatusResponse]:
    """
    Get the current status of a backtest request.
    """
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")
    
    try:
        status = await service.get_status(request_id)
        
        if status.get("status") == "not_found":
            logger.warning(
                "Backtest not found",
                correlation_id=correlation_id,
                request_id=request_id
            )
            raise HTTPException(status_code=404, detail=f"Backtest {request_id} not found")
        
        return StandardResponse(
            success=True,
            data=BacktestStatusResponse(
                request_id=request_id,
                status=status.get("status", "unknown"),
                progress=status.get("progress", 0),
                started_at=status.get("started_at"),
                completed_at=status.get("completed_at"),
                error_message=status.get("error")
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get backtest status",
            correlation_id=correlation_id,
            request_id=request_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get(
    "/{request_id}/result",
    response_model=StandardResponse[BacktestResultResponse],
    summary="Get backtest results", 
    description="Retrieve the results of a completed backtest"
)
async def get_backtest_result(
    request_id: str,
    http_request: Request,
    include_timeseries: bool = False,
    service: BacktestService = Depends(get_backtest_service)
) -> StandardResponse[BacktestResultResponse]:
    """
    Get the results of a completed backtest.
    
    Args:
        request_id: The backtest request ID
        include_timeseries: Whether to include equity curve data
    """
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")
    
    try:
        # Check status first
        status = await service.get_status(request_id)
        
        if status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=f"Backtest {request_id} not found")
        
        if status.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Backtest is not completed. Current status: {status.get('status')}"
            )
        
        # Get result
        result = await service.get_result(request_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Results not found")
        
        logger.info(
            "Returning backtest results",
            correlation_id=correlation_id,
            request_id=request_id,
            include_timeseries=include_timeseries
        )
        
        # Handle both object attributes and dictionary access for compatibility
        def get_attr_or_key(obj, attr, default=None):
            if hasattr(obj, attr):
                return getattr(obj, attr)
            elif isinstance(obj, dict):
                return obj.get(attr, default)
            return default
        
        # Get original request data to fill in missing dates
        # Check if we have the request info in running_backtests or get from status
        request_info = None
        if request_id in service.running_backtests:
            request_info = service.running_backtests[request_id].get("request")
        
        # Fallback dates - use reasonable defaults if not available
        from datetime import datetime, timezone
        default_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        default_end = datetime(2024, 12, 31, tzinfo=timezone.utc)
        
        # Extract dates from request info or use result data
        start_date = get_attr_or_key(result, "start_date")
        end_date = get_attr_or_key(result, "end_date")
        
        if not start_date and request_info:
            # Handle both dict and object access for request_info
            if hasattr(request_info, 'start_date'):
                start_date = request_info.start_date
            elif isinstance(request_info, dict):
                start_date = request_info.get("start_date", default_start)
            else:
                start_date = default_start
        elif not start_date:
            start_date = default_start
            
        if not end_date and request_info:
            # Handle both dict and object access for request_info
            if hasattr(request_info, 'end_date'):
                end_date = request_info.end_date
            elif isinstance(request_info, dict):
                end_date = request_info.get("end_date", default_end)
            else:
                end_date = default_end
        elif not end_date:
            end_date = default_end
        
        # Ensure dates are datetime objects
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        response_data = BacktestResultResponse(
            request_id=get_attr_or_key(result, "request_id", request_id),
            strategy_name=get_attr_or_key(result, "strategy_name", "unknown"),
            start_date=start_date,
            end_date=end_date,
            initial_capital=get_attr_or_key(result, "initial_capital", 0),
            final_value=get_attr_or_key(result, "final_value", 0),
            total_return=get_attr_or_key(result, "total_return", 0),
            annualized_return=get_attr_or_key(result, "annualized_return", 0),
            sharpe_ratio=get_attr_or_key(result, "sharpe_ratio", 0),
            max_drawdown=get_attr_or_key(result, "max_drawdown", 0),
            total_trades=get_attr_or_key(result, "total_trades", 0),
            total_fees=get_attr_or_key(result, "total_fees", 0),
            equity_curve=get_attr_or_key(result, "metrics_history") if include_timeseries else None,
            metrics_summary=get_attr_or_key(result, "metrics_summary", {})
        )
        
        return StandardResponse(
            success=True,
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get backtest result",
            correlation_id=correlation_id,
            request_id=request_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to get result: {str(e)}")


@router.delete(
    "/{request_id}",
    response_model=StandardResponse[dict],
    summary="Cancel a backtest",
    description="Cancel a running backtest"
)
async def cancel_backtest(
    request_id: str,
    http_request: Request,
    service: BacktestService = Depends(get_backtest_service)
) -> StandardResponse[dict]:
    """
    Cancel a running backtest.
    """
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")
    
    try:
        cancelled = await service.cancel_backtest(request_id)
        
        if not cancelled:
            logger.warning(
                "Failed to cancel backtest - not found or already completed",
                correlation_id=correlation_id,
                request_id=request_id
            )
            raise HTTPException(status_code=404, detail=f"Backtest {request_id} not found or already completed")
        
        logger.info(
            "Backtest cancelled successfully",
            correlation_id=correlation_id,
            request_id=request_id
        )
        
        return StandardResponse(
            success=True,
            data={"message": f"Backtest {request_id} cancelled successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to cancel backtest",
            correlation_id=correlation_id,
            request_id=request_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to cancel backtest: {str(e)}")



