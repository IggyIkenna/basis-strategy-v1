# Component Spec: Backtest Service 🧪

**Component**: Backtest Service  
**Responsibility**: Orchestrate backtest execution using EventDrivenStrategyEngine  
**Priority**: ⭐⭐⭐ CRITICAL (Enables backtesting functionality)  
**Backend File**: `backend/src/basis_strategy_v1/core/services/backtest_service.py` ✅ **IMPLEMENTED**  
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

Orchestrate backtest execution using the EventDrivenStrategyEngine with proper request validation, configuration management, and result storage.

**Key Principles**:
- **Request Validation**: Validate backtest parameters before execution
- **Configuration Management**: Load and merge strategy configurations
- **Engine Orchestration**: Initialize and execute EventDrivenStrategyEngine
- **Result Storage**: Save results to filesystem for quality gates
- **Error Handling**: Comprehensive error handling with specific error codes
- **State Management**: Track running and completed backtests

---

## 🏗️ **Architecture**

### **Service Flow**

```
API Request → Request Validation → Config Creation → Engine Initialization → Execution → Result Storage
```

### **Core Classes**

#### **BacktestService**
Main service class that orchestrates backtest execution.

#### **BacktestRequest**
Request object containing all backtest parameters:
- `strategy_name`: Strategy to execute
- `start_date` / `end_date`: Backtest time range
- `initial_capital`: Starting capital amount
- `share_class`: Share class ('USDT' or 'ETH')
- `config_overrides`: Optional configuration overrides
- `debug_mode`: Enable debug logging

#### **MockExecutionEngine**
Mock execution engine for backtesting (legacy support).

---

## 🔧 **Key Methods**

### **Request Management**

```python
def create_request(self, strategy_name: str, start_date: datetime, end_date: datetime,
                  initial_capital: Decimal, share_class: str, 
                  config_overrides: Dict[str, Any] = None,
                  debug_mode: bool = False) -> BacktestRequest:
    """Create a backtest request with validation."""
```

### **Backtest Execution**

```python
async def run_backtest(self, request: BacktestRequest) -> str:
    """
    Run a backtest using Phase 3 architecture with proper dependency injection.
    
    Flow:
    1. Validate request parameters
    2. Load configuration using ConfigManager
    3. Create data provider using DataProviderFactory
    4. Initialize EventDrivenStrategyEngine
    5. Execute backtest synchronously
    6. Save results to filesystem
    """
```

### **Status and Results**

```python
async def get_status(self, request_id: str) -> Dict[str, Any]:
    """Get the status of a backtest (running/completed/failed)."""

async def get_result(self, request_id: str) -> Optional[Dict[str, Any]]:
    """Get the result of a completed backtest."""

async def cancel_backtest(self, request_id: str) -> bool:
    """Cancel a running backtest."""
```

---

## 🔄 **Data Flow**

### **Request Processing**

1. **API Request**: Receive backtest request from API
2. **Validation**: Validate request parameters (dates, capital, share class)
3. **Config Loading**: Load strategy configuration using ConfigManager
4. **Config Merging**: Apply request overrides to base configuration
5. **Data Provider**: Create data provider using DataProviderFactory
6. **Engine Init**: Initialize EventDrivenStrategyEngine with all dependencies
7. **Execution**: Execute backtest using engine's run_backtest method
8. **Result Storage**: Save results to filesystem for quality gates

### **Backtest Mode Quality Gate Validation**

Following [11_backtest_mode_quality_gates.md](../../.cursor/tasks/11_backtest_mode_quality_gates.md):

#### **Position Monitor Initialization**
- **Strategy mode capital**: Position monitor must be initialized with proper capital based on strategy mode
- **Initial token allocation**: Must have initial capital in at least one token
- **No empty state**: Position monitor cannot start in empty state

#### **First Runtime Loop Validation**
- **Required actions**: Must perform at least one of:
  - Wallet transfers
  - Trades
  - Smart contract actions
- **No "do nothing"**: Strategy cannot be in "do nothing" state
- **Position setup**: Must set up desired positions on first runtime loop

#### **Tight Loop Architecture**
- **Sequential execution**: position_monitor → exposure_monitor → risk_monitor → pnl_monitor
- **State persistence**: All components maintain state across timesteps
- **No reset**: No component resets state between iterations

### **Configuration Integration**

