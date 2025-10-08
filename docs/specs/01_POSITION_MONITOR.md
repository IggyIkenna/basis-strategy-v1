# Component Spec: Position Monitor 📊

**Component**: Position Monitor (wraps Token + Derivative monitors)  
**Responsibility**: Track raw balances across all venues with sync guarantee  
**Priority**: ⭐⭐⭐ CRITICAL (Foundation for all other components)  
**Backend File**: `backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py`

---

## 🎯 **Purpose**

Track raw ERC-20/token balances and derivative positions with **NO conversions**.

**Key Principle**: This component knows about balances in NATIVE token units only.
- aWeETH is just a number (doesn't know it represents underlying weETH)
- ETH is just a number (doesn't know its USD value)
- Perp position is just a size (doesn't know its USD exposure)

**Data Flow Integration**:
- **Initialization**: Receives `initial_capital` and `share_class` in constructor
- **State Management**: Maintains internal balance state, no external data dependencies
- **Output**: Provides `get_snapshot()` method for other components
- **No Market Data**: Pure balance tracking, no price conversions

**Conversions happen in Exposure Monitor!**

### **Seasonal Reward Tokens** 🎁

**KING Token Handling** (from EtherFi restaking):
- **KING**: Wrapped token containing EIGEN + ETHFI (dollar-equivalent value)
- **EIGEN**: Unwrapped from KING tokens (seasonal rewards)
- **ETHFI**: Unwrapped from KING tokens (seasonal rewards)
- **Distribution**: Weekly + ad-hoc distributions to weETH holders
- **Unwrapping**: KING → EIGEN + ETHFI when threshold exceeded (100x gas fee)
- **Selling**: EIGEN/ETHFI sold for USDT on Binance

**BTC Support**:
- **BTC**: Wrapped BTC (ERC-20) for basis trading strategies
- **aBTC**: AAVE aToken for BTC lending
- **variableDebtBTC**: AAVE debt token for BTC borrowing

### **AAVE Index Mechanics** 🔢

**Important**: AAVE uses index-based growth where:
- **aWeETH balance is CONSTANT** after supply (never changes)
- **Underlying weETH claimable grows** via `weETH_claimable = aWeETH * LiquidityIndex`
- **Index at supply time determines** how much aWeETH you receive: `aWeETH = weETH_supplied / LiquidityIndex_at_supply`
- **Our data uses normalized indices** (~1.0, not the raw 1e27 values from AAVE docs)

**Example**:
```python
# At supply (t=0): Supply 100 weETH when index = 1.05
aWeETH_received = 100 / 1.05 = 95.24  # This stays constant

# At withdrawal (t=n): Index = 1.08
weETH_claimable = 95.24 * 1.08 = 102.86  # This grows with index
```

---

## 📦 **Component Structure**

### **Wrapped Monitors** (Internal)

```python
class TokenBalanceMonitor:
    """Track raw token balances (internal to PositionMonitor)."""
    
    def __init__(self):
        # On-chain wallet (single Ethereum address)
        self.wallet = {
            'ETH': 0.0,                    # Native ETH for gas
            'USDT': 0.0,                   # USDT ERC-20
            'BTC': 0.0,                    # BTC ERC-20 (wrapped BTC)
            'weETH': 0.0,                  # Free weETH (not in AAVE)
            'wstETH': 0.0,                 # Free wstETH
            'aWeETH': 0.0,                 # AAVE aToken (CONSTANT - grows via index)
            'awstETH': 0.0,                # AAVE aToken for wstETH
            'aUSDT': 0.0,                  # AAVE aToken for USDT
            'aBTC': 0.0,                   # AAVE aToken for BTC
            'variableDebtWETH': 0.0,       # AAVE debt token (CONSTANT - grows via index)
            'variableDebtUSDT': 0.0,       # AAVE debt token for USDT
            'variableDebtBTC': 0.0,        # AAVE debt token for BTC
            'KING': 0.0,                   # KING rewards (seasonal - to be unwrapped into EIGEN and ETHFI)
            'EIGEN': 0.0,                  # EIGEN rewards (seasonal - from KING unwrapping)
            'ETHFI': 0.0                   # ETHFI rewards (seasonal - from KING unwrapping)
        }
        
        # CEX accounts (separate per exchange)
        self.cex_accounts = {
            'binance': {'USDT': 0.0, 'ETH': 0.0, 'BTC': 0.0},
            'bybit': {'USDT': 0.0, 'ETH': 0.0, 'BTC': 0.0},
            'okx': {'USDT': 0.0, 'ETH': 0.0, 'BTC': 0.0}
        }

class DerivativeBalanceMonitor:
    """Track perpetual positions (internal to PositionMonitor)."""
    
    def __init__(self):
        self.perp_positions = {
            'binance': {},  # Dict[instrument, PositionData]
            'bybit': {},
            'okx': {}
        }
        
        # Position data structure
        # {
        #     'ETHUSDT-PERP': {
        #         'size': -8.562,           # Negative for short
        #         'entry_price': 2920.00,
        #         'entry_timestamp': timestamp,
        #         'notional_usd': 25000.0
        #     }
        # }
```

### **Position Monitor** (Public Interface)

```python
class PositionMonitor:
    """
    Wrapper ensuring Token + Derivative monitors update synchronously.
    
    PUBLIC INTERFACE for all other components.
    """
    
    def __init__(self, 
                 config: Dict[str, Any], 
                 execution_mode: str, 
                 initial_capital: float, 
                 share_class: str,
                 data_provider=None):
        """
        Initialize position monitor with capital from API request.
        
        Phase 3: NO DEFAULTS - all parameters must be provided from API request.
        
        Args:
            config: Strategy configuration from validated config manager
            execution_mode: 'backtest' or 'live' (from startup config)
            initial_capital: Initial capital amount from API request (NO DEFAULT)
            share_class: Share class from API request ('USDT' or 'ETH') (NO DEFAULT)
            data_provider: Data provider instance for price lookups
        """
        self.config = config
        self.execution_mode = execution_mode
        self.initial_capital = initial_capital
        self.share_class = share_class
        self.data_provider = data_provider
        
        # Validate required parameters (FAIL FAST)
        if not initial_capital or initial_capital <= 0:
            raise ValueError(f"Invalid initial_capital: {initial_capital}. Must be > 0.")
        
        if share_class not in ['USDT', 'ETH']:
            raise ValueError(f"Invalid share_class: {share_class}. Must be 'USDT' or 'ETH'.")
        
        # Internal monitors
        self._token_monitor = TokenBalanceMonitor()
        self._derivative_monitor = DerivativeBalanceMonitor()
        
        # Initialize capital based on share class (NO DEFAULTS)
        self._initialize_capital()
        
        # Redis for inter-component communication
        self.redis = None
        if execution_mode == 'live':
            try:
                import os
                redis_url = os.getenv('BASIS_REDIS_URL')
                if not redis_url:
                    raise ValueError("BASIS_REDIS_URL environment variable required for live mode")
                
                self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis.ping()
                logger.info("Redis connection established for Position Monitor")
            except Exception as e:
                logger.error(f"Redis connection failed for live mode: {e}")
                raise ValueError(f"Redis required for live mode but connection failed: {e}")
        
        logger.info(f"Position Monitor initialized: {execution_mode} mode, {share_class} share class, {initial_capital} initial capital")
    
    def _initialize_capital(self):
        """Initialize capital based on share class and initial capital from API request."""
        if self.share_class == 'USDT':
            self._token_monitor.wallet['USDT'] = float(self.initial_capital)
            logger.info(f"Initialized USDT capital: {self.initial_capital}")
        elif self.share_class == 'ETH':
            self._token_monitor.wallet['ETH'] = float(self.initial_capital)
            logger.info(f"Initialized ETH capital: {self.initial_capital}")
        else:
            raise ValueError(f"Invalid share class: {self.share_class}")
        
        logger.info(f"Capital initialized: {self.share_class} = {self.initial_capital}")
    
    async def update(self, changes: Dict):
        """
        Update balances (SYNCHRONOUS - blocks until complete).
        
        Args:
            changes: {
                'token_changes': [
                    {'venue': 'WALLET', 'token': 'ETH', 'delta': -0.0035, 'reason': 'GAS_FEE'},
                    {'venue': 'WALLET', 'token': 'aWeETH', 'delta': +95.24, 'reason': 'AAVE_SUPPLY'}
                ],
                'derivative_changes': [
                    {'venue': 'binance', 'instrument': 'ETHUSDT-PERP', 'action': 'OPEN', 'data': {...}}
                ]
            }
        
        Returns:
            Updated snapshot
        """
        # Update token balances
        for change in changes.get('token_changes', []):
            self._apply_token_change(change)
        
        # Update derivative positions
        for change in changes.get('derivative_changes', []):
            self._apply_derivative_change(change)
        
        # Get snapshot
        snapshot = self.get_snapshot()
        
        # Publish to Redis (for other components)
        if self.redis:
            await self.redis.set('position:snapshot', json.dumps(snapshot))
            await self.redis.publish('position:updated', json.dumps({
                'timestamp': changes.get('timestamp'),
                'trigger': changes.get('trigger')
            }))
        
        return snapshot
    
    def get_snapshot(self) -> Dict:
        """Get current position snapshot (read-only)."""
        # Convert PositionData objects to dictionaries for serialization
        perp_positions = {}
        for venue, positions in self._derivative_monitor.perp_positions.items():
            perp_positions[venue] = {}
            if positions:  # Only include instruments that have positions
                for instrument, position_data in positions.items():
                    perp_positions[venue][instrument] = {
                        'size': position_data.size,
                        'entry_price': position_data.entry_price,
                        'entry_timestamp': position_data.entry_timestamp,
                        'notional_usd': position_data.notional_usd
                    }
        
        return {
            'wallet': self._token_monitor.wallet.copy(),
            'cex_accounts': {k: v.copy() for k, v in self._token_monitor.cex_accounts.items()},
            'perp_positions': perp_positions,
            'last_updated': pd.Timestamp.now(tz='UTC')
        }
    
    async def reconcile_with_live(self):
        """
        Reconcile tracked balances with live queries (live mode only).
        
        Queries:
        - Web3: Actual wallet balances
        - CEX APIs: Actual account balances
        - CEX APIs: Actual perp positions
        
        Compares with tracked, logs discrepancies.
        """
        if self.execution_mode != 'live':
            return  # Backtest doesn't need reconciliation
        
        # Query real balances
        real_wallet = await self._query_web3_wallet()
        real_cex = await self._query_cex_balances()
        real_perps = await self._query_perp_positions()
        
        # Compare
        discrepancies = self._find_discrepancies(
            tracked={'wallet': self._token_monitor.wallet, ...},
            real={'wallet': real_wallet, ...}
        )
        
        if discrepancies:
            logger.error(f"⚠️ BALANCE DISCREPANCIES: {discrepancies}")
            # Alert monitoring system
            await self._alert_discrepancies(discrepancies)
```

---

## 📊 **Data Structures**

### **Input: Balance Changes**

```python
{
    'timestamp': pd.Timestamp('2024-05-12 00:00:00', tz='UTC'),
    'trigger': 'GAS_FEE_PAID',  # What caused this update
    'token_changes': [
        {
            'venue': 'WALLET',  # or 'BINANCE', 'BYBIT', 'OKX'
            'token': 'ETH',
            'delta': -0.0035,   # Change (negative = decrease)
            'new_balance': 49.9965,  # New balance after change
            'reason': 'GAS_FEE_PAID'
        }
    ],
    'derivative_changes': [
        {
            'venue': 'binance',
            'instrument': 'ETHUSDT-PERP',
            'action': 'OPEN',  # or 'CLOSE', 'ADJUST'
            'data': {
                'size': -8.562,
                'entry_price': 2920.00,
                'notional_usd': 25000.0
            }
        }
    ]
}
```

### **Output: Position Snapshot**

```python
{
    'timestamp': pd.Timestamp('2024-05-12 00:00:00', tz='UTC'),
    'wallet': {
        'ETH': 49.9965,
        'USDT': 0.0,
        'BTC': 0.0,
        'weETH': 0.0,
        'wstETH': 0.0,
        'aWeETH': 95.24,              # CONSTANT scaled balance
        'aUSDT': 0.0,                 # AAVE aToken for USDT
        'aBTC': 0.0,                  # AAVE aToken for BTC
        'variableDebtWETH': 88.70,    # CONSTANT scaled balance
        'variableDebtUSDT': 0.0,      # AAVE debt token for USDT
        'variableDebtBTC': 0.0,       # AAVE debt token for BTC
        'KING': 0.0,                  # KING rewards (seasonal)
        'EIGEN': 0.0,                 # EIGEN rewards (seasonal)
        'ETHFI': 0.0                  # ETHFI rewards (seasonal)
    },
    'cex_accounts': {
        'binance': {
            'USDT': 24992.50,
            'ETH': 0.0,
            'BTC': 0.0
        },
        'bybit': {
            'USDT': 24985.30,
            'ETH': 0.0,
            'BTC': 0.0
        },
        'okx': {
            'USDT': 24980.15,
            'ETH': 0.0,
            'BTC': 0.0
        }
    },
    'perp_positions': {
        'binance': {
            'ETHUSDT-PERP': {
                'size': -8.562,
                'entry_price': 2920.00,
                'entry_timestamp': '2024-05-12 00:00:00',
                'notional_usd': 25000.0
            }
        },
        'bybit': {
            'ETHUSDT-PERP': {
                'size': -8.551,
                'entry_price': 2921.50,
                'entry_timestamp': '2024-05-12 00:00:00',
                'notional_usd': 24975.0
            }
        },
        'okx': {
            'ETHUSDT-PERP': {
                'size': -8.557,
                'entry_price': 2920.50,
                'entry_timestamp': '2024-05-12 00:00:00',
                'notional_usd': 24987.5
            }
        }
    }
}
```

---

## 🔄 **Update Triggers**

### **Events That Trigger Updates**:

**Hourly** (Scheduled):
- `HOURLY_RECONCILIATION` - Query fresh balances (live mode)

**On-Chain Operations**:
- `GAS_FEE_PAID` - Reduces wallet.ETH
- `STAKE_DEPOSIT` - wallet.ETH → wallet.weETH
- `COLLATERAL_SUPPLIED` - wallet.weETH → wallet.aWeETH (via index!)
- `COLLATERAL_SUPPLIED_BTC` - wallet.BTC → wallet.aBTC (via index!)
- `COLLATERAL_SUPPLIED_USDT` - wallet.USDT → wallet.aUSDT (via index!)
- `LOAN_CREATED` - Creates wallet.variableDebtWETH, adds wallet.ETH
- `LOAN_CREATED_BTC` - Creates wallet.variableDebtBTC, adds wallet.BTC
- `LOAN_CREATED_USDT` - Creates wallet.variableDebtUSDT, adds wallet.USDT
- `LOAN_REPAID` - Reduces wallet.variableDebtWETH, reduces wallet.ETH
- `LOAN_REPAID_BTC` - Reduces wallet.variableDebtBTC, reduces wallet.BTC
- `LOAN_REPAID_USDT` - Reduces wallet.variableDebtUSDT, reduces wallet.USDT
- `ATOMIC_LEVERAGE_LOOP` - Multiple changes (flash loan bundle)
- `VENUE_TRANSFER` - wallet ↔ CEX
- `KING_REWARD_DISTRIBUTION` - Adds wallet.KING (seasonal rewards)
- `KING_UNWRAPPED` - wallet.KING → wallet.EIGEN + wallet.ETHFI
- `SEASONAL_REWARDS_SOLD` - wallet.EIGEN + wallet.ETHFI → wallet.USDT (via CEX)

**CEX Operations**:
- `SPOT_TRADE` - Updates CEX token balances
- `TRADE_EXECUTED` (perp) - Updates perp_positions + CEX balance (execution cost)
- `FUNDING_PAYMENT` - Updates CEX USDT balance

**Derivative Events**:
- `PERP_OPENED` - Creates new position
- `PERP_CLOSED` - Removes position
- `PERP_ADJUSTED` - Changes position size

---

## 🔗 **Integration with Other Components**

### **Data Sources** ⭐ CRITICAL

**Backtest Mode**:
```python
# Position Monitor is SIMULATED state
# Does NOT query anything - execution managers TELL it what changed

# Example flow:
CEXExecutionManager.trade_spot('binance', 'ETH/USDT', 'BUY', 15.2)
    → Simulates trade using historical prices
    → Calculates: filled=15.2, cost=$50,000, exec_cost=$35
    → Tells Position Monitor what changed:
    position_monitor.update({
        'token_changes': [
            {'venue': 'binance', 'token': 'ETH_spot', 'delta': +15.2},
            {'venue': 'binance', 'token': 'USDT', 'delta': -50035}
        ]
    })
    
# Position Monitor just tracks what it's told
# No queries needed (simulation IS reality)
```

**Live Mode** (Two data sources):
```python
# 1. OPTIMISTIC UPDATES (Continuous - same as backtest)
CEXExecutionManager.trade_spot(...)
    → Submits REAL order to Binance API
    → Gets order fill confirmation
    → Tells Position Monitor what changed (optimistic update)

# Position Monitor tracks optimistically
position_monitor.update({'token_changes': [...]})

# 2. RECONCILIATION QUERIES (Periodic - hourly)
position_monitor.reconcile_with_live()
    → Queries ACTUAL balances:
    
    # On-chain (via Web3)
    actual_eth = await web3.eth.get_balance(wallet_address)
    actual_aweeth = await aweeth_contract.balanceOf(wallet_address)
    actual_debt = await debt_contract.balanceOf(wallet_address)
    
    # CEX (via CCXT private API)
    binance_actual = await binance_exchange.fetch_balance()
    binance_positions = await binance_exchange.fetch_positions()
    
    → Compares tracked vs actual
    → If discrepancy > threshold:
        logger.error("Balance drift detected!")
        # Sync to actual (actual is ground truth)
        position_monitor.wallet['ETH'] = actual_eth
```

**Key Distinction**:
- **Backtest**: Only optimistic updates (from execution managers)
- **Live**: Optimistic updates + periodic reconciliation queries

**Data Provider NOT Used by Position Monitor** ✅
- Position Monitor = STATE tracker (balances)
- Data Provider = MARKET data (prices, rates)
- Position Monitor doesn't need market data (just balance changes)

### **Publishes To** (Downstream):
- **Exposure Monitor** ← Position snapshot (via Redis)
- **Event Logger** ← Balance change events

### **Receives From** (Upstream):
- **CEX Execution Manager** ← Trade results (optimistic updates)
- **OnChain Execution Manager** ← Transaction results (optimistic updates)

### **Queries** (Live Mode Only, Periodic):
- **Web3 RPC** ← Actual wallet balances (hourly reconciliation)
- **CEX APIs (CCXT)** ← Actual account balances & positions (hourly reconciliation)

---

## 💻 **Implementation**

### **File**: `backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py`

### **Dependencies**:
```python
from typing import Dict, List, Optional
import redis
import json
import logging
from datetime import datetime
```

### **Core Functions**:

```python
async def update(self, changes: Dict) -> Dict:
    """
    Update positions (SYNCHRONOUS).
    
    Guarantees both token and derivative monitors update together.
    """

async def get_snapshot(self) -> Dict:
    """Get current snapshot (read-only)."""

async def reconcile_with_live(self) -> Dict:
    """Live mode only: Compare tracked vs actual balances."""

def _apply_token_change(self, change: Dict):
    """Apply single token balance change."""

def _apply_derivative_change(self, change: Dict):
    """Apply single derivative position change."""

async def _publish_update(self, snapshot: Dict):
    """Publish update to Redis."""

async def _query_web3_wallet(self) -> Dict:
    """Live mode: Query actual wallet balances."""

async def _query_cex_balances(self) -> Dict:
    """Live mode: Query actual CEX balances."""

async def _query_perp_positions(self) -> Dict:
    """Live mode: Query actual perp positions."""
```

---

## 🔧 **Mode-Specific Behavior**

### **Backtest Mode**:
```python
# Simulated balances
position_monitor.wallet['ETH'] -= 0.0035  # Direct update

# No reconciliation needed
# No live queries
# State is ground truth
```

### **Live Mode**:
```python
# Tracked balances (may drift from actual)
position_monitor.wallet['ETH'] -= 0.0035  # Update tracked

# Hourly reconciliation
actual_eth = await web3.eth.get_balance(wallet_address)
if abs(actual_eth - tracked_eth) > 0.01:
    logger.warning(f"Balance drift: tracked={tracked_eth}, actual={actual_eth}")
    # Sync to actual
    position_monitor.wallet['ETH'] = actual_eth
```

---

## 📊 **Redis Integration**

### **Published Data**:

**Key**: `position:snapshot`
```json
{
  "wallet": {...},
  "cex_accounts": {...},
  "perp_positions": {...},
  "last_updated": "2024-05-12T00:00:00Z"
}
```

**Channel**: `position:updated`
```json
{
  "timestamp": "2024-05-12T00:00:00Z",
  "trigger": "GAS_FEE_PAID",
  "changes_count": 1
}
```

### **Subscribers**:
- Exposure Monitor (recalculates on every update)
- Event Logger (logs balance change event)

---

## 🧪 **Testing**

### **Unit Tests**:
```python
def test_token_balance_update():
    monitor = PositionMonitor()
    
    # Initial state
    assert monitor.wallet['ETH'] == 0.0
    
    # Update
    monitor.update({'token_changes': [
        {'venue': 'WALLET', 'token': 'ETH', 'delta': 100.0}
    ]})
    
    # Verify
    assert monitor.wallet['ETH'] == 100.0

def test_aave_supply_uses_index():
    """Critical: aToken amount depends on liquidity index."""
    monitor = PositionMonitor()
    
    # Supply 100 weETH when index = 1.05
    weeth_to_supply = 100.0
    liquidity_index = 1.05
    aweeth_received = weeth_to_supply / liquidity_index  # 95.24
    
    monitor.update({'token_changes': [
        {'venue': 'WALLET', 'token': 'weETH', 'delta': -100.0},
        {'venue': 'WALLET', 'token': 'aWeETH', 'delta': aweeth_received}
    ]})
    
    # Verify aToken amount is index-dependent
    assert monitor.wallet['aWeETH'] == pytest.approx(95.24, abs=0.01)
    assert monitor.wallet['weETH'] == 0.0

def test_sync_token_and_derivative():
    """Token and derivative monitors update together."""
    monitor = PositionMonitor()
    
    # Atomic update
    snapshot = monitor.update({
        'token_changes': [
            {'venue': 'binance', 'token': 'USDT', 'delta': -7.50}  # Execution cost
        ],
        'derivative_changes': [
            {'venue': 'binance', 'instrument': 'ETHUSDT-PERP', 'action': 'OPEN', 'data': {...}}
        ]
    })
    
    # Both updated
    assert snapshot['cex_accounts']['binance']['USDT'] == -7.50  # Cost deducted
    assert 'ETHUSDT-PERP' in snapshot['perp_positions']['binance']  # Position opened
```

---

## 📋 **Integration Example**

### **Called By**: CEX Execution Manager

```python
# In CEXExecutionManager.trade_perp()
result = await self._execute_perp_trade('binance', 'ETHUSDT-PERP', 'SHORT', 8.562)

# Update Position Monitor
await self.position_monitor.update({
    'timestamp': timestamp,
    'trigger': 'TRADE_EXECUTED',
    'token_changes': [
        {
            'venue': 'binance',
            'token': 'USDT',
            'delta': -result['execution_cost'],
            'reason': 'PERP_EXECUTION_COST'
        }
    ],
    'derivative_changes': [
        {
            'venue': 'binance',
            'instrument': 'ETHUSDT-PERP',
            'action': 'OPEN',
            'data': {
                'size': -8.562,
                'entry_price': result['fill_price'],
                'notional_usd': result['notional']
            }
        }
    ]
})
```

### **Called By**: OnChain Execution Manager (KING Token Handling)

```python
# In OnChainExecutionManager.unwrap_king_tokens()
king_balance = 100.0  # KING tokens to unwrap
eigen_received = 50.0  # EIGEN tokens received
ethfi_received = 50.0  # ETHFI tokens received

# Update Position Monitor
await self.position_monitor.update({
    'timestamp': timestamp,
    'trigger': 'KING_UNWRAPPED',
    'token_changes': [
        {
            'venue': 'WALLET',
            'token': 'KING',
            'delta': -king_balance,
            'reason': 'KING_UNWRAPPED'
        },
        {
            'venue': 'WALLET',
            'token': 'EIGEN',
            'delta': +eigen_received,
            'reason': 'KING_UNWRAPPED'
        },
        {
            'venue': 'WALLET',
            'token': 'ETHFI',
            'delta': +ethfi_received,
            'reason': 'KING_UNWRAPPED'
        }
    ]
})
```

---

## ⚡ **Performance Considerations**

**Memory**: ~100 token balances + ~10 perp positions = minimal  
**Redis**: Publish on every update (10k+ times in backtest)  
**Optimization**: Only publish if subscribers exist (live mode)

---

## 🎯 **Success Criteria**

- [ ] Tracks all wallet tokens accurately (ETH, USDT, BTC, weETH, wstETH, aTokens, debt tokens)
- [ ] Tracks seasonal reward tokens (KING, EIGEN, ETHFI)
- [ ] Tracks all CEX balances per exchange (USDT, ETH, BTC)
- [ ] Tracks all perp positions with entry prices
- [ ] Updates synchronously (no partial state)
- [ ] Publishes to Redis for other components
- [ ] Reconciles with live balances (live mode)
- [ ] AAVE aToken amounts respect liquidity index
- [ ] Perp position tracking includes per-exchange entry prices
- [ ] KING token unwrapping properly updates EIGEN/ETHFI balances
- [ ] BTC support for basis trading strategies

---

**Status**: Specification complete, ready for implementation! ✅


