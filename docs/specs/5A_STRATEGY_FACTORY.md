# Strategy Factory Component Specification

## Purpose
Factory for creating strategy instances based on mode with proper dependency injection and tight loop architecture integration.

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](../MODES.md) - Canonical strategy mode definitions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides
- **Config-Driven Architecture**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Mode-agnostic architecture guide
- **Code Structures**: [CODE_STRUCTURE_PATTERNS.md](../CODE_STRUCTURE_PATTERNS.md) - Complete implementation patterns

## Responsibilities
1. Create strategy instances based on mode configuration
2. Provide proper dependency injection for strategy components
3. Integrate with tight loop architecture
4. Support all 7 strategy modes with inheritance-based architecture
5. Validate strategy mode configuration

## State
- strategy_map: Dict[str, Type[BaseStrategyManager]] (strategy class mapping)
- created_strategies: Dict[str, BaseStrategyManager] (created strategy instances)
- mode_validation: Dict[str, bool] (mode validation results)

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- config: Dict (reference, never modified)
- execution_mode: str (BASIS_EXECUTION_MODE)

These references are stored in __init__ and used throughout component lifecycle.
Components NEVER receive these as method parameters during runtime.

## Configuration Parameters

### **Config-Driven Architecture**

The Strategy Factory is **mode-agnostic** and uses `component_config.strategy_factory` from the mode configuration:

```yaml
component_config:
  strategy_factory:
    timeout: 30           # Strategy creation timeout in seconds
    max_retries: 3        # Maximum retry attempts
    validation_strict: true # Strict mode validation
```

### **Configuration Parameter Definitions**

| Parameter | Description | Valid Values | Required | Default |
|-----------|-------------|--------------|----------|---------|
| `timeout` | Strategy creation timeout | 1-300 seconds | No | 30 |
| `max_retries` | Maximum retry attempts | 1-10 | No | 3 |
| `validation_strict` | Strict mode validation | true/false | No | true |

### **Strategy Factory Behavior by Strategy Mode**

| Mode | Timeout | Max Retries | Validation |
|------|---------|-------------|------------|
| **Pure Lending** | 30s | 3 | Strict |
| **BTC Basis** | 30s | 3 | Strict |
| **ETH Basis** | 30s | 3 | Strict |
| **ETH Staking Only** | 30s | 3 | Strict |
| **ETH Leveraged** | 30s | 3 | Strict |
| **USDT MN No Leverage** | 30s | 3 | Strict |
| **USDT Market Neutral** | 30s | 3 | Strict |

**Key Insight**: The Strategy Factory uses **identical configuration** for all strategy modes. No mode-specific configuration needed.

**Cross-Reference**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas with full examples for all 7 modes

## Environment Variables

### System-Level Variables
- **BASIS_EXECUTION_MODE**: 'backtest' | 'live' (determines strategy behavior)
- **BASIS_LOG_LEVEL**: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' (logging level)
- **BASIS_DATA_DIR**: Path to data directory (for backtest mode)

### Component-Specific Variables
- **STRATEGY_FACTORY_TIMEOUT**: Strategy creation timeout in seconds (default: 30)
- **STRATEGY_FACTORY_MAX_RETRIES**: Maximum retry attempts for strategy creation (default: 3)

## Config Fields Used

### Universal Config (All Components)
- **execution_mode**: 'backtest' | 'live' (from strategy mode slice)
- **log_level**: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' (from strategy mode slice)

### Component-Specific Config
- **component_config.strategy_factory.timeout**: int - Strategy creation timeout
  - **Usage**: Determines how long to wait for strategy creation
  - **Default**: 30 (seconds)
  - **Validation**: Must be > 0 and < 300
  - **Used in**: Strategy creation timeout handling

- **component_config.strategy_factory.max_retries**: int - Maximum retry attempts
  - **Usage**: Determines retry behavior for failed strategy creation
  - **Default**: 3
  - **Validation**: Must be > 0 and < 10
  - **Used in**: Strategy creation retry logic

  - **Usage**: Determines whether to perform strict validation of strategy mode
  - **Default**: true
  - **Used in**: Strategy mode validation

## Config-Driven Behavior

