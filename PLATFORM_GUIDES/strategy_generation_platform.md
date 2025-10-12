# Strategy Generation Platform

## Overview
- Generates trading signals from ML model predictions
- Supports both live trading and backtesting modes
- Integrates with QuantConnect and internal order management
- Handles multiple strategies, symbols, and timeframes
- Manages separate strategy channels per client (e.g., ikenna, odum, christian)
- Implements signal aggregation and filtering logic
- Optimized for low-latency signal generation
- Supports parallel processing by client, strategy, symbol, and timeframe

## Service Components

### 1. Client Management
- **Client Configuration**:
  - Client-specific strategy settings
  - Exchange account mappings
  - Signal routing preferences (QuantConnect/Internal)
  - Performance tracking per client
- **Strategy Channels**:
  - Isolated strategy execution per client
  - Client-specific model selection
  - Independent signal generation
  - Separate performance monitoring

### 2. Signal Generation
- **ML Model Integration**:
  - Client-specific model selection
  - Real-time model prediction consumption
  - Multi-model signal aggregation
  - Confidence threshold filtering
  - Signal timing optimization
- **Strategy Logic**:
  - Client-specific strategy implementations
  - Signal combination rules
  - Entry/exit condition definitions
  - Position sizing logic

### 3. Output Management
- **QuantConnect Integration**:
  - Client-specific CSV signal file generation
  - Signal format standardization
  - Batch upload automation
  - Live trading integration
- **Internal Platform Integration**:
  - Client-specific signal streaming
  - Order management integration
  - Position tracking feedback
  - Performance monitoring

### 4. Signal Processing
- **Signal Validation**:
  - Data completeness checks
  - Model health validation
  - Signal consistency checks
  - Timing verification
- **Signal Enhancement**:
  - Volatility-based filtering
  - Trend confirmation
  - Signal strength scoring
  - Entry timing optimization

### 5. Performance Analytics
- **Signal Quality Metrics**:
  - Signal accuracy tracking
  - Timing precision analysis
  - Strategy performance metrics
  - Model contribution analysis
- **System Metrics**:
  - Signal latency tracking
  - Processing throughput
  - Resource utilization
  - Error rate monitoring

## Work Distribution & Process Management

### Process Architecture
1. **Independent Processes**
   - Each client-strategy-symbol combination runs as separate process
   - No Python GIL limitations
   - Process-level isolation for stability
   - Independent scaling per component

2. **Process Management Integration**
```python
class StrategyProcessManager:
    def __init__(self, config):
        self.config = config
        self.process_manager = ProcessManagementClient()
        
    def start_strategy_processes(self):
        """Start independent processes for each strategy combination."""
        process_configs = self._generate_process_configs()
        
        for process_config in process_configs:
            self.process_manager.start_process(
                name=f"strategy_{process_config['client_id']}_{process_config['strategy_id']}_{process_config['symbol']}",
                command=f"python strategy_runner.py",
                args=json.dumps(process_config),
                environment=self.config['environment'],
                mode=self.config['mode']
            )
    
    def _generate_process_configs(self):
        """Generate configurations for each process."""
        configs = []
        for client in self.config['clients']:
            client_config = self.config['clients'][client]
            for strategy_id in client_config['strategies']:
                for symbol in self.symbols:
                    configs.append({
                        'client_id': client,
                        'strategy_id': f"{client}_{strategy_id}",
                        'symbol': symbol,
                        'routing': client_config['routing'],
                        'models': client_config['models'],
                        'config': self._get_process_config(client, strategy_id, symbol)
                    })
        return configs
```

### Operational Modes

#### 1. Environment Types

##### Local Development
- **Storage**: Local DuckDB
- **Messaging**: Local pub/sub
- **Dependencies**: Mock implementations
- **Deployment**: Single process
```python
LOCAL_DEV_CONFIG = {
    'environment': 'local-dev',
    'storage': {
        'type': 'duckdb',
        'path': './local.db'
    },
    'messaging': {
        'type': 'local_pubsub',
        'queue_size': 1000
    },
    'dependencies': {
        'market_data': 'mock',
        'feature_engineering': 'mock',
        'ml_inference': 'mock'
    }
}
```

##### Local Integration
- **Storage**: Shared DuckDB
- **Messaging**: Redis pub/sub
- **Dependencies**: Containerized services
- **Deployment**: Docker compose
```python
LOCAL_INTEGRATION_CONFIG = {
    'environment': 'local-integration',
    'storage': {
        'type': 'duckdb',
        'path': '/shared/data.db'
    },
    'messaging': {
        'type': 'redis',
        'host': 'redis'
    },
    'dependencies': {
        'market_data': 'container',
        'feature_engineering': 'container',
        'ml_inference': 'container'
    }
}
```

