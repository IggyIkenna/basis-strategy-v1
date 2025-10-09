# Venue Architecture Specification

**Last Reviewed**: January 2025  
**Status**: ✅ Canonical architecture based on consolidated principles  
**Source**: Consolidated from CANONICAL_ARCHITECTURAL_PRINCIPLES.md, MODES.md, and task specifications

**Canonical References**:
- **Strategy Modes**: `docs/MODES.md` - Complete strategy mode specifications and venue requirements
- **Execution Architecture**: `docs/MODES.md` - Venue-based execution architecture and instruction types
- **Venue Selection Logic**: `docs/MODES.md` - CEX, DeFi, and infrastructure venue mapping
- **Capital Allocation**: `docs/MODES.md` - Strategy constraints and capital allocation logic

## Overview

This document defines the venue-based execution architecture for the basis-strategy-v1 platform. The architecture supports multiple execution venues (CEX, DeFi, Infrastructure) with mode-agnostic components and venue-specific execution interfaces.

## Core Architecture Principles

### 1. Venue-Based Execution Architecture (Canonical Principle #8)
**CRITICAL REQUIREMENT**: Execution manager is venue-centric, with configuration mapping action types to venues for each strategy.

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

### Base Execution Interface
All venue interfaces inherit from `BaseExecutionInterface`:

```python
class BaseExecutionInterface(ABC):
    """Base class for all execution interfaces."""
    
    @abstractmethod
    async def execute_trade(self, instruction: Dict, market_data: Dict) -> Dict:
        """Execute trade instruction."""
    
    @abstractmethod
    async def get_balance(self, asset: str, venue: Optional[str] = None) -> float:
        """Get balance for asset."""
    
    @abstractmethod
    async def get_position(self, symbol: str, venue: Optional[str] = None) -> Dict:
        """Get position for symbol."""
    
    @abstractmethod
    async def execute_transfer(self, instruction: Dict, market_data: Dict) -> Dict:
        """Execute transfer instruction."""
```

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
- **AAVE V3**: LST collateral supply and ETH borrowing for leverage loops
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
- **AAVE V3**: LST collateral supply and ETH borrowing for leverage loops
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
- **Dummy venue calls**: Execution interfaces make dummy calls to venues but don't wait for responses
- **Immediate completion**: Mark themselves complete to trigger downstream chain of updates
- **Data provider handles**: CSV vs DB routing for backtest mode
- **Time-based triggers**: Only time-based execution
- **Position monitor initialization**: Via strategy mode

### Live Mode
- **Real execution**: Using external APIs (testnet or production)
- **Real delays**: Transaction confirmations and API rate limits
- **Retry logic**: Exponential backoff for failed operations
- **External interfaces**: Provide data to position monitor

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

### Live Mode
- **Retry logic**: Wait 5s, retry with exponential backoff
- **Max attempts**: Maximum 3 attempts
- **Error logging**: Log error and pass failure down after max attempts
- **Continue execution**: Continue tight loop after non-critical errors

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

## Required Code Restructuring

### 1. Create Execution Manager
**Priority**: HIGH - Core missing component

**Reference**: `docs/MODES.md` - Execution Architecture section

**ARCHITECTURE**: Centralized ExecutionManager routes requests to execution type interfaces (wallet vs trade) which direct to venue client implementations (simulation for backtest vs different endpoints using env variable credentials for live).

**Required Implementation**:
```python
class ExecutionManager:
    """Centralized execution manager for venue-based instruction routing."""
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        self.execution_mode = execution_mode
        self.config = config
        self.execution_interfaces = {}  # wallet, trade, etc.
        self._initialize_execution_interfaces()
    
    def _initialize_execution_interfaces(self):
        """Initialize execution type interfaces (wallet, trade, etc.)."""
        # Create execution interfaces that handle different instruction types
        # Each interface routes to appropriate venue client implementations
        
    async def route_instruction(self, instruction_type: str, instruction: Dict, market_data: Dict) -> Dict:
        """Route instruction to appropriate execution type interface."""
        # Route to execution type interface (wallet_transfer, cex_trade, smart_contract)
        # Each interface handles venue client routing and credential management
        
    def _get_venue_credentials(self, venue: str, environment: str) -> Dict:
        """Get venue credentials based on environment (dev/staging/prod)."""
        # Route to appropriate environment-specific credentials from env.unified
        
    def _map_instruction_to_interface(self, instruction_type: str) -> str:
        """Map instruction type to execution interface."""
        # wallet_transfer -> TransferExecutionInterface
        # cex_trade -> CEXExecutionInterface  
        # smart_contract -> OnChainExecutionInterface
```

