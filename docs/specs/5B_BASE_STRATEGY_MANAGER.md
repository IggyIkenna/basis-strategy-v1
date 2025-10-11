# Base Strategy Manager Component Specification

## Purpose
Abstract base class for all strategy managers providing inheritance-based architecture with standardized wrapper actions and mode-specific strategy logic.

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](../MODES.md) - Canonical strategy mode definitions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides
- **Config-Driven Architecture**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Mode-agnostic architecture guide
- **Code Structures**: [CODE_STRUCTURE_PATTERNS.md](../CODE_STRUCTURE_PATTERNS.md) - Complete implementation patterns

## Responsibilities
1. Provide abstract base class for all strategy managers
2. Define standardized wrapper actions for all strategy modes
3. Implement inheritance-based architecture for strategy modes
4. Provide mode-specific strategy logic through abstract methods
5. Integrate with tight loop architecture and component dependencies

## State
- strategy_type: str (strategy mode type)
- actions: List[StrategyAction] (available strategy actions)
- rebalancing_triggers: List[str] (rebalancing trigger conditions)
- position_calculation: Dict (position calculation configuration)
- last_action_timestamp: pd.Timestamp
- action_history: List[Dict] (action execution history)

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- risk_monitor: RiskMonitor (reference, for risk checks)
- position_monitor: PositionMonitor (reference, for position data)
- event_engine: EventDrivenStrategyEngine (reference, for event coordination)
- config: Dict (reference, never modified)
- execution_mode: str (BASIS_EXECUTION_MODE)

These references are stored in __init__ and used throughout component lifecycle.
Components NEVER receive these as method parameters during runtime.

## Configuration Parameters

### **Config-Driven Architecture**

The Base Strategy Manager is **mode-specific but config-driven** and uses `component_config.strategy_manager` from the mode configuration:

```yaml
component_config:
  strategy_manager:
    strategy_type: "mode_name"  # Strategy mode type
    actions: ["entry_full", "exit_full"]  # Available actions
    rebalancing_triggers: ["deposit", "withdrawal"]  # Rebalancing triggers
    position_calculation:
      target_position: "aave_usdt_supply"  # Mode-specific position calculation
      max_position: "equity"
```

### **Configuration Parameter Definitions**

| Parameter | Description | Valid Values | Required | Default |
|-----------|-------------|--------------|----------|---------|
| `strategy_type` | Strategy mode type | Mode name string | Yes | None |
| `actions` | Available strategy actions | List of action strings | Yes | [] |
| `rebalancing_triggers` | Rebalancing trigger conditions | List of trigger strings | Yes | [] |
| `position_calculation` | Position calculation configuration | Dict with calculation rules | Yes | {} |

### **Base Strategy Manager Behavior by Strategy Mode**

| Mode | Strategy Type | Actions | Rebalancing Triggers |
|------|---------------|---------|---------------------|
| **Pure Lending** | "pure_lending" | entry_full, exit_full | deposit, withdrawal |
| **BTC Basis** | "btc_basis" | entry_full, exit_full | deposit, withdrawal |
| **ETH Basis** | "eth_basis" | entry_full, exit_full | deposit, withdrawal |
| **ETH Staking Only** | "eth_staking_only" | entry_full, exit_full | deposit, withdrawal |
| **ETH Leveraged** | "eth_leveraged" | entry_full, exit_full | deposit, withdrawal |
| **USDT MN No Leverage** | "usdt_mn_no_leverage" | entry_full, exit_full | deposit, withdrawal |
| **USDT Market Neutral** | "usdt_market_neutral" | entry_full, exit_full | deposit, withdrawal |

**Key Insight**: The Base Strategy Manager provides **inheritance-based architecture** with config-driven behavior. Each strategy mode inherits from this base class and implements mode-specific logic.

**Cross-Reference**: [19_CONFIGURATION.md](19_CONFIGURATION.md) - Complete config schemas with full examples for all 7 modes

## Environment Variables

### System-Level Variables
- **BASIS_EXECUTION_MODE**: 'backtest' | 'live' (determines strategy behavior)
- **BASIS_LOG_LEVEL**: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' (logging level)
- **BASIS_DATA_DIR**: Path to data directory (for backtest mode)

