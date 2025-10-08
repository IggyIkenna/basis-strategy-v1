# TASK: Run Comprehensive Quality Gates Suite

## CONTEXT
Overall quality gates: 8/24 tests passing (33.3%). Need to improve to 15/24 tests passing (60%+). This covers multiple tasks from REMAINING_TASKS.md.

## REQUIREMENTS FROM DOCS
1) Read docs/REMAINING_TASKS.md sections for Tasks 1-8 completely
2) Run comprehensive quality gates validation
3) Fix any remaining issues
4) Target 15/24 tests passing (60%+)

## EXECUTION STEPS
1) Health check: curl -s http://localhost:8001/health/
2) Run: python scripts/run_quality_gates.py
3) Analyze results and identify failing tests
4) Run individual strategy tests:
   - python scripts/test_pure_lending_quality_gates.py
   - python scripts/test_btc_basis_quality_gates.py
   - python scripts/test_tight_loop_quality_gates.py
   - python scripts/test_position_monitor_persistence_quality_gates.py
5) Fix any remaining issues
6) Re-run: python scripts/run_quality_gates.py
7) Verify 15/24 tests pass

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
