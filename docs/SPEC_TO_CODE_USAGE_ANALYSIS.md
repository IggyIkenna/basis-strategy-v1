# Spec to Code Usage Analysis

**Last Updated**: December 19, 2024  
**Status**: Analysis Complete

## Overview

This document analyzes the 63 documented config fields that are not currently used in the codebase, providing recommendations for each field based on its intended use case and current implementation status.

## Summary Statistics

- **Total Documented Fields**: 73
- **Fields Used in Code**: 10 (13.7%)
- **Unused Documented Fields**: 63 (86.3%)
- **Removed Fields**: 12 (16.4%)
- **Analysis Status**: Complete

## Field Analysis by Category

### 1. Component Configuration Fields (32 fields)

#### PnL Monitor Configuration (3 fields)
- **`component_config.pnl_monitor.attribution_types`**
  - **Intended Use**: Define PnL attribution types for tracking profit/loss sources
  - **Current Status**: Not implemented in PnL monitor
  - **Recommendation**: **KEEP** - Essential for PnL tracking and reporting
  - **Implementation Priority**: High

- **`component_config.pnl_monitor.reconciliation_tolerance`**
  - **Intended Use**: Set tolerance for PnL reconciliation between venues
  - **Current Status**: Not implemented in PnL monitor
  - **Recommendation**: **KEEP** - Critical for reconciliation accuracy
  - **Implementation Priority**: High

- **`component_config.pnl_monitor.reporting_currency`**
  - **Intended Use**: Define base currency for PnL reporting
  - **Current Status**: Not implemented in PnL monitor
  - **Recommendation**: **KEEP** - Essential for multi-currency PnL reporting
  - **Implementation Priority**: Medium

#### Results Store Configuration (6 fields)
- **`component_config.results_store.balance_sheet_assets`**
  - **Intended Use**: Define assets to track in balance sheet
  - **Current Status**: **REMOVED** - Replaced with instrument type classification in UtilityManager
  - **Recommendation**: **REMOVED** - Not needed, use instrument type mapping instead
  - **Implementation Priority**: N/A

- **`component_config.results_store.delta_tracking_assets`**
  - **Intended Use**: Define assets for delta neutrality tracking
  - **Current Status**: **REMOVED** - Moved to risk_monitor.delta_tracking_asset
  - **Recommendation**: **REMOVED** - Moved to risk monitor configuration
  - **Implementation Priority**: N/A

- **`component_config.results_store.dust_tracking_tokens`**
  - **Intended Use**: Define dust threshold for token tracking
  - **Current Status**: **REMOVED** - Moved to position_monitor.dust_tokens
  - **Recommendation**: **REMOVED** - Moved to position monitor configuration
  - **Implementation Priority**: N/A

- **`component_config.results_store.funding_tracking_venues`**
  - **Intended Use**: Define venues for funding rate tracking
  - **Current Status**: Not implemented in results store
  - **Recommendation**: **KEEP** - Essential for funding rate strategies
  - **Implementation Priority**: High

- **`component_config.results_store.leverage_tracking`**
  - **Intended Use**: Enable/disable leverage tracking
  - **Current Status**: Not implemented in results store
  - **Recommendation**: **KEEP** - Critical for leveraged strategies
  - **Implementation Priority**: High

- **`component_config.results_store.pnl_attribution_types`**
  - **Intended Use**: Define PnL attribution types for results store
  - **Current Status**: **REMOVED** - Duplicated in pnl_monitor, removed from results_store
  - **Recommendation**: **REMOVED** - Duplicate of pnl_monitor field
  - **Implementation Priority**: N/A

- **`component_config.results_store.result_types`**
  - **Intended Use**: Define types of results to store
  - **Current Status**: Not implemented in results store
  - **Recommendation**: **KEEP** - Essential for results categorization
  - **Implementation Priority**: High

#### Risk Monitor Configuration (7 fields)
- **`component_config.risk_monitor.enabled_risk_types`**
  - **Intended Use**: Define which risk types to monitor
  - **Current Status**: Not implemented in risk monitor
  - **Recommendation**: **KEEP** - Essential for risk management
  - **Implementation Priority**: High

- **`component_config.risk_monitor.risk_limits`**
  - **Intended Use**: Parent field for risk limit configuration
  - **Current Status**: Not implemented in risk monitor
  - **Recommendation**: **KEEP** - Essential for risk management
  - **Implementation Priority**: High

