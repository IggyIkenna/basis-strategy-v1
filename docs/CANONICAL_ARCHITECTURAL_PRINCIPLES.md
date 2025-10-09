# Canonical Architectural Principles

**Last Reviewed**: October 8, 2025  
**Status**: ✅ Consolidated from all .cursor/tasks/ files

## Overview

This document consolidates all architectural principles from the 27 `.cursor/tasks/` files to serve as the canonical source of truth for the documentation refactor. These principles must be followed by all components and documented consistently across all documentation.

## Core Architecture Principles

### 1. No Hardcoded Values (Task 06)
**CRITICAL RULE**: NEVER use hardcoded values to fix issues. Always use proper data flow and component integration.

**Forbidden**:
- Hardcoding any values (liquidity index, rates, prices, configuration values, etc.)
- Bypassing the data provider or configuration loading architecture
- Using static values instead of dynamic data
- Fixing issues with "magic numbers"

**Required**:
- Use data provider for all external data and configuration loading for all components
- Query data provider for current timestamp
- Pass data through proper component chain
- Use dynamic data, not static values

### 2. Singleton Pattern (Task 13)
**CRITICAL REQUIREMENT**: All components must use the singleton pattern to ensure single instances across the entire run.

**Requirements**:
- Each component must be a SINGLE instance across the entire run
- All components must share the SAME config instance
- All components must share the SAME data provider instance
- No duplicate component initialization
- Synchronized data flows between all components

### 3. Mode-Agnostic Architecture (Task 14)
**CRITICAL REQUIREMENT**: Components must be mode-agnostic where appropriate, but strategy mode-specific where necessary.

**Mode-Agnostic Components**:
- Position Monitor: Generic monitoring tool, not strategy mode specific
- P&L Monitor: Must work for both backtest and live modes
- Exposure Monitor: Generic exposure calculation
- Risk Monitor: Generic risk assessment
- Utility Manager: Generic utility methods

**Mode-Specific Components**:
- Strategy Manager: Strategy mode specific by nature
- Data Subscriptions: Heavily strategy mode dependent
- Execution Interfaces: Strategy mode aware for data subscriptions

### 4. Tight Loop Architecture (Task 10)
**MANDATORY SEQUENCE**: Components MUST execute in chain sequential triggers after each action that requires position update (trade or wallet transfer) without exception. the component that triggers the action that requires position update must await chain completion before proceeding to the next action. For now we only allow the following sequence with tight loop architecture triggered by execution_managers calling position_monitor to update position either by simulating the update in backtest or by calling for a position refresh in live mode:

```
position_monitor → exposure_monitor → risk_monitor → pnl_monitor
```

**Execution Flow Options**:
- **Strategy Manager Path**: position_monitor → exposure_monitor → risk_monitor → pnl_monitor → strategy → execution_managers
- **Tight Loop Path**: position_monitor → exposure_monitor → risk_monitor → pnl_monitor → execution_managers

### 5. Clean Component Architecture (Task 16)
**CRITICAL REQUIREMENT**: Components must be designed to be naturally clean without needing state clearing or resetting.

**Forbidden**:
- Clearing/resetting component state to mask architectural problems
- Using "clean state" hacks instead of fixing root causes
- Having components that need to be "cleared" between runs

**Required**:
- Design components to be naturally clean without needing state clearing
- Fix root causes instead of using "clean state" hacks
- Ensure components are properly initialized with correct state from the start

### 6. Configuration Architecture (Task 08)
**CRITICAL REQUIREMENT**: All configuration must be loaded from YAML files and validated through Pydantic models.

**Required**:
- Load all configuration from YAML files (not hardcoded in code)
- Use environment variables only when specified in .env files
- Validate all configuration through Pydantic models
- Follow the YAML-based config structure (modes/venues/scenarios)

**Forbidden**:
- Hardcoding any configuration values (API keys, file paths, timeouts, etc.)
- Bypassing configuration loading architecture
- Using static configuration values instead of dynamic loading

### 6.1. Infrastructure Configuration Elimination
**CRITICAL DECISION**: JSON configs eliminated entirely - all infrastructure configuration handled through environment variables and hardcoded defaults.

**Environment Variables (Environment-Specific)**:
- `BASIS_REDIS_URL` - Redis connection URL
- `BASIS_DATA_DIR` - Data directory path  
- `BASIS_RESULTS_DIR` - Results storage path
- `BASIS_API_CORS_ORIGINS` - API CORS origins (comma-separated)
- `BASIS_API_PORT` - API port
- `BASIS_API_HOST` - API host
- `BASIS_EXECUTION_MODE` - Execution mode (backtest/live) - controls venue execution behavior
- `BASIS_DATA_MODE` - Data source mode (csv/db) - controls data source for backtest mode only, NOT related to data persistence or execution routing

**Hardcoded Defaults (Always True for Realistic Backtesting)**:
- **Cross-network simulations**: Always `true` - enables realistic transfer simulations
- **Cross-network transfers**: Always `true` - enables realistic cross-venue operations
- **Rate usage**: Always use live rates (never fixed rates for realistic modeling)

