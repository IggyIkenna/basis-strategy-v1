# Architectural Decision Records (ADRs)

**Status**: Historical Record - Referenced by REFERENCE_ARCHITECTURE_CANONICAL.md
**Updated**: October 10, 2025
**Purpose**: Complete historical record of all architectural decisions

## Overview
This document contains the full details of all architectural decisions made for the basis-strategy-v1 platform.

**Canonical Source**: REFERENCE_ARCHITECTURE_CANONICAL.md contains principle summaries and references these detailed ADRs.

---

## ADR-001: Tight Loop Architecture Redefinition

**Date**: 2025-01-06  
**Status**: Accepted  
**Context**: The original tight loop architecture defined a monitoring cascade (position → exposure → risk → pnl) that was not being triggered and created confusion about execution flow.

**Decision**: Redefine tight loop as execution reconciliation pattern with proper full loop sequence: `execution_manager → execution_interface_manager → position_update_handler → position_monitor → reconciliation_component`

**Consequences**:
- **Positive**: Clear execution flow with position verification after each instruction
- **Positive**: Eliminates race conditions through sequential execution
- **Positive**: Proper component orchestration with Position Update Handler
- **Positive**: P&L calculated on final positions after all trades complete
- **Negative**: Major architectural change affecting all documentation
- **Negative**: Requires updating all execution interfaces

**Implementation**:
- **Full Loop** (every timestep): `time trigger → position_monitor → exposure_monitor → risk_monitor → strategy_manager → [tight loop if execution needed] → pnl_calculator → results_store`
- **Tight Loop** (only when execution happens): `execution_manager → execution_interface_manager → position_update_handler → position_monitor → reconciliation_component`
- Position Update Handler orchestrates tight loop reconciliation handshake
- Execution Manager orchestrates Execution Interface Manager which routes to venue-specific interfaces
- Execution Manager awaits reconciliation success before proceeding to next instruction
- P&L Calculator runs after tight loop to mark P&L on final positions
- Results Store runs after P&L calculation to persist results (async I/O exception)
- Loop-within-loop pattern prevents race conditions

**References**: 11_POSITION_UPDATE_HANDLER.md, 10_RECONCILIATION_COMPONENT.md

## ADR-002: Redis Removal

**Date**: 2025-01-06  
**Status**: Accepted  
**Context**: Redis was used for pub/sub messaging between components but added complexity without clear benefits in a single-threaded system.

**Decision**: Remove Redis entirely and use direct function calls for all component communication.

**Consequences**:
- **Positive**: Simplified architecture with direct function calls
- **Positive**: No external dependencies for component communication
- **Positive**: Single-threaded execution eliminates concurrency issues
- **Positive**: Easier debugging and testing
- **Negative**: No real-time pub/sub messaging capabilities
- **Negative**: All communication must be synchronous

**Implementation**:
- Remove all Redis references from documentation
- Update all components to use direct function calls
- Remove Redis configuration and environment variables
- Update health checks to not depend on Redis

## ADR-003: Reference-Based Architecture

**Date**: 2025-01-06  
**Status**: Accepted  
**Context**: Components were passing config, data_provider, and other components as runtime parameters, creating inconsistent data access patterns and potential state pollution.

**Decision**: Implement reference-based architecture where components receive all shared resources as references during initialization and never pass them as runtime parameters.

**Consequences**:
- **Positive**: Consistent data access patterns across all components
- **Positive**: No data/config passing between components
- **Positive**: Clear ownership of shared resources
- **Positive**: Easier debugging and testing
- **Negative**: Components must be initialized with all required references
- **Negative**: No dynamic component injection at runtime

**Implementation**:
- Components store references in `__init__`: `self.config`, `self.data_provider`, `self.position_monitor`, etc.
- Components use references directly: `market_data = self.data_provider.get_data(timestamp)`
- NEVER pass references as method parameters during runtime
- NEVER create own instances of config or data_provider
- All components share singleton instances via references

**References**: REFERENCE_ARCHITECTURE_CANONICAL.md section I.2

## ADR-004: Shared Clock Pattern

**Date**: 2025-01-06  
**Status**: Accepted  
**Context**: Components were advancing time independently and using different timestamps, leading to data inconsistency and potential forward-looking bias.

**Decision**: EventDrivenStrategyEngine owns the authoritative timestamp and passes it to all component method calls. Components never advance time.

**Consequences**:
- **Positive**: All components use identical data snapshots
- **Positive**: No forward-looking bias possible
- **Positive**: Deterministic execution with same timestamp → same data
- **Positive**: Easy debugging by timestamp
- **Negative**: Components cannot advance time independently
- **Negative**: All data queries must use passed timestamp

