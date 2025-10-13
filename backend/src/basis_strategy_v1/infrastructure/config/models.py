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
    enable_market_impact: Optional[bool] = Field(None, description="Whether market impact is enabled")
    
    # Asset configuration
    share_class: str = Field(..., description="Share class (USDT or ETH)")
    asset: str = Field(..., description="Primary asset")
    lst_type: Optional[str] = Field(None, description="LST type if applicable")
    rewards_mode: Optional[str] = Field(None, description="Rewards mode")
    position_deviation_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Position deviation threshold")
    
    # Risk parameters
    margin_ratio_target: Optional[float] = Field(None, ge=0.0, description="Margin ratio target")
    target_apy: Optional[float] = Field(None, ge=0.0, description="Target APY")
    max_drawdown: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maximum drawdown")
    
    # Execution parameters
    time_throttle_interval: Optional[int] = Field(None, ge=1, description="Time throttle interval in seconds")
    
    # Data requirements
    data_requirements: List[str] = Field(..., description="Required data types")
    
    # Optional fields for specific strategies
    leverage_enabled: Optional[bool] = Field(None, description="Whether leverage is enabled")
    max_ltv: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maximum loan-to-value ratio")
    liquidation_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Liquidation threshold")
    max_stake_spread_move: Optional[float] = Field(None, ge=0.0, description="Maximum stake spread move")
    
    # Venue configuration
    venues: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Venue configuration with instruments and order types")
    
    # Hedge configuration
    hedge_venues: Optional[List[str]] = Field(None, description="Hedge venues")
    hedge_allocation: Optional[Dict[str, float]] = Field(None, description="Hedge allocation percentages")
    
    # Individual hedge allocation fields (for backward compatibility)
    hedge_allocation_binance: Optional[float] = Field(None, ge=0.0, le=1.0, description="Binance hedge allocation")
    hedge_allocation_bybit: Optional[float] = Field(None, ge=0.0, le=1.0, description="Bybit hedge allocation")
    hedge_allocation_okx: Optional[float] = Field(None, ge=0.0, le=1.0, description="OKX hedge allocation")
    
    # Component configuration
    component_config: Optional[Dict[str, Any]] = Field(None, description="Component-specific configuration")
    
    # Additional fields used in YAML files but not in current model
    hedge_allocation: Optional[Dict[str, float]] = Field(None, description="Hedge allocation mapping")
    
    # ML-specific configuration
    ml_config: Optional[Dict[str, Any]] = Field(None, description="ML model configuration")
    
    # ML config subfields (for validation)
    ml_model_name: Optional[str] = Field(None, description="ML model name")
    ml_model_version: Optional[str] = Field(None, description="ML model version")
    ml_signal_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="ML signal threshold")
    ml_max_position_size: Optional[float] = Field(None, ge=0.0, le=1.0, description="ML maximum position size")
    ml_confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="ML confidence threshold")
    ml_retraining_frequency: Optional[str] = Field(None, description="ML retraining frequency")
    ml_feature_importance_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="ML feature importance threshold")
    
    # Event logger configuration
    event_logger: Optional[Dict[str, Any]] = Field(None, description="Event logger configuration")
    
    # Strategy-specific parameters
    delta_tolerance: Optional[float] = Field(None, ge=0.0, le=1.0, description="Delta neutrality tolerance")
    dust_delta: Optional[float] = Field(None, ge=0.0, le=1.0, description="Dust delta threshold for small positions")
    stake_allocation_eth: Optional[float] = Field(None, ge=0.0, le=1.0, description="ETH stake allocation percentage")
    funding_threshold: Optional[float] = Field(None, ge=0.0, description="Funding rate threshold for basis trading")
    
    @field_validator('share_class')
    @classmethod
    def validate_share_class(cls, v):
        """Validate share class is USDT or ETH."""
        if v not in ['USDT', 'ETH']:
            raise ValueError(f"share_class must be 'USDT' or 'ETH', got: {v}")
        return v
    
    @field_validator('asset')
    @classmethod
    def validate_asset(cls, v):
        """Validate asset is valid."""
        valid_assets = ['USDT', 'ETH', 'BTC', 'USDC']
        if v not in valid_assets:
            raise ValueError(f"asset must be one of {valid_assets}, got: {v}")
        return v
    
    @field_validator('rewards_mode')
    @classmethod
    def validate_rewards_mode(cls, v):
        """Validate rewards mode."""
        valid_modes = ['base_only', 'base_eigen', 'base_eigen_seasonal']
        if v not in valid_modes:
            raise ValueError(f"rewards_mode must be one of {valid_modes}, got: {v}")
        return v
    
    @model_validator(mode='after')
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
            expected_venue = "etherfi" if self.lst_type == "weeth" else "lido" if self.lst_type == "wsteth" else None
            if expected_venue and expected_venue not in self.venues:
                raise ValueError(f"Mode {self.mode}: lst_type '{self.lst_type}' requires venue '{expected_venue}' in venues config")
        
        # Borrowing requires max_ltv
        if self.borrowing_enabled and not self.max_ltv:
            raise ValueError(f"Mode {self.mode}: borrowing_enabled requires max_ltv")
        
        # Validate hedge configuration
        if self.hedge_venues and not self.hedge_allocation and not any([self.hedge_allocation_binance, self.hedge_allocation_bybit, self.hedge_allocation_okx]):
            raise ValueError(f"Mode {self.mode}: hedge_venues specified but no hedge_allocation or individual allocation fields")
        
        if (self.hedge_allocation or any([self.hedge_allocation_binance, self.hedge_allocation_bybit, self.hedge_allocation_okx])) and not self.hedge_venues:
            raise ValueError(f"Mode {self.mode}: hedge allocation specified but no hedge_venues")
        
        # Check hedge allocation sums to 1.0
        if self.hedge_allocation:
            total_allocation = sum(self.hedge_allocation.values())
            if abs(total_allocation - 1.0) > 0.01:
                raise ValueError(f"Mode {self.mode}: hedge_allocation sums to {total_allocation}, expected 1.0")
        
        # Check individual allocation fields sum to 1.0
        individual_allocations = [self.hedge_allocation_binance, self.hedge_allocation_bybit, self.hedge_allocation_okx]
        if any(individual_allocations):
            total_individual = sum(a for a in individual_allocations if a is not None)
            if abs(total_individual - 1.0) > 0.01:
                raise ValueError(f"Mode {self.mode}: individual hedge allocations sum to {total_individual}, expected 1.0")
        
        # NEW: Venue-LST validation
        if self.staking_enabled and self.lst_type and self.venues:
            expected_venue = "etherfi" if self.lst_type == "weeth" else "lido" if self.lst_type == "wsteth" else None
            if expected_venue and expected_venue not in self.venues:
                raise ValueError(f"Mode {self.mode}: lst_type '{self.lst_type}' requires venue '{expected_venue}' in venues config")
        
        # NEW: Share class consistency validation (config-driven)
        # Load share class configuration to validate asset compatibility
        try:
            import yaml
            from pathlib import Path
            
            # Load share class config
            share_class_file = Path(__file__).parent.parent.parent.parent.parent / "configs" / "share_classes" / f"{self.share_class.lower()}_stable.yaml"
            if not share_class_file.exists():
                share_class_file = Path(__file__).parent.parent.parent.parent.parent / "configs" / "share_classes" / f"{self.share_class.lower()}_directional.yaml"
            
            if share_class_file.exists():
                with open(share_class_file, 'r') as f:
                    share_class_config = yaml.safe_load(f)
                
                market_neutral = share_class_config.get('market_neutral', False)
                
                # Market neutral share classes can trade different assets (for hedging)
                # Directional share classes should trade the same asset as share class
                if not market_neutral and self.share_class != self.asset:
                    raise ValueError(f"Mode {self.mode}: Directional share class '{self.share_class}' should trade same asset '{self.share_class}', not '{self.asset}'")
                
                # Market neutral share classes can trade different assets
                # USDT share class can trade USDT, ETH, BTC for market neutral strategies
                # ETH share class can trade ETH, BTC for market neutral strategies
                if market_neutral:
                    if self.share_class == 'USDT' and self.asset not in ['USDT', 'ETH', 'BTC']:
                        raise ValueError(f"Mode {self.mode}: USDT market neutral share class should trade USDT, ETH, or BTC, not {self.asset}")
                    elif self.share_class == 'ETH' and self.asset not in ['ETH', 'BTC']:
                        raise ValueError(f"Mode {self.mode}: ETH market neutral share class should trade ETH or BTC, not {self.asset}")
                        
        except Exception as e:
            # If share class config loading fails, log warning but don't fail validation
            logger.warning(f"Could not load share class config for validation: {e}")
        
        # NEW: Risk parameter alignment
        if self.max_drawdown and self.max_drawdown > 0.5:
            logger.warning(f"Mode {self.mode}: High max_drawdown {self.max_drawdown} (>50%)")
        
        if self.target_apy and self.target_apy > 100:
            logger.warning(f"Mode {self.mode}: Very high target_apy {self.target_apy}% (>100%)")
        
        # NEW: Basis trading validation
        if self.basis_trade_enabled and not self.hedge_venues:
            raise ValueError(f"Mode {self.mode}: basis_trade_enabled requires hedge_venues")
        
        # NEW: Market neutral validation
        if 'market_neutral' in self.mode.lower() and not self.hedge_venues:
            raise ValueError(f"Mode {self.mode}: market_neutral mode requires hedge_venues")
        
        return self


