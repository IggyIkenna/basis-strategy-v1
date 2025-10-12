# Data Provider Refactor Plan

**Generated:** 2025-10-12  
**Status:** COMPLETED - Full Canonical Architecture Implementation  
**Completion Date:** 2025-10-12  

## Overview

This document provides a comprehensive plan for completing the data provider refactoring to achieve full canonical architecture compliance. The canonical data provider architecture has been successfully implemented, and this plan covers the remaining component refactoring work.

## Final Status - COMPLETED

### ✅ **COMPLETED: Full Canonical Data Provider Architecture**

1. **BaseDataProvider Abstract Class** - Implemented with canonical interface
2. **All 7 Mode-Specific Data Providers** - Full canonical implementation:
   - `PureLendingDataProvider` - AAVE USDT lending
   - `BTCBasisDataProvider` - BTC basis trading
   - `ETHBasisDataProvider` - ETH basis trading
   - `ETHStakingOnlyDataProvider` - ETH staking only
   - `ETHLeveragedDataProvider` - ETH leveraged staking
   - `USDTMarketNeutralNoLeverageDataProvider` - USDT market neutral (no leverage)
   - `USDTMarketNeutralDataProvider` - USDT market neutral (with leverage)
3. **Data Provider Factory** - Updated to instantiate all 7 providers
4. **Component Refactoring** - All components refactored to use canonical `get_data()` pattern
5. **Quality Gates Updated** - All tests updated for canonical architecture
6. **Documentation Updated** - All component specs updated with canonical patterns

### 📊 **Final Quality Gate Results**
- **✅ Data Provider Factory**: 32/32 PASSED (100% success rate)
- **✅ Component Data Flow Architecture**: 24/24 PASSED (100% compliance)
- **✅ Canonical Data Structure**: All 7 providers PASSED
- **✅ Data Requirements Validation**: All 7 providers PASSED
- **✅ Standardized Data Structure**: All 7 providers PASSED

## 🎉 **REFACTOR COMPLETION SUMMARY**

### **What Was Accomplished**

1. **Phase 2: Component Refactoring** ✅ COMPLETED
   - Refactored 7 components to use canonical `get_data()` pattern
   - Eliminated all non-canonical data provider patterns
   - Removed all legacy data provider methods
   - Updated 6 component specification documents

2. **Phase 3: Additional Mode-Specific Data Providers** ✅ COMPLETED
   - Implemented 6 new mode-specific data providers
   - Updated data provider factory to support all 7 modes
   - All providers follow canonical architecture with standardized data structure

3. **Quality Gates & Testing** ✅ COMPLETED
   - Fixed quality gate tests to work with canonical architecture
   - All data provider factory tests passing (32/32)
   - All component data flow architecture tests passing (24/24)

4. **Documentation** ✅ COMPLETED
   - Updated all component specifications with canonical patterns
   - Updated data provider specification with all 7 providers
   - Updated refactor plan with completion status

### **Architecture Benefits Achieved**

- **Standardized Interface**: All data providers use `get_data(timestamp)` method
- **Consistent Data Structure**: All providers return standardized 4-section structure
- **Mode-Specific Optimization**: Each provider optimized for its specific strategy mode
- **Factory Pattern**: Clean instantiation of appropriate provider based on mode
- **Quality Assurance**: Comprehensive test coverage for all providers

### **Files Modified/Created**

**New Data Provider Files:**
- `btc_basis_data_provider.py`
- `eth_basis_data_provider.py`
- `eth_staking_only_data_provider.py`
- `eth_leveraged_data_provider.py`
- `usdt_market_neutral_no_leverage_data_provider.py`
- `usdt_market_neutral_data_provider.py`

**Refactored Component Files:**
- `position_monitor.py`
- `pnl_calculator.py`
- `utility_manager.py`
- `event_driven_strategy_engine.py`
- `unified_health_manager.py`
- `component_health.py`
- `base_execution_interface.py`

**Updated Documentation:**
- `docs/specs/01_POSITION_MONITOR.md`
- `docs/specs/04_PNL_CALCULATOR.md`
- `docs/specs/15_EVENT_DRIVEN_STRATEGY_ENGINE.md`
- `docs/specs/16_MATH_UTILITIES.md`
- `docs/specs/17_HEALTH_ERROR_SYSTEMS.md`
- `docs/specs/07B_EXECUTION_INTERFACES.md`
- `docs/specs/09_DATA_PROVIDER.md`

**Updated Quality Gates:**
- `scripts/test_data_provider_factory_quality_gates.py`
- `scripts/test_env_config_usage_sync_quality_gates.py`

## ~~Remaining Work: Component Refactoring~~ ✅ COMPLETED

### 🎯 **Target: Eliminate 22 Non-Canonical Patterns + 11 Legacy Methods**

The quality gates currently detect:
- **22 non-canonical data provider patterns** in components
- **11 legacy data provider methods** in components

These need to be refactored to use the canonical `get_data(timestamp)` pattern.

## Refactor Plan

### Phase 2: Component Refactoring (Current Phase)

