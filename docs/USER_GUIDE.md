# User Guide - Advanced Usage & Strategy Configuration 📚

**For**: Advanced strategy configuration, results interpretation, and optimization  
**Level**: Intermediate to advanced  
**Prerequisites**: Platform running (see [GETTING_STARTED.md](GETTING_STARTED.md))  
**Updated**: January 6, 2025 - Core components working, critical issues remain  
**Last Reviewed**: January 6, 2025  
**Status**: ✅ Aligned with canonical architectural principles

---

## 📚 **Canonical Sources**

**This guide aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Design Decisions**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Core design decisions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

---

## ✅ **Current System Status**

**Backend**: ✅ **Core Components Implemented** | 🔄 **Critical Issues Remain**
- All API endpoints working
- Backtest system executing end-to-end
- 6 strategies available and loaded
- All data loading successfully
- 17% test coverage with 43 passing tests

**Frontend**: 🔧 **Backend Integration Complete**
- API integration working
- Some UI components need completion

**Ready For**: 🔄 **Backtesting** (after critical fixes)

## 📚 **Key References**

**Technical Details**:
- **Components** → [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) (11 core components + specs/)
- **Architecture** → [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) (design decisions)
- **Configuration** → [specs/CONFIGURATION.md](specs/CONFIGURATION.md) (config management)
- **Data Validation** → [specs/09_DATA_PROVIDER](specs/09_DATA_PROVIDER) (data requirements)

---

## 🎯 **Understanding Strategy Modes**

### **7 Strategy Modes**

**Pure USDT Lending** (Simplest):
- Supply USDT to AAVE
- Earn supply interest (~4-6% APY)
- No leverage, no hedging
- **Best for**: Conservative, stable returns

**BTC Basis Trading** (Market-Neutral):
- Long BTC spot + Short BTC perp
- Earn funding rates (~5-10% APY)
- Market-neutral (no BTC price risk)
- **Best for**: Funding rate capture

**ETH Basis Trading** (Directional):
- Long ETH spot + Short ETH perp
- Earn funding rates (~5-10% APY)
- ETH share class (directional exposure)
- **Best for**: ETH exposure with funding rate capture

**ETH Staking Only** (Directional):
- Stake ETH (weETH or wstETH)
- No leverage, no hedging
- ETH share class (directional exposure)
- **Best for**: Simple ETH staking returns (~3-5% APY)

**ETH Leveraged Staking** (Directional):
- Stake ETH (weETH or wstETH)
- Leverage via AAVE borrowing
- ETH share class (directional exposure)
- **Best for**: Leveraged staking returns (6-15% APY)

**USDT Market-Neutral No Leverage** (Market-Neutral):
- Buy ETH, stake, hedge with perps
- No leverage on staking side
- USDT share class (market-neutral)
- **Best for**: Market-neutral staking returns (6-10% APY)

**USDT Market-Neutral** (Most Complex):
- Buy ETH, stake, leverage via AAVE
- Hedge with perpetual futures
- Multi-venue tracking
- **Best for**: Maximum returns with market neutrality (8-15% APY)

---

## 🚀 **Live Trading**

### **Live Trading vs Backtesting**

| **Aspect** | **Backtesting** | **Live Trading** |
|------------|-----------------|------------------|
| **Data Source** | Historical CSV files | Real-time APIs (LiveDataProvider) |
| **Execution** | Simulated (Execution Interfaces) | Real blockchain/CEX (Execution Interfaces) |
| **Transfers** | Simulated cross-venue transfers | Real cross-venue transfers with completion waiting |
| **Risk** | Historical validation | Real-time circuit breakers |
| **Capital** | Virtual | Real money |
| **Speed** | Fast (pre-loaded data) | Real-time (30s cycles) |
| **Architecture** | Same component-based system | Same component-based system |

### **Live Trading Setup**

#### **1. Prerequisites**
- **API Keys**: Binance, Bybit, OKX exchange accounts
- **Wallet**: Ethereum wallet with private key
- **Capital**: Minimum $10,000 recommended
- **Monitoring**: 24/7 system monitoring setup

