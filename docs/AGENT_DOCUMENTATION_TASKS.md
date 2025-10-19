# Agent Documentation Tasks

**Generated:** 2025-10-12  
**Purpose:** Systematic documentation of remaining missing items identified by quality gates  
**Status:** Ready for Agent Execution  
**Total Tasks:** 18 items across 4 categories (8 require code changes)

## 🚨 **CRITICAL UPDATE: ML Strategy Integration Scope**

**ML Strategy Implementation Status**: Partially implemented but **NOT using canonical architecture**

**Current ML Implementation**:
- ✅ ML strategy manager exists (`ml_directional_strategy_manager.py`)
- ✅ ML data provider exists (`ml_directional_data_provider.py`) 
- ✅ ML mode configurations exist (`ml_btc_directional.yaml`)
- ❌ **ML strategy uses non-canonical `get_ml_prediction()` method**
- ❌ **ML data provider missing `ml_data` section in canonical structure**
- ❌ **ML methods not integrated into canonical `get_data()` pattern**

**Impact**: ML strategy integration is **incomplete** and violates canonical architecture standards.

## 📊 **UPDATED SCOPE SUMMARY**

### **Total Tasks**: 18 items across 4 categories
- **Documentation Only**: 10 items (45 minutes)
- **Code Changes Required**: 8 items (150 minutes)
- **Total Estimated Time**: 3.25 hours

### **Category Breakdown**:
1. **Data Provider Queries**: 1 item (documentation)
2. **Event Logging Patterns**: 9 items (documentation) 
3. **Data Provider Architecture Violations**: 3 items (code changes)
4. **ML Strategy Canonical Architecture Integration**: 5 items (code changes)

### **Critical Discovery**: 
The ML strategy integration plan shows as "done" but the implementation **does not use canonical architecture**. This means:
- ML strategy manager exists but uses non-canonical patterns
- ML data provider exists but missing canonical data structure
- ML functionality works but violates architectural standards
- Quality gates correctly identify these as violations

## Overview

This document provides specific, actionable tasks for an AI agent to systematically address the remaining documentation gaps identified by the environment config usage sync quality gates. Each task includes:

- **Exact location** where documentation should be added
- **Specific content** to be documented
- **File paths** to modify
- **Validation steps** to ensure completion

## Task Categories

1. **Data Provider Queries** (1 item)
2. **Event Logging Patterns** (9 items)  
3. **Data Provider Architecture Violations** (3 items)
4. **ML Strategy Canonical Architecture Integration** (5 items) - **NEW CATEGORY**

---

## 1. DATA PROVIDER QUERIES (1 item)

### Task 1.1: Identify and Document Missing Data Provider Query

**Objective**: Find and document the 1 undocumented data provider query in core components

**Steps**:
1. **Identify the Missing Query**:
   ```bash
   # Run quality gates to get specific details
   python scripts/test_env_config_usage_sync_quality_gates.py
   ```
   Look for output showing "1 undocumented data provider query" in core components

2. **Locate the Query in Code**:
   - Search for data provider method calls in core components
   - Identify which specific query is not documented

3. **Add to Component Specification**:
   - Find the appropriate component spec file in `docs/specs/`
   - Add the missing query to the "## Data Provider Queries" section
   - Follow the canonical pattern format

**Expected Format**:
```markdown
## Data Provider Queries

### Canonical Data Provider Pattern
Component uses the canonical `get_data(timestamp)` pattern:

```python
# Canonical pattern - single get_data call
data = self.data_provider.get_data(timestamp)
[missing_query] = data['[section]']['[subsection]']
```

### Data Types Requested
- **[section].[subsection]**: Description of the missing query
  - **Usage**: How the component uses this data
  - **Update frequency**: When this data is updated
```

**Validation**:
- Run quality gates again to confirm the query is now documented
- Verify the component spec file has been updated correctly

---

## 2. EVENT LOGGING PATTERNS (9 items)

### Task 2.1: Document Core Component Event Logging Patterns (5 items)

**Objective**: Add 5 undocumented event logging patterns to core component specifications

