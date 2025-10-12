# Feature & Target Engineering Workflow

## Overview
This document outlines the comprehensive feature engineering process for our cryptocurrency prediction model. It covers the entire pipeline from data acquisition to feature generation, with a unified approach that treats all patterns as features. The system is designed to generate initially ~25,000 features across multiple timeframes, coins and feature groups while carefully preventing lookahead bias through standardized lagging.

Key Concepts:
- All patterns are treated as features, including what traditionally would be considered "targets"
- Features come in two types:
  1. Regular features: Looking back in time (e.g., RSI, MACD)
  2. Target features: Looking forward in time (e.g., future price movements, future swing events)
- Both types of features use the same standardized lagging system:
  - Regular features: Lagged to prevent lookahead bias
  - Target features: First computed as forward-looking features, then lagged for training
- This unified approach ensures:
  - Consistent feature generation between training and inference
  - No special handling needed for targets vs features
  - Same code works for both historical and live data
  - Natural handling of multiple prediction horizons

## Feature Engineering Pipeline

### Data Acquisition & Preparation
1. **Raw Data Sources**
   - Market Data Service buffer endpoints for recent data:
     - Last 100 candles for each timeframe (1m to 1d)
     - Initial data load on service startup
     - Real-time updates via pub/sub
   - Market Data Service historical endpoints for backfill:
     - Supports both generation and retrieval modes
     - Gap detection and regeneration
     - Follows platform standard patterns
   - Supported timeframes:
     - Base: 1-minute candles
     - Derived: 5m, 15m, 1h, 4h, 1d
     - All sourced from Market Data Service

2. **Data Access Patterns**
   - Service Startup:
     ```python
     def initialize_data_buffers(self):
         """Initialize data buffers from Market Data Service."""
         for timeframe in TIMEFRAMES:
             # Get last 100 candles for each timeframe
             buffer_data = market_data_client.get_buffer(
                 exchange=exchange,
                 symbol=symbol,
                 timeframe=timeframe
             )
             self.process_initial_data(buffer_data)
             
         # Subscribe to real-time updates
         self.subscribe_to_updates()
     ```
   
   - Historical Data Access:
     ```python
     def get_historical_data(self, start_time, end_time):
         """Get historical data from Market Data Service."""
         return market_data_client.get_history(
             exchange=exchange,
             symbol=symbol,
             start_time=start_time,
             end_time=end_time,
             mode=self.backfill_mode  # 'generate' or 'retrieve'
         )
     ```

3. **Data Processing Flow**
   - Initial buffer population from Market Data Service
   - Real-time updates via pub/sub subscription
   - No direct buffer management
   - Feature computation on received data
   - Backfill support through Market Data endpoints

4. **Cross-Exchange Aggregation**
   - Uses Market Data Service's pre-aggregated data
   - Consistent data across all services
   - Unified source of truth

### Feature Generation Architecture

1. **Feature Generator Hierarchy**
   Features are generated using a modular architecture with specialized generators, all inheriting standardized lagging from the base generator:

   ```
   Feature Generation Hierarchy
   ├── BaseFeatureGenerator (parent class with standardized lagging)
   │   ├── CandlestickFeatureGenerator
   │   ├── MarketStructureFeatureGenerator
   │   ├── TechnicalIndicatorOrchestrator
   │   │   ├── MovingAveragesGroup
   │   │   ├── OscillatorsGroup
   │   │   ├── VolatilityBandsGroup
   │   │   ├── TrendStrengthGroup
   │   │   ├── VWAPVolumeProfileGroup
   │   │   └── MomentumGroup
   │   ├── TemporalFeatureGenerator
   │   ├── VolatilityFeatureGenerator
   │   ├── CrossSectionalFeatureGenerator
   │   ├── EconomicEventFeatureGenerator
   │   ├── MarketMicrostructureFeatureGenerator
   │   ├── ComplexPatternRecognitionGroup
   │   ├── RoundNumbersGroup
   │   ├── ReturnMetricsGroup
   │   └── RegimeClassificationGroup
   ```

2. **Standardized Feature Lagging**
   All features implement a consistent lagging approach through the base generator:
   ```python
   class BaseFeatureGenerator:
       def __init__(self, config=None):
           # Standard lagging configuration
           self.feature_lag_multiples = [1, 2, 3, 4]  # Standard 4 lags for all features
           self.min_lag_bars = 1  # Minimum lag in bars
           
       def apply_feature_lags(self, features, window=1):
           """Apply standard lagging to features."""
           lagged_features = {}
           for feat_name, feat_array in features.items():
               for lag_multiple in self.feature_lag_multiples:
                   lag = window * lag_multiple
                   lagged_name = f"{feat_name}_lag_{lag}"
                   lagged_features[lagged_name] = np.roll(feat_array, lag)
                   lagged_features[lagged_name][:lag] = 0
           return lagged_features
   ```

