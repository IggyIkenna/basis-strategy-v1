# Strategy Modes Specification

## Overview

This document provides comprehensive specifications for all strategy modes in the basis-strategy-v1 platform. Each mode represents a distinct investment strategy with specific risk profiles, yield sources, and execution requirements.

## 📚 **Canonical Sources**

- **Instrument Definitions**: [INSTRUMENT_DEFINITIONS.md](INSTRUMENT_DEFINITIONS.md) - Canonical position key format (`venue:position_type:symbol`)
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions (this document)
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

## Core Principles

### Share Class Architecture
- **USDT Share Class**: Market-neutral strategies, P&L in USDT
- **ETH Share Class**: Directional strategies, P&L in ETH
- Config field: `market_neutral: true/false` in share class config

### Config-Driven Component Architecture
Components use `component_config` to determine behavior:
- **Mode-Agnostic**: Position/Exposure/Risk/PnL monitors work across all modes
- **Mode-Specific**: Strategy Manager has mode-specific logic via inheritance
- **Data Requirements**: Each mode specifies `data_requirements` list
- **Component Configs**: Each mode has `component_config` dict for all components

See: 19_CONFIGURATION.md for complete mode configs, REFERENCE_ARCHITECTURE_CANONICAL.md for architecture patterns.

**ADR References**: ADR-052 (config-driven components), ADR-056 (component architecture)

### Testing Patterns and Instrument Key Formats

**Updated October 18, 2025** - Based on comprehensive test suite validation:

#### Instrument Key Format Standards
- **Canonical Format**: `venue:position_type:symbol` (e.g., `aave_v3:aToken:aUSDT`)
- **Position Keys**: Use full instrument keys in `calculate_target_position()` returns
- **Test Expectations**: Tests must match actual strategy return formats, not simplified keys

#### Multi-Venue Strategy Patterns
- **Pure Lending Strategies**: Create orders for AAVE only (no Morpho lending data available)
- **Flash Loan Strategies**: Use Morpho for atomic leveraged staking operations only
- **Order Creation**: Each venue gets separate orders with venue-specific instrument keys
- **Test Mocking**: Position monitors must be mocked for exit order tests
- **Venue Names**: Use actual venue names (`aave_v3`, `morpho`) not enum values

#### Strategy-Specific Patterns
- **ETH Staking**: Returns `etherfi:BaseToken:WEETH` not `weeth_balance`
- **ML Strategies**: Require `signal` parameter for order creation methods
- **Leveraged Strategies**: Require `target_ltv` parameter for order creation
- **Basis Strategies**: Use allocation factors (e.g., `btc_allocation: 0.8`)

#### Error Message Patterns
- **Instrument Validation**: "Required instrument X not in position_subscriptions" (not "Invalid format")
- **Method Signatures**: `generate_orders(timestamp, exposure, risk_assessment, market_data)` + optional `pnl`
- **Logging**: Use `self.logger.error(message, error_code, exc_info, **context)` not `self.log_error()`

### Execution Venue Mapping
**Venue Selection Rules**:
- **Spot Trades**: Binance spot (preferred) unless part of atomic on-chain transaction (then DEX)
- **Wallet Transfers**: Always on-chain via Alchemy (Web3 wrapper)
- **Lending/Borrowing**: Currently AAVE (extensible to other venues like Compound)
- **Flash Loans**: Morpho (via Instadapp middleware) for atomic leverage operations
- **Perp Shorts**: CEX venues based on `hedge_allocation` ratios (0 = skip venue)
- **Staking/Unstaking**: Lido or EtherFi based on `lst_type` configuration

**Available Venues**:
- **CEX**: Binance, Bybit, OKX (spot + perps)
- **DeFi**: AAVE V3, Lido, EtherFi
- **Flash Loans**: Morpho (via Instadapp middleware for atomic leveraged staking only)
- **Infrastructure**: Alchemy (Web3), Uniswap (DEX swaps), Instadapp (atomic transaction middleware)

### Capital Allocation Logic

**Strategy Constraints Determine Capital Allocation**:

**No Locked Capital Strategies** (`borrowing_enabled: false` + `lending_enabled: false` + `staking_enabled: false`):
- **BTC Basis**: All capital available for spot + perp positions
- **No maintenance margin issues**: Can use all BTC for perp shorts
- **No cross-venue issues**: No locked capital on AAVE or staking protocols

**Locked Capital Strategies** (`staking_enabled: true` + `share_class != asset`):
- **Must reserve capital for perp margin**: Cannot use LST as CEX collateral
- **USDT Market Neutral modes**: Use `stake_allocation_percentage` to split equity
  - `stake_allocation_percentage`: Proportion for ETH staking (locked on-chain)
  - `1 - stake_allocation_percentage`: Proportion for CEX margin (in USDT)
- **Why USDT margin**: Forces P&L to move in equally offsetting directions
  - CEX gains when on-chain loses (in USDT terms)
  - If used ETH as margin, would create long ETH delta distortion

**Directional Strategies** (`share_class == asset` + `staking_enabled: true`):
- **ETH Leveraged/Staking Only**: No hedging required
- **All capital can be staked**: No need to reserve for perp margin
- **No cross-venue capital allocation**: Single venue focus

### Execution Modes

**Execution Modes**:
- **Atomic Transactions**: Via Instadapp middleware for complex multi-step operations (leveraged staking)
- **Sequential Transactions**: Direct API calls to individual venues (Lido, AAVE, etc.) for simple operations
- **Leveraged Staking**: Always use atomic flash loan execution for efficiency

**Withdrawal Handling**:
- **All strategies unwind 1:1 with withdrawals** (no exceptions)
- **Immediate processing**: Withdrawals processed immediately if free equity available
- **Complex unwinding**: Only required for unstaking and/or unwinding basis trades

### Standardized Strategy Manager Architecture

**PLANNED ARCHITECTURE**: Inheritance-based strategy modes with standardized wrapper actions (per strategy_manager_refactor.md)

