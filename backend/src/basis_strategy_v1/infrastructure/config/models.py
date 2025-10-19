"""
Pydantic Models for Configuration Validation

Defines Pydantic models for all configuration types to ensure
type safety, validation, and fail-fast behavior.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 33 (Fail-Fast Configuration)
Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-040 (Fail-Fast Configuration)
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class StrategyType(str, Enum):
    """Strategy type enumeration."""

    LENDING = "lending"
    STAKING = "staking"
    BASIS_TRADING = "basis_trading"
    LEVERAGED = "leveraged"
    MARKET_NEUTRAL = "market_neutral"


class VenueType(str, Enum):
    """Venue type enumeration."""

    CEX = "cex"
    DEFI = "defi"
    INFRASTRUCTURE = "infrastructure"


class ShareClassType(str, Enum):
    """Share class type enumeration."""

    STABLE = "stable"
    DIRECTIONAL = "directional"


class BaseCurrency(str, Enum):
    """Base currency enumeration."""

    USDT = "USDT"
    ETH = "ETH"
    BTC = "BTC"


class ModeConfig(BaseModel):
    """Mode configuration model."""

    model_config = {"extra": "allow"}  # Allow extra fields for flexibility

    # Core identification
    mode: str = Field(..., description="Mode name")

    # Strategy flags
    lending_enabled: bool = Field(..., description="Whether lending is enabled")
    staking_enabled: bool = Field(..., description="Whether staking is enabled")
    basis_trade_enabled: bool = Field(..., description="Whether basis trading is enabled")
    borrowing_enabled: Optional[bool] = Field(None, description="Whether borrowing is enabled")
    enable_market_impact: Optional[bool] = Field(
        None, description="Whether market impact is enabled"
    )

    # Asset configuration
    share_class: str = Field(..., description="Share class (USDT or ETH)")
    margin_currency: Optional[str] = Field(None, description="Margin currency (USDT, ETH, or BTC)")
    lst_type: Optional[str] = Field(None, description="LST type if applicable")
    position_deviation_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Position deviation threshold"
    )

    # Risk parameters
    margin_ratio_target: Optional[float] = Field(None, ge=0.0, description="Margin ratio target")
    target_apy: Optional[float] = Field(None, ge=0.0, description="Target APY")
    max_drawdown: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maximum drawdown")

    # Execution parameters
    time_throttle_interval: Optional[int] = Field(
        None, ge=1, description="Time throttle interval in seconds"
    )

    # Data requirements - removed as part of DATA_ARCHITECTURE_REFACTOR_PLAN.md
    # CSV mappings are now derived from position_subscriptions in data providers

    # Optional fields for specific strategies
    leverage_enabled: Optional[bool] = Field(None, description="Whether leverage is enabled")
    liquidation_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Liquidation threshold"
    )
    max_stake_spread_move: Optional[float] = Field(
        None, ge=0.0, description="Maximum stake spread move"
    )

    # Venue configuration
    venues: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Venue configuration with instruments and order types"
    )

    # Hedge configuration
    hedge_venues: Optional[List[str]] = Field(None, description="Hedge venues")
    hedge_allocation: Optional[Dict[str, float]] = Field(
        None, description="Hedge allocation percentages"
    )

    # Individual hedge allocation fields (for backward compatibility)
    hedge_allocation_binance: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Binance hedge allocation"
    )
    hedge_allocation_bybit: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Bybit hedge allocation"
    )
    hedge_allocation_okx: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="OKX hedge allocation"
    )

    # Component configuration
    component_config: Optional[Dict[str, Any]] = Field(
        None, description="Component-specific configuration"
    )

    # Component config subfields (for validation)
    component_settlement: Optional[Dict[str, Any]] = Field(
        None, description="Settlement component configuration"
    )
    component_live_trading_service: Optional[Dict[str, Any]] = Field(
        None, description="Live trading service configuration"
    )
    component_position_update_handler: Optional[Dict[str, Any]] = Field(
        None, description="Position update handler configuration"
    )

    # Settlement config subfields
    settlement_funding_enabled: Optional[bool] = Field(
        None, description="Settlement funding enabled"
    )
    settlement_seasonal_rewards_enabled: Optional[bool] = Field(
        None, description="Settlement seasonal rewards enabled"
    )
    settlement_margin_pnl_enabled: Optional[bool] = Field(
        None, description="Settlement margin PnL enabled"
    )
    settlement_seasonal_rewards_frequency: Optional[str] = Field(
        None, description="Settlement seasonal rewards frequency"
    )

    # Live trading service config subfields
    live_trading_service_execution_timeout: Optional[int] = Field(
        None, ge=1, description="Live trading service execution timeout"
    )
    live_trading_service_timeout: Optional[int] = Field(
        None, ge=1, description="Live trading service timeout"
    )

    # Position update handler config subfields
    position_update_handler_reconciliation_tolerance: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Position update handler reconciliation tolerance"
    )

    # Additional fields used in YAML files but not in current model
    hedge_allocation: Optional[Dict[str, float]] = Field(
        None, description="Hedge allocation mapping"
    )

    # ML-specific configuration
    ml_config: Optional[Dict[str, Any]] = Field(None, description="ML model configuration")

    # ML config subfields (for validation)
    ml_model_name: Optional[str] = Field(None, description="ML model name")
    ml_model_version: Optional[str] = Field(None, description="ML model version")
    ml_signal_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="ML signal threshold"
    )
    ml_max_position_size: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="ML maximum position size"
    )
    ml_confidence_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="ML confidence threshold"
    )
    ml_retraining_frequency: Optional[str] = Field(None, description="ML retraining frequency")
    ml_feature_importance_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="ML feature importance threshold"
    )

    # Additional ML config fields
    ml_signal_granularity: Optional[str] = Field(None, description="ML signal granularity")
    ml_sd_cap_bps: Optional[float] = Field(
        None, ge=0.0, description="ML standard deviation cap in basis points"
    )
    ml_take_profit_sd: Optional[float] = Field(
        None, ge=0.0, description="ML take profit standard deviation"
    )
    ml_sd_floor_bps: Optional[float] = Field(
        None, ge=0.0, description="ML standard deviation floor in basis points"
    )
    ml_stop_loss_sd: Optional[float] = Field(
        None, ge=0.0, description="ML stop loss standard deviation"
    )

    # Event logger configuration
    event_logger: Dict[str, Any] = Field(..., description="Event logger configuration")

    # Strategy-specific parameters
    # Note: delta_tolerance moved to component_config.risk_monitor (now under risk params)
    dust_delta: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Dust delta threshold for small positions"
    )
    stake_allocation_percentage: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="ETH stake allocation percentage"
    )

    # Protocol configuration
    lending_protocol: Optional[str] = Field(None, description="Lending protocol (e.g., AAVE)")
    staking_protocol: Optional[str] = Field(
        None, description="Staking protocol (e.g., Lido, EtherFi)"
    )

    # Data configuration
    data_type: Optional[str] = Field(None, description="Data type for strategy")
    data_requirements: Optional[List[str]] = Field(
        None, description="Data requirements for strategy"
    )

    # Risk parameters
    funding_threshold: Optional[float] = Field(None, ge=0.0, description="Funding threshold")
    rewards_mode: Optional[str] = Field(None, description="Rewards mode")
    max_ltv: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Maximum loan-to-value ratio"
    )
    target_ltv: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Target loan-to-value ratio"
    )

    # Strategy configuration (legacy - for backward compatibility)
    strategy_config: Optional[Dict[str, Any]] = Field(
        None, description="Strategy configuration (legacy)"
    )

    # Strategy config subfields (for validation)
    strategy_signal_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Strategy signal threshold"
    )
    strategy_max_position_size: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Strategy maximum position size"
    )
    strategy_stop_loss_pct: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Strategy stop loss percentage"
    )
    strategy_delta_tracking_asset: Optional[str] = Field(
        None, description="Strategy delta tracking asset"
    )
    strategy_target_ltv: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Strategy target LTV"
    )
    strategy_position_deviation_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Strategy position deviation threshold"
    )

    @field_validator("share_class")
    @classmethod
    def validate_share_class(cls, v):
        """Validate share class is USDT, ETH, or BTC."""
        if v not in ["USDT", "ETH", "BTC"]:
            raise ValueError(f"share_class must be 'USDT', 'ETH', or 'BTC', got: {v}")
        return v

    @field_validator("margin_currency")
    @classmethod
    def validate_margin_currency(cls, v):
        """Validate margin currency is valid."""
        if v is not None:
            valid_currencies = ["USDT", "ETH", "BTC", "USDC"]
            if v not in valid_currencies:
                raise ValueError(f"margin_currency must be one of {valid_currencies}, got: {v}")
        return v

    @model_validator(mode="after")
    def validate_business_logic(self):
        """Validate business logic constraints."""
        # Leverage requires borrowing
        if self.leverage_enabled and not self.borrowing_enabled:
            raise ValueError(f"Mode {self.mode}: leverage_enabled requires borrowing_enabled")

        # Staking requires lst_type
        if self.staking_enabled and not self.lst_type:
            raise ValueError(f"Mode {self.mode}: staking_enabled requires lst_type")

        # Validate LST type → venue mapping
        if self.staking_enabled and self.lst_type and self.venues:
            expected_venue = (
                "etherfi"
                if self.lst_type == "weeth"
                else "lido"
                if self.lst_type == "wsteth"
                else None
            )
            if expected_venue and expected_venue not in self.venues:
                raise ValueError(
                    f"Mode {self.mode}: lst_type '{self.lst_type}' requires venue '{expected_venue}' in venues config"
                )

        # Borrowing requires max_ltv
        if self.borrowing_enabled and not self.max_ltv:
            raise ValueError(f"Mode {self.mode}: borrowing_enabled requires max_ltv")

        # Validate hedge configuration (LEGACY FIELDS - now in component_config.strategy_manager.position_calculation)
        # These validations only apply if using legacy hedge_venues/hedge_allocation fields at root level
        # The preferred location is now component_config.strategy_manager.position_calculation.hedge_allocation
        if (
            self.hedge_venues
            and not self.hedge_allocation
            and not any(
                [
                    self.hedge_allocation_binance,
                    self.hedge_allocation_bybit,
                    self.hedge_allocation_okx,
                ]
            )
        ):
            logger.warning(
                f"Mode {self.mode}: hedge_venues specified but no hedge_allocation. Consider using component_config.strategy_manager.position_calculation.hedge_allocation instead"
            )

        if (
            self.hedge_allocation
            or any(
                [
                    self.hedge_allocation_binance,
                    self.hedge_allocation_bybit,
                    self.hedge_allocation_okx,
                ]
            )
        ) and not self.hedge_venues:
            logger.warning(
                f"Mode {self.mode}: hedge allocation specified but no hedge_venues. Consider using component_config.strategy_manager.position_calculation.hedge_allocation instead"
            )

        # Check hedge allocation sums to 1.0 (legacy field)
        if self.hedge_allocation:
            total_allocation = sum(self.hedge_allocation.values())
            if abs(total_allocation - 1.0) > 0.01:
                raise ValueError(
                    f"Mode {self.mode}: hedge_allocation sums to {total_allocation}, expected 1.0"
                )

        # Check individual allocation fields sum to 1.0 (legacy fields)
        individual_allocations = [
            self.hedge_allocation_binance,
            self.hedge_allocation_bybit,
            self.hedge_allocation_okx,
        ]
        if any(individual_allocations):
            total_individual = sum(a for a in individual_allocations if a is not None)
            if abs(total_individual - 1.0) > 0.01:
                raise ValueError(
                    f"Mode {self.mode}: individual hedge allocations sum to {total_individual}, expected 1.0"
                )

        # NEW: Venue-LST validation
        if self.staking_enabled and self.lst_type and self.venues:
            expected_venue = (
                "etherfi"
                if self.lst_type == "weeth"
                else "lido"
                if self.lst_type == "wsteth"
                else None
            )
            if expected_venue and expected_venue not in self.venues:
                raise ValueError(
                    f"Mode {self.mode}: lst_type '{self.lst_type}' requires venue '{expected_venue}' in venues config"
                )

        # NEW: Share class consistency validation (config-driven)
        # Load share class configuration to validate asset compatibility
        try:
            import yaml
            from pathlib import Path

            # Load share class config
            share_class_file = (
                Path(__file__).parent.parent.parent.parent.parent
                / "configs"
                / "share_classes"
                / f"{self.share_class.lower()}_stable.yaml"
            )
            if not share_class_file.exists():
                share_class_file = (
                    Path(__file__).parent.parent.parent.parent.parent
                    / "configs"
                    / "share_classes"
                    / f"{self.share_class.lower()}_directional.yaml"
                )

            if share_class_file.exists():
                with open(share_class_file, "r") as f:
                    share_class_config = yaml.safe_load(f)

                market_neutral = share_class_config.get("market_neutral", False)

                # Asset validation is now handled through component_config.risk_monitor.delta_tracking_asset
                # This ensures proper separation of concerns and config-driven architecture

        except Exception as e:
            # If share class config loading fails, log warning but don't fail validation
            logger.warning(f"Could not load share class config for validation: {e}")

        # NEW: Risk parameter alignment
        if self.max_drawdown and self.max_drawdown > 0.5:
            logger.warning(f"Mode {self.mode}: High max_drawdown {self.max_drawdown} (>50%)")

        if self.target_apy and self.target_apy > 100:
            logger.warning(f"Mode {self.mode}: Very high target_apy {self.target_apy}% (>100%)")

        # NEW: Basis trading validation
        # Check if hedge allocation is defined in component_config.strategy_manager.position_calculation.hedge_allocation
        hedge_allocation_defined = (
            self.component_config
            and isinstance(self.component_config, dict)
            and "strategy_manager" in self.component_config
            and isinstance(self.component_config["strategy_manager"], dict)
            and "position_calculation" in self.component_config["strategy_manager"]
            and isinstance(self.component_config["strategy_manager"]["position_calculation"], dict)
            and "hedge_allocation"
            in self.component_config["strategy_manager"]["position_calculation"]
        )

        # Also check for legacy hedge_venues field or venues with perp instruments for backward compatibility
        legacy_hedge_defined = self.hedge_venues or (
            self.venues
            and any(
                venue_name in ["binance", "bybit", "okx"]
                and venue_config.get("instruments")
                and any("PERP" in str(inst).upper() for inst in venue_config.get("instruments", []))
                for venue_name, venue_config in self.venues.items()
            )
        )

        hedge_venues_defined = hedge_allocation_defined or legacy_hedge_defined

        if self.basis_trade_enabled and not hedge_venues_defined:
            raise ValueError(
                f"Mode {self.mode}: basis_trade_enabled requires hedge_allocation in component_config.strategy_manager.position_calculation or venues with perpetual instruments"
            )

        # NEW: Market neutral validation
        if "market_neutral" in self.mode.lower() and not hedge_venues_defined:
            raise ValueError(
                f"Mode {self.mode}: market_neutral mode requires hedge_allocation in component_config.strategy_manager.position_calculation or venues with perpetual instruments"
            )

        # NEW: Margin currency validation
        if self.margin_currency:
            # For ML directional strategies, margin_currency should match share_class for consistency
            if "ml_" in self.mode.lower() and "directional" in self.mode.lower():
                if self.margin_currency != self.share_class:
                    # Allow this but log a warning for clarity
                    logger.warning(
                        f"Mode {self.mode}: ML directional strategy has margin_currency '{self.margin_currency}' different from share_class '{self.share_class}'"
                    )

            # For basis trading, margin_currency should typically be USDT
            if self.basis_trade_enabled and self.margin_currency != "USDT":
                logger.warning(
                    f"Mode {self.mode}: Basis trading typically uses USDT margin, but margin_currency is '{self.margin_currency}'"
                )

        return self


class RiskMonitorConfig(BaseModel):
    """Risk monitor configuration model."""

    enabled_risk_types: List[str] = Field(..., description="Enabled risk types")
    risk_limits: Dict[str, Any] = Field(..., description="Risk limits configuration")

    # Additional fields used in YAML files
    target_margin_ratio: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Target margin ratio"
    )
    cex_margin_ratio_min: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Minimum CEX margin ratio"
    )
    maintenance_margin_requirement: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Maintenance margin requirement"
    )
    delta_tolerance: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Delta tolerance threshold"
    )
    liquidation_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Liquidation threshold"
    )


class ExposureMonitorConfig(BaseModel):
    """Exposure monitor configuration model."""

    pass


class PnLMonitorConfig(BaseModel):
    """PnL Monitor configuration model."""

    attribution_types: List[str] = Field(..., description="PnL attribution types")
    reporting_currency: str = Field(..., description="PnL reporting currency")
    reconciliation_tolerance: float = Field(..., ge=0.0, description="Reconciliation tolerance")


class StrategyManagerConfig(BaseModel):
    """Strategy manager configuration model."""

    strategy_type: str = Field(..., description="Strategy type")
    actions: List[str] = Field(..., description="Available actions")
    rebalancing_triggers: List[str] = Field(..., description="Rebalancing triggers")
    position_calculation: Dict[str, Any] = Field(..., description="Position calculation config")

    # Additional fields used in YAML files
    target_position: Optional[str] = Field(None, description="Target position type")
    hedge_position: Optional[str] = Field(None, description="Hedge position type")
    method: Optional[str] = Field(None, description="Position calculation method")
    leverage_ratio: Optional[float] = Field(
        None, ge=0.0, description="Leverage ratio for positions"
    )
    hedge_allocation: Optional[Dict[str, float]] = Field(
        None, description="Hedge allocation mapping"
    )


class ExecutionManagerConfig(BaseModel):
    """Execution manager configuration model.

    Note: Configuration for ExecutionManager component.
    ExecutionManager uses tight loop architecture and processes orders sequentially.
    It receives orders from StrategyManager and executes them via VenueInterfaceManager.
    The following fields are deprecated and maintained for backward compatibility only.
    """

    # Deprecated fields (maintained for backward compatibility)
    supported_actions: Optional[List[str]] = Field(
        None,
        description="[DEPRECATED] Supported venue actions - not used in tight loop architecture",
    )
    entry_full: Optional[List[str]] = Field(None, description="[DEPRECATED] Actions for full entry")
    exit_full: Optional[List[str]] = Field(None, description="[DEPRECATED] Actions for full exit")
    entry_partial: Optional[List[str]] = Field(
        None, description="[DEPRECATED] Actions for partial entry"
    )
    exit_partial: Optional[List[str]] = Field(
        None, description="[DEPRECATED] Actions for partial exit"
    )
    open_perp_short: Optional[List[str]] = Field(
        None, description="[DEPRECATED] Actions for opening perp short"
    )
    open_perp_long: Optional[List[str]] = Field(
        None, description="[DEPRECATED] Actions for opening perp long"
    )

    # Additional execution manager fields
    tight_loop_timeout: Optional[int] = Field(
        None, ge=1, description="Tight loop timeout in seconds"
    )


class ResultsStoreConfig(BaseModel):
    """Results store configuration model."""

    result_types: List[str] = Field(..., description="Result types to store")
    balance_sheet_assets: List[str] = Field(..., description="Balance sheet assets")
    pnl_attribution_types: List[str] = Field(..., description="PnL attribution types")
    leverage_tracking: Optional[bool] = Field(None, description="Whether to track leverage")
    dust_tracking_tokens: Optional[List[str]] = Field(None, description="Dust tracking tokens")

    # Additional fields used in YAML files
    delta_tracking_assets: Optional[List[str]] = Field(
        None, description="Assets for delta tracking"
    )
    funding_tracking_venues: Optional[List[str]] = Field(
        None, description="Venues for funding tracking"
    )


class StrategyFactoryConfig(BaseModel):
    """Strategy factory configuration model."""

    timeout: int = Field(..., ge=1, description="Timeout in seconds")
    max_retries: int = Field(..., ge=0, description="Maximum retry attempts")
    validation_strict: bool = Field(..., description="Whether to use strict validation")


class VenueConfig(BaseModel):
    """Venue configuration model."""

    model_config = {"extra": "allow"}  # Allow extra fields for flexibility

    # Core identification
    venue: str = Field(..., description="Venue name")
    type: VenueType = Field(..., description="Venue type")
    description: Optional[str] = Field(None, description="Venue description")
    version: Optional[str] = Field(None, description="Venue API version")
    enabled: Optional[bool] = Field(None, description="Whether venue is enabled")

    # Network configuration
    network: Optional[str] = Field(None, description="Network name")
    service: Optional[str] = Field(None, description="Service type for infrastructure venues")

    # Trading parameters (venue-specific, loaded from data provider)
    min_trade_size_usd: Optional[float] = Field(
        None, ge=0.0, description="Minimum trade size in USD"
    )
    max_trade_size_usd: Optional[float] = Field(
        None, ge=0.0, description="Maximum trade size in USD"
    )
    min_order_size_usd: Optional[float] = Field(
        None, ge=0.0, description="Minimum order size in USD"
    )
    max_slippage_bps: Optional[int] = Field(
        None, ge=0, le=10000, description="Maximum slippage in basis points"
    )

    # Trading fees
    trading_fees: Optional[Dict[str, float]] = Field(None, description="Trading fees (maker/taker)")

    # Risk parameters (loaded from data provider)
    max_leverage: Optional[float] = Field(None, ge=1.0, description="Maximum leverage")

    # Staking parameters
    min_stake_amount: Optional[float] = Field(None, ge=0.0, description="Minimum stake amount")
    unstaking_period: Optional[int] = Field(None, ge=0, description="Unstaking period in seconds")

    # Instrument configuration
    canonical_instruments: Optional[List[str]] = Field(
        None, description="Canonical instruments for this venue"
    )
    max_gas_limit: Optional[int] = Field(None, ge=0, description="Maximum gas limit")
    max_deadline_seconds: Optional[int] = Field(
        None, ge=0, description="Maximum deadline in seconds"
    )

    # API configuration
    api_contract: Optional[Dict[str, Any]] = Field(None, description="API contract specification")
    auth: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    endpoints: Optional[Dict[str, Any]] = Field(None, description="API endpoints configuration")
    validation: Optional[Dict[str, Any]] = Field(None, description="Validation configuration")

    # Protocol and symbol support
    protocols: Optional[List[str]] = Field(None, description="Supported protocols")
    supported_operations: Optional[List[str]] = Field(None, description="Supported operations")
    supported_symbols: Optional[List[str]] = Field(None, description="Supported trading symbols")

    # Examples and documentation
    example: Optional[Dict[str, Any]] = Field(None, description="Example requests and responses")

    # Required venue fields (used in YAML configs - note: YAML uses 'type' not 'venue_type')
    type: str = Field(..., description="Venue type (cex, defi, infrastructure)")
    venue_type: Optional[str] = Field(
        None, description="Venue type (cex, defi, infrastructure) - alias for type"
    )

    # Optional venue fields (used in YAML configs)
    instruments: Optional[List[str]] = Field(
        None, description="Trading instruments available on venue"
    )
    order_types: Optional[List[str]] = Field(None, description="Supported order types on venue")
    min_amount: Optional[float] = Field(None, ge=0.0, description="Minimum trade amount for venue")

    # Additional venue-specific fields
    request_format: Optional[Dict[str, Any]] = Field(
        None, description="Request format specification"
    )
    response_format: Optional[Dict[str, Any]] = Field(
        None, description="Response format specification"
    )
    valid_signals: Optional[List[str]] = Field(None, description="Valid signal types")
    require_confidence_score: Optional[bool] = Field(
        None, description="Whether confidence score is required"
    )
    min_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )

    @field_validator("venue")
    @classmethod
    def validate_venue_name(cls, v):
        """Validate venue name."""
        valid_venues = [
            "binance",
            "bybit",
            "okx",
            "aave_v3",
            "etherfi",
            "lido",
            "morpho",
            "alchemy",
            "instadapp",
            "ml_inference_api",
            "uniswap",
        ]
        if v not in valid_venues:
            raise ValueError(f"venue must be one of {valid_venues}, got: {v}")
        return v


class ShareClassConfig(BaseModel):
    """Share class configuration model."""

    model_config = {"extra": "allow"}  # Allow extra fields for flexibility

    # Core identification
    share_class: str = Field(..., description="Share class name")
    type: ShareClassType = Field(..., description="Share class type")
    description: Optional[str] = Field(None, description="Share class description")

    # Currency configuration
    quote_currency: Optional[str] = Field(None, description="Quote currency")
    decimal_places: Optional[int] = Field(
        None, ge=0, le=18, description="Decimal places for precision"
    )

    # Risk profile
    risk_level: Optional[str] = Field(None, description="Risk level (low, medium, high)")
    market_neutral: Optional[bool] = Field(
        None, description="Whether market neutral strategies are supported"
    )
    allows_hedging: Optional[bool] = Field(None, description="Whether hedging is allowed")

    # Strategy support
    supported_strategies: List[str] = Field(..., description="Supported strategy modes")
    leverage_supported: Optional[bool] = Field(None, description="Whether leverage is supported")
    leverage_enabled: Optional[bool] = Field(None, description="Whether leverage is enabled")
    staking_supported: Optional[bool] = Field(None, description="Whether staking is supported")
    basis_trading_supported: Optional[bool] = Field(
        None, description="Whether basis trading is supported"
    )

    # Risk parameters
    max_leverage: Optional[float] = Field(None, ge=1.0, description="Maximum leverage")

    # Performance targets
    target_apy_range: Optional[Dict[str, float]] = Field(None, description="Target APY range")
    max_drawdown: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Maximum drawdown limit"
    )

    @field_validator("share_class")
    @classmethod
    def validate_share_class_name(cls, v):
        """Validate share class name."""
        if v not in ["USDT", "ETH", "BTC"]:
            raise ValueError(f"share_class must be 'USDT', 'ETH', or 'BTC', got: {v}")
        return v

    @field_validator("supported_strategies")
    @classmethod
    def validate_supported_strategies(cls, v):
        """Validate supported strategies."""
        valid_strategies = [
            "pure_lending_usdt",
            "pure_lending_eth",
            "btc_basis",
            "eth_basis",
            "eth_leveraged",
            "eth_staking_only",
            "usdt_eth_staking_hedged_leveraged",
            "usdt_eth_staking_hedged_simple",
            "ml_btc_directional_usdt_margin",
            "ml_btc_directional_btc_margin",
        ]
        for strategy in v:
            if strategy not in valid_strategies:
                raise ValueError(f"supported_strategies contains invalid strategy: {strategy}")
        return v

    @field_validator("target_apy_range")
    @classmethod
    def validate_target_apy_range(cls, v):
        """Validate target APY range."""
        if v is None:
            return v
        if "min" not in v or "max" not in v:
            raise ValueError("target_apy_range must contain 'min' and 'max' keys")
        if v["min"] >= v["max"]:
            raise ValueError("target_apy_range min must be less than max")
        if v["min"] < 0 or v["max"] < 0:
            raise ValueError("target_apy_range values must be non-negative")
        return v


class ConfigurationSet(BaseModel):
    """Complete configuration set model."""

    modes: Dict[str, ModeConfig] = Field(..., description="Mode configurations")
    venues: Dict[str, VenueConfig] = Field(..., description="Venue configurations")
    share_classes: Dict[str, ShareClassConfig] = Field(
        ..., description="Share class configurations"
    )

    @model_validator(mode="after")
    def validate_cross_references(self):
        """Validate cross-references between configurations."""
        # Validate mode-share class compatibility
        for mode_name, mode_config in self.modes.items():
            share_class_name = mode_config.share_class

            # Find matching share class config
            share_class_config = None
            for sc_name, sc_config in self.share_classes.items():
                if sc_config.share_class == share_class_name:
                    share_class_config = sc_config
                    break

            if not share_class_config:
                raise ValueError(
                    f"Mode {mode_name}: Share class '{share_class_name}' not found in share class configs"
                )

            # Check if mode is supported by share class
            if mode_name not in share_class_config.supported_strategies:
                raise ValueError(
                    f"Mode {mode_name}: Strategy not supported by share class '{share_class_name}'. Supported strategies: {share_class_config.supported_strategies}"
                )

            # Validate leverage compatibility
            if mode_config.leverage_enabled and not share_class_config.leverage_enabled:
                raise ValueError(
                    f"Mode {mode_name}: Leverage enabled but share class '{share_class_name}' does not support leverage"
                )

            # Asset currency compatibility is now validated through component_config.risk_monitor.delta_tracking_asset
            # This ensures proper config-driven architecture and separation of concerns

        return self


class ConfigurationValidationError(Exception):
    """Configuration validation error."""

    pass


def validate_mode_config(config_dict: Dict[str, Any], mode_name: str) -> ModeConfig:
    """
    Validate and create ModeConfig from dictionary.

    Args:
        config_dict: Configuration dictionary
        mode_name: Mode name for error reporting

    Returns:
        Validated ModeConfig

    Raises:
        ConfigurationValidationError: If validation fails
    """
    try:
        return ModeConfig(**config_dict)
    except Exception as e:
        raise ConfigurationValidationError(f"Mode {mode_name} validation failed: {e}")


def validate_venue_config(config_dict: Dict[str, Any], venue_name: str) -> VenueConfig:
    """
    Validate and create VenueConfig from dictionary.

    Args:
        config_dict: Configuration dictionary
        venue_name: Venue name for error reporting

    Returns:
        Validated VenueConfig

    Raises:
        ConfigurationValidationError: If validation fails
    """
    try:
        return VenueConfig(**config_dict)
    except Exception as e:
        raise ConfigurationValidationError(f"Venue {venue_name} validation failed: {e}")


def validate_share_class_config(
    config_dict: Dict[str, Any], share_class_name: str
) -> ShareClassConfig:
    """
    Validate and create ShareClassConfig from dictionary.

    Args:
        config_dict: Configuration dictionary
        share_class_name: Share class name for error reporting

    Returns:
        Validated ShareClassConfig

    Raises:
        ConfigurationValidationError: If validation fails
    """
    try:
        return ShareClassConfig(**config_dict)
    except Exception as e:
        raise ConfigurationValidationError(f"Share class {share_class_name} validation failed: {e}")


def validate_complete_configuration(
    modes: Dict[str, Dict[str, Any]],
    venues: Dict[str, Dict[str, Any]],
    share_classes: Dict[str, Dict[str, Any]],
) -> ConfigurationSet:
    """
    Validate complete configuration set.

    Args:
        modes: Mode configuration dictionaries
        venues: Venue configuration dictionaries
        share_classes: Share class configuration dictionaries

    Returns:
        Validated ConfigurationSet

    Raises:
        ConfigurationValidationError: If validation fails
    """
    try:
        # Convert dictionaries to Pydantic models
        validated_modes = {}
        for mode_name, mode_dict in modes.items():
            validated_modes[mode_name] = validate_mode_config(mode_dict, mode_name)

        validated_venues = {}
        for venue_name, venue_dict in venues.items():
            validated_venues[venue_name] = validate_venue_config(venue_dict, venue_name)

        validated_share_classes = {}
        for share_class_name, share_class_dict in share_classes.items():
            validated_share_classes[share_class_name] = validate_share_class_config(
                share_class_dict, share_class_name
            )

        # Create and validate complete configuration set
        return ConfigurationSet(
            modes=validated_modes, venues=validated_venues, share_classes=validated_share_classes
        )

    except Exception as e:
        raise ConfigurationValidationError(f"Complete configuration validation failed: {e}")
