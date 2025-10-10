"""Canonical Configuration Models - Venue-aware mathematical derivation.

TODO-REFACTOR: MODE-SPECIFIC LOGIC IN GENERIC COMPONENTS VIOLATION - See docs/REFERENCE_ARCHITECTURE_CANONICAL.md
ISSUE: This component may have mode-specific logic that should be generic:

1. GENERIC VS MODE-SPECIFIC REQUIREMENTS:
   - Components should be mode-agnostic where possible
   - Mode-specific logic should be isolated
   - Generic components should not contain strategy-specific code

2. REQUIRED VERIFICATION:
   - Check for mode-specific logic in generic configuration models
   - Ensure configuration models are truly generic
   - Isolate any mode-specific validation logic

3. CANONICAL SOURCE:
   - docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Generic vs Mode-Specific Architecture
   - Components must be mode-agnostic

This is the SINGLE SOURCE OF TRUTH for all configuration validation.
Features intelligent parameter derivation from venue constants + user risk tolerance.

Key Innovation: Instead of manually setting dozens of LTV/margin parameters,
users set 3 risk tolerance parameters and system mathematically derives
ALL operating parameters from actual venue liquidation thresholds.

Migration from: odum-basis-strategy-v1/src/config_schema.py (494 lines)
Enhanced with: Mathematical derivation, venue-aware calculations, massive simplification
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Dict, List, Optional, Any, Literal, Union
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)



# REMOVED: StakingVenue, StableCoin, S enums - not used in configs
# staking venue will be determined by lst_type in strategy config
# stablecoin handling is simplified


class BacktestConfig(BaseModel):
    """Minimal backtest configuration (runtime parameters removed)."""
    # Most backtest parameters are now runtime-only, not config parameters
    pass


class StrategyConfig(BaseModel):
    """Strategy configuration parameters with dependency validation"""
    
    # CORE IDENTITY (NEVER AUTO-CORRECT - User precedence hierarchy)
    share_class: Optional[str] = Field(default=None, description="Share class for strategy")
    
    # NEW MODE FIELDS (Component Architecture)
    mode: Optional[str] = Field(default=None, description="Strategy mode: pure_lending, btc_basis, eth_leveraged, usdt_market_neutral")
    asset: Optional[str] = Field(default=None, description="Primary asset: ETH or BTC")
    lst_type: Optional[str] = Field(default=None, description="Liquid staking token type: weeth or wsteth")
    rewards_mode: Optional[str] = Field(default=None, description="Rewards mode: base_only, base_eigen, base_eigen_seasonal")
    position_deviation_threshold: Optional[float] = Field(
        default=0.02, 
        ge=0.0, 
        le=1.0,
        description="Minimum deviation from target position to trigger rebalancing (fraction of target)"
    )
    hedge_venues: List[str] = Field(default=[], description="List of hedge venues: binance, bybit, okx")
    hedge_allocation: Dict[str, float] = Field(default={}, description="Hedge allocation per venue")
    
    # RISK PARAMETERS (eMode Configuration)
    max_ltv: Optional[float] = Field(default=None, description="Maximum LTV (eMode parameter)")
    liquidation_threshold: Optional[float] = Field(default=None, description="Liquidation threshold (eMode parameter)")
    margin_ratio_target: Optional[float] = Field(default=None, description="Target margin ratio for CEX positions")
    max_stake_spread_move: Optional[float] = Field(default=None, description="Max expected adverse weETH/ETH oracle move (for LTV buffer)")
    delta_tolerance: Optional[float] = Field(default=None, description="Delta neutrality tolerance (fraction of gross exposure)")
    
    # PERFORMANCE TARGETS (for frontend wizard and backtest validation)
    target_apy: Optional[float] = Field(default=None, description="Expected APY for frontend wizard guidance and backtest validation")
    max_drawdown: Optional[float] = Field(default=None, description="Expected max drawdown for risk validation and alert thresholds")
    
    # BASE OPERATIONS (Control derivative features - User precedence hierarchy)
    lending_enabled: Optional[bool] = Field(default=None, description="Enable LendingComponent")
    staking_enabled: Optional[bool] = Field(default=None, description="Enable StakingComponent") 
    basis_trade_enabled: Optional[bool] = Field(default=None, description="Enable BasisTradingComponent")
    borrowing_enabled: Optional[bool] = Field(default=None, description="Enable AAVE borrowing for leveraged staking")
    # REMOVED: leverage_enabled - not in any config files
    
    # DERIVATIVE FEATURES (Controlled by base operations - User precedence hierarchy)
    
    # ADVANCED FEATURES (Simplified)
    # REMOVED: market_neutral_required (auto-derived from share_class)
    # REMOVED: unified_platform_enabled, vip_otc_available (too complex for MVP)
    # REMOVED: initial_capital_strategy (auto-derived from parameter hierarchy)
    
    # REMOVED: Manual LTV parameters - now mathematically derived from venue constants + risk tolerance
    # All LTV limits are calculated from max_underlying_move, max_basis_move, max_staked_basis_move
    
    # EXECUTION CONFIGURATION
    enable_market_impact: bool = Field(default=True, description="Enable market impact simulation for trades")
    data_requirements: Optional[Dict[str, Any]] = Field(default=None, description="Data requirements for this strategy")
    
    # MONITORING CONFIGURATION (flattened fields from configs)
    max_drawdown: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Maximum allowed drawdown")
    monitoring_position_check_interval: Optional[int] = Field(default=None, description="Position check interval in seconds")
    monitoring_risk_check_interval: Optional[int] = Field(default=None, description="Risk check interval in seconds")
    
    # REMOVED: monitoring Dict field - flattened to individual fields
    
    # REMOVED: monitoring_alert_thresholds fields - not needed in config, calculated at runtime
    
    # ASSET CONFIGURATION
    lst_type: Optional[str] = Field(default=None, description="Liquid staking token type")
    
    # HEDGE ALLOCATION (flattened fields from configs)
    hedge_allocation_binance: Optional[float] = Field(default=None, description="Binance hedge allocation")
    hedge_allocation_bybit: Optional[float] = Field(default=None, description="Bybit hedge allocation")
    hedge_allocation_okx: Optional[float] = Field(default=None, description="OKX hedge allocation")
    
    # REMOVED: capital_allocation fields - not needed in config, calculated at runtime
    
    # MODE IDENTIFICATION
    mode: Optional[str] = Field(default=None, description="Strategy mode identifier")
    
    
    # REMOVED: Enhanced risk parameters that aren't in configs
    # max_underlying_move, max_spot_perp_basis_move, max_staked_basis_move, 
    # beta_basis_as_collateral, hf_target_after_shock, hf_drift_trigger_pct,
    # market_impact_threshold, max_acceptable_impact_bps, min_trade_amount_usd
    # These will be added back only if they appear in actual config files
    
    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: Optional[str]) -> Optional[str]:
        """Validate strategy mode."""
        if v is not None:
            valid_modes = ['pure_lending', 'btc_basis', 'eth_leveraged', 'usdt_market_neutral', 'eth_staking_only', 'usdt_market_neutral_no_leverage']
            if v not in valid_modes:
                raise ValueError(f"Invalid mode: {v}. Valid modes: {valid_modes}")
        return v
    
    @field_validator('asset')
    @classmethod
    def validate_asset(cls, v: Optional[str]) -> Optional[str]:
        """Validate primary asset."""
        if v is not None:
            valid_assets = ['ETH', 'BTC']
            if v.upper() not in valid_assets:
                raise ValueError(f"Invalid asset: {v}. Valid assets: {valid_assets}")
        return v.upper() if v else v
    
    @field_validator('lst_type')
    @classmethod
    def validate_lst_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate liquid staking token type."""
        if v is not None:
            valid_types = ['weeth', 'wsteth']
            if v.lower() not in valid_types:
                raise ValueError(f"Invalid lst_type: {v}. Valid types: {valid_types}")
        return v.lower() if v else v
    
    @field_validator('rewards_mode')
    @classmethod
    def validate_rewards_mode(cls, v: Optional[str]) -> Optional[str]:
        """Validate rewards mode."""
        if v is not None:
            valid_modes = ['base_only', 'base_eigen', 'base_eigen_seasonal']
            if v not in valid_modes:
                raise ValueError(f"Invalid rewards_mode: {v}. Valid modes: {valid_modes}")
        return v
    
    
    @field_validator('max_ltv', 'liquidation_threshold', 'margin_ratio_target', 'max_stake_spread_move', 'delta_tolerance')
    @classmethod
    def validate_risk_parameters(cls, v: Optional[float]) -> Optional[float]:
        """Validate risk parameters."""
        if v is not None:
            if v < 0 or v > 1:
                raise ValueError(f"Risk parameter must be between 0 and 1, got {v}")
        return v
    
    @field_validator('target_apy', 'max_drawdown')
    @classmethod
    def validate_performance_targets(cls, v: Optional[float]) -> Optional[float]:
        """Validate performance targets."""
        if v is not None:
            if v < 0:
                raise ValueError(f"Performance target must be non-negative, got {v}")
        return v
    
    @field_validator('hedge_venues')
    @classmethod
    def validate_hedge_venues(cls, v: List[str]) -> List[str]:
        """Validate hedge venues."""
        valid_venues = ['binance', 'bybit', 'okx']
        for venue in v:
            if venue.lower() not in valid_venues:
                raise ValueError(f"Invalid hedge venue: {venue}. Valid venues: {valid_venues}")
        return [venue.lower() for venue in v]
    
    @field_validator('hedge_allocation')
    @classmethod
    def validate_hedge_allocation(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate hedge allocation sums to 1.0."""
        if v:
            total = sum(v.values())
            if abs(total - 1.0) > 0.01:  # Allow small floating point errors
                raise ValueError(f"Hedge allocation must sum to 1.0, got {total}")
        return v

    @property
    def ltv_target(self) -> float:
        """Calculate target LTV dynamically from max_ltv and max_stake_spread_move."""
        if self.max_ltv is None or self.max_stake_spread_move is None:
            return 0.0
        
        # target_ltv = max_ltv * (1 - max_stake_spread_move)
        # Example: 0.93 * (1 - 0.02215) = 0.93 * 0.97785 = 0.909 ≈ 0.91
        return self.max_ltv * (1 - self.max_stake_spread_move)
    
    @model_validator(mode='after')
    def validate_parameter_dependencies(self):
        """Validate parameter dependencies using user's precedence hierarchy."""
        return validate_config_dependencies(self)


# REMOVED: OperationalConfig - merged into InfrastructureConfig since both map to configs/*.json


class VenueConfig(BaseModel):
    """Venue configuration - covers all fields from configs/venues/*.yaml"""
    
    # Core venue identification
    venue: Optional[str] = Field(default=None, description="Venue name")
    type: Optional[str] = Field(default=None, description="Venue type (cex, defi, infrastructure)")
    network: Optional[str] = Field(default=None, description="Network (ethereum, etc)")
    service: Optional[str] = Field(default=None, description="Service type (rpc_provider, etc)")
    
    # Trading parameters
    max_leverage: Optional[int] = Field(default=None, description="Maximum leverage")
    min_order_size_usd: Optional[int] = Field(default=None, description="Minimum order size in USD")
    
    # REMOVED: trading_fees fields - not needed in config, handled by execution engine
    
    # Staking parameters
    min_stake_amount: Optional[float] = Field(default=None, description="Minimum stake amount")
    unstaking_period: Optional[int] = Field(default=None, description="Unstaking period in days")
    
    # REMOVED: Risk thresholds that are calculated by RiskMonitor at runtime
    # aave_ltv_warning, aave_ltv_critical, margin_warning_pct, margin_critical_pct, 
    # net_delta_warning, net_delta_critical - these don't appear in venue configs




class ShareClassConfig(BaseModel):
    """Share class configuration - covers all fields from configs/share_classes/*.yaml"""
    
    # Core share class identification
    share_class: Optional[str] = Field(default=None, description="Share class identifier")
    base_currency: Optional[str] = Field(default=None, description="Base currency")
    quote_currency: Optional[str] = Field(default=None, description="Quote currency") 
    type: Optional[str] = Field(default=None, description="Share class type (stable, directional)")
    decimal_places: Optional[int] = Field(default=None, description="Decimal places for precision")
    description: Optional[str] = Field(default=None, description="Share class description")
    
    # Share class capabilities
    allows_hedging: Optional[bool] = Field(default=None, description="Whether hedging is allowed")
    basis_trading_supported: Optional[bool] = Field(default=None, description="Whether basis trading is supported")
    leverage_supported: Optional[bool] = Field(default=None, description="Whether leverage is supported")
    staking_supported: Optional[bool] = Field(default=None, description="Whether staking is supported")
    market_neutral: Optional[bool] = Field(default=None, description="Whether market neutral strategies are required")
    
    # Risk and strategy parameters
    risk_level: Optional[str] = Field(default=None, description="Risk level (low_to_medium, high)")
    supported_strategies: Optional[List[str]] = Field(default=None, description="List of supported strategy modes")




class InfrastructureConfig(BaseModel):
    """Infrastructure configuration - REMOVED JSON configs, all handled by environment variables or hardcoded defaults.
    
    DESIGN DECISION: Eliminated configs/*.json entirely because:
    - Database/Storage URLs: Environment-specific → moved to env variables
    - API CORS origins: Environment-specific → moved to env variables  
    - Cross-network simulations: Always enabled for realistic backtesting
    - Rates: Use live rates, not fixed rates
    - Testnet: Live trading concern, not needed for backtest focus
    
    This eliminates JSON config complexity and focuses on YAML-only config structure.
    """
    
    # REMOVED: All infrastructure fields moved to appropriate locations:
    # - Environment variables: database_url, api_cors_origins, storage_path
    # - Hardcoded defaults: cross_network_log_simulations=True, cross_network_simulate_transfers=True  
    # - Eliminated: rates_use_fixed_rates (always use live rates), testnet (live trading only)
    
    pass  # Empty model - infrastructure handled by environment variables


class ConfigSchema(BaseModel):
    """Main configuration schema - single source of truth"""
    
    # THE 3 MAIN CONFIGURATION MODELS (systematic mapping to configs/)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig, description="Strategy configuration from configs/modes/")
    venue: VenueConfig = Field(default_factory=VenueConfig, description="Venue configuration from configs/venues/")
    share_class_config: Optional[ShareClassConfig] = Field(default=None, description="Share class configuration from configs/share_classes/")
    
    # REMOVED: InfrastructureConfig - all fields moved to environment variables or hardcoded defaults
    # This eliminates the need for configs/*.json files entirely
    
    # Minimal backtest config for quality gate compatibility
    backtest: BacktestConfig = Field(default_factory=BacktestConfig, description="Minimal backtest configuration")
    
    # REMOVED: rates (ScenarioRatesConfig) - not used anywhere in codebase
    # REMOVED: collateral (CollateralConfig) - all LTV and margin parameters now mathematically derived
    # from strategy.max_underlying_move, strategy.max_basis_move, strategy.max_staked_basis_move
    
    @model_validator(mode='after')
    def validate_full_config_consistency(self):
        """Final validation of complete configuration consistency."""
        # Additional cross-section validation can be added here
        return self


# ============================================================================
# MODE-AWARE VALIDATION
# ============================================================================

# Define which modes require which configuration fields
MODE_REQUIREMENTS = {
    'pure_lending': {
        'required_fields': ['lending_enabled', 'data_requirements', 'enable_market_impact'],
        'optional_fields': ['margin_ratio_target', 'max_underlying_move', 'max_spot_perp_basis_move'],
        'forbidden_fields': ['staking_enabled', 'basis_trade_enabled', 'hedge_venues', 'lst_type']
    },
    'btc_basis': {
        'required_fields': ['basis_trade_enabled', 'hedge_venues', 'hedge_allocation_binance', 'hedge_allocation_bybit', 'hedge_allocation_okx', 'data_requirements', 'enable_market_impact', 'lending_enabled'],
        'optional_fields': ['margin_ratio_target'],
        'forbidden_fields': ['staking_enabled']
    },
    'eth_leveraged': {
        'required_fields': ['lending_enabled', 'staking_enabled', 'max_ltv', 'liquidation_threshold', 'max_stake_spread_move', 'data_requirements', 'enable_market_impact', 'lst_type', 'max_drawdown', 'monitoring_position_check_interval', 'monitoring_risk_check_interval'],
        'optional_fields': [],
        'forbidden_fields': ['basis_trade_enabled', 'hedge_venues']
    },
    'usdt_market_neutral': {
        'required_fields': ['lending_enabled', 'staking_enabled', 'basis_trade_enabled', 'hedge_venues', 'hedge_allocation_binance', 'hedge_allocation_bybit', 'hedge_allocation_okx', 'margin_ratio_target', 'data_requirements', 'enable_market_impact', 'lst_type', 'max_drawdown', 'monitoring_position_check_interval', 'monitoring_risk_check_interval'],
        'optional_fields': ['max_ltv', 'liquidation_threshold', 'max_stake_spread_move'],
        'forbidden_fields': []
    },
    'eth_staking_only': {
        'required_fields': ['staking_enabled', 'data_requirements', 'enable_market_impact', 'lst_type', 'max_drawdown', 'monitoring_position_check_interval', 'monitoring_risk_check_interval'],
        'optional_fields': ['max_ltv', 'liquidation_threshold', 'max_stake_spread_move'],
        'forbidden_fields': ['lending_enabled', 'basis_trade_enabled', 'hedge_venues']
    },
    'usdt_market_neutral_no_leverage': {
        'required_fields': ['staking_enabled', 'basis_trade_enabled', 'hedge_venues', 'hedge_allocation_binance', 'hedge_allocation_bybit', 'hedge_allocation_okx', 'data_requirements', 'enable_market_impact', 'lst_type', 'max_drawdown', 'monitoring_position_check_interval', 'monitoring_risk_check_interval'],
        'optional_fields': ['margin_ratio_target'],
        'forbidden_fields': ['lending_enabled']
    }
}


def validate_mode_specific_config(config: ConfigSchema, mode: str) -> ConfigSchema:
    """
    Validate configuration for a specific mode.
    
    Args:
        config: Configuration to validate
        mode: Strategy mode (e.g., 'pure_lending', 'eth_leveraged')
        
    Returns:
        Validated configuration
        
    Raises:
        ValueError: If mode-specific validation fails
    """
    if mode not in MODE_REQUIREMENTS:
        raise ValueError(f"Unknown mode: {mode}. Valid modes: {list(MODE_REQUIREMENTS.keys())}")
    
    requirements = MODE_REQUIREMENTS[mode]
    strategy_config = config.strategy.model_dump()
    
    # Check required fields
    missing_required = []
    for field in requirements['required_fields']:
        if field not in strategy_config or strategy_config[field] is None:
            missing_required.append(field)
    
    if missing_required:
        raise ValueError(f"Mode '{mode}' requires fields: {missing_required}")
    
    # Check forbidden fields
    forbidden_present = []
    for field in requirements['forbidden_fields']:
        if field in strategy_config and strategy_config[field] is not None and strategy_config[field] != False:
            forbidden_present.append(field)
    
    if forbidden_present:
        raise ValueError(f"Mode '{mode}' forbids fields: {forbidden_present}")
    
    # Validate mode-specific logic
    if mode == 'usdt_market_neutral':
        # USDT market neutral must have hedging
        if not strategy_config.get('hedge_venues') or not strategy_config.get('hedge_allocation'):
            raise ValueError("USDT market neutral mode requires hedge_venues and hedge_allocation")
        
        # Hedge allocation must sum to 1.0
        hedge_allocation = strategy_config.get('hedge_allocation', {})
        if hedge_allocation:
            total = sum(hedge_allocation.values())
            if abs(total - 1.0) > 0.01:
                raise ValueError(f"Hedge allocation must sum to 1.0, got {total}")
    
    elif mode == 'eth_leveraged':
        # ETH leveraged must have staking leverage enabled
        pass  # No specific validation needed here
    
    elif mode == 'btc_basis':
        # BTC basis must have hedge venues
        if not strategy_config.get('hedge_venues'):
            raise ValueError("BTC basis mode requires hedge_venues")
    
    return config


def get_mode_specific_config(config: ConfigSchema, mode: str) -> Dict[str, Any]:
    """
    Get mode-specific configuration with only relevant fields.
    
    Args:
        config: Full configuration
        mode: Strategy mode
        
    Returns:
        Mode-specific configuration dictionary
    """
    if mode not in MODE_REQUIREMENTS:
        raise ValueError(f"Unknown mode: {mode}")
    
    requirements = MODE_REQUIREMENTS[mode]
    strategy_config = config.strategy.model_dump()
    
    # Filter to only relevant fields
    relevant_fields = set(requirements['required_fields'] + requirements['optional_fields'])
    mode_config = {k: v for k, v in strategy_config.items() if k in relevant_fields}
    
    # Add infrastructure config if mode has monitoring requirements
    if any(field in ['health_check_interval', 'position_check_interval', 'risk_check_interval'] 
           for field in strategy_config.keys()):
        mode_config['infrastructure'] = config.infrastructure.model_dump()
    
    # Add venue config
    mode_config['venues'] = config.venues.model_dump()
    
    return mode_config


# ============================================================================
# PARAMETER DEPENDENCY VALIDATION (User's Precedence Hierarchy)
# ============================================================================

def validate_config_dependencies(strategy_config: StrategyConfig) -> StrategyConfig:
    """
    Validate parameter dependencies using user's precedence hierarchy (simplified).
    
    Precedence Rules (from user answers):
    1. share_class = Ultimate precedence (never auto-correct)
    2. Base features control derivative features
    3. Auto-derive removed parameters (market_neutral, staking_venue, etc.)
    4. Fail-fast for impossible dependencies
    
    Args:
        strategy_config: Strategy configuration to validate
        
    Returns:
        Validated and potentially auto-corrected configuration
        
    Raises:
        ValueError: For impossible configurations that can't be auto-corrected
    """
    corrections = []
    
    # NEW MODE VALIDATION
    if strategy_config.mode:
        # Validate mode-specific parameter consistency
        if strategy_config.mode == 'pure_lending':
            if not strategy_config.lending_enabled:
                strategy_config.lending_enabled = True
                corrections.append("Auto-enabled lending_enabled for pure_lending mode")
            if strategy_config.staking_enabled:
                strategy_config.staking_enabled = False
                corrections.append("Auto-disabled staking_enabled for pure_lending mode")
            if strategy_config.basis_trade_enabled:
                strategy_config.basis_trade_enabled = False
                corrections.append("Auto-disabled basis_trade_enabled for pure_lending mode")
        
        elif strategy_config.mode == 'btc_basis':
            if not strategy_config.basis_trade_enabled:
                strategy_config.basis_trade_enabled = True
                corrections.append("Auto-enabled basis_trade_enabled for btc_basis mode")
            if strategy_config.lending_enabled:
                strategy_config.lending_enabled = False
                corrections.append("Auto-disabled lending_enabled for btc_basis mode")
            if strategy_config.staking_enabled:
                strategy_config.staking_enabled = False
                corrections.append("Auto-disabled staking_enabled for btc_basis mode")
        
        elif strategy_config.mode in ['eth_leveraged', 'usdt_market_neutral']:
            if not strategy_config.lending_enabled:
                strategy_config.lending_enabled = True
                corrections.append(f"Auto-enabled lending_enabled for {strategy_config.mode} mode")
            if not strategy_config.staking_enabled:
                strategy_config.staking_enabled = True
                corrections.append(f"Auto-enabled staking_enabled for {strategy_config.mode} mode")
            # restaking_enabled not in configs, skip this logic
            
            if strategy_config.mode == 'usdt_market_neutral':
                if not strategy_config.basis_trade_enabled:
                    strategy_config.basis_trade_enabled = True
                    corrections.append("Auto-enabled basis_trade_enabled for usdt_market_neutral mode")
    
    # Validate asset consistency with mode
    if strategy_config.asset and strategy_config.mode:
        if strategy_config.mode == 'btc_basis' and strategy_config.asset != 'BTC':
            raise ValueError(f"Asset mismatch: btc_basis mode requires asset=BTC, got {strategy_config.asset}")
        elif strategy_config.mode in ['eth_leveraged', 'usdt_market_neutral'] and strategy_config.asset != 'ETH':
            raise ValueError(f"Asset mismatch: {strategy_config.mode} mode requires asset=ETH, got {strategy_config.asset}")
    
    # Validate lst_type for ETH modes
    if strategy_config.mode in ['eth_leveraged', 'usdt_market_neutral'] and not strategy_config.lst_type:
        strategy_config.lst_type = 'weeth'  # Default to weeth
        corrections.append(f"Auto-set lst_type=weeth for {strategy_config.mode} mode")
    
    # Validate rewards_mode for ETH modes
    if strategy_config.mode in ['eth_leveraged', 'usdt_market_neutral'] and not strategy_config.rewards_mode:
        strategy_config.rewards_mode = 'base_eigen_seasonal'  # Default to full rewards
        corrections.append(f"Auto-set rewards_mode=base_eigen_seasonal for {strategy_config.mode} mode")
    
    # Validate hedge_venues for modes that need hedging
    if strategy_config.mode in ['btc_basis', 'eth_leveraged', 'usdt_market_neutral']:
        if not strategy_config.hedge_venues:
            if strategy_config.mode == 'btc_basis':
                strategy_config.hedge_venues = ['binance', 'bybit']
                strategy_config.hedge_allocation = {'binance': 0.5, 'bybit': 0.5}
            else:  # eth_leveraged, usdt_market_neutral
                strategy_config.hedge_venues = ['binance', 'bybit', 'okx']
                strategy_config.hedge_allocation = {'binance': 0.33, 'bybit': 0.33, 'okx': 0.34}
            corrections.append(f"Auto-set hedge_venues and allocation for {strategy_config.mode} mode")
    
    
    # AUTO-DERIVE REMOVED PARAMETERS (User simplification)
    
    # Auto-derive market neutrality (no longer user-configurable)
    market_neutral_required = (strategy_config.share_class == "USDT")
    corrections.append(f"Auto-set market_neutral_required={market_neutral_required} (based on {strategy_config.share_class} share class)")
    
    # Auto-derive staking venue (no longer user-configurable)  
    # Will be determined by lst_type later in the backtest logic
    staking_venue = "lido"  # Default, will be overridden based on lst_type
    corrections.append(f"Auto-selected staking_venue={staking_venue} (default, will be determined by lst_type)")
    
    # Auto-derive initial capital strategy (no longer user-configurable)
    if strategy_config.share_class == "ETH":
        initial_capital_strategy = "already_have_eth"  # ETH share class never buys ETH
    elif (strategy_config.share_class == "USDT" and 
          strategy_config.staking_enabled and 
          strategy_config.basis_trade_enabled and 
          not strategy_config.borrowing_enabled):
        initial_capital_strategy = "buy_eth_first"  # Need ETH for staking, using buy+hedge
    else:
        initial_capital_strategy = "keep_usdt_first"  # Default for other USDT strategies
    corrections.append(f"Auto-set initial_capital_strategy={initial_capital_strategy}")
    
    # PRECEDENCE RULE 1: Base features control derivatives
    # If staking disabled, disable all staking derivatives
    if strategy_config.staking_enabled is False:
        # restaking_enabled not in configs, so skip this logic
        pass
    
    
    # PRECEDENCE RULE 3: ETH share class basis trading requires leverage (from original system)
    if (strategy_config.share_class == "ETH" and 
        strategy_config.basis_trade_enabled and 
        not strategy_config.basis_trade_leverage_enabled):
        
        strategy_config.basis_trade_leverage_enabled = True
        corrections.append("Auto-enabled basis_trade_leverage_enabled (required for ETH share class basis trading)")
    
    # FAIL-FAST RULES (Cannot auto-correct)
    
    # FAIL-FAST RULE 1: Must have at least one operation (only check if operations are explicitly set)
    operations = [strategy_config.lending_enabled, strategy_config.staking_enabled, strategy_config.basis_trade_enabled]
    if any(op is not None for op in operations) and not any(operations):
        raise ValueError(
            "IMPOSSIBLE CONFIG: At least one operation must be enabled. "
            "No operations selected - strategy would do nothing. "
            "Fix: Enable at least one of: lending_enabled, staking_enabled, or basis_trade_enabled"
        )
    
    # FAIL-FAST RULE 2: Basis trading needs reasonable risk tolerance for margin capacity
    if strategy_config.basis_trade_enabled and strategy_config.max_underlying_move >= 0.40:
        raise ValueError(
            "IMPOSSIBLE CONFIG: basis_trade_enabled=true with max_underlying_move >= 40% is too risky. "
            "Basis trading needs reasonable risk tolerance for borrowing capacity. "
            "Fix: Reduce max_underlying_move to < 40% or disable basis_trade_enabled"
        )
    
    # FAIL-FAST RULE 3: Complex USDT staking dependency (User's discovery)
    if (strategy_config.share_class == "USDT" and 
        strategy_config.staking_enabled and 
        not strategy_config.borrowing_enabled and 
        not strategy_config.basis_trade_enabled):
        
        raise ValueError(
            "IMPOSSIBLE CONFIG: USDT staking requires ETH acquisition path. "
            "USDT share class cannot stake without maintaining market neutrality. "
            "Choose: A) Enable borrowing_enabled=true (borrow ETH) OR "
            "B) Enable basis_trade_enabled=true (buy+hedge ETH)"
        )
    
    
    # Log corrections (many auto-derivations)
    if corrections:
        logger.info(f"CONFIG AUTO-DERIVATIONS: {'; '.join(corrections)}")
    
    # Store auto-derived parameters for system use (not part of user config)
    strategy_config._auto_derived = {
        'market_neutral_required': market_neutral_required,
        'staking_venue': staking_venue,
        'initial_capital_strategy': initial_capital_strategy
    }
    
    return strategy_config


# ============================================================================
# VALIDATION UTILITIES
# ============================================================================

# REMOVED: get_venue_aware_parameters - now handled by RiskCalculations in Risk Monitor


# REMOVED: validate_venue_aware_risk_settings - now handled by RiskCalculations in Risk Monitor


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def load_and_validate_config(config_dict: Dict[str, Any]) -> ConfigSchema:
    """
    Load and validate complete configuration using canonical schema.
    
    Args:
        config_dict: Raw configuration dictionary
        
    Returns:
        Validated ConfigSchema with auto-corrections applied
        
    Raises:
        ValueError: For impossible configurations that can't be auto-corrected
    """
    try:
        # Create Pydantic model (includes all field validation)
        config = ConfigSchema(**config_dict)
        
        # Additional cross-section validation using venue-aware approach
        # Note: initial_capital validation moved to runtime validation in BacktestService
        # since initial_capital is now a runtime parameter, not a config parameter
        
        return config
        
    except Exception as e:
        if "AUTO-CORRECTED" in str(e) or "IMPOSSIBLE CONFIG" in str(e):
            # Re-raise our validation errors as-is
            raise
        else:
            # Wrap Pydantic validation errors with context
            raise ValueError(f"Config validation failed: {str(e)}")


def get_corrections_from_config(original_dict: Dict[str, Any], validated_config: ConfigSchema) -> List[Dict[str, Any]]:
    """Extract what corrections were made for API response."""
    corrections = []
    
    # Compare original vs validated to detect changes
    # This is a simplified implementation - could be more sophisticated
    
    original_strategy = original_dict.get('strategy', {})
    validated_strategy = validated_config.strategy.model_dump()
    
    for key, new_value in validated_strategy.items():
        original_value = original_strategy.get(key)
        if original_value != new_value and original_value is not None:
            corrections.append({
                'parameter': f'strategy.{key}',
                'from': original_value,
                'to': new_value,
                'reason': f'Parameter dependency auto-correction'
            })
    
    return corrections
