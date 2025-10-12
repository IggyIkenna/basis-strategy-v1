# ML Inference Platform

## Overview
- Real-time model inference across multiple timeframes (1m, 5m, 15m, 1h, 4h, 1d)
- Loads models from ML Training Platform's model registry
- Subscribes to Feature Engineering Platform's feature updates
- Generates predictions for each timeframe as features become available
- Publishes predictions for Strategy Platform consumption

## Components

### 1. Model Management
- **Model Loading**:
  - Loads models from registry (MLflow/Vertex AI)
  - Handles model versioning and updates
  - Maintains model cache for fast inference
  - Supports multiple models per timeframe (e.g. swing-high-v1-1h, swing-high-v2-1h, swing-high-v1-4h, etc.)

### 2. Feature Processing
- **Feature Subscription**:
  - Subscribes to feature updates by timeframe
  - Validates feature completeness
  - Handles feature normalization/scaling
  - Maintains feature history for lookback periods

### 3. Prediction Generation
- **Timeframe-Specific Processing**:
  - Separate prediction pipelines per timeframe
  - Batches predictions when possible
  - Calculates prediction confidence scores
  - Handles missing/incomplete features

### 4. Output Publishing
- **Event Publishing**:
  - Real-time prediction events
  - Prediction metadata and confidence
  - Model version tracking
  - Performance metrics

## Workflow

### Real-time Flow
1. Subscribe to feature updates for each timeframe
2. Receive feature update event
3. Load appropriate model for timeframe
4. Generate prediction
5. Publish prediction event

```python
# Example prediction event
{
    "event_id": "123e4567-e89b-12d3-a456-426614174001",
    "timestamp": "2024-03-21T10:01:00Z",
    "service": "ml-inference-service",
    "environment": "production",
    "sub_environment": "live",
    "mode": "live",
    "event_type": "prediction",
    "model_id": "swing-high-v1-1h",
    "model_version": "1.0.0",
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "prediction": 1,  # 1 for long, -1 for short, 0 for neutral
    "confidence": 0.85
}
```

### Batch Flow
1. Receive batch prediction request
2. Load historical features
3. Generate predictions in batch
4. Store results
5. Publish batch completion event

## Performance Optimizations

### 1. Model Serving
- Model caching in memory
- Batch prediction support
- GPU acceleration when available
- Model warmup on startup

### 2. Feature Processing
- Feature caching per timeframe
- Pre-computed feature normalization
- Vectorized operations
- Parallel processing

### 3. Event Handling
- Asynchronous event processing
- Event batching for efficiency
- Back-pressure handling
- Error recovery

## Monitoring & Metrics

### 1. Performance Metrics
- Prediction latency
- Throughput per timeframe
- Cache hit rates
- Resource utilization

### 2. Quality Metrics
- Prediction accuracy
- Feature drift detection
- Model performance tracking
- Error rates

### 3. Operational Metrics
- Service health
- Event processing delays
- Resource bottlenecks
- Error patterns

## Configuration Example
```python
inference_config = {
    # Model serving
    "model_cache_size": 10,  # Number of models to keep in memory
    "batch_size": 32,        # Batch size for predictions
    "warmup_iterations": 100, # Model warmup iterations
    
    # Feature processing
    "feature_cache_duration": "1h",
    "max_feature_age": "7d",
    "normalize_features": True,
    
    # Performance
    "max_concurrent_predictions": 100,
    "prediction_timeout_ms": 100,
    "use_gpu": False,
    
    # Timeframes
    "enabled_timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
    "timeframe_specific_models": {
        "1h": "momentum-v1-1h",
        "4h": "momentum-v1-4h",
        "1d": "momentum-v1-1d"
    }
}
```

## Best Practices

## Environment-Specific Configurations

### Local Development (local-dev)
- Local model serving
- Fast model loading
- Minimal batch size
- CPU inference only
- Development metrics

### Local Integration (local-integration)
- Containerized serving
- Service integration
- Basic batch processing
- Mock feature pipeline
- Performance testing

### Central Development (central-dev)
- Vertex AI endpoints
- Development scaling
- Full batch processing
- Feature pipeline integration
- Monitoring setup

### Integration Test
- Automated inference tests
- Latency validation
- Throughput testing
- Error handling checks
- Performance profiling

### Staging
- Production-like setup
- Load testing
- Full feature pipeline
- Scaling validation
- Complete monitoring

### Production
- Optimized endpoints
- Maximum throughput
- Production monitoring
- Auto-scaling
- High availability

## Work Distribution

### Parallel Processing Dimensions
1. **By Symbol**
   - Independent prediction pipelines per symbol
   - Symbol-specific model loading
   - Separate feature subscriptions
   - Horizontal scaling capability

2. **By Exchange**
   - Exchange-specific data processing
   - Independent feature normalization
   - Cross-exchange model application
   - Exchange-level monitoring

3. **By Model Type**
   - Parallel inference for different model types:
     - Directional models (up/down)
     - Volatility models
     - Swing point models
     - Pattern completion models
   - Independent resource allocation
   - Type-specific optimization

4. **Implementation Example**
```python
class InferenceOrchestrator:
    def __init__(self, config):
        self.symbols = ['BTC', 'ETH', 'SOL']
        self.exchanges = ['BINANCE', 'BYBIT', 'OKX']
        self.model_types = [
            'directional', 'volatility', 'swing_points',
            'pattern_completion'
        ]
        
    def distribute_inference(self):
        """Distribute inference tasks across all dimensions."""
        inference_tasks = []
        for symbol in self.symbols:
            for exchange in self.exchanges:
                for model_type in self.model_types:
                    task = {
                        'symbol': symbol,
                        'exchange': exchange,
                        'model_type': model_type,
                        'model': self.load_model(symbol, model_type),
                        'config': self.get_config(symbol, exchange, model_type)
                    }
                    inference_tasks.append(task)
        
        # Execute inference in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.run_inference, task) 
                      for task in inference_tasks]
            predictions = [f.result() for f in futures]
        
        return self.aggregate_predictions(predictions)
```

### Resource Allocation
1. **Compute Resources**
   - GPU allocation by model type
   - CPU core distribution
   - Memory management per symbol
   - Load balancing across exchanges

2. **Model Serving**
   - Model cache per symbol/type
   - Batch size optimization
   - Resource sharing policies
   - Priority-based scheduling

3. **Network Resources**
   - Feature subscription bandwidth
   - Prediction publishing capacity
   - Exchange API quotas
   - Cross-datacenter optimization
