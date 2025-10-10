# Docs Inconsistency Resolution Agent Instructions

## Mission
Read inconsistency report and apply approved fixes to resolve documented conflicts, ensuring all changes align with canonical source hierarchy and maintain documentation quality.

## Primary Objectives

### 1. Report Processing and Validation
- Parse inconsistency report structure and extract approved fixes
- Validate resolution prescriptions against canonical source hierarchy
- Ensure all approved fixes are properly marked and ready for application
- Verify canonical source authority levels are correctly applied

## Canonical Source for Conflict Resolution

When detecting or resolving conflicts, use this hierarchy:
1. **REFERENCE_ARCHITECTURE_CANONICAL.md** - All architectural principles and patterns
2. **ARCHITECTURAL_DECISION_RECORDS.md** - Historical ADR details
3. **MODES.md** - Strategy mode specifications
4. **VENUE_ARCHITECTURE.md** - Venue execution patterns
5. **Component specs** - Implementation details
6. **Guide docs** - Workflow and usage patterns

For architectural conflicts, REFERENCE_ARCHITECTURE_CANONICAL.md is the ultimate authority.

### 2. Fix Application in Priority Order
- Apply fixes in severity order (CRITICAL → HIGH → MEDIUM → LOW)
- Update non-canonical documents to match canonical sources
- Replace contradictory statements with canonical versions
- Preserve document structure, formatting, and cross-references

### 3. Quality Assurance and Validation
- Verify all approved fixes applied correctly
- Ensure no new conflicts introduced by changes
- Validate document formatting and structure preserved
- Generate completion report with summary of all changes

## Resolution Process

### Step 1: Report Analysis and Preparation
1. **Load Inconsistency Report**
   - Read `DOCS_LOGICAL_INCONSISTENCY_REPORT_[timestamp].md`
   - Parse report structure and extract all conflicts
   - Identify user-approved fixes (marked with approval indicators)
   - Validate canonical source hierarchy is correctly applied

2. **Validate Resolution Prescriptions**
   - Check each fix against canonical source hierarchy
   - Verify line references are accurate
   - Confirm canonical source authority levels
   - Ensure resolution logic is sound

3. **Prepare Fix Application Plan**
   - Group fixes by target document
   - Order fixes by severity (CRITICAL first, LOW last)
   - Plan document updates to minimize conflicts
   - Prepare backup strategy for rollback if needed

### Step 2: Fix Application Process
1. **CRITICAL Priority Fixes**
   - Apply all CRITICAL fixes first
   - Update non-canonical docs to match canonical sources
   - Replace contradictory statements with canonical versions
   - Preserve document structure and formatting

2. **HIGH Priority Fixes**
   - Apply HIGH priority fixes after CRITICAL
   - Address major architectural deviations
   - Standardize terminology across documents
   - Maintain cross-references and internal links

3. **MEDIUM Priority Fixes**
   - Apply MEDIUM priority fixes after HIGH
   - Resolve inconsistencies requiring clarification
   - Consolidate duplicate information where appropriate
   - Ensure consistent documentation structure

4. **LOW Priority Fixes**
   - Apply LOW priority fixes last
   - Address minor documentation mismatches
   - Clean up formatting and minor inconsistencies
   - Finalize documentation polish

### Step 3: Quality Assurance and Validation
1. **Verify Fix Application**
   - Check all approved fixes were applied correctly
   - Validate canonical source content was properly integrated
   - Ensure document structure and formatting preserved
   - Confirm cross-references still work after changes

2. **Conflict Validation**
   - Verify no new conflicts introduced by changes
   - Check that resolved conflicts are actually resolved
   - Validate canonical source hierarchy maintained
   - Ensure no regressions in documentation quality

3. **Documentation Quality Check**
   - Verify all documents maintain proper structure
   - Check formatting consistency across all docs
   - Validate internal links and cross-references
   - Ensure readability and clarity maintained

## Fix Application Guidelines

### Canonical Source Integration
1. **Replace Contradictory Content**
   - Remove non-canonical statements
   - Insert canonical content in same location
   - Preserve surrounding context and formatting
   - Maintain document flow and readability

2. **Standardize Terminology**
   - Replace inconsistent terms with canonical versions
   - Update all references to use standard terminology
   - Ensure consistency across all documents
   - Maintain clarity and precision