### Component-Specific Variables
- **STRATEGY_MANAGER_TIMEOUT**: Strategy action timeout in seconds (default: 30)
- **STRATEGY_MANAGER_MAX_RETRIES**: Maximum retry attempts for strategy actions (default: 3)

## Config Fields Used

### Universal Config (All Components)
- **execution_mode**: 'backtest' | 'live' (from strategy mode slice)
- **log_level**: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' (from strategy mode slice)

### Component-Specific Config
- **strategy_manager_settings**: Dict (strategy manager-specific settings)
  - **timeout**: Strategy action timeout
  - **max_retries**: Maximum retry attempts
  - **validation_strict**: Strict action validation
- **strategy_settings**: Dict (strategy-specific settings)
  - **strategy_type**: Strategy mode type
  - **actions**: Available strategy actions
  - **rebalancing_triggers**: Rebalancing trigger conditions
  - **position_calculation**: Position calculation configuration

## Config-Driven Behavior

The Base Strategy Manager is **mode-specific but config-driven** - it provides inheritance-based architecture with config-driven behavior:

**Component Configuration** (from `component_config.strategy_manager`):
```yaml
component_config:
  strategy_manager:
    # Strategy Manager is mode-specific but config-driven
    # Uses inheritance-based architecture with config-driven behavior
    strategy_type: "mode_name"  # Strategy mode type
    actions: ["entry_full", "exit_full"]  # Available actions
    rebalancing_triggers: ["deposit", "withdrawal"]  # Rebalancing triggers
    position_calculation:
      target_position: "aave_usdt_supply"  # Mode-specific position calculation
      max_position: "equity"
```

**Mode-Specific but Config-Driven Strategy Logic**:
- Provides inheritance-based architecture for strategy modes
- Uses config-driven action definitions and rebalancing triggers
- Implements mode-specific strategy logic through abstract methods
- Uses config-driven position calculation configuration

**Strategy Logic by Mode**:

**Pure Lending Mode**:
- Inherits: `BaseStrategyManager` with pure lending strategy logic
- Actions: `entry_full`, `exit_full` for AAVE USDT supply
- Rebalancing: `deposit`, `withdrawal` triggers
- Position Calculation: AAVE USDT supply position

**BTC Basis Mode**:
- Inherits: `BaseStrategyManager` with BTC basis strategy logic
- Actions: `entry_full`, `exit_full`, `entry_partial`, `exit_partial` for BTC spot/perp
- Rebalancing: `deposit`, `withdrawal`, `funding_rate_change` triggers
- Position Calculation: BTC spot/perp position with funding rate arbitrage

**ETH Leveraged Mode**:
- Inherits: `BaseStrategyManager` with ETH leveraged strategy logic
- Actions: `entry_full`, `exit_full`, `leverage_up`, `leverage_down` for ETH/LST/AAVE
- Rebalancing: `deposit`, `withdrawal`, `liquidation_risk` triggers
- Position Calculation: ETH/LST/AAVE position with leverage management

**Key Principle**: Base Strategy Manager is **inheritance-based** - it provides:
- Abstract base class for all strategy modes
- Standardized wrapper actions for all strategies
- Mode-specific strategy logic through abstract methods
- Config-driven behavior for actions and rebalancing triggers

All strategy logic is implemented through inheritance - each strategy mode extends the base class and implements mode-specific logic while using config-driven behavior for actions and triggers.

## Abstract Methods

### calculate_target_position()
```python
@abstractmethod
def calculate_target_position(self, timestamp: pd.Timestamp, trigger_source: str) -> Dict[str, Any]:
    """
    Calculate target position for this strategy mode.
    
    Parameters:
    - timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
    - trigger_source: 'full_loop' | 'tight_loop' | 'manual' | 'action_breakdown'
    
    Returns:
    - Dict[str, Any]: Target position configuration with mode-specific fields
    
    Must be implemented by each strategy-specific subclass.
    """
```

### validate_action()
```python
@abstractmethod
def validate_action(self, action: str, timestamp: pd.Timestamp) -> bool:
    """
    Validate strategy action for this mode.
    
    Parameters:
    - action: Strategy action to validate ('entry_full', 'exit_full', etc.)
    - timestamp: Current loop timestamp
    
    Returns:
    - bool: True if action is valid for this strategy mode
    
    Must be implemented by each strategy-specific subclass.
    """
```

