# Basis Strategy - DeFi Strategy Platform 🚀

## 💼 **Business Overview**

**Live and backtesting framework for multi-strategy yield generation** through staking, lending, and funding rate arbitrage across web3 and CEX platforms.

### **Product Model**
- **Share Classes**: Clients invest in USDT or ETH share classes
- **Yield Strategies**: Staking rewards + funding rate arbitrage with optional leverage
- **Dynamic Rebalancing**: Maximum capital allocation minus withdrawal buffer
- **Fast Withdrawals**: Buffer management for rapid client redemptions
- **Fully Automated**: Complete web UI with monitoring and control

### **Similar To**: Ethena, but enhanced with:
- Multiple share classes (USDT/ETH)
- Fast withdrawal capability
- Dynamic capital rebalancing
- Multiple strategy modes per share class
- Advanced cross-venue optimization

### **Development Phases**
1. **Phase 1** (Current): Major refactor for local deployment and improved architecture
2. **Phase 2**: 100% working, tested, deployed backtesting system
3. **Phase 3**: E2E simulation in staging with small capital
4. **Phase 4**: Live trading with full capital deployment

### **Quality Standards**
- **80% minimum** unit test coverage per task
- **80% target** unit and integration test coverage overall
- **100% target** e2e test coverage
- **Audit-grade** logging and reconciliation

---

## 🎯 **Quick Start**

### **Environment Setup**
```bash
# Development environment (default)
./platform.sh backtest

# Staging environment
BASIS_ENVIRONMENT=staging ./platform.sh backtest

# Production environment
BASIS_ENVIRONMENT=prod ./platform.sh backtest
```

### **Documentation**
- **[Getting Started](docs/GETTING_STARTED.md)** - Complete setup guide
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Environment and deployment management
- **[Environment Variables](docs/ENVIRONMENT_VARIABLES.md)** - Configuration reference
- **[Quality Gates](docs/QUALITY_GATES.md)** - Implementation priorities and quality gates
- **[Component Specs](docs/specs/)** - Detailed component implementation guides
- **[Documentation Hub](docs/README.md)** - Complete documentation index

---

## 📊 **Current Status**

### **✅ Completed (9/18 tasks)**
- **Core Components**: Position Monitor, Event Logger, Exposure Monitor, Risk Monitor, P&L Calculator
- **Execution Components**: Strategy Manager, CEX Execution Manager, OnChain Execution Manager, Data Provider

### **🔄 Major Refactor In Progress**
- **Configuration System**: Implementing unified config manager with fail-fast environment loading
- **Data Provider**: Removing minimal data creation, implementing comprehensive startup data loading
- **API Layer**: Adding structured logging, health checks, and synchronous backtest execution
- **Platform Scripts**: Updating for local deployment without Docker while maintaining Docker compatibility

### **📋 Refactor Phases**
1. **Phase 1**: Environment and Configuration (In Progress)
2. **Phase 2**: Data Provider Updates (Pending)
3. **Phase 3**: Component Updates (Pending)
4. **Phase 4**: API and Platform (Pending)
5. **Phase 5**: Documentation and Cleanup (Pending)

**Total Remaining Work**: 5-7 days for refactor completion

---

## 🔄 **Current Refactor**

### **Why We're Refactoring**
The current system has some architectural issues that need to be addressed before moving to production:
- **Configuration Management**: Too many config files with overlapping responsibilities
- **Data Loading**: Minimal data creation instead of comprehensive data loading
- **Error Handling**: Inconsistent error handling and logging
- **Local Deployment**: Requires Docker, no local development option
- **Component Initialization**: No proper dependency tracking or health checking

### **Refactor Goals**
- ✅ **Fail-Fast Configuration**: No defaults, clear error messages pointing to actual locations
- ✅ **Comprehensive Data Loading**: Load ALL data at startup, validate for all modes
- ✅ **Structured Logging**: Error codes, stack traces, component health tracking
- ✅ **Local Deployment**: `./platform.sh start` without Docker
- ✅ **Clean Architecture**: Single responsibility, no duplicates, no backward compatibility

### **Refactor Phases**
1. **Environment & Configuration** - Unified config manager, fail-fast env loading
2. **Data Provider Updates** - Remove minimal data, implement comprehensive loading
3. **Component Updates** - Proper dependency tracking, health checking
4. **API & Platform** - Structured logging, local deployment scripts
5. **Documentation & Cleanup** - Update docs, remove deprecated files

### **Quality Gates**
Each phase must pass specific quality gates before proceeding:
```bash
# Check current phase
python scripts/run_quality_gates.py --phase 1

# Check all phases
python scripts/run_quality_gates.py --all --strict
```

---

## 🏗️ **Architecture**

### **Component-Based Service Architecture**
- **9 Core Components** - Modular, testable, maintainable
- **6 Strategy Modes** - Pure lending, BTC basis, ETH leveraged, ETH staking only, USDT market neutral, USDT market neutral no leverage
- **Real-time Processing** - Direct function calls, event-driven updates
- **Audit-Grade Logging** - Complete event trail and reconciliation
- **Common Architecture** - Shared codebase for backtest and live modes
- **Mode-Specific Execution** - Backtest uses simulations, live uses real APIs

### **Technology Stack**
- **Backend**: Python, FastAPI, Pandas
- **Frontend**: React, TypeScript, Tailwind CSS, Plotly
- **Infrastructure**: Docker, Google Cloud Platform
- **Testing**: pytest, comprehensive test coverage

---

## 🚀 **Getting Started**

### **For Developers (After Refactor)**
```bash
# Clone and setup
git clone <repository>
cd basis-strategy-v1
git checkout agent-implementation

# Setup environment (after refactor)
./platform.sh start

# Run tests
pytest

# Start development
cd frontend && npm run dev
# Backend will be running via platform.sh
```

