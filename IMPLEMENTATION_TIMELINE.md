# 6-Day End-to-End Implementation Timeline

## Overview
This document provides a detailed implementation timeline for completing the Basis Strategy v1 platform in 6-7 days using background agents. The timeline is designed to build from foundational infrastructure to complete end-to-end functionality, with strategic parallelization opportunities.

**Date**: October 12, 2025  
**Last Updated**: October 12, 2025  
**Total Tasks**: 43 tasks across 6-7 days  
**Estimated Hours**: 80-100 hours total (50 sequential + 30 parallel)  
**Target Completion**: 6-7 calendar days with 3-5 background agents

---

## Current Status (October 12, 2025)

### Completed Work
- ✅ Documentation alignment (Oct 9-10)
- ✅ Environment switching (Task 01)
- ✅ Config loading & validation (Task 02)
- ✅ Quality gates: 12/24 passing (50%)

### Remaining Architectural Violations
Reference: `docs/DEVIATIONS_AND_CORRECTIONS.md`
- 🔴 High Priority (3): Async/await, Strategy manager refactor, Mode-specific logic
- 🟡 Medium Priority (7): Fail-fast config, Singleton pattern, etc.
- 🟢 Low Priority (1): Frontend implementation

### Quality Gate Status
- **Current**: 12/24 passing (50%)
- **Target**: 19/24 passing (80%)
- **Gap**: 7 quality gates to fix

---

## Day 1: Foundation - Environment, Config, and Data Loading (8 hours)

### Phase 1A: Environment & Configuration Infrastructure (4 hours)
**Goal**: Get startup/deployment working with proper env file switching and fail-fast validation

#### Task 01: Environment File Switching & Fail-Fast (2 hours) ✅ COMPLETED (Oct 10)
- **Agent**: Primary
- **Files**: `backend/src/basis_strategy_v1/infrastructure/config/`, `env.unified`, `env.dev`, `env.staging`, `env.prod`
- **Quality Gate**: `python scripts/run_quality_gates.py --category unit`
- **Success Criteria**:
  - [x] BASIS_ENVIRONMENT switching works (dev/staging/prod)
  - [x] Fail-fast on missing env files
  - [x] Required env variables validated from env.unified
  - [x] Environment overrides work correctly

#### Task 02: Full Config Loading & Validation (2 hours) ✅ COMPLETED (Oct 10)
- **Agent**: Primary (sequential with Task 01)
- **Files**: `backend/src/basis_strategy_v1/core/config/config_loader.py`, `configs/`
- **Quality Gate**: `python scripts/run_quality_gates.py --category unit`
- **Success Criteria**:
  - [x] All YAML files load correctly (modes/venues/share_classes)
  - [x] Pydantic validation works
  - [x] Fail-fast on missing/invalid config fields
  - [x] Cross-reference validation works

### Phase 1B: Data Loading Quality Gates (4 hours)
**Goal**: Validate we have all required data for all modes before proceeding

#### Task 03: Data Loading Quality Gate (4 hours)
- **Agent**: Primary (can run parallel with Phase 2A setup)
- **Files**: `tests/unit/test_data_provider_unit.py` (NEW)
- **Quality Gate**: `python scripts/run_quality_gates.py --category unit`
- **Success Criteria**:
  - [ ] All data files exist and are accessible
  - [ ] Data completeness validated for all strategy modes
  - [ ] Data alignment and timestamps validated
  - [ ] Data quality metrics meet thresholds

**Day 1 Success Criteria**:
- [x] Environment switching working (dev/staging/prod) ✅ COMPLETED
- [x] Config loading with full validation working ✅ COMPLETED
- [ ] All data files validated for all modes 🔄 IN PROGRESS

---

## Day 2: Architectural Violations Resolution (12-16 hours)

### Phase 2A: High Priority Architectural Violations (8-10 hours)
**Goal**: Fix the 3 critical violations blocking further progress

#### Task 07: Fix Async/Await Violations (4-5 hours) 🔴 CRITICAL
- **Status**: NOT STARTED
- **Violation**: ADR-006 Synchronous Component Execution
- **Files**: 5 component files with 40+ async methods
  - `position_monitor.py:239` - `async def update()` should be synchronous
  - `risk_monitor.py` - 18 async internal methods
  - `strategy_manager.py` - 9 async internal methods
  - `pnl_calculator.py:194` - `async def calculate_pnl()` should be synchronous
  - `position_update_handler.py` - 3 async internal methods
