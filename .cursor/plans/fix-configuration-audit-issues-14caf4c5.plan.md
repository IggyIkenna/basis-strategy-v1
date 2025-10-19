<!-- 14caf4c5-9dd7-48ac-8f23-0221170ac3dc 423853d9-d69d-48a1-af3c-a7e707fee027 -->
# Fix All Configuration Audit Issues

## Overview

Fix 200+ configuration violations identified by 8 quality gate scripts to achieve 100% test pass rate.

## Phase 1: Critical Configuration Fixes (Immediate)

### 1.1 Remove `asset` Field Completely

**Files to Update:**

- **Pydantic Models** (`backend/src/basis_strategy_v1/infrastructure/config/models.py`):
  - Remove `asset` field (line 65)
  - Remove `validate_asset` validator (lines 132-140)
  - Remove all asset validation logic in `validate_business_logic` (lines 220-233, 554)

- **All Strategy Files** (10 files):
  - `pure_lending_usdt_strategy.py`: Replace `self.asset` with `self.delta_tracking_asset` from risk monitor config
  - `pure_lending_eth_strategy.py`: Same replacement pattern
  - `btc_basis_strategy.py`: Update initialization and usage
  - `eth_basis_strategy.py`: Update initialization and usage
  - `eth_leveraged_strategy.py`: Update initialization and usage
  - `eth_staking_only_strategy.py`: Update initialization and usage
  - `usdt_eth_staking_hedged_leveraged_strategy.py`: Update initialization and usage
  - `usdt_eth_staking_hedged_simple_strategy.py`: Update initialization and usage
  - `ml_btc_directional_btc_margin_strategy.py`: Remove line 73, use risk monitor config
  - `ml_btc_directional_usdt_margin_strategy.py`: Remove line 96, use risk monitor config

- **Code Pattern**:
  ```python
  # OLD: self.asset = config.get('asset', 'ETH')
  # NEW:
  self.delta_tracking_asset = config.get('component_config', {}).get('risk_monitor', {}).get('delta_tracking_asset', 'ETH')
  ```

- **YAML Files**: Verify all 10 mode YAML files have `component_config.risk_monitor.delta_tracking_asset` defined

**Validation**: Run `python3 scripts/validate_config_alignment.py` - should have 0 asset field errors

### 1.2 Standardize `instrument_key` Terminology (52 instances)

**Replace all `position_key` with `instrument_key` in 14 files:**

- **Strategy files** (10 files - 31 instances):
  - Search and replace `position_key` → `instrument_key` in all strategy classes

- **Core model files** (4 files - 21 instances):
  - `backend/src/basis_strategy_v1/core/models/venues.py` (3 instances)
  - `backend/src/basis_strategy_v1/core/models/instruments.py` (7 instances)
  - `backend/src/basis_strategy_v1/core/models/venue_validation.py` (7 instances)
  - `backend/src/basis_strategy_v1/core/components/position_monitor.py` (2 instances)

**Canonical Format**: `venue:position_type:symbol` (variable name = `instrument_key`)

**Validation**: Run `python3 scripts/quality_gates/validate_position_key_format.py` - should have 0 position_key errors

### 1.3 Fix Invalid Position Type `LST` → `BaseToken`

**4 YAML files to update:**

- `configs/modes/eth_staking_only.yaml:104` - Change `etherfi:LST:weETH` → `etherfi:BaseToken:weETH`
- `configs/modes/eth_leveraged.yaml:76` - Change `etherfi:LST:weETH` → `etherfi:BaseToken:weETH`
- `configs/modes/usdt_eth_staking_hedged_simple.yaml:80` - Change `etherfi:LST:weETH` → `etherfi:BaseToken:weETH`
- `configs/modes/usdt_eth_staking_hedged_leveraged.yaml:90` - Change `etherfi:LST:weETH` → `etherfi:BaseToken:weETH`

**Validation**: Run `python3 scripts/quality_gates/validate_position_key_format.py` - should have 0 LST errors

### 1.4 Fix Component Initialization Failures

**Add `log_dir` parameter handling:**

- `backend/src/basis_strategy_v1/core/components/position_monitor.py`
- `backend/src/basis_strategy_v1/core/components/exposure_monitor.py`

Ensure both components handle `None` log_dir gracefully or provide defaults.

## Phase 2: Configuration Alignment (High Priority)

### 2.1 Add Orphaned Config Fields to Pydantic Models

**Update `backend/src/basis_strategy_v1/infrastructure/config/models.py`:**

**ML Config Fields** (add to `ModeConfig`):

```python
# In ml_config dict, document these optional fields:
# - signal_granularity: Optional[str]
# - sd_cap_bps: Optional[float]
# - take_profit_sd: Optional[float]
```

