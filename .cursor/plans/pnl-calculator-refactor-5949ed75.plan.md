<!-- 5949ed75-c85d-42f6-b15e-62045d94d63d e7ab967c-e4ba-44f8-a4ef-60c7a5c145e8 -->
# Comprehensive PnL Monitor Read/Calculate Separation Refactor Plan

## Overview

This plan refactors ALL components calling PnL Monitor to use proper read/calculate separation. The current `get_current_pnl()` method will be renamed to `calculate_pnl()` and new read-only methods will be added for O(1) cached access.

## Scope: Complete Project Coverage

After searching the entire codebase, the following areas need updates:

### Code Files (15 files)

- Core implementation: `pnl_monitor.py`
- Direct callers: `event_driven_strategy_engine.py`, `position_update_handler.py`
- Test scripts: `test_pnl_monitor_enhanced.py`, `test_pnl_monitor_plot.py`
- Unit tests: `test_pnl_monitor_unit.py`
- Integration tests: `conftest.py`
- Quality gates: `test_mode_agnostic_architecture_quality_gates.py`, `test_pnl_monitor_separation_quality_gates.py`, `run_quality_gates.py`
- API routes: `results.py`, `live_trading.py`
- Infrastructure: `async_results_store.py`
- Services: `backtest_service.py`

### Documentation Files (8 files)

- Specs: `04_pnl_monitor.md`, `11_POSITION_UPDATE_HANDLER.md`, `15_EVENT_DRIVEN_STRATEGY_ENGINE.md`, `18_RESULTS_STORE.md`
- Workflow: `WORKFLOW_GUIDE.md`
- Code patterns: `CODE_STRUCTURE_PATTERNS.md`
- Integration: `INTEGRATION_ALIGNMENT_REPORT.md`
- Architecture: `pnl_monitor_ARCHITECTURE_ANALYSIS.md`

### Quality Gate Scripts (4 files)

- `test_pnl_monitor_separation_quality_gates.py`
- `test_component_signature_validation_quality_gates.py`
- `run_quality_gates.py`
- Task files in `.cursor/tasks/`

### Frontend Files (TypeScript/React)

- API constants: `frontend/src/utils/constants.ts`
- Performance components: `frontend/src/components/live/LivePerformanceDashboard.tsx`
- API integration files calling PnL endpoints

---

## Phase 1: Core PnL Monitor Updates

### 1.1 Add New Read-Only Methods

**File**: `backend/src/basis_strategy_v1/core/math/pnl_monitor.py`

Add new read-only methods:

```python
def get_latest_pnl(self) -> Optional[Dict]:
    """Get the most recent P&L result without calculation."""
    return self.latest_pnl_result

def get_pnl_history(self, limit: int = 100) -> List[Dict]:
    """Get P&L history without calculation."""
    return self.pnl_history[-limit:] if self.pnl_history else []

def get_cumulative_attribution(self) -> Dict[str, float]:
    """Get cumulative attribution values without calculation."""
    return self.cumulative_attribution.copy()

def get_pnl_summary(self) -> str:
    """Get formatted summary of latest P&L without calculation."""
    if not self.latest_pnl_result:
        return "No P&L data available"
    
    pnl = self.latest_pnl_result
    return f"Total P&L: ${pnl.get('total_pnl_usd', 0):,.2f} | Return: {pnl.get('return_percent', 0):.2f}%"
```

Add enhanced state storage:

```python
def __init__(self, ...):
    # ... existing init code ...
    
    # Add caching state
    self.latest_pnl_result: Optional[Dict] = None
    self.pnl_history: List[Dict] = []
    self.calculation_timestamps: List[pd.Timestamp] = []
```

### 1.2 Rename get_current_pnl() to calculate_pnl()

**File**: `backend/src/basis_strategy_v1/core/math/pnl_monitor.py` (Line 200)

