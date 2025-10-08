# Advanced Rebalancing - Cross-Venue Transfer & Emergency Protocols 🔄

**Component**: Advanced Rebalancing System  
**Responsibility**: Intelligent cross-venue transfers and emergency rebalancing for complex scenarios  
**Priority**: ⭐⭐⭐ CRITICAL (Safety & yield optimization for leveraged strategies)  
**Backend Files**: 
- `backend/src/basis_strategy_v1/core/rebalancing/transfer_manager.py`
- **NOT YET INTEGRATED**: `backend/src/basis_strategy_v1/core/strategies/components/strategy_manager.py`

---

## 🎯 **Purpose**

Handle complex multi-venue rebalancing scenarios for leveraged strategies (eth_leveraged, usdt_market_neutral).

**Key Principles**:
- **Cross-venue intelligence**: Optimal asset selection for transfers (AAVE ↔ CEX ↔ EtherFi)
- **Yield preservation**: Minimize yield loss during rebalancing
- **Emergency protocols**: Fast response to critical situations (margin calls, liquidations)
- **Cost optimization**: Balance transfer costs vs yield impact

**Critical For**:
- USDT Market-Neutral mode (most complex: AAVE + multi-CEX hedging)
- ETH Leveraged mode with hedging (USDT share class)
- Any strategy with both on-chain and off-chain positions

**Not Needed For**:
- Pure Lending (single venue)
- BTC Basis (CEX only)
- ETH Staking Only (no hedging)

---

## 🏗️ **Architecture**

### **Implementation Status: PARTIALLY IMPLEMENTED** 

**✅ IMPLEMENTED: CrossVenueTransferManager** (1068 lines)
- Optimal transfer routing between venues
- Asset selection (ETH vs USDT vs weETH)
- Cost analysis and safety validation
- Transfer execution sequencing
- **INCLUDES**: ComplexScenarioRebalancer, EmergencyRebalancingProtocols, RebalancingOptimizer classes

**❌ NOT INTEGRATED: StrategyManager Integration**
- StrategyManager currently uses simple rebalancing logic
- Advanced rebalancing classes exist but are not used
- No mode-specific initialization of transfer manager
- No emergency protocol integration

---

## 📊 **Data Structures**

### **Transfer Instruction**

```python
{
    'source_venue': 'AAVE',      # or 'ETHERFI', 'BYBIT', 'BINANCE', 'OKX'
    'target_venue': 'BYBIT',
    'amount_usd': 10000.0,
    'purpose': 'Margin support',
    
    'transfer_plan': {
        'asset': 'USDT',                    # Optimal asset for transfer
        'total_cost': 35.50,                # Gas + fees + opportunity cost
        'cost_bps': 3.55,                   # Cost in basis points
        'route_description': 'Withdraw USDT from AAVE → Bybit margin',
        'steps': [
            {
                'step': 1,
                'action': 'withdraw',
                'venue': 'AAVE',
                'token': 'USDT',
                'amount': 10000,
                'description': 'Withdraw $10,000 USDT from AAVE'
            },
            {
                'step': 2,
                'action': 'transfer',
                'venue': 'BYBIT',
                'token': 'USDT',
                'amount': 10000,
                'description': 'Transfer $10,000 USDT to Bybit margin'
            }
        ]
    }
}
```

---

## 💻 **Core Functions**

### **CrossVenueTransferManager**

```python
class CrossVenueTransferManager:
    """Manage intelligent transfers between venues."""
    
    async def execute_optimal_transfer(
        self,
        source_venue: str,
        target_venue: str,
        amount_usd: float,
        market_data,
        purpose: str = "Rebalancing"
    ) -> List[Trade]:
        """
        Execute optimal transfer with cost minimization.
        
        Safety Checks:
        1. Minimum transfer size ($5k minimum)
        2. Maximum transfer size ($100k safety limit)
        3. Source venue safety (won't breach LTV/margin)
        4. Target venue capacity
        
        Returns:
            List of Trade objects for execution
        """
    
    async def _determine_optimal_transfer_asset(
        self,
        source_venue: str,
        target_venue: str,
        amount_usd: float,
        market_data
    ) -> str:
        """
        Choose optimal asset for transfer.
        
        Logic:
        - ETHERFI → BYBIT: ETH (free unstaking, direct transfer)
        - ETHERFI → AAVE: weETH (keep as collateral, most efficient)
        - AAVE → BYBIT: USDT (direct margin deposit)
        - BYBIT → AAVE: USDT (direct collateral)
        - BYBIT → ETHERFI: ETH (for staking)
        
        Returns:
            Asset symbol ('ETH', 'USDT', 'weETH')
        """
    
    async def _calculate_transfer_cost(
        self,
        source_venue: str,
        target_venue: str,
        amount_usd: float,
        asset: str
    ) -> float:
        """
        Calculate total transfer cost.
        
        Includes:
        - Gas costs (2-3 transactions typically)
        - Exchange withdrawal fees
        - Opportunity cost (lost staking yield during transfer)
        - Conversion fees if asset swap needed
        """
```

