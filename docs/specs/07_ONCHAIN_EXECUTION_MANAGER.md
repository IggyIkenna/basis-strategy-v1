# Component Spec: OnChain Execution Manager ⛓️

**Component**: OnChain Execution Interface  
**Responsibility**: Execute blockchain transactions (wallet, AAVE, staking, flash loans)  
**Priority**: ⭐⭐⭐ CRITICAL (Executes on-chain operations)  
**Backend File**: `backend/src/basis_strategy_v1/core/interfaces/onchain_execution_interface.py` ✅ **CORRECT**  
**Last Reviewed**: October 8, 2025  
**Status**: ✅ Aligned with canonical sources (.cursor/tasks/ + MODES.md)

---

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [CANONICAL_ARCHITECTURAL_PRINCIPLES.md](../CANONICAL_ARCHITECTURAL_PRINCIPLES.md) - Consolidated from all .cursor/tasks/
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Task Specifications**: `.cursor/tasks/` - Individual task specifications

---

## 🎯 **Purpose**

Execute all on-chain operations.

**Key Principles**:
- **Backtest**: Simulate using validated calculators from analyzers
- **Live**: Execute real transactions via Web3.py with real-time market data
- **Market Data Integration**: Receives market data snapshots for gas optimization and timing
- **Gas tracking**: All operations pay gas (from wallet.ETH)
- **Index-aware**: AAVE operations use current indices
- **Atomic bundles**: Support flash loan leverage loops (Instadapp)
- **Gas Optimization**: Uses real-time gas prices for transaction timing

**Operations**:
- Wallet transfers (ERC-20)
- Uniswap swaps
- AAVE supply/borrow/repay/withdraw
- Lido staking (wstETH)
- EtherFi staking (weETH)
- Atomic leverage loops (flash loans via Instadapp)
- Sequential leverage loops (iterative)

---

## 📊 **Data Structures**

### **Input**: Transaction Instruction + Market Data

```python
{
    'instruction': {
        'operation': 'ATOMIC_LEVERAGE_ENTRY',  # or 'AAVE_SUPPLY', 'STAKE', etc.
        'params': {
            'equity': 50000.0,
            'target_ltv': 0.91,
            'lst_type': 'weeth',
            # ... operation-specific params
        },
        'timestamp': timestamp
    },
    'market_data': {
        'eth_usd_price': 3300.50,
        'gas_price_gwei': 25.5,
        'gas_price_fast_gwei': 30.0,
        'gas_price_standard_gwei': 20.0,
        'aave_usdt_apy': 0.08,
        'lst_prices': {
            'wsteth_usd': 3301.25,
            'reth_usd': 3300.80,
            'sfrxeth_usd': 3301.10
        },
        'timestamp': timestamp,
        'data_age_seconds': 0
    }
}
```

### **Output**: Transaction Result

```python
{
    'success': True,
    'operation': 'ATOMIC_LEVERAGE_ENTRY',
    'gas_cost_eth': 0.012,
    'gas_cost_usd': 39.60,
    
    # Net effect on wallet
    'balance_changes': {
        'token_changes': [
            {'venue': 'WALLET', 'token': 'aWeETH', 'delta': +95.24},
            {'venue': 'WALLET', 'token': 'variableDebtWETH', 'delta': +88.70},
            {'venue': 'WALLET', 'token': 'ETH', 'delta': -0.012}  # Gas
        ]
    },
    
    # Event data (for logging)
    'events': [
        {'event_type': 'ATOMIC_TRANSACTION', ...},  # Wrapper
        {'event_type': 'FLASH_BORROW', ...},        # Step 1
        {'event_type': 'STAKE_DEPOSIT', ...},       # Step 2
        # ... all steps
    ]
}
```

---

## 💻 **Core Functions**

### **Atomic Leverage Loop** (Most Complex)

