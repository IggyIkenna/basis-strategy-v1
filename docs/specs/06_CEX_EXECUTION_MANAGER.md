# Component Spec: CEX Execution Manager 🏦

**Component**: CEX Execution Interface  
**Responsibility**: Execute spot and perpetual trades on centralized exchanges  
**Priority**: ⭐⭐ HIGH (Executes off-chain operations)  
**Backend File**: `backend/src/basis_strategy_v1/core/interfaces/cex_execution_interface.py` ✅ **CORRECT**

---

## 🎯 **Purpose**

Execute trades on CEXs (Binance, Bybit, OKX).

**Key Principles**:
- **Backtest**: Simulate using historical prices + execution cost model
- **Live**: Execute real orders via CCXT with real-time market data
- **Market Data Integration**: Receives market data snapshots for execution decisions
- **Updates Position Monitor**: Tells Position Monitor what changed
- **Logs Events**: Calls Event Logger for every trade
- **Per-exchange prices**: Uses venue-specific futures data
- **Execution Timing**: Uses market data for optimal execution timing

**Execution Cost Mechanics**:
- **Arrival Price**: Last known price when instruction issued
- **Fill Price**: Actual price filled at
- **Execution Cost**: arrival_price - fill_price (slippage)
- **Backtest**: Fixed slippage from execution cost model (no tick data)
- **Live**: Real slippage from order fill

---

## 📊 **Data Structures**

### **Input**: Trade Instruction + Market Data

```python
{
    'instruction': {
        'venue': 'binance',  # 'binance', 'bybit', 'okx'
        'trade_type': 'SPOT' or 'PERP',
        'pair': 'ETH/USDT' or 'ETHUSDT-PERP',
        'side': 'BUY' or 'SELL' (spot) or 'SHORT' or 'LONG' (perp),
        'amount': 15.2,  # ETH amount
        'timestamp': timestamp
    },
    'market_data': {
        'eth_usd_price': 3300.50,
        'btc_usd_price': 45000.25,
        'perp_funding_rates': {
            'binance': {'ETHUSDT-PERP': 0.0001},
            'bybit': {'ETHUSDT-PERP': 0.0002},
            'okx': {'ETHUSDT-PERP': 0.0003}
        },
        'gas_price_gwei': 25.5,
        'timestamp': timestamp,
        'data_age_seconds': 0
    }
}
```

### **Output**: Execution Result

```python
{
    'success': True,
    'venue': 'binance',
    'trade_type': 'SPOT',
    'pair': 'ETH/USDT',
    'side': 'BUY',
    'amount_requested': 15.2,
    'amount_filled': 15.2,
    'fill_price': 3305.20,
    'notional_usd': 50239.04,
    'execution_cost_usd': 35.17,
    'execution_cost_bps': 7.0,
    
    # Balance changes (for Position Monitor)
    'balance_changes': {
        'token_changes': [
            {'venue': 'binance', 'token': 'ETH_spot', 'delta': +15.2},
            {'venue': 'binance', 'token': 'USDT', 'delta': -50274.21}  # notional + cost
        ],
        'derivative_changes': []  # None for spot trade
    },
    
    # Event data (for Event Logger)
    'event_data': {
        'event_type': 'SPOT_TRADE',
        'venue': 'BINANCE',
        # ... full event details
    }
}
```

---

## 💻 **Core Functions**

