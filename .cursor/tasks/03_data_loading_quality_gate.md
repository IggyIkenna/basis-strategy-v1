# DATA LOADING QUALITY GATE

## OVERVIEW
This task implements a comprehensive pre-check quality gate for all data files to validate data completeness, alignment, and availability for all strategy modes before proceeding with implementation. This ensures we have all required data before attempting any strategy execution.

**Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 8 (Data Provider Architecture)  
**Reference**: `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-002 (Data Provider Architecture)  
**Reference**: `docs/specs/06_DATA_PROVIDER.md` - Data provider specification  
**Reference**: `data/` - All data directories and files  
**Reference**: `scripts/test_data_provider_refactor_quality_gates.py` - Existing data quality gates

## CRITICAL REQUIREMENTS

### 1. Data Completeness Validation
- **Market data**: Validate all required market data files exist for all strategy modes
- **Protocol data**: Validate all required protocol data files exist for all venues
- **Blockchain data**: Validate all required blockchain data files exist
- **Execution costs**: Validate all required execution cost data exists
- **Manual sources**: Validate all required manual data sources exist

### 2. Data Alignment Validation
- **Timestamp alignment**: Verify data timestamps are consistent across all sources
- **Data freshness**: Verify data is recent enough for strategy execution
- **Data gaps**: Detect and report any gaps in time series data
- **Data consistency**: Verify data consistency across different sources

### 3. Strategy Mode Data Requirements
- **Pure lending**: Validate data for AAVE, Morpho, and other lending protocols
- **BTC basis**: Validate data for BTC funding rates, futures, and spot prices
- **ETH basis**: Validate data for ETH funding rates, futures, spot prices, and LST data
- **USDT market neutral**: Validate data for all venues and cross-venue arbitrage

### 4. Data Quality Metrics
- **Coverage**: Measure data coverage for each strategy mode
- **Completeness**: Measure data completeness for each time period
- **Accuracy**: Validate data accuracy where possible
- **Reliability**: Assess data source reliability

## FORBIDDEN PRACTICES

### 1. Partial Data Validation
- **No incomplete validation**: Don't proceed if any required data is missing
- **No warning-only validation**: Missing data must be errors, not warnings
- **No graceful degradation**: Missing critical data must cause failure

### 2. Assumption-Based Validation
- **No data assumptions**: Don't assume data exists without verification
- **No format assumptions**: Don't assume data formats without validation
- **No source assumptions**: Don't assume data sources without verification

## REQUIRED IMPLEMENTATION

### 1. Data Availability Checker
```python
# scripts/test_data_availability_quality_gates.py
class DataAvailabilityChecker:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.market_data_dir = f"{data_dir}/market_data"
        self.protocol_data_dir = f"{data_dir}/protocol_data"
        self.blockchain_data_dir = f"{data_dir}/blockchain_data"
        self.execution_costs_dir = f"{data_dir}/execution_costs"
        self.manual_sources_dir = f"{data_dir}/manual_sources"
    
    def check_all_data_availability(self) -> dict:
        # 1. Check market data availability
        # 2. Check protocol data availability
        # 3. Check blockchain data availability
        # 4. Check execution cost data availability
        # 5. Check manual source data availability
        # 6. Validate data alignment and timestamps
        # 7. Return comprehensive data availability report
