# Pure Lending Strategy Specification Updates

**Generated**: October 13, 2025  
**Status**: ✅ UPDATES COMPLETE - Simplified and corrected specification

---

## 🎯 **Key Updates Made**

### **1. Centralized Risk Data**
- **Before**: `aave_health_factor` duplicated in both `market_data` and `risk_assessment`
- **After**: `aave_health_factor` only in `risk_assessment` (centralized from risk monitor)
- **Rationale**: Avoid double counting and ensure single source of truth

### **2. Simplified Input Data Requirements**
- **Removed**: `pnl_data` parameter (not required by MODES.md or WORKFLOW_GUIDE.md)
- **Removed**: `total_usdt_exposure` (redundant with `total_value_usd`)
- **Removed**: `liquidity_risk` and `concentration_risk` (invented parameters not in config/code)
- **Kept**: Essential data only - market rates, exposure data, and centralized risk assessment

### **3. Simplified Decision Triggers**
- **Before**: Complex triggers (capital change, yield optimization, liquidity management)
- **After**: Simple equity deviation trigger (primary) + risk management trigger
- **Rationale**: Pure lending strategy should rebalance based on equity changes, not complex optimization

### **4. Removed Reserve Ratio References**
- **Before**: 90-95% AAVE allocation with 5-10% liquidity reserve
- **After**: 100% AAVE allocation (pure lending strategy)
- **Rationale**: Pure lending means all capital should be lent, no reserves needed

### **5. Equity-Based Rebalancing**
- **Trigger**: Portfolio equity deviates from last rebalanced state by `position_deviation_threshold`
- **Default Threshold**: 2% (configurable per strategy)
- **Action**: Rebalance to 100% AAVE lending when equity changes significantly

---

## 📊 **Updated Specification Structure**

### **Input Data Requirements (Simplified)**
```python
{
    'market_data': {
        'aave_usdt_supply_rate': float,  # Current USDT supply rate on AAVE
        'aave_usdt_borrow_rate': float,  # Current USDT borrow rate on AAVE
        'usdt_price': float             # USDT price (should be ~1.0)
    },
    'exposure_data': {
        'total_value_usd': float,       # Total portfolio value in USD
        'usdt_balance': float,          # USDT balance in wallet
        'ausdt_balance': float          # aUSDT balance (lent on AAVE)
    },
    'risk_assessment': {
        'aave_health_factor': float     # AAVE protocol health (centralized from risk monitor)
    }
}
```

### **Decision Logic (Simplified)**
```python
def make_strategy_decision(self, timestamp, trigger_source, market_data, exposure_data, risk_assessment):
    # 1. Risk Assessment - Exit if AAVE health factor too low
    if risk_assessment['aave_health_factor'] < 1.5:
        return self._create_risk_exit_decision(timestamp, "AAVE health factor too low")
    
    # 2. Equity Deviation Check - Rebalance if equity changed significantly
    current_equity = exposure_data['total_value_usd']
    equity_deviation = self._calculate_equity_deviation(current_equity)
    
    if equity_deviation > self.config.get('position_deviation_threshold', 0.02):  # 2% default
        return self._create_rebalance_decision(timestamp, "Equity deviation detected", equity_deviation)
    
    # 3. Default: Maintain Current Position
    return self._create_maintain_decision(timestamp, "No action needed")
```

### **Position Targets (Simplified)**
- **AAVE Lending**: 100% of total equity
- **Wallet Liquidity**: 0% (pure lending strategy)
- **Target Yield**: Maximize AAVE USDT supply rate

---

## 🔧 **Configuration Updates**

### **Before (Complex)**
```yaml
decision_parameters:
  capital_change_threshold: 0.05  # 5%
  yield_optimization_threshold: 0.001  # 0.1%
  liquidity_reserve_ratio: 0.05  # 5%
  max_aave_allocation: 0.95  # 95%
risk_limits:
  min_aave_health_factor: 1.5
  min_liquidity_ratio: 0.05
  max_concentration_risk: 0.95
```

### **After (Simplified)**
```yaml
decision_parameters:
  position_deviation_threshold: 0.02  # 2% equity deviation threshold
risk_limits:
  min_aave_health_factor: 1.5
```

---

## 🎯 **Decision Triggers (Simplified)**

### **1. Equity Deviation Trigger (Primary)**
- **Trigger**: Portfolio equity deviates from last rebalanced state by `position_deviation_threshold`
- **Calculation**: `abs(current_equity - last_rebalanced_equity) / last_rebalanced_equity > position_deviation_threshold`
- **Default Threshold**: 2% (configurable per strategy)
- **Action**: Rebalance to optimal allocation (100% AAVE lending)

### **2. Risk Management Trigger**
- **AAVE Health Factor**: <1.5 triggers immediate exit to wallet
- **Source**: Centralized from risk monitor via `risk_assessment['aave_health_factor']`

---

## 🚀 **Benefits of Updates**

### **1. Simplified Architecture**
- **Fewer Parameters**: Removed invented parameters not in config/code
- **Clearer Logic**: Single trigger based on equity deviation
- **Centralized Data**: Single source of truth for risk data

### **2. Aligned with Design**
- **Pure Lending**: 100% allocation to AAVE (no reserves)
- **Equity-Based**: Rebalancing based on portfolio equity changes
- **Risk-First**: AAVE health factor as primary risk metric

### **3. Easier Implementation**
- **Fewer Dependencies**: No complex P&L data requirements
- **Clearer Logic**: Simple equity deviation calculation
- **Standardized**: Uses common `position_deviation_threshold` pattern

---

## 📋 **Patterns for Other Strategies**

### **Generic Patterns to Apply**
1. **Centralized Risk Data**: Get `aave_health_factor` from `risk_assessment` only
2. **Equity-Based Rebalancing**: Use `position_deviation_threshold` for all strategies
3. **Remove Reserve Ratios**: No reserve_ratio or reserve_balance references
4. **Remove Invented Parameters**: Only use parameters that exist in config/code
5. **Simplified Decision Logic**: Focus on equity deviation + risk management

### **Strategy-Specific Variations**
- **Pure Lending**: 100% AAVE allocation
- **BTC Basis**: Spot + perp positions based on equity
- **ETH Leveraged**: Staking + leverage based on equity
- **Market Neutral**: Balanced long/short positions based on equity

---

## ✅ **Updated Specification Status**

The Pure Lending Strategy specification is now:
- ✅ **Simplified**: Removed complex and invented parameters
- ✅ **Aligned**: Matches actual config and code structure
- ✅ **Centralized**: Single source of truth for risk data
- ✅ **Equity-Based**: Uses standard equity deviation rebalancing
- ✅ **Pure Lending**: 100% AAVE allocation (no reserves)

This specification can now serve as a clean template for implementing the Pure Lending Strategy and as a pattern for updating other strategy specifications.

---

**Status**: ✅ Pure Lending Strategy specification updated and simplified
