# Docs Logical Inconsistency Detection Agent Instructions

## Mission
Identify logical inconsistencies across all documentation through exhaustive cross-referencing of every doc to every other doc, generating prescriptive resolution reports.

## Primary Objectives

### 1. Exhaustive Cross-Reference Analysis
- Cross-reference all 35 documentation files against each other
- Detect semantic contradictions in same concepts
- Identify structural inconsistencies in terminology and definitions
- Generate comprehensive conflict matrix showing all relationships

### 2. Canonical Source Prioritization
- Establish clear hierarchy of authoritative sources
- Always prioritize canonical sources as correct
- Provide prescriptive resolutions based on canonical authority
- Ensure consistent application of architectural principles

### 3. Prescriptive Report Generation
- Generate detailed inconsistency reports with exact line references
- Provide specific resolution steps for each conflict
- Classify conflicts by severity and impact
- Create actionable fix recommendations

## Analysis Process

### Step 1: Documentation Inventory and Loading
1. **Load All Documentation Files**
   - Read all files in `docs/` directory (18 files)
   - Read all files in `docs/specs/` directory (17 files)
   - Load canonical source files for reference
   - Create in-memory index of all content

2. **Extract Key Concepts and Terms**
   - Parse each document for architectural concepts
   - Extract configuration requirements and patterns
   - Identify API specifications and endpoints
   - Catalog quality gate criteria and testing requirements
   - Extract component responsibilities and workflows

3. **Build Concept Mapping**
   - Create concept-to-document mapping
   - Identify documents discussing same topics
   - Map terminology variations for same concepts
   - Build semantic similarity index

### Step 2: Exhaustive Cross-Reference Analysis
1. **Pairwise Document Analysis**
   - For each document pair (A, B):
     - Extract overlapping concepts and topics
     - Compare statements about same concepts
     - Detect contradictory descriptions
     - Identify conflicting requirements
     - Flag inconsistent terminology

2. **Semantic Contradiction Detection**
   - Compare architectural principles across docs
   - Detect opposing configuration requirements
   - Identify conflicting API specifications
   - Spot incompatible quality gate criteria
   - Find contradictory workflow descriptions

3. **Structural Inconsistency Detection**
   - Identify inconsistent terminology for same concepts
   - Detect different data structure definitions
   - Find conflicting component responsibilities
   - Spot divergent testing requirements
   - Flag mismatched implementation patterns

### Step 3: Canonical Source Hierarchy Application
1. **Establish Authority Levels**
   - **Level 1 (Highest)**: `REFERENCE_ARCHITECTURE_CANONICAL.md`
   - **Level 2**: `ARCHITECTURAL_DECISION_RECORDS.md`
   - **Level 3**: `MODES.md`
   - **Level 4**: `VENUE_ARCHITECTURE.md`
   - **Level 5**: Component specs (`docs/specs/`)
   - **Level 6**: Guide docs (`WORKFLOW_GUIDE.md`, `USER_GUIDE.md`, etc.)
   - **Level 7**: Task files (`.cursor/tasks/`)

## Canonical Source for Conflict Resolution

When detecting or resolving conflicts, use this hierarchy:
1. **REFERENCE_ARCHITECTURE_CANONICAL.md** - All architectural principles and patterns
2. **ARCHITECTURAL_DECISION_RECORDS.md** - Historical ADR details
3. **MODES.md** - Strategy mode specifications
4. **VENUE_ARCHITECTURE.md** - Venue execution patterns
5. **Component specs** - Implementation details
6. **Guide docs** - Workflow and usage patterns

For architectural conflicts, REFERENCE_ARCHITECTURE_CANONICAL.md is the ultimate authority.

2. **Conflict Resolution Logic**
   - When conflicts found, higher authority level wins
   - Generate prescriptive fix: update lower authority to match higher
   - Provide exact line references for required changes
   - Include rationale for canonical source choice

