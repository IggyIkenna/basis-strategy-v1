# Data Requirements & Validation - Quick Reference 📊

**Status**: 🚧 LIGHTWEIGHT REFERENCE - See [DATA_VALIDATION_GUIDE.md](DATA_VALIDATION_GUIDE.md) for complete details  
**Purpose**: Quick reference for data requirements  
**Archive After**: All content migrated to DATA_VALIDATION_GUIDE.md  
**Updated**: October 3, 2025

---

## 📚 **For Complete Documentation**

**See [DATA_VALIDATION_GUIDE.md](DATA_VALIDATION_GUIDE.md)** for:
- Complete data requirements (22 files)
- Validation levels (unit, integration, backtest, live)
- Configuration validation infrastructure
- Data quality metrics
- Error handling
- Testing procedures

---

## 🎯 **Quick Summary**

### **Data Requirements**
- **Total Files**: 22 data files covering May 12, 2024 to September 18, 2025
- **Categories**: AAVE rates, oracle prices, market data, futures, staking, gas costs
- **Validation**: Comprehensive validation at 4 levels

### **Component Data Access**
```python
# DataProvider loads all data in _load_data_for_mode()
data_provider = DataProvider(data_dir, mode, execution_mode, config)

# Components receive data as needed:
exposure = await exposure_monitor.calculate_exposure(
    timestamp=timestamp,
    position_snapshot=positions,
    market_data=market_data
)
```

### **Oracle Assumptions**
- **Binance** is primary oracle for BTC/USDT and ETH/USDT spot prices
- **AAVE oracles** used for weETH/wstETH pricing (vs USD and vs ETH)
- **USD = USDT assumption**: 1:1 parity
- **No USD/USDT conversion** needed in calculations

---

## 📋 **Data File Categories**

### **1. AAVE Protocol Data** (4 files)
- weETH, wstETH, WETH, USDT rates
- Required for all lending/staking modes

### **2. Oracle Prices** (3 files)
- AAVE oracle prices for weETH/ETH, wstETH/ETH, wstETH/USD
- Required for AAVE mechanics

### **3. Market Data** (2 files)
- BTC/USDT, ETH/USDT (Binance as primary oracle)
- Required for all modes

### **4. Futures Data** (5 files)
- BTC/ETH perpetuals from Binance, Bybit, OKX
- Required for hedged modes

### **5. Staking Data** (2 files)
- Seasonal rewards, benchmark yields
- Required for staking modes

### **6. Execution & Gas Costs** (2 files)
- Execution cost lookup, gas prices
- Required for all modes

### **7. AAVE Risk Parameters** (1 file)
- aave_v3_risk_parameters.json (LTV limits, liquidation thresholds)
- Required for risk calculations

### **8. Protocol Tokens** (2 files)
- EIGEN/USDT, ETHFI/USDT prices
- Required for KING token handling

**For detailed file paths and requirements**: See [DATA_VALIDATION_GUIDE.md](DATA_VALIDATION_GUIDE.md)

---

## ✅ **Validation Levels**

### **Level 1: Unit Tests**
- File existence, format, date ranges
- **Location**: `test_data_validation.py`

### **Level 2: Integration Tests**
- Mode-specific data loading
- **Location**: `test_data_validation.py`

### **Level 3: Backtest Startup**
- Fail-fast validation before execution
- **Location**: `DataProvider.__init__()`

### **Level 4: Live Mode**
- Real-time data quality checks
- **Location**: Live execution components

**For complete validation details**: See [DATA_VALIDATION_GUIDE.md](DATA_VALIDATION_GUIDE.md)

---

## 🔄 **Strategy Mode Requirements**

| Mode | Data Sources | Files |
|------|--------------|-------|
| **pure_lending** | 4 sources | Gas, execution costs, USDT rates, lookup |
| **btc_basis** | 9 sources | Gas, execution, BTC spot/futures/funding, lookup |
| **eth_leveraged** | 9 sources | Gas, execution, weETH/WETH rates, oracle, staking, ETH spot |
| **usdt_market_neutral** | 15 sources | All ETH data + futures + funding rates |

---

## 🚨 **Common Issues**

### **Missing Data**
```bash
# Error: Required data file not found
FileNotFoundError: data/protocol_data/aave/rates/aave_v3_..._weETH_rates...csv
```
**Solution**: Download missing data file or run data downloader

### **Date Range Issues**
```bash
# Error: Data starts too late
ValueError: Data starts at 2024-05-13 but required start is 2024-05-12
```
**Solution**: Extend data coverage or adjust backtest dates

### **Configuration Validation Failures**
```bash
# Error: Invalid configuration
ConfigurationError: leverage_enabled=true but max_leverage not specified
```
**Solution**: Fix configuration per validation error message

**For complete error handling**: See [DATA_VALIDATION_GUIDE.md](DATA_VALIDATION_GUIDE.md)

---

## 📝 **Quick Testing**

```bash
# Run all validation tests
python3 test_data_validation.py

# Check specific mode
python3 -c "from test_data_validation import DataValidationTestSuite; \
            suite = DataValidationTestSuite(); \
            suite.test_mode_specific_data()"
```

---

## 🎯 **Next Steps**

1. **Need validation details?** → [DATA_VALIDATION_GUIDE.md](DATA_VALIDATION_GUIDE.md)
2. **Need data provider details?** → [specs/09_DATA_PROVIDER.md](specs/09_DATA_PROVIDER.md)
3. **Need AAVE mechanics?** → [specs/02_EXPOSURE_MONITOR.md](specs/02_EXPOSURE_MONITOR.md)

---

**This is a lightweight reference. All detailed content is in [DATA_VALIDATION_GUIDE.md](DATA_VALIDATION_GUIDE.md)**

*Last Updated: October 3, 2025*
