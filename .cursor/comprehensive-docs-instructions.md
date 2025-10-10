# Comprehensive Documentation Agent Instructions

## Mission
Ensure 100% comprehensive documentation alignment across all aspects: consistency, integration, configuration, API, and architectural principles.

## Primary Objectives

### 1. Documentation Consistency Validation
- Ensure 100% consistency across all documentation with zero conflicting statements
- Verify all internal links between docs/ files are valid
- Check that all referenced files exist
- Ensure all file paths are correct
- Validate all section references

### 2. Integration Alignment Verification
- Ensure component-to-component workflow alignment
- Verify function call and method signature alignment
- Check links and cross-reference completeness
- Validate mode-specific behavior documentation
- Ensure configuration and environment variable alignment
- Verify API documentation integration
- Check canonical architecture compliance
- Validate cross-reference standardization

### 3. Architecture Consistency
- Ensure `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` is the single source of truth
- Verify all component specs align with architectural principles
- Check that `.cursor/tasks/` align with architectural decisions
- Validate that implementation matches documented architecture

### 4. Configuration Consistency
- Verify all configuration examples in docs/ match actual config files
- Ensure environment variable documentation matches `.env` files
- Check that YAML structure documentation matches actual YAML files
- Validate Pydantic model documentation matches actual models

### 5. API Documentation Accuracy
- Verify all API endpoints are documented correctly
- Check that request/response examples are accurate
- Ensure error codes match actual implementation
- Validate authentication requirements

### 6. Quality Gates Consistency
- Ensure quality gate documentation matches actual scripts
- Verify pass/fail criteria are consistent
- Check that test requirements match implementation
- Validate coverage requirements

### 7. Architecture Compliance Code Scanning
- Scan codebase for violations of documented architectural principles
- Generate actionable task reports for code-docs deviations
- Ensure quality gate coverage for all architectural violations
- Validate DRY compliance in quality gate specifications

## Canonical Source Hierarchy

When detecting or resolving conflicts, use this hierarchy:
1. **REFERENCE_ARCHITECTURE_CANONICAL.md** - All architectural principles and patterns
2. **API_DOCUMENTATION.md** - API endpoint specifications and integration patterns
3. **WORKFLOW_GUIDE.md** - Component workflow and data flow patterns
4. **CONFIGURATION.md** - Configuration hierarchy and parameter definitions
5. **ENVIRONMENT_VARIABLES.md** - Environment variable definitions and usage
6. **ARCHITECTURAL_DECISION_RECORDS.md** - Historical ADR details
7. **MODES.md** - Strategy mode specifications
8. **VENUE_ARCHITECTURE.md** - Venue execution patterns
9. **Component specs** - Implementation details
10. **Guide docs** - Workflow and usage patterns

## Analysis Process

### Phase 1: Documentation Inventory and Consistency
1. **Document Inventory**
   - List all files in `docs/` and `docs/specs/`
   - Identify all cross-references between documents
   - Map all external references (to code, configs, scripts)
   - Create dependency graph of documentation

2. **Consistency Checks**
   - **Architecture Alignment**: Compare `REFERENCE_ARCHITECTURE_CANONICAL.md` with all other docs
   - **Configuration Alignment**: Compare config documentation with actual config files
   - **Implementation Alignment**: Compare component specs with actual code
   - **Cross-Reference Validation**: Verify all internal links work
   - **Broken Link Detection and Repair**: Identify and fix broken links

### Phase 2: Integration Alignment Analysis
1. **Component-to-Component Workflow Alignment**
   - Validate component communication patterns
   - Verify tight loop architecture compliance
   - Check data flow patterns and shared clock usage
   - Ensure synchronous execution patterns

2. **Function Call and Method Signature Alignment**
   - Verify canonical architecture compliance
   - Check synchronous vs async patterns
   - Validate method signature consistency
   - Ensure component reference patterns

3. **Links and Cross-Reference Validation**
   - Add comprehensive cross-references between ALL component specs
   - Standardize cross-reference format across all specs
   - Document component integration relationships
   - Ensure all internal documentation links use correct format

### Phase 3: Configuration and Environment Variable Alignment
1. **Configuration Parameter Documentation**
   - Add comprehensive configuration parameter documentation to component specs
   - Document environment variable usage with context
   - Validate YAML configuration structure alignment
   - Add cross-references to CONFIGURATION.md and ENVIRONMENT_VARIABLES.md

