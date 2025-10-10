# Position Update Handler Component Specification

## Purpose
Orchestrates the tight loop sequence between position updates and downstream component chain, abstracting tight loop complexity from EventDrivenStrategyEngine. 

## 📚 **Canonical Sources**

- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](../MODES.md) - Canonical strategy mode definitions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides
- **Related Components**: [06_EXECUTION_MANAGER.md](06_EXECUTION_MANAGER.md) - Execution Manager integration
- **Related Components**: [07_EXECUTION_INTERFACE_MANAGER.md](07_EXECUTION_INTERFACE_MANAGER.md) - Execution Interface Manager integration

## Responsibilities
1. Receive position update triggers from Execution Manager
2. Orchestrate tight loop: position_monitor → exposure_monitor → risk_monitor → pnl_calculator
3. Handle both full loop and tight loop triggers
4. Coordinate reconciliation handshake with Execution Manager

## State
- tight_loop_active: bool
- current_loop_timestamp: pd.Timestamp
- loop_execution_count: int (per full loop cycle)
- last_trigger_source: str
- execution_deltas: Dict (current deltas being processed)

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- position_monitor: PositionMonitor
- exposure_monitor: ExposureMonitor
- risk_monitor: RiskMonitor
- pnl_calculator: PnLCalculator
- reconciliation_component: ReconciliationComponent
- data_provider: DataProvider (reference only, uses shared clock)
- config: Dict (reference, never modified)
- execution_mode: str (BASIS_EXECUTION_MODE)

These references are stored in __init__ and used throughout component lifecycle.
Components NEVER receive these as method parameters during runtime.

## Core Methods

### update_state(timestamp: pd.Timestamp, trigger_source: str, execution_deltas: Dict = None)
Main entry point for position update orchestration.

Parameters:
- timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
- trigger_source: 'full_loop' | 'execution_manager' | 'manual'
- execution_deltas: Dict (optional) - position deltas from execution manager

Behavior:
1. Store current state: timestamp, trigger_source, execution_deltas
2. Route to appropriate execution path based on trigger_source
3. Execute tight loop sequence with or without reconciliation
4. NO async/await: Synchronous orchestration only

Returns:
- None (state updated in place)

### _execute_tight_loop(timestamp: pd.Timestamp, execution_deltas: Dict = None)
Execute the tight loop sequence with reconciliation handshake.

Parameters:
- timestamp: Current loop timestamp
- execution_deltas: Position deltas from execution manager (optional)

Behavior:
1. Call position_monitor.update_state(timestamp, execution_deltas, 'execution_manager')
2. Call reconciliation_component.update_state(timestamp, simulated_state, 'execution_manager')
3. If reconciliation success: Continue tight loop chain
4. If reconciliation failed: Trigger refresh loop
5. Call exposure_monitor.update_state(timestamp, 'tight_loop')
6. Call risk_monitor.update_state(timestamp, 'tight_loop')
7. Call pnl_calculator.update_state(timestamp, 'tight_loop')

### _execute_full_loop(timestamp: pd.Timestamp)
Execute the full loop sequence without reconciliation.

Parameters:
- timestamp: Current loop timestamp

Behavior:
1. Call position_monitor.update_state(timestamp, None, 'full_loop')
2. Call exposure_monitor.update_state(timestamp, 'full_loop')
3. Call risk_monitor.update_state(timestamp, 'full_loop')
4. Call pnl_calculator.update_state(timestamp, 'full_loop')

## Data Access Pattern

Components query data using shared clock:
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str, execution_deltas: Dict = None):
    # Store current state
    self.current_loop_timestamp = timestamp
    self.last_trigger_source = trigger_source
    self.execution_deltas = execution_deltas
    
    # Route to appropriate execution path
    if trigger_source == 'execution_manager':
        self._execute_tight_loop(timestamp, execution_deltas)
    elif trigger_source == 'full_loop':
        self._execute_full_loop(timestamp)
