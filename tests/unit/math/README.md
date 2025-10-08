# Math Tests

This directory contains comprehensive tests for all mathematical calculators in the basis strategy system.

## Test Structure

### Core Calculator Tests

- **`test_math_integration.py`** - Integration tests for all math calculators using actual implementations
- **`test_pnl_calculator.py`** - P&L calculation tests (moved from components)
- **`test_risk_monitor_calculators.py`** - Risk monitor calculator integration tests (moved from components)
- **`test_risk_monitor_dynamic_ltv.py`** - Dynamic LTV calculation tests (moved from components)

### Individual Calculator Tests

The following test files were created to test individual calculator classes, but may need updates to match actual implementations:

- **`test_yield_calculator.py`** - Yield and APY/APR calculation tests
- **`test_ltv_calculator.py`** - Loan-to-Value ratio calculation tests
- **`test_margin_calculator.py`** - Margin and leverage calculation tests
- **`test_health_calculator.py`** - Health factor and risk calculation tests
- **`test_aave_rate_calculator.py`** - AAVE interest rate calculation tests
- **`test_metrics_calculator.py`** - Performance metrics calculation tests

## Calculator Classes Tested

### 1. YieldCalculator (`backend/src/basis_strategy_v1/core/math/yield_calculator.py`)
- APY to APR conversion
- APR to APY conversion
- Simple and compound yield calculations
- Staking, lending, and funding yield calculations
- Blended APR calculations
- Effective yield calculations with fees

### 2. LTVCalculator (`backend/src/basis_strategy_v1/core/math/ltv_calculator.py`)
- Current LTV calculation
- Projected LTV after borrowing
- Next loop capacity calculation
- Health factor calculation
- Leverage headroom calculation
- Multi-collateral LTV calculations

### 3. HealthCalculator (`backend/src/basis_strategy_v1/core/math/health_calculator.py`)
- Health factor calculation
- Weighted health factor for multiple assets
- Distance to liquidation
- Risk score calculation
- Safe withdrawal and borrow amounts
- Required collateral for target health

### 4. MarginCalculator (`backend/src/basis_strategy_v1/core/math/margin_calculator.py`)
- Margin requirement calculation
- Maintenance margin calculation
- Margin ratio calculation
- Liquidation price calculation
- Available margin calculation
- Funding payment calculation
- Portfolio margin calculation
- Cross-margin calculations

### 5. MetricsCalculator (`backend/src/basis_strategy_v1/core/math/metrics_calculator.py`)
- Portfolio metrics calculation
- Total return calculation
- Performance metrics
- Risk metrics

### 6. AAVERateCalculator (`backend/src/basis_strategy_v1/core/math/aave_rate_calculator.py`)
- AAVE interest rate calculation
- Market impact delta calculation
- Utilization impact calculation

### 7. PnLCalculator (`backend/src/basis_strategy_v1/core/math/pnl_calculator.py`)
- P&L calculation and attribution
- Balance-based vs attribution-based P&L
- Reconciliation between different P&L methods

## Running Tests

### Run All Math Tests
```bash
python -m pytest tests/unit/math/ -v
```

### Run Specific Test File
```bash
python -m pytest tests/unit/math/test_math_integration.py -v
```

### Run Individual Test
```bash
python -m pytest tests/unit/math/test_math_integration.py::TestMathIntegration::test_yield_calculator_basic -v
```

## Test Coverage

The integration tests (`test_math_integration.py`) provide comprehensive coverage of:
- ✅ Basic functionality of all calculators
- ✅ Precision handling with Decimal arithmetic
- ✅ Edge cases and error handling
- ✅ Integration between different calculators
- ✅ Real-world scenarios (yield-LTV integration)

## Notes

- All calculators use `Decimal` for precise financial calculations
- Tests verify both mathematical correctness and precision
- Integration tests ensure calculators work together properly
- Edge cases are tested to ensure robust error handling
- Tests follow the existing codebase patterns and requirements

## Future Improvements

1. **Update Individual Tests**: The individual calculator test files may need updates to match actual method signatures
2. **Add More Edge Cases**: Additional edge cases for extreme values and error conditions
3. **Performance Tests**: Add performance benchmarks for calculation speed
4. **Property-Based Testing**: Consider using hypothesis for property-based testing of mathematical properties
5. **Integration with Real Data**: Tests with actual market data and realistic scenarios
