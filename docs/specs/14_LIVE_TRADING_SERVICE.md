# Component Spec: Live Trading Service 🚀

**Component**: Live Trading Service  
**Responsibility**: Orchestrate live trading using EventDrivenStrategyEngine with real execution  
**Priority**: ⭐⭐⭐ CRITICAL (Enables live trading functionality)  
**Backend File**: `backend/src/basis_strategy_v1/core/services/live_service.py` ✅ **IMPLEMENTED**  
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

Orchestrate live trading using the EventDrivenStrategyEngine with real execution, risk management, and continuous monitoring.

**Key Principles**:
- **Real Execution**: Use real APIs and execution interfaces for live trading
- **Risk Management**: Continuous risk limit monitoring and emergency stop capabilities
- **Background Execution**: Asynchronous strategy execution with monitoring
- **Heartbeat Monitoring**: Track strategy health and detect failures
- **Emergency Controls**: Emergency stop and risk limit breach handling
- **Performance Tracking**: Real-time performance metrics and P&L tracking

---

## 🏗️ **Architecture**

### **Service Flow**

```
API Request → Request Validation → Config Creation → Engine Initialization → Background Execution → Monitoring → Risk Management
```

### **Core Classes**

#### **LiveTradingService**
Main service class that orchestrates live trading execution.

#### **LiveTradingRequest**
Request object containing all live trading parameters:
- `strategy_name`: Strategy to execute
- `initial_capital`: Starting capital amount
- `share_class`: Share class ('USDT' or 'ETH')
- `config_overrides`: Optional configuration overrides
- `risk_limits`: Risk management limits and thresholds

---

## 🔧 **Key Methods**

### **Request Management**

```python
def create_request(self, strategy_name: str, initial_capital: Decimal, share_class: str,
                  config_overrides: Dict[str, Any] = None, 
                  risk_limits: Dict[str, Any] = None) -> LiveTradingRequest:
    """Create a live trading request with validation."""
```

### **Live Trading Execution**

```python
async def start_live_trading(self, request: LiveTradingRequest) -> str:
    """
    Start live trading asynchronously.
    
    Flow:
    1. Validate request parameters and risk limits
    2. Load configuration using ConfigManager
    3. Initialize EventDrivenStrategyEngine
    4. Start background execution task
    5. Begin monitoring and risk management
    """
```

### **Monitoring and Control**

```python
async def stop_live_trading(self, request_id: str) -> bool:
    """Stop a running live trading strategy."""

async def get_status(self, request_id: str) -> Dict[str, Any]:
    """Get the status of a live trading strategy."""

async def get_performance_metrics(self, request_id: str) -> Optional[Dict[str, Any]]:
    """Get performance metrics for a live trading strategy."""

async def check_risk_limits(self, request_id: str) -> Dict[str, Any]:
    """Check if risk limits are being breached."""

async def emergency_stop(self, request_id: str, reason: str = "Emergency stop") -> bool:
    """Emergency stop a live trading strategy."""
```

---

## 🔄 **Data Flow**

### **Request Processing**

1. **API Request**: Receive live trading request from API
2. **Validation**: Validate request parameters and risk limits
3. **Config Loading**: Load strategy configuration using ConfigManager
4. **Config Merging**: Apply request overrides to base configuration
5. **Engine Init**: Initialize EventDrivenStrategyEngine with live execution mode
6. **Background Execution**: Start strategy execution in background task
7. **Monitoring**: Continuous monitoring of strategy health and performance
8. **Risk Management**: Continuous risk limit checking and breach handling

### **Live Trading Client Validation**

Following [12_live_trading_quality_gates.md](../../.cursor/tasks/12_live_trading_quality_gates.md):

#### **Client Requirement Validation**
- **Mode-based client requirements**: Each strategy mode requires specific clients
- **Configuration-driven**: Client requirements determined by config YAML files
- **Environment-specific**: Testnet vs production client configurations
- **Venue-specific**: Different venues require different clients

#### **Client Availability Validation**
- **API connectivity**: All required APIs must be accessible
- **Authentication**: All required authentication must be valid
- **Rate limits**: Rate limits must be within acceptable ranges
- **Client initialization**: All clients must initialize successfully

#### **Environment-Specific Validation**
- **Testnet environment**: All clients must connect to testnet endpoints
- **Production environment**: All clients must connect to production endpoints
- **Environment-specific configuration**: Testnet vs production must be correctly configured

### **Configuration Integration**

