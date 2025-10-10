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

## Canonical Source for Conflict Resolution

When detecting or resolving conflicts, use this hierarchy:
1. **REFERENCE_ARCHITECTURE_CANONICAL.md** - All architectural principles and patterns
2. **ARCHITECTURAL_DECISION_RECORDS.md** - Historical ADR details
3. **MODES.md** - Strategy mode specifications
4. **VENUE_ARCHITECTURE.md** - Venue execution patterns
5. **Component specs** - Implementation details
6. **Guide docs** - Workflow and usage patterns

For architectural conflicts, REFERENCE_ARCHITECTURE_CANONICAL.md is the ultimate authority.

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

### 6. Integration Alignment Consistency
- Ensure component-to-component workflow alignment
- Verify function call and method signature alignment
- Check links and cross-reference completeness
- Validate mode-specific behavior documentation
- Ensure configuration and environment variable alignment
- Verify API documentation integration
- Check canonical architecture compliance
- Validate cross-reference standardization

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

6. **Content Similarity Analysis**
   - Analyze content similarity between referenced and existing files
   - Identify best matches for broken references
   - Suggest content consolidation where appropriate

7. **Integration Alignment Analysis**
   - Check component-to-component workflow alignment
   - Verify function call and method signature alignment
   - Validate links and cross-reference completeness
   - Check mode-specific behavior documentation
   - Ensure configuration and environment variable alignment
   - Verify API documentation integration
   - Check canonical architecture compliance
   - Validate cross-reference standardization

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

### Step 4: Broken Link Repair Process
1. **Link Analysis**
   - Extract all markdown links from docs/ directory
   - Categorize links: internal, external, file references, section references
   - Test each link for validity

2. **Broken Link Identification**
   - Identify links pointing to non-existent files
   - Find links with incorrect paths
   - Detect links to moved/renamed files
   - Flag links to non-existent sections

3. **Content Matching Algorithm**
   - For each broken link, analyze the context around the link
   - Extract keywords and concepts from the broken reference
   - Search existing docs/ files for similar content
   - Score potential matches based on:
     - Content similarity (keywords, concepts)
     - File name similarity
     - Directory structure similarity
     - Section heading similarity

4. **Redirect Creation (CRITICAL: DO NOT REMOVE LINKS)**
   - **NEVER remove broken links** - the information should always exist somewhere
   - Select best match for each broken link based on content similarity
   - **Update the broken link to point to the correct file** with the most relevant content
   - Add explanatory comment about the redirect if needed
   - Ensure all information from the broken reference is preserved in the target

5. **Validation**
   - Verify all redirects work correctly
   - Ensure redirected content is relevant
   - Check that no information is lost
   - Confirm all references are updated

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
1. **File**: docs/REFERENCE_ARCHITECTURE_CANONICAL.md
   **Issue**: Contradicts REFERENCE_ARCHITECTURE_CANONICAL.md on singleton pattern
   **Resolution**: Update to match canonical source

## High Priority Conflicts
1. **File**: docs/API_DOCUMENTATION.md
   **Issue**: Missing endpoint /api/v1/backtest/status
   **Resolution**: Add documentation for missing endpoint

## Medium Priority Issues
1. **File**: docs/ENVIRONMENT_VARIABLES.md
   **Issue**: Outdated environment variable names
   **Resolution**: Update to match current .env files

## Cross-Reference Issues
1. **File**: docs/COMPONENT_SPECS_INDEX.md
   **Issue**: Links to non-existent file docs/specs/14_COMPONENT.md
   **Resolution**: Remove broken link or create missing file

## Broken Link Analysis
1. **Broken Link**: docs/REFERENCE_ARCHITECTURE_CANONICAL.md → docs/specs/14_COMPONENT.md
   **Context**: "See component specification for details"
   **Best Match**: docs/specs/05_STRATEGY_MANAGER.md (85% content similarity)
   **Resolution**: Update link to point to docs/specs/05_STRATEGY_MANAGER.md
   **Reason**: Contains similar component architecture information

2. **Broken Link**: docs/COMPONENT_SPECS_INDEX.md → docs/specs/08_EVENT_LOGGER.md
   **Context**: "Event logging implementation details"
   **Best Match**: docs/specs/08_EVENT_LOGGER.md (file exists but path incorrect)
   **Resolution**: Fix path from docs/specs/08_EVENT_LOGGER.md to docs/specs/08_EVENT_LOGGER.md
   **Reason**: File exists, just incorrect path reference

## Content Similarity Analysis
1. **Referenced Content**: "Component architecture patterns"
   **Existing Files**: 
     - docs/specs/05_STRATEGY_MANAGER.md (85% similarity)
     - docs/REFERENCE_ARCHITECTURE_CANONICAL.md (78% similarity)
   **Recommendation**: Use docs/specs/05_STRATEGY_MANAGER.md as redirect target

## Recommendations
1. Update docs/REFERENCE_ARCHITECTURE_CANONICAL.md to match canonical principles
2. Add missing API endpoint documentation
3. Fix broken cross-references
4. Remove outdated configuration examples
5. **CRITICAL: Redirect broken links to closest relevant content (NEVER remove links)**
6. Consolidate similar content where appropriate
7. **Ensure all information is preserved and accessible through redirects**
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

# Extract all internal links
grep -r "\[.*\]([^http]" docs/ | sed 's/.*\[\([^]]*\)\](\([^)]*\)).*/\2/' | sort | uniq

# Find links to non-existent files
grep -r "\[.*\]([^http]" docs/ | sed 's/.*\[\([^]]*\)\](\([^)]*\)).*/\2/' | while read link; do
  if [[ ! -f "docs/$link" && ! -f "$link" ]]; then
    echo "BROKEN: $link"
  fi
done

# Find section references
grep -r "#" docs/ | grep -v "^#" | sed 's/.*#\([^[:space:]]*\).*/\1/' | sort | uniq

# Check for moved/renamed files
find docs/ -name "*.md" -exec basename {} \; | sort | uniq
```

### Validation Commands
```bash
# Check if referenced files exist
grep -r "\.md" docs/ | sed 's/.*\[\([^]]*\)\](\([^)]*\)).*/\2/' | sort | uniq

# Verify API endpoints
grep -r "/api/" docs/ | grep -v "http"

# Check quality gate references
grep -r "quality_gates" docs/
```

## Error Handling

### If Conflicts Found
1. **Document the conflict** with specific file references
2. **Identify the canonical source** for resolution
3. **Provide specific resolution steps**
4. **Prioritize by impact** (critical > high > medium > low)

### If Files Missing
1. **List all missing files** referenced in documentation
2. **Identify if file should exist** or reference should be removed
3. **Provide creation or removal recommendations**

### If References Broken
1. **List all broken references** with file locations
2. **Identify correct paths** or suggest removal
3. **Provide fix recommendations**

## Final Deliverable

Produce a comprehensive consistency report that:
1. **Identifies all conflicts** with specific file and line references
2. **Provides resolution recommendations** for each conflict
3. **Prioritizes fixes** by impact and urgency
4. **Includes validation checklist** showing what was checked
5. **Provides actionable next steps** for achieving 100% consistency

The goal is to achieve zero conflicting statements across the entire docs/ directory.
