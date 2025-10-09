# Architectural Decisions - CANONICAL REFERENCE 🏛️

**Status**: ⭐ **CANONICAL SOURCE** - Single source of truth for all design decisions  
**Usage**: All other docs REFERENCE this file, do not duplicate content  
**Updated**: October 6, 2025 - Updated to reflect 100% implementation completion  
**Last Reviewed**: October 8, 2025  
**Status**: ✅ Aligned with canonical sources (.cursor/tasks/ + MODES.md)

---

## ADR-001: Separate Data Source from Execution Mode

**Date**: 2025-01-09  
**Status**: Accepted  
**Context**: The original architecture conflated data source (csv vs db) with execution mode (backtest vs live), leading to confusion and inflexibility.

**Decision**: Separate `BASIS_DATA_MODE` (csv/db) from `BASIS_EXECUTION_MODE` (backtest/live) to create clear separation of concerns.

**Consequences**:
- **Positive**: Clear separation between data source and execution behavior
- **Positive**: On-demand data loading eliminates startup bottlenecks
- **Positive**: Environment-driven validation using `BASIS_DATA_START_DATE`/`BASIS_DATA_END_DATE`
- **Positive**: `BASIS_DATA_MODE` only controls data source, NOT persistence or execution routing
- **Negative**: Requires refactoring of data provider factory and initialization logic
- **Negative**: More complex environment variable validation

**Implementation**:
- `BASIS_DATA_MODE=csv|db` controls data source for backtest mode only
- `BASIS_EXECUTION_MODE=backtest|live` controls venue execution behavior
- Data loaded on-demand during API calls, not at startup
- Date range validation against environment variables
- Health checks handle uninitialized data provider state

---

## 📚 **Cross-References**

**For implementation details**, see:
- **AAVE mechanics** → [specs/02_EXPOSURE_MONITOR.md](specs/02_EXPOSURE_MONITOR.md)
- **Component overview** → [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md)
- **Implementation tasks** → [REQUIREMENTS.md](REQUIREMENTS.md)
- **Timeline** → [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)
- **Configuration** → [specs/CONFIGURATION.md](specs/CONFIGURATION.md)

---

## 🎯 **Core Design Decisions**

### **1. Configuration Separation of Concerns** ✅
**Decision**: Implement proper configuration hierarchy with clear separation of concerns

**Implementation**:
```
configs/
├── modes/                # Strategy mode configurations (YAML)
├── venues/               # Venue configurations (YAML)
├── share_classes/        # Share class configurations (YAML)
└── scenarios/            # Scenario configurations (YAML) - NOT YET IMPLEMENTED

deploy/
├── .env.dev           # Caddy deployment variables (local)
├── .env.staging         # Caddy deployment variables (staging)
└── .env                 # Caddy deployment variables (production)
```

**Rationale**:
- **Clear Responsibility**: Each config file has a specific purpose
- **No Duplication**: Single source of truth for each configuration type
- **Environment Isolation**: Proper separation between dev/staging/production
- **Deployment Separation**: BASIS config vs Caddy deployment config

**Configuration Loading Order**:
1. **YAML-based configuration system** (CURRENT IMPLEMENTATION)
   - `modes/*.yaml` - Strategy mode configurations
   - `venues/*.yaml` - Venue configurations  
   - `share_classes/*.yaml` - Share class configurations
   - `scenarios/` - Scenario configurations (NOT YET IMPLEMENTED)

2. **YAML-based configuration** (IMPLEMENTED)
   - `configs/modes/*.yaml` (strategy configurations) - ✅ IMPLEMENTED
   - `configs/venues/*.yaml` (venue configurations) - ✅ IMPLEMENTED
   - `configs/share_classes/*.yaml` (share class definitions) - ✅ IMPLEMENTED

### **2. Live Data Provider Architecture** ✅
**Decision**: Implement LiveDataProvider with same interface as HistoricalDataProvider

**Implementation**:
```python
class DataProvider:
    def __init__(self, data_dir: str, mode: str, execution_mode: str = 'backtest', config: Optional[Dict] = None):
        if execution_mode == 'live':
            from .live_data_provider import LiveDataProvider
            self.live_provider = LiveDataProvider(config)
        else:
            self.live_provider = None
            self._load_data_for_mode()  # Historical data
```

**Rationale**:
- **Seamless Switching**: Same interface for backtest and live modes
- **Real-time Data**: Live WebSocket/API feeds for live trading
- **Caching Strategy**: In-memory and Redis support with configurable TTL
- **Error Handling**: Graceful degradation when live sources fail
- **Environment Awareness**: Automatic API key loading from environment variables

**Data Sources**:
- **CEX APIs**: Binance, Bybit, OKX for spot/futures prices and funding rates
- **DeFi APIs**: AAVE, EtherFi, Lido for protocol data
- **Oracle APIs**: Chainlink, Pyth for price feeds
- **Gas APIs**: Etherscan, Alchemy for gas price data

### **3. Execution Interface Architecture** ✅
**Decision**: Implement execution interfaces with seamless backtest/live switching

**Implementation**:
```python
# Factory pattern for execution interfaces
class ExecutionInterfaceFactory:
    @staticmethod
    def create_all_interfaces(execution_mode: str, config: Dict) -> Dict[str, BaseExecutionInterface]:
        interfaces = {}
        interfaces['cex'] = CEXExecutionInterface(execution_mode, config)
        interfaces['onchain'] = OnChainExecutionInterface(execution_mode, config)
        return interfaces

# EventDrivenStrategyEngine integration
class EventDrivenStrategyEngine:
    def __init__(self, config):
        self.execution_interfaces = ExecutionInterfaceFactory.create_all_interfaces(
            execution_mode=self.execution_mode,
            config=self.config
        )
```

**Rationale**:
- **Seamless Switching**: Same interface for backtest and live execution
- **Real Execution**: Live mode uses CCXT (CEX) and Web3.py (on-chain) for real trades
- **Simulated Execution**: Backtest mode uses validated calculators and market data
- **Unified Interface**: Single API for all execution operations regardless of mode
- **Component Integration**: Properly integrated with Position Monitor, Event Logger, and Data Provider

**Execution Types**:
- **CEX Execution**: Spot and perpetual trading on Binance, Bybit, OKX
- **On-Chain Execution**: AAVE operations, staking, swaps, wallet transfers
- **Error Handling**: Graceful fallbacks and comprehensive logging
- **Dependency Injection**: Clean separation of concerns with proper component wiring

### **3. Hybrid Approach: Extract → Integrate** ✅
**Decision**: Extract calculators from monolithic scripts → Copy to backend → Integrate

**Rationale**:
- Validates calculations first (low risk)
- Backend uses proven logic
- Prepares for live trading (pure functions)
- No throwaway code

**Timeline**: 2.5 weeks to working web UI

---

### **2. Calculator Import: Copy to Backend** ✅
**Decision**: Copy validated calculators to `backend/src/basis_strategy_v1/core/math/`

