<!-- e0ecd24f-6c75-4220-97f7-cea4c197dd74 1f2576df-a0df-42a9-9cb8-9b8e81baca15 -->
# Component Spec Standardization v5 - Refined Plan

## Context & Current State

### What Changed Since Original Plan

- **Spec count**: Plan mentioned 19 specs, but **20 spec files** currently exist
- **Partial implementation**: Some specs (10_RECONCILIATION, 11_POSITION_UPDATE_HANDLER, 06/07/08 execution layer) already have basic "Environment Variables" sections
- **File numbering issue**: Two files numbered `16_` (MATH_UTILITIES and RESULTS_STORE), two numbered `08_` (EVENT_LOGGER and EXECUTION_INTERFACES)
- **Current implementation**: EventLogger stores events in memory, exports to CSV. Individual components (ExposureMonitor, RiskMonitor) have separate `.log` files via standard Python logging
- **Health system exists**: 17_HEALTH_ERROR_SYSTEMS.md is comprehensive and documents structured error handling patterns

### Scope Clarification

This plan will:

1. Standardize ALL 20 component specs to 18-section format
2. Add missing sections (Environment Variables, Config Fields, Data Queries) to 15+ specs that lack them
3. **ENHANCE** Event Logging sections to document component-specific log file routing (ideal state, may need implementation)
4. **ENHANCE** Error Codes sections with structured error handling + health integration patterns from 17_HEALTH_ERROR_SYSTEMS.md
5. Fix file numbering conflicts (16_ and 08_ duplicates)
6. Update quality gate validation to enforce 18-section structure

## 18-Section Standard Format

All component specs MUST have these sections in order:

1. **Purpose** - What the component does
2. **Responsibilities** - Specific duties
3. **State** - Internal state variables
4. **Component References (Set at Init)** - What's passed during initialization
5. **Environment Variables** ⭐ NEW/ENHANCE - Which env vars are read
6. **Config Fields Used** ⭐ NEW - Which config fields from strategy mode slice
7. **Data Provider Queries** ⭐ NEW - Which data queries (or "N/A")
8. **Core Methods** - Main API surface
9. **Data Access Pattern** - How it queries data with shared clock
10. **Mode-Aware Behavior** - Backtest vs Live differences
11. **Event Logging Requirements** ⭐ ENHANCED - Separate log files + EventLogger integration
12. **Error Codes** ⭐ ENHANCED - Structured errors + health integration
13. **Quality Gates** - Validation criteria
14. **Integration Points** - How it connects to other components
15. **Code Structure Example** - Implementation template
16. **Related Documentation** - Cross-references

*Note: Specs may have additional domain-specific sections (e.g., "AAVE Conversion Logic" in Exposure Monitor), but these 16 are mandatory.*

## New Section Requirements

### Section 5: Environment Variables

**Template**:

````markdown
## Environment Variables

### System-Level Variables (Read at Initialization)
- `BASIS_EXECUTION_MODE`: backtest | live
  - **Usage**: Determines simulated vs real API behavior
  - **Read at**: Component __init__
  - **Affects**: Mode-aware conditional logic

- `BASIS_ENVIRONMENT`: dev | staging | production
  - **Usage**: Credential routing for venue APIs
  - **Read at**: Component __init__ (if uses external APIs)
  - **Affects**: Which API keys/endpoints to use

- `BASIS_DEPLOYMENT_MODE`: local | docker
  - **Usage**: Port/host configuration
  - **Read at**: Component __init__ (if network calls)
  - **Affects**: Connection strings

- `BASIS_DATA_MODE`: csv | db
  - **Usage**: Data source selection (DataProvider only)
  - **Read at**: DataProvider __init__
  - **Affects**: File-based vs database data loading

### Component-Specific Variables
[List any component-specific env vars, or "None"]

### Environment Variable Access Pattern
```python
def __init__(self, ...):
    # Read env vars ONCE at initialization
    self.execution_mode = os.getenv('BASIS_EXECUTION_MODE', 'backtest')
    # NEVER read env vars during runtime loops
````

### Behavior NOT Determinable from Environment Variables

[List hard-coded behaviors that can't be env-controlled]

````

### Section 6: Config Fields Used
**Template**:
```markdown
## Config Fields Used

### Universal Config (All Components)
- `mode`: str - e.g., 'eth_basis', 'pure_lending'
- `share_class`: str - 'usdt_stable' | 'eth_directional'
- `initial_capital`: float - Starting capital

