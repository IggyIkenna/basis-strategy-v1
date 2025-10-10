# Codebase Documentation Agent Instructions

## Mission
Ensure refactor areas have comprehensive docstrings showing what's due for refactor, what the refactor will look like, links to docs for full spec, and quality gate criteria.

## Primary Objectives

### 1. Refactor Area Identification
- Search codebase for TODO comments and TODO-REFACTOR markers
- Find FIXME and HACK comments indicating refactor needs
- Locate architecture violation patterns from tasks
- Identify code sections mentioned in task refactor requirements
- Find components with implementation status issues

### 2. Docstring Validation and Enhancement
- Check if refactor areas have module/class/function docstrings
- Verify docstrings explain what needs refactoring
- Ensure docstrings describe planned refactor approach
- Validate docstrings link to relevant docs/specs
- Confirm docstrings reference quality gate criteria

### 3. Traceability Establishment
- Ensure every refactor area links to corresponding task
- Validate links to relevant documentation specs
- Confirm links to quality gate tests
- Establish complete traceability chain: code → task → doc → quality gate

## Canonical Source for Conflict Resolution

When detecting or resolving conflicts, use this hierarchy:
1. **REFERENCE_ARCHITECTURE_CANONICAL.md** - All architectural principles and patterns
2. **ARCHITECTURAL_DECISION_RECORDS.md** - Historical ADR details
3. **MODES.md** - Strategy mode specifications
4. **VENUE_ARCHITECTURE.md** - Venue execution patterns
5. **Component specs** - Implementation details
6. **Guide docs** - Workflow and usage patterns

For architectural conflicts, REFERENCE_ARCHITECTURE_CANONICAL.md is the ultimate authority.

## Analysis Process

### Step 1: Refactor Area Discovery
1. **Search Codebase for Refactor Markers**
   - Search for "TODO" comments in all Python files
   - Find "TODO-REFACTOR" markers specifically
   - Identify "FIXME" and "HACK" comments
   - Look for architecture violation patterns from tasks
   - Find code sections mentioned in task requirements

2. **Cross-Reference with Tasks**
   - Map each refactor area to relevant task files
   - Identify tasks that reference specific code areas
   - Find architecture violations mentioned in tasks
   - Locate quality gate failures that need code fixes

3. **Cross-Reference with Documentation**
   - Map each refactor area to relevant spec files
   - Find implementation status sections mentioning refactor needs
   - Identify architectural principles being violated
   - Locate quality gate requirements for each area

### Step 2: Docstring Analysis
1. **Current Docstring Assessment**
   - Check if refactor areas have existing docstrings
   - Evaluate completeness of current documentation
   - Identify missing information in docstrings
   - Assess quality of existing refactor documentation

2. **Template Compliance Check**
   - Verify docstrings follow required template structure
   - Check for required sections (REFACTOR REQUIRED, Planned Refactor, etc.)
   - Validate presence of traceability links
   - Ensure proper formatting and structure

3. **Traceability Validation**
   - Verify links to task files are correct and exist
   - Check links to documentation specs are valid
   - Confirm links to quality gate tests are accurate
   - Validate all four pieces of traceability are present

### Step 3: Documentation Enhancement
1. **Missing Docstring Creation**
   - Create comprehensive docstrings for areas without them
   - Follow template structure for consistency
   - Include all required sections and information
   - Add proper traceability links

2. **Incomplete Docstring Enhancement**
   - Add missing sections to existing docstrings
   - Enhance descriptions of refactor needs
   - Add missing traceability links
   - Improve clarity and completeness

3. **Template Standardization**
   - Ensure all docstrings follow consistent template
   - Standardize formatting and structure
   - Verify all required sections are present
   - Maintain consistent terminology and style

## Docstring Template

### Required Template Structure
```python
"""
Component/Function Name

REFACTOR REQUIRED:
    Current Issue: [What's wrong with current implementation]
    Violation: [Architecture principle violated]
    Task Reference: .cursor/tasks/XX_task_name.md
    
Planned Refactor:
    Approach: [High-level description of refactor]
    Key Changes:
        - [Change 1]
        - [Change 2]
        - [Change 3]
    
Documentation:
    Spec: docs/specs/XX_COMPONENT.md
    Architecture: docs/REFERENCE_ARCHITECTURE_CANONICAL.md (Section X)
    Implementation Status: docs/specs/XX_COMPONENT.md#current-implementation-status
    
Quality Gates:
    Test: scripts/test_XX_quality_gates.py
    Success Criteria: [Specific criteria from quality gates]
    Coverage Required: 80%+ unit test coverage
    
Related:
    Task: .cursor/tasks/XX_task_name.md
    Depends On: [Other components that need refactoring first]
    Blocks: [What this blocks]

Args/Returns:
    [Normal function documentation]
"""
```

