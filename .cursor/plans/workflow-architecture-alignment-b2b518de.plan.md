<!-- b2b518de-a74e-44cf-bc7a-8804ac1da201 c3f0708d-b7d7-45fe-a7b5-a9328c1ede02 -->
# Workflow Architecture Alignment Plan

## Overview

Align WORKFLOW_GUIDE.md with actual implementation and architectural decisions. Fix 10 critical conflicts between documentation and code.

## Phase 1: Execution Architecture Refactor (Issues 1, 2, 3)

### Architecture Decision

- **Keep**: VenueManager as orchestrator (processes List[Order] → List[Trade])
- **Keep**: VenueInterfaceManager as router (routes Orders to execution interfaces)
- **Fix**: Remove duplicate tight loop logic from VenueManager
- **Fix**: Position Monitor calls position interfaces DIRECTLY (not through VenueManager)
- **Credentials**: VenueInterfaceFactory remains single source (loads once, creates both execution and position interfaces)

### 1.1 Update VenueManager

**File**: `backend/src/basis_strategy_v1/core/execution/execution_manager.py`

**Changes**:

- Remove `_execute_venue_loop()` method (tight loop duplication)
- Remove `_verify_reconciliation()` method (tight loop duplication)
- Keep `_execute_venue_loop()` ONLY as orchestrator that:
  - Receives `List[Order]` from strategy
  - Processes orders sequentially
  - Routes each order to VenueInterfaceManager
  - Triggers PositionUpdateHandler for tight loop after each order
  - Returns `List[Trade]`
- Remove async from internal methods (keep only for I/O)
- Update to query data with timestamp (not pass market_data around)

### 1.2 Update VenueInterfaceManager

**File**: `backend/src/basis_strategy_v1/core/execution/venue_interface_manager.py`

**Changes**:

- Keep routing logic for Orders → execution interfaces
- Remove any tight loop orchestration
- Remove async from internal routing methods
- Route ONLY to execution interfaces (not position interfaces)
- Update to query data with timestamp

### 1.3 Update Position Monitor

**File**: `backend/src/basis_strategy_v1/core/components/position_monitor.py`

**Changes**:

- Ensure position_interfaces injected at init from VenueInterfaceFactory
- `get_real_positions()` calls position interfaces DIRECTLY
- Remove any routing through VenueManager/VenueInterfaceManager
- Keep clean separation: simulated vs real positions

### 1.4 Update EventDrivenStrategyEngine

**File**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py`

**Changes**:

- Initialize VenueInterfaceFactory ONCE
- Create execution interfaces → inject into VenueManager
- Create position interfaces → inject into Position Monitor
- Remove `_trigger_tight_loop()` method (PositionUpdateHandler owns this)
- Update component initialization sequence

## Phase 2: Tight Loop Consolidation (Issue 2, 5)

### 2.1 PositionUpdateHandler as ONLY Tight Loop Owner

**File**: `backend/src/basis_strategy_v1/core/components/position_update_handler.py`

**Changes**:

- Keep `_execute_tight_loop()` as THE tight loop implementation
- Sequence: position_monitor → exposure_monitor → risk_monitor → pnl_monitor
- Reconciliation happens HERE (not in VenueManager)
- VenueManager just calls `position_update_handler.update_state()` after each Order execution

### 2.2 Remove Tight Loop from VenueManager

**File**: `backend/src/basis_strategy_v1/core/execution/execution_manager.py`

**Changes**:

- Delete `_execute_venue_loop()` tight loop logic
- Delete `_verify_reconciliation()` method
- Keep ONLY: process Order → route → trigger PositionUpdateHandler → get Trade result

### 2.3 Remove Tight Loop from EventDrivenStrategyEngine

**File**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py`

**Changes**:

- Delete `_trigger_tight_loop()` method (lines 790-819)
- All tight loop orchestration happens in PositionUpdateHandler

## Phase 3: Position Monitor Simulation Pattern (Issue 6)

### 3.1 Implement Simulated vs Real Position Pattern

**File**: `backend/src/basis_strategy_v1/core/components/position_monitor.py`

**Changes**:

- Add `simulated_positions` state (what execution manager thinks positions are)
- Add `real_positions` state (what actual venues report)
- `update_state(timestamp, 'execution_manager', changes)`:
  - Updates `simulated_positions` with expected changes
  - In BOTH backtest and live mode
- `update_state(timestamp, 'position_refresh', None)`:
  - Queries real positions via position interfaces
  - Updates `real_positions`
  - In backtest: real = simulated (always match)
  - In live: real = actual venue query

### 3.2 Reconciliation Component Integration

**File**: `backend/src/basis_strategy_v1/core/components/reconciliation_component.py`

**Changes**:

- `reconcile_position()` compares:
  - `position_monitor.simulated_positions` (expected)
  - `position_monitor.real_positions` (actual)
- In backtest: always matches (skip reconciliation)
- In live: flag discrepancies

### 3.3 Update PositionUpdateHandler

**File**: `backend/src/basis_strategy_v1/core/components/position_update_handler.py`

**Changes**:

- Remove mode-specific logic (lines 246-262)
- Always call: `position_monitor.update_state(timestamp, 'execution_manager', changes)`
- Then call: `position_monitor.update_state(timestamp, 'position_refresh', None)`
- Let position monitor handle mode-specific behavior internally
- Reconciliation compares simulated vs real

## Phase 4: Data Query Pattern Enforcement (Issue 7)

### 4.1 Remove market_data Parameter Passing

**Files**:

- `execution_manager.py`
- `position_update_handler.py`
- `venue_interface_manager.py`

**Changes**:

- Remove `market_data` as method parameter
- All components query: `market_data = self.data_provider.get_data(timestamp)`
- No caching of market_data across timestamps
- Follow Shared Clock Pattern (ADR-004)

### 4.2 Update All Component Methods

**Pattern**:

```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs):
    # Query data with timestamp (not passed as parameter)
    market_data = self.data_provider.get_data(timestamp)
    # Use market_data locally
```

## Phase 5: Transfer Architecture Cleanup (Issue 9)

### 5.1 Merge WalletTransferExecutor into TransferExecutionInterface

**Files**:

- `backend/src/basis_strategy_v1/core/interfaces/transfer_execution_interface.py`
- `backend/src/basis_strategy_v1/core/execution/wallet_transfer_executor.py` (DELETE)

**Changes**:

- Merge wallet transfer logic from WalletTransferExecutor into TransferExecutionInterface
- TransferExecutionInterface handles ALL transfer types:
  - Wallet-to-venue transfers
  - Venue-to-venue transfers
  - Cross-chain transfers
- Delete `wallet_transfer_executor.py`

### 5.2 Remove CrossVenueTransferManager References

**Files**:

- `docs/WORKFLOW_GUIDE.md` (line 2072)
- `backend/src/basis_strategy_v1/core/interfaces/transfer_execution_interface.py` (lines 5, 58)
- `tests/unit/test_transfer_execution_interface_unit.py` (lines 64, 105, 135, 164, 246, 264, 280, 342, 373)

**Changes**:

- Remove all references to `CrossVenueTransferManager`
- Update tests to test `TransferExecutionInterface` directly
- Update docs to describe single transfer interface

## Phase 6: Async Pattern Cleanup (Issue 10)

### 6.1 Remove Async from Internal Methods

**Files**:

- `execution_manager.py`
- `venue_interface_manager.py`

**Changes**:

- Remove `async def` from `_execute_venue_loop()`, `_send_instruction()`, internal routing methods
- Keep `async` ONLY for:
  - External API entry points
  - I/O operations (Event Logger, Results Storage)
- Use synchronous execution for component chain

### 6.2 Update Method Signatures

**Pattern**:

```python
# BEFORE (wrong)what abou
async def _send_instruction(self, instruction: Dict, market_data: Dict) -> Dict:

# AFTER (correct)
def _send_instruction(self, instruction: Dict, timestamp: pd.Timestamp) -> Dict:
    market_data = self.data_provider.get_data(timestamp)
```

## Phase 7: Comprehensive Documentation Updates (ALL AFFECTED FILES)