---

### **EmergencyRebalancingProtocols**

```python
class EmergencyRebalancingProtocols:
    """Handle critical rebalancing situations."""
    
    async def execute_emergency_rebalancing(
        self,
        emergency_type: str,  # 'LTV_CRITICAL', 'MARGIN_CRITICAL', 'CROSS_VENUE_CRITICAL'
        health_data: Dict[str, Any],
        market_data
    ) -> List[Trade]:
        """
        Execute emergency protocols.
        
        Priority Order:
        1. MARGIN_CRITICAL: Prevent CEX liquidation (catastrophic - lose ALL margin)
        2. LTV_CRITICAL: Prevent AAVE liquidation (expensive - lose bonus %)
        3. CROSS_VENUE_CRITICAL: Rebalance venue imbalances
        """
    
    async def _emergency_margin_support(
        self,
        health_data: Dict[str, Any],
        market_data
    ) -> List[Trade]:
        """
        Emergency margin support to prevent CEX liquidation.
        
        Priority:
        1. Use available USDT in wallet (fastest)
        2. Transfer from AAVE if LTV allows (fast)
        3. Emergency unstaking from EtherFi (slower, yield loss)
        4. Reduce position size (last resort)
        """
    
    async def _emergency_ltv_reduction(
        self,
        health_data: Dict[str, Any],
        market_data
    ) -> List[Trade]:
        """
        Emergency LTV reduction to prevent AAVE liquidation.
        
        Priority:
        1. Use wallet USDT (fastest)
        2. Transfer from Bybit margin (if available)
        3. Emergency unstaking from EtherFi
        """
```

---

### **ComplexScenarioRebalancer**

```python
class ComplexScenarioRebalancer:
    """Advanced rebalancing for complex multi-venue leveraged scenarios."""
    
    async def handle_complex_leveraged_rebalancing(
        self,
        health_assessment: Dict[str, Any],
        market_data
    ) -> List[Trade]:
        """
        Handle complex scenarios with multiple debts + restaking + basis trading.
        
        Detection:
        - Multiple debt types (ETH + USDT debt)
        - Restaking enabled (weETH/eETH)
        - Basis trading (CEX hedging)
        
        Priority:
        1. Critical margin (CEX): Immediate margin support
        2. Multi-debt LTV: Optimize debt composition (reduce least efficient)
        3. Cross-venue arbitrage: Yield optimization
        """
    
    async def _handle_complex_ltv_optimization(
        self,
        aave_health: Dict[str, Any],
        market_data
    ) -> List[Trade]:
        """
        Optimize multi-debt LTV.
        
        Strategy:
        - Calculate debt efficiency (yield/cost ratio per debt type)
        - Reduce least efficient debt first
        - Preserve high-yield debt (staking leverage)
        - Reduce low-yield debt (basis trade leverage)
        """
```

---

### **RebalancingOptimizer**

```python
class RebalancingOptimizer:
    """Optimize rebalancing for yield preservation."""
    
    async def analyze_rebalancing_yield_impact(
        self,
        proposed_transfers: List[Dict[str, Any]],
        market_data
    ) -> Dict[str, Any]:
        """
        Analyze yield impact of proposed rebalancing.
        
        Calculates:
        - Current yield (staking + lending + funding)
        - Projected yield after transfers
        - Net yield impact
        - Transfer costs
        - Recommendation: EXECUTE, NEUTRAL, or DEFER
        
        Returns:
            {
                'current_yield_breakdown': {...},
                'projected_yield_breakdown': {...},
                'net_yield_impact_usd': float,
                'total_transfer_cost_usd': float,
                'net_benefit_usd': float,
                'recommendation': 'EXECUTE' | 'NEUTRAL' | 'DEFER',
                'rationale': str
            }
        """
```

---

## 🔗 **Integration with StrategyManager**

### **Current Implementation Status: NOT INTEGRATED**

