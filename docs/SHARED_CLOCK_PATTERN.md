# Shared Clock Pattern

## Core Principle
EventDrivenStrategyEngine owns the current timestamp and passes it to all component method calls. Components NEVER advance time, only receive timestamps.

## Data Access Pattern
All components query data using:
```python
market_data = self.data_provider.get_data(timestamp)
```

## Time Constraint
Data retrieved MUST be <= timestamp to ensure:
1. All components in same loop use identical data
2. No forward-looking bias
3. If data updates mid-loop, stale snapshot prevents inconsistency

## Clock Owner: EventDrivenStrategyEngine
- Manages current_timestamp
- Advances timestamp per loop iteration
- Passes timestamp to all component update_state() calls

## Component Behavior
- Receive timestamp as parameter
- Query data_provider with that exact timestamp
- NEVER advance or modify timestamp
- NEVER cache data across timestamps

## Full Loop Flow
1. EventDrivenStrategyEngine: current_timestamp = next_timestamp
2. EventDrivenStrategyEngine: Calls _process_timestep(current_timestamp)
3. _process_timestep: Calls component.update_state(current_timestamp, ...)
4. Each component: market_data = self.data_provider.get_data(current_timestamp)
5. All components use same timestamp → same data snapshot

## Code Structure Example
```python
class EventDrivenStrategyEngine:
    def __init__(self, config: Dict, execution_mode: str, data_provider: DataProvider, components: Dict):
        self.config = config
        self.execution_mode = execution_mode
        self.data_provider = data_provider
        self.components = components
        self.current_timestamp = None
        self.timestamps = []  # Loaded from data_provider
    
    def run_backtest(self, start_date: str, end_date: str):
        self.timestamps = self.data_provider.get_timestamps(start_date, end_date)
        
        for timestamp in self.timestamps:
            self.current_timestamp = timestamp
            self._process_timestep(timestamp)
    
    def _process_timestep(self, timestamp: pd.Timestamp):
        # Pass timestamp to all components
        self.components['position_monitor'].update_state(timestamp, 'full_loop')
        self.components['exposure_monitor'].update_state(timestamp, 'full_loop')
        self.components['risk_monitor'].update_state(timestamp, 'full_loop')
        self.components['pnl_calculator'].update_state(timestamp, 'full_loop')
        # ... rest of full loop
```

```python
class ExampleComponent:
    def __init__(self, config: Dict, data_provider: DataProvider, execution_mode: str):
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        self.last_update_timestamp = None
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
        # Receive timestamp, never generate/modify it
        market_data = self.data_provider.get_data(timestamp)
        
        # All logic uses this exact timestamp
        self.last_update_timestamp = timestamp
        
        # Process with timestamp-consistent data
        self._process_with_data(market_data, timestamp)
```

## Data Provider Implementation
```python
class DataProvider:
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        # Enforce data <= timestamp constraint
        filtered_data = {}
        for key, data_series in self.data.items():
            # Get latest data point <= timestamp
            filtered_data[key] = data_series[data_series.index <= timestamp].iloc[-1]
        
        return filtered_data
    
    def get_timestamps(self, start_date: str, end_date: str) -> List[pd.Timestamp]:
        # Return all timestamps in range for engine to iterate
        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)
        return self.data['prices'].index[(self.data['prices'].index >= start_ts) & 
                                        (self.data['prices'].index <= end_ts)].tolist()
```

## Benefits
1. **Data Consistency**: All components use identical data snapshots
2. **No Forward Bias**: Impossible to accidentally use future data
3. **Deterministic**: Same timestamp always produces same data
4. **Debugging**: Easy to trace data usage by timestamp
5. **Performance**: Single data query per component per timestamp

## Anti-Patterns to Avoid
```python
# WRONG - Component advancing time
def update_state(self, timestamp: pd.Timestamp):
    next_timestamp = timestamp + pd.Timedelta(hours=1)  # Don't advance time
    future_data = self.data_provider.get_data(next_timestamp)

# WRONG - Caching data across timestamps
def update_state(self, timestamp: pd.Timestamp):
    if not hasattr(self, '_cached_data'):
        self._cached_data = self.data_provider.get_data(timestamp)  # Don't cache
    market_data = self._cached_data

# WRONG - Using current time instead of passed timestamp
def update_state(self, timestamp: pd.Timestamp):
    current_time = pd.Timestamp.now()  # Don't use current time
    market_data = self.data_provider.get_data(current_time)

# CORRECT - Always use passed timestamp
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    market_data = self.data_provider.get_data(timestamp)
    # Use timestamp for all time-based logic
```

## Integration with Other Patterns
- **Reference-Based Architecture**: Components use stored data_provider reference with timestamps
- **Request Isolation Pattern**: Fresh data_provider created per request with mode-specific data
- **Mode-Aware Behavior**: Data provider returns different data based on execution_mode
- **Synchronous Execution**: Timestamp passing enables synchronous data queries
