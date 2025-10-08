# Current Execution Workflow - Complete Map

## Full Workflow from Strategy Decision to Results Storage

### 1. **Event Engine Main Loop** (`event_driven_strategy_engine.py`)

```python
async def _process_timestep(timestamp, market_data, results):
    # 1. Get positions
    position_snapshot = position_monitor.get_snapshot()
    
    # 2. Calculate exposure  
    exposure = exposure_monitor.calculate_exposure(timestamp, position_snapshot, market_data)
    
    # 3. Assess risk
    risk_assessment = risk_monitor.assess_risk(exposure_data=exposure, market_data=market_data)
    
    # 4. Calculate P&L
    pnl = pnl_calculator.calculate_pnl(current_exposure=exposure, timestamp=timestamp)
    
    # 5. Make strategy decision
    strategy_decision = strategy_manager.make_strategy_decision(
        current_exposure=exposure,
        risk_assessment=risk_assessment, 
        config=config,
        market_data=market_data
    )
    
    # 6. Execute decision
    if strategy_decision['action'] != 'HOLD':
        await strategy_manager.execute_decision(
            decision=strategy_decision,
            timestamp=timestamp,
            execution_interfaces=execution_interfaces
        )
    
    # 7. Log events
    await event_logger.log_event(...)
    
    # 8. Store results
    results['pnl_history'].append(...)
```

### 2. **Strategy Manager Decision Flow** (`strategy_manager.py`)

#### **2a. Decision Making**
```python
def make_strategy_decision(current_exposure, risk_assessment, config, market_data):
    if mode == 'btc_basis':
        action = _btc_basis_decision(market_data, current_exposure)
        if action in ['INITIAL_SETUP', 'REBALANCE']:
            decision['desired_positions'] = _desired_btc_basis(action, params, current_exposure)
    return decision

def _btc_basis_decision(market_data, current_exposure):
    if _needs_initial_btc_basis_setup(current_exposure):
        return 'INITIAL_SETUP'
    elif _needs_btc_basis_rebalancing(current_exposure):
        return 'REBALANCE'
    return 'HOLD'

def _desired_btc_basis(change_type, params, current_exposure):
    if change_type == 'INITIAL_SETUP':
        return _calculate_initial_btc_basis_positions(params)
    elif change_type == 'REBALANCE':
        return _calculate_rebalance_btc_basis_positions(current_exposure)
```

#### **2b. Execution Orchestration**
```python
async def execute_decision(decision, timestamp, execution_interfaces):
    action = decision['action']
    
    if action == 'INITIAL_SETUP' and mode == 'btc_basis':
        await _execute_btc_basis_setup(decision, timestamp, execution_interfaces)
    # etc.

async def _execute_btc_basis_setup(decision, timestamp, execution_interfaces):
    desired_positions = decision['desired_positions']
    
    # Phase 1: Transfers
    for transfer in desired_positions['transfers']:
        if is_simple_wallet_to_cex_transfer(transfer):
            await _execute_simple_transfer(transfer, timestamp)  # Direct position monitor update
        else:
            await execution_interfaces['transfer'].execute_transfer(transfer)  # Complex routing
    
    # Phase 2: Spot Trades  
    for spot_trade in desired_positions['spot_trades']:
        await execution_interfaces['cex'].execute_trade(spot_trade)
    
    # Phase 3: Perp Trades
    for perp_trade in desired_positions['perp_trades']:
        await execution_interfaces['cex'].execute_trade(perp_trade)
```

### 3. **Execution Interface Flow** (New Architecture)

#### **3a. CEX Execution Interface** (`cex_execution_interface.py`)
```python
async def execute_trade(instruction, market_data):
    venue = instruction['venue']
    trade_type = instruction['trade_type']  # 'SPOT' or 'PERP'
    pair = instruction['pair']  # 'BTC/USDT' or 'BTCUSDT'
    side = instruction['side']  # 'BUY' or 'SELL'
    amount = instruction['amount']
    
    if execution_mode == 'backtest':
        result = await _execute_backtest_trade(instruction, market_data)
    else:
        result = await _execute_live_trade(instruction, market_data)
    
    # Update position monitor
    await _update_position_monitor(result)
    
    # Log event
    await _log_execution_event('CEX_TRADE_EXECUTED', result)
    
    return result
```