```python
class CEXExecutionManager:
    """Execute trades on centralized exchanges."""
    
    def __init__(self, execution_mode, position_monitor, event_logger, data_provider):
        self.execution_mode = execution_mode
        self.position_monitor = position_monitor
        self.event_logger = event_logger
        self.data_provider = data_provider
        
        # Live mode: Initialize CCXT clients
        if execution_mode == 'live':
            self.exchanges = {
                # Binance Spot (for spot trading)
                'binance_spot': ccxt.binance({
                    'apiKey': config['cex']['binance_spot_api_key'],
                    'secret': config['cex']['binance_spot_secret'],
                    'sandbox': config['cex']['binance_spot_testnet']
                }),
                # Binance Futures (for perpetual futures trading)
                'binance_futures': ccxt.binance({
                    'apiKey': config['cex']['binance_futures_api_key'],
                    'secret': config['cex']['binance_futures_secret'],
                    'sandbox': config['cex']['binance_futures_testnet'],
                    'options': {'defaultType': 'future'}  # Enable futures trading
                }),
                'bybit': ccxt.bybit({
                    'apiKey': config['cex']['bybit_api_key'],
                    'secret': config['cex']['bybit_secret'],
                    'sandbox': config['cex']['bybit_testnet']
                }),
                'okx': ccxt.okx({
                    'apiKey': config['cex']['okx_api_key'],
                    'secret': config['cex']['okx_secret'],
                    'password': config['cex']['okx_passphrase'],
                    'sandbox': config['cex']['okx_testnet']
                })
            }
    
    async def trade_spot(
        self,
        venue: str,
        pair: str,
        side: str,
        amount: float,
        timestamp: pd.Timestamp,
        market_data: Dict
    ) -> Dict:
        """
        Execute spot trade.
        
        Backtest: Simulate using historical prices
        Live: Execute real order via CCXT with market data
        """
        if self.execution_mode == 'backtest':
            result = await self._simulate_spot_trade(venue, pair, side, amount, timestamp, market_data)
        else:  # live
            result = await self._execute_spot_trade_live(venue, pair, side, amount, market_data)
        
        # Update Position Monitor (encapsulated!)
        await self.position_monitor.update({
            'timestamp': timestamp,
            'trigger': 'SPOT_TRADE',
            **result['balance_changes']
        })
        
        # Log event (encapsulated!)
        await self.event_logger.log_event(
            timestamp=timestamp,
            **result['event_data'],
            position_snapshot=await self.position_monitor.get_snapshot()
        )
        
        return result
    
    async def _simulate_spot_trade(
        self,
        venue: str,
        pair: str,
        side: str,
        amount: float,
        timestamp: pd.Timestamp,
        market_data: Dict
    ) -> Dict:
        """Backtest: Simulate spot trade."""
        # Get price from market data (live) or Data Provider (backtest)
        asset = pair.split('/')[0]
        if market_data and 'data_age_seconds' in market_data:
            # Live mode: use real-time price from market data
            price = market_data[f'{asset.lower()}_usd_price']
        else:
            # Backtest mode: use historical price from Data Provider
            price = await self.data_provider.get_spot_price(asset, timestamp)
        
        # Get execution cost from model
        notional = amount × price
        exec_cost_bps = await self.data_provider.get_execution_cost(
            pair, notional, venue, 'SPOT'
        )
        exec_cost_usd = notional × (exec_cost_bps / 10000)
        
        # Calculate fill
        filled_amount = amount
        fill_price = price
        total_cost = notional + exec_cost_usd if side == 'BUY' else notional - exec_cost_usd
        
        # Prepare balance changes
        base_token, quote_token = pair.split('/')
        
        if side == 'BUY':
            balance_changes = {
                'token_changes': [
                    {'venue': venue, 'token': f'{base_token}_spot', 'delta': +filled_amount},
                    {'venue': venue, 'token': quote_token, 'delta': -total_cost}
                ]
            }
        else:  # SELL
            balance_changes = {
                'token_changes': [
                    {'venue': venue, 'token': f'{base_token}_spot', 'delta': -filled_amount},
                    {'venue': venue, 'token': quote_token, 'delta': +total_cost}
                ]
            }
        
        return {
            'success': True,
            'venue': venue,
            'amount_filled': filled_amount,
            'fill_price': fill_price,
            'notional_usd': notional,
            'execution_cost_usd': exec_cost_usd,
            'balance_changes': balance_changes,
            'event_data': {
                'event_type': 'SPOT_TRADE',
                'venue': venue.upper(),
                'token': base_token,
                'amount': filled_amount,
                'side': side,
                'fill_price': fill_price,
                'execution_cost_usd': exec_cost_usd
            }
        }
    
    async def trade_perp(
        self,
        venue: str,
        instrument: str,
        side: str,
        size_eth: float,
        timestamp: pd.Timestamp,
        market_data: Dict
    ) -> Dict:
        """
        Execute perpetual futures trade.
        
        Backtest: Simulate using futures prices
        Live: Execute real order via CCXT with market data
        """
        if self.execution_mode == 'backtest':
            result = await self._simulate_perp_trade(venue, instrument, side, size_eth, timestamp, market_data)
        else:  # live
            result = await self._execute_perp_trade_live(venue, instrument, side, size_eth, market_data)
        
        # Update Position Monitor (derivatives!)
        await self.position_monitor.update({
            'timestamp': timestamp,
            'trigger': 'PERP_TRADE',
            **result['balance_changes']
        })
        
        # Log event
        await self.event_logger.log_event(
            timestamp=timestamp,
            **result['event_data'],
            position_snapshot=await self.position_monitor.get_snapshot()
        )
        
        return result
    
    async def _simulate_perp_trade(
        self,
        venue: str,
        instrument: str,
        side: str,
        size_eth: float,
        timestamp: pd.Timestamp,
        market_data: Dict
    ) -> Dict:
        """Backtest: Simulate perp trade with venue-specific price."""
        # CRITICAL: Use per-exchange futures price!
        asset = instrument.split('USDT')[0]  # 'ETH' or 'BTC'
        
        if market_data and 'data_age_seconds' in market_data:
            # Live mode: use real-time perp price from market data
            entry_price = market_data['perp_prices'][venue][instrument]
        else:
            # Backtest mode: use historical price from Data Provider
            entry_price = await self.data_provider.get_futures_price(asset, venue, timestamp)
        
        # Notional
        notional = abs(size_eth) × entry_price
        
        # Execution cost
        exec_cost_bps = await self.data_provider.get_execution_cost(
            instrument, notional, venue, 'PERP'
        )
        exec_cost_usd = notional × (exec_cost_bps / 10000)
        
        # Balance changes
        balance_changes = {
            'token_changes': [
                {'venue': venue, 'token': 'USDT', 'delta': -exec_cost_usd}  # Cost from margin
            ],
            'derivative_changes': [
                {
                    'venue': venue,
                    'instrument': instrument,
                    'action': 'OPEN' if side in ['SHORT', 'LONG'] else 'CLOSE',
                    'data': {
                        'size': -abs(size_eth) if side == 'SHORT' else abs(size_eth),
                        'entry_price': entry_price,
                        'notional_usd': notional
                    }
                }
            ]
        }
        
        return {
            'success': True,
            'venue': venue,
            'size': size_eth,
            'entry_price': entry_price,
            'notional_usd': notional,
            'execution_cost_usd': exec_cost_usd,
            'balance_changes': balance_changes,
            'event_data': {
                'event_type': 'TRADE_EXECUTED',
                'venue': venue.upper(),
                'token': asset,
                'amount': abs(size_eth),
                'side': side,
                'instrument': instrument,
                'entry_price': entry_price,
                'notional_usd': notional,
                'execution_cost_usd': exec_cost_usd
            }
        }
    
    async def _execute_spot_trade_live(self, venue, pair, side, amount, market_data):
        """Live: Execute real spot trade via CCXT."""
        # Get exchange client (use spot client for spot trading)
        if venue == 'binance':
            exchange = self.exchanges['binance_spot']
        else:
            exchange = self.exchanges[venue]
        
        # Submit market order
        order = await exchange.create_market_order(
            symbol=pair,
            side=side.lower(),
            amount=amount
        )
        
        # Parse result
        filled_amount = order['filled']
        fill_price = order['average']
        notional = filled_amount × fill_price
        fees = order['fee']['cost']
        
        # Prepare balance changes (same structure as backtest!)
        base_token, quote_token = pair.split('/')
        
        if side == 'BUY':
            balance_changes = {
                'token_changes': [
                    {'venue': venue, 'token': f'{base_token}_spot', 'delta': +filled_amount},
                    {'venue': venue, 'token': quote_token, 'delta': -(notional + fees)}
                ]
            }
        else:
            balance_changes = {
                'token_changes': [
                    {'venue': venue, 'token': f'{base_token}_spot', 'delta': -filled_amount},
                    {'venue': venue, 'token': quote_token, 'delta': +(notional - fees)}
                ]
            }
        
        return {
            'success': True,
            'venue': venue,
            'amount_filled': filled_amount,
            'fill_price': fill_price,
            'execution_cost_usd': fees,
            'balance_changes': balance_changes,
            'event_data': {...}  # Same structure
        }
    
    async def _execute_perp_trade_live(self, venue, instrument, side, size_eth, market_data):
        """Live: Execute real perpetual futures trade via CCXT."""
        # Get exchange client (use futures client for perp trading)
        if venue == 'binance':
            exchange = self.exchanges['binance_futures']
        else:
            exchange = self.exchanges[venue]
        
        # Submit market order
        order = await exchange.create_market_order(
            symbol=instrument,
            side=side.lower(),
            amount=abs(size_eth)
        )
        
        # Parse result
        filled_amount = order['filled']
        fill_price = order['average']
        notional = filled_amount × fill_price
        fees = order['fee']['cost']
        
        # Prepare balance changes (derivatives!)
        balance_changes = {
            'derivative_changes': [
                {
                    'venue': venue,
                    'instrument': instrument,
                    'action': 'OPEN' if side in ['SHORT', 'LONG'] else 'CLOSE',
                    'data': {
                        'size': -abs(size_eth) if side == 'SHORT' else abs(size_eth),
                        'entry_price': fill_price,
                        'notional_usd': notional
                    }
                }
            ]
        }
        
        return {
            'success': True,
            'venue': venue,
            'size': size_eth,
            'entry_price': fill_price,
            'notional_usd': notional,
            'execution_cost_usd': fees,
            'balance_changes': balance_changes,
            'event_data': {
                'event_type': 'TRADE_EXECUTED',
                'venue': venue.upper(),
                'token': instrument.split('USDT')[0],
                'amount': abs(size_eth),
                'side': side,
                'instrument': instrument,
                'price': fill_price,
                'execution_cost_usd': fees
            }
        }
```