**Base Strategy Manager**:
- **Equity Tracking**: Always track equity in share class currency (assets net of debt, excluding futures positions)
- **Target Position Calculation**: Compare current position to desired position based on equity
- **Position Deviation Threshold**: Only trigger rebalancing when deviation exceeds `position_deviation_threshold` (default 2%)
- **Standardized Actions**: All strategies use 5 wrapper actions:
  1. `entry_full`: Enter full position (initial setup or large deposits)
  2. `entry_partial`: Scale up position (small deposits or PnL gains)
  3. `exit_full`: Exit entire position (withdrawals or risk override)
  4. `exit_partial`: Scale down position (small withdrawals or risk reduction)
  5. `sell_dust`: Convert non-share-class tokens to share class currency
- **Tight Loop Integration**: Strategy manager triggers tight loop after position updates
- **Centralized Utilities**: All utility methods accessed through centralized utility manager
- **Event Engine Integration**: Proper integration with EventDrivenStrategyEngine for consistent event handling

**Strategy Inheritance**:
- Each strategy mode inherits from BaseStrategyManager
- Implements mode-specific logic for the 5 wrapper actions
- Strategy mode passed via API endpoint (backtest/live mode)
- **Strategy Factory**: Creates strategy instances based on mode
- Fixed wallet assumption: All deposits/withdrawals go to same on-chain wallet

**Risk Management Integration**:
- **Risk Monitor**: Manages venue-specific risks (strategy agnostic)
- **Circuit Breaker**: Risk assessment triggers override actions (bypasses normal rebalancing)
- **Risk Override**: Only tells strategy to reduce position, never to enter desired position
- **Centralized Risk**: Deterministic, centralized risk management across all strategies
- **Tight Loop Integration**: Risk monitor part of mandatory sequential component chain
- **Event Engine Integration**: Risk events properly integrated with EventDrivenStrategyEngine

---

## Strategy Mode Specifications

**Note**: There are 9 YAML configs and 9 documented strategies. All strategy modes are documented below.

### 1. Pure Lending Mode (`pure_lending_usdt`)

**Objective**: Simple USDT lending strategy without leverage, staking, or hedging.

**Strategy Description**:
- Deploy all capital to AAVE USDT lending
- Collect lending yield (3-8% APY target)
- No market risk exposure
- No rebalancing required after initial lend/supply action (set-and-forget) because we are not taking any directional exposure that we need to hedge across venues (share class intention is market neutral (`market_neutral: true` in share class config) & `share_class == asset` in mode config) and our initial position is in USDT and therefore market neutral therefore hedged already. Our yield is in USDT terms (and so is our share class) and our P&L auto compounds in USDT terms.

**Config Constraints**:
- `share_class == asset` ("USDT" == "USDT"): No hedging required
- `market_neutral: true` in share class config: Enforces market neutrality
- `lending_enabled: true` and `staking_enabled: false`: Pure lending strategy
- `borrowing_enabled: false`: No leverage or borrowing

**Required Execution Venues**:
- **AAVE V3**: USDT lending/supply operations
- **Alchemy**: Wallet transfers (if any)
- **No CEX venues**: No spot trades or perp positions
- **No staking venues**: No LST operations

**Key Parameters**:
- `share_class`: "USDT"
- `asset`: "USDT" 
- `lending_enabled`: true
- `staking_enabled`: false
- `basis_trade_enabled`: false
- `borrowing_enabled`: false
- `target_apy`: 0.05 (5%)

**Execution Flow**:
1. **Initial Setup** (backtest mode): Supply `initial_capital` USDT to AAVE
2. **Live Mode**: Read existing AAVE positions and rebalance as needed
3. **Ongoing**: Collect lending yield, no rebalancing actions needed
4. **Deposits**: Add new USDT to AAVE supply (same as initial setup)
5. **Withdrawals**: Withdraw USDT from AAVE (1:1 with withdrawal amount)
6. **Rebalancing**: Based on equity changes (deposits/withdrawals/PnL)
7. **Tight Loop**: Position updates trigger sequential component chain (position_monitor → exposure_monitor → risk_monitor → pnl_monitor)

**Risk Profile**:
- **Market Risk**: None (USDT stablecoin)
- **Protocol Risk**: AAVE smart contract risk
- **Liquidity Risk**: Low (AAVE USDT is highly liquid)
- **Max Drawdown**: 0.5% (only gas/conversion costs)

**Data Requirements**:
- USDT/USD spot prices
- AAVE USDT lending rates
- Ethereum gas prices
- Execution cost models

---

### 2. BTC Basis Trading Mode (`btc_basis`)

**Objective**: Market-neutral BTC basis trading strategy collecting funding rate premiums.

**Strategy Description**:
- Long BTC spot positions on CEX
- Short BTC perpetual futures on CEX (equal size)
- Collect funding rate premiums from shorts
- Maintain delta neutrality (net BTC exposure = 0)
- No leverage or borrowing
- **USDT share class** with **BTC asset** requires hedging to maintain market neutrality

**Config Constraints**:
- `share_class != asset` ("USDT" != "BTC"): Must hedge directional exposure
- `market_neutral: true` in share class config: Enforces hedging requirements
- `basis_trade_enabled: true`: Requires equal spot long and perp short positions
- `borrowing_enabled: false` and `lending_enabled: false`: No leverage or lending
- `staking_enabled: false`: No staking operations
- **No locked capital**: All BTC available for spot + perp positions (no maintenance margin issues)

**Required Execution Venues**:
- **Binance**: BTC spot trades + BTC perp shorts (40% allocation)
- **Bybit**: BTC perp shorts (30% allocation)
- **OKX**: BTC perp shorts (30% allocation)
- **Alchemy**: Wallet transfers (if any)
- **No DeFi venues**: No lending or staking operations

**Key Parameters**:
- `share_class`: "USDT"
- `asset`: "BTC"
- `lending_enabled`: false
- `staking_enabled`: false
- `basis_trade_enabled`: true
- `borrowing_enabled`: false
- `hedge_venues`: ["binance", "bybit", "okx"]
- `hedge_allocation`:
  - `binance`: 0.4
  - `bybit`: 0.3
  - `okx`: 0.3
- `target_apy`: 0.08 (8%)

**Execution Flow**:
1. **Initial Setup** (backtest mode): 
   - Buy BTC spot on CEX with `initial_capital`
   - Short BTC perpetual futures (equal size)
   - Distribute across multiple venues per `hedge_allocation` ratios
