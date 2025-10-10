# Execution Interface Manager Component Specification

## Purpose
Routes 3 types of instructions (wallet_transfer, smart_contract_action, cex_trade) to appropriate venue execution interfaces (CEX, DEX, OnChain).               

## 📚 **Canonical Sources**

- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](../MODES.md) - Canonical strategy mode definitions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

## Responsibilities
1. Parse instruction type from instruction block
2. Route to correct venue interface (Binance, Hyperliquid, Uniswap, AAVE, etc.)
3. Handle atomic chaining for smart contract actions
4. Return execution deltas (net position changes) to Execution Manager

## State
- current_instruction: Dict
- routing_history: List[Dict] (for debugging)
- instructions_routed: int
- instructions_failed: int
- venue_interfaces: Dict[str, ExecutionInterface]

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- cex_execution_interfaces: Dict[str, CEXExecutionInterface] (keyed by venue: 'binance', 'hyperliquid')
- dex_execution_interfaces: Dict[str, DEXExecutionInterface] (keyed by venue: 'uniswap', 'curve')
- onchain_execution_interfaces: Dict[str, OnChainExecutionInterface] (keyed by protocol: 'aave', 'morpho')
- data_provider: DataProvider (reference, uses shared clock for pricing)
- config: Dict (reference, venue-specific settings)
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
None

### Environment Variable Access Pattern
```python
def __init__(self, ...):
    # Read env vars ONCE at initialization
    self.execution_mode = os.getenv('BASIS_EXECUTION_MODE', 'backtest')
    # NEVER read env vars during runtime loops
```

### Behavior NOT Determinable from Environment Variables
- Instruction routing logic (hard-coded algorithms)
- Venue interface selection (hard-coded mapping)
- Execution delta aggregation (hard-coded logic)

## Config Fields Used

### Universal Config (All Components)
- `strategy_mode`: str - e.g., 'eth_basis', 'pure_lending'
- `share_class`: str - 'usdt_stable' | 'eth_directional'
- `initial_capital`: float - Starting capital

### Component-Specific Config
- `venue_timeout`: int - Timeout for venue API calls
  - **Usage**: Determines how long to wait for venue responses
  - **Default**: 15 (seconds)
  - **Validation**: Must be > 0 and < 120

- `max_retries_per_venue`: int - Maximum retries per venue
  - **Usage**: Determines retry behavior for venue failures
  - **Default**: 3
  - **Validation**: Must be > 0 and < 10

### Config Access Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str, instruction_block: Dict = None):
    # Read config fields (NEVER modify)
    timeout = self.config.get('venue_timeout', 15)
    max_retries = self.config.get('max_retries_per_venue', 3)
```

### Behavior NOT Determinable from Config
- Instruction type parsing (hard-coded logic)
- Venue interface routing (hard-coded mapping)
- Execution delta aggregation (hard-coded algorithms)

## Data Provider Queries

### Data Types Requested
`data = self.data_provider.get_data(timestamp)`

#### Market Data
- `prices`: Dict[str, float] - Token prices in USD
  - **Tokens needed**: ETH, USDT, BTC, LST tokens
  - **Update frequency**: 1min
  - **Usage**: Price validation for execution

### Query Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str, instruction_block: Dict = None):
    data = self.data_provider.get_data(timestamp)
    prices = data['market_data']['prices']
```

### Data NOT Available from DataProvider
None - all data comes from DataProvider

## Core Methods

### update_state(timestamp: pd.Timestamp, trigger_source: str, instruction_block: Dict = None)
Main entry point for instruction routing.

Parameters:
- timestamp: Current loop timestamp (from EventDrivenStrategyEngine)
- trigger_source: 'execution_manager' | 'manual' | 'retry'
- instruction_block: Dict (optional) - instruction block from Execution Manager

Behavior:
1. If instruction_block provided: Route instruction to appropriate interface
2. Aggregate deltas from all sub-instructions
3. Return net position changes to Execution Manager
4. NO async/await: Synchronous execution only

Returns:
- Dict: Execution deltas (net position changes)

### route_instruction(timestamp: pd.Timestamp, instruction_block: Dict) -> Dict
Route instruction block to appropriate venue interface.

Parameters:
- timestamp: Current loop timestamp
- instruction_block: Instruction block from Execution Manager

Returns:
- Dict: Execution deltas (net position changes)

Behavior:
1. Parse instruction_type from block
2. Route to appropriate interface
3. Aggregate deltas from all sub-instructions
4. Return net position changes

### _route_cex_trade(instruction: Dict) -> Dict
Route CEX trade instruction to appropriate CEX interface.

Parameters:
- instruction: CEX trade instruction

Returns:
- Dict: Execution deltas from CEX trade

### _route_smart_contract_action(instruction: Dict) -> Dict
Route smart contract action to appropriate OnChain interface.

Parameters:
- instruction: Smart contract action instruction

Returns:
- Dict: Execution deltas from smart contract action

### _route_wallet_transfer(instruction: Dict) -> Dict
Route wallet transfer to appropriate interface.

Parameters:
- instruction: Wallet transfer instruction

