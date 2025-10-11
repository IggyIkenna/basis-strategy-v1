<!-- d9055591-4ea9-4d64-8449-fcf12a06f9ad 8061c604-9434-4051-a4e1-5fdee1e5b8f0 -->
# Complete Component Spec Standardization v4

## Overview

Standardize all 19 component specs with **18-section format** that explicitly documents:

1. **Environment Variables** - which env vars each component reads
2. **Config Fields** - which config fields from strategy mode slice
3. **Data Queries** - which data from DataProvider
4. **Event Logging** - separate log files per component + audit requirements
5. **Error Codes** - structured error handling + component health integration
6. **Quality Gates** - validation criteria

---

## FINAL Section Order (18 Sections)

1. Purpose
2. Responsibilities
3. State
4. Component References (Set at Init)
5. **Environment Variables** ⭐ NEW
6. **Config Fields Used** ⭐ NEW
7. **Data Provider Queries** ⭐ NEW (or N/A if no data queries)
8. Core Methods
9. Data Access Pattern
10. Mode-Aware Behavior
11. **Event Logging Requirements** ⭐ ENHANCED with separate log files
12. **Error Codes** ⭐ ENHANCED with structured error handling + health integration
13. Quality Gates
14. Integration Points
15. Code Structure Example
16. Related Documentation

---

## CRITICAL NEW REQUIREMENTS

### Event Logging Requirements Section MUST Include:

#### 1. Separate Component Event Log File (11 Main Components)

Each of the 11 main components gets its own event log file:

```
logs/events/position_monitor_events.jsonl
logs/events/exposure_monitor_events.jsonl
logs/events/risk_monitor_events.jsonl
logs/events/pnl_calculator_events.jsonl
logs/events/strategy_manager_events.jsonl
logs/events/execution_manager_events.jsonl
logs/events/execution_interface_manager_events.jsonl
logs/events/execution_interfaces_events.jsonl
logs/events/data_provider_events.jsonl
logs/events/reconciliation_events.jsonl
logs/events/position_update_handler_events.jsonl
```

#### 2. Event Logging via Centralized EventLogger

- All events go through `self.event_logger.log_event()`
- EventLogger routes events to component-specific log files
- JSON Lines format (one event per line)
- Daily rotation, 30-day retention

#### 3. Required Events to Log

- Component initialization
- Every state update (full loop + tight loop)
- All errors with error codes
- Component-specific critical events

### Error Codes Section MUST Include:

#### 1. Structured Error Handling Pattern

```python
from backend.src.basis_strategy_v1.core.error_codes.exceptions import ComponentError

raise ComponentError(
    error_code='[PREFIX]-001',
    message='Detailed error message',
    component='[ComponentName]',
    severity='CRITICAL|HIGH|MEDIUM|LOW',
    original_exception=e
)
```

#### 2. Error Propagation Rules

- **CRITICAL**: Propagate to health system → trigger app restart
- **HIGH**: Log and retry with exponential backoff
- **MEDIUM**: Log and continue with degraded functionality
- **LOW**: Log for monitoring only

#### 3. Component Health Integration

```python
def __init__(self, ..., health_manager: UnifiedHealthManager):
    # Register component with health system
    self.health_manager = health_manager
    self.health_manager.register_component(
        component_name='[ComponentName]',
        checker=self._health_check
    )

def _health_check(self) -> Dict:
    return {
        'status': 'healthy' | 'degraded' | 'unhealthy',
        'last_update': self.last_update_timestamp,
        'errors': self.recent_errors,
        'metrics': {...}
    }
```

#### 4. Health Status Triggers

- **healthy**: No errors, normal processing times
- **degraded**: Minor errors, slower processing, retries succeeding
- **unhealthy**: Critical errors, failed retries → 503 response → alert → restart

**Reference**: `docs/specs/17_HEALTH_ERROR_SYSTEMS.md`

---

## NEW Section Templates

### Template 1: Environment Variables

````markdown
## Environment Variables

### Required Environment Variables

#### System-Level Variables (All Components)
- `BASIS_EXECUTION_MODE`: backtest | live
  - **Usage**: Determines simulated vs real API behavior
  - **Read at**: Component initialization
  - **Affects**: Mode-aware conditional logic

