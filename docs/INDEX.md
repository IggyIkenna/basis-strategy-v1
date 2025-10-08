# Documentation Index 📚

**Quick Navigation** - Find what you need in < 3 clicks  
**Status**: Backend implemented ✅ Core components working, critical issues remain  
**Updated**: October 5, 2025 - Implementation completed

---

## 🚀 **START HERE**

### **New User?**
→ **[START_HERE.md](START_HERE.md)** (5 min read)
- Project overview & 4 strategy modes
- Current implementation status
- Read this first!

### **Want to Run It?**
→ **[QUICK_START.md](QUICK_START.md)** (5 min read)
- Get the platform running immediately
- Test your first backtest
- Backend fully functional

### **Implementation Status?**
→ **[IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)** (10 min read)
- Implementation completed
- All critical fixes done
- Production-ready status

→ **[REQUIREMENTS.md](REQUIREMENTS.md)** (reference)
- Component-by-component tasks
- Acceptance criteria
- Test coverage requirements

### **Need Component Details?**
→ **[COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md)** (5 min read)
- 9 core components overview
- Component dependencies
- Backend file mapping

→ **[specs/](specs/)** directory
- 12 detailed implementation specs (~6,000 lines)
- Each component fully documented

---

## 📚 **Reference Documentation**

### **Architecture & Design**
→ **[ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md)** ⭐ **CANONICAL SOURCE**
- 38 approved design decisions
- Wallet/venue model, timing constraints
- AAVE position naming, hedge logic
- Single source of truth for all design choices

→ **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** ⭐ **VISUAL ROADMAP**
- Complete system workflows with Mermaid diagrams
- Environment & configuration flows
- Event chain processing
- Execution interface workflows
- Strategy mode workflows
- Visual system architecture

→ **[COMPONENT_HEALTH_SYSTEM.md](COMPONENT_HEALTH_SYSTEM.md)** ⭐ **HEALTH MONITORING**
- Comprehensive component health checking
- Real-time health status with timestamps
- Error codes for troubleshooting
- API endpoints for dynamic health checking
- Component readiness validation

→ **[QUALITY_GATES.md](QUALITY_GATES.md)** ⭐ **QUALITY VALIDATION**
- Complete system quality gates specification
- Component health validation requirements
- Event chain validation requirements
- Test coverage requirements (80% target)
- Performance benchmarks and validation
- Integration testing requirements

### **Configuration**
→ **[CONFIG_WORKFLOW.md](CONFIG_WORKFLOW.md)**
- Configuration hierarchy & validation
- Mode/venue/share class configs
- Update workflow & restart procedures

### **API, Events, & Data**
→ **[REFERENCE.md](REFERENCE.md)**
- API endpoints & request/response formats
- Event structure & types
- Component data structures
- Error codes & logging

---

## 📖 **User Documentation**

→ **[QUICK_START.md](QUICK_START.md)** - 10-minute getting started  
→ **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user manual  
→ **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Docker + GCloud deployment  
→ **[SCRIPTS_DATA_GUIDE.md](SCRIPTS_DATA_GUIDE.md)** - Data pipeline & orchestrators  
→ **[WALLET_SETUP_GUIDE.md](WALLET_SETUP_GUIDE.md)** - Wallet configuration  
→ **[KING_TOKEN_HANDLING_GUIDE.md](KING_TOKEN_HANDLING_GUIDE.md)** - KING token unwrapping  
→ **[DATA_VALIDATION_GUIDE.md](DATA_VALIDATION_GUIDE.md)** - Complete data validation guide (primary)  
→ **[DATA_REQUIREMENTS_AND_VALIDATION_GUIDE.md](DATA_REQUIREMENTS_AND_VALIDATION_GUIDE.md)** - Quick reference (lightweight)  
→ **[ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md)** - Environment variables

---

## 🏗️ **Component Specifications** (Source of Truth)

All component specs in **[specs/](specs/)** directory:

**Core Components**:
1. [Position Monitor](specs/01_POSITION_MONITOR.md) - Balance tracking
2. [Exposure Monitor](specs/02_EXPOSURE_MONITOR.md) - AAVE conversion & net delta
3. [Risk Monitor](specs/03_RISK_MONITOR.md) - LTV, margin, liquidation
4. [P&L Calculator](specs/04_PNL_CALCULATOR.md) - Balance & attribution P&L
5. [Strategy Manager](specs/05_STRATEGY_MANAGER.md) - Mode-specific orchestration
6. [CEX Execution Manager](specs/06_CEX_EXECUTION_MANAGER.md) - CEX trading
7. [OnChain Execution Manager](specs/07_ONCHAIN_EXECUTION_MANAGER.md) - Blockchain operations
8. [Event Logger](specs/08_EVENT_LOGGER.md) - Audit logging
9. [Data Provider](specs/09_DATA_PROVIDER.md) - Market data

**Standards**:
10. [Redis Messaging](specs/10_REDIS_MESSAGING_STANDARD.md) - Inter-component communication
11. [Error Logging](specs/11_ERROR_LOGGING_STANDARD.md) - Structured logging

**Frontend**:
12. [Frontend Spec](specs/12_FRONTEND_SPEC.md) - UI wizard/stepper
13. [Advanced Rebalancing](specs/13_ADVANCED_REBALANCING.md) - Rebalancing logic

---

## 📊 **Current Status**

**Component Specs**: 12/12 Complete ✅  
**Backend Infrastructure**: Exists, needs method alignment  
**Timeline**: 1-2 weeks to production-ready (critical issues need resolution)  
**Blockers**: Pure lending yield calculation, quality gates

---

## 🔍 **Finding Specific Information**

| Looking for... | Go to... |
|----------------|----------|
| System workflows & diagrams | [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) |
| Component health monitoring | [COMPONENT_HEALTH_SYSTEM.md](COMPONENT_HEALTH_SYSTEM.md) |
| Quality gates & validation | [QUALITY_GATES.md](QUALITY_GATES.md) |
| AAVE index mechanics | [specs/02_EXPOSURE_MONITOR.md](specs/02_EXPOSURE_MONITOR.md) |
| Timing & event model | [ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md) |
| Mode configurations | [CONFIG_WORKFLOW.md](CONFIG_WORKFLOW.md) |
| Component data flow | [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) |
| Implementation tasks | [REQUIREMENTS.md](REQUIREMENTS.md) |
| API endpoints | [REFERENCE.md](REFERENCE.md) |
| Error codes | [specs/11_ERROR_LOGGING_STANDARD.md](specs/11_ERROR_LOGGING_STANDARD.md) |

---

**For document updates**: See [README.md](README.md) changelog

*Last Updated: October 3, 2025*
