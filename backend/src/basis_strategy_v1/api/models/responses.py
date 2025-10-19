"""API Response Models."""

from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, Optional, List, Generic, TypeVar
from enum import Enum


T = TypeVar("T")


class ResponseStatus(str, Enum):
    """Response status values."""

    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class StandardResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool = Field(..., description="Whether the request was successful")

    data: Optional[T] = Field(default=None, description="Response data if successful")

    error: Optional[Dict[str, Any]] = Field(
        default=None, description="Error details if unsuccessful"
    )

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"result": "example"},
                "error": None,
                "timestamp": "2025-10-13T12:34:25Z",
            }
        }


class BacktestResponse(BaseModel):
    """Backtest submission response."""

    request_id: str = Field(..., description="Unique request ID for tracking")

    status: ResponseStatus = Field(..., description="Current status of the backtest")

    strategy_name: str = Field(..., description="Strategy being backtested")

    estimated_time_seconds: Optional[int] = Field(
        default=None, description="Estimated completion time in seconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "bt_20251013_123425_abc123",
                "status": "pending",
                "strategy_name": "usdt_market_neutral",
                "estimated_time_seconds": 45,
            }
        }


class BacktestStatusResponse(BaseModel):
    """Backtest status check response."""

    request_id: str
    status: ResponseStatus
    progress: float = Field(ge=0, le=1, description="Progress percentage (0-1)")
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "bt_20251013_123425_abc123",
                "status": "running",
                "progress": 0.65,
                "started_at": "2025-10-13T12:34:25Z",
                "completed_at": None,
                "error_message": None,
            }
        }


class BacktestResultResponse(BaseModel):
    """Complete backtest result."""

    request_id: str
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal
    final_value: Decimal

    # Performance metrics
    total_return: Decimal = Field(..., description="Total return percentage")
    annualized_return: Decimal = Field(..., description="Annualized return percentage")
    sharpe_ratio: Decimal = Field(..., description="Risk-adjusted return metric")
    max_drawdown: Decimal = Field(..., description="Maximum drawdown percentage")
    target_apy: Optional[Decimal] = Field(
        None, description="Target APY from strategy configuration"
    )
    target_max_drawdown: Optional[Decimal] = Field(
        None, description="Target max drawdown from strategy configuration"
    )
    apy_vs_target: Optional[Dict[str, Any]] = Field(
        None, description="APY validation against target"
    )
    drawdown_vs_target: Optional[Dict[str, Any]] = Field(
        None, description="Max drawdown validation against target"
    )

    # Trading statistics
    total_trades: int
    winning_trades: Optional[int] = None
    losing_trades: Optional[int] = None
    total_fees: Decimal

    # Time series data
    equity_curve: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Equity curve time series"
    )

    metrics_summary: Dict[str, Any] = Field(default_factory=dict, description="Additional metrics")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "bt_20251013_123425_abc123",
                "strategy_name": "usdt_market_neutral",
                "start_date": "2024-05-12T00:00:00Z",
                "end_date": "2024-09-10T23:59:59Z",
                "initial_capital": 100000,
                "final_value": 108500,
                "total_return": 0.085,
                "annualized_return": 0.28,
                "sharpe_ratio": 1.8,
                "max_drawdown": 0.035,
                "total_trades": 24,
                "winning_trades": 18,
                "losing_trades": 6,
                "total_fees": 320,
                "equity_curve": None,
                "metrics_summary": {
                    "avg_trade_return": 0.0035,
                    "win_rate": 0.75,
                    "max_consecutive_wins": 5,
                    "max_consecutive_losses": 2,
                },
            }
        }


class StrategyInfoResponse(BaseModel):
    """Strategy information response."""

    name: str
    description: str
    share_class: str
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    expected_return: str = Field(..., description="Expected return range")
    minimum_capital: Optional[Decimal] = None
    supported_venues: List[str]
    parameters: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "usdt_market_neutral",
                "description": "Market-neutral USDT strategy with basis trading and lending",
                "share_class": "USDT",
                "risk_level": "medium",
                "expected_return": "8-15% APY",
                "minimum_capital": 10000,
                "supported_venues": ["AAVE", "Bybit", "Binance"],
                "parameters": {
                    "rebalancing_enabled": True,
                    "max_leverage": 2.0,
                    "funding_rate_threshold": 0.01,
                },
            }
        }


class StrategyListResponse(BaseModel):
    """List of available strategies."""

    strategies: List[StrategyInfoResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "strategies": [
                    {
                        "name": "usdt_market_neutral",
                        "description": "Market-neutral USDT strategy with basis trading and lending",
                        "share_class": "USDT",
                        "risk_level": "medium",
                        "expected_return": "8-15% APY",
                        "minimum_capital": 10000,
                        "supported_venues": ["AAVE", "Bybit", "Binance"],
                        "parameters": {},
                    },
                    {
                        "name": "eth_leveraged",
                        "description": "Leveraged ETH staking with hedging",
                        "share_class": "ETH",
                        "risk_level": "high",
                        "expected_return": "12-25% APY",
                        "minimum_capital": 5000,
                        "supported_venues": ["EigenLayer", "Bybit"],
                        "parameters": {},
                    },
                ],
                "total": 2,
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": {"field": "initial_capital", "error": "Must be greater than 0"},
            }
        }


