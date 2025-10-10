# TASK: Fix BTC Basis Strategy Quality Gates

## CONTEXT
BTC basis strategy currently 8/10 quality gates passing (80.0%), need to fix the 2 failing ones. This is Task 3 from REMAINING_TASKS.md.

## REQUIREMENTS FROM DOCS
1) Read docs/REMAINING_TASKS.md Task 3 section completely
2) Read docs/specs/06_CEX_EXECUTION_MANAGER.md for CEX execution specifications
3) Read docs/specs/08_EXECUTION_INTERFACES.md for interface requirements
4) Fix trade execution issues preventing proper BTC basis trades
5) Ensure CEX interface context dependency issues are resolved
6) Target 10/10 quality gates passing (100%)

## KEY FILES TO REFERENCE
- docs/REMAINING_TASKS.md (Task 3)
- docs/specs/06_CEX_EXECUTION_MANAGER.md
- docs/specs/08_EXECUTION_INTERFACES.md
- backend/src/basis_strategy_v1/core/interfaces/cex_execution_interface.py
- backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py
- scripts/test_btc_basis_quality_gates.py

## EXECUTION STEPS
1) Health check: curl -s http://localhost:8001/health/
2) Run: python scripts/test_btc_basis_quality_gates.py
3) Identify which 2 quality gates are failing
4) Check backend logs: tail -f backend/logs/api.log
5) Fix the failing quality gates:
   - Check CEX execution interface: backend/src/basis_strategy_v1/core/interfaces/cex_execution_interface.py
   - Check historical data provider: backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py
   - Verify trade execution flow
6) Test fix: python scripts/test_btc_basis_quality_gates.py
7) Verify all 10 quality gates pass

## SUCCESS CRITERIA
- 10/10 quality gates passing (100%)
- BTC basis trades executing properly
- CEX interface working correctly
- Detailed report of what was fixed

## MANDATORY QUALITY GATE VALIDATION
**BEFORE MOVING TO NEXT TASK**, you MUST:

1. **Run BTC Basis Quality Gates**:
   ```bash
   python scripts/test_btc_basis_quality_gates.py
   ```

2. **Verify BTC Basis Pass Rate**:
   - Must achieve 10/10 BTC basis quality gates passing (100%)
   - Current: 8/10 passing (80%)
   - Target: 10/10 passing (100%)

3. **Verify Overall Quality Gate Improvement**:
   - Overall: Should improve from current 8/24 to 16/24+ (65%+)
   - BTC Basis: Must be 10/10 passing

4. **Document Results**:
   - List of BTC basis quality gates that now pass
   - List of any remaining failures (with reasons)
   - Overall quality gate pass rate improvement
   - What was fixed to achieve the results

**DO NOT PROCEED TO NEXT TASK** until quality gates validate the BTC basis strategy is working correctly.

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

DO NOT STOP until all 10 quality gates pass. Report progress after each fix.
