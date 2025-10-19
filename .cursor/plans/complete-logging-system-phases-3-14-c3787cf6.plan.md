<!-- c3787cf6-9f78-453b-85c1-51cb54f7ca3c e67c90c5-7de6-409c-acdb-69141598af6e -->
# Complete Unified Execution Flow and Logging System (Phases 3-14)

**Status**: Phases 1 & 2 ✅ COMPLETE | Phases 3-14 → In Progress

## Completed (Phases 1-2)

- ✅ ExecutionHandshake model created
- ✅ All 12 domain event models created
- ✅ Error codes registry created
- ✅ Order model updated with expected_deltas
- ✅ Trade model deleted
- ✅ LogDirectoryManager created
- ✅ DomainEventLogger created
- ✅ StructuredLogger updated

---

## PHASE 3: Strategy Manager & All Strategies (11 files)

### Base Strategy Manager

**File**: `backend/src/basis_strategy_v1/core/components/strategy_manager.py`

**Changes**:

- Update `__init__` to accept `correlation_id`, `pid`, `log_dir` parameters
- Initialize `StructuredLogger` with new parameters
- Initialize `DomainEventLogger`
- Add `_calculate_expected_deltas(order_params)` method dispatcher
- Add operation-specific delta calculators:
  - `_calculate_spot_trade_deltas()` - price * amount calculation
  - `_calculate_perp_trade_deltas()` - similar to spot
  - `_calculate_supply_deltas()` - uses AAVE supply index from utility_manager
  - `_calculate_borrow_deltas()` - similar to supply
  - `_calculate_repay_deltas()` - reverse of borrow
  - `_calculate_withdraw_deltas()` - reverse of supply
  - `_calculate_stake_deltas()` - uses staking rate/conversion
  - `_calculate_unstake_deltas()` - reverse of stake
  - `_calculate_swap_deltas()` - uses DEX pricing
  - `_calculate_transfer_deltas()` - 1:1 movement
- Update all error logging with error codes (STRAT-001, STRAT-002, STRAT-003)

### Pure Lending Strategies (2 files)

**Files**:

- `backend/src/basis_strategy_v1/core/strategies/pure_lending_usdt_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/pure_lending_eth_strategy.py`

**Changes** (both files):

- Update ALL order creation methods to populate new Order fields
- Calculate `expected_deltas` using utility_manager AAVE supply index
- Generate `operation_id` using `uuid.uuid4().hex`
- Populate `source_venue`, `target_venue`, `source_token`, `target_token`
- Add `operation_details` with AAVE index, health factor, etc.
- Update `_create_entry_full_orders()`, `_create_exit_partial_orders()`, etc.

### Basis Trading Strategies (2 files)

**Files**:

- `backend/src/basis_strategy_v1/core/strategies/btc_basis_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/eth_basis_strategy.py`

**Changes** (both files):

- Update spot trade order creation with expected_deltas
- Update perp trade order creation with expected_deltas
- Update transfer order creation with expected_deltas
- Populate all new Order fields for each operation
- Handle BTC/ETH-specific pricing

### ETH Strategies (3 files)

**Files**:

- `backend/src/basis_strategy_v1/core/strategies/eth_leveraged_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/eth_staking_only_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_strategy.py`

**Changes**:

- Update staking order creation with ETH → stETH/weETH conversion deltas
- Update atomic group orders with `atomic_group_id` and `sequence_in_group`
- Calculate expected_deltas for all operations in atomic groups
- Populate all new Order fields

### Remaining Strategies (3 files)

**Files**:

- `backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_no_leverage_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/ml_btc_directional_btc_margin_strategy.py`
- `backend/src/basis_strategy_v1/core/strategies/ml_btc_directional_usdt_margin_strategy.py`

**Changes**: Same pattern as above for their respective operations

---

## PHASE 4: Execution Manager (3 files)

### Rename and Refactor VenueManager

**File**: `backend/src/basis_strategy_v1/core/execution/execution_manager.py` → `execution_manager.py`

**Changes**:

- **RENAME** file: `execution_manager.py` → `execution_manager.py`
- **RENAME** class: `VenueManager` → `ExecutionManager`
- **REMOVE** all Trade imports (line 19: `from ...core.models.trade import Trade`)
- Update `__init__` to accept `correlation_id`, `pid`, `log_dir`
- Initialize `StructuredLogger` with new parameters
- Initialize `DomainEventLogger`
- **CHANGE** method signature: `process_instructions(instructions)` → `process_orders(timestamp, orders: List[Order]) -> List[ExecutionHandshake]`
- Add `_process_single_order(order)` method
- Add `_process_atomic_group(orders)` method
- Add `_log_operation_execution(handshake, order)` - logs OperationExecutionEvent
- Add `_log_atomic_group_execution(handshakes, orders)` - logs AtomicOperationGroupEvent
- Add `_log_tight_loop_execution(order, handshake, reconciliation_success)` - logs TightLoopExecutionEvent
- Add `_convert_deltas_to_structured_format(deltas)` - converts simple dict to structured list
- **REMOVE** `_convert_trade_to_execution_deltas()` method (legacy Trade conversion)
- Update `_reconcile_with_retry()` to use ExecutionHandshake
- Update all error logging with error codes (EXEC-001 through EXEC-008)

### Update Venue Interface Manager

**File**: `backend/src/basis_strategy_v1/core/execution/venue_interface_manager.py`

**Changes**:

- **REMOVE** all Trade imports
- Update `route_to_venue(order: Order) -> ExecutionHandshake` return type
- Update `_route_to_cex()` return type
- Update `_route_to_onchain()` return type
- Update `_route_to_transfer()` return type
- Update error handling with error codes (VEN-001 through VEN-006)

### Update Execution Module Init

**File**: `backend/src/basis_strategy_v1/core/execution/__init__.py`

**Changes**:

- Remove `from .execution_manager import VenueManager`
- Add `from .execution_manager import ExecutionManager`
- Update `__all__` export list

---

## PHASE 5: All Venue Interfaces (6 files)

### Base Interface

**File**: `backend/src/basis_strategy_v1/core/interfaces/base_execution_interface.py`

**Changes**:

- Remove Trade imports
- Update all abstract method return types to `ExecutionHandshake`

### CEX Interface

**File**: `backend/src/basis_strategy_v1/core/interfaces/cex_execution_interface.py`

**Changes**:

- Remove Trade imports
- Update `execute_trade() -> ExecutionHandshake`
- Update `_execute_backtest_trade() -> ExecutionHandshake`
- Update `_execute_live_trade() -> ExecutionHandshake`
- Update all execution methods

### OnChain Interface

**File**: `backend/src/basis_strategy_v1/core/interfaces/onchain_execution_interface.py`

**Changes**:

- Remove Trade imports
- Update all methods: `execute_supply()`, `execute_borrow()`, `execute_stake()` → `ExecutionHandshake`
- Update backtest and live execution methods

### Transfer Interface

**File**: `backend/src/basis_strategy_v1/core/interfaces/transfer_execution_interface.py`

**Changes**:

- Remove Trade imports
- Update `execute_transfer() -> ExecutionHandshake`

### Interface Factory & Init (2 files)

**Files**:

- `backend/src/basis_strategy_v1/core/interfaces/venue_interface_factory.py`
- `backend/src/basis_strategy_v1/core/interfaces/__init__.py`

**Changes**: Remove Trade references, update type hints

---

## PHASE 6: All Core Components (6 files)

### Position Monitor

**File**: `backend/src/basis_strategy_v1/core/components/position_monitor.py`

**Changes**:

- Update `__init__` to accept `correlation_id`, `pid`, `log_dir`
- Initialize `StructuredLogger` with new parameters
- Initialize `DomainEventLogger`
- Add `_log_position_snapshot()` method
- Call after every position update: `self.domain_event_logger.log_position_snapshot(PositionSnapshot(...))`
- Update error logging with error codes (POS-001 through POS-005)

