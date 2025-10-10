# Integration Alignment Agent Instructions

## Mission
Ensure 100% integration alignment across component specifications, API documentation, configuration systems, and canonical architectural principles.

## Trigger Conditions
**CRITICAL**: This agent should ONLY run after the following conditions are met:

1. **Quality Gates Agent completes successfully** (60%+ overall pass rate)
2. **Architecture Compliance Agent completes successfully** (no violations)
3. **Task Execution Agent completes successfully** (core tasks finished)
4. **System health validation passes** (all components healthy)

**Pre-execution check**: Run `python3 scripts/test_integration_alignment_quality_gates.py` first to validate current alignment status.

## Primary Objectives

### 1. Component-to-Component Workflow Alignment
- Verify component communication patterns match canonical architecture
- Validate tight loop architecture compliance
- Check data flow patterns and shared clock usage
- Ensure synchronous execution patterns
- Validate component reference patterns (set at init, never runtime parameters)

### 2. Function Call and Method Signature Alignment
- Verify canonical architecture compliance across all components
- Check synchronous vs async patterns
- Validate method signature consistency
- Ensure component reference patterns
- Validate shared clock pattern usage

### 3. Links and Cross-Reference Validation
- Add comprehensive cross-references between ALL component specs
- Standardize cross-reference format across all specs
- Document component integration relationships
- Ensure all internal documentation links use correct format
- Validate external links to canonical sources

### 4. Mode-Specific Behavior Documentation
- Validate BASIS_EXECUTION_MODE usage consistency
- Check backtest vs live behavior documentation
- Ensure mode-agnostic components don't have mode-specific logic
- Validate mode-aware behavior documentation

### 5. Configuration and Environment Variable Alignment
- Add comprehensive configuration parameter documentation to component specs
- Document environment variable usage with context
- Validate YAML configuration structure alignment
- Add cross-references to CONFIGURATION.md and ENVIRONMENT_VARIABLES.md
- Ensure configuration parameter usage is clearly explained

### 6. API Documentation Integration
- Add API endpoint references to component specs
- Document API integration patterns
- Add cross-references to API_DOCUMENTATION.md
- Ensure component specs reference API documentation
- Validate endpoint integration patterns

## Canonical Source Hierarchy

When detecting or resolving alignment issues, use this hierarchy:
1. **REFERENCE_ARCHITECTURE_CANONICAL.md** - All architectural principles and patterns
2. **API_DOCUMENTATION.md** - API endpoint specifications and integration patterns
3. **WORKFLOW_GUIDE.md** - Component workflow and data flow patterns
4. **CONFIGURATION.md** - Configuration hierarchy and parameter definitions
5. **ENVIRONMENT_VARIABLES.md** - Environment variable definitions and usage
6. **Component specs** - Implementation details and integration patterns

## Analysis Process

### Phase 1: Component-to-Component Workflow Alignment
1. **Validate Component Communication Patterns**
   - Check method signatures: `update_state(timestamp: pd.Timestamp, trigger_source: str, ...)`
   - Verify components receive references at init, never as runtime parameters
   - Validate direct method calls (no async messaging)
   - Check shared clock pattern usage

2. **Verify Tight Loop Architecture Compliance**
   - Check tight loop execution reconciliation pattern
   - Validate execution_manager → execution_interface_manager → position_update_handler chain
   - Ensure synchronous execution (no async/await in internal methods)
   - Validate reconciliation handshake patterns

3. **Validate Data Flow Patterns**
   - Check DataProvider provides market data snapshots
   - Verify components query data using shared clock pattern
   - Ensure components don't cache data across timestamps
   - Validate on-demand loading pattern for backtest mode

### Phase 2: Function Call and Method Signature Alignment
1. **Verify Canonical Architecture Compliance**
   - Check "Component References (Set at Init)" sections exist
   - Verify all component references are listed
   - Confirm statement: "These references are stored in __init__ and used throughout component lifecycle"
   - Validate no component references passed as runtime method parameters

2. **Validate Synchronous vs Async Patterns**
   - Confirm internal methods are synchronous (no async def)
   - Verify async only used for I/O operations (Event Logger exception)
   - Check method signatures don't use async/await incorrectly

### Phase 3: Links and Cross-Reference Validation
1. **Add Comprehensive Cross-References**
   - Add cross-references to ALL related components
   - Document component integration relationships
   - Standardize cross-reference format across all specs
   - Ensure all components reference each other appropriately

2. **Validate Link Formats**
   - Check all internal documentation links use correct format: `[text](path.md)`
   - Verify external links to canonical sources are properly formatted
   - Ensure cross-references between component specs are consistent

### Phase 4: Mode-Specific Behavior Documentation
1. **Validate Mode Documentation Consistency**
   - Check BASIS_EXECUTION_MODE usage is consistent across all components
   - Verify backtest vs live behavior is clearly marked in mode-aware components
   - Ensure mode-agnostic components properly document generic behavior
   - Validate no mode-specific logic found in generic components

### Phase 5: Configuration and Environment Variable Alignment
1. **Add Configuration Parameter Documentation**
   - Document all relevant config parameters in component specs
   - Add environment variable documentation with usage context
   - Include YAML configuration structure documentation
   - Add cross-references to CONFIGURATION.md and ENVIRONMENT_VARIABLES.md

