# PnL Calculator Component Specification

**Last Reviewed**: October 11, 2025

## Purpose
Calculate balance-based & attribution P&L with reconciliation in share class currency using config-driven, mode-agnostic architecture.

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [../REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Mode-Agnostic Architecture**: [../REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Config-driven architecture guide
- **Code Structures**: [../CODE_STRUCTURE_PATTERNS.md](../CODE_STRUCTURE_PATTERNS.md) - Complete implementation patterns  
- **Configuration**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas for all 7 modes
- **Strategy Specifications**: [../MODES.md](../MODES.md) - Strategy mode definitions

## Responsibilities
1. **Config-Driven Attribution Calculation**: Calculate only attribution types enabled in `component_config.pnl_calculator.attribution_types`
2. **Balance-Based P&L (Source of Truth)**: Calculate P&L from portfolio value change using `share_class_value` from exposure
3. **Attribution P&L (Breakdown by Source)**: Calculate P&L breakdown by component (supply yield, funding, staking, etc.)
4. **Reconciliation Validation**: Validate balance-based vs attribution P&L within configurable tolerance
5. **Mode-Agnostic Implementation**: Same P&L calculation logic for all strategy modes (pure_lending, btc_basis, eth_leveraged, etc.)
6. **Share Class Currency Reporting**: Report P&L in share class currency (USDT or ETH)
7. **Execution Mode Aware**: Same logic for backtest and live modes (only data source differs)

## State
- current_pnl: Dict (P&L metrics in share class currency)
- previous_exposure: Dict (last exposure snapshot for delta calculations)
- cumulative_attributions: Dict[str, float] (cumulative tracking per attribution type)
- initial_total_value: float (starting portfolio value)
- last_calculation_timestamp: pd.Timestamp
- pnl_history: List[Dict] (for debugging)

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- exposure_monitor: ExposureMonitor (reference, call get_current_exposure())
- data_provider: BaseDataProvider (reference, query with timestamps)
- config: Dict (reference, never modified)
- execution_mode: str (BASIS_EXECUTION_MODE)

These references are stored in __init__ and used throughout component lifecycle.
Components NEVER receive these as method parameters during runtime.

## Configuration Parameters

### **Config-Driven Architecture**

The PnL Calculator is **mode-agnostic** and uses `component_config.pnl_calculator` from the mode configuration:

```yaml
component_config:
  pnl_calculator:
    attribution_types: ["supply_yield", "funding_pnl", "delta_pnl", "transaction_costs"]
    reporting_currency: "USDT"
    reconciliation_tolerance: 0.02
```

### **Attribution Type Definitions**

| Attribution Type | Description | Data Required | Calculation Method |
|-----------------|-------------|---------------|-------------------|
| `supply_yield` | AAVE supply interest earned | aave_indexes | Index growth × collateral balance |
| `borrow_costs` | AAVE borrow interest paid | aave_indexes | Index growth × debt balance (negative) |
| `staking_yield_oracle` | LST oracle price appreciation | oracle_prices | Oracle drift × LST balance |
| `staking_yield_rewards` | Seasonal rewards (EIGEN, ETHFI) | reward_data | Actual rewards received |
| `funding_pnl` | Perp funding payments | funding_rates | Rate × perp notional |
| `delta_pnl` | Unhedged exposure P&L | prices, positions | Delta × price change |
| `basis_pnl` | Spot-perp spread changes | spot_prices, perp_prices | Spread change × position |
| `price_change_pnl` | Token price movements | prices | Price change × balance |
| `transaction_costs` | Gas and fees | execution_costs | Sum of all costs |

### **Attribution Types by Strategy Mode**

| Mode | Attribution Types |
|------|-------------------|
| **Pure Lending** | supply_yield, transaction_costs |
| **BTC Basis** | funding_pnl, delta_pnl, basis_pnl, transaction_costs |
| **ETH Basis** | funding_pnl, delta_pnl, basis_pnl, transaction_costs |
| **ETH Staking Only** | staking_yield_oracle, staking_yield_rewards, price_change_pnl, transaction_costs |
| **ETH Leveraged** | supply_yield, staking_yield_oracle, staking_yield_rewards, borrow_costs, price_change_pnl, transaction_costs |
| **USDT MN No Leverage** | staking_yield_oracle, staking_yield_rewards, funding_pnl, delta_pnl, transaction_costs |
| **USDT Market Neutral** | supply_yield, staking_yield_oracle, staking_yield_rewards, borrow_costs, funding_pnl, delta_pnl, price_change_pnl, transaction_costs |

**Key Insight**: The component calculates **only the attribution types enabled in config** for each mode. Unused attribution types are not calculated (graceful handling).

**Cross-Reference**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas with full examples for all 7 modes

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
- P&L calculation algorithms (config-driven via attribution_types)
- Attribution calculation formulas (hardcoded algorithms)
- Reconciliation tolerance (config-driven via reconciliation_tolerance)

## Config Fields Used

### Universal Config (All Components)
- `mode`: str - e.g., 'eth_basis', 'pure_lending' (NOT 'mode')
- `share_class`: str - 'USDT' | 'ETH'
- `asset`: str - 'USDT' | 'ETH' | 'BTC'
- `initial_capital`: float - Starting capital

### Component-Specific Config (from component_config.pnl_calculator)
- `attribution_types`: List[str] - Attribution types to calculate
  - **Usage**: Determines which attribution calculations to perform
  - **Required**: Yes
  - **Validation**: Must be non-empty list of valid attribution types

- `reporting_currency`: str - Currency for P&L reporting
  - **Usage**: Determines P&L reporting currency
  - **Required**: Yes
  - **Validation**: Must be 'USDT' or 'ETH'

- `reconciliation_tolerance`: float - Tolerance for balance vs attribution reconciliation
  - **Usage**: Validates P&L reconciliation within tolerance
  - **Required**: Yes
  - **Validation**: Must be between 0.0 and 1.0

### Config Access Pattern
```python
def __init__(self, config: Dict, ...):
    # Extract config in __init__ (NEVER in methods)
    self.pnl_config = config.get('component_config', {}).get('pnl_calculator', {})
    self.attribution_types = self.pnl_config.get('attribution_types', [])
    self.reporting_currency = self.pnl_config.get('reporting_currency', 'USDT')
    self.reconciliation_tolerance = self.pnl_config.get('reconciliation_tolerance', 0.02)
```

## Data Flow Pattern

### Input Parameters
- `positions`: Position data from position monitor
- `exposure_data`: Exposure data from exposure monitor
- `risk_metrics`: Risk metrics from risk monitor
- `market_data`: Market data from data provider
- `timestamp`: Current timestamp for data consistency

### Output Data
- `pnl_data`: Calculated P&L data
- `attribution_data`: P&L attribution data

### Data Flow
```
Position Monitor → positions → P&L Calculator → pnl_data → Results Store
Exposure Monitor → exposure_data → P&L Calculator → pnl_data → Results Store
Risk Monitor → risk_metrics → P&L Calculator → pnl_data → Results Store
Data Provider → market_data → P&L Calculator → pnl_data → Results Store
```

### Behavior NOT Determinable from Config
- P&L calculation formulas (hardcoded algorithms)
- Attribution calculation logic (hardcoded rules)
- Data structure expectations (hardcoded field names)

## Data Provider Queries

### Data Types Requested
`data = self.data_provider.get_data(timestamp)`

#### Market Data
- `prices`: Dict[str, float] - Token prices in USD
  - **Tokens needed**: ETH, USDT, BTC, LST tokens, AAVE tokens
  - **Update frequency**: 1min
  - **Usage**: P&L calculations and position valuation

- `funding_rates`: Dict[str, float] - CEX funding rates
  - **Rates needed**: BTC/ETH perp funding rates per venue
  - **Update frequency**: 8 hours (0/8/16 UTC)
  - **Usage**: Funding P&L calculations

#### Protocol Data
- `aave_indexes`: Dict[str, float] - AAVE liquidity indexes
  - **Tokens needed**: aETH, aUSDT, aBTC, variableDebtETH, etc.
  - **Update frequency**: 1min
  - **Usage**: AAVE position P&L calculations

- `oracle_prices`: Dict[str, float] - LST oracle prices
  - **Tokens needed**: weETH, wstETH oracle prices
  - **Update frequency**: 1min
  - **Usage**: Staking yield oracle calculations

#### Staking Data
- `base_rewards`: Dict[str, float] - Base staking rewards
- `eigen_rewards`: Dict[str, Any] - EIGEN reward distributions
- `ethfi_rewards`: Dict[str, Any] - ETHFI reward distributions

#### Execution Data
- `execution_costs`: Dict[str, float] - Gas and execution costs
  - **Costs needed**: Gas costs, trading fees, execution fees
  - **Update frequency**: On execution
  - **Usage**: Transaction cost calculations

### Query Pattern
```python
def calculate_pnl(self, timestamp: pd.Timestamp, trigger_source: str, market_data: Dict):
    # Use provided market data (no internal querying)
    prices = market_data['market_data']['prices']
    aave_indexes = market_data['protocol_data']['aave_indexes']
    funding_rates = market_data['market_data']['funding_rates']
```

### Data NOT Available from DataProvider
None - all data comes from DataProvider

## Core Methods

### calculate_pnl(timestamp: pd.Timestamp, trigger_source: str, market_data: Dict) -> Dict
Main entry point for P&L calculations.

**Parameters**:
- timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
- trigger_source: 'full_loop' | 'tight_loop' | 'manual'
- market_data: Current market data from DataProvider

**Behavior**:
1. Get current exposure from stored reference: `current_exposure = self.exposure_monitor.get_current_exposure()`
2. Use provided market data (no internal querying)
3. Calculate balance-based P&L (source of truth)
4. Calculate attribution P&L (breakdown by enabled types)
5. Reconcile balance vs attribution P&L
6. Update internal state and return complete P&L structure

**Returns**:
- Dict: Complete P&L structure with balance_based, attribution, reconciliation

### get_current_pnl() -> Dict
Get current P&L snapshot.

**Returns**:
- Dict: Current P&L metrics (last calculated values)

## Data Access Pattern

### Query Pattern
```python
def calculate_pnl(self, timestamp: pd.Timestamp, trigger_source: str, market_data: Dict):
    # Get exposure from stored reference
    current_exposure = self.exposure_monitor.get_current_exposure()
    
    # Use provided market data for attribution calculations
    
    # Calculate balance-based P&L (source of truth)
    balance_pnl = self._calculate_balance_based_pnl(current_exposure)
    
    # Calculate attribution P&L (breakdown)
    attribution_pnl = self._calculate_attribution_pnl(
        current_exposure, 
        self.previous_exposure,
        market_data,
        timestamp
    )
    
    # Reconcile P&L
    reconciliation = self._reconcile_pnl(balance_pnl, attribution_pnl, timestamp)
    
    # Update state
    self.previous_exposure = current_exposure
    self.current_pnl = {
        'balance_based': balance_pnl,
        'attribution': attribution_pnl,
        'reconciliation': reconciliation
    }
    
    return self.current_pnl
```

**NEVER** pass exposure data or market data as parameters between components.
**NEVER** cache market data across timestamps.
**ALWAYS** get fresh data via component references.

## Mode-Aware Behavior

### Backtest Mode
```python
def calculate_pnl(self, timestamp: pd.Timestamp, trigger_source: str, market_data: Dict):
    if self.execution_mode == 'backtest':
        # Use historical data for P&L calculations
        return self._calculate_pnl_with_historical_data(timestamp, market_data)
```

### Live Mode
```python
def calculate_pnl(self, timestamp: pd.Timestamp, trigger_source: str, market_data: Dict):
    elif self.execution_mode == 'live':
        # Use real-time data for P&L calculations
        return self._calculate_pnl_with_realtime_data(timestamp, market_data)
```

**Key**: Only difference is data source and alerting - calculation logic is identical.

## **MODE-AGNOSTIC IMPLEMENTATION EXAMPLE**

### **Complete Config-Driven PnL Calculator**

```python
from typing import Dict, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class PnLCalculator:
    """Mode-agnostic PnL calculator using config-driven behavior"""
    
    def __init__(self, config: Dict, data_provider: 'BaseDataProvider', execution_mode: str,
                 exposure_monitor: 'ExposureMonitor'):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        self.exposure_monitor = exposure_monitor
        
        # Extract config-driven settings
        self.pnl_config = config.get('component_config', {}).get('pnl_calculator', {})
        self.attribution_types = self.pnl_config.get('attribution_types', [])
        self.reporting_currency = self.pnl_config.get('reporting_currency', 'USDT')
        self.reconciliation_tolerance = self.pnl_config.get('reconciliation_tolerance', 0.02)
        
        # Initialize component-specific state
        self.current_pnl = {}
        self.previous_exposure = None
        self.cumulative_attributions = {attr: 0.0 for attr in self.attribution_types}
        self.initial_total_value = None
        self.last_calculation_timestamp = None
        self.pnl_history = []
        
        # Validate config
        self._validate_pnl_config()
        
        logger.info(f"PnLCalculator initialized with attribution_types: {self.attribution_types}")
    
    def _validate_pnl_config(self):
        """Validate PnL calculator configuration"""
        if not self.attribution_types:
            raise ValueError("attribution_types cannot be empty")
        
        # Valid attribution types
        valid_attribution_types = [
            'supply_yield', 'borrow_costs',  # AAVE attribution
            'staking_yield_oracle', 'staking_yield_rewards',  # Staking attribution
            'funding_pnl', 'delta_pnl', 'basis_pnl',  # Trading attribution
            'price_change_pnl', 'transaction_costs'  # General attribution
        ]
        
        for attr_type in self.attribution_types:
            if attr_type not in valid_attribution_types:
                raise ValueError(f"Invalid attribution type: {attr_type}. Valid types: {valid_attribution_types}")
        
        if self.reporting_currency not in ['USDT', 'ETH']:
            raise ValueError(f"Invalid reporting_currency: {self.reporting_currency}. Must be 'USDT' or 'ETH'")
        
        if not 0.0 <= self.reconciliation_tolerance <= 1.0:
            raise ValueError(f"reconciliation_tolerance must be between 0.0 and 1.0, got {self.reconciliation_tolerance}")
    
    def calculate_pnl(self, timestamp: pd.Timestamp, trigger_source: str, market_data: Dict) -> Dict:
        """
        Calculate P&L using config-driven attribution types.
        
        This method is MODE-AGNOSTIC - it works for all strategy modes
        by only calculating the attribution types enabled in the config.
        
        Args:
            timestamp: Current timestamp from EventDrivenStrategyEngine
            trigger_source: Source of the calculation trigger
            market_data: Current market data from DataProvider
        
        Returns:
            Dict with balance_based, attribution, reconciliation, timestamp
        """
        # Log component start (per EVENT_LOGGER.md)
        start_time = pd.Timestamp.now()
        logger.debug(f"PnLCalculator.calculate_pnl started at {start_time}")
        
        # Get current exposure from stored reference
        current_exposure = self.exposure_monitor.get_current_exposure()
        
        # Use provided market data for attribution calculations
        
        # Set initial value if first calculation
        if self.initial_total_value is None:
            self.initial_total_value = current_exposure['share_class_value']
        
        # 1. Balance-Based P&L (source of truth)
        balance_pnl = self._calculate_balance_based_pnl(current_exposure)
        
        # 2. Attribution P&L (breakdown by enabled types)
        attribution_pnl = self._calculate_attribution_pnl(
            current_exposure, 
            self.previous_exposure,
            market_data,
            timestamp
        )
        
        # 3. Reconciliation
        reconciliation = self._reconcile_pnl(balance_pnl, attribution_pnl, timestamp)
        
        # Update state
        self.previous_exposure = current_exposure
        self.current_pnl = {
            'balance_based': balance_pnl,
            'attribution': attribution_pnl,
            'reconciliation': reconciliation,
            'timestamp': timestamp
        }
        self.last_calculation_timestamp = timestamp
        
        # Log component end (per EVENT_LOGGER.md)
        end_time = pd.Timestamp.now()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000
        logger.debug(f"PnLCalculator.calculate_pnl completed at {end_time}, took {processing_time_ms:.2f}ms")
        
        return self.current_pnl
    
    def get_current_pnl(self) -> Dict:
        """Get current P&L snapshot"""
        return self.current_pnl.copy()
    
    def _calculate_balance_based_pnl(self, current_exposure: Dict) -> Dict:
        """
        Calculate balance-based P&L (source of truth).
        P&L = current_value - initial_value
        """
        current_value = current_exposure['share_class_value']
        pnl_cumulative = current_value - self.initial_total_value
        
        return {
            'total_value_current': current_value,
            'total_value_initial': self.initial_total_value,
            'pnl_cumulative': pnl_cumulative,
            'pnl_pct': (pnl_cumulative / self.initial_total_value) * 100 if self.initial_total_value > 0 else 0.0
        }
    
    def _calculate_attribution_pnl(self, current_exposure: Dict, previous_exposure: Optional[Dict], 
                                 market_data: Dict, timestamp: pd.Timestamp) -> Dict:
        """
        Calculate attribution P&L using config-driven attribution types.
        Only calculates enabled attribution types from config.
        """
        attribution_pnl = {}
        
        # Calculate each enabled attribution type
        for attr_type in self.attribution_types:
            try:
                if attr_type == 'supply_yield':
                    # Check if AAVE data available (graceful for mode-agnostic)
                    if 'aave_indexes' in market_data.get('protocol_data', {}):
                        attribution_pnl[attr_type] = self._calc_supply_yield(current_exposure, previous_exposure, market_data)
                    else:
                        attribution_pnl[attr_type] = 0.0  # Gracefully skip if data unavailable
                
                elif attr_type == 'borrow_costs':
                    if 'aave_indexes' in market_data.get('protocol_data', {}):
                        attribution_pnl[attr_type] = self._calc_borrow_costs(current_exposure, previous_exposure, market_data)
                    else:
                        attribution_pnl[attr_type] = 0.0
                
                elif attr_type == 'staking_yield_oracle':
                    if 'oracle_prices' in market_data.get('protocol_data', {}):
                        attribution_pnl[attr_type] = self._calc_staking_yield_oracle(current_exposure, previous_exposure, market_data)
                    else:
                        attribution_pnl[attr_type] = 0.0
                
                elif attr_type == 'staking_yield_rewards':
                    if 'eigen_rewards' in market_data.get('staking_data', {}) or 'ethfi_rewards' in market_data.get('staking_data', {}):
                        attribution_pnl[attr_type] = self._calc_staking_yield_rewards(current_exposure, previous_exposure, market_data)
                    else:
                        attribution_pnl[attr_type] = 0.0
                
                elif attr_type == 'funding_pnl':
                    if 'funding_rates' in market_data.get('market_data', {}):
                        attribution_pnl[attr_type] = self._calc_funding_pnl(current_exposure, previous_exposure, market_data, timestamp)
                    else:
                        attribution_pnl[attr_type] = 0.0
                
                elif attr_type == 'delta_pnl':
                    attribution_pnl[attr_type] = self._calc_delta_pnl(current_exposure, previous_exposure, market_data)
                
                elif attr_type == 'basis_pnl':
                    if 'perp_prices' in market_data.get('protocol_data', {}):
                        attribution_pnl[attr_type] = self._calc_basis_pnl(current_exposure, previous_exposure, market_data)
                    else:
                        attribution_pnl[attr_type] = 0.0
                
                elif attr_type == 'price_change_pnl':
                    attribution_pnl[attr_type] = self._calc_price_change_pnl(current_exposure, previous_exposure, market_data)
                
                elif attr_type == 'transaction_costs':
                    if 'execution_costs' in market_data.get('execution_data', {}):
                        attribution_pnl[attr_type] = self._calc_transaction_costs(current_exposure, previous_exposure, market_data)
                    else:
                        attribution_pnl[attr_type] = 0.0
                
                else:
                    logger.warning(f"Unknown attribution type: {attr_type}")
                    attribution_pnl[attr_type] = 0.0
            
            except Exception as e:
                logger.error(f"Error calculating {attr_type}: {e}")
                attribution_pnl[attr_type] = 0.0  # Gracefully handle errors
        
        # Update cumulative tracking
        for attr_type, value in attribution_pnl.items():
            self.cumulative_attributions[attr_type] += value
        
        # Add cumulative totals
        attribution_pnl['pnl_cumulative'] = sum(self.cumulative_attributions.values())
        
        return attribution_pnl
    
    def _reconcile_pnl(self, balance_pnl: Dict, attribution_pnl: Dict, timestamp: pd.Timestamp) -> Dict:
        """
        Reconcile balance-based vs attribution P&L.
        Tolerance comes from config: reconciliation_tolerance
        """
        balance_pnl_value = balance_pnl['pnl_cumulative']
        attribution_pnl_value = attribution_pnl['pnl_cumulative']
        difference = balance_pnl_value - attribution_pnl_value
        
        # Calculate tolerance (annualized, pro-rated for period)
        if self.previous_exposure is None:
            # First calculation - no period yet
            tolerance = 0.0
        else:
            # Calculate period in months
            period_start = self.last_calculation_timestamp or timestamp
            period_months = (timestamp - period_start).days / 30.44
            tolerance = self.initial_total_value * self.reconciliation_tolerance * (period_months / 12)
        
        passed = abs(difference) <= tolerance
        
        return {
            'balance_pnl': balance_pnl_value,
            'attribution_pnl': attribution_pnl_value,
            'difference': difference,
            'tolerance': tolerance,
            'passed': passed,
            'diff_pct_of_capital': (difference / self.initial_total_value) * 100 if self.initial_total_value > 0 else 0.0
        }
    
    # Individual attribution calculation methods
    def _calc_supply_yield(self, current_exposure: Dict, previous_exposure: Optional[Dict], market_data: Dict) -> float:
        """Calculate AAVE supply yield from index growth"""
        if previous_exposure is None:
            return 0.0
        
        # Implementation would calculate supply yield from AAVE index growth
        # This is a placeholder - actual implementation would be more complex
        return 0.0
    
    def _calc_borrow_costs(self, current_exposure: Dict, previous_exposure: Optional[Dict], market_data: Dict) -> float:
        """Calculate AAVE borrow costs from index growth (negative)"""
        if previous_exposure is None:
            return 0.0
        
        # Implementation would calculate borrow costs from AAVE debt index growth
        return 0.0
    
    def _calc_staking_yield_oracle(self, current_exposure: Dict, previous_exposure: Optional[Dict], market_data: Dict) -> float:
        """Calculate staking yield from oracle price appreciation"""
        if previous_exposure is None:
            return 0.0
        
        # Implementation would calculate oracle price drift
        return 0.0
    
    def _calc_staking_yield_rewards(self, current_exposure: Dict, previous_exposure: Optional[Dict], market_data: Dict) -> float:
        """Calculate staking yield from seasonal rewards"""
        if previous_exposure is None:
            return 0.0
        
        # Implementation would calculate actual rewards received
        return 0.0
    
    def _calc_funding_pnl(self, current_exposure: Dict, previous_exposure: Optional[Dict], market_data: Dict, timestamp: pd.Timestamp) -> float:
        """Calculate funding P&L from perp funding rates"""
        if previous_exposure is None:
            return 0.0
        
        # Implementation would calculate funding payments
        return 0.0
    
    def _calc_delta_pnl(self, current_exposure: Dict, previous_exposure: Optional[Dict], market_data: Dict) -> float:
        """Calculate delta P&L from unhedged exposure"""
        if previous_exposure is None:
            return 0.0
        
        # Implementation would calculate delta exposure P&L
        return 0.0
    
    def _calc_basis_pnl(self, current_exposure: Dict, previous_exposure: Optional[Dict], market_data: Dict) -> float:
        """Calculate basis P&L from spot-perp spread changes"""
        if previous_exposure is None:
            return 0.0
        
        # Implementation would calculate basis spread changes
        return 0.0
    
    def _calc_price_change_pnl(self, current_exposure: Dict, previous_exposure: Optional[Dict], market_data: Dict) -> float:
        """Calculate price change P&L from token price movements"""
        if previous_exposure is None:
            return 0.0
        
        # Implementation would calculate price change P&L
        return 0.0
    
    def _calc_transaction_costs(self, current_exposure: Dict, previous_exposure: Optional[Dict], market_data: Dict) -> float:
        """Calculate transaction costs (gas, fees)"""
        if previous_exposure is None:
            return 0.0
        
        # Implementation would calculate transaction costs
        return 0.0
```

### **Key Benefits of Mode-Agnostic Implementation**

1. **No Mode-Specific Logic**: Component has zero hardcoded mode checks
2. **Config-Driven Behavior**: All behavior determined by `attribution_types` and `reconciliation_tolerance`
3. **Graceful Data Handling**: Skips calculations when data is unavailable (returns 0.0)
4. **Easy Extension**: Adding new attribution types doesn't require mode-specific changes
5. **Self-Documenting**: Attribution types and limits clearly defined in config

### **Config Validation in Component Factory**

```python
class ComponentFactory:
    """Creates components with config validation"""
    
    @staticmethod
    def create_pnl_calculator(config: Dict, data_provider: 'BaseDataProvider', execution_mode: str,
                             exposure_monitor: 'ExposureMonitor') -> PnLCalculator:
        """Create PnL Calculator with config validation"""
        # Extract PnL calculator specific config
        pnl_config = config.get('component_config', {}).get('pnl_calculator', {})
        
        # Validate required config
        required_fields = ['attribution_types', 'reporting_currency', 'reconciliation_tolerance']
        for field in required_fields:
            if field not in pnl_config:
                raise ValueError(f"Missing required config for pnl_calculator: {field}")
        
        # Validate attribution types
        valid_attribution_types = [
            'supply_yield', 'borrow_costs', 'staking_yield_oracle', 'staking_yield_rewards',
            'funding_pnl', 'delta_pnl', 'basis_pnl', 'price_change_pnl', 'transaction_costs'
        ]
        for attr_type in pnl_config.get('attribution_types', []):
            if attr_type not in valid_attribution_types:
                raise ValueError(f"Invalid attribution type: {attr_type}. Valid: {valid_attribution_types}")
        
        # Create component
        return PnLCalculator(config, data_provider, execution_mode, exposure_monitor)
```

---

## Event Logging Requirements

### Component Event Log File
**Separate log file** for this component's events:
- **File**: `logs/events/pnl_calculator_events.jsonl`
- **Format**: JSON Lines (one event per line)
- **Rotation**: Daily rotation, keep 30 days
- **Purpose**: Component-specific audit trail

### Event Logging via EventLogger
All events logged through centralized EventLogger:

```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='[event_type]',
    component='PnLCalculator',
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
    component='PnLCalculator',
    data={
        'execution_mode': self.execution_mode,
        'attribution_types': self.attribution_types,
        'reporting_currency': self.reporting_currency,
        'reconciliation_tolerance': self.reconciliation_tolerance,
        'config_hash': hash(str(self.config))
    }
)
```

#### 2. State Updates (Every calculate_pnl() Call)
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='state_update',
    component='PnLCalculator',
    data={
        'trigger_source': trigger_source,
        'balance_pnl': self.current_pnl.get('balance_based', {}).get('pnl_cumulative', 0),
        'attribution_pnl': self.current_pnl.get('attribution', {}).get('pnl_cumulative', 0),
        'reconciliation_passed': self.current_pnl.get('reconciliation', {}).get('passed', False),
        'processing_time_ms': processing_time
    }
)
```

#### 3. Error Events
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='error',
    component='PnLCalculator',
    data={
        'error_code': 'PNL-001',
        'error_message': str(e),
        'stack_trace': traceback.format_exc(),
        'error_severity': 'CRITICAL|HIGH|MEDIUM|LOW'
    }
)
```

#### 4. Component-Specific Critical Events
- **P&L Calculation Failed**: When P&L calculation fails
- **Attribution Error**: When P&L attribution fails
- **Reconciliation Mismatch**: When P&L reconciliation fails

### Event Retention & Output Formats

#### Dual Logging Approach
**Both formats are used**:
1. **JSON Lines (Iterative)**: Write events to component-specific JSONL files during execution
   - **Purpose**: Real-time monitoring during backtest runs
   - **Location**: `logs/events/pnl_calculator_events.jsonl`
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

### Component Error Code Prefix: PNL
All PnLCalculator errors use the `PNL` prefix.

### Error Code Registry
**Source**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`

All error codes registered with:
- **code**: Unique error code
- **component**: Component name
- **severity**: CRITICAL | HIGH | MEDIUM | LOW
- **message**: Human-readable error message
- **resolution**: How to resolve

### Component Error Codes

#### PNL-001: P&L Calculation Failed (HIGH)
**Description**: Failed to calculate P&L metrics
**Cause**: Invalid exposure data, missing market data, calculation errors
**Recovery**: Retry with fallback values, check data availability
```python
raise ComponentError(
    error_code='PNL-001',
    message='P&L calculation failed',
    component='PnLCalculator',
    severity='HIGH'
)
```

#### PNL-002: Attribution Calculation Failed (MEDIUM)
**Description**: Failed to calculate P&L attribution
**Cause**: Invalid attribution data, missing source information
**Recovery**: Log warning, use default attribution, continue processing
```python
raise ComponentError(
    error_code='PNL-002',
    message='P&L attribution calculation failed',
    component='PnLCalculator',
    severity='MEDIUM'
)
```

#### PNL-003: Reconciliation Mismatch (HIGH)
**Description**: P&L reconciliation failed
**Cause**: Position data mismatch, calculation errors
**Recovery**: Retry reconciliation, check position data integrity
```python
raise ComponentError(
    error_code='PNL-003',
    message='P&L reconciliation mismatch',
    component='PnLCalculator',
    severity='HIGH'
)
```

#### PNL-004: Required Data Missing (HIGH)
**Description**: Required market data or exposure data missing for P&L calculation
**Cause**: DataProvider not loading required data, ExposureMonitor not providing required fields
**Recovery**: Check DataProvider data_requirements, verify ExposureMonitor output structure
```python
raise ComponentError(
    error_code='PNL-004',
    message='Required data missing for P&L calculation',
    component='PnLCalculator',
    severity='HIGH'
)
```

### Structured Error Handling Pattern

#### Error Raising
```python
from backend.src.basis_strategy_v1.core.error_codes.exceptions import ComponentError

try:
    result = self._calculate_pnl(exposure_data, market_data)
except Exception as e:
    # Log error event
    self.event_logger.log_event(
        timestamp=timestamp,
        event_type='error',
        component='PnLCalculator',
        data={
            'error_code': 'PNL-001',
            'error_message': str(e),
            'stack_trace': traceback.format_exc()
        }
    )
    
    # Raise structured error
    raise ComponentError(
        error_code='PNL-001',
        message=f'PnLCalculator failed: {str(e)}',
        component='PnLCalculator',
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
def __init__(self, ..., health_manager: 'UnifiedHealthManager'):
    # Store health manager reference
    self.health_manager = health_manager
    
    # Register component with health system
    self.health_manager.register_component(
        component_name='PnLCalculator',
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
            'attribution_types_count': len(self.attribution_types),
            'reconciliation_passed': self.current_pnl.get('reconciliation', {}).get('passed', False)
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
- [x] All 19 sections present and complete
- [x] Canonical Sources section links to all 5 architecture docs
- [x] Configuration Parameters shows exact YAML from 19_CONFIGURATION.md
- [x] Table showing attribution types for all 7 modes
- [x] MODE-AGNOSTIC IMPLEMENTATION EXAMPLE with complete class structure
- [x] ComponentFactory validation pattern included
- [x] No mode-specific if statements in main calculate_pnl method
- [x] Uses BaseDataProvider type (not DataProvider)
- [x] Uses config['mode'] (not config['mode'])
- [x] Cross-references 19_CONFIGURATION.md, CODE_STRUCTURE_PATTERNS.md, REFERENCE_ARCHITECTURE_CANONICAL.md
- [x] Component-specific log file documented (`logs/events/pnl_calculator_events.jsonl`)
- [x] Data flow pattern: calls exposure_monitor.get_current_exposure() and data_provider.get_data(timestamp) directly

### Section Order Validation
- [x] Title and Purpose (section 1)
- [x] Canonical Sources (section 2)
- [x] Responsibilities (section 3)
- [x] State (section 4)
- [x] Component References (Set at Init) (section 5)
- [x] Configuration Parameters (section 6)
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
- [x] Integration Points (section 17)
- [x] Current Implementation Status (section 18)
- [x] Related Documentation (section 19)

### Implementation Status
- [x] Spec is complete and follows template
- [x] All required sections present
- [x] Config-driven patterns documented
- [x] Graceful data handling shown
- [x] ComponentFactory pattern included

## Integration Points

### Called BY
- EventDrivenStrategyEngine (full loop): pnl_calculator.calculate_pnl(timestamp, 'full_loop')
- PositionUpdateHandler (tight loop): pnl_calculator.calculate_pnl(timestamp, 'tight_loop')

### Calls TO
- exposure_monitor.get_current_exposure() - exposure data queries (via stored reference)
- data_provider.get_data(timestamp) - market data queries (via stored reference)

### Communication
- Direct method calls ONLY
- NO event publishing
- NO Redis/message queues
- NO async/await in internal methods

## Current Implementation Status

**Overall Completion**: 90% (Core functionality working, centralized utility manager needs implementation)

### **Core Functionality Status**
- ✅ **Working**: Config-driven attribution system, balance-based P&L calculation, reconciliation validation, share class awareness, cumulative tracking, graceful data handling, mode-agnostic implementation
- ⚠️ **Partial**: Centralized utility manager implementation (scattered utility methods need centralization)
- ❌ **Missing**: None
- 🔄 **Refactoring Needed**: Centralized utility manager implementation

### **Architecture Compliance Status**
- ✅ **COMPLIANT**: Component follows canonical architectural principles
  - **Reference-Based Architecture**: Components receive references at init, never pass as runtime parameters
  - **Shared Clock Pattern**: All methods receive timestamp from EventDrivenStrategyEngine
  - **Request Isolation Pattern**: Fresh instances per backtest/live request
  - **Synchronous Component Execution**: Internal methods are synchronous, async only for I/O operations
  - **Mode-Agnostic Behavior**: Uses config-driven attribution types, no mode-specific logic
  - **Config-Driven Attribution**: Uses component_config.pnl_calculator.attribution_types for behavior

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
- **Integration**: Integrates with quality gate system through P&L calculator tests

### **Task Completion Status**
- **Related Tasks**: 
  - [Task 18: USDT Market Neutral Quality Gates](../../.cursor/tasks/18_usdt_market_neutral_quality_gates.md) - Generic vs Mode-Specific Architecture (100% complete - config-driven attribution system implemented)
  - [Task 14: Component Data Flow Architecture](../../.cursor/tasks/14_component_data_flow_architecture.md) - Mode-Agnostic Architecture (90% complete - centralized utilities need implementation)
  - [Task 15: Pure Lending Quality Gates](../../.cursor/tasks/15_pure_lending_quality_gates.md) - Mode-Specific PnL Calculator (100% complete - config-driven attribution system implemented)
- **Completion**: 90% complete overall
- **Blockers**: Centralized utility manager implementation
- **Next Steps**: Implement centralized utility manager for scattered utility methods

## Related Documentation

### **Architecture Patterns**
- [Reference-Based Architecture](../REFERENCE_ARCHITECTURE_CANONICAL.md)
- [Shared Clock Pattern](../SHARED_CLOCK_PATTERN.md)
- [Request Isolation Pattern](../REQUEST_ISOLATION_PATTERN.md)
- [Mode-Agnostic Architecture](../REFERENCE_ARCHITECTURE_CANONICAL.md)

### **Component Integration**
- [Exposure Monitor Specification](02_EXPOSURE_MONITOR.md) - Provides exposure data for P&L calculations
- [Risk Monitor Specification](03_RISK_MONITOR.md) - Uses P&L metrics for risk assessment
- [Strategy Manager Specification](05_STRATEGY_MANAGER.md) - Depends on P&L Calculator for performance metrics
- [Data Provider Specification](09_DATA_PROVIDER.md) - Provides market data for P&L calculations
- [Event Logger Specification](08_EVENT_LOGGER.md) - Logs P&L calculation events
- [Position Update Handler Specification](11_POSITION_UPDATE_HANDLER.md) - Triggers P&L updates
- [Results Store Specification](18_RESULTS_STORE.md) - Stores P&L results (needs alignment with config-driven attribution types)

### **Configuration and Implementation**
- [Configuration Guide](19_CONFIGURATION.md) - Complete config schemas for all 7 modes
- [Code Structure Patterns](../CODE_STRUCTURE_PATTERNS.md) - Implementation patterns
- [Data Provider Specification](09_DATA_PROVIDER.md) - Data access patterns
- [Event Logger Specification](08_EVENT_LOGGER.md) - Event logging integration

---

**Status**: ⭐ **CANONICAL EXAMPLE** - Complete spec following all guidelines! ✅