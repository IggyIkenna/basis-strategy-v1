# Venue Architecture Specification

**Last Reviewed**: January 6, 2025  
**Status**: ✅ Focused on venue-based execution architecture  
**Scope**: Venue-specific architecture only - no duplication of other architectural content

**Canonical References**:
- **Strategy Modes**: `docs/MODES.md` - Complete strategy mode specifications and venue requirements
- **Execution Architecture**: `docs/MODES.md` - Venue-based execution architecture and instruction types
- **Venue Selection Logic**: `docs/MODES.md` - CEX, DeFi, and infrastructure venue mapping
- **Capital Allocation**: `docs/MODES.md` - Strategy constraints and capital allocation logic

## Overview

This document defines the venue-based execution architecture for the basis-strategy-v1 platform. The architecture supports multiple execution venues (CEX, DeFi, Infrastructure) with mode-agnostic components and venue-specific execution interfaces.

**Scope**: This document focuses specifically on venue-based execution architecture. For other architectural concerns, see:
- **Component Architecture**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`
- **Strategy Manager**: `docs/specs/05_STRATEGY_MANAGER.md`
- **Configuration Management**: `docs/specs/19_CONFIGURATION.md`
- **Quality Gates**: `docs/QUALITY_GATES.md`

## Core Architecture Principles

### 1. Three-Way Venue Interaction Architecture (Canonical Principle #8)
**CRITICAL REQUIREMENT**: Each venue has three distinct interaction types that must be handled separately.

**Three-Way Venue Interaction**:

**A. Market Data Feed (Public)**:
- Backtest: Historical CSV data loaded at startup
- Live: Real-time API connections with heartbeat tests
- Component: DataProvider
- No credentials needed for backtest

**B. Order Handling (Private, Credentials in Live Only)**:
- Backtest: Simulated execution, always returns success
- Live: Real order submission, await confirmation
- Component: Execution interfaces
- Startup test: Verify API connection (no actual order)

**C. Position Updates (Private, Credentials in Live Only)**:
- Backtest: Position monitor updates via simulation (stateful - cannot recover after restart)
- Live: Position monitor queries venue for actual positions (stateless - can recover after restart)
- Component: Position Monitor
- Part of tight loop reconciliation

**Key Principles**:
- **Action Type to Venue Mapping**: Execution manager maps action types from strategy manager to appropriate venues
- **Strategy Manager Defines Actions**: Strategy manager defines action types, not specific venues/interfaces
- **Environment-Specific Clients**: Each venue needs clients with live, testnet, and simulation modes
- **Mode-Agnostic Components**: Position monitor, exposure monitor, risk monitor, P&L monitor work across all venues
- **Config-Driven Parameters**: Components use configuration parameters instead of venue-specific logic

### 2. Execution Venue Mapping (From MODES.md)
**Venue Selection Rules**:
- **Spot Trades**: Binance spot (preferred) unless part of atomic on-chain transaction (then DEX)
  - **Exception**: weETH and wstETH not supported on Binance spot - use staking venues directly (preferred for buying) or DEX (faster but more expensive for selling)
- **Wallet Transfers**: Always on-chain via Alchemy (Web3 wrapper)
- **Lending/Borrowing**: Currently AAVE (extensible to other venues like Compound)
- **Flash Loans**: Morpho (via Instadapp middleware) for atomic leverage operations
- **Perp Shorts**: CEX venues based on `hedge_allocation` ratios (0 = skip venue)
- **Staking/Unstaking**: Lido or EtherFi based on `lst_type` configuration

## Available Venues

**Reference**: `docs/MODES.md` - Execution Venue Summary section

### CEX Venues
- **Binance**: Spot + perpetual futures trading
- **Bybit**: Perpetual futures trading
- **OKX**: Perpetual futures trading

### DeFi Venues
- **AAVE V3**: Lending/borrowing operations
- **Lido**: ETH staking (wstETH)
- **EtherFi**: ETH staking (weETH)
- **Morpho**: Flash loans

### Infrastructure Venues
- **Alchemy**: Web3 RPC provider and wallet operations
- **Uniswap**: DEX swaps for atomic transactions
- **Instadapp**: Atomic transaction middleware (wrapper for complex multi-step operations)

## Strategy Mode Venue Requirements

**Reference**: `docs/MODES.md` - Strategy Mode Specifications section

Each strategy mode has specific venue requirements based on its configuration:

### Venue Usage by Strategy Mode
- **Pure Lending**: AAVE V3 + Alchemy only
- **BTC Basis**: Binance, Bybit, OKX + Alchemy
- **ETH Basis**: Binance, Bybit, OKX + Alchemy  
- **ETH Staking Only**: Lido/EtherFi + Alchemy
- **ETH Leveraged**: Lido/EtherFi, AAVE V3, Morpho + Alchemy, Instadapp
- **USDT Market Neutral No Leverage**: Binance, Bybit, OKX, Lido/EtherFi + Alchemy
- **USDT Market Neutral**: Binance, Bybit, OKX, Lido/EtherFi, AAVE V3, Morpho + Alchemy, Instadapp

### Capital Allocation Strategy
**Reference**: `docs/MODES.md` - Capital Allocation Logic section

- **No Locked Capital Strategies**: All capital available for spot + perp positions
- **Locked Capital Strategies**: Must reserve capital for perp margin (USDT margin for market neutral)
- **Directional Strategies**: All capital can be staked (no hedging required)

## Venue Configuration Structure

### Environment Variables (From env.unified)
**CRITICAL**: All venue credentials are environment-specific and stored in env.unified:

**SEPARATION OF CONCERNS**:
- **BASIS_DEPLOYMENT_MODE**: Controls port/host forwarding and dependency injection (local vs docker)
- **BASIS_ENVIRONMENT**: Controls venue credential routing (dev/staging/prod) and data sources (CSV vs DB)
- **BASIS_EXECUTION_MODE**: Controls venue execution behavior (backtest simulation vs live execution)

```bash
# Development Environment - Venue Credentials
BASIS_DEV__ALCHEMY__PRIVATE_KEY=
BASIS_DEV__ALCHEMY__RPC_URL=
BASIS_DEV__ALCHEMY__WALLET_ADDRESS=
BASIS_DEV__ALCHEMY__NETWORK=sepolia
BASIS_DEV__ALCHEMY__CHAIN_ID=11155111