**Implementation**:
- EventDrivenStrategyEngine manages `self.current_timestamp`
- All component methods receive `timestamp: pd.Timestamp` as first parameter
- Components query data: `self.data_provider.get_data(timestamp)`
- Data provider enforces `data <= timestamp` constraint
- All components in same loop iteration use identical timestamp → identical data

**References**: 15_EVENT_DRIVEN_STRATEGY_ENGINE.md

## ADR-005: Request Isolation Pattern

**Date**: 2025-01-06  
**Status**: Accepted  
**Context**: Multiple backtest/live requests could interfere with each other through shared component state, and config overrides could pollute global configuration.

**Decision**: Each backtest/live request creates completely fresh instances of DataProvider, config slice, and all components. No state pollution between requests.

**Consequences**:
- **Positive**: Multiple concurrent requests don't interfere
- **Positive**: Config overrides isolated per request
- **Positive**: Component state isolated per request
- **Positive**: Global config stays pristine for re-slicing
- **Negative**: Higher memory usage per request
- **Negative**: Slower request initialization

**Implementation**:
- App startup: Load and validate full config once, store as immutable global
- Per request: Slice config for strategy_name mode, apply overrides to slice
- Per request: Create fresh DataProvider with mode-specific data
- Per request: Create fresh component instances with references
- Post request: Discard all instances, global config unchanged

## ADR-006: Synchronous Component Execution

**Date**: 2025-01-06  
**Status**: Accepted  
**Context**: Internal component methods were using async/await unnecessarily, adding complexity without benefits in a single-threaded system.

**Decision**: Remove async/await from all internal component methods. Keep async only for external API entry points, request queuing, and I/O operations.

**Consequences**:
- **Positive**: Simplified component execution model
- **Positive**: No async/await complexity in internal methods
- **Positive**: Synchronous while/for loops for reconciliation polling
- **Positive**: Easier debugging and testing
- **Negative**: No concurrent execution within components
- **Negative**: All internal execution must be synchronous

**Implementation**:
- Remove `async def` from all component `update_state()` and internal methods
- Remove `await` from all inter-component calls
- Use synchronous while/for loops for reconciliation polling
- Keep `async def` ONLY for: BacktestService.run_backtest(), LiveTradingService.start_live_trading(), request queue management

**Exceptions for I/O Operations**:

1. **Event Logger** - Async for non-blocking I/O
   - Uses `async def` for all logging methods
   - Components await: `await self.event_logger.log_event(...)`
   - Guarantees ordering through sequential awaits
   - Rationale: File/DB writes shouldn't block trading operations

2. **Results Storage** - Async with Queue Pattern
   - Uses AsyncIO queue for FIFO ordering guarantees
   - Background worker processes queue sequentially
   - Prevents race conditions under heavy load
   - Same implementation for backtest and live modes
   - Rationale: Large result sets benefit from async I/O

**Ordering Guarantees**:
- AsyncIO's single-threaded event loop prevents race conditions
- Queue ensures FIFO processing even with variable write times
- Await semantics guarantee completion before next operation
- No dropped data or out-of-order writes

**Implementation**:
- Event Logger: Direct async methods with await
- Results Store: Queue-based async with background worker
- Both follow same async pattern for consistency

## ADR-007: 11 Component Architecture

**Date**: 2025-01-06  
**Status**: Accepted  
**Context**: The system had 9 components but needed additional components for reconciliation and position update orchestration.

**Decision**: Expand to 11 components by adding Reconciliation Component and elevating Position Update Handler to full component status.

**Consequences**:
- **Positive**: Clear separation of concerns for reconciliation
- **Positive**: Position Update Handler abstracts tight loop complexity
- **Positive**: Better component organization and responsibilities
- **Negative**: Additional components to maintain
- **Negative**: More complex initialization sequence

**Implementation**:
- Add Reconciliation Component for position state validation
- Elevate Position Update Handler to full component with own specification
- Update EventDrivenStrategyEngine to handle 11 components
- Update all documentation to reflect 11 component architecture

## ADR-008: Three-Way Venue Interaction

**Date**: 2025-01-06  
**Status**: Accepted  
**Context**: Venues have different interaction types that were not clearly separated, leading to confusion about credential requirements and execution behavior.

**Decision**: Define three distinct venue interaction types: Market Data Feed (public), Order Handling (private), Position Updates (private).

**Consequences**:
- **Positive**: Clear separation of venue interaction types
- **Positive**: Different credential requirements per interaction type
- **Positive**: Backtest vs live behavior clearly defined per interaction
- **Positive**: Startup validation can test each interaction type separately
- **Negative**: More complex venue initialization logic
- **Negative**: Requires updating all venue-related documentation