### Exposure Monitor

**File**: `backend/src/basis_strategy_v1/core/components/exposure_monitor.py`

**Changes**:

- Update `__init__` to accept `correlation_id`, `pid`, `log_dir`
- Initialize loggers
- Add `_log_exposure_snapshot()` method
- Call after every exposure calculation
- Update error logging with error codes (EXP-001 through EXP-005)

### Risk Monitor

**File**: `backend/src/basis_strategy_v1/core/components/risk_monitor.py`

**Changes**:

- Update `__init__` to accept `correlation_id`, `pid`, `log_dir`
- Initialize loggers
- Add `_log_risk_assessment()` method
- Call after every risk calculation
- Update error logging with error codes (RISK-001 through RISK-006)

### PnL Monitor

**File**: `backend/src/basis_strategy_v1/core/components/pnl_monitor.py`

**Changes**:

- Update `__init__` to accept `correlation_id`, `pid`, `log_dir`
- Initialize loggers
- Add `_log_pnl_calculation()` method
- Call after every P&L calculation
- Update error logging with error codes (PNL-001 through PNL-005)

### Position Update Handler

**File**: `backend/src/basis_strategy_v1/core/components/position_update_handler.py`

**Changes**:

- Update `__init__` to accept `correlation_id`, `pid`, `log_dir`
- Initialize loggers
- Add `_log_reconciliation_event()` method
- Call after every reconciliation
- Update tight loop logic to work with ExecutionManager
- Update error logging with error codes

### Components Init

**File**: `backend/src/basis_strategy_v1/core/components/__init__.py`

**Changes**: Remove Trade references

---

## PHASE 7: Event Engine & Services (4 files)

### Event Driven Strategy Engine

**File**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py`

**Changes**:

- At `__init__`: Generate `correlation_id = uuid.uuid4().hex`
- Get `pid = os.getpid()`
- Create log directory:
```python
from ...infrastructure.logging.log_directory_manager import LogDirectoryManager
self.log_dir = LogDirectoryManager.create_run_logs(
    correlation_id=self.correlation_id,
    pid=self.pid,
    mode=self.mode,
    strategy=self.strategy_name,
    capital=self.initial_capital
)
```

- Pass `correlation_id`, `pid`, `log_dir` to ALL component initializations
- **RENAME** attribute: `self.execution_manager` → `self.execution_manager`
- **UPDATE** import: `from ..execution.execution_manager import ExecutionManager`
- Remove Trade imports
- Update `_process_strategy_decision()` to handle `List[ExecutionHandshake]`
- Update error logging with error codes (ENGINE-001 through ENGINE-004)

### Backtest Service

**File**: `backend/src/basis_strategy_v1/core/services/backtest_service.py`

**Changes**:

- Generate `correlation_id` before creating engine (if not already done by engine)
- Remove Trade references
- Update result processing

### Live Service

**File**: `backend/src/basis_strategy_v1/core/services/live_service.py`

**Changes**:

- Generate `correlation_id` before creating engine (if not already done by engine)
- Remove Trade references
- Update result processing

### API Main

**File**: `backend/src/basis_strategy_v1/api/main.py`

**Changes**:

- Generate `correlation_id` for each request
- Initialize `StructuredLogger` for API: `api.log` in logs/{correlation_id}/{pid}/
- Add structured logging for requests/responses
- Add error logging with stack traces for exceptions
- Update startup/shutdown logging

---

## PHASE 8: Configuration (12 files)

### Config Models

**File**: `backend/src/basis_strategy_v1/infrastructure/config/models.py`

**Changes**:

- Update `VenueManagerConfig` → `ExecutionManagerConfig` (or rename field)
- Remove Trade references

### All Mode Config Files (10 files)

**Files**: All YAML files in `configs/modes/`

**Changes** (all files):

- Rename `execution_manager:` → `execution_manager:` in component_config
- Keep all timeout/retry parameters unchanged

**Example**:

```yaml
component_config:
  execution_manager:  # RENAMED FROM execution_manager
    execution_timeout: 30
    max_retries: 3
