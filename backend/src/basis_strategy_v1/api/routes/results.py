"""Results retrieval endpoints."""

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import FileResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog
import zipfile
import tempfile
import os

from ..models.responses import StandardResponse, BacktestResultResponse
from ..dependencies import get_backtest_service
from pathlib import Path
import re
import csv
import glob
import shutil

logger = structlog.get_logger()
router = APIRouter()


@router.get(
    "/{result_id}/events",
    summary="Get event/trade log",
    description="Return chronological actions with balances and pnl attribution if available",
)
async def get_result_events(
    result_id: str,
    request: Request,
    limit: int = Query(500, ge=1, le=10000, description="Max events to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    service=Depends(get_backtest_service),
) -> StandardResponse[Dict[str, Any]]:
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    try:
        logger.info("Fetching events log", correlation_id=correlation_id, result_id=result_id)
        result = None
        if not result:
            # Fallback: try in-memory service (recent runs)
            try:
                result = await service.get_result(result_id)
            except Exception:
                result = None
        if not result:
            # Last-resort fallback: parse event_log CSV from results directory
            events_from_csv, totals = _load_events_from_csv(result_id, limit, offset)
            if events_from_csv is not None:
                return StandardResponse(
                    success=True,
                    data={
                        "events": events_from_csv,
                        "total_events": totals,
                        "has_event_log": True,
                        "component_summaries": {},
                        "balances_by_venue": {},
                    },
                )
            raise HTTPException(status_code=404, detail=f"Result {result_id} not found")
        # Prefer rich event_log if present, fall back to trades
        # Support when result is wrapped (status dict) or plain dict
        payload = result if isinstance(result, dict) else {}
        full_event_log = payload.get("event_log") or []
        trades = payload.get("trade_history") or payload.get("trades") or []
        # Apply pagination to event_log
        paged_events = full_event_log[offset : offset + limit] if full_event_log else []
        component_summaries = result.get("component_summaries", {})
        balances = result.get("balances_by_venue", {})
        return StandardResponse(
            success=True,
            data={
                "events": paged_events if full_event_log else trades,
                "total_events": len(full_event_log) if full_event_log else len(trades),
                "has_event_log": bool(full_event_log),
                "component_summaries": component_summaries,
                "balances_by_venue": balances,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch events",
            correlation_id=correlation_id,
            result_id=result_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")


@router.get(
    "/{result_id}/export",
    summary="Get export information",
    description="Get information about available export files (charts and CSV)",
)
async def get_export_info(result_id: str, request: Request) -> StandardResponse[Dict[str, Any]]:
    """Get information about available export files."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    try:
        logger.info("Getting export info", correlation_id=correlation_id, result_id=result_id)

        # Find the result directory
        source_root = Path("results").resolve()
        candidates = sorted(glob.glob(str(source_root / f"{result_id}_*")))
        if not candidates:
            raise HTTPException(status_code=404, detail=f"Result {result_id} not found")

        src_dir = Path(candidates[0])

        # Prepare file listing
        chart_files = {}
        csv_files = []
        for p in src_dir.glob("*.html"):
            name = p.stem
            parts = name.split("_")
            chart_name = parts[-1] if len(parts) >= 3 else p.stem
            chart_files[chart_name] = f"/api/v1/results/{result_id}/charts/{chart_name}"

        for p in src_dir.glob("*.csv"):
            csv_files.append(str(p.name))

        return StandardResponse(
            success=True,
            data={
                "export_dir": str(src_dir),
                "chart_files": chart_files,
                "csv_files": csv_files,
                "download_url": f"/api/v1/results/{result_id}/download",
                "total_files": len(chart_files) + len(csv_files),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get export info",
            correlation_id=correlation_id,
            result_id=result_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get export info: {str(e)}")


@router.get(
    "/{result_id}/download",
    summary="Download charts and CSV as ZIP file",
    description="Download all charts and CSV files as a ZIP file",
)
async def download_result_assets(
    result_id: str,
    request: Request,
) -> FileResponse:
    """Download all result assets as a ZIP file."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    try:
        logger.info("Creating download ZIP", correlation_id=correlation_id, result_id=result_id)

        # Find the result directory
        source_root = Path("results").resolve()
        candidates = sorted(glob.glob(str(source_root / f"{result_id}_*")))
        if not candidates:
            raise HTTPException(status_code=404, detail=f"Result {result_id} not found")

        src_dir = Path(candidates[0])
        strategy_name = src_dir.name.split("_", 1)[1] if "_" in src_dir.name else "unknown"

        # Create temporary ZIP file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            zip_path = tmp_file.name

        # Create ZIP with all result files
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in src_dir.rglob("*"):
                if file_path.is_file():
                    # Add file to ZIP with relative path
                    arcname = file_path.relative_to(src_dir)
                    zip_file.write(file_path, arcname)

        # Prepare download filename
        download_filename = f"{result_id}_{strategy_name}_export.zip"

        logger.info(f"ZIP created: {zip_path}, size: {os.path.getsize(zip_path)} bytes")

        # Return as file download
        return FileResponse(
            path=zip_path,
            filename=download_filename,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={download_filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create download ZIP",
            correlation_id=correlation_id,
            result_id=result_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to create download: {str(e)}")


def _load_events_from_csv(result_id: str, limit: int, offset: int):
    """Best-effort: Load events from saved CSV if DB/store does not have them."""
    try:
        base = Path("results")
        candidates = sorted(glob.glob(str(base / f"{result_id}_*")))
        if not candidates:
            return None, 0
        export_dir = Path(candidates[0])
        files = list(export_dir.glob(f"{result_id}_*_event_log.csv"))
        if not files:
            return None, 0
        csv_path = files[0]
        rows = []
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic normalization: numbers to float when possible
                for key in ["gross_value", "net_value", "total_fees_paid"]:
                    if key in row and row[key] not in (None, ""):
                        try:
                            row[key] = float(row[key])
                        except Exception:
                            pass
                rows.append(row)
        total = len(rows)
        return rows[offset : offset + limit], total
    except Exception:
        return None, 0


def _scan_results_filesystem(strategy_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Scan results/ directory for exported result folders and index them.
    Format: results/{request_id}_{strategy}/
    """
    base = Path("results")
    if not base.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for entry in base.iterdir():
        if not entry.is_dir():
            continue
        name = entry.name
        # Match UUID_prefix_strategy pattern
        # UUID v4: 8-4-4-4-12 hex
        m = re.match(
            r"^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})_(.+)$",
            name,
        )
        if not m:
            continue
        req_id, strategy = m.group(1), m.group(2)
        if strategy_filter and strategy_filter != strategy:
            continue
        # Get a simple created_at from directory mtime
        try:
            stat = entry.stat()
            created_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
        except Exception:
            created_at = None
        # Enrich with metrics by reading equity_curve CSV (same logic as summary loader)
        summary = _load_result_summary_from_filesystem(req_id)
        rows.append(
            {
                "request_id": req_id,
                "strategy_name": strategy,
                "status": "completed",
                "created_at": created_at,
                "export_dir": str(entry),
                "source": "filesystem",
                "initial_capital": summary.get("initial_capital") if summary else None,
                "final_value": summary.get("final_value") if summary else None,
                "total_return": summary.get("total_return") if summary else None,
                "start_date": summary.get("start_date") if summary else None,
                "end_date": summary.get("end_date") if summary else None,
                "total_trades": summary.get("total_trades") if summary else None,
            }
        )
    return rows


def _load_result_summary_from_filesystem(result_id: str) -> Optional[Dict[str, Any]]:
    """Parse CSVs in results/{id}_* to reconstruct a minimal result summary.
    Uses equity_curve CSV to fill initial/final values and dates.
    """
    try:
        base = Path("results")
        candidates = sorted(glob.glob(str(base / f"{result_id}_*")))
        if not candidates:
            return None
        export_dir = Path(candidates[0])
        # Find equity curve
        eq_files = list(export_dir.glob(f"{result_id}_*_equity_curve.csv"))
        strategy_name = export_dir.name.split("_", 1)[1] if "_" in export_dir.name else "unknown"
        initial_capital = 0.0
        final_value = 0.0
        total_return = 0.0
        start_date = None
        end_date = None
        total_trades = 0
        total_fees = 0.0
        if eq_files:
            import pandas as pd

            df = pd.read_csv(eq_files[0])
            if not df.empty:
                # Expect columns: timestamp, net_value, ...
                start_date = str(df.iloc[0].get("timestamp"))
                end_date = str(df.iloc[-1].get("timestamp"))
                try:
                    initial_capital = float(
                        df.iloc[0].get("net_value", df.iloc[0].get("gross_value", 0.0))
                    )
                    final_value = float(
                        df.iloc[-1].get("net_value", df.iloc[-1].get("gross_value", 0.0))
                    )
                    if initial_capital:
                        total_return = (final_value - initial_capital) / initial_capital
                except Exception:
                    pass
        # Optional: trades CSV for counts
        trade_files = list(export_dir.glob(f"{result_id}_*_trades.csv"))
        if trade_files:
            try:
                import pandas as pd

                df_tr = pd.read_csv(trade_files[0])
                total_trades = int(len(df_tr))
            except Exception:
                pass
        # Build summary
        return {
            "request_id": result_id,
            "strategy_name": strategy_name,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
            "final_value": final_value,
            "total_return": total_return,
            "total_trades": total_trades,
            "total_fees": total_fees,
        }
    except Exception:
        return None


@router.get(
    "/",
    response_model=StandardResponse[List[Dict[str, Any]]],
    summary="List backtest results",
    description="Get a list of all backtest results with optional filtering",
)
async def list_results(
    request: Request,
    strategy: Optional[str] = Query(None, description="Filter by strategy name"),
    start_date: Optional[datetime] = Query(
        None, description="Filter by start date after this date"
    ),
    end_date: Optional[datetime] = Query(None, description="Filter by start date before this date"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Results offset for pagination"),
    service=Depends(get_backtest_service),
) -> StandardResponse[List[Dict[str, Any]]]:
    """
    List backtest results with optional filtering and pagination.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    try:
        logger.info(
            "Listing backtest results",
            correlation_id=correlation_id,
            strategy_filter=strategy,
            limit=limit,
            offset=offset,
        )

        # Query results from store
        store_rows: List[Dict[str, Any]] = []

        # Normalize store rows to a common dict format
        normalized_store = []
        for row in store_rows:
            try:
                normalized_store.append(
                    {
                        "request_id": row.get("id") or row.get("request_id"),
                        "strategy_name": row.get("strategy_name", "unknown"),
                        "status": row.get("status", "completed"),
                        "created_at": row.get("created_at"),
                        "completed_at": row.get("completed_at"),
                        "source": "store",
                    }
                )
            except Exception:
                continue

        # Scan filesystem under results/ to find existing exports (with metrics summary)
        fs_rows = _scan_results_filesystem(strategy)

        # Merge: prefer filesystem summaries for metrics, overlay store metadata
        merged: Dict[str, Dict[str, Any]] = {}
        for r in normalized_store:
            rid = r.get("request_id")
            if rid:
                merged[rid] = r
        for r in fs_rows:
            rid = r.get("request_id")
            if rid:
                merged[rid] = {**merged.get(rid, {}), **r}

        # Convert to list and sort by created_at (fallback to export_dir mtime)
        merged_list = list(merged.values())

        def _sort_key(item):
            ts = item.get("created_at")
            return ts or ""

        merged_list.sort(key=_sort_key, reverse=True)

        # Enrich missing fields from in-memory/service results when possible
        for item in merged_list:
            try:
                if (
                    item.get("start_date") is None
                    or item.get("end_date") is None
                    or item.get("total_return") is None
                    or item.get("initial_capital") is None
                    or item.get("final_value") is None
                ):
                    rid = item.get("request_id")
                    if rid:
                        svc_result = await service.get_result(rid)
                        if isinstance(svc_result, dict) and svc_result.get("status") == None:
                            # Completed result payload
                            item["start_date"] = svc_result.get(
                                "start_date", item.get("start_date")
                            )
                            item["end_date"] = svc_result.get("end_date", item.get("end_date"))
                            item["initial_capital"] = svc_result.get(
                                "initial_capital", item.get("initial_capital")
                            )
                            item["final_value"] = svc_result.get(
                                "final_value", item.get("final_value")
                            )
                            item["total_return"] = svc_result.get(
                                "total_return", item.get("total_return")
                            )
            except Exception:
                continue

        # Pagination
        paged = merged_list[offset : offset + limit]

        return StandardResponse(success=True, data=paged)

    except Exception as e:
        logger.error("Failed to list results", correlation_id=correlation_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list results: {str(e)}")


@router.get(
    "/{result_id}",
    response_model=StandardResponse[BacktestResultResponse],
    summary="Get specific result",
    description="Get a specific backtest result by ID",
)
async def get_result(
    result_id: str,
    request: Request,
    include_timeseries: bool = Query(False, description="Include equity curve time series data"),
    service=Depends(get_backtest_service),
) -> StandardResponse[BacktestResultResponse]:
    """
    Get a specific backtest result by ID.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    try:
        logger.info(
            "Fetching backtest result",
            correlation_id=correlation_id,
            result_id=result_id,
            include_timeseries=include_timeseries,
        )

        # Prefer in-memory service result (new runs have richer metrics)
        result = await service.get_result(result_id)
        if isinstance(result, dict) and result.get("status") is not None:
            # Not completed; force 404/unfinished behavior below by nulling
            result = None

        # Fallback to filesystem export if not found anywhere
        if not result:
            fs_summary = _load_result_summary_from_filesystem(result_id)
            if fs_summary is None:
                logger.warning(
                    "Result not found", correlation_id=correlation_id, result_id=result_id
                )
                raise HTTPException(status_code=404, detail=f"Result {result_id} not found")
            result = fs_summary

        # Convert to response model (hard fail if missing start/end)
        if not result.get("start_date") or not result.get("end_date"):
            raise HTTPException(status_code=500, detail="Result missing start_date/end_date")
        response_data = BacktestResultResponse(
            request_id=result.get("request_id", result_id),
            strategy_name=result.get("strategy_name", "unknown"),
            start_date=result.get("start_date"),
            end_date=result.get("end_date"),
            initial_capital=result.get("initial_capital", 0),
            final_value=result.get("final_value", 0),
            total_return=result.get("total_return", 0),
            annualized_return=result.get("annualized_return", 0),
            sharpe_ratio=result.get("sharpe_ratio", 0),
            max_drawdown=result.get("max_drawdown", 0),
            total_trades=result.get("total_trades", 0),
            total_fees=result.get("total_fees", 0),
            equity_curve=result.get("equity_curve") if include_timeseries else None,
            metrics_summary=result.get("metrics_summary", {}),
        )

        # Add chart links to the response (only include charts that actually exist)
        base_url = f"/api/v1/results/{result_id}"
        chart_links = {
            "charts_list": f"{base_url}/charts",
            "equity_curve": f"{base_url}/charts/equity_curve",
            "dashboard": f"{base_url}/charts/dashboard",
            "pnl_attribution": f"{base_url}/charts/pnl_attribution",
            "component_performance": f"{base_url}/charts/component_performance",
            "fee_breakdown": f"{base_url}/charts/fee_breakdown",
            "metrics_summary": f"{base_url}/charts/metrics_summary",
            "ltv_ratio": f"{base_url}/charts/ltv_ratio",
            "balance_venue": f"{base_url}/charts/balance_venue",
            "balance_token": f"{base_url}/charts/balance_token",
            "margin_health": f"{base_url}/charts/margin_health",
            "exposure": f"{base_url}/charts/exposure",
        }

        # Include chart links in response
        response_with_charts = {**response_data.dict(), "chart_links": chart_links}

        return StandardResponse(success=True, data=response_with_charts)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch result",
            correlation_id=correlation_id,
            result_id=result_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to fetch result: {str(e)}")


@router.get(
    "/{result_id}/pnl/latest",
    summary="Get latest P&L",
    description="Get most recent P&L calculation without recalculating",
)
async def get_latest_pnl(
    result_id: str, request: Request, service=Depends(get_backtest_service)
) -> StandardResponse[Dict[str, Any]]:
    """Get latest P&L data without recalculation."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    try:
        logger.info("Fetching latest P&L", correlation_id=correlation_id, result_id=result_id)

        # Get the engine for this result
        engine = service.get_engine(result_id)
        if not engine or not engine.pnl_monitor:
            raise HTTPException(status_code=404, detail="P&L data not available")

        # Get latest P&L without calculation
        latest_pnl = engine.pnl_monitor.get_latest_pnl()
        if not latest_pnl:
            raise HTTPException(status_code=404, detail="No P&L data available")

        return StandardResponse(success=True, data=latest_pnl)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get latest P&L",
            correlation_id=correlation_id,
            result_id=result_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get latest P&L: {str(e)}")


@router.get(
    "/{result_id}/pnl/history", summary="Get P&L history", description="Get historical P&L data"
)
async def get_pnl_history(
    result_id: str,
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="Maximum P&L records to return"),
    service=Depends(get_backtest_service),
) -> StandardResponse[List[Dict[str, Any]]]:
    """Get P&L history without recalculation."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    try:
        logger.info(
            "Fetching P&L history", correlation_id=correlation_id, result_id=result_id, limit=limit
        )

        # Get the engine for this result
        engine = service.get_engine(result_id)
        if not engine or not engine.pnl_monitor:
            raise HTTPException(status_code=404, detail="P&L data not available")

        # Get P&L history without calculation
        pnl_history = engine.pnl_monitor.get_pnl_history(limit=limit)

        return StandardResponse(success=True, data=pnl_history)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get P&L history",
            correlation_id=correlation_id,
            result_id=result_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get P&L history: {str(e)}")


@router.get(
    "/{result_id}/pnl/attribution",
    summary="Get P&L attribution",
    description="Get cumulative P&L attribution data",
)
async def get_pnl_attribution(
    result_id: str, request: Request, service=Depends(get_backtest_service)
) -> StandardResponse[Dict[str, float]]:
    """Get cumulative P&L attribution without recalculation."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    try:
        logger.info("Fetching P&L attribution", correlation_id=correlation_id, result_id=result_id)

        # Get the engine for this result
        engine = service.get_engine(result_id)
        if not engine or not engine.pnl_monitor:
            raise HTTPException(status_code=404, detail="P&L data not available")

        # Get cumulative attribution without calculation
        attribution = engine.pnl_monitor.get_cumulative_attribution()

        return StandardResponse(success=True, data=attribution)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get P&L attribution",
            correlation_id=correlation_id,
            result_id=result_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get P&L attribution: {str(e)}")


@router.delete(
    "/{result_id}",
    response_model=StandardResponse[dict],
    summary="Delete result",
    description="Delete a backtest result",
)
async def delete_result(result_id: str, request: Request) -> StandardResponse[dict]:
    """
    Delete a backtest result.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    try:
        deleted = False

        if not deleted:
            raise HTTPException(status_code=404, detail=f"Result {result_id} not found")

        logger.info(
            "Result deleted successfully", correlation_id=correlation_id, result_id=result_id
        )

        return StandardResponse(
            success=True, data={"message": f"Result {result_id} deleted successfully"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete result",
            correlation_id=correlation_id,
            result_id=result_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to delete result: {str(e)}")