2. **Live Mode**: Read existing positions and rebalance as needed
3. **Rebalancing**: 
   - **Target Position**: Long BTC spot = current equity, Short BTC perps = current equity
   - **Deposits**: Scale up both legs to match new equity (same as initial setup)
   - **Withdrawals**: Scale down both legs proportionally (1:1 with withdrawal amount)
   - **PnL Changes**: Adjust positions to match equity changes
4. **Risk Override**: If maintenance margin issues, reduce position to stay within limits
5. **Tight Loop**: Position updates trigger sequential component chain (position_monitor → exposure_monitor → risk_monitor → pnl_monitor)

**Risk Profile**:
- **Market Risk**: None (delta neutral)
- **Basis Risk**: BTC spot-perp basis moves
- **Funding Risk**: Funding rate changes
- **Exchange Risk**: CEX counterparty risk
- **Max Drawdown**: 2% (basis volatility)

**Data Requirements**:
- BTC spot prices (all venues)
- BTC perpetual futures prices
- Funding rates (all venues)
- Gas costs
- Execution costs

---



### 3. ETH Basis Trading Mode (`eth_basis`)

**Objective**: Market-neutral ETH basis trading strategy collecting funding rate premiums.

**Strategy Description**:
- Long ETH spot positions on CEX
- Short ETH perpetual futures on CEX (equal size)
- Collect funding rate premiums from shorts
- Maintain delta neutrality (net ETH exposure = 0)
- No leverage or borrowing
- **ETH share class** with **ETH asset** - directional strategy (no hedging required)

**Config Constraints**:
- `share_class == asset` ("ETH" == "ETH"): No hedging required for directional strategy
- `market_neutral: false` in share class config: Allows directional exposure
- `basis_trade_enabled: true`: Requires equal spot long and perp short positions
- `borrowing_enabled: false` and `lending_enabled: false`: No leverage or lending
- `staking_enabled: false`: No staking operations
- **No locked capital**: All ETH available for spot + perp positions (no maintenance margin issues)

**Required Execution Venues**:
- **Binance**: ETH spot trades + ETH perp shorts (40% allocation)
- **Bybit**: ETH perp shorts (30% allocation)
- **OKX**: ETH perp shorts (30% allocation)
- **Alchemy**: Wallet transfers (if any)
- **No DeFi venues**: No lending or staking operations

**Key Parameters**:
- `share_class`: "ETH"
- `asset`: "ETH"
- `lending_enabled`: false
- `staking_enabled`: false
- `basis_trade_enabled`: true
- `borrowing_enabled`: false
- `hedge_venues`: ["binance", "bybit", "okx"]
- `hedge_allocation`:
  - `binance`: 0.4
  - `bybit`: 0.3
  - `okx`: 0.3
- `target_apy`: 0.08 (8%)

**Execution Flow**:
1. **Initial Setup** (backtest mode): 
   - Buy ETH spot on CEX with `initial_capital`
   - Short ETH perpetual futures (equal size)
   - Distribute across multiple venues per `hedge_allocation` ratios
2. **Live Mode**: Read existing positions and rebalance as needed
3. **Rebalancing**: 
   - **Target Position**: Long ETH spot = current equity, Short ETH perps = current equity
   - **Deposits**: Scale up both legs to match new equity (same as initial setup)
   - **Withdrawals**: Scale down both legs proportionally (1:1 with withdrawal amount)
   - **PnL Changes**: Adjust positions to match equity changes
4. **Risk Override**: If maintenance margin issues, reduce position to stay within limits
5. **Tight Loop**: Position updates trigger sequential component chain (position_monitor → exposure_monitor → risk_monitor → pnl_monitor)


**Risk Profile**:
- **Market Risk**: None (delta neutral)
- **Basis Risk**: ETH spot-perp basis moves
- **Funding Risk**: Funding rate changes
- **Max Drawdown**: 2% (basis trading volatility)

**Data Requirements**:
- ETH/USD spot prices
- ETH perpetual futures prices
- Funding rates across venues
- Gas costs
- Execution costs

---

### 4. ETH Staking Only Mode (`eth_staking_only`)

**Objective**: Unleveraged ETH staking strategy with LST rewards.

**Strategy Description**:
- Buy ETH and stake via liquid staking tokens (weETH/wstETH)
- Collect base staking rewards + EIGEN rewards
- No leverage, no hedging
- ETH share class (P&L in ETH terms)
- **Directional ETH exposure** - takes ETH price risk

**Config Constraints**:
- `share_class == asset` ("ETH" == "ETH"): No hedging required for directional strategy
- `market_neutral: false` in share class config: Allows directional exposure
- `staking_enabled: true` and `lending_enabled: false`: Pure staking strategy
- `borrowing_enabled: false`: No leverage or borrowing

**Required Execution Venues**:
- **Lido or EtherFi**: ETH staking/unstaking (based on `lst_type`)
- **Alchemy**: Wallet transfers and ETH conversions
- **No CEX venues**: No spot trades or perp positions
- **No lending venues**: No AAVE operations

**Key Parameters**:
- `share_class`: "ETH"
- `asset`: "ETH"
- `lst_type`: "weeth" or "wsteth"
- `lending_enabled`: false
- `staking_enabled`: true
- `basis_trade_enabled`: false
- `borrowing_enabled`: false
- `target_apy`: 0.03 (3%)

**Execution Flow**:
1. **Initial Setup** (backtest mode):
   - Convert `initial_capital` USDT to ETH
   - Stake ETH via LST protocol (based on `lst_type`)
   - Receive LST tokens (weETH/wstETH)
2. **Live Mode**: Read existing positions and rebalance as needed
3. **Rebalancing**:
   - **Target Position**: Stake ETH = current equity
   - **Deposits**: Buy more ETH and stake (same as initial setup)
   - **Withdrawals**: Unstake LST and convert to ETH (1:1 with withdrawal amount)
   - **PnL Changes**: Adjust staked position to match equity changes
4. **Ad-hoc Actions**:
   - **Sell Dust**: Convert KING tokens (EIGEN/ETHFI composite) to ETH (if `lst_type: weeth` and dust > `dust_delta` threshold)
5. **Tight Loop**: Position updates trigger sequential component chain (position_monitor → exposure_monitor → risk_monitor → pnl_monitor)


