# Component Spec: Health & Error Systems 🏥

**Component**: Health & Error Systems (Unified Monitoring)  
**Responsibility**: Single source of truth for health monitoring and error handling systems  
**Priority**: ⭐⭐ MEDIUM (Critical for operations and debugging)  
**Backend Files**: `backend/src/basis_strategy_v1/core/health/` + `backend/src/basis_strategy_v1/core/error_codes/` ✅ **IMPLEMENTED**  
**Last Reviewed**: January 6, 2025  
**Status**: ✅ Aligned with canonical sources (.cursor/tasks/ + MODES.md)

---

## 📚 **Canonical Sources**

**This component spec aligns with canonical architectural principles**:
- **Architectural Principles**: [CANONICAL_ARCHITECTURAL_PRINCIPLES.md](../CANONICAL_ARCHITECTURAL_PRINCIPLES.md) - Consolidated from all .cursor/tasks/
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Task Specifications**: `.cursor/tasks/` - Individual task specifications

---

## 🎯 **Purpose**

Consolidate health monitoring and error handling systems into a single source of truth, providing comprehensive system monitoring and debugging capabilities.

**Key Principles**:
- **Unified Health System**: Single system consolidating all health checks
- **Centralized Error Registry**: 200+ error codes across all components
- **Real-time Monitoring**: Live health status and error tracking
- **Mode-Aware Filtering**: Different behavior for backtest vs live mode
- **Structured Logging**: Comprehensive error logging with stack traces
- **Fail-Fast Behavior**: Proper error propagation with error codes

---

## 🏗️ **Architecture Overview**

### **Health System Architecture**

```mermaid
graph TD
    A[UnifiedHealthManager] --> B[ComponentHealthChecker]
    A --> C[InfrastructureHealth]
    A --> D[SystemMetrics]
    A --> E[LiveTradingHealth]
    
    B --> F[PositionMonitorHealthChecker]
    B --> G[DataProviderHealthChecker]
    B --> H[RiskMonitorHealthChecker]
    B --> I[EventLoggerHealthChecker]
    
    C --> J[Redis/DB Health]
    C --> K[Data Provider Health]
    
    D --> L[CPU/Memory/Disk]
    D --> M[Process Metrics]
    
    E --> N[Strategy Heartbeats]
    E --> O[Live Trading Status]
    
    A --> P[API Endpoints]
    P --> Q[/health - Fast Heartbeat]
    P --> R[/health/detailed - Comprehensive]
    
    style A fill:#e1f5fe
    style P fill:#f3e5f5
```

**Full Architecture Details**: See [SYSTEM_HEALTH.md](SYSTEM_HEALTH.md) for comprehensive health system documentation.

---

## 🏥 **Health System Components**

### **Unified Health Manager**

Central orchestrator for all health checks with two clean endpoints:

- **`/health`**: Fast heartbeat check (< 50ms) - no authentication required
- **`/health/detailed`**: Comprehensive health check - no authentication required

### **Singleton Pattern Validation**

Following [13_singleton_pattern_requirements.md](../../.cursor/tasks/13_singleton_pattern_requirements.md):

#### **Single Instance Per Component**
- **Each component**: Must be a SINGLE instance across the entire run
- **No duplication**: Never initialize the same component twice in different places
- **Shared state**: All components share the same state and data

#### **Shared Configuration and Data Provider**
- **Single config instance**: All components must share the SAME config instance
- **Single data provider**: All components must share the SAME data provider instance
- **Synchronized data flows**: All components use the same data source

### **Venue-Based Execution Context**

Following [VENUE_ARCHITECTURE.md](../VENUE_ARCHITECTURE.md):

#### **Venue-Specific Health Monitoring**
- **CEX venues**: API connectivity, authentication, rate limits
- **DeFi venues**: Smart contract connectivity, gas price monitoring
- **Infrastructure venues**: RPC connectivity, network status
- **Environment-specific**: Testnet vs production health checks

#### **Execution Mode Health Checks**
- **Backtest mode**: Data provider health, configuration validation
- **Live mode**: Venue API health, real-time data feeds
- **Testnet mode**: Testnet venue connectivity
- **Production mode**: Production venue connectivity

### **Component Health Checkers**

Each component has a dedicated health checker:

- **PositionMonitorHealthChecker**: Wallet, CEX, perp position monitoring (5 error codes)
- **DataProviderHealthChecker**: Environment variables, data loading, market data, live provider (12 error codes)
- **RiskMonitorHealthChecker**: Risk assessment, configuration, Redis (9 error codes)
- **EventLoggerHealthChecker**: Event logging, Redis, balance snapshots (5 error codes)
- **StrategyManagerHealthChecker**: Mode detection, orchestration, decisions (10 error codes)
- **CEXExecutionHealthChecker**: Trade execution, margin, slippage (12 error codes)
- **OnChainExecutionHealthChecker**: Transactions, gas, contracts (12 error codes)
- **ConfigurationHealthChecker**: Validation, loading, environment (20 error codes)
- **MathCalculatorsHealthChecker**: AAVE, Health, LTV, Margin, Yield (48 error codes)
- **ExecutionInterfacesHealthChecker**: Factory, CEX, Transfer, OnChain (29 error codes)
- **LiveDataProviderHealthChecker**: API connections, rate limits, timeouts (10 error codes)

### **Health Status States**

| Status | Description | Action Required |
|--------|-------------|-----------------|
| **HEALTHY** | Component fully operational | None |
| **NOT_READY** | Component initialized but not ready (e.g., data provider without loaded data) | Wait or check dependencies |
| **UNHEALTHY** | Component has critical issues | Immediate attention required |
| **UNKNOWN** | Cannot determine status | Investigate |
| **NOT_CONFIGURED** | Component intentionally not set up | None (expected) |

### **Mode-Aware Filtering**

**Backtest Mode**:
- Redis Connection: Optional (not_configured if not available)
- Live Data Provider: Not needed (not_configured)
- API Connections: Not needed (not_configured)
- Components Shown: Core components only

**Live Mode**:
- Redis Connection: Required (healthy/unhealthy)
- Live Data Provider: Required (healthy/unhealthy)
- API Connections: Required (healthy/unhealthy)
- Components Shown: All components including live-specific ones

**Full Health System Details**: See [SYSTEM_HEALTH.md](SYSTEM_HEALTH.md) for comprehensive health monitoring documentation.

---

## ⚠️ **Error Code System**

### **Centralized Error Registry**

The system maintains a comprehensive error code registry with **200+ error codes** across **19 components**:

#### **Error Code Format**
`{COMPONENT}-{NUMBER}`

**Component Prefixes**:
- `POS-` Position Monitor (5 codes)
- `EXP-` Exposure Monitor (5 codes)
- `RISK-` Risk Monitor (9 codes)
- `STRAT-` Strategy Manager (10 codes)
- `CEX-` CEX Execution (12 codes)
- `CHAIN-` OnChain Execution (12 codes)
- `DATA-` Data Provider (10 codes)
- `EVENT-` Event Logger (5 codes)
- `CONFIG-` Configuration (10 codes)
- `LIVE-` Live Data (10 codes)
- `AAVE-` AAVE Calculator (8 codes)
- `HEALTH-` Health Calculator (8 codes)
- `LTV-` LTV Calculator (8 codes)
- `MARGIN-` Margin Calculator (12 codes)
- `YIELD-` Yield Calculator (12 codes)
- `FACTORY-` Interface Factory (6 codes)
- `CEX-IF-` CEX Interface (8 codes)
- `TRANSFER-IF-` Transfer Interface (7 codes)
- `ONCHAIN-IF-` OnChain Interface (8 codes)

#### **Severity Classification**

| Severity | Description | Action |
|----------|-------------|--------|
| **CRITICAL** | System-threatening errors | Immediate alerts + halt execution |
| **HIGH** | Serious errors requiring attention | Log + count, email if > 5 in 1 hour |
| **MEDIUM** | Moderate issues | Log + monitor |
| **LOW** | Minor issues | Log only |

### **Structured Error Logging**

#### **Core Logging Functions**

```python
from basis_strategy_v1.infrastructure.monitoring.logging import (
    log_structured_error,
    log_exception_with_stack_trace,
    log_component_health
)

# Log structured error with context
log_structured_error(
    error_code='RISK-001',
    message='Health factor below safe threshold',
    component='risk_monitor',
    context={'health_factor': 0.95, 'threshold': 1.0}
)

# Log exception with full stack trace
log_exception_with_stack_trace(
    error_code='RISK-009',
    component='risk_monitor',
    context={'operation': 'risk_calculation', 'timestamp': datetime.now()}
)

# Log component health status
log_component_health(
    component='position_monitor',
    status='healthy',
    metrics={'wallet_tokens': 5, 'cex_accounts': 3}
)
```

