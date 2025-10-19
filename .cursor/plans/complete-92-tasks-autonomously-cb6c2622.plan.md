<!-- cb6c2622-d44b-4e02-89ba-481c1398fbb0 364e327c-a529-42fb-b5c8-f0b604290048 -->
# Complete 92 Tasks - Autonomous Execution Plan

## Execution Strategy

**Approach**: Parallelize independent tasks, execute sequentially where dependencies exist

**Frontend Tasks**: Skip tasks 24, 27, 28 completely (excluded per user request)

**Backend Status**: Running with dependencies installed (confirmed by user)

**Timeline**: 12 days, 89 tasks (92 minus 3 frontend tasks)

## Phase 1: Foundation (Day 1) - Sequential Execution

**Tasks 01-03**: Environment, Config, Data Loading (8 hours)

### Critical Infrastructure Setup

- Task 01: Environment file switching & fail-fast validation
  - Reference: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6.1
  - Quality Gate: `tests/unit/test_config_manager_unit.py`
  - Deliverable: BASIS_ENVIRONMENT switching working

- Task 02: Config loading & validation
  - Reference: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6.1
  - Quality Gate: `scripts/test_config_validation_quality_gates.py`
  - Deliverable: All YAML configs load with Pydantic validation

- Task 03: Data loading quality gate
  - Reference: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 8
  - Quality Gate: `scripts/test_data_provider_refactor_quality_gates.py`
  - Deliverable: All data files validated for all modes

**Success Criteria**: Foundation solid - env switching, config loading, data validation all working

## Phase 2: Core Architecture (Day 2) - Parallel Execution

**Tasks 04-14**: Architecture refactors and component integration (12-16 hours)

### Batch 2A: Async/Await & Reference Architecture (Parallel)

- Task 07: Fix async/await violations (6-8 hours)
  - Files: `position_monitor.py`, `risk_monitor.py`, `strategy_manager.py`, `pnl_monitor.py`
  - Remove async from internal methods per ADR-006

- Task 10: Reference-based architecture (6-8 hours)
  - Target: All component files
  - Store references in `__init__`, singleton per request

### Batch 2B: Singleton & Strategy Manager (Sequential - depends on 2A)

- Task 11: Singleton pattern (6-8 hours)
  - Target: `event_driven_strategy_engine.py`, components
  - Single instance per component per request

- Task 06: Strategy manager refactor (6-8 hours)
  - DELETE `transfer_manager.py`
  - Create BaseStrategyManager, StrategyFactory with 5 standardized actions

### Batch 2C: Mode-Agnostic & Fail-Fast (Parallel)

- Task 08: Mode-agnostic architecture (6-8 hours)
  - Targets: `exposure_monitor.py`, `pnl_monitor.py`
  - Config params instead of mode checks

- Task 09: Fail-fast configuration (6-8 hours)
  - Target: `risk_monitor.py` (62 `.get()` instances)
  - Direct config access, no defaults

**Success Criteria**: Architecture violations fixed, reference-based pattern implemented, mode-agnostic components

## Phase 3: Integration & API (Day 3) - Parallel Execution

**Tasks 12-14, 04-05**: Component integration and API completion (12-16 hours)

### Batch 3A: Component Integration (Sequential)

- Task 12: Tight loop architecture (6-8 hours)
  - Targets: `position_monitor.py`, `position_update_handler.py`, `execution_manager.py`
  - Sequential chain with reconciliation handshake

- Task 13: Consolidate duplicate risk monitors (2 hours)
  - DELETE `core/rebalancing/risk_monitor.py`
  - Update all imports

- Task 14: Component data flow architecture (4 hours)
  - Target: `docs/specs/` (all component specs)
  - Document parameter-based data flows

### Batch 3B: API & Infrastructure (Parallel with 3A)

- Task 04: Complete API endpoints (6-8 hours)
  - Target: `backend/src/basis_strategy_v1/api/`
  - All strategy, backtest, results endpoints

- Task 05: Health & logging (6-8 hours)
  - Target: `backend/src/basis_strategy_v1/infrastructure/health/`
  - Unified health system, structured logging

