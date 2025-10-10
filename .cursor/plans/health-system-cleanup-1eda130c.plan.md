<!-- 1eda130c-8f81-468e-ad87-563ec06295fc 00796f30-1108-4f78-b763-b1e8e506ea0a -->
# Health System Cleanup and Consolidation

## Phase 1: Create New Unified Health System

### 1.1 Create New Health Manager

**File**: `backend/src/basis_strategy_v1/core/health/unified_health_manager.py`

Create a brand new unified health manager that:

- Consolidates infrastructure health (DB, data provider)
- Consolidates config health (component registration)
- Consolidates component health (200+ error codes, readiness checks)
- Mode-aware (backtest vs live)
- No health history (only last check timestamp)
- No caching (real-time checks)
- Excludes components not needed in current mode from response

**Key Methods**:

```python
class UnifiedHealthManager:
    async def check_basic_health() -> Dict[str, Any]
        # Fast heartbeat check (< 50ms)
        # Returns: status, timestamp, service, execution_mode, uptime, system metrics
    
    async def check_detailed_health() -> Dict[str, Any]
        # Comprehensive check
        # Returns: all components, system metrics, summary
        # Only includes components relevant to current execution mode
    
    async def _check_component_health(component_name: str) -> Dict[str, Any]
        # Real component health based on:
        # - No error codes present
        # - Config loaded successfully
        # - Data available (if needed)
        # - Dependencies satisfied
```

### 1.2 Update Component Health Checkers

**File**: `backend/src/basis_strategy_v1/core/health/component_health.py`

Keep existing component health checkers but update to:

- Remove health history (only store last_check_timestamp)
- Work with new UnifiedHealthManager
- Keep 200+ error codes system
- Keep readiness checks logic

**Preserve**:

- `HealthStatus` enum
- `ComponentHealthReport` dataclass (remove history fields)
- `ComponentHealthChecker` base class
- `PositionMonitorHealthChecker`
- `DataProviderHealthChecker`
- `RiskMonitorHealthChecker`
- `EventLoggerHealthChecker`

**Remove**:

- `health_history` list
- `get_component_health_history()` method

### 1.3 Update Health Module Exports

**File**: `backend/src/basis_strategy_v1/core/health/__init__.py`

Export new unified manager:

```python
from .unified_health_manager import (
    UnifiedHealthManager,
    unified_health_manager
)
from .component_health import (
    HealthStatus,
    ComponentHealthReport,
    ComponentHealthChecker,
    # ... all checkers
)
```

## Phase 2: Simplify Health Endpoints

### 2.1 Consolidate Health Routes

**File**: `backend/src/basis_strategy_v1/api/routes/health.py`

Simplify to 2 endpoints only:

```python
@router.get("/")
async def basic_health() -> HealthResponse:
    # Fast heartbeat (< 50ms)
    # No authentication required
    # Returns: status, timestamp, service, execution_mode, uptime, system metrics

@router.get("/detailed")
async def detailed_health() -> HealthResponse:
    # Comprehensive health
    # No authentication required
    # Returns: all components (mode-filtered), system metrics, summary
    # Includes live trading health when in live mode
```

### 2.2 Delete Redundant Health Route File

**File**: `backend/src/basis_strategy_v1/api/routes/component_health.py` - DELETE

All component health now in `/health/detailed`

### 2.3 Update Live Trading Health

**File**: `backend/src/basis_strategy_v1/api/routes/live_trading.py`

Remove `/live-trading/health` endpoint (lines 303-336)

- Health now included in `/health/detailed` when in live mode

### 2.4 Update Health Response Models

**File**: `backend/src/basis_strategy_v1/api/models/responses.py`

Simplify to single `HealthResponse` model:

```python
class HealthResponse(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    service: Optional[str] = "basis-strategy-v1"
    execution_mode: Optional[str] = None
    uptime_seconds: Optional[float] = None
    system: Optional[Dict[str, Any]] = None
    components: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
```

Remove: `LiveTradingHealthResponse` (merged into HealthResponse)

## Phase 3: Remove Redundant Health Systems

### 3.1 Delete Infrastructure Health System

**File**: `backend/src/basis_strategy_v1/infrastructure/monitoring/health.py` - DELETE

