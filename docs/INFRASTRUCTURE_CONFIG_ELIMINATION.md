# Infrastructure Config Elimination

## Design Decision: JSON Configs Eliminated

We eliminated `configs/*.json` files entirely because all infrastructure configuration is better handled through:

### Environment Variables (Environment-Specific)
- `BASIS_REDIS_URL` - Redis connection URL
- `BASIS_DATA_DIR` - Data directory path  
- `BASIS_RESULTS_DIR` - Results storage path
- `BASIS_API_CORS_ORIGINS` - API CORS origins (comma-separated)
- `BASIS_API_PORT` - API port
- `BASIS_API_HOST` - API host

### Hardcoded Defaults (Always True for Realistic Backtesting)
- **Cross-network simulations**: Always `true` - enables realistic transfer simulations
- **Cross-network transfers**: Always `true` - enables realistic cross-venue operations
- **Rate usage**: Always use live rates (never fixed rates for realistic modeling)

### Eliminated (Live Trading Only)
- **Testnet configuration**: Live trading concern, not needed for backtest focus
- **Complex infrastructure configs**: Over-engineered for current backtest focus

## Benefits
1. **Simplified config structure**: Only YAML files for strategy/venue/share_class configs
2. **Environment-appropriate**: Infrastructure settings properly separated by environment
3. **Hardcoded sensible defaults**: No need to configure obvious settings
4. **Reduced complexity**: Eliminated JSON config loading and merging logic
5. **Focused on backtest**: Removed live trading complexity

## Implementation
- Infrastructure fields moved to environment variables in `backend/env.unified` and `.env.local`
- Cross-network and rate logic hardcoded to sensible defaults in components
- JSON config loading removed from `config_manager.py`
- Validation simplified to only check YAML configs

## Future: Testnet Implementation
When implementing live trading, testnet configuration should be:
- Testnet endpoints in environment variables (per-environment)
- Testnet-specific logic in execution components
- Simulation vs real execution mode flags
