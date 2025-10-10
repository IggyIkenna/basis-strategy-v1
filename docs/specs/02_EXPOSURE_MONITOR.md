# Exposure Monitor Component Specification

## Purpose
Convert all balances to share class currency and calculate net delta exposure across all venues.

## 📚 **Canonical Sources**

- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](../MODES.md) - Canonical strategy mode definitions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

## Responsibilities
1. Convert token balances to share class currency (ETH or USD)
2. Calculate net delta exposure (sum all long ETH - sum all short ETH)
3. Handle AAVE index mechanics for aToken conversions
4. Provide exposure snapshots to other components
5. MODE-AWARE: Same conversion logic for both backtest and live modes

## State
- current_exposure: Dict (exposure in share class currency)
- last_calculation_timestamp: pd.Timestamp
- exposure_history: List[Dict] (for debugging)
- share_class: str (ETH or USDT)

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- position_monitor: PositionMonitor (reference, call get_current_positions())
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
- AAVE index conversion logic (hard-coded conversion rates)
- Exposure calculation precision (hard-coded decimal places)
- Exposure history retention (hard-coded limits)

## Config Fields Used

### Universal Config (All Components)
- `strategy_mode`: str - e.g., 'eth_basis', 'pure_lending'
- `share_class`: str - 'usdt_stable' | 'eth_directional'
- `initial_capital`: float - Starting capital

### Component-Specific Config
- `exposure_tolerance`: float - Tolerance for exposure calculations
  - **Usage**: Determines precision of exposure calculations
  - **Default**: 0.001 (0.1%)
  - **Validation**: Must be > 0 and < 0.01

- `exposure_history_limit`: int - Maximum exposure history entries
  - **Usage**: Limits memory usage for exposure history
  - **Default**: 1000
  - **Validation**: Must be > 0

### Config Access Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    # Read config fields (NEVER modify)
    tolerance = self.config.get('exposure_tolerance', 0.001)
```

### Behavior NOT Determinable from Config
- AAVE index conversion rates (hard-coded)
- Token price precision (hard-coded decimal places)
- Exposure calculation algorithm (hard-coded logic)

## Data Provider Queries

### Data Types Requested
`data = self.data_provider.get_data(timestamp)`

#### Market Data
- `prices`: Dict[str, float] - Token prices in USD
  - **Tokens needed**: ETH, USDT, BTC, LST tokens, AAVE tokens
  - **Update frequency**: 1min
  - **Usage**: Token price conversion for exposure calculations

#### Protocol Data
- `aave_indexes`: Dict[str, float] - AAVE liquidity indexes
  - **Tokens needed**: aETH, aUSDT, aBTC, variableDebtETH, etc.
  - **Update frequency**: 1min
  - **Usage**: AAVE token conversion to underlying assets

### Query Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    data = self.data_provider.get_data(timestamp)
    prices = data['market_data']['prices']
    aave_indexes = data['protocol_data']['aave_indexes']
```

### Data NOT Available from DataProvider
None - all data comes from DataProvider

### **YAML Configuration**
**Mode Configuration** (from `configs/modes/*.yaml`):
- `share_class`: Share class ('USDT' | 'ETH') - determines exposure currency
- `asset`: Primary asset ('BTC' | 'ETH') - determines exposure calculation
- `lst_type`: LST type ('weeth' | 'wsteth') - affects AAVE conversion logic
- `leverage_enabled`: Enable leverage (boolean) - affects exposure calculations

**Venue Configuration** (from `configs/venues/*.yaml`):
- `venue`: Venue identifier - used for venue-specific exposure calculations
- `type`: Venue type ('cex' | 'dex' | 'onchain') - affects exposure logic
- `supported_assets`: Supported asset lists - used for exposure validation

**Share Class Configuration** (from `configs/share_classes/*.yaml`):
- `base_currency`: Base currency ('USDT' | 'ETH') - determines exposure currency
- `market_neutral`: Market neutral flag (boolean) - affects exposure calculations

**Cross-Reference**: [CONFIGURATION.md](CONFIGURATION.md) - Complete configuration hierarchy
**Cross-Reference**: [ENVIRONMENT_VARIABLES.md](../ENVIRONMENT_VARIABLES.md) - Environment variable definitions

## Core Methods

### update_state(timestamp: pd.Timestamp, trigger_source: str, **kwargs)
Main entry point for exposure calculations.

Parameters:
- timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
- trigger_source: 'full_loop' | 'tight_loop' | 'manual'
- **kwargs: Additional parameters (not used)

Behavior:
1. Query data using: market_data = self.data_provider.get_data(timestamp)
2. Access position monitor via reference: positions = self.position_monitor.get_current_positions()
3. Calculate exposure based on current positions and market data
4. NO async/await: Synchronous execution only

Returns:
- None (state updated in place)

### get_current_exposure() -> Dict
Get current exposure snapshot.

Returns:
- Dict: Current exposure in share class currency

