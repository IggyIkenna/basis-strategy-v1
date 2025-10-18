 # Seasonal Rewards and M2M PnL Implementation Gap

**Date**: October 15, 2025  
**Status**: Critical Gap Identified  
**Reporter**: User (Ikenna)

---

## Executive Summary

The `WORKFLOW_REFACTOR_SPECIFICATION.md` defines 5 trigger sources for position updates, but **2 of them are not implemented** and **never called** in the actual backtest workflow:

1. ✅ `initial_capital` - **IMPLEMENTED** (called once at backtest start)
2. ✅ `venue_manager` - **IMPLEMENTED** (called during tight loop)
3. ✅ `position_refresh` - **IMPLEMENTED** (called in live mode only)
4. ❌ `seasonal_rewards` - **NOT IMPLEMENTED** (stub exists but never called)
5. ❌ `m2m_pnl` - **NOT IMPLEMENTED** (stub exists but never called)

---

## Current Implementation Status

### What EXISTS in Code

#### Position Monitor Stub Methods
```python
# backend/src/basis_strategy_v1/core/components/position_monitor.py lines 869-898

def _apply_seasonal_rewards(self, timestamp: pd.Timestamp) -> None:
    """
    Apply seasonal rewards to simulated positions (backtest only).
    
    Args:
        timestamp: Current timestamp
    """
    try:
        # Apply staking rewards to simulated positions
        # This would be implemented based on specific staking logic
        pass  # ❌ NO IMPLEMENTATION
    except Exception as e:
        logger.error(f"Error applying seasonal rewards: {e}")
        raise

def _apply_m2m_pnl(self, timestamp: pd.Timestamp, execution_deltas: Dict) -> None:
    """
    Apply M2M PnL to simulated positions (backtest only).
    
    Args:
        timestamp: Current timestamp
        execution_deltas: Execution deltas for M2M calculation
    """
    try:
        # Apply M2M PnL to simulated positions
        # This would be implemented based on specific M2M logic
        pass  # ❌ NO IMPLEMENTATION
    except Exception as e:
        logger.error(f"Error applying M2M PnL: {e}")
        raise
```

#### Trigger Routing Logic
```python
# backend/src/basis_strategy_v1/core/components/position_monitor.py lines 640-646

elif trigger_source == 'seasonal_rewards':
    if self.execution_mode == 'backtest':
        self._apply_seasonal_rewards(timestamp)  # ✅ ROUTING EXISTS
        
elif trigger_source == 'm2m_pnl':
    if self.execution_mode == 'backtest':
        self._apply_m2m_pnl(timestamp, execution_deltas)  # ✅ ROUTING EXISTS
```

### What's MISSING

#### No Calls in Event Engine
```python
# backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py

# ✅ initial_capital IS called (line 414)
self.position_monitor.update_state(start_dt, 'initial_capital', None)

# ❌ seasonal_rewards is NEVER called
# ❌ m2m_pnl is NEVER called
```

**Grep Confirmation**:
```bash
$ grep -r "seasonal_rewards" backend/src/basis_strategy_v1/core/event_engine/
# NO RESULTS

$ grep -r "m2m_pnl" backend/src/basis_strategy_v1/core/event_engine/
# NO RESULTS
```

---

## Why This Matters

### 1. Incomplete Backtest Simulation

**Seasonal Rewards** are critical for strategies involving staking:
- Leveraged staking (ETH/BTC staked with leverage)
- Restaking protocols (EigenLayer, Symbiotic, etc.)
- Staking rewards compound over time and affect:
  - Position balances
  - Exposure calculations
  - P&L attribution
  - Risk assessment

**Example**: Leveraged ETH staking strategy
- Strategy stakes 100 ETH with 2x leverage (200 ETH total staked)
- Expected staking APR: 3.5%
- **WITHOUT seasonal_rewards trigger**: Backtest shows only funding costs and price changes
- **WITH seasonal_rewards trigger**: Backtest includes staking income, making strategy profitable

### 2. Missing M2M PnL Updates

**Mark-to-Market PnL** is critical for derivatives and perpetuals:
- Perp funding payments settle periodically (every 8 hours typically)
- CEX exchanges automatically settle funding to account balance
- This changes available capital without explicit trades
- Affects:
  - Available capital for next orders
  - Leverage ratios
  - Risk calculations
  - Position reconciliation

