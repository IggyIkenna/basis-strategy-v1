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
        examples=["usdt_pure_lending", "eth_leveraged_staking"]
    )
    
    start_date: datetime = Field(
        ...,
        description="Backtest start date",
        examples=["2024-01-01T00:00:00Z"]
    )
    
    end_date: datetime = Field(
        ...,
        description="Backtest end date",
        examples=["2024-01-31T00:00:00Z"]
    )
    
    initial_capital: Decimal = Field(
        ...,
        gt=0,
        description="Initial capital amount",
        examples=[100000]
    )
    
    share_class: ShareClass = Field(
        default=ShareClass.USDT,
        description="Share class for the strategy"
    )
    
    config_overrides: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional configuration overrides"
    )
    
    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode to print detailed position monitor state"
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
                "strategy_name": "usdt_pure_lending",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T00:00:00Z",
                "initial_capital": 100000,
                "share_class": "USDT",
                "config_overrides": {
                    "strategy": {
                        "max_underlying_move": 0.12,
                        "max_basis_move": 0.04,
                        "max_staked_basis_move": 0.03,
                        "rebalancing_threshold": 0.10
                    },
                    "rates": {
                        "aave_usdt_supply_apr": 0.045,
                        "eth_staking_apr": 0.030
                    },
                    "fees": {
                        "gas_cost_usd": 30
                    }
                },
                "debug_mode": True
            }
        }


class LiveTradingRequest(BaseModel):
    """Live trading configuration request."""
    
    strategy_name: str = Field(
        ...,
        description="Strategy to run live"
    )
    
    initial_capital: Decimal = Field(
        ...,
        gt=0,
        description="Initial capital to allocate"
    )
    
    share_class: ShareClass = Field(
        default=ShareClass.USDT,
        description="Share class for the strategy"
    )
    
    exchange: str = Field(
        ...,
        description="Exchange to trade on",
        examples=["bybit", "binance"]
    )
    
    api_credentials: Dict[str, str] = Field(
        ...,
        description="Exchange API credentials"
    )
    
    risk_limits: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Risk management limits"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy_name": "usdt_pure_lending",
                "initial_capital": 10000,
                "share_class": "USDT",
                "exchange": "bybit",
                "api_credentials": {
                    "api_key": "your_api_key",
                    "api_secret": "your_api_secret"
                },
                "risk_limits": {
                    "max_position_size": 50000,
                    "max_leverage": 2.0,
                    "stop_loss_pct": 0.10
                }
            }
        }


class RebalanceRequest(BaseModel):
    """Manual rebalancing request."""
    
    strategy_id: str = Field(
        ...,
        description="ID of the running strategy"
    )
    
    force: bool = Field(
        default=False,
        description="Force rebalancing even if not needed"
    )
    
    target_allocation: Optional[Dict[str, Decimal]] = Field(
        default=None,
        description="Optional target allocation override"
    )