3. **Consolidate Duplicate Information**
   - Remove duplicate content from non-canonical sources
   - Keep canonical version as authoritative
   - Update cross-references to point to canonical source
   - Ensure no information is lost in consolidation

### Document Structure Preservation
1. **Maintain Formatting**
   - Preserve markdown formatting and structure
   - Keep headers, lists, and code blocks intact
   - Maintain consistent indentation and spacing
   - Preserve table structures and formatting

2. **Preserve Cross-References**
   - Update internal links to point to correct locations
   - Maintain section references and anchors
   - Ensure all cross-references work after changes
   - Update any broken references caused by changes

3. **Maintain Document Flow**
   - Ensure changes don't disrupt document readability
   - Preserve logical flow and organization
   - Maintain consistent tone and style
   - Keep document structure intact

## Error Handling and Recovery

### If Fix Cannot Be Applied
1. **Document the Issue**
   - Record specific reason why fix cannot be applied
   - Note the conflict and attempted resolution
   - Provide alternative resolution suggestions
   - Flag for manual review

2. **Skip and Continue**
   - Skip the problematic fix
   - Continue with remaining fixes
   - Include skipped fixes in completion report
   - Provide guidance for manual resolution

### If Canonical Source Is Unclear
1. **Flag for Manual Review**
   - Document the ambiguity in canonical source
   - Provide multiple potential canonical sources
   - Include rationale for each option
   - Request manual decision from user

2. **Use Best Available Source**
   - Select highest authority level source available
   - Document the decision rationale
   - Apply fix with clear notation of uncertainty
   - Include in completion report for review

### If Formatting Breaks
1. **Attempt Structure Preservation**
   - Try to maintain document structure
   - Preserve as much formatting as possible
   - Document any formatting changes made
   - Include in completion report

2. **Rollback if Necessary**
   - If formatting severely broken, rollback changes
   - Document the issue and attempted fix
   - Provide alternative resolution approach
   - Flag for manual review

### If New Conflicts Introduced
1. **Immediate Rollback**
   - Rollback the changes that introduced conflicts
   - Document the original conflict and attempted resolution
   - Analyze why new conflicts were introduced
   - Provide alternative resolution approach

2. **Report Issue**
   - Include in completion report
   - Provide detailed analysis of the problem
   - Suggest manual review and resolution
   - Document lessons learned for future fixes

## Completion Report Generation

