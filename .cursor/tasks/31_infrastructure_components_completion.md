# INFRASTRUCTURE COMPONENTS COMPLETION

## OVERVIEW
This task completes the missing infrastructure component implementations identified in the implementation gap report. These components provide essential services and utilities for the system. The task covers Math Utilities, Health & Error Systems, Results Store, Configuration, and Event Logger validation.

**Reference**: `docs/specs/16_MATH_UTILITIES.md` - Centralized math functions specification  
**Reference**: `docs/specs/17_HEALTH_ERROR_SYSTEMS.md` - Error codes and health monitoring specification  
**Reference**: `docs/specs/18_RESULTS_STORE.md` - Queue-based async storage specification  
**Reference**: `docs/specs/19_CONFIGURATION.md` - Config loading and validation specification  
**Reference**: `docs/specs/08_EVENT_LOGGER.md` - Async event logging specification  
**Reference**: `docs/REFERENCE_ARCHITECTURE_CANONICAL.md` - ADR-006 (Async I/O exceptions)  
**Reference**: `docs/IMPLEMENTATION_GAP_REPORT.md` - Component gap analysis

## CRITICAL REQUIREMENTS

### 1. Math Utilities Standardization
- **Centralized math functions**: Implement centralized math utility functions
- **Liquidity index calculations**: Implement liquidity index calculations
- **Market price conversions**: Implement market price conversion utilities
- **Currency conversions**: Implement currency conversion utilities
- **Error codes**: Add missing error codes MATH-001 through MATH-013

### 2. Health & Error Systems Completion
- **Error code registry**: Complete error code registry system
- **Health monitoring**: Complete health monitoring system
- **Error handling**: Complete error handling system
- **Health endpoints**: Complete health endpoint implementation
- **Error codes**: Add missing error codes HEALTH-001 through HEALTH-013

### 3. Results Store Validation
- **Async implementation**: Validate async results store implementation
- **Queue-based storage**: Validate queue-based async storage
- **FIFO ordering**: Validate FIFO ordering guarantees
- **Error handling**: Validate error handling in async operations
- **Error codes**: Add missing error codes RS-001 through RS-013

### 4. Configuration Validation
- **Config loading**: Validate config loading system
- **Config validation**: Validate config validation system
- **Environment variables**: Validate environment variable handling
- **Config slicing**: Validate config slicing functionality
- **Error codes**: Add missing error codes CONFIG-001 through CONFIG-013

### 5. Event Logger Validation
- **Async I/O**: Validate async I/O implementation per ADR-006
- **Event logging**: Validate event logging functionality
- **Structured logging**: Validate structured logging
- **Log retention**: Validate log retention policies
- **Error codes**: Add missing error codes EVENT-001 through EVENT-013

## IMPLEMENTATION STRATEGY

### Phase 1: Math Utilities Standardization
1. **Create/Update**: `backend/src/basis_strategy_v1/core/utilities/math_utilities.py`
2. **Implement centralized functions**: Liquidity index, market prices, conversions
3. **Add utility manager**: Centralized utility manager for all components
4. **Add error handling**: Comprehensive error handling
5. **Add error codes**: Implement comprehensive error code system

### Phase 2: Health & Error Systems Completion
1. **Complete**: `backend/src/basis_strategy_v1/core/health/`
2. **Complete error code registry**: `backend/src/basis_strategy_v1/core/error_codes/error_code_registry.py`
3. **Complete health monitoring**: `backend/src/basis_strategy_v1/core/health/unified_health_manager.py`
4. **Complete health endpoints**: Health endpoint implementation
5. **Add error codes**: Implement comprehensive error code system

### Phase 3: Results Store Validation
1. **Validate**: `backend/src/basis_strategy_v1/infrastructure/persistence/async_results_store.py`
2. **Validate async implementation**: Queue-based async storage
3. **Validate FIFO ordering**: FIFO ordering guarantees
4. **Validate error handling**: Error handling in async operations
5. **Add error codes**: Implement comprehensive error code system

### Phase 4: Configuration Validation
1. **Validate**: `backend/src/basis_strategy_v1/infrastructure/config/`
2. **Validate config loading**: Config loading system
3. **Validate config validation**: Config validation system
4. **Validate environment handling**: Environment variable handling
5. **Add error codes**: Implement comprehensive error code system