**Example**: BTC basis trade
- Long spot BTC: $100,000
- Short BTC perp: $100,000 notional
- Funding rate: +0.01% (pay funding as short)
- Every 8 hours: -$10 funding cost settled to balance
- **WITHOUT m2m_pnl trigger**: Balance doesn't reflect settled funding
- **WITH m2m_pnl trigger**: Balance updates match real CEX behavior

---

## How This Should Work (Per Specification)

### Backtest Workflow with All Triggers

```python
# INITIALIZATION (once at start)
self.position_monitor.update_state(start_dt, 'initial_capital', None)

# MAIN LOOP (each timestep)
for timestamp in timestamps:
    
    # 1. Check if seasonal rewards should be applied
    if self._should_apply_seasonal_rewards(timestamp):
        self.position_monitor.update_state(
            timestamp, 
            'seasonal_rewards', 
            None
        )
    
    # 2. Process strategy and orders
    strategy_orders = self.strategy_manager.generate_orders(...)
    
    if strategy_orders:
        # 3. Execute orders with tight loop
        for order in strategy_orders:
            execution_result = self.venue_manager.execute_order(order)
            
            # 4. Reconcile execution (venue_manager trigger)
            self.position_monitor.update_state(
                timestamp,
                'venue_manager',
                execution_result['deltas']
            )
    
    # 5. Check if M2M settlement should occur
    if self._should_apply_m2m_settlement(timestamp):
        m2m_deltas = self._calculate_m2m_settlement(timestamp)
        self.position_monitor.update_state(
            timestamp,
            'm2m_pnl',
            m2m_deltas
        )
    
    # 6. Calculate exposure, risk, PnL (using updated positions)
    exposure = self.exposure_monitor.calculate_exposure(...)
    risk = self.risk_monitor.assess_risk(...)
    pnl = self.pnl_monitor.calculate_pnl(...)
```

---

## Reconciliation Strategy Options

### Option 1: Implement Missing Triggers (High Effort, High Fidelity)

**Pros**:
- Most accurate backtest simulation
- Matches specification exactly
- Handles complex staking/funding scenarios
- Future-proof for new strategy modes

**Cons**:
- Significant implementation effort
- Need to determine when to apply triggers
- Need strategy-specific logic for calculations
- Adds complexity to backtest loop

**Implementation Checklist**:
- [ ] Define trigger timing logic (`_should_apply_seasonal_rewards`, `_should_apply_m2m_settlement`)
- [ ] Implement `_apply_seasonal_rewards()` with actual staking calculations
- [ ] Implement `_apply_m2m_pnl()` with actual funding settlement logic
- [ ] Add trigger calls to `EventDrivenStrategyEngine._process_timestep()`
- [ ] Test with leveraged staking and basis strategies
- [ ] Update documentation to reflect implementation

### Option 2: Fold Into Existing Triggers (Medium Effort, Good Fidelity)

**Approach**: Handle seasonal rewards and M2M PnL within existing `venue_manager` trigger

**Pros**:
- Simpler implementation
- No new trigger timing logic needed
- Works within existing architecture
- Still accurate for most scenarios

**Cons**:
- Less explicit separation of concerns
- Harder to debug specific reward/settlement issues
- Doesn't match specification exactly

**Implementation**:
```python
# In PositionMonitor._query_venue_balances()
def _query_venue_balances(self, timestamp: pd.Timestamp):
    """
    Query venue balances with automatic seasonal rewards and M2M PnL.
    """
    if self.execution_mode == 'backtest':
        # Copy simulated to real
        self.real_positions = self.simulated_positions.copy()
        
        # Apply any pending seasonal rewards
        self._apply_pending_seasonal_rewards(timestamp)
        
        # Apply any pending M2M settlements
        self._apply_pending_m2m_settlements(timestamp)
        
    elif self.execution_mode == 'live':
        # Query real venues (includes rewards and settlements automatically)
        self.real_positions = self._query_real_venues(timestamp)
```

### Option 3: Remove Triggers from Specification (Low Effort, Lower Fidelity)

**Approach**: Acknowledge these triggers aren't needed for current strategy modes

**Pros**:
- No implementation needed
- Aligns specification with reality
- Simpler architecture

**Cons**:
- Less accurate for staking strategies
- Less accurate for funding settlements
- Limits future strategy options
- Technical debt

**Documentation Updates**:
- Update `WORKFLOW_REFACTOR_SPECIFICATION.md` to only include 3 triggers
- Update `MODE_SPECIFIC_BEHAVIOR_GUIDE.md` to remove references
- Update component specs to remove trigger routing
- Add ADR explaining why triggers were removed