- `BASIS_ENVIRONMENT`: dev | staging | production
  - **Usage**: Credential routing for venue APIs
  - **Read at**: Component initialization (if uses venues)
  - **Affects**: Which API keys/endpoints to use

- `BASIS_DEPLOYMENT_MODE`: local | docker
  - **Usage**: Port/host configuration
  - **Read at**: Component initialization (if network calls)
  - **Affects**: Connection strings

- `BASIS_DATA_MODE`: csv | db
  - **Usage**: Data source selection (DataProvider only)
  - **Read at**: DataProvider initialization
  - **Affects**: File-based vs database data loading

#### Component-Specific Variables
- [List any component-specific env vars]

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

### Template 2: Config Fields Used

```markdown
## Config Fields Used

### Required Config Fields
From `self.config` (strategy mode slice):

#### Universal Config (All Components)
- `mode`: str - e.g., 'eth_basis', 'pure_lending'
- `share_class`: str - 'usdt_stable' | 'eth_directional'
- `initial_capital`: float - Starting capital

#### Component-Specific Config
- `[field_name]`: [type] - [description]
  - **Usage**: [how component uses this]
  - **Default**: [default value]
  - **Validation**: [constraints]

### Mode-Specific Config Differences
[Document how config differs per strategy mode]

### Config Access Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    # Read config fields (NEVER modify)
    max_leverage = self.config['risk_limits']['max_leverage']
````

### Behavior NOT Determinable from Config

[List hard-coded logic that can't be config-controlled]

````

### Template 3: Data Provider Queries

```markdown
## Data Provider Queries

### Data Types Requested
`data = self.data_provider.get_data(timestamp)`

#### Market Data
- `prices`: Dict[str, float] - Token prices in USD
  - **Tokens needed**: [ETH, USDT, etc.]
  - **Update frequency**: [real-time | 1min | 5min | 1h]
  - **Usage**: [position valuation | trade sizing]

[Continue for all data types needed]

### Query Pattern
```python
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    data = self.data_provider.get_data(timestamp)
    prices = data['market_data']['prices']
````

### Data NOT Available from DataProvider

[List external data sources accessed directly]

**OR** if no queries:

```markdown
## Data Provider Queries
**N/A** - This component does not directly query DataProvider.
```



`````

### Template 4: Event Logging Requirements ⭐ ENHANCED

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
`````

#### 2. State Updates (Every update_state() Call)

```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='state_update',
    component='[ComponentName]',
    data={
        'trigger_source': trigger_source,
        'state_before': state_before,
        'state_after': state_after,
        'processing_time_ms': processing_time
    }
)
```

#### 3. Error Events

```python
self.event_logger.log_event(
    timestamp=timestamp,
    event_type='error',
    component='[ComponentName]',
    data={
        'error_code': '[PREFIX]-XXX',
        'error_message': str(e),
        'stack_trace': traceback.format_exc(),
        'error_severity': 'CRITICAL|HIGH|MEDIUM|LOW'
    }
)
```

#### 4. Component-Specific Critical Events

[Document component-specific events, e.g.:]

- Position Monitor: reconciliation_mismatch, position_sync_failed
- Strategy Manager: action_decided, instruction_blocks_generated
- Execution Manager: tight_loop_started, tight_loop_completed

### Event Log Structure

```json
{
  "timestamp": "2025-10-10T12:00:00Z",
  "order": 12345,
  "event_type": "state_update",
  "component": "PositionMonitor",
  "data": {...}
}
```

### Event Retention

- **Backtest**: Keep all events in memory, write at completion
- **Live**: Write immediately, rotate daily, keep 30 days
````

### Template 5: Error Codes ⭐ ENHANCED

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

#### Health Monitoring Flow

1. Component raises error (HIGH or CRITICAL)
2. After N failures, component reports **unhealthy** status
3. Health manager detects unhealthy component
4. Health endpoint returns 503 Service Unavailable
5. Monitoring system alerts operators
6. Auto-restart triggered (if configured)

**Reference**: `docs/specs/17_HEALTH_ERROR_SYSTEMS.md`

````

---

## Quality Gate System Updates

### Update REQUIRED_SECTIONS
```python
REQUIRED_SECTIONS = [
    "Purpose", "Responsibilities", "State",
    "Component References (Set at Init)",
    "Environment Variables",  # NEW
    "Config Fields Used",  # NEW
    "Data Provider Queries",  # NEW (or N/A)
    "Core Methods",
    "Data Access Pattern",
    "Mode-Aware Behavior",
    "Event Logging Requirements",  # ENHANCED - separate log files
    "Error Codes",  # ENHANCED - structured errors + health
    "Quality Gates",
    "Integration Points",
    "Code Structure Example",
    "Related Documentation"
]
````

