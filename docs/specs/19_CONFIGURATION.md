# Configuration Manager Component Specification

**Last Reviewed**: October 12, 2025

## Purpose
Manage configuration loading, validation, and system restarts for the Basis Strategy platform using a **config-driven architecture** that enables mode-agnostic components while supporting mode-specific data requirements and behavior.

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [../REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Core principles including config-driven architecture
- **Strategy Specifications**: [../MODES.md](../MODES.md) - Strategy mode definitions
- **Configuration Guide**: [../ENVIRONMENT_VARIABLES.md](../ENVIRONMENT_VARIABLES.md) - Environment variable management
- **Implementation Patterns**: [../CODE_STRUCTURE_PATTERNS.md](../CODE_STRUCTURE_PATTERNS.md) - Complete implementation patterns
- **Component Index**: [../COMPONENT_SPECS_INDEX.md](../COMPONENT_SPECS_INDEX.md) - All 20 components (11 core + 9 supporting)

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

### System-Level Variables (Read at Initialization)
- `BASIS_EXECUTION_MODE`: backtest | live
  - **Usage**: Determines simulated vs real API behavior
  - **Read at**: Component __init__
  - **Affects**: Mode-aware conditional logic

- `BASIS_ENVIRONMENT`: dev | staging | production
  - **Usage**: Credential routing for venue APIs
  - **Read at**: Component __init__ (if uses external APIs)
  - **Affects**: Which API keys/endpoints to use

- `BASIS_DEPLOYMENT_MODE`: local | docker
  - **Usage**: Port/host configuration
  - **Read at**: Component __init__ (if network calls)
  - **Affects**: Connection strings

- `BASIS_DATA_MODE`: csv | db
  - **Usage**: Data source selection (DataProvider only)
  - **Read at**: DataProvider __init__
  - **Affects**: File-based vs database data loading

### Component-Specific Variables
- `CONFIG_VALIDATION_STRICT`: Strict configuration validation mode (default: true)
- `CONFIG_CACHE_SIZE`: Configuration cache size (default: 1000)
- `CONFIG_RELOAD_INTERVAL`: Configuration reload interval in seconds (default: 300)

### Environment Variable Access Pattern
```python
def __init__(self, ...):
    # Read env vars ONCE at initialization
    self.execution_mode = os.getenv('BASIS_EXECUTION_MODE', 'backtest')
    # NEVER read env vars during runtime loops
```

### Behavior NOT Determinable from Environment Variables
- Configuration file paths (hard-coded in component)
- Validation rules (hard-coded business logic)
- Cache behavior (hard-coded algorithms)

## Config Fields Used

### Universal Config (All Components)
- `mode`: str - Strategy mode name (e.g., 'pure_lending', 'btc_basis')
- `share_class`: str - Share class currency ('USDT' | 'ETH')
- `asset`: str - Primary asset name
- `execution_mode`: 'backtest' | 'live' (from strategy mode slice)
- `log_level`: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' (from strategy mode slice)
- `initial_capital`: float - Starting capital amount for the strategy

### Config-Driven Architecture Fields
- `data_requirements`: List[str] - Data types required by this mode
  - **Usage**: Validates that DataProvider can satisfy all requirements
  - **Examples**: ["aave_usdt_rates", "btc_spot_prices", "eth_usd_prices"]
- `component_config`: Dict - Component behavior configuration
  - **risk_monitor**: Risk calculation configuration
  - **exposure_monitor**: Asset tracking configuration
  - **pnl_calculator**: PnL attribution configuration
  - **strategy_manager**: Strategy behavior configuration
  - **execution_manager**: Execution action configuration
  - **results_store**: Results storage configuration

### ML-Specific Configuration Fields
- `ml_config`: Dict - Machine learning model configuration
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
- `delta_tolerance`: float - Delta neutrality tolerance (0.0-1.0)
- `stake_allocation_eth`: float - ETH stake allocation percentage (0.0-1.0)
- `funding_threshold`: float - Funding rate threshold for basis trading
- `max_ltv`: float - Maximum loan-to-value ratio (0.0-1.0)
- `leverage_enabled`: bool - Whether leverage is enabled for this mode
- `hedge_venues`: List[str] - List of venues used for hedging
- `hedge_allocation_bybit`: float - Allocation percentage to Bybit for hedging
- `position_deviation_threshold`: float - Position deviation threshold (0.0-1.0)
- `rewards_mode`: str - Rewards collection mode

### Share Class Configuration Fields
- `share_class`: str - Share class name ('USDT' | 'ETH')
- `type`: str - Share class type ('stable' | 'directional')
- `base_currency`: str - Base currency ('USDT' | 'ETH')
- `description`: str - Share class description
- `decimal_places`: int - Decimal places for precision (0-18)
- `risk_level`: str - Risk level ('low', 'medium', 'high')
- `market_neutral`: bool - Whether market neutral strategies are supported
- `allows_hedging`: bool - Whether hedging is allowed
- `supported_strategies`: List[str] - List of supported strategy modes
- `leverage_supported`: bool - Whether leverage is supported
- `staking_supported`: bool - Whether staking is supported
- `basis_trading_supported`: bool - Whether basis trading is supported
- `max_leverage`: Optional[float] - Maximum leverage allowed (1.0+)
- `target_apy_range`: Optional[Dict[str, float]] - Target APY range (min/max)
- `max_drawdown`: Optional[float] - Maximum drawdown limit (0.0-1.0)

### Venue Configuration Fields
- `venues`: Dict[str, Dict] - Venue configuration mapping
- `venues.{venue_name}.venue_type`: str - Venue type ('cex', 'defi', 'infrastructure')
- `venues.{venue_name}.enabled`: bool - Whether venue is enabled for this mode
- `venues.{venue_name}.instruments`: List[str] - Trading instruments available on venue
- `venues.{venue_name}.order_types`: List[str] - Supported order types on venue

### Event Logger Configuration Fields
- `event_logger`: Dict - Event logging configuration
- `event_logger.log_path`: str - Path to log files
- `event_logger.log_format`: str - Log format ('json', 'text')
- `event_logger.log_level`: str - Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
- `event_logger.event_categories`: Dict[str, List[str]] - Event categories and types
- `event_logger.event_logging_settings`: Dict - Event logging behavior settings
- `event_logger.log_retention_policy`: Dict - Log retention and rotation settings
- `event_logger.logging_requirements`: Dict - Logging feature requirements
- `event_logger.event_filtering`: Dict - Event filtering configuration

### Config Access Pattern
```python
def __init__(self, config: Dict, ...):
    # Extract config in __init__ (NEVER in methods)
    self.mode = config.get('mode')
    self.share_class = config.get('share_class')
    self.component_config = config.get('component_config', {})
```

## Core Methods

### get_data(timestamp: pd.Timestamp) -> Dict[str, Any]
Returns configuration data for the specified timestamp. Implements the canonical data provider pattern.

### create_component(component_type: str, config: Dict[str, Any]) -> Any
Creates a component instance using the component factory with validated configuration.

### get_complete_config(mode: str = None, venue: str = None) -> Dict[str, Any]
Returns complete configuration for specified mode and venue with validation.

### get_available_strategies() -> List[str]
Returns list of available strategy modes from configuration files.

### get_mode_config(mode_name: str) -> Dict[str, Any]
Returns configuration for a specific strategy mode with validation.

### get_venue_config(venue_name: str) -> Dict[str, Any]
Returns configuration for a specific venue with validation.

### get_share_class_config(share_class_name: str) -> Dict[str, Any]
Returns configuration for a specific share class with validation.

### strategy_exists(strategy_name: str) -> bool
Checks if a strategy configuration exists and is valid.

### validate_strategy_name(strategy_name: str) -> None
Validates strategy name and raises error if invalid.

### check_component_health() -> Dict[str, Any]
Returns component health status and validation results.

### is_healthy() -> bool
Returns boolean health status for the configuration system.

## Configuration Parameters

### Config-Driven Architecture

The Configuration Manager uses a **mode-agnostic** approach where components receive configuration through `component_config` sections:

```yaml
component_config:
  risk_monitor:
    risk_limits:
      liquidation_threshold: 0.8
      target_margin_ratio: 0.5
      delta_tolerance: 0.005
  exposure_monitor:
    track_assets: ["ETH", "weETH", "aWeETH", "variableDebtWETH", "USDT"]
    conversion_methods:
      ETH: "usd_price"
      weETH: "oracle_price"
      aWeETH: "aave_index"
```

### Configuration File Structure

**Complete Configuration Examples**: See `configs/modes/*.yaml` for complete examples for all 7 strategy modes.

**Configuration Categories**:

| Category | Description | Files |
|----------|-------------|-------|
| **Mode Configs** | Strategy-specific configuration | `configs/modes/*.yaml` |
| **Venue Configs** | Venue-specific settings | `configs/venues/*.yaml` |
| **Share Class Configs** | Share class definitions | `configs/share_classes/*.yaml` |
| **Base Config** | Global settings | `configs/base.yaml` |

**Cross-Reference**: [../MODES.md](../MODES.md) - Strategy mode definitions and configuration requirements

## Data Access Pattern

### Canonical Data Provider Pattern
Configuration Manager uses the canonical `get_data(timestamp)` pattern to provide configuration data:

```python
# Canonical pattern - single get_data call
config_data = self.config_manager.get_data(timestamp)
mode_config = config_data['mode_config']
venue_config = config_data['venue_config']
component_config = config_data['component_config']
```

### Data Types Provided
- `mode_config` - Strategy mode configuration
- `venue_config` - Venue-specific configuration
- `share_class_config` - Share class configuration
- `component_config` - Component behavior configuration
- `ml_config` - ML model configuration (if applicable)

## Mode-Aware Behavior

### Backtest Mode
- Loads configuration from YAML files
- Validates configuration structure and business rules
- Provides configuration caching for performance
- Simulates configuration updates without system restart

### Live Mode
- Loads configuration from YAML files with live validation
- Validates environment-specific credentials
- Provides configuration hot-reloading capability
- Handles configuration updates with system restart coordination

### Behavior NOT Determinable from Environment Variables
- Configuration file loading logic (hard-coded paths)
- Validation rule implementation (hard-coded business logic)
- Cache management algorithms (hard-coded behavior)

## Event Logging Requirements

### Component-Specific Events
- `config_loaded` - Configuration successfully loaded
- `config_validated` - Configuration validation completed
- `config_error` - Configuration loading or validation failed
- `strategy_discovered` - Strategy configuration discovered
- `venue_validated` - Venue configuration validated

### Event Data Structure
```json
{
  "event_type": "config_loaded",
  "component": "config_manager",
  "mode": "btc_basis",
  "config_files": ["configs/modes/btc_basis.yaml"],
  "validation_status": "success",
  "timestamp": "2025-10-12T10:00:00Z"
}
```

## Error Codes

### Configuration Manager Error Codes
- **CFG-001**: Configuration loading failed
- **CFG-002**: Environment variable not set
- **CFG-003**: Configuration file not found
- **CFG-004**: Configuration parsing error
- **CFG-005**: Configuration validation failed
- **CFG-006**: Strategy not found
- **CFG-007**: Configuration merge failed
- **CFG-008**: Configuration health check failed

### Error Handling Pattern
```python
try:
    config = self._load_config_file(file_path)
except Exception as e:
    self.log_error(e, context={'file_path': str(file_path)})
    raise ComponentError('CFG-001', f"Configuration loading failed: {e}")
```

## Code Structure Example

### Configuration Manager Implementation Pattern
```python
class ConfigManager(StandardizedLoggingMixin):
    def __init__(self):
        self.config_cache: Dict[str, Any] = {}
        self._validation_result: Optional[ValidationResult] = None
        
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Canonical data provider pattern."""
        return {
            'mode_config': self.get_mode_config(self.current_mode),
            'venue_config': self.get_venue_config(self.current_venue),
            'component_config': self.get_component_config()
        }
    
    def get_mode_config(self, mode_name: str) -> Dict[str, Any]:
        """Get validated mode configuration."""
        if mode_name not in self.config_cache:
            self._load_and_validate_mode(mode_name)
        return self.config_cache[mode_name]
```

## Integration Points

### Data Provider Integration
- **DataProvider Factory**: Creates mode-specific data providers using configuration
- **Data Requirements Validation**: Validates that data providers can satisfy mode requirements
- **Cross-Reference**: [09_DATA_PROVIDER.md](09_DATA_PROVIDER.md) - Data provider configuration

### Component Factory Integration
- **Component Creation**: Creates components with validated configuration
- **Config-Driven Behavior**: Components receive behavior configuration through component_config
- **Cross-Reference**: [10_COMPONENT_FACTORY.md](10_COMPONENT_FACTORY.md) - Component factory integration

### Execution Manager Integration
- **Venue Configuration**: Provides venue-specific configuration for execution interfaces
- **Strategy Configuration**: Provides strategy-specific configuration for execution planning
- **Cross-Reference**: [06_EXECUTION_MANAGER.md](06_EXECUTION_MANAGER.md) - Execution configuration

## Quality Gates

### Implementation Compliance
- **Core Methods**: All 12 core methods implemented
- **Config Parameters**: All configuration parameters supported
- **Architecture Compliance**: 0.95 (excellent compliance with config-driven architecture)

### Validation Requirements
- Configuration file structure validation
- Business rule validation (risk limits, position sizes, etc.)
- Environment variable validation
- Cross-reference validation (venues, share classes, strategies)

### Performance Requirements
- Configuration loading: < 100ms for single mode
- Configuration caching: < 10ms for cached configs
- Validation: < 50ms for complete configuration validation

## Related Documentation

- **Environment Variables**: [../ENVIRONMENT_VARIABLES.md](../ENVIRONMENT_VARIABLES.md) - Environment variable management
- **Strategy Modes**: [../MODES.md](../MODES.md) - Strategy mode definitions and configuration
- **Data Provider**: [09_DATA_PROVIDER.md](09_DATA_PROVIDER.md) - Data provider configuration integration
- **Component Factory**: [10_COMPONENT_FACTORY.md](10_COMPONENT_FACTORY.md) - Component factory integration
- **Execution Manager**: [06_EXECUTION_MANAGER.md](06_EXECUTION_MANAGER.md) - Execution configuration
- **Venue Architecture**: [../VENUE_ARCHITECTURE.md](../VENUE_ARCHITECTURE.md) - Venue configuration patterns
- **Health Systems**: [17_HEALTH_ERROR_SYSTEMS.md](17_HEALTH_ERROR_SYSTEMS.md) - Health monitoring integration