```python
# Create config for live trading using config infrastructure
config = self._create_config(request)

# Add request-specific overrides for live trading
base_config.update({
    'share_class': request.share_class,
    'initial_capital': float(request.initial_capital),
    'execution_mode': 'live',
    'live_trading': {
        'initial_capital': float(request.initial_capital),
        'risk_limits': request.risk_limits,
        'started_at': datetime.utcnow().isoformat()
    }
})
```

**Configuration Details**: See [CONFIGURATION.md](../CONFIGURATION.md) for comprehensive configuration management.

### **Singleton Pattern Requirements**

Following [13_singleton_pattern_requirements.md](../../.cursor/tasks/13_singleton_pattern_requirements.md):

#### **Single Instance Per Component**
- **Each component**: Must be a SINGLE instance across the entire run
- **No duplication**: Never initialize the same component twice in different places
- **Shared state**: All components share the same state and data

#### **Shared Configuration and Data Provider**
- **Single config instance**: All components must share the SAME config instance
- **Single data provider**: All components must share the SAME data provider instance
- **Synchronized data flows**: All components use the same data source

### **Venue-Based Execution Architecture**

Following [VENUE_ARCHITECTURE.md](../VENUE_ARCHITECTURE.md):

#### **Live Mode Venue Execution**
- **Real execution**: Using external APIs (testnet or production)
- **Real delays**: Transaction confirmations and API rate limits
- **Retry logic**: Exponential backoff for failed operations
- **External interfaces**: Provide data to position monitor

#### **Environment-Specific Venue Configuration**
- **BASIS_ENVIRONMENT**: Controls venue credential routing (dev/staging/prod)
- **BASIS_EXECUTION_MODE**: Controls venue execution behavior (backtest simulation vs live execution)
- **Venue credentials**: Environment-specific credentials from env.unified
- **Testnet vs production**: Different endpoints and networks based on environment

---

## 🔗 **Dependencies**

### **Core Dependencies**

- **EventDrivenStrategyEngine**: [15_EVENT_DRIVEN_STRATEGY_ENGINE.md](15_EVENT_DRIVEN_STRATEGY_ENGINE.md) - Main orchestration engine
- **Data Provider**: [09_DATA_PROVIDER.md](09_DATA_PROVIDER.md) - Live data access
- **Configuration**: [CONFIGURATION.md](../CONFIGURATION.md) - Strategy configuration management

### **Infrastructure Dependencies**

- **ConfigManager**: Unified configuration management
- **Live Data Provider**: Real-time market data access
- **Execution Interfaces**: Real execution interfaces for live trading

---

## ⚠️ **Error Codes**

### **Live Trading Service Error Codes**

| Code | Description | Severity |
|------|-------------|----------|
| **LT-001** | Live trading request validation failed | HIGH |
| **LT-002** | Config creation failed | HIGH |
| **LT-003** | Strategy engine initialization failed | CRITICAL |
| **LT-004** | Live trading execution failed | CRITICAL |
| **LT-005** | Live trading monitoring failed | MEDIUM |
| **LT-006** | Live trading stop failed | MEDIUM |
| **LT-007** | Risk check failed | HIGH |

### **Error Handling**

```python
# Request validation
errors = request.validate()
if errors:
    logger.error(f"[LT-001] Live trading request validation failed: {', '.join(errors)}")
    raise ValueError(f"Invalid request: {', '.join(errors)}")

# Engine initialization
try:
    strategy_engine = EventDrivenStrategyEngine(config)
except Exception as e:
    logger.error(f"[LT-003] Strategy engine initialization failed: {e}")
    raise

# Live trading execution
try:
    await strategy_engine.run_live()
except Exception as e:
    logger.error(f"[LT-004] Live trading {request_id} failed: {e}", exc_info=True)
    # Update status to failed but continue monitoring
```

**Error System Details**: See [17_HEALTH_ERROR_SYSTEMS.md](17_HEALTH_ERROR_SYSTEMS.md) for comprehensive error handling.

---

## 🛡️ **Risk Management**

### **Risk Limits**

```python
risk_limits = {
    'max_drawdown': 0.10,        # 10% maximum drawdown
    'max_position_size': 100000,  # Maximum position size
    'max_daily_loss': 5000,      # Maximum daily loss
    'health_factor_threshold': 1.2,  # Minimum health factor
    'margin_ratio_threshold': 0.2    # Minimum margin ratio
}
```

### **Risk Monitoring**

