<!-- 25bc6094-cdf2-4d2b-b5c9-b4184884e913 e9cbcf1b-8b37-4890-910d-427cd2ba0849 -->
# Mode-Agnostic Architecture Refactor

## Overview

Implement comprehensive mode-agnostic architecture refactor to eliminate mode-specific logic from components and enable fully config-driven behavior. This refactor touches ALL documentation, configuration files, codebase components, and tests.

**Estimated Timeline**: 64-84 hours (8-10.5 days)

**Total Todos**: 227 actionable items across 8 phases

## Execution Order

1. **Phase 1**: Documentation Updates (foundation) - 8-10 hours
2. **Phase 2**: Configuration Refactor (enables everything else) - 6-8 hours  
3. **Phase 3**: DataProvider Refactor (data layer) - 8-10 hours
4. **Phase 4**: Component Refactor (core logic) - 16-20 hours
5. **Phase 5**: Service Layer Updates (integration) - 4-6 hours
6. **Phase 6**: Test Updates (validation) - 12-16 hours
7. **Phase 7**: Task File Updates (traceability) - 4-6 hours
8. **Phase 8**: Quality Gate Updates (final validation) - 6-8 hours

**Critical Path**: Phases 1-4 must be sequential

**Parallelizable**: Phases 6-8 can be done in parallel after Phase 5

## Phase 1: Documentation Updates (8-10 hours)

### Update Canonical Architecture Documents

- Update `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` with Config-Driven Mode-Agnostic Architecture section
- Add DataProvider abstraction layer pattern with code examples
- Document config-driven component behavior principles  
- Update Section 7 (Generic vs Mode-Specific) with detailed config approach
- Update `docs/MODES.md` with config-driven PnL attribution examples
- Add config-driven exposure calculation examples to MODES.md

### Update All Component Specifications

- Add "Config-Driven Behavior" section to all 20 specs in `docs/specs/`
- Update "Configuration Parameters" sections with mode-agnostic config examples
- Add "Data Requirements" section showing config-driven data subscription
- Update code examples to show config-driven logic instead of mode checks
- Specifically update: 02_EXPOSURE_MONITOR.md, 03_RISK_MONITOR.md, 04_pnl_monitor.md, 05_STRATEGY_MANAGER.md, 06_VENUE_MANAGER.md, 09_DATA_PROVIDER.md

### Update Workflow and API Documentation

- Update `docs/WORKFLOW_GUIDE.md` workflow diagrams for config-driven data flow
- Add config-driven strategy execution examples to WORKFLOW_GUIDE.md
- Update `docs/API_DOCUMENTATION.md` with config override parameters
- Add config override examples to API_DOCUMENTATION.md

### Create New Documentation File

- Create `docs/CONFIG_DRIVEN_ARCHITECTURE.md`
- Write complete guide to config-driven architecture
- Document config hierarchy and inheritance patterns
- Document DataProvider factory pattern
- Document config validation strategies
- Add examples for all 7 strategy modes

## Phase 2: Configuration Refactor (6-8 hours)

### Update All 7 Mode Configuration Files

For each of the 7 files in `configs/modes/`:

- `pure_lending_usdt_usdt.yaml` - Add data_requirements and component_config sections
- `btc_basis.yaml` - Add data_requirements and component_config sections
- `eth_basis.yaml` - Add data_requirements and component_config sections
- `eth_leveraged.yaml` - Add data_requirements and component_config sections
- `eth_staking_only.yaml` - Add data_requirements and component_config sections
- `usdt_market_neutral_no_leverage.yaml` - Add data_requirements and component_config sections
- `usdt_market_neutral.yaml` - Add data_requirements and component_config sections

Each must include:

```yaml
data_requirements: [...]
component_config:
  risk_monitor: {...}
  exposure_monitor: {...}
  pnl_monitor: {...}
  strategy_manager: {...}
  execution_manager: {...}
  results_store: {...}
```

