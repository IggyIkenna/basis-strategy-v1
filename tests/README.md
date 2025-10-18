# Basis Strategy Test Suite

## Overview

This directory contains the complete test suite for the Basis Strategy project, organized into a conventional 3-tier testing structure that replaces the previous monolithic quality gates.

**Note**: All tests are now consolidated in this `tests/` directory. Orchestration scripts remain in `scripts/` directory.

## 3-Tier Testing Philosophy

### 1. Unit Tests (`tests/unit/`)
- **Purpose**: Component isolation with mocked dependencies
- **Scope**: Individual component behavior testing
- **Dependencies**: Minimal, using pytest fixtures and mocks
- **Execution Time**: Fast (~10s for all unit tests)
- **Critical**: Yes - must pass for system to be considered functional

### 2. Integration Tests (`tests/integration/`)
- **Purpose**: Component data flow validation per WORKFLOW_GUIDE.md
- **Scope**: Component interaction patterns and data flows
- **Dependencies**: Real components with minimal real data
- **Execution Time**: Medium (~60s for all integration tests)
- **Critical**: Yes - validates component interactions

### 3. E2E Tests (`tests/e2e/`)
- **Purpose**: Full strategy execution with real data
- **Scope**: Complete strategy workflows
- **Dependencies**: Full system with real data
- **Execution Time**: Slow (~120s for all E2E tests)
- **Critical**: No - only run when unit + integration tests pass

## Directory Structure

```
tests/
├── unit/                          # 67 component isolation tests
│   ├── conftest.py               # Shared pytest fixtures
│   ├── test_position_monitor_unit.py
│   ├── test_exposure_monitor_unit.py
│   ├── test_risk_monitor_unit.py
│   ├── test_pnl_monitor_unit.py
│   ├── test_strategy_manager_unit.py
│   ├── test_execution_manager_unit.py
│   ├── test_data_provider_unit.py
│   ├── test_config_manager_unit.py
│   ├── test_event_logger_unit.py
│   ├── test_results_store_unit.py
│   ├── test_health_system_unit.py
│   ├── test_api_endpoints_unit.py
│   ├── test_environment_switching_unit.py
│   ├── test_config_validation_unit.py
│   ├── test_live_data_validation_unit.py
│   ├── # API Routes unit tests (9 tests)
│   ├── test_auth_routes_unit.py
│   ├── test_backtest_routes_unit.py
│   ├── test_capital_routes_unit.py
│   ├── test_charts_routes_unit.py
│   ├── test_config_routes_unit.py
│   ├── test_health_routes_unit.py
│   ├── test_live_trading_routes_unit.py
│   ├── test_results_routes_unit.py
│   ├── test_strategies_routes_unit.py
│   ├── # Core Strategies unit tests (9 tests)
│   ├── test_btc_basis_strategy_unit.py
│   ├── test_eth_basis_strategy_unit.py
│   ├── test_eth_leveraged_strategy_unit.py
│   ├── test_eth_staking_only_strategy_unit.py
│   ├── test_pure_lending_usdt_strategy_unit.py
│   ├── test_strategy_factory_unit.py
│   ├── test_usdt_market_neutral_strategy_unit.py
│   ├── test_usdt_market_neutral_no_leverage_strategy_unit.py
│   ├── test_ml_directional_strategy_unit.py
│   ├── # Infrastructure Data Provider unit tests (13 tests)
│   ├── test_btc_basis_data_provider_unit.py
│   ├── test_data_provider_factory_unit.py
│   ├── test_config_driven_historical_data_provider_unit.py
│   ├── test_data_validator_unit.py
│   ├── test_eth_basis_data_provider_unit.py
│   ├── test_eth_leveraged_data_provider_unit.py
│   ├── test_eth_staking_only_data_provider_unit.py
│   ├── test_historical_data_provider_unit.py
│   ├── test_live_data_provider_unit.py
│   ├── test_ml_directional_data_provider_unit.py
│   ├── test_pure_lending_usdt_data_provider_unit.py
│   ├── test_usdt_market_neutral_data_provider_unit.py
│   ├── test_usdt_market_neutral_no_leverage_data_provider_unit.py
│   ├── # Core Math unit tests (4 tests)
│   ├── test_health_calculator_unit.py
│   ├── test_ltv_calculator_unit.py
│   ├── test_margin_calculator_unit.py
│   ├── test_metrics_calculator_unit.py
│   ├── # Execution Interfaces unit tests (3 tests)
│   ├── test_cex_execution_interface_unit.py
│   ├── test_onchain_execution_interface_unit.py
│   ├── test_transfer_execution_interface_unit.py
│   ├── # Zero Coverage Components unit tests (11 tests)
│   ├── test_venue_adapters_unit.py
│   ├── test_backtest_service_unit.py
│   ├── test_live_service_unit.py
│   ├── test_component_health_unit.py
│   ├── test_unified_health_manager_unit.py
│   ├── test_utility_manager_unit.py
│   ├── test_error_code_registry_unit.py
│   ├── test_execution_instructions_unit.py
│   ├── test_reconciliation_component_unit.py
│   ├── test_api_call_queue_unit.py
│   └── test_chart_storage_visualization_unit.py
├── integration/                   # 14 component data flow tests
│   ├── conftest.py               # Real component fixtures
│   ├── test_data_flow_position_to_exposure.py
│   ├── test_data_flow_exposure_to_risk.py
│   ├── test_data_flow_risk_to_strategy.py
│   ├── test_data_flow_strategy_to_execution.py
│   ├── test_tight_loop_reconciliation.py
│   └── test_repo_structure_integration.py
└── e2e/                          # 12 strategy execution tests (8 *_e2e.py + 4 *_quality_gates.py)
    ├── test_pure_lending_usdt_e2e.py
    ├── test_btc_basis_e2e.py
    ├── test_eth_basis_e2e.py
    ├── test_usdt_market_neutral_e2e.py
    ├── test_eth_staking_only_e2e.py
    ├── test_eth_leveraged_staking_e2e.py
    ├── test_usdt_market_neutral_no_leverage_e2e.py
    ├── test_performance_e2e.py
    ├── test_pure_lending_usdt_quality_gates.py
    ├── test_btc_basis_quality_gates.py
    ├── test_eth_basis_quality_gates.py
    ├── test_usdt_market_neutral_quality_gates.py
```

