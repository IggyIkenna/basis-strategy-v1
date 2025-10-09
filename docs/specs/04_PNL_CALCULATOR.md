# Component Spec: P&L Calculator 💰

**Component**: P&L Calculator  
**Responsibility**: Calculate balance-based & attribution P&L with reconciliation  
**Priority**: ⭐⭐⭐ CRITICAL (Core performance metric)  
**Backend File**: `backend/src/basis_strategy_v1/core/math/pnl_calculator.py`  
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

Calculate P&L using two methods and reconcile them.

**Key Principles**:
- **Balance-Based P&L** = Source of truth (actual portfolio value change)
- **Attribution P&L** = Breakdown by component (where P&L comes from)
- **Reconciliation** = Validate balance vs attribution (should match within tolerance)
- **Share class aware** = ETH vs USDT reporting

**Data Flow Integration**:
- **Input**: Receives `current_exposure` and `previous_exposure` as parameters
- **Method**: `calculate_pnl(current_exposure, previous_exposure=None, timestamp=None, period_start=None)`
- **State Management**: Saves own previous P&L state internally
- **No External Dependencies**: Only needs exposure data, no market data or other components

**From**: PNL_RECONCILIATION.md (complete incorporation)

---

## 💡 **Two P&L Calculation Methods**

### **Method 1: Balance-Based P&L** (Source of Truth) ✅

**Concept**: Total value at end - total value at start

**Why Source of Truth**:
- Reflects ACTUAL portfolio value change
- Includes ALL effects (known and unknown)
- Can't miss any P&L source
- Simple and verifiable

**Formula**:
```python
balance_pnl = final_total_value - initial_total_value
```

### **Method 2: Attribution P&L** (Breakdown) 📊

**Concept**: Sum all known P&L components

**Why Important**:
- Shows WHERE P&L comes from
- Helps optimize strategy
- Validates calculations
- Debugging tool

**Formula** (components are signed):
```python
attribution_pnl = (
    supply_yield +              # Positive (AAVE supply interest)
    staking_yield_oracle +      # Positive (oracle price drift - weETH/ETH grows ~2.8% APR)
    staking_yield_rewards +     # Positive (seasonal rewards - EIGEN weekly, ETHFI airdrops)
    borrow_costs +              # Negative (AAVE debt interest)
    funding_pnl +               # ± (perp funding rates)
    delta_pnl +                 # ± (unhedged exposure)
    transaction_costs           # Negative (gas + execution)
)

# Note: Staking yield split into:
# - staking_yield_oracle: Continuous (non-rebasing token appreciation)
# - staking_yield_rewards: Discrete (seasonal airdrops)
```

### **Reconciliation**: They Should Match!

**Tolerance**: 2% of initial capital (annualized)

```python
tolerance = initial_capital × 0.02 × (period_months / 12)

# Example: 1 month on $100k
# Tolerance = $100,000 × 0.02 × (1/12) = $166.67

if abs(balance_pnl - attribution_pnl) <= tolerance:
    status = "✅ RECONCILIATION PASSED"
else:
    status = "⚠️ RECONCILIATION GAP - Investigate"
```

---

## 📊 **Data Structures**

### **Input**: Exposure Data (current & previous)

```python
{
    'current_exposure': {...},   # From Exposure Monitor (current hour)
    'previous_exposure': {...},  # From previous hour
    'timestamp': timestamp
}
```

### **Output**: P&L Data