**Implementation**:
- Market Data Feed: Public data, no credentials in backtest
- Order Handling: Private operations, credentials in live only
- Position Updates: Private queries, part of tight loop reconciliation
- Backtest: Simulated for all three types
- Live: Real APIs for all three types with heartbeat tests

## ADR-009: Separate Data Source from Execution Mode

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
- **Implementation tasks** → [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) <!-- Redirected from REQUIREMENTS.md - requirements are component specifications -->
- **Timeline** → [README.md](README.md) <!-- Redirected from IMPLEMENTATION_ROADMAP.md - implementation status is documented here -->
- **Configuration** → [specs/19_CONFIGURATION.md](specs/19_CONFIGURATION.md)

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
- **Caching Strategy**: In-memory support with configurable TTL
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

**Core Principle: Shared Clock Pattern**
EventDrivenStrategyEngine owns the authoritative timestamp. All components receive timestamps as parameters and query data using those exact timestamps. Components NEVER advance time.

**Constraint 1: Hourly Data Snapshots Only**
```python
# EventDrivenStrategyEngine manages current_timestamp
# All market data updates ON THE HOUR
# Valid: '2024-05-12 14:00:00'
# Invalid: '2024-05-12 14:30:00' (no data)

# All components use same timestamp → same data snapshot
def _process_timestep(self, timestamp: pd.Timestamp):
    # Pass timestamp to all components
    self.position_monitor.update_state(timestamp, 'full_loop')
    self.exposure_monitor.update_state(timestamp, 'full_loop')
    self.risk_monitor.update_state(timestamp, 'full_loop')
    
    # All components query with identical timestamp
    # market_data = self.data_provider.get_data(timestamp)
    # Returns same snapshot for all components
```

**Constraint 2: Data Provider Time Constraint**
```python
class DataProvider:
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        # Enforce data <= timestamp constraint
        filtered_data = {}
        for key, data_series in self.data.items():
            # Get latest data point <= timestamp
            filtered_data[key] = data_series[data_series.index <= timestamp].iloc[-1]
        return filtered_data
```

**Constraint 3: Atomic Event Execution Within Timestamp**
```python
# Atomic leveraged staking execution
# All 70+ events share same timestamp: '2024-05-12 00:00:00'
# Differentiated by tight loop order: 1, 2, 3, ..., 70

# Atomic flash loan (1 transaction)
# 6-7 events share same timestamp
# Differentiated by tight loop order: 1, 2, 3, 4, 5, 6

# ALL use same price snapshot (no timing risk)
# Components receive timestamp, never generate/modify it
```

**Component Behavior Requirements**:
```python
class ExampleComponent:
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
        # Receive timestamp, never generate/modify it
        market_data = self.data_provider.get_data(timestamp)
        
        # All logic uses this exact timestamp
        self.last_update_timestamp = timestamp
        
        # Process with timestamp-consistent data
        self._process_with_data(market_data, timestamp)
```

**Anti-Patterns to Avoid**:
```python
# WRONG - Component advancing time
def update_state(self, timestamp: pd.Timestamp):
    next_timestamp = timestamp + pd.Timedelta(hours=1)  # Don't advance time
    future_data = self.data_provider.get_data(next_timestamp)

# WRONG - Caching data across timestamps
def update_state(self, timestamp: pd.Timestamp):
    if not hasattr(self, '_cached_data'):
        self._cached_data = self.data_provider.get_data(timestamp)  # Don't cache
    market_data = self._cached_data

# WRONG - Using current time instead of passed timestamp
def update_state(self, timestamp: pd.Timestamp):
    current_time = pd.Timestamp.now()  # Don't use current time
    market_data = self.data_provider.get_data(current_time)
```

---

### **6. Obsolete Code Removal** ✅

**Remove**:
- ✅ USDT borrowing on AAVE for basis trade (not economical)
- ✅ Multiple ETH entry paths (standardize to atomic flash loan only)
- ✅ Fixed balance P&L mode (ETH analyzer is outdated)

**Keep**:
- ✅ Pure USDT lending mode (simple supply-only)
- ✅ WETH/ETH auto-conversion (AAVE unwraps, EtherFi accepts both)

**Clarifications**:
- ETH share class: One path (stake → AAVE leveraged staking), atomic flash loan only
- WETH/ETH: Assume protocols handle conversion, always talk in wrapped non-rebasing tokens

---

### **7. Share Class P&L Currency** ✅

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

**KING Token Handling**:
- All weETH rewards (EIGEN, ETHFI) come as KING tokens (composite wrapper)
- KING tokens count as dust and require unwrapping and selling
- See docs/KING_TOKEN_HANDLING_GUIDE.md for unwrapping flow
- No need to track KING price - it's a derivative structure mapping to ETHFI + EIGEN
- When unwrapping, track equivalent ETHFI and EIGEN amounts for P&L attribution

