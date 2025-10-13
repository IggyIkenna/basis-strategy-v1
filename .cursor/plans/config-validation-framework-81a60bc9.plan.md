<!-- 81a60bc9-90c7-42c1-84a0-c4a41b06ffee 68a7c57b-e82f-4112-80eb-043f94983732 -->
# Config Validation Quality Gates Framework Implementation

## Overview

Transform the broken config validation system into a robust, comprehensive framework that validates configuration, environment variables, and data integrity before deployment. Integrate quality gates into both platform.sh and docker/deploy.sh build processes.

## Phase 1: Fix Critical Validation Script Bugs (IMMEDIATE)

### 1.1 Fix validate_config_alignment.py Bugs

**File**: `scripts/validate_config_alignment.py`

**Issues to Fix**:

1. **Pydantic Deprecation** (lines 69-71): Replace `__fields__` with `model_fields`
2. **ConfigSchema Undefined** (line 456): Remove or define ConfigSchema validation
3. **Wildcard Generation Debug**: Debug why wildcards (`component_config.*`, `venues.*`) aren't being applied in main execution

**Changes**:

```python
# Line 69-71: Fix Pydantic v2 compatibility
if hasattr(model_class, '__fields__'):  # DELETE
    for field_name, field_info in model_class.__fields__.items():  # DELETE
# Replace with:
if hasattr(model_class, 'model_fields'):
    for field_name, field_info in model_class.model_fields.items():

# Lines 498-526: Remove broken ConfigSchema validation section
# Either define ConfigSchema or remove the entire validate_pydantic_validation method
```

**Expected Result**: Orphaned fields drop from 329 to <20 legitimate issues

### 1.2 Test Fixed Validation

```bash
python3 scripts/validate_config_alignment.py
# Should show mostly PASS results with <20 real orphaned fields
```

## Phase 2: Enhance Quality Gate Framework (HIGH PRIORITY)

### 2.1 Add "Config Fields Used" Sections to Component Specs

**Files**: All 23 component specs in `docs/specs/*.md`

**Template to Add**:

```markdown
## Config Fields Used

### Mode-Specific Config
- **target_apy**: Target annual percentage yield for strategy
- **max_drawdown**: Maximum allowable drawdown percentage
- **lending_enabled**: Whether lending is enabled

### Component-Specific Config  
- **component_config.position_monitor.balance_tracking**: Enable balance tracking
- **component_config.position_monitor.update_frequency**: Position update frequency
```

**Components to Update** (from glob search):

- 01_POSITION_MONITOR.md
- 02_EXPOSURE_MONITOR.md
- 03_RISK_MONITOR.md
- 04_PNL_CALCULATOR.md
- 05_STRATEGY_MANAGER.md
- 06_EXECUTION_MANAGER.md
- 07_EXECUTION_INTERFACE_MANAGER.md
- 07B_EXECUTION_INTERFACES.md
- 07C_EXECUTION_INTERFACE_FACTORY.md
- 08_EVENT_LOGGER.md
- 09_DATA_PROVIDER.md
- 10_RECONCILIATION_COMPONENT.md
- 11_POSITION_UPDATE_HANDLER.md
- 12_FRONTEND_SPEC.md
- 13_BACKTEST_SERVICE.md
- 14_LIVE_TRADING_SERVICE.md
- 15_EVENT_DRIVEN_STRATEGY_ENGINE.md
- 16_MATH_UTILITIES.md
- 17_HEALTH_ERROR_SYSTEMS.md
- 18_RESULTS_STORE.md
- 19_CONFIGURATION.md
- 5A_STRATEGY_FACTORY.md
- 5B_BASE_STRATEGY_MANAGER.md

### 2.2 Create Documentation Sync Validator

**New File**: `scripts/test_config_documentation_sync_quality_gates.py`

**Purpose**: Ensure every config in `docs/specs/19_CONFIGURATION.md` appears in component specs

**Validation Logic**:

```python
def validate_config_documentation_sync():
    # 1. Extract all configs from 19_CONFIGURATION.md
    # 2. Extract all "Config Fields Used" from component specs
    # 3. Check bidirectional sync:
    #    - Every config in 19_CONFIGURATION.md → used in at least one component spec
    #    - Every config in component specs → documented in 19_CONFIGURATION.md
    # 4. Report orphaned references
```

### 2.3 Create Config Usage Validator

**New File**: `scripts/test_config_usage_sync_quality_gates.py`

**Purpose**: Ensure every config in mode YAML files is documented

**Validation Logic**:

```python
def validate_config_usage_sync():
    # 1. Load all 9 mode configs (btc_basis.yaml, eth_basis.yaml, etc.)
    # 2. Extract all config fields from YAML files
    # 3. Check against 19_CONFIGURATION.md:
    #    - Every YAML field → documented in 19_CONFIGURATION.md
    #    - Every documented field → used in at least one mode YAML
    # 4. Report undocumented/unused configs
```

## Phase 3: Business Logic & Strategy Validation (MEDIUM PRIORITY)

### 3.1 Enhance Pydantic Business Logic Validation

**File**: `backend/src/basis_strategy_v1/infrastructure/config/models.py`

**Current Validators** (lines 126-167):

- Leverage → borrowing validation
- Staking → lst_type validation
- Basis trading → hedge_venues validation

**New Validators to Add**:

```python
@model_validator(mode='after')
def validate_business_logic(self):
    # Existing validations...
    
    # NEW: Venue-LST validation
    if self.staking_enabled and self.lst_type and self.venues:
        expected_venue = "etherfi" if self.lst_type == "weeth" else "lido"
        if expected_venue not in self.venues:
            raise ValueError(f"lst_type '{self.lst_type}' requires venue '{expected_venue}'")
    
    # NEW: Share class consistency
    if 'usdt' in self.mode.lower() and self.asset != 'USDT':
        raise ValueError(f"USDT mode should use USDT asset, not {self.asset}")
    
    # NEW: Risk parameter alignment
    if self.max_drawdown and self.max_drawdown > 0.5:
        logger.warning(f"Mode {self.mode}: High max_drawdown {self.max_drawdown}")
    
    return self
```

### 3.2 Create Strategy Intention Validator

**New File**: `scripts/test_modes_intention_quality_gates.py`

**Purpose**: Validate mode configs match MODES.md strategy descriptions

**Validation Examples**:

- Pure lending → only AAVE venues
- Basis strategies → CEX venues + Alchemy
- Market neutral → both DeFi and CEX
- ML strategies → only CEX venues

### 3.3 Create Config Loading Test

**New File**: `scripts/test_config_loading_quality_gates.py`

**Purpose**: Test all 9 mode configs load and validate at startup

**Test Logic**:

```python
def test_all_configs_load():
    modes = ['pure_lending', 'btc_basis', 'eth_basis', 'eth_leveraged',
             'eth_staking_only', 'usdt_market_neutral', 
             'usdt_market_neutral_no_leverage', 'ml_btc_directional', 
             'ml_usdt_directional']
    
    for mode in modes:
        config = load_mode_config(mode)
        validate_mode_config(config, mode)  # Pydantic validation
        assert config is not None
```

## Phase 4: CI/CD Integration (CRITICAL)

### 4.1 Integrate Quality Gates into platform.sh

**File**: `platform.sh`

**Add Quality Gate Check Function** (after load_environment function, ~line 150):

```bash
run_quality_gates() {
    echo -e "${BLUE}🚦 Running quality gates...${NC}"
    
    # Run configuration validation
    python3 scripts/validate_config_alignment.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Configuration validation failed${NC}"
        return 1
    fi
    
    # Run environment variable validation
    python3 scripts/test_env_config_usage_sync_quality_gates.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Environment variable validation failed${NC}"
        return 1
    fi
    
    # Run data validation
    python3 scripts/test_data_availability_quality_gates.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Data validation failed${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ All quality gates passed${NC}"
    return 0
}
```

**Integrate into start_backend function** (around line 200):

```bash
start_backend() {
    echo -e "${BLUE}🚀 Starting backend...${NC}"
    
    create_directories
    load_environment
    
    # NEW: Run quality gates before starting
    run_quality_gates
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Quality gates failed. Aborting startup.${NC}"
        exit 1
    fi
    
    # ... rest of start_backend logic
}
```

### 4.2 Integrate Quality Gates into docker/deploy.sh

**File**: `docker/deploy.sh`

**Add Quality Gate Check Function** (after validate_deployment_config, ~line 194):

```bash
run_quality_gates() {
    echo -e "${BLUE}🚦 Running quality gates...${NC}"
    
    # Change to project root (docker/deploy.sh runs in docker/ dir)
    cd ..
    
    # Run configuration validation
    python3 scripts/validate_config_alignment.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Configuration validation failed${NC}"
        return 1
    fi
    
    # Run environment variable validation
    python3 scripts/test_env_config_usage_sync_quality_gates.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Environment variable validation failed${NC}"
        return 1
    fi
    
    # Run data validation
    python3 scripts/test_data_availability_quality_gates.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Data validation failed${NC}"
        return 1
    fi
    
    # Return to docker directory
    cd docker
    
    echo -e "${GREEN}✅ All quality gates passed${NC}"
    return 0
}
```

**Integrate into start_services function** (around line 135):

