# Agent A - Frontend Specialist Instructions 🎨

## 🚀 **CRITICAL: Frontend-Only Implementation Guide**

**Agent Role**: Frontend Development Specialist (100% Frontend Focus)  
**Environment**: Cursor Web Browser  
**Branch**: `agent-implementation`  
**Total Remaining Work**: 4-5 days  
**Status**: Backend 99.5% complete, focus on frontend implementation

---

 ## 📋 **PHASE 1: Frontend Implementation (4-5 days)**

### **🎯 CURRENT CONTEXT: Backend is 99.5% Complete!**
**BTC Basis Strategy**: Perfect trade execution, delta neutrality achieved, new architecture working  
**Pure Lending Strategy**: Ready for implementation  
**Your Focus**: Build excellent frontend to visualize and interact with this working backend

### **Step 1.1: Enhance Frontend Wizard Forms**
**Priority**: 🔴 **CRITICAL** - Current forms are basic text, need visual appeal

**Files**: `frontend/src/components/wizard/*`
**Goal**: Transform basic forms into beautiful, interactive wizard

**Current Issues**:
- Forms are mostly text rather than visually appealing
- Strategy mode loading doesn't work properly
- No real-time validation
- No estimated APY display
- Basic styling, not professional

**Implementation Approach**: Use Beautiful Soup or Selenium to update forms programmatically

**Enhanced Wizard Requirements**:
1. **Visual Mode Cards**: Strategy modes with icons, APY ranges, risk indicators
2. **Interactive Forms**: Sliders, dropdowns, checkboxes with proper styling
3. **Real-time Validation**: Backend API integration for parameter validation
4. **Estimated APY Display**: Show expected returns based on configuration
5. **Progress Indicator**: Clear step progression with validation status

### **Step 1.2: Implement Results Visualization**
**Priority**: 🔴 **CRITICAL** - Need to query backtest results and display charts

**Files**: `frontend/src/components/results/*`
**Goal**: Complete results dashboard with embedded Plotly charts

**Current Issues**:
- Cannot query backtest results by ID
- No embedded Plotly chart display
- No event log viewer for backtests
- No performance metrics display

**Implementation Requirements**:
1. **Results API Integration**: Query backtest results by ID from backend
2. **Embedded Plotly Charts**: Display interactive charts from backend HTML
3. **Event Log Viewer**: Virtualized table for 70k+ events with filtering
4. **Performance Metrics**: APY, drawdown, P&L attribution, delta neutrality
5. **Export Functionality**: Download results, charts, and event logs

### **Step 1.3: Run Quality Gates Validation**
**Priority**: 🔴 **CRITICAL** - Validate current system status

**Commands to run**:
```bash
# Run test coverage analysis
python scripts/analyze_test_coverage.py

# Run quality gates validation
python scripts/run_quality_gates.py

# Run performance quality gates
python scripts/performance_quality_gates.py
```

**Expected Output**: Document current test coverage, identify gaps, and validate system health

### **Step 1.4: Fix EventDrivenStrategyEngine Method Calls**
**Priority**: 🟡 **HIGH** - Method signature mismatches

