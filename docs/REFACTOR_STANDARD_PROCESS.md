# Refactor Standard Process Guide

**Date**: October 10, 2025  
**Version**: 2.0  
**Scope**: Small to Medium Complexity Refactors  
**Status**: Active Standard Process

---

## Overview

This document defines the **Refactor Standard Process** - a comprehensive 9-agent chain workflow for handling small to medium complexity refactoring tasks. This process ensures complete traceability from code refactoring needs through tasks to documentation and quality gates, with optimal logical ordering and integration alignment validation.

**Updated for Component Spec Standardization**: This process now includes validation for the new 18-section component specification format, including Environment Variables, Config Fields Used, Data Provider Queries, Event Logging Requirements, and Error Codes sections.

**Note**: Large refactors may still require bespoke setup and custom agent configurations.

---

## Process Philosophy

### **Complete Traceability Chain**
Every refactor must have complete traceability across four key artifacts:
- **Code**: Docstrings explaining what needs refactoring and why
- **Tasks**: Detailed refactor requirements and approach
- **Documentation**: Component specifications and implementation status
- **Quality Gates**: Validation criteria and test requirements

### **Automated Validation**
The process uses specialized agents to automatically validate:
- Documentation consistency and completeness
- Task-documentation alignment
- Code documentation quality
- Traceability link integrity

### **Canonical Source Hierarchy**
When conflicts arise, the following hierarchy determines canonical sources:
1. **REFERENCE_ARCHITECTURE_CANONICAL.md** (highest authority - architectural principles)
2. **MODES.md** (strategy mode definitions and requirements)
3. **VENUE_ARCHITECTURE.md** (venue-specific execution patterns)
4. **Component specs** (`docs/specs/`)
5. **Guide docs** (`WORKFLOW_GUIDE.md`, `USER_GUIDE.md`, etc.)
6. **Task files** (`.cursor/tasks/`)

---

## 9-Agent Chain Process (Logical Order)

### **Phase 1: Documentation Foundation** (Agents 1-2)

#### **Agent 1: Docs Specs Implementation Status Agent**
**Purpose**: Establish baseline documentation state with current implementation status

**What it does**:
- Adds comprehensive "Current Implementation Status" sections to all `docs/specs/` files
- Documents architecture compliance violations
- Extracts TODO items and refactoring needs from codebase
- Maps implementation gaps to specific refactoring tasks
- Validates spec structure against 18-section canonical format
- Ensures all component specs follow the standardized 18-section format

**Output**: Updated `docs/specs/` files with implementation status sections

**Timeline**: 4-6 hours

#### **Agent 2: Docs Consistency Agent**
**Purpose**: Ensure documentation consistency and fix broken links

**What it does**:
- Validates all cross-references between documentation files
- Fixes broken internal links by redirecting to closest relevant content
- Ensures architectural principles are consistently applied
- Verifies configuration documentation matches actual files
- Validates API documentation accuracy
- **NEW**: Includes integration alignment checks and cross-reference validation
- **NEW**: Validates 18-section component specification format compliance
- **NEW**: Ensures Event Logging Requirements and Error Codes sections are properly documented

**Output**: 100% consistent documentation with working links

**Timeline**: 2-3 hours

### **Phase 2: Core Implementation** (Agents 3-4)

#### **Agent 3: Task Execution Agent**
**Purpose**: Execute core implementation tasks and fixes

**What it does**:
- Executes tasks from `.cursor/tasks/00_master_task_sequence.md` in sequence
- Implements critical fixes and refactoring requirements
- Ensures all core functionality is working
- Validates implementation against task requirements
- Reports progress after each task completion

**Output**: Completed core implementation tasks

**Timeline**: 6-8 hours

#### **Agent 4: Architecture Compliance Agent**
**Purpose**: Ensure all code follows architectural principles and rules

**What it does**:
- Scans codebase for rule violations from `.cursor/rules.json`
- Fixes each violation found (hardcoded values, singleton patterns, etc.)
- Validates fixes don't break functionality
- Ensures mode-agnostic component design
- Verifies configuration loaded from YAML files

**Output**: Architecture-compliant codebase

**Timeline**: 4-6 hours

### **Phase 3: System Validation** (Agents 5-6)

#### **Agent 5: Quality Gates Agent**
**Purpose**: Run and fix quality gates to achieve target pass rates