---

### **10. Leveraged Staking Execution** ✅

**Atomic Flash Loan Only**:
- Leveraged staking ALWAYS uses atomic flash loan (single transaction)
- Formula: Target LTV determines leverage ratio
- Entry: `borrow_flash → stake → supply_lst → borrow_aave → repay_flash`
- Exit/Unwind: `borrow_flash → withdraw_lst → swap_to_eth → repay_aave → repay_flash`
- Cost: ~$50 gas vs ~$200 for sequential
- No sequential option - atomic is always superior

**No Parameters Needed**:
- Atomic flash loan execution is deterministic based on target LTV
- No iteration limits or position size thresholds required

---

### **11. Hedging Logic** ✅

**ETH Share Class**:
- Never hedge (directional ETH exposure desired)
- Throw error if `basis_trade_enabled: true` (invalid config)

**USDT Share Class**:
- Always hedge (market-neutral required)
- Auto-enable `basis_trade_enabled` if staking enabled
- Throw error if disabled for staking strategies

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

**Key**: Same process, just different starting balance! TODO: eventually we need to ensure that the starting balance is always positive and ETH exists on teh right vanues that consume gas from the start (not important, gas is low we may do this manually)

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

**In Backtest**: Same process for alignment but in practice we will be simulating the execution so it will be simultaneous anyway (atomic execution assumption)

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

**By Request ID**:
```
results/{request_id}/
  summary.json
  hourly_pnl.csv
  event_log.csv
  balance_sheet.csv
  plots/
    cumulative_pnl.html
    pnl_components.html
    delta_neutrality.html
    margin_ratios.html
```

**Plots**: Plotly HTML (interactive), served by backend API

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
- Binance spot for absolute USD pricing (perp neutrality) and we hahve hourly pricing which we dont for aave oracle. we dont have USD pricing for uniswap
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


### **23. Rebalancing Implementation** ✅

**Strategy Manager Actions**:
- Uses 5 standardized actions from docs/MODES.md
- `entry_full`, `entry_partial`, `exit_full`, `exit_partial`, `sell_dust`
- Each breaks down into instruction blocks for Execution Manager

**Triggers**:
1. **Risk-triggered** (Priority 1): Risk Monitor detects warning/critical breach
   - LTV warning/critical (AAVE)
   - Maintenance margin warning/critical (CEX)
   - Strategy Manager unwinds to safe levels FIRST
   - Next loop iteration checks for optimal position
2. **Position-triggered** (Priority 2): Deviation from target exceeds `position_deviation_threshold`
   - Checked after risk is within safe levels
   - Uses reserve balance vs `reserve_ratio` to decide if unwinding needed

**Fast vs Slow Withdrawals**:
- Fast: Uses reserve balance (no unwinding needed)
- Slow: Requires unwinding positions (flash loan for leveraged modes)
- Decision based on: `reserve_balance / total_equity < reserve_ratio`

**No Complex Transfer Manager**:
- Removed per strategy_manager_refactor.md
- Strategy Manager calculates desired state
- Execution Manager handles venue routing

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


### **26. Validation Philosophy** ✅

**Multi-Level Validation Strategy**:

**Level 1: Schema Validation** (Pydantic)
- Field types, ranges, required fields
- Enum validation (mode, asset, lst_type)

**Level 2: Business Logic Validation**
- Share class consistency: `market_neutral` flag matches hedging requirements
- Asset consistency: BTC basis requires BTC asset, ETH modes require ETH asset
- Hedge allocation sums to 1.0
- LST type valid for strategy mode
- Reward mode valid for LST type (wstETH only supports base_only)

**Level 3: Mode-Specific Validation**
- Required fields per mode (MODE_REQUIREMENTS)
- Forbidden fields per mode
- Parameter dependencies (lending+staking requires borrowing or basis_trade for USDT)

**Level 4: Data Availability Validation**
- Required data files exist for backtest date range
- Risk parameters available (AAVE, CEX margin requirements)
- Market data coverage complete

**Level 5: Cross-Component Consistency**
- Venue configs match strategy mode venue requirements
- Warning thresholds < critical thresholds
- Position deviation threshold < 1.0
- Reserve ratio reasonable (0.05 - 0.2 range)

**Implementation**: config_validator.py with comprehensive validation functions

---

### **27. Testing Granularity** ✅

**Quality Gate Requirements**:
- MANDATORY for all components in docs/specs/
- Prevents breaking implementations during iteration
- See docs/QUALITY_GATES.md for gate categories
- Target: 80% unit/integration coverage, 100% e2e coverage

**Component Quality Gates**:
- Each spec in docs/specs/ has corresponding quality gate tests
- Integration tests validate cross-component interactions
- E2E tests validate full backtest flow per strategy mode