**Implementation**:
```bash
# After extraction and validation
cp scripts/analyzers/calculators/*.py backend/src/basis_strategy_v1/core/math/

# Backend imports
from ...math.aave_calculator import AAVECalculator
```

**Rationale**:
- Clean Python imports (no path hacks)
- Backend is self-contained package
- Can deploy without scripts/ directory
- Sync script when calculators change

**Note**: Extract calculators from monolithic scripts FIRST, then copy

---

### **3. BTC Mode: Implement with Data Download** ✅
**Decision**: Implement BTC mode, download BTC data first

**Data Needed**:
- BTC/USDT spot (Binance)
- BTC perpetual futures OHLCV (Binance, Bybit)
- BTC funding rates (Binance, Bybit, OKX)

**Scripts**: Already exist in `scripts/orchestrators/fetch_cex_data.py`  
**Action**: Add BTC pairs to existing download scripts

---

### **4. Wallet/Venue Model** ✅

**On-Chain (Single Ethereum Wallet)**:
```python
wallet = {
    'ETH': float,              # Native ETH (pays gas for ALL on-chain tx)
    'USDT': float,             # USDT holdings
    'weETH': float,            # LST holdings (free, not supplied to AAVE)
    'wstETH': float,           # Alternative LST
    'aWeETH': float,           # AAVE aToken (CONSTANT scaled balance)
    'variableDebtWETH': float  # AAVE debt token (CONSTANT scaled balance)
}
```

**AAVE Position Naming** (Critical Clarification):
```python
# What wallet actually holds
wallet.aWeETH  # ERC-20 aToken (constant)
wallet.variableDebtWETH  # ERC-20 debt token (constant)

# AAVE positions (derived, multiple representations)
aave = {
    # Native (what AAVE sees after index multiplication)
    'weeth_supply_native': wallet.aWeETH × liquidity_index,  # Redeemable weETH
    'weth_debt_native': wallet.variableDebtWETH × borrow_index,  # Owed WETH
    
    # ETH equivalent (multiply by oracle price)
    'weeth_supply_eth': (wallet.aWeETH × liquidity_index) × (weETH/ETH oracle),
    'weth_debt_eth': wallet.variableDebtWETH × borrow_index,  # WETH = ETH (1:1)
    
    # USD equivalent (multiply by ETH/USD price)
    'weeth_supply_usd': weeth_supply_eth × eth_usd_price,
    'weth_debt_usd': weth_debt_eth × eth_usd_price
}
```

**Naming Convention**:
- `_native`: Native token units (what AAVE calculates)
- `_eth`: ETH equivalent (for delta tracking)
- `_usd`: USD equivalent (for P&L in USDT modes)

**Off-Chain (Separate CEX Accounts)**:
```python
cex_accounts = {
    'binance': {
        'balance_usdt': float,  # Total account balance
        'eth_spot': float,      # Spot ETH holdings
        'btc_spot': float,      # Spot BTC holdings
        'perp_positions': {...}
    },
    'bybit': { /* separate account */ },
    'okx': { /* separate account */ }
}
```

**Key Points**:
- EtherFi/Lido are conversion protocols (wallet.ETH → wallet.weETH)
- AAVE positions via aTokens in wallet (not separate balances)
- Each CEX is completely separate account/wallet

---

### **5. Backtest Timing Constraints** ⏰

**Constraint 1: Hourly Price Updates Only**
```python
# All market data updates ON THE HOUR
# Valid: '2024-05-12 14:00:00'
# Invalid: '2024-05-12 14:30:00' (no data)

# All prices from same hourly snapshot
eth_spot = get_price('ETH/USDT', '2024-05-12 14:00:00')
binance_perp = get_price('ETHUSDT-PERP', '2024-05-12 14:00:00')
oracle_weeth = get_price('weETH/ETH', '2024-05-12 14:00:00')
```

**Constraint 2: Atomic Event Execution**
```python
# Sequential leverage loop (23 iterations)
# All 70+ events share same timestamp: '2024-05-12 00:00:00'
# Differentiated by order: 1, 2, 3, ..., 70

# Atomic flash loan (1 transaction)
# 6-7 events share same timestamp
# Differentiated by order: 1, 2, 3, 4, 5, 6

# ALL use same price snapshot (no timing risk)
```

**Event Timing Structure**:
```python
event = {
    'timestamp': pd.Timestamp,  # Trigger time (on the hour)
    'order': int,               # Global sequence (1, 2, 3...)
    'status': 'completed',      # Always in backtest
    
    # Live trading extensions (all None in backtest)
    'completion_timestamp': None,
    'tx_hash': None,
    'confirmation_blocks': None
}
```

---

### **6. USDT Market-Neutral Entry Flow** ✅

**Standardized Flow**:
```python
# Step 1: Fund ALL CEXs simultaneously
wallet.USDT -= (binance + bybit + okx)
cex['binance'].USDT += binance
cex['bybit'].USDT += bybit
cex['okx'].USDT += okx

# Step 2: Execute ALL perp shorts simultaneously (same timestamp!)
# Binance: Spot + Perp
cex['binance'].ETH_spot += eth_bought
cex['binance'].perp = short_binance

# Bybit & OKX: Perp only (executed at same time as Binance!)
cex['bybit'].perp = short_bybit
cex['okx'].perp = short_okx

# Step 3: Transfer ETH to wallet
cex['binance'].ETH_spot -= eth_transfer
wallet.ETH += eth_transfer

# Step 4: Leverage loop on wallet
# (All at same timestamp)
```

**Key**: ALL perp shorts at same time, not sequential!

---

### **7. Obsolete Code Removal** ✅

**Remove**:
- ✅ USDT borrowing on AAVE for basis trade (not economical)
- ✅ Multiple ETH entry paths (standardize to one, but keep atomic vs sequential toggle)
- ✅ Fixed balance P&L mode (ETH analyzer is outdated)

**Keep**:
- ✅ Pure USDT lending mode (simple supply-only)
- ✅ WETH/ETH auto-conversion (AAVE unwraps, EtherFi accepts both)

**Clarifications**:
- ETH share class: One path (stake → AAVE loop), but atomic vs sequential toggle remains
- WETH/ETH: Assume protocols handle conversion, always talk in wrapped non-rebasing tokens

---

### **8. Share Class P&L Currency** ✅

**ETH Share Class**:
- All P&L in ETH
- Initial capital in ETH (e.g., 100.0 = 100 ETH)
- CSV columns: `net_pnl_eth`, `cumulative_pnl_eth`
- Plots: ETH-denominated axes

**USDT Share Class**:
- All P&L in USD
- Initial capital in USD (e.g., 100000 = $100k)
- CSV columns: `net_pnl_usd`, `cumulative_pnl_usd`
- Plots: USD-denominated axes

---

### **9. Reward Modes for weETH** ✅

