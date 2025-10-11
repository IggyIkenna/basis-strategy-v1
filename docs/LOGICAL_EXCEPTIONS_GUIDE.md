# Logical Exceptions Guide

**Last Updated**: October 11, 2025

## Purpose

This guide documents all logical exceptions to architectural principles, specifically fail-fast patterns and async/await usage. These exceptions are validated by quality gates to ensure proper implementation.

## 📚 **Canonical Sources**

**This guide aligns with canonical architectural principles**:
- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](REFERENCE_ARCHITECTURE_CANONICAL.md) - Core principles including ADR-006 and ADR-040
- **Quality Gates**: [QUALITY_GATES.md](QUALITY_GATES.md) - Implementation validation standards
- **Component Specifications**: [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) - All component specs

## Fail-Fast Exceptions (ADR-040)

### Allowed: I/O Operations

These operations use `.get()` with defaults because they handle external data sources where missing fields are expected:

```python
# File loading: Optional columns in CSV files
df = pd.read_csv(file_path)
optional_column = df.get('optional_field', None)

# API responses: Optional fields in external APIs
response = requests.get(api_url)
data = response.json().get('data', {})

# Database queries: Optional fields in database results
result = db.query("SELECT * FROM table")
field_value = result.get('optional_field', None)

# Configuration parsing: Optional config sections
config_section = config.get('optional_section', {})
```

### Allowed: Mode-Agnostic Components

These components return 0/empty for missing data to support mode-agnostic design:

```python
# Exposure tracking: Returns 0 for missing venues
exposure = exposures.get(f'{venue}_USDT', {}).get('exposure_usd', 0)

# Attribution types: Returns 0 for unused attribution types
funding_pnl = attributions.get('funding_pnl', 0)
lending_pnl = attributions.get('lending_pnl', 0)

# Risk types: Returns None if risk type not applicable to mode
health_factor = risks.get('aave_health_factor', None)
liquidation_risk = risks.get('liquidation_risk', None)

# Balance tracking: Returns 0 for missing balances
balance = balances.get('USDT', 0)
```

### Allowed: Documented Config Defaults

These use `.get()` with documented defaults from component specifications:

```python
# Execution timeout: Documented default 30 seconds
timeout = config.get('execution_timeout', 30)

# Retry attempts: Documented default 3 attempts
retries = config.get('retry_attempts', 3)

# Batch size: Documented default 100
batch_size = config.get('batch_size', 100)

# Log level: Documented default 'INFO'
log_level = config.get('log_level', 'INFO')
```

### Violations: Business Logic

These should use direct access `config['field']` to fail fast on missing required data:

```python
# Required config fields: Must fail fast
mode = config['mode']  # Not config.get('mode', 'default')
data_requirements = config['data_requirements']  # Not config.get('data_requirements', [])

# Critical calculations: Must fail fast on missing inputs
required_price = data['market_data']['prices']['USDT']  # Not .get() with default

# Mode selection: Never default mode silently
strategy_mode = config['strategy_mode']  # Not config.get('strategy_mode', 'default')
```

## Async/Await Exceptions (ADR-006)

### Allowed: I/O Operations

These operations are async because they involve external I/O that can be slow:

```python
# EventLogger: All methods are async per ADR-006
async def log_event(self, event_type: str, data: Dict[str, Any], timestamp: pd.Timestamp):
    """Log event with global ordering"""
    async with self._order_lock:
        await self._write_event_to_storage(event)

# ResultsStore: Queue-based async operations
async def store_result(self, result_type: str, data: Dict[str, Any], timestamp: pd.Timestamp):
    """Store result with async I/O"""
    await self.results_queue.put((result_type, data, timestamp))

# File I/O: Data loading and persistence
async def load_data(self, file_path: Path) -> pd.DataFrame:
    """Load data asynchronously"""
    return await asyncio.to_thread(pd.read_csv, file_path)

# Database queries: Async database operations
async def query_database(self, query: str) -> Dict[str, Any]:
    """Execute database query asynchronously"""
    return await self.db.execute(query)

# API calls: External API requests
async def fetch_price_data(self, symbol: str) -> Dict[str, Any]:
    """Fetch price data from external API"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f'/api/price/{symbol}') as response:
            return await response.json()
```

### Required: API Call Queueing

All concurrent API calls must be queued to prevent race conditions:

```python
class APICallQueue:
    """Queue for sequential API call processing"""
    
    def __init__(self):
        self.queue = asyncio.Queue()
        self.worker_task = None
    
    async def enqueue_call(self, api_func, *args, **kwargs):
        """Enqueue API call for sequential processing"""
        await self.queue.put((api_func, args, kwargs))
        return await self._get_result()
    
    async def _worker(self):
        """Worker processes API calls sequentially"""
        while True:
            api_func, args, kwargs = await self.queue.get()
            try:
                result = await api_func(*args, **kwargs)
                # Process result sequentially
            except Exception as e:
                # Handle error
            finally:
                self.queue.task_done()
```