### 7.1 Update WORKFLOW_GUIDE.md

**File**: `docs/WORKFLOW_GUIDE.md`

**Changes**:

- **Lines 1756-1760, 2064-2066**: Delete and replace with VenueManager vs VenueInterfaceManager architecture
- **Lines 1822-1846**: Delete old tight loop definition, replace with PositionUpdateHandler-only pattern
- **Lines 1929-2030**: Verify P&L Monitor mode-agnostic changes completed
- **Lines 2069-2099**: Delete CrossVenueTransferManager section entirely, replace with TransferExecutionInterface
- **Line 236**: Delete old signature, replace with correct position_monitor.update_state() signature
- **Lines 916-925**: Delete any market_data passing examples, replace with timestamp query pattern
- **Section 1.2 (lines 32-41)**: Add execution architecture diagram
- **Section 3 (lines 172-202)**: Update workflow trigger types to reflect architecture
- **Section 5 (lines 439-597)**: Update external API workflows for new architecture
- **Section 8 (lines 974-1178)**: Update internal system workflows for tight loop
- **Section 14 (lines 1618-1817)**: Update component-to-component workflows
- **Section 15 (lines 1819-1923)**: Replace entire tight loop section
- **Delete ALL references to**: CrossVenueTransferManager, old tight loop pattern, async internal methods

### 7.2 Update VENUE_ARCHITECTURE.md

**File**: `docs/VENUE_ARCHITECTURE.md`

**Changes**:

- **Section "Three-Way Venue Interaction"**: Update with position interface pattern
- **Section "Execution Interface Architecture"**: Delete async method examples
- **Section "Position Interface Creation"**: Add new section for direct calling pattern
- **Section "Credential Management"**: Clarify VenueInterfaceFactory as single source
- **Delete ALL references to**: CrossVenueTransferManager, execution manager (use VenueManager), async internal methods

### 7.3 Update REFERENCE_ARCHITECTURE_CANONICAL.md

