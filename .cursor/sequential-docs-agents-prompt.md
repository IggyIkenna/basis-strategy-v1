# Sequential Documentation Agents - Web Browser Prompt

## 🎯 **Mission Overview**

Execute two specialized documentation agents in sequence within the same browser session to achieve 100% documentation consistency and complete implementation status across all docs/specs/ files.

## 📋 **Execution Sequence**

### **Phase 1: Implementation Status Agent** (First - Foundation)
- **Duration**: 4-6 hours
- **Focus**: Add implementation status sections and validate structure
- **Output**: Complete specs with implementation status

### **Phase 2: Docs Consistency Agent** (Second - Refinement)  
- **Duration**: 2-3 hours
- **Focus**: Fix broken links and ensure consistency
- **Output**: 100% working documentation with zero conflicts

## 🚀 **Web Browser Prompt**

```
You are a documentation orchestration agent. Your mission is to execute two specialized agents in sequence to achieve complete documentation consistency and implementation status across all docs/specs/ files.

## PHASE 1: IMPLEMENTATION STATUS AGENT

**Agent Hat**: 🎩 IMPLEMENTATION STATUS AGENT

You are now the Documentation Specs Implementation Status Agent. Your mission is to add comprehensive "Current Implementation Status" sections and validate complete structure for all files in docs/specs/ based on the actual state of the codebase versus canonical architectural principles.

**Your Instructions:**
1. Read .cursor/docs-specs-implementation-status-instructions.md for detailed mission
2. Analyze all 19 files in docs/specs/ directory
3. Examine corresponding codebase implementations in backend/src/basis_strategy_v1/core/strategies/components/
4. Extract TODO items and architecture violations from codebase
5. Map implementation status to .cursor/tasks/ requirements
6. Add comprehensive implementation status sections to each spec
7. **CRITICAL**: Validate and enhance spec structure to match canonical format
8. **CRITICAL**: Ensure all implementation status reflects actual codebase state
9. **CRITICAL**: Document all architecture violations with specific details
10. **CRITICAL**: Extract and categorize all TODO items from codebase
11. **CRITICAL**: Ensure all specs have complete structure sections

**Implementation Status Section Template:**
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

**Required Spec Structure Sections:**
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

**Phase 1 Success Criteria:**
- All 19 files in docs/specs/ have implementation status sections
- All 19 files in docs/specs/ have complete structure sections
- Implementation status accurately reflects codebase state
- All architecture violations are documented
- All TODO items are extracted and categorized
- Quality gate status is accurate for each component
- Task completion status is properly mapped
- All specs have consistent formatting and structure

**Phase 1 Validation:**
Run this command to validate Phase 1 completion:
```bash
python scripts/run_quality_gates.py --docs
```

**Expected Phase 1 Results:**
- Specs implementation status passed: 18/18 ✅
- Specs structure passed: 18/18 ✅
- Overall pass rate: 100% ✅

---

## PHASE 2: DOCS CONSISTENCY AGENT

**Agent Hat**: 🎩 DOCS CONSISTENCY AGENT

You are now the Documentation Consistency Agent. Your mission is to ensure 100% consistency across all documentation in the docs/ directory with zero conflicting statements.

**Your Instructions:**
1. Read .cursor/docs-consistency-instructions.md for detailed mission
2. Analyze all files in docs/ and docs/specs/ directories
3. Check for conflicts between documentation files
4. Validate all cross-references and file paths
5. Ensure architectural principles are consistently applied
6. Verify configuration documentation matches actual files
7. Check API documentation accuracy
8. Validate quality gate documentation
9. **CRITICAL**: Detect and repair all broken links by redirecting to closest relevant content
10. **CRITICAL**: Ensure all file references point to existing files
11. **CRITICAL**: Validate all section references are valid

**Broken Link Repair Process:**
- Extract all markdown links from docs/ directory
- Identify broken links (non-existent files, incorrect paths, moved files)
- For each broken link, analyze context and find closest relevant content
- Score potential matches based on content similarity, file name similarity, and directory structure
- **CRITICAL: NEVER remove broken links - always redirect to best matching existing content**
- Update all references to point to correct files with most relevant information
- Validate that redirected content is relevant and no information is lost
- Ensure all information is preserved and accessible through redirects

**Phase 2 Success Criteria:**
- Zero conflicting statements across docs/ directory
- All cross-references work correctly
- All configuration examples are accurate
- All API documentation is complete
- **ALL broken links identified and redirected to closest relevant content (NEVER removed)**
- **ALL file references point to existing files**
- **ALL section references are valid**
- **ALL information preserved and accessible through redirects**

**Phase 2 Validation:**
Run this command to validate Phase 2 completion:
```bash
python scripts/run_quality_gates.py --docs
```

**Expected Phase 2 Results:**
- Documentation structure passed: 17/17 ✅
- Specs implementation status passed: 18/18 ✅
- Specs structure passed: 18/18 ✅
- Link validation passed: 100% ✅
- Overall pass rate: 100% ✅

---

## 🎯 **Overall Success Criteria**

After both phases complete:
- **All 19 docs/specs/ files** have comprehensive implementation status sections
- **All 19 docs/specs/ files** have complete structure matching canonical format
- **All broken links** are redirected to closest relevant content
- **Zero conflicting statements** across entire docs/ directory
- **100% quality gate compliance** for documentation validation
- **All information preserved** and accessible through redirects

## 🔄 **Execution Flow**

1. **Start with Phase 1** (Implementation Status Agent)
2. **Complete all 19 specs** with implementation status and structure validation
3. **Validate Phase 1** with quality gates
4. **Switch to Phase 2** (Docs Consistency Agent)
5. **Fix all broken links** and ensure consistency
6. **Validate Phase 2** with quality gates
7. **Confirm overall success** with final quality gate run

## ⚠️ **Important Notes**

- **Work in sequence** - complete Phase 1 fully before starting Phase 2
- **Use agent hats** to maintain focus and avoid confusion
- **Validate each phase** before proceeding to the next
- **Never remove broken links** - always redirect to relevant content
- **Preserve all information** - ensure nothing is lost in the process

Start with Phase 1: Implementation Status Agent. Read the instructions file and begin your analysis of the codebase implementations.
```

## 🎯 **Usage Instructions**

1. **Copy the entire prompt above** into your web browser
2. **Execute Phase 1** completely (Implementation Status Agent)
3. **Validate Phase 1** with quality gates
4. **Execute Phase 2** completely (Docs Consistency Agent)  
5. **Validate Phase 2** with quality gates
6. **Confirm overall success** with final validation

## 📊 **Expected Timeline**

- **Phase 1**: 4-6 hours (Implementation Status)
- **Phase 2**: 2-3 hours (Docs Consistency)
- **Total**: 6-9 hours for complete documentation overhaul

## ✅ **Success Validation**

Run this command after each phase and at the end:
```bash
python scripts/run_quality_gates.py --docs
```

**Final Success Criteria:**
- All quality gates pass (100% compliance)
- All specs have implementation status sections
- All specs have complete structure
- All broken links are redirected
- Zero conflicting statements
- All information preserved and accessible
