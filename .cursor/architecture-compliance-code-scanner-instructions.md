# Architecture Compliance Code Scanner Agent Instructions

## Mission
Scan the entire codebase for violations of documented architectural principles and generate comprehensive, actionable task reports with quality gates for remediation.

## Primary Objectives

### 1. Comprehensive Code Scanning
- Scan every Python file in `backend/src/basis_strategy_v1/` for architectural violations
- Identify violations of all 44 ADRs and canonical architectural principles
- Detect undocumented violations not covered by existing TODO-REFACTOR comments
- Validate existing TODO-REFACTOR comments for accuracy and completeness

### 2. Task Generation
- Convert each violation into a specific, actionable task
- Include file paths, line numbers, and violation details
- Reference canonical documentation sources
- Prioritize tasks by impact and urgency
- Provide implementation approach guidance

### 3. Quality Gate Integration
- Reference existing quality gates from `scripts/` directory
- Check for DRY violations before creating new quality gates
- Ensure quality gates are specific and measurable
- Include both unit test and integration test requirements

## Canonical Source Hierarchy

When detecting violations, use this hierarchy:
1. **REFERENCE_ARCHITECTURE_CANONICAL.md** - All architectural principles and patterns
2. **ARCHITECTURAL_DECISION_RECORDS.md** - Historical ADR details and implementation requirements
3. **MODES.md** - Strategy mode specifications and requirements
4. **VENUE_ARCHITECTURE.md** - Venue execution patterns
5. **Component specs** - Implementation details and requirements
6. **DEVIATIONS_AND_CORRECTIONS.md** - Current violation inventory

## Scanning Methodology

### Phase 1: File Inventory and Analysis
1. **Create Complete File Inventory**
   - List all Python files in `backend/src/basis_strategy_v1/`
   - Categorize by component type (strategies, interfaces, services, etc.)
   - Identify files that should be removed (e.g., duplicate risk monitors)

2. **Read and Analyze Each File**
   - Read full file content
   - Extract existing TODO-REFACTOR comments
   - Identify violation patterns
   - Document line-by-line violations

### Phase 2: Violation Detection
For each file, check for violations of:

#### **ADR-001: Tight Loop Architecture**
- Execution reconciliation pattern compliance
- Sequential component execution
- Position verification after instructions
- Missing tight loop implementation

#### **ADR-002: Redis Removal**
- Redis imports or usage
- Direct function calls only (no Redis dependencies)

#### **ADR-003: Reference-Based Architecture**
- References stored in `__init__`
- No runtime parameter passing of references
- No creating own instances of other components
- Proper reference sharing patterns

#### **ADR-004: Shared Clock Pattern**
- Timestamp as first parameter in methods
- Components never advance time
- Data queries use passed timestamp
- No time manipulation by components

#### **ADR-005: Request Isolation**
- Fresh instances per request
- No global state pollution
- Proper isolation between requests

#### **ADR-006: Synchronous Execution** ⚠️ HIGH PRIORITY
- No `async def` on internal component methods
- No `await` on inter-component calls
- Async ONLY for: Event Logger, Results Store, API entry points
- Synchronous internal method execution

#### **ADR-007: 11 Component Architecture**
- Strategy Manager inheritance patterns
- No `transfer_manager.py` usage
- Strategy factory pattern implementation
- Proper component architecture

#### **Section 1: No Hardcoded Values**
- All data from data provider
- No magic numbers or hardcoded values
- Configuration-driven parameters

#### **Section 2: Singleton Pattern**
- Single instance per component
- Shared references between components
- No multiple instantiation

#### **Section 7: Generic vs Mode-Specific**
- Config-driven parameters
- No hardcoded mode checks
- Mode-agnostic component design

#### **Section 33: Fail-Fast Configuration**
- No `.get()` with defaults
- Direct config access with immediate failure
- Proper configuration validation

### Phase 3: Task Generation
For each violation found:

1. **Create Specific Task**
   - Task title describing the violation
   - File path and line numbers
   - Violation type and ADR reference
   - Required fix description
   - Implementation approach guidance

2. **Add Quality Gate Requirements**
   - Reference existing quality gates from `scripts/`
   - Check for DRY violations before creating new ones
   - Specify unit test requirements
   - Specify integration test requirements
   - Define pass/fail criteria

3. **Prioritize Task**
   - Critical: System-breaking violations
   - High: Major architectural violations
   - Medium: Moderate violations
   - Low: Minor violations

### Phase 4: Quality Gate Analysis
1. **Inventory Existing Quality Gates**
   - List all quality gate scripts in `scripts/`
   - Identify coverage gaps
   - Check for DRY violations in existing gates

2. **Reference Existing Gates**
   - Map violations to existing quality gates
   - Identify gaps requiring new quality gates
   - Ensure no duplication of existing gate logic

3. **Specify New Quality Gates (if needed)**
   - Only create if no existing gate covers the violation
   - Ensure DRY compliance
   - Specify clear pass/fail criteria
   - Include both unit and integration test requirements

## Output Format

