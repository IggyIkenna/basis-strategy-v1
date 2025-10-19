"""API Request Models."""

from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import pytz


class ShareClass(str, Enum):
    """Share class options."""

    ETH = "ETH"
    USDT = "USDT"


class BacktestRequest(BaseModel):
    """Backtest execution request."""

    strategy_name: str = Field(
        ...,
        description="Name of the strategy to backtest",
        examples=[
            "usdt_market_neutral",
            "eth_leveraged",
            "pure_lending_usdt",
            "eth_basis",
            "btc_basis",
            "eth_staking_only",
            "usdt_market_neutral_no_leverage",
        ],
    )

    start_date: datetime = Field(
        ...,
        description="Backtest start date",
        examples=["2024-05-12T00:00:00Z", "2024-06-01T00:00:00Z", "2024-07-01T00:00:00Z"],
    )

    end_date: datetime = Field(
        ...,
        description="Backtest end date",
        examples=["2024-08-31T23:59:59Z", "2024-09-10T23:59:59Z", "2025-01-31T23:59:59Z"],
    )

    initial_capital: Decimal = Field(
        ..., gt=0, description="Initial capital amount", examples=[10000, 50000, 100000, 500000]
    )

    share_class: ShareClass = Field(
        default=ShareClass.USDT, description="Share class for the strategy"
    )

    config_overrides: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional configuration overrides. Can override component_config, target_apy, max_drawdown, and other strategy parameters. Examples: component_config.risk_monitor.risk_limits, component_config.pnl_monitor.reconciliation_tolerance, target_apy, max_drawdown",
    )

    debug_mode: bool = Field(
        default=False, description="Enable debug mode to print detailed position monitor state"
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_utc_datetime(cls, v: datetime) -> datetime:
        """Ensure datetime is timezone-aware and convert to UTC if needed."""
        if v.tzinfo is None:
            # Timezone-naive datetime - assume UTC and make timezone-aware
            v = pytz.UTC.localize(v)
        elif v.tzinfo != pytz.UTC:
            # Convert to UTC if not already UTC
            v = v.astimezone(pytz.UTC)
        return v

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: datetime, info) -> datetime:
        """Ensure end date is after start date."""
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("End date must be after start date")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_name": "usdt_market_neutral",
                "start_date": "2024-05-12T00:00:00Z",
                "end_date": "2024-09-10T23:59:59Z",
                "initial_capital": 100000,
                "share_class": "USDT",
                "config_overrides": {
                    "component_config": {
                        "risk_monitor": {
                            "risk_limits": {
                                "aave_health_factor_min": 1.2,
                                "cex_margin_ratio_min": 0.15,
                                "target_ltv": 0.85,
                            }
                        },
                        "pnl_monitor": {"reconciliation_tolerance": 0.01},
                        "strategy_manager": {
                            "position_calculation": {
                                "hedge_allocation": {"binance": 0.5, "bybit": 0.3, "okx": 0.2}
                            }
                        },
                    },
                    "target_apy": 0.12,
                    "max_drawdown": 0.03,
                },
                "debug_mode": False,
            }
        }


class LiveTradingRequest(BaseModel):
    """Live trading configuration request."""

    strategy_name: str = Field(
        ...,
        description="Strategy to run live",
        examples=[
            "usdt_market_neutral",
            "eth_leveraged",
            "pure_lending_usdt",
            "eth_basis",
            "btc_basis",
            "eth_staking_only",
        ],
    )

    share_class: ShareClass = Field(
        default=ShareClass.USDT, description="Share class for the strategy"
    )

    exchange: str = Field(..., description="Exchange to trade on", examples=["bybit", "binance"])

    api_credentials: Dict[str, str] = Field(..., description="Exchange API credentials")

    risk_limits: Optional[Dict[str, Any]] = Field(
        default=None, description="Risk management limits"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_name": "usdt_market_neutral",
                "share_class": "USDT",
                "exchange": "bybit",
                "api_credentials": {"api_key": "your_api_key", "api_secret": "your_api_secret"},
                "risk_limits": {
                    "max_position_size": 50000,
                    "max_leverage": 2.0,
                    "stop_loss_pct": 0.10,
                },
            }
        }


class RebalanceRequest(BaseModel):
    """Manual rebalancing request."""

    strategy_id: str = Field(..., description="ID of the running strategy")

    force: bool = Field(default=False, description="Force rebalancing even if not needed")

    target_allocation: Optional[Dict[str, Decimal]] = Field(
        default=None, description="Optional target allocation override"
    )
