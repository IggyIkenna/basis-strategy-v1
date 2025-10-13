# Reference Architecture - Canonical Source

**Status**: ⭐ **CANONICAL SOURCE** - Single source of truth for all architectural principles and patterns  
**Updated**: October 10, 2025  
**Purpose**: Comprehensive architectural reference for basis-strategy-v1 platform

---

## Overview

This document serves as the single canonical source of truth for all architectural principles, patterns, and decisions. All other documentation references this file for architectural guidance.

**Related Documentation**:
- **Historical ADRs**: [ARCHITECTURAL_DECISION_RECORDS.md](ARCHITECTURAL_DECISION_RECORDS.md) - Complete decision history
- **Component Specs**: [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) - Implementation details
- **Workflow Patterns**: [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - System workflows
- **Strategy Modes**: [MODES.md](MODES.md) - Strategy definitions
- **Venue Architecture**: [VENUE_ARCHITECTURE.md](VENUE_ARCHITECTURE.md) - Venue patterns

---

## I. Core Architectural Patterns

### 1. Component References (Set at Init)

All components follow the **Reference-Based Architecture** pattern where component references are set once during initialization and NEVER passed as runtime parameters:

- **config**: Dict (reference, never modified)
- **execution_mode**: str (BASIS_EXECUTION_MODE)
- **event_logger**: EventLogger instance
- **data_provider**: DataProvider instance
- **position_monitor**: PositionMonitor instance
- **exposure_monitor**: ExposureMonitor instance
- **risk_monitor**: RiskMonitor instance
- **pnl_calculator**: PnLCalculator instance
- **strategy_manager**: StrategyManager instance
- **venue_manager**: VenueManager instance

These references are stored in `__init__` and used throughout component lifecycle. Components NEVER receive these as method parameters during runtime.

### 2. Reference-Based Architecture Pattern

**Core Principle**: Components NEVER pass config, data_provider, or other components to each other. All shared resources are set as references during initialization and accessed directly throughout the component lifecycle.

**Singleton Pattern Per Request**:
- ONE config instance (mode-filtered + overrides applied) per request
- ONE data_provider instance (mode-specific data) per request
- ONE instance of each of the 11 components per request
- All components share these singleton instances via references

**Initialization Sequence** (per backtest/live request):
1. BacktestService/LiveTradingService receives request with strategy_name + overrides
2. Load full validated config (done once at app startup)
3. Slice config for strategy_name mode
4. Apply request overrides to sliced config (never modify global config)
5. Create fresh DataProvider via DataProviderFactory.create(execution_mode, config_slice)
6. Create fresh components with references to config_slice, data_provider, other components (11 components total)
7. Components store references in __init__, never create their own instances

**What Components Store at Init**:
- `self.config = config` (reference, NEVER modified)
- `self.data_provider = data_provider` (reference, call with timestamps)
- `self.position_monitor = position_monitor` (reference, call update_state methods)
- `self.execution_mode = execution_mode` (BASIS_EXECUTION_MODE)

**What Components NEVER Do**:
- Pass config/data_provider/components as method parameters (runtime)
- Create their own config/data instances
- Modify shared config
- Cache data snapshots (always query data_provider with timestamp)

**Code Structure Example**:
```python
class ExampleComponent:
    def __init__(self, config: Dict, data_provider: DataProvider, 
                 execution_mode: str, **component_refs):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        self.position_monitor = component_refs.get('position_monitor')
        self.event_logger = component_refs.get('event_logger')
        self.results_store = component_refs.get('results_store')
        
        # Initialize component-specific state
        self._state = {}
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs):
        # Use stored references directly
        market_data = self.data_provider.get_data(timestamp)
        position = self.position_monitor.get_current_position() if self.position_monitor else {}
        
        # Mode-aware behavior
        if self.execution_mode == 'backtest':
            # Backtest-specific logic
            pass
        elif self.execution_mode == 'live':
            # Live-specific logic
            pass
```

### 2. Shared Clock Pattern

**Core Principle**: EventDrivenStrategyEngine owns the authoritative timestamp and passes it to all component method calls. Components never advance time.

**Data Access Pattern**:
All components query data using:
```python
market_data = self.data_provider.get_data(timestamp)
```

**Time Constraint**:
Data retrieved MUST be <= timestamp to ensure:
1. All components in same loop use identical data
2. No forward-looking bias
3. If data updates mid-loop, stale snapshot prevents inconsistency

**Clock Owner: EventDrivenStrategyEngine**:
- Manages current_timestamp
- Advances timestamp per loop iteration
- Passes timestamp to all component update_state() calls

**Component Behavior**:
- Receive timestamp as parameter
- Query data_provider with that exact timestamp
- NEVER advance or modify timestamp
- NEVER cache data across timestamps

**Full Loop Flow**:
1. EventDrivenStrategyEngine: current_timestamp = next_timestamp
2. EventDrivenStrategyEngine: Calls _process_timestep(current_timestamp)
3. _process_timestep: Calls component.update_state(current_timestamp, ...)
4. Each component: market_data = self.data_provider.get_data(current_timestamp)
5. All components use same timestamp → same data snapshot

**Code Structure Example**:
```python
class EventDrivenStrategyEngine:
    def __init__(self, config: Dict, execution_mode: str, data_provider: DataProvider, components: Dict):
        self.config = config
        self.execution_mode = execution_mode
        self.data_provider = data_provider
        self.components = components
        self.current_timestamp = None
        self.timestamps = []  # Loaded from data_provider
    
    def run_backtest(self, start_date: str, end_date: str):
        self.timestamps = self.data_provider.get_timestamps(start_date, end_date)
        
        for timestamp in self.timestamps:
            self.current_timestamp = timestamp
            self._process_timestep(timestamp)
    
    def _process_timestep(self, timestamp: pd.Timestamp):
        # Pass timestamp to all components
        self.components['position_monitor'].update_state(timestamp, 'full_loop')
        self.components['exposure_monitor'].update_state(timestamp, 'full_loop')
        self.components['risk_monitor'].update_state(timestamp, 'full_loop')
        self.components['pnl_calculator'].update_state(timestamp, 'full_loop')
        # ... rest of full loop
```

### 3. Request Isolation Pattern

**Core Principle**: Each backtest/live request creates completely fresh instances of DataProvider, config slice, and all components. No state pollution between requests.

**App Startup (Once)**:
1. Load full config for all modes
2. Validate against Pydantic schemas
3. Check environment variables
4. Store validated global config (immutable)

**Per Request Lifecycle**:
1. **Request arrives** at BacktestService/LiveTradingService with:
   - strategy_name (mode)
   - config_overrides (optional)
   - start_date, end_date (backtest only)

2. **Config Slicing** (never modifies global config):
   - config_slice = global_config.get_mode(strategy_name)
   - config_slice.apply_overrides(request.config_overrides)

3. **Fresh DataProvider**:
   - data_provider = DataProviderFactory.create(execution_mode, config_slice)
   - Backtest: Load historical data for mode
   - Live: Initialize API clients for mode

4. **Fresh Components**:
   - Position Monitor initialized with initial_capital (backtest) or real sync (live)
   - All components created with references to config_slice, data_provider, other components
   - Component state starts fresh (no carryover from previous requests)

5. **Request Execution**:
   - EventDrivenStrategyEngine runs with fresh instances
   - Components share references, maintain state within this request only

6. **Request Completion**:
   - Save results
   - Discard all instances (GC cleanup)
   - Global config remains unchanged for next request

**Code Structure Example**:
```python
class BacktestService:
    def __init__(self, global_config: Dict):
        self.global_config = global_config  # Immutable, validated at startup
    
    async def run_backtest(self, request: BacktestRequest) -> str:
        # 1. Slice config for mode (never modifies global_config)
        config_slice = self._slice_config(request.strategy_name)
        
        # 2. Apply overrides to slice
        if request.config_overrides:
            config_slice = self._apply_overrides(config_slice, request.config_overrides)
        
        # 3. Create fresh DataProvider
        data_provider = DataProviderFactory.create('backtest', config_slice)
        data_provider.load_data_for_backtest(request.strategy_name, 
                                             request.start_date, 
                                             request.end_date)
        
        # 4. Create fresh components with references
        components = self._initialize_components(config_slice, data_provider, 'backtest')
        
        # 5. Run with fresh instances
        engine = EventDrivenStrategyEngine(config_slice, 'backtest', 
                                          data_provider, components)
        results = engine.run_backtest(request.start_date, request.end_date)
        
        # 6. Save results, discard instances (GC cleanup)
        self._save_results(request.request_id, results)
        return request.request_id
```

### 4. Synchronous Component Execution

**Core Principle**: Internal component methods are synchronous (no async/await). Only external API entry points, request queuing, and I/O operations use async.

**Implementation Requirements**:
1. Remove `async def` from all component `update_state()` and internal methods
2. Remove `await` from all inter-component calls
3. Use synchronous while/for loops for reconciliation polling
4. Keep `async def` ONLY for:
   - BacktestService.run_backtest() (API entry point)
   - LiveTradingService.start_live_trading() (API entry point)
   - Request queue management
   - I/O operations (Event Logger, Results Storage)

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

### 5. Mode-Aware Component Behavior

**Core Principle**: Components use BASIS_EXECUTION_MODE to conditionally execute backtest vs live logic. Same component, same code path, different behavior based on mode.

**Implementation Requirements**:
1. Store `self.execution_mode` at initialization (from BASIS_EXECUTION_MODE env var)
2. Use `if self.execution_mode == 'backtest':` / `elif self.execution_mode == 'live':` for conditional logic
3. Keep backtest and live code in same methods (not separate classes)
4. Minimize divergence - only differ when absolutely necessary

**Code Structure Example**:
```python
class PositionMonitor:
    def __init__(self, config: Dict, data_provider: DataProvider, execution_mode: str):
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode  # 'backtest' or 'live'
        
        # Initialize based on mode
        if self.execution_mode == 'backtest':
            self._initialize_backtest_positions()
        elif self.execution_mode == 'live':
            self._sync_live_positions()
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, 
                    execution_deltas: Dict = None):
        if execution_deltas:
            # Update simulated state (same for both modes)
            self._update_simulated_positions(execution_deltas)
            
            # Update real state (mode-specific)
            if self.execution_mode == 'backtest':
                # In backtest, simulated = real
                self._real_positions = self._simulated_positions.copy()
            elif self.execution_mode == 'live':
                # In live, query external APIs
                self._sync_live_positions()
        else:
            # Regular update (no execution deltas)
            self._update_positions(timestamp)
```

### 6. Async I/O for Non-Critical Path

**Accepted Exception**: Event Logger and Results Storage use async I/O operations as an exception to synchronous component execution.

**Rationale**:
- I/O operations (file/DB writes) are not in the critical trading path
- Async I/O provides performance benefits without affecting core logic
- Sequential awaits guarantee ordering without race conditions

**Implementation**:
- Event Logger: Direct async methods with await
- Results Storage: Queue-based async with background worker
- AsyncIO's single-threaded event loop prevents race conditions
- Queue ensures FIFO processing even with variable write times
- No dropped data or out-of-order writes

---

## II. Config-Driven Mode-Agnostic Architecture

### Core Principle
Components are mode-agnostic and use configuration to determine behavior rather than hardcoded mode-specific logic.

### Component Categories

**Mode-Agnostic Components** (use component_config):
- Position Monitor (tracks all positions)
- Exposure Monitor (config-driven asset tracking)
- Risk Monitor (config-driven risk types)
- P&L Calculator (config-driven attribution)
- Reconciliation Component (always the same)
- Execution Interface Manager (venue routing)
- Event Logger (logging is universal)
- Results Store (config-driven result types)

**Mode-Specific Components** (naturally strategy-specific):
- Strategy Manager (inherits from BaseStrategyManager, mode-specific logic)
- Data Provider (mode-specific subscriptions via DataProviderFactory)

### Configuration Structure

Each mode YAML contains:
- `data_requirements`: List of data types needed
- `component_config`: Dict of component behavior configs
  - `risk_monitor`: enabled_risk_types, risk_limits
  - `exposure_monitor`: track_assets, conversion_methods
  - `pnl_calculator`: attribution_types, reporting_currency
  - `strategy_manager`: strategy_type, actions, rebalancing_triggers
  - `execution_manager`: supported_actions, action_mapping
  - `results_store`: result_types, tracking configs

### Implementation Pattern

```python
class ModeAgnosticComponent:
    def __init__(self, config: Dict, data_provider, execution_mode: str, **refs):
        # Extract component-specific config
        self.component_config = config.get('component_config', {}).get('component_name', {})
        self.config_param = self.component_config.get('param', [])
        
        # Validate config
        self._validate_config()
    
    def process(self, data: Dict) -> Dict:
        results = {}
        
        # Process only configured items (no mode checks!)
        for item in self.config_param:
            if self._data_available(item, data):
                results[item] = self._calculate(item, data)
            else:
                results[item] = None  # Graceful handling
        
        return results
```

**References**:
- Implementation: CODE_STRUCTURE_PATTERNS.md sections 2-4
- Config schemas: 19_CONFIGURATION.md
- ADRs: ADR-052, ADR-053, ADR-054, ADR-055

---

## III. Architectural Principles

### 1. No Hardcoded Values
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

### 2. Singleton Pattern
**CRITICAL REQUIREMENT**: All components must use the singleton pattern to ensure single instances across the entire run.

**Requirements**:
- Each component must be a SINGLE instance across the entire run
- All components must share the SAME config instance
- All components must share the SAME data provider instance
- No duplicate component initialization
- Synchronized data flows between all components

### 3. Mode-Agnostic Architecture
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

### 4. Tight Loop Architecture
**CRITICAL DEFINITION**: Tight loop is the execution reconciliation pattern that ensures position updates are verified before proceeding to the next instruction.

**TIGHT LOOP DEFINITION**:
```
execution_manager → execution_interface_manager → position_update_handler → position_monitor → reconciliation_component
```

**Key Principles**:
- Execution manager sends ONE instruction at a time
- Execution Manager orchestrates Execution Interface Manager which routes to venue-specific interfaces
- Position Update Handler orchestrates tight loop reconciliation handshake
- Execution manager awaits reconciliation success before proceeding to next instruction
- Move to next instruction ONLY after reconciliation
- Happens WITHIN the broader full loop for each execution instruction
- Ensures no race conditions via sequential execution

**Full Loop Pattern** (Every Timestep):
```
time trigger → position_monitor → exposure_monitor → risk_monitor → strategy_manager → [tight loop if execution needed] → pnl_calculator → results_store
```

**Tight Loop Pattern** (Only When Execution Happens):
```
execution_manager → execution_interface_manager → position_update_handler → position_monitor → reconciliation_component
```

### 5. Clean Component Architecture
**CRITICAL REQUIREMENT**: Components must be designed to be naturally clean without needing state clearing or resetting.

**Forbidden**:
- Clearing/resetting component state to mask architectural problems
- Using "clean state" hacks instead of fixing root causes
- Having components that need to be "cleared" between runs

**Required**:
- Design components to be naturally clean without needing state clearing
- Fix root causes instead of using "clean state" hacks
- Ensure components are properly initialized with correct state from the start

### 6. Configuration Architecture
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

#### 6.1.1. Configuration Validation Architecture
**CRITICAL REQUIREMENT**: All configuration must be validated through comprehensive quality gates before deployment.

**Validation Framework**:
- **Mode Config Validation**: All mode YAML files validated against Pydantic models
- **Documentation Sync**: All config fields documented in component specs
- **Usage Sync**: All documented fields used in mode configurations
- **Strategy Intention**: Mode configs match intended strategy descriptions
- **Config Loading**: All configs load successfully at startup

**Quality Gate Scripts**:
- `validate_config_alignment.py` - Pydantic model alignment validation
- `test_config_documentation_sync_quality_gates.py` - Component spec sync validation
- `test_config_usage_sync_quality_gates.py` - Mode YAML usage validation
- `test_modes_intention_quality_gates.py` - Strategy intention validation
- `test_config_loading_quality_gates.py` - Config loading validation

**CI/CD Integration**:
- Quality gates run automatically in `platform.sh` before backend startup
- Quality gates run automatically in `docker/deploy.sh` before Docker build
- Builds fail immediately if any validation fails

**Business Logic Validation**:
- **Venue-LST validation**: LST type requires appropriate venue (weeth → etherfi, wsteth → lido)
- **Share class consistency**: USDT modes use USDT asset, ETH modes use ETH/BTC
- **Risk parameter alignment**: Warnings for high drawdown (>50%) or APY (>100%)
- **Basis trading validation**: Basis trading requires hedge venues
- **Market neutral validation**: Market neutral modes require hedge venues

#### 6.1. Infrastructure Configuration Elimination
**CRITICAL DECISION**: JSON configs eliminated entirely - all infrastructure configuration handled through environment variables and hardcoded defaults.

**Environment Variables (Environment-Specific)**:
- `BASIS_DATA_DIR` - Data directory path  
- `BASIS_RESULTS_DIR` - Results storage path
- `BASIS_API_CORS_ORIGINS` - API CORS origins (comma-separated)
- `BASIS_API_PORT` - API port
- `BASIS_API_HOST` - API host
- `BASIS_EXECUTION_MODE` - Execution mode (backtest/live) - controls venue execution behavior
- `BASIS_DATA_MODE` - Data source mode (csv/db) - controls data source for backtest mode only, NOT related to data persistence or execution routing. Can be set independently of BASIS_ENVIRONMENT (dev can use db, prod can use csv).

**Combined Behavior**:
- `BASIS_EXECUTION_MODE='backtest'` + `BASIS_DATA_MODE='csv'` = simulated execution with CSV data
- `BASIS_EXECUTION_MODE='live'` + `BASIS_DATA_MODE='api'` = real execution with API data
- Strategy mode config determines data subscriptions for both modes

**Hardcoded Defaults (Always True for Realistic Backtesting)**:
- **Cross-network simulations**: Always `true` - enables realistic transfer simulations
- **Cross-network transfers**: Always `true` - enables realistic cross-venue operations
- **Rate usage**: Always use live rates (never fixed rates for realistic modeling)

#### 6.2. Unified Health System
**CRITICAL DECISION**: Single unified health system with 2 endpoints only - `/health` (fast heartbeat) and `/health/detailed` (comprehensive).

**Key Principles**:
- **No authentication required** on health endpoints
- **Mode-aware filtering** (backtest vs live components)
- **Real-time health checks** (no caching)
- **No health history tracking** (performance optimized)
- **200+ error codes preserved** across all components

### 7. Config-Driven Mode-Agnostic Architecture
**CRITICAL DISTINCTION**: Components should be generic and mode-agnostic, using configuration parameters to drive behavior instead of mode-specific logic.

**Generic Components**:
- Position Monitor: Generic monitoring tool
- P&L Attribution: Generic attribution logic across all modes
- Exposure Monitor: Generic exposure calculation
- Risk Monitor: Generic risk assessment
- Utility Manager: Generic utility methods

**Config-Driven Component Behavior**:
- Components use configuration parameters instead of mode-specific if statements
- Each mode specifies which data types, risk types, and attribution types to use
- Components gracefully handle missing data by returning zeros or skipping calculations
- No hardcoded mode logic in component implementations

**P&L Monitor Must Be Mode-Agnostic**:
- Single logic for both backtest and live modes
- No mode-specific if statements in P&L calculations
- Universal balance calculation across all venues (wallets, smart contracts, CEX spot, CEX derivatives)
- Generic P&L attribution system: all attribution types calculated uniformly across modes
- Unused attributions return 0 P&L (no mode-specific logic)
- Attribution types specified in config: `attribution_types: ["supply_yield", "funding_pnl", "delta_pnl", "transaction_costs"]`

**Exposure Monitor Must Be Mode-Agnostic**:
- Generic exposure calculation using config-driven asset tracking
- Track assets specified in config: `track_assets: ["BTC", "USDT", "ETH"]`
- Conversion methods specified in config: `conversion_methods: {"BTC": "usd_price", "USDT": "direct"}`
- No mode-specific asset handling logic

**Risk Monitor Must Be Mode-Agnostic**:
- Generic risk assessment using config-driven risk types
- Risk types specified in config: `enabled_risk_types: ["aave_health_factor", "cex_margin_ratio", "funding_risk"]`
- Risk limits specified in config: `risk_limits: {"aave_health_factor_min": 1.1, "cex_margin_ratio_min": 0.2}`
- No mode-specific risk calculation logic

**Data Provider Abstraction Layer**:
- Base DataProvider class with standardized interface
- Mode-specific data providers inherit from base class
- Standardized data structure returned to all components
- Data requirements specified in config: `data_requirements: ["btc_spot_prices", "btc_futures_prices", "btc_funding_rates"]`

**DataProvider Factory Pattern**:
```python
class DataProviderFactory:
    @staticmethod
    def create(execution_mode: str, config: Dict) -> DataProvider:
        mode = config['mode']
        data_requirements = config.get('data_requirements', [])
        
        # Create mode-specific data provider
        if mode == 'pure_lending':
            provider = PureLendingDataProvider(execution_mode, config)
        elif mode == 'btc_basis':
            provider = BTCBasisDataProvider(execution_mode, config)
        # ... etc
        
        # Validate that provider can satisfy data requirements
        provider.validate_data_requirements(data_requirements)
        return provider
```

**Standardized Data Structure**:
```python
def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
    return {
        'market_data': {
            'prices': {'BTC': 45000.0, 'ETH': 3000.0, 'USDT': 1.0},
            'rates': {'funding_binance_btc': 0.0001, 'aave_usdt_supply': 0.05}
        },
        'protocol_data': {
            'aave_indexes': {'aUSDT': 1.05, 'aETH': 1.02},
            'oracle_prices': {'weETH': 1.0256, 'wstETH': 1.0150}
        }
    }
```

**Centralized Utility Methods**:
- Liquidity index, market prices, conversions must be centralized
- NOT in execution interfaces
- Shared access across all components that need these utilities
- Global data states accessed using current event loop timestamp

### 8. Three-Way Venue Interaction Architecture
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

**Available Venues**:
- **CEX**: Binance, Bybit, OKX (spot + perps)
- **DeFi**: AAVE V3, Lido, EtherFi, Morpho (flash loans)
- **Infrastructure**: Alchemy (Web3), Uniswap (DEX swaps), Instadapp (atomic transaction middleware)

### 9. Execution Interface Factory (Extended)

**Position Interface Creation**:
- Creates both execution and position monitoring interfaces
- Uses same credentials and venue configuration
- Handles both backtest (simulation) and live (real API) modes

**Initialization Dependencies**:
- Position Monitor depends on Execution Interface Factory
- Execution Interface Factory must be initialized before Position Monitor

**Factory Methods**:
```python
@staticmethod
def create_position_interface(venue: str, execution_mode: str, config: Dict) -> BasePositionInterface:
    """Create position monitoring interface for a specific venue."""

@staticmethod
def get_position_interfaces(venues: List[str], execution_mode: str, config: Dict) -> Dict[str, BasePositionInterface]:
    """Create position monitoring interfaces for multiple venues."""
```

**Position Interface Types**:
- **CEX Position Interface**: Binance, Bybit, OKX position monitoring
- **OnChain Position Interface**: AAVE, Morpho, Lido, EtherFi position monitoring
- **Transfer Position Interface**: Wallet position monitoring

**Architecture Benefits**:
- Same credentials (API keys, endpoints) as execution interfaces
- Same venues (from `configs/modes/*.yaml`) as execution
- Maintains canonical factory pattern consistency
- Avoids credential management duplication
- Follows DRY principles

### 10. Backtest vs Live Mode Architecture
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
- Tight loop (execution reconciliation) maintained in both modes
- Sequential component execution (no concurrency)
- Direct function call communication (no Redis)
- State persistence across runs

### 11. P&L Calculator Mode-Agnostic
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

### 12. Strategy Manager Refactor
**CRITICAL REQUIREMENT**: Remove complex rebalancing system and implement inheritance-based strategy modes.

**Key Changes**:
- **Remove**: `backend/src/basis_strategy_v1/core/rebalancing/transfer_manager.py` (too complex)
- **Remove**: `docs/specs/13_ADVANCED_REBALANCING.md` (strategies manage own rebalancing)
- **Implement**: Inheritance-based strategy modes with standardized wrapper actions
- **Standardized Actions**: All strategies use 5 wrapper actions (entry_full, entry_partial, exit_full, exit_partial, sell_dust)
- **Strategy Factory**: Create strategy instances based on mode
- **Fixed Wallet Assumption**: All deposits/withdrawals go to same on-chain wallet

### 13. Duplicate Risk Monitors Consolidation
**CRITICAL REQUIREMENT**: Consolidate duplicate risk monitor files.

**Files to Consolidate**:
- **CORRECT**: `backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py`
- **REMOVE**: `backend/src/basis_strategy_v1/core/rebalancing/risk_monitor.py` (duplicate)
- **Update**: Import in `rebalancing/__init__.py` to use correct location

### 14. Dust Management System
**REQUIREMENT**: Implement dust management for non-share-class tokens.

**Dust Tokens**:
- EIGEN, ETHFI, KING rewards from weETH staking
- Any tokens that are neither share class currency nor asset currency nor LST tokens

**Requirements**:
- Dust detection with configurable threshold (`dust_delta`)
- Automatic conversion to share class currency
- Priority over normal rebalancing
- Integration with strategy manager

### 14. Equity Tracking System
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

## IV. Key Architectural Decisions Summary

### Core ADRs (ADR-001 through ADR-009)

| ADR | Title | Date | Status | Summary |
|-----|-------|------|--------|---------|
| ADR-001 | Tight Loop Architecture Redefinition | 2025-01-06 | Accepted | Redefine tight loop as execution reconciliation pattern with proper full loop sequence. Ensures position verification after each instruction and eliminates race conditions. |
| ADR-002 | Redis Removal | 2025-01-06 | Accepted | Remove Redis entirely and use direct function calls for all component communication. Simplifies architecture and eliminates external dependencies. |
| ADR-003 | Reference-Based Architecture | 2025-01-06 | Accepted | Components receive all shared resources as references during initialization and never pass them as runtime parameters. Ensures consistent data access patterns. |
| ADR-004 | Shared Clock Pattern | 2025-01-06 | Accepted | EventDrivenStrategyEngine owns authoritative timestamp and passes it to all component method calls. Components never advance time, ensuring data consistency. |
| ADR-005 | Request Isolation Pattern | 2025-01-06 | Accepted | Each backtest/live request creates completely fresh instances of DataProvider, config slice, and all components. Prevents state pollution between requests. |
| ADR-006 | Synchronous Component Execution | 2025-01-06 | Accepted | Remove async/await from all internal component methods. Keep async only for external API entry points, request queuing, and I/O operations. |
| ADR-007 | 11 Component Architecture | 2025-01-06 | Accepted | Expand to 11 components by adding Reconciliation Component and elevating Position Update Handler to full component status. |
| ADR-008 | Three-Way Venue Interaction | 2025-01-06 | Accepted | Define three distinct venue interaction types: Market Data Feed (public), Order Handling (private), Position Updates (private). |
| ADR-009 | Separate Data Source from Execution Mode | 2025-01-09 | Accepted | Separate BASIS_DATA_MODE (csv/db) from BASIS_EXECUTION_MODE (backtest/live) to create clear separation of concerns. |

**Full ADR Details**: See [ARCHITECTURAL_DECISION_RECORDS.md](ARCHITECTURAL_DECISION_RECORDS.md) for complete rationale, consequences, and implementation details.

### Configuration and Infrastructure ADRs (ADR-010 through ADR-044)

| ADR | Title | Date | Status | Summary |
|-----|-------|------|--------|---------|
| ADR-010 | Configuration Separation of Concerns | 2025-01-06 | Accepted | Implement proper configuration hierarchy with clear separation of concerns using YAML-based mode system. |
| ADR-011 | Live Data Provider Architecture | 2025-01-06 | Accepted | Implement LiveDataProvider with same interface as HistoricalDataProvider for seamless backtest/live switching. |
| ADR-012 | Execution Interface Architecture | 2025-01-06 | Accepted | Implement execution interfaces with seamless backtest/live switching using factory pattern. |
| ADR-039 | Configuration Architecture: YAML-Based Mode System | 2025-01-06 | Accepted | Use YAML-based configuration with mode-specific files and centralized loading. |
| ADR-040 | Config Validation: Fail-Fast, No Silent Defaults | 2025-01-06 | Accepted | Do NOT use .get('value', 'fallback') pattern for config access. Explicit failures better than silent wrong behavior. |
| ADR-042 | Config Infrastructure Components | 2025-01-06 | Accepted | Centralized configuration infrastructure with health monitoring and validation. |

### Component and Data Flow ADRs

| ADR | Title | Date | Status | Summary |
|-----|-------|------|--------|---------|
| ADR-041 | Component Data Flow Architecture | 2025-01-06 | Accepted | Aligned with canonical patterns: Shared Clock, Reference-Based Architecture, Request Isolation. |
| ADR-043 | BacktestService Configuration Integration | 2025-01-06 | Accepted | BacktestService must use existing config infrastructure for dynamic configuration loading. |
| ADR-044 | Live Trading Data Flow Integration | 2025-01-06 | Accepted | Strategy Manager receives real-time market data as input parameter for unified interface. |
| ADR-057 | ML Strategy Integration Architecture | 2025-01-10 | Accepted | Extend platform with ML strategy modes using optional data provider methods, new strategy manager implementations, and graceful degradation for missing ML data/APIs. |

### Service Architecture ADRs

| ADR | Title | Date | Status | Summary |
|-----|-------|------|--------|---------|
| ADR-021 | Live Trading Architecture | 2025-01-06 | Accepted | Service orchestration pattern with BacktestService and LiveTradingService. |
| ADR-046 | Live Trading Service Architecture | 2025-01-06 | Accepted | Create LiveTradingService to orchestrate live trading strategies, mirroring BacktestService pattern. |

---

## IV. Component Integration Patterns

### 1. Component Initialization Pattern (15/17 specs)
**Recurring Pattern**: All components follow consistent initialization with references.

```python
def __init__(self, config: Dict, data_provider: DataProvider, 
             execution_mode: str, **component_refs):
    # Store references (NEVER modified)
    self.config = config
    self.data_provider = data_provider
    self.execution_mode = execution_mode
    
    # Store component references
    self.position_monitor = component_refs.get('position_monitor')
    self.exposure_monitor = component_refs.get('exposure_monitor')
    self.risk_monitor = component_refs.get('risk_monitor')
    self.event_logger = component_refs.get('event_logger')
    self.results_store = component_refs.get('results_store')
    
    # Initialize component-specific state
    self._state = {}
```

### 2. Component Communication Pattern (Universal)
**Pattern**: Direct method calls only, no Redis/pub-sub, synchronous execution.

```python
# Components communicate via direct method calls
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    # Call other components directly
    position = self.position_monitor.get_current_position()
    exposure = self.exposure_monitor.get_current_exposure()
    risk_metrics = self.risk_monitor.get_current_risk_metrics()
    
    # No async/await for internal calls
    # No Redis messaging
    # No pub/sub patterns
```

### 3. Data Access Pattern (15/17 specs)
**Pattern**: Timestamp-based queries, no caching across timestamps, data provider enforces data <= timestamp.

```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    # Always query with timestamp
    market_data = self.data_provider.get_data(timestamp)
    
    # Never cache data across timestamps
    # Data provider enforces data <= timestamp constraint
    # All components in same loop use identical timestamp → identical data
```

### 4. Mode-Aware Behavior Pattern (9/17 specs)
**Pattern**: Components use execution_mode for conditional logic.

```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    if self.execution_mode == 'backtest':
        # Backtest-specific logic
        self._handle_backtest_logic(timestamp)
    elif self.execution_mode == 'live':
        # Live-specific logic
        self._handle_live_logic(timestamp)
    else:
        raise ValueError(f"Unknown execution mode: {self.execution_mode}")
```

### 5. Error Handling Pattern
**Pattern**: Backtest fails fast, live retries with exponential backoff.

```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    try:
        # Component logic
        self._process_logic(timestamp)
    except Exception as e:
        if self.execution_mode == 'backtest':
            # Fail fast in backtest
            raise e
        elif self.execution_mode == 'live':
            # Retry with exponential backoff in live
            self._retry_with_backoff(timestamp, e)
```

---

## V. Quality Gates and Validation

### Quality Gate Requirements

**Current Status**:
- **Target**: 15/24 overall gates passing (60%+)
- **Current**: 8/24 passing
- **Critical Issues**: 1166% APY in pure lending (should be 3-8%)

### Quality Gate Categories

1. **Pure Lending Gates**: APY must be 3-8%, balance-based P&L from aUSDT liquidity index. Quality gate APY ranges should exist for every strategy.
2. **BTC Basis Gates**: 10/10 quality gates for BTC basis
3. **Scripts Directory Gates**: 10/14 scripts must pass (70%+)
4. **Backtest Mode Gates**: First runtime loop must perform actions
5. **Live Trading Gates**: Client requirements determined by config YAML
6. **Tight Loop Gates**: Sequential component execution validation

### Testing Requirements

**MANDATORY**: Every completed task must include minimum 80% unit test coverage

**Target Coverage**:
- 80% unit and integration test coverage overall
- 100% e2e test coverage
- No task is complete without comprehensive tests

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

## VI. Implementation References

### Component Specifications
- **Component Overview**: [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md)
- **Position Monitor**: [specs/01_POSITION_MONITOR.md](specs/01_POSITION_MONITOR.md)
- **Exposure Monitor**: [specs/02_EXPOSURE_MONITOR.md](specs/02_EXPOSURE_MONITOR.md)
- **Risk Monitor**: [specs/03_RISK_MONITOR.md](specs/03_RISK_MONITOR.md)
- **P&L Calculator**: [specs/04_PNL_CALCULATOR.md](specs/04_PNL_CALCULATOR.md)
- **Strategy Manager**: [specs/05_STRATEGY_MANAGER.md](specs/05_STRATEGY_MANAGER.md)
- **Execution Manager**: [specs/06_EXECUTION_MANAGER.md](specs/06_EXECUTION_MANAGER.md)
- **Execution Interface Manager**: [specs/07_EXECUTION_INTERFACE_MANAGER.md](specs/07_EXECUTION_INTERFACE_MANAGER.md)
- **Event Logger**: [specs/08_EVENT_LOGGER.md](specs/08_EVENT_LOGGER.md)
- **Results Store**: [specs/18_RESULTS_STORE.md](specs/18_RESULTS_STORE.md)
- **Data Provider**: [specs/09_DATA_PROVIDER.md](specs/09_DATA_PROVIDER.md)
- **Position Update Handler**: [specs/11_POSITION_UPDATE_HANDLER.md](specs/11_POSITION_UPDATE_HANDLER.md)
- **Reconciliation Component**: [specs/10_RECONCILIATION_COMPONENT.md](specs/10_RECONCILIATION_COMPONENT.md)
- **Configuration**: [specs/19_CONFIGURATION.md](specs/19_CONFIGURATION.md)
- **Health Error Systems**: [specs/17_HEALTH_ERROR_SYSTEMS.md](specs/17_HEALTH_ERROR_SYSTEMS.md)

### Workflow and Pattern Documentation
- **Workflow Patterns**: [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)
- **Strategy Modes**: [MODES.md](MODES.md)
- **Venue Architecture**: [VENUE_ARCHITECTURE.md](VENUE_ARCHITECTURE.md)
- **API Documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

### Historical Documentation
- **ADR Details**: [ARCHITECTURAL_DECISION_RECORDS.md](ARCHITECTURAL_DECISION_RECORDS.md)
- **Deployment Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **User Guide**: [USER_GUIDE.md](USER_GUIDE.md)
- **Getting Started**: [GETTING_STARTED.md](GETTING_STARTED.md)

---

## Summary

This canonical reference consolidates all architectural principles, patterns, and decisions into a single source of truth. It provides:

1. **Core Architectural Patterns**: Six fundamental patterns that define how the system operates
2. **Architectural Principles**: 14 critical principles that must be followed by all components
3. **Key Architectural Decisions**: Summary of 44 ADRs with links to detailed historical records
4. **Component Integration Patterns**: Five recurring patterns found across component specifications
5. **Quality Gates and Validation**: Testing requirements and quality gate criteria
6. **Implementation References**: Complete cross-reference to all related documentation

**Canonical Source Hierarchy**:
1. **REFERENCE_ARCHITECTURE_CANONICAL.md** (this document) - Highest authority
2. **ARCHITECTURAL_DECISION_RECORDS.md** - Historical ADR details
3. **MODES.md** - Strategy mode specifications
4. **VENUE_ARCHITECTURE.md** - Venue execution patterns
5. **Component specs** - Implementation details
6. **Guide docs** - Workflow and usage patterns

All architectural conflicts should be resolved using this hierarchy, with this document serving as the ultimate authority for architectural decisions.

---

## VII. Frontend Component Architecture

### Overview
Frontend follows component-based architecture with clear separation of concerns:
- **Wizard flow** for configuration
- **Results display** for analytics
- **Live trading controls** for execution
- **Authentication** for security

### Key Patterns

#### 1. Component Isolation
Each component is self-contained with clear props interface:
- No global state (except auth context)
- Props-driven rendering
- Type safety via TypeScript

#### 2. API Integration
Centralized API client pattern:
- Single source of API calls (services/api.ts)
- Retry logic for 503 errors
- Error handling and logging

#### 3. Analytics Display
Results page uses tabbed interface:
- **Overview**: Metric cards grid
- **Charts**: Plotly interactive charts
- **Events**: Virtualized event log

#### 4. Real-time Updates
Live mode uses polling pattern:
- 60-second intervals
- Non-blocking updates
- Connection status indicator

### Cross-References
- **ADR-052**: Analytics Precomputation Strategy
- **ADR-053**: Live Trading Real-time Update Pattern
- **ADR-054**: Authentication Architecture
- **ADR-055**: Grafana Integration for Live Mode
- **ADR-056**: Deposit/Withdraw Triggering Rebalance
- **ADR-057**: Stop vs Emergency Stop Distinction
- **ADR-058**: Download Formats Priority
- **ADR-059**: Chart Rendering Strategy

See [docs/specs/12_FRONTEND_SPEC.md](specs/12_FRONTEND_SPEC.md) for complete implementation details.