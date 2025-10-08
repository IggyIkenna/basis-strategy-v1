# TASK 1: DOCS-CODEBASE RECONCILIATION (CRITICAL)

## OVERVIEW
This is a comprehensive reconciliation between the documentation, the existing `.cursor/tasks`, and the codebase to ensure consistency and completeness. The goal is to identify deviations, conflicts, and gaps, then make necessary adjustments to align all three sources of truth.

## CONTEXT
- **Documentation**: 42 markdown files in docs/, 13 component specs in docs/specs/
- **Tasks**: 20+ task files in .cursor/tasks/ directory
- **Codebase**: 79 Python files in backend/src/basis_strategy_v1/
- **Current Issue**: Potential conflicts and gaps between docs, tasks, and code

## CANONICAL SOURCE
The `.cursor/tasks` directory is considered the canonical source of truth for this reconciliation process. Any conflicts or deviations should be resolved by aligning docs and code with the tasks defined in `.cursor/tasks`.

## OBJECTIVES
1. **Identify Conflicts**: Find discrepancies between docs, `.cursor/tasks`, and code
2. **Reconcile Deviations**: Adjust docs or code to match the canonical source (`.cursor/tasks`)
3. **Enhance Completeness**: Add missing details in docs or code where necessary
4. **Remove Redundancy**: Eliminate unused or conflicting information
5. **Ensure Consistency**: All three sources must be aligned and consistent

## RECONCILIATION PROCESS

### Phase 1: Documentation Analysis
1. **Review All Docs**: Go through each document in the `docs/` directory
2. **Check Completeness**: Ensure docs cover all aspects mentioned in `.cursor/tasks`
3. **Identify Gaps**: Note any missing details or incomplete sections
4. **Document Conflicts**: List any deviations from `.cursor/tasks`

### Phase 2: Codebase Analysis
1. **Review Code**: Examine the codebase for deviations from `.cursor/tasks`
2. **Check Implementation**: Ensure code implements all features outlined in tasks
3. **Identify Gaps**: Note any missing implementations or incomplete features
4. **Document Conflicts**: List any deviations from `.cursor/tasks`

### Phase 3: Reconciliation Actions
**A) Enhance/Remove Docs**: If docs are incomplete or conflict with `.cursor/tasks`, update or remove them
**B) Enhance/Remove Code**: If code is incomplete or conflicts with `.cursor/tasks`, update or remove it
**C) Remove Redundancy**: Eliminate any redundant or conflicting information

## IMPLEMENTATION STEPS

### Step 1: Create Comprehensive Inventory
1. **List All Docs**: Create inventory of all documents in `docs/` and `docs/specs/`
2. **List All Tasks**: Create inventory of all tasks in `.cursor/tasks/`
3. **List All Code Files**: Create inventory of all code files in backend/
4. **Cross-Reference**: Map relationships between docs, tasks, and code

### Step 2: Identify Conflicts and Gaps
1. **Compare Docs with Tasks**: Identify discrepancies between docs and tasks
2. **Compare Code with Tasks**: Identify discrepancies between code and tasks
3. **Check Completeness**: Ensure all tasks have corresponding docs and code
4. **Document Issues**: Create detailed list of all conflicts and gaps

### Step 3: Reconcile Deviations
1. **Update Docs**: Modify or remove docs to align with `.cursor/tasks`
2. **Update Code**: Modify or remove code to align with `.cursor/tasks`
3. **Add Missing Elements**: Add missing docs or code where needed
4. **Remove Redundancy**: Eliminate conflicting or redundant information

### Step 4: Validate and Test
1. **Review Changes**: Ensure all changes align with canonical source
2. **Test Functionality**: Verify code changes don't break existing functionality
3. **Update Documentation**: Ensure all documentation is accurate and complete
4. **Quality Gate Check**: Run quality gates to ensure no regressions

## KEY AREAS TO FOCUS ON

### 1. Architecture Compliance
- **Singleton Pattern**: Ensure docs and code match singleton requirements
- **Mode-Agnostic Components**: Verify P&L monitor and other components are mode-agnostic
- **Tight Loop Architecture**: Ensure docs and code match tight loop requirements
- **Configuration Architecture**: Verify YAML-based config structure is consistent

### 2. Strategy Mode Implementation
- **Pure Lending**: Ensure docs and code match pure lending requirements
- **BTC Basis**: Ensure docs and code match BTC basis requirements
- **ETH Leveraged**: Ensure docs and code match ETH leveraged requirements
- **Configuration**: Verify strategy mode configs are complete and consistent

### 3. Quality Gates and Testing
- **Quality Gate Scripts**: Ensure all quality gate scripts are documented and working
- **Test Coverage**: Verify test coverage requirements are met
- **Validation Requirements**: Ensure validation requirements are consistent

### 4. Data Provider and Configuration
- **Data Provider**: Ensure data provider implementation matches docs
- **Configuration Loading**: Verify configuration loading architecture is consistent
- **Environment Variables**: Ensure environment variable usage is documented

## SUCCESS CRITERIA
- [ ] All docs align with `.cursor/tasks` (canonical source)
- [ ] All code aligns with `.cursor/tasks` (canonical source)
- [ ] No redundant or conflicting information remains
- [ ] All gaps and deviations are addressed
- [ ] Documentation is complete and accurate
- [ ] Code implementation is complete and consistent
- [ ] Quality gates continue to pass
- [ ] No functionality is lost during reconciliation

## MANDATORY QUALITY GATE VALIDATION
**BEFORE CONSIDERING TASK COMPLETE**, you MUST:

1. **Run Full Quality Gates Suite**:
   ```bash
   python scripts/run_quality_gates.py
   ```

2. **Verify No Regressions**:
   - All existing quality gates must continue to pass
   - No new failures introduced by reconciliation changes
   - System functionality remains intact

3. **Document Reconciliation Results**:
   - List of docs updated/removed
   - List of code files updated/removed
   - List of conflicts resolved
   - List of gaps filled
   - Overall consistency achieved

4. **Create Reconciliation Report**:
   - Summary of changes made
   - Verification that all three sources are now aligned
   - Confirmation that `.cursor/tasks` remains canonical source

**DO NOT PROCEED TO NEXT TASK** until reconciliation is complete and quality gates validate no regressions.

## TIMEOUT HANDLING
- 15-minute timeout per major reconciliation step
- If hangs, kill and retry up to 3 times
- Restart backend if needed: ./platform.sh stop-local && ./platform.sh backtest

## ERROR RECOVERY
If you encounter any error:
1) Log the exact error message
2) Check the relevant log files
3) Attempt to fix the error
4) Retry the operation
5) If still failing after 3 attempts, document the issue and continue with next step
6) Do not give up or stop the entire task

## PROGRESS VALIDATION
After each phase, validate progress:
1) What was accomplished
2) Current status vs target
3) What needs to be done next
4) Any blockers encountered
5) Estimated completion time
6) Do not proceed without this validation

## CONTINUATION
After completing this task, immediately proceed to the next task without waiting for confirmation. Do not stop or ask for permission to continue.

DO NOT STOP until reconciliation is complete and all three sources are aligned. Report progress after each phase.
