# Target Repository Structure

**Last Updated:** December 19, 2024  
**Purpose:** Reference document for agents completing the 26 cursor tasks to prevent breaking changes  
**Status:** Target state after all architectural refactoring is complete

## Overview

This document defines the target repository structure after all 26 cursor tasks are completed. It serves as a canonical reference to ensure agents don't break existing functionality while implementing new features.

## Backend Structure (`backend/src/basis_strategy_v1/`)

### Core Components (`core/`)

#### Strategies (`core/strategies/`)
```
core/strategies/
├── __init__.py                                    [KEEP]
├── base_strategy_manager.py                       [KEEP] - Abstract base class
├── strategy_factory.py                            [KEEP] - Factory pattern
├── pure_lending_strategy.py                       [KEEP] - Existing implementation
├── btc_basis_strategy.py                          [CREATE] - New strategy
├── eth_basis_strategy.py                          [CREATE] - New strategy
├── eth_staking_only_strategy.py                   [CREATE] - New strategy
├── eth_leveraged_strategy.py                      [CREATE] - New strategy
├── usdt_market_neutral_no_leverage_strategy.py    [CREATE] - New strategy
├── usdt_market_neutral_strategy.py                [CREATE] - New strategy
└── components/                                    [KEEP]
    ├── __init__.py                                [KEEP]
    ├── position_monitor.py                        [KEEP] - Mode-agnostic
    ├── risk_monitor.py                            [KEEP] - Fail-fast config
    ├── exposure_monitor.py                        [KEEP] - Mode-agnostic
    ├── strategy_manager.py                        [KEEP] - Synchronous
    ├── position_update_handler.py                 [KEEP] - Synchronous
    └── execution_manager.py                       [KEEP] - Synchronous
```

#### Execution (`core/execution/`)
```
core/execution/
├── __init__.py                                    [KEEP]
├── execution_manager.py                           [KEEP] - Fixed syntax
└── wallet_transfer_executor.py                    [KEEP]
```

#### Reconciliation (`core/reconciliation/`)
```
core/reconciliation/
├── __init__.py                                    [CREATE]
└── reconciliation_component.py                    [CREATE] - New component
```

#### Math (`core/math/`)
```
core/math/
├── __init__.py                                    [KEEP]
├── pnl_calculator.py                              [KEEP] - Mode-agnostic
├── yield_calculator.py                            [KEEP]
├── risk_calculator.py                             [KEEP]
└── ... (other math utilities)                     [KEEP]
```

#### Utilities (`core/utilities/`)
```
core/utilities/
├── __init__.py                                    [KEEP]
└── utility_manager.py                             [KEEP] - Centralized utilities
```

#### Event Engine (`core/event_engine/`)
```
core/event_engine/
├── __init__.py                                    [KEEP]
└── event_driven_strategy_engine.py                [MODIFY] - Add singleton pattern
```

#### Services (`core/services/`)
```
core/services/
├── __init__.py                                    [KEEP]
├── backtest_service.py                            [KEEP] - Fixed imports
└── live_service.py                                [KEEP] - Fixed imports
```

#### Interfaces (`core/interfaces/`)
```
core/interfaces/
├── __init__.py                                    [KEEP]
├── base_execution_interface.py                    [KEEP]
├── cex_execution_interface.py                     [KEEP]
├── onchain_execution_interface.py                 [KEEP]
├── transfer_execution_interface.py                [KEEP]
└── execution_interface_factory.py                 [KEEP]
```

### Infrastructure (`infrastructure/`)

#### Config (`infrastructure/config/`)
```
infrastructure/config/
├── __init__.py                                    [KEEP]
├── config_manager.py                              [KEEP] - Single source of truth
├── config_validator.py                            [KEEP]
└── models.py                                      [KEEP] - Consolidated models
```

#### Data (`infrastructure/data/`)
```
infrastructure/data/
├── __init__.py                                    [KEEP]
├── historical_data_provider.py                    [KEEP] - Synchronous
├── live_data_provider.py                          [KEEP] - Async for I/O only
└── ... (other data providers)                     [KEEP]
```

### API (`api/`)

#### Routes (`api/routes/`)
```
api/routes/
├── __init__.py                                    [KEEP]
├── backtest.py                                    [KEEP] - Uses new strategy factory
├── live_trading.py                                [KEEP] - Uses new strategy factory
├── strategies.py                                  [KEEP] - Fixed imports
└── health.py                                      [KEEP]
```

## Deleted Files (DO NOT RECREATE)

### Core Config (Deleted - Use infrastructure/config instead)
```
❌ core/config/                                    [DELETED]
    ├── __init__.py
    ├── config_models.py
    └── models.py
```

### Rebalancing (Deleted - Use strategies/components instead)
```
❌ core/rebalancing/                               [DELETED]
    ├── risk_monitor.py                            [DELETED - duplicate]
    └── transfer_manager.py                        [DELETED - architectural violation]
```

### Duplicate Components (Deleted - Use centralized versions)
```
❌ core/strategies/components/                     [DELETED - 13 files]
    ├── api_interface.py
    ├── data_provider.py
    ├── event_manager.py
    ├── execution_engine.py
    ├── execution_interface.py
    ├── health_monitor.py
    ├── logging_interface.py
    ├── metrics_collector.py
    ├── monitoring_manager.py
    ├── performance_monitor.py
    ├── pnl_monitor.py
    ├── results_aggregator.py
    ├── results_store.py
    └── strategy_engine.py
```

## Key Architectural Principles

