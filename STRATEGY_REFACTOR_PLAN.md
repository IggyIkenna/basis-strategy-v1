# ETH Staking Only Strategy Refactor Plan

## Overview

Refactor all strategy implementations to align with consistent architectural patterns. This comprehensive refactor covers 9 different strategies across multiple asset classes and execution types, from simple staking to complex ML-driven directional trading.

## Complete Strategy Matrix

| Strategy | Share Class | Asset | Type | Data Type | Key Features |
|----------|-------------|-------|------|-----------|--------------|
| ETH Staking Only | ETH | ETH | Simple Staking | defi | WETH → LST |
| ETH Leveraged | ETH | ETH | Leveraged Staking | defi | Atomic flash loans |
| Pure Lending ETH | ETH | ETH | Lending | defi | ETH → aETH |
| Pure Lending USDT | USDT | USDT | Lending | defi | USDT → aUSDT |
| ETH Basis | ETH/USDT | ETH | Delta Neutral | defi | Long spot + short perp |
| BTC Basis | USDT | BTC | Delta Neutral | defi | Long spot + short perp |
| ML BTC Directional (BTC Margin) | BTC | BTC | ML Directional | cefi | ML signals → perp trades |
| ML BTC Directional (USDT Margin) | USDT | BTC | ML Directional | cefi | ML signals → perp trades |
| USDT Market Neutral (Leveraged) | USDT | ETH | Market Neutral | defi | Staking + hedging |
| USDT Market Neutral (Simple) | USDT | ETH | Market Neutral | defi | Staking + hedging |

## Better Naming Conventions

**Current Confusing Names → Recommended Names:**

| Current Name | Recommended Name | Reason |
|--------------|------------------|---------|
| `usdt_market_neutral_strategy.py` | `usdt_eth_staking_hedged_leveraged_strategy.py` | Clear: USDT share class, ETH asset, staking + hedging, leveraged |
| `usdt_market_neutral_no_leverage_strategy.py` | `usdt_eth_staking_hedged_simple_strategy.py` | Clear: USDT share class, ETH asset, staking + hedging, simple |

**Naming Convention Benefits:**
- **Share Class**: USDT, ETH, BTC
- **Asset**: ETH, BTC, USDT  
- **Strategy Type**: Staking, Leveraged, Lending, Basis, ML Directional, Market Neutral
- **Sub-type**: Hedged, Simple, Leveraged, etc.

This makes it immediately clear what each strategy does and how it differs from others.

## Dust Handling Strategy

### Implementation Details

**Staking Strategies (Active Dust Handling):**
```python
def _create_dust_sell_orders(self, dust_tokens: Dict[str, float]) -> List[Order]:
    """Convert staking dust to share class currency."""
    orders = []
    
    for token, amount in dust_tokens.items():
        if amount > 0 and token != self.share_class:
            # Convert dust tokens (ETH, EIGEN, ETHFI) to share class
            if token in ['ETH', 'EIGEN', 'ETHFI']:
                orders.append(Order(
                    venue='binance',  # or appropriate venue
                    operation=OrderOperation.SPOT_TRADE,
                    pair=f'{token}/{self.share_class}',
                    side='SELL',
                    amount=amount,
                    execution_mode='sequential',
                    strategy_intent='dust_cleanup',
                    strategy_id=self.strategy_id
                ))
    
    return orders
```

**Non-Staking Strategies (Pass-Through Dust Handling):**
```python
def _create_dust_sell_orders(self, dust_tokens: Dict[str, float]) -> List[Order]:
    """Pass-through method: track but don't trade dust."""
    # Non-staking strategies only have ETH network transaction fees as dust
    # These are tracked but not actively traded
    logger.info(f"Dust tokens tracked but not traded: {dust_tokens}")
    return []  # No orders created
```

**Staking Strategies (Need Dust Handling):**
- ETH Staking Only
- ETH Leveraged  
- USDT Market Neutral (both versions)
- **Dust Sources**: ETH (from gas/borrow), EIGEN, ETHFI from staking yields
- **Action**: Convert dust to share class currency

**Non-Staking Strategies (Pass-Through Dust Handling):**
- Pure Lending ETH/USDT
- ETH/BTC Basis Trading
- ML BTC Directional
- **Dust Sources**: Only ETH network transaction fees
- **Action**: Track but don't trade (pass-through method)

## Key Changes

### 1. Strategy Architecture Alignment

The ETH Staking Only strategy should be similar to ETH Leveraged strategy but simplified:

**Difference from ETH Leveraged:**
- ETH Leveraged: Atomic flash loan staking with leverage to reach `target_ltv`
- ETH Staking Only: Simple staking without leverage (WETH → stake to get LST)

### 2. Constructor Updates

**Update `__init__` method to match BaseStrategyManager signature:**

Current (incorrect):
```python
def __init__(self, config: Dict[str, Any], risk_monitor, position_monitor, event_engine):
```

New (correct):
```python
def __init__(self, config: Dict[str, Any], data_provider, exposure_monitor, 
             position_monitor, risk_monitor, utility_manager=None, 
             correlation_id: str = None, pid: int = None, log_dir: Path = None):
```