### Step 4: Report Generation
1. **Executive Summary**
   - Total documents analyzed
   - Total inconsistencies found
   - Critical conflicts count
   - Overall consistency score percentage
   - High-level recommendations

2. **Critical Inconsistencies Section**
   - **CRITICAL**: Blocks implementation or causes system failure
   - **HIGH**: Major architectural deviation
   - **MEDIUM**: Inconsistency requiring clarification
   - **LOW**: Minor documentation mismatch

3. **Detailed Conflict Analysis**
   For each inconsistency:
   ```markdown
   ## [Doc A] vs [Doc B] - [Concept Name]
   
   **Conflict Type**: [Semantic/Structural]
   **Severity**: [CRITICAL/HIGH/MEDIUM/LOW]
   
   **Doc A Statement** (Line X):
   > [Exact quote from Doc A]
   
   **Doc B Statement** (Line Y):
   > [Exact quote from Doc B]
   
   **Canonical Source**: [Which document is authoritative]
   **Authority Level**: [1-6 based on hierarchy]
   
   **Prescribed Resolution**:
   - Update [Non-canonical doc] line [X] to match [Canonical doc] line [Y]
   - Change: "[Current text]" → "[Canonical text]"
   - Rationale: [Why canonical source is correct]
   
   **Impact Assessment**:
   - [Description of impact if not fixed]
   - [Potential consequences]
   ```

4. **Cross-Reference Matrix**
   - Matrix showing all document pairs analyzed
   - Conflict count per pair
   - Severity distribution
   - Coverage completeness verification

## Detection Capabilities

### Semantic Analysis
- **Concept Contradiction Detection**: Find same concepts described differently
- **Architectural Principle Conflicts**: Detect opposing architectural statements
- **Configuration Requirement Conflicts**: Identify incompatible config requirements
- **API Specification Conflicts**: Find contradictory API documentation
- **Quality Gate Conflicts**: Spot incompatible testing criteria

### Structural Analysis
- **Terminology Inconsistency**: Same concepts using different terms
- **Data Structure Conflicts**: Different definitions for same data structures
- **Component Responsibility Conflicts**: Overlapping or conflicting responsibilities
- **Workflow Divergence**: Different descriptions of same processes
- **Testing Requirement Mismatches**: Incompatible testing approaches

### Advanced Detection
- **Implicit Contradictions**: Detect logical inconsistencies not explicitly stated
- **Context-Dependent Conflicts**: Find conflicts that depend on specific contexts
- **Temporal Inconsistencies**: Detect outdated information vs current requirements
- **Scope Boundary Conflicts**: Find overlapping or conflicting scope definitions

## Report Structure Template

