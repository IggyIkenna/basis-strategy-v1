# Fix Component Data Flow Architecture

## Overview
Update all component specifications to use parameter-based data flow instead of direct component references. Components should pass data as parameters rather than calling other components directly.

**Reference**: `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-003, ADR-004, ADR-005  
**Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 1, 2, 3  
**Reference**: `docs/DEVIATIONS_AND_CORRECTIONS.md` - Lines 193-206 (Component Data Flow Architecture)

## QUALITY GATE
**Quality Gate Script**: `tests/integration/test_data_flow_position_to_exposure.py`
**Validation**: Parameter-based data flow, component isolation, data passing patterns
**Status**: ❌ FAILING

## CRITICAL REQUIREMENTS

### 1. Parameter-Based Data Flow
- **Component Specs**: Update all component specifications to show parameter-based data flow
- **No Direct Component References**: Components should not call other components directly
- **Data as Parameters**: Pass data as parameters between components

### 2. Component Specification Updates
- **All Specs**: Update component specifications to show correct data flow patterns
- **Data Flow Diagrams**: Update flow diagrams to show parameter-based flow
- **Method Signatures**: Update method signatures to show parameter-based flow

## AFFECTED FILES

### Component Specifications
- `docs/specs/01_POSITION_MONITOR.md` - Position monitor specification
- `docs/specs/02_EXPOSURE_MONITOR.md` - Exposure monitor specification
- `docs/specs/03_RISK_MONITOR.md` - Risk monitor specification
- `docs/specs/04_PNL_CALCULATOR.md` - P&L calculator specification
- `docs/specs/05_STRATEGY_MANAGER.md` - Strategy manager specification
- All other component specifications in `docs/specs/`

### Component Implementation
- Components that show direct component references in specifications
- Data flow diagrams that show direct component calls
- Method signatures that show direct component access

## IMPLEMENTATION REQUIREMENTS

### 1. Parameter-Based Data Flow Pattern
```python
# ❌ WRONG: Direct component references in specs
class ExposureMonitor:
    def calculate_exposure(self, timestamp):
        # Direct component call
        positions = self.position_monitor.get_current_positions()
        market_data = self.data_provider.get_data(timestamp)
        return self._calculate_exposure(positions, market_data)

# ✅ CORRECT: Parameter-based data flow
class ExposureMonitor:
    def calculate_exposure(self, positions, market_data, timestamp):
        # Data passed as parameters
        return self._calculate_exposure(positions, market_data)
```

### 2. Component Specification Updates
Update all component specifications to show:
```markdown
## Data Flow Pattern

### Input Parameters
- `positions`: Current position data from position monitor
- `market_data`: Current market data from data provider
- `timestamp`: Current timestamp for data consistency

### Output Data
- `exposure_data`: Calculated exposure data
- `risk_metrics`: Calculated risk metrics

### Data Flow
```
Position Monitor → positions → Exposure Monitor → exposure_data → Risk Monitor
Data Provider → market_data → Exposure Monitor → exposure_data → Risk Monitor
```
```

### 3. Method Signature Updates
```python
# ❌ WRONG: Method signatures showing direct component access
def update_state(self, timestamp, trigger_source, **kwargs):
    positions = self.position_monitor.get_current_positions()
    market_data = self.data_provider.get_data(timestamp)

# ✅ CORRECT: Method signatures showing parameter-based flow
def update_state(self, positions, market_data, timestamp, trigger_source, **kwargs):
    # Data passed as parameters
    pass
```

## COMPONENT SPECIFICATION UPDATES

### 1. Position Monitor Specification
Update `docs/specs/01_POSITION_MONITOR.md`:
```markdown
## Data Flow Pattern

### Input Parameters
- `execution_results`: Results from execution interfaces
- `market_data`: Current market data from data provider
- `timestamp`: Current timestamp for data consistency

### Output Data
- `position_data`: Current position data
- `position_history`: Historical position data

### Data Flow
```
Execution Interfaces → execution_results → Position Monitor → position_data → Exposure Monitor
Data Provider → market_data → Position Monitor → position_data → Exposure Monitor
```
```

### 2. Exposure Monitor Specification
Update `docs/specs/02_EXPOSURE_MONITOR.md`:
```markdown
## Data Flow Pattern

### Input Parameters
- `positions`: Position data from position monitor
- `market_data`: Market data from data provider
- `timestamp`: Current timestamp for data consistency

### Output Data
- `exposure_data`: Calculated exposure data
- `exposure_history`: Historical exposure data

### Data Flow
```
Position Monitor → positions → Exposure Monitor → exposure_data → Risk Monitor
Data Provider → market_data → Exposure Monitor → exposure_data → Risk Monitor
```
```

### 3. Risk Monitor Specification
Update `docs/specs/03_RISK_MONITOR.md`:
```markdown
## Data Flow Pattern

### Input Parameters
- `positions`: Position data from position monitor
- `exposure_data`: Exposure data from exposure monitor
- `market_data`: Market data from data provider
- `timestamp`: Current timestamp for data consistency

