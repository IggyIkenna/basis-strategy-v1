# Execution Interface Factory Component Specification

## Purpose
Factory for creating execution interface instances based on venue requirements with proper dependency injection and tight loop architecture integration.

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](../MODES.md) - Canonical strategy mode definitions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides
- **Config-Driven Architecture**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Mode-agnostic architecture guide
- **Code Structures**: [CODE_STRUCTURE_PATTERNS.md](../CODE_STRUCTURE_PATTERNS.md) - Complete implementation patterns

## Responsibilities
1. Create execution interface instances based on venue requirements
2. Provide proper dependency injection for execution interfaces
3. Integrate with tight loop architecture
4. Support all venue types (CEX, DEX, OnChain) with standardized interfaces
5. Validate venue configuration and requirements

## State
- interface_map: Dict[str, Type[ExecutionInterface]] (interface class mapping)
- created_interfaces: Dict[str, ExecutionInterface] (created interface instances)
- venue_validation: Dict[str, bool] (venue validation results)

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- config: Dict (reference, never modified)
- execution_mode: str (BASIS_EXECUTION_MODE)

These references are stored in __init__ and used throughout component lifecycle.
Components NEVER receive these as method parameters during runtime.

## Configuration Parameters

### **Config-Driven Architecture**

The Execution Interface Factory is **mode-agnostic** and uses `component_config.execution_interface_factory` from the mode configuration:

```yaml
component_config:
  execution_interface_factory:
    timeout: 30           # Interface creation timeout in seconds
    max_retries: 3        # Maximum retry attempts
    validation_strict: true # Strict venue validation
```

### **Configuration Parameter Definitions**

| Parameter | Description | Valid Values | Required | Default |
|-----------|-------------|--------------|----------|---------|
| `timeout` | Interface creation timeout | 1-300 seconds | No | 30 |
| `max_retries` | Maximum retry attempts | 1-10 | No | 3 |
| `validation_strict` | Strict venue validation | true/false | No | true |

### **Execution Interface Factory Behavior by Strategy Mode**

| Mode | Timeout | Max Retries | Validation |
|------|---------|-------------|------------|
| **Pure Lending** | 30s | 3 | Strict |
| **BTC Basis** | 30s | 3 | Strict |
| **ETH Basis** | 30s | 3 | Strict |
| **ETH Staking Only** | 30s | 3 | Strict |
| **ETH Leveraged** | 30s | 3 | Strict |
| **USDT MN No Leverage** | 30s | 3 | Strict |
| **USDT Market Neutral** | 30s | 3 | Strict |

**Key Insight**: The Execution Interface Factory uses **identical configuration** for all strategy modes. No mode-specific configuration needed.

**Cross-Reference**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas with full examples for all 7 modes

## Environment Variables

### System-Level Variables
- **BASIS_EXECUTION_MODE**: 'backtest' | 'live' (determines interface behavior)
- **BASIS_LOG_LEVEL**: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' (logging level)
- **BASIS_DATA_DIR**: Path to data directory (for backtest mode)

### Component-Specific Variables
- **EXECUTION_INTERFACE_FACTORY_TIMEOUT**: Interface creation timeout in seconds (default: 30)
- **EXECUTION_INTERFACE_FACTORY_MAX_RETRIES**: Maximum retry attempts for interface creation (default: 3)

## Environment-Specific Credential Routing

### Credential Routing Method

The Execution Interface Factory provides environment-specific credential routing to ensure proper credential selection based on `BASIS_ENVIRONMENT`. This method is used by all factory methods to inject the correct credentials into execution interfaces.

