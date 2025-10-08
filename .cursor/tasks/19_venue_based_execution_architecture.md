# VENUE-BASED EXECUTION ARCHITECTURE

## OVERVIEW
Execution manager is venue-centric, with configuration mapping action types to venues for each strategy. Each venue needs clients with live, testnet, and simulation modes for smooth transition from backtest to live trading.

## VENUE CONFIGURATION ARCHITECTURE

### 1. Action Type to Venue Mapping
Each strategy mode needs configuration that maps action types to specific venues:

```yaml
# configs/modes/btc_basis.yaml
venues:
  hedge_execution:
    primary: "binance"
    hedge_allocation: 0.5  # 50% hedge allocation to binance
  
  staking_execution:
    primary: "lido"  # lst_type determines staking venue
    lst_type: "lido"
  
  flash_loan_execution:
    primary: "instadapp"
    use_flash_loan: true  # Whether CAN use instadapp for atomic flash loan entries
  
  unwind_execution:
    primary: "instadapp"
    unwind_mode: "flash_loan"  # Whether support flash loans on way out (for staking strategies)
  
  lending_execution:
    primary: "aave"
    on_chain_leverage_venue: "aave"  # For borrow and lending
  
  wallet_transfer:
    primary: "alchemy"
    wallet_client: "alchemy"  # For wallet transfers
```

### 2. Venue-Specific Configuration
Each venue needs configuration for different environments:

```yaml
# configs/venues/binance.yaml
environments:
  live:
    base_url: "https://api.binance.com"
    api_key: "${BINANCE_LIVE_API_KEY}"
    secret_key: "${BINANCE_LIVE_SECRET_KEY}"
    testnet: false
  
  testnet:
    base_url: "https://testnet.binance.vision"
    api_key: "${BINANCE_TESTNET_API_KEY}"
    secret_key: "${BINANCE_TESTNET_SECRET_KEY}"
    testnet: true
  
  simulation:
    base_url: "https://testnet.binance.vision"  # Use testnet for simulation
    api_key: "${BINANCE_TESTNET_API_KEY}"
    secret_key: "${BINANCE_TESTNET_SECRET_KEY}"
    testnet: true
    simulation_mode: true

# configs/venues/aave.yaml
environments:
  live:
    network: "ethereum"
    contract_address: "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9"
    rpc_url: "${ETHEREUM_RPC_URL}"
    testnet: false
  
  testnet:
    network: "ethereum"
    contract_address: "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9"  # Testnet address
    rpc_url: "${ETHEREUM_TESTNET_RPC_URL}"
    testnet: true
  
  simulation:
    network: "ethereum"
    contract_address: "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9"
    rpc_url: "${ETHEREUM_TESTNET_RPC_URL}"
    testnet: true
    simulation_mode: true

# configs/venues/alchemy.yaml
environments:
  live:
    network: "ethereum"
    rpc_url: "${ALCHEMY_LIVE_RPC_URL}"
    api_key: "${ALCHEMY_LIVE_API_KEY}"
    testnet: false
  
  testnet:
    network: "ethereum"
    rpc_url: "${ALCHEMY_TESTNET_RPC_URL}"
    api_key: "${ALCHEMY_TESTNET_API_KEY}"
    testnet: true
  
  simulation:
    network: "ethereum"
    rpc_url: "${ALCHEMY_TESTNET_RPC_URL}"
    api_key: "${ALCHEMY_TESTNET_API_KEY}"
    testnet: true
    simulation_mode: true
```

## VENUE CLIENT ARCHITECTURE

### 1. Venue Client Interface
Each venue needs a client that supports multiple modes:

```python
class VenueClient:
    """Base class for venue clients."""
    
    def __init__(self, config, environment):
        self.config = config
        self.environment = environment  # live, testnet, or simulation
        self.venue_config = self._load_venue_config()
    
    def _load_venue_config(self):
        """Load venue-specific configuration for current environment."""
        env_config = self.config.get(f'venues.{self.venue_name}.environments.{self.environment}')
        return env_config
    
    def is_live(self) -> bool:
        """Check if client is in live mode."""
        return self.environment == 'live'
    
    def is_testnet(self) -> bool:
        """Check if client is in testnet mode."""
        return self.environment == 'testnet'
    
    def is_simulation(self) -> bool:
        """Check if client is in simulation mode."""
        return self.environment == 'simulation'

class BinanceClient(VenueClient):
    """Binance venue client."""
    
    def __init__(self, config, environment):
        self.venue_name = 'binance'
        super().__init__(config, environment)
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Binance client based on environment."""
        if self.is_live():
            return ccxt.binance({
                'apiKey': self.venue_config['api_key'],
                'secret': self.venue_config['secret_key'],
                'sandbox': False
            })
        else:  # testnet or simulation
            return ccxt.binance({
                'apiKey': self.venue_config['api_key'],
                'secret': self.venue_config['secret_key'],
                'sandbox': True
            })

class AaveClient(VenueClient):
    """Aave venue client."""
    
    def __init__(self, config, environment):
        self.venue_name = 'aave'
        super().__init__(config, environment)
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Aave client based on environment."""
        return Web3(Web3.HTTPProvider(self.venue_config['rpc_url']))

class AlchemyClient(VenueClient):
    """Alchemy venue client."""
    
    def __init__(self, config, environment):
        self.venue_name = 'alchemy'
        super().__init__(config, environment)
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Alchemy client based on environment."""
        return Web3(Web3.HTTPProvider(self.venue_config['rpc_url']))
```

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
# .env.local (for local development)
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

