# Repository Integration Plan - Complete Implementation Guide 🏗️

**Purpose**: Complete guide for backend/frontend integration and cleanup  
**Status**: ✅ CORE COMPONENTS IMPLEMENTED - Critical issues remain  
**Timeline**: 🔄 1-2 WEEKS TO PRODUCTION READY - Critical fixes needed  
**Updated**: October 6, 2025 - Updated to reflect actual implementation status

---

## 📚 **Key References**

- **Tasks & Acceptance Criteria** → [REQUIREMENTS.md](REQUIREMENTS.md)
- **Timeline & Phases** → [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)
- **Architecture Decisions** → [ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md)
- **Component Specifications** → [specs/](specs/)

---

## 🎯 **Current Status**

### ✅ **Core Components Implemented** (95%)
- ✅ All 9 components exist with correct file structure
- ✅ Config system implemented (YAML modes, venues, share classes)
- ✅ Data validation system working
- ✅ AAVE index mechanics correctly implemented
- ✅ Frontend wizard components exist
- ✅ Test infrastructure in place (47 test files)
- ✅ Execution interfaces architecture implemented
- ✅ Live data provider implemented
- ✅ Transfer execution interface implemented
- ✅ Cross-venue transfer orchestration working
- ✅ Seamless backtest/live mode switching
- ✅ Error code system implemented
- ✅ Liquidation simulation working
- ✅ KING token handling complete
- ✅ Seasonal rewards applied correctly
- ✅ target_apy/max_drawdown integrated

### 🔴 **Critical Issues Remaining**
- 🔄 **Pure Lending Yield Calculation**: Unrealistic 1166% APY (should be 3-8%)
- 🔄 **Scripts Directory Quality Gates**: Only 5/14 scripts passing (35.7%)
- 🔄 **RiskMonitor Data Provider Compatibility**: API backtest endpoint fails
- 🔄 **Phase 1 Quality Gates Script**: Division by zero error prevents validation

### 🔴 **CRITICAL Fixes Status** (4/4 COMPLETED ✅)
1. ✅ RiskMonitor.assess_risk() wrapper method - **COMPLETED**
2. ✅ DataProvider method alignment - **COMPLETED** 
3. ✅ ExposureMonitor call fix (pass timestamp and market_data) - **COMPLETED**
4. ✅ Fail-fast config access (remove .get() defaults) - **COMPLETED** (all .get() patterns removed from RiskMonitor)

### 🟡 **HIGH PRIORITY Features** (ALL COMPLETED ✅)
5. ✅ Error codes system (POS-001, EXP-001, etc.) - **COMPLETED**
6. ✅ Liquidation simulation (CEX + AAVE) - **COMPLETED**
7. ✅ KING token handling (unwrap/sell orchestration) - **COMPLETED**
8. ✅ Seasonal rewards (discrete event application) - **COMPLETED**
9. ✅ target_apy/max_drawdown integration - **COMPLETED**

---

## 🔄 **Component → Backend File Mapping**

| Component | Backend Location | Type | Spec |
|-----------|------------------|------|------|
| **Position Monitor** | `core/strategies/components/position_monitor.py` | ✅ EXISTS | [01](specs/01_POSITION_MONITOR.md) |
| **Exposure Monitor** | `core/strategies/components/exposure_monitor.py` | ✅ EXISTS | [02](specs/02_EXPOSURE_MONITOR.md) |
| **Risk Monitor** | `core/rebalancing/risk_monitor.py` | ✅ EXISTS | [03](specs/03_RISK_MONITOR.md) |
| **P&L Calculator** | `core/math/pnl_calculator.py` | ✅ EXISTS | [04](specs/04_PNL_CALCULATOR.md) |
| **Strategy Manager** | `core/strategies/components/strategy_manager.py` | ✅ EXISTS | [05](specs/05_STRATEGY_MANAGER.md) |
| **CEX Exec Manager** | `core/strategies/components/cex_execution_manager.py` | ✅ EXISTS | [06](specs/06_CEX_EXECUTION_MANAGER.md) |
| **OnChain Exec Manager** | `core/strategies/components/onchain_execution_manager.py` | ✅ EXISTS | [07](specs/07_ONCHAIN_EXECUTION_MANAGER.md) |
| **Event Logger** | `core/strategies/components/event_logger.py` | ✅ EXISTS | [08](specs/08_EVENT_LOGGER.md) |
| **Data Provider** | `infrastructure/data/historical_data_provider.py` | ✅ EXISTS | [09](specs/09_DATA_PROVIDER.md) |
| **Live Data Provider** | `infrastructure/data/live_data_provider.py` | ✅ EXISTS | [12](specs/12_LIVE_DATA_PROVIDER.md) |
| **Transfer Manager** | `core/rebalancing/transfer_manager.py` | ✅ EXISTS | [Transfer Manager](specs/03_RISK_MONITOR.md) |
| **Execution Interfaces** | `core/interfaces/` | ✅ EXISTS | [08](specs/08_EXECUTION_INTERFACES.md) |

