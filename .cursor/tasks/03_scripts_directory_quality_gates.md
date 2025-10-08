# TASK: Fix Scripts Directory Quality Gates

## CONTEXT
5/14 scripts passing (35.7%), need 10/14 passing (70%+). This is Task 7 from REMAINING_TASKS.md.

## REQUIREMENTS FROM DOCS
1) Read docs/REMAINING_TASKS.md Task 7 section completely
2) Read docs/QUALITY_GATES.md for quality gate standards
3) Read docs/QUALITY_GATES_SUMMARY.md for current status
4) All backtest mode quality gates should pass
5) Live mode can be marked as expected failures
6) Target 10/14 scripts passing (70%+)

## KEY FILES TO REFERENCE
- docs/REMAINING_TASKS.md (Task 7)
- docs/QUALITY_GATES.md
- docs/QUALITY_GATES_SUMMARY.md
- scripts/ directory (all 14 scripts)
- backend/logs/ (for error analysis)

## EXECUTION STEPS
1) Health check: curl -s http://localhost:8001/health/
2) Run: python scripts/run_quality_gates.py
3) Identify which 8 scripts are failing
4) Fix each failing script one by one:
   - python scripts/test_btc_basis_quality_gates.py
   - python scripts/monitor_quality_gates.py
   - python scripts/performance_quality_gates.py
   - python scripts/test_tight_loop_quality_gates.py
   - python scripts/test_config_and_data_validation.py
   - python scripts/test_e2e_backtest_flow.py
   - python scripts/analyze_test_coverage.py
   - python scripts/orchestrate_quality_gates.py
   - python scripts/run_phases_1_to_3.py
5) After each fix, re-run: python scripts/run_quality_gates.py
6) Continue until 10/14 scripts pass

## SUCCESS CRITERIA
- 10/14 scripts passing (70%+)
- All backtest mode gates pass
- Live mode gates marked as expected failures
- Detailed report of what was fixed

## MANDATORY QUALITY GATE VALIDATION
**BEFORE MOVING TO NEXT TASK**, you MUST:

1. **Run Full Quality Gates Suite**:
   ```bash
   python scripts/run_quality_gates.py
   ```

2. **Verify Scripts Directory Pass Rate**:
   - Must achieve 10/14 scripts passing (70%+)
   - Current: 5/14 passing (35.7%)
   - Target: 10/14 passing (70%+)

3. **Verify Overall Quality Gate Improvement**:
   - Overall: Should improve from current 8/24 to 15/24+ (60%+)
   - Scripts Directory: Must be 10/14 passing

4. **Document Results**:
   - List of scripts that now pass
   - List of scripts that still fail (with reasons)
   - Overall quality gate pass rate improvement
   - What was fixed to achieve the results

**DO NOT PROCEED TO NEXT TASK** until quality gates validate the improvements are working correctly.

## TIMEOUT HANDLING
- 5-minute timeout per script
- If hangs, kill and retry
- Restart backend if needed

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

DO NOT STOP until 10/14 scripts pass. Report progress after each script fix.