**Success Criteria**: Tight loop working, single risk monitor, all API endpoints complete

## Phase 4: Strategy E2E Validation (Day 4) - Sequential Execution

**Tasks 15-18**: Strategy mode E2E tests (12-16 hours)

### Simple Strategies First

- Task 15: Pure lending E2E (4-5 hours)
  - Quality Gate: `tests/e2e/test_pure_lending_usdt_e2e.py`
  - Target: 3-8% APY validation (not 1166%)

- Task 16: BTC basis E2E (4-5 hours)
  - Quality Gate: `tests/e2e/test_btc_basis_e2e.py`
  - Target: Funding rate calculations, basis spread

- Task 17: ETH basis E2E (4-5 hours)
  - Quality Gate: `tests/e2e/test_eth_basis_e2e.py`
  - Target: ETH mechanics, LST integration

- Task 18: USDT market neutral E2E (4-5 hours)
  - Quality Gate: `tests/e2e/test_usdt_market_neutral_e2e.py`
  - Target: Full leverage, multi-venue hedging

**Success Criteria**: All 4 strategy modes passing E2E tests with correct metrics

## Phase 5: Component Unit Tests (Day 5) - Parallel Execution

**Tasks 19-23, 32-35**: Core component unit tests (12-16 hours)

### Batch 5A: Monitoring Components (Parallel)

- Task 19: Position monitor unit tests (8-10 hours)
  - File: `tests/unit/test_position_monitor_unit.py`
  - Target: 80% coverage, config-driven architecture

- Task 20: Exposure monitor unit tests (8-10 hours)
  - File: `tests/unit/test_exposure_monitor_unit.py`
  - Target: 80% coverage, mode-agnostic design

- Task 21: Risk monitor unit tests (8-10 hours)
  - File: `tests/unit/test_risk_monitor_unit.py`
  - Target: 80% coverage, fail-fast validation

### Batch 5B: Strategy & PnL (Parallel)

- Task 22: Strategy manager unit tests (8-10 hours)
  - File: `tests/unit/test_strategy_manager_unit.py`
  - Target: 80% coverage, inheritance-based

- Task 23: P&L calculator unit tests (8-10 hours)
  - File: `tests/unit/test_pnl_monitor_unit.py`
  - Target: 80% coverage, mode-agnostic

### Batch 5C: Infrastructure Components (Parallel)

- Task 32: Event logger unit tests (4-6 hours)
- Task 33: Results store unit tests (4-6 hours)
- Task 34: Health system unit tests (4-6 hours)
- Task 35: API endpoints unit tests (4-6 hours)

**Success Criteria**: All core components with 80% unit test coverage

## Phase 6: Execution & Integration (Day 6) - Mixed Execution

**Tasks 25-26, 30-31, 36-40**: Execution infrastructure and integration tests (12-16 hours)

### Batch 6A: Execution Components (Sequential)

- Task 30: Execution components implementation (8-10 hours)
  - Reference: `docs/specs/06_VENUE_MANAGER.md`, `docs/specs/07_VENUE_INTERFACE_MANAGER.md`
  - Complete execution infrastructure

- Task 31: Infrastructure components completion (6-8 hours)
  - Reference: `docs/specs/HEALTH_ERROR_SYSTEMS.md`
  - Health systems, error handling, results store

### Batch 6B: Service Validation (Parallel with 6A)

- Task 25: Live mode quality gates (6-8 hours)
  - Quality Gate: `scripts/test_live_mode_quality_gates.py`
  - Live data provider, execution framework

- Task 26: Service layer & engine validation (6-8 hours)
  - Quality Gate: `scripts/run_quality_gates.py`
  - Service layer validation

### Batch 6C: Integration Tests (Sequential - after 6A/6B)

- Task 36: Position→Exposure data flow (4-6 hours)
- Task 37: Exposure→Risk data flow (4-6 hours)
- Task 38: Risk→Strategy data flow (4-6 hours)
- Task 39: Strategy→Execution data flow (4-6 hours)
- Task 40: Tight loop reconciliation (4-6 hours)

**Success Criteria**: Execution infrastructure complete, integration tests passing