```python
# Get validated config for the specific strategy mode
config_manager = get_config_manager()
config = config_manager.get_complete_config(mode=request.strategy_name)

# Apply config overrides from request
if request.config_overrides:
    config.update(request.config_overrides)

# Get data provider (already loaded with all data at startup)
data_provider = create_data_provider(
    data_dir=config_manager.get_data_directory(),
    startup_mode=config_manager.get_startup_mode(),
    config=config,
    strategy_mode=request.strategy_name,
    backtest_start_date=request.start_date.strftime('%Y-%m-%d'),
    backtest_end_date=request.end_date.strftime('%Y-%m-%d')
)
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

#### **Backtest Mode Venue Simulation**
- **Simulated execution**: Using historical data and execution cost models
- **No real API calls**: All operations simulated
- **Dummy venue calls**: Execution interfaces make dummy calls to venues but don't wait for responses
- **Immediate completion**: Mark themselves complete to trigger downstream chain of updates
- **Data provider handles**: CSV vs DB routing for backtest mode

#### **Venue Configuration Integration**
- **Environment variables**: BASIS_EXECUTION_MODE=backtest controls venue simulation behavior
- **Venue data loading**: Historical data provider loads venue-specific data for simulation
- **Execution cost modeling**: Fixed slippage from execution cost model

---

## 🔗 **Dependencies**

### **Core Dependencies**

- **EventDrivenStrategyEngine**: [15_EVENT_DRIVEN_STRATEGY_ENGINE.md](15_EVENT_DRIVEN_STRATEGY_ENGINE.md) - Main orchestration engine
- **Data Provider**: [09_DATA_PROVIDER.md](09_DATA_PROVIDER.md) - Historical data access
- **Configuration**: [CONFIGURATION.md](../CONFIGURATION.md) - Strategy configuration management

### **Infrastructure Dependencies**

- **ConfigManager**: Unified configuration management
- **DataProviderFactory**: Data provider creation
- **ResultStore**: Result persistence for quality gates

---

## ⚠️ **Error Codes**

### **Backtest Service Error Codes**

| Code | Description | Severity |
|------|-------------|----------|
| **BT-001** | Backtest request validation failed | HIGH |
| **BT-002** | Config creation failed | HIGH |
| **BT-003** | Strategy engine initialization failed | CRITICAL |
| **BT-004** | Backtest execution failed | CRITICAL |
| **BT-005** | Result processing failed | MEDIUM |

### **Error Handling**

```python
# Request validation
errors = request.validate()
if errors:
    logger.error(f"[BT-001] Backtest request validation failed: {', '.join(errors)}")
    raise ValueError(f"Invalid request: {', '.join(errors)}")

# Config creation
try:
    config = self._create_config(request)
except Exception as e:
    logger.error(f"[BT-002] Config creation failed: {e}")
    raise

# Engine initialization
try:
    strategy_engine = EventDrivenStrategyEngine(...)
except Exception as e:
    logger.error(f"[BT-003] Strategy engine initialization failed: {e}")
    raise
```

**Error System Details**: See [17_HEALTH_ERROR_SYSTEMS.md](17_HEALTH_ERROR_SYSTEMS.md) for comprehensive error handling.

---

## 🧪 **Usage Examples**

### **Basic Backtest Execution**

```python
from basis_strategy_v1.core.services.backtest_service import BacktestService
from datetime import datetime
from decimal import Decimal

# Create service
service = BacktestService()

# Create request
request = service.create_request(
    strategy_name='pure_lending',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    initial_capital=Decimal('100000'),
    share_class='USDT',
    debug_mode=True
)

# Run backtest
request_id = await service.run_backtest(request)
print(f"Backtest started: {request_id}")

# Check status
status = await service.get_status(request_id)
print(f"Status: {status['status']}, Progress: {status['progress']}")

# Get results when completed
if status['status'] == 'completed':
    results = await service.get_result(request_id)
    print(f"Final value: {results['final_value']}")
    print(f"Total return: {results['total_return']}")
```

### **Backtest with Configuration Overrides**

```python
# Create request with custom configuration
request = service.create_request(
    strategy_name='btc_basis',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    initial_capital=Decimal('50000'),
    share_class='ETH',
    config_overrides={
        'strategy': {
            'target_apy': 0.15,  # 15% target APY
            'max_drawdown': 0.05  # 5% max drawdown
        }
    }
)

# Run backtest
request_id = await service.run_backtest(request)
```

### **Backtest Monitoring**

```python
# Monitor backtest progress
while True:
    status = await service.get_status(request_id)
    
    if status['status'] == 'completed':
        results = await service.get_result(request_id)
        print("Backtest completed!")
        print(f"Annualized return: {results['annualized_return']:.2%}")
        print(f"Max drawdown: {results['max_drawdown']:.2%}")
        break
    elif status['status'] == 'failed':
        print(f"Backtest failed: {status.get('error', 'Unknown error')}")
        break
    else:
        print(f"Progress: {status['progress']:.1%}")
        await asyncio.sleep(5)  # Check every 5 seconds
