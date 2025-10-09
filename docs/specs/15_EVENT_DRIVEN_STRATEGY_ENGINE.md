# Component Spec: Event-Driven Strategy Engine 🚀

**Component**: Event-Driven Strategy Engine  
**Responsibility**: Orchestrate all 9 components in dependency order with tight loop architecture  
**Priority**: ⭐⭐⭐ CRITICAL (Core orchestration engine)  
**Backend File**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py` ✅ **IMPLEMENTED**  
**Last Reviewed**: January 6, 2025  
**Status**: ✅ Aligned with canonical sources (.cursor/tasks/ + MODES.md)

---

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [CANONICAL_ARCHITECTURAL_PRINCIPLES.md](../CANONICAL_ARCHITECTURAL_PRINCIPLES.md) - Consolidated from all .cursor/tasks/
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Task Specifications**: `.cursor/tasks/` - Individual task specifications

---

## 🎯 **Purpose**

Wire together all 9 components in a coordinated manner following the **tight loop architecture** and **singleton pattern** requirements.

**Key Principles**:
- **Component Orchestration**: Initialize all 9 components in dependency order
- **Dependency Injection**: Proper component wiring with shared config and data provider
- **Tight Loop Architecture**: Sequential component execution triggered by position updates
- **Event-Driven Execution**: Components respond to events and trigger downstream components
- **Mode-Agnostic**: Same orchestration for backtest and live modes
- **Health Integration**: Automatic registration with unified health manager

---

## 🏗️ **Architecture**

### **Component Orchestration**

The engine orchestrates these 9 components in dependency order:

1. **Position Monitor** → Foundation component (others depend on it)
2. **Event Logger** → Logging infrastructure
3. **Exposure Monitor** → Depends on Position Monitor + Data Provider
4. **Risk Monitor** → Depends on Position Monitor + Exposure Monitor + Data Provider
5. **P&L Calculator** → Depends on Position Monitor + Exposure Monitor + Risk Monitor
6. **Strategy Manager** → Depends on all monitoring components
7. **CEX Execution Manager** → Depends on Strategy Manager
8. **OnChain Execution Manager** → Depends on Strategy Manager
9. **Data Provider** → Shared across all components

### **Component Specifications**

Each component has detailed specifications:
- **Position Monitor**: [01_POSITION_MONITOR.md](01_POSITION_MONITOR.md)
- **Exposure Monitor**: [02_EXPOSURE_MONITOR.md](02_EXPOSURE_MONITOR.md)
- **Risk Monitor**: [03_RISK_MONITOR.md](03_RISK_MONITOR.md)
- **P&L Calculator**: [04_PNL_CALCULATOR.md](04_PNL_CALCULATOR.md)
- **Strategy Manager**: [05_STRATEGY_MANAGER.md](05_STRATEGY_MANAGER.md)
- **CEX Execution Manager**: [06_CEX_EXECUTION_MANAGER.md](06_CEX_EXECUTION_MANAGER.md)
- **OnChain Execution Manager**: [07_ONCHAIN_EXECUTION_MANAGER.md](07_ONCHAIN_EXECUTION_MANAGER.md)
- **Execution Interfaces**: [08_EXECUTION_INTERFACES.md](08_EXECUTION_INTERFACES.md)
- **Data Provider**: [09_DATA_PROVIDER.md](09_DATA_PROVIDER.md)

---

## 🔄 **Tight Loop Architecture**

### **Mandatory Sequence**

Following [CANONICAL_ARCHITECTURAL_PRINCIPLES.md](../CANONICAL_ARCHITECTURAL_PRINCIPLES.md) section 4:

```
position_monitor → exposure_monitor → risk_monitor → pnl_monitor
```

**Execution Flow Options**:
- **Strategy Manager Path**: position_monitor → exposure_monitor → risk_monitor → pnl_monitor → strategy → execution_managers
- **Tight Loop Path**: position_monitor → exposure_monitor → risk_monitor → pnl_monitor → execution_managers

### **Position Update Handler**

The engine implements a `PositionUpdateHandler` that triggers the tight loop:

```python
class PositionUpdateHandler:
    """Tight loop trigger mechanism for position updates."""
    
    async def handle_position_update(self, trigger_event: str, changes: Dict[str, Any]):
        """Trigger tight loop after position update."""
        # 1. Update position monitor
        await self.position_monitor.update_position(trigger_event, changes)
        
        # 2. Trigger tight loop sequence
        await self._execute_tight_loop()
    
    async def _execute_tight_loop(self):
        """Execute tight loop: position → exposure → risk → P&L."""
        # Get current position
        position = await self.position_monitor.get_snapshot()
        
        # Calculate exposure
        exposure = await self.exposure_monitor.calculate_exposure(position, self.current_timestamp)
        
        # Assess risk
        risk = await self.risk_monitor.assess_risk(exposure, self.current_timestamp)
        
        # Calculate P&L
        pnl = await self.pnl_calculator.calculate_pnl(exposure, risk, self.current_timestamp)
