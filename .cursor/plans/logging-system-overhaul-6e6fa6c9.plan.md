<!-- 6e6fa6c9-347a-4fe4-bdd7-e590f938504c 6800009b-7eb6-4703-8fe2-3d9eb878525a -->
# EXHAUSTIVE Unified Execution Flow and Logging System Refactor

## Overview

Complete refactor combining execution flow improvements with logging system overhaul. This plan lists EVERY SINGLE FILE that needs to be created, modified, or deleted. NO backward compatibility - clean break from legacy Trade model.

**Total File Count**:

- **New Files**: 22
- **Deleted Files**: 2  
- **Modified Python Files**: 35
- **Modified Config Files**: 10
- **Modified Documentation Files**: 35
- **New Test Files**: 8
- **Total Files Affected**: 112 files

---

## PHASE 1: CORE DATA MODELS

### 1.1 CREATE New Model Files (5 files)

#### File 1: `backend/src/basis_strategy_v1/core/models/execution.py` ✨ NEW

**Purpose**: ExecutionHandshake model and OperationType/ExecutionStatus enums

```python
from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class OperationType(str, Enum):
    """All operation types supported"""
    # CEX
    SPOT_TRADE = "spot_trade"
    PERP_TRADE = "perp_trade"
    
    # DeFi
    SUPPLY = "supply"
    BORROW = "borrow"
    REPAY = "repay"
    WITHDRAW = "withdraw"
    STAKE = "stake"
    UNSTAKE = "unstake"
    SWAP = "swap"
    
    # Flash loans
    FLASH_BORROW = "flash_borrow"
    FLASH_REPAY = "flash_repay"
    
    # Transfers
    TRANSFER = "transfer"

class ExecutionStatus(str, Enum):
    """Execution status for handshakes"""
    CONFIRMED = "confirmed"
    PENDING = "pending"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class ExecutionHandshake(BaseModel):
    """Execution result from venue interface - REPLACES Trade"""
    operation_id: str
    status: ExecutionStatus
    actual_deltas: Dict[str, float]  # Simple runtime format
    execution_details: Dict[str, Any]
    fee_amount: float = 0.0
    fee_currency: str = "USDT"
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    submitted_at: datetime
    executed_at: Optional[datetime] = None
    venue_metadata: Dict[str, Any] = Field(default_factory=dict)
    simulated: bool = False
```

#### File 2: `backend/src/basis_strategy_v1/core/models/domain_events.py` ✨ NEW

**Purpose**: All Pydantic domain event models for JSONL logging

Contains:

- `PositionSnapshot`
- `ExposureSnapshot`
- `RiskAssessment`
- `PnLCalculation`
- `OrderEvent`
- `OperationExecutionEvent`
- `AtomicOperationGroupEvent`
- `ExecutionDeltaEvent`
- `ReconciliationEvent`
- `TightLoopExecutionEvent`
- `EventLoggingOperationEvent`
- `StrategyDecision`

#### File 3: `backend/src/basis_strategy_v1/core/errors/error_codes.py` ✨ NEW

**Purpose**: Static error code registry and ComponentError exception

```python
ERROR_REGISTRY = {
    'POS-001': 'Position reconciliation mismatch',
    'POS-002': 'Invalid position delta',
    'POS-003': 'Position state unavailable',
    'EXP-001': 'Exposure calculation failed',
    'EXP-002': 'Missing market data for exposure',
    'EXP-003': 'Position data unavailable',
    'RISK-001': 'Health factor calculation failed',
    'RISK-002': 'LTV ratio exceeds threshold',
    'RISK-003': 'Margin call triggered',
    'PNL-001': 'PnL calculation failed',
    'PNL-002': 'Missing price data',
    'EXEC-001': 'Order execution failed',
    'EXEC-002': 'Execution timeout',
    'EXEC-003': 'Tight loop reconciliation failed',
    'EXEC-004': 'System failure triggered',
    'EXEC-005': 'Atomic group execution failed',
    'VEN-001': 'Venue routing failed',
    'VEN-002': 'Venue timeout',
    'VEN-003': 'Venue unavailable',
    'LOG-001': 'Failed to write event file',
    'LOG-002': 'Event buffer overflow',
    'LOG-003': 'Log directory creation failed',
    'STRAT-001': 'Strategy decision failed',
    'STRAT-002': 'Expected deltas calculation failed',
    'STRAT-003': 'Invalid order generated',
}

class ComponentError(Exception):
    """Exception for critical component errors"""
    def __init__(self, error_code: str, message: str, component: str, severity: str):
        self.error_code = error_code
        self.message = message
        self.component = component
        self.severity = severity
        super().__init__(f"[{error_code}] {component}: {message}")
```

#### File 4: `backend/src/basis_strategy_v1/infrastructure/logging/log_directory_manager.py` ✨ NEW

**Purpose**: Manages logs/{correlation_id}/{pid}/ directory structure

Methods:

- `create_run_logs(correlation_id, pid, mode, strategy, capital) -> Path`
- Creates directory structure
- Writes run_metadata.json

#### File 5: `backend/src/basis_strategy_v1/infrastructure/logging/domain_event_logger.py` ✨ NEW

**Purpose**: Writes domain events to JSONL files

Methods for each event type:

- `log_operation_execution(event: OperationExecutionEvent)`
- `log_atomic_group(event: AtomicOperationGroupEvent)`
- `log_reconciliation(event: ReconciliationEvent)`
- `log_tight_loop_execution(event: TightLoopExecutionEvent)`
- `log_position_snapshot(event: PositionSnapshot)`
- `log_exposure_snapshot(event: ExposureSnapshot)`
- `log_risk_assessment(event: RiskAssessment)`
- `log_pnl_calculation(event: PnLCalculation)`
- `log_order_event(event: OrderEvent)`
- `log_execution_delta(event: ExecutionDeltaEvent)`
- `log_strategy_decision(event: StrategyDecision)`
- `log_event_logging_operation(event: EventLoggingOperationEvent)`

### 1.2 MODIFY Existing Model Files (2 files)

#### File 6: `backend/src/basis_strategy_v1/core/models/order.py` 🔧 MODIFY

**Changes**:

