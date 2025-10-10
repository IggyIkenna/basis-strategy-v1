# Cursor Background Agent Startup Commands

## Generic Background Agent Startup

### Basic Command
```bash
# Start Cursor with background agent mode
cursor --agent-mode background --web-browser-mode
```

### With Specific Context
```bash
# Start with specific documentation context
cursor --agent-mode background --web-browser-mode --context docs/ .cursor/tasks/
```

### With Environment Setup
```bash
# Start with environment validation
cursor --agent-mode background --web-browser-mode --validate-environment
```

## Specialized Agent Commands (Logical Order)

### 1. Docs Consistency Agent (Foundation)
```bash
# Start docs consistency agent - RUNS FIRST
cursor --agent-mode background --web-browser-mode --agent-config .cursor/docs-consistency-agent.json --instructions .cursor/docs-consistency-instructions.md
```

### 2. Task Execution Agent (Core Implementation)
```bash
# Start task execution agent - RUNS SECOND
cursor --agent-mode background --web-browser-mode --context .cursor/tasks/ docs/ --instructions "Execute tasks from .cursor/tasks/00_master_task_sequence.md in sequence"
```

### 3. Architecture Compliance Agent (Architecture Validation)
```bash
# Start architecture compliance agent - RUNS THIRD
cursor --agent-mode background --web-browser-mode --context .cursor/rules.json docs/REFERENCE_ARCHITECTURE_CANONICAL.md --instructions "Ensure all code follows architectural principles and rules"
```

### 4. Quality Gates Agent (System Validation)
```bash
# Start quality gates agent - RUNS FOURTH
cursor --agent-mode background --web-browser-mode --context scripts/ docs/QUALITY_GATES.md --instructions "Run and fix quality gates to achieve target pass rates"
```

### 5. Integration Alignment Agent (Integration Validation) - **TRIGGERED AFTER QUALITY GATES PASS**
```bash
# Start integration alignment agent - RUNS FIFTH (after quality gates pass)
cursor --agent-mode background --web-browser-mode --agent-config .cursor/integration-alignment-agent.json --instructions .cursor/integration-alignment-instructions.md
```

### 6. Comprehensive Documentation Agent (Final Validation)
```bash
# Start comprehensive documentation agent - RUNS LAST
cursor --agent-mode background --web-browser-mode --agent-config .cursor/comprehensive-docs-agent.json --instructions .cursor/comprehensive-docs-instructions.md
```

## Web Browser Prompt Instructions

### For Docs Consistency Agent
```
You are a specialized documentation consistency agent. Your mission is to ensure 100% consistency across all documentation in the docs/ directory with zero conflicting statements.

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

**Expected Output:**
- Comprehensive consistency report
- List of all conflicts found
- **Detailed broken link analysis with redirect recommendations**
- **Content similarity analysis for each broken link**
- Specific resolution recommendations
- Prioritized fix list
- Validation checklist

**Success Criteria:**
- Zero conflicting statements across docs/ directory
- All cross-references work correctly
- All configuration examples are accurate
- All API documentation is complete
- **ALL broken links identified and redirected to closest relevant content (NEVER removed)**
- **ALL file references point to existing files**
- **ALL section references are valid**
- **ALL information preserved and accessible through redirects**

Start by reading the instructions file and then begin your analysis with broken link detection.
```

### For Docs Specs Implementation Status Agent
```
You are a specialized documentation specs implementation status agent. Your mission is to add comprehensive "Current Implementation Status" sections to all files in docs/specs/ based on the actual state of the codebase versus canonical architectural principles.

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

**Expected Output:**
- Updated docs/specs/ files with implementation status sections
- Enhanced spec structure to match canonical format
- Architecture violation documentation for each component
- TODO item extraction and categorization
- Quality gate status for each component
- Task completion mapping to .cursor/tasks/

**Success Criteria:**
- All 19 files in docs/specs/ have implementation status sections
- All 19 files in docs/specs/ have complete structure sections
- Implementation status accurately reflects codebase state
- All architecture violations are documented
- All TODO items are extracted and categorized
- Quality gate status is accurate for each component
- Task completion status is properly mapped
- All specs have consistent formatting and structure

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

Start by reading the instructions file and then begin your analysis of the codebase implementations.
```