The Strategy Factory is **mode-agnostic** by design - it creates strategy instances without mode-specific logic:

**Component Configuration** (from `component_config.strategy_factory`):
```yaml
component_config:
  strategy_factory:
    # Strategy Factory is inherently mode-agnostic
    # Creates strategy instances regardless of strategy mode
    # No mode-specific configuration needed
    timeout: 30           # Strategy creation timeout in seconds
    max_retries: 3        # Maximum retry attempts
    validation_strict: true # Strict mode validation
```

**Mode-Agnostic Strategy Creation**:
- Creates strategy instances based on mode configuration
- Same creation logic for all strategy modes
- No mode-specific if statements in strategy creation
- Uses config-driven timeout and retry settings

**Strategy Creation by Mode**:

**Pure Lending Mode**:
- Creates: `PureLendingStrategy` instance with AAVE USDT configuration
- Dependencies: risk_monitor, position_monitor, event_engine
- Same creation logic as other modes

**BTC Basis Mode**:
- Creates: `BTCBasisStrategy` instance with BTC spot/futures configuration
- Dependencies: risk_monitor, position_monitor, event_engine
- Same creation logic as other modes

**ETH Leveraged Mode**:
- Creates: `ETHLeveragedStrategy` instance with ETH/LST/AAVE configuration
- Dependencies: risk_monitor, position_monitor, event_engine
- Same creation logic as other modes

**Key Principle**: Strategy Factory is **purely creation** - it does NOT:
- Make mode-specific decisions about which strategies to create
- Handle strategy-specific creation logic
- Convert or transform configuration data
- Make business logic decisions

All creation logic is generic - it uses the strategy class mapping to create the appropriate strategy instance based on mode configuration, with each strategy handling mode-specific logic internally using inheritance-based architecture.

## Environment Variables

### System-Level Variables (Read at Initialization)
- `BASIS_EXECUTION_MODE`: backtest | live
  - **Usage**: Passed to created strategy instances
  - **Read at**: Factory creation time
  - **Affects**: Strategy behavior mode

- `BASIS_ENVIRONMENT`: dev | staging | production
  - **Usage**: Credential routing for strategies
  - **Read at**: Factory creation time
  - **Affects**: Which API keys strategies use

### Component-Specific Variables
- `STRATEGY_FACTORY_TIMEOUT`: Strategy creation timeout in seconds (default: 30)
- `STRATEGY_FACTORY_MAX_RETRIES`: Maximum retry attempts (default: 3)

### Environment Variable Access Pattern
```python
def __init__(self, ...):
    # Read env vars ONCE at initialization
    self.execution_mode = os.getenv('BASIS_EXECUTION_MODE', 'backtest')
    # NEVER read env vars during runtime loops
```

### Behavior NOT Determinable from Environment Variables
- Strategy class mapping (hard-coded STRATEGY_MAP)
- Dependency injection logic (hard-coded validation)
- Factory creation patterns (hard-coded algorithms)

## Config Fields Used

### Universal Config (All Components)
- `mode`: str - Strategy mode name (e.g., 'pure_lending', 'btc_basis')
- `share_class`: str - 'USDT' | 'ETH'
- `asset`: str - 'USDT' | 'ETH' | 'BTC'

### Component-Specific Config (from component_config.strategy_factory)
- `timeout`: int - Strategy creation timeout in seconds
  - **Usage**: Determines max wait time for strategy initialization
  - **Required**: No (default: 30)
  - **Validation**: Must be > 0 and < 300

- `max_retries`: int - Maximum retry attempts
  - **Usage**: Retry logic for failed strategy creation
  - **Required**: No (default: 3)
  - **Validation**: Must be > 0 and < 10

- `validation_strict`: bool - Strict validation mode
  - **Usage**: Fail-fast on configuration errors
  - **Required**: No (default: true)
  - **Validation**: Must be boolean

### Config Access Pattern
```python
def __init__(self, config: Dict, ...):
    # Extract config in __init__ (NEVER in methods)
    self.factory_config = config.get('component_config', {}).get('strategy_factory', {})
    self.timeout = self.factory_config.get('timeout', 30)
    self.max_retries = self.factory_config.get('max_retries', 3)
    self.validation_strict = self.factory_config.get('validation_strict', True)
```

