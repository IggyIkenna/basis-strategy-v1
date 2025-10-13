<!-- 927facc6-a531-4ef0-af0b-debc669a3732 753992de-a935-43a3-964a-b759f9de9e37 -->
# Implementation Gap Resolution Plan

## Objective

Resolve implementation gaps identified in `implementation_gap_report.json` by:

1. Mapping existing methods to canonical specifications (rename approach)
2. Implementing truly missing methods/components
3. Updating all integration points to use canonical method names
4. Validating with quality gates after each component

## Strategy

- **No backward compatibility**: Clean breaks with immediate refactoring of all callers
- **No redundant methods**: Remove old method names after renaming
- **Integration-aware**: Update all component integration points simultaneously
- **Quality-gated progress**: Run quality gates after each major component refactor

---

## Phase 1: Verify Current Implementation Status

### Step 1.1: Audit Existing Implementations

Run the implementation gap quality gate script to get current status:

- `python scripts/test_implementation_gap_quality_gates.py`
- Review `implementation_gap_report.json` to confirm which components actually have implementations
- Cross-check against actual file existence in `backend/src/basis_strategy_v1/`

**Key Question**: The gap report shows Position Monitor as "NEEDS_WORK" but the file exists with 19 methods. Need to verify if the issue is:

- Method naming mismatch (e.g., `calculate_positions` vs `get_real_positions`)
- Missing canonical methods that need to be added
- Both (rename existing + add missing)

---

## Phase 2: Core Component Method Alignment (High Priority)

### Step 2.1: Position Monitor Refactor

**File**: `backend/src/basis_strategy_v1/core/components/position_monitor.py`

**Canonical Methods Required** (from `docs/specs/01_POSITION_MONITOR.md`):

- `get_real_positions(timestamp: pd.Timestamp) -> Dict`
- `get_current_positions() -> Dict`
- `update_state(timestamp: pd.Timestamp, trigger_source: str, execution_deltas: Optional[Dict] = None) -> None`

**Existing Methods to Map**:

- `calculate_positions(timestamp)` → Analyze if this maps to `get_real_positions()`
- `get_all_positions(timestamp)` → Analyze if this maps to `get_current_positions()`
- `get_snapshot(timestamp)` → Determine relationship to canonical methods

**Actions**:

1. Read Position Monitor implementation fully to understand current method behavior
2. Map existing methods to canonical requirements based on functionality
3. Rename methods to canonical names (e.g., `calculate_positions` → `get_real_positions`)
4. Add missing `update_state()` method if not present
5. Update ALL integration points:

- `event_driven_strategy_engine.py` line 546: `position_monitor.get_snapshot()`
- `position_update_handler.py` line 147: `position_monitor.update()`
- Any other callers found via grep

6. Remove old method names completely

**Quality Gate**: Run after completion to verify Position Monitor compliance

### Step 2.2: Exposure Monitor Refactor

**File**: `backend/src/basis_strategy_v1/core/components/exposure_monitor.py`

**Canonical Methods Required** (from `docs/specs/02_EXPOSURE_MONITOR.md`):

- `calculate_exposure(timestamp: pd.Timestamp, position_snapshot: Dict, market_data: Dict) -> Dict`
- `get_current_exposure() -> Dict`

**Existing Methods to Map**:

- `calculate_exposures(positions, timestamp)` → Likely maps to `calculate_exposure()` (note singular vs plural)

**Actions**:

1. Verify method signature compatibility with canonical spec
2. Rename `calculate_exposures` → `calculate_exposure` (singular)
3. Add `get_current_exposure()` if missing
4. Update ALL integration points:

- `event_driven_strategy_engine.py` line 564: `exposure_monitor.calculate_exposures()`
- `position_update_handler.py` line 155: `exposure_monitor.calculate_exposure()`
- Resolve inconsistency between the two callers

5. Remove old method names

**Quality Gate**: Run after completion

### Step 2.3: Risk Monitor Refactor

**File**: `backend/src/basis_strategy_v1/core/components/risk_monitor.py`

**Canonical Methods Required** (from `docs/specs/03_RISK_MONITOR.md`):

