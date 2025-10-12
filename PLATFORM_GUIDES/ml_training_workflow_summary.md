# ML Training Workflow

## Overview
- 2160 model variants: BTC/ETH/SOL breakout/reversion prediction using swing event features
- Classification targets: Selected from swing event features (breakout/reversion patterns)
- Algorithm: LightGBM
- Goal: Reduce ~15K features to 300-500, optimize model precision with feature screening and hyperparameter tuning
- Dataset: ~600K total rows; filtered based on swing event occurrence
- Features: ~15K total (~5K per coin); each model uses features from all coins (cross-coin training)
- Evaluation metric: Average precision score across all classes

## Variant Structure
- 6 lookback windows: [2, 3, 5, 10, 20, 50]
- 120 target variations per window:
  - Target types: high_breakout, high_reversion, low_breakout, low_reversion
  - Standard deviation thresholds: [1.0, 1.5, 2.0, 2.5]
  - Breakout/reversion thresholds: [0.5, 1.0, 1.5]
- 3 cryptocurrencies
- Data filtered to rows with identified swing events

## Pipeline
1. **Data Preparation**
   - Drop features: >70% missing values
   - Apply variance threshold
   - Remove correlations: >90%
   - Drop features where >95% values are the same
   - Drop features where >90% values are NaN
   - No standardization needed (tree-based models)
   - Output: ~5-8K features

2. **Feature Selection**
   - Remove target-related features from input features
   - Chronological subsampling (20-30K samples)
   - Shallow LightGBM: max 30 leaves, depth 5, ~100 rounds
   - Early stopping: ~20 rounds
   - Extract top 200 features per variant
   - Aggregate features across variants
   - Expected output: ~300-500 features

3. **Hyperparameter Tuning - Multi-Stage Approach**
   - **Stage 1:** Initial Model Selection (25% of compute budget)
     - Train all 2160 variants with default parameters on reduced feature set
     - Early stopping: ~30 rounds to prevent overfitting
     - Select top performing variant for each of the 36 combinations (1 per coin × 6 timeframes × 2 swing types)
   
   - **Stage 2:** Coarse Optimization (15% of compute budget)
     - Select 6 representative models (one from each timeframe)
     - Run Bayesian optimization with broad parameter ranges
     - Early stopping: ~40 rounds for optimization runs
   
   - **Stage 3:** Targeted Optimization (35% of compute budget)
     - Apply learnings from Stage 2 to all 36 models
     - Use rolling-window CV (5 folds) with chronological train/validate splits
     - Early stopping: ~40 rounds for consistent evaluation
   
   - **Stage 4:** Fine-tuning (25% of compute budget)
     - Further optimize best-performing models with focused parameter ranges
     - Early stopping: ~50 rounds for fine-tuning
   
   - **Tuned Parameter Space:**
     - num_leaves: [30, 50, 80]
     - max_depth: [5, 6, 7, 9]
     - feature_fraction: [0.7]
     - min_child_samples: 1% of training samples (adaptive to dataset size)
     - learning_rate: [0.01, 0.05, 0.1]
     - lambda_l1: [0, 0.01, 0.1]
   
   - **Fixed LightGBM Parameters:**
     - objective: 'multiclass' (fixed for our classification task)
     - num_class: 3 (breakout, reversal, neither)
     - metric: 'multi_logloss' (for early stopping) and 'average_precision' (for evaluation)
     - boosting_type: 'gbdt'
     - verbosity: -1 (silent during hyperparameter search)
     - bagging_freq: 5 (use bagging every 5 iterations)
     - bagging_fraction: 0.8 (use 80% of data for each tree)

4. **Production Training**
   - Train each model variant with its optimal hyperparameters identified during tuning
   - Use sufficient boosting rounds (500-1000) with early stopping (patience ~50 rounds)
   - Train on full available dataset with proper chronological validation splits
   - Save best performing models to model registry for inference stage

5. **Inference & Deployment**
   - Generate batch predictions for entire historical period (2019-present)
   - Save top model per main variant (36 models) to model registry with versioning
   - Deployment modes:
     - Local: Use ML workflow framework
     - Cloud: Deploy on Vertex AI
   - Live inferencing: Append to historical predictions using latest models from registry
   - Inference frequency: Based on prediction time horizon