**What it does**:
- Runs comprehensive quality gates validation
- Identifies failing quality gates
- Fixes each failing quality gate
- Re-runs quality gates after each fix
- Continues until target pass rates achieved (60%+ overall)
- **NEW**: Validates 18-section component specification format compliance
- **NEW**: Ensures all component specs have proper Event Logging Requirements and Error Codes sections

**Output**: Quality gates passing at target rates

**Timeline**: 4-6 hours

#### **Agent 5.5: Environment & Config Usage Sync Validation** (NEW)
**Purpose**: Validate that all environment variables, config fields, data queries, and event logging used in components are properly documented

**What it does**:
- Scans all component implementations for environment variable usage
- Extracts all config field references by component
- Identifies all data provider queries by component
- Maps all event logging patterns by component
- Compares usage against documentation in ENVIRONMENT_VARIABLES.md and component specs
- Reports undocumented usage and unused documentation
- Ensures 100% sync between code and documentation

**Validation Categories**:
1. Environment Variable Sync (ENVIRONMENT_VARIABLES.md)
2. Config Field Sync (component spec section 6)
3. Data Provider Query Sync (component spec section 7)
4. Event Logging Requirements Sync (component spec section 10)

**Output**: Comprehensive usage sync report with gaps and remediation steps

**Timeline**: 1-2 hours

**Quality Gate**: `scripts/test_env_config_usage_sync_quality_gates.py`

#### **Agent 5.6: Repository Structure Validation & Documentation** (NEW)
**Purpose**: Validate actual repository structure against canonical documentation and generate updated TARGET_REPOSITORY_STRUCTURE.md

**What it does**:
- Scans backend/src/basis_strategy_v1/ directory structure
- Compares actual structure against specs, CODE_STRUCTURE_PATTERNS.md, and REFERENCE_ARCHITECTURE_CANONICAL.md
- Identifies files that are correctly placed, misplaced, missing, or obsolete
- Generates updated TARGET_REPOSITORY_STRUCTURE.md with file annotations:
  - [KEEP]: File in correct location, following patterns
  - [DELETE]: Obsolete file, should be removed
  - [UPDATE]: File exists but needs architecture compliance fixes
  - [MOVE]: File in wrong location, should be relocated
  - [CREATE]: Missing file, should be created
- Provides migration paths and justifications for each annotation

**Output**: Updated docs/TARGET_REPOSITORY_STRUCTURE.md with comprehensive structure documentation

**Timeline**: 2-3 hours

**Quality Gate**: `scripts/test_repo_structure_quality_gates.py`

#### **Agent 6: Integration Alignment Agent** - **TRIGGERED AFTER QUALITY GATES PASS**
**Purpose**: Ensure 100% integration alignment across component specifications, API documentation, configuration systems, and canonical architectural principles

**What it does**:
- Validates component-to-component workflow alignment
- Verifies function call and method signature alignment
- Checks links and cross-reference completeness
- Validates mode-specific behavior documentation
- Ensures configuration and environment variable alignment
- Verifies API documentation integration
- **NEW**: Validates 18-section component specification format compliance
- **NEW**: Ensures Event Logging Requirements and Error Codes sections are properly integrated
- **CRITICAL**: Only runs after quality gates pass (system is stable)

**Output**: 100% integration alignment across all aspects

**Timeline**: 3-4 hours

### **Phase 4: Conflict Detection and Resolution** (Agents 7-8)

#### **Agent 7: Docs Logical Inconsistency Detection Agent**
**Purpose**: Identify logical inconsistencies across all documentation

**What it does**:
- Cross-references every doc against every other doc (1,190 comparisons)
- Detects semantic contradictions in same concepts
- Identifies structural inconsistencies in terminology
- Generates prescriptive resolution reports based on canonical source hierarchy
- Creates comprehensive conflict matrix

**Output**: `DOCS_LOGICAL_INCONSISTENCY_REPORT_[timestamp].md`

**Timeline**: 3-4 hours

#### **Agent 8: Docs Inconsistency Resolution Agent**
**Purpose**: Apply approved fixes to resolve documented conflicts

**What it does**:
- Reads inconsistency report and applies user-approved fixes
- Updates non-canonical docs to match canonical sources
- Preserves document structure and formatting
- Validates no new conflicts are introduced
- Generates completion report

**Output**: Resolved documentation conflicts with completion report

**Timeline**: 2-3 hours