### 2. Fix Environment Variable Integration
**Priority**: HIGH - Critical for live trading

**SEPARATION OF CONCERNS**:
- **BASIS_DEPLOYMENT_MODE**: Controls port/host forwarding and dependency injection (local vs docker)
- **BASIS_ENVIRONMENT**: Controls venue credential routing (dev/staging/prod) and data sources (CSV vs DB)
- **BASIS_EXECUTION_MODE**: Controls venue execution behavior (backtest simulation vs live execution)

**Required Changes**:
- **Update CEX execution interface** to use environment-specific variables (follow LiveDataProvider pattern)
- **Implement BASIS_ENVIRONMENT routing** to select dev/staging/prod credentials
- **Add separate spot/futures client initialization** for Binance with environment-specific endpoints
- **Add testnet vs production endpoint routing** based on environment
- **Update OnChain execution interface** to use environment-specific Alchemy credentials
- **Add environment-specific network routing** (Sepolia for dev, Ethereum for prod)

### 3. Remove Transfer Manager Complexity
**Priority**: MEDIUM - Architectural cleanup

**Required Actions**:
- Remove `backend/src/basis_strategy_v1/core/rebalancing/transfer_manager.py`
- Move venue routing logic to execution manager
- Simplify strategy manager to use execution manager for all venue operations

### 4. Enhance Venue Configuration
**Priority**: MEDIUM - Configuration completeness

**PURPOSE**: Venue configuration files contain **static venue data only**:
- Order size constraints (min_order_size_usd, max_leverage)
- Trading parameters (tick_size, min_size)
- Protocol parameters (unstaking_period, liquidation_threshold)
- **NOT credentials** - credentials handled by environment variables

**Required Additions**:
- Add detailed static venue parameters to YAML files
- Add venue capability definitions (spot, futures, staking, etc.)
- **NO environment-specific sections** - credentials handled by env variables

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

## Comprehensive Implementation Roadmap

### Phase 1: Strategy Manager Refactor (CRITICAL PRIORITY)
**Based on**: strategy_manager_refactor.md + `docs/MODES.md` - Standardized Strategy Manager Architecture section

1. **Remove Transfer Manager Complexity**:
   - Delete `backend/src/basis_strategy_v1/core/rebalancing/transfer_manager.py` (1068 lines)
   - Remove all references to transfer manager in strategy manager

2. **Implement Inheritance-Based Strategy Modes**:
   - Create `BaseStrategyManager` with standardized wrapper actions
   - Implement 5 wrapper actions: `entry_full`, `entry_partial`, `exit_full`, `exit_partial`, `sell_dust`
   - Create strategy-specific implementations: `BTCBasisStrategyManager`, `ETHLeveragedStrategyManager`, etc.
   - **Reference**: `docs/MODES.md` - Standardized Strategy Manager Architecture section

3. **Create Strategy Factory**:
   - Implement strategy instance creation based on mode
   - Add strategy mode detection and instantiation

4. **Implement Equity Tracking System**:
   - Add comprehensive equity tracking in share class currency
   - Track assets minus debt (excluding futures positions)
   - Include AAVE aTokens, LST tokens, CEX balances, on-chain wallet balances

### Phase 2: Generic vs Mode-Specific Architecture Fix (CRITICAL PRIORITY)
**Based on**: 18_generic_vs_mode_specific_architecture.md

1. **Fix Exposure Monitor**:
   - Remove mode-specific logic (`if mode == 'btc_basis'`)
   - Implement config-driven parameters (`asset`, `share_class`)
   - Make component truly mode-agnostic

2. **Fix P&L Monitor**:
   - Ensure generic attribution logic across all modes
   - Add share_class awareness for reporting currency
   - Remove any mode-specific P&L calculation logic

3. **Validate Generic Components**:
   - Position Monitor: ✅ Already correctly implemented as generic
   - Risk Monitor: ✅ Already correctly implemented with config-driven parameters
   - Utility Manager: Ensure generic utility methods

### Phase 3: Execution Manager Implementation (HIGH PRIORITY)
**Based on**: execution_venue_integration.md, 19_venue_based_execution_architecture.md