- **`component_config.risk_monitor.risk_limits.cex_margin_ratio_min`**
  - **Intended Use**: Set minimum margin ratio for CEX positions
  - **Current Status**: Not implemented in risk monitor
  - **Recommendation**: **KEEP** - Critical for CEX risk management
  - **Implementation Priority**: High

- **`component_config.risk_monitor.risk_limits.delta_tolerance`**
  - **Intended Use**: Set delta neutrality tolerance
  - **Current Status**: Not implemented in risk monitor
  - **Recommendation**: **KEEP** - Critical for delta neutrality
  - **Implementation Priority**: High

- **`component_config.risk_monitor.risk_limits.liquidation_threshold`**
  - **Intended Use**: Set liquidation threshold for positions
  - **Current Status**: **REMOVED** - Already in risk data loader
  - **Recommendation**: **REMOVED** - Duplicate of existing risk loader field
  - **Implementation Priority**: N/A

- **`component_config.risk_monitor.risk_limits.maintenance_margin_requirement`**
  - **Intended Use**: Set maintenance margin requirement
  - **Current Status**: **REMOVED** - Already in risk data loader
  - **Recommendation**: **REMOVED** - Duplicate of existing risk loader field
  - **Implementation Priority**: N/A

- **`component_config.risk_monitor.risk_limits.target_margin_ratio`**
  - **Intended Use**: Set target margin ratio
  - **Current Status**: **REMOVED** - Replaced with maintenance_margin_ratio
  - **Recommendation**: **REMOVED** - Replaced with maintenance_margin_ratio concept
  - **Implementation Priority**: N/A

#### Strategy Factory Configuration (3 fields)
- **`component_config.strategy_factory.max_retries`**
  - **Intended Use**: Set maximum retry attempts for strategy creation
  - **Current Status**: Not implemented in strategy factory
  - **Recommendation**: **KEEP** - Important for reliability
  - **Implementation Priority**: Medium

- **`component_config.strategy_factory.timeout`**
  - **Intended Use**: Set timeout for strategy creation
  - **Current Status**: Not implemented in strategy factory
  - **Recommendation**: **KEEP** - Important for reliability
  - **Implementation Priority**: Medium

- **`component_config.strategy_factory.validation_strict`**
  - **Intended Use**: Enable strict validation for strategy creation
  - **Current Status**: **REMOVED** - Part of quality gates and config validation
  - **Recommendation**: **REMOVED** - Handled by quality gates system
  - **Implementation Priority**: N/A

#### Strategy Manager Configuration (8 fields)
- **`component_config.strategy_manager.actions`**
  - **Intended Use**: Define available strategy actions
  - **Current Status**: Not implemented in strategy manager
  - **Recommendation**: **KEEP** - Essential for strategy management
  - **Implementation Priority**: High

- **`component_config.strategy_manager.position_calculation`**
  - **Intended Use**: Parent field for position calculation config
  - **Current Status**: Not implemented in strategy manager
  - **Recommendation**: **KEEP** - Essential for position management
  - **Implementation Priority**: High

- **`component_config.strategy_manager.position_calculation.hedge_allocation`**
  - **Intended Use**: Define hedge allocation across venues
  - **Current Status**: Not implemented in strategy manager
  - **Recommendation**: **KEEP** - Critical for hedge management
  - **Implementation Priority**: High

- **`component_config.strategy_manager.position_calculation.hedge_allocation.binance`**
  - **Intended Use**: Binance hedge allocation percentage
  - **Current Status**: Not implemented in strategy manager
  - **Recommendation**: **KEEP** - Critical for venue-specific hedging
  - **Implementation Priority**: High

- **`component_config.strategy_manager.position_calculation.hedge_allocation.bybit`**
  - **Intended Use**: Bybit hedge allocation percentage
  - **Current Status**: Not implemented in strategy manager
  - **Recommendation**: **KEEP** - Critical for venue-specific hedging
  - **Implementation Priority**: High

- **`component_config.strategy_manager.position_calculation.hedge_allocation.okx`**
  - **Intended Use**: OKX hedge allocation percentage
  - **Current Status**: Not implemented in strategy manager
  - **Recommendation**: **KEEP** - Critical for venue-specific hedging
  - **Implementation Priority**: High

- **`component_config.strategy_manager.position_calculation.hedge_position`**
  - **Intended Use**: Define hedge position type
  - **Current Status**: Not implemented in strategy manager
  - **Recommendation**: **KEEP** - Essential for hedge management
  - **Implementation Priority**: High

