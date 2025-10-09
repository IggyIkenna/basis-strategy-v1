# API Documentation - Complete Reference 🚀

**Purpose**: Comprehensive API documentation covering all endpoints, request/response structures, and integration patterns  
**Status**: ✅ Complete API reference with new unified health system  
**Updated**: January 2025  
**Last Reviewed**: January 2025  
**Status**: ✅ Aligned with canonical sources and health system cleanup plan

---

## 📚 **Canonical Sources**

**This API documentation aligns with canonical architectural principles**:
- **Health System**: `.cursor/plans/health-system-cleanup-1eda130c.plan.md` - New unified health system (2 endpoints only)
- **Architectural Principles**: [CANONICAL_ARCHITECTURAL_PRINCIPLES.md](CANONICAL_ARCHITECTURAL_PRINCIPLES.md) - Consolidated from all .cursor/tasks/
- **Strategy Specifications**: [MODES.md](MODES.md) - Canonical strategy mode definitions
- **Venue Architecture**: [VENUE_ARCHITECTURE.md](VENUE_ARCHITECTURE.md) - Venue client initialization and execution

## 📚 **Key References**

- **Component Details** → [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md)
- **Workflow Guide** → [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)
- **Configuration** → [specs/CONFIGURATION.md](specs/CONFIGURATION.md)
- **Environment Variables** → [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md)
- **Deployment Guide** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## 🎯 **API Overview**

The Basis Strategy API provides a comprehensive interface for:
- **Backtest Execution**: Historical strategy testing with full component chain
- **Live Trading**: Real-time strategy execution with venue integration
- **Health Monitoring**: System health and component status monitoring
- **Capital Management**: Deposit and withdrawal operations
- **Position Management**: Position updates and monitoring

### **API Architecture**

```mermaid
graph TD
    A[FastAPI Server] --> B[Health Endpoints]
    A --> C[Backtest Endpoints]
    A --> D[Live Trading Endpoints]
    A --> E[Capital Management Endpoints]
    A --> F[Position Management Endpoints]
    
    B --> G[Unified Health Manager]
    C --> H[EventDrivenStrategyEngine]
    D --> H
    E --> I[Position Monitor]
    F --> I
    
    style A fill:#e3f2fd
    style G fill:#f1f8e9
    style H fill:#e8f5e8
    style I fill:#fff3e0
```

### **Base URL Structure**

```
Development: http://localhost:8001/api/v1
Staging: https://staging-api.basis-strategy.com/api/v1
Production: https://api.basis-strategy.com/api/v1
```

---

## 🏥 **Health Endpoints**

### **1. Basic Health Check**

**Endpoint**: `GET /health`

**Purpose**: Fast heartbeat check (< 50ms) for load balancers and monitoring systems

**Response Time**: < 50ms

**Authentication**: None required

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-06T12:00:00Z",
  "service": "basis-strategy-v1",
  "execution_mode": "backtest",
  "uptime_seconds": 3600,
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "memory_available_gb": 8.5
  }
}
```

**Status Values**:
- `"healthy"`: All systems operational
- `"degraded"`: Some non-critical issues
- `"unhealthy"`: Critical system failures

### **2. Detailed Health Check**

**Endpoint**: `GET /health/detailed`

**Purpose**: Comprehensive health check including all components and system metrics

**Response Time**: < 500ms

**Authentication**: None required

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-06T12:00:00Z",
  "service": "basis-strategy-v1",
  "execution_mode": "backtest",
  "uptime_seconds": 3600,
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "memory_available_gb": 8.5,
    "disk_percent": 23.1,
    "process": {
      "memory_mb": 256.5,
      "threads": 8,
      "connections": 3
    }
  },
  "components": {
    "position_monitor": {
      "status": "healthy",
      "timestamp": "2025-01-06T12:00:00Z",
      "error_code": null,
      "error_message": null,
      "readiness_checks": {
        "initialized": true,
        "redis_connected": true,
        "snapshot_available": true
      },
      "metrics": {
        "wallet_tokens": 12,
        "cex_accounts": 3
      }
    },
    "data_provider": {
      "status": "healthy",
      "timestamp": "2025-01-06T12:00:00Z",
      "error_code": null,
      "error_message": null,
      "readiness_checks": {
        "initialized": true,
        "data_loaded": true,
        "market_data_available": true
      },
      "metrics": {
        "data_sources": 8,
        "execution_mode": "backtest"
      }
    }
  },
  "summary": {
    "total_components": 9,
    "healthy_components": 9,
    "unhealthy_components": 0,
    "not_ready_components": 0,
    "unknown_components": 0
  }
}
```