### **Phase 5: Final Validation** (Agents 8-9)

#### **Agent 8: Comprehensive Documentation Agent** (Final Documentation Check)
**Purpose**: Ensure 100% comprehensive documentation alignment across all aspects

**What it does**:
- Combines all documentation processes into final comprehensive validation
- Validates documentation consistency across all files
- Verifies integration alignment across component specifications
- Checks configuration and environment variable alignment
- Validates API documentation integration
- Ensures canonical architecture compliance

**Output**: 100% comprehensive documentation alignment

**Timeline**: 2-3 hours

#### **Agent 9: Architecture Compliance Code Scanner Agent** (Code-Docs Deviation Detection)
**Purpose**: Scan codebase for violations of documented architectural principles and generate actionable task reports

**What it does**:
- Scans all Python files for violations of all 44 ADRs and architectural principles
- Identifies line-by-line violations with file paths and line numbers
- Generates actionable task reports for each violation found
- Ensures quality gate coverage for all architectural violations
- References existing quality gates from scripts/ directory
- Checks for DRY compliance in quality gate specifications
- Provides prioritized task breakdown by impact and urgency
- Creates implementation roadmap with timeline

**Output**: Comprehensive architecture compliance report with actionable tasks and quality gates

**Timeline**: 3-4 hours

---

## Integration Alignment Quality Gate

### **Quality Gate Script**
- **File**: `scripts/test_integration_alignment_quality_gates.py`
- **Purpose**: Validates 100% integration alignment across all aspects
- **Categories**: 8-phase alignment validation
  1. Component-to-component workflow alignment
  2. Function call and method signature alignment
  3. Links and cross-reference validation
  4. Mode-specific behavior documentation
  5. Configuration and environment variable alignment
  6. API documentation integration
  7. **NEW**: 18-section component specification format compliance
  8. **NEW**: Event Logging Requirements and Error Codes integration

### **Success Criteria**
- **100% Pass Rate**: All integration alignment checks must pass
- **Comprehensive Coverage**: All component specs must have cross-references
- **Configuration Documentation**: All config parameters must be documented
- **API Integration**: All API endpoints must be referenced
- **Canonical Compliance**: All specs must align with canonical architecture
- **NEW**: 18-Section Format Compliance: All component specs must follow the standardized 18-section format
- **NEW**: Event Logging Integration: All components must have proper Event Logging Requirements and Error Codes sections

### **Trigger Conditions**
The Integration Alignment Agent should **ONLY** run after:
1. **Quality Gates Agent completes successfully** (60%+ overall pass rate)
2. **Architecture Compliance Agent completes successfully** (no violations)
3. **Task Execution Agent completes successfully** (core tasks finished)
4. **System health validation passes** (all components healthy)

### **Pre-Execution Check**
```bash
# Validate current alignment status before running agent
python3 scripts/test_integration_alignment_quality_gates.py
```

---

## When to Use This Process

### **Small to Medium Complexity Refactors**
This process is ideal for:
- **Component refactoring**: Updating individual components to follow architectural patterns
- **API standardization**: Aligning APIs with documented specifications
- **Architecture compliance**: Fixing violations of architectural principles
- **Quality gate improvements**: Addressing failing quality gate criteria
- **Documentation gaps**: Filling missing implementation status or specs
- **Task-doc misalignment**: Resolving conflicts between tasks and documentation

### **Complexity Indicators**
**Use this process when**:
- Refactor affects 1-3 major components
- Changes are well-defined in existing tasks
- Documentation structure is mostly in place
- Quality gate criteria are established
- Timeline is 1-2 weeks or less

### **When NOT to Use This Process**
**Use bespoke setup for**:
- **Large architectural changes**: Complete system redesigns
- **New feature development**: Major new capabilities not in existing specs
- **Technology migrations**: Moving to new frameworks or languages
- **Multi-month projects**: Complex refactors spanning multiple quarters
- **Research projects**: Exploratory work without clear requirements

---

## Execution Workflow

### **Step 1: Pre-Execution Setup**
1. **Validate Prerequisites**
   - Ensure all relevant tasks exist in `.cursor/tasks/`
   - Verify component specs exist in `docs/specs/`
   - Confirm quality gate tests are available
   - Check that canonical architectural principles are up to date