- `calculate_risks(timestamp: pd.Timestamp, exposure_data: Dict, market_data: Dict) -> Dict`
- `get_current_risk_metrics() -> Dict`

**Existing Methods to Map**:

- `calculate_risks(exposures, timestamp)` → Already matches canonical name, verify signature

**Actions**:

1. Verify `calculate_risks()` signature matches canonical spec
2. Add `get_current_risk_metrics()` if missing
3. Add `update_state()` if missing
4. Update integration points in Event Engine and other callers
5. Ensure method signatures are consistent

**Quality Gate**: Run after completion

### Step 2.4: Execution Manager Refactor

**File**: `backend/src/basis_strategy_v1/core/execution/execution_manager.py`

**Canonical Methods Required** (from `docs/specs/06_EXECUTION_MANAGER.md`):

- `execute_instruction(instruction_block: Dict, timestamp: pd.Timestamp) -> Dict`
- `get_execution_status(execution_id: str) -> Dict`
- `update_state(timestamp: pd.Timestamp, trigger_source: str, instruction_blocks: Optional[List[Dict]] = None) -> None`

**Existing Methods**:

- `execute_instruction_sequence(instructions, market_data)` → Determine mapping to canonical

**Actions**:

1. Read Execution Manager implementation to understand current behavior
2. Map or create canonical methods
3. Update integration points in Position Update Handler and Event Engine
4. Ensure consistency with Execution Interface Manager calls

**Quality Gate**: Run after completion

---

## Phase 3: Missing Component Implementations (High Priority)

### Step 3.1: Verify Execution Interface Manager Status

**File**: `backend/src/basis_strategy_v1/core/execution/execution_interface_manager.py`

**Status**: File exists but gap report shows missing implementation

**Actions**:

1. Read the file to understand current state
2. Compare against canonical spec `docs/specs/07_EXECUTION_INTERFACE_MANAGER.md`
3. Implement missing canonical methods:

- `route_instruction(instruction: Dict) -> ExecutionInterface`
- `get_execution_interface(venue: str, interface_type: str) -> ExecutionInterface`
- `validate_venue_credentials(venue: str) -> bool`
- `get_supported_venues() -> List[str]`
- `update_state(timestamp: pd.Timestamp, trigger_source: str, **kwargs) -> None`

4. Ensure integration with Execution Manager

**Quality Gate**: Run after completion

### Step 3.2: Strategy Manager Implementation

**File**: `backend/src/basis_strategy_v1/core/components/strategy_manager.py`

**Status**: File does not exist

**Actions**:

1. Check if strategy logic exists elsewhere (e.g., in individual strategy files)
2. Read canonical spec `docs/specs/05_STRATEGY_MANAGER.md`
3. Create Strategy Manager implementation with canonical methods:

- `generate_instructions(timestamp: pd.Timestamp, risk_data: Dict, market_data: Dict) -> List[Dict]`
- `get_current_strategy_state() -> Dict`
- `update_state(timestamp: pd.Timestamp, trigger_source: str, **kwargs) -> List[Dict]`

4. Integrate with Event Engine orchestration
5. Update Event Engine to use Strategy Manager instead of direct strategy calls

**Quality Gate**: Run after completion

### Step 3.3: PnL Calculator Implementation

**File**: `backend/src/basis_strategy_v1/core/components/pnl_calculator.py`

**Status**: File does not exist

**Actions**:

1. Check if PnL logic exists elsewhere
2. Read canonical spec `docs/specs/04_PNL_CALCULATOR.md`
3. Create PnL Calculator implementation with canonical methods:

- `calculate_pnl(timestamp: pd.Timestamp, position_data: Dict, market_data: Dict) -> Dict`
- `get_current_pnl() -> Dict`
- `update_state(timestamp: pd.Timestamp, trigger_source: str, **kwargs) -> None`

4. Integrate with Event Engine orchestration

**Quality Gate**: Run after completion

---

## Phase 4: Integration Point Reconciliation

### Step 4.1: Event Engine Integration Update