1. **Create ExecutionManager class**:
   - Implement venue-based instruction routing
   - Add environment-specific credential routing
   - Integrate with existing execution interfaces
   - Add venue capability detection

2. **Fix Environment Variable Integration**:
   - Update CEX execution interface to use environment-specific variables
   - Implement proper credential routing based on `BASIS_ENVIRONMENT`
   - Add separate spot/futures client initialization for Binance
   - Add testnet vs production endpoint routing

3. **Implement Venue-Based Routing**:
   - Map action types from strategy manager to appropriate venues
   - Handle special cases like weETH/wstETH not available on Binance spot
   - Add venue selection logic based on strategy configuration

### Phase 4: Mode-Agnostic Architecture Implementation (HIGH PRIORITY)
**Based on**: 14_mode_agnostic_architecture_requirements.md

1. **Ensure Mode-Agnostic Components**:
   - Position Monitor: Generic monitoring tool ✅
   - P&L Monitor: Must work for both backtest and live modes
   - Exposure Monitor: Generic exposure calculation
   - Risk Monitor: Generic risk assessment
   - Utility Manager: Generic utility methods

2. **Fix Mode-Specific Components**:
   - Strategy Manager: Strategy mode specific by nature ✅
   - Data Subscriptions: Heavily strategy mode dependent
   - Execution Interfaces: Strategy mode aware for data subscriptions

### Phase 5: Venue Configuration Enhancement (MEDIUM PRIORITY)
1. **Enhance Venue Configuration Files**:
   - Add detailed venue parameters to existing YAML files
   - Add environment-specific configuration sections
   - Add venue capability definitions (spot, futures, staking, etc.)
   - Add missing Instadapp configuration

2. **Update Configuration Loading**:
   - Implement venue configuration merging in config manager
   - Add venue-specific configuration validation
   - Test configuration loading for all strategy modes

### Phase 6: Execution Interface Enhancement (MEDIUM PRIORITY)
1. **Align Execution Interfaces**:
   - Implement missing market data integration features
   - Add atomic operation support for DeFi venues
   - Enhance error handling and retry logic
   - Add proper venue client initialization

2. **Data Provider Integration**:
   - Complete live data provider venue API integration
   - Add venue-specific data loading to historical data provider
   - Implement market data snapshot generation for execution decisions

### Phase 7: Quality Gate Implementation (HIGH PRIORITY)
1. **Backtest Mode Quality Gates**:
   - Implement data provider initialization checks
   - Add venue data availability validation
   - Test data synchronization across venues

2. **Live Mode Quality Gates**:
   - Implement venue API health checks
   - Add credential validation
   - Test endpoint connectivity

3. **Integration Testing**:
   - Run venue integration quality gates
   - Run configuration quality gates
   - Run execution quality gates
   - Fix any issues found during validation

### Phase 8: Dust Management System (MEDIUM PRIORITY)
**Based on**: dust_management_system task

1. **Implement Dust Detection**:
   - Add configurable threshold (`dust_delta`)
   - Detect non-share-class tokens (EIGEN, ETHFI rewards)
   - Priority over normal rebalancing

2. **Implement Dust Conversion**:
   - Automatic conversion to share class currency
   - Integration with strategy manager
   - Handle weETH staking rewards

### Phase 9: Reserve Management System (MEDIUM PRIORITY)
**Based on**: reserve_management_system task

1. **Implement Reserve Monitoring**:
   - Monitor reserves against `reserve_ratio` config parameter
   - Publish reserve_low events for downstream consumers
   - Handle fast vs slow withdrawal execution modes

2. **Implement Withdrawal Handling**:
   - All strategies unwind 1:1 with withdrawals
   - Fast unwinding using available reserves
   - Slow unwinding requiring unwinding locked positions

## Comprehensive Codebase Analysis Against Canonical Requirements

### 1. Strategy Manager Refactor Requirements ⚠️
**Status**: PARTIALLY IMPLEMENTED - Needs major refactoring per strategy_manager_refactor.md

**Current Issues**:
- **Complex Rebalancing System**: Still uses complex transfer_manager.py (1068 lines) that should be removed
- **Missing Inheritance-Based Strategy Modes**: No standardized wrapper actions (entry_full, entry_partial, exit_full, exit_partial, sell_dust)
- **No Strategy Factory**: Missing strategy instance creation based on mode
- **Mode-Specific Logic**: Has mode checks that should be config-driven parameters

