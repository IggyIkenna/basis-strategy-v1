# MODE-AGNOSTIC ARCHITECTURE REQUIREMENTS

## OVERVIEW
Components must be mode-agnostic where appropriate, but strategy mode-specific where necessary. The key distinction is between **execution mode** (backtest vs live) and **strategy mode** (pure lending, BTC basis, etc.). Components should be execution mode-agnostic but can be strategy mode-aware for configuration-driven nuances.

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

## SUCCESS CRITERIA
- [ ] P&L monitor is completely mode-agnostic
- [ ] All utility methods are centralized
- [ ] No utility methods in execution interfaces
- [ ] No duplicated utility methods across components
- [ ] All components use centralized utility manager
- [ ] All components access same global data states
- [ ] P&L calculation works consistently for both modes
- [ ] System architecture is simplified and more maintainable