### Output Data
- `risk_metrics`: Calculated risk metrics
- `risk_alerts`: Risk alerts and warnings

### Data Flow
```
Position Monitor → positions → Risk Monitor → risk_metrics → Strategy Manager
Exposure Monitor → exposure_data → Risk Monitor → risk_metrics → Strategy Manager
Data Provider → market_data → Risk Monitor → risk_metrics → Strategy Manager
```
```

### 4. P&L Calculator Specification
Update `docs/specs/04_PNL_CALCULATOR.md`:
```markdown
## Data Flow Pattern

### Input Parameters
- `positions`: Position data from position monitor
- `exposure_data`: Exposure data from exposure monitor
- `risk_metrics`: Risk metrics from risk monitor
- `market_data`: Market data from data provider
- `timestamp`: Current timestamp for data consistency

### Output Data
- `pnl_data`: Calculated P&L data
- `attribution_data`: P&L attribution data

### Data Flow
```
Position Monitor → positions → P&L Calculator → pnl_data → Results Store
Exposure Monitor → exposure_data → P&L Calculator → pnl_data → Results Store
Risk Monitor → risk_metrics → P&L Calculator → pnl_data → Results Store
Data Provider → market_data → P&L Calculator → pnl_data → Results Store
```
```

### 5. Strategy Manager Specification
Update `docs/specs/05_STRATEGY_MANAGER.md`:
```markdown
## Data Flow Pattern

### Input Parameters
- `exposure_data`: Exposure data from exposure monitor
- `risk_metrics`: Risk metrics from risk monitor
- `market_data`: Market data from data provider
- `timestamp`: Current timestamp for data consistency

### Output Data
- `execution_instructions`: Strategy execution instructions
- `strategy_decisions`: Strategy decision data

### Data Flow
```
Exposure Monitor → exposure_data → Strategy Manager → execution_instructions → Execution Manager
Risk Monitor → risk_metrics → Strategy Manager → execution_instructions → Execution Manager
Data Provider → market_data → Strategy Manager → execution_instructions → Execution Manager
```
```

## VALIDATION REQUIREMENTS

### Component Specification Validation
- [ ] All component specs show parameter-based data flow
- [ ] No direct component references in specifications
- [ ] Data flow diagrams show parameter-based flow
- [ ] Method signatures show parameter-based flow

### Data Flow Pattern Validation
- [ ] Components receive data as parameters
- [ ] Components output data for other components
- [ ] No direct component method calls
- [ ] Data flows through parameters, not direct calls

### Specification Consistency Validation
- [ ] All specs follow same data flow pattern
- [ ] Data flow diagrams are consistent
- [ ] Method signatures are consistent
- [ ] No conflicting data flow patterns

## TESTING REQUIREMENTS

### Specification Validation Tests
- [ ] Test all component specs show parameter-based flow
- [ ] Test data flow diagrams are accurate
- [ ] Test method signatures are consistent
- [ ] Test no direct component references

### Implementation Validation Tests
- [ ] Test components follow parameter-based flow
- [ ] Test data flows through parameters
- [ ] Test no direct component calls
- [ ] Test data consistency across components

## SUCCESS CRITERIA
- [ ] All component specifications updated to show parameter-based data flow
- [ ] No direct component references in specifications
- [ ] Data flow diagrams show parameter-based flow
- [ ] Method signatures show parameter-based flow
- [ ] All specs follow consistent data flow pattern
- [ ] Data flows through parameters, not direct calls
- [ ] Component specifications are consistent and accurate

## IMPLEMENTATION CHECKLIST

### Phase 1: Audit Current Specifications
- [ ] Review all component specifications
- [ ] Identify direct component references
- [ ] List data flow pattern violations
- [ ] Categorize by component and severity

### Phase 2: Update Component Specifications
- [ ] Update position monitor specification
- [ ] Update exposure monitor specification
- [ ] Update risk monitor specification
- [ ] Update P&L calculator specification
- [ ] Update strategy manager specification
- [ ] Update all other component specifications

### Phase 3: Update Data Flow Diagrams
- [ ] Update data flow diagrams in all specs
- [ ] Ensure parameter-based flow shown
- [ ] Remove direct component references
- [ ] Verify diagram consistency

### Phase 4: Update Method Signatures
- [ ] Update method signatures in all specs
- [ ] Show parameter-based flow
- [ ] Remove direct component access
- [ ] Verify signature consistency

### Phase 5: Testing and Validation
- [ ] Test all specifications are updated
- [ ] Test data flow patterns are consistent
- [ ] Test no direct component references
- [ ] Check for regressions

## RELATED TASKS
- `25_fix_reference_based_architecture_gaps.md` - Reference-based architecture affects data flow
- `14_mode_agnostic_architecture_requirements.md` - Mode-agnostic components need proper data flow
- `10_tight_loop_architecture_requirements.md` - Tight loop architecture affects data flow