- **Quality Gate**: `scripts/test_async_await_quality_gates.py`
- **Success Criteria**:
  - [ ] Remove async/await from all internal component methods
  - [ ] Keep async only for Event Logger, Results Store, API entry points
  - [ ] All TODO-REFACTOR comments addressed
  - [ ] Quality gate passes: Async/Await compliance 100%

#### Task 06: Strategy Manager Refactor (4-5 hours) 🔴 CRITICAL
- **Status**: NOT STARTED
- **Violation**: ADR-007, Strategy Manager Refactor
- **Files**: `strategy_manager.py`, `transfer_manager.py` (DELETE), new strategy files
- **Quality Gate**: `scripts/test_strategy_manager_refactor_quality_gates.py`
- **Success Criteria**:
  - [ ] DELETE transfer_manager.py (1068 lines)
  - [ ] Create BaseStrategyManager with 5 standardized actions
  - [ ] Implement strategy-specific managers per mode
  - [ ] Create StrategyFactory for mode-based instantiation
  - [ ] All TODO-REMOVE comments addressed

### Phase 2B: Medium Priority Architectural Violations (4-6 hours)
**Goal**: Fix remaining violations to enable component integration

#### Task 08: Mode-Agnostic Architecture (2-3 hours) 🟡 HIGH
- **Status**: NOT STARTED
- **Violation**: Canonical Principles Section 7
- **Files**: `exposure_monitor.py`, `pnl_calculator.py`, new `utility_manager.py`
- **Quality Gate**: `scripts/test_mode_agnostic_quality_gates.py`
- **Success Criteria**:
  - [ ] Fix generic vs mode-specific violations
  - [ ] Use config parameters (asset, share_class, lst_type) instead of mode checks
  - [ ] Create centralized utility manager
  - [ ] All TODO-REFACTOR comments addressed

#### Task 09: Fail-Fast Configuration (2-3 hours) 🟡 MEDIUM
- **Status**: NOT STARTED
- **Violation**: Canonical Principles Section 33
- **Files**: `risk_monitor.py`
- **Quality Gate**: `scripts/test_fail_fast_config_quality_gates.py`
- **Success Criteria**:
  - [ ] Replace .get() with direct access in risk_monitor.py (62 instances)
  - [ ] Implement fail-fast configuration access
  - [ ] All components use direct config access
  - [ ] No TODO comments present

#### Task 10: Reference-Based Architecture (2-3 hours) 🟡 MEDIUM
- **Status**: NOT STARTED
- **Violation**: ADR-003 Reference-Based Architecture
- **Files**: All component files
- **Quality Gate**: `scripts/test_reference_architecture_quality_gates.py`
- **Success Criteria**:
  - [ ] Store references in `__init__`, never pass as runtime parameters
  - [ ] Ensure singleton pattern per request
  - [ ] All components follow reference-based pattern
  - [ ] No TODO comments present

#### Task 11: Singleton Pattern Enforcement (2-3 hours) 🟡 MEDIUM
- **Status**: NOT STARTED
- **Violation**: Canonical Principles Section 2
- **Files**: `event_driven_strategy_engine.py`, all component files
- **Quality Gate**: `scripts/test_singleton_pattern_quality_gates.py`
- **Success Criteria**:
  - [ ] Single instance per component per request
  - [ ] Shared config and data_provider instances
  - [ ] Singleton pattern enforced throughout
  - [ ] No TODO comments present

**Day 2 Success Criteria**:
- [ ] All async/await violations fixed (Task 07)
- [ ] Strategy manager refactored with inheritance (Task 06)
- [ ] Mode-agnostic components implemented (Task 08)
- [ ] Fail-fast configuration implemented (Task 09)
- [ ] Reference-based architecture implemented (Task 10)
- [ ] Singleton pattern enforced (Task 11)
- [ ] **BLOCKING**: Days 3-6 cannot proceed until Day 2 complete

---

## Day 3: Component Integration & Quality Gates (12-16 hours)

**⚠️ BLOCKED**: Cannot proceed until Day 2 architectural violations are resolved

### Phase 3A: Complete Component Integration (6-8 hours)
**Goal**: Ensure all components have correct signatures and integration patterns

