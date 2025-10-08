# CONFIGURATION ARCHITECTURE GUIDE

## OVERVIEW
All configuration must be loaded from YAML files and validated through Pydantic models. No hardcoded configuration values are allowed.

## CONFIGURATION STRUCTURE
- **YAML Files**: All configuration in configs/ directory
- **Pydantic Models**: All config validated through config_models.py
- **Structure**: Follow modes/venues/scenarios YAML structure
- **Environment**: Use .env files only when specified in documentation

## REQUIRED PRACTICES
- ✅ Load all configuration from YAML files (not hardcoded in code)
- ✅ Use environment variables only when specified in .env files
- ✅ Validate all configuration through Pydantic models
- ✅ Follow the YAML-based config structure (modes/venues/scenarios)
- ✅ Create configuration entries in appropriate YAML files if config is missing
- ✅ Add to Pydantic models in config_models.py to ensure validation passes

## FORBIDDEN PRACTICES
- ❌ Hardcoding any configuration values (API keys, file paths, timeouts, etc.)
- ❌ Bypassing configuration loading architecture
- ❌ Using static configuration values instead of dynamic loading
- ❌ Ignoring Pydantic validation

## CONFIGURATION FILES STRUCTURE
```
configs/
├── modes/
│   ├── pure_lending.yaml
│   ├── btc_basis.yaml
│   └── eth_leveraged.yaml
├── venues/
│   ├── binance.yaml
│   ├── bybit.yaml
│   └── okx.yaml
└── scenarios/
    ├── backtest.yaml
    └── live.yaml
```

## PYDANTIC MODELS
All configuration must be defined in `config_models.py` with proper validation:
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class VenueConfig(BaseModel):
    api_key: str = Field(..., description="API key for venue")
    secret_key: str = Field(..., description="Secret key for venue")
    timeout: int = Field(default=30, description="Timeout in seconds")
    
class ModeConfig(BaseModel):
    name: str = Field(..., description="Mode name")
    venues: Dict[str, VenueConfig] = Field(..., description="Venue configurations")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Mode parameters")
```

## CONFIGURATION LOADING
Components must load configuration through the configuration loading architecture:
```python
from basis_strategy_v1.core.config.config_loader import ConfigLoader

class MyComponent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Load specific configuration
        self.api_key = self.config.get('api_key')
        self.timeout = self.config.get('timeout_seconds', 30)
```

## EXAMPLES OF WRONG APPROACHES
```python
# ❌ WRONG: Hardcoded API key
api_key = "sk-1234567890abcdef"

# ❌ WRONG: Hardcoded file path
data_file = "/path/to/data.csv"

# ❌ WRONG: Hardcoded timeout
timeout = 30

# ❌ WRONG: Hardcoded URL
base_url = "https://api.example.com"
```

## EXAMPLES OF CORRECT APPROACHES
```python
# ✅ CORRECT: Load from configuration
api_key = self.config.get('api_key')

# ✅ CORRECT: Use configuration loading
data_file = self.config.get('data_file_path')

# ✅ CORRECT: Load from YAML config
timeout = self.config.get('timeout_seconds', 30)

# ✅ CORRECT: Load from configuration
base_url = self.config.get('base_url')
```

## ADDING NEW CONFIGURATION
When adding new configuration:
1. Add to appropriate YAML file in configs/ directory
2. Update Pydantic models in config_models.py
3. Add validation rules if needed
4. Update component to load from configuration
5. Test configuration loading and validation

## VALIDATION CHECKLIST
Before committing any configuration changes:
- [ ] No hardcoded configuration values
- [ ] Configuration loaded from YAML files
- [ ] Pydantic validation passes for all config
- [ ] Configuration entries added to appropriate YAML files
- [ ] Pydantic models updated if new config fields added
- [ ] Component loads configuration properly
- [ ] Configuration structure follows modes/venues/scenarios pattern

## ERROR HANDLING
If configuration is missing:
1. Check if configuration exists in YAML files
2. Verify Pydantic models are updated
3. Ensure configuration loading is working
4. Add missing configuration to appropriate YAML file
5. Update Pydantic models if needed
6. Fix the root cause, don't hardcode values