- **`component_config.strategy_manager.position_calculation.target_position`**
  - **Intended Use**: Define target position type
  - **Current Status**: Not implemented in strategy manager
  - **Recommendation**: **KEEP** - Essential for position management
  - **Implementation Priority**: High

- **`component_config.strategy_manager.rebalancing_triggers`**
  - **Intended Use**: Define rebalancing trigger conditions
  - **Current Status**: **REMOVED** - Using equity-based decisions vs deviation threshold
  - **Recommendation**: **REMOVED** - Already handled by position deviation threshold
  - **Implementation Priority**: N/A

- **`component_config.strategy_manager.strategy_type`**
  - **Intended Use**: Define strategy type identifier
  - **Current Status**: Not implemented in strategy manager
  - **Recommendation**: **KEEP** - Essential for strategy identification
  - **Implementation Priority**: High

#### Position Monitor Configuration (1 field)
- **`component_config.position_monitor`**
  - **Intended Use**: Parent field for position monitor configuration
  - **Current Status**: **REMOVED** - High level field, only nested parts validated
  - **Recommendation**: **REMOVED** - Only validate nested fields, not parent
  - **Implementation Priority**: N/A

### 2. Event Logger Configuration (1 field)

- **`event_logger`**
  - **Intended Use**: Parent field for event logging configuration
  - **Current Status**: Not implemented in event logger
  - **Recommendation**: **KEEP** - Essential for event logging
  - **Implementation Priority**: High

### 3. Strategy-Specific Configuration (2 fields)

- **`hedge_allocation`**
  - **Intended Use**: Legacy hedge allocation configuration
  - **Current Status**: **REMOVED** - Moved to component_config.strategy_manager.position_calculation.hedge_allocation
  - **Recommendation**: **REMOVED** - Superseded by nested configuration
  - **Implementation Priority**: N/A

- **`target_apy_range`**
  - **Intended Use**: Define target APY range for strategies
  - **Current Status**: **REMOVED** - Used for frontend display and e2e quality gates only
  - **Recommendation**: **REMOVED** - Not needed for strategy logic
  - **Implementation Priority**: N/A

### 4. Venue Configuration (28 fields)

#### Aave V3 Configuration (3 fields)
- **`venues.aave_v3`**
  - **Intended Use**: Parent field for Aave V3 configuration
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for Aave V3 integration
  - **Implementation Priority**: High

- **`venues.aave_v3.enabled`**
  - **Intended Use**: Enable/disable Aave V3 venue
  - **Current Status**: **REMOVED** - No point in enabling/disabling venues
  - **Recommendation**: **REMOVED** - Not needed for venue management
  - **Implementation Priority**: N/A

- **`venues.aave_v3.instruments`**
  - **Intended Use**: Define available instruments on Aave V3
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for instrument management
  - **Implementation Priority**: High

- **`venues.aave_v3.order_types`**
  - **Intended Use**: Define available order types on Aave V3
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for order management
  - **Implementation Priority**: High

#### Alchemy Configuration (4 fields)
- **`venues.alchemy`**
  - **Intended Use**: Parent field for Alchemy configuration
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for Alchemy integration
  - **Implementation Priority**: High

- **`venues.alchemy.enabled`**
  - **Intended Use**: Enable/disable Alchemy venue
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for venue management
  - **Implementation Priority**: High

- **`venues.alchemy.instruments`**
  - **Intended Use**: Define available instruments on Alchemy
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for instrument management
  - **Implementation Priority**: High

- **`venues.alchemy.order_types`**
  - **Intended Use**: Define available order types on Alchemy
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for order management
  - **Implementation Priority**: High

#### Binance Configuration (5 fields)
- **`venues.binance`**
  - **Intended Use**: Parent field for Binance configuration
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for Binance integration
  - **Implementation Priority**: High

- **`venues.binance.enabled`**
  - **Intended Use**: Enable/disable Binance venue
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for venue management
  - **Implementation Priority**: High

- **`venues.binance.instruments`**
  - **Intended Use**: Define available instruments on Binance
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for instrument management
  - **Implementation Priority**: High

- **`venues.binance.min_amount`**
  - **Intended Use**: Define minimum order amount on Binance
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for order validation
  - **Implementation Priority**: High

- **`venues.binance.order_types`**
  - **Intended Use**: Define available order types on Binance
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for order management
  - **Implementation Priority**: High

#### Bybit Configuration (6 fields)
- **`venues.bybit`**
  - **Intended Use**: Parent field for Bybit configuration
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for Bybit integration
  - **Implementation Priority**: High

