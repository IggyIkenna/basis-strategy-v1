<!-- 0fc822a4-e650-4d96-aa77-a9a12c2c3e7d 82a382a6-4652-4f84-9964-2104b7b4d91c -->
# Docs Logical Inconsistency Agent System

## Overview

Create two new agents that work together to identify and resolve logical inconsistencies across all documentation through exhaustive cross-referencing.

## Agent 1: Docs Logical Inconsistency Detection Agent

### Files to Create

1. **`.cursor/docs-logical-inconsistency-agent.json`** - Agent configuration
2. **`.cursor/docs-logical-inconsistency-instructions.md`** - Implementation instructions for agent
3. **`.cursor/docs-logical-inconsistency-web-prompt.md`** - Web browser prompt for background execution

### Agent Configuration Structure

Based on existing patterns from `docs-consistency-agent.json` and `docs-specs-implementation-status-agent.json`:

- `agent_name`: "Docs Logical Inconsistency Detection Agent"
- `background_mode`: true
- `web_browser_mode`: true
- `focus_areas`: ["docs/", "docs/specs/", ".cursor/tasks/"]
- `context_files`: All canonical docs (REFERENCE_ARCHITECTURE_CANONICAL.md, REFERENCE_ARCHITECTURE_CANONICAL.md, etc.)
- `primary_mission`: "Identify logical inconsistencies across all documentation through exhaustive cross-referencing of every doc to every other doc"

### Detection Capabilities

**Semantic Analysis:**

- Cross-reference same concepts with different descriptions
- Detect contradictory architectural principles
- Find conflicting configuration requirements
- Identify opposing API specifications
- Spot incompatible quality gate criteria

**Structural Analysis:**

- Inconsistent terminology for same concepts
- Different data structure definitions
- Conflicting component responsibilities
- Divergent workflow descriptions
- Mismatched testing requirements

### Report Generation

Output format: `DOCS_LOGICAL_INCONSISTENCY_REPORT_[timestamp].md`

Report structure:

```markdown
# Logical Inconsistency Analysis Report

## Executive Summary
- Total docs analyzed: X
- Inconsistencies found: Y
- Critical conflicts: Z
- Consistency score: X%

## Critical Inconsistencies (MUST FIX)
[Doc A] vs [Doc B]:
- **Concept**: [What concept has conflict]
- **Doc A Statement** (Line X): [Exact quote]
- **Doc B Statement** (Line Y): [Exact quote]
- **Conflict Type**: [Semantic/Structural]
- **Canonical Source**: [Which is authoritative]
- **Prescribed Resolution**: [Specific fix with priority to canonical]
- **Priority**: CRITICAL/HIGH/MEDIUM/LOW

## Matrix Analysis
[Cross-reference matrix showing all doc pairs checked]
```

### Cross-Referencing Strategy

**Exhaustive approach:**