### Validation Checks

- Separate event log file documented for 11 main components
- EventLogger usage pattern documented
- All 4 event types documented (init, state_update, error, critical)
- Structured error handling with ComponentError
- Error propagation rules documented (CRITICAL/HIGH/MEDIUM/LOW)
- Component health integration with _health_check() method
- Health status definitions (healthy/degraded/unhealthy)

---

## Implementation Plan

### Phase 1: Create Comprehensive Templates

- Environment Variables section template
- Config Fields Used section template
- Data Provider Queries section template
- **Event Logging Requirements template with separate log files**
- **Error Codes template with structured error handling + health integration**

### Phase 2: Update Core Components (5)

Position, Exposure, Risk, PnL, Strategy Manager

- Apply all 18 sections
- Document separate event log file for each
- Add structured error handling
- Add health check integration

### Phase 3: Update Execution Layer (5)

Execution Manager, Interface Manager, Interfaces, Reconciliation, Position Update Handler

- Apply all 18 sections with full templates

### Phase 4: Update Service Components (5)

Data Provider, Event Logger, Backtest Service, Live Service, Strategy Engine

- Apply all 18 sections with full templates

### Phase 5: Update Supporting Components (4)

Math Utilities, Health/Error, Frontend, Configuration

- Apply all 18 sections (adjusted for their specific roles)

### Phase 6: Update Quality Gate Agents (6)

- Update agent configs for 18-section validation
- Add checks for separate event log files
- Add checks for structured error handling
- Add checks for health integration

### Phase 7: Update Quality Gate Scripts (4)

- Update run_quality_gates.py for 18-section structure
- Create validate_error_codes.py
- Create validate_quality_gates.py
- Create validate_component_structure.py

### Phase 8: Update Process Documentation

- Update REFACTOR_STANDARD_PROCESS.md with new requirements
- Document separate event log file requirement
- Document structured error handling requirement
- Document component health integration requirement

### Phase 9: Final Validation

- Run all quality gate scripts
- Validate all 11 main components have separate event log files
- Validate all components use structured error handling
- Validate all 11 main components have health check integration

---

## Summary

**Sections**: 18 (was 15)

**New Requirements**: 6 major additions

1. Environment Variables section
2. Config Fields Used section
3. Data Provider Queries section
4. Separate event log files (11 main components)
5. Structured error handling (ComponentError)
6. Component health integration (UnifiedHealthManager)

**Component Specs**: 19 files to update

**Agent Configs**: 6 files

**Scripts**: 1 update + 3 new

**Lines Added**: 3000-5000 (increased from 2500-4000)

**Key Benefits**:

- Complete dependency documentation (env vars, config, data)
- Separate audit trail per component (debugging)
- Structured error handling (operational excellence)
- Component health monitoring (reliability)
- All behaviors explicitly documented (no ambiguity)

### To-dos

- [ ] Create 3 new architecture pattern docs (REFERENCE_ARCHITECTURE.md, SHARED_CLOCK_PATTERN.md, REQUEST_ISOLATION_PATTERN.md)
- [ ] Create 2 new component specs (10_RECONCILIATION_COMPONENT.md, 11_POSITION_UPDATE_HANDLER.md)
- [ ] Restructure 4 execution layer docs (05_STRATEGY_MANAGER, 06_EXECUTION_MANAGER new, 07_EXECUTION_INTERFACE_MANAGER new, 08_EXECUTION_INTERFACES new), delete old 06/07
- [ ] Update 9 existing component specs with reference-based architecture, shared clock, no async, standardized update_state signature
- [ ] Update 5 high-level architecture docs (ARCHITECTURAL_DECISIONS, TIGHT_LOOP_ARCHITECTURE, WORKFLOW_GUIDE, CONFIGURATION, DEVIATIONS_AND_CORRECTIONS)
- [ ] Final pass: remove contradictions, add cross-references, standardize terminology, validate all 11 components follow same structure