```python
def calculate_pnl(
    self,
    current_exposure: Dict,
    previous_exposure: Optional[Dict] = None,
    timestamp: pd.Timestamp = None,
    period_start: pd.Timestamp = None
) -> Dict:
    """
    Explicitly calculate P&L and store results.
    
    This method performs full P&L calculation and updates internal state.
    For read-only access to cached results, use get_latest_pnl().
    """
    # ... existing get_current_pnl logic ...
    
    # Store results in cache
    self.latest_pnl_result = pnl_result
    self.pnl_history.append(pnl_result)
    self.calculation_timestamps.append(timestamp)
    
    return pnl_result
```

Add deprecated alias:

```python
def get_current_pnl(self, *args, **kwargs) -> Dict:
    """DEPRECATED: Use calculate_pnl() instead."""
    import warnings
    warnings.warn(
        "get_current_pnl() is deprecated, use calculate_pnl() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return self.calculate_pnl(*args, **kwargs)
```

### 1.3 Update Internal Self-Calls

**File**: `backend/src/basis_strategy_v1/core/math/pnl_monitor.py` (Line 304)

Change from:

```python
pnl_result = self.get_current_pnl(
    current_exposure=current_exposure,
    previous_exposure=previous_exposure,
    timestamp=timestamp
)
```

To:

```python
pnl_result = self.calculate_pnl(
    current_exposure=current_exposure,
    previous_exposure=previous_exposure,
    timestamp=timestamp
)
```

---

## Phase 2: Update Direct Callers

### 2.1 EventDrivenStrategyEngine Updates

**File**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py`

**Line 623** - Main timestep calculation:

```python
# OLD:
pnl = self.pnl_monitor.get_current_pnl(
    current_exposure=exposure,
    timestamp=timestamp
)

# NEW:
pnl = self.pnl_monitor.calculate_pnl(
    current_exposure=exposure,
    timestamp=timestamp
)
```

**Line 687** - Final calculation:

```python
# OLD:
final_pnl = self.pnl_monitor.get_current_pnl(final_exposure, timestamp=self.current_timestamp)

# NEW:
final_pnl = self.pnl_monitor.calculate_pnl(final_exposure, timestamp=self.current_timestamp)
```

### 2.2 PositionUpdateHandler Updates

**File**: `backend/src/basis_strategy_v1/core/components/position_update_handler.py`

**Line 281** - Tight loop recalculation:

```python
# OLD:
updated_pnl = self.pnl_monitor.get_current_pnl(
    current_exposure=updated_exposure,
    timestamp=timestamp
)

# NEW:
updated_pnl = self.pnl_monitor.calculate_pnl(
    current_exposure=updated_exposure,
    timestamp=timestamp
)
```

**Line 399** - Atomic update recalculation:

```python
# OLD:
updated_pnl = self.pnl_monitor.get_current_pnl(
    current_exposure=updated_exposure,
    timestamp=timestamp
)

# NEW:
updated_pnl = self.pnl_monitor.calculate_pnl(
    current_exposure=updated_exposure,
    timestamp=timestamp
)
```

---

## Phase 3: Update Test Scripts

### 3.1 Enhanced Test Script

**File**: `scripts/test_pnl_monitor_enhanced.py` (Line 283)

```python
# OLD:
pnl_result = pnl_monitor.get_current_pnl(
    current_exposure=exposure,
    timestamp=timestamp
)

# NEW:
pnl_result = pnl_monitor.calculate_pnl(
    current_exposure=exposure,
    timestamp=timestamp
)
```

### 3.2 Plot Test Script

**File**: `scripts/test_pnl_monitor_plot.py` (Line 164)

```python
# OLD:
pnl_result = pnl_monitor.get_current_pnl(
    current_exposure=exposure,
    timestamp=timestamp
)