**Environment Detection and Credential Routing**:
```python
@classmethod
def _get_venue_credentials(cls, venue: str) -> Dict:
    """Get environment-specific credentials for venue."""
    environment = os.getenv('BASIS_ENVIRONMENT', 'dev')
    credential_prefix = f"BASIS_{environment.upper()}__"
    
    if venue == 'binance':
        return {
            'spot_api_key': os.getenv(f'{credential_prefix}CEX__BINANCE_SPOT_API_KEY'),
            'spot_secret': os.getenv(f'{credential_prefix}CEX__BINANCE_SPOT_SECRET'),
            'futures_api_key': os.getenv(f'{credential_prefix}CEX__BINANCE_FUTURES_API_KEY'),
            'futures_secret': os.getenv(f'{credential_prefix}CEX__BINANCE_FUTURES_SECRET'),
        }
    elif venue == 'bybit':
        return {
            'api_key': os.getenv(f'{credential_prefix}CEX__BYBIT_API_KEY'),
            'secret': os.getenv(f'{credential_prefix}CEX__BYBIT_SECRET'),
        }
    elif venue == 'okx':
        return {
            'api_key': os.getenv(f'{credential_prefix}CEX__OKX_API_KEY'),
            'secret': os.getenv(f'{credential_prefix}CEX__OKX_SECRET'),
            'passphrase': os.getenv(f'{credential_prefix}CEX__OKX_PASSPHRASE'),
        }
    elif venue == 'alchemy':
        return {
            'private_key': os.getenv(f'{credential_prefix}ALCHEMY__PRIVATE_KEY'),
            'rpc_url': os.getenv(f'{credential_prefix}ALCHEMY__RPC_URL'),
            'wallet_address': os.getenv(f'{credential_prefix}ALCHEMY__WALLET_ADDRESS'),
            'network': os.getenv(f'{credential_prefix}ALCHEMY__NETWORK'),
            'chain_id': os.getenv(f'{credential_prefix}ALCHEMY__CHAIN_ID'),
        }
    else:
        raise ValueError(f"Unknown venue: {venue}")
```

### Credential Validation

All credentials must be validated before interface creation to ensure they are present and contain valid values.

```python
@classmethod
def _validate_credentials(cls, credentials: Dict, venue: str) -> bool:
    """Validate that required credentials are present and non-empty."""
    for key, value in credentials.items():
        if not value or value.startswith('your_') or value == '0x...':
            raise ValueError(f"Invalid or missing credential for {venue}: {key}")
    return True
```

### Environment Detection Logic

The factory uses `BASIS_ENVIRONMENT` to determine which credential set to use:

- **Development** (`BASIS_ENVIRONMENT=dev`): Uses `BASIS_DEV__*` credentials (testnet APIs)
- **Staging** (`BASIS_ENVIRONMENT=staging`): Uses `BASIS_STAGING__*` credentials (mainnet APIs, staging wallet)
- **Production** (`BASIS_ENVIRONMENT=prod`): Uses `BASIS_PROD__*` credentials (mainnet APIs, production wallet)

**Reference**: [VENUE_ARCHITECTURE.md](../VENUE_ARCHITECTURE.md) - Environment Variables section
**Reference**: [ENVIRONMENT_VARIABLES.md](../ENVIRONMENT_VARIABLES.md) - Environment-Specific Credential Routing section

## Config Fields Used

### Universal Config (All Components)
- **execution_mode**: 'backtest' | 'live' (from strategy mode slice)
- **log_level**: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' (from strategy mode slice)

### Component-Specific Config
- **execution_interface_factory_settings**: Dict (execution interface factory-specific settings)
  - **timeout**: Interface creation timeout
  - **max_retries**: Maximum retry attempts
  - **validation_strict**: Strict venue validation
- **venue_settings**: Dict (venue-specific settings)
  - **venue_type**: Venue type (CEX, DEX, OnChain)
  - **dependencies**: Interface dependencies

## Data Provider Queries

### Data Types Requested
**CLARIFICATION**: Execution Interface Factory does NOT query DataProvider directly. It creates execution interfaces that may query data providers for market data and execution information.

### Data NOT Available from DataProvider
Execution Interface Factory does not query DataProvider - it creates interfaces that handle their own data access patterns.

## Config-Driven Behavior

The Execution Interface Factory is **mode-agnostic** by design - it creates execution interface instances without mode-specific logic:

**Component Configuration** (from `component_config.execution_interface_factory`):
```yaml
component_config:
  execution_interface_factory:
    # Execution Interface Factory is inherently mode-agnostic
    # Creates execution interface instances regardless of strategy mode
    # No mode-specific configuration needed
    timeout: 30           # Interface creation timeout in seconds
    max_retries: 3        # Maximum retry attempts
    validation_strict: true # Strict venue validation
```

**Mode-Agnostic Interface Creation**:
- Creates execution interface instances based on venue requirements
- Same creation logic for all strategy modes
- No mode-specific if statements in interface creation
- Uses config-driven timeout and retry settings

**Interface Creation by Venue Type**:

**CEX Execution Interfaces**:
- Creates: `BinanceExecutionInterface`, `BybitExecutionInterface`, `OKXExecutionInterface`
- Dependencies: position_monitor, event_logger, data_provider
- Same creation logic as other venue types

**DEX Execution Interfaces**:
- Creates: `UniswapExecutionInterface`, `CurveExecutionInterface`
- Dependencies: position_monitor, event_logger, data_provider
- Same creation logic as other venue types

**OnChain Execution Interfaces**:
- Creates: `AAVEExecutionInterface`, `MorphoExecutionInterface`, `LidoExecutionInterface`
- Dependencies: position_monitor, event_logger, data_provider
- Same creation logic as other venue types

**Key Principle**: Execution Interface Factory is **purely creation** - it does NOT:
- Make mode-specific decisions about which interfaces to create
- Handle strategy-specific interface creation logic
- Convert or transform configuration data
- Make business logic decisions

All creation logic is generic - it uses the interface class mapping to create the appropriate execution interface instance based on venue requirements, with each interface handling venue-specific logic internally using standardized interfaces.

## Interface Class Mapping

```python
INTERFACE_MAP = {
    # CEX Interfaces
    'binance': BinanceExecutionInterface,
    'bybit': BybitExecutionInterface,
    'okx': OKXExecutionInterface,
    
    # DEX Interfaces
    'uniswap': UniswapExecutionInterface,
    'curve': CurveExecutionInterface,
    
    # OnChain Interfaces
    'aave': AAVEExecutionInterface,
    'morpho': MorphoExecutionInterface,
    'lido': LidoExecutionInterface,
    'etherfi': EtherFiExecutionInterface,
}
```

## MODE-AGNOSTIC IMPLEMENTATION EXAMPLE

### Complete Execution Interface Factory Implementation