#### Task 12: Tight Loop Architecture (2-3 hours) 🟡 MEDIUM
- **Status**: BLOCKED (depends on Task 07, 10)
- **Violation**: ADR-001 Tight Loop Architecture
- **Files**: `position_monitor.py`, `position_update_handler.py`, `execution_manager.py`
- **Quality Gate**: `scripts/test_tight_loop_architecture_quality_gates.py`
- **Success Criteria**:
  - [ ] Implement proper sequential chain with reconciliation handshake
  - [ ] Position updates verified before proceeding
  - [ ] Reconciliation pattern implemented
  - [ ] All TODO-REFACTOR comments addressed

#### Task 13: Consolidate Duplicate Risk Monitors (1-2 hours) 🟡 MEDIUM
- **Status**: BLOCKED (depends on Task 07)
- **Violation**: Single source of truth principle
- **Files**: `core/rebalancing/risk_monitor.py` (DELETE), `core/rebalancing/__init__.py`
- **Quality Gate**: `scripts/test_consolidate_duplicate_risk_monitors_quality_gates.py`
- **Success Criteria**:
  - [ ] Delete `core/rebalancing/risk_monitor.py` (duplicate)
  - [ ] Update imports to use correct location
  - [ ] All imports working correctly
  - [ ] No TODO comments present

#### Task 14: Component Data Flow Architecture (3-4 hours) 🟡 MEDIUM
- **Status**: BLOCKED (depends on Tasks 08, 10)
- **Violation**: Multiple ADRs
- **Files**: All specs in `docs/specs/`
- **Quality Gate**: `scripts/test_component_data_flow_architecture_quality_gates.py`
- **Success Criteria**:
  - [ ] Update all component specs to show parameter-based data flow
  - [ ] Document data flow patterns
  - [ ] Validate component integration patterns
  - [ ] No TODO comments present

### Phase 3B: API Endpoints & Health/Logging (6-8 hours)
**Goal**: Complete API endpoints, health checks, and structured logging

#### Task 04: Complete API Endpoints (3-4 hours) 🟢 LOW
- **Status**: BLOCKED (depends on Task 06)
- **Files**: `backend/src/basis_strategy_v1/api/`
- **Quality Gate**: `scripts/test_api_endpoints_quality_gates.py`
- **Success Criteria**:
  - [ ] Implement missing API endpoints from specs
  - [ ] Strategy selection endpoints
  - [ ] Backtest/live trading endpoints
  - [ ] Results retrieval endpoints

#### Task 05: Health Checks & Structured Logging (3-4 hours) 🟢 LOW
- **Status**: BLOCKED (depends on Task 11)
- **Files**: `backend/src/basis_strategy_v1/infrastructure/health/`, component files for logging
- **Quality Gate**: `scripts/test_health_logging_quality_gates.py`
- **Success Criteria**:
  - [ ] Unified health system (/health, /health/detailed)
  - [ ] Structured logging for all components
  - [ ] Event logging integration

**Day 3 Success Criteria**:
- [ ] Tight loop architecture implemented (Task 12)
- [ ] Duplicate files removed (Task 13)
- [ ] All API endpoints complete (Task 04)
- [ ] Health checks and logging structured (Task 05)
- [ ] **DEPENDENCY**: All Day 2 tasks must be completed first

---

## Day 4: Strategy Mode Validation - Simple to Complex (12-16 hours)

**⚠️ BLOCKED**: Cannot proceed until Day 3 component integration is complete

### Phase 4A: Pure Lending Mode (Complete E2E) (4-5 hours)
**Goal**: First complete strategy mode validation from data → results

#### Task 15: Pure Lending E2E Quality Gates (4-5 hours)
- **Status**: BLOCKED (depends on Tasks 12, 13, 14)
- **Files**: `scripts/test_pure_lending_quality_gates.py`
- **Quality Gate**: Uses existing `test_pure_lending_quality_gates.py`
- **Success Criteria**:
  - [ ] Deploy backend in dev env
  - [ ] Run backtest API call for pure_lending
  - [ ] Validate data loading
  - [ ] Validate component initialization
  - [ ] Validate APY: 3-8% (not 1166%)
  - [ ] Validate backtest results make sense

### Phase 4B: BTC Basis Mode (4-5 hours)
**Goal**: Second strategy mode - basis trading complexity

