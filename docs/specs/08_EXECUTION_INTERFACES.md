# Component Spec: Execution Interfaces 🚀

**Component**: Execution Interfaces  
**Responsibility**: Unified execution abstraction for backtest and live modes  
**Priority**: ⭐⭐⭐ CRITICAL (Enables live trading)  
**Backend File**: `backend/src/basis_strategy_v1/core/interfaces/` ✅ **IMPLEMENTED**

---

## 🎯 **Purpose**

Provide a unified execution interface that seamlessly switches between backtest (simulated) and live (real) execution modes.

**Key Principles**:
- **Seamless Switching**: Same interface for backtest and live modes
- **Real Execution**: Live mode uses CCXT (CEX) and Web3.py (on-chain) for real trades
- **Simulated Execution**: Backtest mode uses validated calculators and market data
- **Unified Interface**: Single API for all execution operations regardless of mode
- **Component Integration**: Properly integrated with Position Monitor, Event Logger, and Data Provider

---

## 📊 **Data Structures**

### **Base Execution Interface** ✅ **IMPLEMENTED**

```python
class BaseExecutionInterface(ABC):
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        self.execution_mode = execution_mode
        self.config = config
        self.position_monitor = None
        self.event_logger = None
        self.data_provider = None
    
    def set_dependencies(self, position_monitor, event_logger, data_provider):
        """Set component dependencies."""
        self.position_monitor = position_monitor
        self.event_logger = event_logger
        self.data_provider = data_provider
    
    @abstractmethod
    async def execute_trade(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trade instruction."""
        pass
    
    @abstractmethod
    async def get_balance(self, asset: str, venue: Optional[str] = None) -> float:
        """Get current balance for an asset."""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str, venue: Optional[str] = None) -> Dict[str, Any]:
        """Get current position for a trading pair."""
        pass
    
    @abstractmethod
    async def cancel_all_orders(self, venue: Optional[str] = None) -> Dict[str, Any]:
        """Cancel all open orders."""
        pass
    
    @abstractmethod
    async def execute_transfer(self, instruction: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a cross-venue transfer."""
        pass
```

### **CEX Execution Interface** ✅ **IMPLEMENTED**

```python
class CEXExecutionInterface(BaseExecutionInterface):
    """CEX execution interface for centralized exchange trading."""
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        super().__init__(execution_mode, config)
        
        # Initialize exchange clients for live mode
        if execution_mode == 'live':
            self._init_exchange_clients()  # Initialize CCXT clients
        else:
            self.exchange_clients = {}
    
    def _init_exchange_clients(self):
        """Initialize CCXT exchange clients for live mode."""
        # Supports Binance, Bybit, OKX with API key configuration
        # Includes sandbox mode support and rate limiting
```

### **OnChain Execution Interface** ✅ **IMPLEMENTED**

```python
class OnChainExecutionInterface(BaseExecutionInterface):
    """On-chain execution interface for blockchain operations."""
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        super().__init__(execution_mode, config)
        
        # Initialize Web3 clients for live mode
        if execution_mode == 'live':
            self._init_web3_clients()  # Initialize Web3 clients
        else:
            self.web3_clients = {}
            self.contracts = {}
    
    def _init_web3_clients(self):
        """Initialize Web3 clients and contracts for live mode."""
        # Supports Ethereum mainnet via Alchemy
        # Includes contract initialization for AAVE, staking protocols
```

---

## 🔄 **Execution Flow**

### **Backtest Mode**

```python
# 1. Simulated execution using market data
result = await interface.execute_trade(instruction, market_data)

# 2. Calculate execution costs and slippage
execution_cost = self._get_execution_cost(instruction, market_data)
slippage = execution_cost / 10000  # Convert bps to decimal

# 3. Simulate fill price with slippage
if side in ['BUY', 'LONG']:
    fill_price = market_price * (1 + slippage)
else:
    fill_price = market_price * (1 - slippage)

# 4. Log event and update position monitor
self._log_execution_event('CEX_TRADE_EXECUTED', result)
self._update_position_monitor(changes)
```

### **Live Mode**

```python
# 1. Real execution using CCXT/Web3
if trade_type == 'SPOT':
    order = await exchange.create_market_order(symbol, side, amount)
else:  # PERP
    order = await exchange.create_market_order(symbol, side, amount, None, None, {'type': 'market'})

# 2. Extract real execution data
result = {
    'status': 'FILLED',
    'amount': order.get('filled', amount),
    'price': order.get('average', order.get('price', 0.0)),
    'order_id': order.get('id', ''),
    'execution_mode': 'live'
}

# 3. Log event and update position monitor
self._log_execution_event('CEX_TRADE_EXECUTED', result)
self._update_position_monitor(changes)
```