```

NEVER pass data as parameter between components.
NEVER cache data across timestamps.

## Mode-Aware Behavior

### Backtest Mode
```python
def _execute_tight_loop(self, timestamp: pd.Timestamp, execution_deltas: Dict = None):
    if self.execution_mode == 'backtest':
        # Execute tight loop with simulated reconciliation
        self.position_monitor.update_state(timestamp, execution_deltas, 'execution_manager')
        # Reconciliation always succeeds in backtest
        self.exposure_monitor.update_state(timestamp, 'tight_loop')
        self.risk_monitor.update_state(timestamp, 'tight_loop')
        self.pnl_calculator.update_state(timestamp, 'tight_loop')
```

### Live Mode
```python
def _execute_tight_loop(self, timestamp: pd.Timestamp, execution_deltas: Dict = None):
    elif self.execution_mode == 'live':
        # Execute tight loop with real reconciliation
        self.position_monitor.update_state(timestamp, execution_deltas, 'execution_manager')
        
        # Check reconciliation status
        if self.reconciliation_component.reconciliation_status == 'success':
            # Continue tight loop chain
            self.exposure_monitor.update_state(timestamp, 'tight_loop')
            self.risk_monitor.update_state(timestamp, 'tight_loop')
            self.pnl_calculator.update_state(timestamp, 'tight_loop')
        else:
            # Reconciliation failed - trigger refresh
            self._trigger_position_refresh(timestamp)
```

## Integration with Tight Loop

### Execution Manager Integration
```python
# Execution Manager calls this sequence
def _process_single_block(self, timestamp: pd.Timestamp, block: Dict):
    # Reset reconciliation status
    self.reconciliation_component.reconciliation_status = 'pending'
    
    # Execute instruction and get deltas
    deltas = self.execution_interface_manager.route_instruction(timestamp, block)
    
    # Update position with deltas via Position Update Handler
    self.position_update_handler.update_state(timestamp, 'execution_manager', deltas)
    
    # Check reconciliation status (synchronous polling)
    if self.reconciliation_component.reconciliation_status == 'success':
        return True
    else:
        return False
```

### EventDrivenStrategyEngine Integration
```python
# EventDrivenStrategyEngine calls this for full loop
def _process_timestep(self, timestamp: pd.Timestamp):
    # Full loop - no execution deltas
    self.position_update_handler.update_state(timestamp, 'full_loop')
    
    # Strategy decision and execution (if any)
    # ... strategy logic ...