### Component-Specific Config
- `[field_name]`: [type] - [description]
  - **Usage**: [how component uses this]
  - **Default**: [default value if optional]
  - **Validation**: [constraints]

[Repeat for each config field]

### Config Access Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    # Read config fields (NEVER modify)
    max_leverage = self.config['risk_limits']['max_leverage']
````

### Behavior NOT Determinable from Config

[List hard-coded logic that can't be config-controlled]

````

### Section 7: Data Provider Queries
**Template** (if component queries data):
```markdown
## Data Provider Queries

### Data Types Requested
`data = self.data_provider.get_data(timestamp)`

#### Market Data
- `prices`: Dict[str, float] - Token prices in USD
  - **Tokens needed**: [ETH, USDT, BTC, etc.]
  - **Update frequency**: [real-time | 1min | 5min | 1h]
  - **Usage**: [position valuation | trade sizing]

[Continue for: funding_rates, apy_data, liquidity_index, etc.]

### Query Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    data = self.data_provider.get_data(timestamp)
    prices = data['market_data']['prices']
````

### Data NOT Available from DataProvider

[List external data sources accessed directly, or "None - all data from DataProvider"]

````

**OR** (if no queries):
```markdown
## Data Provider Queries
**N/A** - This component does not directly query DataProvider.
[Optional: Explain how it gets data, e.g., "Receives data from other components"]
````

### Section 11: Event Logging Requirements (ENHANCED)

**Template**:

````markdown
## Event Logging Requirements

### Component Event Log File
**Separate log file** for this component's events:
- **File**: `logs/events/[component_name]_events.jsonl`
- **Format**: JSON Lines (one event per line)
- **Rotation**: Daily rotation, keep 30 days
- **Purpose**: Component-specific audit trail

**11 Main Component Log Files**:
1. `logs/events/position_monitor_events.jsonl`
2. `logs/events/exposure_monitor_events.jsonl`
3. `logs/events/risk_monitor_events.jsonl`
4. `logs/events/pnl_calculator_events.jsonl`
5. `logs/events/strategy_manager_events.jsonl`
6. `logs/events/execution_manager_events.jsonl`
7. `logs/events/execution_interface_manager_events.jsonl`
8. `logs/events/execution_interfaces_events.jsonl`
9. `logs/events/data_provider_events.jsonl`
10. `logs/events/reconciliation_events.jsonl`
11. `logs/events/position_update_handler_events.jsonl`

### Event Logging via EventLogger
All events logged through centralized EventLogger:

```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='[event_type]',
    component='[ComponentName]',
    data={
        'event_specific_data': value,
        'state_snapshot': self.get_state_snapshot()  # optional
    }
)
````

### Events to Log

#### 1. Component Initialization

```python
self.event_logger.log_event(
    timestamp=pd.Timestamp.now(),
    event_type='component_initialization',
    component='[ComponentName]',
    data={
        'execution_mode': self.execution_mode,
        'config_hash': hash(str(self.config))
    }
)
```

#### 2. State Updates (Every update_state() Call)

[Document state update events]

#### 3. Error Events

[Document error logging pattern]

#### 4. Component-Specific Critical Events

[Document component-specific events]

### Event Retention & Output Formats

#### Dual Logging Approach

**Both formats are used**:

1. **JSON Lines (Iterative)**: Write events to component-specific JSONL files during execution

                                                                                                                                                                                                - **Purpose**: Real-time monitoring during backtest runs
                                                                                                                                                                                                - **Location**: `logs/events/[component]_events.jsonl`
                                                                                                                                                                                                - **When**: Events written as they occur (buffered for performance)

2. **CSV Export (Final)**: Comprehensive CSV export at Results Store stage

                                                                                                                                                                                                - **Purpose**: Final analysis, spreadsheet compatibility
                                                                                                                                                                                                - **Location**: `results/[backtest_id]/events.csv`
                                                                                                                                                                                                - **When**: At backtest completion or on-demand

#### Mode-Specific Behavior

- **Backtest**: 
                                                                                                                                - Write JSONL iteratively (allows tracking during long runs)
                                                                                                                                - Export CSV at completion to Results Store
                                                                                                                                - Keep all events in memory for final processing

- **Live**: 
                                                                                                                                - Write JSONL immediately (no buffering)
                                                                                                                                - Rotate daily, keep 30 days
                                                                                                                                - CSV export on-demand for analysis

**Note**: Current implementation stores events in memory and exports to CSV only. Enhanced implementation will add iterative JSONL writing. Reference: `docs/specs/17_HEALTH_ERROR_SYSTEMS.md`

````

### Section 12: Error Codes (ENHANCED)
**Template**:
```markdown
## Error Codes

### Component Error Code Prefix: [PREFIX]
All [ComponentName] errors use the `[PREFIX]` prefix.

### Error Code Registry
**Source**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`

All error codes registered with:
- **code**: Unique error code
- **component**: Component name
- **severity**: CRITICAL | HIGH | MEDIUM | LOW
- **message**: Human-readable error message
- **resolution**: How to resolve

### Component Error Codes

#### [PREFIX]-001: [Error Name] (SEVERITY)
**Description**: [What this error means]
**Cause**: [What causes this error]
**Recovery**: [How to recover]
```python
raise ComponentError(
    error_code='[PREFIX]-001',
    message='Detailed error message',
    component='[ComponentName]',
    severity='CRITICAL'
)
````

[Continue for all error codes...]

### Structured Error Handling Pattern

#### Error Raising

```python
from backend.src.basis_strategy_v1.core.error_codes.exceptions import ComponentError

try:
    result = self._risky_operation(timestamp)
except Exception as e:
    # Log error event
    self.event_logger.log_event(
        timestamp=timestamp,
        event_type='error',
        component='[ComponentName]',
        data={
            'error_code': '[PREFIX]-001',
            'error_message': str(e),
            'stack_trace': traceback.format_exc()
        }
    )
    
    # Raise structured error
    raise ComponentError(
        error_code='[PREFIX]-001',
        message=f'[ComponentName] failed: {str(e)}',
        component='[ComponentName]',
        severity='HIGH',
        original_exception=e
    )
```

#### Error Propagation Rules

- **CRITICAL**: Propagate to health system → trigger app restart
- **HIGH**: Log and retry with exponential backoff (max 3 retries)
- **MEDIUM**: Log and continue with degraded functionality
- **LOW**: Log for monitoring, no action needed

### Component Health Integration

#### Health Check Registration

```python
def __init__(self, ..., health_manager: UnifiedHealthManager):
    # Store health manager reference
    self.health_manager = health_manager
    
    # Register component with health system
    self.health_manager.register_component(
        component_name='[ComponentName]',
        checker=self._health_check
    )

def _health_check(self) -> Dict:
    """Component-specific health check."""
    return {
        'status': 'healthy' | 'degraded' | 'unhealthy',
        'last_update': self.last_update_timestamp,
        'errors': self.recent_errors[-10:],  # Last 10 errors
        'metrics': {
            'update_count': self.update_count,
            'avg_processing_time_ms': self.avg_processing_time,
            'error_rate': self.error_count / max(self.update_count, 1)
        }
    }
```

#### Health Status Definitions

- **healthy**: No errors in last 100 updates, processing time < threshold
- **degraded**: Minor errors, slower processing, retries succeeding
- **unhealthy**: Critical errors, failed retries, unable to process

**Reference**: `docs/specs/17_HEALTH_ERROR_SYSTEMS.md`

````

## Implementation Phases

### Phase 0: File Numbering Cleanup (30 min)
**Issue**: Duplicate file numbers (two `08_` files, two `16_` files)

**Actions**:
1. Rename `08_EXECUTION_INTERFACES.md` → `07A_EXECUTION_INTERFACES.md` (or renumber execution layer)
2. Rename `16_RESULTS_STORE.md` → `18_RESULTS_STORE.md`
3. Update all cross-references in other docs
4. Update COMPONENT_SPECS_INDEX.md

### Phase 1: Update Core Monitoring Components (5 specs, 3-4 hours)
**Components**: 01_POSITION_MONITOR, 02_EXPOSURE_MONITOR, 03_RISK_MONITOR, 04_PNL_CALCULATOR, 05_STRATEGY_MANAGER

**Actions per spec**:
1. Add **Environment Variables** section (new)
2. Add **Config Fields Used** section (new)
3. Add **Data Provider Queries** section (new)
4. **ENHANCE Event Logging Requirements** with component-specific log file + EventLogger integration
5. **ENHANCE Error Codes** with structured error handling + health integration
6. Validate all 18 sections present
7. Ensure section order matches standard

**Validation**:
- All 5 sections present and complete
- EventLogger integration documented
- Health check integration documented
- Component-specific log file documented

### Phase 2: Update Execution Layer Components (5 specs, 3-4 hours)
**Components**: 06_EXECUTION_MANAGER, 07_EXECUTION_INTERFACE_MANAGER, 08_EVENT_LOGGER, 07A_EXECUTION_INTERFACES, 10_RECONCILIATION_COMPONENT, 11_POSITION_UPDATE_HANDLER

**Notes**:
- 06/07/08/10/11 already have basic "Environment Variables" sections - enhance these
- 08_EVENT_LOGGER needs special treatment (it IS the logging system)
- Add all missing sections

**Validation**:
- Environment Variables sections enhanced (not just basic)
- Config Fields documented comprehensively
- Data queries documented

### Phase 3: Update Service Components (4 specs, 2-3 hours)
**Components**: 09_DATA_PROVIDER, 13_BACKTEST_SERVICE, 14_LIVE_TRADING_SERVICE, 15_EVENT_DRIVEN_STRATEGY_ENGINE

**Special considerations**:
- 09_DATA_PROVIDER: "Data Provider Queries" section is "N/A" (it IS the data provider)
- Service components may have different config structure

### Phase 4: Update Supporting Components (5 specs, 2-3 hours)
**Components**: 12_FRONTEND_SPEC, 16_MATH_UTILITIES, 17_HEALTH_ERROR_SYSTEMS, 18_RESULTS_STORE (renamed), CONFIGURATION

**Special considerations**:
- 12_FRONTEND_SPEC: Different environment variables (VITE_*)
- 16_MATH_UTILITIES: Likely no state, simplified sections
- 17_HEALTH_ERROR_SYSTEMS: Already comprehensive, add missing sections
- CONFIGURATION: Meta-component, may need adapted format

### Phase 5: Update Quality Gate Validation (2 hours)

**CRITICAL REQUIREMENT**: All quality gate scripts MUST be integrated into `run_quality_gates.py` to prevent orphaned tests. This is now a cursor rule.

#### Update existing quality gate script:
**File**: `scripts/test_docs_structure_validation_quality_gates.py`

**Changes**:
1. Add 18-section validation (currently checks for basic structure + implementation status)
2. Add REQUIRED_SECTIONS constant with all 18 sections:
   ```python
   REQUIRED_SECTIONS = [
       "Purpose", "Responsibilities", "State",
       "Component References (Set at Init)",
       "Environment Variables",  # NEW
       "Config Fields Used",  # NEW
       "Data Provider Queries",  # NEW
       "Core Methods",
       "Data Access Pattern",
       "Mode-Aware Behavior",
       "Event Logging Requirements",  # Check for component-specific log files
       "Error Codes",  # Check for structured error handling
       "Quality Gates",
       "Integration Points",
       "Code Structure Example",
       "Related Documentation"
   ]
   ```
3. Add validation for:
   - Section order matches standard
   - Event Logging section documents component-specific JSONL files (11 main components)
   - Event Logging section documents dual logging (CSV + JSONL)
   - Error Codes section has structured error handling pattern
   - Error Codes section references health integration
   - Environment Variables section present for all 20 specs
   - Config Fields Used section present for all 20 specs
   - Data Provider Queries section present (or "N/A") for all 20 specs

#### Verify integration in run_quality_gates.py:
- Confirm `test_docs_structure_validation_quality_gates.py` is in 'docs' category (✅ Already integrated)
- Ensure it can be run via: `python scripts/run_quality_gates.py --category docs`
- No new orphaned scripts created

### Phase 6: Update Process Documentation & Agent Specs (2-3 hours)

**Files to update**:
1. **docs/REFACTOR_STANDARD_PROCESS.md**:
   - Add requirement: All specs must have 18 sections in standard order
   - Update Agent 1 requirements: Validate 18-section format
   - Add validation: Environment Variables section documented
   - Add validation: Config Fields Used section documented
   - Add validation: Data Provider Queries section documented (or N/A)
   - Add validation: Separate event log files documented (11 main components)
   - Add validation: Structured error handling documented
   - Add validation: Health integration documented (11 main components)
   - Update success criteria to include 18-section validation
   - Update validation commands for new section checks

2. **Agent Configuration Files** (`.cursor/`):
   - **docs-specs-implementation-status-agent.json**:
     - Update to validate 18 sections present
     - Add checks for new sections (Environment Variables, Config Fields, Data Queries)
     - Validate section order matches standard
   
   - **docs-consistency-agent.json**:
     - Update to check cross-references in new sections
     - Validate template consistency across all 20 specs
     - Check Event Logging section references 17_HEALTH_ERROR_SYSTEMS.md
   
   - **docs-logical-inconsistency-agent.json**:
     - Update to detect inconsistencies in new sections
     - Check Environment Variables documented consistently
     - Validate Config Fields align with actual config YAMLs
     - Check Data Provider Queries match DataProvider spec
   
   - **docs-inconsistency-resolution-agent.json**:
     - Update to handle new section types
     - Preserve 18-section structure during fixes
   
   - **docs-tasks-alignment-agent.json**:
     - Update to validate task coverage for new section requirements
   
   - **codebase-documentation-agent.json**:
     - Update to check for 18-section compliance in docstrings

3. **docs/COMPONENT_SPECS_INDEX.md**:
   - Update component count (20 specs)
   - Update file numbering (fix 08/16 conflicts)
   - Add note about 18-section standard format
   - Update component list with corrected file numbers
   - Add reference to section templates

4. **docs/README.md**:
   - Update component spec documentation links
   - Add note about 18-section standard
   - Update getting started guide if needed

### Phase 7: Final Validation (1 hour)

**Run quality gates**:
```bash
python scripts/validate_component_specs.py
python scripts/test_docs_structure_validation_quality_gates.py
````

**Manual checks**:

- [ ] All 20 specs have 18 sections
- [ ] No duplicate file numbers
- [ ] All cross-references work
- [ ] Event logging documented for 11 main components
- [ ] Health integration documented for 11 main components
- [ ] Environment variables documented for all components
- [ ] Config fields documented for all components
- [ ] Data queries documented (or "N/A") for all components

## Key Benefits

1. **Complete Dependency Documentation**: Every component explicitly documents env vars, config fields, and data queries
2. **Operational Excellence**: Structured error handling + health monitoring for reliability
3. **Debugging Support**: Separate audit trail per component
4. **No Ambiguity**: All behaviors explicitly documented
5. **Consistency**: All 20 specs follow identical structure
6. **Automated Validation**: Quality gates enforce standard

## Adherence to .cursorrules

### DRY Principle

- Cross-reference 17_HEALTH_ERROR_SYSTEMS.md instead of duplicating error handling patterns
- Reference REFERENCE_ARCHITECTURE_CANONICAL.md for architectural principles
- Use templates to avoid duplication

### Documentation Rules

- Update docs/ first (this plan)
- Ensure all specs reference same logic
- No summary docs - enhance existing specs

### Refactoring Rules

- Clean breaks: Fix file numbering conflicts completely
- No backward compatibility: New 18-section format is standard
- Document breaking changes explicitly

### Canonical Architecture

- 17_HEALTH_ERROR_SYSTEMS.md is canonical for error handling
- REFERENCE_ARCHITECTURE_CANONICAL.md is canonical for architecture
- Component specs must align with canonical sources

## Estimated Effort

- **Phase 0**: 30 min (file renaming)
- **Phase 1-4**: 10-14 hours (updating 20 specs)
- **Phase 5**: 2 hours (quality gates)
- **Phase 6**: 1 hour (process docs)
- **Phase 7**: 1 hour (validation)

**Total**: 14-18 hours over 2-3 days

## Success Criteria

- [ ] All 20 component specs have 18 sections in standard order
- [ ] No duplicate file numbers (08, 16 conflicts resolved)
- [ ] Environment Variables documented for all 20 specs
- [ ] Config Fields documented for all 20 specs
- [ ] Data Provider Queries documented (or "N/A") for all 20 specs
- [ ] Event Logging enhanced with component-specific log files (11 main components)
- [ ] Error Codes enhanced with structured error handling (all components)
- [ ] Health integration documented (11 main components)
- [ ] Quality gate scripts validate 18-section structure
- [ ] All cross-references work
- [ ] Process documentation updated

### To-dos

- [ ] Phase 0: Fix file numbering conflicts (08_ and 16_ duplicates) and update cross-references
- [ ] Phase 1: Update 5 core monitoring components with all 18 sections (Position, Exposure, Risk, PnL, Strategy Manager)
- [ ] Phase 2: Update 6 execution layer components (Execution Manager, Interface Manager, Event Logger, Execution Interfaces, Reconciliation, Position Update Handler)
- [ ] Phase 3: Update 4 service components (Data Provider, Backtest Service, Live Service, Strategy Engine)
- [ ] Phase 4: Update 5 supporting components (Frontend, Math Utilities, Health/Error Systems, Results Store, Configuration)
- [ ] Phase 5: Create validate_component_specs.py and update existing quality gate validation
- [ ] Phase 6: Update process documentation (REFACTOR_STANDARD_PROCESS.md, COMPONENT_SPECS_INDEX.md, README.md)
- [ ] Phase 7: Run quality gates and perform final validation checks