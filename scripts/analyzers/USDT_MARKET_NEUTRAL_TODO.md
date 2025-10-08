# USDT Market-Neutral Leveraged Restaking - Completion Guide

**Current Status:** Template complete, data loading working ✅  
**Remaining Work:** ~500 lines of implementation  
**Estimated Time:** 1-2 hours  
**File:** `scripts/analyzers/analyze_leveraged_restaking_USDT.py` (currently 281 lines)

---

## ✅ What's Already Done

### Infrastructure (Complete)
- ✅ Data loading (7 sources: AAVE rates, staking, spot, futures, funding, oracle, gas)
- ✅ Timezone handling (all UTC-aware)
- ✅ Configuration dataclass with multi-exchange support
- ✅ Event logging framework
- ✅ Main function with argument parsing
- ✅ File structure and imports

### Helper Methods (Complete)
- ✅ `_get_spot_price()` - ETH/USDT spot price lookup
- ✅ `_get_funding_rate()` - Binance funding rate lookup  
- ✅ `_get_gas_cost_usd()` - Gas costs in USD
- ✅ `_log_event()` - Event logging

### Reference Implementation Available
- ✅ Can copy from `analyze_leveraged_restaking_ETH.py` (1,191 lines)
- ✅ Base library available: `base_leveraged_restaking.py`

---

## 🔨 What Needs Implementation

### 1. Missing Helper Methods (~150 lines)

**Add these methods (copy/adapt from ETH version):**

```python
def _get_rates_at_timestamp(self, timestamp: pd.Timestamp) -> Dict[str, float]:
    """Get AAVE weETH supply and WETH borrow rates."""
    # Copy from analyze_leveraged_restaking_ETH.py lines 184-214
    # Returns: weeth_supply_growth_factor, weth_borrow_growth_factor, weeth_price

def _get_staking_yield_at_timestamp(self, timestamp: pd.Timestamp) -> Dict[str, float]:
    """Get staking yields (base + seasonal, filtered by eigen_only config)."""
    # Copy from analyze_leveraged_restaking_ETH.py lines 216-269
    # Returns: base_yield_hourly, seasonal_yield_hourly, etc.

def _get_bybit_funding_rate(self, timestamp: pd.Timestamp) -> float:
    """Get Bybit funding rate (need to load bybit data too!)."""
    # Similar to _get_funding_rate() but for bybit_funding data
    # NOTE: Need to add bybit funding data loading in _load_data()!
```

**Add to `_load_data()`:**
```python
# Load Bybit funding rates (missing!)
bybit_funding_file = self.data_dir / "market_data" / "derivatives" / "funding_rates" / "bybit_ETHUSDT_funding_rates_2024-01-01_2025-09-26.csv"
self.data['bybit_funding'] = pd.read_csv(bybit_funding_file)
self.data['bybit_funding']['timestamp'] = pd.to_datetime(self.data['bybit_funding']['funding_timestamp'], format='ISO8601', utc=True)
self.data['bybit_funding'] = self.data['bybit_funding'].set_index('timestamp').sort_index()
```

### 2. Leverage Loop Implementation (~100 lines)

**Add `_execute_leverage_loop_usd()` method:**

```python
def _execute_leverage_loop_usd(self, timestamp: pd.Timestamp, long_capital_usd: float, eth_price: float) -> Dict:
    """
    Execute leverage loop starting with USD.
    
    Steps:
    1. Convert USD to WETH: weth = long_capital_usd / eth_price
    2. Loop:
       a. Stake WETH → weETH (using oracle price)
       b. Supply weETH to AAVE
       c. Borrow WETH at 93% LTV
       d. Repeat until remaining < $10k
    3. Track gas costs in USD
    4. Return position details
    """
    
    # Reference: analyze_leveraged_restaking_ETH.py lines 293-440
    # Key differences:
    # - Track costs in USD (multiply gas_eth * eth_price)
    # - Loop condition: (available_weth * eth_price) >= self.config.min_position_usd
    # - Return net_position_usd instead of net_position_eth
    
    # Returns:
    return {
        'weeth_collateral': total_weeth_collateral,  # in weETH
        'weth_debt': total_weth_debt,                # in WETH
        'net_position_weth': collateral_value_weth - total_weth_debt,  # in WETH
        'net_position_usd': net_position_weth * eth_price,
        'long_eth_exposure': net_position_weth,  # For hedge sizing
        'health_factor': HF,
        'leverage_multiplier': leverage,
        'total_gas_costs_usd': total_gas,
        'venue_positions': {...}
    }
```