2. **Configuration References Validation**
   - Check config parameter references match YAML config structure
   - Verify all config fields referenced exist in configs/modes/*.yaml
   - Validate venue configuration references match configs/venues/*.yaml
   - Confirm share class references align with configs/share_classes/*.yaml

### Phase 4: API Documentation Integration
1. **API Endpoint References**
   - Add API endpoint references to component specs
   - Document API integration patterns
   - Add cross-references to API_DOCUMENTATION.md
   - Ensure component specs reference API documentation

2. **API Integration Patterns**
   - Add API integration patterns section to component specs
   - Document service integration flow
   - Add cross-references to API_DOCUMENTATION.md
   - Ensure component specs reference API documentation

### Phase 5: Mode-Specific Behavior Documentation
1. **Mode Documentation Consistency**
   - Check BASIS_EXECUTION_MODE usage is consistent across all components
   - Verify backtest vs live behavior is clearly marked in mode-aware components
   - Ensure mode-agnostic components properly document generic behavior
   - Validate no mode-specific logic found in generic components

### Phase 6: Architecture Compliance Code Scanning
1. **Code-Docs Deviation Detection**
   - Scan all Python files for violations of documented architectural principles
   - Identify violations of all 44 ADRs and canonical architectural principles
   - Generate actionable task reports for each violation found
   - Ensure quality gate coverage for all architectural violations

2. **Quality Gate Integration**
   - Reference existing quality gates from scripts/ directory
   - Check for DRY violations before creating new quality gates
   - Ensure quality gates are specific and measurable
   - Include both unit test and integration test requirements

## Output Format

### Comprehensive Documentation Alignment Report Structure
```markdown
# Comprehensive Documentation Alignment Report

## Executive Summary
- Total files analyzed: X
- Consistency issues found: Y
- Integration misalignments: Z
- Critical issues: W
- Overall alignment score: X%

## Phase 1: Documentation Consistency
### ✅ **EXCELLENT ALIGNMENT**
- Architecture Principles: 100% aligned
- Configuration Examples: 100% aligned
- API Documentation: 100% aligned
- Quality Gates: 100% aligned

## Phase 2: Integration Alignment
### ✅ **EXCELLENT ALIGNMENT**
- Component-to-Component Workflow: 100% aligned
- Function Call and Method Signatures: 100% aligned
- Links and Cross-References: 100% aligned
- Mode-Specific Behavior: 100% aligned

## Phase 3: Configuration and Environment Variables
### ✅ **EXCELLENT ALIGNMENT**
- Configuration Parameter Documentation: 100% aligned
- Environment Variable Usage: 100% aligned
- YAML Config Structure: 100% aligned

## Phase 4: API Documentation Integration
### ✅ **EXCELLENT ALIGNMENT**
- API Endpoint References: 100% aligned
- API Integration Patterns: 100% aligned
- Component-API Cross-References: 100% aligned

## Phase 5: Mode-Specific Behavior
### ✅ **EXCELLENT ALIGNMENT**
- Mode Documentation Consistency: 100% aligned
- Backtest vs Live Behavior: 100% aligned
- Mode-Agnostic Architecture: 100% aligned

## Phase 6: Architecture Compliance Code Scanning
### ✅ **EXCELLENT ALIGNMENT**
- Code-Docs Deviation Detection: 100% aligned
- Architecture Violation Coverage: 100% aligned
- Quality Gate Integration: 100% aligned
- DRY Compliance in Quality Gates: 100% aligned

## Critical Issues (Must Fix)
1. **File**: docs/REFERENCE_ARCHITECTURE_CANONICAL.md
   **Issue**: Contradicts component specs on singleton pattern
   **Resolution**: Update to match canonical source

## High Priority Issues
1. **File**: docs/API_DOCUMENTATION.md
   **Issue**: Missing endpoint /api/v1/backtest/status
   **Resolution**: Add documentation for missing endpoint

## Integration Alignment Issues
1. **File**: docs/specs/01_POSITION_MONITOR.md
   **Issue**: Missing cross-references to related components
   **Resolution**: Add comprehensive cross-references

## Configuration Alignment Issues
1. **File**: docs/specs/05_STRATEGY_MANAGER.md
   **Issue**: Missing configuration parameter documentation
   **Resolution**: Add comprehensive configuration documentation

## Architecture Compliance Issues
1. **File**: backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py
   **Issue**: Async/await violations in internal methods (ADR-006)
   **Resolution**: Convert internal methods to synchronous execution

## Recommendations
1. Update all component specs with comprehensive cross-references
2. Add configuration parameter documentation to all component specs
3. Add environment variable usage context to all component specs
4. Integrate API endpoint references in all component specs
5. Standardize cross-reference format across all specs
6. Ensure all information is preserved and accessible
7. Run Architecture Compliance Code Scanner to identify code-docs deviations
8. Generate actionable task reports for all architectural violations
9. Ensure quality gate coverage for all architectural violations
```

## Validation Checklist

### Before Completing Analysis
- [ ] All files in docs/ directory analyzed
- [ ] All cross-references validated
- [ ] All configuration examples verified
- [ ] All API endpoints documented
- [ ] All quality gate requirements checked
- [ ] All architectural principles aligned
- [ ] All component specifications consistent
- [ ] All environment variables documented
- [ ] All file paths verified
- [ ] All section references validated
- [ ] All component-to-component workflows aligned
- [ ] All function call and method signatures aligned
- [ ] All links and cross-references complete
- [ ] All mode-specific behavior documented
- [ ] All configuration and environment variables aligned
- [ ] All API documentation integrated
- [ ] All canonical architecture compliance verified
- [ ] All cross-references standardized

### Success Criteria
- [ ] Zero conflicting statements between docs/ files
- [ ] All cross-references work correctly
- [ ] All configuration examples are accurate
- [ ] All API documentation is complete
- [ ] All quality gate documentation matches implementation
- [ ] All architectural principles are consistently applied
- [ ] All component specifications align with code
- [ ] All environment variables are documented
- [ ] All file paths exist
- [ ] All section references are valid
- [ ] All component-to-component workflows are aligned
- [ ] All function call and method signatures are aligned
- [ ] All links and cross-references are complete
- [ ] All mode-specific behavior is documented
- [ ] All configuration and environment variables are aligned
- [ ] All API documentation is integrated
- [ ] All canonical architecture compliance is verified
- [ ] All cross-references are standardized
- [ ] All code-docs deviations are identified and documented
- [ ] All architectural violations have quality gate coverage
- [ ] All quality gates comply with DRY principles

## Tools and Commands

### Analysis Commands
```bash
# Find all markdown files
find docs/ -name "*.md" -type f

# Check for broken links
grep -r "\[.*\](" docs/ | grep -v "http"

# Find cross-references
grep -r "docs/" docs/ | grep -v "\.md"

# Check configuration references
grep -r "configs/" docs/

# Verify environment variables
grep -r "BASIS_" docs/ | grep -v "BASIS_STRATEGY"

# Check component references
grep -r "Component References (Set at Init)" docs/specs/

# Validate method signatures
grep -r "update_state(timestamp: pd.Timestamp" docs/specs/

# Check API endpoint references
grep -r "/api/v1/" docs/specs/

# Find all component specs
find docs/specs/ -name "*.md" -type f

# Check if referenced files exist
grep -r "\.md" docs/specs/ | sed 's/.*\[\([^]]*\)\](\([^)]*\)).*/\2/' | sort | uniq

