# Docs-Tasks Alignment Agent Instructions

## Mission
Ensure complete alignment between documentation and tasks - docs reflect task status, tasks are comprehensive, no conflicts exist, and all tasks reference relevant docs.

## Primary Objectives

### 1. Bidirectional Validation
- **Docs → Tasks**: Verify all pending work in docs has corresponding tasks
- **Tasks → Docs**: Ensure all tasks reference relevant documentation
- **Implementation Status**: Check that implementation status sections reference tasks
- **Quality Gates**: Validate quality gate requirements match between docs and tasks

### 2. Conflict Detection and Resolution
- Find tasks that contradict documented principles
- Identify tasks with outdated references to moved/renamed docs
- Detect tasks requiring features not documented in specs
- Flag tasks with success criteria different from doc criteria

### 3. Task Completeness Validation
- Check if refactoring needs in docs have comprehensive tasks
- Verify each architecture violation has a task
- Ensure each TODO in implementation status has task coverage
- Validate missing features in docs have corresponding tasks

## Analysis Process

### Step 1: Documentation Analysis
1. **Load All Documentation**
   - Read all files in `docs/` directory (18 files)
   - Read all files in `docs/specs/` directory (17 files)
   - Extract implementation status sections
   - Identify pending work and TODO items
   - Catalog quality gate requirements

2. **Extract Pending Work**
   - Find all "❌ Missing" items in implementation status
   - Identify "🔄 Refactoring Needed" items
   - Extract "⚠️ Partial" functionality items
   - Catalog architecture violations mentioned
   - List quality gate failures

3. **Map Documentation Requirements**
   - Identify architectural decisions requiring tasks
   - Extract component specifications needing implementation
   - Find API requirements needing development
   - Catalog testing requirements needing validation

### Step 2: Task Analysis
1. **Load All Task Files**
   - Read all files in `.cursor/tasks/` directory (29 files)
   - Extract task objectives and requirements
   - Identify task completion criteria
   - Catalog task references to documentation
   - Map task priorities and dependencies

2. **Validate Task References**
   - Check if tasks reference existing documentation
   - Verify task references point to correct files
   - Validate task requirements match doc specifications
   - Ensure task completion criteria align with doc success criteria

3. **Identify Task Gaps**
   - Find pending work in docs without corresponding tasks
   - Identify architecture violations without tasks
   - Check for missing feature development tasks
   - Validate quality gate failure tasks exist

### Step 3: Conflict Detection
1. **Architecture Conflicts**
   - Compare task requirements with architectural principles
   - Check for tasks that violate documented patterns
   - Identify tasks with conflicting architectural approaches
   - Validate task priorities against documented priorities

2. **Specification Conflicts**
   - Compare task requirements with component specs
   - Check for tasks requiring features not in specs
   - Identify tasks with different API requirements
   - Validate task scope against documented scope

3. **Quality Gate Conflicts**
   - Compare task success criteria with quality gate requirements
   - Check for tasks with different testing requirements
   - Identify tasks with conflicting coverage requirements
   - Validate task validation approach against quality gates

### Step 4: Completeness Validation
1. **Task Coverage Analysis**
   - Map each pending work item to existing tasks
   - Identify gaps where no tasks exist
   - Check task comprehensiveness for complex refactors
   - Validate task dependencies are properly documented

2. **Documentation Coverage Analysis**
   - Map each task to referenced documentation
   - Identify tasks without proper doc references
   - Check for outdated or incorrect doc references
   - Validate task context is properly documented

## Report Generation

