# Risk Monitor Component Specification

**Last Reviewed**: October 10, 2025

## Purpose
Calculate risk metrics from exposure data and trigger alerts for risk management.

## Responsibilities
1. Calculate LTV ratios for AAVE positions
2. Calculate health factors for protocol positions
3. Calculate margin ratios for CEX positions
4. Provide risk snapshots to other components
5. MODE-AWARE: Same risk calculation logic for both backtest and live modes

## State
- current_risk_metrics: Dict (risk metrics)
- last_calculation_timestamp: pd.Timestamp
- risk_history: List[Dict] (for debugging)

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- position_monitor: PositionMonitor (reference, call get_current_positions())
- exposure_monitor: ExposureMonitor (reference, call get_current_exposure())
- data_provider: DataProvider (reference, query with timestamps)
- config: Dict (reference, never modified)
- execution_mode: str (BASIS_EXECUTION_MODE)

These references are stored in __init__ and used throughout component lifecycle.
Components NEVER receive these as method parameters during runtime.

## Configuration Parameters

**Mode Configuration** (from `configs/modes/*.yaml`):
- `risk_limits`: Risk limit configurations - used for risk calculations
- `max_leverage`: Maximum leverage allowed - used for leverage validation
- `liquidation_threshold`: Liquidation threshold - used for risk monitoring

**Venue Configuration** (from `configs/venues/*.yaml`):
- `risk_parameters`: Venue-specific risk parameters - used for venue risk calculations
- `collateral_requirements`: Collateral requirements - used for risk assessment

**Share Class Configuration** (from `configs/share_classes/*.yaml`):
- `risk_tolerance`: Risk tolerance level - used for risk limit calculations
- `max_exposure`: Maximum exposure limits - used for exposure validation

**Cross-Reference**: [CONFIGURATION.md](CONFIGURATION.md) - Complete configuration hierarchy
**Cross-Reference**: [ENVIRONMENT_VARIABLES.md](../ENVIRONMENT_VARIABLES.md) - Environment variable definitions

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
- Risk calculation algorithms (hard-coded formulas)
- Risk threshold values (hard-coded limits)
- Risk history retention (hard-coded limits)

## Config Fields Used

### Universal Config (All Components)
- `strategy_mode`: str - e.g., 'eth_basis', 'pure_lending'
- `share_class`: str - 'usdt_stable' | 'eth_directional'
- `initial_capital`: float - Starting capital

### Component-Specific Config
- `target_ltv`: float - Target LTV ratio for AAVE positions
  - **Usage**: Determines risk threshold for AAVE positions
  - **Default**: 0.8 (80%)
  - **Validation**: Must be > 0 and < 1.0

- `max_drawdown`: float - Maximum drawdown limit
  - **Usage**: Risk limit for overall portfolio
  - **Default**: 0.2 (20%)
  - **Validation**: Must be > 0 and < 0.5

- `risk_history_limit`: int - Maximum risk history entries
  - **Usage**: Limits memory usage for risk history
  - **Default**: 1000
  - **Validation**: Must be > 0

### Config Access Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    # Read config fields (NEVER modify)
    target_ltv = self.config.get('target_ltv', 0.8)
    max_drawdown = self.config.get('max_drawdown', 0.2)
```

### Behavior NOT Determinable from Config
- Risk calculation formulas (hard-coded algorithms)
- Risk alert thresholds (hard-coded values)
- Risk metric precision (hard-coded decimal places)

## Data Provider Queries

### Data Types Requested
`data = self.data_provider.get_data(timestamp)`

#### Market Data
- `prices`: Dict[str, float] - Token prices in USD
  - **Tokens needed**: ETH, USDT, BTC, LST tokens, AAVE tokens
  - **Update frequency**: 1min
  - **Usage**: Risk calculations and position valuation

#### Protocol Data
- `aave_indexes`: Dict[str, float] - AAVE liquidity indexes
  - **Tokens needed**: aETH, aUSDT, aBTC, variableDebtETH, etc.
  - **Update frequency**: 1min
  - **Usage**: LTV and health factor calculations

### Query Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    data = self.data_provider.get_data(timestamp)
    prices = data['market_data']['prices']
    aave_indexes = data['protocol_data']['aave_indexes']
```

### Data NOT Available from DataProvider
None - all data comes from DataProvider

## Data Access Pattern

### Query Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    # Query data using shared clock
    data = self.data_provider.get_data(timestamp)
    prices = data['market_data']['prices']
    aave_indexes = data['protocol_data']['aave_indexes']
    
    # Access other components via references
    positions = self.position_monitor.get_current_positions()
    exposure = self.exposure_monitor.get_current_exposure()