---

## 📁 **Backend Repository Structure**

### **What EXISTS** ✅

```
backend/src/basis_strategy_v1/
├── api/                                    # ✅ API unchanged
│   ├── main.py
│   ├── dependencies.py
│   ├── middleware/
│   ├── models/ (requests, responses)
│   └── routes/ (backtest, results, health, etc.)
│
├── core/
│   ├── config/
│   │   ├── config_models.py              # ✅ REUSE (618 lines)
│   │   └── venue_constants.py            # ✅ REUSE (414 lines)
│   │
│   ├── strategies/
│   │   └── components/
│   │       ├── position_monitor.py       # ✅ EXISTS
│   │       ├── exposure_monitor.py       # ✅ EXISTS
│   │       ├── event_logger.py           # ✅ EXISTS
│   │       ├── strategy_manager.py       # ✅ EXISTS
│   │       ├── cex_execution_manager.py  # ✅ EXISTS
│   │       └── onchain_execution_manager.py # ✅ EXISTS
│   │
│   ├── interfaces/                        # ✅ NEW - Execution Interfaces
│   │   ├── base_execution_interface.py   # ✅ EXISTS
│   │   ├── cex_execution_interface.py    # ✅ EXISTS
│   │   ├── onchain_execution_interface.py # ✅ EXISTS
│   │   ├── transfer_execution_interface.py # ✅ EXISTS
│   │   └── execution_interface_factory.py # ✅ EXISTS
│   │
│   ├── math/
│   │   ├── pnl_calculator.py             # ✅ EXISTS
│   │   ├── aave_rate_calculator.py       # ✅ REUSE
│   │   ├── health_calculator.py          # ✅ REUSE
│   │   ├── ltv_calculator.py             # ✅ REUSE
│   │   ├── margin_calculator.py          # ✅ REUSE
│   │   ├── metrics_calculator.py         # ✅ REUSE
│   │   └── yield_calculator.py           # ✅ REUSE
│   │
│   ├── rebalancing/
│   │   ├── risk_monitor.py               # ✅ EXISTS
│   │   └── transfer_manager.py           # ✅ EXISTS
│   │
│   ├── services/
│   │   ├── backtest_service.py           # ✅ EXISTS
│   │   └── live_service.py               # ✅ EXISTS
│   │
│   └── event_engine/
│       └── event_driven_strategy_engine.py  # ✅ INTEGRATED
│
└── infrastructure/
    ├── config/
    │   ├── config_loader.py              # ✅ COMPLETE
    │   ├── config_validator.py           # ✅ COMPLETE
    │   ├── health_check.py               # ✅ COMPLETE
    │   ├── settings.py                   # ✅ COMPLETE
    │   └── strategy_discovery.py         # ✅ EXISTS
    │
    ├── data/
    │   ├── historical_data_provider.py   # ✅ EXISTS (mode-aware)
    │   └── live_data_provider.py         # ✅ EXISTS
    │
    ├── monitoring/
    │   ├── health.py                     # ✅ EXISTS
    │   ├── logging.py                    # ✅ EXISTS
    │   └── metrics.py                    # ✅ EXISTS
    │
    ├── cache/redis_client.py             # ✅ REUSE
    ├── persistence/result_store.py       # ✅ REUSE
    ├── storage/chart_storage.py          # ✅ REUSE
    └── visualization/chart_generator.py  # ✅ REUSE
```

---

## 🔧 **Critical Implementation Tasks**

### **IMPL-CRITICAL-01: RiskMonitor Method Alignment** ⭐⭐⭐
**Owner**: Agent A  
**Estimate**: 15 minutes

**Issue**: Missing `assess_risk()` wrapper method

**Tasks**:
- [ ] Add `assess_risk(exposure, market_data=None)` method
- [ ] Call `calculate_overall_risk()` internally
- [ ] Match EventDrivenStrategyEngine expectations

