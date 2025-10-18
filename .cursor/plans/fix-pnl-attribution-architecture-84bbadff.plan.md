<!-- 84bbadff-154e-463f-ab41-73d78796699f 48a924c7-c6c6-4a39-a9a2-a476a4a91d9a -->
# Fix PnL Monitor Mode-Agnostic Architecture

## Overview

Refactor PnL Monitor to be truly mode-agnostic using config-driven attribution types, implement centralized utility manager usage with quality gates, and clean up orphaned Redis/legacy comments.

## Phase 1: PnL Monitor Config-Driven Attribution (Issue #3)

### 1.1 Update PnL Monitor Implementation

**File**: `backend/src/basis_strategy_v1/core/math/pnl_monitor.py`

**Changes**:

- Remove `_calculate_basis_attribution()` method (mode-specific)
- Keep only `_calculate_default_attribution()` as the universal method
- Ensure all 9 attribution types are implemented:
  - `supply_yield` - AAVE supply interest
  - `borrow_costs` - AAVE borrow costs
  - `staking_yield_oracle` - LST oracle price appreciation
  - `staking_yield_rewards` - Seasonal rewards (EIGEN, ETHFI)
  - `funding_pnl` - Perp funding payments
  - `delta_pnl` - Unhedged exposure P&L
  - `basis_pnl` - Spot-perp spread changes
  - `dust_pnl` - Dust token price movements
  - `transaction_costs` - Gas and fees
- Ensure each attribution method gracefully returns 0.0 when data unavailable
- Update `_calculate_balance_based_pnl()` to use share class currency from exposure monitor

### 1.2 Update Exposure Monitor for Share Class Support

**File**: `backend/src/basis_strategy_v1/core/components/exposure_monitor.py`

**Changes**:

- Ensure exposure output includes both:
  - `total_value_usd`: Total portfolio value in USD
  - `share_class_value`: Total portfolio value in share class currency (USDT or ETH)
- Verify conversion methods use utility manager (not inline conversions)

### 1.3 Fix Mode YAML Configurations

**Files**:

- `configs/modes/pure_lending_usdt_usdt.yaml`
- `configs/modes/btc_basis.yaml`
- `configs/modes/eth_basis.yaml`
- `configs/modes/eth_staking_only.yaml`
- `configs/modes/eth_leveraged.yaml`
- `configs/modes/usdt_market_neutral_no_leverage.yaml`
- `configs/modes/usdt_market_neutral.yaml`

**Changes**:

- Ensure `component_config.pnl_monitor.attribution_types` lists correct attribution types per strategy
- Reference table from `docs/specs/04_pnl_monitor.md` lines 73-83 for correct mappings
- Ensure `reporting_currency` matches `share_class`

### 1.4 Update PnL Monitor Specification

**File**: `docs/specs/04_pnl_monitor.md`

**Changes**:

- Remove any references to mode-specific attribution methods
- Emphasize config-driven attribution in all examples
- Update implementation example to show only `_calculate_default_attribution()`

### 1.5 Update Workflow Guide

**File**: `docs/WORKFLOW_GUIDE.md`

**Changes**:

- Lines 1929-2030: Update P&L Monitor section to reflect config-driven implementation
- Remove any mentions of `_calculate_basis_attribution()` as separate method
- Clarify that attribution is purely config-driven with graceful degradation

### 1.6 Update PnL Monitor Unit Tests

**File**: `tests/unit/test_pnl_monitor_unit.py`

**Changes**:

- Add tests for ALL 9 attribution types individually
- Test `_calculate_balance_based_pnl()` with both USDT and ETH share classes
- Test graceful handling when data is unavailable (should return 0.0)
- Test that only configured attribution types are calculated
- Add integration test calling exposure_monitor.get_current_exposure() for real data

## Phase 2: Centralized Utility Manager Enforcement (Issue #4)

### 2.1 Identify Utility Manager Usage Patterns

**Analysis**:

- Scan codebase for inline utility methods that should use utility_manager:
  - Liquidity index calculations
  - Market price conversions
  - Share class currency conversions
  - Oracle price lookups

### 2.2 Update Components to Use Utility Manager

**Files** (identify during analysis):

- `backend/src/basis_strategy_v1/core/math/pnl_monitor.py`
- `backend/src/basis_strategy_v1/core/components/exposure_monitor.py`
- `backend/src/basis_strategy_v1/core/components/risk_monitor.py`
- Any execution interfaces with utility methods

**Changes**:

- Replace inline calculations with `self.utility_manager.method_name()`
- Ensure all components receive utility_manager reference at init
- Remove hardcoded values (e.g., funding rates, liquidity indexes)

### 2.3 Create Utility Manager Compliance Quality Gate

**File**: `scripts/test_implementation_gap_quality_gates.py`

