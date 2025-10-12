# Strategy Manager Component Specification

**Last Reviewed**: October 10, 2025

## Purpose
Mode-specific strategy brain that decides 5 standardized actions and breaks them down into sequential instruction blocks for Execution Manager.

## Mode-Specific Architecture

This component is **naturally mode-specific** because position calculation logic differs fundamentally across strategies:
- Inherits from BaseStrategyManager
- Each mode has specific subclass (PureLendingStrategyManager, BTCBasisStrategyManager, etc.)
- Factory pattern for creation (StrategyManagerFactory)
- Config still drives parameters (hedge_allocation, rebalancing_triggers, etc.)

See: 5A_STRATEGY_FACTORY.md for factory pattern, CODE_STRUCTURE_PATTERNS.md section 5, ADR-052

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Core principles including config-driven architecture
- **Strategy Specifications**: [MODES.md](../MODES.md) - Strategy mode definitions
- **Configuration Guide**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas
- **Implementation Patterns**: [CODE_STRUCTURE_PATTERNS.md](../CODE_STRUCTURE_PATTERNS.md) - Complete implementation patterns
- **Component Index**: [COMPONENT_SPECS_INDEX.md](../COMPONENT_SPECS_INDEX.md) - All 20 components (11 core + 9 supporting)

## Responsibilities
1. Decide 5 standardized actions (entry_full, entry_partial, exit_full, exit_partial, sell_dust)
2. Break down actions into sequential instruction blocks for Execution Manager
3. NO execution logic: Just instruction block creation
4. Mode-specific decision logic based on exposure, risk, and market data

## Mode-Specific but Config-Driven Architecture

**Important**: The Strategy Manager is **naturally mode-specific** by design, but uses **config-driven behavior** to determine its specific logic:

**Component Configuration** (from `component_config.strategy_manager`):
```yaml
component_config:
  strategy_manager:
    strategy_type: "pure_lending"  # or "btc_basis", "eth_leveraged", etc.
    actions: ["entry_full", "exit_full"]  # Available actions for this mode
    rebalancing_triggers: ["deposit", "withdrawal"]  # What triggers rebalancing
    position_calculation:
      target_position: "aave_usdt_supply"  # Mode-specific position calculation
      max_position: "equity"
```

**Config-Driven Strategy Behavior**:
- Uses `strategy_type` to determine which mode-specific logic to execute
- Uses `actions` to determine which standardized actions are available
- Uses `rebalancing_triggers` to determine when to rebalance
- Uses `position_calculation` to determine how to calculate target positions
- **Still mode-specific**: Each strategy type has different position calculation logic
- **But config-driven**: Behavior is determined by config parameters, not hardcoded mode checks

**Inheritance-Based Architecture**:
- BaseStrategyManager provides abstract base class with standardized wrapper actions
- Mode-specific subclasses implement abstract methods for strategy logic
- Config-driven parameters work together with inheritance-based logic
- Both patterns complement each other for complete strategy management

**Config-Driven + Inheritance Pattern Integration**:

| Aspect | Config-Driven | Inheritance-Based | How They Work Together |
|--------|---------------|-------------------|----------------------|
| **Strategy Type** | `strategy_type` parameter | Concrete subclass selection | Config determines which subclass to instantiate |
| **Available Actions** | `actions` list from config | Abstract method implementations | Config defines what actions are available, inheritance provides implementation |
| **Rebalancing Triggers** | `rebalancing_triggers` from config | Mode-specific trigger logic | Config defines triggers, inheritance provides mode-specific handling |
| **Position Calculation** | `position_calculation` config | Abstract `calculate_target_position()` | Config provides parameters, inheritance provides mode-specific calculation logic |
| **Validation** | Config validation rules | Abstract `validate_action()` | Config defines validation rules, inheritance provides mode-specific validation |

**Example Configurations by Mode**:

**Pure Lending Mode**:
```yaml
strategy_manager:
  strategy_type: "pure_lending"
  actions: ["entry_full", "exit_full"]
  rebalancing_triggers: ["deposit", "withdrawal"]
  position_calculation:
    target_position: "aave_usdt_supply"
    max_position: "equity"
```

**BTC Basis Mode**:
```yaml
strategy_manager:
  strategy_type: "btc_basis"
  actions: ["entry_full", "entry_partial", "exit_partial", "exit_full"]
  rebalancing_triggers: ["deposit", "withdrawal", "delta_drift"]
  position_calculation:
    target_position: "btc_spot_long"
    hedge_position: "btc_perp_short"
    hedge_allocation: {"binance": 0.4, "bybit": 0.3, "okx": 0.3}
```

