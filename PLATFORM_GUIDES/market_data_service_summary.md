# Market Data Service

## Overview
- Fetches historical OHLCV (Open, High, Low, Close, Volume) data from multiple cryptocurrency exchanges
- Supports Binance, Bybit, OKX for OHLCV data (via CCXT library)
- Supports Deribit for DVOL (Implied Volatility Index) data (via direct HTTP API)
- Focuses on BTC/USDT, ETH/USDT, SOL/USDT trading pairs
- Parallelizes data fetching by symbol and exchange for efficiency
- Supports both live trading and backtesting modes
- Manages a circular buffer of recent data points for live trading
- Persists data to storage for later use in backtesting

## Timeframes and Data Types
- Primary data collection at 1-minute intervals (changed from 5-minute)
- Data types:
  - OHLCV data: Standard price and volume candlestick data
  - DVOL data: Deribit Volatility Index data for volatility measurements
  - Storage format: Parquet files for efficient storage and quick access

## Service Components

### 1. Data Fetching
- **Exchange Connectors**:
  - CCXT-based connector for Binance, Bybit, OKX
  - Custom HTTP-based connector for Deribit (not supported by CCXT)
- **Rate Limiting**:
  - Built-in rate limiting system for each exchange
  - Configurable limits based on exchange API constraints
  - Automatic cooldown periods to prevent API throttling
- **Error Handling**:
  - Robust retry logic for network errors and API failures
  - Graceful degradation if an exchange is temporarily unavailable

### 2. Data Storage
- **Live Data Cache**:
  - Maintains rolling buffers for all timeframes
  - Buffer size: 100 candles per timeframe
  - Timeframes: 1m, 5m, 15m, 1h, 4h, 1d
  - In-memory storage for fast access
  - Serves as source of truth for recent data
  - Provides unified access for other services
- **Persistent Storage**:
  - Parquet file format for compressed, column-oriented storage
  - Organized by exchange/symbol/timeframe
  - Optimized for quick retrieval during backtesting
  - Supports both generation and retrieval modes
- **Data Integrity**:
  - Automatic deduplication of data points
  - Gap detection and handling
  - Data validation to ensure OHLCV constraints are maintained
  - Buffer consistency checks across timeframes

### 3. Operation Modes
- **Live Trading Mode**:
  - Maintains real-time buffers for all timeframes
  - Periodically persists data to storage
  - Configurable persistence frequency
  - Provides buffer access endpoints for other services
- **Backtest Mode**:
  - Loads historical data from persistent storage
  - Supports date range filtering for specific backtest periods
  - Ensures data consistency for reproducible backtest results
  - Offers both generation and retrieval modes

### 4. Service Integration
- **Buffer Access Endpoints**:
  - GET `/api/v1/market-data/{exchange}/{symbol}/buffer/{timeframe}`
  - Returns last 100 candles for specified timeframe
  - Used by Feature Engineering for initial data
  - Supports all standard timeframes
- **Historical Data Endpoints**:
  - GET `/api/v1/market-data/{exchange}/{symbol}/history`
  - Supports both generation and retrieval modes
  - Follows platform standard backfill patterns
  - Gap detection and regeneration capabilities
- **Pub/Sub Topics**:
  - Real-time updates for each timeframe
  - Buffer state change notifications
  - Data generation status events

### 5. Parallel Processing
- Parallelizes data fetching by symbol and exchange
- Configurable number of workers capped by the number of cores available and set given the number of exchanges and symbols
- Job queue management to prevent overwhelming exchange APIs
- Progress tracking and completion handling

## Implementation Details

### Data Flow
1. Request parameters defined (exchanges, symbols, date range)
2. Jobs distributed to worker processes (one per exchange/symbol combination)
3. Data fetched in batches with appropriate rate limiting
4. Data validated, processed, and stored in standardized format
5. Results aggregated and made available to other system components

### CCXT Integration
- Leverages CCXT library's unified API for exchange connectivity
- Standardizes data format across different exchanges
- Handles exchange-specific quirks and requirements

### Deribit DVOL Specifics
- Fetches hourly DVOL data for maximum historical coverage
- Resamples to 1-minute intervals using forward fill technique
- Handles pagination for large historical datasets

### Performance Optimizations
- Batched requests to minimize API calls
- Data caching to reduce redundant fetching
- Vectorized operations for data processing
- Efficient storage format selection

## Best Practices
- Respect exchange API rate limits
- Implement robust error handling and retry logic
- Maintain data integrity with validation checks
- Use efficient data storage formats
- Parallelize where appropriate but avoid overwhelming resources
- Log operations for monitoring and debugging

## Environment-Specific Configurations

### Local Development (local-dev)
- Single process data fetching
- Local DuckDB for data storage
- File-based configuration
- Mocked exchange APIs for testing
- Limited historical data

### Local Integration (local-integration)
- Docker containerized service
- Shared DuckDB instance
- Inter-service communication testing
- Mock/real exchange API toggle
- Recent historical data only

### Central Development (central-dev)
- First environment with real exchange APIs
- BigQuery for data storage
- Full service deployment
- Development API rate limits
- Extended historical data

### Integration Test
- Automated API integration tests
- Exchange API simulation
- Data consistency validation
- Performance benchmarking
- Test-specific datasets

### Staging
- Production-like setup
- Full historical data access
- Production API rate limits
- Complete exchange integration
- Performance validation

### Production
- Paper Trading
  - Production infrastructure
  - Paper trading API endpoints
  - Full historical data
  - Production monitoring

- Live Trading
  - Isolated production setup
  - Live exchange API access
  - Real-time data processing
  - Critical monitoring

## Work Distribution & Scaling

### Processing Dimensions
1. **By Symbol**
   - Independent data fetching per symbol
   - Symbol-specific rate limiting
   - Separate buffer management
   - Individual persistence streams

2. **By Exchange**
   - Parallel exchange connections
   - Exchange-specific error handling
   - Independent API quota management
   - Cross-exchange synchronization

3. **Implementation Example**
```python
class MarketDataOrchestrator:
    def __init__(self, config):
        self.symbols = ['BTC', 'ETH', 'SOL']
        self.exchanges = ['BINANCE', 'BYBIT', 'OKX']
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
        
    def distribute_data_collection(self):
        """Distribute data collection across symbols and exchanges."""
        collection_tasks = []
        for symbol in self.symbols:
            for exchange in self.exchanges:
                task = {
                    'symbol': symbol,
                    'exchange': exchange,
                    'timeframes': self.timeframes,
                    'config': self.get_config(symbol, exchange)
                }
                collection_tasks.append(task)
        
        # Execute collection in parallel
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.collect_data, task) 
                      for task in collection_tasks]
            results = [f.result() for f in futures]
        
        return self.aggregate_market_data(results)
```

### Resource Management
1. **Network Resources**
   - Per-exchange bandwidth allocation
   - API rate limit monitoring
   - Connection pool management
   - Request prioritization

2. **Storage Resources**
   - Symbol-specific partitioning
   - Exchange-based organization
   - Buffer size management
   - Cleanup policies

3. **Compute Resources**
   - Worker allocation strategy
   - Memory limits per symbol
   - CPU core distribution
   - Load balancing rules 