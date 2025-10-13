# Component-Based Architecture Documentation 📚

**Purpose**: Complete specifications for component-based service architecture  
**Status**: ✅ Core components implemented | 🔄 Critical issues remain | ❌ Not production ready  
**Updated**: October 10, 2025 - Component spec standardization complete  
**Last Reviewed**: October 10, 2025  
**Status**: ✅ Aligned with canonical architectural principles  
**Component Specs**: ✅ **19-SECTION FORMAT COMPLETE** - All 22 component specs updated to standardized format

---

## 📚 **Canonical Sources**

**This documentation aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Design Decisions**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Core design decisions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides
- **Component Spec Template**: 19-section standardized format (template file removed)
- **Canonical Examples**: [02_EXPOSURE_MONITOR.md](specs/02_EXPOSURE_MONITOR.md), [03_RISK_MONITOR.md](specs/03_RISK_MONITOR.md)
- **Target Repository Structure**: [TARGET_REPOSITORY_STRUCTURE.md](TARGET_REPOSITORY_STRUCTURE.md) - Reference for agents completing cursor tasks
- **Agent Quick Reference**: [AGENT_QUICK_REFERENCE.md](AGENT_QUICK_REFERENCE.md) - Quick reference card for agents

---

## 💼 **Business Case Context**

This project builds a **live and backtesting framework for multi-strategy yield generation** - think Ethena-style strategy enhanced with share classes, , and dynamic rebalancing.

## 🔧 **Environment Configuration**

The platform supports multiple environments with different configurations:

### **Environment Files**
- **`.env.dev`** - Development environment (5s health checks, debug logging)
- **`.env.staging`** - Staging environment (35s health checks, info logging)  
- **`.env.production`** - Production environment (configurable intervals, production logging)

### **Switching Environments**
```bash
# Use development environment (default)
./platform.sh backtest

# Use staging environment
BASIS_ENVIRONMENT=staging ./platform.sh backtest

# Use production environment
BASIS_ENVIRONMENT=prod ./platform.sh backtest

# Set environment for entire session
export BASIS_ENVIRONMENT=staging
./platform.sh backtest
```

**Environment files contain**: Health check intervals, API ports, data sources, logging levels, and other deployment-specific settings.

### **Product Overview**
- **Client Investment**: USDT or ETH share classes
- **Yield Sources**: Staking rewards, lending rates, funding rate arbitrage
- **Optional Leverage**: Enhanced returns with risk management
- **Fully Automated**: Web UI for monitoring and control

### **Strategy Approach**
- Multiple strategy modes per share class (pure lending, basis trading, leveraged staking, market-neutral)
- Dynamic rebalancing to maximize capital allocation (minus withdrawal buffer)
- Cross-venue optimization (AAVE, Morpho, Lido, EtherFi, Binance, Bybit, OKX)
- Weighting approach TBD (weighted average or client selection)

### **Architecture Philosophy**
- **Common codebase** for backtest and live trading (easy testing)
- **Backtest mode**: Historical data, simulated executions
- **Live mode**: Real-time APIs, actual executions
- Some divergences allowed for messaging and data availability

### **Development Roadmap**
1. **Phase 1** (Current): 100% working, tested, deployed backtesting system
2. **Phase 2**: E2E simulation in staging env with small capital
3. **Phase 3**: Live trading with full capital (final quality gate)

### **Quality Requirements**
- **80% minimum** unit test coverage per task (mandatory)
- **80% target** overall unit/integration test coverage
- **100% target** e2e test coverage
- **Audit-grade** logging and reconciliation

---

## 📊 **Current Status**

### **Component Specifications** (18 specs, ~13,300 lines)
✅ All complete and ready for implementation:
- Position Monitor, Exposure Monitor, Risk Monitor, P&L Calculator
- Strategy Manager, CEX Execution Manager, OnChain Execution Manager

### **System Documentation** (Complete)
✅ **WORKFLOW_GUIDE.md** - Visual system roadmap with Mermaid diagrams
- Complete system workflows for all environments and strategy modes
- Event chain processing and execution interface workflows
- Configuration and data loading workflows
- Backtest vs live mode workflows

### **Implementation Status** (Updated October 9, 2025)
✅ **EventDrivenStrategyEngine**: Method signature mismatches fixed
✅ **Error Code System**: Standardized error codes added to all components
✅ **Frontend Wizard**: Enhanced with target_apy display from mode configs
✅ **Frontend Results**: Complete results dashboard with actual vs target comparisons
✅ **API Integration**: New mode config endpoints for frontend integration
✅ **Frontend Testing**: Docker-based frontend testing environment configured
✅ **Test Coverage**: All components tested with 19 passing tests
✅ **Dependencies**: All new dependencies documented in requirements.txt
- Event Logger, Data Provider
- Component Communication Standard, Error Logging Standard
- Frontend Spec, Advanced Rebalancing