```bash
start_services() {
    echo -e "${BLUE}🚀 Starting $SERVICES services in $ENVIRONMENT environment...${NC}"
    
    setup_environment
    validate_deployment_config
    
    # NEW: Run quality gates before building
    run_quality_gates
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Quality gates failed. Aborting deployment.${NC}"
        exit 1
    fi
    
    # ... rest of start_services logic
}
```

### 4.3 Update run_quality_gates.py Integration

**File**: `scripts/run_quality_gates.py`

**Update configuration category** (lines 60-67):

```python
'configuration': {
    'description': 'Configuration Validation',
    'scripts': [
        'validate_config_alignment.py',              # Fixed
        'test_config_documentation_sync_quality_gates.py',  # New
        'test_config_usage_sync_quality_gates.py',   # New  
        'test_modes_intention_quality_gates.py',     # New
        'test_config_loading_quality_gates.py'       # New
    ],
    'critical': True
}
```

## Phase 5: Documentation Updates (CRITICAL)

### 5.1 Update QUALITY_GATES.md

**File**: `docs/QUALITY_GATES.md`

**Sections to Update**:

1. **Quality Gate Categories** (line 61): Add new configuration scripts
2. **Configuration Validation** section (lines 151-157): Update status and script list
3. **Critical Issues** section (lines 194-218): Update with fixed validation status
4. **Action Items** section (lines 332-350): Update with new validation framework

**New Content to Add**:

```markdown
### Configuration Validation Framework

The configuration validation framework ensures complete alignment between:
- **Mode Configs** (configs/modes/*.yaml) ↔ Pydantic models
- **Venue Configs** (configs/venues/*.yaml) ↔ Pydantic models
- **Component Specs** (docs/specs/*.md) ↔ Configuration documentation
- **Environment Variables** (env.unified + overrides) ↔ Documentation

#### Validation Scripts

1. **validate_config_alignment.py** - Validates Pydantic model alignment
2. **test_config_documentation_sync_quality_gates.py** - Validates component spec sync
3. **test_config_usage_sync_quality_gates.py** - Validates mode YAML usage
4. **test_modes_intention_quality_gates.py** - Validates strategy intentions
5. **test_config_loading_quality_gates.py** - Validates config loading

#### CI/CD Integration

Configuration quality gates run automatically in:
- **platform.sh**: Before every backend start
- **docker/deploy.sh**: Before every Docker deployment

Builds fail immediately if any validation fails.
```

### 5.2 Update DEPLOYMENT_GUIDE.md

**File**: `docs/DEPLOYMENT_GUIDE.md`

**Section to Add** (after "🏗️ Architecture Overview", ~line 80):

```markdown

### Quality Gates Integration

Both platform.sh and docker/deploy.sh automatically validate configuration, environment variables, and data before deployment:

**Validation Steps**:

1. **Configuration Validation**: Ensures all mode configs align with Pydantic models
2. **Environment Variable Validation**: Ensures all env vars are documented and used
3. **Data Validation**: Ensures all required data files exist and are valid

**Quality Gate Scripts**:

- `scripts/validate_config_alignment.py` - Config/model alignment
- `scripts/test_env_config_usage_sync_quality_gates.py` - Env var sync
- `scripts/test_data_availability_quality_gates.py` - Data availability

### To-dos

- [ ] Fix validate_config_alignment.py: Pydantic deprecation, ConfigSchema undefined, wildcard matching debug
- [ ] Add 'Config Fields Used' sections to all 23 component specs in docs/specs/
- [ ] Create test_config_documentation_sync_quality_gates.py for component spec sync validation
- [ ] Create test_config_usage_sync_quality_gates.py for mode YAML usage validation
- [ ] Enhance Pydantic business logic validation in config/models.py (venue-LST, share class, risk params)
- [ ] Create test_modes_intention_quality_gates.py for strategy intention validation
- [ ] Create test_config_loading_quality_gates.py to test all 9 mode configs load successfully
- [ ] Add run_quality_gates() function to platform.sh and integrate into start_backend()
- [ ] Add run_quality_gates() function to docker/deploy.sh and integrate into start_services()
- [ ] Update run_quality_gates.py configuration category with all 5 new validation scripts
- [ ] Update QUALITY_GATES.md with new config validation framework and CI/CD integration
- [ ] Update DEPLOYMENT_GUIDE.md with quality gates integration section and updated checklist
- [ ] Add Configuration Validation Architecture section to REFERENCE_ARCHITECTURE_CANONICAL.md
- [ ] Test fixed validate_config_alignment.py shows <20 orphaned fields
- [ ] Test all 4 new quality gate scripts individually
- [ ] Test quality gates run in platform.sh and docker/deploy.sh builds
- [ ] Verify all documentation updates are complete and accurate