#### **3b. Transfer Execution Interface** (`transfer_execution_interface.py`)
```python
async def execute_transfer(instruction, market_data):
    # ONLY for complex transfers (AAVE↔EtherFi↔CEX)
    # Simple wallet→CEX transfers bypass this entirely
    
    source_venue = instruction['source_venue']
    target_venue = instruction['target_venue']
    amount_usd = instruction['amount_usd']
    
    # Use transfer manager for complex routing
    trades = await transfer_manager.execute_optimal_transfer(...)
    
    # Execute each trade in sequence
    for trade in trades:
        await _execute_transfer_trade(trade)
```

#### **3c. OnChain Execution Interface** (`onchain_execution_interface.py`)
```python
async def execute_trade(instruction, market_data):
    operation = instruction['operation']  # 'AAVE_SUPPLY', 'STAKE', 'ATOMIC_LEVERAGE'
    
    if operation == 'AAVE_SUPPLY':
        result = await _execute_aave_supply(instruction)
    elif operation == 'ATOMIC_LEVERAGE':
        result = await _execute_atomic_leverage(instruction)  # Flash loan support
    
    await _update_position_monitor(result)
    await _log_execution_event('ONCHAIN_OPERATION_EXECUTED', result)
    
    return result
```

### 4. **Legacy Components** (Currently Causing Confusion)

#### **4a. Legacy CEX Execution Manager** (`cex_execution_manager.py`)
- **Status**: Legacy, should be removed
- **Current Issue**: Overlaps with `cex_execution_interface.py`
- **Action**: Remove entirely, port any missing functionality to interface

#### **4b. Legacy OnChain Execution Manager** (`onchain_execution_manager.py`)  
- **Status**: Legacy, should be removed
- **Current Issue**: Overlaps with `onchain_execution_interface.py`
- **Action**: Remove entirely, port any missing functionality to interface

#### **4c. Transfer Manager** (`transfer_manager.py`)
- **Status**: Over-complex for simple operations
- **Current Issue**: Simple wallet→CEX transfers get over-engineered
- **Action**: Keep for complex scenarios only, bypass for simple transfers

## Current Issues & Root Causes

### 1. **`'trade_type'` Error**
- **Root Cause**: Field mapping inconsistency between components
- **Location**: CEX execution interface expecting different field names
- **Fix**: Standardize instruction format

### 2. **Transfer Complexity**
- **Root Cause**: Simple transfers routed through complex transfer manager
- **Location**: Transfer manager trying to create `Trade` objects for simple operations
- **Fix**: Bypass transfer manager for simple wallet→CEX transfers

### 3. **Async/Await Issues**
- **Root Cause**: Base execution interface methods not properly async
- **Location**: `_log_execution_event` and `_update_position_monitor` missing awaits
- **Fix**: Make base methods async and add awaits

### 4. **Dual Execution Systems**
- **Root Cause**: Legacy managers and new interfaces both active
- **Location**: Event Engine trying to use both systems
- **Fix**: Remove legacy managers entirely

## Instruction Format Standardization

### **Current Problem**: Multiple Formats
```python
# Strategy Manager generates:
{'venue': 'binance', 'symbol': 'BTCUSDT', 'side': 'buy', 'amount': 0.5}

# CEX Interface expects:
{'venue': 'binance', 'pair': 'BTC/USDT', 'side': 'BUY', 'trade_type': 'SPOT'}

# Transfer Interface expects:
{'source_venue': 'wallet', 'target_venue': 'binance', 'amount_usd': 40000}
```

