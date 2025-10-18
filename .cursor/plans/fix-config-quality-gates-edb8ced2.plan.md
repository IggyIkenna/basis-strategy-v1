<!-- edb8ced2-4a0b-45a9-975e-df8eac2e9e3a 65f2bf10-947b-4c43-a3de-9a0c12bc10ce -->
# Fix Config Field Mismatches and Update Analysis Document

## Overview

Address the remaining 52.3% gap in config documentation sync by fixing field name mismatches between component specs and 19_CONFIGURATION.md, then provide comprehensive documentation update.

## Current Status Analysis

### Mismatch Categories

**Category 1: Fields in 19_CONFIGURATION.MD but NOT in specs (57 fields)**

These are fields that exist in the config documentation but are not properly documented in component/strategy specs:

- **Top-level config fields**: `base_currency`, `initial_capital`, `environment`, `execution_mode`, `log_level`, `validation_strict`
- **Strategy-specific fields**: `allows_hedging`, `basis_trading_supported`, `leverage_enabled`, `leverage_supported`, `market_neutral`, `max_drawdown`, `max_leverage`, `max_ltv`, `position_deviation_threshold`, `rewards_mode`, `stake_allocation_percentage`, `staking_supported`
- **ML config fields**: `ml_config`, `ml_config.candle_interval`, `ml_config.model_name`, `ml_config.model_registry`, `model_name`, `model_registry`, `model_version`, `signal_threshold`, `max_position_size`
- **Data fields**: `candle_interval`, `data_requirements`
- **Event logger fields**: `event_logger`, `event_logger.*` (9 fields)
- **Component parent fields**: `component_config`, `execution_manager`, `exposure_monitor`, `pnl_monitor`, `results_store`, `risk_monitor`, `strategy_manager`
- **Venue parent fields**: `venues`, `instruments`
- **Other fields**: `decimal_places`, `delta_tolerance`, `description`, `funding_threshold`, `hedge_allocation_bybit`, `hedge_venues`, `risk_level`, `supported_strategies`, `target_apy_range`, `type`

**Category 2: Fields in specs but NOT in 19_CONFIGURATION.MD (35 fields)**

These are fields documented in component specs but missing from 19_CONFIGURATION.MD:

- **Execution manager action mappings**: `component_config.execution_manager.action_mapping`, `*.entry_partial`, `*.exit_partial`, `*.open_perp_short`, `*.open_perp_long`, `*.close_perp`, `*.supported_actions` (7 fields)
- **Exposure monitor conversion methods**: `component_config.exposure_monitor.conversion_methods.BTC`, `.ETH`, `.USDT`, `.aWeETH`, `.weETH`, `.KING`, `.EIGEN`, `.ETHFI`, `.variableDebtWETH`, `.BTC_PERP`, `.ETH_PERP`, `.exposure_currency`, `.track_assets` (13 fields)
- **Results store fields**: `component_config.results_store.delta_tracking_assets`, `.dust_tracking_tokens`, `.funding_tracking_venues`, `.leverage_tracking`, `.pnl_attribution_types`, `.result_types` (6 fields)
- **Risk monitor fields**: `component_config.risk_monitor.enabled_risk_types`, `.risk_limits` (2 fields)
- **Strategy factory fields**: `component_config.strategy_factory.max_retries`, `.validation_strict` (2 fields)
- **Venue-specific fields**: `venues.binance.min_amount`, `venues.bybit.max_leverage`, `venues.bybit.min_amount`, `venues.okx.max_leverage`, `venues.okx.min_amount` (5 fields)

## Implementation Plan

### Phase 1: Add Missing Top-Level Fields to Strategy Specs (High Priority)

**Problem**: Top-level fields like `base_currency`, `initial_capital`, `environment`, `execution_mode`, `log_level`, `validation_strict` are documented in 19_CONFIGURATION.md but not extracted from strategy specs.

**Root Cause**: These fields are documented in specs but the current extraction logic filters them out or they're formatted differently.

**Solution**: Verify these fields are properly formatted with `**field_name**:` pattern in all strategy specs.

**Files to update**:

- All 9 strategy specs in `docs/specs/strategies/`

### Phase 2: Add Missing Strategy-Specific Fields to Strategy Specs (High Priority)

**Problem**: Strategy-specific fields like `allows_hedging`, `basis_trading_supported`, `leverage_enabled`, etc. are in 19_CONFIGURATION.md but not in strategy specs.

**Root Cause**: These fields are documented without the `**field_name**:` pattern, so they're not being extracted.

**Solution**: Ensure all strategy-specific fields use the proper markdown format `**field_name**: type - description`.

**Fields to add to strategy specs**:

- `allows_hedging` → USDT Market Neutral strategies
- `basis_trading_supported` → Basis strategies
- `leverage_enabled`, `leverage_supported`, `max_leverage` → Leveraged strategies
- `market_neutral` → Market neutral strategies
- `max_drawdown`, `max_ltv`, `position_deviation_threshold` → All strategies
- `rewards_mode`, `stake_allocation_percentage`, `staking_supported` → Staking strategies
- `hedge_allocation_bybit`, `hedge_venues` → Basis and market neutral strategies

### Phase 3: Add Missing ML Fields to ML Strategy Specs (High Priority)

**Problem**: ML config fields are in 19_CONFIGURATION.md but not properly extracted from ML strategy specs.

**Solution**: Ensure ML strategy specs document all `ml_config.*` fields with proper format.

**Files to update**:

- `docs/specs/strategies/08_ML_BTC_DIRECTIONAL_STRATEGY.md`
- `docs/specs/strategies/09_ML_USDT_DIRECTIONAL_STRATEGY.md`

**Fields to verify**:

- `ml_config.candle_interval`
- `ml_config.model_name`
- `ml_config.model_registry`
- `ml_config.signal_threshold` (currently documented as just `signal_threshold`)
- `ml_config.max_position_size` (currently documented as just `max_position_size`)

### Phase 4: Add Missing Event Logger Fields to Event Logger Spec (Medium Priority)

**Problem**: Event logger fields are in 19_CONFIGURATION.md but not extracted from `08_EVENT_LOGGER.md`.

**Solution**: Ensure all event logger fields use proper `**field_name**:` format.

**File to update**: `docs/specs/08_EVENT_LOGGER.md`

**Fields to verify** (9 fields):

- `event_logger` (parent field)
- `event_logger.event_categories`
- `event_logger.event_filtering`
- `event_logger.event_logging_settings`
- `event_logger.log_format`
- `event_logger.log_level`
- `event_logger.log_path`
- `event_logger.log_retention_policy`
- `event_logger.logging_requirements`

### Phase 5: Add Component Parent Fields to Component Specs (Low Priority)

**Problem**: Parent fields like `component_config`, `execution_manager`, `exposure_monitor`, etc. are in 19_CONFIGURATION.md but not extracted.

**Root Cause**: These are parent dictionary fields that may not need to be individually documented in specs since their nested fields are documented.

**Solution**: Either:

1. Add parent fields to specs with `**component_config**: Dict - Component configuration`
2. OR update field classifier to mark these as "parent only" fields that don't need spec documentation

**Recommendation**: Option 2 - Update field classifier to exclude parent-only fields from quality gate checks.

### Phase 6: Add Missing Fields to 19_CONFIGURATION.MD (High Priority)

**Problem**: 35 fields are documented in component specs but missing from 19_CONFIGURATION.md.

**Solution**: Add these fields to the appropriate sections of 19_CONFIGURATION.md.

**Fields to add**:

**Execution Manager Section**:

```markdown
**component_config.execution_manager.action_mapping**: Dict[str, List[str]] - Maps strategy actions to venue actions
**component_config.execution_manager.action_mapping.entry_partial**: List[str] - Venue actions for partial entry
**component_config.execution_manager.action_mapping.exit_partial**: List[str] - Venue actions for partial exit
**component_config.execution_manager.action_mapping.open_perp_short**: List[str] - Venue actions for opening perp shorts
**component_config.execution_manager.action_mapping.open_perp_long**: List[str] - Venue actions for opening perp longs
**component_config.execution_manager.action_mapping.close_perp**: List[str] - Venue actions for closing perps
**component_config.execution_manager.supported_actions**: List[str] - List of supported venue actions
```

**Exposure Monitor Section**:

```markdown
**component_config.exposure_monitor.exposure_currency**: str - Currency for exposure calculations
**component_config.exposure_monitor.track_assets**: List[str] - Assets to track for exposure
**component_config.exposure_monitor.conversion_methods.BTC**: str - BTC conversion method
**component_config.exposure_monitor.conversion_methods.ETH**: str - ETH conversion method
**component_config.exposure_monitor.conversion_methods.USDT**: str - USDT conversion method
... (and 8 more conversion method fields)
```

**Results Store Section**:

```markdown
**component_config.results_store.result_types**: List[str] - Types of results to store
**component_config.results_store.delta_tracking_assets**: List[str] - Assets for delta tracking
**component_config.results_store.dust_tracking_tokens**: List[str] - Tokens to track as dust
**component_config.results_store.funding_tracking_venues**: List[str] - Venues for funding tracking
**component_config.results_store.leverage_tracking**: bool - Enable leverage tracking
**component_config.results_store.pnl_attribution_types**: List[str] - PnL attribution types
```

**Risk Monitor Section**:

```markdown
**component_config.risk_monitor.enabled_risk_types**: List[str] - Enabled risk types
**component_config.risk_monitor.risk_limits**: Dict - Risk limits configuration
```

**Strategy Factory Section**:

```markdown
**component_config.strategy_factory.max_retries**: int - Maximum retry attempts
**component_config.strategy_factory.validation_strict**: bool - Strict validation mode
```

**Venue Configuration Section**:

```markdown
**venues.binance.min_amount**: float - Minimum order amount for Binance
**venues.bybit.min_amount**: float - Minimum order amount for Bybit
**venues.bybit.max_leverage**: float - Maximum leverage for Bybit
**venues.okx.min_amount**: float - Minimum order amount for OKX
**venues.okx.max_leverage**: float - Maximum leverage for OKX
```

### Phase 7: Update ENHANCED_CONFIG_VIOLATIONS_ANALYSIS.MD

Create comprehensive status report documenting:

1. **Implementation Progress Summary**

   - Initial state: 0.9% coverage
   - Current state: 47.7% coverage
   - Target state: 100% coverage

2. **Completed Work**

   - Fixed quality gate extraction (blocking issue resolved)
   - Added Config Fields Used sections to all 15 component specs
   - Added Config Fields Used sections to all 9 strategy specs
   - Improved field filtering and extraction logic

3. **Remaining Work Analysis**

   - 57 fields in 19_CONFIGURATION.md not in specs (categorized by type)
   - 35 fields in specs not in 19_CONFIGURATION.md (categorized by component)
   - Detailed breakdown of each field with target location and priority

4. **Root Cause Analysis**

   - Field name formatting inconsistencies
   - Parent vs nested field documentation patterns
   - ML config field naming conventions
   - Strategy-specific field placement

5. **Recommended Next Steps**

   - Phase-by-phase implementation guide
   - Estimated effort per phase
   - Priority ordering
   - Expected quality gate impact

6. **Quality Gate Metrics Projection**

   - Current: 47.7% coverage, 92 orphaned
   - After Phase 1-3: ~75% coverage, ~50 orphaned (estimated)
   - After Phase 4-6: ~95% coverage, ~10 orphaned (estimated)
   - After all phases: 100% coverage, 0 orphaned (target)

## Success Criteria

- All strategy-specific fields properly documented in strategy specs
- All ML config fields properly formatted in ML strategy specs
- All component config fields added to 19_CONFIGURATION.md
- Quality gate coverage improved to >80%
- ENHANCED_CONFIG_VIOLATIONS_ANALYSIS.md updated with comprehensive status

## Estimated Effort

- Phase 1: 30 minutes (verify/fix field formatting in strategy specs)
- Phase 2: 1 hour (add strategy-specific fields to specs)
- Phase 3: 30 minutes (fix ML fields in ML strategy specs)
- Phase 4: 20 minutes (fix event logger fields)
- Phase 5: 15 minutes (decide on parent fields approach)
- Phase 6: 1 hour (add missing fields to 19_CONFIGURATION.md)
- Phase 7: 30 minutes (update analysis document)
- **Total**: ~4 hours

## Files to Modify

**Component Specs**:

- `docs/specs/08_EVENT_LOGGER.md`

**Strategy Specs** (all 9):

- `docs/specs/strategies/01_pure_lending_usdt_STRATEGY.md`
- `docs/specs/strategies/02_BTC_BASIS_STRATEGY.md`
- `docs/specs/strategies/03_ETH_BASIS_STRATEGY.md`
- `docs/specs/strategies/04_ETH_STAKING_ONLY_STRATEGY.md`
- `docs/specs/strategies/05_ETH_LEVERAGED_STRATEGY.md`
- `docs/specs/strategies/06_USDT_MARKET_NEUTRAL_NO_LEVERAGE_STRATEGY.md`
- `docs/specs/strategies/07_USDT_MARKET_NEUTRAL_STRATEGY.md`
- `docs/specs/strategies/08_ML_BTC_DIRECTIONAL_STRATEGY.md`
- `docs/specs/strategies/09_ML_USDT_DIRECTIONAL_STRATEGY.md`

**Configuration Documentation**:

- `docs/specs/19_CONFIGURATION.md`

**Analysis Document**:

- `ENHANCED_CONFIG_VIOLATIONS_ANALYSIS.md`

**Quality Gate Script** (if needed):

- `scripts/test_config_documentation_sync_quality_gates.py`

### To-dos

- [ ] Verify and fix field formatting in all strategy specs to use **field_name**: pattern
- [ ] Add missing strategy-specific fields to appropriate strategy specs
- [ ] Fix ML config fields in ML strategy specs to use proper ml_config.* naming
- [ ] Fix event logger fields in 08_EVENT_LOGGER.md
- [ ] Decide approach for parent fields (update specs or exclude from quality gate)
- [ ] Add 35 missing fields to docs/specs/19_CONFIGURATION.md
- [ ] Update ENHANCED_CONFIG_VIOLATIONS_ANALYSIS.md with comprehensive status report
- [ ] Run quality gates and validate >80% coverage achieved