### calculate_exposure(timestamp: pd.Timestamp, positions: Dict, market_data: Dict) -> Dict
Calculate exposure from positions and market data.

Parameters:
- timestamp: Current loop timestamp
- positions: Position snapshot from PositionMonitor
- market_data: Market data from DataProvider

Returns:
- Dict: Exposure in share class currency

## Data Access Pattern

Components query data using shared clock:
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs):
    # Query data with timestamp (data <= timestamp guaranteed)
    market_data = self.data_provider.get_data(timestamp)
    positions = self.position_monitor.get_current_positions()
    
    # Calculate exposure based on current state
    exposure = self.calculate_exposure(timestamp, positions, market_data)
    
    # Update internal state
    self.current_exposure = exposure
    self.last_calculation_timestamp = timestamp
```

NEVER pass market_data or positions as parameters between components.
NEVER cache market_data across timestamps.

## Mode-Aware Behavior

### Backtest Mode
```python
def calculate_exposure(self, timestamp: pd.Timestamp, positions: Dict, market_data: Dict):
    if self.execution_mode == 'backtest':
        # Use historical market data for conversions
        return self._calculate_exposure_with_data(positions, market_data)
```

### Live Mode
```python
def calculate_exposure(self, timestamp: pd.Timestamp, positions: Dict, market_data: Dict):
    elif self.execution_mode == 'live':
        # Use real-time market data for conversions
        return self._calculate_exposure_with_data(positions, market_data)
```

## Event Logging Requirements

### Component Event Log File
**Separate log file** for this component's events:
- **File**: `logs/events/exposure_monitor_events.jsonl`
- **Format**: JSON Lines (one event per line)
- **Rotation**: Daily rotation, keep 30 days
- **Purpose**: Component-specific audit trail

### Event Logging via EventLogger
All events logged through centralized EventLogger:

```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='[event_type]',
    component='ExposureMonitor',
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
    component='ExposureMonitor',
    data={
        'execution_mode': self.execution_mode,
        'share_class': self.share_class,
        'config_hash': hash(str(self.config))
    }
)
```

#### 2. State Updates (Every update_state() Call)
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='state_update',
    component='ExposureMonitor',
    data={
        'trigger_source': trigger_source,
        'net_delta_exposure': self.current_exposure.get('net_delta', 0),
        'total_value': self.current_exposure.get('total_value', 0),
        'processing_time_ms': processing_time
    }
)
```

#### 3. Error Events
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='error',
    component='ExposureMonitor',
    data={
        'error_code': 'EXP-001',
        'error_message': str(e),
        'stack_trace': traceback.format_exc(),
        'error_severity': 'CRITICAL|HIGH|MEDIUM|LOW'
    }
)
```

#### 4. Component-Specific Critical Events
- **AAVE Conversion Failed**: When AAVE index conversion fails
- **Exposure Calculation Error**: When exposure calculation fails
- **Price Data Missing**: When required price data is unavailable

### Event Retention & Output Formats

#### Dual Logging Approach
**Both formats are used**:
1. **JSON Lines (Iterative)**: Write events to component-specific JSONL files during execution
   - **Purpose**: Real-time monitoring during backtest runs
   - **Location**: `logs/events/exposure_monitor_events.jsonl`
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

### Component Error Code Prefix: EXP
All ExposureMonitor errors use the `EXP` prefix.

### Error Code Registry
**Source**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`

All error codes registered with:
- **code**: Unique error code
- **component**: Component name
- **severity**: CRITICAL | HIGH | MEDIUM | LOW
- **message**: Human-readable error message
- **resolution**: How to resolve

### Component Error Codes

#### EXP-001: AAVE Conversion Failed (HIGH)
**Description**: Failed to convert AAVE tokens to underlying assets
**Cause**: Missing AAVE indexes, invalid token addresses, network issues
**Recovery**: Retry with fallback values, check AAVE index data
```python
raise ComponentError(
    error_code='EXP-001',
    message='AAVE conversion failed for token',
    component='ExposureMonitor',
    severity='HIGH'
)
```

#### EXP-002: Price Data Missing (HIGH)
**Description**: Required price data not available for exposure calculation
**Cause**: DataProvider issues, missing price feeds, network problems
**Recovery**: Use cached prices, retry data fetch, check data provider
```python
raise ComponentError(
    error_code='EXP-002',
    message='Price data missing for exposure calculation',
    component='ExposureMonitor',
    severity='HIGH'
)
```

#### EXP-003: Exposure Calculation Error (MEDIUM)
**Description**: Failed to calculate net delta exposure
**Cause**: Invalid position data, calculation overflow, precision errors
**Recovery**: Log warning, use previous exposure, continue processing
```python
raise ComponentError(
    error_code='EXP-003',
    message='Exposure calculation failed',
    component='ExposureMonitor',
    severity='MEDIUM'
)
```

### Structured Error Handling Pattern

