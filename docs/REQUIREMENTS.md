# Production Requirements: Component-Based Architecture 📋

**Project**: Component-based service architecture implementation  
**Status**: ✅ Core components implemented - Critical issues remain  
**Timeline**: 🔄 1-2 WEEKS TO PRODUCTION READY - Critical fixes needed  
**Updated**: October 6, 2025 - Updated to reflect actual implementation status

---

## 🎯 **Project Goals**

### **Primary Goals** ✅ MOSTLY ACHIEVED
1. ✅ All 9 components implemented and working
2. ✅ Support 4 strategy modes
3. ✅ Audit-grade event logging
4. ✅ Backtest-to-live ready
5. ✅ Method alignment fixes completed
6. ✅ Error code system implemented

### **Success Criteria** 🔄 PARTIALLY ACHIEVED
- [x] All critical method fixes complete
- [x] Error code system implemented (POS-001, EXP-001, etc.)
- [x] Liquidation simulation working
- [x] KING token handling implemented
- [x] Seasonal rewards applied correctly
- [x] 43% unit test coverage achieved (133/133 component tests passing)
- [x] All integration tests passing
- [x] Backend deployment validated
- [x] P&L reconciliation working
- [ ] **Pure lending yield calculation** (1166% APY issue)
- [ ] **Quality gates** (5/14 scripts passing)
- [ ] **RiskMonitor compatibility** (API endpoint fails)

---

## 📚 **Component Specifications**

**For complete implementation details**: See [specs/](specs/) directory (12 detailed specs, ~6,000 lines)

**Component List**:
1. [Position Monitor](specs/01_POSITION_MONITOR.md) - Balance tracking
2. [Exposure Monitor](specs/02_EXPOSURE_MONITOR.md) - AAVE conversion & net delta
3. [Risk Monitor](specs/03_RISK_MONITOR.md) - LTV, margin, liquidation
4. [P&L Calculator](specs/04_PNL_CALCULATOR.md) - Balance & attribution P&L
5. [Strategy Manager](specs/05_STRATEGY_MANAGER.md) - Mode orchestration
6. [CEX Execution Manager](specs/06_CEX_EXECUTION_MANAGER.md) - CEX trading
7. [OnChain Execution Manager](specs/07_ONCHAIN_EXECUTION_MANAGER.md) - Blockchain ops
8. [Event Logger](specs/08_EVENT_LOGGER.md) - Audit logging
9. [Data Provider](specs/09_DATA_PROVIDER.md) - Market data

**Standards**:
10. [Redis Messaging](specs/10_REDIS_MESSAGING_STANDARD.md) - Inter-component communication
11. [Error Logging](specs/11_ERROR_LOGGING_STANDARD.md) - Structured logging

**Frontend**:
12. [Frontend Spec](specs/12_FRONTEND_SPEC.md) - UI wizard

---

## 🔴 **CRITICAL FIXES** (Priority 1, ~1-2 hours)

### **IMPL-CRITICAL-01: RiskMonitor Method Alignment**
**File**: `backend/src/basis_strategy_v1/core/rebalancing/risk_monitor.py`  
**Issue**: Missing `assess_risk()` wrapper method  
**Owner**: Agent A

**Tasks**:
- [ ] Add `assess_risk(exposure, market_data=None)` method
- [ ] Call `calculate_overall_risk()` internally
- [ ] Match EventDrivenStrategyEngine expectations

**Acceptance Criteria**:
- [ ] Engine can call `risk_monitor.assess_risk(exposure)`
- [ ] Method returns complete risk assessment
- [ ] Tests pass

**Estimate**: 15 minutes

---

### **IMPL-CRITICAL-02: DataProvider Initialization**
**File**: `backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py`  
**Issue**: Engine shouldn't call `load_mode_specific_data()` (data loaded in `__init__`)  
**Owner**: Agent B

**Tasks**:
- [ ] Remove `load_mode_specific_data()` from public API
- [ ] Ensure `__init__` loads all data based on mode
- [ ] Update EventDrivenStrategyEngine integration

**Acceptance Criteria**:
- [ ] Data loaded once at initialization
- [ ] Engine doesn't call load methods
- [ ] Tests pass

**Estimate**: 20 minutes

---

### **IMPL-CRITICAL-03: ExposureMonitor Parameters**
**File**: `backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py`  
**Issue**: `calculate_exposure()` needs timestamp and market_data parameters  
**Owner**: Agent A

**Tasks**:
- [ ] Update `calculate_exposure(timestamp, position_snapshot=None, market_data=None)`
- [ ] Engine must pass timestamp and market_data
- [ ] Update all callers

**Acceptance Criteria**:
- [ ] Method signature matches spec
- [ ] Engine passes all required parameters
- [ ] Tests pass

**Estimate**: 15 minutes

---

### **IMPL-CRITICAL-04: Config Fail-Fast**
**File**: `backend/src/basis_strategy_v1/core/rebalancing/risk_monitor.py`  
**Issue**: Remove `.get()` defaults, fail fast if config missing  
**Owner**: Agent A