---

### **IMPL-CRITICAL-02: DataProvider Initialization** ⭐⭐⭐
**Owner**: Agent B  
**Estimate**: 20 minutes

**Issue**: Engine shouldn't call `load_mode_specific_data()` (loaded in `__init__`)

**Tasks**:
- [ ] Remove `load_mode_specific_data()` from public API
- [ ] Ensure `__init__` loads all data based on mode
- [ ] Update EventDrivenStrategyEngine integration

---

### **IMPL-CRITICAL-03: ExposureMonitor Parameters** ⭐⭐⭐
**Owner**: Agent A  
**Estimate**: 15 minutes

**Issue**: `calculate_exposure()` needs timestamp and market_data parameters

**Tasks**:
- [ ] Update `calculate_exposure(timestamp, position_snapshot=None, market_data=None)`
- [ ] Engine must pass timestamp and market_data
- [ ] Update all callers

---

### **IMPL-CRITICAL-04: Config Fail-Fast** ⭐⭐⭐
**Owner**: Agent A  
**Estimate**: 20 minutes

**Issue**: Remove `.get()` defaults, fail fast if config missing

**Tasks**:
- [ ] Replace all `.get()` with direct access in RiskMonitor
- [ ] Let KeyError raise if config missing
- [ ] Add clear error messages

---

## 🟡 **High Priority Features**

### **IMPL-HIGH-01: Error Code System** ⭐⭐
**Owner**: Both agents  
**Estimate**: 1 day

**Tasks**:
- [ ] Implement error codes: POS-001, EXP-001, RISK-001, PNL-001, STRAT-001, CEX-001, CHAIN-001, DATA-001, EVENT-001
- [ ] Add structured error logging
- [ ] Update error messages with codes
- [ ] Document all error codes

**Spec**: [specs/11_ERROR_LOGGING_STANDARD.md](specs/11_ERROR_LOGGING_STANDARD.md)

---

### **IMPL-HIGH-02: Liquidation Simulation** ⭐⭐
**Owner**: Agent B  
**Estimate**: 4 hours

**Tasks**:
- [ ] Implement `simulate_liquidation()` for AAVE
  - HF < 1 triggers liquidation
  - 50% debt repaid by liquidator
  - Liquidation bonus (1% for E-mode) seized
- [ ] Implement `simulate_cex_liquidation()` for CEX
  - Margin ratio < 10% triggers liquidation
  - ALL margin lost (catastrophic)
- [ ] Add tests for liquidation scenarios

**Spec**: [specs/03_RISK_MONITOR.md](specs/03_RISK_MONITOR.md) (lines 405-527)

---

### **IMPL-HIGH-03: KING Token Handling** ⭐⭐
**Owner**: Agent B  
**Estimate**: 5 hours

**Tasks**:
- [ ] Auto unwrap KING → EIGEN + ETHFI in StrategyManager
- [ ] Auto sell EIGEN/ETHFI to USDT
- [ ] Event logging for unwrap/sell operations
- [ ] Integration with OnChainExecutionManager

**Spec**: [KING_TOKEN_HANDLING_GUIDE.md](KING_TOKEN_HANDLING_GUIDE.md)

---

### **IMPL-HIGH-04: Seasonal Rewards** ⭐⭐
**Owner**: Agent A  
**Estimate**: 2 hours

**Tasks**:
- [ ] Apply seasonal rewards as discrete events (not continuous)
- [ ] Use exact timestamps from data files
- [ ] Log with balance snapshots
- [ ] Track cumulative rewards

**Spec**: [specs/08_EVENT_LOGGER.md](specs/08_EVENT_LOGGER.md)

---

### **IMPL-HIGH-05: target_apy/max_drawdown Integration** ⭐
**Owner**: Both agents  
**Estimate**: 2 hours

**Tasks**:
- [ ] Use `target_apy` for frontend guidance
- [ ] Use `max_drawdown` for risk warnings
- [ ] Validate in config system
- [ ] Display in frontend wizard

---

## 🎨 **Frontend Implementation**

### **Current Structure**
```
frontend/src/
├── App.tsx
├── main.tsx
└── index.css
```