2. **Prepare Environment**
   - Ensure backend server is running for code analysis
   - Verify all documentation files are accessible
   - Confirm task files are properly formatted
   - Check that quality gate scripts are functional

### **Step 2: Execute Agent Chain**
Execute agents in logical sequence, validating each phase before proceeding:

```bash
# Phase 1: Documentation Foundation
# Run Agent 1: Docs Specs Implementation Status Agent
# Validate: All specs have implementation status sections

# Run Agent 2: Docs Consistency Agent  
# Validate: All links work, no broken references

# Phase 2: Core Implementation
# Run Agent 3: Task Execution Agent
# Validate: Core implementation tasks completed successfully

# Run Agent 4: Architecture Compliance Agent
# Validate: All architectural violations fixed, code is compliant

# Phase 3: System Validation
# Run Agent 5: Quality Gates Agent
# Validate: Quality gates passing at target rates (60%+ overall)

# Run Agent 6: Integration Alignment Agent (TRIGGERED AFTER QUALITY GATES PASS)
# Pre-check: python3 scripts/test_integration_alignment_quality_gates.py
# Validate: 100% integration alignment achieved

# Phase 4: Conflict Detection and Resolution
# Run Agent 7: Docs Logical Inconsistency Detection Agent
# Review: DOCS_LOGICAL_INCONSISTENCY_REPORT_[timestamp].md
# Mark approved fixes in report

# Run Agent 8: Docs Inconsistency Resolution Agent
# Validate: All approved fixes applied, no new conflicts

# Phase 5: Final Validation
# Run Agent 8: Comprehensive Documentation Agent
# Validate: 100% comprehensive documentation alignment

# Run Agent 9: Architecture Compliance Code Scanner Agent
# Validate: Complete architecture compliance report with actionable tasks
```

### **Step 3: Post-Execution Validation**
1. **Run Quality Gates**
   ```bash
   python scripts/run_quality_gates.py --docs
   ```

2. **Validate Traceability**
   - Verify all refactor areas have complete traceability
   - Check that all links work correctly
   - Confirm task-doc alignment is complete

3. **Review Reports**
   - Examine all generated reports for completeness
   - Address any remaining issues identified
   - Update implementation status as needed

---

## Agent Configuration and Usage

### **Agent Files Location**
All agent configurations are stored in `.cursor/`:
- `docs-specs-implementation-status-agent.json`
- `docs-consistency-agent.json`
- `integration-alignment-agent.json` (NEW)
- `comprehensive-docs-agent.json` (NEW)
- `architecture-compliance-code-scanner-agent.json` (NEW)
- `docs-logical-inconsistency-agent.json`
- `docs-inconsistency-resolution-agent.json`
- `docs-tasks-alignment-agent.json`
- `codebase-documentation-agent.json`

### **Execution Methods**
**Web Browser Mode** (Recommended):
- Use provided web prompts for background execution
- Allows for long-running analysis without interruption
- Provides comprehensive progress tracking

**Direct Execution**:
- Run agents directly using configuration files
- Suitable for quick validation runs
- Requires manual progress monitoring

### **Report Management**
**Generated Reports**:
- `integration_alignment_quality_gates_report.md` (NEW)
- `architecture_compliance_code_scanner_report.md` (NEW)
- `DOCS_LOGICAL_INCONSISTENCY_REPORT_[timestamp].md`
- `INCONSISTENCY_RESOLUTION_COMPLETION_REPORT_[timestamp].md`
- `DOCS_TASKS_ALIGNMENT_REPORT_[timestamp].md`
- `CODEBASE_DOCUMENTATION_REPORT_[timestamp].md`

**Report Retention**:
- Keep reports for at least 30 days for reference
- Archive successful reports for process improvement
- Use reports to identify process optimization opportunities

---

## Quality Assurance

### **Success Criteria**
Each phase must meet specific success criteria before proceeding:

**Phase 1 Success**:
- All `docs/specs/` files have implementation status sections
- All documentation links work correctly
- No broken cross-references exist

**Phase 2 Success**:
- Core implementation tasks completed successfully
- All architectural violations fixed
- Code is compliant with architectural principles