### Phase 5: Event Logger Validation
1. **Validate**: `backend/src/basis_strategy_v1/core/strategies/components/event_logger.py`
2. **Validate async I/O**: Async I/O implementation per ADR-006
3. **Validate event logging**: Event logging functionality
4. **Validate structured logging**: Structured logging
5. **Add error codes**: Implement comprehensive error code system

## REQUIRED IMPLEMENTATION

### 1. Math Utilities
```python
# backend/src/basis_strategy_v1/core/utilities/math_utilities.py
class MathUtilities:
    """Centralized math utility functions for all components."""
    
    def __init__(self, config: Dict, data_provider: BaseDataProvider):
        self.config = config
        self.data_provider = data_provider
    
    def get_liquidity_index(self, token: str, timestamp: pd.Timestamp) -> float:
        """Get liquidity index for a token at a specific timestamp."""
        try:
            return self.data_provider.get_liquidity_index(token, timestamp)
        except Exception as e:
            raise MathUtilitiesError(f"MATH-001: Failed to get liquidity index for {token}: {e}")
    
    def get_market_price(self, token: str, currency: str, timestamp: pd.Timestamp) -> float:
        """Get market price for token in specified currency at timestamp."""
        try:
            return self.data_provider.get_market_price(token, currency, timestamp)
        except Exception as e:
            raise MathUtilitiesError(f"MATH-002: Failed to get market price for {token}/{currency}: {e}")
    
    def convert_to_usdt(self, amount: float, token: str, timestamp: pd.Timestamp) -> float:
        """Convert token amount to USDT equivalent."""
        try:
            price = self.get_market_price(token, 'USDT', timestamp)
            return amount * price
        except Exception as e:
            raise MathUtilitiesError(f"MATH-003: Failed to convert {amount} {token} to USDT: {e}")
    
    def convert_from_liquidity_index(self, amount: float, token: str, timestamp: pd.Timestamp) -> float:
        """Convert from liquidity index (e.g., aUSDT to USDT)."""
        try:
            liquidity_index = self.get_liquidity_index(token, timestamp)
            return amount / liquidity_index
        except Exception as e:
            raise MathUtilitiesError(f"MATH-004: Failed to convert from liquidity index for {token}: {e}")
```

### 2. Health & Error Systems
```python
# backend/src/basis_strategy_v1/core/health/unified_health_manager.py
class UnifiedHealthManager:
    """Unified health management system."""
    
    def __init__(self):
        self.health_checkers = {}
        self.error_registry = ErrorCodeRegistry()
    
    def register_health_checker(self, component_name: str, checker: HealthChecker):
        """Register a health checker for a component."""
        self.health_checkers[component_name] = checker
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        try:
            status = {
                'overall_status': 'healthy',
                'components': {},
                'timestamp': pd.Timestamp.now(),
                'errors': []
            }
            
            for component_name, checker in self.health_checkers.items():
                try:
                    component_status = checker.check_health()
                    status['components'][component_name] = component_status
                    
                    if component_status['status'] != 'healthy':
                        status['overall_status'] = 'unhealthy'
                        status['errors'].extend(component_status.get('errors', []))
                        
                except Exception as e:
                    status['components'][component_name] = {
                        'status': 'error',
                        'error': str(e),
                        'timestamp': pd.Timestamp.now()
                    }
                    status['overall_status'] = 'unhealthy'
                    status['errors'].append(f"HEALTH-001: Health check failed for {component_name}: {e}")
            
            return status
            
        except Exception as e:
            return {
                'overall_status': 'error',
                'error': f"HEALTH-002: Failed to get health status: {e}",
                'timestamp': pd.Timestamp.now()
            }
```