**Add New Quality Gate**:

```python
def test_utility_manager_compliance(self):
    """Ensure components use centralized utility manager, not inline calculations"""
    # Scan for patterns like:
    # - Direct liquidity index calculations
    # - Inline price conversions
    # - Hardcoded conversion rates
    # Exclude utility_manager.py itself and test files
```

### 2.4 Update Component Specifications

**Files**:

- `docs/specs/02_EXPOSURE_MONITOR.md`
- `docs/specs/03_RISK_MONITOR.md`
- `docs/specs/04_pnl_monitor.md`

**Changes**:

- Add utility_manager to "Component References (Set at Init)" section
- Document which utility methods each component uses
- Show example calls to utility_manager methods

## Phase 3: Remove Orphaned Comments (Issue #5)

### 3.1 Remove Redis-Related Comments

**Search Pattern**: "Redis removed", "Redis publishing removed", "Redis subscription removed"

**Files to Clean**:

- `backend/src/basis_strategy_v1/core/math/pnl_monitor.py` (lines 223, 302, 926-928)
- Any other files with Redis removal comments

**Action**: Delete these orphaned comments entirely

### 3.2 Remove Legacy TODO-REFACTOR Comments

**Files**:

- `backend/src/basis_strategy_v1/core/math/pnl_monitor.py` (lines 1-36, 710-715)
- `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py` (lines 1-21)

**Action**:

- Remove TODO-REFACTOR comments that have been addressed
- Keep only active TODOs that represent actual pending work

### 3.3 Update Documentation References

**Files**:

- `docs/WORKFLOW_GUIDE.md` (lines 2598-2600 - remove Redis comments)
- Any component specs with outdated Redis references

## Phase 4: Integration Testing & Validation

### 4.1 Run PnL Monitor Integration Tests

**Command**: `pytest tests/unit/test_pnl_monitor_unit.py -v`

**Validation**:

- All 9 attribution types tested
- Balance-based P&L works for both USDT and ETH share classes
- Config-driven behavior verified for all 7 strategy modes

### 4.2 Run Utility Manager Compliance Quality Gate

**Command**: `python scripts/test_implementation_gap_quality_gates.py --category utility_manager`

**Validation**:

- No inline utility calculations found (except in utility_manager itself)
- All components use centralized utility methods

### 4.3 Run Full Quality Gate Suite

**Command**: `python scripts/test_implementation_gap_quality_gates.py --all`

**Validation**:

- All existing quality gates still pass
- New utility manager compliance gate passes

## Success Criteria

- [ ] PnL Monitor uses only `_calculate_default_attribution()` with config-driven behavior
- [ ] All 9 attribution types implemented and tested individually
- [ ] Balance-based P&L uses share_class_value from exposure monitor
- [ ] Exposure monitor provides both total_value_usd and share_class_value
- [ ] All 7 mode YAML files have correct attribution_types configured
- [ ] Utility manager used consistently across all components
- [ ] Quality gate enforces utility manager usage
- [ ] All orphaned Redis/legacy comments removed
- [ ] All integration tests pass
- [ ] Documentation updated and consistent

## Files Modified Summary

**Backend Code** (8-10 files):

- pnl_monitor.py
- exposure_monitor.py
- risk_monitor.py (if needed)
- event_driven_strategy_engine.py
- utility_manager.py (enhancements)

**Configuration** (7 files):

- All mode YAML files in configs/modes/

**Documentation** (4-5 files):

- 04_pnl_monitor.md
- 02_EXPOSURE_MONITOR.md
- WORKFLOW_GUIDE.md
- Other component specs as needed

**Tests** (2-3 files):

- test_pnl_monitor_unit.py
- test_implementation_gap_quality_gates.py
- Integration tests

**Total**: ~20-25 files

### To-dos

- [ ] Refactor pnl_monitor.py: remove _calculate_basis_attribution, implement all 9 attribution types in _calculate_default_attribution, update _calculate_balance_based_pnl for share class
- [ ] Update exposure_monitor.py to provide both total_value_usd and share_class_value in exposure output
- [ ] Fix all 7 mode YAML files with correct attribution_types per strategy (reference pnl_monitor.md table)
- [ ] Update test_pnl_monitor_unit.py to test all 9 attribution types individually plus balance-based P&L for both share classes
- [ ] Refactor components to use centralized utility_manager for all conversions (no inline calculations)
- [ ] Create utility manager compliance quality gate in test_implementation_gap_quality_gates.py
- [ ] Remove all orphaned Redis and legacy TODO-REFACTOR comments from entire codebase
- [ ] Update docs: 04_pnl_monitor.md, 02_EXPOSURE_MONITOR.md, WORKFLOW_GUIDE.md for config-driven attribution
- [ ] Run all integration tests and quality gates to validate changes