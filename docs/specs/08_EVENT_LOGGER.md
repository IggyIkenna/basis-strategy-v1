# Event Logger Component Specification

## Purpose
Detailed audit-grade event tracking with balance snapshots for debugging and audit trails.

## Responsibilities
1. Log all component state changes with timestamps
2. Maintain global event ordering across all components
3. Provide event history for debugging
4. MODE-AWARE: Same logging logic for both backtest and live modes

## State
- events: List[Dict] (event history)
- global_order: int (auto-increment for every event)
- _order_lock: asyncio.Lock (thread-safe order assignment)
- last_log_timestamp: pd.Timestamp

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- config: Dict (reference, never modified)
- execution_mode: str (BASIS_EXECUTION_MODE)

These references are stored in __init__ and used throughout component lifecycle.
Components NEVER receive these as method parameters during runtime.

## Environment Variables

### System-Level Variables (Read at Initialization)
- `BASIS_EXECUTION_MODE`: backtest | live
  - **Usage**: Determines simulated vs real API behavior
  - **Read at**: Component __init__
  - **Affects**: Mode-aware conditional logic

- `BASIS_ENVIRONMENT`: dev | staging | production
  - **Usage**: Credential routing for venue APIs
  - **Read at**: Component __init__ (if uses external APIs)
  - **Affects**: Which API keys/endpoints to use

- `BASIS_DEPLOYMENT_MODE`: local | docker
  - **Usage**: Port/host configuration
  - **Read at**: Component __init__ (if network calls)
  - **Affects**: Connection strings

- `BASIS_DATA_MODE`: csv | db
  - **Usage**: Data source selection (DataProvider only)
  - **Read at**: DataProvider __init__
  - **Affects**: File-based vs database data loading

### Component-Specific Variables
None

### Environment Variable Access Pattern
```python
def __init__(self, ...):
    # Read env vars ONCE at initialization
    self.execution_mode = os.getenv('BASIS_EXECUTION_MODE', 'backtest')
    # NEVER read env vars during runtime loops
```

### Behavior NOT Determinable from Environment Variables
- Event logging format (hard-coded structure)
- Event ordering logic (hard-coded algorithms)
- Event retention policy (hard-coded limits)

## Config Fields Used

### Universal Config (All Components)
- `strategy_mode`: str - e.g., 'eth_basis', 'pure_lending'
- `share_class`: str - 'usdt_stable' | 'eth_directional'
- `initial_capital`: float - Starting capital

### Component-Specific Config
- `event_buffer_size`: int - Maximum events to keep in memory
  - **Usage**: Determines memory usage for event buffering
  - **Default**: 10000
  - **Validation**: Must be > 0 and < 100000

- `event_export_format`: str - Format for event export
  - **Usage**: Determines export format (csv, json, both)
  - **Default**: 'both'
  - **Validation**: Must be 'csv', 'json', or 'both'

### Config Access Pattern
```python
def log_event(self, timestamp: pd.Timestamp, event_type: str, component: str, data: Dict):
    # Read config fields (NEVER modify)
    buffer_size = self.config.get('event_buffer_size', 10000)
    export_format = self.config.get('event_export_format', 'both')
```

### Behavior NOT Determinable from Config
- Event logging format (hard-coded structure)
- Event ordering logic (hard-coded algorithms)
- Async I/O patterns (hard-coded implementation)

## Data Provider Queries

### Data Types Requested
N/A - EventLogger does not query DataProvider

### Query Pattern
N/A - EventLogger does not query DataProvider

### Data NOT Available from DataProvider
All data - EventLogger does not use DataProvider

## Core Methods

### log_event(timestamp: pd.Timestamp, event_type: str, component: str, data: Dict)
Log an event with global ordering.

Parameters:
- timestamp: Current loop timestamp
- event_type: Type of event (position_update, exposure_calculation, etc.)
- component: Component that generated the event
- data: Event-specific data

### get_events(timestamp: pd.Timestamp = None) -> List[Dict]
Get event history.