3. **Parallelization Strategy**
   The feature generation is parallelized across multiple dimensions:

   a. **By Symbol**: BTC, ETH, SOL processed independently
   b. **By Time Bucket**: 
      - Data split into quarterly buckets with 100-period overlap between quarters
      - Prevents NaN values at the start of new quarters for technical features
   c. **By Timeframe**: Different timeframes processed in parallel
   d. **By Feature Group**: Different feature generators run in parallel
   e. **By Technical Subgroup**: Technical indicators split into subgroups to optimize memory usage

   ```
   Parallelization Dimensions:
     Symbols       × Time Buckets       × Timeframes     × Feature Groups         × Tech Subgroups
     ├── BTC       × ├── 2022-Q1       × ├── 1m         × ├── Candlestick        × ├── Moving Averages
     ├── ETH         ├── 2022-Q2         ├── 5m           ├── Market Structure      ├── Oscillators
     └── SOL         ├── ...             ├── 15m          ├── Technical Indicators  ├── Volatility Bands
                     └── 2023-Q4         ├── 1h           ├── Temporal              ├── Trend Strength
                                         ├── 4h           ├── Volatility            ├── VWAP & Volume Profile
                                         └── 24h          └── Market Microstructure  └── Momentum
   ```

4. **Service-Level Parallelization Control**
   - Feature generation controlled by a service-level orchestrator
   - Dynamic process allocation based on system resources
   - Configurable max parallel processes per dimension
   - Process monitoring and restart capability for long-running jobs
   - Resource throttling to prevent memory exhaustion

5. **Modular Architecture Implementation**
   ```python
   class FeaturePipeline:
       def __init__(self, config):
           self.generators = [
               CandlestickFeatureGenerator(config),
               TechnicalIndicatorOrchestrator(config),
               VWAPVolumeProfileFeatureGenerator(config),
               VolatilityFeatureGenerator(config),
               MarketStructureFeatureGenerator(config),
               TemporalFeatureGenerator(config),
               EconomicEventFeatureGenerator(config),
               ComplexPatternRecognitionGroup(config),
               RoundNumbersGroup(config),
               ReturnMetricsGroup(config),
               RegimeClassificationGroup(config)
           ]
       
       def generate_features(self, market_data, symbol):
           feature_dfs = []
           # Parallel processing
           for generator in self.generators:
               features = generator.generate_features(market_data, symbol)
               feature_dfs.append(features)
           
           # Combine features
           return pd.concat(feature_dfs, axis=1)
   ```

6. **Computational Resource Management**
   - Efficient memory usage with NumPy optimized arrays
   - Batch processing for large datasets
   - Caching and memoization of intermediate calculations
   - Dynamic scaling based on available system resources

### Feature Groups & Techniques

1. **Candlestick Patterns**
   - Japanese candlestick pattern recognition
   - Multi-timeframe pattern detection
   - Pattern strength and reliability metrics

2. **Market Structure Features**
   - Support and resistance levels
   - Swing high/low detection
   - Chart pattern recognition (H&S, triangles, etc.)
   - Fibonacci retracement levels
   - Market structure event detection with time-since tracking

3. **Swing Event Features**
   - Unified approach treating all patterns as features
   - Swing high/low detection using lagged data
   - Multiple lookback windows and standard deviation thresholds
   - Post-event pattern classification (breakout/reversion)
   - Time-since tracking for all events
   - Standard 4 lags for all features
   
   ```python
   class SwingEventFeatureGenerator(BaseFeatureGenerator):
       def __init__(self, config=None):
           super().__init__(config)
           # Configuration parameters
           self.lookback_windows = [10, 20, 30, 50]
           self.std_dev_thresholds = [1.0, 1.5, 2.0, 2.5]
           self.breakout_thresholds = [0.5, 1.0, 1.5]
           self.reversion_thresholds = [0.5, 1.0, 1.5]
           
       def generate_features(self, data):
           features = {}
           events = {}
           
           # Generate base features
           for window in self.lookback_windows:
               for std_dev in self.std_dev_thresholds:
                   # Detect swing events
                   swing_features = self.detect_swing_events(data, window, std_dev)
                   
                   # Apply standard lagging
                   lagged_features = self.apply_feature_lags(swing_features, window)
                   features.update(lagged_features)
           
           return features
   ```