### get_rebalancing_condition()
```python
@abstractmethod
def get_rebalancing_condition(self, timestamp: pd.Timestamp) -> Optional[str]:
    """
    Get rebalancing condition for this strategy mode.
    
    Parameters:
    - timestamp: Current loop timestamp
    
    Returns:
    - Optional[str]: Rebalancing condition name or None if no rebalancing needed
      - 'margin_critical': CEX margin ratio too low
      - 'delta_drift': Net delta exposure too high
      - 'ltv_high': AAVE LTV ratio too high
      - 'funding_rate_change': Funding rate opportunity
      - None: No rebalancing needed
    
    Must be implemented by each strategy-specific subclass.
    """
```

## **MODE-AGNOSTIC IMPLEMENTATION EXAMPLE**

### **Complete BaseStrategyManager Class**

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
    
    def _generate_entry_full_instructions(self, target_positions: Dict, params: Dict, market_data: Dict) -> List[Dict]:
        """Generate instruction blocks for entry_full action"""
        # Base implementation - can be overridden by subclasses
        return [{
            'block_id': f"entry_full_{self.last_decision_timestamp}",
            'action': 'entry_full',
            'priority': 1,
            'instructions': [],
            'expected_deltas': target_positions,
            'dependencies': []
        }]
    
    def _generate_entry_partial_instructions(self, target_positions: Dict, params: Dict, market_data: Dict) -> List[Dict]:
        """Generate instruction blocks for entry_partial action"""
        return [{
            'block_id': f"entry_partial_{self.last_decision_timestamp}",
            'action': 'entry_partial',
            'priority': 1,
            'instructions': [],
            'expected_deltas': target_positions,
            'dependencies': []
        }]
    
    def _generate_exit_full_instructions(self, target_positions: Dict, params: Dict, market_data: Dict) -> List[Dict]:
        """Generate instruction blocks for exit_full action"""
        return [{
            'block_id': f"exit_full_{self.last_decision_timestamp}",
            'action': 'exit_full',
            'priority': 1,
            'instructions': [],
            'expected_deltas': target_positions,
            'dependencies': []
        }]
    
    def _generate_exit_partial_instructions(self, target_positions: Dict, params: Dict, market_data: Dict) -> List[Dict]:
        """Generate instruction blocks for exit_partial action"""
        return [{
            'block_id': f"exit_partial_{self.last_decision_timestamp}",
            'action': 'exit_partial',
            'priority': 1,
            'instructions': [],
            'expected_deltas': target_positions,
            'dependencies': []
        }]
    
    def _generate_sell_dust_instructions(self, target_positions: Dict, params: Dict, market_data: Dict) -> List[Dict]:
        """Generate instruction blocks for sell_dust action"""
        return [{
            'block_id': f"sell_dust_{self.last_decision_timestamp}",
            'action': 'sell_dust',
            'priority': 1,
            'instructions': [],
            'expected_deltas': {},
            'dependencies': []
        }]
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

