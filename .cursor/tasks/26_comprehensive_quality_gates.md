# SERVICE LAYER & ENGINE VALIDATION

## OVERVIEW
This task validates the existing service layer implementations against canonical specifications and ensures comprehensive quality gates coverage. The services exist but need validation against specs, request isolation pattern compliance, and comprehensive quality gate implementation.

**Reference**: `docs/specs/13_BACKTEST_SERVICE.md` - Backtest orchestration specification  
**Reference**: `docs/specs/14_LIVE_TRADING_SERVICE.md` - Live trading orchestration specification  
**Reference**: `docs/specs/15_EVENT_DRIVEN_STRATEGY_ENGINE.md` - Event loop management specification  
**Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - ADR-005 (Request Isolation)  
**Reference**: `docs/QUALITY_GATES.md` - Validation requirements  
**Reference**: `docs/IMPLEMENTATION_GAP_REPORT.md` - Component gap analysis

## CONTEXT
Current quality gates: 12/24 tests passing (50%). Need to improve to 20/24 tests passing (80%+) through service layer validation and comprehensive quality gate implementation.

## CRITICAL REQUIREMENTS

### 1. Backtest Service Validation
- **Request isolation**: Validate fresh component instantiation per request
- **Config slicing**: Validate config slicing and override application
- **Data provider creation**: Validate fresh DataProvider creation per request
- **Component initialization**: Validate fresh component creation per request
- **Error codes**: Add missing error codes BT-001 through BT-013

### 2. Live Trading Service Validation
- **Request isolation**: Validate fresh component instantiation per request
- **Live execution**: Validate live execution patterns
- **Real-time monitoring**: Validate real-time monitoring capabilities
- **Error handling**: Validate live trading error handling
- **Error codes**: Add missing error codes LT-001 through LT-013

### 3. Event Engine Validation
- **Event loop management**: Validate event loop management per spec
- **Component orchestration**: Validate component orchestration
- **Timestamp management**: Validate shared clock pattern
- **Error handling**: Validate event engine error handling
- **Error codes**: Add missing error codes EE-001 through EE-013

### 4. Quality Gates Implementation
- **Service layer gates**: Add quality gates for all service components
- **Integration gates**: Add integration quality gates
- **Performance gates**: Add performance quality gates
- **Error handling gates**: Add error handling quality gates
- **Coverage gates**: Add test coverage quality gates

## SUCCESS CRITERIA
- 15/24 tests passing (60%+)
- All critical tasks completed
- Detailed report of improvements made

## MANDATORY QUALITY GATE VALIDATION
**BEFORE MOVING TO NEXT TASK**, you MUST:

1. **Run Full Quality Gates Suite**:
   ```bash
   python scripts/run_quality_gates.py
   ```

2. **Verify Overall Pass Rate**:
   - Must achieve 15/24 quality gates passing (60%+)
   - Current: 8/24 passing (33.3%)
   - Target: 15/24 passing (60%+)

3. **Verify Critical Quality Gates**:
   - Pure Lending: Must be 9/9 passing (100%)
   - BTC Basis: Must be 10/10 passing (100%)
   - Scripts Directory: Must be 10/14 passing (70%+)

4. **Document Results**:
   - Overall quality gate pass rate achieved
   - Breakdown by category (Pure Lending, BTC Basis, Scripts Directory, etc.)
   - List of any remaining failures (with reasons)
   - System health assessment

**DO NOT PROCEED TO NEXT TASK** until quality gates validate the overall system improvements are working correctly.

## TIMEOUT HANDLING
- 10-minute timeout per command
- If hangs, kill and retry up to 3 times
- Restart backend if needed: ./platform.sh stop-local && ./platform.sh backtest

## CONTINUATION
After completing this task, immediately proceed to the next task without waiting for confirmation. Do not stop or ask for permission to continue.

## ERROR RECOVERY
If you encounter any error:
1) Log the exact error message
2) Check the relevant log files
3) Attempt to fix the error
4) Retry the operation
5) If still failing after 3 attempts, document the issue and continue with next step
6) Do not give up or stop the entire task

## PROGRESS VALIDATION
After each step, validate progress:
1) What was accomplished
2) Current status vs target
3) What needs to be done next
4) Any blockers encountered
5) Estimated completion time
6) Do not proceed without this validation

DO NOT STOP until 15/24 tests pass. Report progress after each fix.
