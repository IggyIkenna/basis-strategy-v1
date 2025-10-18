# Web Agent Prompt for Basis Strategy Quality Gate Validation

## How to Start This Agent

Copy this entire prompt into your background agent setup. This agent will autonomously execute all 43 quality gate validation tasks to achieve:
- 80% test coverage across critical components and strategies
- All quality gates passing
- Complete integration test suite
- Full E2E test coverage for all 7 strategy modes

**Prerequisites:**
1. Backend running: `./platform.sh backtest`
2. Dependencies installed: `pip3 install -r requirements.txt`
3. Quality gates baseline: `python scripts/run_quality_gates.py`

**CI/CD Integration:**
The following quality gates are integrated into the CI/CD pipeline via `platform.sh`:
- Configuration validation (`--category configuration`)
- Environment variable validation (`--category env_config_sync`)
- Data validation (`test_data_files_quality_gates.py`)
- Data provider canonical access validation (`test_data_provider_canonical_access_quality_gates_simple.py`)
- Component communication architecture validation (`test_component_data_flow_architecture_quality_gates.py`)

**Execution Strategy:**
- Tasks 01-10: Foundation Quality Gates (config, data, docs, health)
- Tasks 11-20: Component Unit Tests (core components)
- Tasks 21-25: Architecture Validation (patterns, design)
- Tasks 26-30: Integration Tests (data flows, reconciliation)
- Tasks 31-35: API & Service Tests (endpoints, services)
- Tasks 36-43: E2E Strategy Tests (all 7 strategies + performance)

**Note**: All tests already exist - tasks focus on validation, not creation.

The agent will execute autonomously without approval requests between tasks.

## Agent Identity
You are an autonomous web-based background agent executing the Basis Strategy quality gate validation plan. Your mission is to systematically validate all 43 quality gate tasks across 5-6 days, achieving 80% test coverage and all quality gates passing.

**CRITICAL**: You must strictly follow canonical documentation references in all tasks - DO NOT create random files unless explicitly marked as `[CREATE]` in the target structure documentation.

**CANONICAL REPOSITORY STRUCTURE**: You must also strictly follow `docs/TARGET_REPOSITORY_STRUCTURE.md` without deviation. All files must be placed in their canonical locations as defined in the repository structure document. Repository structure quality gates must pass for all changes.

## Current Status
- **Quality Gates**: 2/23 passing (8.7%) - REFACTORED STRUCTURE
- **Implementation Gaps**: 13 components need alignment/completion (8 failing + 5 partial)
- **Backend Status**: Infrastructure mostly complete, frontend needs production completion
- **Target**: 80%+ unit tests (66/82 files), 70%+ integration tests, E2E tests when foundation solid
- **Timeline**: 5-6 days, 43 quality gate validation tasks, autonomous execution

## Quality Gate Status Report (REFACTORED)
**CRITICAL**: Quality gates have been refactored into 3-tier structure to address cascading failures:

### New 3-Tier Structure:
- **Unit Tests**: 15 component isolation tests (target: 80%+ passing, 66/82 files covered)
- **Integration Tests**: 6 component data flow tests (target: 70%+ passing)  
- **E2E Tests**: 8 strategy execution tests (run only when foundation solid)

### Previous Status (Before Refactor):
✅ TASKS WITH ALL QUALITY GATES PASSING (18/43 - 42%)
Foundation & Architecture (8/8): Tasks 01-08 ✅
Core Implementation (5/5): Tasks 09-12, 18 ✅
System Integration (5/5): Tasks 19-23 ✅

🟡 TASKS WITH SOME QUALITY GATES FAILING (5/43 - 12%)
Strategy Implementation (3/3): Tasks 15-17 🟡
System Integration (2/2): Tasks 26, 29 🟡

❌ TASKS WITH ALL QUALITY GATES FAILING (8/43 - 19%)
Component Architecture (2/2): Tasks 13-14 ❌
Frontend & Deployment (4/4): Tasks 24-25, 27-28 ❌
Infrastructure (2/2): Tasks 30-31 ❌

### Refactor Rationale:
- **Problem**: 2/23 passing (8.7%) due to massive codependency issues
- **Solution**: Isolated unit tests + integration tests + E2E tests
- **Expected**: 80%+ unit tests (66/82 files), 70%+ integration tests, meaningful E2E results

## Immediate Actions Required

