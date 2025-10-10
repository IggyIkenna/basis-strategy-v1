# Strategy Manager Component Specification

**Last Reviewed**: October 10, 2025

## Purpose
Mode-specific strategy brain that decides 5 standardized actions and breaks them down into sequential instruction blocks for Execution Manager.

## 📚 **Canonical Sources**

- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](../MODES.md) - Canonical strategy mode definitions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides
- **API Documentation**: [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) - Strategy selection endpoints and integration patterns

## Responsibilities
1. Decide 5 standardized actions (entry_full, entry_partial, exit_full, exit_partial, sell_dust)
2. Break down actions into sequential instruction blocks for Execution Manager
3. NO execution logic: Just instruction block creation
4. Mode-specific decision logic based on exposure, risk, and market data

## 🏗️ **API Integration**

**Strategy Selection Endpoints**:
- **GET /api/v1/strategies/**: List available strategy modes
- **GET /api/v1/strategies/{mode}/config**: Get strategy mode configuration
- **POST /api/v1/strategies/{mode}/validate**: Validate strategy configuration
- **GET /api/v1/strategies/{mode}/requirements**: Get venue and data requirements

**Integration Pattern**:
1. **Strategy Discovery**: API endpoints expose available strategy modes
2. **Configuration Management**: Strategy Manager provides mode-specific config templates
3. **Validation**: Validate strategy parameters before execution
4. **Requirements**: Provide venue and data requirements for each strategy mode
5. **Decision Logic**: Execute mode-specific decision logic during strategy execution

**Cross-Reference**: [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) - Strategy endpoints (lines 702-816)

## State
- current_action: str | None
- last_decision_timestamp: pd.Timestamp
- action_history: List[Dict] (for debugging)
- instruction_blocks_generated: int

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- exposure_monitor: ExposureMonitor (read-only access to state)
- risk_monitor: RiskMonitor (read-only access to state)
- data_provider: DataProvider (reference, query with timestamps)
- config: Dict (reference, never modified)
- execution_mode: str (BASIS_EXECUTION_MODE)

These references are stored in __init__ and used throughout component lifecycle.
Components NEVER receive these as method parameters during runtime.

## Environment Variables

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
None

### Environment Variable Access Pattern
```python
def __init__(self, ...):
    # Read env vars ONCE at initialization
    self.execution_mode = os.getenv('BASIS_EXECUTION_MODE', 'backtest')
    # NEVER read env vars during runtime loops
```

### Behavior NOT Determinable from Environment Variables
- Strategy decision logic (hard-coded algorithms)
- Action selection rules (hard-coded thresholds)
- Instruction block generation (hard-coded templates)

## Config Fields Used

### Universal Config (All Components)
- `strategy_mode`: str - e.g., 'eth_basis', 'pure_lending'
- `share_class`: str - 'usdt_stable' | 'eth_directional'
- `initial_capital`: float - Starting capital

### Component-Specific Config
- `rebalance_threshold`: float - Threshold for triggering rebalancing
  - **Usage**: Determines when to trigger rebalancing actions
  - **Default**: 0.05 (5%)
  - **Validation**: Must be > 0 and < 0.2

- `action_history_limit`: int - Maximum action history entries
  - **Usage**: Limits memory usage for action history
  - **Default**: 1000
  - **Validation**: Must be > 0

### Config Access Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    # Read config fields (NEVER modify)
    threshold = self.config.get('rebalance_threshold', 0.05)
```

### Behavior NOT Determinable from Config
- Strategy decision algorithms (hard-coded logic)
- Action selection rules (hard-coded thresholds)
- Instruction block templates (hard-coded structures)

## Data Provider Queries

### Data Types Requested
`data = self.data_provider.get_data(timestamp)`

#### Market Data
- `prices`: Dict[str, float] - Token prices in USD
  - **Tokens needed**: ETH, USDT, BTC, LST tokens
  - **Update frequency**: 1min
  - **Usage**: Strategy decision making and market analysis

### Query Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    data = self.data_provider.get_data(timestamp)
    prices = data['market_data']['prices']
```

### Data NOT Available from DataProvider
None - all data comes from DataProvider

## Configuration Parameters

### **Environment Variables**
- **BASIS_EXECUTION_MODE**: Controls execution behavior ('backtest' | 'live')
- **BASIS_ENVIRONMENT**: Controls credential routing ('dev' | 'staging' | 'production')
- **BASIS_DATA_MODE**: Controls data source ('csv' | 'db')

### **YAML Configuration**
**Mode Configuration** (from `configs/modes/*.yaml`):
- `mode`: Strategy mode identifier - determines strategy logic
- `share_class`: Share class ('USDT' | 'ETH') - affects strategy decisions
- `asset`: Primary asset ('BTC' | 'ETH') - affects strategy logic
- `target_apy`: Target APY (float) - used for strategy decisions
- `max_drawdown`: Maximum drawdown (float) - used for risk management
- `leverage_enabled`: Enable leverage (boolean) - affects strategy logic
- `target_ltv`: Target LTV ratio (float) - used for strategy decisions
- `hedge_venues`: List of hedge venues - used for strategy execution
- `hedge_allocation`: Hedge allocation per venue - used for strategy execution

**Venue Configuration** (from `configs/venues/*.yaml`):
- `venue`: Venue identifier - used for strategy execution
- `type`: Venue type ('cex' | 'dex' | 'onchain') - affects strategy logic
- `max_leverage`: Maximum leverage - used for strategy decisions
- `trading_fees`: Fee structure - used for cost calculations

**Share Class Configuration** (from `configs/share_classes/*.yaml`):
- `base_currency`: Base currency ('USDT' | 'ETH') - affects strategy decisions
- `risk_level`: Risk level ('low_to_medium' | 'medium_to_high') - affects strategy logic
- `market_neutral`: Market neutral flag (boolean) - affects strategy logic
- `supported_strategies`: List of supported strategies - used for validation

**Cross-Reference**: [CONFIGURATION.md](CONFIGURATION.md) - Complete configuration hierarchy
**Cross-Reference**: [ENVIRONMENT_VARIABLES.md](../ENVIRONMENT_VARIABLES.md) - Environment variable definitions

## 📦 **Component Structure**

### **Core Classes**

#### **StrategyManager**
Strategy execution and instruction generation system.

```python
class StrategyManager:
    def __init__(self, config: Dict, execution_mode: str, health_manager: UnifiedHealthManager):
        # Store references (never passed as runtime parameters)
        self.config = config
        self.execution_mode = execution_mode
        self.health_manager = health_manager
        
        # Initialize state
        self.strategies = {}
        self.last_execution_timestamp = None
        self.execution_count = 0
        
        # Register with health system
        self.health_manager.register_component(
            component_name='StrategyManager',
            checker=self._health_check
        )
```

## 📊 **Data Structures**

### **Strategy Registry**
```python
strategies: Dict[str, Strategy]
- Type: Dict[str, Strategy]
- Purpose: Registry of active strategies
- Keys: Strategy names (e.g., 'pure_lending', 'basis_trading')
- Values: Strategy instances
```

### **Execution Statistics**
```python
execution_count: int
- Type: int
- Purpose: Track number of executions
- Thread Safety: Atomic operations

last_execution_timestamp: pd.Timestamp
- Type: pd.Timestamp
- Purpose: Track last execution time
- Thread Safety: Single writer
```

## 🧪 **Testing**

### **Unit Tests**
- **Test Strategy Execution**: Verify strategy execution logic
- **Test Instruction Generation**: Verify instruction generation
- **Test Strategy Management**: Verify strategy management
- **Test Error Handling**: Verify structured error handling
- **Test Health Integration**: Verify health monitoring

### **Integration Tests**
- **Test Backend Integration**: Verify backend integration
- **Test Event Logging**: Verify event logging integration
- **Test Health Monitoring**: Verify health system integration
- **Test Performance**: Verify strategy execution performance

### **Test Coverage**
- **Target**: 80% minimum unit test coverage
- **Critical Paths**: 100% coverage for strategy operations
- **Error Paths**: 100% coverage for error handling
- **Health Paths**: 100% coverage for health monitoring

## ✅ **Success Criteria**

### **Functional Requirements**
- [ ] Strategy execution working
- [ ] Instruction generation operational
- [ ] Strategy management functional
- [ ] Error handling complete
- [ ] Health monitoring integrated

### **Performance Requirements**
- [ ] Strategy execution < 100ms
- [ ] Instruction generation < 50ms
- [ ] Strategy management < 10ms
- [ ] Memory usage < 100MB for strategies
- [ ] CPU usage < 10% during normal operations

### **Quality Requirements**
- [ ] 80% minimum test coverage
- [ ] All error codes documented
- [ ] Health integration complete
- [ ] Event logging operational
- [ ] Documentation complete

## 📅 **Last Reviewed**

**Last Reviewed**: October 10, 2025  
**Reviewer**: Component Spec Standardization  
**Status**: ✅ **18-SECTION FORMAT COMPLETE**

## Core Methods

### update_state(timestamp: pd.Timestamp, trigger_source: str, **kwargs)
Main entry point for strategy decision making.

Parameters:
- timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
- trigger_source: 'full_loop' | 'manual' | 'risk_trigger'
- **kwargs: Additional parameters (e.g., deposit_amount, withdrawal_amount)

Behavior:
1. Query data using: market_data = self.data_provider.get_data(timestamp)
2. Access other components via references: exposure = self.exposure_monitor.get_current_exposure()
3. Decide appropriate action based on current state
4. Break down action into instruction blocks
5. NO async/await: Synchronous execution only

Returns:
- List[Dict]: Sequential instruction blocks for Execution Manager

### decide_action(timestamp: pd.Timestamp, current_exposure: Dict, risk_metrics: Dict, market_data: Dict) -> str
Decide which of the 5 standardized actions to take.

Parameters:
- timestamp: Current loop timestamp
- current_exposure: Current exposure from ExposureMonitor
- risk_metrics: Current risk metrics from RiskMonitor
- market_data: Market data from DataProvider

Returns:
- str: One of 'entry_full', 'entry_partial', 'exit_full', 'exit_partial', 'sell_dust'

### break_down_action(action: str, params: Dict, market_data: Dict) -> List[Dict]
Break down action into sequential instruction blocks.

Parameters:
- action: The standardized action to break down
- params: Action-specific parameters
- market_data: Market data for instruction generation

Returns:
- List[Dict]: Sequential instruction blocks for Execution Manager

## Data Access Pattern

### Query Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs):
    # Query data using shared clock
    data = self.data_provider.get_data(timestamp)
    prices = data['market_data']['prices']
    
    # Access other components via references
    current_exposure = self.exposure_monitor.get_current_exposure()
    risk_metrics = self.risk_monitor.get_current_risk_metrics()
```

### Data Dependencies
- **ExposureMonitor**: Current exposure for strategy decisions
- **RiskMonitor**: Risk metrics for strategy decisions
- **DataProvider**: Market data for strategy analysis

## Mode-Aware Behavior

### Backtest Mode
```python
def decide_action(self, timestamp: pd.Timestamp, exposure: Dict, risk_metrics: Dict, market_data: Dict):
    if self.execution_mode == 'backtest':
        # Use historical data for strategy decisions
        return self._decide_action_with_historical_data(exposure, risk_metrics, market_data)
```

### Live Mode
```python
def decide_action(self, timestamp: pd.Timestamp, exposure: Dict, risk_metrics: Dict, market_data: Dict):
    elif self.execution_mode == 'live':
        # Use real-time data for strategy decisions
        return self._decide_action_with_realtime_data(exposure, risk_metrics, market_data)
```

## Event Logging Requirements

### Component Event Log File
**Separate log file** for this component's events:
- **File**: `logs/events/strategy_manager_events.jsonl`
- **Format**: JSON Lines (one event per line)
- **Rotation**: Daily rotation, keep 30 days
- **Purpose**: Component-specific audit trail

### Event Logging via EventLogger
All events logged through centralized EventLogger:

```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='[event_type]',
    component='StrategyManager',
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
    component='StrategyManager',
    data={
        'execution_mode': self.execution_mode,
        'strategy_mode': self.config.get('strategy_mode'),
        'config_hash': hash(str(self.config))
    }
)
```

#### 2. State Updates (Every update_state() Call)
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='state_update',
    component='StrategyManager',
    data={
        'trigger_source': trigger_source,
        'current_action': self.current_action,
        'instruction_blocks_generated': self.instruction_blocks_generated,
        'processing_time_ms': processing_time
    }
)
```

#### 3. Error Events
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='error',
    component='StrategyManager',
    data={
        'error_code': 'STRAT-001',
        'error_message': str(e),
        'stack_trace': traceback.format_exc(),
        'error_severity': 'CRITICAL|HIGH|MEDIUM|LOW'
    }
)
```

#### 4. Component-Specific Critical Events
- **Action Decision Failed**: When strategy decision fails
- **Instruction Block Generation Failed**: When instruction block creation fails
- **Strategy Mode Invalid**: When strategy mode is invalid

### Event Retention & Output Formats

#### Dual Logging Approach
**Both formats are used**:
1. **JSON Lines (Iterative)**: Write events to component-specific JSONL files during execution
   - **Purpose**: Real-time monitoring during backtest runs
   - **Location**: `logs/events/strategy_manager_events.jsonl`
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

### Component Error Code Prefix: STRAT
All StrategyManager errors use the `STRAT` prefix.

### Error Code Registry
**Source**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`

All error codes registered with:
- **code**: Unique error code
- **component**: Component name
- **severity**: CRITICAL | HIGH | MEDIUM | LOW
- **message**: Human-readable error message
- **resolution**: How to resolve

### Component Error Codes

#### STRAT-001: Strategy Decision Failed (HIGH)
**Description**: Failed to make strategy decision
**Cause**: Invalid exposure data, missing risk metrics, decision logic errors
**Recovery**: Retry with fallback values, check data availability
```python
raise ComponentError(
    error_code='STRAT-001',
    message='Strategy decision failed',
    component='StrategyManager',
    severity='HIGH'
)
```

#### STRAT-002: Instruction Block Generation Failed (HIGH)
**Description**: Failed to generate instruction blocks
**Cause**: Invalid action, template errors, generation logic failures
**Recovery**: Retry generation, check action validity
```python
raise ComponentError(
    error_code='STRAT-002',
    message='Instruction block generation failed',
    component='StrategyManager',
    severity='HIGH'
)
```

#### STRAT-003: Strategy Mode Invalid (CRITICAL)
**Description**: Invalid or unsupported strategy mode
**Cause**: Configuration errors, mode not implemented
**Recovery**: Check configuration, implement missing mode
```python
raise ComponentError(
    error_code='STRAT-003',
    message='Strategy mode invalid or not supported',
    component='StrategyManager',
    severity='CRITICAL'
)
```

### Structured Error Handling Pattern

#### Error Raising
```python
from backend.src.basis_strategy_v1.core.error_codes.exceptions import ComponentError

try:
    result = self._decide_action(exposure, risk_metrics, market_data)
except Exception as e:
    # Log error event
    self.event_logger.log_event(
        timestamp=timestamp,
        event_type='error',
        component='StrategyManager',
        data={
            'error_code': 'STRAT-001',
            'error_message': str(e),
            'stack_trace': traceback.format_exc()
        }
    )
    
    # Raise structured error
    raise ComponentError(
        error_code='STRAT-001',
        message=f'StrategyManager failed: {str(e)}',
        component='StrategyManager',
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
        component_name='StrategyManager',
        checker=self._health_check
    )

def _health_check(self) -> Dict:
    """Component-specific health check."""
    return {
        'status': 'healthy' | 'degraded' | 'unhealthy',
        'last_update': self.last_decision_timestamp,
        'errors': self.recent_errors[-10:],  # Last 10 errors
        'metrics': {
            'update_count': self.update_count,
            'avg_processing_time_ms': self.avg_processing_time,
            'error_rate': self.error_count / max(self.update_count, 1),
            'current_action': self.current_action,
            'instruction_blocks_generated': self.instruction_blocks_generated
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
- [ ] Data Provider Queries section documents market data queries
- [ ] Event Logging Requirements section documents component-specific JSONL file
- [ ] Event Logging Requirements section documents dual logging (JSONL + CSV)
- [ ] Error Codes section has structured error handling pattern
- [ ] Error Codes section references health integration
- [ ] Health integration documented with UnifiedHealthManager
- [ ] Component-specific log file documented (`logs/events/strategy_manager_events.jsonl`)

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

Components query data using shared clock:
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs):
    # Query data with timestamp (data <= timestamp guaranteed)
    market_data = self.data_provider.get_data(timestamp)
    current_exposure = self.exposure_monitor.get_current_exposure()
    risk_metrics = self.risk_monitor.get_current_risk_metrics()
    
    # Decide action based on current state
    action = self.decide_action(timestamp, current_exposure, risk_metrics, market_data)
    
    # Break down action into instruction blocks
    instruction_blocks = self.break_down_action(action, kwargs, market_data)
```

NEVER pass market_data as parameter between components.
NEVER cache market_data across timestamps.

## Standardized Actions

### 1. entry_full
Enter full position (initial setup or large deposits)
- **Trigger**: Initial capital deployment, large deposits
- **Goal**: Establish complete target position
- **Instruction Blocks**: Full position setup across all venues

### 2. entry_partial
Scale up position (small deposits or PnL gains)
- **Trigger**: Small deposits, PnL reinvestment
- **Goal**: Incrementally increase position size
- **Instruction Blocks**: Partial position additions

### 3. exit_full
Exit entire position (withdrawals or risk override)
- **Trigger**: Full withdrawals, risk limits exceeded
- **Goal**: Close all positions and return to cash
- **Instruction Blocks**: Complete position unwinding

### 4. exit_partial
Scale down position (small withdrawals or risk reduction)
- **Trigger**: Small withdrawals, risk reduction
- **Goal**: Incrementally decrease position size
- **Instruction Blocks**: Partial position reductions

### 5. sell_dust
Convert non-share-class tokens to share class currency
- **Trigger**: Dust token accumulation
- **Goal**: Convert rewards/dust to share class currency
- **Instruction Blocks**: Token conversion operations

## Instruction Block Structure

```python
{
    'block_id': str,  # Unique identifier
    'action': str,    # One of the 5 standardized actions
    'priority': int,  # Execution order
    'instructions': [
        {
            'instruction_type': 'wallet_transfer' | 'smart_contract_action' | 'cex_trade',
            'venue': str,  # Target venue
            'params': Dict,  # Instruction-specific parameters
            'estimated_deltas': Dict  # Expected position changes
        }
    ],
    'expected_deltas': Dict,  # Net position changes for this block
    'dependencies': List[str]  # Block IDs that must complete first
}
```

## Mode-Specific Decision Logic

### Pure Lending Mode
```python
def decide_action(self, timestamp, current_exposure, risk_metrics, market_data):
    if self.execution_mode == 'backtest':
        # Backtest-specific logic
        if current_exposure['total_deployed'] == 0:
            return 'entry_full'
        elif risk_metrics['ltv_ratio'] > 0.9:
            return 'exit_partial'
        else:
            return 'entry_partial'
    elif self.execution_mode == 'live':
        # Live-specific logic
        if current_exposure['total_deployed'] == 0:
            return 'entry_full'
        elif risk_metrics['ltv_ratio'] > 0.9:
            return 'exit_partial'
        else:
            return 'entry_partial'
```

### BTC Basis Mode
```python
def decide_action(self, timestamp, current_exposure, risk_metrics, market_data):
    funding_rate = market_data['funding_rates']['btc']
    if funding_rate > 0.001:  # Positive funding
        return 'entry_full' if current_exposure['btc_short'] == 0 else 'entry_partial'
    elif funding_rate < -0.001:  # Negative funding
        return 'exit_full' if current_exposure['btc_short'] > 0 else 'sell_dust'
    else:
        return 'sell_dust'  # No clear opportunity
```

### ETH Leveraged Mode
```python
def decide_action(self, timestamp, current_exposure, risk_metrics, market_data):
    if self.share_class == 'USDT':
        # Market-neutral (hedged)
        if current_exposure['eth_delta'] > 0.1:
            return 'exit_partial'  # Reduce delta exposure
        elif current_exposure['eth_delta'] < -0.1:
            return 'entry_partial'  # Increase delta exposure
        else:
            return 'sell_dust'
    elif self.share_class == 'ETH':
        # Directional (unhedged)
        if risk_metrics['leverage_ratio'] > 2.0:
            return 'exit_partial'  # Reduce leverage
        else:
            return 'entry_partial'  # Increase leverage
```

---

## 💻 **Core Functions**

```python
class StrategyManager:
    """Mode-specific strategy orchestration."""
    
    def __init__(self, config: Dict, exposure_monitor, risk_monitor, execution_mode: str):
        self.config = config
        self.exposure_monitor = exposure_monitor
        self.risk_monitor = risk_monitor
        self.execution_mode = execution_mode
        
        # Initial capital (for delta calculations)
        self.initial_capital = config['backtest']['initial_capital']
        self.share_class = config['strategy']['share_class']
        
        # Using direct method calls for component communication
    
    def handle_position_change(
        self,
        change_type: str,
        params: Dict,
        current_exposure: Dict,
        risk_metrics: Dict,
        market_data: Dict
    ) -> Dict:
        """
        Unified handler for ALL position changes.
        
        Args:
            change_type: 'INITIAL_SETUP', 'DEPOSIT', 'WITHDRAWAL', 'REBALANCE'
            params: Type-specific parameters
            current_exposure: Current exposure from monitor
            risk_metrics: Current risks from monitor
            market_data: Real-time market data (prices, funding rates, gas)
        
        Returns:
            Instructions for execution managers
        """
        # Get desired position (mode-specific!)
        desired = self._get_desired_position(change_type, params, current_exposure, market_data)
        
        # Calculate gap
        gap = self._calculate_gap(current_exposure, desired)
        
        # Generate instructions to close gap
        instructions = self._generate_instructions(gap, change_type, market_data)
        
        return {
            'trigger': change_type,
            'current_state': self._extract_current_state(current_exposure),
            'desired_state': desired,
            'gaps': gap,
            'instructions': instructions
        }
    
    def _get_desired_position(
        self,
        change_type: str,
        params: Dict,
        current_exposure: Dict,
        market_data: Dict
    ) -> Dict:
        """
        Get desired position (MODE-SPECIFIC!).
        
        This is THE key function - different per mode!
        """
        # Use config-driven parameters instead of mode-specific logic
        strategy_mode = self.config['strategy']['mode']
        
        if strategy_mode == 'pure_lending':
            return self._desired_pure_lending(change_type, params, market_data)
        
        elif strategy_mode == 'btc_basis':
            return self._desired_btc_basis(change_type, params, current_exposure, market_data)
        
        elif strategy_mode == 'eth_leveraged':
            return self._desired_eth_leveraged(change_type, params, current_exposure, market_data)
        
        elif strategy_mode == 'usdt_market_neutral':
            return self._desired_usdt_market_neutral(change_type, params, current_exposure, market_data)
        
        else:
            raise ValueError(f"Unknown strategy mode: {strategy_mode}")
    
    # ===== MODE-SPECIFIC DESIRED POSITION FUNCTIONS =====
    
    def _desired_pure_lending(self, change_type, params, market_data):
        """Pure lending: All capital in AAVE USDT."""
        if change_type == 'INITIAL_SETUP':
            return {
                'aave_usdt_supplied': self.initial_capital,
                'target_delta_eth': 0,
                'target_perp_positions': {},
                'aave_apy': market_data.get('aave_usdt_apy', 0.08)
            }
        
        elif change_type == 'DEPOSIT':
            return {
                'aave_usdt_supplied': 'INCREASE',  # Add to AAVE
                'deposit_amount': params['amount'],
                'aave_apy': market_data.get('aave_usdt_apy', 0.08)
            }
        
        # No rebalancing needed for pure lending
        return {}
    
    def _desired_btc_basis(self, change_type, params, current_exposure, market_data):
        """BTC basis: Long spot, short perp (market-neutral)."""
        if change_type == 'INITIAL_SETUP':
            # Initial BTC amount
            btc_price = market_data['btc_usd_price']
            capital_for_spot = self.initial_capital * 0.5
            btc_amount = capital_for_spot / btc_price
            
            return {
                'btc_spot': btc_amount,
                'btc_perp_short': -btc_amount,  # Equal short
                'target_delta_btc': 0,  # Market-neutral
                'cex_venue': self.config['strategy']['hedge_venues'][0],  # Single venue
                'btc_price': btc_price,
                'funding_rate': market_data['perp_funding_rates'][self.config['strategy']['hedge_venues'][0]].get('BTCUSDT-PERP', 0)
            }
        
        elif change_type == 'REBALANCE':
            # Maintain market neutrality
            current_btc_spot = current_exposure.get('btc_spot', 0)
            return {
                'btc_perp_short': -current_btc_spot,  # Match spot
                'target_delta_btc': 0,
                'btc_price': market_data['btc_usd_price'],
                'funding_rate': market_data['perp_funding_rates'][self.config['strategy']['hedge_venues'][0]].get('BTCUSDT-PERP', 0)
            }
        
        return {}
    
    def _desired_eth_leveraged(self, change_type, params, current_exposure, market_data):
        """
        ETH leveraged staking.
        
        Two sub-modes:
        - ETH share class: Long ETH, no hedge
        - USDT share class: Hedged with perps
        """
        if change_type == 'INITIAL_SETUP':
            if self.share_class == 'ETH':
                # No hedging, directional ETH
                return {
                    'aave_ltv': self.config['strategy']['target_ltv'],  # e.g., 0.91
                    'target_delta_eth': self.initial_capital,  # Stay long ETH
                    'target_perp_positions': {},  # No hedging!
                    'eth_price': market_data['eth_usd_price'],
                    'gas_price': market_data['gas_price_gwei']
                }
            
            else:  # USDT share class
                # Need hedging
                eth_price = market_data['eth_usd_price']
                capital_for_staking = self.initial_capital * 0.5
                eth_amount = capital_for_staking / eth_price
                
                return {
                    'aave_ltv': 0.91,
                    'target_delta_eth': 0,  # Market-neutral
                    'initial_eth_to_stake': eth_amount,
                    'target_perp_short_total': -eth_amount,  # Hedge
                    'eth_price': eth_price,
                    'gas_price': market_data['gas_price_gwei'],
                    'funding_rates': market_data['perp_funding_rates']
                }
        
        elif change_type == 'REBALANCE':
            # Maintain target LTV and delta
            if self.share_class == 'ETH':
                return {
                    'aave_ltv': 0.91,
                    'target_delta_eth': 'MAINTAIN',  # Don't change (directional)
                    'eth_price': market_data['eth_usd_price'],
                    'gas_price': market_data['gas_price_gwei']
                }
            else:  # USDT
                # Hedge should match AAVE net position
                aave_net_eth = current_exposure['erc20_wallet_net_delta_eth']
                return {
                    'aave_ltv': 0.91,
                    'target_delta_eth': 0,
                    'target_perp_short_total': -aave_net_eth,
                    'eth_price': market_data['eth_usd_price'],
                    'gas_price': market_data['gas_price_gwei'],
                    'funding_rates': market_data['perp_funding_rates']
                }
        
        return {}
    
    def _desired_usdt_market_neutral(self, change_type, params, current_exposure, market_data):
        """
        USDT market-neutral (most complex).
        
        Always maintain:
        - AAVE LTV: 0.91
        - Net delta: 0
        - Perp short = AAVE net long
        """
        aave_net_eth = current_exposure['erc20_wallet_net_delta_eth']
        
        if change_type == 'INITIAL_SETUP':
            eth_price = market_data['eth_usd_price']
            capital_for_staking = self.initial_capital * 0.5
            eth_to_stake = capital_for_staking / eth_price
            
            return {
                'aave_ltv': 0.91,
                'target_delta_eth': 0,
                'initial_eth_to_stake': eth_to_stake,
                'target_perp_short_total': -eth_to_stake,
                'hedge_allocation': self.config['strategy']['hedge_allocation'],
                'eth_price': eth_price,
                'gas_price': market_data['gas_price_gwei'],
                'funding_rates': market_data['perp_funding_rates'],
                'aave_apy': market_data.get('aave_usdt_apy', 0.08)
            }
        
        elif change_type == 'REBALANCE':
            return {
                'aave_ltv': 0.91,
                'target_delta_eth': 0,
                'target_perp_short_total': -aave_net_eth,  # Match AAVE
                'target_margin_ratio': 1.0,  # Full capital utilization
                'eth_price': market_data['eth_usd_price'],
                'gas_price': market_data['gas_price_gwei'],
                'funding_rates': market_data['perp_funding_rates']
            }
        
        elif change_type == 'DEPOSIT':
            # New capital: Split 50/50 (staking / hedge)
            return {
                'add_to_aave': params['amount'] * 0.5,
                'add_to_cex_margin': params['amount'] * 0.5,
                'eth_price': market_data['eth_usd_price'],
                'gas_price': market_data['gas_price_gwei']
            }
        
        return {}
```

---

## 🔧 **Instruction Generation**

```python
def _generate_instructions(self, gap: Dict, trigger_type: str, market_data: Dict) -> List[Dict]:
    """
    Generate execution instructions to close gap.
    
    Instructions are prioritized and sequenced.
    """
    instructions = []
    
    # Priority 1: Margin critical (prevent CEX liquidation)
    if 'margin_deficit_usd' in gap and gap['margin_deficit_usd'] > 1000:
        instructions.append(self._gen_add_margin_instruction(gap, market_data))
    
    # Priority 2: AAVE LTV critical (prevent AAVE liquidation)
    if 'aave_ltv_excess' in gap and gap['aave_ltv_excess'] > 0.02:
        instructions.append(self._gen_reduce_ltv_instruction(gap, market_data))
    
    # Priority 3: Delta drift (maintain market neutrality)
    if 'delta_gap_eth' in gap and abs(gap['delta_gap_eth']) > 2.0:
        instructions.append(self._gen_adjust_delta_instruction(gap, market_data))
    
    return instructions

def _gen_add_margin_instruction(self, gap: Dict, market_data: Dict) -> Dict:
    """
    Generate instruction to add margin to CEX.
    
    Flow:
    1. Atomic deleverage AAVE (free up ETH)
    2. Transfer ETH to CEX
    3. Sell ETH for USDT (spot)
    4. Reduce perp short (proportionally)
    """
    amount_usd = gap['margin_deficit_usd']
    venue = gap['critical_venue']  # Which exchange needs margin
    
    return {
        'priority': 1,
        'type': 'ADD_MARGIN_TO_CEX',
        'venue': venue,
        'amount_usd': amount_usd,
        'actions': [
            {
                'step': 1,
                'action': 'ATOMIC_DELEVERAGE_AAVE',
                'executor': 'OnChainExecutionManager',
                'params': {
                    'amount_usd': amount_usd,
                    'mode': 'atomic'  # Always use atomic flash loan for leveraged staking
                }
            },
            {
                'step': 2,
                'action': 'TRANSFER_ETH_TO_CEX',
                'executor': 'OnChainExecutionManager',
                'params': {
                    'venue': venue,
                    'amount_eth': amount_usd / market_data['eth_usd_price']
                }
            },
            {
                'step': 3,
                'action': 'SELL_ETH_SPOT',
                'executor': 'CEXExecutionManager',
                'params': {
                    'venue': venue,
                    'amount_eth': amount_usd / market_data['eth_usd_price']
                }
            },
            {
                'step': 4,
                'action': 'REDUCE_PERP_SHORT',
                'executor': 'CEXExecutionManager',
                'params': {
                    'venue': venue,
                    'instrument': 'ETHUSDT-PERP',
                    'amount_eth': amount_usd / market_data['eth_usd_price']
                }
            }
        ]
    }
```

---

## 🔄 **Mode-Specific Desired Positions**

### **Pure USDT Lending**

```python
desired_position = {
    'aave_usdt_supplied': initial_capital,  # All capital in AAVE
    'target_delta_eth': 0,                  # No ETH exposure
    'target_perp_positions': {},            # No derivatives
    'rebalancing_needed': False             # Never rebalances (simple!)
}
```

### **BTC Basis**

```python
desired_position = {
    'btc_spot': initial_btc_amount,           # Long BTC spot
    'btc_perp_short': -initial_btc_amount,    # Short BTC perp (equal)
    'target_delta_btc': 0,                    # Market-neutral
    'cex_venue': 'binance',                   # Single venue (cross-margin)
    'rebalancing_trigger': 'delta_drift > 3%'  # Adjust hedge if drift
}
```

### **ETH Leveraged** (ETH share class)

```python
desired_position = {
    'aave_ltv': 0.91,                         # Leverage target
    'target_delta_eth': initial_capital_eth,  # Stay long ETH (directional!)
    'target_perp_positions': {},              # No hedging
    'rebalancing_trigger': 'ltv_drift or hf_low'  # Only AAVE risk
}
```

### **ETH Leveraged** (USDT share class)

```python
desired_position = {
    'aave_ltv': 0.91,
    'target_delta_eth': 0,                    # Market-neutral
    'target_perp_short_total': -aave_net_eth, # Hedge AAVE position
    'hedge_allocation': {'binance': 0.33, 'bybit': 0.33, 'okx': 0.34},
    'rebalancing_trigger': 'ltv_drift or delta_drift or margin_low'
}
```

### **USDT Market-Neutral** (Most Complex)

```python
desired_position = {
    'aave_ltv': 0.91,
    'target_delta_eth': 0,
    'target_perp_short_total': -aave_net_eth,
    'target_perp_allocation': {
        'binance': aave_net_eth * 0.33,
        'bybit': aave_net_eth * 0.33,
        'okx': aave_net_eth * 0.34
    },
    'target_margin_ratio': 1.0,  # 100% margin (full capital utilization)
    'rebalancing_triggers': [
        'margin_ratio < 20% (URGENT)',
        'delta_drift > 5% (WARNING)',
        'ltv > 90% (CRITICAL)'
    ]
}
```

---

## 🚨 **Rebalancing Logic** (From FINAL_FIXES_SPECIFICATION.md)

### **Triggers**

```python
def check_rebalancing_needed(self, risk_metrics: Dict) -> Optional[str]:
    """Check if rebalancing needed."""
    
    # Priority 1: Margin critical (prevent CEX liquidation)
    if risk_metrics['cex_margin']['any_critical']:
        return 'MARGIN_CRITICAL'
    
    if risk_metrics['cex_margin']['min_margin_ratio'] < self.margin_warning_threshold:
        return 'MARGIN_WARNING'
    
    # Priority 2: Delta drift (maintain market neutrality)
    if risk_metrics['delta']['critical']:
        return 'DELTA_DRIFT_CRITICAL'
    
    if risk_metrics['delta']['warning']:
        return 'DELTA_DRIFT_WARNING'
    
    # Priority 3: AAVE LTV (prevent AAVE liquidation)
    if risk_metrics['aave']['critical']:
        return 'AAVE_LTV_CRITICAL'
    
    if risk_metrics['aave']['warning']:
        return 'AAVE_LTV_WARNING'
    
    # No rebalancing needed
    return None
```

### **Rebalancing Actions**

**Margin Support** (Most Common):
```python
# When ETH rises:
# - Perps lose money (shorts losing)
# - CEX margin depletes
# - Need to add margin

# Solution:
1. Reduce AAVE position (atomic deleverage via flash loan)
2. Free ETH from AAVE
3. Send ETH to CEX
4. Sell ETH for USDT (add to margin)
5. Reduce perp short (proportionally, maintain delta neutrality)

# Cost: ~$30-50 per rebalance (atomic mode)
```

**Delta Adjustment**:
```python
# When AAVE position grows from yields:
# - AAVE net ETH increases
# - Perp short stays same
# - Net delta drifts positive

# Solution:
1. Open additional perp shorts (no AAVE change)
2. Use existing CEX margin
3. Restore delta to 0

# Cost: ~$10-20 (just perp execution costs)
```

**Emergency Deleverage**:
```python
# When health factor too low:
# - AAVE at risk of liquidation
# - Reduce position significantly

# Solution:
1. Atomic deleverage AAVE (large amount)
2. Don't touch perps (accept delta exposure)
3. Preserve AAVE safety > maintain delta neutrality

# Cost: ~$30-50 + accept delta risk
```

---

## 🚀 **Live Trading Data Flow**

### **Real-Time Market Data Requirements**

```python
# Live Trading Mode - Data Provider Integration
class LiveDataProvider:
    """Real-time market data for live trading."""
    
    async def get_market_snapshot(self) -> Dict[str, Any]:
        """Get current market data snapshot."""
        return {
            # Core prices
            'eth_usd_price': await self.get_eth_price(),
            'btc_usd_price': await self.get_btc_price(),
            
            # AAVE rates
            'aave_usdt_apy': await self.get_aave_usdt_rate(),
            'aave_eth_apy': await self.get_aave_eth_rate(),
            
            # Perpetual funding rates (critical for basis strategies)
            'perp_funding_rates': {
                'binance': await self.get_binance_funding_rates(),
                'bybit': await self.get_bybit_funding_rates(),
                'okx': await self.get_okx_funding_rates()
            },
            
            # Gas prices (for on-chain operations)
            'gas_price_gwei': await self.get_current_gas_price(),
            'gas_price_fast_gwei': await self.get_fast_gas_price(),
            
            # LST prices (for staking strategies)
            'lst_prices': {
                'wsteth_usd': await self.get_wsteth_price(),
                'reth_usd': await self.get_reth_price(),
                'sfrxeth_usd': await self.get_sfrxeth_price()
            },
            
            'timestamp': datetime.utcnow(),
            'data_age_seconds': 0  # Real-time data
        }
```

### **Live vs Backtest Data Differences**

| **Aspect** | **Backtest Mode** | **Live Mode** |
|------------|-------------------|---------------|
| **Data Source** | Historical CSV files | Real-time APIs |
| **Latency** | Instant (pre-loaded) | 100-500ms per call |
| **Data Age** | Historical timestamps | Current timestamp |
| **Funding Rates** | Historical averages | Real-time rates |
| **Gas Prices** | Historical averages | Current network state |
| **Price Updates** | Per timestep | Continuous |
| **Error Handling** | Fail-fast | Retry with fallbacks |

### **Live Trading Deployment Considerations**

```python
# Live Trading Configuration
LIVE_TRADING_CONFIG = {
    'data_provider': {
        'type': 'live',
        'refresh_interval_seconds': 30,  # Update every 30s
        'max_data_age_seconds': 60,      # Reject data older than 1min
        'fallback_sources': ['primary', 'secondary', 'tertiary'],
        'rate_limits': {
            'binance': 1200,  # requests per minute
            'bybit': 120,
            'okx': 20
        }
    },
    
    'execution': {
        'slippage_tolerance': 0.005,     # 0.5% max slippage
        'gas_price_multiplier': 1.2,     # 20% above current gas
        'max_gas_price_gwei': 100,       # Emergency gas limit
        'execution_timeout_seconds': 300 # 5min max execution time
    },
    
    'risk_management': {
        'max_position_size_usd': 1000000,
        'emergency_stop_loss_pct': 0.15,  # 15% max loss
        'heartbeat_timeout_seconds': 300, # 5min heartbeat timeout
        'circuit_breaker_enabled': True
    }
}
```

### **Component State Logging**

**All Components** (Position Monitor, Exposure Monitor, Risk Monitor, Strategy Manager, Execution Interfaces):

**Backtest Mode**:
```python
logger.info(f"{component_name}: State before operation", extra={
    'timestamp': timestamp,  # Same as operation timestamp
    'status': 'pending',
    'state_snapshot': self._get_state()
})

# ... operation ...

logger.info(f"{component_name}: State after operation", extra={
    'timestamp': timestamp,  # Same timestamp (simulated)
    'status': 'complete',
    'state_snapshot': self._get_state()
})
```

**Live Mode**:
```python
logger.info(f"{component_name}: State before operation", extra={
    'timestamp': datetime.now(timezone.utc),
    'status': 'pending',
    'state_snapshot': self._get_state()
})

# ... operation ...

logger.info(f"{component_name}: State after operation", extra={
    'timestamp': datetime.now(timezone.utc),  # Different timestamp (real elapsed time)
    'status': 'complete',
    'duration_ms': elapsed_time,
    'state_snapshot': self._get_state()
})
```

**Benefits**:
- Track operation duration in live mode
- Runtime logs show component state changes
- Identical structure in backtest (timestamps same) vs live (timestamps differ)

### **Live Trading Deployment Mechanics**

#### **1. Environment Setup**
```bash
# Production environment variables
export TRADING_MODE=live
export DATA_PROVIDER_MODE=live
export EXECUTION_MODE=live
export RISK_MODE=strict

# API credentials (encrypted)
export BINANCE_API_KEY=encrypted_key
export BINANCE_API_SECRET=encrypted_secret
export BYBIT_API_KEY=encrypted_key
export BYBIT_API_SECRET=encrypted_secret

# Wallet configuration
export WALLET_PRIVATE_KEY=encrypted_key
export WALLET_ADDRESS=0x...
```

#### **2. Service Orchestration**
```python
# Live Trading Service Architecture
class LiveTradingOrchestrator:
    """Orchestrates live trading execution."""
    
    def __init__(self):
        self.data_provider = LiveDataProvider()
        self.strategy_manager = StrategyManager()
        self.execution_managers = {
            'cex': CEXExecutionManager(),
            'onchain': OnChainExecutionManager()
        }
        self.risk_monitor = LiveRiskMonitor()
        self.heartbeat_monitor = HeartbeatMonitor()
    
    async def run_live_trading_loop(self):
        """Main live trading loop."""
        while self.is_running:
            try:
                # 1. Get fresh market data
                market_data = await self.data_provider.get_market_snapshot()
                
                # 2. Check if data is fresh enough
                if market_data['data_age_seconds'] > 60:
                    logger.warning("Market data too old, skipping cycle")
                    continue
                
                # 3. Get current exposure and risk
                exposure = await self.exposure_monitor.get_current_exposure()
                risk = await self.risk_monitor.get_current_risk()
                
                # 4. Make strategy decision with live data
                decision = await self.strategy_manager.handle_position_change(
                    change_type='REBALANCE',
                    params={},
                    current_exposure=exposure,
                    risk_metrics=risk,
                    market_data=market_data  # ← Live data!
                )
                
                # 5. Execute if needed
                if decision['instructions']:
                    await self.execute_instructions(decision['instructions'])
                
                # 6. Update heartbeat
                await self.heartbeat_monitor.update_heartbeat()
                
            except Exception as e:
                logger.error(f"Live trading loop error: {e}")
                await self.emergency_stop()
            
            # Wait for next cycle
            await asyncio.sleep(30)  # 30-second cycles
```

#### **3. Deployment Differences**

| **Component** | **Backtest** | **Live Trading** |
|---------------|--------------|------------------|
| **Data Provider** | CSV file reader | Real-time API client |
| **Execution** | Simulated | Real blockchain/CEX |
| **Risk Monitoring** | Historical validation | Real-time circuit breakers |
| **Error Handling** | Fail-fast | Retry + fallback |
| **Logging** | File-based | Real-time monitoring |
| **Monitoring** | Basic metrics | Full observability stack |

---

## 🔗 **Integration**

### **Triggered By**:
- Risk Monitor updates (via direct method calls)
- User actions (deposit, withdrawal)
- Hourly checks (scheduled)

### **Uses Data From**:
- **Exposure Monitor** ← Current exposure
- **Risk Monitor** ← Risk metrics
- **Config** ← Targets, thresholds, mode

### **Issues Instructions To**:
- **CEX Execution Manager** ← CEX trades
- **OnChain Execution Manager** ← On-chain transactions

### **Component Communication**:

**Direct Method Calls**:
- Risk Monitor → Check if rebalancing needed via direct method calls
- CEX Execution Manager ← CEX trades via direct method calls
- OnChain Execution Manager ← On-chain transactions via direct method calls

---

## 🧪 **Testing**

```python
def test_initial_setup_usdt_market_neutral():
    """Test initial position for USDT market-neutral mode."""
    manager = StrategyManager('usdt_market_neutral', config, ...)
    
    desired = manager._get_desired_position(
        'INITIAL_SETUP',
        {'eth_price': 3300},
        current_exposure={}
    )
    
    # Should want:
    # - 0.91 LTV on AAVE
    # - 0 net delta
    # - Perp shorts to hedge
    assert desired['aave_ltv'] == 0.91
    assert desired['target_delta_eth'] == 0
    assert desired['target_perp_short_total'] < 0  # Short

def test_rebalancing_instruction_generation():
    """Test rebalancing instruction generation."""
    gap = {
        'margin_deficit_usd': 9124.50,
        'critical_venue': 'binance'
    }
    
    manager = StrategyManager('usdt_market_neutral', config, ...)
    instruction = manager._gen_add_margin_instruction(gap)
    
    # Should have 4 actions
    assert len(instruction['actions']) == 4
    assert instruction['actions'][0]['action'] == 'ATOMIC_DELEVERAGE_AAVE'
    assert instruction['actions'][1]['action'] == 'TRANSFER_ETH_TO_CEX'
    assert instruction['actions'][2]['action'] == 'SELL_ETH_SPOT'
    assert instruction['actions'][3]['action'] == 'REDUCE_PERP_SHORT'

def test_mode_determines_hedging():
    """Test mode-specific hedging logic."""
    # ETH share class: No hedging
    manager_eth = StrategyManager('eth_leveraged', config_eth, ...)
    desired_eth = manager_eth._desired_eth_leveraged('INITIAL_SETUP', {}, {})
    assert desired_eth['target_perp_positions'] == {}
    
    # USDT share class: Always hedge
    manager_usdt = StrategyManager('eth_leveraged', config_usdt, ...)
    desired_usdt = manager_usdt._desired_eth_leveraged('INITIAL_SETUP', {'eth_price': 3300}, {})
    assert desired_usdt['target_perp_short_total'] < 0
```

---

## 🔧 **Current Implementation Status**

**Overall Completion**: 85% (Core functionality working, inheritance-based strategy modes need implementation)

### **Core Functionality Status**
- ✅ **Working**: Mode detection, basic strategy decision logic, instruction generation, direct method calls, config-driven parameters, BASIS_ENVIRONMENT routing
- ⚠️ **Partial**: Inheritance-based strategy modes implementation (BaseStrategyManager and strategy-specific implementations need completion)
- ❌ **Missing**: None
- 🔄 **Refactoring Needed**: Inheritance-based strategy modes implementation

### **Architecture Compliance Status**
- ✅ **COMPLIANT**: Component follows canonical architectural principles
  - **Reference-Based Architecture**: Components receive references at init, never pass as runtime parameters
  - **Shared Clock Pattern**: All methods receive timestamp from EventDrivenStrategyEngine
  - **Request Isolation Pattern**: Fresh instances per backtest/live request
  - **Synchronous Component Execution**: Internal methods are synchronous, async only for I/O operations
  - **Mode-Aware Behavior**: Uses BASIS_EXECUTION_MODE for conditional logic
  - **Config-Driven Parameters**: Uses config parameters (share_class, asset, lst_type, hedge_allocation) instead of hardcoded mode logic

### **Implementation Status**
- **High Priority**:
  - Complete BaseStrategyManager with standardized wrapper actions (entry_full, entry_partial, exit_full, exit_partial, sell_dust)
  - Complete strategy-specific implementations (BTCBasisStrategyManager, ETHLeveragedStrategyManager, etc.)
  - Complete StrategyFactory for mode-based instantiation
- **Medium Priority**:
  - Optimize strategy decision performance
- **Low Priority**:
  - None identified

### **Quality Gate Status**
- **Current Status**: PARTIAL
- **Failing Tests**: Inheritance-based strategy modes tests
- **Requirements**: Complete inheritance-based strategy modes implementation
- **Integration**: Integrates with quality gate system through strategy manager tests

### **Component Integration**
- [Position Monitor Specification](01_POSITION_MONITOR.md) - Provides position data for strategy decisions
- [Exposure Monitor Specification](02_EXPOSURE_MONITOR.md) - Provides exposure data for strategy decisions
- [Risk Monitor Specification](03_RISK_MONITOR.md) - Provides risk metrics for strategy decisions
- [Execution Manager Specification](06_EXECUTION_MANAGER.md) - Receives instruction blocks for execution
- [Data Provider Specification](09_DATA_PROVIDER.md) - Provides market data for strategy decisions
- [Event Logger Specification](08_EVENT_LOGGER.md) - Logs strategy decision events

### **Task Completion Status**
- **Related Tasks**: 
  - [.cursor/tasks/06_strategy_manager_refactor.md](../../.cursor/tasks/06_strategy_manager_refactor.md) - Strategy Manager Refactor (80% complete - inheritance-based strategy modes need completion)
  - [.cursor/tasks/18_generic_vs_mode_specific_architecture.md](../../.cursor/tasks/18_generic_vs_mode_specific_architecture.md) - Generic vs Mode-Specific Architecture (100% complete - config-driven parameters implemented)
- **Completion**: 85% complete overall
- **Blockers**: Inheritance-based strategy modes implementation
- **Next Steps**: Complete BaseStrategyManager, implement strategy-specific classes, complete StrategyFactory

---

## 🎯 **Success Criteria**

- [ ] Mode detection works correctly
- [ ] Desired position correct for each mode
- [ ] Handles initial setup same as rebalancing (unified approach)
- [ ] Generates correct instructions for gaps
- [ ] Prioritizes margin critical > delta drift > LTV
- [ ] ETH share class never hedges
- [ ] USDT share class always hedges
- [ ] Instructions include all steps for execution
- [ ] Supports fast vs slow unwinding modes
- [ ] Communicates with execution managers via direct method calls

---

**Status**: Specification complete! ✅