**Required Implementation** (per strategy_manager_refactor.md):
```python
class BaseStrategyManager:
    """Base strategy manager with standardized wrapper actions."""
    
    def __init__(self, config: Dict, mode: str):
        self.config = config
        self.mode = mode
        self.share_class = config.get('share_class')
        self.asset = config.get('asset')
    
    async def entry_full(self, equity: float, market_data: Dict) -> List[InstructionBlock]:
        """Enter full position (initial setup or large deposits)."""
        pass
    
    async def entry_partial(self, equity: float, market_data: Dict) -> List[InstructionBlock]:
        """Scale up position (small deposits or PnL gains)."""
        pass
    
    async def exit_full(self, equity: float, market_data: Dict) -> List[InstructionBlock]:
        """Exit entire position (withdrawals or risk override)."""
        pass
    
    async def exit_partial(self, equity: float, market_data: Dict) -> List[InstructionBlock]:
        """Scale down position (small withdrawals or risk reduction)."""
        pass
    
    async def sell_dust(self, equity: float, market_data: Dict) -> List[InstructionBlock]:
        """Convert non-share-class tokens to share class currency."""
        pass

class BTCBasisStrategyManager(BaseStrategyManager):
    """BTC Basis strategy implementation."""
    pass

class ETHLeveragedStrategyManager(BaseStrategyManager):
    """ETH Leveraged strategy implementation."""
    pass
```

### 2. Generic vs Mode-Specific Architecture Requirements ⚠️
**Status**: MAJOR VIOLATIONS - Components have incorrect mode-specific logic

**Critical Violations**:

#### Position Monitor ❌
**Current**: Generic monitoring tool ✅
**Issue**: Correctly implemented as generic

#### Exposure Monitor ❌
**Current**: Uses mode-specific logic instead of config-driven parameters
```python
# ❌ WRONG: Mode-specific logic
mode = self.config.get('mode')
if mode == 'btc_basis':
    return self._calculate_btc_exposure()
```
**Required**: Config-driven parameters
```python
# ✅ CORRECT: Config-driven parameters
asset = self.config.get('asset')  # Which deltas to monitor
share_class = self.config.get('share_class')  # Reporting currency
```

#### P&L Monitor ❌
**Current**: Mode-agnostic but missing share_class awareness
**Required**: Generic attribution logic that only cares about share_class for reporting

#### Risk Monitor ❌
**Current**: Uses mode-specific parameters correctly ✅
**Issue**: Correctly implemented with config-driven parameters

#### Strategy Manager ❌
**Current**: Has mode-specific logic but wrong implementation
**Required**: Inheritance-based strategy modes with standardized wrapper actions

### 3. Environment Variable Integration Gap ⚠️
**Impact**: Live trading will fail due to incorrect credential routing

**Current Implementation Issues**:
- **Live Data Provider**: ✅ Correctly implements environment variable routing using `BASIS_DEV__CEX__BINANCE_SPOT_API_KEY` pattern
- **Execution Interfaces**: ❌ Use hardcoded config keys instead of environment-specific routing
- **Missing BASIS_ENVIRONMENT Routing**: ❌ No logic to route based on `BASIS_ENVIRONMENT` (dev/staging/prod) to select appropriate credentials
- **Backtest Mode Misunderstanding**: ❌ Execution interfaces should NOT require credentials or heartbeat tests in backtest mode

**Required Implementation** (per architecture_updates.md):
```python
def _get_venue_credentials(self, venue: str, environment: str, execution_mode: str) -> Dict:
    """Route to appropriate environment-specific credentials based on BASIS_ENVIRONMENT and BASIS_EXECUTION_MODE."""
    if execution_mode == 'backtest':
        # Backtest mode: Execution interfaces exist for CODE ALIGNMENT only
        # NO credentials needed - NO heartbeat tests - NO real API calls
        # Data source (CSV vs DB) is handled by DATA PROVIDER, not venue execution manager
        # Venues are simulated based on data loaded by data provider
        return {
            'simulation_mode': True,
            'no_credentials_required': True,
            'no_heartbeat_tests': True,
            'data_source_handled_by_data_provider': True
        }
    elif execution_mode == 'live':
        # Live mode: Use real APIs (testnet for dev, mainnet for prod)
        if environment == 'dev':
            return {
                'api_key': os.getenv(f'BASIS_DEV__CEX__{venue.upper()}_API_KEY'),
                'secret': os.getenv(f'BASIS_DEV__CEX__{venue.upper()}_SECRET'),
                'testnet': True,
                'network': 'sepolia',
                'heartbeat_tests_required': True
            }
        elif environment == 'staging':
            return {
                'api_key': os.getenv(f'BASIS_STAGING__CEX__{venue.upper()}_API_KEY'),
                'secret': os.getenv(f'BASIS_STAGING__CEX__{venue.upper()}_SECRET'),
                'testnet': True,
                'network': 'sepolia',
                'heartbeat_tests_required': True
            }
        elif environment == 'production':
            return {
                'api_key': os.getenv(f'BASIS_PROD__CEX__{venue.upper()}_API_KEY'),
                'secret': os.getenv(f'BASIS_PROD__CEX__{venue.upper()}_SECRET'),
                'testnet': False,
                'network': 'ethereum',
                'heartbeat_tests_required': True
            }
```