### Behavior NOT Determinable from Config
- Strategy class mapping (hard-coded STRATEGY_MAP)
- Validation logic (hard-coded algorithms)
- Dependency injection patterns (hard-coded)

## Data Provider Queries

### Data Types Requested
N/A - StrategyFactory doesn't query DataProvider (it creates strategies that use DataProvider)

### Query Pattern
N/A - Factory doesn't access data

### Data NOT Available from DataProvider
All data - StrategyFactory is a pure factory component

## Core Methods

### create_strategy(mode: str, config: Dict, data_provider: BaseDataProvider, execution_mode: str, exposure_monitor: ExposureMonitor, risk_monitor: RiskMonitor) -> BaseStrategyManager
Create strategy instance based on mode.

**Parameters**:
- mode: Strategy mode name
- config: Complete configuration dictionary
- data_provider: Data provider instance
- execution_mode: 'backtest' or 'live'
- exposure_monitor: Exposure monitor instance
- risk_monitor: Risk monitor instance

**Returns**:
- BaseStrategyManager: Strategy instance for specified mode

### validate_mode(mode: str) -> bool
Validate that mode is supported.

**Parameters**:
- mode: Strategy mode name to validate

**Returns**:
- bool: True if mode supported, False otherwise

### get_available_modes() -> List[str]
Get list of available strategy modes.

**Returns**:
- List[str]: All supported mode names

## Data Access Pattern

Factory doesn't access data - it creates components that access data:

```python
@classmethod
def create_strategy(cls, mode: str, config: Dict, dependencies: Dict) -> BaseStrategyManager:
    # No data access - pure factory
    strategy_class = cls.STRATEGY_MAP[mode]
    return strategy_class(config, dependencies)
```

## Mode-Aware Behavior

### Backtest Mode
```python
def create_strategy(cls, mode: str, config: Dict, ...):
    # Same factory logic for backtest
    # Passes execution_mode='backtest' to created strategy
    return strategy_class(config, ..., execution_mode='backtest')
```

### Live Mode
```python
def create_strategy(cls, mode: str, config: Dict, ...):
    # Same factory logic for live
    # Passes execution_mode='live' to created strategy
    return strategy_class(config, ..., execution_mode='live')
```

**Key**: Factory logic identical - only passes different execution_mode parameter.

## **MODE-AGNOSTIC IMPLEMENTATION EXAMPLE**

### **Complete Strategy Factory Implementation**