**Event Logger Fields** (add to `ModeConfig.event_logger` validation):

- `event_filtering.include_patterns: Optional[List[str]]`
- `logging_requirements.structured_logging: Optional[bool]`

**Execution Manager Fields** (add to `ExecutionManagerConfig`):

- `tight_loop_timeout: Optional[int]`

**Venue Config Fields** (add to `VenueConfig` - already has placeholders):

- Ensure `order_types`, `venue_type`, `enabled` are properly defined (they are at lines 428, 424, 385)

**Leverage and Strategy Fields** (add to `ModeConfig`):

- `leverage_enabled` already exists at line 82
- Ensure `hedge_allocation` in component_config.strategy_manager.position_calculation

**Risk Monitor Fields** (add to `RiskMonitorConfig`):

- `liquidation_threshold` already exists at line 303

### 2.2 Remove Orphaned/Legacy Config Fields

**Remove from YAML files and code:**

- `strategy_config.signal_threshold` - use `ml_config.signal_threshold` instead
- `delta_tolerance` at root level - use `component_config.risk_monitor.delta_tolerance`
- `event_logger.log_retention_policy.rotation_frequency` - remove entirely
- `component_config.strategy_manager.position_calculation.max_position_size` - remove
- `component_config.strategy_manager.position_calculation.take_profit_pct` - remove
- `component_config.results_store.leverage_tracking` - remove
- `component_config.results_store.pnl_attribution_types` - use `component_config.pnl_monitor.attribution_types`

**Replace in code:**

- `component_config.pnl_monitor.reporting_currency` → use `share_class` field instead

### 2.3 Add Hedge Allocation to Basis Strategies

**2 YAML files:**

- `configs/modes/btc_basis.yaml`
- `configs/modes/eth_basis.yaml`

Add under `component_config.strategy_manager.position_calculation`:

```yaml
hedge_allocation:
  binance: 0.4
  bybit: 0.3
  okx: 0.3
```

**Validation**: Run `python3 scripts/validate_config_alignment.py` - should have 0 orphaned field errors

## Phase 3: Component Signature Alignment

### 3.1 Update Component Specs with Init Parameters

**Add `pid` and `log_dir` to 6 component specs:**

- `docs/specs/01_POSITION_MONITOR.md`
- `docs/specs/02_EXPOSURE_MONITOR.md`
- `docs/specs/03_RISK_MONITOR.md`
- `docs/specs/04_PNL_MONITOR.md`
- `docs/specs/05_STRATEGY_MANAGER.md`
- `docs/specs/11_POSITION_UPDATE_HANDLER.md`

Update `__init__` signatures to include: `['self', 'config', 'data_provider', ..., 'correlation_id', 'pid', 'log_dir']`

### 3.2 Update Method Signatures to Include Timestamp

**54 method signature mismatches - update specs to match implementations:**

Priority methods to update in specs:

- `risk_monitor.assess_risk`: Add `timestamp` parameter
- `venue_interface_manager.route_to_venue`: Add `timestamp` parameter before `order`
- All data access methods: Ensure `timestamp` parameter is included

**Strategy**: Take union of spec and implementation signatures, prioritizing timestamp inclusion for better functionality.

**Validation**: Run `python3 scripts/test_component_signature_validation_quality_gates.py` - should have 0 signature mismatches

## Phase 4: Data Provider Access Pattern Fixes

### 4.1 Standardize Data Access in 4 Components

**Update these files to use standardized patterns:**

1. **`backend/src/basis_strategy_v1/core/components/pnl_monitor.py`**:

   - Replace direct `get_data()` calls
   - Use `utility_manager.get_price_for_instrument_key()` for market data
   - Use position interfaces for account data

2. **`backend/src/basis_strategy_v1/core/components/position_update_handler.py`**:

   - Replace direct `get_data()` calls
   - Use standardized utility manager methods

3. **`backend/src/basis_strategy_v1/core/strategies/ml_btc_directional_usdt_margin_strategy.py`**:

   - Replace direct data provider calls
   - Use utility manager for market data
   - Use position interfaces for positions/balances

4. **`backend/src/basis_strategy_v1/core/strategies/ml_btc_directional_btc_margin_strategy.py`**:

   - Same pattern as above

**Standard Patterns:**

```python
# Market data - use UtilityManager
price = self.utility_manager.get_price_for_instrument_key(instrument_key, timestamp, quote_currency='USD')
funding_rate = self.utility_manager.get_funding_rate(venue, symbol, timestamp)
oracle_price = self.utility_manager.get_oracle_price(token, quote_currency, timestamp)

# Position/Balance data - use Position Interfaces
balances = self.position_interface.get_balances(timestamp)
positions = self.position_interface.get_positions(timestamp)
```

