# Live Trading Service Component Specification

**Last Reviewed**: October 11, 2025

## Purpose
Orchestrate live trading with real execution and risk management using EventDrivenStrategyEngine.

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](../MODES.md) - Canonical strategy mode definitions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

## Current Implementation Status

**Status**: ✅ **PARTIALLY IMPLEMENTED** (HIGH Priority)
**Last Updated**: October 12, 2025
**Implementation File**: `backend/src/basis_strategy_v1/core/services/live_service.py`

### Implementation Status
- **Core Methods**: 3/3 methods implemented (run_live_trading, _apply_overrides, _slice_config)
- **Config Parameters**: 0/0 implemented (timeout, risk limits, position limits)
- **Architecture Compliance**: 0.60 (good implementation with config gaps)

### Implementation Details
- **LiveTradingRequest**: ✅ Implemented with validation
- **Config Management**: ✅ Implemented with override support
- **Engine Integration**: ✅ Integrated with EventDrivenStrategyEngine
- **Error Handling**: ✅ Comprehensive error codes (LT-001 through LT-011)
- **Risk Management**: ✅ Basic risk checks implemented
- **Environment Controls**: ✅ BASIS_LIVE_TRADING__ENABLED and BASIS_LIVE_TRADING__READ_ONLY

### Remaining Gaps
- **Config Integration**: Service-level config parameters not implemented
- **Concurrent Execution**: Max concurrent trades not enforced
- **Memory Management**: Memory limits not implemented
- **Position Limits**: Position size limits not enforced
- **Risk Management**: Advanced risk management not implemented

### Task Recommendations
- Add config-driven service parameters (timeout, risk limits, position limits)
- Implement concurrent execution management
- Add memory monitoring and cleanup
- Implement advanced risk management features
- Add comprehensive unit tests

## Responsibilities
1. Receive live trading requests with strategy_name and config overrides
2. Slice config for strategy mode and apply overrides
3. Create fresh DataProvider and component instances
4. Orchestrate live trading via EventDrivenStrategyEngine
5. Manage continuous trading execution

## State
- global_config: Dict (immutable, validated at startup)
- running_strategies: Dict[str, asyncio.Task] (active live trading tasks)
- strategy_status: Dict[str, Dict] (strategy execution status)

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- global_config: Dict (reference, never modified)
- config_manager: ConfigManager (reference, for config slicing)

These references are stored in __init__ and used throughout component lifecycle.
Components NEVER receive these as method parameters during runtime.

## Configuration Parameters

### **Config-Driven Architecture**

The Live Trading Service is **mode-agnostic** and uses configuration from the strategy mode:

```yaml
# From strategy mode configuration
live_trading_service:
  timeout_seconds: 7200
  max_concurrent_trades: 3
  memory_limit_mb: 4096
  risk_management_enabled: true
  execution_timeout: 30
  position_size_limit: 1000000
```

### **Parameter Definitions**
- **timeout_seconds**: Maximum execution time for live trading
- **max_concurrent_trades**: Maximum concurrent trade executions
- **memory_limit_mb**: Memory limit for live trading execution
- **risk_management_enabled**: Enable real-time risk management
- **execution_timeout**: Timeout for individual trade executions
- **position_size_limit**: Maximum position size limit

## Environment Variables

### System-Level Variables
- **BASIS_EXECUTION_MODE**: 'backtest' | 'live' (determines service behavior)
- **BASIS_LOG_LEVEL**: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' (logging level)
- **BASIS_DATA_DIR**: Path to data directory (for backtest mode)

### Live Trading Safety Controls
- **BASIS_LIVE_TRADING__ENABLED**: Enable/disable live trading (default: false)
  - **Usage**: Master safety switch for live trading
  - **Values**: true | false
  - **Impact**: When false, all live trading requests are rejected
  - **Safety**: Must be explicitly set to true to enable live trading

- **BASIS_LIVE_TRADING__READ_ONLY**: Read-only mode for testing (default: true)
  - **Usage**: Safe testing mode that prevents real trades
  - **Values**: true | false
  - **Impact**: When true, logs trades but doesn't execute them
  - **Safety**: Recommended for initial testing

- **BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD**: Maximum trade size in USD (default: 100)
  - **Usage**: Risk management limit for trade sizes
  - **Values**: Positive number
  - **Impact**: Rejects trades exceeding this amount
  - **Safety**: Prevents large accidental trades

- **BASIS_LIVE_TRADING__EMERGENCY_STOP_LOSS_PCT**: Emergency stop loss threshold (default: 0.15)
  - **Usage**: Automatic stop when drawdown exceeds threshold
  - **Values**: 0.0 to 1.0 (percentage)
  - **Impact**: Automatically stops strategy when breached
  - **Safety**: Circuit breaker for large losses

- **BASIS_LIVE_TRADING__HEARTBEAT_TIMEOUT_SECONDS**: Heartbeat timeout (default: 300)
  - **Usage**: Health monitoring timeout
  - **Values**: Positive integer (seconds)
  - **Impact**: Considers strategy unhealthy if no heartbeat
  - **Safety**: Early detection of strategy failures

- **BASIS_LIVE_TRADING__CIRCUIT_BREAKER_ENABLED**: Enable circuit breaker (default: true)
  - **Usage**: Enable automatic emergency stops
  - **Values**: true | false
  - **Impact**: When enabled, triggers emergency stops on breaches
  - **Safety**: Additional safety layer for risk management

### Safety Controls Implementation

The live trading service implements comprehensive safety controls through environment variables:

**Startup Validation**:
- All live trading variables are validated at startup when `BASIS_EXECUTION_MODE=live`
- Invalid values cause startup failure with clear error messages
- Default values are applied for missing variables

**Runtime Safety Checks**:
- `BASIS_LIVE_TRADING__ENABLED` is checked before accepting any live trading requests
- `BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD` is validated against initial capital
- `BASIS_LIVE_TRADING__READ_ONLY` mode is enforced during execution
- `BASIS_LIVE_TRADING__EMERGENCY_STOP_LOSS_PCT` triggers automatic stops
- `BASIS_LIVE_TRADING__HEARTBEAT_TIMEOUT_SECONDS` is used for health monitoring
- `BASIS_LIVE_TRADING__CIRCUIT_BREAKER_ENABLED` controls emergency stop behavior

**Error Codes**:
- `LT-008`: Live trading disabled via BASIS_LIVE_TRADING__ENABLED
- `LT-009`: Live trading in read-only mode via BASIS_LIVE_TRADING__READ_ONLY
- `LT-010`: Initial capital exceeds maximum trade size
- `LT-011`: Emergency stop loss threshold breached

## Config Fields Used

### Universal Config (All Components)
- **execution_mode**: 'backtest' | 'live' (from strategy mode slice)
- **log_level**: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' (from strategy mode slice)

### Component-Specific Config
- **live_trading_settings**: Dict (live trading-specific settings)
  - **timeout**: Live trading execution timeout
  - **max_concurrent**: Maximum concurrent strategies
  - **memory_limit**: Memory limit per strategy
- **strategy_settings**: Dict (strategy-specific settings)
  - **strategy_name**: Strategy mode name
  - **config_overrides**: Strategy configuration overrides

## Config-Driven Behavior

The Live Trading Service uses configuration to determine how to initialize components and handle config overrides:

**Component Configuration** (from `component_config.live_trading_service`):
```yaml
component_config:
  live_trading_service:
    # Live Trading Service uses config-driven component initialization
    # No mode-specific configuration needed
    timeout: 3600           # Live trading execution timeout in seconds
    max_concurrent: 5       # Maximum concurrent strategies
    memory_limit: 1024      # Memory limit per strategy in MB
```

**Config-Driven Component Initialization**:
- Uses `BaseDataProviderFactory.create()` to create mode-specific data providers
- Uses `ComponentFactory.create_all()` to create config-driven components
- Applies config overrides to component configurations
- No mode-specific if statements in component initialization

**Component Initialization by Mode**:

**Pure Lending Mode**:
- Creates: `PureLendingDataProvider` with real-time AAVE USDT data
- Creates: config-driven components with pure lending config
- Applies: config overrides to component configurations
- Same initialization logic as other modes

**BTC Basis Mode**:
- Creates: `BTCBasisDataProvider` with real-time BTC spot/futures/funding data
- Creates: config-driven components with BTC basis config
- Applies: config overrides to component configurations
- Same initialization logic as other modes

**ETH Leveraged Mode**:
- Creates: `ETHLeveragedDataProvider` with real-time ETH/LST/AAVE data
- Creates: config-driven components with ETH leveraged config
- Applies: config overrides to component configurations
- Same initialization logic as other modes

**Key Principle**: Live Trading Service is **purely orchestration** - it does NOT:
- Make mode-specific decisions about which components to create
- Handle strategy-specific initialization logic
- Convert or transform configuration data
- Make business logic decisions

All initialization logic is generic - it uses factory patterns to create mode-specific data providers and config-driven components, then applies config overrides to customize component behavior.

## MODE-AGNOSTIC IMPLEMENTATION EXAMPLE

### Complete Live Trading Service Implementation

```python
from typing import Dict, List, Any, Optional
import asyncio
import uuid
import logging
from datetime import datetime
from decimal import Decimal

class LiveTradingService:
    """Service for orchestrating live trading execution using factory-based initialization"""
    
    def __init__(self, global_config: Dict[str, Any], config_manager: ConfigManager):
        # Store references (NEVER modified)
        self.global_config = global_config
        self.config_manager = config_manager
        
        # Extract config-driven service settings
        self.service_config = global_config.get('component_config', {}).get('live_trading_service', {})
        self.timeout = self.service_config.get('timeout', 3600)
        self.max_concurrent = self.service_config.get('max_concurrent', 5)
        self.memory_limit = self.service_config.get('memory_limit', 1024)
        
        # Initialize service state
        self.running_strategies: Dict[str, Dict[str, Any]] = {}
        self.completed_strategies: Dict[str, Dict[str, Any]] = {}
        self.strategy_status: Dict[str, Dict] = {}
        
        # Validate config
        self._validate_service_config()
        
        logging.info("LiveTradingService initialized with factory-based architecture")
    
    def _validate_service_config(self):
        """Validate live trading service configuration"""
        if self.timeout <= 0:
            raise ValueError("live_trading_service.timeout must be positive")
        
        if self.max_concurrent <= 0:
            raise ValueError("live_trading_service.max_concurrent must be positive")
        
        if self.memory_limit <= 0:
            raise ValueError("live_trading_service.memory_limit must be positive")
    
    async def start_live_trading(self, request: LiveTradingRequest) -> str:
        """
        Start live trading using factory-based component initialization.
        
        Parameters:
        - request: LiveTradingRequest with strategy_name, config_overrides, risk_limits
        
        Returns:
        - str: Request ID for tracking
        
        Raises:
        - ValueError: If request validation fails
        - RuntimeError: If live trading execution fails
        """
        request_id = str(uuid.uuid4())
        
        try:
            # 1. Validate request
            self._validate_request(request)
            
            # 2. Check concurrent limit
            if len(self.running_strategies) >= self.max_concurrent:
                raise RuntimeError(f"Maximum concurrent strategies ({self.max_concurrent}) reached")
            
            # 3. Slice config for strategy mode
            config_slice = self._slice_config(request.strategy_name)
            
            # 4. Apply config overrides
            final_config = self._apply_overrides(config_slice, request.config_overrides)
            
            # 5. Create fresh data provider using factory
            data_provider = self._create_data_provider(final_config, request)
            
            # 6. Create fresh component instances using factory
            components = self._create_components(final_config, data_provider)
            
            # 7. Initialize EventDrivenStrategyEngine
            strategy_engine = EventDrivenStrategyEngine(
                config=final_config,
                execution_mode='live',
                data_provider=data_provider,
                **components
            )
            
            # 8. Store running strategy
            self.running_strategies[request_id] = {
                'request': request,
                'config': final_config,
                'strategy_engine': strategy_engine,
                'status': 'running',
                'started_at': datetime.utcnow(),
                'last_heartbeat': datetime.utcnow(),
                'total_pnl': 0.0,
                'total_trades': 0,
                'current_drawdown': 0.0
            }
            
            # 9. Start live trading asynchronously
            asyncio.create_task(self._execute_live_trading(request_id, strategy_engine, request))
            
            logging.info(f"Live trading {request_id} started for strategy {request.strategy_name}")
            return request_id
            
        except Exception as e:
            logging.error(f"Failed to start live trading {request_id}: {e}")
            raise
    
    def _validate_request(self, request: LiveTradingRequest):
        """Validate live trading request parameters"""
        if not request.strategy_name:
            raise ValueError("strategy_name cannot be empty")
        
        if not request.initial_capital or request.initial_capital <= 0:
            raise ValueError("initial_capital must be positive")
        
        if request.share_class not in ['USDT', 'ETH']:
            raise ValueError("share_class must be 'USDT' or 'ETH'")
        
        if not request.risk_limits:
            raise ValueError("risk_limits are required for live trading")
        
        # Validate risk limits
        required_risk_limits = ['max_drawdown', 'max_daily_loss']
        for limit in required_risk_limits:
            if limit not in request.risk_limits:
                raise ValueError(f"risk_limits.{limit} is required")
    
    def _slice_config(self, strategy_name: str) -> Dict[str, Any]:
        """
        Slice config for strategy mode (never modifies global config).
        
        Parameters:
        - strategy_name: Strategy mode name
        
        Returns:
        - Dict: Mode-specific config slice
        """
        try:
            return self.config_manager.get_complete_config(mode=strategy_name)
        except Exception as e:
            logging.error(f"Failed to slice config for strategy {strategy_name}: {e}")
            raise ValueError(f"Config slicing failed for strategy {strategy_name}: {e}")
    
    def _apply_overrides(self, config_slice: Dict[str, Any], overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply overrides to config slice (never modifies global config).
        
        Parameters:
        - config_slice: Mode-specific config
        - overrides: Request overrides
        
        Returns:
        - Dict: Config with overrides applied
        """
        if not overrides:
            return config_slice.copy()
        
        # Deep copy to avoid modifying original
        final_config = config_slice.copy()
        
        # Apply overrides recursively
        for key, value in overrides.items():
            if key in final_config and isinstance(final_config[key], dict) and isinstance(value, dict):
                final_config[key].update(value)
            else:
                final_config[key] = value
        
        return final_config
    
    def _create_data_provider(self, config: Dict[str, Any], request: LiveTradingRequest) -> BaseDataProvider:
        """
        Create fresh data provider using factory pattern.
        
        Parameters:
        - config: Complete configuration
        - request: Live trading request
        
        Returns:
        - BaseDataProvider: Fresh data provider instance
        """
        try:
            # Use DataProviderFactory to create mode-specific data provider
            data_provider = DataProviderFactory.create(
                mode=request.strategy_name,
                execution_mode='live',
                config=config
            )
            
            logging.info(f"Created {request.strategy_name} data provider for live trading")
            return data_provider
            
        except Exception as e:
            logging.error(f"Failed to create data provider for {request.strategy_name}: {e}")
            raise RuntimeError(f"Data provider creation failed: {e}")
    
    def _create_components(self, config: Dict[str, Any], data_provider: BaseDataProvider) -> Dict[str, Any]:
        """
        Create fresh component instances using factory pattern.
        
        Parameters:
        - config: Complete configuration
        - data_provider: Data provider instance
        
        Returns:
        - Dict[str, Any]: Dictionary of component instances
        """
        try:
            # Use ComponentFactory to create all components
            components = ComponentFactory.create_all(
                config=config,
                execution_mode='live',
                data_provider=data_provider
            )
            
            logging.info(f"Created {len(components)} components for live trading")
            return components
            
        except Exception as e:
            logging.error(f"Failed to create components: {e}")
            raise RuntimeError(f"Component creation failed: {e}")
    
    async def _execute_live_trading(self, request_id: str, strategy_engine: EventDrivenStrategyEngine, request: LiveTradingRequest):
        """Execute live trading and handle monitoring"""
        try:
            # Start live trading execution
            await strategy_engine.run_live()
            
            # Move to completed
            if request_id in self.running_strategies:
                strategy_info = self.running_strategies.pop(request_id)
                strategy_info.update({
                    'status': 'completed',
                    'completed_at': datetime.utcnow()
                })
                self.completed_strategies[request_id] = strategy_info
            
            logging.info(f"Live trading {request_id} completed successfully")
            
        except Exception as e:
            logging.error(f"Live trading {request_id} failed: {e}")
            
            # Move to completed with error
            if request_id in self.running_strategies:
                strategy_info = self.running_strategies.pop(request_id)
                strategy_info.update({
                    'status': 'failed',
                    'completed_at': datetime.utcnow(),
                    'error': str(e)
                })
                self.completed_strategies[request_id] = strategy_info
    
    async def stop_live_trading(self, request_id: str) -> bool:
        """Stop live trading for specific request"""
        if request_id in self.running_strategies:
            strategy_info = self.running_strategies.pop(request_id)
            strategy_info.update({
                'status': 'stopped',
                'completed_at': datetime.utcnow()
            })
            self.completed_strategies[request_id] = strategy_info
            return True
        return False
    
    async def get_strategy_status(self, request_id: str) -> Dict[str, Any]:
        """Get current status of live trading strategy"""
        if request_id in self.running_strategies:
            strategy_info = self.running_strategies[request_id]
            return {
                'request_id': request_id,
                'status': 'running',
                'started_at': strategy_info['started_at'].isoformat(),
                'last_heartbeat': strategy_info['last_heartbeat'].isoformat(),
                'total_pnl': strategy_info['total_pnl'],
                'total_trades': strategy_info['total_trades'],
                'current_drawdown': strategy_info['current_drawdown']
            }
        elif request_id in self.completed_strategies:
            strategy_info = self.completed_strategies[request_id]
            return {
                'request_id': request_id,
                'status': strategy_info['status'],
                'started_at': strategy_info['started_at'].isoformat(),
                'completed_at': strategy_info['completed_at'].isoformat(),
                'error': strategy_info.get('error')
            }
        else:
            raise ValueError(f"Strategy {request_id} not found")
    
    async def check_risk_limits(self, request_id: str) -> Dict[str, Any]:
        """Check if risk limits are being breached"""
        if request_id not in self.running_strategies:
            raise ValueError(f"Strategy {request_id} not found")
        
        strategy_info = self.running_strategies[request_id]
        request = strategy_info['request']
        
        breaches = []
        
        # Check max drawdown
        max_drawdown = request.risk_limits.get('max_drawdown')
        if max_drawdown is not None:
            current_drawdown = abs(strategy_info['current_drawdown'])
            if current_drawdown > max_drawdown:
                breaches.append({
                    'type': 'max_drawdown',
                    'limit': max_drawdown,
                    'current': current_drawdown,
                    'breach_pct': ((current_drawdown - max_drawdown) / max_drawdown) * 100
                })
        
        # Check max daily loss
        max_daily_loss = request.risk_limits.get('max_daily_loss')
        if max_daily_loss is not None:
            current_pnl = strategy_info['total_pnl']
            if current_pnl < -max_daily_loss:
                breaches.append({
                    'type': 'max_daily_loss',
                    'limit': max_daily_loss,
                    'current': abs(current_pnl),
                    'breach_pct': ((abs(current_pnl) - max_daily_loss) / max_daily_loss) * 100
                })
        
        if breaches:
            return {
                'status': 'breach_detected',
                'breaches': breaches,
                'action_required': True
            }
        else:
            return {
                'status': 'within_limits',
                'breaches': [],
                'action_required': False
            }
    
    async def emergency_stop(self, request_id: str, reason: str = "Emergency stop") -> bool:
        """Emergency stop a live trading strategy"""
        logging.warning(f"Emergency stop requested for {request_id}: {reason}")
        
        # Stop the strategy
        success = await self.stop_live_trading(request_id)
        
        if success and request_id in self.completed_strategies:
            # Add emergency stop info
            self.completed_strategies[request_id]['emergency_stop'] = {
                'reason': reason,
                'stopped_at': datetime.utcnow()
            }
        
        return success
```