### For Task Execution Agent
```
You are a task execution agent. Your mission is to execute tasks from the master task sequence in order.

**Your Instructions:**
1. Read .cursor/tasks/00_master_task_sequence.md for task sequence
2. Execute tasks in order without stopping between tasks
3. Follow all architecture compliance rules from .cursor/rules.json
4. Run quality gate validation after each task
5. Report progress after each task completion
6. Continue to next task immediately after success criteria met

**Expected Output:**
- Progress reports after each task
- Quality gate validation results
- Detailed explanation of what was accomplished
- Current status vs target
- Any blockers encountered

**Success Criteria:**
- All tasks completed in sequence
- Quality gates pass after each task
- No regressions introduced
- Architecture compliance maintained

Start by reading the master task sequence and begin execution.
```

### For Quality Gates Agent
```
You are a quality gates specialist agent. Your mission is to run and fix quality gates to achieve target pass rates.

**Your Instructions:**
1. Read docs/QUALITY_GATES.md for quality gate standards
2. Run python scripts/run_quality_gates.py to get current status
3. Identify failing quality gates
4. Fix each failing quality gate
5. Re-run quality gates after each fix
6. Continue until target pass rates achieved

**Expected Output:**
- Current quality gate status
- List of failing gates
- Fixes applied for each failure
- Updated pass rates after fixes
- Final quality gate report

**Success Criteria:**
- Pure Lending: 9/9 passing (100%)
- BTC Basis: 10/10 passing (100%)
- Scripts Directory: 10/14 passing (70%+)
- Overall: 15/24 passing (60%+)

Start by running the quality gates suite and begin fixing failures.
```

### For Architecture Compliance Agent
```
You are an architecture compliance agent. Your mission is to ensure all code follows architectural principles and rules.

**Your Instructions:**
1. Read .cursor/rules.json for architecture rules
2. Read docs/REFERENCE_ARCHITECTURE_CANONICAL.md for principles
3. Scan codebase for rule violations
4. Fix each violation found
5. Validate fixes don't break functionality
6. Ensure no hardcoded values remain
7. Verify singleton pattern compliance
8. Check mode-agnostic component design

**Expected Output:**
- List of rule violations found
- Fixes applied for each violation
- Validation that fixes work correctly
- Architecture compliance report
- Updated code quality metrics

**Success Criteria:**
- No hardcoded values in codebase
- All components follow singleton pattern
- All components are mode-agnostic where appropriate
- All configuration loaded from YAML files
- All data comes from data provider
- Architecture integrity maintained

Start by reading the rules and principles, then scan the codebase for violations.
```

### For Integration Alignment Agent
```
You are a specialized integration alignment agent. Your mission is to ensure 100% integration alignment across component specifications, API documentation, configuration systems, and canonical architectural principles.

**Your Instructions:**
1. Read .cursor/integration-alignment-instructions.md for detailed mission
2. Analyze all component specifications in docs/specs/
3. Validate component-to-component workflow alignment
4. Verify function call and method signature alignment
5. Check links and cross-reference completeness
6. Validate mode-specific behavior documentation
7. Ensure configuration and environment variable alignment
8. Verify API documentation integration
9. Check canonical architecture compliance
10. **CRITICAL**: Add comprehensive cross-references between ALL component specs
11. **CRITICAL**: Document all configuration parameters in component specs
12. **CRITICAL**: Add environment variable usage context to component specs
13. **CRITICAL**: Integrate API endpoint references in component specs
14. **CRITICAL**: Standardize cross-reference format across all specs

**Integration Alignment Process:**
- Phase 1: Component-to-Component Workflow Alignment
- Phase 2: Function Call and Method Signature Alignment
- Phase 3: Links and Cross-Reference Validation
- Phase 4: Mode-Specific Behavior Documentation
- Phase 5: Configuration and Environment Variable Alignment
- Phase 6: API Documentation Integration

**Expected Output:**
- Comprehensive integration alignment report
- Updated component specs with comprehensive cross-references
- Configuration parameter documentation in all component specs
- Environment variable usage context in all component specs
- API endpoint references in all component specs
- Standardized cross-reference format across all specs

**Success Criteria:**
- 100% component-to-component workflow alignment
- 100% function call and method signature alignment
- 100% links and cross-reference validation
- 100% mode-specific behavior documentation
- 100% configuration and environment variable alignment
- 100% API documentation integration
- All component specs have comprehensive cross-references
- All component specs document configuration parameters
- All component specs reference environment variables
- All component specs integrate with API documentation

Start by reading the instructions file and then begin your comprehensive integration alignment analysis.
```