```python
    async def atomic_leverage_loop(
        self,
        equity: float,
        target_ltv: float,
        lst_type: str,
        mode: str,  # 'entry' or 'exit'
        timestamp: pd.Timestamp,
        market_data: Dict
    ) -> Dict:
    """
    Execute atomic leverage loop via flash loan (Instadapp).
    
    Entry: Flash borrow → stake → supply → borrow → repay flash
    Exit: Flash borrow → repay debt → withdraw → swap → repay flash
    
    Uses validated calculator from USDT analyzer!
    """
        if self.execution_mode == 'backtest':
            if mode == 'entry':
                result = await self._simulate_atomic_entry(equity, target_ltv, lst_type, timestamp, market_data)
            else:  # exit/deleverage
                result = await self._simulate_atomic_exit(equity, lst_type, timestamp, market_data)
        else:  # live
            # Requires: BASIS_INSTADAPP__API_KEY and BASIS_INSTADAPP__API_SECRET
            if mode == 'entry':
                result = await self._execute_atomic_entry_live(equity, target_ltv, lst_type, market_data)
            else:
                result = await self._execute_atomic_exit_live(equity, lst_type, market_data)
    
    # Update Position Monitor
    await self.position_monitor.update({
        'timestamp': timestamp,
        'trigger': f'ATOMIC_LEVERAGE_{mode.upper()}',
        **result['balance_changes']
    })
    
    # Log atomic transaction (wrapper + details)
    await self.event_logger.log_atomic_transaction(
        timestamp=timestamp,
        bundle_name=f'ATOMIC_LEVERAGE_{mode.upper()}',
        detail_events=result['events'],
        net_result=result['net_result'],
        position_snapshot=await self.position_monitor.get_snapshot()
    )
    
    return result

    async def _simulate_atomic_entry(
        self,
        equity: float,
        target_ltv: float,
        lst_type: str,
        timestamp: pd.Timestamp,
        market_data: Dict
    ) -> Dict:
    """
    Backtest: Simulate atomic leverage entry.
    
    Uses validated calculator from analyze_leveraged_restaking_USDT.py!
    """
    # Import validated calculator
    from ....scripts.analyzers.calculators.leverage_loop import execute_atomic_flash
    
    # Create data lookup function (use market data if available)
    if market_data and 'data_age_seconds' in market_data:
        # Live mode: use real-time data from market_data
        data_lookup = {
            'get_oracle_price': lambda: market_data['lst_prices'][f'{lst_type}_usd'],
            'get_liquidity_index': lambda: market_data.get('aave_indices', {}).get(f'{lst_type}_liquidity_index', 1.0),
            'get_borrow_index': lambda: market_data.get('aave_indices', {}).get('weth_borrow_index', 1.0),
            'get_gas_cost': lambda op: self._calculate_gas_cost_from_market_data(op, market_data)
        }
    else:
        # Backtest mode: use historical data from Data Provider
        data_lookup = {
            'get_oracle_price': lambda: self.data_provider.get_oracle_price(lst_type, timestamp),
            'get_liquidity_index': lambda: self.data_provider.get_aave_index(lst_type, 'liquidity', timestamp),
            'get_borrow_index': lambda: self.data_provider.get_aave_index('WETH', 'borrow', timestamp),
            'get_gas_cost': lambda op: self.data_provider.get_gas_cost(op, timestamp)
        }
    
    # Call validated calculator
    calc_result = execute_atomic_flash(
        timestamp=timestamp,
        equity=equity,
        target_ltv=target_ltv,
        max_ltv=0.93,  # AAVE protocol max
        liquidation_threshold=0.95,
        data_lookup=data_lookup
    )
    
    # Convert to our result format
    return {
        'success': True,
        'operation': 'ATOMIC_LEVERAGE_ENTRY',
        'mode': 'ATOMIC_FLASH',
        'flash_amount': calc_result['flash_amount'],
        'collateral_supplied': calc_result['weeth_collateral'],
        'debt_created': calc_result['weth_debt'],
        'leverage_achieved': calc_result['leverage_multiplier'],
        'gas_cost_eth': calc_result['gas_cost_eth'],
        'gas_cost_usd': calc_result['gas_cost_usd'],
        
        # Balance changes
        'balance_changes': {
            'token_changes': [
                {'venue': 'WALLET', 'token': f'a{lst_type.upper()}', 'delta': +calc_result['aweeth_received']},
                {'venue': 'WALLET', 'token': 'variableDebtWETH', 'delta': +calc_result['debt_created']},
                {'venue': 'WALLET', 'token': 'ETH', 'delta': -calc_result['gas_cost_eth']}
            ]
        },
        
        # Events (wrapper + 6 detail events)
        'events': calc_result['events'],
        'net_result': {
            'collateral': calc_result['weeth_collateral'],
            'debt': calc_result['weth_debt'],
            'leverage': calc_result['leverage_multiplier'],
            'health_factor': calc_result['health_factor']
        }
    }
```

### **Sequential Leverage Loop**