**base_only**:
- Oracle price growth only (weETH/ETH appreciates)
- No EIGEN weekly rewards
- No ETHFI seasonal drops

**base_eigen**:
- Oracle price growth
- Plus EIGEN weekly distributions (from GitBook data)
- No ETHFI seasonal drops

**base_eigen_seasonal**:
- Oracle price growth
- Plus EIGEN weekly distributions
- Plus ETHFI seasonal drops (ad-hoc from GitBook data)

**Rewards Mode Validation**:
- All strategies can use any rewards mode
- Limitation is data availability, not strategy type
- Validation checks if required data exists for backtest period
- `base_only` is most conservative (works with any data period)

**wstETH**:
- Only supports `base_only` (no restaking rewards, just base Lido staking)

---

### **10. Leverage Loop Variations** ✅

**Iteration Limits**:
- `None` = Unlimited (until remaining < $10k)
- `0` = No leverage (stake once, no borrow)
- `1` = One loop (stake → borrow → stake again, stop)

**Execution Methods**:
- **Sequential** (23 iterations): 70+ events, ~$200 gas, easier to debug
- **Atomic Flash** (1 transaction): 6-7 events, ~$50 gas, gas efficient

**Default**: Atomic flash for USDT modes (gas savings)  
**Available**: Both methods in all leverage modes

---

### **11. Hedging Logic** ✅

**ETH Share Class**:
- Never hedge (directional ETH exposure desired)
- Auto-disable `basis_trade_enabled` if set

**USDT Share Class**:
- Always hedge (market-neutral required)
- Auto-enable `basis_trade_enabled` if staking enabled
- Fail with error if disabled for staking strategies

---

### **12. Gas Debt Accounting** ✅

**USDT Share Class**:
```python
# Start with 0 ETH
wallet.ETH = 0

# Gas fees create negative balance
wallet.ETH -= gas_fee  # Goes negative

# Track as debt
gas_debt_eth = -wallet.ETH if wallet.ETH < 0 else 0

# Reduce total value
total_value_usd -= gas_debt_eth × eth_price
```

**ETH Share Class**:
```python
# Start with positive ETH
wallet.ETH = initial_capital  # e.g., 100.0 ETH

# Gas fees deduct from balance
wallet.ETH -= gas_fee  # Reduces positive balance

# No separate "gas debt" tracking
# Just normal balance deduction
```

**Key**: Same process, just different starting balance!

---

### **13. Event Logging Detail** ✅

**All Modes**: Full detail
- Atomic transaction breakdowns (flash loan 6-step sequence)
- Per-venue balance snapshots in every event
- Margin ratio tracking
- LTV impact annotations

**Reason**: Complete audit trail for all strategies  
**Exception**: None (even simple modes get full detail)

---

### **14. Per-Exchange Price Tracking** ✅

**Required**: YES
```python
# Each exchange has separate prices
binance_mark = get_futures_price('ETH', 'binance', timestamp)
bybit_mark = get_futures_price('ETH', 'bybit', timestamp)
okx_mark = binance_mark  # Proxy (no OKX data yet)

# Separate M2M calculations
binance_mtm = eth_short × (entry - binance_mark)
bybit_mtm = eth_short × (entry - bybit_mark)
# NOT: (binance_mtm + bybit_mtm) / 2 (WRONG!)
```

**Validation**: Flag if price divergence > 0.5% (possible data error)  
**Arbitrage Alert**: Log if divergence > 1% (arbitrage opportunity)

---

### **15. Spot Venue Selection** ✅

**Default**: Binance (for USDT strategies)  
**Reason**: Already funding Binance for perps, enables simultaneous execution  
**Alternative**: Uniswap (configurable option)  
**Impact**: If Uniswap, can't execute spot + perp simultaneously

**In Backtest**: Simultaneous anyway (atomic execution assumption)

---

### **16. CEX Hedge Allocation** ✅

**User Configurable**:
```yaml
hedge_allocation:
  binance: 0.33  # User sets percentages
  bybit: 0.33
  okx: 0.34
```

**Not**: Auto-calculated based on funding rates (too complex for now)

---

### **17. Output File Structure** ✅

**Organized Approach**:
```
data/analysis/usdt_market_neutral/
  summary_20241001_1430.json
  hourly_pnl_20241001_1430.csv
  event_log_20241001_1430.csv
  balance_sheet_20241001_1430.csv
  plots/
    cumulative_pnl.html       # Plotly interactive
    pnl_components.html
    delta_neutrality.html
    margin_ratios.html
    # ... all plots as Plotly HTML
```

**Plots**: Plotly HTML (interactive, browser-friendly), NOT PNG

---

### **18. Seasonal Reward Distribution** ✅

**Discrete Events**: YES
```python
# Not: Smooth hourly accrual
# Instead: Discrete payments on exact dates

if timestamp == payout_date:
    avg_weeth_balance = calc_period_average(weeth_balances)
    reward_amount = distribution_rate × avg_weeth_balance
    
    event_logger.log_event(
        timestamp=timestamp,
        event_type='REWARD_PAYMENT',
        venue='EIGENLAYER',  # or 'ETHERFI'
        token='EIGEN',  # or 'ETHFI'
        amount=reward_amount,
        earning_period=(period_start, period_end)
    )
```

**Data Sources**:
- `data/manual_sources/etherfi_distributions/seasonal_drops.csv`
- `data/manual_sources/etherfi_distributions/ethfi_topups_raw.csv`
- `data/manual_sources/etherfi_distributions/eigen_distributions_raw.csv`

**Processing**: Use exact distribution times, don't smooth

---

### **19. Data File Naming** ✅

**Dynamic Data File Loading**:
```python
# Data files loaded dynamically based on configuration and date ranges
# No hardcoded file paths - all loaded through DataProvider configuration
DATA_FILES = {
    'eth_spot_binance': config.get_data_file_path('eth_spot_binance', start_date, end_date),
    'weeth_rates': config.get_data_file_path('weeth_rates', start_date, end_date),
    'binance_futures': config.get_data_file_path('binance_futures', start_date, end_date),
    # All file paths loaded from configuration, not hardcoded
}
```

**Rationale**: Saves time, known data ranges  
**Future**: Auto-discover latest files or pass as config param

---

### **20. Pricing Oracle Strategy** ✅

**Spot Prices** (ETH/USD):
- **Source**: Binance USDT spot (hourly OHLCV)
- **Reason**: Used for perp comparison, needs to match perp pricing source
- **File**: `binance_ETHUSDT_spot_1h_*.csv` OR `uniswapv3_WETHUSDT_1h_*.csv`

**AAVE Oracle** (weETH/ETH, wstETH/ETH):
- **Source**: AAVE oracle prices (interpolated daily → hourly)
- **Reason**: Measures staked spread risk, LST de-pegging
- **Use**: Health factor calculations, delta calculations
- **File**: `weETH_ETH_oracle_*.csv`