### Integration with Factory Pattern

```python
# Example usage showing factory-based initialization
class LiveTradingService:
    def __init__(self, global_config: Dict[str, Any], config_manager: ConfigManager):
        # ... initialization ...
        
        # Factory-based component creation
        self.data_provider_factory = DataProviderFactory()
        self.component_factory = ComponentFactory()
        
        logging.info("LiveTradingService initialized with factory pattern")
    
    def _create_data_provider(self, config: Dict[str, Any], request: LiveTradingRequest) -> BaseDataProvider:
        """Create data provider using factory pattern"""
        return self.data_provider_factory.create(
            mode=request.strategy_name,
            execution_mode='live',
            config=config
        )
    
    def _create_components(self, config: Dict[str, Any], data_provider: BaseDataProvider) -> Dict[str, Any]:
        """Create components using factory pattern"""
        return self.component_factory.create_all(
            config=config,
            execution_mode='live',
            data_provider=data_provider
        )
```

## Data Provider Queries

### Market Data Queries
- **prices**: Real-time market prices for all tokens
- **orderbook**: Real-time order book data
- **funding_rates**: Real-time funding rates
- **liquidity**: Real-time liquidity data

### Protocol Data Queries
- **protocol_rates**: Real-time lending/borrowing rates
- **stake_rates**: Real-time staking rewards and rates
- **protocol_balances**: Real-time protocol balances

### Data NOT Available from DataProvider
- **Live trading results** - handled by Results Store
- **Component state** - handled by individual components
- **Execution results** - handled by execution components

## Data Access Pattern

### Query Pattern
```python
def start_live_trading(self, request: LiveTradingRequest):
    # Create fresh DataProvider for live trading
    data_provider = self._create_data_provider(request)
    
    # Load real-time data sources
    data = data_provider.load_live_data()
    
    return data
```

### Data Dependencies
- **Real-time Data**: Prices, orderbook, funding rates, liquidity
- **Protocol Data**: Real-time lending rates, staking rates, protocol balances
- **Strategy Config**: Strategy mode configuration and overrides

## Mode-Aware Behavior

