<!-- b836a230-e599-4243-854c-58988cc8908b 1dbf4aaa-c146-4531-9847-d55c3133e484 -->
# Data Provider Architecture Refactor Plan

## Overview

Refactor data provider to separate data source mode (csv vs db) from execution mode (backtest vs live), eliminate startup data loading in backtest mode, and implement on-demand data loading with date range validation.

## Core Architectural Changes

### 1. New Environment Variable: BASIS_DATA_MODE

- Add `BASIS_DATA_MODE` (values: `csv` or `db`) to control data source
- **Critical**: This has NOTHING to do with data persistence or execution/venue routing
- Only controls where DataProvider loads data from in backtest mode
- Fail-fast validation at startup (no default value)
- Already added to env files: `.env.dev`, `.env.staging`, `.env.production`, `env.unified`

### 2. Eliminate Confusion: startup_mode → execution_mode

**Current Problem**: `startup_mode` parameter conflates execution mode with data source
**Solution**:

- Remove `startup_mode` parameter entirely from `data_provider_factory.py`
- Use `BASIS_EXECUTION_MODE` env var directly (backtest vs live)
- Use `BASIS_DATA_MODE` env var for data source (csv vs db)
- `db` mode raises `NotImplementedError` (future implementation)

### 3. Data Loading Timing Changes

**Current (Broken)**: Load all data at server startup in `main.py` lifespan
**New (Correct)**:

- **Startup**: No data loading, only validate environment variables and config
- **Backtest API Call**: Load data on-demand based on strategy mode + date range
- **Live Mode**: Validate API connections at startup (no data loading)

### 4. Date Range Validation Strategy

- Keep `BASIS_DATA_START_DATE` and `BASIS_DATA_END_DATE` as "available data range"
- At backtest API call: Validate requested date range ⊆ available range
- Reject requests outside available range immediately (fail-fast)
- Quality Gate Phase 2: Validate data loading for ALL modes to ensure deployment readiness

## Implementation Steps

### Step 1: Update Environment Variable Infrastructure

**File: `env.unified`**

- Add `BASIS_DATA_MODE` documentation (already exists, just verify)

**File: `docs/ENVIRONMENT_VARIABLES.md`**

- Document `BASIS_DATA_MODE=csv|db`
- Clarify it only controls data source, NOT persistence/execution
- Add fail-fast validation requirement

**File: `backend/src/basis_strategy_v1/api/main.py`**

- Add `BASIS_DATA_MODE` to required env vars in `validate_core_startup_config()`
- Remove data provider initialization from `lifespan()` startup
- Remove `get_data_provider()` call at startup
- Remove `_validate_data_at_startup()` call

**File: `backend/src/basis_strategy_v1/infrastructure/config/config_validator.py`**

- Add `BASIS_DATA_MODE` to required environment variables list
- Add validation: must be `csv` or `db`

### Step 2: Refactor Data Provider Factory

**File: `backend/src/basis_strategy_v1/infrastructure/data/data_provider_factory.py`**

- Remove `startup_mode` parameter
- Add `execution_mode` parameter (from `BASIS_EXECUTION_MODE` env var)
- Add `data_mode` parameter (from `BASIS_DATA_MODE` env var)
- Factory logic:
- If `execution_mode == 'backtest'` and `data_mode == 'csv'`: Return `HistoricalDataProvider`
- If `execution_mode == 'backtest'` and `data_mode == 'db'`: Raise `NotImplementedError`
- If `execution_mode == 'live'`: Return `LiveDataProvider` (data_mode irrelevant)
- Update docstring to clarify new architecture

### Step 3: Update HistoricalDataProvider

**File: `backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py`**

- Remove `execution_mode` parameter from `__init__` (always backtest if using this class)
- Remove immediate data loading from `__init__`
- Add new method: `load_data_for_backtest(mode: str, start_date: str, end_date: str)`
- Validates date range against `BASIS_DATA_START_DATE` and `BASIS_DATA_END_DATE`
- Loads only data required for the specific strategy mode (from `data_requirements` in config)
- Validates loaded data covers the requested date range
- Raises `DataProviderError` with specific error codes if validation fails
- Update `_validate_backtest_dates()` to use provided dates instead of instance attributes
- Keep mode-specific loading logic in `_load_data_for_mode()` but make it accept parameters

### Step 4: Update LiveDataProvider

**File: `backend/src/basis_strategy_v1/infrastructure/data/live_data_provider.py`**

