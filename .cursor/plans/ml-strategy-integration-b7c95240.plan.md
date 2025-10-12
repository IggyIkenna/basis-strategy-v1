<!-- b7c95240-7404-4225-9383-a80bf2456b4c 0e88a7c1-d444-4eb4-9993-c90ae880e54c -->
# ML Strategy Integration Refactor Plan

## Overview

Integrate ML-driven trading strategies into basis-strategy-v1 with two new modes: `ml_btc_directional` and `ml_usdt_directional`. These strategies trade BTC/USDT perp futures on 5-min intervals using ML predictions, supporting long/short positions with take-profit and stop-loss orders.

## Key Design Decisions

### 1. Minimal Changes Philosophy

- **Leverage existing config-driven architecture** - no new architectural patterns
- **Reuse mode-agnostic components** - Position/Exposure/Risk/PnL monitors work as-is
- **Add ML-specific strategy managers** - inherit from BaseStrategyManager
- **Extend DataProvider** - add ML data types to existing data abstraction
- **Keep execution simple** - CEX perp orders through existing execution interfaces
- **Backward compatible** - ML data optional, existing tests unaffected

### 2. Data Architecture (Simplified)

- **Backtest**: OHLCV 5-min + predictions stored in `data/`
    - `data/market_data/ml/ohlcv_5min_{symbol}.csv` - OHLCV bars
    - `data/ml_data/predictions/{symbol}_predictions.csv` - ML signals (long/short/neutral + TP/SL)
    - **No feature storage** - features handled externally by ML service
- **Live**: External API provides predictions only
    - ML service handles feature engineering internally
    - Fallback to graceful degradation if API unavailable
- **Optional ML Data**: DataProvider checks for ML data availability
    - If missing, existing strategies work unchanged
    - ML strategies fail gracefully with helpful error message

### 3. Strategy Execution Flow

- **Entry**: At start of 5-min candle based on ML signal (long/short)
- **Exit**: Stop-loss (priority 1) → Take-profit (priority 2) → End of candle (priority 3)
- **Position sizing**: Full position (100% equity) per signal
- **Hold logic**: If new signal matches current position, hold (no action)

## Implementation Steps

### Step 1: Extend Data Provider for ML Data Types

**Files to modify:**

- `backend/src/basis_strategy_v1/core/data_provider/base_data_provider.py`
- `backend/src/basis_strategy_v1/core/data_provider/data_provider.py`
- `backend/src/basis_strategy_v1/core/data_provider/data_provider_factory.py`

**Changes:**

1. Add ML data types to BaseDataProvider (optional methods):
```python
def get_ml_ohlcv(self, timestamp: pd.Timestamp, symbol: str) -> Optional[Dict]:
    """
    Get 5-min OHLCV bar for timestamp and symbol.
    Returns None if ML data not configured (backward compatible).
    """
    if not self._ml_data_enabled():
        return None
    return self._load_ml_ohlcv(timestamp, symbol)
    
def get_ml_prediction(self, timestamp: pd.Timestamp, symbol: str) -> Optional[Dict]:
    """
    Get ML prediction: {'signal': 'long'|'short'|'neutral', 'confidence': float, 
                        'take_profit': float, 'stop_loss': float}
    Returns None if ML data not configured (backward compatible).
    """
    if not self._ml_data_enabled():
        return None
    return self._load_ml_prediction(timestamp, symbol)

def _ml_data_enabled(self) -> bool:
    """Check if ML data is configured for this strategy mode."""
    return 'ml_ohlcv_5min' in self.config.get('data_requirements', [])
```

2. Implement CSV loading for backtest mode:
```python
def _load_ml_ohlcv(self, timestamp: pd.Timestamp, symbol: str) -> Dict:
    """Load OHLCV from CSV file."""
    # Check if file exists
    file_path = f"{self.data_dir}/market_data/ml/ohlcv_5min_{symbol.lower()}.csv"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ML OHLCV data not found: {file_path}")
    
    # Load and return data for timestamp
    # ... implementation
```