BASIS_DEV__CEX__BINANCE_SPOT_API_KEY=
BASIS_DEV__CEX__BINANCE_SPOT_SECRET=
BASIS_DEV__CEX__BINANCE_FUTURES_API_KEY=
BASIS_DEV__CEX__BINANCE_FUTURES_SECRET=

BASIS_DEV__CEX__BYBIT_API_KEY=
BASIS_DEV__CEX__BYBIT_SECRET=

BASIS_DEV__CEX__OKX_API_KEY=
BASIS_DEV__CEX__OKX_SECRET=
BASIS_DEV__CEX__OKX_PASSPHRASE=

# Production Environment - Venue Credentials
BASIS_PROD__ALCHEMY__PRIVATE_KEY=
BASIS_PROD__ALCHEMY__RPC_URL=
BASIS_PROD__ALCHEMY__WALLET_ADDRESS=
BASIS_PROD__ALCHEMY__NETWORK=mainnet
BASIS_PROD__ALCHEMY__CHAIN_ID=1

BASIS_PROD__CEX__BINANCE_SPOT_API_KEY=
BASIS_PROD__CEX__BINANCE_SPOT_SECRET=
BASIS_PROD__CEX__BINANCE_FUTURES_API_KEY=
BASIS_PROD__CEX__BINANCE_FUTURES_SECRET=

BASIS_PROD__CEX__BYBIT_API_KEY=
BASIS_PROD__CEX__BYBIT_SECRET=