Parameters:
- timestamp: Optional timestamp filter

Returns:
- List[Dict]: Event history

## Async I/O Pattern

**Exception to ADR-006: Synchronous Component Execution**

The Event Logger uses `async def` methods as an accepted exception to the synchronous component execution principle:

**Rationale**:
- File/DB writes are I/O operations that shouldn't block trading operations
- Async I/O provides performance benefits without affecting critical path
- Sequential awaits guarantee ordering without race conditions

**Implementation**:
- All logging methods use `async def` with `await` calls
- Components await: `await self.event_logger.log_event(...)`
- AsyncIO's single-threaded event loop prevents race conditions
- No dropped data or out-of-order writes

**Ordering Guarantees**:
- Sequential awaits ensure events are logged in correct order
- Global order counter maintains chronological sequence
- AsyncIO queue processing is FIFO by design

---

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) <!-- Link is valid --> - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

---

## 🎯 **Purpose**

Log all events with complete context for audit trail.

**Key Principles**:
- **Global order**: Every event gets unique sequence number
- **Balance snapshots**: Include position snapshot in every event (optional)
- **Atomic bundles**: Support wrapper + detail events (flash loans, leveraged staking)
- **Hourly timestamps**: All events on the hour in backtest
- **Future-proof**: Optional fields for live trading (tx_hash, confirmation, etc.)

**Matches**: `analyze_leveraged_restaking_USDT.py` event logging (audit-grade detail!)

---

## 📊 **Data Structures**

### **Event Structure**

```python
{
    # Timing
    'timestamp': pd.Timestamp,     # Trigger time (on the hour in backtest)
    'order': int,                  # Global sequence (1, 2, 3...)
    'status': str,                 # 'completed' (backtest), 'pending'/'confirmed' (live)
    
    # Event identification
    'event_type': str,             # 'GAS_FEE_PAID', 'STAKE_DEPOSIT', etc.
    'event_id': Optional[str],     # For live correlation (None in backtest)
    
    # Venue and asset
    'venue': str,                  # 'ETHEREUM', 'AAVE', 'ETHERFI', 'BINANCE', etc.
    'token': str,                  # 'ETH', 'USDT', 'weETH', etc.
    'amount': float,               # Primary amount
    
    # Balance snapshots (optional, for audit)
    'wallet_balance_after': Optional[Dict],      # Full Position Monitor output after event
    'cex_balance_after': Optional[Dict],         # CEX balances after event (subset of wallet_balance_after)
    'aave_position_after': Optional[Dict],       # AAVE derived positions (subset of wallet_balance_after)
    
    # Cost tracking
    'gas_cost_eth': Optional[float],
    'gas_cost_usd': Optional[float],
    'gas_units': Optional[int],
    'gas_price_gwei': Optional[float],
    'execution_cost_usd': Optional[float],
    'execution_cost_bps': Optional[float],
    
    # Transaction details
    'purpose': str,                               # Human-readable description
    'transaction_type': str,                      # Category
    'related_events': Optional[List[int]],        # Order numbers of related events
    'iteration': Optional[int],                   # For loops (1, 2, 3...)
    'parent_event': Optional[int],                # For atomic bundles
    
    # Live trading fields (None in backtest)
    'trigger_timestamp': Optional[pd.Timestamp],  # When decision made
    'completion_timestamp': Optional[pd.Timestamp], # When tx confirmed
    'tx_hash': Optional[str],
    'confirmation_blocks': Optional[int],
    
    # Additional context (mode-specific)
    **extra_data
}
```

---

## 💻 **Core Functions**

### **Initialization**

