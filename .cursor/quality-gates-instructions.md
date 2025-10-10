# Quality Gates Agent Instructions

## Mission
Run and fix quality gates to achieve target pass rates.

## Primary Objectives

### 1. Quality Gate Execution
- Run comprehensive quality gates validation using `python scripts/run_quality_gates.py`
- Identify failing quality gates systematically
- Fix each failing quality gate
- Re-run quality gates after each fix
- Continue until target pass rates achieved

### 2. Target Achievement
- **Pure Lending**: 9/9 passing (100%)
- **BTC Basis**: 10/10 passing (100%)
- **Scripts Directory**: 10/14 passing (70%+)
- **Overall**: 15/24 passing (60%+)

### 3. Fix Implementation
- Address configuration issues
- Implement missing functionality
- Fix test failures
- Fill documentation gaps
- Resolve architecture violations
- Fix integration problems

## Quality Gate Categories

### Pure Lending Strategy (Target: 9/9 passing)
1. Configuration validation
2. Data loading validation
3. Strategy execution validation
4. Risk management validation
5. PnL calculation validation
6. Position monitoring validation
7. Exposure monitoring validation
8. Event logging validation
9. Results storage validation

### BTC Basis Strategy (Target: 10/10 passing)
1. Configuration validation
2. Data loading validation
3. Strategy execution validation
4. Risk management validation
5. PnL calculation validation
6. Position monitoring validation
7. Exposure monitoring validation
8. Event logging validation
9. Results storage validation
10. Basis trading validation

### Scripts Directory (Target: 10/14 passing)
1. Environment switching validation
2. Config loading validation
3. Data loading validation
4. API endpoints validation
5. Health logging validation
6. Strategy manager refactor validation
7. Async/await violations validation
8. Mode agnostic architecture validation
9. Fail fast configuration validation
10. Reference based architecture validation
11. Singleton pattern validation
12. Tight loop architecture validation
13. Component data flow validation
14. Integration alignment validation

## Execution Process

### Step 1: Initial Assessment
1. **Run Quality Gates**
   ```bash
   python scripts/run_quality_gates.py
   ```

2. **Analyze Results**
   - Identify failing quality gates
   - Categorize failures by type
   - Prioritize fixes by impact

### Step 2: Systematic Fixing
1. **Fix Each Category**
   - Start with Pure Lending (highest priority)
   - Move to BTC Basis
   - Address Scripts Directory issues
   - Fix overall system issues

2. **After Each Fix**
   - Re-run quality gates
   - Verify fix worked
   - Check for regressions
   - Document progress

### Step 3: Target Achievement
1. **Monitor Progress**
   - Track pass rates for each category
   - Ensure targets are being met
   - Address any regressions

2. **Final Validation**
   - Run complete quality gate suite
   - Verify all targets achieved
   - Document final results

## Fix Categories

### Configuration Issues
- Missing configuration files
- Incorrect configuration values
- Environment variable problems
- YAML structure issues

### Missing Implementations
- Unimplemented functions
- Missing classes or methods
- Incomplete interfaces
- Missing error handling

### Test Failures
- Failing unit tests
- Integration test problems
- Mock setup issues
- Test data problems

### Documentation Gaps
- Missing docstrings
- Incomplete API documentation
- Missing configuration documentation
- Incomplete error documentation

### Architecture Violations
- Hardcoded values
- Singleton pattern violations
- Mode-specific code
- Configuration access violations

### Integration Problems
- Component integration issues
- API integration problems
- Data flow problems
- Event handling issues

## Expected Output

### Quality Gates Report
```markdown
# Quality Gates Progress Report

## Current Status
- **Pure Lending**: 7/9 passing (78%) - Target: 9/9 (100%)
- **BTC Basis**: 8/10 passing (80%) - Target: 10/10 (100%)
- **Scripts Directory**: 8/14 passing (57%) - Target: 10/14 (70%+)
- **Overall**: 15/24 passing (63%) - Target: 15/24 (60%+)

## Fixes Applied
### Pure Lending
1. **Configuration Issue**: Fixed missing config file
   **Status**: ✅ Fixed
   **Result**: 8/9 passing

### BTC Basis
1. **Missing Implementation**: Added missing method
   **Status**: ✅ Fixed
   **Result**: 9/10 passing

## Next Steps
1. Fix remaining Pure Lending issues
2. Address BTC Basis configuration
3. Improve Scripts Directory coverage
```

## Success Criteria
- Pure Lending: 9/9 passing (100%)
- BTC Basis: 10/10 passing (100%)
- Scripts Directory: 10/14 passing (70%+)
- Overall: 15/24 passing (60%+)
- All fixes validated and working
- No regressions introduced

## Web Agent Integration
This agent is designed to work alongside the main web agent:
- **Priority**: High (runs after architecture compliance)
- **Context Sharing**: Yes (shares quality gates and testing context)
- **Compatibility**: Full web agent compatibility
- **Triggers**: After architecture compliance agent completes
- **Dependencies**: Architecture compliance complete
- **Prerequisites**: Backend running, tests available