**Patterns to Document**:
1. **event** - Event logging method
2. **execution** - Execution event logging  
3. **position** - Position event logging
4. **timestep** - Timestep event logging
5. **transfer** - Transfer event logging

**Steps**:
1. **Identify Core Components Using These Patterns**:
   - Search codebase for these logging patterns
   - Map each pattern to the appropriate component

2. **Update Component Specifications**:
   - Add "## Event Logging Requirements" section to each relevant component spec
   - Document each pattern with usage examples

**Expected Format**:
```markdown
## Event Logging Requirements

### Event Logging Patterns
Component logs the following business events:

1. **event**: [Description of event logging]
   - **Usage**: [How and when this event is logged]
   - **Data**: [What data is included in the log]

2. **execution**: [Description of execution logging]
   - **Usage**: [How and when execution events are logged]
   - **Data**: [What execution data is logged]

3. **position**: [Description of position logging]
   - **Usage**: [How and when position events are logged]
   - **Data**: [What position data is logged]

4. **timestep**: [Description of timestep logging]
   - **Usage**: [How and when timestep events are logged]
   - **Data**: [What timestep data is logged]

5. **transfer**: [Description of transfer logging]
   - **Usage**: [How and when transfer events are logged]
   - **Data**: [What transfer data is logged]
```

**Files to Update**:
- `docs/specs/01_POSITION_MONITOR.md`
- `docs/specs/02_EXPOSURE_MONITOR.md`
- `docs/specs/03_RISK_MONITOR.md`
- `docs/specs/04_PNL_CALCULATOR.md`
- `docs/specs/05_STRATEGY_MANAGER.md`
- `docs/specs/06_EXECUTION_MANAGER.md`
- `docs/specs/07A_CEX_EXECUTION_INTERFACE.md`
- `docs/specs/07B_EXECUTION_INTERFACES.md`
- `docs/specs/11_SHARE_CLASS_MANAGER.md`
- `docs/specs/15_EVENT_DRIVEN_STRATEGY_ENGINE.md`

### Task 2.2: Document Infrastructure Component Event Logging Patterns (4 items)

**Objective**: Add 4 undocumented event logging patterns to infrastructure component specifications

**Patterns to Document**:
1. **business** - Business event logging
2. **data** - Data event logging
3. **risk** - Risk event logging
4. **strategy** - Strategy event logging

**Steps**:
1. **Identify Infrastructure Components Using These Patterns**:
   - Search codebase for these logging patterns in infrastructure components
   - Map each pattern to the appropriate component

2. **Update Component Specifications**:
   - Add "## Event Logging Requirements" section to each relevant component spec
   - Document each pattern with usage examples

**Expected Format**:
```markdown
## Event Logging Requirements

### Event Logging Patterns
Component logs the following business events:

1. **business**: [Description of business event logging]
   - **Usage**: [How and when business events are logged]
   - **Data**: [What business data is logged]

2. **data**: [Description of data event logging]
   - **Usage**: [How and when data events are logged]
   - **Data**: [What data events are logged]

3. **risk**: [Description of risk event logging]
   - **Usage**: [How and when risk events are logged]
   - **Data**: [What risk data is logged]

4. **strategy**: [Description of strategy event logging]
   - **Usage**: [How and when strategy events are logged]
   - **Data**: [What strategy data is logged]
```

**Files to Update**:
- `docs/specs/08_EVENT_LOGGER.md`
- `docs/specs/09_DATA_PROVIDER.md`
- `docs/specs/12_LIVE_SERVICE.md`
- `docs/specs/13_BACKTEST_SERVICE.md`
- `docs/specs/14_CONFIG_MANAGER.md`
- `docs/specs/16_MATH_UTILITIES.md`
- `docs/specs/17_HEALTH_ERROR_SYSTEMS.md`
- `docs/specs/18_METRICS_COLLECTOR.md`
- `docs/specs/19_CONFIGURATION.md`

**Validation**:
- Run quality gates to confirm event logging patterns are now documented
- Verify all component spec files have been updated correctly

---