```python
class EventLogger:
    """Audit-grade event logging."""
    
    def __init__(self, execution_mode='backtest', include_balance_snapshots=True):
        self.execution_mode = execution_mode
        self.include_balance_snapshots = include_balance_snapshots
        self.events = []
        self.global_order = 0  # Auto-increment for every event
        self._order_lock = asyncio.Lock()  # Thread-safe order assignment
        
        # Using direct method calls for component communication
    
    async def log_event(
        self,
        timestamp: pd.Timestamp,
        event_type: str,
        venue: str,
        token: str = None,
        amount: float = None,
        position_snapshot: Optional[Dict] = None,
        **event_data
    ) -> int:
        """
        Log an event with automatic order assignment.
        
        Args:
            timestamp: Event time (on the hour in backtest)
            event_type: Type of event
            venue: Where it happened
            token: Token involved
            amount: Primary amount
            position_snapshot: Current position state (from Position Monitor)
            **event_data: Additional event-specific data
        
        Returns:
            Event order number (for correlation)
        """
        async with self._order_lock:
            self.global_order += 1
        
            event = {
                'timestamp': timestamp,
                'order': self.global_order,
                'event_type': event_type,
                'venue': venue,
                'token': token,
                'amount': amount,
                'status': 'completed' if self.execution_mode == 'backtest' else 'pending',
                **event_data
            }
        
            # Add balance snapshot if provided and enabled
            if self.include_balance_snapshots and position_snapshot:
                # Include full Position Monitor output for complete audit trail
                event['wallet_balance_after'] = position_snapshot  # Full Position Monitor output
                event['cex_balance_after'] = position_snapshot.get('cex_accounts')
                event['aave_position_after'] = {
                    'wallet': position_snapshot.get('wallet'),
                    'perp_positions': position_snapshot.get('perp_positions')
                }
                # Could add more derived data (AAVE positions, etc.)
            
            self.events.append(event)
            
            # Components use direct method calls
                    'timestamp': timestamp.isoformat()
                }))
            
            return self.global_order
```

### **Helper Methods** (Typed Event Logging)

