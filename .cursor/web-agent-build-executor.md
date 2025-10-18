# Web Agent Build Executor - 26-Step Implementation Plan

## Mission Statement
You are an autonomous web-based background agent executing the 26-step Basis Strategy build plan. Your mission is to systematically implement all tasks across 6 days, achieving 20/24 quality gates passing (83%) and 80% unit test coverage.

## Current Status Analysis
- **Quality Gates**: 1/16 passing (6.2%) - CRITICAL FAILURE
- **Backend Status**: Not running (connection timeout)
- **Target**: 20/24 quality gates passing (83%)
- **Timeline**: 6 days, 26 tasks, autonomous execution

## Execution Protocol

### Phase 1: Environment Setup & Validation
1. **Start Backend**: `./platform.sh backtest` (force backtest mode)
2. **Verify Health**: `curl -s http://localhost:8001/health/`
3. **Baseline Quality Gates**: `python scripts/run_quality_gates.py`
4. **Document Starting Point**: Record current 1/16 passing status

### Phase 2: Day-by-Day Task Execution

#### Day 1: Foundation (Tasks 01-03)
**Priority**: CRITICAL - Foundation must be solid
- **Task 01**: Environment file switching & fail-fast validation
- **Task 02**: Config loading & validation with Pydantic
- **Task 03**: Data loading quality gate for all modes

**Success Criteria**:
- Environment switching works (dev/staging/prod)
- All YAML configs load with validation
- All data files validated for all modes

#### Day 2: Core Architecture (Tasks 07,10,11,06,08,09)
**Priority**: HIGH - Fix architectural violations
- **Task 07**: Fix async/await violations (18 methods across 5 files)
- **Task 10**: Reference-based architecture implementation
- **Task 11**: Singleton pattern enforcement
- **Task 06**: Strategy manager refactor (DELETE transfer_manager.py)
- **Task 08**: Mode-agnostic architecture
- **Task 09**: Fail-fast configuration (62 .get() instances)

**Success Criteria**:
- All async/await violations removed from internal methods
- Components use reference-based architecture
- Single instance per component per request
- Strategy manager uses inheritance-based approach

#### Day 3: Integration (Tasks 12-14,04-05)
**Priority**: HIGH - Component integration
- **Task 12**: Tight loop architecture implementation
- **Task 13**: Consolidate duplicate risk monitors
- **Task 14**: Component data flow architecture
- **Task 04**: Complete API endpoints
- **Task 05**: Health & logging structure

**Success Criteria**:
- Tight loop reconciliation working
- Single risk monitor (delete duplicate)
- All API endpoints complete
- Unified health system

#### Day 4: Strategy Validation (Tasks 15-17)
**Priority**: HIGH - E2E strategy validation
- **Task 15**: Pure lending E2E (fix 1166% APY → 3-8%)
- **Task 16**: BTC basis E2E validation
- **Task 17**: ETH basis E2E validation

**Success Criteria**:
- Pure lending APY: 3-8% (not 1166%)
- BTC basis funding rate calculations working
- ETH basis LST integration working

#### Day 5: Complex Modes & Unit Tests (Tasks 18-23)
**Priority**: MEDIUM - Complex strategies + testing
- **Task 18**: USDT market neutral E2E
- **Tasks 19-23**: Component unit tests (80% coverage each)

**Success Criteria**:
- USDT market neutral with full leverage
- 80% unit test coverage for all components

#### Day 6: Frontend & Live Mode (Tasks 24-26)
**Priority**: MEDIUM - Frontend and live mode
- **Task 24**: Frontend implementation
- **Task 25**: Live mode framework
- **Task 26**: Comprehensive quality gates

**Success Criteria**:
- Frontend results components complete
- Live mode framework ready
- 20/24 quality gates passing (83%)

## Quality Gate Protocol

### Before Each Task
1. **Read Complete Task File**: Understand requirements and success criteria
2. **Check Current Status**: Run relevant quality gates
3. **Plan Implementation**: Follow Reference patterns from task files

