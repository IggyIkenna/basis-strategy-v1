# Strategy Modes Specification

## Overview

This document provides comprehensive specifications for all strategy modes in the basis-strategy-v1 platform. Each mode represents a distinct investment strategy with specific risk profiles, yield sources, and execution requirements.

## 📚 **Canonical Sources**

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
- **DeFi**: AAVE V3, Lido, EtherFi, Morpho (flash loans)
- **Infrastructure**: Alchemy (Web3), Uniswap (DEX swaps), Instadapp (atomic transaction middleware)

### Capital Allocation Logic

**Strategy Constraints Determine Capital Allocation**:

**No Locked Capital Strategies** (`borrowing_enabled: false` + `lending_enabled: false` + `staking_enabled: false`):
- **BTC Basis**: All capital available for spot + perp positions
- **No maintenance margin issues**: Can use all BTC for perp shorts
- **No cross-venue issues**: No locked capital on AAVE or staking protocols

**Locked Capital Strategies** (`staking_enabled: true` + `share_class != asset`):
- **Must reserve capital for perp margin**: Cannot use LST as CEX collateral
- **USDT Market Neutral modes**: Use `stake_allocation_eth` to split equity
  - `stake_allocation_eth`: Proportion for ETH staking (locked on-chain)
  - `1 - stake_allocation_eth`: Proportion for CEX margin (in USDT)
- **Why USDT margin**: Forces P&L to move in equally offsetting directions
  - CEX gains when on-chain loses (in USDT terms)
  - If used ETH as margin, would create long ETH delta distortion

**Directional Strategies** (`share_class == asset` + `staking_enabled: true`):
- **ETH Leveraged/Staking Only**: No hedging required
- **All capital can be staked**: No need to reserve for perp margin
- **No cross-venue capital allocation**: Single venue focus

### Reserve Management & Execution Modes

**Reserve Parameters**:
- Each strategy defines a `reserve_ratio` config parameter (e.g., 5% of total capital)
- Strategies monitor reserves and send fast execution requests when reserves are low
- Reserve low events are published for downstream consumers to handle withdrawal speed
- Position deviation from target must exceed `position_deviation_threshold` before rebalancing triggers

**Execution Modes**:
- **Atomic Transactions**: Via Instadapp middleware for complex multi-step operations (leveraged staking)
- **Sequential Transactions**: Direct API calls to individual venues (Lido, AAVE, etc.) for simple operations
- **Leveraged Staking**: Always use atomic flash loan execution for efficiency

**Withdrawal Handling**:
- **All strategies unwind 1:1 with withdrawals** (no exceptions)
- **Reserve balance affects speed**: Fast vs slow unwinding
- **Fast unwinding**: Uses available reserves
- **Slow unwinding**: Requires unwinding locked positions

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

**Note**: There are 7 YAML configs and 7 documented strategies. All strategy modes are documented below.

### 1. Pure Lending Mode (`pure_lending`)

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

**Reserve Balance Management**:
- **Fast Withdrawals**: Maintain USDT reserve for immediate client redemptions
- **Reserve Threshold**: If reserve < `reserve_ratio` of total USDT, publish reserve_low event
- **Unwinding**: All withdrawals unwind 1:1 from AAVE (fast, ~1-2 blocks)

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
- `hedge_allocation_binance`: 0.4
- `hedge_allocation_bybit`: 0.3
- `hedge_allocation_okx`: 0.3
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

**Reserve Balance Management**:
- **Fast Withdrawals**: Maintain USDT reserve for immediate client redemptions
- **Reserve Threshold**: If reserve < `reserve_ratio` of total USDT, publish reserve_low event
- **Unwinding**: All withdrawals unwind 1:1 (close perp shorts first, then sell spot positions)

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
- `hedge_allocation_binance`: 0.4
- `hedge_allocation_bybit`: 0.3
- `hedge_allocation_okx`: 0.3
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

**Reserve Balance Management**:
- **Fast Withdrawals**: Maintain ETH reserve for immediate client redemptions
- **Reserve Threshold**: If reserve < `reserve_ratio` of total ETH, publish reserve_low event
- **Unwinding**: All withdrawals unwind 1:1 (close perp shorts first, then sell spot positions)

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
- `asset`: "USDT" (converted to ETH)
- `lst_type`: "weeth" or "wsteth"
- `lending_enabled`: false
- `staking_enabled`: true
- `basis_trade_enabled`: false
- `borrowing_enabled`: false
- `rewards_mode`: "base_eigen"
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

**Reserve Balance Management**:
- **Fast Withdrawals**: Maintain ETH reserve for immediate client redemptions
- **Reserve Threshold**: If reserve < 10% of total ETH, slow down withdrawals
- **Unwinding**: If too many withdrawals, unstake LST (slow, can take days via protocol)

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