```python
async def log_gas_fee(
    self,
    timestamp: pd.Timestamp,
    gas_cost_eth: float,
    gas_cost_usd: float,
    operation_type: str,
    gas_units: int,
    gas_price_gwei: float,
    position_snapshot: Optional[Dict] = None
) -> int:
    """Log gas fee payment."""
    return await self.log_event(
        timestamp=timestamp,
        event_type='GAS_FEE_PAID',
        venue='ETHEREUM',
        token='ETH',
        amount=gas_cost_eth,
        gas_cost_eth=gas_cost_eth,
        gas_cost_usd=gas_cost_usd,
        gas_units=gas_units,
        gas_price_gwei=gas_price_gwei,
        fee_type=operation_type,
        position_snapshot=position_snapshot
    )

async def log_stake(
    self,
    timestamp: pd.Timestamp,
    venue: str,  # 'ETHERFI' or 'LIDO'
    eth_in: float,
    lst_out: float,
    oracle_price: float,
    iteration: Optional[int] = None,
    position_snapshot: Optional[Dict] = None
) -> int:
    """Log staking operation."""
    return await self.log_event(
        timestamp=timestamp,
        event_type='STAKE_DEPOSIT',
        venue=venue,
        token='ETH',
        amount=eth_in,
        input_token='ETH',
        output_token='weETH' if venue == 'ETHERFI' else 'wstETH',
        amount_out=lst_out,
        oracle_price=oracle_price,
        iteration=iteration,
        position_snapshot=position_snapshot
    )

async def log_aave_supply(
    self,
    timestamp: pd.Timestamp,
    token: str,
    amount_supplied: float,
    atoken_received: float,
    liquidity_index: float,
    iteration: Optional[int] = None,
    position_snapshot: Optional[Dict] = None
) -> int:
    """
    Log AAVE collateral supply.
    
    CRITICAL: aToken amount depends on liquidity index!
    """
    return await self.log_event(
        timestamp=timestamp,
        event_type='COLLATERAL_SUPPLIED',
        venue='AAVE',
        token=token,
        amount=amount_supplied,
        atoken_received=atoken_received,
        liquidity_index=liquidity_index,
        conversion_note=f'{amount_supplied} {token} → {atoken_received} a{token} (index={liquidity_index})',
        iteration=iteration,
        position_snapshot=position_snapshot
    )

async def log_atomic_transaction(
    self,
    timestamp: pd.Timestamp,
    bundle_name: str,
    detail_events: List[Dict],
    net_result: Dict,
    position_snapshot: Optional[Dict] = None
) -> List[int]:
    """
    Log atomic transaction (flash loan bundle).
    
    Creates wrapper event + detail events.
    
    Args:
        bundle_name: 'ATOMIC_LEVERAGE_ENTRY', 'ATOMIC_DELEVERAGE', etc.
        detail_events: List of individual operations
        net_result: Summary of net effect
    
    Returns:
        List of event order numbers [wrapper_order, detail_orders...]
    """
    # Log wrapper event
    wrapper_order = await self.log_event(
        timestamp=timestamp,
        event_type='ATOMIC_TRANSACTION',
        venue='INSTADAPP',
        token='COMPOSITE',
        amount=1,
        bundle_name=bundle_name,
        net_result=net_result,
        detail_count=len(detail_events),
        position_snapshot=position_snapshot
    )
    
    # Log detail events
    detail_orders = []
    for detail in detail_events:
        detail_order = await self.log_event(
            timestamp=timestamp,
            parent_event=wrapper_order,
            **detail
        )
        detail_orders.append(detail_order)
    
    return [wrapper_order] + detail_orders

async def log_perp_trade(
    self,
    timestamp: pd.Timestamp,
    venue: str,
    instrument: str,
    side: str,
    size_eth: float,
    entry_price: float,
    notional_usd: float,
    execution_cost_usd: float,
    position_snapshot: Optional[Dict] = None
) -> int:
    """Log perpetual futures trade."""
    return await self.log_event(
        timestamp=timestamp,
        event_type='TRADE_EXECUTED',
        venue=venue.upper(),
        token='ETH',
        amount=abs(size_eth),
        side=side,  # 'SHORT' or 'LONG'
        instrument=instrument,
        entry_price=entry_price,
        notional_usd=notional_usd,
        execution_cost_usd=execution_cost_usd,
        position_snapshot=position_snapshot
    )

async def log_funding_payment(
    self,
    timestamp: pd.Timestamp,
    venue: str,
    funding_rate: float,
    notional_usd: float,
    pnl_usd: float,
    position_snapshot: Optional[Dict] = None
) -> int:
    """Log funding rate payment (8-hourly)."""
    pnl_type = 'RECEIVED' if pnl_usd > 0 else 'PAID'
    
    return await self.log_event(
        timestamp=timestamp,
        event_type='FUNDING_PAYMENT',
        venue=venue.upper(),
        token='USDT',
        amount=abs(pnl_usd),
        funding_rate=funding_rate,
        notional_usd=notional_usd,
        pnl_usd=pnl_usd,
        pnl_type=pnl_type,
        position_snapshot=position_snapshot
    )
```

---

## 📋 **Event Types**

### **On-Chain Events**:
- `GAS_FEE_PAID` - Gas payment
- `STAKE_DEPOSIT` - ETH → LST
- `STAKE_WITHDRAWAL` - LST → ETH
- `COLLATERAL_SUPPLIED` - Token → AAVE
- `COLLATERAL_WITHDRAWN` - AAVE → Token
- `LOAN_CREATED` - Borrow from AAVE
- `LOAN_REPAID` - Repay to AAVE
- `VENUE_TRANSFER` - Wallet ↔ CEX

### **CEX Events**:
- `SPOT_TRADE` - CEX spot trade
- `TRADE_EXECUTED` - Perp trade
- `FUNDING_PAYMENT` - Funding rate payment

### **Complex Events**:
- `ATOMIC_TRANSACTION` - Wrapper for flash loan bundle
- `FLASH_BORROW` - Flash loan initiation
- `FLASH_REPAID` - Flash loan repayment
- `ATOMIC_LEVERAGE_EXECUTION` - Atomic leveraged staking execution

