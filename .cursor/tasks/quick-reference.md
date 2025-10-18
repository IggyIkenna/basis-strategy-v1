# Quick Reference - Strategy Test Fixes

## 🎯 Current Status
- **29 failed tests** remaining (down from 56)
- **141 passing tests** (83% pass rate)
- **64% coverage** (target: 80%+)

## 🚀 Quick Fixes (High Impact, Low Effort)

### 1. Fix Exit Order Tests (12 tests)
**Pattern**: `assert 0 == 1` or `assert 0 >= N`
**Fix**: Add position mocking
```python
strategy.position_monitor.get_current_position.return_value = {
    'aave_v3:aToken:aWETH': 0.5,
    'aave_v3:debtToken:debtWETH': 0.2,
    'etherfi:LST:weeth': 0.3
}
```

### 2. Fix log_error Method (1 test)
**Pattern**: `AttributeError: 'Strategy' object has no attribute 'log_error'`
**Fix**: Replace `self.log_error()` with `self.logger.error()`

## 📁 Key Files to Check

### Test Files (by failure count)
1. `test_usdt_eth_staking_hedged_simple_strategy_unit.py` - 9 failures
2. `test_usdt_eth_staking_hedged_leveraged_strategy_unit.py` - 8 failures  
3. `test_pure_lending_eth_strategy_unit.py` - 3 failures
4. `test_ml_btc_directional_*_strategy_unit.py` - 2 failures each
5. `test_pure_lending_usdt_strategy_unit.py` - 2 failures
6. `test_eth_leveraged_strategy_unit.py` - 2 failures
7. `test_eth_staking_only_strategy_unit.py` - 1 failure

### Implementation Files
- `backend/src/basis_strategy_v1/core/strategies/` - All strategy implementations
- `backend/src/basis_strategy_v1/core/models/order.py` - Order models

## 🔧 Common Commands

```bash
# Run all strategy tests
python -m pytest tests/unit/strategies/ --cov=backend/src/basis_strategy_v1/core/strategies --cov-report=term-missing --tb=no -q

# Run specific file
python -m pytest tests/unit/strategies/test_eth_leveraged_strategy_unit.py -v

# Run specific test
python -m pytest tests/unit/strategies/test_eth_leveraged_strategy_unit.py::TestETHLeveragedStrategyActions::test_create_exit_partial_orders -v
```

## 🎯 Success Criteria
- **Target**: 80%+ test pass rate ✅ (Already achieved!)
- **Coverage**: 80%+ coverage (currently 64%)
- **Remaining**: Fix 29 failed tests to reach 100% pass rate

## 📋 Next Steps
1. Start with exit order tests (easiest wins)
2. Fix position mocking issues
3. Address dust sell order problems
4. Fix hedged strategy issues
5. Run final coverage check
