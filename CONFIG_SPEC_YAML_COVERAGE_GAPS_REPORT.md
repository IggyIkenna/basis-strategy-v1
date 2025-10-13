# Config Spec YAML Coverage Gaps Report

**Generated**: October 13, 2025  
**Quality Gate**: Config Spec YAML Sync  
**Coverage**: 72.4% (63/87 fields synchronized)

## Executive Summary

After simplifying the config documentation quality gates to focus on specs ↔ YAML configs (removing 19_CONFIGURATION.md from validation), we have identified significant gaps between component specifications and YAML configuration files. The current coverage is 72.4%, with 24 fields documented in specs but missing from YAML configs, and 24 fields present in YAML configs but not documented in specs.

## Coverage Analysis

### Overall Statistics
- **Total Spec Fields**: 87
- **Total YAML Fields**: 87  
- **Synchronized Fields**: 63
- **Coverage Percentage**: 72.4%
- **Orphaned References**: 48 total (24 in each direction)

### Component Field Distribution
- **Component Specs**: 10 specs with 87 total fields
- **Strategy Specs**: 9 specs with 87 total fields
- **YAML Configs**: 87 fields across all config files

## Gap Analysis by Category

### 1. Spec Fields Missing from YAML Configs (24 fields)

#### Execution Manager Action Mappings (3 fields)
- `component_config.execution_manager.action_mapping.close_perp`
- `component_config.execution_manager.action_mapping.open_perp_long`
- `component_config.execution_manager.action_mapping.open_perp_short`

**Impact**: These fields define venue-specific action mappings for perpetual trading operations. Missing from YAML means execution manager cannot route actions properly.

#### Exposure Monitor Conversion Methods (9 fields)
- `component_config.exposure_monitor.conversion_methods.EIGEN`
- `component_config.exposure_monitor.conversion_methods.ETH`
- `component_config.exposure_monitor.conversion_methods.ETHFI`
- `component_config.exposure_monitor.conversion_methods.ETH_PERP`
- `component_config.exposure_monitor.conversion_methods.KING`
- `component_config.exposure_monitor.conversion_methods.USDT`
- `component_config.exposure_monitor.conversion_methods.aWeETH`
- `component_config.exposure_monitor.conversion_methods.variableDebtWETH`
- `component_config.exposure_monitor.conversion_methods.weETH`

**Impact**: These fields define how different assets are converted for exposure calculations. Missing from YAML means exposure monitor cannot properly calculate cross-asset exposures.

#### Results Store Configuration (4 fields)
- `component_config.results_store.delta_tracking_assets`
- `component_config.results_store.dust_tracking_tokens`
- `component_config.results_store.funding_tracking_venues`
- `component_config.results_store.leverage_tracking`

**Impact**: These fields control what data is tracked and stored. Missing from YAML means results store may not track all required metrics.

#### Risk Monitor Configuration (1 field)
- `component_config.risk_monitor.risk_limits.liquidation_threshold`

**Impact**: Missing liquidation threshold configuration means risk monitor cannot properly assess liquidation risk.

#### Strategy Manager Position Calculation (2 fields)
- `component_config.strategy_manager.position_calculation.leverage_ratio`
- `component_config.strategy_manager.position_calculation.method`

**Impact**: Missing position calculation configuration means strategy manager cannot properly calculate position sizes.

#### Venue Configuration (5 fields)
- `venues.binance.min_amount`
- `venues.bybit.max_leverage`
- `venues.bybit.min_amount`
- `venues.okx.max_leverage`
- `venues.okx.min_amount`

**Impact**: Missing venue-specific constraints means execution interfaces cannot enforce proper order sizing and leverage limits.

### 2. YAML Fields Missing from Specs (24 fields)

#### Top-Level Configuration (8 fields)
- `api_contract`
- `auth`
- `base_currency`
- `basis_trade_enabled`
- `lending_enabled`
- `leverage_supported`
- `staking_enabled`
- `target_apy_range`

**Impact**: These fields are used in YAML configs but not documented in specs, making it unclear how they should be used.

#### Component Configuration (4 fields)
- `component_config`
- `component_config.pnl_calculator.reconciliation_tolerance`
- `component_config.pnl_calculator.reporting_currency`
- `component_config.risk_monitor.risk_limits.cex_margin_ratio_min`

