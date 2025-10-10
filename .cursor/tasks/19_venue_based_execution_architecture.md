# VENUE-BASED EXECUTION ARCHITECTURE

## CANONICAL SOURCE
This task file provides implementation guidance. For complete architectural details, see:
- **docs/VENUE_ARCHITECTURE.md** - Canonical venue architecture specification
- **docs/MODES.md** - Strategy mode specifications and venue requirements

## KEY ARCHITECTURAL CLARIFICATIONS

### Configuration Structure
- **Sensitive Credentials**: Stored in env.unified (API keys, secrets, private keys)
- **Static Venue Attributes**: Stored in configs/venues/*.yaml (order sizes, tick sizes, protocol parameters)
- **Venue Subscriptions**: Stored in configs/modes/*.yaml (which venues each strategy can use)

### Environment Variables
- **BASIS_ENVIRONMENT**: Controls venue credential routing (dev/staging/prod)
- **BASIS_EXECUTION_MODE**: Controls venue execution behavior (backtest vs live)
- **Naming Convention**: BASIS_{ENV}__{CATEGORY}__{VENUE}_{PARAM}
  - Example: BASIS_DEV__CEX__BINANCE_SPOT_API_KEY
  - Example: BASIS_PROD__ALCHEMY__RPC_URL

## OVERVIEW
Execution manager is venue-centric, with configuration mapping action types to venues for each strategy. Each venue needs clients with live, testnet, and simulation modes for smooth transition from backtest to live trading. All execution interfaces implement tight loop reconciliation for position verification.

## VENUE CONFIGURATION ARCHITECTURE

### 1. Configuration Separation of Concerns

**Sensitive Credentials (env.unified)**:
```bash
# Development Environment
BASIS_DEV__ALCHEMY__PRIVATE_KEY=
BASIS_DEV__ALCHEMY__RPC_URL=
BASIS_DEV__ALCHEMY__WALLET_ADDRESS=
BASIS_DEV__CEX__BINANCE_SPOT_API_KEY=
BASIS_DEV__CEX__BINANCE_SPOT_SECRET=

# Production Environment  
BASIS_PROD__ALCHEMY__PRIVATE_KEY=
BASIS_PROD__ALCHEMY__RPC_URL=
BASIS_PROD__ALCHEMY__WALLET_ADDRESS=
BASIS_PROD__CEX__BINANCE_SPOT_API_KEY=
BASIS_PROD__CEX__BINANCE_SPOT_SECRET=
```

**Static Venue Attributes (configs/venues/binance.yaml)**:
```yaml
venue_type: "cex"
supported_markets:
  - spot
  - futures
trading_parameters:
  min_order_size_usd: 10
  max_leverage: 125
  tick_size: 0.01
  min_size: 0.001
```

**Venue Subscriptions (configs/modes/btc_basis.yaml)**:
```yaml
mode: "btc_basis"
share_class: "USDT"
asset: "BTC"

# Venue subscriptions - which venues this strategy can use
venues:
  data_subscriptions:
    - binance  # Market data
    - bybit    # Market data
    - okx      # Market data
  
  execution_subscriptions:
    cex_spot:
      - binance  # BTC spot trades
    cex_futures:
      - binance  # 40% hedge allocation
      - bybit    # 30% hedge allocation
      - okx      # 30% hedge allocation
    wallet:
      - alchemy  # On-chain wallet transfers
```

### 2. Environment-Specific Routing
**Reference**: docs/VENUE_ARCHITECTURE.md - Environment Variable Configuration section

Execution manager routes to appropriate credentials based on BASIS_ENVIRONMENT:
- **dev**: Uses BASIS_DEV__* credentials, testnet endpoints
- **staging**: Uses BASIS_STAGING__* credentials, testnet endpoints
- **production**: Uses BASIS_PROD__* credentials, mainnet endpoints

## VENUE CLIENT ARCHITECTURE

### 1. Venue Client Interface
Each venue client loads credentials from environment variables based on BASIS_ENVIRONMENT:

```python
class VenueClient:
    """Base class for venue clients."""
    
    def __init__(self, venue_name: str, environment: str):
        self.venue_name = venue_name
        self.environment = environment  # from BASIS_ENVIRONMENT
        self.credentials = self._load_credentials()
        self.static_config = self._load_static_config()
    
    def _load_credentials(self):
        """Load credentials from environment variables."""
        # Example: BASIS_DEV__CEX__BINANCE_SPOT_API_KEY
        prefix = f"BASIS_{self.environment.upper()}__"
        return {
            'api_key': os.getenv(f'{prefix}CEX__{self.venue_name.upper()}_SPOT_API_KEY'),
            'secret': os.getenv(f'{prefix}CEX__{self.venue_name.upper()}_SPOT_SECRET')
        }
    
    def _load_static_config(self):
        """Load static venue configuration from YAML."""
        # Load from configs/venues/{venue_name}.yaml
        return load_yaml(f'configs/venues/{self.venue_name}.yaml')
    
    def is_live(self) -> bool:
        """Check if client is in live mode."""
        return self.environment in ['staging', 'production']
    
    def is_testnet(self) -> bool:
        """Check if client is in testnet mode."""
        return self.environment in ['dev', 'staging']
    
    def is_simulation(self) -> bool:
        """Check if client is in simulation mode."""
        return self.environment == 'backtest'

class BinanceClient(VenueClient):
    """Binance venue client."""
    
    def __init__(self, environment: str):
        super().__init__('binance', environment)
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Binance client based on environment."""
        if self.is_live():
            return ccxt.binance({
                'apiKey': self.credentials['api_key'],
                'secret': self.credentials['secret'],
                'sandbox': False
            })
        else:  # testnet or simulation
            return ccxt.binance({
                'apiKey': self.credentials['api_key'],
                'secret': self.credentials['secret'],
                'sandbox': True
            })

class AaveClient(VenueClient):
    """Aave venue client."""
    
    def __init__(self, environment: str):
        super().__init__('aave', environment)
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Aave client based on environment."""
        rpc_url = os.getenv(f'BASIS_{self.environment.upper()}__ALCHEMY__RPC_URL')
        return Web3(Web3.HTTPProvider(rpc_url))

class AlchemyClient(VenueClient):
    """Alchemy venue client."""
    
    def __init__(self, environment: str):
        super().__init__('alchemy', environment)
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Alchemy client based on environment."""
        rpc_url = os.getenv(f'BASIS_{self.environment.upper()}__ALCHEMY__RPC_URL')
        return Web3(Web3.HTTPProvider(rpc_url))
```

## EXECUTION MODES

### Backtest Mode
**CRITICAL**: Execution interfaces in backtest mode exist for CODE ALIGNMENT only:
- **NO credentials required**: Don't load API keys or secrets
- **NO heartbeat tests**: Don't test API connectivity
- **NO real API calls**: All operations simulated
- **Dummy venue calls**: Make dummy calls but don't wait for responses
- **Immediate completion**: Mark operations complete to trigger downstream updates
- **Data source**: Handled by DATA PROVIDER (CSV vs DB), not execution manager

### Live Mode
- **Real credentials**: Load from BASIS_ENVIRONMENT-specific env variables
- **API connectivity**: Test heartbeat and validate credentials
- **Real execution**: Actual API calls to testnet or production
- **Error handling**: Retry logic with exponential backoff

### 2. Execution Manager Venue Routing
Execution manager routes actions to appropriate venues based on strategy configuration:

```python
class ExecutionManager:
    """Venue-based execution manager."""
    
    def __init__(self, config, data_provider, utility_manager):
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        self.venue_clients = self._initialize_venue_clients()
    
    def _initialize_venue_clients(self):
        """Initialize venue clients based on environment."""
        environment = os.getenv('ENVIRONMENT', 'simulation')
        venue_clients = {}
        
        # Initialize all venue clients for current environment
        for venue_name in ['binance', 'bybit', 'okx', 'aave', 'lido', 'alchemy', 'instadapp']:
            venue_clients[venue_name] = self._create_venue_client(venue_name, environment)
        
        return venue_clients
    
    def _create_venue_client(self, venue_name, environment):
        """Create venue client for specific venue and environment."""
        if venue_name == 'binance':
            return BinanceClient(self.config, environment)
        elif venue_name == 'aave':
            return AaveClient(self.config, environment)
        elif venue_name == 'alchemy':
            return AlchemyClient(self.config, environment)
        # ... other venue clients
    
    def execute_action(self, action, mode, timestamp):
        """Execute action using appropriate venue based on strategy configuration."""
        # Get venue configuration for this action type and mode
        venue_config = self.config.get(f'modes.{mode}.venues.{action.action_type}')
        venue_name = venue_config['primary']
        
        # Get venue client
        venue_client = self.venue_clients[venue_name]
        
        # Execute action using venue client
        return venue_client.execute(action, timestamp)
```

## ENVIRONMENT CONFIGURATION

### 1. Environment Variables
Environment determines which components are in what mode:

```bash
# .env.dev (for local development)
ENVIRONMENT=simulation
BINANCE_TESTNET_API_KEY=your_testnet_key
BINANCE_TESTNET_SECRET_KEY=your_testnet_secret
ALCHEMY_TESTNET_RPC_URL=your_testnet_rpc_url
ALCHEMY_TESTNET_API_KEY=your_testnet_api_key

# .env.testnet (for testnet deployment)
ENVIRONMENT=testnet
BINANCE_TESTNET_API_KEY=your_testnet_key
BINANCE_TESTNET_SECRET_KEY=your_testnet_secret
ALCHEMY_TESTNET_RPC_URL=your_testnet_rpc_url
ALCHEMY_TESTNET_API_KEY=your_testnet_api_key

# .env.live (for live deployment)
ENVIRONMENT=live
BINANCE_LIVE_API_KEY=your_live_key
BINANCE_LIVE_SECRET_KEY=your_live_secret
ALCHEMY_LIVE_RPC_URL=your_live_rpc_url
ALCHEMY_LIVE_API_KEY=your_live_api_key
```

### 2. Mixed Environment Support
Can mix and match environments for different venues:

```yaml
# configs/environments/mixed_testnet.yaml
venues:
  binance:
    environment: "testnet"  # Use testnet for CEX execution
  
  aave:
    environment: "simulation"  # Use simulation for on-chain execution
  
  alchemy:
    environment: "testnet"  # Use testnet for wallet transfers
```

## STRATEGY MODE CONFIGURATION

### 1. Required vs Optional Venues
Not every strategy mode needs each venue configuration:

```yaml
# configs/modes/pure_lending.yaml
venues:
  lending_execution:
    primary: "aave"
    on_chain_leverage_venue: "aave"
  # No hedge_execution, staking_execution, flash_loan_execution needed

# configs/modes/btc_basis.yaml
venues:
  hedge_execution:
    primary: "binance"
    hedge_allocation: 0.5
  # No staking_execution, lending_execution needed

# configs/modes/eth_staking.yaml
venues:
  staking_execution:
    primary: "lido"
    lst_type: "lido"
  flash_loan_execution:
    primary: "instadapp"
    use_flash_loan: true
  unwind_execution:
    primary: "instadapp"
    unwind_mode: "flash_loan"
  # No hedge_execution, lending_execution needed
```

### 2. Venue Configuration Rules
Rules for what configuration needs to be present for each strategy mode:

```yaml
# configs/venue_requirements.yaml
strategy_requirements:
  pure_lending:
    required_venues: ["aave", "alchemy"]
    optional_venues: []
  
  btc_basis:
    required_venues: ["binance", "alchemy"]
    optional_venues: ["bybit", "okx"]
  
  eth_staking:
    required_venues: ["lido", "instadapp", "alchemy"]
    optional_venues: []
  
  eth_leveraged:
    required_venues: ["aave", "lido", "instadapp", "alchemy"]
    optional_venues: ["binance", "bybit", "okx"]
```

## IMPLEMENTATION REQUIREMENTS

### 1. Venue Client Factory
```python
class VenueClientFactory:
    """Factory for creating venue clients."""
    
    @staticmethod
    def create_client(venue_name: str, config, environment: str) -> VenueClient:
        """Create venue client for specific venue and environment."""
        if venue_name == 'binance':
            return BinanceClient(config, environment)
        elif venue_name == 'aave':
            return AaveClient(config, environment)
        elif venue_name == 'alchemy':
            return AlchemyClient(config, environment)
        elif venue_name == 'lido':
            return LidoClient(config, environment)
        elif venue_name == 'instadapp':
            return InstadappClient(config, environment)
        else:
            raise ValueError(f"Unknown venue: {venue_name}")
```

### 2. Environment Manager
```python
class EnvironmentManager:
    """Manages environment configuration and venue client initialization."""
    
    def __init__(self, config):
        self.config = config
        self.environment = os.getenv('ENVIRONMENT', 'simulation')
        self.venue_clients = self._initialize_venue_clients()
    
    def _initialize_venue_clients(self):
        """Initialize all venue clients for current environment."""
        venue_clients = {}
        for venue_name in self._get_required_venues():
            venue_clients[venue_name] = VenueClientFactory.create_client(
                venue_name, self.config, self.environment
            )
        return venue_clients
    
    def _get_required_venues(self):
        """Get list of required venues for current strategy mode."""
        # This would be determined by the current strategy mode
        return ['binance', 'aave', 'alchemy', 'lido', 'instadapp']
```

## VALIDATION REQUIREMENTS

### 1. Venue Configuration Validation
- [ ] All required venues have configuration for current environment
- [ ] All venue clients can be initialized successfully
- [ ] Environment variables are properly set
- [ ] Venue-specific credentials are available

### 2. Strategy Mode Validation
- [ ] Strategy mode has required venue configurations
- [ ] Optional venue configurations are properly marked
- [ ] Venue requirements are met for strategy mode
- [ ] No unnecessary venue configurations

### 3. Environment Validation
- [ ] Environment is properly set via environment variables
- [ ] All venue clients are in correct mode (live/testnet/simulation)
- [ ] Mixed environment configurations work correctly
- [ ] Transition from simulation to testnet to live is smooth

## SUCCESS CRITERIA
- [ ] Venue-based execution architecture implemented
- [ ] Action type to venue mapping works correctly
- [ ] All venue clients support live/testnet/simulation modes
- [ ] Environment configuration is flexible and configurable
- [ ] Strategy modes only have required venue configurations
- [ ] Smooth transition from backtest to live trading
- [ ] Mixed environment support works correctly
- [ ] Venue client factory and environment manager implemented