**Objective**: Leveraged ETH staking strategy with LST rewards.

**Strategy Description**:
- Buy ETH and stake via LST
- Use AAVE to borrow against LST collateral
- Reinvest borrowed funds into more ETH staking
- Create leveraged position using atomic flash loan
- ETH share class (P&L in ETH terms)
- **Directional ETH exposure** - takes ETH price risk (no hedging)

**Config Constraints**:
- `share_class == asset` ("ETH" == "ETH"): No hedging required for directional strategy
- `market_neutral: false` in share class config: Allows directional exposure
- `staking_enabled: true` and `lending_enabled: true`: Leveraged staking strategy
- `borrowing_enabled: true`: Enables leveraged staking via AAVE borrowing

**Required Execution Venues**:
- **Lido or EtherFi**: ETH staking/unstaking (based on `lst_type`)
- **AAVE V3**: LST collateral supply and ETH borrowing for leveraged staking
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
- `rewards_mode`: "base_eigen"
- `max_ltv`: 0.91
- `liquidation_threshold`: 0.95
- `target_apy`: 0.20 (20%)

**Execution Flow**:
1. **Initial Setup** (backtest mode):
   - Buy ETH and stake via LST (based on `lst_type`)
   - Use atomic flash loan to create leverage: borrow_flash → stake → supply_lst → borrow_aave → repay_flash
   - **Leverage Formula**: `target_ltv / (1 - target_ltv)` (e.g., 0.9 LTV = 9x leverage)
   - **Desired Supply**: `equity * leverage`, **Desired Debt**: `equity * (leverage - 1)`
2. **Live Mode**: Read existing positions and rebalance as needed
3. **Rebalancing**:
   - **Target Position**: Supply = `equity * leverage`, Debt = `equity * (leverage - 1)`
   - **Deposits**: Stake excess ETH, recalculate desired debt/supply, execute atomic leverage
   - **Withdrawals**: Unwind leveraged position (1:1 with withdrawal amount)
   - **PnL Changes**: Adjust positions to match equity changes
4. **Risk Override**: If LTV health factor too low, reduce position to stay within limits
5. **Ad-hoc Actions**:
   - **Sell Dust**: Convert KING tokens (EIGEN/ETHFI composite) to ETH (if `lst_type: weeth` and dust > `dust_delta` threshold)
   - **Fast Unwind**: If reserves too low, DEX swap LST to ETH for immediate withdrawal
6. **Tight Loop**: Position updates trigger sequential component chain (position_monitor → exposure_monitor → risk_monitor → pnl_monitor)

**Reserve Balance Management**:
- **Fast Withdrawals**: Maintain ETH reserve for immediate client redemptions
- **Reserve Threshold**: If reserve < `reserve_ratio` of total ETH, publish reserve_low event
- **Unwinding**: If too many withdrawals, unwind leveraged position (slow, requires multiple AAVE transactions)

**Risk Profile**:
- **Market Risk**: Full ETH price exposure (directional strategy)
- **Liquidation Risk**: AAVE liquidation if health factor < 1.0
- **Staking Risk**: LST protocol risk
- **Leverage Risk**: Amplified ETH price exposure (no hedging)
- **Max Drawdown**: 4% (leveraged staking volatility, not ETH price risk)

**Data Requirements**:
- ETH/USD spot prices
- LST prices and oracle prices
- AAVE lending rates
- Staking rewards data
- EIGEN rewards data
- AAVE risk parameters
- Gas costs
- Execution costs

---

### 5. USDT Market Neutral No Leverage Mode (`usdt_market_neutral_no_leverage`)

**Objective**: Market-neutral ETH staking strategy without leverage, hedged to USDT.

**Strategy Description**:
- Take `stake_allocation_eth` proportion of equity and buy ETH
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
- `stake_allocation_eth`: Configures proportion of equity for staking vs hedging
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
- `stake_allocation_eth`: 0.5 (50% to staking, 50% to hedge margin)
- `lending_enabled`: false
- `staking_enabled`: true
- `basis_trade_enabled`: true
- `borrowing_enabled`: false
- `rewards_mode`: "base_eigen_seasonal"
- `hedge_venues`: ["binance", "bybit", "okx"]
- `target_apy`: 0.08 (8%)

**Execution Flow**:
1. **Initial Setup** (backtest mode):
   - Split equity: `stake_allocation_eth` to ETH staking, `1 - stake_allocation_eth` to CEX margin
   - **Step 1**: Fund ALL CEXs simultaneously with USDT margin
     ```python
     wallet.USDT -= (binance + bybit + okx)
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
     wallet.ETH += eth_transfer
     # Stake ETH via LST protocol (based on lst_type)
     ```
   - **Key**: ALL perp shorts at same time, not sequential!
