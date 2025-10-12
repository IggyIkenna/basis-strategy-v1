# [Component Name] Component Specification

**⚠️ TEMPLATE FILE**: This is a template with placeholder links. Replace all bracketed placeholders with actual values.

**Last Reviewed**: [Date]

## Purpose
[One sentence describing what this component does using config-driven, mode-agnostic language if applicable]

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles including config-driven architecture
- **Strategy Specifications**: [MODES.md](../MODES.md) - Canonical strategy mode definitions
- **Configuration Guide**: [19_CONFIGURATION.md](specs/19_CONFIGURATION.md) - Complete config schemas with component_config
- **Implementation Patterns**: [CODE_STRUCTURE_PATTERNS.md](../CODE_STRUCTURE_PATTERNS.md) - Complete implementation patterns
- **Component Index**: [COMPONENT_SPECS_INDEX.md](../COMPONENT_SPECS_INDEX.md) - All 20 components (11 core + 9 supporting)

## Responsibilities
1. **[Primary Responsibility]**: [Config-driven description if mode-agnostic, or mode-specific description with explanation]
2. **[Secondary Responsibility]**: [Description]
3. **[Additional Responsibilities]**: [Description]
4. **Execution Mode Aware**: Same logic for backtest and live modes (only data source differs)

## State
- state_var_1: Type (description)
- state_var_2: Type (description)
- last_action_timestamp: pd.Timestamp
- component_history: List[Dict] (for debugging)

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- component_ref_1: ComponentType (reference, call method_name())
- component_ref_2: ComponentType (reference, call method_name())
- data_provider: BaseDataProvider (reference, query with timestamps)
- config: Dict (reference, never modified)
- execution_mode: str (BASIS_EXECUTION_MODE)

These references are stored in __init__ and used throughout component lifecycle.
Components NEVER receive these as method parameters during runtime.

## Configuration Parameters

### **Config-Driven Architecture**

**Is this component mode-agnostic or mode-specific?**
- **Mode-Agnostic**: Uses component_config to determine behavior (no mode checks)
- **Mode-Specific**: Naturally requires strategy-specific logic (e.g., Strategy Manager)

**For mode-agnostic components**:
- Behavior determined by component_config parameters
- Graceful handling when data unavailable (return None/0)
- No hardcoded mode-specific if/else logic
- See: CODE_STRUCTURE_PATTERNS.md for implementation patterns
- ADRs: ADR-052, ADR-053, ADR-054

**For mode-specific components**:
- Inherit from base class (e.g., BaseStrategyManager)
- Mode-specific logic in subclass
- Use factory pattern for creation
- See: 5A_STRATEGY_FACTORY.md for pattern

The [Component Name] is **[mode-agnostic|mode-specific]** and uses `component_config.[component_name]` from the mode configuration:

```yaml
component_config:
  [component_name]:
    [param_1]: [value]  # [Description]
    [param_2]: [value]  # [Description]
    [param_3]:
      [nested_param_1]: [value]
      [nested_param_2]: [value]
```

### **[Config Parameter] Definitions**

| Parameter | Description | Valid Values | Required | Default |
|-----------|-------------|--------------|----------|---------|
| `[param_1]` | [Description] | [Valid values] | Yes/No | [Default value] |
| `[param_2]` | [Description] | [Valid values] | Yes/No | [Default value] |

### **[Component Behavior] by Strategy Mode**

| Mode | [Behavior Column 1] | [Behavior Column 2] |
|------|---------------------|---------------------|
| **Pure Lending** | [Value] | [Value] |
| **BTC Basis** | [Value] | [Value] |
| **ETH Basis** | [Value] | [Value] |
| **ETH Staking Only** | [Value] | [Value] |
| **ETH Leveraged** | [Value] | [Value] |
| **USDT MN No Leverage** | [Value] | [Value] |
| **USDT Market Neutral** | [Value] | [Value] |