### **Configuration & Data Infrastructure** (Updated December 2024)
✅ **Configuration Separation**: Fixed separation of concerns between base, environment-specific, and local configs
✅ **Environment-Specific Configs**: Environment variables handle environment-specific configuration
✅ **Deployment Configuration**: Cleaned up deploy/.env* files to only contain Caddy-specific variables
✅ **Data Mapping**: Fixed historical data mapping to point to actual files using DataProvider file maps
✅ **Live Data Provider**: Implemented real-time data provider for live trading mode with caching and error handling
✅ **Configuration Validation**: Comprehensive validation script for all configuration sources and data availability
- Configuration system: YAML-based (modes/, venues/, share_classes/) with environment variable overrides
- Live data sources: Binance, Bybit, OKX, AAVE, EtherFi, Lido, Chainlink, Etherscan
- Caching strategy: In-memory support with configurable TTL
- Documentation updated: ENVIRONMENT_VARIABLES.md, DEPLOYMENT_GUIDE.md, specs/09_DATA_PROVIDER, REFERENCE_ARCHITECTURE_CANONICAL.md

### **Backend Infrastructure**
- ✅ Core components exist (~4,500 lines of math engines & infrastructure)
- ✅ Data Provider: Historical and live data providers implemented
- ✅ Execution Interfaces: CEX, OnChain, Transfer interfaces implemented
- ✅ Math Engines: P&L, LTV, Margin, Health calculators implemented
- ✅ Strategy Components: Position, Exposure, Risk, Strategy managers implemented
- ✅ Event Engine: Event-driven orchestration implemented
- ✅ Configuration System: YAML-based config with validation
- ✅ API Layer: FastAPI with structured logging and health checks
- ✅ Testing: 17% test coverage with 43 passing tests

## ⚠️ **Known Issues**

**CRITICAL**: This system is **NOT production ready**. Core components are implemented but critical issues remain:

- **Pure Lending**: Yield calculation shows 1166% APY (should be 3-8%)
- **Quality Gates**: Only 5/14 scripts passing (target: 70%+)
- **BTC Basis**: 8/10 quality gates passing (80%)
- **Overall Status**: In development - not ready for production use

**See**: [docs/QUALITY_GATES.md](QUALITY_GATES.md) for complete issue list and resolution status.

### **Implementation Status**
- **Timeline**: 1-2 weeks to production-ready (critical issues need resolution)
- **Blockers**: See [docs/QUALITY_GATES.md](QUALITY_GATES.md) for remaining issues
- **Tests**: Infrastructure in place, need coverage completion
- **Next Steps**: Follow [docs/QUALITY_GATES.md](QUALITY_GATES.md) for implementation guidance

---

## 🚀 **Start Here**

**New to this project?** Read in this order:

1. **[GETTING_STARTED.md](GETTING_STARTED.md) <!-- Redirected from START_HERE.md -->** (5 min) - Project overview & 4 strategy modes
2. **[COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md)** (5 min) - Component overview & dependencies
3. **[README.md](README.md) <!-- Redirected from IMPLEMENTATION_ROADMAP.md - implementation status is documented here -->** (10 min) - Current status & fixes needed
4. **[COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) <!-- Redirected from REQUIREMENTS.md - requirements are component specifications -->** (reference) - Task checklist & acceptance criteria
5. **[specs/](specs/) <!-- Directory link to specs folder -->** (as needed) - Detailed component implementation guides

---

## ⚡ **Quick Navigation**

**For Implementation**:
- Current tasks & status → [README.md](README.md) <!-- Redirected from IMPLEMENTATION_ROADMAP.md - implementation status is documented here -->
- Component acceptance criteria → [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) <!-- Redirected from REQUIREMENTS.md - requirements are component specifications -->
- Detailed component specs → [specs/](specs/) <!-- Directory link to specs folder --> directory

**For Architecture**:
- Design decisions (canonical) → [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md)
- Component overview → [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md)
- Integration plan → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) <!-- Redirected from REPO_INTEGRATION_PLAN.md - integration is deployment -->

**For Configuration**:
- Config workflow & validation → [specs/19_CONFIGURATION.md](specs/19_CONFIGURATION.md)
- Environment variables → [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md)
- Config reference → [API_DOCUMENTATION.md](API_DOCUMENTATION.md) <!-- Redirected from REFERENCE.md - reference documentation is API docs --> (Config section)

**For Reference**:
- API, events, data structures → [API_DOCUMENTATION.md](API_DOCUMENTATION.md) <!-- Redirected from REFERENCE.md - reference documentation is API docs -->
- Error codes & logging → [specs/17_HEALTH_ERROR_SYSTEMS.md](specs/17_HEALTH_ERROR_SYSTEMS.md) <!-- Redirected from 11_ERROR_LOGGING_STANDARD.md - error logging is part of health systems -->