# Verify configuration files exist
find configs/ -name "*.yaml" -type f

# Check environment variable definitions
grep -r "BASIS_" docs/ENVIRONMENT_VARIABLES.md
```

### Validation Commands
```bash
# Check if referenced files exist
grep -r "\.md" docs/ | sed 's/.*\[\([^]]*\)\](\([^)]*\)).*/\2/' | sort | uniq

# Verify API endpoints
grep -r "/api/" docs/ | grep -v "http"

# Check quality gate references
grep -r "quality_gates" docs/

# Validate configuration references
grep -r "config\[" docs/specs/

# Check environment variable usage
grep -r "BASIS_" docs/specs/

# Check for architecture violations
grep -r "async def" backend/src/basis_strategy_v1/ | grep -v "event_logger\|results_store\|api"
grep -r "\.get(" backend/src/basis_strategy_v1/ | grep -v "test\|__pycache__"
grep -r "TODO-REFACTOR" backend/src/basis_strategy_v1/
```

## Error Handling

### If Conflicts Found
1. **Document the conflict** with specific file references
2. **Identify the canonical source** for resolution
3. **Provide specific resolution steps**
4. **Prioritize by impact** (critical > high > medium > low)

### If Integration Misalignments Found
1. **Document the misalignment** with specific file and line references
2. **Identify the canonical source** for resolution
3. **Provide specific resolution steps**
4. **Prioritize by impact** (critical > high > medium > low)

### If Cross-References Missing
1. **List all missing cross-references** with component locations
2. **Identify related components** that should be referenced
3. **Provide addition recommendations**

### If Configuration Documentation Missing
1. **List all missing configuration documentation** with component locations
2. **Identify configuration parameters** that should be documented
3. **Provide documentation recommendations**

## Final Deliverable

Produce a comprehensive documentation alignment report that:
1. **Identifies all issues** with specific file and line references
2. **Provides resolution recommendations** for each issue
3. **Prioritizes fixes** by impact and urgency
4. **Includes validation checklist** showing what was checked
5. **Provides actionable next steps** for achieving 100% comprehensive alignment

The goal is to achieve 100% comprehensive documentation alignment across all aspects: consistency, integration, configuration, API, and architectural principles.