- Add `operation_id: str`
- Add `source_venue: str`
- Add `target_venue: str`
- Add `source_token: str`
- Add `target_token: str`
- Add `expected_deltas: Dict[str, float]`
- Add `operation_details: Dict[str, Any]`
- Update all validators
- Update `model_config`

#### File 7: `backend/src/basis_strategy_v1/core/models/__init__.py` 🔧 MODIFY

**Changes**:

- Remove `from .trade import Trade`
- Add `from .execution import ExecutionHandshake, OperationType, ExecutionStatus`
- Add `from .domain_events import *`
- Update `__all__` export list

### 1.3 DELETE Legacy Model Files (1 file)

#### File 8: `backend/src/basis_strategy_v1/core/models/trade.py` ❌ DELETE

**Action**: Complete deletion - NO backward compatibility

---

## PHASE 2: LOGGING INFRASTRUCTURE

### 2.1 MODIFY Structured Logger (1 file)

#### File 9: `backend/src/basis_strategy_v1/infrastructure/logging/structured_logger.py` 🔧 MODIFY

**Changes**:

- Update `__init__` to accept `correlation_id`, `pid`, `log_dir`, `engine`
- Add `_get_timestamp_info()` method (engine ts vs real UTC)
- Update all logging methods (`error`, `warning`, `info`, `debug`, `critical`)
- Add full stack trace support for ERROR/CRITICAL (`exc_info=e`)
- Add error code support with `extra={}` metadata
- Update file logging to write to `log_dir / f"{component_name}.log"`

---

## PHASE 3: STRATEGY MANAGER AND ALL STRATEGIES

### 3.1 MODIFY Base Strategy Manager (1 file)

#### File 10: `backend/src/basis_strategy_v1/core/components/strategy_manager.py` 🔧 MODIFY

**Changes**:

- Add `_calculate_expected_deltas(order_params: Dict) -> Dict[str, float]`
- Add `_calculate_spot_trade_deltas(params: Dict) -> Dict[str, float]`
- Add `_calculate_supply_deltas(params: Dict) -> Dict[str, float]`
- Add `_calculate_borrow_deltas(params: Dict) -> Dict[str, float]`
- Add `_calculate_repay_deltas(params: Dict) -> Dict[str, float]`
- Add `_calculate_withdraw_deltas(params: Dict) -> Dict[str, float]`
- Add `_calculate_stake_deltas(params: Dict) -> Dict[str, float]`
- Add `_calculate_unstake_deltas(params: Dict) -> Dict[str, float]`
- Add `_calculate_swap_deltas(params: Dict) -> Dict[str, float]`
- Add `_calculate_transfer_deltas(params: Dict) -> Dict[str, float]`
- Add `_calculate_perp_trade_deltas(params: Dict) -> Dict[str, float]`
- Update `__init__` to accept `correlation_id`, `pid`, `log_dir`
- Initialize `DomainEventLogger`
- Update all error logging with error codes and stack traces

### 3.2 MODIFY All 10 Strategy Implementations (10 files)

#### File 11: `backend/src/basis_strategy_v1/core/strategies/pure_lending_usdt_strategy.py` 🔧 MODIFY

**Changes**:

- Update `_create_entry_full_orders()` to calculate expected_deltas
- Populate all new Order fields (operation_id, source_venue, target_venue, source_token, target_token, expected_deltas, operation_details)
- Generate operation_id using UUID
- Use AAVE supply index from utility_manager for aToken calculation
- Update all order creation methods

#### File 12: `backend/src/basis_strategy_v1/core/strategies/pure_lending_eth_strategy.py` 🔧 MODIFY

**Same changes as File 11**

#### File 13: `backend/src/basis_strategy_v1/core/strategies/btc_basis_strategy.py` 🔧 MODIFY

**Changes**:

- Update all order creation methods to calculate expected_deltas
- Handle CEX spot trades (BTC/USDT)
- Handle perp trades (SHORT positions)
- Handle transfers (wallet → CEX)
- Populate all new Order fields

#### File 14: `backend/src/basis_strategy_v1/core/strategies/eth_basis_strategy.py` 🔧 MODIFY

**Same changes as File 13 but for ETH**

#### File 15: `backend/src/basis_strategy_v1/core/strategies/eth_leveraged_strategy.py` 🔧 MODIFY

**Changes**:

- Update atomic group order creation
- Calculate expected_deltas for: spot trade, stake, perp hedge
- Handle atomic_group_id and sequence_in_group
- Populate all new Order fields

#### File 16: `backend/src/basis_strategy_v1/core/strategies/eth_staking_only_strategy.py` 🔧 MODIFY

**Changes**:

- Update staking order creation
- Calculate expected_deltas for stake operations
- Handle ETH → stETH / weETH conversions
- Populate all new Order fields

#### File 17: `backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_strategy.py` 🔧 MODIFY

**Changes**:

- Update order creation for lending + staking + hedging
- Calculate expected_deltas for all operations
- Handle atomic groups if needed
- Populate all new Order fields

#### File 18: `backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_no_leverage_strategy.py` 🔧 MODIFY

**Same changes as File 17 but without leverage**

#### File 19: `backend/src/basis_strategy_v1/core/strategies/ml_btc_directional_btc_margin_strategy.py` 🔧 MODIFY

**Changes**:

- Update ML-based order creation
- Calculate expected_deltas for directional trades
- Handle margin positions
- Populate all new Order fields

#### File 20: `backend/src/basis_strategy_v1/core/strategies/ml_btc_directional_usdt_margin_strategy.py` 🔧 MODIFY

**Same changes as File 19 but USDT margin**

---

## PHASE 4: EXECUTION MANAGER (RENAME FROM VENUE_MANAGER)

### 4.1 RENAME and REFACTOR (1 file)

#### File 21: `backend/src/basis_strategy_v1/core/execution/execution_manager.py` 🔄 RENAME from venue_manager.py

**Changes**:

- Rename class `VenueManager` → `ExecutionManager`
- Remove ALL Trade imports and references
- Update `__init__` to accept `correlation_id`, `pid`, `log_dir`
- Initialize `DomainEventLogger`
- Change `process_instructions()` → `process_orders(timestamp, orders: List[Order]) -> List[ExecutionHandshake]`
- Add `_process_single_order()` method
- Add `_process_atomic_group()` method
- Add `_log_operation_execution()` method
- Add `_log_atomic_group_execution()` method
- Add `_log_tight_loop_execution()` method
- Add `_convert_deltas_to_structured_format()` utility
- Remove `_convert_trade_to_execution_deltas()` (legacy)
- Update `_reconcile_with_retry()` to use ExecutionHandshake
- Update all error logging with error codes
- Update tight loop logic