**File**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py`

**Changes Required**:
- Line 129: Fix `load_mode_specific_data()` → `_load_data_for_mode()`
- Line 176: Fix `calculate_exposure()` method signature
- Line 179: Fix `assess_risk()` method signature  
- Line 188: Fix `make_strategy_decision()` method signature
- Line 94: Fix `StrategyManager` initialization

**Expected Result**: EventDrivenStrategyEngine runs without method signature errors.

### **Step 1.2: Add Error Codes to Owned Components**
```bash
# Add error codes to these 4 files (risk_monitor.py moved to Agent B)
```

**Files to Update**:
1. `backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py`
2. `backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py`
3. `backend/src/basis_strategy_v1/core/math/pnl_calculator.py`
4. `backend/src/basis_strategy_v1/core/strategies/components/event_logger.py`

**Error Codes to Add**:
- POS-001 to POS-005 for Position Monitor
- EXP-001 to EXP-005 for Exposure Monitor
- PNL-001 to PNL-004 for P&L Calculator
- EVENT-001 to EVENT-005 for Event Logger

**Expected Result**: All components log errors with standardized codes.

---

## 📋 **PHASE 2: Test Coverage Improvement (Week 2)**

### **Step 2.1: API Routes Coverage**
**Priority**: 🟡 **HIGH** - Current coverage: 0%  
**Target**: 80% coverage

**Files to Cover**:
- `backend/src/basis_strategy_v1/api/routes/backtest.py` (107 statements)
- `backend/src/basis_strategy_v1/api/routes/charts.py` (146 statements)
- `backend/src/basis_strategy_v1/api/routes/component_health.py` (72 statements)
- `backend/src/basis_strategy_v1/api/routes/health.py` (43 statements)
- `backend/src/basis_strategy_v1/api/routes/live_trading.py` (112 statements)
- `backend/src/basis_strategy_v1/api/routes/results.py` (275 statements)
- `backend/src/basis_strategy_v1/api/routes/strategies.py` (159 statements)

**Implementation**:
```bash
# Create comprehensive API tests
mkdir -p tests/integration/api/
touch tests/integration/api/test_backtest_routes.py
touch tests/integration/api/test_charts_routes.py
touch tests/integration/api/test_health_routes.py
touch tests/integration/api/test_live_trading_routes.py
touch tests/integration/api/test_results_routes.py
touch tests/integration/api/test_strategies_routes.py
```

### **Step 2.2: Frontend Implementation**
**Priority**: 🟡 **MEDIUM** - Complete frontend wizard UI

**Files to Complete**:
- `frontend/src/components/wizard/StrategyWizard.tsx`
- `frontend/src/components/wizard/ShareClassSelector.tsx`
- `frontend/src/components/wizard/ParameterInputs.tsx`
- `frontend/src/components/wizard/ValidationDisplay.tsx`

**Features to Implement**:
- Target APY display and validation
- Real-time parameter validation
- API integration with backend
- Form state management

**Expected Result**: Complete wizard form with validation and API calls.

### **Step 2.2: Complete Frontend Results Display**
```bash
# Continue in frontend directory
# Create results components
```

**Files to Create/Complete**:
- `frontend/src/components/results/MetricCard.tsx`
- `frontend/src/components/results/PlotlyChart.tsx`
- `frontend/src/components/results/EventLogViewer.tsx`
- `frontend/src/components/results/ResultsDashboard.tsx`

**Features to Implement**:
- Performance metrics display
- Interactive charts with Plotly
- Event log viewer with filtering
- Target vs actual comparison

**Expected Result**: Complete results dashboard with interactive visualizations.

---

## 📋 **PHASE 3: Component Health System (Week 3)**

### **Step 3.1: Implement Health Check Endpoints**
**Priority**: 🟡 **HIGH** - Health monitoring system

**Endpoints to Implement**:
- `GET /health/components` - All component health
- `GET /health/readiness` - System readiness
- `GET /health/errors` - Error summary
- `GET /health/components/{component}` - Specific component health

**Files to Create**:
- `backend/src/basis_strategy_v1/api/routes/component_health.py` (enhance existing)
- `tests/integration/api/test_health_routes.py`

### **Step 3.2: Component Registration**
**Priority**: 🟡 **HIGH** - Register all components with health system

**Components to Register**:
- Position Monitor
- Exposure Monitor
- Risk Monitor
- P&L Calculator
- Strategy Manager
- Data Provider
- Event Logger
- Execution Interfaces
- Event Engine

### **Step 3.3: Integration Testing**
**Priority**: 🟡 **MEDIUM** - Test complete user journey

**Test Coverage**:
- EventDrivenStrategyEngine method fixes
- Frontend wizard to results flow
- API integration
- Error code logging
- Health check endpoints

**Expected Result**: All integration tests pass.

---

## 🎯 **Success Criteria**

### **Phase 1 Complete When** (Critical Fixes):
- [ ] Configuration system works for tests (90%+ test pass rate)
- [ ] Data dependencies resolved (AAVE risk params, LST prices)
- [ ] Method signatures aligned across components
- [ ] EventDrivenStrategyEngine runs without crashes
- [ ] Error codes appear in all Agent A component logs

### **Phase 2 Complete When** (Test Coverage):
- [ ] API routes: 80% test coverage achieved
- [ ] Frontend wizard form is fully functional
- [ ] Results dashboard displays data correctly
- [ ] API integration works end-to-end
- [ ] Overall test coverage: 60%+

### **Phase 3 Complete When** (Health System):
- [ ] All components registered with health system
- [ ] Health check endpoints functional
- [ ] Component health reporting working
- [ ] System readiness checks pass
- [ ] All integration tests pass

### **Quality Gates Achieved When**:
- [ ] Test coverage: 80% overall
- [ ] Component health: 100% healthy
- [ ] Event chain: 100% functional
- [ ] Performance: Meets all benchmarks
- [ ] API integration: 100% functional

---

## 🚨 **Critical Notes**

1. **NO RISK MONITOR TASKS**: All risk monitor tasks moved to Agent B for orthogonality
2. **Focus on EventDrivenStrategyEngine**: This is the critical path for system functionality
3. **Error Codes Required**: All components must log errors with standardized codes
4. **Frontend Priority**: Complete the user interface for the backtesting system
5. **Test Everything**: Each phase must pass tests before moving to the next

---

## 📞 **Coordination with Agent B**

- **Agent B handles**: All risk monitor tasks, infrastructure, execution, liquidation simulation
- **Agent A handles**: EventDrivenStrategyEngine fixes, frontend, error codes for owned components
- **No shared files**: Complete orthogonality achieved
- **No coordination needed**: Both agents can work in parallel

---

**Total Estimated Time**: 3 days  
**Critical Path**: EventDrivenStrategyEngine fixes → Frontend implementation → Integration testing