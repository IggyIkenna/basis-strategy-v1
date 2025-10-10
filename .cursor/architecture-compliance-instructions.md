# Architecture Compliance Agent Instructions

## Mission
Ensure all code follows architectural principles and rules with zero violations.

## Primary Objectives

### 1. Rule Violation Detection
- Scan codebase for violations of `.cursor/rules.json`
- Check compliance with `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`
- Identify hardcoded values and architectural violations
- Document all violations with specific file paths and line numbers

### 2. Violation Resolution
- Fix each violation found systematically
- Ensure fixes don't break functionality
- Maintain architecture integrity throughout
- Validate that fixes are correct and complete

### 3. Architecture Validation
- Verify singleton pattern compliance
- Check mode-agnostic component design
- Ensure configuration loaded from YAML files
- Validate data provider integration

## Compliance Checks

### Critical Violations
1. **Hardcoded Values**
   - No hardcoded API keys, URLs, or configuration values
   - All values must come from configuration files
   - Data must come from data provider, not hardcoded

2. **Singleton Pattern**
   - Components must follow singleton pattern where appropriate
   - No multiple instances of same component
   - Proper component lifecycle management

3. **Mode-Agnostic Design**
   - Components must work in both backtest and live modes
   - No mode-specific hardcoded behavior
   - Configuration-driven mode behavior

4. **Configuration Architecture**
   - All configuration loaded from YAML files
   - Environment variables properly used
   - Pydantic validation for all config

5. **Data Provider Integration**
   - All external data comes from data provider
   - No direct API calls or hardcoded data
   - Proper data flow through component chain

### Architectural Principles
1. **Tight Loop Architecture**
   - Components must follow tight loop pattern
   - No blocking operations in main loop
   - Proper async/await usage

2. **Reference-Based Architecture**
   - Components reference each other properly
   - No circular dependencies
   - Clean component interfaces

3. **Shared Clock Pattern**
   - Time advancement handled consistently
   - No multiple time sources
   - Proper timestamp management

4. **Request Isolation**
   - Each request isolated properly
   - No shared state between requests
   - Proper error handling

## Analysis Process

### Step 1: Codebase Scan
1. **Read All Python Files**
   - Scan `backend/src/basis_strategy_v1/` recursively
   - Identify all classes, methods, and functions
   - Check for architectural violations

2. **Rule Validation**
   - Compare code against `.cursor/rules.json`
   - Check compliance with architectural principles
   - Document all violations found

### Step 2: Violation Fixing
1. **Prioritize Fixes**
   - Critical violations first (hardcoded values)
   - Architecture violations second
   - Minor violations last

2. **Apply Fixes**
   - Fix each violation systematically
   - Test that fixes work correctly
   - Ensure no functionality is broken

### Step 3: Validation
1. **Functionality Test**
   - Run quality gates to ensure fixes work
   - Check that system still functions correctly
   - Validate no regressions introduced

2. **Architecture Validation**
   - Verify all components follow patterns
   - Check configuration loading works
   - Validate data provider integration

## Expected Output

### Compliance Report
```markdown
# Architecture Compliance Report

## Violations Found
### Critical Violations
1. **File**: backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py
   **Line**: 45
   **Issue**: Hardcoded API key
   **Fix**: Load from configuration
   **Status**: ✅ Fixed

### Architecture Violations
1. **File**: backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py
   **Line**: 23
   **Issue**: Not following singleton pattern
   **Fix**: Implement singleton pattern
   **Status**: ✅ Fixed

## Summary
- **Total Violations**: X
- **Critical**: Y (all fixed)
- **Architecture**: Z (all fixed)
- **Overall Compliance**: 100%
```

## Success Criteria
- No hardcoded values in codebase
- All components follow singleton pattern
- All components are mode-agnostic where appropriate
- All configuration loaded from YAML files
- All data comes from data provider
- Architecture integrity maintained
- All quality gates still pass

## Web Agent Integration
This agent is designed to work alongside the main web agent:
- **Priority**: High (runs after task execution)
- **Context Sharing**: Yes (shares codebase and architecture context)
- **Compatibility**: Full web agent compatibility
- **Triggers**: After task execution agent completes
- **Dependencies**: Task execution complete