**Add missing attributes:**
- `self.share_class = config.get('share_class', 'ETH')`
- `self.asset = config.get('asset', 'ETH')`
- Add `from pathlib import Path` import

### 3. Implement Missing Methods

**Add the 5 standard strategy actions that are currently missing:**

1. `_create_entry_full_orders(equity: float) -> List[Order]`
2. `_create_entry_partial_orders(equity_delta: float) -> List[Order]`
3. `_create_exit_full_orders(equity: float) -> List[Order]`
4. `_create_exit_partial_orders(equity_delta: float) -> List[Order]`
5. `_create_dust_sell_orders(dust_tokens: Dict[str, float]) -> List[Order]`

**Simple staking order sequence:**
```python
# For entry_full and entry_partial:
# 1. STAKE WETH to get LST (weETH/wstETH)
orders.append(Order(
    venue=self.staking_protocol,
    operation=OrderOperation.STAKE,
    token_in='WETH',
    token_out=self.lst_type,
    amount=eth_amount,
    execution_mode='sequential',
    strategy_intent='entry_full',
    strategy_id='eth_staking_only'
))

# For exit_full and exit_partial:
# 1. UNSTAKE LST to get WETH
orders.append(Order(
    venue=self.staking_protocol,
    operation=OrderOperation.UNSTAKE,
    token_in=self.lst_type,
    token_out='WETH',
    amount=lst_amount,
    execution_mode='sequential',
    strategy_intent='exit_full',
    strategy_id='eth_staking_only'
))
```

### 4. Update generate_orders Method

**Current implementation is incomplete - needs to call the 5 standard actions:**

Current (incorrect):
```python
def generate_orders(self, timestamp: pd.Timestamp, exposure: Dict, risk_assessment: Dict, pnl: Dict, market_data: Dict) -> List[Order]:
    try:
        current_equity = self.get_current_equity(exposure)
        
        # Determine action based on current state
        if current_equity == 0:
            # No position - enter full
            return self._create_entry_full_orders(current_equity)
        elif risk_assessment.get('risk_override', False):
            # Risk override - exit full
            return self._create_exit_full_orders(current_equity)
        elif exposure.get('withdrawal_requested', False):
            # Withdrawal requested - exit full
            return self._create_exit_full_orders(current_equity)
        else:
            # Maintain current position
            return []
```

New (correct):
```python
def generate_orders(self, timestamp: pd.Timestamp, exposure: Dict, risk_assessment: Dict, pnl: Dict, market_data: Dict) -> List[Order]:
    """
    Generate orders for ETH staking only strategy.
    
    Args:
        timestamp: Current timestamp
        exposure: Current exposure data
        risk_assessment: Risk assessment data
        pnl: Current PnL data (deprecated)
        market_data: Current market data
        
    Returns:
        List of Order objects to execute
    """
    try:
        # Get current equity and positions
        current_equity = exposure.get('total_exposure', 0.0)
        current_positions = exposure.get('positions', {})
        
        # Check if we have any position
        has_position = current_positions.get(f'{self.lst_type.lower()}_balance', 0.0) > 0
        
        # ETH Staking Only Strategy Decision Logic
        if current_equity > 0 and not has_position:
            # Enter full position
            return self._create_entry_full_orders(current_equity)
        elif current_equity > 0 and has_position:
            # Check for dust tokens to sell
            dust_tokens = exposure.get('dust_tokens', {})
            if dust_tokens:
                return self._create_dust_sell_orders(dust_tokens)
            else:
                # No action needed
                return []
        else:
            # No equity or exit needed
            return []
            
    except Exception as e:
        self.log_error(
            error=e,
            context={
                'method': 'generate_orders',
                'strategy_type': self.__class__.__name__
            }
        )
        logger.error(f"Error in ETH staking only strategy order generation: {e}")
        return []
```

### 5. Add Missing Utility Method

**Add `_get_asset_price()` method:**
```python
def _get_asset_price(self) -> float:
    """Get current ETH price for testing."""
    # In real implementation, this would get actual price from market data
    return 3000.0  # Mock ETH price
```

### 6. Update Documentation

**Files to update:**

- `docs/STRATEGY_MODES.md` (lines 316-378)
  - Fix asset configuration (should be "ETH" not "USDT")
  - Update execution flow to be simpler (no leverage)
  - Clarify difference from ETH Leveraged strategy
  - Update risk profile to remove leverage references

**Key documentation changes:**
- **Asset**: Should be "ETH" not "USDT" (line 341)
- **Execution Flow**: Simple staking without leverage
- **Key Difference**: No atomic flash loans, no AAVE operations
- **Risk Profile**: No liquidation risk, no leverage risk

### 7. Update Config File

**File:** `configs/modes/eth_staking_only.yaml`

**Verify configuration:**
- `share_class: "ETH"`
- `asset: "ETH"`
- `borrowing_enabled: false`
- `lending_enabled: false`
- `staking_enabled: true`
- No AAVE venues needed
- No Instadapp venues needed

## Files to Modify