```

### .gitignore

**File**: `.gitignore`

**Changes**:

- Remove `backend/logs/`
- Add `logs/` (root level)

---

## PHASE 9: Documentation - Component Specs (14 files)

### Core Component Specs (6 files)

**Files**:

- `docs/specs/01_POSITION_MONITOR.md`
- `docs/specs/02_EXPOSURE_MONITOR.md`
- `docs/specs/03_RISK_MONITOR.md`
- `docs/specs/04_PNL_MONITOR.md`
- `docs/specs/05_STRATEGY_MANAGER.md`
- `docs/specs/11_POSITION_UPDATE_HANDLER.md`

**Changes** (all files):

- Add "Domain Event Logging" section
- Document relevant event schema (PositionSnapshot, ExposureSnapshot, etc.)
- Update initialization signature to include correlation_id/pid/log_dir
- Add error code documentation for component
- Update examples with new logging patterns

### Execution Specs (3 files)

**File**: `docs/specs/06_VENUE_MANAGER.md` → **RENAME** to `docs/specs/06_EXECUTION_MANAGER.md`

**Changes**:

- Rename throughout: VenueManager → ExecutionManager
- Remove Trade references
- Add ExecutionHandshake documentation
- Add domain event logging section (OperationExecutionEvent, AtomicOperationGroupEvent, TightLoopExecutionEvent)
- Update tight loop flow diagrams
- Add error codes (EXEC-001 through EXEC-008)
- Update method signatures and examples

**Files**:

- `docs/specs/07_VENUE_INTERFACE_MANAGER.md`
- `docs/specs/07A_VENUE_INTERFACES.md`

**Changes**: Remove Trade, update to ExecutionHandshake, add error codes

### Other Component Specs (5 files)

**Files**:

- `docs/specs/08_EVENT_LOGGER.md`
- `docs/specs/13_BACKTEST_SERVICE.md`
- `docs/specs/14_LIVE_TRADING_SERVICE.md`
- `docs/specs/15_EVENT_DRIVEN_STRATEGY_ENGINE.md`
- `docs/specs/5B_BASE_STRATEGY_MANAGER.md`

**Changes**: Update with new logging, ExecutionManager, correlation_id generation

---

## PHASE 10: Documentation - Strategy Specs (9 files)

**Files**: All 9 files in `docs/specs/strategies/`

**Changes** (all files):

- Update order creation examples with expected_deltas calculation
- Show all new Order fields populated
- Update execution flow to use ExecutionHandshake
- Add operation-specific examples (AAVE index for lending, staking rates for ETH, etc.)

---

## PHASE 11: Documentation - Root Docs (13 files)

### New Documentation

**File**: `docs/LOGGING_GUIDE.md` ✨ **CREATE NEW**

**Contents**:

- Log directory structure: `logs/{correlation_id}/{pid}/`
- Component log files (api.log, position_monitor.log, etc.)
- Domain event JSONL files (all 12 types)
- Complete event schemas with examples
- Operation types documentation
- Atomic group logging
- Error code registry (all codes documented)
- Structured logging patterns
- Stack trace requirements
- Timestamp strategy (engine vs UTC)
- Debugging workflows
- Log querying examples with jq/grep

### Major Architecture Docs (7 files)

**Files**:

- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`
- `docs/ARCHITECTURAL_DECISION_RECORDS.md`
- `docs/TIGHT_LOOP_ARCHITECTURE.md`
- `docs/ERROR_HANDLING_PATTERNS.md`
- `docs/HEALTH_ERROR_SYSTEMS.md`
- `docs/WORKFLOW_GUIDE.md`
- `docs/ORDER_TRADE_EXECUTION_DELTAS_FLOW.md`

**Changes**: Comprehensive updates to remove Trade, add ExecutionHandshake, rename VenueManager → ExecutionManager, add logging architecture, add error codes, update all diagrams

### Supporting Docs (6 files)

**Files**:

- `docs/MODES.md`
- `docs/STRATEGY_MODES.md`
- `docs/MODE_SPECIFIC_BEHAVIOR_GUIDE.md`
- `docs/COMPONENT_SPECS_INDEX.md`
- `docs/CODE_STRUCTURE_PATTERNS.md`
- `docs/TARGET_REPOSITORY_STRUCTURE.md`

**Changes**: Update references to ExecutionManager, new logging patterns, config changes

---

## PHASE 12: Testing (8 new files)

### New Unit Tests (5 files)

1. `tests/unit/models/test_execution.py` - ExecutionHandshake validation
2. `tests/unit/models/test_domain_events.py` - All 12 domain event models
3. `tests/unit/logging/test_log_directory_manager.py` - Directory creation, metadata
4. `tests/unit/logging/test_domain_event_logger.py` - JSONL writing
5. `tests/unit/components/test_strategy_manager_deltas.py` - Expected deltas calculation

### New Integration Tests (3 files)

6. `tests/integration/test_execution_flow.py` - Order → ExecutionHandshake flow
7. `tests/integration/test_structured_logging.py` - Log directory, event files
8. `tests/integration/test_atomic_operations.py` - Atomic groups

### Update Existing Tests

- Search all test files for Trade or VenueManager
- Replace with ExecutionHandshake and ExecutionManager
- Update mock return values
- Update assertions

---

## PHASE 13: Validation & Cleanup

### Pure Lending USDT End-to-End Test

1. Stop any running servers: `./platform.sh stop`
2. Start backend: `./platform.sh backtest`
3. Run backtest via curl (from test_initial_capital_logging.sh)
4. Verify log structure exists: `logs/{correlation_id}/{pid}/`
5. Check all log files created
6. Verify SUPPLY operation logged correctly
7. Verify aUSDT calculation uses AAVE index
8. Verify expected_deltas matches actual_deltas

### Run Full Test Suite

```bash
cd tests
pytest -v --cov=backend/src/basis_strategy_v1 --cov-report=html
```

- Target: 80%+ coverage
- Zero Trade references
- All ExecutionManager references correct

### Run Quality Gates

```bash
python tests/quality_gates/run_quality_gates.py --all
```

---

## Implementation Priority

1. **Phase 3**: Strategy Manager + All Strategies (foundation for expected_deltas)
2. **Phase 4**: Execution Manager (core execution flow)
3. **Phase 5**: Venue Interfaces (execution layer)
4. **Phase 6**: Core Components (logging integration)
5. **Phase 7**: Event Engine + Services (orchestration)
6. **Phase 8**: Configuration (deployment support)
7. **Phase 9-11**: Documentation (completeness)
8. **Phase 12**: Testing (validation)
9. **Phase 13**: End-to-End Validation (quality gate)

### To-dos

- [ ] Update StrategyManager with correlation_id/pid/log_dir, add all _calculate_*_deltas methods, integrate DomainEventLogger
- [ ] Update all 10 strategy implementations to calculate expected_deltas and populate new Order fields
- [ ] Rename execution_manager.py to execution_manager.py, remove Trade imports, update to ExecutionHandshake, add domain event logging
- [ ] Update all 6 venue interface files to remove Trade and return ExecutionHandshake
- [ ] Update all 6 core components with correlation_id/pid/log_dir, integrate DomainEventLogger, add error codes
- [ ] Update EventDrivenStrategyEngine with correlation_id generation and log directory creation, update services and API
- [ ] Update all 10 mode YAML configs to rename execution_manager to execution_manager, update .gitignore
- [ ] Update 14 component spec docs with domain event logging, ExecutionManager rename, error codes
- [ ] Update 9 strategy spec docs with expected_deltas examples and ExecutionHandshake flow
- [ ] Create LOGGING_GUIDE.md and update 12 root documentation files with new architecture
- [ ] Create 8 new test files and update existing tests to use ExecutionHandshake and ExecutionManager
- [ ] Run Pure Lending USDT end-to-end test, full test suite, and quality gates for final validation