```python
from typing import Dict, Any, List, Type
import logging

class StrategyFactory:
    """Factory for creating strategy instances based on mode with complete implementation"""
    
    # Complete strategy class mapping for all 7 modes
    STRATEGY_MAP: Dict[str, Type[BaseStrategyManager]] = {
        'pure_lending': PureLendingStrategy,
        'btc_basis': BTCBasisStrategy,
        'eth_basis': ETHBasisStrategy,
        'eth_staking_only': ETHStakingOnlyStrategy,
        'eth_leveraged': ETHLeveragedStrategy,
        'usdt_market_neutral_no_leverage': USDTMarketNeutralNoLeverageStrategy,
        'usdt_market_neutral': USDTMarketNeutralStrategy,
    }
    
    @classmethod
    def create_strategy(
        cls, 
        mode: str, 
        config: Dict[str, Any], 
        data_provider: BaseDataProvider,
        execution_mode: str,
        exposure_monitor: ExposureMonitor,
        risk_monitor: RiskMonitor
    ) -> BaseStrategyManager:
        """
        Create strategy instance based on mode with dependency injection.
        
        Parameters:
        - mode: Strategy mode name (e.g., 'pure_lending', 'btc_basis')
        - config: Complete configuration dictionary
        - data_provider: Data provider instance
        - execution_mode: 'backtest' or 'live'
        - exposure_monitor: Exposure monitor instance
        - risk_monitor: Risk monitor instance
        
        Returns:
        - BaseStrategyManager: Strategy instance for the specified mode
        
        Raises:
        - ValueError: If mode is not supported or dependencies are missing
        """
        # Validate mode
        if not cls.validate_mode(mode):
            raise ValueError(f"Unsupported strategy mode: {mode}")
        
        # Get strategy class
        strategy_class = cls.STRATEGY_MAP[mode]
        
        # Validate dependencies
        cls._validate_dependencies(
            data_provider, exposure_monitor, risk_monitor
        )
        
        # Create strategy instance with dependency injection
        try:
            strategy_instance = strategy_class(
                config=config,
                data_provider=data_provider,
                execution_mode=execution_mode,
                exposure_monitor=exposure_monitor,
                risk_monitor=risk_monitor
            )
            
            logging.info(f"Successfully created {mode} strategy instance")
            return strategy_instance
            
        except Exception as e:
            logging.error(f"Failed to create {mode} strategy instance: {e}")
            raise ValueError(f"Strategy creation failed for mode {mode}: {e}")
    
    @classmethod
    def validate_mode(cls, mode: str) -> bool:
        """
        Validate that mode is supported and strategy class exists.
        
        Parameters:
        - mode: Strategy mode name to validate
        
        Returns:
        - bool: True if mode is supported, False otherwise
        """
        if not mode:
            return False
        
        if mode not in cls.STRATEGY_MAP:
            logging.warning(f"Unknown strategy mode: {mode}")
            return False
        
        # Check if strategy class exists and is importable
        strategy_class = cls.STRATEGY_MAP[mode]
        if not strategy_class:
            logging.error(f"Strategy class not found for mode: {mode}")
            return False
        
        return True
    
    @classmethod
    def get_available_modes(cls) -> List[str]:
        """
        Get list of available strategy modes.
        
        Returns:
        - List[str]: List of all supported strategy mode names
        """
        return list(cls.STRATEGY_MAP.keys())
    
    @classmethod
    def get_strategy_info(cls, mode: str) -> Dict[str, Any]:
        """
        Get information about a specific strategy mode.
        
        Parameters:
        - mode: Strategy mode name
        
        Returns:
        - Dict[str, Any]: Strategy information including class, description, etc.
        """
        if not cls.validate_mode(mode):
            raise ValueError(f"Unknown strategy mode: {mode}")
        
        strategy_class = cls.STRATEGY_MAP[mode]
        
        return {
            'mode': mode,
            'class_name': strategy_class.__name__,
            'module': strategy_class.__module__,
            'description': strategy_class.__doc__ or f"Strategy for {mode} mode",
            'is_available': True
        }
    
    @classmethod
    def _validate_dependencies(
        cls,
        data_provider: BaseDataProvider,
        exposure_monitor: ExposureMonitor,
        risk_monitor: RiskMonitor
    ) -> None:
        """Validate dependencies (private method)."""
        """
        Validate that all required dependencies are available.
        
        Parameters:
        - data_provider: Data provider instance
        - exposure_monitor: Exposure monitor instance
        - risk_monitor: Risk monitor instance
        
        Raises:
        - ValueError: If any dependency is missing or invalid
        """
        if not data_provider:
            raise ValueError("data_provider is required")
        
        if not exposure_monitor:
            raise ValueError("exposure_monitor is required")
        
        if not risk_monitor:
            raise ValueError("risk_monitor is required")
        
        # Additional validation can be added here
        logging.debug("All strategy dependencies validated successfully")
    
    @classmethod
    def create_all_strategies(
        cls,
        config: Dict[str, Any],
        data_provider: BaseDataProvider,
        execution_mode: str,
        exposure_monitor: ExposureMonitor,
        risk_monitor: RiskMonitor
    ) -> Dict[str, BaseStrategyManager]:
        """
        Create all available strategy instances (for testing/debugging).
        
        Parameters:
        - config: Complete configuration dictionary
        - data_provider: Data provider instance
        - execution_mode: 'backtest' or 'live'
        - exposure_monitor: Exposure monitor instance
        - risk_monitor: Risk monitor instance
        
        Returns:
        - Dict[str, BaseStrategyManager]: Dictionary mapping mode names to strategy instances
        """
        strategies = {}
        
        for mode in cls.get_available_modes():
            try:
                strategies[mode] = cls.create_strategy(
                    mode=mode,
                    config=config,
                    data_provider=data_provider,
                    execution_mode=execution_mode,
                    exposure_monitor=exposure_monitor,
                    risk_monitor=risk_monitor
                )
            except Exception as e:
                logging.error(f"Failed to create strategy for mode {mode}: {e}")
                # Continue with other strategies
        
        return strategies
```