---

## 🏗️ **Factory Pattern**

### **Execution Interface Factory** ✅ **IMPLEMENTED**

```python
class ExecutionInterfaceFactory:
    @staticmethod
    def create_interface(interface_type: str, execution_mode: str, config: Dict[str, Any]) -> BaseExecutionInterface:
        """Create a single execution interface."""
        if interface_type == 'cex':
            return CEXExecutionInterface(execution_mode, config)
        elif interface_type == 'onchain':
            return OnChainExecutionInterface(execution_mode, config)
        elif interface_type == 'transfer':
            return TransferExecutionInterface(execution_mode, config)
        else:
            raise ValueError(f"Unsupported interface type: {interface_type}")
    
    @staticmethod
    def create_all_interfaces(execution_mode: str, config: Dict[str, Any]) -> Dict[str, BaseExecutionInterface]:
        """Create all execution interfaces for the given mode."""
        interfaces = {}
        
        interfaces['cex'] = ExecutionInterfaceFactory.create_interface('cex', execution_mode, config)
        interfaces['onchain'] = ExecutionInterfaceFactory.create_interface('onchain', execution_mode, config)
        interfaces['transfer'] = ExecutionInterfaceFactory.create_interface('transfer', execution_mode, config)
        
        return interfaces
    
    @staticmethod
    def set_interface_dependencies(interfaces: Dict[str, BaseExecutionInterface], 
                                 position_monitor, event_logger, data_provider):
        """Set dependencies for all interfaces."""
        for interface_type, interface in interfaces.items():
            if interface:
                interface.set_dependencies(position_monitor, event_logger, data_provider)
```

### **EventDrivenStrategyEngine Integration** ✅ **IMPLEMENTED**

```python
class EventDrivenStrategyEngine:
    def __init__(self, config):
        # Create execution interfaces using factory
        self.execution_interfaces = ExecutionInterfaceFactory.create_all_interfaces(
            execution_mode=self.execution_mode,
            config=self.config
        )
        
        # Set dependencies for execution interfaces
        ExecutionInterfaceFactory.set_interface_dependencies(
            interfaces=self.execution_interfaces,
            position_monitor=self.position_monitor,
            event_logger=self.event_logger,
            data_provider=self.data_provider
        )
        
        # Set Position Update Handler for tight loop management
        self._set_position_update_handler_on_interfaces()
    
    def _set_position_update_handler_on_interfaces(self):
        """Set Position Update Handler on all execution interfaces for tight loop management."""
        for interface_type, interface in self.execution_interfaces.items():
            if interface:
                interface.position_update_handler = self.position_update_handler
    
    async def execute_decision(self, decision, timestamp, execution_interfaces, market_data):
        """Execute strategy decision using execution interfaces."""
        # Delegate all execution to Strategy Manager with execution interfaces
        await self.strategy_manager.execute_decision(
            decision=decision,
            timestamp=timestamp,
            execution_interfaces=execution_interfaces,
            market_data=market_data
        )
```

---

## 🔧 **Configuration**

### **Live Mode Configuration**

```python
# CEX API Keys
config = {
    'binance_api_key': 'your_binance_api_key',
    'binance_secret': 'your_binance_secret',
    'binance_sandbox': False,
    
    'bybit_api_key': 'your_bybit_api_key',
    'bybit_secret': 'your_bybit_secret',
    'bybit_sandbox': False,
    
    'okx_api_key': 'your_okx_api_key',
    'okx_secret': 'your_okx_secret',
    'okx_passphrase': 'your_okx_passphrase',
    'okx_sandbox': False,
    
    # Web3 Configuration
    'alchemy_api_key': 'your_alchemy_api_key',
    'wallet_private_key': 'your_wallet_private_key',
    'wallet_address': 'your_wallet_address'
}
```

### **Backtest Mode Configuration**

```python
# No API keys needed for backtest mode
config = {
    'execution_mode': 'backtest',
    'data': {'data_dir': 'data/'},
    'initial_capital': 100000
}
```

---

## 🧪 **Testing**

### **Interface Testing**