# NEW:
pnl_result = pnl_monitor.calculate_pnl(
    current_exposure=exposure,
    timestamp=timestamp
)
```

---

## Phase 4: Update Unit Tests

### 4.1 Main Unit Tests

**File**: `tests/unit/test_pnl_monitor_unit.py`

Update ALL instances of `calculate_pnl()` calls to ensure they're testing the calculation method, not a read-only method.

Add new tests for read-only methods:

```python
def test_get_latest_pnl_without_calculation(self, mock_config, mock_data_provider, mock_utility_manager):
    """Test read-only access to latest P&L."""
    pnl_monitor = PnLMonitor(...)
    
    # Should return None before any calculation
    assert pnl_monitor.get_latest_pnl() is None
    
    # Calculate P&L
    pnl_monitor.calculate_pnl(100000.0, 95000.0)
    
    # Should return cached result
    latest = pnl_monitor.get_latest_pnl()
    assert latest is not None
    assert isinstance(latest, dict)

def test_get_pnl_history(self, mock_config, mock_data_provider, mock_utility_manager):
    """Test P&L history retrieval."""
    pnl_monitor = PnLMonitor(...)
    
    # Calculate multiple P&L values
    for value in [100000, 101000, 102000]:
        pnl_monitor.calculate_pnl(value, 100000.0)
    
    # Get history
    history = pnl_monitor.get_pnl_history(limit=2)
    assert len(history) == 2

def test_get_cumulative_attribution(self, mock_config, mock_data_provider, mock_utility_manager):
    """Test cumulative attribution access."""
    pnl_monitor = PnLMonitor(...)
    
    attribution = pnl_monitor.get_cumulative_attribution()
    assert isinstance(attribution, dict)
```

### 4.2 Integration Test Config

**File**: `tests/integration/conftest.py` (Line 435)

```python
# OLD:
pnl_result = pnl_monitor.calculate_pnl(test_exposure, timestamp=pd.Timestamp.now())

# NEW: (already using calculate_pnl - verify it's correct)
pnl_result = pnl_monitor.calculate_pnl(test_exposure, timestamp=pd.Timestamp.now())
```

---

## Phase 5: Update Quality Gates

### 5.1 PnL Separation Quality Gate

**File**: `scripts/test_pnl_monitor_separation_quality_gates.py`

Update to check for:

1. `calculate_pnl()` method exists
2. Read-only methods exist: `get_latest_pnl()`, `get_pnl_history()`, `get_cumulative_attribution()`
3. `get_current_pnl()` is marked as deprecated (if kept as alias)

### 5.2 Mode Agnostic Quality Gate

**File**: `scripts/test_mode_agnostic_architecture_quality_gates.py` (Line 276)

```python
# Already using calculate_pnl - verify it works
pnl_result = pnl_monitor.calculate_pnl(test_exposure, timestamp=pd.Timestamp.now())
```

### 5.3 Component Signature Quality Gate

**File**: `scripts/test_component_signature_validation_quality_gates.py` (Line 409)

Update expected signatures:

```python
'pnl_monitor': [
    'calculate_pnl',  # Renamed from get_current_pnl
    'get_latest_pnl',  # New read-only method
    'get_pnl_history',  # New read-only method
    'get_cumulative_attribution',  # New read-only method
    'get_pnl_summary',  # New read-only method
    'update_state',
    'get_pnl_attribution'
],
```

### 5.4 Quality Gates Runner

**File**: `scripts/run_quality_gates.py`

Ensure PnL Monitor tests are included in unit test category (already present at line 81).

---

## Phase 6: Add Read-Only Usage Points

### 6.1 Results Store Integration

**File**: `backend/src/basis_strategy_v1/infrastructure/persistence/async_results_store.py`

Add PnL Monitor reference and read-only access:

```python
class AsyncResultsStore:
    def __init__(self, results_dir: str, execution_mode: str, utility_manager=None, pnl_monitor=None):
        # ... existing init ...
        self.pnl_monitor = pnl_monitor
    
    async def _write_timestep_result(self, item: Dict):
        """Write timestep result including P&L data."""
        # ... existing code ...
        
        # Add P&L data if available
        if self.pnl_monitor:
            latest_pnl = self.pnl_monitor.get_latest_pnl()
            if latest_pnl:
                data['pnl'] = latest_pnl
        
        # ... rest of write logic ...