**Calculator Tests**: Pure math only
- Unit tests with known inputs/outputs
- Test each function independently
- 100% code coverage for calculators

**Component Tests**: Integration between components  
**Mode Tests**: End-to-end per mode  
**Backend Tests**: API integration  
**Frontend Tests**: User flows

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


### **30. Margin Ratio Thresholds** ✅

**Data Sources**:
- **Actual MMR & Liquidation Thresholds**: From `data/market_data/derivatives/risk_params/` (backtest) or queried from exchange APIs (live)
- **Warning Thresholds**: From `configs/venues/*.yaml` with optional strategy mode overrides
- Same pattern as AAVE: `data/protocol_data/aave/risk_params/aave_v3_risk_parameters.json`

**Config Merge**:
```python
# Venue default
venue_config = {
  'margin_warning_threshold': 0.20,
  'margin_critical_threshold': 0.10
}

# Optional mode override
mode_config = {
  'margin_warning_threshold': 0.25  # More conservative
}

# Merged: mode overrides venue default
final_threshold = 0.25
```

**Files**:
- `data/market_data/derivatives/risk_params/binance_margin_requirements.json`
- `data/market_data/derivatives/risk_params/bybit_margin_requirements.json`
- `data/market_data/derivatives/risk_params/okx_margin_requirements.json`

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

### **Component State Logging**

**All Components** (Position Monitor, Exposure Monitor, Risk Monitor, Strategy Manager, Execution Interfaces):

**Backtest Mode**:
```python
logger.info(f"{component_name}: State before operation", extra={
    'timestamp': timestamp,  # Same as operation timestamp
    'status': 'pending',
    'state_snapshot': self._get_state()
})

# ... operation ...

logger.info(f"{component_name}: State after operation", extra={
    'timestamp': timestamp,  # Same timestamp (simulated)
    'status': 'complete',
    'state_snapshot': self._get_state()
})
```

**Live Mode**:
```python
logger.info(f"{component_name}: State before operation", extra={
    'timestamp': datetime.now(timezone.utc),
    'status': 'pending',
    'state_snapshot': self._get_state()
})

# ... operation ...

logger.info(f"{component_name}: State after operation", extra={
    'timestamp': datetime.now(timezone.utc),  # Different timestamp (real elapsed time)
    'status': 'complete',
    'duration_ms': elapsed_time,
    'state_snapshot': self._get_state()
})
```

**Benefits**:
- Track operation duration in live mode
- Runtime logs show component state changes
- Identical structure in backtest (timestamps same) vs live (timestamps differ)

### **Transition from Backtest to Live**

**What Stays Same** ✅:
```python
# Pure calculators (NO CHANGES!)
AAVECalculator.calculate_health_factor(...)
LeverageCalculator.execute_atomic_leverage(...)
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

**Phase 1 (MVP - Live Trading)**:
- CSV files for simplicity
- Same format as backtest
- Easy debugging and inspection
- Results written to `results/{request_id}/`

**Future (Phase 2+)**:
- Database for scalability
- Time-series optimization
- Query performance for analytics

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

**References**: 19_CONFIGURATION.md

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

**Aligned with Canonical Patterns**:
- **Shared Clock Pattern** (docs/SHARED_CLOCK_PATTERN.md): EventDrivenStrategyEngine owns timestamp, passes to all components
- **Reference-Based Architecture** (docs/REFERENCE_ARCHITECTURE_CANONICAL.md): Components store config, data_provider, other component references at init
- **Request Isolation Pattern** (docs/REQUEST_ISOLATION_PATTERN.md): Fresh instances per backtest/live request

**Data Flow**:
```python
# EventDrivenStrategyEngine manages timestamp
for timestamp in self.timestamps:
    self.current_timestamp = timestamp
    
    # All components receive same timestamp
    self.position_monitor.update_state(timestamp, 'full_loop')
    self.exposure_monitor.update_state(timestamp, 'full_loop') 
    self.risk_monitor.update_state(timestamp, 'full_loop')
    self.pnl_calculator.update_state(timestamp, 'full_loop')
    
    # Components query data with timestamp
    # market_data = self.data_provider.get_data(timestamp)
    # Ensures all components see identical data snapshot
```

**Component References** (stored at init, never passed as runtime params):

```python
class ExampleComponent:
    def __init__(self, config, data_provider, execution_mode, position_monitor=None):
        self.config = config  # Reference, never modified
        self.data_provider = data_provider  # Query with timestamps
        self.execution_mode = execution_mode  # 'backtest' or 'live'
        self.position_monitor = position_monitor  # Reference
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
        # Use stored references directly
        market_data = self.data_provider.get_data(timestamp)
        position = self.position_monitor.get_current_position()
