# ENVIRONMENT FILE SWITCHING & FAIL-FAST

## OVERVIEW
This task implements proper environment file switching with BASIS_ENVIRONMENT variable and fail-fast validation for missing environment files and required variables. This is the foundational infrastructure that enables proper deployment across dev/staging/prod environments.

**Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 6.1 (Infrastructure Configuration Elimination)  
**Reference**: `docs/ENVIRONMENT_VARIABLES.md` - Environment variable specifications  
**Reference**: `docs/IMPLEMENTATION_GAP_REPORT.md` - Component gap analysis  
**Reference**: `env.dev`, `env.staging`, `env.prod`, `env.unified` - Environment files

## CRITICAL REQUIREMENTS

### 1. Environment File Switching
- **BASIS_ENVIRONMENT variable**: Support dev/staging/prod switching
- **Environment-specific files**: `env.dev`, `env.staging`, `env.prod`
- **Fallback to unified**: Use `env.unified` as base with environment-specific overrides
- **Startup validation**: Verify environment file exists and is readable

### 2. Fail-Fast on Missing Environment Files
- **Immediate failure**: If environment file doesn't exist, fail with clear error message
- **File validation**: Check file permissions and readability
- **Environment detection**: Auto-detect environment if BASIS_ENVIRONMENT not set (default to dev)
- **Clear error messages**: Specify which environment file is missing and expected location

### 3. Required Environment Variables Validation
- **From env.unified**: All variables in env.unified must be present
- **Missing variable detection**: Fail immediately if any required variable is missing
- **Type validation**: Validate variable types (string, int, bool) where applicable
- **Format validation**: Validate formats (URLs, API keys, file paths) where applicable

### 4. Environment Variable Overrides
- **Override support**: Allow environment-specific files to override variables from env.unified
- **Override validation**: Ensure overrides maintain correct types and formats
- **Precedence order**: env.{environment} > env.unified > system environment variables
- **Override documentation**: Log which variables are being overridden

## FORBIDDEN PRACTICES

### 1. Silent Failures
- **No default values**: Never provide default values for missing environment variables
- **No graceful degradation**: Missing critical variables must cause immediate failure
- **No warnings only**: Missing variables must be errors, not warnings

### 2. Environment File Assumptions
- **No hardcoded paths**: Don't assume environment files are in specific locations
- **No missing file tolerance**: Don't continue if environment file is missing
- **No partial loading**: Don't load partial environment configurations

## REQUIRED IMPLEMENTATION

### 1. Environment Configuration System
- **Environment Loader**: Implement environment file loading with fail-fast validation
- **Variable Access**: Implement fail-fast environment variable access  
- **Startup Integration**: Integrate environment validation into application startup
- **Error Handling**: Implement comprehensive error handling for missing files/variables

**Implementation Details**: See `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 6.1 for complete implementation patterns and `docs/ENVIRONMENT_VARIABLES.md` for variable specifications.

### 2. Environment File Structure
- **env.unified**: Base environment variables (all environments)
- **env.dev**: Development overrides
- **env.staging**: Staging overrides  
- **env.prod**: Production overrides

### 3. Integration Points
- **Backend startup**: Integrate environment loading into backend startup sequence
- **Frontend build**: Use environment variables for frontend build process
- **Docker integration**: Support environment file mounting in containers

## VALIDATION

### 1. Environment File Existence
- **Test missing files**: Verify failure when environment files are missing
- **Test file permissions**: Verify failure when files are not readable
- **Test environment switching**: Verify correct file loading per BASIS_ENVIRONMENT

### 2. Variable Validation
- **Test missing variables**: Verify failure when required variables are missing
- **Test type validation**: Verify failure when variables have wrong types
- **Test format validation**: Verify failure when variables have invalid formats

### 3. Override Functionality
- **Test override precedence**: Verify environment-specific overrides work correctly
- **Test override validation**: Verify overrides maintain correct types
- **Test override logging**: Verify override actions are logged

## QUALITY GATES

### 1. Environment Switching Quality Gate
```bash
# scripts/test_environment_switching_quality_gates.py
def test_environment_switching():
    # Test dev environment loading
    # Test staging environment loading  
    # Test prod environment loading
    # Test missing environment file failure
    # Test missing variable failure
    # Test override functionality
```

### 2. Integration Quality Gate
```bash
# Test backend startup with different environments
# Test frontend build with different environments
# Test Docker container startup with environment files
```

## SUCCESS CRITERIA

### 1. Environment File Switching ✅
- [ ] BASIS_ENVIRONMENT variable controls environment file loading
- [ ] Environment-specific files (env.dev, env.staging, env.prod) are loaded correctly
- [ ] Fallback to env.unified works when environment-specific file is missing
- [ ] Environment detection works when BASIS_ENVIRONMENT is not set

### 2. Fail-Fast Validation ✅
- [ ] Missing environment files cause immediate failure with clear error messages
- [ ] Missing required variables cause immediate failure with clear error messages
- [ ] Invalid variable types/formats cause immediate failure with clear error messages
- [ ] No silent failures or default values for missing variables

### 3. Override Functionality ✅
- [ ] Environment-specific files can override variables from env.unified
- [ ] Override precedence is correct (env.{environment} > env.unified > system)
- [ ] Override validation maintains correct types and formats
- [ ] Override actions are logged for debugging

### 4. Integration ✅
- [ ] Backend startup works with environment file switching
- [ ] Frontend build process uses environment variables correctly
- [ ] Docker containers can mount and use environment files
- [ ] All quality gates pass

## QUALITY GATE SCRIPT

The quality gate script `scripts/test_environment_switching_quality_gates.py` will:

1. **Test Environment File Loading**
   - Verify each environment file loads correctly
   - Verify missing files cause appropriate failures
   - Verify file permission errors are handled

2. **Test Variable Validation**
   - Verify all required variables from env.unified are present
   - Verify missing variables cause immediate failure
   - Verify type and format validation works

3. **Test Override Functionality**
   - Verify environment-specific overrides work
   - Verify override precedence is correct
   - Verify override validation maintains types

4. **Test Integration**
   - Verify backend startup with different environments
   - Verify frontend build with environment variables
   - Verify Docker container startup

**Expected Results**: All tests pass, no silent failures, clear error messages for missing files/variables.
