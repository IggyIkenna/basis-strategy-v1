<!-- 60da519d-b4ad-42cd-88b7-5fd89375061f c202acda-fbbf-4630-9222-194c880c2d74 -->
# Position Monitor Live Integration

## Context

Position Monitor currently only simulates positions in backtest mode. Live trading requires real position data from venue APIs. This plan extends the Execution Interface Factory to create position monitoring interfaces, maintaining canonical factory pattern consistency and DRY principles.

## Architecture Decision

**Decision**: Extend Execution Interface Factory to create position monitoring interfaces rather than creating a separate Position Interface Factory.

**Rationale**:

- Same credentials (API keys, endpoints) as execution interfaces
- Same venues (from `configs/modes/*.yaml`) as execution
- Maintains canonical factory pattern consistency
- Avoids credential management duplication

## Implementation Strategy

### Phase 1: Documentation Updates (2-3 days)

Update architectural documentation to reflect position interface patterns:

**Files to Update**:

- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Add Position Interface Factory section under Execution Interface Factory, update initialization sequence
- `docs/specs/07B_EXECUTION_INTERFACES.md` - Add position monitoring interface methods (`create_position_interface`, `get_position_interfaces`)
- `docs/specs/01_POSITION_MONITOR.md` - Update initialization to include position interfaces, document live position monitoring integration
- `docs/WORKFLOW_GUIDE.md` - Update initialization sequence and add position interface creation workflow
- `docs/TARGET_REPOSITORY_STRUCTURE.md` - Add position interface files structure under `core/interfaces/`
- `docs/ARCHITECTURAL_DECISION_RECORDS.md` - Add ADR-001 for Position Monitor Live Integration Architecture

### Phase 2: Position Interface Implementation (5-7 days)

Implement position monitoring interfaces:

**New Files**:

1. `backend/src/basis_strategy_v1/core/interfaces/base_position_interface.py`

- Base class with methods: `get_positions()`, `get_balance()`, `get_position_history()`

2. `backend/src/basis_strategy_v1/core/interfaces/cex_position_interface.py`

- CEX-specific position monitoring (Binance, Bybit, OKX)

3. `backend/src/basis_strategy_v1/core/interfaces/onchain_position_interface.py`

- OnChain-specific position monitoring (AAVE, Morpho, Lido, EtherFi)

**Extended Files**:

1. `backend/src/basis_strategy_v1/core/interfaces/execution_interface_factory.py`

- Add `create_position_interface(venue, execution_mode, config)` method
- Add `get_position_interfaces(venues, execution_mode, config)` method

2. `backend/src/basis_strategy_v1/core/components/position_monitor.py`

- Add `execution_interface_factory` parameter to `__init__`
- Create position interfaces for enabled venues
- Update `get_real_positions()` to use position interfaces in live mode
- Maintain backtest simulation for code symmetry

3. `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py`

- Reorder initialization: Execution Interface Factory before Position Monitor
- Pass Execution Interface Factory to Position Monitor

### Phase 3: Testing and Integration (3-4 days)

**Unit Tests** (80%+ coverage):

- `tests/unit/test_position_interfaces.py` - Position interface creation and initialization
- `tests/unit/test_execution_interface_factory_position.py` - Factory extension tests
- `tests/unit/test_position_monitor_live_integration.py` - Position Monitor with live interfaces

**Integration Tests** (100% coverage):

- `tests/integration/test_position_monitor_live_workflow.py` - End-to-end position monitoring workflow
- `tests/integration/test_execution_interface_factory_extensions.py` - Factory position interface creation

**Quality Gates**:

- Update `scripts/test_implementation_gap_quality_gates.py` to include position interface methods
- Add position interface compliance checks

### Phase 4: Validation and Deployment (2-3 days)

Run comprehensive validation:

1. Run implementation gap quality gates
2. Run integration alignment quality gates
3. Run strategy-specific quality gates
4. Validate canonical compliance (100% compliance score)
5. Deploy and monitor

## Success Criteria

- 100% canonical compliance score for all updated components
- 80%+ unit test coverage, 100% integration test coverage
- All quality gates pass
- Position Monitor successfully integrates with venue APIs in live mode
- Backtest mode maintains simulation functionality

## Configuration Requirements

**No new config parameters needed** - uses existing venue configuration from `configs/modes/*.yaml` and existing credentials from execution interfaces.

## Risk Mitigation

- Reuse existing credential management patterns
- Implement proper rate limiting and retry logic
- Comprehensive error handling for venue API failures
- Maintain existing backtest functionality
- Optimize position interface creation and management

## Timeline

- Phase 1: 2-3 days (documentation)
- Phase 2: 5-7 days (core implementation)
- Phase 3: 3-4 days (testing and integration)
- Phase 4: 2-3 days (validation and deployment)

**Total**: 12-17 days for complete implementation

### To-dos

- [ ] Update architectural documentation (REFERENCE_ARCHITECTURE_CANONICAL.md, execution interfaces spec, position monitor spec, workflow guide, target structure, ADR)
- [ ] Implement base_position_interface.py with core methods (get_positions, get_balance, get_position_history)
- [ ] Implement cex_position_interface.py for CEX position monitoring
- [ ] Implement onchain_position_interface.py for OnChain position monitoring
- [ ] Extend ExecutionInterfaceFactory with create_position_interface and get_position_interfaces methods
- [ ] Update PositionMonitor to use position interfaces (add factory dependency, update get_real_positions, maintain backtest simulation)
- [ ] Update EventDrivenStrategyEngine initialization sequence (factory before position monitor)
- [ ] Implement unit tests for position interfaces, factory extensions, and position monitor integration (80%+ coverage)
- [ ] Implement integration tests for position monitor live workflow and factory extensions (100% coverage)
- [ ] Update quality gates to include position interface compliance checks
- [ ] Run all quality gates, validate canonical compliance, and deploy with monitoring