# AAVE Conversion Mechanics Technical Guide

**Date**: October 11, 2025  
**Purpose**: Technical guide for AAVE token conversion mechanics, index calculations, and exposure conversion chains  
**Status**: ⭐ **TECHNICAL REFERENCE** - Essential for understanding AAVE token mechanics

---

## Overview

This guide explains the critical AAVE token conversion mechanics that are essential for accurate exposure calculations. Understanding these mechanics is crucial for proper balance tracking, P&L calculation, and health factor calculations.

## 🔑 **Why This is Essential**

**User's Clarification**: *"aWeETH amount depends on liquidity index at time of supply"*

**This affects EVERYTHING**:
- Balance tracking (wallet.aWeETH is scaled, not 1:1)
- P&L calculation (growth from index + oracle)
- Health factor (uses underlying, not scaled)

**All Three Statements Are True**:
1. **aWeETH is CONSTANT** after supply (never changes)
2. **aWeETH amount depends on liquidity index at time of supply** (initial calculation)
3. **Our data uses normalized indices** (~1.0, not 1e27)

## The Conversion Chain ⛓️

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

## Why Indices Are NOT 1:1 🔴

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

## AAVE Index Mechanics

### Liquidity Index Growth

The AAVE liquidity index grows over time as users earn supply yield:

```python
# Initial supply
supply_amount = 100.0 weETH
initial_liquidity_index = 1.05
aweeth_received = supply_amount / initial_liquidity_index
# = 100.0 / 1.05 = 95.24 aWeETH

# After 1 year (index grew to 1.10 from 5% APY)
current_liquidity_index = 1.10
weeth_redeemable = aweeth_received × current_liquidity_index
# = 95.24 × 1.10 = 104.76 weETH

# Yield earned = 104.76 - 100.0 = 4.76 weETH (4.76% yield)
```

### Borrow Index Growth

Similar mechanics apply to debt tokens:

```python
# Initial borrow
borrow_amount = 50.0 WETH
initial_borrow_index = 1.02
debt_received = borrow_amount / initial_borrow_index
# = 50.0 / 1.02 = 49.02 variableDebtWETH

# After 1 year (index grew to 1.08 from 6% APY)
current_borrow_index = 1.08
weth_owed = debt_received × current_borrow_index
# = 49.02 × 1.08 = 52.94 WETH

# Interest accrued = 52.94 - 50.0 = 2.94 WETH (5.88% interest)
```

## Conversion Formulas

### Collateral Token Conversion

```python
def convert_aave_collateral_to_underlying(
    scaled_balance: float,
    liquidity_index: float
) -> float:
    """
    Convert AAVE collateral token to underlying asset.
    
    Args:
        scaled_balance: ERC-20 token balance (constant)
        liquidity_index: Current AAVE liquidity index (grows over time)
    
    Returns:
        Underlying asset amount (grows with yield)
    """
    return scaled_balance × liquidity_index

def convert_underlying_to_eth(
    underlying_balance: float,
    oracle_price: float
) -> float:
    """
    Convert underlying asset to ETH equivalent.
    
    Args:
        underlying_balance: Underlying asset amount
        oracle_price: Oracle price (grows with staking yield)
    
    Returns:
        ETH equivalent amount
    """
    return underlying_balance × oracle_price

def convert_eth_to_usd(
    eth_amount: float,
    eth_usd_price: float
) -> float:
    """
    Convert ETH to USD.
    
    Args:
        eth_amount: ETH amount
        eth_usd_price: Current ETH/USD price
    
    Returns:
        USD equivalent amount
    """
    return eth_amount × eth_usd_price
```

### Debt Token Conversion

```python
def convert_aave_debt_to_underlying(
    scaled_debt: float,
    borrow_index: float
) -> float:
    """
    Convert AAVE debt token to underlying debt.
    
    Args:
        scaled_debt: ERC-20 debt token balance (constant)
        borrow_index: Current AAVE borrow index (grows over time)
    
    Returns:
        Underlying debt amount (grows with interest)
    """
    return scaled_debt × borrow_index
```

## Complete Conversion Chain Example

### aWeETH → USD Conversion

```python
def calculate_aweeth_exposure(
    aweeth_scaled: float,
    liquidity_index: float,
    oracle_price: float,
    eth_usd_price: float
) -> Dict[str, float]:
    """
    Complete aWeETH to USD conversion chain.
    
    Returns all intermediate values for debugging.
    """
    # Step 1: Scaled → Underlying
    weeth_underlying = aweeth_scaled × liquidity_index
    
    # Step 2: Underlying → ETH
    weeth_in_eth = weeth_underlying × oracle_price
    
    # Step 3: ETH → USD
    weeth_in_usd = weeth_in_eth × eth_usd_price
    
    return {
        'scaled_balance': aweeth_scaled,      # What wallet shows (CONSTANT)
        'underlying_balance': weeth_underlying,  # What AAVE sees (GROWS)
        'eth_equivalent': weeth_in_eth,       # For delta tracking
        'usd_equivalent': weeth_in_usd,       # For P&L (USDT modes)
        
        # Conversion details (for debugging)
        'liquidity_index': liquidity_index,
        'oracle_price': oracle_price,
        'eth_usd_price': eth_usd_price,
        'conversion_chain': f'{aweeth_scaled:.2f} aWeETH → {weeth_underlying:.2f} weETH → {weeth_in_eth:.2f} ETH → ${weeth_in_usd:,.2f}'
    }
```

