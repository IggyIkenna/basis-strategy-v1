# Documentation Specs Implementation Status Agent Instructions

## Mission
Add comprehensive "Current Implementation Status" sections to all files in `docs/specs/` based on the actual state of the codebase versus canonical architectural principles.

## Primary Objectives

### 1. Implementation Status Analysis
- Analyze all 19 files in `docs/specs/` directory
- Examine corresponding codebase implementations in `backend/src/basis_strategy_v1/core/strategies/components/`
- Extract TODO items and architecture violations from codebase
- Map implementation status to `.cursor/tasks/` requirements

### 2. Spec Structure Validation
- Validate and enhance spec structure to match canonical format
- Ensure all implementation status reflects actual codebase state
- Document all architecture violations with specific details
- Extract and categorize all TODO items from codebase

### 3. Implementation Status Section Template
Each spec must include:
```markdown
## 🔧 **Current Implementation Status**

**Overall Completion**: X% (Core functionality working, architecture refactoring needed)

### **Core Functionality Status**
- ✅ **Working**: [List working features]
- ⚠️ **Partial**: [List partially working features]
- ❌ **Missing**: [List missing features]
- 🔄 **Refactoring Needed**: [List features needing refactoring]

### **Architecture Compliance Status**
- ❌ **VIOLATIONS FOUND**: [List specific violations]
  - **Issue**: [Specific violation description]
  - **Canonical Source**: [Reference to .cursor/tasks/ or architectural principles]
  - **Priority**: [High/Medium/Low]
  - **Fix Required**: [Specific fix needed]

### **TODO Items and Refactoring Needs**
- **High Priority**: [TODO items from codebase]
- **Medium Priority**: [TODO items from codebase]
- **Low Priority**: [TODO items from codebase]

### **Quality Gate Status**
- **Current Status**: [PASS/FAIL/PARTIAL]
- **Failing Tests**: [List specific failing tests]
- **Requirements**: [What's needed to pass]

### **Task Completion Status**
- **Related Tasks**: [List relevant .cursor/tasks/ items]
- **Completion**: [X% complete for each task]
- **Next Steps**: [Specific next steps needed]
```

## Analysis Process

### Step 1: Codebase Analysis
1. **Component Implementation Review**
   - Read each component file in `backend/src/basis_strategy_v1/core/strategies/components/`
   - Identify working vs non-working functionality
   - Document architecture violations
   - Extract TODO comments and refactoring needs

2. **Architecture Compliance Check**
   - Compare implementation against `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`
   - Check compliance with `.cursor/rules.json`
   - Identify violations of architectural principles
   - Document specific fixes needed

3. **Task Mapping**
   - Map implementation gaps to specific `.cursor/tasks/` items
   - Identify task completion status
   - Document next steps for each component

### Step 2: Spec Enhancement
1. **Structure Validation**
   - Ensure all specs follow 18-section canonical format
   - Add missing sections where needed
   - Standardize formatting and structure

2. **Implementation Status Addition**
   - Add comprehensive implementation status sections
   - Include specific details about violations and fixes
   - Reference relevant tasks and architectural principles

3. **Cross-Reference Updates**
   - Update cross-references to other components
   - Ensure all links point to correct files
   - Add missing integration documentation

### Step 3: Quality Gate Integration
1. **Quality Gate Status**
   - Check current quality gate status for each component
   - Identify failing tests and requirements
   - Document what's needed to pass quality gates

2. **Test Coverage Analysis**
   - Review existing tests for each component
   - Identify missing test coverage
   - Document testing requirements

## Required Spec Structure Sections
- Title with component name and emoji
- Component metadata (responsibility, priority, backend file, last reviewed, status)
- Canonical Sources section
- Purpose section
- Component Structure section
- Data Structures section
- Integration with Other Components section
- Implementation section
- Mode-Specific Behavior section
- Testing section
- **Current Implementation Status section (NEW)**
- Success Criteria section

## Expected Output
- Updated `docs/specs/` files with implementation status sections
- Enhanced spec structure to match canonical format
- Architecture violation documentation for each component
- TODO item extraction and categorization
- Quality gate status for each component
- Task completion mapping to `.cursor/tasks/`

## Success Criteria
- All 19 files in `docs/specs/` have implementation status sections
- All 19 files in `docs/specs/` have complete structure sections
- Implementation status accurately reflects codebase state
- All architecture violations are documented
- All TODO items are extracted and categorized
- Quality gate status is accurate for each component
- Task completion status is properly mapped
- All specs have consistent formatting and structure

## Web Agent Integration
This agent is designed to work alongside the main web agent:
- **Priority**: Highest (runs first in refactor process)
- **Context Sharing**: Yes (shares documentation and codebase context)
- **Compatibility**: Full web agent compatibility
- **Triggers**: First phase of refactor standard process
