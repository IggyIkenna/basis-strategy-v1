<!-- 4928a2b4-2cb4-4040-805f-041aa916eca5 77b21399-be98-41d1-8201-2dfc720d2dd6 -->
# Configuration Quality Gate 100% Compliance Plan

## Overview

Achieve 100% configuration quality gate compliance by systematically addressing all 108 config violations through documentation updates, quality gate enhancements, and field classifier fixes.

## Phase 1: Remove Unused Fields from 19_CONFIGURATION.md

**Target**: `docs/specs/19_CONFIGURATION.md`

Remove the following unused event logger fields:

- `event_logger.audit_requirements`
- `event_logger.compliance_settings`

These fields are not used in the codebase and should be removed from documentation.

## Phase 2: Update Component Specs (Venues, Event Logger, Core Components)

### 2.1 Venue-Related Component Specs (31 fields)

**Update `docs/specs/07A_VENUE_INTERFACES.md`**:

Add "Config Fields Used" section documenting venue-specific configuration fields for each venue interface (AAVE v3, Alchemy, Binance, Bybit, Etherfi, OKX).

**Update `docs/specs/07_VENUE_INTERFACE_MANAGER.md`**:

Add "Config Fields Used" section documenting the top-level `venues` configuration object and shared venue management fields.

**Update `docs/specs/07B_VENUE_INTERFACE_FACTORY.md`**:

Add "Config Fields Used" section documenting venue factory configuration fields used for creating venue instances.

### 2.2 Event Logger Spec (9 remaining fields)

**Update `docs/specs/08_EVENT_LOGGER.md`**:

Add "Config Fields Used" section documenting remaining event logger configuration fields (excluding the 2 removed in Phase 1):

- `event_logger`, `event_logger.event_categories`, `event_logger.event_filtering`, `event_logger.event_logging_settings`, `event_logger.log_format`, `event_logger.log_level`, `event_logger.log_path`, `event_logger.log_retention_policy`, `event_logger.logging_requirements`

### 2.3 Core Component Specs (26 fields)

**Update the following component specs** with "Config Fields Used" sections:

- `docs/specs/05_STRATEGY_MANAGER.md` - Add `component_config.strategy_manager.*` fields
- `docs/specs/03_RISK_MONITOR.md` - Add `component_config.risk_monitor.*` fields
- `docs/specs/04_pnl_monitor.md` - Add `component_config.pnl_monitor.*` fields
- `docs/specs/06_VENUE_MANAGER.md` - Add `component_config.execution_manager.*` fields
- `docs/specs/02_EXPOSURE_MONITOR.md` - Add `component_config.exposure_monitor.*` fields
- `docs/specs/18_RESULTS_STORE.md` - Add `component_config.results_store.*` fields
- `docs/specs/5A_STRATEGY_FACTORY.md` - Add `component_config.strategy_factory.*` fields
- `docs/specs/09_DATA_PROVIDER.md` - Add data-related fields (`data_requirements`, `candle_interval`, `model_name`, `model_registry`, `model_version`)
- `docs/specs/16_MATH_UTILITIES.md` - Add math-related fields (`decimal_places`, `funding_threshold`)

## Phase 3: Update Strategy Specs (20 fields)

**Update individual strategy specs** in `docs/specs/strategies/`:

- `01_pure_lending_usdt_STRATEGY.md` - Add config fields: `max_drawdown`, `max_ltv`, `position_deviation_threshold`
- `02_BTC_BASIS_STRATEGY.md` - Add config fields: `basis_trading_supported`, `hedge_allocation_bybit`, `hedge_venues`
- `03_ETH_BASIS_STRATEGY.md` - Add config fields: `basis_trading_supported`, `hedge_allocation_bybit`, `hedge_venues`
- `04_ETH_STAKING_ONLY_STRATEGY.md` - Add config fields: `staking_supported`, `rewards_mode`, `stake_allocation_percentage`
- `05_ETH_LEVERAGED_STRATEGY.md` - Add config fields: `leverage_enabled`, `leverage_supported`, `max_leverage`, `staking_supported`
- `06_USDT_MARKET_NEUTRAL_NO_LEVERAGE_STRATEGY.md` - Add config fields: `market_neutral`, `allows_hedging`
- `07_USDT_MARKET_NEUTRAL_STRATEGY.md` - Add config fields: `market_neutral`, `allows_hedging`, `leverage_enabled`
- `08_ML_BTC_DIRECTIONAL_STRATEGY.md` - Add config fields: `ml_config.*` fields
- `09_ML_USDT_DIRECTIONAL_STRATEGY.md` - Add config fields: `ml_config.*` fields

Each strategy spec should add a "Config Fields Used" section listing strategy-specific configuration fields.

## Phase 4: Enhance Quality Gate Script

**Update `scripts/test_config_documentation_sync_quality_gates.py`**:

Modify the `extract_config_fields_from_component_specs()` method to:

1. Scan top-level specs: `docs/specs/*.md` (existing behavior)
2. **NEW**: Scan strategy specs: `docs/specs/strategies/*.md`

**Implementation**:

```python
# After scanning top-level specs (line 221-262)
# Add strategy specs scanning:
strategies_dir = self.specs_dir / "strategies"
if strategies_dir.exists():
    for strategy_file in strategies_dir.glob("*.md"):
        # Apply same extraction logic as component specs
        component_name = strategy_file.stem
        config_fields = set()
        # ... (same extraction patterns)
        if config_fields:
            component_configs[component_name] = config_fields
```

Remove suppressed threshold at line 283 by changing:

```python
min_coverage_threshold = 100.0  # Already set to 100%, keep this
```

And at line 365, change:

```python
max_orphaned_threshold = 0.0  # Change from 90.0 to 0.0 (no orphaned allowed)
```

## Phase 5: Fix Field Classifier

**Update `scripts/config_field_classifier.py`**:

Review and fix venue field detection issues to ensure all YAML fields are properly detected and classified. Specifically:

1. Verify `FIXED_SCHEMA_DICTS['venues']` includes all venue fields (lines 70-82)
2. Ensure venue wildcards (`venues.*.enabled`, `venues.*.instruments`, etc.) are properly matched
3. Test field detection against actual YAML files to validate accuracy

## Validation

After completing all phases, run the following to validate 100% compliance:

```bash
# Run configuration quality gates
python3 scripts/run_quality_gates.py --category configuration

# Expected results:
# - Config Documentation Sync: PASS (100%)
# - Component Spec Sync: PASS (100%)
# - Orphaned References: PASS (0 orphaned)
# - Overall Status: PASS
```

## Success Criteria

- All 108 config violations resolved
- Config Documentation Sync: 100% coverage
- Config Usage Sync: 100% coverage
- No orphaned references (0%)
- No suppressed thresholds in quality gates
- All quality gate tests pass without warnings

### To-dos

- [ ] Remove unused event logger fields (audit_requirements, compliance_settings) from 19_CONFIGURATION.md
- [ ] Update venue-related component specs (07A, 07, 07B) with Config Fields Used sections for 31 venue fields
- [ ] Update 08_EVENT_LOGGER.md with Config Fields Used section for 9 remaining event logger fields
- [ ] Update 9 core component specs with Config Fields Used sections for 26 component config fields
- [ ] Update 9 strategy specs with Config Fields Used sections for 20 strategy-specific fields
- [ ] Enhance quality gate script to scan strategy specs and remove suppressed thresholds
- [ ] Fix field classifier venue field detection issues
- [ ] Run configuration quality gates to validate 100% compliance