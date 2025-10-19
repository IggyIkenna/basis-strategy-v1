<!-- a4b2dcee-0e47-42e3-8e15-8ff2a9a3d4d5 285bbafb-3cee-46b0-a756-2118093cc8cd -->
# Complete Phase 6-7: Core Components & Event Engine Unified Logging

## Overview

Update all Phase 6 core components and Phase 7 Event Engine to use the new unified logging system, replacing legacy logging patterns completely.

## Phase 6: Core Components (6 files)

### 1. Position Monitor

**File**: `backend/src/basis_strategy_v1/core/components/position_monitor.py`

**Current Issues**:

- Uses legacy `get_position_monitor_logger()` (line 24)
- Uses `StandardizedLoggingMixin` (line 30)
- Only accepts `correlation_id` parameter (line 47)
- No `pid` or `log_dir` parameters

**Changes**:

- **REMOVE** import: `from ...infrastructure.logging.structured_logger import get_position_monitor_logger`
- **REMOVE** import: `from ...core.logging.base_logging_interface import StandardizedLoggingMixin`
- **ADD** imports:
  ```python
  from pathlib import Path
  from ...infrastructure.logging.structured_logger import StructuredLogger
  from ...infrastructure.logging.domain_event_logger import DomainEventLogger
  from ...core.models.domain_events import PositionSnapshot
  from ...core.errors.error_codes import ERROR_REGISTRY
  ```

- **REMOVE** inheritance: `StandardizedLoggingMixin` from class definition (line 30)
- **UPDATE** `__init__` signature to add `pid: int = None, log_dir: Path = None` after `correlation_id`
- **REPLACE** logging initialization (lines 79-82):
  ```python
  # Initialize logging infrastructure
  self.correlation_id = correlation_id or str(uuid.uuid4().hex)
  self.pid = pid or os.getpid()
  self.log_dir = log_dir
  
  # Initialize structured logger
  self.logger = StructuredLogger(
      component_name="PositionMonitor",
      correlation_id=self.correlation_id,
      pid=self.pid,
      log_dir=self.log_dir,
      engine=None  # Will be set by event engine if available
  )
  
  # Initialize domain event logger
  self.domain_event_logger = DomainEventLogger(self.log_dir)
  ```

- **ADD** method `_log_position_snapshot()`:
  ```python
  def _log_position_snapshot(self, trigger_source: str = None) -> None:
      """Log position snapshot as domain event."""
      if not self.log_dir:
          return
      
      timestamp = datetime.now().isoformat()
      real_utc = datetime.now(timezone.utc).isoformat()
      
      # Calculate total value (use share class for simplicity)
      total_value = sum(abs(v) for v in self.simulated_positions.values())
      
      snapshot = PositionSnapshot(
          timestamp=timestamp,
          real_utc_time=real_utc,
          correlation_id=self.correlation_id,
          pid=self.pid,
          positions=self.simulated_positions.copy(),
          total_value_usd=total_value,
          position_type='simulated' if self.execution_mode == 'backtest' else 'real',
          trigger_source=trigger_source,
          metadata={}
      )
      
      self.domain_event_logger.log_position_snapshot(snapshot)
  ```

- **CALL** `_log_position_snapshot()` after every position update in:
  - `apply_execution_deltas()` method
  - `_apply_automatic_settlements()` method
  - Any method that modifies positions
- **UPDATE** all error logging to use error codes (POS-001 through POS-005):
  ```python
  self.logger.error(
      "Failed to apply execution deltas",
      error_code="POS-001",
      exc_info=e,
      operation="apply_execution_deltas"
  )
  ```

- **REPLACE** all `self.structured_logger` calls with `self.logger`

---

### 2. Exposure Monitor

**File**: `backend/src/basis_strategy_v1/core/components/exposure_monitor.py`

**Current Issues**:

- Uses legacy `get_structured_logger('exposure_monitor')` (line 61)
- Uses `StandardizedLoggingMixin` (line 21)
- Only accepts `correlation_id` parameter (line 37)