```

### 2. Strategy Mode Data Requirements
```python
# Define data requirements for each strategy mode
STRATEGY_DATA_REQUIREMENTS = {
    'pure_lending': {
        'protocols': ['aave_v3', 'morpho'],
        'assets': ['USDC', 'USDT', 'DAI'],
        'timeframes': ['1h', '1d'],
        'required_fields': ['apy', 'total_supply', 'total_borrow']
    },
    'btc_basis': {
        'venues': ['binance', 'bybit', 'okx'],
        'assets': ['BTC'],
        'timeframes': ['1h', '1d'],
        'required_fields': ['funding_rate', 'spot_price', 'futures_price']
    },
    'eth_basis': {
        'venues': ['binance', 'bybit', 'okx'],
        'protocols': ['lido', 'etherfi'],
        'assets': ['ETH'],
        'timeframes': ['1h', '1d'],
        'required_fields': ['funding_rate', 'spot_price', 'futures_price', 'lst_apy']
    },
    'usdt_market_neutral': {
        'venues': ['binance', 'bybit', 'okx'],
        'protocols': ['aave_v3', 'morpho', 'lido', 'etherfi'],
        'assets': ['USDT', 'USDC', 'ETH'],
        'timeframes': ['1h', '1d'],
        'required_fields': ['funding_rate', 'spot_price', 'futures_price', 'apy', 'lst_apy']
    }
}
```

### 3. Data Quality Metrics
- **Coverage metrics**: Measure data coverage for each strategy mode
- **Completeness metrics**: Measure data completeness for each time period
- **Alignment metrics**: Measure data alignment across sources
- **Freshness metrics**: Measure data freshness and staleness

## VALIDATION

### 1. Data File Existence
- **Test all files exist**: Verify all required data files exist
- **Test file accessibility**: Verify all data files are readable
- **Test file formats**: Verify all data files have correct formats

### 2. Data Content Validation
- **Test data completeness**: Verify data is complete for required time periods
- **Test data alignment**: Verify data timestamps are aligned
- **Test data consistency**: Verify data is consistent across sources

### 3. Strategy Mode Validation
- **Test pure lending data**: Verify all data required for pure lending exists
- **Test BTC basis data**: Verify all data required for BTC basis exists
- **Test ETH basis data**: Verify all data required for ETH basis exists
- **Test USDT market neutral data**: Verify all data required for USDT market neutral exists

## QUALITY GATES

### 1. Data Availability Quality Gate
```bash
# scripts/test_data_availability_quality_gates.py
def test_data_availability():
    # Test all data files exist and are accessible
    # Test data completeness for all strategy modes
    # Test data alignment and timestamps
    # Test data quality metrics
```

### 2. Strategy Mode Data Quality Gate
```bash
# Test data requirements for each strategy mode
# Test data coverage and completeness
# Test data alignment across sources
```

## SUCCESS CRITERIA

### 1. Data File Availability ✅
- [ ] All required market data files exist and are accessible
- [ ] All required protocol data files exist and are accessible
- [ ] All required blockchain data files exist and are accessible
- [ ] All required execution cost data files exist and are accessible
- [ ] All required manual source data files exist and are accessible

### 2. Data Completeness ✅
- [ ] Data is complete for all required time periods
- [ ] Data coverage is sufficient for all strategy modes
- [ ] Data gaps are identified and reported
- [ ] Data freshness is adequate for strategy execution

### 3. Data Alignment ✅
- [ ] Data timestamps are aligned across all sources
- [ ] Data consistency is maintained across sources
- [ ] Data quality metrics meet minimum thresholds
- [ ] Data validation passes for all strategy modes

### 4. Strategy Mode Support ✅
- [ ] Pure lending data requirements are met
- [ ] BTC basis data requirements are met
- [ ] ETH basis data requirements are met
- [ ] USDT market neutral data requirements are met

## QUALITY GATE SCRIPT

The quality gate script `scripts/test_data_availability_quality_gates.py` will:

1. **Test Data File Availability**
   - Verify all required data files exist and are accessible
   - Verify data file formats are correct
   - Verify data file permissions are appropriate

2. **Test Data Completeness**
   - Verify data is complete for all required time periods
   - Verify data coverage is sufficient for all strategy modes
   - Verify data gaps are identified and reported

3. **Test Data Alignment**
   - Verify data timestamps are aligned across all sources
   - Verify data consistency is maintained across sources
   - Verify data quality metrics meet minimum thresholds

4. **Test Strategy Mode Data Requirements**
   - Verify pure lending data requirements are met
   - Verify BTC basis data requirements are met
   - Verify ETH basis data requirements are met
   - Verify USDT market neutral data requirements are met

**Expected Results**: All data files are available, complete, and aligned. All strategy modes have sufficient data for execution.