### 4.2 MODIFY Venue Interface Manager (1 file)

#### File 22: `backend/src/basis_strategy_v1/core/execution/venue_interface_manager.py` 🔧 MODIFY

**Changes**:

- Remove ALL Trade imports and references
- Update `route_to_venue()` return type: `Trade` → `ExecutionHandshake`
- Update `_route_to_cex()` return type
- Update `_route_to_onchain()` return type
- Update `_route_to_transfer()` return type
- Update all internal method signatures
- Update error handling to use error codes

### 4.3 UPDATE Execution Module **init** (1 file)

#### File 23: `backend/src/basis_strategy_v1/core/execution/__init__.py` 🔧 MODIFY

**Changes**:

- Remove `from .venue_manager import VenueManager`
- Add `from .execution_manager import ExecutionManager`
- Update `__all__` export list

---

## PHASE 5: ALL VENUE INTERFACES

### 5.1 MODIFY Base Interface (1 file)

#### File 24: `backend/src/basis_strategy_v1/core/interfaces/base_execution_interface.py` 🔧 MODIFY

**Changes**:

- Remove Trade imports
- Update all method return types to ExecutionHandshake
- Update abstract method signatures

### 5.2 MODIFY CEX Interface (1 file)

#### File 25: `backend/src/basis_strategy_v1/core/interfaces/cex_execution_interface.py` 🔧 MODIFY

**Changes**:

- Remove Trade imports
- Update `execute_trade()` return type → ExecutionHandshake
- Update `_execute_backtest_trade()` to return ExecutionHandshake
- Update `_execute_live_trade()` to return ExecutionHandshake
- Update `_execute_backtest_transfer()` to return ExecutionHandshake
- Update `_execute_live_transfer()` to return ExecutionHandshake
- Update all execution methods

### 5.3 MODIFY OnChain Interface (1 file)

#### File 26: `backend/src/basis_strategy_v1/core/interfaces/onchain_execution_interface.py` 🔧 MODIFY

**Changes**:

- Remove Trade imports
- Update all execution methods to return ExecutionHandshake
- Update `execute_supply()`, `execute_borrow()`, `execute_stake()`, etc.
- Update backtest and live execution methods

### 5.4 MODIFY Transfer Interface (1 file)

#### File 27: `backend/src/basis_strategy_v1/core/interfaces/transfer_execution_interface.py` 🔧 MODIFY

**Changes**:

- Remove Trade imports
- Update `execute_transfer()` to return ExecutionHandshake
- Update backtest and live transfer methods

### 5.5 MODIFY Interface Factory (1 file)

#### File 28: `backend/src/basis_strategy_v1/core/interfaces/venue_interface_factory.py` 🔧 MODIFY

**Changes**:

- Update type hints if referencing Trade
- Update any factory methods that return interfaces

### 5.6 UPDATE Interfaces **init** (1 file)

#### File 29: `backend/src/basis_strategy_v1/core/interfaces/__init__.py` 🔧 MODIFY

**Changes**:

- Remove Trade imports if present
- Update exports if needed

---

## PHASE 6: ALL CORE COMPONENTS

### 6.1 MODIFY Position Monitor (1 file)

#### File 30: `backend/src/basis_strategy_v1/core/components/position_monitor.py` 🔧 MODIFY

**Changes**:

- Update `__init__` to accept `correlation_id`, `pid`, `log_dir`
- Initialize `DomainEventLogger`
- Add `_log_position_snapshot()` method
- Log PositionSnapshot after every position update
- Update error logging with error codes and stack traces

### 6.2 MODIFY Exposure Monitor (1 file)

#### File 31: `backend/src/basis_strategy_v1/core/components/exposure_monitor.py` 🔧 MODIFY

**Changes**:

- Update `__init__` to accept `correlation_id`, `pid`, `log_dir`
- Initialize `DomainEventLogger`
- Add `_log_exposure_snapshot()` method
- Log ExposureSnapshot after every exposure calculation
- Update error logging with error codes (EXP-001, EXP-002, etc.)
- Use structured logging with `exc_info=e` for stack traces

### 6.3 MODIFY Risk Monitor (1 file)

#### File 32: `backend/src/basis_strategy_v1/core/components/risk_monitor.py` 🔧 MODIFY

**Changes**:

- Update `__init__` to accept `correlation_id`, `pid`, `log_dir`
- Initialize `DomainEventLogger`
- Add `_log_risk_assessment()` method
- Log RiskAssessment after every risk calculation
- Update error logging with error codes (RISK-001, RISK-002, etc.)
- Use structured logging with stack traces

### 6.4 MODIFY PnL Monitor (1 file)

#### File 33: `backend/src/basis_strategy_v1/core/components/pnl_monitor.py` 🔧 MODIFY

**Changes**:

- Update `__init__` to accept `correlation_id`, `pid`, `log_dir`
- Initialize `DomainEventLogger`
- Add `_log_pnl_calculation()` method
- Log PnLCalculation after every P&L calculation
- Update error logging with error codes (PNL-001, PNL-002, etc.)
- Use structured logging with stack traces

### 6.5 MODIFY Position Update Handler (1 file)

#### File 34: `backend/src/basis_strategy_v1/core/components/position_update_handler.py` 🔧 MODIFY

**Changes**:

- Update `__init__` to accept `correlation_id`, `pid`, `log_dir`
- Initialize `DomainEventLogger`
- Add `_log_reconciliation_event()` method
- Log ReconciliationEvent after every reconciliation
- Update tight loop logic to work with ExecutionManager
- Update error logging with error codes

### 6.6 UPDATE Components **init** (1 file)

#### File 35: `backend/src/basis_strategy_v1/core/components/__init__.py` 🔧 MODIFY

**Changes**:

- Update imports if needed
- Remove Trade references

---

## PHASE 7: EVENT ENGINE AND SERVICES

### 7.1 MODIFY Event Driven Strategy Engine (1 file)