**Changes**:

- **REMOVE** import: `from ...infrastructure.logging.structured_logger import get_structured_logger`
- **REMOVE** import: `from ...core.logging.base_logging_interface import StandardizedLoggingMixin`
- **ADD** imports:
  ```python
  from pathlib import Path
  import os
  import uuid
  from ...infrastructure.logging.structured_logger import StructuredLogger
  from ...infrastructure.logging.domain_event_logger import DomainEventLogger
  from ...core.models.domain_events import ExposureSnapshot
  from ...core.errors.error_codes import ERROR_REGISTRY
  ```

- **REMOVE** inheritance from class definition
- **UPDATE** `__init__` signature (line 37): add `pid: int = None, log_dir: Path = None` after `correlation_id`
- **REPLACE** logging initialization (lines 61-76):
  ```python
  # Initialize logging infrastructure
  self.correlation_id = correlation_id or str(uuid.uuid4().hex)
  self.pid = pid or os.getpid()
  self.log_dir = log_dir
  
  # Initialize structured logger
  self.logger = StructuredLogger(
      component_name="ExposureMonitor",
      correlation_id=self.correlation_id,
      pid=self.pid,
      log_dir=self.log_dir,
      engine=None
  )
  
  # Initialize domain event logger
  self.domain_event_logger = DomainEventLogger(self.log_dir)
  
  self.logger.info(
      f"ExposureMonitor initialized: share_class={self.share_class}",
      share_class=self.share_class,
      mode=config.get('mode')
  )
  ```

- **ADD** method `_log_exposure_snapshot()`:
  ```python
  def _log_exposure_snapshot(self, exposures: Dict[str, Any]) -> None:
      """Log exposure snapshot as domain event."""
      if not self.log_dir:
          return
      
      timestamp = datetime.now().isoformat()
      real_utc = datetime.now(timezone.utc).isoformat()
      
      snapshot = ExposureSnapshot(
          timestamp=timestamp,
          real_utc_time=real_utc,
          correlation_id=self.correlation_id,
          pid=self.pid,
          net_delta_usd=exposures.get('net_delta_usd', 0.0),
          asset_exposures=exposures.get('asset_exposures', {}),
          total_value_usd=exposures.get('total_value_usd', 0.0),
          share_class_value=exposures.get('share_class_value', 0.0),
          metadata={}
      )
      
      self.domain_event_logger.log_exposure_snapshot(snapshot)
  ```

- **CALL** `_log_exposure_snapshot()` after every exposure calculation
- **UPDATE** all error logging with error codes (EXP-001 through EXP-005)
- **REPLACE** all `self.structured_logger` calls with `self.logger`

---

### 3. Risk Monitor

**File**: `backend/src/basis_strategy_v1/core/components/risk_monitor.py`

**Current Issues**:

- Uses legacy `get_risk_monitor_logger()` (line 50)
- Uses `StandardizedLoggingMixin` (line 25)
- Only accepts `correlation_id` parameter (line 34)

**Changes**:

- **REMOVE** import: `from ...infrastructure.logging.structured_logger import get_risk_monitor_logger`
- **REMOVE** import: `from ...core.logging.base_logging_interface import StandardizedLoggingMixin`
- **ADD** imports:
  ```python
  from pathlib import Path
  import os
  import uuid
  from ...infrastructure.logging.structured_logger import StructuredLogger
  from ...infrastructure.logging.domain_event_logger import DomainEventLogger
  from ...core.models.domain_events import RiskAssessment
  from ...core.errors.error_codes import ERROR_REGISTRY
  ```