```python
# Test backtest mode
config_backtest = {'execution_mode': 'backtest', 'data': {'data_dir': 'data/'}}
engine_backtest = EventDrivenStrategyEngine(config_backtest)

# Test live mode
config_live = {'execution_mode': 'live', 'binance_api_key': '...'}
engine_live = EventDrivenStrategyEngine(config_live)

# Test execution
instruction = {
    'venue_type': 'cex',
    'venue': 'binance',
    'trade_type': 'SPOT',
    'pair': 'ETH/USDT',
    'side': 'BUY',
    'amount': 1.0
}

market_data = {'eth_usd_price': 3000.0, 'binance_spot_price': 3000.0}
result = await engine.execute_trade_with_interface(instruction, market_data)
```

---

## 📈 **Benefits**

### **Seamless Mode Switching**
- Same API for backtest and live execution
- No code changes needed when switching modes
- Consistent behavior across modes

### **Real Trading Capability**
- Live mode uses real CCXT and Web3.py clients
- Proper error handling and logging
- Real-time market data integration

### **Simulated Trading**
- Backtest mode uses validated calculators
- Realistic execution costs and slippage
- Historical market data integration

### **Component Integration**
- Proper dependency injection
- Event logging for all operations
- Position monitor updates
- Data provider integration

---

## 🚀 **Usage Examples**

### **CEX Trading**

```python
# Spot trade
cex_instruction = {
    'venue_type': 'cex',
    'venue': 'binance',
    'trade_type': 'SPOT',
    'pair': 'ETH/USDT',
    'side': 'BUY',
    'amount': 1.0
}

result = await engine.execute_trade_with_interface(cex_instruction, market_data)

# Perpetual trade
perp_instruction = {
    'venue_type': 'cex',
    'venue': 'bybit',
    'trade_type': 'PERP',
    'pair': 'ETHUSDT-PERP',
    'side': 'LONG',
    'amount': 1.0
}

result = await engine.execute_trade_with_interface(perp_instruction, market_data)
```

### **On-Chain Operations**

```python
# AAVE supply
aave_instruction = {
    'venue_type': 'onchain',
    'operation': 'AAVE_SUPPLY',
    'token': 'ETH',
    'amount': 1.0
}

result = await engine.execute_trade_with_interface(aave_instruction, market_data)

# Staking
staking_instruction = {
    'venue_type': 'onchain',
    'operation': 'STAKE',
    'token': 'ETH',
    'amount': 1.0
}

result = await engine.execute_trade_with_interface(staking_instruction, market_data)
```

---

## 🔍 **Error Handling**

### **Live Mode Errors**

```python
try:
    result = await interface.execute_trade(instruction, market_data)
except Exception as e:
    logger.error(f"Failed to execute live trade: {e}")
    # Graceful degradation or retry logic
```

### **Backtest Mode Errors**

```python
try:
    result = await interface.execute_trade(instruction, market_data)
except Exception as e:
    logger.error(f"Failed to execute backtest trade: {e}")
    # Use fallback execution logic
```

---

## 📋 **Implementation Status** ✅ **FULLY IMPLEMENTED**

- ✅ **Base Execution Interface**: Abstract base class with required methods and dependency injection
- ✅ **CEX Execution Interface**: CCXT integration for live mode, simulation for backtest, supports Binance/Bybit/OKX
- ✅ **OnChain Execution Interface**: Web3.py integration for live mode, simulation for backtest, Alchemy support
- ✅ **Transfer Execution Interface**: Cross-venue transfer capabilities with sophisticated transfer logic
- ✅ **Execution Interface Factory**: Factory pattern for interface creation with error handling
- ✅ **EventDrivenStrategyEngine Integration**: Seamless integration with strategy engine and position update handler
- ✅ **Dependency Injection**: Proper component wiring with position monitor, event logger, data provider
- ✅ **Error Handling**: Comprehensive error handling and logging with dedicated loggers
- ✅ **Position Update Handler Integration**: Tight loop management for position → exposure → risk → P&L flow
- ✅ **Transaction Confirmation**: Live mode transaction confirmation with retry logic

---

## 🎯 **Next Steps**

1. **API Key Management**: Secure API key storage and rotation
2. **Rate Limiting**: Implement rate limiting for live API calls
3. **Order Management**: Advanced order types and management
4. **Slippage Protection**: Dynamic slippage protection based on market conditions
5. **Gas Optimization**: Gas price optimization for on-chain operations
6. **Multi-Venue Execution**: Cross-venue arbitrage and execution
7. **Risk Controls**: Pre-trade risk checks and limits
8. **Monitoring**: Real-time execution monitoring and alerting
