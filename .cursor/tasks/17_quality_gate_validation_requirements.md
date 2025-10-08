# QUALITY GATE VALIDATION REQUIREMENTS

## OVERVIEW
Every task MUST include mandatory quality gate validation before moving to the next task. This ensures that fixes are working correctly and prevents regression.

## MANDATORY VALIDATION REQUIREMENTS

### 1. Task-Specific Quality Gates
Each task must run the relevant quality gates that cover the specific functionality being fixed:

#### **Task 1: Pure Lending Yield Fix**
- **Quality Gate**: `python scripts/test_pure_lending_quality_gates.py`
- **Validation**: APY must be within 3-8% range (NOT 1166%)
- **Pass Rate**: Pure Lending must be 9/9 passing (100%)

#### **Task 2: Scripts Directory Quality Gates**
- **Quality Gate**: `python scripts/run_quality_gates.py`
- **Validation**: Scripts Directory must be 10/14 passing (70%+)
- **Pass Rate**: Overall should improve from 8/24 to 15/24+ (60%+)

#### **Task 3: BTC Basis Strategy Fix**
- **Quality Gate**: `python scripts/test_btc_basis_quality_gates.py`
- **Validation**: BTC Basis must be 10/10 passing (100%)
- **Pass Rate**: Overall should improve from 8/24 to 16/24+ (65%+)

#### **Task 4: Comprehensive Quality Gates**
- **Quality Gate**: `python scripts/run_quality_gates.py`
- **Validation**: Overall must be 15/24 passing (60%+)
- **Pass Rate**: All critical quality gates must pass

#### **Task 15: Mode-Specific P&L Calculator Fix**
- **Quality Gates**: 
  - `python scripts/test_pure_lending_quality_gates.py`
  - `python scripts/test_btc_basis_quality_gates.py`
- **Validation**: Generic P&L attribution system works for both strategies
- **Pass Rate**: No mode-specific if statements, all attributions calculated uniformly

### 2. Architecture Compliance Validation
For architecture-related tasks, additional validation is required:

#### **Singleton Pattern Validation**
- [ ] All components use single instances
- [ ] No duplicate component initialization
- [ ] Shared config and data provider instances
- [ ] Synchronized data flows

#### **Mode-Agnostic Validation**
- [ ] P&L monitor works for both backtest and live modes
- [ ] No mode-specific if statements
- [ ] Generic attribution system works across all modes
- [ ] Unused attributions return 0 P&L

#### **Configuration Validation**
- [ ] No hardcoded values
- [ ] All configuration loaded from YAML files
- [ ] Pydantic validation passes
- [ ] Configurable conversion rates work correctly

### 3. Quality Gate Execution Process

#### **Step 1: Run Relevant Quality Gates**
```bash
# For specific strategy fixes
python scripts/test_pure_lending_quality_gates.py
python scripts/test_btc_basis_quality_gates.py

# For overall system validation
python scripts/run_quality_gates.py
```

#### **Step 2: Verify Pass Rates**
- Check the specific pass rate requirements for the task
- Ensure overall system improvement
- Document any remaining failures

#### **Step 3: Validate Functionality**
- Test the specific functionality that was fixed
- Ensure no regression in other areas
- Verify architecture compliance

#### **Step 4: Document Results**
- Final pass rate achieved
- What was fixed to achieve the results
- Any remaining issues or limitations
- Overall system health assessment

### 4. Quality Gate Requirements by Task Type

#### **Bug Fix Tasks**
- Run the specific quality gates that cover the bug
- Verify the bug is fixed
- Ensure no new bugs introduced
- Check overall system health

#### **Architecture Tasks**
- Run multiple quality gates to ensure no regression
- Validate architecture compliance
- Check for hardcoded values or mode-specific logic
- Ensure singleton pattern and clean component design

#### **Feature Tasks**
- Run comprehensive quality gates
- Validate new functionality works correctly
- Ensure backward compatibility
- Check overall system improvement

### 5. Failure Handling

#### **If Quality Gates Fail**
1. **Analyze the failure**: Check logs and error messages
2. **Identify root cause**: Determine why the fix didn't work
3. **Implement additional fixes**: Address the root cause
4. **Re-run quality gates**: Test the additional fixes
5. **Repeat until passing**: Don't proceed until quality gates pass

#### **If Quality Gates Pass but Functionality is Wrong**
1. **Verify the fix**: Check that the intended functionality works
2. **Test edge cases**: Ensure the fix is robust
3. **Check for side effects**: Verify no unintended consequences
4. **Document limitations**: Note any known issues or limitations

### 6. Quality Gate Documentation Requirements

#### **Required Documentation**
- **Pass Rate Achieved**: Specific numbers (e.g., 9/9, 10/14, 15/24)
- **What Was Fixed**: Detailed explanation of the changes made
- **Validation Results**: Results of quality gate validation
- **Remaining Issues**: Any issues that still need to be addressed
- **System Health**: Overall assessment of system health

#### **Example Documentation**
```
## QUALITY GATE VALIDATION RESULTS

### Pure Lending Yield Fix
- **Pass Rate**: 9/9 passing (100%)
- **APY Achieved**: 5.2% (within 3-8% range)
- **What Was Fixed**: P&L calculation now uses proper balance changes from aUSDT liquidity index
- **Validation**: APY quality gate passes, no regression in other areas
- **System Health**: Overall improved from 8/24 to 9/24 passing

### Remaining Issues
- None identified for this task
```

## ENFORCEMENT

### **Mandatory Requirements**
- **NO TASK COMPLETION** without quality gate validation
- **NO PROGRESSION** to next task without passing quality gates
- **NO EXCEPTIONS** to quality gate validation requirements

### **Quality Gate Commands**
```bash
# Individual strategy quality gates
python scripts/test_pure_lending_quality_gates.py
python scripts/test_btc_basis_quality_gates.py
python scripts/test_tight_loop_quality_gates.py
python scripts/test_position_monitor_persistence_quality_gates.py

# Overall quality gates
python scripts/run_quality_gates.py
python scripts/orchestrate_quality_gates.py
```

### **Validation Checklist**
- [ ] Relevant quality gates run successfully
- [ ] Pass rate requirements met
- [ ] Functionality validated
- [ ] No regression detected
- [ ] Architecture compliance verified
- [ ] Results documented
- [ ] Ready to proceed to next task

## SUCCESS CRITERIA
- [ ] All tasks include mandatory quality gate validation
- [ ] Quality gates validate fixes are working correctly
- [ ] No task progression without validation
- [ ] Comprehensive documentation of validation results
- [ ] System health continuously monitored and improved

