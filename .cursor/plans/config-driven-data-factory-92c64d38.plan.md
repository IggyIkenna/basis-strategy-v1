<!-- 92c64d38-fa43-48c9-b0b6-688ebd4572ee 49c3d2c8-c8ae-4b8f-bc06-2824ab97bf04 -->
# Config-Driven Data Provider Factory Implementation

## Phase 1: Create Mode-Specific Data Providers (Base + 7 Modes)

### 1.1 Create BaseDataProvider Abstract Class

**File**: `backend/src/basis_strategy_v1/data_provider/base_data_provider.py`

- Implement abstract `BaseDataProvider` class per spec lines 19-42 in 09_DATA_PROVIDER.md
- Define standardized `get_data()` method returning structured dict (market_data, protocol_data)
- Add abstract `validate_data_requirements()` method
- Include `available_data_types` list for validation
- Add `get_timestamps()` method for backtest period validation

### 1.2 Create PureLendingDataProvider

**File**: `backend/src/basis_strategy_v1/data_provider/pure_lending_usdt_data_provider.py`

- Extend BaseDataProvider
- Load USDT prices, AAVE lending rates, gas costs, execution costs
- Validate data_requirements: ["usdt_prices", "aave_lending_rates", "gas_costs", "execution_costs"]
- Return standardized structure with market_data and protocol_data

### 1.3 Create BTCBasisDataProvider

**File**: `backend/src/basis_strategy_v1/data_provider/btc_basis_data_provider.py`

- Extend BaseDataProvider
- Load BTC spot prices, BTC futures (binance/bybit/okx), funding rates
- Validate data_requirements per btc_basis.yaml config
- Handle venue-specific price differences

### 1.4 Create ETHBasisDataProvider

**File**: `backend/src/basis_strategy_v1/data_provider/eth_basis_data_provider.py`

- Extend BaseDataProvider
- Load ETH spot prices, ETH futures (binance/bybit/okx), funding rates
- Similar structure to BTC basis but ETH-specific

### 1.5 Create ETHLeveragedDataProvider

**File**: `backend/src/basis_strategy_v1/data_provider/eth_leveraged_data_provider.py`

- Extend BaseDataProvider
- Load ETH prices, weETH/wstETH oracle prices, AAVE rates (weETH, WETH), staking rewards, EIGEN/ETHFI rewards
- Most complex provider with LST and leverage data

### 1.6 Create ETHStakingOnlyDataProvider

**File**: `backend/src/basis_strategy_v1/data_provider/eth_staking_only_data_provider.py`

- Extend BaseDataProvider
- Load ETH prices, weETH oracle prices, staking rewards (no leverage/borrowing)
- Simpler version of ETHLeveragedDataProvider

### 1.7 Create USDTMarketNeutralNoLeverageDataProvider

**File**: `backend/src/basis_strategy_v1/data_provider/usdt_market_neutral_no_leverage_data_provider.py`

- Extend BaseDataProvider
- Load ETH prices, weETH oracle prices, perp funding rates, staking rewards
- No AAVE borrowing data needed

### 1.8 Create USDTMarketNeutralDataProvider

**File**: `backend/src/basis_strategy_v1/data_provider/usdt_market_neutral_data_provider.py`

- Extend BaseDataProvider
- Load ALL data: ETH prices, weETH oracle, AAVE rates, perp funding, staking rewards
- Most complex provider combining leverage + hedging + staking

## Phase 2: Refactor DataProviderFactory

### 2.1 Update data_provider_factory.py

**File**: `backend/src/basis_strategy_v1/infrastructure/data/data_provider_factory.py`

- Replace current factory logic with config-driven approach
- Use mode from config to select appropriate provider class
- Call `validate_data_requirements()` on created provider
- Pass config dict to provider constructor
- Support both execution_mode='backtest' and 'live'

### 2.2 Add Factory Validation

- Validate config contains required 'mode' field (fail-fast)
- Validate config contains 'data_requirements' list
- Validate BASIS_DATA_START_DATE and BASIS_DATA_END_DATE env vars
- Log provider creation with mode and data_requirements

## Phase 3: Comprehensive Data Validation System

### 3.1 Create DataValidator Class

**File**: `backend/src/basis_strategy_v1/infrastructure/data/data_validator.py`

