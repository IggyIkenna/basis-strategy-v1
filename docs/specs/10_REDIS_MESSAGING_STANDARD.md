# Standard: Redis Messaging 📡

**Purpose**: Define Redis pub/sub patterns for inter-component communication  
**Priority**: ⭐⭐ MEDIUM (Optional for backtest, required for live)  
**Applies To**: Event Logger only (other components use direct method calls)

---

## 🎯 **Purpose**

Standardize Redis usage for backtest-to-live compatibility.

**Key Principles**:
- **Synchronous in backtest**: Direct method calls for simplicity and performance
- **Redis in live**: Real-time event publishing via pub/sub (Event Logger only)
- **Fallback support**: Event Logger works with or without Redis
- **Pub/Sub for events**: Event Logger publishes events to Redis (live only)
- **Keys for state**: Latest event data cached for queries (live only)
- **TTL policies**: Hourly data expires after 1 hour (live only)

**Implementation Note**: Redis is currently only implemented in the Event Logger component. Other components communicate via direct method calls, not Redis pub/sub as originally planned.

---

## 📊 **Channel Naming Convention**

### **Pattern**: `{component}:{event_type}`

**Examples**:
- `position:updated` - Position Monitor published update
- `exposure:calculated` - Exposure Monitor calculated exposure
- `risk:calculated` - Risk Monitor calculated risks
- `pnl:calculated` - P&L Calculator calculated P&L
- `strategy:instructions` - Strategy Manager issued instructions
- `events:logged` - Event Logger logged event

---

## 🔑 **Key Naming Convention**

### **Pattern**: `{component}:{data_type}`

**Examples**:
- `position:snapshot` - Latest position snapshot
- `exposure:current` - Latest exposure data
- `risk:current` - Latest risk metrics
- `pnl:current` - Latest P&L data
- `strategy:rebalancing` - Current rebalancing plan

---

## 🔄 **Synchronous vs Asynchronous Patterns**

### **Backtest Mode** (Synchronous)
```python
# Direct method calls for simplicity and performance
position = position_monitor.get_snapshot()
exposure = exposure_monitor.calculate_exposure(position, timestamp)
risk = risk_monitor.assess_risk(exposure, timestamp)
pnl = pnl_calculator.calculate_pnl(exposure, risk, timestamp)
```

### **Live Mode** (Asynchronous with Redis)
```python
# Redis pub/sub for real-time communication
await redis.publish('position:updated', position_data)
await redis.subscribe('exposure:calculated', exposure_callback)
```

### **Component Interface**
```python
class Component:
    def __init__(self, redis_enabled: bool = False):
        self.redis_enabled = redis_enabled
        self.redis = redis.Redis() if redis_enabled else None
    
    def calculate(self, data):
        """Synchronous calculation - works in both modes"""
        result = self._do_calculation(data)
        
        if self.redis_enabled:
            # Publish result for live mode
            await self.redis.publish(f'{self.name}:calculated', result)
        
        return result
```

---

## 📋 **Data Formats**

### **Channel Messages** (Lightweight notifications)

```json
{
  "timestamp": "2024-05-12T14:00:00Z",
  "component": "position_monitor",
  "event": "updated",
  "metadata": {
    "trigger": "GAS_FEE_PAID",
    "changes_count": 1
  }
}
```

### **Key Values** (Full data, JSON)

```json
{
  "timestamp": "2024-05-12T14:00:00Z",
  "wallet": {...},
  "cex_accounts": {...},
  "perp_positions": {...}
}
```

---

## ⏱️ **TTL Policies**

```python
TTL_CONFIG = {
    # Hourly data (expires after 1 hour)
    'position:snapshot': 3600,      # 1 hour
    'exposure:current': 3600,
    'risk:current': 3600,
    'pnl:current': 3600,
    
    # Historical data (longer retention)
    'events:history': 86400,        # 24 hours
    'pnl:hourly_series': 86400,
    
    # Persistent (no expiry)
    'config:strategy': None,
    'config:initial_state': None
}
```

---

## 🔄 **Component Pub/Sub Patterns**

### **Position Monitor**

