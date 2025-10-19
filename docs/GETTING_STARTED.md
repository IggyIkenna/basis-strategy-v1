# Getting Started - Complete Setup Guide 🚀

**Get the platform running and test your first strategy in under 10 minutes**  
**Updated**: January 15, 2025 - Test organization consolidated and platform.sh commands added  
**Last Reviewed**: January 15, 2025  
**Status**: ✅ Aligned with canonical architectural principles

---

## 📚 **Canonical Sources**

**This guide aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Design Decisions**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Core design decisions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

---

## Architecture Overview

The platform uses a **config-driven, mode-agnostic architecture**:

### Component Organization
- **11 Core Components**: Runtime execution (Position/Exposure/Risk/PnL monitors, Strategy/Execution managers, etc.)
- **9 Supporting Components**: Services, utilities, infrastructure
- See: COMPONENT_SPECS_INDEX.md for complete list

### Configuration System
Each strategy mode is defined in YAML:
- `data_requirements`: What data the mode needs
- `component_config`: How each component behaves for this mode
- See: 19_CONFIGURATION.md for complete schemas

### Key Architectural Patterns
- **Reference-Based**: Components store references at init, never pass as params (ADR-003)
- **Shared Clock**: EventDrivenStrategyEngine owns timestamp (ADR-004)
- **Request Isolation**: Fresh instances per request (ADR-005)
- **Config-Driven**: Components use config, not mode checks (ADR-052)

See: REFERENCE_ARCHITECTURE_CANONICAL.md for complete architectural principles.

---

## ⚡ **Prerequisites** (Required before starting)

- **Python 3.8+**: Backend requirements
- **Node.js 16+**: Frontend requirements

**Note**: For backtest mode, no venue credentials (API keys) are required - execution is simulated.

## 🔧 **Environment Configuration**

The platform supports multiple environments with different configurations:

### **Environment Files**
- **`.env.dev`** - Development environment (5s health checks)
- **`.env.staging`** - Staging environment (35s health checks)  
- **`.env.production`** - Production environment (configurable)

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

**Environment files contain**: Health check intervals, API ports, data sources, and other deployment-specific settings.

---

## 🎯 **What We're Building**

A **live and backtesting framework** for multi-strategy yield generation with:
- 7 strategy modes (pure lending, BTC basis, ETH basis, ETH staking, ETH leveraged, USDT market-neutral variants)
- Share classes (USDT stable, ETH directional)
- Fully automated with web UI

### **7 Strategy Modes**

**1. Pure USDT Lending** (Simplest)
- Supply USDT to AAVE → Earn interest
- No staking, no leverage, no hedging
- ~4-6% APR

**2. BTC Basis Trading** (Market-Neutral)
- Buy BTC spot + Short BTC perp
- Earn funding rates
- ~5-10% APR

**3. ETH Basis Trading** (Directional)
- Buy ETH spot + Short ETH perp
- Earn funding rates
- ETH share class (directional exposure)
- ~5-10% APR

**4. ETH Staking Only** (Directional)
- Stake ETH (wstETH or weETH)
- No leverage, no hedging
- ETH share class (directional exposure)
- ~3-5% APR

**5. ETH Leveraged Staking** (Directional)
- Stake ETH (wstETH or weETH)
- Leveraged staking on AAVE
- ETH share class (directional exposure)
- ~6-15% APR

**6. USDT Market-Neutral No Leverage** (Market-Neutral)
- Buy ETH + Stake + Hedge with perps
- No leverage on staking side
- USDT share class (market-neutral)
- ~6-10% APR

**7. USDT Market-Neutral** (Most Complex)
- Buy ETH + Stake + Leverage + Hedge with perps
- Full leveraged staking position
- Multi-venue tracking
- USDT share class (market-neutral)
- ~8-15% APR

---

## ✅ **Current System Status**

**Backend**: ✅ **Core Components Implemented** | 🔄 **Environment Setup Issues**
- All API endpoints working
- Backtest system executing end-to-end
- 6 strategies available (pure_lending, eth_leveraged, etc.)
- All data loading successfully
- 17% test coverage with 43 passing tests
- **CRITICAL**: Backend server health checks failing (environment setup issue)
- **CRITICAL**: Pure lending shows 1166% APY (should be 3-8%)