```markdown
# Logical Inconsistency Analysis Report

**Generated**: [Current timestamp]
**Scope**: All documentation files (35 total)
**Analysis Type**: Exhaustive cross-referencing with prescriptive resolution

---

## Executive Summary

- **Total Documents Analyzed**: 35
- **Total Inconsistencies Found**: [X]
- **Critical Conflicts**: [Y] (blocks implementation)
- **High Priority Conflicts**: [Z] (major architectural deviation)
- **Medium Priority Conflicts**: [A] (requires clarification)
- **Low Priority Conflicts**: [B] (minor documentation mismatch)
- **Overall Consistency Score**: [X]%

### Key Findings
- [Summary of most critical issues]
- [Architectural principle violations]
- [Configuration conflicts]
- [API documentation issues]

---

## Critical Inconsistencies (MUST FIX)

### [Concept Name] - [Doc A] vs [Doc B]
**Conflict Type**: [Semantic/Structural]
**Severity**: CRITICAL

**Doc A Statement** (Line X):
> [Exact quote]

**Doc B Statement** (Line Y):
> [Exact quote]

**Canonical Source**: [Authoritative document]
**Authority Level**: [1-6]

**Prescribed Resolution**:
- Update [Non-canonical doc] line [X] to match [Canonical doc] line [Y]
- Change: "[Current text]" → "[Canonical text]"
- Rationale: [Why canonical source is correct]

**Impact Assessment**:
- [Description of impact if not fixed]
- [Potential system consequences]

---

## High Priority Inconsistencies

[Same format as Critical, but with HIGH severity]

---

## Medium Priority Inconsistencies

[Same format as Critical, but with MEDIUM severity]

---

## Low Priority Inconsistencies

[Same format as Critical, but with LOW severity]

---

## Cross-Reference Matrix

| Doc A | Doc B | Conflicts | Critical | High | Medium | Low |
|-------|-------|-----------|----------|------|--------|-----|
| [Doc] | [Doc] | [X] | [Y] | [Z] | [A] | [B] |

---

## Recommendations

### Immediate Actions Required (CRITICAL)
1. [List critical fixes needed]
2. [Architecture violations to resolve]
3. [Configuration conflicts to fix]

### High Priority Actions
1. [List high priority fixes]
2. [Major deviations to address]

### Medium Priority Actions
1. [List medium priority fixes]
2. [Clarifications needed]

### Low Priority Actions
1. [List low priority fixes]
2. [Minor improvements]

---

## Success Criteria

### Primary Success Criteria
- [ ] All CRITICAL inconsistencies identified and resolved
- [ ] All HIGH priority conflicts addressed
- [ ] Canonical sources properly prioritized
- [ ] Prescriptive resolutions provided for all conflicts

### Secondary Success Criteria
- [ ] All MEDIUM priority conflicts resolved
- [ ] Cross-reference matrix complete
- [ ] Terminology standardized
- [ ] Documentation consistency achieved

### Tertiary Success Criteria
- [ ] All LOW priority conflicts resolved
- [ ] Complete coverage of all doc pairs
- [ ] Quality gates pass
- [ ] No remaining logical inconsistencies

---

## Next Steps

1. **Review Report**: Examine all identified inconsistencies
2. **Prioritize Fixes**: Start with CRITICAL conflicts
3. **Apply Resolutions**: Use prescriptive fixes provided
4. **Validate Changes**: Ensure no new conflicts introduced
5. **Update Documentation**: Apply all approved fixes
6. **Re-run Analysis**: Verify consistency achieved
```

## Validation Requirements

### Before Completing Analysis
- [ ] All 35 documentation files loaded and analyzed
- [ ] All document pairs cross-referenced
- [ ] All conflicts identified and classified
- [ ] Canonical sources properly prioritized
- [ ] Prescriptive resolutions provided for all conflicts
- [ ] Cross-reference matrix complete
- [ ] Report generated with proper structure

### Success Criteria
- [ ] Complete logical inconsistency analysis performed
- [ ] All conflicts have prescriptive resolution
- [ ] Canonical sources properly prioritized
- [ ] Matrix shows complete coverage
- [ ] Report is actionable and specific
- [ ] All line references are accurate
- [ ] Severity levels are appropriate

## Error Handling

### If Inconsistencies Cannot Be Resolved
1. **Document the uncertainty** in the analysis
2. **List specific areas** that need manual review
3. **Provide guidance** for further investigation
4. **Reference relevant canonical sources** for resolution

### If Canonical Source Is Unclear
1. **Document the ambiguity** in source hierarchy
2. **List potential canonical sources** with rationale
3. **Provide guidance** for manual decision
4. **Suggest escalation** to project maintainers

### If Semantic Analysis Fails
1. **Document the analysis limitation**
2. **List specific concepts** that need manual review
3. **Provide fallback analysis** using structural comparison
4. **Suggest manual review** for complex conflicts

## Final Deliverable

Produce a comprehensive logical inconsistency report that:
1. **Identifies all conflicts** with specific file and line references
2. **Provides prescriptive resolutions** based on canonical source hierarchy
3. **Classifies conflicts by severity** and impact
4. **Includes complete cross-reference matrix** showing all relationships
5. **Provides actionable next steps** for achieving 100% consistency

The goal is to provide a complete and accurate analysis of all logical inconsistencies across the entire documentation system, with clear guidance for resolution.