### **Integration with Event-Driven Strategy Engine**

```python
class EventDrivenStrategyEngine:
    """Event driven strategy engine with factory integration"""
    
    def __init__(self, config: Dict, execution_mode: str, data_provider: BaseDataProvider, components: Dict):
        self.config = config
        self.execution_mode = execution_mode
        self.data_provider = data_provider
        self.components = components
        
        # Create strategy using factory
        self.strategy_manager = StrategyFactory.create_strategy(
            mode=config['mode'],
            config=config,
            data_provider=data_provider,
            execution_mode=execution_mode,
            exposure_monitor=components['exposure_monitor'],
            risk_monitor=components['risk_monitor']
        )
    
    def run_backtest(self, start_date: str, end_date: str):
        """Run backtest with factory-created strategy"""
        timestamps = self.data_provider.get_timestamps(start_date, end_date)
        
        for timestamp in timestamps:
            # Strategy manager created by factory handles all strategy logic
            instruction_blocks = self.strategy_manager.update_state(timestamp, 'full_loop')
            
            # Process instruction blocks through execution manager
            if instruction_blocks:
                self.components['execution_manager'].execute_instructions(instruction_blocks)
```

### **Key Benefits of Complete Factory Implementation**

1. **Complete Mode Coverage**: All 7 strategy modes mapped and supported
2. **Dependency Injection**: Proper component references for all strategy instances
3. **Error Handling**: Comprehensive validation and error handling
4. **Mode Validation**: Ensures strategy modes are valid and supported
5. **Integration Ready**: Works seamlessly with Event-Driven Strategy Engine
6. **Extensible**: Easy to add new strategy modes by updating STRATEGY_MAP

### **Strategy Class Mapping (Complete)**

| Mode | Strategy Class | Description | Complexity |
|------|----------------|-------------|------------|
| **pure_lending** | `PureLendingStrategy` | AAVE USDT supply only | Simple |
| **btc_basis** | `BTCBasisStrategy` | BTC spot + perp hedge | Medium |
| **eth_basis** | `ETHBasisStrategy` | ETH spot + perp hedge | Medium |
| **eth_staking_only** | `ETHStakingOnlyStrategy` | ETH staking only | Simple |
| **eth_leveraged** | `ETHLeveragedStrategy` | Leveraged ETH staking | Complex |
| **usdt_market_neutral_no_leverage** | `USDTMarketNeutralNoLeverageStrategy` | Market-neutral without leverage | Medium |
| **usdt_market_neutral** | `USDTMarketNeutralStrategy` | Full market-neutral with leverage | Complex |

### **Config Requirements**

**Status**: ⚠️ Pending YAML Updates

The following config fields are needed in `component_config.strategy_factory` but not yet present in mode YAML files:

| Field | Type | Description | Required For |
|-------|------|-------------|--------------|
| `timeout` | int | Strategy creation timeout in seconds | All modes |
| `max_retries` | int | Maximum retry attempts for strategy creation | All modes |
| `validation_strict` | bool | Strict mode validation | All modes |

**Action Required**: Add these fields to mode YAML files in `configs/modes/*.yaml`

## Event Logging Requirements

### Component Event Log File
**Separate log file** for this component's events:
- **File**: `logs/events/strategy_factory_events.jsonl`
- **Format**: JSON Lines (one event per line)
- **Rotation**: Daily rotation, keep 30 days
- **Purpose**: Component-specific audit trail

### Event Logging via EventLogger
All events logged through centralized EventLogger:

```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='[event_type]',
    component='StrategyFactory',
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
    component='StrategyFactory',
    data={
        'available_modes': self.get_available_modes(),
        'config_hash': hash(str(self.config))
    }
)
```