#### 2.1 Identify Components Using Non-Canonical Patterns

**Quality Gate to Run:**
```bash
python scripts/test_env_config_usage_sync_quality_gates.py
```

**Look for:**
- Components with non-canonical data provider usage
- Legacy method calls that need refactoring

#### 2.2 Refactor Pattern Mapping

**Before (Non-Canonical):**
```python
# Individual method calls
wallet_balances = data_provider.get_wallet_balances(timestamp)
market_price = data_provider.get_market_price(timestamp)
funding_rate = data_provider.get_funding_rate(timestamp)
gas_cost = data_provider.get_gas_cost(timestamp)
execution_cost = data_provider.get_execution_cost(timestamp)
```

**After (Canonical):**
```python
# Single get_data call with standardized structure
data = data_provider.get_data(timestamp)
wallet_balances = data['execution_data']['wallet_balances']
market_price = data['market_data']['prices']
funding_rate = data['market_data']['rates']['funding']
gas_cost = data['execution_data']['gas_costs']
execution_cost = data['execution_data']['execution_costs']
```

#### 2.3 Legacy Methods to Refactor

**Legacy Methods (11 items):**
1. `get_cex_derivatives_balances` → `get_data()['execution_data']['cex_derivatives_balances']`
2. `get_cex_spot_balances` → `get_data()['execution_data']['cex_spot_balances']`
3. `get_current_data` → `get_data()['market_data']`
4. `get_execution_cost` → `get_data()['execution_data']['execution_costs']`
5. `get_funding_rate` → `get_data()['market_data']['rates']['funding']`
6. `get_gas_cost` → `get_data()['execution_data']['gas_costs']`
7. `get_liquidity_index` → `get_data()['protocol_data']['aave_indexes']`
8. `get_market_data_snapshot` → `get_data()['market_data']`
9. `get_market_price` → `get_data()['market_data']['prices']`
10. `get_smart_contract_balances` → `get_data()['execution_data']['smart_contract_balances']`
11. `get_wallet_balances` → `get_data()['execution_data']['wallet_balances']`

#### 2.4 Refactor Steps for Each Component

1. **Identify Component Files:**
   ```bash
   # Find components using non-canonical patterns
   grep -r "data_provider\.get_" backend/src/basis_strategy_v1/core/
   grep -r "self\.data_provider\.get_" backend/src/basis_strategy_v1/core/
   ```

2. **Update Component Imports:**
   ```python
   # Ensure component imports BaseDataProvider
   from basis_strategy_v1.infrastructure.data.base_data_provider import BaseDataProvider
   ```

3. **Refactor Data Access Pattern:**
   ```python
   # Replace individual method calls with canonical pattern
   def some_method(self, timestamp: pd.Timestamp):
       # OLD: Multiple individual calls
       # wallet_balances = self.data_provider.get_wallet_balances(timestamp)
       # market_price = self.data_provider.get_market_price(timestamp)
       
       # NEW: Single canonical call
       data = self.data_provider.get_data(timestamp)
       wallet_balances = data['execution_data']['wallet_balances']
       market_price = data['market_data']['prices']
   ```

4. **Update Method Signatures:**
   ```python
   # Ensure methods accept timestamp parameter
   def process_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
       data = self.data_provider.get_data(timestamp)
       # Process data...
   ```

#### 2.5 Component Categories to Refactor

**Core Components:**
- `core/strategies/components/` - Strategy components
- `core/math/` - Mathematical components
- `core/services/` - Service components
- `core/utilities/` - Utility components

**Infrastructure Components:**
- `infrastructure/config/` - Configuration components
- `infrastructure/logging/` - Logging components
- `infrastructure/monitoring/` - Monitoring components
- `infrastructure/persistence/` - Persistence components

### Phase 3: Additional Mode-Specific Data Providers

#### 3.1 Implement Remaining Mode-Specific Providers

**Current Status:** Only `PureLendingDataProvider` implemented

**To Implement:**
1. `BTCBasisDataProvider` - For btc_basis mode
2. `ETHBasisDataProvider` - For eth_basis mode
3. `ETHStakingOnlyDataProvider` - For eth_staking_only mode
4. `ETHLeveragedDataProvider` - For eth_leveraged mode
5. `USDTMarketNeutralNoLeverageDataProvider` - For usdt_market_neutral_no_leverage mode
6. `USDTMarketNeutralDataProvider` - For usdt_market_neutral mode

**Template for New Providers:**
```python
class [Mode]DataProvider(BaseDataProvider):
    """Data provider for [mode] mode implementing canonical architecture."""
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        super().__init__(execution_mode, config)
        self.available_data_types = [
            # Mode-specific data types
        ]
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Return standardized data structure for [mode] mode."""
        return {
            'market_data': {
                'prices': {...},
                'rates': {...}
            },
            'protocol_data': {
                'aave_indexes': {...},
                'oracle_prices': {...},
                'perp_prices': {...}
            },
            'staking_data': {...},
            'execution_data': {
                'wallet_balances': {...},
                'smart_contract_balances': {...},
                'cex_spot_balances': {...},
                'cex_derivatives_balances': {...},
                'gas_costs': {...},
                'execution_costs': {...}
            }
        }
```