#### **Stack Trace Requirements**

**All ERROR and CRITICAL logs MUST include stack traces** for debugging:

```python
import traceback
import sys

try:
    risky_operation()
except Exception as e:
    log_structured_error(
        error_code='COMP-002',
        message=f'Operation failed: {str(e)}',
        component='component_name',
        context={
            'exception_type': type(e).__name__,
            'exception_message': str(e),
            'stack_trace': traceback.format_exc()
        }
    )
```

### **Alert Thresholds**

| Log Level | Action | Notification | Halt Execution |
|-----------|--------|--------------|----------------|
| **WARNING** | Log only | None (unless repeated) | False |
| **ERROR** | Log + count | Email if > 5 in 1 hour | False |
| **CRITICAL** | Log + immediate notification | Email + Telegram + halt | True |

**Full Error System Details**: See [11_ERROR_LOGGING_STANDARD.md](11_ERROR_LOGGING_STANDARD.md) for comprehensive error handling documentation.

---

## 🔗 **Integration Points**

### **EventDrivenStrategyEngine Integration**

The EventDrivenStrategyEngine automatically registers all components with the unified health manager:

```python
def _register_health_checkers(self):
    """Register all components with the unified health check system."""
    from ..health import unified_health_manager
    
    unified_health_manager.register_component(
        "position_monitor", 
        PositionMonitorHealthChecker(self.position_monitor)
    )
    unified_health_manager.register_component(
        "data_provider", 
        DataProviderHealthChecker(self.data_provider)
    )
    # ... register all other components
```

### **Data Provider Health Checks (New Architecture)**

The Data Provider health checker validates the new on-demand loading architecture:

```python
# Data Provider Health Checker
class DataProviderHealthChecker(ComponentHealthChecker):
    async def _perform_readiness_checks(self) -> Dict[str, bool]:
        checks = {}
        
        # Check environment variables
        checks["basis_data_mode_set"] = os.getenv('BASIS_DATA_MODE') is not None
        checks["basis_execution_mode_set"] = os.getenv('BASIS_EXECUTION_MODE') is not None
        
        # Check if data is loaded (new architecture: data loaded on-demand)
        if hasattr(self.data_provider, '_data_loaded'):
            checks["data_loaded"] = self.data_provider._data_loaded
        else:
            # Legacy check for backward compatibility
            checks["data_loaded"] = len(self.data_provider.data) > 0
        
        # Check market data availability (only if data is loaded)
        if checks["data_loaded"]:
            try:
                test_timestamp = pd.Timestamp('2024-06-01', tz='UTC')
                market_data = self.data_provider.get_market_data_snapshot(test_timestamp)
                checks["market_data_available"] = isinstance(market_data, dict) and len(market_data) > 0
            except:
                checks["market_data_available"] = False
        else:
            checks["market_data_available"] = True  # Not applicable if no data loaded
        
        return checks
```

**Health Status Behavior**:
- **HEALTHY**: Environment variables set, data loaded, market data available
- **NOT_READY**: Environment variables set, but no data loaded yet (expected for on-demand architecture)
- **UNHEALTHY**: Missing environment variables or data loading failures

### **Component Health Integration**

All components integrate with the health system:

```python
# Component health reporting
async def get_status(self) -> Dict[str, Any]:
    """Get current status with health information."""
    from ..health import unified_health_manager
    health_report = await unified_health_manager.check_detailed_health()
    
    return {
        'mode': self.mode,
        'health': {
            'overall_status': health_report['status'],
            'timestamp': health_report['timestamp'],
            'summary': health_report['summary'],
            'components': health_report['components']
        }
    }
```

---

## 🧪 **Usage Examples**

### **Health Monitoring**

```python
from basis_strategy_v1.core.health import unified_health_manager

# Get basic health (fast)
basic_health = await unified_health_manager.check_basic_health()
print(f"System status: {basic_health['status']}")

# Get detailed health (comprehensive)
detailed_health = await unified_health_manager.check_detailed_health()
print(f"Healthy components: {detailed_health['summary']['healthy_components']}")

# Check specific component
component_health = detailed_health['components']['position_monitor']
if component_health['status'] == 'healthy':
    print("Position Monitor is healthy")
else:
    print(f"Position Monitor error: {component_health['error_code']}")
```

