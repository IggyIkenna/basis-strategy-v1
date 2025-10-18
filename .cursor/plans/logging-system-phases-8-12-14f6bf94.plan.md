<!-- 14f6bf94-8717-40a2-9397-2f09b9b7a682 d1d07d98-83b6-470f-987a-3ffe58030376 -->
# Complete Logging System Phases 8-12

## Overview

Complete configuration updates, comprehensive documentation updates, and test scaffolding for the unified execution flow and logging system while another agent works on Phases 3-7.

---

## PHASE 8: Configuration (12 files)

### 8.1 Config Models Update

**File**: `backend/src/basis_strategy_v1/infrastructure/config/models.py`

**Changes**:

1. Rename `VenueManagerConfig` class to `ExecutionManagerConfig` (line 333)
2. Update class docstring to reflect ExecutionManager purpose
3. Update all references in validators and comments
4. Keep field names unchanged (backward compatible at field level)

**Implementation**:

```python
class ExecutionManagerConfig(BaseModel):
    """Execution manager configuration model.
    
    Note: Renamed from VenueManagerConfig to align with ExecutionManager.
    ExecutionManager uses tight loop architecture and processes orders sequentially.
    """
    # Fields remain the same for backward compatibility
    # max_retry_attempts, tight_loop_timeout, retry_delay_seconds, etc.
```

### 8.2 Update All 10 Mode YAML Configs

**Files**: All files in `configs/modes/*.yaml`

- `pure_lending_usdt.yaml`
- `pure_lending_eth.yaml`
- `btc_basis.yaml`
- `eth_basis.yaml`
- `eth_leveraged.yaml`
- `eth_staking_only.yaml`
- `usdt_market_neutral.yaml`
- `usdt_market_neutral_no_leverage.yaml`
- `ml_btc_directional_usdt_margin.yaml`
- `ml_btc_directional_btc_margin.yaml`

**Changes** (all files):

```yaml
# OLD:
component_config:
  venue_manager:
    max_retry_attempts: 3
    tight_loop_timeout: 120
    # ...

# NEW:
component_config:
  execution_manager:  # RENAMED
    max_retry_attempts: 3
    tight_loop_timeout: 120
    # ... (all other fields unchanged)
```

**Search & Replace Pattern**:

- Find: `venue_manager:` (under component_config)
- Replace: `execution_manager:`
- Keep all nested fields unchanged

### 8.3 Update .gitignore

**File**: `.gitignore`

**Changes**:

```gitignore
# OLD (line 20):
backend/logs/

# NEW:
# Remove backend/logs/ (already have logs/ at line 19)
# logs/ at root covers all logs including backend/logs/
```

**Action**: Remove line 20 (`backend/logs/`) since `logs/` at line 19 already covers it

---

## PHASE 9: Documentation - Component Specs (14 files)

### 9.1 Core Component Specs (6 files)

#### Position Monitor

**File**: `docs/specs/01_POSITION_MONITOR.md`

**Add Section**: "Domain Event Logging" (after "Mode-Aware Behavior" section)

**Content**:

```markdown
## Domain Event Logging

### Event File
**File**: `logs/{correlation_id}/{pid}/events/positions.jsonl`

### Event Schema
Logs `PositionSnapshot` events after every position update:

\`\`\`python
{
    "timestamp": "2025-01-15T10:30:00",
    "real_utc_time": "2025-01-15T10:30:00.123456",
    "correlation_id": "abc123",
    "pid": 12345,
    "positions": {"aave:aToken:aUSDT": 10000.0, "wallet:BaseToken:USDT": 5000.0},
    "total_value_usd": 15000.0,
    "position_type": "simulated",
    "trigger_source": "execution_manager",
    "metadata": {}
}
\`\`\`

### Logging Pattern
\`\`\`python
def update_state(self, timestamp, trigger_source, execution_deltas=None):
    # ... position updates ...
    
    # Log position snapshot
    snapshot = PositionSnapshot(
        timestamp=timestamp.isoformat(),
        real_utc_time=datetime.utcnow().isoformat(),
        correlation_id=self.correlation_id,
        pid=self.pid,
        positions=self.positions.copy(),
        total_value_usd=self.total_value_usd,
        position_type="simulated" if self.execution_mode == "backtest" else "real",
        trigger_source=trigger_source
    )
    self.domain_event_logger.log_position_snapshot(snapshot)
\`\`\`

### Error Codes
- **POS-001**: Position update failed (HIGH)
- **POS-002**: Invalid position key (MEDIUM)
- **POS-003**: Position calculation error (HIGH)
- **POS-004**: Negative position detected (HIGH)
- **POS-005**: Position reconciliation mismatch (CRITICAL)
```

**Repeat Similar Pattern For**:

- `02_EXPOSURE_MONITOR.md` - Add ExposureSnapshot logging
- `03_RISK_MONITOR.md` - Add RiskAssessment logging
- `04_PNL_MONITOR.md` - Add PnLCalculation logging
- `05_STRATEGY_MANAGER.md` - Add StrategyDecision logging
- `11_POSITION_UPDATE_HANDLER.md` - Add ReconciliationEvent logging

### 9.2 Execution Manager Spec

**File**: `docs/specs/06_VENUE_MANAGER.md` → **RENAME** to `docs/specs/06_EXECUTION_MANAGER.md`

**Changes**:

1. **Rename file**: `06_VENUE_MANAGER.md` → `06_EXECUTION_MANAGER.md`
2. **Global replace**: `VenueManager` → `ExecutionManager`
3. **Global replace**: `venue_manager` → `execution_manager`
4. **Update title**: "Venue Manager Component Specification" → "Execution Manager Component Specification"
5. **Update Purpose section**: Replace with ExecutionManager purpose
6. **Remove all Trade references**: Replace with ExecutionHandshake
7. **Add Domain Event Logging section**:
```markdown
## Domain Event Logging

### Event Files
- `logs/{correlation_id}/{pid}/events/operation_executions.jsonl` - OperationExecutionEvent
- `logs/{correlation_id}/{pid}/events/atomic_groups.jsonl` - AtomicOperationGroupEvent
- `logs/{correlation_id}/{pid}/events/tight_loop.jsonl` - TightLoopExecutionEvent

### OperationExecutionEvent Schema
\`\`\`python
{
    "timestamp": "2025-01-15T10:30:00",
    "real_utc_time": "2025-01-15T10:30:00.123456",
    "correlation_id": "abc123",
    "pid": 12345,
    "operation_id": "supply_001",
    "operation_type": "supply",
    "venue": "aave_v3",
    "source_token": "USDT",
    "target_token": "aUSDT",
    "status": "confirmed",
    "expected_deltas": [{"position_key": "aave:aToken:aUSDT", "delta_amount": 10000.0, ...}],
    "actual_deltas": {"aave:aToken:aUSDT": 10000.0, "wallet:BaseToken:USDT": -10000.0},
    "fee_amount": 0.0,
    "fee_currency": "USDT",
    "execution_duration_ms": 125.5,
    "simulated": true
}
\`\`\`

### Tight Loop Execution Pattern
\`\`\`python
def process_orders(self, timestamp, orders):
    for order in orders:
        # Execute order
        handshake = self.venue_interface_manager.route_to_venue(order)
        
        # Log operation execution
        self._log_operation_execution(order, handshake)
        
        # Reconcile with retry
        reconciliation_success = self._reconcile_with_retry(timestamp, handshake)
        
        # Log tight loop execution
        self._log_tight_loop_execution(order, handshake, reconciliation_success)
\`\`\`
```


**Update Error Codes Section**:

```markdown
### Error Codes
- **EXEC-001**: Order execution failed (HIGH)
- **EXEC-002**: Venue interface unavailable (CRITICAL)
- **EXEC-003**: Invalid order format (MEDIUM)
- **EXEC-004**: Order validation failed (MEDIUM)
- **EXEC-005**: Reconciliation timeout (CRITICAL)
- **EXEC-006**: Atomic group rollback (HIGH)
- **EXEC-007**: Position mismatch after execution (CRITICAL)
- **EXEC-008**: Execution handshake invalid (HIGH)
```

### 9.3 Venue Interface Specs (2 files)

**Files**:

- `docs/specs/07_VENUE_INTERFACE_MANAGER.md`
- `docs/specs/07A_VENUE_INTERFACES.md`

**Changes**:

1. Remove all Trade references
2. Replace with ExecutionHandshake return types
3. Update method signatures: `execute_*() -> ExecutionHandshake`
4. Add error codes: VEN-001 through VEN-006

### 9.4 Other Component Specs (5 files)

**Files**:

- `docs/specs/08_EVENT_LOGGER.md` - Update with domain event logging patterns
- `docs/specs/13_BACKTEST_SERVICE.md` - Add correlation_id generation
- `docs/specs/14_LIVE_TRADING_SERVICE.md` - Add correlation_id generation
- `docs/specs/15_EVENT_DRIVEN_STRATEGY_ENGINE.md` - Add log directory creation
- `docs/specs/5B_BASE_STRATEGY_MANAGER.md` - Add expected_deltas calculation

**Key Updates**:

- Show correlation_id generation at engine initialization
- Show log directory creation using LogDirectoryManager
- Show passing correlation_id/pid/log_dir to all components
- Update ExecutionManager initialization (not VenueManager)

---

## PHASE 10: Documentation - Strategy Specs (9 files)

**Files**: All files in `docs/specs/strategies/`

- `01_PURE_LENDING_STRATEGY.md`
- `02_BTC_BASIS_STRATEGY.md`
- `03_ETH_BASIS_STRATEGY.md`
- `04_ETH_STAKING_ONLY_STRATEGY.md`
- `05_ETH_LEVERAGED_STRATEGY.md`
- `06_USDT_MARKET_NEUTRAL_NO_LEVERAGE_STRATEGY.md`
- `07_USDT_MARKET_NEUTRAL_STRATEGY.md`
- `08_ML_BTC_DIRECTIONAL_STRATEGY.md`
- `09_ML_USDT_DIRECTIONAL_STRATEGY.md`

**Changes** (all files):

### Add "Expected Deltas Calculation" Section

**For Pure Lending (01)**:

```markdown
## Expected Deltas Calculation

### Supply Operation
\`\`\`python
def _calculate_supply_deltas(self, amount, token):
    """Calculate expected deltas for AAVE supply operation."""
    # Get current AAVE supply index from utility_manager
    supply_index = self.utility_manager.get_aave_supply_index(token)
    
    # Calculate aToken amount: amount * supply_index
    atoken_amount = amount * supply_index
    
    return [
        {
            "position_key": f"aave:aToken:a{token}",
            "delta_amount": atoken_amount,
            "token": f"a{token}",
            "venue": "aave_v3",
            "operation_type": "supply"
        },
        {
            "position_key": f"wallet:BaseToken:{token}",
            "delta_amount": -amount,
            "token": token,
            "venue": "wallet",
            "operation_type": "supply"
        }
    ]
\`\`\`

### Order Creation with Expected Deltas
\`\`\`python
def _create_supply_order(self, amount):
    expected_deltas = self._calculate_supply_deltas(amount, "USDT")
    
    return Order(
        operation_id=uuid.uuid4().hex,
        venue="aave_v3",
        operation="supply",
        source_venue="wallet",
        target_venue="aave_v3",
        source_token="USDT",
        target_token="aUSDT",
        amount=amount,
        expected_deltas=expected_deltas,
        operation_details={
            "aave_supply_index": self.utility_manager.get_aave_supply_index("USDT"),
            "health_factor_before": self.risk_monitor.get_health_factor()
        }
    )
\`\`\`
```

