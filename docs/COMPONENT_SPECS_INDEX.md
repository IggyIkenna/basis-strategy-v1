# Component Specifications - Index 📚

**Purpose**: Central index to all component specifications  
**Status**: ✅ Core components implemented | 🔄 Critical issues remain | ❌ Not production ready  
**Updated**: October 10, 2025 - Core components working, critical issues remain  
**Last Reviewed**: October 10, 2025  
**Status**: ✅ Aligned with canonical architectural principles  
**Standard Format**: All 20 component specs follow 18-section standard format

---

## 📚 **Canonical Sources**

**This index aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Design Decisions**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Core design decisions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

---

## ✅ **Current Implementation Status**

**All 9 Core Components**: ✅ **CORE COMPONENTS IMPLEMENTED** | 🔄 **CRITICAL ISSUES REMAIN** | ❌ **NOT PRODUCTION READY**
- Backend deployment functional with critical issues
- All API endpoints working
- Backtest system executing end-to-end with yield calculation issues
- Test coverage working towards 80% target

## ⚠️ **Known Issues**

**CRITICAL**: This system is **NOT production ready**. Core components are implemented but critical issues remain:

- **Pure Lending**: Yield calculation shows 1166% APY (should be 3-8%)
- **Quality Gates**: Only 5/14 scripts passing (target: 70%+)
- **BTC Basis**: 8/10 quality gates passing (80%)
- **Overall Status**: In development - not ready for production use

**See**: [docs/QUALITY_GATES.md](QUALITY_GATES.md) for complete issue list and resolution status.

## 📋 **18-Section Standard Format**

All component specifications follow a standardized 18-section format:

1. **Purpose** - What the component does
2. **Responsibilities** - Specific duties  
3. **State** - Internal state variables
4. **Component References (Set at Init)** - What's passed during initialization
5. **Environment Variables** ⭐ - Which env vars are read
6. **Config Fields Used** ⭐ - Which config fields from strategy mode slice
7. **Data Provider Queries** ⭐ - Which data queries (or "N/A")
8. **Core Methods** - Main API surface
9. **Data Access Pattern** - How it queries data with shared clock
10. **Mode-Aware Behavior** - Backtest vs Live differences
11. **Event Logging Requirements** ⭐ - Separate log files + EventLogger integration
12. **Error Codes** ⭐ - Structured errors + health integration
13. **Quality Gates** - Validation criteria
14. **Integration Points** - How it connects to other components
15. **Code Structure Example** - Implementation template
16. **Related Documentation** - Cross-references

*Note: Specs may have additional domain-specific sections, but these 16 are mandatory.*

## 🎯 **Component Overview**

### **State Monitoring** (Reactive - Triggered by Events) ✅
1. **[Position Monitor](specs/01_POSITION_MONITOR.md)** - Token + Derivative balance tracking
2. **[Exposure Monitor](specs/02_EXPOSURE_MONITOR.md)** - Exposure aggregation & conversion ⭐ **AAVE mechanics canonical source**
3. **[Risk Monitor](specs/03_RISK_MONITOR.md)** - Risk metrics & liquidation simulation
4. **[P&L Calculator](specs/04_PNL_CALCULATOR.md)** - Balance & attribution P&L with reconciliation

### **Decision & Orchestration** (Proactive - Issues Instructions) ✅
5. **[Strategy Manager](specs/05_STRATEGY_MANAGER.md)** - Mode-specific orchestration & rebalancing

### **Execution** (Action - Executes Instructions) ✅
6. **[Execution Manager](specs/06_EXECUTION_MANAGER.md)** - Cross-venue execution orchestration
7. **[Execution Interface Manager](specs/07_EXECUTION_INTERFACE_MANAGER.md)** - Interface management
8. **[Event Logger](specs/08_EVENT_LOGGER.md)** - Audit-grade event tracking
8A. **[Execution Interfaces](specs/08A_EXECUTION_INTERFACES.md)** - Unified execution abstraction (backtest/live)
9. **[Data Provider](specs/09_DATA_PROVIDER.md)** - Market data access (historical + live modes)
10. **[Reconciliation Component](specs/10_RECONCILIATION_COMPONENT.md)** - Position reconciliation
11. **[Position Update Handler](specs/11_POSITION_UPDATE_HANDLER.md)** - Position update orchestration

### **Service Components** (Always Active)
12. **[Frontend Spec](specs/12_FRONTEND_SPEC.md)** - Wizard/stepper UI
13. **[Backtest Service](specs/13_BACKTEST_SERVICE.md)** - Backtest execution service
14. **[Live Trading Service](specs/14_LIVE_TRADING_SERVICE.md)** - Live trading service
15. **[Event Driven Strategy Engine](specs/15_EVENT_DRIVEN_STRATEGY_ENGINE.md)** - Strategy execution engine

### **Supporting Components** (Utilities & Infrastructure)
16. **[Math Utilities](specs/16_MATH_UTILITIES.md)** - Mathematical utilities
17. **[Health & Error Systems](specs/17_HEALTH_ERROR_SYSTEMS.md)** - Structured logging & health monitoring
18. **[Results Store](specs/18_RESULTS_STORE.md)** - Results storage and retrieval