#### File 36: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py` 🔧 MODIFY

**Changes**:

- Generate `correlation_id` using `uuid.uuid4().hex` at init
- Get `pid` using `os.getpid()`
- Create log directory using `LogDirectoryManager.create_run_logs()`
- Pass `correlation_id`, `pid`, `log_dir` to ALL components
- Rename `self.venue_manager` → `self.execution_manager`
- Import `ExecutionManager` instead of `VenueManager`
- Remove ALL Trade imports and references
- Update `_process_strategy_decision()` to handle `List[ExecutionHandshake]`
- Update all component initialization calls
- Update error logging with error codes

### 7.2 MODIFY Backtest Service (1 file)

#### File 37: `backend/src/basis_strategy_v1/core/services/backtest_service.py` 🔧 MODIFY

**Changes**:

- Generate `correlation_id` before creating engine
- Pass `correlation_id` to EventDrivenStrategyEngine if needed
- Remove Trade references
- Update result processing if using Trade

### 7.3 MODIFY Live Service (1 file)

#### File 38: `backend/src/basis_strategy_v1/core/services/live_service.py` 🔧 MODIFY

**Changes**:

- Generate `correlation_id` before creating engine
- Pass `correlation_id` to EventDrivenStrategyEngine if needed
- Remove Trade references
- Update result processing if using Trade

---

## PHASE 8: API SERVER

### 8.1 MODIFY API Main (1 file)

#### File 39: `backend/src/basis_strategy_v1/api/main.py` 🔧 MODIFY

**Changes**:

- Generate `correlation_id` for each request
- Create api.log in `logs/{correlation_id}/{pid}/`
- Add structured logging for requests/responses
- Add error logging with stack traces
- Update startup/shutdown logging

---

## PHASE 9: CONFIGURATION AND INFRASTRUCTURE

### 9.1 MODIFY Config Models (1 file)

#### File 40: `backend/src/basis_strategy_v1/infrastructure/config/models.py` 🔧 MODIFY

**Changes**:

- Update `VenueManagerConfig` → `ExecutionManagerConfig` (or rename field)
- Update any Trade references
- Update validation if needed

### 9.2 MODIFY All Mode Config Files (10 files)

#### File 41: `configs/modes/pure_lending_usdt.yaml` 🔧 MODIFY

**Changes**:

- Rename `venue_manager:` → `execution_manager:` in component_config
- Keep all timeout/retry parameters

#### File 42: `configs/modes/pure_lending_eth.yaml` 🔧 MODIFY

**Same changes as File 41**

#### File 43: `configs/modes/btc_basis.yaml` 🔧 MODIFY

**Same changes as File 41**

#### File 44: `configs/modes/eth_basis.yaml` 🔧 MODIFY

**Same changes as File 41**

#### File 45: `configs/modes/eth_leveraged.yaml` 🔧 MODIFY

**Same changes as File 41**

#### File 46: `configs/modes/eth_staking_only.yaml` 🔧 MODIFY

**Same changes as File 41**

#### File 47: `configs/modes/usdt_market_neutral.yaml` 🔧 MODIFY

**Same changes as File 41**

#### File 48: `configs/modes/usdt_market_neutral_no_leverage.yaml` 🔧 MODIFY

**Same changes as File 41**

#### File 49: `configs/modes/ml_btc_directional_btc_margin.yaml` 🔧 MODIFY

**Same changes as File 41**

#### File 50: `configs/modes/ml_btc_directional_usdt_margin.yaml` 🔧 MODIFY

**Same changes as File 41**

### 9.3 MODIFY .gitignore (1 file)

#### File 51: `.gitignore` 🔧 MODIFY

**Changes**:

- Remove `backend/logs/`
- Add `logs/` (root level)

---

## PHASE 10: DOCUMENTATION - COMPONENT SPECS

### 10.1 MODIFY Core Component Specs (6 files)

#### File 52: `docs/specs/01_POSITION_MONITOR.md` 🔧 MODIFY

**Changes**:

- Add domain event logging section
- Add PositionSnapshot event schema
- Update initialization to include correlation_id/pid/log_dir
- Add error code documentation (POS-001, POS-002, POS-003)
- Update examples with new logging

#### File 53: `docs/specs/02_EXPOSURE_MONITOR.md` 🔧 MODIFY

**Changes**:

- Add domain event logging section
- Add ExposureSnapshot event schema
- Update initialization
- Add error code documentation (EXP-001, EXP-002, EXP-003)
- Update structured error logging examples

#### File 54: `docs/specs/03_RISK_MONITOR.md` 🔧 MODIFY

**Changes**:

- Add domain event logging section
- Add RiskAssessment event schema
- Update initialization
- Add error code documentation (RISK-001, RISK-002, RISK-003)

#### File 55: `docs/specs/04_PNL_MONITOR.md` 🔧 MODIFY

**Changes**:

- Add domain event logging section
- Add PnLCalculation event schema
- Update initialization
- Add error code documentation (PNL-001, PNL-002)

#### File 56: `docs/specs/05_STRATEGY_MANAGER.md` 🔧 MODIFY

**Changes**:

- Add expected_deltas calculation section
- Document all `_calculate_*_deltas()` methods
- Update Order creation examples with new fields
- Add OrderEvent and StrategyDecision event schemas
- Update error code documentation (STRAT-001, STRAT-002, STRAT-003)

#### File 57: `docs/specs/11_POSITION_UPDATE_HANDLER.md` 🔧 MODIFY

**Changes**:

- Add ReconciliationEvent logging section
- Add domain event schema
- Update tight loop architecture description
- Update interaction with ExecutionManager (not VenueManager)

### 10.2 RENAME and MODIFY Execution Specs (3 files)

#### File 58: `docs/specs/06_EXECUTION_MANAGER.md` 🔄 RENAME from 06_VENUE_MANAGER.md

**Changes**:

- Rename all instances of VenueManager → ExecutionManager
- Remove Trade model references
- Add ExecutionHandshake documentation
- Add domain event logging (OperationExecutionEvent, AtomicOperationGroupEvent, TightLoopExecutionEvent)
- Update tight loop flow diagrams
- Add atomic group handling section
- Add error code documentation (EXEC-001 through EXEC-005)
- Update all method signatures
- Update examples with new flow

