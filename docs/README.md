# Component-Based Architecture Documentation 📚

**Purpose**: Complete specifications for component-based service architecture  
**Status**: ✅ ALL SPECIFICATIONS COMPLETE - Ready for implementation  
**Updated**: October 3, 2025 - Documentation cleanup & streamlining

---

## 💼 **Business Case Context**

This project builds a **live and backtesting framework for multi-strategy yield generation** - think Ethena-style strategy enhanced with share classes, fast withdrawals, and dynamic rebalancing.

### **Product Overview**
- **Client Investment**: USDT or ETH share classes
- **Yield Sources**: Staking rewards, lending rates, funding rate arbitrage
- **Optional Leverage**: Enhanced returns with risk management
- **Fast Withdrawals**: Dynamic buffer for rapid redemptions
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

### **Component Specifications** (12 specs, ~6,000 lines)
✅ All complete and ready for implementation:
- Position Monitor, Exposure Monitor, Risk Monitor, P&L Calculator
- Strategy Manager, CEX Execution Manager, OnChain Execution Manager

### **System Documentation** (Complete)
✅ **WORKFLOW_GUIDE.md** - Visual system roadmap with Mermaid diagrams
- Complete system workflows for all environments and strategy modes
- Event chain processing and execution interface workflows
- Configuration and data loading workflows
- Backtest vs live mode workflows

### **Agent A Implementation Status** (Updated October 3, 2025)
✅ **EventDrivenStrategyEngine**: Method signature mismatches fixed
✅ **Error Code System**: Standardized error codes added to all Agent A components
✅ **Frontend Wizard**: Enhanced with target_apy display from mode configs
✅ **Frontend Results**: Complete results dashboard with actual vs target comparisons
✅ **API Integration**: New mode config endpoints for frontend integration
✅ **Frontend Testing**: Docker-based frontend testing environment configured
✅ **Test Coverage**: All Agent A components tested with 19 passing tests
✅ **Dependencies**: All new dependencies documented in requirements.txt
- Event Logger, Data Provider
- Redis Messaging Standard, Error Logging Standard
- Frontend Spec, Advanced Rebalancing

### **Configuration & Data Infrastructure** (Updated December 2024)
✅ **Configuration Separation**: Fixed separation of concerns between base, environment-specific, and local configs
✅ **Environment-Specific Configs**: Added staging.json and production.json for proper environment management
✅ **Deployment Configuration**: Cleaned up deploy/.env* files to only contain Caddy-specific variables
✅ **Data Mapping**: Fixed historical data mapping to point to actual files using DataProvider file maps
✅ **Live Data Provider**: Implemented real-time data provider for live trading mode with caching and error handling
✅ **Configuration Validation**: Comprehensive validation script for all configuration sources and data availability
- Configuration system: YAML-based (modes/, venues/, share_classes/) - JSON hierarchy not yet implemented
- Live data sources: Binance, Bybit, OKX, AAVE, EtherFi, Lido, Chainlink, Etherscan
- Caching strategy: In-memory and Redis support with configurable TTL
- Documentation updated: ENVIRONMENT_VARIABLES.md, DEPLOYMENT_GUIDE.md, DATA_VALIDATION_GUIDE.md, ARCHITECTURAL_DECISIONS.md

### **Backend Infrastructure**
- ✅ Core components exist (~4,500 lines of math engines & infrastructure)
- ✅ Data Provider: Historical and live data providers implemented
- ✅ Execution Interfaces: CEX, OnChain, Transfer interfaces implemented
- ✅ Math Engines: P&L, LTV, Margin, Health calculators implemented
- ✅ Strategy Components: Position, Exposure, Risk, Strategy managers implemented
- ✅ Event Engine: Event-driven orchestration implemented
- ✅ Configuration System: YAML-based config with validation
- ✅ API Layer: FastAPI with structured logging and health checks
- ✅ Testing: 43% test coverage with 133/133 component tests passing

### **Critical Issues Remaining**
- 🔄 **Pure Lending Yield Calculation**: Unrealistic 1166% APY (should be 3-8%)
- 🔄 **Scripts Directory Quality Gates**: Only 5/14 scripts passing (35.7%)
- 🔄 **Configuration System**: JSON hierarchy documented but not implemented

### **Implementation Status**
- **Timeline**: 1-2 weeks to production-ready (critical issues need resolution)
- **Blockers**: Pure lending yield calculation, quality gates
- **Tests**: Infrastructure in place, need coverage completion

---

## 🚀 **Start Here**

**New to this project?** Read in this order:

1. **[START_HERE.md](START_HERE.md)** (5 min) - Project overview & 4 strategy modes
2. **[COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md)** (5 min) - Component overview & dependencies
3. **[IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)** (10 min) - Current status & fixes needed
4. **[REQUIREMENTS.md](REQUIREMENTS.md)** (reference) - Task checklist & acceptance criteria
5. **[specs/](specs/)** (as needed) - Detailed component implementation guides

---

## ⚡ **Quick Navigation**

**For Implementation**:
- Current tasks & status → [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)
- Component acceptance criteria → [REQUIREMENTS.md](REQUIREMENTS.md)
- Detailed component specs → [specs/](specs/) directory

**For Architecture**:
- Design decisions (canonical) → [ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md)
- Component overview → [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md)
- Integration plan → [REPO_INTEGRATION_PLAN.md](REPO_INTEGRATION_PLAN.md)

**For Configuration**:
- Config workflow & validation → [CONFIG_WORKFLOW.md](CONFIG_WORKFLOW.md)
- Environment variables → [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md)
- Config reference → [REFERENCE.md](REFERENCE.md) (Config section)

**For Reference**:
- API, events, data structures → [REFERENCE.md](REFERENCE.md)
- Error codes & logging → [specs/11_ERROR_LOGGING_STANDARD.md](specs/11_ERROR_LOGGING_STANDARD.md)

**For Users**:
- Quick start guide → [QUICK_START.md](QUICK_START.md)
- User manual → [USER_GUIDE.md](USER_GUIDE.md)
- Deployment guide → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## 🎯 **Key Design Decisions**

### **Component Architecture** (See [ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md) for complete details)

**Sync Update Chain**:
```
Balance Change → Position Monitor → Exposure Monitor → Risk Monitor → P&L Calculator → Strategy Manager
```

**Data Transport**: Redis for backtest & live (same pattern)

**Position Tracking**: Wrapped monitors (Token + Derivative) with sync guarantee

**Strategy Manager**: Unified handler for all position changes (initial, deposit, withdrawal, rebalancing)

### **Critical Implementation Details**

For complete details, see individual component specs:

- **AAVE Mechanics**: [specs/02_EXPOSURE_MONITOR.md](specs/02_EXPOSURE_MONITOR.md) - Index-dependent conversions (NOT 1:1!)
- **Timing Model**: [ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md) - Hourly alignment, atomic events
- **Mode Logic**: [specs/05_STRATEGY_MANAGER.md](specs/05_STRATEGY_MANAGER.md) - Mode-specific desired positions
- **Execution**: [specs/06_CEX_EXECUTION_MANAGER.md](specs/06_CEX_EXECUTION_MANAGER.md), [specs/07_ONCHAIN_EXECUTION_MANAGER.md](specs/07_ONCHAIN_EXECUTION_MANAGER.md)

---

## 📚 **Documentation Map**

**Core Documentation** (Read these):
- [INDEX.md](INDEX.md) - Navigation hub
- [START_HERE.md](START_HERE.md) - Project overview
- [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) - Component list
- [ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md) - Design choices (canonical)

**Implementation Guides**:
- [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) - Week-by-week plan
- [REQUIREMENTS.md](REQUIREMENTS.md) - Tasks & acceptance criteria
- [REPO_INTEGRATION_PLAN.md](REPO_INTEGRATION_PLAN.md) - File mapping

**Component Specs** (12 files, ~6,000 lines):
- [specs/](specs/) - Detailed implementation for each component

**Reference**:
- [REFERENCE.md](REFERENCE.md) - API, events, config, data structures
- [CONFIG_WORKFLOW.md](CONFIG_WORKFLOW.md) - Configuration guide

**User Documentation**:
- [QUICK_START.md](QUICK_START.md), [USER_GUIDE.md](USER_GUIDE.md)
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md), [SCRIPTS_DATA_GUIDE.md](SCRIPTS_DATA_GUIDE.md)
- [WALLET_SETUP_GUIDE.md](WALLET_SETUP_GUIDE.md), [KING_TOKEN_HANDLING_GUIDE.md](KING_TOKEN_HANDLING_GUIDE.md)

---

## ✅ **Next Actions**

### **For Implementation Team**:
1. Review [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) for current status
2. Start with critical fixes (method alignment)
3. Follow [REQUIREMENTS.md](REQUIREMENTS.md) for task checklist
4. Reference [specs/](specs/) for implementation details

### **For Single Developer**:
- Follow REQUIREMENTS.md sequentially
- Reference component specs as needed
- ~3-5 days for critical fixes + polish

### **For Two Developers**:
- Agent A: Monitoring components + Frontend
- Agent B: Execution components + Deployment  
- See [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) for parallel work strategy

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

**Ready to implement!** 🚀 See [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) to begin.