### Violations: Component Methods

These should be synchronous per ADR-006:

```python
# Component update methods: Must be synchronous
def update_state(self, timestamp: pd.Timestamp, trigger_source: str):
    """Update component state synchronously"""
    # Process state update
    position = self.position_monitor.get_current_position()
    
    # Exception: EventLogger async I/O
    await self.event_logger.log_event('state_update', data, timestamp)

# Internal calculations: Must be synchronous
def calculate_pnl(self, data: Dict[str, Any]) -> float:
    """Calculate PnL synchronously"""
    return self._compute_pnl(data)

# Inter-component calls: Must be synchronous
def get_exposure(self, venue: str) -> float:
    """Get exposure from exposure monitor synchronously"""
    return self.exposure_monitor.get_venue_exposure(venue)

# Reconciliation loops: Must be synchronous
def reconcile_positions(self) -> Dict[str, Any]:
    """Reconcile positions synchronously"""
    return self._perform_reconciliation()
```

## Quality Gate Validation

### Logical Exception Validator

The `test_logical_exceptions_quality_gates.py` script validates:

1. **Fail-Fast Exceptions**: Checks `.get()` usage against documented exceptions
2. **Async/Await Exceptions**: Validates async patterns against ADR-006 exceptions
3. **API Call Queueing**: Ensures concurrent API calls are properly queued

### Mode-Agnostic Design Validator

The `test_mode_agnostic_design_quality_gates.py` script validates:

1. **Component Data Requirements**: Ensures components handle missing data gracefully
2. **Graceful Degradation**: Validates 0/empty return patterns for missing data
3. **Downstream Dependencies**: Checks components don't fail on mode-specific data

## Implementation Examples

### Good: Mode-Agnostic Component

```python
class ExposureMonitor:
    """Mode-agnostic exposure monitoring"""
    
    def get_venue_exposure(self, venue: str) -> float:
        """Get exposure for venue, returns 0 if not tracked"""
        # Mode-agnostic: Returns 0 for venues not in current mode
        return self.exposures.get(f'{venue}_USDT', {}).get('exposure_usd', 0)
    
    def get_asset_exposure(self, asset: str) -> float:
        """Get exposure for asset, returns 0 if not tracked"""
        # Mode-agnostic: Returns 0 for assets not in current mode
        return self.exposures.get(asset, 0)
```

### Good: Async I/O with Queueing

```python
class DataProvider:
    """Data provider with async I/O and queueing"""
    
    def __init__(self):
        self.api_queue = APICallQueue()
    
    async def get_spot_price(self, symbol: str) -> float:
        """Get spot price with queued API call"""
        return await self.api_queue.enqueue_call(
            self._fetch_price_from_api, symbol
        )
    
    async def _fetch_price_from_api(self, symbol: str) -> float:
        """Fetch price from external API"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f'/api/price/{symbol}') as response:
                data = await response.json()
                return data['price']
```

### Bad: Violation Examples

```python
# BAD: Silent failure masking config error
mode = config.get('mode', 'default')  # Should fail fast if mode missing

# BAD: Async component internal method
async def update_state(self, timestamp: pd.Timestamp):
    """Should be synchronous"""
    # Component internal logic should be sync

# BAD: Hard failure on mode-specific data
funding_rate = data['market_data']['rates']['funding_rate']  # KeyError in non-hedged modes

# BAD: Concurrent API calls without queueing
async def fetch_multiple_prices(self, symbols: List[str]):
    """Should queue calls sequentially"""
    tasks = [self._fetch_price(symbol) for symbol in symbols]
    return await asyncio.gather(*tasks)  # Race condition risk
```

## Related Documentation

### Architecture Patterns
- [Reference-Based Architecture](REFERENCE_ARCHITECTURE_CANONICAL.md) - Core architectural principles
- [Mode-Agnostic Architecture](REFERENCE_ARCHITECTURE_CANONICAL.md) - Config-driven architecture guide
- [Request Isolation Pattern](REQUEST_ISOLATION_PATTERN.md) - Component isolation patterns

### Component Specifications
- [Event Logger Specification](specs/08_EVENT_LOGGER.md) - Async I/O exception patterns
- [Results Store Specification](specs/18_RESULTS_STORE.md) - Queue-based async operations
- [Data Provider Specification](specs/09_DATA_PROVIDER.md) - Mode-agnostic data handling

### Quality Gates
- [Quality Gates](QUALITY_GATES.md) - Implementation validation standards
- [Logical Exception Quality Gate](../scripts/test_logical_exceptions_quality_gates.py) - Validation script
- [Mode-Agnostic Design Quality Gate](../scripts/test_mode_agnostic_design_quality_gates.py) - Validation script

---

**Status**: Complete with comprehensive exception patterns documented! ✅  
**Last Reviewed**: October 11, 2025