### **Needed Components**
```
frontend/src/
├── components/
│   ├── wizard/
│   │   ├── WizardContainer.tsx
│   │   ├── ShareClassStep.tsx
│   │   ├── ModeSelectionStep.tsx
│   │   ├── BasicConfigStep.tsx
│   │   ├── StrategyConfigStep.tsx
│   │   └── ReviewStep.tsx
│   ├── forms/
│   │   ├── USDTMarketNeutralForm.tsx
│   │   ├── PureLendingForm.tsx
│   │   ├── BTCBasisForm.tsx
│   │   └── ETHLeveragedForm.tsx
│   └── results/
│       ├── MetricCard.tsx
│       ├── PlotlyChart.tsx
│       ├── EventLogViewer.tsx
│       └── ResultsPage.tsx
```

**Tasks**:
- [ ] Install dependencies (shadcn/ui, Tailwind CSS)
- [ ] Create wizard container with stepper logic
- [ ] Implement all 5 wizard steps
- [ ] Create mode-specific form components
- [ ] Add real-time validation
- [ ] Implement results display
- [ ] Connect to backend API

**Spec**: [specs/12_FRONTEND_SPEC.md](specs/12_FRONTEND_SPEC.md)

---

## 💻 **EventDrivenStrategyEngine Integration**

### **Current State** (needs component integration)
```python
class EventDrivenStrategyEngine:
    def __init__(self, config, data_provider, execution_engine):
        # Currently has inline logic for everything
        pass
    
    async def run_backtest(self, start, end):
        # ~2,000 lines of inline logic
        pass
```

### **Target State** (component-based)
```python
class EventDrivenStrategyEngine:
    def __init__(self, config, data_provider, execution_engine):
        # Detect mode
        self.mode = self._detect_mode(config)
        
        # Initialize all 9 components
        self.position_monitor = PositionMonitor(execution_mode='backtest')
        self.exposure_monitor = ExposureMonitor(config['share_class'], 
                                                 self.position_monitor, 
                                                 data_provider)
        self.risk_monitor = RiskMonitor(config, self.exposure_monitor)
        self.pnl_calculator = PnLCalculator(config['share_class'], 
                                            config['initial_capital'])
        self.strategy_manager = StrategyManager(self.mode, config, 
                                                self.exposure_monitor, 
                                                self.risk_monitor)
        self.event_logger = EventLogger(execution_mode='backtest')
        self.cex_exec = CEXExecutionManager('backtest', 
                                            self.position_monitor, 
                                            self.event_logger, 
                                            data_provider)
        self.onchain_exec = OnChainExecutionManager('backtest', 
                                                     self.position_monitor, 
                                                     self.event_logger, 
                                                     data_provider)
    
    async def run_backtest(self, start, end):
        # Synchronous component chain (300 lines, not 2,000)
        for timestamp in timestamps:
            position = self.position_monitor.get_snapshot()
            exposure = self.exposure_monitor.calculate_exposure(timestamp, 
                                                                position, 
                                                                market_data)
            risks = self.risk_monitor.assess_risk(exposure, market_data)
            pnl = self.pnl_calculator.calculate_pnl(exposure, timestamp)
            
            if risks['any_critical']:
                instructions = self.strategy_manager.generate_instructions(
                    exposure, risks)
                for instruction in instructions:
                    await self._execute_instruction(instruction, timestamp)
        
        return self.pnl_calculator.get_summary()
```

---

## 📊 **Component Integration Patterns**

### **Pattern 1: Synchronous Update Chain**
```python
# When balance changes (synchronous for backtest):
position = self.position_monitor.update(changes, timestamp)
    ↓
exposure = self.exposure_monitor.calculate_exposure(timestamp, position, market_data)
    ↓
risks = self.risk_monitor.assess_risk(exposure, market_data)
    ↓
pnl = self.pnl_calculator.calculate_pnl(exposure, timestamp)
    ↓
if risks['needs_rebalancing']:
    instructions = self.strategy_manager.generate_instructions(exposure, risks)
```

### **Pattern 2: Execution Manager Usage**
```python
# Component issues instruction
instruction = {
    'type': 'ATOMIC_LEVERAGE_ENTRY',
    'params': {'equity': 50000, 'target_ltv': 0.91}
}

# Engine routes to appropriate manager
if instruction['type'] in ['ATOMIC_LEVERAGE_ENTRY', 'AAVE_SUPPLY', 'STAKE']:
    result = await self.onchain_exec.execute(instruction)
elif instruction['type'] in ['TRADE_SPOT', 'TRADE_PERP']:
    result = await self.cex_exec.execute(instruction)

# Manager automatically:
# - Executes operation
# - Updates Position Monitor
# - Logs events
# - Returns result
```