#### 2. Strategy Creation (Every create_strategy() Call)
```python
self.event_logger.log_event(
    timestamp=pd.Timestamp.now(),
    event_type='strategy_created',
    component='StrategyFactory',
    data={
        'mode': mode,
        'strategy_class': strategy_class.__name__,
        'processing_time_ms': processing_time
    }
)
```

#### 3. Error Events
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='error',
    component='StrategyFactory',
    data={
        'error_code': 'STRAT-FAC-001',
        'error_message': str(e),
        'stack_trace': traceback.format_exc(),
        'error_severity': 'CRITICAL|HIGH|MEDIUM|LOW'
    }
)
```

#### 4. Component-Specific Critical Events
- **Strategy Creation Failed**: When strategy instantiation fails
- **Mode Validation Failed**: When mode is unsupported
- **Dependency Validation Failed**: When required dependencies missing

## Error Codes

### Component Error Code Prefix: STRAT-FAC
All StrategyFactory errors use the `STRAT-FAC` prefix.

### Error Code Registry
**Source**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`

All error codes registered with:
- **code**: Unique error code
- **component**: Component name
- **severity**: CRITICAL | HIGH | MEDIUM | LOW
- **message**: Human-readable error message
- **resolution**: How to resolve

### Component Error Codes

#### STRAT-FAC-001: Strategy Creation Failed (HIGH)
**Description**: Failed to create strategy instance
**Cause**: Invalid mode, missing dependencies, initialization errors
**Recovery**: Check mode name, verify dependencies, check configuration
```python
raise ComponentError(
    error_code='STRAT-FAC-001',
    message='Strategy creation failed',
    component='StrategyFactory',
    severity='HIGH'
)
```

#### STRAT-FAC-002: Mode Validation Failed (HIGH)
**Description**: Strategy mode not supported
**Cause**: Invalid mode name, mode not in STRATEGY_MAP
**Recovery**: Check mode name against available modes, verify STRATEGY_MAP
```python
raise ComponentError(
    error_code='STRAT-FAC-002',
    message='Mode validation failed',
    component='StrategyFactory',
    severity='HIGH'
)
```

#### STRAT-FAC-003: Dependency Validation Failed (CRITICAL)
**Description**: Required dependencies missing or invalid
**Cause**: Missing data_provider, exposure_monitor, or risk_monitor
**Recovery**: Immediate action required, verify all dependencies provided
```python
raise ComponentError(
    error_code='STRAT-FAC-003',
    message='Dependency validation failed',
    component='StrategyFactory',
    severity='CRITICAL'
)
```

### Structured Error Handling Pattern

#### Error Raising
```python
from backend.src.basis_strategy_v1.core.error_codes.exceptions import ComponentError

try:
    strategy = cls.STRATEGY_MAPmode(config, dependencies)
except Exception as e:
    # Log error event
    self.event_logger.log_event(
        timestamp=timestamp,
        event_type='error',
        component='StrategyFactory',
        data={
            'error_code': 'STRAT-FAC-001',
            'error_message': str(e),
            'stack_trace': traceback.format_exc()
        }
    )
    
    # Raise structured error
    raise ComponentError(
        error_code='STRAT-FAC-001',
        message=f'StrategyFactory failed: {str(e)}',
        component='StrategyFactory',
        severity='HIGH',
        original_exception=e
    )
```

#### Error Propagation Rules
- **CRITICAL**: Propagate to health system → trigger app restart
- **HIGH**: Log and retry with exponential backoff (max 3 retries)
- **MEDIUM**: Log and continue with degraded functionality
- **LOW**: Log for monitoring, no action needed

## Quality Gates

### Validation Criteria
- [ ] All 19 sections present and complete
- [ ] Canonical Sources section includes all 5+ architecture docs
- [ ] Configuration Parameters shows component_config.strategy_factory structure
- [ ] MODE-AGNOSTIC IMPLEMENTATION present (factory is mode-agnostic)
- [ ] ComponentFactory pattern NOT needed (this IS the factory)
- [ ] Table showing strategy modes (all 7 modes)
- [ ] Cross-references to CONFIGURATION.md, CODE_STRUCTURE_PATTERNS.md
- [ ] No mode-specific if statements in create_strategy method
- [ ] BaseDataProvider type used (not DataProvider)
- [ ] config['mode'] used (not config['strategy_mode'])

