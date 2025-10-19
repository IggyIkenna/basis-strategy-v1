# Basis Strategy - DeFi Strategy Platform 🚀

## 💼 **Business Overview**

**Live and backtesting framework for multi-strategy yield generation** through staking, lending, and funding rate arbitrage across web3 and CEX platforms.

### **Product Model**
- **Share Classes**: Clients invest in USDT or ETH share classes
- **Yield Strategies**: Staking rewards + funding rate arbitrage with optional leverage
- **Dynamic Rebalancing**: Maximum capital allocation minus withdrawal buffer
- **Fully Automated**: Complete web UI with monitoring and control

### **Similar To**: Ethena, but enhanced with:
- Multiple share classes (USDT/ETH)
- Dynamic capital rebalancing
- Multiple strategy modes per share class
- Advanced cross-venue optimization

### **Development Phases**
1. **Phase 1** (Current): Major refactor for local deployment and improved architecture
2. **Phase 2**: 100% working, tested, deployed backtesting system for defi and basis trading
3. **Phase 3**: E2E simulation in dev environment with no capital for defi and basis trading
4. **Phase 4**: Integration of ML directional data provider and ML directional strategy manager into the backtesting system
5. **Phase 5**: Integration of ML directional data provider and ML directional strategy manager into the live trading system dev environment with no capital
6. **Phase 6**: E2E simulation in staging with small capital for defi and basis trading
7. **Phase 7**: E2E simulation in staging environment with small capital for ML directional trading
8. **Phase 8**: Live trading with full capital deployment for ML directional trading
9. **Phase 9**: Live trading with full capital deployment for defi and basis trading


### **Quality Standards**
- **80% minimum** unit test coverage per task
- **80% target** unit and integration test coverage overall
- **100% target** e2e test coverage
- **Audit-grade** logging and reconciliation
- **Centralized Testing**: All tests orchestrated through `run_quality_gates.py`
- **Platform Commands**: Dedicated test commands for different areas

---

## 🎯 **Quick Start**

### **Environment Setup**
```bash
# Development environment (default)
./platform.sh dev

# Staging environment
BASIS_ENVIRONMENT=staging ./platform.sh start

# Production environment
BASIS_ENVIRONMENT=prod ./platform.sh start

# Test specific areas
./platform.sh config-test     # Configuration validation
./platform.sh data-test       # Data validation
./platform.sh workflow-test   # Workflow integration
./platform.sh component-test  # Component architecture
./platform.sh e2e-test        # End-to-end testing
```

### **Documentation**
- **[Getting Started](docs/GETTING_STARTED.md)** - Complete setup guide
- **[Test Organization](docs/TEST_ORGANIZATION.md)** - Test structure and platform commands
- **[Quality Gates](docs/QUALITY_GATES.md)** - Implementation priorities and quality gates
- **[Component Specs](docs/specs/)** - Detailed component implementation guides
- **[Documentation Hub](docs/README.md)** - Complete documentation index

---

## 📊 **Current Status**

### **✅ Completed (January 2025)**
- **Core Components**: Position Monitor, Event Logger, Exposure Monitor, Risk Monitor, P&L Calculator
- **Execution Components**: Strategy Manager, VenueManager, VenueInterfaceManager, Data Provider
- **Test Organization**: Consolidated test structure with centralized orchestration
- **Platform Commands**: 6 dedicated test commands for different areas
- **Quality Gates**: Centralized quality gates system with category-based organization

### **🔄 Recent Improvements**
- **Test Consolidation**: Moved 15 orphaned tests to proper directories
- **Platform Commands**: Added config-test, data-test, workflow-test, component-test, e2e-test
- **Centralized Testing**: All tests now run through `run_quality_gates.py`
- **Documentation**: Updated all relevant docs with new test organization

### **📋 Current Focus**
1. **Test Infrastructure**: Fix remaining test execution issues
2. **Strategy Naming**: Update strategy tests to match new naming conventions
3. **Test Coverage**: Work towards 80% coverage target
4. **Integration Testing**: Complete component interaction validation

---

## 🧪 **Testing System**

### **Test Organization (January 2025)**
The test system has been completely restructured for better maintainability:

#### **New Directory Structure**
```
tests/
├── unit/
│   ├── components/          # EventDrivenStrategyEngine components
│   ├── calculators/         # Math and calculation components
│   ├── data/               # Data-related components
│   ├── engines/            # Engine components
│   └── pricing/            # Pricing components
├── integration/            # Integration tests
└── e2e/                   # End-to-end tests
```

#### **Platform Commands**
```bash
# Test specific areas
./platform.sh config-test     # Configuration validation
./platform.sh data-test       # Data validation
./platform.sh workflow-test   # Workflow integration
./platform.sh component-test  # Component architecture
./platform.sh e2e-test        # End-to-end testing

# Run comprehensive tests
./platform.sh test            # All quality gates
```