3. Implement API client for live mode:
```python
def _fetch_ml_prediction_from_api(self, timestamp: pd.Timestamp, symbol: str) -> Dict:
    """Fetch ML prediction from external API with caching and fallback."""
    # Check cache first
    cache_key = f"ml_pred_{symbol}_{timestamp}"
    if cache_key in self._ml_cache:
        return self._ml_cache[cache_key]
    
    # Call external API
    try:
        response = requests.post(
            self.ml_api_config['endpoints']['predictions'],
            headers={'Authorization': f"Bearer {os.getenv('BASIS_ML_API_TOKEN')}"},
            json={'symbol': symbol, 'timestamp': timestamp.isoformat()},
            timeout=30
        )
        result = response.json()
        self._ml_cache[cache_key] = result
        return result
    except Exception as e:
        logger.error(f"ML API call failed: {e}")
        # Graceful degradation - return neutral signal
        return {'signal': 'neutral', 'confidence': 0.0}
```

4. Add configuration check on initialization:
```python
def __init__(self, config: Dict, execution_mode: str):
    super().__init__(config, execution_mode)
    
    # Check ML data requirements
    if 'ml_ohlcv_5min' in config.get('data_requirements', []):
        self._validate_ml_data_availability()
        
def _validate_ml_data_availability(self):
    """Validate ML data is available (backtest) or API is configured (live)."""
    if self.execution_mode == 'backtest':
        # Check if ML data files exist
        for symbol in self._get_ml_symbols():
            file_path = f"{self.data_dir}/market_data/ml/ohlcv_5min_{symbol}.csv"
            if not os.path.exists(file_path):
                logger.warning(f"ML data not found: {file_path}")
    elif self.execution_mode == 'live':
        # Check if ML API is configured
        if not os.getenv('BASIS_ML_API_TOKEN'):
            raise ValueError("BASIS_ML_API_TOKEN not set for ML strategy in live mode")
```


**Backward Compatibility:**

- ML methods return `None` if ML data not configured
- Existing strategies never call ML methods
- Tests pass without ML data files

**Reference files:**

- `docs/specs/09_DATA_PROVIDER.md` - Data provider patterns
- Existing data loading: `backend/src/basis_strategy_v1/core/data_provider/data_provider.py:200-400`

---

### Step 2: Create ML Strategy Mode Configurations

**Files to create:**

- `configs/modes/ml_btc_directional.yaml`
- `configs/modes/ml_usdt_directional.yaml`

**Configuration structure:**

```yaml
mode: "ml_btc_directional"
share_class: "BTC"
asset: "BTC"
market_neutral: false  # Directional strategy
lending_enabled: false
staking_enabled: false
basis_trade_enabled: false
borrowing_enabled: false
leverage_enabled: true  # Perp futures
initial_capital: 10000.0

# ML-specific parameters
ml_config:
  model_registry: "mlflow"
  model_name: "btc_5min_strategy"
  model_version: "production"
  candle_interval: "5min"
  signal_threshold: 0.65  # Min confidence to trade
  max_position_size: 1.0  # 100% of equity

# Execution venues (perp only)
venues:
  binance:
    venue_type: "cex"
    enabled: true
    instruments: ["BTC-PERP"]
    order_types: ["market", "limit", "stop_loss", "take_profit"]

# Data requirements (NO FEATURES - handled externally)
data_requirements:
  - "ml_ohlcv_5min"       # OHLCV 5-min bars
  - "ml_predictions"      # ML signals (long/short/neutral + TP/SL)
  - "btc_usd_prices"      # For PnL calculation
  - "gas_costs"
  - "execution_costs"

# Component configs (mode-agnostic)
component_config:
  position_monitor:
    track_assets: ["BTC", "USDT", "BTC_PERP"]
    initial_balances:
      wallet: {}
      cex_accounts: ["binance"]
      perp_positions: ["binance"]
    fail_on_unknown_asset: true
    
  exposure_monitor:
    exposure_currency: "BTC"
    track_assets: ["BTC", "USDT", "BTC_PERP"]
    conversion_methods:
      BTC: "direct"
      USDT: "usd_price"
      BTC_PERP: "perp_mark_price"
      
  risk_monitor:
    enabled_risk_types: ["cex_margin_ratio", "delta_risk"]
    risk_limits:
      target_margin_ratio: 0.5
      cex_margin_ratio_min: 0.15
      maintenance_margin_requirement: 0.10
      delta_tolerance: 1.0  # 100% delta allowed (directional)
      
  pnl_calculator:
    attribution_types: ["funding_pnl", "price_change_pnl", "transaction_costs"]
    reporting_currency: "BTC"
    reconciliation_tolerance: 0.02
    
  strategy_manager:
    strategy_type: "ml_directional"
    rebalancing_interval: "5min"
    position_deviation_threshold: 0.05
    actions: ["entry_long", "entry_short", "exit_position", "update_stops"]
    
  execution_manager:
    supported_actions: ["open_perp_long", "open_perp_short", "close_perp", "update_stop_loss", "update_take_profit"]
    action_mapping:
      open_perp_long: ["binance_perp"]
      open_perp_short: ["binance_perp"]
      close_perp: ["binance_perp"]
```

