# KING Token Handling Guide 👑

**Purpose**: Guide for handling KING token rewards from EtherFi restaking  
**Status**: ✅ IMPLEMENTED - KING token handling fully functional  
**Updated**: October 5, 2025  
**Last Reviewed**: October 8, 2025  
**Status**: ✅ Aligned with canonical sources (.cursor/tasks/ + MODES.md)

---

## ✅ **Implementation Status**

**KING Token Handling**: ✅ **FULLY IMPLEMENTED**
- StrategyManager.handle_king_token_management() - Detects KING balance and triggers unwrapping
- OnChainExecutionManager.unwrap_and_sell_king_tokens() - Executes unwrapping and selling
- EventLogger.log_seasonal_reward_distribution() - Logs reward events
- Seasonal rewards data loading from CSV files
- Comprehensive unit tests for all KING handling components

## 🎯 **Overview**

The BASIS strategy system handles KING token rewards from EtherFi restaking (weETH only). KING tokens are distributed periodically and need to be unwrapped into EIGEN and/or ETHFI tokens, then sold for USDT on Binance.

---

## 📊 **KING Token Distribution**

### **Source Data**
- **File**: `data/protocol_data/staking/restaking_final/etherfi_seasonal_rewards_2024-01-01_2025-09-18.csv`
- **Columns**: `period_start`, `period_end`, `payout_date`, `period_days`, `reward_type`, `event_name`, `eigen_per_eeth_weekly`, `eigen_price_usd`, `eth_price_usd`, `weekly_reward_eth`, `daily_yield_pct`, `daily_yield_conservative`, `daily_yield_aggressive`, `daily_yield_final`, `distribution_mechanism`, `data_source`, `data_quality`, `defillama_reward_apy`, `ethfi_per_eeth`, `ethfi_price_usd`, `distribution_eth`