#### **ETHLeveragedStrategy (Most Complex)**
```python
class ETHLeveragedStrategy(BaseStrategyManager):
    """Strategy manager for ETH leveraged mode - most complex"""
    
    def calculate_target_position(self, timestamp: pd.Timestamp, trigger_source: str) -> Dict[str, Any]:
        """ETH leveraged position calculation - complex multi-venue strategy"""
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
        """Validate ETH leveraged strategy actions"""
        # ETH leveraged supports all actions
        return action in self.available_actions
    
    def get_rebalancing_condition(self, timestamp: pd.Timestamp) -> Optional[str]:
        """Check for ETH leveraged rebalancing conditions"""
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

### **Key Benefits of Inheritance-Based Implementation**

1. **Standardized Interface**: All strategies implement the same abstract methods
2. **Config-Driven Parameters**: All behavior determined by `component_config.strategy_manager`
3. **Mode-Specific Logic**: Each strategy implements its own calculation and validation logic
4. **Graceful Data Handling**: Skips calculations when data is unavailable
5. **Easy Extension**: Adding new strategy modes requires new subclass + config
6. **Self-Documenting**: Abstract methods clearly define required interface

### **Config-Driven Parameters**

The BaseStrategyManager works with inheritance to provide both config-driven behavior and mode-specific logic:

| Aspect | Config-Driven | Inheritance-Based | How They Work Together |
|--------|---------------|-------------------|----------------------|
| **Strategy Type** | `strategy_type` parameter | Concrete subclass selection | Config determines which subclass to instantiate |
| **Available Actions** | `actions` list from config | Abstract method implementations | Config defines what actions are available, inheritance provides implementation |
| **Rebalancing Triggers** | `rebalancing_triggers` from config | Mode-specific trigger logic | Config defines triggers, inheritance provides mode-specific handling |
| **Position Calculation** | `position_calculation` config | Abstract `calculate_target_position()` | Config provides parameters, inheritance provides mode-specific calculation logic |
| **Validation** | Config validation rules | Abstract `validate_action()` | Config defines validation rules, inheritance provides mode-specific validation |

## Standardized Wrapper Actions

All strategy modes support these standardized wrapper actions:

1. **entry_full**: Enter full position for the strategy
2. **exit_full**: Exit full position for the strategy
3. **entry_partial**: Enter partial position (if supported by mode)
4. **exit_partial**: Exit partial position (if supported by mode)
5. **rebalance**: Rebalance position based on current conditions

## Integration Points

### Called BY
- Event-Driven Strategy Engine (strategy execution): `strategy_manager.execute_action(action, timestamp)`
- Strategy Factory (strategy initialization): `strategy_manager.initialize(config, dependencies)`
- Backtest Service (strategy setup): `strategy_manager.setup_backtest(config)`

### Calls TO
- Risk Monitor (risk checks): `risk_monitor.check_risk_limits(action)`
- Position Monitor (position data): `position_monitor.get_current_positions()`
- Event Engine (event coordination): `event_engine.trigger_event(event_type, data)`

### Communication
- Direct method calls ONLY
- NO event publishing
- NO Redis/message queues
- NO async/await in internal methods

The Base Strategy Manager integrates with the Event-Driven Strategy Engine to provide:

1. **Action Execution**: Execute strategy actions through the engine
2. **Position Updates**: Update positions through the engine
3. **Risk Checks**: Validate actions through risk monitor
4. **Event Coordination**: Coordinate with other components through the engine

## Error Handling

The Base Strategy Manager handles errors gracefully:

1. **Invalid Actions**: Returns error for unsupported actions
2. **Risk Violations**: Validates actions against risk limits
3. **Position Errors**: Handles position calculation errors
4. **Configuration Errors**: Validates strategy configuration

## Data Provider Queries

### Data Types Requested
`data = self.data_provider.get_data(timestamp)`

#### Market Data
- `prices`: Dict[str, float] - Token prices in USD
  - **Tokens needed**: ETH, BTC, USDT (varies by strategy mode)
  - **Update frequency**: Every timestamp
  - **Usage**: Position calculations, risk assessments

- `rates`: Dict[str, float] - Rates (funding, lending, etc.)
  - **Rates needed**: Funding rates, lending rates (varies by strategy mode)
  - **Update frequency**: Every timestamp
  - **Usage**: Strategy decision making

#### Protocol Data
- `aave_indexes`: Dict[str, float] - AAVE liquidity indexes
  - **Tokens needed**: aUSDT, aETH, aWETH (varies by strategy mode)
  - **Update frequency**: Every timestamp
  - **Usage**: AAVE position calculations

- `oracle_prices`: Dict[str, float] - LST oracle prices
  - **Tokens needed**: wstETH, rETH, sfrxETH (varies by strategy mode)
  - **Update frequency**: Every timestamp
  - **Usage**: LST position calculations

- `perp_prices`: Dict[str, float] - Perpetual mark prices
  - **Instruments needed**: ETH-PERP, BTC-PERP (varies by strategy mode)
  - **Update frequency**: Every timestamp
  - **Usage**: Perpetual position calculations

### Query Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs):
    # Query data with timestamp (data <= timestamp guaranteed)
    data = self.data_provider.get_data(timestamp)
    
    # Access other components via references
    current_exposure = self.exposure_monitor.get_current_exposure()
    risk_metrics = self.risk_monitor.get_current_risk_metrics()
    
    # Process using standardized data structures
    action = self.decide_action(timestamp, current_exposure, risk_metrics, data)
    
    # Update internal state
    self.current_action = action
    self.last_decision_timestamp = timestamp
```