2. **Live Mode**: Read existing positions and rebalance as needed
3. **Rebalancing**:
   - Monitor delta neutrality (from risk monitor)
   - Adjust perp shorts if delta drift > `max_delta_drift`
   - Maintain `stake_allocation_eth` allocation between staking and hedge
4. **Deposits**: Scale up both legs proportionally
5. **Withdrawals**: Scale down both legs proportionally (1:1 with withdrawal amount)
6. **Tight Loop**: Position updates trigger sequential component chain (position_monitor → exposure_monitor → risk_monitor → pnl_monitor)

**Reserve Balance Management**:
- **Fast Withdrawals**: Maintain USDT reserve for immediate client redemptions
- **Reserve Threshold**: If reserve < `reserve_ratio` of total USDT, publish reserve_low event
- **Unwinding**: All withdrawals unwind 1:1 (close perp shorts first, then unstake LST)

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

### 6. USDT Market Neutral Mode (`usdt_market_neutral`)

**Objective**: Market-neutral leveraged ETH staking strategy, hedged to USDT.

**Strategy Description**:
- Take `stake_allocation_eth` proportion of equity and buy ETH
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
- `stake_allocation_eth`: Configures proportion of equity for leveraged staking vs hedging
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
- `stake_allocation_eth`: 0.5 (50% to leveraged staking, 50% to hedge margin)
- `lending_enabled`: true
- `staking_enabled`: true
- `basis_trade_enabled`: true
- `borrowing_enabled`: true
- `rewards_mode`: "base_eigen_seasonal"
- `hedge_venues`: ["binance", "bybit", "okx"]
- `target_apy`: 0.15 (15%)

**Execution Flow**:
1. **Initial Setup** (backtest mode):
   - Split equity: `stake_allocation_eth` to leveraged ETH staking, `1 - stake_allocation_eth` to CEX margin
   - **Step 1**: Fund ALL CEXs simultaneously with USDT margin
     ```python
     wallet.USDT -= (binance + bybit + okx)
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
     wallet.ETH += eth_transfer
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

**Reserve Balance Management**:
- **Fast Withdrawals**: Maintain USDT reserve for immediate client redemptions
- **Reserve Threshold**: If reserve < `reserve_ratio` of total USDT, publish reserve_low event
- **Unwinding**: All withdrawals unwind 1:1 (close perp shorts first, then unwind leveraged position)

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

## Strategy Manager Architecture

**PLANNED ARCHITECTURE**: Inheritance-based strategy modes with standardized wrapper actions (per strategy_manager_refactor.md)

### Inheritance-Based Interface
All strategy modes inherit from BaseStrategyManager and implement the same 5 wrapper actions:
- **entry_full**: Deploy capital according to strategy (initial setup)
- **entry_partial**: Scale up existing positions (deposits)
- **exit_partial**: Scale down existing positions (withdrawals)
- **exit_full**: Exit entire position (risk override)
- **sell_dust**: Convert non-share-class tokens to share class currency

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
- `hedge_allocation`: Distribution across hedging venues
- `stake_allocation_eth`: Proportion of equity for staking vs hedging

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
| USDT Market Neutral No Leverage | 8% | 2% | Medium | None (hedged) |
| USDT Market Neutral | 15% | 4% | High | None (hedged) |

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
| **USDT Market Neutral No Leverage** | Binance, Bybit, OKX | Lido/EtherFi | Alchemy |
| **USDT Market Neutral** | Binance, Bybit, OKX | Lido/EtherFi, AAVE V3, Morpho | Alchemy, Instadapp |

### Venue Selection Logic

**CEX Venues**:
- **Spot Trades**: Binance preferred (unless atomic on-chain transaction requires DEX)
- **Perp Shorts**: Distributed based on `hedge_allocation` ratios
- **Allocation Logic**: `hedge_allocation_binance: 0.4`, `hedge_allocation_bybit: 0.3`, `hedge_allocation_okx: 0.3`

**DeFi Venues**:
- **Staking**: Lido (wstETH) or EtherFi (weETH) based on `lst_type` config
- **Lending**: AAVE V3 (extensible to Compound, Morpho, etc.)
- **Flash Loans**: Morpho (via Instadapp middleware) for atomic leverage operations
- **DEX Swaps**: Uniswap (for atomic on-chain transactions)

**Infrastructure**:
- **Wallet Transfers**: Alchemy (Web3 wrapper) for all on-chain operations
- **Atomic Transactions**: Instadapp middleware for complex multi-step operations
- **Data Access**: All venues provide market data and execution interfaces

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
- **USDT Market Neutral modes**: Must split equity between staking and perp margin
- **`stake_allocation_eth`**: Proportion for ETH staking (locked on-chain)
- **`1 - stake_allocation_eth`**: Proportion for CEX margin (in USDT)
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