## Phase 7: Additional E2E Tests (Day 7) - Sequential Execution

**Tasks 41-43, 29**: Remaining strategy modes and utilities (12-16 hours)

- Task 41: ETH staking only E2E (4-6 hours)
- Task 42: ETH leveraged staking E2E (4-6 hours)
- Task 43: USDT market neutral no leverage E2E (4-6 hours)
- Task 29: Shared utilities implementation (4-6 hours)

**Success Criteria**: All 7 strategy modes E2E passing

## Phase 8: API Routes Unit Tests (Day 8) - Parallel Execution

**Tasks 44-52**: API routes unit tests (12-16 hours)

### All API Routes in Parallel (9 tests)

- Task 44: Auth routes unit tests
- Task 45: Backtest routes unit tests
- Task 46: Capital routes unit tests
- Task 47: Charts routes unit tests
- Task 48: Config routes unit tests
- Task 49: Health routes unit tests
- Task 50: Live trading routes unit tests
- Task 51: Results routes unit tests
- Task 52: Strategies routes unit tests

**Success Criteria**: All API routes with 80% unit test coverage

## Phase 9: Core Strategies Unit Tests (Day 9) - Parallel Execution

**Tasks 53-61**: Core strategies unit tests (12-16 hours)

### All Strategy Tests in Parallel (9 tests)

- Task 53: BTC basis strategy unit tests
- Task 54: ETH basis strategy unit tests
- Task 55: ETH leveraged strategy unit tests
- Task 56: ETH staking only strategy unit tests
- Task 57: Pure lending strategy unit tests
- Task 58: Strategy factory unit tests
- Task 59: USDT market neutral strategy unit tests
- Task 60: USDT market neutral no leverage strategy unit tests
- Task 61: ML directional strategy unit tests

**Success Criteria**: All strategy implementations with 80% unit test coverage

## Phase 10: Data Provider Unit Tests (Day 10) - Parallel Execution

**Tasks 62-74**: Infrastructure data provider unit tests (12-16 hours)

### All Data Provider Tests in Parallel (13 tests)

- Task 62: BTC basis data provider unit tests
- Task 63: Data provider factory unit tests
- Task 64: Config driven historical data provider unit tests
- Task 65: Data validator unit tests
- Task 66: ETH basis data provider unit tests
- Task 67: ETH leveraged data provider unit tests
- Task 68: ETH staking only data provider unit tests
- Task 69: Historical data provider unit tests
- Task 70: Live data provider unit tests
- Task 71: ML directional data provider unit tests
- Task 72: Pure lending data provider unit tests
- Task 73: USDT market neutral data provider unit tests
- Task 74: USDT market neutral no leverage data provider unit tests

**Success Criteria**: All data providers with 80% unit test coverage

## Phase 11: Math & Execution Unit Tests (Day 11) - Parallel Execution

**Tasks 75-81**: Core math and execution interfaces (12-16 hours)

### Math Calculators (Parallel - 4 tests)

- Task 75: Health calculator unit tests
- Task 76: LTV calculator unit tests
- Task 77: Margin calculator unit tests
- Task 78: Metrics calculator unit tests

### Execution Interfaces (Parallel - 3 tests)

- Task 79: CEX execution interface unit tests
- Task 80: On-chain execution interface unit tests
- Task 81: Transfer execution interface unit tests

**Success Criteria**: All math and execution interfaces with 80% unit test coverage

## Phase 12: Zero Coverage Components (Day 12) - Parallel Execution

**Tasks 82-92**: Final component unit tests (12-16 hours)

### All Zero Coverage Components in Parallel (11 tests)

- Task 82: Venue adapters unit tests
- Task 83: Backtest service unit tests
- Task 84: Live service unit tests
- Task 85: Component health unit tests
- Task 86: Unified health manager unit tests
- Task 87: Utility manager unit tests
- Task 88: Error code registry unit tests
- Task 89: Execution instructions unit tests
- Task 90: Reconciliation component unit tests
- Task 91: API call queue unit tests
- Task 92: Chart storage and visualization unit tests

**Success Criteria**: All remaining components with 80% unit test coverage