### Data NOT Available from DataProvider
None - all data comes from DataProvider

## Core Methods

### update_state(timestamp: pd.Timestamp, trigger_source: str, **kwargs) -> List[Dict]
Main entry point for strategy decision making.

**Parameters**:
- timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
- trigger_source: 'full_loop' | 'tight_loop' | 'manual'
- **kwargs: Additional parameters (deposit_amount, withdrawal_amount, etc.)

**Behavior**:
1. Query data using: data = self.data_provider.get_data(timestamp)
2. Access component refs: exposure_monitor, risk_monitor
3. Decide action using config-driven triggers and inheritance-based logic
4. Break down action into instruction blocks
5. NO async/await: Synchronous execution only

**Returns**:
- List[Dict]: Instruction blocks for execution

### decide_action(timestamp: pd.Timestamp, current_exposure: Dict, risk_metrics: Dict, market_data: Dict) -> str
Decide which of the configured actions to take.

**Returns**:
- str: Action name or None if no action needed

### break_down_action(action: str, params: Dict, market_data: Dict) -> List[Dict]
Break down action into sequential instruction blocks.

**Returns**:
- List[Dict]: Instruction blocks for execution

## Data Access Pattern

### Query Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs):
    # Query data with timestamp (data <= timestamp guaranteed)
    data = self.data_provider.get_data(timestamp)
    
    # Access other components via references
    current_exposure = self.exposure_monitor.get_current_exposure()
    risk_metrics = self.risk_monitor.get_current_risk_metrics()
    
    # Process using standardized data structures
    action = self.decide_action(timestamp, current_exposure, risk_metrics, data)
    instruction_blocks = self.break_down_action(action, kwargs, data)
    
    # Update internal state
    self.current_action = action
    self.last_decision_timestamp = timestamp
    self.action_history.append({
        'timestamp': timestamp,
        'action': action,
        'trigger_source': trigger_source,
        'instruction_blocks_count': len(instruction_blocks)
    })
```

**NEVER** pass market_data or component refs as parameters between components.
**NEVER** cache market_data across timestamps.

## Mode-Aware Behavior

### Backtest Mode
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs):
    if self.execution_mode == 'backtest':
        # Use historical/simulated data
        data = self.data_provider.get_data(timestamp)
        return self._process_backtest_strategy(data, **kwargs)
```

### Live Mode
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs):
    elif self.execution_mode == 'live':
        # Use real-time data/APIs
        data = self.data_provider.get_data(timestamp)
        return self._process_live_strategy(data, **kwargs)
```

## Event Logging Requirements

### Component Event Log File
**Separate log file** for this component's events:
- **File**: `logs/events/base_strategy_manager_events.jsonl`
- **Format**: JSON Lines (one event per line)
- **Rotation**: Daily rotation, keep 30 days
- **Purpose**: Component-specific audit trail

### Event Logging via EventLogger
All events logged through centralized EventLogger:

```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='[event_type]',
    component='BaseStrategyManager',
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
    component='BaseStrategyManager',
    data={
        'strategy_type': self.strategy_type,
        'available_actions': self.available_actions,
        'config_hash': hash(str(self.config))
    }
)
```

#### 2. Strategy Decisions (Every update_state() Call)
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='strategy_decision',
    component='BaseStrategyManager',
    data={
        'trigger_source': trigger_source,
        'action': action,
        'instruction_blocks_count': len(instruction_blocks),
        'processing_time_ms': processing_time
    }
)
```

#### 3. Error Events
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='error',
    component='BaseStrategyManager',
    data={
        'error_code': 'STRAT-BASE-001',
        'error_message': str(e),
        'stack_trace': traceback.format_exc(),
        'error_severity': 'CRITICAL|HIGH|MEDIUM|LOW'
    }
)
```

#### 4. Component-Specific Critical Events
- **Action Validation Failed**: When action is invalid for strategy mode
- **Position Calculation Failed**: When target position calculation fails
- **Rebalancing Triggered**: When rebalancing condition is met

## Error Codes

### Component Error Code Prefix: STRAT-BASE
All BaseStrategyManager errors use the `STRAT-BASE` prefix.

### Error Code Registry
**Source**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`