**Component Status Values**:
- `"healthy"`: Component fully operational
- `"not_ready"`: Component initialized but not ready
- `"unhealthy"`: Component has critical failures
- `"unknown"`: Cannot determine status
- `"not_configured"`: Component intentionally not set up

**Mode-Aware Filtering**:
- **Backtest Mode**: Only includes components relevant to backtest execution (core components only)
- **Live Mode**: Includes all components including live trading health checks

---

## 🧪 **Backtest Endpoints**

### **1. Start Backtest**

**Endpoint**: `POST /backtest/start`

**Purpose**: Start a new backtest with specified strategy and parameters

**Request**:
```json
{
  "strategy_name": "usdt_market_neutral",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z",
  "initial_capital": 100000.0,
  "share_class": "USDT"
}
```

**Request Validation**:
- `strategy_name`: Must be valid strategy mode from `configs/modes/`
- `start_date`: Must be valid ISO 8601 datetime
- `end_date`: Must be after start_date
- `initial_capital`: Must be positive number
- `share_class`: Must be "USDT" or "ETH"

**Response**:
```json
{
  "backtest_id": "bt_20240115_103000_abc123",
  "status": "started",
  "strategy_name": "usdt_market_neutral",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z",
  "initial_capital": 100000.0,
  "share_class": "USDT",
  "estimated_duration_minutes": 15,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### **2. Get Backtest Status**

**Endpoint**: `GET /backtest/{backtest_id}/status`

**Purpose**: Get current status of a running backtest

**Response**:
```json
{
  "backtest_id": "bt_20240115_103000_abc123",
  "status": "running",
  "progress_percent": 65.5,
  "current_timestamp": "2024-01-15T15:30:00Z",
  "events_processed": 1250,
  "estimated_completion": "2024-01-15T10:45:00Z",
  "current_equity": 102500.0,
  "current_pnl": 2500.0
}
```

**Status Values**:
- `"queued"`: Backtest queued for execution
- `"running"`: Backtest currently executing
- `"completed"`: Backtest finished successfully
- `"failed"`: Backtest failed with error
- `"cancelled"`: Backtest was cancelled

### **3. Stop Backtest**

**Endpoint**: `POST /backtest/{backtest_id}/stop`

**Purpose**: Stop a running backtest

**Response**:
```json
{
  "backtest_id": "bt_20240115_103000_abc123",
  "status": "stopped",
  "stopped_at": "2024-01-15T10:35:00Z",
  "progress_percent": 45.2,
  "events_processed": 850
}
```

### **4. Get Backtest Results**

**Endpoint**: `GET /backtest/{backtest_id}/results`

**Purpose**: Get complete results of a finished backtest

**Response**:
```json
{
  "backtest_id": "bt_20240115_103000_abc123",
  "status": "completed",
  "strategy_name": "usdt_market_neutral",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z",
  "initial_capital": 100000.0,
  "final_capital": 105250.0,
  "total_return": 0.0525,
  "annualized_return": 0.68,
  "max_drawdown": 0.023,
  "sharpe_ratio": 1.85,
  "total_events": 2500,
  "execution_time_seconds": 900,
  "results_files": {
    "csv_report": "/results/bt_20240115_103000_abc123/results.csv",
    "html_plots": "/results/bt_20240115_103000_abc123/plots.html"
  },
  "performance_attribution": {
    "supply_yield": 0.008,
    "staking_yield_oracle": 0.0015,
    "staking_yield_rewards": 0.0005,
    "borrow_costs": -0.002,
    "funding_pnl": 0.018,
    "delta_pnl": 0.001,
    "transaction_costs": -0.0002
  },
  "risk_metrics": {
    "max_ltv_used": 0.89,
    "liquidation_events": 0,
    "rebalancing_events": 45
  }
}
```

### **Performance Attribution Breakdown**

The `performance_attribution` field breaks down the total return into specific sources of profit/loss, matching the comprehensive P&L Calculator specification:

**Component Details**:

1. **`supply_yield`** (0.008 = 0.8%):
   - Interest earned from **supplying assets to AAVE** (aUSDT, aETH, etc.)
   - Example: Supply USDT to AAVE and earn 5% APY
   - Primary return source for pure lending mode

2. **`staking_yield_oracle`** (0.0015 = 0.15%):
   - **LST price appreciation** (weETH/ETH grows ~2.8% APR)
   - Example: weETH appreciates relative to ETH due to staking rewards
   - Continuous, non-rebasing token appreciation

3. **`staking_yield_rewards`** (0.0005 = 0.05%):
   - **Seasonal rewards** (EIGEN weekly, ETHFI airdrops)
   - Example: Receive EIGEN tokens weekly, ETHFI airdrops
   - Discrete, event-based rewards

4. **`borrow_costs`** (-0.002 = -0.2%):
   - **Cost of borrowing** from AAVE (debt interest)
   - Example: Borrow ETH from AAVE at 3% APY
   - Always negative (cost), reduces total return

5. **`funding_pnl`** (0.018 = 1.8%):
   - Profit/loss from **funding rate payments** on perpetual positions
   - Example: Short ETH perp pays 0.01% funding every 8 hours
   - Positive when you receive funding, negative when you pay

6. **`delta_pnl`** (0.001 = 0.1%):
   - Profit/loss from **unhedged exposure** × price changes
   - Example: Small ETH exposure due to imperfect hedging
   - Can be positive or negative depending on market moves

7. **`transaction_costs`** (-0.0002 = -0.02%):
   - **Gas fees + execution costs** (slippage, trading fees)
   - Example: Gas for AAVE transactions, CEX trading fees
   - Always negative (cost), reduces total return

**Total Attribution**: 0.008 + 0.0015 + 0.0005 - 0.002 + 0.018 + 0.001 - 0.0002 = 0.0268 (2.68%)

---

## 🚀 **Live Trading Endpoints**

### **1. Start Live Trading**

**Endpoint**: `POST /live/start`

**Purpose**: Start live trading with specified strategy

**Request**:
```json
{
  "strategy_name": "usdt_market_neutral",
  "share_class": "USDT",
  "max_trade_size_usd": 10000.0,
  "emergency_stop_loss_pct": 0.15
}
```

**Request Validation**:
- `strategy_name`: Must be valid strategy mode
- `share_class`: Must be "USDT" or "ETH"
- `max_trade_size_usd`: Must be positive number
- `emergency_stop_loss_pct`: Must be between 0.01 and 0.50

**Response**:
```json
{
  "live_trading_id": "lt_20240115_103000_def456",
  "status": "started",
  "strategy_name": "usdt_market_neutral",
  "share_class": "USDT",
  "max_trade_size_usd": 10000.0,
  "emergency_stop_loss_pct": 0.15,
  "venue_health": {
    "binance": "healthy",
    "bybit": "healthy",
    "okx": "healthy",
    "aave_v3": "healthy"
  },
  "started_at": "2024-01-15T10:30:00Z"
}
```

### **2. Get Live Trading Status**

**Endpoint**: `GET /live/{live_trading_id}/status`

**Purpose**: Get current status of live trading

**Response**:
```json
{
  "live_trading_id": "lt_20240115_103000_def456",
  "status": "running",
  "strategy_name": "usdt_market_neutral",
  "current_equity": 102500.0,
  "current_pnl": 2500.0,
  "total_trades": 15,
  "last_trade_at": "2024-01-15T10:25:00Z",
  "venue_status": {
    "binance": "healthy",
    "bybit": "healthy",
    "okx": "healthy",
    "aave_v3": "healthy"
  },
  "risk_metrics": {
    "current_ltv": 0.85,
    "liquidation_risk": "low",
    "margin_ratio": 1.18
  }
}
```

### **3. Stop Live Trading**

**Endpoint**: `POST /live/{live_trading_id}/stop`

**Purpose**: Stop live trading and close all positions

**Response**:
```json
{
  "live_trading_id": "lt_20240115_103000_def456",
  "status": "stopped",
  "stopped_at": "2024-01-15T10:35:00Z",
  "final_equity": 102500.0,
  "total_pnl": 2500.0,
  "positions_closed": 3,
  "closing_time_seconds": 45
}
```

---

## 💰 **Capital Management Endpoints**

### **1. Deposit Capital**

**Endpoint**: `POST /capital/deposit`

**Purpose**: Add capital to the strategy

**Request**:
```json
{
  "amount": 50000.0,
  "currency": "USDT",
  "share_class": "USDT",
  "source": "external_wallet"
}
```

**Response**:
```json
{
  "deposit_id": "dep_20240115_103000_ghi789",
  "amount": 50000.0,
  "currency": "USDT",
  "share_class": "USDT",
  "status": "completed",
  "new_total_equity": 150000.0,
  "deposited_at": "2024-01-15T10:30:00Z"
}
```

### **2. Withdraw Capital**

**Endpoint**: `POST /capital/withdraw`

**Purpose**: Withdraw capital from the strategy

**Request**:
```json
{
  "amount": 25000.0,
  "currency": "USDT",
  "share_class": "USDT",
  "withdrawal_type": "fast"
}
```

**Response**:
```json
{
  "withdrawal_id": "wth_20240115_103000_jkl012",
  "amount": 25000.0,
  "currency": "USDT",
  "share_class": "USDT",
  "status": "completed",
  "withdrawal_type": "fast",
  "new_total_equity": 125000.0,
  "withdrawn_at": "2024-01-15T10:30:00Z"
}
```

**Withdrawal Types**:
- `"fast"`: Withdraw from available reserves (immediate)
- `"slow"`: Unwind positions to free up capital (may take time)

---

## 📊 **Position Management Endpoints**

### **1. Get Current Positions**

**Endpoint**: `GET /positions/current`

**Purpose**: Get current position snapshot across all venues

**Response**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "total_equity": 125000.0,
  "share_class": "USDT",
  "positions": {
    "wallet": {
      "ETH": 10.5,
      "USDT": 5000.0,
      "weETH": 5.2
    },
    "cex": {
      "binance": {
        "spot": {
          "ETH": 2.5,
          "USDT": 10000.0
        },
        "futures": {
          "ETHUSDT": -5.0
        }
      }
    },
    "defi": {
      "aave_v3": {
        "aUSDT": 50000.0,
        "debt_ETH": -8.0
      }
    }
  },
  "exposure": {
    "net_delta_eth": 0.05,
    "net_delta_usdt": 125000.0,
    "lending_exposure": 50000.0,
    "staking_exposure": 15.7
  }
}
```