### Section Order Validation
- [x] Title and Purpose (section 1)
- [x] Canonical Sources (section 2)
- [x] Responsibilities (section 3)
- [x] State (section 4)
- [x] Component References (Set at Init) (section 5)
- [x] Config-Driven Behavior (section 6)
- [x] Environment Variables (section 7)
- [x] Config Fields Used (section 8)
- [x] Data Provider Queries (section 9)
- [x] Core Methods (section 10)
- [x] Data Access Pattern (section 11)
- [x] Mode-Aware Behavior (section 12)
- [x] MODE-AGNOSTIC IMPLEMENTATION EXAMPLE (section 13)
- [x] Event Logging Requirements (section 14)
- [x] Error Codes (section 15)
- [x] Quality Gates (section 16)
- [x] Integration with Event-Driven Strategy Engine (section 17)
- [ ] Current Implementation Status (section 18)
- [ ] Related Documentation (section 19)

### Implementation Status
- [ ] Spec complete with all 19 sections
- [ ] All required sections present
- [ ] Mode-agnostic patterns documented
- [ ] Factory pattern fully documented

## Integration Points

### Called BY
- Event-Driven Strategy Engine (strategy creation): `factory.create_strategy(mode, config, dependencies)`
- Backtest Service (strategy initialization): `factory.create_strategy(mode, config, dependencies)`
- Live Trading Service (strategy initialization): `factory.create_strategy(mode, config, dependencies)`

### Calls TO
- BaseStrategyManager subclasses (creation): `STRATEGY_MAPmode(config, dependencies)`
- Component Factory (dependency creation): `ComponentFactory.create_*()` methods
- Config Manager (loading): `config_manager.load_strategy_config(mode)`

### Communication
- Direct method calls ONLY
- NO event publishing
- NO Redis/message queues
- NO async/await in internal methods

The Strategy Factory integrates with the Event-Driven Strategy Engine to provide:

1. **Dependency Injection**: Proper component references for strategy instances
2. **Tight Loop Integration**: Strategy instances work with tight loop architecture
3. **Mode Validation**: Ensures strategy modes are valid and supported
4. **Instance Management**: Manages strategy instance lifecycle

## Error Handling

The Strategy Factory handles errors gracefully:

1. **Invalid Mode**: Returns error for unsupported strategy modes
2. **Missing Dependencies**: Validates all required dependencies are available
3. **Creation Failures**: Retries strategy creation with configurable retry logic
4. **Configuration Errors**: Validates strategy configuration before creation

## Testing

The Strategy Factory supports comprehensive testing:

1. **Unit Tests**: Test strategy creation for each mode
2. **Integration Tests**: Test strategy integration with Event-Driven Strategy Engine
3. **Mock Testing**: Test with mocked dependencies
4. **Error Testing**: Test error handling and recovery

## Current Implementation Status

**Overall Completion**: 95% (Spec complete, implementation needs updates)

### **Core Functionality Status**
- ✅ **Working**: Strategy class mapping, mode validation, dependency injection
- ⚠️ **Partial**: Error handling patterns, event logging integration
- ❌ **Missing**: Config-driven timeout/retry settings, health integration
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
- [Base Strategy Manager Specification](5B_BASE_STRATEGY_MANAGER.md) - Abstract base class for all strategies
- [Strategy Manager Specification](05_STRATEGY_MANAGER.md) - Concrete strategy implementations
- [Event-Driven Strategy Engine Specification](15_EVENT_DRIVEN_STRATEGY_ENGINE.md) - Engine integration
- [Data Provider Specification](09_DATA_PROVIDER.md) - Data access patterns

### **Configuration and Implementation**
- [Configuration Guide](19_CONFIGURATION.md) - Complete config schemas for all 7 modes
- [Code Structure Patterns](../CODE_STRUCTURE_PATTERNS.md) - Implementation patterns
- [Event Logger Specification](08_EVENT_LOGGER.md) - Event logging integration

---

**Status**: Specification complete ✅  
**Last Reviewed**: October 11, 2025


