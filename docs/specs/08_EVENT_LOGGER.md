# Event Logger Component Specification

**Last Reviewed**: October 10, 2025

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

## Configuration Parameters

**Mode Configuration** (from `configs/modes/*.yaml`):
- `event_logging_settings`: Event logging settings - used for event logging configuration
- `log_retention_policy`: Log retention policy - used for log management
- `event_filtering`: Event filtering settings - used for event filtering

**Venue Configuration** (from `configs/venues/*.yaml`):
- `logging_requirements`: Venue-specific logging requirements - used for venue-specific logging
- `event_categories`: Event categories - used for event categorization

**Share Class Configuration** (from `configs/share_classes/*.yaml`):
- `audit_requirements`: Audit requirements - used for audit logging
- `compliance_settings`: Compliance settings - used for compliance logging

## Config-Driven Behavior

The Event Logger is **mode-agnostic** by design - it logs events without mode-specific logic:

**Component Configuration** (from `component_config.event_logger`):
```yaml
component_config:
  event_logger:
    # Event Logger is inherently mode-agnostic
    # Logs all events regardless of strategy mode
    # No mode-specific configuration needed
    event_buffer_size: 10000    # Maximum events to keep in memory
    event_export_format: "json" # Format for event export
    log_retention_days: 30      # Log retention period
```

**Mode-Agnostic Event Logging**:
- Logs all component state changes with timestamps
- Same logging logic for all strategy modes
- No mode-specific if statements in event logging
- Uses config-driven buffer size and retention settings

**Event Logging by Mode**:

**Pure Lending Mode**:
- Logs: position_monitor (USDT/aUSDT), exposure_monitor (USDT exposure), risk_monitor (AAVE health), pnl_calculator (supply yield)
- Simple event logging
- Same logging logic as other modes

**BTC Basis Mode**:
- Logs: position_monitor (BTC spot/perp), exposure_monitor (BTC/USDT exposure), risk_monitor (CEX margin/funding risk), pnl_calculator (funding/delta PnL)
- Multi-venue event logging
- Same logging logic as other modes

**ETH Leveraged Mode**:
- Logs: position_monitor (ETH/LST/AAVE), exposure_monitor (ETH exposure), risk_monitor (AAVE health/liquidation), pnl_calculator (staking/borrow PnL)
- Complex AAVE event logging
- Same logging logic as other modes

**Key Principle**: Event Logger is **purely logging** - it does NOT:
- Make mode-specific decisions about which events to log
- Handle strategy-specific logging logic
- Filter or transform events based on strategy mode
- Make business logic decisions

All event logging is generic - it logs all component state changes with timestamps and global ordering regardless of strategy mode, providing audit-grade event trails for debugging and compliance.

**Cross-Reference**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete configuration hierarchy
**Cross-Reference**: [ENVIRONMENT_VARIABLES.md](../ENVIRONMENT_VARIABLES.md) - Environment variable definitions

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
- `mode`: str - e.g., 'eth_basis', 'pure_lending'
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

### Logging Configuration Fields
- `log_format`: str - Log format specification
  - **Usage**: Used in `event_logger.py:58` to set the format for log output
  - **Required**: Yes
  - **Used in**: `event_logger.py:58`

- `log_path`: str - Log file path
  - **Usage**: Used in `event_logger.py:53` to set the path where log files are written
  - **Required**: Yes
  - **Used in**: `event_logger.py:53`

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

## Data Access Pattern

### Query Pattern
```python
def log_event(self, timestamp: pd.Timestamp, event_type: str, component: str, data: Dict):
    # EventLogger does not query external data sources
    # All data comes from component parameters
    pass
```

### Data Dependencies
- **No external data dependencies** - EventLogger is a pure logging component
- **All data comes from component parameters** passed to log_event()

## Mode-Aware Behavior

### Backtest Mode
```python
def log_event(self, timestamp: pd.Timestamp, event_type: str, component: str, data: Dict):
    if self.execution_mode == 'backtest':
        # Store events in memory for CSV export
        self._store_event_in_memory(timestamp, event_type, component, data)
```

### Live Mode
```python
def log_event(self, timestamp: pd.Timestamp, event_type: str, component: str, data: Dict):
    elif self.execution_mode == 'live':
        # Write events immediately to JSONL files
        self._write_event_to_jsonl(timestamp, event_type, component, data)
```

