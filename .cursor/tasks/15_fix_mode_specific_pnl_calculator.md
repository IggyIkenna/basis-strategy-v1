# CRITICAL FIX: Make P&L Calculator Mode-Agnostic

## CONTEXT
The P&L calculator is currently mode-specific (different logic for backtest vs live), which violates architecture principles. It should be mode-agnostic and work for both modes.

## ISSUE IDENTIFIED
- **Mode-specific P&L logic**: Different calculation logic for backtest vs live modes
- **Utility methods in execution interfaces**: `_get_liquidity_index` should be centralized
- **Duplicated utility methods**: Same methods duplicated across components
- **Inconsistent data access**: Components not using same global data states

## REQUIRED FIX

### 1. Make P&L Monitor Mode-Agnostic
- **Single logic**: P&L monitor must work for both backtest and live modes
- **No mode-specific code**: Remove any mode-specific P&L calculation logic
- **Universal balance calculation**: Calculate balances across all venues and asset types
- **Mode-independent**: Should not care whether data comes from backtest simulation or live APIs

### 2. Centralize Utility Methods
- **Remove from execution interfaces**: Move `_get_liquidity_index` out of execution interfaces
- **Create centralized utility manager**: All utility methods in one place
- **Shared access**: All components that need these utilities must use the same methods
- **Global data states**: All utilities must access the same global data states

### 3. Universal Balance Calculation
P&L monitor must calculate balances across:
- **Wallets**: All wallet balances
- **Smart contract pools**: AAVE, Lido, EtherFi, etc.
- **CEX spot**: All centralized exchange spot balances
- **CEX derivatives**: All centralized exchange futures/derivatives balances
- **Overall USDT balance**: Total USDT equivalent value
- **Overall share class balance**: Total share class value (ETH or USDT)

