# FULL CONFIG LOADING & VALIDATION

## OVERVIEW
This task implements complete configuration loading from YAML files (modes/venues/share_classes) with full Pydantic validation and fail-fast behavior for missing or invalid configuration fields. This builds on the environment file switching to provide comprehensive configuration management.

**Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 33 (Fail-Fast Configuration)  
**Reference**: `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-040 (Fail-Fast Configuration)  
**Reference**: `docs/MODES.md` - Strategy mode configurations  
**Reference**: `configs/modes/` - Mode configuration files  
**Reference**: `configs/venues/` - Venue configuration files  
**Reference**: `configs/share_classes/` - Share class configuration files

## CRITICAL REQUIREMENTS

### 1. Complete YAML Configuration Loading
- **Mode configurations**: Load all files from `configs/modes/` directory
- **Venue configurations**: Load all files from `configs/venues/` directory  
- **Share class configurations**: Load all files from `configs/share_classes/` directory
- **Configuration merging**: Merge configurations based on dependencies and references
- **File validation**: Verify all YAML files are valid and parseable

### 2. Pydantic Model Validation
- **Schema enforcement**: All configuration must conform to Pydantic models
- **Type validation**: Validate all field types (str, int, float, bool, list, dict)
- **Range validation**: Validate numeric ranges where applicable
- **Enum validation**: Validate enum values where applicable
- **Required field validation**: Ensure all required fields are present

### 3. Fail-Fast Configuration Access
- **Direct access**: Use direct key access (config['key']) instead of .get() with defaults
- **Immediate failure**: Raise KeyError immediately if required configuration is missing
- **Clear error messages**: Provide specific error messages for missing or invalid configurations
- **Validation at startup**: Validate all configurations during application startup

### 4. Configuration Dependencies
- **Cross-references**: Validate references between mode, venue, and share class configurations
- **Dependency resolution**: Ensure all referenced configurations exist and are valid
- **Circular dependency detection**: Detect and prevent circular configuration dependencies
- **Dependency validation**: Validate that referenced configurations are compatible

## FORBIDDEN PRACTICES

### 1. Default Value Usage
- **No .get() with defaults**: Never use config.get('key', default_value) pattern
- **No fallback values**: Don't provide fallback values for missing configurations
- **No optional configurations**: All configurations should be required and validated

### 2. Partial Configuration Loading
- **No partial loading**: Don't load partial configurations if some files are missing
- **No graceful degradation**: Missing configurations must cause immediate failure
- **No warning-only validation**: Configuration errors must be fatal, not warnings

## REQUIRED IMPLEMENTATION

### 1. Configuration Loader
```python
# backend/src/basis_strategy_v1/core/config/config_loader.py
class ConfigLoader:
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = config_dir
        self.modes_dir = f"{config_dir}/modes"
        self.venues_dir = f"{config_dir}/venues"
        self.share_classes_dir = f"{config_dir}/share_classes"
    
    def load_all_configurations(self) -> dict:
        # 1. Load all mode configurations
        # 2. Load all venue configurations
        # 3. Load all share class configurations
        # 4. Validate all configurations with Pydantic models
        # 5. Resolve cross-references and dependencies
        # 6. Return validated configuration dict
```

### 2. Pydantic Models
```python
# backend/src/basis_strategy_v1/core/config/models.py
class ModeConfig(BaseModel):
    name: str
    strategy_type: str
    venues: List[str]
    share_class: str
    # ... other required fields

class VenueConfig(BaseModel):
    name: str
    type: str  # CEX, DeFi, etc.
    # ... other required fields

class ShareClassConfig(BaseModel):
    name: str
    asset: str
    # ... other required fields
```

### 3. Configuration Validation
- **Startup validation**: Validate all configurations during application startup
- **Runtime validation**: Validate configuration access patterns
- **Dependency validation**: Validate cross-references between configurations

## VALIDATION

### 1. Configuration File Loading
- **Test all files load**: Verify all YAML files in configs/ directories load correctly
- **Test invalid YAML**: Verify invalid YAML files cause appropriate failures
- **Test missing files**: Verify missing configuration files cause appropriate failures

### 2. Pydantic Validation
- **Test schema validation**: Verify all configurations conform to Pydantic models
- **Test type validation**: Verify type validation works for all field types
- **Test required fields**: Verify missing required fields cause validation failures

### 3. Cross-Reference Validation
- **Test dependency resolution**: Verify cross-references between configurations work
- **Test circular dependencies**: Verify circular dependencies are detected and prevented
- **Test invalid references**: Verify invalid references cause appropriate failures

## QUALITY GATES

### 1. Configuration Loading Quality Gate
```bash
# scripts/test_config_validation_quality_gates.py
def test_config_loading():
    # Test all configuration files load correctly
    # Test Pydantic validation works
    # Test cross-reference validation works
    # Test fail-fast behavior for missing/invalid configs
```

### 2. Integration Quality Gate
```bash
# Test configuration loading during backend startup
# Test configuration access patterns in components
# Test configuration validation in different environments
```

## SUCCESS CRITERIA

### 1. Complete Configuration Loading ✅
- [ ] All YAML files in configs/modes/ load correctly
- [ ] All YAML files in configs/venues/ load correctly
- [ ] All YAML files in configs/share_classes/ load correctly
- [ ] Configuration merging and cross-references work correctly

### 2. Pydantic Validation ✅
- [ ] All configurations conform to Pydantic models
- [ ] Type validation works for all field types
- [ ] Range and enum validation work where applicable
- [ ] Required field validation works correctly

### 3. Fail-Fast Behavior ✅
- [ ] Missing configurations cause immediate failure with clear error messages
- [ ] Invalid configurations cause immediate failure with clear error messages
- [ ] No .get() with defaults pattern used anywhere
- [ ] All configuration access uses direct key access

### 4. Integration ✅
- [ ] Configuration loading works during backend startup
- [ ] Configuration access works in all components
- [ ] Configuration validation works in all environments
- [ ] All quality gates pass

## QUALITY GATE SCRIPT

The quality gate script `scripts/test_config_validation_quality_gates.py` will:

1. **Test Configuration File Loading**
   - Verify all YAML files in configs/ directories load correctly
   - Verify invalid YAML files cause appropriate failures
   - Verify missing configuration files cause appropriate failures

2. **Test Pydantic Validation**
   - Verify all configurations conform to Pydantic models
   - Verify type validation works for all field types
   - Verify required field validation works

3. **Test Cross-Reference Validation**
   - Verify cross-references between configurations work
   - Verify circular dependencies are detected and prevented
   - Verify invalid references cause appropriate failures

4. **Test Fail-Fast Behavior**
   - Verify missing configurations cause immediate failure
   - Verify invalid configurations cause immediate failure
   - Verify no .get() with defaults pattern is used

**Expected Results**: All configurations load and validate correctly, fail-fast behavior works, no silent failures.