## Event Logging Requirements

### Component Event Log File
**Separate log file** for this component's events:
- **File**: `logs/events/event_logger_events.jsonl`
- **Format**: JSON Lines (one event per line)
- **Rotation**: Daily rotation, keep 30 days
- **Purpose**: Component-specific audit trail

### Event Logging via EventLogger
All events logged through centralized EventLogger:

```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='[event_type]',
    component='EventLogger',
    data={
        'event_specific_data': value,
        'state_snapshot': self.get_state_snapshot()  # optional
    }
)
```

### Events to Log

#### 1. Component Initialization
```python
self.event_logger.log_event(
    timestamp=pd.Timestamp.now(),
    event_type='component_initialization',
    component='EventLogger',
    data={
        'execution_mode': self.execution_mode,
        'config_hash': hash(str(self.config))
    }
)
```

#### 2. State Updates (Every log_event() Call)
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='state_update',
    component='EventLogger',
    data={
        'event_type': event_type,
        'source_component': component,
        'global_order': self.global_order,
        'events_count': len(self.events),
        'processing_time_ms': processing_time
    }
)
```

#### 3. Error Events
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='error',
    component='EventLogger',
    data={
        'error_code': 'EVT-001',
        'error_message': str(e),
        'stack_trace': traceback.format_exc(),
        'error_severity': 'CRITICAL|HIGH|MEDIUM|LOW'
    }
)
```

#### 4. Component-Specific Critical Events
- **Event Logging Failed**: When event logging fails
- **Global Order Assignment Failed**: When order assignment fails
- **Event Export Failed**: When event export fails

#### 5. Infrastructure Event Patterns
- **`data`**: Logs data-related events
  - **Usage**: Logged for data provider operations and data updates
  - **Data**: data_type, source, timestamp, data_quality_metrics
- **`risk`**: Logs risk-related events
  - **Usage**: Logged when risk thresholds are exceeded
  - **Data**: risk_type, severity, threshold_value, current_value, component
- **`event`**: Logs event system updates
  - **Usage**: Logged for event system state changes
  - **Data**: event_count, system_status, performance_metrics
- **`business`**: Logs business-related events
  - **Usage**: Logged for business logic events
  - **Data**: business metrics, performance data, operational events

### Event Retention & Output Formats

#### Dual Logging Approach
**Both formats are used**:
1. **JSON Lines (Iterative)**: Write events to component-specific JSONL files during execution
   - **Purpose**: Real-time monitoring during backtest runs
   - **Location**: `logs/events/event_logger_events.jsonl`
   - **When**: Events written as they occur (buffered for performance)
   
2. **CSV Export (Final)**: Comprehensive CSV export at Results Store stage
   - **Purpose**: Final analysis, spreadsheet compatibility
   - **Location**: `results/[backtest_id]/events.csv`
   - **When**: At backtest completion or on-demand

#### Mode-Specific Behavior
- **Backtest**: 
  - Write JSONL iteratively (allows tracking during long runs)
  - Export CSV at completion to Results Store
  - Keep all events in memory for final processing
  
- **Live**: 
  - Write JSONL immediately (no buffering)
  - Rotate daily, keep 30 days
  - CSV export on-demand for analysis

**Note**: Current implementation stores events in memory and exports to CSV only. Enhanced implementation will add iterative JSONL writing. Reference: `docs/specs/17_HEALTH_ERROR_SYSTEMS.md`

## Error Codes

### Component Error Code Prefix: EVT
All EventLogger errors use the `EVT` prefix.