BASIS_PROD__CEX__OKX_API_KEY=
BASIS_PROD__CEX__OKX_SECRET=
BASIS_PROD__CEX__OKX_PASSPHRASE=
```

### Venue Configuration Files
**Status**: Venue configuration files exist in `configs/venues/` directory.

**PURPOSE**: Venue configuration files contain **static venue data only**:
- Order size constraints (min_order_size_usd, max_leverage)
- Trading parameters (tick_size, min_size)
- Protocol parameters (unstaking_period, liquidation_threshold)
- **NOT credentials** - credentials handled by environment variables

**Current Structure**:
```
configs/venues/
├── aave_v3.yaml
├── alchemy.yaml
├── binance.yaml
├── bybit.yaml
├── etherfi.yaml
├── instadapp.yaml  # TODO-ADD: Missing atomic transaction middleware
├── lido.yaml
├── morpho.yaml
└── okx.yaml
```

**Missing Infrastructure Venue**:
- **Instadapp**: Atomic transaction middleware wrapper for complex multi-step operations

## Execution Interface Architecture

### Tight Loop Integration
All execution interfaces are integrated with the tight loop reconciliation pattern:

```python
class BaseExecutionInterface(ABC):
    """Base class for all execution interfaces."""
    
    @abstractmethod
    async def execute_trade(self, instruction: Dict, market_data: Dict) -> Dict:
        """Execute trade instruction and trigger tight loop reconciliation."""
    
    @abstractmethod
    async def get_balance(self, asset: str, venue: Optional[str] = None) -> float:
        """Get balance for asset."""
    
    @abstractmethod
    async def get_position(self, symbol: str, venue: Optional[str] = None) -> Dict:
        """Get position for symbol."""
    
    @abstractmethod
    async def execute_transfer(self, instruction: Dict, market_data: Dict) -> Dict:
        """Execute transfer instruction and trigger tight loop reconciliation."""
    
    async def _trigger_tight_loop(self, instruction: Dict, result: Dict):
        """Trigger tight loop: execution → position_monitor → reconciliation."""
        # Update position monitor
        # ❌ INCORRECT:
        # await self.position_monitor.update_state()(result)
        
        # ✅ CORRECT:
        self.position_monitor.update_state(
            timestamp=timestamp,
            trigger_source='execution_manager',
            execution_deltas=result
        )
        
        # Verify reconciliation
        await self._verify_reconciliation(instruction, result)
```

**Note**: The `update_state()` method signature is standardized across all components per Reference-Based Architecture pattern. See [01_POSITION_MONITOR.md](specs/01_POSITION_MONITOR.md) for complete interface specification.

### CEX Execution Interface
**File**: `backend/src/basis_strategy_v1/core/interfaces/cex_execution_interface.py`

**Responsibilities**:
- Execute spot and perpetual trades on CEX venues
- Handle CCXT client initialization for live mode
- Simulate trades in backtest mode
- Update position monitor with balance changes
- Log events via event logger

**Key Features**:
- **Per-exchange futures prices**: Uses venue-specific futures data
- **Execution cost modeling**: Handles slippage and fees
- **Market data integration**: Uses real-time data for live execution
- **Error handling**: Retry logic with exponential backoff

### On-Chain Execution Interface
**File**: `backend/src/basis_strategy_v1/core/interfaces/onchain_execution_interface.py`

**Responsibilities**:
- Execute smart contract operations (AAVE, staking, swaps)
- Handle Web3 client initialization
- Manage gas cost estimation
- Support both atomic and sequential operations

**Key Features**:
- **Web3 integration**: Alchemy RPC provider
- **Contract interactions**: AAVE, Lido, EtherFi, Uniswap
- **Gas optimization**: Dynamic gas price estimation
- **Transaction batching**: Atomic operation support

### Transfer Execution Interface
**File**: `backend/src/basis_strategy_v1/core/interfaces/transfer_execution_interface.py`

**Responsibilities**:
- Execute venue-to-venue transfers
- Coordinate between CEX and on-chain interfaces
- Handle wallet transfers and deposits/withdrawals

## Execution Interface Factory

**File**: `backend/src/basis_strategy_v1/core/interfaces/execution_interface_factory.py`

**Purpose**: Create and configure execution interfaces based on strategy requirements.

```python
class ExecutionInterfaceFactory:
    @staticmethod
    def create_interface(
        interface_type: str,
        execution_mode: str,
        config: Dict[str, Any],
        data_provider=None
    ) -> BaseExecutionInterface:
        """Create execution interface based on type and mode."""
    
    @staticmethod
    def create_all_interfaces(
        execution_mode: str,
        config: Dict[str, Any],
        data_provider=None
    ) -> Dict[str, BaseExecutionInterface]:
        """Create all required interfaces for strategy."""