- Keep existing structure (live mode doesn't use BASIS_DATA_MODE)
- Ensure connection validation happens at initialization
- No changes to data loading logic

### Step 5: Update API Dependencies

**File: `backend/src/basis_strategy_v1/api/dependencies.py`**

- Update `get_data_provider()` to NOT load data at call time
- Change to factory function that creates provider instances on-demand
- Remove `@lru_cache()` decorator (no longer singleton)
- Accept `mode`, `start_date`, `end_date` parameters for backtest
- For backtest: Create provider, call `load_data_for_backtest()`, return
- For live: Create provider with mode-specific requirements, return

### Step 6: Update Backtest API Route

**File: `backend/src/basis_strategy_v1/api/routes/backtest.py`** (need to check if exists)

- In backtest submission endpoint:
- Get `BASIS_EXECUTION_MODE` and `BASIS_DATA_MODE` from env
- Validate requested date range against `BASIS_DATA_START_DATE`/`BASIS_DATA_END_DATE`
- Create data provider on-demand with strategy mode + date range
- Pass data provider to backtest service
- Handle `DataProviderError` exceptions with proper error responses

### Step 7: Update Health Check System

**File: `backend/src/basis_strategy_v1/core/health/component_health.py`**

- Update `DataProviderHealthChecker` to handle non-loaded state
- Add check: "is data loaded?" → if no, report "not_ready"
- Add check: "environment variables set?" → validate `BASIS_DATA_MODE`

**File: `backend/src/basis_strategy_v1/core/health/unified_health_manager.py`**

- Update `_check_data_provider()` to handle uninitialized state
- Report data provider as "healthy" if env vars valid, even without loaded data
- For backtest mode: Check if data provider can be created successfully

**File: `backend/src/basis_strategy_v1/api/routes/health.py`**

- No changes needed (uses unified health manager)

### Step 8: Update Documentation

**File: `docs/specs/09_DATA_PROVIDER.md`**

- Update "Three-Mode Data Architecture" section:
- Remove `startup_mode` references
- Add `BASIS_DATA_MODE` (csv vs db) and `BASIS_EXECUTION_MODE` (backtest vs live)
- Document: csv for file-based, db for database (not implemented)
- Update "Initialization" section: No data loading at init for backtest mode
- Update "Data Loading" section: On-demand loading during API calls
- Add section: "Date Range Validation with Environment Variables"
- Update factory pattern documentation

**File: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`**

- Section 6.1 "Infrastructure Configuration Elimination":
- Add `BASIS_DATA_MODE` to environment variables list
- Clarify: Only controls data source, NOT persistence/execution
- Update configuration architecture section if needed

**File: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`**

- Add decision record: "Separate Data Source from Execution Mode"
- Document why `BASIS_DATA_MODE` is separate from `BASIS_EXECUTION_MODE`
- Document on-demand data loading architecture

**File: `docs/USER_GUIDE.md`**

- Update environment setup section with `BASIS_DATA_MODE`
- Update backtest workflow to explain on-demand data loading
- Document date range validation behavior

**File: `docs/specs/17_HEALTH_ERROR_SYSTEMS.md`**

- Update data provider health checks documentation
- Add error codes for date range validation failures
- Document uninitialized data provider health status

**File: `docs/DEPLOYMENT_GUIDE.md`**

- Add `BASIS_DATA_MODE` to environment variable configuration
- Update deployment checklist to include data mode validation

### Step 9: Update Quality Gates (Phase 2)

**File: `scripts/run_quality_gates.py`**

- Update Phase 2 validation: `validate_phase_2_gates()`
- Remove startup data loading validation
- Add: Test data loading for ALL strategy modes (pure_lending, btc_basis, eth_leveraged, usdt_market_neutral)
- Add: Validate each mode can load data within `BASIS_DATA_START_DATE` to `BASIS_DATA_END_DATE`
- Add: Test date range validation (reject out-of-range requests)
- Add: Validate `BASIS_DATA_MODE` environment variable
- Add: Test data provider health check with uninitialized state
- Ensure at least 80% of Phase 2 gates pass

**Create new test script: `scripts/test_data_provider_refactor_quality_gates.py`**
-

### To-dos

- [ ] Update environment variable infrastructure: Add BASIS_DATA_MODE validation to config_validator.py, update ENVIRONMENT_VARIABLES.md documentation, verify env.unified and .env.* files
- [ ] Remove data loading from main.py lifespan: Remove get_data_provider() and _validate_data_at_startup() calls from startup, add BASIS_DATA_MODE to validate_core_startup_config()
- [ ] Refactor data_provider_factory.py: Remove startup_mode parameter, add execution_mode and data_mode parameters, update factory logic for csv/db/live modes
- [ ] Update HistoricalDataProvider: Remove execution_mode parameter, add load_data_for_backtest() method for on-demand loading, update date validation logic
- [ ] Update api/dependencies.py: Remove @lru_cache from get_data_provider(), make it accept mode/start_date/end_date parameters, implement on-demand data loading
- [ ] Update backtest API route: Add date range validation against BASIS_DATA_START_DATE/END_DATE, create data provider on-demand with strategy mode and dates, handle DataProviderError exceptions
- [ ] Update health check system: Modify DataProviderHealthChecker and unified_health_manager.py to handle uninitialized data provider state, add BASIS_DATA_MODE validation
- [ ] Update docs/specs/09_DATA_PROVIDER.md: Document BASIS_DATA_MODE, remove startup_mode references, add on-demand loading section, update factory pattern docs
- [ ] Update REFERENCE_ARCHITECTURE_CANONICAL.md, REFERENCE_ARCHITECTURE_CANONICAL.md, USER_GUIDE.md, DEPLOYMENT_GUIDE.md: Add BASIS_DATA_MODE documentation, clarify separation from execution mode
- [ ] Update docs/specs/17_HEALTH_ERROR_SYSTEMS.md: Document data provider health checks for uninitialized state, add error codes for date validation failures
- [ ] Update scripts/run_quality_gates.py Phase 2: Test data loading for ALL modes, validate date range rejection, test BASIS_DATA_MODE validation, ensure no startup loading
- [ ] Create scripts/test_data_provider_refactor_quality_gates.py: Comprehensive tests for new architecture including env validation, on-demand loading, date validation, health checks
- [ ] Grep and fix all references: Search for startup_mode, update health checks, fix get_data_provider() calls, ensure no conflicts in backend/ and docs/
- [ ] Run quality gates: Execute test_data_provider_refactor_quality_gates.py and run_quality_gates.py --phase 2 to validate data provider health and date validation