## Implementation Details
- Feature engineering: Implemented in specialized generators (candlestick, technical, temporal, market structure, volatility)
- Target engineering: Swing high/low identification with multiple timeframes and thresholds
- Data pipeline scripts will follow a structure similar to: run_feature_generation.sh, generate_features.py
- Target generation scripts will follow a structure similar to: run_target_generation.sh, generate_targets.py

## Best Practices
- Maintain chronological data integrity
- Use early stopping
- Moderate complexity with strong regularization
- Consistent feature sets across variants
- Regular retraining
- Cross-coin feature utilization for improved signal detection

## Environment-Specific Configurations

### Local Development (local-dev)
- Local MLflow instance
- Small training datasets
- Quick model iterations
- CPU-only training
- SQLite model registry

### Local Integration (local-integration)
- Containerized MLflow
- Shared model registry
- Integration testing
- Sample dataset pipeline
- Basic GPU support

### Central Development (central-dev)
- Vertex AI integration
- Development compute resources
- Full training pipeline
- Shared model registry
- Extended GPU access

### Integration Test
- Automated training tests
- Pipeline validation
- Performance benchmarking
- Test dataset suite
- Regression testing

### Staging
- Production-like resources
- Full dataset access
- Performance validation
- Complete pipeline testing
- UAT environment

### Production
- Maximum compute resources
- Production data pipeline
- Optimized training
- Full monitoring suite
- Production model registry

## Work Distribution & Process Management

### Parallel Processing Dimensions
1. **By Model Variant**
   - Independent processes for each model variant
   - Complete isolation between variant training
   - No shared memory or state
   - Separate logs and artifacts per variant

2. **Variant Breakdown**
   - Total variants = 2160 (3 symbols × 6 windows × 120 variations)
   - Process groups by symbol (BTC, ETH, SOL)
   - Sub-groups by lookback window
   - Final split by target configuration

3. **Process Management**
```python
class ModelTrainingOrchestrator:
    def __init__(self, config):
        self.symbols = ['BTC', 'ETH', 'SOL']
        self.lookback_windows = [2, 3, 5, 10, 20, 50]
        self.target_configs = self._generate_target_configs()
        self.max_concurrent_processes = config.get('max_concurrent_processes', 20)
        
    def _generate_target_configs(self):
        """Generate all target configurations."""
        configs = []
        for target_type in ['high_breakout', 'high_reversion', 
                           'low_breakout', 'low_reversion']:
            for std_dev in [1.0, 1.5, 2.0, 2.5]:
                for threshold in [0.5, 1.0, 1.5]:
                    configs.append({
                        'type': target_type,
                        'std_dev': std_dev,
                        'threshold': threshold
                    })
        return configs
    
    def distribute_training(self):
        """Distribute training across separate processes."""
        training_jobs = []
        for symbol in self.symbols:
            for window in self.lookback_windows:
                for target_config in self.target_configs:
                    job = {
                        'symbol': symbol,
                        'window': window,
                        'target_config': target_config,
                        'output_dir': f'models/{symbol}/{window}/{target_config["type"]}'
                    }
                    training_jobs.append(job)
        
        # Process pool for managing concurrent training jobs
        completed_jobs = []
        active_processes = {}
        
        while training_jobs or active_processes:
            # Start new processes up to max concurrent
            while len(active_processes) < self.max_concurrent_processes and training_jobs:
                job = training_jobs.pop(0)
                process = subprocess.Popen(
                    ['python', 'train_model.py', json.dumps(job)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                active_processes[job['output_dir']] = {
                    'process': process,
                    'job': job,
                    'start_time': time.time()
                }
            
            # Check completed processes
            for model_dir, process_info in list(active_processes.items()):
                if process_info['process'].poll() is not None:
                    completed_jobs.append(process_info['job'])
                    del active_processes[model_dir]
            
            time.sleep(10)  # Check status every 10 seconds
        
        return completed_jobs
```

### Resource Management
1. **System Resources**
   - Process-level memory isolation
   - CPU core allocation per process
   - GPU assignment for supported models
   - Disk I/O management

2. **Training Coordination**
   - Maximum concurrent processes limit
   - Process health monitoring
   - Automatic restart on failure
   - Resource usage tracking

3. **Artifact Management**
   - Separate artifact directories per variant
   - Independent model versioning
   - Isolated training logs
   - Variant-specific metrics 