### **Monitoring Events**:
- `HOURLY_RECONCILIATION` - Balance sync
- `PRICE_UPDATE` - Market data update
- `RISK_ALERT` - Risk threshold breached
- `REBALANCE_EXECUTED` - Rebalancing completed

---

## 🔗 **Integration**

### **Used By** (All components log events):
- Position Monitor (balance changes)
- Exposure Monitor (exposure updates)
- Risk Monitor (risk alerts)
- P&L Calculator (P&L snapshots)
- Strategy Manager (rebalancing decisions)
- CEX Execution Manager (trades)
- OnChain Execution Manager (transactions)

### **Provides Data To**:
- **CSV Export** - Final event_log.csv file
- **Direct Method Calls** - Component communication

---

## 📊 **Component Communication**

### **Direct Method Calls**:

**Event Logging**: Components call `log_event()` directly
```json
{
  "order": 1523,
  "event_type": "GAS_FEE_PAID",
  "timestamp": "2024-05-12T14:00:00Z",
  "venue": "ETHEREUM"
}
```

**Channel**: `events:atomic_bundle`
```json
{
  "wrapper_order": 1,
  "bundle_name": "ATOMIC_LEVERAGE_ENTRY",
  "detail_orders": [2, 3, 4, 5, 6, 7],
  "timestamp": "2024-05-12T00:00:00Z"
}
```

---

## 🔄 **Backtest vs Live**

### **Backtest**:
```python
event = {
    'timestamp': pd.Timestamp('2024-05-12 14:00:00', tz='UTC'),
    'order': 1523,
    'event_type': 'STAKE_DEPOSIT',
    'status': 'completed',  # Always completed
    'completion_timestamp': None,  # Same as timestamp
    'tx_hash': None,
    'confirmation_blocks': None
}
```

### **Live**:
```python
# Initial log (pending)
event = {
    'timestamp': pd.Timestamp.now(tz='UTC'),
    'trigger_timestamp': pd.Timestamp.now(tz='UTC'),
    'order': 1523,
    'event_type': 'STAKE_DEPOSIT',
    'status': 'pending'
}

# Update when submitted
event_logger.update_event(1523, {
    'status': 'submitted',
    'tx_hash': '0xabc123...'
})

# Update when confirmed
event_logger.update_event(1523, {
    'status': 'confirmed',
    'completion_timestamp': pd.Timestamp.now(tz='UTC'),
    'confirmation_blocks': 12
})
```

---

## 🧪 **Testing**

```python
def test_global_order_unique():
    """Test each event gets unique order."""
    logger = EventLogger()
    
    order1 = logger.log_event(timestamp, 'GAS_FEE_PAID', 'ETHEREUM')
    order2 = logger.log_event(timestamp, 'STAKE_DEPOSIT', 'ETHERFI')
    
    assert order1 == 1
    assert order2 == 2
    assert order1 != order2

def test_atomic_bundle_logging():
    """Test wrapper + detail events for atomic transactions."""
    logger = EventLogger()
    
    orders = logger.log_atomic_transaction(
        timestamp=timestamp,
        bundle_name='ATOMIC_LEVERAGE_ENTRY',
        detail_events=[
            {'event_type': 'FLASH_BORROW', 'venue': 'BALANCER', ...},
            {'event_type': 'STAKE_DEPOSIT', 'venue': 'ETHERFI', ...},
            # ... 6 steps
        ],
        net_result={'collateral': 95.24, 'debt': 88.7}
    )
    
    # 1 wrapper + 6 details = 7 events
    assert len(orders) == 7
    assert logger.events[0]['event_type'] == 'ATOMIC_TRANSACTION'
    assert logger.events[1]['parent_event'] == orders[0]

def test_balance_snapshots_included():
    """Test position snapshots included in events."""
    logger = EventLogger(include_balance_snapshots=True)
    
    snapshot = {
        'wallet': {'ETH': 49.9965, 'aWeETH': 95.24},
        'cex_accounts': {'binance': {'USDT': 24992.50}}
    }
    
    order = logger.log_event(
        timestamp=timestamp,
        event_type='GAS_FEE_PAID',
        venue='ETHEREUM',
        position_snapshot=snapshot
    )
    
    event = logger.events[0]
    assert event['wallet_balance_after'] == snapshot  # Full Position Monitor output
    assert event['cex_balance_after'] == snapshot['cex_accounts']
```