### Error Code Registry
**Source**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`

All error codes registered with:
- **code**: Unique error code
- **component**: Component name
- **severity**: CRITICAL | HIGH | MEDIUM | LOW
- **message**: Human-readable error message
- **resolution**: How to resolve

### Component Error Codes

#### EVT-001: Event Logging Failed (HIGH)
**Description**: Failed to log event
**Cause**: Invalid event data, logging system errors, I/O failures
**Recovery**: Retry logging, check event data validity, verify I/O permissions
```python
raise ComponentError(
    error_code='EVT-001',
    message='Event logging failed',
    component='EventLogger',
    severity='HIGH'
)
```

#### EVT-002: Global Order Assignment Failed (CRITICAL)
**Description**: Failed to assign global order to event
**Cause**: Lock acquisition failure, order counter overflow, concurrency issues
**Recovery**: Immediate action required, check lock system, restart if necessary
```python
raise ComponentError(
    error_code='EVT-002',
    message='Global order assignment failed',
    component='EventLogger',
    severity='CRITICAL'
)
```

#### EVT-003: Event Export Failed (MEDIUM)
**Description**: Failed to export events to CSV/JSONL
**Cause**: File system errors, export format issues, I/O failures
**Recovery**: Log warning, retry export, check file system permissions
```python
raise ComponentError(
    error_code='EVT-003',
    message='Event export failed',
    component='EventLogger',
    severity='MEDIUM'
)
```

### Structured Error Handling Pattern

#### Error Raising
```python
from backend.src.basis_strategy_v1.core.error_codes.exceptions import ComponentError

try:
    result = self._log_event_internal(timestamp, event_type, component, data)
except Exception as e:
    # Log error event (if possible)
    try:
        self._log_error_event(timestamp, str(e), traceback.format_exc())
    except:
        pass  # Avoid infinite recursion
    
    # Raise structured error
    raise ComponentError(
        error_code='EVT-001',
        message=f'EventLogger failed: {str(e)}',
        component='EventLogger',
        severity='HIGH',
        original_exception=e
    )
```

#### Error Propagation Rules
- **CRITICAL**: Propagate to health system → trigger app restart
- **HIGH**: Log and retry with exponential backoff (max 3 retries)
- **MEDIUM**: Log and continue with degraded functionality
- **LOW**: Log for monitoring, no action needed

### Component Health Integration

#### Health Check Registration
```python
def __init__(self, ..., health_manager: UnifiedHealthManager):
    # Store health manager reference
    self.health_manager = health_manager
    
    # Register component with health system
    self.health_manager.register_component(
        component_name='EventLogger',
        checker=self._health_check
    )

def _health_check(self) -> Dict:
    """Component-specific health check."""
    return {
        'status': 'healthy' | 'degraded' | 'unhealthy',
        'last_update': self.last_log_timestamp,
        'errors': self.recent_errors[-10:],  # Last 10 errors
        'metrics': {
            'update_count': self.update_count,
            'avg_processing_time_ms': self.avg_processing_time,
            'error_rate': self.error_count / max(self.update_count, 1),
            'events_logged': len(self.events),
            'global_order': self.global_order,
            'memory_usage_mb': self._get_memory_usage()
        }
    }