### 4. Generic P&L Attribution System
- **Universal attribution logic**: All P&L attributions work the same way across all modes
- **Mode-agnostic attributions**: Some modes won't use certain attributions (0 P&L for unused attributions)
- **Generic basis attribution**: Rename "BTC basis P&L" to "basis attribution" - applies to any spot long + perp short position
- **Share class driven reporting**: P&L attribution only cares about share_class from configs/modes/*.yaml to determine reporting currency
- **Config-driven parameters**: Components care about specific config parameters (share_class, asset, lst_type, hedge_allocation) not strategy mode
- **No mode-specific if statements**: Remove mode-specific logic from P&L calculations

## IMPLEMENTATION REQUIREMENTS

### 1. Create Centralized Utility Manager
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
    
    def get_share_class_from_mode(self, mode: str) -> str:
        """Get share class from mode config."""
        return self.config.get(f'modes.{mode}.share_class')
    
    def convert_to_share_class_currency(self, amount: float, token: str, share_class: str, timestamp: datetime) -> float:
        """Convert token amount to share class currency (ETH or USDT)."""
        if share_class == 'USDT':
            return self.convert_to_usdt(amount, token, timestamp)
        elif share_class == 'ETH':
            return self.convert_to_eth(amount, token, timestamp)
        else:
            raise ValueError(f"Unknown share class: {share_class}")
    
    def convert_to_eth(self, amount: float, token: str, timestamp: datetime) -> float:
        """Convert token amount to ETH equivalent."""
        price = self.get_market_price(token, 'ETH', timestamp)
        return amount * price
```

### 2. Update P&L Monitor to be Mode-Agnostic
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
        
        # Calculate total share class balance (ETH or USDT)
        total_share_class_balance = self._calculate_total_share_class_balance(
            wallet_balances, smart_contract_balances, 
            cex_spot_balances, cex_derivatives_balances, timestamp
        )
        
        # Calculate P&L change since last snapshot
        pnl_change = self._calculate_pnl_change(
            total_usdt_balance, total_share_class_balance, timestamp
        )
        
        return pnl_change
    
    def calculate_pnl_attribution(self, exposures, timestamp, mode):
        """Calculate P&L attribution regardless of mode, but report in share class currency."""
        # Get share class from mode config (only thing we care about from strategy mode)
        share_class = self.utility_manager.get_share_class_from_mode(mode)
        
        attribution = {}
        
        # Generic basis attribution (spot long + perp short)
        attribution['basis'] = self._calculate_basis_attribution(exposures, timestamp, share_class)
        
        # Generic funding attribution (short perp exposure * funding rate)
        attribution['funding'] = self._calculate_funding_attribution(exposures, timestamp, share_class)
        
        # Generic delta attribution (net delta exposure)
        attribution['delta'] = self._calculate_delta_attribution(exposures, timestamp, share_class)
        
        # Generic lending attribution (lending yield)
        attribution['lending'] = self._calculate_lending_attribution(exposures, timestamp, share_class)
        
        # Generic staking attribution (staking yield)
        attribution['staking'] = self._calculate_staking_attribution(exposures, timestamp, share_class)
        
        return attribution
    
    def _calculate_basis_attribution(self, exposures, timestamp, share_class):
        """Calculate basis attribution for any spot long + perp short position."""
        # Find spot long positions
        spot_long_exposure = 0.0
        perp_short_exposure = 0.0
        
        for venue, positions in exposures.items():
            if venue.startswith('cex_spot'):
                for token, position in positions.items():
                    if position > 0:  # Long position
                        spot_long_exposure += position
        
        for venue, positions in exposures.items():
            if venue.startswith('cex_derivatives'):
                for token, position in positions.items():
                    if position < 0:  # Short position
                        perp_short_exposure += abs(position)
        
        # Calculate basis P&L if we have both spot long and perp short
        if spot_long_exposure > 0 and perp_short_exposure > 0:
            # Get spot and perp prices in share class currency
            spot_price = self.utility_manager.get_market_price('BTC', share_class, timestamp)
            perp_price = self.utility_manager.get_market_price('BTC-PERP', share_class, timestamp)
            
            # Basis P&L = (spot_price - perp_price) * min(spot_long, perp_short)
            basis_spread = spot_price - perp_price
            basis_exposure = min(spot_long_exposure, perp_short_exposure)
            return basis_spread * basis_exposure
        
        return 0.0  # No basis attribution if no spot long + perp short positions
```

### 3. Update All Components to Use Centralized Utilities
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

## FILES TO MODIFY

### 1. Create New Files
- **backend/src/basis_strategy_v1/core/utilities/utility_manager.py**: Centralized utility manager
- **backend/src/basis_strategy_v1/core/utilities/__init__.py**: Utilities package init

### 2. Modify Existing Files
- **backend/src/basis_strategy_v1/core/math/pnl_calculator.py**: Make mode-agnostic with generic attribution system
- **backend/src/basis_strategy_v1/core/interfaces/onchain_execution_interface.py**: Remove utility methods
- **backend/src/basis_strategy_v1/core/interfaces/cex_execution_interface.py**: Remove utility methods
- **backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py**: Use centralized utilities
- **backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py**: Use centralized utilities

### 3. Update Component Manager
- **backend/src/basis_strategy_v1/core/component_manager.py**: Add utility manager to component initialization

### 4. Update Configuration Files
- **configs/share_classes/usdt_share_class.yaml**: Add USD/USDT conversion rate
- **configs/share_classes/eth_share_class.yaml**: Add USD/ETH conversion rate
- **backend/src/basis_strategy_v1/core/config/config_models.py**: Add conversion rate fields to Pydantic models

## SUCCESS CRITERIA

### P&L Monitor
- [ ] P&L monitor is completely mode-agnostic
- [ ] No mode-specific P&L calculation logic
- [ ] Calculates balances across all venues (wallets, smart contracts, CEX spot, CEX derivatives)
- [ ] Uses centralized utility methods
- [ ] Works for both backtest and live modes
- [ ] Generic P&L attribution system implemented
- [ ] All attribution types calculated uniformly (basis, funding, delta, lending, staking)
- [ ] Unused attributions return 0 P&L (no mode-specific if statements)
- [ ] Balance tracking in both USD and share class terms (ETH or USDT)

### Utility Manager
- [ ] Centralized utility manager created
- [ ] All utility methods centralized (liquidity index, market prices, conversions)
- [ ] No utility methods in execution interfaces
- [ ] No duplicated utility methods across components
- [ ] All utilities access global data states
- [ ] USD/USDT conversion methods using share class config
- [ ] Configurable conversion rates in YAML files

### Component Integration
- [ ] All components use centralized utility manager
- [ ] No local utility methods in components
- [ ] All components access same global data states
- [ ] All operations use current event loop timestamp
- [ ] Consistent data access across all components

### Configuration Integration
- [ ] Share class config files updated with conversion rates
- [ ] Pydantic models updated with conversion rate fields
- [ ] No hardcoded conversion rates (1:1 USD/USDT)
- [ ] All conversion rates configurable via YAML

## VALIDATION REQUIREMENTS

### Architecture Validation
- [ ] P&L monitor is mode-agnostic
- [ ] Utility methods are centralized
- [ ] No utility methods in execution interfaces
- [ ] No duplicated utility methods across components
- [ ] All components use centralized utility manager
- [ ] Generic P&L attribution system works across all modes
- [ ] No mode-specific if statements in P&L calculations
- [ ] All attribution types calculated uniformly

### Functionality Validation
- [ ] P&L calculation works for both backtest and live modes
- [ ] All utility methods work correctly
- [ ] All components can access utilities
- [ ] Data access is consistent across components
- [ ] System architecture is simplified and more maintainable
- [ ] Generic attribution system works for all strategy modes
- [ ] Unused attributions return 0 P&L correctly
- [ ] Balance tracking works in both USD and share class terms
- [ ] Conversion rates work correctly from config

## MANDATORY QUALITY GATE VALIDATION
**BEFORE MOVING TO NEXT TASK**, you MUST:

1. **Run Pure Lending Quality Gates**:
   ```bash
   python scripts/test_pure_lending_quality_gates.py
   ```

2. **Run BTC Basis Quality Gates**:
   ```bash
   python scripts/test_btc_basis_quality_gates.py
   ```

3. **Verify P&L Attribution System**:
   - Generic attribution system works for both strategies
   - No mode-specific if statements in P&L calculations
   - All attribution types calculated uniformly
   - Unused attributions return 0 P&L correctly

4. **Verify Utility Manager Integration**:
   - All components use centralized utility manager
   - No utility methods in execution interfaces
   - Configurable conversion rates work correctly
   - No hardcoded values remain

5. **Document Results**:
   - P&L attribution system validation results
   - Utility manager integration status
   - Any remaining mode-specific logic found
   - Overall architecture compliance status

**DO NOT PROCEED TO NEXT TASK** until quality gates validate the mode-agnostic P&L calculator is working correctly.

## FORBIDDEN PRACTICES
- ❌ Making P&L monitor mode-specific
- ❌ Putting utility methods in execution interfaces
- ❌ Duplicating utility methods across components
- ❌ Having different P&L calculation logic per mode
- ❌ Not using centralized utility manager
- ❌ Using mode-specific if statements in P&L calculations
- ❌ Hardcoding conversion rates (1:1 USD/USDT)
- ❌ Having different attribution logic per mode
- ❌ Making attribution calculations mode-specific

## REQUIRED PRACTICES
- ✅ Make P&L monitor mode-agnostic
- ✅ Centralize all utility methods
- ✅ Use centralized utility manager in all components
- ✅ Access global data states using current event loop timestamp
- ✅ Ensure consistent data access across all components
- ✅ Implement generic P&L attribution system
- ✅ Calculate all attribution types uniformly across modes
- ✅ Use configurable conversion rates from YAML files
- ✅ Track balances in both USD and share class terms
- ✅ Return 0 P&L for unused attributions (no mode-specific logic)

## IMPLEMENTATION EXAMPLES

### Generic Attribution System
```python
# ✅ CORRECT: Generic basis attribution
def _calculate_basis_attribution(self, exposures, timestamp):
    """Works for any spot long + perp short position."""
    # Find any spot long positions
    spot_long_exposure = self._get_spot_long_exposure(exposures)
    # Find any perp short positions  
    perp_short_exposure = self._get_perp_short_exposure(exposures)
    
    if spot_long_exposure > 0 and perp_short_exposure > 0:
        # Calculate basis P&L for any token pair
        return self._calculate_basis_pnl(spot_long_exposure, perp_short_exposure, timestamp)
    
    return 0.0  # No basis attribution if no positions

# ❌ WRONG: Mode-specific attribution
def _calculate_btc_basis_attribution(self, exposures, timestamp, mode):
    if mode == 'btc_basis':
        # BTC-specific logic
        return self._calculate_btc_basis_pnl(exposures, timestamp)
    elif mode == 'eth_basis':
        # ETH-specific logic
        return self._calculate_eth_basis_pnl(exposures, timestamp)
    else:
        return 0.0
```

### Configurable Conversion Rates
```python
# ✅ CORRECT: Configurable conversion rates
def convert_usd_to_usdt(self, amount_usd: float, share_class: str) -> float:
    conversion_rate = self.config.get(f'share_classes.{share_class}.usd_to_usdt_rate', 1.0)
    return amount_usd * conversion_rate

# ❌ WRONG: Hardcoded conversion rates
def convert_usd_to_usdt(self, amount_usd: float) -> float:
    return amount_usd * 1.0  # Hardcoded 1:1 rate
```

DO NOT make P&L monitor mode-specific. Use centralized utility methods and generic attribution system for all components.
