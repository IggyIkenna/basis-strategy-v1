# Position Monitor Live Integration - Comprehensive Implementation Plan

## Overview

This plan implements live position monitoring by extending the Execution Interface Factory to create position monitoring interfaces. This maintains architectural consistency while providing real-time position data for live trading.

## Architectural Decision Record (ADR)

### ADR-001: Position Monitor Live Integration Architecture

**Status**: Proposed  
**Date**: December 2024  
**Context**: Position Monitor currently only simulates positions in backtest mode. Live trading requires real position data from venue APIs.

**Decision**: Extend Execution Interface Factory to create position monitoring interfaces rather than creating a separate Position Interface Factory.

**Rationale**:
- Same credentials (API keys, endpoints) as execution interfaces
- Same venues (from `configs/modes/*.yaml`) as execution
- Same architecture (venue-specific interfaces, error handling, retry logic)
- Maintains canonical factory pattern consistency
- Avoids credential management duplication
- Follows DRY principles

**Consequences**:
- Execution Interface Factory becomes more comprehensive
- Position Monitor initialization depends on Execution Interface Factory
- Initialization order in Event Driven Strategy Engine needs reordering
- Backtest mode maintains simulation for code symmetry

## Required Documentation Updates

### 1. Reference Architecture Canonical Updates

**File**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`

**Updates Needed**:
- Add Position Interface Factory section under Execution Interface Factory
- Update initialization sequence to reflect Position Monitor dependency on Execution Interface Factory
- Add live position monitoring patterns
- Update component reference architecture to include position interfaces

**Key Sections to Update**:
```markdown
### 7. Execution Interface Factory (Extended)

**Position Interface Creation**:
- Creates both execution and position monitoring interfaces
- Uses same credentials and venue configuration
- Handles both backtest (simulation) and live (real API) modes

**Initialization Dependencies**:
- Position Monitor depends on Execution Interface Factory
- Execution Interface Factory must be initialized before Position Monitor
```

### 2. Execution Interface Factory Spec Updates

**File**: `docs/specs/07B_EXECUTION_INTERFACES.md`

**Updates Needed**:
- Add position monitoring interface methods
- Document position interface creation patterns
- Add live vs backtest position monitoring behavior
- Update factory method signatures

**New Methods to Document**:
```markdown
### create_position_interface(venue: str, execution_mode: str, config: Dict) -> BasePositionInterface
### get_position_interfaces(venues: List[str], execution_mode: str, config: Dict) -> Dict[str, BasePositionInterface]
```

### 3. Position Monitor Spec Updates

**File**: `docs/specs/01_POSITION_MONITOR.md`

**Updates Needed**:
- Update initialization to include position interfaces
- Document live position monitoring integration
- Update get_real_positions method to use position interfaces
- Add position interface dependency documentation

**Key Updates**:
```markdown
### Live Position Monitoring Integration

**Position Interface Dependencies**:
- Position Monitor creates position interfaces via Execution Interface Factory
- Each enabled venue gets a position interface
- Position interfaces handle venue-specific API calls

**Initialization Sequence**:
1. Execution Interface Factory initialized first
2. Position Monitor requests position interfaces from factory
3. Position interfaces created with same credentials as execution interfaces
```

### 4. Workflow Guide Updates

**File**: `docs/WORKFLOW_GUIDE.md`

**Updates Needed**:
- Update initialization sequence in Event Driven Strategy Engine
- Document position interface creation workflow
- Add live position monitoring workflow
- Update component dependency graph

**New Workflow Section**:
```markdown
### Position Interface Creation Workflow