2. **Validate Configuration References**
   - Check config parameter references match YAML config structure
   - Verify all config fields referenced exist in configs/modes/*.yaml
   - Validate venue configuration references match configs/venues/*.yaml
   - Confirm share class references align with configs/share_classes/*.yaml

3. **Validate Environment Variable Usage**
   - Check BASIS_ENVIRONMENT usage is consistent
   - Verify BASIS_DEPLOYMENT_MODE references are accurate
   - Validate BASIS_EXECUTION_MODE usage matches canonical definition
   - Confirm BASIS_DATA_MODE usage in Data Provider spec

### Phase 6: API Documentation Integration
1. **Add API Endpoint References**
   - Add API endpoint references to Backtest Service spec
   - Add API endpoint references to Live Trading Service spec
   - Add API integration patterns to Event Engine spec
   - Add strategy selection endpoint references to Strategy Manager spec

2. **Document API Integration Patterns**
   - Add API integration patterns section to component specs
   - Document service integration flow
   - Add cross-references to API_DOCUMENTATION.md
   - Ensure component specs reference API documentation

## Output Format

### Integration Alignment Report Structure
```markdown
# Integration Alignment Report

## Executive Summary
- Total components analyzed: X
- Alignment issues found: Y
- Critical misalignments: Z
- Overall alignment score: X%

## Phase 1: Component-to-Component Workflow Alignment
### ✅ **EXCELLENT ALIGNMENT**
- Component Communication Patterns: 100% aligned
- Tight Loop Architecture: 100% aligned
- Data Flow Patterns: 100% aligned

## Phase 2: Function Call and Method Signature Alignment
### ✅ **EXCELLENT ALIGNMENT**
- Canonical Architecture Compliance: 100% aligned
- Synchronous vs Async Patterns: 100% aligned
- Method Signature Consistency: 100% aligned

## Phase 3: Links and Cross-Reference Validation
### ✅ **EXCELLENT ALIGNMENT**
- Comprehensive Cross-References: 100% aligned
- Link Format Consistency: 100% aligned
- Component Integration Documentation: 100% aligned

## Phase 4: Mode-Specific Behavior Documentation
### ✅ **EXCELLENT ALIGNMENT**
- Mode Documentation Consistency: 100% aligned
- Backtest vs Live Behavior: 100% aligned
- Mode-Agnostic Architecture: 100% aligned

## Phase 5: Configuration and Environment Variable Alignment
### ✅ **EXCELLENT ALIGNMENT**
- Configuration Parameter Documentation: 100% aligned
- Environment Variable Usage: 100% aligned
- YAML Config Structure: 100% aligned

## Phase 6: API Documentation Integration
### ✅ **EXCELLENT ALIGNMENT**
- API Endpoint References: 100% aligned
- API Integration Patterns: 100% aligned
- Component-API Cross-References: 100% aligned

## Recommendations
1. Add comprehensive cross-references between ALL component specs
2. Document all configuration parameters in component specs
3. Add environment variable usage context
4. Integrate API endpoint references
5. Standardize cross-reference format across all specs
```

## Validation Checklist

### Before Completing Analysis
- [ ] All component specs analyzed for workflow alignment
- [ ] All method signatures validated for canonical compliance
- [ ] All cross-references added and validated
- [ ] All mode-specific behavior documented
- [ ] All configuration parameters documented
- [ ] All environment variables documented
- [ ] All API endpoints referenced in component specs
- [ ] All architectural principles aligned
- [ ] All component integration relationships documented
- [ ] All configuration references validated

### Success Criteria
- [ ] 100% component-to-component workflow alignment
- [ ] 100% function call and method signature alignment
- [ ] 100% links and cross-reference validation
- [ ] 100% mode-specific behavior documentation
- [ ] 100% configuration and environment variable alignment
- [ ] 100% API documentation integration
- [ ] All component specs have comprehensive cross-references
- [ ] All component specs document configuration parameters
- [ ] All component specs reference environment variables
- [ ] All component specs integrate with API documentation

## Tools and Commands

### Analysis Commands
```bash
# Find all component specs
find docs/specs/ -name "*.md" -type f

# Check component references
grep -r "Component References (Set at Init)" docs/specs/

# Validate method signatures
grep -r "update_state(timestamp: pd.Timestamp" docs/specs/

# Check cross-references
grep -r "\[.*\]\(.*\.md\)" docs/specs/

# Validate configuration references
grep -r "config\[" docs/specs/

# Check environment variable usage
grep -r "BASIS_" docs/specs/

# Validate API endpoint references
grep -r "/api/v1/" docs/specs/
```

### Validation Commands
```bash
# Check if referenced files exist
grep -r "\.md" docs/specs/ | sed 's/.*\[\([^]]*\)\](\([^)]*\)).*/\2/' | sort | uniq

# Verify configuration files exist
find configs/ -name "*.yaml" -type f

# Check environment variable definitions
grep -r "BASIS_" docs/ENVIRONMENT_VARIABLES.md
```

## Error Handling

### If Misalignments Found
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

Produce a comprehensive integration alignment report that:
1. **Identifies all misalignments** with specific file and line references
2. **Provides resolution recommendations** for each misalignment
3. **Prioritizes fixes** by impact and urgency
4. **Includes validation checklist** showing what was checked
5. **Provides actionable next steps** for achieving 100% integration alignment

The goal is to achieve 100% integration alignment across all component specifications, API documentation, configuration systems, and architectural principles.