**Risk Profile**:
- **Market Risk**: Full ETH price exposure (directional strategy)
- **Staking Risk**: LST protocol risk
- **Slashing Risk**: Validator slashing (minimal with LST)
- **Max Drawdown**: 1% (staking yield volatility, not ETH price risk)

**Data Requirements**:
- ETH/USD spot prices
- LST prices (weETH/ETH, wstETH/ETH)
- Staking rewards data
- EIGEN rewards data
- Gas costs
- Execution costs

---

### 4. ETH Leveraged Mode (`eth_leveraged`)

**Objective**: Leveraged ETH staking strategy with LST rewards using atomic flash loan leverage.

**Strategy Description**:
- Stake ETH via LST protocols (receiveweETH/wstETH)
- Use atomic flash loan to create leveraged position in single transaction
- Flash borrow WETH → stake to get LST → supply LST to AAVE → borrow WETH from AAVE → repay flash loan
- ETH share class (P&L in ETH terms)
- **Directional ETH exposure** - takes ETH price risk (no hedging)
- **Key Difference from ETH Staking Only**: Uses atomic flash loan leverage to reach `target_ltv`

**Config Constraints**:
- `share_class == asset` ("ETH" == "ETH"): No hedging required for directional strategy
- `market_neutral: false` in share class config: Allows directional exposure
- `staking_enabled: true` and `lending_enabled: true`: Leveraged staking strategy
- `borrowing_enabled: true`: Enables leveraged staking via AAVE borrowing

**Required Execution Venues**:
- **Lido or EtherFi**: ETH staking/unstaking (based on `lst_type`)
- **AAVE V3**: LST collateral supply and WETH borrowing for leveraged staking
- **Instadapp**: Flash loan provider for atomic leverage operations
- **Alchemy**: Wallet transfers and ETH conversions
- **No CEX venues**: No spot trades or perp positions

**Key Parameters**:
- `share_class`: "ETH"
- `asset`: "ETH"
- `lst_type`: "weeth" or "wsteth"
- `lending_enabled`: true
- `staking_enabled`: true
- `basis_trade_enabled`: false
- `borrowing_enabled`: true
- `target_ltv`: Calculated dynamically by risk_monitor using `utility_manager.calculate_dynamic_ltv_target()`
- `target_apy`: 0.20 (20%)

**Atomic Flash Loan Execution Flow**:
1. **Initial Setup** (backtest mode):
   - **Atomic Flash Loan Sequence** (all in single transaction):
     1. `FLASH_BORROW` WETH from Morpho (via Instadapp)
     2. `STAKE` WETH to get LST (weETH/wstETH)
     3. `SUPPLY` LST to AAVE as collateral
     4. `BORROW` WETH from AAVE (up to target_ltv)
     5. `FLASH_REPAY` WETH to Morpho
   - **Leverage Formula**: `leverage = target_ltv / (1 - target_ltv)` (e.g., 0.9 LTV = 9x leverage)
   - **Target Supply**: `equity * leverage` (in LST terms)
   - **Target Debt**: `equity * (leverage - 1)` (in WETH terms)

2. **Live Mode**: Read existing positions and rebalance as needed

3. **Rebalancing**:
   - **Target Position**: Supply = `equity * leverage`, Debt = `equity * (leverage - 1)`
   - **Deposits**: Execute atomic flash loan leverage for additional equity
   - **Withdrawals**: Unwind leveraged position (repay debt → withdraw collateral → unstake)
   - **PnL Changes**: Adjust positions to match equity changes

4. **Risk Override**: If LTV health factor too low, reduce position to stay within limits

5. **Ad-hoc Actions**:
   - **Sell Dust**: Convert KING tokens (EIGEN/ETHFI composite) to ETH (if `lst_type: weeth` and dust > `dust_delta` threshold)

6. **Tight Loop**: Position updates trigger sequential component chain (position_monitor → exposure_monitor → risk_monitor → pnl_monitor)

**Flash Loan Mechanics**:
- **Provider**: Morpho via Instadapp middleware
- **Purpose**: Create leveraged staking position atomically
- **Sequence**: All 5 operations must succeed or all fail (atomic transaction)
- **Benefits**: Avoids sequential borrowing loops, reduces gas costs, eliminates MEV risk
- **Risk**: Flash loan failure results in no position change (fail-safe)

**Risk Profile**:
- **Market Risk**: Full ETH price exposure (directional strategy)
- **Liquidation Risk**: AAVE liquidation if health factor < 1.0
- **Staking Risk**: LST protocol risk
- **Leverage Risk**: Amplified ETH price exposure (no hedging)
- **Flash Loan Risk**: Atomic transaction failure (fail-safe)
- **Max Drawdown**: 4% (leveraged staking volatility, not ETH price risk)

**Data Requirements**:
- ETH/USD spot prices
- LST prices and oracle prices
- AAVE lending rates and risk parameters
- Staking rewards data
- EIGEN rewards data
- Flash loan rates and availability
- Gas costs
- Execution costs

---

### 5. USDT ETH Staking Hedged Simple Mode (`usdt_eth_staking_hedged_simple`)

**Objective**: Market-neutral ETH staking strategy without leverage, hedged to USDT.

**Strategy Description**:
- Take `stake_allocation_percentage` proportion of equity and buy ETH
- Stake ETH via LST protocols
- Send remaining equity to CEX for perp shorting
- Hedge ETH exposure with short perps
- USDT share class (P&L in USDT terms)
- **USDT share class** with **ETH asset** requires hedging to maintain market neutrality

**Config Constraints**:
- `share_class != asset` ("USDT" != "ETH"): Must hedge directional exposure
- `market_neutral: true` in share class config: Enforces hedging requirements
- `staking_enabled: true` and `basis_trade_enabled: true`: Staking + hedging strategy
- `borrowing_enabled: false`: No leverage or borrowing
- `stake_allocation_percentage`: Configures proportion of equity for staking vs hedging
- **Locked capital strategy**: Must reserve USDT for CEX margin (cannot use LST as collateral)