### Create Config Validation Schemas

Update `backend/src/basis_strategy_v1/infrastructure/config/models.py`:

- Add ComponentConfigModel Pydantic schema
- Add DataRequirementsModel schema
- Add RiskMonitorConfigModel schema
- Add ExposureMonitorConfigModel schema
- Add PnLMonitorConfigModel schema
- Add StrategyManagerConfigModel schema
- Add VenueManagerConfigModel schema
- Add ResultsStoreConfigModel schema
- Add validation methods for each config type
- Add comprehensive error messages for validation failures

## Phase 3: DataProvider Refactor (8-10 hours)

### Create Base DataProvider Class

Create `backend/src/basis_strategy_v1/infrastructure/data/base_data_provider.py`:

- Define abstract get_data(timestamp) interface
- Define standardized data structure format
- Add validate_data_requirements() abstract method
- Document return structure for market_data and protocol_data
- Add comprehensive docstrings with examples

### Create 7 Mode-Specific DataProvider Classes

Create new files in `backend/src/basis_strategy_v1/infrastructure/data/`:

- `pure_lending_usdt_data_provider.py` - Implement PureLendingDataProvider
- `btc_basis_data_provider.py` - Implement BTCBasisDataProvider
- `eth_basis_data_provider.py` - Implement ETHBasisDataProvider  
- `eth_leveraged_data_provider.py` - Implement ETHLeveragedDataProvider
- `eth_staking_only_data_provider.py` - Implement ETHStakingOnlyDataProvider
- `usdt_market_neutral_no_leverage_data_provider.py` - Implement USDTMarketNeutralNoLeverageDataProvider
- `usdt_market_neutral_data_provider.py` - Implement USDTMarketNeutralDataProvider

Each provider must:

- Inherit from BaseDataProvider
- Implement _load_data_for_mode() with mode-specific data loading
- Implement get_data() returning standardized structure
- Implement validate_data_requirements()

### Update DataProviderFactory

Update `backend/src/basis_strategy_v1/infrastructure/data/data_provider_factory.py`:

- Update create() method to instantiate new provider classes
- Add config validation before provider creation
- Add data requirements validation
- Add comprehensive error handling

## Phase 4: Component Refactor (16-20 hours)

### Refactor Risk Monitor

Update `backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py`:

- Extract risk_config from config in **init**
- Store enabled_risk_types, risk_limits from config
- Update assess_risk() to loop through enabled_risk_types
- Remove ALL mode-specific if statements
- Add graceful handling for missing data in each risk calculation
- Update _calculate_aave_health_factor(), _calculate_cex_margin_ratio(), _calculate_funding_risk()

### Refactor Exposure Monitor

Update `backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py`:

- Extract exposure_config from config in **init**
- Store track_assets, conversion_methods, exposure_currency from config
- Update calculate_exposure() to loop through track_assets
- Remove ALL mode-specific if statements
- Add _validate_exposure_config() method
- Update _calculate_asset_exposure() to use conversion_methods
- Add graceful handling for missing conversion data

### Refactor PnL Monitor

Update `backend/src/basis_strategy_v1/core/math/pnl_monitor.py`:

- Extract pnl_config from config in **init**
- Store attribution_types, reporting_currency, reconciliation_tolerance from config
- Create cumulative_attributions dict from attribution_types
- Update _calculate_attribution_pnl() to loop through attribution_types
- Remove ALL mode-specific if statements
- Add _zero_attribution() method returning zeros for all types
- Update each attribution calculation to check data availability

### Refactor Strategy Manager

Update `backend/src/basis_strategy_v1/core/strategies/components/strategy_manager.py`:

- Extract strategy_config from config in **init**
- Store strategy_type, available_actions, rebalancing_triggers from config
- Update calculate_target_positions() to use strategy_type
- Keep mode-specific position calculation but make it config-driven
- Add config validation for strategy-specific requirements

### Refactor Execution Manager  