**ETH Leveraged Mode**:
```yaml
strategy_manager:
  strategy_type: "eth_leveraged"
  actions: ["entry_full", "entry_partial", "exit_partial", "exit_full", "sell_dust"]
  rebalancing_triggers: ["deposit", "withdrawal", "ltv_drift"]
  position_calculation:
    target_position: "leveraged_eth_staking"
    leverage_ratio: 0.9
    lst_type: "weeth"
```

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
- data_provider: BaseDataProvider (reference, query with timestamps)
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
- `mode`: str - e.g., 'eth_basis', 'pure_lending'
- `share_class`: str - 'usdt_stable' | 'eth_directional'
- `initial_capital`: float - Starting capital

### Component-Specific Config
- `strategy_type`: str - Strategy mode type (from component_config)
  - **Usage**: Determines which mode-specific strategy logic to execute
  - **Values**: 'pure_lending', 'btc_basis', 'eth_leveraged', etc.
  - **Validation**: Must match available strategy types

- `actions`: List[str] - Available strategy actions (from component_config)
  - **Usage**: Determines which standardized actions are available
  - **Values**: ['entry_full', 'exit_full', 'entry_partial', 'exit_partial']
  - **Validation**: Must be valid action types

- `rebalancing_triggers`: List[str] - Rebalancing trigger conditions (from component_config)
  - **Usage**: Determines when to trigger rebalancing actions
  - **Values**: ['deposit', 'withdrawal', 'funding_rate_change', 'liquidation_risk']
  - **Validation**: Must be valid trigger types

- `position_calculation`: Dict - Position calculation configuration (from component_config)
  - **Usage**: Determines how to calculate target positions
  - **Fields**: target_position, max_position, calculation_method
  - **Validation**: Must have required calculation fields

### Strategy-Specific Config Fields
- `lst_type`: str - Liquid staking token type
  - **Usage**: Used in strategy initialization to set default LST type for staking operations
  - **Required**: Yes
  - **Used in**: `usdt_market_neutral_strategy.py:52`, `eth_leveraged_strategy.py:51`, etc.

- `staking_protocol`: str - Staking protocol selection
  - **Usage**: Used in strategy initialization to set default staking protocol
  - **Required**: Yes
  - **Used in**: `usdt_market_neutral_strategy.py:54`, `eth_leveraged_strategy.py:52`, etc.

- `lending_protocol`: str - Lending protocol selection
  - **Usage**: Used in strategy initialization to set default lending protocol
  - **Required**: Yes
  - **Used in**: `usdt_market_neutral_strategy.py:53`, `usdt_market_neutral_no_leverage_strategy.py:52`

- `eth_allocation`: float - ETH allocation percentage
  - **Usage**: Used in strategy initialization to set ETH allocation percentage
  - **Required**: Yes
  - **Used in**: `usdt_market_neutral_strategy.py:50`, `eth_leveraged_strategy.py:49`, etc.

- `btc_allocation`: float - BTC allocation percentage
  - **Usage**: Used in strategy initialization to set BTC allocation percentage
  - **Required**: Yes
  - **Used in**: `btc_basis_strategy.py:49`

- `usdt_allocation`: float - USDT allocation percentage
  - **Usage**: Used in strategy initialization to set USDT allocation percentage
  - **Required**: Yes
  - **Used in**: `usdt_market_neutral_strategy.py:49`, `usdt_market_neutral_no_leverage_strategy.py:49`

- `funding_threshold`: float - Minimum funding rate threshold for basis trades
  - **Usage**: Used in basis strategy initialization to set funding rate threshold
  - **Required**: Yes
  - **Used in**: `eth_basis_strategy.py:50`, `btc_basis_strategy.py:50`

- `max_leverage`: float - Maximum leverage allowed
  - **Usage**: Used in strategy initialization to set maximum leverage limit
  - **Required**: Yes
  - **Used in**: `eth_basis_strategy.py:51`, `btc_basis_strategy.py:51`

- `hedge_allocation`: float - Hedge allocation percentage
  - **Usage**: Used in leveraged strategy initialization to set hedge allocation
  - **Required**: Yes
  - **Used in**: `eth_leveraged_strategy.py:53`

- `leverage_multiplier`: float - Leverage multiplier factor
  - **Usage**: Used in strategy initialization to set leverage multiplier
  - **Required**: Yes
  - **Used in**: `usdt_market_neutral_strategy.py:51`, `eth_leveraged_strategy.py:50`