**For Basis Trading (02, 03)**:

```markdown
## Expected Deltas Calculation

### Spot Trade
\`\`\`python
def _calculate_spot_trade_deltas(self, side, amount, price, token):
    """Calculate expected deltas for spot trade."""
    base_amount = amount if side == "BUY" else -amount
    quote_amount = -(amount * price) if side == "BUY" else amount * price
    
    return [
        {"position_key": f"binance:BaseToken:{token}", "delta_amount": base_amount},
        {"position_key": "binance:BaseToken:USDT", "delta_amount": quote_amount}
    ]
\`\`\`

### Perp Trade
\`\`\`python
def _calculate_perp_trade_deltas(self, side, amount, token):
    """Calculate expected deltas for perpetual futures."""
    delta_amount = amount if side == "LONG" else -amount
    
    return [
        {"position_key": f"binance:PerpPosition:{token}-PERP", "delta_amount": delta_amount}
    ]
\`\`\`
```

**For ETH Staking (04, 05)**:

```markdown
## Expected Deltas Calculation

### Stake Operation
\`\`\`python
def _calculate_stake_deltas(self, amount, lst_type):
    """Calculate expected deltas for ETH staking."""
    # Get current staking conversion rate
    if lst_type == "weeth":
        conversion_rate = self.utility_manager.get_weeth_conversion_rate()
        lst_token = "weETH"
        venue = "etherfi"
    else:
        conversion_rate = self.utility_manager.get_wsteth_conversion_rate()
        lst_token = "wstETH"
        venue = "lido"
    
    # Calculate LST amount
    lst_amount = amount * conversion_rate
    
    return [
        {"position_key": f"{venue}:LST:{lst_token}", "delta_amount": lst_amount},
        {"position_key": "wallet:BaseToken:ETH", "delta_amount": -amount}
    ]
\`\`\`
```

### Update Execution Flow Section

Replace Trade with ExecutionHandshake:

```markdown
## Execution Flow

1. Strategy Manager creates Orders with expected_deltas
2. ExecutionManager processes orders sequentially
3. VenueInterfaceManager routes to appropriate venue
4. Venue returns ExecutionHandshake with actual_deltas
5. ExecutionManager logs OperationExecutionEvent
6. PositionUpdateHandler reconciles expected vs actual deltas
7. TightLoopExecutionEvent logged for each operation
```

---

## PHASE 11: Documentation - Root Docs (13 files)

### 11.1 Create New LOGGING_GUIDE.md

**File**: `docs/LOGGING_GUIDE.md` ✨ **CREATE NEW**

**Contents** (comprehensive):