```

### Data Dependencies
- **PositionMonitor**: Current positions for risk calculations
- **ExposureMonitor**: Current exposure for risk assessment
- **DataProvider**: Market data and protocol data

## Mode-Aware Behavior

### Backtest Mode
```python
def calculate_risk_metrics(self, timestamp: pd.Timestamp, positions: Dict, market_data: Dict):
    if self.execution_mode == 'backtest':
        # Use historical data for risk calculations
        return self._calculate_risk_with_historical_data(positions, market_data)
```

### Live Mode
```python
def calculate_risk_metrics(self, timestamp: pd.Timestamp, positions: Dict, market_data: Dict):
    elif self.execution_mode == 'live':
        # Use real-time data for risk calculations
        return self._calculate_risk_with_realtime_data(positions, market_data)
```

## Event Logging Requirements

### Component Event Log File
**Separate log file** for this component's events:
- **File**: `logs/events/risk_monitor_events.jsonl`
- **Format**: JSON Lines (one event per line)
- **Rotation**: Daily rotation, keep 30 days
- **Purpose**: Component-specific audit trail

### Event Logging via EventLogger
All events logged through centralized EventLogger:

```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='[event_type]',
    component='RiskMonitor',
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
    component='RiskMonitor',
    data={
        'execution_mode': self.execution_mode,
        'config_hash': hash(str(self.config))
    }
)
```

#### 2. State Updates (Every update_state() Call)
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='state_update',
    component='RiskMonitor',
    data={
        'trigger_source': trigger_source,
        'ltv_ratio': self.current_risk_metrics.get('ltv_ratio', 0),
        'health_factor': self.current_risk_metrics.get('health_factor', 0),
        'processing_time_ms': processing_time
    }
)
```

#### 3. Error Events
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='error',
    component='RiskMonitor',
    data={
        'error_code': 'RISK-001',
        'error_message': str(e),
        'stack_trace': traceback.format_exc(),
        'error_severity': 'CRITICAL|HIGH|MEDIUM|LOW'
    }
)
```

#### 4. Component-Specific Critical Events
- **Risk Alert Triggered**: When risk thresholds are exceeded
- **Risk Calculation Failed**: When risk calculation fails
- **Health Factor Critical**: When health factor drops below threshold

### Event Retention & Output Formats

#### Dual Logging Approach
**Both formats are used**:
1. **JSON Lines (Iterative)**: Write events to component-specific JSONL files during execution
   - **Purpose**: Real-time monitoring during backtest runs
   - **Location**: `logs/events/risk_monitor_events.jsonl`
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

### Component Error Code Prefix: RISK
All RiskMonitor errors use the `RISK` prefix.

### Error Code Registry
**Source**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`

All error codes registered with:
- **code**: Unique error code
- **component**: Component name
- **severity**: CRITICAL | HIGH | MEDIUM | LOW
- **message**: Human-readable error message
- **resolution**: How to resolve

### Component Error Codes

#### RISK-001: Risk Calculation Failed (HIGH)
**Description**: Failed to calculate risk metrics
**Cause**: Invalid position data, missing market data, calculation errors
**Recovery**: Retry with fallback values, check data availability
```python
raise ComponentError(
    error_code='RISK-001',
    message='Risk calculation failed',
    component='RiskMonitor',
    severity='HIGH'
)
```

#### RISK-002: Health Factor Critical (CRITICAL)
**Description**: Health factor dropped below critical threshold
**Cause**: High LTV ratio, price volatility, liquidation risk
**Recovery**: Immediate action required, check position safety
```python
raise ComponentError(
    error_code='RISK-002',
    message='Health factor critical - liquidation risk',
    component='RiskMonitor',
    severity='CRITICAL'
)
```

#### RISK-003: Risk Alert Generation Failed (MEDIUM)
**Description**: Failed to generate risk alerts
**Cause**: Alert system issues, notification failures
**Recovery**: Log warning, continue processing, check alert system
```python
raise ComponentError(
    error_code='RISK-003',
    message='Risk alert generation failed',
    component='RiskMonitor',
    severity='MEDIUM'
)
```

### Structured Error Handling Pattern