- **REMOVE** inheritance from class definition
- **UPDATE** `__init__` signature (line 34): add `pid: int = None, log_dir: Path = None` after `correlation_id`
- **REPLACE** logging initialization (lines 50-53):
  ```python
  # Initialize logging infrastructure
  self.correlation_id = correlation_id or str(uuid.uuid4().hex)
  self.pid = pid or os.getpid()
  self.log_dir = log_dir
  
  # Initialize structured logger
  self.logger = StructuredLogger(
      component_name="RiskMonitor",
      correlation_id=self.correlation_id,
      pid=self.pid,
      log_dir=self.log_dir,
      engine=None
  )
  
  # Initialize domain event logger
  self.domain_event_logger = DomainEventLogger(self.log_dir)
  ```

- **ADD** method `_log_risk_assessment()`:
  ```python
  def _log_risk_assessment(self, risk_data: Dict[str, Any]) -> None:
      """Log risk assessment as domain event."""
      if not self.log_dir:
          return
      
      timestamp = datetime.now().isoformat()
      real_utc = datetime.now(timezone.utc).isoformat()
      
      assessment = RiskAssessment(
          timestamp=timestamp,
          real_utc_time=real_utc,
          correlation_id=self.correlation_id,
          pid=self.pid,
          health_factor=risk_data.get('health_factor'),
          ltv_ratio=risk_data.get('ltv_ratio'),
          liquidation_threshold=risk_data.get('liquidation_threshold'),
          margin_usage=risk_data.get('margin_usage'),
          risk_level=risk_data.get('risk_level', 'unknown'),
          warnings=risk_data.get('warnings', []),
          breaches=risk_data.get('breaches', []),
          metadata={}
      )
      
      self.domain_event_logger.log_risk_assessment(assessment)
  ```

- **CALL** `_log_risk_assessment()` after every risk calculation
- **UPDATE** all error logging with error codes (RISK-001 through RISK-006)
- **REPLACE** all `self.structured_logger` calls with `self.logger`

---

### 4. PnL Monitor

**File**: `backend/src/basis_strategy_v1/core/components/pnl_monitor.py`

**Changes**:

- **ADD** imports:
  ```python
  from pathlib import Path
  import os
  import uuid
  from ...infrastructure.logging.structured_logger import StructuredLogger
  from ...infrastructure.logging.domain_event_logger import DomainEventLogger
  from ...core.models.domain_events import PnLCalculation
  from ...core.errors.error_codes import ERROR_REGISTRY
  ```

- **UPDATE** `__init__` signature to add `correlation_id: str = None, pid: int = None, log_dir: Path = None`
- **ADD** logging initialization in `__init__`:
  ```python
  # Initialize logging infrastructure
  self.correlation_id = correlation_id or str(uuid.uuid4().hex)
  self.pid = pid or os.getpid()
  self.log_dir = log_dir
  
  # Initialize structured logger
  self.logger = StructuredLogger(
      component_name="PnLMonitor",
      correlation_id=self.correlation_id,
      pid=self.pid,
      log_dir=self.log_dir,
      engine=None
  )
  
  # Initialize domain event logger
  self.domain_event_logger = DomainEventLogger(self.log_dir)
  ```

- **ADD** method `_log_pnl_calculation()`:
  ```python
  def _log_pnl_calculation(self, pnl_data: Dict[str, Any]) -> None:
      """Log P&L calculation as domain event."""
      if not self.log_dir:
          return
      
      timestamp = datetime.now().isoformat()
      real_utc = datetime.now(timezone.utc).isoformat()
      
      calculation = PnLCalculation(
          timestamp=timestamp,
          real_utc_time=real_utc,
          correlation_id=self.correlation_id,
          pid=self.pid,
          realized_pnl=pnl_data.get('realized_pnl', 0.0),
          unrealized_pnl=pnl_data.get('unrealized_pnl', 0.0),
          total_pnl=pnl_data.get('total_pnl', 0.0),
          fees_paid=pnl_data.get('fees_paid', 0.0),
          funding_received=pnl_data.get('funding_received', 0.0),
          pnl_by_venue=pnl_data.get('pnl_by_venue', {}),
          pnl_by_asset=pnl_data.get('pnl_by_asset', {}),
          metadata={}
      )
      
      self.domain_event_logger.log_pnl_calculation(calculation)
  ```