### **Centralized Orchestration**
All tests are now orchestrated through `run_quality_gates.py`:
- **Single Entry Point**: All quality gates run through one script
- **Category-Based**: Tests organized by functional area
- **Consistent Error Handling**: Uniform error reporting across all tests
- **Maintainable**: Changes to test structure only need updates in one place

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

### **For Developers**
```bash
# Clone and setup
git clone <repository>
cd basis-strategy-v1

# Setup environment
./platform.sh dev

# Run tests
./platform.sh test

# Test specific areas
./platform.sh component-test  # After component changes
./platform.sh config-test     # After config changes
./platform.sh data-test       # After data changes

# Start development
cd frontend && npm run dev
# Backend will be running via platform.sh
```

### **For Agents**
```bash
# Test organization and platform commands (completed)
# Current focus: Fix test infrastructure and strategy naming

# Run quality gates
python scripts/run_quality_gates.py

# Test specific areas
./platform.sh config-test
./platform.sh data-test
./platform.sh component-test
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

### **Test Organization (Updated January 2025)**
- **Unit Tests** - `tests/unit/` - Organized by functional area (components, calculators, data, engines, pricing)
- **Integration Tests** - `tests/integration/` - Component coordination and data flows
- **E2E Tests** - `tests/e2e/` - Full workflow tests
- **Quality Gates** - `scripts/run_quality_gates.py` - Centralized orchestration

### **Run Tests**
```bash
# Platform commands (recommended)
./platform.sh test            # All quality gates
./platform.sh config-test     # Configuration validation
./platform.sh data-test       # Data validation
./platform.sh workflow-test   # Workflow integration
./platform.sh component-test  # Component architecture
./platform.sh e2e-test        # End-to-end testing

# Direct quality gates
python scripts/run_quality_gates.py

# Specific categories
python scripts/run_quality_gates.py --category unit
python scripts/run_quality_gates.py --category integration_data_flows
python scripts/run_quality_gates.py --category e2e_strategies
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

### **Key Metrics (January 2025)**
- **Components**: 9/9 implemented ✅ (core components working)
- **Test Organization**: ✅ Consolidated and organized
- **Platform Commands**: 6/6 test commands implemented ✅
- **Quality Gates**: Centralized system with category-based organization ✅
- **Documentation**: 30+ files, comprehensive coverage
- **Architecture**: Component-based, event-driven
- **Frontend**: 50% complete (wizard components exist, needs integration)

### **Quality Gates**
```bash
# Run all quality gates
python scripts/run_quality_gates.py

# Test specific areas
./platform.sh config-test
./platform.sh data-test
./platform.sh workflow-test
./platform.sh component-test
./platform.sh e2e-test

# List all available categories
python scripts/run_quality_gates.py --list-categories
```

---

## 🤝 **Contributing**

### **Agent Workflow**
1. Read the [Test Organization Guide](docs/TEST_ORGANIZATION.md) for current test structure
2. Follow testing guidelines with 80% coverage minimum
3. Use platform commands for testing: `./platform.sh component-test`
4. Run quality gates: `python scripts/run_quality_gates.py`
5. Update progress and commit with descriptive messages

### **Development Workflow**
1. Create feature branch from main
2. Follow testing guidelines in `docs/TEST_ORGANIZATION.md`
3. Use platform commands for testing specific areas
4. Ensure all tests pass: `./platform.sh test`
5. Submit pull request with clear description

---

## 📞 **Support**

### **Documentation**
- **[Test Organization](docs/TEST_ORGANIZATION.md)** - Test structure and platform commands
- **[Quality Gates](docs/QUALITY_GATES.md)** - Implementation priorities and quality gates
- **[Getting Started](docs/GETTING_STARTED.md)** - Complete setup guide
- **[Architecture Decisions](docs/REFERENCE_ARCHITECTURE_CANONICAL.md)** - Design rationale

### **Agent Support**
- **[Test Organization Guide](docs/TEST_ORGANIZATION.md)** - Current test structure
- **[Quality Gates](docs/QUALITY_GATES.md)** - Quality gates and validation
- **[Component Specs](docs/specs/)** - Detailed component implementation guides

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🎯 **Mission**

Build a production-ready yield generation platform with:
- **Client-Focused**: USDT/ETH share classes 
- **Multi-Strategy**: Staking, lending, funding rate arbitrage with leverage
- **Dynamic Optimization**: Automated capital allocation and rebalancing
- **Common Architecture**: Unified codebase for backtesting and live trading
- **Rigorous Testing**: 80% unit/integration, 100% e2e coverage
- **Audit-Grade**: Complete event logging, reconciliation, compliance
- **Production Ready**: Local and Docker deployment, GCP, monitoring, automated execution

**Strategy**: Ethena-style enhanced with share classes, and advanced rebalancing  
**Current Focus**: Test infrastructure fixes and strategy naming updates  
**Next Steps**: Fix test execution → Achieve 80% coverage → Complete integration testing → Live trading

**Test organization complete! Ready for infrastructure fixes and full implementation!** 🚀