## Running Tests

### Run All Tests
```bash
python scripts/run_quality_gates.py
```

### Run Unit Tests Only
```bash
python scripts/run_quality_gates.py --category unit
```

### Run Integration Tests Only
```bash
python scripts/run_quality_gates.py --category integration_data_flows
```

### Run E2E Tests Only
```bash
python scripts/run_quality_gates.py --category e2e_strategies
```

### Run E2E Quality Gates Tests (Legacy)
```bash
python scripts/run_quality_gates.py --category e2e_quality_gates
```

### Run Specific Test File
```bash
python -m pytest tests/unit/test_position_monitor_unit.py -v
```

## Smart Skipping Logic

E2E tests are automatically skipped if:
- Unit tests < 80% passing
- Integration tests < 80% passing

This prevents wasting time on E2E tests when the foundation is broken.

## Migration from Scripts

This test structure replaces the previous `scripts/` quality gates:

### Before (Scripts):
- **2/23 passing (8.7%)** - misleading due to cascading failures
- 40+ scripts, poorly organized
- Massive codependency issues
- Can't identify root causes
- Tests take 150+ seconds
- Most failures due to integration issues

### After (Tests):
- **Clear 3-tier structure**: Unit → Integration → E2E
- **Pinpoint failures**: Unit tests identify exact component issues
- **Data flow validation**: Integration tests validate WORKFLOW_GUIDE.md patterns
- **Meaningful E2E**: Only run when foundation solid
- **Faster execution**: Unit tests run in parallel (~10s), skip E2E if foundation broken
- **Expected passing rate**: 80%+ for unit tests, 70%+ for integration, E2E depends on fixes
- **Complete coverage**: 67 unit tests, 14 integration tests, 12 E2E tests (8 *_e2e.py + 4 *_quality_gates.py)

## Quality Gate Integration

The quality gate runner (`scripts/run_quality_gates.py`) automatically:
1. Runs unit tests first (critical)
2. Runs integration tests second (critical)
3. Runs E2E tests last (non-critical, only if foundation solid)
4. Provides clear tier-based reporting
5. Skips E2E tests if unit/integration < 80% passing

## Adding New Tests

### For Unit Tests:
1. Create test file in `tests/unit/`
2. Use fixtures from `conftest.py`
3. Test component in isolation with mocks
4. Add to `unit` category in `run_quality_gates.py`

### For Integration Tests:
1. Create test file in `tests/integration/`
2. Use real component fixtures
3. Test component interactions and data flows
4. Add to `integration_data_flows` category

### For E2E Tests:
1. Create test file in `tests/e2e/`
2. Test complete strategy execution
3. Use real data and full system
4. Add to `e2e_strategies` category (use *_e2e.py naming)

## Troubleshooting

### Unit Tests Failing:
1. Check component initialization
2. Verify mock fixtures are correct
3. Check component configuration
4. Review component error handling

### Integration Tests Failing:
1. Check component data flows
2. Verify real data availability
3. Check component interactions
4. Review WORKFLOW_GUIDE.md patterns

### E2E Tests Failing:
1. Check if unit/integration tests pass first
2. Verify real data availability
3. Check strategy configuration
4. Review complete system setup

### All Tests Failing:
1. Check data directory exists
2. Verify backend dependencies
3. Check configuration files
4. Review system requirements

## Relationship with Scripts Directory

The `scripts/` directory contains orchestration and utility scripts that work with these tests:

### Quality Gate Orchestration
- **`scripts/run_quality_gates.py`** - Main quality gate runner that executes tests by category
- **`scripts/analyze_test_coverage.py`** - Test coverage analysis for unit tests
- **`scripts/load_env.py`** - Environment loading for quality gates

### Test Execution
```bash
# Run all quality gates (includes tests)
python scripts/run_quality_gates.py

# Run specific test categories
python scripts/run_quality_gates.py --category unit
python scripts/run_quality_gates.py --category integration_data_flows
python scripts/run_quality_gates.py --category e2e_strategies

# Run tests directly with pytest
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

## Reference Documentation

- **Test Organization Guide**: `scripts/TEST_ORGANIZATION.md`
- **Component Workflows**: `docs/WORKFLOW_GUIDE.md`
- **Architecture Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`
- **Quality Gates**: `scripts/run_quality_gates.py`
- **Scripts Documentation**: `scripts/README.md`
