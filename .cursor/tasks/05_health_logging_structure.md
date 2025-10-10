# HEALTH CHECKS & STRUCTURED LOGGING

## OVERVIEW
This task implements a unified health system with standardized health check endpoints and structured logging for all components to enable better debugging and monitoring. This provides comprehensive system observability and debugging capabilities.

**Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - Section 10 (Health System Architecture)  
**Reference**: `docs/ARCHITECTURAL_DECISION_RECORDS.md` - ADR-008 (Health System Unification)  
**Reference**: `docs/specs/08_EVENT_LOGGER.md` - Event logger specification  
**Reference**: `backend/src/basis_strategy_v1/infrastructure/health/` - Health system structure

## CRITICAL REQUIREMENTS

### 1. Unified Health System
- **Basic health endpoint**: GET /health - Simple health check for load balancers
- **Detailed health endpoint**: GET /health/detailed - Comprehensive health information
- **Component health checks**: Individual health checks for all components
- **Dependency health checks**: Health checks for external dependencies (APIs, databases)

### 2. Structured Logging Implementation
- **Component logging**: Structured logging for all components (Position Monitor, Risk Monitor, etc.)
- **Event logging integration**: Integration with Event Logger for strategy events
- **Log levels**: Appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Log formatting**: Consistent JSON log formatting for all components

### 3. Health Check Components
- **Data Provider health**: Check data provider connectivity and data freshness
- **Strategy Manager health**: Check strategy manager status and configuration
- **Risk Monitor health**: Check risk monitor status and circuit breaker state
- **Position Monitor health**: Check position monitor status and reconciliation state
- **Execution Manager health**: Check execution manager status and venue connectivity

### 4. Logging Integration
- **Event Logger integration**: All components log to Event Logger
- **Structured event format**: Consistent event format across all components
- **Event correlation**: Event correlation IDs for tracing requests
- **Performance logging**: Performance metrics logging for all components

## FORBIDDEN PRACTICES

### 1. Inconsistent Health Checks
- **No ad-hoc health checks**: All health checks must follow unified format
- **No missing health checks**: All components must have health checks
- **No inconsistent responses**: All health check responses must follow consistent format

### 2. Unstructured Logging
- **No print statements**: No print statements for logging
- **No inconsistent log formats**: All logs must follow structured format
- **No missing log levels**: All logs must have appropriate log levels

## REQUIRED IMPLEMENTATION

### 1. Health System Implementation
```python
# backend/src/basis_strategy_v1/infrastructure/health/health_checker.py
class HealthChecker:
    def __init__(self):
        self.components = []
        self.dependencies = []
    
    def register_component(self, component):
        # Register component for health checking
    
    def check_health(self) -> dict:
        # Perform basic health check
    
    def check_detailed_health(self) -> dict:
        # Perform detailed health check with component status
```

### 2. Health Check Endpoints
```python
# backend/src/basis_strategy_v1/api/health.py
@router.get("/health")
async def basic_health():
    # Return simple health status

@router.get("/health/detailed")
async def detailed_health():
    # Return detailed health information
```

### 3. Component Health Checks
```python
# Each component implements health check interface
class ComponentHealthCheck:
    def check_health(self) -> dict:
        # Return component health status
    
    def get_health_details(self) -> dict:
        # Return detailed component health information
```

### 4. Structured Logging Implementation
```python
# backend/src/basis_strategy_v1/infrastructure/logging/structured_logger.py
class StructuredLogger:
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.event_logger = None
    
    def log_event(self, level: str, message: str, **kwargs):
        # Log structured event
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        # Log performance metrics
```

### 5. Component Logging Integration
- **Position Monitor**: Structured logging for position updates and reconciliation
- **Risk Monitor**: Structured logging for risk calculations and circuit breaker events
- **Strategy Manager**: Structured logging for strategy execution and rebalancing
- **Execution Manager**: Structured logging for execution events and venue interactions
- **Data Provider**: Structured logging for data loading and API interactions

## VALIDATION

### 1. Health Check Functionality
- **Test basic health**: Verify /health endpoint returns correct status
- **Test detailed health**: Verify /health/detailed endpoint returns comprehensive information
- **Test component health**: Verify all components have working health checks
- **Test dependency health**: Verify external dependency health checks work

### 2. Logging Functionality
- **Test structured logging**: Verify all components use structured logging
- **Test log levels**: Verify appropriate log levels are used
- **Test event integration**: Verify Event Logger integration works
- **Test performance logging**: Verify performance metrics are logged

### 3. Integration Validation
- **Test health integration**: Verify health checks integrate with all components
- **Test logging integration**: Verify logging integrates with all components
- **Test error handling**: Verify health checks and logging handle errors appropriately

## QUALITY GATES

### 1. Health System Quality Gate
```bash
# scripts/test_health_logging_quality_gates.py
def test_health_system():
    # Test basic health endpoint
    # Test detailed health endpoint
    # Test component health checks
    # Test dependency health checks
```

### 2. Logging System Quality Gate
```bash
# Test structured logging implementation
# Test log level usage
# Test event logger integration
# Test performance logging
```

## SUCCESS CRITERIA

### 1. Unified Health System ✅
- [ ] GET /health returns simple health status
- [ ] GET /health/detailed returns comprehensive health information
- [ ] All components have working health checks
- [ ] External dependency health checks work

### 2. Structured Logging ✅
- [ ] All components use structured logging
- [ ] Appropriate log levels are used throughout
- [ ] Event Logger integration works for all components
- [ ] Performance metrics are logged for all components

### 3. Component Health Checks ✅
- [ ] Data Provider health check works
- [ ] Strategy Manager health check works
- [ ] Risk Monitor health check works
- [ ] Position Monitor health check works
- [ ] Execution Manager health check works

### 4. Logging Integration ✅
- [ ] Position Monitor logs structured events
- [ ] Risk Monitor logs structured events
- [ ] Strategy Manager logs structured events
- [ ] Execution Manager logs structured events
- [ ] Data Provider logs structured events

## QUALITY GATE SCRIPT

The quality gate script `scripts/test_health_logging_quality_gates.py` will:

1. **Test Health System**
   - Verify basic health endpoint returns correct status
   - Verify detailed health endpoint returns comprehensive information
   - Verify all components have working health checks
   - Verify external dependency health checks work

2. **Test Structured Logging**
   - Verify all components use structured logging
   - Verify appropriate log levels are used
   - Verify Event Logger integration works
   - Verify performance metrics are logged

3. **Test Component Integration**
   - Verify health checks integrate with all components
   - Verify logging integrates with all components
   - Verify error handling works appropriately

4. **Test System Observability**
   - Verify system health can be monitored
   - Verify debugging information is available
   - Verify performance metrics are accessible

**Expected Results**: Unified health system works correctly, structured logging is implemented throughout, all components are observable and debuggable.
