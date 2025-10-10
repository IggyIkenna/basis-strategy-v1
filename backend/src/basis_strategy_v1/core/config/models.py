"""
Pydantic Models for Configuration Validation

Defines Pydantic models for all configuration types to ensure
type safety, validation, and fail-fast behavior.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 33 (Fail-Fast Configuration)
Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-040 (Fail-Fast Configuration)
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, validator, root_validator
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
    CEX = "CEX"
    DEFI = "DeFi"
    LST = "LST"
    RPC = "RPC"


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
    
    # Core identification
    mode: str = Field(..., description="Mode name")
    
    # Strategy flags
    lending_enabled: bool = Field(..., description="Whether lending is enabled")
    staking_enabled: bool = Field(..., description="Whether staking is enabled")
    basis_trade_enabled: bool = Field(..., description="Whether basis trading is enabled")
    borrowing_enabled: bool = Field(..., description="Whether borrowing is enabled")
    enable_market_impact: bool = Field(..., description="Whether market impact is enabled")
    
    # Asset configuration
    share_class: str = Field(..., description="Share class (USDT or ETH)")
    asset: str = Field(..., description="Primary asset")
    lst_type: Optional[str] = Field(None, description="LST type if applicable")
    rewards_mode: str = Field(..., description="Rewards mode")
    reserve_ratio: float = Field(..., ge=0.0, le=1.0, description="Reserve ratio")
    position_deviation_threshold: float = Field(..., ge=0.0, le=1.0, description="Position deviation threshold")
    
    # Risk parameters
    margin_ratio_target: float = Field(..., ge=0.0, description="Margin ratio target")
    target_apy: float = Field(..., ge=0.0, description="Target APY")
    max_drawdown: float = Field(..., ge=0.0, le=1.0, description="Maximum drawdown")
    
    # Execution parameters
    time_throttle_interval: int = Field(..., ge=1, description="Time throttle interval in seconds")
    
    # Data requirements
    data_requirements: List[str] = Field(..., description="Required data types")
    
    # Optional fields for specific strategies
    leverage_enabled: Optional[bool] = Field(None, description="Whether leverage is enabled")
    max_ltv: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maximum loan-to-value ratio")
    liquidation_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Liquidation threshold")
    max_stake_spread_move: Optional[float] = Field(None, ge=0.0, description="Maximum stake spread move")
    
    # Hedge configuration
    hedge_venues: Optional[List[str]] = Field(None, description="Hedge venues")
    hedge_allocation: Optional[Dict[str, float]] = Field(None, description="Hedge allocation percentages")
    
    @validator('share_class')
    def validate_share_class(cls, v):
        """Validate share class is USDT or ETH."""
        if v not in ['USDT', 'ETH']:
            raise ValueError(f"share_class must be 'USDT' or 'ETH', got: {v}")
        return v
    
    @validator('asset')
    def validate_asset(cls, v):
        """Validate asset is valid."""
        valid_assets = ['USDT', 'ETH', 'BTC', 'USDC']
        if v not in valid_assets:
            raise ValueError(f"asset must be one of {valid_assets}, got: {v}")
        return v
    
    @validator('rewards_mode')
    def validate_rewards_mode(cls, v):
        """Validate rewards mode."""
        valid_modes = ['base_only', 'rewards_included', 'staking_rewards']
        if v not in valid_modes:
            raise ValueError(f"rewards_mode must be one of {valid_modes}, got: {v}")
        return v
    
    @root_validator
    def validate_business_logic(cls, values):
        """Validate business logic constraints."""
        mode = values.get('mode', '')
        share_class = values.get('share_class', '')
        basis_trade_enabled = values.get('basis_trade_enabled', False)
        leverage_enabled = values.get('leverage_enabled', False)
        borrowing_enabled = values.get('borrowing_enabled', False)
        
        # ETH share class cannot have basis trading enabled
        if share_class == 'ETH' and basis_trade_enabled:
            raise ValueError(f"Mode {mode}: basis_trade_enabled cannot be true for ETH share class (directional strategy)")
        
        # Leverage requires borrowing
        if leverage_enabled and not borrowing_enabled:
            raise ValueError(f"Mode {mode}: leverage_enabled requires borrowing_enabled")
        
        # Validate hedge configuration
        hedge_venues = values.get('hedge_venues', [])
        hedge_allocation = values.get('hedge_allocation', {})
        
        if hedge_venues and not hedge_allocation:
            raise ValueError(f"Mode {mode}: hedge_venues specified but no hedge_allocation")
        
        if hedge_allocation and not hedge_venues:
            raise ValueError(f"Mode {mode}: hedge_allocation specified but no hedge_venues")
        
        # Check hedge allocation sums to 1.0
        if hedge_allocation:
            total_allocation = sum(hedge_allocation.values())
            if abs(total_allocation - 1.0) > 0.01:
                raise ValueError(f"Mode {mode}: hedge_allocation sums to {total_allocation}, expected 1.0")
        
        return values


class VenueConfig(BaseModel):
    """Venue configuration model."""
    
    # Core identification
    venue: str = Field(..., description="Venue name")
    type: VenueType = Field(..., description="Venue type")
    
    # Optional configuration
    network: Optional[str] = Field(None, description="Network name")
    chain_id: Optional[int] = Field(None, ge=1, description="Chain ID")
    rpc_url: Optional[str] = Field(None, description="RPC URL")
    
    # Trading parameters
    min_trade_size: Optional[float] = Field(None, ge=0.0, description="Minimum trade size")
    max_trade_size: Optional[float] = Field(None, ge=0.0, description="Maximum trade size")
    trading_fee: Optional[float] = Field(None, ge=0.0, le=1.0, description="Trading fee percentage")
    
    # Risk parameters
    max_leverage: Optional[float] = Field(None, ge=1.0, description="Maximum leverage")
    liquidation_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Liquidation threshold")
    
    @validator('venue')
    def validate_venue_name(cls, v):
        """Validate venue name."""
        valid_venues = [
            'binance', 'bybit', 'okx', 'aave_v3', 'etherfi', 'lido', 
            'morpho', 'alchemy', 'compound', 'uniswap'
        ]
        if v not in valid_venues:
            raise ValueError(f"venue must be one of {valid_venues}, got: {v}")
        return v


class ShareClassConfig(BaseModel):
    """Share class configuration model."""
    
    # Core identification
    share_class: str = Field(..., description="Share class name")
    type: ShareClassType = Field(..., description="Share class type")
    base_currency: BaseCurrency = Field(..., description="Base currency")
    
    # Strategy support
    supported_strategies: List[str] = Field(..., description="Supported strategy modes")
    
    # Risk parameters
    leverage_supported: bool = Field(..., description="Whether leverage is supported")
    max_leverage: Optional[float] = Field(None, ge=1.0, description="Maximum leverage")
    
    # Performance targets
    target_apy_range: Dict[str, float] = Field(..., description="Target APY range")
    max_drawdown_limit: float = Field(..., ge=0.0, le=1.0, description="Maximum drawdown limit")
    
    @validator('share_class')
    def validate_share_class_name(cls, v):
        """Validate share class name."""
        if v not in ['USDT', 'ETH']:
            raise ValueError(f"share_class must be 'USDT' or 'ETH', got: {v}")
        return v
    
    @validator('supported_strategies')
    def validate_supported_strategies(cls, v):
        """Validate supported strategies."""
        valid_strategies = [
            'pure_lending', 'btc_basis', 'eth_basis', 'eth_leveraged',
            'eth_staking_only', 'usdt_market_neutral', 'usdt_market_neutral_no_leverage'
        ]
        for strategy in v:
            if strategy not in valid_strategies:
                raise ValueError(f"supported_strategies contains invalid strategy: {strategy}")
        return v
    
    @validator('target_apy_range')
    def validate_target_apy_range(cls, v):
        """Validate target APY range."""
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
    
    @root_validator
    def validate_cross_references(cls, values):
        """Validate cross-references between configurations."""
        modes = values.get('modes', {})
        venues = values.get('venues', {})
        share_classes = values.get('share_classes', {})
        
        # Validate mode-share class compatibility
        for mode_name, mode_config in modes.items():
            share_class_name = mode_config.share_class
            
            # Find matching share class config
            share_class_config = None
            for sc_name, sc_config in share_classes.items():
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
        
        return values


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
