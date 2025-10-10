# Integration Alignment Agent Instructions

## Mission
Ensure 100% integration alignment across component specifications, API documentation, configuration systems, and canonical architectural principles.

## Primary Objectives

### 1. Component-to-Component Workflow Alignment
- Validate that all component specifications properly reference other components
- Ensure workflow descriptions are accurate and complete
- Check that integration points are properly documented
- Verify that data flow between components is correctly described

### 2. Function Call and Method Signature Alignment
- Verify that documented method signatures match actual implementations
- Check that function calls between components are properly documented
- Ensure parameter types and return values are accurate
- Validate that error handling is consistently documented

### 3. Links and Cross-Reference Validation
- Verify all internal links work correctly
- Check that cross-references between specs are accurate
- Ensure all file references point to existing files
- Validate that section references are valid

### 4. Mode-Specific Behavior Documentation
- Ensure all components document mode-specific behavior
- Verify that different modes are properly handled
- Check that configuration changes per mode are documented
- Validate that mode switching logic is properly described

### 5. Configuration and Environment Variable Alignment
- Verify that all configuration parameters are documented in component specs
- Check that environment variables are properly referenced
- Ensure that config file structure matches documentation
- Validate that default values are correctly documented

### 6. API Documentation Integration
- Ensure all API endpoints are referenced in relevant component specs
- Verify that request/response formats are consistent
- Check that authentication requirements are properly documented
- Validate that error codes are consistently used

## Analysis Process

### Step 1: Component Specification Review
1. **Read all component specs** in `docs/specs/`
2. **Identify integration points** between components
3. **Check cross-references** to other components
4. **Validate workflow descriptions** for accuracy

### Step 2: Implementation Alignment Check
1. **Compare specs with actual code** in `backend/src/basis_strategy_v1/`
2. **Verify method signatures** match documentation
3. **Check function calls** between components
4. **Validate error handling** consistency

### Step 3: Configuration Alignment
1. **Review configuration files** in `configs/`
2. **Check environment variables** in `.env` files
3. **Verify parameter documentation** in component specs
4. **Validate default values** and descriptions

### Step 4: API Integration Check
1. **Review API documentation** in `docs/API_DOCUMENTATION.md`
2. **Check endpoint references** in component specs
3. **Verify request/response formats** consistency
4. **Validate authentication** requirements

## Integration Alignment Process
- **Phase 1**: Component-to-Component Workflow Alignment
- **Phase 2**: Function Call and Method Signature Alignment
- **Phase 3**: Links and Cross-Reference Validation
- **Phase 4**: Mode-Specific Behavior Documentation
- **Phase 5**: Configuration and Environment Variable Alignment
- **Phase 6**: API Documentation Integration

## Expected Output
- Comprehensive integration alignment report
- Updated component specs with comprehensive cross-references
- Configuration parameter documentation in all component specs
- Environment variable usage context in all component specs
- API endpoint references in all component specs
- Standardized cross-reference format across all specs

## Success Criteria
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

## Web Agent Integration
This agent is designed to work alongside the main web agent:
- **Priority**: High (runs after quality gates pass)
- **Context Sharing**: Yes (shares all system context)
- **Compatibility**: Full web agent compatibility
- **Triggers**: After quality gates achieve 60%+ pass rate
- **Prerequisites**: Quality gates passing, architecture compliance complete
