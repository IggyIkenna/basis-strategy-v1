# Task-Docs Conflict Analysis Report - Updated

**Date**: October 10, 2025  
**Scope**: All 28 task files vs all 35 documentation files  
**Analysis Type**: Hybrid format - Summary of resolved conflicts + detailed remaining architectural violations  
**Companion Document**: [DEVIATIONS_AND_CORRECTIONS.md](docs/DEVIATIONS_AND_CORRECTIONS.md) - Current architectural violations in codebase

---

## Executive Summary

**MAJOR DOCUMENTATION ALIGNMENT COMPLETED** (October 9-10, 2025): The original 127 conflicts identified in January 2025 have been largely resolved through comprehensive documentation updates. This report now focuses on the **11 remaining architectural violations** in the codebase that require implementation tasks.

### Current Status
- **Resolved Conflicts**: 116+ conflicts (91.3%) - **COMPLETED**
- **Remaining Violations**: 11 architectural violations (8.7%) - **REQUIRE IMPLEMENTATION**
- **Documentation Quality**: ✅ **HIGH** - Consistent, honest, and aligned with codebase
- **Next Priority**: Focus on remaining architectural violations in codebase

### Major Resolutions Completed (October 9-10, 2025)
1. **Environment Variable Clarifications** - BASIS_ENVIRONMENT role clarified across all docs
2. **Redis Removal** - Complete removal from user docs, requirements.txt, and pyproject.toml
3. **Implementation Status Honesty** - Honest status with "Known Issues" sections added
4. **Tight Loop Architecture** - Updated all flow diagrams to match ADR-001
5. **Backtest Credential Requirements** - Clear exemption documentation and code implementation
6. **Scenario Directory Cleanup** - All scenario references removed from docs and code
7. **Health System Unification** - Standardized to 2 endpoints only (/health, /health/detailed)
8. **File Path Audit** - All backend file paths verified and accurate

---

## Remaining Architectural Violations (Codebase Implementation Required)

**Source**: [DEVIATIONS_AND_CORRECTIONS.md](docs/DEVIATIONS_AND_CORRECTIONS.md) - Lines 38-222  
**Status**: 11 violations requiring implementation tasks  
**Priority**: 3 HIGH, 6 MEDIUM, 1 LOW

### HIGH Priority Violations (Must Fix Before Production)

#### 1. Async/Await in Component Methods ❌ HIGH PRIORITY
**Violation**: ADR-006 Synchronous Component Execution  
**Affected Files**:
- `position_monitor.py:239` - `async def update()` should be synchronous
- `risk_monitor.py` - 18 async internal methods (lines 485,498,598,666,721,742,781,846,887,932,972,1033,1037,1057,1229,1338,1472,1485)
- `strategy_manager.py` - 9 async internal methods (lines 492,1061,1085,1160,1219,1271,1298,1311,1343)
- `pnl_calculator.py:194` - `async def calculate_pnl()` should be synchronous
- `position_update_handler.py` - 3 async internal methods (lines 105,194,240)

**Canonical Source**: 
- `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-006 Synchronous Component Execution
- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 6 (Async I/O for Non-Critical Path)

**Required Fix**: Remove async/await from all internal component methods. Keep async ONLY for Event Logger, Results Store, and API entry points (BacktestService.run_backtest, LiveTradingService.start_live_trading).

**Status**: TODO-REFACTOR comments present in code  
**Task File**: **NEW TASK NEEDED** - `.cursor/tasks/23_fix_async_await_violations.md`

#### 2. Strategy Manager Architecture ❌ HIGH PRIORITY
**Violation**: ADR-007, Strategy Manager Refactor  
**Affected Files**:
- `strategy_manager.py:1-42` - Missing inheritance-based architecture
- `transfer_manager.py` - 1068 lines, should be REMOVED entirely
- No StrategyFactory implementation

**Canonical Source**:
- `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-007 (11 Component Architecture)
- `docs/MODES.md` - Standardized Strategy Manager Architecture
- `docs/specs/05_STRATEGY_MANAGER.md`

**Required Fix**:
1. DELETE transfer_manager.py
2. Create BaseStrategyManager with 5 standardized actions
3. Create strategy-specific implementations (BTCBasisStrategyManager, etc.)
4. Create StrategyFactory for mode-based instantiation

**Status**: TODO-REMOVE comment in transfer_manager.py, TODO-REFACTOR in strategy_manager.py  
**Task File**: `strategy_manager_refactor.md` (EXISTS - needs update)

#### 3. Generic vs Mode-Specific Violations ❌ HIGH PRIORITY
**Violation**: Canonical Principles Section 7  
**Affected Files**:
- `exposure_monitor.py:1-48` - Mode-specific logic instead of config params
- `pnl_calculator.py:1-37` - Mode-specific P&L calculation
- Components use hardcoded mode checks instead of config parameters

**Canonical Source**:
- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 7 (Generic vs Mode-Specific)
- `docs/specs/02_EXPOSURE_MONITOR.md`
- `docs/specs/04_PNL_CALCULATOR.md`

**Required Fix**: Use config parameters (asset, share_class, lst_type, hedge_allocation) instead of mode-specific if statements

