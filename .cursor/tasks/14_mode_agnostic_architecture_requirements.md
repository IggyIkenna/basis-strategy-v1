# MODE-AGNOSTIC ARCHITECTURE REQUIREMENTS

## OVERVIEW
Components must be mode-agnostic where appropriate, but strategy mode-specific where necessary. The key distinction is between **execution mode** (backtest vs live) and **strategy mode** (pure lending, BTC basis, etc.). Components should be execution mode-agnostic but can be strategy mode-aware for configuration-driven nuances.

**Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 7 (Generic vs Mode-Specific)  
**Reference**: `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-003, ADR-004, ADR-005  
**Reference**: `docs/specs/02_EXPOSURE_MONITOR.md` - Generic exposure calculation  
**Reference**: `docs/specs/04_PNL_CALCULATOR.md` - Mode-agnostic P&L calculation

## CRITICAL REQUIREMENTS

### 1. P&L Monitor Must Be Mode-Agnostic
- **Single logic**: P&L monitor must work for both backtest and live modes
- **No mode-specific code**: No different logic per mode
- **Universal balance calculation**: Calculate balances across all venues and asset types
- **Mode-independent**: Should not care whether data comes from backtest simulation or live APIs

### 2. Centralized Utility Methods
- **Liquidity index**: Must be centralized method, not in execution interfaces
- **Market prices**: Must be centralized method for all token/currency conversions
- **Shared access**: All components that need these utilities must use the same methods
- **Global data states**: All utilities must access the same global data states

### 3. Universal Balance Calculation
P&L monitor must calculate balances across:
- **Wallets**: All wallet balances
- **Smart contract pools**: AAVE, Lido, EtherFi, etc.
- **CEX spot**: All centralized exchange spot balances
- **CEX derivatives**: All centralized exchange futures/derivatives balances
- **Overall USDT balance**: Total USDT equivalent value
- **Overall share class balance**: Total share class value

## FORBIDDEN PRACTICES

### ❌ Mode-Specific P&L Logic
```python
# ❌ WRONG: Different P&L logic per mode
class PnLMonitor:
    def calculate_pnl(self, mode):
        if mode == 'backtest':
            return self._calculate_backtest_pnl()
        elif mode == 'live':
            return self._calculate_live_pnl()
```

### ❌ Utility Methods in Execution Interfaces
```python
# ❌ WRONG: Utility method in execution interface
class OnChainExecutionInterface:
    def _get_liquidity_index(self, token, timestamp):
        # This should be centralized, not in execution interface
        pass
```

### ❌ Duplicated Utility Methods
```python
# ❌ WRONG: Same utility method in multiple components
class OnChainExecutionInterface:
    def _get_liquidity_index(self, token, timestamp):
        pass

class ExposureMonitor:
    def _get_liquidity_index(self, token, timestamp):  # Duplicate!
        pass
```

## REQUIRED IMPLEMENTATION

### ✅ Mode-Agnostic P&L Monitor
```python
class PnLMonitor:
    """Mode-agnostic P&L monitor that works for both backtest and live modes."""
    
    def __init__(self, config, data_provider, utility_manager):
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager  # Centralized utilities
    
    def calculate_pnl(self, exposures, timestamp):
        """Calculate P&L regardless of mode."""
        # Get all balances across all venues
        wallet_balances = self._get_wallet_balances(exposures, timestamp)
        smart_contract_balances = self._get_smart_contract_balances(exposures, timestamp)
        cex_spot_balances = self._get_cex_spot_balances(exposures, timestamp)
        cex_derivatives_balances = self._get_cex_derivatives_balances(exposures, timestamp)
        
        # Calculate total USDT equivalent
        total_usdt_balance = self._calculate_total_usdt_balance(
            wallet_balances, smart_contract_balances, 
            cex_spot_balances, cex_derivatives_balances, timestamp
        )
        
        # Calculate total share class balance
        total_share_class_balance = self._calculate_total_share_class_balance(
            wallet_balances, smart_contract_balances, 
            cex_spot_balances, cex_derivatives_balances, timestamp
        )
        
        # Calculate P&L change since last snapshot
        pnl_change = self._calculate_pnl_change(
            total_usdt_balance, total_share_class_balance, timestamp
        )
        
        return pnl_change
```

### ✅ Centralized Utility Manager
```python
class UtilityManager:
    """Centralized utility methods for all components."""
    
    def __init__(self, config, data_provider):
        self.config = config
        self.data_provider = data_provider
    
    def get_liquidity_index(self, token: str, timestamp: datetime) -> float:
        """Get liquidity index for a token at a specific timestamp."""
        return self.data_provider.get_liquidity_index(token, timestamp)
    
    def get_market_price(self, token: str, currency: str, timestamp: datetime) -> float:
        """Get market price for token in specified currency at timestamp."""
        return self.data_provider.get_market_price(token, currency, timestamp)
    
    def convert_to_usdt(self, amount: float, token: str, timestamp: datetime) -> float:
        """Convert token amount to USDT equivalent."""
        price = self.get_market_price(token, 'USDT', timestamp)
        return amount * price
    
    def convert_from_liquidity_index(self, amount: float, token: str, timestamp: datetime) -> float:
        """Convert from liquidity index (e.g., aUSDT to USDT)."""
        liquidity_index = self.get_liquidity_index(token, timestamp)
        return amount / liquidity_index