```python
{
    'timestamp': timestamp,
    'share_class': 'USDT',  # or 'ETH'
    
    # Balance-Based P&L (source of truth)
    'balance_based': {
        'total_value_current': 99753.45,
        'total_value_previous': 99507.12,
        'pnl_hourly': 246.33,              # This hour
        'pnl_cumulative': 1238.45,         # Since start
        'pnl_pct': 1.238,                  # % of initial capital
    },
    
    # Attribution P&L (breakdown)
    'attribution': {
        # Hourly components
        'supply_pnl': 12.34,
        'staking_pnl': 0.0,  # Only for seasonal (base in price appreciation)
        'price_change_pnl': 8.56,
        'borrow_cost': -5.23,
        'funding_pnl': 2.15,
        'delta_pnl': 0.45,
        'transaction_costs': 0.0,  # Only at t=0
        'pnl_hourly': 18.27,
        
        # Cumulative components
        'cumulative_supply_pnl': 543.21,
        'cumulative_staking_pnl': 0.0,
        'cumulative_price_change_pnl': 382.45,
        'cumulative_borrow_cost': -234.56,
        'cumulative_funding_pnl': 892.45,
        'cumulative_delta_pnl': 12.34,
        'cumulative_transaction_costs': -246.05,
        'pnl_cumulative': 1349.84
    },
    
    # Reconciliation
    'reconciliation': {
        'balance_pnl': 1238.45,
        'attribution_pnl': 1349.84,
        'difference': -111.39,
        'unexplained_pnl': -111.39,  # Same as difference (residual)
        'tolerance': 166.67,  # 2% annualized for 1 month
        'passed': True,  # |diff| <= tolerance
        'diff_pct_of_capital': -0.111,  # -0.111%
        
        # Potential sources of unexplained P&L
        'potential_sources': {
            'spread_basis_pnl': 'Spot-perp spread changes not explicitly tracked',
            'seasonal_rewards_unsold': 'EIGEN/ETHFI tokens received but not sold to USD',
            'funding_notional_drift': 'Funding on entry notional vs current exposure',
            'yield_calc_approximations': 'Hourly accrual vs actual discrete payments'
        }
    }
}
```

---

## 💻 **Core Functions**

