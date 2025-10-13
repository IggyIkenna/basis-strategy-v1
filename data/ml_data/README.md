# ML Data Directory Structure

This directory contains ML-related data files for the basis-strategy-v1 platform.

## Directory Structure

```
data/
├── market_data/
│   └── ml/
│       ├── btc_5min_ohlcv.csv      # BTC 5-minute OHLCV bars
│       └── usdt_5min_ohlcv.csv     # USDT 5-minute OHLCV bars
└── ml_data/
    └── predictions/
        ├── btc_predictions.csv      # BTC ML predictions
        └── usdt_predictions.csv     # USDT ML predictions
```

## Data File Formats

### OHLCV Data (`data/market_data/ml/`)

**File naming convention:** `{symbol}_5min_ohlcv.csv`

**Example:** `btc_5min_ohlcv.csv`

**CSV format:**
```csv
timestamp,open,high,low,close,volume
2025-01-01 00:00:00,50000.0,50100.0,49900.0,50050.0,100.5
2025-01-01 00:05:00,50050.0,50200.0,50000.0,50150.0,120.3
```

**Required columns:**
- `timestamp`: ISO format timestamp (YYYY-MM-DD HH:MM:SS)
- `open`: Opening price
- `high`: High price
- `low`: Low price
- `close`: Closing price
- `volume`: Trading volume

### ML Predictions (`data/ml_data/predictions/`)

**File naming convention:** `{symbol}_predictions.csv`

**Example:** `btc_predictions.csv`

**CSV format:**
```csv
timestamp,signal,confidence,sd
2025-01-01 00:00:00,long,0.85,0.025
2025-01-01 00:05:00,short,0.72,0.018
2025-01-01 00:10:00,neutral,0.45,0.015
```

**Required columns:**
- `timestamp`: ISO format timestamp (YYYY-MM-DD HH:MM:SS)
- `signal`: Trading signal (`long`, `short`, `neutral`, `hold`)
- `confidence`: Signal confidence (0.0 to 1.0)
- `sd`: Standard deviation for stop-loss/take-profit calculation (as decimal, e.g., 0.025 for 2.5%)

**Stop-Loss/Take-Profit Calculation:**
The strategy calculates stop-loss and take-profit levels dynamically using the standard deviation:
- **Long positions**: Stop-loss = price × (1 - 2×sd), Take-profit = price × (1 + 3×sd)
- **Short positions**: Stop-loss = price × (1 + 2×sd), Take-profit = price × (1 - 3×sd)
- **Neutral signals**: No stop-loss or take-profit levels

## ML Strategy Requirements

### Data Requirements

ML strategies require the following data types in their configuration:

```yaml
data_requirements:
  - "ml_ohlcv_5min"       # OHLCV 5-min bars
  - "ml_predictions"      # ML signals (long/short/neutral + TP/SL)
  - "btc_usd_prices"      # For PnL calculation (BTC mode)
  - "eth_usd_prices"      # For PnL calculation (ETH mode)
  - "usdt_usd_prices"     # For PnL calculation (USDT mode)
  - "gas_costs"
  - "execution_costs"
```

### Environment Variables

For live mode, set the following environment variable:

```bash
export BASIS_ML_API_TOKEN="your_ml_api_token_here"
```

### Supported Strategy Modes

- `ml_btc_directional`: BTC directional ML strategy
- `ml_usdt_directional`: USDT directional ML strategy

## Data Generation

### Backtest Mode

For backtesting, ML data files must be prepared in advance:

1. **OHLCV Data**: Generate 5-minute OHLCV bars for the backtest period
2. **Predictions**: Generate ML predictions for the same timestamps

### Live Mode

For live trading, ML predictions are fetched from an external API:

- **API Endpoint**: Configured in `configs/venues/ml_inference_api.yaml`
- **Authentication**: Bearer token via `BASIS_ML_API_TOKEN`
- **Fallback**: Returns neutral signal if API unavailable

## Data Validation

The system validates ML data on startup:

1. **File Existence**: Checks if required ML data files exist
2. **Format Validation**: Validates CSV format and required columns
3. **Timestamp Alignment**: Ensures predictions align with OHLCV timestamps
4. **API Connectivity**: Tests ML API connection (live mode)

## Error Handling

### Missing Data Files

If ML data files are missing:
- **Backtest Mode**: Raises `FileNotFoundError` with helpful message
- **Live Mode**: Falls back to neutral signals

### API Failures

If ML API is unavailable:
- **Live Mode**: Returns neutral signal with warning log
- **Graceful Degradation**: System continues running with reduced functionality

## TODO Items

- [ ] Prepare sample ML data files for testing
- [ ] Set up ML API credentials for staging environment
- [ ] Implement ML data validation tests
- [ ] Add ML data generation scripts
- [ ] Document ML model training pipeline

## Related Documentation

- [ML Strategy Integration Plan](../ml-strategy-integration.plan.md)
- [Strategy Modes Documentation](../../docs/MODES.md)
- [Data Provider Specification](../../docs/specs/09_DATA_PROVIDER.md)