### 3. Results Store
```python
# backend/src/basis_strategy_v1/infrastructure/persistence/async_results_store.py
class AsyncResultsStore:
    """Queue-based async results store with FIFO ordering guarantees."""
    
    def __init__(self, results_dir: str, execution_mode: str):
        self.results_dir = Path(results_dir)
        self.execution_mode = execution_mode
        self.queue = asyncio.Queue()
        self.worker_task = None
        self._start_worker()
    
    def _start_worker(self):
        """Start background worker for processing queue."""
        self.worker_task = asyncio.create_task(self._process_queue())
    
    async def _process_queue(self):
        """Process queue items sequentially to maintain FIFO ordering."""
        while True:
            try:
                item = await self.queue.get()
                await self._process_item(item)
                self.queue.task_done()
            except Exception as e:
                logger.error(f"RS-001: Error processing queue item: {e}")
    
    async def _process_item(self, item: Dict[str, Any]):
        """Process a single queue item."""
        try:
            if item['type'] == 'backtest_result':
                await self._save_backtest_result(item['data'])
            elif item['type'] == 'live_result':
                await self._save_live_result(item['data'])
            else:
                raise ValueError(f"RS-002: Unknown item type: {item['type']}")
        except Exception as e:
            logger.error(f"RS-003: Error processing item: {e}")
    
    async def save_backtest_result(self, result_data: Dict[str, Any]):
        """Save backtest result asynchronously."""
        try:
            await self.queue.put({
                'type': 'backtest_result',
                'data': result_data,
                'timestamp': pd.Timestamp.now()
            })
        except Exception as e:
            raise AsyncResultsStoreError(f"RS-004: Failed to queue backtest result: {e}")
```

### 4. Configuration
```python
# backend/src/basis_strategy_v1/infrastructure/config/config_loader.py
class ConfigLoader:
    """Configuration loading and validation system."""
    
    def __init__(self):
        self.global_config = None
        self.validated_config = None
    
    def load_global_config(self) -> Dict[str, Any]:
        """Load and validate global configuration."""
        try:
            # Load mode configurations
            modes_config = self._load_modes_config()
            
            # Load venue configurations
            venues_config = self._load_venues_config()
            
            # Load share class configurations
            share_classes_config = self._load_share_classes_config()
            
            # Combine configurations
            self.global_config = {
                'modes': modes_config,
                'venues': venues_config,
                'share_classes': share_classes_config
            }
            
            # Validate configuration
            self.validated_config = self._validate_config(self.global_config)
            
            return self.validated_config
            
        except Exception as e:
            raise ConfigLoaderError(f"CONFIG-001: Failed to load global config: {e}")
    
    def slice_config_for_mode(self, mode: str, overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Slice configuration for specific mode."""
        try:
            if not self.validated_config:
                raise ValueError("CONFIG-002: Global config not loaded")
            
            if mode not in self.validated_config['modes']:
                raise ValueError(f"CONFIG-003: Mode {mode} not found in configuration")
            
            # Get mode configuration
            mode_config = self.validated_config['modes'][mode].copy()
            
            # Apply overrides if provided
            if overrides:
                mode_config = self._apply_overrides(mode_config, overrides)
            
            return mode_config
            
        except Exception as e:
            raise ConfigLoaderError(f"CONFIG-004: Failed to slice config for mode {mode}: {e}")
```

### 5. Event Logger
```python
# backend/src/basis_strategy_v1/core/strategies/components/event_logger.py
class EventLogger:
    """Async event logger with structured logging."""
    
    def __init__(self, config: Dict, execution_mode: str):
        self.config = config
        self.execution_mode = execution_mode
        self.log_dir = Path(config.get('log_dir', 'logs'))
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize structured logger
        self.structured_logger = self._setup_structured_logger()
    
    async def log_event(self, event_type: str, event_data: Dict[str, Any], timestamp: pd.Timestamp = None):
        """Log event asynchronously."""
        try:
            if timestamp is None:
                timestamp = pd.Timestamp.now()
            
            log_entry = {
                'timestamp': timestamp.isoformat(),
                'event_type': event_type,
                'execution_mode': self.execution_mode,
                'data': event_data
            }
            
            # Log to structured logger
            self.structured_logger.info(
                f"Event: {event_type}",
                extra=log_entry
            )
            
            # Log to file
            await self._write_to_file(log_entry)
            
        except Exception as e:
            # Don't raise exception to avoid breaking the main flow
            logger.error(f"EVENT-001: Failed to log event {event_type}: {e}")
    
    async def _write_to_file(self, log_entry: Dict[str, Any]):
        """Write log entry to file asynchronously."""
        try:
            log_file = self.log_dir / f"events_{pd.Timestamp.now().strftime('%Y-%m-%d')}.jsonl"
            
            async with aiofiles.open(log_file, 'a') as f:
                await f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"EVENT-002: Failed to write to log file: {e}")
```

## VALIDATION REQUIREMENTS