#### Error Raising
```python
from backend.src.basis_strategy_v1.core.error_codes.exceptions import ComponentError

try:
    result = self._calculate_exposure(positions, market_data)
except Exception as e:
    # Log error event
    self.event_logger.log_event(
        timestamp=timestamp,
        event_type='error',
        component='ExposureMonitor',
        data={
            'error_code': 'EXP-003',
            'error_message': str(e),
            'stack_trace': traceback.format_exc()
        }
    )
    
    # Raise structured error
    raise ComponentError(
        error_code='EXP-003',
        message=f'ExposureMonitor failed: {str(e)}',
        component='ExposureMonitor',
        severity='MEDIUM',
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
        component_name='ExposureMonitor',
        checker=self._health_check
    )

def _health_check(self) -> Dict:
    """Component-specific health check."""
    return {
        'status': 'healthy' | 'degraded' | 'unhealthy',
        'last_update': self.last_calculation_timestamp,
        'errors': self.recent_errors[-10:],  # Last 10 errors
        'metrics': {
            'update_count': self.update_count,
            'avg_processing_time_ms': self.avg_processing_time,
            'error_rate': self.error_count / max(self.update_count, 1),
            'net_delta_exposure': self.current_exposure.get('net_delta', 0),
            'total_value': self.current_exposure.get('total_value', 0)
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
- [ ] Data Provider Queries section documents market data and protocol data queries
- [ ] Event Logging Requirements section documents component-specific JSONL file
- [ ] Event Logging Requirements section documents dual logging (JSONL + CSV)
- [ ] Error Codes section has structured error handling pattern
- [ ] Error Codes section references health integration
- [ ] Health integration documented with UnifiedHealthManager
- [ ] Component-specific log file documented (`logs/events/exposure_monitor_events.jsonl`)

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

## Integration Points

### Called BY
- EventDrivenStrategyEngine (full loop): exposure_monitor.update_state(timestamp, 'full_loop')
- PositionUpdateHandler (tight loop): exposure_monitor.update_state(timestamp, 'tight_loop')
- StrategyManager (exposure query): exposure_monitor.get_current_exposure()

### Calls TO
- data_provider.get_data(timestamp) - data queries
- position_monitor.get_current_positions() - position queries

### Communication
- Direct method calls ONLY
- NO event publishing
- NO Redis/message queues
- NO async/await in internal methods

## Code Structure Example

```python
class ExposureMonitor:
    def __init__(self, config: Dict, data_provider: DataProvider, execution_mode: str,
                 position_monitor: PositionMonitor):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        self.position_monitor = position_monitor
        
        # Initialize component-specific state
        self.current_exposure = {}
        self.last_calculation_timestamp = None
        self.exposure_history = []
        self.share_class = config.get('share_class', 'USDT')
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs):
        """Main exposure calculation entry point."""
        # Query data with timestamp
        market_data = self.data_provider.get_data(timestamp)
        positions = self.position_monitor.get_current_positions()
        
        # Calculate exposure
        exposure = self.calculate_exposure(timestamp, positions, market_data)
        
        # Update internal state
        self.current_exposure = exposure
        self.last_calculation_timestamp = timestamp
        self.exposure_history.append({
            'timestamp': timestamp,
            'exposure': exposure.copy()
        })
    
    def get_current_exposure(self) -> Dict:
        """Get current exposure snapshot."""
        return self.current_exposure.copy()
    
    def calculate_exposure(self, timestamp: pd.Timestamp, positions: Dict, market_data: Dict) -> Dict:
        """Calculate exposure from positions and market data."""
        # Convert all positions to share class currency
        exposure = {
            'total_equity': 0.0,
            'net_delta_eth': 0.0,
            'net_delta_usd': 0.0,
            'venue_exposures': {}
        }
        
        # Process each venue
        for venue, venue_positions in positions.items():
            venue_exposure = self._calculate_venue_exposure(venue_positions, market_data)
            exposure['venue_exposures'][venue] = venue_exposure
            exposure['total_equity'] += venue_exposure['equity']
            exposure['net_delta_eth'] += venue_exposure['delta_eth']
            exposure['net_delta_usd'] += venue_exposure['delta_usd']
        
        return exposure
    
    def _calculate_venue_exposure(self, venue_positions: Dict, market_data: Dict) -> Dict:
        """Calculate exposure for a single venue."""
        # Implementation would handle AAVE index mechanics, token conversions, etc.
        pass
