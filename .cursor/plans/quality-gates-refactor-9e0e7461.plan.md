<!-- 9e0e7461-a98c-42db-9e1d-67a41f84f96c a7e0955c-b947-458e-8bb9-e904860127e0 -->
# Quality Gates Refactoring Plan

## Problem Statement

Current quality gates have massive codependency issues causing cascading failures:

- **2/23 passing (8.7%)** - but this is misleading
- Most tests are integration tests that fail if ANY component is broken
- Config/data bootstrap issues cause 10+ tests to fail immediately
- Duplicate category keys in `run_quality_gates.py`
- No clear component-level isolation

## Solution Approach

Restructure into 3 test tiers:

1. **Unit Tests** - One per component, mocked dependencies
2. **Integration Tests** - Validate component interactions per WORKFLOW_GUIDE.md
3. **E2E Tests** - Full strategy execution with real data (kept optional/non-critical until unit/integration pass)

## Implementation Steps

### Phase 1: Create Unit Test Framework (tests/unit/)

Create new directory structure:

```
scripts/
  unit_tests/
    __init__.py
    conftest.py  # Shared pytest fixtures
    test_position_monitor_unit.py
    test_exposure_monitor_unit.py
    test_risk_monitor_unit.py
    test_pnl_monitor_unit.py
    test_strategy_manager_unit.py
    test_execution_manager_unit.py
    test_data_provider_unit.py
    test_config_manager_unit.py
  integration_tests/
    __init__.py
    conftest.py
    test_data_flow_position_to_exposure.py
    test_data_flow_exposure_to_risk.py
    test_data_flow_risk_to_strategy.py
    test_data_flow_strategy_to_execution.py
    test_tight_loop_reconciliation.py
  e2e_tests/
    __init__.py
    test_pure_lending_usdt_e2e.py
    test_btc_basis_e2e.py
    test_eth_basis_e2e.py
    test_usdt_market_neutral_e2e.py
```

#### 1.1: Create Shared Fixtures (`tests/unit/conftest.py`)

Create pytest fixtures for:

- Mock config with all required fields
- Mock data provider with minimal test data
- Mock market data snapshots
- Mock position snapshots
- Mock utility manager

Use combination approach: mocks for speed, minimal real data files for validation.

