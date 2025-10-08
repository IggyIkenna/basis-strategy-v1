"""Chart serving endpoints for backtest results."""

from fastapi import APIRouter, HTTPException, Path, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path as FilePath
from typing import Dict, Any
from glob import glob as glob_files
import structlog

from ..dependencies import get_backtest_service
from ...core.services.backtest_service import BacktestService

logger = structlog.get_logger()
router = APIRouter()


@router.get(
    "/{request_id}/charts",
    response_model=Dict[str, str],
    summary="List available charts",
    description="Get a list of all available charts for a backtest result"
)
async def list_charts(
    request_id: str = Path(..., description="Backtest request ID"),
    request: Request = ...,
    service: BacktestService = Depends(get_backtest_service)
) -> JSONResponse:
    """List all available charts for a backtest result.

    Robust fallback: if the result record isn't found in the store, attempt to
    discover generated chart files on disk and list only those that exist.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    try:
        logger.info("Listing available charts", correlation_id=correlation_id, request_id=request_id)

        # Default chart names (expanded with newly implemented charts)
        default_charts = [
            "equity_curve",
            "pnl_attribution",
            "component_performance",
            "fee_breakdown",
            "metrics_summary",
            "dashboard",
            "ltv_ratio",
            "balance_venue",
            "balance_token",
            "margin_health",
            "exposure",
        ]

        # Try to load the result (for presence and potential strategy name)
        result = await service.get_result(request_id)
        strategy_name = None
        if result:
            strategy_name = result.get("strategy_name")
        else:
            # Fallback: infer strategy name from results directory
            results_dir = FilePath("results")
            if results_dir.exists():
                for item in results_dir.iterdir():
                    if item.is_dir() and item.name.startswith(request_id + "_"):
                        parts = item.name.split("_", 1)
                        if len(parts) == 2:
                            strategy_name = parts[1]
                            logger.info("Inferred strategy name for listing", correlation_id=correlation_id,
                                        request_id=request_id, strategy_name=strategy_name)
                            break

        charts_found: Dict[str, str] = {}

        def chart_exists(name: str) -> bool:
            # Candidate paths to check for presence of generated HTML
            candidate_paths = [
                FilePath(f"results/{request_id}_{strategy_name}/{request_id}_{strategy_name}_{name}.html") if strategy_name else None,
                FilePath(f"results/{request_id}/{name}.html"),
                FilePath(f"results/{name}.html"),
                FilePath(f"odum-basis-strategy-v1/results/{name}.html"),
                FilePath(f"odum-basis-strategy-v1/results/scenarios/{strategy_name}/{strategy_name}_{name}.html") if strategy_name else None,
            ]
            for p in candidate_paths:
                if p and p.exists():
                    return True
            # Glob fallback
            results_root = FilePath("results")
            for pattern in [
                f"{request_id}_*/{request_id}_*_{name}.html",
                f"{request_id}/{name}.html",
                f"**/{request_id}_*_{name}.html",
            ]:
                for path_str in glob_files(str(results_root / pattern), recursive=True):
                    return True
            legacy_root = FilePath("odum-basis-strategy-v1/results")
            for pattern in [
                f"{name}.html",
                f"scenarios/*/*_{name}.html",
            ]:
                for path_str in glob_files(str(legacy_root / pattern), recursive=True):
                    return True
            return False

        # 1) Discover all saved chart HTMLs under results/{request_id}_*
        if strategy_name:
            results_dir = FilePath(f"results/{request_id}_{strategy_name}")
            if results_dir.exists():
                for p in results_dir.glob("*.html"):
                    stem = p.stem  # requestid_strategy_name_chart
                    parts = stem.split("_")
                    chart_name = parts[-1] if len(parts) >= 3 else stem
                    charts_found[chart_name] = f"/api/v1/results/{request_id}/charts/{chart_name}"

        # 2) Include any default charts present even if not discovered above
        for name in default_charts:
            if name not in charts_found and chart_exists(name):
                charts_found[name] = f"/api/v1/results/{request_id}/charts/{name}"

        if not charts_found:
            # If we do have a result record, still return default endpoints
            if result:
                charts_found = {name: f"/api/v1/results/{request_id}/charts/{name}" for name in default_charts}
            else:
                # No result and no files discovered
                raise HTTPException(status_code=404, detail=f"No charts found for backtest {request_id}")

        return JSONResponse(content={"charts": charts_found})

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list charts", correlation_id=correlation_id, request_id=request_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list charts: {str(e)}")


@router.get(
    "/{request_id}/charts/{chart_name}",
    response_class=HTMLResponse,
    summary="Get specific chart",
    description="Get a specific interactive chart as HTML"
)
async def get_chart(
    request_id: str = Path(..., description="Backtest request ID"),
    chart_name: str = Path(..., description="Chart name (equity_curve, dashboard, etc.)"),
    request: Request = ...,
    service: BacktestService = Depends(get_backtest_service)
) -> HTMLResponse:
    """Serve a specific chart as interactive HTML."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        logger.info("Serving chart", correlation_id=correlation_id, request_id=request_id, chart_name=chart_name)
        
        # Try to get backtest result for strategy name
        result = await service.get_result(request_id)
        strategy_name = "unknown"
        
        if result:
            strategy_name = result.get("strategy_name", "unknown")
        else:
            # If result not found, try to infer strategy name from existing chart files
            # This is a fallback for when results aren't stored but charts exist
            results_dir = FilePath("results")
            logger.info(f"Result not found for {request_id}, trying to infer strategy name from directories")
            for item in results_dir.iterdir():
                logger.debug(f"Checking directory: {item.name}")
                if item.is_dir() and item.name.startswith(request_id):
                    # Extract strategy name from directory name: request_id_strategy_name
                    parts = item.name.split("_", 1)
                    logger.debug(f"Directory parts: {parts}")
                    if len(parts) == 2:
                        strategy_name = parts[1]
                        logger.info(f"Inferred strategy name '{strategy_name}' from directory: {item.name}")
                        break
            
            if strategy_name == "unknown":
                logger.warning(f"Could not infer strategy name for {request_id}")
        
        # Valid chart names
        
        valid_charts = {
            "equity_curve",
            "pnl_attribution",
            "component_performance",
            "fee_breakdown",
            "metrics_summary",
            "dashboard",
            "ltv_ratio",
            "balance_venue",
            "balance_token",
            "margin_health",
            "exposure",
        }
        
        if chart_name not in valid_charts:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid chart name. Valid options: {', '.join(valid_charts)}"
            )
        
        # Check multiple possible locations (prioritize request_id naming)
        chart_paths = [
            # PRIMARY: Request-specific results with strategy name (our new format)
            FilePath(f"results/{request_id}_{strategy_name}/{request_id}_{strategy_name}_{chart_name}.html"),
            # SECONDARY: Request-specific results (simple)
            FilePath(f"results/{request_id}/{chart_name}.html"),
            # FALLBACK: Current run (root results/) 
            FilePath(f"results/{chart_name}.html"),
            # FALLBACK: Old sophisticated backtester format
            FilePath(f"odum-basis-strategy-v1/results/{chart_name}.html"),
            # FALLBACK: Scenario-specific results
            FilePath(f"odum-basis-strategy-v1/results/scenarios/{strategy_name}/{strategy_name}_{chart_name}.html")
        ]
        
        chart_content = None
        logger.debug(f"Looking for chart '{chart_name}' with strategy '{strategy_name}'")
        for i, chart_path in enumerate(chart_paths):
            logger.debug(f"Trying path {i+1}: {chart_path}")
            if chart_path.exists():
                logger.info(f"Found chart at: {chart_path}")
                try:
                    with open(chart_path, 'r', encoding='utf-8') as f:
                        chart_content = f.read()
                    logger.info(f"Successfully read chart content ({len(chart_content)} chars)")
                    break
                except Exception as e:
                    logger.error(f"Failed to read chart file {chart_path}: {e}")
            else:
                logger.debug(f"Chart path does not exist: {chart_path}")
        
        # Fallback: try to locate chart via glob search by request_id and chart_name
        if not chart_content:
            try:
                logger.info("Attempting glob-based fallback to locate chart file",
                            correlation_id=correlation_id, request_id=request_id, chart_name=chart_name)

                # Search under results/ using patterns that match our naming convention
                results_root = FilePath("results")
                patterns = [
                    f"{request_id}_*/{request_id}_*_{chart_name}.html",  # request-specific named dir/file
                    f"{request_id}/{chart_name}.html",                     # simple request dir
                    f"**/{request_id}_*_{chart_name}.html",                # any nested path
                ]

                matched_path = None
                for pattern in patterns:
                    logger.debug(f"Glob searching: results/{pattern}")
                    for path_str in glob_files(str(results_root / pattern), recursive=True):
                        matched_path = FilePath(path_str)
                        logger.info(f"Glob matched chart at: {matched_path}")
                        break
                    if matched_path:
                        break

                if not matched_path:
                    # Also try legacy odum directory
                    legacy_root = FilePath("odum-basis-strategy-v1/results")
                    for pattern in patterns:
                        logger.debug(f"Glob searching legacy: {legacy_root}/{pattern}")
                        for path_str in glob_files(str(legacy_root / pattern), recursive=True):
                            matched_path = FilePath(path_str)
                            logger.info(f"Glob matched legacy chart at: {matched_path}")
                            break
                        if matched_path:
                            break

                if matched_path and matched_path.exists():
                    with open(matched_path, 'r', encoding='utf-8') as f:
                        chart_content = f.read()
                    logger.info(f"Successfully read chart content from glob match ({len(chart_content)} chars)")
            except Exception as e:
                logger.error(f"Glob-based fallback failed: {e}")

        if not chart_content:
            raise HTTPException(
                status_code=404, 
                detail=f"Chart '{chart_name}' not found for backtest {request_id}"
            )
        
        return HTMLResponse(
            content=chart_content,
            headers={"Content-Type": "text/html; charset=utf-8"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to serve chart", correlation_id=correlation_id, 
                    request_id=request_id, chart_name=chart_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to serve chart: {str(e)}")


@router.get(
    "/{request_id}/dashboard",
    response_class=HTMLResponse, 
    summary="Get comprehensive dashboard",
    description="Get the comprehensive dashboard with all charts and metrics"
)
async def get_dashboard(
    request_id: str = Path(..., description="Backtest request ID"),
    request: Request = ...,
    service: BacktestService = Depends(get_backtest_service)
) -> HTMLResponse:
    """Serve the comprehensive dashboard chart."""
    return await get_chart(request_id, "dashboard", request, service)