### 1. Math Utilities Validation
- [ ] Centralized math functions implemented and tested
- [ ] Liquidity index calculations implemented and tested
- [ ] Market price conversions implemented and tested
- [ ] Currency conversions implemented and tested
- [ ] Error codes implemented and tested

### 2. Health & Error Systems Validation
- [ ] Error code registry completed and tested
- [ ] Health monitoring completed and tested
- [ ] Error handling completed and tested
- [ ] Health endpoints completed and tested
- [ ] Error codes implemented and tested

### 3. Results Store Validation
- [ ] Async implementation validated and tested
- [ ] Queue-based storage validated and tested
- [ ] FIFO ordering validated and tested
- [ ] Error handling validated and tested
- [ ] Error codes implemented and tested

### 4. Configuration Validation
- [ ] Config loading validated and tested
- [ ] Config validation validated and tested
- [ ] Environment variables validated and tested
- [ ] Config slicing validated and tested
- [ ] Error codes implemented and tested

### 5. Event Logger Validation
- [ ] Async I/O validated and tested
- [ ] Event logging validated and tested
- [ ] Structured logging validated and tested
- [ ] Log retention validated and tested
- [ ] Error codes implemented and tested

## QUALITY GATES

### 1. Infrastructure Components Quality Gate
```bash
# scripts/test_infrastructure_components_quality_gates.py
def test_infrastructure_components():
    # Test math utilities
    # Test health & error systems
    # Test results store
    # Test configuration
    # Test event logger
    # Validate async I/O patterns
    # Validate error handling
```

### 2. Integration Quality Gate
```bash
# Test integration between all infrastructure components
# Test async I/O integration
# Test error handling integration
# Test health monitoring integration
# Validate performance
```

## SUCCESS CRITERIA

### 1. Math Utilities ✅
- [ ] Centralized math functions implemented and tested
- [ ] Liquidity index calculations implemented and tested
- [ ] Market price conversions implemented and tested
- [ ] Currency conversions implemented and tested
- [ ] Error codes implemented and tested

### 2. Health & Error Systems ✅
- [ ] Error code registry completed and tested
- [ ] Health monitoring completed and tested
- [ ] Error handling completed and tested
- [ ] Health endpoints completed and tested
- [ ] Error codes implemented and tested

### 3. Results Store ✅
- [ ] Async implementation validated and tested
- [ ] Queue-based storage validated and tested
- [ ] FIFO ordering validated and tested
- [ ] Error handling validated and tested
- [ ] Error codes implemented and tested

### 4. Configuration ✅
- [ ] Config loading validated and tested
- [ ] Config validation validated and tested
- [ ] Environment variables validated and tested
- [ ] Config slicing validated and tested
- [ ] Error codes implemented and tested

### 5. Event Logger ✅
- [ ] Async I/O validated and tested
- [ ] Event logging validated and tested
- [ ] Structured logging validated and tested
- [ ] Log retention validated and tested
- [ ] Error codes implemented and tested

### 6. Integration Testing ✅
- [ ] All infrastructure components integrate correctly
- [ ] Async I/O patterns work correctly
- [ ] Error handling works across components
- [ ] Health monitoring works correctly
- [ ] Performance meets requirements

## QUALITY GATE SCRIPT

The quality gate script `scripts/test_infrastructure_components_quality_gates.py` will:

1. **Test Math Utilities**
   - Verify centralized math functions
   - Verify liquidity index calculations
   - Verify market price conversions
   - Verify currency conversions
   - Verify error codes

2. **Test Health & Error Systems**
   - Verify error code registry
   - Verify health monitoring
   - Verify error handling
   - Verify health endpoints
   - Verify error codes

3. **Test Results Store**
   - Verify async implementation
   - Verify queue-based storage
   - Verify FIFO ordering
   - Verify error handling
   - Verify error codes

4. **Test Configuration**
   - Verify config loading
   - Verify config validation
   - Verify environment variables
   - Verify config slicing
   - Verify error codes

5. **Test Event Logger**
   - Verify async I/O
   - Verify event logging
   - Verify structured logging
   - Verify log retention
   - Verify error codes

6. **Test Integration**
   - Verify all components integrate correctly
   - Verify async I/O patterns
   - Verify error handling across components
   - Verify health monitoring
   - Verify performance

**Expected Results**: All infrastructure components completed, async I/O patterns validated, comprehensive error handling, health monitoring functional, all quality gates passing.
