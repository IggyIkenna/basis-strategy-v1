# PROJECT CONTEXT GUIDE FOR BACKGROUND AGENTS

## REPOSITORY STRUCTURE
This is a DeFi yield optimization platform with multiple trading strategies focused on yield generation through staking and funding rates with optional leverage.

## KEY DIRECTORIES
- **docs/**: 42 markdown files with comprehensive documentation
- **docs/specs/**: 13 component specifications (01_POSITION_MONITOR.md through 13_ADVANCED_REBALANCING.md)
- **backend/**: 79 Python files with core strategy implementation
- **frontend/**: React/TypeScript web interface
- **scripts/**: 14 quality gate and testing scripts
- **configs/**: YAML configuration files
- **data/**: Historical market data
- **results/**: Backtest results and analysis

## CRITICAL DOCUMENTATION FILES
- **docs/REMAINING_TASKS.md**: Current task priorities and status
- **docs/QUALITY_GATES.md**: Quality gate standards and requirements
- **docs/QUALITY_GATES_SUMMARY.md**: Current quality gate status
- **docs/ARCHITECTURAL_DECISIONS.md**: System architecture decisions
- **docs/IMPLEMENTATION_ROADMAP.md**: Development roadmap

## COMPONENT SPECIFICATIONS (docs/specs/)
- **01_POSITION_MONITOR.md**: Position tracking and state management
- **02_EXPOSURE_MONITOR.md**: Risk exposure calculations
- **03_RISK_MONITOR.md**: Risk assessment and limits
- **04_PNL_CALCULATOR.md**: Profit and loss calculations
- **05_STRATEGY_MANAGER.md**: Strategy orchestration
- **06_CEX_EXECUTION_MANAGER.md**: Centralized exchange execution
- **07_ONCHAIN_EXECUTION_MANAGER.md**: On-chain execution
- **08_EXECUTION_INTERFACES.md**: Execution interface specifications
- **09_DATA_PROVIDER.md**: Data provider specifications
- **10_REDIS_MESSAGING_STANDARD.md**: Messaging standards
- **11_ERROR_LOGGING_STANDARD.md**: Error logging standards
- **12_FRONTEND_SPEC.md**: Frontend specifications
- **13_ADVANCED_REBALANCING.md**: Advanced rebalancing logic

## BACKEND CORE COMPONENTS
- **backend/src/basis_strategy_v1/core/math/pnl_calculator.py**: P&L calculations
- **backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py**: Position monitoring
- **backend/src/basis_strategy_v1/core/interfaces/cex_execution_interface.py**: CEX execution
- **backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py**: Data provider

## QUALITY GATE SCRIPTS
- **scripts/test_pure_lending_quality_gates.py**: Pure lending strategy tests
- **scripts/test_btc_basis_quality_gates.py**: BTC basis strategy tests
- **scripts/test_tight_loop_quality_gates.py**: Architecture tests
- **scripts/run_quality_gates.py**: Full quality gate suite
- **scripts/orchestrate_quality_gates.py**: Orchestrated testing

## CURRENT CRITICAL ISSUES
1. **Pure Lending Yield**: 1166% APY instead of 3-8% (CRITICAL)
2. **Scripts Directory**: 5/14 scripts passing, need 10/14 (HIGH)
3. **BTC Basis Strategy**: 8/10 quality gates passing, need 10/10 (HIGH)
4. **Overall Quality Gates**: 8/24 passing, need 15/24 (MEDIUM)

## ENVIRONMENT SETUP
- **Backend**: Python 3.10+, FastAPI, Redis
- **Frontend**: React 19, TypeScript, Vite
- **Testing**: pytest, Vitest
- **Platform**: ./platform.sh backtest (for backtest mode)

## LOGGING AND DEBUGGING
- **Backend logs**: backend/logs/
- **API logs**: backend/logs/api.log
- **Component logs**: backend/logs/[component].log
- **Health check**: curl -s http://localhost:8001/health/

## SUCCESS CRITERIA
- Pure lending APY: 3-8% (not 1166%)
- Scripts directory: 10/14 passing (70%+)
- BTC basis strategy: 10/10 passing (100%)
- Overall quality gates: 15/24 passing (60%+)