**File**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`

**Changes**:

- **ADR-002 (Tight Loop)**: Delete old definition, replace with PositionUpdateHandler ownership
- **ADR-058 (Order/Trade)**: Add clarification that position queries NOT part of Order/Trade
- **Section 4 (Synchronous Execution)**: Delete async internal method examples
- **Section 5 (Mode-Aware Behavior)**: Verify position monitor simulated vs real pattern
- **Section 8 (Three-Way Venue Interaction)**: Update with position interface direct calling
- **Section II (Config-Driven Architecture)**: Update component interaction examples
- **Delete ALL references to**: Old tight loop pattern, async internal methods, execution manager (use VenueManager)

### 7.4 Update ARCHITECTURAL_DECISION_RECORDS.md

**File**: `docs/ARCHITECTURAL_DECISION_RECORDS.md`

**Changes**:

- **ADR-001**: Delete old position interface factory language, replace with VenueInterfaceFactory pattern
- **ADR-002**: Delete entire ADR, rewrite with PositionUpdateHandler as tight loop owner
- **ADR-004 (Shared Clock)**: Add examples showing data query pattern (not passing market_data)
- **ADR-006 (Synchronous Execution)**: Delete async internal method examples
- **ADR-058 (Order/Trade)**: Add section: "Position Queries Separate from Order/Trade System"
- **New ADR-059**: "Position Monitor Simulated vs Real Pattern" (add new ADR)
- **Delete ALL references to**: Old tight loop definitions, CrossVenueTransferManager, execution manager terminology

### 7.5 Update Component Specs (ALL 11 SPECS)

**Files**:

- `docs/specs/01_POSITION_MONITOR.md`
- `docs/specs/02_EXPOSURE_MONITOR.md`
- `docs/specs/03_RISK_MONITOR.md`
- `docs/specs/04_pnl_monitor.md`
- `docs/specs/05_STRATEGY_MANAGER.md`
- `docs/specs/06_VENUE_MANAGER.md`
- `docs/specs/07_VENUE_INTERFACE_MANAGER.md`
- `docs/specs/08_EVENT_LOGGER.md`
- `docs/specs/09_DATA_PROVIDER.md`
- `docs/specs/10_RECONCILIATION_COMPONENT.md`
- `docs/specs/11_POSITION_UPDATE_HANDLER.md`
- `docs/specs/18_RESULTS_STORE.md`

**Changes for EACH spec**:

- **Section 4 (Component References)**: Update to reflect new architecture
- **Section 7 (Data Provider Queries)**: Delete market_data passing, replace with timestamp queries
- **Section 8 (Core Methods)**: Update method signatures to remove async from internal methods
- **Section 10 (Mode-Aware Behavior)**: Update examples for new patterns
- **Section 14 (Integration Points)**: Update Called BY/Calls TO sections
- **Delete ALL references to**: CrossVenueTransferManager, old tight loop, async internal methods, market_data parameters

**Specific updates per spec**:

- **01_POSITION_MONITOR.md**: Add simulated vs real position pattern, position interface direct calling
- **06_VENUE_MANAGER.md**: Replace with Order/Trade processing, remove tight loop
- **07_VENUE_INTERFACE_MANAGER.md**: Execution interface routing only, no position routing
- **11_POSITION_UPDATE_HANDLER.md**: Emphasize as ONLY tight loop owner
- **10_RECONCILIATION_COMPONENT.md**: Update to compare simulated vs real positions

### 7.6 Update Configuration Documentation

**File**: `docs/specs/19_CONFIGURATION.md`

**Changes**:

- Update VenueManager configuration examples
- Remove any CrossVenueTransferManager config references
- Update execution interface configuration patterns
- Add position interface configuration patterns
- Delete ALL references to: CrossVenueTransferManager, old tight loop config

### 7.7 Update All Other Documentation Files

**Files to search and update**:

- `docs/MODES.md`
- `docs/DEPLOYMENT_GUIDE.md`
- `docs/USER_GUIDE.md`
- `docs/API_DOCUMENTATION.md`
- `docs/GETTING_STARTED.md`
- `docs/QUALITY_GATES.md`
- `docs/CODE_STRUCTURE_PATTERNS.md`
- `docs/DEVIATIONS_AND_CORRECTIONS.md`
- `docs/TARGET_REPOSITORY_STRUCTURE.md`
- `docs/COMPONENT_SPECS_INDEX.md`

**Pattern for each file**:

- Search for: "CrossVenueTransferManager", "execution manager" (should be VenueManager), "tight loop" (verify correct definition), "async def" in internal methods, "market_data" as parameter
- Delete old references entirely
- Replace with correct architecture patterns
- Ensure consistency with canonical sources

### 7.8 Update ALL README Files

**Files**:

- `README.md` (root)
- `backend/README.md`
- `tests/README.md`
- `docs/README.md`
- `scripts/README.md`
- Any other README files in subdirectories

**Changes**:

- Update architecture diagrams
- Update component descriptions
- Delete references to removed components/patterns
- Ensure consistency with REFERENCE_ARCHITECTURE_CANONICAL.md

### 7.9 Update Docstrings in ALL Code Files

**Pattern**:

- Search ALL .py files for docstrings containing: "CrossVenueTransferManager", "execution manager", "tight loop", "async" internal methods, "market_data" parameters
- Delete incorrect docstrings entirely
- Replace with correct architecture documentation
- Ensure all docstrings match component spec "Purpose" sections

**Files to check** (run grep across entire codebase):

- All files in `backend/src/basis_strategy_v1/core/`
- All files in `backend/src/basis_strategy_v1/infrastructure/`
- All test files
- All script files

## Phase 8: Test Updates

### 8.1 Update Unit Tests

**Files**:

- `tests/unit/test_execution_manager_unit.py`
- `tests/unit/test_venue_interface_manager_unit.py`
- `tests/unit/test_position_monitor_unit.py`
- `tests/unit/test_position_update_handler_unit.py`
- `tests/unit/test_transfer_execution_interface_unit.py`

**Changes**:

- Test VenueManager Order → Trade processing
- Test VenueInterfaceManager routing (execution interfaces only)
- Test Position Monitor simulated vs real position pattern
- Test Position Monitor direct position interface calls
- Test PositionUpdateHandler as tight loop owner
- Update transfer tests (remove CrossVenueTransferManager mocks)

### 8.2 Update Integration Tests

**Files**:

- `tests/integration/test_tight_loop_reconciliation.py`
- `tests/integration/test_execution_flow.py`

**Changes**:

- Test full Order → Trade → PositionUpdate → Reconciliation flow
- Test position interface direct calling in live mode
- Test reconciliation comparing simulated vs real positions

## Phase 9: Quality Gate Updates

### 9.1 Create Workflow Architecture Quality Gate

**File**: `scripts/test_workflow_architecture_quality_gates.py`

**Validations**:

- VenueManager processes List[Order] → List[Trade]
- VenueInterfaceManager routes to execution interfaces only
- Position Monitor calls position interfaces directly
- PositionUpdateHandler is ONLY tight loop owner
- No async in internal component methods (except I/O)
- No market_data passed as parameters
- Data queried with timestamp
- TransferExecutionInterface is single transfer handler
- No CrossVenueTransferManager references

### 9.2 Update Existing Quality Gates

**Files**:

- `scripts/test_implementation_gap_quality_gates.py`
- `scripts/test_mode_agnostic_design_quality_gates.py`

**Changes**:

- Add checks for execution architecture pattern
- Add checks for position interface pattern
- Add checks for data query pattern

## Phase 10: Integration and Validation

### 10.1 Run All Tests

- Unit tests (80%+ coverage requirement)
- Integration tests
- Quality gates (all must pass)

### 10.2 Run Backtest Validation

- Pure lending mode backtest
- BTC basis mode backtest
- Verify Order/Trade flow works
- Verify tight loop works
- Verify position reconciliation works

### 10.3 Documentation Review

- All docs consistent (no conflicts)
- WORKFLOW_GUIDE matches implementation
- ADRs reflect actual architecture
- Component specs match code

## Success Criteria

### Code Architecture

- ✅ VenueManager processes List[Order] → List[Trade]
- ✅ VenueInterfaceManager routes to execution interfaces only
- ✅ Position Monitor calls position interfaces directly
- ✅ PositionUpdateHandler is ONLY tight loop owner
- ✅ VenueInterfaceFactory loads credentials once for both interface types
- ✅ No async in internal component methods (except I/O)
- ✅ All components query data with timestamp (no passing market_data)

### Transfer Architecture

- ✅ TransferExecutionInterface is single transfer handler
- ✅ WalletTransferExecutor deleted and merged
- ✅ No CrossVenueTransferManager references

### Position Pattern

- ✅ Position Monitor maintains simulated vs real positions
- ✅ Reconciliation compares simulated vs real
- ✅ Backtest: real always equals simulated
- ✅ Live: real queried from venues via position interfaces

### Documentation

- ✅ WORKFLOW_GUIDE.md matches implementation (no conflicts)
- ✅ All ADRs updated and consistent
- ✅ Component specs match code
- ✅ VENUE_ARCHITECTURE.md updated

### Testing

- ✅ All unit tests pass (80%+ coverage)
- ✅ All integration tests pass
- ✅ All quality gates pass
- ✅ Backtest validation passes

## Files Modified Summary

**Backend Code** (~15 files):

- execution_manager.py (refactor)
- venue_interface_manager.py (refactor)
- position_monitor.py (add simulated vs real pattern)
- position_update_handler.py (remove mode-specific logic)
- event_driven_strategy_engine.py (update initialization)
- transfer_execution_interface.py (merge wallet transfer)
- wallet_transfer_executor.py (DELETE)
- reconciliation_component.py (update for simulated vs real)

**Documentation** (~6 files):

- WORKFLOW_GUIDE.md (major updates)
- VENUE_ARCHITECTURE.md (updates)
- REFERENCE_ARCHITECTURE_CANONICAL.md (clarifications)
- ARCHITECTURAL_DECISION_RECORDS.md (updates)
- Component specs (4-5 files)

**Tests** (~8 files):

- Unit tests (5 files)
- Integration tests (2 files)
- Quality gates (1 new + 2 updated)

**Total**: ~30 files