### Config Access Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    # Read config fields (NEVER modify) - Config-driven approach
    strategy_type = self.config['component_config']['strategy_manager']['strategy_type']
    actions = self.config['component_config']['strategy_manager']['actions']
    triggers = self.config['component_config']['strategy_manager']['rebalancing_triggers']
    position_calc = self.config['component_config']['strategy_manager']['position_calculation']
    
    # Use config-driven strategy logic
    if self._should_rebalance(triggers, trigger_source):
        target_position = self._calculate_target_position(position_calc)
        self._execute_strategy_action(actions, target_position)
```

## Data Flow Pattern

### Input Parameters
- `exposure_data`: Exposure data from exposure monitor
- `risk_metrics`: Risk metrics from risk monitor
- `market_data`: Market data from data provider
- `timestamp`: Current timestamp for data consistency

### Output Data
- `execution_instructions`: Strategy execution instructions
- `strategy_decisions`: Strategy decision data

### Data Flow
```
Exposure Monitor → exposure_data → Strategy Manager → execution_instructions → Execution Manager
Risk Monitor → risk_metrics → Strategy Manager → execution_instructions → Execution Manager
Data Provider → market_data → Strategy Manager → execution_instructions → Execution Manager
```

### Behavior NOT Determinable from Config
- Strategy decision algorithms (inheritance-based logic)
- Action selection rules (config-driven thresholds)
- Instruction block templates (config-driven structures)

## Data Provider Queries

### Data Types Requested
`data = self.data_provider.get_data(timestamp)`

#### Market Data
- `prices`: Dict[str, float] - Token prices in USD
  - **Tokens needed**: ETH, USDT, BTC, LST tokens
  - **Update frequency**: 1min
  - **Usage**: Strategy decision making and market analysis

#### ML Data (ML Strategy Manager Only)
- **`get_ml_prediction`**: Get ML prediction for specific asset
  - **Usage**: Used by MLDirectionalStrategyManager for trading signals
  - **Parameters**: timestamp (pd.Timestamp), asset (str)
  - **Returns**: Dict - ML prediction with signal and confidence
  - **Implementation**: Calls data provider's get_ml_prediction method

### Query Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    data = self.data_provider.get_data(timestamp)
    prices = data['market_data']['prices']
```

### Data NOT Available from DataProvider
None - all data comes from DataProvider

## Configuration Parameters

### **Config-Driven Architecture**

The Strategy Manager is **mode-specific** and uses `component_config.strategy_manager` from the mode configuration:

```yaml
component_config:
  strategy_manager:
    strategy_type: "pure_lending"  # Strategy mode type
    actions: ["entry_full", "exit_full"]  # Available strategy actions
    rebalancing_triggers: ["deposit", "withdrawal"]  # Rebalancing trigger conditions
    position_calculation:
      target_position: "aave_usdt_supply"  # Mode-specific position calculation
      max_position: "equity"
      hedge_allocation:  # For basis strategies
        binance: 0.4
        bybit: 0.3
        okx: 0.3
```

### **Strategy Manager Configuration by Mode**

| Mode | Strategy Type | Actions | Rebalancing Triggers | Position Calculation |
|------|---------------|---------|---------------------|---------------------|
| **Pure Lending** | `pure_lending` | `["entry_full", "exit_full"]` | `["deposit", "withdrawal"]` | AAVE USDT supply only |
| **BTC Basis** | `btc_basis` | `["entry_full", "entry_partial", "exit_partial", "exit_full"]` | `["deposit", "withdrawal", "delta_drift"]` | BTC spot + perp hedge |
| **ETH Basis** | `eth_basis` | `["entry_full", "entry_partial", "exit_partial", "exit_full"]` | `["deposit", "withdrawal", "delta_drift"]` | ETH spot + perp hedge |
| **ETH Staking Only** | `eth_staking_only` | `["entry_full", "exit_full"]` | `["deposit", "withdrawal"]` | ETH staking only |
| **ETH Leveraged** | `eth_leveraged` | `["entry_full", "entry_partial", "exit_partial", "exit_full", "sell_dust"]` | `["deposit", "withdrawal", "ltv_drift"]` | Leveraged ETH staking |
| **USDT MN No Leverage** | `usdt_market_neutral_no_leverage` | `["entry_full", "entry_partial", "exit_partial", "exit_full"]` | `["deposit", "withdrawal", "delta_drift"]` | Market-neutral without leverage |
| **USDT Market Neutral** | `usdt_market_neutral` | `["entry_full", "entry_partial", "exit_partial", "exit_full", "sell_dust"]` | `["deposit", "withdrawal", "delta_drift", "margin_critical"]` | Full market-neutral with leverage |

