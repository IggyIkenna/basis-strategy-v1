# Tight Loop Architecture

**Purpose**: Comprehensive documentation of the tight loop architecture and ownership model  
**Status**: ✅ CANONICAL REFERENCE - Authoritative source for tight loop implementation  
**Last Updated**: October 15, 2025

**Scope**: This document provides **implementation-level details** for the tight loop pattern. For system-wide workflow context, see [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md). For configuration details, see [VENUE_EXECUTION_CONFIG_GUIDE.md](VENUE_EXECUTION_CONFIG_GUIDE.md).

**When to use this document**:
- ✅ Implementing ExecutionManager orchestration logic
- ✅ Implementing PositionUpdateHandler reconciliation logic
- ✅ Understanding retry logic and system failure handling
- ✅ Writing tests for tight loop components
- ✅ Debugging tight loop execution issues
- ✅ Performance tuning and optimization

**When to use other documents**:
- **System overview** → [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)
- **Configuration** → [VENUE_EXECUTION_CONFIG_GUIDE.md](VENUE_EXECUTION_CONFIG_GUIDE.md)
- **Architectural principles** → [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md)

---

## Overview

The tight loop is the **Order → Execution → Reconciliation** cycle that ensures every order is fully executed and reconciled before proceeding to the next order. This architecture provides atomic order processing with guaranteed consistency between expected and actual positions.

**Critical Design Decision**: The tight loop has a dual ownership model:
- **ExecutionManager** orchestrates the cycle (coordinates Order → Execution → Reconciliation)
- **PositionUpdateHandler** owns the reconciliation logic (performs actual position reconciliation)

## Canonical Sources