#### **2. Configuration**
```yaml
# Live trading configuration
trading_mode: live
data_provider_mode: live
execution_mode: live
risk_mode: strict

# Risk limits
max_position_size_usd: 1000000
emergency_stop_loss_pct: 0.15
heartbeat_timeout_seconds: 300
```

#### **3. Starting Live Trading**
```bash
# Configure for live trading
vim backend/env.unified
# Set: BASIS_EXECUTION_MODE=live
# Set: BASIS_LIVE_TRADING__ENABLED=true
# Set: BASIS_LIVE_TRADING__READ_ONLY=true  # Start with read-only

# Deploy live trading system
cd docker
./deploy.sh local all start  # or staging/prod

# Monitor via web interface
# - Frontend: http://localhost:5173
# - API: http://localhost:8001/docs
# - Monitoring: http://localhost:9090
```

### **Live Trading Monitoring**

#### **Real-Time Metrics**
- **Position Status**: Current exposure across all venues
- **Risk Metrics**: LTV, margin ratios, delta exposure
- **Performance**: Real-time P&L, returns, drawdown
- **System Health**: Data freshness, API connectivity, heartbeat (via `/health/detailed`)

#### **Circuit Breakers**
- **Daily Loss Limit**: 15% maximum daily loss
- **Position Size Limit**: $1M maximum position
- **Data Age Limit**: 60 seconds maximum data age
- **Heartbeat Timeout**: 5 minutes maximum silence

#### **Emergency Controls**
- **Emergency Stop**: Immediate position closure
- **Manual Rebalancing**: Force rebalancing outside normal triggers
- **Position Adjustment**: Manual position size changes
- **Risk Override**: Temporarily adjust risk limits

---

## 🧭 **Wizard Flow Guide**

### **Step 1: Choose Share Class**

**USDT (Stable)**:
- Returns in USD
- Must be market-neutral
- No ETH price risk
- **Choose if**: You want stable, predictable returns

**ETH (Directional)**:
- Returns in ETH
- Long ETH exposure
- Benefits from ETH appreciation
- **Choose if**: You're bullish on ETH

---

### **Step 2: Choose Strategy Mode**

**Available modes depend on share class**:

**USDT Share Class**:
- ✅ Pure USDT Lending
- ✅ BTC Basis Trading
- ✅ USDT Market-Neutral No Leverage
- ✅ USDT Market-Neutral

**ETH Share Class**:
- ✅ ETH Basis Trading
- ✅ ETH Staking Only
- ✅ ETH Leveraged Staking

---

### **Step 3: Basic Configuration**

**Initial Capital**:
- USDT modes: USD amount (e.g., $100,000)
- ETH modes: ETH amount (e.g., 100 ETH)
- **Minimum**: $10,000 or 10 ETH

**Date Range**:
- **Available**: 2024-01-01 to 2025-09-18
- **Recommended**: 2024-05-12 to 2025-09-18 (full data for weETH)
- **Note**: weETH launched 2024-05-12, wstETH available from 2024-01-01

---

### **Step 4: Strategy Parameters** (Mode-Specific)

**For USDT Market-Neutral**:

**Staking Token**:
- `weETH` (EtherFi) - Restaking rewards available
- `wstETH` (Lido) - Classic staking only

**Rewards Mode** (locked for USDT):
- `base_only` - Oracle price drift only
- (EIGEN/ETHFI rewards only available for ETH share class)

**Leverage Options**:
- **Execution**: Atomic flash loan only (saves ~$150 gas vs sequential)
- **Target LTV**: 0.91 recommended (safe), 0.93 max (risky)
- **No Iterations**: Atomic execution is deterministic based on target LTV

**Hedging**:
- **Venues**: Select exchanges (Binance, Bybit, OKX)
- **Allocation**: Split hedge across exchanges (default 33/33/34)

**Risk Thresholds**:
- **Margin Warning**: 20% (triggers rebalancing alert)
- **Delta Threshold**: 5% (triggers hedge adjustment)

---

### **Step 5: Review & Submit**

**Review Summary**:
- All configuration displayed
- Estimated APY range shown
- Submit to run backtest

**Estimated Time**: 30-60 seconds for full 18-month backtest

---

## 📊 **Understanding Results**

### **Summary Metrics**