**Frontend**: 🔧 **Backend Integration Complete**
- API integration working
- Some UI components need completion

**Production Ready**: ❌ **NOT READY** - Critical yield calculation issue

## ⚠️ **Known Issues**

**CRITICAL**: This system is **NOT production ready**. Core components are implemented but critical issues remain:

- **Pure Lending**: Yield calculation shows 1166% APY (should be 3-8%)
- **Quality Gates**: Only 5/14 scripts passing (target: 70%+)
- **BTC Basis**: 8/10 quality gates passing (80%)
- **Overall Status**: In development - not ready for production use

**See**: [docs/QUALITY_GATES.md](QUALITY_GATES.md) for complete issue list and resolution status.

---

## 🚀 **1. Start the Platform** (2 min)

### **Option A: Non-Docker (Local Development)**
```bash
# From project root
./platform.sh start        # Backend + Frontend (uses env file BASIS_EXECUTION_MODE to decide backtest or live)
./platform.sh dev          # Backend only (dev mode, uses env.dev overrides)
./platform.sh stop         # Stop all services
```

**Backend-Only Development Options**:
```bash
# Dev mode (backend only, uses env.dev overrides)
./platform.sh dev

# Backend only with environment variables
SKIP_FRONTEND=true ./platform.sh start

# Skip quality gates for rapid development
SKIP_QUALITY_GATES=true ./platform.sh dev

# Both options combined
SKIP_FRONTEND=true SKIP_QUALITY_GATES=true ./platform.sh start
```

**Execution Mode Behavior**:
- **`./platform.sh start`**: Uses `BASIS_EXECUTION_MODE` from environment files
- **`./platform.sh dev`**: **Always uses dev mode** with env.dev overrides
- **Default env files**: `dev` and `staging` = backtest, `production` = live

### **Option B: Docker (All Environments)**
```bash
# From project root
cd docker && ./deploy.sh local all start    # Full stack
cd docker && ./deploy.sh local backend start # Backend only
```

**What starts**:
- ✅ Backend API (port 8001) - **CORE COMPONENTS WORKING**
- 🔧 Frontend UI (port 5173) - Backend integration working (only with `./platform.sh start`)

**Access**:
- Frontend: http://localhost:5173 (only with `./platform.sh start`)
- API Docs: http://localhost:8001/docs
- Health: http://localhost:8001/health
- Detailed Health: http://localhost:8001/health/detailed
- Strategies: http://localhost:8001/api/v1/strategies/

**Backend-Only Access** (with `./platform.sh dev`):
- API Docs: http://localhost:8001/docs
- Health: http://localhost:8001/health
- Detailed Health: http://localhost:8001/health/detailed
- Strategies: http://localhost:8001/api/v1/strategies/

---

## 🎯 **2. Run Your First Backtest** (3 min)

### **Via API** (Currently Working):

```bash
# Test the API directly
curl -X POST "http://localhost:8001/api/v1/backtest/" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "pure_lending",
    "share_class": "USDT",
    "initial_capital": 100000,
    "start_date": "2024-05-12T00:00:00Z",
    "end_date": "2024-09-10T23:59:59Z"
  }'
```

### **Via UI** (When Frontend Complete):

1. **Open** http://localhost:5173
2. **Choose Share Class**: Select "USDT (Stable)"
3. **Choose Strategy**: Click "USDT Pure Lending" (simplest!)
4. **Configure**:
   - Initial Capital: $100,000
   - Period: 2024-05-12 to 2024-09-10
5. **Review**: Check summary, see estimated APY (4-6%)
6. **Submit**: Click "Run Backtest"

**Result**: Backtest runs (~30 seconds)

---

## 📊 **3. View Results** (2 min)

### **Summary**:
- Total P&L: $4,523
- APY: 5.2%
- Reconciliation: ✅ Passed ($2.15 diff)

### **Charts** (Interactive Plotly):
- Cumulative P&L over time
- Interest rate evolution
- Drawdown chart

### **Event Log**:
- Filter by type, venue, date
- Expand rows to see balance snapshots
- Download filtered events to CSV