**❌ CURRENT STATE**: StrategyManager uses simple rebalancing logic and does not integrate with the advanced rebalancing system.

**Current StrategyManager Rebalancing**:
```python
class StrategyManager:
    """Current implementation with simple rebalancing."""
    
    def check_rebalancing_needed(self, risk_metrics: Dict) -> Optional[str]:
        """Check if rebalancing needed."""
        # Priority 1: Margin critical (prevent CEX liquidation)
        if risk_metrics.get('cex_margin', {}).get('any_critical', False):
            return 'MARGIN_CRITICAL'
        
        # Priority 2: Delta drift (maintain market neutrality)
        if risk_metrics.get('delta', {}).get('critical', False):
            return 'DELTA_DRIFT_CRITICAL'
        
        # Priority 3: AAVE LTV (prevent AAVE liquidation)
        if risk_metrics.get('aave', {}).get('critical', False):
            return 'AAVE_LTV_CRITICAL'
        
        return None
    
    # Simple rebalancing logic - no advanced transfer manager integration
    def _calculate_rebalance_btc_basis_positions(self, current_exposure: Dict) -> Dict:
        """Simple BTC basis rebalancing - no cross-venue transfers."""
        # ... existing simple logic ...
```

### **Planned Integration (NOT YET IMPLEMENTED)**

```python
class StrategyManager:
    """Planned integration with advanced rebalancing."""
    
    def __init__(self, config, position_monitor, risk_monitor):
        # ... existing initialization ...
        
        # TODO: Initialize advanced rebalancing for complex modes
        if self.mode in ['usdt_market_neutral', 'eth_leveraged_hedged']:
            from ..rebalancing.transfer_manager import (
                CrossVenueTransferManager,
                EmergencyRebalancingProtocols,
                RebalancingOptimizer
            )
            
            self.transfer_manager = CrossVenueTransferManager(config, portfolio)
            self.emergency_protocols = EmergencyRebalancingProtocols(config, portfolio, self.transfer_manager)
            self.rebalancing_optimizer = RebalancingOptimizer(config)
        else:
            # Simple modes don't need advanced rebalancing
            self.transfer_manager = None
            self.emergency_protocols = None
    
    async def handle_rebalancing(self, risk_data: Dict) -> List[Trade]:
        """
        TODO: Handle rebalancing (uses advanced rebalancing for complex modes).
        """
        # Check for emergency
        if risk_data['overall_status'] == 'CRITICAL':
            if self.emergency_protocols:
                # Use advanced emergency protocols
                return await self.emergency_protocols.execute_emergency_rebalancing(
                    emergency_type=self._determine_emergency_type(risk_data),
                    health_data=risk_data,
                    market_data=self.data_provider.get_market_data_snapshot(timestamp)
                )
            else:
                # Simple emergency logic for basic modes
                return await self._simple_emergency_rebalancing(risk_data)
        
        # Standard rebalancing
        if self.transfer_manager:
            # Analyze yield impact before executing
            yield_analysis = await self.rebalancing_optimizer.analyze_rebalancing_yield_impact(
                proposed_transfers, market_data
            )
            
            if yield_analysis['recommendation'] == 'EXECUTE':
                # Execute transfers using CrossVenueTransferManager
                return await self._execute_complex_rebalancing(risk_data)
        else:
            # Simple rebalancing for basic modes
            return await self._simple_rebalancing(risk_data)
```

---

## 🧪 **Testing Requirements**

### **Unit Tests**

```python
# tests/unit/rebalancing/test_transfer_manager.py

def test_optimal_transfer_asset_selection():
    """Test optimal asset selection for different venue pairs."""
    transfer_manager = CrossVenueTransferManager(config, portfolio)
    
    # ETHERFI → BYBIT should use ETH
    asset = transfer_manager._determine_optimal_transfer_asset('ETHERFI', 'BYBIT', 10000, market_data)
    assert asset == 'ETH'
    
    # AAVE → BYBIT should use USDT
    asset = transfer_manager._determine_optimal_transfer_asset('AAVE', 'BYBIT', 10000, market_data)
    assert asset == 'USDT'

def test_emergency_margin_support():
    """Test emergency margin support protocols."""
    emergency = EmergencyRebalancingProtocols(config, portfolio, transfer_manager)
    
    health_data = {
        'venue_breakdown': {
            'bybit': {
                'margin_ratio': 0.11,  # Just above liquidation
                'margin_shortfall_usd': 5000
            }
        }
    }
    
    trades = await emergency._emergency_margin_support(health_data, market_data)
    
    # Should generate margin support trades
    assert len(trades) > 0
    assert trades[0].purpose == 'EMERGENCY: Margin support'

def test_yield_impact_analysis():
    """Test rebalancing yield impact analysis."""
    optimizer = RebalancingOptimizer(config)
    
    proposed_transfers = [
        {'from_venue': 'ETHERFI', 'to_venue': 'BYBIT', 'amount_usd': 10000}
    ]
    
    analysis = await optimizer.analyze_rebalancing_yield_impact(proposed_transfers, market_data)
    
    assert 'recommendation' in analysis
    assert analysis['recommendation'] in ['EXECUTE', 'NEUTRAL', 'DEFER']
    assert 'net_benefit_usd' in analysis
```