class RiskMonitorConfig(BaseModel):
    """Risk monitor configuration model."""
    
    enabled_risk_types: List[str] = Field(..., description="Enabled risk types")
    risk_limits: Dict[str, Any] = Field(..., description="Risk limits configuration")
    
    # Additional fields used in YAML files
    target_margin_ratio: Optional[float] = Field(None, ge=0.0, le=1.0, description="Target margin ratio")
    cex_margin_ratio_min: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum CEX margin ratio")
    maintenance_margin_requirement: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maintenance margin requirement")
    delta_tolerance: Optional[float] = Field(None, ge=0.0, le=1.0, description="Delta tolerance threshold")
    liquidation_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Liquidation threshold")


class ExposureMonitorConfig(BaseModel):
    """Exposure monitor configuration model."""
    
    exposure_currency: str = Field(..., description="Exposure reporting currency")
    track_assets: List[str] = Field(..., description="Assets to track")
    conversion_methods: Dict[str, str] = Field(..., description="Asset conversion methods")
    
    # Additional fields used in YAML files
    USDT: Optional[str] = Field(None, description="USDT conversion method")
    aWeETH: Optional[str] = Field(None, description="aWeETH conversion method")
    EIGEN: Optional[str] = Field(None, description="EIGEN conversion method")
    weETH: Optional[str] = Field(None, description="weETH conversion method")
    variableDebtWETH: Optional[str] = Field(None, description="variableDebtWETH conversion method")