**Key Insight**: The Strategy Manager uses **config-driven parameters** to determine available actions and triggers, while **inheritance-based logic** provides mode-specific position calculation and validation.

### **Environment Variables**
- **BASIS_EXECUTION_MODE**: Controls execution behavior ('backtest' | 'live')
- **BASIS_ENVIRONMENT**: Controls credential routing ('dev' | 'staging' | 'production')
- **BASIS_DATA_MODE**: Controls data source ('csv' | 'db')

**Cross-Reference**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete configuration hierarchy
**Cross-Reference**: [ENVIRONMENT_VARIABLES.md](../ENVIRONMENT_VARIABLES.md) - Environment variable definitions

## **MODE-AGNOSTIC IMPLEMENTATION EXAMPLE**

### **Complete Config-Driven + Inheritance Strategy Manager**

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd

class BaseStrategyManager(ABC):
    """Abstract base class for all strategy managers with config-driven behavior"""
    
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str,
                 exposure_monitor: ExposureMonitor, risk_monitor: RiskMonitor):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        self.exposure_monitor = exposure_monitor
        self.risk_monitor = risk_monitor
        
        # Extract config-driven strategy settings
        self.strategy_config = config.get('component_config', {}).get('strategy_manager', {})
        self.strategy_type = self.strategy_config.get('strategy_type')
        self.available_actions = self.strategy_config.get('actions', [])
        self.rebalancing_triggers = self.strategy_config.get('rebalancing_triggers', [])
        self.position_calculation = self.strategy_config.get('position_calculation', {})
        
        # Initialize component-specific state
        self.current_action = None
        self.last_decision_timestamp = None
        self.action_history = []
        self.instruction_blocks_generated = 0
        
        # Validate config
        self._validate_strategy_config()
    
    def _validate_strategy_config(self):
        """Validate strategy manager configuration"""
        if not self.strategy_type:
            raise ValueError("strategy_manager.strategy_type cannot be empty")
        
        if not self.available_actions:
            raise ValueError("strategy_manager.actions cannot be empty")
        
        if not self.rebalancing_triggers:
            raise ValueError("strategy_manager.rebalancing_triggers cannot be empty")
        
        valid_actions = ['entry_full', 'entry_partial', 'exit_full', 'exit_partial', 'sell_dust']
        for action in self.available_actions:
            if action not in valid_actions:
                raise ValueError(f"Invalid action: {action}")
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs) -> List[Dict]:
        """
        Main entry point for strategy decision making.
        Uses both config-driven parameters and inheritance-based logic.
        """
        # Log component start (per EVENT_LOGGER.md)
        start_time = pd.Timestamp.now()
        logger.debug(f"StrategyManager.update_state started at {start_time}")
        
        # Query data using shared clock
        data = self.data_provider.get_data(timestamp)
        
        # Access other components via references
        current_exposure = self.exposure_monitor.get_current_exposure()
        risk_metrics = self.risk_monitor.get_current_risk_metrics()
        
        # Decide action using config-driven triggers and inheritance-based logic
        action = self.decide_action(timestamp, current_exposure, risk_metrics, data)
        
        # Break down action into instruction blocks
        instruction_blocks = self.break_down_action(action, kwargs, data)
        
        # Update state
        self.current_action = action
        self.last_decision_timestamp = timestamp
        self.action_history.append({
            'timestamp': timestamp,
            'action': action,
            'trigger_source': trigger_source,
            'instruction_blocks_count': len(instruction_blocks)
        })
        self.instruction_blocks_generated += len(instruction_blocks)
        
        # Log component end (per EVENT_LOGGER.md)
        end_time = pd.Timestamp.now()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000
        logger.debug(f"StrategyManager.update_state completed at {end_time}, took {processing_time_ms:.2f}ms")
        
        # Log state update event
        self.event_logger.log_event(
            timestamp=timestamp,
            event_type='state_update_completed',
            component='StrategyManager',
            data={
                'trigger_source': trigger_source,
                'action': action,
                'instruction_blocks_count': len(instruction_blocks),
                'processing_time_ms': processing_time_ms,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
        )
        
        return instruction_blocks
    
    def decide_action(self, timestamp: pd.Timestamp, current_exposure: Dict, 
                     risk_metrics: Dict, market_data: Dict) -> str:
        """
        Decide which of the configured actions to take.
        Uses config-driven triggers and inheritance-based logic.
        """
        # Check if rebalancing is needed using config-driven triggers
        rebalancing_condition = self.get_rebalancing_condition(timestamp)
        
        if rebalancing_condition:
            # Use inheritance-based logic to determine specific action
            return self._determine_rebalancing_action(
                rebalancing_condition, current_exposure, risk_metrics, market_data
            )
        
        # Check for new deposits/withdrawals
        if 'deposit_amount' in kwargs and kwargs['deposit_amount'] > 0:
            return 'entry_full' if 'entry_full' in self.available_actions else 'entry_partial'
        
        if 'withdrawal_amount' in kwargs and kwargs['withdrawal_amount'] > 0:
            return 'exit_full' if 'exit_full' in self.available_actions else 'exit_partial'
        
        # No action needed
        return None
    
    def break_down_action(self, action: str, params: Dict, market_data: Dict) -> List[Dict]:
        """
        Break down action into sequential instruction blocks.
        Uses config-driven position calculation and inheritance-based logic.
        """
        if not action:
            return []
        
        # Calculate target positions using inheritance-based logic
        target_positions = self.calculate_target_position(
            self.last_decision_timestamp, 'action_breakdown'
        )
        
        # Generate instruction blocks based on action type
        if action == 'entry_full':
            return self._generate_entry_full_instructions(target_positions, params, market_data)
        elif action == 'entry_partial':
            return self._generate_entry_partial_instructions(target_positions, params, market_data)
        elif action == 'exit_full':
            return self._generate_exit_full_instructions(target_positions, params, market_data)
        elif action == 'exit_partial':
            return self._generate_exit_partial_instructions(target_positions, params, market_data)
        elif action == 'sell_dust':
            return self._generate_sell_dust_instructions(target_positions, params, market_data)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    @abstractmethod
    def calculate_target_position(self, timestamp: pd.Timestamp, trigger_source: str) -> Dict[str, Any]:
        """
        Calculate target position for this strategy mode.
        MUST be implemented by each strategy-specific subclass.
        """
        pass
    
    @abstractmethod
    def validate_action(self, action: str, timestamp: pd.Timestamp) -> bool:
        """
        Validate strategy action for this mode.
        MUST be implemented by each strategy-specific subclass.
        """
        pass
    
    @abstractmethod
    def get_rebalancing_condition(self, timestamp: pd.Timestamp) -> Optional[str]:
        """
        Get rebalancing condition for this strategy mode.
        MUST be implemented by each strategy-specific subclass.
        """
        pass
    
    def _determine_rebalancing_action(self, condition: str, current_exposure: Dict, 
                                    risk_metrics: Dict, market_data: Dict) -> str:
        """Determine specific rebalancing action based on condition"""
        # This can be overridden by subclasses for mode-specific logic
        if condition == 'margin_critical':
            return 'exit_partial' if 'exit_partial' in self.available_actions else 'exit_full'
        elif condition == 'delta_drift':
            return 'entry_partial' if 'entry_partial' in self.available_actions else 'entry_full'
        elif condition == 'ltv_high':
            return 'exit_partial' if 'exit_partial' in self.available_actions else 'exit_full'
        else:
            return 'entry_partial' if 'entry_partial' in self.available_actions else None
```

### **Concrete Strategy Implementations**

#### **PureLendingStrategy (Simplest)**
```python
class PureLendingStrategy(BaseStrategyManager):
    """Strategy manager for pure lending mode - simplest implementation"""
    
    def calculate_target_position(self, timestamp: pd.Timestamp, trigger_source: str) -> Dict[str, Any]:
        """Pure lending position calculation - all capital in AAVE USDT"""
        current_exposure = self.exposure_monitor.get_current_exposure()
        equity = current_exposure.get('total_exposure', 0.0)
        
        return {
            'aave_usdt_supply': equity,
            'wallet_usdt': 0.0,
            'target_delta_eth': 0.0,
            'target_perp_positions': {}
        }
    
    def validate_action(self, action: str, timestamp: pd.Timestamp) -> bool:
        """Validate pure lending strategy actions"""
        # Pure lending only supports entry_full and exit_full
        valid_actions = ['entry_full', 'exit_full']
        return action in valid_actions
    
    def get_rebalancing_condition(self, timestamp: pd.Timestamp) -> Optional[str]:
        """Pure lending rarely needs rebalancing"""
        # Only rebalance on deposits/withdrawals, not market conditions
        return None
```

#### **BTCBasisStrategy (Medium Complexity)**
```python
class BTCBasisStrategy(BaseStrategyManager):
    """Strategy manager for BTC basis mode - medium complexity"""
    
    def calculate_target_position(self, timestamp: pd.Timestamp, trigger_source: str) -> Dict[str, Any]:
        """BTC basis position calculation - long spot, short perp"""
        current_exposure = self.exposure_monitor.get_current_exposure()
        equity = current_exposure.get('total_exposure', 0.0)
        
        # Get BTC price from market data
        data = self.data_provider.get_data(timestamp)
        btc_price = data['market_data']['prices'].get('BTC', 0.0)
        
        if btc_price == 0:
            return {}  # Graceful handling of missing data
        
        # Calculate target BTC spot position (50% of equity)
        target_btc_spot = (equity * 0.5) / btc_price
        
        # Calculate target perp short positions across venues
        hedge_allocation = self.position_calculation.get('hedge_allocation', {})
        target_perp_shorts = {}
        for venue, allocation in hedge_allocation.items():
            target_perp_shorts[venue] = -target_btc_spot * allocation
        
        return {
            'btc_spot_long': target_btc_spot,
            'btc_perp_shorts': target_perp_shorts,
            'target_delta_btc': 0.0,  # Market-neutral
            'btc_price': btc_price
        }
    
    def validate_action(self, action: str, timestamp: pd.Timestamp) -> bool:
        """Validate BTC basis strategy actions"""
        # BTC basis supports all actions
        return action in self.available_actions
    
    def get_rebalancing_condition(self, timestamp: pd.Timestamp) -> Optional[str]:
        """Check for BTC basis rebalancing conditions"""
        current_exposure = self.exposure_monitor.get_current_exposure()
        risk_metrics = self.risk_monitor.get_current_risk_metrics()
        
        # Check delta drift
        net_delta = current_exposure.get('net_delta', 0.0)
        total_exposure = current_exposure.get('total_exposure', 1.0)
        delta_ratio = abs(net_delta) / total_exposure
        
        if delta_ratio > 0.05:  # 5% delta drift
            return 'delta_drift'
        
        # Check margin ratio
        if risk_metrics.get('cex_margin_ratio', {}).get('min_ratio', 1.0) < 0.2:
            return 'margin_critical'
        
        return None
```

#### **USDTMarketNeutralStrategy (Most Complex)**
```python
class USDTMarketNeutralStrategy(BaseStrategyManager):
    """Strategy manager for USDT market-neutral mode - most complex"""
    
    def calculate_target_position(self, timestamp: pd.Timestamp, trigger_source: str) -> Dict[str, Any]:
        """USDT market-neutral position calculation - complex multi-venue strategy"""
        current_exposure = self.exposure_monitor.get_current_exposure()
        equity = current_exposure.get('total_exposure', 0.0)
        
        # Get market data
        data = self.data_provider.get_data(timestamp)
        eth_price = data['market_data']['prices'].get('ETH', 0.0)
        
        if eth_price == 0:
            return {}  # Graceful handling of missing data
        
        # Calculate target AAVE position (50% of equity)
        target_aave_eth = (equity * 0.5) / eth_price
        
        # Calculate target perp short positions to hedge AAVE
        hedge_allocation = self.position_calculation.get('hedge_allocation', {})
        target_perp_shorts = {}
        for venue, allocation in hedge_allocation.items():
            target_perp_shorts[venue] = -target_aave_eth * allocation
        
        return {
            'aave_eth_supply': target_aave_eth,
            'aave_ltv': 0.91,  # Target LTV
            'target_perp_shorts': target_perp_shorts,
            'target_delta_eth': 0.0,  # Market-neutral
            'target_margin_ratio': 1.0,  # Full capital utilization
            'eth_price': eth_price
        }
    
    def validate_action(self, action: str, timestamp: pd.Timestamp) -> bool:
        """Validate USDT market-neutral strategy actions"""
        # Market-neutral supports all actions
        return action in self.available_actions
    
    def get_rebalancing_condition(self, timestamp: pd.Timestamp) -> Optional[str]:
        """Check for market-neutral rebalancing conditions"""
        current_exposure = self.exposure_monitor.get_current_exposure()
        risk_metrics = self.risk_monitor.get_current_risk_metrics()
        
        # Check margin ratio (highest priority)
        min_margin_ratio = risk_metrics.get('cex_margin_ratio', {}).get('min_ratio', 1.0)
        if min_margin_ratio < 0.2:
            return 'margin_critical'
        elif min_margin_ratio < 0.3:
            return 'margin_warning'
        
        # Check delta drift
        net_delta = current_exposure.get('net_delta', 0.0)
        total_exposure = current_exposure.get('total_exposure', 1.0)
        delta_ratio = abs(net_delta) / total_exposure
        
        if delta_ratio > 0.05:  # 5% delta drift
            return 'delta_drift'
        
        # Check AAVE LTV
        aave_ltv = risk_metrics.get('aave_ltv', 0.0)
        if aave_ltv > 0.9:
            return 'ltv_high'
        
        return None
```

### **Key Benefits of Config-Driven + Inheritance Implementation**

1. **Config-Driven Parameters**: All behavior determined by `component_config.strategy_manager`
2. **Inheritance-Based Logic**: Mode-specific logic implemented through abstract methods
3. **Graceful Data Handling**: Skips calculations when data is unavailable
4. **Standardized Interface**: All strategies implement the same abstract methods
5. **Easy Extension**: Adding new strategy modes requires new subclass + config
6. **Self-Documenting**: Config parameters clearly define strategy behavior

### **Config Requirements**

**Status**: ✅ Complete

The following config fields are required in `component_config.strategy_manager`:

| Field | Type | Description | Required For |
|-------|------|-------------|--------------|
| `strategy_type` | str | Strategy mode type | All modes |
| `actions` | List[str] | Available strategy actions | All modes |
| `rebalancing_triggers` | List[str] | Rebalancing trigger conditions | All modes |
| `position_calculation` | Dict | Position calculation configuration | All modes |
| `hedge_allocation` | Dict | Hedge venue allocation (nested in position_calculation) | Basis strategies |

**Implementation**: These fields are documented in the YAML examples above and should be added to mode YAML files in `configs/modes/*.yaml`

## 📦 **Component Structure**

### **Core Classes**

#### **BaseStrategyManager** (Abstract Base Class)
Abstract base class for all strategy managers providing inheritance-based architecture.

#### **StrategyFactory**
Factory for creating strategy instances based on mode with proper dependency injection.

```python
class StrategyFactory:
    STRATEGY_MAP = {
        'pure_lending': PureLendingStrategy,
        'btc_basis': BTCBasisStrategy,
        'eth_leveraged': ETHLeveragedStrategy,
        # ... etc
    }
    
    @classmethod
    def create_strategy(cls, mode: str, config: Dict, dependencies: Dict) -> BaseStrategyManager:
        """Create strategy instance based on mode with dependency injection."""
        strategy_class = cls.STRATEGY_MAP.get(mode)
        if not strategy_class:
            raise ValueError(f"Unsupported strategy mode: {mode}")
        
        return strategy_class(config, dependencies)
```

#### **Concrete Strategy Implementations**
Mode-specific strategy implementations extending BaseStrategyManager.

```python
class PureLendingStrategy(BaseStrategyManager):
    def calculate_target_position(self, timestamp: pd.Timestamp, trigger_source: str) -> Dict[str, Any]:
        """Pure lending strategy position calculation."""
        # Mode-specific logic for AAVE USDT supply
        pass
    
    def validate_action(self, action: StrategyAction, timestamp: pd.Timestamp) -> bool:
        """Validate pure lending strategy actions."""
        # Mode-specific validation logic
        pass
    
    def get_rebalancing_condition(self, timestamp: pd.Timestamp) -> Optional[str]:
        """Get pure lending rebalancing conditions."""
        # Mode-specific rebalancing logic
        pass
```
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
        'mode': self.config.get('mode'),
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

#### 5. Event Patterns
- **`event`**: Logs when strategy is created
  - **Usage**: Logged during strategy factory creation
  - **Data**: strategy_type, mode, config_hash, creation_time
- **`event`**: Logs when strategy creation fails
  - **Usage**: Logged when strategy creation encounters errors
  - **Data**: error_message, strategy_type, mode, error_details
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

### ML Directional Mode (BTC/USDT)
```python
def decide_action(self, timestamp, current_exposure, risk_metrics, market_data):
    # Get ML prediction for current timestamp
    ml_prediction = self.data_provider.get_ml_prediction(timestamp, self.asset)
    
    if not ml_prediction or ml_prediction['confidence'] < self.signal_threshold:
        return 'sell_dust'  # No valid signal
    
    signal = ml_prediction['signal']
    confidence = ml_prediction['confidence']
    
    if signal == 'long':
        if current_exposure['perp_position'] <= 0:  # No long position
            return 'entry_full'  # Enter long position
        else:
            return 'sell_dust'  # Already long, hold
    elif signal == 'short':
        if current_exposure['perp_position'] >= 0:  # No short position
            return 'entry_full'  # Enter short position
        else:
            return 'sell_dust'  # Already short, hold
    elif signal == 'neutral':
        if current_exposure['perp_position'] != 0:  # Has position
            return 'exit_full'  # Close position
        else:
            return 'sell_dust'  # Already neutral
    else:  # 'hold'
        return 'sell_dust'  # Hold current position
```

**ML-Specific Configuration**:
```yaml
ml_config:
  signal_threshold: 0.65  # Minimum confidence to trade
  max_position_size: 1.0  # 100% of equity per signal
  candle_interval: "5min"  # 5-minute intervals
```

**Data Requirements**:
- `ml_ohlcv_5min`: 5-minute OHLCV bars
- `ml_predictions`: ML signals (long/short/neutral + TP/SL)
- Asset prices for PnL calculation

**Execution Actions**:
- `open_perp_long`: Open long perp position with TP/SL
- `open_perp_short`: Open short perp position with TP/SL
- `close_perp`: Close existing perp position
- `update_stop_loss`: Update stop-loss order
- `update_take_profit`: Update take-profit order

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
        mode = self.config['mode']
        
        if mode == 'pure_lending':
            return self._desired_pure_lending(change_type, params, market_data)
        
        elif mode == 'btc_basis':
            return self._desired_btc_basis(change_type, params, current_exposure, market_data)
        
        elif mode == 'eth_leveraged':
            return self._desired_eth_leveraged(change_type, params, current_exposure, market_data)
        
        elif mode == 'usdt_market_neutral':
            return self._desired_usdt_market_neutral(change_type, params, current_exposure, market_data)
        
        else:
            raise ValueError(f"Unknown strategy mode: {mode}")
    
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
| **Error Handling** | Config-driven validation | Config-driven retry with fallbacks |

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
| **Error Handling** | Config-driven validation | Config-driven retry + fallback |
| **Logging** | File-based | Real-time monitoring |
| **Monitoring** | Basic metrics | Full observability stack |

---

## 🔗 **Integration**

### **Triggered By**:
- Event-Driven Strategy Engine (orchestrated calls)
- User actions (deposit, withdrawal) - via engine
- Scheduled checks (hourly) - via engine

### **Uses Data From**:
- **Exposure Monitor** ← Current exposure (via stored reference)
- **Risk Monitor** ← Risk metrics (via stored reference)
- **Config** ← Targets, thresholds, mode

### **Issues Instructions To**:
- **Execution Manager** ← Instruction blocks (returned to engine)

### **Component Communication**:

**Orchestrated by Event-Driven Strategy Engine**:
- Strategy Manager queries data via stored references (exposure_monitor, risk_monitor)
- Strategy Manager returns instruction blocks to engine
- Engine routes instruction blocks to Execution Manager
- NO direct method calls to other components

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
  - [Task 18: USDT Market Neutral Quality Gates](../../.cursor/tasks/18_usdt_market_neutral_quality_gates.md) - Generic vs Mode-Specific Architecture (100% complete - config-driven parameters implemented)
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

## Integration Points

### Called BY
- EventDrivenStrategyEngine (full_loop): strategy_manager.update_state(timestamp, 'full_loop')
- EventDrivenStrategyEngine (tight_loop): strategy_manager.update_state(timestamp, 'tight_loop')
- Manual triggers (manual): strategy_manager.update_state(timestamp, 'manual')

### Calls TO
- exposure_monitor.get_current_exposure() - current exposure data
- risk_monitor.get_current_risk_metrics() - risk metrics
- data_provider.get_data(timestamp) - market data queries

### Communication
- Direct method calls ONLY
- NO event publishing
- NO Redis/message queues
- NO async/await in internal methods

## Current Implementation Status

**Overall Completion**: 85% (Spec complete, implementation needs updates)

### **Core Functionality Status**
- ✅ **Working**: Mode detection, action decision logic, instruction generation
- ⚠️ **Partial**: Error handling patterns, event logging integration
- ❌ **Missing**: Concrete strategy implementations, health integration
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
- [Strategy Factory Specification](5A_STRATEGY_FACTORY.md) - Factory for creating strategy instances
- [Base Strategy Manager Specification](5B_BASE_STRATEGY_MANAGER.md) - Abstract base class
- [Exposure Monitor Specification](02_EXPOSURE_MONITOR.md) - Exposure data provider
- [Risk Monitor Specification](03_RISK_MONITOR.md) - Risk metrics provider

### **Configuration and Implementation**
- [Configuration Guide](19_CONFIGURATION.md) - Complete config schemas for all 7 modes
- [Code Structure Patterns](../CODE_STRUCTURE_PATTERNS.md) - Implementation patterns
- [Event Logger Specification](08_EVENT_LOGGER.md) - Event logging integration

---

**Status**: Specification complete! ✅  
**Last Reviewed**: October 11, 2025