1. `backend/src/basis_strategy_v1/core/strategies/eth_staking_only_strategy.py` - Main strategy refactor
2. `backend/src/basis_strategy_v1/core/strategies/pure_lending_eth_strategy.py` - Pure lending ETH strategy refactor
3. `backend/src/basis_strategy_v1/core/strategies/pure_lending_usdt_strategy.py` - Pure lending USDT strategy refactor
4. `backend/src/basis_strategy_v1/core/strategies/eth_basis_strategy.py` - ETH basis trading strategy refactor
5. `backend/src/basis_strategy_v1/core/strategies/btc_basis_strategy.py` - BTC basis trading strategy refactor
6. `backend/src/basis_strategy_v1/core/strategies/ml_btc_directional_btc_margin_strategy.py` - ML BTC directional strategy refactor
7. `backend/src/basis_strategy_v1/core/strategies/ml_btc_directional_usdt_margin_strategy.py` - ML BTC directional strategy refactor
8. `backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_strategy.py` - USDT market neutral strategy refactor
9. `backend/src/basis_strategy_v1/core/strategies/usdt_market_neutral_no_leverage_strategy.py` - USDT market neutral no leverage strategy refactor
10. `docs/STRATEGY_MODES.md` - Update strategy documentation
11. `configs/modes/eth_staking_only.yaml` - Verify configuration (if needed)
12. `configs/modes/pure_lending_eth.yaml` - Verify configuration (if needed)
13. `configs/modes/pure_lending_usdt.yaml` - Verify configuration (if needed)
14. `configs/modes/eth_basis.yaml` - Verify configuration (if needed)
15. `configs/modes/btc_basis.yaml` - Verify configuration (if needed)
16. `configs/modes/ml_btc_directional_btc_margin.yaml` - Verify configuration (if needed)
17. `configs/modes/ml_btc_directional_usdt_margin.yaml` - Verify configuration (if needed)
18. `configs/modes/usdt_market_neutral.yaml` - Verify configuration (if needed)
19. `configs/modes/usdt_market_neutral_no_leverage.yaml` - Verify configuration (if needed)

## Testing Requirements

**ETH Staking Only Strategy:**
- Unit tests for `ETHStakingOnlyStrategy.generate_orders()`
- Verify simple staking order sequence
- Test `calculate_target_position()` with various equity values
- Integration test with position_monitor
- Verify no leverage or borrowing logic

**Pure Lending ETH Strategy:**
- Unit tests for `PureLendingETHStrategy.generate_orders()`
- Verify simple lending order sequence (ETH → aETH)
- Test position deviation logic with various thresholds
- Test `calculate_target_position()` with various equity values
- Integration test with AAVE position tracking

**Pure Lending USDT Strategy:**
- Unit tests for `PureLendingUSDTStrategy.generate_orders()`
- Verify simple lending order sequence (USDT → aUSDT)
- Test position deviation logic with various thresholds
- Test `calculate_target_position()` with various equity values
- Integration test with AAVE position tracking

**Basis Trading Strategies:**
- Unit tests for `ETHBasisStrategy.generate_orders()` and `BTCBasisStrategy.generate_orders()`
- Verify delta-neutral position logic (long spot + short perp)
- Test position deviation logic for both spot and perp positions
- Test sequential execution of multiple rebalancing orders
- Integration test with CEX venues (Binance, Bybit)

**ML Directional Strategies:**
- Unit tests for both ML BTC directional strategies
- Verify ML signal processing and interpretation
- Test confidence threshold logic (>0.8)
- Test signal mapping (SWING_LOW_BREAKOUT → SHORT, etc.)
- Test hold logic (no action when signal matches current position)
- Integration test with ML data provider and signal data
- Test signal granularity configuration (5min intervals)

**USDT Market Neutral Strategies:**
- Unit tests for both USDT market neutral strategies
- Verify position allocation logic (stake vs hedge equity)
- Test stake allocation percentage configuration
- Test hedge allocation across venues (Binance, Bybit, OKX)
- Verify market neutral mechanics (staking + perp short)
- Integration test with both DeFi (staking) and CEX (hedging) venues
- Test leveraged vs simple staking components
- Test active dust handling (convert staking dust to USDT)

**All Strategies:**
- Verify all 5 standard strategy actions work correctly
- Test rebalancing logic based on `position_deviation_threshold`
- Verify no leverage, borrowing, or staking logic where not applicable
- Test error handling and edge cases
- Verify proper order creation for each strategy type
- Test position calculation accuracy
- Test dust handling differences (active vs pass-through)

## Implementation Notes

- **Simplicity**: This strategy should be the simplest possible - just stake ETH to get LST
- **No Leverage**: No flash loans, no AAVE operations, no borrowing
- **Sequential Execution**: All operations are sequential, not atomic
- **Clean Architecture**: Follow the same patterns as ETH Leveraged but simplified
- **WETH Standard**: Use WETH not ETH for all operations (DeFi standard)

---

## Pure Lending Strategies Refactor

### Overview

Refactor both `pure_lending_eth_strategy.py` and `pure_lending_usdt_strategy.py` to implement simple lending strategies that take ETH/USDT respectively and lend it on AAVE, receiving aTokens for their deposits.

### Strategy Architecture

**Pure Lending ETH Strategy:**
- Takes ETH and lends it on AAVE
- Receives aETH tokens for deposits
- Target amount = current equity
- Exit: withdraw aETH to get ETH back

