<!-- 29ad27a3-9508-4126-b88d-8f802c21c2c7 f226ef69-e471-4841-bb21-b7f353df56bc -->
# Instrument Key Format Standardization Plan

## Current State

**INSTRUMENT_DEFINITIONS.md already exists** and is comprehensive! It defines:

- Canonical format: `venue:position_type:symbol`
- All position types: BaseToken, aToken, debtToken, Perp, LST
- **LST clarification**: LST (Liquid Staking Token) is tracked like BaseToken in Position Monitor but requires different market data lookup (oracle/conversion rates)
- All venues: wallet, binance, bybit, okx, aave_v3, etherfi, lido, morpho
- Complete symbol lists for all 9 strategy modes
- Parsing rules, validation, and migration guides

**Current Usage**:

- 583 matches of canonical format in 40 files (grep results)
- 5 files still reference deprecated terms (instrument_id, instrument_key, position_id)
- 751 potential format inconsistencies to review (dot notation, missing position_type, etc.)
- Already referenced in some docs (REFERENCE_ARCHITECTURE_CANONICAL.md, EXPOSURE_MONITOR.md)

## Implementation Steps

### Phase 1: Scan and Identify Inconsistencies

**Run comprehensive scan script**:

```bash
python scripts/scan_instrument_key_inconsistencies.py
```

This will:

- Scan all backend Python code (`backend/**/*.py`)
- Scan all frontend TypeScript code (`frontend/**/*.ts`, `frontend/**/*.tsx`)
- Scan all configs (`configs/**/*.yaml`)
- Scan all documentation (`docs/**/*.md`)
- Scan all tests (`tests/**/*.py`)
- Scan all scripts (`scripts/**/*.py`)

**Generates**:

- `instrument_key_INCONSISTENCIES_REPORT.md` - Human-readable report
- `instrument_key_inconsistencies.json` - Machine-readable data

**Identifies**:

1. Deprecated variable names: `instrument_id`, `instrument_key`, `position_id`, `asset_id`, `asset_key`
2. Deprecated format patterns:

                                                                                                                                                                                                                                                                                                                                                                                                - Dot notation: `wallet.USDT`, `binance.BTC`
                                                                                                                                                                                                                                                                                                                                                                                                - Missing position_type: `binance:USDT`, `aave:aUSDT`
                                                                                                                                                                                                                                                                                                                                                                                                - Underscore format: `binance_BTC_USDT`

3. Inconsistent documentation references

### Phase 2: Update INSTRUMENT_DEFINITIONS.md

**Enhancements** (if needed after scan):

- Add "Last Updated" timestamp with current date (October 16, 2025)
- Add cross-references to all component specs that use position keys
- Add quality gate validation section
- Add troubleshooting/FAQ section for common migration issues
- Ensure all 9 strategy modes are documented (already done)

**Key files**:

- `docs/INSTRUMENT_DEFINITIONS.md`

### Phase 3: Update All Documentation

**Update every doc in `docs/` to**:

1. Reference INSTRUMENT_DEFINITIONS.md for position key format
2. Use canonical format in all examples
3. Replace deprecated terminology
4. Add canonical source references section

**Documentation files to update** (~40 files):

**Core docs**:

- `docs/README.md`
- `docs/INDEX.md`
- `docs/GETTING_STARTED.md`
- `docs/USER_GUIDE.md`
- `docs/DEPLOYMENT_GUIDE.md`
- `docs/API_DOCUMENTATION.md`
- `docs/MODES.md`
- `docs/WORKFLOW_GUIDE.md`
- `docs/TIGHT_LOOP_ARCHITECTURE.md`
- `docs/VENUE_EXECUTION_CONFIG_GUIDE.md`
- `docs/CODE_STRUCTURE_PATTERNS.md`
- `docs/ERROR_HANDLING_PATTERNS.md`
- `docs/HEALTH_ERROR_SYSTEMS.md`
- `docs/QUALITY_GATES.md`

**Component specs** (all 20):