### Backtest Mode
```python
def start_live_trading(self, request: LiveTradingRequest):
    if self.execution_mode == 'backtest':
        # Backtest mode not supported for live trading service
        raise ValueError("Live trading service only supports live mode")
```

### Live Mode
```python
def start_live_trading(self, request: LiveTradingRequest):
    elif self.execution_mode == 'live':
        # Start live trading with real-time data
        return self._start_live_trading_internal(request)
```

## Event Logging Requirements

### Component Event Log File
**Separate log file** for this component's events:
- **File**: `logs/events/live_trading_service_events.jsonl`
- **Format**: JSON Lines (one event per line)
- **Rotation**: Daily rotation, keep 30 days
- **Purpose**: Component-specific audit trail

### Event Logging via EventLogger
All events logged through centralized EventLogger:

```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='[event_type]',
    component='LiveTradingService',
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
    component='LiveTradingService',
    data={
        'execution_mode': self.execution_mode,
        'max_concurrent': self.max_concurrent,
        'config_hash': hash(str(self.global_config))
    }
)
```

#### 2. State Updates (Every start_live_trading() Call)
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='state_update',
    component='LiveTradingService',
    data={
        'request_id': request_id,
        'strategy_name': request.strategy_name,
        'running_strategies': len(self.running_strategies),
        'processing_time_ms': processing_time
    }
)
```

#### 3. Error Events
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='error',
    component='LiveTradingService',
    data={
        'error_code': 'LTS-001',
        'error_message': str(e),
        'stack_trace': traceback.format_exc(),
        'error_severity': 'CRITICAL|HIGH|MEDIUM|LOW'
    }
)
```

#### 4. Component-Specific Critical Events
- **Live Trading Failed**: When live trading execution fails
- **Config Slicing Failed**: When config slicing fails
- **Component Creation Failed**: When component creation fails

### Event Retention & Output Formats

#### Dual Logging Approach
**Both formats are used**:
1. **JSON Lines (Iterative)**: Write events to component-specific JSONL files during execution
   - **Purpose**: Real-time monitoring during live trading
   - **Location**: `logs/events/live_trading_service_events.jsonl`
   - **When**: Events written as they occur (buffered for performance)
   
2. **CSV Export (Final)**: Comprehensive CSV export at Results Store stage
   - **Purpose**: Final analysis, spreadsheet compatibility
   - **Location**: `results/[strategy_id]/events.csv`
   - **When**: At strategy completion or on-demand

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

### Component Error Code Prefix: LTS
All LiveTradingService errors use the `LTS` prefix.

### Error Code Registry
**Source**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`

All error codes registered with:
- **code**: Unique error code
- **component**: Component name
- **severity**: CRITICAL | HIGH | MEDIUM | LOW
- **message**: Human-readable error message
- **resolution**: How to resolve

### Component Error Codes

#### LTS-001: Live Trading Failed (HIGH)
**Description**: Failed to execute live trading
**Cause**: Component failures, API issues, configuration errors
**Recovery**: Retry live trading, check configuration, verify API connectivity
```python
raise ComponentError(
    error_code='LTS-001',
    message='Live trading execution failed',
    component='LiveTradingService',
    severity='HIGH'
)
```

#### LTS-002: Config Slicing Failed (HIGH)
**Description**: Failed to slice configuration for strategy
**Cause**: Invalid strategy name, missing config, configuration errors
**Recovery**: Check strategy name, verify configuration, fix config issues
```python
raise ComponentError(
    error_code='LTS-002',
    message='Config slicing failed',
    component='LiveTradingService',
    severity='HIGH'
)
```

#### LTS-003: Component Creation Failed (CRITICAL)
**Description**: Failed to create component instances
**Cause**: Component initialization failures, dependency issues, resource constraints
**Recovery**: Immediate action required, check system resources, restart if necessary
```python
raise ComponentError(
    error_code='LTS-003',
    message='Component creation failed',
    component='LiveTradingService',
    severity='CRITICAL'
)
```

### Structured Error Handling Pattern

#### Error Raising
```python
from backend.src.basis_strategy_v1.core.error_codes.exceptions import ComponentError

try:
    result = self._start_live_trading_internal(request)
except Exception as e:
    # Log error event
    self.event_logger.log_event(
        timestamp=timestamp,
        event_type='error',
        component='LiveTradingService',
        data={
            'error_code': 'LTS-001',
            'error_message': str(e),
            'stack_trace': traceback.format_exc()
        }
    )
    
    # Raise structured error
    raise ComponentError(
        error_code='LTS-001',
        message=f'LiveTradingService failed: {str(e)}',
        component='LiveTradingService',
        severity='HIGH',
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
        component_name='LiveTradingService',
        checker=self._health_check
    )

