# CONSOLIDATE DUPLICATE RISK MONITORS

## OVERVIEW
There are two identical `risk_monitor.py` files that need to be consolidated:
1. `backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py` (CORRECT LOCATION)
2. `backend/src/basis_strategy_v1/core/rebalancing/risk_monitor.py` (DUPLICATE TO REMOVE)

The correct location is `backend/src/basis_strategy_v1/core/strategies/components/` as this is where the main EventDrivenStrategyEngine imports it from.

## CURRENT USAGE ANALYSIS

### Files Importing from CORRECT Location:
- `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py` (line 28)
- `backend/src/basis_strategy_v1/core/strategies/components/__init__.py` (line 12)

### Files Importing from DUPLICATE Location:
- `backend/src/basis_strategy_v1/core/rebalancing/__init__.py` (line 3)

## CONSOLIDATION PLAN

### Step 1: Update Import in rebalancing/__init__.py
Change the import in `backend/src/basis_strategy_v1/core/rebalancing/__init__.py` from:
```python
from .risk_monitor import RiskMonitor
```
to:
```python
from ..strategies.components.risk_monitor import RiskMonitor
```

### Step 2: Remove Duplicate File
Delete `backend/src/basis_strategy_v1/core/rebalancing/risk_monitor.py`

### Step 3: Verify No Breaking Changes
Ensure all imports still work and no quality gates are broken.

## IMPLEMENTATION REQUIREMENTS

### 1. Update Import Statement
```python
# backend/src/basis_strategy_v1/core/rebalancing/__init__.py
from ..strategies.components.risk_monitor import RiskMonitor
```

### 2. Remove Duplicate File
```bash
rm backend/src/basis_strategy_v1/core/rebalancing/risk_monitor.py
```

### 3. Verify All Imports Work
- EventDrivenStrategyEngine should still import RiskMonitor correctly
- rebalancing module should still have access to RiskMonitor
- All existing functionality should remain intact

## VALIDATION REQUIREMENTS

### 1. Import Validation
- [ ] EventDrivenStrategyEngine can import RiskMonitor from strategies.components
- [ ] rebalancing module can import RiskMonitor from strategies.components
- [ ] No import errors in any files

### 2. Functionality Validation
- [ ] RiskMonitor class works identically to before
- [ ] All methods and properties are accessible
- [ ] No runtime errors

### 3. Quality Gate Validation
- [ ] All existing quality gates still pass
- [ ] No new linting errors introduced
- [ ] Risk monitor tests still pass

## SUCCESS CRITERIA
- [ ] Only one risk_monitor.py file exists (in strategies/components)
- [ ] All imports work correctly
- [ ] No functionality is lost
- [ ] All quality gates continue to pass
- [ ] Code is cleaner with no duplication

## IMPLEMENTATION STEPS

### Step 1: Update Import
```python
# File: backend/src/basis_strategy_v1/core/rebalancing/__init__.py
# Change line 3 from:
from .risk_monitor import RiskMonitor
# To:
from ..strategies.components.risk_monitor import RiskMonitor
```

### Step 2: Remove Duplicate
```bash
# Remove the duplicate file
rm backend/src/basis_strategy_v1/core/rebalancing/risk_monitor.py
```

### Step 3: Test Imports
```python
# Test that imports still work
from backend.src.basis_strategy_v1.core.strategies.components.risk_monitor import RiskMonitor
from backend.src.basis_strategy_v1.core.rebalancing import RiskMonitor as RebalancingRiskMonitor

# Both should be the same class
assert RiskMonitor is RebalancingRiskMonitor
```

## MANDATORY QUALITY GATE VALIDATION

### Before Making Changes:
1. Run existing quality gates to establish baseline
2. Document current passing status

### After Making Changes:
1. **Import Test**: Verify all imports work correctly
2. **Functionality Test**: Ensure RiskMonitor works identically
3. **Quality Gate Test**: Run all existing quality gates
4. **Regression Test**: Ensure no existing functionality is broken

### Quality Gate Commands:
```bash
# Test imports
python -c "from backend.src.basis_strategy_v1.core.strategies.components.risk_monitor import RiskMonitor; print('✅ Import works')"
python -c "from backend.src.basis_strategy_v1.core.rebalancing import RiskMonitor; print('✅ Rebalancing import works')"

# Run risk monitor specific tests
python -m pytest tests/unit/components/test_risk_monitor.py -v

# Run quality gates
python scripts/risk_monitor_quality_gates.py

# Run full test suite to ensure no regressions
python -m pytest tests/ -v
```

## NOTES
- This is a simple consolidation task that should not break any existing functionality
- The two files are identical, so no code changes are needed beyond import updates
- This follows the architectural principle of having components in the correct location (strategies/components)
- The rebalancing module should import from the main component location, not have its own copy
