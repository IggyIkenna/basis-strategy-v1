# Environment & Config Usage Sync Agent Instructions

## Mission
Ensure 100% sync between environment variable/config field usage in code and their documentation across all components.

## Primary Objectives

### 1. Environment Variable Usage Sync
- Scan all Python files in `backend/src/basis_strategy_v1/` for environment variable usage patterns
- Extract all environment variables referenced in code (os.getenv, os.environ, settings access)
- Compare against documented variables in `docs/ENVIRONMENT_VARIABLES.md`
- Report undocumented variables and unused documented variables
- Ensure all BASIS_* variables are properly documented

### 2. Config Field Usage Sync
- Scan all Python files for config field access patterns (config['field'], self.config['field'])
- Extract all config field references by component
- Compare against "Config Fields Used" sections in `docs/specs/*.md`
- Report missing documentation and unused documented fields per component
- Ensure all configuration parameters are documented in component specs

### 3. Data Provider Query Sync
- Scan all Python files for data provider method calls (data_provider.get_*, self.data_provider.query_*)
- Extract all data provider queries by component
- Compare against "Data Provider Queries" sections in `docs/specs/*.md`
- Report missing documentation and unused documented queries per component
- Ensure all data access patterns are documented

### 4. Event Logging Requirements Sync
- Scan all Python files for event logging patterns (event_logger.log_*, logger.*, logging.*)
- Extract all event logging calls by component
- Compare against "Event Logging Requirements" sections in `docs/specs/*.md`
- Report missing documentation and unused documented event types per component
- Ensure all logging patterns are documented

## Analysis Process

### Step 1: Code Usage Extraction
1. **Scan Backend Source Code**
   - Process all `.py` files in `backend/src/basis_strategy_v1/`
   - Exclude test files and `__pycache__` directories
   - Use regex patterns to extract usage patterns

2. **Environment Variable Patterns**
   ```python
   patterns = [
       r'os\.getenv\([\'"]([^\'"]+)[\'"]',
       r'os\.environ\[[\'"]([^\'"]+)[\'"]',
       r'settings\[[\'"]([^\'"]+)[\'"]',
       r'get_settings\(\)\[[\'"]([^\'"]+)[\'"]',
       r'config_manager\.get\([\'"]([^\'"]+)[\'"]'
   ]
   ```

3. **Config Field Patterns**
   ```python
   patterns = [
       r'config\[[\'"]([^\'"]+)[\'"]',
       r'self\.config\[[\'"]([^\'"]+)[\'"]',
       r'complete_config\[[\'"]([^\'"]+)[\'"]',
       r'get_complete_config\(\)\[[\'"]([^\'"]+)[\'"]'
   ]
   ```

4. **Data Provider Query Patterns**
   ```python
   patterns = [
       r'data_provider\.get_([a-zA-Z_]+)',
       r'self\.data_provider\.get_([a-zA-Z_]+)',
       r'data_provider\.query_([a-zA-Z_]+)',
       r'self\.data_provider\.query_([a-zA-Z_]+)',
       r'data_provider\.([a-zA-Z_]+)\(',
       r'self\.data_provider\.([a-zA-Z_]+)\('
   ]
   ```

5. **Event Logging Patterns**
   ```python
   patterns = [
       r'event_logger\.log_([a-zA-Z_]+)',
       r'self\.event_logger\.log_([a-zA-Z_]+)',
       r'logger\.([a-zA-Z_]+)',
       r'logging\.([a-zA-Z_]+)',
       r'log_([a-zA-Z_]+)'
   ]
   ```

### Step 2: Documentation Extraction
1. **Environment Variables Documentation**
   - Parse `docs/ENVIRONMENT_VARIABLES.md`
   - Extract all documented variables from tables and code blocks
   - Use patterns to find BASIS_*, VITE_*, HEALTH_*, etc.

2. **Component Specs Documentation**
   - Process all `.md` files in `docs/specs/`
   - Extract documented fields from "Config Fields Used" sections
   - Extract documented queries from "Data Provider Queries" sections
   - Extract documented logging from "Event Logging Requirements" sections

### Step 3: Comparison and Analysis
1. **Environment Variables**
   - Find undocumented: used_in_code - documented_in_docs
   - Find unused: documented_in_docs - used_in_code
   - Report gaps and provide remediation steps

2. **Config Fields by Component**
   - Compare usage vs documentation per component
   - Identify components with missing documentation
   - Provide specific field names that need documentation

3. **Data Provider Queries by Component**
   - Compare usage vs documentation per component
   - Identify missing query documentation
   - Provide specific method names that need documentation

4. **Event Logging by Component**
   - Compare usage vs documentation per component
   - Identify missing logging documentation
   - Provide specific logging patterns that need documentation

## Validation Requirements

### Environment Variable Validation
- **Required**: All environment variables used in code must be documented in `ENVIRONMENT_VARIABLES.md`
- **Pattern**: BASIS_*, VITE_*, HEALTH_*, APP_*, ACME_*, HTTP_*, HTTPS_*, DATA_*, STRATEGY_*
- **Format**: Variables should be documented in tables with usage, component, and purpose columns