#### Error Raising
```python
from backend.src.basis_strategy_v1.core.error_codes.exceptions import ComponentError

try:
    result = self._calculate_risk_metrics(positions, market_data)
except Exception as e:
    # Log error event
    self.event_logger.log_event(
        timestamp=timestamp,
        event_type='error',
        component='RiskMonitor',
        data={
            'error_code': 'RISK-001',
            'error_message': str(e),
            'stack_trace': traceback.format_exc()
        }
    )
    
    # Raise structured error
    raise ComponentError(
        error_code='RISK-001',
        message=f'RiskMonitor failed: {str(e)}',
        component='RiskMonitor',
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
        component_name='RiskMonitor',
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
            'ltv_ratio': self.current_risk_metrics.get('ltv_ratio', 0),
            'health_factor': self.current_risk_metrics.get('health_factor', 0)
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
- [ ] Component-specific log file documented (`logs/events/risk_monitor_events.jsonl`)

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

### **YAML Configuration**
**Mode Configuration** (from `configs/modes/*.yaml`):
- `target_ltv`: Target LTV ratio (float) - used for AAVE risk calculations
- `max_drawdown`: Maximum drawdown (float) - used for risk limits
- `leverage_enabled`: Enable leverage (boolean) - affects risk calculations
- `hedge_venues`: List of hedge venues - used for margin ratio calculations
- `hedge_allocation`: Hedge allocation per venue - used for risk distribution

**Venue Configuration** (from `configs/venues/*.yaml`):
- `venue`: Venue identifier - used for venue-specific risk calculations
- `type`: Venue type ('cex' | 'dex' | 'onchain') - affects risk logic
- `max_leverage`: Maximum leverage - used for margin ratio calculations
- `trading_fees`: Fee structure - used for cost calculations

**Share Class Configuration** (from `configs/share_classes/*.yaml`):
- `risk_level`: Risk level ('low_to_medium' | 'medium_to_high') - affects risk thresholds
- `market_neutral`: Market neutral flag (boolean) - affects risk calculations

**Cross-Reference**: [CONFIGURATION.md](CONFIGURATION.md) - Complete configuration hierarchy
**Cross-Reference**: [ENVIRONMENT_VARIABLES.md](../ENVIRONMENT_VARIABLES.md) - Environment variable definitions

## Core Methods

### update_state(timestamp: pd.Timestamp, trigger_source: str, **kwargs)
Main entry point for risk calculations.

Parameters:
- timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
- trigger_source: 'full_loop' | 'tight_loop' | 'manual'
- **kwargs: Additional parameters (not used)

Behavior:
1. Query data using: market_data = self.data_provider.get_data(timestamp)
2. Access other components via references: positions = self.position_monitor.get_current_positions()
3. Calculate risk metrics based on current state
4. NO async/await: Synchronous execution only

Returns:
- None (state updated in place)

### get_current_risk_metrics() -> Dict
Get current risk metrics snapshot.

Returns:
- Dict: Current risk metrics

---

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) <!-- Link is valid --> - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

---

## 🎯 **Purpose**

Monitor three types of risk using exposure data:
1. **AAVE LTV Risk** - Loan-to-value ratio on lending protocol
2. **CEX Margin Risk** - Margin ratios on perpetual futures
3. **Net Delta Risk** - Deviation from target delta (market neutrality)

**Key Principles**:
- **Reactive**: Triggered by Exposure Monitor updates
- **Multi-venue**: Track each CEX separately
- **Threshold-based**: Warning, urgent, critical levels
- **Fail-safe**: Conservative thresholds (user buffer above venue liquidation)

**Data Flow Integration**:
- **Input**: Receives `exposure` and `market_data` as parameters
- **Method**: `assess_risk(exposure, market_data=None)`
- **No Direct Dependencies**: Doesn't hold DataProvider references
- **Data Source**: Exposure data from ExposureMonitor, market data from EventDrivenStrategyEngine

---

## 📊 **Data Structures**

### **Input**: Exposure Data (from Exposure Monitor)

```python
{
    'timestamp': timestamp,
    'exposures': {...},  # Per-token breakdown
    'net_delta_eth': -5.118,
    'erc20_wallet_net_delta_eth': +3.104,
    'cex_wallet_net_delta_eth': -8.222,
    'total_value_usd': 99753.45
}
```

### **Output**: Risk Metrics

```python
{
    'timestamp': timestamp,
    
    # AAVE Risk
    'aave': {
        'ltv': 0.892,                    # Current LTV (debt / collateral)
        'health_factor': 1.067,          # (LT × collateral) / debt
        'collateral_value_eth': 107.44,
        'debt_value_eth': 95.796,
        'safe_ltv_threshold': 0.91,      # From config (target operating LTV)
        'max_ltv': 0.93,                 # AAVE protocol max (can't withdraw above this)
        'liquidation_threshold': 0.95,   # LTV where liquidation happens (weETH E-mode)
        'liquidation_bonus': 0.01,       # Penalty if liquidated (1% for E-mode)
        'buffer_to_max_ltv': 0.038,      # 93% - 89.2% = 3.8%
        'pct_move_to_liquidation': 6.25, # % ETH can drop before liquidation (based on HF)
        'status': 'SAFE',                # 'SAFE', 'WARNING', 'CRITICAL'
        'warning': False,                # ltv > 85%
        'critical': False                # ltv > 90%
    },
    
    # CEX Margin Risk (per exchange)
    'cex_margin': {
        'binance': {
            'balance_usdt': 24992.50,
            'exposure_usdt': 28299.47,      # Mark-to-market value of perps
            'margin_ratio': 0.883,          # balance / exposure
            'required_margin': 4244.92,     # 15% initial margin
            'free_margin': 20747.58,        # balance - required
            'maintenance_margin': 0.10,     # Binance liquidation threshold
            'buffer_to_liquidation': 0.783, # 88.3% - 10% = 78.3%
            'status': 'SAFE',
            'warning': False,               # ratio < 20%
            'critical': False               # ratio < 12%
        },
        'bybit': {
            'balance_usdt': 24985.30,
            'exposure_usdt': 28277.38,
            'margin_ratio': 0.884,
            'status': 'SAFE',
            'warning': False,
            'critical': False
        },
        'okx': {
            'balance_usdt': 24980.15,
            'exposure_usdt': 28267.89,
            'margin_ratio': 0.884,
            'status': 'SAFE',
            'warning': False,
            'critical': False
        },
        'min_margin_ratio': 0.883,          # Worst exchange
        'any_warning': False,
        'any_critical': False
    },
    
    # Net Delta Risk
    'delta': {
        'net_delta_eth': -5.118,
        'target_delta_eth': 0.0,            # From mode (0 for market-neutral)
        'delta_drift_eth': -5.118,          # Current - target
        'delta_drift_pct': -3.01,           # vs initial capital in ETH
        'drift_threshold_pct': 5.0,         # From config
        'status': 'SAFE',                   # < 5% is safe
        'warning': False,                   # > 3%
        'critical': False                   # > 5%
    },
    
    # Overall status (worst of all risks)
    'overall_status': 'SAFE',               # 'SAFE', 'WARNING', 'CRITICAL'
    'any_warnings': False,
    'any_critical_alerts': False,
    
    # Alerts (list of triggered alerts)
    'alerts': []  # e.g., ['binance_margin_warning', 'delta_drift_warning']
}
```

---

## 💻 **Core Functions**

```python
class RiskMonitor:
    """Monitor all risk metrics."""
    
    def __init__(self, config, exposure_monitor=None, data_provider=None):
        self.config = config
        self.exposure_monitor = exposure_monitor
        self.data_provider = data_provider
        
        # Risk thresholds from config (FAIL-FAST - no .get() defaults!)
        self.aave_safe_ltv = config['strategy']['target_ltv']  # Fail if missing
        self.aave_ltv_warning = config['risk']['aave_ltv_warning']  # Fail if missing
        self.aave_ltv_critical = config['risk']['aave_ltv_critical']  # Fail if missing
        
        # Load AAVE risk parameters (liquidation bonuses)
        import json
        from pathlib import Path
        risk_params_path = Path(config.get('data_dir', 'data')) / 'protocol_data/aave/risk_params/aave_v3_risk_parameters.json'
        with open(risk_params_path, 'r') as f:
            self.aave_risk_params = json.load(f)
        self.aave_liquidation_bonus_emode = self.aave_risk_params['emode']['liquidation_bonus']['weETH_WETH']  # 0.01
        self.aave_liquidation_threshold_emode = self.aave_risk_params['emode']['liquidation_thresholds']['weETH_WETH']  # 0.95
        
        self.margin_warning_threshold = config['risk']['margin_warning_pct']  # e.g., 0.20
        self.margin_critical_threshold = config['risk']['margin_critical_pct']  # e.g., 0.12
        self.margin_liquidation = 0.10  # Venue constant (all CEXs)
        
        self.delta_threshold_pct = config['strategy']['rebalance_threshold_pct']  # e.g., 5.0
        
        # Using direct method calls for component communication
    
    def assess_risk(self, exposure_data: Dict, timestamp: pd.Timestamp = None) -> Dict:
        """
        Unified risk assessment (PUBLIC API - called by EventDrivenStrategyEngine).
        
        This is a wrapper that calls calculate_overall_risk() internally.
        """
        return self.calculate_overall_risk(exposure_data)
    
    def calculate_risks(self, exposure_data: Dict) -> Dict:
        """
        Calculate all risk metrics from exposure data.
        
        Triggered by: Exposure Monitor updates
        
        Returns: Complete risk assessment
        """
        risks = {
            'timestamp': exposure_data['timestamp'],
            'aave': self._calculate_aave_risk(exposure_data),
            'cex_margin': self._calculate_cex_margin_risk(exposure_data),
            'delta': self._calculate_delta_risk(exposure_data),
        }
        
        # Overall status (worst of all)
        all_statuses = [
            risks['aave']['status'],
            risks['cex_margin'].get('min_status', 'SAFE'),
            risks['delta']['status']
        ]
        
        if 'CRITICAL' in all_statuses:
            risks['overall_status'] = 'CRITICAL'
        elif 'WARNING' in all_statuses:
            risks['overall_status'] = 'WARNING'
        else:
            risks['overall_status'] = 'SAFE'
        
        # Collect all alerts
        risks['alerts'] = self._collect_alerts(risks)
        risks['any_warnings'] = any(s['warning'] for s in [risks['aave'], risks['delta']] + list(risks['cex_margin'].values()) if isinstance(s, dict) and 'warning' in s)
        risks['any_critical_alerts'] = any(s['critical'] for s in [risks['aave'], risks['delta']] + list(risks['cex_margin'].values()) if isinstance(s, dict) and 'critical' in s)
        
            # Components use direct method calls
            'alerts': risks['alerts']
        }))
        
        return risks
    
    def _calculate_aave_risk(self, exposure_data: Dict) -> Dict:
        """Calculate AAVE LTV and health factor risk."""
        # Get AAVE exposures
        aave_collateral_eth = 0.0
        aave_debt_eth = 0.0
        
        for token, exp in exposure_data['exposures'].items():
            if 'aWeETH' in token or 'awstETH' in token:
                aave_collateral_eth += exp['exposure_eth']
            elif 'variableDebt' in token:
                aave_debt_eth += exp['exposure_eth']
        
        # Calculate metrics
        if aave_collateral_eth > 0 and aave_debt_eth > 0:
            ltv = aave_debt_eth / aave_collateral_eth
            
            # Health Factor = (LT × collateral) / debt
            liquidation_threshold = 0.95  # E-mode for weETH/wstETH (this is the LTV where liquidation happens)
            health_factor = (liquidation_threshold * aave_collateral_eth) / aave_debt_eth
            
            # Calculate % move to liquidation
            # HF = 1 means liquidation
            # Current HF = 1.067
            # ETH can drop by: (1 - 1/HF) × 100 = (1 - 1/1.067) × 100 = 6.28%
            pct_move_to_liquidation = (1 - 1/health_factor) * 100 if health_factor > 1 else 0
        else:
            ltv = 0.0
            health_factor = float('inf')
            pct_move_to_liquidation = 100.0  # No risk
        
        # Check thresholds
        warning = ltv > self.aave_ltv_warning
        critical = ltv > self.aave_ltv_critical
        
        if critical:
            status = 'CRITICAL'
        elif warning:
            status = 'WARNING'
        else:
            status = 'SAFE'
        
        return {
            'ltv': ltv,
            'health_factor': health_factor,
            'collateral_value_eth': aave_collateral_eth,
            'debt_value_eth': aave_debt_eth,
            'safe_ltv_threshold': self.aave_safe_ltv,
            'liquidation_ltv': 0.93,  # AAVE E-mode max
            'liquidation_threshold': liquidation_threshold,
            'buffer_to_liquidation': 0.93 - ltv,
            'status': status,
            'warning': warning,
            'critical': critical
        }
    
    def _calculate_cex_margin_risk(self, exposure_data: Dict) -> Dict:
        """Calculate CEX margin ratios per exchange."""
        cex_risks = {}
        
        for venue in ['binance', 'bybit', 'okx']:
            # Get CEX balance
            balance_key = f'{venue}_USDT'
            balance_usdt = exposure_data['exposures'].get(balance_key, {}).get('balance', 0)
            
            # Get perp exposure (mark-to-market)
            exposure_usdt = 0.0
            for token, exp in exposure_data['exposures'].items():
                if token.startswith(f'{venue}_') and 'PERP' in token:
                    exposure_usdt += abs(exp['exposure_usd'])
            
            if exposure_usdt > 0:
                margin_ratio = balance_usdt / exposure_usdt
                required_margin = exposure_usdt * 0.15  # 15% initial margin
                free_margin = balance_usdt - required_margin
            else:
                margin_ratio = 1.0
                required_margin = 0.0
                free_margin = balance_usdt
            
            # Check thresholds
            warning = margin_ratio < self.margin_warning_threshold
            critical = margin_ratio < self.margin_critical_threshold
            
            if critical:
                status = 'CRITICAL'
            elif warning:
                status = 'WARNING'
            else:
                status = 'SAFE'
            
            cex_risks[venue] = {
                'balance_usdt': balance_usdt,
                'exposure_usdt': exposure_usdt,
                'margin_ratio': margin_ratio,
                'required_margin': required_margin,
                'free_margin': free_margin,
                'maintenance_margin': self.margin_liquidation,
                'buffer_to_liquidation': margin_ratio - self.margin_liquidation,
                'status': status,
                'warning': warning,
                'critical': critical
            }
        
        # Find worst exchange
        ratios = [v['margin_ratio'] for v in cex_risks.values() if v['exposure_usdt'] > 0]
        min_margin_ratio = min(ratios) if ratios else 1.0
        
        cex_risks['min_margin_ratio'] = min_margin_ratio
        cex_risks['any_warning'] = any(v.get('warning', False) for v in cex_risks.values())
        cex_risks['any_critical'] = any(v.get('critical', False) for v in cex_risks.values())
        
        return cex_risks
    
    def _calculate_delta_risk(self, exposure_data: Dict) -> Dict:
        """Calculate net delta risk."""
        net_delta_eth = exposure_data['net_delta_eth']
        
        # Target delta from config (config-driven parameters)
        target_delta_eth = self.config['strategy']['target_delta_eth']
        
        # Calculate drift
        delta_drift_eth = net_delta_eth - target_delta_eth
        
        # As percentage of TOKEN EQUITY (not initial capital!)
        # This scales properly with deposits/withdrawals
        token_equity_eth = exposure_data['token_equity_eth']
        
        if token_equity_eth > 0:
            delta_drift_pct = (abs(delta_drift_eth) / token_equity_eth) * 100
        else:
            delta_drift_pct = 0.0
        
        # Check thresholds
        warning = delta_drift_pct > (self.delta_threshold_pct * 0.6)  # 60% of threshold
        critical = delta_drift_pct > self.delta_threshold_pct
        
        if critical:
            status = 'CRITICAL'
        elif warning:
            status = 'WARNING'
        else:
            status = 'SAFE'
        
        return {
            'net_delta_eth': net_delta_eth,
            'target_delta_eth': target_delta_eth,
            'delta_drift_eth': delta_drift_eth,
            'delta_drift_pct': delta_drift_pct,
            'drift_threshold_pct': self.delta_threshold_pct,
            'status': status,
            'warning': warning,
            'critical': critical
        }
```

---

## 🔔 **Alert Generation**

```python
def _collect_alerts(self, risks: Dict) -> List[str]:
    """Collect all triggered alerts."""
    alerts = []
    
    # AAVE alerts
    if risks['aave']['critical']:
        alerts.append('AAVE_LTV_CRITICAL')
    elif risks['aave']['warning']:
        alerts.append('AAVE_LTV_WARNING')
    
    # CEX margin alerts (per exchange)
    for venue in ['binance', 'bybit', 'okx']:
        venue_risk = risks['cex_margin'][venue]
        if venue_risk['critical']:
            alerts.append(f'{venue.upper()}_MARGIN_CRITICAL')
        elif venue_risk['warning']:
            alerts.append(f'{venue.upper()}_MARGIN_WARNING')
    
    # Delta alerts
    if risks['delta']['critical']:
        alerts.append('DELTA_DRIFT_CRITICAL')
    elif risks['delta']['warning']:
        alerts.append('DELTA_DRIFT_WARNING')
    
    return alerts
```

---

    def simulate_liquidation(
        self,
        collateral_eth: float,
        debt_eth: float,
        eth_price_drop_pct: float
    ) -> Optional[Dict]:
        """
        Simulate AAVE liquidation if ETH drops by X%.
        
        AAVE v3 Liquidation Logic:
        1. If HF < 1, position can be liquidated
        2. Liquidator repays up to 50% of debt on your behalf
        3. Liquidator seizes: debt_repaid × (1 + liquidation_bonus) of collateral
        4. You lose collateral > debt repaid (the bonus is your penalty)
        
        Example:
        - Liquidator repays 100 WETH debt
        - Liquidator seizes 101 WETH worth of weETH (1% bonus)
        - You lose 1 WETH extra (incentive for liquidators)
        
        Args:
            collateral_eth: Current AAVE collateral in ETH
            debt_eth: Current AAVE debt in ETH
            eth_price_drop_pct: How much ETH drops (e.g., 10 for 10%)
        
        Returns:
            Liquidation result dict or None if position remains safe
        """
        # Simulate price drop (collateral value drops)
        new_collateral_eth = collateral_eth * (1 - eth_price_drop_pct / 100)
        
        # Debt unchanged (denominated in ETH/WETH)
        new_debt_eth = debt_eth
        
        # Calculate new health factor
        liquidation_threshold = 0.95  # weETH E-mode
        new_hf = (liquidation_threshold * new_collateral_eth) / new_debt_eth if new_debt_eth > 0 else float('inf')
        
        if new_hf >= 1.0:
            return None  # Safe, no liquidation
        
        # Liquidation triggered!
        logger.warning(f"🚨 LIQUIDATION SIMULATED: HF={new_hf:.3f} after {eth_price_drop_pct}% ETH drop")
        
        # Liquidator repays up to 50% of debt (AAVE protocol rule)
        max_debt_repaid_eth = new_debt_eth * 0.50
        
        # Liquidator seizes collateral (with bonus)
        liquidation_bonus = 0.01  # 1% for E-mode (5-7% for normal mode)
        collateral_seized_eth = max_debt_repaid_eth * (1 + liquidation_bonus)
        
        # Position after liquidation
        remaining_collateral_eth = new_collateral_eth - collateral_seized_eth
        remaining_debt_eth = new_debt_eth - max_debt_repaid_eth
        
        # Health factor after liquidation (should be > 1 now)
        post_liquidation_hf = (liquidation_threshold * remaining_collateral_eth) / remaining_debt_eth if remaining_debt_eth > 0 else float('inf')
        post_liquidation_ltv = remaining_debt_eth / remaining_collateral_eth if remaining_collateral_eth > 0 else 0
        
        return {
            'liquidated': True,
            'trigger': f'ETH dropped {eth_price_drop_pct}%, HF fell below 1.0',
            'pre_liquidation': {
                'collateral_eth': new_collateral_eth,
                'debt_eth': new_debt_eth,
                'health_factor': new_hf,
                'ltv': new_debt_eth / new_collateral_eth if new_collateral_eth > 0 else 0
            },
            'liquidation_details': {
                'debt_repaid_eth': max_debt_repaid_eth,
                'collateral_seized_eth': collateral_seized_eth,
                'liquidation_bonus': liquidation_bonus,
                'user_loss_eth': collateral_seized_eth - max_debt_repaid_eth  # Penalty
            },
            'post_liquidation': {
                'remaining_collateral_eth': remaining_collateral_eth,
                'remaining_debt_eth': remaining_debt_eth,
                'health_factor': post_liquidation_hf,
                'ltv': post_liquidation_ltv
            }
        }

    
    def simulate_cex_liquidation(
        self,
        venue: str,
        current_margin_usdt: float,
        position_exposure_usdt: float
    ) -> Optional[Dict]:
        """
        Simulate CEX liquidation (catastrophic - lose ALL margin).
        
        CEX Liquidation (Binance/Bybit/OKX):
        - Maintenance margin: 10%
        - If margin_ratio < 10%: LIQUIDATION TRIGGERED
        - Result: Account balance → 0 (ALL margin lost)
        - Position closed at market
        
        Args:
            venue: Exchange (binance, bybit, okx)
            current_margin_usdt: Current margin balance
            position_exposure_usdt: Mark-to-market position value
            
        Returns:
            Liquidation result or None if safe
        """
        maintenance_margin = 0.10
        margin_ratio = current_margin_usdt / position_exposure_usdt if position_exposure_usdt > 0 else 1.0
        
        if margin_ratio >= maintenance_margin:
            return None  # Safe
        
        # CATASTROPHIC LIQUIDATION
        return {
            'liquidated': True,
            'venue': venue,
            'margin_lost': current_margin_usdt,  # ALL
            'remaining_balance': 0.0,
            'balance_updates': {
                f'{venue}_USDT': 0.0  # Account wiped
            }
        }

---

## 🔗 **Integration**

### **Triggered By**:
- Exposure Monitor updates (sync chain: position → exposure → risk)

### **Uses Data From**:
- **Exposure Monitor** ← Exposure breakdown
- **Config** ← Risk thresholds

### **Provides Data To**:
- **Strategy Manager** ← Risk metrics (for rebalancing decisions)
- **Event Logger** ← Risk alerts

### **Component Communication**:

**Direct Method Calls**:
- Exposure Monitor → Triggers risk calculation via direct method calls
- Strategy Manager ← Risk metrics via direct method calls
- Event Logger ← Risk alerts via direct method calls

---

## 🧪 **Testing**

```python
def test_aave_ltv_calculation():
    """Test AAVE LTV and HF calculations."""
    exposure = {
        'exposures': {
            'aWeETH': {'exposure_eth': 107.44},
            'variableDebtWETH': {'exposure_eth': 95.796}
        }
    }
    
    risk = RiskMonitor(config, exposure_monitor)
    aave_risk = risk._calculate_aave_risk(exposure)
    
    # LTV = debt / collateral
    expected_ltv = 95.796 / 107.44
    assert aave_risk['ltv'] == pytest.approx(expected_ltv, abs=0.001)
    
    # HF = (0.95 × 107.44) / 95.796
    expected_hf = (0.95 * 107.44) / 95.796
    assert aave_risk['health_factor'] == pytest.approx(expected_hf, abs=0.001)

def test_margin_ratio_warning():
    """Test CEX margin warnings trigger correctly."""
    exposure = {
        'exposures': {
            'binance_USDT': {'balance': 5000},  # Low balance
            'binance_ETHUSDT-PERP': {'exposure_usd': 28000}  # High exposure
        }
    }
    
    risk = RiskMonitor(config, exposure_monitor)
    cex_risk = risk._calculate_cex_margin_risk(exposure)
    
    # Margin ratio = 5000 / 28000 = 17.9% (below 20% warning!)
    assert cex_risk['binance']['margin_ratio'] < 0.20
    assert cex_risk['binance']['warning'] == True
    assert cex_risk['binance']['status'] == 'WARNING'
```

---

## 🎯 **Mode-Specific Behavior**

### **Pure Lending**:
```python
# Only AAVE risk matters
# No CEX margin risk (no perps)
# No delta risk (no hedging)
```

### **BTC Basis**:
```python
# No AAVE risk (no lending)
# CEX margin risk (BTC perps)
# Delta risk (should be ~0 for market-neutral)
```

### **ETH Leveraged** (ETH share class):
```python
# AAVE risk (leveraged staking)
# No CEX margin risk (no hedging)
# No delta risk (directional ETH exposure is the strategy!)
```

### **USDT Market-Neutral**:
```python
# All three risks monitored!
# Most complex
```

---

## 🔄 **Backtest vs Live**

### **Backtest**:
- Triggered by exposure updates (sync chain)
- Calculates once per hour
- Logs warnings to console + event log

### **Live**:
- Same calculation logic
- But also:
  - Triggers real-time alerts (email, Telegram, etc.)
  - Can trigger emergency stops
  - Logs to monitoring system (Prometheus)

---

## 🔧 **Current Implementation Status**

**Overall Completion**: 90% (Core functionality working, minor config integration needed)

### **Core Functionality Status**
- ✅ **Working**: AAVE LTV calculation, AAVE health factor calculation, margin ratios per exchange, delta drift calculation, warning triggers, critical alerts, mode-aware risk assessment, direct method calls, conservative thresholds, generic risk calculation logic
- ⚠️ **Partial**: Minor config integration (funding rate needs config YAML integration)
- ❌ **Missing**: None
- 🔄 **Refactoring Needed**: Minor config integration

## Related Documentation
- [Reference-Based Architecture](../REFERENCE_ARCHITECTURE_CANONICAL.md)
- [Shared Clock Pattern](../SHARED_CLOCK_PATTERN.md)
- [Request Isolation Pattern](../REQUEST_ISOLATION_PATTERN.md)

### **Component Integration**
- [Position Monitor Specification](01_POSITION_MONITOR.md) - Provides position data for risk calculations
- [Exposure Monitor Specification](02_EXPOSURE_MONITOR.md) - Provides exposure data for risk calculations
- [P&L Calculator Specification](04_PNL_CALCULATOR.md) - Depends on Risk Monitor for risk metrics
- [Strategy Manager Specification](05_STRATEGY_MANAGER.md) - Depends on Risk Monitor for risk metrics
- [Data Provider Specification](09_DATA_PROVIDER.md) - Provides market data for risk calculations
- [Event Logger Specification](08_EVENT_LOGGER.md) - Logs risk assessment events
- [Position Update Handler Specification](11_POSITION_UPDATE_HANDLER.md) - Triggers risk updates

### **Architecture Compliance Status**
- ✅ **COMPLIANT**: Component follows canonical architectural principles
  - **Reference-Based Architecture**: Components receive references at init, never pass as runtime parameters
  - **Shared Clock Pattern**: All methods receive timestamp from EventDrivenStrategyEngine
  - **Request Isolation Pattern**: Fresh instances per backtest/live request
  - **Synchronous Component Execution**: Internal methods are synchronous, async only for I/O operations
  - **Mode-Aware Behavior**: Uses BASIS_EXECUTION_MODE for conditional logic
  - **Generic Risk Calculation**: Uses generic risk calculation logic instead of mode-specific PnL calculator logic

### **Implementation Status**
- **High Priority**:
  - Add funding rate to config YAML instead of hardcoding (line 912 in risk_monitor.py)
- **Medium Priority**:
  - Optimize risk calculation performance
- **Low Priority**:
  - None identified

### **Quality Gate Status**
- **Current Status**: PARTIAL
- **Failing Tests**: Config integration tests
- **Requirements**: Complete config integration for funding rate
- **Integration**: Integrates with quality gate system through risk monitor quality gates

### **Task Completion Status**
- **Related Tasks**: 
  - [.cursor/tasks/15_fix_mode_specific_pnl_calculator.md](../../.cursor/tasks/15_fix_mode_specific_pnl_calculator.md) - Mode-Specific PnL Calculator (100% complete - generic logic implemented)
  - [.cursor/tasks/06_architecture_compliance_rules.md](../../.cursor/tasks/06_architecture_compliance_rules.md) - No Hardcoded Values (95% complete - minor config integration needed)
- **Completion**: 90% complete overall
- **Blockers**: Minor config integration
- **Next Steps**: Add funding rate to config YAML

---

## 🎯 **Success Criteria**

- [ ] Calculates AAVE LTV correctly
- [ ] Calculates AAVE health factor correctly (HF = LT × C / D)
- [ ] Calculates margin ratios per exchange
- [ ] Calculates delta drift
- [ ] Triggers warnings at correct thresholds
- [ ] Triggers critical alerts before liquidation
- [ ] Mode-aware (only relevant risks per mode)
- [ ] Communicates with Strategy Manager via direct method calls
- [ ] Conservative thresholds (user buffer above venue limits)

---

**Status**: Specification complete! ✅

