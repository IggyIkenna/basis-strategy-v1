# Docs Consistency Agent Instructions

## Mission
Ensure 100% consistency across all documentation in the `docs/` directory with zero conflicting statements.

## Primary Objectives

### 1. Cross-Reference Validation
- Verify all internal links between docs/ files are valid
- Check that all referenced files exist
- Ensure all file paths are correct
- Validate all section references

### 2. Architecture Consistency
- Ensure `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` is the single source of truth
- Verify all component specs align with architectural principles
- Check that `.cursor/tasks/` align with architectural decisions
- Validate that implementation matches documented architecture

### 3. Configuration Consistency
- Verify all configuration examples in docs/ match actual config files
- Ensure environment variable documentation matches `.env` files
- Check that YAML structure documentation matches actual YAML files
- Validate Pydantic model documentation matches actual models

### 4. API Documentation Accuracy
- Verify all API endpoints are documented correctly
- Check that request/response examples are accurate
- Ensure error codes match actual implementation
- Validate authentication requirements

### 5. Quality Gates Consistency
- Ensure quality gate documentation matches actual scripts
- Verify pass/fail criteria are consistent
- Check that test requirements match implementation
- Validate coverage requirements

## Analysis Process

### Step 1: Document Inventory
1. List all files in `docs/` and `docs/specs/`
2. Identify all cross-references between documents
3. Map all external references (to code, configs, scripts)
4. Create dependency graph of documentation

### Step 2: Consistency Checks
1. **Architecture Alignment**
   - Compare `REFERENCE_ARCHITECTURE_CANONICAL.md` with all other docs
   - Check for contradictory architectural statements
   - Verify component specifications align with principles

2. **Configuration Alignment**
   - Compare config documentation with actual config files
   - Verify environment variable documentation
   - Check YAML structure documentation

3. **Implementation Alignment**
   - Compare component specs with actual code
   - Verify API documentation with actual endpoints
   - Check quality gate documentation with actual scripts

4. **Cross-Reference Validation**
   - Verify all internal links work
   - Check all file references exist
   - Validate all section references

5. **Broken Link Detection and Repair**
   - Identify all broken internal links
   - Find closest relevant content for each broken link
   - Create redirects to most appropriate existing content
   - Update all references to point to correct files

### Step 3: Conflict Resolution
1. **Identify Conflicts**
   - List all contradictory statements
   - Identify outdated information
   - Find missing documentation
   - Catalog all broken links and references

2. **Prioritize Fixes**
   - Critical conflicts (architecture, configuration)
   - High priority (API, quality gates, broken links)
   - Medium priority (examples, references)
   - Low priority (formatting, minor inconsistencies)

3. **Resolution Strategy**
   - Update conflicting documents to match canonical source
   - Remove outdated information
   - Add missing documentation
   - Fix broken references
   - **CRITICAL: Redirect broken links to closest relevant content (DO NOT REMOVE)**
   - Ensure all information is preserved and accessible

## Output Format

### Consistency Report Structure
```markdown
# Documentation Consistency Report

## Executive Summary
- Total files analyzed: X
- Conflicts found: Y
- Critical issues: Z
- Overall consistency score: X%

## Critical Conflicts (Must Fix)
1. **File**: docs/ARCHITECTURAL_DECISION_RECORDS.md
   **Issue**: Contradicts REFERENCE_ARCHITECTURE_CANONICAL.md on singleton pattern
   **Resolution**: Update to match canonical source

## High Priority Conflicts
1. **File**: docs/API_DOCUMENTATION.md
   **Issue**: Missing endpoint /api/v1/backtest/status
   **Resolution**: Add documentation for missing endpoint

## Broken Link Analysis
1. **Broken Link**: docs/ARCHITECTURAL_DECISION_RECORDS.md → docs/specs/14_COMPONENT.md
   **Context**: "See component specification for details"
   **Best Match**: docs/specs/05_STRATEGY_MANAGER.md (85% content similarity)
   **Resolution**: Update link to point to docs/specs/05_STRATEGY_MANAGER.md
   **Reason**: Contains similar component architecture information

## Recommendations
1. Update docs/ARCHITECTURAL_DECISION_RECORDS.md to match canonical principles
2. Add missing API endpoint documentation
3. Fix broken cross-references
4. Remove outdated configuration examples
5. **CRITICAL: Redirect broken links to closest relevant content (NEVER remove links)**
6. Consolidate similar content where appropriate
7. **Ensure all information is preserved and accessible through redirects**
```

## Success Criteria
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

## Web Agent Integration
This agent is designed to work alongside the main web agent:
- **Priority**: High (runs after docs specs agent)
- **Context Sharing**: Yes (shares documentation context)
- **Compatibility**: Full web agent compatibility
- **Triggers**: After docs specs implementation status agent completes