```

---

## 🔧 **Component Initialization**

### **Singleton Pattern Requirements**

Following [13_singleton_pattern_requirements.md](../../.cursor/tasks/13_singleton_pattern_requirements.md):

#### **Single Instance Per Component**
- **Each component**: Must be a SINGLE instance across the entire run
- **No duplication**: Never initialize the same component twice in different places
- **Shared state**: All components share the same state and data

#### **Shared Configuration and Data Provider**
- **Single config instance**: All components must share the SAME config instance
- **Single data provider**: All components must share the SAME data provider instance
- **Synchronized data flows**: All components use the same data source

### **Dependency Injection Pattern**

```python
class EventDrivenStrategyEngine:
    def __init__(self, config: Dict[str, Any], execution_mode: str, 
                 data_provider, initial_capital: float, share_class: str):
        """Initialize with injected parameters (no defaults)."""
        
        # Validate required parameters (FAIL FAST)
        if not initial_capital or initial_capital <= 0:
            raise ValueError(f"Invalid initial_capital: {initial_capital}. Must be > 0.")
        
        if share_class not in ['USDT', 'ETH']:
            raise ValueError(f"Invalid share_class: {share_class}. Must be 'USDT' or 'ETH'.")
        
        # Store shared instances (SINGLETON PATTERN)
        self.config = config  # Single config instance shared across all components
        self.data_provider = data_provider  # Single data provider instance shared across all components
        
        # Initialize components in dependency order
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all components with proper dependency injection and singleton pattern."""
        
        # 1. Position Monitor (foundational) - SINGLE INSTANCE
        self.position_monitor = PositionMonitor(
            config=self.config,  # Shared config instance
            execution_mode=self.execution_mode,
            initial_capital=self.initial_capital,
            share_class=self.share_class,
            data_provider=self.data_provider  # Shared data provider instance
        )
        
        # 2. Event Logger - SINGLE INSTANCE
        self.event_logger = EventLogger(execution_mode=self.execution_mode)
        
        # 3. Exposure Monitor (depends on position_monitor + data_provider) - SINGLE INSTANCE
        self.exposure_monitor = ExposureMonitor(
            config=self.config,  # Shared config instance
            share_class=self.share_class,
            position_monitor=self.position_monitor,  # Shared position monitor instance
            data_provider=self.data_provider  # Shared data provider instance
        )
        
        # 4. Risk Monitor (depends on position_monitor + exposure_monitor + data_provider) - SINGLE INSTANCE
        self.risk_monitor = RiskMonitor(
            config=self.config,  # Shared config instance
            position_monitor=self.position_monitor,  # Shared position monitor instance
            exposure_monitor=self.exposure_monitor,  # Shared exposure monitor instance
            data_provider=self.data_provider  # Shared data provider instance
        )
        
        # 5. P&L Calculator (depends on all monitoring components) - SINGLE INSTANCE
        self.pnl_calculator = PnLCalculator(
            config=self.config,  # Shared config instance
            position_monitor=self.position_monitor,  # Shared position monitor instance
            exposure_monitor=self.exposure_monitor,  # Shared exposure monitor instance
            risk_monitor=self.risk_monitor,  # Shared risk monitor instance
            data_provider=self.data_provider  # Shared data provider instance
        )
        
        # 6. Strategy Manager (depends on all monitoring components) - SINGLE INSTANCE
        self.strategy_manager = StrategyManager(
            config=self.config,  # Shared config instance
            position_monitor=self.position_monitor,  # Shared position monitor instance
            exposure_monitor=self.exposure_monitor,  # Shared exposure monitor instance
            risk_monitor=self.risk_monitor,  # Shared risk monitor instance
            pnl_calculator=self.pnl_calculator,  # Shared P&L calculator instance
            data_provider=self.data_provider  # Shared data provider instance
        )
        
        # 7. Execution Interfaces (depends on strategy manager) - SINGLE INSTANCES
        self.execution_interfaces = ExecutionInterfaceFactory.create_all_interfaces(
            execution_mode=self.execution_mode,
            config=self.config  # Shared config instance
        )
        
        # Set dependencies for execution interfaces (all shared instances)
        ExecutionInterfaceFactory.set_interface_dependencies(
            interfaces=self.execution_interfaces,
            position_monitor=self.position_monitor,  # Shared position monitor instance
            event_logger=self.event_logger,  # Shared event logger instance
            data_provider=self.data_provider  # Shared data provider instance
        )
        
        # 8. Position Update Handler (tight loop management) - SINGLE INSTANCE
        self.position_update_handler = PositionUpdateHandler(
            position_monitor=self.position_monitor,  # Shared position monitor instance
            exposure_monitor=self.exposure_monitor,  # Shared exposure monitor instance
            risk_monitor=self.risk_monitor,  # Shared risk monitor instance
            pnl_calculator=self.pnl_calculator  # Shared P&L calculator instance
        )
```

### **Mode-Agnostic Architecture Requirements**

Following [14_mode_agnostic_architecture_requirements.md](../../.cursor/tasks/14_mode_agnostic_architecture_requirements.md):

#### **P&L Monitor Must Be Mode-Agnostic**
- **Single logic**: P&L monitor must work for both backtest and live modes
- **No mode-specific code**: No different logic per mode
- **Universal balance calculation**: Calculate balances across all venues and asset types
- **Mode-independent**: Should not care whether data comes from backtest simulation or live APIs

#### **Centralized Utility Methods**
- **Liquidity index**: Must be centralized method, not in execution interfaces
- **Market prices**: Must be centralized method for all token/currency conversions
- **Shared access**: All components that need these utilities must use the same methods
- **Global data states**: All utilities must access the same global data states

### **Clean Component Architecture Requirements**

Following [16_clean_component_architecture_requirements.md](../../.cursor/tasks/16_clean_component_architecture_requirements.md):

#### **Naturally Clean Component Design**
- **No state clearing**: Components should not need to clear or reset their state
- **Proper initialization**: Components should initialize with correct state from the start
- **Single instance**: Each component should be one instance per basis strategy instance
- **Clean lifecycle**: Components should have a clean, predictable lifecycle

#### **Root Cause Fixing**
- **No masking**: Don't use "clean state" hacks to mask architectural problems
- **Identify root cause**: If state needs clearing, identify why and fix the root cause
- **Proper architecture**: Design components to work correctly without state manipulation

### **Generic vs Mode-Specific Architecture**

Following [18_generic_vs_mode_specific_architecture.md](../../.cursor/tasks/18_generic_vs_mode_specific_architecture.md):

#### **Generic Components (Mode-Agnostic)**
- **Position Monitor**: Generic monitoring tool, not strategy mode specific
- **P&L Attribution**: Generic attribution logic across all modes
- **Exposure Monitor**: Generic exposure calculation using config parameters
- **Risk Monitor**: Generic risk assessment using config parameters
- **Utility Manager**: Generic utility methods

#### **Mode-Specific Components (Naturally Strategy Mode Specific)**
- **Strategy Manager**: Strategy mode specific by nature
- **Data Subscriptions**: Heavily strategy mode dependent
- **Execution Interfaces**: Strategy mode aware for data subscriptions

### **Venue-Based Execution Architecture**

Following [VENUE_ARCHITECTURE.md](../VENUE_ARCHITECTURE.md):

#### **Venue-Based Execution Manager**
- **Action Type to Venue Mapping**: Execution manager maps action types from strategy manager to appropriate venues
- **Strategy Manager Defines Actions**: Strategy manager defines action types, not specific venues/interfaces
- **Environment-Specific Clients**: Each venue needs clients with live, testnet, and simulation modes
- **Mode-Agnostic Components**: Position monitor, exposure monitor, risk monitor, P&L monitor work across all venues

#### **Execution Interface Factory Integration**
- **Venue Client Initialization**: Create venue clients based on environment and execution mode
- **Environment Variable Integration**: Use BASIS_ENVIRONMENT and BASIS_EXECUTION_MODE for venue configuration
- **Backtest Mode Simulation**: Dummy venue calls for backtest mode
- **Live Mode Execution**: Real API calls for live mode

---

## 🔄 **Execution Modes**

### **Backtest Mode**

```python
async def run_backtest(self, start_date: str, end_date: str) -> Dict[str, Any]:
    """Execute backtest with historical data."""
    
    # Initialize backtest state
    self.current_timestamp = pd.Timestamp(start_date)
    end_timestamp = pd.Timestamp(end_date)
    
    # Event loop: process each timestamp
    while self.current_timestamp <= end_timestamp:
        # Get market data for current timestamp
        market_data = await self.data_provider.get_market_data(self.current_timestamp)
        
        # Execute strategy decision
        decision = await self.strategy_manager.make_decision(
            timestamp=self.current_timestamp,
            market_data=market_data
        )
        
        # Execute decision if any
        if decision:
            await self.execute_decision(decision, self.current_timestamp, market_data)
        
        # Advance to next timestamp
        self.current_timestamp += pd.Timedelta(hours=1)
```

### **Live Mode**

```python
async def run_live(self):
    """Execute live trading with real-time data."""
    
    self.is_running = True
    
    while self.is_running:
        try:
            # Get current market data
            market_data = await self.data_provider.get_live_market_data()
            
            # Execute strategy decision
            decision = await self.strategy_manager.make_decision(
                timestamp=pd.Timestamp.now(),
                market_data=market_data
            )
            
            # Execute decision if any
            if decision:
                await self.execute_decision(decision, pd.Timestamp.now(), market_data)
            
            # Wait before next iteration
            await asyncio.sleep(60)  # 1 minute intervals
            
        except Exception as e:
            logger.error(f"Live trading error: {e}")
            # Continue execution (don't halt on non-critical errors)
```

---

## 🏥 **Health Integration**

### **Automatic Registration**

The engine automatically registers all components with the unified health manager:

```python
def _register_health_checkers(self):
    """Register all components with the unified health check system."""
    from ..health import unified_health_manager
    
    unified_health_manager.register_component(
        "position_monitor", 
        PositionMonitorHealthChecker(self.position_monitor)
    )
    unified_health_manager.register_component(
        "data_provider", 
        DataProviderHealthChecker(self.data_provider)
    )
    # ... register all other components
```

### **Health Status Reporting**

```python
async def get_status(self) -> Dict[str, Any]:
    """Get current status of all components with health information."""
    from ..health import unified_health_manager
    health_report = await unified_health_manager.check_detailed_health()
    
    return {
        'mode': self.mode,
        'share_class': self.share_class,
        'execution_mode': self.execution_mode,
        'health': {
            'overall_status': health_report['status'],
            'timestamp': health_report['timestamp'],
            'summary': health_report['summary'],
            'components': health_report['components']
        },
        'current_timestamp': self.current_timestamp,
        'is_running': self.is_running
    }
```

**Health System Details**: See [SYSTEM_HEALTH.md](SYSTEM_HEALTH.md) for comprehensive health monitoring.

---

## ⚠️ **Error Handling**

### **Backtest Mode (Fail-Fast)**

```python
try:
    # Component initialization
    self._initialize_components()
except Exception as e:
    logger.error(f"Component initialization failed: {e}")
    raise ValueError(f"Engine initialization failed: {e}")

try:
    # Strategy execution
    await self.execute_decision(decision, timestamp, market_data)
except Exception as e:
    logger.error(f"Strategy execution failed: {e}")
    raise ValueError(f"Strategy execution failed: {e}")
```

### **Live Mode (Retry Logic)**

```python
async def execute_decision_with_retry(self, decision, timestamp, market_data, max_attempts=3):
    """Execute decision with retry logic for live mode."""
    
    for attempt in range(max_attempts):
        try:
            await self.execute_decision(decision, timestamp, market_data)
            return  # Success
        except Exception as e:
            if attempt < max_attempts - 1:
                wait_time = 5 * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Execution failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Execution failed after {max_attempts} attempts: {e}")
                # Continue execution (don't halt live trading)
```

---

## 🚀 **Usage Examples**

### **Backtest Execution**

```python
# Initialize engine
engine = EventDrivenStrategyEngine(
    config=config,
    execution_mode='backtest',
    data_provider=data_provider,
    initial_capital=100000.0,
    share_class='USDT'
)

# Run backtest
results = await engine.run_backtest(
    start_date='2024-01-01',
    end_date='2024-12-31'
)

# Get final status
status = await engine.get_status()
print(f"Backtest completed: {status['health']['overall_status']}")
```

### **Live Trading Execution**

```python
# Initialize engine
engine = EventDrivenStrategyEngine(
    config=config,
    execution_mode='live',
    data_provider=data_provider,
    initial_capital=100000.0,
    share_class='USDT'
)

# Start live trading
await engine.run_live()

# Monitor health
while True:
    status = await engine.get_status()
    if status['health']['overall_status'] != 'healthy':
        logger.warning(f"Engine health issue: {status['health']}")
    await asyncio.sleep(60)
```

### **Component Access**

```python
# Access individual components
position = await engine.position_monitor.get_snapshot()
exposure = await engine.exposure_monitor.calculate_exposure(position, timestamp)
risk = await engine.risk_monitor.assess_risk(exposure, timestamp)
pnl = await engine.pnl_calculator.calculate_pnl(exposure, risk, timestamp)

# Execute strategy decision
decision = await engine.strategy_manager.make_decision(timestamp, market_data)
if decision:
    await engine.execute_decision(decision, timestamp, market_data)
```

---

## 📋 **Implementation Status** ✅ **FULLY IMPLEMENTED**

- ✅ **Component Orchestration**: All 9 components initialized in dependency order
- ✅ **Dependency Injection**: Proper component wiring with shared config and data provider
- ✅ **Tight Loop Architecture**: PositionUpdateHandler triggers sequential component execution
- ✅ **Event-Driven Execution**: Components respond to events and trigger downstream components
- ✅ **Mode-Agnostic Design**: Same orchestration for backtest and live modes
- ✅ **Health Integration**: Automatic registration with unified health manager
- ✅ **Error Handling**: Fail-fast in backtest, retry logic in live mode
- ✅ **Singleton Pattern**: Single instance across entire run with shared config and data provider
- ✅ **No Hardcoded Values**: All configuration loaded from YAML files
- ✅ **Clean Component Architecture**: Components naturally clean without state clearing
- ✅ **Mode-Agnostic Architecture**: P&L monitor works for both modes, centralized utility methods
- ✅ **Generic vs Mode-Specific**: Generic components use config parameters, mode-specific components are naturally strategy mode specific
- ✅ **Venue-Based Execution**: Action type to venue mapping, environment-specific clients
- ✅ **Architecture Compliance**: All components follow canonical architectural principles

---

## 🎯 **Next Steps**

1. **Performance Optimization**: Component execution timing and memory usage
2. **Advanced Error Recovery**: Component-level error recovery mechanisms
3. **Dynamic Component Loading**: Runtime component addition/removal
4. **Cross-Component Communication**: Enhanced event system for component coordination
5. **Monitoring Integration**: Real-time performance metrics and alerting

## 🔍 **Quality Gate Validation**

Following [17_quality_gate_validation_requirements.md](../../.cursor/tasks/17_quality_gate_validation_requirements.md):

### **Mandatory Quality Gate Validation**
**BEFORE CONSIDERING TASK COMPLETE**, you MUST:

1. **Run Component Quality Gates**:
   ```bash
   python scripts/test_pure_lending_quality_gates.py
   python scripts/test_btc_basis_quality_gates.py
   ```

2. **Verify Architecture Compliance**:
   - Singleton pattern: All components use single instances with shared config and data provider
   - Mode-agnostic: P&L monitor works for both backtest and live modes
   - Clean component architecture: Components naturally clean without state clearing
   - Generic vs mode-specific: Generic components use config parameters, mode-specific components are naturally strategy mode specific
   - Venue-based execution: Action type to venue mapping works correctly

3. **Verify Component Integration**:
   - All 9 components initialize in dependency order
   - Tight loop architecture works correctly
   - Event-driven execution triggers downstream components
   - Health integration works correctly

4. **Document Results**:
   - Architecture compliance status
   - Component integration results
   - Any remaining issues or limitations

**DO NOT PROCEED TO NEXT TASK** until quality gates validate the event-driven strategy engine is working correctly.

---

**Status**: Event-Driven Strategy Engine is complete and fully operational! 🎉

*Last Updated: January 6, 2025*