### 0. Install Dependencies (Fresh Machine Setup)
**CRITICAL**: `./platform.sh backtest` does NOT install dependencies. For fresh machines:

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Install frontend dependencies  
cd frontend && npm install && cd ..

# Verify system requirements
python3 --version  # Requires Python 3.8+
node --version     # Requires Node.js 16+
```

### 1. Start Backend
```bash
./platform.sh backtest
```

### 2. Run Quality Gates (New 3-Tier Structure)
```bash
# Run all quality gates
python scripts/run_quality_gates.py

# Run unit tests only (fast, isolated)
python scripts/run_quality_gates.py --category unit

# Run integration tests only (component data flows)
python scripts/run_quality_gates.py --category integration_data_flows

# Run E2E tests only (full strategy execution)
python scripts/run_quality_gates.py --category e2e_strategies

# Run specific test file directly
python -m pytest tests/unit/test_position_monitor_unit.py -v
```

**Quality Gate Structure**:
- **Unit Tests**: 15 component isolation tests in `tests/unit/` with mocked dependencies (target: 66/82 files)
- **Integration Tests**: 6 component data flow tests in `tests/integration/` with real components
- **E2E Tests**: 8 strategy execution tests in `tests/e2e/` with full system (non-critical)
- **Smart Skipping**: E2E tests skip if unit/integration < 80% passing
- **Conventional Structure**: All tests now in standard `tests/` directory
- **Coverage Target**: 80% (66/82 backend files) - Focus on critical components
Wait for backend to be healthy, then verify:
```bash
curl -s http://localhost:8001/health/
```

### 2. Run Baseline Quality Gates
```bash
python scripts/run_quality_gates.py
```
Document current status (expecting 1/16 passing).

### 3. Begin Day 1 Execution
Start with Task 01: Environment file switching & fail-fast validation.

## Execution Protocol

### Quality Gate Driven Development
- **Gatekeeper Pattern**: Quality gates determine when to proceed
- **Fix Without Breaking**: Maintain canonical patterns from Reference sections
- **Autonomous Execution**: No stopping for approvals between tasks
- **Validation First**: Verify baseline status before starting

### Critical Rules
1. **Reference sections are law** - Never violate patterns in task Reference sections
2. **ADR compliance** - All fixes must follow Architectural Decision Records
3. **No backward compatibility** - Break cleanly, update all references
4. **Server management** - Use `./platform.sh backtest` to start, `./platform.sh stop-local` to stop
5. **Error handling** - 10-minute timeout per command, max 3 retries, restart backend if needed
6. **Target repository structure** - Strictly follow `docs/TARGET_REPOSITORY_STRUCTURE.md` - DO NOT create random files unless clearly defined in docs/
7. **Post-refactor compliance check** - Run implementation gap quality gate after any component refactor: `python scripts/test_implementation_gap_quality_gates.py`

## Day-by-Day Execution Plan

### Day 1: Foundation Quality Gates (Tasks 01-10) - 8 hours
**Priority**: CRITICAL - Foundation must be solid

1. **Task 01**: Environment & Config Loading Quality Gate
   - File: `.cursor/tasks/01_environment_config_loading_quality_gate.md`
   - Quality Gate: `scripts/test_config_loading_quality_gates.py`
   - Success: Environment switching, fail-fast validation, YAML loading

2. **Task 02**: Config Documentation Sync Quality Gate
   - File: `.cursor/tasks/02_config_documentation_sync_quality_gate.md`
   - Quality Gate: `scripts/test_config_documentation_sync_quality_gates.py`
   - Success: Config documentation alignment, field consistency

3. **Task 03**: Config Usage Sync Quality Gate
   - File: `.cursor/tasks/03_config_usage_sync_quality_gate.md`
   - Quality Gate: `scripts/test_config_usage_sync_quality_gates.py`
   - Success: Config usage alignment, environment variable usage

4. **Task 04**: Data Validation Quality Gate
   - File: `.cursor/tasks/04_data_validation_quality_gate.md`
   - Quality Gate: `scripts/test_data_validation_quality_gates.py`
   - Success: Data validation, data integrity, format validation

5. **Task 05**: Data Provider Factory Quality Gate
   - File: `.cursor/tasks/05_data_provider_factory_quality_gate.md`
   - Quality Gate: `scripts/test_data_provider_factory_quality_gates.py`
   - Success: Data provider factory, provider creation, registry management

6. **Task 06**: Data Availability Quality Gate
   - File: `.cursor/tasks/06_data_availability_quality_gate.md`
   - Quality Gate: `scripts/test_data_availability_quality_gates.py`
   - Success: Data availability, data file validation, completeness

7. **Task 07**: Docs Structure Validation Quality Gate
   - File: `.cursor/tasks/07_docs_structure_validation_quality_gate.md`
   - Quality Gate: `scripts/test_docs_structure_validation_quality_gates.py`
   - Success: Documentation structure, implementation gap detection

8. **Task 08**: Docs Link Validation Quality Gate
   - File: `.cursor/tasks/08_docs_link_validation_quality_gate.md`
   - Quality Gate: `scripts/test_docs_link_validation_quality_gates.py`
   - Success: Documentation link validation, broken link detection

9. **Task 09**: Implementation Gap Validation Quality Gate
   - File: `.cursor/tasks/09_implementation_gap_validation_quality_gate.md`
   - Quality Gate: `scripts/test_implementation_gap_quality_gates.py`
   - Success: Implementation gap detection, component alignment

10. **Task 10**: Health & Logging Quality Gate
    - File: `.cursor/tasks/10_health_logging_quality_gate.md`
    - Quality Gate: `scripts/test_health_logging_quality_gates.py`
    - Success: Health system validation, logging structure

**Success Criteria**:
- All foundation quality gates pass
- Environment switching works (dev/staging/prod)
- All YAML configs load with validation
- All data files validated for all modes
- Documentation structure and links validated

### Day 2: Component Unit Tests (Tasks 11-20) - 8 hours
**Priority**: HIGH - Core component validation

1. **Task 11**: Position Monitor Unit Quality Gate
   - File: `.cursor/tasks/11_position_monitor_unit_quality_gate.md`
   - Quality Gate: `tests/unit/test_position_monitor_unit.py`
   - Success: Position monitoring, balance tracking, persistence

2. **Task 12**: Exposure Monitor Unit Quality Gate
   - File: `.cursor/tasks/12_exposure_monitor_unit_quality_gate.md`
   - Quality Gate: `tests/unit/test_exposure_monitor_unit.py`
   - Success: Exposure monitoring, asset filtering

3. **Task 13**: Risk Monitor Unit Quality Gate
   - File: `.cursor/tasks/13_risk_monitor_unit_quality_gate.md`
   - Quality Gate: `tests/unit/test_risk_monitor_unit.py`
   - Success: Risk monitoring, risk calculations

4. **Task 14**: P&L Calculator Unit Quality Gate
   - File: `.cursor/tasks/14_pnl_monitor_unit_quality_gate.md`
   - Quality Gate: `tests/unit/test_pnl_monitor_unit.py`
   - Success: P&L calculation, attribution P&L

5. **Task 15**: Strategy Manager Unit Quality Gate
   - File: `.cursor/tasks/15_strategy_manager_unit_quality_gate.md`
   - Quality Gate: `tests/unit/test_strategy_manager_unit.py`
   - Success: Strategy management, inheritance-based architecture

6. **Task 16**: Venue Manager Unit Quality Gate
   - File: `.cursor/tasks/16_venue_manager_unit_quality_gate.md`
   - Quality Gate: `tests/unit/test_venue_manager_unit.py`
   - Success: Venue management, venue interface management

7. **Task 17**: Event Logger Unit Quality Gate
   - File: `.cursor/tasks/17_event_logger_unit_quality_gate.md`
   - Quality Gate: `tests/unit/test_event_logger_unit.py`
   - Success: Event logging functionality, formatting, error handling

8. **Task 18**: Results Store Unit Quality Gate
   - File: `.cursor/tasks/18_results_store_unit_quality_gate.md`
   - Quality Gate: `tests/unit/test_results_store_unit.py`
   - Success: Results storage, persistence

9. **Task 19**: Health System Unit Quality Gate
   - File: `.cursor/tasks/19_health_system_unit_quality_gate.md`
   - Quality Gate: `tests/unit/test_health_system_unit.py`
   - Success: Health system functionality, health monitoring

10. **Task 20**: Config Manager Unit Quality Gate
    - File: `.cursor/tasks/20_config_manager_unit_quality_gate.md`
    - Quality Gate: `tests/unit/test_config_manager_unit.py`
    - Success: Config management, configuration loading

**Success Criteria**:
- All component unit tests pass
- 80% test coverage achieved for core components
- All components aligned with canonical specifications

### Day 3: Architecture Validation (Tasks 21-25) - 6 hours
**Priority**: HIGH - Architecture pattern validation

1. **Task 21**: Reference Architecture Quality Gate
   - File: `.cursor/tasks/21_reference_architecture_quality_gate.md`
   - Quality Gate: `scripts/test_reference_architecture_quality_gates.py`
   - Success: Reference architecture compliance, architectural patterns

2. **Task 22**: Mode-Agnostic Design Quality Gate
   - File: `.cursor/tasks/22_mode_agnostic_design_quality_gate.md`
   - Quality Gate: `scripts/test_mode_agnostic_design_quality_gates.py`
   - Success: Mode-agnostic design patterns, config-driven architecture

3. **Task 23**: Singleton Pattern Quality Gate
   - File: `.cursor/tasks/23_singleton_pattern_quality_gate.md`
   - Quality Gate: `scripts/test_singleton_pattern_quality_gates.py`
   - Success: Singleton pattern implementation, single instances per request

4. **Task 24**: Async/Await Fixes Quality Gate
   - File: `.cursor/tasks/24_async_await_fixes_quality_gate.md`
   - Quality Gate: `scripts/test_async_await_fixes_quality_gates.py`
   - Success: Async/await pattern fixes, ADR-006 compliance

5. **Task 25**: Fail-Fast Configuration Quality Gate
   - File: `.cursor/tasks/25_fail_fast_configuration_quality_gate.md`
   - Quality Gate: `scripts/test_fail_fast_configuration_quality_gates.py`
   - Success: Fail-fast configuration, direct config access

**Success Criteria**:
- All architecture validation quality gates pass
- Reference architecture compliance validated
- Mode-agnostic design patterns working
- Singleton pattern implementation correct

### Day 4: Integration Tests (Tasks 26-30) - 6 hours
**Priority**: HIGH - Component integration validation

1. **Task 26**: Data Flow Position→Exposure Quality Gate
   - File: `.cursor/tasks/26_data_flow_position_to_exposure_quality_gate.md`
   - Quality Gate: `tests/integration/test_data_flow_position_to_exposure.py`
   - Success: Position→Exposure data flow, state persistence, venue aggregation

2. **Task 27**: Data Flow Exposure→Risk Quality Gate
   - File: `.cursor/tasks/27_data_flow_exposure_to_risk_quality_gate.md`
   - Quality Gate: `tests/integration/test_data_flow_exposure_to_risk.py`
   - Success: Exposure→Risk data flow, risk calculations

3. **Task 28**: Data Flow Risk→Strategy Quality Gate
   - File: `.cursor/tasks/28_data_flow_risk_to_strategy_quality_gate.md`
   - Quality Gate: `tests/integration/test_data_flow_risk_to_strategy.py`
   - Success: Risk→Strategy data flow, strategy decisions

4. **Task 29**: Data Flow Strategy→Execution Quality Gate
   - File: `.cursor/tasks/29_data_flow_strategy_to_execution_quality_gate.md`
   - Quality Gate: `tests/integration/test_data_flow_strategy_to_execution.py`
   - Success: Strategy→Execution data flow, execution instructions

5. **Task 30**: Tight Loop Reconciliation Quality Gate
   - File: `.cursor/tasks/30_tight_loop_reconciliation_quality_gate.md`
   - Quality Gate: `tests/integration/test_tight_loop_reconciliation.py`
   - Success: Tight loop reconciliation, sequential chain, reconciliation handshake

**Success Criteria**:
- All integration tests pass
- Data flows work correctly between components
- Tight loop reconciliation working
- 70%+ integration test coverage achieved

### Day 5: API & Service Tests (Tasks 31-35) - 6 hours
**Priority**: HIGH - API and service validation

1. **Task 31**: API Endpoints Quality Gate
   - File: `.cursor/tasks/31_api_endpoints_quality_gate.md`
   - Quality Gate: `tests/integration/test_api_endpoints_quality_gates.py`
   - Success: API endpoints, API functionality, integration tests

2. **Task 32**: Health Monitoring Quality Gate
   - File: `.cursor/tasks/32_health_monitoring_quality_gate.md`
   - Quality Gate: `tests/integration/test_health_monitoring_quality_gates.py`
   - Success: Health monitoring, health system integration

3. **Task 33**: Backtest Service Quality Gate
   - File: `.cursor/tasks/33_backtest_service_quality_gate.md`
   - Quality Gate: `tests/unit/test_backtest_service_unit.py`
   - Success: Backtest service, service layer validation

4. **Task 34**: Live Service Quality Gate
   - File: `.cursor/tasks/34_live_service_quality_gate.md`
   - Quality Gate: `tests/unit/test_live_service_unit.py`
   - Success: Live service, live trading service

5. **Task 35**: Repo Structure Integration Quality Gate
   - File: `.cursor/tasks/35_repo_structure_integration_quality_gate.md`
   - Quality Gate: `tests/integration/test_repo_structure_integration.py`
   - Success: Repository structure validation, file organization

**Success Criteria**:
- All API and service tests pass
- API endpoints functionality validated
- Health monitoring working correctly
- Service layer validation complete

### Day 6: E2E Strategy Tests (Tasks 36-43) - 8 hours
**Priority**: HIGH - End-to-end strategy validation

1. **Task 36**: Pure Lending E2E Quality Gate
   - File: `.cursor/tasks/36_pure_lending_usdt_e2e_quality_gate.md`
   - Quality Gate: `tests/e2e/test_pure_lending_usdt_e2e.py`
   - Success: Pure lending strategy execution, 3-8% APY validation

2. **Task 37**: BTC Basis E2E Quality Gate
   - File: `.cursor/tasks/37_btc_basis_e2e_quality_gate.md`
   - Quality Gate: `tests/e2e/test_btc_basis_e2e.py`
   - Success: BTC basis strategy execution, funding rate calculations

3. **Task 38**: ETH Basis E2E Quality Gate
   - File: `.cursor/tasks/38_eth_basis_e2e_quality_gate.md`
   - Quality Gate: `tests/e2e/test_eth_basis_e2e.py`
   - Success: ETH basis strategy execution, ETH mechanics, LST integration

4. **Task 39**: USDT Market Neutral E2E Quality Gate
   - File: `.cursor/tasks/39_usdt_market_neutral_e2e_quality_gate.md`
   - Quality Gate: `tests/e2e/test_usdt_market_neutral_e2e.py`
   - Success: USDT market neutral strategy execution, full leverage, multi-venue hedging

5. **Task 40**: ETH Staking Only E2E Quality Gate
   - File: `.cursor/tasks/40_eth_staking_only_e2e_quality_gate.md`
   - Quality Gate: `tests/e2e/test_eth_staking_only_e2e.py`
   - Success: ETH staking only strategy execution, staking mechanics

6. **Task 41**: ETH Leveraged Staking E2E Quality Gate
   - File: `.cursor/tasks/41_eth_leveraged_staking_e2e_quality_gate.md`
   - Quality Gate: `tests/e2e/test_eth_leveraged_staking_e2e.py`
   - Success: ETH leveraged staking strategy execution, leveraged staking mechanics

7. **Task 42**: USDT Market Neutral No Leverage E2E Quality Gate
   - File: `.cursor/tasks/42_usdt_market_neutral_no_leverage_e2e_quality_gate.md`
   - Quality Gate: `tests/e2e/test_usdt_market_neutral_no_leverage_e2e.py`
   - Success: USDT market neutral no leverage strategy execution, hedging without leverage

8. **Task 43**: Performance E2E Quality Gate
   - File: `.cursor/tasks/43_performance_e2e_quality_gate.md`
   - Quality Gate: `tests/e2e/test_performance_e2e.py`
   - Success: Performance validation, system performance benchmarks

**Success Criteria**:
- All E2E strategy tests pass
- All 7 strategy modes working correctly
- Performance benchmarks met
- System ready for production deployment

## Canonical Documentation References

### Primary Canonical Sources
- **Architecture**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Single source of truth for all architectural principles
- **Strategy Modes**: `docs/MODES.md` - Canonical strategy mode definitions
- **Component Specs**: `docs/specs/` - Detailed component implementation guides
- **Workflow Guide**: `docs/WORKFLOW_GUIDE.md` - Component data flow patterns
- **Target Structure**: `docs/TARGET_REPOSITORY_STRUCTURE.md` - File organization rules

### Task-to-Documentation Mapping

**Foundation Tasks (01-03)**:
- Task 01: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6.1 (Environment switching)
- Task 02: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6.1 (Config validation)
- Task 03: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 8 (Data loading)

**Architecture Tasks (04-14)**:
- Task 04: `docs/specs/12_FRONTEND_SPEC.md` (API endpoints)
- Task 05: `docs/specs/HEALTH_ERROR_SYSTEMS.md` (Health & logging)
- Task 06: `docs/specs/05_STRATEGY_MANAGER.md` (Strategy manager)
- Task 07: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6 (Async/await)
- Task 08: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 7 (Mode-agnostic)
- Task 09: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6.1 (Fail-fast)
- Task 10: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 1 (Reference-based)
- Task 11: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 2 (Singleton)
- Task 12: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 3 (Tight loop)
- Task 13: `docs/specs/03_RISK_MONITOR.md` (Risk monitor consolidation)
- Task 14: `docs/WORKFLOW_GUIDE.md` (Component data flows)

**Strategy Tasks (15-18)**:
- Task 15: `docs/MODES.md` (Pure lending mode)
- Task 16: `docs/MODES.md` (BTC basis mode)
- Task 17: `docs/MODES.md` (ETH basis mode)
- Task 18: `docs/MODES.md` (USDT market neutral mode)

**Component Tasks (19-23)**:
- Task 19: `docs/specs/01_POSITION_MONITOR.md`
- Task 20: `docs/specs/02_EXPOSURE_MONITOR.md`
- Task 21: `docs/specs/03_RISK_MONITOR.md`
- Task 22: `docs/specs/05_STRATEGY_MANAGER.md`
- Task 23: `docs/specs/04_pnl_monitor.md`

**Infrastructure Tasks (24-31)**:
- Task 24: `docs/specs/12_FRONTEND_SPEC.md` (Frontend - EXCLUDED)
- Task 25: `docs/specs/14_LIVE_TRADING_SERVICE.md` (Live mode)
- Task 26: `docs/specs/13_BACKTEST_SERVICE.md` (Service validation)
- Task 27: `docs/specs/12_FRONTEND_SPEC.md` (Authentication - EXCLUDED)
- Task 28: `docs/specs/12_FRONTEND_SPEC.md` (Live trading UI - EXCLUDED)
- Task 29: `docs/specs/16_MATH_UTILITIES.md` (Shared utilities)
- Task 30: `docs/specs/06_VENUE_MANAGER.md`, `docs/specs/07_VENUE_INTERFACE_MANAGER.md`
- Task 31: `docs/specs/HEALTH_ERROR_SYSTEMS.md` (Infrastructure components)

**Test Tasks (32-43)**:
- Tasks 32-35: `docs/specs/` (Component unit tests)
- Tasks 36-40: `docs/WORKFLOW_GUIDE.md` (Integration tests)
- Tasks 41-43: `docs/MODES.md` (E2E strategy tests)

**Missing Test Creation Tasks (44-80)**:
- Tasks 44-51: API Routes unit tests (8 missing)
- Tasks 52-60: Core Strategies unit tests (9 missing)
- Tasks 61-73: Infrastructure Data unit tests (13 missing)
- Tasks 74-77: Core Math unit tests (4 missing)
- Tasks 78-80: Execution Interfaces unit tests (3 missing)
- Tasks 81-92: Zero Coverage components unit tests (12 missing)

**Note**: Tasks 44-92 are additional test creation tasks needed to achieve 80% coverage (66/82 files). These should be added to the task sequence after the current 43 tasks are completed.

## Task Execution Protocol

### Before Each Task
1. **Read Complete Task File**: Understand requirements and success criteria
2. **Review Canonical References**: Read the specific canonical document listed above
3. **Check Target Structure**: Verify files to modify/create against `docs/TARGET_REPOSITORY_STRUCTURE.md`
4. **Check Current Status**: Run relevant quality gates
5. **Plan Implementation**: Follow canonical patterns from Reference sections

### During Task Execution
1. **Follow Canonical Patterns**: Never violate patterns in Reference sections
2. **Follow Target Structure**: Strictly adhere to `docs/TARGET_REPOSITORY_STRUCTURE.md`
3. **Implement Changes**: Make required modifications only to files marked as `[KEEP]` or `[MODIFY]`
4. **Create Only Specified Files**: Only create files explicitly marked as `[CREATE]` in target structure
5. **Align with Specifications**: Ensure all implementations align with component specifications
6. **Test Incrementally**: Run quality gates after major changes
7. **Fix Issues**: Address failures without breaking canonical patterns

### After Each Task
1. **Run Task-Specific Quality Gate**: Verify task completion
2. **Run Post-Refactor Compliance Check**: If component was refactored, run `python scripts/test_implementation_gap_quality_gates.py`
3. **Document Results**: Record what was accomplished
4. **Check for Regressions**: Ensure no breaking changes
5. **Proceed to Next Task**: Continue autonomously

## Key Commands

### Fresh Machine Setup
```bash
# Install dependencies (REQUIRED for fresh machines)
pip3 install -r requirements.txt
cd frontend && npm install && cd ..

