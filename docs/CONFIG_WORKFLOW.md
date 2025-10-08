# Configuration Workflow Guide 🔧

**Purpose**: Guide for managing configuration updates, validation, and system restarts  
**Updated**: October 5, 2025 - Configuration fixed and working

---

## ✅ **Current Configuration Status**

**Configuration System**: ✅ **FULLY FUNCTIONAL**
- Environment variables fixed (BASIS_ENVIRONMENT=dev)
- Strategy discovery working (configs/modes/ path fixed)
- All 6 strategies loading successfully
- Configuration validation passing
- Backend deployment working

## 🎯 **Configuration Architecture**

### **Centralized Loading**
- **Single Source**: `backend/src/basis_strategy_v1/infrastructure/config/`
- **Loaded Once**: At system startup
- **No Hot Reloading**: Changes require full restart

### **Configuration Hierarchy**
```
1. Environment Variables (BASIS_*) - Highest Priority
2. YAML Configuration Files (CURRENT IMPLEMENTATION):
   - Mode-Specific (configs/modes/*.yaml)
   - Venue-Specific (configs/venues/*.yaml)
   - Share Class (configs/share_classes/*.yaml)
   - Scenarios (configs/scenarios/*.yaml) - NOT YET IMPLEMENTED

3. JSON Hierarchy (DOCUMENTED BUT NOT IMPLEMENTED):
   - Environment-Specific Overrides (configs/{dev,staging,production}.json) - MISSING
   - Local Development Overrides (configs/local.json) - MISSING
   - Base Configuration (configs/default.json) - MISSING
```

### **Separation of Concerns**
- **YAML Configuration** (CURRENT): Mode, venue, and share class specific configurations
- **Environment Variables** (`BASIS_*`): Runtime configuration overrides
- **Deployment Configuration** (`deploy/.env*`): Caddy-specific deployment variables only
- **JSON Hierarchy** (NOT IMPLEMENTED): Base, environment, and local configuration files

---

## 🔄 **Configuration Update Workflow**

### **Step 1: Make Changes**

**Environment Variables** (`backend/env.unified`):
```bash
BASIS_ENVIRONMENT=dev
BASIS_DEV__ALCHEMY__PRIVATE_KEY=your_key
BASIS_DEV__CEX__BINANCE_SPOT_API_KEY=your_key
```

**Environment-Specific Configuration** (`configs/staging.json`):
```json
{
  "environment": "staging",
  "debug": false,
  "api": {
    "port": 8001,
    "cors_origins": ["https://defi-project-uat.odum-research.com"]
  },
  "database": {
    "type": "postgresql",
    "url": "postgresql://basis_strategy_v1:password@postgres:5432/basis_strategy_v1"
  }
}
```

**Local Development Overrides** (`configs/local.json`):
```json
{
  "environment": "dev",
  "debug": true,
  "api": {
    "port": 8000,
    "cors_origins": ["http://localhost:5173"]
  },
  "redis": {
    "url": "redis://localhost:6379/0"
  }
}
```

**Mode Configuration** (`configs/modes/usdt_market_neutral.yaml`):
```yaml
mode: "usdt_market_neutral"
target_apy: 0.15
max_drawdown: 0.04
leverage_enabled: true
target_ltv: 0.91
```

**Venue Configuration** (`configs/venues/aave_v3.yaml`):
```yaml
venue: "aave_v3"
network: "ethereum"
liquidation_threshold: 0.95  # E-mode for weETH/WETH
```

### **Step 2: Validate**

**Automatic Validation** (at startup):
```bash
python -m pytest tests/unit/config/test_config_validation.py -v
```

**Manual Validation**:
```python
from basis_strategy_v1.infrastructure.config.config_validator import validate_configuration

result = validate_configuration()
if not result.is_valid:
    print(f"Validation failed: {result.errors}")
```

### **Step 3: Restart System**

