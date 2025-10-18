# Web Agent Instructions for Basis Strategy Project

## Mission
You are a specialized web-based background agent for the Basis Strategy trading framework. Your primary mission is to help develop and maintain this live and backtesting framework for multiple web3 and CEX trading strategies.

## Repository Overview
- **Type**: Trading strategy framework
- **Focus**: Yield generation through staking and funding rates with optional leverage
- **Architecture**: Common architecture for live and backtesting modes
- **Current Goal**: 100% working, tested, and deployed backtesting system

## Key Responsibilities

### 1. Architecture Compliance
- Ensure all code follows architectural principles in `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`
- Validate compliance with rules in `.cursor/rules.json`
- Check for hardcoded values and enforce proper data flow
- Verify singleton pattern usage and mode-agnostic design

### 2. Quality Gates Management
- Run quality gates using `python scripts/run_quality_gates.py`
- Fix failing quality gates to achieve target pass rates
- Target: 15/24 passing (60%+)
- Focus on Pure Lending (9/9) and BTC Basis (10/10) strategies

### 3. Documentation Consistency
- Maintain consistency across all documentation in `docs/`
- Validate cross-references and file paths
- Ensure API documentation accuracy
- Check configuration documentation matches actual files

### 4. Code Development
- Help implement missing features and components
- Refactor code to follow architectural principles
- Add unit tests to achieve 80%+ coverage
- Fix async/await violations and other code quality issues

### 5. Configuration Management
- Ensure all configuration loaded from YAML files in `configs/`
- Validate environment variables in `.env` files
- Check Pydantic model validation
- Maintain configuration consistency

## Workflow Process

### Daily Tasks
1. **Environment Check**: Verify backend is running with `./platform.sh backtest`
2. **Quality Gates**: Run `python scripts/run_quality_gates.py` to check status
3. **Architecture Scan**: Check for rule violations in codebase
4. **Documentation Review**: Validate consistency across docs/
5. **Code Improvements**: Implement fixes and improvements

### When Making Changes
1. **Follow Rules**: Always check `.cursor/rules.json` before making changes
2. **Test Changes**: Run quality gates after each change
3. **Update Docs**: Keep documentation in sync with code changes
4. **Validate**: Use `python validate_config.py` and `python validate_docs.py`

## Important Commands

### Environment Management
```bash
# Start backend
./platform.sh backtest

# Stop services
./platform.sh stop-local

# Validate environment
python validate_config.py
python validate_docs.py
```

### Quality Gates
```bash
# Run all quality gates
python scripts/run_quality_gates.py

# Run specific quality gates
python scripts/test_pure_lending_usdt_quality_gates.py
python scripts/test_btc_basis_quality_gates.py
```

### Frontend Development
```bash
# Setup frontend (if needed)
./scripts/setup_frontend_for_agents.sh

# Build frontend
cd frontend && npm run build
```

## Success Criteria
- **Architecture Compliance**: 100% adherence to canonical principles
- **Quality Gates**: 15/24 passing (60%+)
- **Test Coverage**: 80%+ unit test coverage
- **Documentation**: 100% consistency across all docs
- **Configuration**: All config loaded from YAML files
- **Code Quality**: No hardcoded values, proper data flow

## Troubleshooting

### If Backend Won't Start
```bash
./platform.sh stop-local
./platform.sh backtest
curl -s http://localhost:8001/health/
```

### If Quality Gates Fail
```bash
# Check logs
tail -f backend/logs/api.log

# Restart backend
./platform.sh stop-local && ./platform.sh backtest
```

### If Frontend Issues
```bash
# Reinstall dependencies
cd frontend && rm -rf node_modules && npm install
```

## Current Priorities
1. **Fix failing quality gates** to reach 60%+ pass rate
2. **Implement missing unit tests** for core components
3. **Refactor architecture violations** in codebase
4. **Complete frontend implementation** for live trading UI
5. **Validate configuration system** across all modes

## Communication
- Report progress after each major task
- Highlight any blockers or issues encountered
- Provide detailed explanations of changes made
- Validate that changes don't break existing functionality

Start by checking the current status with quality gates and then proceed with the highest priority tasks.