1. Event Driven Strategy Engine initializes Execution Interface Factory
2. Execution Interface Factory creates execution interfaces for enabled venues
3. Position Monitor requests position interfaces from Execution Interface Factory
4. Position interfaces created with same credentials and configuration
5. Position Monitor uses interfaces for live position monitoring
```

### 5. Target Repository Structure Updates

**File**: `docs/TARGET_REPOSITORY_STRUCTURE.md`

**Updates Needed**:
- Add position interface files under `core/interfaces/`
- Update interface factory documentation
- Add position interface test structure

**New Files to Document**:
```
backend/src/basis_strategy_v1/core/interfaces/
├── base_position_interface.py
├── cex_position_interface.py
├── onchain_position_interface.py
└── transfer_position_interface.py
```

## Implementation Requirements

### 1. Execution Interface Factory Extensions

**File**: `backend/src/basis_strategy_v1/core/interfaces/execution_interface_factory.py`

**New Methods to Implement**:
```python
@staticmethod
def create_position_interface(venue: str, execution_mode: str, config: Dict[str, Any]) -> BasePositionInterface:
    """Create position monitoring interface for a specific venue."""

@staticmethod
def get_position_interfaces(venues: List[str], execution_mode: str, config: Dict[str, Any]) -> Dict[str, BasePositionInterface]:
    """Create position monitoring interfaces for multiple venues."""