Returns:
- Dict: Execution deltas from wallet transfer

## Instruction Types

### 1. wallet_transfer
Move tokens between wallets (e.g., CEX → wallet → protocol)
```python
{
    'instruction_type': 'wallet_transfer',
    'from_venue': 'binance',
    'to_venue': 'wallet',
    'token': 'USDT',
    'amount': 1000.0,
    'estimated_deltas': {
        'binance': {'USDT': -1000.0},
        'wallet': {'USDT': 1000.0}
    }
}
```

### 2. smart_contract_action
DeFi interactions (supply, borrow, stake, swap) - can be atomically chained
```python
{
    'instruction_type': 'smart_contract_action',
    'protocol': 'aave',
    'action': 'supply',
    'token': 'USDT',
    'amount': 1000.0,
    'estimated_deltas': {
        'aave': {'aUSDT': 1000.0, 'USDT': -1000.0}
    }
}
```

### 3. cex_trade
CEX spot or perp trades
```python
{
    'instruction_type': 'cex_trade',
    'venue': 'binance',
    'trade_type': 'spot',
    'side': 'sell',
    'symbol': 'ETHUSDT',
    'amount': 1.0,
    'estimated_deltas': {
        'binance': {'ETH': -1.0, 'USDT': 3300.0}
    }
}
```

## Data Access Pattern

Components query data using shared clock:
```python
def route_instruction(self, timestamp: pd.Timestamp, instruction_block: Dict):
    # Query data with timestamp (data <= timestamp guaranteed)
    market_data = self.data_provider.get_data(timestamp)
    
    # Parse instruction type
    instruction_type = instruction_block['instruction_type']
    
    # Route to appropriate interface
    if instruction_type == 'cex_trade':
        return self._route_cex_trade(instruction_block)
    elif instruction_type == 'smart_contract_action':
        return self._route_smart_contract_action(instruction_block)
    elif instruction_type == 'wallet_transfer':
        return self._route_wallet_transfer(instruction_block)
```

NEVER pass market_data as parameter between components.
NEVER cache market_data across timestamps.

## Mode-Aware Behavior

### Backtest Mode
```python
def _route_cex_trade(self, instruction: Dict):
    if self.execution_mode == 'backtest':
        # Simulate CEX trade execution
        venue = instruction['venue']
        interface = self.cex_execution_interfaces[venue]
        return interface.execute_backtest_trade(instruction)
```

### Live Mode
```python
def _route_cex_trade(self, instruction: Dict):
    elif self.execution_mode == 'live':
        # Execute real CEX trade
        venue = instruction['venue']
        interface = self.cex_execution_interfaces[venue]
        return interface.execute_live_trade(instruction)
```

## Integration Points

### Called BY
- ExecutionManager (instruction routing): execution_interface_manager.route_instruction(timestamp, instruction_block)

### Calls TO
- cex_execution_interfaces[venue].execute_trade(instruction) - CEX trade execution
- dex_execution_interfaces[venue].execute_swap(instruction) - DEX swap execution
- onchain_execution_interfaces[protocol].execute_action(instruction) - OnChain action execution

### Communication
- Direct method calls ONLY
- NO event publishing
- NO Redis/message queues
- NO async/await in internal methods

## Error Handling

### Backtest Mode
- **Fail fast**: Fail fast and pass failure down codebase
- **Immediate feedback**: Errors should be immediately visible
- **Stop execution**: Stop instruction routing on critical errors
- **Simulated execution**: All executions are simulated

### Live Mode
- **Retry logic**: Wait 0.1s, retry with exponential backoff
- **Max attempts**: Maximum 3 attempts per instruction
- **Error logging**: Log error and pass failure down after max attempts
- **Real execution**: All executions are real API calls

## Configuration Parameters

### From Config
- venue_configs: Dict (venue-specific settings)
- max_retry_attempts: int = 3
- retry_delay_seconds: float = 0.1
- enable_atomic_chaining: bool = True

### Environment Variables
- BASIS_EXECUTION_MODE: 'backtest' | 'live' (controls execution behavior)

## Code Structure Example