### During Task Execution
1. **Follow Canonical Patterns**: Never violate patterns in Reference sections
2. **Implement Changes**: Make required modifications
3. **Test Incrementally**: Run quality gates after major changes
4. **Fix Issues**: Address failures without breaking canonical patterns

### After Each Task
1. **Run Task-Specific Quality Gate**: Verify task completion
2. **Document Results**: Record what was accomplished
3. **Check for Regressions**: Ensure no breaking changes
4. **Proceed to Next Task**: Continue autonomously

## Critical Rules

### Canonical Pattern Preservation
- **Reference sections are law** - Never violate patterns in task Reference sections
- **ADR compliance** - All fixes must follow Architectural Decision Records
- **No backward compatibility** - Break cleanly, update all references

### Server Management
- **Use `./platform.sh backtest`** to start backend in backtest mode
- **Use `./platform.sh stop-local`** before restarting
- **Restart server before long-running tests** if needed
- **Check server status** with `ps aux | grep python` if commands hang

### Error Handling
- **10-minute timeout per command**
- **Max 3 retry attempts**
- **Restart backend if needed**
- **Document and continue** (don't stop for approvals)

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

### Parallelization (Where Noted)
- **Day 2**: Tasks 6, 8, 9 can run parallel
- **Day 3**: Tasks 4, 5 can run parallel
- **Day 5**: Tasks 19-23 can run parallel
- **Day 6**: Tasks 24, 25 can run parallel

## Key Commands

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
python scripts/test_pure_lending_usdt_quality_gates.py
```

### Testing
```bash
# Run test suite
cd tests && python -m pytest -v

# Check coverage
python scripts/analyze_test_coverage.py
```

## Current Critical Issues

### Backend Not Running
- **Issue**: Connection timeout on localhost:8001
- **Action**: Start backend with `./platform.sh backtest`
- **Verify**: `curl -s http://localhost:8001/health/`

### Quality Gates Failing
- **Current**: 1/16 passing (6.2%)
- **Target**: 20/24 passing (83%)
- **Critical**: Pure lending showing 1166% APY (should be 3-8%)

### Architecture Violations
- **Async/await violations**: 18 methods across 5 files
- **Strategy manager**: Needs refactor, delete transfer_manager.py
- **Mode-agnostic**: Components need config params instead of mode checks

## Execution Strategy

### Start Immediately
1. **Start Backend**: `./platform.sh backtest`
2. **Verify Health**: Check backend is responding
3. **Begin Day 1**: Start with Task 01 (Environment file switching)
4. **Execute Autonomously**: Continue through all 26 tasks

### Daily Checkpoints
- **End of Day 1**: Environment + config + data foundation complete
- **End of Day 2**: Core architecture violations fixed
- **End of Day 3**: Component integration complete
- **End of Day 4**: 3 strategy modes E2E passing
- **End of Day 5**: Complex strategy + 80% unit coverage
- **End of Day 6**: Frontend + live mode + 20/24 gates passing

### Final Validation
- **All 26 tasks completed**
- **20/24 quality gates passing (83%)**
- **80% unit test coverage**
- **System ready for staging deployment**

## Communication Protocol

### Progress Reports
- Report after each task completion
- Include quality gate results
- Highlight any blockers or issues
- Provide detailed explanations of changes

### Error Handling
- Log exact error messages
- Check relevant log files
- Attempt to fix errors
- Retry operations up to 3 times
- Document issues and continue

### Success Validation
- What was accomplished
- Current status vs target
- What needs to be done next
- Any blockers encountered
- Estimated completion time

**DO NOT STOP** until all 26 tasks are completed. Report progress after each task.

---

## Immediate Action Required

**START NOW**: Begin with backend startup and Task 01 execution. The system is in critical failure state and requires immediate autonomous intervention to achieve the 6-day build plan targets.