**Required Execution Venues**:
- **Lido or EtherFi**: ETH staking/unstaking (based on `lst_type`)
- **Binance**: ETH perp shorts (40% allocation)
- **Bybit**: ETH perp shorts (30% allocation)
- **OKX**: ETH perp shorts (30% allocation)
- **Alchemy**: Wallet transfers and ETH conversions
- **No lending venues**: No AAVE operations

**Key Parameters**:
- `share_class`: "USDT"
- `asset`: "ETH"
- `lst_type`: "weeth" or "wsteth"
- `stake_allocation_percentage`: 0.5 (50% to staking, 50% to hedge margin)
- `lending_enabled`: false
- `staking_enabled`: true
- `basis_trade_enabled`: true
- `borrowing_enabled`: false
- `hedge_venues`: ["binance", "bybit", "okx"]
- `target_apy`: 0.08 (8%)

**Execution Flow**:
1. **Initial Setup** (backtest mode):
   - Split equity: `stake_allocation_percentage` to ETH staking, `1 - stake_allocation_percentage` to CEX margin
   - **Step 1**: Fund ALL CEXs simultaneously with USDT margin
     ```python
     wallet:BaseToken:USDT -= (binance + bybit + okx)
     cex['binance'].USDT += binance
     cex['bybit'].USDT += bybit
     cex['okx'].USDT += okx
     ```
   - **Step 2**: Execute ALL perp shorts simultaneously (same timestamp!)
     ```python
     # Binance: Spot + Perp
     cex['binance'].ETH_spot += eth_bought
     cex['binance'].perp = short_binance
     
     # Bybit & OKX: Perp only (executed at same time as Binance!)
     cex['bybit'].perp = short_bybit
     cex['okx'].perp = short_okx
     ```
   - **Step 3**: Transfer ETH to wallet and stake via LST
     ```python
     cex['binance'].ETH_spot -= eth_transfer
     wallet:BaseToken:ETH += eth_transfer
     # Stake ETH via LST protocol (based on lst_type)
     ```
   - **Key**: ALL perp shorts at same time, not sequential!
2. **Live Mode**: Read existing positions and rebalance as needed
3. **Rebalancing**:
   - Monitor delta neutrality (from risk monitor)
   - Adjust perp shorts if delta drift > `max_delta_drift`
   - Maintain `stake_allocation_percentage` allocation between staking and hedge
4. **Deposits**: Scale up both legs proportionally
5. **Withdrawals**: Scale down both legs proportionally (1:1 with withdrawal amount)
6. **Tight Loop**: Position updates trigger sequential component chain (position_monitor → exposure_monitor → risk_monitor → pnl_monitor)


**Risk Profile**:
- **Market Risk**: None (delta neutral)
- **Staking Risk**: LST protocol risk
- **Funding Risk**: Perp funding rate costs
- **Exchange Risk**: CEX counterparty risk
- **Max Drawdown**: 2% (staking + funding volatility)

**Data Requirements**:
- ETH/USD spot prices
- LST prices and oracle prices
- Staking rewards data
- EIGEN and ETHFI rewards data
- Perp funding rates (all venues)
- Gas costs
- Execution costs

---

### 6. USDT ETH Staking Hedged Leveraged Mode (`usdt_eth_staking_hedged_leveraged`)

**Objective**: Market-neutral leveraged ETH staking strategy, hedged to USDT.

**Strategy Description**:
- Take `stake_allocation_percentage` proportion of equity and buy ETH
- Stake ETH via LST protocols
- Use AAVE to create leveraged position on staking side
- Send remaining equity to CEX for perp shorting
- Hedge leveraged ETH exposure with short perps
- USDT share class (P&L in USDT terms)
- **USDT share class** with **ETH asset** requires hedging to maintain market neutrality

**Config Constraints**:
- `share_class != asset` ("USDT" != "ETH"): Must hedge directional exposure
- `market_neutral: true` in share class config: Enforces hedging requirements
- `staking_enabled: true`, `lending_enabled: true`, and `basis_trade_enabled: true`: Leveraged staking + hedging strategy
- `borrowing_enabled: true`: Enables leveraged staking via AAVE borrowing
- `stake_allocation_percentage`: Configures proportion of equity for leveraged staking vs hedging
- **Locked capital strategy**: Must reserve USDT for CEX margin (cannot use LST as collateral)
- **Flash loan potential**: Morpho/Instadapp for atomic leverage operations

**Required Execution Venues**:
- **Lido or EtherFi**: ETH staking/unstaking (based on `lst_type`)
- **AAVE V3**: LST collateral supply and ETH borrowing for leveraged staking
- **Binance**: ETH perp shorts (40% allocation)
- **Bybit**: ETH perp shorts (30% allocation)
- **OKX**: ETH perp shorts (30% allocation)
- **Alchemy**: Wallet transfers and ETH conversions

**Key Parameters**:
- `share_class`: "USDT"
- `asset`: "ETH"
- `lst_type`: "weeth" or "wsteth"
- `stake_allocation_percentage`: 0.5 (50% to leveraged staking, 50% to hedge margin)
- `lending_enabled`: true
- `staking_enabled`: true
- `basis_trade_enabled`: true
- `borrowing_enabled`: true
- `hedge_venues`: ["binance", "bybit", "okx"]
- `target_apy`: 0.15 (15%)

**Execution Flow**:
1. **Initial Setup** (backtest mode):
   - Split equity: `stake_allocation_percentage` to leveraged ETH staking, `1 - stake_allocation_percentage` to CEX margin
   - **Step 1**: Fund ALL CEXs simultaneously with USDT margin
     ```python
     wallet:BaseToken:USDT -= (binance + bybit + okx)
     cex['binance'].USDT += binance
     cex['bybit'].USDT += bybit
     cex['okx'].USDT += okx
     ```
   - **Step 2**: Execute ALL perp shorts simultaneously (same timestamp!)
     ```python
     # Binance: Spot + Perp
     cex['binance'].ETH_spot += eth_bought
     cex['binance'].perp = short_binance
     
     # Bybit & OKX: Perp only (executed at same time as Binance!)
     cex['bybit'].perp = short_bybit
     cex['okx'].perp = short_okx
     ```
   - **Step 3**: Transfer ETH to wallet and create leveraged position
     ```python
     cex['binance'].ETH_spot -= eth_transfer
     wallet:BaseToken:ETH += eth_transfer
     # Stake ETH via LST (based on lst_type)
     # Create AAVE leveraged position: borrow_flash → stake → supply_lst → borrow_aave → repay_flash
     ```
   - **Key**: ALL perp shorts at same time, not sequential!