**Pure Lending USDT Strategy:**
- Takes USDT and lends it on AAVE  
- Receives aUSDT tokens for deposits
- Target amount = current equity
- Exit: withdraw aUSDT to get USDT back

### Key Implementation Details

**Position Deviation Logic:**
```python
# Check if rebalancing is needed based on position_deviation_threshold
position_deviation_threshold = self.strategy_config.get('position_deviation_threshold', 0.02)  # 2%

current_lent_amount = current_positions.get(f'aave_v3:aToken:a{self.asset}', 0.0)
target_lent_amount = current_equity
deviation = abs(current_lent_amount - target_lent_amount) / target_lent_amount if target_lent_amount > 0 else 0

if deviation > position_deviation_threshold:
    # Create rebalancing orders
    return self._create_rebalancing_orders(current_equity, current_lent_amount)
```

**Simple Lending Order Sequence:**

For ETH Strategy:
```python
# Entry: Supply ETH to AAVE
orders.append(Order(
    venue='aave_v3',
    operation=OrderOperation.SUPPLY,
    token_in='ETH',
    token_out='aETH',
    amount=eth_amount,
    execution_mode='sequential',
    strategy_intent='entry_full',
    strategy_id='pure_lending_eth'
))

# Exit: Withdraw aETH from AAVE
orders.append(Order(
    venue='aave_v3',
    operation=OrderOperation.WITHDRAW,
    token_out='ETH',
    amount=aeth_amount,
    execution_mode='sequential',
    strategy_intent='exit_full',
    strategy_id='pure_lending_eth'
))
```

For USDT Strategy:
```python
# Entry: Supply USDT to AAVE
orders.append(Order(
    venue='aave_v3',
    operation=OrderOperation.SUPPLY,
    token_in='USDT',
    token_out='aUSDT',
    amount=usdt_amount,
    execution_mode='sequential',
    strategy_intent='entry_full',
    strategy_id='pure_lending_usdt'
))

# Exit: Withdraw aUSDT from AAVE
orders.append(Order(
    venue='aave_v3',
    operation=OrderOperation.WITHDRAW,
    token_out='USDT',
    amount=ausdt_amount,
    execution_mode='sequential',
    strategy_intent='exit_full',
    strategy_id='pure_lending_usdt'
))
```

### Required Changes

**1. Constructor Updates:**
- Both strategies already have correct BaseStrategyManager signature
- Add missing `share_class` and `asset` attributes from config
- Add `from pathlib import Path` import to USDT strategy

