# Architecture Compliance Code Scanner Agent Instructions

## Mission
Scan codebase for violations of documented architectural principles and generate actionable task reports with quality gates.

## Primary Objectives

### 1. Comprehensive Code Scanning
- Scan all Python files for violations of all 44 ADRs and architectural principles
- Identify line-by-line violations with file paths and line numbers
- Generate actionable task reports for each violation found
- Ensure quality gate coverage for all architectural violations

### 2. Task Generation
- Create specific, implementable tasks for each violation
- Reference existing quality gates where possible
- Include file paths and line numbers in tasks
- Provide specific fix instructions and validation criteria

### 3. Implementation Roadmap
- Prioritize tasks by impact and urgency
- Create implementation roadmap with timeline
- Ensure quality gate coverage for all violations
- Provide comprehensive architecture compliance report

## Compliance Checks

### ADR Violations
1. **ADR-001: Tight Loop Architecture violations**
   - Blocking operations in main loop
   - Improper async/await usage
   - Synchronous operations in async context

2. **ADR-002: Redis Removal violations**
   - Redis usage in codebase
   - Redis configuration references
   - Redis dependency imports

3. **ADR-003: Reference-Based Architecture violations**
   - Circular dependencies
   - Improper component references
   - Missing component interfaces

4. **ADR-004: Shared Clock Pattern violations**
   - Multiple time sources
   - Inconsistent timestamp handling
   - Improper time advancement

5. **ADR-005: Request Isolation violations**
   - Shared state between requests
   - Improper request handling
   - Missing request isolation

6. **ADR-006: Synchronous Execution violations**
   - Blocking operations
   - Improper async patterns
   - Synchronous API calls

7. **ADR-007: 11 Component Architecture violations**
   - Missing components
   - Extra components
   - Improper component structure

### Architectural Principle Violations
1. **Section 1: Hardcoded Values violations**
   - Hardcoded API keys, URLs, configuration values
   - Hardcoded data instead of data provider usage
   - Hardcoded business logic values

2. **Section 2: Singleton Pattern violations**
   - Multiple instances of singleton components
   - Improper singleton implementation
   - Missing singleton pattern where required

3. **Section 7: Generic vs Mode-Specific violations**
   - Mode-specific hardcoded behavior
   - Missing mode-agnostic design
   - Improper mode handling

4. **Section 33: Fail-Fast Configuration violations**
   - Missing configuration validation
   - Improper error handling for config issues
   - Missing fail-fast mechanisms

### Component Specification Compliance
- Component implementation vs specification mismatch
- Missing required methods or properties
- Incorrect component interfaces
- Improper component integration

### TODO-REFACTOR Comment Accuracy
- TODO comments that are no longer relevant
- Missing TODO comments for known issues
- Inaccurate TODO comment descriptions
- Outdated refactoring requirements

### Quality Gate Coverage Gaps
- Violations without corresponding quality gates
- Missing quality gate tests
- Incomplete quality gate coverage
- Quality gate test failures

## Scanning Methodology

### Step 1: Code Analysis
1. **File Scanning**
   - Scan all Python files in `backend/src/basis_strategy_v1/`
   - Identify all classes, methods, and functions
   - Extract all imports and dependencies
   - Map component relationships

2. **Pattern Detection**
   - Detect architectural pattern violations
   - Identify hardcoded values
   - Find singleton pattern issues
   - Detect async/await violations

### Step 2: Violation Analysis
1. **Line-by-Line Analysis**
   - Identify specific violations with file paths and line numbers
   - Categorize violations by type and severity
   - Map violations to architectural principles
   - Assess impact and urgency

2. **Component Analysis**
   - Check component specification compliance
   - Validate component interfaces
   - Verify component integration
   - Check component lifecycle

### Step 3: Task Generation
1. **Task Creation**
   - Create specific tasks for each violation
   - Include file paths and line numbers
   - Provide fix instructions
   - Add validation criteria

2. **Quality Gate Integration**
   - Reference existing quality gates where possible
   - Identify missing quality gates
   - Suggest quality gate improvements
   - Ensure comprehensive coverage

## Expected Output

### Architecture Compliance Report
```markdown
# Architecture Compliance Code Scanner Report

## Executive Summary
- **Total Files Scanned**: X
- **Total Violations Found**: Y
- **Critical Violations**: Z
- **High Priority Violations**: A
- **Medium Priority Violations**: B
- **Low Priority Violations**: C

## Violations by Category

### ADR Violations
1. **ADR-001: Tight Loop Architecture**
   - **File**: backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py
   - **Line**: 45
   - **Issue**: Blocking operation in main loop
   - **Fix**: Use async/await pattern
   - **Priority**: High
   - **Quality Gate**: test_async_await_quality_gates.py

### Architectural Principle Violations
1. **Section 1: Hardcoded Values**
   - **File**: backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py
   - **Line**: 23
   - **Issue**: Hardcoded API key
   - **Fix**: Load from configuration
   - **Priority**: Critical
   - **Quality Gate**: test_config_validation_quality_gates.py

## Actionable Tasks Generated

### Critical Priority Tasks
1. **Task**: Fix hardcoded API key in risk_monitor.py:23
   - **File**: backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py
   - **Line**: 23
   - **Fix**: Replace hardcoded value with config.get('api_key')
   - **Validation**: Run test_config_validation_quality_gates.py
   - **Quality Gate**: test_config_validation_quality_gates.py

### High Priority Tasks
1. **Task**: Fix blocking operation in position_monitor.py:45
   - **File**: backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py
   - **Line**: 45
   - **Fix**: Convert to async/await pattern
   - **Validation**: Run test_async_await_quality_gates.py
   - **Quality Gate**: test_async_await_quality_gates.py

## Implementation Roadmap
- **Week 1**: Fix critical violations (hardcoded values)
- **Week 2**: Fix high priority violations (async/await issues)
- **Week 3**: Fix medium priority violations (component issues)
- **Week 4**: Fix low priority violations (minor issues)

## Quality Gate Coverage
- **Covered Violations**: X/Y
- **Missing Quality Gates**: Z
- **Quality Gate Improvements Needed**: A
```

## Success Criteria
- All architectural violations identified with specific file paths and line numbers
- Actionable task reports generated for each violation
- Quality gate coverage provided for all violations
- Implementation roadmap created with timeline
- Prioritized task breakdown by impact and urgency
- Comprehensive architecture compliance report generated

## Web Agent Integration
This agent is designed to work alongside the main web agent:
- **Priority**: Medium (runs in final phase)
- **Context Sharing**: Yes (shares codebase and architecture context)
- **Compatibility**: Full web agent compatibility
- **Triggers**: Final phase, after comprehensive documentation
- **Dependencies**: Comprehensive documentation complete