**Why Two Oracles**:
- Binance spot for absolute USD pricing (perp neutrality)
- AAVE oracle for relative ETH pricing (staked spreads)
- Different purposes, both needed

---

### **21. Live Trading Architecture** ✅

**Service Orchestration Pattern**:
```python
# BacktestService orchestrates backtests
backtest_service = BacktestService()
request = backtest_service.create_request(...)
request_id = await backtest_service.run_backtest(request)

# LiveTradingService orchestrates live trading
live_service = LiveTradingService()
request = live_service.create_request(...)
request_id = await live_service.start_live_trading(request)
```

**Live Service Components**:
- **Request Management**: LiveTradingRequest with validation
- **Strategy Orchestration**: Manages EventDrivenStrategyEngine lifecycle
- **Risk Monitoring**: Real-time risk limit checking
- **Health Monitoring**: Heartbeat tracking and health checks
- **Emergency Controls**: Emergency stop and risk breach handling
- **Performance Tracking**: Real-time P&L and metrics

**Data Access Abstraction**:
```python
class DataLoader:
    def __init__(self, mode: str = 'backtest'):
        self.mode = mode
    
    def get_spot_price(self, asset, timestamp):
        if self.mode == 'backtest':
            return self.csv_data[asset].loc[timestamp, 'price']
        elif self.mode == 'live':
            return await self.db.get_latest_price(asset)
```

**Key**: Service layer orchestrates, components stay pure

---

### **22. Atomic vs Sequential Leverage Loops** ✅

**Sequential (Traditional)**:
```python
# 23 separate transactions, 23 blocks
for iteration in range(1, 24):
    # Each iteration: 3 events (gas, stake, supply, gas, borrow)
    # Total: 70+ events at same timestamp
    # Order: 1, 2, 3, ..., 70
    # Iteration field groups related events
    
events = [
    {'order': 1, 'event': 'GAS_FEE_PAID', 'iteration': 1},
    {'order': 2, 'event': 'STAKE_DEPOSIT', 'iteration': 1},
    {'order': 3, 'event': 'COLLATERAL_SUPPLIED', 'iteration': 1},
    {'order': 4, 'event': 'GAS_FEE_PAID', 'iteration': 1},
    {'order': 5, 'event': 'LOAN_CREATED', 'iteration': 1},
    # ... repeat for 23 iterations
]
```

**Atomic Flash Loan (One Block)**:
```python
# Single transaction, 1 block
# 6-7 events at same timestamp
# Order: 1, 2, 3, 4, 5, 6
# No iteration field (single atomic operation)

events = [
    {'order': 1, 'event': 'ATOMIC_TRANSACTION', 'bundle': 'LEVERAGE_ENTRY'},
    {'order': 2, 'event': 'FLASH_BORROW', 'parent': 1},
    {'order': 3, 'event': 'STAKE_DEPOSIT', 'parent': 1},
    {'order': 4, 'event': 'COLLATERAL_SUPPLIED', 'parent': 1},
    {'order': 5, 'event': 'LOAN_CREATED', 'parent': 1},
    {'order': 6, 'event': 'FLASH_REPAID', 'parent': 1},
    {'order': 7, 'event': 'GAS_FEE_PAID', 'parent': 1}
]
```

**Distinction**:
- Sequential: Many iterations, `iteration` field
- Atomic: One bundle, `parent` field links to bundle event

---

### **23. Rebalancing Implementation** 🔮

**Status**: Future phase (after core modes working)

**From FINAL_FIXES_SPECIFICATION.md**:

**Triggers**:
1. Margin ratio < 20% (URGENT - add margin to CEX)
2. Delta drift > 5% (WARNING - adjust hedge)
3. Health factor < 1.10 (CRITICAL - reduce AAVE leverage)

**Atomic Deleverage Flow**:
```python
# Extract capital from AAVE position
1. Flash borrow WETH
2. Repay partial AAVE debt
3. Withdraw weETH collateral
4. Swap weETH → ETH (one swap)
5. Repay flash loan
6. Send freed ETH to CEX

# CEX execution
7. Sell ETH for USDT (spot)
8. Reduce perp short (buy to cover)
9. Rebalance between exchanges if needed
```

**Target Margin Ratio**: 100% (full capital utilization)  
**Exchange Split**: 50/50 target, allow ±1-2% drift

**Priority**: Phase 4+ (after core modes validated)  
**Estimate**: ~400-500 lines

---

### **24. Balance Sheet Tracking** ✅

**All Modes**: Track complete balance sheet
```python
total_value = (
    sum(cex_account_balances) +       # All CEX accounts
    aave_collateral_value -            # AAVE supply
    aave_debt_value -                  # AAVE debt
    gas_debt_eth × eth_price +        # Gas debt (if negative)
    wallet.free_eth × eth_price +     # Free ETH (if any)
    wallet.free_usdt                  # Free USDT (if any)
)
```

**Mode Differences**:
- Pure lending: Just USDT position
- BTC basis: Just CEX account + BTC spot
- ETH leveraged: AAVE + wallet, no CEX
- USDT neutral: All venues (most complex)

**CSV Output**: Balance sheet history for ALL modes (optional extra file)

---

### **25. Config vs CLI Priority** ✅

**CLI Overrides YAML**:
```bash
python unified_analyzer.py \
  --config config.yaml \           # max_leverage_iterations: 10
  --max-leverage-iterations 20     # Overrides to 20
```

**Rationale**: CLI is more immediate, user's last word

**Required Parameters**:
- Mode (or auto-detect from flags)
- Share class
- Initial capital
- Start date, end date

**Optional**: Everything else has smart defaults

---

### **26. Validation Philosophy** ✅

**Fail-Fast for Impossible Configs**:
```yaml
# This fails immediately
share_class: USDT
staking_enabled: true
basis_trade_enabled: false
# Error: "USDT staking requires hedging!"
```

**Auto-Correct for Derivable**:
```yaml
# This auto-corrects
share_class: ETH
basis_trade_enabled: true
# Auto-disables basis_trade, logs warning
```

**Rule**: If mode can be inferred, auto-correct. If contradiction, fail.

---

### **27. Testing Granularity** ✅

**Calculator Tests**: Pure math only
- Unit tests with known inputs/outputs
- Test each function independently
- 100% code coverage for calculators

**Component Tests**: Integration between components  
**Mode Tests**: End-to-end per mode  
**Backend Tests**: API integration  
**Frontend Tests**: User flows

**No Need**: Automated old vs new comparison scripts

---

### **28. Plot Format** ✅

**Plotly HTML Interactive Charts**:
```python
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(...))
fig.write_html('cumulative_pnl.html')
```

**Not**: PNG static images  
**Reason**: Interactive, browser-friendly, better UX

**Location**:
```
data/analysis/usdt_market_neutral/
  plots/
    cumulative_pnl.html
    delta_neutrality.html
    margin_ratios.html
```

---

### **29. Documentation Structure** ✅

