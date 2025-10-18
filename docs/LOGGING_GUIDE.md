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
```
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
```

### Log Directory Creation
```python
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
```

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
```python
from infrastructure.logging.structured_logger import StructuredLogger

self.logger = StructuredLogger(
    component_name="PositionMonitor",
    log_dir=log_dir,
    correlation_id=correlation_id,
    pid=pid
)
```

### Usage
```python
self.logger.info("Position updated", extra={
    "trigger_source": "execution_manager",
    "positions_count": len(self.positions)
})

self.logger.error("Position update failed", extra={
    "error_code": "POS-001",
    "stack_trace": traceback.format_exc()
})
```

## Domain Event Logs (Domain Event Logger)

### Purpose
- Complete audit trail
- State snapshots
- Event replay capability
- Analysis and debugging

### Event Files
Each event type gets its own JSONL file in `events/` subdirectory.

### Initialization
```python
from infrastructure.logging.domain_event_logger import DomainEventLogger

self.domain_event_logger = DomainEventLogger(
    log_dir=log_dir,
    correlation_id=correlation_id,
    pid=pid
)
```

### Event Schemas

#### 1. PositionSnapshot
**File**: `events/positions.jsonl`
**Logged by**: PositionMonitor
**Frequency**: Every position update

```json
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
```

#### 2. OperationExecutionEvent
**File**: `events/operation_executions.jsonl`
**Logged by**: ExecutionManager
**Frequency**: Every operation execution

```json
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
```

#### 3. TightLoopExecutionEvent
**File**: `events/tight_loop.jsonl`
**Logged by**: ExecutionManager
**Frequency**: Every tight loop cycle

```json
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
```

#### 4. ExposureSnapshot
**File**: `events/exposures.jsonl`
**Logged by**: ExposureMonitor
**Frequency**: Every exposure calculation

```json
{
  "timestamp": "2025-01-15T10:30:00",
  "real_utc_time": "2025-01-15T10:30:00.123456",
  "correlation_id": "abc123",
  "pid": 12345,
  "net_delta_usd": 0.0,
  "asset_exposures": {
    "USDT": {"quantity": 10000.0, "usd_value": 10000.0, "percentage": 0.67},
    "ETH": {"quantity": 2.0, "usd_value": 5000.0, "percentage": 0.33}
  },
  "total_value_usd": 15000.0,
  "share_class_value": 15000.0,
  "metadata": {}
}
```

#### 5. RiskAssessment
**File**: `events/risk_assessments.jsonl`
**Logged by**: RiskMonitor
**Frequency**: Every risk calculation

```json
{
  "timestamp": "2025-01-15T10:30:00",
  "real_utc_time": "2025-01-15T10:30:00.123456",
  "correlation_id": "abc123",
  "pid": 12345,
  "health_factor": 1.85,
  "ltv_ratio": 0.65,
  "liquidation_threshold": 0.80,
  "margin_usage": 0.45,
  "risk_score": 0.25,
  "risk_level": "low",
  "breach_detected": false,
  "metadata": {}
}
```

#### 6. PnLCalculation
**File**: `events/pnl_calculations.jsonl`
**Logged by**: PnLMonitor
**Frequency**: Every P&L calculation

```json
{
  "timestamp": "2025-01-15T10:30:00",
  "real_utc_time": "2025-01-15T10:30:00.123456",
  "correlation_id": "abc123",
  "pid": 12345,
  "total_pnl_usd": 150.25,
  "total_pnl_share_class": 150.25,
  "pnl_attribution": {
    "supply_yield": 45.50,
    "transaction_costs": -2.25,
    "funding_pnl": 0.0
  },
  "period_start": "2025-01-15T09:30:00",
  "period_end": "2025-01-15T10:30:00",
  "metadata": {}
}
```

#### 7. StrategyDecision
**File**: `events/strategy_decisions.jsonl`
**Logged by**: StrategyManager
**Frequency**: Every strategy decision

```json
{
  "timestamp": "2025-01-15T10:30:00",
  "real_utc_time": "2025-01-15T10:30:00.123456",
  "correlation_id": "abc123",
  "pid": 12345,
  "strategy_name": "pure_lending_usdt",
  "decision_type": "rebalance",
  "orders_generated": 2,
  "total_order_value_usd": 10000.0,
  "decision_reason": "position_deviation_threshold_exceeded",
  "metadata": {}
}
```

#### 8. AtomicOperationGroupEvent
**File**: `events/atomic_groups.jsonl`
**Logged by**: ExecutionManager
**Frequency**: Every atomic group execution

```json
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
```

#### 9. ReconciliationEvent
**File**: `events/reconciliation.jsonl`
**Logged by**: PositionUpdateHandler
**Frequency**: Every reconciliation