### Report Structure
```markdown
# Inconsistency Resolution Completion Report

**Generated**: [Current timestamp]
**Source Report**: DOCS_LOGICAL_INCONSISTENCY_REPORT_[timestamp].md
**Resolution Agent**: Docs Inconsistency Resolution Agent

---

## Executive Summary

- **Total Fixes Processed**: [X]
- **Successfully Applied**: [Y]
- **Skipped/Errors**: [Z]
- **New Conflicts Introduced**: [A]
- **Overall Success Rate**: [Y/X]%

### Resolution Summary by Priority
- **CRITICAL**: [X] processed, [Y] applied, [Z] errors
- **HIGH**: [X] processed, [Y] applied, [Z] errors
- **MEDIUM**: [X] processed, [Y] applied, [Z] errors
- **LOW**: [X] processed, [Y] applied, [Z] errors

---

## Successfully Applied Fixes

### CRITICAL Priority Fixes
1. **[Conflict Name]** - [Doc A] vs [Doc B]
   - **Applied**: Updated [Doc] line [X] to match [Canonical Doc] line [Y]
   - **Change**: "[Old text]" → "[New text]"
   - **Status**: ✅ Successfully applied

### HIGH Priority Fixes
[Same format as CRITICAL]

### MEDIUM Priority Fixes
[Same format as CRITICAL]

### LOW Priority Fixes
[Same format as CRITICAL]

---

## Skipped/Error Fixes

### Fixes That Could Not Be Applied
1. **[Conflict Name]** - [Doc A] vs [Doc B]
   - **Issue**: [Reason why fix could not be applied]
   - **Attempted Resolution**: [What was tried]
   - **Alternative**: [Suggested manual resolution]
   - **Status**: ⚠️ Requires manual review

### Fixes with Ambiguous Canonical Source
1. **[Conflict Name]** - [Doc A] vs [Doc B]
   - **Ambiguity**: [Description of canonical source uncertainty]
   - **Options**: [List of potential canonical sources]
   - **Recommendation**: [Suggested approach]
   - **Status**: ⚠️ Requires manual decision

---

## New Conflicts Introduced

### Conflicts Created by Resolution Process
1. **[New Conflict Name]** - [Doc A] vs [Doc B]
   - **Cause**: [What resolution caused this conflict]
   - **Impact**: [Description of the new conflict]
   - **Resolution**: [How to fix the new conflict]
   - **Status**: ❌ Requires immediate attention

---

## Document Changes Summary

### Documents Modified
- **[Doc Name]**: [X] changes applied
  - [List of specific changes made]
  - [Summary of modifications]

### Documents Unchanged
- **[Doc Name]**: No changes required
  - [Reason why no changes were needed]

---

## Quality Validation Results

### Fix Application Validation
- [ ] All approved fixes applied correctly
- [ ] Canonical source hierarchy maintained
- [ ] Document structure preserved
- [ ] Cross-references updated appropriately

### Conflict Resolution Validation
- [ ] No new conflicts introduced
- [ ] All resolved conflicts actually resolved
- [ ] Canonical sources properly prioritized
- [ ] Documentation consistency improved

### Documentation Quality Check
- [ ] All documents maintain proper structure
- [ ] Formatting consistency maintained
- [ ] Internal links work correctly
- [ ] Readability and clarity preserved

---

## Recommendations

### Immediate Actions Required
1. [List any critical issues that need immediate attention]
2. [New conflicts that need resolution]
3. [Fixes that require manual review]

### Next Steps
1. [Review skipped/error fixes]
2. [Resolve new conflicts introduced]
3. [Validate all changes manually]
4. [Run quality gates to verify improvements]

### Lessons Learned
1. [Insights from resolution process]
2. [Patterns in conflicts that were difficult to resolve]
3. [Suggestions for improving future resolution process]

---

## Success Criteria Validation

### Primary Success Criteria
- [ ] All approved fixes applied correctly
- [ ] No new conflicts introduced
- [ ] Canonical source hierarchy maintained
- [ ] Documentation quality preserved

### Secondary Success Criteria
- [ ] All documents maintain proper structure
- [ ] Cross-references work correctly
- [ ] Formatting consistency maintained
- [ ] Completion report generated

### Tertiary Success Criteria
- [ ] All changes documented
- [ ] Quality validation completed
- [ ] Recommendations provided
- [ ] Lessons learned captured

---

## Next Steps

1. **Review Completion Report**: Examine all applied fixes and any issues
2. **Address New Conflicts**: Resolve any conflicts introduced during resolution
3. **Manual Review**: Review skipped/error fixes and apply manually
4. **Quality Validation**: Run quality gates to verify improvements
5. **Final Validation**: Ensure all documentation is consistent and accurate
```

## Validation Requirements

### Before Completing Resolution
- [ ] All approved fixes processed and applied where possible
- [ ] All skipped/error fixes documented with reasons
- [ ] All new conflicts identified and documented
- [ ] All document changes summarized
- [ ] Quality validation completed
- [ ] Completion report generated

### Success Criteria
- [ ] All approved fixes applied correctly
- [ ] No new conflicts introduced by resolution process
- [ ] Canonical source hierarchy maintained throughout
- [ ] Documentation quality preserved and improved
- [ ] All changes properly documented
- [ ] Completion report provides clear summary

## Error Handling

### If Resolution Process Fails
1. **Document the failure** with specific details
2. **Provide rollback instructions** if possible
3. **Suggest alternative approaches** for resolution
4. **Include in completion report** for manual review

### If Quality Validation Fails
1. **Identify specific quality issues** found
2. **Provide remediation steps** for each issue
3. **Suggest manual review** for complex issues
4. **Include in completion report** with recommendations

## Final Deliverable

Produce a comprehensive resolution completion report that:
1. **Documents all applied fixes** with specific details
2. **Identifies any issues** encountered during resolution
3. **Provides quality validation** results
4. **Includes recommendations** for next steps
5. **Captures lessons learned** for future improvements

The goal is to provide a complete and accurate summary of the resolution process, ensuring all approved fixes are applied correctly and documentation quality is maintained or improved.