- **CALL** `_log_pnl_calculation()` after every P&L calculation
- **UPDATE** all error logging with error codes (PNL-001 through PNL-005)

---

### 5. Position Update Handler

**File**: `backend/src/basis_strategy_v1/core/components/position_update_handler.py`

**Changes**:

- **ADD** imports:
  ```python
  from pathlib import Path
  import os
  import uuid
  from ...infrastructure.logging.structured_logger import StructuredLogger
  from ...infrastructure.logging.domain_event_logger import DomainEventLogger
  from ...core.models.domain_events import ReconciliationEvent
  from ...core.errors.error_codes import ERROR_REGISTRY
  ```

- **UPDATE** `__init__` signature to add `correlation_id: str = None, pid: int = None, log_dir: Path = None`
- **ADD** logging initialization
- **ADD** method `_log_reconciliation_event()`:
  ```python
  def _log_reconciliation_event(
      self,
      trigger_source: str,
      reconciliation_type: str,
      success: bool,
      simulated_positions: Dict[str, float],
      real_positions: Dict[str, float],
      mismatches: List[Dict[str, Any]],
      retry_attempt: Optional[int] = None,
      max_retries: Optional[int] = None
  ) -> None:
      """Log reconciliation event."""
      if not self.log_dir:
          return
      
      timestamp = datetime.now().isoformat()
      real_utc = datetime.now(timezone.utc).isoformat()
      
      event = ReconciliationEvent(
          timestamp=timestamp,
          real_utc_time=real_utc,
          correlation_id=self.correlation_id,
          pid=self.pid,
          trigger_source=trigger_source,
          reconciliation_type=reconciliation_type,
          success=success,
          simulated_positions=simulated_positions,
          real_positions=real_positions,
          mismatches=mismatches,
          retry_attempt=retry_attempt,
          max_retries=max_retries,
          metadata={}
      )
      
      self.domain_event_logger.log_reconciliation(event)
  ```

- **CALL** `_log_reconciliation_event()` after every reconciliation
- **UPDATE** error logging with error codes

---

### 6. Components Init

**File**: `backend/src/basis_strategy_v1/core/components/__init__.py`

**Changes**:

- **VERIFY** no Trade references remain

---

## Phase 7: Event Engine & Services (4 files)

### 1. Event Driven Strategy Engine

