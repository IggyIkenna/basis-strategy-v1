# Component Health Check System 🏥

**Purpose**: Comprehensive health monitoring for all system components  
**Status**: ✅ COMPLETE - Full health check system with comprehensive error codes implemented  
**Updated**: January 6, 2025

---

## 🎯 **Overview**

The Component Health Check System provides **real-time monitoring** of all system components with:
- **Timestamps** for all health reports
- **Comprehensive error codes** (200+ codes across 19 components)
- **Severity-based error classification** (CRITICAL, HIGH, MEDIUM, LOW)
- **Readiness status** validation
- **Dynamic health checking** via API endpoints
- **Component-specific metrics** and dependencies
- **Structured error logging** with rich context
- **Centralized error code registry** for validation and lookup

---

## 🏗️ **Architecture**

### **Core Components**

```mermaid
graph TD
    A[SystemHealthAggregator] --> B[ComponentHealthChecker]
    B --> C[PositionMonitorHealthChecker]
    B --> D[DataProviderHealthChecker]
    B --> E[RiskMonitorHealthChecker]
    B --> F[EventLoggerHealthChecker]
    
    C --> G[ComponentHealthReport]
    D --> G
    E --> G
    F --> G
    
    G --> H[HealthStatus Enum]
    G --> I[Error Codes]
    G --> J[Timestamps]
    G --> K[Readiness Checks]
    G --> L[Metrics]
    
    A --> M[API Endpoints]
    M --> N[/health/components]
    M --> O[/health/readiness]
    M --> P[/health/errors]
    
    style A fill:#e1f5fe
    style G fill:#e8f5e8
    style M fill:#f3e5f5
```

### **Health Status States**

| Status | Description | Action Required |
|--------|-------------|-----------------|
| **HEALTHY** | Component fully operational | None |
| **NOT_READY** | Component initialized but not ready | Wait or check dependencies |
| **UNHEALTHY** | Component has critical issues | Immediate attention required |
| **UNKNOWN** | Cannot determine status | Investigate |
| **NOT_CONFIGURED** | Component intentionally not set up | None (expected) |

---

## 🔧 **Implementation Details**

### **Component Health Checkers**

#### **PositionMonitorHealthChecker**
- **Readiness Checks**: Initialization, Redis connection, snapshot availability
- **Metrics**: Wallet tokens, CEX accounts, perp positions, execution mode
- **Error Codes**: POS-001 (balance drift), POS-002 (negative balance), POS-003 (CEX mismatch), POS-004 (invalid venue), POS-005 (Redis connection lost)

#### **DataProviderHealthChecker**
- **Readiness Checks**: Initialization, data loaded, market data available, live provider
- **Metrics**: Data sources, execution mode, mode, data directory
- **Error Codes**: DATA-001 (file not found), DATA-002 (parsing failed), DATA-003 (validation failed), DATA-004 (timestamp alignment), DATA-005 (missing data), DATA-006 (sync failed), DATA-007 (snapshot failed), DATA-008 (source unavailable), DATA-009 (timeout), DATA-010 (format invalid)

#### **RiskMonitorHealthChecker**
- **Readiness Checks**: Initialization, config available, Redis connection, risk assessment
- **Metrics**: Current risks, LTV thresholds, margin thresholds, delta threshold
- **Error Codes**: RISK-001 (health factor below threshold), RISK-002 (margin ratio critical), RISK-003 (delta drift excessive), RISK-004 (config validation failed), RISK-005 (exposure data missing), RISK-006 (AAVE liquidation simulation failed), RISK-007 (CEX liquidation simulation failed), RISK-008 (LST price deviation critical), RISK-009 (risk calculation error)

#### **EventLoggerHealthChecker**
- **Readiness Checks**: Initialization, Redis connection, event logging available
- **Metrics**: Total events, global order, execution mode, balance snapshots
- **Error Codes**: EVENT-001 (logging failed), EVENT-002 (serialization failed), EVENT-003 (storage failed), EVENT-004 (retrieval failed), EVENT-005 (validation failed)

### **Health Report Structure**

```json
{
  "component_name": "position_monitor",
  "status": "healthy",
  "timestamp": "2024-06-01T12:00:00Z",
  "error_code": null,
  "error_message": null,
  "readiness_checks": {
    "initialized": true,
    "redis_connected": true,
    "redis_ping": true,
    "snapshot_available": true
  },
  "metrics": {
    "wallet_tokens": 12,
    "cex_accounts": 3,
    "perp_positions": 3,
    "execution_mode": "backtest"
  },
  "dependencies": []
}
```

---

## 🌐 **API Endpoints**

### **GET /health/components**
**Purpose**: Get comprehensive health status for all components