---

## 🎯 **Mode-Specific Usage**

### **USDT Market-Neutral** (Uses ALL features)

```python
# Uses all 4 advanced rebalancing classes
# - CrossVenueTransferManager: AAVE ↔ Binance/Bybit/OKX
# - ComplexScenarioRebalancer: Multi-debt optimization
# - EmergencyRebalancingProtocols: Critical situation handling
# - RebalancingOptimizer: Yield-preserving decisions
```

### **ETH Leveraged (USDT Share Class)** (Uses transfer + emergency)

```python
# Uses 2 classes:
# - CrossVenueTransferManager: AAVE ↔ CEX transfers
# - EmergencyRebalancingProtocols: Emergency protocols
# 
# Does NOT use:
# - ComplexScenarioRebalancer (single debt type)
# - RebalancingOptimizer (simpler yield analysis)
```

### **Simple Modes** (No advanced rebalancing)

```python
# Pure Lending, BTC Basis, ETH Staking Only:
# - Don't initialize any advanced rebalancing classes
# - StrategyManager handles simple rebalancing logic
```

---

## 🚨 **Emergency Scenarios**

### **Scenario 1: CEX Margin Critical**

**Trigger**: Margin ratio < 12% (critical threshold)

**Response**:
1. Calculate margin shortfall
2. Identify fastest source (AAVE > EtherFi > reduce position)
3. Execute emergency transfer via CrossVenueTransferManager
4. Log emergency event

**Typical Flow** (Bybit margin critical):
```
1. Withdraw USDT from AAVE (if LTV safe)
2. Transfer to Bybit margin account
3. Reduce perp short proportionally (maintain delta neutrality)
4. Log: EMERGENCY_MARGIN_SUPPORT
```

---

### **Scenario 2: AAVE LTV Critical**

**Trigger**: LTV > 90% or Health Factor < 1.1

**Response**:
1. Calculate collateral needed
2. Source: Wallet USDT > Bybit margin > EtherFi unstaking
3. Execute emergency transfer
4. Supply to AAVE to reduce LTV

**Typical Flow**:
```
1. Use wallet USDT if available (fastest)
2. If insufficient: Transfer from Bybit
3. If still insufficient: Emergency unstake from EtherFi
4. Supply all to AAVE
5. Log: EMERGENCY_LTV_REDUCTION
```

---

### **Scenario 3: Cross-Venue Imbalance**

**Trigger**: Large P&L imbalance between venues (>$10k difference)

**Response**:
1. Identify excess venue (largest positive P&L)
2. Identify deficit venue (largest negative P&L)
3. Transfer from excess to deficit
4. Rebalance to target allocation

---

## 🔧 **Yield Optimization Logic**

### **Transfer Cost-Benefit Analysis**

```python
# Calculate current yield
current_yield = {
    'staking': $4000/year (weETH staking),
    'lending': $2000/year (AAVE supply),
    'funding': $8000/year (CEX funding),
    'borrowing_cost': -$3000/year (AAVE borrow)
}
total_current = $11,000/year

# Proposed: Transfer $10k from EtherFi to Bybit for margin support
projected_yield = {
    'staking': $3600/year (lost $400 from unstaking),
    'lending': $2000/year (unchanged),
    'funding': $8200/year (gained $200 from better margin efficiency),
    'borrowing_cost': -$3000/year (unchanged)
}
total_projected = $10,800/year

# Net impact: -$200/year yield loss
# Transfer cost: $50 (one-time)

# Decision:
if net_impact > transfer_cost:
    recommendation = 'EXECUTE'  # Long-term benefit
elif abs(net_impact) < transfer_cost * 0.5:
    recommendation = 'NEUTRAL'  # Minimal impact
else:
    recommendation = 'DEFER'  # Yield loss too high
```