**Note:** No feature data requirements - features handled externally by ML service.

**Reference files:**

- `configs/modes/btc_basis.yaml` - Similar CEX perp structure
- `configs/modes/eth_leveraged.yaml` - Directional strategy patterns
- `docs/specs/19_CONFIGURATION.md` - Config schemas

---

### Step 3: Implement ML Strategy Managers

**Files to create:**

- `backend/src/basis_strategy_v1/core/strategy/ml_directional_strategy_manager.py`

**Implementation:** (Same as before, no feature-related code)

---

### Step 4: Update Strategy Factory

**Files to modify:**

- `backend/src/basis_strategy_v1/core/strategy/strategy_factory.py`

**Changes:**

1. Add ML strategy manager imports
2. Add mode mapping (same as before)

---

### Step 5: Extend Execution Manager for ML Actions

(Same as before - no changes needed)

---

### Step 6: Update Event-Driven Strategy Engine

(Same as before - support 5-min intervals)

---

### Step 7: Add ML Data Files Structure (Simplified)

**Directories to create:**

```
data/
├── market_data/
│   └── ml/
│       ├── btc_5min_ohlcv.csv
│       └── usdt_5min_ohlcv.csv
└── ml_data/
    └── predictions/
        ├── btc_predictions.csv
        └── usdt_predictions.csv
```

**CSV schemas:**

1. OHLCV 5-min (`btc_5min_ohlcv.csv`):
```csv
timestamp,open,high,low,close,volume
2025-01-01 00:00:00,50000,50100,49900,50050,100.5
```

2. Predictions (`btc_predictions.csv`):
```csv
timestamp,signal,confidence,stop_loss,take_profit
2025-01-01 00:00:00,long,0.85,49500,51000
```


**Note:** No feature files - simplified data structure.

---

### Step 8: Add ML Inference API Configuration

**Files to create:**

- `configs/venues/ml_inference_api.yaml`

**Configuration (predictions only):**

```yaml
venue_name: "ml_inference_api"
venue_type: "api"
enabled: true

# API endpoints (predictions only - features handled internally)
endpoints:
  predictions: "https://ml-inference-api.example.com/v1/predictions"

# Authentication (environment-specific)
auth:
  type: "bearer_token"
  token_env_var: "BASIS_ML_API_TOKEN"

# Request configuration
request_config:
  timeout_seconds: 30
  retry_attempts: 3
  retry_backoff_seconds: 5
  cache_ttl_seconds: 300  # 5-min cache

# Response validation
validation:
  require_confidence_score: true
  min_confidence: 0.0
  valid_signals: ["long", "short", "neutral"]
```

---

### Step 9: Update Documentation

(Same as before, clarify that features are NOT queried by this system)

---

### Step 10: Add Unit Tests (Backward Compatible)

**Files to create:**

- `tests/unit/test_ml_directional_strategy_manager.py`
- `tests/unit/test_ml_data_provider.py`

**Test coverage:**

1. ML Strategy Manager tests (isolated with mocked data)
2. ML Data Provider tests (optional - skip if ML data missing)

**Backward Compatibility Pattern:**

```python
import pytest
import os

@pytest.mark.skipif(
    not os.path.exists('data/ml_data/predictions/btc_predictions.csv'),
    reason="ML data not available - optional test"
)
def test_ml_strategy_backtest():
    """Test ML strategy - skipped if ML data not present."""
    # ... test implementation
```

**Existing Tests:**

- All existing strategy tests continue to pass
- No ML data required for non-ML strategies
- ML tests skip gracefully if data missing

---

### Step 11: Integration Testing (Optional)

**Files to create:**

- `tests/integration/test_ml_strategy_backtest.py`

**Test scenarios (all marked as optional):**

```python
@pytest.mark.ml_strategy  # Custom marker for ML tests
@pytest.mark.skipif(...)
def test_ml_strategy_end_to_end():
    """Full e2e test - only runs if ML data present."""
    pass
```

---

## Backward Compatibility Guarantees