**Response**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-06-01T12:00:00Z",
    "components": {
      "position_monitor": { /* ComponentHealthReport */ },
      "data_provider": { /* ComponentHealthReport */ },
      "risk_monitor": { /* ComponentHealthReport */ },
      "event_logger": { /* ComponentHealthReport */ }
    },
    "summary": {
      "total_components": 4,
      "healthy_components": 4,
      "unhealthy_components": 0,
      "not_ready_components": 0,
      "unknown_components": 0
    }
  }
}
```

### **GET /health/components/{component_name}**
**Purpose**: Get detailed health status for specific component with history

**Parameters**:
- `component_name`: Name of component to check
- `limit`: Number of historical reports (default: 10)

### **GET /health/readiness**
**Purpose**: Check if all components are ready for operation

**Response**:
```json
{
  "success": true,
  "data": {
    "is_ready": true,
    "overall_status": "healthy",
    "ready_components": ["position_monitor", "data_provider", "risk_monitor", "event_logger"],
    "not_ready_components": [],
    "unhealthy_components": []
  }
}
```

### **GET /health/errors**
**Purpose**: Get summary of all component errors with error codes

**Response**:
```json
{
  "success": true,
  "data": {
    "total_errors": 0,
    "errors": [],
    "timestamp": "2024-06-01T12:00:00Z"
  }
}
```

---

## 🔄 **Integration with EventDrivenStrategyEngine**

### **Automatic Registration**
The `EventDrivenStrategyEngine` automatically registers all component health checkers during initialization:

```python
def _register_health_checkers(self):
    """Register all components with the health check system."""
    system_health_aggregator.register_component(
        "position_monitor", 
        PositionMonitorHealthChecker(self.position_monitor)
    )
    system_health_aggregator.register_component(
        "data_provider", 
        DataProviderHealthChecker(self.data_provider)
    )
    # ... other components
```

### **Enhanced Status Reporting**
The `get_status()` method now includes comprehensive health information:

```python
async def get_status(self) -> Dict[str, Any]:
    """Get current status of all components with health information."""
    health_report = await system_health_aggregator.get_system_health()
    
    return {
        'mode': self.mode,
        'share_class': self.share_class,
        'execution_mode': self.execution_mode,
        'health': {
            'overall_status': health_report['status'],
            'timestamp': health_report['timestamp'],
            'summary': health_report['summary'],
            'components': health_report['components']
        },
        # ... other status information
    }
```

---

## 📊 **Health Monitoring Features**

### **Real-time Health Checking**
- **Automatic Registration**: All components automatically registered with health system
- **Continuous Monitoring**: Health status checked on every API call
- **Historical Tracking**: Maintains health check history per component

### **Error Code System**
- **Component-Specific**: Each component has unique error codes (POS-001, DATA-001, etc.)
- **Descriptive Messages**: Clear error messages for troubleshooting
- **Error Aggregation**: API endpoint to get all current errors

### **Readiness Validation**
- **Component-Specific**: Each component defines its own readiness criteria
- **Dependency Checking**: Validates component dependencies
- **System Readiness**: Overall system readiness based on all components

### **Metrics Collection**
- **Operational Metrics**: Component-specific operational data
- **Performance Metrics**: Health check timing and frequency
- **Dependency Metrics**: Component dependency status

---

## 🚀 **Usage Examples**

### **Check System Health**
```bash
curl http://localhost:8000/health/components
```

### **Check Component Readiness**
```bash
curl http://localhost:8000/health/readiness
```

### **Get Component Errors**
```bash
curl http://localhost:8000/health/errors
```

### **Check Specific Component**
```bash
curl http://localhost:8000/health/components/position_monitor
```

### **Programmatic Health Checking**
```python
from basis_strategy_v1.core.health import system_health_aggregator

# Get system health
health_report = await system_health_aggregator.get_system_health()

# Check specific component
component_health = health_report['components']['position_monitor']
if component_health['status'] == 'healthy':
    print("Position Monitor is healthy")
else:
    print(f"Position Monitor error: {component_health['error_code']}")
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
- **Cause**: Data not loaded or live provider unavailable
- **Action**: Check data files and live data provider configuration
- **Error Codes**: DATA-001, DATA-002, DATA-003

### **Health Check Debugging**

1. **Check Overall Status**: Use `/health/readiness` to see system readiness
2. **Check Component Details**: Use `/health/components/{component}` for specific issues
3. **Check Error Summary**: Use `/health/errors` to see all current errors
4. **Check Health History**: Use component detail endpoint to see health trends

---

## 📈 **Monitoring Integration**

### **Prometheus Metrics**
The health system integrates with Prometheus metrics for monitoring:

- **Component Health Status**: Gauge metrics for each component
- **Health Check Duration**: Histogram of health check timing
- **Error Rates**: Counter of health check errors
- **System Readiness**: Overall system readiness metric

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