4. **Technical Indicators**
   The technical indicators are divided into specialized subgroups:

   a. **Moving Averages Group**
      - Simple, Exponential, Weighted, and Hull MAs
      - Ichimoku Cloud components
      - Moving average crossovers and ribbons
      - MA-derived slopes and accelerations

   b. **Oscillators Group**
      - RSI with multiple periods and thresholds
      - MACD with multiple parameter sets
      - Stochastic Oscillator (Fast and Slow)
      - CCI, MFI, ROC, and Williams %R
      - Comprehensive oscillator event detection

   c. **Volatility Bands Group**
      - Bollinger Bands with multiple periods and deviations
      - Keltner Channels
      - Donchian Channels
      - ATR-based bands
      - Band crossover and squeeze events

   d. **Trend Strength Group**
      - ADX and Directional Movement Index
      - Aroon Indicator
      - Trend intensity and persistence measures
      - Trend classification (strength, direction, age)

   e. **VWAP & Volume Profile Group**
      - Standard VWAP for multiple timeframes
      - Anchored VWAP calculations (daily, weekly, monthly)
      - VWAP bands and deviation metrics
      - Volume Profile indicators (POC, Value Area)
      - VWAP crossover and deviation events
      - Time-since VWAP events (crosses, touches, deviations)

5. **Temporal Features**
   - Time of day, day of week, month cyclicality
   - Seasonality features
   - Historical event anniversaries
   - Cyclical time encoding

6. **Volatility Features**
   - Historical and implied volatility measures
   - Volatility regime detection
   - Volatility term structure
   - GARCH model predictions

7. **Market Microstructure**
   - Order book imbalance metrics
   - Supply/demand zones
   - Delta volume and cumulative delta
   - Trading activity metrics

8. **Cross-Sectional Features**
   - Crypto index relative performance
   - Altcoin correlation metrics
   - Sector rotation indicators
   - Cross-market influences

9. **Economic Events**
   - FOMC meeting proximity
   - CPI and NFP release timing
   - Market reaction to previous events
   - Cyclic and time-since event features

10. **Complex Pattern Recognition**
    - Advanced chart pattern detection (Head & Shoulders, triangles, etc.)
    - Pattern completion and target calculation
    - Time-since pattern events tracking
    - Pattern strength and reliability metrics

11. **Round Numbers Analysis**
    - Price interaction with psychological levels
    - Fibonacci retracement and extension levels
    - Level density and clustering analysis
    - Time-since level interactions

12. **Enhanced Return Metrics**
    - Multi-timeframe return analysis
    - Return distribution characteristics
    - Volatility-adjusted returns
    - Volume-weighted returns
    - Drawdown analysis
    - Non-linear transformations for tree models

13. **Market Regime Classification**
    - Trend regime detection and classification
    - Volatility regime analysis
    - Correlation regime identification
    - Liquidity regime assessment
    - Combined regime analysis
    - Regime stability and transition tracking

### Time-Since Event Features
For all feature groups, we implement time-since calculations with standardized lagging:

```python
def _calculate_time_since_events(self, events):
    """Calculate time since various events with standard lagging."""
    time_since_features = {}
    
    for event_name, event_array in events.items():
        # Calculate basic time-since
        time_since = np.zeros_like(event_array, dtype=float)
        counter = 0
        for i in range(len(event_array)):
            if event_array[i]:
                counter = 0
            else:
                counter += 1
            time_since[i] = counter
        
        # Apply standard lagging to time-since features
        lagged_features = self.apply_feature_lags(
            {f'time_since_{event_name}': time_since}
        )
        time_since_features.update(lagged_features)
    
    return time_since_features
```

### Lookahead Bias Prevention
We prevent lookahead bias through several mechanisms:

1. **Standardized Feature Lagging**
   ```python
   def prevent_lookahead(self, features, window=1):
       """Apply standard lagging to prevent lookahead bias."""
       return self.apply_feature_lags(features, window)
   ```

2. **Point-in-time Feature Generation**
   - All features are calculated using only data available at prediction time
   - Rolling windows always look backward, never forward
   - Standard 4 lags applied to all features

3. **Proper Handling of Resampled Data**
   - When resampling to higher timeframes, we ensure that only completed bars are used
   - Partial bar information is never used in feature calculation
   - Lagging is applied after resampling to maintain consistency

4. **Data Leakage Audits**
   - Automated tests to verify absence of future data leakage
   - Timestamp-based verification of feature calculation integrity
   - Validation of lag application across all feature groups

### Data Storage & Organization
1. **File Format & Structure**
   - Parquet files for efficient storage and retrieval
   - Partitioning by symbol, date range, and feature group
   - Compression to minimize storage requirements