### 3. Perp Short Implementation (~80 lines)

**Add `_open_perp_shorts()` method:**

```python
def _open_perp_shorts(self, timestamp: pd.Timestamp, hedge_size_usd: float, eth_price: float) -> Dict:
    """
    Open short ETH perpetuals to hedge long exposure.
    
    Key sizing: hedge_size_usd should equal actual_long_eth_exposure * eth_price
    (Not initial allocation! Must match realized long position)
    """
    
    # Split across exchanges
    binance_notional = hedge_size_usd * self.config.binance_hedge_pct
    bybit_notional = hedge_size_usd * self.config.bybit_hedge_pct
    
    binance_eth_short = binance_notional / eth_price
    bybit_eth_short = bybit_notional / eth_price
    
    # Log events
    self._log_event(timestamp, 'TRADE_EXECUTED', 'BINANCE', 'ETH', binance_eth_short,
                   side='SHORT', notional_usd=binance_notional, instrument='ETHUSDT-PERP')
    
    # Returns:
    return {
        'binance': {'eth_short': X, 'notional_usd': Y, 'entry_price': eth_price},
        'bybit': {'eth_short': A, 'notional_usd': B, 'entry_price': eth_price},
        'total_eth_short': binance_eth_short + bybit_eth_short,
        'total_notional_usd': hedge_size_usd
    }
```

### 4. Funding Cost Tracking (~50 lines)

**Add `_calculate_funding_costs()` method:**

```python
def _calculate_funding_costs(self, timestamp: pd.Timestamp, short_positions: Dict) -> Dict:
    """
    Calculate funding costs (paid every 8 hours at 00:00, 08:00, 16:00 UTC).
    """
    
    hour = timestamp.hour
    if hour not in [0, 8, 16]:
        return {'total_funding_cost_usd': 0.0, 'binance_cost': 0.0, 'bybit_cost': 0.0}
    
    # Get rates
    binance_fr = self._get_funding_rate(timestamp)  # Binance
    bybit_fr = self._get_bybit_funding_rate(timestamp)  # Bybit (need to implement!)
    
    # Calculate costs (shorts PAY positive funding)
    binance_cost = short_positions['binance']['notional_usd'] * binance_fr
    bybit_cost = short_positions['bybit']['notional_usd'] * bybit_fr
    
    # Log funding payments
    if binance_cost != 0:
        self._log_event(timestamp, 'FUNDING_PAYMENT', 'BINANCE', 'USDT', binance_cost,
                       funding_rate=binance_fr)
    
    return {
        'total_funding_cost_usd': binance_cost + bybit_cost,
        'binance_cost': binance_cost,
        'bybit_cost': bybit_cost,
        'binance_rate': binance_fr,
        'bybit_rate': bybit_fr
    }
```

### 5. Main Analysis Loop (~200 lines)

**Update `run_analysis()` method (currently just a stub):**