```

**See**: docs/WORKFLOW_GUIDE.md for complete flow, docs/SHARED_CLOCK_PATTERN.md for timestamp management

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

### **36. Component Communication Standard** ✅

**Decision**: Use direct method calls for inter-component communication

**Patterns**:
- **Direct method calls**: Components call each other's methods directly
- **Synchronous execution**: No network overhead, immediate response
- **In-memory state**: All state maintained in component memory
- **Backtest**: Single-threaded, synchronous execution
- **Live**: Same pattern, no architectural changes needed

**See**: Component specifications for direct method call patterns

---

### **37. Error Logging Standard** ✅

**Decision**: Structured logging with component-specific error codes

**Format**:
- JSON structured logs
- Error codes: `{COMPONENT}-{NUMBER}` (e.g., `POS-001`, `EXP-002`)
- Context data: Include position snapshots
- Alert thresholds: WARNING (log), ERROR (count), CRITICAL (halt)

**See**: [`specs/17_HEALTH_ERROR_SYSTEMS.md`](specs/17_HEALTH_ERROR_SYSTEMS.md) <!-- Redirected from 11_ERROR_LOGGING_STANDARD.md - error logging is part of health systems --> for complete spec

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

**Total Decisions**: 44 (all approved, **CORE COMPONENTS IMPLEMENTED** ✅, documentation aligned)

| # | Decision | Choice | Reference |
|---|----------|--------|-----------|
| 1 | Approach | Component-based service architecture | All specs |
| 2 | Calculator Import | Copy to backend/math/ | REPO_INTEGRATION |
| 3 | BTC Mode | Implement with data download | REQUIREMENTS |
| 4 | Wallet Model | Single on-chain, separate CEX | Position Monitor |
| 5 | Timing | Hourly + atomic execution | Data Provider |
| 6 | Event Order | Global sequence | Event Logger |
| 7 | Live Fields | Optional (future-proof) | Event Logger |
| 8 | Leveraged Staking | Atomic flash loan only | OnChain Manager |
| 9 | Spot Oracle | Binance USDT | Data Provider |
| 10 | LST Oracle | AAVE oracle | Exposure Monitor |
| 11 | Seasonal Rewards | Discrete events | Staking Yields |
| 12 | Output Format | Organized + Plotly HTML | All specs |
| 13 | Data Files | Dynamic configuration loading | Data Provider |
| 14 | Share Class P&L | ETH vs USDT reporting | P&L Calculator |
| 15 | Reward Modes | base_only, base_eigen, base_eigen_seasonal | Staking Yields |
| 16 | Leverage Execution | Atomic flash loan only | Leveraged Staking |
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
| 36 | Component Communication | Direct method calls | **Decision 36** |
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
**Documentation Aligned**: ✅  
**Implementation Status**: ✅ **CORE COMPONENTS IMPLEMENTED** | ✅ **DOCUMENTATION ALIGNED** | 🔄 **LIVE MODE IMPLEMENTATION IN PROGRESS**

**See**: [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) <!-- Redirected from REQUIREMENTS.md - requirements are component specifications --> for task breakdown  
**See**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) <!-- Redirected from REPO_INTEGRATION_PLAN.md - integration is deployment --> for file mapping  
**See**: [specs/19_CONFIGURATION.md](specs/19_CONFIGURATION.md) for configuration management

## ADR-052: Config-Driven Mode-Agnostic Components

**Date**: 2025-10-11  
**Status**: Accepted  
**Context**: Components were using hardcoded mode-specific if/else logic, making them difficult to reuse across different strategy modes and creating maintenance overhead.

**Decision**: Components use `component_config` from mode YAML to determine behavior instead of mode-specific if/else logic. This enables mode-agnostic components that work identically across all 7 strategy modes.

**Consequences**:
- **Positive**: Components become reusable across all strategy modes
- **Positive**: Modes defined purely in YAML configuration
- **Positive**: Easier testing with config-driven behavior
- **Positive**: No hardcoded mode logic in components
- **Negative**: Requires comprehensive config schemas for all modes
- **Negative**: Components must handle missing data gracefully

**Implementation**:
- Components extract behavior from `config.get('component_config', {}).get('component_name', {})`
- No mode checks: `if mode == 'pure_lending'` → Use config parameters instead
- Graceful data handling: Return None/0 when required data unavailable
- All behavior controlled by configuration parameters

**References**: 19_CONFIGURATION.md, CODE_STRUCTURE_PATTERNS.md sections 2-4

## ADR-053: DataProvider Factory with Data Requirements Validation

**Date**: 2025-10-11  
**Status**: Accepted  
**Context**: Different strategy modes need completely different data subscriptions (pure lending vs market neutral), but there was no validation that DataProviders could satisfy mode requirements.

**Decision**: Mode-specific DataProviders validate `data_requirements` from config at initialization, ensuring fail-fast behavior when data cannot be provided.

**Consequences**:
- **Positive**: Fail-fast on missing data requirements
- **Positive**: Clear data contracts per mode
- **Positive**: Prevents runtime data errors
- **Positive**: Explicit data requirements in config
- **Negative**: Requires comprehensive data requirement definitions
- **Negative**: DataProvider creation can fail at startup

**Implementation**:
- Each mode specifies `data_requirements: ["data_type_1", "data_type_2"]`
- DataProviderFactory validates provider can satisfy all requirements
- Provider.validate_data_requirements() raises ValueError if missing
- Clear error messages for missing data types

**References**: 09_DATA_PROVIDER.md, 19_CONFIGURATION.md data_requirements section

## ADR-054: Graceful Data Handling in Components

**Date**: 2025-10-11  
**Status**: Accepted  
**Context**: Not all strategy modes have all data types (e.g., pure lending has no perp data), but components were failing when required data was unavailable.

**Decision**: Components return None/0 for calculations when required data is unavailable, enabling them to work across modes with different data subscriptions.

**Consequences**:
- **Positive**: Components work across all modes regardless of data availability
- **Positive**: No crashes on missing data
- **Positive**: Graceful degradation of functionality
- **Positive**: Mode-agnostic component behavior
- **Negative**: Components must handle None/0 values in calculations
- **Negative**: Potential for silent failures if not handled properly

**Implementation**:
- Check data availability before calculations: `if 'perp_prices' in data.get('protocol_data', {}):`
- Return None for missing data: `results[item] = None`
- Return 0 for numeric calculations when data unavailable
- Log warnings for missing data in debug mode

**References**: CODE_STRUCTURE_PATTERNS.md sections 2-4, component specs

## ADR-055: Component Factory with Config Validation

**Date**: 2025-10-11  
**Status**: Accepted  
**Context**: Components were being created without validating that they received valid configuration, leading to runtime errors and unclear failure modes.

**Decision**: ComponentFactory validates `component_config` before creating component instances, ensuring fail-fast behavior on configuration errors.

**Consequences**:
- **Positive**: Fail-fast on config errors at startup
- **Positive**: Clear config contracts for each component
- **Positive**: Prevents runtime configuration errors
- **Positive**: Explicit validation of required config fields
- **Negative**: Component creation can fail at startup
- **Negative**: Requires comprehensive config validation rules

**Implementation**:
- ComponentFactory validates required fields for each component
- Check component-specific config completeness
- Validate config parameter values and types
- Raise ValueError with clear error messages for missing/invalid config

**References**: CODE_STRUCTURE_PATTERNS.md section 10, 19_CONFIGURATION.md

## ADR-056: Core vs Supporting Components Architecture

**Date**: 2025-10-11  
**Status**: Accepted  
**Context**: The system had 20+ components but no clear distinction between runtime execution components and supporting infrastructure, making architecture understanding difficult.

**Decision**: Organize components into 11 core components (runtime data/decision/execution flow) and 9 supporting components (services, utilities, infrastructure).

**Consequences**:
- **Positive**: Clear architecture boundaries
- **Positive**: Easier onboarding and understanding
- **Positive**: Clear separation of runtime vs infrastructure concerns
- **Positive**: Better component organization
- **Negative**: Requires updating all documentation references
- **Negative**: May need to adjust component counts in various places

**Implementation**:
- **Core Components (11)**: Position Monitor, Exposure Monitor, Risk Monitor, PnL Calculator, Strategy Manager, Execution Manager, Execution Interface Manager, Reconciliation Component, Position Update Handler, Event Logger, Data Provider
- **Supporting Components (9)**: Backtest Service, Live Trading Service, Event Driven Strategy Engine, Execution Interfaces, Execution Interface Factory, Strategy Factory, Math Utilities, Health & Error Systems, Results Store, Configuration

**References**: COMPONENT_SPECS_INDEX.md, all component specs

## Decision Index

| ADR | Title | Date | Status | Impact |
|-----|-------|------|--------|--------|
| ADR-001 | Tight Loop Architecture Redefinition | 2025-01-06 | Accepted | High |
| ADR-002 | Redis Removal | 2025-01-06 | Accepted | Medium |
| ADR-003 | Reference-Based Architecture | 2025-01-06 | Accepted | High |
| ADR-004 | Shared Clock Pattern | 2025-01-06 | Accepted | High |
| ADR-005 | Request Isolation Pattern | 2025-01-06 | Accepted | High |
| ADR-006 | Synchronous Component Execution | 2025-01-06 | Accepted | Medium |
| ADR-007 | 11 Component Architecture | 2025-01-06 | Accepted | Medium |
| ADR-008 | Three-Way Venue Interaction | 2025-01-06 | Accepted | Medium |
| ADR-009 | Separate Data Source from Execution Mode | 2025-01-09 | Accepted | Medium |
| ADR-010 | Configuration Separation of Concerns | 2025-01-06 | Accepted | High |
| ADR-011 | Live Data Provider Architecture | 2025-01-06 | Accepted | High |
| ADR-012 | Execution Interface Architecture | 2025-01-06 | Accepted | High |
| ADR-013 | Calculator Import Strategy | 2025-01-06 | Accepted | Medium |
| ADR-014 | BTC Mode Implementation | 2025-01-06 | Accepted | Medium |
| ADR-015 | Wallet/Venue Model | 2025-01-06 | Accepted | High |
| ADR-016 | Backtest Timing Constraints | 2025-01-06 | Accepted | High |
| ADR-017 | Obsolete Code Removal | 2025-01-06 | Accepted | Low |
| ADR-018 | Share Class P&L Currency | 2025-01-06 | Accepted | Medium |
| ADR-019 | Reward Modes for weETH | 2025-01-06 | Accepted | Medium |
| ADR-020 | Leveraged Staking Execution | 2025-01-06 | Accepted | High |
| ADR-021 | Hedging Logic | 2025-01-06 | Accepted | Medium |
| ADR-022 | Gas Debt Accounting | 2025-01-06 | Accepted | Medium |
| ADR-023 | Event Logging Detail | 2025-01-06 | Accepted | Low |
| ADR-024 | Per-Exchange Price Tracking | 2025-01-06 | Accepted | Medium |
| ADR-025 | Spot Venue Selection | 2025-01-06 | Accepted | Low |
| ADR-026 | CEX Hedge Allocation | 2025-01-06 | Accepted | Low |
| ADR-027 | Output File Structure | 2025-01-06 | Accepted | Low |
| ADR-028 | Seasonal Reward Distribution | 2025-01-06 | Accepted | Medium |
| ADR-029 | Data File Naming | 2025-01-06 | Accepted | Low |
| ADR-030 | Pricing Oracle Strategy | 2025-01-06 | Accepted | Medium |
| ADR-031 | Live Trading Architecture | 2025-01-06 | Accepted | High |
| ADR-032 | Rebalancing Implementation | 2025-01-06 | Accepted | High |
| ADR-033 | Balance Sheet Tracking | 2025-01-06 | Accepted | Medium |
| ADR-034 | Validation Philosophy | 2025-01-06 | Accepted | High |
| ADR-035 | Testing Granularity | 2025-01-06 | Accepted | Medium |
| ADR-036 | Plot Format | 2025-01-06 | Accepted | Low |
| ADR-037 | Margin Ratio Thresholds | 2025-01-06 | Accepted | Medium |
| ADR-038 | Shared Calculator Logic | 2025-01-06 | Accepted | Medium |
| ADR-039 | Data File Naming Strategy | 2025-01-06 | Accepted | Low |
| ADR-040 | Config Validation: Fail-Fast | 2025-01-06 | Accepted | High |
| ADR-041 | Configuration Architecture | 2025-01-06 | Accepted | High |
| ADR-042 | Exposure Monitor Outputs | 2025-01-06 | Accepted | Medium |
| ADR-043 | BacktestService Configuration | 2025-01-06 | Accepted | High |
| ADR-044 | Component Data Flow Architecture | 2025-01-06 | Accepted | High |
| ADR-045 | Config Infrastructure Components | 2025-01-06 | Accepted | High |
| ADR-046 | Live Trading Service Architecture | 2025-01-06 | Accepted | High |
| ADR-047 | Deployment to GCloud | 2025-01-06 | Accepted | Medium |
| ADR-048 | Component Communication Standard | 2025-01-06 | Accepted | Medium |
| ADR-049 | Error Logging Standard | 2025-01-06 | Accepted | Medium |
| ADR-050 | Liquidation Simulation | 2025-01-06 | Accepted | Medium |
| ADR-051 | Live Trading Data Flow Integration | 2025-01-06 | Accepted | High |
| ADR-052 | Config-Driven Mode-Agnostic Components | 2025-10-11 | Accepted | High |
| ADR-053 | DataProvider Factory with Data Requirements Validation | 2025-10-11 | Accepted | High |
| ADR-054 | Graceful Data Handling in Components | 2025-10-11 | Accepted | High |
| ADR-055 | Component Factory with Config Validation | 2025-10-11 | Accepted | High |
| ADR-056 | Core vs Supporting Components Architecture | 2025-10-11 | Accepted | High |