### 1. Single Source of Truth
- **Config:** Use `infrastructure/config/` only
- **Risk Monitor:** Use `core/strategies/components/risk_monitor.py` only
- **Utilities:** Use `core/utilities/utility_manager.py` only

### 2. Mode-Agnostic Components
- All components work in both backtest and live modes
- No mode-specific if statements in core components
- Use config parameters instead of hardcoded mode checks

### 3. Synchronous Internal Methods
- Remove `async/await` from internal component methods
- Keep `async` only for API entry points and I/O operations
- Event Logger and Results Storage can remain async

### 4. Fail-Fast Configuration
- Use direct config access instead of `.get()` with defaults
- Fail immediately on missing required config values
- No silent fallbacks to default values

### 5. Strategy Factory Pattern
- All 7 strategies registered in `StrategyFactory.STRATEGY_MAP`
- Use factory to create strategy instances
- Standardized 5 actions: `entry_full`, `entry_partial`, `exit_full`, `exit_partial`, `sell_dust`

## Import Patterns

### Correct Imports (Use These)
```python
# Config
from ...infrastructure.config.config_manager import get_config_manager
from ...infrastructure.config.models import ConfigSchema

# Strategies
from ..strategies.strategy_factory import StrategyFactory
from ..strategies.components.risk_monitor import RiskMonitor

# Services
from ..services.backtest_service import BacktestService
from ..services.live_service import LiveTradingService

# Reconciliation
from ..reconciliation.reconciliation_component import ReconciliationComponent
```

### Incorrect Imports (DO NOT USE)
```python
# ❌ DON'T USE - These are deleted
from ..config import load_and_validate_config
from ..rebalancing.risk_monitor import RiskMonitor
from ..strategies.components.pnl_monitor import PnLMonitor
```

## Component Dependencies

### Core Component Hierarchy
```
EventDrivenStrategyEngine (Singleton)
├── StrategyFactory
│   ├── PureLendingStrategy
│   ├── BTCBasisStrategy
│   ├── ETHBasisStrategy
│   ├── ETHStakingOnlyStrategy
│   ├── ETHLeveragedStrategy
│   ├── USDTMarketNeutralNoLeverageStrategy
│   └── USDTMarketNeutralStrategy
├── PositionMonitor
├── RiskMonitor
├── ExposureMonitor
├── PnLCalculator
├── UtilityManager
├── ExecutionManager
├── PositionUpdateHandler
└── ReconciliationComponent
```

### Service Layer
```
API Routes
├── BacktestService
│   ├── EventDrivenStrategyEngine
│   ├── DataProvider
│   └── StrategyFactory
└── LiveTradingService
    ├── EventDrivenStrategyEngine
    ├── DataProvider
    └── StrategyFactory
```

## Testing Structure

### Unit Tests (`tests/unit/`)
```
tests/unit/
├── components/
│   ├── test_position_monitor.py                   [KEEP]
│   ├── test_risk_monitor.py                       [KEEP]
│   ├── test_exposure_monitor.py                   [KEEP]
│   └── test_reconciliation_component.py           [CREATE]
├── strategies/
│   ├── test_strategy_factory.py                   [CREATE]
│   ├── test_btc_basis_strategy.py                 [CREATE]
│   ├── test_eth_basis_strategy.py                 [CREATE]
│   └── ... (other strategy tests)                 [CREATE]
├── services/
│   ├── test_backtest_service.py                   [KEEP]
│   └── test_live_service.py                       [KEEP]
└── ... (other test categories)                    [KEEP]
```

## Quality Gates

### Expected Quality Gate Status
- **Strategy Validation:** 2/2 passing (after strategy implementations)
- **Component Validation:** 5/5 passing (after architectural fixes)
- **Configuration Validation:** 2/2 passing (after config consolidation)
- **Integration Validation:** 2/2 passing (after service updates)

### Quality Gate Scripts
```
scripts/
├── test_pure_lending_quality_gates.py             [KEEP]
├── test_btc_basis_quality_gates.py                [KEEP]
├── test_eth_basis_quality_gates.py                [KEEP]
├── test_strategy_manager_refactor_quality_gates.py [KEEP]
├── test_tight_loop_architecture_quality_gates.py  [KEEP]
└── ... (other quality gate scripts)               [KEEP]
```

## Critical Warnings

### ⚠️ DO NOT:
1. **Recreate deleted files** - They were removed for architectural reasons
2. **Add async to internal methods** - Keep components synchronous
3. **Use old config imports** - Use infrastructure/config only
4. **Create duplicate components** - Use centralized versions
5. **Break the strategy factory pattern** - All strategies must be registered

### ✅ DO:
1. **Use the strategy factory** - For all strategy creation
2. **Follow mode-agnostic patterns** - No hardcoded mode checks
3. **Use fail-fast configuration** - Direct config access
4. **Maintain singleton pattern** - For event engine
5. **Update quality gates** - To match new architecture

## File Status Legend

- `[KEEP]` - File exists and should remain unchanged
- `[MODIFY]` - File exists but needs updates
- `[CREATE]` - File needs to be created
- `[DELETE]` - File should be deleted (already done)
- `[RELOCATE]` - File should be moved to new location

## Validation Checklist

Before completing any task, verify:
- [ ] All imports use correct paths (infrastructure/config, not core/config)
- [ ] No deleted files are being recreated
- [ ] Strategy factory includes all 7 strategies
- [ ] Components are mode-agnostic
- [ ] No async in internal methods
- [ ] Fail-fast configuration is used
- [ ] Quality gates are updated to match new architecture

---

**Note:** This document should be referenced before making any changes to ensure architectural consistency and prevent breaking existing functionality.