**Tasks**:
- [ ] Replace all `.get()` with direct access
- [ ] Let KeyError raise if config missing
- [ ] Add clear error messages

**Acceptance Criteria**:
- [ ] Config errors fail fast at startup
- [ ] Clear error messages
- [ ] Tests pass

**Estimate**: 20 minutes

---

## 🟡 **HIGH PRIORITY FEATURES** (Priority 2, ~2-3 days)

### **IMPL-HIGH-01: Error Code System**
**Files**: All 9 components  
**Spec**: [specs/11_ERROR_LOGGING_STANDARD.md](specs/11_ERROR_LOGGING_STANDARD.md)  
**Owner**: Both agents (divide by component)

**Tasks**:
- [ ] Implement error codes: POS-001, EXP-001, RISK-001, PNL-001, STRAT-001, CEX-001, CHAIN-001, DATA-001, EVENT-001
- [ ] Add structured error logging
- [ ] Update error messages with codes
- [ ] Document all error codes

**Acceptance Criteria**:
- [ ] All errors have error codes
- [ ] Structured logging in place
- [ ] Error code documentation complete
- [ ] Tests include error code validation

**Estimate**: 1 day

---

### **IMPL-HIGH-02: Liquidation Simulation**
**Files**: `backend/src/basis_strategy_v1/core/rebalancing/risk_monitor.py`  
**Spec**: [specs/03_RISK_MONITOR.md](specs/03_RISK_MONITOR.md) (lines 405-527)  
**Owner**: Agent A

**Tasks**:
- [ ] Implement `simulate_liquidation()` for AAVE
  - HF < 1 triggers liquidation
  - 50% debt repaid by liquidator
  - Liquidation bonus (1% for E-mode) seized
- [ ] Implement `simulate_cex_liquidation()` for CEX
  - Margin ratio < 10% triggers liquidation
  - ALL margin lost (catastrophic)
- [ ] Add tests for liquidation scenarios

**Acceptance Criteria**:
- [ ] AAVE liquidation simulates correctly (HF, bonus, remaining)
- [ ] CEX liquidation simulates margin loss
- [ ] Tests cover edge cases
- [ ] Results match manual calculations

**Estimate**: 4 hours

---

### **IMPL-HIGH-03: KING Token Handling**
**Files**: 
- `backend/src/basis_strategy_v1/core/strategies/strategy_manager.py`
- `backend/src/basis_strategy_v1/infrastructure/execution/onchain_execution_manager.py`  
**Spec**: [docs/KING_TOKEN_HANDLING_GUIDE.md](KING_TOKEN_HANDLING_GUIDE.md)  
**Owner**: Agent B

**Tasks**:
- [ ] Auto unwrap KING → EIGEN + ETHFI in StrategyManager
- [ ] Auto sell EIGEN/ETHFI to USDT
- [ ] Event logging for unwrap/sell operations
- [ ] Integration with OnChainExecutionManager

**Acceptance Criteria**:
- [ ] KING auto unwraps when detected
- [ ] EIGEN/ETHFI auto sells to USDT
- [ ] Events logged with balance snapshots
- [ ] Tests pass

**Estimate**: 4 hours

---

### **IMPL-HIGH-04: Seasonal Rewards**
**Files**: `backend/src/basis_strategy_v1/core/strategies/components/event_logger.py`  
**Spec**: [specs/08_EVENT_LOGGER.md](specs/08_EVENT_LOGGER.md)  
**Owner**: Agent A

**Tasks**:
- [ ] Apply seasonal rewards as discrete events (not continuous)
- [ ] Use exact timestamps from data files
- [ ] Log with balance snapshots
- [ ] Track cumulative rewards

**Acceptance Criteria**:
- [ ] Rewards applied at exact timestamps
- [ ] Not smoothed/interpolated
- [ ] Event log shows discrete events
- [ ] Tests pass

**Estimate**: 2 hours

---

### **IMPL-HIGH-05: target_apy/max_drawdown Integration**
**Files**: 
- `backend/src/basis_strategy_v1/core/rebalancing/risk_monitor.py`
- `frontend/src/` (wizard components)  
**Spec**: Mode configs in `configs/modes/*.yaml`  
**Owner**: Both agents

**Tasks**:
- [ ] Use `target_apy` for frontend guidance
- [ ] Use `max_drawdown` for risk warnings
- [ ] Validate in config system
- [ ] Display in frontend wizard

**Acceptance Criteria**:
- [ ] Config validates target_apy/max_drawdown
- [ ] RiskMonitor uses for warnings
- [ ] Frontend displays values
- [ ] Tests pass

**Estimate**: 2 hours

---

## ✅ **TESTING REQUIREMENTS** (Priority 3, ongoing)

### **Unit Tests**
**Requirement**: **80% minimum coverage per component** (mandatory)