2. **Live Mode**: Read existing positions and rebalance as needed with the same order of operations accepting some time delay awaiting execution instruction completions
3. **Rebalancing**:
   - Monitor AAVE health factor and delta neutrality (from risk monitor)
   - Add margin to CEX if perps losing money
   - Reduce AAVE LTV if health factor too low
   - Adjust perp shorts to maintain delta neutrality
4. **Deposits**: Scale up both legs proportionally
5. **Withdrawals**: Unwind both legs proportionally (1:1 with withdrawal amount)
6. **Tight Loop**: Position updates trigger sequential component chain (position_monitor → exposure_monitor → risk_monitor → pnl_monitor)


**Risk Profile**:
- **Market Risk**: None (delta neutral)
- **Liquidation Risk**: AAVE liquidation risk
- **Staking Risk**: LST protocol risk
- **Funding Risk**: Perp funding rate costs
- **Exchange Risk**: CEX counterparty risk
- **Leverage Risk**: Amplified staking yields and risks
- **Max Drawdown**: 4% (leveraged staking + funding volatility)

**Data Requirements**:
- ETH/USD spot prices
- LST prices and oracle prices
- AAVE lending rates and risk parameters
- Staking rewards data
- EIGEN and ETHFI rewards data
- Perp funding rates (all venues)
- Gas costs
- Execution costs

---

### 7. ML BTC Directional Mode (`ml_btc_directional_usdt_margin`)

**Objective**: ML-driven directional BTC strategy with long/short perp trading on 5-minute intervals.

**Strategy Description**:
- Use ML predictions for entry/exit signals (long/short/neutral)
- Trade BTC/USDT perp futures on 5-minute intervals
- Full position sizing (100% of equity per signal)
- Take-profit and stop-loss orders for risk management
- BTC share class (P&L in BTC terms)

**Config Constraints**:
- `share_class == asset` ("BTC" == "BTC"): No hedging required
- `market_neutral: false`: Directional strategy
- `leverage_enabled: true`: Perp futures trading
- `lending_enabled: false`, `staking_enabled: false`: Pure perp strategy
- `borrowing_enabled: false`: No borrowing

**Required Execution Venues**:
- **Binance**: BTC perp futures trading
- **No DeFi venues**: No lending, staking, or on-chain operations

**Key Parameters**:
- `share_class`: "BTC"
- `asset`: "BTC"
- `market_neutral`: false
- `leverage_enabled`: true
- `lending_enabled`: false
- `staking_enabled`: false
- `basis_trade_enabled`: false
- `borrowing_enabled`: false
- `initial_capital`: 1.0 (1 BTC)
- `ml_config.signal_threshold`: 0.7 (min confidence to trade)
- `ml_config.max_position_size`: 1.0 (100% of equity)

**Execution Flow**:
1. **Entry**: At start of 5-min candle based on ML signal (long/short)
2. **Exit**: Stop-loss (priority 1) → Take-profit (priority 2) → End of candle (priority 3)
3. **Position sizing**: Full position (100% equity) per signal
4. **Hold logic**: If new signal matches current position, hold (no action)

**Stop-Loss and Take-Profit Management**:
ML strategies use standard deviation from ML signal data to calculate stop-loss and take-profit prices:

**Configuration**:
```yaml
ml_config:
  take_profit_sd: 2  # Standard deviations for take profit
  stop_loss_sd: 2  # Standard deviations for stop loss
  sd_floor_bps: 10  # Minimum SD in basis points (0.10%)
  sd_cap_bps: 1000  # Maximum SD cap in basis points (10%)
```

**Calculation Logic**:
1. Extract `sd` field from ML signal data (standard deviation of price prediction)
2. Floor and cap SD: `sd_bps = max(sd_floor_bps, min(raw_sd * 10000, sd_cap_bps))`
3. Calculate price moves:
   - Take profit: `entry_price ± (sd_decimal * take_profit_sd * entry_price)`
   - Stop loss: `entry_price ∓ (sd_decimal * stop_loss_sd * entry_price)`
4. Direction:
   - LONG: TP above entry, SL below entry
   - SHORT: TP below entry, SL above entry

**Order Integration**:
Stop-loss and take-profit prices are included in Order model and automatically monitored by execution venues (Binance, Bybit, OKX).

**Data Requirements**:
- `ml_ohlcv_5min`: OHLCV 5-min bars
- `ml_predictions`: ML signals (long/short/neutral + TP/SL)
- `btc_usd_prices`: For PnL calculation
- `gas_costs`, `execution_costs`: For cost tracking

**Risk Profile**:
- **Market Risk**: High (directional exposure)
- **ML Risk**: Model prediction accuracy
- **Liquidation Risk**: Perp margin requirements
- **Exchange Risk**: CEX counterparty risk
- **Max Drawdown**: 20% (directional strategy)

---

### 8. ML USDT Directional Mode (`ml_usdt_directional_usdt_margin`)

**Objective**: ML-driven directional USDT strategy with long/short perp trading on 5-minute intervals.

**Strategy Description**:
- Use ML predictions for entry/exit signals (long/short/neutral)
- Trade USDT perp futures on 5-minute intervals
- Full position sizing (100% of equity per signal)
- Take-profit and stop-loss orders for risk management
- USDT share class (P&L in USDT terms)

**Config Constraints**:
- `share_class == asset` ("USDT" == "USDT"): No hedging required
- `market_neutral: false`: Directional strategy
- `leverage_enabled: true`: Perp futures trading
- `lending_enabled: false`, `staking_enabled: false`: Pure perp strategy
- `borrowing_enabled: false`: No borrowing

**Required Execution Venues**:
- **Binance**: USDT perp futures trading
- **No DeFi venues**: No lending, staking, or on-chain operations

**Key Parameters**:
- `share_class`: "USDT"
- `asset`: "USDT"
- `market_neutral`: false
- `leverage_enabled`: true
- `lending_enabled`: false
- `staking_enabled`: false
- `basis_trade_enabled`: false
- `borrowing_enabled`: false
- `initial_capital`: 10000.0 (10k USDT)
- `ml_config.signal_threshold`: 0.7 (same threshold for both strategies)
- `ml_config.max_position_size`: 1.0 (100% of equity)