- Validate file existence with DataProviderError('DATA-001')
- Validate CSV parsing with DataProviderError('DATA-002')
- Validate empty files with DataProviderError('DATA-003')
- Validate date range coverage with DataProviderError('DATA-004')
- Validate missing columns with DataProviderError('DATA-010')
- Validate timestamp formats with DataProviderError('DATA-011')
- Validate data gaps with DataProviderError('DATA-012')
- Validate env variables with DataProviderError('DATA-013')

### 3.2 Enhance _validate_data_file Function

**File**: `backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py`

- Keep existing validation logic
- Add more comprehensive error codes
- Validate timestamp alignment (hourly)
- Validate data completeness (no nulls in critical columns)
- Return detailed validation report

### 3.3 Add Data Quality Metrics

- Coverage metrics per strategy mode
- Completeness metrics per time period
- Alignment metrics across sources
- Freshness metrics for data staleness

## Phase 4: Update Quality Gates

### 4.1 Create test_data_availability_quality_gates.py

**File**: `scripts/test_data_availability_quality_gates.py`

- Implement DataAvailabilityChecker class per 03_data_loading_quality_gate.md lines 54-73
- Test all data files exist and are accessible
- Test data completeness for all required time periods
- Test data alignment across sources
- Test strategy mode data requirements (pure_lending_usdt, btc_basis, eth_basis, usdt_market_neutral)

### 4.2 Create test_data_provider_factory_quality_gates.py

**File**: `scripts/test_data_provider_factory_quality_gates.py`

- Test factory creates correct provider for each mode
- Test provider validates data_requirements correctly
- Test provider loads correct data files
- Test standardized data structure returned
- Test error handling for missing data

### 4.3 Update run_quality_gates.py

**File**: `scripts/run_quality_gates.py`

- Add 'data_loading' category to quality_gate_categories
- Include both new quality gate scripts
- Set critical=True for data validation gates

### 4.4 Integration Tests

- Test data provider factory with all 7 mode configs
- Test data validation catches all error types
- Test fail-fast behavior on missing data
- Test standardized data structure across all providers

## Phase 5: Update Historical Data Provider

### 5.1 Refactor historical_data_provider.py

**File**: `backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py`

- Remove hardcoded mode-specific logic from _load_data_for_mode()
- Use data_requirements from config to drive loading
- Implement name mapping from config names to internal keys
- Keep _validate_data_requirements() method
- Update to use new BaseDataProvider interface

### 5.2 Add Config-Driven Loading

- Read data_requirements from config['data_requirements']
- Map requirement names to file paths (usdt_prices → usdt_rates file)
- Load only required files per mode
- Fail fast if required file missing

## Phase 6: Documentation Updates

### 6.1 Update 09_DATA_PROVIDER.md

- Document new BaseDataProvider abstraction
- Document all 7 mode-specific providers
- Document DataProviderFactory usage
- Update examples with config-driven approach

### 6.2 Update 19_CONFIGURATION.md

- Validate data_requirements examples match implementation
- Validate component_config examples are accurate
- Add factory usage examples

## Success Criteria

### Implementation Complete

- [ ] BaseDataProvider abstract class created
- [ ] All 7 mode-specific providers implemented
- [ ] DataProviderFactory refactored with config-driven logic
- [ ] Comprehensive data validation system in place
- [ ] All quality gates passing

### Data Validation

- [ ] File existence validation with error codes
- [ ] Date range validation with BASIS_DATA_START_DATE/END_DATE
- [ ] Timestamp alignment validation (hourly)
- [ ] Data completeness validation (no nulls)
- [ ] Data gaps detection and reporting

### Quality Gates

- [ ] test_data_availability_quality_gates.py passing
- [ ] test_data_provider_factory_quality_gates.py passing
- [ ] All strategy modes validated (pure_lending_usdt, btc_basis, eth_basis, usdt_market_neutral)
- [ ] Integration with run_quality_gates.py complete

### Architecture Compliance

- [ ] No hardcoded mode logic in providers
- [ ] Config-driven data loading throughout
- [ ] Fail-fast on missing data (no graceful degradation)
- [ ] Standardized data structure returned by all providers
- [ ] Environment variables used correctly (paths/dates only, not data selection)

### To-dos

- [ ] Set up environment variables for validation
- [ ] Run and fix config alignment validation
- [ ] Run and fix config and data validation
- [ ] Run and fix data availability quality gate
- [ ] Run and fix data provider factory validation
- [ ] Run full quality gate suite and verify all pass