```python
async def sequential_leverage_loop(
    self,
    initial_eth: float,
    target_ltv: float,
    lst_type: str,
    max_iterations: Optional[int],
    timestamp: pd.Timestamp
) -> Dict:
    """
    Execute sequential leverage loop (iterative staking).
    
    Each iteration:
    1. Pay gas
    2. Stake ETH → LST
    3. Pay gas
    4. Supply LST to AAVE
    5. Pay gas
    6. Borrow WETH
    7. Loop until remaining < threshold
    
    Uses validated calculator from analyzers!
    """
    if self.execution_mode == 'backtest':
        # Import validated calculator
        from ....scripts.analyzers.calculators.leverage_loop import execute_recursive_loop
        
        calc_result = execute_recursive_loop(
            timestamp=timestamp,
            initial_capital=initial_eth,
            max_ltv=0.93,
            target_ltv=target_ltv,
            min_threshold=self.config['strategy']['min_loop_position_usd'],
            max_iterations=max_iterations,
            lst_type=lst_type,
            data_lookup=self._create_data_lookup()
        )
    
    else:  # live
        # Execute real transactions iteratively
        # No additional API keys needed (direct protocol calls)
        calc_result = await self._execute_sequential_loop_live(...)
    
    # Update Position Monitor
    # Log events (one per iteration step)
    # Return result
    
    return calc_result
```

### **Fast vs Slow Unwinding**

```python
async def unwind_position(
    self,
    amount_to_unwind: float,
    unwind_mode: str,  # 'fast' or 'slow'
    timestamp: pd.Timestamp
) -> Dict:
    """
    Unwind staked position.
    
    Fast mode (DEX):
    - Swap LST → WETH on Uniswap/Curve
    - Can use flash loans (immediate)
    - Higher cost (DEX fees + slippage)
    
    Slow mode (Direct protocol):
    - Redeem LST → ETH via EtherFi/Lido
    - Can't use flash loans (withdrawal queue, days)
    - Lower cost (just gas)
    """
    if unwind_mode == 'fast':
        # DEX swap (immediate, can use flash)
        result = await self._unwind_via_dex(amount_to_unwind, timestamp)
    
    else:  # slow
        # Direct protocol redemption (queue, no flash)
        result = await self._unwind_via_protocol(amount_to_unwind, timestamp)
    
    return result

async def _unwind_via_dex(self, amount, timestamp):
    """Fast unwinding: Swap LST on DEX."""
    # Swap weETH → WETH on Uniswap
    # Pay DEX fees + slippage
    # Immediate (one block)
    # Can be part of atomic deleverage (flash loan)
    pass

async def _unwind_via_protocol(self, amount, timestamp):
    """Slow unwinding: Direct redemption."""
    # Redeem weETH → ETH via EtherFi
    # Free (just gas)
    # Slow (withdrawal queue)
    # Can't use flash loans (need to wait for queue)
    pass
```

---

## 🚀 **Live Trading Market Data Integration**

### **Gas Optimization with Market Data**

```python
# Gas price optimization for live trading
async def optimize_gas_price(self, market_data: Dict, urgency: str = 'standard') -> Dict:
    """Optimize gas price based on market conditions and urgency."""
    
    # Get current gas prices from market data
    gas_prices = {
        'slow': market_data.get('gas_price_slow_gwei', 15.0),
        'standard': market_data.get('gas_price_standard_gwei', 20.0),
        'fast': market_data.get('gas_price_fast_gwei', 25.0),
        'instant': market_data.get('gas_price_instant_gwei', 30.0)
    }
    
    # Choose gas price based on urgency and market conditions
    if urgency == 'critical':
        # Use fast gas for critical operations (liquidation prevention)
        selected_gas = gas_prices['fast']
    elif urgency == 'high':
        # Use standard gas for high priority operations
        selected_gas = gas_prices['standard']
    else:
        # Use slow gas for routine operations
        selected_gas = gas_prices['slow']
    
    # Check if gas prices are reasonable
    if selected_gas > 100:  # 100 gwei threshold
        logger.warning(f"High gas price detected: {selected_gas} gwei")
        # Consider delaying non-critical operations
    
    return {
        'gas_price_gwei': selected_gas,
        'gas_price_wei': int(selected_gas * 1e9),
        'estimated_cost_usd': self._estimate_gas_cost_usd(selected_gas, market_data['eth_usd_price'])
    }

async def _calculate_gas_cost_from_market_data(self, operation: str, market_data: Dict) -> float:
    """Calculate gas cost in USD using real-time market data."""
    
    # Get gas price based on operation type
    if operation in ['ATOMIC_LEVERAGE_ENTRY', 'ATOMIC_LEVERAGE_EXIT']:
        gas_price_gwei = market_data.get('gas_price_fast_gwei', 25.0)  # Fast for atomic operations
    elif operation in ['AAVE_SUPPLY', 'AAVE_BORROW']:
        gas_price_gwei = market_data.get('gas_price_standard_gwei', 20.0)  # Standard for AAVE
    else:
        gas_price_gwei = market_data.get('gas_price_slow_gwei', 15.0)  # Slow for routine operations
    
    # Estimate gas limit for operation
    gas_limits = {
        'ATOMIC_LEVERAGE_ENTRY': 800000,  # Complex atomic operation
        'ATOMIC_LEVERAGE_EXIT': 600000,   # Complex atomic operation
        'AAVE_SUPPLY': 200000,            # Simple AAVE operation
        'AAVE_BORROW': 250000,            # Simple AAVE operation
        'STAKE_DEPOSIT': 150000,          # Simple staking operation
        'TRANSFER': 21000                 # Simple transfer
    }
    
    gas_limit = gas_limits.get(operation, 100000)  # Default 100k gas
    
    # Calculate cost in ETH
    gas_cost_eth = (gas_price_gwei * 1e9 * gas_limit) / 1e18
    
    # Convert to USD
    eth_price = market_data['eth_usd_price']
    gas_cost_usd = gas_cost_eth * eth_price
    
    return gas_cost_usd
```