def _health_check(self) -> Dict:
    """Component-specific health check."""
    return {
        'status': 'healthy' | 'degraded' | 'unhealthy',
        'last_update': self.last_trading_timestamp,
        'errors': self.recent_errors[-10:],  # Last 10 errors
        'metrics': {
            'update_count': self.update_count,
            'avg_processing_time_ms': self.avg_processing_time,
            'error_rate': self.error_count / max(self.update_count, 1),
            'running_strategies': len(self.running_strategies),
            'strategy_status': self.strategy_status,
            'memory_usage_mb': self._get_memory_usage()
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
- [ ] All 18 sections present and complete
- [ ] Environment Variables section documents system-level and component-specific variables
- [ ] Config Fields Used section documents universal and component-specific config
- [ ] Data Provider Queries section documents real-time data queries
- [ ] Event Logging Requirements section documents component-specific JSONL file
- [ ] Event Logging Requirements section documents dual logging (JSONL + CSV)
- [ ] Error Codes section has structured error handling pattern
- [ ] Error Codes section references health integration
- [ ] Health integration documented with UnifiedHealthManager
- [ ] Component-specific log file documented (`logs/events/live_trading_service_events.jsonl`)

### Section Order Validation
- [ ] Purpose (section 1)
- [ ] Responsibilities (section 2)
- [ ] State (section 3)
- [ ] Component References (Set at Init) (section 4)
- [ ] Environment Variables (section 5)
- [ ] Config Fields Used (section 6)
- [ ] Data Provider Queries (section 7)
- [ ] Core Methods (section 8)
- [ ] Data Access Pattern (section 9)
- [ ] Mode-Aware Behavior (section 10)
- [ ] Event Logging Requirements (section 11)
- [ ] Error Codes (section 12)
- [ ] Quality Gates (section 13)
- [ ] Integration Points (section 14)
- [ ] Code Structure Example (section 15)
- [ ] Related Documentation (section 16)

### Implementation Status
- [ ] Backend implementation exists and matches spec
- [ ] All required methods implemented
- [ ] Error handling follows structured pattern
- [ ] Health integration implemented
- [ ] Event logging implemented

## Core Methods

### start_live_trading(request: LiveTradingRequest) -> str
Start live trading with fresh component instances.

Parameters:
- request: LiveTradingRequest with strategy_name, config_overrides

Returns:
- str: Request ID for tracking

Behavior:
1. Slice config for strategy_name mode
2. Apply request overrides to slice
3. Create fresh DataProvider with live APIs
4. Create fresh component instances with references
5. Start live trading via EventDrivenStrategyEngine
6. Manage continuous execution

### stop_live_trading(request_id: str) -> bool
Stop live trading for specific request.

Parameters:
- request_id: Request ID to stop

Returns:
- bool: Success status

### get_strategy_status(request_id: str) -> Dict
Get current status of live trading strategy.

Parameters:
- request_id: Request ID

Returns:
- Dict: Strategy execution status

---

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) <!-- Link is valid --> - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides
- **API Documentation**: [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) - Live trading API endpoints and integration patterns

---

## 🎯 **Purpose**

Orchestrate live trading using the EventDrivenStrategyEngine with real execution, risk management, and continuous monitoring.

**Key Principles**:
- **Real Execution**: Use real APIs and execution interfaces for live trading
- **Tight Loop Integration**: Implements tight loop reconciliation for execution verification
- **Position Reconciliation**: Verifies position updates match execution expectations
- **Risk Management**: Continuous risk limit monitoring and emergency stop capabilities
- **Background Execution**: Asynchronous strategy execution with monitoring
- **Heartbeat Monitoring**: Track strategy health and detect failures
- **Emergency Controls**: Emergency stop and risk limit breach handling
- **Performance Tracking**: Real-time performance metrics and P&L tracking

---

## 🏗️ **Architecture**

### **API Integration**

**Primary Endpoints**:
- **POST /api/v1/live/start**: Start live trading strategy
- **GET /api/v1/live/status**: Check live trading status
- **POST /api/v1/live/stop**: Stop live trading strategy
- **GET /api/v1/live/performance**: Get real-time performance metrics
- **POST /api/v1/live/emergency-stop**: Emergency stop all trading

**Integration Pattern**:
1. **Strategy Initialization**: Start live trading with strategy configuration
2. **Continuous Monitoring**: Real-time position and risk monitoring
3. **Execution Management**: Orchestrate EventDrivenStrategyEngine with live execution
4. **Status Updates**: Provide real-time status and performance metrics
5. **Emergency Controls**: Emergency stop and risk limit breach handling
6. **Performance Tracking**: Real-time P&L and performance analytics

**Cross-Reference**: [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) - Live trading API endpoints (lines 307-606)

## 📦 **Component Structure**

### **Core Classes**

#### **LiveTradingService**
Main service class that orchestrates live trading execution.

#### **LiveTradingRequest**
Request object containing all live trading parameters.

#### **LiveTradingResult**
Result object containing live trading execution results.

---

## 📊 **Data Structures**

### **LiveTradingRequest**
```python
{
    'strategy_name': str,
    'initial_capital': Decimal,
    'share_class': str,
    'config_overrides': Optional[Dict[str, Any]],
    'risk_limits': Dict[str, Any],
    'monitoring_enabled': bool
}
```

### **LiveTradingResult**
```python
{
    'request_id': str,
    'status': 'running' | 'completed' | 'failed' | 'stopped',
    'started_at': datetime,
    'completed_at': Optional[datetime],
    'performance_metrics': Dict[str, Any],
    'risk_metrics': Dict[str, Any],
    'error': Optional[str]
}
```

---

## 🔗 **Integration with Other Components**

### **Component Dependencies**
- **ConfigManager**: Load and merge strategy configurations
- **DataProviderFactory**: Create data provider for live mode
- **EventDrivenStrategyEngine**: Execute live trading using engine
- **Risk Monitor**: Continuous risk limit monitoring
- **Health System**: Monitor strategy health and detect failures

### **API Integration**
- **Live Trading API**: Receive live trading requests from frontend
- **Status API**: Provide live trading status and results
- **Health API**: Monitor live trading service health
- **Emergency API**: Emergency stop and risk limit breach handling

---

## 💻 **Implementation**

### **Service Initialization**
```python
class LiveTradingService:
    def __init__(self):
        self.running_strategies = {}
        self.completed_strategies = {}
        self.config_manager = ConfigManager()
        self.data_provider_factory = DataProviderFactory()
        self.risk_monitor = RiskMonitor()
        self.health_monitor = HealthMonitor()
```

### **Live Trading Execution**
```python
async def start_live_trading(self, request: LiveTradingRequest) -> str:
    """Start live trading using Phase 3 architecture."""
    request_id = str(uuid.uuid4())
    
    try:
        # 1. Validate request parameters
        self._validate_request(request)
        
        # 2. Load configuration
        config = self.config_manager.get_complete_config(mode=request.strategy_name)
        
        # 3. Create data provider
        data_provider = self.data_provider_factory.create('live', config)
        
        # 4. Initialize engine
        engine = EventDrivenStrategyEngine(config, 'live', data_provider)
        
        # 5. Start background execution
        task = asyncio.create_task(self._execute_live_trading(engine, request))
        self.running_strategies[request_id] = task
        
        return request_id
        
    except Exception as e:
        self._handle_error(request_id, e)
        raise
```

---

## 🧪 **Testing**

### **Live Trading Tests**
```python
def test_live_trading_request_validation():
    """Test live trading request validation."""
    service = LiveTradingService()
    
    # Valid request
    request = LiveTradingRequest(
        strategy_name='pure_lending',
        initial_capital=Decimal('100000'),
        share_class='USDT',
        risk_limits={'max_drawdown': 0.05}
    )
    
    request_id = await service.start_live_trading(request)
    assert request_id is not None

def test_live_trading_execution():
    """Test live trading execution flow."""
    service = LiveTradingService()
    request = create_valid_request()
    
    request_id = await service.start_live_trading(request)
    
    # Check status
    status = await service.get_status(request_id)
    assert status['status'] in ['running', 'completed', 'failed']
    
    # Check risk monitoring
    risk_status = await service.get_risk_status(request_id)
    assert risk_status is not None

def test_emergency_stop():
    """Test emergency stop functionality."""
    service = LiveTradingService()
    request = create_valid_request()
    
    request_id = await service.start_live_trading(request)
    
    # Emergency stop
    success = await service.emergency_stop(request_id)
    assert success is True
    
    # Check status
    status = await service.get_status(request_id)
    assert status['status'] == 'stopped'
```

---

## 🏗️ **Architecture**

### **Service Flow**

```
API Request → Request Validation → Config Creation → Engine Initialization → Background Execution → Monitoring → Risk Management
```

### **Core Classes**

#### **LiveTradingService**
Main service class that orchestrates live trading execution.

#### **LiveTradingRequest**
Request object containing all live trading parameters:
- `strategy_name`: Strategy to execute
- `initial_capital`: Starting capital amount
- `share_class`: Share class ('USDT' or 'ETH')
- `config_overrides`: Optional configuration overrides
- `risk_limits`: Risk management limits and thresholds

---

## 🔧 **Key Methods**

### **Request Management**

```python
def create_request(self, strategy_name: str, initial_capital: Decimal, share_class: str,
                  config_overrides: Dict[str, Any] = None, 
                  risk_limits: Dict[str, Any] = None) -> LiveTradingRequest:
    """Create a live trading request with validation."""
```

### **Live Trading Execution**

```python
async def start_live_trading(self, request: LiveTradingRequest) -> str:
    """
    Start live trading asynchronously.
    
    Flow:
    1. Validate request parameters and risk limits
    2. Load configuration using ConfigManager
    3. Initialize EventDrivenStrategyEngine
    4. Start background execution task
    5. Begin monitoring and risk management
    """
```

### **Monitoring and Control**

```python
async def stop_live_trading(self, request_id: str) -> bool:
    """Stop a running live trading strategy."""

async def get_status(self, request_id: str) -> Dict[str, Any]:
    """Get the status of a live trading strategy."""

async def get_performance_metrics(self, request_id: str) -> Optional[Dict[str, Any]]:
    """Get performance metrics for a live trading strategy."""

async def check_risk_limits(self, request_id: str) -> Dict[str, Any]:
    """Check if risk limits are being breached."""

async def emergency_stop(self, request_id: str, reason: str = "Emergency stop") -> bool:
    """Emergency stop a live trading strategy."""
```

---

## 🔄 **Data Flow**

### **Request Processing**

1. **API Request**: Receive live trading request from API
2. **Validation**: Validate request parameters and risk limits
3. **Config Loading**: Load strategy configuration using ConfigManager
4. **Config Merging**: Apply request overrides to base configuration
5. **Engine Init**: Initialize EventDrivenStrategyEngine with live execution mode
6. **Background Execution**: Start strategy execution in background task
7. **Monitoring**: Continuous monitoring of strategy health and performance
8. **Risk Management**: Continuous risk limit checking and breach handling

### **Live Trading Client Validation**

Following [Live Trading Quality Gates](QUALITY_GATES.md) <!-- Redirected from 12_live_trading_quality_gates.md - live trading quality gates are documented in quality gates -->:

#### **Client Requirement Validation**
- **Mode-based client requirements**: Each strategy mode requires specific clients
- **Configuration-driven**: Client requirements determined by config YAML files
- **Environment-specific**: Testnet vs production client configurations
- **Venue-specific**: Different venues require different clients

#### **Client Availability Validation**
- **API connectivity**: All required APIs must be accessible
- **Authentication**: All required authentication must be valid
- **Rate limits**: Rate limits must be within acceptable ranges
- **Client initialization**: All clients must initialize successfully

#### **Environment-Specific Validation**
- **Testnet environment**: All clients must connect to testnet endpoints
- **Production environment**: All clients must connect to production endpoints
- **Environment-specific configuration**: Testnet vs production must be correctly configured

### **Configuration Integration**

```python
# Create config for live trading using config infrastructure
config = self._create_config(request)

# Add request-specific overrides for live trading
base_config.update({
    'share_class': request.share_class,
    'initial_capital': float(request.initial_capital),
    'execution_mode': 'live',
    'live_trading': {
        'initial_capital': float(request.initial_capital),
        'risk_limits': request.risk_limits,
        'started_at': datetime.utcnow().isoformat()
    }
})
```

**Configuration Details**: See [19_CONFIGURATION.md](19_CONFIGURATION.md) <!-- Link is valid --> <!-- Link is valid --> for comprehensive configuration management.

### **Singleton Pattern Requirements**

Following [Singleton Pattern Requirements](REFERENCE_ARCHITECTURE_CANONICAL.md#2-singleton-pattern-task-13) <!-- Redirected from 13_singleton_pattern_requirements.md - singleton pattern is documented in canonical principles -->:

#### **Single Instance Per Component**
- **Each component**: Must be a SINGLE instance across the entire run
- **No duplication**: Never initialize the same component twice in different places
- **Shared state**: All components share the same state and data

#### **Shared Configuration and Data Provider**
- **Single config instance**: All components must share the SAME config instance
- **Single data provider**: All components must share the SAME data provider instance
- **Synchronized data flows**: All components use the same data source

### **Venue-Based Execution Architecture**

Following [VENUE_ARCHITECTURE.md](../VENUE_ARCHITECTURE.md) <!-- Link is valid -->:

#### **Live Mode Venue Execution**
- **Real execution**: Using external APIs (testnet or production)
- **Real delays**: Transaction confirmations and API rate limits
- **Retry logic**: Exponential backoff for failed operations
- **External interfaces**: Provide data to position monitor

#### **Environment-Specific Venue Configuration**
- **BASIS_ENVIRONMENT**: Controls venue credential routing (dev/staging/prod)
- **BASIS_EXECUTION_MODE**: Controls venue execution behavior (backtest simulation vs live execution)
- **Venue credentials**: Environment-specific credentials from env.unified
- **Testnet vs production**: Different endpoints and networks based on environment

---

## 🔗 **Dependencies**

### **Core Dependencies**

- **EventDrivenStrategyEngine**: [15_EVENT_DRIVEN_STRATEGY_ENGINE.md](15_EVENT_DRIVEN_STRATEGY_ENGINE.md) <!-- Link is valid --> - Main orchestration engine
- **Data Provider**: [09_DATA_PROVIDER.md](09_DATA_PROVIDER.md) <!-- Link is valid --> - Live data access
- **Configuration**: [19_CONFIGURATION.md](19_CONFIGURATION.md) <!-- Link is valid --> <!-- Link is valid --> - Strategy configuration management

### **Infrastructure Dependencies**

- **ConfigManager**: Unified configuration management
- **Live Data Provider**: Real-time market data access
- **Execution Interfaces**: Real execution interfaces for live trading

---

## ⚠️ **Error Codes**

### **Live Trading Service Error Codes**

| Code | Description | Severity |
|------|-------------|----------|
| **LT-001** | Live trading request validation failed | HIGH |
| **LT-002** | Config creation failed | HIGH |
| **LT-003** | Strategy engine initialization failed | CRITICAL |
| **LT-004** | Live trading execution failed | CRITICAL |
| **LT-005** | Live trading monitoring failed | MEDIUM |
| **LT-006** | Live trading stop failed | MEDIUM |
| **LT-007** | Risk check failed | HIGH |

### **Error Handling**

```python
# Request validation
errors = request.validate()
if errors:
    logger.error(f"[LT-001] Live trading request validation failed: {', '.join(errors)}")
    raise ValueError(f"Invalid request: {', '.join(errors)}")

# Engine initialization
try:
    strategy_engine = EventDrivenStrategyEngine(config)
except Exception as e:
    logger.error(f"[LT-003] Strategy engine initialization failed: {e}")
    raise

# Live trading execution
try:
    await strategy_engine.run_live()
except Exception as e:
    logger.error(f"[LT-004] Live trading {request_id} failed: {e}", exc_info=True)
    # Update status to failed but continue monitoring
```

**Error System Details**: See [17_HEALTH_ERROR_SYSTEMS.md](17_HEALTH_ERROR_SYSTEMS.md) <!-- Link is valid --> for comprehensive error handling.

---

## 🛡️ **Risk Management**

### **Risk Limits**

```python
risk_limits = {
    'max_drawdown': 0.10,        # 10% maximum drawdown
    'max_position_size': 100000,  # Maximum position size
    'max_daily_loss': 5000,      # Maximum daily loss
    'health_factor_threshold': 1.2,  # Minimum health factor
    'margin_ratio_threshold': 0.2    # Minimum margin ratio
}
```

### **Risk Monitoring**

```python
async def check_risk_limits(self, request_id: str) -> Dict[str, Any]:
    """Check if risk limits are being breached."""
    
    breaches = []
    
    # Check max drawdown
    max_drawdown = risk_limits.get('max_drawdown')
    if max_drawdown is not None:
        current_drawdown = abs(strategy_info['current_drawdown'])
        if current_drawdown > max_drawdown:
            breaches.append({
                'type': 'max_drawdown',
                'limit': max_drawdown,
                'current': current_drawdown,
                'breach_pct': ((current_drawdown - max_drawdown) / max_drawdown) * 100
            })
    
    # Check other risk limits...
    
    if breaches:
        return {
            'status': 'breach_detected',
            'breaches': breaches,
            'action_required': True
        }
    else:
        return {
            'status': 'within_limits',
            'breaches': [],
            'action_required': False
        }
```

### **Emergency Stop**

```python
async def emergency_stop(self, request_id: str, reason: str = "Emergency stop") -> bool:
    """Emergency stop a live trading strategy."""
    logger.warning(f"Emergency stop requested for {request_id}: {reason}")
    
    # Stop the strategy
    success = await self.stop_live_trading(request_id)
    
    if success and request_id in self.completed_strategies:
        # Add emergency stop info
        self.completed_strategies[request_id]['emergency_stop'] = {
            'reason': reason,
            'stopped_at': datetime.utcnow()
        }
    
    return success
```

---

## 📊 **Performance Monitoring**

### **Performance Metrics**

```python
async def get_performance_metrics(self, request_id: str) -> Optional[Dict[str, Any]]:
    """Get performance metrics for a live trading strategy."""
    
    # Calculate performance metrics
    initial_capital = strategy_info['request'].initial_capital
    current_pnl = strategy_info['total_pnl']
    current_value = float(initial_capital) + current_pnl
    return_pct = (current_pnl / float(initial_capital)) * 100
    
    return {
        'initial_capital': float(initial_capital),
        'current_value': current_value,
        'total_pnl': current_pnl,
        'return_pct': return_pct,
        'total_trades': strategy_info['total_trades'],
        'current_drawdown': strategy_info['current_drawdown'],
        'uptime_hours': (datetime.utcnow() - strategy_info['started_at']).total_seconds() / 3600,
        'engine_status': engine_status,
        'last_heartbeat': strategy_info['last_heartbeat']
    }
```

### **Health Monitoring**

```python
async def health_check(self) -> Dict[str, Any]:
    """Perform health check on all running strategies."""
    health_status = {
        'total_strategies': len(self.running_strategies),
        'healthy_strategies': 0,
        'unhealthy_strategies': 0,
        'strategies': []
    }
    
    current_time = datetime.utcnow()
    
    for request_id, strategy_info in self.running_strategies.items():
        last_heartbeat = strategy_info['last_heartbeat']
        time_since_heartbeat = (current_time - last_heartbeat).total_seconds()
        
        # Consider unhealthy if no heartbeat for more than 5 minutes
        is_healthy = time_since_heartbeat < 300
        
        if is_healthy:
            health_status['healthy_strategies'] += 1
        else:
            health_status['unhealthy_strategies'] += 1
        
        health_status['strategies'].append({
            'request_id': request_id,
            'strategy_name': strategy_info['request'].strategy_name,
            'is_healthy': is_healthy,
            'last_heartbeat': last_heartbeat,
            'time_since_heartbeat_seconds': time_since_heartbeat
        })
    
    return health_status
```

---

## 🧪 **Usage Examples**

### **Basic Live Trading**

```python
from basis_strategy_v1.core.services.live_service import LiveTradingService
from decimal import Decimal

# Create service
service = LiveTradingService()

# Create request
request = service.create_request(
    strategy_name='pure_lending',
    initial_capital=Decimal('100000'),
    share_class='USDT',
    risk_limits={
        'max_drawdown': 0.05,  # 5% max drawdown
        'max_daily_loss': 1000  # $1000 max daily loss
    }
)

# Start live trading
request_id = await service.start_live_trading(request)
print(f"Live trading started: {request_id}")

# Monitor status
status = await service.get_status(request_id)
print(f"Status: {status['status']}")
print(f"Total trades: {status['total_trades']}")
print(f"Total P&L: {status['total_pnl']}")
```

### **Risk Management**

```python
# Check risk limits
risk_check = await service.check_risk_limits(request_id)
if risk_check['status'] == 'breach_detected':
    print("Risk limit breached!")
    for breach in risk_check['breaches']:
        print(f"- {breach['type']}: {breach['current']:.2%} (limit: {breach['limit']:.2%})")
    
    # Emergency stop if needed
    if breach['breach_pct'] > 50:  # 50% over limit
        await service.emergency_stop(request_id, "Risk limit breach exceeded 50%")
```

### **Performance Monitoring**

```python
# Get performance metrics
metrics = await service.get_performance_metrics(request_id)
if metrics:
    print(f"Current value: ${metrics['current_value']:,.2f}")
    print(f"Total return: {metrics['return_pct']:.2%}")
    print(f"Uptime: {metrics['uptime_hours']:.1f} hours")
    print(f"Total trades: {metrics['total_trades']}")
```

### **Strategy Management**

```python
# Get all running strategies
running_strategies = await service.get_all_running_strategies()
print(f"Running strategies: {len(running_strategies)}")

for strategy in running_strategies:
    print(f"- {strategy['strategy_name']}: {strategy['status']}")

# Stop a strategy
success = await service.stop_live_trading(request_id)
if success:
    print("Strategy stopped successfully")
```

---

## 🔄 **Live vs Backtest Differences**

### **Execution Mode**

| Aspect | Backtest | Live Trading |
|--------|----------|--------------|
| **Data Source** | Historical CSV files | Real-time APIs |
| **Execution** | Simulated | Real trades |
| **Timing** | Historical timestamps | Real-time intervals |
| **Risk Management** | Post-hoc analysis | Real-time monitoring |
| **Error Handling** | Fail-fast | Retry with exponential backoff |
| **Monitoring** | Progress tracking | Heartbeat monitoring |

### **Configuration Differences**

```python
# Backtest configuration
backtest_config = {
    'execution_mode': 'backtest',
    'data': {'data_dir': 'data/'},
    'backtest': {
        'start_date': '2024-01-01',
        'end_date': '2024-12-31'
    }
}

# Live trading configuration
live_config = {
    'execution_mode': 'live',
    'live_trading': {
        'risk_limits': {...},
        'monitoring_interval': 60,
        'heartbeat_timeout': 300
    }
}
```

---

## 📋 **Implementation Status** ✅ **FULLY IMPLEMENTED**

- ✅ **Request Validation**: Comprehensive parameter and risk limit validation
- ✅ **Configuration Management**: Integration with ConfigManager for live trading configs
- ✅ **Engine Orchestration**: Proper EventDrivenStrategyEngine initialization for live mode
- ✅ **Background Execution**: Asynchronous strategy execution with monitoring
- ✅ **Risk Management**: Continuous risk limit monitoring and emergency stop
- ✅ **Performance Tracking**: Real-time performance metrics and P&L tracking
- ✅ **Health Monitoring**: Heartbeat monitoring and health checks
- ✅ **Error Handling**: Comprehensive error handling with retry logic
- ✅ **State Management**: Running and completed strategy tracking
- ✅ **Emergency Controls**: Emergency stop and risk breach handling
- ✅ **Live Trading Client Validation**: Client requirement validation, API connectivity, authentication
- ✅ **Singleton Pattern**: Single instance per component with shared config and data provider
- ✅ **Venue-Based Execution**: Live mode venue execution with environment-specific configuration
- ✅ **Mode-Agnostic Architecture**: Components work for both backtest and live modes

---

## 🔧 **Current Implementation Status**

**Overall Completion**: 95% (Fully implemented and operational)

### **Core Functionality Status**
- ✅ **Working**: Request validation, configuration management, engine orchestration, background execution, risk management, performance tracking, health monitoring, error handling, state management, emergency controls, live trading client validation, singleton pattern, venue-based execution, mode-agnostic architecture
- ⚠️ **Partial**: None
- ❌ **Missing**: None
- 🔄 **Refactoring Needed**: Minor enhancements for production readiness

### **Architecture Compliance Status**
- ✅ **COMPLIANT**: Live trading service follows canonical architecture requirements
- **No Violations Found**: Component fully compliant with architectural principles

### **TODO Items and Refactoring Needs**
- **High Priority**:
  - None identified
- **Medium Priority**:
  - Advanced risk management with dynamic risk limit adjustment
  - Real-time alerts via WebSocket-based notifications
  - Portfolio management for multi-strategy coordination
- **Low Priority**:
  - Performance analytics with advanced performance attribution
  - Regulatory compliance with audit trails and compliance reporting

### **Quality Gate Status**
- **Current Status**: PASS
- **Failing Tests**: None
- **Requirements**: All requirements met
- **Integration**: Fully integrated with quality gate system

### **Task Completion Status**
- **Related Tasks**: 
  - [docs/QUALITY_GATES.md](../QUALITY_GATES.md) - Live Trading Quality Gates (95% complete - fully implemented)
  - [docs/QUALITY_GATES.md](../QUALITY_GATES.md) - Quality Gate Validation (95% complete - fully implemented)
- **Completion**: 95% complete overall
- **Blockers**: None
- **Next Steps**: Implement minor enhancements for production readiness

---

## 🎯 **Next Steps**

1. **Advanced Risk Management**: Dynamic risk limit adjustment
2. **Real-time Alerts**: WebSocket-based real-time notifications
3. **Portfolio Management**: Multi-strategy portfolio coordination
4. **Performance Analytics**: Advanced performance attribution
5. **Regulatory Compliance**: Audit trails and compliance reporting

## 🔍 **Quality Gate Validation**

Following [Quality Gate Validation](QUALITY_GATES.md) <!-- Redirected from 17_quality_gate_validation_requirements.md - quality gate validation is documented in quality gates -->:

### **Mandatory Quality Gate Validation**
**BEFORE CONSIDERING TASK COMPLETE**, you MUST:

1. **Run Live Trading Quality Gates**:
   ```bash
   python scripts/run_quality_gates.py --category e2e_strategies
   ```

2. **Verify Live Trading Client Validation**:
   - All required clients for strategy mode are available
   - All clients initialize successfully
   - All clients can connect to external services
   - Client configurations are valid and complete

3. **Verify Architecture Compliance**:
   - Singleton pattern: All components use single instances
   - Mode-agnostic: Components work for both backtest and live modes
   - Venue-based execution: Live mode venue execution works correctly

4. **Document Results**:
   - Live trading client validation results
   - Architecture compliance status
   - Any remaining issues or limitations

**DO NOT PROCEED TO NEXT TASK** until quality gates validate the live trading service is working correctly.

---

**Status**: Live Trading Service is complete and fully operational! 🎉



## Standardized Logging Methods

### log_structured_event(timestamp, event_type, level, message, component_name, data=None, correlation_id=None)
Log a structured event with standardized format.

**Parameters**:
- `timestamp`: Event timestamp (pd.Timestamp)
- `event_type`: Type of event (EventType enum)
- `level`: Log level (LogLevel enum)
- `message`: Human-readable message (str)
- `component_name`: Name of the component logging the event (str)
- `data`: Optional structured data dictionary (Dict[str, Any])
- `correlation_id`: Optional correlation ID for tracing (str)

**Returns**: None

### log_component_event(event_type, message, data=None, level=LogLevel.INFO)
Log a component-specific event with automatic timestamp and component name.

**Parameters**:
- `event_type`: Type of event (EventType enum)
- `message`: Human-readable message (str)
- `data`: Optional structured data dictionary (Dict[str, Any])
- `level`: Log level (defaults to INFO)

**Returns**: None

### log_performance_metric(metric_name, value, unit, data=None)
Log a performance metric.

**Parameters**:
- `metric_name`: Name of the metric (str)
- `value`: Metric value (float)
- `unit`: Unit of measurement (str)
- `data`: Optional additional context data (Dict[str, Any])

**Returns**: None

### log_error(error, context=None, correlation_id=None)
Log an error with standardized format.

**Parameters**:
- `error`: Exception object (Exception)
- `context`: Optional context data (Dict[str, Any])
- `correlation_id`: Optional correlation ID for tracing (str)

**Returns**: None

### log_warning(message, data=None, correlation_id=None)
Log a warning with standardized format.

**Parameters**:
- `message`: Warning message (str)
- `data`: Optional context data (Dict[str, Any])
- `correlation_id`: Optional correlation ID for tracing (str)

**Returns**: None

## Public API Methods

### check_component_health() -> Dict[str, Any]
**Purpose**: Check component health status for monitoring and diagnostics.

**Returns**:
```python
{
    'status': 'healthy' | 'degraded' | 'unhealthy',
    'error_count': int,
    'execution_mode': 'live',
    'active_strategies_count': int,
    'completed_trades_count': int,
    'component': 'LiveTradingService'
}
```

**Usage**: Called by health monitoring systems to track Live Trading Service status and performance.

### check_risk_limits() -> Dict[str, Any]
**Purpose**: Check current risk limits and exposure levels.

**Returns**: Dictionary containing risk limit status and current exposure levels

**Usage**: Called by external systems to monitor risk compliance during live trading.

### emergency_stop() -> Dict[str, Any]
**Purpose**: Immediately stop all live trading activities.

**Returns**: Dictionary containing emergency stop status and details

**Usage**: Called by external systems to halt all trading operations in emergency situations.

### get_status() -> Dict[str, Any]
**Purpose**: Get current status of the live trading service.

**Returns**: Dictionary containing service status information

**Usage**: Called by external systems to check service status and health.

### get_all_running_strategies() -> List[Dict[str, Any]]
**Purpose**: Get list of all currently running strategies.

**Returns**: List of dictionaries containing strategy information

**Usage**: Called by external systems to monitor active strategies.

### get_performance_metrics() -> Dict[str, Any]
**Purpose**: Get performance metrics for live trading.

**Returns**: Dictionary containing performance metrics and statistics

**Usage**: Called by external systems to retrieve trading performance data.

### check_emergency_stop_loss() -> Dict[str, Any]
**Purpose**: Check if emergency stop loss conditions are met.

**Returns**: Dictionary containing emergency stop loss status

**Usage**: Called by external systems to monitor stop loss conditions.

### health_check() -> Dict[str, Any]
**Purpose**: Perform comprehensive health check of the live trading service.

**Returns**: Dictionary containing detailed health status information

**Usage**: Called by external systems to perform comprehensive health monitoring.

## Related Documentation

### Component Specifications
- [15_EVENT_DRIVEN_STRATEGY_ENGINE.md](15_EVENT_DRIVEN_STRATEGY_ENGINE.md) - Strategy engine orchestration
- [13_BACKTEST_SERVICE.md](13_BACKTEST_SERVICE.md) - Backtest service
- [01_POSITION_MONITOR.md](01_POSITION_MONITOR.md) - Position tracking component
- [02_EXPOSURE_MONITOR.md](02_EXPOSURE_MONITOR.md) - Exposure monitoring component
- [03_RISK_MONITOR.md](03_RISK_MONITOR.md) - Risk monitoring component

### Architecture Documentation
- [../REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical principles
- [../CODE_STRUCTURE_PATTERNS.md](../CODE_STRUCTURE_PATTERNS.md) - Implementation patterns
- [../ARCHITECTURAL_DECISION_RECORDS.md](../ARCHITECTURAL_DECISION_RECORDS.md) - ADR-001 tight loop

### Configuration Documentation
- [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas
- [../MODES.md](../MODES.md) - Strategy mode definitions

*Last Updated: January 6, 2025*
