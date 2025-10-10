# Reconciliation Component Specification

## Purpose
Validates Position Monitor's simulated position state (from execution manager deltas) against real position state (from external APIs or backtest simulation), enabling execution manager to proceed only after successful reconciliation.      

## 📚 **Canonical Sources**

- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](../MODES.md) - Canonical strategy mode definitions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

## Responsibilities
1. Compare simulated vs real position state (all tokens + derivatives)
2. Return success/failure to execution manager
3. Trigger position refresh on mismatch (live mode only)
4. MODE-AWARE: Always succeed in backtest, poll/retry in live

## State
- current_reconciliation_status: 'pending' | 'success' | 'failed'
- last_reconciliation_timestamp: pd.Timestamp
- reconciliation_history: List[Dict] (for debugging)
- retry_count: int (per instruction block)
- max_retries: int = 3

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- position_monitor: PositionMonitor (read-only access to state)
- config: Dict (reference, NEVER modified)
- execution_mode: str (BASIS_EXECUTION_MODE)

These references are stored in __init__ and used throughout component lifecycle.
Components NEVER receive these as method parameters during runtime.

## Core Methods

### update_state(timestamp: pd.Timestamp, simulated_state: Dict, trigger_source: str) -> bool
Main entry point for reconciliation validation.

Parameters:
- timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
- simulated_state: Position state from execution manager deltas
- trigger_source: 'execution_manager' | 'position_refresh' | 'manual'

Behavior:
1. Query real state using: real_state = self.position_monitor.get_real_positions()
2. Compare simulated vs real state based on execution_mode
3. Update reconciliation_status based on comparison result
4. NO async/await: Synchronous execution only

Returns:
- bool: True if reconciliation successful, False if failed

### check_reconciliation(simulated_positions: Dict, real_positions: Dict) -> bool
Compare all tokens and derivatives for exact match.

Parameters:
- simulated_positions: Position state from execution manager
- real_positions: Position state from external APIs or backtest

Returns:
- bool: True if match within tolerance, False otherwise

Behavior:
1. Compare all token balances (USDT, ETH, aUSDT, aETH, wstETH, weETH, etc.)
2. Compare all derivative positions (futures, perps)
3. Apply tolerance thresholds for floating point precision
4. Log discrepancies for debugging

## Data Access Pattern

Components query data using shared clock:
```python
def update_state(self, timestamp: pd.Timestamp, simulated_state: Dict, trigger_source: str):
    # Query real state with timestamp (data <= timestamp guaranteed)
    real_state = self.position_monitor.get_real_positions()
    
    # Compare states
    match = self.check_reconciliation(simulated_state, real_state)
    
    # Update status based on mode
    if self.execution_mode == 'backtest':
        self.reconciliation_status = 'success'
    elif self.execution_mode == 'live':
        self.reconciliation_status = 'success' if match else 'failed'
```

NEVER pass position data as parameter between components.
NEVER cache position data across timestamps.

## Mode-Aware Behavior

### Backtest Mode
```python
def update_state(self, timestamp: pd.Timestamp, simulated_state: Dict, trigger_source: str):
    if self.execution_mode == 'backtest':
        # Always succeed immediately in backtest
        self.reconciliation_status = 'success'
        self.last_reconciliation_timestamp = timestamp
        return True
```

### Live Mode
```python
def update_state(self, timestamp: pd.Timestamp, simulated_state: Dict, trigger_source: str):
    elif self.execution_mode == 'live':
        # Poll external APIs with retries in live
        real_state = self.position_monitor.get_real_positions()
        match = self.check_reconciliation(simulated_state, real_state)
        
        if match:
            self.reconciliation_status = 'success'
            self.last_reconciliation_timestamp = timestamp
            return True
        else:
            self.reconciliation_status = 'failed'
            self.retry_count += 1
            return False
```

## Integration with Tight Loop

### Execution Flow
1. Execution Manager sends instruction to Position Monitor with deltas
2. Position Monitor updates simulated state, then real state
3. Position Monitor calls Reconciliation.update_state(timestamp, simulated_state, 'execution_manager')
4. Reconciliation compares simulated vs real
5. If match: Set reconciliation_status='success', Execution Manager proceeds
6. If mismatch (live only): Set status='failed', trigger Position Monitor refresh, retry
7. If persistent failure: Component health check fails → app restart

### Reconciliation Handshake
```python
# Execution Manager calls this sequence
def _process_single_block(self, timestamp: pd.Timestamp, block: Dict):
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        # Reset reconciliation status
        self.reconciliation_component.reconciliation_status = 'pending'
        
        # Execute instruction and get deltas
        deltas = self.execution_interface_manager.route_instruction(timestamp, block)
        
        # Update position with deltas
        self.position_update_handler.update_state(timestamp, 'execution_manager', deltas)
        
        # Check reconciliation status (synchronous polling)
        if self.reconciliation_component.reconciliation_status == 'success':
            return True
        
        retry_count += 1
        time.sleep(0.1)  # Small delay before retry
    
    raise ReconciliationError(f"Failed after {max_retries} attempts")
```

## Health Integration
- Max retry attempts: 3
- Timeout per attempt: 5s (live mode)
- Persistent failure triggers health system alert (see 17_HEALTH_ERROR_SYSTEMS.md)

