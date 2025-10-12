# Basis Strategy Test Suite

## Overview

This directory contains the complete test suite for the Basis Strategy project, organized into a conventional 3-tier testing structure that replaces the previous monolithic quality gates.

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
├── unit/                          # 8 component isolation tests
│   ├── conftest.py               # Shared pytest fixtures
│   ├── test_position_monitor_unit.py
│   ├── test_exposure_monitor_unit.py
│   ├── test_risk_monitor_unit.py
│   ├── test_pnl_calculator_unit.py
│   ├── test_strategy_manager_unit.py
│   ├── test_execution_manager_unit.py
│   ├── test_data_provider_unit.py
│   └── test_config_manager_unit.py
├── integration/                   # 5 component data flow tests
│   ├── conftest.py               # Real component fixtures
│   ├── test_data_flow_position_to_exposure.py
│   ├── test_data_flow_exposure_to_risk.py
│   ├── test_data_flow_risk_to_strategy.py
│   ├── test_data_flow_strategy_to_execution.py
│   └── test_tight_loop_reconciliation.py
└── e2e/                          # 4 strategy execution tests
    ├── test_pure_lending_e2e.py
    ├── test_btc_basis_e2e.py
    ├── test_eth_basis_e2e.py
    └── test_usdt_market_neutral_e2e.py
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
4. Add to `e2e_strategies` category

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

## Reference Documentation

- **Test Organization Guide**: `scripts/TEST_ORGANIZATION.md`
- **Component Workflows**: `docs/WORKFLOW_GUIDE.md`
- **Architecture Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`
- **Quality Gates**: `scripts/run_quality_gates.py`