## 3. DATA PROVIDER ARCHITECTURE VIOLATIONS (5 items)

### Task 3.1: Fix ML Strategy Manager Non-Canonical Method (1 item)

**Objective**: Replace `get_ml_prediction()` with canonical pattern

**File**: `backend/src/basis_strategy_v1/core/strategies/ml_directional_strategy_manager.py`

**Current Code** (Line 319):
```python
prediction = self.data_provider.get_ml_prediction(timestamp, self.asset)
```

**Required Fix**:
```python
# Get ML prediction from canonical data structure
data = self.data_provider.get_data(timestamp)
prediction = data.get('ml_data', {}).get('predictions', {}).get(self.asset)
```

**Steps**:
1. **Update the method call** to use canonical `get_data(timestamp)` pattern
2. **Access ML prediction** from the standardized data structure
3. **Handle missing data** gracefully with `.get()` methods
4. **Test the change** to ensure ML functionality still works

### Task 3.2: Fix Direct Attribute Access in Health Manager (2 items)

**Objective**: Replace direct attribute access with proper methods

**File**: `backend/src/basis_strategy_v1/core/health/unified_health_manager.py`

**Current Code** (Lines 281, 285, 289):
```python
if not self.data_provider._data_loaded:
if not self.data_provider.data:
if hasattr(self.data_provider, '_data_loaded') and self.data_provider._data_loaded:
```

**Required Fix**:
```python
# Replace direct attribute access with proper method calls
if not hasattr(self.data_provider, 'is_data_loaded') or not self.data_provider.is_data_loaded():
    # Handle case where data is not loaded
    pass

# Or use a test call to get_data to check if data is available
try:
    test_data = self.data_provider.get_data(pd.Timestamp.now())
    # Data is available
except Exception:
    # Data is not available
    pass
```

**Steps**:
1. **Replace direct attribute access** with proper method calls
2. **Use try/catch pattern** or proper method to check data availability
3. **Maintain existing functionality** while using canonical patterns

### Task 3.3: Fix Direct Attribute Access in Component Health (1 item)

**Objective**: Replace direct attribute access with proper methods

**File**: `backend/src/basis_strategy_v1/core/health/component_health.py`

**Current Code** (Line 236):
```python
checks["data_loaded"] = self.data_provider._data_loaded
```

**Required Fix**:
```python
# Replace direct attribute access with proper method
checks["data_loaded"] = hasattr(self.data_provider, 'is_data_loaded') and self.data_provider.is_data_loaded()
```

**Steps**:
1. **Replace direct attribute access** with proper method call
2. **Maintain the health check functionality**
3. **Use canonical patterns** for data provider interaction

### Task 3.4: Update Data Provider to Support ML Predictions (1 item)

**Objective**: Ensure data providers can return ML prediction data

**Files**: All data provider implementations

**Required Addition**:
Add ML prediction data to the canonical data structure:

```python
def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
    # ... existing code ...
    return {
        'market_data': { ... },
        'protocol_data': { ... },
        'staking_data': { ... },
        'execution_data': { ... },
        'ml_data': {  # NEW SECTION
            'predictions': self._get_ml_predictions(timestamp),
            'model_status': self._get_ml_model_status(timestamp)
        }
    }

def _get_ml_predictions(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
    """Get ML predictions at timestamp."""
    # Implementation depends on data availability
    return {
        'BTC': 0.0,  # Placeholder
        'ETH': 0.0   # Placeholder
    }
```

**Steps**:
1. **Add ml_data section** to all data provider `get_data()` methods
2. **Implement placeholder methods** for ML predictions
3. **Ensure backward compatibility** with existing code

**Validation**:
- Run quality gates to confirm all violations are resolved
- Run data provider factory tests to ensure no regressions
- Verify all components still function correctly

---

## 4. ML STRATEGY CANONICAL ARCHITECTURE INTEGRATION (5 items)

### Task 4.1: Fix ML Strategy Manager Non-Canonical Method (1 item)

**Objective**: Replace `get_ml_prediction()` with canonical `get_data(timestamp)` pattern

