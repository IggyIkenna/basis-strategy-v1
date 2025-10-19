"""Live Trading API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from typing import Optional, Dict, Any
import structlog

from ..models.requests import LiveTradingRequest, RebalanceRequest
from ..models.responses import (
    StandardResponse,
    LiveTradingResponse,
    LiveTradingStatusResponse,
    LiveTradingPerformanceResponse,
    LiveTradingStrategiesResponse,
    BacktestResponse,
)
from ..dependencies import get_live_trading_service
from ...core.services.live_service import LiveTradingService

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    "/start",
    response_model=StandardResponse[LiveTradingResponse],
    summary="Start live trading",
    description="Start a live trading strategy with the specified parameters",
)
async def start_live_trading(
    request: LiveTradingRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    service: LiveTradingService = Depends(get_live_trading_service),
) -> StandardResponse[BacktestResponse]:
    """
    Start live trading for the specified strategy and parameters.

    The strategy runs asynchronously and returns a request ID for tracking.

    # Strategy mode selection implemented via strategy_name parameter validation
    # Strategy validation and venue routing handled by StrategyFactory
    """
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")

    try:
        logger.info(
            "Starting live trading",
            correlation_id=correlation_id,
            strategy_name=request.strategy_name,
            share_class=request.share_class,
        )

        # Convert API request to service request
        service_request = service.create_request(
            strategy_name=request.strategy_name,
            share_class=request.share_class,
            config_overrides={
                "exchange": request.exchange,
                "api_credentials": request.api_credentials,
            },
            risk_limits=request.risk_limits,
        )

        # Start live trading
        request_id = await service.start_live_trading(service_request)

        logger.info(
            "Live trading started successfully",
            correlation_id=correlation_id,
            request_id=request_id,
        )

        return StandardResponse(
            success=True,
            data=LiveTradingResponse(
                request_id=request_id,
                status="started",
                strategy_name=request.strategy_name,
                share_class=request.share_class.value,
                initial_capital=request.initial_capital,
                message="Live trading started successfully",
            ),
            correlation_id=correlation_id,
        )

    except ValueError as e:
        logger.warning(
            "Live trading validation failed", correlation_id=correlation_id, error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(
            "Live trading start failed", correlation_id=correlation_id, error=str(e), exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to start live trading: {str(e)}")


@router.get(
    "/status",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Get live trading system status",
    description="Get the overall live trading system status",
)
async def get_live_trading_system_status(
    http_request: Request, service: LiveTradingService = Depends(get_live_trading_service)
) -> StandardResponse[Dict[str, Any]]:
    """Get the overall live trading system status."""
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")

    try:
        system_status = await service.get_system_status()

        return StandardResponse(success=True, data=system_status, correlation_id=correlation_id)

    except Exception as e:
        logger.error(
            "Failed to get live trading system status",
            correlation_id=correlation_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


@router.get(
    "/status/{request_id}",
    response_model=StandardResponse[LiveTradingStatusResponse],
    summary="Get live trading status",
    description="Get the current status of a live trading strategy",
)
async def get_live_trading_status(
    request_id: str,
    http_request: Request,
    service: LiveTradingService = Depends(get_live_trading_service),
) -> StandardResponse[LiveTradingStatusResponse]:
    """Get the current status of a live trading strategy."""
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")

    try:
        status = await service.get_status(request_id)

        if status["status"] == "not_found":
            raise HTTPException(status_code=404, detail="Live trading strategy not found")

        return StandardResponse(
            success=True,
            data=LiveTradingStatusResponse(
                request_id=request_id,
                status=status["status"],
                progress=status.get("progress"),
                started_at=status.get("started_at"),
                completed_at=status.get("completed_at"),
                last_heartbeat=status.get("last_heartbeat"),
                total_trades=status.get("total_trades"),
                total_pnl=status.get("total_pnl"),
                current_drawdown=status.get("current_drawdown"),
                risk_breaches=status.get("risk_breaches"),
                error=status.get("error"),
            ),
            correlation_id=correlation_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get live trading status",
            correlation_id=correlation_id,
            request_id=request_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get(
    "/performance/{request_id}",
    response_model=StandardResponse[LiveTradingPerformanceResponse],
    summary="Get live trading performance",
    description="Get performance metrics for a live trading strategy",
)
async def get_live_trading_performance(
    request_id: str,
    http_request: Request,
    service: LiveTradingService = Depends(get_live_trading_service),
) -> StandardResponse[LiveTradingPerformanceResponse]:
    """Get performance metrics for a live trading strategy."""
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")

    try:
        metrics = await service.get_performance_metrics(request_id)

        if metrics is None:
            raise HTTPException(status_code=404, detail="Live trading strategy not found")

        return StandardResponse(
            success=True,
            data=LiveTradingPerformanceResponse(
                request_id=request_id,
                initial_capital=metrics.get("initial_capital"),
                current_value=metrics.get("current_value"),
                total_pnl=metrics.get("total_pnl"),
                return_pct=metrics.get("return_pct"),
                total_trades=metrics.get("total_trades"),
                current_drawdown=metrics.get("current_drawdown"),
                uptime_hours=metrics.get("uptime_hours"),
                engine_status=metrics.get("engine_status"),
                last_heartbeat=metrics.get("last_heartbeat"),
            ),
            correlation_id=correlation_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get live trading performance",
            correlation_id=correlation_id,
            request_id=request_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get performance: {str(e)}")


@router.post(
    "/stop/{request_id}",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Stop live trading",
    description="Stop a running live trading strategy",
)
async def stop_live_trading(
    request_id: str,
    http_request: Request,
    service: LiveTradingService = Depends(get_live_trading_service),
) -> StandardResponse[Dict[str, Any]]:
    """Stop a running live trading strategy."""
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")

    try:
        success = await service.stop_live_trading(request_id)

        if not success:
            raise HTTPException(
                status_code=404, detail="Live trading strategy not found or already stopped"
            )

        logger.info(
            "Live trading stopped successfully",
            correlation_id=correlation_id,
            request_id=request_id,
        )

        return StandardResponse(
            success=True,
            data={"message": "Live trading stopped successfully", "request_id": request_id},
            correlation_id=correlation_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to stop live trading",
            correlation_id=correlation_id,
            request_id=request_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to stop live trading: {str(e)}")


@router.post(
    "/emergency-stop/{request_id}",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Emergency stop live trading",
    description="Emergency stop a live trading strategy with reason",
)
async def emergency_stop_live_trading(
    request_id: str,
    reason: str = "Emergency stop requested",
    http_request: Request = None,
    service: LiveTradingService = Depends(get_live_trading_service),
) -> StandardResponse[Dict[str, Any]]:
    """Emergency stop a live trading strategy."""
    correlation_id = (
        getattr(http_request.state, "correlation_id", "unknown") if http_request else "unknown"
    )

    try:
        success = await service.emergency_stop(request_id, reason)

        if not success:
            raise HTTPException(status_code=404, detail="Live trading strategy not found")

        logger.warning(
            "Live trading emergency stopped",
            correlation_id=correlation_id,
            request_id=request_id,
            reason=reason,
        )

        return StandardResponse(
            success=True,
            data={
                "message": "Live trading emergency stopped",
                "request_id": request_id,
                "reason": reason,
            },
            correlation_id=correlation_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to emergency stop live trading",
            correlation_id=correlation_id,
            request_id=request_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to emergency stop: {str(e)}")


# Live trading health now included in /health/detailed endpoint


@router.get(
    "/strategies",
    response_model=StandardResponse[LiveTradingStrategiesResponse],
    summary="List running strategies",
    description="Get list of all currently running live trading strategies",
)
async def list_running_strategies(
    http_request: Request, service: LiveTradingService = Depends(get_live_trading_service)
) -> StandardResponse[LiveTradingStrategiesResponse]:
    """Get list of all currently running live trading strategies."""
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")

    try:
        strategies = await service.get_all_running_strategies()

        return StandardResponse(
            success=True,
            data=LiveTradingStrategiesResponse(strategies=strategies, count=len(strategies)),
            correlation_id=correlation_id,
        )

    except Exception as e:
        logger.error(
            "Failed to list running strategies", correlation_id=correlation_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to list strategies: {str(e)}")


@router.post(
    "/rebalance",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Manual rebalancing",
    description="Trigger manual rebalancing for a running strategy",
)
async def manual_rebalance(
    request: RebalanceRequest,
    http_request: Request,
    service: LiveTradingService = Depends(get_live_trading_service),
) -> StandardResponse[Dict[str, Any]]:
    """
    Trigger manual rebalancing for a running strategy.

    Note: This is a placeholder endpoint. The actual rebalancing logic
    is handled by the StrategyManager and TransferManager components
    orchestrated by the EventDrivenStrategyEngine.
    """
    correlation_id = getattr(http_request.state, "correlation_id", "unknown")

    try:
        # Check if strategy is running
        status = await service.get_status(request.strategy_id)

        if status["status"] == "not_found":
            raise HTTPException(status_code=404, detail="Strategy not found")

        if status["status"] not in ["running", "starting"]:
            raise HTTPException(status_code=400, detail="Strategy is not running")

        # TODO: Implement actual rebalancing logic
        # This would involve:
        # 1. Getting current exposure from ExposureMonitor
        # 2. Getting risk assessment from RiskMonitor
        # 3. Having StrategyManager generate rebalancing instructions
        # 4. Having TransferManager execute the rebalancing

        logger.info(
            "Manual rebalancing requested",
            correlation_id=correlation_id,
            strategy_id=request.strategy_id,
            force=request.force,
        )

        return StandardResponse(
            success=True,
            data={
                "message": "Rebalancing request received",
                "strategy_id": request.strategy_id,
                "note": "Rebalancing logic handled by StrategyManager and TransferManager",
            },
            correlation_id=correlation_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to trigger rebalancing",
            correlation_id=correlation_id,
            strategy_id=request.strategy_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to trigger rebalancing: {str(e)}")
