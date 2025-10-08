# Config Alignment Analysis Report

## Overview
This document provides a detailed analysis of the misalignment between configuration files in `configs/` and Pydantic models in `config_models.py`. The analysis reveals significant gaps that need to be addressed.

## Summary Statistics (Current State - After Environment Restructuring)
- **Total unique config fields**: 169 (reduced from 259)
- **Total unique model fields**: 63 (unchanged)
- **Coverage**: 14.8% (improved from 12.4%)
- **Orphaned config fields**: 144 (reduced from 227)
- **Orphaned model fields**: 38 (increased from 31)
- **Modes with extra fields**: 6 out of 6 modes (unchanged)
- **Modes missing from MODE_REQUIREMENTS**: 0 (unchanged)

### **Environment Variable Restructuring Completed**
- **Environment variables trimmed** to only essential startup and sensitive info
- **Non-sensitive venue data** moved to `configs/venues/*.yaml`
- **Infrastructure settings** moved to `configs/default.json`
- **Share class strategy validation** added to config validator

## Detailed Misalignment Analysis

### 1. Orphaned Config Fields (227 fields in configs but not in Pydantic models)

#### **High Priority - Core Infrastructure Fields**
```
monitoring.*
- monitoring.log_format
- monitoring.health_check_interval
- monitoring.alert_thresholds.drawdown_warning
- monitoring.alert_thresholds.drawdown_critical
- monitoring.position_check_interval
- monitoring.risk_check_interval

api.*
- api.host
- api.port
- api.cors_origins

contracts.*
- contracts.mainnet.rewards_distributor
- contracts.mainnet.lending_pool
- contracts.mainnet.data_provider
- contracts.mainnet.oracle
- contracts.sepolia.lending_pool
- contracts.sepolia.data_provider
- contracts.sepolia.oracle

health.*
- health.check_interval_seconds
- health.component_timeout_seconds
- health.unhealthy_threshold

database.*
- database.type
- database.url
- database.host
- database.port
- database.user
- database.password
- database.name
- database.pool_size
- database.echo

cache.*
- cache.type
- cache.redis_url
- cache.ttl.default
- cache.ttl.results
- cache.ttl.market_data

redis.*
- redis.enabled
- redis.url
- redis.session_ttl
- redis.cache_ttl

storage.*
- storage.type
- storage.path
```

#### **Medium Priority - Data and Execution Fields**
```
data.*
- data.provider
- data.data_dir
- data.cache_enabled
- data.interpolation_method
- data.forward_fill_limit
- data.validation_mode

execution_costs.*
- execution_costs.model
- execution_costs.data_path
- execution_costs.fail_if_missing

fees.*
- fees._comment
- fees.bybit_maker_fee_bps
- fees.bybit_taker_fee_bps
- fees.bybit_withdrawal_fee_bps
- fees.binance_maker_fee_bps
- fees.binance_taker_fee_bps
- fees.binance_withdrawal_fee_bps
- fees.okx_maker_fee_bps
- fees.okx_taker_fee_bps
- fees.okx_withdrawal_fee_bps
- fees.aave_deposit_fee_bps
- fees.aave_withdraw_fee_bps

protocol_fees.*
- protocol_fees.flash_loan_fee
- protocol_fees.reserve_factor

trading_fees.*
- trading_fees.spot_maker
- trading_fees.spot_taker
- trading_fees.futures_maker
- trading_fees.futures_taker

flash_loans.*
- flash_loans.fee_rate
- flash_loans.min_loan_amount

supported_assets.*
- supported_assets.supply
- supported_assets.borrow

staking.*
- staking.unstaking_period
- staking.rewards_distributor

gas_limits.*
- gas_limits.supply
- gas_limits.borrow
- gas_limits.repay
- gas_limits.flash_loan

api_endpoints.*
- api_endpoints.spot
- api_endpoints.futures

contract_addresses.*
- contract_addresses.mainnet.lending_pool
- contract_addresses.mainnet.data_provider
- contract_addresses.mainnet.oracle
- contract_addresses.sepolia.lending_pool
- contract_addresses.sepolia.data_provider
- contract_addresses.sepolia.oracle

rpc.*
- rpc.primary_endpoint
- rpc.fallback_endpoints
- rpc.timeout_seconds
- rpc.retry_count

network.*
- network.ethereum
- network.sepolia

integration.*
- integration.gas_price_multiplier
- integration.gas_limit
- integration.max_slippage

rate_limits.*
- rate_limits.requests_per_second
- rate_limits.requests_per_minute

features.*
- features.enhanced_apis
- features.block_trace_support
- features.transaction_simulation

output.*
- output._comment
- output.generate_cumulative_return_chart
- output.generate_strategy_allocation_chart
- output.generate_venue_balance_chart

premium.*
- premium.enhanced_trace_api
```