### 1. Existing Tests Unaffected

- **No ML data required**: Existing tests run unchanged
- **Optional ML data**: ML-related tests skip if data missing
- **No breaking changes**: All existing functionality preserved

### 2. DataProvider Changes

- **Optional ML methods**: Return `None` if ML not configured
- **Graceful degradation**: Missing ML data doesn't break non-ML strategies
- **Configuration-driven**: ML data loaded only if `data_requirements` includes ML types

### 3. Test Execution

```bash
# Run all tests (ML tests skip if data missing)
pytest tests/

# Run only non-ML tests (existing tests)
pytest tests/ -m "not ml_strategy"

# Run ML tests only (requires ML data)
pytest tests/ -m "ml_strategy"
```

### 4. Data Validation on Startup

```python
# BacktestService initialization
def _validate_strategy_data_requirements(self, strategy_name: str):
    """Validate required data is available before backtest starts."""
    config = self._get_mode_config(strategy_name)
    data_reqs = config.get('data_requirements', [])
    
    if 'ml_predictions' in data_reqs:
        # Check ML data availability
        if not self._ml_data_available(config['asset']):
            raise ValueError(
                f"ML data not available for {strategy_name}. "
                f"Please prepare ML data files or use a different strategy."
            )
```

---

## Migration Path

### Phase 1: Core Infrastructure (Week 1)

- Step 1: Data Provider extensions (backward compatible)
- Step 2: Mode configurations (new files only)
- Step 3: ML Strategy Manager (new file only)
- Step 4: Strategy Factory update (additive change)

**Testing after Phase 1:**

- Run existing test suite → all pass (ML tests skip)
- Verify no regressions

### Phase 2: Execution & Integration (Week 2)

- Step 5: Execution Manager extensions (additive)
- Step 6: Event Engine updates (additive)
- Step 7: Data file structure (new directories)
- Step 8: API configuration (new file)

**Testing after Phase 2:**

- Run existing test suite → all pass
- ML tests still skip (no data yet)

### Phase 3: ML Data Preparation (Week 3)

- Prepare sample ML data files
- Configure ML API credentials (staging)
- Enable ML tests

**Testing after Phase 3:**

- Run full test suite including ML tests
- Validate ML strategy behavior

### Phase 4: Validation (Week 4)

- Backtest validation with real ML data
- Live mode staging test (small capital)
- Production deployment

---

## Key Benefits

1. **No Breaking Changes**: Existing strategies and tests unaffected
2. **Optional ML Data**: System works with or without ML files
3. **Minimal Code Changes**: Only additive changes to existing components
4. **Graceful Degradation**: Missing ML data handled cleanly
5. **Test Isolation**: ML tests skip if data unavailable
6. **Simplified Data**: No feature storage - handled externally
7. **Production-Ready**: Same patterns as existing strategies

---

## API Contract (Simplified)

### Live Mode - Prediction Request (Features handled internally by ML service)

```bash
curl -X POST https://ml-inference-api.example.com/v1/predictions \
  -H "Authorization: Bearer ${ML_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC-PERP",
    "timestamp": "2025-01-01T00:00:00Z"
  }'
```

**Response:**

```json
{
  "symbol": "BTC-PERP",
  "timestamp": "2025-01-01T00:00:00Z",
  "signal": "long",
  "confidence": 0.85,
  "stop_loss": 49500.0,
  "take_profit": 51000.0,
  "model_version": "v1.2.3"
}
```

**Note:** ML service handles feature engineering internally - this system only receives final predictions.

### To-dos

- [ ] Step 1: Extend Data Provider for ML data types (OHLCV, predictions)
- [ ] Step 2: Create ML strategy mode configurations (ml_btc_directional, ml_usdt_directional)
- [ ] Step 3: Implement ML Strategy Manager (ml_directional_strategy_manager.py)
- [ ] Step 4: Update Strategy Factory to support ML strategies
- [ ] Step 5: Extend Execution Manager for ML actions (perp orders with TP/SL)
- [ ] Step 6: Update Event-Driven Strategy Engine (5-min interval support)
- [ ] Step 7: Create ML data directory structure and README
- [ ] Step 8: Add ML Inference API configuration (ml_inference_api.yaml)
- [ ] Step 9: Update documentation (MODES.md, DATA_PROVIDER spec, etc.)
- [ ] Step 10: Add unit tests with skip decorators
- [ ] Step 11: Add integration tests with skip decorators