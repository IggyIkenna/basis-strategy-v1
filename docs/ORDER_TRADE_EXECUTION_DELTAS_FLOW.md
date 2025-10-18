# Order → ExecutionHandshake → execution_deltas Flow

**Purpose**: Comprehensive documentation of the Order → ExecutionHandshake → execution_deltas data flow
**Status**: ✅ CANONICAL REFERENCE - Authoritative source for execution flow
**Last Updated**: January 27, 2025

## Overview

This document describes the complete data flow from Order creation through ExecutionHandshake execution to execution_deltas for position updates. This flow ensures proper type safety and data consistency throughout the execution pipeline.

## Data Flow Architecture

### 1. Order Creation (Strategy Manager)
```python
# Strategy Manager creates Order objects
order = Order(
    venue='binance',
    operation=OrderOperation.SPOT_TRADE,
    pair='BTC/USDT',
    side='BUY',
    amount=0.5,
    order_type='market'
)
```

### 2. Order Routing (VenueInterfaceManager)
```python
# VenueInterfaceManager routes Order to appropriate venue interface
def route_to_venue(self, timestamp: pd.Timestamp, order: Order) -> ExecutionHandshake:
    # Route based on order.operation
    if order.operation.value == 'spot_trade':
        return self._route_to_cex(timestamp, order)
    elif order.operation.value == 'supply':
        return self._route_to_onchain(timestamp, order)
    # ... etc
```

### 3. ExecutionHandshake Execution (Venue Interfaces)
```python
# Venue interfaces execute orders and return ExecutionHandshake objects
def execute_spot_trade(self, order: Order, timestamp: pd.Timestamp) -> ExecutionHandshake:
    # Execute the trade
    # ...
    return ExecutionHandshake(
        order=order,
        status=ExecutionHandshakeStatus.EXECUTED,
        executed_amount=0.5,
        executed_price=45000.0,
        position_deltas={'BTC': 0.5, 'USDT': -22500.0},
        fee_amount=22.5,
        fee_currency='USDT'
    )
```

### 4. execution_deltas Conversion (ExecutionManager)
```python
# ExecutionManager converts ExecutionHandshake to execution_deltas for PositionUpdateHandler
def _convert_trade_to_execution_deltas(self, trade: ExecutionHandshake) -> List[Dict]:
    execution_deltas = []
    
    # Convert ExecutionHandshake.position_deltas to execution_deltas format
    for asset, delta_amount in trade.position_deltas.items():
        position_key = f"{trade.order.venue}:token:{asset}"
        execution_delta = {
            "position_key": position_key,
            "delta_amount": delta_amount,
            "source": "trade",
            "price": trade.executed_price,
            "fee": trade.fee_amount if trade.fee_currency == asset else 0.0
        }
        execution_deltas.append(execution_delta)
    
    return execution_deltas
```

### 5. Position Reconciliation (PositionUpdateHandler)
```python
# PositionUpdateHandler receives execution_deltas and updates positions
def update_state(self, timestamp: pd.Timestamp, trigger_source: str, execution_deltas: List[Dict]):
    # Apply execution_deltas to PositionMonitor
    self.position_monitor.update_state(timestamp, trigger_source, execution_deltas)
    # ... reconciliation logic
```

## Data Structure Definitions

### Order Class
```python
class Order(BaseModel):
    venue: str
    operation: OrderOperation
    pair: Optional[str] = None
    side: Optional[Literal["BUY", "SELL", "LONG", "SHORT"]] = None
    amount: float
    price: Optional[float] = None
    order_type: Literal["market", "limit"] = "market"
    # ... other fields
```

### ExecutionHandshake Class
```python
class ExecutionHandshake(BaseModel):
    order: Order
    status: ExecutionHandshakeStatus
    trade_id: Optional[str] = None
    executed_amount: float = 0.0
    executed_price: Optional[float] = None
    position_deltas: Dict[str, float] = Field(default_factory=dict)
    fee_amount: float = 0.0
    fee_currency: str = "USDT"
    # ... other fields
```

### execution_deltas Format
```python
execution_deltas: List[Dict] = [
    {
        "position_key": "binance:BaseToken:BTC",
        "delta_amount": 0.5,
        "source": "trade",
        "price": 45000.0,
        "fee": 0.0
    },
    {
        "position_key": "binance:BaseToken:USDT", 
        "delta_amount": -22500.0,
        "source": "trade",
        "price": 45000.0,
        "fee": 22.5
    }
]
```

## Component Responsibilities

### ExecutionManager
- **Receives**: `List[Order]` from Strategy Manager
- **Processes**: Each Order sequentially through tight loop
- **Converts**: `ExecutionHandshake.position_deltas` → `execution_deltas`
- **Returns**: `List[ExecutionHandshake]` to EventDrivenStrategyEngine

### VenueInterfaceManager
- **Receives**: `Order` from ExecutionManager
- **Routes**: Order to appropriate venue interface
- **Returns**: `ExecutionHandshake` object (successful or failed)

### Venue Interfaces
- **Receives**: `Order` from VenueInterfaceManager
- **Executes**: Order on venue (CEX/DeFi/Wallet)
- **Returns**: `ExecutionHandshake` object with execution results

### PositionUpdateHandler
- **Receives**: `execution_deltas` from ExecutionManager
- **Applies**: Deltas to PositionMonitor
- **Reconciles**: Simulated vs real positions

## Error Handling

### Order Execution Failures
```python
# VenueInterfaceManager returns failed ExecutionHandshake instead of raising
return ExecutionHandshake(
    order=order,
    status='failed',
    error_code='VIM-001',
    error_message=str(e)
)
```

### Reconciliation Failures
```python
# ExecutionManager retries reconciliation with exponential backoff
reconciliation_success = self._reconcile_with_retry(timestamp, execution_deltas, i)
if not reconciliation_success:
    self._trigger_system_failure(f"Reconciliation failed for order {i}")
```

## Type Safety Benefits

1. **Order Objects**: Strongly typed order specifications prevent invalid orders
2. **ExecutionHandshake Objects**: Structured execution results with proper error handling
3. **execution_deltas**: Standardized format for position updates
4. **Method Signatures**: Clear contracts between components

## Integration Points

### Called BY
- EventDrivenStrategyEngine: `execution_manager.process_orders(timestamp, orders)`

### Calls TO
- VenueInterfaceManager: `route_to_venue(timestamp, order)`
- PositionUpdateHandler: `update_state(timestamp, 'execution_manager', execution_deltas)`

### Data Flow
```
Strategy Manager → List[Order] → ExecutionManager → VenueInterfaceManager → Venue Interfaces → ExecutionHandshake → execution_deltas → PositionUpdateHandler → PositionMonitor
```

## Testing Considerations

1. **Unit Tests**: Test each component with proper Order/ExecutionHandshake objects
2. **Integration Tests**: Test complete Order → ExecutionHandshake → execution_deltas flow
3. **Error Tests**: Test failure scenarios and error propagation
4. **Type Tests**: Ensure proper type safety throughout the flow

## Related Documentation

- [TIGHT_LOOP_ARCHITECTURE.md](TIGHT_LOOP_ARCHITECTURE.md) - Tight loop orchestration
- [06_VENUE_MANAGER.md](specs/06_VENUE_MANAGER.md) - ExecutionManager specification
- [07_VENUE_INTERFACE_MANAGER.md](specs/07_VENUE_INTERFACE_MANAGER.md) - VenueInterfaceManager specification
- [07A_VENUE_INTERFACES.md](specs/07A_VENUE_INTERFACES.md) - Venue interfaces specification