```python
from typing import Dict, List, Type, Any, Optional
from abc import ABC, abstractmethod
import logging

class ExecutionInterfaceFactory:
    """Factory for creating execution interface instances based on venue requirements"""
    
    # Complete venue class mapping for all supported venues
    VENUE_MAP: Dict[str, Type[ExecutionInterface]] = {
        # CEX Interfaces
        'binance': BinanceExecutionInterface,
        'bybit': BybitExecutionInterface,
        'okx': OKXExecutionInterface,
        
        # DEX Interfaces
        'uniswap': UniswapExecutionInterface,
        'curve': CurveExecutionInterface,
        
        # OnChain Interfaces
        'aave': AAVEExecutionInterface,
        'morpho': MorphoExecutionInterface,
        'lido': LidoExecutionInterface,
        'etherfi': EtherFiExecutionInterface,
        'instadapp': InstadappExecutionInterface,
    }
    
    @classmethod
    def create_interface(
        cls,
        venue: str,
        config: Dict[str, Any],
        execution_mode: str,
        position_monitor: PositionMonitor,
        event_logger: EventLogger,
        data_provider: BaseDataProvider
    ) -> ExecutionInterface:
        """
        Create execution interface instance based on venue with dependency injection.
        
        Parameters:
        - venue: Venue name (e.g., 'binance', 'aave', 'uniswap')
        - config: Complete configuration dictionary
        - execution_mode: 'backtest' or 'live'
        - position_monitor: Position monitor instance
        - event_logger: Event logger instance
        - data_provider: Data provider instance
        
        Returns:
        - ExecutionInterface: Execution interface instance for the specified venue
        
        Raises:
        - ValueError: If venue is not supported or dependencies are missing
        """
        # Validate venue
        if not cls.validate_venue(venue):
            raise ValueError(f"Unsupported venue: {venue}")
        
        # Get interface class
        interface_class = cls.VENUE_MAP[venue]
        
        # Validate dependencies
        cls._validate_dependencies(
            position_monitor, event_logger, data_provider
        )
        
        # Extract venue-specific config
        venue_config = config.get('venue_settings', {}).get(venue, {})
        
        # Get environment-specific credentials
        credentials = cls._get_venue_credentials(venue)
        cls._validate_credentials(credentials, venue)
        
        # Create interface instance with dependency injection
        try:
            interface_instance = interface_class(
                venue=venue,
                config=config,
                execution_mode=execution_mode,
                position_monitor=position_monitor,
                event_logger=event_logger,
                data_provider=data_provider,
                venue_config=venue_config,
                credentials=credentials
            )
            
            logging.info(f"Successfully created {venue} execution interface")
            return interface_instance
            
        except Exception as e:
            logging.error(f"Failed to create {venue} execution interface: {e}")
            raise ValueError(f"Interface creation failed for venue {venue}: {e}")
    
    @classmethod
    def create_all_interfaces(
        cls,
        config: Dict[str, Any],
        execution_mode: str,
        position_monitor: PositionMonitor,
        event_logger: EventLogger,
        data_provider: BaseDataProvider
    ) -> Dict[str, ExecutionInterface]:
        """
        Create all required execution interface instances based on config.
        
        Parameters:
        - config: Complete configuration dictionary
        - execution_mode: 'backtest' or 'live'
        - position_monitor: Position monitor instance
        - event_logger: Event logger instance
        - data_provider: Data provider instance
        
        Returns:
        - Dict[str, ExecutionInterface]: Dictionary mapping venue names to interface instances
        """
        interfaces = {}
        
        # Get required venues from config
        required_venues = config.get('venue_settings', {}).keys()
        
        for venue in required_venues:
            try:
                interfaces[venue] = cls.create_interface(
                    venue=venue,
                    config=config,
                    execution_mode=execution_mode,
                    position_monitor=position_monitor,
                    event_logger=event_logger,
                    data_provider=data_provider
                )
            except Exception as e:
                logging.error(f"Failed to create interface for venue {venue}: {e}")
                # Continue with other venues
                continue
        
        return interfaces
    
    @classmethod
    def validate_venue(cls, venue: str) -> bool:
        """
        Validate that venue is supported and interface class exists.
        
        Parameters:
        - venue: Venue name to validate
        
        Returns:
        - bool: True if venue is supported, False otherwise
        """
        if not venue:
            return False
        
        if venue not in cls.VENUE_MAP:
            logging.warning(f"Unknown venue: {venue}")
            return False
        
        # Check if interface class exists and is importable
        interface_class = cls.VENUE_MAP[venue]
        if not interface_class:
            logging.error(f"Interface class not found for venue: {venue}")
            return False
        
        return True
    
    @classmethod
    def get_available_venues(cls) -> List[str]:
        """
        Get list of available venues.
        
        Returns:
        - List[str]: List of all supported venue names
        """
        return list(cls.VENUE_MAP.keys())
    
    @classmethod
    def get_venue_info(cls, venue: str) -> Dict[str, Any]:
        """
        Get information about a specific venue.
        
        Parameters:
        - venue: Venue name
        
        Returns:
        - Dict[str, Any]: Venue information including class, type, etc.
        """
        if not cls.validate_venue(venue):
            raise ValueError(f"Unknown venue: {venue}")
        
        interface_class = cls.VENUE_MAP[venue]
        
        # Determine venue type
        venue_type = cls._get_venue_type(venue)
        
        return {
            'venue': venue,
            'class_name': interface_class.__name__,
            'module': interface_class.__module__,
            'venue_type': venue_type,
            'description': interface_class.__doc__ or f"Execution interface for {venue}",
            'is_available': True
        }
    
    @classmethod
    def _validate_dependencies(
        cls,
        position_monitor: PositionMonitor,
        event_logger: EventLogger,
        data_provider: BaseDataProvider
    ) -> None:
        """
        Validate that all required dependencies are available.
        
        Parameters:
        - position_monitor: Position monitor instance
        - event_logger: Event logger instance
        - data_provider: Data provider instance
        
        Raises:
        - ValueError: If any dependency is missing or invalid
        """
        if not position_monitor:
            raise ValueError("position_monitor is required")
        
        if not event_logger:
            raise ValueError("event_logger is required")
        
        if not data_provider:
            raise ValueError("data_provider is required")
        
        # Additional validation can be added here
        logging.debug("All execution interface dependencies validated successfully")
    
    @classmethod
    def _get_venue_type(cls, venue: str) -> str:
        """
        Get venue type (CEX, DEX, OnChain) for a venue.
        
        Parameters:
        - venue: Venue name
        
        Returns:
        - str: Venue type
        """
        venue_type_mapping = {
            # CEX venues
            'binance': 'CEX',
            'bybit': 'CEX',
            'okx': 'CEX',
            
            # DEX venues
            'uniswap': 'DEX',
            'curve': 'DEX',
            
            # OnChain venues
            'aave': 'OnChain',
            'morpho': 'OnChain',
            'lido': 'OnChain',
            'etherfi': 'OnChain',
            'instadapp': 'OnChain',
        }
        
        return venue_type_mapping.get(venue, 'Unknown')
```