### **Error Code Usage**

```python
from basis_strategy_v1.core.error_codes import get_error_info, validate_error_code

# Validate error code
if validate_error_code('POS-001'):
    error_info = get_error_info('POS-001')
    print(f"Message: {error_info.message}")
    print(f"Severity: {error_info.severity.value}")

# Log structured error
log_structured_error(
    error_code='RISK-001',
    message='Health factor below safe threshold',
    component='risk_monitor',
    context={'health_factor': 0.95, 'threshold': 1.0}
)
```

### **API Endpoints**

```bash
# Fast health check
curl http://localhost:8000/health

# Comprehensive health check
curl http://localhost:8000/health/detailed

# Check health in backtest mode (only shows backtest-relevant components)
curl http://localhost:8000/health/detailed

# Check health in live mode (shows all components including live trading health)
curl http://localhost:8000/health/detailed
```

---

## 🔄 **Automatic Health Monitoring**

### **Health Check Intervals**

The system supports configurable health check intervals via `HEALTH_CHECK_INTERVAL` environment variable:

```bash
# Format: <number><unit> where unit is s (seconds) or m (minutes)
HEALTH_CHECK_INTERVAL=30s   # Check every 30 seconds (recommended)
HEALTH_CHECK_INTERVAL=1m    # Check every 1 minute
```

### **Health Check Endpoints**

Two endpoints available, configurable via `HEALTH_CHECK_ENDPOINT`:

| Endpoint | Speed | Use Case | Recommended For |
|----------|-------|----------|-----------------|
| `/health` | < 50ms | Fast heartbeat | Production monitoring (default) |
| `/health/detailed` | ~200ms | Comprehensive | Detailed troubleshooting |

### **Automatic Restart Behavior**

**Docker Deployments**:
- Docker native healthcheck monitors backend container
- On unhealthy: Docker automatically restarts backend container
- Redis data preserved (separate container)
- Configurable via `docker-compose.yml` healthcheck section

**Non-Docker Deployments**:
- Background monitor script (`scripts/health_monitor.sh`)
- On unhealthy: Executes `platform.sh restart` 
- Restarts: Backend + Frontend + Redis (data preserved)
- Retry logic: 3 attempts with exponential backoff (5s, 10s, 20s)
- After 3 failures: Stops retrying, logs error for manual intervention

### **Monitoring Integration**

The health monitoring system integrates with:
- **Docker**: Native container health checks
- **Platform Script**: Automatic daemon process management
- **Logs**: Health check status logged to `logs/health_monitor.log`
- **Metrics**: Health check timing and failure rates tracked

### **Configuration Example**

```bash
# env.unified or override files
HEALTH_CHECK_INTERVAL=30s          # Check every 30 seconds
HEALTH_CHECK_ENDPOINT=/health      # Use fast endpoint

# For detailed monitoring (slower but comprehensive)
HEALTH_CHECK_ENDPOINT=/health/detailed
```

---

## 📊 **Monitoring Integration**

### **Prometheus Metrics**

The unified health system integrates with Prometheus metrics:

- **Component Health Status**: Gauge metrics for each component
- **Health Check Duration**: Histogram of health check timing
- **Error Rates**: Counter of health check errors
- **System Readiness**: Overall system readiness metric
- **Mode-specific Metrics**: Different metrics for backtest vs live mode

### **Logging Integration**

All health checks are logged with structured logging:

```python
logger.info(
    "Component health check completed",
    component="position_monitor",
    status="healthy",
    duration_ms=15.2,
    readiness_checks={"initialized": True, "redis_connected": True}
)
```

---

## 🔍 **Troubleshooting Guide**

### **Common Health Issues**

#### **Component Not Ready**
- **Cause**: Component initialized but dependencies not available
- **Action**: Check component dependencies and configuration
- **Error Codes**: Component-specific NOT_READY errors

#### **Component Unhealthy**
- **Cause**: Critical component failure
- **Action**: Immediate investigation required
- **Error Codes**: Component-specific UNHEALTHY errors

#### **Redis Connection Issues**
- **Cause**: Redis not available in live mode
- **Action**: Check Redis service status
- **Error Codes**: POS-002, EVENT-002

