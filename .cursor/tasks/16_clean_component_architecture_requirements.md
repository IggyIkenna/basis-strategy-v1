# CLEAN COMPONENT ARCHITECTURE REQUIREMENTS

## OVERVIEW
Components must be designed to be naturally clean without needing state clearing or resetting. The need to "clear state" indicates architectural problems that should be fixed at the root cause.

## CRITICAL REQUIREMENTS

### 1. Naturally Clean Component Design
- **No state clearing**: Components should not need to clear or reset their state
- **Proper initialization**: Components should initialize with correct state from the start
- **Single instance**: Each component should be one instance per basis strategy instance
- **Clean lifecycle**: Components should have a clean, predictable lifecycle

### 2. Root Cause Fixing
- **No masking**: Don't use "clean state" hacks to mask architectural problems
- **Identify root cause**: If state needs clearing, identify why and fix the root cause
- **Proper architecture**: Design components to work correctly without state manipulation
- **Clean separation**: Ensure proper separation of concerns between components

### 3. Component State Management
- **Initialization**: Components should initialize with correct state from the start
- **State persistence**: Components should maintain state correctly across runs
- **No resetting**: Components should not need to reset their state
- **Clean transitions**: State transitions should be clean and predictable

## FORBIDDEN PRACTICES

### ❌ State Clearing to Mask Problems
```python
# ❌ WRONG: Clearing state to mask architectural problems
class PositionMonitor:
    def initialize(self):
        # Clear all balances before initializing capital to ensure clean state
        for token in self._token_monitor.wallet:
            self._token_monitor.wallet[token] = 0.0
        logger.info(f"Position Monitor: Cleared all wallet balances for fresh start")
```

### ❌ Using "Clean State" Hacks
```python
# ❌ WRONG: Using "clean state" hacks instead of fixing root causes
class Component:
    def reset_state(self):
        # This masks the real problem - why does state need to be reset?
        self.state = {}
        self.initialized = False
    
    def clear_all_data(self):
        # This suggests the component wasn't designed properly
        self.data = {}
        self.cache = {}
        self.history = []
```

### ❌ Multiple Component Instances
```python
# ❌ WRONG: Multiple instances of same component
class StrategyManager:
    def __init__(self):
        self.position_monitor = PositionMonitor(config)  # Instance 1

class ExecutionManager:
    def __init__(self):
        self.position_monitor = PositionMonitor(config)  # Instance 2 (WRONG!)
```

## REQUIRED IMPLEMENTATION

### ✅ Naturally Clean Component Design
```python
class PositionMonitor:
    """Naturally clean position monitor that doesn't need state clearing."""
    
    def __init__(self, config, data_provider):
        self.config = config
        self.data_provider = data_provider
        # Initialize with correct state from the start
        self.wallet_balances = self._initialize_wallet_balances()
        self.initialized = True
    
    def _initialize_wallet_balances(self):
        """Initialize with proper state, don't clear later."""
        return {token: 0.0 for token in self.config.get('supported_tokens', [])}
    
    def update_balances(self, new_balances):
        """Update balances without clearing existing state."""
        for token, balance in new_balances.items():
            if token in self.wallet_balances:
                self.wallet_balances[token] = balance
```

### ✅ Proper Component Lifecycle
```python
class Component:
    """Component with proper lifecycle that doesn't need state clearing."""
    
    def __init__(self, config, data_provider):
        self.config = config
        self.data_provider = data_provider
        # Initialize with correct state from the start
        self.state = self._initialize_state()
        self.initialized = True
    
    def _initialize_state(self):
        """Initialize with proper state, don't reset later."""
        return self.config.get('initial_state', {})
    
    def update_state(self, new_state):
        """Update state without clearing existing state."""
        self.state.update(new_state)
```

### ✅ Single Instance Pattern
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
        # All components share the same instances and are naturally clean
```

## ROOT CAUSE ANALYSIS

### Why Components Need State Clearing
If a component needs state clearing, it usually indicates:

1. **Multiple instances**: Component is being created multiple times
2. **Poor initialization**: Component isn't initialized with correct state
3. **State persistence issues**: Component state isn't managed properly
4. **Architectural problems**: Component design is flawed

### How to Fix Root Causes

#### 1. Fix Multiple Instances
```python
# ❌ WRONG: Multiple instances
class StrategyManager:
    def __init__(self):
        self.position_monitor = PositionMonitor(config)  # Instance 1