#### File 59: `docs/specs/07_VENUE_INTERFACE_MANAGER.md` 🔧 MODIFY

**Changes**:

- Remove Trade model references
- Update return type documentation: Trade → ExecutionHandshake
- Update routing flow diagrams
- Add error code documentation (VEN-001, VEN-002, VEN-003)
- Update examples

#### File 60: `docs/specs/07A_VENUE_INTERFACES.md` 🔧 MODIFY

**Changes**:

- Remove Trade model references throughout
- Update all interface method signatures to return ExecutionHandshake
- Update CEX interface examples
- Update OnChain interface examples
- Update Transfer interface examples
- Add atomic transaction handling for OnChain

### 10.3 MODIFY Other Component Specs (4 files)

#### File 61: `docs/specs/08_EVENT_LOGGER.md` 🔧 MODIFY

**Changes**:

- Add DomainEventLogger documentation
- Add all domain event schemas
- Add JSONL file structure documentation
- Update event_logger_operations.jsonl schema

#### File 62: `docs/specs/13_BACKTEST_SERVICE.md` 🔧 MODIFY

**Changes**:

- Update to use ExecutionManager
- Remove Trade references
- Update execution flow diagrams
- Add correlation_id generation

#### File 63: `docs/specs/14_LIVE_TRADING_SERVICE.md` 🔧 MODIFY

**Changes**:

- Update to use ExecutionManager
- Remove Trade references
- Update execution flow diagrams
- Add correlation_id generation

#### File 64: `docs/specs/15_EVENT_DRIVEN_STRATEGY_ENGINE.md` 🔧 MODIFY

**Changes**:

- Update component initialization with correlation_id/pid/log_dir
- Rename venue_manager → execution_manager
- Remove Trade references
- Update execution flow section
- Add log directory creation section

---

## PHASE 11: DOCUMENTATION - STRATEGY SPECS

### 11.1 MODIFY All Strategy Specs (9 files)

#### File 65: `docs/specs/strategies/01_PURE_LENDING_STRATEGY.md` 🔧 MODIFY

**Changes**:

- Update order creation examples with expected_deltas calculation
- Add AAVE supply index usage example
- Show new Order fields populated
- Update execution flow to use ExecutionHandshake

#### File 66: `docs/specs/strategies/02_BTC_BASIS_STRATEGY.md` 🔧 MODIFY

**Changes**:

- Update order creation with expected_deltas for spot + perp
- Show transfer order creation
- Update all Order fields
- Update execution flow

#### File 67: `docs/specs/strategies/03_ETH_BASIS_STRATEGY.md` 🔧 MODIFY

**Same changes as File 66 for ETH**

#### File 68: `docs/specs/strategies/04_ETH_STAKING_ONLY_STRATEGY.md` 🔧 MODIFY

**Changes**:

- Update staking order creation with expected_deltas
- Show ETH → stETH/weETH conversion
- Update Order fields

#### File 69: `docs/specs/strategies/05_ETH_LEVERAGED_STRATEGY.md` 🔧 MODIFY

**Changes**:

- Update atomic group order creation
- Show expected_deltas for each operation in group
- Update atomic_group_id and sequence_in_group usage
- Update execution flow with atomic handling

#### File 70: `docs/specs/strategies/06_USDT_MARKET_NEUTRAL_NO_LEVERAGE_STRATEGY.md` 🔧 MODIFY

**Changes**:

- Update order creation with expected_deltas
- Update lending + staking operations
- Update Order fields

#### File 71: `docs/specs/strategies/07_USDT_MARKET_NEUTRAL_STRATEGY.md` 🔧 MODIFY

**Same as File 70 but with leverage**

#### File 72: `docs/specs/strategies/08_ML_BTC_DIRECTIONAL_STRATEGY.md` 🔧 MODIFY

**Changes**:

- Update ML-based order creation
- Add expected_deltas for directional trades
- Update Order fields

#### File 73: `docs/specs/strategies/09_ML_USDT_DIRECTIONAL_STRATEGY.md` 🔧 MODIFY

**Same as File 72**

---

## PHASE 12: DOCUMENTATION - ROOT DOCS

### 12.1 CREATE New Documentation (1 file)

#### File 74: `docs/LOGGING_GUIDE.md` ✨ NEW

**Contents**:

- Log directory structure (`logs/{correlation_id}/{pid}/`)
- Component log files (api.log, position_monitor.log, etc.)
- Domain event JSONL files (all 12 event types)
- Event schemas (full Pydantic models documented)
- Operation types (SPOT_TRADE, SUPPLY, STAKE, etc.)
- Atomic group logging
- Error code registry (all error codes documented)
- Structured logging patterns
- Stack trace requirements
- Timestamp strategy (engine vs UTC)
- Debugging workflows
- Log querying examples

### 12.2 MODIFY Major Architecture Docs (7 files)

#### File 75: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` 🔧 MODIFY

**Changes**:

- Update execution flow section completely
- Remove Trade model references
- Add ExecutionHandshake documentation
- Update Order model documentation with new fields
- Rename VenueManager → ExecutionManager throughout
- Add domain event logging architecture
- Update component interaction diagrams
- Add log directory structure section

#### File 76: `docs/ARCHITECTURAL_DECISION_RECORDS.md` 🔧 MODIFY

**Changes**:

- Add new ADR: "ADR-XXX: Unified Execution Flow and Logging System Refactor"
- Document decision to remove Trade model
- Document ExecutionHandshake adoption
- Document VenueManager → ExecutionManager rename
- Document expected_deltas calculation strategy
- Document domain event logging architecture
- Document atomic group handling approach
- Include date, context, decision, rationale, consequences

#### File 77: `docs/TIGHT_LOOP_ARCHITECTURE.md` 🔧 MODIFY

**Changes**:

- Rename all VenueManager → ExecutionManager
- Update tight loop flow diagrams
- Update reconciliation flow with ExecutionHandshake
- Update retry logic documentation
- Add domain event logging in tight loop
- Update component responsibilities section

#### File 78: `docs/ERROR_HANDLING_PATTERNS.md` 🔧 MODIFY

**Changes**:

- Add comprehensive error code registry
- Add structured logging patterns (raise vs log decision tree)
- Add stack trace requirements
- Add ComponentError usage guidelines
- Update all error handling examples with new patterns
- Add correlation_id tracking section