### Integration with Event-Driven Strategy Engine

```python
# Example usage in Event-Driven Strategy Engine
class EventDrivenStrategyEngine:
    def __init__(self, config: Dict[str, Any]):
        # ... other initialization ...
        
        # Create execution interfaces using factory
        self.execution_interfaces = ExecutionInterfaceFactory.create_all_interfaces(
            config=config,
            execution_mode=config.get('execution_mode'),
            position_monitor=self.position_monitor,
            event_logger=self.event_logger,
            data_provider=self.data_provider
        )
        
        logging.info(f"Created {len(self.execution_interfaces)} execution interfaces")
    
    def execute_instructions(self, instructions: List[Dict], timestamp: pd.Timestamp):
        """Execute instructions using appropriate execution interfaces"""
        for instruction in instructions:
            venue = instruction.get('venue')
            if venue in self.execution_interfaces:
                interface = self.execution_interfaces[venue]
                interface.execute_instruction(instruction, timestamp)
            else:
                logging.error(f"No execution interface found for venue: {venue}")
```

## Venue Class Mapping (Complete)

| Venue | Interface Class | Venue Type | Description | Dependencies |
|-------|----------------|------------|-------------|--------------|
| `binance` | `BinanceExecutionInterface` | CEX | Binance spot and perpetual trading | position_monitor, event_logger, data_provider |
| `bybit` | `BybitExecutionInterface` | CEX | Bybit spot and perpetual trading | position_monitor, event_logger, data_provider |
| `okx` | `OKXExecutionInterface` | CEX | OKX spot and perpetual trading | position_monitor, event_logger, data_provider |
| `uniswap` | `UniswapExecutionInterface` | DEX | Uniswap V3 swaps and liquidity | position_monitor, event_logger, data_provider |
| `curve` | `CurveExecutionInterface` | DEX | Curve stablecoin swaps | position_monitor, event_logger, data_provider |
| `aave` | `AAVEExecutionInterface` | OnChain | AAVE lending and borrowing | position_monitor, event_logger, data_provider |
| `morpho` | `MorphoExecutionInterface` | OnChain | Morpho lending and borrowing | position_monitor, event_logger, data_provider |
| `lido` | `LidoExecutionInterface` | OnChain | Lido ETH staking | position_monitor, event_logger, data_provider |
| `etherfi` | `EtherFiExecutionInterface` | OnChain | EtherFi liquid staking | position_monitor, event_logger, data_provider |
| `instadapp` | `InstadappExecutionInterface` | OnChain | Instadapp DeFi operations | position_monitor, event_logger, data_provider |