**Total P&L**:
- USDT modes: Shown in USD
- ETH modes: Shown in ETH
- **Meaning**: Total profit/loss from strategy

**APY (Compounded)**:
- Annualized return percentage
- **Meaning**: If maintained for 1 year, expected return

**P&L Reconciliation**:
- **Balance-Based**: Actual portfolio value change (source of truth)
- **Attribution**: Sum of all P&L components (breakdown)
- **Difference**: Should be < 2% tolerance
- **Unexplained PNL**: Residual (spread changes, etc.)
- **Status**: ✅ Pass or ⚠️ Investigate

**Max Drawdown**:
- Maximum peak-to-trough decline
- **Meaning**: Worst losing streak

---

### **P&L Components** (Attribution Breakdown)

**Supply PNL**: Interest earned from AAVE supply  
**Staking Yield (Oracle)**: weETH/ETH price appreciation (~2.8% APR)  
**Staking Yield (Rewards)**: EIGEN weekly + ETHFI airdrops  
**Borrow Cost**: Interest paid on AAVE debt  
**Funding PNL**: Perpetual funding rate payments (± depending on rate)  
**Delta PNL**: P&L from unhedged exposure  
**Transaction Costs**: Gas + execution costs

---

### **Risk Metrics**

**Health Factor** (AAVE):
- Formula: (Liquidation Threshold × Collateral) / Debt
- > 1.5: Safe
- 1.1-1.5: Caution
- < 1.1: Warning
- < 1.0: Liquidated!

**% Move to Liquidation**:
- How much ETH can drop before HF = 1
- Formula: (1 - 1/HF) × 100
- Example: HF = 1.067 → 6.28% drop to liquidation

**Margin Ratio** (CEX):
- Formula: Account Balance / Position Exposure
- > 50%: Safe
- 20-50%: Caution
- < 20%: Warning (rebalance!)
- < 10%: Liquidation

**Net Delta**:
- Your market exposure in ETH
- **Target**: 0 for market-neutral strategies
- **Acceptable**: ±5% drift before rebalancing

---

### **Charts**

**Cumulative P&L**:
- Your total returns over time
- Compare to Ethena benchmark (if applicable)
- Interactive: Zoom, pan, hover for details

**P&L Components**:
- Stacked view of all P&L sources
- See which components contribute most
- Identify optimization opportunities

**Delta Neutrality** (hedged strategies):
- Net delta % over time
- Should hover near 0%
- Spikes indicate rebalancing needed

**Margin Ratios** (hedged strategies):
- CEX margin health per exchange
- Warning/critical thresholds marked
- Shows when rebalancing happened

---

### **Event Log**

**70,000+ events** documenting every operation:

**Filter by**:
- Event type (GAS_FEE, STAKE, TRADE, etc.)
- Venue (ETHEREUM, AAVE, BINANCE, etc.)
- Date range

**Expand Row** to see:
- Wallet balances after event
- CEX balances after event
- AAVE positions
- Gas details

**Export**: Filtered events to CSV for analysis

---

## 🎨 **Advanced Configuration**

### **Leverage Settings**

**Flash Loan** (Recommended):
- Single atomic transaction
- ~$50 gas cost
- Faster, more efficient

**Legacy Sequential** (Deprecated):
- Multiple transactions (23 iterations) - NO LONGER SUPPORTED
- ~$200 gas cost
- Replaced by atomic flash loan execution

**Target LTV**:
- 0.91: Safe (recommended)
- 0.85: Very conservative
- 0.93: Maximum (risky!)

---

### **Hedging Strategy**

**Venue Selection**:
- Binance: Required (spot purchase venue)
- Bybit: Optional (additional liquidity)
- OKX: Optional (note: futures data incomplete, proxies to Binance)

**Allocation**:
- Default: 33/33/34 (equal split)
- Customize based on preferences
- Affects funding rate exposure

---

### **Risk Management**

**Margin Warning**: 20% (default)
- Below this: System alerts
- Action: Consider adding margin
- **Change if**: You want earlier warnings (e.g., 30%)

**Delta Threshold**: 5% (default)
- Above this: Hedge drift warning
- Action: Rebalancing recommended
- **Change if**: You want tighter neutrality (e.g., 3%)