**Impact**: Missing component config documentation means developers don't know how to configure these components.

#### Strategy Manager Hedge Allocation (3 fields)
- `component_config.strategy_manager.position_calculation.hedge_allocation.binance`
- `component_config.strategy_manager.position_calculation.hedge_allocation.bybit`
- `component_config.strategy_manager.position_calculation.hedge_allocation.okx`

**Impact**: These fields are used in YAML but not documented in specs, despite being critical for venue allocation.

#### Venue and Infrastructure (9 fields)
- `endpoints`
- `event_logger`
- `example`
- `ml_config`
- `trading_fees`
- `type`
- `validation`
- `venue`
- `venues`

**Impact**: Missing venue and infrastructure configuration documentation makes it difficult to understand system architecture.

## Priority Recommendations

### High Priority (Critical for Functionality)

1. **Add Missing Venue Configuration Fields to YAML**
   - Add `venues.binance.min_amount`, `venues.bybit.max_leverage`, etc. to venue YAML files
   - These are critical for proper order execution and risk management

2. **Add Missing Component Config Fields to YAML**
   - Add execution manager action mappings to YAML configs
   - Add exposure monitor conversion methods to YAML configs
   - Add results store tracking configuration to YAML configs

3. **Document YAML-Only Fields in Specs**
   - Add `component_config.pnl_calculator.reconciliation_tolerance` to PnL Calculator spec
   - Add `component_config.risk_monitor.risk_limits.cex_margin_ratio_min` to Risk Monitor spec
   - Add hedge allocation fields to Strategy Manager spec

### Medium Priority (Important for Completeness)

4. **Add Missing Strategy Configuration Fields to YAML**
   - Add `component_config.strategy_manager.position_calculation.leverage_ratio` to strategy YAML files
   - Add `component_config.strategy_manager.position_calculation.method` to strategy YAML files

5. **Document Top-Level Configuration Fields in Specs**
   - Add `basis_trade_enabled`, `lending_enabled`, `leverage_supported`, `staking_enabled` to relevant strategy specs
   - Add `target_apy_range` to strategy specs

### Low Priority (Nice to Have)

6. **Document Infrastructure Fields in Specs**
   - Add `api_contract`, `auth`, `endpoints` to venue specs
   - Add `trading_fees`, `validation` to venue specs

## Implementation Plan

### Phase 1: Critical Venue Configuration (Week 1)
- [ ] Add missing venue fields to `configs/venues/*.yaml` files
- [ ] Update venue specs to document these fields
- [ ] Test venue configuration loading

### Phase 2: Component Configuration (Week 2)
- [ ] Add missing component config fields to YAML files
- [ ] Update component specs to document YAML-only fields
- [ ] Test component initialization with new configs

### Phase 3: Strategy Configuration (Week 3)
- [ ] Add missing strategy fields to YAML files
- [ ] Update strategy specs to document YAML-only fields
- [ ] Test strategy execution with new configs

### Phase 4: Infrastructure Documentation (Week 4)
- [ ] Document remaining YAML-only fields in specs
- [ ] Update quality gates to reflect new coverage
- [ ] Validate 100% coverage achieved

## Expected Outcomes

After implementing all recommendations:
- **Coverage**: 100% (87/87 fields synchronized)
- **Orphaned References**: 0
- **Quality Gate Status**: PASS
- **Maintainability**: Improved with clear spec ↔ YAML alignment

## Quality Gate Integration

The simplified quality gate (`test_config_spec_yaml_sync_quality_gates.py`) will automatically validate:
- Spec fields are present in YAML configs
- YAML fields are documented in specs
- No orphaned references exist

This provides a maintainable validation system focused on the canonical sources (specs and YAML configs) without the complexity of maintaining a comprehensive reference document.

## Conclusion

The current 72.4% coverage represents a solid foundation after simplifying the validation system. The identified gaps are primarily in venue configuration, component configuration, and strategy-specific fields. Addressing these gaps will improve system reliability, developer experience, and configuration maintainability.

The simplified quality gate system provides a clear path to 100% coverage while maintaining focus on the canonical sources of truth: component specifications and YAML configuration files.