All functionality moved to UnifiedHealthManager

### 3.2 Delete Config Health System

**File**: `backend/src/basis_strategy_v1/infrastructure/config/health_check.py` - DELETE

All functionality moved to UnifiedHealthManager

### 3.3 Update Dependencies File

**File**: `backend/src/basis_strategy_v1/api/dependencies.py`

Update health checker dependencies:

- Remove `get_health_checker_async()` (old system)
- Add `get_unified_health_manager()` (new system)
- Update `StubHealthChecker` to match new interface

## Phase 4: Update Component Integrations

Update 22 component integration files to use new unified system:

### 4.1 Event Engine Integration

**File**: `backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py`

Update `_register_health_checkers()` to use unified_health_manager

### 4.2 Data Provider Integration

**Files**:

- `infrastructure/data/live_data_provider.py`
- `infrastructure/data/historical_data_provider.py`

Update health reporting to use new system

### 4.3 Component Integrations (20 files)

Update all components that report health status:

- `core/strategies/components/exposure_monitor.py`
- `core/strategies/components/risk_monitor.py`
- `core/strategies/components/position_monitor.py`
- `core/rebalancing/risk_monitor.py`
- `core/rebalancing/transfer_manager.py`
- All other component files

Change: Import from `unified_health_manager` instead of old health systems

## Phase 5: Update Documentation

### 5.1 Update Component Health System Doc

**File**: `docs/COMPONENT_HEALTH_SYSTEM.md`

Major rewrite:

- Remove health history sections
- Update to 2 endpoints only
- Document live vs backtest differences
- Document mode-filtered component responses
- Update error code integration
- Remove cached health sections

### 5.2 Update Quality Gates Doc

**File**: `docs/QUALITY_GATES.md`

Update health check sections:

- Simplify to 2 endpoints
- Remove health history references
- Update component health requirements

### 5.3 Update Deployment Guide

**File**: `docs/DEPLOYMENT_GUIDE.md`

Update health check sections (lines 567-613):

- Simplify to 2 endpoints
- Remove Redis requirement mentions (Redis removed)

### 5.4 Update Config Workflow

**File**: `docs/specs/CONFIGURATION.md`

Update health monitoring section (lines 211-227):

- Reference new unified system
- Remove old health check references

### 5.5 Update Architectural Decisions

**File**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md`

Add new decision for unified health system

### 5.6 Update Workflow Guide

**File**: `docs/WORKFLOW_GUIDE.md`

Update health monitoring sections:

- Simplify health check workflow
- Remove component health route references

### 5.7 Update Getting Started

**File**: `docs/GETTING_STARTED.md`

Update health check examples:

- Use new 2 endpoints only
- Remove component health references

### 5.8 Update User Guide

**File**: `docs/USER_GUIDE.md`

Update health monitoring section:

- Simplify to 2 endpoints
- Update examples

## Phase 6: Update Tests

### 6.1 Update Health API Tests

**File**: `tests/unit/api/test_health.py`

Update tests for:

- New 2 endpoints only
- New response structure
- No health history
- Mode-filtered components

### 6.2 Remove Component Health Tests

Delete tests for removed component_health routes

## Phase 7: Update API Route Registration

### 7.1 Update Main API

**File**: `backend/src/basis_strategy_v1/api/main.py`

Update route registration:

- Keep `health.router` with prefix `/health`
- Remove `component_health.router` registration

## Success Criteria

- Only 2 health endpoints: `/health` and `/health/detailed`
- No authentication required on either endpoint
- `/health` responds in < 50ms
- Components not needed in current mode excluded from response
- No health history tracking
- No caching of health checks
- All 200+ error codes preserved
- Real component health based on error codes, config, and data
- Live trading health merged into `/health/detailed`
- All documentation updated
- All tests passing

### To-dos

- [ ] Create new unified health manager that consolidates all health systems
- [ ] Update component health checkers to remove history and work with new manager
- [ ] Consolidate to 2 health endpoints and update response models
- [ ] Delete infrastructure/monitoring/health.py, infrastructure/config/health_check.py, and api/routes/component_health.py
- [ ] Update 22 component files to use new unified health system
- [ ] Update 8 documentation files with new health system architecture
- [ ] Update health API tests for new system