```python
async def check_risk_limits(self, request_id: str) -> Dict[str, Any]:
    """Check if risk limits are being breached."""
    
    breaches = []
    
    # Check max drawdown
    max_drawdown = risk_limits.get('max_drawdown')
    if max_drawdown is not None:
        current_drawdown = abs(strategy_info['current_drawdown'])
        if current_drawdown > max_drawdown:
            breaches.append({
                'type': 'max_drawdown',
                'limit': max_drawdown,
                'current': current_drawdown,
                'breach_pct': ((current_drawdown - max_drawdown) / max_drawdown) * 100
            })
    
    # Check other risk limits...
    
    if breaches:
        return {
            'status': 'breach_detected',
            'breaches': breaches,
            'action_required': True
        }
    else:
        return {
            'status': 'within_limits',
            'breaches': [],
            'action_required': False
        }
```

### **Emergency Stop**

```python
async def emergency_stop(self, request_id: str, reason: str = "Emergency stop") -> bool:
    """Emergency stop a live trading strategy."""
    logger.warning(f"Emergency stop requested for {request_id}: {reason}")
    
    # Stop the strategy
    success = await self.stop_live_trading(request_id)
    
    if success and request_id in self.completed_strategies:
        # Add emergency stop info
        self.completed_strategies[request_id]['emergency_stop'] = {
            'reason': reason,
            'stopped_at': datetime.utcnow()
        }
    
    return success
```

---

## 📊 **Performance Monitoring**

### **Performance Metrics**

```python
async def get_performance_metrics(self, request_id: str) -> Optional[Dict[str, Any]]:
    """Get performance metrics for a live trading strategy."""
    
    # Calculate performance metrics
    initial_capital = strategy_info['request'].initial_capital
    current_pnl = strategy_info['total_pnl']
    current_value = float(initial_capital) + current_pnl
    return_pct = (current_pnl / float(initial_capital)) * 100
    
    return {
        'initial_capital': float(initial_capital),
        'current_value': current_value,
        'total_pnl': current_pnl,
        'return_pct': return_pct,
        'total_trades': strategy_info['total_trades'],
        'current_drawdown': strategy_info['current_drawdown'],
        'uptime_hours': (datetime.utcnow() - strategy_info['started_at']).total_seconds() / 3600,
        'engine_status': engine_status,
        'last_heartbeat': strategy_info['last_heartbeat']
    }
```

### **Health Monitoring**

```python
async def health_check(self) -> Dict[str, Any]:
    """Perform health check on all running strategies."""
    health_status = {
        'total_strategies': len(self.running_strategies),
        'healthy_strategies': 0,
        'unhealthy_strategies': 0,
        'strategies': []
    }
    
    current_time = datetime.utcnow()
    
    for request_id, strategy_info in self.running_strategies.items():
        last_heartbeat = strategy_info['last_heartbeat']
        time_since_heartbeat = (current_time - last_heartbeat).total_seconds()
        
        # Consider unhealthy if no heartbeat for more than 5 minutes
        is_healthy = time_since_heartbeat < 300
        
        if is_healthy:
            health_status['healthy_strategies'] += 1
        else:
            health_status['unhealthy_strategies'] += 1
        
        health_status['strategies'].append({
            'request_id': request_id,
            'strategy_name': strategy_info['request'].strategy_name,
            'is_healthy': is_healthy,
            'last_heartbeat': last_heartbeat,
            'time_since_heartbeat_seconds': time_since_heartbeat
        })
    
    return health_status
```

---

## 🧪 **Usage Examples**

### **Basic Live Trading**

```python
from basis_strategy_v1.core.services.live_service import LiveTradingService
from decimal import Decimal

# Create service
service = LiveTradingService()

# Create request
request = service.create_request(
    strategy_name='pure_lending',
    initial_capital=Decimal('100000'),
    share_class='USDT',
    risk_limits={
        'max_drawdown': 0.05,  # 5% max drawdown
        'max_daily_loss': 1000  # $1000 max daily loss
    }
)

# Start live trading
request_id = await service.start_live_trading(request)
print(f"Live trading started: {request_id}")

# Monitor status
status = await service.get_status(request_id)
print(f"Status: {status['status']}")
print(f"Total trades: {status['total_trades']}")
print(f"Total P&L: {status['total_pnl']}")
```

### **Risk Management**

```python
# Check risk limits
risk_check = await service.check_risk_limits(request_id)
if risk_check['status'] == 'breach_detected':
    print("Risk limit breached!")
    for breach in risk_check['breaches']:
        print(f"- {breach['type']}: {breach['current']:.2%} (limit: {breach['limit']:.2%})")
    
    # Emergency stop if needed
    if breach['breach_pct'] > 50:  # 50% over limit
        await service.emergency_stop(request_id, "Risk limit breach exceeded 50%")
```