### Report Structure
```markdown
# Docs-Tasks Alignment Report

**Generated**: [Current timestamp]
**Scope**: All documentation files (35) and task files (29)
**Analysis Type**: Bidirectional validation with conflict detection

---

## Executive Summary

- **Total Docs Analyzed**: 35
- **Total Tasks Analyzed**: 29
- **Alignment Score**: [X]%
- **Critical Conflicts**: [Y]
- **Missing Task Coverage**: [Z]
- **Tasks Missing Doc References**: [A]

### Key Findings
- [Summary of most critical alignment issues]
- [Architecture conflicts found]
- [Task coverage gaps identified]
- [Documentation reference issues]

---

## Docs Missing Task Coverage

### CRITICAL Priority
[List pending work in docs without tasks - blocks implementation]
- **Doc**: [File name]
- **Pending Work**: [Description of what needs to be done]
- **Current Status**: [Implementation status from doc]
- **Required Task**: [What task should exist]
- **Priority**: CRITICAL
- **Impact**: [Why this blocks implementation]

### HIGH Priority
[Same format as CRITICAL, but HIGH priority]

### MEDIUM Priority
[Same format as CRITICAL, but MEDIUM priority]

### LOW Priority
[Same format as CRITICAL, but LOW priority]

---

## Tasks Missing Doc References

### Tasks Without Documentation References
- **Task**: [Task file name]
- **Issue**: [Missing or incorrect doc reference]
- **Required Docs**: [What docs should be referenced]
- **Impact**: [Why this matters for implementation]
- **Priority**: [CRITICAL/HIGH/MEDIUM/LOW]

### Tasks With Outdated References
- **Task**: [Task file name]
- **Current Reference**: [What it currently references]
- **Correct Reference**: [What it should reference]
- **Issue**: [Why current reference is wrong]
- **Priority**: [CRITICAL/HIGH/MEDIUM/LOW]

---

## Task-Doc Conflicts

### Architecture Conflicts
[List conflicts between tasks and architectural principles]
- **Task**: [Task file]
- **Doc**: [Doc file]
- **Conflict**: [Description of conflict]
- **Task Statement** (Line X): [Quote from task]
- **Doc Statement** (Line Y): [Quote from doc]
- **Resolution**: [Which should be canonical and how to fix]
- **Priority**: [CRITICAL/HIGH/MEDIUM/LOW]

### Specification Conflicts
[Same format as Architecture Conflicts, but for component specs]

### Quality Gate Conflicts
[Same format as Architecture Conflicts, but for quality gate requirements]

---

## Task Completeness Issues

### Incomplete Task Coverage
[List areas where task coverage is incomplete]
- **Area**: [Component/feature area]
- **Docs Coverage**: [What docs say needs work]
- **Task Coverage**: [What tasks exist]
- **Gap**: [What's missing]
- **Required Task**: [What should be created]
- **Priority**: [CRITICAL/HIGH/MEDIUM/LOW]

### Task Dependencies Missing
[List tasks that reference missing dependencies]
- **Task**: [Task file]
- **Missing Dependency**: [What dependency is missing]
- **Impact**: [Why this matters]
- **Required Action**: [What needs to be done]
- **Priority**: [CRITICAL/HIGH/MEDIUM/LOW]

---

## Implementation Status Alignment

### Implementation Status Sections
[List implementation status sections and their task references]
- **Doc**: [Spec file]
- **Component**: [Component name]
- **Implementation Status**: [Current status]
- **Task References**: [What tasks are referenced]
- **Missing References**: [What tasks should be referenced]
- **Alignment**: [GOOD/PARTIAL/POOR]

---

## Recommendations

### Immediate Actions Required (CRITICAL)
1. [List critical conflicts that must be resolved]
2. [Missing task coverage that blocks implementation]
3. [Architecture violations that need immediate attention]

### High Priority Actions
1. [List high priority alignment issues]
2. [Task coverage gaps that need addressing]
3. [Documentation reference issues to fix]

### Medium Priority Actions
1. [List medium priority improvements]
2. [Task completeness enhancements]
3. [Documentation alignment improvements]

### Low Priority Actions
1. [List low priority refinements]
2. [Minor documentation updates]
3. [Task reference improvements]

---

## Success Criteria Validation

### Primary Success Criteria
- [ ] All docs with pending work have corresponding tasks
- [ ] All tasks reference relevant documentation
- [ ] No conflicts between task requirements and doc specs
- [ ] Task completeness validated for all refactor areas

### Secondary Success Criteria
- [ ] Implementation status sections properly reference tasks
- [ ] Quality gate requirements aligned between docs and tasks
- [ ] Architectural decisions have corresponding compliance tasks
- [ ] All TODO items in docs have task coverage

### Tertiary Success Criteria
- [ ] Task dependencies properly documented
- [ ] Task priorities align with documented priorities
- [ ] Task scope matches documented component scope
- [ ] Complete traceability between docs and tasks

---

## Next Steps

1. **Review Alignment Report**: Examine all identified issues
2. **Prioritize Fixes**: Start with CRITICAL conflicts and missing coverage
3. **Create Missing Tasks**: Add tasks for pending work without coverage
4. **Update Task References**: Fix outdated or missing doc references
5. **Resolve Conflicts**: Apply canonical source logic to resolve conflicts
6. **Validate Alignment**: Re-run analysis to verify improvements

## Canonical Source for Conflict Resolution

When detecting or resolving conflicts, use this hierarchy:
1. **REFERENCE_ARCHITECTURE_CANONICAL.md** - All architectural principles and patterns
2. **ARCHITECTURAL_DECISION_RECORDS.md** - Historical ADR details
3. **MODES.md** - Strategy mode specifications
4. **VENUE_ARCHITECTURE.md** - Venue execution patterns
5. **Component specs** - Implementation details
6. **Guide docs** - Workflow and usage patterns

For architectural conflicts, REFERENCE_ARCHITECTURE_CANONICAL.md is the ultimate authority.

## Canonical Source Logic

### When Conflicts Occur
**Docs win for:**
- Architecture principles (REFERENCE_ARCHITECTURE_CANONICAL.md)
- Component specifications (docs/specs/)
- API definitions and interfaces
- Quality gate standards and criteria

**Tasks win for:**
- Implementation priorities and sequencing
- Refactoring approach and tactics
- Development methodology decisions
- Resource allocation and timeline

**Resolution Process:**
1. Identify the conflict type (architecture, spec, quality gate, etc.)
2. Determine canonical source based on conflict type
3. Update non-canonical source to match canonical
4. Document the resolution rationale
5. Verify no new conflicts introduced

### Conflict Resolution Examples
- **Architecture Violation**: Task requires singleton pattern, doc shows multiple instances → Update doc to match task
- **Spec Mismatch**: Task requires different API than spec → Update spec to match task if justified
- **Quality Gate Conflict**: Task has different test criteria than quality gates → Update task to match quality gates
- **Priority Mismatch**: Task priority differs from documented priority → Update task to match documented priority

## Validation Requirements

### Before Completing Analysis
- [ ] All 35 documentation files analyzed
- [ ] All 29 task files analyzed
- [ ] All pending work items mapped to tasks
- [ ] All task references validated
- [ ] All conflicts identified and classified
- [ ] All gaps documented with recommendations
- [ ] Report generated with complete analysis

### Success Criteria
- [ ] Complete alignment between documentation and tasks
- [ ] No conflicts between task requirements and doc specs
- [ ] All pending work has corresponding task coverage
- [ ] All tasks reference relevant documentation
- [ ] Implementation status sections properly reference tasks
- [ ] Quality gate requirements aligned between docs and tasks
- [ ] Comprehensive alignment report generated

## Error Handling

### If Task Coverage Cannot Be Determined
1. **Document the uncertainty** in the analysis
2. **List specific areas** that need investigation
3. **Provide guidance** for further analysis
4. **Reference relevant documentation** for resolution

### If Conflicts Cannot Be Resolved
1. **Document the conflict** with specific details
2. **Identify potential canonical sources** for resolution
3. **Provide resolution options** with rationale
4. **Flag for manual review** if automatic resolution unclear

### If Documentation References Are Broken
1. **List all broken references** with file locations
2. **Identify correct references** or suggest removal
3. **Provide fix recommendations** for each broken reference
4. **Include in recommendations** for immediate action

## Final Deliverable

Produce a comprehensive docs-tasks alignment report that:
1. **Identifies all alignment issues** with specific file and line references
2. **Provides resolution recommendations** for each conflict
3. **Documents missing task coverage** with specific task requirements
4. **Validates task completeness** for all refactor areas
5. **Includes actionable next steps** for achieving full alignment

The goal is to provide complete alignment between documentation and tasks, ensuring all pending work has proper task coverage and all tasks reference relevant documentation.