```

## Related Documentation
- [Reference-Based Architecture](../REFERENCE_ARCHITECTURE.md)
- [Shared Clock Pattern](../SHARED_CLOCK_PATTERN.md)
- [Request Isolation Pattern](../REQUEST_ISOLATION_PATTERN.md)

### **Component Integration**
- [Position Monitor Specification](01_POSITION_MONITOR.md) - Provides position data for exposure calculations
- [Risk Monitor Specification](03_RISK_MONITOR.md) - Depends on Exposure Monitor for exposure data
- [P&L Calculator Specification](04_PNL_CALCULATOR.md) - Depends on Exposure Monitor for exposure data
- [Strategy Manager Specification](05_STRATEGY_MANAGER.md) - Depends on Exposure Monitor for exposure data
- [Data Provider Specification](09_DATA_PROVIDER.md) - Provides market data for exposure calculations
- [Event Logger Specification](08_EVENT_LOGGER.md) - Logs exposure calculation events
- [Position Update Handler Specification](11_POSITION_UPDATE_HANDLER.md) - Triggers exposure updates

---

## 🔑 **AAVE Conversion Logic** (CRITICAL!)

### **Why This is Essential**

**User's Clarification**: *"aWeETH amount depends on liquidity index at time of supply"*

**This affects EVERYTHING**:
- Balance tracking (wallet.aWeETH is scaled, not 1:1)
- P&L calculation (growth from index + oracle)
- Health factor (uses underlying, not scaled)

**All Three Statements Are True**:
1. **aWeETH is CONSTANT** after supply (never changes)
2. **aWeETH amount depends on liquidity index at time of supply** (initial calculation)
3. **Our data uses normalized indices** (~1.0, not 1e27)

### **The Conversion Chain** ⛓️

```python
# Step 1: Wallet holds aWeETH (CONSTANT scaled balance)
wallet.aWeETH = 95.24  # ERC-20 token balance (doesn't change from yields!)

# Step 2: Convert to underlying weETH (via liquidity index)
current_liquidity_index = 1.10  # Grows over time from AAVE supply yield
weeth_underlying = wallet.aWeETH × current_liquidity_index
# = 95.24 × 1.10 = 104.76 weETH (grew from index!)

# Step 3: Convert to ETH (via oracle price)
weeth_eth_oracle = 1.0256  # Grows over time from base staking
weeth_in_eth = weeth_underlying × weeth_eth_oracle
# = 104.76 × 1.0256 = 107.44 ETH (grew from oracle!)

# Step 4: Convert to USD (via spot price)
eth_usd_price = 3305.20
weeth_in_usd = weeth_in_eth × eth_usd_price
# = 107.44 × 3305.20 = $355,092

# Final exposure:
# - Native: 95.24 aWeETH (wallet balance)
# - Underlying: 104.76 weETH (redeemable from AAVE)
# - ETH: 107.44 ETH (for delta tracking)
# - USD: $355,092 (for P&L in USDT modes)
```

### **Why Indices Are NOT 1:1** 🔴

**Wrong Assumption** (I had this initially):
```python
# ❌ WRONG! Assumes 1:1 conversion
wallet.weETH = 100.0
wallet.aWeETH = 100.0  # WRONG!
```

**Correct** (Index-dependent):
```python
# ✅ CORRECT! Depends on current liquidity index
wallet.weETH = 100.0
current_liquidity_index = 1.05

# Supply to AAVE
aweeth_received = wallet.weETH / current_liquidity_index
# = 100.0 / 1.05 = 95.24 aWeETH

wallet.aWeETH = 95.24  # This is what you actually receive!

# Later (index grew to 1.10 from AAVE yield)
weeth_redeemable = wallet.aWeETH × new_liquidity_index
# = 95.24 × 1.10 = 104.76 weETH