#### Task 16: BTC Basis E2E Quality Gates (4-5 hours)
- **Status**: BLOCKED (depends on Task 15)
- **Files**: `scripts/test_btc_basis_quality_gates.py`
- **Quality Gate**: Uses existing `test_btc_basis_quality_gates.py`
- **Success Criteria**:
  - [ ] Deploy backend in dev env
  - [ ] Run backtest API call for btc_basis
  - [ ] Validate funding rate calculations
  - [ ] Validate basis spread mechanics
  - [ ] Validate expected returns per config

### Phase 4C: ETH Basis Mode (4-5 hours)
**Goal**: Third strategy mode - ETH basis complexity

#### Task 17: ETH Basis E2E Quality Gates (4-5 hours)
- **Status**: BLOCKED (depends on Task 16)
- **Files**: `scripts/test_eth_basis_quality_gates.py`
- **Quality Gate**: `scripts/test_eth_basis_quality_gates.py`
- **Success Criteria**:
  - [ ] Deploy backend in dev env
  - [ ] Run backtest API call for eth_basis
  - [ ] Validate ETH-specific mechanics
  - [ ] Validate LST integration
  - [ ] Validate expected returns per config

**Day 4 Success Criteria**:
- [ ] Pure lending E2E passing (3-8% APY) (Task 15)
- [ ] BTC basis E2E passing (Task 16)
- [ ] ETH basis E2E passing (Task 17)
- [ ] **DEPENDENCY**: All Day 3 tasks must be completed first

---

## Day 5: Complex Modes & Component Unit Tests (12-16 hours)

**⚠️ BLOCKED**: Cannot proceed until Day 4 strategy validation is complete

### Phase 5A: USDT Market Neutral (Most Complex) (4-5 hours)
**Goal**: Most complex strategy mode with full leverage and hedging

#### Task 18: USDT Market Neutral E2E Quality Gates (4-5 hours)
- **Status**: BLOCKED (depends on Tasks 15, 16, 17)
- **Files**: `scripts/test_usdt_market_neutral_quality_gates.py`
- **Quality Gate**: `scripts/test_usdt_market_neutral_quality_gates.py`
- **Success Criteria**:
  - [ ] Deploy backend in dev env
  - [ ] Run backtest API call for usdt_market_neutral
  - [ ] Validate full leverage mechanics
  - [ ] Validate multi-venue hedging
  - [ ] Validate cross-venue capital allocation
  - [ ] Validate expected returns per config

### Phase 5B: Component-by-Component Unit Tests (8-10 hours)
**Goal**: Validate each component's signatures and integrations match specs

#### Task 19: Position Monitor Unit Tests (2-3 hours)
- **Status**: BLOCKED (depends on Task 12)
- **Files**: `scripts/unit_tests/test_position_monitor_unit.py`
- **Quality Gate**: `scripts/test_position_monitor_unit_tests_quality_gates.py`
- **Success Criteria**:
  - [ ] Test component signatures match spec
  - [ ] Test integration with execution interfaces
  - [ ] Test reconciliation patterns
  - [ ] 80% test coverage achieved

#### Task 20: Exposure Monitor Unit Tests (2-3 hours)
- **Status**: BLOCKED (depends on Task 08)
- **Files**: `scripts/unit_tests/test_exposure_monitor_unit.py`
- **Quality Gate**: `scripts/test_exposure_monitor_unit_tests_quality_gates.py`
- **Success Criteria**:
  - [ ] Test exposure calculations
  - [ ] Test integration with position monitor
  - [ ] Test config-driven parameters
  - [ ] 80% test coverage achieved

#### Task 21: Risk Monitor Unit Tests (2-3 hours)
- **Status**: BLOCKED (depends on Task 09)
- **Files**: `scripts/unit_tests/test_risk_monitor_unit.py`
- **Quality Gate**: `scripts/test_risk_monitor_unit_tests_quality_gates.py`
- **Success Criteria**:
  - [ ] Test risk calculations
  - [ ] Test integration with exposure monitor
  - [ ] Test circuit breaker logic
  - [ ] 80% test coverage achieved

#### Task 22: Strategy Manager Unit Tests (2-3 hours)
- **Status**: BLOCKED (depends on Task 06)
- **Files**: `scripts/unit_tests/test_strategy_manager_unit.py`
- **Quality Gate**: `scripts/test_strategy_manager_unit_tests_quality_gates.py`
- **Success Criteria**:
  - [ ] Test 5 standardized actions
  - [ ] Test strategy-specific implementations
  - [ ] Test factory pattern
  - [ ] 80% test coverage achieved