- `docs/specs/01_POSITION_MONITOR.md` (already updated)
- `docs/specs/02_EXPOSURE_MONITOR.md` (already references it)
- `docs/specs/03_RISK_MONITOR.md`
- `docs/specs/04_PNL_MONITOR.md`
- `docs/specs/05_STRATEGY_MANAGER.md`
- `docs/specs/06_VENUE_MANAGER.md`
- `docs/specs/07_VENUE_INTERFACE_MANAGER.md`
- `docs/specs/07A_VENUE_INTERFACES.md`
- `docs/specs/07B_EXECUTION_INTERFACES.md`
- `docs/specs/07B_VENUE_INTERFACE_FACTORY.md`
- `docs/specs/08_EVENT_LOGGER.md`
- `docs/specs/09_DATA_PROVIDER.md`
- `docs/specs/10_RECONCILIATION_COMPONENT.md`
- `docs/specs/11_POSITION_UPDATE_HANDLER.md`
- `docs/specs/12_FRONTEND_SPEC.md`
- `docs/specs/13_BACKTEST_SERVICE.md`
- `docs/specs/14_LIVE_TRADING_SERVICE.md`
- `docs/specs/15_EVENT_DRIVEN_STRATEGY_ENGINE.md`
- `docs/specs/16_MATH_UTILITIES.md`
- `docs/specs/18_RESULTS_STORE.md`
- `docs/specs/19_CONFIGURATION.md`
- `docs/specs/20_UTILITY_MANAGER.md`
- `docs/specs/5A_STRATEGY_FACTORY.md`
- `docs/specs/5B_BASE_STRATEGY_MANAGER.md`

**Strategy specs** (all 9):

- `docs/specs/strategies/01_pure_lending_usdt_STRATEGY.md`
- `docs/specs/strategies/02_BTC_BASIS_STRATEGY.md`
- `docs/specs/strategies/03_ETH_BASIS_STRATEGY.md`
- `docs/specs/strategies/04_ETH_STAKING_ONLY_STRATEGY.md`
- `docs/specs/strategies/05_ETH_LEVERAGED_STRATEGY.md`
- `docs/specs/strategies/06_USDT_MARKET_NEUTRAL_NO_LEVERAGE_STRATEGY.md`
- `docs/specs/strategies/07_USDT_MARKET_NEUTRAL_STRATEGY.md`
- `docs/specs/strategies/08_ML_BTC_DIRECTIONAL_STRATEGY.md`
- `docs/specs/strategies/09_ML_USDT_DIRECTIONAL_STRATEGY.md`

**Standard update pattern**:

```markdown
## 📚 **Canonical Sources**

**Instrument Definitions**: [../INSTRUMENT_DEFINITIONS.md](../INSTRUMENT_DEFINITIONS.md) - Canonical position key format (`venue:position_type:symbol`)
```

### Phase 4: Fix Backend Code Inconsistencies

**Scan results will identify specific files**, but expected fixes:

**Deprecated variable name replacements**:

```python
# Replace in all Python files
instrument_id → position_key
instrument_key → position_key
position_id → position_key
asset_id → position_key (if used for positions)
asset_key → position_key (if used for positions)
```

**Deprecated format fixes**:

```python
# Dot notation
"wallet.USDT" → "wallet:BaseToken:USDT"
"binance.BTC" → "binance:BaseToken:BTC"

# Missing position_type
"binance:USDT" → "binance:BaseToken:USDT"
"aave:aUSDT" → "aave_v3:aToken:aUSDT"

# Underscore format
"binance_BTC_USDT" → "binance:Perp:BTCUSDT"
```

**Key components likely needing updates** (based on grep):

- `backend/src/basis_strategy_v1/core/components/position_monitor.py`
- `backend/src/basis_strategy_v1/core/components/exposure_monitor.py`
- `backend/src/basis_strategy_v1/core/components/pnl_monitor.py`
- `backend/src/basis_strategy_v1/core/components/risk_monitor.py`
- `backend/src/basis_strategy_v1/core/utilities/utility_manager.py`
- `backend/src/basis_strategy_v1/core/execution/execution_manager.py`
- All strategy files in `backend/src/basis_strategy_v1/core/strategies/`
- All interface files in `backend/src/basis_strategy_v1/core/interfaces/`
- All data providers in `backend/src/basis_strategy_v1/infrastructure/data/`

### Phase 5: Fix Frontend Code Inconsistencies

**Frontend TypeScript** (if needed):

- Update type definitions in `frontend/src/types/index.ts`
- Replace deprecated variable names
- Use canonical format in all API responses
- Update UI components that display position keys

### Phase 6: Update Configuration Files

**Review and update** (based on scan results):

- All mode configs: `configs/modes/*.yaml`
- Ensure `position_subscriptions` use canonical format
- Verify venue configurations reference correct position types

**Example validation**:

```yaml
component_config:
  position_monitor:
    position_subscriptions:
   - "wallet:BaseToken:USDT"  # ✅ Correct
   - "binance:BaseToken:BTC"  # ✅ Correct
   - "binance:Perp:BTCUSDT"   # ✅ Correct
      # NOT: "wallet.USDT" or "binance:USDT"
```

### Phase 7: Update Tests

**Update all test files** in `tests/`:

- Replace deprecated variable names
- Use canonical format in test data
- Update assertions to expect canonical format
- Add tests for position key validation

**Key test files** (based on grep):

- `tests/unit/test_position_monitor_refactor.py`
- `tests/unit/test_data_provider_unit.py`
- `tests/unit/test_historical_data_provider_unit.py`
- `tests/unit/test_btc_basis_strategy_unit.py`
- `tests/unit/test_eth_basis_strategy_unit.py`
- All other strategy and component tests

### Phase 8: Update Quality Gates

**Add/update quality gate validation**:

- Leverage existing `scripts/quality_gates/validate_position_key_format.py`
- Integrate into `tests/quality_gates/run_quality_gates.py`
- Add checks for:
                                                                                                                                                                                                                                                                - Deprecated variable names in code
                                                                                                                                                                                                                                                                - Deprecated format patterns in configs
                                                                                                                                                                                                                                                                - Missing INSTRUMENT_DEFINITIONS.md references in docs
                                                                                                                                                                                                                                                                - Canonical format in all position_subscriptions

**Update**:

- `scripts/quality_gates/validate_position_key_format.py` (already exists)
- `tests/quality_gates/run_quality_gates.py` - add new validation
- `docs/QUALITY_GATES.md` - document new checks

### Phase 9: Verification

**Run quality gates**:

```bash
python tests/quality_gates/run_quality_gates.py --category all
```

**Run tests**:

```bash
pytest tests/ -v
```

**Verify fixes**:

```bash
python scripts/scan_instrument_key_inconsistencies.py
# Should show 0 issues
```

**Manual verification**:

- Review updated documentation for consistency
- Check that all component specs reference INSTRUMENT_DEFINITIONS.md
- Verify configs use canonical format
- Confirm code uses `position_key` variable name exclusively

## Key Files to Create/Modify

**New files**:

- `scripts/scan_instrument_key_inconsistencies.py` ✅ (created)
- `instrument_key_INCONSISTENCIES_REPORT.md` (generated by script)
- `instrument_key_inconsistencies.json` (generated by script)

**Files to update**:

- `docs/INSTRUMENT_DEFINITIONS.md` - Add timestamp, enhance if needed
- ~40 documentation files in `docs/` - Add canonical source references
- ~66 backend Python files - Replace deprecated patterns
- ~8 config files in `configs/modes/` - Verify canonical format
- ~30 test files - Update to canonical format
- Quality gate scripts - Add validation

## Success Criteria

1. ✅ Scanning script runs successfully and generates report
2. ✅ INSTRUMENT_DEFINITIONS.md is comprehensive and up-to-date
3. ✅ All docs reference INSTRUMENT_DEFINITIONS.md in canonical sources section
4. ✅ Zero deprecated variable names (`instrument_id`, etc.) in codebase
5. ✅ Zero deprecated format patterns (dot notation, missing position_type) in code
6. ✅ All configs use canonical format in position_subscriptions
7. ✅ All tests pass with canonical format
8. ✅ Quality gates pass with new validation checks
9. ✅ Scan report shows 0 inconsistencies
10. ✅ Documentation is consistent and cross-referenced

## Estimated Scope

- **Documentation updates**: ~40 files
- **Backend code fixes**: ~66 Python files (varies by scan results)
- **Frontend code fixes**: ~0 files (no matches found)
- **Config updates**: ~8 YAML files (verification only)
- **Test updates**: ~30 test files
- **Quality gate updates**: 2-3 scripts

This is a comprehensive refactoring but with the scanning script, we can systematically identify and fix all inconsistencies across the entire codebase.

### To-dos

- [ ] Run scan_instrument_key_inconsistencies.py to identify all format inconsistencies across codebase
- [ ] Update INSTRUMENT_DEFINITIONS.md with current timestamp, add LST position type, and any enhancements based on scan results
- [ ] Update core documentation files (README, INDEX, GETTING_STARTED, USER_GUIDE, etc.) to reference INSTRUMENT_DEFINITIONS.md
- [ ] Update all 20 component specs to reference INSTRUMENT_DEFINITIONS.md in canonical sources section
- [ ] Update all 9 strategy specs to reference INSTRUMENT_DEFINITIONS.md and use canonical format
- [ ] Fix all backend code inconsistencies: replace deprecated variable names and format patterns
- [ ] Verify all mode configs use canonical format in position_subscriptions
- [ ] Update all test files to use canonical format and replace deprecated patterns
- [ ] Update quality gate scripts to validate position key format compliance
- [ ] Run quality gates, tests, and rescan to verify all inconsistencies are fixed