##### Cloud Development
- **Storage**: BigQuery
- **Messaging**: Pub/Sub
- **Dependencies**: Cloud services
- **Deployment**: Kubernetes
```python
CLOUD_DEV_CONFIG = {
    'environment': 'cloud-dev',
    'storage': {
        'type': 'bigquery',
        'project': 'dev-project'
    },
    'messaging': {
        'type': 'pubsub',
        'project': 'dev-project'
    },
    'dependencies': {
        'market_data': 'service',
        'feature_engineering': 'service',
        'ml_inference': 'service'
    }
}
```

#### 2. Execution Modes

##### Mock Mode
```python
class MockModeRunner:
    def __init__(self, config):
        self.mock_market_data = MockMarketData()
        self.mock_ml_inference = MockMLInference()
        
    def run(self):
        """Run strategy with mock dependencies."""
        while True:
            market_data = self.mock_market_data.get_next()
            predictions = self.mock_ml_inference.predict(market_data)
            signals = self.generate_signals(predictions)
            self.publish_signals(signals)
```

##### Live Mode
```python
class LiveModeRunner:
    def __init__(self, config):
        self.market_data_client = MarketDataClient()
        self.ml_inference_client = MLInferenceClient()
        self.signal_publisher = SignalPublisher()
        
    def run(self):
        """Run strategy with live dependencies."""
        self.market_data_client.subscribe(self.on_market_data)
        
    def on_market_data(self, market_data):
        """Handle real-time market data."""
        predictions = self.ml_inference_client.get_predictions(market_data)
        signals = self.generate_signals(predictions)
        self.signal_publisher.publish(signals)
```

##### Simulation Mode
```python
class SimulationModeRunner:
    def __init__(self, config):
        self.market_data_replay = MarketDataReplay()
        self.ml_inference_client = MLInferenceClient()
        
    def run(self):
        """Run strategy with simulated market data."""
        while data := self.market_data_replay.get_next():
            predictions = self.ml_inference_client.get_predictions(data)
            signals = self.generate_signals(predictions)
            self.record_signals(signals)
```

##### Historical Mode
```python
class HistoricalModeRunner:
    def __init__(self, config):
        self.market_data_loader = HistoricalDataLoader()
        self.ml_inference_client = MLInferenceClient()
        
    def run(self):
        """Run strategy on historical data."""
        data_chunks = self.market_data_loader.get_chunks()
        for chunk in data_chunks:
            predictions = self.ml_inference_client.get_predictions(chunk)
            signals = self.generate_signals(predictions)
            self.persist_signals(signals)
```

### Updated Configuration Example
```python
config = {
    # Environment Configuration
    'environment': 'cloud-dev',
    'mode': 'live',
    
    # Client Management
    'clients': {
        'ikenna': {
            'strategies': ['swing_high_v1', 'swing_low_v1'],
            'routing': 'quantconnect',
            'models': {
                'swing_high_v1': {
                    'model_id': 'swing_high_model_v1',
                    'confidence_threshold': 0.80,
                    'lookback_window': 20
                },
                'swing_low_v1': {
                    'model_id': 'swing_low_model_v1',
                    'confidence_threshold': 0.80,
                    'lookback_window': 20
                }
            },
            'quantconnect': {
                'api_key': 'IKENNA_QC_API_KEY',
                'project_id': 'IKENNA_QC_PROJECT_ID'
            }
        }
        // ... other client configs ...
    },
    
    # Storage Configuration
    'storage': {
        'type': 'bigquery',
        'project': 'dev-project',
        'dataset': 'strategy_signals'
    },
    
    # Messaging Configuration
    'messaging': {
        'type': 'pubsub',
        'project': 'dev-project',
        'topic': 'strategy_signals'
    },
    
    # Process Management
    'process': {
        'memory_limit_mb': 1024,
        'cpu_limit': 1,
        'log_level': 'INFO'
    }
}
```

## Best Practices
- Implement comprehensive signal validation per client
- Monitor model prediction quality for each strategy
- Track signal generation latency by client
- Maintain detailed signal logs per client
- Handle platform-specific requirements
- Implement client-specific circuit breakers
- Monitor resource usage per client
- Test on multiple market conditions
- Validate with out-of-sample testing
- Ensure client data isolation
- Regular performance reviews per client
- Maintain separate audit trails per client 