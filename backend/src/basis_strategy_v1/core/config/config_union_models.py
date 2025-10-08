"""Comprehensive Configuration Models - Union of all configs."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from enum import Enum

class AllowsHedgingConfigUnion(BaseModel):
    """Union model for allows_hedging configuration."""


class AssetConfigUnion(BaseModel):
    """Union model for asset configuration."""


class BaseCurrencyConfigUnion(BaseModel):
    """Union model for base_currency configuration."""


class BasisTradeEnabledConfigUnion(BaseModel):
    """Union model for basis_trade_enabled configuration."""


class BasisTradingSupportedConfigUnion(BaseModel):
    """Union model for basis_trading_supported configuration."""


class BorrowingEnabledConfigUnion(BaseModel):
    """Union model for borrowing_enabled configuration."""


class DataRequirementsConfigUnion(BaseModel):
    """Union model for data_requirements configuration."""


class DecimalPlacesConfigUnion(BaseModel):
    """Union model for decimal_places configuration."""


class DeltaToleranceConfigUnion(BaseModel):
    """Union model for delta_tolerance configuration."""


class DescriptionConfigUnion(BaseModel):
    """Union model for description configuration."""


class EnableMarketImpactConfigUnion(BaseModel):
    """Union model for enable_market_impact configuration."""


class HedgeAllocationConfigUnion(BaseModel):
    """Union model for hedge_allocation configuration."""


class HedgeAllocationBinanceConfigUnion(BaseModel):
    """Union model for hedge_allocation_binance configuration."""


class HedgeAllocationBybitConfigUnion(BaseModel):
    """Union model for hedge_allocation_bybit configuration."""


class HedgeAllocationOkxConfigUnion(BaseModel):
    """Union model for hedge_allocation_okx configuration."""


class HedgeVenuesConfigUnion(BaseModel):
    """Union model for hedge_venues configuration."""


class LendingEnabledConfigUnion(BaseModel):
    """Union model for lending_enabled configuration."""


class LeverageSupportedConfigUnion(BaseModel):
    """Union model for leverage_supported configuration."""


class LiquidationThresholdConfigUnion(BaseModel):
    """Union model for liquidation_threshold configuration."""


class LstTypeConfigUnion(BaseModel):
    """Union model for lst_type configuration."""


class MarginRatioTargetConfigUnion(BaseModel):
    """Union model for margin_ratio_target configuration."""


class MarketNeutralConfigUnion(BaseModel):
    """Union model for market_neutral configuration."""


class MaxDrawdownConfigUnion(BaseModel):
    """Union model for max_drawdown configuration."""


class MaxLeverageConfigUnion(BaseModel):
    """Union model for max_leverage configuration."""


class MaxLeverageLoopsConfigUnion(BaseModel):
    """Union model for max_leverage_loops configuration."""


class MaxLtvConfigUnion(BaseModel):
    """Union model for max_ltv configuration."""


class MaxStakeSpreadMoveConfigUnion(BaseModel):
    """Union model for max_stake_spread_move configuration."""


class MinLoopPositionUsdConfigUnion(BaseModel):
    """Union model for min_loop_position_usd configuration."""


class MinOrderSizeUsdConfigUnion(BaseModel):
    """Union model for min_order_size_usd configuration."""


class MinStakeAmountConfigUnion(BaseModel):
    """Union model for min_stake_amount configuration."""


class ModeConfigUnion(BaseModel):
    """Union model for mode configuration."""


class MonitoringPositionCheckIntervalConfigUnion(BaseModel):
    """Union model for monitoring_position_check_interval configuration."""


class MonitoringRiskCheckIntervalConfigUnion(BaseModel):
    """Union model for monitoring_risk_check_interval configuration."""


class NetworkConfigUnion(BaseModel):
    """Union model for network configuration."""


class QuoteCurrencyConfigUnion(BaseModel):
    """Union model for quote_currency configuration."""


class RewardsModeConfigUnion(BaseModel):
    """Union model for rewards_mode configuration."""


class RiskLevelConfigUnion(BaseModel):
    """Union model for risk_level configuration."""


class ServiceConfigUnion(BaseModel):
    """Union model for service configuration."""


class ShareClassConfigUnion(BaseModel):
    """Union model for share_class configuration."""


class StakingEnabledConfigUnion(BaseModel):
    """Union model for staking_enabled configuration."""


class StakingSupportedConfigUnion(BaseModel):
    """Union model for staking_supported configuration."""


class SupportedStrategiesConfigUnion(BaseModel):
    """Union model for supported_strategies configuration."""


class TargetApyConfigUnion(BaseModel):
    """Union model for target_apy configuration."""


class TypeConfigUnion(BaseModel):
    """Union model for type configuration."""


class UnstakingPeriodConfigUnion(BaseModel):
    """Union model for unstaking_period configuration."""


class UnwindModeConfigUnion(BaseModel):
    """Union model for unwind_mode configuration."""


class UseFlashLoanConfigUnion(BaseModel):
    """Union model for use_flash_loan configuration."""


class VenueConfigUnion(BaseModel):
    """Union model for venue configuration."""


class ConfigUnion(BaseModel):
    """Main union model covering all configuration files."""

    allows_hedging: Optional[AllowsHedgingConfigUnion] = Field(default=None, description="allows_hedging configuration")
    asset: Optional[AssetConfigUnion] = Field(default=None, description="asset configuration")
    base_currency: Optional[BaseCurrencyConfigUnion] = Field(default=None, description="base_currency configuration")
    basis_trade_enabled: Optional[BasisTradeEnabledConfigUnion] = Field(default=None, description="basis_trade_enabled configuration")
    basis_trading_supported: Optional[BasisTradingSupportedConfigUnion] = Field(default=None, description="basis_trading_supported configuration")
    borrowing_enabled: Optional[BorrowingEnabledConfigUnion] = Field(default=None, description="borrowing_enabled configuration")
    data_requirements: Optional[DataRequirementsConfigUnion] = Field(default=None, description="data_requirements configuration")
    decimal_places: Optional[DecimalPlacesConfigUnion] = Field(default=None, description="decimal_places configuration")
    delta_tolerance: Optional[DeltaToleranceConfigUnion] = Field(default=None, description="delta_tolerance configuration")
    description: Optional[DescriptionConfigUnion] = Field(default=None, description="description configuration")
    enable_market_impact: Optional[EnableMarketImpactConfigUnion] = Field(default=None, description="enable_market_impact configuration")
    hedge_allocation: Optional[HedgeAllocationConfigUnion] = Field(default=None, description="hedge_allocation configuration")
    hedge_allocation_binance: Optional[HedgeAllocationBinanceConfigUnion] = Field(default=None, description="hedge_allocation_binance configuration")
    hedge_allocation_bybit: Optional[HedgeAllocationBybitConfigUnion] = Field(default=None, description="hedge_allocation_bybit configuration")
    hedge_allocation_okx: Optional[HedgeAllocationOkxConfigUnion] = Field(default=None, description="hedge_allocation_okx configuration")
    hedge_venues: Optional[HedgeVenuesConfigUnion] = Field(default=None, description="hedge_venues configuration")
    lending_enabled: Optional[LendingEnabledConfigUnion] = Field(default=None, description="lending_enabled configuration")
    leverage_supported: Optional[LeverageSupportedConfigUnion] = Field(default=None, description="leverage_supported configuration")
    liquidation_threshold: Optional[LiquidationThresholdConfigUnion] = Field(default=None, description="liquidation_threshold configuration")
    lst_type: Optional[LstTypeConfigUnion] = Field(default=None, description="lst_type configuration")
    margin_ratio_target: Optional[MarginRatioTargetConfigUnion] = Field(default=None, description="margin_ratio_target configuration")
    market_neutral: Optional[MarketNeutralConfigUnion] = Field(default=None, description="market_neutral configuration")
    max_drawdown: Optional[MaxDrawdownConfigUnion] = Field(default=None, description="max_drawdown configuration")
    max_leverage: Optional[MaxLeverageConfigUnion] = Field(default=None, description="max_leverage configuration")
    max_leverage_loops: Optional[MaxLeverageLoopsConfigUnion] = Field(default=None, description="max_leverage_loops configuration")
    max_ltv: Optional[MaxLtvConfigUnion] = Field(default=None, description="max_ltv configuration")
    max_stake_spread_move: Optional[MaxStakeSpreadMoveConfigUnion] = Field(default=None, description="max_stake_spread_move configuration")
    min_loop_position_usd: Optional[MinLoopPositionUsdConfigUnion] = Field(default=None, description="min_loop_position_usd configuration")
    min_order_size_usd: Optional[MinOrderSizeUsdConfigUnion] = Field(default=None, description="min_order_size_usd configuration")
    min_stake_amount: Optional[MinStakeAmountConfigUnion] = Field(default=None, description="min_stake_amount configuration")
    mode: Optional[ModeConfigUnion] = Field(default=None, description="mode configuration")
    monitoring_position_check_interval: Optional[MonitoringPositionCheckIntervalConfigUnion] = Field(default=None, description="monitoring_position_check_interval configuration")
    monitoring_risk_check_interval: Optional[MonitoringRiskCheckIntervalConfigUnion] = Field(default=None, description="monitoring_risk_check_interval configuration")
    network: Optional[NetworkConfigUnion] = Field(default=None, description="network configuration")
    quote_currency: Optional[QuoteCurrencyConfigUnion] = Field(default=None, description="quote_currency configuration")
    rewards_mode: Optional[RewardsModeConfigUnion] = Field(default=None, description="rewards_mode configuration")
    risk_level: Optional[RiskLevelConfigUnion] = Field(default=None, description="risk_level configuration")
    service: Optional[ServiceConfigUnion] = Field(default=None, description="service configuration")
    share_class: Optional[ShareClassConfigUnion] = Field(default=None, description="share_class configuration")
    staking_enabled: Optional[StakingEnabledConfigUnion] = Field(default=None, description="staking_enabled configuration")
    staking_supported: Optional[StakingSupportedConfigUnion] = Field(default=None, description="staking_supported configuration")
    supported_strategies: Optional[SupportedStrategiesConfigUnion] = Field(default=None, description="supported_strategies configuration")
    target_apy: Optional[TargetApyConfigUnion] = Field(default=None, description="target_apy configuration")
    type: Optional[TypeConfigUnion] = Field(default=None, description="type configuration")
    unstaking_period: Optional[UnstakingPeriodConfigUnion] = Field(default=None, description="unstaking_period configuration")
    unwind_mode: Optional[UnwindModeConfigUnion] = Field(default=None, description="unwind_mode configuration")
    use_flash_loan: Optional[UseFlashLoanConfigUnion] = Field(default=None, description="use_flash_loan configuration")
    venue: Optional[VenueConfigUnion] = Field(default=None, description="venue configuration")