#### **Data Provider Issues**
- **Cause**: Data not loaded, live provider unavailable, or environment variables missing
- **Action**: Check data files, live data provider configuration, and environment variables
- **Error Codes**: DATA-001, DATA-002, DATA-003, DATA-011, DATA-013, DATA-014
- **New Architecture**: DATA-011 (date range validation), DATA-013 (missing env vars), DATA-014 (missing dates)

### **Health Check Debugging**

1. **Check Overall Status**: Use `/health/detailed` to see system readiness
2. **Check Component Details**: Use `/health/detailed` to see all component status
3. **Check Error Summary**: Use `/health/detailed` to see all current errors
4. **Check System Metrics**: Use `/health/detailed` to see system performance

---

## 📋 **Implementation Status** ✅ **FULLY IMPLEMENTED**

### **Health System**
- ✅ **Unified Health Manager**: Single system consolidating all health checks
- ✅ **Two Clean Endpoints**: `/health` (fast) and `/health/detailed` (comprehensive)
- ✅ **No Authentication Required**: Both endpoints accessible without auth
- ✅ **Mode-aware Health Checking**: Different behavior for backtest vs live mode
- ✅ **Component Health Checkers**: All core components have health checkers
- ✅ **Health Status Enum**: Complete status enumeration
- ✅ **Real-time Health Checks**: No caching, real-time status
- ✅ **No Health History**: Performance optimized (only last check timestamp)
- ✅ **System Aggregation**: Comprehensive system health reporting

### **Error Code System**
- ✅ **Centralized Error Registry**: `ErrorCodeRegistry` with 200+ error codes
- ✅ **Component Coverage**: All 19 components have comprehensive error codes
- ✅ **Severity Classification**: CRITICAL, HIGH, MEDIUM, LOW error levels
- ✅ **Validation System**: Error code existence and format validation
- ✅ **Structured Error Logging**: `log_structured_error()` and `log_component_health()`
- ✅ **Stack Trace Integration**: Automatic stack trace capture for ERROR/CRITICAL logs
- ✅ **Fail-Fast Behavior**: Proper error propagation with error codes
- ✅ **Alert Integration**: Severity-based alerting and notification

### **Integration**
- ✅ **Engine Integration**: Automatic registration with EventDrivenStrategyEngine
- ✅ **Component Integration**: All components integrated with health system
- ✅ **API Integration**: Health endpoints ready for monitoring
- ✅ **Monitoring Integration**: Prometheus metrics and structured logging

### **Architecture Compliance**
- ✅ **Singleton Pattern Validation**: Single instance per component with shared config and data provider
- ✅ **Venue-Based Execution Context**: Venue-specific health monitoring and execution mode health checks

---

## 🎯 **Next Steps**

1. **Advanced Monitoring**: Real-time dashboards and alerting
2. **Performance Optimization**: Health check caching and optimization
3. **Predictive Health**: Machine learning-based health prediction
4. **Automated Recovery**: Self-healing capabilities for common issues
5. **Compliance Reporting**: Audit trails and compliance documentation

## 🔍 **Quality Gate Validation**

Following [17_quality_gate_validation_requirements.md](../../.cursor/tasks/17_quality_gate_validation_requirements.md):

### **Mandatory Quality Gate Validation**
**BEFORE CONSIDERING TASK COMPLETE**, you MUST:

1. **Run Health & Error Systems Quality Gates**:
   ```bash
   python scripts/test_pure_lending_quality_gates.py
   python scripts/test_btc_basis_quality_gates.py
   ```

2. **Verify Singleton Pattern Validation**:
   - All components use single instances with shared config and data provider
   - No component duplication across the system
   - Shared state and data flows work correctly

3. **Verify Venue-Based Execution Context**:
   - Venue-specific health monitoring works correctly
   - Execution mode health checks work for backtest and live modes
   - Environment-specific health checks work correctly

4. **Verify Health System Integration**:
   - Health endpoints work correctly
   - Component health checkers work correctly
   - Error code system works correctly

5. **Document Results**:
   - Singleton pattern validation results
   - Venue-based execution context validation results
   - Health system integration results
   - Any remaining issues or limitations

**DO NOT PROCEED TO NEXT TASK** until quality gates validate the health & error systems are working correctly.

---

**Status**: Health & Error Systems are complete and fully operational! 🎉

*Last Updated: January 6, 2025*
