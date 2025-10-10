# Fix Async/Await Violations

## Overview
Remove async/await from all internal component methods to comply with ADR-006 Synchronous Component Execution. Keep async ONLY for Event Logger, Results Store, and API entry points.

**Reference**: `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-006 Synchronous Component Execution  
**Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 6 (Async I/O for Non-Critical Path)  
**Reference**: `docs/DEVIATIONS_AND_CORRECTIONS.md` - Lines 38-54 (Async/Await in Component Methods)

## CRITICAL REQUIREMENTS

### 1. Remove Async/Await from Internal Component Methods
- **Position Monitor**: `async def update()` should be synchronous
- **Risk Monitor**: 18 async internal methods need to be synchronous
- **Strategy Manager**: 9 async internal methods need to be synchronous
- **P&L Calculator**: `async def calculate_pnl()` should be synchronous
- **Position Update Handler**: 3 async internal methods need to be synchronous

### 2. Keep Async ONLY for I/O Operations
- **Event Logger**: Keep async for file I/O operations
- **Results Store**: Keep async for database/file operations
- **API Entry Points**: Keep async for BacktestService.run_backtest, LiveTradingService.start_live_trading

## AFFECTED FILES

### Position Monitor
- `backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py:239`
- **Issue**: `async def update()` should be synchronous
- **Fix**: Remove `async` keyword, make method synchronous

### Risk Monitor
- `backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py`
- **Issue**: 18 async internal methods (lines 485,498,598,666,721,742,781,846,887,932,972,1033,1037,1057,1229,1338,1472,1485)
- **Fix**: Remove `async` keyword from all internal methods

### Strategy Manager
- `backend/src/basis_strategy_v1/core/strategies/components/strategy_manager.py`
- **Issue**: 9 async internal methods (lines 492,1061,1085,1160,1219,1271,1298,1311,1343)
- **Fix**: Remove `async` keyword from all internal methods

### P&L Calculator
- `backend/src/basis_strategy_v1/core/math/pnl_calculator.py:194`
- **Issue**: `async def calculate_pnl()` should be synchronous
- **Fix**: Remove `async` keyword, make method synchronous

### Position Update Handler
- `backend/src/basis_strategy_v1/core/strategies/components/position_update_handler.py`
- **Issue**: 3 async internal methods (lines 105,194,240)
- **Fix**: Remove `async` keyword from all internal methods

## IMPLEMENTATION REQUIREMENTS

### 1. Synchronous Component Methods
```python
# ❌ WRONG: Async internal component method
class PositionMonitor:
    async def update(self, timestamp, trigger_source, **kwargs):
        # Internal component logic should be synchronous
        pass

# ✅ CORRECT: Synchronous internal component method
class PositionMonitor:
    def update(self, timestamp, trigger_source, **kwargs):
        # Internal component logic is synchronous
        pass
```

### 2. Keep Async for I/O Operations
```python
# ✅ CORRECT: Keep async for I/O operations
class EventLogger:
    async def log_event(self, event_data):
        # File I/O operations can be async
        await self._write_to_file(event_data)

class ResultsStore:
    async def store_results(self, results):
        # Database operations can be async
        await self._save_to_database(results)

class BacktestService:
    async def run_backtest(self, config):
        # API entry point can be async
        pass
```

### 3. Component Method Signatures
All component methods should follow this pattern:
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs):
    """Synchronous component method."""
    # Use stored references directly
    market_data = self.data_provider.get_data(timestamp)
    position = self.position_monitor.get_current_position() if self.position_monitor else {}
    
    # Synchronous processing
    self._process_data(market_data, position)
```

## VALIDATION REQUIREMENTS

### Component Method Validation
- [ ] All internal component methods are synchronous
- [ ] No `async def` in component internal methods
- [ ] Component methods use direct function calls
- [ ] No `await` calls in component internal methods

### I/O Operation Validation
- [ ] Event Logger keeps async for file I/O
- [ ] Results Store keeps async for database operations
- [ ] API entry points keep async
- [ ] No async/await in component business logic

### Architecture Compliance
- [ ] ADR-006 compliance verified
- [ ] All components follow synchronous execution pattern
- [ ] I/O operations properly isolated to async methods
- [ ] Component chain execution is synchronous

## TESTING REQUIREMENTS

### Unit Tests
- [ ] Test all component methods are synchronous
- [ ] Test component method signatures
- [ ] Test no async/await in component logic
- [ ] Test I/O operations remain async

### Integration Tests
- [ ] Test component chain execution
- [ ] Test event logger async operations
- [ ] Test results store async operations
- [ ] Test API entry point async operations

## SUCCESS CRITERIA
- [ ] All internal component methods are synchronous
- [ ] No async/await in component business logic
- [ ] Event Logger, Results Store, and API entry points keep async
- [ ] ADR-006 compliance achieved
- [ ] Component chain execution is synchronous
- [ ] All TODO-REFACTOR comments for async/await resolved
- [ ] No regressions in component functionality

## IMPLEMENTATION CHECKLIST

### Phase 1: Identify All Async Methods
- [ ] Scan all component files for `async def`
- [ ] Categorize methods as internal vs I/O
- [ ] Create list of methods to convert to synchronous

### Phase 2: Convert Internal Methods
- [ ] Remove `async` keyword from internal methods
- [ ] Remove `await` calls from internal methods
- [ ] Update method signatures
- [ ] Test method functionality

### Phase 3: Verify I/O Operations
- [ ] Ensure Event Logger keeps async
- [ ] Ensure Results Store keeps async
- [ ] Ensure API entry points keep async
- [ ] Test I/O operations work correctly

### Phase 4: Testing and Validation
- [ ] Run unit tests for all components
- [ ] Run integration tests
- [ ] Verify ADR-006 compliance
- [ ] Check for regressions

## RELATED TASKS
- `strategy_manager_refactor.md` - Strategy Manager refactor may affect async methods
- `13_singleton_pattern_requirements.md` - Singleton pattern affects component initialization
- `10_tight_loop_architecture_requirements.md` - Tight loop architecture affects component execution