**Status**: TODO-REFACTOR comments in affected files  
**Task File**: `14_mode_agnostic_architecture_requirements.md` + `18_generic_vs_mode_specific_architecture.md` (MERGE NEEDED)

### MEDIUM Priority Violations (Should Fix Soon)

#### 4. Fail-Fast Configuration Violations ❌ MEDIUM PRIORITY
**Violation**: Canonical Principles Section 33  
**Affected Files**:
- `risk_monitor.py` - 62 instances of `.get()` with defaults (lines 272,308-311,314,316-320,331-338,452-459,539,788,1099)

**Canonical Source**:
- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 33 (Fail-Fast Configuration)
- `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-040

**Required Fix**: Use direct config access and let KeyError raise if missing

**Status**: No TODO comments present  
**Task File**: **NEW TASK NEEDED** - `.cursor/tasks/24_implement_fail_fast_configuration.md`

#### 5. Singleton Pattern Not Enforced ❌ MEDIUM PRIORITY
**Violation**: Canonical Principles Section 2  
**Affected Files**:
- `event_driven_strategy_engine.py:1-20` - Components may not properly implement singleton pattern
- Multiple components may create multiple instances

**Canonical Source**:
- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 2 (Singleton Pattern)
- `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-003 (Reference-Based Architecture)

**Required Fix**: Enforce singleton pattern for all 11 components with shared instances

**Status**: TODO-REFACTOR comment present  
**Task File**: `13_singleton_pattern_requirements.md` (EXISTS - needs update)

#### 6. Duplicate Risk Monitor Files ❌ MEDIUM PRIORITY
**Violation**: Single source of truth principle  
**Affected Files**:
- CORRECT: `core/strategies/components/risk_monitor.py`
- REMOVE: `core/rebalancing/risk_monitor.py` (duplicate)

**Canonical Source**:
- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 12 (Duplicate Risk Monitors Consolidation)

**Required Fix**: Delete duplicate file, update imports

**Status**: No TODO comments present  
**Task File**: `21_consolidate_duplicate_risk_monitors.md` (EXISTS - needs update)

#### 7. Tight Loop Architecture Implementation ❌ MEDIUM PRIORITY
**Violation**: ADR-001 Tight Loop Architecture  
**Affected Files**:
- `position_monitor.py:1-20` - Tight loop sequence not enforced
- `position_update_handler.py:1-20` - Tight loop sequence not enforced
- Multiple components with TODO-REFACTOR comments

**Canonical Source**:
- `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-001 Tight Loop Architecture Redefinition
- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 4 (Tight Loop Architecture)

**Required Fix**: Implement proper sequential chain with reconciliation handshake

**Status**: TODO-REFACTOR comments present  
**Task File**: `10_tight_loop_architecture_requirements.md` (EXISTS - needs update)

#### 8. Missing Centralized Utility Manager ❌ MEDIUM PRIORITY
**Violation**: Canonical Principles Section 7  
**Affected Files**:
- `exposure_monitor.py:12-28` - Scattered utility methods
- Multiple components have scattered utility methods

**Canonical Source**:
- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 7 (Centralized Utility Methods)
- `docs/specs/16_MATH_UTILITIES.md`

**Required Fix**: Create UtilityManager component with centralized methods

**Status**: TODO-REFACTOR comment present  
**Task File**: `14_mode_agnostic_architecture_requirements.md` (EXISTS - covers this)

#### 9. Reference-Based Architecture Gaps ❌ MEDIUM PRIORITY
**Violation**: ADR-003 Reference-Based Architecture  
**Affected Files**:
- Multiple components may pass references as runtime parameters
- Components may create own instances

**Canonical Source**:
- `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-003 Reference-Based Architecture
- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 1 (Reference-Based Architecture Pattern)

**Required Fix**: Store references in __init__, never pass as runtime parameters

**Status**: No TODO comments present  
**Task File**: **NEW TASK NEEDED** - `.cursor/tasks/25_fix_reference_based_architecture_gaps.md`

#### 10. Component Data Flow Architecture ❌ MEDIUM PRIORITY
**Violation**: Multiple ADRs  
**Affected Files**:
- Component specifications show inconsistent data flow patterns
- Direct component references instead of parameter-based flow

