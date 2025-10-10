# Execution Interfaces Component Specification

## Purpose
Venue-specific execution clients that handle actual trade execution, order management, and API interactions for CEX, DEX, and OnChain protocols.                

## 📚 **Canonical Sources**

- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](../MODES.md) - Canonical strategy mode definitions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

## Responsibilities
1. Execute venue-specific API calls (live) or simulations (backtest)
2. Handle order management (create, cancel, modify)
3. Parse venue responses into standardized format
4. Return execution deltas (net position changes)
5. MODE-AWARE: Real execution (live) vs simulated (backtest)

## Interface Types

### 1. CEXExecutionInterface
Binance, Hyperliquid (spot + perp)
- **Spot Trading**: Buy/sell spot assets
- **Perp Trading**: Open/close perpetual positions
- **Order Management**: Create, cancel, modify orders
- **Balance Management**: Query balances, transfer funds

### 2. DEXExecutionInterface
Uniswap, Curve (swaps)
- **Token Swaps**: Execute token-to-token swaps
- **Liquidity Management**: Add/remove liquidity
- **Price Impact**: Calculate and minimize price impact
- **Gas Optimization**: Optimize gas usage for swaps

### 3. OnChainExecutionInterface
AAVE, Morpho, Lido, EigenLayer (supply, borrow, stake)
- **Supply Actions**: Supply assets to protocols
- **Borrow Actions**: Borrow assets from protocols
- **Staking Actions**: Stake assets for rewards
- **Atomic Transactions**: Chain multiple actions atomically

## State
- current_orders: Dict[str, Dict] (active orders by order_id)
- execution_history: List[Dict] (for debugging)
- orders_executed: int
- orders_failed: int
- last_execution_timestamp: pd.Timestamp

## Component References (Set at Init)
The following are set once during initialization and NEVER passed as runtime parameters:

- data_provider: DataProvider (reference, uses shared clock for pricing)
- config: Dict (reference, venue-specific settings)
- execution_mode: str (BASIS_EXECUTION_MODE)

These references are stored in __init__ and used throughout component lifecycle.
Components NEVER receive these as method parameters during runtime.

## Core Methods (per interface)

### execute_spot_trade(timestamp: pd.Timestamp, instruction: Dict) -> Dict
Execute spot trade on CEX.

Parameters:
- timestamp: Current loop timestamp
- instruction: Spot trade instruction

Returns:
- Dict: Execution deltas (net position changes)

### execute_perp_trade(timestamp: pd.Timestamp, instruction: Dict) -> Dict
Execute perpetual trade on CEX.

Parameters:
- timestamp: Current loop timestamp
- instruction: Perp trade instruction

Returns:
- Dict: Execution deltas (net position changes)

### execute_swap(timestamp: pd.Timestamp, instruction: Dict) -> Dict
Execute token swap on DEX.

Parameters:
- timestamp: Current loop timestamp
- instruction: Swap instruction

Returns:
- Dict: Execution deltas (net position changes)

### execute_supply(timestamp: pd.Timestamp, instruction: Dict) -> Dict
Execute supply action on OnChain protocol.

Parameters:
- timestamp: Current loop timestamp
- instruction: Supply instruction

Returns:
- Dict: Execution deltas (net position changes)

### execute_borrow(timestamp: pd.Timestamp, instruction: Dict) -> Dict
Execute borrow action on OnChain protocol.

Parameters:
- timestamp: Current loop timestamp
- instruction: Borrow instruction

Returns:
- Dict: Execution deltas (net position changes)

## Data Access Pattern

Components query data using shared clock:
```python
def execute_spot_trade(self, timestamp: pd.Timestamp, instruction: Dict):
    # Query data with timestamp (data <= timestamp guaranteed)
    market_data = self.data_provider.get_data(timestamp)
    
    # Get current price for execution
    price = market_data['prices'][instruction['symbol']]
    
    # Execute trade based on mode
    if self.execution_mode == 'backtest':
        return self._execute_backtest_trade(instruction, price)
    elif self.execution_mode == 'live':
        return self._execute_live_trade(instruction, price)
```

NEVER pass market_data as parameter between components.
NEVER cache market_data across timestamps.

## Mode-Specific Behavior

### Backtest Mode
```python
def _execute_backtest_trade(self, instruction: Dict, price: float) -> Dict:
    # Simulate execution using data_provider.get_data(timestamp)
    symbol = instruction['symbol']
    side = instruction['side']
    amount = instruction['amount']
    
    # Calculate execution deltas
    if side == 'buy':
        deltas = {
            'tokens': {symbol: amount},
            'usd': -amount * price
        }
    else:  # sell
        deltas = {
            'tokens': {symbol: -amount},
            'usd': amount * price
        }
    
    return deltas
```

### Live Mode
```python
def _execute_live_trade(self, instruction: Dict, price: float) -> Dict:
    # Real API calls to venues
    venue = instruction['venue']
    symbol = instruction['symbol']
    side = instruction['side']
    amount = instruction['amount']
    
    # Execute real trade
    order_response = self._submit_order(venue, symbol, side, amount)
    
    # Parse response into deltas
    deltas = self._parse_order_response(order_response)
    
    return deltas
```

## Integration Points

### Called BY
- ExecutionInterfaceManager (instruction routing): interface.execute_trade(timestamp, instruction)