#### File 79: `docs/HEALTH_ERROR_SYSTEMS.md` 🔧 MODIFY

**Changes**:

- Add new logging infrastructure integration
- Add domain event logging for health status
- Update error code propagation
- Add log directory structure for health logs
- Update health check logging examples

#### File 80: `docs/WORKFLOW_GUIDE.md` 🔧 MODIFY

**Changes**:

- Update entire execution flow section
- Replace Trade with ExecutionHandshake throughout
- Rename VenueManager → ExecutionManager throughout
- Add expected_deltas calculation workflow
- Add domain event logging workflow
- Update all code examples
- Update component interaction diagrams
- Add atomic group execution workflow
- Update backtest workflow
- Update live trading workflow

#### File 81: `docs/ORDER_TRADE_EXECUTION_DELTAS_FLOW.md` 🔧 MODIFY (or DELETE and merge into WORKFLOW_GUIDE)

**Changes**:

- Remove Trade model references completely
- Update to Order → ExecutionHandshake flow
- Add expected_deltas calculation flow
- Update execution delta flow
- Add domain event logging flow

### 12.3 MODIFY Supporting Docs (9 files)

#### File 82: `docs/MODES.md` 🔧 MODIFY

**Changes**:

- Update venue_manager → execution_manager in config examples
- Update execution flow examples
- Update Order creation examples with new fields

#### File 83: `docs/STRATEGY_MODES.md` 🔧 MODIFY

**Same changes as File 82**

#### File 84: `docs/MODE_SPECIFIC_BEHAVIOR_GUIDE.md` 🔧 MODIFY

**Same changes as File 82**

#### File 85: `docs/COMPONENT_SPECS_INDEX.md` 🔧 MODIFY

**Changes**:

- Update index to reference 06_EXECUTION_MANAGER.md (not VENUE_MANAGER)
- Add references to new documentation

#### File 86: `docs/CODE_STRUCTURE_PATTERNS.md` 🔧 MODIFY

**Changes**:

- Update component patterns with new initialization signature
- Add domain event logging patterns
- Update error handling patterns

#### File 87: `docs/TARGET_REPOSITORY_STRUCTURE.md` 🔧 MODIFY

**Changes**:

- Update file structure to show logs/ at root
- Update core/execution to show execution_manager.py
- Update core/models to show execution.py and domain_events.py
- Add core/errors/error_codes.py

#### File 88: `docs/LOGICAL_EXCEPTIONS_GUIDE.md` 🔧 MODIFY

**Changes**:

- Update with ComponentError usage
- Add error code guidance

#### File 89: `docs/QUALITY_GATES.md` 🔧 MODIFY

**Changes**:

- Update quality gate tests to use new execution flow
- Update validation criteria

#### File 90: `docs/EXECUTION_FLOW_VS_LOGGING_PLAN_ANALYSIS.md` 🔧 MODIFY or ❌ DELETE

**Action**: Either update to reflect implemented solution or delete as obsolete

---

## PHASE 13: TESTING

### 13.1 CREATE New Unit Tests (5 files)

#### File 91: `tests/unit/models/test_execution.py` ✨ NEW

**Tests**:

- ExecutionHandshake model validation
- OperationType enum values
- ExecutionStatus enum values
- Pydantic serialization/deserialization

#### File 92: `tests/unit/models/test_domain_events.py` ✨ NEW

**Tests**:

- All 12 domain event models
- Pydantic validation for each
- JSONL serialization
- Required field validation

#### File 93: `tests/unit/logging/test_log_directory_manager.py` ✨ NEW

**Tests**:

- Directory creation (logs/{correlation_id}/{pid}/)
- Metadata file creation
- run_metadata.json content validation

#### File 94: `tests/unit/logging/test_domain_event_logger.py` ✨ NEW

**Tests**:

- JSONL file writing for each event type
- File creation in events/ subdirectory
- Event serialization

#### File 95: `tests/unit/components/test_strategy_manager_deltas.py` ✨ NEW

**Tests**:

- `_calculate_expected_deltas()` for all operation types
- AAVE index usage for supply operations
- Staking rate usage for stake operations
- Price calculation for spot trades
- Expected delta accuracy

### 13.2 CREATE New Integration Tests (3 files)

#### File 96: `tests/integration/test_execution_flow.py` ✨ NEW

**Tests**:

- End-to-end Order → ExecutionHandshake flow
- ExecutionManager processing
- VenueInterfaceManager routing
- Venue interface execution
- Reconciliation with PositionUpdateHandler

#### File 97: `tests/integration/test_structured_logging.py` ✨ NEW

**Tests**:

- Log directory creation
- Component log file creation
- Domain event JSONL file creation
- Event content validation
- Error logging with stack traces

#### File 98: `tests/integration/test_atomic_operations.py` ✨ NEW

**Tests**:

- Atomic group order creation
- Atomic group execution
- AtomicOperationGroupEvent logging
- Rollback handling (simulated)

### 13.3 MODIFY Existing Tests (unknown count - needs audit)

**Action**: Search all test files for Trade or VenueManager references and update:

- Replace Trade with ExecutionHandshake
- Update VenueManager to ExecutionManager
- Update test assertions
- Update mock return values

### 13.4 UPDATE Quality Gate Tests

**Action**: Update `tests/quality_gates/run_quality_gates.py` and all quality gate scripts:

- Update component interaction tests
- Update execution flow tests
- Update configuration validation tests

---

## PHASE 14: VALIDATION AND CLEANUP

### 14.1 Pure Lending USDT End-to-End Test

**Steps**:

1. Start backend: `./platform.sh dev`
2. Run backtest: `curl -X POST http://localhost:8001/api/v1/backtest/ ...` (from test_initial_capital_logging.sh)
3. Verify log structure: `ls -la logs/{correlation_id}/{pid}/`
4. Check files exist:

   - `api.log`
   - `strategy_manager.log`
   - `execution_manager.log`
   - `position_monitor.log`
   - `exposure_monitor.log`
   - `risk_monitor.log`
   - `pnl_monitor.log`
   - `position_update_handler.log`
   - `events/operation_executions.jsonl`
   - `events/positions.jsonl`
   - `events/exposures.jsonl`
   - `events/risk_assessments.jsonl`
   - `events/pnl_calculations.jsonl`
   - `events/reconciliations.jsonl`