## ✅ **System Status**

### **Completed Features**
- ✅ **Component Health Checkers**: All core components have health checkers
- ✅ **Health Status Enum**: Complete status enumeration
- ✅ **Comprehensive Error Code System**: 200+ error codes across 19 components
- ✅ **Centralized Error Registry**: `ErrorCodeRegistry` with validation and lookup
- ✅ **Severity Classification**: CRITICAL, HIGH, MEDIUM, LOW error levels
- ✅ **Structured Error Logging**: `log_structured_error()` and `log_component_health()`
- ✅ **Timestamp Integration**: All health reports include timestamps
- ✅ **Readiness Validation**: Component-specific readiness checks
- ✅ **Metrics Collection**: Component-specific operational metrics
- ✅ **API Endpoints**: Complete health checking API
- ✅ **Engine Integration**: Automatic registration with EventDrivenStrategyEngine
- ✅ **System Aggregation**: Comprehensive system health reporting
- ✅ **Health History**: Historical health tracking per component
- ✅ **Fail-Fast Behavior**: Proper error propagation with error codes

### **Health Check Coverage**
- ✅ **Position Monitor**: Wallet, CEX, perp position monitoring (5 error codes)
- ✅ **Data Provider**: Data loading, market data, live provider (10 error codes)
- ✅ **Risk Monitor**: Risk assessment, configuration, Redis (9 error codes)
- ✅ **Event Logger**: Event logging, Redis, balance snapshots (5 error codes)
- ✅ **Strategy Manager**: Mode detection, orchestration, decisions (10 error codes)
- ✅ **CEX Execution Manager**: Trade execution, margin, slippage (12 error codes)
- ✅ **OnChain Execution Manager**: Transactions, gas, contracts (12 error codes)
- ✅ **Configuration System**: Validation, loading, environment (20 error codes)
- ✅ **Math Calculators**: AAVE, Health, LTV, Margin, Yield (48 error codes)
- ✅ **Execution Interfaces**: Factory, CEX, Transfer, OnChain (29 error codes)
- ✅ **Live Data Provider**: API connections, rate limits, timeouts (10 error codes)

---

## 🔢 **Error Code Integration**

### **Centralized Error Registry**
The health system now integrates with a comprehensive error code registry:

```python
from basis_strategy_v1.core.error_codes import get_error_info, validate_error_code

# Get error information
error_info = get_error_info('RISK-001')
print(f"Message: {error_info.message}")
print(f"Severity: {error_info.severity.value}")

# Validate error code
if validate_error_code('POS-002'):
    print("Valid error code")
```

### **Structured Error Logging**
Health checks now use structured error logging with severity-based log levels:

```python
from basis_strategy_v1.infrastructure.monitoring.logging import log_structured_error

# Log with error code and context
log_structured_error(
    error_code='RISK-001',
    message='Health factor below safe threshold',
    component='risk_monitor',
    context={'health_factor': 0.95, 'threshold': 1.0}
)
```

### **Error Code Coverage**
- **Total Error Codes**: 200+ across all components
- **Severity Levels**: CRITICAL, HIGH, MEDIUM, LOW
- **Component Coverage**: All 19 components have comprehensive error codes
- **Validation**: Centralized validation and lookup system

### **Health Check Error Integration**
Health checkers now provide detailed error information:

```json
{
  "component_name": "risk_monitor",
  "status": "unhealthy",
  "timestamp": "2025-01-06T12:00:00Z",
  "error_code": "RISK-001",
  "error_message": "Health factor below safe threshold",
  "severity": "critical",
  "readiness_checks": {
    "initialized": true,
    "config_available": true,
    "risk_assessment_available": false
  },
  "metrics": {
    "current_risks": 4,
    "aave_safe_ltv": 0.8
  }
}
```

---

## 🎯 **Benefits**

### **For Operations**
- **Real-time Monitoring**: Know component status at all times
- **Proactive Issue Detection**: Identify problems before they impact operations
- **Quick Troubleshooting**: Error codes and messages for rapid diagnosis
- **System Readiness**: Ensure all components ready before operations

### **For Development**
- **Component Validation**: Verify component initialization and configuration
- **Dependency Tracking**: Understand component dependencies
- **Health History**: Track component health over time
- **API Integration**: Programmatic health checking

### **For Production**
- **Monitoring Integration**: Works with existing monitoring systems
- **Alerting**: Health status can trigger alerts
- **Debugging**: Detailed health information for troubleshooting
- **Performance**: Lightweight health checks with minimal overhead

---

**Status**: Component Health Check System with comprehensive error codes is complete and fully operational! 🎉

*Last Updated: January 6, 2025*