class ExecutionManager:
    def __init__(self):
        self.position_monitor = PositionMonitor(config)  # Instance 2

# ✅ CORRECT: Single instance
class ComponentManager:
    def __init__(self):
        self.position_monitor = PositionMonitor(config)  # Single instance
    
    def get_position_monitor(self):
        return self.position_monitor  # Always returns same instance
```

#### 2. Fix Poor Initialization
```python
# ❌ WRONG: Poor initialization
class PositionMonitor:
    def __init__(self):
        self.wallet_balances = {}  # Empty, needs clearing later
    
    def initialize(self):
        # Clear all balances before initializing capital
        for token in self._token_monitor.wallet:
            self._token_monitor.wallet[token] = 0.0

# ✅ CORRECT: Proper initialization
class PositionMonitor:
    def __init__(self, config, data_provider):
        self.config = config
        self.data_provider = data_provider
        # Initialize with correct state from the start
        self.wallet_balances = self._initialize_wallet_balances()
    
    def _initialize_wallet_balances(self):
        return {token: 0.0 for token in self.config.get('supported_tokens', [])}
```

#### 3. Fix State Persistence Issues
```python
# ❌ WRONG: State persistence issues
class Component:
    def __init__(self):
        self.state = {}
        self.initialized = False
    
    def reset_state(self):
        self.state = {}
        self.initialized = False

# ✅ CORRECT: Proper state persistence
class Component:
    def __init__(self, config, data_provider):
        self.config = config
        self.data_provider = data_provider
        # Initialize with correct state from the start
        self.state = self._initialize_state()
        self.initialized = True
    
    def _initialize_state(self):
        return self.config.get('initial_state', {})
```

## VALIDATION REQUIREMENTS

### Component Design Validation
- [ ] Component is naturally clean without needing state clearing
- [ ] Component initializes with correct state from the start
- [ ] Component is single instance per basis strategy instance
- [ ] Component has clean, predictable lifecycle
- [ ] No state clearing or resetting methods

### Architecture Validation
- [ ] No multiple instances of same component
- [ ] Proper component initialization
- [ ] Correct state persistence
- [ ] Clean separation of concerns
- [ ] Root causes identified and fixed

### State Management Validation
- [ ] State is properly initialized
- [ ] State transitions are clean and predictable
- [ ] No state clearing or resetting needed
- [ ] State persistence works correctly
- [ ] Component lifecycle is clean

## IMPLEMENTATION CHECKLIST

### Design Phase
- [ ] Identify components that need state clearing
- [ ] Analyze why state clearing is needed
- [ ] Design components to be naturally clean
- [ ] Plan proper component initialization

### Implementation Phase
- [ ] Remove state clearing methods
- [ ] Fix component initialization
- [ ] Ensure single instance pattern
- [ ] Implement proper state management

### Testing Phase
- [ ] Test that components are naturally clean
- [ ] Test that no state clearing is needed
- [ ] Test that components work correctly
- [ ] Test that state persistence works

### Validation Phase
- [ ] Verify components are naturally clean
- [ ] Verify no state clearing is needed
- [ ] Verify single instance pattern works
- [ ] Verify proper state management

## SUCCESS CRITERIA
- [ ] All components are naturally clean without needing state clearing
- [ ] No state clearing or resetting methods exist
- [ ] All components initialize with correct state from the start
- [ ] All components are single instance per basis strategy instance
- [ ] Root causes of state clearing needs are identified and fixed
- [ ] System architecture is clean and maintainable
- [ ] Component lifecycle is predictable and clean
- [ ] State management is proper and consistent

## FORBIDDEN PRACTICES
- ❌ Clearing/resetting component state to mask architectural problems
- ❌ Using "clean state" hacks instead of fixing root causes
- ❌ Having components that need to be "cleared" between runs
- ❌ Creating multiple instances of the same component
- ❌ Poor component initialization

## REQUIRED PRACTICES
- ✅ Design components to be naturally clean without needing state clearing
- ✅ Fix root causes instead of using "clean state" hacks
- ✅ Ensure components are properly initialized with correct state from the start
- ✅ Use single instance pattern for all components
- ✅ Implement proper state management and persistence