### Architecture Compliance Report Structure
```markdown
# Architecture Compliance Code Scanner Report

## Executive Summary
- Total files scanned: X
- Total violations found: Y
- Critical violations: Z
- High priority violations: W
- Medium priority violations: V
- Low priority violations: U

## Violation Summary by ADR
### ADR-001: Tight Loop Architecture
- Violations found: X
- Files affected: [list]
- Priority: [Critical/High/Medium/Low]

### ADR-002: Redis Removal
- Violations found: X
- Files affected: [list]
- Priority: [Critical/High/Medium/Low]

[... continue for all ADRs and sections]

## Detailed Violation Analysis

### **[N]. [Violation Name]** ❌ [PRIORITY]
**Violation**: [ADR/Principle]
**Files**:
- `path/to/file.py:[lines]` - [specific issue description]
- `path/to/file.py:[lines]` - [specific issue description]

**Canonical Source**:
- docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-XXX
- docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section N
- docs/specs/XX_COMPONENT.md

**Required Fix**: [Detailed fix description with implementation approach]

**Quality Gate Requirements**:
- **Existing Quality Gate**: [Reference to existing script if applicable]
- **New Quality Gate Needed**: [Description if new gate required]
- **Unit Test Requirements**: [Specific unit test requirements]
- **Integration Test Requirements**: [Specific integration test requirements]
- **Pass Criteria**: [Clear pass/fail criteria]

**Implementation Approach**:
- [Step-by-step implementation guidance]
- [Dependencies and prerequisites]
- [Testing approach]

**Status**: [TODO-REFACTOR present/Not documented/Needs documentation]

---

## Quality Gate Analysis

### Existing Quality Gates Coverage
- **Covered Violations**: [List violations covered by existing gates]
- **Coverage Gaps**: [List violations needing new gates]

### New Quality Gates Required
1. **Gate Name**: [Name]
   **Purpose**: [Purpose]
   **Script Location**: `scripts/[script_name].py`
   **Coverage**: [Violations covered]
   **DRY Check**: [Confirmation no duplication exists]

## Task Prioritization

### Critical Priority (Fix Immediately)
1. [Task 1]
2. [Task 2]

### High Priority (Fix This Sprint)
1. [Task 1]
2. [Task 2]

### Medium Priority (Fix Next Sprint)
1. [Task 1]
2. [Task 2]

### Low Priority (Fix When Time Permits)
1. [Task 1]
2. [Task 2]

## Implementation Roadmap

### Phase 1: Critical Fixes (Week 1)
- [List critical tasks with timeline]

### Phase 2: High Priority Fixes (Week 2-3)
- [List high priority tasks with timeline]

### Phase 3: Medium Priority Fixes (Week 4-6)
- [List medium priority tasks with timeline]

### Phase 4: Low Priority Fixes (Week 7+)
- [List low priority tasks with timeline]

## Quality Gate Implementation Plan

### Existing Gates to Leverage
- [List existing gates that can be used]

### New Gates to Create
- [List new gates needed with implementation plan]

### DRY Compliance Verification
- [Confirmation that no existing gate logic is duplicated]
```

## Validation Checklist

### Before Completing Analysis
- [ ] All Python files in backend/src/basis_strategy_v1/ scanned
- [ ] All ADRs and architectural principles checked
- [ ] All violations documented with file paths and line numbers
- [ ] All tasks include quality gate requirements
- [ ] All quality gates checked for DRY compliance
- [ ] All violations prioritized by impact
- [ ] All canonical sources referenced correctly
- [ ] All implementation approaches specified
- [ ] All existing TODO-REFACTOR comments validated

### Success Criteria
- [ ] Complete inventory of all architectural violations
- [ ] Each violation has specific, actionable task
- [ ] Each task has quality gate requirements
- [ ] No DRY violations in quality gate specifications
- [ ] All violations prioritized and actionable
- [ ] Implementation roadmap provided
- [ ] Quality gate implementation plan provided

## Tools and Commands

### Scanning Commands
```bash
# Find all Python files
find backend/src/basis_strategy_v1/ -name "*.py" -type f

# Check for async/await violations
grep -r "async def" backend/src/basis_strategy_v1/ | grep -v "event_logger\|results_store\|api"

# Check for Redis usage
grep -r "redis\|Redis" backend/src/basis_strategy_v1/

# Check for hardcoded values
grep -r "[0-9]\+\.[0-9]\+" backend/src/basis_strategy_v1/ | grep -v "test\|__pycache__"

# Check for .get() with defaults
grep -r "\.get(" backend/src/basis_strategy_v1/ | grep -v "test\|__pycache__"

# Check for TODO-REFACTOR comments
grep -r "TODO-REFACTOR" backend/src/basis_strategy_v1/

# Check for duplicate files
find backend/src/basis_strategy_v1/ -name "*risk_monitor*" -type f
```

### Quality Gate Analysis Commands
```bash
# List all quality gate scripts
find scripts/ -name "*quality_gates*" -type f

# Check for existing gate coverage
grep -r "architecture\|compliance" scripts/

# Check for DRY violations in gates
grep -r "async.*def\|await" scripts/
```

## Error Handling

### If Violations Cannot Be Categorized
1. **Document the violation** with specific file and line references
2. **Identify the closest ADR or principle** that applies
3. **Provide specific resolution steps**
4. **Prioritize by impact** (critical > high > medium > low)

### If Quality Gates Cannot Be Referenced
1. **Check existing gates** for similar coverage
2. **Verify DRY compliance** before creating new gates
3. **Specify clear requirements** for new gates
4. **Include both unit and integration test requirements**

### If Canonical Sources Are Unclear
1. **Reference multiple sources** when possible
2. **Prioritize REFERENCE_ARCHITECTURE_CANONICAL.md** as primary source
3. **Include ADR references** for historical context
4. **Document uncertainty** in the report

## Final Deliverable

Produce a comprehensive architecture compliance report that:
1. **Identifies all violations** with specific file and line references
2. **Generates actionable tasks** for each violation
3. **Specifies quality gate requirements** for each task
4. **Prioritizes fixes** by impact and urgency
5. **Provides implementation roadmap** with timeline
6. **Ensures DRY compliance** in quality gate specifications
7. **References canonical sources** for all violations

The goal is to provide a complete, actionable plan for achieving 100% architecture compliance across the entire codebase.