1. Load all docs in memory (docs/*.md + docs/specs/*.md = ~35 files)
2. For each doc pair (A, B):

   - Extract key concepts, terms, principles from both
   - Compare statements about same concepts
   - Detect contradictions using semantic similarity
   - Flag structural inconsistencies

3. Generate conflict matrix showing all relationships
4. Prioritize by canonical source hierarchy:

   - REFERENCE_ARCHITECTURE_CANONICAL.md (highest)
   - REFERENCE_ARCHITECTURE_CANONICAL.md
   - Component specs
   - Other docs

### Prescriptive Resolution Logic

- Always prioritize canonical sources as correct
- Suggest updating non-canonical to match canonical
- Provide exact line references for changes
- Include severity assessment
- Suggest consolidation where duplicate info exists

## Agent 2: Docs Inconsistency Resolution Agent

### Files to Create

1. **`.cursor/docs-inconsistency-resolution-agent.json`** - Agent configuration
2. **`.cursor/docs-inconsistency-resolution-instructions.md`** - Implementation instructions
3. **`.cursor/docs-inconsistency-resolution-web-prompt.md`** - Web browser prompt

### Agent Configuration

- `agent_name`: "Docs Inconsistency Resolution Agent"
- `background_mode`: true
- `web_browser_mode`: true
- `input_file`: "DOCS_LOGICAL_INCONSISTENCY_REPORT_[timestamp].md"
- `primary_mission`: "Read inconsistency report and apply approved fixes to resolve documented conflicts"

### Resolution Capabilities

**Report Processing:**

- Parse inconsistency report structure
- Extract approved fixes (marked by user)
- Validate resolution prescriptions
- Apply fixes in priority order

**Fix Application:**

- Update non-canonical docs to match canonical sources
- Replace contradictory statements
- Standardize terminology
- Consolidate duplicate information
- Preserve context and formatting

**Validation:**

- Verify fixes don't create new conflicts
- Ensure all approved items resolved
- Generate completion report
- Run quality gates if available

### Workflow Integration

1. User runs Detection Agent → generates report
2. User reviews report, marks approved fixes
3. User runs Resolution Agent with approved report
4. Agent applies all approved fixes
5. Agent generates completion summary

## Implementation Steps

### Step 1: Create Detection Agent Files

Create three files with detection agent configuration, instructions, and web prompt following existing patterns.

### Step 2: Create Resolution Agent Files  

Create three files with resolution agent configuration, instructions, and web prompt for fix application.

### Step 3: Integration

Ensure agents reference each other appropriately and can be chained together in workflow.

### Step 4: Validation

Test with small doc subset to ensure detection and resolution work correctly.

## Key Design Decisions

**Why Exhaustive Cross-Referencing:**

- Ensures no conflicts missed
- Creates comprehensive conflict matrix
- Provides full visibility into doc relationships

**Why Prescriptive Reports:**

- Reduces manual decision-making
- Leverages canonical source hierarchy
- Provides actionable resolution steps

**Why Separate Agents:**

- Allows manual review between detection and fixing
- Prevents automatic incorrect changes
- Gives user control over resolution

**Canonical Source Priority:**

1. REFERENCE_ARCHITECTURE_CANONICAL.md
2. REFERENCE_ARCHITECTURE_CANONICAL.md  
3. VENUE_ARCHITECTURE.md
4. Component specs (docs/specs/)
5. Guide docs (WORKFLOW_GUIDE.md, USER_GUIDE.md, etc.)
6. Task files (.cursor/tasks/)

## Success Criteria

### Detection Agent Success

- All 35 docs cross-referenced against each other
- Report generated with all inconsistencies found
- Each conflict has prescriptive resolution
- Canonical sources properly prioritized
- Matrix shows complete coverage

### Resolution Agent Success

- All approved fixes applied correctly
- No new conflicts introduced
- Completion report generated
- Documentation consistency improved
- Quality gates pass (if applicable)

### Overall Success

- `.cursor/docs-logical-inconsistency-agent.json` created
- `.cursor/docs-logical-inconsistency-instructions.md` created
- `.cursor/docs-logical-inconsistency-web-prompt.md` created
- `.cursor/docs-inconsistency-resolution-agent.json` created
- `.cursor/docs-inconsistency-resolution-instructions.md` created
- `.cursor/docs-inconsistency-resolution-web-prompt.md` created
- All files follow existing agent patterns
- Agents can be executed independently
- Workflow documented in instructions

### To-dos

- [ ] Create .cursor/docs-logical-inconsistency-agent.json with configuration for detection agent
- [ ] Create .cursor/docs-logical-inconsistency-instructions.md with comprehensive detection methodology
- [ ] Create .cursor/docs-logical-inconsistency-web-prompt.md for background web execution
- [ ] Create .cursor/docs-inconsistency-resolution-agent.json with configuration for resolution agent
- [ ] Create .cursor/docs-inconsistency-resolution-instructions.md with fix application methodology
- [ ] Create .cursor/docs-inconsistency-resolution-web-prompt.md for background fix execution