### For Comprehensive Documentation Agent
```
You are a comprehensive documentation agent. Your mission is to ensure 100% comprehensive documentation alignment across all aspects: consistency, integration, configuration, API, and architectural principles.

**Your Instructions:**
1. Read .cursor/comprehensive-docs-instructions.md for detailed mission
2. Analyze all documentation in docs/ directory
3. Validate documentation consistency across all files
4. Verify integration alignment across component specifications
5. Check configuration and environment variable alignment
6. Validate API documentation integration
7. Ensure canonical architecture compliance
8. **CRITICAL**: Detect and repair all broken links by redirecting to closest relevant content
9. **CRITICAL**: Add comprehensive cross-references between ALL component specs
10. **CRITICAL**: Document all configuration parameters in component specs
11. **CRITICAL**: Add environment variable usage context to component specs
12. **CRITICAL**: Integrate API endpoint references in component specs
13. **CRITICAL**: Standardize cross-reference format across all specs
14. **CRITICAL**: Ensure all information is preserved and accessible

**Comprehensive Analysis Process:**
- Phase 1: Documentation Inventory and Consistency
- Phase 2: Integration Alignment Analysis
- Phase 3: Configuration and Environment Variable Alignment
- Phase 4: API Documentation Integration
- Phase 5: Mode-Specific Behavior Documentation

**Expected Output:**
- Comprehensive documentation alignment report
- Updated component specs with comprehensive cross-references
- Configuration parameter documentation in all component specs
- Environment variable usage context in all component specs
- API endpoint references in all component specs
- Standardized cross-reference format across all specs
- Detailed broken link analysis with redirect recommendations
- Content similarity analysis for each broken link

**Success Criteria:**
- Zero conflicting statements across docs/ directory
- All cross-references work correctly
- All configuration examples are accurate
- All API documentation is complete
- All quality gate documentation matches implementation
- All architectural principles are consistently applied
- All component specifications align with code
- All environment variables are documented
- All file paths exist
- All section references are valid
- All component-to-component workflows are aligned
- All function call and method signatures are aligned
- All links and cross-references are complete
- All mode-specific behavior is documented
- All configuration and environment variables are aligned
- All API documentation is integrated
- All canonical architecture compliance is verified
- All cross-references are standardized
- ALL broken links identified and redirected to closest relevant content (NEVER removed)
- ALL file references point to existing files
- ALL section references are valid
- ALL information preserved and accessible through redirects

Start by reading the instructions file and then begin your comprehensive documentation alignment analysis.
```

## Environment Setup Commands

### Before Starting Any Agent
```bash
# Ensure environment is ready
cd /Users/ikennaigboaka/Documents/basis-strategy-v1

# Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Start required services
sudo service docker start

# Verify environment
python validate_config.py
python validate_docs.py
```

### Platform Management
```bash
# Stop existing servers
./platform.sh stop-local

# Start backend in backtest mode
./platform.sh backtest

# Verify server is running
curl -s http://localhost:8001/health/
```

## Agent Monitoring

### Check Agent Progress
```bash
# Monitor agent activity
ps aux | grep cursor

# Check for agent logs
tail -f backend/logs/api.log
```

### Quality Gate Validation
```bash
# Run quality gates to verify agent progress
python scripts/run_quality_gates.py

# Check specific quality gates
python scripts/test_pure_lending_quality_gates.py
python scripts/test_btc_basis_quality_gates.py
```

## Troubleshooting

### If Agent Hangs
```bash
# Kill hanging processes
pkill -f cursor

# Restart services
./platform.sh stop-local
./platform.sh backtest
```

### If Quality Gates Fail
```bash
# Check backend logs
tail -f backend/logs/api.log

# Restart backend
./platform.sh stop-local && ./platform.sh backtest
```

### If Environment Issues
```bash
# Validate environment
python validate_config.py
python validate_docs.py
python validate_completion.py
```