#### Task 23: P&L Calculator Unit Tests (2-3 hours)
- **Status**: BLOCKED (depends on Task 08)
- **Files**: `scripts/unit_tests/test_pnl_calculator_unit.py`
- **Quality Gate**: `scripts/test_pnl_calculator_unit_tests_quality_gates.py`
- **Success Criteria**:
  - [ ] Test mode-agnostic P&L calculations
  - [ ] Test attribution logic
  - [ ] Test integration with other components
  - [ ] 80% test coverage achieved

**Day 5 Success Criteria**:
- [ ] USDT market neutral E2E passing (Task 18)
- [ ] All component unit tests passing (Tasks 19-23)
- [ ] 80% unit test coverage achieved
- [ ] **DEPENDENCY**: All Day 4 tasks must be completed first

---

## Day 6: Frontend & Live Mode Completion (12-16 hours)

**⚠️ BLOCKED**: Cannot proceed until Day 5 unit tests are complete

### Phase 6A: Frontend Results Components (6-8 hours)
**Goal**: Complete missing frontend components

#### Task 24: Frontend Implementation (6-8 hours) 🟢 LOW
- **Status**: BLOCKED (depends on Task 04)
- **Files**: `frontend/src/components/results/`
- **Quality Gate**: `scripts/test_frontend_implementation_quality_gates.py`
- **Success Criteria**:
  - [ ] Implement ResultsPage component
  - [ ] Implement MetricCard component
  - [ ] Implement PlotlyChart component
  - [ ] Implement EventLogViewer component
  - [ ] API service layer
  - [ ] Type definitions

### Phase 6B: Live Mode Framework (6-8 hours)
**Goal**: Complete live mode framework (not full testing)

#### Task 25: Live Mode Quality Gates (6-8 hours) 🟢 LOW
- **Status**: BLOCKED (depends on Tasks 04, 05)
- **Files**: `backend/src/basis_strategy_v1/infrastructure/data/live_data_provider.py`, execution interfaces
- **Quality Gate**: `scripts/test_live_mode_quality_gates.py`
- **Success Criteria**:
  - [ ] Implement live data provider completeness
  - [ ] Implement live execution interface framework
  - [ ] Validate API client initialization
  - [ ] Basic live mode startup test (no actual trading)

#### Task 26: Comprehensive Quality Gates (2-3 hours)
- **Status**: BLOCKED (depends on all previous tasks)
- **Files**: `scripts/run_quality_gates.py`
- **Quality Gate**: `python scripts/run_quality_gates.py`
- **Success Criteria**:
  - [ ] Run full quality gate suite
  - [ ] Target: 19/24 passing (80%)
  - [ ] Document remaining issues

**Day 6 Success Criteria**:
- [ ] Frontend results components complete (Task 24)
- [ ] Live mode framework complete (Task 25)
- [ ] 19/24 quality gates passing (80%) (Task 26)
- [ ] System ready for staging deployment
- [ ] **DEPENDENCY**: All Day 5 tasks must be completed first

---

## Parallelization Strategy

### ⚠️ BLOCKING DEPENDENCIES
**CRITICAL**: Days 3-6 are completely blocked until Day 2 architectural violations are resolved.

### High Parallelization Opportunities (Multiple Agents)
- **Day 2, Phase 2B**: Tasks 08+09+10+11 can run in parallel (after Tasks 06+07 complete)
- **Day 3, Phase 3B**: Task 04 (API endpoints) || Task 05 (health/logging) - BLOCKED
- **Day 5, Phase 5B**: All 5 component unit test tasks in parallel (19-23) - BLOCKED
- **Day 6**: Task 24 (frontend) || Task 25 (live mode) - BLOCKED

### Sequential Required (File Conflicts)
- **Day 1**: All sequential (config/env foundation) ✅ COMPLETED
- **Day 2, Phase 2A**: Tasks 07, 06 must be sequential (critical architectural fixes)
- **Day 2, Phase 2B**: Tasks 08-11 can be parallel (after 06+07 complete)
- **Days 3-6**: All sequential due to architectural dependencies

### Agent Allocation Strategy
- **Primary Agent**: Handles Day 2 critical architectural fixes (Tasks 06, 07)
- **Agent A**: Handles Day 2 parallel tasks (08, 10) after critical fixes
- **Agent B**: Handles Day 2 parallel tasks (09, 11) after critical fixes
- **Agent C**: Standby for Day 3+ (blocked until Day 2 complete)
- **Agent D**: Standby for Day 5+ (blocked until Day 2 complete)
- **Agent E**: Standby for Day 5+ (blocked until Day 2 complete)