# Verify system requirements
python3 --version  # Requires Python 3.8+
node --version     # Requires Node.js 16+
```

### Environment Management
```bash
# Start backend in backtest mode
./platform.sh backtest

# Stop services
./platform.sh stop-local

# Check status
./platform.sh status
```

### Quality Gates
```bash
# Run all quality gates
python scripts/run_quality_gates.py

# Run specific quality gates
python scripts/test_environment_switching_quality_gates.py
python scripts/test_async_ordering_quality_gates.py
python scripts/run_quality_gates.py --category e2e_strategies

# Post-refactor compliance check (REQUIRED after component refactors)
python scripts/test_implementation_gap_quality_gates.py
```

### Testing
```bash
# Run test suite
cd tests && python -m pytest -v

# Check coverage
python scripts/analyze_test_coverage.py
```

### Day 7: Infrastructure & Live Mode Completion (Tasks 27-31) - 12-16 hours
**Priority**: MEDIUM - Infrastructure completion and live mode

1. **Task 27**: Infrastructure components completion
   - File: `.cursor/tasks/31_infrastructure_components_completion.md`
   - Reference: `docs/specs/16_MATH_UTILITIES.md`, `docs/specs/HEALTH_ERROR_SYSTEMS.md`
   - Success: Complete infrastructure components, unified health system

2. **Task 28**: Live mode quality gates
   - File: `.cursor/tasks/25_live_mode_quality_gates.md`
   - Reference: `docs/specs/14_LIVE_TRADING_SERVICE.md`
   - Success: Live data provider, execution framework

3. **Task 29**: Shared utilities implementation
   - File: `.cursor/tasks/29_shared_utilities.md`
   - Reference: `docs/specs/16_MATH_UTILITIES.md`
   - Success: Math utilities, shared helper functions

4. **Task 30**: Execution components implementation
   - File: `.cursor/tasks/30_execution_components_implementation.md`
   - Reference: `docs/specs/06_VENUE_MANAGER.md`, `docs/specs/07_VENUE_INTERFACE_MANAGER.md`
   - Success: Complete execution infrastructure, tight loop architecture

5. **Task 31**: Infrastructure components completion
   - File: `.cursor/tasks/31_infrastructure_components_completion.md`
   - Reference: `docs/specs/HEALTH_ERROR_SYSTEMS.md`
   - Success: Health systems, error handling, results store

**Success Criteria**:
- Infrastructure components complete and aligned with specs
- Live mode framework ready
- Shared utilities implemented
- Execution infrastructure complete
- All quality gates passing
- System ready for staging deployment

**Note**: Frontend tasks (24, 27, 28) are excluded - frontend is a separate challenge.

## Success Metrics

### Daily Targets
- **Day 1**: Foundation Quality Gates (Tasks 01-10) ✅
- **Day 2**: Component Unit Tests (Tasks 11-20) ✅
- **Day 3**: Architecture Validation (Tasks 21-25) ✅
- **Day 4**: Integration Tests (Tasks 26-30) ✅
- **Day 5**: API & Service Tests (Tasks 31-35) ✅
- **Day 6**: E2E Strategy Tests (Tasks 36-43) ✅

### Quality Gate Targets
- **Foundation**: 10/10 quality gates passing (100%)
- **Unit Tests**: 10/10 component tests passing (100%)
- **Architecture**: 5/5 validation tests passing (100%)
- **Integration**: 5/5 integration tests passing (100%)
- **API & Services**: 5/5 service tests passing (100%)
- **E2E Strategies**: 8/8 strategy tests passing (100%)

### Final Target
- **43/43 quality gate validation tasks completed** (100%)
- **All quality gates passing** (100%)
- **80% test coverage** (66/82 backend files)
- **All 7 strategy modes E2E working**
- **System ready for production deployment**

## Autonomous Operation

### No Approval Requests
- Execute tasks autonomously without stopping for approvals
- Quality gates are the only checkpoints
- Fix failures immediately without breaking patterns
- Continue until all 43 quality gate validation tasks complete

### Progress Tracking
- Log completion after each task
- Report quality gate results
- Document any issues encountered
- Update success criteria checkboxes

### Error Handling
- Log exact error messages
- Check relevant log files
- Attempt to fix errors
- Retry operations up to 3 times
- Document issues and continue

## Current Critical Issues

### Dependencies Not Installed (Fresh Machine)
- **Issue**: `./platform.sh backtest` fails if dependencies not installed
- **Action**: Install dependencies first: `pip3 install -r requirements.txt && cd frontend && npm install && cd ..`
- **Verify**: Check Python/Node versions and package installation

### Backend Not Running
- **Issue**: Connection timeout on localhost:8001
- **Action**: Start backend with `./platform.sh backtest` (after dependencies installed)
- **Verify**: `curl -s http://localhost:8001/health/`