```markdown
# Logging Architecture Guide

**Purpose**: Comprehensive guide to the unified logging system
**Status**: ✅ CANONICAL REFERENCE
**Last Updated**: 2025-01-15

## Overview

The basis-strategy system uses a dual logging approach:
1. **Structured Component Logs** - Component-specific log files for debugging
2. **Domain Event Logs** - JSONL event files for comprehensive audit trail

## Log Directory Structure

### Directory Layout
\`\`\`
logs/
  {correlation_id}/              # Unique per run
    {pid}/                        # Process ID
      api.log                     # API request/response logs
      position_monitor.log        # Position monitor component logs
      exposure_monitor.log        # Exposure monitor logs
      risk_monitor.log            # Risk monitor logs
      pnl_monitor.log             # P&L monitor logs
      strategy_manager.log        # Strategy manager logs
      execution_manager.log       # Execution manager logs
      events/                     # Domain events directory
        positions.jsonl           # PositionSnapshot events
        exposures.jsonl           # ExposureSnapshot events
        risk_assessments.jsonl    # RiskAssessment events
        pnl_calculations.jsonl    # PnLCalculation events
        strategy_decisions.jsonl  # StrategyDecision events
        operation_executions.jsonl # OperationExecutionEvent
        atomic_groups.jsonl       # AtomicOperationGroupEvent
        tight_loop.jsonl          # TightLoopExecutionEvent
        reconciliation.jsonl      # ReconciliationEvent
\`\`\`

### Log Directory Creation
\`\`\`python
from infrastructure.logging.log_directory_manager import LogDirectoryManager

# At engine initialization
log_dir = LogDirectoryManager.create_run_logs(
    correlation_id=correlation_id,
    pid=os.getpid(),
    mode="pure_lending_usdt",
    strategy="pure_lending",
    capital=10000.0
)
# Returns: Path("logs/{correlation_id}/{pid}/")
\`\`\`

## Component Logs (Structured Logger)

### Purpose
- Debug-level operational logs
- Error stack traces
- Performance metrics
- Component-specific diagnostics

### Log Files
Each component gets its own log file:
- `position_monitor.log`
- `exposure_monitor.log`
- `risk_monitor.log`
- `pnl_monitor.log`
- `strategy_manager.log`
- `execution_manager.log`

### Initialization
\`\`\`python
from infrastructure.logging.structured_logger import StructuredLogger

self.logger = StructuredLogger(
    component_name="PositionMonitor",
    log_dir=log_dir,
    correlation_id=correlation_id,
    pid=pid
)
\`\`\`

### Usage
\`\`\`python
self.logger.info("Position updated", extra={
    "trigger_source": "execution_manager",
    "positions_count": len(self.positions)
})

self.logger.error("Position update failed", extra={
    "error_code": "POS-001",
    "stack_trace": traceback.format_exc()
})
\`\`\`

## Domain Event Logs (Domain Event Logger)

### Purpose
- Complete audit trail
- State snapshots
- Event replay capability
- Analysis and debugging

### Event Files
Each event type gets its own JSONL file in `events/` subdirectory.

### Initialization
\`\`\`python
from infrastructure.logging.domain_event_logger import DomainEventLogger

self.domain_event_logger = DomainEventLogger(
    log_dir=log_dir,
    correlation_id=correlation_id,
    pid=pid
)
\`\`\`

### Event Schemas

#### 1. PositionSnapshot
**File**: `events/positions.jsonl`
**Logged by**: PositionMonitor
**Frequency**: Every position update

\`\`\`json
{
  "timestamp": "2025-01-15T10:30:00",
  "real_utc_time": "2025-01-15T10:30:00.123456",
  "correlation_id": "abc123",
  "pid": 12345,
  "positions": {
    "aave:aToken:aUSDT": 10000.0,
    "wallet:BaseToken:USDT": 5000.0
  },
  "total_value_usd": 15000.0,
  "position_type": "simulated",
  "trigger_source": "execution_manager",
  "metadata": {}
}
\`\`\`

#### 2. OperationExecutionEvent
**File**: `events/operation_executions.jsonl`
**Logged by**: ExecutionManager
**Frequency**: Every operation execution

\`\`\`json
{
  "timestamp": "2025-01-15T10:30:00",
  "real_utc_time": "2025-01-15T10:30:00.123456",
  "correlation_id": "abc123",
  "pid": 12345,
  "operation_id": "supply_001",
  "operation_type": "supply",
  "venue": "aave_v3",
  "source_token": "USDT",
  "target_token": "aUSDT",
  "status": "confirmed",
  "expected_deltas": [
    {
      "position_key": "aave:aToken:aUSDT",
      "delta_amount": 10000.0,
      "token": "aUSDT",
      "venue": "aave_v3",
      "operation_type": "supply"
    }
  ],
  "actual_deltas": {
    "aave:aToken:aUSDT": 10000.0,
    "wallet:BaseToken:USDT": -10000.0
  },
  "fee_amount": 0.0,
  "fee_currency": "USDT",
  "execution_duration_ms": 125.5,
  "simulated": true,
  "error_code": null,
  "error_message": null
}
\`\`\`

#### 3. TightLoopExecutionEvent
**File**: `events/tight_loop.jsonl`
**Logged by**: ExecutionManager
**Frequency**: Every tight loop cycle

\`\`\`json
{
  "timestamp": "2025-01-15T10:30:00",
  "real_utc_time": "2025-01-15T10:30:00.123456",
  "correlation_id": "abc123",
  "pid": 12345,
  "operation_id": "supply_001",
  "execution_success": true,
  "reconciliation_success": true,
  "retry_count": 0,
  "total_duration_ms": 150.5,
  "execution_duration_ms": 125.5,
  "reconciliation_duration_ms": 25.0
}
\`\`\`

[Continue with all 12 event schemas...]

## Operation Types

### CEX Operations
- **SPOT_TRADE**: Buy/sell on spot market
- **PERP_TRADE**: Open/close perpetual futures positions

### DeFi Operations
- **SUPPLY**: Supply assets to lending protocols (AAVE, Morpho)
- **BORROW**: Borrow assets from lending protocols
- **REPAY**: Repay borrowed assets
- **WITHDRAW**: Withdraw supplied assets
- **STAKE**: Stake ETH for LST tokens (stETH, weETH)
- **UNSTAKE**: Unstake LST tokens back to ETH
- **SWAP**: Swap tokens on DEX (Uniswap)

### Transfer Operations
- **TRANSFER**: Move assets between venues (wallet → wallet)

### Flash Loan Operations
- **FLASH_BORROW**: Borrow in flash loan
- **FLASH_REPAY**: Repay flash loan

## Atomic Operations

### Atomic Group Pattern
Multiple operations executed atomically (all succeed or all fail).

\`\`\`python
# Create atomic group
atomic_group_id = uuid.uuid4().hex

orders = [
    Order(
        operation_id=f"{atomic_group_id}_1",
        atomic_group_id=atomic_group_id,
        sequence_in_group=0,
        # ... supply order
    ),
    Order(
        operation_id=f"{atomic_group_id}_2",
        atomic_group_id=atomic_group_id,
        sequence_in_group=1,
        # ... borrow order
    )
]
\`\`\`

### AtomicOperationGroupEvent
\`\`\`json
{
  "timestamp": "2025-01-15T10:30:00",
  "real_utc_time": "2025-01-15T10:30:00.123456",
  "correlation_id": "abc123",
  "pid": 12345,
  "atomic_group_id": "group_001",
  "operation_ids": ["supply_001", "borrow_001"],
  "operation_types": ["supply", "borrow"],
  "all_succeeded": true,
  "rollback_occurred": false,
  "total_duration_ms": 250.5
}
\`\`\`

## Error Code Registry

### Component Prefixes
- **POS-xxx**: PositionMonitor
- **EXP-xxx**: ExposureMonitor
- **RISK-xxx**: RiskMonitor
- **PNL-xxx**: PnLMonitor
- **STRAT-xxx**: StrategyManager
- **EXEC-xxx**: ExecutionManager
- **VEN-xxx**: VenueInterfaceManager
- **ENGINE-xxx**: EventDrivenStrategyEngine

### Error Severity
- **CRITICAL**: System failure, requires restart
- **HIGH**: Component failure, retry required
- **MEDIUM**: Degraded functionality, log and continue
- **LOW**: Warning, no action needed

### Example Error Codes
- **EXEC-001**: Order execution failed (HIGH)
- **EXEC-005**: Reconciliation timeout (CRITICAL)
- **POS-005**: Position reconciliation mismatch (CRITICAL)
- **RISK-001**: Risk limit breached (HIGH)

## Timestamp Strategy

### Engine Timestamp (Backtest)
- **Source**: EventDrivenStrategyEngine clock
- **Format**: `pd.Timestamp` from data provider
- **Used for**: All business logic, event timestamps

### Real UTC Time (Live)
- **Source**: `datetime.utcnow()`
- **Format**: ISO 8601 string
- **Used for**: Audit trail, real-world correlation

### Pattern
\`\`\`python
# In domain event
timestamp=timestamp.isoformat(),        # Engine timestamp
real_utc_time=datetime.utcnow().isoformat()  # Actual UTC time
\`\`\`

## Debugging Workflows

### Find Failed Operations
\`\`\`bash
# Find all failed operations
jq 'select(.status == "failed")' logs/{correlation_id}/{pid}/events/operation_executions.jsonl

# Count failures by operation type
jq -r '.operation_type' logs/{correlation_id}/{pid}/events/operation_executions.jsonl | sort | uniq -c
\`\`\`

### Trace Single Operation
\`\`\`bash
# Get all events for operation_id
grep "supply_001" logs/{correlation_id}/{pid}/events/*.jsonl
\`\`\`

### Position History
\`\`\`bash
# Get position history for specific position_key
jq '.positions["aave:aToken:aUSDT"]' logs/{correlation_id}/{pid}/events/positions.jsonl
\`\`\`

### Reconciliation Issues
\`\`\`bash
# Find reconciliation failures
jq 'select(.reconciliation_success == false)' logs/{correlation_id}/{pid}/events/tight_loop.jsonl
\`\`\`

## Log Querying Examples

### Using jq
\`\`\`bash
# Get all positions at specific timestamp
jq 'select(.timestamp == "2025-01-15T10:30:00")' events/positions.jsonl

# Calculate total USD value over time
jq -r '[.timestamp, .total_value_usd] | @csv' events/positions.jsonl

# Find operations with high execution time
jq 'select(.execution_duration_ms > 1000)' events/operation_executions.jsonl
\`\`\`

### Using grep
\`\`\`bash
# Find all supply operations
grep '"operation_type":"supply"' events/operation_executions.jsonl

# Find all CRITICAL errors
grep '"severity":"CRITICAL"' *.log

# Find specific correlation_id
grep "abc123" events/*.jsonl
\`\`\`

## Performance Considerations

### Buffered Writing
- Events buffered in memory (100 events)
- Flushed every 5 seconds or on buffer full
- Prevents I/O bottleneck

### JSONL Format
- One event per line (newline-delimited JSON)
- Efficient for streaming and appending
- Easy to parse with standard tools

### Log Rotation
- Automatic rotation at 100MB per file
- Keep last 7 days in backtest mode
- Keep last 30 days in live mode

## Integration with Results Store

### Backtest Completion
At backtest completion, Results Store:
1. Copies all log files to `results/{backtest_id}/logs/`
2. Exports domain events to CSV for analysis
3. Generates summary reports

### CSV Export Format
\`\`\`python
# Export positions to CSV
df = pd.read_json("events/positions.jsonl", lines=True)
df.to_csv("results/{backtest_id}/positions.csv", index=False)
\`\`\`

## Reference Documentation

- **Domain Event Models**: `backend/src/basis_strategy_v1/core/models/domain_events.py`
- **Structured Logger**: `backend/src/basis_strategy_v1/infrastructure/logging/structured_logger.py`
- **Domain Event Logger**: `backend/src/basis_strategy_v1/infrastructure/logging/domain_event_logger.py`
- **Log Directory Manager**: `backend/src/basis_strategy_v1/infrastructure/logging/log_directory_manager.py`
- **Error Code Registry**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`
```

### 11.2 Major Architecture Docs (7 files)

#### REFERENCE_ARCHITECTURE_CANONICAL.md

**Changes**:

1. Replace all VenueManager → ExecutionManager
2. Replace all Trade → ExecutionHandshake
3. Add "Logging Architecture" section
4. Update "Component Initialization" section with correlation_id/pid/log_dir
5. Update all diagrams and flow charts

#### ORDER_TRADE_EXECUTION_DELTAS_FLOW.md

**Changes**:

1. Update title: "Order → ExecutionHandshake → execution_deltas Flow"
2. Replace Trade with ExecutionHandshake throughout
3. Update data flow diagrams
4. Add expected_deltas calculation examples
5. Update ExecutionManager conversion method

#### TIGHT_LOOP_ARCHITECTURE.md

**Changes**:

1. Update ExecutionManager references (not VenueManager)
2. Update tight loop flow with ExecutionHandshake
3. Add domain event logging to tight loop cycle
4. Update retry logic examples

#### ERROR_HANDLING_PATTERNS.md

**Changes**:

1. Add error code registry reference
2. Update component error codes (EXEC-xxx, POS-xxx, etc.)
3. Add structured error logging patterns
4. Update error propagation rules

#### HEALTH_ERROR_SYSTEMS.md

**Changes**:

1. Update health integration with ExecutionManager
2. Add correlation_id to health checks
3. Update error logging patterns

#### WORKFLOW_GUIDE.md

**Changes**:

1. Update execution flow with ExecutionManager
2. Replace Trade with ExecutionHandshake
3. Update component initialization pattern
4. Add logging integration examples

#### ARCHITECTURAL_DECISION_RECORDS.md

**Changes**:

1. Add ADR for VenueManager → ExecutionManager rename
2. Add ADR for Trade → ExecutionHandshake migration
3. Add ADR for unified logging architecture
4. Add ADR for domain event logging

### 11.3 Supporting Docs (6 files)

#### MODES.md, STRATEGY_MODES.md, MODE_SPECIFIC_BEHAVIOR_GUIDE.md

**Changes**:

- Update config examples: venue_manager → execution_manager
- Update execution flow references

#### COMPONENT_SPECS_INDEX.md

**Changes**:

- Update spec link: 06_VENUE_MANAGER.md → 06_EXECUTION_MANAGER.md
- Update descriptions

#### CODE_STRUCTURE_PATTERNS.md, TARGET_REPOSITORY_STRUCTURE.md

**Changes**:

- Update code examples with ExecutionManager
- Update logging patterns

---

## PHASE 12: Testing (8 new test files)

### 12.1 Unit Test Scaffolds (5 files)

#### Test File 1: test_execution.py

**File**: `tests/unit/models/test_execution.py`

**Purpose**: Test ExecutionHandshake model validation

**Contents**:

```python
"""
Unit tests for ExecutionHandshake model.

Tests the execution result model that replaces Trade.
"""
import pytest
from datetime import datetime
from backend.src.basis_strategy_v1.core.models.execution import (
    ExecutionHandshake,
    ExecutionStatus,
    OperationType
)

