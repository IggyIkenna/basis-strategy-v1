# Request Isolation Pattern

## Overview
This document defines the Request Isolation Pattern - a critical architectural pattern that ensures complete isolation between backtest and live trading requests. Each request gets fresh instances of all components, preventing state pollution and enabling concurrent execution.

## Core Principle
Each backtest/live request gets completely fresh instances of DataProvider, config slice, and all components. No state pollution between requests.

## 📚 **Canonical Sources**

**This pattern aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides
- **Shared Clock Pattern**: [SHARED_CLOCK_PATTERN.md](SHARED_CLOCK_PATTERN.md) - Time management patterns

## App Startup (Once)
1. Load full config for all modes
2. Validate against Pydantic schemas
3. Check environment variables
4. Store validated global config (immutable)

## Per Request Lifecycle
1. **Request arrives** at BacktestService/LiveTradingService with:
   - strategy_name (mode)
   - config_overrides (optional)
   - start_date, end_date (backtest only)

2. **Config Slicing** (never modifies global config):
   - config_slice = global_config.get_mode(strategy_name)
   - config_slice.apply_overrides(request.config_overrides)

3. **Fresh DataProvider**:
   - data_provider = DataProviderFactory.create(execution_mode, config_slice)
   - Backtest: Load historical data for mode
   - Live: Initialize API clients for mode

4. **Fresh Components**:
   - Position Monitor initialized with initial_capital (backtest) or real sync (live)
   - All components created with references to config_slice, data_provider, other components
   - Component state starts fresh (no carryover from previous requests)

5. **Request Execution**:
   - EventDrivenStrategyEngine runs with fresh instances
   - Components share references, maintain state within this request only

6. **Request Completion**:
   - Save results
   - Discard all instances (GC cleanup)
   - Global config remains unchanged for next request

## Why This Matters
- Multiple concurrent backtest requests don't interfere
- Config overrides isolated per request
- Component state isolated per request
- Global config stays pristine for re-slicing

## Code Structure Example
```python
class BacktestService:
    def __init__(self, global_config: Dict):
        self.global_config = global_config  # Immutable, validated at startup
    
    async def run_backtest(self, request: BacktestRequest) -> str:
        # 1. Slice config for mode (never modifies global_config)
        config_slice = self._slice_config(request.strategy_name)
        
        # 2. Apply overrides to slice
        if request.config_overrides:
            config_slice = self._apply_overrides(config_slice, request.config_overrides)
        
        # 3. Create fresh DataProvider
        data_provider = DataProviderFactory.create('backtest', config_slice)
        data_provider.load_data_for_backtest(request.strategy_name, 
                                             request.start_date, 
                                             request.end_date)
        
        # 4. Create fresh components with references
        components = self._initialize_components(config_slice, data_provider, 'backtest')
        
        # 5. Run with fresh instances
        engine = EventDrivenStrategyEngine(config_slice, 'backtest', 
                                          data_provider, components)
        results = engine.run_backtest(request.start_date, request.end_date)
        
        # 6. Save results, discard instances (GC cleanup)
        self._save_results(request.request_id, results)
        return request.request_id
    
    def _slice_config(self, strategy_name: str) -> Dict:
        # Create deep copy of mode-specific config (never modify global)
        mode_config = copy.deepcopy(self.global_config['modes'][strategy_name])
        return mode_config
    
    def _apply_overrides(self, config_slice: Dict, overrides: Dict) -> Dict:
        # Apply overrides to slice (never modify global)
        config_slice.update(overrides)
        return config_slice
    
    def _initialize_components(self, config: Dict, data_provider: DataProvider, 
                              execution_mode: str) -> Dict:
        # Create fresh component instances with references
        position_monitor = PositionMonitor(config, data_provider, execution_mode)
        exposure_monitor = ExposureMonitor(config, data_provider, execution_mode, position_monitor)
        risk_monitor = RiskMonitor(config, data_provider, execution_mode, position_monitor, exposure_monitor)
        pnl_calculator = PnLCalculator(config, data_provider, execution_mode, 
                                      position_monitor, exposure_monitor, risk_monitor)
        strategy_manager = StrategyManager(config, data_provider, execution_mode, 
                                          exposure_monitor, risk_monitor)
        reconciliation_component = ReconciliationComponent(config, data_provider, execution_mode, position_monitor)
        position_update_handler = PositionUpdateHandler(config, data_provider, execution_mode,
                                                       position_monitor, exposure_monitor, risk_monitor, 
                                                       pnl_calculator, reconciliation_component)
        execution_manager = ExecutionManager(config, data_provider, execution_mode,
                                            position_update_handler, reconciliation_component)
        execution_interface_manager = ExecutionInterfaceManager(config, data_provider, execution_mode)
        event_logger = EventLogger(execution_mode)
        
        return {
            'position_monitor': position_monitor,
            'exposure_monitor': exposure_monitor,
            'risk_monitor': risk_monitor,
            'pnl_calculator': pnl_calculator,
            'strategy_manager': strategy_manager,
            'reconciliation_component': reconciliation_component,
            'position_update_handler': position_update_handler,
            'execution_manager': execution_manager,
            'execution_interface_manager': execution_interface_manager,
            'event_logger': event_logger
        }
```

