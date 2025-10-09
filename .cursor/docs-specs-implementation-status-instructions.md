# Documentation Specs Implementation Status Agent Instructions

## Mission
Add comprehensive "Current Implementation Status" sections to all files in `docs/specs/` based on the actual state of the codebase versus canonical architectural principles and task requirements.

## Primary Objectives

### 1. Implementation Status Analysis
- Analyze each component's current implementation state
- Identify architecture compliance violations
- Document TODO items and refactoring needs
- Assess quality gate status
- Map task completion status

### 2. Spec Structure Enhancement
- Add standardized "Current Implementation Status" section to each spec
- Include architecture compliance status
- Document specific TODO items from codebase
- Reference relevant .cursor/tasks/ items
- Provide quality gate status

### 3. Canonical Alignment
- Ensure all status sections align with canonical architectural principles
- Reference specific task requirements from .cursor/tasks/
- Map implementation gaps to specific refactoring tasks
- Validate against quality gate requirements

## Analysis Process

### Step 1: Component Analysis
1. **Read each spec file** in `docs/specs/`
2. **Analyze corresponding codebase** implementation
3. **Identify architecture violations** from code comments
4. **Extract TODO items** from codebase
5. **Map to .cursor/tasks/** requirements
6. **Validate spec structure** against canonical format

### Step 2: Implementation Status Documentation
1. **Current Implementation Status**
   - Overall completion percentage
   - Core functionality status
   - Architecture compliance status
   - Known issues and limitations

2. **Architecture Compliance Status**
   - List specific violations found in code
   - Reference canonical architectural principles
   - Map to specific .cursor/tasks/ requirements
   - Priority level for fixes

3. **TODO Items and Refactoring Needs**
   - Extract TODO items from codebase
   - Categorize by priority and type
   - Reference specific task requirements
   - Provide implementation guidance

4. **Quality Gate Status**
   - Current quality gate pass/fail status
   - Specific failing tests or validations
   - Requirements for passing quality gates
   - Integration with overall quality gate system

5. **Task Completion Status**
   - Map to specific .cursor/tasks/ items
   - Completion percentage for each task
   - Blockers and dependencies
   - Next steps for completion

### Step 3: Spec File Updates
1. **Add Implementation Status Section** to each spec
2. **Validate and enhance spec structure** to match canonical format
3. **Ensure consistency** across all specs
4. **Reference canonical sources** appropriately
5. **Update last reviewed dates**

### Step 4: Spec Structure Validation
1. **Validate Required Sections** are present:
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
   - **Current Implementation Status section** (NEW - must be added)
   - Success Criteria section

2. **Ensure Consistent Formatting**:
   - Proper markdown headers (##, ###)
   - Consistent emoji usage
   - Proper code blocks with language specification
   - Consistent bullet point formatting
   - Proper cross-references to other docs

3. **Validate Content Quality**:
   - All sections have meaningful content
   - Code examples are accurate and complete
   - Cross-references are valid
   - Implementation status reflects actual codebase state

## Implementation Status Section Template

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
- **High Priority**:
  - [TODO item from codebase with reference]
  - [Specific refactoring needed]
- **Medium Priority**:
  - [TODO item from codebase with reference]
- **Low Priority**:
  - [TODO item from codebase with reference]

### **Quality Gate Status**
- **Current Status**: [PASS/FAIL/PARTIAL]
- **Failing Tests**: [List specific failing tests]
- **Requirements**: [What's needed to pass]
- **Integration**: [How it integrates with quality gate system]

### **Task Completion Status**
- **Related Tasks**: [List relevant .cursor/tasks/ items]
- **Completion**: [X% complete for each task]
- **Blockers**: [List any blockers]
- **Next Steps**: [Specific next steps needed]
```

## Component-Specific Analysis

### Position Monitor (01_POSITION_MONITOR.md)
- **Current State**: Core functionality working, tight loop architecture violations
- **Key Issues**: TODO-REFACTOR comments in code, live mode queries not implemented
- **Tasks**: 10_tight_loop_architecture_requirements.md

### Exposure Monitor (02_EXPOSURE_MONITOR.md)
- **Current State**: Generic vs mode-specific architecture violations
- **Key Issues**: Mode-specific logic instead of config-driven parameters
- **Tasks**: 18_generic_vs_mode_specific_architecture.md, 14_mode_agnostic_architecture_requirements.md

### Strategy Manager (05_STRATEGY_MANAGER.md)
- **Current State**: Major architecture violations, needs complete refactoring
- **Key Issues**: Complex transfer_manager.py, missing inheritance-based strategy modes
- **Tasks**: strategy_manager_refactor.md, 18_generic_vs_mode_specific_architecture.md

### Event Logger (08_EVENT_LOGGER.md)
- **Current State**: Core functionality working, tight loop architecture violations
- **Key Issues**: TODO-REFACTOR comments for tight loop compliance
- **Tasks**: 10_tight_loop_architecture_requirements.md

### Risk Monitor (03_RISK_MONITOR.md)
- **Current State**: Mode-specific PnL calculator violations
- **Key Issues**: Mode-specific logic instead of generic risk calculation
- **Tasks**: 15_fix_mode_specific_pnl_calculator.md

## Quality Gate Integration

### Documentation Structure Quality Gate
- **Requirement**: All docs/specs/ files must have implementation status sections
- **Validation**: Check for presence of "Current Implementation Status" section
- **Pass Criteria**: All specs have comprehensive implementation status

### Architecture Compliance Quality Gate
- **Requirement**: All components must comply with canonical architectural principles
- **Validation**: Check for architecture violations in implementation status
- **Pass Criteria**: No high-priority architecture violations

### Task Completion Quality Gate
- **Requirement**: All .cursor/tasks/ items must be properly referenced
- **Validation**: Check for task references in implementation status
- **Pass Criteria**: All relevant tasks properly mapped

## Output Requirements

### For Each Spec File
1. **Add Implementation Status Section** using the template
2. **Maintain existing content** and structure
3. **Update last reviewed date** to current date
4. **Ensure consistency** with other specs
5. **Reference canonical sources** appropriately

### Validation Checklist
- [ ] All docs/specs/ files have implementation status sections
- [ ] Implementation status reflects actual codebase state
- [ ] Architecture violations are properly documented
- [ ] TODO items are extracted from codebase
- [ ] Quality gate status is accurate
- [ ] Task completion status is mapped
- [ ] Canonical sources are properly referenced
- [ ] Last reviewed dates are updated

## Success Criteria

### Primary Success Criteria
- [ ] All 19 files in docs/specs/ have implementation status sections
- [ ] Implementation status accurately reflects codebase state
- [ ] All architecture violations are documented
- [ ] All TODO items are extracted and categorized
- [ ] Quality gate status is accurate for each component
- [ ] Task completion status is properly mapped

### Secondary Success Criteria
- [ ] Implementation status sections are consistent across specs
- [ ] Canonical sources are properly referenced
- [ ] Last reviewed dates are updated
- [ ] Documentation structure quality gate passes
- [ ] Architecture compliance quality gate passes
- [ ] Task completion quality gate passes
- [ ] All spec files have required structure sections
- [ ] All spec files have consistent formatting
- [ ] All spec files have accurate content

## Error Handling

### If Implementation Status Cannot Be Determined
1. **Document the uncertainty** in the implementation status
2. **List specific areas** that need investigation
3. **Provide guidance** for further analysis
4. **Reference relevant tasks** for resolution

### If Architecture Violations Are Found
1. **Document each violation** with specific details
2. **Reference canonical sources** for the violation
3. **Provide priority level** for fixing
4. **Map to specific tasks** for resolution

### If Quality Gate Status Is Unclear
1. **Document the uncertainty** in quality gate status
2. **List specific tests** that need to be run
3. **Provide guidance** for validation
4. **Reference quality gate requirements**

## Final Deliverable

Produce updated docs/specs/ files that:
1. **Include comprehensive implementation status sections**
2. **Accurately reflect current codebase state**
3. **Document all architecture violations**
4. **Extract and categorize all TODO items**
5. **Provide accurate quality gate status**
6. **Map task completion status**
7. **Maintain consistency across all specs**
8. **Reference canonical sources appropriately**

The goal is to provide a complete and accurate picture of the current implementation status for all components in the system.