class LiveTradingResponse(BaseModel):
    """Live trading start response."""

    request_id: str = Field(
        ..., description="Unique request ID for tracking the live trading strategy"
    )

    status: ResponseStatus = Field(..., description="Current status of the live trading strategy")

    strategy_name: str = Field(..., description="Strategy being run live")

    share_class: str = Field(..., description="Share class (USDT or ETH)")

    initial_capital: Decimal = Field(..., description="Initial capital allocated to the strategy")

    message: Optional[str] = Field(default=None, description="Additional status message")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "lt_20251013_123425_def456",
                "status": "started",
                "strategy_name": "usdt_market_neutral",
                "share_class": "USDT",
                "initial_capital": 100000,
                "message": "Live trading started successfully",
            }
        }


class LiveTradingStatusResponse(BaseModel):
    """Live trading status response."""

    request_id: str = Field(..., description="Unique request ID for tracking")

    status: ResponseStatus = Field(..., description="Current status of the live trading strategy")

    progress: Optional[float] = Field(
        default=None, ge=0, le=1, description="Progress percentage (0-1) if applicable"
    )

    started_at: Optional[datetime] = Field(
        default=None, description="When the strategy was started"
    )

    completed_at: Optional[datetime] = Field(
        default=None, description="When the strategy was completed/stopped"
    )

    last_heartbeat: Optional[datetime] = Field(
        default=None, description="Last heartbeat from the strategy"
    )

    total_trades: Optional[int] = Field(default=None, description="Total number of trades executed")

    total_pnl: Optional[Decimal] = Field(default=None, description="Total P&L in strategy currency")

    current_drawdown: Optional[Decimal] = Field(
        default=None, description="Current drawdown percentage"
    )

    risk_breaches: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="List of risk limit breaches"
    )

    error: Optional[str] = Field(default=None, description="Error message if strategy failed")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "lt_20251013_123425_def456",
                "status": "running",
                "progress": None,
                "started_at": "2025-10-13T12:34:25Z",
                "completed_at": None,
                "last_heartbeat": "2025-10-13T12:39:25Z",
                "total_trades": 15,
                "total_pnl": 1250.50,
                "current_drawdown": -0.025,
                "risk_breaches": [],
                "error": None,
            }
        }


class LiveTradingPerformanceResponse(BaseModel):
    """Live trading performance metrics response."""

    request_id: str = Field(..., description="Unique request ID for tracking")

    initial_capital: Decimal = Field(..., description="Initial capital allocated")

    current_value: Decimal = Field(..., description="Current portfolio value")

    total_pnl: Decimal = Field(..., description="Total P&L in strategy currency")

    return_pct: Decimal = Field(..., description="Total return percentage")

    total_trades: int = Field(..., description="Total number of trades executed")

    current_drawdown: Decimal = Field(..., description="Current drawdown percentage")

    uptime_hours: float = Field(..., description="Strategy uptime in hours")

    engine_status: Optional[Dict[str, Any]] = Field(
        default=None, description="Status of the strategy engine components"
    )

    last_heartbeat: Optional[datetime] = Field(default=None, description="Last heartbeat timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "lt_20251013_123425_def456",
                "initial_capital": 100000,
                "current_value": 101250.50,
                "total_pnl": 1250.50,
                "return_pct": 1.25,
                "total_trades": 15,
                "current_drawdown": -0.025,
                "uptime_hours": 24.5,
                "engine_status": {
                    "mode": "usdt_market_neutral",
                    "components": {
                        "position_monitor": "active",
                        "risk_monitor": "active",
                        "strategy_manager": "active",
                    },
                },
                "last_heartbeat": "2025-10-13T12:39:25Z",
            }
        }


# LiveTradingHealthResponse removed - now included in HealthResponse


class LiveTradingStrategiesResponse(BaseModel):
    """List of running live trading strategies response."""

    strategies: List[Dict[str, Any]] = Field(..., description="List of running strategies")

    count: int = Field(..., description="Total number of running strategies")

    class Config:
        json_schema_extra = {
            "example": {
                "strategies": [
                    {
                        "request_id": "lt_20251013_123425_def456",
                        "strategy_name": "usdt_market_neutral",
                        "share_class": "USDT",
                        "status": "running",
                        "started_at": "2025-10-13T12:34:25Z",
                        "last_heartbeat": "2025-10-13T12:39:25Z",
                    }
                ],
                "count": 1,
            }
        }


class HealthResponse(BaseModel):
    """Unified health check response."""

    status: str = Field(..., description="Overall health status: healthy, degraded, unhealthy")
    timestamp: datetime = Field(..., description="Health check timestamp")
    service: Optional[str] = Field(default="basis-strategy-v1", description="Service name")
    execution_mode: Optional[str] = Field(
        default=None, description="Current execution mode: backtest or live"
    )
    uptime_seconds: Optional[float] = Field(default=None, description="Service uptime in seconds")
    system: Optional[Dict[str, Any]] = Field(
        default=None, description="System metrics (CPU, memory, disk)"
    )
    components: Optional[Dict[str, Any]] = Field(
        default=None, description="Component health status (mode-filtered)"
    )
    summary: Optional[Dict[str, Any]] = Field(default=None, description="Health summary statistics")
    error: Optional[str] = Field(default=None, description="Error message if health check failed")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-13T12:34:25Z",
                "service": "basis-strategy-v1",
                "execution_mode": "backtest",
                "uptime_seconds": 3600,
                "system": {"cpu_percent": 15.2, "memory_percent": 45.8, "memory_available_gb": 8.5},
                "components": {
                    "position_monitor": {
                        "status": "healthy",
                        "error_code": None,
                        "readiness_checks": {
                            "initialized": True,
                            "cache_available": True,
                            "snapshot_available": True,
                        },
                    }
                },
                "summary": {
                    "total_components": 9,
                    "healthy_components": 9,
                    "unhealthy_components": 0,
                },
            }
        }