### variableDebtWETH → USD Conversion

```python
def calculate_debt_exposure(
    debt_scaled: float,
    borrow_index: float,
    eth_usd_price: float
) -> Dict[str, float]:
    """
    Complete variableDebtWETH to USD conversion chain.
    """
    # Step 1: Scaled → Underlying
    weth_debt_underlying = debt_scaled × borrow_index
    
    # Step 2: WETH = ETH (1:1)
    debt_in_eth = weth_debt_underlying
    
    # Step 3: ETH → USD
    debt_in_usd = debt_in_eth × eth_usd_price
    
    return {
        'scaled_debt': debt_scaled,           # variableDebtWETH (CONSTANT)
        'underlying_debt': weth_debt_underlying,  # WETH owed (GROWS)
        'eth_equivalent': debt_in_eth,        # For delta (negative contribution)
        'usd_equivalent': debt_in_usd,        # For P&L
        
        # Conversion details
        'borrow_index': borrow_index,
        'eth_usd_price': eth_usd_price
    }
```

## Health Factor Calculation

Health factor uses underlying balances, not scaled balances:

```python
def calculate_health_factor(
    collateral_underlying: float,
    debt_underlying: float,
    liquidation_threshold: float
) -> float:
    """
    Calculate AAVE health factor using underlying balances.
    
    Args:
        collateral_underlying: Total underlying collateral value
        debt_underlying: Total underlying debt value
        liquidation_threshold: AAVE liquidation threshold
    
    Returns:
        Health factor (HF < 1.0 triggers liquidation)
    """
    if debt_underlying == 0:
        return float('inf')  # No debt = infinite health factor
    
    return (collateral_underlying × liquidation_threshold) / debt_underlying
```

## Common Mistakes to Avoid

### Mistake 1: Assuming 1:1 AAVE Conversion
```python
# ❌ WRONG!
aweeth = weeth_supplied  # Assumes 1:1

# ✅ CORRECT!
aweeth = weeth_supplied / current_liquidity_index
```

### Mistake 2: Using Scaled Balance for Value
```python
# ❌ WRONG!
collateral_value = wallet.aWeETH × oracle_price  # Uses scaled!

# ✅ CORRECT!
underlying = wallet.aWeETH × liquidity_index  # Get underlying first
collateral_value = underlying × oracle_price  # Then multiply oracle
```

### Mistake 3: Using Scaled Balance for Health Factor
```python
# ❌ WRONG!
health_factor = (wallet.aWeETH × liquidation_threshold) / wallet.variableDebtWETH

# ✅ CORRECT!
collateral_underlying = wallet.aWeETH × liquidity_index
debt_underlying = wallet.variableDebtWETH × borrow_index
health_factor = (collateral_underlying × liquidation_threshold) / debt_underlying
```

## Data Structure Requirements

### Required Market Data
```python
market_data = {
    'protocol_data': {
        'aave_indexes': {
            'aWeETH': 1.10,           # Liquidity index (grows with yield)
            'variableDebtWETH': 1.08  # Borrow index (grows with interest)
        },
        'oracle_prices': {
            'weETH': 1.0256           # Oracle price (grows with staking)
        }
    },
    'market_data': {
        'prices': {
            'ETH': 3305.20            # ETH/USD price
        }
    }
}
```

### Position Snapshot Structure
```python
position_snapshot = {
    'wallet': {
        'aWeETH': 95.24,              # Scaled balance (constant)
        'variableDebtWETH': 49.02     # Scaled debt (constant)
    }
}
```

## Testing Examples

### Test Case 1: Initial Supply
```python
def test_initial_supply():
    """Test initial AAVE supply conversion"""
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
```

### Test Case 2: Complete Conversion Chain
```python
def test_complete_conversion_chain():
    """Test complete aWeETH → USD conversion"""
    aweeth_scaled = 95.24
    liquidity_index = 1.10
    oracle_price = 1.0256
    eth_usd_price = 3305.20
    
    result = calculate_aweeth_exposure(
        aweeth_scaled, liquidity_index, oracle_price, eth_usd_price
    )
    
    assert result['scaled_balance'] == 95.24
    assert result['underlying_balance'] == pytest.approx(104.76, abs=0.01)
    assert result['eth_equivalent'] == pytest.approx(107.44, abs=0.01)
    assert result['usd_equivalent'] == pytest.approx(355092, abs=100)
```

## Integration with Exposure Monitor

This technical guide is referenced by the Exposure Monitor specification for:

1. **Asset Conversion Logic**: How to convert AAVE tokens to underlying assets
2. **Exposure Calculation**: Using underlying balances for accurate exposure
3. **Health Factor Calculation**: Using underlying balances for risk assessment
4. **P&L Attribution**: Tracking yield from index growth

**Cross-Reference**: See [Exposure Monitor Specification](specs/02_EXPOSURE_MONITOR.md) for implementation details.

---

**Status**: ⭐ **TECHNICAL REFERENCE** - Essential for AAVE token mechanics understanding