class TestExecutionHandshake:
    """Test ExecutionHandshake model validation."""
    
    def test_successful_cex_trade(self):
        """Test successful CEX spot trade execution."""
        # TODO: Implement after Phase 5 completes venue interfaces
        handshake = ExecutionHandshake(
            operation_id="spot_001",
            status=ExecutionStatus.CONFIRMED,
            actual_deltas={
                "binance:BaseToken:BTC": 0.5,
                "binance:BaseToken:USDT": -22500.0
            },
            execution_details={
                "executed_price": 45000.0,
                "executed_amount": 0.5
            },
            fee_amount=22.5,
            fee_currency="USDT",
            submitted_at=datetime.now(),
            executed_at=datetime.now(),
            simulated=False
        )
        
        assert handshake.was_successful()
        assert not handshake.was_failed()
        assert handshake.get_total_cost() > 0
    
    def test_failed_defi_operation(self):
        """Test failed DeFi supply operation."""
        # TODO: Implement after Phase 5 completes venue interfaces
        handshake = ExecutionHandshake(
            operation_id="supply_001",
            status=ExecutionStatus.FAILED,
            actual_deltas={},
            execution_details={},
            error_code="EXEC-001",
            error_message="Insufficient balance",
            submitted_at=datetime.now(),
            simulated=True
        )
        
        assert handshake.was_failed()
        assert not handshake.was_successful()
        assert handshake.error_code == "EXEC-001"
    
    def test_pending_operation(self):
        """Test pending operation status."""
        # TODO: Implement after Phase 5 completes venue interfaces
        pass
    
    def test_rolled_back_operation(self):
        """Test atomic group rollback."""
        # TODO: Implement after Phase 5 completes venue interfaces
        pass