### **2. Update Position**

**Endpoint**: `POST /positions/update`

**Purpose**: Manually update position (for external changes)

**Request**:
```json
{
  "venue": "binance",
  "asset": "ETH",
  "amount": 2.5,
  "position_type": "spot",
  "reason": "external_transfer"
}
```

**Response**:
```json
{
  "position_id": "pos_20240115_103000_mno345",
  "venue": "binance",
  "asset": "ETH",
  "amount": 2.5,
  "position_type": "spot",
  "status": "updated",
  "updated_at": "2024-01-15T10:30:00Z",
  "new_total_equity": 125000.0
}
```

---

## 🔧 **Error Handling**

### **Error Response Format**

All API endpoints return errors in a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid strategy name provided",
    "details": {
      "field": "strategy_name",
      "value": "invalid_strategy",
      "allowed_values": ["usdt_market_neutral", "btc_basis", "eth_leveraged"]
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_20240115_103000_pqr678"
  }
}
```

### **Common Error Codes**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `STRATEGY_NOT_FOUND` | 404 | Strategy mode not found |
| `BACKTEST_NOT_FOUND` | 404 | Backtest ID not found |
| `LIVE_TRADING_NOT_FOUND` | 404 | Live trading ID not found |
| `INSUFFICIENT_CAPITAL` | 400 | Not enough capital for operation |
| `VENUE_UNAVAILABLE` | 503 | Venue API unavailable |
| `SYSTEM_ERROR` | 500 | Internal system error |
| `RATE_LIMIT_EXCEEDED` | 429 | API rate limit exceeded |

---

## 🔐 **Authentication & Security**

### **API Key Authentication**

For production endpoints, include API key in header:

```bash
curl -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     https://api.basis-strategy.com/api/v1/backtest/start
```

### **Rate Limiting**

- **Health Endpoints**: 100 requests/minute
- **Backtest Endpoints**: 10 requests/minute
- **Live Trading Endpoints**: 5 requests/minute
- **Capital/Position Endpoints**: 20 requests/minute

### **CORS Configuration**

```json
{
  "allowed_origins": [
    "https://app.basis-strategy.com",
    "https://staging-app.basis-strategy.com"
  ],
  "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
  "allowed_headers": ["Content-Type", "X-API-Key"]
}
```

---

## 📈 **Integration Examples**

### **1. Start Backtest with Error Handling**

```python
import requests
import json