```

### 6.2 Backtest Service Integration

**File**: `backend/src/basis_strategy_v1/core/services/backtest_service.py`

Update to use read-only methods when gathering results:

```python
async def _execute_backtest_sync(self, request_id: str) -> Dict[str, Any]:
    # ... existing execution ...
    
    # Get P&L data without recalculation
    if engine.pnl_monitor:
        latest_pnl = engine.pnl_monitor.get_latest_pnl()
        pnl_history = engine.pnl_monitor.get_pnl_history()
        
        results['latest_pnl'] = latest_pnl
        results['pnl_history'] = pnl_history
```

### 6.3 API Endpoints Integration

**File**: `backend/src/basis_strategy_v1/api/routes/results.py`

Add new read-only P&L endpoints:

```python
@router.get(
    "/{result_id}/pnl/latest",
    summary="Get latest P&L",
    description="Get most recent P&L calculation without recalculating"
)
async def get_latest_pnl(result_id: str, service = Depends(get_backtest_service)):
    engine = service.get_engine(result_id)
    if not engine or not engine.pnl_monitor:
        raise HTTPException(status_code=404, detail="P&L data not available")
    
    latest_pnl = engine.pnl_monitor.get_latest_pnl()
    return StandardResponse(success=True, data=latest_pnl)

@router.get(
    "/{result_id}/pnl/history",
    summary="Get P&L history",
    description="Get historical P&L data"
)
async def get_pnl_history(result_id: str, limit: int = 100, service = Depends(get_backtest_service)):
    engine = service.get_engine(result_id)
    if not engine or not engine.pnl_monitor:
        raise HTTPException(status_code=404, detail="P&L data not available")
    
    pnl_history = engine.pnl_monitor.get_pnl_history(limit=limit)
    return StandardResponse(success=True, data=pnl_history)
```

**File**: `backend/src/basis_strategy_v1/api/routes/live_trading.py`

Update performance endpoint to use read-only methods:

```python
async def get_live_trading_performance(request_id: str, ...):
    # ... existing code ...
    
    # Use read-only P&L access
    if engine.pnl_monitor:
        latest_pnl = engine.pnl_monitor.get_latest_pnl()
        metrics['pnl_data'] = latest_pnl
```

---

## Phase 7: Update Documentation

### 7.1 PnL Monitor Spec

**File**: `docs/specs/04_pnl_monitor.md`

Update Core Methods section (around line 243, 255, 274):

```markdown
### calculate_pnl(current_exposure: Dict, previous_exposure: Optional[Dict] = None, timestamp: pd.Timestamp = None, period_start: pd.Timestamp = None) -> Dict

Explicitly calculate P&L and store results. This method performs full calculation.

### get_latest_pnl() -> Optional[Dict]

Get the most recent P&L result without calculation. O(1) read operation.

### get_pnl_history(limit: int = 100) -> List[Dict]

Get P&L history without calculation. O(n) where n = limit.

### get_cumulative_attribution() -> Dict[str, float]

Get cumulative attribution values without calculation. O(1) read operation.

### get_pnl_summary() -> str

Get formatted summary of latest P&L without calculation. O(1) read operation.
```

Update usage examples (line 1082-1083):

```markdown
- EventDrivenStrategyEngine (full loop): pnl_monitor.calculate_pnl(current_exposure, previous_exposure, timestamp)
- PositionUpdateHandler (tight loop): pnl_monitor.calculate_pnl(current_exposure, previous_exposure, timestamp)
- Results Store (read-only): pnl_monitor.get_latest_pnl()
- API Endpoints (read-only): pnl_monitor.get_latest_pnl()
```

### 7.2 Position Update Handler Spec

**File**: `docs/specs/11_POSITION_UPDATE_HANDLER.md` (Line 254)

````markdown
```python
# OLD:
updated_pnl = self.pnl_monitor.get_current_pnl(
    current_exposure=updated_exposure,
    timestamp=timestamp
)