**File**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py`

**Actions**:

1. Update all component method calls to use canonical method names
2. Update `_process_timestep()` method (line 534+) to use:

- `position_monitor.get_current_positions()` instead of `get_snapshot()`
- `exposure_monitor.calculate_exposure()` instead of `calculate_exposures()`

3. Verify orchestration sequence follows canonical pattern
4. Ensure all components receive correct parameters

**Quality Gate**: Run backtest quality gates

### Step 4.2: Position Update Handler Integration Update

**File**: `backend/src/basis_strategy_v1/core/components/position_update_handler.py`

**Actions**:

1. Update `handle_position_update()` method (line 111+) to use canonical method names
2. Replace `position_monitor.update()` with `position_monitor.update_state()`
3. Replace `exposure_monitor.calculate_exposure()` signature to match canonical
4. Update risk monitor calls
5. Ensure tight loop sequence uses canonical methods

**Quality Gate**: Run tight loop quality gates

### Step 4.3: Strategy-Specific Integration Updates

**Files**: Individual strategy implementations

**Actions**:

1. Search for any direct component method calls in strategy files
2. Update to use canonical method names
3. Ensure strategies work with Strategy Manager abstraction

---

## Phase 5: Quality Gate Validation

### Step 5.1: Component-Level Quality Gates

Run quality gates after each component refactor:

- Position Monitor: `python scripts/run_quality_gates.py --category components`
- Exposure Monitor: Same
- Risk Monitor: Same
- Execution components: Same

### Step 5.2: Integration Quality Gates

Run after all integration point updates:

- `python scripts/test_integration_alignment_quality_gates.py`
- Verify 100% integration alignment

### Step 5.3: End-to-End Quality Gates

Run strategy-specific quality gates:

- Pure Lending: `python scripts/test_pure_lending_quality_gates.py`
- BTC Basis: `python scripts/test_btc_basis_quality_gates.py`
- Target: 75%+ pass rate

### Step 5.4: Implementation Gap Re-validation

Final validation:

- `python scripts/test_implementation_gap_quality_gates.py`
- Target: 100% canonical compliance for refactored components

---

## Success Criteria

1. **Method Alignment**: All core components use canonical method names
2. **No Legacy Methods**: Old method names completely removed
3. **Integration Consistency**: All callers use canonical method names
4. **Quality Gates**: 75%+ pass rate on strategy quality gates
5. **Implementation Compliance**: 100% for Position, Exposure, Risk, Execution components
6. **No Breaking Changes**: Backtest runs successfully end-to-end

---

## Risk Mitigation

1. **Integration Breakage**: Update all callers simultaneously with method renames
2. **Incomplete Mapping**: Verify functionality equivalence before renaming
3. **Quality Regression**: Run quality gates after each component to catch issues early
4. **Missing Methods**: Implement with minimal viable functionality first, enhance later

### To-dos

- [ ] Run implementation gap quality gates and verify which components actually need refactoring vs are already compliant
- [ ] Refactor Position Monitor to use canonical method names (get_real_positions, get_current_positions, update_state) and update all callers
- [ ] Refactor Exposure Monitor to use canonical method names (calculate_exposure singular, get_current_exposure) and update all callers
- [ ] Refactor Risk Monitor to ensure canonical compliance (calculate_risks, get_current_risk_metrics, update_state) and update all callers
- [ ] Refactor Execution Manager to use canonical methods (execute_instruction, get_execution_status, update_state) and update all callers
- [ ] Verify Execution Interface Manager implementation status and implement missing canonical methods if needed
- [ ] Create Strategy Manager component with canonical methods and integrate with Event Engine
- [ ] Create PnL Calculator component with canonical methods and integrate with Event Engine
- [ ] Update Event Engine to use all canonical method names across all component calls
- [ ] Update Position Update Handler to use canonical method names in tight loop sequence
- [ ] Run integration alignment quality gates to verify 100% integration consistency
- [ ] Run strategy-specific quality gates (Pure Lending, BTC Basis) targeting 75%+ pass rate
- [ ] Run final implementation gap quality gates to confirm 100% canonical compliance