```json
{
  "timestamp": "2025-01-15T10:30:00",
  "real_utc_time": "2025-01-15T10:30:00.123456",
  "correlation_id": "abc123",
  "pid": 12345,
  "reconciliation_type": "execution_deltas",
  "trigger_source": "execution_manager",
  "reconciliation_success": true,
  "expected_deltas_count": 2,
  "actual_deltas_count": 2,
  "reconciliation_duration_ms": 25.5,
  "metadata": {}
}
```

#### 10. ExecutionDeltaEvent
**File**: `events/execution_deltas.jsonl`
**Logged by**: PositionUpdateHandler
**Frequency**: Every execution delta application

```json
{
  "timestamp": "2025-01-15T10:30:00",
  "real_utc_time": "2025-01-15T10:30:00.123456",
  "correlation_id": "abc123",
  "pid": 12345,
  "delta_type": "execution_deltas",
  "trigger_source": "execution_manager",
  "deltas_applied": 2,
  "total_delta_value_usd": 10000.0,
  "metadata": {}
}
```

#### 11. HealthStatusEvent
**File**: `events/health_status.jsonl`
**Logged by**: HealthMonitor
**Frequency**: Every health check

```json
{
  "timestamp": "2025-01-15T10:30:00",
  "real_utc_time": "2025-01-15T10:30:00.123456",
  "correlation_id": "abc123",
  "pid": 12345,
  "overall_status": "healthy",
  "component_statuses": {
    "PositionMonitor": "healthy",
    "ExecutionManager": "healthy"
  },
  "health_score": 0.95,
  "metadata": {}
}
```

#### 12. SystemErrorEvent
**File**: `events/system_errors.jsonl`
**Logged by**: All components
**Frequency**: Every error occurrence

```json
{
  "timestamp": "2025-01-15T10:30:00",
  "real_utc_time": "2025-01-15T10:30:00.123456",
  "correlation_id": "abc123",
  "pid": 12345,
  "error_code": "EXEC-001",
  "error_message": "Order execution failed",
  "component": "ExecutionManager",
  "severity": "HIGH",
  "stack_trace": "Traceback (most recent call last)...",
  "metadata": {}
}
```

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

```python
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
```

### AtomicOperationGroupEvent
```json
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
```

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
```python
# In domain event
timestamp=timestamp.isoformat(),        # Engine timestamp
real_utc_time=datetime.utcnow().isoformat()  # Actual UTC time
```

## Debugging Workflows

### Find Failed Operations
```bash
# Find all failed operations
jq 'select(.status == "failed")' logs/{correlation_id}/{pid}/events/operation_executions.jsonl

# Count failures by operation type
jq -r '.operation_type' logs/{correlation_id}/{pid}/events/operation_executions.jsonl | sort | uniq -c
```

### Trace Single Operation
```bash
# Get all events for operation_id
grep "supply_001" logs/{correlation_id}/{pid}/events/*.jsonl
```

### Position History
```bash
# Get position history for specific position_key
jq '.positions["aave:aToken:aUSDT"]' logs/{correlation_id}/{pid}/events/positions.jsonl
```

### Reconciliation Issues
```bash
# Find reconciliation failures
jq 'select(.reconciliation_success == false)' logs/{correlation_id}/{pid}/events/tight_loop.jsonl
```

## Log Querying Examples

### Using jq
```bash
# Get all positions at specific timestamp
jq 'select(.timestamp == "2025-01-15T10:30:00")' events/positions.jsonl

# Calculate total USD value over time
jq -r '[.timestamp, .total_value_usd] | @csv' events/positions.jsonl

# Find operations with high execution time
jq 'select(.execution_duration_ms > 1000)' events/operation_executions.jsonl
```

### Using grep
```bash
# Find all supply operations
grep '"operation_type":"supply"' events/operation_executions.jsonl

# Find all CRITICAL errors
grep '"severity":"CRITICAL"' *.log

# Find specific correlation_id
grep "abc123" events/*.jsonl
```

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
```python
# Export positions to CSV
df = pd.read_json("events/positions.jsonl", lines=True)
df.to_csv("results/{backtest_id}/positions.csv", index=False)
```

## Reference Documentation

- **Domain Event Models**: `backend/src/basis_strategy_v1/core/models/domain_events.py`
- **Structured Logger**: `backend/src/basis_strategy_v1/infrastructure/logging/structured_logger.py`
- **Domain Event Logger**: `backend/src/basis_strategy_v1/infrastructure/logging/domain_event_logger.py`
- **Log Directory Manager**: `backend/src/basis_strategy_v1/infrastructure/logging/log_directory_manager.py`
- **Error Code Registry**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`