**All venues use identical factory creation logic** - the only difference is the interface class, not the creation process.

## Config Requirements

The Execution Interface Factory requires the following config structure:

```yaml
component_config:
  execution_interface_factory:
    timeout: 30           # Interface creation timeout in seconds
    max_retries: 3        # Maximum retry attempts
    validation_strict: true # Strict venue validation

venue_settings:
  binance:
    testnet: false
    rate_limits:
      requests_per_minute: 1200
  aave:
    network: "mainnet"
    gas_strategy: "standard"
  uniswap:
    network: "mainnet"
    gas_strategy: "fast"
```

## Factory Methods

### create_all_interfaces()
```python
@classmethod
def create_all_interfaces(
    cls,
    execution_mode: str,
    config: Dict[str, Any],
    data_provider
) -> Dict[str, ExecutionInterface]:
    """Create all required execution interface instances."""
```

### create_interface()
```python
@classmethod
def create_interface(
    cls,
    venue: str,
    execution_mode: str,
    config: Dict[str, Any],
    data_provider
) -> ExecutionInterface:
    """Create specific execution interface instance."""
```

### set_interface_dependencies()
```python
@classmethod
def set_interface_dependencies(
    cls,
    interfaces: Dict[str, ExecutionInterface],
    position_monitor,
    event_logger,
    data_provider
) -> None:
    """Set dependencies for all execution interfaces."""
```

### validate_venue()
```python
@classmethod
def validate_venue(cls, venue: str) -> bool:
    """Validate that venue is supported and interface class exists."""
```

### get_available_venues()
```python
@classmethod
def get_available_venues(cls) -> List[str]:
    """Get list of available venues."""
```

## Error Handling

### Credential Validation Errors

The factory handles credential validation errors during interface creation:

**Error Types**:
- **Missing Credentials**: Environment-specific credentials not set
- **Invalid Credentials**: Placeholder values or empty strings
- **Unknown Venue**: Venue not supported by credential routing

**Error Handling Pattern**:
```python
try:
    credentials = cls._get_venue_credentials(venue)
    cls._validate_credentials(credentials, venue)
except ValueError as e:
    logging.error(f"Credential validation failed for {venue}: {e}")
    raise ValueError(f"Interface creation failed for venue {venue}: {e}")
```

**Recovery Procedures**:
1. **Missing Credentials**: Check environment variable configuration
2. **Invalid Credentials**: Verify credential values are not placeholders
3. **Unknown Venue**: Add venue to credential routing method

**Error Codes**:
- **EIF-001**: Missing environment-specific credentials
- **EIF-002**: Invalid credential values (placeholders)
- **EIF-003**: Unknown venue in credential routing

## Integration Points

### Called BY
- Execution Manager (interface creation): `factory.create_interface(venue, interface_type, config)`
- Strategy Manager (interface initialization): `factory.create_interface(venue, interface_type, config)`
- Backtest Service (interface setup): `factory.create_interface(venue, interface_type, config)`

### Calls TO
- ExecutionInterface subclasses (creation): `VENUE_MAPvenue(config, dependencies)`
- Component Factory (dependency creation): `ComponentFactory.create_*()` methods
- Config Manager (validation): `config_manager.validate_venue_config(venue)`

### Communication
- Direct method calls ONLY
- NO event publishing
- NO Redis/message queues
- NO async/await in internal methods

The Execution Interface Factory integrates with the Event-Driven Strategy Engine to provide:

1. **Dependency Injection**: Proper component references for execution interfaces
2. **Tight Loop Integration**: Execution interfaces work with tight loop architecture
3. **Venue Validation**: Ensures venues are valid and supported
4. **Instance Management**: Manages execution interface instance lifecycle

## Error Handling

The Execution Interface Factory handles errors gracefully:

1. **Invalid Venue**: Returns error for unsupported venues
2. **Missing Dependencies**: Validates all required dependencies are available
3. **Creation Failures**: Retries interface creation with configurable retry logic
4. **Configuration Errors**: Validates venue configuration before creation

## Core Methods

### create_interface(venue: str, config: Dict, execution_mode: str, position_monitor: PositionMonitor, event_logger: EventLogger, data_provider: BaseDataProvider) -> ExecutionInterface
Create execution interface instance based on venue.

**Parameters**:
- venue: Venue name (e.g., 'binance', 'aave', 'uniswap')
- config: Complete configuration dictionary
- execution_mode: 'backtest' or 'live'
- position_monitor: Position monitor instance
- event_logger: Event logger instance
- data_provider: Data provider instance

**Returns**:
- ExecutionInterface: Interface instance for specified venue

### create_all_interfaces(config: Dict, execution_mode: str, position_monitor: PositionMonitor, event_logger: EventLogger, data_provider: BaseDataProvider) -> Dict[str, ExecutionInterface]
Create all required execution interface instances based on config.

**Returns**:
- Dict[str, ExecutionInterface]: Dictionary mapping venue names to interface instances

### validate_venue(venue: str) -> bool
Validate that venue is supported.

**Parameters**:
- venue: Venue name to validate

**Returns**:
- bool: True if venue supported, False otherwise

### get_available_venues() -> List[str]
Get list of available venues.

**Returns**:
- List[str]: All supported venue names

## Data Access Pattern

Factory doesn't access data - it creates components that access data:

```python
@classmethod
def create_interface(cls, venue: str, config: Dict, dependencies: Dict) -> ExecutionInterface:
    # No data access - pure factory
    interface_class = cls.VENUE_MAP[venue]
    return interface_class(config, dependencies)
```

## Mode-Aware Behavior

### Backtest Mode
```python
def create_interface(self, venue: str, interface_type: str, config: Dict) -> ExecutionInterface:
    # Create mock/simulated interfaces for backtest mode
    # Same creation logic for all strategy modes
    return self._create_mock_interface(venue, interface_type, config)
```

### Live Mode
```python
def create_interface(self, venue: str, interface_type: str, config: Dict) -> ExecutionInterface:
    # Create real interfaces for live mode
    # Same creation logic for all strategy modes
    return self._create_live_interface(venue, interface_type, config)
```

**Key**: Only difference is interface type (mock vs real) - creation logic is identical across all modes.

## Event Logging Requirements

### Component Event Log File
**Separate log file** for this component's events:
- **File**: `logs/events/execution_interface_factory_events.jsonl`
- **Format**: JSON Lines (one event per line)
- **Rotation**: Daily rotation, keep 30 days
- **Purpose**: Component-specific audit trail

### Event Logging via EventLogger
All events logged through centralized EventLogger:

```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='[event_type]',
    component='ExecutionInterfaceFactory',
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
    component='ExecutionInterfaceFactory',
    data={
        'available_venues': self.get_available_venues(),
        'config_hash': hash(str(self.config))
    }
)
```

#### 2. Interface Creation (Every create_interface() Call)
```python
self.event_logger.log_event(
    timestamp=pd.Timestamp.now(),
    event_type='interface_created',
    component='ExecutionInterfaceFactory',
    data={
        'venue': venue,
        'interface_class': interface_class.__name__,
        'processing_time_ms': processing_time
    }
)
```

#### 3. Error Events
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='error',
    component='ExecutionInterfaceFactory',
    data={
        'error_code': 'EIF-001',
        'error_message': str(e),
        'stack_trace': traceback.format_exc(),
        'error_severity': 'CRITICAL|HIGH|MEDIUM|LOW'
    }
)
```

#### 4. Component-Specific Critical Events
- **Interface Creation Failed**: When interface instantiation fails
- **Venue Validation Failed**: When venue is unsupported
- **Credential Validation Failed**: When required credentials missing

## Error Codes

### Component Error Code Prefix: EIF
All ExecutionInterfaceFactory errors use the `EIF` prefix.

### Error Code Registry
**Source**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`

