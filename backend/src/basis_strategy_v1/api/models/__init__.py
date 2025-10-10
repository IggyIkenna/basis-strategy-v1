"""API Models package.

Contains Pydantic models for request/response validation.
"""

from .requests import (
    BacktestRequest,
    LiveTradingRequest,
    RebalanceRequest,
    ShareClass
)
from .responses import (
    StandardResponse,
    BacktestResponse,
    BacktestStatusResponse,
    BacktestResultResponse,
    StrategyInfoResponse,
    StrategyListResponse,
    HealthResponse,
    ErrorResponse,
    ResponseStatus
)

# Alias for backward compatibility
ApiResponse = StandardResponse

__all__ = [
    # Request models
    "BacktestRequest",
    "LiveTradingRequest", 
    "RebalanceRequest",
    "ShareClass",
    # Response models
    "StandardResponse",
    "ApiResponse",
    "BacktestResponse",
    "BacktestStatusResponse", 
    "BacktestResultResponse",
    "StrategyInfoResponse",
    "StrategyListResponse",
    "HealthResponse",
    "ErrorResponse",
    "ResponseStatus",
]
