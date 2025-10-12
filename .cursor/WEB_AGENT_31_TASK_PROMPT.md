# Web Agent Prompt for Basis Strategy Implementation Gap Build Plan

## How to Start This Agent

Copy this entire prompt into your background agent setup. This agent will autonomously execute all 43 tasks to achieve:
- 100% test coverage across all components and strategies
- All quality gates passing
- Complete integration test suite
- Full E2E test coverage for all 7 strategy modes

**Prerequisites:**
1. Backend running: `./platform.sh backtest`
2. Dependencies installed: `pip3 install -r requirements.txt`
3. Quality gates baseline: `python scripts/run_quality_gates.py`

**Execution Strategy:**
- Tasks 01-03: Foundation (config, data)
- Tasks 04-14: Architecture & core components
- Tasks 32-35: Missing component tests
- Tasks 36-40: Integration tests
- Tasks 15-18, 41-43: E2E strategy tests
- Tasks 19-23: Component unit tests
- Tasks 24-31: Frontend & live mode

The agent will execute autonomously without approval requests between tasks.

## Agent Identity
You are an autonomous web-based background agent executing the Basis Strategy implementation gap build plan. Your mission is to systematically address all 20 component implementation gaps across 7 days, achieving 20/24 quality gates passing (83%) and 80% unit test coverage.

**CRITICAL**: You must strictly follow canonical documentation references in all tasks - DO NOT create random files unless explicitly marked as `[CREATE]` in the target structure documentation.

## Current Status
- **Quality Gates**: 2/23 passing (8.7%) - REFACTORED STRUCTURE
- **Implementation Gaps**: 13 components need alignment/completion (8 failing + 5 partial)
- **Backend Status**: Infrastructure mostly complete, frontend needs production completion
- **Target**: 80%+ unit tests, 70%+ integration tests, E2E tests when foundation solid
- **Timeline**: 7 days, 43 tasks, autonomous execution

## Quality Gate Status Report (REFACTORED)
**CRITICAL**: Quality gates have been refactored into 3-tier structure to address cascading failures:

### New 3-Tier Structure:
- **Unit Tests**: 8 component isolation tests (target: 80%+ passing)
- **Integration Tests**: 5 component data flow tests (target: 70%+ passing)  
- **E2E Tests**: 4 strategy execution tests (run only when foundation solid)

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
- **Expected**: 80%+ unit tests, 70%+ integration tests, meaningful E2E results

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
- **Unit Tests**: 8 component isolation tests in `tests/unit/` with mocked dependencies
- **Integration Tests**: 5 component data flow tests in `tests/integration/` with real components
- **E2E Tests**: 4 strategy execution tests in `tests/e2e/` with full system (non-critical)
- **Smart Skipping**: E2E tests skip if unit/integration < 80% passing
- **Conventional Structure**: All tests now in standard `tests/` directory
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

## Day-by-Day Execution Plan

### Day 1: Foundation (Tasks 01-03) - 8 hours
**Priority**: CRITICAL - Foundation must be solid

1. **Task 01**: Environment file switching & fail-fast validation
   - File: `.cursor/tasks/01_environment_file_switching.md`
   - Reference: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6.1
   - Quality Gate: `scripts/test_environment_switching_quality_gates.py`
   - Success: BASIS_ENVIRONMENT switching, fail-fast validation

2. **Task 02**: Config loading & validation
   - File: `.cursor/tasks/02_config_loading_validation.md`
   - Reference: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6.1
   - Quality Gate: `scripts/test_config_validation_quality_gates.py`
   - Success: All YAML loading, Pydantic validation, fail-fast

3. **Task 03**: Data loading quality gate
   - File: `.cursor/tasks/03_data_loading_quality_gate.md`
   - Reference: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 8
   - Quality Gate: `scripts/test_data_provider_refactor_quality_gates.py`
   - Success: All data files validated for all modes

**Success Criteria**:
- Environment switching works (dev/staging/prod)
- All YAML configs load with validation
- All data files validated for all modes

### Day 2: Core Architecture (Tasks 07,10,11,06,08,09) - 12-16 hours
**Priority**: HIGH - Fix architectural violations

1. **Task 07**: Fix async/await violations (HIGH PRIORITY)
   - File: `.cursor/tasks/07_fix_async_await_violations.md`
   - Reference: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6
   - Targets: `position_monitor.py`, `risk_monitor.py`, `strategy_manager.py`, `pnl_calculator.py`, `position_update_handler.py`
   - Quality Gate: `scripts/test_async_ordering_quality_gates.py`
   - Critical: Remove async from internal methods per ADR-006

2. **Task 10**: Reference-based architecture
   - File: `.cursor/tasks/10_reference_based_architecture.md`
   - Reference: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 1
   - Target: All component files
   - Success: Store references in `__init__`, singleton per request