```

---

## 📊 **Result Processing**

### **Result Data Structure**

```python
result_data = {
    'request_id': request_id,
    'strategy_name': request.strategy_name,
    'share_class': request.share_class,
    'start_date': request.start_date.isoformat(),
    'end_date': request.end_date.isoformat(),
    'initial_capital': str(request.initial_capital),
    'final_value': str(results.get('final_value', 0)),
    'total_return': str(results.get('total_return', 0)),
    'annualized_return': str(results.get('annualized_return', 0)),
    'sharpe_ratio': str(results.get('sharpe_ratio', 0)),
    'max_drawdown': str(results.get('max_drawdown', 0)),
    'target_apy': results.get('target_apy'),
    'target_max_drawdown': results.get('target_max_drawdown'),
    'apy_vs_target': results.get('apy_vs_target'),
    'drawdown_vs_target': results.get('drawdown_vs_target'),
    'total_trades': results.get('total_trades', 0),
    'total_fees': str(results.get('total_fees', 0)),
    'equity_curve': results.get('equity_curve'),
    'metrics_summary': results.get('metrics_summary', {})
}
```

### **Quality Gate Integration**

```python
# Save results to filesystem for quality gates
try:
    from ...infrastructure.persistence.result_store import ResultStore
    result_store = ResultStore()
    await result_store.save_result(request_id, result_data)
    logger.info(f"✅ Results saved to filesystem for request {request_id}")
except Exception as e:
    logger.warning(f"⚠️ Failed to save results to filesystem: {e}")
    # Continue without failing the backtest
```

---

## 🔄 **State Management**

### **Running Backtests**

```python
self.running_backtests: Dict[str, Dict[str, Any]] = {
    request_id: {
        'request': request,
        'config': config,
        'strategy_engine': strategy_engine,
        'status': 'running',
        'started_at': datetime.utcnow(),
        'progress': 0
    }
}
```

### **Completed Backtests**

```python
self.completed_backtests: Dict[str, Dict[str, Any]] = {
    request_id: {
        'request': request,
        'config': config,
        'strategy_engine': strategy_engine,
        'status': 'completed',
        'started_at': datetime.utcnow(),
        'completed_at': datetime.utcnow(),
        'results': results
    }
}
```

### **Memory Management**

```python
# Clean up running backtests to free memory and prevent state persistence
if request_id in self.running_backtests:
    del self.running_backtests[request_id]
```

---

## 📋 **Implementation Status** ✅ **FULLY IMPLEMENTED**

- ✅ **Request Validation**: Comprehensive parameter validation with error codes
- ✅ **Configuration Management**: Integration with ConfigManager and DataProviderFactory
- ✅ **Engine Orchestration**: Proper EventDrivenStrategyEngine initialization and execution
- ✅ **Result Storage**: Filesystem persistence for quality gates
- ✅ **Error Handling**: Comprehensive error handling with specific error codes
- ✅ **State Management**: Running and completed backtest tracking
- ✅ **Memory Management**: Proper cleanup to prevent state persistence
- ✅ **Quality Gate Integration**: Result validation against targets
- ✅ **Debug Support**: Debug mode for detailed logging
- ✅ **API Integration**: Ready for API endpoint integration
- ✅ **Backtest Mode Quality Gates**: Position monitor initialization, first runtime loop validation, tight loop architecture
- ✅ **Singleton Pattern**: Single instance per component with shared config and data provider
- ✅ **Venue-Based Execution**: Backtest mode venue simulation with execution cost modeling
- ✅ **Mode-Agnostic Architecture**: Components work for both backtest and live modes

---

## 🎯 **Next Steps**

1. **Performance Optimization**: Parallel backtest execution
2. **Advanced Monitoring**: Real-time progress updates via WebSocket
3. **Result Caching**: Cache results for repeated backtests
4. **Batch Processing**: Multiple backtest execution
5. **Advanced Validation**: Strategy-specific parameter validation

## 🔍 **Quality Gate Validation**

Following [17_quality_gate_validation_requirements.md](../../.cursor/tasks/17_quality_gate_validation_requirements.md):

### **Mandatory Quality Gate Validation**
**BEFORE CONSIDERING TASK COMPLETE**, you MUST:

1. **Run Backtest Quality Gates**:
   ```bash
   python scripts/test_pure_lending_quality_gates.py
   python scripts/test_btc_basis_quality_gates.py
   ```

2. **Verify Backtest Mode Validation**:
   - Position monitor properly initialized with strategy mode capital
   - First runtime loop performs required actions
   - No "do nothing" strategy state
   - Tight loop architecture maintained

3. **Verify Architecture Compliance**:
   - Singleton pattern: All components use single instances
   - Mode-agnostic: Components work for both backtest and live modes
   - Venue-based execution: Backtest mode venue simulation works correctly

4. **Document Results**:
   - Backtest mode validation results
   - Architecture compliance status
   - Any remaining issues or limitations

**DO NOT PROCEED TO NEXT TASK** until quality gates validate the backtest service is working correctly.

---

**Status**: Backtest Service is complete and fully operational! 🎉

*Last Updated: January 6, 2025*
