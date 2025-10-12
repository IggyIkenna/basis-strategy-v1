# Test Organization Guide

## Overview

This document describes the new 3-tier testing structure for the Basis Strategy project, replacing the previous monolithic quality gates with organized, isolated tests.

## 3-Tier Testing Philosophy

### 1. Unit Tests (`scripts/unit_tests/`)
- **Purpose**: Component isolation with mocked dependencies
- **Scope**: Individual component behavior testing
- **Dependencies**: Minimal, using pytest fixtures and mocks
- **Execution Time**: Fast (~10s for all unit tests)
- **Critical**: Yes - must pass for system to be considered functional

### 2. Integration Tests (`scripts/integration_tests/`)
- **Purpose**: Component data flow validation per WORKFLOW_GUIDE.md
- **Scope**: Component interaction patterns and data flows
- **Dependencies**: Real components with minimal real data
- **Execution Time**: Medium (~60s for all integration tests)
- **Critical**: Yes - validates component interactions

### 3. E2E Tests (`scripts/e2e_tests/`)
- **Purpose**: Full strategy execution with real data
- **Scope**: Complete strategy workflows
- **Dependencies**: Full system with real data
- **Execution Time**: Slow (~120s for all E2E tests)
- **Critical**: No - only run when unit + integration tests pass

## Directory Structure

```
tests/                             # Conventional test directory
├── unit/                          # Unit tests with mocked dependencies
│   ├── conftest.py               # Shared pytest fixtures
│   ├── test_position_monitor_unit.py
│   ├── test_exposure_monitor_unit.py
│   ├── test_risk_monitor_unit.py
│   ├── test_pnl_calculator_unit.py
│   ├── test_strategy_manager_unit.py
│   ├── test_execution_manager_unit.py
│   ├── test_data_provider_unit.py
│   └── test_config_manager_unit.py
├── integration/                   # Integration tests with real components
│   ├── conftest.py               # Real component fixtures
│   ├── test_data_flow_position_to_exposure.py
│   ├── test_data_flow_exposure_to_risk.py
│   ├── test_data_flow_risk_to_strategy.py
│   ├── test_data_flow_strategy_to_execution.py
│   └── test_tight_loop_reconciliation.py
└── e2e/                          # E2E tests with full system
    ├── test_pure_lending_e2e.py
    ├── test_btc_basis_e2e.py
    ├── test_eth_basis_e2e.py
    └── test_usdt_market_neutral_e2e.py

scripts/
├── deprecated/                    # Deprecated quality gate scripts
│   ├── monitor_quality_gates.py
│   ├── test_config_and_data_validation.py
│   ├── test_async_ordering_quality_gates.py
│   ├── test_tight_loop_quality_gates.py
│   └── test_e2e_backtest_flow.py
└── run_quality_gates.py          # Main quality gate runner
```

## When to Write Unit vs Integration vs E2E Tests

### Write Unit Tests When:
- Testing individual component behavior
- Validating component initialization
- Testing error handling within a component
- Testing component configuration
- Testing component edge cases
- Testing component performance

### Write Integration Tests When:
- Testing component data flows per WORKFLOW_GUIDE.md
- Validating component interaction patterns
- Testing tight loop architecture
- Testing component reconciliation
- Testing component state persistence

### Write E2E Tests When:
- Testing complete strategy execution
- Validating full system workflows
- Testing strategy performance with real data
- Testing strategy error recovery
- Testing strategy configuration changes

## How to Use Pytest Fixtures

### Unit Test Fixtures (`tests/unit/conftest.py`)

```python
@pytest.fixture
def mock_config():
    """Minimal config with all required fields"""
    return {
        'mode': 'pure_lending',
        'share_class': 'USDT',
        'asset': 'USDT',
        'initial_capital': 100000.0,
        'max_drawdown': 0.2,
        'leverage_enabled': False
    }

@pytest.fixture
def mock_data_provider():
    """Mock data provider with test data"""
    mock_provider = Mock()
    mock_provider.get_price.return_value = 3000.0
    return mock_provider
```

### Integration Test Fixtures (`tests/integration/conftest.py`)

```python
@pytest.fixture
def real_data_provider():
    """Load 1 week real data for validation"""
    data_provider = DataProvider(data_dir='data', mode='backtest')
    return data_provider

@pytest.fixture
def real_components(real_data_provider):
    """Initialize real components with real data provider"""
    position_monitor = PositionMonitor(config=test_config, data_provider=real_data_provider)
    return {'position_monitor': position_monitor}
```

## How to Run Specific Test Tiers

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

### Run Specific Test File
```bash
python -m pytest tests/unit/test_position_monitor_unit.py -v
```

## Smart Skipping Logic

E2E tests are automatically skipped if:
- Unit tests < 80% passing
- Integration tests < 80% passing

This prevents wasting time on E2E tests when the foundation is broken.

## Legacy Script Migration

### Scripts Moved to Legacy:
- `monitor_quality_gates.py` → replaced by unit tests for position/exposure/pnl
- `test_config_and_data_validation.py` → replaced by config + data provider unit tests
- `test_async_ordering_quality_gates.py` → moved to integration tests
- `test_tight_loop_quality_gates.py` → moved to integration tests
- `test_e2e_backtest_flow.py` → moved to integration tests

### Migration Timeline:
1. **Phase 1**: Create new unit/integration/e2e structure ✅
2. **Phase 2**: Update quality gate runner ✅
3. **Phase 3**: Move legacy scripts ✅
4. **Phase 4**: Update documentation ✅
5. **Phase 5**: Deprecate legacy scripts (future)

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
4. Add to `e2e_strategies` category

## Quality Gate Categories

### Critical Categories (Must Pass):
- `docs_validation`: Documentation structure validation
- `docs`: Documentation link validation
- `configuration`: Configuration validation
- `unit`: Unit tests - component isolation
- `integration`: Integration alignment validation
- `integration_data_flows`: Component data flow validation
- `data_loading`: Data provider validation
- `env_config_sync`: Environment variable sync validation
- `logical_exceptions`: Logical exception validation
- `mode_agnostic_design`: Mode-agnostic design validation
- `health`: Health system validation
- `repo_structure`: Repository structure validation

### Non-Critical Categories (Optional):
- `e2e_strategies`: E2E strategy tests (run only if foundation solid)
- `performance`: Performance validation
- `coverage`: Test coverage analysis

### Legacy Categories (Deprecated):
- `strategy`: Strategy validation (legacy)
- `components`: Component validation (legacy)

## Expected Outcomes

### Before Refactor:
- **2/23 passing (8.7%)**
- 40+ scripts, poorly organized
- Cascading failures hide root causes
- Can't identify which component broken
- Tests take 150+ seconds to run
- Most failures due to integration issues

### After Refactor:
- **Clear tier-based results**: Unit (8 tests) → Integration (5 tests) → E2E (4 tests)
- **Pinpoint failures**: Unit tests identify exact component issues
- **Data flow validation**: Integration tests validate WORKFLOW_GUIDE.md patterns
- **Meaningful E2E**: Only run when foundation solid
- **Faster execution**: Unit tests run in parallel (~10s), skip E2E if foundation broken
- **Expected passing rate**: 80%+ for unit tests, 70%+ for integration, E2E depends on fixes

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