```

### ✅ Component Usage of Centralized Utilities
```python
class OnChainExecutionInterface:
    def __init__(self, config, data_provider, utility_manager):
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager  # Use centralized utilities
    
    def execute_trade(self, instruction, market_data):
        # Use centralized utility instead of local method
        liquidity_index = self.utility_manager.get_liquidity_index(
            instruction['token'], market_data['timestamp']
        )
        # ... rest of execution logic

class ExposureMonitor:
    def __init__(self, config, data_provider, utility_manager):
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager  # Use centralized utilities
    
    def calculate_exposure(self, positions, timestamp):
        # Use centralized utility instead of local method
        liquidity_index = self.utility_manager.get_liquidity_index(
            'USDT', timestamp
        )
        # ... rest of exposure calculation
```

## P&L MONITOR REQUIREMENTS

### Universal Balance Calculation
The P&L monitor must calculate balances across all venues:

#### 1. Wallet Balances
- **All tokens**: ETH, USDT, BTC, etc.
- **All venues**: Binance, Bybit, OKX, etc.
- **USDT equivalent**: Convert all to USDT using market prices

#### 2. Smart Contract Balances
- **AAVE**: aUSDT, aETH, etc. (convert using liquidity index)
- **Lido**: stETH (convert using market price)
- **EtherFi**: eETH (convert using market price)
- **Other protocols**: All other smart contract positions

#### 3. CEX Spot Balances
- **All exchanges**: Binance, Bybit, OKX, etc.
- **All tokens**: All spot positions
- **USDT equivalent**: Convert all to USDT

#### 4. CEX Derivatives Balances
- **All exchanges**: Binance, Bybit, OKX, etc.
- **All derivatives**: Futures, options, etc.
- **USDT equivalent**: Convert all to USDT

#### 5. Overall Balances
- **Total USDT balance**: Sum of all USDT equivalents
- **Total share class balance**: Sum of all share class values
- **P&L change**: Change since last snapshot

## IMPLEMENTATION REQUIREMENTS

### 1. Remove Mode-Specific Logic
- **P&L monitor**: Remove any mode-specific P&L calculation logic
- **Execution interfaces**: Remove utility methods, use centralized ones
- **Exposure monitor**: Remove utility methods, use centralized ones
- **All components**: Use centralized utility manager

### 2. Create Centralized Utility Manager
- **Liquidity index**: Centralized method for all components
- **Market prices**: Centralized method for all components
- **Conversions**: Centralized methods for all conversions
- **Global data access**: All utilities access same global data states

### 3. Update Component Architecture
- **Dependency injection**: All components receive utility manager
- **Shared utilities**: All components use same utility methods
- **Consistent data**: All components access same global data states
- **Timestamp-based**: All operations use current event loop timestamp

## VALIDATION REQUIREMENTS

### P&L Monitor Validation
- [ ] P&L monitor is mode-agnostic
- [ ] No mode-specific P&L calculation logic
- [ ] Calculates balances across all venues
- [ ] Uses centralized utility methods
- [ ] Works for both backtest and live modes

### Utility Manager Validation
- [ ] Centralized utility manager created
- [ ] All utility methods centralized
- [ ] No utility methods in execution interfaces
- [ ] No duplicated utility methods across components
- [ ] All utilities access global data states

### Component Integration Validation
- [ ] All components use centralized utility manager
- [ ] No local utility methods in components
- [ ] All components access same global data states
- [ ] All operations use current event loop timestamp
- [ ] Consistent data access across all components

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
- [ ] P&L monitor is completely mode-agnostic
- [ ] All utility methods are centralized
- [ ] No utility methods in execution interfaces
- [ ] No duplicated utility methods across components
- [ ] All components use centralized utility manager
- [ ] All components access same global data states
- [ ] P&L calculation works consistently for both modes
- [ ] System architecture is simplified and more maintainable
- [ ] Generic components are mode-agnostic
- [ ] Components care about config parameters, not strategy mode
- [ ] P&L attribution only cares about share_class for reporting
- [ ] Position monitor is generic monitoring tool
- [ ] Strategy manager is naturally strategy mode specific
- [ ] Data subscriptions are strategy mode dependent
- [ ] No hardcoded strategy mode logic in generic components
- [ ] All config parameters properly accessed from YAML files