Update `backend/src/basis_strategy_v1/core/execution/execution_manager.py`:

- Extract execution_config from config in **init**
- Store supported_actions, action_mapping from config
- Update execute_strategy_action() to use action_mapping
- Remove mode-specific logic from action execution
- Add validation that requested actions are supported

### Refactor Results Store

Update `backend/src/basis_strategy_v1/core/results/results_store.py`:

- Extract results_config from config in **init**
- Store result_types, balance_sheet_assets, pnl_attribution_types from config
- Update store_results() to loop through result_types
- Add graceful handling for optional result types
- Return None for result types not configured

### Create Component Factory

Create `backend/src/basis_strategy_v1/core/strategies/component_factory.py`:

- Add ComponentFactory class with config validation
- Add create_risk_monitor(), create_exposure_monitor(), create_pnl_monitor() factory methods
- Add create_strategy_manager(), create_execution_manager(), create_results_store() factory methods
- Add create_all() method to create all components
- Add comprehensive error messages for missing config

## Phase 5: Service Layer Updates (4-6 hours)

### Update Backtest Service

Update `backend/src/basis_strategy_v1/api/services/backtest_service.py`:

- Use DataProviderFactory.create() instead of mode-specific providers
- Remove mode-specific provider instantiation
- Use ComponentFactory.create_all() for component initialization
- Add config override handling in run_backtest()
- Add config completeness validation before starting
- Update error handling for config issues

### Update Live Trading Service

Update `backend/src/basis_strategy_v1/api/services/live_trading_service.py`:

- Use DataProviderFactory.create() instead of mode-specific providers
- Remove mode-specific provider instantiation
- Use ComponentFactory.create_all() for component initialization
- Add config override handling in start_live_trading()
- Add config completeness validation
- Update error handling for config issues

### Update API Endpoints

Update `backend/src/basis_strategy_v1/api/routes/*.py`:

- Add config_overrides parameter to BacktestRequest model
- Add config_overrides parameter to LiveTradingRequest model
- Update response models for config-driven result types
- Update API documentation strings in routes
- Add validation for config override format

## Phase 6: Test Updates (12-16 hours)

### Update Unit Tests

Update all `tests/unit/components/*.py`:

- Create config fixtures in tests/unit/components/conftest.py
- Update test_risk_monitor.py: Add config fixtures, test enabled_risk_types, test missing config handling
- Update test_exposure_monitor.py: Add config fixtures, test track_assets, test conversion_methods
- Update test_pnl_monitor.py: Add config fixtures, test attribution_types, test graceful zero returns
- Update test_strategy_manager.py: Add config fixtures, test strategy_type
- Update test_execution_manager.py: Add config fixtures, test action_mapping
- Add config override tests to all component tests

### Update Integration Tests

Update `tests/integration/*.py`:

- Update tests to use new config structure
- Add DataProvider factory pattern tests
- Add ComponentFactory pattern tests
- Add config validation tests
- Add config override functionality tests

### Update E2E Tests

Update all 7 E2E test files in `tests/e2e/`:

- test_pure_lending_usdt.py, test_btc_basis.py, test_eth_basis.py, test_eth_leveraged.py
- test_eth_staking_only.py, test_usdt_market_neutral_no_leverage.py, test_usdt_market_neutral.py
- Verify config-driven data subscriptions work correctly
- Verify config-driven component behavior works correctly
- Add config override scenarios to all E2E tests

## Phase 7: Task File Updates (4-6 hours)

### Update Existing Task Files

Update `.cursor/tasks/`:

- 02_config_loading_validation.md - Add validation for new config structure
- 03_data_loading_quality_gate.md - Update for DataProvider abstraction
- 04_complete_api_endpoints.md - Add config override endpoints
- 09_fail_fast_19_CONFIGURATION.md - Update for new config structure
- 14_component_data_flow_architecture.md - Update for config-driven flow
- Verify no changes needed: 01, 05, 10, 11, 12, 13 task files