**Key Insight**: The component [does what] **only for [config items]** specified in config. Un[configured items] are [how handled gracefully].

**Cross-Reference**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas with full examples for all 7 modes

## Environment Variables

**Validation**: This section is validated by `test_env_config_usage_sync_quality_gates.py` to ensure 100% sync with actual code usage.

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
[List component-specific env vars or state "None"]

### Environment Variable Access Pattern
```python
def __init__(self, ...):
    # Read env vars ONCE at initialization
    self.execution_mode = os.getenv('BASIS_EXECUTION_MODE', 'backtest')
    # NEVER read env vars during runtime loops
```

### Behavior NOT Determinable from Environment Variables
- [Behavior 1] ([why it's hardcoded])
- [Behavior 2] ([why it's hardcoded])

## Config Fields Used

**Validation**: This section is validated by `test_env_config_usage_sync_quality_gates.py` to ensure 100% sync with actual code usage.

### Universal Config (All Components)
- `mode`: str - e.g., 'eth_basis', 'pure_lending' (NOT 'mode')
- `share_class`: str - 'USDT' | 'ETH'
- `asset`: str - 'USDT' | 'ETH' | 'BTC'
- `initial_capital`: float - Starting capital

### Component-Specific Config
- `[config_field_1]`: [Type] - [Description]
  - **Usage**: [How it's used]
  - **Default**: [Default value]
  - **Validation**: [Validation rules]

### Config Access Pattern
```python
def method_name(self, timestamp: pd.Timestamp, trigger_source: str):
    # Read config fields (NEVER modify)
    [param] = self.config.get('[config_field]', [default_value])
```

### Behavior NOT Determinable from Config
- [Behavior 1] ([why it's hardcoded])
- [Behavior 2] ([why it's hardcoded])

## Data Provider Queries

**Validation**: This section is validated by `test_env_config_usage_sync_quality_gates.py` to ensure 100% sync with actual code usage.

### Data Types Requested
`data = self.data_provider.get_data(timestamp)`

#### Market Data
- `prices`: Dict[str, float] - Token prices in USD
  - **Tokens needed**: [List tokens]
  - **Update frequency**: [Frequency]
  - **Usage**: [How used]

- `rates`: Dict[str, float] - Rates (funding, lending, etc.)
  - **Rates needed**: [List rates]
  - **Update frequency**: [Frequency]
  - **Usage**: [How used]

#### Protocol Data
- `aave_indexes`: Dict[str, float] - AAVE liquidity indexes
  - **Tokens needed**: [List if applicable]
  - **Update frequency**: [Frequency]
  - **Usage**: [How used]

- `oracle_prices`: Dict[str, float] - LST oracle prices
  - **Tokens needed**: [List if applicable]
  - **Update frequency**: [Frequency]
  - **Usage**: [How used]

- `perp_prices`: Dict[str, float] - Perpetual mark prices
  - **Instruments needed**: [List if applicable]
  - **Update frequency**: [Frequency]
  - **Usage**: [How used]

#### Staking Data (if applicable)
- `base_rewards`: Dict[str, float] - Base staking rewards
- `eigen_rewards`: Dict[str, Any] - EIGEN reward distributions
- `ethfi_rewards`: Dict[str, Any] - ETHFI reward distributions

#### Execution Data
- `gas_costs`: Dict[str, float] - Ethereum gas costs
- `execution_costs`: Dict[str, float] - Execution fee models

### Query Pattern
```python
def method_name(self, timestamp: pd.Timestamp, trigger_source: str):
    data = self.data_provider.get_data(timestamp)
    prices = data['market_data']['prices']
    rates = data['market_data']['rates']
    # ... use standardized data structure
```

### Data NOT Available from DataProvider
[List any data not from DataProvider, or state "None - all data comes from DataProvider"]

## Core Methods

### primary_method(timestamp: pd.Timestamp, trigger_source: str, **kwargs)
[Main entry point description]

**Parameters**:
- timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
- trigger_source: 'full_loop' | 'tight_loop' | 'manual'
- **kwargs: [Additional parameters if any]

**Behavior**:
1. Query data using: data = self.data_provider.get_data(timestamp)
2. Access component refs: [access pattern]
3. [Process data]
4. NO async/await: Synchronous execution only

**Returns**:
- None (state updated in place) OR Dict ([return structure])

### [secondary_method]() -> [ReturnType]
[Description]

**Returns**:
- [Return type and structure]

## Data Access Pattern

### Query Pattern
```python
def method_name(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs):
    # Query data with timestamp (data <= timestamp guaranteed)
    market_data = self.data_provider.get_data(timestamp)
    
    # Access other components via references
    [component_data] = self.[component_ref].[getter_method]()
    
    # Process using standardized data structures
    result = self._process([params])
    
    # Update internal state
    self.[state_var] = result
    self.last_[action]_timestamp = timestamp
```

**NEVER** pass market_data or component refs as parameters between components.
**NEVER** cache market_data across timestamps.

## Mode-Aware Behavior

### Backtest Mode
```python
def [method](self, ...):
    if self.execution_mode == 'backtest':
        # Use historical/simulated data
        return self._[backtest_specific_logic](...)
```

### Live Mode
```python
def [method](self, ...):
    elif self.execution_mode == 'live':
        # Use real-time data/APIs
        return self._[live_specific_logic](...)
```

## **MODE-AGNOSTIC IMPLEMENTATION EXAMPLE**

### **Complete Config-Driven [Component Name]**

```python
class [ComponentName]:
    """[Mode-agnostic|Mode-specific] [component purpose] using config-driven behavior"""
    
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                 [component_ref_1]: [ComponentType], [component_ref_2]: [ComponentType]):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Store component references
        self.[component_ref_1] = [component_ref_1]
        self.[component_ref_2] = [component_ref_2]
        
        # Extract config-driven settings
        self.[component]_config = config.get('component_config', {}).get('[component_name]', {})
        self.[config_param_1] = self.[component]_config.get('[param_1]', [])
        self.[config_param_2] = self.[component]_config.get('[param_2]', {})
        
        # Initialize component-specific state
        self.[state_var] = {}
        self.last_[action]_timestamp = None
        self.[component]_history = []
        
        # Validate config
        self._validate_[component]_config()
    
    def _validate_[component]_config(self):
        """Validate [component] configuration"""
        if not self.[config_param_1]:
            raise ValueError("[component].[param_1] cannot be empty")
        
        valid_[param_1]_values = [
            '[value_1]', '[value_2]', '[value_3]'
        ]
        
        for item in self.[config_param_1]:
            if item not in valid_[param_1]_values:
                raise ValueError(f"Invalid [param_1]: {item}")
    
    def [main_method](self, [params]) -> Dict:
        """
        [Main method description].
        MODE-AGNOSTIC - works for all strategy modes.
        """
        results = {}
        
        # Process only configured items
        for item in self.[config_param_1]:
            try:
                if item == '[value_1]':
                    if '[required_data]' in [data_source].get('[data_category]', {}):
                        results[item] = self._calculate_[value_1](...)
                    else:
                        results[item] = None  # Data not available - gracefully skip
                
                elif item == '[value_2]':
                    if '[required_data]' in [data_source].get('[data_category]', {}):
                        results[item] = self._calculate_[value_2](...)
                    else:
                        results[item] = None
                
                # ... etc (NO mode-specific logic!)
            
            except Exception as e:
                logger.error(f"Error calculating {item}: {e}")
                results[item] = None
        
        # Apply limits/validation from config
        [validation_results] = self._apply_[validation]([results], self.[config_param_2])
        
        return {
            '[result_key_1]': results,
            '[result_key_2]': [validation_results],
            'enabled_[items]': self.[config_param_1],
            'timestamp': [timestamp]
        }
    
    def _calculate_[specific_item](self, [params]) -> [ReturnType]:
        """
        Calculate [specific item].
        Includes graceful data handling.
        """
        # Check data availability first
        if '[required_data]' not in [data_source].get('[data_category]', {}):
            return None  # OR return 0.0 for numeric results
        
        # Perform calculation
        [calculation_logic]
        
        return [result]
```

### **Key Benefits of Mode-Agnostic Implementation**

1. **No Mode-Specific Logic**: Component has zero hardcoded mode checks
2. **Config-Driven Behavior**: All behavior determined by `[config_params]`
3. **Graceful Data Handling**: Skips calculations when data is unavailable
4. **Easy Extension**: Adding new [items] doesn't require mode-specific changes
5. **Self-Documenting**: [Config params] clearly defined in config

### **Individual [Calculation] Methods**

Each [item type] has its own calculation method that can be called independently:

```python
def _calculate_[item_1](self, [params]) -> [ReturnType]:
    """Calculate [item_1] with graceful data handling"""
    # Check data availability
    if '[required_data]' not in [data_source].get('[category]', {}):
        return None  # Gracefully skip if data unavailable
    
    # Extract required data
    [data_var] = [data_source]['[category]']['[required_data]']
    
    # Perform calculation
    [result] = [calculation_formula]
    
    return [result]

def _calculate_[item_2](self, [params]) -> [ReturnType]:
    """Calculate [item_2] with graceful data handling"""
    # Similar pattern with data availability check
    pass
```

### **Config Validation in Component Factory**

```python
class ComponentFactory:
    """Creates components with config validation"""
    
    @staticmethod
    def create_[component_name](config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                                [component_ref_1]: [ComponentType],
                                [component_ref_2]: [ComponentType]) -> [ComponentClass]:
        """Create [Component Name] with config validation"""
        # Extract component-specific config
        [component]_config = config.get('component_config', {}).get('[component_name]', {})
        
        # Validate required config
        required_fields = ['[field_1]', '[field_2]', '[field_3]']
        for field in required_fields:
            if field not in [component]_config:
                raise ValueError(f"Missing required config for [component_name]: {field}")
        
        # Validate [specific validation]
        valid_[param] = ['[value_1]', '[value_2]', '[value_3]']
        for item in [component]_config.get('[param]', []):
            if item not in valid_[param]:
                raise ValueError(f"Invalid [param]: {item}")
        
        # Create component
        return [ComponentClass](config, data_provider, execution_mode, [component_ref_1], [component_ref_2])
```

---

## Event Logging Requirements

**Validation**: This section is validated by `test_env_config_usage_sync_quality_gates.py` to ensure 100% sync with actual code usage.

### Component Event Log File
**Separate log file** for this component's events:
- **File**: `logs/events/[component_name]_events.jsonl`
- **Format**: JSON Lines (one event per line)
- **Rotation**: Daily rotation, keep 30 days
- **Purpose**: Component-specific audit trail

### Event Logging via EventLogger
All events logged through centralized EventLogger:

```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='[event_type]',
    component='[ComponentName]',
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
    component='[ComponentName]',
    data={
        'execution_mode': self.execution_mode,
        '[component_specific_field]': [value],
        'config_hash': hash(str(self.config))
    }
)
```

#### 2. State Updates (Every update_state() Call)
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='state_update',
    component='[ComponentName]',
    data={
        'trigger_source': trigger_source,
        '[metric_1]': self.[state_var].get('[metric_1]', 0),
        '[metric_2]': self.[state_var].get('[metric_2]', 0),
        'processing_time_ms': processing_time
    }
)
```

#### 3. Error Events
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='error',
    component='[ComponentName]',
    data={
        'error_code': '[ERR-001]',
        'error_message': str(e),
        'stack_trace': traceback.format_exc(),
        'error_severity': 'CRITICAL|HIGH|MEDIUM|LOW'
    }
)
```

#### 4. Component-Specific Critical Events
- **[Event 1]**: [When this happens]
- **[Event 2]**: [When this happens]
- **[Event 3]**: [When this happens]

### Event Retention & Output Formats

#### Dual Logging Approach
**Both formats are used**:
1. **JSON Lines (Iterative)**: Write events to component-specific JSONL files during execution
   - **Purpose**: Real-time monitoring during backtest runs
   - **Location**: `logs/events/[component_name]_events.jsonl`
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

### Component Error Code Prefix: [XXX]
All [ComponentName] errors use the `[XXX]` prefix.

### Error Code Registry
**Source**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`

All error codes registered with:
- **code**: Unique error code
- **component**: Component name
- **severity**: CRITICAL | HIGH | MEDIUM | LOW
- **message**: Human-readable error message
- **resolution**: How to resolve

### Component Error Codes

#### [XXX]-001: [Error Name] ([Severity])
**Description**: [What this error means]
**Cause**: [What causes this error]
**Recovery**: [How to recover]
```python
raise ComponentError(
    error_code='[XXX]-001',
    message='[Error message]',
    component='[ComponentName]',
    severity='[SEVERITY]'
)
```

#### [XXX]-002: [Error Name] ([Severity])
**Description**: [What this error means]
**Cause**: [What causes this error]
**Recovery**: [How to recover]

#### [XXX]-003: [Error Name] ([Severity])
**Description**: [What this error means]
**Cause**: [What causes this error]
**Recovery**: [How to recover]

### Structured Error Handling Pattern

#### Error Raising
```python
from backend.src.basis_strategy_v1.core.error_codes.exceptions import ComponentError

try:
    result = self._[calculation_method]([params])
except Exception as e:
    # Log error event
    self.event_logger.log_event(
        timestamp=timestamp,
        event_type='error',
        component='[ComponentName]',
        data={
            'error_code': '[XXX]-001',
            'error_message': str(e),
            'stack_trace': traceback.format_exc()
        }
    )
    
    # Raise structured error
    raise ComponentError(
        error_code='[XXX]-001',
        message=f'[ComponentName] failed: {str(e)}',
        component='[ComponentName]',
        severity='[SEVERITY]',
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
        component_name='[ComponentName]',
        checker=self._health_check
    )

def _health_check(self) -> Dict:
    """Component-specific health check."""
    return {
        'status': 'healthy' | 'degraded' | 'unhealthy',
        'last_update': self.last_[action]_timestamp,
        'errors': self.recent_errors[-10:],  # Last 10 errors
        'metrics': {
            'update_count': self.update_count,
            'avg_processing_time_ms': self.avg_processing_time,
            'error_rate': self.error_count / max(self.update_count, 1),
            '[component_metric_1]': self.[state_var].get('[metric_1]', 0),
            '[component_metric_2]': self.[state_var].get('[metric_2]', 0)
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
- [ ] All 19 sections present and complete
- [ ] Environment Variables section documents system-level and component-specific variables
- [ ] Config Fields Used section documents universal and component-specific config
- [ ] Data Provider Queries section documents market data and protocol data queries
- [ ] Event Logging Requirements section documents component-specific JSONL file
- [ ] Event Logging Requirements section documents dual logging (JSONL + CSV)
- [ ] Error Codes section has structured error handling pattern
- [ ] Error Codes section references health integration
- [ ] Health integration documented with UnifiedHealthManager
- [ ] Component-specific log file documented (`logs/events/[component_name]_events.jsonl`)
- [ ] MODE-AGNOSTIC IMPLEMENTATION EXAMPLE section added with complete code structure

### Section Order Validation
- [ ] Title and Purpose (section 1)
- [ ] Canonical Sources (section 2)
- [ ] Responsibilities (section 3)
- [ ] State (section 4)
- [ ] Component References (Set at Init) (section 5)
- [ ] Configuration Parameters (section 6)
- [ ] Environment Variables (section 7)
- [ ] Config Fields Used (section 8)
- [ ] Data Provider Queries (section 9)
- [ ] Core Methods (section 10)
- [ ] Data Access Pattern (section 11)
- [ ] Mode-Aware Behavior (section 12)
- [ ] MODE-AGNOSTIC IMPLEMENTATION EXAMPLE (section 13) ⭐ NEW
- [ ] Event Logging Requirements (section 14)
- [ ] Error Codes (section 15)
- [ ] Quality Gates (section 16)
- [ ] Integration Points (section 17)
- [ ] Current Implementation Status (section 18)
- [ ] Related Documentation (section 19)

### Implementation Status
- [ ] Backend implementation exists and matches spec
- [ ] All required methods implemented
- [ ] Error handling follows structured pattern
- [ ] Health integration implemented
- [ ] Event logging implemented
- [ ] Config-driven behavior implemented

## Integration Points

### Called BY
- [Component 1] ([trigger type]): [component].[method](timestamp, '[trigger]')
- [Component 2] ([trigger type]): [component].[method](timestamp, '[trigger]')

### Calls TO
- [component_ref].[method]() - [what data/functionality]
- data_provider.get_data(timestamp) - data queries

### Communication
- Direct method calls ONLY
- NO event publishing
- NO Redis/message queues
- NO async/await in internal methods

## Current Implementation Status

**Overall Completion**: [XX]% ([Brief status])

### **Core Functionality Status**
- ✅ **Working**: [List working features]
- ⚠️ **Partial**: [List partial features with what's missing]
- ❌ **Missing**: [List missing features]
- 🔄 **Refactoring Needed**: [List refactoring needs]

### **Architecture Compliance Status**
- ✅ **COMPLIANT**: Component follows canonical architectural principles
  - **Reference-Based Architecture**: Components receive references at init, never pass as runtime parameters
  - **Shared Clock Pattern**: All methods receive timestamp from EventDrivenStrategyEngine
  - **Request Isolation Pattern**: Fresh instances per backtest/live request
  - **Synchronous Component Execution**: Internal methods are synchronous, async only for I/O operations
  - **Mode-Aware Behavior**: Uses BASIS_EXECUTION_MODE for conditional logic
  - **[Additional Compliance]**: [Specific compliance notes]

### **Implementation Status**
- **High Priority**:
  - [High priority items]
- **Medium Priority**:
  - [Medium priority items]
- **Low Priority**:
  - [Low priority items]

### **Quality Gate Status**
- **Current Status**: [PASS|PARTIAL|FAIL]
- **Failing Tests**: [List failing tests or "None"]
- **Requirements**: [What's needed to pass]
- **Integration**: [Integration status with quality gate system]

### **Task Completion Status**
- **Related Tasks**: 
  - [Link to related task files]
- **Completion**: [XX]% complete overall
- **Blockers**: [List blockers or "None"]
- **Next Steps**: [What needs to be done next]

## Related Documentation

### **Architecture Patterns**
- [Reference-Based Architecture](../REFERENCE_ARCHITECTURE_CANONICAL.md)
- [Shared Clock Pattern](../SHARED_CLOCK_PATTERN.md)
- [Request Isolation Pattern](../REQUEST_ISOLATION_PATTERN.md)
- [Config-Driven Architecture](../REFERENCE_ARCHITECTURE_CANONICAL.md) Section II

### **Component Integration**
- [[Component 1] Specification]([file].md) - [How it relates]
- [[Component 2] Specification]([file].md) - [How it relates]
- [[Component 3] Specification]([file].md) - [How it relates]

### **Configuration and Implementation**
- [Configuration Guide](19_CONFIGURATION.md) - Complete config schemas for all 7 modes
- [Code Structure Patterns](../CODE_STRUCTURE_PATTERNS.md) - Implementation patterns
- [Data Provider Specification](09_DATA_PROVIDER.md) - Data access patterns
- [Event Logger Specification](08_EVENT_LOGGER.md) - Event logging integration

---

**Status**: Specification [complete|in progress|needs review] ✅