# TODO: Add tests for:
# - validation errors
# - edge cases (zero amounts, negative fees, etc.)
# - simulated vs real execution
# - position delta calculations
```

#### Test File 2: test_domain_events.py

**File**: `tests/unit/models/test_domain_events.py`

**Purpose**: Test all 12 domain event models

**Contents**:

```python
"""
Unit tests for domain event models.

Tests all 12 domain event Pydantic models for JSONL logging.
"""
import pytest
from datetime import datetime
from backend.src.basis_strategy_v1.core.models.domain_events import (
    PositionSnapshot,
    ExposureSnapshot,
    RiskAssessment,
    PnLCalculation,
    StrategyDecision,
    OperationExecutionEvent,
    AtomicOperationGroupEvent,
    TightLoopExecutionEvent,
    ReconciliationEvent,
    ExecutionDeltaEvent,
    HealthStatusEvent,
    SystemErrorEvent
)

class TestPositionSnapshot:
    """Test PositionSnapshot event model."""
    
    def test_valid_snapshot(self):
        """Test valid position snapshot creation."""
        # TODO: Implement after Phase 3 completes PositionMonitor updates
        snapshot = PositionSnapshot(
            timestamp="2025-01-15T10:30:00",
            real_utc_time="2025-01-15T10:30:00.123456",
            correlation_id="abc123",
            pid=12345,
            positions={"aave:aToken:aUSDT": 10000.0},
            total_value_usd=10000.0,
            position_type="simulated"
        )
        
        assert snapshot.correlation_id == "abc123"
        assert snapshot.pid == 12345
        assert len(snapshot.positions) == 1

class TestOperationExecutionEvent:
    """Test OperationExecutionEvent model."""
    
    def test_successful_execution(self):
        """Test successful operation execution event."""
        # TODO: Implement after Phase 4 completes ExecutionManager updates
        pass
    
    def test_failed_execution(self):
        """Test failed operation execution event."""
        # TODO: Implement after Phase 4 completes ExecutionManager updates
        pass

# TODO: Add test classes for all 12 event types
# TODO: Test validation errors
# TODO: Test JSON serialization
# TODO: Test edge cases
```

#### Test File 3: test_log_directory_manager.py

**File**: `tests/unit/logging/test_log_directory_manager.py`

**Purpose**: Test log directory creation and metadata

**Contents**:

```python
"""
Unit tests for LogDirectoryManager.

Tests log directory structure creation and metadata.
"""
import pytest
from pathlib import Path
import json
from backend.src.basis_strategy_v1.infrastructure.logging.log_directory_manager import (
    LogDirectoryManager
)