### **Configuration**
19. **[Configuration](specs/CONFIGURATION.md)** - Configuration management

---

## 🔄 **Component Interaction Flow**

**DEPRECATED**: The monitoring cascade (position → exposure → risk → pnl) is no longer automatic.
**NEW ARCHITECTURE**: See ADR-001 in REFERENCE_ARCHITECTURE_CANONICAL.md for current tight loop definition.

**Current Tight Loop Pattern**:
```
execution → position_monitor → reconciliation → next instruction
```

**Full Loop Pattern**:
```
time trigger (60s) → strategy decision → [tight loop 1] → [tight loop 2] → ... → [tight loop N] → complete
```

**Key Principles**:
- Execution manager sends ONE instruction at a time
- Position monitor updates (simulated in backtest, queried in live)
- Execution manager verifies position matches expected state
- Move to next instruction ONLY after reconciliation
- Happens WITHIN the full loop for each execution instruction
- Ensures no race conditions via sequential execution

---

## 📋 **Component Dependency Matrix**

| Component | Depends On | Outputs To |
|-----------|------------|------------|
| **Position Monitor** | Data Provider | Exposure Monitor, Event Logger |
| **Exposure Monitor** | Position Monitor, Data Provider | Risk Monitor, P&L Calculator |
| **Risk Monitor** | Exposure Monitor | Strategy Manager, Event Logger |
| **P&L Calculator** | Exposure Monitor | Results, Event Logger |
| **Strategy Manager** | Risk Monitor, Exposure Monitor | Execution Managers |
| **CEX Exec Manager** | Position Monitor (for updates) | Event Logger |
| **OnChain Exec Manager** | Position Monitor (for updates) | Event Logger |
| **Event Logger** | All components | Results, CSV export |
| **Data Provider** | None (data source) | All monitors |

---

## 🏗️ **Backend File Mapping**

| Component | Backend File | Type |
|-----------|--------------|------|
| **Position Monitor** | `core/strategies/components/position_monitor.py` | ✅ IMPLEMENTED |
| **Exposure Monitor** | `core/strategies/components/exposure_monitor.py` | ✅ IMPLEMENTED |
| **Risk Monitor** | `core/rebalancing/risk_monitor.py` | ✅ IMPLEMENTED |
| **P&L Calculator** | `core/math/pnl_calculator.py` | ✅ IMPLEMENTED |
| **Strategy Manager** | `core/strategies/components/strategy_manager.py` | ✅ IMPLEMENTED |
| **Execution Manager** | `core/execution/execution_manager.py` | ✅ IMPLEMENTED |
| **Execution Interface Manager** | `core/execution/execution_interface_manager.py` | ✅ IMPLEMENTED |
| **Event Logger** | `core/strategies/components/event_logger.py` | ✅ IMPLEMENTED |
| **Execution Interfaces** | `core/interfaces/` | ✅ IMPLEMENTED |
| **Data Provider** | `infrastructure/data/historical_data_provider.py` | ✅ IMPLEMENTED |
| **Reconciliation Component** | `core/reconciliation/reconciliation_component.py` | ✅ IMPLEMENTED |
| **Position Update Handler** | `core/strategies/components/position_update_handler.py` | ✅ IMPLEMENTED |

**For detailed implementation**: See individual component specs in [specs/](specs/) <!-- Directory link to specs folder --> directory

**File paths verified**: October 10, 2025 - All backend file paths confirmed to exist

---

## 🔧 **Configuration Integration**

All components use centralized config infrastructure:
- **ConfigLoader** (`infrastructure/config/config_loader.py`)
- **ConfigValidator** (`infrastructure/config/config_validator.py`)
- **HealthChecker** (`infrastructure/config/health_check.py`)

**For config details**: See [specs/CONFIGURATION.md](specs/CONFIGURATION.md)

---

## 📊 **Implementation Roadmap**

**For week-by-week plan**: See [README.md](README.md) <!-- Redirected from IMPLEMENTATION_ROADMAP.md - implementation status is documented here -->

**For task breakdown**: See [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) <!-- Redirected from REQUIREMENTS.md - requirements are component specifications -->

**Current Priority**:
1. Critical method alignment fixes (1-2 hours)
2. Error code system implementation
3. Advanced features (liquidation sim, KING handling)

---

## 🎯 **Next Steps**

1. **Start implementing?** → [README.md](README.md) <!-- Redirected from IMPLEMENTATION_ROADMAP.md - implementation status is documented here -->
2. **Need component details?** → [specs/](specs/) <!-- Directory link to specs folder --> directory (12 detailed specs)
3. **Architecture questions?** → [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md)
4. **Configuration help?** → [specs/CONFIGURATION.md](specs/CONFIGURATION.md)

---

**Ready to build!** 🚀 See component specs for complete implementation details.

*Last Updated: October 10, 2025*