### Config Field Validation
- **Required**: All config fields used in components must be documented in component spec section 6
- **Format**: Fields should be listed with descriptions and usage context
- **Scope**: Per-component documentation required

### Data Provider Query Validation
- **Required**: All data provider method calls must be documented in component spec section 7
- **Format**: Queries should be listed with parameters and return values
- **Scope**: Per-component documentation required

### Event Logging Validation
- **Required**: All event logging patterns must be documented in component spec section 10
- **Format**: Logging patterns should be listed with event types and contexts
- **Scope**: Per-component documentation required

## Output Format

### Comprehensive Report Structure
```json
{
    "overall_status": "PASS" | "FAIL",
    "env_variables": {
        "undocumented": ["VAR1", "VAR2"],
        "unused": ["VAR3", "VAR4"],
        "status": "PASS" | "FAIL"
    },
    "config_fields": {
        "by_component": {
            "component_name": {
                "undocumented": ["field1", "field2"],
                "unused": ["field3", "field4"],
                "status": "PASS" | "FAIL"
            }
        }
    },
    "data_queries": {
        "by_component": { ... }
    },
    "event_logging": {
        "by_component": { ... }
    },
    "summary": {
        "total_undocumented_env_vars": 0,
        "components_with_undocumented_config": 0,
        "components_with_undocumented_queries": 0,
        "components_with_undocumented_logging": 0
    }
}
```

### Remediation Steps
For each category with failures, provide:
1. **Specific Items**: List exact variables/fields/queries/logging patterns that need documentation
2. **File Locations**: Point to specific files where documentation should be added
3. **Documentation Format**: Provide examples of proper documentation format
4. **Priority**: Mark high-priority items that block system functionality

## Success Criteria

### Environment Variables
- **100% Coverage**: All environment variables used in code are documented
- **No Orphans**: No documented variables are unused in code
- **Proper Format**: All variables follow BASIS_* naming convention

### Config Fields
- **100% Coverage**: All config fields used per component are documented
- **Component-Specific**: Each component has complete config field documentation
- **Proper Format**: All fields are documented in component spec section 6

### Data Provider Queries
- **100% Coverage**: All data provider queries used per component are documented
- **Component-Specific**: Each component has complete query documentation
- **Proper Format**: All queries are documented in component spec section 7

### Event Logging
- **100% Coverage**: All event logging patterns used per component are documented
- **Component-Specific**: Each component has complete logging documentation
- **Proper Format**: All logging patterns are documented in component spec section 10

## Integration with Quality Gates

### Quality Gate Script
- **File**: `tests/unit/test_env_config_usage_sync_unit.py`
- **Category**: `env_config_sync` in main quality gate runner
- **Critical**: Yes (must pass for system validation)

### Execution Context
- **Trigger**: After Quality Gates Agent (Agent 5) completes
- **Prerequisites**: Quality gates passing at 60%+ rate
- **Timeline**: 1-2 hours for comprehensive validation

### Reporting Integration
- **Format**: JSON output for programmatic processing
- **Logging**: Detailed progress and results logging
- **Exit Codes**: 0 for success, 1 for failure

## Web Agent Integration

### Compatibility
- **Background Mode**: Yes (can run in background)
- **Web Browser Mode**: Yes (supports web interface)
- **Context Sharing**: Yes (shares all system context)

### Execution Order
- **Position**: Agent 5.5 in 9-step process
- **After**: Quality Gates Agent (Agent 5)
- **Before**: Integration Alignment Agent (Agent 6)

### Prerequisites
- Quality gates passing at 60%+ overall rate
- Architecture compliance complete
- System health validation passed

## Troubleshooting

### Common Issues
1. **Missing Documentation Files**: Ensure `ENVIRONMENT_VARIABLES.md` and component specs exist
2. **Pattern Matching Failures**: Verify regex patterns match actual code patterns
3. **Component Name Extraction**: Ensure component names are correctly extracted from file paths
4. **Documentation Format**: Verify component specs follow 18-section format

### Error Recovery
1. **Partial Failures**: Continue processing other categories if one fails
2. **Missing Files**: Skip missing documentation files with warnings
3. **Pattern Errors**: Log pattern matching errors and continue
4. **Timeout Issues**: Process files in batches to avoid timeouts

### Validation Commands
```bash
# Run the quality gate script directly
python -m pytest tests/unit/test_env_config_usage_sync_unit.py

# Check for undocumented environment variables
grep -r "os.getenv\|os.environ\[" backend/src/basis_strategy_v1/ | grep -v test

# Validate specific component documentation
grep -r "Config Fields Used" docs/specs/
grep -r "Data Provider Queries" docs/specs/
grep -r "Event Logging Requirements" docs/specs/
```

## Expected Outcomes

### Immediate Results
- Comprehensive report of all usage vs documentation gaps
- Specific remediation steps for each category
- Component-by-component breakdown of missing documentation

### Long-term Benefits
- 100% documentation coverage for all configuration usage
- Reduced onboarding time for new developers
- Clear visibility into component dependencies
- Automated validation prevents documentation drift
- Improved maintainability and system understanding