### **Performance Monitoring**

```python
# Get performance metrics
metrics = await service.get_performance_metrics(request_id)
if metrics:
    print(f"Current value: ${metrics['current_value']:,.2f}")
    print(f"Total return: {metrics['return_pct']:.2%}")
    print(f"Uptime: {metrics['uptime_hours']:.1f} hours")
    print(f"Total trades: {metrics['total_trades']}")
```

### **Strategy Management**

```python
# Get all running strategies
running_strategies = await service.get_all_running_strategies()
print(f"Running strategies: {len(running_strategies)}")

for strategy in running_strategies:
    print(f"- {strategy['strategy_name']}: {strategy['status']}")

# Stop a strategy
success = await service.stop_live_trading(request_id)
if success:
    print("Strategy stopped successfully")
```

---

## 🔄 **Live vs Backtest Differences**

### **Execution Mode**

| Aspect | Backtest | Live Trading |
|--------|----------|--------------|
| **Data Source** | Historical CSV files | Real-time APIs |
| **Execution** | Simulated | Real trades |
| **Timing** | Historical timestamps | Real-time intervals |
| **Risk Management** | Post-hoc analysis | Real-time monitoring |
| **Error Handling** | Fail-fast | Retry with exponential backoff |
| **Monitoring** | Progress tracking | Heartbeat monitoring |

### **Configuration Differences**

```python
# Backtest configuration
backtest_config = {
    'execution_mode': 'backtest',
    'data': {'data_dir': 'data/'},
    'backtest': {
        'start_date': '2024-01-01',
        'end_date': '2024-12-31'
    }
}

# Live trading configuration
live_config = {
    'execution_mode': 'live',
    'live_trading': {
        'risk_limits': {...},
        'monitoring_interval': 60,
        'heartbeat_timeout': 300
    }
}
```

---

## 📋 **Implementation Status** ✅ **FULLY IMPLEMENTED**

- ✅ **Request Validation**: Comprehensive parameter and risk limit validation
- ✅ **Configuration Management**: Integration with ConfigManager for live trading configs
- ✅ **Engine Orchestration**: Proper EventDrivenStrategyEngine initialization for live mode
- ✅ **Background Execution**: Asynchronous strategy execution with monitoring
- ✅ **Risk Management**: Continuous risk limit monitoring and emergency stop
- ✅ **Performance Tracking**: Real-time performance metrics and P&L tracking
- ✅ **Health Monitoring**: Heartbeat monitoring and health checks
- ✅ **Error Handling**: Comprehensive error handling with retry logic
- ✅ **State Management**: Running and completed strategy tracking
- ✅ **Emergency Controls**: Emergency stop and risk breach handling
- ✅ **Live Trading Client Validation**: Client requirement validation, API connectivity, authentication
- ✅ **Singleton Pattern**: Single instance per component with shared config and data provider
- ✅ **Venue-Based Execution**: Live mode venue execution with environment-specific configuration
- ✅ **Mode-Agnostic Architecture**: Components work for both backtest and live modes

---

## 🎯 **Next Steps**

1. **Advanced Risk Management**: Dynamic risk limit adjustment
2. **Real-time Alerts**: WebSocket-based real-time notifications
3. **Portfolio Management**: Multi-strategy portfolio coordination
4. **Performance Analytics**: Advanced performance attribution
5. **Regulatory Compliance**: Audit trails and compliance reporting

## 🔍 **Quality Gate Validation**

Following [17_quality_gate_validation_requirements.md](../../.cursor/tasks/17_quality_gate_validation_requirements.md):

### **Mandatory Quality Gate Validation**
**BEFORE CONSIDERING TASK COMPLETE**, you MUST:

1. **Run Live Trading Quality Gates**:
   ```bash
   python scripts/test_pure_lending_quality_gates.py
   python scripts/test_btc_basis_quality_gates.py
   ```

2. **Verify Live Trading Client Validation**:
   - All required clients for strategy mode are available
   - All clients initialize successfully
   - All clients can connect to external services
   - Client configurations are valid and complete

3. **Verify Architecture Compliance**:
   - Singleton pattern: All components use single instances
   - Mode-agnostic: Components work for both backtest and live modes
   - Venue-based execution: Live mode venue execution works correctly

4. **Document Results**:
   - Live trading client validation results
   - Architecture compliance status
   - Any remaining issues or limitations

**DO NOT PROCEED TO NEXT TASK** until quality gates validate the live trading service is working correctly.

---

**Status**: Live Trading Service is complete and fully operational! 🎉

*Last Updated: January 6, 2025*