### Health Check Integration
```python
def get_health_status(self) -> Dict:
    """Health check for reconciliation component."""
    if self.execution_mode == 'backtest':
        return {'status': 'healthy', 'reconciliation_status': self.reconciliation_status}
    
    elif self.execution_mode == 'live':
        if self.retry_count >= self.max_retries:
            return {
                'status': 'unhealthy',
                'error': 'Reconciliation failed after max retries',
                'retry_count': self.retry_count,
                'last_timestamp': self.last_reconciliation_timestamp
            }
        else:
            return {
                'status': 'healthy',
                'reconciliation_status': self.reconciliation_status,
                'retry_count': self.retry_count
            }
```

## Integration Points

### Called BY
- PositionUpdateHandler (tight loop): reconciliation_component.update_state(timestamp, simulated_state, 'execution_manager')
- ExecutionManager (status check): reconciliation_component.reconciliation_status
- Health System (health check): reconciliation_component.get_health_status()

### Calls TO
- position_monitor.get_real_positions() - real state queries
- position_monitor.refresh_positions() - position refresh triggers (live mode only)

### Communication
- Direct method calls ONLY
- NO event publishing
- NO Redis/message queues
- NO async/await in internal methods

## Error Handling

### Backtest Mode
- **Fail fast**: Always succeed (no real reconciliation needed)
- **Immediate feedback**: Status set to 'success' immediately
- **No retries**: Not applicable in backtest mode

### Live Mode
- **Retry logic**: Wait 0.1s, retry with exponential backoff
- **Max attempts**: Maximum 3 attempts per instruction block
- **Error logging**: Log error and set status to 'failed' after max attempts
- **Health integration**: Persistent failure triggers health system alert

## Configuration Parameters

### From Config
- reconciliation_tolerance: float = 0.01 (1% tolerance for floating point comparisons)
- max_retry_attempts: int = 3
- retry_delay_seconds: float = 0.1
- health_check_timeout: int = 5

### Environment Variables
- BASIS_EXECUTION_MODE: 'backtest' | 'live' (controls reconciliation behavior)

## Code Structure Example

```python
class ReconciliationComponent:
    def __init__(self, config: Dict, data_provider: DataProvider, 
                 execution_mode: str, position_monitor: PositionMonitor):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        self.position_monitor = position_monitor
        
        # Initialize component-specific state
        self.reconciliation_status = 'pending'
        self.last_reconciliation_timestamp = None
        self.reconciliation_history = []
        self.retry_count = 0
        self.max_retries = config.get('max_retry_attempts', 3)
        self.tolerance = config.get('reconciliation_tolerance', 0.01)
    
    def update_state(self, timestamp: pd.Timestamp, simulated_state: Dict, 
                    trigger_source: str) -> bool:
        """Main reconciliation entry point."""
        if self.execution_mode == 'backtest':
            # Always succeed in backtest
            self.reconciliation_status = 'success'
            self.last_reconciliation_timestamp = timestamp
            return True
        
        elif self.execution_mode == 'live':
            # Compare simulated vs real in live mode
            real_state = self.position_monitor.get_real_positions()
            match = self.check_reconciliation(simulated_state, real_state)
            
            if match:
                self.reconciliation_status = 'success'
                self.last_reconciliation_timestamp = timestamp
                self.retry_count = 0  # Reset on success
                return True
            else:
                self.reconciliation_status = 'failed'
                self.retry_count += 1
                return False
    
    def check_reconciliation(self, simulated_positions: Dict, real_positions: Dict) -> bool:
        """Compare positions within tolerance."""
        for token, sim_balance in simulated_positions.items():
            real_balance = real_positions.get(token, 0)
            if abs(sim_balance - real_balance) > self.tolerance:
                logger.warning(f"Position mismatch for {token}: sim={sim_balance}, real={real_balance}")
                return False
        return True
    
    def get_health_status(self) -> Dict:
        """Health check integration."""
        if self.execution_mode == 'backtest':
            return {'status': 'healthy', 'reconciliation_status': self.reconciliation_status}
        
        elif self.execution_mode == 'live':
            if self.retry_count >= self.max_retries:
                return {
                    'status': 'unhealthy',
                    'error': 'Reconciliation failed after max retries',
                    'retry_count': self.retry_count
                }
            else:
                return {
                    'status': 'healthy',
                    'reconciliation_status': self.reconciliation_status,
                    'retry_count': self.retry_count
                }
```

## Related Documentation
- [Reference-Based Architecture](../REFERENCE_ARCHITECTURE.md)
- [Shared Clock Pattern](../SHARED_CLOCK_PATTERN.md)
- [Request Isolation Pattern](../REQUEST_ISOLATION_PATTERN.md)

### **Component Integration**
- [Position Monitor Specification](01_POSITION_MONITOR.md) - Validates position state against real state
- [Execution Manager Specification](06_EXECUTION_MANAGER.md) - Receives reconciliation requests from execution
- [Position Update Handler Specification](11_POSITION_UPDATE_HANDLER.md) - Orchestrates reconciliation in tight loop
- [Data Provider Specification](09_DATA_PROVIDER.md) - Provides market data for reconciliation
- [Event Logger Specification](08_EVENT_LOGGER.md) - Logs reconciliation events
- [Health Error Systems](17_HEALTH_ERROR_SYSTEMS.md) - Reports reconciliation failures