```python
class PnLCalculator:
    """Calculate P&L using balance-based and attribution methods."""
    
    def __init__(self, share_class, initial_capital):
        self.share_class = share_class
        self.initial_capital = initial_capital
        
        # Track cumulative attribution components
        self.cumulative = {
            'supply_pnl': 0.0,
            'staking_yield_oracle': 0.0,    # Oracle price drift (weETH/ETH appreciation)
            'staking_yield_rewards': 0.0,   # Seasonal rewards (EIGEN + ETHFI)
            'borrow_cost': 0.0,
            'funding_pnl': 0.0,
            'delta_pnl': 0.0,
            'transaction_costs': 0.0
        }
        
        # Initial value (set at t=0)
        self.initial_total_value = None
        
        # Redis
        self.redis = redis.Redis()
        self.redis.subscribe('risk:calculated', self._on_risk_update)
    
    async def calculate_pnl(
        self,
        current_exposure: Dict,
        previous_exposure: Optional[Dict],
        timestamp: pd.Timestamp,
        period_start: pd.Timestamp
    ) -> Dict:
        """
        Calculate both P&L methods and reconcile.
        
        Triggered by: Risk Monitor updates (sequential chain)
        """
        # Set initial value if first calculation
        if self.initial_total_value is None:
            self.initial_total_value = current_exposure['total_value_usd']
        
        # 1. Balance-Based P&L (source of truth)
        balance_pnl_data = self._calculate_balance_based_pnl(
            current_exposure,
            period_start,
            timestamp
        )
        
        # 2. Attribution P&L (breakdown)
        attribution_pnl_data = self._calculate_attribution_pnl(
            current_exposure,
            previous_exposure,
            timestamp
        )
        
        # 3. Reconciliation
        reconciliation = self._reconcile_pnl(
            balance_pnl_data,
            attribution_pnl_data,
            period_start,
            timestamp
        )
        
        # Combine results
        pnl_data = {
            'timestamp': timestamp,
            'share_class': self.share_class,
            'balance_based': balance_pnl_data,
            'attribution': attribution_pnl_data,
            'reconciliation': reconciliation
        }
        
        # Publish to Redis
        await self.redis.set('pnl:current', json.dumps(pnl_data))
        await self.redis.publish('pnl:calculated', json.dumps({
            'timestamp': timestamp.isoformat(),
            'pnl_cumulative': balance_pnl_data['pnl_cumulative'],
            'reconciliation_passed': reconciliation['passed']
        }))
        
        return pnl_data
    
    def _calculate_balance_based_pnl(
        self,
        current_exposure: Dict,
        period_start: pd.Timestamp,
        current_time: pd.Timestamp
    ) -> Dict:
        """Calculate P&L from portfolio value change."""
        current_value = current_exposure['share_class_value']
        pnl_cumulative = current_value - self.initial_total_value
        
        return {
            'total_value_current': current_value,
            'total_value_initial': self.initial_total_value,
            'pnl_cumulative': pnl_cumulative,
            'pnl_pct': (pnl_cumulative / self.initial_capital) * 100
        }
    
    def _calculate_attribution_pnl(
        self,
        current_exposure: Dict,
        previous_exposure: Optional[Dict],
        timestamp: pd.Timestamp
    ) -> Dict:
        """Calculate P&L from component breakdown."""
        if previous_exposure is None:
            # First hour, no P&L yet
            return self._zero_attribution()
        
        # Calculate hourly P&L components
        # (This logic comes from analyzers - validated!)
        
        # Supply yield (AAVE supply index growth)
        supply_pnl = self._calc_supply_pnl(current_exposure, previous_exposure)
        
        # Staking rewards (seasonal only - base in price appreciation)
        staking_pnl = self._calc_staking_pnl(current_exposure, previous_exposure)
        
        # Price appreciation (oracle price changes)
        price_change_pnl = self._calc_price_change_pnl(current_exposure, previous_exposure)
        
        # Borrow costs (AAVE debt index growth)
        borrow_cost = self._calc_borrow_cost(current_exposure, previous_exposure)
        
        # Funding P&L (perp funding rates - only at 0/8/16 UTC)
        funding_pnl = self._calc_funding_pnl(current_exposure, timestamp)
        
        # Delta P&L (unhedged exposure × price change)
        delta_pnl = self._calc_delta_pnl(current_exposure, previous_exposure)
        
        # Transaction costs (only at t=0)
        transaction_costs = 0.0  # Handled separately
        
        # Update cumulatives
        self.cumulative['supply_pnl'] += supply_pnl
        self.cumulative['staking_pnl'] += staking_pnl
        self.cumulative['price_change_pnl'] += price_change_pnl
        self.cumulative['borrow_cost'] += borrow_cost
        self.cumulative['funding_pnl'] += funding_pnl
        self.cumulative['delta_pnl'] += delta_pnl
        
        return {
            # Hourly
            'supply_pnl': supply_pnl,
            'staking_pnl': staking_pnl,
            'price_change_pnl': price_change_pnl,
            'borrow_cost': borrow_cost,
            'funding_pnl': funding_pnl,
            'delta_pnl': delta_pnl,
            'transaction_costs': transaction_costs,
            'pnl_hourly': sum([supply_pnl, staking_pnl, price_change_pnl, borrow_cost, funding_pnl, delta_pnl]),
            
            # Cumulative
            **{f'cumulative_{k}': v for k, v in self.cumulative.items()},
            'pnl_cumulative': sum(self.cumulative.values())
        }
    
    def _reconcile_pnl(
        self,
        balance_data: Dict,
        attribution_data: Dict,
        period_start: pd.Timestamp,
        current_time: pd.Timestamp
    ) -> Dict:
        """Reconcile balance vs attribution P&L."""
        balance_pnl = balance_data['pnl_cumulative']
        attribution_pnl = attribution_data['pnl_cumulative']
        diff = balance_pnl - attribution_pnl
        
        # Calculate tolerance (2% annualized, pro-rated)
        period_months = (current_time - period_start).days / 30.44
        tolerance = self.initial_capital * 0.02 * (period_months / 12)
        
        passed = abs(diff) <= tolerance
        
        return {
            'balance_pnl': balance_pnl,
            'attribution_pnl': attribution_pnl,
            'difference': diff,
            'tolerance': tolerance,
            'passed': passed,
            'diff_pct_of_capital': (diff / self.initial_capital) * 100
        }
```

---

## 📊 **Mode-Specific P&L Components**

### **Pure USDT Lending** (Simplest)

```python
# Balance-Based
balance_pnl = final_aave_usdt - initial_capital

# Attribution
attribution_pnl = (
    cumulative_supply_yield +
    cumulative_transaction_costs
)
```

### **BTC Basis** (Market-Neutral)

```python
# Balance-Based
balance_pnl = (final_cex_balance + final_btc_spot_value) - initial_capital

# Attribution
attribution_pnl = (
    cumulative_funding_pnl +
    cumulative_delta_pnl +
    cumulative_transaction_costs
)
```

### **ETH Leveraged** (ETH Share Class)

```python
# Balance-Based (in ETH)
balance_pnl_eth = (final_aave_collateral - final_aave_debt - gas_paid) - initial_eth

# Attribution (in ETH)
attribution_pnl_eth = (
    cumulative_supply_pnl_eth +
    cumulative_staking_pnl_eth +      # Base + EIGEN + seasonal
    cumulative_price_change_pnl_eth +
    cumulative_borrow_costs_eth +
    cumulative_transaction_costs_eth
)
```