Reference: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` for component initialization patterns

#### 1.2: Position Monitor Unit Test (`test_position_monitor_unit.py`)

Test ONLY PositionMonitor with mocked dependencies:

- **Test 1**: `collect_positions()` returns correct structure
- **Test 2**: State persistence across timesteps
- **Test 3**: AAVE balance conversion (aUSDT → USDT)
- **Test 4**: LST balance conversion (weETH → ETH)
- **Test 5**: Multi-venue position aggregation
- **Test 6**: Error handling for missing venue data

Reference: `docs/specs/01_POSITION_MONITOR.md`

#### 1.3: Exposure Monitor Unit Test (`test_exposure_monitor_unit.py`)

Test ONLY ExposureMonitor with mocked position data:

- **Test 1**: Asset filtering based on config
- **Test 2**: Net delta calculation in share class currency
- **Test 3**: Underlying balance calculation for derivatives
- **Test 4**: Per-venue exposure breakdown
- **Test 5**: Zero exposure handling
- **Test 6**: Missing price data graceful degradation

Reference: `docs/specs/02_EXPOSURE_MONITOR.md`

#### 1.4: Risk Monitor Unit Test (`test_risk_monitor_unit.py`)

Test ONLY RiskMonitor with mocked exposure data:

- **Test 1**: Max drawdown check
- **Test 2**: Leverage ratio calculation
- **Test 3**: Position limit validation
- **Test 4**: Risk breach detection
- **Test 5**: Mode-agnostic risk calculations
- **Test 6**: Fail-fast config access (no `.get()`)

Reference: `docs/specs/03_RISK_MONITOR.md`

#### 1.5: P&L Calculator Unit Test (`test_pnl_monitor_unit.py`)

Test ONLY PnLCalculator with mocked data:

- **Test 1**: Unrealized P&L calculation
- **Test 2**: Attribution P&L (lending vs funding vs staking)
- **Test 3**: Gas cost tracking
- **Test 4**: Total return percentage
- **Test 5**: Error code propagation
- **Test 6**: Share class currency conversion

Reference: `docs/specs/04_pnl_monitor.md`

#### 1.6: Strategy Manager Unit Test (`test_strategy_manager_unit.py`)

Test ONLY BaseStrategyManager and concrete implementations:

- **Test 1**: StrategyFactory creates correct manager for each mode
- **Test 2**: 5 standardized actions (open_position, close_position, rebalance, hedge, transfer)
- **Test 3**: Read-only behavior (no position updates)
- **Test 4**: Instruction block generation
- **Test 5**: Mode-specific strategy logic
- **Test 6**: Risk limit respect

Reference: `docs/specs/05_STRATEGY_MANAGER.md`, `docs/specs/5A_STRATEGY_FACTORY.md`, `docs/specs/5B_BASE_STRATEGY_MANAGER.md`

#### 1.7: Execution Manager Unit Test (`test_execution_manager_unit.py`)

Test ONLY VenueManager with mocked interfaces:

- **Test 1**: Instruction routing to correct interface
- **Test 2**: Sequential execution (one at a time)
- **Test 3**: Position reconciliation after execution
- **Test 4**: Error handling and retry logic
- **Test 5**: Transaction confirmation in live mode
- **Test 6**: Execution cost tracking

Reference: `docs/specs/06_VENUE_MANAGER.md`

#### 1.8: Data Provider Unit Test (`test_data_provider_unit.py`)

Test ONLY DataProvider with minimal test data:

- **Test 1**: Load data based on mode requirements
- **Test 2**: Fail-fast validation at startup
- **Test 3**: Price lookup for all assets
- **Test 4**: Funding rate lookup
- **Test 5**: AAVE index lookup
- **Test 6**: Graceful handling of missing optional data

Reference: `docs/specs/09_DATA_PROVIDER.md`

#### 1.9: Config Manager Unit Test (`test_config_manager_unit.py`)

Test ONLY ConfigManager:

- **Test 1**: Load base config (local.json)
- **Test 2**: Load mode config (modes/*.yaml)
- **Test 3**: Load venue config (venues/*.yaml)
- **Test 4**: Merge configs correctly
- **Test 5**: Environment switching (dev/staging/prod)
- **Test 6**: Fail-fast validation with Pydantic

Reference: `docs/specs/19_CONFIGURATION.md`

### Phase 2: Create Integration Tests (tests/integration/)

These validate component interactions per WORKFLOW_GUIDE.md patterns, using real data files.

#### 2.1: Data Flow Fixtures (`conftest.py`)

Create fixtures with minimal real data:

- Load actual config files (modes/pure_lending_usdt_usdt.yaml)
- Load minimal data slice (1 week: 2024-05-12 to 2024-05-19)
- Real DataProvider instance
- Real component instances (not mocked)

#### 2.2: Position → Exposure Integration (`test_data_flow_position_to_exposure.py`)

Validate WORKFLOW_GUIDE.md "Position Monitor → Exposure Monitor Workflow":

- **Test 1**: Position snapshot flows to exposure monitor
- **Test 2**: Asset filtering based on mode config
- **Test 3**: Net delta calculation matches expected
- **Test 4**: Per-venue breakdown aggregates correctly
- **Test 5**: Share class conversion accurate

Reference: `docs/WORKFLOW_GUIDE.md` lines 1621-1642

#### 2.3: Exposure → Risk Integration (`test_data_flow_exposure_to_risk.py`)

Validate WORKFLOW_GUIDE.md "Exposure Monitor → Risk Monitor Workflow":

- **Test 1**: Exposure report flows to risk monitor
- **Test 2**: Risk calculations based on actual exposure
- **Test 3**: Breach detection triggers correctly
- **Test 4**: Risk limits enforced
- **Test 5**: Mode-specific risk rules apply

Reference: `docs/WORKFLOW_GUIDE.md` lines 1644-1665

#### 2.4: Risk → Strategy Integration (`test_data_flow_risk_to_strategy.py`)

Validate WORKFLOW_GUIDE.md "Risk Monitor → Strategy Manager Workflow":

- **Test 1**: Risk assessment flows to strategy manager
- **Test 2**: Strategy decisions respect risk limits
- **Test 3**: Instruction blocks generated correctly
- **Test 4**: Mode-specific strategy logic applies
- **Test 5**: No-op when within safe limits

Reference: `docs/WORKFLOW_GUIDE.md` lines 1687-1710

#### 2.5: Strategy → Execution Integration (`test_data_flow_strategy_to_execution.py`)

Validate WORKFLOW_GUIDE.md "Strategy Manager → Execution Interfaces Workflow":

- **Test 1**: Instructions route to correct interfaces
- **Test 2**: Position monitor updates after execution
- **Test 3**: Sequential execution (no parallelism)
- **Test 4**: Reconciliation handshake completes
- **Test 5**: Event logging captures all actions

Reference: `docs/WORKFLOW_GUIDE.md` lines 1713-1741

#### 2.6: Tight Loop Reconciliation (`test_tight_loop_reconciliation.py`)

Validate REFERENCE_ARCHITECTURE_CANONICAL.md ADR-001:

- **Test 1**: Execution → Position Update → Reconciliation
- **Test 2**: Sequential tight loops (no race conditions)
- **Test 3**: State persistence across loops
- **Test 4**: Error recovery in tight loop
- **Test 5**: Live mode transaction confirmation

Reference: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 1, `docs/specs/15_EVENT_DRIVEN_STRATEGY_ENGINE.md` lines 131-180

### Phase 3: Refactor E2E Tests (scripts/e2e_tests/)

Move existing strategy tests here, mark as non-critical until unit/integration pass.

#### 3.1: Pure Lending E2E (`test_pure_lending_usdt_e2e.py`)

Refactor `test_pure_lending_usdt_quality_gates.py`:

- Keep full backtest execution with real data
- Validate 3-8% APY range
- Mark as **non-critical** in run_quality_gates.py
- Only run if unit + integration tests pass

#### 3.2: BTC Basis E2E (`test_btc_basis_e2e.py`)

Refactor `test_btc_basis_quality_gates.py`:

- Keep full backtest execution
- Validate funding rate calculations
- Mark as **non-critical**

#### 3.3: ETH Basis E2E (`test_eth_basis_e2e.py`)

Refactor `test_eth_basis_quality_gates.py`:

- Keep full backtest execution
- Validate LST mechanics
- Mark as **non-critical**

#### 3.4: USDT Market Neutral E2E (`test_usdt_market_neutral_e2e.py`)

Refactor `test_usdt_market_neutral_quality_gates.py`:

- Keep full backtest execution
- Validate full leverage + hedging
- Mark as **non-critical**

### Phase 4: Update Quality Gate Runner

#### 4.1: Fix Duplicate Categories

In `scripts/run_quality_gates.py`, remove duplicates:

- Line 60 vs 143: `'integration'` defined twice
- Line 105 vs 135: `'data_loading'` defined twice
- Line 67 vs 158: `'env_config_sync'` defined twice

#### 4.2: Reorganize Categories

Update `quality_gate_categories` dict:

```python
self.quality_gate_categories = {
    'unit': {
        'description': 'Unit Tests - Component Isolation',
        'scripts': [
            'unit_tests/test_position_monitor_unit.py',
            'unit_tests/test_exposure_monitor_unit.py',
            'unit_tests/test_risk_monitor_unit.py',
            'unit_tests/test_pnl_monitor_unit.py',
            'unit_tests/test_strategy_manager_unit.py',
            'unit_tests/test_execution_manager_unit.py',
            'unit_tests/test_data_provider_unit.py',
            'unit_tests/test_config_manager_unit.py'
        ],
        'critical': True
    },
    'integration': {
        'description': 'Integration Tests - Component Data Flows',
        'scripts': [
            'integration_tests/test_data_flow_position_to_exposure.py',
            'integration_tests/test_data_flow_exposure_to_risk.py',
            'integration_tests/test_data_flow_risk_to_strategy.py',
            'integration_tests/test_data_flow_strategy_to_execution.py',
            'integration_tests/test_tight_loop_reconciliation.py'
        ],
        'critical': True
    },
    'e2e': {
        'description': 'E2E Tests - Full Strategy Execution',
        'scripts': [
            'e2e_tests/test_pure_lending_usdt_e2e.py',
            'e2e_tests/test_btc_basis_e2e.py',
            'e2e_tests/test_eth_basis_e2e.py',
            'e2e_tests/test_usdt_market_neutral_e2e.py'
        ],
        'critical': False  # Only run after unit + integration pass
    },
    'docs': {
        'description': 'Documentation Validation',
        'scripts': [
            'test_docs_structure_validation_quality_gates.py',
            'test_docs_link_validation_quality_gates.py'
        ],
        'critical': True
    },
    'config': {
        'description': 'Configuration Validation',
        'scripts': [
            'validate_config_alignment.py',
            'test_env_config_usage_sync_quality_gates.py'
        ],
        'critical': True
    },
    'health': {
        'description': 'Health System Validation',
        'scripts': [],  # Built-in
        'critical': True
    },
    'coverage': {
        'description': 'Test Coverage Analysis',
        'scripts': ['analyze_test_coverage.py'],
        'critical': False
    }
}
```

#### 4.3: Update Execution Order

Run in dependency order:

1. **docs** (validate documentation)
2. **config** (validate configuration)
3. **unit** (validate components in isolation)
4. **integration** (validate component interactions)
5. **e2e** (validate full strategies - only if unit + integration pass)
6. **health** (validate health system)
7. **coverage** (analyze coverage)

#### 4.4: Add Smart Skipping

Skip E2E tests if unit or integration tests fail:

```python
if unit_passed < unit_total or integration_passed < integration_total:
    print("⚠️  Skipping E2E tests - unit or integration tests failing")
    skip_e2e = True