### 4. Missing Execution Manager ⚠️
**Impact**: Strategy manager cannot properly route instructions to venues
**Solution**: Create centralized execution manager with venue-based routing

### 5. Transfer Manager Complexity ⚠️
**Impact**: Overly complex architecture that doesn't align with canonical principles
**Solution**: Remove transfer manager and move logic to execution manager

### 6. Incomplete Venue Client Initialization ⚠️
**Impact**: Missing separate spot/futures clients and environment-specific configuration
**Solution**: Enhance venue client initialization with proper environment routing

## Summary of Critical Issues

### 🚨 **CRITICAL PRIORITY** (Must Fix First):
1. **Strategy Manager Refactor**: Remove transfer_manager.py, implement inheritance-based strategy modes
2. **Generic vs Mode-Specific Architecture**: Fix Exposure Monitor and P&L Monitor to use config-driven parameters
3. **Environment Variable Integration**: Fix execution interfaces to use BASIS_ENVIRONMENT routing
4. **Execution Manager**: Create centralized venue-based instruction routing

### ⚠️ **HIGH PRIORITY**:
5. **Mode-Agnostic Architecture**: Ensure components work for both backtest and live modes
6. **Venue-Based Routing**: Implement proper venue selection logic
7. **Quality Gates**: Implement backtest and live mode validation

### 📋 **MEDIUM PRIORITY**:
8. **Venue Configuration Enhancement**: Add detailed parameters and environment-specific sections
9. **Execution Interface Enhancement**: Add missing market data integration and atomic operations
10. **Dust Management System**: Implement dust detection and conversion
11. **Reserve Management System**: Implement reserve monitoring and withdrawal handling

## Validation Checklist

### Architecture Compliance
- [ ] Strategy manager uses inheritance-based strategy modes with standardized wrapper actions
- [ ] Transfer manager complexity removed (1068 lines deleted)
- [ ] Execution manager routes instructions from strategy manager to venues
- [ ] Environment variables properly routed based on BASIS_ENVIRONMENT
- [ ] Generic components use config-driven parameters, not mode-specific logic
- [ ] Mode-specific components are naturally strategy mode specific

### Component Quality
- [ ] Position Monitor: Generic monitoring tool ✅
- [ ] Exposure Monitor: Uses config-driven parameters (asset, share_class)
- [ ] P&L Monitor: Generic attribution logic with share_class awareness
- [ ] Risk Monitor: Generic risk assessment with config-driven parameters ✅
- [ ] Strategy Manager: Inheritance-based with standardized wrapper actions
- [ ] Execution Manager: Venue-based instruction routing

### Environment Integration
- [ ] CEX execution interface uses environment-specific variables
- [ ] OnChain execution interface uses environment-specific credentials
- [ ] Testnet vs production endpoint routing implemented
- [ ] Sepolia for dev vs Ethereum for prod network routing

### Quality Gates
- [ ] Backtest mode: Data provider initialization checks
- [ ] Live mode: Venue API health checks and credential validation
- [ ] Integration testing: All quality gates pass

---

**Status**: Document completed with comprehensive analysis of current state and required restructuring.

**Next Steps**: 
1. **CRITICAL**: Implement Strategy Manager refactor (remove transfer_manager.py, add inheritance-based modes)
2. **CRITICAL**: Fix Generic vs Mode-Specific architecture violations
3. **CRITICAL**: Fix environment variable integration in execution interfaces
4. **CRITICAL**: Create ExecutionManager class for venue-based routing
5. **HIGH**: Implement mode-agnostic architecture requirements
6. **HIGH**: Add quality gates for backtest and live mode validation