#### **Low Priority - Mode-Specific Fields**
```
# Mode-specific fields that appear in multiple modes
target_apy
max_drawdown
unwind_mode
rewards_mode
share_class
lst_type
hedge_venues
hedge_allocation.*
capital_allocation.*
data_requirements
lending_enabled
staking_enabled
basis_trade_enabled
use_flash_loan
max_leverage_loops
min_loop_position_usd
max_stake_spread_move
margin_ratio_target
```

#### **Risk and Operational Fields**
```
risk.*
- risk.bybit_cascade_threshold
- risk.service_degradation_risk
- risk.cross_platform_cascade_enabled
- risk.liquidation_risk
- risk.slashing_risk
- risk.rpc_failure_risk
- risk.protocol_risk
- risk.validator_penalty

operational.*
- operational.margin_check_frequency_hours
- operational.interest_frequency_hours
- operational.staking_reward_frequency_hours
- operational.rebalancing_frequency_hours

ltv.*
- ltv._comment
- ltv.standard_limits.ETH
- ltv.standard_limits.WETH
- ltv.standard_limits.wstETH
- ltv.standard_limits.weETH
- ltv.standard_limits.USDT
- ltv.emode_limits.wstETH_ETH
- ltv.emode_limits.weETH_ETH
- ltv.safe_ltv.standard_borrowing
- ltv.safe_ltv.emode_borrowing
- ltv.market_risk_buffer
- ltv.basis_risk_buffer

venues.*
- venues._comment

backtest.*
- backtest.default_initial_capital
- backtest.default_start_date
- backtest.default_end_date
- backtest.default_eth_price

execution.*
- execution.enable_static_compounding
```

### 2. Orphaned Model Fields (31 fields in Pydantic models but not in configs)

#### **Strategy Config Fields**
```
max_staked_basis_move
market_impact_threshold
max_spot_perp_basis_move
next_leverage_loop_factor
max_underlying_move
leverage_staking_currency
net_delta_critical
staking_reward_frequency_hours
infrastructure
hf_drift_trigger_pct
beta_basis_as_collateral
risk_check_interval
margin_critical_pct
restaking_enabled
min_trade_amount_usd
rebalancing_frequency_hours
interest_frequency_hours
plot_venue_balances
plot_token_balances
basis_trade_leverage_enabled
position_check_interval
net_delta_warning
aave_ltv_warning
margin_warning_pct
max_acceptable_impact_bps
```

#### **Backtest Config Fields**
```
plot_venue_balances
plot_token_balances
```

#### **Operational Config Fields**
```
health_check_interval
position_check_interval
risk_check_interval
alert_thresholds
```

#### **Venue Config Fields**
```
aave_ltv_warning
aave_ltv_critical
margin_warning_pct
margin_critical_pct
net_delta_warning
net_delta_critical
```

#### **Infrastructure Config Fields**
```
infrastructure
```

### 3. Mode-Specific Misalignments (Current State)

#### **Modes Missing from MODE_REQUIREMENTS**
- ✅ **RESOLVED**: Test modes (`test_btc_basis`, `test_pure_lending`) have been removed from codebase

#### **Modes with Extra Fields (not in their requirements)**
1. **usdt_market_neutral**: 5 extra fields
   - `target_apy`, `monitoring.alert_thresholds.drawdown_critical`, `unwind_mode`, `hedge_allocation.okx`, `rewards_mode`

2. **btc_basis**: 5 extra fields
   - `target_apy`, `monitoring.alert_thresholds.drawdown_critical`, `staking_enabled`, `monitoring`, `share_class`