2. **Naming Conventions**
   ```
   features_{symbol}_{start_date}_{end_date}_{feature_group}.parquet
   ```

3. **Version Control & Reproducibility**
   - Feature calculation parameters stored with data
   - Seed values for stochastic processes
   - Source data hash verification

## Target Generation Pipeline

### Forward-Looking Feature Types
1. **Directional Price Movement**
   - Classification features (up/neutral/down) based on future returns
   - Regression features (expected return)
   - Probability-calibrated features
   - Generated with multiple forward windows (1m, 5m, 15m, 1h, 4h, 24h)
   - Multiple threshold levels for classification

2. **Trend Reversal Points**
   - Future swing high/low identification
   - Future trend exhaustion signals
   - Future pattern completion events
   - Generated as forward-looking features then lagged

3. **Volatility Breakouts**
   - Future significant price movement predictions
   - Future range expansion events
   - Future volatility regime changes
   - Forward-looking volatility features

### Forward Feature Generation Process
1. **Forward Window Calculation**
   ```python
   def calculate_forward_features(self, price_data, windows=[1, 5, 15, 60, 240, 1440]):
       """Calculate forward-looking features that will be lagged for training."""
       forward_features = {}
       
       for window in windows:
           # Calculate future returns
           future_returns = price_data.shift(-window) / price_data - 1
           
           # Calculate future volatility
           future_volatility = price_data.rolling(window).std().shift(-window)
           
           # Detect future swing points
           future_swing_highs = detect_swing_points(price_data, window, 'high').shift(-window)
           future_swing_lows = detect_swing_points(price_data, window, 'low').shift(-window)
           
           # Store with window identifier
           forward_features.update({
               f'future_return_{window}': future_returns,
               f'future_volatility_{window}': future_volatility,
               f'future_swing_high_{window}': future_swing_highs,
               f'future_swing_low_{window}': future_swing_lows
           })
       
       # Apply standard lagging to make features usable for training
       return self.apply_feature_lags(forward_features)
   ```

2. **Feature Distribution Management**
   - Balance classification features
   - Normalize regression features
   - Handle rare events consistently
   - Maintain distribution statistics for monitoring

3. **Integration with Regular Features**
   ```python
   def generate_all_features(self, price_data):
       """Generate both regular and forward-looking features with consistent lagging."""
       # Generate regular backward-looking features
       regular_features = self.generate_regular_features(price_data)
       
       # Generate forward-looking features
       forward_features = self.calculate_forward_features(price_data)
       
       # Both feature sets are already properly lagged by their respective functions
       return pd.concat([regular_features, forward_features], axis=1)
   ```

### Training Data Preparation
1. **Feature-Target Alignment**
   - Temporal alignment of features and targets
   - Handling of different timeframes
   - Ensuring causal relationships

2. **Dataset Splitting**
   - Time-based train/validation/test splits
   - Cross-validation strategies for time series
   - Out-of-sample testing approaches

3. **Feature Selection & Importance**
   - Importance-based feature ranking
   - Correlation analysis and redundancy reduction
   - Domain-specific feature grouping

4. **Final Dataset Format**
   ```python
   def create_training_dataset(self, features, targets, start_date, end_date):
       """Create a training-ready dataset by combining features and targets."""
       # Align dates
       aligned_features = features.loc[start_date:end_date]
       aligned_targets = targets.loc[start_date:end_date]
       
       # Merge and handle any missing values
       dataset = pd.concat([aligned_features, aligned_targets], axis=1)
       dataset = handle_missing_values(dataset)
       
       # Final preprocessing
       dataset = normalize_features(dataset)
       
       return dataset
   ```

## Best Practices & Challenges

### Performance Optimization
1. **TA-Lib Integration**
   - Hardware-optimized indicator calculations
   - Vectorized operations for speed
   - Proper NumPy array handling

2. **Feature Calculation Efficiency**
   - Preventing redundant calculations
   - Algorithmic optimizations for complex features
   - Progressive resolution for multi-timeframe features

### Common Pitfalls
1. **Data Leakage Issues**
   - Forward-looking bias in indicators
   - Test set contamination
   - Cross-dataset leakage

2. **Computational Bottlenecks**
   - Memory-efficient processing of large datasets
   - Distributed computation strategies
   - Progressive feature generation

### Monitoring & Maintenance
1. **Feature Stability**
   - Detecting distribution shifts
   - Monitoring feature importance over time
   - Automated feature quality assessment

2. **Pipeline Extensibility**
   - Adding new feature groups
   - Integrating novel data sources
   - Updating feature calculation methodologies 

## ML Pipeline Integration