# Profit from AAVE yield: 104.76 - 100.0 = 4.76 weETH!
```

**Impact**:
- Get this wrong → All balances wrong
- Get this wrong → All P&L wrong
- Get this wrong → Health factor wrong
- **This is the #1 most critical calculation!**

---

## 📊 **Data Structures**

### **Input**: Position Snapshot (from Position Monitor)

```python
{
    'timestamp': timestamp,
    'wallet': {
        'ETH': 10.5,
        'USDT': 0.0,
        'weETH': 0.0,  # Free weETH (not in AAVE)
        'aWeETH': 95.24,  # AAVE aToken (CONSTANT scaled balance)
        'variableDebtWETH': 88.70  # AAVE debt token (CONSTANT scaled balance)
    },
    'cex_accounts': {
        'binance': {'USDT': 24992.50, 'ETH_spot': 0.0},
        'bybit': {'USDT': 24985.30},
        'okx': {'USDT': 24980.15}
    },
    'perp_positions': {
        'binance': {
            'ETHUSDT-PERP': {
                'size': -8.562,
                'entry_price': 2920.00
            }
        },
        'bybit': {'ETHUSDT-PERP': {'size': -8.551, 'entry_price': 2921.50}},
        'okx': {'ETHUSDT-PERP': {'size': -8.557, 'entry_price': 2920.50}}
    }
}
```

### **Input**: Market Data (from Data Provider)

```python
{
    'timestamp': timestamp,
    'eth_usd_price': 3305.20,
    'weeth_liquidity_index': 1.10,
    'weth_borrow_index': 1.08,
    'weeth_eth_oracle': 1.0256,
    'binance_eth_perp_mark': 3305.20,
    'bybit_eth_perp_mark': 3306.15,
    'okx_eth_perp_mark': 3304.80
}
```

### **Output**: Exposure Data

```python
{
    'timestamp': timestamp,
    'share_class': 'USDT',  # or 'ETH'
    
    # Per-token exposure breakdown
    'exposures': {
        'aWeETH': {
            'wallet_balance': 95.24,        # Raw wallet balance (scaled)
            'underlying_native': 104.76,    # Underlying weETH (scaled × index)
            'exposure_eth': 107.44,         # ETH equivalent (× oracle)
            'exposure_usd': 355092.00,      # USD equivalent (× ETH price)
            'direction': 'LONG'             # Long ETH exposure
        },
        'variableDebtWETH': {
            'wallet_balance': 88.70,        # Raw debt token balance (scaled)
            'underlying_native': 95.796,    # Underlying WETH owed (scaled × index)
            'exposure_eth': 95.796,         # ETH equivalent (WETH = ETH)
            'exposure_usd': 316604.75,      # USD equivalent
            'direction': 'SHORT'            # Short ETH exposure (debt)
        },
        'binance_USDT': {
            'balance': 24992.50,
            'exposure_eth': 7.56,           # USDT / ETH price
            'exposure_usd': 24992.50,
            'direction': 'SHORT_ETH'        # USDT is short ETH
        },
        'binance_ETHUSDT-PERP': {
            'size': -8.562,
            'entry_price': 2920.00,
            'mark_price': 3305.20,
            'exposure_eth': -8.562,
            'exposure_usd': -28299.47,
            'unrealized_pnl': -3296.63,
            'direction': 'SHORT'
        },
        # ... all tokens and positions
    },
    
    # Aggregated metrics
    'total_long_eth': 107.44,     # Sum of all long ETH
    'total_short_eth': 112.558,   # Sum of all short ETH (debt + USDT + perps)
    'net_delta_eth': -5.118,      # Total: Long - Short
    'net_delta_pct': -3.01,       # vs initial position
    
    # Net delta by venue (for downstream use)
    'erc20_wallet_net_delta_eth': +3.104,   # On-chain: AAVE collateral - debt + free ETH
    'cex_wallet_net_delta_eth': -8.222,     # Off-chain: CEX balances + perps
    # erc20 + cex = net_delta_eth
    
    # Token equity (for delta drift % calculations)
    'token_equity_eth': 11.644,             # Net assets - debts (in ETH)
    'token_equity_usd': 38492.12,           # Net assets - debts (in USD)
    # Formula: (AAVE collateral + CEX balances + free tokens) - (AAVE debt + gas debt)
    # Used for: Delta drift % = net_delta_eth / token_equity_eth
    
    # Total value (in share class currency)
    'total_value_usd': 355092 - 316605 - gas_debt + cex_balances,
    'total_value_eth': total_value_usd / eth_price,
    'share_class_value': total_value_usd  # USD for USDT share class
}
```

---

## 💻 **Core Functions**

### **Main Calculation**

```python
class ExposureMonitor:
    """Calculate exposure from raw balances."""
    
    def __init__(self, config: Dict, position_monitor, data_provider, execution_mode: str):
        self.config = config
        self.position_monitor = position_monitor  # Shared instance reference
        self.data_provider = data_provider  # Shared instance reference
        self.execution_mode = execution_mode
        self.share_class = config.get('share_class', 'USDT')
    
    def calculate_exposure(self, timestamp: pd.Timestamp) -> Dict:
        """
        Calculate exposure from current positions.
        
        Triggered by: Position Monitor updates
        
        Returns: Complete exposure breakdown
        """
        # Get current positions (from Position Monitor)
        position = self.position_monitor.get_snapshot()
        
        # Get current market data (from Data Provider)
        market_data = self.data_provider.get_market_data(timestamp)
        
        # Calculate exposures per token
        exposures = {}
        
        # 1. AAVE aWeETH (CRITICAL: Index-dependent conversion!)
        if position['wallet']['aWeETH'] > 0:
            exposures['aWeETH'] = self._calculate_aave_collateral_exposure(
                aweeth_scaled=position['wallet']['aWeETH'],
                liquidity_index=market_data['weeth_liquidity_index'],
                oracle_price=market_data['weeth_eth_oracle'],
                eth_usd_price=market_data['eth_usd_price']
            )
        
        # 2. AAVE variableDebtWETH
        if position['wallet']['variableDebtWETH'] > 0:
            exposures['variableDebtWETH'] = self._calculate_aave_debt_exposure(
                debt_scaled=position['wallet']['variableDebtWETH'],
                borrow_index=market_data['weth_borrow_index'],
                eth_usd_price=market_data['eth_usd_price']
            )
        
        # 3. Free wallet ETH (can be negative for USDT modes = gas debt)
        if position['wallet']['ETH'] != 0:
            exposures['wallet_ETH'] = self._calculate_eth_exposure(
                eth_amount=position['wallet']['ETH'],
                eth_usd_price=market_data['eth_usd_price']
            )
        
        # 4. CEX USDT balances
        for venue in ['binance', 'bybit', 'okx']:
            usdt = position['cex_accounts'][venue]['USDT']
            if usdt != 0:
                exposures[f'{venue}_USDT'] = {
                    'balance': usdt,
                    'exposure_eth': usdt / market_data['eth_usd_price'],
                    'exposure_usd': usdt,
                    'direction': 'SHORT_ETH'  # USDT is short ETH
                }
        
        # 5. Perp positions (per exchange with separate mark prices!)
        for venue in ['binance', 'bybit', 'okx']:
            for instrument, pos in position['perp_positions'].get(venue, {}).items():
                mark_price = market_data[f'{venue.lower()}_eth_perp_mark']
                exposures[f'{venue}_{instrument}'] = {
                    'size': pos['size'],
                    'entry_price': pos['entry_price'],
                    'mark_price': mark_price,
                    'exposure_eth': pos['size'],  # Already in ETH
                    'exposure_usd': pos['size'] × mark_price,
                    'unrealized_pnl': pos['size'] × (pos['entry_price'] - mark_price),
                    'direction': 'SHORT' if pos['size'] < 0 else 'LONG'
                }
        
        # Calculate aggregates
        net_delta_eth = self._calculate_net_delta(exposures)
        total_value = self._calculate_total_value(exposures, market_data)
        
        return {
            'timestamp': timestamp,
            'share_class': self.share_class,
            'exposures': exposures,
            'net_delta_eth': net_delta_eth,
            'total_value_usd': total_value,
            'total_value_eth': total_value / market_data['eth_usd_price'],
            'share_class_value': total_value if self.share_class == 'USDT' else total_value / market_data['eth_usd_price']
        }
    
    def _calculate_aave_collateral_exposure(
        self,
        aweeth_scaled: float,
        liquidity_index: float,
        oracle_price: float,
        eth_usd_price: float
    ) -> Dict:
        """
        Calculate AAVE collateral exposure with INDEX-DEPENDENT conversion.
        
        This is THE MOST CRITICAL calculation in the entire system!
        
        Conversion chain:
        1. Scaled balance (wallet.aWeETH) - CONSTANT
        2. × liquidity_index → Underlying weETH (grows from AAVE yield)
        3. × oracle_price → ETH equivalent (grows from base staking)
        4. × eth_usd_price → USD equivalent (changes with ETH price)
        """
        # Step 1: Scaled → Underlying (via AAVE index)
        # Indices in our data are normalized (~1.0, NOT 1e27!)
        weeth_underlying = aweeth_scaled × liquidity_index
        
        # Step 2: Underlying weETH → ETH (via oracle)
        weeth_in_eth = weeth_underlying × oracle_price
        
        # Step 3: ETH → USD (via spot price)
        weeth_in_usd = weeth_in_eth × eth_usd_price
        
        return {
            'wallet_balance_scaled': aweeth_scaled,      # What wallet shows (CONSTANT)
            'underlying_native': weeth_underlying,        # What AAVE sees (GROWS)
            'exposure_eth': weeth_in_eth,                # For delta tracking
            'exposure_usd': weeth_in_usd,                # For P&L (USDT modes)
            'direction': 'LONG',
            
            # Conversion details (for debugging)
            'liquidity_index': liquidity_index,
            'oracle_price': oracle_price,
            'eth_usd_price': eth_usd_price,
            'conversion_chain': f'{aweeth_scaled:.2f} aWeETH → {weeth_underlying:.2f} weETH → {weeth_in_eth:.2f} ETH → ${weeth_in_usd:,.2f}'
        }
    
    def _calculate_aave_debt_exposure(
        self,
        debt_scaled: float,
        borrow_index: float,
        eth_usd_price: float
    ) -> Dict:
        """
        Calculate AAVE debt exposure with INDEX-DEPENDENT conversion.
        
        Same principle as collateral, but for debt.
        """
        # Scaled → Underlying (via borrow index)
        weth_debt_underlying = debt_scaled × borrow_index
        
        # WETH = ETH (1:1)
        debt_in_eth = weth_debt_underlying
        
        # ETH → USD
        debt_in_usd = debt_in_eth × eth_usd_price
        
        return {
            'wallet_balance_scaled': debt_scaled,        # variableDebtWETH (CONSTANT)
            'underlying_native': weth_debt_underlying,   # WETH owed (GROWS)
            'exposure_eth': debt_in_eth,                 # For delta (negative contribution)
            'exposure_usd': debt_in_usd,                 # For P&L
            'direction': 'SHORT',  # Debt is short exposure
            
            # Conversion details
            'borrow_index': borrow_index,
            'eth_usd_price': eth_usd_price
        }
