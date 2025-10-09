# Component Specifications - Index 📚

**Purpose**: Central index to all component specifications  
**Status**: ✅ Core components implemented, critical issues remain  
**Updated**: October 5, 2025 - Core components working, critical issues remain  
**Last Reviewed**: October 8, 2025  
**Status**: ✅ Aligned with canonical sources (.cursor/tasks/ + MODES.md)

---

## 📚 **Canonical Sources**

**This index aligns with canonical architectural principles**:
- **Architectural Principles**: [CANONICAL_ARCHITECTURAL_PRINCIPLES.md](CANONICAL_ARCHITECTURAL_PRINCIPLES.md) - Consolidated from all .cursor/tasks/
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Design Decisions**: [ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md) - Core design decisions
- **Task Specifications**: `.cursor/tasks/` - Individual task specifications

---

## ✅ **Current Implementation Status**

**All 9 Core Components**: ✅ **CORE COMPONENTS IMPLEMENTED, CRITICAL ISSUES REMAIN**
- Backend deployment functional with critical issues
- All API endpoints working
- Backtest system executing end-to-end with yield calculation issues
- Test coverage working towards 80% target

## 🎯 **Component Overview**

### **State Monitoring** (Reactive - Triggered by Events) ✅
1. **[Position Monitor](specs/01_POSITION_MONITOR.md)** - Token + Derivative balance tracking
2. **[Exposure Monitor](specs/02_EXPOSURE_MONITOR.md)** - Exposure aggregation & conversion ⭐ **AAVE mechanics canonical source**
3. **[Risk Monitor](specs/03_RISK_MONITOR.md)** - Risk metrics & liquidation simulation
4. **[P&L Calculator](specs/04_PNL_CALCULATOR.md)** - Balance & attribution P&L with reconciliation

### **Decision & Orchestration** (Proactive - Issues Instructions) ✅
5. **[Strategy Manager](specs/05_STRATEGY_MANAGER.md)** - Mode-specific orchestration & rebalancing

### **Execution** (Action - Executes Instructions) ✅
6. **[CEX Execution Interface](specs/06_CEX_EXECUTION_MANAGER.md)** - Off-chain execution
7. **[OnChain Execution Interface](specs/07_ONCHAIN_EXECUTION_MANAGER.md)** - On-chain execution
8. **[Execution Interfaces](specs/08_EXECUTION_INTERFACES.md)** - Unified execution abstraction (backtest/live)
9. **[Execution Manager](specs/08_EXECUTION_INTERFACES.md)** - Cross-venue execution orchestration

### **Supporting Infrastructure** (Always Active)
10. **[Event Logger](specs/08_EVENT_LOGGER.md)** - Audit-grade event tracking
11. **[Data Provider](specs/09_DATA_PROVIDER.md)** - Market data access (historical + live modes)

### **Standards** (Cross-Cutting)
12. **[Redis Messaging Standard](specs/10_REDIS_MESSAGING_STANDARD.md)** - Pub/sub patterns
13. **[Error Logging Standard](specs/11_ERROR_LOGGING_STANDARD.md)** - Structured logging

### **Frontend**
14. **[Frontend Spec](specs/12_FRONTEND_SPEC.md)** - Wizard/stepper UI
15. **[Advanced Rebalancing](specs/13_ADVANCED_REBALANCING.md)** - Rebalancing logic

---

## 🔄 **Component Interaction Flow**

```
Balance Change Event
    ↓ (synchronous chain)
Position Monitor
    ↓ (immediate)
Exposure Monitor
    ↓ (immediate)
Risk Monitor
    ↓ (immediate)
P&L Calculator
    ↓ (immediate)
Strategy Manager (checks if action needed)
    ↓ (if rebalancing triggered)
Execution Managers (execute instructions)
    ↓ (feedback loop)
Position Monitor (balance changes from execution)
```

**All synchronous until execution!**

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
| **CEX Exec Interface** | `core/interfaces/cex_execution_interface.py` | ✅ IMPLEMENTED |
| **OnChain Exec Interface** | `core/interfaces/onchain_execution_interface.py` | ✅ IMPLEMENTED |
| **Event Logger** | `core/strategies/components/event_logger.py` | ✅ IMPLEMENTED |
| **Data Provider** | `infrastructure/data/historical_data_provider.py` | ✅ IMPLEMENTED |

**For detailed implementation**: See individual component specs in [specs/](specs/) directory

---

## 🔧 **Configuration Integration**

All components use centralized config infrastructure:
- **ConfigLoader** (`infrastructure/config/config_loader.py`)
- **ConfigValidator** (`infrastructure/config/config_validator.py`)
- **HealthChecker** (`infrastructure/config/health_check.py`)

**For config details**: See [specs/CONFIGURATION.md](specs/CONFIGURATION.md)

---

## 📊 **Implementation Roadmap**

**For week-by-week plan**: See [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)

**For task breakdown**: See [REQUIREMENTS.md](REQUIREMENTS.md)

**Current Priority**:
1. Critical method alignment fixes (1-2 hours)
2. Error code system implementation
3. Advanced features (liquidation sim, KING handling)

---

## 🎯 **Next Steps**

1. **Start implementing?** → [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)
2. **Need component details?** → [specs/](specs/) directory (12 detailed specs)
3. **Architecture questions?** → [ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md)
4. **Configuration help?** → [specs/CONFIGURATION.md](specs/CONFIGURATION.md)

---

**Ready to build!** 🚀 See component specs for complete implementation details.

*Last Updated: October 3, 2025*