**Canonical Source**:
- `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-003, ADR-004, ADR-005
- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 1, 2, 3

**Required Fix**: Update all component specifications to use parameter-based data flow

**Status**: No TODO comments present  
**Task File**: **NEW TASK NEEDED** - `.cursor/tasks/26_fix_component_data_flow_architecture.md`

### LOW Priority Violations (Can Defer)

#### 11. Frontend Implementation Gap ❌ LOW PRIORITY
**Violation**: Frontend specification incomplete  
**Affected Files**:
- `frontend/src/components/results/` - Directory is empty
- Missing: ResultsPage, MetricCard, PlotlyChart, EventLogViewer
- Missing: API service layer, type definitions

**Canonical Source**:
- `docs/specs/12_FRONTEND_SPEC.md`

**Required Fix**: Implement missing results components

**Status**: No TODO comments present  
**Task File**: **NEW TASK NEEDED** - `.cursor/tasks/27_complete_frontend_implementation.md`

---

## Task File Mapping Summary

### Existing Tasks (Need Updates)
- `strategy_manager_refactor.md` - Maps to violation #2 (Strategy Manager Architecture)
- `13_singleton_pattern_requirements.md` - Maps to violation #5 (Singleton Pattern)
- `21_consolidate_duplicate_risk_monitors.md` - Maps to violation #6 (Duplicate Risk Monitor)
- `10_tight_loop_architecture_requirements.md` - Maps to violation #7 (Tight Loop Implementation)
- `14_mode_agnostic_architecture_requirements.md` - Maps to violations #3, #8 (Generic vs Mode-Specific, Utility Manager)
- `18_generic_vs_mode_specific_architecture.md` - **MERGE INTO TASK 14** (DRY violation)

### New Tasks Required
- `.cursor/tasks/23_fix_async_await_violations.md` - Violation #1 (Async/Await)
- `.cursor/tasks/24_implement_fail_fast_configuration.md` - Violation #4 (Fail-Fast Config)
- `.cursor/tasks/25_fix_reference_based_architecture_gaps.md` - Violation #9 (Reference-Based Architecture)
- `.cursor/tasks/26_fix_component_data_flow_architecture.md` - Violation #10 (Component Data Flow)
- `.cursor/tasks/27_complete_frontend_implementation.md` - Violation #11 (Frontend Implementation)

---

## Recommendations

### Immediate Actions Required (HIGH Priority)
1. **Fix Async/Await Violations**: Remove async/await from all internal component methods (ADR-006 violation)
2. **Complete Strategy Manager Refactor**: Remove transfer_manager.py, implement inheritance-based architecture
3. **Fix Generic vs Mode-Specific Violations**: Use config-driven parameters instead of mode-specific logic

### High Priority Actions (MEDIUM Priority)
4. **Implement Fail-Fast Configuration**: Replace .get() patterns with direct config access
5. **Enforce Singleton Pattern**: Ensure all 11 components use single instances
6. **Remove Duplicate Risk Monitor**: Delete duplicate file, update imports
7. **Implement Tight Loop Architecture**: Add proper sequential chain with reconciliation handshake
8. **Create Centralized Utility Manager**: Centralize scattered utility methods
9. **Fix Reference-Based Architecture Gaps**: Store references in __init__, never pass as runtime parameters
10. **Fix Component Data Flow Architecture**: Update component specs to use parameter-based data flow

### Low Priority Actions
11. **Complete Frontend Implementation**: Implement missing results components

---

## Success Criteria

### Primary Success Criteria (HIGH Priority)
- [ ] All async/await violations fixed (ADR-006 compliance)
- [ ] Strategy manager refactored with inheritance-based architecture
- [ ] Generic vs mode-specific violations resolved with config-driven parameters

### Secondary Success Criteria (MEDIUM Priority)
- [ ] Fail-fast configuration implemented (no .get() with defaults)
- [ ] Singleton pattern enforced for all 11 components
- [ ] Duplicate risk monitor file removed
- [ ] Tight loop architecture properly implemented
- [ ] Centralized utility manager created
- [ ] Reference-based architecture gaps fixed
- [ ] Component data flow architecture updated

### Tertiary Success Criteria (LOW Priority)
- [ ] Frontend implementation completed
- [ ] All task files updated with correct documentation references
- [ ] No duplicate content across task files (DRY compliance)
- [ ] All references validated and working

---

## Next Steps

### Implementation Roadmap
1. **6-Day Implementation Timeline** - Complete end-to-end implementation
2. **26 Tasks Organized by Day** - From foundation to complete functionality
3. **Strategic Parallelization** - Multiple background agents for efficiency
4. **Quality Gate Integration** - Comprehensive validation throughout

### Task File Structure (26 Tasks)
- **Day 1 (Foundation)**: Tasks 01-03 (Environment, Config, Data)
- **Day 2 (Core Refactors)**: Tasks 06-11 (Architecture violations)
- **Day 3 (Integration)**: Tasks 12-14, 04-05 (Components, API, Health)
- **Day 4 (Strategy Modes)**: Tasks 15-17 (Pure lending, BTC basis, ETH basis)
- **Day 5 (Complex + Tests)**: Tasks 18, 19-23 (USDT market neutral, Unit tests)
- **Day 6 (Frontend + Live)**: Tasks 24-26 (Frontend, Live mode, Quality gates)

### Execution Strategy
1. **Sequential Foundation** (Days 1-2) - Build infrastructure first
2. **Parallel Development** (Days 2-6) - Multiple agents for efficiency
3. **Quality Gate Validation** - After each task and day
4. **Incremental Complexity** - Simple to complex strategy modes
5. **Comprehensive Testing** - Unit tests + E2E validation

### Success Criteria
- **26/26 tasks completed** (100%)
- **20/24 quality gates passing** (83%)
- **80% unit test coverage** achieved
- **4/4 strategy modes** working end-to-end
- **System ready for staging deployment**

This updated analysis provides a complete 6-day implementation roadmap for resolving all architectural violations and achieving full end-to-end functionality.