```

### Phase 5: Deprecate Old Quality Gates

Move to `scripts/deprecated/`:

- `monitor_quality_gates.py` (replaced by unit + integration tests)
- `test_tight_loop_quality_gates.py` (replaced by integration test)
- `test_async_ordering_quality_gates.py` (replaced by unit test for results store)
- `test_config_and_data_validation.py` (replaced by config unit test)
- `test_e2e_backtest_flow.py` (replaced by e2e tests)

Keep these for reference but exclude from run_quality_gates.py.

### Phase 6: Update Documentation

#### 6.1: Update QUALITY_GATES.md

Document new 3-tier structure:

- Unit test purpose and scope
- Integration test purpose and data flows
- E2E test purpose and when they run
- How to run each tier independently
- How to add new tests

#### 6.2: Update WEB_AGENT_31_TASK_PROMPT.md

Update quality gate status section:

- Document actual current status (2/23 passing)
- Explain new structure after refactor
- Update task priorities based on unit test failures

#### 6.3: Create Migration Guide

Document for developers:

- Where to find old tests (scripts/deprecated/)
- How to run new test tiers
- How to add component unit tests
- How to add integration tests for new data flows

## Expected Outcomes

### Before Refactor:

- **2/23 passing (8.7%)**
- Cascading failures hide root causes
- Can't identify which component is actually broken
- Integration tests dominate, unit tests absent

### After Refactor:

- **Clear component-level failures** (unit tests pinpoint exact issues)
- **Data flow validation** (integration tests validate interactions)
- **Meaningful E2E results** (only run when foundation is solid)
- **Faster test execution** (unit tests run in parallel, skip E2E if foundation broken)
- **80%+ passing rate** (unit tests focus on one thing, should mostly pass)

## Files to Create:

- `scripts/unit_tests/conftest.py`
- `scripts/unit_tests/test_position_monitor_unit.py`
- `scripts/unit_tests/test_exposure_monitor_unit.py`
- `scripts/unit_tests/test_risk_monitor_unit.py`
- `scripts/unit_tests/test_pnl_monitor_unit.py`
- `scripts/unit_tests/test_strategy_manager_unit.py`
- `scripts/unit_tests/test_execution_manager_unit.py`
- `scripts/unit_tests/test_data_provider_unit.py`
- `scripts/unit_tests/test_config_manager_unit.py`
- `scripts/integration_tests/conftest.py`
- `scripts/integration_tests/test_data_flow_position_to_exposure.py`
- `scripts/integration_tests/test_data_flow_exposure_to_risk.py`
- `scripts/integration_tests/test_data_flow_risk_to_strategy.py`
- `scripts/integration_tests/test_data_flow_strategy_to_execution.py`
- `scripts/integration_tests/test_tight_loop_reconciliation.py`
- `scripts/e2e_tests/test_pure_lending_usdt_e2e.py`
- `scripts/e2e_tests/test_btc_basis_e2e.py`
- `scripts/e2e_tests/test_eth_basis_e2e.py`
- `scripts/e2e_tests/test_usdt_market_neutral_e2e.py`
- `scripts/deprecated/` (directory for old tests)

## Files to Modify:

- `scripts/run_quality_gates.py` (fix duplicates, reorganize categories, add smart skipping)
- `docs/QUALITY_GATES.md` (document new structure)
- `.cursor/WEB_AGENT_31_TASK_PROMPT.md` (update status)

## Files to Move:

- `scripts/monitor_quality_gates.py` → `scripts/deprecated/`
- `scripts/test_tight_loop_quality_gates.py` → `scripts/deprecated/`
- `scripts/test_async_ordering_quality_gates.py` → `scripts/deprecated/`
- `scripts/test_config_and_data_validation.py` → `scripts/deprecated/`
- `scripts/test_e2e_backtest_flow.py` → `scripts/deprecated/`

### To-dos

- [ ] Create shared pytest fixtures in scripts/unit_tests/conftest.py with mocked config, data provider, and test data
- [ ] Create test_position_monitor_unit.py with 6 isolated tests for position collection, state persistence, and conversions
- [ ] Create test_exposure_monitor_unit.py with 6 isolated tests for asset filtering, net delta, and exposure calculations
- [ ] Create test_risk_monitor_unit.py with 6 isolated tests for risk calculations, breach detection, and fail-fast config
- [ ] Create test_pnl_monitor_unit.py with 6 isolated tests for P&L calculation, attribution, and error propagation
- [ ] Create test_strategy_manager_unit.py with 6 isolated tests for strategy factory, actions, and mode-specific logic
- [ ] Create test_execution_manager_unit.py with 6 isolated tests for routing, reconciliation, and error handling
- [ ] Create test_data_provider_unit.py with 6 isolated tests for data loading, validation, and graceful degradation
- [ ] Create test_config_manager_unit.py with 6 isolated tests for config loading, merging, and environment switching
- [ ] Create integration test fixtures in scripts/integration_tests/conftest.py with real data and components
- [ ] Create test_data_flow_position_to_exposure.py validating Position→Exposure workflow per WORKFLOW_GUIDE.md
- [ ] Create test_data_flow_exposure_to_risk.py validating Exposure→Risk workflow per WORKFLOW_GUIDE.md
- [ ] Create test_data_flow_risk_to_strategy.py validating Risk→Strategy workflow per WORKFLOW_GUIDE.md
- [ ] Create test_data_flow_strategy_to_execution.py validating Strategy→Execution workflow per WORKFLOW_GUIDE.md
- [ ] Create test_tight_loop_reconciliation.py validating tight loop architecture per ADR-001
- [ ] Move and refactor 4 strategy E2E tests to scripts/e2e_tests/ and mark as non-critical
- [ ] Fix duplicate category keys in run_quality_gates.py (integration, data_loading, env_config_sync)
- [ ] Reorganize quality_gate_categories dict with new unit/integration/e2e structure
- [ ] Add smart skipping logic to skip E2E tests if unit or integration tests fail
- [ ] Move 5 old quality gate scripts to scripts/deprecated/ directory
- [ ] Update QUALITY_GATES.md and WEB_AGENT_31_TASK_PROMPT.md with new structure and create migration guide