---

## 🚀 **Live Trading Market Data Integration**

### **Market Data Usage in Live Trading**

```python
# Live trading execution with market data
async def execute_with_market_data(self, instruction: Dict, market_data: Dict) -> Dict:
    """Execute trade with real-time market data considerations."""
    
    # Check data freshness
    if market_data['data_age_seconds'] > 30:
        logger.warning(f"Market data is {market_data['data_age_seconds']}s old")
    
    # Use real-time prices for execution decisions
    current_price = market_data[f"{instruction['asset'].lower()}_usd_price"]
    
    # Check funding rates for perp trades
    if instruction['trade_type'] == 'PERP':
        funding_rate = market_data['perp_funding_rates'][instruction['venue']][instruction['instrument']]
        if abs(funding_rate) > 0.001:  # 0.1% threshold
            logger.info(f"High funding rate: {funding_rate:.4f}")
    
    # Execute with market data context
    return await self._execute_trade(instruction, market_data)
```

### **Execution Timing Optimization**

```python
# Market data-driven execution timing
async def optimize_execution_timing(self, instruction: Dict, market_data: Dict) -> Dict:
    """Optimize execution timing based on market conditions."""
    
    # Check market volatility
    price_volatility = market_data.get('price_volatility', {})
    if price_volatility.get('eth_1min_volatility', 0) > 0.02:  # 2% threshold
        logger.warning("High volatility detected, using limit orders")
        return await self._execute_limit_order(instruction, market_data)
    
    # Check liquidity
    liquidity_metrics = market_data.get('liquidity_metrics', {})
    if liquidity_metrics.get('eth_bid_ask_spread', 0) > 0.005:  # 0.5% threshold
        logger.warning("Wide bid-ask spread, adjusting execution")
        return await self._execute_with_slippage_protection(instruction, market_data)
    
    # Normal execution
    return await self._execute_market_order(instruction, market_data)
```