```python
def run_analysis(self, start_date, end_date):
    # ... (initialization already done)
    
    # Execute leverage loop
    long_position = self._execute_leverage_loop_usd(t0, long_capital_usd, eth_price_spot)
    
    # CRITICAL: Size hedge to ACTUAL long exposure, not initial allocation!
    actual_long_eth = long_position['long_eth_exposure']
    actual_hedge_usd = actual_long_eth * eth_price_spot
    
    short_positions = self._open_perp_shorts(t0, actual_hedge_usd, eth_price_spot)
    
    # Verify market neutrality
    net_delta = actual_long_eth - short_positions['total_eth_short']
    # Should be ~0!
    
    # Hourly P&L tracking
    for timestamp in timestamps[1:]:
        # 1. Get current prices/rates
        eth_price = self._get_spot_price(timestamp)
        rates = self._get_rates_at_timestamp(timestamp)
        staking_yields = self._get_staking_yield_at_timestamp(timestamp)
        
        # 2. Calculate LONG side P&L (in WETH → USD)
        supply_pnl_weth = collateral_value * (supply_growth_factor - 1)
        seasonal_pnl_weth = collateral_value * seasonal_yield
        borrow_cost_weth = debt_value * (borrow_growth_factor - 1)
        price_change_pnl_weth = weeth_units * (new_price - old_price)
        
        long_pnl_usd = (supply + seasonal + price - borrow) * eth_price
        
        # 3. Calculate SHORT side costs
        funding_costs = self._calculate_funding_costs(timestamp, short_positions)
        
        # 4. NET P&L (should be market-neutral!)
        net_pnl_usd = long_pnl_usd - funding_costs['total']
        
        # 5. Update position balances
        weeth_collateral *= supply_growth_factor * (1 + seasonal_yield)
        weth_debt *= borrow_growth_factor
        
        # 6. Track cumul atives and record
        hourly_pnl.append({...})
    
    # Calculate metrics (APY, APR, Sharpe, etc.)
    # Save results
```

### 6. Save & Plot Methods (~100 lines)

**Add save_results() and create_plots():**

These can be directly copied from my previous implementation (lines 709-819 from the version I had).

Key plots needed:
1. Cumulative Net P&L (USD)
2. P&L Components (supply, seasonal, price, borrow, funding)
3. **Market Neutrality** (delta % over time) ← Critical!
4. Health Factor
5. ETH Price evolution
6. Long vs Short exposure (should track together)

---

## 📋 Step-by-Step Implementation Checklist

### Session Start

- [ ] 1. Read current `analyze_leveraged_restaking_USDT.py` file
- [ ] 2. Verify data loading works (test run with stub)

### Core Implementation

- [ ] 3. Add `_get_rates_at_timestamp()` (copy from ETH, lines 184-214)
- [ ] 4. Add `_get_staking_yield_at_timestamp()` (copy from ETH, lines 216-269)
- [ ] 5. Add Bybit funding data loading to `_load_data()`
- [ ] 6. Add `_get_bybit_funding_rate()` method
- [ ] 7. Implement `_execute_leverage_loop_usd()` (~100 lines)
- [ ] 8. Implement `_open_perp_shorts()` (~80 lines)
- [ ] 9. Implement `_calculate_funding_costs()` (~50 lines)
- [ ] 10. Complete `run_analysis()` with full hourly tracking (~200 lines)
- [ ] 11. Add `save_results()` method (~30 lines)
- [ ] 12. Add `create_plots()` method (6 panels, ~100 lines)

### Testing

- [ ] 13. Test 1-day run (verify no errors)
- [ ] 14. Check market neutrality (delta should be <5%)
- [ ] 15. Verify funding costs appear every 8 hours
- [ ] 16. Test full period (May 2024 - Sep 2025)
- [ ] 17. Verify output files created
- [ ] 18. Check visualizations

### Validation

- [ ] 19. Verify P&L components sum correctly
- [ ] 20. Check funding costs reasonable (~5-10% APR drag)
- [ ] 21. Compare vs ETH version (should be lower due to funding)
- [ ] 22. Market neutrality check (net delta near zero throughout)

---

## 🎯 Expected Results

### Hypothesis

**ETH Leveraged (Directional):**
- APR: 20.52%
- Exposure: Long 100 ETH

**USDT Market-Neutral (Hedged):**
- APR: ~10-15% (after funding costs)
- Exposure: ~0 ETH (market-neutral)
- Components:
  - Long yields: +20% (same as ETH)
  - Funding costs: -5 to -10% (8-hourly payments)
  - Net: ~10-15%

### Key Validation Checks

**1. Market Neutrality:**
```python
net_delta_eth = long_eth_exposure - total_eth_short
delta_pct = net_delta_eth / long_eth_exposure * 100

# Should be: abs(delta_pct) < 5%
# If >5%: Hedge sizing incorrect!
```

**2. Funding Cost Frequency:**
```python
# Count non-zero funding payments
funding_payments = len([x for x in hourly_pnl if x['funding_cost_usd'] != 0])

# Should be: ~total_hours / 8 (3 times per day)
# For 1.35 years: ~11,856 hours / 8 ≈ 1,482 funding payments
```