**Execution Flow**:
1. **Entry**: At start of 5-min candle based on ML signal (long/short)
2. **Exit**: Stop-loss (priority 1) → Take-profit (priority 2) → End of candle (priority 3)
3. **Position sizing**: Full position (100% equity) per signal
4. **Hold logic**: If new signal matches current position, hold (no action)

**Data Requirements**:
- `ml_ohlcv_5min`: OHLCV 5-min bars
- `ml_predictions`: ML signals (long/short/neutral + TP/SL)
- `usdt_usd_prices`: For PnL calculation
- `gas_costs`, `execution_costs`: For cost tracking

**Risk Profile**:
- **Market Risk**: High (directional exposure)
- **ML Risk**: Model prediction accuracy
- **Liquidation Risk**: Perp margin requirements
- **Exchange Risk**: CEX counterparty risk
- **Max Drawdown**: 20% (directional strategy)

---

## Strategy Manager Architecture

**PLANNED ARCHITECTURE**: Inheritance-based strategy modes with standardized wrapper actions (per strategy_manager_refactor.md)

### Inheritance-Based Interface
All strategy modes inherit from BaseStrategyManager and implement the same 5 wrapper actions:
- **entry_full**: Deploy capital according to strategy (initial setup)
- **entry_partial**: Scale up existing positions (deposits)
- **exit_partial**: Scale down existing positions (withdrawals)
- **exit_full**: Exit entire position (risk override)
- **sell_dust**: Convert non-share-class tokens to share class currency

### Dust Handling by Strategy Type

**Active Dust Handling** (ETH strategies):
- **ETH Staking Only**: Convert EIGEN/ETHFI dust to ETH
- **ETH Leveraged**: Convert EIGEN/ETHFI dust to ETH
- **USDT ETH Staking Hedged**: Convert EIGEN/ETHFI dust to USDT

**Pass-Through Dust Handling** (Non-staking strategies):
- **Basis Strategies**: No dust generation (no staking rewards)
- **Pure Lending**: No dust generation (no staking rewards)
- **ML Strategies**: No dust generation (no staking rewards)

### Mode-Specific Implementation
Each strategy mode implements mode-specific logic for the 5 wrapper actions:
- **Desired Position Calculation**: Each mode calculates its target positions differently
- **Rebalancing Triggers**: Different risk thresholds per mode
- **Instruction Generation**: Mode-specific execution sequences

### Config-Driven Parameters
Components use configuration parameters instead of mode-specific logic:
- `share_class`: Determines reporting currency and hedging requirements
- `asset`: Primary asset being traded
- `lst_type`: Liquid staking token type
- `stake_allocation_percentage`: Proportion of equity for staking vs hedging

---

## Execution Architecture

### Venue-Based Execution
All strategies use venue-based execution architecture:
- **On-Chain Venues**: AAVE, EtherFi, Lido, Uniswap
- **CEX Venues**: Binance, Bybit, OKX
- **Action Type Mapping**: Each action type maps to appropriate venues

### Execution Modes
- **Backtest Mode**: Simulated execution with historical data
- **Live Mode**: Real execution with external APIs
- **Testnet Mode**: Live execution on testnets

### Instruction Types
- **Wallet Transfers**: Simple venue-to-venue transfers
- **CEX Trades**: Spot and perpetual trades
- **Smart Contract Operations**: AAVE, staking, swaps
- **Atomic Operations**: Flash loan sequences

---

## Risk Management

### Risk Dimensions
All strategies monitor:
- **Market Risk**: Delta exposure to underlying assets
- **Liquidation Risk**: AAVE health factor and CEX margin ratios
- **Protocol Risk**: Smart contract and CEX counterparty risk
- **Funding Risk**: Perpetual funding rate costs
- **Liquidity Risk**: Ability to exit positions

### Rebalancing Triggers
- **Margin Critical**: CEX margin ratio < 20%
- **LTV Critical**: AAVE health factor < 1.1
- **Delta Drift**: Net delta > 5% of equity
- **Performance**: P&L-based position sizing

### Emergency Protocols
- **Circuit Breakers**: Stop trading on extreme moves
- **Emergency Unwinding**: Rapid position reduction
- **Fallback Modes**: Simplified execution paths

---

## Data Requirements

### Market Data
- **Spot Prices**: ETH, BTC, USDT across all venues
- **Derivatives Prices**: Perpetual futures prices
- **Funding Rates**: Real-time funding rates from all CEX
- **Gas Prices**: Ethereum network gas prices

### Protocol Data
- **AAVE Data**: Lending rates, risk parameters, oracle prices
- **Staking Data**: LST prices, staking rewards, EIGEN rewards
- **Execution Data**: Historical execution costs and slippage

### Risk Data
- **Liquidation Thresholds**: AAVE and CEX liquidation parameters
- **Volatility Data**: Historical volatility for risk calculations
- **Correlation Data**: Asset correlations for portfolio risk

---

## Performance Targets

| Strategy Mode | Target APY | Max Drawdown | Risk Level | Market Exposure |
|---------------|------------|--------------|------------|-----------------|
| Pure Lending | 5% | 0.5% | Low | None (USDT) |
| BTC Basis | 8% | 2% | Medium | None (hedged) |
| ETH Basis | 8% | 2% | Medium | None (hedged) |
| ETH Staking Only | 3% | 1% | Low | Full ETH (directional) |
| ETH Leveraged | 20% | 4% | High | Full ETH (directional) |
| USDT ETH Staking Hedged Simple | 8% | 2% | Medium | None (hedged) |
| USDT ETH Staking Hedged Leveraged | 15% | 4% | High | None (hedged) |

---

## Execution Venue Summary

### Venue Usage by Strategy Mode

