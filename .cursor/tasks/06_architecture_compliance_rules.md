# ARCHITECTURE COMPLIANCE RULES FOR BACKGROUND AGENTS

## CRITICAL RULE: NO HARDCODED VALUES
**NEVER use hardcoded values to fix issues. Always use proper data flow and component integration.**

## PROPER DATA FLOW ARCHITECTURE
1. **Data Provider** loads all data at startup from data/ directory
2. **Execution Interfaces** query data provider for current timestamp data
3. **Tight Loop Reconciliation** verifies execution matches position updates
4. **Position Monitor** receives data from execution interfaces
5. **Component Chain** passes data through proper sequence

## FORBIDDEN PRACTICES
- ❌ Hardcoding any values (liquidity index, rates, prices, configuration values, etc.)
- ❌ Bypassing the data provider or configuration loading architecture
- ❌ Using static values instead of dynamic data
- ❌ Fixing issues with "magic numbers"
- ❌ Ignoring the component chain architecture
- ❌ Initializing multiple instances of the same component
- ❌ Creating separate config or data instances
- ❌ Having unsynchronized data flows between components
- ❌ Making components mode-specific when they should be mode-agnostic
- ❌ Duplicating utility methods across components
- ❌ Putting utility methods in execution interfaces instead of centralized location
- ❌ Having different P&L calculation logic per mode
- ❌ Clearing/resetting component state to mask architectural problems
- ❌ Using "clean state" hacks instead of fixing root causes
- ❌ Having components that need to be "cleared" between runs

## REQUIRED PRACTICES
- ✅ Use data provider for all external data and configuration loading for all components
- ✅ Query data provider for current timestamp
- ✅ Implement tight loop reconciliation after each execution instruction
- ✅ Verify position updates match execution expectations
- ✅ Pass data through proper component chain
- ✅ Maintain architecture integrity
- ✅ Use dynamic data, not static values
- ✅ Use configuration loading architecture for all components
- ✅ Create configuration entries in appropriate YAML files if config is missing
- ✅ Add to Pydantic models in config_models.py to ensure validation passes
- ✅ Load all configuration from YAML files (not hardcoded in code)
- ✅ Use environment variables only when specified in .env files
- ✅ Validate all configuration through Pydantic models
- ✅ Follow the YAML-based config structure (modes/venues/scenarios)
- ✅ Use SINGLE instance of each component across the entire run
- ✅ Share the SAME config instance across all components
- ✅ Share the SAME data provider instance across all components
- ✅ Ensure synchronized data flows between all components
- ✅ Make P&L monitor mode-agnostic for both backtest and live modes
- ✅ Centralize utility methods for liquidity index, market prices, and conversions
- ✅ Use shared utility methods across all components that need them
- ✅ Access global data states using current event loop timestamp
- ✅ Design components to be naturally clean without needing state clearing
- ✅ Fix root causes instead of using "clean state" hacks
- ✅ Ensure components are properly initialized with correct state from the start

## DATA SOURCES
- **Market Data**: data/market/ directory
- **Protocol Data**: data/protocol_data/ directory (AAVE, Lido, etc.)
- **Historical Data**: data/ directory with timestamp-based files
- **Configuration**: configs/ directory with YAML files
- **Environment Variables**: .env files (only when specified)

## CONFIGURATION ARCHITECTURE
- **YAML Files**: All configuration must be in configs/ directory
- **Pydantic Models**: All config must be validated through config_models.py
- **Structure**: Follow modes/venues/scenarios YAML structure
- **Loading**: Use configuration loading architecture for all components
- **Validation**: All config must pass Pydantic validation
- **Environment**: Use .env files only when specified in documentation

## COMPONENT INTEGRATION REQUIREMENTS
1. **Data Provider**: Must load all data at startup
2. **Execution Interfaces**: Must query data provider for current data
3. **Position Monitor**: Must receive data from execution interfaces
4. **Strategy Manager**: Must coordinate data flow through components

## SINGLETON PATTERN REQUIREMENTS
1. **Single Instance**: Each component must be a SINGLE instance across the entire run
2. **Shared Config**: All components must share the SAME config instance
3. **Shared Data Provider**: All components must share the SAME data provider instance
4. **Synchronized Data**: All components must have synchronized data flows
5. **No Duplication**: Never initialize the same component twice in different places

## MODE-AGNOSTIC COMPONENT REQUIREMENTS
1. **P&L Monitor**: Must be mode-agnostic and work for both backtest and live modes
2. **Centralized Utilities**: Common utility methods must be centralized and shared
3. **No Mode-Specific Logic**: Components should not have different logic per mode
4. **Shared Data Access**: All components must access the same global data states
5. **Timestamp-Based**: All operations must use the current event loop timestamp