**2. Implement Missing Methods:**
Both strategies need the 5 standard actions:
- `_create_entry_full_orders(equity: float) -> List[Order]`
- `_create_entry_partial_orders(equity_delta: float) -> List[Order]`
- `_create_exit_full_orders(equity: float) -> List[Order]`
- `_create_exit_partial_orders(equity_delta: float) -> List[Order]`
- `_create_dust_sell_orders(dust_tokens: Dict[str, float]) -> List[Order]` (Pass-through: track but don't trade)

**3. Update generate_orders Method:**
- Implement position deviation logic using `component_config.strategy_manager.position_deviation_threshold`
- Compare current lent amount vs target equity
- Create rebalancing orders when deviation exceeds threshold

**4. Add Utility Methods:**
- `_get_asset_price()` method for price calculations
- `_calculate_position_deviation()` method for rebalancing logic

**5. Position Calculation:**
```python
def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
    """Calculate target position for pure lending strategy."""
    return {
        f'aave_v3:aToken:a{self.asset}': current_equity,  # Target lent amount
        f'{self.share_class.lower()}_balance': 0.0,  # No reserve balance
        'total_equity': current_equity
    }
```

### Configuration Updates

**Pure Lending ETH Config:**
- `share_class: "ETH"`
- `asset: "ETH"`
- `borrowing_enabled: false`
- `lending_enabled: true`
- `staking_enabled: false`

**Pure Lending USDT Config:**
- `share_class: "USDT"`
- `asset: "USDT"` (fix from current "BTC")
- `borrowing_enabled: false`
- `lending_enabled: true`
- `staking_enabled: false`

### Documentation Updates

**Update STRATEGY_MODES.md:**
- Fix asset configuration for USDT strategy
- Clarify simple lending mechanics
- Document position deviation threshold logic
- Update risk profiles (no leverage, no staking risk)

## Expected Result

All three strategies will be clean, simple implementations that:

**ETH Staking Only:**
- Stakes WETH to get LST tokens (weETH/wstETH)
- No leverage or borrowing
- No complex atomic transactions

**Pure Lending ETH:**
- Lends ETH on AAVE to get aETH tokens
- Target amount = current equity
- Rebalances based on position deviation threshold

**Pure Lending USDT:**
- Lends USDT on AAVE to get aUSDT tokens  
- Target amount = current equity
- Rebalances based on position deviation threshold

**Basis Trading Strategies:**
- Long spot + short perp positions (delta neutral)
- Target amount = current equity for both positions
- Rebalances based on position deviation threshold
- Captures funding rate premiums

**ML Directional Strategies:**
- ML signal-driven BTC perpetual trading
- Confidence threshold >0.8 for signal execution
- Signal interpretation: SWING_LOW_BREAKOUT → SHORT, SWING_HIGH_BREAKOUT → LONG, etc.
- Position size = current equity (always long or short by equity amount)
- Hold logic: no action when signal matches current position
- CEFI data type for ML signals

**USDT Market Neutral Strategies:**
- USDT share class with ETH asset exposure
- Position allocation: stake_allocation_percentage for staking, remainder for hedging
- Leveraged version: ETH leveraged staking + ETH perp short hedge
- Simple version: ETH simple staking + ETH perp short hedge
- Hedge allocation across venues (Binance, Bybit, OKX)
- Market neutral: reduced directional risk through hedging

**All Strategies:**
- Follow the same architectural patterns
- Implement the 5 standard strategy actions
- Use sequential execution (not atomic)
- Easy to understand and maintain
- Proper position deviation logic for rebalancing
- Clean separation of concerns (staking, lending, basis trading, ML directional)

---

## Basis Trading Strategies Refactor

### Overview

Refactor both `eth_basis_strategy.py` and `btc_basis_strategy.py` to implement delta-neutral basis trading strategies that go long spot and short perpetuals to capture funding rate differentials.

### Strategy Architecture

**ETH Basis Strategy:**
- Long ETH spot position = current equity
- Short ETH perpetual position = current equity
- Delta neutral (net ETH exposure = 0)
- Captures funding rate premiums from shorts

**BTC Basis Strategy:**
- Long BTC spot position = current equity
- Short BTC perpetual position = current equity
- Delta neutral (net BTC exposure = 0)
- Captures funding rate premiums from shorts

### Key Implementation Details

**Position Deviation Logic:**
```python
# Check if rebalancing is needed based on position_deviation_threshold
position_deviation_threshold = self.strategy_config.get('position_deviation_threshold', 0.02)  # 2%

current_spot = current_positions.get(f'{self.asset.lower()}_balance', 0.0)
current_perp = current_positions.get(f'{self.asset.lower()}_perp_short', 0.0)
target_position = current_equity

spot_deviation = abs(current_spot - target_position) / target_position if target_position > 0 else 0
perp_deviation = abs(current_perp - target_position) / target_position if target_position > 0 else 0

orders = []
if spot_deviation > position_deviation_threshold:
    orders.extend(self._create_spot_rebalancing_orders(current_equity, current_spot))
if perp_deviation > position_deviation_threshold:
    orders.extend(self._create_perp_rebalancing_orders(current_equity, current_perp))

return orders
```

**Basis Trading Order Sequences:**

For ETH Basis Strategy:
```python
# Spot Long: Buy ETH spot
orders.append(Order(
    venue='binance',
    operation=OrderOperation.SPOT_TRADE,
    pair='ETH/USDT',
    side='BUY',
    amount=eth_amount,
    execution_mode='sequential',
    strategy_intent='basis_spot_long',
    strategy_id='eth_basis'
))

# Perp Short: Short ETH perpetual
orders.append(Order(
    venue='bybit',
    operation=OrderOperation.PERP_TRADE,
    pair='ETHUSDT',
    side='SHORT',
    amount=eth_amount,
    execution_mode='sequential',
    strategy_intent='basis_perp_short',
    strategy_id='eth_basis'
))
```

For BTC Basis Strategy:
```python
# Spot Long: Buy BTC spot
orders.append(Order(
    venue='binance',
    operation=OrderOperation.SPOT_TRADE,
    pair='BTC/USDT',
    side='BUY',
    amount=btc_amount,
    execution_mode='sequential',
    strategy_intent='basis_spot_long',
    strategy_id='btc_basis'
))

# Perp Short: Short BTC perpetual
orders.append(Order(
    venue='bybit',
    operation=OrderOperation.PERP_TRADE,
    pair='BTCUSDT',
    side='SHORT',
    amount=btc_amount,
    execution_mode='sequential',
    strategy_intent='basis_perp_short',
    strategy_id='btc_basis'
))
```

### Required Changes

**1. Constructor Updates:**
- Both strategies already have correct BaseStrategyManager signature
- Add missing `share_class` and `asset` attributes from config
- Add hedge venue allocation configuration

**2. Implement Missing Methods:**
Both strategies need the 5 standard actions:
- `_create_entry_full_orders(equity: float) -> List[Order]`
- `_create_entry_partial_orders(equity_delta: float) -> List[Order]`
- `_create_exit_full_orders(equity: float) -> List[Order]`
- `_create_exit_partial_orders(equity_delta: float) -> List[Order]`
- `_create_dust_sell_orders(dust_tokens: Dict[str, float]) -> List[Order]` (Pass-through: track but don't trade)

**3. Update generate_orders Method:**
- Implement position deviation logic for both spot and perp positions
- Create separate rebalancing orders for spot and perp if both deviate
- Handle sequential execution of multiple orders

**4. Position Calculation:**
```python
def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
    """Calculate target position for basis trading strategy."""
    return {
        f'{self.asset.lower()}_balance': current_equity,  # Long spot
        f'{self.asset.lower()}_perp_short': current_equity,  # Short perp
        f'{self.share_class.lower()}_balance': 0.0,  # No reserve balance
        'total_equity': current_equity
    }
```

### Configuration Updates

**ETH Basis Config:**
- `share_class: "ETH"` or `"USDT"`
- `asset: "ETH"`
- `borrowing_enabled: false`
- `lending_enabled: false`
- `staking_enabled: false`
- `basis_trade_enabled: true`

**BTC Basis Config:**
- `share_class: "USDT"`
- `asset: "BTC"`
- `borrowing_enabled: false`
- `lending_enabled: false`
- `staking_enabled: false`
- `basis_trade_enabled: true`

---

## ML Directional Strategies Refactor

### Overview

Refactor both `ml_btc_directional_btc_margin_strategy.py` and `ml_btc_directional_usdt_margin_strategy.py` to implement ML-driven directional BTC trading strategies that read signals from `data/ml_data/predictions/btc_predictions.csv` and execute long/short positions based on signal confidence and direction.

### Strategy Architecture

**ML BTC Directional Strategy (Both Margin Types):**
- Reads ML signals from data provider via `ml_service.py`
- Signal confidence threshold: >0.8
- Signal types and meanings:
  - `SWING_LOW_BREAKOUT`: Sell signal (go short)
  - `SWING_HIGH_BREAKOUT`: Buy signal (go long)
  - `SWING_HIGH_REVERSAL`: Sell signal (go short)
  - `SWING_LOW_NEUTRAL`: Neutral signal (go flat)
- Position size: Always long or short by current equity amount
- Hold logic: If signal direction matches current position, do nothing

### Key Implementation Details

**ML Signal Processing:**
```python
def _get_ml_signal(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
    """Get ML signal for current timestamp."""
    try:
        # Get ML prediction from data provider
        ml_data = self.data_provider.get_ml_prediction(timestamp, 'BTC')
        
        if not ml_data:
            return {'signal': 'NEUTRAL', 'confidence': 0.0}
        
        return {
            'signal': ml_data['prediction'],
            'confidence': ml_data['confidence'],
            'timestamp': timestamp
        }
    except Exception as e:
        logger.error(f"Error getting ML signal: {e}")
        return {'signal': 'NEUTRAL', 'confidence': 0.0}

def _interpret_signal(self, signal_data: Dict[str, Any]) -> str:
    """Interpret ML signal into trading action."""
    signal = signal_data['signal']
    confidence = signal_data['confidence']
    
    if confidence < 0.8:  # Confidence threshold
        return 'HOLD'
    
    signal_mapping = {
        'SWING_LOW_BREAKOUT': 'SHORT',
        'SWING_HIGH_BREAKOUT': 'LONG',
        'SWING_HIGH_REVERSAL': 'SHORT',
        'SWING_LOW_NEUTRAL': 'FLAT'
    }
    
    return signal_mapping.get(signal, 'HOLD')
```

**ML Trading Order Sequences:**

```python
# Long Position: Buy BTC perpetual
orders.append(Order(
    venue='binance',
    operation=OrderOperation.PERP_TRADE,
    pair='BTCUSDT',
    side='LONG',
    amount=btc_amount,
    execution_mode='sequential',
    strategy_intent='ml_long',
    strategy_id='ml_btc_directional'
))

# Short Position: Short BTC perpetual
orders.append(Order(
    venue='binance',
    operation=OrderOperation.PERP_TRADE,
    pair='BTCUSDT',
    side='SHORT',
    amount=btc_amount,
    execution_mode='sequential',
    strategy_intent='ml_short',
    strategy_id='ml_btc_directional'
))

# Flat Position: Close current position
orders.append(Order(
    venue='binance',
    operation=OrderOperation.PERP_TRADE,
    pair='BTCUSDT',
    side='LONG' if current_position < 0 else 'SHORT',  # Close opposite
    amount=abs(current_position),
    execution_mode='sequential',
    strategy_intent='ml_flat',
    strategy_id='ml_btc_directional'
))
```

### Required Changes

**1. Constructor Updates:**
- Fix constructor signature to match BaseStrategyManager
- Add missing `share_class` and `asset` attributes from config
- Add ML-specific configuration (signal granularity, confidence threshold)

**2. Implement Missing Methods:**
Both strategies need the 5 standard actions:
- `_create_entry_full_orders(equity: float, signal: str) -> List[Order]`
- `_create_entry_partial_orders(equity_delta: float, signal: str) -> List[Order]`
- `_create_exit_full_orders(equity: float) -> List[Order]`
- `_create_exit_partial_orders(equity_delta: float) -> List[Order]`
- `_create_dust_sell_orders(dust_tokens: Dict[str, float]) -> List[Order]` (Pass-through: track but don't trade)

**3. Update generate_orders Method:**
- Get ML signal for current timestamp
- Check signal confidence threshold
- Determine if position change is needed
- Create appropriate orders based on signal direction

**4. Add ML-Specific Methods:**
- `_get_ml_signal(timestamp: pd.Timestamp) -> Dict[str, Any]`
- `_interpret_signal(signal_data: Dict[str, Any]) -> str`
- `_should_change_position(current_position: float, signal: str) -> bool`

**5. Position Calculation:**
```python
def calculate_target_position(self, current_equity: float, signal: str) -> Dict[str, float]:
    """Calculate target position for ML directional strategy."""
    if signal == 'LONG':
        return {
            'btc_perp_long': current_equity,
            'btc_perp_short': 0.0,
            f'{self.share_class.lower()}_balance': 0.0,
            'total_equity': current_equity
        }
    elif signal == 'SHORT':
        return {
            'btc_perp_long': 0.0,
            'btc_perp_short': current_equity,
            f'{self.share_class.lower()}_balance': 0.0,
            'total_equity': current_equity
        }
    else:  # FLAT or HOLD
        return {
            'btc_perp_long': 0.0,
            'btc_perp_short': 0.0,
            f'{self.share_class.lower()}_balance': current_equity,
            'total_equity': current_equity
        }
```

### Configuration Updates

**ML BTC Directional BTC Margin Config:**
- `share_class: "BTC"`
- `asset: "BTC"`
- `data_type: "cefi"`  # CEFI data type for ML signals
- `borrowing_enabled: false`
- `lending_enabled: false`
- `staking_enabled: false`
- `ml_enabled: true`
- `signal_granularity: "5min"`
- `confidence_threshold: 0.8`

**ML BTC Directional USDT Margin Config:**
- `share_class: "USDT"`
- `asset: "BTC"`
- `data_type: "cefi"`  # CEFI data type for ML signals
- `borrowing_enabled: false`
- `lending_enabled: false`
- `staking_enabled: false`
- `ml_enabled: true`
- `signal_granularity: "5min"`
- `confidence_threshold: 0.8`

### Key Differences Between Margin Types

**BTC Margin vs USDT Margin:**
- **No impact on trading direction or instrument** - both trade BTC perpetuals
- **Margin type only affects**: Which margin currency is used on the exchange
- **Pre-funded assumption**: Margin is already supplied on exchange
- **No wallet/DeFi activity**: Ready to long/short perps immediately
- **Same signal processing**: Both use same ML signals and logic

### Documentation Updates

**Update STRATEGY_MODES.md:**
- Document basis trading mechanics (long spot + short perp)
- Document ML signal interpretation and confidence thresholds
- Clarify margin type differences (no impact on trading logic)
- Update risk profiles for directional vs delta-neutral strategies
- Document signal granularity configuration options

---

## USDT Market Neutral Strategies Refactor

### Overview

Refactor both `usdt_market_neutral_strategy.py` and `usdt_market_neutral_no_leverage_strategy.py` to implement USDT share class strategies that combine ETH staking/leveraged staking with ETH perpetual shorting to create market-neutral positions.

### Strategy Architecture

**USDT Market Neutral Strategy (Leveraged):**
- Similar to ETH Leveraged Strategy but with USDT share class
- Fraction of equity: ETH leveraged staking (via atomic flash loans)
- Remaining equity: ETH perpetual short positions (market neutral hedge)
- `stake_allocation_percentage`: Portion of equity for staking
- `hedge_allocation`: Venue allocation for hedging (Binance, Bybit, OKX)

**USDT Market Neutral No Leverage Strategy:**
- Similar to ETH Staking Only Strategy but with USDT share class
- Fraction of equity: ETH staking (simple staking)
- Remaining equity: ETH perpetual short positions (market neutral hedge)
- `stake_allocation_percentage`: Portion of equity for staking
- `hedge_allocation`: Venue allocation for hedging (Binance, Bybit, OKX)

### Key Implementation Details

**Position Allocation Logic:**
```python
def _calculate_position_allocation(self, current_equity: float) -> Dict[str, float]:
    """Calculate position allocation between staking and hedging."""
    stake_allocation_pct = self.strategy_config.get('stake_allocation_percentage', 0.5)  # 50% default
    
    stake_equity = current_equity * stake_allocation_pct
    hedge_equity = current_equity * (1 - stake_allocation_pct)
    
    return {
        'stake_equity': stake_equity,
        'hedge_equity': hedge_equity,
        'stake_allocation_pct': stake_allocation_pct
    }
```

**Market Neutral Order Sequences:**

For USDT Market Neutral Strategy (Leveraged):
```python
# 1. ETH Leveraged Staking (atomic flash loan sequence)
if stake_equity > 0:
    # Same as ETH Leveraged Strategy but with stake_equity amount
    orders.extend(self._create_eth_leveraged_orders(stake_equity, target_ltv))

# 2. ETH Perpetual Short (hedge allocation)
if hedge_equity > 0:
    hedge_venues = self.strategy_config.get('hedge_allocation', {})
    for venue, allocation_pct in hedge_venues.items():
        venue_hedge_amount = hedge_equity * allocation_pct
        orders.append(Order(
            venue=venue,
            operation=OrderOperation.PERP_TRADE,
            pair='ETHUSDT',
            side='SHORT',
            amount=venue_hedge_amount,
            execution_mode='sequential',
            strategy_intent='market_neutral_hedge',
            strategy_id='usdt_market_neutral'
        ))
```

For USDT Market Neutral No Leverage Strategy:
```python
# 1. ETH Staking (simple staking)
if stake_equity > 0:
    # Same as ETH Staking Only Strategy but with stake_equity amount
    orders.extend(self._create_eth_staking_orders(stake_equity))

# 2. ETH Perpetual Short (hedge allocation)
if hedge_equity > 0:
    hedge_venues = self.strategy_config.get('hedge_allocation', {})
    for venue, allocation_pct in hedge_venues.items():
        venue_hedge_amount = hedge_equity * allocation_pct
        orders.append(Order(
            venue=venue,
            operation=OrderOperation.PERP_TRADE,
            pair='ETHUSDT',
            side='SHORT',
            amount=venue_hedge_amount,
            execution_mode='sequential',
            strategy_intent='market_neutral_hedge',
            strategy_id='usdt_market_neutral_no_leverage'
        ))
```

### Required Changes

**1. Constructor Updates:**
- Fix constructor signature to match BaseStrategyManager
- Add missing `share_class` and `asset` attributes from config
- Add stake allocation and hedge allocation configuration

**2. Implement Missing Methods:**
Both strategies need the 5 standard actions:
- `_create_entry_full_orders(equity: float) -> List[Order]`
- `_create_entry_partial_orders(equity_delta: float) -> List[Order]`
- `_create_exit_full_orders(equity: float) -> List[Order]`
- `_create_exit_partial_orders(equity_delta: float) -> List[Order]`
- `_create_dust_sell_orders(dust_tokens: Dict[str, float]) -> List[Order]` (Active: convert staking dust to USDT)

**3. Add Allocation Methods:**
- `_calculate_position_allocation(equity: float) -> Dict[str, float]`
- `_create_eth_leveraged_orders(stake_equity: float, target_ltv: float) -> List[Order]`
- `_create_eth_staking_orders(stake_equity: float) -> List[Order]`
- `_create_hedge_orders(hedge_equity: float) -> List[Order]`

**4. Position Calculation:**
```python
def calculate_target_position(self, current_equity: float, target_ltv: float = None) -> Dict[str, float]:
    """Calculate target position for USDT market neutral strategy."""
    allocation = self._calculate_position_allocation(current_equity)
    
    if self.strategy_type == 'leveraged':
        # Leveraged staking positions
        leverage = target_ltv / (1 - target_ltv) if target_ltv and target_ltv < 1.0 else 1.0
        return {
            'eth_balance': 0.0,
            f'{self.lst_type.lower()}_balance': allocation['stake_equity'] * leverage,
            'aave_v3:aToken:aWETH': allocation['stake_equity'] * leverage,
            'aave_v3:debtToken:debtWETH': allocation['stake_equity'] * (leverage - 1),
            'eth_perpetual_short': allocation['hedge_equity'],
            f'{self.share_class.lower()}_balance': 0.0,
            'total_equity': current_equity
        }
    else:
        # Simple staking positions
        return {
            'eth_balance': 0.0,
            f'{self.lst_type.lower()}_balance': allocation['stake_equity'],
            'eth_perpetual_short': allocation['hedge_equity'],
            f'{self.share_class.lower()}_balance': 0.0,
            'total_equity': current_equity
        }
```

### Configuration Updates

**USDT Market Neutral Config:**
- `share_class: "USDT"`
- `asset: "ETH"`
- `data_type: "defi"`
- `borrowing_enabled: true` (for leveraged staking)
- `lending_enabled: false`
- `staking_enabled: true`
- `basis_trade_enabled: false`
- `stake_allocation_percentage: 0.5` (50% for staking)
- `hedge_allocation: {binance: 0.4, bybit: 0.3, okx: 0.3}`

**USDT Market Neutral No Leverage Config:**
- `share_class: "USDT"`
- `asset: "ETH"`
- `data_type: "defi"`
- `borrowing_enabled: false`
- `lending_enabled: false`
- `staking_enabled: true`
- `basis_trade_enabled: false`
- `stake_allocation_percentage: 0.5` (50% for staking)
- `hedge_allocation: {binance: 0.4, bybit: 0.3, okx: 0.3}`

### Better Naming Conventions

**Current Names (Confusing):**
- `usdt_market_neutral_strategy.py` → **`usdt_eth_staking_hedged_strategy.py`**
- `usdt_market_neutral_no_leverage_strategy.py` → **`usdt_eth_staking_simple_hedged_strategy.py`**

**Alternative Naming Options:**
1. **By Strategy Type:**
   - `usdt_eth_leveraged_hedged_strategy.py`
   - `usdt_eth_simple_hedged_strategy.py`

2. **By Market Neutral Focus:**
   - `usdt_eth_market_neutral_leveraged_strategy.py`
   - `usdt_eth_market_neutral_simple_strategy.py`

3. **By Share Class + Asset:**
   - `usdt_eth_staking_hedged_leveraged_strategy.py`
   - `usdt_eth_staking_hedged_simple_strategy.py`

**Recommended Naming:**
- `usdt_eth_staking_hedged_leveraged_strategy.py`
- `usdt_eth_staking_hedged_simple_strategy.py`

This naming clearly indicates:
- Share class: USDT
- Asset: ETH
- Strategy: Staking + Hedged
- Type: Leveraged vs Simple

### Documentation Updates

**Update STRATEGY_MODES.md:**
- Document USDT share class strategies
- Explain stake allocation percentage logic
- Document hedge allocation across venues
- Clarify market neutral mechanics (staking + perp short)
- Update risk profiles (market neutral = reduced directional risk)