### Quality Gates Need Improvement
- **Current**: 12/24 passing (50%)
- **Target**: 20/24 passing (83%)
- **Critical**: Need to address 20 component implementation gaps

### Test Coverage Gap Analysis
- **Current Coverage**: 35.3% (29/82 backend files)
- **Target Coverage**: 80% (66/82 backend files)
- **Missing Tests**: 37 additional test files needed

#### Critical Missing Test Categories:
1. **API Routes** (8 missing): auth, backtest, capital, charts, config, health, live_trading, results
2. **Core Strategies** (9 missing): All 7 strategy modes + factory + ML directional
3. **Infrastructure Data** (13 missing): All data provider implementations
4. **Core Math** (4 missing): health, ltv, margin, metrics calculators
5. **Execution Interfaces** (3 missing): CEX, onchain, transfer interfaces
6. **Zero Coverage** (12 missing): venue adapters, core services, utilities, error codes

#### Coverage Priority:
- **High Priority**: API routes, core strategies, data providers (critical path)
- **Medium Priority**: Core math, execution interfaces (important functionality)
- **Low Priority**: Infrastructure utilities, adapters (supporting components)

### Implementation Gaps
- **Component Alignment**: 20 components need alignment with canonical specifications
- **Execution Infrastructure**: Execution components need implementation/completion
- **Service Validation**: Service layer needs validation against specifications
- **Infrastructure Components**: Math utilities, health systems, results store need completion

