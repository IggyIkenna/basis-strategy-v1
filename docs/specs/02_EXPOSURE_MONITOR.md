# Component Spec: Exposure Monitor 🎯

**Component**: Exposure Monitor  
**Responsibility**: Convert all balances to share class currency, calculate net delta  
**Priority**: ⭐⭐⭐ CRITICAL (Foundation for risk, P&L, strategy decisions)  
**Backend File**: `backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py`  
**Last Reviewed**: October 8, 2025  
**Status**: ✅ Aligned with canonical sources (.cursor/tasks/ + MODES.md)

---

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [CANONICAL_ARCHITECTURAL_PRINCIPLES.md](../CANONICAL_ARCHITECTURAL_PRINCIPLES.md) - Consolidated from all .cursor/tasks/
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Task Specifications**: `.cursor/tasks/` - Individual task specifications

---

## 🎯 **Purpose**

Aggregate exposure across all venues in share class currency.

**Key Principles**:
- **Converts**: Token balances → ETH or USD (share class dependent)
- **AAVE conversion chain**: aWeETH → underlying weETH → ETH → USD (via indices + oracle)
- **Net delta calculation**: Sum all long ETH - sum all short ETH
- **Share class aware**: ETH share class = ETH units, USDT share class = USD units

**Data Flow Integration**:
- **Input**: Receives `position_snapshot` and `market_data` as parameters
- **Method**: `calculate_exposure(timestamp, position_snapshot=None, market_data=None)`
- **No Direct Dependencies**: Doesn't hold DataProvider or PositionMonitor references
- **Data Source**: Market data passed from EventDrivenStrategyEngine via `_process_timestamp()`

**Critical**: This is where AAVE index mechanics happen! (From PNL_RECONCILIATION.md)

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
    
    def __init__(self, share_class: str, position_monitor, data_provider):
        self.share_class = share_class
        self.position_monitor = position_monitor
        self.data_provider = data_provider
    
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
- Position Monitor updates (via Redis `position:updated` channel)

### **Uses Data From**:
- **Position Monitor** ← Raw balances
- **Data Provider** ← Prices, indices, oracles

### **Publishes To**:
- **Risk Monitor** ← Exposure data
- **P&L Calculator** ← Exposure data
- **Strategy Manager** ← Exposure data

### **Redis Pub/Sub**:

**Subscribes**:
- `position:updated` → Triggers recalculation

**Publishes**:
- `exposure:calculated` (channel) → Notifies downstream
- `exposure:current` (key) → Latest exposure data

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

## 🎯 **Success Criteria**

- [ ] Correct AAVE index conversions (scaled → underlying)
- [ ] Net delta calculation accurate
- [ ] Per-exchange perp prices used
- [ ] Share class value in correct currency
- [ ] Total value includes all venues
- [ ] Gas debt handled correctly (negative ETH)
- [ ] USDT as short ETH exposure
- [ ] Triggered by every position update
- [ ] Publishes to downstream components
- [ ] Balance sheet data available for plotting (wallet, CEX, AAVE positions)

---

**Status**: Specification complete! ✅


