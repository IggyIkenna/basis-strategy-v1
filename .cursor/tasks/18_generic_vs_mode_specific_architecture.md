# GENERIC VS MODE-SPECIFIC ARCHITECTURE REQUIREMENTS

## OVERVIEW
Components should be generic and mode-agnostic, but care about specific config parameters rather than strategy mode. Only a few components are naturally strategy mode specific.

## GENERIC COMPONENTS (Mode-Agnostic)

### 1. Position Monitor
- **Should be**: Generic monitoring tool, not strategy mode specific
- **Cares about**: All positions across all venues (wallets, smart contracts, CEX spot, CEX derivatives)
- **Doesn't care about**: Strategy mode, only tracks positions generically

### 2. P&L Attribution
- **Should be**: Generic attribution logic across all modes
- **Cares about**: 
  - **share_class** from configs/modes/*.yaml (determines reporting currency)
  - Generic attribution types (basis, funding, delta, lending, staking)
- **Doesn't care about**: Strategy mode specifics, only share class for reporting

### 3. Exposure Monitor
- **Should be**: Generic exposure calculation
- **Cares about**: 
  - **asset** from config (which deltas to monitor/measure directional exposure in)
  - **share_class** from config (reporting currency)
- **Doesn't care about**: Strategy mode specifics

### 4. Risk Monitor
- **Should be**: Generic risk assessment
- **Cares about**: 
  - **asset** from config (which assets to assess risk for)
  - **share_class** from config (reporting currency)
- **Doesn't care about**: Strategy mode specifics

### 5. Utility Manager
- **Should be**: Generic utility methods
- **Cares about**: 
  - **share_class** from config (conversion methods)
  - Generic utility functions (liquidity index, market prices, conversions)
- **Doesn't care about**: Strategy mode specifics

## CONFIG-DRIVEN PARAMETERS

### Common Config Parameters Components Care About:
1. **share_class**: What P&L to report in (ETH or USDT)
2. **asset**: Which deltas to monitor/measure directional exposure in
3. **lst_type**: Which staking venue for staking strategies
4. **hedge_allocation**: For basis strategies
5. **venue_configs**: Which venues to use
6. **data_requirements**: What data to subscribe to

### Config Structure:
```yaml
# configs/modes/pure_lending.yaml
share_class: "USDT"
asset: "USDT"
lst_type: null  # Not applicable for pure lending
hedge_allocation: null  # Not applicable for pure lending

# configs/modes/btc_basis.yaml
share_class: "USDT"
asset: "BTC"
lst_type: null  # Not applicable for BTC basis
hedge_allocation: 0.5  # 50% hedge allocation

# configs/modes/eth_staking.yaml
share_class: "ETH"
asset: "ETH"
lst_type: "lido"  # Use Lido for staking
hedge_allocation: null  # Not applicable for staking
```

## MODE-SPECIFIC COMPONENTS (Naturally Strategy Mode Specific)

### 1. Strategy Manager
- **Should be**: Strategy mode specific by nature
- **Reason**: Each strategy has its own rules and config variations
- **Cares about**: Strategy mode, execution instructions, strategy-specific logic

### 2. Data Subscriptions
- **Should be**: Heavily strategy mode dependent
- **Reason**: Different strategies need different data feeds
- **Cares about**: 
  - **data_requirements** from config
  - Strategy-specific data needs
  - Live vs historical data requirements

### 3. Execution Interfaces
- **Should be**: Strategy mode aware for data subscriptions
- **Reason**: Need to know what data to subscribe to
- **Cares about**: 
  - **venue_configs** from config
  - **data_requirements** from config
  - Strategy-specific execution requirements

## IMPLEMENTATION REQUIREMENTS

### 1. Generic Component Design
```python
class PositionMonitor:
    """Generic position monitoring tool."""
    
    def __init__(self, config, data_provider):
        self.config = config
        self.data_provider = data_provider
        # No strategy mode dependency
    
    def get_all_positions(self, timestamp):
        """Get all positions across all venues."""
        # Generic position tracking, no mode-specific logic
        pass

class PnLMonitor:
    """Generic P&L monitoring and attribution."""
    
    def __init__(self, config, data_provider, utility_manager):
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        # No strategy mode dependency
    
    def calculate_pnl_attribution(self, exposures, timestamp, mode):
        """Calculate P&L attribution, report in share class currency."""
        # Only care about share_class from mode config
        share_class = self.utility_manager.get_share_class_from_mode(mode)
        # Generic attribution logic
        pass
```

### 2. Config-Driven Parameter Access
```python
class ExposureMonitor:
    """Generic exposure monitoring."""
    
    def __init__(self, config, data_provider, utility_manager):
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
    
    def calculate_exposure(self, positions, timestamp, mode):
        """Calculate exposure based on config parameters."""
        # Get config parameters, not strategy mode logic
        asset = self.config.get(f'modes.{mode}.asset')
        share_class = self.config.get(f'modes.{mode}.share_class')
        
        # Generic exposure calculation using config parameters
        pass
```

### 3. Strategy Mode Specific Components
```python
class StrategyManager:
    """Strategy mode specific by nature."""
    
    def __init__(self, config, data_provider, mode):
        self.config = config
        self.data_provider = data_provider
        self.mode = mode  # Strategy mode specific
    
    def generate_execution_instructions(self, market_data, timestamp):
        """Generate strategy-specific execution instructions."""
        # Strategy mode specific logic
        if self.mode == 'pure_lending':
            return self._generate_lending_instructions(market_data, timestamp)
        elif self.mode == 'btc_basis':
            return self._generate_basis_instructions(market_data, timestamp)
        # etc.
```

## FORBIDDEN PRACTICES

### ❌ Mode-Specific Generic Components
```python
# ❌ WRONG: Position monitor caring about strategy mode
class PositionMonitor:
    def get_positions(self, mode):
        if mode == 'pure_lending':
            return self._get_lending_positions()
        elif mode == 'btc_basis':
            return self._get_basis_positions()

# ❌ WRONG: P&L attribution caring about strategy mode
class PnLMonitor:
    def calculate_attribution(self, mode):
        if mode == 'btc_basis':
            return self._calculate_btc_basis_attribution()
        elif mode == 'eth_staking':
            return self._calculate_eth_staking_attribution()
```

### ❌ Hardcoded Strategy Mode Logic
```python
# ❌ WRONG: Hardcoded strategy mode checks
def calculate_exposure(self, mode):
    if mode == 'btc_basis':
        return self._calculate_btc_exposure()
    elif mode == 'eth_staking':
        return self._calculate_eth_exposure()
```

## REQUIRED PRACTICES

### ✅ Config-Driven Generic Components
```python
# ✅ CORRECT: Position monitor is generic
class PositionMonitor:
    def get_all_positions(self, timestamp):
        """Get all positions across all venues."""
        # Generic position tracking
        pass

# ✅ CORRECT: P&L attribution cares only about share class
class PnLMonitor:
    def calculate_attribution(self, exposures, timestamp, mode):
        share_class = self.utility_manager.get_share_class_from_mode(mode)
        # Generic attribution logic, report in share class currency
        pass

# ✅ CORRECT: Exposure monitor uses config parameters
class ExposureMonitor:
    def calculate_exposure(self, positions, timestamp, mode):
        asset = self.config.get(f'modes.{mode}.asset')
        share_class = self.config.get(f'modes.{mode}.share_class')
        # Generic exposure calculation using config parameters
        pass
```

### ✅ Strategy Mode Specific Components
```python
# ✅ CORRECT: Strategy manager is naturally mode specific
class StrategyManager:
    def __init__(self, config, data_provider, mode):
        self.mode = mode  # Strategy mode specific by nature
    
    def generate_execution_instructions(self, market_data, timestamp):
        # Strategy mode specific logic
        pass
```

## VALIDATION REQUIREMENTS

### Generic Component Validation
- [ ] Position monitor is generic and mode-agnostic
- [ ] P&L attribution is generic but cares about share_class
- [ ] Exposure monitor uses config parameters (asset, share_class)
- [ ] Risk monitor uses config parameters (asset, share_class)
- [ ] Utility manager is generic with config-driven conversions

### Config Parameter Validation
- [ ] All components access config parameters, not strategy mode logic
- [ ] share_class determines reporting currency
- [ ] asset determines which deltas to monitor
- [ ] lst_type determines staking venue
- [ ] hedge_allocation determines basis strategy parameters

### Strategy Mode Specific Validation
- [ ] Strategy manager is strategy mode specific by nature
- [ ] Data subscriptions are strategy mode dependent
- [ ] Execution interfaces are strategy mode aware for data subscriptions

## SUCCESS CRITERIA
- [ ] Generic components are mode-agnostic
- [ ] Components care about config parameters, not strategy mode
- [ ] P&L attribution only cares about share_class for reporting
- [ ] Position monitor is generic monitoring tool
- [ ] Strategy manager is naturally strategy mode specific
- [ ] Data subscriptions are strategy mode dependent
- [ ] No hardcoded strategy mode logic in generic components
- [ ] All config parameters properly accessed from YAML files