```

## Strategy-Venue Mapping

### Pure Lending Mode
**Required Venues**:
- **AAVE V3**: USDT lending/supply operations
- **Alchemy**: Wallet transfers (if any)
- **No CEX venues**: No spot trades or perp positions
- **No staking venues**: No LST operations

### BTC Basis Trading Mode
**Required Venues**:
- **Binance**: BTC spot trades + BTC perp shorts (40% allocation)
- **Bybit**: BTC perp shorts (30% allocation)
- **OKX**: BTC perp shorts (30% allocation)
- **Alchemy**: Wallet transfers (if any)
- **No DeFi venues**: No lending or staking operations

### ETH Basis Trading Mode
**Required Venues**:
- **Binance**: ETH spot trades + ETH perp shorts (40% allocation)
- **Bybit**: ETH perp shorts (30% allocation)
- **OKX**: ETH perp shorts (30% allocation)
- **Alchemy**: Wallet transfers (if any)
- **No DeFi venues**: No lending or staking operations

### ETH Staking Only Mode
**Required Venues**:
- **Lido or EtherFi**: ETH staking/unstaking (based on `lst_type`)
- **Alchemy**: Wallet transfers and ETH conversions
- **No CEX venues**: No spot trades or perp positions
- **No lending venues**: No AAVE operations

### ETH Leveraged Mode
**Required Venues**:
- **Lido or EtherFi**: ETH staking/unstaking (based on `lst_type`)
- **AAVE V3**: LST collateral supply and ETH borrowing for leveraged staking
- **Morpho**: Flash loans for atomic leverage operations
- **Alchemy**: Wallet transfers and ETH conversions
- **Instadapp**: Atomic transaction middleware
- **No CEX venues**: No spot trades or perp positions

### USDT Market Neutral No Leverage Mode
**Required Venues**:
- **Lido or EtherFi**: ETH staking/unstaking (based on `lst_type`)
- **Binance**: ETH perp shorts (40% allocation)
- **Bybit**: ETH perp shorts (30% allocation)
- **OKX**: ETH perp shorts (30% allocation)
- **Alchemy**: Wallet transfers and ETH conversions
- **No lending venues**: No AAVE operations

### USDT Market Neutral Mode
**Required Venues**:
- **Lido or EtherFi**: ETH staking/unstaking (based on `lst_type`)
- **AAVE V3**: LST collateral supply and ETH borrowing for leveraged staking
- **Binance**: ETH perp shorts (40% allocation)
- **Bybit**: ETH perp shorts (30% allocation)
- **OKX**: ETH perp shorts (30% allocation)
- **Morpho**: Flash loans for atomic leverage operations
- **Alchemy**: Wallet transfers and ETH conversions
- **Instadapp**: Atomic transaction middleware

## Capital Allocation Strategy

### No Locked Capital Strategies
**Examples**: BTC Basis, ETH Basis
- **All capital available**: For spot + perp positions
- **No maintenance margin issues**: Can use all asset for perp shorts
- **No cross-venue issues**: No locked capital on AAVE or staking protocols

### Locked Capital with Hedging Strategies
**Examples**: USDT Market Neutral modes
- **Must reserve capital**: For perp margin (cannot use LST as CEX collateral)
- **`stake_allocation_eth`**: Proportion for ETH staking (locked on-chain)
- **`1 - stake_allocation_eth`**: Proportion for CEX margin (in USDT)
- **Why USDT margin**: Forces P&L to move in equally offsetting directions

### Directional Strategies
**Examples**: ETH Leveraged, ETH Staking Only
- **No hedging required**: All capital can be staked
- **No cross-venue capital allocation**: Single venue focus
- **Flash loan potential**: Morpho/Instadapp for atomic leverage operations

## Execution Modes

### Backtest Mode
- **Simulated execution**: Using historical data and execution cost models
- **No real API calls**: All operations simulated
- **Tight loop reconciliation**: Simulated position updates with immediate reconciliation
- **Data provider handles**: CSV vs DB routing for backtest mode
- **Time-based triggers**: Only time-based execution
- **Position monitor initialization**: Via strategy mode
- **Stateful**: Cannot recover after restart

### Live Mode
- **Real execution**: Using external APIs (testnet or production)
- **Real delays**: Transaction confirmations and API rate limits
- **Retry logic**: Exponential backoff for failed operations
- **Tight loop reconciliation**: Real position queries with reconciliation verification
- **Stateless**: Can recover after restart by querying venue positions

### Testnet Mode
- **Live execution**: On testnets (Sepolia, testnet exchanges)
- **Real transaction costs**: But with testnet tokens
- **Full integration testing**: Without production risk

## Data Flow Architecture

### Market Data Integration
**Live Trading Market Data Usage**:
- **Real-time prices**: For execution decisions
- **Data freshness checks**: Alert if data > 30 seconds old
- **Funding rate monitoring**: For perp trade decisions
- **Volatility assessment**: For execution timing optimization

### Execution Cost Modeling
- **Arrival Price**: Last known price when instruction issued
- **Fill Price**: Actual price filled at
- **Execution Cost**: arrival_price - fill_price (slippage)
- **Backtest**: Fixed slippage from execution cost model
- **Live**: Real slippage from order fill

## Error Handling and Resilience

### Backtest Mode
- **Fail fast**: Fail fast and pass failure down codebase
- **Immediate feedback**: Errors should be immediately visible
- **Stop execution**: Stop tight loop on critical errors
- **Stateful**: Cannot recover after restart

### Live Mode
- **Retry logic**: Wait 5s, retry with exponential backoff
- **Max attempts**: Maximum 3 attempts
- **Error logging**: Log error and pass failure down after max attempts
- **Continue execution**: Continue tight loop after non-critical errors
- **Stateless**: Can recover after restart by querying venue positions

## Configuration Management

### Environment-Specific Configuration
**CRITICAL**: All venue credentials are environment-specific:
- **Development**: Sepolia testnet, testnet exchange APIs
- **Production**: Mainnet, production exchange APIs
- **Staging**: Can use either testnet or mainnet based on testing needs

### Configuration Loading
**File**: `backend/src/basis_strategy_v1/infrastructure/config/config_manager.py`

**Process**:
1. Load environment variables from env.unified
2. Load venue-specific configurations (when available)
3. Merge with strategy-specific overrides
4. Validate configuration completeness
5. Initialize venue clients based on configuration

## Current Codebase Analysis

### Venue Configuration Files ✅
**Status**: Venue configuration files exist in `configs/venues/` directory.

**Available Files**:
- `aave_v3.yaml` - AAVE V3 protocol configuration
- `alchemy.yaml` - Alchemy infrastructure configuration  
- `binance.yaml` - Binance exchange configuration
- `bybit.yaml` - Bybit exchange configuration
- `etherfi.yaml` - EtherFi staking configuration
- `lido.yaml` - Lido staking configuration
- `morpho.yaml` - Morpho flash loan configuration
- `okx.yaml` - OKX exchange configuration

**Current Structure**: Basic venue identification and type classification, but missing detailed configuration parameters needed for execution.

### Execution Interface Implementation ⚠️
**Current State**: Execution interfaces exist but have significant gaps compared to canonical specifications.

**Critical Issues Identified**:

1. **Environment Variable Integration Gap**:
   - CEX execution interface uses environment-specific config keys (`BASIS_DEV__CEX__BINANCE_SPOT_API_KEY`, `BASIS_PROD__CEX__BYBIT_API_KEY`) 
   - Live data provider correctly implements environment variable routing, execution interfaces should follow same pattern

2. **Missing Execution Manager**:
   - No centralized execution manager to route instructions from strategy manager to appropriate venues
   - Strategy manager directly calls execution interfaces instead of going through venue-based routing
   - Missing venue-based instruction routing as specified in canonical architecture

3. **Incomplete Venue Client Initialization**:
   - CEX interface only initializes basic CCXT clients
   - Missing separate spot/futures clients for Binance as specified in canonical architecture
   - Missing environment-specific client configuration (dev/staging/prod)

4. **Transfer Manager Complexity**:
   - Current `transfer_manager.py` is overly complex (1068 lines) and should be removed per canonical architecture
   - Strategy manager should handle venue routing directly through execution manager

### Data Provider Integration ⚠️
**Current State**: Data providers have partial venue integration.

**Issues Identified**:
- Live data provider correctly implements environment variable routing for venue credentials
- Historical data provider loads venue-specific data but may not align with execution interface needs
- Missing market data snapshot generation for execution decisions in live mode

### Configuration Management ⚠️
**Current State**: Configuration loading exists but has gaps.

**Issues Identified**:
- Config manager loads environment variables but doesn't route them to execution interfaces
- Execution interfaces expect different config structure than what's provided
- Missing venue-specific configuration merging for execution interfaces

## Venue Implementation Status

**Reference**: For implementation details, see:
- **Strategy Manager Architecture**: `docs/specs/05_STRATEGY_MANAGER.md` - Strategy manager refactor and inheritance-based modes
- **Execution Manager**: `docs/specs/06_EXECUTION_MANAGER.md` - Centralized execution manager for venue routing
- **Configuration Management**: `docs/specs/19_CONFIGURATION.md` - Environment variable integration and venue configuration
- **Architectural Decisions**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Generic vs mode-specific architecture and component design

### Current Implementation Gaps
- **Missing Execution Manager**: No centralized venue-based instruction routing
- **Environment Variable Integration**: Execution interfaces need BASIS_ENVIRONMENT routing
- **Venue Configuration Enhancement**: Need detailed venue parameters in YAML files
- **Transfer Manager Complexity**: Overly complex architecture needs simplification

## Quality Gates

### Backtest Mode Quality Gates
**Data Provider Initialization Check**:
- [ ] Historical data provider loads all required venue data for strategy mode
- [ ] Data availability validation passes for backtest date range
- [ ] All venue-specific data sources are accessible (CSV files or database)
- [ ] Data synchronization validation passes across all venues

### Live Mode Quality Gates  
**Venue Connectivity Check**:
- [ ] All required venues respond to API health checks
- [ ] Environment-specific credentials are valid and accessible
- [ ] Testnet vs production endpoints are correctly configured
- [ ] Market data feeds are active and responsive
- [ ] Web3 connections are established for DeFi venues

### Venue Integration Gates
- [ ] All required venues can be initialized for each strategy mode
- [ ] Venue credentials are properly loaded from environment variables
- [ ] Execution interfaces can execute trades on all required venues
- [ ] Error handling works correctly for all venues
- [ ] Market data integration works for live trading

### Configuration Gates
- [ ] Venue configuration files exist and are properly structured
- [ ] Environment variables are properly loaded and validated
- [ ] Strategy-venue mapping works correctly
- [ ] Configuration validation passes for all strategy modes

### Execution Gates
- [ ] Backtest mode can simulate trades on all venues
- [ ] Live mode can execute real trades on all venues
- [ ] Testnet mode works correctly for all venues
- [ ] Atomic operations work correctly for DeFi venues
- [ ] Transfer operations work correctly between venues

## Implementation References

**For detailed implementation roadmaps, see**:
- **Strategy Manager Refactor**: `docs/specs/05_STRATEGY_MANAGER.md` - Inheritance-based strategy modes and transfer manager removal
- **Generic vs Mode-Specific Architecture**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Component architecture and mode-agnostic design
- **Execution Manager Implementation**: `docs/specs/06_EXECUTION_MANAGER.md` - Venue-based instruction routing
- **Configuration Management**: `docs/specs/19_CONFIGURATION.md` - Environment variable integration and venue configuration
- **Quality Gate Implementation**: `docs/QUALITY_GATES.md` - Venue-specific quality checks and validation
- **Dust Management System**: `docs/specs/05_STRATEGY_MANAGER.md` - Dust detection and conversion
- **Reserve Management System**: `docs/specs/05_STRATEGY_MANAGER.md` - Reserve monitoring and withdrawal handling

## Codebase Analysis References

**For detailed codebase analysis, see**:
- **Strategy Manager Analysis**: `docs/specs/05_STRATEGY_MANAGER.md` - Current implementation gaps and refactor requirements
- **Component Architecture Analysis**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Generic vs mode-specific architecture violations
- **Environment Integration Analysis**: `docs/specs/19_CONFIGURATION.md` - Environment variable integration gaps
- **Execution Manager Analysis**: `docs/specs/06_EXECUTION_MANAGER.md` - Missing execution manager and venue routing
- **Quality Gate Analysis**: `docs/QUALITY_GATES.md` - Venue-specific quality gate requirements

---

**Status**: Document focused on venue-based execution architecture with cross-references to other architectural documents.

**Next Steps**: 
1. **CRITICAL**: Implement Execution Manager for venue-based instruction routing
2. **CRITICAL**: Fix environment variable integration in execution interfaces
3. **CRITICAL**: Implement tight loop reconciliation pattern in execution interfaces
4. **HIGH**: Add quality gates for backtest and live mode validation
5. **MEDIUM**: Enhance venue configuration files with detailed parameters