# NEW:
updated_pnl = self.pnl_monitor.calculate_pnl(
    current_exposure=updated_exposure,
    timestamp=timestamp
)
````

```

### 7.3 Event Driven Strategy Engine Spec

**File**: `docs/specs/15_EVENT_DRIVEN_STRATEGY_ENGINE.md`

Update all method call examples (lines 239, 1039, 1145, 1536):

````markdown
```python
# Calculate P&L (explicit calculation)
pnl = await self.pnl_monitor.calculate_pnl(exposure, risk, self.current_timestamp)

# Read latest P&L (no calculation)
latest_pnl = self.pnl_monitor.get_latest_pnl()
````

```

### 7.4 Results Store Spec

**File**: `docs/specs/18_RESULTS_STORE.md` (Line 598)

```markdown
- pnl_monitor.get_latest_pnl() - Latest P&L metrics (read-only)
- pnl_monitor.get_pnl_history() - Historical P&L data (read-only)
```

### 7.5 Workflow Guide

**File**: `docs/WORKFLOW_GUIDE.md` (Lines 1915, 1938)

```markdown
| **P&L Monitor** | `calculate_pnl()` | Calculate performance | timestamp, trigger_source, market_data | P&L dict |

- **P&L Monitor**: `backend/src/basis_strategy_v1/core/math/pnl_monitor.py:calculate_pnl()`
- **P&L Read Access**: `backend/src/basis_strategy_v1/core/math/pnl_monitor.py:get_latest_pnl()`
```

### 7.6 Code Structure Patterns

**File**: `docs/CODE_STRUCTURE_PATTERNS.md` (Line 646)

````markdown
```python
def calculate_pnl(self, current_exposure: Dict, previous_exposure: Optional[Dict] = None, ...):
    """Explicitly calculate P&L and store results."""
    # Calculation logic
    return pnl_result

def get_latest_pnl(self) -> Optional[Dict]:
    """Get cached P&L result without calculation."""
    return self.latest_pnl_result
````

```

### 7.7 Integration Alignment Report

**File**: `docs/INTEGRATION_ALIGNMENT_REPORT.md` (Lines 160, 166)

```markdown
- `calculate_pnl(...)` - Performs P&L calculation and updates state
- `get_latest_pnl()` - Query current P&L snapshot (read-only)
- `get_pnl_history()` - Query P&L history (read-only)
```

### 7.8 Architecture Analysis

**File**: `pnl_monitor_ARCHITECTURE_ANALYSIS.md`

Update to reflect completed refactor:

```markdown
## STATUS: COMPLETED

The PnL Monitor has been successfully refactored with proper read/calculate separation:

### ✅ Implemented Changes

1. Renamed `get_current_pnl()` → `calculate_pnl()`
2. Added read-only methods:
   - `get_latest_pnl()` - O(1) cached access
   - `get_pnl_history()` - Historical data access
   - `get_cumulative_attribution()` - Attribution data access
   - `get_pnl_summary()` - Formatted summary
3. Updated all 15 code files
4. Updated all 8 documentation files
5. Updated all quality gates
6. Added comprehensive tests
```

---

## Phase 8: Frontend Integration

### 8.1 API Constants

**File**: `frontend/src/utils/constants.ts`

Add new P&L endpoints:

```typescript
export const API_ENDPOINTS = {
  // ... existing endpoints ...
  
  PNL: {
    LATEST: (id: string) => `/results/${id}/pnl/latest`,
    HISTORY: (id: string) => `/results/${id}/pnl/history`,
    ATTRIBUTION: (id: string) => `/results/${id}/pnl/attribution`,
  },
} as const;
```

### 8.2 Performance Dashboard

**File**: `frontend/src/components/live/LivePerformanceDashboard.tsx`

Add hooks for read-only P&L data:

```typescript
const { data: latestPnl } = useQuery({
  queryKey: ['pnl', 'latest', requestId],
  queryFn: () => api.get(API_ENDPOINTS.PNL.LATEST(requestId)),
  refetchInterval: 5000, // Refresh every 5s
});