```python
# Publishes
await redis.publish('position:updated', {
    'timestamp': timestamp,
    'trigger': 'GAS_FEE_PAID'
})
await redis.set('position:snapshot', json.dumps(snapshot), ex=3600)

# Subscribes
# (None - Position Monitor is first in chain)
```

### **Exposure Monitor**

```python
# Subscribes
redis.subscribe('position:updated', callback=self._on_position_update)

# Publishes
await redis.publish('exposure:calculated', {
    'timestamp': timestamp,
    'net_delta_eth': -5.12
})
await redis.set('exposure:current', json.dumps(exposure_data), ex=3600)
```

### **Risk Monitor**

```python
# Subscribes
redis.subscribe('exposure:calculated', callback=self._on_exposure_update)

# Publishes
await redis.publish('risk:calculated', {
    'timestamp': timestamp,
    'overall_status': 'WARNING',
    'alerts': ['BINANCE_MARGIN_WARNING']
})
await redis.set('risk:current', json.dumps(risk_data), ex=3600)
```

### **P&L Calculator**

```python
# Subscribes
redis.subscribe('risk:calculated', callback=self._on_risk_update)

# Publishes
await redis.publish('pnl:calculated', {
    'timestamp': timestamp,
    'pnl_cumulative': 1238.45
})
await redis.set('pnl:current', json.dumps(pnl_data), ex=3600)
```

### **Strategy Manager**

```python
# Subscribes
redis.subscribe('risk:calculated', callback=self._on_risk_update)

# Publishes
await redis.publish('strategy:instructions', {
    'timestamp': timestamp,
    'instruction_count': 2,
    'priority': 'CRITICAL'
})
await redis.set('strategy:rebalancing', json.dumps(instructions), ex=3600)
```

---

## ⚠️ **Error Handling**

### **Redis Unavailable**

```python
try:
    await redis.publish('position:updated', message)
except redis.ConnectionError:
    logger.warning("Redis unavailable, continuing without pub/sub")
    # Backtest: OK (can run in-memory)
    # Live: ALERT (need Redis for real-time monitoring!)
    
    if execution_mode == 'live':
        raise RuntimeError("Redis required for live trading!")
```

### **Message Deserialization**

```python
try:
    data = json.loads(message)
except json.JSONDecodeError:
    logger.error(f"Invalid JSON in Redis message: {message}")
    # Skip this message, continue
```

---

## 🧪 **Testing**

```python
def test_redis_pub_sub():
    """Test Redis pub/sub works."""
    redis_client = redis.Redis()
    
    # Subscribe
    pubsub = redis_client.pubsub()
    pubsub.subscribe('position:updated')
    
    # Publish
    redis_client.publish('position:updated', json.dumps({'test': True}))
    
    # Receive
    message = pubsub.get_message(timeout=1)
    assert message is not None
    assert json.loads(message['data'])['test'] == True

def test_ttl_expiry():
    """Test TTL policies work."""
    redis_client = redis.Redis()
    
    # Set with TTL
    redis_client.set('test:data', 'value', ex=1)  # 1 second
    
    # Immediately available
    assert redis_client.get('test:data') == b'value'
    
    # Wait for expiry
    time.sleep(2)
    
    # Should be gone
    assert redis_client.get('test:data') is None
```

---

## 🔄 **Backtest vs Live**

### **Backtest**:
```python
# Redis is OPTIONAL
if redis_available:
    await redis.publish(...)
    # Helps with debugging (can monitor Redis during backtest)
else:
    # In-memory direct calls
    await exposure_monitor.calculate_exposure(position_data)
```

### **Live**:
```python
# Redis is REQUIRED
if not redis_available:
    raise RuntimeError("Redis required for live trading!")

# Real-time monitoring depends on Redis pub/sub
# Multiple processes can monitor same strategy
```

---

## 🎯 **Success Criteria**

- [ ] All components use consistent channel names
- [ ] All components use consistent key names
- [ ] TTL policies prevent memory bloat
- [ ] Graceful degradation if Redis unavailable (backtest)
- [ ] Fail-fast if Redis unavailable (live)
- [ ] JSON serialization/deserialization works
- [ ] Pub/sub triggers downstream components
- [ ] Keys allow latest state queries

---

**Status**: Standard complete! ✅