## Live Trading Service Example
```python
class LiveTradingService:
    def __init__(self, global_config: Dict):
        self.global_config = global_config  # Immutable, validated at startup
    
    async def start_live_trading(self, request: LiveTradingRequest) -> str:
        # 1. Slice config for mode (never modifies global_config)
        config_slice = self._slice_config(request.strategy_name)
        
        # 2. Apply overrides to slice
        if request.config_overrides:
            config_slice = self._apply_overrides(config_slice, request.config_overrides)
        
        # 3. Create fresh DataProvider
        data_provider = DataProviderFactory.create('live', config_slice)
        
        # 4. Create fresh components with references
        components = self._initialize_components(config_slice, data_provider, 'live')
        
        # 5. Run with fresh instances
        engine = EventDrivenStrategyEngine(config_slice, 'live', 
                                          data_provider, components)
        task = asyncio.create_task(self._execute_live_trading(engine, request))
        self.running_strategies[request.request_id] = task
        
        return request.request_id
```

## Benefits
1. **Isolation**: Requests can't interfere with each other
2. **Config Safety**: Global config never modified, always pristine
3. **Override Support**: Per-request config changes without global impact
4. **Memory Management**: Fresh instances prevent memory leaks
5. **Concurrency**: Multiple requests can run simultaneously
6. **Debugging**: Each request has isolated state for troubleshooting

## Anti-Patterns to Avoid
```python
# WRONG - Reusing instances across requests
class BacktestService:
    def __init__(self):
        self.data_provider = DataProvider()  # Shared across requests
        self.components = {}  # Shared across requests
    
    async def run_backtest(self, request):
        # Reuses same instances - state pollution risk
        results = self.engine.run_backtest(request.start_date, request.end_date)

# WRONG - Modifying global config
def _apply_overrides(self, config_slice, overrides):
    self.global_config.update(overrides)  # Modifies global config

# WRONG - Caching components
def _initialize_components(self, config, data_provider, execution_mode):
    if not hasattr(self, '_cached_components'):
        self._cached_components = self._create_components(...)  # Cached across requests
    return self._cached_components

# CORRECT - Fresh instances per request
async def run_backtest(self, request):
    config_slice = self._slice_config(request.strategy_name)  # Fresh slice
    data_provider = DataProviderFactory.create('backtest', config_slice)  # Fresh instance
    components = self._initialize_components(config_slice, data_provider, 'backtest')  # Fresh instances
    engine = EventDrivenStrategyEngine(config_slice, 'backtest', data_provider, components)  # Fresh engine
```

## Integration with Other Patterns
- **Reference-Based Architecture**: Fresh references created per request
- **Shared Clock Pattern**: Fresh data_provider with mode-specific data
- **Mode-Aware Behavior**: Components initialized with correct execution_mode
- **Synchronous Execution**: Fresh instances enable clean synchronous execution
