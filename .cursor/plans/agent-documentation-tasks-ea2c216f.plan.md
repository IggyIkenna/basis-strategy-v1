<!-- ea2c216f-9668-432c-a85c-efe0b6220630 4522606f-356f-4bb7-88f4-58c7a917abf1 -->
# Agent Documentation Tasks Implementation

## Overview

Systematically implement all 18 tasks across 4 categories to resolve quality gate failures and complete ML strategy canonical architecture integration.

## Phase 1: Data Provider Queries (Task 1.1)

**Goal**: Document 2 undocumented data provider queries in core components

**Undocumented Queries**:

1. `get_ml_prediction()` - Used in `ml_directional_strategy_manager.py:319`
2. Direct attribute accesses in health components (`._data_loaded`, `.data`, `.execution_mode`, `.live_provider`)

**Actions**:

- Add ML prediction query to strategy manager spec (`docs/specs/05_STRATEGY_MANAGER.md`)
- Document health check data provider patterns in health system spec (`docs/specs/17_HEALTH_ERROR_SYSTEMS.md`)

## Phase 2: Event Logging Patterns (Tasks 2.1, 2.2)

**Goal**: Document 9 undocumented event logging patterns (5 core + 4 infrastructure)

**Core Component Patterns** (5 patterns):

- `log_event` - Event logging method
- `log_execution` - Execution event logging  
- `log_position` - Position event logging
- `log_timestep` - Timestep event logging
- `log_transfer` - Transfer event logging

**Files Using These Patterns**:

- `event_driven_strategy_engine.py`
- `base_execution_interface.py`
- `reconciliation_component.py`
- `wallet_transfer_executor.py`

**Actions**:

- Add "## Event Logging Requirements" sections to:
  - `docs/specs/15_EVENT_DRIVEN_STRATEGY_ENGINE.md`
  - `docs/specs/07B_EXECUTION_INTERFACES.md`
  - `docs/specs/10_RECONCILIATION_COMPONENT.md`

**Infrastructure Component Patterns** (4 patterns):

- `log_business` - Business event logging
- `log_data` - Data event logging
- `log_risk` - Risk event logging
- `log_strategy` - Strategy event logging

**Note**: Quality gate reports these but grep shows no usage. Will document expected patterns in infrastructure specs as placeholders.

**Actions**:

- Add "## Event Logging Requirements" sections to:
  - `docs/specs/08_EVENT_LOGGER.md`
  - `docs/specs/09_DATA_PROVIDER.md`

## Phase 3: Data Provider Architecture Violations (Tasks 3.1-3.4)

**Goal**: Fix 5 architecture violations (4 non-canonical methods + 1 legacy method)

### Task 3.1: Fix ML Strategy Manager Non-Canonical Method

**File**: `backend/src/basis_strategy_v1/core/strategies/ml_directional_strategy_manager.py:319`

Replace:

```python
prediction = self.data_provider.get_ml_prediction(timestamp, self.asset)
```

With:

```python
data = self.data_provider.get_data(timestamp)
prediction = data.get('ml_data', {}).get('predictions', {}).get(self.asset)
```

### Task 3.2: Fix Health Manager Direct Attribute Access

**File**: `backend/src/basis_strategy_v1/core/health/unified_health_manager.py:281,285,289`

Replace direct `._data_loaded` and `.data` access with proper method calls or try/catch pattern.

### Task 3.3: Fix Component Health Direct Attribute Access

**File**: `backend/src/basis_strategy_v1/core/health/component_health.py:236`

Replace:

```python
checks["data_loaded"] = self.data_provider._data_loaded
```

With:

```python
checks["data_loaded"] = hasattr(self.data_provider, 'is_data_loaded') and self.data_provider.is_data_loaded()
```

Also fix other direct accesses on lines 260-261, 276, 286, 290, 301.

### Task 3.4: Update Data Provider Base Class

**File**: `backend/src/basis_strategy_v1/infrastructure/data/base_data_provider.py`

Add `is_data_loaded()` method to base class to support health checks without direct attribute access.

## Phase 4: ML Strategy Canonical Architecture Integration (Tasks 4.1-4.5)

**Goal**: Complete ML strategy integration with canonical architecture

### Task 4.1: Fix ML Strategy Manager (duplicate of 3.1)

Same as Task 3.1 - already covered.

### Task 4.2: Add ML Data Section to ML Data Provider

**File**: `backend/src/basis_strategy_v1/infrastructure/data/ml_directional_data_provider.py:89-112`

Add to `get_data()` return structure:

```python
'ml_data': {
    'predictio ns': self._get_ml_predictions(timestamp),
    'ohlcv': self._get_ml_ohlcv_data(timestamp),
    'model_status': self._get_ml_model_status(timestamp)
}
```

### Task 4.3: Integrate Existing ML Methods

**File**: `backend/src/basis_strategy_v1/infrastructure/data/ml_directional_data_provider.py`

Create wrapper methods:

- `_get_ml_predictions(timestamp)` → calls existing `_load_ml_prediction()`
- `_get_ml_ohlcv_data(timestamp)` → calls existing `_load_ml_ohlcv()`
- `_get_ml_model_status(timestamp)` → returns model status dict

### Task 4.4: Verify ML Data Provider Factory Integration

**File**: `backend/src/basis_strategy_v1/infrastructure/data/data_provider_factory.py`

Already integrated (lines 109-110, 144-147). Verify modes work correctly.

### Task 4.5: Add ML Data Provider to Quality Gate Tests

**File**: `scripts/test_data_provider_factory_quality_gates.py`

Add ML modes to test coverage and validate `ml_data` section structure.

## Validation Strategy

After each phase:

1. Run: `python scripts/test_env_config_usage_sync_quality_gates.py`
2. Run: `python scripts/test_data_provider_factory_quality_gates.py`
3. Verify no regressions in existing tests

## Success Criteria

- Data Provider Queries: 0 undocumented queries
- Event Logging Patterns: 0 undocumented patterns
- Data Provider Architecture: 0 violations
- ML Strategy Integration: Full canonical compliance
- All quality gates: PASSING

### To-dos

- [ ] Document 2 undocumented data provider queries in component specs
- [ ] Document 9 event logging patterns across core and infrastructure specs
- [ ] Fix 5 data provider architecture violations in code
- [ ] Complete ML strategy canonical architecture integration (5 tasks)
- [ ] Run quality gates and verify all tests pass