const { data: pnlHistory } = useQuery({
  queryKey: ['pnl', 'history', requestId],
  queryFn: () => api.get(API_ENDPOINTS.PNL.HISTORY(requestId)),
  refetchInterval: 30000, // Refresh every 30s
});
```

---

## Phase 9: Testing and Validation

### 9.1 Unit Test Coverage

Run all PnL Monitor unit tests:

```bash
pytest tests/unit/test_pnl_monitor_unit.py -v
```

Expected: 100% pass rate with new read-only method tests.

### 9.2 Integration Tests

Run integration tests:

```bash
pytest tests/integration/ -v -k pnl
```

### 9.3 Quality Gates

Run PnL-specific quality gates:

```bash
python scripts/run_quality_gates.py --category unit
python scripts/test_pnl_monitor_separation_quality_gates.py
python scripts/test_component_signature_validation_quality_gates.py
```

Expected: All quality gates pass.

### 9.4 E2E Strategy Tests

Run strategy tests to ensure P&L calculation still works:

```bash
pytest tests/e2e/test_pure_lending_usdt_e2e.py -v
pytest tests/e2e/test_btc_basis_e2e.py -v
```

---

## Phase 10: Migration and Cleanup

### 10.1 Deprecation Period

Keep `get_current_pnl()` as deprecated alias for 2 weeks to allow gradual migration.

### 10.2 Remove Deprecated Method

After 2 weeks, remove the deprecated alias:

```python
# Remove from pnl_monitor.py:
def get_current_pnl(self, *args, **kwargs) -> Dict:
    # DELETE THIS METHOD
```

### 10.3 Final Documentation Update

Update all documentation to remove references to deprecated method.

---

## Success Criteria

- [ ] All 15 code files updated
- [ ] All 8 documentation files updated
- [ ] All 4 quality gate scripts updated
- [ ] Frontend integration complete
- [ ] All unit tests pass (100% coverage)
- [ ] All integration tests pass
- [ ] All quality gates pass
- [ ] Read-only operations < 1ms (O(1))
- [ ] Calculation operations maintain current performance
- [ ] Memory usage increase < 10% for caching
- [ ] No breaking changes for end users

---

## Timeline

- Phase 1-2 (Core + Callers): 2 days
- Phase 3-4 (Tests): 2 days
- Phase 5-6 (Quality Gates + Integration): 2 days
- Phase 7-8 (Documentation + Frontend): 2 days
- Phase 9 (Testing): 1 day
- Phase 10 (Cleanup): 1 day
- **Total: 10 days**

---

## Rollback Plan

If issues arise:

1. Revert `calculate_pnl()` rename → restore `get_current_pnl()`
2. Keep read-only methods (they don't break anything)
3. Revert downstream component changes
4. Restore documentation

Rollback time: < 1 hour using git revert.

### To-dos

- [ ] Phase 1: Update PnL Monitor core - add read-only methods, rename get_current_pnl to calculate_pnl, add caching
- [ ] Phase 2: Update direct callers - EventDrivenStrategyEngine and PositionUpdateHandler
- [ ] Phase 3: Update test scripts - test_pnl_monitor_enhanced.py and test_pnl_monitor_plot.py
- [ ] Phase 4: Update unit tests - add tests for read-only methods in test_pnl_monitor_unit.py
- [ ] Phase 5: Update quality gates - separation, mode-agnostic, component signature, and runner scripts
- [ ] Phase 6: Add read-only usage points - ResultsStore, BacktestService, API endpoints
- [ ] Phase 7: Update all documentation - 8 doc files including specs, guides, and architecture
- [ ] Phase 8: Frontend integration - API constants and performance dashboard
- [ ] Phase 9: Comprehensive testing - unit, integration, quality gates, E2E strategy tests
- [ ] Phase 10: Migration and cleanup - remove deprecated method after transition period