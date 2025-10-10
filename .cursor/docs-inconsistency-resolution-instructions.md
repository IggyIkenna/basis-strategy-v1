# Docs Inconsistency Resolution Agent Instructions

## Mission
Apply approved fixes to resolve documented conflicts based on inconsistency detection report.

## Primary Objectives

### 1. Report Processing
- Read inconsistency report and identify approved fixes
- Apply user-approved fixes systematically
- Update non-canonical docs to match canonical sources
- Preserve document structure and formatting

### 2. Conflict Resolution
- Resolve architectural principle conflicts
- Fix configuration requirement conflicts
- Address API documentation conflicts
- Resolve component specification conflicts
- Fix quality gate conflicts
- Address task-documentation conflicts

### 3. Validation and Reporting
- Validate no new conflicts are introduced
- Generate completion report
- Ensure all fixes are properly applied
- Verify document integrity

## Resolution Process

### Step 1: Report Analysis
1. **Read Inconsistency Report**
   - Parse `DOCS_LOGICAL_INCONSISTENCY_REPORT_[timestamp].md`
   - Identify approved fixes (marked by user)
   - Categorize fixes by type and priority
   - Plan resolution sequence

2. **Validate Prerequisites**
   - Ensure canonical sources are available
   - Verify target documents exist
   - Check that fixes are feasible
   - Confirm user approval for all fixes

### Step 2: Systematic Resolution
1. **Apply Fixes by Priority**
   - Critical conflicts first
   - High priority conflicts second
   - Medium priority conflicts third
   - Low priority conflicts last

2. **Resolution Strategies**
   - Update conflicting documents to match canonical source
   - Remove outdated information
   - Add missing documentation
   - Fix broken references
   - Standardize terminology
   - Consolidate duplicate information

### Step 3: Validation
1. **Conflict Resolution Validation**
   - Verify all approved fixes applied
   - Check that conflicts are resolved
   - Ensure no new conflicts introduced
   - Validate document structure preserved

2. **Quality Assurance**
   - Run consistency checks
   - Validate cross-references
   - Check document formatting
   - Ensure readability maintained

## Canonical Source Hierarchy

When applying fixes, follow this hierarchy:

1. **REFERENCE_ARCHITECTURE_CANONICAL.md** (highest authority)
2. **MODES.md** (strategy mode definitions)
3. **VENUE_ARCHITECTURE.md** (venue-specific patterns)
4. **Component specs** (`docs/specs/`)
5. **Guide docs** (`WORKFLOW_GUIDE.md`, etc.)
6. **Task files** (`.cursor/tasks/`)

## Resolution Strategies

### Architectural Principle Conflicts
- Update non-canonical docs to match `REFERENCE_ARCHITECTURE_CANONICAL.md`
- Ensure consistent architectural statements
- Remove contradictory design patterns
- Standardize component descriptions

### Configuration Requirement Conflicts
- Update config docs to match actual config files
- Ensure consistent environment variable descriptions
- Standardize YAML structure documentation
- Align default value specifications

### API Documentation Conflicts
- Update API docs to match actual implementation
- Ensure consistent request/response formats
- Standardize error code documentation
- Align authentication requirements

### Component Specification Conflicts
- Update component specs to match canonical descriptions
- Ensure consistent interface specifications
- Standardize data structure definitions
- Align integration requirements

### Quality Gate Conflicts
- Update quality gate docs to match actual scripts
- Ensure consistent test requirements
- Standardize coverage requirements
- Align validation criteria

### Task-Documentation Conflicts
- Update tasks to match documentation
- Update documentation to match tasks
- Add missing task coverage
- Remove outdated task descriptions

### Terminology Inconsistencies
- Standardize terminology across all documents
- Use consistent naming conventions
- Standardize abbreviations
- Use consistent technical terminology

### Structural Inconsistencies
- Standardize document structure
- Use consistent section organization
- Apply consistent formatting
- Use consistent templates

## Expected Output

### Resolution Completion Report
```markdown
# Documentation Inconsistency Resolution Completion Report

## Summary
- **Total Conflicts Identified**: X
- **Approved Fixes**: Y
- **Fixes Applied**: Z
- **Conflicts Resolved**: A
- **New Conflicts Introduced**: 0

## Fixes Applied

### Critical Conflicts
1. **Concept**: Component Architecture
   **Files**: docs/ARCHITECTURAL_DECISION_RECORDS.md
   **Issue**: Contradictory singleton pattern requirements
   **Resolution**: Updated to match REFERENCE_ARCHITECTURE_CANONICAL.md
   **Status**: ✅ Resolved

### High Priority Conflicts
1. **Concept**: API Authentication
   **Files**: docs/USER_GUIDE.md
   **Issue**: Conflicting authentication requirements
   **Resolution**: Updated to match API_DOCUMENTATION.md
   **Status**: ✅ Resolved

### Terminology Standardization
1. **Concept**: Risk Management
   **Files**: Multiple files
   **Issue**: Inconsistent terminology
   **Resolution**: Standardized on "Risk Monitor"
   **Status**: ✅ Resolved

## Validation Results
- **Cross-Reference Validation**: ✅ All links working
- **Document Structure**: ✅ Preserved
- **Formatting Consistency**: ✅ Maintained
- **New Conflicts**: ✅ None introduced
- **Readability**: ✅ Maintained

## Next Steps
1. Review resolved conflicts
2. Validate system functionality
3. Run quality gates
4. Proceed to next phase
```

## Success Criteria
- All approved fixes applied successfully
- No new conflicts introduced during resolution
- Document structure and formatting preserved
- All cross-references working correctly
- Completion report generated
- System ready for next phase

## Web Agent Integration
This agent is designed to work alongside the main web agent:
- **Priority**: Medium (runs after logical inconsistency detection)
- **Context Sharing**: Yes (shares documentation context)
- **Compatibility**: Full web agent compatibility
- **Triggers**: After logical inconsistency detection agent completes
- **Dependencies**: Logical inconsistency detection complete
- **Requires User Approval**: Yes (user must approve fixes before application)
