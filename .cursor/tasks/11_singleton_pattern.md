# SINGLETON PATTERN REQUIREMENTS

## OVERVIEW
All components must use the singleton pattern to ensure single instances across the entire run, preventing data synchronization issues and ensuring consistent state management.

**Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 2 (Singleton Pattern)  
**Reference**: `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-003 (Reference-Based Architecture)  
**Reference**: `docs/specs/01_POSITION_MONITOR.md` - Component specification  
**Reference**: `docs/specs/02_EXPOSURE_MONITOR.md` - Component specification  
**Reference**: `docs/specs/03_RISK_MONITOR.md` - Component specification

## CRITICAL REQUIREMENTS

### 1. Single Instance Per Component
- **Each component**: Must be a SINGLE instance across the entire run
- **No duplication**: Never initialize the same component twice in different places
- **Shared state**: All components share the same state and data
- **Consistent behavior**: All parts of the system see the same component state

### 2. Shared Configuration
- **Single config instance**: All components must share the SAME config instance
- **Consistent configuration**: All components see the same configuration values
- **No config duplication**: Never load configuration multiple times
- **Synchronized settings**: All components use the same settings

### 3. Shared Data Provider
- **Single data provider**: All components must share the SAME data provider instance
- **Consistent data**: All components see the same data
- **No data duplication**: Never create multiple data provider instances
- **Synchronized data flows**: All components use the same data source

## IMPLEMENTATION PATTERNS

### Pattern 1: Component Manager (Recommended)
```python
class ComponentManager:
    """Manages all component instances as singletons."""
    
    def __init__(self):
        # Single instances created once
        self.config = load_config()
        self.data_provider = DataProvider(self.config)
        self.position_monitor = PositionMonitor(self.config, self.data_provider)
        self.exposure_monitor = ExposureMonitor(self.config, self.data_provider)
        self.risk_monitor = RiskMonitor(self.config, self.data_provider)
        self.pnl_monitor = PnLMonitor(self.config, self.data_provider)
        self.strategy_manager = StrategyManager(self.config, self.data_provider)
        self.cex_execution_manager = CEXExecutionManager(self.config, self.data_provider)
        self.onchain_execution_manager = OnChainExecutionManager(self.config, self.data_provider)
    
    def get_component(self, component_name: str):
        """Get a component instance."""
        return getattr(self, component_name, None)
```

### Pattern 2: Dependency Injection
```python
class MyComponent:
    """Component that receives shared instances via dependency injection."""
    
    def __init__(self, config, data_provider, position_monitor):
        self.config = config  # Shared config instance
        self.data_provider = data_provider  # Shared data provider
        self.position_monitor = position_monitor  # Shared position monitor
```

### Pattern 3: Service Locator
```python
class ServiceLocator:
    """Service locator pattern for component access."""
    
    _instance = None
    _components = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_component(self, name: str, component):
        """Register a component instance."""
        self._components[name] = component
    
    def get_component(self, name: str):
        """Get a component instance."""
        return self._components.get(name)
```

## FORBIDDEN PRACTICES

### ❌ Multiple Component Instances
```python
# ❌ WRONG: Multiple instances of same component
position_monitor_1 = PositionMonitor(config)
position_monitor_2 = PositionMonitor(config)  # Different instance!

# ❌ WRONG: Creating components in different places
class StrategyManager:
    def __init__(self):
        self.position_monitor = PositionMonitor(config)  # Instance 1

class ExecutionManager:
    def __init__(self):
        self.position_monitor = PositionMonitor(config)  # Instance 2 (WRONG!)
```

### ❌ Multiple Config Instances
```python
# ❌ WRONG: Multiple config instances
config_1 = load_config()
config_2 = load_config()  # Different instance!

# ❌ WRONG: Loading config in multiple places
class ComponentA:
    def __init__(self):
        self.config = load_config()  # Instance 1

class ComponentB:
    def __init__(self):
        self.config = load_config()  # Instance 2 (WRONG!)
```

### ❌ Multiple Data Provider Instances
```python
# ❌ WRONG: Multiple data provider instances
data_provider_1 = DataProvider(config)
data_provider_2 = DataProvider(config)  # Different instance!