```python
class ExecutionInterfaceManager:
    def __init__(self, config: Dict, data_provider: DataProvider, execution_mode: str):
        # Store references (NEVER modified)
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Initialize venue interfaces
        self.cex_execution_interfaces = self._initialize_cex_interfaces()
        self.dex_execution_interfaces = self._initialize_dex_interfaces()
        self.onchain_execution_interfaces = self._initialize_onchain_interfaces()
        
        # Initialize component-specific state
        self.current_instruction = None
        self.routing_history = []
        self.instructions_routed = 0
        self.instructions_failed = 0
    
    def route_instruction(self, timestamp: pd.Timestamp, instruction_block: Dict) -> Dict:
        """Route instruction block to appropriate venue interface."""
        # Store current instruction
        self.current_instruction = instruction_block
        
        try:
            # Parse instruction type
            instruction_type = instruction_block['instruction_type']
            
            # Route to appropriate interface
            if instruction_type == 'cex_trade':
                deltas = self._route_cex_trade(instruction_block)
            elif instruction_type == 'smart_contract_action':
                deltas = self._route_smart_contract_action(instruction_block)
            elif instruction_type == 'wallet_transfer':
                deltas = self._route_wallet_transfer(instruction_block)
            else:
                raise ValueError(f"Unknown instruction type: {instruction_type}")
            
            # Update statistics
            self.instructions_routed += 1
            self.routing_history.append({
                'timestamp': timestamp,
                'instruction_type': instruction_type,
                'success': True,
                'deltas': deltas
            })
            
            return deltas
            
        except Exception as e:
            # Update statistics
            self.instructions_failed += 1
            self.routing_history.append({
                'timestamp': timestamp,
                'instruction_type': instruction_block.get('instruction_type', 'unknown'),
                'success': False,
                'error': str(e)
            })
            raise
    
    def _route_cex_trade(self, instruction: Dict) -> Dict:
        """Route CEX trade instruction to appropriate CEX interface."""
        venue = instruction['venue']
        interface = self.cex_execution_interfaces[venue]
        
        if self.execution_mode == 'backtest':
            return interface.execute_backtest_trade(instruction)
        elif self.execution_mode == 'live':
            return interface.execute_live_trade(instruction)
    
    def _route_smart_contract_action(self, instruction: Dict) -> Dict:
        """Route smart contract action to appropriate OnChain interface."""
        protocol = instruction['protocol']
        interface = self.onchain_execution_interfaces[protocol]
        
        if self.execution_mode == 'backtest':
            return interface.execute_backtest_action(instruction)
        elif self.execution_mode == 'live':
            return interface.execute_live_action(instruction)
    
    def _route_wallet_transfer(self, instruction: Dict) -> Dict:
        """Route wallet transfer to appropriate interface."""
        from_venue = instruction['from_venue']
        to_venue = instruction['to_venue']
        
        # Determine which interface to use
        if from_venue in self.cex_execution_interfaces:
            interface = self.cex_execution_interfaces[from_venue]
        elif to_venue in self.cex_execution_interfaces:
            interface = self.cex_execution_interfaces[to_venue]
        else:
            # Default to onchain interface for wallet-to-wallet transfers
            interface = self.onchain_execution_interfaces['wallet']
        
        if self.execution_mode == 'backtest':
            return interface.execute_backtest_transfer(instruction)
        elif self.execution_mode == 'live':
            return interface.execute_live_transfer(instruction)
    
    def _initialize_cex_interfaces(self) -> Dict[str, CEXExecutionInterface]:
        """Initialize CEX execution interfaces."""
        interfaces = {}
        for venue in self.config.get('venues', {}).get('cex', []):
            interfaces[venue] = CEXExecutionInterface(
                venue=venue,
                config=self.config['venues']['cex'][venue],
                data_provider=self.data_provider,
                execution_mode=self.execution_mode
            )
        return interfaces
    
    def _initialize_dex_interfaces(self) -> Dict[str, DEXExecutionInterface]:
        """Initialize DEX execution interfaces."""
        interfaces = {}
        for venue in self.config.get('venues', {}).get('dex', []):
            interfaces[venue] = DEXExecutionInterface(
                venue=venue,
                config=self.config['venues']['dex'][venue],
                data_provider=self.data_provider,
                execution_mode=self.execution_mode
            )
        return interfaces
    
    def _initialize_onchain_interfaces(self) -> Dict[str, OnChainExecutionInterface]:
        """Initialize OnChain execution interfaces."""
        interfaces = {}
        for protocol in self.config.get('venues', {}).get('onchain', []):
            interfaces[protocol] = OnChainExecutionInterface(
                protocol=protocol,
                config=self.config['venues']['onchain'][protocol],
                data_provider=self.data_provider,
                execution_mode=self.execution_mode
            )
        return interfaces
    
    def get_routing_status(self) -> Dict:
        """Get current routing status."""
        return {
            'status': 'healthy',
            'current_instruction': self.current_instruction,
            'instructions_routed': self.instructions_routed,
            'instructions_failed': self.instructions_failed,
            'execution_mode': self.execution_mode,
            'available_venues': {
                'cex': list(self.cex_execution_interfaces.keys()),
                'dex': list(self.dex_execution_interfaces.keys()),
                'onchain': list(self.onchain_execution_interfaces.keys())
            }
        }
```

## Related Documentation
- [Reference-Based Architecture](../REFERENCE_ARCHITECTURE.md)
- [Shared Clock Pattern](../SHARED_CLOCK_PATTERN.md)
- [Request Isolation Pattern](../REQUEST_ISOLATION_PATTERN.md)

### **Component Integration**
- [Execution Manager Specification](06_EXECUTION_MANAGER.md) - Provides instruction blocks for routing
- [Execution Interfaces Specification](08A_EXECUTION_INTERFACES.md) - Defines venue execution interfaces
- [Data Provider Specification](09_DATA_PROVIDER.md) - Provides market data for execution
- [Event Logger Specification](08_EVENT_LOGGER.md) - Logs execution routing events
- [Position Update Handler Specification](11_POSITION_UPDATE_HANDLER.md) - Receives execution deltas
