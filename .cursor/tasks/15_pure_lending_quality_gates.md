# CRITICAL TASK: Fix Pure Lending Yield Calculation

## CONTEXT
Pure lending strategy shows 1166% APY (7% yield in 10 days) instead of required 3-8% APY. This is Task 4 from REMAINING_TASKS.md.

## REQUIREMENTS FROM DOCS
1) Read docs/REMAINING_TASKS.md Task 4 section completely
2) Read docs/specs/04_PNL_CALCULATOR.md for P&L calculation specifications
3) Read docs/QUALITY_GATES.md for APY validation requirements
4) Fix P&L calculation to use proper balance changes from aUSDT liquidity index
5) Balance changes = aUSDT from previous period vs current period, each converted to USDT by multiplying by liquidity index
6) Only account for tokens actually in wallet, not locked in AAVE/Lido/EtherFi smart contracts
7) APY must be within 3-8% range (NOT 2-50%)

## KEY FILES TO REFERENCE
- docs/REMAINING_TASKS.md (Task 4)
- docs/specs/04_PNL_CALCULATOR.md
- docs/QUALITY_GATES.md
- backend/src/basis_strategy_v1/core/math/pnl_calculator.py
- scripts/test_pure_lending_quality_gates.py

## EXECUTION STEPS
1) Health check: curl -s http://localhost:8001/health/
2) Run: python scripts/test_pure_lending_quality_gates.py
3) Analyze the 1166% APY error in logs
4) Fix backend/src/basis_strategy_v1/core/math/pnl_calculator.py
5) Test fix: python scripts/test_pure_lending_quality_gates.py
6) Verify APY is now 3-8%
7) Report final APY percentage achieved

## SUCCESS CRITERIA
- APY between 3-8% (not 1166%)
- Quality gates pass
- Detailed explanation of what was fixed

## MANDATORY QUALITY GATE VALIDATION
**BEFORE MOVING TO NEXT TASK**, you MUST:

1. **Run Pure Lending Quality Gates**:
   ```bash
   python scripts/test_pure_lending_quality_gates.py
   ```

2. **Verify APY is within 3-8% range**:
   - Check the APY output in the test results
   - Must be between 3-8% (NOT 1166%)
   - If not within range, fix and re-test

3. **Verify Quality Gate Pass Rate**:
   - Pure Lending: Must be 9/9 passing (100%)
   - Overall: Should improve from current 8/24 to 9/24

4. **Document Results**:
   - Final APY percentage achieved
   - Quality gate pass/fail status
   - What was fixed to achieve the result

**DO NOT PROCEED TO NEXT TASK** until quality gates validate the fix is working correctly.

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

DO NOT STOP until success criteria are met. Report progress after each step.