## Execution Rules

### Parallelization Strategy

1. **Foundation tasks (01-03)**: Sequential - critical dependencies
2. **Architecture tasks (04-14)**: Mixed - parallel within batches, sequential between batches
3. **E2E tests (15-18, 41-43)**: Sequential - validate incrementally
4. **Unit tests (19-92)**: Maximum parallelization - independent test creation

### Quality Gate Checkpoints

- After each task: Run task-specific quality gate
- After each day: Run `python scripts/run_quality_gates.py`
- Fix failures immediately without breaking canonical patterns
- Document any issues and continue

### Error Handling

- Log exact error messages
- Retry operations up to 3 times
- Restart backend if needed: `./platform.sh stop && ./platform.sh backtest`
- Document issues and continue (don't stop)

### Canonical Compliance

- **Reference sections are law**: Never violate patterns in task Reference sections
- **ADR compliance**: All fixes must follow Architectural Decision Records
- **No backward compatibility**: Break cleanly, update all references
- **Target structure**: Strictly follow `docs/TARGET_REPOSITORY_STRUCTURE.md`

## Success Metrics

### Final Target

- **89/89 tasks completed** (92 minus 3 frontend tasks)
- **All quality gates passing** (100%)
- **80% test coverage** (66/82 backend files)
- **All 7 strategy modes E2E working**
- **System ready for staging deployment**

### Daily Progress Tracking

- Report completion after each task
- Update success criteria checkboxes
- Document quality gate results
- Track coverage improvements

## Key Files to Monitor

### Critical Documentation

- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Architecture source of truth
- `docs/TARGET_REPOSITORY_STRUCTURE.md` - File organization rules
- `docs/MODES.md` - Strategy mode definitions
- `docs/specs/` - Component specifications

### Quality Gate Commands

```bash
# Run all quality gates
python scripts/run_quality_gates.py

# Run specific categories
python scripts/run_quality_gates.py --category unit
python scripts/run_quality_gates.py --category integration_data_flows
python scripts/run_quality_gates.py --category e2e_strategies

# Run specific test
python -m pytest tests/unit/test_position_monitor_unit.py -v
```

### Backend Management

```bash
# Start backend
./platform.sh backtest

# Stop backend
./platform.sh stop

# Check health
curl -s http://localhost:8001/health/
```

## Notes

- **Frontend tasks excluded**: Tasks 24, 27, 28 are completely skipped per user request
- **Autonomous execution**: No approval requests between tasks, quality gates are checkpoints
- **Parallelization optimized**: Maximum efficiency with parallel execution where safe
- **Backend confirmed running**: Dependencies installed, ready to execute

### To-dos

- [ ] Phase 1: Foundation - Environment, Config, Data Loading (Tasks 01-03)
- [ ] Phase 2: Core Architecture - Async/Await, Reference Architecture, Singleton (Tasks 04-14)
- [ ] Phase 3: Integration & API - Tight Loop, API Endpoints, Health (Tasks 12-14, 04-05)
- [ ] Phase 4: Strategy E2E Validation - Pure Lending, BTC/ETH Basis, USDT Market Neutral (Tasks 15-18)
- [ ] Phase 5: Component Unit Tests - Monitoring, Strategy, Infrastructure (Tasks 19-23, 32-35)
- [ ] Phase 6: Execution & Integration - Execution Infrastructure, Service Validation, Data Flows (Tasks 25-26, 30-31, 36-40)
- [ ] Phase 7: Additional E2E Tests - ETH Staking, Leveraged, Utilities (Tasks 41-43, 29)
- [ ] Phase 8: API Routes Unit Tests - All 9 API route tests (Tasks 44-52)
- [ ] Phase 9: Core Strategies Unit Tests - All 9 strategy tests (Tasks 53-61)
- [ ] Phase 10: Data Provider Unit Tests - All 13 data provider tests (Tasks 62-74)
- [ ] Phase 11: Math & Execution Unit Tests - 4 math + 3 execution interface tests (Tasks 75-81)
- [ ] Phase 12: Zero Coverage Components - Final 11 component tests (Tasks 82-92)