3. **pure_lending**: 5 extra fields
   - `target_apy`, `monitoring.alert_thresholds.drawdown_critical`, `staking_enabled`, `monitoring`, `share_class`

4. **eth_leveraged**: 5 extra fields
   - `hedge_allocation`, `target_apy`, `monitoring.alert_thresholds.drawdown_critical`, `unwind_mode`, `hedge_venues`

5. **usdt_market_neutral_no_leverage**: 5 extra fields
   - `target_apy`, `monitoring.alert_thresholds.drawdown_critical`, `unwind_mode`, `max_stake_spread_move`, `hedge_allocation.okx`

6. **eth_staking_only**: 5 extra fields
   - `hedge_allocation`, `target_apy`, `monitoring.alert_thresholds.drawdown_critical`, `unwind_mode`, `hedge_venues`

## Root Cause Analysis (Updated)

### 1. **Incomplete Pydantic Model Coverage**
The Pydantic models only cover 63 fields out of 259 total config fields (24.3% coverage, improved from 22.6%). This suggests:
- Many config fields are not being validated
- Configuration loading may be incomplete
- Type safety is compromised

### 2. **Missing Configuration Files**
31 model fields don't exist in any config files (reduced from 37), suggesting:
- Models reference non-existent configuration
- Default values are hardcoded instead of configurable
- Configuration structure is incomplete

### 3. **Inconsistent Mode Requirements**
- ✅ **RESOLVED**: Test modes have been removed from codebase
- All 6 active modes have extra fields not defined in their requirements
- Mode validation is not comprehensive

### 4. **Fragmented Configuration Structure**
Configuration is spread across multiple files without clear hierarchy:
- `default.json` - base configuration (109 fields)
- `modes/*.yaml` - mode-specific overrides (27-34 fields each)
- `venues/*.yaml` - venue-specific settings (21-38 fields each)
- No clear mapping between these and Pydantic models

### 5. **Progress Made**
- **Reduced orphaned config fields**: 256 → 227 (29 fields resolved)
- **Reduced orphaned model fields**: 37 → 31 (6 fields resolved)
- **Improved coverage**: 9.5% → 12.4% (2.9% improvement)
- **Removed test modes**: 2 files deleted
- **Cleaned redundant fields**: 15 redundant fields removed

## Recommended Actions (Updated)

### Phase 1: Immediate Fixes ✅ **PARTIALLY COMPLETED**
1. ✅ **COMPLETED**: Removed test modes from codebase
2. ✅ **COMPLETED**: Updated mode requirements to include commonly used fields
3. ✅ **COMPLETED**: Removed 15 redundant config fields
4. 🔄 **IN PROGRESS**: Add missing fields to Pydantic models for high-priority infrastructure fields
5. 🔄 **IN PROGRESS**: Remove orphaned model fields that don't exist in configs

### Phase 2: Comprehensive Alignment
1. **Add high-priority infrastructure fields** to Pydantic models:
   - `monitoring.*` fields (log_format, health_check_interval, etc.)
   - `api.*` fields (host, port, cors_origins)
   - `contracts.*` fields (mainnet/sepolia contract addresses)
   - `health.*` fields (check_interval_seconds, component_timeout_seconds)
   - `database.*` fields (type, url, host, port, etc.)
   - `cache.*` fields (type, redis_url, ttl settings)
   - `redis.*` fields (enabled, url, session_ttl, cache_ttl)
   - `storage.*` fields (type, path)

2. **Add medium-priority fields** to Pydantic models:
   - `data.*` fields (provider, data_dir, cache_enabled, etc.)
   - `execution_costs.*` fields (model, data_path, fail_if_missing)
   - `fees.*` fields (trading fees, protocol fees, withdrawal fees)
   - `flash_loans.*` fields (fee_rate, min_loan_amount)
   - `supported_assets.*` fields (supply, borrow)
   - `gas_limits.*` fields (supply, borrow, repay, flash_loan)
   - `api_endpoints.*` fields (spot, futures)
   - `contract_addresses.*` fields (mainnet/sepolia addresses)
   - `rpc.*` fields (primary_endpoint, fallback_endpoints, timeout_seconds)
   - `integration.*` fields (gas_price_multiplier, gas_limit, max_slippage)
   - `rate_limits.*` fields (requests_per_second, requests_per_minute)
   - `features.*` fields (enhanced_apis, block_trace_support, transaction_simulation)
   - `output.*` fields (chart generation settings)
   - `premium.*` fields (enhanced_trace_api)