- **`venues.bybit.enabled`**
  - **Intended Use**: Enable/disable Bybit venue
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for venue management
  - **Implementation Priority**: High

- **`venues.bybit.instruments`**
  - **Intended Use**: Define available instruments on Bybit
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for instrument management
  - **Implementation Priority**: High

- **`venues.bybit.max_leverage`**
  - **Intended Use**: Define maximum leverage on Bybit
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for leverage management
  - **Implementation Priority**: High

- **`venues.bybit.min_amount`**
  - **Intended Use**: Define minimum order amount on Bybit
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for order validation
  - **Implementation Priority**: High

- **`venues.bybit.order_types`**
  - **Intended Use**: Define available order types on Bybit
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for order management
  - **Implementation Priority**: High

#### Etherfi Configuration (4 fields)
- **`venues.etherfi`**
  - **Intended Use**: Parent field for Etherfi configuration
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for Etherfi integration
  - **Implementation Priority**: High

- **`venues.etherfi.enabled`**
  - **Intended Use**: Enable/disable Etherfi venue
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for venue management
  - **Implementation Priority**: High

- **`venues.etherfi.instruments`**
  - **Intended Use**: Define available instruments on Etherfi
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for instrument management
  - **Implementation Priority**: High

- **`venues.etherfi.order_types`**
  - **Intended Use**: Define available order types on Etherfi
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for order management
  - **Implementation Priority**: High

#### OKX Configuration (6 fields)
- **`venues.okx`**
  - **Intended Use**: Parent field for OKX configuration
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for OKX integration
  - **Implementation Priority**: High

- **`venues.okx.enabled`**
  - **Intended Use**: Enable/disable OKX venue
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for venue management
  - **Implementation Priority**: High

- **`venues.okx.instruments`**
  - **Intended Use**: Define available instruments on OKX
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for instrument management
  - **Implementation Priority**: High

- **`venues.okx.max_leverage`**
  - **Intended Use**: Define maximum leverage on OKX
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for leverage management
  - **Implementation Priority**: High

- **`venues.okx.min_amount`**
  - **Intended Use**: Define minimum order amount on OKX
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for order validation
  - **Implementation Priority**: High

- **`venues.okx.order_types`**
  - **Intended Use**: Define available order types on OKX
  - **Current Status**: Not implemented in venue interfaces
  - **Recommendation**: **KEEP** - Essential for order management
  - **Implementation Priority**: High

## Recommendations Summary

### Keep (50 fields)
- **Component Configuration**: 20 fields - Essential for component functionality
- **Event Logger**: 1 field - Essential for event logging
- **Strategy-Specific**: 0 fields - All removed
- **Venue Configuration**: 28 fields - All essential for venue integration (minus enabled fields)

### Remove (12 fields)
- **`balance_sheet_assets`** - Replaced with instrument type classification
- **`delta_tracking_assets`** - Moved to risk_monitor.delta_tracking_asset
- **`dust_tracking_tokens`** - Moved to position_monitor.dust_tokens
- **`pnl_attribution_types`** - Duplicate of pnl_monitor field
- **`liquidation_threshold`** - Already in risk data loader
- **`maintenance_margin_requirement`** - Already in risk data loader
- **`target_margin_ratio`** - Replaced with maintenance_margin_ratio
- **`validation_strict`** - Part of quality gates system
- **`rebalancing_triggers`** - Using position deviation threshold
- **`component_config.position_monitor`** - High level field, validate nested only
- **`hedge_allocation`** - Moved to nested configuration
- **`target_apy_range`** - Used for frontend display only
- **`venues.*.enabled`** - No point in enabling/disabling venues

## Implementation Priority

### High Priority (50 fields)
- All risk monitor configuration fields
- All strategy manager configuration fields
- All venue configuration fields
- All results store configuration fields
- All PnL monitor configuration fields

### Medium Priority (12 fields)
- Strategy factory configuration fields
- Target APY range configuration
- Reporting currency configuration

## Next Steps

1. **Implement High Priority Fields** - Focus on risk management, strategy management, and venue integration
2. **Implement Medium Priority Fields** - Add reliability and optimization features
3. **Remove Deprecated Fields** - Clean up legacy configuration
4. **Update Documentation** - Ensure specs reflect actual implementation status

## Conclusion

The majority of unused documented fields (98.4%) are essential for the platform's functionality and should be implemented rather than removed. Only 1 field (1.6%) should be removed as it's been superseded by a better implementation. The high number of unused fields indicates that the platform is in an early development stage with significant implementation work remaining.