---

## Current Strategy Mode Analysis

### Pure Lending (pure_lending_usdt)
- **Needs seasonal_rewards?**: ❌ No - lending interest accumulates continuously
- **Needs m2m_pnl?**: ❌ No - no perps/futures involved
- **Current Implementation**: ✅ Adequate

### BTC Basis (btc_basis)
- **Needs seasonal_rewards?**: ❌ No - no staking involved
- **Needs m2m_pnl?**: ⚠️ YES - funding settlements every 8 hours
- **Current Implementation**: ⚠️ Missing M2M updates

### ETH Basis (eth_basis)
- **Needs seasonal_rewards?**: ❌ No - no staking involved (unless leveraged staking variant)
- **Needs m2m_pnl?**: ⚠️ YES - funding settlements every 8 hours
- **Current Implementation**: ⚠️ Missing M2M updates

### Leveraged Staking (if planned)
- **Needs seasonal_rewards?**: ✅ YES - critical for staking income
- **Needs m2m_pnl?**: ⚠️ YES - if using perps for hedge
- **Current Implementation**: ❌ Cannot accurately backtest

---

## Recommended Path Forward

### Recommended: Option 2 (Fold Into Existing Triggers)

**Rationale**:
1. **Current needs**: BTC/ETH basis strategies need M2M PnL for funding settlements
2. **Future needs**: Leveraged staking will need seasonal rewards
3. **Simplicity**: Don't add more trigger timing complexity
4. **Accuracy**: Can still be very accurate with proper implementation

**Implementation Plan**:

#### Phase 1: M2M PnL (Critical for Current Strategies)
1. Implement funding settlement calculation in `PnLCalculator`
2. Apply settlements within `_query_venue_balances()` during backtest
3. Test with BTC/ETH basis strategies
4. Validate funding settlements match expected rates

#### Phase 2: Seasonal Rewards (Future Strategies)
1. Implement staking reward calculation based on strategy mode
2. Apply rewards within `_query_venue_balances()` during backtest
3. Test with leveraged staking strategies
4. Validate rewards match expected APRs

#### Phase 3: Documentation Update
1. Update `WORKFLOW_REFACTOR_SPECIFICATION.md` to reflect folded approach
2. Update component specs to remove separate trigger routing
3. Add implementation details to `MODE_SPECIFIC_BEHAVIOR_GUIDE.md`
4. Create ADR documenting decision and rationale

---

## Impact Assessment

### If We Do Nothing

**BTC/ETH Basis Backtests**:
- ❌ Missing funding settlement updates to balance
- ❌ Leverage ratios drift over time
- ❌ Risk calculations become inaccurate
- ❌ P&L attribution missing funding components
- ⚠️ Cannot accurately compare backtest to live trading

**Leveraged Staking Backtests**:
- ❌ Missing staking reward income
- ❌ Strategy appears unprofitable when it's actually profitable
- ❌ Cannot evaluate strategy viability
- ⚠️ Cannot deploy to production confidently

### If We Implement (Option 2)

**BTC/ETH Basis Backtests**:
- ✅ Accurate funding settlements
- ✅ Correct leverage ratios over time
- ✅ Accurate risk calculations
- ✅ Complete P&L attribution
- ✅ Backtest matches live trading behavior

**Leveraged Staking Backtests**:
- ✅ Accurate staking income
- ✅ Strategy profitability correctly calculated
- ✅ Can evaluate strategy viability
- ✅ Confident production deployment

---

## Next Steps

1. **Decision Required**: Choose reconciliation option (recommend Option 2)
2. **Priority Assessment**: Determine urgency based on strategy deployment timeline
3. **Implementation**: Execute chosen option with proper testing
4. **Validation**: Run backtests and compare to expected behavior
5. **Documentation**: Update all affected docs to match implementation

---

## Related Documents

- `WORKFLOW_REFACTOR_SPECIFICATION.md` - Original specification defining 5 triggers
- `MODE_SPECIFIC_BEHAVIOR_GUIDE.md` - Mode-specific behavior patterns
- `docs/specs/01_POSITION_MONITOR.md` - Position monitor component spec
- `docs/specs/11_POSITION_UPDATE_HANDLER.md` - Position update handler spec
- `backend/src/basis_strategy_v1/core/components/position_monitor.py` - Implementation

---

**Status**: Awaiting decision on reconciliation approach