3. **Task 11**: Singleton pattern
   - File: `.cursor/tasks/11_singleton_pattern.md`
   - Reference: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 2
   - Target: `event_driven_strategy_engine.py`, components
   - Success: Single instance per component per request

4. **Task 06**: Strategy manager refactor (HIGH PRIORITY)
   - File: `.cursor/tasks/06_strategy_manager_refactor.md`
   - Reference: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 3
   - Actions: DELETE `transfer_manager.py`, create BaseStrategyManager, StrategyFactory
   - Success: 5 standardized actions, inheritance-based

5. **Task 08**: Mode-agnostic architecture (HIGH PRIORITY)
   - File: `.cursor/tasks/08_mode_agnostic_architecture.md`
   - Reference: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 7
   - Targets: `exposure_monitor.py`, `pnl_calculator.py`
   - Success: Config params instead of mode checks

6. **Task 09**: Fail-fast configuration
   - File: `.cursor/tasks/09_fail_fast_19_CONFIGURATION.md`
   - Reference: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6.1
   - Target: `risk_monitor.py` (62 `.get()` instances)
   - Success: Direct config access, no defaults

**Success Criteria**:
- All async/await violations removed from internal methods
- Components use reference-based architecture
- Single instance per component per request
- Strategy manager uses inheritance-based approach

### Day 3: Integration (Tasks 12-14,04-05) - 12-16 hours
**Priority**: HIGH - Component integration

1. **Task 12**: Tight loop architecture
   - File: `.cursor/tasks/12_tight_loop_architecture.md`
   - Targets: `position_monitor.py`, `position_update_handler.py`, `execution_manager.py`
   - Quality Gate: `scripts/test_tight_loop_quality_gates.py`
   - Success: Sequential chain with reconciliation handshake

2. **Task 13**: Consolidate duplicate risk monitors
   - File: `.cursor/tasks/13_consolidate_duplicate_risk_monitors.md`
   - Action: DELETE `core/rebalancing/risk_monitor.py`
   - Success: Single risk monitor, imports updated

3. **Task 14**: Component data flow architecture
   - File: `.cursor/tasks/14_component_data_flow_architecture.md`
   - Target: `docs/specs/` (all component specs)
   - Success: Parameter-based data flow documented

4. **Task 04**: Complete API endpoints
   - File: `.cursor/tasks/04_complete_api_endpoints.md`
   - Target: `backend/src/basis_strategy_v1/api/`
   - Quality Gate: `scripts/test_api_endpoints_quality_gates.py`
   - Success: All strategy, backtest, results endpoints

5. **Task 05**: Health & logging
   - File: `.cursor/tasks/05_health_logging_structure.md`
   - Target: `backend/src/basis_strategy_v1/infrastructure/health/`
   - Quality Gate: `scripts/test_health_logging_quality_gates.py`
   - Success: Unified health system, structured logging

**Success Criteria**:
- Tight loop reconciliation working
- Single risk monitor (delete duplicate)
- All API endpoints complete
- Unified health system

### Day 4: Strategy Validation (Tasks 15-17) - 12-16 hours
**Priority**: HIGH - E2E strategy validation

1. **Task 15**: Pure lending E2E
   - File: `.cursor/tasks/15_pure_lending_quality_gates.md`
   - Quality Gate: `tests/e2e/test_pure_lending_e2e.py`
   - Success: 3-8% APY validation (not 1166%)

2. **Task 16**: BTC basis E2E
   - File: `.cursor/tasks/16_btc_basis_quality_gates.md`
   - Quality Gate: `tests/e2e/test_btc_basis_e2e.py`
   - Success: Funding rate calculations, basis spread

3. **Task 17**: ETH basis E2E
   - File: `.cursor/tasks/17_eth_basis_quality_gates.md`
   - Quality Gate: `tests/e2e/test_eth_basis_e2e.py`
   - Success: ETH mechanics, LST integration

**Success Criteria**:
- Pure lending APY: 3-8% (not 1166%)
- BTC basis funding rate calculations working
- ETH basis LST integration working

### Day 5: Component Alignment & Unit Tests (Tasks 18-23) - 12-16 hours
**Priority**: HIGH - Component alignment with specs + testing

1. **Task 18**: USDT market neutral E2E
   - File: `.cursor/tasks/18_usdt_market_neutral_quality_gates.md`
   - Quality Gate: `tests/e2e/test_usdt_market_neutral_e2e.py`
   - Success: Full leverage, multi-venue hedging

2. **Tasks 19-23**: Component alignment & unit tests (PARALLEL)
   - Task 19: Position Monitor Alignment - `docs/specs/01_POSITION_MONITOR.md`
   - Task 20: Exposure Monitor Alignment - `docs/specs/02_EXPOSURE_MONITOR.md`
   - Task 21: Risk Monitor Alignment - `docs/specs/03_RISK_MONITOR.md`
   - Task 22: Strategy Manager Unit Tests - `docs/specs/05_STRATEGY_MANAGER.md`
   - Task 23: P&L Calculator Alignment - `docs/specs/04_PNL_CALCULATOR.md`
   - Success: 80% test coverage each, alignment with canonical specs

