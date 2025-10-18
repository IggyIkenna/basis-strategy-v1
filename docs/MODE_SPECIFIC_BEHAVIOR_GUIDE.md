# Mode-Specific Behavior Guide

**Purpose**: Detailed technical reference for execution mode-specific behavior (backtest vs live)  
**Status**: ✅ CANONICAL REFERENCE  
**Last Updated**: October 15, 2025

---

## Overview

This guide provides comprehensive documentation of mode-specific behavior differences between backtest and live execution modes. The system maintains a mode-agnostic architecture where possible, but certain components require different behavior based on the execution mode.

**Key Principle**: Same component code handles both modes through `execution_mode` parameter, with mode-specific logic branches only where absolutely necessary.

## Canonical Sources

**This guide aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Workflow Architecture**: [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Complete workflow documentation
- **Tight Loop Architecture**: [TIGHT_LOOP_ARCHITECTURE.md](TIGHT_LOOP_ARCHITECTURE.md) - Tight loop orchestration patterns
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

---

## 5-Trigger System Overview

The PositionMonitor uses five distinct triggers with mode-specific behavior to handle position updates:

### Trigger Summary Table

| Trigger | Live Mode | Backtest Mode | Purpose |
|---------|-----------|---------------|---------|
| `execution_manager` | ✅ Apply execution + query real venues | ✅ Apply execution + set real = simulated | Tight loop orchestration |
| `position_refresh` | ✅ Query real venues (60-second cycle) | ❌ No value - path-dependent | Live balance refresh |
| `initial_capital` | ❌ Covered by position_refresh | ✅ Set starting capital | Backtest initialization |
| `seasonal_rewards` | ❌ Covered by position_refresh | ✅ Simulate staking rewards | Backtest simulation |
| `m2m_pnl` | ❌ Covered by position_refresh | ✅ Simulate M2M PnL | Backtest simulation |

### Trigger Usage Patterns

**Live Mode** uses only 2 triggers:
- `execution_manager` - During tight loop execution and reconciliation
- `position_refresh` - During 60-second refresh cycles for true balance queries

**Backtest Mode** uses all 5 triggers:
- `execution_manager` - During tight loop execution (real = simulated)
- `initial_capital` - At initialization to set starting capital
- `seasonal_rewards` - To simulate staking rewards in path-dependent loop
- `m2m_pnl` - To simulate mark-to-market PnL in path-dependent loop

---

## PositionMonitor Trigger Handling

### Complete Implementation

```python
def update_state(self, timestamp, trigger_source, execution_deltas=None):
    """
    Mode-specific balance updates with simplified trigger sources.
    """
    if trigger_source == 'execution_manager':
        # TIGHT LOOP: Apply execution + query balances (mode-specific)
        if execution_deltas:
            self._apply_execution_deltas(execution_deltas)
        self._query_venue_balances(timestamp)  # Mode-specific handling
        
    elif trigger_source == 'position_refresh':
        # LIVE ONLY: 60-second refresh cycle
        if self.execution_mode == 'live':
            self._query_venue_balances(timestamp)
        else:
            # Backtest: No value in position_refresh
            pass
            
    elif trigger_source == 'initial_capital':
        # BACKTEST ONLY: Set starting capital
        if self.execution_mode == 'backtest':
            self._apply_initial_capital()
        else:
            # Live: Covered by position_refresh
            pass
            
    elif trigger_source == 'seasonal_rewards':
        # BACKTEST ONLY: Simulate staking rewards
        if self.execution_mode == 'backtest':
            self._apply_seasonal_rewards(timestamp)
        else:
            # Live: Covered by position_refresh
            pass
            
    elif trigger_source == 'm2m_pnl':
        # BACKTEST ONLY: Simulate M2M PnL
        if self.execution_mode == 'backtest':
            self._apply_m2m_pnl(execution_deltas)
        else:
            # Live: Covered by position_refresh
            pass
```

---

## Backtest Mode Behavior

### Execution Deltas Application

```python
def _apply_execution_deltas(self, execution_deltas):
    """
    Backtest: Apply trade results to simulated positions (path-dependent).
    """
    if execution_deltas:
        # Apply trade results to simulated positions
        for asset, delta in execution_deltas.items():
            current_amount = self.simulated_positions.get(asset, {}).get('amount', 0)
            self.simulated_positions[asset] = {
                'amount': current_amount + delta,
                'timestamp': timestamp,
                'source': 'backtest_simulation'
            }
```

### Venue Balance Query

```python
def _query_venue_balances(self, timestamp):
    """
    Backtest: Real positions = simulated positions (path-dependent).
    """
    # In backtest, real positions are identical to simulated positions
    self.real_positions = self.simulated_positions.copy()
    
    # Update last positions
    self.last_positions = self.real_positions
```

### Initial Capital Setup

```python
def _apply_initial_capital(self):
    """
    Backtest: Set starting capital for simulation.
    """
    self.simulated_positions = {
        'USDT': {'amount': self.initial_capital, 'timestamp': self.start_timestamp},
        'ETH': {'amount': 0, 'timestamp': self.start_timestamp}
    }
```

### Seasonal Rewards Simulation

```python
def _apply_seasonal_rewards(self, timestamp):
    """
    Backtest: Simulate staking rewards in path-dependent loop.
    """
    # Apply staking rewards to simulated positions
    # Implementation depends on strategy mode and staking configuration
    pass
```

### Mark-to-Market PnL Simulation

```python
def _apply_m2m_pnl(self, execution_deltas):
    """
    Backtest: Simulate M2M PnL in path-dependent loop.
    """
    # Apply M2M PnL to simulated positions
    # Implementation depends on strategy mode and market data
    pass
```

**Key Principle**: In backtest mode, simulated positions ARE the real positions. No querying of external venues occurs.

---

## Live Mode Behavior

### Execution Deltas Application

```python
def _apply_execution_deltas(self, execution_deltas):
    """
    Live: Apply expected trade results to simulated positions for reconciliation.
    """
    if execution_deltas:
        # Apply expected trade results to simulated positions
        for asset, delta in execution_deltas.items():
            current_amount = self.simulated_positions.get(asset, {}).get('amount', 0)
            self.simulated_positions[asset] = {
                'amount': current_amount + delta,
                'timestamp': timestamp,
                'source': 'live_expectation'
            }
```

### Venue Balance Query

```python
def _query_venue_balances(self, timestamp):
    """
    Live: Query actual positions from venues for true balances.
    """
    # Query real positions from all venue interfaces
    venue_positions = self._query_venue_positions(timestamp)
    
    # Aggregate positions across venues
    self.real_positions = self._aggregate_venue_positions(venue_positions)
    
    # Update last positions
    self.last_positions = self.real_positions
```

### 60-Second Refresh Cycle

```python
def refresh_positions(self, timestamp):
    """
    Live: 60-second refresh cycle for true balances and PnL attribution.
    """
    # Query real balances from venues
    real_balances = self._query_venue_balances(timestamp)
    
    # Calculate exposure from real balances
    exposure = self.exposure_monitor.calculate_exposure(
        timestamp=timestamp,
        position_snapshot=real_balances,
        market_data=self.data_provider.get_data(timestamp)
    )
    
    # Calculate PnL attribution
    pnl = self.pnl_monitor.calculate_pnl(
        current_exposure=exposure,
        timestamp=timestamp
    )
    
    return {
        'positions': real_balances,
        'exposure': exposure,
        'pnl': pnl
    }
```

**Key Principle**: In live mode, simulated positions represent expected state, while real positions reflect actual venue balances. Reconciliation compares these two.

---

## PositionUpdateHandler Reconciliation

### Backtest Mode Reconciliation

```python
def _reconcile_positions(self):
    """
    Backtest: Simulated positions = real positions (always succeeds).
    """
    # In backtest, simulated and real positions are identical
    return {
        'success': True,
        'reconciliation_type': 'backtest_simulation',
        'simulated_positions': self.position_monitor.simulated_positions,
        'real_positions': self.position_monitor.real_positions,
        'message': 'Backtest mode: simulated positions match real positions'
    }
```

**Behavior**: Always returns success because simulated = real in backtest mode.

### Live Mode Reconciliation

```python
def _reconcile_positions(self):
    """
    Live: Compare simulated vs real positions with tolerance.
    """
    simulated = self.position_monitor.simulated_positions
    real = self.position_monitor.real_positions
    tolerance = self.config.get('reconciliation_tolerance', 0.01)
    
    mismatches = []
    
    # Check all assets for position mismatches
    all_assets = set(simulated.keys()) | set(real.keys())
    
    for asset in all_assets:
        sim_amount = simulated.get(asset, {}).get('amount', 0)
        real_amount = real.get(asset, {}).get('amount', 0)
        difference = abs(sim_amount - real_amount)
        
        if difference > tolerance:
            mismatches.append({
                'asset': asset,
                'simulated': sim_amount,
                'real': real_amount,
                'difference': difference,
                'tolerance': tolerance
            })
    
    if mismatches:
        return {
            'success': False,
            'reconciliation_type': 'live_mismatch',
            'mismatches': mismatches,
            'message': f'Position reconciliation failed: {len(mismatches)} mismatches found'
        }
    else:
        return {
            'success': True,
            'reconciliation_type': 'live_match',
            'simulated_positions': simulated,
            'real_positions': real,
            'message': 'Position reconciliation successful'
        }
```

**Behavior**: Compares simulated vs real with configurable tolerance. Returns failure if mismatches exceed tolerance.

---

## Execution Interface Behavior

### Backtest Mode Execution

```python
class CEXExecutionInterface:
    def execute_trade(self, symbol, side, amount, order_type):
        """
        Backtest: Simulate trade execution using historical data.
        """
        # Simulate trade execution
        execution_price = self.data_provider.get_price(symbol, self.timestamp)
        
        return {
            'success': True,
            'trade_id': f"backtest_{uuid.uuid4()}",
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'execution_price': execution_price,
            'execution_time': self.timestamp,
            'mode': 'backtest_simulation'
        }
```

**Characteristics**:
- Uses historical prices from data provider
- Generates simulated trade IDs
- Always succeeds (unless data missing)
- No network calls
- Instant execution

### Live Mode Execution

```python
class CEXExecutionInterface:
    def execute_trade(self, symbol, side, amount, order_type):
        """
        Live: Execute real trade via exchange API.
        """
        try:
            # Execute real trade
            exchange = self.exchange_clients[self.venue]
            order = exchange.create_market_order(symbol, side, amount)
            
            # Wait for order fill
            filled_order = exchange.fetch_order(order['id'])
            
            return {
                'success': True,
                'trade_id': filled_order['id'],
                'symbol': symbol,
                'side': side,
                'amount': filled_order['filled'],
                'execution_price': filled_order['average'],
                'execution_time': pd.Timestamp.now(),
                'mode': 'live_execution'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mode': 'live_execution'
            }
```

**Characteristics**:
- Makes actual exchange API calls
- Uses real trade IDs from exchange
- Can fail due to network/exchange issues
- Has execution latency
- Returns actual fill prices and amounts

---

## Key Insights

### 1. True Balances vs Simulation

**Live Mode Priority**: Use true balances from venues, not simulations
- 60-second refresh cycle queries real venues
- Reconciliation compares expected vs actual
- PnL attribution based on true balances

**Backtest Mode Priority**: Use path-dependent simulations
- No venue queries (simulated = real)
- All balance updates through simulation
- PnL based on simulated positions

### 2. Reconciliation Scope

- **During Tight Loop**: Reconciliation occurs only with `execution_manager` trigger
- **During Refresh**: No reconciliation, just true balance queries (live mode)
- **Failure Handling**: See [ERROR_HANDLING_PATTERNS.md](ERROR_HANDLING_PATTERNS.md)

### 3. Simplified Trigger Model

Live mode eliminated unnecessary complexity:
- Only 2 triggers needed (execution_manager, position_refresh)
- Staking rewards, M2M PnL covered by position_refresh
- Initial capital covered by position_refresh

Backtest mode uses all 5 triggers for path-dependent simulation.

---

## Related Documentation

### Component Specifications
- **Position Monitor**: [specs/01_POSITION_MONITOR.md](specs/01_POSITION_MONITOR.md) - Position state management
- **Position Update Handler**: [specs/11_POSITION_UPDATE_HANDLER.md](specs/11_POSITION_UPDATE_HANDLER.md) - Tight loop ownership
- **Execution Interfaces**: [specs/07A_VENUE_INTERFACES.md](specs/07A_VENUE_INTERFACES.md) - Execution implementations

### Architecture Documentation
- **Workflow Guide**: [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Complete workflow patterns
- **Tight Loop Architecture**: [TIGHT_LOOP_ARCHITECTURE.md](TIGHT_LOOP_ARCHITECTURE.md) - Orchestration patterns
- **Error Handling**: [ERROR_HANDLING_PATTERNS.md](ERROR_HANDLING_PATTERNS.md) - Error and retry patterns
- **Reference Architecture**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Core principles

---

**Status**: Complete technical reference for mode-specific behavior  
**Last Reviewed**: October 15, 2025  
**Reviewer**: Documentation Refactor Implementation


