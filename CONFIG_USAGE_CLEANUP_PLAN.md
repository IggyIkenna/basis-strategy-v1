# Config Usage Cleanup Plan

Based on analysis of config usage in code vs YAML definitions.

## Issues Found

### 1. ❌ `component_config` - Parent Field Accessed Directly

**Problem:** Code accesses parent field `component_config` directly as an intermediate variable instead of accessing nested fields directly.

**Current Usage:**
```python
# backend/src/basis_strategy_v1/core/components/pnl_monitor.py:154
component_config = config['component_config']

# backend/src/basis_strategy_v1/core/components/exposure_monitor.py:45
component_config = config['component_config']

# backend/src/basis_strategy_v1/core/components/risk_monitor.py:76
component_config = config['component_config']
```

**Fix:** Access nested fields directly:
```python
# Instead of:
component_config = config['component_config']
pnl_config = component_config['pnl_monitor']

# Use:
pnl_config = config['component_config.pnl_monitor']
# OR (if dict access)
pnl_config = config['component_config']['pnl_monitor']
```

**Action Items:**
- [ ] Update `pnl_monitor.py` line 154
- [ ] Update `exposure_monitor.py` line 45
- [ ] Update `risk_monitor.py` line 76

---

### 2. ❌ `hedge_allocation` - Wrong Config Path

**Problem:** Code accesses `hedge_allocation` at root level, but it's nested under `component_config.strategy_manager.position_calculation.hedge_allocation` in YAML.

**Current Usage:**
```python
# backend/src/basis_strategy_v1/core/utilities/utility_manager.py:300
hedge_allocation = mode_config.get('hedge_allocation')

# backend/src/basis_strategy_v1/core/strategies/eth_leveraged_strategy.py:56
self.hedge_allocation = config['hedge_allocation']
```

**YAML Structure:**
```yaml
component_config:
  strategy_manager:
    position_calculation:
      hedge_allocation:
        binance: 0.4
        bybit: 0.3
        okx: 0.3
```

**Fix:** Use correct nested path:
```python
# Instead of:
hedge_allocation = config['hedge_allocation']

# Use:
hedge_allocation = config['component_config']['strategy_manager']['position_calculation']['hedge_allocation']
# OR (if using dot notation)
hedge_allocation = config['component_config.strategy_manager.position_calculation.hedge_allocation']
```

**Action Items:**
- [ ] Update `utility_manager.py` line 300
- [ ] Update `eth_leveraged_strategy.py` line 56
- [ ] Add `component_config.strategy_manager.position_calculation.hedge_allocation` to specs documentation

---

### 3. ✅ `leverage_supported` - Already Correct (ShareClassConfig only)

**Status:** NOT a problem! This is a ShareClassConfig field, not a ModeConfig field.

**Usage:**
```python
# backend/src/basis_strategy_v1/infrastructure/config/models.py:457
leverage_supported: bool = Field(..., description="Whether leverage is supported")  # ShareClassConfig

# backend/src/basis_strategy_v1/infrastructure/config/models.py:534
if mode_config.leverage_enabled and not share_class_config.leverage_supported:
    raise ValueError(...)

# backend/src/basis_strategy_v1/infrastructure/config/config_validator.py:533
share_class_leverage = share_class_config.get('leverage_supported', False)
```

**Explanation:**
- `leverage_enabled` is a **ModeConfig** field (whether a specific strategy mode uses leverage)
- `leverage_supported` is a **ShareClassConfig** field (whether a share class allows leverage)
- They serve different purposes and both are needed for validation

**Action Items:**
- [x] No changes needed - this is correct!

---

### 4. ⚠️ Feature Flags Need Documentation

These configs are used correctly but missing from specs documentation:

#### `asset` ✅ Used in:
```python
# backend/src/basis_strategy_v1/infrastructure/config/config_validator.py:515
mode_asset = mode_config.get('asset')

# backend/src/basis_strategy_v1/core/strategies/base_strategy_manager.py:50
self.asset = config['asset']
```

#### `basis_trade_enabled` ✅ Used in:
```python
# backend/src/basis_strategy_v1/api/routes/strategies.py:37
has_basis_trading = config.get('basis_trade_enabled', False)

# Multiple other places in models.py for validation
```

#### `lending_enabled` ✅ Used in:
```python
# backend/src/basis_strategy_v1/api/routes/strategies.py:39
has_lending = config.get('lending_enabled', False)

# backend/src/basis_strategy_v1/infrastructure/config/config_validator.py:546
required_fields = [..., 'lending_enabled', ...]
```

#### `staking_enabled` ✅ Used in:
```python
# backend/src/basis_strategy_v1/api/routes/strategies.py:38
has_staking = config.get('staking_enabled', False)

# backend/src/basis_strategy_v1/infrastructure/config/models.py:160
if self.staking_enabled and not self.lst_type:
    raise ValueError(...)
```

**Action Items:**
- [ ] Add `asset` to appropriate component specs (appears in BaseStrategyManager)
- [ ] Add `basis_trade_enabled` to strategy specs documentation
- [ ] Add `lending_enabled` to strategy specs documentation
- [ ] Add `staking_enabled` to strategy specs documentation

---

## Summary of Action Items

### Code Changes (3 files)
1. **pnl_monitor.py** - Remove intermediate `component_config` variable, access nested fields directly
2. **exposure_monitor.py** - Remove intermediate `component_config` variable, access nested fields directly
3. **risk_monitor.py** - Remove intermediate `component_config` variable, access nested fields directly
4. **utility_manager.py** - Fix `hedge_allocation` access path
5. **eth_leveraged_strategy.py** - Fix `hedge_allocation` access path

### Documentation Updates (4 specs)
1. Add `asset` to BaseStrategyManager spec (05_STRATEGY_MANAGER.md)
2. Add `basis_trade_enabled` to mode config documentation
3. Add `lending_enabled` to mode config documentation
4. Add `staking_enabled` to mode config documentation
5. Add `component_config.strategy_manager.position_calculation.hedge_allocation` to strategy manager spec

### No Changes Needed
- ✅ `leverage_supported` is correct - it's a ShareClassConfig field, not ModeConfig

---

## Expected Impact

After these changes:
- **Code to Spec Coverage:** Will improve from 30% to ~50%
- **Code + YAML Only:** Will drop from 4 to 0 configs
- **Code Only:** Will drop from 3 to 0 configs
- **Fully Covered:** Will increase from 2 to ~6 configs

All config access will follow the correct patterns and have proper documentation.