**Success Criteria**:
- USDT market neutral with full leverage
- All monitoring components aligned with canonical specifications
- 80% unit test coverage for all components

### Day 6: Execution Infrastructure & Service Validation (Tasks 24-26) - 12-16 hours
**Priority**: HIGH - Execution infrastructure and service validation

1. **Task 24**: Execution components implementation
   - File: `.cursor/tasks/30_execution_components_implementation.md`
   - Reference: `docs/specs/06_EXECUTION_MANAGER.md`, `docs/specs/07_EXECUTION_INTERFACE_MANAGER.md`
   - Success: Complete execution infrastructure, tight loop architecture

2. **Task 25**: Service layer & engine validation
   - File: `.cursor/tasks/26_comprehensive_quality_gates.md`
   - Reference: `docs/specs/13_BACKTEST_SERVICE.md`, `docs/specs/14_LIVE_TRADING_SERVICE.md`
   - Quality Gate: `scripts/run_quality_gates.py`
   - Success: Service layer validation, request isolation compliance

3. **Task 26**: Live mode quality gates
   - File: `.cursor/tasks/25_live_mode_quality_gates.md`
   - Quality Gate: `scripts/test_live_mode_quality_gates.py`
   - Success: Live data provider, execution framework

**Success Criteria**:
- Execution infrastructure complete and aligned with specs
- Service layer validation complete
- Live mode framework ready
- 18/24 quality gates passing (75%)

## Task Execution Protocol

### Before Each Task
1. **Read Complete Task File**: Understand requirements and success criteria
2. **Review Canonical References**: Read all Reference sections in task files
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
2. **Document Results**: Record what was accomplished
3. **Check for Regressions**: Ensure no breaking changes
4. **Proceed to Next Task**: Continue autonomously

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
```

### Testing
```bash
# Run test suite
cd tests && python -m pytest -v

# Check coverage
python scripts/analyze_test_coverage.py
```

### Day 7: Infrastructure & Frontend Completion (Tasks 27-30) - 12-16 hours
**Priority**: MEDIUM - Infrastructure completion and frontend

1. **Task 27**: Infrastructure components completion
   - File: `.cursor/tasks/31_infrastructure_components_completion.md`
   - Reference: `docs/specs/16_MATH_UTILITIES.md`, `docs/specs/17_HEALTH_ERROR_SYSTEMS.md`
   - Success: Complete infrastructure components, unified health system

2. **Task 28**: Frontend implementation completion
   - File: `.cursor/tasks/24_frontend_implementation.md`
   - Reference: `docs/specs/12_FRONTEND_SPEC.md`
   - Success: Complete frontend implementation per specs

3. **Task 29**: Authentication system implementation
   - File: `.cursor/tasks/27_authentication_system.md`
   - Reference: `docs/specs/12_FRONTEND_SPEC.md` (authentication section)
   - Success: Username/password authentication, JWT tokens

4. **Task 30**: Live trading UI implementation
   - File: `.cursor/tasks/28_live_trading_ui.md`
   - Reference: `docs/specs/12_FRONTEND_SPEC.md` (live trading section)
   - Success: Live trading controls, real-time monitoring

**Success Criteria**:
- Infrastructure components complete and aligned with specs
- Frontend implementation complete per specifications
- Authentication system functional
- Live trading UI complete
- 20/24 quality gates passing (83%)
- System ready for staging deployment

## Success Metrics

### Daily Targets
- **Day 1**: Environment + config + data foundation ✅
- **Day 2**: Core architecture violations fixed ✅
- **Day 3**: Component integration complete ✅
- **Day 4**: 3 strategy modes E2E passing ✅
- **Day 5**: Component alignment + 80% unit coverage ✅
- **Day 6**: Execution infrastructure + service validation ✅
- **Day 7**: Infrastructure + frontend completion ✅

### Final Target
- **30/30 tasks completed** (100%)
- **20/24 quality gates passing** (83%)
- **All 20 component implementation gaps addressed**
- **80% unit test coverage**
- **4/4 strategy modes E2E working**
- **System ready for staging deployment**

## Autonomous Operation

### No Approval Requests
- Execute tasks autonomously without stopping for approvals
- Quality gates are the only checkpoints
- Fix failures immediately without breaking patterns
- Continue until all 26 tasks complete

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

**DO NOT STOP** until all 30 tasks are completed. Report progress after each task.

---

## START NOW

Begin with backend startup and Task 01 execution. The system has implementation gaps that need to be addressed to achieve the 7-day build plan targets.

**First Command**: `./platform.sh backtest`