**File**: `backend/src/basis_strategy_v1/core/strategies/ml_directional_strategy_manager.py`

**Current Code** (Line 319):
```python
prediction = self.data_provider.get_ml_prediction(timestamp, self.asset)
```

**Required Fix**:
```python
# Get ML prediction from canonical data structure
data = self.data_provider.get_data(timestamp)
prediction = data.get('ml_data', {}).get('predictions', {}).get(self.asset)
```

**Steps**:
1. **Update the method call** to use canonical `get_data(timestamp)` pattern
2. **Access ML prediction** from the standardized data structure
3. **Handle missing data** gracefully with `.get()` methods
4. **Test the change** to ensure ML functionality still works

### Task 4.2: Add ML Data Section to ML Data Provider (1 item)

**Objective**: Add `ml_data` section to canonical data structure

**File**: `backend/src/basis_strategy_v1/infrastructure/data/ml_directional_data_provider.py`

**Current Code** (Lines 89-112):
```python
return {
    'market_data': { ... },
    'protocol_data': { ... },
    'staking_data': {},  # No staking for ML directional
    'execution_data': { ... }
}
```

**Required Fix**:
```python
return {
    'market_data': { ... },
    'protocol_data': { ... },
    'staking_data': {},  # No staking for ML directional
    'execution_data': { ... },
    'ml_data': {  # NEW SECTION
        'predictions': self._get_ml_predictions(timestamp),
        'ohlcv': self._get_ml_ohlcv_data(timestamp),
        'model_status': self._get_ml_model_status(timestamp)
    }
}
```

**Steps**:
1. **Add ml_data section** to the `get_data()` method return structure
2. **Implement helper methods** for ML data retrieval
3. **Integrate existing ML methods** into canonical structure
4. **Maintain backward compatibility** with existing ML functionality

### Task 4.3: Integrate Existing ML Methods into Canonical Structure (2 items)

**Objective**: Connect existing ML methods to canonical data structure

**File**: `backend/src/basis_strategy_v1/infrastructure/data/ml_directional_data_provider.py`

**Existing Methods to Integrate**:
- `_load_ml_ohlcv()` → `_get_ml_ohlcv_data()`
- `_load_ml_prediction()` → `_get_ml_predictions()`

**Required Implementation**:
```python
def _get_ml_predictions(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
    """Get ML predictions at timestamp."""
    try:
        prediction = self._load_ml_prediction(timestamp, self.asset)
        return {
            self.asset: prediction
        }
    except Exception as e:
        logger.warning(f"ML prediction not available: {e}")
        return {
            self.asset: {'signal': 'neutral', 'confidence': 0.0}
        }

def _get_ml_ohlcv_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
    """Get ML OHLCV data at timestamp."""
    try:
        ohlcv = self._load_ml_ohlcv(timestamp, self.asset)
        return {
            self.asset: ohlcv
        }
    except Exception as e:
        logger.warning(f"ML OHLCV not available: {e}")
        return {}

def _get_ml_model_status(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
    """Get ML model status at timestamp."""
    return {
        'model_version': 'v1.0.0',
        'last_updated': timestamp.isoformat(),
        'status': 'active'
    }
```

**Steps**:
1. **Create wrapper methods** that call existing ML methods
2. **Handle exceptions gracefully** with fallback values
3. **Return standardized structure** for ML data
4. **Maintain existing functionality** while adding canonical structure

### Task 4.4: Update ML Data Provider Factory Integration (1 item)

**Objective**: Ensure ML data provider is properly integrated with factory

**File**: `backend/src/basis_strategy_v1/infrastructure/data/data_provider_factory.py`

**Current Status**: ML data provider exists but may not be properly mapped

**Required Check**:
```python
# Verify ML data provider is mapped to ML modes
ML_MODE_MAPPING = {
    'ml_btc_directional': MLDirectionalDataProvider,
    'ml_usdt_directional': MLDirectionalDataProvider,
}
```

**Steps**:
1. **Verify ML mode mapping** in data provider factory
2. **Ensure ML data provider** is imported and available
3. **Test ML mode instantiation** through factory
4. **Validate canonical data structure** is returned