### **For Agents (Current Refactor)**
```bash
# Phase 1: Environment and Configuration
cursor --agent-task config_manager_implementation

# Phase 2: Data Provider Updates
cursor --agent-task data_provider_refactor

# Phase 3: Component Updates
cursor --agent-task component_updates

# Phase 4: API and Platform
cursor --agent-task api_platform_updates

# Phase 5: Documentation and Cleanup
cursor --agent-task documentation_cleanup

# Check progress
python scripts/run_quality_gates.py --phase 1
```

---

## 📚 **Documentation**

### **Architecture & Design**
- **[Start Here](docs/START_HERE.md)** - Project overview and goals
- **[Architecture](docs/ARCHITECTURE.md)** - System design and patterns
- **[Component Specs](docs/specs/)** - Detailed component specifications
- **[Architectural Decisions](docs/REFERENCE_ARCHITECTURE_CANONICAL.md)** - 38 key design decisions

### **Implementation Guides**
- **[Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md)** - 4-week development plan
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment
- **[Testing Guide](docs/TESTING_GUIDE.md)** - Comprehensive testing strategy
- **[Development Guide](docs/DEVELOPMENT_GUIDE.md)** - Developer workflow

### **Reference Documentation**
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Config Reference](docs/CONFIG_REFERENCE.md)** - Configuration parameters
- **[User Guide](docs/USER_GUIDE.md)** - End-user documentation

---

## 🧪 **Testing**

### **Test Organization**
- **Unit Tests** - `tests/unit/` - Component-level tests
- **Integration Tests** - `tests/integration/` - Component coordination
- **E2E Tests** - `tests/e2e/` - Full workflow tests

### **Run Tests**
```bash
# All tests
pytest

# By category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# With coverage
pytest --cov=backend/src tests/
```

---

## 🚀 **Deployment**

### **Local Development (After Refactor)**
```bash
# Start all services (no Docker required)
./platform.sh start

# Health check
curl http://localhost:8001/health/

# Stop services
./platform.sh stop

# Restart services
./platform.sh restart
```

### **Docker Development (Still Supported)**
```bash
# Start all services with Docker
docker-compose -f deploy/docker-compose.yml up -d

# Health check
curl http://localhost:8001/health/
```

### **Production Deployment**
```bash
# Deploy to Google Cloud
./deploy/deploy-prod.sh

# Monitor deployment
./deploy/health_check_comprehensive.sh
```

---

## 📈 **Progress Tracking**

### **Real-time Status**
- **[Refactor Plan](REFACTOR_PLAN.md)** - Comprehensive refactor implementation plan
- **[Progress JSON](agent-progress.json)** - Machine-readable progress
- **[Quality Gates](docs/QUALITY_GATES.md)** - Implementation priorities and quality gates
- **[Component Specs](docs/specs/)** - Detailed component implementation guides

### **Key Metrics**
- **Components**: 9/9 implemented ✅ (all tests passing)
- **Refactor Phases**: 1/5 in progress (Environment and Configuration)
- **Tests**: 9/9 component tests passing, integration tests need async fixes
- **Documentation**: 29 files, 6,000+ lines
- **Architecture**: Component-based, event-driven (being enhanced)
- **Frontend**: 50% complete (wizard components exist, needs integration)

### **Quality Gates**
```bash
# Check current phase progress
python scripts/run_quality_gates.py --phase 1

# Check all phases
python scripts/run_quality_gates.py --all

# Check specific phase range
python scripts/run_quality_gates.py --phase-range 1-3
```

---

## 🤝 **Contributing**

### **Agent Workflow (Refactor)**
1. Read the [Refactor Plan](REFACTOR_PLAN.md) for current phase
2. Follow strict implementation requirements (no fallbacks, fail-fast)
3. Search existing codebase before implementing (no assumptions)
4. Implement with comprehensive tests (80% coverage minimum)
5. Run quality gates for current phase: `python scripts/run_quality_gates.py --phase X`
6. Update progress and commit with descriptive messages

### **Development Workflow**
1. Create feature branch from `agent-implementation`
2. Follow testing guidelines in `docs/TESTING_GUIDE.md`
3. Ensure all tests pass
4. Submit pull request with clear description

---

## 📞 **Support**

### **Documentation**
- **[FAQ](docs/FAQ.md)** - Frequently asked questions
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Architecture Decisions](docs/REFERENCE_ARCHITECTURE_CANONICAL.md)** - Design rationale

### **Agent Support**
- **[Agent Setup](AGENT_SETUP.md)** - Environment configuration
- **[Progress Monitoring](check_agent_progress.sh)** - Status checking
- **[Validation](validate_completion.py)** - Task completion validation

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🎯 **Mission**

Build a production-ready yield generation platform with:
- **Client-Focused**: USDT/ETH share classes with fast withdrawals
- **Multi-Strategy**: Staking, lending, funding rate arbitrage with leverage
- **Dynamic Optimization**: Automated capital allocation and rebalancing
- **Common Architecture**: Unified codebase for backtesting and live trading
- **Rigorous Testing**: 80% unit/integration, 100% e2e coverage
- **Audit-Grade**: Complete event logging, reconciliation, compliance
- **Production Ready**: Local and Docker deployment, GCP, monitoring, automated execution

**Strategy**: Ethena-style enhanced with share classes, fast withdrawals, and advanced rebalancing  
**Current Focus**: Major refactor for improved architecture and local deployment  
**Next Steps**: Complete refactor → 100% working backtesting system → Staging simulation → Live trading

**Ready for refactor completion and end-to-end implementation!** 🚀