All error codes registered with:
- **code**: Unique error code
- **component**: Component name
- **severity**: CRITICAL | HIGH | MEDIUM | LOW
- **message**: Human-readable error message
- **resolution**: How to resolve

### Component Error Codes

#### STRAT-BASE-001: Action Validation Failed (HIGH)
**Description**: Strategy action is invalid for this mode
**Cause**: Invalid action name, action not in available_actions
**Recovery**: Check action against available_actions, verify strategy mode
```python
raise ComponentError(
    error_code='STRAT-BASE-001',
    message='Action validation failed',
    component='BaseStrategyManager',
    severity='HIGH'
)
```

#### STRAT-BASE-002: Position Calculation Failed (HIGH)
**Description**: Target position calculation failed
**Cause**: Missing market data, calculation errors, invalid parameters
**Recovery**: Check market data availability, verify calculation parameters
```python
raise ComponentError(
    error_code='STRAT-BASE-002',
    message='Position calculation failed',
    component='BaseStrategyManager',
    severity='HIGH'
)
```

#### STRAT-BASE-003: Rebalancing Condition Error (MEDIUM)
**Description**: Error in rebalancing condition check
**Cause**: Missing risk metrics, invalid exposure data
**Recovery**: Check risk monitor and exposure monitor data
```python
raise ComponentError(
    error_code='STRAT-BASE-003',
    message='Rebalancing condition error',
    component='BaseStrategyManager',
    severity='MEDIUM'
)
```

### Structured Error Handling Pattern

#### Error Raising
```python
from backend.src.basis_strategy_v1.core.error_codes.exceptions import ComponentError

try:
    action = self.decide_action(timestamp, current_exposure, risk_metrics, market_data)
except Exception as e:
    # Log error event
    self.event_logger.log_event(
        timestamp=timestamp,
        event_type='error',
        component='BaseStrategyManager',
        data={
            'error_code': 'STRAT-BASE-001',
            'error_message': str(e),
            'stack_trace': traceback.format_exc()
        }
    )
    
    # Raise structured error
    raise ComponentError(
        error_code='STRAT-BASE-001',
        message=f'BaseStrategyManager failed: {str(e)}',
        component='BaseStrategyManager',
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
- [ ] Configuration Parameters shows component_config.strategy_manager structure
- [ ] MODE-AGNOSTIC IMPLEMENTATION present (base class is mode-agnostic)
- [ ] Abstract methods documented with inheritance pattern
- [ ] Table showing strategy modes (all 7 modes)
- [ ] Cross-references to CONFIGURATION.md, CODE_STRUCTURE_PATTERNS.md
- [ ] No mode-specific if statements in base class methods
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
- [ ] Inheritance-based patterns documented
- [ ] Abstract method interface documented

## Testing

The Base Strategy Manager supports comprehensive testing:

1. **Unit Tests**: Test abstract methods and wrapper actions
2. **Integration Tests**: Test strategy integration with Event-Driven Strategy Engine
3. **Mock Testing**: Test with mocked dependencies
4. **Error Testing**: Test error handling and recovery

## Current Implementation Status

**Overall Completion**: 90% (Spec complete, implementation needs updates)

### **Core Functionality Status**
- ✅ **Working**: Abstract method definitions, config-driven behavior, inheritance pattern
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
- [Strategy Manager Specification](05_STRATEGY_MANAGER.md) - Concrete strategy implementations
- [Exposure Monitor Specification](02_EXPOSURE_MONITOR.md) - Exposure data provider
- [Risk Monitor Specification](03_RISK_MONITOR.md) - Risk metrics provider

### **Configuration and Implementation**
- [Configuration Guide](19_CONFIGURATION.md) - Complete config schemas for all 7 modes
- [Code Structure Patterns](../CODE_STRUCTURE_PATTERNS.md) - Implementation patterns
- [Event Logger Specification](08_EVENT_LOGGER.md) - Event logging integration

---

**Status**: Specification complete ✅  
**Last Reviewed**: October 11, 2025