### Realistic Timeline Impact
- **Original Estimate**: 6 days with parallelization
- **Reality**: 6-7 days due to architectural blocking dependencies
- **Critical Path**: Day 2 → Day 3 → Day 4 → Day 5 → Day 6 (sequential)

---

## Risk Mitigation

### High-Risk Tasks
- **Task 07**: Async/await refactor (touches many files)
- **Task 06**: Strategy manager refactor (major architectural change)
- **Task 18**: USDT market neutral (most complex strategy)

### Mitigation Strategies
- **Incremental commits**: Commit after each task completion
- **Quality gates**: Run quality gates after each task
- **Rollback plan**: Keep previous versions for quick rollback
- **Testing**: Comprehensive testing at each phase

### Contingency Planning
- **If Day 1-2 delayed**: Focus on core refactors first
- **If Day 4-5 delayed**: Prioritize pure lending and BTC basis
- **If Day 6 delayed**: Complete frontend, defer live mode

---

## Success Metrics

### Daily Success Metrics
- **Day 1**: Foundation infrastructure working
- **Day 2**: Core architecture violations fixed
- **Day 3**: Component integration complete
- **Day 4**: 3 strategy modes working end-to-end
- **Day 5**: Complex strategy + unit tests complete
- **Day 6**: Frontend + live mode + quality gates

### Overall Success Metrics
- **43/43 tasks completed** (100%)
- **19/24 quality gates passing** (80%) - Updated from 83%
- **80% unit test coverage** achieved
- **4/4 strategy modes** working end-to-end
- **System ready for staging deployment**
- **11 architectural violations resolved**

---

## Quality Gate Integration

### Quality Gate Scripts Created
- `scripts/test_environment_switching_quality_gates.py`
- `scripts/test_config_validation_quality_gates.py`
- `scripts/test_api_endpoints_quality_gates.py`
- `scripts/test_health_logging_quality_gates.py`
- `scripts/test_eth_basis_quality_gates.py`
- `scripts/test_usdt_market_neutral_quality_gates.py`

### Quality Gate Execution
- **After each task**: Run relevant quality gate
- **After each day**: Run day-specific quality gates
- **End of project**: Run comprehensive quality gate suite

---

## Changes from Original Timeline (October 12, 2025)

### Why Updated
- Original timeline assumed architectural violations were fixed
- 11 architectural violations discovered and documented
- Quality gate reality check: 12/24 (50%) vs assumed higher baseline
- Documentation alignment work (Oct 9-10) completed but not tracked

### Major Adjustments
1. **Task Count**: 26 → 43 tasks (master sequence alignment)
2. **Duration**: 6 days → 6-7 days (realistic estimation)
3. **Quality Gate Target**: 83% → 80% (realistic based on current 50%)
4. **Architectural Violations**: Added as explicit blocking tasks
5. **Completion Tracking**: Added actual dates for completed work
6. **Dependencies**: Added explicit blocking dependencies (Day 2 blocks Days 3-6)
7. **Status Tracking**: Added current status for all tasks

### Current Reality vs Original Assumptions
- **Original**: Assumed all architectural violations were resolved
- **Reality**: 11 critical violations blocking progress
- **Original**: Assumed 83% quality gate pass rate
- **Reality**: Currently 50%, targeting 80%
- **Original**: 6-day timeline with parallelization
- **Reality**: 6-7 days due to sequential dependencies

---

## Conclusion

This 6-7 day implementation timeline provides a realistic approach to completing the Basis Strategy v1 platform. The timeline acknowledges current architectural debt and provides a structured path to resolve 11 critical violations before proceeding with new development.

**Key Success Factors**:
1. **Architectural debt resolution first** (Day 2 critical violations)
2. **Sequential dependencies** (Days 2-6 must be sequential)
3. **Quality gate validation** (throughout, targeting 80%)
4. **Incremental complexity** (simple to complex strategies)
5. **Comprehensive testing** (unit tests + E2E validation)
6. **Realistic expectations** (acknowledging current 50% quality gate status)

**Expected Outcome**: Complete, tested, and deployable Basis Strategy v1 platform ready for staging deployment, with all 11 architectural violations resolved and 19/24 quality gates passing (80%).
