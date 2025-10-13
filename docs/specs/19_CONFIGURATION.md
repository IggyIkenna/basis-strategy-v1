# Configuration Workflow Guide 🔧

**Purpose**: Guide for managing configuration updates, validation, and system restarts  
**Updated**: October 5, 2025 - Configuration fixed and working  
**Last Reviewed**: October 9, 2025  
**Status**: ✅ Aligned with canonical architectural principles

---

## 📚 **Canonical Sources**

**This configuration guide aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Configuration Architecture**: [docs/REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - YAML-based config requirements
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

## Current Implementation Status

**Status**: ✅ **PARTIALLY IMPLEMENTED** (MEDIUM Priority)
**Last Updated**: October 12, 2025
**Implementation File**: `backend/src/basis_strategy_v1/infrastructure/config/config_manager.py`

### Implementation Status
- **Core Methods**: 0/0 methods implemented (all utility methods, no core API)
- **Config Parameters**: 0/0 implemented (config loading, validation, slicing)
- **Architecture Compliance**: 0.40 (good foundation with gaps)

### Implementation Details
- **Config Loading**: ✅ YAML file loading implemented
- **Environment Variables**: ✅ Environment variable loading with fail-fast
- **Config Validation**: ✅ Basic validation implemented
- **Strategy Discovery**: ✅ Strategy file discovery implemented
- **Config Slicing**: ✅ Mode-specific config slicing implemented
- **Error Handling**: ✅ Comprehensive error codes (CONFIG-MGR-001 through CONFIG-MGR-008)

### Remaining Gaps
- **Config Hot-Reloading**: Hot-reloading not implemented
- **Config Caching**: Advanced caching not implemented
- **Data Provider Validation**: Data provider config validation not implemented
- **Component Factory Integration**: Component factory integration not implemented
- **Environment Variable Naming**: Inconsistencies in environment variable naming

### Task Recommendations
- Implement config hot-reloading functionality
- Add advanced config caching and performance optimization
- Implement data provider configuration validation
- Fix environment variable naming inconsistencies
- Add comprehensive unit tests
- Integrate with component factory for config-driven component creation

---

## Purpose
Manage configuration loading, validation, and system restarts for the Basis Strategy platform using a **config-driven architecture** that enables mode-agnostic components while supporting mode-specific data requirements and behavior.

## Responsibilities
1. Load and validate configuration from YAML files with config-driven architecture support
2. Manage environment variables and system settings
3. Provide configuration slicing for strategy modes with data_requirements and component_config
4. Handle configuration updates and system restarts
5. Validate configuration consistency and integrity including data provider validation
6. Support configuration hot-reloading and validation
7. Enable factory-based component creation with config validation
8. Support mode-agnostic component behavior through configuration parameters

## State
- global_config: Dict (immutable, validated at startup with config-driven architecture)
- config_cache: Dict (cached configuration slices with data_requirements and component_config)
- validation_results: Dict (configuration validation results including data provider validation)
- last_validation_timestamp: pd.Timestamp
- data_provider_factory: DataProviderFactory (for creating mode-specific data providers)
- component_factory: ComponentFactory (for creating config-driven components)

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- config_paths: Dict (reference, never modified)
- execution_mode: str (BASIS_EXECUTION_MODE)

These references are stored in __init__ and used throughout component lifecycle.
Components NEVER receive these as method parameters during runtime.

## Environment Variables

### System-Level Variables
- **BASIS_EXECUTION_MODE**: 'backtest' | 'live' (determines configuration behavior)
- **BASIS_LOG_LEVEL**: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' (logging level)
- **BASIS_DATA_DIR**: Path to data directory (for backtest mode)

### Component-Specific Variables
- **CONFIG_VALIDATION_STRICT**: Strict configuration validation mode (default: true)
- **CONFIG_CACHE_SIZE**: Configuration cache size (default: 1000)
- **CONFIG_RELOAD_INTERVAL**: Configuration reload interval in seconds (default: 300)

## Environment-Specific Credential Integration

### Credential Routing Patterns

The configuration system integrates with environment-specific credential routing to ensure proper credential selection based on `BASIS_ENVIRONMENT`. This integration enables execution components to access the correct credentials for their environment without hardcoded credential management.

**Environment Detection and Credential Routing**:
```python
def validate_environment_credentials() -> bool:
    """Validate that all required environment-specific credentials are set."""
    environment = os.getenv('BASIS_ENVIRONMENT', 'dev')
    credential_prefix = f"BASIS_{environment.upper()}__"
    
    # Get required venues from configuration
    required_venues = _get_required_venues_from_config()
    
    # Validate each venue's credentials
    for venue in required_venues:
        _validate_venue_credentials(venue, credential_prefix)
    
    return True

def _get_required_venues_from_config() -> List[str]:
    """Extract required venues from configuration (private method)."""
    venues = []
    
    # Get venues from strategy mode configuration
    for mode_file in glob.glob('configs/modes/*.yaml'):
        with open(mode_file, 'r') as f:
            config = yaml.safe_load(f)
            if 'venues' in config:
                venues.extend(config['venues'].keys())
    
    return list(set(venues))

def _validate_venue_credentials(venue: str, credential_prefix: str) -> None:
    """Validate credentials for a specific venue (private method)."""
    if venue == 'binance':
        required_creds = [
            f'{credential_prefix}CEX__BINANCE_SPOT_API_KEY',
            f'{credential_prefix}CEX__BINANCE_SPOT_SECRET',
            f'{credential_prefix}CEX__BINANCE_FUTURES_API_KEY',
            f'{credential_prefix}CEX__BINANCE_FUTURES_SECRET'
        ]
    elif venue == 'bybit':
        required_creds = [
            f'{credential_prefix}CEX__BYBIT_API_KEY',
            f'{credential_prefix}CEX__BYBIT_SECRET'
        ]
    elif venue == 'okx':
        required_creds = [
            f'{credential_prefix}CEX__OKX_API_KEY',
            f'{credential_prefix}CEX__OKX_SECRET',
            f'{credential_prefix}CEX__OKX_PASSPHRASE'
        ]
    elif venue == 'alchemy':
        required_creds = [
            f'{credential_prefix}ALCHEMY__PRIVATE_KEY',
            f'{credential_prefix}ALCHEMY__RPC_URL',
            f'{credential_prefix}ALCHEMY__WALLET_ADDRESS',
            f'{credential_prefix}ALCHEMY__NETWORK',
            f'{credential_prefix}ALCHEMY__CHAIN_ID'
        ]
    else:
        raise ValueError(f"Unknown venue: {venue}")
    
    # Validate each required credential
    for cred_var in required_creds:
        value = os.getenv(cred_var)
        if not value or value.startswith('your_') or value == '0x...':
            raise ValueError(f"Missing or invalid credential: {cred_var}")
```

### Integration with Execution Components

The configuration system provides credential routing integration for all execution components:

**Execution Interface Factory Integration**:
- Factory methods use `_get_venue_credentials()` to inject environment-specific credentials
- Credential validation occurs before interface creation
- Environment-specific credential routing based on `BASIS_ENVIRONMENT`

**Execution Interface Manager Integration**:
- Manager coordinates credential routing to execution interfaces
- All venue credentials are validated before interface initialization
- Credential management is centralized through the manager

**Execution Manager Integration**:
- Manager coordinates credential validation across all execution components
- Credential routing is coordinated through the Execution Interface Manager
- All venue credentials are validated before execution component initialization

### Credential Structure Documentation

**Environment-Specific Credential Prefixes**:
- **Development**: `BASIS_DEV__*` (testnet APIs, Sepolia network)
- **Staging**: `BASIS_STAGING__*` (mainnet APIs, staging wallet)
- **Production**: `BASIS_PROD__*` (mainnet APIs, production wallet)

**Venue-Specific Credential Mapping**:

**CEX Venues**:
- **Binance**: `BASIS_{ENV}__CEX__BINANCE_SPOT_API_KEY`, `BASIS_{ENV}__CEX__BINANCE_SPOT_SECRET`, `BASIS_{ENV}__CEX__BINANCE_FUTURES_API_KEY`, `BASIS_{ENV}__CEX__BINANCE_FUTURES_SECRET`
- **Bybit**: `BASIS_{ENV}__CEX__BYBIT_API_KEY`, `BASIS_{ENV}__CEX__BYBIT_SECRET`
- **OKX**: `BASIS_{ENV}__CEX__OKX_API_KEY`, `BASIS_{ENV}__CEX__OKX_SECRET`, `BASIS_{ENV}__CEX__OKX_PASSPHRASE`

**OnChain Venues**:
- **Alchemy**: `BASIS_{ENV}__ALCHEMY__PRIVATE_KEY`, `BASIS_{ENV}__ALCHEMY__RPC_URL`, `BASIS_{ENV}__ALCHEMY__WALLET_ADDRESS`, `BASIS_{ENV}__ALCHEMY__NETWORK`, `BASIS_{ENV}__ALCHEMY__CHAIN_ID`

### Configuration Examples

**Environment-Specific Credential Usage**:
```yaml
# configs/modes/btc_basis.yaml
mode: "btc_basis"
share_class: "USDT"
asset: "BTC"

# This mode requires CEX venues for basis trading
venues:
  - "binance"
  - "bybit"
  - "okx"

# Credentials are loaded via environment-specific routing
# No hardcoded credentials in configuration files
```

**Credential Validation Examples**:
```python
# Configuration validation includes credential validation
def validate_configuration(config: Dict) -> bool:
    """Validate configuration including credentials."""
    # Validate configuration structure
    validate_config_structure(config)
    
    # Validate environment-specific credentials
    validate_environment_credentials()
    
    return True
```

### Error Handling Patterns

**Credential Validation Errors**:
- **Missing Credentials**: Environment-specific credentials not set
- **Invalid Credentials**: Placeholder values or empty strings
- **Unknown Venue**: Venue not supported by credential routing

**Error Handling Pattern**:
```python
try:
    validate_environment_credentials()
except ValueError as e:
    logging.error(f"Credential validation failed: {e}")
    raise ConfigurationError(f"Configuration validation failed: {e}")
```

**Reference**: [VENUE_ARCHITECTURE.md](../VENUE_ARCHITECTURE.md) - Environment Variables section
**Reference**: [ENVIRONMENT_VARIABLES.md](../ENVIRONMENT_VARIABLES.md) - Environment-Specific Credential Routing section
**Reference**: [07B_EXECUTION_INTERFACES.md](07B_EXECUTION_INTERFACES.md) - Environment-Specific Credential Usage section
**Reference**: [07C_EXECUTION_INTERFACE_FACTORY.md](07C_EXECUTION_INTERFACE_FACTORY.md) - Environment-Specific Credential Routing section
**Reference**: [07_EXECUTION_INTERFACE_MANAGER.md](07_EXECUTION_INTERFACE_MANAGER.md) - Venue Credential Management section
**Reference**: [06_EXECUTION_MANAGER.md](06_EXECUTION_MANAGER.md) - Credential Management for Venue Initialization section

## Config Fields Used

### Universal Config (All Components)
- **mode**: str - Strategy mode name (e.g., 'pure_lending', 'btc_basis')
- **share_class**: str - Share class currency ('USDT' | 'ETH')
- **asset**: str - Primary asset name
- **execution_mode**: 'backtest' | 'live' (from strategy mode slice)
- **log_level**: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' (from strategy mode slice)
- **initial_capital**: float - Starting capital amount for the strategy

### Config-Driven Architecture Fields
- **data_requirements**: List[str] - Data types required by this mode
  - **Usage**: Validates that DataProvider can satisfy all requirements
  - **Examples**: ["aave_usdt_rates", "btc_spot_prices", "eth_usd_prices"]
- **component_config**: Dict - Component behavior configuration
  - **risk_monitor**: Risk calculation configuration
  - **exposure_monitor**: Asset tracking configuration
  - **pnl_calculator**: PnL attribution configuration
  - **strategy_manager**: Strategy behavior configuration
  - **execution_manager**: Execution action configuration
  - **results_store**: Results storage configuration

### ML-Specific Configuration Fields
- **ml_config**: Dict - Machine learning model configuration
  - **model_registry**: str - ML model registry (e.g., 'mlflow')
  - **model_name**: str - Model name (e.g., 'btc_5min_strategy', 'usdt_5min_strategy')
  - **model_version**: str - Model version (e.g., 'production')
  - **candle_interval**: str - Candle interval for ML predictions (e.g., '5min')
  - **signal_threshold**: float - Confidence threshold for trading signals (0.0-1.0)
  - **max_position_size**: float - Maximum position size as fraction of equity (0.0-1.0)
  - **Usage**: Used in ML directional strategies for model inference and signal generation
  - **Required**: Yes for ML strategies (ml_btc_directional, ml_usdt_directional)
  - **Used in**: `ml_directional_data_provider.py`, ML strategy components

### Strategy-Specific Configuration Fields
- **delta_tolerance**: float - Delta neutrality tolerance (0.0-1.0)
  - **Usage**: Maximum allowed gross exposure deviation for delta neutrality
  - **Default**: 0.005 (0.5%) for basis trading, 1.0 (100%) for directional strategies
  - **Used in**: Risk monitoring and position management
- **stake_allocation_eth**: float - ETH stake allocation percentage (0.0-1.0)
  - **Usage**: Percentage of capital allocated to ETH staking vs margin trading
  - **Used in**: Market neutral strategies for capital allocation
- **funding_threshold**: float - Funding rate threshold for basis trading
  - **Usage**: Minimum funding rate differential to trigger basis trades
  - **Used in**: Basis trading strategies for trade signal generation
- **max_ltv**: float - Maximum loan-to-value ratio (0.0-1.0)
  - **Usage**: Maximum LTV for borrowing positions
  - **Used in**: Risk monitoring and position sizing
- **leverage_enabled**: bool - Whether leverage is enabled for this mode
  - **Usage**: Controls leverage availability in strategy execution
  - **Used in**: Strategy execution and risk management
- **hedge_venues**: List[str] - List of venues used for hedging
  - **Usage**: Defines which venues are used for hedging positions
  - **Examples**: ["binance", "bybit", "okx"]
  - **Used in**: Hedging execution and venue selection
- **hedge_allocation_bybit**: float - Allocation percentage to Bybit for hedging
  - **Usage**: Defines percentage of hedge allocation to Bybit
  - **Used in**: Hedge allocation and execution planning
- **position_deviation_threshold**: float - Position deviation threshold (0.0-1.0)
  - **Usage**: Threshold for triggering position rebalancing
  - **Used in**: Position monitoring and rebalancing logic
- **rewards_mode**: str - Rewards collection mode
  - **Usage**: Defines how rewards are collected and distributed
  - **Examples**: "base_only", "eigen_rewards", "staking_rewards"
  - **Used in**: Rewards calculation and distribution

### Share Class Configuration Fields
- **share_class**: str - Share class name ('USDT' | 'ETH')
- **type**: str - Share class type ('stable' | 'directional')
- **base_currency**: str - Base currency ('USDT' | 'ETH')
- **description**: str - Share class description
- **decimal_places**: int - Decimal places for precision (0-18)
- **risk_level**: str - Risk level ('low', 'medium', 'high')
- **market_neutral**: bool - Whether market neutral strategies are supported
- **allows_hedging**: bool - Whether hedging is allowed
- **supported_strategies**: List[str] - List of supported strategy modes
- **leverage_supported**: bool - Whether leverage is supported
- **staking_supported**: bool - Whether staking is supported
- **basis_trading_supported**: bool - Whether basis trading is supported
- **max_leverage**: Optional[float] - Maximum leverage allowed (1.0+)
- **target_apy_range**: Optional[Dict[str, float]] - Target APY range (min/max)
- **max_drawdown**: Optional[float] - Maximum drawdown limit (0.0-1.0)
  - **Usage**: Used in share class configuration for risk management and strategy selection
  - **Required**: Core fields required, optional fields for advanced configuration
  - **Used in**: Share class validation, strategy selection, risk management

### Venue Configuration Fields
- **venues**: Dict[str, Dict] - Venue configuration mapping
  - **Usage**: Defines trading venues and their specific configuration
  - **Required**: Yes for all modes that use venues
  - **Used in**: Venue interface creation, execution management, credential routing
- **venues.{venue_name}.venue_type**: str - Venue type ('cex', 'defi', 'infrastructure')
  - **Usage**: Determines venue interface type and behavior
  - **Examples**: 'cex' for centralized exchanges, 'defi' for DeFi protocols, 'infrastructure' for blockchain infrastructure
  - **Used in**: Venue interface factory, execution routing
- **venues.{venue_name}.enabled**: bool - Whether venue is enabled for this mode
  - **Usage**: Controls venue availability in strategy execution
  - **Default**: true
  - **Used in**: Venue filtering, execution planning
- **venues.{venue_name}.instruments**: List[str] - Trading instruments available on venue
  - **Usage**: Defines what can be traded on this venue
  - **Examples**: ["BTC-SPOT", "BTC-PERP"], ["ETH-STAKE", "WEETH-UNSTAKE"], ["WALLET-TRANSFER"]
  - **Used in**: Instrument validation, execution routing
- **venues.{venue_name}.order_types**: List[str] - Supported order types on venue
  - **Usage**: Defines available order execution methods
  - **Examples**: ["market", "limit"], ["stake", "unstake"], ["borrow", "repay", "supply", "withdraw"]
  - **Used in**: Order execution, venue interface configuration

### Specific Venue Configuration Fields
- **venues.aave_v3**: Dict - AAVE V3 DeFi protocol configuration
- **venues.aave_v3.venue_type**: str - Venue type ('defi')
- **venues.aave_v3.enabled**: bool - Whether AAVE V3 is enabled
- **venues.aave_v3.instruments**: List[str] - Available instruments (e.g., ["USDT-LENDING", "USDT-BORROWING"])
- **venues.aave_v3.order_types**: List[str] - Supported order types (e.g., ["supply", "withdraw", "borrow", "repay"])

- **venues.alchemy**: Dict - Alchemy blockchain infrastructure configuration
- **venues.alchemy.venue_type**: str - Venue type ('infrastructure')
- **venues.alchemy.enabled**: bool - Whether Alchemy is enabled
- **venues.alchemy.instruments**: List[str] - Available instruments (e.g., ["WALLET-TRANSFER"])
- **venues.alchemy.order_types**: List[str] - Supported order types (e.g., ["transfer"])

- **venues.binance**: Dict - Binance CEX configuration
- **venues.binance.venue_type**: str - Venue type ('cex')
- **venues.binance.enabled**: bool - Whether Binance is enabled
- **venues.binance.instruments**: List[str] - Available instruments (e.g., ["BTC-SPOT", "BTC-PERP"])
- **venues.binance.order_types**: List[str] - Supported order types (e.g., ["market", "limit"])

- **venues.bybit**: Dict - Bybit CEX configuration
- **venues.bybit.venue_type**: str - Venue type ('cex')
- **venues.bybit.enabled**: bool - Whether Bybit is enabled
- **venues.bybit.instruments**: List[str] - Available instruments (e.g., ["BTC-PERP"])
- **venues.bybit.order_types**: List[str] - Supported order types (e.g., ["market", "limit"])

- **venues.etherfi**: Dict - EtherFi staking protocol configuration
- **venues.etherfi.venue_type**: str - Venue type ('defi')
- **venues.etherfi.enabled**: bool - Whether EtherFi is enabled
- **venues.etherfi.instruments**: List[str] - Available instruments (e.g., ["ETH-STAKE", "WEETH-UNSTAKE"])
- **venues.etherfi.order_types**: List[str] - Supported order types (e.g., ["stake", "unstake"])

- **venues.okx**: Dict - OKX CEX configuration
- **venues.okx.venue_type**: str - Venue type ('cex')
- **venues.okx.enabled**: bool - Whether OKX is enabled
- **venues.okx.instruments**: List[str] - Available instruments (e.g., ["BTC-PERP"])
- **venues.okx.order_types**: List[str] - Supported order types (e.g., ["market", "limit"])
- **venues.{venue_name}.min_amount**: Optional[float] - Minimum trade amount for venue
  - **Usage**: Enforces minimum trade size limits
  - **Used in**: Trade size validation, execution filtering
- **venues.{venue_name}.max_leverage**: Optional[float] - Maximum leverage available on venue
  - **Usage**: Defines leverage limits for venue
  - **Used in**: Risk management, position sizing
  - **Usage**: Used in venue configuration for execution routing and risk management
  - **Required**: Core venue fields required, optional fields for advanced configuration
  - **Used in**: Venue interface creation, execution management, risk monitoring

### Component Config Fields Used in Code
- `exposure_monitor`: Dict - Exposure monitor configuration
  - **Usage**: Used in `exposure_monitor.py:41` to extract component-specific settings
  - **Required**: Yes
  - **Used in**: `exposure_monitor.py:41`

- `risk_monitor`: Dict - Risk monitor configuration
  - **Usage**: Used in `risk_monitor.py:61` to extract risk monitor specific settings
  - **Required**: Yes
  - **Used in**: `risk_monitor.py:61`

- `pnl_calculator`: Dict - PnL calculator configuration
  - **Usage**: Used in `pnl_calculator.py:178` to extract PnL calculator specific settings
  - **Required**: Yes
  - **Used in**: `pnl_calculator.py:178`

### Event Logger Configuration Fields
- **event_logger**: Dict - Event logging configuration
  - **Usage**: Configures event logging behavior and output format
  - **Required**: Yes for all modes
  - **Used in**: Event logging, audit trails, debugging
- **event_logger.log_path**: str - Path to log files
  - **Usage**: Directory where log files are stored
  - **Default**: "./logs"
  - **Used in**: Log file management
- **event_logger.log_format**: str - Log format ('json', 'text')
  - **Usage**: Format for log output
  - **Default**: "json"
  - **Used in**: Log parsing and analysis
- **event_logger.log_level**: str - Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
  - **Usage**: Minimum log level to record
  - **Default**: "INFO"
  - **Used in**: Log filtering
- **event_logger.event_categories**: Dict[str, List[str]] - Event categories and types
  - **Usage**: Defines event categorization for filtering and analysis
  - **Examples**: {"data": ["data_loaded", "data_updated"], "risk": ["risk_breach", "risk_warning"]}
  - **Used in**: Event filtering, categorization
- **event_logger.event_logging_settings**: Dict - Event logging behavior settings
  - **Usage**: Controls event logging behavior
  - **Used in**: Event processing, buffering
- **event_logger.log_retention_policy**: Dict - Log retention and rotation settings
  - **Usage**: Manages log file lifecycle
  - **Used in**: Log file management, cleanup
- **event_logger.audit_requirements**: Dict - Audit trail requirements
  - **Usage**: Configures audit trail behavior
  - **Used in**: Compliance, auditing
- **event_logger.compliance_settings**: Dict - Compliance-related settings
  - **Usage**: Configures compliance behavior
  - **Used in**: Regulatory compliance
- **event_logger.logging_requirements**: Dict - Logging feature requirements
  - **Usage**: Enables/disables specific logging features
  - **Used in**: Feature toggling
- **event_logger.event_filtering**: Dict - Event filtering configuration
  - **Usage**: Configures event filtering behavior
  - **Used in**: Event processing

### Component Configuration Fields
- **component_config.strategy_manager.position_calculation.target_position**: str - Target position type
  - **Usage**: Defines the primary position type for strategy execution
  - **Examples**: "btc_spot_long", "eth_stake_long"
  - **Used in**: Strategy position calculation and execution
- **component_config.strategy_manager.position_calculation.hedge_position**: str - Hedge position type
  - **Usage**: Defines the hedge position type for risk management
  - **Examples**: "btc_perp_short", "eth_perp_short"
  - **Used in**: Risk management and hedging execution
- **component_config.strategy_manager.position_calculation.method**: str - Position calculation method
  - **Usage**: Defines how positions are calculated
  - **Examples**: "delta_neutral", "directional"
  - **Used in**: Position sizing and risk calculation
- **component_config.strategy_manager.position_calculation.leverage_ratio**: float - Leverage ratio for positions
  - **Usage**: Defines leverage multiplier for position sizing
  - **Used in**: Position sizing and risk management
- **component_config.execution_manager.action_mapping.entry_full**: List[str] - Actions for full entry
  - **Usage**: Defines sequence of actions for full position entry
  - **Examples**: ["cex_spot_buy", "cex_perp_short"]
  - **Used in**: Execution planning and order sequencing
- **component_config.execution_manager.action_mapping.exit_full**: List[str] - Actions for full exit
  - **Usage**: Defines sequence of actions for full position exit
  - **Examples**: ["cex_perp_close", "cex_spot_sell"]
  - **Used in**: Execution planning and order sequencing
- **component_config.risk_monitor.risk_limits.liquidation_threshold**: float - Liquidation threshold
  - **Usage**: Defines liquidation threshold for risk monitoring
  - **Used in**: Risk monitoring and position management
- **component_config.risk_monitor.risk_limits.target_margin_ratio**: float - Target margin ratio
  - **Usage**: Defines target margin ratio for CEX positions
  - **Used in**: Risk monitoring and position management
- **component_config.risk_monitor.risk_limits.delta_tolerance**: float - Delta tolerance threshold
  - **Usage**: Defines maximum allowed delta deviation
  - **Used in**: Risk monitoring and delta neutrality
- **component_config.risk_monitor.risk_limits.maintenance_margin_requirement**: float - Maintenance margin requirement
  - **Usage**: Defines minimum margin requirement for positions
  - **Used in**: Risk monitoring and margin management
- **component_config.exposure_monitor.conversion_methods**: Dict[str, str] - Asset conversion methods
  - **Usage**: Defines how assets are converted to USD for exposure calculation
  - **Examples**: {"BTC": "usd_price", "BTC_PERP": "perp_mark_price"}
  - **Used in**: Exposure monitoring and risk calculation
- **component_config.pnl_calculator.attribution_types**: List[str] - PnL attribution types
  - **Usage**: Defines types of PnL attribution to track
  - **Examples**: ["funding_pnl", "delta_pnl", "basis_pnl", "transaction_costs"]
  - **Used in**: PnL calculation and reporting
- **component_config.strategy_manager.strategy_type**: str - Strategy type identifier
  - **Usage**: Defines the specific strategy type being executed
  - **Examples**: "btc_basis", "eth_leveraged", "pure_lending"
  - **Used in**: Strategy routing and behavior selection
- **component_config.strategy_manager.actions**: List[str] - Available strategy actions
  - **Usage**: Defines actions available to the strategy
  - **Examples**: ["entry_full", "entry_partial", "exit_partial", "exit_full"]
  - **Used in**: Strategy execution and action planning
- **component_config.strategy_manager.rebalancing_triggers**: List[str] - Rebalancing trigger conditions
  - **Usage**: Defines conditions that trigger position rebalancing
  - **Examples**: ["deposit", "withdrawal", "delta_drift"]
  - **Used in**: Strategy rebalancing logic
- **component_config.strategy_factory.timeout**: int - Strategy factory timeout
  - **Usage**: Defines timeout for strategy factory operations
  - **Used in**: Strategy initialization and error handling
- **component_config.results_store.balance_sheet_assets**: List[str] - Assets tracked in balance sheet
  - **Usage**: Defines which assets are tracked in balance sheet
  - **Examples**: ["BTC", "USDT", "ETH", "BTC_PERP"]
  - **Used in**: Results storage and balance sheet generation

- `data_dir`: str - Directory path for data storage
  - **Usage**: Used in `data_provider_factory.py:62` and `risk_monitor.py:86` for data file paths
  - **Required**: Yes
  - **Used in**: `data_provider_factory.py:62`, `risk_monitor.py:86`

### Component-Specific Config
  - **validation_strict**: Strict validation mode
  - **environment**: System environment

## Config-Driven Architecture

The configuration system now supports a **config-driven architecture** that enables mode-agnostic components while supporting mode-specific data requirements and behavior. This architecture eliminates mode-specific logic from components and uses configuration to drive behavior.

### Core Principles

#### 1. Mode-Agnostic Components
Components should be **mode-agnostic** - they work identically across all strategy modes without hardcoded mode-specific logic.

#### 2. Config-Driven Behavior
Component behavior is determined by **configuration parameters** rather than mode-specific if/else statements.

#### 3. Data Provider Abstraction
A **DataProvider abstraction layer** provides standardized data access while allowing mode-specific data loading.

#### 4. Graceful Data Handling
Components gracefully handle missing data by returning zeros or skipping calculations rather than failing.

### Configuration Structure

Each strategy mode configuration includes:

```yaml
mode: "mode_name"
share_class: "USDT"  # or "ETH"
asset: "ASSET_NAME"

# Data requirements (what this mode needs)
data_requirements:
  - "data_type_1"
  - "data_type_2"

# Component behavior configs
component_config:
  risk_monitor:
    enabled_risk_types: ["aave_health_factor", "cex_margin_ratio"]
    risk_limits:
      aave_health_factor_min: 1.1
      cex_margin_ratio_min: 0.2
```

### Field Documentation Standards

**Purpose**: Standards for documenting configuration fields to ensure 100% quality gate alignment

#### Required Fields
All required fields (non-Optional in Pydantic models) MUST be documented with:
- **Field name**: Bold field name with type
- **Description**: Clear description of purpose and usage
- **Example**: Concrete example value when helpful

#### Nested Object Fields  
Document all required levels: `component_config.strategy_manager.position_calculation`

**Example**:
```markdown
**component_config.strategy_manager.position_calculation**: Dict[str, Any]
- Position calculation configuration for strategy manager
- Contains target_position, hedge_position, and hedge_allocation settings
```

#### Fixed Schema Dictionary Fields
Document all nested fields for fixed schema dicts (api_contract, auth, ml_config, component_config):

**Example**:
```markdown
**ml_config.model_registry**: str
- ML model registry type (e.g., "mlflow", "s3")

**ml_config.model_name**: str  
- Model name for inference (e.g., "btc_5min_strategy")

**ml_config.candle_interval**: str
- Candle interval for model predictions (e.g., "5min")
```

#### Dynamic Dictionary Fields
Document parent field once with structure example for truly dynamic dicts:

**Example**:
```markdown
**component_config.strategy_manager.position_calculation.hedge_allocation**: Dict[str, float]
- Dynamic dictionary mapping venue names to allocation percentages
- Keys are venue names from hedge_venues list
- Values must sum to 1.0
- Example: `{"binance": 0.4, "bybit": 0.3, "okx": 0.3}`
```

#### List Fields
Document field type and structure, not specific data values:

**Example**:
```markdown
**data_requirements**: List[str]
- List of data types required for this strategy mode
- Example: ["btc_prices", "btc_futures", "funding_rates"]

**instruments**: List[str]  
- List of trading instruments for this venue
- Example: ["BTC-SPOT", "BTC-PERP"]
```

#### Field Classification

### DataProvider Abstraction Layer

#### Base DataProvider Class
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd

class BaseDataProvider(ABC):
    """Abstract base class for all data providers"""
    
    def __init__(self, execution_mode: str, config: Dict):
        self.execution_mode = execution_mode
        self.config = config
        self.available_data_types = []
    
    @abstractmethod
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Return standardized data structure"""
        pass
    
    @abstractmethod
    def validate_data_requirements(self, data_requirements: List[str]) -> None:
        """Validate that this provider can satisfy data requirements"""
        pass
```

#### Standardized Data Structure
```python
def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
    """Return standardized data structure for all components"""
    return {
        'market_data': {
            'prices': {
                'BTC': 45000.0,
                'ETH': 3000.0,
                'USDT': 1.0
            },
            'rates': {
                'funding_binance_btc': 0.0001,
                'aave_usdt_supply': 0.05
            }
        },
        'protocol_data': {
            'aave_indexes': {
                'aUSDT': 1.05,
                'aETH': 1.02
            },
            'oracle_prices': {
                'weETH': 1.0256,
                'wstETH': 1.0150
            }
        }
    }
```

#### DataProvider Factory
```python
class DataProviderFactory:
    """Factory for creating mode-specific data providers"""
    
    @staticmethod
    def create(execution_mode: str, config: Dict) -> BaseDataProvider:
        mode = config['mode']
        data_requirements = config.get('data_requirements', [])
        
        # Create mode-specific data provider
        if mode == 'pure_lending':
            provider = PureLendingDataProvider(execution_mode, config)
        elif mode == 'btc_basis':
            provider = BTCBasisDataProvider(execution_mode, config)
        elif mode == 'eth_basis':
            provider = ETHBasisDataProvider(execution_mode, config)
        elif mode == 'eth_leveraged':
            provider = ETHLeveragedDataProvider(execution_mode, config)
        elif mode == 'eth_staking_only':
            provider = ETHStakingOnlyDataProvider(execution_mode, config)
        elif mode == 'usdt_market_neutral_no_leverage':
            provider = USDTMarketNeutralNoLeverageDataProvider(execution_mode, config)
        elif mode == 'usdt_market_neutral':
            provider = USDTMarketNeutralDataProvider(execution_mode, config)
        else:
            raise ValueError(f"Unknown strategy mode: {mode}")
        
        # Validate that provider can satisfy data requirements
        provider.validate_data_requirements(data_requirements)
        
        return provider
```

### Component Factory Pattern

```python
class ComponentFactory:
    """Factory for creating components with config validation"""
    
    @staticmethod
    def create_risk_monitor(config: Dict, data_provider: BaseDataProvider, execution_mode: str) -> RiskMonitor:
        # Extract risk monitor specific config
        risk_config = config.get('component_config', {}).get('risk_monitor', {})
        
        # Validate required config
        required_fields = ['enabled_risk_types', 'risk_limits']
        for field in required_fields:
            if field not in risk_config:
                raise ValueError(f"Missing required config for risk_monitor: {field}")
        
        return RiskMonitor(config, data_provider, execution_mode)
    
    @staticmethod
    def create_exposure_monitor(config: Dict, data_provider: BaseDataProvider, execution_mode: str) -> ExposureMonitor:
        # Extract exposure monitor specific config
        exposure_config = config.get('component_config', {}).get('exposure_monitor', {})
        
        # Validate required config
        required_fields = ['exposure_currency', 'track_assets', 'conversion_methods']
        for field in required_fields:
            if field not in exposure_config:
                raise ValueError(f"Missing required config for exposure_monitor: {field}")
        
        return ExposureMonitor(config, data_provider, execution_mode)
    
    @staticmethod
    def create_all(config: Dict, data_provider: BaseDataProvider, execution_mode: str) -> Dict[str, Any]:
        """Create all components with config validation"""
        components = {}
        
        components['risk_monitor'] = ComponentFactory.create_risk_monitor(config, data_provider, execution_mode)
        components['exposure_monitor'] = ComponentFactory.create_exposure_monitor(config, data_provider, execution_mode)
        components['pnl_calculator'] = ComponentFactory.create_pnl_calculator(config, data_provider, execution_mode)
        components['strategy_manager'] = ComponentFactory.create_strategy_manager(config, data_provider, execution_mode)
        components['execution_manager'] = ComponentFactory.create_execution_manager(config, data_provider, execution_mode)
        components['results_store'] = ComponentFactory.create_results_store(config, data_provider, execution_mode)
        
        return components
```

### Config-Driven Component Behavior

#### Risk Monitor - Config-Driven Risk Types
```python
class RiskMonitor:
    """Mode-agnostic risk assessment using config-driven behavior"""
    
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str):
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Extract component-specific config
        self.risk_config = config.get('component_config', {}).get('risk_monitor', {})
        self.enabled_risk_types = self.risk_config.get('enabled_risk_types', [])
        self.risk_limits = self.risk_config.get('risk_limits', {})
    
    def assess_risk(self, exposure_data: Dict, market_data: Dict) -> Dict:
        """Assess risk based on config-driven requirements"""
        risk_metrics = {}
        
        # Only calculate risks that are enabled in config
        if 'aave_health_factor' in self.enabled_risk_types:
            if 'aave_indexes' in market_data['protocol_data']:
                risk_metrics['aave_health_factor'] = self._calculate_health_factor(
                    exposure_data, market_data['protocol_data']['aave_indexes']
                )
        
        if 'cex_margin_ratio' in self.enabled_risk_types:
            if 'perp_prices' in market_data['protocol_data']:
                risk_metrics['cex_margin_ratio'] = self._calculate_margin_ratio(
                    exposure_data, market_data['protocol_data']['perp_prices']
                )
        
        if 'funding_risk' in self.enabled_risk_types:
            funding_rates = {k: v for k, v in market_data['market_data']['rates'].items() 
                            if 'funding' in k}
            if funding_rates:
                risk_metrics['funding_risk'] = self._calculate_funding_risk(funding_rates)
        
        # Apply risk limits from config
        risk_alerts = self._check_risk_limits(risk_metrics, self.risk_limits)
        
        return {
            'risk_metrics': risk_metrics,
            'risk_alerts': risk_alerts,
            'enabled_risk_types': self.enabled_risk_types
        }
```

#### Exposure Monitor - Config-Driven Asset Tracking
```python
class ExposureMonitor:
    """Mode-agnostic exposure calculation using config-driven asset tracking"""
    
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str):
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Extract exposure-specific config
        self.exposure_config = config.get('component_config', {}).get('exposure_monitor', {})
        self.exposure_currency = self.exposure_config.get('exposure_currency', 'USDT')
        self.track_assets = self.exposure_config.get('track_assets', [])
        self.conversion_methods = self.exposure_config.get('conversion_methods', {})
        
        # Validate config
        self._validate_exposure_config()
    
    def calculate_exposure(self, timestamp: pd.Timestamp, position_snapshot: Dict, market_data: Dict) -> Dict:
        """Calculate exposure using config-driven asset tracking"""
        
        # Calculate exposure for each tracked asset
        asset_exposures = {}
        total_exposure = 0.0
        
        for asset in self.track_assets:
            asset_exposure = self._calculate_asset_exposure(
                asset, position_snapshot, market_data, timestamp
            )
            asset_exposures[asset] = asset_exposure
            total_exposure += asset_exposure['exposure_value']
        
        # Calculate net delta (sum of all asset deltas)
        net_delta = sum(exp['delta_exposure'] for exp in asset_exposures.values())
        
        return {
            'timestamp': timestamp,
            'exposure_currency': self.exposure_currency,
            'total_exposure': total_exposure,
            'net_delta': net_delta,
            'asset_exposures': asset_exposures,
            'tracked_assets': self.track_assets
        }
```

#### PnL Calculator - Config-Driven Attribution
```python
class PnLCalculator:
    """Mode-agnostic PnL calculation using config-driven attribution"""
    
    def __init__(self, config: Dict, data_provider: BaseDataProvider, execution_mode: str):
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Extract PnL-specific config
        self.pnl_config = config.get('component_config', {}).get('pnl_calculator', {})
        self.attribution_types = self.pnl_config.get('attribution_types', [])
        self.reporting_currency = self.pnl_config.get('reporting_currency', 'USDT')
        self.reconciliation_tolerance = self.pnl_config.get('reconciliation_tolerance', 0.02)
        
        # Initialize cumulative tracking for each attribution type
        self.cumulative_attributions = {attr_type: 0.0 for attr_type in self.attribution_types}
        
        # Store initial value for balance-based PnL
        self.initial_total_value = None
    
    def get_current_pnl(self, current_exposure: Dict, previous_exposure: Optional[Dict], timestamp: pd.Timestamp, period_start: pd.Timestamp) -> Dict:
        """Calculate PnL using config-driven attribution system"""
        
        # Set initial value if first calculation
        if self.initial_total_value is None:
            self.initial_total_value = current_exposure['share_class_value']
        
        # 1. Balance-Based PnL (source of truth)
        balance_pnl_data = self._calculate_balance_based_pnl(current_exposure, period_start, timestamp)
        
        # 2. Attribution PnL (config-driven breakdown)
        attribution_pnl_data = self._calculate_attribution_pnl(current_exposure, previous_exposure, timestamp)
        
        # 3. Reconciliation
        reconciliation = self._reconcile_pnl(balance_pnl_data, attribution_pnl_data, period_start, timestamp)
        
        return {
            'timestamp': timestamp,
            'share_class': self.reporting_currency,
            'balance_based': balance_pnl_data,
            'attribution': attribution_pnl_data,
            'reconciliation': reconciliation
        }
```

### Strategy Factory Configuration

The Strategy Factory is **mode-agnostic** by design and uses `component_config.strategy_factory` for configuration:

```yaml
component_config:
  strategy_factory:
    timeout: 30           # Strategy creation timeout in seconds
    max_retries: 3        # Maximum retry attempts for strategy creation
    validation_strict: true # Strict mode validation (fail fast on errors)
```

#### Strategy Factory Configuration Fields

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `timeout` | int | 30 | Maximum time in seconds to wait for strategy creation |
| `max_retries` | int | 3 | Maximum number of retry attempts for failed strategy creation |
| `validation_strict` | bool | true | Enable strict validation (fail fast on configuration errors) |

#### Strategy Factory Usage Example

```python
from basis_strategy_v1.strategy.strategy_factory import StrategyFactory

# Create strategy instance using factory
strategy = StrategyFactory.create_strategy(
    mode="btc_basis",
    config=config,
    data_provider=data_provider,
    execution_mode="backtest",
    exposure_monitor=exposure_monitor,
    risk_monitor=risk_monitor
)

# Factory uses config-driven timeout and retry settings
# - timeout: 30 seconds (from config)
# - max_retries: 3 attempts (from config)
# - validation_strict: true (from config)
```

#### Strategy Factory Environment Variables

The Strategy Factory also uses component-specific environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `STRATEGY_FACTORY_TIMEOUT` | 30 | Override config timeout value |
| `STRATEGY_FACTORY_MAX_RETRIES` | 3 | Override config max_retries value |

**Environment Variable Precedence**: Environment variables override config values if set.

### 📋 **COMPREHENSIVE CONFIG SCHEMA TEMPLATES**

This section provides **complete, production-ready config templates** for all 7 strategy modes showing the full schema for mode-agnostic and mode-specific configurations.

---

## **FULL CONFIG SCHEMA STRUCTURE**

Every strategy mode configuration follows this complete structure:

```yaml
# ============================================================================
# STRATEGY IDENTIFICATION
# ============================================================================
mode: "mode_name"                    # Strategy mode identifier
share_class: "USDT" | "ETH"                   # Share class currency
asset: "USDT" | "ETH" | "BTC"                 # Primary asset

# ============================================================================
# STRATEGY FLAGS (Enable/Disable Strategy Components)
# ============================================================================
lending_enabled: true | false                  # Enable AAVE lending
staking_enabled: true | false                  # Enable LST staking
basis_trade_enabled: true | false              # Enable basis trading (spot + perp hedging)
borrowing_enabled: true | false                # Enable AAVE borrowing (leverage)
enable_market_impact: true | false             # Enable market impact modeling

# ============================================================================
# ASSET CONFIGURATION
# ============================================================================
lst_type: "weeth" | "wsteth" | null           # LST type (if staking_enabled)
rewards_mode: "base_only" | "base_eigen" | "base_eigen_seasonal"  # Reward calculation mode
position_deviation_threshold: 0.0-1.0         # Min deviation to trigger rebalancing (default 0.02 = 2%)

# ============================================================================
# HEDGING CONFIGURATION (For market-neutral strategies)
# ============================================================================
hedge_venues: ["binance", "bybit", "okx"]     # CEX venues for perp hedging
hedge_allocation_binance: 0.0-1.0             # Allocation to Binance (must sum to 1.0)
hedge_allocation_bybit: 0.0-1.0               # Allocation to Bybit
hedge_allocation_okx: 0.0-1.0                 # Allocation to OKX
stake_allocation_eth: 0.0-1.0                 # Proportion for ETH staking (USDT market neutral modes)

# ============================================================================
# RISK PARAMETERS
# ============================================================================
margin_ratio_target: 0.0-1.0                  # Target CEX margin ratio (basis modes)
max_stake_spread_move: 0.0-1.0                # Max expected adverse LST/ETH oracle move
max_ltv: 0.0-1.0                              # Maximum LTV for AAVE (from AAVE risk params)
liquidation_threshold: 0.0-1.0                # Liquidation threshold (from AAVE risk params)
delta_tolerance: 0.0-1.0                      # Delta neutrality tolerance (basis modes)

# ============================================================================
# PERFORMANCE TARGETS
# ============================================================================
target_apy: 0.0-1.0                           # Target APY (annual)
max_drawdown: 0.0-1.0                         # Maximum drawdown tolerance

# ============================================================================
# EXECUTION PARAMETERS
# ============================================================================
time_throttle_interval: 1-3600                # Time between actions (seconds, live mode)

# ============================================================================
# DATA REQUIREMENTS (What data this mode needs)
# ============================================================================
data_requirements:
  - "data_type_1"                             # Data type identifiers
  - "data_type_2"
  # ... (mode-specific data needs)

# ============================================================================
# COMPONENT CONFIGURATION (How components should behave)
# ============================================================================
component_config:
  risk_monitor:
    enabled_risk_types: ["risk_type_1", "risk_type_2"]
    risk_limits:
      risk_type_1_min: 0.0
      risk_type_1_max: 1.0
  
  exposure_monitor:
    exposure_currency: "USDT" | "ETH"
    track_assets: ["asset_1", "asset_2"]
    conversion_methods:
      asset_1: "conversion_method"
      asset_2: "conversion_method"
  
  pnl_calculator:
    attribution_types: ["attribution_1", "attribution_2"]
    reporting_currency: "USDT" | "ETH"
    reconciliation_tolerance: 0.0-1.0
  
  strategy_manager:
    strategy_type: "mode_name"
    actions: ["action_1", "action_2"]
    rebalancing_triggers: ["trigger_1", "trigger_2"]
    position_calculation:
      target_position: "calculation_method"
      max_position: "limit_method"
  
  execution_manager:
    supported_actions: ["action_1", "action_2"]
    action_mapping:
      action_1: ["venue_action_1", "venue_action_2"]
      action_2: ["venue_action_3"]
  
  results_store:
    result_types: ["result_type_1", "result_type_2"]
    balance_sheet_assets: ["asset_1", "asset_2"]
    pnl_attribution_types: ["attribution_1", "attribution_2"]
```

---

## **1. PURE LENDING MODE - COMPLETE CONFIG**

```yaml
# ============================================================================
# Pure Lending Mode Configuration
# Simple USDT lending strategy without leverage, staking, or hedging
# ============================================================================

# STRATEGY IDENTIFICATION
mode: "pure_lending"
share_class: "USDT"
asset: "USDT"

# STRATEGY FLAGS
lending_enabled: true
staking_enabled: false
basis_trade_enabled: false
borrowing_enabled: false
enable_market_impact: true

# ASSET CONFIGURATION
lst_type: null                                # No staking
rewards_mode: "base_only"                     # No special rewards
position_deviation_threshold: 0.02            # 2% deviation triggers rebalancing

# HEDGING CONFIGURATION (Not applicable - market neutral by nature)
hedge_venues: []
hedge_allocation_binance: 0.0
hedge_allocation_bybit: 0.0
hedge_allocation_okx: 0.0

# RISK PARAMETERS (Simple lending - minimal risk)
margin_ratio_target: 1.0                      # Not applicable (no CEX margin)
max_stake_spread_move: 0.0                    # Not applicable (no staking)
max_ltv: 0.0                                  # Not applicable (no borrowing)
liquidation_threshold: 0.0                    # Not applicable (no borrowing)
delta_tolerance: 0.0                          # Not applicable (no basis trading)

# PERFORMANCE TARGETS
target_apy: 0.05                              # 5% APY target
max_drawdown: 0.005                           # 0.5% max drawdown (only gas costs)

# EXECUTION PARAMETERS
time_throttle_interval: 60                    # 60 seconds between actions (live)

# DATA REQUIREMENTS
data_requirements:
  - "usdt_prices"                             # USDT/USD spot prices
  - "aave_lending_rates"                      # AAVE USDT supply rates
  - "aave_indexes"                            # AAVE liquidity indexes
  - "gas_costs"                               # Ethereum gas prices
  - "execution_costs"                         # Execution cost models

# COMPONENT CONFIGURATION
component_config:
  risk_monitor:
    enabled_risk_types: ["protocol_risk"]     # Only protocol risk (AAVE)
    risk_limits:
      protocol_risk_max: 0.01                 # 1% max protocol risk
  
  exposure_monitor:
    exposure_currency: "USDT"
    track_assets: ["USDT", "aUSDT", "ETH"]    # Track USDT, aUSDT, and ETH (gas)
    conversion_methods:
      USDT: "direct"                          # 1:1 conversion
      aUSDT: "aave_index"                     # Convert via AAVE index
      ETH: "usd_price"                        # Convert via ETH/USD price
  
  pnl_calculator:
    attribution_types: ["supply_yield", "transaction_costs"]
    reporting_currency: "USDT"
    reconciliation_tolerance: 0.02            # 2% tolerance
  
  strategy_manager:
    strategy_type: "pure_lending"
    actions: ["entry_full", "exit_full"]      # Only full entry/exit
    rebalancing_triggers: ["deposit", "withdrawal"]
    position_calculation:
      target_position: "aave_usdt_supply"
      max_position: "equity"                  # All equity to AAVE
  
  execution_manager:
    supported_actions: ["aave_supply", "aave_withdraw"]
    action_mapping:
      entry_full: ["aave_supply"]
      exit_full: ["aave_withdraw"]
  
  results_store:
    result_types: ["balance_sheet", "pnl_attribution", "risk_metrics", "execution_log"]
    balance_sheet_assets: ["USDT", "aUSDT", "ETH"]
    pnl_attribution_types: ["supply_yield", "transaction_costs"]
```

---

## **2. BTC BASIS MODE - COMPLETE CONFIG**

```yaml
# ============================================================================
# BTC Basis Trading Mode Configuration
# Market-neutral BTC basis trading with perp hedging across multiple CEX
# ============================================================================

# STRATEGY IDENTIFICATION
mode: "btc_basis"
share_class: "USDT"
asset: "BTC"

# STRATEGY FLAGS
lending_enabled: false
staking_enabled: false
basis_trade_enabled: true
borrowing_enabled: false
enable_market_impact: true

# ASSET CONFIGURATION
lst_type: null                                # No staking
rewards_mode: "base_only"                     # No special rewards
position_deviation_threshold: 0.02            # 2% deviation triggers rebalancing

# HEDGING CONFIGURATION
hedge_venues: ["binance", "bybit", "okx"]
hedge_allocation_binance: 0.4                 # 40% to Binance
hedge_allocation_bybit: 0.3                   # 30% to Bybit
hedge_allocation_okx: 0.3                     # 30% to OKX

# RISK PARAMETERS
margin_ratio_target: 0.8                      # 80% conservative margin ratio
max_stake_spread_move: 0.0                    # Not applicable (no staking)
max_ltv: 0.0                                  # Not applicable (no borrowing)
liquidation_threshold: 0.0                    # Not applicable (no borrowing)
delta_tolerance: 0.005                        # 0.5% delta tolerance

# PERFORMANCE TARGETS
target_apy: 0.08                              # 8% APY target (funding rates)
max_drawdown: 0.02                            # 2% max drawdown

# EXECUTION PARAMETERS
time_throttle_interval: 60                    # 60 seconds between actions (live)

# DATA REQUIREMENTS
data_requirements:
  - "btc_prices"                              # BTC/USDT spot prices
  - "btc_futures"                             # BTC perpetual futures prices
  - "funding_rates"                           # Funding rates (all venues)
  - "gas_costs"                               # Ethereum gas prices
  - "execution_costs"                         # Execution cost models

# COMPONENT CONFIGURATION
component_config:
  risk_monitor:
    enabled_risk_types: ["cex_margin_ratio", "funding_risk", "basis_risk", "delta_risk"]
    risk_limits:
      cex_margin_ratio_min: 0.2               # 20% minimum margin ratio
      funding_risk_max: 0.05                  # 5% max funding risk
      basis_risk_max: 0.03                    # 3% max basis risk
      delta_risk_max: 0.01                    # 1% max delta risk
  
  exposure_monitor:
    exposure_currency: "USDT"
    track_assets: ["BTC", "USDT", "ETH", "BTC_SPOT", "BTC_PERP"]
    conversion_methods:
      BTC: "usd_price"                        # Convert via BTC/USD price
      USDT: "direct"                          # 1:1 conversion
      ETH: "usd_price"                        # Convert via ETH/USD price
      BTC_SPOT: "usd_price"                   # Spot position value
      BTC_PERP: "perp_mark_price"             # Perp position value
  
  pnl_calculator:
    attribution_types: ["funding_pnl", "delta_pnl", "basis_pnl", "transaction_costs"]
    reporting_currency: "USDT"
    reconciliation_tolerance: 0.02            # 2% tolerance
  
  strategy_manager:
    strategy_type: "btc_basis"
    actions: ["entry_full", "entry_partial", "exit_partial", "exit_full"]
    rebalancing_triggers: ["deposit", "withdrawal", "delta_drift", "funding_change"]
    position_calculation:
      target_position: "btc_spot_long"
      hedge_position: "btc_perp_short"
      hedge_allocation: {"binance": 0.4, "bybit": 0.3, "okx": 0.3}
  
  execution_manager:
    supported_actions: ["cex_spot_buy", "cex_spot_sell", "cex_perp_short", "cex_perp_close", "cex_margin_add"]
    action_mapping:
      entry_full: ["cex_spot_buy", "cex_perp_short"]
      entry_partial: ["cex_spot_buy", "cex_perp_short"]
      exit_partial: ["cex_perp_close", "cex_spot_sell"]
      exit_full: ["cex_perp_close", "cex_spot_sell"]
  
  results_store:
    result_types: ["balance_sheet", "pnl_attribution", "risk_metrics", "execution_log", "delta_tracking", "funding_tracking"]
    balance_sheet_assets: ["BTC", "USDT", "ETH", "BTC_SPOT", "BTC_PERP"]
    pnl_attribution_types: ["funding_pnl", "delta_pnl", "basis_pnl", "transaction_costs"]
    delta_tracking_assets: ["BTC"]
    funding_tracking_venues: ["binance", "bybit", "okx"]
```

---

## **3. ETH LEVERAGED MODE - COMPLETE CONFIG**

```yaml
# ============================================================================
# ETH Leveraged Staking Mode Configuration
# Leveraged ETH staking with LST rewards (no hedging - directional ETH exposure)
# ============================================================================

# STRATEGY IDENTIFICATION
mode: "eth_leveraged"
share_class: "ETH"
asset: "ETH"

# STRATEGY FLAGS
lending_enabled: true                         # AAVE lending for leverage
staking_enabled: true                         # LST staking
basis_trade_enabled: false                    # No hedging (directional)
borrowing_enabled: true                       # AAVE borrowing for leverage
enable_market_impact: true

# ASSET CONFIGURATION
lst_type: "weeth"                             # EtherFi weETH
rewards_mode: "base_eigen"                    # Base staking + EIGEN rewards
position_deviation_threshold: 0.02            # 2% deviation triggers rebalancing

# HEDGING CONFIGURATION (Not applicable - directional strategy)
hedge_venues: []
hedge_allocation_binance: 0.0
hedge_allocation_bybit: 0.0
hedge_allocation_okx: 0.0

# RISK PARAMETERS
margin_ratio_target: 1.0                      # Not applicable (no CEX margin)
max_stake_spread_move: 0.02215                # 2.215% max adverse weETH/ETH oracle move
max_ltv: 0.91                                 # 91% maximum LTV (from AAVE risk params)
liquidation_threshold: 0.95                   # 95% liquidation threshold (from AAVE)
delta_tolerance: 0.0                          # Not applicable (directional)

# PERFORMANCE TARGETS
target_apy: 0.20                              # 20% APY target (leveraged staking)
max_drawdown: 0.04                            # 4% max drawdown

# EXECUTION PARAMETERS
time_throttle_interval: 60                    # 60 seconds between actions (live)

# DATA REQUIREMENTS
data_requirements:
  - "eth_prices"                              # ETH/USDT spot prices
  - "weeth_prices"                            # weETH/ETH oracle prices
  - "aave_lending_rates"                      # AAVE rates (weETH, WETH)
  - "aave_indexes"                            # AAVE liquidity indexes
  - "staking_rewards"                         # Base staking yields
  - "eigen_rewards"                           # EIGEN distributions
  - "gas_costs"                               # Ethereum gas prices
  - "execution_costs"                         # Execution cost models
  - "aave_risk_params"                        # AAVE v3 risk parameters

# COMPONENT CONFIGURATION
component_config:
  risk_monitor:
    enabled_risk_types: ["aave_health_factor", "liquidation_risk", "ltv_risk", "protocol_risk"]
    risk_limits:
      aave_health_factor_min: 1.1             # 1.1 minimum health factor
      liquidation_threshold: 0.95             # 95% liquidation threshold
      ltv_max: 0.91                           # 91% max LTV
      protocol_risk_max: 0.02                 # 2% max protocol risk
  
  exposure_monitor:
    exposure_currency: "ETH"
    track_assets: ["ETH", "weETH", "aWeETH", "variableDebtWETH", "EIGEN", "KING"]
    conversion_methods:
      ETH: "direct"                           # 1:1 (base currency)
      weETH: "oracle_price"                   # Convert via weETH/ETH oracle
      aWeETH: "aave_index"                    # Convert via AAVE liquidity index
      variableDebtWETH: "aave_index"          # Convert via AAVE borrow index
      EIGEN: "usd_price"                      # Convert via EIGEN/USD price
      KING: "unwrap"                          # Unwrap KING to EIGEN + ETHFI
  
  pnl_calculator:
    attribution_types: ["supply_yield", "staking_yield_oracle", "staking_yield_rewards", "borrow_costs", "price_change_pnl", "transaction_costs"]
    reporting_currency: "ETH"
    reconciliation_tolerance: 0.02            # 2% tolerance
  
  strategy_manager:
    strategy_type: "eth_leveraged"
    actions: ["entry_full", "entry_partial", "exit_partial", "exit_full", "sell_dust", "add_leverage", "reduce_leverage"]
    rebalancing_triggers: ["deposit", "withdrawal", "ltv_drift", "dust_threshold"]
    position_calculation:
      target_position: "leveraged_eth_staking"
      leverage_calculation: "target_ltv / (1 - target_ltv)"
      dust_threshold: 0.01                    # 1% of equity
  
  execution_manager:
    supported_actions: ["etherfi_stake", "etherfi_unstake", "aave_supply", "aave_withdraw", "aave_borrow", "aave_repay", "sell_dust", "flash_loan"]
    action_mapping:
      entry_full: ["etherfi_stake", "aave_supply", "aave_borrow"]
      entry_partial: ["etherfi_stake", "aave_supply", "aave_borrow"]
      exit_partial: ["aave_repay", "aave_withdraw", "etherfi_unstake"]
      exit_full: ["aave_repay", "aave_withdraw", "etherfi_unstake"]
      sell_dust: ["unwrap_king", "sell_dust"]
      add_leverage: ["flash_loan", "aave_borrow"]
      reduce_leverage: ["aave_repay"]
  
  results_store:
    result_types: ["balance_sheet", "pnl_attribution", "risk_metrics", "execution_log", "leverage_tracking", "dust_tracking"]
    balance_sheet_assets: ["ETH", "weETH", "aWeETH", "variableDebtWETH", "EIGEN", "KING"]
    pnl_attribution_types: ["supply_yield", "staking_yield_oracle", "staking_yield_rewards", "borrow_costs", "price_change_pnl", "transaction_costs"]
    leverage_tracking: true
    dust_tracking_tokens: ["EIGEN", "ETHFI", "KING"]
```

---

## **4. ETH STAKING ONLY MODE - COMPLETE CONFIG**

```yaml
# ============================================================================
# ETH Staking Only Mode Configuration
# Unleveraged ETH staking (no borrowing, no hedging - directional ETH exposure)
# ============================================================================

# STRATEGY IDENTIFICATION
mode: "eth_staking_only"
share_class: "ETH"
asset: "ETH"

# STRATEGY FLAGS
lending_enabled: false                        # No AAVE lending
staking_enabled: true                         # LST staking
basis_trade_enabled: false                    # No hedging (directional)
borrowing_enabled: false                      # No leverage
enable_market_impact: true

# ASSET CONFIGURATION
lst_type: "weeth"                             # EtherFi weETH
rewards_mode: "base_eigen"                    # Base staking + EIGEN rewards
position_deviation_threshold: 0.02            # 2% deviation triggers rebalancing

# HEDGING CONFIGURATION (Not applicable - directional strategy)
hedge_venues: []
hedge_allocation_binance: 0.0
hedge_allocation_bybit: 0.0
hedge_allocation_okx: 0.0

# RISK PARAMETERS (Minimal - no leverage, no hedging)
margin_ratio_target: 1.0                      # Not applicable
max_stake_spread_move: 0.0                    # Not applicable (no leverage)
max_ltv: 0.0                                  # Not applicable (no borrowing)
liquidation_threshold: 0.0                    # Not applicable (no borrowing)
delta_tolerance: 0.0                          # Not applicable (directional)

# PERFORMANCE TARGETS
target_apy: 0.03                              # 3% APY target (base staking)
max_drawdown: 0.01                            # 1% max drawdown (staking volatility)

# EXECUTION PARAMETERS
time_throttle_interval: 60                    # 60 seconds between actions (live)

# DATA REQUIREMENTS
data_requirements:
  - "eth_prices"                              # ETH/USDT spot prices
  - "weeth_prices"                            # weETH/ETH oracle prices
  - "staking_rewards"                         # Base staking yields
  - "eigen_rewards"                           # EIGEN distributions
  - "gas_costs"                               # Ethereum gas prices
  - "execution_costs"                         # Execution cost models

# COMPONENT CONFIGURATION
component_config:
  risk_monitor:
    enabled_risk_types: ["protocol_risk"]     # Only protocol risk
    risk_limits:
      protocol_risk_max: 0.01                 # 1% max protocol risk
  
  exposure_monitor:
    exposure_currency: "ETH"
    track_assets: ["ETH", "weETH", "EIGEN", "KING"]
    conversion_methods:
      ETH: "direct"                           # 1:1 (base currency)
      weETH: "oracle_price"                   # Convert via weETH/ETH oracle
      EIGEN: "usd_price"                      # Convert via EIGEN/USD price
      KING: "unwrap"                          # Unwrap KING to EIGEN + ETHFI
  
  pnl_calculator:
    attribution_types: ["staking_yield_oracle", "staking_yield_rewards", "price_change_pnl", "transaction_costs"]
    reporting_currency: "ETH"
    reconciliation_tolerance: 0.02            # 2% tolerance
  
  strategy_manager:
    strategy_type: "eth_staking_only"
    actions: ["entry_full", "exit_full", "sell_dust"]
    rebalancing_triggers: ["deposit", "withdrawal", "dust_threshold"]
    position_calculation:
      target_position: "eth_staking"
      max_position: "equity"                  # All equity to staking
  
  execution_manager:
    supported_actions: ["etherfi_stake", "etherfi_unstake", "sell_dust"]
    action_mapping:
      entry_full: ["etherfi_stake"]
      exit_full: ["etherfi_unstake"]
      sell_dust: ["unwrap_king", "sell_dust"]
  
  results_store:
    result_types: ["balance_sheet", "pnl_attribution", "risk_metrics", "execution_log", "dust_tracking"]
    balance_sheet_assets: ["ETH", "weETH", "EIGEN", "KING"]
    pnl_attribution_types: ["staking_yield_oracle", "staking_yield_rewards", "price_change_pnl", "transaction_costs"]
    dust_tracking_tokens: ["EIGEN", "ETHFI", "KING"]
```

---

## **5. ETH BASIS MODE - COMPLETE CONFIG**

```yaml
# ============================================================================
# ETH Basis Trading Mode Configuration
# Market-neutral ETH basis trading (ETH share class - no USDT conversion)
# ============================================================================

# STRATEGY IDENTIFICATION
mode: "eth_basis"
share_class: "ETH"
asset: "ETH"

# STRATEGY FLAGS
lending_enabled: false
staking_enabled: false
basis_trade_enabled: true
borrowing_enabled: false
enable_market_impact: true

# ASSET CONFIGURATION
lst_type: null                                # No staking
rewards_mode: "base_only"                     # No special rewards
position_deviation_threshold: 0.02            # 2% deviation triggers rebalancing

# HEDGING CONFIGURATION
hedge_venues: ["binance", "bybit", "okx"]
hedge_allocation_binance: 0.4                 # 40% to Binance
hedge_allocation_bybit: 0.3                   # 30% to Bybit
hedge_allocation_okx: 0.3                     # 30% to OKX

# RISK PARAMETERS
margin_ratio_target: 0.8                      # 80% conservative margin ratio
max_stake_spread_move: 0.0                    # Not applicable (no staking)
max_ltv: 0.0                                  # Not applicable (no borrowing)
liquidation_threshold: 0.0                    # Not applicable (no borrowing)
delta_tolerance: 0.005                        # 0.5% delta tolerance

# PERFORMANCE TARGETS
target_apy: 0.08                              # 8% APY target (funding rates)
max_drawdown: 0.02                            # 2% max drawdown

# EXECUTION PARAMETERS
time_throttle_interval: 60                    # 60 seconds between actions (live)

# DATA REQUIREMENTS
data_requirements:
  - "eth_prices"                              # ETH/USDT spot prices
  - "eth_futures"                             # ETH perpetual futures prices
  - "funding_rates"                           # Funding rates (all venues)
  - "gas_costs"                               # Ethereum gas prices
  - "execution_costs"                         # Execution cost models

# COMPONENT CONFIGURATION
component_config:
  risk_monitor:
    enabled_risk_types: ["cex_margin_ratio", "funding_risk", "basis_risk", "delta_risk"]
    risk_limits:
      cex_margin_ratio_min: 0.2               # 20% minimum margin ratio
      funding_risk_max: 0.05                  # 5% max funding risk
      basis_risk_max: 0.03                    # 3% max basis risk
      delta_risk_max: 0.01                    # 1% max delta risk
  
  exposure_monitor:
    exposure_currency: "ETH"
    track_assets: ["ETH", "ETH_SPOT", "ETH_PERP", "USDT"]
    conversion_methods:
      ETH: "direct"                           # 1:1 (base currency)
      ETH_SPOT: "direct"                      # Spot position value
      ETH_PERP: "perp_mark_price"             # Perp position value
      USDT: "eth_price"                       # Convert USDT to ETH
  
  pnl_calculator:
    attribution_types: ["funding_pnl", "delta_pnl", "basis_pnl", "transaction_costs"]
    reporting_currency: "ETH"
    reconciliation_tolerance: 0.02            # 2% tolerance
  
  strategy_manager:
    strategy_type: "eth_basis"
    actions: ["entry_full", "entry_partial", "exit_partial", "exit_full"]
    rebalancing_triggers: ["deposit", "withdrawal", "delta_drift", "funding_change"]
    position_calculation:
      target_position: "eth_spot_long"
      hedge_position: "eth_perp_short"
      hedge_allocation: {"binance": 0.4, "bybit": 0.3, "okx": 0.3}
  
  execution_manager:
    supported_actions: ["cex_spot_buy", "cex_spot_sell", "cex_perp_short", "cex_perp_close", "cex_margin_add"]
    action_mapping:
      entry_full: ["cex_spot_buy", "cex_perp_short"]
      entry_partial: ["cex_spot_buy", "cex_perp_short"]
      exit_partial: ["cex_perp_close", "cex_spot_sell"]
      exit_full: ["cex_perp_close", "cex_spot_sell"]
  
  results_store:
    result_types: ["balance_sheet", "pnl_attribution", "risk_metrics", "execution_log", "delta_tracking", "funding_tracking"]
    balance_sheet_assets: ["ETH", "ETH_SPOT", "ETH_PERP", "USDT"]
    pnl_attribution_types: ["funding_pnl", "delta_pnl", "basis_pnl", "transaction_costs"]
    delta_tracking_assets: ["ETH"]
    funding_tracking_venues: ["binance", "bybit", "okx"]
```

---

## **6. USDT MARKET NEUTRAL (NO LEVERAGE) MODE - COMPLETE CONFIG**

```yaml
# ============================================================================
# USDT Market Neutral No Leverage Mode Configuration
# Market-neutral ETH staking without leverage (USDT share class)
# ============================================================================

# STRATEGY IDENTIFICATION
mode: "usdt_market_neutral_no_leverage"
share_class: "USDT"
asset: "ETH"

# STRATEGY FLAGS
lending_enabled: false                        # No AAVE lending
staking_enabled: true                         # LST staking
basis_trade_enabled: true                     # Perp hedging for market neutrality
borrowing_enabled: false                      # No leverage
enable_market_impact: true

# ASSET CONFIGURATION
lst_type: "weeth"                             # EtherFi weETH
rewards_mode: "base_eigen_seasonal"           # Base + EIGEN + seasonal rewards
position_deviation_threshold: 0.02            # 2% deviation triggers rebalancing
stake_allocation_eth: 0.5                     # 50% to staking, 50% to hedge margin

# HEDGING CONFIGURATION
hedge_venues: ["binance", "bybit", "okx"]
hedge_allocation_binance: 0.4                 # 40% to Binance
hedge_allocation_bybit: 0.3                   # 30% to Bybit
hedge_allocation_okx: 0.3                     # 30% to OKX

# RISK PARAMETERS
margin_ratio_target: 0.8                      # 80% conservative margin ratio
max_stake_spread_move: 0.0                    # Not applicable (no leverage)
max_ltv: 0.0                                  # Not applicable (no borrowing)
liquidation_threshold: 0.0                    # Not applicable (no borrowing)
delta_tolerance: 0.005                        # 0.5% delta tolerance

# PERFORMANCE TARGETS
target_apy: 0.08                              # 8% APY target (staking + funding)
max_drawdown: 0.02                            # 2% max drawdown

# EXECUTION PARAMETERS
time_throttle_interval: 60                    # 60 seconds between actions (live)

# DATA REQUIREMENTS
data_requirements:
  - "eth_prices"                              # ETH/USDT spot prices
  - "weeth_prices"                            # weETH/ETH oracle prices
  - "eth_futures"                             # ETH perpetual futures prices
  - "funding_rates"                           # Funding rates (all venues)
  - "staking_rewards"                         # Base staking yields
  - "eigen_rewards"                           # EIGEN distributions
  - "gas_costs"                               # Ethereum gas prices
  - "execution_costs"                         # Execution cost models

# COMPONENT CONFIGURATION
component_config:
  risk_monitor:
    enabled_risk_types: ["cex_margin_ratio", "funding_risk", "delta_risk", "protocol_risk"]
    risk_limits:
      cex_margin_ratio_min: 0.2               # 20% minimum margin ratio
      funding_risk_max: 0.05                  # 5% max funding risk
      delta_risk_max: 0.01                    # 1% max delta risk
      protocol_risk_max: 0.01                 # 1% max protocol risk
  
  exposure_monitor:
    exposure_currency: "USDT"
    track_assets: ["ETH", "weETH", "USDT", "ETH_PERP", "EIGEN", "KING"]
    conversion_methods:
      ETH: "usd_price"                        # Convert via ETH/USD price
      weETH: "oracle_price"                   # Convert via weETH/ETH oracle, then USD
      USDT: "direct"                          # 1:1 conversion
      ETH_PERP: "perp_mark_price"             # Perp position value
      EIGEN: "usd_price"                      # Convert via EIGEN/USD price
      KING: "unwrap"                          # Unwrap KING to EIGEN + ETHFI
  
  pnl_calculator:
    attribution_types: ["staking_yield_oracle", "staking_yield_rewards", "funding_pnl", "delta_pnl", "transaction_costs"]
    reporting_currency: "USDT"
    reconciliation_tolerance: 0.02            # 2% tolerance
  
  strategy_manager:
    strategy_type: "usdt_market_neutral_no_leverage"
    actions: ["entry_full", "entry_partial", "exit_partial", "exit_full", "sell_dust", "rebalance_hedge"]
    rebalancing_triggers: ["deposit", "withdrawal", "delta_drift", "funding_change", "dust_threshold"]
    position_calculation:
      target_position: "eth_staking"
      hedge_position: "eth_perp_short"
      stake_allocation: 0.5
      hedge_allocation: {"binance": 0.4, "bybit": 0.3, "okx": 0.3}
  
  execution_manager:
    supported_actions: ["etherfi_stake", "etherfi_unstake", "cex_perp_short", "cex_perp_close", "cex_margin_add", "sell_dust"]
    action_mapping:
      entry_full: ["etherfi_stake", "cex_perp_short"]
      entry_partial: ["etherfi_stake", "cex_perp_short"]
      exit_partial: ["cex_perp_close", "etherfi_unstake"]
      exit_full: ["cex_perp_close", "etherfi_unstake"]
      sell_dust: ["unwrap_king", "sell_dust"]
      rebalance_hedge: ["cex_perp_adjust"]
  
  results_store:
    result_types: ["balance_sheet", "pnl_attribution", "risk_metrics", "execution_log", "delta_tracking", "funding_tracking", "dust_tracking"]
    balance_sheet_assets: ["ETH", "weETH", "USDT", "ETH_PERP", "EIGEN", "KING"]
    pnl_attribution_types: ["staking_yield_oracle", "staking_yield_rewards", "funding_pnl", "delta_pnl", "transaction_costs"]
    delta_tracking_assets: ["ETH"]
    funding_tracking_venues: ["binance", "bybit", "okx"]
    dust_tracking_tokens: ["EIGEN", "ETHFI", "KING"]
```

---

## **7. USDT MARKET NEUTRAL MODE - COMPLETE CONFIG**

```yaml
# ============================================================================
# USDT Market Neutral Mode Configuration
# Market-neutral leveraged ETH staking (USDT share class) - FULL COMPLEXITY
# ============================================================================

# STRATEGY IDENTIFICATION
mode: "usdt_market_neutral"
share_class: "USDT"
asset: "ETH"

# STRATEGY FLAGS
lending_enabled: true                         # AAVE lending for leverage
staking_enabled: true                         # LST staking
basis_trade_enabled: true                     # Perp hedging for market neutrality
borrowing_enabled: true                       # AAVE borrowing for leverage
enable_market_impact: true

# ASSET CONFIGURATION
lst_type: "weeth"                             # EtherFi weETH
rewards_mode: "base_eigen_seasonal"           # Base + EIGEN + seasonal rewards
position_deviation_threshold: 0.02            # 2% deviation triggers rebalancing
stake_allocation_eth: 0.5                     # 50% to leveraged staking, 50% to hedge margin

# HEDGING CONFIGURATION
hedge_venues: ["binance", "bybit", "okx"]
hedge_allocation_binance: 0.4                 # 40% to Binance
hedge_allocation_bybit: 0.3                   # 30% to Bybit
hedge_allocation_okx: 0.3                     # 30% to OKX

# RISK PARAMETERS
margin_ratio_target: 0.8                      # 80% conservative margin ratio (CEX)
max_stake_spread_move: 0.02215                # 2.215% max adverse weETH/ETH oracle move
max_ltv: 0.91                                 # 91% maximum LTV (from AAVE risk params)
liquidation_threshold: 0.95                   # 95% liquidation threshold (from AAVE)
delta_tolerance: 0.005                        # 0.5% delta tolerance

# PERFORMANCE TARGETS
target_apy: 0.15                              # 15% APY target (leveraged staking + funding)
max_drawdown: 0.04                            # 4% max drawdown

# EXECUTION PARAMETERS
time_throttle_interval: 60                    # 60 seconds between actions (live)

# DATA REQUIREMENTS
data_requirements:
  - "eth_prices"                              # ETH/USDT spot prices
  - "weeth_prices"                            # weETH/ETH oracle prices
  - "eth_futures"                             # ETH perpetual futures prices
  - "funding_rates"                           # Funding rates (all venues)
  - "aave_lending_rates"                      # AAVE rates (weETH, WETH)
  - "aave_indexes"                            # AAVE liquidity indexes
  - "staking_rewards"                         # Base staking yields
  - "eigen_rewards"                           # EIGEN distributions
  - "gas_costs"                               # Ethereum gas prices
  - "execution_costs"                         # Execution cost models
  - "aave_risk_params"                        # AAVE v3 risk parameters

# COMPONENT CONFIGURATION
component_config:
  risk_monitor:
    enabled_risk_types: ["aave_health_factor", "liquidation_risk", "ltv_risk", "cex_margin_ratio", "funding_risk", "delta_risk", "protocol_risk"]
    risk_limits:
      aave_health_factor_min: 1.1             # 1.1 minimum health factor
      liquidation_threshold: 0.95             # 95% liquidation threshold
      ltv_max: 0.91                           # 91% max LTV
      cex_margin_ratio_min: 0.2               # 20% minimum margin ratio
      funding_risk_max: 0.05                  # 5% max funding risk
      delta_risk_max: 0.01                    # 1% max delta risk
      protocol_risk_max: 0.02                 # 2% max protocol risk
  
  exposure_monitor:
    exposure_currency: "USDT"
    track_assets: ["ETH", "weETH", "aWeETH", "variableDebtWETH", "USDT", "ETH_PERP", "EIGEN", "KING"]
    conversion_methods:
      ETH: "usd_price"                        # Convert via ETH/USD price
      weETH: "oracle_price"                   # Convert via weETH/ETH oracle, then USD
      aWeETH: "aave_index"                    # Convert via AAVE liquidity index, then USD
      variableDebtWETH: "aave_index"          # Convert via AAVE borrow index, then USD
      USDT: "direct"                          # 1:1 conversion
      ETH_PERP: "perp_mark_price"             # Perp position value
      EIGEN: "usd_price"                      # Convert via EIGEN/USD price
      KING: "unwrap"                          # Unwrap KING to EIGEN + ETHFI
  
  pnl_calculator:
    attribution_types: ["supply_yield", "staking_yield_oracle", "staking_yield_rewards", "borrow_costs", "funding_pnl", "delta_pnl", "price_change_pnl", "transaction_costs"]
    reporting_currency: "USDT"
    reconciliation_tolerance: 0.02            # 2% tolerance
  
  strategy_manager:
    strategy_type: "usdt_market_neutral"
    actions: ["entry_full", "entry_partial", "exit_partial", "exit_full", "sell_dust", "add_leverage", "reduce_leverage", "rebalance_hedge"]
    rebalancing_triggers: ["deposit", "withdrawal", "ltv_drift", "delta_drift", "funding_change", "dust_threshold"]
    position_calculation:
      target_position: "leveraged_eth_staking"
      hedge_position: "eth_perp_short"
      stake_allocation: 0.5
      leverage_calculation: "target_ltv / (1 - target_ltv)"
      hedge_allocation: {"binance": 0.4, "bybit": 0.3, "okx": 0.3}
      dust_threshold: 0.01                    # 1% of equity
  
  execution_manager:
    supported_actions: ["etherfi_stake", "etherfi_unstake", "aave_supply", "aave_withdraw", "aave_borrow", "aave_repay", "cex_perp_short", "cex_perp_close", "cex_margin_add", "sell_dust", "flash_loan"]
    action_mapping:
      entry_full: ["etherfi_stake", "aave_supply", "aave_borrow", "cex_perp_short"]
      entry_partial: ["etherfi_stake", "aave_supply", "aave_borrow", "cex_perp_short"]
      exit_partial: ["cex_perp_close", "aave_repay", "aave_withdraw", "etherfi_unstake"]
      exit_full: ["cex_perp_close", "aave_repay", "aave_withdraw", "etherfi_unstake"]
      sell_dust: ["unwrap_king", "sell_dust"]
      add_leverage: ["flash_loan", "aave_borrow"]
      reduce_leverage: ["aave_repay"]
      rebalance_hedge: ["cex_perp_adjust"]
  
  results_store:
    result_types: ["balance_sheet", "pnl_attribution", "risk_metrics", "execution_log", "leverage_tracking", "delta_tracking", "funding_tracking", "dust_tracking"]
    balance_sheet_assets: ["ETH", "weETH", "aWeETH", "variableDebtWETH", "USDT", "ETH_PERP", "EIGEN", "KING"]
    pnl_attribution_types: ["supply_yield", "staking_yield_oracle", "staking_yield_rewards", "borrow_costs", "funding_pnl", "delta_pnl", "price_change_pnl", "transaction_costs"]
    leverage_tracking: true
    delta_tracking_assets: ["ETH"]
    funding_tracking_venues: ["binance", "bybit", "okx"]
    dust_tracking_tokens: ["EIGEN", "ETHFI", "KING"]
```

---

## **CONFIG SCHEMA REFERENCE TABLES**

### **Strategy Flags**
| Flag | Pure Lending | BTC Basis | ETH Basis | ETH Staking | ETH Leveraged | USDT MN No Lev | USDT MN |
|------|--------------|-----------|-----------|-------------|---------------|----------------|---------|
| `lending_enabled` | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| `staking_enabled` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `basis_trade_enabled` | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| `borrowing_enabled` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |

### **Risk Monitor Types by Mode**
| Risk Type | Pure Lending | BTC Basis | ETH Basis | ETH Staking | ETH Leveraged | USDT MN No Lev | USDT MN |
|-----------|--------------|-----------|-----------|-------------|---------------|----------------|---------|
| `ltv_risk` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| `liquidation_risk` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| `cex_margin_ratio` | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| `delta_risk` | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |

### **PnL Attribution Types by Mode**
| Attribution Type | Pure Lending | BTC Basis | ETH Basis | ETH Staking | ETH Leveraged | USDT MN No Lev | USDT MN |
|------------------|--------------|-----------|-----------|-------------|---------------|----------------|---------|
| `supply_yield` | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| `staking_yield_oracle` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `staking_yield_rewards` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `borrow_costs` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| `funding_pnl` | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| `delta_pnl` | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| `basis_pnl` | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `price_change_pnl` | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| `transaction_costs` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### **Conversion Methods by Asset**
| Asset | Conversion Method | Description |
|-------|-------------------|-------------|
| `USDT` | `direct` | 1:1 conversion (always $1) |
| `ETH` | `direct` | 1:1 for ETH share class, `usd_price` for USDT |
| `BTC` | `usd_price` | Convert via BTC/USD spot price |
| `weETH` | `oracle_price` | Convert via weETH/ETH oracle price |
| `wstETH` | `oracle_price` | Convert via wstETH/ETH oracle price |
| `aUSDT` | `aave_index` | Convert via AAVE liquidity index |
| `aWeETH` | `aave_index` | Convert via AAVE liquidity index |
| `variableDebtWETH` | `aave_index` | Convert via AAVE borrow index |
| `EIGEN` | `usd_price` | Convert via EIGEN/USD spot price |
| `KING` | `unwrap` | Unwrap to EIGEN + ETHFI, then convert |
| `BTC_SPOT` | `usd_price` | Spot position value |
| `BTC_PERP` | `perp_mark_price` | Perp mark price |
| `ETH_PERP` | `perp_mark_price` | Perp mark price |

### **Execution Actions by Mode**
| Action | Pure Lending | BTC Basis | ETH Basis | ETH Staking | ETH Leveraged | USDT MN No Lev | USDT MN |
|--------|--------------|-----------|-----------|-------------|---------------|----------------|---------|
| `entry_full` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `entry_partial` | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| `exit_partial` | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| `exit_full` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `sell_dust` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `add_leverage` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| `reduce_leverage` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| `rebalance_hedge` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

### **Data Requirements by Mode**
| Data Type | Pure Lending | BTC Basis | ETH Basis | ETH Staking | ETH Leveraged | USDT MN No Lev | USDT MN |
|-----------|--------------|-----------|-----------|-------------|---------------|----------------|---------|
| `usdt_prices` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `eth_prices` | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `btc_prices` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `btc_futures` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `eth_futures` | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ |
| `funding_rates` | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| `aave_lending_rates` | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| `aave_indexes` | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| `weeth_prices` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `staking_rewards` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `eigen_rewards` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `ethfi_rewards` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| `aave_risk_params` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| `lst_market_prices` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| `gas_costs` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `execution_costs` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### **Rebalancing Triggers by Mode**
| Trigger | Pure Lending | BTC Basis | ETH Basis | ETH Staking | ETH Leveraged | USDT MN No Lev | USDT MN |
|---------|--------------|-----------|-----------|-------------|---------------|----------------|---------|
| `deposit` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `withdrawal` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `delta_drift` | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| `funding_change` | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| `ltv_drift` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| `dust_threshold` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |

### **Result Types by Mode**
| Result Type | Pure Lending | BTC Basis | ETH Basis | ETH Staking | ETH Leveraged | USDT MN No Lev | USDT MN |
|-------------|--------------|-----------|-----------|-------------|---------------|----------------|---------|
| `balance_sheet` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `pnl_attribution` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `risk_metrics` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `execution_log` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `delta_tracking` | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| `funding_tracking` | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| `leverage_tracking` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| `dust_tracking` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |

---

## **COMPONENT BEHAVIOR PATTERNS**

### **Mode-Agnostic Components (Config-Driven)**

These components work identically across all modes, using config to determine behavior:

#### **1. Risk Monitor**
```python
# Mode-agnostic implementation
class RiskMonitor:
    def __init__(self, config: Dict, ...):
        # Extract config-driven settings
        self.enabled_risk_types = config['component_config']['risk_monitor']['enabled_risk_types']
        self.risk_limits = config['component_config']['risk_monitor']['risk_limits']
    
    def assess_risk(self, exposure_data: Dict, market_data: Dict) -> Dict:
        risk_metrics = {}
        
        # Only calculate enabled risk types
        for risk_type in self.enabled_risk_types:
            if risk_type == 'aave_health_factor':
                risk_metrics[risk_type] = self._calculate_health_factor(...)
            elif risk_type == 'cex_margin_ratio':
                risk_metrics[risk_type] = self._calculate_margin_ratio(...)
            # ... etc (NO mode-specific logic!)
        
        return risk_metrics
```

#### **2. Exposure Monitor**
```python
# Mode-agnostic implementation
class ExposureMonitor:
    def __init__(self, config: Dict, ...):
        # Extract config-driven settings
        self.exposure_currency = config['component_config']['exposure_monitor']['exposure_currency']
        self.track_assets = config['component_config']['exposure_monitor']['track_assets']
        self.conversion_methods = config['component_config']['exposure_monitor']['conversion_methods']
    
    def calculate_exposure(self, position_snapshot: Dict, market_data: Dict) -> Dict:
        asset_exposures = {}
        
        # Only track configured assets
        for asset in self.track_assets:
            method = self.conversion_methods[asset]
            asset_exposures[asset] = self._convert_asset(asset, method, ...)
        
        return asset_exposures  # (NO mode-specific logic!)
```

#### **3. PnL Calculator**
```python
# Mode-agnostic implementation
class PnLCalculator:
    def __init__(self, config: Dict, ...):
        # Extract config-driven settings
        self.attribution_types = config['component_config']['pnl_calculator']['attribution_types']
        self.reporting_currency = config['component_config']['pnl_calculator']['reporting_currency']
    
    def get_current_pnl(self, current_exposure: Dict, previous_exposure: Dict) -> Dict:
        attributions = {}
        
        # Only calculate enabled attribution types
        for attr_type in self.attribution_types:
            if attr_type == 'supply_yield':
                attributions[attr_type] = self._calc_supply_yield(...)
            elif attr_type == 'funding_pnl':
                attributions[attr_type] = self._calc_funding_pnl(...)
            # ... etc (NO mode-specific logic!)
        
        # Unused types return 0 (graceful handling)
        return attributions
```

#### **4. Position Monitor**
```python
# Mode-agnostic implementation
class PositionMonitor:
    def __init__(self, config: Dict, ...):
        # No mode-specific configuration needed
        self.execution_mode = execution_mode  # Only cares about backtest vs live
    
    def update_state(self, timestamp: pd.Timestamp, changes: Dict) -> Dict:
        if self.execution_mode == 'backtest':
            # Simulated position updates
            return self._update_simulated_positions(changes)
        else:
            # Real position refresh from exchanges
            return self._refresh_from_exchanges()
        
        # (NO strategy mode logic!)
```

#### **5. Reconciliation Component**
```python
# Mode-agnostic implementation
class ReconciliationComponent:
    def __init__(self, config: Dict, ...):
        # Simple tolerance setting
        self.reconciliation_tolerance = 0.01  # 1% tolerance for all modes
    
    def reconcile_position(self, expected: Dict, actual: Dict) -> Dict:
        # Same logic for all modes
        return self._compare_positions(expected, actual, self.reconciliation_tolerance)
```

### **Mode-Specific Components (Naturally Strategy-Specific)**

These components have mode-specific logic by nature:

#### **1. Strategy Manager**
```python
# Mode-specific implementation (using inheritance)
class BaseStrategyManager(ABC):
    def __init__(self, config: Dict, ...):
        self.strategy_config = config['component_config']['strategy_manager']
        self.strategy_type = self.strategy_config['strategy_type']
    
    @abstractmethod
    def calculate_target_positions(self, exposure: Dict, market_data: Dict) -> Dict:
        """Each strategy calculates positions differently"""
        pass

class PureLendingStrategyManager(BaseStrategyManager):
    def calculate_target_positions(self, exposure: Dict, market_data: Dict) -> Dict:
        # Pure lending specific logic
        return {'aave_usdt_supply': exposure['total_equity']}

class BTCBasisStrategyManager(BaseStrategyManager):
    def calculate_target_positions(self, exposure: Dict, market_data: Dict) -> Dict:
        # BTC basis specific logic
        equity = exposure['total_equity']
        hedge_allocation = self.strategy_config['position_calculation']['hedge_allocation']
        return {
            'btc_spot_long': equity / market_data['btc_price'],
            'btc_perp_shorts': {...}  # Distributed across venues
        }
```

#### **2. Execution Manager**
```python
# Mode-agnostic with config-driven action mapping
class ExecutionManager:
    def __init__(self, config: Dict, ...):
        self.execution_config = config['component_config']['execution_manager']
        self.supported_actions = self.execution_config['supported_actions']
        self.action_mapping = self.execution_config['action_mapping']
    
    def execute_action(self, action_type: str, params: Dict) -> Dict:
        # Config-driven action mapping
        action_sequence = self.action_mapping[action_type]
        
        for action in action_sequence:
            if action not in self.supported_actions:
                raise ValueError(f"Unsupported action: {action}")
            
            self._execute_venue_action(action, params)
```

#### **3. Results Store**
```python
# Mode-agnostic with config-driven result types
class ResultsStore:
    def __init__(self, config: Dict, ...):
        self.results_config = config['component_config']['results_store']
        self.result_types = self.results_config['result_types']
        self.balance_sheet_assets = self.results_config.get('balance_sheet_assets', [])
    
    def store_results(self, timestamp: pd.Timestamp, component_data: Dict) -> Dict:
        stored_results = {}
        
        # Only store configured result types
        for result_type in self.result_types:
            if result_type == 'balance_sheet':
                stored_results[result_type] = self._store_balance_sheet(...)
            elif result_type == 'delta_tracking':
                if result_type in self.result_types:  # Check if enabled
                    stored_results[result_type] = self._store_delta_tracking(...)
            # ... etc
        
        return stored_results
```

---

## **DATA PROVIDER ABSTRACTION LAYER**

### **Base DataProvider Interface**

All mode-specific data providers implement this standardized interface:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd

class BaseDataProvider(ABC):
    """Abstract base class for all data providers"""
    
    def __init__(self, execution_mode: str, config: Dict):
        self.execution_mode = execution_mode
        self.config = config
        self.available_data_types = []  # Set by subclasses
    
    @abstractmethod
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Return standardized data structure.
        
        ALL providers must return data in this exact format:
        {
            'market_data': {
                'prices': {...},
                'rates': {...}
            },
            'protocol_data': {
                'aave_indexes': {...},
                'oracle_prices': {...},
                'perp_prices': {...}
            }
        }
        """
        pass
    
    @abstractmethod
    def validate_data_requirements(self, data_requirements: List[str]) -> None:
        """
        Validate that this provider can satisfy all data requirements.
        Raises ValueError if any requirements cannot be met.
        """
        pass
    
    @abstractmethod
    def get_timestamps(self, start_date: str, end_date: str) -> List[pd.Timestamp]:
        """Get available timestamps for backtest period"""
        pass
```

### **Mode-Specific DataProvider Implementations**

#### **PureLendingDataProvider**
```python
class PureLendingDataProvider(BaseDataProvider):
    """Data provider for pure lending mode"""
    
    def __init__(self, execution_mode: str, config: Dict):
        super().__init__(execution_mode, config)
        self.available_data_types = [
            'usdt_prices',
            'aave_lending_rates',
            'aave_indexes',
            'gas_costs',
            'execution_costs'
        ]
    
    def validate_data_requirements(self, data_requirements: List[str]) -> None:
        missing = [req for req in data_requirements if req not in self.available_data_types]
        if missing:
            raise ValueError(f"PureLendingDataProvider cannot satisfy: {missing}")
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Return standardized data structure"""
        return {
            'market_data': {
                'prices': {
                    'USDT': 1.0,  # Always 1.0
                    'ETH': self._load_eth_price(timestamp)  # For gas calculations
                },
                'rates': {
                    'aave_usdt_supply': self._load_aave_usdt_rate(timestamp)
                }
            },
            'protocol_data': {
                'aave_indexes': {
                    'aUSDT': self._load_aave_usdt_index(timestamp)
                },
                'oracle_prices': {},  # Empty for this mode
                'perp_prices': {}     # Empty for this mode
            },
            'execution_data': {
                'gas_costs': self._load_gas_costs(timestamp),
                'execution_costs': self._load_execution_costs()
            }
        }
```

#### **BTCBasisDataProvider**
```python
class BTCBasisDataProvider(BaseDataProvider):
    """Data provider for BTC basis mode"""
    
    def __init__(self, execution_mode: str, config: Dict):
        super().__init__(execution_mode, config)
        self.available_data_types = [
            'btc_prices',
            'btc_futures',
            'funding_rates',
            'gas_costs',
            'execution_costs'
        ]
        self.hedge_venues = config.get('hedge_venues', ['binance', 'bybit', 'okx'])
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Return standardized data structure"""
        return {
            'market_data': {
                'prices': {
                    'BTC': self._load_btc_spot_price(timestamp),
                    'USDT': 1.0,
                    'ETH': self._load_eth_price(timestamp)  # For gas
                },
                'rates': {
                    f'funding_{venue}_btc': self._load_funding_rate(venue, 'BTC', timestamp)
                    for venue in self.hedge_venues
                }
            },
            'protocol_data': {
                'aave_indexes': {},  # Empty for this mode
                'oracle_prices': {},  # Empty for this mode
                'perp_prices': {
                    f'{venue}_btc_perp': self._load_perp_price(venue, 'BTC', timestamp)
                    for venue in self.hedge_venues
                }
            },
            'execution_data': {
                'gas_costs': self._load_gas_costs(timestamp),
                'execution_costs': self._load_execution_costs()
            }
        }
```

#### **USDTMarketNeutralDataProvider**
```python
class USDTMarketNeutralDataProvider(BaseDataProvider):
    """Data provider for USDT market neutral mode (MOST COMPLEX)"""
    
    def __init__(self, execution_mode: str, config: Dict):
        super().__init__(execution_mode, config)
        self.available_data_types = [
            'eth_prices',
            'weeth_prices',
            'eth_futures',
            'funding_rates',
            'aave_lending_rates',
            'aave_indexes',
            'staking_rewards',
            'eigen_rewards',
            'ethfi_rewards',
            'aave_risk_params',
            'lst_market_prices',
            'gas_costs',
            'execution_costs'
        ]
        self.hedge_venues = config.get('hedge_venues', ['binance', 'bybit', 'okx'])
        self.lst_type = config.get('lst_type', 'weeth')
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Return standardized data structure with ALL data types"""
        return {
            'market_data': {
                'prices': {
                    'ETH': self._load_eth_spot_price(timestamp),
                    'USDT': 1.0,
                    'EIGEN': self._load_eigen_price(timestamp),
                    'ETHFI': self._load_ethfi_price(timestamp)
                },
                'rates': {
                    f'funding_{venue}_eth': self._load_funding_rate(venue, 'ETH', timestamp)
                    for venue in self.hedge_venues
                } | {
                    'aave_weeth_supply': self._load_aave_supply_rate(self.lst_type, timestamp),
                    'aave_weth_borrow': self._load_aave_borrow_rate('WETH', timestamp)
                }
            },
            'protocol_data': {
                'aave_indexes': {
                    f'a{self.lst_type.upper()}': self._load_aave_index(self.lst_type, 'supply', timestamp),
                    'variableDebtWETH': self._load_aave_index('WETH', 'borrow', timestamp)
                },
                'oracle_prices': {
                    self.lst_type: self._load_oracle_price(self.lst_type, timestamp)
                },
                'perp_prices': {
                    f'{venue}_eth_perp': self._load_perp_price(venue, 'ETH', timestamp)
                    for venue in self.hedge_venues
                },
                'aave_risk_params': self._load_aave_risk_params(),
                'lst_market_prices': {
                    f'{self.lst_type}_curve': self._load_curve_price(self.lst_type, timestamp),
                    f'{self.lst_type}_uniswap': self._load_uniswap_price(self.lst_type, timestamp)
                }
            },
            'staking_data': {
                'base_rewards': self._load_base_staking_rewards(self.lst_type, timestamp),
                'eigen_rewards': self._load_eigen_rewards(timestamp),
                'ethfi_rewards': self._load_ethfi_rewards(timestamp)
            },
            'execution_data': {
                'gas_costs': self._load_gas_costs(timestamp),
                'execution_costs': self._load_execution_costs()
            }
        }
```

### **DataProvider Factory**

```python
class DataProviderFactory:
    """Factory for creating mode-specific data providers"""
    
    @staticmethod
    def create(execution_mode: str, config: Dict) -> BaseDataProvider:
        """
        Create mode-specific data provider based on mode.
        Validates that provider can satisfy all data_requirements.
        """
        mode = config['mode']
        data_requirements = config.get('data_requirements', [])
        
        # Create mode-specific provider
        provider_map = {
            'pure_lending': PureLendingDataProvider,
            'btc_basis': BTCBasisDataProvider,
            'eth_basis': ETHBasisDataProvider,
            'eth_staking_only': ETHStakingOnlyDataProvider,
            'eth_leveraged': ETHLeveragedDataProvider,
            'usdt_market_neutral_no_leverage': USDTMarketNeutralNoLeverageDataProvider,
            'usdt_market_neutral': USDTMarketNeutralDataProvider
        }
        
        if mode not in provider_map:
            raise ValueError(f"Unknown strategy mode: {mode}")
        
        provider = provider_map[mode](execution_mode, config)
        
        # Validate that provider can satisfy all data requirements
        provider.validate_data_requirements(data_requirements)
        
        return provider
```

---

## **STANDARDIZED DATA STRUCTURES**

All data providers return data in these standardized structures:

### **Market Data Structure**
```python
'market_data': {
    'prices': {
        'USDT': float,        # Always 1.0
        'ETH': float,         # ETH/USDT spot price
        'BTC': float,         # BTC/USDT spot price
        'EIGEN': float,       # EIGEN/USDT spot price
        'ETHFI': float        # ETHFI/USDT spot price
    },
    'rates': {
        'aave_usdt_supply': float,              # AAVE USDT supply rate (APR)
        'aave_weeth_supply': float,             # AAVE weETH supply rate (APR)
        'aave_weth_borrow': float,              # AAVE WETH borrow rate (APR)
        'funding_binance_btc': float,           # Binance BTC funding rate
        'funding_bybit_btc': float,             # Bybit BTC funding rate
        'funding_okx_btc': float,               # OKX BTC funding rate
        'funding_binance_eth': float,           # Binance ETH funding rate
        'funding_bybit_eth': float,             # Bybit ETH funding rate
        'funding_okx_eth': float                # OKX ETH funding rate
    }
}
```

### **Protocol Data Structure**
```python
'protocol_data': {
    'aave_indexes': {
        'aUSDT': float,                         # AAVE USDT liquidity index
        'aWeETH': float,                        # AAVE weETH liquidity index
        'aWstETH': float,                       # AAVE wstETH liquidity index
        'variableDebtWETH': float               # AAVE WETH borrow index
    },
    'oracle_prices': {
        'weeth': float,                         # weETH/ETH oracle price
        'wsteth': float                         # wstETH/ETH oracle price
    },
    'perp_prices': {
        'binance_btc_perp': float,              # Binance BTC perp mark price
        'bybit_btc_perp': float,                # Bybit BTC perp mark price
        'okx_btc_perp': float,                  # OKX BTC perp mark price
        'binance_eth_perp': float,              # Binance ETH perp mark price
        'bybit_eth_perp': float,                # Bybit ETH perp mark price
        'okx_eth_perp': float                   # OKX ETH perp mark price
    },
    'aave_risk_params': {
        'weeth': {
            'max_ltv': float,                   # E.g., 0.93 for E-mode
            'liquidation_threshold': float,     # E.g., 0.95 for E-mode
            'liquidation_bonus': float          # E.g., 0.01 for E-mode
        }
    },
    'lst_market_prices': {
        'weeth_curve': float,                   # weETH/ETH Curve price
        'weeth_uniswap': float,                 # weETH/ETH Uniswap price
        'wsteth_curve': float,                  # wstETH/ETH Curve price
        'wsteth_uniswap': float                 # wstETH/ETH Uniswap price
    }
}
```

### **Staking Data Structure**
```python
'staking_data': {
    'base_rewards': {
        'weeth': float,                         # weETH base staking APR
        'wsteth': float                         # wstETH base staking APR
    },
    'eigen_rewards': {
        'weeth': float,                         # EIGEN rewards APR for weETH
        'distribution_schedule': [...]          # Weekly distribution amounts
    },
    'ethfi_rewards': {
        'weeth': float,                         # ETHFI rewards APR for weETH
        'airdrop_schedule': [...]               # Airdrop events
    }
}
```

### **Execution Data Structure**
```python
'execution_data': {
    'gas_costs': {
        'base_fee': float,                      # Ethereum base fee (gwei)
        'priority_fee': float,                  # Priority fee (gwei)
        'total_gas_price': float                # Total gas price (gwei)
    },
    'execution_costs': {
        'aave_supply': float,                   # Gas cost for AAVE supply
        'aave_withdraw': float,                 # Gas cost for AAVE withdraw
        'etherfi_stake': float,                 # Gas cost for EtherFi stake
        'cex_spot_buy': float,                  # Fee for CEX spot buy
        'cex_perp_short': float                 # Fee for CEX perp short
    }
}
```

---

## **MODE-AGNOSTIC COMPONENT USAGE EXAMPLES**

### **Example 1: Risk Monitor (Mode-Agnostic)**

```python
# Pure Lending Mode
config = {
    'component_config': {
        'risk_monitor': {
            'enabled_risk_types': ['protocol_risk'],
            'risk_limits': {'protocol_risk_max': 0.01}
        }
    }
}

risk_monitor = RiskMonitor(config, data_provider, 'backtest')
risk_metrics = risk_monitor.assess_risk(exposure_data, market_data)
# Returns: {'protocol_risk': 0.005}  (only enabled type)

# USDT Market Neutral Mode
config = {
    'component_config': {
        'risk_monitor': {
            'enabled_risk_types': ['aave_health_factor', 'cex_margin_ratio', 'funding_risk', 'delta_risk'],
            'risk_limits': {
                'aave_health_factor_min': 1.1,
                'cex_margin_ratio_min': 0.2,
                'funding_risk_max': 0.05,
                'delta_risk_max': 0.01
            }
        }
    }
}

risk_monitor = RiskMonitor(config, data_provider, 'backtest')
risk_metrics = risk_monitor.assess_risk(exposure_data, market_data)
# Returns: {
#     'aave_health_factor': 1.5,
#     'cex_margin_ratio': 0.45,
#     'funding_risk': 0.03,
#     'delta_risk': 0.005
# }
```

### **Example 2: Exposure Monitor (Mode-Agnostic)**

```python
# Pure Lending Mode
config = {
    'component_config': {
        'exposure_monitor': {
            'exposure_currency': 'USDT',
            'track_assets': ['USDT', 'aUSDT', 'ETH'],
            'conversion_methods': {
                'USDT': 'direct',
                'aUSDT': 'aave_index',
                'ETH': 'usd_price'
            }
        }
    }
}

exposure_monitor = ExposureMonitor(config, data_provider, 'backtest')
exposure = exposure_monitor.calculate_exposure(timestamp, position_snapshot, market_data)
# Returns exposure for USDT, aUSDT, ETH only

# USDT Market Neutral Mode
config = {
    'component_config': {
        'exposure_monitor': {
            'exposure_currency': 'USDT',
            'track_assets': ['ETH', 'weETH', 'aWeETH', 'variableDebtWETH', 'USDT', 'ETH_PERP', 'EIGEN', 'KING'],
            'conversion_methods': {
                'ETH': 'usd_price',
                'weETH': 'oracle_price',
                'aWeETH': 'aave_index',
                'variableDebtWETH': 'aave_index',
                'USDT': 'direct',
                'ETH_PERP': 'perp_mark_price',
                'EIGEN': 'usd_price',
                'KING': 'unwrap'
            }
        }
    }
}

exposure_monitor = ExposureMonitor(config, data_provider, 'backtest')
exposure = exposure_monitor.calculate_exposure(timestamp, position_snapshot, market_data)
# Returns exposure for all 8 tracked assets
```

### **Example 3: PnL Calculator (Mode-Agnostic)**

```python
# Pure Lending Mode
config = {
    'component_config': {
        'pnl_calculator': {
            'attribution_types': ['supply_yield', 'transaction_costs'],
            'reporting_currency': 'USDT',
            'reconciliation_tolerance': 0.02
        }
    }
}

pnl_calculator = PnLCalculator(config, data_provider, 'backtest')
pnl_data = pnl_calculator.get_current_pnl(current_exposure, previous_exposure, timestamp, period_start)
# Returns: {
#     'attribution': {
#         'supply_yield': 45.23,
#         'transaction_costs': -2.15,
#         'funding_pnl': 0.0,  # Not in attribution_types, returns 0
#         'delta_pnl': 0.0      # Not in attribution_types, returns 0
#     }
# }

# USDT Market Neutral Mode
config = {
    'component_config': {
        'pnl_calculator': {
            'attribution_types': ['supply_yield', 'staking_yield_oracle', 'staking_yield_rewards', 
                                 'borrow_costs', 'funding_pnl', 'delta_pnl', 'price_change_pnl', 'transaction_costs'],
            'reporting_currency': 'USDT',
            'reconciliation_tolerance': 0.02
        }
    }
}

pnl_calculator = PnLCalculator(config, data_provider, 'backtest')
pnl_data = pnl_calculator.get_current_pnl(current_exposure, previous_exposure, timestamp, period_start)
# Returns: {
#     'attribution': {
#         'supply_yield': 125.34,
#         'staking_yield_oracle': 89.12,
#         'staking_yield_rewards': 34.56,
#         'borrow_costs': -78.90,
#         'funding_pnl': 45.67,
#         'delta_pnl': -2.34,
#         'price_change_pnl': 156.78,
#         'transaction_costs': -12.45
#     }
# }
```

---

## **CONFIG-DRIVEN VALIDATION**

### **Pydantic Schema Validation**

Complete Pydantic models for config-driven architecture:

```python
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Union
from enum import Enum

class ShareClass(str, Enum):
    """Share class enumeration"""
    USDT = "USDT"
    ETH = "ETH"

class AssetType(str, Enum):
    """Asset type enumeration"""
    USDT = "USDT"
    ETH = "ETH"
    BTC = "BTC"

class LSTType(str, Enum):
    """LST type enumeration"""
    WEETH = "weeth"
    WSTETH = "wsteth"

class RewardsMode(str, Enum):
    """Rewards mode enumeration"""
    BASE_ONLY = "base_only"
    BASE_EIGEN = "base_eigen"
    BASE_EIGEN_SEASONAL = "base_eigen_seasonal"

class ConversionMethod(str, Enum):
    """Conversion method enumeration"""
    DIRECT = "direct"
    USD_PRICE = "usd_price"
    ETH_PRICE = "eth_price"
    ORACLE_PRICE = "oracle_price"
    AAVE_INDEX = "aave_index"
    PERP_MARK_PRICE = "perp_mark_price"
    UNWRAP = "unwrap"

# ============================================================================
# COMPONENT CONFIG MODELS
# ============================================================================

class RiskMonitorConfig(BaseModel):
    """Risk monitor component configuration"""
    enabled_risk_types: List[str] = Field(..., description="List of risk types to calculate")
    risk_limits: Dict[str, float] = Field(..., description="Risk limits for each risk type")
    
    @validator('enabled_risk_types')
    def validate_risk_types(cls, v):
        valid_types = [
            'protocol_risk', 'aave_health_factor', 'liquidation_risk', 'ltv_risk',
            'cex_margin_ratio', 'funding_risk', 'basis_risk', 'delta_risk'
        ]
        for risk_type in v:
            if risk_type not in valid_types:
                raise ValueError(f"Invalid risk type: {risk_type}")
        return v

class ExposureMonitorConfig(BaseModel):
    """Exposure monitor component configuration"""
    exposure_currency: ShareClass = Field(..., description="Currency for exposure calculations")
    track_assets: List[str] = Field(..., description="Assets to track for exposure")
    conversion_methods: Dict[str, str] = Field(..., description="Conversion method for each asset")
    
    @validator('track_assets')
    def validate_track_assets(cls, v):
        if not v:
            raise ValueError("track_assets cannot be empty")
        return v
    
    @validator('conversion_methods')
    def validate_conversion_methods(cls, v, values):
        track_assets = values.get('track_assets', [])
        for asset in track_assets:
            if asset not in v:
                raise ValueError(f"Missing conversion method for asset: {asset}")
        
        valid_methods = ['direct', 'usd_price', 'eth_price', 'oracle_price', 'aave_index', 'perp_mark_price', 'unwrap']
        for asset, method in v.items():
            if method not in valid_methods:
                raise ValueError(f"Invalid conversion method for {asset}: {method}")
        return v

class PnLCalculatorConfig(BaseModel):
    """PnL calculator component configuration"""
    attribution_types: List[str] = Field(..., description="List of attribution types to calculate")
    reporting_currency: ShareClass = Field(..., description="Currency for PnL reporting")
    reconciliation_tolerance: float = Field(..., ge=0, le=1, description="Tolerance for PnL reconciliation")
    
    @validator('attribution_types')
    def validate_attribution_types(cls, v):
        valid_types = [
            'supply_yield', 'staking_yield_oracle', 'staking_yield_rewards', 'borrow_costs',
            'funding_pnl', 'delta_pnl', 'basis_pnl', 'price_change_pnl', 'transaction_costs'
        ]
        for attr_type in v:
            if attr_type not in valid_types:
                raise ValueError(f"Invalid attribution type: {attr_type}")
        return v

class PositionCalculationConfig(BaseModel):
    """Position calculation configuration"""
    target_position: str = Field(..., description="Target position calculation method")
    max_position: Optional[str] = Field(None, description="Maximum position limit")
    hedge_position: Optional[str] = Field(None, description="Hedge position type")
    leverage_calculation: Optional[str] = Field(None, description="Leverage calculation formula")
    stake_allocation: Optional[float] = Field(None, ge=0, le=1, description="Stake allocation")
    hedge_allocation: Optional[Dict[str, float]] = Field(None, description="Hedge allocation per venue")
    dust_threshold: Optional[float] = Field(None, ge=0, le=1, description="Dust threshold")

class StrategyManagerConfig(BaseModel):
    """Strategy manager component configuration"""
    strategy_type: str = Field(..., description="Strategy type name")
    actions: List[str] = Field(..., description="Available strategy actions")
    rebalancing_triggers: List[str] = Field(..., description="Triggers for rebalancing")
    position_calculation: PositionCalculationConfig = Field(..., description="Position calculation config")
    
    @validator('actions')
    def validate_actions(cls, v):
        valid_actions = [
            'entry_full', 'entry_partial', 'exit_partial', 'exit_full',
            'sell_dust', 'add_leverage', 'reduce_leverage', 'rebalance_hedge'
        ]
        for action in v:
            if action not in valid_actions:
                raise ValueError(f"Invalid action: {action}")
        return v
    
    @validator('rebalancing_triggers')
    def validate_triggers(cls, v):
        valid_triggers = [
            'deposit', 'withdrawal', 'delta_drift', 'funding_change', 
            'ltv_drift', 'dust_threshold'
        ]
        for trigger in v:
            if trigger not in valid_triggers:
                raise ValueError(f"Invalid rebalancing trigger: {trigger}")
        return v

class ExecutionManagerConfig(BaseModel):
    """Execution manager component configuration"""
    supported_actions: List[str] = Field(..., description="Supported execution actions")
    action_mapping: Dict[str, List[str]] = Field(..., description="Mapping of strategy actions to execution actions")
    
    @validator('action_mapping')
    def validate_action_mapping(cls, v, values):
        supported_actions = values.get('supported_actions', [])
        for strategy_action, execution_actions in v.items():
            for exec_action in execution_actions:
                if exec_action not in supported_actions:
                    raise ValueError(f"Action mapping references unsupported action: {exec_action}")
        return v

class ResultsStoreConfig(BaseModel):
    """Results store component configuration"""
    result_types: List[str] = Field(..., description="Result types to store")
    balance_sheet_assets: List[str] = Field(..., description="Assets to include in balance sheet")
    pnl_attribution_types: List[str] = Field(..., description="PnL attribution types to store")
    delta_tracking_assets: Optional[List[str]] = Field(None, description="Assets for delta tracking")
    funding_tracking_venues: Optional[List[str]] = Field(None, description="Venues for funding tracking")
    leverage_tracking: Optional[bool] = Field(False, description="Enable leverage tracking")
    dust_tracking_tokens: Optional[List[str]] = Field(None, description="Tokens for dust tracking")
    
    @validator('result_types')
    def validate_result_types(cls, v):
        valid_types = [
            'balance_sheet', 'pnl_attribution', 'risk_metrics', 'execution_log',
            'delta_tracking', 'funding_tracking', 'leverage_tracking', 'dust_tracking'
        ]
        for result_type in v:
            if result_type not in valid_types:
                raise ValueError(f"Invalid result type: {result_type}")
        return v

class ComponentConfigModel(BaseModel):
    """Complete component configuration model"""
    risk_monitor: RiskMonitorConfig
    exposure_monitor: ExposureMonitorConfig
    pnl_calculator: PnLCalculatorConfig
    strategy_manager: StrategyManagerConfig
    execution_manager: ExecutionManagerConfig
    results_store: ResultsStoreConfig

# ============================================================================
# MODE CONFIG MODEL
# ============================================================================

class ModeConfigModel(BaseModel):
    """Complete mode configuration model"""
    
    # Strategy identification
    mode: str = Field(..., description="Strategy mode name")
    share_class: ShareClass = Field(..., description="Share class currency")
    asset: AssetType = Field(..., description="Primary asset")
    
    # Strategy flags
    lending_enabled: bool = Field(..., description="Enable AAVE lending")
    staking_enabled: bool = Field(..., description="Enable LST staking")
    basis_trade_enabled: bool = Field(..., description="Enable basis trading")
    borrowing_enabled: bool = Field(..., description="Enable AAVE borrowing")
    enable_market_impact: bool = Field(..., description="Enable market impact modeling")
    
    # Asset configuration
    lst_type: Optional[LSTType] = Field(None, description="LST type")
    rewards_mode: RewardsMode = Field(..., description="Rewards calculation mode")
    position_deviation_threshold: float = Field(..., ge=0, le=1, description="Position deviation threshold")
    stake_allocation_eth: Optional[float] = Field(None, ge=0, le=1, description="Stake allocation (USDT MN modes)")
    
    # Hedging configuration
    hedge_venues: List[str] = Field(default_factory=list, description="CEX venues for hedging")
    hedge_allocation_binance: float = Field(0.0, ge=0, le=1, description="Binance allocation")
    hedge_allocation_bybit: float = Field(0.0, ge=0, le=1, description="Bybit allocation")
    hedge_allocation_okx: float = Field(0.0, ge=0, le=1, description="OKX allocation")
    
    # Risk parameters
    margin_ratio_target: float = Field(..., ge=0, le=1, description="Target CEX margin ratio")
    max_stake_spread_move: float = Field(0.0, ge=0, le=1, description="Max LST/ETH oracle move")
    max_ltv: float = Field(0.0, ge=0, le=1, description="Maximum LTV")
    liquidation_threshold: float = Field(0.0, ge=0, le=1, description="Liquidation threshold")
    delta_tolerance: float = Field(0.0, ge=0, le=1, description="Delta tolerance")
    
    # Performance targets
    target_apy: float = Field(..., ge=0, description="Target APY")
    max_drawdown: float = Field(..., ge=0, le=1, description="Maximum drawdown")
    
    # Execution parameters
    time_throttle_interval: int = Field(..., ge=1, description="Time between actions (seconds)")
    
    # Data requirements
    data_requirements: List[str] = Field(..., description="Required data types")
    
    # Component configuration
    component_config: ComponentConfigModel = Field(..., description="Component behavior configuration")
    
    @validator('hedge_allocation_binance', 'hedge_allocation_bybit', 'hedge_allocation_okx')
    def validate_hedge_allocation_sum(cls, v, values):
        """Validate that hedge allocations sum to 1.0 when hedging is enabled"""
        if values.get('basis_trade_enabled', False):
            total = (
                values.get('hedge_allocation_binance', 0.0) +
                values.get('hedge_allocation_bybit', 0.0) +
                v  # Current field value
            )
            if not (0.99 <= total <= 1.01):  # Allow small floating point errors
                raise ValueError(f"Hedge allocations must sum to 1.0, got {total}")
        return v
    
    @validator('lst_type')
    def validate_lst_type_when_staking(cls, v, values):
        """Validate that lst_type is set when staking is enabled"""
        if values.get('staking_enabled', False) and v is None:
            raise ValueError("lst_type must be set when staking_enabled is true")
        return v
    
    @validator('stake_allocation_eth')
    def validate_stake_allocation(cls, v, values):
        """Validate stake_allocation_eth for USDT MN modes"""
        if values.get('share_class') == ShareClass.USDT and values.get('staking_enabled', False):
            if v is None:
                raise ValueError("stake_allocation_eth must be set for USDT share class with staking")
        return v
    
    @validator('data_requirements')
    def validate_data_requirements(cls, v):
        """Validate that data requirements are not empty"""
        if not v:
            raise ValueError("data_requirements cannot be empty")
        return v

# ============================================================================
# CONFIG VALIDATION FUNCTIONS
# ============================================================================

class ConfigValidator:
    """Validates config completeness and consistency"""
    
    @staticmethod
    def validate_mode_config(config: Dict) -> List[str]:
        """
        Validate that config has all required fields for the mode.
        Returns list of error messages (empty if valid).
        """
        errors = []
        
        try:
            # Validate using Pydantic model
            ModeConfigModel(**config)
        except Exception as e:
            errors.append(f"Pydantic validation failed: {str(e)}")
        
        # Additional business logic validation
        errors.extend(ConfigValidator._validate_business_logic(config))
        
        return errors
    
    @staticmethod
def _validate_business_logic(config: Dict) -> List[str]:
    """Validate business logic constraints (private method)"""
        errors = []
        
        # Validate share_class vs asset consistency
        if config['share_class'] != config['asset']:
            # Cross-currency modes must have hedging
            if not config.get('basis_trade_enabled', False):
                errors.append(f"Mode with share_class={config['share_class']} and asset={config['asset']} must have basis_trade_enabled=true")
        
        # Validate leverage requires borrowing
        if config.get('max_ltv', 0) > 0 and not config.get('borrowing_enabled', False):
            errors.append("max_ltv > 0 requires borrowing_enabled=true")
        
        # Validate staking requires lst_type
        if config.get('staking_enabled', False) and not config.get('lst_type'):
            errors.append("staking_enabled=true requires lst_type")
        
        # Validate hedge allocation sums to 1.0
        if config.get('basis_trade_enabled', False):
            total_allocation = (
                config.get('hedge_allocation_binance', 0.0) +
                config.get('hedge_allocation_bybit', 0.0) +
                config.get('hedge_allocation_okx', 0.0)
            )
            if not (0.99 <= total_allocation <= 1.01):
                errors.append(f"Hedge allocations must sum to 1.0, got {total_allocation}")
        
        return errors
    
    @staticmethod
    def validate_component_config(component_name: str, component_config: Dict) -> List[str]:
        """Validate component-specific config"""
        errors = []
        
        if component_name == 'risk_monitor':
            if 'enabled_risk_types' not in component_config:
                errors.append("risk_monitor missing enabled_risk_types")
            if 'risk_limits' not in component_config:
                errors.append("risk_monitor missing risk_limits")
        
        elif component_name == 'exposure_monitor':
            if 'exposure_currency' not in component_config:
                errors.append("exposure_monitor missing exposure_currency")
            if 'track_assets' not in component_config:
                errors.append("exposure_monitor missing track_assets")
            if 'conversion_methods' not in component_config:
                errors.append("exposure_monitor missing conversion_methods")
            else:
                # Validate all tracked assets have conversion methods
                track_assets = component_config.get('track_assets', [])
                conversion_methods = component_config['conversion_methods']
                for asset in track_assets:
                    if asset not in conversion_methods:
                        errors.append(f"exposure_monitor missing conversion method for asset: {asset}")
        
        elif component_name == 'pnl_calculator':
            if 'attribution_types' not in component_config:
                errors.append("pnl_calculator missing attribution_types")
            if 'reporting_currency' not in component_config:
                errors.append("pnl_calculator missing reporting_currency")
            if 'reconciliation_tolerance' not in component_config:
                errors.append("pnl_calculator missing reconciliation_tolerance")
        
        elif component_name == 'strategy_manager':
            if 'strategy_type' not in component_config:
                errors.append("strategy_manager missing strategy_type")
            if 'actions' not in component_config:
                errors.append("strategy_manager missing actions")
            if 'rebalancing_triggers' not in component_config:
                errors.append("strategy_manager missing rebalancing_triggers")
        
        elif component_name == 'execution_manager':
            if 'supported_actions' not in component_config:
                errors.append("execution_manager missing supported_actions")
            if 'action_mapping' not in component_config:
                errors.append("execution_manager missing action_mapping")
        
        elif component_name == 'results_store':
            if 'result_types' not in component_config:
                errors.append("results_store missing result_types")
            if 'balance_sheet_assets' not in component_config:
                errors.append("results_store missing balance_sheet_assets")
            if 'pnl_attribution_types' not in component_config:
                errors.append("results_store missing pnl_attribution_types")
        
        return errors
    
    @staticmethod
    def validate_data_provider_compatibility(config: Dict, provider: 'BaseDataProvider') -> List[str]:
        """Validate that data provider can satisfy config requirements"""
        errors = []
        
        data_requirements = config.get('data_requirements', [])
        
        try:
            provider.validate_data_requirements(data_requirements)
        except ValueError as e:
            errors.append(f"DataProvider validation failed: {str(e)}")
        
        return errors

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

# Example: Validate pure lending config
pure_lending_config = {
    'mode': 'pure_lending',
    'share_class': 'USDT',
    'asset': 'USDT',
    'data_requirements': ['usdt_prices', 'aave_lending_rates'],
    'component_config': {...}
}

errors = ConfigValidator.validate_mode_config(pure_lending_config)
if errors:
    print(f"Validation failed: {errors}")
else:
    print("Config is valid!")

# Example: Create data provider with validation
data_provider = DataProviderFactory.create('backtest', pure_lending_config)
# Automatically validates data_requirements against provider capabilities
```

---

## **CONFIG LOADING AND INITIALIZATION FLOW**

### **Complete Initialization Sequence**

```python
class BacktestService:
    """Backtest service using config-driven architecture"""
    
    async def run_backtest(self, request: BacktestRequest) -> str:
        """
        Complete config-driven initialization flow:
        
        1. Load strategy config
        2. Apply overrides
        3. Validate config
        4. Create data provider (validates data requirements)
        5. Create components (validates component config)
        6. Run backtest
        """
        
        # Step 1: Load config for strategy mode
        config = self._load_strategy_config(request.mode)
        
        # Step 2: Apply config overrides (if any)
        if request.config_overrides:
            config = self._apply_config_overrides(config, request.config_overrides)
        
        # Step 3: Validate complete config
        errors = ConfigValidator.validate_mode_config(config)
        if errors:
            raise ValueError(f"Config validation failed: {errors}")
        
        # Step 4: Create data provider (validates data requirements)
        data_provider = DataProviderFactory.create('backtest', config)
        
        # Step 5: Validate data provider compatibility
        provider_errors = ConfigValidator.validate_data_provider_compatibility(config, data_provider)
        if provider_errors:
            raise ValueError(f"DataProvider validation failed: {provider_errors}")
        
        # Step 6: Create components (validates component config)
        components = ComponentFactory.create_all(config, data_provider, 'backtest')
        
        # Step 7: Create event engine and run backtest
        engine = EventDrivenStrategyEngine(config, 'backtest', data_provider, components)
        results = await engine.run_backtest(request.start_date, request.end_date)
        
        return results
```

---

## **CONFIG OVERRIDE SUPPORT**

### **Override Structure**

Config overrides allow runtime customization without modifying YAML files:

```python
# Example: Override risk limits for a specific backtest
config_overrides = {
    'component_config': {
        'risk_monitor': {
            'risk_limits': {
                'aave_health_factor_min': 1.2  # More conservative than default 1.1
            }
        },
        'pnl_calculator': {
            'reconciliation_tolerance': 0.01  # Stricter than default 0.02
        }
    },
    'target_apy': 0.12  # Override target APY
}

# Apply overrides
final_config = apply_config_overrides(base_config, config_overrides)
```

### **Override Validation**

```python
def apply_config_overrides(base_config: Dict, overrides: Dict) -> Dict:
    """
    Apply config overrides with validation.
    Deep merges overrides into base config.
    """
    # Deep merge
    merged_config = deep_merge(base_config.copy(), overrides)
    
    # Validate merged config
    errors = ConfigValidator.validate_mode_config(merged_config)
    if errors:
        raise ValueError(f"Config with overrides is invalid: {errors}")
    
    return merged_config
```

---

## **BENEFITS OF CONFIG-DRIVEN ARCHITECTURE**

### **1. True Mode-Agnostic Components**
- Components have **zero hardcoded mode logic**
- Behavior is **100% driven by config**
- Easy to add new modes without changing component code
- Same component class works for all 7 strategy modes

### **2. Explicit Data Requirements**
- Each mode **declares exactly what data it needs**
- Data providers **validate they can satisfy requirements**
- Clear contract between modes and data providers
- Fail-fast validation catches issues early

### **3. Config-Driven Behavior**
- Component behavior is **configurable per mode**
- Risk limits, attribution types, tracked assets all configurable
- Easy to tune behavior without code changes
- Override support for ad-hoc testing

### **4. Validation and Safety**
- **Pydantic validation** ensures type safety
- **Business logic validation** ensures consistency
- **Data provider validation** ensures data availability
- **Fail-fast approach** catches issues at startup

### **5. Maintainability**
- Clear separation between **data requirements** and **component behavior**
- Easy to understand what each mode needs
- Simple to add new modes or modify existing ones
- Self-documenting configuration structure

---

## **MIGRATION FROM CURRENT ARCHITECTURE**

### **Current State**
Currently, components have mode-specific logic scattered throughout:

```python
# ❌ CURRENT: Mode-specific logic in components
class RiskMonitor:
    def assess_risk(self, exposure_data, market_data):
        if self.mode == 'pure_lending':
            return self._check_aave_risk(...)
        elif self.mode == 'btc_basis':
            return self._check_cex_risk(...)
        # ... mode-specific logic
```

### **Target State**
Components should be config-driven:

```python
# ✅ TARGET: Config-driven behavior
class RiskMonitor:
    def assess_risk(self, exposure_data, market_data):
        risk_metrics = {}
        
        for risk_type in self.enabled_risk_types:  # From config!
            if risk_type == 'aave_health_factor':
                risk_metrics[risk_type] = self._calculate_health_factor(...)
            # ... etc (NO mode logic!)
        
        return risk_metrics
```

### **Migration Steps**

#### **Phase 1: Add component_config to YAML Files**
Update all 7 mode YAML files to include `component_config` section.

#### **Phase 2: Create DataProvider Abstraction**
- Create `BaseDataProvider` abstract class
- Implement 7 mode-specific data providers
- Update `BaseDataProviderFactory`

#### **Phase 3: Update Component Initialization**
- Update components to read `component_config`
- Add validation for required config fields
- Store config-driven settings in `__init__`

#### **Phase 4: Remove Mode-Specific Logic**
- Remove all mode-specific if/else statements
- Replace with config-driven loops
- Add graceful handling for missing data

#### **Phase 5: Update Tests**
- Update all tests to use config-driven approach
- Add config validation tests
- Test with different mode configurations

---

## **SUMMARY**

The config-driven architecture provides:

1. **Complete separation** between data requirements and component behavior
2. **Mode-agnostic components** that work identically across all modes
3. **Standardized data interfaces** that enable consistent component behavior
4. **Comprehensive validation** that catches issues early
5. **Easy extensibility** for adding new modes or modifying existing ones

This architecture **completely resolves** the tension between mode-agnostic components and mode-specific data subscriptions by using configuration as the bridge between them.

---

### Migration Strategy

#### 1. Phase 1: Documentation and Configuration
- Update all documentation to reflect config-driven approach
- Create new configuration structure for all 7 modes
- Add Pydantic validation schemas

#### 2. Phase 2: DataProvider Abstraction
- Create BaseDataProvider abstract class
- Implement 7 mode-specific data providers
- Update DataProviderFactory

#### 3. Phase 3: Component Refactor
- Refactor Risk, Exposure, PnL monitors to be config-driven
- Remove mode-specific if statements
- Add graceful handling for missing data

#### 4. Phase 4: Service Layer Updates
- Update services to use factory pattern
- Add config override handling
- Update API endpoints

#### 5. Phase 5: Testing and Validation
- Update all tests for config-driven behavior
- Add config validation tests
- Update quality gates

### Data Requirements Validation

Each mode specifies its data requirements:

```yaml
data_requirements:
  - "btc_spot_prices"
  - "btc_futures_prices"
  - "btc_funding_rates"
  - "eth_usd_prices"
```

The DataProvider validates that it can satisfy all data requirements:

```python
def validate_data_requirements(self, data_requirements: List[str]) -> None:
    """Validate that this provider can satisfy data requirements"""
    missing_requirements = []
    for requirement in data_requirements:
        if requirement not in self.available_data_types:
            missing_requirements.append(requirement)
    
    if missing_requirements:
        raise ValueError(f"DataProvider cannot satisfy requirements: {missing_requirements}")
```

### Configuration Validation

The configuration system validates:

1. **Required Fields**: All required fields are present
2. **Data Requirements**: Data requirements are reasonable and achievable
3. **Component Config**: Component configurations are complete and valid
4. **Cross-References**: Component configs reference valid data types and assets

## Data Provider Queries

### Config-Driven Data Requirements
The Configuration component validates that DataProviders can satisfy the `data_requirements` specified in each mode configuration:

```yaml
data_requirements:
  - "aave_usdt_rates"
  - "btc_spot_prices"
  - "btc_futures_prices"
  - "btc_funding_rates"
  - "eth_usd_prices"
  - "weeth_eth_oracle_prices"
  - "staking_rewards_data"
```

### Standardized Data Structure
All DataProviders return data in a standardized structure:

```python
{
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

### Data Provider Factory Integration
- **DataProviderFactory.create()**: Creates mode-specific data providers based on mode
- **validate_data_requirements()**: Validates provider can satisfy all data_requirements
- **get_data()**: Returns standardized data structure for all components

### Data NOT Available from DataProvider
- **Configuration data** - handled by Configuration component
- **System settings** - handled by Configuration component
- **Validation results** - handled by Configuration component
- **Component configuration** - handled by Configuration component

## Data Access Pattern

### Config-Driven Query Pattern
```python
def load_config(self, config_path: str):
    # Load configuration from YAML files with config-driven architecture
    config = self._load_yaml_config(config_path)
    
    # Validate config-driven architecture requirements
    validation_result = self._validate_config_driven_architecture(config)
    
    # Create DataProvider factory for mode-specific data providers
    data_provider = DataProviderFactory.create(
        execution_mode=self.execution_mode,
        config=config
    )
    
    # Create Component factory for config-driven components
    components = ComponentFactory.create_all(
        config=config,
        data_provider=data_provider,
        execution_mode=self.execution_mode
    )
    
    return config
```

### Config-Driven Data Dependencies
- **Data Requirements**: Validated against DataProvider capabilities
- **Component Config**: Drives component behavior through configuration
- **Market Data**: Accessed through standardized DataProvider interface
- **Protocol Data**: Accessed through standardized DataProvider interface
- **Configuration Files**: YAML files with data_requirements and component_config

## Mode-Aware Behavior

### Config-Driven Mode Behavior
The Configuration component now supports both execution modes (backtest/live) and strategy modes (pure_lending, btc_basis, etc.) through the config-driven architecture:

### Backtest Mode
```python
def load_config(self, config_path: str):
    if self.execution_mode == 'backtest':
        # Load backtest-specific configuration with config-driven architecture
        config = self._load_backtest_config(config_path)
        
        # Create backtest DataProvider with historical data
        data_provider = DataProviderFactory.create(
            execution_mode='backtest',
            config=config
        )
        
        # Validate data requirements for backtest mode
        data_provider.validate_data_requirements(config['data_requirements'])
        
        return config
```

### Live Mode
```python
def load_config(self, config_path: str):
    elif self.execution_mode == 'live':
        # Load live-specific configuration with config-driven architecture
        config = self._load_live_config(config_path)
        
        # Create live DataProvider with real-time data
        data_provider = DataProviderFactory.create(
            execution_mode='live',
            config=config
        )
        
        # Validate data requirements for live mode
        data_provider.validate_data_requirements(config['data_requirements'])
        
        return config
```

### Strategy Mode Behavior
All strategy modes (pure_lending, btc_basis, eth_leveraged, etc.) use the same config-driven architecture:
- **Data Requirements**: Each mode specifies its data needs
- **Component Config**: Each mode configures component behavior
- **Factory Pattern**: Same factories create mode-specific instances
- **Validation**: Same validation logic applies to all modes

## Event Logging Requirements

### Component Event Log File
**Separate log file** for this component's events:
- **File**: `logs/events/configuration_events.jsonl`
- **Format**: JSON Lines (one event per line)
- **Rotation**: Daily rotation, keep 30 days
- **Purpose**: Component-specific audit trail

### Event Logging via EventLogger
All events logged through centralized EventLogger:

```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='[event_type]',
    component='Configuration',
    data={
        'event_specific_data': value,
        'state_snapshot': self.get_state_snapshot()  # optional
    }
)
```

### Events to Log

#### 1. Component Initialization
```python
self.event_logger.log_event(
    timestamp=pd.Timestamp.now(),
    event_type='component_initialization',
    component='Configuration',
    data={
        'execution_mode': self.execution_mode,
        'config_paths': list(self.config_paths.keys()),
        'config_hash': hash(str(self.global_config))
    }
)
```

#### 2. State Updates (Every config load/validation)
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='state_update',
    component='Configuration',
    data={
        'config_path': config_path,
        'validation_result': validation_result,
        'cache_size': len(self.config_cache),
        'processing_time_ms': processing_time
    }
)
```

#### 3. Error Events
```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='error',
    component='Configuration',
    data={
        'error_code': 'CFG-001',
        'error_message': str(e),
        'stack_trace': traceback.format_exc(),
        'error_severity': 'CRITICAL|HIGH|MEDIUM|LOW'
    }
)
```

#### 4. Component-Specific Critical Events
- **Config Load Failed**: When configuration loading fails
- **Config Validation Failed**: When configuration validation fails
- **Config Cache Full**: When configuration cache is full

### Event Retention & Output Formats

#### Dual Logging Approach
**Both formats are used**:
1. **JSON Lines (Iterative)**: Write events to component-specific JSONL files during execution
   - **Purpose**: Real-time monitoring during backtest runs
   - **Location**: `logs/events/configuration_events.jsonl`
   - **When**: Events written as they occur (buffered for performance)
   
2. **CSV Export (Final)**: Comprehensive CSV export at Results Store stage
   - **Purpose**: Final analysis, spreadsheet compatibility
   - **Location**: `results/[backtest_id]/events.csv`
   - **When**: At backtest completion or on-demand

#### Mode-Specific Behavior
- **Backtest**: 
  - Write JSONL iteratively (allows tracking during long runs)
  - Export CSV at completion to Results Store
  - Keep all events in memory for final processing
  
- **Live**: 
  - Write JSONL immediately (no buffering)
  - Rotate daily, keep 30 days
  - CSV export on-demand for analysis

**Note**: Current implementation stores events in memory and exports to CSV only. Enhanced implementation will add iterative JSONL writing. Reference: `docs/specs/17_HEALTH_ERROR_SYSTEMS.md`

## Error Codes

### Component Error Code Prefix: CFG
All Configuration errors use the `CFG` prefix.

### Error Code Registry
**Source**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`

All error codes registered with:

### Component Error Codes

#### CFG-001: Config Load Failed (HIGH)
**Description**: Failed to load configuration
**Cause**: File system errors, YAML parsing errors, missing files
**Recovery**: Check file paths, verify YAML syntax, ensure files exist
```python
raise ComponentError(
    error_code='CFG-001',
    message='Configuration loading failed',
    component='Configuration',
    severity='HIGH'
)
```

#### CFG-002: Config Validation Failed (HIGH)
**Description**: Configuration validation failed
**Cause**: Invalid configuration values, missing required fields, type mismatches
**Recovery**: Check configuration values, verify required fields, fix type issues
```python
raise ComponentError(
    error_code='CFG-002',
    message='Configuration validation failed',
    component='Configuration',
    severity='HIGH'
)
```

#### CFG-003: Config Cache Full (MEDIUM)
**Description**: Configuration cache has reached capacity
**Cause**: Too many cached configurations, cache size limit reached
**Recovery**: Clear old cache entries, increase cache size, optimize caching
```python
raise ComponentError(
    error_code='CFG-003',
    message='Configuration cache full',
    component='Configuration',
    severity='MEDIUM'
)
```

### Structured Error Handling Pattern

#### Error Raising
```python
from backend.src.basis_strategy_v1.core.error_codes.exceptions import ComponentError

try:
    result = self._load_config_internal(config_path)
except Exception as e:
    # Log error event
    self.event_logger.log_event(
        timestamp=timestamp,
        event_type='error',
        component='Configuration',
        data={
            'error_code': 'CFG-001',
            'error_message': str(e),
            'stack_trace': traceback.format_exc()
        }
    )
    
    # Raise structured error
    raise ComponentError(
        error_code='CFG-001',
        message=f'Configuration failed: {str(e)}',
        component='Configuration',
        severity='HIGH',
        original_exception=e
    )
```

#### Error Propagation Rules
- **CRITICAL**: Propagate to health system → trigger app restart
- **HIGH**: Log and retry with exponential backoff (max 3 retries)
- **MEDIUM**: Log and continue with degraded functionality
- **LOW**: Log for monitoring, no action needed

### Component Health Integration

#### Health Check Registration
```python
def __init__(self, ..., health_manager: UnifiedHealthManager):
    # Store health manager reference
    self.health_manager = health_manager
    
    # Register component with health system
    self.health_manager.register_component(
        component_name='Configuration',
        checker=self._health_check
    )

def _health_check(self) -> Dict:
    """Component-specific health check (private method)."""
    return {
        'status': 'healthy' | 'degraded' | 'unhealthy',
        'last_update': self.last_validation_timestamp,
        'errors': self.recent_errors[-10:],  # Last 10 errors
        'metrics': {
            'update_count': self.update_count,
            'avg_processing_time_ms': self.avg_processing_time,
            'error_rate': self.error_count / max(self.update_count, 1),
            'config_cache_size': len(self.config_cache),
            'validation_success_rate': self._calculate_validation_success_rate(),
            'memory_usage_mb': self._get_memory_usage()
        }
    }
```

#### Health Status Definitions

**Reference**: `docs/specs/17_HEALTH_ERROR_SYSTEMS.md`

## Core Methods

#

## Standardized Logging Methods

### log_structured_event(timestamp, event_type, level, message, component_name, data=None, correlation_id=None)
Log a structured event with standardized format.

**Parameters**:
- `timestamp`: Event timestamp (pd.Timestamp)
- `event_type`: Type of event (EventType enum)
- `level`: Log level (LogLevel enum)
- `message`: Human-readable message (str)
- `component_name`: Name of the component logging the event (str)
- `data`: Optional structured data dictionary (Dict[str, Any])
- `correlation_id`: Optional correlation ID for tracing (str)

**Returns**: None

### log_component_event(event_type, message, data=None, level=LogLevel.INFO)
Log a component-specific event with automatic timestamp and component name.

**Parameters**:
- `event_type`: Type of event (EventType enum)
- `message`: Human-readable message (str)
- `data`: Optional structured data dictionary (Dict[str, Any])
- `level`: Log level (defaults to INFO)

**Returns**: None

### log_performance_metric(metric_name, value, unit, data=None)
Log a performance metric.

**Parameters**:
- `metric_name`: Name of the metric (str)
- `value`: Metric value (float)
- `unit`: Unit of measurement (str)
- `data`: Optional additional context data (Dict[str, Any])

**Returns**: None

### log_error(error, context=None, correlation_id=None)
Log an error with standardized format.

**Parameters**:
- `error`: Exception object (Exception)
- `context`: Optional context data (Dict[str, Any])
- `correlation_id`: Optional correlation ID for tracing (str)

**Returns**: None

### log_warning(message, data=None, correlation_id=None)
Log a warning with standardized format.

**Parameters**:
- `message`: Warning message (str)
- `data`: Optional context data (Dict[str, Any])
- `correlation_id`: Optional correlation ID for tracing (str)

**Returns**: None

## Primary API Surface
```python
def load_config(self, config_path: str) -> Dict:
    """Load configuration from YAML files with config-driven architecture."""
    
def validate_config_driven_architecture(self, config: Dict) -> Dict:
    """Validate config-driven architecture requirements."""
    
def create_data_provider(self, config: Dict) -> BaseDataProvider:
    """Create mode-specific data provider using DataProviderFactory."""
    
def create_components(self, config: Dict, data_provider: BaseDataProvider) -> Dict:
    """Create config-driven components using ComponentFactory."""
    
def get_config_slice(self, mode: str, venue: str) -> Dict:
    """Get configuration slice for specific mode and venue."""
    
def reload_config(self, config_path: str) -> Dict:
    """Reload configuration and validate config-driven architecture."""
    
def get_config_status(self) -> Dict:
    """Get configuration status and health metrics."""
```

### Config-Driven Configuration Operations
- **load_config()**: Configuration loading from YAML files with data_requirements and component_config
- **validate_config_driven_architecture()**: Validate config-driven architecture requirements
- **create_data_provider()**: Create mode-specific data providers using factory pattern
- **create_components()**: Create config-driven components using factory pattern
- **get_config_slice()**: Mode and venue-specific configuration slicing
- **reload_config()**: Configuration hot-reloading with config-driven validation
- **get_config_status()**: Configuration health and status including factory status

## Integration Points

### Config-Driven Component Dependencies
- **All Components**: Configuration provider with config-driven architecture support
- **DataProviderFactory**: Creates mode-specific data providers based on mode
- **ComponentFactory**: Creates config-driven components with validation
- **Strategy Manager**: Strategy-specific configuration with component_config
- **Execution Manager**: Execution configuration with action mapping
- **Risk Monitor**: Risk configuration with enabled_risk_types and risk_limits
- **Exposure Monitor**: Exposure configuration with track_assets and conversion_methods
- **PnL Calculator**: PnL configuration with attribution_types and reporting_currency

### Config-Driven Data Flow
1. **Configuration Loading**: YAML file loading with data_requirements and component_config
2. **Config-Driven Validation**: Validate config-driven architecture requirements
3. **DataProvider Creation**: Create mode-specific data providers using factory
4. **Component Creation**: Create config-driven components using factory
5. **Configuration Distribution**: Distribute config-driven configuration to components
6. **Hot Reloading**: Configuration updates with config-driven validation

### Config-Driven API Integration
- **YAML Parser**: Configuration file parsing with config-driven structure
- **Config-Driven Validation**: Validate data_requirements and component_config
- **DataProviderFactory**: Mode-specific data provider creation
- **ComponentFactory**: Config-driven component creation with validation
- **Hot Reload**: Configuration update handling with config-driven validation
- **System Restart**: Configuration change propagation with factory recreation

## Code Structure Example

### Config-Driven Component Implementation
```python
class ConfigurationManager:
    def __init__(self, config_paths: Dict, execution_mode: str, 
                 health_manager: UnifiedHealthManager):
        # Store references (never passed as runtime parameters)
        self.config_paths = config_paths
        self.execution_mode = execution_mode
        self.health_manager = health_manager
        
        # Initialize config-driven architecture state
        self.global_config = {}
        self.config_cache = {}
        self.validation_results = {}
        self.last_validation_timestamp = None
        self.data_provider_factory = DataProviderFactory()
        self.component_factory = ComponentFactory()
        
        # Register with health system
        self.health_manager.register_component(
            component_name='ConfigurationManager',
            checker=self._health_check
        )
    
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML files with config-driven architecture."""
        try:
            # Load configuration with config-driven structure
            config = self._load_yaml_config(config_path)
            
            # Validate config-driven architecture requirements
            validation_result = self._validate_config_driven_architecture(config)
            
            # Create DataProvider for this mode
            data_provider = self.data_provider_factory.create(
                execution_mode=self.execution_mode,
                config=config
            )
            
            # Create config-driven components
            components = self.component_factory.create_all(
                config=config,
                data_provider=data_provider,
                execution_mode=self.execution_mode
            )
            
            # Log event
            self.event_logger.log_event(
                timestamp=pd.Timestamp.now(),
                event_type='config_loaded',
                component='ConfigurationManager',
                data={
                    'config_path': config_path, 
                    'validation_result': validation_result,
                    'mode': config.get('mode'),
                    'data_requirements': config.get('data_requirements', []),
                    'components_created': list(components.keys())
                }
            )
            
            return config
            
        except Exception as e:
            # Log error and raise structured error
            self.event_logger.log_event(
                timestamp=pd.Timestamp.now(),
                event_type='error',
                component='ConfigurationManager',
                data={'error_code': 'CFG-001', 'error_message': str(e)}
            )
            raise ComponentError(
                error_code='CFG-001',
                message=f'Configuration loading failed: {str(e)}',
                component='ConfigurationManager',
                severity='HIGH'
            )
    
    def _health_check(self) -> Dict:
        """Component-specific health check."""
        return {
            'status': 'healthy' if len(self.validation_results) == 0 else 'degraded',
            'last_validation': self.last_validation_timestamp,
            'metrics': {
                'config_cache_size': len(self.config_cache),
                'validation_errors': len(self.validation_results),
                'global_config_size': len(self.global_config)
            }
        }
```

## Related Documentation

### Component Specifications
- **Strategy Manager**: [05_STRATEGY_MANAGER.md](05_STRATEGY_MANAGER.md) - Strategy configuration
- **Execution Manager**: [06_EXECUTION_MANAGER.md](06_EXECUTION_MANAGER.md) - Execution configuration
- **Data Provider**: [09_DATA_PROVIDER.md](09_DATA_PROVIDER.md) - Data source configuration
- **Health & Error Systems**: [17_HEALTH_ERROR_SYSTEMS.md](17_HEALTH_ERROR_SYSTEMS.md) - Health monitoring integration

### Architecture Documentation
- **Reference Architecture**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Configuration management patterns
- **YAML Configuration**: YAML-based configuration specifications
- **Schema Validation**: Configuration validation and error handling

### Implementation Guides
- **Configuration Loading**: YAML file loading and parsing patterns
- **Schema Validation**: Configuration validation specifications
- **Hot Reloading**: Configuration update and system restart patterns

## Quality Gates

### Validation Criteria
- [ ] All 18 sections present and complete
- [ ] Environment Variables section documents system-level and component-specific variables
- [ ] Config Fields Used section documents universal and component-specific config
- [ ] Data Provider Queries section documents market and protocol data queries
- [ ] Event Logging Requirements section documents component-specific JSONL file
- [ ] Event Logging Requirements section documents dual logging (JSONL + CSV)
- [ ] Error Codes section has structured error handling pattern
- [ ] Error Codes section references health integration
- [ ] Health integration documented with UnifiedHealthManager
- [ ] Component-specific log file documented (`logs/events/configuration_events.jsonl`)

### Section Order Validation
- [ ] Purpose (section 1)
- [ ] Responsibilities (section 2)
- [ ] State (section 3)
- [ ] Component References (Set at Init) (section 4)
- [ ] Environment Variables (section 5)
- [ ] Config Fields Used (section 6)
- [ ] Data Provider Queries (section 7)
- [ ] Core Methods (section 8)
- [ ] Data Access Pattern (section 9)
- [ ] Mode-Aware Behavior (section 10)
- [ ] Event Logging Requirements (section 11)
- [ ] Error Codes (section 12)
- [ ] Quality Gates (section 13)
- [ ] Integration Points (section 14)
- [ ] Code Structure Example (section 15)
- [ ] Related Documentation (section 16)

### Implementation Status
- [ ] Backend implementation exists and matches spec
- [ ] All required methods implemented
- [ ] Error handling follows structured pattern
- [ ] Health integration implemented
- [ ] Event logging implemented

## ✅ **Current Configuration Status**

**Configuration System**: ✅ **FULLY FUNCTIONAL**
- Environment variables fixed (BASIS_ENVIRONMENT=dev)
- Strategy discovery working (configs/modes/ path fixed)
- All 6 strategies loading successfully
- Configuration validation passing
- Backend deployment working

## 📦 **Component Structure**

### **Core Classes**

#### **ConfigManager**
Main configuration management system.

#### **ConfigValidator**
Configuration validation and health checking.

#### **ConfigLoader**
Configuration loading from YAML files.

---

## 📊 **Data Structures**

### **Configuration Hierarchy**
```python
{
    'environment_variables': {
        'BASIS_ENVIRONMENT': str,
        'BASIS_DEPLOYMENT_MODE': str,
        'BASIS_EXECUTION_MODE': str,
        'BASIS_DEV__*': Dict[str, Any],
        'BASIS_STAGING__*': Dict[str, Any],
        'BASIS_PROD__*': Dict[str, Any]
    },
    'yaml_configs': {
        'modes': Dict[str, Any],
        'venues': Dict[str, Any],
        'share_classes': Dict[str, Any],
        'scenarios': Dict[str, Any]
    }
}
```

### **Mode Configuration**
```python
{
    'mode': str,
    'share_class': str,
    'asset': str,
    'lst_type': str,
    'rewards_mode': str,
    'target_apy': float,
    'max_drawdown': float,
    'leverage_enabled': bool,
    'target_ltv': float
}
```

---

## 🔗 **Integration with Other Components**

### **Component Dependencies**
- **All Components**: Load configuration from ConfigManager
- **Data Provider**: Uses configuration for data source selection
- **Execution Managers**: Use configuration for venue routing
- **Strategy Manager**: Uses configuration for strategy parameters

### **Configuration Flow**
```
Environment Variables → YAML Files → ConfigManager → Components
```

---

## 💻 **Implementation**

### **Config Manager**
```python
class ConfigManager:
    def __init__(self):
        self.environment_variables = {}
        self.yaml_configs = {}
        self.validator = ConfigValidator()
    
    def load_configuration(self):
        """Load configuration from environment and YAML files."""
        self._load_environment_variables()
        self._load_yaml_configs()
        self._validate_configuration()
    
    def get_complete_config(self, mode: str) -> Dict[str, Any]:
        """Get complete configuration for a specific mode."""
        base_config = self.yaml_configs['modes'][mode]
        venue_configs = self._merge_venue_configs(base_config)
        return self._merge_environment_overrides(venue_configs)
```

---

## 🧪 **Testing**

### **Configuration Tests**
```python
def test_config_loading():
    """Test configuration loading from files."""
    manager = ConfigManager()
    manager.load_configuration()
    
    assert manager.yaml_configs['modes'] is not None
    assert manager.yaml_configs['venues'] is not None
    assert manager.yaml_configs['share_classes'] is not None

def test_config_validation():
    """Test configuration validation."""
    manager = ConfigManager()
    manager.load_configuration()
    
    # Test valid configuration
    config = manager.get_complete_config('pure_lending')
    assert config['mode'] == 'pure_lending'
    assert config['share_class'] == 'USDT'
    
    # Test invalid configuration
    with pytest.raises(ValueError):
        manager.get_complete_config('invalid_mode')

def test_environment_overrides():
    """Test environment variable overrides."""
    manager = ConfigManager()
    manager.load_configuration()
    
    # Test environment override
    config = manager.get_complete_config('pure_lending')
    assert 'BASIS_ENVIRONMENT' in config
```

---

## 🎯 **Configuration Architecture**

### **Centralized Loading**
- **Single Source**: `backend/src/basis_strategy_v1/infrastructure/config/`
- **Loaded Once**: At system startup
- **No Hot Reloading**: Changes require full restart

### **Complete Configuration Hierarchy**
```
1. Environment Variables (BASIS_*) - Highest Priority
   ├── BASIS_ENVIRONMENT (dev/staging/prod) - Controls credential routing
   ├── BASIS_DEPLOYMENT_MODE (local/docker) - Controls port/host forwarding
   ├── BASIS_EXECUTION_MODE (backtest/live) - Controls venue behavior
   └── BASIS_DEV__*/BASIS_STAGING__*/BASIS_PROD__* - Environment-specific credentials

2. YAML Configuration Files (CURRENT IMPLEMENTATION):
   ├── Mode-Specific (configs/modes/*.yaml) - Strategy parameters
   ├── Venue-Specific (configs/venues/*.yaml) - Venue capabilities
   ├── Share Class (configs/share_classes/*.yaml) - Share class definitions
   └── Scenarios (configs/scenarios/*.yaml) - NOT YET IMPLEMENTED

```

### **How All Configuration Fits Together**

The system uses a **layered configuration approach** where each layer builds upon the previous:

#### **Layer 1: Base YAML Configuration**
```yaml
# configs/modes/usdt_market_neutral.yaml
mode: "usdt_market_neutral"
share_class: "USDT"
asset: "ETH"
target_apy: 0.15
max_drawdown: 0.04
leverage_enabled: true
hedge_venues: ["binance", "bybit", "okx"]
hedge_allocation:
  binance: 0.4
  bybit: 0.3
  okx: 0.3
```

#### **Layer 2: Venue Configuration**
```yaml
# configs/venues/binance.yaml
venue: "binance"
type: "cex"
trading_fees:
  spot_maker: 0.001
  futures_maker: 0.0002
max_leverage: 125
supported_assets:
  spot: ["BTC", "ETH", "USDT"]
  futures: ["BTCUSDT", "ETHUSDT"]
```

#### **Layer 3: Share Class Configuration**
```yaml
# configs/share_classes/usdt_stable.yaml
base_currency: "USDT"
risk_level: "low_to_medium"
market_neutral: true
supported_strategies:
  - "usdt_market_neutral"
  - "btc_basis"
```

#### **Layer 4: Environment Variables Override**
```bash
# env.unified + .env.dev
BASIS_ENVIRONMENT=dev
BASIS_DEPLOYMENT_MODE=local
BASIS_EXECUTION_MODE=backtest

# Environment-specific credentials
BASIS_DEV__CEX__BINANCE_SPOT_API_KEY=testnet_key
BASIS_DEV__ALCHEMY__PRIVATE_KEY=testnet_wallet_key
```

#### **Final Merged Configuration**
The system merges all layers into a single configuration object:

```yaml
# Complete merged configuration for usdt_market_neutral strategy
mode: "usdt_market_neutral"
share_class: "USDT"
asset: "ETH"
target_apy: 0.15
max_drawdown: 0.04
leverage_enabled: true

# From venue configs
venues:
  binance:
    venue: "binance"
    type: "cex"
    trading_fees:
      spot_maker: 0.001
      futures_maker: 0.0002
    max_leverage: 125

# From share class config
base_currency: "USDT"
risk_level: "low_to_medium"
market_neutral: true

# From environment variables
environment: "dev"
deployment_mode: "local"
execution_mode: "backtest"
credentials:
  binance_spot_api_key: "testnet_key"
  alchemy_private_key: "testnet_wallet_key"
```

### **Configuration Loading Flow**

The system follows a specific sequence when loading configuration:

```mermaid
graph TD
    A[System Startup] --> B[Load Environment Variables]
    B --> C[Detect BASIS_ENVIRONMENT]
    C --> D[Load YAML Mode Config]
    D --> E[Load YAML Venue Configs]
    E --> F[Load YAML Share Class Config]
    F --> G[Apply Environment Variable Overrides]
    G --> H[Validate Complete Configuration]
    H --> I[Initialize Components]
    
    style A fill:#e3f2fd
    style C fill:#fff3e0
    style D fill:#e8f5e8
    style E fill:#e8f5e8
    style F fill:#e8f5e8
    style G fill:#fff3e0
    style H fill:#ffebee
    style I fill:#e8f5e8
```

#### **Step-by-Step Configuration Loading**

1. **Environment Variable Loading**:
   ```python
   # Load from env.unified + override files
   BASIS_ENVIRONMENT=dev
   BASIS_DEPLOYMENT_MODE=local
   BASIS_EXECUTION_MODE=backtest
   ```

2. **Mode Configuration Loading**:
   ```python
   # Load strategy-specific parameters
   mode_config = load_yaml("configs/modes/usdt_market_neutral.yaml")
   # Result: {mode: "usdt_market_neutral", target_apy: 0.15, ...}
   ```

3. **Venue Configuration Loading**:
   ```python
   # Load all required venue configs
   venue_configs = {}
   for venue in mode_config["hedge_venues"]:
       venue_configs[venue] = load_yaml(f"configs/venues/{venue}.yaml")
   # Result: {binance: {...}, bybit: {...}, okx: {...}}
   ```

4. **Share Class Configuration Loading**:
   ```python
   # Load share class definition
   share_class_config = load_yaml(f"configs/share_classes/{mode_config['share_class'].lower()}_stable.yaml")
   # Result: {base_currency: "USDT", risk_level: "low_to_medium", ...}
   ```

5. **Environment Variable Override**:
   ```python
   # Apply environment-specific overrides
   if BASIS_ENVIRONMENT == "dev":
       credentials = load_dev_credentials()
   elif BASIS_ENVIRONMENT == "prod":
       credentials = load_prod_credentials()
   ```

6. **Final Configuration Merge**:
   ```python
   # Merge all layers into final config
   final_config = {
       **mode_config,
       "venues": venue_configs,
       **share_class_config,
       "environment": BASIS_ENVIRONMENT,
       "credentials": credentials
   }
   ```

### **Separation of Concerns**

**DESIGN CHOICE**: Clear separation between static configuration and deployment-specific configuration:

#### **YAML Configuration Files** (Static Strategy/Venue Configs)
- **Purpose**: Static configuration that rarely changes based on deployment
- **Content**: Strategy parameters, venue capabilities, share class definitions
- **Examples**: `target_apy`, `max_drawdown`, `lst_type`, `hedge_allocation`, venue trading parameters
- **Location**: `configs/modes/*.yaml`, `configs/venues/*.yaml`, `configs/share_classes/*.yaml`
- **When to Change**: Strategy modifications, new venues, parameter tuning

#### **Environment Variables** (Deployment-Specific Configs)
- **Purpose**: Configuration that changes per deployment environment
- **Content**: Database URLs, API ports, venue credentials, data sources
- **Examples**: `BASIS_DATABASE__URL`, `BASIS_DEV__CEX__BINANCE_SPOT_API_KEY`
- **Location**: `backend/env.unified` (overridden by deployment-specific files)
- **When to Change**: Different deployments (local vs staging vs production)

#### **Frontend Deployment Configuration** (Optional)
- **Purpose**: Frontend and Caddy-specific deployment variables
- **Content**: Domain names, TLS settings, port mappings, basic auth, API endpoints
- **Examples**: `APP_DOMAIN`, `ACME_EMAIL`, `BASIC_AUTH_HASH`, `VITE_API_BASE_URL`
- **Location**: Root `.env*` files and `frontend/.env*` files
- **When to Change**: Infrastructure changes, domain changes, frontend deployment
- **Note**: Required for full-stack deployment, optional for backend-only mode

**Reference**: `docs/ENVIRONMENT_VARIABLES.md` - Configuration Separation of Concerns section

---

## 🔄 **Configuration Update Workflow**

### **Step 1: Make Changes**

**Environment Variables** (`backend/env.unified`):
```bash
# Deployment-specific configuration
BASIS_ENVIRONMENT=dev
BASIS_DEPLOYMENT_MODE=local
BASIS_EXECUTION_MODE=backtest

# Database (deployment-specific)
BASIS_DATABASE__TYPE=sqlite
BASIS_DATABASE__URL=sqlite:///./data/basis_strategy_v1.db

# API Configuration (deployment-specific)
BASIS_API__PORT=8001
BASIS_API__CORS_ORIGINS=["http://localhost:5173"]

# Venue Credentials (environment-specific)
BASIS_DEV__ALCHEMY__PRIVATE_KEY=your_testnet_key
BASIS_DEV__CEX__BINANCE_SPOT_API_KEY=your_testnet_key
```

**YAML Configuration** (`configs/modes/btc_basis.yaml`):
```yaml
# Static strategy configuration
mode: "btc_basis"
share_class: "USDT"
asset: "BTC"
target_apy: 0.12
max_drawdown: 0.05
hedge_allocation:
  binance: 0.4
  bybit: 0.3
  okx: 0.3
```

**Venue Configuration** (`configs/venues/binance.yaml`):
```yaml
# Static venue configuration
venue: "binance"
type: "cex"
capabilities: ["spot", "futures"]
min_order_size_usd: 10
max_leverage: 125
```

**Mode Configuration** (`configs/modes/usdt_market_neutral.yaml`):
```yaml
mode: "usdt_market_neutral"
target_apy: 0.15
max_drawdown: 0.04
leverage_enabled: true
target_ltv: 0.91
```

**Venue Configuration** (`configs/venues/aave_v3.yaml`):
```yaml
venue: "aave_v3"
network: "ethereum"
liquidation_threshold: 0.95  # E-mode for weETH/WETH
```

### **Step 2: Validate**

**Automatic Validation** (at startup):
```bash
python -m pytest tests/unit/test_config_manager_unit.py -v
```

**Manual Validation**:
```python
from basis_strategy_v1.infrastructure.config.config_validator import validate_configuration

result = validate_configuration()
if not result.is_valid:
    print(f"Validation failed: {result.errors}")
```

### **Step 3: Restart System**

**Full restart required**:
```bash
# Stop all services
./deploy/stop-local.sh

# Start all services (config reloaded)
./deploy/deploy-local.sh
```

**Why restart needed**:
- Environment variables loaded at startup
- Configuration cached for performance
- Component health checks require re-read

---

## 🏗️ **Configuration Infrastructure**

### **ConfigLoader** (`config_loader.py`)
- Loads all YAML and JSON configs
- Caching, environment overrides, deep merging
- Usage: `get_config_loader().get_complete_config(mode=mode)`

### **ConfigValidator** (`config_validator.py`)
- Validates at startup
- Business logic validation
- Usage: `validate_configuration()`

### **HealthChecker** (`health_check.py`)
- Component health monitoring
- Usage: `register_component()`, `mark_component_healthy()`

### **Settings** (`settings.py`)
- Legacy compatibility layer
- Usage: `get_settings()`, `get_setting(key_path)`

### **Integration Pattern**:
```python
from ...infrastructure.config.config_loader import get_config_loader
from ...infrastructure.config.health_check import register_component

# Load config
config_loader = get_config_loader()
config = config_loader.get_complete_config(mode=mode)

# Register component
register_component('strategy_manager', ['data_provider', 'risk_monitor'])

# Use config (fail-fast, no .get() patterns)
lst_type = config['lst_type']  # Raises KeyError if missing
```

---

## 🏥 **Health Monitoring**

### **Check System Health**:
```python
from basis_strategy_v1.infrastructure.config.health_check import is_system_healthy

if is_system_healthy():
    print("✅ All components healthy")
else:
    print("❌ System unhealthy")
```

### **Health Check API**:
```bash
curl http://localhost:8001/health/detailed
```

---

## 🔍 **Configuration Validation**

### **Quality Gates Integration**

The configuration system is integrated with the consolidated quality gates system:

```bash
# Run all quality gates (includes config validation)
python3 scripts/run_quality_gates.py

# Run only configuration validation
python3 scripts/run_quality_gates.py --category configuration

# Run specific phase validation
python3 scripts/run_quality_gates.py --phase 1  # Environment and Configuration
python3 scripts/run_quality_gates.py --phase 2  # Data Provider Updates

# List all available quality gate categories
python3 scripts/run_quality_gates.py --list-categories
```

**Quality Gate Categories**:
- **strategy** - Strategy validation (Pure Lending, BTC Basis)
- **components** - Component validation (Position Monitor, Risk Monitor, etc.)
- **performance** - Performance validation (backtest speed, API response times)
- **configuration** - Configuration validation (config loading, alignment)
- **integration** - Integration validation (E2E backtest flow, live data)
- **coverage** - Test coverage analysis

### **Validation Levels**:
1. **File Structure**: Required files exist, syntax valid
2. **Environment Variables**: Required vars set, no placeholders
3. **Business Logic**: Leverage consistent, venues match allocations
4. **Component Health**: All components registered and healthy

### **Common Errors**:
```bash
# Missing environment variable
❌ Missing: BASIS_DEV__ALCHEMY__PRIVATE_KEY

# Invalid JSON
❌ Invalid YAML config: Expecting ',' at line 5

# Business logic issue
#TODO: add example as ltv more useful anymore 

# Component not initialized
❌ Component strategy_manager not initialized
```

---

## 📁 **Configuration Files**

### **Mode Configs** (`configs/modes/*.yaml` - 6 modes):
- `pure_lending.yaml` - USDT lending only
- `btc_basis.yaml` - BTC basis trading
- `eth_leveraged.yaml` - ETH leveraged staking
- `eth_staking_only.yaml` - ETH staking without leverage
- `usdt_market_neutral.yaml` - USDT market-neutral (full complexity)
- `usdt_market_neutral_no_leverage.yaml` - USDT market-neutral without leverage

**Key fields**: `mode`, `share_class`, `asset`, `lst_type`, `rewards_mode`, `target_apy`, `max_drawdown`, `leverage_enabled`, `target_ltv`

### **Share Class Configs** (`configs/share_classes/*.yaml` - 2 classes):
- `usdt_stable.yaml` - USDT stablecoin share class
- `eth_directional.yaml` - ETH directional share class

**Key fields**: `share_class`, `type`, `base_currency`, `market_neutral`, `supported_strategies`

### **Venue Configs** (`configs/venues/*.yaml` - 8 venues):
- `aave_v3.yaml` - AAVE V3 lending
- `alchemy.yaml` - Alchemy RPC
- `binance.yaml` - Binance CEX
- `bybit.yaml` - Bybit CEX
- `etherfi.yaml` - EtherFi staking
- `lido.yaml` - Lido staking
- `morpho.yaml` - Morpho lending
- `okx.yaml` - OKX CEX

---

## 🚨 **Best Practices**

### **Environment Management**:

**Development Environment**:
```bash
# Environment Variables (backend/env.unified)
BASIS_ENVIRONMENT=dev
BASIS_DEPLOYMENT_MODE=local
BASIS_EXECUTION_MODE=backtest

# Database (deployment-specific)
BASIS_DATABASE__TYPE=sqlite
BASIS_DATABASE__URL=sqlite:///./data/basis_strategy_v1.db

# Venue Credentials (environment-specific - testnet)
BASIS_DEV__ALCHEMY__NETWORK=sepolia
BASIS_DEV__ALCHEMY__CHAIN_ID=11155111
BASIS_DEV__CEX__BINANCE_SPOT_API_KEY=testnet_key
```

**Staging Environment**:
```bash
# Environment Variables (backend/env.unified)
BASIS_ENVIRONMENT=staging
BASIS_DEPLOYMENT_MODE=docker
BASIS_EXECUTION_MODE=backtest

# Database (deployment-specific)
BASIS_DATABASE__TYPE=postgresql
BASIS_DATABASE__URL=postgresql://basis_strategy_v1:password@postgres:5432/basis_strategy_v1

# Venue Credentials (environment-specific - testnet for safety)
BASIS_STAGING__ALCHEMY__NETWORK=sepolia
BASIS_STAGING__ALCHEMY__CHAIN_ID=11155111
BASIS_STAGING__CEX__BINANCE_SPOT_API_KEY=testnet_key
```

**Production Environment**:
```bash
# Environment Variables (backend/env.unified)
BASIS_ENVIRONMENT=production
BASIS_DEPLOYMENT_MODE=docker
BASIS_EXECUTION_MODE=live

# Database (deployment-specific)
BASIS_DATABASE__TYPE=postgresql
BASIS_DATABASE__URL=postgresql://basis_strategy_v1:password@postgres:5432/basis_strategy_v1

# Venue Credentials (environment-specific - mainnet)
BASIS_PROD__ALCHEMY__NETWORK=mainnet
BASIS_PROD__ALCHEMY__CHAIN_ID=1
BASIS_PROD__CEX__BINANCE_SPOT_API_KEY=mainnet_key
```

**Reference**: `docs/ENVIRONMENT_VARIABLES.md` - Environment-Specific Credential Routing section

### **Configuration Testing**:
```bash
# Test validation
pytest tests/unit/test_config_manager_unit.py -v

# Test loading
pytest tests/unit/test_data_provider_unit.py -v

# Test health
pytest tests/unit/test_risk_monitor_unit.py -v
```

---

## 🔧 **Troubleshooting**

### **Configuration Not Loading**:
1. Check file paths correct
2. Verify JSON/YAML syntax
3. Ensure required files exist
4. Check file permissions

### **Environment Variables Not Set**:
1. Check `backend/env.unified` exists
2. Verify variable names
3. Replace placeholder values
4. Restart after changes

### **Component Not Healthy**:
1. Check component registration
2. Verify component reads config
3. Check dependencies satisfied
4. Review error messages

### **Debugging Commands**:
```bash
# Validate config
python -c "from basis_strategy_v1.infrastructure.config.config_validator import validate_configuration; print(validate_configuration())"

# Check health
python -c "from basis_strategy_v1.infrastructure.config.health_check import get_health_summary; print(get_health_summary())"

# List env vars
env | grep BASIS_
```

---

## 📊 **Configuration Field Categories**

### **Fields from Data** (Not in mode configs):
- `max_ltv` - From `data/protocol_data/aave/risk_params/aave_v3_risk_parameters.json` (0.93 for E-mode)
- `liquidation_threshold` - From same file (0.95 for E-mode)
- `liquidation_bonus` - From same file (0.01 for E-mode)

**Rationale**: Protocol parameters from data (updatable without code changes)

### **Fields Dynamically Calculated**:
- `ltv_target` = `max_ltv × (1 - max_stake_spread_move)`
- Example: `0.93 × (1 - 0.02215) = 0.9094`

### **Mode Configuration Fields**:

**Core Strategy**:
- `mode`, `share_class`, `asset`, `lst_type`, `rewards_mode`
- `lending_enabled`, `staking_enabled`, `basis_trade_enabled`, `leverage_enabled`

**Execution**:
- `position_deviation_threshold`: Minimum deviation from target position to trigger rebalancing (default 0.02 = 2%)

**Hedging** (market-neutral modes):
- `hedge_venues`, `hedge_allocation`

**Risk**:
- `margin_ratio_target`, `max_stake_spread_move`

**Performance**:
- `target_apy`, `max_drawdown`

**For complete field listing**: See mode YAML files

---

## 📋 **Checklist**

### **Before Changes**:
- [ ] Backup current configuration
- [ ] Understand impact
- [ ] Plan restart window
- [ ] Test in dev first

### **After Changes**:
- [ ] Validate syntax
- [ ] Check environment variables
- [ ] Verify business logic
- [ ] Restart system
- [ ] Check component health
- [ ] Run config tests
- [ ] Monitor behavior

### **Production Deployment**:
- [ ] Test in staging
- [ ] Validate all configs
- [ ] Check environment variables
- [ ] Plan maintenance window
- [ ] Backup production config
- [ ] Deploy with monitoring
- [ ] Verify system health
- [ ] Monitor for issues

---

## 🎯 **Summary**

**Key Points**:
1. Configuration is centralized
2. Changes require restart
3. Validation is comprehensive
4. Health monitoring built-in
5. Testing required

**Workflow**:
1. Make changes to config/env files
2. Validate configuration
3. Restart system
4. Check health
5. Monitor system

---

## 🔧 **Current Implementation Status**

**Overall Completion**: 95% (Fully implemented and operational)

### **Core Functionality Status**
- ✅ **Working**: Centralized loading, complete configuration hierarchy, environment variables, YAML configuration files, mode-specific configs, venue-specific configs, share class configs, configuration validation, quality gates integration, health check API, configuration testing, troubleshooting, best practices
- ⚠️ **Partial**: None
- ❌ **Missing**: None
- 🔄 **Refactoring Needed**: Minor enhancements for production readiness

### **Architecture Compliance Status**
- ✅ **COMPLIANT**: Configuration system follows canonical architecture requirements
- **No Violations Found**: Component fully compliant with architectural principles

### **TODO Items and Refactoring Needs**
- **High Priority**:
  - None identified
- **Medium Priority**:
  - None identified
- **Low Priority**:
  - None identified

### **Quality Gate Status**
- **Current Status**: PASS
- **Failing Tests**: None
- **Requirements**: All requirements met
- **Integration**: Fully integrated with quality gate system

### **Task Completion Status**
- **Related Tasks**: 
  - [docs/REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) (95% complete - fully implemented)
- **Completion**: 95% complete overall
- **Blockers**: None
- **Next Steps**: None - component is production ready

## Public API Methods

### get_complete_config() -> Dict[str, Any]
**Purpose**: Get the complete configuration dictionary.

**Returns**: Dictionary containing all configuration data

**Usage**: Called by other components to retrieve complete configuration.

### load_scenario_config(scenario_name: str) -> Dict[str, Any]
**Purpose**: Load configuration for a specific scenario.

**Parameters**:
- `scenario_name`: Name of the scenario to load (str)

**Returns**: Dictionary containing scenario configuration

**Usage**: Called by scenario management components to load scenario-specific configurations.

### get_settings() -> Dict[str, Any]
**Purpose**: Get current system settings.

**Returns**: Dictionary containing system settings

**Usage**: Called by components to retrieve current system settings.

### get_environment() -> str
**Purpose**: Get current environment name.

**Returns**: Current environment name (str)

**Usage**: Called by components to determine current environment.

### get_mode_config(mode_name: str) -> Dict[str, Any]
**Purpose**: Get configuration for a specific mode.

**Parameters**:
- `mode_name`: Name of the mode (str)

**Returns**: Dictionary containing mode configuration

**Usage**: Called by mode-specific components to retrieve mode configurations.

### get_data(timestamp: pd.Timestamp) -> Dict[str, Any]
**Purpose**: Get data using canonical data access pattern.

**Parameters**:
- `timestamp`: Current timestamp

**Returns**: Dictionary containing configuration data

**Usage**: Called by other components to retrieve configuration data.

### get_execution_mode() -> str
**Purpose**: Get current execution mode.

**Returns**: Current execution mode (str)

**Usage**: Called by components to determine execution mode.

### get_data_directory() -> str
**Purpose**: Get the data directory path.

**Returns**: Data directory path (str)

**Usage**: Called by data components to get data directory location.

### get_results_directory() -> str
**Purpose**: Get the results directory path.

**Returns**: Results directory path (str)

**Usage**: Called by results components to get results directory location.

### get_available_strategies() -> List[str]
**Purpose**: Get list of available strategies.

**Returns**: List of available strategy names

**Usage**: Called by strategy management components to discover available strategies.

### get_config_manager() -> Any
**Purpose**: Get the configuration manager instance.

**Returns**: Configuration manager instance

**Usage**: Called by components to get configuration manager reference.

### validate_strategy_name(strategy_name: str) -> bool
**Purpose**: Validate if a strategy name is valid.

**Parameters**:
- `strategy_name`: Name of the strategy to validate (str)

**Returns**: True if strategy name is valid, False otherwise

**Usage**: Called by strategy components to validate strategy names.

### strategy_exists(strategy_name: str) -> bool
**Purpose**: Check if a strategy exists.

**Parameters**:
- `strategy_name`: Name of the strategy to check (str)

**Returns**: True if strategy exists, False otherwise

**Usage**: Called by strategy components to check strategy existence.

### check_component_health() -> Dict[str, Any]
**Purpose**: Check component health status for monitoring and diagnostics.

**Returns**:
```python
{
    'status': 'healthy' | 'degraded' | 'unhealthy',
    'error_count': int,
    'execution_mode': 'backtest' | 'live',
    'config_cache_size': int,
    'component': 'ConfigManager'
}
```

**Usage**: Called by health monitoring systems to track Configuration Manager status and performance.

### get_data_date_range() -> Dict[str, Any]
**Purpose**: Get the date range for data operations.

**Returns**: Dictionary containing date range information

**Usage**: Called by data components to get data date range.

### is_healthy() -> bool
**Purpose**: Check if the configuration system is healthy.

**Returns**: True if healthy, False otherwise

**Usage**: Called by health monitoring systems to check configuration system health.

### get_venue_config(venue_name: str) -> Dict[str, Any]
**Purpose**: Get configuration for a specific venue.

**Parameters**:
- `venue_name`: Name of the venue (str)

**Returns**: Dictionary containing venue configuration

**Usage**: Called by venue components to retrieve venue configurations.

### load_mode_config(mode_name: str) -> Dict[str, Any]
**Purpose**: Load configuration for a specific mode.

**Parameters**:
- `mode_name`: Name of the mode (str)

**Returns**: Dictionary containing mode configuration

**Usage**: Called by mode components to load mode configurations.

### load_share_class_config(share_class_name: str) -> Dict[str, Any]
**Purpose**: Load configuration for a specific share class.

**Parameters**:
- `share_class_name`: Name of the share class (str)

**Returns**: Dictionary containing share class configuration

**Usage**: Called by share class components to load share class configurations.

### get_strategy_file_path(strategy_name: str) -> str
**Purpose**: Get the file path for a specific strategy.

**Parameters**:
- `strategy_name`: Name of the strategy (str)

**Returns**: File path for the strategy (str)

**Usage**: Called by strategy components to get strategy file paths.

### create_component(component_type: str, config: Dict[str, Any]) -> Any
**Purpose**: Create a component instance with configuration.

**Parameters**:
- `component_type`: Type of component to create (str)
- `config`: Configuration for the component (Dict[str, Any])

**Returns**: Created component instance

**Usage**: Called by component factory to create configured component instances.

### load_venue_config(venue_name: str) -> Dict[str, Any]
**Purpose**: Load configuration for a specific venue.

**Parameters**:
- `venue_name`: Name of the venue (str)

**Returns**: Dictionary containing venue configuration

**Usage**: Called by venue components to load venue configurations.

### get_share_class_config(share_class_name: str) -> Dict[str, Any]
**Purpose**: Get configuration for a specific share class.

**Parameters**:
- `share_class_name`: Name of the share class (str)

**Returns**: Dictionary containing share class configuration

**Usage**: Called by share class components to retrieve share class configurations.

### load_strategy_config(strategy_name: str) -> Dict[str, Any]
**Purpose**: Load configuration for a specific strategy.

**Parameters**:
- `strategy_name`: Name of the strategy (str)

**Returns**: Dictionary containing strategy configuration

**Usage**: Called by strategy components to load strategy configurations.

---

**Remember**: Configuration changes require full system restart! 🔄

*Last Updated: October 3, 2025*
