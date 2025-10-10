# Docs Logical Inconsistency Detection Agent Instructions

## Mission
Identify logical inconsistencies across all documentation through comprehensive cross-referencing.

## Primary Objectives

### 1. Comprehensive Cross-Referencing
- Cross-references every doc against every other doc (1,190+ comparisons)
- Detects semantic contradictions in same concepts
- Identifies structural inconsistencies in terminology
- Generates prescriptive resolution reports based on canonical source hierarchy

### 2. Conflict Matrix Generation
- Creates comprehensive conflict matrix
- Categorizes conflicts by type and severity
- Provides specific file and line references
- Suggests resolution strategies

### 3. Canonical Source Application
- Applies canonical source hierarchy for resolution
- Identifies authoritative sources for each concept
- Provides clear resolution guidance
- Ensures consistency across documentation

## Analysis Methodology

### Step 1: Document Inventory
1. **Catalog All Documents**
   - List all files in `docs/` and `docs/specs/`
   - Identify all cross-references between documents
   - Map all external references (to code, configs, scripts)
   - Create dependency graph of documentation

### Step 2: Semantic Analysis
1. **Concept Extraction**
   - Extract key concepts from each document
   - Identify terminology used for same concepts
   - Map concept relationships across documents
   - Detect semantic contradictions

2. **Cross-Reference Analysis**
   - Validate all internal links between docs
   - Check that all referenced files exist
   - Ensure all file paths are correct
   - Validate all section references

### Step 3: Inconsistency Detection
1. **Contradiction Detection**
   - Compare statements about same concepts
   - Identify conflicting information
   - Detect outdated information
   - Find missing documentation

2. **Structural Analysis**
   - Check terminology consistency
   - Validate formatting consistency
   - Ensure structural consistency
   - Identify organizational issues

## Conflict Categories

### Architectural Principle Conflicts
- Contradictory architectural statements
- Conflicting design patterns
- Inconsistent component descriptions
- Conflicting mode behavior descriptions

### Configuration Requirement Conflicts
- Contradictory configuration requirements
- Conflicting environment variable descriptions
- Inconsistent YAML structure documentation
- Conflicting default value specifications

### API Documentation Conflicts
- Contradictory API endpoint descriptions
- Conflicting request/response formats
- Inconsistent error code documentation
- Conflicting authentication requirements

### Component Specification Conflicts
- Contradictory component descriptions
- Conflicting interface specifications
- Inconsistent data structure definitions
- Conflicting integration requirements

### Quality Gate Conflicts
- Contradictory quality gate criteria
- Conflicting test requirements
- Inconsistent coverage requirements
- Conflicting validation criteria

### Task-Documentation Conflicts
- Tasks that contradict documentation
- Documentation that contradicts tasks
- Missing task coverage for documented features
- Outdated task descriptions

### Terminology Inconsistencies
- Same concept described with different terms
- Inconsistent naming conventions
- Conflicting abbreviations
- Inconsistent technical terminology

### Structural Inconsistencies
- Inconsistent document structure
- Conflicting section organization
- Inconsistent formatting
- Conflicting template usage

## Canonical Source Hierarchy

When conflicts arise, the following hierarchy determines canonical sources:

1. **REFERENCE_ARCHITECTURE_CANONICAL.md** (highest authority - architectural principles)
2. **MODES.md** (strategy mode definitions and requirements)
3. **VENUE_ARCHITECTURE.md** (venue-specific execution patterns)
4. **Component specs** (`docs/specs/`)
5. **Guide docs** (`WORKFLOW_GUIDE.md`, `USER_GUIDE.md`, etc.)
6. **Task files** (`.cursor/tasks/`)

## Expected Output

### Inconsistency Report Structure
```markdown
# Documentation Logical Inconsistency Report

## Executive Summary
- Total documents analyzed: X
- Total comparisons made: Y
- Conflicts found: Z
- Critical conflicts: A
- High priority conflicts: B
- Medium priority conflicts: C
- Low priority conflicts: D

## Conflict Matrix

### Critical Conflicts (Must Fix)
1. **Concept**: Component Architecture
   **Files**: docs/ARCHITECTURAL_DECISION_RECORDS.md vs docs/REFERENCE_ARCHITECTURE_CANONICAL.md
   **Issue**: Contradictory singleton pattern requirements
   **Canonical Source**: docs/REFERENCE_ARCHITECTURE_CANONICAL.md
   **Resolution**: Update ARCHITECTURAL_DECISION_RECORDS.md to match canonical source

### High Priority Conflicts
1. **Concept**: API Authentication
   **Files**: docs/API_DOCUMENTATION.md vs docs/USER_GUIDE.md
   **Issue**: Conflicting authentication requirements
   **Canonical Source**: docs/API_DOCUMENTATION.md
   **Resolution**: Update USER_GUIDE.md to match API documentation

### Terminology Inconsistencies
1. **Concept**: Risk Management
   **Files**: Multiple files use different terms
   **Issue**: "Risk Monitor" vs "Risk Manager" vs "Risk Controller"
   **Canonical Source**: docs/specs/03_RISK_MONITOR.md
   **Resolution**: Standardize on "Risk Monitor" across all documents

## Resolution Recommendations
1. Update non-canonical documents to match canonical sources
2. Standardize terminology across all documents
3. Remove outdated information
4. Add missing documentation
5. Consolidate duplicate information
```

## Success Criteria
- All logical inconsistencies identified with specific file references
- Conflict matrix generated with categorization
- Resolution recommendations provided based on canonical source hierarchy
- All documents cross-referenced against all other documents
- Semantic contradictions detected and documented
- Structural inconsistencies identified and categorized

## Web Agent Integration
This agent is designed to work alongside the main web agent:
- **Priority**: Medium (runs after integration alignment)
- **Context Sharing**: Yes (shares documentation context)
- **Compatibility**: Full web agent compatibility
- **Triggers**: After integration alignment agent completes
- **Dependencies**: Integration alignment complete