**3. P&L Attribution:**
```python
# All components should sum to net P&L
net_pnl = supply + seasonal + price - borrow - funding

# Verify:
assert abs(cumulative_net_pnl - sum(all_components)) < $1
```

---

## 📁 Code Snippets to Copy

### From analyze_leveraged_restaking_ETH.py

**Lines to Copy:**

1. **184-214**: `_get_rates_at_timestamp()` 
   - No changes needed
   
2. **216-269**: `_get_staking_yield_at_timestamp()`
   - Add `eigen_only` parameter check
   
3. **293-440**: `_execute_leverage_loop_at_t0()`
   - Adapt for USD:
     - Change: `initial_eth` → `long_capital_usd / eth_price`
     - Change: Loop condition to USD: `(available_weth * eth_price) >= min_position_usd`
     - Change: Gas costs to USD: `gas_eth * eth_price`
     - Add: Track `net_position_usd` in return dict

4. **442-545**: `_update_position_balances()`
   - Can use for hourly P&L if needed
   - Or inline the logic in run_analysis()

### New Code (Market-Neutral Specific)

**Perp Short Opening:**
```python
# Key: Size hedge to ACTUAL long exposure (after leverage)
# NOT to initial allocation!

actual_long_eth = long_position['long_eth_exposure']
hedge_size_usd = actual_long_eth * eth_price

short_positions = self._open_perp_shorts(t0, hedge_size_usd, eth_price)

# Verify:
net_delta = actual_long_eth - short_positions['total_eth_short']
# Should be ~0!
```

**Funding Cost Calculation:**
```python
# Only pay funding at 00:00, 08:00, 16:00 UTC
if timestamp.hour in [0, 8, 16]:
    binance_cost = binance_notional * binance_funding_rate
    bybit_cost = bybit_notional * bybit_funding_rate
    total_funding = binance_cost + bybit_cost
else:
    total_funding = 0.0
```

---

## 🐛 Known Issues to Avoid

### Issue 1: Delta Mismatch

**Problem:** If hedge is sized to initial allocation ($50k), but long position after leverage is different ($40k net), delta won't be neutral.

**Solution:**
```python
# ❌ WRONG:
hedge_size = initial_usdt * 0.5  # $50k

# ✅ CORRECT:
long_eth_exposure = leverage_loop_result['long_eth_exposure']
hedge_size = long_eth_exposure * eth_price  # Matches actual exposure!
```

### Issue 2: Timezone Mismatch

**Problem:** Funding rates have UTC timestamps, but search uses tz-naive.

**Solution:** Already fixed! Use `utc=True` in all pd.to_datetime() calls.

### Issue 3: Double-Counting Base Staking

**Problem:** Same as ETH version - base staking is in oracle price.

**Solution:** Already handled in `_get_staking_yield_at_timestamp()` - only add seasonal!

### Issue 4: Funding Frequency

**Problem:** Applying funding cost every hour instead of every 8 hours.

**Solution:**
```python
if timestamp.hour not in [0, 8, 16]:
    return 0.0  # No funding this hour
```

---

## 📊 Expected Output Files

### 1. Summary JSON
```json
{
  "config": {
    "initial_usdt": 100000,
    "allocation_long_pct": 0.5,
    "binance_hedge_pct": 0.5,
    "bybit_hedge_pct": 0.5
  },
  "initial_positions": {
    "long": {...},
    "short": {
      "binance": {"eth_short": 5.08, "notional": $20325},
      "bybit": {"eth_short": 5.08, "notional": $20325}
    },
    "net_delta_eth": 0.0,
    "delta_pct": 0.0
  },
  "summary": {
    "cumulative_supply_pnl_usd": 1200,
    "cumulative_seasonal_pnl_usd": 23000,
    "cumulative_price_change_pnl_usd": 45000,
    "cumulative_borrow_cost_usd": -42000,
    "cumulative_funding_cost_usd": -12000,
    "cumulative_net_pnl_usd": 15200,
    "apr": 15.2,
    "apy": 14.5
  }
}
```

### 2. Hourly P&L CSV (20+ columns)