```

### 2. Position Interface Implementations

**New Files to Create**:

#### `backend/src/basis_strategy_v1/core/interfaces/base_position_interface.py`
```python
class BasePositionInterface:
    """Base class for position monitoring interfaces."""
    
    async def get_positions(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Get positions from venue."""
    
    async def get_balance(self, asset: str) -> float:
        """Get balance for specific asset."""
    
    async def get_position_history(self, start_time: pd.Timestamp, end_time: pd.Timestamp) -> List[Dict]:
        """Get position history for time range."""
```

#### `backend/src/basis_strategy_v1/core/interfaces/cex_position_interface.py`
```python
class CEXPositionInterface(BasePositionInterface):
    """CEX position monitoring interface."""
    
    def __init__(self, venue: str, execution_mode: str, config: Dict[str, Any]):
        # Initialize CEX-specific position monitoring
```

#### `backend/src/basis_strategy_v1/core/interfaces/onchain_position_interface.py`
```python
class OnChainPositionInterface(BasePositionInterface):
    """OnChain position monitoring interface."""
    
    def __init__(self, venue: str, execution_mode: str, config: Dict[str, Any]):
        # Initialize OnChain-specific position monitoring
```

### 3. Position Monitor Updates

**File**: `backend/src/basis_strategy_v1/core/components/position_monitor.py`

**Updates Needed**:
- Add position interface initialization in `__init__`
- Update `get_real_positions` to use position interfaces
- Add position interface dependency management
- Maintain backtest simulation for code symmetry

**Key Changes**:
```python
def __init__(self, config: Dict[str, Any], data_provider, utility_manager, execution_interface_factory):
    # Store execution interface factory reference
    self.execution_interface_factory = execution_interface_factory
    
    # Create position interfaces for enabled venues
    self.position_interfaces = {}
    for venue, venue_config in config.get('venues', {}).items():
        if venue_config.get('enabled', False):
            self.position_interfaces[venue] = self.execution_interface_factory.create_position_interface(
                venue, self.execution_mode, config
            )

def get_real_positions(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
    """Get positions from all enabled venues."""
    if self.execution_mode == 'live':
        return self._get_live_positions(timestamp)
    else:  # backtest
        return self._get_simulated_positions(timestamp)
```

### 4. Event Driven Strategy Engine Updates

**File**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py`

**Updates Needed**:
- Reorder initialization sequence
- Initialize Execution Interface Factory before Position Monitor
- Pass Execution Interface Factory to Position Monitor

**New Initialization Order**:
```python
def _initialize_components(self):
    # 1. Initialize Execution Interface Factory first
    self.execution_interface_factory = ExecutionInterfaceFactory()
    
    # 2. Initialize Position Monitor with Execution Interface Factory
    self.position_monitor = PositionMonitor(
        config=self.config,
        data_provider=self.data_provider,
        utility_manager=self.utility_manager,
        execution_interface_factory=self.execution_interface_factory
    )
    
    # 3. Initialize other components...
```

## Testing Requirements

### 1. Unit Tests

**New Test Files**:
- `tests/unit/test_position_interfaces.py`
- `tests/unit/test_execution_interface_factory_position.py`
- `tests/unit/test_position_monitor_live_integration.py`

**Test Coverage Requirements**:
- Position interface creation and initialization
- Live position monitoring functionality
- Backtest simulation maintenance
- Error handling and retry logic
- Credential management integration

### 2. Integration Tests

**New Test Files**:
- `tests/integration/test_position_monitor_live_workflow.py`
- `tests/integration/test_execution_interface_factory_extensions.py`

**Test Scenarios**:
- End-to-end position monitoring workflow
- Execution Interface Factory position interface creation
- Position Monitor initialization with position interfaces
- Live vs backtest mode behavior verification

### 3. Quality Gates

**Updates Needed**:
- Update `scripts/test_implementation_gap_quality_gates.py` to include position interface methods
- Add position interface compliance checks
- Update execution interface factory compliance checks

## Configuration and Environment

**No Changes Required**:
- No new config parameters needed
- No new environment variables required
- Uses existing venue configuration from `configs/modes/*.yaml`
- Uses existing credentials from execution interfaces

## Implementation Phases

### Phase 1: Documentation and Architecture
1. Create ADR-001
2. Update Reference Architecture Canonical
3. Update Execution Interface Factory spec
4. Update Position Monitor spec
5. Update Workflow Guide
6. Update Target Repository Structure

### Phase 2: Core Implementation
1. Implement base position interface
2. Implement CEX position interface
3. Implement OnChain position interface
4. Extend Execution Interface Factory
5. Update Position Monitor

### Phase 3: Integration and Testing
1. Update Event Driven Strategy Engine initialization
2. Implement unit tests
3. Implement integration tests
4. Update quality gates
5. Run comprehensive test suite

### Phase 4: Validation and Deployment
1. Run implementation gap quality gates
2. Run integration alignment quality gates
3. Run strategy-specific quality gates
4. Validate canonical compliance
5. Deploy and monitor

## Success Criteria

1. **Canonical Compliance**: 100% compliance score for all updated components
2. **Test Coverage**: 80%+ unit test coverage, 100% integration test coverage
3. **Architecture Consistency**: All components follow canonical patterns
4. **Documentation Completeness**: All specs updated and consistent
5. **Quality Gates**: All quality gates pass
6. **Live Integration**: Position Monitor successfully integrates with venue APIs
7. **Backtest Compatibility**: Backtest mode maintains simulation functionality

## Risk Mitigation

1. **Credential Security**: Reuse existing credential management patterns
2. **API Rate Limits**: Implement proper rate limiting and retry logic
3. **Error Handling**: Comprehensive error handling for venue API failures
4. **Backward Compatibility**: Maintain existing backtest functionality
5. **Performance**: Optimize position interface creation and management

## Dependencies

- Execution Interface Factory must be implemented and tested
- Position Monitor must be refactored to canonical compliance
- Event Driven Strategy Engine must support new initialization order
- All venue configurations must be properly set up
- Credential management must be secure and tested

## Timeline Estimate

- **Phase 1**: 2-3 days (documentation)
- **Phase 2**: 5-7 days (core implementation)
- **Phase 3**: 3-4 days (testing and integration)
- **Phase 4**: 2-3 days (validation and deployment)

**Total**: 12-17 days for complete implementation

## References

- `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Core architectural principles
- `docs/specs/01_POSITION_MONITOR.md` - Position Monitor specification
- `docs/specs/07B_EXECUTION_INTERFACES.md` - Execution Interface specification
- `docs/WORKFLOW_GUIDE.md` - System workflow documentation
- `docs/TARGET_REPOSITORY_STRUCTURE.md` - Repository structure guide
- `backend/src/basis_strategy_v1/core/interfaces/execution_interface_factory.py` - Current factory implementation
- `backend/src/basis_strategy_v1/core/components/position_monitor.py` - Current Position Monitor implementation
- `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py` - Event Engine implementation