**Eliminated (Live Trading Only)**:
- **Testnet configuration**: Live trading concern, not needed for backtest focus
- **Complex infrastructure configs**: Over-engineered for current backtest focus

### 6.2. Unified Health System
**CRITICAL DECISION**: Single unified health system with 2 endpoints only - `/health` (fast heartbeat) and `/health/detailed` (comprehensive).

**Key Principles**:
- **No authentication required** on health endpoints
- **Mode-aware filtering** (backtest vs live components)
- **Real-time health checks** (no caching)
- **No health history tracking** (performance optimized)
- **200+ error codes preserved** across all components

**Benefits**:
- Simplified config structure: Only YAML files for strategy/venue/share_class configs
- Environment-appropriate: Infrastructure settings properly separated by environment
- Hardcoded sensible defaults: No need to configure obvious settings
- Reduced complexity: Eliminated JSON config loading and merging logic
- Focused on backtest: Removed live trading complexity

**Future: Testnet Implementation**:
When implementing live trading, testnet configuration should be:
- Testnet endpoints in environment variables (per-environment)
- Testnet-specific logic in execution components
- Simulation vs real execution mode flags

### 7. Generic vs Mode-Specific Architecture (Task 18)
**CRITICAL DISTINCTION**: Components should be generic and mode-agnostic, but care about specific config parameters rather than strategy mode.

**Generic Components**:
- Position Monitor: Generic monitoring tool
- P&L Attribution: Generic attribution logic across all modes
- Exposure Monitor: Generic exposure calculation
- Risk Monitor: Generic risk assessment
- Utility Manager: Generic utility methods

**P&L Monitor Must Be Mode-Agnostic**:
- Single logic for both backtest and live modes
- No mode-specific if statements in P&L calculations
- Universal balance calculation across all venues (wallets, smart contracts, CEX spot, CEX derivatives)
- Generic P&L attribution system: all attribution types calculated uniformly across modes
- Unused attributions return 0 P&L (no mode-specific logic)

**Centralized Utility Methods**:
- Liquidity index, market prices, conversions must be centralized
- NOT in execution interfaces
- Shared access across all components that need these utilities
- Global data states accessed using current event loop timestamp

**Config-Driven Parameters**:
- `share_class`: What P&L to report in (ETH or USDT)
- `asset`: Which deltas to monitor/measure directional exposure in
- `lst_type`: Which staking venue for staking strategies
- `hedge_allocation`: For basis strategies
- `venue_configs`: Which venues to use

**environment variables**:
- variables are stored in `env.unified` and overridden by `env.dev`, `env.staging`, `env.production`. they are used to control the behavior of the system in different environments. environment agnostic variables should NOT be stored in `env.unified`.
- `BASIS_EXECUTION_MODE`: Execution mode (backtest/live) - controls venue execution behavior
- `BASIS_DATA_MODE`: Data source mode (csv/db) - controls data source for backtest mode only
- `BASIS_ENVIRONMENT`: Environment type (dev/staging/prod)
- `BASIS_DEPLOYMENT_MODE`: Deployment type (local/docker)
- `BASIS_DATA_DIR`: Data directory
- `BASIS_RESULTS_DIR`: Results directory
- `BASIS_REDIS_URL`: Redis connection
- `BASIS_DEBUG`: Debug mode
- `BASIS_LOG_LEVEL`: Logging verbosity
- `BASIS_DATA_START_DATE`: Data start date
- `BASIS_DATA_END_DATE`: Data end date

### 8. Venue-Based Execution Architecture (Task 19)
**CRITICAL REQUIREMENT**: Execution manager is venue-centric, with configuration mapping action types to venues for each strategy.

**Venue Configuration**:
- Action type to venue mapping for each strategy
- Each venue needs clients with live, testnet, and simulation modes
- Environment determines which components are in what mode

**Available Venues**:
- **CEX**: Binance, Bybit, OKX (spot + perps)
- **DeFi**: AAVE V3, Lido, EtherFi, Morpho (flash loans)
- **Infrastructure**: Alchemy (Web3), Uniswap (DEX swaps), Instadapp (atomic transaction middleware)

### 9. Backtest vs Live Mode Architecture (Task 09)
**CRITICAL DISTINCTION**: System operates in two distinct modes with specific considerations.

**Backtest Mode**:
- Simulated execution with historical data
- Time-based triggers only
- Position monitor initialization via strategy mode is key
- First runtime loop must perform actions (no "do nothing" state)

**Live Mode**:
- Real execution with external APIs (testnet or production)
- Real delays and transaction confirmations
- Retry logic with exponential backoff
- External interfaces provide data to position monitor

**Shared Architecture**:
- Tight loop architecture maintained in both modes
- Sequential component execution
- State persistence across runs

### 10. P&L Calculator Mode-Agnostic (Task 15)
**CRITICAL FIX**: P&L calculator must be mode-agnostic and work for both backtest and live modes.

**Requirements**:
- Single logic for both backtest and live modes
- No mode-specific P&L calculation logic
- Universal balance calculation across all venues
- Centralized utility methods
- Generic P&L attribution system