### **USDT Market-Neutral** (Most Complex)

```python
# Balance-Based (in USD)
balance_pnl_usd = (
    sum(final_cex_balances) +
    final_aave_collateral_usd -
    final_aave_debt_usd -
    final_gas_debt_usd
) - initial_total_value_usd

# Attribution (in USD)
attribution_pnl_usd = (
    cumulative_supply_pnl +
    cumulative_price_change_pnl +
    cumulative_borrow_costs +
    cumulative_funding_pnl +
    cumulative_delta_pnl +
    cumulative_transaction_costs
)
```

---

## 🔍 **Common Reconciliation Issues**

### **Issue 1: Seasonal Rewards Not Sold**

**Problem**: Attribution includes seasonal rewards, but tokens not converted to USD yet

**Example**:
```python
# Attribution includes
cumulative_eigen_rewards = $500  # EIGEN tokens received
cumulative_ethfi_rewards = $200  # ETHFI tokens received

# But balance doesn't show USD
# Wallet shows: 15 EIGEN + 8 ETHFI (not sold!)

# Gap: ~$700
```

**Solution**:
1. Quick fix: Remove seasonal from attribution
2. Long-term: Track token balances, simulate auto-sell

### **Issue 2: Funding on Wrong Notional**

**Problem**: Funding calculated on fixed entry notional, but exposure changes

**Solution**: Use current mark price for exposure
```python
funding_pnl = (eth_short × current_mark_price) × funding_rate
# Not: (eth_short × entry_price) × funding_rate
```

### **Issue 3: Missing Balance Components**

**Common mistakes**:
- Forgetting gas debt
- Forgetting free wallet balances
- Double-counting CEX balances
- Wrong AAVE index conversions

---

## 🧪 **Testing**

```python
def test_balance_based_pnl():
    """Test balance-based P&L calculation."""
    calculator = PnLCalculator('USDT', 100000)
    
    # Set initial
    calculator.initial_total_value = 99753.45  # After entry costs
    
    # Calculate after 1 month
    current_exposure = {'share_class_value': 100992.28}
    
    pnl_data = calculator._calculate_balance_based_pnl(current_exposure, ...)
    
    # P&L = 100992.28 - 99753.45 = 1238.83
    assert pnl_data['pnl_cumulative'] == pytest.approx(1238.83, abs=1.0)

def test_reconciliation():
    """Test reconciliation within tolerance."""
    calculator = PnLCalculator('USDT', 100000)
    
    balance_data = {'pnl_cumulative': 1238.83}
    attribution_data = {'pnl_cumulative': 1200.15}
    
    # 1 month period
    period_start = pd.Timestamp('2024-05-12', tz='UTC')
    current_time = pd.Timestamp('2024-06-12', tz='UTC')
    
    reconciliation = calculator._reconcile_pnl(
        balance_data, attribution_data, period_start, current_time
    )
    
    # Diff = 38.68
    # Tolerance = 100000 × 0.02 × (1/12) = 166.67
    # Should pass
    assert reconciliation['passed'] == True
    assert abs(reconciliation['difference']) < reconciliation['tolerance']
```

---

## 🔗 **Integration**

### **Triggered By**:
- Risk Monitor updates (sequential chain: position → exposure → risk → pnl)

### **Uses Data From**:
- **Exposure Monitor** ← Current & previous exposure
- **Config** ← Initial capital, period dates

### **Publishes To**:
- **Results** ← P&L data for API response
- **Event Logger** ← P&L snapshots (hourly)

### **Redis**:

**Subscribes**:
- `risk:calculated` → Triggers P&L calculation (after risk calculation)

**Publishes**:
- `pnl:calculated` (channel)
- `pnl:current` (key)

---

## 🎯 **Success Criteria**

- [ ] Balance-based P&L calculated correctly
- [ ] Attribution P&L breaks down all sources
- [ ] Reconciliation validates within tolerance
- [ ] Mode-specific component tracking
- [ ] Share class aware (ETH vs USD)
- [ ] Handles all edge cases (no AAVE, no CEX, etc.)
- [ ] Logs reconciliation failures for debugging
- [ ] Cumulative tracking accurate

---

**Status**: Specification complete! ✅

*Note: Full PNL_RECONCILIATION.md content incorporated. That file can now be deleted.*