**Validation**: Run `python3 scripts/test_data_provider_canonical_access_quality_gates_simple.py` - should pass

## Phase 5: Environment Variables

### 5.1 Dynamic Environment Variable Construction

**Update CEX API key access in venue interfaces:**

**Files to update:**

- `backend/src/basis_strategy_v1/core/venue_interfaces/*_interface.py` (for binance, bybit, okx)

**Pattern to implement:**

```python
def _get_api_credentials(self, venue: str) -> Dict[str, str]:
    environment = os.getenv('BASIS_ENVIRONMENT', 'dev').upper()
    api_key = os.getenv(f"BASIS_{environment}__CEX__{venue.upper()}_API_KEY")
    api_secret = os.getenv(f"BASIS_{environment}__CEX__{venue.upper()}_API_SECRET")
    passphrase = os.getenv(f"BASIS_{environment}__CEX__{venue.upper()}_PASSPHRASE")
    return {'api_key': api_key, 'api_secret': api_secret, 'passphrase': passphrase}
```

**Update documentation:**

- `docs/ENVIRONMENT_VARIABLES.md`: Add pattern documentation with examples for dev/staging/prod

### 5.2 Remove Unused Variables

Remove 56 unused variables from `docs/ENVIRONMENT_VARIABLES.md` documentation.

**Validation**: Run `python3 scripts/test_env_config_usage_sync_quality_gates.py` - should pass

## Phase 6: Architecture Cleanup

### 6.1 Fix Test Position Key Format

**Update 28 instances in test files:**

- `tests/e2e/test_usdt_market_neutral_quality_gates.py` (9 instances)
- `tests/e2e/test_usdt_market_neutral_e2e.py` (9 instances)
- `tests/e2e/test_eth_basis_quality_gates.py` (3 instances)
- `tests/e2e/test_eth_basis_e2e.py` (3 instances)

Replace dot notation with canonical format `venue:position_type:symbol`

### 6.2 Update Configuration Spec

**Update `docs/specs/19_CONFIGURATION.md`:**

- Remove `asset` field from documentation (line 90)
- Update config access patterns to use `component_config.risk_monitor.delta_tracking_asset`
- Document all newly added Pydantic fields

## Final Validation

### Run All Quality Gate Scripts:

```bash
# 1. Config alignment
python3 scripts/validate_config_alignment.py

# 2. Config loading
python3 scripts/test_config_loading_quality_gates.py

# 3. Position key format
python3 scripts/quality_gates/validate_position_key_format.py

# 4. Component signatures
python3 scripts/test_component_signature_validation_quality_gates.py

# 5. Data provider access
python3 scripts/test_data_provider_canonical_access_quality_gates_simple.py

# 6. Workflow architecture
python3 scripts/test_workflow_architecture_quality_gates.py

# 7. Risk monitor consolidation
python3 scripts/test_consolidate_duplicate_risk_monitors_quality_gates.py

# 8. Environment variables
python3 scripts/test_env_config_usage_sync_quality_gates.py
```

**Success Criteria**: All commands return exit code 0 with no errors.

## Implementation Notes

- Clean breaks with no backward compatibility (as per refactoring rules)
- Update all references when changing field names
- Run quality gates after each phase to validate progress
- Restart backend server before running quality gates

### To-dos

- [ ] Remove asset field from Pydantic models, validators, and update all 10 strategy files to use component_config.risk_monitor.delta_tracking_asset
- [ ] Replace all 52 instances of position_key with instrument_key across 14 files
- [ ] Change etherfi:LST:weETH to etherfi:BaseToken:weETH in 4 YAML files
- [ ] Fix position_monitor and exposure_monitor initialization to handle log_dir parameter
- [ ] Add orphaned config fields to Pydantic models (ML config, event logger, execution manager, etc.)
- [ ] Remove legacy config fields from YAML files and code (signal_threshold, delta_tolerance, etc.)
- [ ] Add hedge_allocation to btc_basis.yaml and eth_basis.yaml under component_config
- [ ] Update 6 component specs to include pid and log_dir in __init__ signatures
- [ ] Update method signatures in specs to include timestamp parameter (54 mismatches)
- [ ] Update 4 components to use standardized data access patterns (utility_manager and position_interface)
- [ ] Implement dynamic environment variable construction for CEX API keys in venue interfaces
- [ ] Update ENVIRONMENT_VARIABLES.md with dynamic pattern documentation and remove 56 unused variables
- [ ] Update 28 test instances to use canonical position key format instead of dot notation
- [ ] Update docs/specs/19_CONFIGURATION.md to remove asset field and document new patterns
- [ ] Run all 8 quality gate scripts and verify 100% pass rate with exit code 0