def start_backtest(strategy_name, start_date, end_date, initial_capital):
    url = "https://api.basis-strategy.com/api/v1/backtest/start"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "your-api-key"
    }
    data = {
        "strategy_name": strategy_name,
        "start_date": start_date,
        "end_date": end_date,
        "initial_capital": initial_capital,
        "share_class": "USDT"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_data = response.json()
        print(f"Error: {error_data['error']['message']}")
        return None
```

### **2. Monitor Backtest Progress**

```python
def monitor_backtest(backtest_id):
    url = f"https://api.basis-strategy.com/api/v1/backtest/{backtest_id}/status"
    headers = {"X-API-Key": "your-api-key"}
    
    while True:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        print(f"Progress: {data['progress_percent']:.1f}%")
        print(f"Current P&L: ${data['current_pnl']:.2f}")
        
        if data['status'] in ['completed', 'failed', 'cancelled']:
            break
            
        time.sleep(30)  # Check every 30 seconds
```

### **3. Health Check Integration**

```python
def check_system_health():
    # Fast health check
    url = "https://api.basis-strategy.com/health"
    response = requests.get(url)
    data = response.json()
    
    if data['status'] == 'healthy':
        print("✅ System healthy")
        return True
    else:
        print(f"❌ System unhealthy: {data['status']}")
        return False

def check_detailed_health():
    # Comprehensive health check
    url = "https://api.basis-strategy.com/health/detailed"
    response = requests.get(url)
    data = response.json()
    
    print(f"Overall Status: {data['status']}")
    print(f"Execution Mode: {data['execution_mode']}")
    print(f"Components: {data['summary']['healthy_components']}/{data['summary']['total_components']} healthy")
    
    return data['status'] == 'healthy'
```

---

## 🎯 **API Versioning**

### **Current Version**: v1

**Version Header**:
```bash
curl -H "API-Version: v1" \
     https://api.basis-strategy.com/api/v1/health/
```

### **Backward Compatibility**

- **v1**: Current stable version
- **Future versions**: Will maintain backward compatibility for at least 6 months
- **Deprecation**: 3-month notice before removing deprecated endpoints

---

## 📋 **API Testing**

### **Health Check Test**

```bash
# Basic health check
curl https://api.basis-strategy.com/health

# Detailed health check
curl https://api.basis-strategy.com/health/detailed
```

### **Backtest Test**

```bash
# Start backtest
curl -X POST https://api.basis-strategy.com/api/v1/backtest/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "strategy_name": "usdt_market_neutral",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "initial_capital": 100000.0,
    "share_class": "USDT"
  }'
```

---

## 🎯 **Summary**

**Key Points**:
1. **Unified Health System**: Only 2 health endpoints (basic + detailed)
2. **Mode-Aware**: Health checks filter components based on execution mode
3. **Comprehensive Coverage**: All system operations covered by API
4. **Error Handling**: Consistent error format across all endpoints
5. **Security**: API key authentication and rate limiting

**API Endpoints**:
- **Health**: 2 endpoints (basic + detailed)
- **Backtest**: 4 endpoints (start, status, stop, results)
- **Live Trading**: 3 endpoints (start, status, stop)
- **Capital Management**: 2 endpoints (deposit, withdraw)
- **Position Management**: 2 endpoints (current, update)

**Total**: 13 endpoints covering all system functionality

---

**Remember**: All API endpoints are documented with complete request/response examples! 🚀

*Last Updated: January 2025*
