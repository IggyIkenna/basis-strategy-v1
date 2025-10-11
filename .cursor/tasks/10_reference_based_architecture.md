# FIX REFERENCE-BASED ARCHITECTURE GAPS

## OVERVIEW
Implement proper reference-based architecture where components store references in `__init__` and never pass them as runtime parameters. Components should never create their own instances of shared resources.

**Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 1 (Reference-Based Architecture Pattern)  
**Reference**: `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-003 (Reference-Based Architecture)  
**Reference**: `docs/IMPLEMENTATION_GAP_REPORT.md` - Component gap analysis

## CRITICAL REQUIREMENTS

### 1. Store References in __init__
- **All Components**: Store shared resources as references during initialization
- **Never Pass as Runtime Parameters**: Never pass config, data_provider, or other components as method parameters
- **Never Create Own Instances**: Components must never create their own instances of shared resources

### 2. Shared Resource Management
- **Single Config Instance**: All components share the same config instance
- **Single Data Provider**: All components share the same data provider instance
- **Component References**: Components store references to other components at initialization

## AFFECTED AREAS

### Multiple Components
- Components that may pass references as runtime parameters
- Components that may create their own instances
- Components that don't properly store references in `__init__`

### Event-Driven Strategy Engine
- `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py:1-20`
- Components may not properly implement reference-based pattern

## IMPLEMENTATION REQUIREMENTS

### 1. Reference-Based Component Design
- **Store References in __init__**: All components store shared resources as references during initialization
- **Never Pass as Runtime Parameters**: Never pass config, data_provider, or other components as method parameters
- **Never Create Own Instances**: Components must never create their own instances of shared resources
- **Component Reference Management**: Components store references to other components at initialization

**Implementation Details**: See `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` Section 1 for complete reference-based architecture patterns and component initialization requirements.

### 2. Component Initialization Pattern
- **Event-Driven Strategy Engine**: Initialize components with proper reference passing
- **Shared Resource Management**: Single config and data provider instances across all components
- **Component Dependencies**: Proper dependency injection and reference management
            position_monitor=self.position_monitor
        )
        
        self.risk_monitor = RiskMonitor(
            config=self.config,
            data_provider=self.data_provider,
            position_monitor=self.position_monitor,
            exposure_monitor=self.exposure_monitor
        )
```

### 3. Never Create Own Instances
```python
# ❌ WRONG: Creating own instances
class Component:
    def __init__(self):
        self.config = load_config()  # Creating own instance
        self.data_provider = DataProvider(self.config)  # Creating own instance
    
    def some_method(self):
        position_monitor = PositionMonitor(self.config)  # Creating own instance

# ✅ CORRECT: Use provided references
class Component:
    def __init__(self, config, data_provider, position_monitor):
        self.config = config  # Use provided reference
        self.data_provider = data_provider  # Use provided reference
        self.position_monitor = position_monitor  # Use provided reference
    
    def some_method(self):
        # Use stored reference
        position = self.position_monitor.get_current_position()
```

### 4. Method Parameter Patterns
```python
# ❌ WRONG: Passing references as method parameters
def update_state(self, config, data_provider, position_monitor, timestamp):
    market_data = data_provider.get_data(timestamp)
    position = position_monitor.get_current_position()

# ✅ CORRECT: Use stored references
def update_state(self, timestamp, trigger_source, **kwargs):
    market_data = self.data_provider.get_data(timestamp)
    position = self.position_monitor.get_current_position()
```

## COMPONENT REFERENCE PATTERNS

### 1. Core Component References
All components should store these references in `__init__`:
```python
def __init__(self, config, data_provider, **component_refs):
    # Core references
    self.config = config
    self.data_provider = data_provider
    self.execution_mode = execution_mode
    
    # Component references
    self.position_monitor = component_refs.get('position_monitor')
    self.exposure_monitor = component_refs.get('exposure_monitor')
    self.risk_monitor = component_refs.get('risk_monitor')
    self.pnl_calculator = component_refs.get('pnl_calculator')
    self.strategy_manager = component_refs.get('strategy_manager')
    self.event_logger = component_refs.get('event_logger')
    self.results_store = component_refs.get('results_store')
```

### 2. Component-Specific References
Different components may need different references:
```python
# Position Monitor - minimal references
def __init__(self, config, data_provider, event_logger):
    self.config = config
    self.data_provider = data_provider
    self.event_logger = event_logger

# Risk Monitor - needs position and exposure monitors
def __init__(self, config, data_provider, position_monitor, exposure_monitor):
    self.config = config
    self.data_provider = data_provider
    self.position_monitor = position_monitor
    self.exposure_monitor = exposure_monitor
```

## VALIDATION REQUIREMENTS

### Reference Storage Validation
- [ ] All components store references in `__init__`
- [ ] No references passed as runtime parameters
- [ ] Components never create their own instances
- [ ] All shared resources accessed via stored references

### Component Initialization Validation
- [ ] Single config instance shared across all components
- [ ] Single data provider instance shared across all components
- [ ] Component references properly stored at initialization
- [ ] No duplicate instances of shared resources

### Method Parameter Validation
- [ ] No config passed as method parameters
- [ ] No data_provider passed as method parameters
- [ ] No component references passed as method parameters
- [ ] All method parameters are data/state, not references

## TESTING REQUIREMENTS

### Unit Tests
- [ ] Test components store references in `__init__`
- [ ] Test no references passed as runtime parameters
- [ ] Test components use stored references
- [ ] Test no own instance creation

### Integration Tests
- [ ] Test single config instance across components
- [ ] Test single data provider instance across components
- [ ] Test component reference sharing
- [ ] Test no duplicate resource instances

## SUCCESS CRITERIA
- [ ] All components store references in `__init__`
- [ ] No references passed as runtime parameters
- [ ] Components never create their own instances
- [ ] Single config instance shared across all components
- [ ] Single data provider instance shared across all components
- [ ] Component references properly stored at initialization
- [ ] All shared resources accessed via stored references
- [ ] ADR-003 compliance achieved

## IMPLEMENTATION CHECKLIST

### Phase 1: Audit Current Implementation
- [ ] Scan all components for reference passing patterns
- [ ] Identify components that create own instances
- [ ] List all reference-based architecture violations
- [ ] Categorize by component and severity

### Phase 2: Fix Component Initialization
- [ ] Update all components to store references in `__init__`
- [ ] Remove reference passing from method parameters
- [ ] Ensure single instances of shared resources
- [ ] Test component initialization

### Phase 3: Fix Method Parameters
- [ ] Remove config from method parameters
- [ ] Remove data_provider from method parameters
- [ ] Remove component references from method parameters
- [ ] Update method signatures

### Phase 4: Testing and Validation
- [ ] Run unit tests for all components
- [ ] Test reference sharing across components
- [ ] Verify single instance pattern
- [ ] Check for regressions

## RELATED TASKS
- `13_singleton_pattern_requirements.md` - Singleton pattern affects reference sharing
- `14_mode_agnostic_architecture_requirements.md` - Mode-agnostic components need proper references
- `10_tight_loop_architecture_requirements.md` - Tight loop architecture affects component execution