**Phase 3 Success**:
- Quality gates passing at target rates (60%+ overall)
- 100% integration alignment achieved
- All component specs have comprehensive cross-references
- All configuration parameters documented
- All API endpoints referenced
- **NEW**: All component specs follow 18-section standardized format
- **NEW**: All components have proper Event Logging Requirements and Error Codes sections
- **NEW**: 100% environment variable usage documented in ENVIRONMENT_VARIABLES.md
- **NEW**: 100% config field usage documented in component specs (section 6)
- **NEW**: 100% data provider queries documented in component specs (section 7)
- **NEW**: 100% event logging patterns documented in component specs (section 10)
- **NEW**: Repository structure validated against canonical documentation
- **NEW**: TARGET_REPOSITORY_STRUCTURE.md updated with current state and required changes
- **NEW**: All component files correctly mapped to expected locations per specs

**Phase 4 Success**:
- All logical inconsistencies identified and resolved
- No new conflicts introduced during resolution
- Canonical source hierarchy properly applied

**Phase 5 Success**:
- 100% comprehensive documentation alignment achieved
- All aspects of documentation are aligned
- Complete architecture compliance report generated
- All code-docs deviations identified and documented
- Actionable task reports with quality gates provided

### **Validation Commands**
```bash
# Validate documentation structure
python scripts/run_quality_gates.py --docs

# Validate integration alignment (NEW)
python scripts/test_integration_alignment_quality_gates.py

# Validate 18-section component specification format (NEW)
python scripts/test_docs_structure_validation_quality_gates.py

# Validate environment variable and config field usage sync (NEW)
python scripts/test_env_config_usage_sync_quality_gates.py

# Validate repository structure alignment (NEW)
python scripts/test_repo_structure_quality_gates.py

# Run all quality gates including integration alignment
python scripts/run_quality_gates.py --category integration

# Run repository structure quality gates via main runner
python scripts/run_quality_gates.py --category repo_structure

# Check for broken links
grep -r "\[.*\](" docs/ | grep -v "http"

# Verify task references
grep -r "\.cursor/tasks/" docs/

# Check docstring completeness
grep -r "REFACTOR REQUIRED" backend/src/

# Check for architecture violations
grep -r "async def" backend/src/basis_strategy_v1/ | grep -v "event_logger\|results_store\|api"
grep -r "\.get(" backend/src/basis_strategy_v1/ | grep -v "test\|__pycache__"
grep -r "TODO-REFACTOR" backend/src/basis_strategy_v1/

# Check for undocumented environment variables (NEW)
grep -r "os.getenv\|os.environ\[" backend/src/basis_strategy_v1/ | grep -v test

# Validate system health before integration alignment
curl -s http://localhost:8001/health/detailed
```

---

## Troubleshooting

### **Common Issues**

**Agent Execution Failures**:
- **Issue**: Agent hangs or times out
- **Solution**: Restart backend server and retry
- **Prevention**: Ensure server is running before starting agents

**Report Generation Issues**:
- **Issue**: Reports are incomplete or missing sections
- **Solution**: Check agent configuration and retry
- **Prevention**: Validate agent files before execution

**Traceability Link Failures**:
- **Issue**: Links in docstrings don't work
- **Solution**: Verify file paths and update links
- **Prevention**: Use relative paths and validate before committing

**Conflict Resolution Problems**:
- **Issue**: Conflicts can't be automatically resolved
- **Solution**: Manual review and resolution required
- **Prevention**: Ensure canonical sources are clearly defined

### **Escalation Process**
1. **Document the issue** with specific details
2. **Check agent logs** for error messages
3. **Review configuration files** for correctness
4. **Consult canonical sources** for resolution guidance
5. **Escalate to project maintainers** if resolution unclear

---

## Process Optimization

### **Performance Improvements**
- **Parallel Execution**: Run independent agents simultaneously when possible
- **Incremental Updates**: Process only changed files for faster execution
- **Caching**: Cache analysis results to avoid redundant work
- **Selective Processing**: Focus on high-priority areas first

### **Quality Improvements**
- **Template Standardization**: Ensure all agents use consistent templates
- **Validation Enhancement**: Add more comprehensive validation checks
- **Error Handling**: Improve error detection and recovery
- **Reporting**: Enhance report quality and actionability

### **Process Evolution**
- **Regular Review**: Assess process effectiveness monthly
- **Feedback Integration**: Incorporate user feedback for improvements
- **Tool Updates**: Update agents as new capabilities become available
- **Documentation Updates**: Keep this guide current with process changes

---

## Integration with Development Workflow