```

---

## 🔢 **Net Delta Calculation**

```python
def _calculate_net_delta(self, exposures: Dict) -> float:
    """
    Calculate net delta in ETH.
    
    Net delta = All long ETH - All short ETH
    
    Long ETH:
    - AAVE collateral (aWeETH converted to ETH)
    - Free wallet.ETH (if positive)
    - CEX ETH spot holdings
    
    Short ETH:
    - AAVE debt (variableDebtWETH)
    - Free wallet.ETH (if negative - gas debt)
    - CEX USDT balances (USDT / ETH price)
    - Short perp positions
    """
    long_eth = 0.0
    short_eth = 0.0
    
    for token, exp in exposures.items():
        eth_exposure = exp['exposure_eth']
        
        if exp['direction'] in ['LONG', 'LONG_ETH']:
            long_eth += abs(eth_exposure)
        elif exp['direction'] in ['SHORT', 'SHORT_ETH']:
            short_eth += abs(eth_exposure)
    
    return long_eth - short_eth
```

---

## 📊 **Total Value Calculation**

```python
def _calculate_total_value(self, exposures: Dict, market_data: Dict) -> float:
    """
    Calculate total portfolio value in USD.
    
    Sum of all assets minus all liabilities.
    """
    # Assets
    total_assets_usd = 0.0
    
    # AAVE collateral
    if 'aWeETH' in exposures:
        total_assets_usd += exposures['aWeETH']['exposure_usd']
    
    # CEX balances (USDT + spot holdings)
    for venue in ['binance', 'bybit', 'okx']:
        total_assets_usd += exposures.get(f'{venue}_USDT', {}).get('exposure_usd', 0)
        
        # Spot holdings (if any)
        if f'{venue}_ETH_spot' in exposures:
            total_assets_usd += exposures[f'{venue}_ETH_spot']['exposure_usd']
        if f'{venue}_BTC_spot' in exposures:
            total_assets_usd += exposures[f'{venue}_BTC_spot']['exposure_usd']
    
    # Free wallet ETH (if positive)
    if 'wallet_ETH' in exposures and exposures['wallet_ETH']['balance'] > 0:
        total_assets_usd += exposures['wallet_ETH']['exposure_usd']
    
    # Liabilities
    total_liabilities_usd = 0.0
    
    # AAVE debt
    if 'variableDebtWETH' in exposures:
        total_liabilities_usd += exposures['variableDebtWETH']['exposure_usd']
    
    # Gas debt (if ETH balance negative)
    if 'wallet_ETH' in exposures and exposures['wallet_ETH']['balance'] < 0:
        gas_debt_usd = abs(exposures['wallet_ETH']['exposure_usd'])
        total_liabilities_usd += gas_debt_usd
    
    # Perp unrealized P&L affects value (but not delta)
    # Already reflected in CEX balances via M2M updates
    
    # Net value
    total_value_usd = total_assets_usd - total_liabilities_usd
    
    return total_value_usd