3. **Remove or consolidate low-priority fields**:
   - Mode-specific fields that are duplicated across modes
   - Risk and operational fields that are calculated at runtime
   - Fields that are documentation-only

### Phase 3: Quality Assurance
1. **Update config alignment validation** to be more strict
2. **Add automated tests** for configuration completeness
3. **Document configuration schema** comprehensively
4. **Implement configuration migration tools** for future changes

## Files Requiring Updates

### Pydantic Models (`config_models.py`)
- Add missing infrastructure fields
- Remove orphaned fields
- Update field types and validation

### Configuration Files
- `configs/default.json` - Add missing base fields
- `configs/modes/*.yaml` - Standardize field names and structure
- `configs/venues/*.yaml` - Ensure all venue fields are covered

### Validation Logic
- `MODE_REQUIREMENTS` - Add test modes and update requirements
- `validate_config_alignment.py` - Make validation more strict
- `config_manager.py` - Ensure all fields are loaded and validated

## Success Criteria (Current Progress)

The config alignment should achieve:
- **100% coverage**: All config fields have corresponding Pydantic model fields
  - **Current**: 12.4% (32 out of 259 fields aligned)
  - **Remaining**: 227 fields need to be added to Pydantic models
- **0 orphaned fields**: No fields exist in only one place
  - **Current**: 227 orphaned config fields + 31 orphaned model fields = 258 total orphaned
  - **Remaining**: 258 fields need to be resolved
- **Complete mode validation**: All modes have proper requirements defined
  - **Current**: ✅ All 6 active modes have requirements defined
  - **Remaining**: Update requirements to include all extra fields
- **Type safety**: All configuration is properly typed and validated
  - **Current**: ✅ Pydantic validation passes for all configs
  - **Remaining**: Add type safety for all 227 orphaned config fields
- **Clear hierarchy**: Configuration inheritance is well-defined and documented
  - **Current**: ✅ Clear separation between default.json, modes/*.yaml, venues/*.yaml
  - **Remaining**: Document the complete field mapping

### Progress Summary
- **Fields resolved**: 29 orphaned config fields + 6 orphaned model fields = 35 total resolved
- **Coverage improvement**: 9.5% → 12.4% (2.9% improvement)
- **Files cleaned**: 15 redundant fields removed from config files
- **Test modes removed**: 2 files deleted
- **Mode requirements updated**: All 6 active modes have comprehensive requirements

This analysis provides the foundation for a comprehensive configuration system that ensures type safety, completeness, and maintainability.

## Important Configuration Structure Guidelines

### Environment Variables vs Config Files
- **Environment Variables** (`backend/env.unified` + overrides): Only for sensitive info, ports, hosts, debugging, startup mode (live/backtest), data start/end dates needed for system startup mode independent of config files or mode.
- **Config Files**: All other configuration should be in `configs/` directory
- **Environment validation**: Handled by `_validate_environment_variables` in `config_validator.py` (NOT Pydantic models)

### Configuration Hierarchy
1. **`backend/env.unified`**: Base environment variables
2. **`configs/default.json`**: Centralized configuration
3. **`configs/*.json`**: Environment-specific overrides (local.json, production.json, etc.)
4. **`configs/venues/*.yaml`**: Venue-specific configurations
5. **`configs/modes/*.yaml`**: Strategy mode-specific configurations
6. **`configs/share_classes/*.yaml`**: Share class-specific configurations

### Field Resolution Strategy
- **Check Pydantic models first**: If a field exists in Pydantic models, remove from configs/
- **Sensitive data**: Move to environment variables if not already there
- **Centralized config**: Keep in `configs/default.json` unless mode/venue/share-class specific
- **Redundant fields**: Remove duplicates, prefer Pydantic model definitions