## Repository Structure Compliance

### Target Repository Structure Rules
**CRITICAL**: Follow `docs/TARGET_REPOSITORY_STRUCTURE.md` exactly:

#### ✅ DO:
- **Use existing file structure** - Only modify files marked as `[KEEP]` or `[MODIFY]`
- **Create only specified files** - Only create files marked as `[CREATE]`
- **Follow import patterns** - Use correct imports from target structure
- **Maintain component hierarchy** - Follow the defined component dependencies
- **Use strategy factory pattern** - All 7 strategies must be registered in StrategyFactory.STRATEGY_MAP

#### ❌ DO NOT:
- **Create random files** - Only create files explicitly marked as `[CREATE]` in target structure
- **Recreate deleted files** - Files marked as `[DELETE]` should remain deleted
- **Use old import paths** - Use infrastructure/config, not core/config
- **Break strategy factory** - All strategies must be registered in factory
- **Add async to internal methods** - Keep components synchronous per target structure

#### File Status Legend:
- `[KEEP]` - File exists and should remain unchanged
- `[MODIFY]` - File exists but needs updates
- `[CREATE]` - File needs to be created
- `[DELETE]` - File should be deleted (already done)

#### Validation Checklist:
Before completing any task, verify:
- [ ] All imports use correct paths (infrastructure/config, not core/config)
- [ ] No deleted files are being recreated
- [ ] Strategy factory includes all 7 strategies
- [ ] Components are mode-agnostic
- [ ] No async in internal methods
- [ ] Fail-fast configuration is used
- [ ] Components align with canonical specifications
- [ ] Error codes are implemented per component specs
- [ ] Quality gates are updated to match new architecture

## Communication Protocol

### Progress Reports
- Report after each task completion
- Include quality gate results
- Highlight any blockers or issues
- Provide detailed explanations of changes

### Success Validation
- What was accomplished
- Current status vs target
- What needs to be done next
- Any blockers encountered
- Estimated completion time

**DO NOT STOP** until all 43 quality gate validation tasks are completed. Report progress after each task.

---

## START NOW

Begin with backend startup and Task 01 execution. The system has quality gates that need to be validated to achieve the 6-day quality gate validation targets.

**First Command**: `./platform.sh backtest`