### **Proposed Solution**: Unified Format
```python
@dataclass
class ExecutionInstruction:
    # Core fields (always present)
    type: str  # 'TRANSFER', 'SPOT_TRADE', 'PERP_TRADE', 'AAVE_SUPPLY', 'ATOMIC_LEVERAGE'
    execution_type: str  # 'simple', 'complex', 'atomic'
    timestamp_group: str  # For grouping related operations
    
    # Transfer fields (when type='TRANSFER')
    source_venue: Optional[str] = None
    target_venue: Optional[str] = None
    
    # Trade fields (when type='*_TRADE')
    venue: Optional[str] = None
    pair: Optional[str] = None  # Standardized format
    side: Optional[str] = None
    
    # Common fields
    token: Optional[str] = None
    amount: Optional[float] = None
    
    # Metadata
    purpose: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

## Complex Scenario Workflows

### **BTC Basis Setup** (Simple Sequential)
```
1. Transfer: wallet → binance ($40k USDT) [simple]
2. Transfer: wallet → bybit ($30k USDT) [simple] 
3. Transfer: wallet → okx ($30k USDT) [simple]
4. Spot Trade: binance BTC/USDT BUY 0.59 BTC [cex_interface]
5. Spot Trade: bybit BTC/USDT BUY 0.44 BTC [cex_interface]
6. Spot Trade: okx BTC/USDT BUY 0.44 BTC [cex_interface]
7. Perp Trade: binance BTCUSDT SELL 0.59 BTC [cex_interface]
8. Perp Trade: bybit BTCUSDT SELL 0.44 BTC [cex_interface] 
9. Perp Trade: okx BTCUSDT SELL 0.44 BTC [cex_interface]
```

### **Leveraged Staking Setup** (Complex Sequential)
```
1. Transfer: wallet → binance ($50k USDT) [simple]
2. Spot Trade: binance ETH/USDT BUY 15 ETH [cex_interface]
3. Transfer: binance → wallet (15 ETH) [simple]
4. Leverage Loop: 23 iterations [onchain_interface]
   - Iteration 1: Stake 15 ETH → weETH [onchain]
   - Iteration 1: Supply weETH → aWeETH [onchain]  
   - Iteration 1: Borrow WETH [onchain]
   - Iteration 2: Stake WETH → weETH [onchain]
   - ... (repeat 23 times)
5. Perp Trades: Short ETH on 3 venues [cex_interface x3]
```

### **Atomic Leveraged Staking** (Single Transaction)
```
1. Transfer: wallet → binance ($50k USDT) [simple]
2. Spot Trade: binance ETH/USDT BUY 15 ETH [cex_interface]
3. Transfer: binance → wallet (15 ETH) [simple]
4. Atomic Leverage: Flash loan entry [onchain_interface - ATOMIC]
   - Sub-operation 1: Flash borrow WETH
   - Sub-operation 2: Stake ETH → weETH  
   - Sub-operation 3: Supply weETH → aWeETH
   - Sub-operation 4: Borrow WETH
   - Sub-operation 5: Repay flash loan
   - [All in single transaction, single gas payment]
5. Perp Trades: Short ETH on 3 venues [cex_interface x3]
```

## Modules to Remove/Reduce

### **REMOVE ENTIRELY:**
- `cex_execution_manager.py` - Legacy, replaced by `cex_execution_interface.py`
- `onchain_execution_manager.py` - Legacy, replaced by `onchain_execution_interface.py`

### **REDUCE SCOPE:**
- `transfer_manager.py` - Keep only complex cross-venue logic, remove simple transfers
- `event_driven_strategy_engine.py` - Remove execution logic, keep only orchestration

### **ENHANCE:**
- `strategy_manager.py` - Add instruction generation and simple transfer handling
- `*_execution_interface.py` - Fix async/await issues, standardize instruction format
- `position_monitor.py` - Ensure it handles all update scenarios correctly

## Missing Functionality to Add

### **1. Instruction Standardization**
- Unified `ExecutionInstruction` dataclass
- Clear field mapping between components
- Type safety and validation

### **2. Simple Transfer Handler**
- Direct position monitor updates for wallet→CEX transfers
- Bypass complex transfer manager for simple operations

### **3. Atomic Transaction Support**  
- Flash loan operation bundling
- Single gas payment for atomic operations
- Transaction group timestamping

### **4. Better Error Handling**
- Clear error propagation
- Structured error codes
- Component-specific error handling

Would you like me to proceed with implementing this simplified architecture? The key changes would be:

1. **Remove legacy execution managers**
2. **Fix async/await issues in execution interfaces**  
3. **Add simple transfer handling to Strategy Manager**
4. **Standardize instruction format**
5. **Test with BTC basis mode**

What are your thoughts on this plan?
