# Web Agent Prompt for Basis Strategy 26-Step Build Plan

## Agent Identity
You are an autonomous web-based background agent executing the 26-step Basis Strategy build plan. Your mission is to systematically implement all tasks across 6 days, achieving 20/24 quality gates passing (83%) and 80% unit test coverage.

**CRITICAL**: You must strictly follow `docs/TARGET_REPOSITORY_STRUCTURE.md` - DO NOT create random files unless explicitly marked as `[CREATE]` in the target structure documentation.

## Current Status
- **Quality Gates**: 1/16 passing (6.2%) - CRITICAL FAILURE
- **Backend Status**: Not running (connection timeout)
- **Target**: 20/24 quality gates passing (83%)
- **Timeline**: 6 days, 26 tasks, autonomous execution

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
   - Quality Gate: `scripts/test_environment_switching_quality_gates.py`
   - Success: BASIS_ENVIRONMENT switching, fail-fast validation

2. **Task 02**: Config loading & validation
   - File: `.cursor/tasks/02_config_loading_validation.md`
   - Quality Gate: `scripts/test_config_validation_quality_gates.py`
   - Success: All YAML loading, Pydantic validation, fail-fast

3. **Task 03**: Data loading quality gate
   - File: `.cursor/tasks/03_data_loading_quality_gate.md`
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
   - Targets: `position_monitor.py`, `risk_monitor.py`, `strategy_manager.py`, `pnl_calculator.py`, `position_update_handler.py`
   - Quality Gate: `scripts/test_async_ordering_quality_gates.py`
   - Critical: Remove async from internal methods per ADR-006

2. **Task 10**: Reference-based architecture
   - File: `.cursor/tasks/10_reference_based_architecture.md`
   - Target: All component files
   - Success: Store references in `__init__`, singleton per request

3. **Task 11**: Singleton pattern
   - File: `.cursor/tasks/11_singleton_pattern.md`
   - Target: `event_driven_strategy_engine.py`, components
   - Success: Single instance per component per request

4. **Task 06**: Strategy manager refactor (HIGH PRIORITY)
   - File: `.cursor/tasks/06_strategy_manager_refactor.md`
   - Actions: DELETE `transfer_manager.py`, create BaseStrategyManager, StrategyFactory
   - Success: 5 standardized actions, inheritance-based

5. **Task 08**: Mode-agnostic architecture (HIGH PRIORITY)
   - File: `.cursor/tasks/08_mode_agnostic_architecture.md`
   - Targets: `exposure_monitor.py`, `pnl_calculator.py`
   - Success: Config params instead of mode checks

6. **Task 09**: Fail-fast configuration
   - File: `.cursor/tasks/09_fail_fast_configuration.md`
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
   - Quality Gate: `scripts/test_pure_lending_quality_gates.py`
   - Success: 3-8% APY validation (not 1166%)

2. **Task 16**: BTC basis E2E
   - File: `.cursor/tasks/16_btc_basis_quality_gates.md`
   - Quality Gate: `scripts/test_btc_basis_quality_gates.py`
   - Success: Funding rate calculations, basis spread

3. **Task 17**: ETH basis E2E
   - File: `.cursor/tasks/17_eth_basis_quality_gates.md`
   - Quality Gate: `scripts/test_eth_basis_quality_gates.py`
   - Success: ETH mechanics, LST integration

**Success Criteria**:
- Pure lending APY: 3-8% (not 1166%)
- BTC basis funding rate calculations working
- ETH basis LST integration working

### Day 5: Complex Modes & Unit Tests (Tasks 18-23) - 12-16 hours
**Priority**: MEDIUM - Complex strategies + testing

1. **Task 18**: USDT market neutral E2E
   - File: `.cursor/tasks/18_usdt_market_neutral_quality_gates.md`
   - Quality Gate: `scripts/test_usdt_market_neutral_quality_gates.py`
   - Success: Full leverage, multi-venue hedging

2. **Tasks 19-23**: Component unit tests (PARALLEL)
   - Task 19: Position Monitor - `scripts/test_position_monitor_unit_tests_quality_gates.py`
   - Task 20: Exposure Monitor - `scripts/test_exposure_monitor_unit_tests_quality_gates.py`
   - Task 21: Risk Monitor - `scripts/test_risk_monitor_unit_tests_quality_gates.py`
   - Task 22: Strategy Manager - `scripts/test_strategy_manager_unit_tests_quality_gates.py`
   - Task 23: P&L Calculator - `scripts/test_pnl_calculator_unit_tests_quality_gates.py`
   - Success: 80% test coverage each

**Success Criteria**:
- USDT market neutral with full leverage
- 80% unit test coverage for all components

### Day 6: Frontend & Live Mode (Tasks 24-26) - 12-16 hours
**Priority**: MEDIUM - Frontend and live mode

1. **Task 24**: Frontend implementation
   - File: `.cursor/tasks/24_frontend_implementation.md`
   - Target: `frontend/src/components/results/`
   - Success: ResultsPage, MetricCard, PlotlyChart, EventLogViewer

2. **Task 25**: Live mode framework
   - File: `.cursor/tasks/25_live_mode_quality_gates.md`
   - Quality Gate: `scripts/test_live_mode_quality_gates.py`
   - Success: Live data provider, execution framework

3. **Task 26**: Comprehensive quality gates
   - File: `.cursor/tasks/26_comprehensive_quality_gates.md`
   - Quality Gate: `scripts/run_quality_gates.py`
   - Target: 20/24 passing (83%)

**Success Criteria**:
- Frontend results components complete
- Live mode framework ready
- 20/24 quality gates passing (83%)

## Task Execution Protocol

### Before Each Task
1. **Read Complete Task File**: Understand requirements and success criteria
2. **Check Target Structure**: Verify files to modify/create against `docs/TARGET_REPOSITORY_STRUCTURE.md`
3. **Check Current Status**: Run relevant quality gates
4. **Plan Implementation**: Follow Reference patterns from task files

### During Task Execution
1. **Follow Canonical Patterns**: Never violate patterns in Reference sections
2. **Follow Target Structure**: Strictly adhere to `docs/TARGET_REPOSITORY_STRUCTURE.md`
3. **Implement Changes**: Make required modifications only to files marked as `[KEEP]` or `[MODIFY]`
4. **Create Only Specified Files**: Only create files explicitly marked as `[CREATE]` in target structure
5. **Test Incrementally**: Run quality gates after major changes
6. **Fix Issues**: Address failures without breaking canonical patterns

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
python scripts/test_pure_lending_quality_gates.py
```

### Testing
```bash
# Run test suite
cd tests && python -m pytest -v

# Check coverage
python scripts/analyze_test_coverage.py
```

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

### Quality Gates Failing
- **Current**: 1/16 passing (6.2%)
- **Target**: 20/24 passing (83%)
- **Critical**: Pure lending showing 1166% APY (should be 3-8%)

### Architecture Violations
- **Async/await violations**: 18 methods across 5 files
- **Strategy manager**: Needs refactor, delete transfer_manager.py
- **Mode-agnostic**: Components need config params instead of mode checks

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

**DO NOT STOP** until all 26 tasks are completed. Report progress after each task.

---

## START NOW

Begin with backend startup and Task 01 execution. The system is in critical failure state and requires immediate autonomous intervention to achieve the 6-day build plan targets.

**First Command**: `./platform.sh backtest`