---

## 🎯 **Integration with StrategyManager**

### **Rebalancing Decision Flow**

```python
# In StrategyManager.handle_rebalancing()

# 1. Check if advanced rebalancing needed
if self.mode in ['usdt_market_neutral', 'eth_leveraged_hedged']:
    
    # 2. Emergency check
    if risk_data['overall_status'] == 'CRITICAL':
        trades = await self.emergency_protocols.execute_emergency_rebalancing(
            emergency_type, health_data, market_data
        )
    
    # 3. Standard rebalancing with yield optimization
    else:
        # Generate proposed transfers
        proposed_transfers = self._generate_rebalancing_transfers(risk_data)
        
        # Analyze yield impact
        yield_analysis = await self.rebalancing_optimizer.analyze_rebalancing_yield_impact(
            proposed_transfers, market_data
        )
        
        # Execute if beneficial
        if yield_analysis['recommendation'] == 'EXECUTE':
            trades = []
            for transfer in proposed_transfers:
                transfer_trades = await self.transfer_manager.execute_optimal_transfer(
                    transfer['from_venue'],
                    transfer['to_venue'],
                    transfer['amount_usd'],
                    market_data,
                    purpose='Yield-optimized rebalancing'
                )
                trades.extend(transfer_trades)
        else:
            logger.info(f"Deferring rebalancing: {yield_analysis['rationale']}")
            trades = []

else:
    # Simple modes: Direct rebalancing without advanced logic
    trades = await self._simple_rebalancing(risk_data)
```

---

## 🧪 **Success Criteria**

### **✅ IMPLEMENTED**
- [x] CrossVenueTransferManager handles all venue combinations
- [x] Optimal asset selection minimizes costs
- [x] Safety checks prevent unsafe transfers
- [x] Emergency protocols respond in priority order
- [x] Yield impact analysis accurate
- [x] Complex scenario detection works
- [x] Multi-debt optimization correct
- [x] All transfer costs calculated

### **❌ NOT IMPLEMENTED**
- [ ] Integration tests cover emergency scenarios
- [ ] Mode-specific initialization correct
- [ ] StrategyManager integration with advanced rebalancing
- [ ] Emergency protocol integration in StrategyManager
- [ ] Complex mode detection and initialization

---

## 📝 **Usage Notes**

**When to Use Advanced Rebalancing**:
- Complex leveraged scenarios (multiple venues + multiple debts)
- Margin critical situations requiring fast transfers
- LTV critical requiring optimal collateral movement
- Yield optimization during routine rebalancing

**When NOT to Use**:
- Simple single-venue strategies (pure lending)
- Simple two-venue strategies (BTC basis - CEX only)
- Conservative strategies without leverage

**Performance Impact**:
- Additional ~10-20ms per rebalancing decision (yield analysis)
- Worth it for $10k+ transfers (saves opportunity cost)
- Negligible for backtest (pre-calculated paths)

---

**Status**: Advanced Rebalancing classes implemented but NOT INTEGRATED with StrategyManager. Core transfer logic complete, integration pending. 🔧

---

## 📋 **Implementation Notes**

### **Current State**
- **✅ COMPLETE**: All 4 advanced rebalancing classes are fully implemented in `transfer_manager.py`
- **❌ MISSING**: Integration with `StrategyManager` - currently uses simple rebalancing logic
- **❌ MISSING**: Mode-specific initialization of transfer manager
- **❌ MISSING**: Emergency protocol integration in rebalancing flow

### **Integration Requirements**
To complete the advanced rebalancing system, the following integration work is needed:

1. **StrategyManager Integration**:
   - Import transfer manager classes in `strategy_manager.py`
   - Add mode-specific initialization logic
   - Replace simple rebalancing with advanced rebalancing calls

2. **Emergency Protocol Integration**:
   - Connect emergency triggers to emergency protocols
   - Integrate with existing `check_rebalancing_needed()` method

3. **Testing Integration**:
   - Add integration tests for emergency scenarios
   - Test mode-specific initialization
   - Validate cross-venue transfer execution

### **Files to Modify**
- `backend/src/basis_strategy_v1/core/strategies/components/strategy_manager.py` - Add integration
- `tests/integration/test_advanced_rebalancing.py` - Add integration tests
- `tests/unit/rebalancing/test_transfer_manager.py` - Add unit tests