**Per Component**:
- [ ] Position Monitor - 80%+
- [ ] Exposure Monitor - 80%+
- [ ] Risk Monitor - 80%+
- [ ] P&L Calculator - 80%+
- [ ] Strategy Manager - 80%+
- [ ] CEX Execution Manager - 80%+
- [ ] OnChain Execution Manager - 80%+
- [ ] Event Logger - 80%+
- [ ] Data Provider - 80%+

**Location**: `tests/unit/`  
**Run**: `pytest tests/unit/ --cov=backend/src/basis_strategy_v1 --cov-report=term-missing`

---

### **Integration Tests**
**Requirement**: Sync chain works end-to-end

**Tests**:
- [ ] Position → Exposure → Risk → P&L chain
- [ ] Redis pub/sub integration
- [ ] Config loading integration
- [ ] Data provider integration

**Location**: `tests/integration/`  
**Run**: `pytest tests/integration/`

---

### **E2E Tests**
**Requirement**: All 4 modes work via API

**Tests**:
- [ ] Pure USDT Lending - Full backtest
- [ ] BTC Basis - Full backtest
- [ ] ETH Leveraged - Full backtest
- [ ] USDT Market-Neutral - Full backtest

**Location**: `tests/e2e/`  
**Run**: `pytest tests/e2e/`

---

## 🎨 **FRONTEND REQUIREMENTS** (Priority 4, ~1-2 days)

### **IMPL-FRONTEND-01: Mode Selection Wizard Polish**
**Files**: `frontend/src/components/`  
**Spec**: [specs/12_FRONTEND_SPEC.md](specs/12_FRONTEND_SPEC.md)  
**Owner**: Agent A

**Tasks**:
- [ ] Mode selection step polish
- [ ] Parameter validation with helpful errors
- [ ] Display target_apy/max_drawdown
- [ ] Submit with config validation

**Acceptance Criteria**:
- [ ] All 4 modes selectable
- [ ] Validation works
- [ ] Error messages clear
- [ ] UI responsive

**Estimate**: 4 hours

---

### **IMPL-FRONTEND-02: Result Visualization**
**Files**: `frontend/src/components/`  
**Spec**: [specs/12_FRONTEND_SPEC.md](specs/12_FRONTEND_SPEC.md)  
**Owner**: Agent A

**Tasks**:
- [ ] Plotly charts for P&L, delta, margin
- [ ] Event log viewer with filtering
- [ ] Balance sheet display
- [ ] Risk metrics dashboard

**Acceptance Criteria**:
- [ ] Interactive charts work
- [ ] Event log filterable
- [ ] All metrics displayed
- [ ] UI responsive

**Estimate**: 6 hours

---

## 📋 **Task Ownership**

### **Agent A** (Monitoring & Frontend):
- IMPL-CRITICAL-01: RiskMonitor method
- IMPL-CRITICAL-03: ExposureMonitor parameters
- IMPL-CRITICAL-04: Config fail-fast
- IMPL-HIGH-01: Error codes (monitoring components)
- IMPL-HIGH-02: Liquidation simulation
- IMPL-HIGH-04: Seasonal rewards
- IMPL-HIGH-05: target_apy/max_drawdown (RiskMonitor part)
- IMPL-FRONTEND-01: Wizard polish
- IMPL-FRONTEND-02: Result visualization

### **Agent B** (Infrastructure & Execution):
- IMPL-CRITICAL-02: DataProvider initialization
- IMPL-HIGH-01: Error codes (execution components)
- IMPL-HIGH-03: KING token handling
- IMPL-HIGH-05: target_apy/max_drawdown (config/frontend part)

---

## 📚 **Reference Documentation**

**For Implementation**:
- Component specs → [specs/](specs/)
- Architecture → [ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md)
- Roadmap → [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)

**For Configuration**:
- Config workflow → [CONFIG_WORKFLOW.md](CONFIG_WORKFLOW.md)
- Environment vars → [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md)

**For Testing**:
- Test guidelines → [tests/README.md](../tests/README.md)

---

## ✅ **Completion Checklist**

**Critical Fixes** (1-2 hours):
- [ ] All 4 critical method fixes complete
- [ ] All components have correct method signatures
- [ ] EventDrivenStrategyEngine integration working

**High Priority Features** (2-3 days):
- [ ] Error code system implemented
- [ ] Liquidation simulation working
- [ ] KING token handling complete
- [ ] Seasonal rewards applied correctly
- [ ] target_apy/max_drawdown integrated

**Testing** (ongoing):
- [ ] 80%+ unit test coverage per component
- [ ] All integration tests passing
- [ ] E2E tests for all 4 modes passing

**Frontend** (1-2 days):
- [ ] Mode wizard polished
- [ ] Result visualization complete
- [ ] All features working in browser

**Production Ready**:
- [ ] All tests passing
- [ ] All error codes in place
- [ ] Logs are audit-grade
- [ ] Configuration validated
- [ ] Documentation updated
- [ ] Ready for staging deployment

---

**Start with critical fixes, then features, then polish!** 🚀

*Last Updated: October 3, 2025*