class TestLogDirectoryManager:
    """Test log directory management."""
    
    def test_create_run_logs(self, tmp_path):
        """Test log directory creation."""
        # TODO: Implement after Phase 2 LogDirectoryManager is verified
        log_dir = LogDirectoryManager.create_run_logs(
            correlation_id="test123",
            pid=12345,
            mode="pure_lending_usdt",
            strategy="pure_lending",
            capital=10000.0,
            base_dir=tmp_path
        )
        
        assert log_dir.exists()
        assert (log_dir / "events").exists()
        assert (log_dir / "metadata.json").exists()
    
    def test_metadata_contents(self, tmp_path):
        """Test metadata file contents."""
        # TODO: Implement after Phase 2 LogDirectoryManager is verified
        pass
    
    def test_directory_permissions(self, tmp_path):
        """Test directory has correct permissions."""
        # TODO: Implement
        pass

# TODO: Add tests for:
# - multiple runs with same correlation_id
# - invalid parameters
# - cleanup functionality
```

#### Test File 4: test_domain_event_logger.py

**File**: `tests/unit/logging/test_domain_event_logger.py`

**Purpose**: Test JSONL event writing

**Contents**:

```python
"""
Unit tests for DomainEventLogger.

Tests JSONL event file writing and buffering.
"""
import pytest
from pathlib import Path
import json
from backend.src.basis_strategy_v1.infrastructure.logging.domain_event_logger import (
    DomainEventLogger
)
from backend.src.basis_strategy_v1.core.models.domain_events import PositionSnapshot

class TestDomainEventLogger:
    """Test domain event logging."""
    
    def test_log_position_snapshot(self, tmp_path):
        """Test logging position snapshot to JSONL."""
        # TODO: Implement after Phase 2 DomainEventLogger is verified
        logger = DomainEventLogger(
            log_dir=tmp_path,
            correlation_id="test123",
            pid=12345
        )
        
        snapshot = PositionSnapshot(
            timestamp="2025-01-15T10:30:00",
            real_utc_time="2025-01-15T10:30:00.123456",
            correlation_id="test123",
            pid=12345,
            positions={"aave:aToken:aUSDT": 10000.0},
            total_value_usd=10000.0,
            position_type="simulated"
        )
        
        logger.log_position_snapshot(snapshot)
        
        # Verify JSONL file created
        events_file = tmp_path / "events" / "positions.jsonl"
        assert events_file.exists()
        
        # Verify content
        with open(events_file) as f:
            line = f.readline()
            event = json.loads(line)
            assert event["correlation_id"] == "test123"
    
    def test_buffered_writing(self, tmp_path):
        """Test event buffering and flushing."""
        # TODO: Implement after Phase 2 DomainEventLogger is verified
        pass
    
    def test_multiple_event_types(self, tmp_path):
        """Test logging different event types."""
        # TODO: Implement after Phase 2 DomainEventLogger is verified
        pass

# TODO: Add tests for:
# - all 12 event types
# - buffer overflow
# - concurrent writes
# - error handling
```

#### Test File 5: test_strategy_manager_deltas.py

**File**: `tests/unit/components/test_strategy_manager_deltas.py`

**Purpose**: Test expected_deltas calculation

**Contents**:

```python
"""
Unit tests for StrategyManager expected_deltas calculation.

Tests all operation-specific delta calculators.
"""
import pytest
from backend.src.basis_strategy_v1.core.components.strategy_manager import StrategyManager

class TestExpectedDeltasCalculation:
    """Test expected deltas calculation methods."""
    
    def test_spot_trade_deltas(self, mock_config, mock_data_provider):
        """Test spot trade delta calculation."""
        # TODO: Implement after Phase 3 completes StrategyManager updates
        # strategy_manager = StrategyManager(...)
        # deltas = strategy_manager._calculate_spot_trade_deltas(...)
        # assert expected results
        pass
    
    def test_supply_deltas_aave(self, mock_config, mock_data_provider):
        """Test AAVE supply delta calculation with supply index."""
        # TODO: Implement after Phase 3 completes StrategyManager updates
        pass
    
    def test_stake_deltas_eth(self, mock_config, mock_data_provider):
        """Test ETH staking delta calculation with conversion rate."""
        # TODO: Implement after Phase 3 completes StrategyManager updates
        pass
    
    def test_perp_trade_deltas(self, mock_config, mock_data_provider):
        """Test perpetual futures delta calculation."""
        # TODO: Implement after Phase 3 completes StrategyManager updates
        pass

# TODO: Add tests for all operation types:
# - spot_trade, perp_trade
# - supply, borrow, repay, withdraw
# - stake, unstake
# - swap, transfer
```

### 12.2 Integration Test Scaffolds (3 files)

#### Test File 6: test_execution_flow.py

**File**: `tests/integration/test_execution_flow.py`

**Purpose**: Test Order → ExecutionHandshake flow

**Contents**:

```python
"""
Integration tests for execution flow.

Tests complete Order → ExecutionHandshake → reconciliation flow.
"""
import pytest
from backend.src.basis_strategy_v1.core.models.order import Order
from backend.src.basis_strategy_v1.core.execution.execution_manager import ExecutionManager

class TestExecutionFlow:
    """Test complete execution flow integration."""
    
    def test_order_to_handshake_cex(self, real_execution_manager):
        """Test CEX order execution flow."""
        # TODO: Implement after Phase 4-5 complete
        # order = Order(...)
        # handshake = execution_manager.process_orders(timestamp, [order])[0]
        # assert handshake.was_successful()
        pass
    
    def test_order_to_handshake_defi(self, real_execution_manager):
        """Test DeFi order execution flow."""
        # TODO: Implement after Phase 4-5 complete
        pass
    
    def test_failed_order_handling(self, real_execution_manager):
        """Test failed order execution handling."""
        # TODO: Implement after Phase 4-5 complete
        pass