| Strategy Mode | CEX Venues | DeFi Venues | Infrastructure |
|---------------|------------|-------------|----------------|
| **Pure Lending** | None | AAVE V3 | Alchemy |
| **BTC Basis** | Binance, Bybit, OKX | None | Alchemy |
| **ETH Basis** | Binance, Bybit, OKX | None | Alchemy |
| **ETH Staking Only** | None | Lido/EtherFi | Alchemy |
| **ETH Leveraged** | None | Lido/EtherFi, AAVE V3, Morpho | Alchemy, Instadapp |
| **USDT ETH Staking Hedged Simple** | Binance, Bybit, OKX | Lido/EtherFi | Alchemy |
| **USDT ETH Staking Hedged Leveraged** | Binance, Bybit, OKX | Lido/EtherFi, AAVE V3, Morpho | Alchemy, Instadapp |
| **ML BTC Directional** | Binance (BTC perps) | None | None |
| **ML USDT Directional** | Binance (USDT-margined BTC perps) | None | None |

### Venue Selection Logic

**CEX Venues**:
- **Spot Trades**: Binance preferred (unless atomic on-chain transaction requires DEX)
- **Perp Shorts**: Distributed based on `hedge_allocation` ratios
- **Allocation Logic**: `hedge_allocation: {binance: 0.4, bybit: 0.3, okx: 0.3}`

**DeFi Venues**:
- **Staking**: Lido (wstETH) or EtherFi (weETH) based on `lst_type` config
- **Lending**: AAVE V3 (extensible to Compound, Morpho, etc.)
- **Flash Loans**: Morpho (via Instadapp middleware) for atomic leverage operations
- **DEX Swaps**: Uniswap (for atomic on-chain transactions)

**Infrastructure**:
- **Wallet Transfers**: Alchemy (Web3 wrapper) for all on-chain operations
- **Atomic Transactions**: Instadapp middleware for complex multi-step operations
- **Data Access**: All venues provide market data and execution interfaces

**ML Strategy Special Cases**:
- **ML BTC/USDT Directional**: Pure CEX strategies with **no wallet transfers required**
- **Capital Flow**: Initial capital lands directly in CEX wallet (no on-chain → CEX transfers)
- **Position Monitor**: Assumes capital starts at CEX, no transfer tracking needed
- **Infrastructure Integration**: Uses same framework as DeFi strategies but CEX-only execution

### Venue Configuration Requirements

Each strategy mode can infer its required venues from:
1. **Strategy Flags**: `staking_enabled`, `lending_enabled`, `basis_trade_enabled`
2. **Asset Configuration**: `asset` type determines spot trade venues
3. **Hedge Configuration**: `hedge_venues` and `hedge_allocation` determine perp venues
4. **LST Configuration**: `lst_type` determines staking venue (Lido vs EtherFi)
5. **Leverage Configuration**: `borrowing_enabled` determines flash loan requirements

### Capital Allocation Strategy

**No Locked Capital** (`borrowing_enabled: false` + `lending_enabled: false` + `staking_enabled: false`):
- **BTC/ETH Basis**: All capital available for spot + perp positions
- **No maintenance margin issues**: Can use all asset for perp shorts
- **No cross-venue capital allocation**: Single venue focus

**Locked Capital with Hedging** (`staking_enabled: true` + `share_class != asset`):
- **USDT ETH Staking Hedged modes**: Must split equity between staking and perp margin
- **`stake_allocation_percentage`**: Proportion for ETH staking (locked on-chain)
- **`1 - stake_allocation_percentage`**: Proportion for CEX margin (in USDT)
- **Why USDT margin**: Forces P&L to move in equally offsetting directions
  - CEX gains when on-chain loses (in USDT terms)
  - If used ETH as margin, would create long ETH delta distortion

**Directional Strategies** (`share_class == asset` + `staking_enabled: true`):
- **ETH Leveraged/Staking Only**: No hedging required
- **All capital can be staked**: No need to reserve for perp margin
- **Flash loan potential**: Morpho/Instadapp for atomic leverage operations

This venue mapping enables the execution manager to:
- Initialize only required venue clients for each strategy mode
- Route execution instructions to appropriate venues
- Handle venue-specific error handling and retry logic
- Optimize execution costs by choosing appropriate venues
- Manage capital allocation based on strategy constraints

---

## Implementation Notes

### Current Architecture Issues
The current strategy manager and rebalancing code is overly complex and disorganized. The architecture should be simplified to:

1. **Remove transfer_manager.py**: The current `backend/src/basis_strategy_v1/core/rebalancing/transfer_manager.py` should be removed as it's too complex and strategy-agnostic generalization is not feasible
2. **Clean Strategy Manager**: Mode-specific desired position calculation only
3. **Generic Execution Manager**: Venue-based execution for all modes
4. **Unified Rebalancing**: Common rebalancing logic with mode-specific parameters
5. **Config-Driven Components**: Use configuration instead of mode-specific code
6. **Tight Loop Architecture**: Implement mandatory sequential component chain (position_monitor → exposure_monitor → risk_monitor → pnl_monitor)
7. **Centralized Utility Manager**: All utility methods centralized in single utility manager
8. **Event Engine Integration**: All components properly integrated with EventDrivenStrategyEngine

### Required Refactoring
1. **Simplify Strategy Manager**: Focus on desired position calculation
2. **Generic Execution Interfaces**: Venue-based execution for all action types
3. **Unified Instruction Generation**: Common instruction patterns with mode-specific parameters
4. **Config-Driven Risk Management**: Risk thresholds from configuration files
5. **Implement Tight Loop**: Mandatory sequential component chain for all strategy modes
6. **Centralize Utilities**: Move all utility methods to centralized utility manager
7. **Event Engine Integration**: Proper integration with EventDrivenStrategyEngine
8. **Remove Hardcoded Values**: Eliminate all hardcoded strategy-specific values

### Quality Gates
Each strategy mode must pass:
- **Initial Setup**: Correct position deployment
- **Rebalancing**: Proper risk-triggered adjustments
- **Deposits/Withdrawals**: Proportional scaling
- **Risk Management**: Appropriate risk monitoring
- **Performance**: Meeting target APY and drawdown limits
- **Tight Loop Architecture**: Sequential component chain working correctly
- **Centralized Utilities**: All utility methods using centralized utility manager
- **Event Engine Integration**: Proper integration with EventDrivenStrategyEngine
- **No Hardcoded Values**: All values loaded from configuration files

---

This specification provides the foundation for implementing clean, maintainable strategy modes that can be easily extended and modified through configuration rather than code changes.