```

---

## 🔗 **Integration**

### **Triggered By**:
- Position Monitor updates (via direct method calls)

### **Uses Data From**:
- **Position Monitor** ← Raw balances
- **Data Provider** ← Prices, indices, oracles

### **Provides Data To**:
- **Risk Monitor** ← Exposure data
- **P&L Calculator** ← Exposure data
- **Strategy Manager** ← Exposure data

### **Component Communication**:

**Direct Method Calls**:
- Position Monitor → Triggers recalculation via direct method calls
- Risk Monitor ← Exposure data via direct method calls
- P&L Calculator ← Exposure data via direct method calls
- Strategy Manager ← Exposure data via direct method calls

---

## 🧪 **Testing**

```python
def test_aave_index_conversion():
    """Test CRITICAL aWeETH conversion logic."""
    # Supply scenario
    weeth_to_supply = 100.0
    liquidity_index = 1.05
    
    # Calculate aWeETH received (INDEX-DEPENDENT!)
    aweeth_received = weeth_to_supply / liquidity_index
    assert aweeth_received == pytest.approx(95.24, abs=0.01)
    
    # Later: Index grew to 1.10
    new_index = 1.10
    weeth_redeemable = aweeth_received × new_index
    
    # Profit from AAVE yield
    profit = weeth_redeemable - weeth_to_supply
    assert profit == pytest.approx(4.76, abs=0.01)

def test_net_delta_calculation():
    """Test net delta aggregation."""
    exposures = {
        'aWeETH': {'exposure_eth': 107.44, 'direction': 'LONG'},
        'variableDebtWETH': {'exposure_eth': 95.796, 'direction': 'SHORT'},
        'binance_ETHUSDT-PERP': {'exposure_eth': -8.562, 'direction': 'SHORT'},
        'bybit_ETHUSDT-PERP': {'exposure_eth': -8.551, 'direction': 'SHORT'}
    }
    
    monitor = ExposureMonitor('USDT', position_monitor, data_provider)
    net_delta = monitor._calculate_net_delta(exposures)
    
    # 107.44 - (95.796 + 8.562 + 8.551) = -5.469
    assert net_delta == pytest.approx(-5.47, abs=0.1)