All error codes registered with:
- **code**: Unique error code
- **component**: Component name
- **severity**: CRITICAL | HIGH | MEDIUM | LOW
- **message**: Human-readable error message
- **resolution**: How to resolve

### Component Error Codes

#### EIF-001: Interface Creation Failed (HIGH)
**Description**: Failed to create execution interface instance
**Cause**: Invalid venue, missing dependencies, initialization errors
**Recovery**: Check venue name, verify dependencies, check configuration
```python
raise ComponentError(
    error_code='EIF-001',
    message='Interface creation failed',
    component='ExecutionInterfaceFactory',
    severity='HIGH'
)
```

#### EIF-002: Venue Validation Failed (HIGH)
**Description**: Execution venue not supported
**Cause**: Invalid venue name, venue not in VENUE_MAP
**Recovery**: Check venue name against available venues, verify VENUE_MAP
```python
raise ComponentError(
    error_code='EIF-002',
    message='Venue validation failed',
    component='ExecutionInterfaceFactory',
    severity='HIGH'
)
```

#### EIF-003: Credential Validation Failed (CRITICAL)
**Description**: Required credentials missing or invalid
**Cause**: Missing API keys, invalid credential values
**Recovery**: Immediate action required, verify all credentials provided
```python
raise ComponentError(
    error_code='EIF-003',
    message='Credential validation failed',
    component='ExecutionInterfaceFactory',
    severity='CRITICAL'
)
```

### Structured Error Handling Pattern

#### Error Raising
```python
from backend.src.basis_strategy_v1.core.error_codes.exceptions import ComponentError

try:
    interface = cls.VENUE_MAPvenue(config, dependencies)
except Exception as e:
    # Log error event
    self.event_logger.log_event(
        timestamp=timestamp,
        event_type='error',
        component='ExecutionInterfaceFactory',
        data={
            'error_code': 'EIF-001',
            'error_message': str(e),
            'stack_trace': traceback.format_exc()
        }
    )
    
    # Raise structured error
    raise ComponentError(
        error_code='EIF-001',
        message=f'ExecutionInterfaceFactory failed: {str(e)}',
        component='ExecutionInterfaceFactory',
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
- [ ] Configuration Parameters shows component_config.execution_interface_factory structure
- [ ] MODE-AGNOSTIC IMPLEMENTATION present (factory is mode-agnostic)
- [ ] ComponentFactory pattern NOT needed (this IS the factory)
- [ ] Table showing venue types (all venue types)
- [ ] Cross-references to CONFIGURATION.md, CODE_STRUCTURE_PATTERNS.md
- [ ] No mode-specific if statements in create_interface method
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

## Testing

The Execution Interface Factory supports comprehensive testing:

1. **Unit Tests**: Test interface creation for each venue
2. **Integration Tests**: Test interface integration with Event-Driven Strategy Engine
3. **Mock Testing**: Test with mocked dependencies
4. **Error Testing**: Test error handling and recovery

## Current Implementation Status

**Overall Completion**: 95% (Spec complete, implementation needs updates)

### **Core Functionality Status**
- ✅ **Working**: Venue class mapping, venue validation, dependency injection
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
- [Execution Interface Manager Specification](07_EXECUTION_INTERFACE_MANAGER.md) - Manager for execution interfaces
- [Execution Interfaces Specification](07B_EXECUTION_INTERFACES.md) - Individual interface implementations
- [Position Monitor Specification](01_POSITION_MONITOR.md) - Position data provider
- [Event Logger Specification](08_EVENT_LOGGER.md) - Event logging integration

### **Configuration and Implementation**
- [Configuration Guide](19_CONFIGURATION.md) - Complete config schemas for all 7 modes
- [Code Structure Patterns](../CODE_STRUCTURE_PATTERNS.md) - Implementation patterns
- [Venue Architecture](../VENUE_ARCHITECTURE.md) - Venue-specific patterns

---

**Status**: Specification complete ✅  
**Last Reviewed**: October 11, 2025


