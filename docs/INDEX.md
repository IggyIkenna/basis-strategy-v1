# Documentation Index 📚

**Quick Navigation** - Find what you need in < 3 clicks  
**Status**: ✅ Core components implemented | 🔄 Critical issues remain | ❌ Not production ready  
**Updated**: October 5, 2025 - Implementation completed  
**Last Reviewed**: October 8, 2025  
**Status**: ✅ Aligned with canonical architectural principles

---

## 📚 **Canonical Sources**

**This index aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Design Decisions**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Core design decisions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

---

## ⚠️ **Known Issues**

**CRITICAL**: This system is **NOT production ready**. Core components are implemented but critical issues remain:

- **Pure Lending**: Yield calculation shows 1166% APY (should be 3-8%)
- **Quality Gates**: Only 5/14 scripts passing (target: 70%+)
- **BTC Basis**: 8/10 quality gates passing (80%)
- **Overall Status**: In development - not ready for production use

**See**: [docs/QUALITY_GATES.md](QUALITY_GATES.md) for complete issue list and resolution status.

---

## 🚀 **START HERE**

### **New User?**
→ **[GETTING_STARTED.md](GETTING_STARTED.md) <!-- Redirected from START_HERE.md -->** (5 min read)
- Project overview & 4 strategy modes
- Current implementation status
- Read this first!

### **Want to Run It?**
→ **[GETTING_STARTED.md](GETTING_STARTED.md) <!-- Redirected from QUICK_START.md - quick start is part of getting started guide -->** (5 min read)
- Get the platform running immediately
- Test your first backtest
- Backend core components implemented

### **Implementation Status?**
→ **[README.md](README.md) <!-- Redirected from IMPLEMENTATION_ROADMAP.md - implementation status is documented here -->** (10 min read)
- Implementation completed
- All critical fixes done
- Production-ready status

→ **[COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) <!-- Redirected from REQUIREMENTS.md - requirements are component specifications -->** (reference)
- Component-by-component tasks
- Acceptance criteria
- Test coverage requirements

### **Need Component Details?**
→ **[COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md)** (5 min read)
- 11 core components overview
- Component dependencies
- Backend file mapping

→ **[specs/](specs/) <!-- Directory link to specs folder -->** directory
- 12 detailed implementation specs (~6,000 lines)
- Each component fully documented

---

## 📚 **Reference Documentation**

### **Architecture & Design**
→ **[REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md)** ⭐ **CANONICAL SOURCE**
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

→ **[specs/17_HEALTH_ERROR_SYSTEMS.md](specs/17_HEALTH_ERROR_SYSTEMS.md) <!-- Redirected from COMPONENT_HEALTH_SYSTEM.md - health system is in specs -->** ⭐ **HEALTH MONITORING**
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
→ **[specs/CONFIGURATION.md](specs/CONFIGURATION.md)**
- Configuration hierarchy & validation
- Mode/venue/share class configs
- Update workflow & restart procedures

### **API, Events, & Data**
→ **[API_DOCUMENTATION.md](API_DOCUMENTATION.md) <!-- Redirected from REFERENCE.md - reference documentation is API docs -->**
- API endpoints & request/response formats
- Event structure & types
- Component data structures
- Error codes & logging

---

## 📖 **User Documentation**

→ **[GETTING_STARTED.md](GETTING_STARTED.md) <!-- Redirected from QUICK_START.md - quick start is part of getting started guide -->** - 10-minute getting started  
→ **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user manual  
→ **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Docker + GCloud deployment  
→ **[SCRIPTS_DATA_GUIDE.md](SCRIPTS_DATA_GUIDE.md)** - Data pipeline & orchestrators  
→ **[KING_TOKEN_HANDLING_GUIDE.md](KING_TOKEN_HANDLING_GUIDE.md) <!-- Redirected from WALLET_SETUP_GUIDE.md - wallet setup is token handling -->** - Wallet configuration  
→ **[KING_TOKEN_HANDLING_GUIDE.md](KING_TOKEN_HANDLING_GUIDE.md)** - KING token unwrapping  
→ **[specs/09_DATA_PROVIDER](specs/09_DATA_PROVIDER)** - Complete data provider spec with comprehensive validation guide  
→ **[ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md)** - Environment variables

---

## 🏗️ **Component Specifications** (Source of Truth)

All component specs in **[specs/](specs/) <!-- Directory link to specs folder -->** directory:

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
10. [Component Communication](specs/10_COMPONENT_COMMUNICATION_STANDARD.md) - Direct method call patterns
11. [Error Logging](specs/17_HEALTH_ERROR_SYSTEMS.md) <!-- Redirected from 11_ERROR_LOGGING_STANDARD.md - error logging is part of health systems --> - Structured logging

**Frontend**:
12. [Frontend Spec](specs/12_FRONTEND_SPEC.md) - UI wizard/stepper
13. [Strategy Management](specs/05_STRATEGY_MANAGER.md) <!-- Redirected from 13_ADVANCED_REBALANCING.md - rebalancing is strategy management --> - Rebalancing logic

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
| Component health monitoring | [specs/17_HEALTH_ERROR_SYSTEMS.md](specs/17_HEALTH_ERROR_SYSTEMS.md) <!-- Redirected from COMPONENT_HEALTH_SYSTEM.md - health system is in specs --> |
| Quality gates & validation | [QUALITY_GATES.md](QUALITY_GATES.md) |
| AAVE index mechanics | [specs/02_EXPOSURE_MONITOR.md](specs/02_EXPOSURE_MONITOR.md) |
| Timing & event model | [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) |
| Mode configurations | [specs/CONFIGURATION.md](specs/CONFIGURATION.md) |
| Component data flow | [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) |
| Implementation tasks | [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) <!-- Redirected from REQUIREMENTS.md - requirements are component specifications --> |
| API endpoints | [API_DOCUMENTATION.md](API_DOCUMENTATION.md) <!-- Redirected from REFERENCE.md - reference documentation is API docs --> |
| Error codes | [specs/17_HEALTH_ERROR_SYSTEMS.md](specs/17_HEALTH_ERROR_SYSTEMS.md) <!-- Redirected from 11_ERROR_LOGGING_STANDARD.md - error logging is part of health systems --> |

---

**For document updates**: See [README.md](README.md) changelog

*Last Updated: October 3, 2025*