5. Verify SUPPLY operation logged correctly
6. Verify aUSDT calculation uses AAVE index
7. Verify expected_deltas matches actual_deltas
8. Verify no errors in logs

### 14.2 Run Full Test Suite

```bash
cd tests
pytest -v --cov=backend/src/basis_strategy_v1 --cov-report=html
```

Verify:

- All tests pass
- 80%+ coverage achieved
- No Trade references in coverage report
- No VenueManager references (should be ExecutionManager)

### 14.3 Run Quality Gates

```bash
python tests/quality_gates/run_quality_gates.py --all
```

Verify all gates pass.

---

## COMPLETE FILE MANIFEST

### NEW FILES (22 total)

**Python (17)**:

1. `backend/src/basis_strategy_v1/core/models/execution.py`
2. `backend/src/basis_strategy_v1/core/models/domain_events.py`
3. `backend/src/basis_strategy_v1/core/errors/error_codes.py`
4. `backend/src/basis_strategy_v1/infrastructure/logging/log_directory_manager.py`
5. `backend/src/basis_strategy_v1/infrastructure/logging/domain_event_logger.py`
6. `backend/src/basis_strategy_v1/core/execution/execution_manager.py` (rename from venue_manager.py)
7. `tests/unit/models/test_execution.py`
8. `tests/unit/models/test_domain_events.py`
9. `tests/unit/logging/test_log_directory_manager.py`
10. `tests/unit/logging/test_domain_event_logger.py`
11. `tests/unit/components/test_strategy_manager_deltas.py`
12. `tests/integration/test_execution_flow.py`
13. `tests/integration/test_structured_logging.py`
14. `tests/integration/test_atomic_operations.py`

**Documentation (2)**:

15. `docs/LOGGING_GUIDE.md`
16. `docs/specs/06_EXECUTION_MANAGER.md` (rename from 06_VENUE_MANAGER.md)

### DELETED FILES (2 total)

1. `backend/src/basis_strategy_v1/core/models/trade.py` ❌
2. `backend/src/basis_strategy_v1/core/execution/venue_manager.py` ❌ (becomes execution_manager.py)

### MODIFIED PYTHON FILES (35 total)

**Models (2)**:

1. `backend/src/basis_strategy_v1/core/models/order.py`
2. `backend/src/basis_strategy_v1/core/models/__init__.py`

**Logging (1)**:

3. `backend/src/basis_strategy_v1/infrastructure/logging/structured_logger.py`

**Components (6)**:

4. `backend/src/basis_strategy_v1/core/components/strategy_manager.py`
5. `backend/src/basis_strategy_v1/core/components/position_monitor.py`
6. `backend/src/basis_strategy_v1/core/components/exposure_monitor.py`
7. `backend/src/basis_strategy_v1/core/components/risk_monitor.py`
8. `backend/src/basis_strategy_v1/core/components/pnl_monitor.py`
9. `backend/src/basis_strategy_v1/core/components/position_update_handler.py`

**Strategies (10)**:

10. `backend/src/basis_strategy_v1/core/strategies/pure_lending_usdt_strategy.py`
11. `backend/src/basis_strategy_v1/core/strategies/pure_lending_eth_strategy.py`
12. `backend/src/basis_strategy_v1/core/strategies/btc_basis_strategy.py`
13. `backend/src/basis_strategy_v1/core/strategies/eth_basis_strategy.py`
14. `backend/src/basis_strategy_v1/core/strategies/eth_leveraged_strategy.py`
15. `backend/src/basis_strategy_v1/core/strategies/eth_staking_only_strategy.py`
16. `backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_strategy.py`
17. `backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_no_leverage_strategy.py`
18. `backend/src/basis_strategy_v1/core/strategies/ml_btc_directional_btc_margin_strategy.py`
19. `backend/src/basis_strategy_v1/core/strategies/ml_btc_directional_usdt_margin_strategy.py`

**Execution (2)**:

20. `backend/src/basis_strategy_v1/core/execution/venue_interface_manager.py`
21. `backend/src/basis_strategy_v1/core/execution/__init__.py`

**Interfaces (6)**:

22. `backend/src/basis_strategy_v1/core/interfaces/base_execution_interface.py`
23. `backend/src/basis_strategy_v1/core/interfaces/cex_execution_interface.py`
24. `backend/src/basis_strategy_v1/core/interfaces/onchain_execution_interface.py`
25. `backend/src/basis_strategy_v1/core/interfaces/transfer_execution_interface.py`
26. `backend/src/basis_strategy_v1/core/interfaces/venue_interface_factory.py`
27. `backend/src/basis_strategy_v1/core/interfaces/__init__.py`

**Engine & Services (4)**:

28. `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py`
29. `backend/src/basis_strategy_v1/core/services/backtest_service.py`
30. `backend/src/basis_strategy_v1/core/services/live_service.py`
31. `backend/src/basis_strategy_v1/api/main.py`

**Config (2)**:

32. `backend/src/basis_strategy_v1/infrastructure/config/models.py`
33. `.gitignore`

### MODIFIED CONFIG FILES (10 total)

1. `configs/modes/pure_lending_usdt.yaml`
2. `configs/modes/pure_lending_eth.yaml`
3. `configs/modes/btc_basis.yaml`
4. `configs/modes/eth_basis.yaml`
5. `configs/modes/eth_leveraged.yaml`
6. `configs/modes/eth_staking_only.yaml`
7. `configs/modes/usdt_market_neutral.yaml`
8. `configs/modes/usdt_market_neutral_no_leverage.yaml`
9. `configs/modes/ml_btc_directional_btc_margin.yaml`
10. `configs/modes/ml_btc_directional_usdt_margin.yaml`

### MODIFIED DOCUMENTATION FILES (35 total)

**Component Specs (14)**:

1. `docs/specs/01_POSITION_MONITOR.md`
2. `docs/specs/02_EXPOSURE_MONITOR.md`
3. `docs/specs/03_RISK_MONITOR.md`
4. `docs/specs/04_PNL_MONITOR.md`
5. `docs/specs/05_STRATEGY_MANAGER.md`
6. `docs/specs/07_VENUE_INTERFACE_MANAGER.md`
7. `docs/specs/07A_VENUE_INTERFACES.md`
8. `docs/specs/08_EVENT_LOGGER.md`
9. `docs/specs/11_POSITION_UPDATE_HANDLER.md`
10. `docs/specs/13_BACKTEST_SERVICE.md`
11. `docs/specs/14_LIVE_TRADING_SERVICE.md`
12. `docs/specs/15_EVENT_DRIVEN_STRATEGY_ENGINE.md`
13. `docs/specs/19_CONFIGURATION.md`
14. `docs/specs/5B_BASE_STRATEGY_MANAGER.md`

**Strategy Specs (9)**:

15. `docs/specs/strategies/01_PURE_LENDING_STRATEGY.md`
16. `docs/specs/strategies/02_BTC_BASIS_STRATEGY.md`
17. `docs/specs/strategies/03_ETH_BASIS_STRATEGY.md`
18. `docs/specs/strategies/04_ETH_STAKING_ONLY_STRATEGY.md`
19. `docs/specs/strategies/05_ETH_LEVERAGED_STRATEGY.md`
20. `docs/specs/strategies/06_USDT_MARKET_NEUTRAL_NO_LEVERAGE_STRATEGY.md`
21. `docs/specs/strategies/07_USDT_MARKET_NEUTRAL_STRATEGY.md`
22. `docs/specs/strategies/08_ML_BTC_DIRECTIONAL_STRATEGY.md`
23. `docs/specs/strategies/09_ML_USDT_DIRECTIONAL_STRATEGY.md`

**Root Docs (12)**:

24. `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`
25. `docs/ARCHITECTURAL_DECISION_RECORDS.md`
26. `docs/TIGHT_LOOP_ARCHITECTURE.md`
27. `docs/ERROR_HANDLING_PATTERNS.md`
28. `docs/HEALTH_ERROR_SYSTEMS.md`
29. `docs/WORKFLOW_GUIDE.md`
30. `docs/ORDER_TRADE_EXECUTION_DELTAS_FLOW.md`
31. `docs/MODES.md`
32. `docs/STRATEGY_MODES.md`
33. `docs/MODE_SPECIFIC_BEHAVIOR_GUIDE.md`
34. `docs/COMPONENT_SPECS_INDEX.md`
35. `docs/CODE_STRUCTURE_PATTERNS.md`

---

## SUCCESS CRITERIA

✅ **Trade model completely removed** (trade.py deleted)

✅ **ExecutionHandshake replaces Trade everywhere** (35 Python files updated)

✅ **VenueManager renamed to ExecutionManager** (file renamed, 50+ references updated)

✅ **Order model includes expected_deltas and new fields** (order.py updated, all strategies updated)

✅ **Strategy Manager calculates expected_deltas** (11 strategy files updated)

✅ **Log directory structure: logs/{correlation_id}/{pid}/** (LogDirectoryManager created)

✅ **Domain events logged to JSONL files** (DomainEventLogger created, 12 event types)

✅ **All 10 strategies updated** (all strategy .py files modified)

✅ **All 6 core components updated** (all component .py files modified)

✅ **All 5 execution interfaces updated** (all interface .py files modified)

✅ **All 10 mode configs updated** (all .yaml files modified)

✅ **All 35 documentation files updated** (specs + root docs)

✅ **Structured error logging with codes and stack traces** (error_codes.py + structured_logger.py)

✅ **Atomic groups handled correctly** (venue-level atomicity)

✅ **Pure Lending USDT strategy works end-to-end** (validation test)

✅ **All tests pass** (pytest run successful)

✅ **80%+ test coverage** (coverage report)

✅ **Quality gates pass** (run_quality_gates.py successful)

✅ **Server starts successfully** (./platform.sh dev runs)

✅ **Documentation matches implementation** (all 35 docs updated)

---

## IMPLEMENTATION ORDER

1. ✅ Phase 1: Core Data Models (5 new files, 2 modified files, 1 deleted file)
2. ✅ Phase 2: Logging Infrastructure (2 new files, 1 modified file)
3. ✅ Phase 3: Strategy Manager and All Strategies (11 modified files)
4. ✅ Phase 4: Execution Manager (1 renamed file, 2 modified files)
5. ✅ Phase 5: All Venue Interfaces (6 modified files)
6. ✅ Phase 6: All Core Components (6 modified files)
7. ✅ Phase 7: Event Engine and Services (4 modified files)
8. ✅ Phase 8: API Server (1 modified file)
9. ✅ Phase 9: Configuration and Infrastructure (12 modified files)
10. ✅ Phase 10: Documentation - Component Specs (14 modified files, 1 renamed file)
11. ✅ Phase 11: Documentation - Strategy Specs (9 modified files)
12. ✅ Phase 12: Documentation - Root Docs (12 modified files, 1 new file)
13. ✅ Phase 13: Testing (8 new test files, existing tests updated)
14. ✅ Phase 14: Validation and Cleanup (end-to-end test, quality gates)

---

## TOTAL FILES: 112

- **22 new files created**
- **2 files deleted**
- **88 files modified**

### To-dos

- [ ] Create Pydantic domain data models including OperationExecutionEvent and AtomicOperationGroupEvent for all operation types
- [ ] Create log directory manager with correlation_id/pid structure and metadata generation
- [ ] Create domain event logger that writes JSONL files using Pydantic models for all operation types
- [ ] Enhance StructuredLogger with PID, correlation_id, engine timestamps, and stack traces
- [ ] Update EventDrivenStrategyEngine to generate correlation_id and initialize logging infrastructure
- [ ] Update all 8 core components with new logging patterns and domain event logging
- [ ] Update venue_interface_manager to log OperationExecutionEvent and AtomicOperationGroupEvent
- [ ] Update backtest_service and live_service entry points with correlation_id generation
- [ ] Update API server main.py with api.log structured logging
- [ ] Update .gitignore to use root logs/ instead of backend/logs/
- [ ] Create comprehensive LOGGING_GUIDE.md documentation with operation types and atomic groups
- [ ] Update ERROR_HANDLING_PATTERNS.md and HEALTH_ERROR_SYSTEMS.md with new logging patterns
- [ ] Create unit and integration tests for new logging infrastructure including operation types