**Forbidden**:
- Different P&L logic per mode
- Utility methods in execution interfaces
- Duplicated utility methods across components
- Mode-specific if statements in P&L calculations

## Quality Gate Requirements

### Current Status (Task 05)
- **Target**: 15/24 overall gates passing (60%+)
- **Current**: 8/24 passing
- **Critical Issues**: 1166% APY in pure lending (should be 3-8%)

### Quality Gate Categories
1. **Pure Lending Gates** (Task 02): APY must be 3-8%, balance-based P&L from aUSDT liquidity index. Quality gate apy rnages should exist for every strategy.
2. **BTC Basis Gates** (Task 04): 10/10 quality gates for BTC basis
3. **Scripts Directory Gates** (Task 03): 10/14 scripts must pass (70%+)
4. **Backtest Mode Gates** (Task 11): First runtime loop must perform actions
5. **Live Trading Gates** (Task 12): Client requirements determined by config YAML
6. **Tight Loop Gates**: Sequential component execution validation

## Data Flow Architecture

### Proper Data Flow
1. **Data Provider** loads all data at startup from data/ directory
2. **Execution Interfaces** query data provider for current timestamp data
3. **Position Monitor** receives data from execution interfaces
4. **Component Chain** passes data through proper sequence

### Data Sources
- **Market Data**: data/market/ directory
- **Protocol Data**: data/protocol_data/ directory (AAVE, Lido, etc.)
- **Historical Data**: data/ directory with timestamp-based files
- **Configuration**: configs/ directory with YAML files
- **Environment Variables**: .env files (only when specified)

## Component Integration Requirements

### Required Integration
1. **Data Provider**: Must load all data at startup
2. **Execution Interfaces**: Must query data provider for current data
3. **Position Monitor**: Must receive data from execution interfaces
4. **Strategy Manager**: Must coordinate data flow through components

### State Management
- **No reset**: All components must maintain state across runs
- **Persistent state**: State must survive between iterations
- **Cross-run continuity**: Position, risk, and P&L data must persist

## Error Handling

### Backtest Mode
- **Fail fast**: Fail fast and pass failure down codebase
- **Immediate feedback**: Errors should be immediately visible
- **Stop execution**: Stop tight loop on critical errors

### Live Mode
- **Retry logic**: Wait 5s, retry with exponential backoff
- **Max attempts**: Maximum 3 attempts
- **Error logging**: Log error and pass failure down after max attempts
- **Continue execution**: Continue tight loop after non-critical errors

## Additional Critical Principles

### 11. Strategy Manager Refactor (Task strategy_manager_refactor)
**CRITICAL REQUIREMENT**: Remove complex rebalancing system and implement inheritance-based strategy modes.

**Key Changes**:
- **Remove**: `backend/src/basis_strategy_v1/core/rebalancing/transfer_manager.py` (too complex)
- **Remove**: `docs/specs/13_ADVANCED_REBALANCING.md` (strategies manage own rebalancing)
- **Implement**: Inheritance-based strategy modes with standardized wrapper actions
- **Standardized Actions**: All strategies use 5 wrapper actions (entry_full, entry_partial, exit_full, exit_partial, sell_dust)
- **Strategy Factory**: Create strategy instances based on mode
- **Fixed Wallet Assumption**: All deposits/withdrawals go to same on-chain wallet

### 12. Duplicate Risk Monitors Consolidation (Task 21)
**CRITICAL REQUIREMENT**: Consolidate duplicate risk monitor files.

**Files to Consolidate**:
- **CORRECT**: `backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py`
- **REMOVE**: `backend/src/basis_strategy_v1/core/rebalancing/risk_monitor.py` (duplicate)
- **Update**: Import in `rebalancing/__init__.py` to use correct location

### 13. Dust Management System (Task dust_management_system)
**REQUIREMENT**: Implement dust management for non-share-class tokens.

**Dust Tokens**:
- EIGEN, ETHFI, KING rewards from weETH staking
- Any tokens that are neither share class currency nor asset currency nor LST tokens

**Requirements**:
- Dust detection with configurable threshold (`dust_delta`)
- Automatic conversion to share class currency
- Priority over normal rebalancing
- Integration with strategy manager

### 14. Equity Tracking System (Task equity_tracking_system)
**REQUIREMENT**: Implement comprehensive equity tracking in share class currency.

**Equity Definition**:
- **Equity = Assets - Debt** (in share class currency)
- **Assets**: Tokens on actual wallets (not locked in smart contracts)
- **Debt**: Borrowed amounts across all venues
- **Exclusions**: Futures positions (tracked separately for hedging)

**Include in Equity**:
- AAVE aTokens (aUSDT, aETH)
- LST tokens (wstETH, weETH)
- CEX spot and margin balances
- On-chain wallet balances

**Exclude from Equity**:
- Locked assets (ETH stuck at EtherFi)
- Futures positions
- Pending transactions

---

**Source**: Consolidated from .cursor/tasks/ files 02-21 and additional tasks
**Canonical Reference**: This document serves as the single source of truth for all architectural principles
**Last Updated**: October 8, 2025