```

#### Health Status Definitions
- **healthy**: No errors in last 100 updates, processing time < threshold
- **degraded**: Minor errors, slower processing, retries succeeding
- **unhealthy**: Critical errors, failed retries, unable to process

**Reference**: `docs/specs/17_HEALTH_ERROR_SYSTEMS.md`

## Quality Gates

### Validation Criteria
- [ ] All 18 sections present and complete
- [ ] Environment Variables section documents system-level and component-specific variables
- [ ] Config Fields Used section documents universal and component-specific config
- [ ] Data Provider Queries section documents N/A (no external data)
- [ ] Event Logging Requirements section documents component-specific JSONL file
- [ ] Event Logging Requirements section documents dual logging (JSONL + CSV)
- [ ] Error Codes section has structured error handling pattern
- [ ] Error Codes section references health integration
- [ ] Health integration documented with UnifiedHealthManager
- [ ] Component-specific log file documented (`logs/events/event_logger_events.jsonl`)

### Section Order Validation
- [ ] Purpose (section 1)
- [ ] Responsibilities (section 2)
- [ ] State (section 3)
- [ ] Component References (Set at Init) (section 4)
- [ ] Environment Variables (section 5)
- [ ] Config Fields Used (section 6)
- [ ] Data Provider Queries (section 7)
- [ ] Core Methods (section 8)
- [ ] Data Access Pattern (section 9)
- [ ] Mode-Aware Behavior (section 10)
- [ ] Event Logging Requirements (section 11)
- [ ] Error Codes (section 12)
- [ ] Quality Gates (section 13)
- [ ] Integration Points (section 14)
- [ ] Code Structure Example (section 15)
- [ ] Related Documentation (section 16)

### Implementation Status
- [x] Backend implementation exists and matches spec
- [x] All required methods implemented
- [x] Error handling follows structured pattern
- [x] Health integration implemented
- [x] Event logging implemented

## Async I/O Exception Pattern

Per ADR-006 Synchronous Component Execution, EventLogger is an explicit exception to synchronous component execution.

### Rationale
- **File/DB writes are not in critical trading path**: Event logging is asynchronous and doesn't block trading operations
- **Async I/O prevents blocking on disk operations**: File writes and database operations can be slow
- **Sequential awaits guarantee event ordering**: Global event ordering is maintained through async locks
- **No race conditions due to single-threaded event loop**: All async operations are sequential

### Allowed Async Patterns
```python
# All EventLogger methods are async per ADR-006
async def log_event(self, event_type: str, data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
    """Log event with global ordering"""
    async with self._order_lock:
        # Sequential event processing
        event = await self._process_event(event_type, data, timestamp)
        await self._write_event_to_storage(event)
        return event

async def log_gas_fee(self, gas_fee_data: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
    """Log gas fee event"""
    return await self.log_event('gas_fee', gas_fee_data, timestamp)
```

### API Call Queueing
All concurrent API calls are queued to prevent race conditions:
- Single worker processes queue sequentially
- FIFO ordering guaranteed
- No parallel execution of API calls
- Timeout handling per call

## Core Methods

### update_state(timestamp: pd.Timestamp, trigger_source: str, **kwargs)
Standard component update method following canonical architecture:
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs):
    """
    Update component state with new data.
    
    Args:
        timestamp: Current timestamp from EventDrivenStrategyEngine
        trigger_source: Source component that triggered this update
        **kwargs: Additional parameters specific to component
    """
    # Implementation specific to event logger
    pass
```

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
- [Reference-Based Architecture](../REFERENCE_ARCHITECTURE_CANONICAL.md)
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
  - [Task 12: Tight Loop Architecture](../../.cursor/tasks/12_tight_loop_architecture.md) - Tight Loop Architecture (50% complete - violations identified, fixes needed)
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

## Integration Points

### Called BY
- All components (event logging): event_logger.log_event(timestamp, event_type, component, data)
- Results Store (event export): event_logger.get_events(timestamp)
- Health System (health checks): event_logger.get_health_status()

### Calls TO
- None - EventLogger is a leaf component that only stores events

### Communication
- Direct method calls ONLY
- NO event publishing
- NO Redis/message queues
- NO async/await in internal methods

## Current Implementation Status

**Overall Completion**: 85% (Spec complete, implementation needs updates)

### **Core Functionality Status**
- ✅ **Working**: Event logging, global order assignment, CSV export
- ⚠️ **Partial**: Error handling patterns, health integration
- ❌ **Missing**: Config-driven retention settings, health integration
- 🔄 **Refactoring Needed**: Update to use BaseDataProvider type hints

### **Architecture Compliance Status**
- ✅ **COMPLIANT**: Spec follows all canonical architectural principles
  - **Reference-Based Architecture**: Components receive references at init
  - **Shared Clock Pattern**: Methods receive timestamp from engine
  - **Mode-Agnostic Behavior**: Config-driven, no mode-specific logic
  - **Fail-Fast Patterns**: Uses ADR-040 fail-fast access

## Related Documentation

### **Architecture Patterns**
- [Reference-Based Architecture](../REFERENCE_ARCHITECTURE_CANONICAL.md)
- [Mode-Agnostic Architecture](../REFERENCE_ARCHITECTURE_CANONICAL.md)
- [Code Structure Patterns](../CODE_STRUCTURE_PATTERNS.md)
- [Configuration Guide](19_CONFIGURATION.md)

### **Component Integration**
- [Results Store Specification](18_RESULTS_STORE.md) - Exports events to CSV
- [Health Error Systems Specification](17_HEALTH_ERROR_SYSTEMS.md) - Health integration
- [All Component Specs](COMPONENT_SPECS_INDEX.md) - All components log events

### **Configuration and Implementation**
- [Configuration Guide](19_CONFIGURATION.md) - Complete config schemas for all 7 modes
- [Code Structure Patterns](../CODE_STRUCTURE_PATTERNS.md) - Implementation patterns
- [Event Logger Specification](08_EVENT_LOGGER.md) - Event logging integration

---

**Status**: Specification complete! ✅  
**Last Reviewed**: October 11, 2025