**Key Columns:**
- Long side: `supply_pnl_usd`, `seasonal_pnl_usd`, `borrow_cost_usd`, `price_change_pnl_usd`
- Short side: `funding_cost_usd`, `binance_funding_cost_usd`, `bybit_funding_cost_usd`
- Net: `net_pnl_usd`, `cumulative_net_pnl_usd`
- Positions: `weeth_collateral`, `weth_debt`, `health_factor`
- Market neutrality: `long_eth_exposure`, `short_eth_exposure`, `net_delta_eth`, `delta_pct`

### 3. Event Log CSV

**Expected Events:**
- ~23 iterations × 3 gas fees = 69 gas fee events
- 23 stake deposits
- 23 collateral supplies  
- 23 loan creations
- 2 perp short opens (Binance + Bybit)
- ~1,482 funding payments (every 8 hours)
- **Total: ~1,600 events**

### 4. Analysis Plots (6 panels)

1. Cumulative Net P&L (USD)
2. P&L Components (stacked: supply, seasonal, price, -borrow, -funding)
3. **Market Neutrality** (delta % - should oscillate near 0%)
4. Health Factor (long side AAVE risk)
5. ETH Price (shows price moves don't affect P&L!)
6. Long vs Short Exposure (both lines should track together)

---

## 🎯 Success Criteria

### Must Pass:

✅ **Market Neutrality**: `abs(delta_pct) < 5%` throughout  
✅ **P&L Verification**: Components sum to net P&L  
✅ **Funding Frequency**: ~3 payments per day (8-hourly)  
✅ **Gas Costs**: Reasonable (~$200-300 for 23 iterations)  
✅ **Net APR**: 10-15% (long ~20%, funding ~-5 to -10%)  

### Comparison Targets:

| Strategy | APR | Funding Drag | Net APR | Market Exposure |
|----------|-----|--------------|---------|-----------------|
| ETH Directional | 20.52% | 0% | 20.52% | Long 100 ETH |
| **USDT Market-Neutral** | ~20% | -5 to -10% | **10-15%** | ~0 ETH |
| Ethena Benchmark | 11.78% | N/A | 11.78% | ~0 |

**Expected:** USDT market-neutral should be competitive with Ethena!

---

## 💡 Quick Start for Next Session

### Copy-Paste Approach (Fastest)

1. Open `analyze_leveraged_restaking_ETH.py` in one window
2. Open `analyze_leveraged_restaking_USDT.py` in another
3. Copy methods in this order:
   - `_get_rates_at_timestamp()` → paste as-is
   - `_get_staking_yield_at_timestamp()` → paste as-is  
   - `_execute_leverage_loop_at_t0()` → adapt for USD
   - Add perp methods (new code)
   - Complete `run_analysis()` (combine ETH loop + new perp logic)
   - Add save/plot methods

### Test Commands

```bash
# Quick test (1 day)
python scripts/analyzers/analyze_leveraged_restaking_USDT.py \
  --start-date 2024-05-12 \
  --end-date 2024-05-13 \
  --initial-usdt 100000 \
  --no-plots

# Full test (1.35 years)
python scripts/analyzers/analyze_leveraged_restaking_USDT.py \
  --start-date 2024-05-12 \
  --end-date 2025-09-18 \
  --initial-usdt 100000
```

---

## 📖 Reference Files

**Copy From:**
- `scripts/analyzers/analyze_leveraged_restaking_ETH.py` (lines 184-269, 293-440)

**Reference:**
- `scripts/analyzers/base_leveraged_restaking.py` (shared utilities)
- `IMPLEMENTATION_PLAN_USDT.md` (detailed specs)

**Data Files Confirmed Working:**
- ✅ Spot: `uniswapv3_WETHUSDT_1h_*.csv`
- ✅ Funding: `binance_ETHUSDT_funding_rates_*.csv`
- ✅ Bybit funding: `bybit_ETHUSDT_funding_rates_*.csv`
- ✅ All AAVE rates, staking, oracle (same as ETH)

---

**Current File State:**
- Lines: 281
- Status: Template with data loading ✅
- Next: Add 500 lines of implementation
- Time: 1-2 hours focused work

**All infrastructure is ready. Just need the implementation code!** 🚀