## ERROR HANDLING
If data is not available:
1. Check data provider initialization
2. Verify data files exist in data/ directory
3. Ensure proper component chain integration
4. Fix the root cause, don't hardcode values

## VALIDATION CHECKLIST
Before committing any fix:
- [ ] No hardcoded values used (including config values)
- [ ] Data comes from data provider
- [ ] Configuration loaded from YAML files
- [ ] Pydantic validation passes for all config
- [ ] Component chain is maintained
- [ ] Architecture integrity preserved
- [ ] Dynamic data used, not static values
- [ ] Root cause addressed, not symptoms
- [ ] Configuration entries added to appropriate YAML files
- [ ] Pydantic models updated if new config fields added
- [ ] Single instance of each component used across entire run
- [ ] Same config instance shared across all components
- [ ] Same data provider instance shared across all components
- [ ] No duplicate component initialization
- [ ] Synchronized data flows between all components

## EXAMPLES OF WRONG APPROACHES
```python
# ❌ WRONG: Hardcoded value
liquidity_index = 1.070100

# ❌ WRONG: Static value
amount_out = amount * 1.07

# ❌ WRONG: Magic number
gas_cost = 0.001

# ❌ WRONG: Hardcoded configuration
api_key = "sk-1234567890abcdef"

# ❌ WRONG: Hardcoded file path
data_file = "/path/to/data.csv"

# ❌ WRONG: Hardcoded timeout
timeout = 30

# ❌ WRONG: Multiple instances of same component
position_monitor_1 = PositionMonitor(config)
position_monitor_2 = PositionMonitor(config)  # Different instance!

# ❌ WRONG: Separate config instances
config_1 = load_config()
config_2 = load_config()  # Different instance!

# ❌ WRONG: Separate data provider instances
data_provider_1 = DataProvider(config)
data_provider_2 = DataProvider(config)  # Different instance!

# ❌ WRONG: Clearing state to mask architectural problems
class PositionMonitor:
    def initialize(self):
        # Clear all balances before initializing capital to ensure clean state
        for token in self._token_monitor.wallet:
            self._token_monitor.wallet[token] = 0.0
        logger.info(f"Position Monitor: Cleared all wallet balances for fresh start")

# ❌ WRONG: Using "clean state" hacks instead of fixing root causes
class Component:
    def reset_state(self):
        # This masks the real problem - why does state need to be reset?
        self.state = {}
        self.initialized = False
```

## EXAMPLES OF CORRECT APPROACHES
```python
# ✅ CORRECT: Query data provider
liquidity_index = await self.data_provider.get_liquidity_index('USDT', timestamp)

# ✅ CORRECT: Use market data
gas_cost = market_data.get('gas_price_gwei', 20.0) * gas_used

# ✅ CORRECT: Dynamic calculation
amount_out = amount / liquidity_index

# ✅ CORRECT: Load from configuration
api_key = self.config.get('api_key')

# ✅ CORRECT: Use configuration loading
data_file = self.config.get('data_file_path')

# ✅ CORRECT: Load from YAML config
timeout = self.config.get('timeout_seconds', 30)

# ✅ CORRECT: Single instance pattern
class ComponentManager:
    def __init__(self):
        self.config = load_config()  # Single config instance
        self.data_provider = DataProvider(self.config)  # Single data provider
        self.position_monitor = PositionMonitor(self.config, self.data_provider)
        self.exposure_monitor = ExposureMonitor(self.config, self.data_provider)
        # All components share the same config and data provider instances

# ✅ CORRECT: Dependency injection
class MyComponent:
    def __init__(self, config, data_provider):
        self.config = config  # Shared config instance
        self.data_provider = data_provider  # Shared data provider instance

# ✅ CORRECT: Naturally clean component design
class PositionMonitor:
    def __init__(self, config, data_provider):
        self.config = config
        self.data_provider = data_provider
        # Initialize with correct state from the start
        self.wallet_balances = self._initialize_wallet_balances()
        self.initialized = True
    
    def _initialize_wallet_balances(self):
        # Initialize with proper state, don't clear later
        return {token: 0.0 for token in self.config.get('supported_tokens', [])}

# ✅ CORRECT: Proper component lifecycle
class Component:
    def __init__(self, config, data_provider):
        self.config = config
        self.data_provider = data_provider
        # Initialize with correct state from the start
        self.state = self._initialize_state()
        self.initialized = True
    
    def _initialize_state(self):
        # Initialize with proper state, don't reset later
        return self.config.get('initial_state', {})
```

## ENFORCEMENT
- All fixes must maintain architecture integrity
- No shortcuts or hardcoded values allowed
- Data must flow through proper component chain
- Root causes must be addressed, not symptoms