### Feature Selection for Prediction
1. **Swing Event Feature Selection**
   - Select appropriate swing event features as prediction targets
   - Use remaining features as input features
   - No need for separate target generation pipeline
   - Same code works for both training and live inference

2. **Training Data Preparation**
   ```python
   def prepare_training_data(self, features_df, target_config):
       """Prepare training data using swing event features as targets."""
       # Select target features based on configuration
       target_cols = [
           col for col in features_df.columns
           if any(pattern in col for pattern in [
               'high_breakout', 'high_reversion',
               'low_breakout', 'low_reversion'
           ])
       ]
       
       # Filter by specific window and threshold if specified
       if target_config.get('window'):
           target_cols = [
               col for col in target_cols
               if f"_{target_config['window']}_" in col
           ]
       
       # Remove target columns from feature set
       feature_cols = [
           col for col in features_df.columns
           if col not in target_cols
       ]
       
       return features_df[feature_cols], features_df[target_cols]
   ```

3. **Model Training Configuration**
   ```python
   target_config = {
       'window': 20,  # Lookback window for swing detection
       'std_dev': 2.0,  # Standard deviation threshold
       'target_type': 'high_breakout'  # Which pattern to predict
   }
   
   # Prepare data
   X, y = prepare_training_data(features_df, target_config)
   
   # Train model
   model = LightGBM(params)
   model.fit(X, y)
   ```

4. **Live Inference**
   - Use same feature generation code for both training and inference
   - Select appropriate target feature for prediction
   - No need to modify feature generation logic
   - Consistent behavior between training and live trading 

## Environment-Specific Configurations

### Local Development (local-dev)
- Single process feature computation
- Local DuckDB for feature storage
- Limited feature set for quick iteration
- In-memory computation
- Small data samples for development

### Local Integration (local-integration)
- Docker containerized service
- Shared DuckDB for features
- Basic parallelization testing
- Integration with market data service
- Subset of feature groups

### Central Development (central-dev)
- Full distributed computation
- BigQuery for feature storage
- Complete feature set generation
- Development-scale parallelization
- Integration with all dependent services

### Integration Test
- Automated feature validation
- Regression testing suite
- Performance benchmarking
- Feature consistency checks
- Test coverage validation

### Staging
- Production-scale feature generation
- Full historical computation
- Performance optimization testing
- Complete feature set validation
- Load testing

### Production
- Maximum parallelization
- Optimized computation paths
- Full feature set generation
- Comprehensive monitoring
- Production data persistence 

## Work Distribution & Parallelization

### Core Dimensions
1. **By Symbol**
   - Independent processing for each symbol (BTC, ETH, SOL)
   - Separate feature generation pipelines
   - Symbol-specific configuration and parameters
   - Allows horizontal scaling by symbol

2. **By Exchange**
   - Parallel processing across exchanges (Binance, Bybit, OKX)
   - Exchange-specific data normalization
   - Independent rate limiting and error handling
   - Cross-exchange feature computation

3. **By Feature Group**
   - Parallel computation of different feature types:
     - Technical indicators
     - Market structure features
     - Volatility features
     - Temporal features
     - etc.
   - Independent memory management per group
   - Group-specific optimization strategies

4. **Implementation Example**
```python
class FeatureGenerationOrchestrator:
    def __init__(self, config):
        self.symbols = ['BTC', 'ETH', 'SOL']
        self.exchanges = ['BINANCE', 'BYBIT', 'OKX']
        self.feature_groups = [
            'technical', 'market_structure', 'volatility',
            'temporal', 'microstructure', 'cross_sectional'
        ]
        
    def distribute_work(self):
        """Distribute feature generation across all dimensions."""
        jobs = []
        for symbol in self.symbols:
            for exchange in self.exchanges:
                for feature_group in self.feature_groups:
                    job = {
                        'symbol': symbol,
                        'exchange': exchange,
                        'feature_group': feature_group,
                        'config': self.get_config(symbol, exchange, feature_group)
                    }
                    jobs.append(job)
        
        # Execute jobs in parallel with resource constraints
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.process_job, job) for job in jobs]
            results = [f.result() for f in futures]
        
        return self.aggregate_results(results)
```

### Resource Management
1. **Memory Allocation**
   - Per-symbol memory budgets
   - Feature group-specific caching
   - Exchange data buffering limits
   - Garbage collection strategy

2. **CPU Distribution**
   - Dynamic worker allocation
   - Priority-based scheduling
   - Resource monitoring and adjustment
   - Load balancing across dimensions

3. **Storage Optimization**
   - Symbol-specific partitioning
   - Exchange-based data organization
   - Feature group compression strategies
   - Efficient cross-dimension queries 