**Interim Docs**: `claude-4.5-answers/docs/`  
**Analyzer Docs**: `scripts/analyzers/README.md`  
**Main README**: Update with link to analyzer docs

**Later**: Merge to main `docs/` when ready for full migration

---

### **30. Margin Ratio Thresholds** ✅

**Venue Constants** (Real exchange limits):
```python
VENUE_CONSTANTS = {
    'binance': {'maintenance_margin': 0.10},  # 10% liquidation
    'bybit': {'maintenance_margin': 0.10},
    'okx': {'maintenance_margin': 0.10}
}
```

**User Buffer** (Configurable):
```python
config = {
    'margin_warning_threshold': 0.20,  # Warn at 20%
    'margin_urgent_threshold': 0.15,   # Urgent at 15%
    # Liquidation at 10% (venue constant)
}
```

**Plot Annotations**: YES - Show warning periods on margin ratio plot

---

### **31. Shared Calculator Logic** ✅

**Example: Lido vs EtherFi**:
```python
# Shared staking calculator
class StakingCalculator:
    @staticmethod
    def stake_eth_to_lst(eth_amount, oracle_price, lst_type):
        """Works for both wstETH and weETH."""
        lst_received = eth_amount / oracle_price
        return lst_received
    
    @staticmethod
    def get_yield(timestamp, lst_type, rewards_mode, data_loader):
        """Shared yield calculation logic."""
        base_yield = data_loader.get_base_yield(lst_type, timestamp)
        
        if lst_type == 'weeth' and rewards_mode != 'base_only':
            seasonal = data_loader.get_seasonal_rewards(timestamp, rewards_mode)
            return base_yield + seasonal
        
        return base_yield  # wstETH or weeth base_only
```

**Key**: Extract common logic, parametrize differences (token name, yield source)

---

### **32. Data File Naming Strategy** ✅

**Dynamic Data File Mapping**:
```python
# scripts/analyzers/components/data_loader.py

# Data files loaded dynamically through DataProvider configuration
# No hardcoded file paths or dates - all loaded from config
DATA_FILE_MAP = {
    'eth_spot_binance': config.get_data_file_path('eth_spot_binance'),
    'eth_spot_uniswap': config.get_data_file_path('eth_spot_uniswap'),
    'weeth_rates': config.get_data_file_path('weeth_rates'),
    'weth_rates': config.get_data_file_path('weth_rates'),
    'binance_futures': config.get_data_file_path('binance_futures'),
    'bybit_futures': config.get_data_file_path('bybit_futures'),
    'okx_futures': config.get_data_file_path('okx_futures'),
    # All file paths loaded from configuration, not hardcoded
}
```

**Rationale**: 
- Known data ranges
- Saves time (no file discovery)
- Clear and explicit

**Future**: Make configurable or auto-discover latest files

---

## 🔮 **Live Trading Architecture Considerations**

### **Transition from Backtest to Live**

**What Stays Same** ✅:
```python
# Pure calculators (NO CHANGES!)
AAVECalculator.calculate_health_factor(...)
LeverageCalculator.execute_recursive_loop(...)
StakingCalculator.get_yield(...)
# All pure math, works in backtest AND live
```

**What Changes** 🔄:
```python
# Data access (CSV → WebSocket/API)
class DataLoader:
    def __init__(self, execution_mode='backtest'):
        if execution_mode == 'backtest':
            self.data_source = CSVDataSource()
        else:  # live
            self.data_source = LiveDataSource()  # WebSocket, REST API
    
    async def get_spot_price(self, asset, timestamp):
        return await self.data_source.get_price(asset, timestamp)

# Event timing (atomic → real time)
class EventLogger:
    def log_event(self, event_type, **kwargs):
        if self.execution_mode == 'backtest':
            # Single timestamp, immediate completion
            event = {'timestamp': trigger_time, 'status': 'completed'}
        else:  # live
            # Dual timestamp, track status
            event = {'trigger_timestamp': now(), 'status': 'pending'}

# Position tracking (simulated → real balances)
class PositionTracker:
    async def get_wallet_balance(self, token):
        if self.execution_mode == 'backtest':
            return self.simulated_balance[token]
        else:  # live
            return await self.web3_wallet.get_balance(token)
```

**Key Principle**: Calculators pure, components abstract I/O

---

### **Storage Strategy**

**Backtest** (Current):
- Data: CSV files
- Results: JSON + CSV files
- Plots: Plotly HTML files
- Events: CSV file

**Live** (Future):
- Data: PostgreSQL or TimescaleDB
- Results: Database + Redis cache
- Plots: Generated on-demand
- Events: Database with indexed queries

**Migration Path**:
```python
# Abstract storage
class ResultStore:
    async def save_results(self, results):
        if self.mode == 'backtest':
            # Save to CSV files
            pd.DataFrame(results).to_csv(...)
        else:  # live
            # Save to database
            await self.db.insert_results(results)
```

---

### **Real-Time Data Requirements**

**For Live Trading (Future)**:
- WebSocket: Binance/Bybit perpetual prices (real-time)
- REST API: AAVE rates query (every block or cached hourly)
- Web3: On-chain balance queries (wallet.aWeETH, wallet.variableDebtWETH)
- WebSocket: Funding rate updates (8-hourly, but track in real-time)

**All Supported by Same Calculators**:
```python
# Backtest
hf = AAVECalculator.calculate_health_factor(
    collateral_value=csv_data['collateral_value'],
    debt_value=csv_data['debt_value'],
    liquidation_threshold=0.95
)

# Live
hf = AAVECalculator.calculate_health_factor(
    collateral_value=await query_aave_position(),
    debt_value=await query_aave_debt(),
    liquidation_threshold=0.95
)
```

**Same calculator, different data sources!**

---

## 📋 **Rebalancing Specification**

**From FINAL_FIXES_SPECIFICATION.md** (Phase 4 - Future):

### **Rebalancing Triggers**

**Priority 1: Margin Ratio** (Most Critical)
```python
if margin_ratio < 0.20:  # Below 20%
    trigger = 'MARGIN_URGENT'
    action = 'Add significant margin from AAVE'
    target_ratio = 1.0  # Restore to 100%
```

**Priority 2: Delta Drift**
```python
if abs(delta_pct) > 5.0:  # More than 5% drift
    trigger = 'DELTA_REHEDGE'
    action = 'Adjust perp size to match AAVE position'
```

**Priority 3: Health Factor**
```python
if health_factor < 1.10:  # Below safe threshold
    trigger = 'HF_RISK'
    action = 'Reduce AAVE leverage only'
```

### **Rebalancing Actions**

**Margin Support** (Most Common):
```python
# When ETH rises, shorts lose money, need margin
1. Atomic deleverage AAVE (flash loan)
2. Free up ETH from position
3. Transfer ETH to Binance
4. Sell ETH for USDT (spot)
5. Reduce perp short proportionally
6. Transfer excess to other CEXs if needed
```