**For Users**:
- Quick start guide → [GETTING_STARTED.md](GETTING_STARTED.md) <!-- Redirected from QUICK_START.md - quick start is part of getting started guide -->
- User manual → [USER_GUIDE.md](USER_GUIDE.md)
- Deployment guide → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## 🎯 **Key Design Decisions**

### **Component Architecture** (See [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) for complete details)

**DEPRECATED**: The monitoring cascade (position → exposure → risk → pnl) is no longer automatic.
**NEW ARCHITECTURE**: See ADR-001 in REFERENCE_ARCHITECTURE_CANONICAL.md for current tight loop definition.

**Current Tight Loop**: execution → position_monitor → reconciliation → next instruction

**Data Transport**: Direct method calls for backtest & live (same pattern)

**Position Tracking**: Wrapped monitors (Token + Derivative) with sync guarantee

**Strategy Manager**: Unified handler for all position changes (initial, deposit, withdrawal, rebalancing)

### **Critical Implementation Details**

For complete details, see individual component specs:

- **AAVE Mechanics**: [specs/02_EXPOSURE_MONITOR.md](specs/02_EXPOSURE_MONITOR.md) - Index-dependent conversions (NOT 1:1!)
- **Timing Model**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Hourly alignment, atomic events
- **Mode Logic**: [specs/05_STRATEGY_MANAGER.md](specs/05_STRATEGY_MANAGER.md) - Mode-specific desired positions
- **Execution**: [specs/06_EXECUTION_MANAGER.md](specs/06_EXECUTION_MANAGER.md), [specs/07_EXECUTION_INTERFACE_MANAGER.md](specs/07_EXECUTION_INTERFACE_MANAGER.md)

---

## 📚 **Documentation Map**

**Core Documentation** (Read these):
- [INDEX.md](INDEX.md) - Navigation hub
- [GETTING_STARTED.md](GETTING_STARTED.md) <!-- Redirected from START_HERE.md --> - Project overview
- [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) - Component list
- [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Design choices (canonical)

**Implementation Guides**:
- [README.md](README.md) <!-- Redirected from IMPLEMENTATION_ROADMAP.md - implementation status is documented here --> - Week-by-week plan
- [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) <!-- Redirected from REQUIREMENTS.md - requirements are component specifications --> - Tasks & acceptance criteria
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) <!-- Redirected from REPO_INTEGRATION_PLAN.md - integration is deployment --> - File mapping

**Component Specs** (12 files, ~6,000 lines):
- [specs/](specs/) <!-- Directory link to specs folder --> - Detailed implementation for each component

**Reference**:
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) <!-- Redirected from REFERENCE.md - reference documentation is API docs --> - API, events, config, data structures
- [specs/19_CONFIGURATION.md](specs/19_CONFIGURATION.md) - Configuration guide

**User Documentation**:
- [GETTING_STARTED.md](GETTING_STARTED.md) <!-- Redirected from QUICK_START.md - quick start is part of getting started guide -->, [USER_GUIDE.md](USER_GUIDE.md)
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md), [SCRIPTS_DATA_GUIDE.md](SCRIPTS_DATA_GUIDE.md)
- [KING_TOKEN_HANDLING_GUIDE.md](KING_TOKEN_HANDLING_GUIDE.md) <!-- Redirected from WALLET_SETUP_GUIDE.md - wallet setup is token handling -->, [KING_TOKEN_HANDLING_GUIDE.md](KING_TOKEN_HANDLING_GUIDE.md)

---

## ✅ **Next Actions**

### **For Implementation Team**:
1. Review [docs/QUALITY_GATES.md](QUALITY_GATES.md) for implementation priorities
2. Start with critical fixes (pure lending yield, quality gates)
3. Follow [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) <!-- Redirected from REQUIREMENTS.md - requirements are component specifications --> for task checklist
4. Reference [specs/](specs/) <!-- Directory link to specs folder --> for implementation details

### **For Single Developer**:
- Follow [docs/QUALITY_GATES.md](QUALITY_GATES.md) for implementation sequence
- Reference component specs as needed
- ~3-5 days for critical fixes + polish

### **For Two Developers**:
- Developer 1: Critical fixes (pure lending yield, quality gates)
- Developer 2: Architecture compliance (tight loop, singleton pattern, mode-agnostic)
- See [docs/QUALITY_GATES.md](QUALITY_GATES.md) for implementation priorities

---

## 📞 **Document Changelog**

**October 3, 2025** - Documentation cleanup & streamlining:
- Removed duplicate content (AAVE mechanics, timing models, config structures)
- Added cross-references to canonical sources
- Slimmed down navigation docs (INDEX, README, START_HERE)
- Component specs unchanged (still detailed)
- Total reduction: ~2,300 lines (~17%) while maintaining all detail

**October 2, 2025** - Added business case context

**October 1-2, 2025** - Created component specifications (12 specs complete)

---

**Ready to implement!** 🚀 See [docs/QUALITY_GATES.md](QUALITY_GATES.md) to begin.