---

## 🧹 **Backend Cleanup Tasks**

### **Files to Archive** (After validation)
```
backend/src/basis_strategy_v1/
├── core/services/
│   ├── backtest_service.py          # Replaced by new components
│   └── strategy_service.py          # Replaced by Strategy Manager
│
└── infrastructure/execution/
    ├── backtest_execution_engine.py # Replaced by new execution managers
    └── simulated_engine.py          # Replaced by new execution managers
```

**Tasks**:
- [ ] Archive obsolete files to `archive/backend_obsolete/`
- [ ] Update imports in remaining files
- [ ] Remove references from `__init__.py` files
- [ ] Update API routes to use new components
- [ ] Run full test suite

**Note**: Don't delete until after validation

---

## ✅ **Testing Requirements**

### **Unit Tests** (80% minimum coverage per component)
- [ ] Position Monitor - 80%+
- [ ] Exposure Monitor - 80%+
- [ ] Risk Monitor - 80%+
- [ ] P&L Calculator - 80%+
- [ ] Strategy Manager - 80%+
- [ ] CEX Execution Manager - 80%+
- [ ] OnChain Execution Manager - 80%+
- [ ] Event Logger - 80%+
- [ ] Data Provider - 80%+

### **Integration Tests**
- [ ] Position → Exposure → Risk → P&L chain
- [ ] Redis pub/sub integration
- [ ] Config loading integration
- [ ] Data provider integration

### **E2E Tests**
- [ ] Pure USDT Lending - Full backtest
- [ ] BTC Basis - Full backtest
- [ ] ETH Leveraged - Full backtest
- [ ] USDT Market-Neutral - Full backtest

**Location**: `tests/`  
**Guide**: [tests/README.md](../tests/README.md)

---

## 👥 **Task Ownership**

### **Agent A** (Monitoring & Frontend):
- IMPL-CRITICAL-01: RiskMonitor method
- IMPL-CRITICAL-03: ExposureMonitor parameters
- IMPL-CRITICAL-04: Config fail-fast
- IMPL-HIGH-01: Error codes (monitoring components)
- IMPL-HIGH-02: Liquidation simulation
- IMPL-HIGH-04: Seasonal rewards
- IMPL-HIGH-05: target_apy/max_drawdown (RiskMonitor part)
- Frontend implementation

### **Agent B** (Infrastructure & Execution):
- IMPL-CRITICAL-02: DataProvider initialization
- IMPL-HIGH-01: Error codes (execution components)
- IMPL-HIGH-03: KING token handling
- IMPL-HIGH-05: target_apy/max_drawdown (config part)
- Backend cleanup
- Deployment updates

---

## 📋 **Timeline Summary**

### **Phase 1: Critical Fixes** (1-2 hours)
- All 4 critical method fixes

### **Phase 2: High Priority Features** (2-3 days)
- Error codes system
- Liquidation simulation
- KING token handling
- Seasonal rewards
- target_apy/max_drawdown

### **Phase 3: Frontend & Testing** (1-2 days)
- Frontend wizard implementation
- Result visualization
- Unit tests to 80%+
- Integration tests
- E2E tests

### **Phase 4: Cleanup & Deploy** (1 day)
- Backend cleanup
- Production deployment
- Health checks

**Total**: 3-5 days to production-ready

---

## ✅ **Success Criteria**

**Critical Fixes**:
- [ ] All 4 method fixes complete
- [ ] EventDrivenStrategyEngine integration working

**High Priority Features**:
- [ ] Error code system implemented
- [ ] Liquidation simulation working
- [ ] KING token handling complete
- [ ] Seasonal rewards applied correctly
- [ ] target_apy/max_drawdown integrated

**Testing**:
- [ ] 80%+ unit test coverage per component
- [ ] All integration tests passing
- [ ] E2E tests for all 4 modes passing

**Frontend**:
- [ ] Mode wizard polished
- [ ] Result visualization complete

**Production Ready**:
- [ ] All tests passing
- [ ] All error codes in place
- [ ] Logs are audit-grade
- [ ] Configuration validated
- [ ] Documentation updated
- [ ] Ready for staging deployment

---

**Ready to implement!** 🚀 Start with critical fixes, then features, then polish.

**For detailed tasks**: See [REQUIREMENTS.md](REQUIREMENTS.md)  
**For timeline**: See [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)

*Last Updated: October 3, 2025*