### **Pre-Refactor Checklist**
Before starting any refactor, ensure:
- [ ] Relevant tasks exist in `.cursor/tasks/`
- [ ] Component specs exist in `docs/specs/`
- [ ] Quality gate tests are available
- [ ] Canonical architectural principles are current
- [ ] Backend server is running and accessible

### **During Refactor Process**
- [ ] Execute agents in proper sequence
- [ ] Review and approve generated reports
- [ ] Address any issues identified by agents
- [ ] Validate traceability chain integrity
- [ ] Update implementation status as work progresses

### **Post-Refactor Validation**
- [ ] Run quality gates to verify improvements
- [ ] Validate all traceability links work
- [ ] Review final reports for completeness
- [ ] Update documentation with final status
- [ ] Archive reports for future reference

---

## Success Metrics

### **Process Effectiveness**
- **Documentation Completeness**: 100% of specs have implementation status
- **Link Integrity**: 100% of internal links work correctly
- **Integration Alignment**: 100% integration alignment across all aspects
- **Quality Gates**: 60%+ overall pass rate achieved
- **Architecture Compliance**: 0 architectural violations remain
- **Code-Docs Deviation Detection**: 100% of violations identified and documented
- **Task Generation**: 100% of violations have actionable tasks
- **Quality Gate Coverage**: 100% of violations have quality gate requirements
- **Conflict Resolution**: 0 logical inconsistencies remain
- **Task Alignment**: 100% of pending work has task coverage
- **Traceability**: 100% of refactor areas have complete traceability
- **NEW**: 18-Section Format Compliance: 100% of component specs follow standardized format
- **NEW**: Event Logging Integration: 100% of components have proper logging and error handling
- **NEW**: Environment Variable Documentation: 100% of used env vars are documented
- **NEW**: Config Field Documentation: 100% of used config fields are documented per component
- **NEW**: Data Query Documentation: 100% of data provider queries are documented per component
- **NEW**: Event Logging Documentation: 100% of event patterns are documented per component
- **NEW**: Repository Structure Alignment: 100% of components in correct locations
- **NEW**: File Annotation Documentation: All files annotated with action status
- **NEW**: Migration Path Documentation: Clear paths for all [MOVE] files

### **Quality Improvements**
- **Architecture Compliance**: Reduced violations over time
- **Documentation Quality**: Improved clarity and completeness
- **Task Coverage**: Better alignment between docs and tasks
- **Code Documentation**: Enhanced docstring quality and consistency

### **Process Efficiency**
- **Execution Time**: Total process time under 35 hours (updated for 9-agent chain)
- **Manual Intervention**: Minimal manual fixes required
- **Error Rate**: Low failure rate with good error recovery
- **User Satisfaction**: Positive feedback on process effectiveness
- **Integration Alignment**: 100% alignment achieved with minimal manual intervention
- **Architecture Compliance**: Complete violation detection with actionable task generation

---

## Conclusion

The Refactor Standard Process provides a comprehensive, automated approach to handling small to medium complexity refactoring tasks. By ensuring complete traceability from code through tasks to documentation and quality gates, this process maintains high quality standards while providing clear visibility into refactoring progress and requirements.

**Key Benefits**:
- **Complete Traceability**: Full visibility from code to quality gates
- **Automated Validation**: Reduces manual effort and human error
- **Consistent Quality**: Standardized approach ensures consistent results
- **Clear Documentation**: Comprehensive documentation of all refactor areas
- **Efficient Process**: Streamlined workflow reduces time to completion
- **Integration Alignment**: 100% alignment across all documentation aspects
- **Architecture Compliance**: Complete code-docs deviation detection and task generation
- **Logical Ordering**: Agents run in optimal sequence for maximum effectiveness
- **Quality Gate Integration**: Comprehensive validation at each phase
- **Actionable Task Generation**: Every violation becomes a specific, implementable task
- **NEW**: 18-Section Standardization: All component specs follow consistent, comprehensive format
- **NEW**: Enhanced Event Logging: Dual logging approach (JSONL + CSV) for complete audit trails
- **NEW**: Structured Error Handling: Comprehensive error codes and health integration

**Next Steps**:
1. **Familiarize** team with this process
2. **Practice** with small refactors to build experience
3. **Customize** process for specific project needs
4. **Monitor** effectiveness and optimize over time
5. **Scale** to larger refactors as process matures

For questions or process improvements, consult the project maintainers or refer to the individual agent documentation in `.cursor/`.