---

## 📈 **Interpreting Results**

### **Good Strategy Performance**

✅ **P&L Reconciliation Passed** (< 2% diff)  
✅ **Positive Returns** (P&L > 0)  
✅ **APY Beats Benchmark** (> Ethena if USDT mode)  
✅ **Low Drawdown** (< 10%)  
✅ **Stable Health Factor** (never < 1.1)  
✅ **Margin Never Critical** (no liquidations)

### **Red Flags**

⚠️ **P&L Reconciliation Failed** (> 2% diff)
- Check unexplained PNL sources
- May indicate calculation error

⚠️ **Negative Returns** (P&L < 0)
- Check P&L components (which lost money?)
- Review period (bear market?)

⚠️ **High Drawdown** (> 20%)
- Strategy too risky
- Consider lower leverage

⚠️ **Health Factor Warnings**
- Risk of AAVE liquidation
- Reduce target LTV

⚠️ **Margin Warnings**
- Risk of CEX liquidation
- Add more margin or reduce hedge

---

## 🎯 **Strategy Selection Guide**

### **By Risk Tolerance**

**Conservative** (Low risk, stable returns):
- Pure USDT Lending (4-6% APY)
- ETH Staking Only (3-5% APY)
- No leverage, no complexity

**Moderate** (Medium risk, good returns):
- BTC Basis (5-10% APY)
- ETH Basis (5-10% APY)
- USDT Market-Neutral No Leverage (6-10% APY)
- ETH Leveraged with low LTV (6-8% APY)

**Aggressive** (Higher risk, maximum returns):
- USDT Market-Neutral with high LTV (8-15% APY)
- ETH Leveraged with high LTV (6-15% APY)
- Multiple venues
- Complex rebalancing

---

### **By Market Conditions**

**Bull Market** (ETH rising):
- ETH Leveraged (ETH share class) - Benefit from appreciation
- ETH Staking Only (ETH share class) - Simple ETH exposure
- ETH Basis (ETH share class) - ETH exposure with funding
- High leverage OK

**Bear Market** (ETH falling):
- Pure Lending (stable)
- BTC Basis (market-neutral)
- Low leverage strategies

**High Volatility**:
- Market-neutral strategies (USDT modes)
- BTC Basis (market-neutral)
- Tighter risk thresholds

---

## 🚀 **Getting Started Checklist**

**First Time**:
- [ ] Start platform (`cd docker && ./deploy.sh local all start`)
- [ ] Try Pure Lending (simplest mode)
- [ ] Review results
- [ ] Download CSV files
- [ ] Understand metrics

**Development Workflow** (Optimized):
- [ ] Use optimized Docker builds (`docker compose build backend`)
- [ ] Leverage dependency caching (99% faster builds)
- [ ] Run demo script (`./deploy/build-optimized.sh`) to see caching benefits

**Next**:
- [ ] Try BTC Basis or ETH Leveraged
- [ ] Try ETH Staking Only (simple directional)
- [ ] Try USDT Market-Neutral No Leverage (market-neutral)
- [ ] Experiment with parameters
- [ ] Compare to benchmarks
- [ ] Optimize configuration

**Advanced**:
- [ ] Try USDT Market-Neutral (full complexity)
- [ ] Try ETH Basis (directional with funding)
- [ ] Analyze event logs (find optimization opportunities)
- [ ] Test different leverage levels
- [ ] Simulate market scenarios

---

## 📞 **Support Resources**

**Documentation**:
- **CONFIG_REFERENCE.md** - All parameters explained
- **API_REFERENCE.md** - API endpoints
- **COMPONENT_SPECS_INDEX.md** - How it works under the hood

**Data**:
- **SCRIPTS_DATA_GUIDE.md** - Data requirements
- **DEPLOYMENT_GUIDE.md** - Deployment instructions

**Development**:
- **Docker Build Optimization** - 99% faster builds with dependency caching
- **Multi-stage Dockerfile** - Smart layer caching for requirements vs source code
- **Build Demo Script** - `./deploy/build-optimized.sh` shows caching benefits

---

**Status**: User guide complete! Ready to use the platform! ✅

*Last Updated: October 9, 2025*