### **Market Data Structure for CEX Execution**

```python
# Enhanced market data for CEX execution
market_data = {
    # Core prices
    'eth_usd_price': 3300.50,
    'btc_usd_price': 45000.25,
    
    # Perpetual prices (per venue)
    'perp_prices': {
        'binance': {
            'ETHUSDT-PERP': 3301.25,
            'BTCUSDT-PERP': 45001.50
        },
        'bybit': {
            'ETHUSDT-PERP': 3300.75,
            'BTCUSDT-PERP': 45000.80
        },
        'okx': {
            'ETHUSDT-PERP': 3301.00,
            'BTCUSDT-PERP': 45001.20
        }
    },
    
    # Funding rates
    'perp_funding_rates': {
        'binance': {'ETHUSDT-PERP': 0.0001},
        'bybit': {'ETHUSDT-PERP': 0.0002},
        'okx': {'ETHUSDT-PERP': 0.0003}
    },
    
    # Market conditions
    'price_volatility': {
        'eth_1min_volatility': 0.015,
        'btc_1min_volatility': 0.012
    },
    
    'liquidity_metrics': {
        'eth_bid_ask_spread': 0.003,
        'btc_bid_ask_spread': 0.002
    },
    
    'timestamp': datetime.utcnow(),
    'data_age_seconds': 5
}
```

---

## 🔗 **Integration**

### **Called By**:
- Strategy Manager (rebalancing instructions)
- EventDrivenStrategyEngine (initial setup, scheduled trades)

### **Calls**:
- **Position Monitor** ← update() with balance changes
- **Event Logger** ← log_event() for trades
- **Data Provider** ← get prices, execution costs

---

## 🧪 **Testing**

```python
def test_per_exchange_futures_prices():
    """Test that each exchange uses its own futures price."""
    manager = CEXExecutionManager('backtest', ...)
    
    timestamp = pd.Timestamp('2024-08-15 12:00:00', tz='UTC')
    
    # Binance trade
    result_binance = await manager.trade_perp('binance', 'ETHUSDT-PERP', 'SHORT', 8.562, timestamp)
    
    # Bybit trade  
    result_bybit = await manager.trade_perp('bybit', 'ETHUSDT-PERP', 'SHORT', 8.551, timestamp)
    
    # Entry prices should be different!
    assert result_binance['entry_price'] != result_bybit['entry_price']
    assert abs(result_binance['entry_price'] - result_bybit['entry_price']) < 10
```

---

## 🎯 **Success Criteria**

- [ ] Simulates spot trades in backtest
- [ ] Simulates perp trades in backtest
- [ ] Uses per-exchange futures prices (Binance ≠ Bybit)
- [ ] Executes real trades in live mode (CCXT)
- [ ] Updates Position Monitor with results
- [ ] Logs all trades via Event Logger
- [ ] Handles execution costs correctly
- [ ] Supports all 3 venues (Binance, Bybit, OKX)

---

**Status**: Specification complete! ✅