class PnLCalculatorConfig(BaseModel):
    """PnL calculator configuration model."""
    
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
    leverage_ratio: Optional[float] = Field(None, ge=0.0, description="Leverage ratio for positions")
    hedge_allocation: Optional[Dict[str, float]] = Field(None, description="Hedge allocation mapping")


class VenueManagerConfig(BaseModel):
    """Venue manager configuration model."""
    
    supported_actions: List[str] = Field(..., description="Supported venue actions")
    action_mapping: Dict[str, List[str]] = Field(..., description="Action to venue mapping")
    
    # Additional fields used in YAML files
    entry_full: Optional[List[str]] = Field(None, description="Actions for full entry")
    exit_full: Optional[List[str]] = Field(None, description="Actions for full exit")
    entry_partial: Optional[List[str]] = Field(None, description="Actions for partial entry")
    exit_partial: Optional[List[str]] = Field(None, description="Actions for partial exit")
    open_perp_short: Optional[List[str]] = Field(None, description="Actions for opening perp short")
    open_perp_long: Optional[List[str]] = Field(None, description="Actions for opening perp long")


class ResultsStoreConfig(BaseModel):
    """Results store configuration model."""
    
    result_types: List[str] = Field(..., description="Result types to store")
    balance_sheet_assets: List[str] = Field(..., description="Balance sheet assets")
    pnl_attribution_types: List[str] = Field(..., description="PnL attribution types")
    leverage_tracking: Optional[bool] = Field(None, description="Whether to track leverage")
    dust_tracking_tokens: Optional[List[str]] = Field(None, description="Dust tracking tokens")
    
    # Additional fields used in YAML files
    delta_tracking_assets: Optional[List[str]] = Field(None, description="Assets for delta tracking")
    funding_tracking_venues: Optional[List[str]] = Field(None, description="Venues for funding tracking")


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
    min_trade_size_usd: Optional[float] = Field(None, ge=0.0, description="Minimum trade size in USD")
    max_trade_size_usd: Optional[float] = Field(None, ge=0.0, description="Maximum trade size in USD")
    min_order_size_usd: Optional[float] = Field(None, ge=0.0, description="Minimum order size in USD")
    max_slippage_bps: Optional[int] = Field(None, ge=0, le=10000, description="Maximum slippage in basis points")
    
    # Trading fees
    trading_fees: Optional[Dict[str, float]] = Field(None, description="Trading fees (maker/taker)")
    
    # Risk parameters (loaded from data provider)
    max_leverage: Optional[float] = Field(None, ge=1.0, description="Maximum leverage")
    
    # Staking parameters
    min_stake_amount: Optional[float] = Field(None, ge=0.0, description="Minimum stake amount")
    unstaking_period: Optional[int] = Field(None, ge=0, description="Unstaking period in seconds")
    max_gas_limit: Optional[int] = Field(None, ge=0, description="Maximum gas limit")
    max_deadline_seconds: Optional[int] = Field(None, ge=0, description="Maximum deadline in seconds")
    
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
    
    # Additional fields used in YAML files but not in current model
    venue_type: Optional[str] = Field(None, description="Venue type (cex, defi, infrastructure)")
    instruments: Optional[List[str]] = Field(None, description="Trading instruments available on venue")
    order_types: Optional[List[str]] = Field(None, description="Supported order types on venue")
    min_amount: Optional[float] = Field(None, ge=0.0, description="Minimum trade amount for venue")
    
    # Additional venue-specific fields
    request_format: Optional[Dict[str, Any]] = Field(None, description="Request format specification")
    response_format: Optional[Dict[str, Any]] = Field(None, description="Response format specification")
    valid_signals: Optional[List[str]] = Field(None, description="Valid signal types")
    require_confidence_score: Optional[bool] = Field(None, description="Whether confidence score is required")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum confidence threshold")
    
    @field_validator('venue')
    @classmethod
    def validate_venue_name(cls, v):
        """Validate venue name."""
        valid_venues = [
            'binance', 'bybit', 'okx', 'aave_v3', 'etherfi', 'lido', 
            'morpho', 'alchemy', 'instadapp', 'ml_inference_api', 'uniswap'
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
    base_currency: BaseCurrency = Field(..., description="Base currency")
    description: Optional[str] = Field(None, description="Share class description")
    
    # Currency configuration
    quote_currency: Optional[str] = Field(None, description="Quote currency")
    decimal_places: Optional[int] = Field(None, ge=0, le=18, description="Decimal places for precision")
    
    # Risk profile
    risk_level: Optional[str] = Field(None, description="Risk level (low, medium, high)")
    market_neutral: Optional[bool] = Field(None, description="Whether market neutral strategies are supported")
    allows_hedging: Optional[bool] = Field(None, description="Whether hedging is allowed")
    
    # Strategy support
    supported_strategies: List[str] = Field(..., description="Supported strategy modes")
    leverage_supported: bool = Field(..., description="Whether leverage is supported")
    staking_supported: Optional[bool] = Field(None, description="Whether staking is supported")
    basis_trading_supported: Optional[bool] = Field(None, description="Whether basis trading is supported")
    
    # Risk parameters
    max_leverage: Optional[float] = Field(None, ge=1.0, description="Maximum leverage")
    
    # Performance targets
    target_apy_range: Optional[Dict[str, float]] = Field(None, description="Target APY range")
    max_drawdown: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maximum drawdown limit")
    
    @field_validator('share_class')
    @classmethod
    def validate_share_class_name(cls, v):
        """Validate share class name."""
        if v not in ['USDT', 'ETH']:
            raise ValueError(f"share_class must be 'USDT' or 'ETH', got: {v}")
        return v
    
    @field_validator('supported_strategies')
    @classmethod
    def validate_supported_strategies(cls, v):
        """Validate supported strategies."""
        valid_strategies = [
            'pure_lending', 'btc_basis', 'eth_basis', 'eth_leveraged',
            'eth_staking_only', 'usdt_market_neutral', 'usdt_market_neutral_no_leverage',
            'ml_btc_directional', 'ml_usdt_directional'
        ]
        for strategy in v:
            if strategy not in valid_strategies:
                raise ValueError(f"supported_strategies contains invalid strategy: {strategy}")
        return v
    
    @field_validator('target_apy_range')
    @classmethod
    def validate_target_apy_range(cls, v):
        """Validate target APY range."""
        if v is None:
            return v
        if 'min' not in v or 'max' not in v:
            raise ValueError("target_apy_range must contain 'min' and 'max' keys")
        if v['min'] >= v['max']:
            raise ValueError("target_apy_range min must be less than max")
        if v['min'] < 0 or v['max'] < 0:
            raise ValueError("target_apy_range values must be non-negative")
        return v


class ConfigurationSet(BaseModel):
    """Complete configuration set model."""
    
    modes: Dict[str, ModeConfig] = Field(..., description="Mode configurations")
    venues: Dict[str, VenueConfig] = Field(..., description="Venue configurations")
    share_classes: Dict[str, ShareClassConfig] = Field(..., description="Share class configurations")
    
    @model_validator(mode='after')
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
                raise ValueError(f"Mode {mode_name}: Share class '{share_class_name}' not found in share class configs")
            
            # Check if mode is supported by share class
            if mode_name not in share_class_config.supported_strategies:
                raise ValueError(f"Mode {mode_name}: Strategy not supported by share class '{share_class_name}'. Supported strategies: {share_class_config.supported_strategies}")
            
            # Validate leverage compatibility
            if mode_config.leverage_enabled and not share_class_config.leverage_supported:
                raise ValueError(f"Mode {mode_name}: Leverage enabled but share class '{share_class_name}' does not support leverage")
            
            # Validate base currency compatibility
            mode_asset = mode_config.asset
            share_class_currency = share_class_config.base_currency
            
            if 'usdt' in mode_name.lower() and share_class_currency != 'USDT':
                raise ValueError(f"Mode {mode_name}: USDT strategy should use USDT share class, not {share_class_currency}")
            
            if 'eth' in mode_name.lower() and share_class_currency != 'ETH':
                raise ValueError(f"Mode {mode_name}: ETH strategy should use ETH share class, not {share_class_currency}")
        
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


def validate_share_class_config(config_dict: Dict[str, Any], share_class_name: str) -> ShareClassConfig:
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
    share_classes: Dict[str, Dict[str, Any]]
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
            validated_share_classes[share_class_name] = validate_share_class_config(share_class_dict, share_class_name)
        
        # Create and validate complete configuration set
        return ConfigurationSet(
            modes=validated_modes,
            venues=validated_venues,
            share_classes=validated_share_classes
        )
    
    except Exception as e:
        raise ConfigurationValidationError(f"Complete configuration validation failed: {e}")