**File**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py`

**Current State**:

- Has `correlation_id` in `__init__` (line 92)
- Creates components but only passes `correlation_id` (line 144)
- No log directory creation
- No pid tracking

**Changes**:

- **ADD** imports at top:
  ```python
  import os
  import uuid
  from ...infrastructure.logging.log_directory_manager import LogDirectoryManager
  from ...infrastructure.logging.structured_logger import StructuredLogger
  ```

- **UPDATE** `__init__` method (around line 85-115):
  - **BEFORE** any component initialization, add:
  ```python
  # Generate correlation_id and pid for this run
  self.correlation_id = correlation_id or uuid.uuid4().hex
  self.pid = os.getpid()
  
  # Create log directory structure
  self.log_dir = LogDirectoryManager.create_run_logs(
      correlation_id=self.correlation_id,
      pid=self.pid,
      mode=self.mode,
      strategy=self.mode,  # or extract strategy name from config
      capital=self.initial_capital
  )
  
  # Initialize structured logger for engine
  self.logger = StructuredLogger(
      component_name="EventDrivenStrategyEngine",
      correlation_id=self.correlation_id,
      pid=self.pid,
      log_dir=self.log_dir,
      engine=self  # Pass self for timestamp access
  )
  
  self.logger.info(
      f"EventDrivenStrategyEngine initialized: mode={self.mode}, capital={self.initial_capital}",
      mode=self.mode,
      share_class=self.share_class,
      initial_capital=self.initial_capital
  )
  ```

- **UPDATE** ALL component initializations to pass `correlation_id`, `pid`, `log_dir`:
  ```python
  # Position Monitor (line ~136)
  self.position_monitor = PositionMonitor(
      self.config, 
      self.data_provider, 
      self.utility_manager, 
      self.venue_interface_factory,
      self.execution_mode,
      self.initial_capital,
      self.share_class,
      correlation_id=self.correlation_id,
      pid=self.pid,
      log_dir=self.log_dir
  )
  
  # Exposure Monitor
  self.exposure_monitor = ExposureMonitor(
      self.config,
      self.data_provider,
      self.utility_manager,
      correlation_id=self.correlation_id,
      pid=self.pid,
      log_dir=self.log_dir
  )
  
  # Risk Monitor
  self.risk_monitor = RiskMonitor(
      self.config,
      self.data_provider,
      self.utility_manager,
      correlation_id=self.correlation_id,
      pid=self.pid,
      log_dir=self.log_dir
  )
  
  # PnL Calculator
  self.pnl_calculator = PnLMonitor(
      self.config,
      self.data_provider,
      self.utility_manager,
      correlation_id=self.correlation_id,
      pid=self.pid,
      log_dir=self.log_dir
  )
  
  # Position Update Handler
  self.position_update_handler = PositionUpdateHandler(
      self.position_monitor,
      correlation_id=self.correlation_id,
      pid=self.pid,
      log_dir=self.log_dir
  )
  
  # Strategy Manager (already has these parameters from Phase 3)
  # Execution Manager (already renamed from VenueManager in Phase 4)
  ```

- **RENAME** attribute (line ~34): `self.execution_manager` → `self.execution_manager`
- **UPDATE** import (line ~34): `from ..execution.execution_manager import ExecutionManager`
- **UPDATE** all references to `self.execution_manager` → `self.execution_manager`
- **UPDATE** error logging throughout with error codes (ENGINE-001 through ENGINE-004)

---

### 2. Backtest Service

**File**: `backend/src/basis_strategy_v1/core/services/backtest_service.py`

**Changes**:

- No changes needed if EventDrivenStrategyEngine generates correlation_id
- **VERIFY** no Trade references remain

---

### 3. Live Service

**File**: `backend/src/basis_strategy_v1/core/services/live_service.py`

**Changes**:

- No changes needed if EventDrivenStrategyEngine generates correlation_id
- **VERIFY** no Trade references remain

---

### 4. API Main

**File**: `backend/src/basis_strategy_v1/api/main.py`

**Changes**:

- **ADD** correlation_id generation for API requests (if not already done by service layer)
- **VERIFY** correlation_id is passed through to services

---

## Implementation Order

1. **Phase 6.1**: PositionMonitor (foundation component)
2. **Phase 6.2**: ExposureMonitor (depends on positions)
3. **Phase 6.3**: RiskMonitor (depends on positions/exposures)
4. **Phase 6.4**: PnLMonitor (depends on positions)
5. **Phase 6.5**: PositionUpdateHandler (depends on position monitor)
6. **Phase 6.6**: Components **init** cleanup
7. **Phase 7.1**: EventDrivenStrategyEngine (orchestrates all components)
8. **Phase 7.2**: Services verification (backtest/live)
9. **Phase 7.3**: API verification

## Success Criteria

- All components use `StructuredLogger` and `DomainEventLogger`
- All legacy logging (`get_*_logger()`, `StandardizedLoggingMixin`) removed
- All components accept `correlation_id`, `pid`, `log_dir` parameters
- EventDrivenStrategyEngine creates log directory once and passes to all components
- All domain events logged to JSONL files
- All error logging uses error codes
- Log directory structure: `logs/{correlation_id}/{pid}/`
- All component logs in: `logs/{correlation_id}/{pid}/component_name.log`
- All domain events in: `logs/{correlation_id}/{pid}/events/*.jsonl`