def test_share_class_value():
    """Test value returned in share class currency."""
    monitor_usd = ExposureMonitor('USDT', ...)
    monitor_eth = ExposureMonitor('ETH', ...)
    
    exposure_usd = monitor_usd.calculate_exposure(timestamp)
    exposure_eth = monitor_eth.calculate_exposure(timestamp)
    
    # USDT mode returns USD
    assert 'share_class_value' in exposure_usd
    assert exposure_usd['share_class_value'] == exposure_usd['total_value_usd']
    
    # ETH mode returns ETH
    assert exposure_eth['share_class_value'] == exposure_eth['total_value_eth']
```

---

## 🔄 **Backtest vs Live**

### **Backtest**:
- Triggered by Position Monitor updates (synchronous chain)
- Uses historical market data (from CSV)
- Calculates once per update
- No real-time queries

### **Live**:
- Triggered by Position Monitor updates (same)
- Uses live market data (WebSocket cache)
- Real-time oracle price from AAVE contracts
- Can recalculate on-demand for monitoring

---

## ⚠️ **Common Mistakes** (Avoid These!)

### **Mistake 1**: Assuming 1:1 AAVE Conversion
```python
# ❌ WRONG!
aweeth = weeth_supplied  # Assumes 1:1

# ✅ CORRECT!
aweeth = weeth_supplied / current_liquidity_index
```

### **Mistake 2**: Using Scaled Balance for Value
```python
# ❌ WRONG!
collateral_value = wallet.aWeETH × oracle_price  # Uses scaled!

# ✅ CORRECT!
underlying = wallet.aWeETH × liquidity_index  # Get underlying first
collateral_value = underlying × oracle_price  # Then multiply oracle
```

### **Mistake 3**: Shared Perp Prices
```python
# ❌ WRONG!
eth_perp_price = 3305.20  # Same for all exchanges

# ✅ CORRECT!
binance_price = 3305.20  # Binance-specific
bybit_price = 3306.15    # Bybit-specific (different!)
okx_price = 3304.80      # OKX-specific
```

---

## 🔧 **Current Implementation Status**

**Overall Completion**: 85% (Core functionality working, centralized utility manager needs implementation)

### **Core Functionality Status**
- ✅ **Working**: AAVE index conversions, net delta calculation, per-exchange perp prices, share class value calculations, total value aggregation, gas debt handling, USDT short exposure, config-driven parameters
- ⚠️ **Partial**: Centralized utility manager implementation (scattered utility methods need centralization)
- ❌ **Missing**: None
- 🔄 **Refactoring Needed**: Centralized utility manager implementation

### **Architecture Compliance Status**
- ✅ **COMPLIANT**: Component follows canonical architectural principles
  - **Reference-Based Architecture**: Components receive references at init, never pass as runtime parameters
  - **Shared Clock Pattern**: All methods receive timestamp from EventDrivenStrategyEngine
  - **Request Isolation Pattern**: Fresh instances per backtest/live request
  - **Synchronous Component Execution**: Internal methods are synchronous, async only for I/O operations
  - **Mode-Aware Behavior**: Uses BASIS_EXECUTION_MODE for conditional logic
  - **Config-Driven Parameters**: Uses config parameters (asset, share_class, lst_type, hedge_allocation) instead of mode-specific logic

### **Implementation Status**
- **High Priority**:
  - Implement centralized utility manager for scattered utility methods
  - Centralize liquidity index calculations
  - Centralize market price conversions
- **Medium Priority**:
  - Optimize utility method performance
- **Low Priority**:
  - None identified

### **Quality Gate Status**
- **Current Status**: PARTIAL
- **Failing Tests**: Centralized utility manager tests
- **Requirements**: Implement centralized utility manager
- **Integration**: Integrates with quality gate system through exposure monitor tests

### **Task Completion Status**
- **Related Tasks**: 
  - [.cursor/tasks/18_generic_vs_mode_specific_architecture.md](../../.cursor/tasks/18_generic_vs_mode_specific_architecture.md) - Generic vs Mode-Specific Architecture (100% complete - config-driven parameters implemented)
  - [.cursor/tasks/14_mode_agnostic_architecture_requirements.md](../../.cursor/tasks/14_mode_agnostic_architecture_requirements.md) - Mode-Agnostic Architecture (80% complete - centralized utilities need implementation)
- **Completion**: 85% complete overall
- **Blockers**: Centralized utility manager implementation
- **Next Steps**: Implement centralized utility manager for scattered utility methods

---

## 🎯 **Success Criteria**

- [ ] Correct AAVE index conversions (scaled → underlying)
- [ ] Net delta calculation accurate
- [ ] Per-exchange perp prices used
- [ ] Share class value in correct currency
- [ ] Total value includes all venues
- [ ] Gas debt handled correctly (negative ETH)
- [ ] USDT as short ETH exposure
- [ ] Triggered by every position update
- [ ] Provides data to downstream components via direct method calls
- [ ] Balance sheet data available for plotting (wallet, CEX, AAVE positions)

---

**Status**: Specification complete! ✅