# ❌ WRONG: Creating data providers in multiple places
class ComponentA:
    def __init__(self):
        self.data_provider = DataProvider(config)  # Instance 1

class ComponentB:
    def __init__(self):
        self.data_provider = DataProvider(config)  # Instance 2 (WRONG!)
```

## CORRECT IMPLEMENTATION

### ✅ Single Instance Pattern
```python
# ✅ CORRECT: Single instance pattern
class ComponentManager:
    def __init__(self):
        # Create single instances once
        self.config = load_config()
        self.data_provider = DataProvider(self.config)
        self.position_monitor = PositionMonitor(self.config, self.data_provider)
        self.exposure_monitor = ExposureMonitor(self.config, self.data_provider)
        self.risk_monitor = RiskMonitor(self.config, self.data_provider)
        self.pnl_monitor = PnLMonitor(self.config, self.data_provider)
    
    def get_position_monitor(self):
        return self.position_monitor  # Always returns same instance
    
    def get_data_provider(self):
        return self.data_provider  # Always returns same instance
```

### ✅ Dependency Injection
```python
# ✅ CORRECT: Dependency injection
class StrategyManager:
    def __init__(self, config, data_provider, position_monitor):
        self.config = config  # Shared instance
        self.data_provider = data_provider  # Shared instance
        self.position_monitor = position_monitor  # Shared instance

class ExecutionManager:
    def __init__(self, config, data_provider, position_monitor):
        self.config = config  # Same shared instance
        self.data_provider = data_provider  # Same shared instance
        self.position_monitor = position_monitor  # Same shared instance
```

## DATA SYNCHRONIZATION BENEFITS

### Consistent State
- **Single source of truth**: All components see the same data
- **No state conflicts**: No conflicting data between components
- **Synchronized updates**: All components see updates immediately
- **Consistent behavior**: All components behave consistently

### Performance Benefits
- **Memory efficiency**: No duplicate data storage
- **Faster access**: Shared instances reduce initialization overhead
- **Reduced complexity**: Simpler data flow management
- **Better caching**: Shared instances enable better caching

### Debugging Benefits
- **Easier debugging**: Single instance to debug
- **Consistent logs**: All components log to same instance
- **Clear data flow**: Easy to trace data flow through single instances
- **Reduced complexity**: Simpler system architecture

## VALIDATION REQUIREMENTS

### Component Instance Validation
- [ ] Each component is a single instance across the entire run
- [ ] No duplicate component initialization
- [ ] All components share the same config instance
- [ ] All components share the same data provider instance
- [ ] Data flows are synchronized between all components

### Architecture Validation
- [ ] Component manager pattern implemented
- [ ] Dependency injection used where appropriate
- [ ] Service locator pattern used if needed
- [ ] No hardcoded component creation
- [ ] All components access shared instances

### Data Flow Validation
- [ ] All components see the same data
- [ ] No data synchronization issues
- [ ] Consistent state across all components
- [ ] Proper data flow through component chain
- [ ] No duplicate data storage

## IMPLEMENTATION CHECKLIST

### Design Phase
- [ ] Identify all components that need singleton pattern
- [ ] Design component manager or service locator
- [ ] Plan dependency injection strategy
- [ ] Ensure all components can access shared instances

### Implementation Phase
- [ ] Implement component manager or service locator
- [ ] Update all components to use shared instances
- [ ] Remove duplicate component initialization
- [ ] Implement proper dependency injection

### Testing Phase
- [ ] Test that all components use single instances
- [ ] Test data synchronization between components
- [ ] Test that no duplicate instances are created
- [ ] Test that shared state is consistent

### Validation Phase
- [ ] Verify single instance pattern is working
- [ ] Verify data synchronization is working
- [ ] Verify no duplicate instances are created
- [ ] Verify all components share the same data

## SUCCESS CRITERIA
- [ ] All components use single instances across the entire run
- [ ] All components share the same config instance
- [ ] All components share the same data provider instance
- [ ] No duplicate component initialization
- [ ] Data flows are synchronized between all components
- [ ] System architecture is simplified and more maintainable