**Full restart required**:
```bash
# Stop all services
./deploy/stop-local.sh

# Start all services (config reloaded)
./deploy/deploy-local.sh
```

**Why restart needed**:
- Environment variables loaded at startup
- Configuration cached for performance
- Component health checks require re-read

---

## 🏗️ **Configuration Infrastructure**

### **ConfigLoader** (`config_loader.py`)
- Loads all YAML and JSON configs
- Caching, environment overrides, deep merging
- Usage: `get_config_loader().get_complete_config(mode=mode)`

### **ConfigValidator** (`config_validator.py`)
- Validates at startup
- Business logic validation
- Usage: `validate_configuration()`

### **HealthChecker** (`health_check.py`)
- Component health monitoring
- Usage: `register_component()`, `mark_component_healthy()`

### **Settings** (`settings.py`)
- Legacy compatibility layer
- Usage: `get_settings()`, `get_setting(key_path)`

### **Integration Pattern**:
```python
from ...infrastructure.config.config_loader import get_config_loader
from ...infrastructure.config.health_check import register_component

# Load config
config_loader = get_config_loader()
config = config_loader.get_complete_config(mode=mode)

# Register component
register_component('strategy_manager', ['data_provider', 'risk_monitor'])

# Use config (fail-fast, no .get() patterns)
lst_type = config['lst_type']  # Raises KeyError if missing
```

---

## 🏥 **Health Monitoring**

### **Check System Health**:
```python
from basis_strategy_v1.infrastructure.config.health_check import is_system_healthy

if is_system_healthy():
    print("✅ All components healthy")
else:
    print("❌ System unhealthy")
```

### **Health Check API**:
```bash
curl http://localhost:8001/health/config
```

---

## 🔍 **Configuration Validation**

### **Validation Levels**:
1. **File Structure**: Required files exist, syntax valid
2. **Environment Variables**: Required vars set, no placeholders
3. **Business Logic**: Leverage consistent, venues match allocations
4. **Component Health**: All components registered and healthy

### **Common Errors**:
```bash
# Missing environment variable
❌ Missing: BASIS_DEV__ALCHEMY__PRIVATE_KEY

# Invalid JSON
❌ Invalid default.json: Expecting ',' at line 5

# Business logic issue
#TODO: add example as ltv more useful anymore 

# Component not initialized
❌ Component strategy_manager not initialized
```

---

## 📁 **Configuration Files**

### **Mode Configs** (`configs/modes/*.yaml` - 6 modes):
- `pure_lending.yaml` - USDT lending only
- `btc_basis.yaml` - BTC basis trading
- `eth_leveraged.yaml` - ETH leveraged staking
- `eth_staking_only.yaml` - ETH staking without leverage
- `usdt_market_neutral.yaml` - USDT market-neutral (full complexity)
- `usdt_market_neutral_no_leverage.yaml` - USDT market-neutral without leverage

**Key fields**: `mode`, `share_class`, `asset`, `lst_type`, `rewards_mode`, `target_apy`, `max_drawdown`, `leverage_enabled`, `target_ltv`

### **Share Class Configs** (`configs/share_classes/*.yaml` - 2 classes):
- `usdt_stable.yaml` - USDT stablecoin share class
- `eth_directional.yaml` - ETH directional share class

**Key fields**: `share_class`, `type`, `base_currency`, `market_neutral`, `supported_strategies`

### **Venue Configs** (`configs/venues/*.yaml` - 8 venues):
- `aave_v3.yaml` - AAVE V3 lending
- `alchemy.yaml` - Alchemy RPC
- `binance.yaml` - Binance CEX
- `bybit.yaml` - Bybit CEX
- `etherfi.yaml` - EtherFi staking
- `lido.yaml` - Lido staking
- `morpho.yaml` - Morpho lending
- `okx.yaml` - OKX CEX

---

## 🚨 **Best Practices**

### **Environment Management**:

**dev**:
```bash
BASIS_ENVIRONMENT=dev
BASIS_DEV__ALCHEMY__NETWORK=sepolia  # Testnet
```

**Staging**:
```bash
BASIS_ENVIRONMENT=staging
BASIS_STAGING__ALCHEMY__NETWORK=mainnet  # Mainnet, small amounts
```

**Production**:
```bash
BASIS_ENVIRONMENT=production
BASIS_PROD__ALCHEMY__NETWORK=mainnet  # Mainnet, full amounts
```

### **Configuration Testing**:
```bash
# Test validation
pytest tests/unit/config/test_config_validation.py -v

# Test loading
pytest tests/unit/config/test_config_loader.py -v

# Test health
pytest tests/unit/config/test_health_check.py -v
```

---

## 🔧 **Troubleshooting**

### **Configuration Not Loading**:
1. Check file paths correct
2. Verify JSON/YAML syntax
3. Ensure required files exist
4. Check file permissions

### **Environment Variables Not Set**:
1. Check `backend/env.unified` exists
2. Verify variable names
3. Replace placeholder values
4. Restart after changes

### **Component Not Healthy**:
1. Check component registration
2. Verify component reads config
3. Check dependencies satisfied
4. Review error messages

### **Debugging Commands**:
```bash
# Validate config
python -c "from basis_strategy_v1.infrastructure.config.config_validator import validate_configuration; print(validate_configuration())"

# Check health
python -c "from basis_strategy_v1.infrastructure.config.health_check import get_health_summary; print(get_health_summary())"

# List env vars
env | grep BASIS_
```

---

## 📊 **Configuration Field Categories**

### **Fields from Data** (Not in mode configs):
- `max_ltv` - From `data/protocol_data/aave/risk_params/aave_v3_risk_parameters.json` (0.93 for E-mode)
- `liquidation_threshold` - From same file (0.95 for E-mode)
- `liquidation_bonus` - From same file (0.01 for E-mode)

**Rationale**: Protocol parameters from data (updatable without code changes)

### **Fields Dynamically Calculated**:
- `ltv_target` = `max_ltv × (1 - max_stake_spread_move)`
- Example: `0.93 × (1 - 0.02215) = 0.9094`

### **Mode Configuration Fields**:

**Core Strategy**:
- `mode`, `share_class`, `asset`, `lst_type`, `rewards_mode`
- `lending_enabled`, `staking_enabled`, `basis_trade_enabled`, `leverage_enabled`

**Execution**:
- `use_flash_loan`, `unwind_mode`, `max_leverage_loops`, `min_loop_position_usd`

**Hedging** (market-neutral modes):
- `hedge_venues`, `hedge_allocation`

**Risk**:
- `margin_ratio_target`, `max_stake_spread_move`

**Performance**:
- `target_apy`, `max_drawdown`

**For complete field listing**: See mode YAML files

---

## 📋 **Checklist**

### **Before Changes**:
- [ ] Backup current configuration
- [ ] Understand impact
- [ ] Plan restart window
- [ ] Test in dev first

### **After Changes**:
- [ ] Validate syntax
- [ ] Check environment variables
- [ ] Verify business logic
- [ ] Restart system
- [ ] Check component health
- [ ] Run config tests
- [ ] Monitor behavior

### **Production Deployment**:
- [ ] Test in staging
- [ ] Validate all configs
- [ ] Check environment variables
- [ ] Plan maintenance window
- [ ] Backup production config
- [ ] Deploy with monitoring
- [ ] Verify system health
- [ ] Monitor for issues

---

## 🎯 **Summary**

**Key Points**:
1. Configuration is centralized
2. Changes require restart
3. Validation is comprehensive
4. Health monitoring built-in
5. Testing required

**Workflow**:
1. Make changes to config/env files
2. Validate configuration
3. Restart system
4. Check health
5. Monitor system

---

**Remember**: Configuration changes require full system restart! 🔄

*Last Updated: October 3, 2025*