### Template Section Requirements

**REFACTOR REQUIRED Section:**
- **Current Issue**: Clear description of what's wrong
- **Violation**: Specific architecture principle being violated
- **Task Reference**: Link to relevant task file

**Planned Refactor Section:**
- **Approach**: High-level description of refactor strategy
- **Key Changes**: Bulleted list of specific changes needed

**Documentation Section:**
- **Spec**: Link to component specification
- **Architecture**: Link to architectural principles
- **Implementation Status**: Link to current status section

**Quality Gates Section:**
- **Test**: Link to quality gate test file
- **Success Criteria**: Specific criteria from quality gates
- **Coverage Required**: Test coverage requirements

**Related Section:**
- **Task**: Link to task file
- **Depends On**: Other components that need refactoring first
- **Blocks**: What this refactor blocks or unblocks

## Report Generation

### Report Structure
```markdown
# Codebase Documentation Report

**Generated**: [Current timestamp]
**Scope**: All refactor areas in backend/src/
**Analysis Type**: Docstring validation and traceability establishment

---

## Executive Summary

- **Total Refactor Areas Identified**: [X]
- **Areas with Good Docstrings**: [Y]
- **Areas Missing Docstrings**: [Z]
- **Areas with Incomplete Docstrings**: [A]
- **Documentation Completeness**: [W]%

### Key Findings
- [Summary of most critical documentation gaps]
- [Refactor areas with poor traceability]
- [Areas missing quality gate references]
- [Components with architecture violations]

---

## Critical Refactor Areas Missing Docstrings

### CRITICAL Priority
[Priority areas from tasks without proper documentation]
- **File**: [File path]
- **Component**: [Component name]
- **Current State**: [Has docstring? Partial/None?]
- **Task Reference**: [Related task]
- **Required Documentation**: [What docstring should include]
- **Priority**: CRITICAL
- **Impact**: [Why this is critical]

### HIGH Priority
[Same format as CRITICAL, but HIGH priority]

### MEDIUM Priority
[Same format as CRITICAL, but MEDIUM priority]

### LOW Priority
[Same format as CRITICAL, but LOW priority]

---

## Incomplete Docstrings

### Missing Required Sections
[Areas with docstrings but missing key information]
- **File**: [File path]
- **Component**: [Component name]
- **Current Docstring**: [What exists]
- **Missing Information**: [What's missing]
- **Required Additions**: [What to add]
- **Priority**: [CRITICAL/HIGH/MEDIUM/LOW]

### Missing Traceability Links
[Areas with docstrings but missing links]
- **File**: [File path]
- **Component**: [Component name]
- **Missing Links**: [What links are missing]
- **Required Links**: [What links should be added]
- **Impact**: [Why this matters]

---

## Well-Documented Refactor Areas

### Examples of Good Documentation
[Areas that serve as good examples]
- **File**: [File path]
- **Component**: [Component name]
- **Docstring Quality**: [Why it's good]
- **Template Compliance**: [How well it follows template]
- **Traceability**: [Quality of links and references]

---

## Recommended Docstring Updates

### Specific Recommendations with Examples
[Detailed recommendations for each area needing updates]
- **File**: [File path]
- **Line**: [Line number]
- **Current**: [Current docstring or lack thereof]
- **Recommended**: [Full recommended docstring following template]
- **Priority**: [CRITICAL/HIGH/MEDIUM/LOW]
- **Rationale**: [Why this change is needed]

---

## Traceability Matrix

### Complete Traceability Chain
[Showing links between code, tasks, docs, and quality gates]
| Code File | Component | Task | Spec Doc | Quality Gate | Status |
|-----------|-----------|------|----------|--------------|--------|
| [file.py] | [component] | [task.md] | [spec.md] | [test.py] | [GOOD/PARTIAL/POOR] |

### Missing Traceability Links
[Areas where traceability is incomplete]
- **Code File**: [File path]
- **Missing Link**: [What link is missing]
- **Required Link**: [What should be linked]
- **Impact**: [Why this matters]

---

## Architecture Violation Documentation

### Violations with Poor Documentation
[Architecture violations that need better docstring documentation]
- **File**: [File path]
- **Violation**: [What architecture principle is violated]
- **Current Documentation**: [What exists]
- **Required Documentation**: [What should be added]
- **Task Reference**: [Related task]
- **Priority**: [CRITICAL/HIGH/MEDIUM/LOW]

---

## Quality Gate Integration

### Areas Missing Quality Gate References
[Refactor areas that don't reference quality gates]
- **File**: [File path]
- **Component**: [Component name]
- **Missing Reference**: [What quality gate reference is missing]
- **Required Reference**: [What should be referenced]
- **Quality Gate**: [Which quality gate applies]

---

## Recommendations

### Immediate Actions Required (CRITICAL)
1. [List critical refactor areas needing docstrings]
2. [Architecture violations needing documentation]
3. [Areas blocking other refactors]

### High Priority Actions
1. [List high priority documentation improvements]
2. [Missing traceability links to add]
3. [Incomplete docstrings to enhance]

### Medium Priority Actions
1. [List medium priority improvements]
2. [Template standardization needs]
3. [Quality gate reference additions]

### Low Priority Actions
1. [List low priority refinements]
2. [Minor documentation improvements]
3. [Style and formatting updates]

---

## Success Criteria Validation

### Primary Success Criteria
- [ ] All refactor areas identified from tasks
- [ ] Each refactor area has comprehensive docstring
- [ ] All docstrings follow template with required sections
- [ ] Traceability links verified (code → task → doc → quality gate)

### Secondary Success Criteria
- [ ] All TODO-REFACTOR markers have proper documentation
- [ ] All architecture violations have docstring explanations
- [ ] All quality gate failures have docstring references
- [ ] Documentation completeness report generated

### Tertiary Success Criteria
- [ ] All docstrings follow consistent template
- [ ] All traceability links are valid and working
- [ ] All refactor areas have proper priority assessment
- [ ] Complete traceability matrix generated

---

## Next Steps

1. **Review Documentation Report**: Examine all identified gaps
2. **Prioritize Docstring Creation**: Start with CRITICAL areas
3. **Enhance Incomplete Docstrings**: Add missing sections and links
4. **Validate Traceability**: Ensure all links work correctly
5. **Standardize Templates**: Ensure consistent formatting
6. **Re-run Analysis**: Verify improvements and completeness

## Validation Requirements

### Before Completing Analysis
- [ ] All refactor areas identified from codebase search
- [ ] All refactor areas mapped to tasks and docs
- [ ] All docstrings analyzed for completeness
- [ ] All traceability links validated
- [ ] All template compliance checked
- [ ] Report generated with complete analysis

### Success Criteria
- [ ] All refactor areas have comprehensive docstrings
- [ ] All docstrings follow required template
- [ ] All traceability links are valid and complete
- [ ] All architecture violations are documented
- [ ] All quality gate references are included
- [ ] Complete traceability matrix generated

## Error Handling

### If Refactor Areas Cannot Be Identified
1. **Document the search limitations** in the analysis
2. **List specific areas** that need manual review
3. **Provide guidance** for further investigation
4. **Reference task files** for additional context

### If Traceability Links Are Broken
1. **Document all broken links** with file locations
2. **Identify correct links** or suggest creation
3. **Provide fix recommendations** for each broken link
4. **Include in recommendations** for immediate action

### If Template Compliance Is Poor
1. **Document template violations** with specific examples
2. **Provide corrected examples** following template
3. **Suggest standardization approach** for consistency
4. **Include in recommendations** for improvement

## Final Deliverable

Produce a comprehensive codebase documentation report that:
1. **Identifies all refactor areas** with specific file and line references
2. **Assesses docstring completeness** for each refactor area
3. **Provides specific recommendations** for docstring improvements
4. **Validates traceability links** between code, tasks, docs, and quality gates
5. **Includes complete traceability matrix** showing all relationships

The goal is to ensure every refactor area has comprehensive documentation with complete traceability to tasks, documentation, and quality gates.