### **Download**:
- Click "Download Results"
- Gets: hourly_pnl.csv, event_log.csv, plots (HTML)

---

## 🎨 **4. Try Different Modes** (3 min each)

### **BTC Basis Trading**:
```
Share Class: USDT
Mode: BTC Basis Trading
Expected: 5-10% APY from funding rates
```

### **ETH Leveraged Staking**:
```
Share Class: ETH
Mode: ETH Leveraged Staking
Expected: 6-12% APY from leveraged staking
```

### **USDT Market-Neutral** (Most Complex):
```
Share Class: USDT
Mode: USDT Market-Neutral
LST: weETH
Flash Loan: Yes
Expected: 8-15% APY
```

---

## 🔧 **Troubleshooting**

**"Data not found"**:
```bash
# Download data
python scripts/orchestrators/download_all.py --quick-test
```

**"Component initialization failed"**:
```bash
# Check logs
docker compose logs -f backend

# Check health
curl http://localhost:8001/health
curl http://localhost:8001/health/detailed
```

---

## 🏗️ **Key Architectural Decisions**

**For complete details**: See **[REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md)** (canonical source)

### **1. Component-Based Architecture** ✅

**9 Core Components**:
- **Monitoring**: Position Monitor, Exposure Monitor, Risk Monitor, P&L Calculator
- **Orchestration**: Strategy Manager
- **Execution**: CEX Manager, OnChain Manager
- **Infrastructure**: Event Logger, Data Provider

**Sync Update Chain**:
```
**DEPRECATED**: The monitoring cascade (position → exposure → risk → pnl) is no longer automatic.
**NEW ARCHITECTURE**: See ADR-001 in REFERENCE_ARCHITECTURE_CANONICAL.md for current tight loop definition.

**Current Tight Loop**: execution → position_monitor → reconciliation → next instruction
```

**See**: [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) for component details

### **2. Wallet Model** ✅

**On-Chain** (Single Ethereum wallet):
```python
wallet = {
    'ETH': float,                    # Native ETH for gas
    'aWeETH': float,                 # AAVE aToken (CONSTANT scaled balance)
    'variableDebtWETH': float        # AAVE debt token (CONSTANT scaled balance)
}
```

**CRITICAL**: AAVE aToken amounts are **NOT 1:1** with supplied tokens!
- Supply 100 weETH when index=1.05 → Receive 95.24 aWeETH
- **See [specs/02_EXPOSURE_MONITOR.md](specs/02_EXPOSURE_MONITOR.md)** (lines 27-107) for complete AAVE index mechanics

**Off-Chain** (Separate CEX accounts):
```python
cex_accounts = {
    'binance': {'USDT': float, 'ETH_spot': float, 'perp_positions': {...}},
    'bybit': {...},    # Separate account
    'okx': {...}       # Separate account
}
```

### **3. Timing Model** ⏰

**Hourly Price Updates Only**:
- All market data on the hour (minute=0, second=0, UTC)
- All prices from same hourly snapshot
- No intra-hour data

**Atomic Event Execution**:
- Multiple events share same timestamp
- Differentiated by global order (1, 2, 3...)
- All use same price snapshot (no timing risk)

### **4. Share Class Behavior** ✅

**ETH Share Class**:
- P&L in ETH
- Never hedges (directional ETH exposure)
- Initial capital in ETH (e.g., 100 ETH)

**USDT Share Class**:
- P&L in USD
- Always hedges (market-neutral)
- Initial capital in USD (e.g., $100,000)
- Gas debt tracked (wallet.ETH can go negative)

---

## 🔑 **Critical Implementation Notes**

### **AAVE Index Mechanics** 🔢
**CRITICAL**: aToken amounts are **NOT 1:1** with supplied tokens!

**Quick Summary**:
- Wallet holds `aWeETH` (constant scaled balance)
- Underlying grows via: `underlying = aWeETH × liquidityIndex`
- Index determines conversion at supply time

**Example**: Supply 100 weETH when index=1.05 → Receive 95.24 aWeETH

**For complete details**: See **[specs/02_EXPOSURE_MONITOR.md](specs/02_EXPOSURE_MONITOR.md)** (lines 27-107)