### **Distribution Mechanism**
- **Protocol**: EtherFi KING Protocol (formerly LRT²)
- **Token**: KING tokens distributed to ERC-20 wallet  
- **Frequency**: Weekly distributions + ad-hoc ETHFI top-ups
- **Composition**: EIGEN + ETHFI tokens wrapped in KING (dollar-equivalent value)
- **Official Documentation**: [EtherFi GitBook - KING Rewards Distribution](https://etherfi.gitbook.io/etherfi/king-protocol-formerly-lrt/king-rewards-distribution)

### **How KING Unwrapping Works** (from EtherFi GitBook):

**Important**: When you unwrap KING tokens, you receive **EIGEN + ETHFI of the same dollar value**, not just EIGEN.

**Example from EtherFi**:
1. If KING vault holds 10 EIGEN ($1 each) + 10 ETHFI ($1 each) = $20 total
2. Vault has 10 shares → each share worth $2
3. Unwrapping 1 KING share gives you: 1 EIGEN + 1 ETHFI = $2 total value

**After New EIGEN Deposit**:
1. EtherFi deposits 10 EIGEN ($10) into vault
2. Vault mints 5 new shares (at $2 per share)
3. Vault now has 15 shares holding 20 EIGEN + 10 ETHFI
4. Unwrapping 1 share now gives: **1.33 EIGEN + 0.67 ETHFI** = still $2 total

**Key Insight**: EIGEN amount per KING changes over time as vault composition changes, but dollar value remains constant.

**Implementation Note**: Use `eigen_per_eeth_weekly` and `ethfi_per_eeth` from seasonal_rewards.csv to calculate unwrapping ratios for each timestamp

---

## 🔄 **KING Token Processing Workflow**

### **1. Detection**
- **Trigger**: KING tokens appear in wallet balance
- **Threshold**: Minimum $100 (100x multiple of expected gas fees)
- **Calculation**: `KING_balance_usd > (gas_fee_eth * eth_price_usd * 100)`

### **2. Unwrapping Decision**
```python
def should_unwrap_king(king_balance_usd, gas_fee_eth, eth_price_usd):
    """Determine if KING tokens should be unwrapped."""
    min_threshold = gas_fee_eth * eth_price_usd * 100  # 100x gas fee
    return king_balance_usd > min_threshold
```

### **3. Unwrapping Process**
1. **Unwrap KING** → EIGEN + ETHFI tokens
2. **Transfer to Binance** → Spot exchange
3. **Sell for USDT** → EIGEN/USDT, ETHFI/USDT pairs
4. **Update balances** → Remove KING, add USDT

### **4. P&L Attribution**
- **Discrete Application**: Rewards applied based on weETH balance over period
- **Weighted by Position**: Average weETH position during reward period
- **Exact Dates**: Use `period_start`, `period_end`, `payout_date`

---

## 💰 **P&L Calculation**

### **Reward Attribution Formula**
```python
def calculate_king_rewards_pnl(period_data, weeth_balance_history):
    """Calculate KING rewards P&L for a specific period."""
    period_start = period_data['period_start']
    period_end = period_data['period_end']
    payout_date = period_data['payout_date']
    
    # Get average weETH balance during period
    avg_weeth_balance = get_average_balance(weeth_balance_history, period_start, period_end)
    
    # Calculate reward amount
    reward_eth = period_data['weekly_reward_eth']
    reward_usd = reward_eth * get_eth_price(payout_date)
    
    # Attribute to weETH position
    pnl_usd = reward_usd * (avg_weeth_balance / total_weeth_supply)
    
    return pnl_usd
```

### **Balance-Based P&L**
- **Token Balance**: Include KING token value in exposure calculations
- **Price Source**: Use EIGEN/ETHFI spot prices from Binance
- **Volatility**: Accept P&L volatility if below unwrapping threshold

---

## 🔧 **Implementation Requirements**

### **Data Sources**
1. **KING Distribution Data**: `etherfi_seasonal_rewards_*.csv`
2. **EIGEN Prices**: `market_data/spot_prices/protocol_tokens/binance_EIGENUSDT_*.csv`
3. **ETHFI Prices**: `market_data/spot_prices/protocol_tokens/binance_ETHFIUSDT_*.csv`
4. **ETH Prices**: `market_data/spot_prices/eth_usd/binance_ETHUSDT_*.csv`

### **Strategy Manager Integration**
```python
class StrategyManager:
    def handle_king_tokens(self, king_balance, king_price_usd):
        """Handle KING token unwrapping decision."""
        if should_unwrap_king(king_balance * king_price_usd, self.gas_fee_eth, self.eth_price_usd):
            # Trigger unwrapping
            await self.onchain_execution_manager.unwrap_king_tokens(king_balance)
        else:
            # Hold and track in P&L
            self.track_king_balance(king_balance, king_price_usd)
```

### **OnChain Execution Manager**
```python
class OnChainExecutionManager:
    async def unwrap_king_tokens(self, king_balance):
        """Unwrap KING tokens to EIGEN and ETHFI."""
        # 1. Unwrap KING tokens
        eigen_amount, ethfi_amount = await self.king_contract.unwrap(king_balance)
        
        # 2. Transfer to Binance
        await self.transfer_to_binance(eigen_amount, ethfi_amount)
        
        # 3. Sell for USDT
        await self.cex_execution_manager.sell_protocol_tokens(eigen_amount, ethfi_amount)
```

---

## 📈 **Monitoring and Alerts**

### **KING Token Monitoring**
- **Balance Tracking**: Monitor KING token balance in wallet
- **Price Updates**: Track EIGEN/ETHFI prices for valuation
- **Threshold Alerts**: Alert when unwrapping threshold is reached

### **P&L Attribution**
- **Period Tracking**: Track reward periods and payouts
- **Balance History**: Maintain weETH balance history for attribution
- **Performance Metrics**: Calculate KING rewards contribution to total P&L

---

## 🎯 **Success Criteria**

### **KING Token Handling**
- [ ] Detect KING tokens in wallet balance
- [ ] Calculate unwrapping threshold (100x gas fee)
- [ ] Execute unwrapping when threshold exceeded
- [ ] Transfer unwrapped tokens to Binance
- [ ] Sell EIGEN/ETHFI for USDT
- [ ] Update balances and P&L

### **P&L Attribution**
- [ ] Load seasonal rewards data
- [ ] Calculate average weETH balance per period
- [ ] Attribute rewards based on position weight
- [ ] Apply discrete rewards on payout dates
- [ ] Track KING token value in exposure calculations

### **Data Integration**
- [ ] Load protocol token prices (EIGEN, ETHFI)
- [ ] Load seasonal rewards data
- [ ] Load benchmark data for comparison
- [ ] Validate all data files and date ranges

---

## 📚 **References**

- [EtherFi GitBook - KING Rewards Distribution](https://etherfi.gitbook.io/etherfi/king-protocol-formerly-lrt/king-rewards-distribution)
- [EtherFi KING Protocol Documentation](https://etherfi.gitbook.io/etherfi/king-protocol-formerly-lrt)
- [EIGEN Token Information](https://eigenlayer.xyz/)
- [ETHFI Token Information](https://etherfi.io/)

---

**Status**: Specification complete! ✅