# TODO: Add tests for:
# - atomic operations
# - retry logic
# - reconciliation flow
```

#### Test File 7: test_structured_logging.py

**File**: `tests/integration/test_structured_logging.py`

**Purpose**: Test log directory and event files

**Contents**:

```python
"""
Integration tests for structured logging.

Tests complete logging flow with real components.
"""
import pytest
from pathlib import Path
import json

class TestStructuredLogging:
    """Test logging integration."""
    
    def test_log_directory_creation(self, real_engine):
        """Test log directory created on engine start."""
        # TODO: Implement after Phase 7 completes engine updates
        # engine = EventDrivenStrategyEngine(...)
        # assert engine.log_dir.exists()
        # assert (engine.log_dir / "events").exists()
        pass
    
    def test_event_files_created(self, real_engine):
        """Test all event JSONL files created."""
        # TODO: Implement after Phase 6-7 complete
        pass
    
    def test_component_logs_created(self, real_engine):
        """Test component-specific log files created."""
        # TODO: Implement after Phase 6-7 complete
        pass

# TODO: Add tests for:
# - event writing during execution
# - log file rotation
# - metadata accuracy
```

#### Test File 8: test_atomic_operations.py

**File**: `tests/integration/test_atomic_operations.py`

**Purpose**: Test atomic operation groups

**Contents**:

```python
"""
Integration tests for atomic operations.

Tests atomic operation group execution and rollback.
"""
import pytest

class TestAtomicOperations:
    """Test atomic operation groups."""
    
    def test_successful_atomic_group(self, real_execution_manager):
        """Test successful atomic operation group."""
        # TODO: Implement after Phase 4-5 complete
        # Create atomic group with multiple orders
        # Execute and verify all succeed
        pass
    
    def test_atomic_group_rollback(self, real_execution_manager):
        """Test atomic group rollback on failure."""
        # TODO: Implement after Phase 4-5 complete
        # Create atomic group where one order fails
        # Verify all rolled back
        pass
    
    def test_atomic_group_logging(self, real_execution_manager):
        """Test AtomicOperationGroupEvent logging."""
        # TODO: Implement after Phase 4-6 complete
        pass

# TODO: Add tests for:
# - partial failure handling
# - nested atomic groups (if supported)
# - event logging for rollbacks
```

### 12.3 Update Existing Tests

**Pattern**: Search and replace across all existing test files

**Search for**:

- `Trade` (model)
- `VenueManager` (class)
- `venue_manager` (variable)

**Replace with**:

- `ExecutionHandshake`
- `ExecutionManager`
- `execution_manager`

**Files to Update**:

- All files in `tests/unit/`
- All files in `tests/integration/`
- All files in `tests/e2e/`

**Mock Updates**:

```python
# OLD mock return value
mock_venue_manager.process_orders.return_value = [Mock(Trade)]

# NEW mock return value
mock_execution_manager.process_orders.return_value = [Mock(ExecutionHandshake)]
```

---

## Implementation Order

1. **Phase 8**: Configuration (fastest, enables other work)
2. **Phase 9**: Component Specs (documents new patterns)
3. **Phase 10**: Strategy Specs (builds on component docs)
4. **Phase 11**: Root Docs (comprehensive architecture)
5. **Phase 12**: Test Scaffolds (enables future testing)

## Validation Checklist

### Phase 8 Complete

- [ ] ExecutionManagerConfig class renamed in models.py
- [ ] All 10 mode YAML files updated (venue_manager → execution_manager)
- [ ] .gitignore cleaned up (backend/logs/ removed)
- [ ] Config validation tests still pass

### Phase 9 Complete

- [ ] All 6 core component specs have Domain Event Logging section
- [ ] 06_VENUE_MANAGER.md renamed to 06_EXECUTION_MANAGER.md
- [ ] All Trade references removed from execution specs
- [ ] All specs have error code documentation

### Phase 10 Complete

- [ ] All 9 strategy specs have Expected Deltas Calculation section
- [ ] All strategy specs updated with ExecutionHandshake examples
- [ ] Order creation examples show expected_deltas population

### Phase 11 Complete

- [ ] LOGGING_GUIDE.md created with complete documentation
- [ ] 7 major architecture docs updated (ExecutionManager, ExecutionHandshake)
- [ ] 6 supporting docs updated (config examples, references)
- [ ] All diagrams and flowcharts updated

### Phase 12 Complete

- [ ] 5 unit test scaffolds created with TODO markers
- [ ] 3 integration test scaffolds created with TODO markers
- [ ] Test files reference Phase 3-7 implementation work
- [ ] Existing tests updated (Trade → ExecutionHandshake, VenueManager → ExecutionManager)

## Success Criteria

1. **Configuration Consistency**: All configs use execution_manager, no venue_manager references
2. **Documentation Completeness**: All specs and docs reflect ExecutionManager/ExecutionHandshake architecture
3. **Test Readiness**: Test scaffolds ready for implementation completion
4. **Zero Breaking Changes**: Existing functionality preserved, only naming changes
5. **Quality Gate Ready**: System ready for Phase 13 validation

### To-dos

- [ ] Phase 8: Update configuration (models.py class rename, 10 YAML configs, .gitignore)
- [ ] Phase 9: Update 14 component spec docs (add domain event logging, rename execution manager, remove Trade)
- [ ] Phase 10: Update 9 strategy spec docs (add expected_deltas calculation, update execution flow)
- [ ] Phase 11: Create LOGGING_GUIDE.md and update 12 root documentation files
- [ ] Phase 12: Create 8 test file scaffolds with TODO markers referencing Phase 3-7 implementation