**This architecture aligns with canonical architectural principles**:
- **Instrument Definitions**: [INSTRUMENT_DEFINITIONS.md](INSTRUMENT_DEFINITIONS.md) - Canonical position key format (`venue:position_type:symbol`)
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Workflow Architecture**: [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Complete workflow documentation
- **Mode-Specific Behavior**: [MODE_SPECIFIC_BEHAVIOR_GUIDE.md](MODE_SPECIFIC_BEHAVIOR_GUIDE.md) - Mode differences
- **Error Handling**: [ERROR_HANDLING_PATTERNS.md](ERROR_HANDLING_PATTERNS.md) - Error and retry patterns

---

## Tight Loop Definition

### Core Concept

The tight loop ensures that:
1. Each order is executed completely before moving to the next
2. Position reconciliation occurs after every execution
3. The system maintains consistency between simulated and real positions
4. Failures trigger immediate retry or system failure

### Visual Flow

```
Order 1 → Execute → ExecutionHandshake → execution_deltas → Reconcile → ✓ Success
                                                          → ✗ Retry (3x with backoff)
                                                          → ✗ System Failure (after 2min)

Order 2 → Execute → ExecutionHandshake → execution_deltas → Reconcile → ✓ Success
...
Order N → Execute → ExecutionHandshake → execution_deltas → Reconcile → ✓ Success
```

### Why Tight Loop is Critical

**Without tight loop**:
- Orders execute in parallel
- Race conditions between executions
- Inconsistent position state
- Failed reconciliation after batch completion

**With tight loop**:
- Sequential order processing
- No race conditions
- Consistent position state at each step
- Immediate feedback on failures

---

## Ownership Model

### ExecutionManager: Orchestration

**Responsibilities**:
1. Receive orders from Strategy Manager
2. Route each order to VenueInterfaceManager
3. Wait for execution completion (ExecutionHandshake object)
4. Convert ExecutionHandshake.position_deltas to execution_deltas format
5. Call PositionUpdateHandler for reconciliation
6. Implement retry logic with exponential backoff
7. Trigger system failure on timeout
8. Return ExecutionHandshake results to EventDrivenStrategyEngine

**Does NOT**:
- Perform reconciliation logic (PositionUpdateHandler's job)
- Update position state directly (PositionMonitor's job)
- Make venue API calls (VenueInterfaceManager's job)

### PositionUpdateHandler: Reconciliation Owner

**Responsibilities**:
1. Receive reconciliation request from ExecutionManager
2. Update PositionMonitor with execution deltas
3. Query real positions from venues (mode-specific)
4. Compare simulated vs real positions
5. Return reconciliation result with success/failure
6. Trigger downstream component chain (Exposure, Risk, PnL)

**Does NOT**:
- Route orders (ExecutionManager's job)
- Retry reconciliation (ExecutionManager's job)
- Trigger system failures (ExecutionManager's job)

### Clear Separation of Concerns

| Responsibility | Owner |
|----------------|-------|
| Order orchestration | ExecutionManager |
| Order routing | VenueInterfaceManager |
| Order execution | Execution Interfaces |
| Position updates | PositionMonitor |
| Reconciliation logic | PositionUpdateHandler |
| Retry logic | ExecutionManager |
| System failure triggers | ExecutionManager |
| Downstream chain | PositionUpdateHandler |

---

## Reconciliation vs Position Refresh

### Critical Distinction

The position update system uses **2 public triggers** with different purposes:

#### `execution_manager` Trigger - Tight Loop Reconciliation

**Purpose**: Validate execution consistency within the tight loop

**When**: Called immediately after each order execution (inside tight loop)

**What it does**:
1. Apply execution deltas to simulated positions
2. Query real positions from venues
3. **Compare simulated vs real** (reconciliation validation)
4. Trigger retry logic if mismatch found
5. Propagate to downstream components (Exposure, Risk, PnL)

**Backtest mode**: Simulated = Real (always consistent, no retries)  
**Live mode**: Compares simulated vs real (may retry on mismatch)

**Key Point**: This is **reconciliation** - validating that execution matched expectations

#### `position_refresh` Trigger - Position Discovery

**Purpose**: Update position state outside of order execution

**When**: 
- Backtest: Called every timestep by EventDrivenStrategyEngine
- Live: Called every 60 seconds by EventDrivenStrategyEngine

**What it does**:
1. Query current positions from venues
2. Apply automatic settlements (backtest only: funding, rewards, etc.)
3. Update position state for strategy decision-making
4. **NO reconciliation validation** (no comparison, no retries)

**Key Point**: This is **discovery** - refreshing position state for strategy decisions, not validating execution

### Summary Table

| Aspect | `execution_manager` (Tight Loop) | `position_refresh` (Discovery) |
|--------|------------------------------|-------------------------------|
| **Purpose** | Validate execution consistency | Refresh position state |
| **When** | After each order execution | Every timestep (backtest) / 60s (live) |
| **Reconciliation** | ✅ Yes - Compare simulated vs real | ❌ No - Just query current state |
| **Retry logic** | ✅ Yes - Up to 3 attempts with backoff | ❌ No retries |
| **Failure handling** | Triggers system failure after timeout | No failure handling |
| **Component chain** | Triggers Exposure → Risk → PnL | Triggers Exposure → Risk → Strategy |

**Reference**: [specs/01_POSITION_MONITOR.md](specs/01_POSITION_MONITOR.md) for complete Position Monitor specification.

---

## Position Monitor's Role in Tight Loop

### Unified Delta Application

The Position Monitor plays a critical role in the tight loop by applying execution deltas using a unified format. This ensures consistency regardless of delta source (trades, transfers, or settlements).

#### Execution Delta Flow

```
ExecutionManager.process_orders(timestamp, orders)
  ↓
  Route to VenueInterfaceManager → Execute order
  ↓
  Execution result returned in format:
  {
    'success': True,
    'executed_orders': [
      {
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'quantity': 0.5,
        'price': 50000,
        'venue': 'binance',
        'fees': 25
      }
    ]
  }
  ↓
  PositionUpdateHandler.update_state(timestamp, 'execution_manager', execution_result)
  ↓
  PositionMonitor.update_state(timestamp, 'execution_manager', execution_result)
  ↓
  _apply_execution_deltas(execution_result)
    ↓
    Convert to normalized delta format:
    [
      {
        "position_key": "binance:BaseToken:BTC",
        "delta_amount": 0.5,
        "source": "trade",
        "price": 50000,
        "fee": 25
      },
      {
        "position_key": "binance:BaseToken:USDT",
        "delta_amount": -25025,  # -(0.5 * 50000 + 25)
        "source": "trade"
      }
    ]
  ↓
  _apply_position_deltas(timestamp, normalized_deltas)
    ↓
    For each delta:
      - Validate position_key in position_subscriptions
      - Update simulated_positions[position_key] += delta_amount
      - Log delta application
  ↓
  _query_venue_balances(timestamp)
    ↓
    Backtest: real_positions = simulated_positions.copy()
    Live: Query actual positions from venue interfaces
  ↓
  Return real_positions to PositionUpdateHandler
  ↓
  PositionUpdateHandler performs reconciliation (compare simulated vs real)
  ↓
  Return reconciliation_result to ExecutionManager
```

#### Unified Delta Format

All position updates flow through the same delta structure:

```python
{
    "position_key": str,        # "venue:position_type:symbol"
    "delta_amount": float,      # Change in position (+/-)
    "source": str,              # "trade"|"transfer"|"funding"|"reward"|"initial"
    "price": Optional[float],   # Execution price if applicable
    "fee": Optional[float],     # Transaction fee if applicable
    "metadata": Optional[Dict]  # Additional context
}
```

**Benefits**:
1. **Consistency**: All deltas processed identically
2. **Testability**: Single code path to test
3. **Debuggability**: Uniform logging format
4. **Extensibility**: Easy to add new delta sources

#### Position Update in Tight Loop

```python
def _apply_execution_deltas(self, timestamp: pd.Timestamp, execution_result: Dict) -> None:
    """
    Convert execution results from ExecutionManager into normalized deltas.
    Called during tight loop after each order execution.
    """
    # Parse execution result
    executed_orders = execution_result.get('executed_orders', [])
    
    # Convert to normalized deltas
    normalized_deltas = []
    for order in executed_orders:
        venue = order['venue']
        symbol = order['symbol']
        side = order['side']
        quantity = order['quantity']
        price = order['price']
        fees = order.get('fees', 0)
        
        # Extract base and quote assets from symbol (e.g., BTCUSDT → BTC, USDT)
        base_asset, quote_asset = self._parse_symbol(symbol)
        
        # Create delta for base asset
        base_delta = {
            "position_key": f"{venue}:BaseToken:{base_asset}",
            "delta_amount": quantity if side == 'buy' else -quantity,
            "source": "trade",
            "price": price,
            "fee": fees
        }
        
        # Create delta for quote asset (cost of trade + fees)
        quote_cost = quantity * price
        quote_delta = {
            "position_key": f"{venue}:BaseToken:{quote_asset}",
            "delta_amount": -(quote_cost + fees) if side == 'buy' else (quote_cost - fees),
            "source": "trade"
        }
        
        normalized_deltas.extend([base_delta, quote_delta])
    
    # Apply all deltas via unified applier
    self._apply_position_deltas(timestamp, normalized_deltas)
```

#### Critical Ordering in Tight Loop

**MUST follow this exact sequence**:

1. **Apply execution deltas** to simulated_positions
2. **Apply automatic settlements** (backtest only, if due at this timestamp)
3. **Copy simulated to real** (backtest) OR **Query real positions** (live)
4. **Return positions** for reconciliation

```python
# ✅ CORRECT ORDER (Backtest)
def _query_venue_balances(self, timestamp):
    # 1. Apply automatic settlements if due
    automatic_deltas = []
    if self._should_apply_funding(timestamp):
        automatic_deltas.extend(self._generate_funding_settlement_deltas(timestamp))
    # ... other settlements
    
    if automatic_deltas:
        self._apply_position_deltas(timestamp, automatic_deltas)
    
    # 2. CRITICAL: Copy AFTER all deltas applied
    self.real_positions = self.simulated_positions.copy()
```

**Why order matters**:
- Deltas update `simulated_positions`
- Backtest requires `real_positions` to match `simulated_positions` exactly
- Copying before applying deltas → stale `real_positions` → failed reconciliation
- Copying after applying deltas → synchronized positions → successful reconciliation

---

## ExecutionManager Orchestration

### Complete Implementation

```python
def process_orders(self, timestamp, orders):
    """
    Orchestrate tight loop: process orders sequentially with full reconciliation.
    """
    results = []
    
    for i, order in enumerate(orders):
        try:
            # 1. Route order to appropriate execution interface
            execution_result = self.venue_interface_manager.route_to_venue(order)
            
            # 2. Check execution success
            if not execution_result.get('success'):
                self._handle_order_failure(order, execution_result, i)
                continue
            
            # 3. Reconcile execution result (TIGHT LOOP)
            reconciliation_result = self.position_update_handler.update_state(
                timestamp=timestamp,
                trigger_source='execution_manager',
                execution_deltas=execution_result
            )
            
            # 4. Check reconciliation success
            if not reconciliation_result.get('success'):
                # Retry reconciliation up to 3 times
                reconciliation_success = self._reconcile_with_retry(
                    timestamp, execution_result, i
                )
                
                if not reconciliation_success:
                    self._trigger_system_failure(f"Reconciliation failed for order {i}")
                    return []
            
            # 5. Order successfully processed and reconciled
            results.append({
                'order': order,
                'execution_result': execution_result,
                'reconciliation_result': reconciliation_result,
                'success': True
            })
            
        except Exception as e:
            self._handle_error(e, f"process_order_{i}")
            self._trigger_system_failure(f"Order processing failed: {e}")
            return []
    
    return results
```

### Key Implementation Points

1. **Sequential Processing**: Loop through orders one at a time
2. **Synchronous Execution**: Wait for each execution to complete
3. **Immediate Reconciliation**: Reconcile after each execution
4. **Fail-Fast**: Stop processing on critical failures
5. **Complete Results**: Return all successful order results

---

## Retry Logic with Exponential Backoff

### Implementation

```python
def _reconcile_with_retry(self, timestamp, execution_result, order_number):
    """
    Retry reconciliation up to 3 times with exponential backoff.
    """
    max_retries = 3
    start_time = time.time()
    
    for attempt in range(max_retries):
        try:
            reconciliation_result = self.position_update_handler.update_state(
                timestamp=timestamp,
                trigger_source='execution_manager',
                execution_deltas=execution_result
            )
            
            if reconciliation_result.get('success'):
                return True
            
            # Wait before retry (exponential backoff)
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(wait_time)
            
        except Exception as e:
            logger.error(f"Reconciliation attempt {attempt + 1} failed: {e}")
    
    # Check if we've exceeded 2-minute timeout
    if time.time() - start_time > 120:  # 2 minutes
        self._trigger_system_failure(f"Reconciliation timeout for order {order_number}")
    
    return False
```

### Retry Schedule

| Attempt | Wait Time | Cumulative |
|---------|-----------|------------|
| 1       | 0s (immediate) | 0s |
| 2       | 1s | 1s |
| 3       | 2s | 3s |
| 4       | 4s | 7s |

**Maximum retry time**: 7 seconds + execution time  
**Timeout trigger**: After 2 minutes total

---

## System Failure Handling

### Failure Trigger Implementation

```python
def _trigger_system_failure(self, failure_reason):
    """
    Trigger system failure and restart via health/error systems.
    """
    # Update health status to critical
    self.health_status = "critical"
    
    # Log critical error
    logger.critical(f"SYSTEM FAILURE: {failure_reason}")
    
    # Raise SystemExit to trigger deployment restart
    raise SystemExit(f"System failure: {failure_reason}")
```

### When to Trigger System Failure

1. **Reconciliation timeout**: Reconciliation fails for >2 minutes
2. **Order processing exception**: Unhandled exception during order processing
3. **Multiple retry failures**: All retry attempts exhausted
4. **Critical component failure**: Component reports critical health status

### System Restart Workflow

```
1. ExecutionManager triggers SystemExit
2. Deployment system catches SystemExit
3. Health checker marks instance as unhealthy
4. Deployment system spawns new instance
5. New instance initializes from last known good state
6. Processing resumes
```

---

## Sequential Order Processing

### Why Sequential?

**Advantages**:
- No race conditions between orders
- Deterministic execution order
- Clear state at each step
- Easy to reason about failures
- Simplified testing and debugging

**Disadvantages**:
- Slower than parallel execution
- Higher latency for batch orders

**Decision**: Sequential processing chosen for correctness and simplicity. Performance is acceptable for typical order volumes.

### Order Processing State Machine

```
[IDLE] → [ROUTING] → [EXECUTING] → [RECONCILING] → [SUCCESS|FAILURE]
                                                    ↓
                                                [RETRY] → [RECONCILING]
                                                    ↓
                                            [SYSTEM_FAILURE]
```

### State Transitions

| From State | Event | To State |
|-----------|-------|----------|
| IDLE | Receive orders | ROUTING |
| ROUTING | Route complete | EXECUTING |
| EXECUTING | Execution success | RECONCILING |
| EXECUTING | Execution failure | FAILURE |
| RECONCILING | Reconciliation success | SUCCESS |
| RECONCILING | Reconciliation failure | RETRY |
| RETRY | Max retries reached | SYSTEM_FAILURE |
| RETRY | Retry success | SUCCESS |

---

## Integration with Component Chain

### Downstream Component Chain

After successful reconciliation, PositionUpdateHandler triggers:

```python
# In PositionUpdateHandler.update_state()

# 1. Update position
self.position_monitor.update_state(timestamp, 'execution_manager', execution_deltas)

# 2. Recalculate exposure
updated_exposure = self.exposure_monitor.calculate_exposure(
    timestamp=timestamp,
    position_snapshot=position_snapshot,
    market_data=market_data
)

# 3. Reassess risk
updated_risk = self.risk_monitor.assess_risk(
    exposure_data=updated_exposure,
    market_data=market_data
)

# 4. Recalculate P&L
updated_pnl = self.pnl_monitor.calculate_pnl(
    current_exposure=updated_exposure,
    timestamp=timestamp
)
```

### Chain Execution Characteristics

- **Synchronous**: Each component called sequentially
- **Atomic**: Either all succeed or none
- **Consistent**: Position → Exposure → Risk → PnL always in order
- **Fail-Fast**: Stop chain on any component failure

---

## Atomic Transaction Handling

### Special Case: Blockchain Transactions

For atomic blockchain transactions (e.g., stake → supply → borrow):

```python
def process_atomic_transaction(self, timestamp, transaction_blocks):
    """
    Process atomic blockchain transaction as single tight loop.
    """
    # Execute all blocks atomically
    atomic_result = self._execute_atomic_blocks(transaction_blocks)
    
    if not atomic_result.get('success'):
        # All-or-nothing: rollback entire transaction
        self._rollback_atomic_transaction(transaction_blocks)
        return False
    
    # Single reconciliation for entire atomic transaction
    reconciliation_result = self.position_update_handler.update_state(
        timestamp=timestamp,
        trigger_source='execution_manager',
        execution_deltas=atomic_result
    )
    
    return reconciliation_result.get('success')
```

**Key Point**: Atomic transactions are treated as single order for reconciliation purposes.

---

## Performance Considerations

### Expected Latencies

| Operation | Backtest Mode | Live Mode |
|-----------|---------------|-----------|
| Order routing | <1ms | <1ms |
| Order execution | <1ms | 100-500ms |
| Position reconciliation | <10ms | 50-200ms |
| Total per order | <20ms | 200-800ms |

### Throughput Analysis

**Typical Scenario** (5 orders):
- Sequential processing: 5 × 500ms = 2.5 seconds
- With retry (1 failure): 2.5s + 7s = 9.5 seconds
- With timeout: Maximum 2 minutes

**Acceptable Performance**: System typically processes <10 orders per timestep, so sequential processing is performant.

---

## Mode-Specific Behavior

### Backtest Mode

```python
if self.execution_mode == 'backtest':
    # No retries - fail fast for immediate feedback
    reconciliation_result = self.position_update_handler.update_state(
        timestamp=timestamp,
        trigger_source='execution_manager',
        execution_deltas=execution_result
    )
    
    if not reconciliation_result.get('success'):
        # Backtest should never fail reconciliation
        raise BacktestError("Reconciliation failed in backtest mode")
```

**Characteristics**:
- No retries (fail-fast)
- Reconciliation always succeeds (simulated = real)
- Immediate error feedback
- Fast execution (<20ms per order)

### Live Mode

```python
if self.execution_mode == 'live':
    # Retry with exponential backoff
    reconciliation_result = self.position_update_handler.update_state(
        timestamp=timestamp,
        trigger_source='execution_manager',
        execution_deltas=execution_result
    )
    
    if not reconciliation_result.get('success'):
        # Retry up to 3 times
        success = self._reconcile_with_retry(timestamp, execution_result, order_num)
        if not success:
            self._trigger_system_failure("Reconciliation failed")
```

**Characteristics**:
- Retry with exponential backoff
- 2-minute timeout
- Actual venue reconciliation
- System failure on persistent failures

---

## Testing the Tight Loop

### Unit Tests

```python
def test_sequential_order_processing():
    """Test that orders are processed one at a time."""
    orders = [order1, order2, order3]
    results = execution_manager.process_orders(timestamp, orders)
    
    # Verify sequential execution
    assert len(execution_log) == 3
    assert execution_log[0].timestamp < execution_log[1].timestamp
    assert execution_log[1].timestamp < execution_log[2].timestamp

def test_reconciliation_failure_retry():
    """Test retry logic on reconciliation failure."""
    # Simulate reconciliation failure
    mock_handler.update_state.side_effect = [
        {'success': False},  # Attempt 1
        {'success': False},  # Attempt 2
        {'success': True}    # Attempt 3
    ]
    
    results = execution_manager.process_orders(timestamp, [order])
    
    # Verify 3 attempts made
    assert mock_handler.update_state.call_count == 3

def test_system_failure_on_timeout():
    """Test system failure triggered after timeout."""
    # Simulate persistent failure
    mock_handler.update_state.return_value = {'success': False}
    
    with pytest.raises(SystemExit):
        execution_manager.process_orders(timestamp, [order])
```

### Integration Tests

```python
def test_end_to_end_tight_loop():
    """Test complete tight loop from order to reconciliation."""
    order = create_test_order()
    
    results = execution_manager.process_orders(timestamp, [order])
    
    # Verify complete flow
    assert results[0]['success'] == True
    assert 'execution_result' in results[0]
    assert 'reconciliation_result' in results[0]
    
    # Verify position updated
    position = position_monitor.get_current_positions()
    assert position['USDT']['amount'] == expected_amount
```

---

## Related Documentation

### Component Specifications
- **Venue Manager**: [specs/06_VENUE_MANAGER.md](specs/06_VENUE_MANAGER.md) - Complete ExecutionManager spec
- **Position Update Handler**: [specs/11_POSITION_UPDATE_HANDLER.md](specs/11_POSITION_UPDATE_HANDLER.md) - Complete PositionUpdateHandler spec
- **Venue Interface Manager**: [specs/07_VENUE_INTERFACE_MANAGER.md](specs/07_VENUE_INTERFACE_MANAGER.md) - Order routing

### Architecture Documentation
- **Workflow Guide**: [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Complete workflow patterns
- **Mode-Specific Behavior**: [MODE_SPECIFIC_BEHAVIOR_GUIDE.md](MODE_SPECIFIC_BEHAVIOR_GUIDE.md) - Mode differences
- **Error Handling**: [ERROR_HANDLING_PATTERNS.md](ERROR_HANDLING_PATTERNS.md) - Error and retry patterns
- **Reference Architecture**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Core principles

---

**Status**: Complete technical reference for tight loop architecture  
**Last Reviewed**: October 15, 2025  
**Reviewer**: Documentation Refactor Implementation