**Delta Adjustment** (Periodic):
```python
# When AAVE position grows from yields
# Need to increase hedge proportionally
1. Calculate additional hedge needed
2. Open additional perp shorts (no AAVE change)
3. Use margin already at CEX
```

**Emergency Deleverage** (Rare):
```python
# When health factor too low
1. Reduce AAVE position significantly
2. Don't touch perps (creates delta exposure)
3. Accept delta risk to preserve AAVE safety
```

### **Costs & Frequency**

**Per Rebalance**:
- Atomic mode: ~$30-50 (gas + execution)
- Sequential mode: ~$80-120

**Frequency** (Historical Est.):
- Low volatility: 1-2x/month
- High volatility: 2-3x/week

**Implementation**: Phase 4+ (~400-500 lines)

### **33. Config Validation: Fail-Fast, No Silent Defaults** ✅

**Decision**: Do NOT use `.get('value', 'fallback')` pattern for config access

**Rationale**:
- Silent defaults hide typos in config keys
- Makes debugging harder (why isn't my config working?)
- Explicit failures better than silent wrong behavior

**Pattern**:
```python
# ❌ AVOID (silent failure on typo)
lst_type = config.get('lst_type', 'weeth')  # Typo: 'lts_type' → silently uses 'weeth'

# ✅ PREFER (explicit failure)
lst_type = config['lst_type']  # Typo → KeyError with clear message

# ✅ ACCEPTABLE (when genuinely optional)
for venue in ['binance', 'bybit', 'okx']:
    balance = exposures.get(f'{venue}_USDT', {}).get('exposure_usd', 0)
    # OK: We expect some venues won't have this exposure
```

**Exceptions** (When `.get()` is OK):
- Looping through data where some items may not exist
- Optional features with documented defaults
- Mode-specific fields that don't apply to all modes

**Enforcement**: Code review, linting rule

### **39. Configuration Architecture: YAML-Based Mode System** ✅

**Decision**: Use YAML-based configuration with mode-specific files and centralized loading

**Structure**:
```
configs/
├── modes/           # Strategy mode configurations (YAML) - 6 modes
├── venues/          # Venue configurations (YAML) - 8 venues  
├── share_classes/   # Share class configurations (YAML) - 2 classes
└── scenarios/       # Scenario configurations (YAML) - NOT YET IMPLEMENTED
```

**Mode Configuration Files**:
- `btc_basis.yaml` - BTC basis trading with hedging
- `eth_leveraged.yaml` - ETH leveraged staking with LST rewards
- `eth_staking_only.yaml` - ETH staking without leverage
- `pure_lending.yaml` - Simple USDT lending to AAVE
- `usdt_market_neutral.yaml` - Full leveraged restaking with hedging
- `usdt_market_neutral_no_leverage.yaml` - Market neutral without leverage

**Share Class Files**:
- `usdt_stable.yaml` - USDT-denominated share class
- `eth_directional.yaml` - ETH-denominated share class

**Venue Files**:
- `aave_v3.yaml` - AAVE v3 protocol configuration
- `alchemy.yaml` - Alchemy RPC provider
- `binance.yaml` - Binance exchange
- `bybit.yaml` - Bybit exchange
- `etherfi.yaml` - EtherFi staking protocol
- `lido.yaml` - Lido staking protocol
- `morpho.yaml` - Morpho flash loan protocol
- `okx.yaml` - OKX exchange

**Configuration Loading Architecture**:
- **Centralized Loading**: All config loaded from `backend/src/basis_strategy_v1/infrastructure/config/`
- **BacktestService Integration**: Uses `config_loader.py` for dynamic configuration loading
- **Component Access**: Components receive validated config dicts from infrastructure layer
- **Fail-Fast Validation**: Components use direct config access (no .get() patterns)
- **Environment Overrides**: Environment variables override YAML values
- **Health Monitoring**: Components register with config health checker

**Status**: ✅ Implemented and documented

---

### **34. Exposure Monitor Outputs** ✅

**Decision**: Report net delta at multiple granularities

**Outputs**:
```python
{
    'net_delta_eth': -5.118,              # Total net delta
    'erc20_wallet_net_delta_eth': +3.104, # On-chain only (AAVE + wallet)
    'cex_wallet_net_delta_eth': -8.222,   # Off-chain only (CEX balances + perps)
    # erc20 + cex = total
}
```

**Rationale**:
- Downstream components need both views
- Helps diagnose on-chain vs off-chain imbalances
- Useful for rebalancing decisions (which venue to adjust)

### **40. BacktestService Configuration Integration** ✅

**Decision**: BacktestService must use existing config infrastructure for dynamic configuration loading

**Implementation**: BacktestService._create_config() now uses config_loader.py infrastructure

**Fixed Implementation**:
```python
def _create_config(self, request: BacktestRequest) -> Dict[str, Any]:
    """Create configuration using existing config infrastructure."""
    from ...infrastructure.config.config_loader import get_config_loader
    
    # Get config loader
    config_loader = get_config_loader()
    
    # Load base config for the mode
    mode = self._map_strategy_to_mode(request.strategy_name)
    base_config = config_loader.get_complete_config(mode=mode)
    
    # Apply user overrides
    if request.config_overrides:
        base_config = self._deep_merge(base_config, request.config_overrides)
    
    # Add request-specific overrides
    base_config.update({
        'share_class': request.share_class,
        'initial_capital': float(request.initial_capital),
        'backtest': {
            'start_date': request.start_date.isoformat(),
            'end_date': request.end_date.isoformat(),
            'initial_capital': float(request.initial_capital)
        }
    })
    
    return base_config
```

**Benefits**:
- Uses existing YAML configs from configs/modes/*.yaml
- Validates config via config_validator.py
- Supports environment variable overrides
- Consistent with rest of system
- Uses dynamic configuration loading from YAML files

**Status**: ✅ Implemented and documented

---

### **41. Component Data Flow Architecture** ✅

**Decision**: Standardized data passing patterns between components with config infrastructure integration

**Data Flow Pattern**:
```python
# BacktestService → EventDrivenStrategyEngine
config = self._create_config(request)  # Uses config infrastructure
strategy_engine = EventDrivenStrategyEngine(config)
result = await strategy_engine.run_backtest(
    start_date=request.start_date.isoformat(),
    end_date=request.end_date.isoformat(),
    initial_capital=request.initial_capital  # Pass initial capital
)

# EventDrivenStrategyEngine Data Loading
data = await self.data_provider._load_data_for_mode()  # Correct method name

# Component Data Access Pattern
market_data = data_row.to_dict()  # Current market data for timestamp

# Pass to components that need market data:
exposure = await self.exposure_monitor.calculate_exposure(
    timestamp=timestamp,
    position_snapshot=positions,
    market_data=market_data  # Pass market data
)

risk = await self.risk_monitor.assess_risk(
    exposure=exposure,
    market_data=market_data  # Pass market data for risk calculations
)

# Strategy decisions use exposure + risk + config (no direct market data needed)
decision = await self.strategy_manager.make_strategy_decision(
    exposure=exposure,
    risk=risk,
    config=self.config
)

# PnL calculation only needs exposure (saves own previous state)
pnl = await self.pnl_calculator.calculate_pnl(
    current_exposure=exposure,
    previous_exposure=previous_exposure,
    timestamp=timestamp
)
```

**Component Data Requirements**:

**DataProvider**: Loads all data in `_load_data_for_mode()`
- Market prices, AAVE rates, LST prices, gas costs, etc.

**PositionMonitor**: Gets initial capital + share class
- Sets USDT or ETH balance based on mode

**ExposureMonitor**: Gets market data for current timestamp
- Calculates current exposure using market prices

**RiskMonitor**: Gets market data for risk calculations
- AAVE risk params, oracle prices, margin calculations

**StrategyManager**: Uses exposure + risk + config
- No direct market data needed (decisions based on current state)

**PnLCalculator**: Uses exposure only
- Saves own previous P&L state, no external data needed

**Execution Managers**: Get market data for pricing
- Check execution against current market prices

**Status**: ✅ Implemented and documented

---

### **42. Config Infrastructure Components** ✅

**Decision**: Centralized configuration infrastructure with health monitoring and validation

**Infrastructure Components**:

**ConfigLoader** (`config_loader.py`):
- Centralized loading of all YAML and JSON configs
- Caching for performance
- Environment variable overrides
- Deep merging of config hierarchies

**ConfigValidator** (`config_validator.py`):
- Validates all configuration files at startup
- Business logic validation (mode consistency, parameter dependencies)
- Environment variable validation
- Fail-fast approach with detailed error messages

**HealthChecker** (`health_check.py`):
- Component health monitoring
- Config version tracking
- Dependency validation
- System health status reporting

**Settings** (`settings.py`):
- Legacy compatibility layer
- Environment-specific config loading
- Cached settings access

**StrategyDiscovery** (`strategy_discovery.py`):
- Strategy file discovery and validation
- Mode-to-file mapping
- Strategy filtering by share class and risk level

**Integration Pattern**:
```python
# Backend components use config infrastructure
from ...infrastructure.config.config_loader import get_config_loader
from ...infrastructure.config.health_check import register_component

# Load config
config_loader = get_config_loader()
config = config_loader.get_complete_config(mode=mode)

# Register component for health monitoring
register_component('strategy_manager', ['data_provider', 'risk_monitor'])

# Use config (fail-fast, no .get() patterns)
lst_type = config['lst_type']  # Raises KeyError if missing
```

**Benefits**:
- Single source of truth for all configuration
- Comprehensive validation and health monitoring
- Environment-specific overrides
- Performance optimization through caching
- Clear separation of concerns

**Status**: ✅ Implemented and documented

---

### **43. Live Trading Service Architecture** ✅

**Decision**: Create LiveTradingService to orchestrate live trading strategies, mirroring BacktestService pattern

**Service Architecture**:
```python
class LiveTradingService:
    """Service for running live trading strategies using the new component architecture."""
    
    def __init__(self):
        self.running_strategies: Dict[str, Dict[str, Any]] = {}
        self.completed_strategies: Dict[str, Dict[str, Any]] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
```

**Key Features**:
- **Request Management**: LiveTradingRequest with validation and risk limits
- **Strategy Orchestration**: Manages EventDrivenStrategyEngine lifecycle
- **Real-time Monitoring**: Heartbeat tracking, health checks, performance metrics
- **Risk Management**: Real-time risk limit checking and breach detection
- **Emergency Controls**: Emergency stop functionality with reason tracking
- **Status Tracking**: Comprehensive status and performance reporting

**Request Validation**:
```python
@dataclass
class LiveTradingRequest:
    strategy_name: str
    initial_capital: Decimal
    share_class: str
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    risk_limits: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

**Risk Limits Support**:
- `max_drawdown`: Maximum allowed drawdown (0-1)
- `max_position_size`: Maximum position size per asset
- `max_daily_loss`: Maximum daily loss limit
- Real-time breach detection and alerting

**Health Monitoring**:
- Heartbeat tracking (5-minute timeout threshold)
- Component health status reporting
- Automatic unhealthy strategy detection
- Performance metrics tracking

**Integration with EventDrivenStrategyEngine**:
```python
# Live service orchestrates the strategy engine
strategy_engine = EventDrivenStrategyEngine(config)
await strategy_engine.run_live()  # Runs in background

# Service monitors and manages the engine
await live_service.get_status(request_id)
await live_service.get_performance_metrics(request_id)
await live_service.check_risk_limits(request_id)
```

**Error Handling**:
- Component-specific error codes (LT-001 through LT-007)
- Structured error logging with context
- Graceful failure handling and recovery
- Emergency stop capabilities

**Status**: ✅ Implemented and documented

---

### **35. Deployment to GCloud** ✅

**Decision**: Support GCloud VM deployment with GCS data bucket

**Requirements**:
- Update deployment scripts (unified `deploy.sh` approach)
- Create GCS upload script for `data/` directory
- Update `env.unified` for cloud config
- Docker containers already configured

**Data Strategy**:
```bash
# Upload data to GCS
gsutil -m rsync -r data/ gs://basis-strategy-v1-data/

# On VM: Download data
gsutil -m rsync -r gs://basis-strategy-v1-data/ data/
```

**Priority**: After core implementation (Week 4+)

---

### **36. Redis Messaging Standard** ✅

**Decision**: Standardize Redis pub/sub for inter-component communication

**Patterns**:
- **Channel naming**: `{component}:{event}` (e.g., `position:updated`)
- **Key naming**: `{component}:{data_type}` (e.g., `position:snapshot`)
- **TTL**: Hourly data = 1 hour, historical = 24 hours
- **Backtest**: Optional (can run in-memory)
- **Live**: Required (real-time monitoring)

**See**: [`specs/10_REDIS_MESSAGING_STANDARD.md`](specs/10_REDIS_MESSAGING_STANDARD.md) for complete spec

---

### **37. Error Logging Standard** ✅

**Decision**: Structured logging with component-specific error codes

**Format**:
- JSON structured logs
- Error codes: `{COMPONENT}-{NUMBER}` (e.g., `POS-001`, `EXP-002`)
- Context data: Include position snapshots
- Alert thresholds: WARNING (log), ERROR (count), CRITICAL (halt)

**See**: [`specs/11_ERROR_LOGGING_STANDARD.md`](specs/11_ERROR_LOGGING_STANDARD.md) for complete spec

---

### **38. Liquidation Simulation** ✅

**Decision**: Simulate AAVE v3 liquidations in backtest

**AAVE v3 Logic**:
1. If health factor < 1, position can be liquidated
2. Liquidator repays up to 50% of debt
3. Liquidator seizes: debt_repaid × (1 + liquidation_bonus) collateral
4. Liquidation bonus: 1% for E-mode, 5-7% for normal mode

**Example**:
```python
# Liquidator repays 100 WETH debt
# Liquidator seizes 101 WETH worth of weETH (1% bonus)
# User loses 1 WETH (penalty for being liquidated)
```

**Implementation**: Risk Monitor includes simulate_liquidation() function

**See**: [`specs/03_RISK_MONITOR.md`](specs/03_RISK_MONITOR.md) for liquidation simulation logic

---

### **44. Live Trading Data Flow Integration** ✅
**Decision**: Strategy Manager receives real-time market data as input parameter

**Rationale**:
- **Unified Interface**: Same method signature for backtest and live modes
- **Real-Time Decisions**: Live trading requires current prices, funding rates, gas prices
- **Mode-Specific Logic**: Different data sources (CSV vs APIs) but same processing
- **Risk Management**: Live trading needs fresh data for accurate risk calculations

**Implementation**:
```python
# Updated method signature
async def handle_position_change(
    self,
    change_type: str,
    params: Dict,
    current_exposure: Dict,
    risk_metrics: Dict,
    market_data: Dict  # ← New parameter
) -> Dict:
```

**Market Data Structure**:
```python
market_data = {
    'eth_usd_price': 3300.50,
    'btc_usd_price': 45000.25,
    'aave_usdt_apy': 0.08,
    'perp_funding_rates': {
        'binance': {'ETHUSDT-PERP': 0.0001},
        'bybit': {'ETHUSDT-PERP': 0.0002},
        'okx': {'ETHUSDT-PERP': 0.0003}
    },
    'gas_price_gwei': 25.5,
    'timestamp': datetime.utcnow(),
    'data_age_seconds': 0
}
```

**Live Trading Orchestration**:
```python
# Live trading loop
while self.is_running:
    # 1. Get fresh market data
    market_data = await self.data_provider.get_market_snapshot()
    
    # 2. Check data freshness
    if market_data['data_age_seconds'] > 60:
        continue  # Skip stale data
    
    # 3. Make strategy decision with live data
    decision = await self.strategy_manager.handle_position_change(
        change_type='REBALANCE',
        params={},
        current_exposure=exposure,
        risk_metrics=risk,
        market_data=market_data  # ← Live data!
    )
```

**Deployment Differences**:
- **Backtest**: Historical CSV data, simulated execution
- **Live**: Real-time APIs, actual blockchain/CEX execution
- **Monitoring**: Basic metrics vs full observability stack
- **Risk**: Historical validation vs real-time circuit breakers

**See**: [`specs/05_STRATEGY_MANAGER.md`](specs/05_STRATEGY_MANAGER.md) for live trading data flow details

---

## ✅ **Final Architectural Decisions Summary**

**Total Decisions**: 44 (all approved, **CORE COMPONENTS IMPLEMENTED** ✅, critical issues remain)

| # | Decision | Choice | Reference |
|---|----------|--------|-----------|
| 1 | Approach | Component-based service architecture | All specs |
| 2 | Calculator Import | Copy to backend/math/ | REPO_INTEGRATION |
| 3 | BTC Mode | Implement with data download | REQUIREMENTS |
| 4 | Wallet Model | Single on-chain, separate CEX | Position Monitor |
| 5 | Timing | Hourly + atomic execution | Data Provider |
| 6 | Event Order | Global sequence | Event Logger |
| 7 | Live Fields | Optional (future-proof) | Event Logger |
| 8 | Leverage Loops | Atomic & sequential | OnChain Manager |
| 9 | Spot Oracle | Binance USDT | Data Provider |
| 10 | LST Oracle | AAVE oracle | Exposure Monitor |
| 11 | Seasonal Rewards | Discrete events | Staking Yields |
| 12 | Output Format | Organized + Plotly HTML | All specs |
| 13 | Data Files | Dynamic configuration loading | Data Provider |
| 14 | Share Class P&L | ETH vs USDT reporting | P&L Calculator |
| 15 | Reward Modes | base_only, base_eigen, base_eigen_seasonal | Staking Yields |
| 16 | Leverage Iterations | None/0/1/N meanings | Leverage Loop |
| 17 | Hedging Logic | ETH never, USDT always | Strategy Manager |
| 18 | Gas Debt | Track as negative ETH | Position Monitor |
| 19 | Event Logging | Full detail all modes | Event Logger |
| 20 | Per-Exchange Prices | Required for accuracy | CEX Manager |
| 21 | Spot Venue | Configurable, Binance default | Strategy Manager |
| 22 | CEX Allocation | User configurable | Strategy Manager |
| 23 | Atomic Bundles | Wrapper + details | Event Logger |
| 24 | USDT Entry Flow | All perps simultaneous | Strategy Manager |
| 25 | Obsolete Code | List defined | All specs |
| 26 | Balance Sheet | All modes track | Exposure Monitor |
| 27 | Config Priority | CLI overrides YAML | Config Models |
| 28 | Validation | Fail-fast, no silent defaults | ✅ **IMPLEMENTED** | **Decision 33** |
| 29 | Testing | Calculator unit tests only | REQUIREMENTS |
| 30 | Plot Format | Plotly HTML interactive | All specs |
| 31 | Documentation | Interim in claude-4.5-answers/ | README |
| 32 | Margin Thresholds | Venue constants + user buffer | Risk Monitor |
| 33 | Config Access | No .get() defaults | ✅ **IMPLEMENTED** | **All code** |
| 34 | Exposure Outputs | ERC-20 + CEX separate | Exposure Monitor |
| 35 | GCloud Deployment | GCS data bucket | REQUIREMENTS |
| 36 | Redis Messaging | Standardized pub/sub | **Decision 36** |
| 37 | Error Logging | Structured with codes | **Decision 37** |
| 38 | Liquidation Sim | AAVE v3 logic | **Decision 38** |
| 39 | Config Architecture | YAML-based mode system | **Decision 39** |
| 40 | BacktestService Config | Use config infrastructure | **Decision 40** |
| 41 | Component Data Flow | Standardized data passing patterns | **Decision 41** |
| 42 | Config Infrastructure | Centralized config with health monitoring | **Decision 42** |
| 43 | Live Trading Service | Service orchestration for live trading | **Decision 43** |
| 44 | Live Trading Data Flow | Real-time market data integration | **Decision 44** |

---

## 🚀 **Implementation Complete**

**All Decisions Made**: ✅ (44/44)  
**Architecture Complete**: ✅  
**Specifications Ready**: ✅  
**Config Infrastructure**: ✅  
**Implementation Status**: ✅ **CORE COMPONENTS COMPLETE** (critical issues remain)

**See**: [REQUIREMENTS.md](REQUIREMENTS.md) for task breakdown  
**See**: [REPO_INTEGRATION_PLAN.md](REPO_INTEGRATION_PLAN.md) for file mapping  
**See**: [specs/CONFIGURATION.md](specs/CONFIGURATION.md) for configuration management