### Rewrite Major Task Files

Complete rewrites in `.cursor/tasks/`:

- 06_strategy_manager_refactor.md - Update for config-driven strategy manager
- 08_mode_agnostic_architecture.md - Complete rewrite for new approach
- 15-18_*_quality_gates.md - Update for config-driven validation
- 19-23_*_unit_tests.md - Update for config-driven testing

### Create New Task Files

Create in `.cursor/tasks/`:

- 30_data_provider_abstraction.md - Document DataProvider factory and base class
- 31_config_driven_components.md - Document component config refactor approach
- 32_config_validation_system.md - Document config validation and schemas

## Phase 8: Quality Gate Updates (6-8 hours)

### Update Existing Quality Gate Scripts

Update all `scripts/test_*_quality_gates.py`:

- test_risk_monitor_quality_gates.py - Add enabled_risk_types config tests
- test_exposure_monitor_quality_gates.py - Add track_assets config tests
- test_pnl_monitor_quality_gates.py - Add attribution_types config tests
- test_pure_lending_usdt_quality_gates.py - Update for config-driven validation
- test_btc_basis_quality_gates.py - Update for config-driven validation
- test_eth_basis_quality_gates.py - Update for config-driven validation
- test_usdt_market_neutral_quality_gates.py - Update for config-driven validation
- Remove mode-specific assertions from ALL quality gate scripts
- Add config validation tests and missing config handling tests

### Create New Quality Gate Scripts

Create in `scripts/`:

- test_config_driven_architecture_quality_gates.py - Test overall config-driven architecture compliance
- test_data_provider_abstraction_quality_gates.py - Test DataProvider factory and standardized data structure
- test_component_config_validation_quality_gates.py - Test all component config schemas and validation errors

## Success Criteria

**Documentation**: 25 items - All specs updated, new CONFIG_DRIVEN_ARCHITECTURE.md created, workflow docs updated

**Configuration**: 31 items - All 7 mode configs updated, validation schemas complete and working

**Codebase**: 60 items - Base + 7 DataProviders created, 6 components refactored, ComponentFactory created, services updated

**Tests**: 40 items - All unit/integration/E2E tests updated, 80% coverage maintained

**Quality Gates**: 27 items - All scripts updated, 3 new scripts created, 20/24 gates passing (83%)

**Tasks**: 19 items - Existing tasks updated, major tasks rewritten, 3 new tasks created

**Total: 227 actionable todos**

## Risk Mitigation

- Start with documentation to establish patterns
- Update configs early to unblock component refactor
- Test incrementally after each component refactor
- Keep quality gates running to catch regressions
- Maintain backward compatibility in APIs during transition

### To-dos

- [ ] Phase 1: Documentation Updates - Update all canonical docs, component specs, workflow docs, and create CONFIG_DRIVEN_ARCHITECTURE.md (25 items, 8-10 hours)
- [ ] Phase 2: Configuration Refactor - Update all 7 mode configs with data_requirements and component_config sections, create Pydantic validation schemas (31 items, 6-8 hours)
- [ ] Phase 3: DataProvider Refactor - Create base class, 7 mode-specific providers, update factory (60 items, 8-10 hours)
- [ ] Phase 4: Component Refactor - Refactor Risk, Exposure, PnL, Strategy, Execution, Results components to be config-driven, create ComponentFactory (60 items, 16-20 hours)
- [ ] Phase 5: Service Layer Updates - Update Backtest/Live services to use factories, update API endpoints with config overrides (15 items, 4-6 hours)
- [ ] Phase 6: Test Updates - Update all unit/integration/E2E tests for config-driven behavior (40 items, 12-16 hours)
- [ ] Phase 7: Task File Updates - Update existing tasks, rewrite major tasks, create 3 new task files (19 items, 4-6 hours)
- [ ] Phase 8: Quality Gate Updates - Update all existing quality gate scripts, create 3 new quality gate scripts (27 items, 6-8 hours)