### **Market Data Structure for OnChain Execution**

```python
# Enhanced market data for on-chain execution
market_data = {
    # Core prices
    'eth_usd_price': 3300.50,
    
    # Gas prices (multiple tiers)
    'gas_price_slow_gwei': 15.0,
    'gas_price_standard_gwei': 20.0,
    'gas_price_fast_gwei': 25.0,
    'gas_price_instant_gwei': 30.0,
    
    # LST prices (for staking operations)
    'lst_prices': {
        'wsteth_usd': 3301.25,
        'reth_usd': 3300.80,
        'sfrxeth_usd': 3301.10,
        'weeth_usd': 3301.50
    },
    
    # AAVE indices (for supply/borrow calculations)
    'aave_indices': {
        'wsteth_liquidity_index': 1.025,
        'weth_liquidity_index': 1.018,
        'weth_borrow_index': 1.012,
        'usdt_liquidity_index': 1.008
    },
    
    # AAVE rates
    'aave_rates': {
        'wsteth_supply_apy': 0.05,
        'weth_borrow_apy': 0.08,
        'usdt_supply_apy': 0.06
    },
    
    # Network conditions
    'network_conditions': {
        'pending_transactions': 150000,
        'block_time_seconds': 12.1,
        'network_congestion': 'medium'
    },
    
    'timestamp': datetime.utcnow(),
    'data_age_seconds': 5
}
```

### **Transaction Timing Optimization**

```python
# Market data-driven transaction timing
async def optimize_transaction_timing(self, operation: str, market_data: Dict) -> Dict:
    """Optimize transaction timing based on network conditions."""
    
    network_conditions = market_data.get('network_conditions', {})
    
    # Check network congestion
    congestion = network_conditions.get('network_congestion', 'low')
    pending_txs = network_conditions.get('pending_transactions', 0)
    
    if congestion == 'high' or pending_txs > 200000:
        logger.warning("High network congestion detected")
        return {
            'should_delay': True,
            'delay_seconds': 60,
            'reason': 'High network congestion',
            'gas_price_multiplier': 1.2  # Increase gas by 20%
        }
    
    # Check if gas prices are reasonable
    current_gas = market_data.get('gas_price_standard_gwei', 20.0)
    if current_gas > 50:  # 50 gwei threshold
        logger.warning(f"High gas prices: {current_gas} gwei")
        return {
            'should_delay': True,
            'delay_seconds': 300,  # Wait 5 minutes
            'reason': 'High gas prices',
            'gas_price_multiplier': 1.0
        }
    
    # Normal conditions
    return {
        'should_delay': False,
        'delay_seconds': 0,
        'reason': 'Normal conditions',
        'gas_price_multiplier': 1.0
    }
```

---

## 🔗 **Integration**

### **Called By**:
- Strategy Manager (rebalancing, unwinding)
- EventDrivenStrategyEngine (initial setup)

### **Calls**:
- **Position Monitor** ← update() with balance changes
- **Event Logger** ← log_event(), log_atomic_transaction()
- **Data Provider** ← get oracles, indices, gas costs

---

## 🎯 **Success Criteria**

- [ ] Atomic leverage entry works (flash loan)
- [ ] Sequential leverage loop works (iterative)
- [ ] Atomic deleverage works (exit via flash)
- [ ] Fast unwinding works (DEX swap)
- [ ] Slow unwinding works (direct protocol)
- [ ] AAVE supply uses correct index (aWeETH = supply / index)
- [ ] AAVE borrow uses correct index
- [ ] All operations log gas costs
- [ ] Updates Position Monitor correctly
- [ ] Live mode: Web3.py integration

---

**Status**: Specification complete! ✅