### Calls TO
- External venue APIs (live): Real API calls to venues
- DataProvider (backtest): data_provider.get_data(timestamp) for simulations

### Communication
- Direct method calls ONLY
- NO event publishing
- NO Redis/message queues
- NO async/await in internal methods

## Error Handling

### Backtest Mode
- **Fail fast**: Fail fast and pass failure down codebase
- **Immediate feedback**: Errors should be immediately visible
- **Simulated execution**: All executions are simulated
- **No retries**: Not applicable in backtest mode

### Live Mode
- **Retry logic**: Wait 0.1s, retry with exponential backoff
- **Max attempts**: Maximum 3 attempts per order
- **Error logging**: Log error and pass failure down after max attempts
- **Real execution**: All executions are real API calls

## Configuration Parameters

### From Config
- venue_configs: Dict (venue-specific settings)
- api_keys: Dict (API credentials for live mode)
- rate_limits: Dict (rate limiting settings)
- max_retry_attempts: int = 3
- retry_delay_seconds: float = 0.1

### Environment Variables
- BASIS_EXECUTION_MODE: 'backtest' | 'live' (controls execution behavior)

## Code Structure Example

```python
class CEXExecutionInterface:
    def __init__(self, venue: str, config: Dict, data_provider: DataProvider, execution_mode: str):
        # Store references (NEVER modified)
        self.venue = venue
        self.config = config
        self.data_provider = data_provider
        self.execution_mode = execution_mode
        
        # Initialize component-specific state
        self.current_orders = {}
        self.execution_history = []
        self.orders_executed = 0
        self.orders_failed = 0
        self.last_execution_timestamp = None
        
        # Initialize API client for live mode
        if self.execution_mode == 'live':
            self.api_client = self._initialize_api_client()
    
    def execute_spot_trade(self, timestamp: pd.Timestamp, instruction: Dict) -> Dict:
        """Execute spot trade on CEX."""
        # Store current execution
        self.last_execution_timestamp = timestamp
        
        try:
            # Query market data
            market_data = self.data_provider.get_data(timestamp)
            price = market_data['prices'][instruction['symbol']]
            
            # Execute based on mode
            if self.execution_mode == 'backtest':
                deltas = self._execute_backtest_spot_trade(instruction, price)
            elif self.execution_mode == 'live':
                deltas = self._execute_live_spot_trade(instruction, price)
            
            # Update statistics
            self.orders_executed += 1
            self.execution_history.append({
                'timestamp': timestamp,
                'venue': self.venue,
                'instruction': instruction,
                'success': True,
                'deltas': deltas
            })
            
            return deltas
            
        except Exception as e:
            # Update statistics
            self.orders_failed += 1
            self.execution_history.append({
                'timestamp': timestamp,
                'venue': self.venue,
                'instruction': instruction,
                'success': False,
                'error': str(e)
            })
            raise
    
    def execute_perp_trade(self, timestamp: pd.Timestamp, instruction: Dict) -> Dict:
        """Execute perpetual trade on CEX."""
        # Similar structure to execute_spot_trade
        pass
    
    def _execute_backtest_spot_trade(self, instruction: Dict, price: float) -> Dict:
        """Execute simulated spot trade."""
        symbol = instruction['symbol']
        side = instruction['side']
        amount = instruction['amount']
        
        # Calculate execution deltas
        if side == 'buy':
            deltas = {
                'tokens': {symbol: amount},
                'usd': -amount * price
            }
        else:  # sell
            deltas = {
                'tokens': {symbol: -amount},
                'usd': amount * price
            }
        
        return deltas
    
    def _execute_live_spot_trade(self, instruction: Dict, price: float) -> Dict:
        """Execute real spot trade."""
        # Submit real order
        order_response = self.api_client.submit_order(
            symbol=instruction['symbol'],
            side=instruction['side'],
            amount=instruction['amount'],
            order_type='market'
        )
        
        # Parse response into deltas
        deltas = self._parse_order_response(order_response)
        
        return deltas
    
    def _initialize_api_client(self):
        """Initialize API client for live mode."""
        # Initialize venue-specific API client
        if self.venue == 'binance':
            return BinanceClient(self.config['api_key'], self.config['api_secret'])
        elif self.venue == 'hyperliquid':
            return HyperliquidClient(self.config['api_key'])
        else:
            raise ValueError(f"Unknown venue: {self.venue}")
    
    def _parse_order_response(self, order_response: Dict) -> Dict:
        """Parse order response into execution deltas."""
        # Parse venue-specific response format
        return {
            'tokens': order_response['tokens'],
            'usd': order_response['usd_value']
        }
    
    def get_execution_status(self) -> Dict:
        """Get current execution status."""
        return {
            'status': 'healthy',
            'venue': self.venue,
            'orders_executed': self.orders_executed,
            'orders_failed': self.orders_failed,
            'execution_mode': self.execution_mode,
            'active_orders': len(self.current_orders)
        }
```

## Related Documentation
- [Reference-Based Architecture](../REFERENCE_ARCHITECTURE.md)
- [Shared Clock Pattern](../SHARED_CLOCK_PATTERN.md)
- [Request Isolation Pattern](../REQUEST_ISOLATION_PATTERN.md)
- [Execution Interface Manager Specification](07_EXECUTION_INTERFACE_MANAGER.md)