### Task 4.5: Add ML Data Provider to Quality Gate Tests (1 item)

**Objective**: Ensure ML data provider passes canonical architecture tests

**File**: `scripts/test_data_provider_factory_quality_gates.py`

**Required Addition**:
```python
# Add ML modes to test coverage
ML_MODES = ['ml_btc_directional', 'ml_usdt_directional']

# Test ML data provider canonical structure
for mode in ML_MODES:
    if mode in available_modes:
        provider = factory.create_data_provider(mode, test_config)
        data = provider.get_data(test_timestamp)
        
        # Validate ML data structure
        assert 'ml_data' in data, f"ML data provider missing ml_data section"
        assert 'predictions' in data['ml_data'], f"ML data provider missing predictions"
        assert 'ohlcv' in data['ml_data'], f"ML data provider missing ohlcv"
```

**Steps**:
1. **Add ML modes** to quality gate test coverage
2. **Validate ML data structure** in canonical tests
3. **Ensure ML data provider** passes all architecture tests
4. **Update test expectations** for ML-specific data

**Validation**:
- Run ML data provider factory tests to ensure canonical compliance
- Run quality gates to confirm ML violations are resolved
- Test ML strategy manager with canonical data provider
- Verify ML functionality works with canonical architecture

---

## EXECUTION STRATEGY

### Phase 1: Data Provider Queries (Task 1.1)
- **Priority**: High (single item, easy to complete)
- **Estimated Time**: 15 minutes
- **Dependencies**: None

### Phase 2: Event Logging Patterns (Tasks 2.1, 2.2)
- **Priority**: Medium (documentation only, no code changes)
- **Estimated Time**: 45 minutes
- **Dependencies**: None

### Phase 3: Architecture Violations (Tasks 3.1-3.4)
- **Priority**: Medium (code changes required, affects functionality)
- **Estimated Time**: 60 minutes
- **Dependencies**: None

### Phase 4: ML Strategy Canonical Architecture Integration (Tasks 4.1-4.5)
- **Priority**: High (ML strategy integration completion)
- **Estimated Time**: 90 minutes
- **Dependencies**: None

### Validation After Each Phase
```bash
# Run quality gates to verify progress
python scripts/test_env_config_usage_sync_quality_gates.py

# Run data provider tests to ensure no regressions
python scripts/test_data_provider_factory_quality_gates.py
```

## SUCCESS CRITERIA

### Complete Success
- **Data Provider Queries**: 0 undocumented queries
- **Event Logging Patterns**: 0 undocumented patterns
- **Data Provider Architecture**: 0 violations
- **ML Strategy Integration**: Full canonical architecture compliance
- **Quality Gate Status**: All categories PASSING

### Partial Success (Acceptable)
- **Data Provider Queries**: 0 undocumented queries
- **Event Logging Patterns**: 0 undocumented patterns
- **Data Provider Architecture**: ≤ 1 violation (minor cleanup acceptable)

## NOTES

1. **Code Changes Required**: 8 tasks require actual code changes (3 architectural + 5 ML integration)
2. **No Breaking Changes**: All code changes maintain existing functionality while using canonical patterns
3. **ML Strategy Integration**: Critical for completing the ML strategy implementation to canonical standards

2. **Quality Gate Integration**: Each task is designed to directly address specific quality gate failures

3. **Canonical Architecture**: All refactoring follows the established canonical data provider patterns

4. **Documentation Standards**: All documentation follows the established patterns in existing component specifications

5. **Validation**: Each task includes validation steps to ensure completion and no regressions

## REFERENCES

- **Quality Gate Script**: `scripts/test_env_config_usage_sync_quality_gates.py`
- **Data Provider Tests**: `scripts/test_data_provider_factory_quality_gates.py`
- **Component Specifications**: `docs/specs/`
- **Canonical Patterns**: `docs/CODE_STRUCTURE_PATTERNS.md`
- **Missing Items Report**: `docs/MISSING_DOCUMENTATION_ITEMS.md`