---

## 🔧 **Current Implementation Status**

**Overall Completion**: 85% (Core functionality working, tight loop architecture violations need fixing)

### **Core Functionality Status**
- ✅ **Working**: Global order assignment, 20+ event types support, optional balance snapshots, atomic bundle logging, future-proof for live mode, direct method calls, CSV export, parent-child event relationships
- ⚠️ **Partial**: None
- ❌ **Missing**: None
- 🔄 **Refactoring Needed**: Tight loop architecture compliance

### **Architecture Compliance Status**
- ❌ **VIOLATIONS FOUND**: 
  - **Issue**: Tight loop architecture violations - component may not follow strict tight loop sequence requirements
  - **Canonical Source**: [docs/REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Tight Loop Architecture
  - **Priority**: High
  - **Fix Required**: Verify tight loop sequence is enforced, check for proper event processing order, ensure no state clearing violations, validate consistent processing flow

### **TODO Items and Refactoring Needs**
- **High Priority**:
  - Fix tight loop architecture violations (TODO-REFACTOR comment in event_logger.py line 4)
  - Ensure no state clearing violations
- **Medium Priority**:
  - None identified
- **Low Priority**:
  - None identified

## Related Documentation
- [Reference-Based Architecture](../REFERENCE_ARCHITECTURE.md)
- [Shared Clock Pattern](../SHARED_CLOCK_PATTERN.md)
- [Request Isolation Pattern](../REQUEST_ISOLATION_PATTERN.md)

### **Component Integration**
- [Position Monitor Specification](01_POSITION_MONITOR.md) - Logs position update events
- [Exposure Monitor Specification](02_EXPOSURE_MONITOR.md) - Logs exposure calculation events
- [Risk Monitor Specification](03_RISK_MONITOR.md) - Logs risk assessment events
- [P&L Calculator Specification](04_PNL_CALCULATOR.md) - Logs P&L calculation events
- [Strategy Manager Specification](05_STRATEGY_MANAGER.md) - Logs strategy decision events
- [Execution Manager Specification](06_EXECUTION_MANAGER.md) - Logs execution events
- [Execution Interface Manager Specification](07_EXECUTION_INTERFACE_MANAGER.md) - Logs execution routing events
- [Data Provider Specification](09_DATA_PROVIDER.md) - Logs data loading events
- [Reconciliation Component Specification](10_RECONCILIATION_COMPONENT.md) - Logs reconciliation events
- [Position Update Handler Specification](11_POSITION_UPDATE_HANDLER.md) - Logs position update orchestration events

### **Quality Gate Status**
- **Current Status**: PARTIAL
- **Failing Tests**: Tight loop architecture compliance tests
- **Requirements**: Fix tight loop violations
- **Integration**: Integrates with quality gate system through event logger tests

### **Task Completion Status**
- **Related Tasks**: 
  - [.cursor/tasks/10_tight_loop_architecture_requirements.md](../../.cursor/tasks/10_tight_loop_architecture_requirements.md) - Tight Loop Architecture (50% complete - violations identified, fixes needed)
- **Completion**: 85% complete overall
- **Blockers**: Tight loop architecture compliance
- **Next Steps**: Fix tight loop architecture violations

---

## 🎯 **Success Criteria**

- [ ] Global order assignment (unique per event)
- [ ] Support 20+ event types
- [ ] Optional balance snapshots (configurable)
- [ ] Atomic bundle logging (wrapper + details)
- [ ] Future-proof for live (optional fields)
- [ ] Direct method calls for component communication
- [ ] CSV export with all fields
- [ ] Parent-child event relationships

---

**Status**: Specification complete! ✅