### **Position Naming Convention** 🏦
```python
# Wallet tokens (what you actually hold)
wallet.aWeETH               # CONSTANT scaled balance
wallet.variableDebtWETH     # CONSTANT scaled balance

# AAVE positions (derived via index)
aave_weeth_supply_native    # aWeETH × liquidityIndex
aave_weeth_supply_eth       # × oracle price
aave_weeth_supply_usd       # × ETH price
```

### **Leverage Execution** ✅
- **Atomic Flash Only**: 1 transaction, 6-7 events, ~$50 gas
- **No Sequential**: Sequential execution deprecated (was 23 iterations, 70+ events, ~$200 gas)
- **Deterministic**: Based on target LTV, no iteration limits needed

### **Per-Exchange Tracking** 📊
**CRITICAL**: Each CEX has different prices!
- Binance perp price ≠ Bybit perp price ≠ OKX perp price
- Track positions separately per exchange
- Use venue-specific mark prices

---

## 📁 **Data Requirements**

**For complete data file structure**: See **[specs/09_DATA_PROVIDER.md](specs/09_DATA_PROVIDER.md)** (lines 156-216)

**Quick Summary - Required data**:
- ETH/USDT spot prices (Binance)
- AAVE rates (weETH, wstETH, WETH, USDT)
- AAVE oracles (weETH/ETH, wstETH/ETH)
- CEX futures (per exchange: Binance, Bybit, OKX)
- Funding rates (per exchange)
- Gas costs (Ethereum gas prices)
- Execution costs (slippage model)
- Staking rewards (base + seasonal)

**All data must be**:
- Hourly aligned (minute=0, second=0)
- UTC timezone
- Validated at startup

---

## 🧪 **Testing Requirements**

**Mandatory**:
- **80% minimum** unit test coverage per task
- **80% target** overall unit/integration coverage
- **100% target** e2e coverage

### **Test Commands (NEW)**
The platform now includes dedicated test commands for different areas:

```bash
# Test specific areas
./platform.sh config-test     # Configuration validation only
./platform.sh data-test       # Data validation only  
./platform.sh workflow-test   # Workflow integration only
./platform.sh component-test  # Component architecture only
./platform.sh e2e-test        # End-to-end testing only

# Run comprehensive tests
./platform.sh test            # All quality gates
```

### **Test Infrastructure**
- **Centralized Orchestration**: All tests run through `scripts/run_quality_gates.py`
- **Organized Structure**: Tests grouped by functional area in `tests/`
  - `tests/unit/components/` - EventDrivenStrategyEngine components
  - `tests/unit/calculators/` - Math and calculation components
  - `tests/unit/data/` - Data-related components
  - `tests/unit/engines/` - Engine components
  - `tests/unit/pricing/` - Pricing components
  - `tests/integration/` - Integration tests
  - `tests/e2e/` - End-to-end tests

**See**: [tests/README.md](../tests/README.md) for testing guidelines

---

## 🎯 **Next Steps**

**Learn More**:
- **USER_GUIDE.md** - Complete user manual
- **COMPONENT_SPECS_INDEX.md** - Component overview
- **specs/19_CONFIGURATION.md** - Configuration management
- **API_REFERENCE.md** - Complete API documentation

**Advanced**:
- Configure complex strategies (leverage, hedging)
- Understand P&L reconciliation
- Deploy to production (GCloud VM)

---

## 📚 **Documentation Structure**

**Quick Reference**:
- **Architecture** → [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) (canonical)
- **Components** → [specs/](specs/) <!-- Directory link to specs folder --> (implementation details)
- **Implementation** → [README.md](README.md) <!-- Redirected from IMPLEMENTATION_ROADMAP.md - implementation status is documented here -->
- **Tasks** → [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) <!-- Redirected from REQUIREMENTS.md - requirements are component specifications -->
- **Configuration** → [specs/19_CONFIGURATION.md](specs/19_CONFIGURATION.md)
- **API/Events** → [API_DOCUMENTATION.md](API_DOCUMENTATION.md) <!-- Redirected from REFERENCE.md - reference documentation is API docs -->

**See**: [INDEX.md](INDEX.md) for complete navigation

---

**Status**: Getting started complete! You should have your first backtest results! ✅

*Last Updated: January 15, 2025*