```

## Integration Points

### Called BY
- ExecutionManager (tight loop): position_update_handler.update_state(timestamp, 'execution_manager', execution_deltas)
- EventDrivenStrategyEngine (full loop): position_update_handler.update_state(timestamp, 'full_loop')

### Calls TO
- position_monitor.update_state(timestamp, execution_deltas, trigger_source) - position updates
- exposure_monitor.update_state(timestamp, 'tight_loop') - exposure calculations
- risk_monitor.update_state(timestamp, 'tight_loop') - risk assessments
- pnl_calculator.update_state(timestamp, 'tight_loop') - P&L calculations
- reconciliation_component.update_state(timestamp, simulated_state, 'execution_manager') - reconciliation

### Communication
- Direct method calls ONLY
- NO event publishing
- NO Redis/message queues
- NO async/await in internal methods

## Error Handling

### Backtest Mode
- **Fail fast**: Fail fast and pass failure down codebase
- **Immediate feedback**: Errors should be immediately visible
- **Stop execution**: Stop tight loop on critical errors
- **No retries**: Not applicable in backtest mode

### Live Mode
- **Retry logic**: Wait 0.1s, retry with exponential backoff
- **Max attempts**: Maximum 3 attempts per instruction block
- **Error logging**: Log error and pass failure down after max attempts
- **Continue execution**: Continue tight loop after non-critical errors

## Configuration Parameters

### From Config
- tight_loop_timeout: int = 30 (seconds)
- max_retry_attempts: int = 3
- retry_delay_seconds: float = 0.1
- enable_reconciliation: bool = True

### Environment Variables
- BASIS_EXECUTION_MODE: 'backtest' | 'live' (controls tight loop behavior)

## Code Structure Example

```python
class PositionUpdateHandler:
    def __init__(self, config: Dict, data_provider: DataProvider, execution_mode: str,
                 position_monitor: PositionMonitor, exposure_monitor: ExposureMonitor,
                 risk_monitor: RiskMonitor, pnl_calculator: PnLCalculator,
                 reconciliation_component: ReconciliationComponent):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        self.position_monitor = position_monitor
        self.exposure_monitor = exposure_monitor
        self.risk_monitor = risk_monitor
        self.pnl_calculator = pnl_calculator
        self.reconciliation_component = reconciliation_component
        
        # Initialize component-specific state
        self.tight_loop_active = False
        self.current_loop_timestamp = None
        self.loop_execution_count = 0
        self.last_trigger_source = None
        self.execution_deltas = None
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, 
                    execution_deltas: Dict = None):
        """Main orchestration entry point."""
        # Store current state
        self.current_loop_timestamp = timestamp
        self.last_trigger_source = trigger_source
        self.execution_deltas = execution_deltas
        
        # Route to appropriate execution path
        if trigger_source == 'execution_manager':
            self._execute_tight_loop(timestamp, execution_deltas)
        elif trigger_source == 'full_loop':
            self._execute_full_loop(timestamp)
        else:
            raise ValueError(f"Unknown trigger_source: {trigger_source}")
    
    def _execute_tight_loop(self, timestamp: pd.Timestamp, execution_deltas: Dict = None):
        """Execute tight loop with reconciliation handshake."""
        self.tight_loop_active = True
        
        try:
            # Update position with execution deltas
            self.position_monitor.update_state(timestamp, execution_deltas, 'execution_manager')
            
            # Check reconciliation (mode-aware)
            if self.execution_mode == 'backtest':
                # Always succeed in backtest
                reconciliation_success = True
            elif self.execution_mode == 'live':
                # Check real reconciliation status
                reconciliation_success = (self.reconciliation_component.reconciliation_status == 'success')
            
            if reconciliation_success:
                # Continue tight loop chain
                self.exposure_monitor.update_state(timestamp, 'tight_loop')
                self.risk_monitor.update_state(timestamp, 'tight_loop')
                self.pnl_calculator.update_state(timestamp, 'tight_loop')
            else:
                # Reconciliation failed - trigger refresh
                self._trigger_position_refresh(timestamp)
        
        finally:
            self.tight_loop_active = False
            self.loop_execution_count += 1
    
    def _execute_full_loop(self, timestamp: pd.Timestamp):
        """Execute full loop without reconciliation."""
        # Update all components in sequence
        self.position_monitor.update_state(timestamp, None, 'full_loop')
        self.exposure_monitor.update_state(timestamp, 'full_loop')
        self.risk_monitor.update_state(timestamp, 'full_loop')
        self.pnl_calculator.update_state(timestamp, 'full_loop')
    
    def _trigger_position_refresh(self, timestamp: pd.Timestamp):
        """Trigger position refresh for reconciliation failure."""
        if self.execution_mode == 'live':
            # Refresh position and retry reconciliation
            self.position_monitor.update_state(timestamp, None, 'position_refresh')
            # Reconciliation component will be called again by execution manager
    
    def get_health_status(self) -> Dict:
        """Health check for position update handler."""
        return {
            'status': 'healthy',
            'tight_loop_active': self.tight_loop_active,
            'last_trigger_source': self.last_trigger_source,
            'loop_execution_count': self.loop_execution_count,
            'execution_mode': self.execution_mode
        }
```

## Related Documentation
- [Reference-Based Architecture](../REFERENCE_ARCHITECTURE.md)
- [Shared Clock Pattern](../SHARED_CLOCK_PATTERN.md)
- [Request Isolation Pattern](../REQUEST_ISOLATION_PATTERN.md)
- [Position Monitor Specification](01_POSITION_MONITOR.md)
- [Exposure Monitor Specification](02_EXPOSURE_MONITOR.md)
- [Risk Monitor Specification](03_RISK_MONITOR.md)
- [PnL Calculator Specification](04_PNL_CALCULATOR.md)
- [Reconciliation Component Specification](10_RECONCILIATION_COMPONENT.md)
- [Execution Manager Specification](06_EXECUTION_MANAGER.md)
- [Event-Driven Strategy Engine Specification](15_EVENT_DRIVEN_STRATEGY_ENGINE.md)