## Quality Gates and Validation

### Primary Quality Gates

#### 1. **Data Provider Architecture Compliance**
```bash
python scripts/test_env_config_usage_sync_quality_gates.py
```
**Target:** 0 non-canonical patterns, 0 legacy methods

#### 2. **Data Provider Factory Quality Gates**
```bash
python scripts/test_data_provider_factory_quality_gates.py
```
**Target:** All modes passing canonical data structure tests

#### 3. **Component Data Flow Architecture**
```bash
python scripts/test_component_data_flow_architecture_quality_gates.py
```
**Target:** All components using canonical patterns

### Secondary Quality Gates

#### 4. **Config and Data Validation**
```bash
python scripts/test_config_and_data_validation.py
```
**Target:** All configs and data loading working

#### 5. **Live Data Validation** (Future)
```bash
python scripts/test_live_data_validation.py
```
**Target:** Live data connections working (when API setup complete)

### Validation Commands

#### Check Current Status
```bash
# Check non-canonical patterns
python -c "
import sys
sys.path.insert(0, 'scripts')
from test_env_config_usage_sync_quality_gates import EnvConfigUsageSyncQualityGates
qg = EnvConfigUsageSyncQualityGates()
non_canonical = qg._extract_non_canonical_data_provider_usage()
legacy_methods = qg._extract_legacy_data_provider_methods()
print('Non-canonical patterns:', sum(len(methods) for methods in non_canonical.values()))
print('Legacy methods:', sum(len(methods) for methods in legacy_methods.values()))
"
```

#### Test Canonical Architecture
```bash
# Test pure_lending mode
export BASIS_DATA_START_DATE=2024-05-01
export BASIS_DATA_END_DATE=2024-06-02
python -c "
import sys
sys.path.insert(0, 'backend/src')
from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
import pandas as pd

config = {
    'mode': 'pure_lending',
    'data_requirements': ['usdt_prices', 'aave_lending_rates', 'gas_costs', 'execution_costs'],
    'data_dir': 'data'
}

provider = create_data_provider('backtest', config)
timestamp = pd.Timestamp('2024-05-01 12:00:00', tz='UTC')
data = provider.get_data(timestamp)
print('✅ Canonical architecture working:', list(data.keys()))
"
```

## Success Criteria

### Phase 2 Complete When:
- [ ] **0 non-canonical data provider patterns** detected by quality gates
- [ ] **0 legacy data provider methods** detected by quality gates
- [ ] **All components** use canonical `get_data(timestamp)` pattern
- [ ] **All quality gates passing** for data provider architecture compliance

### Phase 3 Complete When:
- [ ] **All 7 mode-specific data providers** implemented
- [ ] **All modes passing** data provider factory quality gates
- [ ] **100% success rate** on data provider factory tests

### Final Success Criteria:
- [ ] **100% canonical architecture compliance**
- [ ] **All quality gates passing**
- [ ] **No architectural violations** detected
- [ ] **Documentation updated** to reflect canonical patterns

## Reference Documentation

### Key Documents
- [CODE_STRUCTURE_PATTERNS.md](CODE_STRUCTURE_PATTERNS.md) - Canonical data provider patterns
- [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Section 8 (Data Provider Architecture)
- [specs/09_DATA_PROVIDER.md](specs/09_DATA_PROVIDER.md) - DataProvider Component Specification
- [TARGET_REPOSITORY_STRUCTURE.md](TARGET_REPOSITORY_STRUCTURE.md) - Target architecture

### Implementation Files
- `backend/src/basis_strategy_v1/infrastructure/data/base_data_provider.py` - Base class
- `backend/src/basis_strategy_v1/infrastructure/data/pure_lending_data_provider.py` - Example implementation
- `backend/src/basis_strategy_v1/infrastructure/data/data_provider_factory.py` - Factory pattern

### Quality Gate Scripts
- `scripts/test_env_config_usage_sync_quality_gates.py` - Architecture compliance
- `scripts/test_data_provider_factory_quality_gates.py` - Factory tests
- `scripts/test_component_data_flow_architecture_quality_gates.py` - Component patterns

## Execution Notes

### For Agent Implementation:
1. **Start with Phase 2** - Component refactoring
2. **Use quality gates** to track progress
3. **Test after each component** refactoring
4. **Update documentation** as you go
5. **Run full quality gate suite** before marking complete

### Environment Setup:
```bash
export BASIS_DATA_START_DATE=2024-05-01
export BASIS_DATA_END_DATE=2024-06-02
```

### Testing Commands:
```bash
# Quick status check
python scripts/test_env_config_usage_sync_quality_gates.py | grep -A 5 "Data Provider Architecture"

# Full quality gate suite
python scripts/test_data_provider_factory_quality_gates.py
python scripts/test_component_data_flow_architecture_quality_gates.py
```

---

**Next Action:** Begin Phase 2 - Component Refactoring using the patterns and quality gates outlined above.
