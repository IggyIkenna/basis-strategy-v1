<!-- f5075160-812f-470d-b8d9-4c7aee81fe4f 259e6366-6992-404d-ba15-fb4104539a5d -->
# 26-Step Agent Build Execution Plan

## Overview

Execute all 29 tasks across 6 days, starting from foundational infrastructure through complete end-to-end functionality. Each task must pass its quality gate validation before proceeding. All fixes must preserve canonical architectural patterns defined in task Reference sections.

## Execution Approach

### Quality Gate Driven Development

- **Gatekeeper Pattern**: Quality gates determine when to proceed
- **Fix Without Breaking**: Maintain canonical patterns from Reference sections
- **Autonomous Execution**: No stopping for approvals between tasks
- **Validation First**: Verify baseline status before starting

### Key Files & References

- **Master Plan**: `.cursor/tasks/00_master_task_sequence.md`
- **Timeline**: `IMPLEMENTATION_TIMELINE.md`
- **Violations**: `docs/DEVIATIONS_AND_CORRECTIONS.md`
- **Canonical**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`
- **ADRs**: `docs/ARCHITECTURAL_DECISION_RECORDS.md`

## Pre-Flight Phase

### Baseline Validation

1. Verify current quality gate status: `python scripts/run_quality_gates.py`
2. Confirm 8/24 baseline (33.3%)
3. Document starting point

## Day 1: Foundation (3 Tasks - 8 hours)

### Task 01: Environment File Switching

- **File**: `.cursor/tasks/01_environment_file_switching.md`
- **Target**: `backend/src/basis_strategy_v1/infrastructure/config/`
- **Quality Gate**: `scripts/test_environment_switching_quality_gates.py`
- **Success**: BASIS_ENVIRONMENT switching, fail-fast validation

### Task 02: Config Loading & Validation

- **File**: `.cursor/tasks/02_config_loading_validation.md`
- **Target**: `backend/src/basis_strategy_v1/core/config/config_loader.py`
- **Quality Gate**: `scripts/test_config_validation_quality_gates.py`
- **Success**: All YAML loading, Pydantic validation, fail-fast

### Task 03: Data Loading Quality Gate

- **File**: `.cursor/tasks/03_data_loading_quality_gate.md`
- **Quality Gate**: `scripts/test_data_provider_refactor_quality_gates.py`
- **Success**: All data files validated for all modes

## Day 2: Core Architecture (6 Tasks - 12-16 hours)

### Task 07: Fix Async/Await Violations (HIGH PRIORITY)

- **File**: `.cursor/tasks/07_fix_async_await_violations.md`
- **Targets**: `position_monitor.py`, `risk_monitor.py`, `strategy_manager.py`, `pnl_calculator.py`, `position_update_handler.py`
- **Quality Gate**: `scripts/test_async_ordering_quality_gates.py`
- **Critical**: Remove async from internal methods per ADR-006

### Task 10: Reference-Based Architecture

- **File**: `.cursor/tasks/10_reference_based_architecture.md`
- **Target**: All component files
- **Success**: Store references in `__init__`, singleton per request

### Task 11: Singleton Pattern

- **File**: `.cursor/tasks/11_singleton_pattern.md`
- **Target**: `event_driven_strategy_engine.py`, components
- **Success**: Single instance per component per request

### Task 06: Strategy Manager Refactor (HIGH PRIORITY)

- **File**: `.cursor/tasks/06_strategy_manager_refactor.md`
- **Actions**: DELETE `transfer_manager.py`, create BaseStrategyManager, StrategyFactory
- **Success**: 5 standardized actions, inheritance-based

### Task 08: Mode-Agnostic Architecture (HIGH PRIORITY)

- **File**: `.cursor/tasks/08_mode_agnostic_architecture.md`
- **Targets**: `exposure_monitor.py`, `pnl_calculator.py`
- **Success**: Config params instead of mode checks

### Task 09: Fail-Fast Configuration

- **File**: `.cursor/tasks/09_fail_fast_19_CONFIGURATION.md`
- **Target**: `risk_monitor.py` (62 `.get()` instances)
- **Success**: Direct config access, no defaults

## Day 3: Integration (5 Tasks - 12-16 hours)

### Task 12: Tight Loop Architecture

- **File**: `.cursor/tasks/12_tight_loop_architecture.md`
- **Targets**: `position_monitor.py`, `position_update_handler.py`, `execution_manager.py`
- **Quality Gate**: `scripts/test_tight_loop_quality_gates.py`
- **Success**: Sequential chain with reconciliation handshake

### Task 13: Consolidate Duplicate Risk Monitors

- **File**: `.cursor/tasks/13_consolidate_duplicate_risk_monitors.md`
- **Action**: DELETE `core/rebalancing/risk_monitor.py`
- **Success**: Single risk monitor, imports updated

### Task 14: Component Data Flow Architecture

- **File**: `.cursor/tasks/14_component_data_flow_architecture.md`
- **Target**: `docs/specs/` (all component specs)
- **Success**: Parameter-based data flow documented

### Task 04: Complete API Endpoints

- **File**: `.cursor/tasks/04_complete_api_endpoints.md`
- **Target**: `backend/src/basis_strategy_v1/api/`
- **Quality Gate**: `scripts/test_api_endpoints_quality_gates.py`
- **Success**: All strategy, backtest, results endpoints

### Task 05: Health & Logging

- **File**: `.cursor/tasks/05_health_logging_structure.md`
- **Target**: `backend/src/basis_strategy_v1/infrastructure/health/`
- **Quality Gate**: `scripts/test_health_logging_quality_gates.py`
- **Success**: Unified health system, structured logging

## Day 4: Strategy Validation (3 Tasks - 12-16 hours)

### Task 15: Pure Lending E2E

- **File**: `.cursor/tasks/15_pure_lending_quality_gates.md`
- **Quality Gate**: `scripts/test_pure_lending_quality_gates.py`
- **Success**: 3-8% APY validation (not 1166%)

### Task 16: BTC Basis E2E

- **File**: `.cursor/tasks/16_btc_basis_quality_gates.md`
- **Quality Gate**: `scripts/test_btc_basis_quality_gates.py`
- **Success**: Funding rate calculations, basis spread

### Task 17: ETH Basis E2E

- **File**: `.cursor/tasks/17_eth_basis_quality_gates.md`
- **Quality Gate**: `scripts/test_eth_basis_quality_gates.py`
- **Success**: ETH mechanics, LST integration

## Day 5: Complex Modes & Unit Tests (6 Tasks - 12-16 hours)

### Task 18: USDT Market Neutral E2E

- **File**: `.cursor/tasks/18_usdt_market_neutral_quality_gates.md`
- **Quality Gate**: `scripts/test_usdt_market_neutral_quality_gates.py`
- **Success**: Full leverage, multi-venue hedging

### Tasks 19-23: Component Unit Tests (PARALLEL)

- **Task 19**: Position Monitor - `scripts/test_position_monitor_unit_tests_quality_gates.py`
- **Task 20**: Exposure Monitor - `scripts/test_exposure_monitor_unit_tests_quality_gates.py`
- **Task 21**: Risk Monitor - `scripts/test_risk_monitor_unit_tests_quality_gates.py`
- **Task 22**: Strategy Manager - `scripts/test_strategy_manager_unit_tests_quality_gates.py`
- **Task 23**: P&L Calculator - `scripts/test_pnl_calculator_unit_tests_quality_gates.py`
- **Success**: 80% test coverage each

## Day 6: Frontend & Live Mode (3 Tasks - 12-16 hours)

### Task 24: Frontend Implementation

- **File**: `.cursor/tasks/24_frontend_implementation.md`
- **Target**: `frontend/src/components/results/`
- **Success**: ResultsPage, MetricCard, PlotlyChart, EventLogViewer

### Task 25: Live Mode Framework

- **File**: `.cursor/tasks/25_live_mode_quality_gates.md`
- **Quality Gate**: `scripts/test_live_mode_quality_gates.py`
- **Success**: Live data provider, execution framework

### Task 26: Comprehensive Quality Gates

- **File**: `.cursor/tasks/26_comprehensive_quality_gates.md`
- **Quality Gate**: `scripts/run_quality_gates.py`
- **Target**: 20/24 passing (83%)

## Critical Rules

### Canonical Pattern Preservation

- **Reference sections are law** - Never violate patterns in task Reference sections
- **ADR compliance** - All fixes must follow Architectural Decision Records
- **No backward compatibility** - Break cleanly, update all references

### Quality Gate Protocol

1. Read complete task file before starting
2. Execute implementation following Reference patterns
3. Run task-specific quality gate
4. If PASS → proceed to next task
5. If FAIL → fix issues WITHOUT breaking canonical patterns
6. Retry quality gate until pass
7. Document results and continue

### Server Management

- Use `./platform.sh backtest` to start backend
- Use `./platform.sh stop-local` before restarting
- Restart server before long-running tests

### Error Handling

- 10-minute timeout per command
- Max 3 retry attempts
- Restart backend if needed
- Document and continue (don't stop)

## Success Metrics

### Daily Targets

- **Day 1**: Environment + config + data foundation ✅
- **Day 2**: Core architecture violations fixed ✅
- **Day 3**: Component integration complete ✅
- **Day 4**: 3 strategy modes E2E passing ✅
- **Day 5**: Complex strategy + 80% unit coverage ✅
- **Day 6**: Frontend + live mode + 20/24 gates passing ✅

### Final Target

- **26/26 tasks completed** (100%)
- **20/24 quality gates passing** (83%)
- **80% unit test coverage**
- **4/4 strategy modes E2E working**
- **System ready for staging deployment**

## Execution Strategy

### Autonomous Operation

- No approval requests between tasks
- Quality gates are the only checkpoints
- Fix failures immediately without breaking patterns
- Continue until all 26 tasks complete

### Parallelization (Where Noted)

- Day 2: Tasks 6, 8, 9 can run parallel
- Day 3: Tasks 4, 5 can run parallel
- Day 5: Tasks 19-23 can run parallel
- Day 6: Tasks 24, 25 can run parallel

### Progress Tracking

- Log completion after each task
- Report quality gate results
- Document any issues encountered
- Update success criteria checkboxes

### To-dos

- [ ] Verify current quality gate baseline status (8/24 passing)
- [ ] Day 1 - Tasks 01-03: Environment, Config, Data Loading foundation
- [ ] Day 2 - Tasks 07,10,11,06,08,09: Core architecture refactors (async, singleton, strategy manager)
- [ ] Day 3 - Tasks 12-14,04-05: Component integration, APIs, health/logging
- [ ] Day 4 - Tasks 15-17: Pure Lending, BTC Basis, ETH Basis E2E validation
- [ ] Day 5 - Tasks 18-23: USDT Market Neutral + Component Unit Tests (80% coverage)
- [ ] Day 6 - Tasks 24-26: Frontend implementation, Live mode, Final quality gates (20/24 passing)