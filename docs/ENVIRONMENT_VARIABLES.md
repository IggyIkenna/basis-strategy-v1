# Environment Variables - Complete Guide 🔧

**Purpose**: Complete mapping, usage, analysis, and recommendations for all environment variables  
**Status**: Comprehensive guide with redundancy analysis  
**Updated**: October 3, 2025 - Consolidated from MAPPING and ANALYSIS docs

---

## 📋 **Table of Contents**

1. [Overview](#overview)
2. [Environment Variables by Category](#environment-variables-by-category)
3. [Usage Analysis](#usage-analysis)
4. [Redundancy Analysis](#redundancy-analysis)
5. [Recommendations](#recommendations)
6. [Security](#security)
7. [Validation](#validation)

---

## 📋 **Overview**

### **Configuration Loading Priority**
1. **Environment Variables** (BASIS_*) - Highest priority
2. **YAML Configuration Files** (configs/modes/, venues/, share_classes/) - Strategy and venue configs
3. **JSON Hierarchy** (configs/default.json, {environment}.json, local.json) - **DOCUMENTED BUT NOT IMPLEMENTED**
4. **Deployment Config** (deploy/.env*) - Caddy-specific deployment variables only

### **Fundamental Environment Variables**
| Variable | Values | Component | Purpose |
|----------|--------|-----------|---------|
| `BASIS_ENVIRONMENT` | dev, staging, production | All components | Controls testnet vs mainnet for ALL services |
| `BASIS_EXECUTION_MODE` | backtest, live | All components | Controls data source, timing, and execution behavior |

**Critical Distinction**:
- **BASIS_ENVIRONMENT**: Controls which APIs to use (testnet vs mainnet)
- **BASIS_EXECUTION_MODE**: Controls how system operates (simulated vs real)

**Backtest Mode**:
- Uses CSV data from `data/` directory
- Simulated execution (no real trades)
- Hourly events (on the hour: 00:00, 01:00, etc.)
- Position tracking via execution manager updates
- All timestamps must be hourly-aligned

**Live Mode**:
- Uses real-time WebSocket/API data via LiveDataProvider
- Real execution via CCXT/Web3
- Continuous events (any timestamp)
- Position tracking via queries + updates

### **Configuration Separation of Concerns**

**YAML Configuration Files** (IMPLEMENTED):
- **Modes** (`configs/modes/*.yaml`): Strategy-specific parameters
- **Venues** (`configs/venues/*.yaml`): Venue-specific configurations  
- **Share Classes** (`configs/share_classes/*.yaml`): Share class definitions

**JSON Hierarchy** (DOCUMENTED BUT NOT IMPLEMENTED):
- **Base Configuration** (`configs/default.json`): Infrastructure defaults
- **Environment-Specific Configuration** (`configs/{dev,staging,production}.json`): Environment overrides
- **Local Development Configuration** (`configs/local.json`): Local overrides

**Deployment Configuration** (`deploy/.env*`):
- Caddy-specific deployment variables only
- Domain names, TLS settings, port mappings
- Basic authentication, health check intervals
- Timestamps are actual execution times

### **Naming Convention**
- **Prefix**: `BASIS_` (all environment variables)
- **Nesting**: Double underscore `__` for nested configuration
- **Example**: `BASIS_API__PORT` → `config['api']['port']`

### **Total Environment Variables**: 45 variables across 15 categories

---

## 🔧 **Environment Variables by Category**

### **1. API Configuration**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_API__PORT` | Backend server port | FastAPI server | dev vs production ports |
| `BASIS_API__RELOAD` | Auto-reload on changes | FastAPI server | dev convenience |

**Code Usage**:
```python
# backend/src/basis_strategy_v1/infrastructure/config/settings.py
settings = get_settings()
api_port = settings['api']['port']  # Default: 8001
```

---

### **2. Database Configuration**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_DATABASE__TYPE` | Database type (sqlite/postgres) | Database layer | dev vs production |
| `BASIS_DATABASE__URL` | Database connection string | Database layer | Local vs cloud database |

**Code Usage**:
```python
# Used by database initialization
db_type = settings['database']['type']  # Default: sqlite
db_url = settings['database']['url']    # Default: sqlite:///./data/basis_strategy_v1.db
```

---

### **3. Redis Configuration**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_REDIS__ENABLED` | Enable Redis pub/sub | All components | Inter-component communication |
| `BASIS_REDIS__URL` | Redis connection string | Redis client | Local vs cloud Redis |
| `BASIS_REDIS__SESSION_TTL` | Session timeout | API layer | User session management |
| `BASIS_REDIS__CACHE_TTL` | Cache timeout | Data provider | Data caching strategy |

**Code Usage**:
```python
# backend/src/basis_strategy_v1/infrastructure/redis_client.py
redis_enabled = settings['redis']['enabled']  # Default: true
redis_url = settings['redis']['url']          # Default: redis://localhost:6379/0
```

---

### **4. Cache Configuration**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_CACHE__TYPE` | Cache type (redis/memory) | Cache layer | Performance vs simplicity |
| `BASIS_CACHE__REDIS_URL` | Redis cache connection | Cache layer | Dedicated cache instance |

**Code Usage**:
```python
# Used by cache layer
cache_type = settings['cache']['type']  # Default: redis
```

---

### **5. dev Settings**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_DEBUG` | Enable debug mode | All components | dev vs production |
| `BASIS_MONITORING__LOG_LEVEL` | Logging verbosity | All components | Debug vs production logging |

**Code Usage**:
```python
# Used throughout codebase
debug_mode = settings['debug']  # Default: true
log_level = settings['monitoring']['log_level']  # Default: DEBUG
```

---

### **6. Data Provider Settings**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_DATA__CACHE_ENABLED` | Enable data caching | Data Provider | Performance optimization |
| `BASIS_DATA__DATA_DIR` | Data file directory | Data Provider | Local vs cloud data storage |

**Code Usage**:
```python
# backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py
cache_enabled = settings['data']['cache_enabled']  # Default: true
data_dir = settings['data']['data_dir']            # Default: ./data
```

---

### **7. Rate Configuration**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_RATES__USE_FIXED_RATES` | Use fixed rates for testing | All components | Testing vs live data |
| `BASIS_RATES__FIXED__BYBIT_FUNDING_APR` | Override funding rate | CEX Execution Manager | Testing specific scenarios |

**Code Usage**:
```python
# Used by rate calculations
use_fixed_rates = settings['rates']['use_fixed_rates']  # Default: false
if use_fixed_rates:
    bybit_funding = settings['rates']['fixed']['bybit_funding_apr']
```

---

### **8. Data Downloader API Keys**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_DOWNLOADERS__COINGECKO_API_KEY` | CoinGecko API access | Data downloaders | Market data access |
| `BASIS_DOWNLOADERS__TARDIS_API_KEY` | Tardis API access | Data downloaders | Historical data access |
| `BASIS_DOWNLOADERS__ALCHEMY_API_KEY` | Alchemy mainnet RPC | Web3 operations | Ethereum mainnet access |
| `BASIS_DOWNLOADERS__ALCHEMY_API_KEY_2` | Alchemy testnet RPC | Web3 operations | Ethereum testnet access |
| `BASIS_DOWNLOADERS__AAVESCAN_API_KEY` | AaveScan Pro API | Data downloaders | AAVE protocol data |

**Code Usage**:
```python
# scripts/downloaders/clients/coingecko_client.py
api_key = settings['downloaders']['coingecko_api_key']
# Used for rate-limited API calls
```

---

### **9. CEX API Configuration**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_CEX__BINANCE_SPOT_API_KEY` | Binance spot trading | CEX Execution Manager | Spot trading access |
| `BASIS_CEX__BINANCE_SPOT_SECRET` | Binance spot secret | CEX Execution Manager | Spot trading authentication |
| `BASIS_CEX__BINANCE_SPOT_TESTNET` | Use testnet | CEX Execution Manager | Testing vs production |
| `BASIS_CEX__BINANCE_FUTURES_API_KEY` | Binance futures trading | CEX Execution Manager | Perpetual futures access |
| `BASIS_CEX__BINANCE_FUTURES_SECRET` | Binance futures secret | CEX Execution Manager | Futures authentication |
| `BASIS_CEX__BINANCE_FUTURES_TESTNET` | Use testnet | CEX Execution Manager | Testing vs production |
| `BASIS_CEX__BYBIT_API_KEY` | Bybit trading | CEX Execution Manager | Multi-exchange hedging |
| `BASIS_CEX__BYBIT_SECRET` | Bybit secret | CEX Execution Manager | Bybit authentication |
| `BASIS_CEX__BYBIT_TESTNET` | Use testnet | CEX Execution Manager | Testing vs production |
| `BASIS_CEX__OKX_API_KEY` | OKX trading | CEX Execution Manager | Multi-exchange hedging |
| `BASIS_CEX__OKX_SECRET` | OKX secret | CEX Execution Manager | OKX authentication |
| `BASIS_CEX__OKX_PASSPHRASE` | OKX passphrase | CEX Execution Manager | OKX authentication |
| `BASIS_CEX__OKX_TESTNET` | Use testnet | CEX Execution Manager | Testing vs production |

**Code Usage**:
```python
# backend/src/basis_strategy_v1/core/strategies/components/cex_execution_manager.py
binance_spot = ccxt.binance({
    'apiKey': settings['cex']['binance_spot_api_key'],
    'secret': settings['cex']['binance_spot_secret'],
    'sandbox': settings['cex']['binance_spot_testnet']
})
```

---

### **10. Web3 Wallet Configuration**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_WEB3__PRIVATE_KEY` | Wallet private key | OnChain Execution Manager | On-chain transaction signing |
| `BASIS_WEB3__WALLET_ADDRESS` | Wallet address | OnChain Execution Manager | Transaction from address |
| `BASIS_WEB3__MAINNET_RPC_URL` | Mainnet RPC endpoint | Web3 operations | Ethereum mainnet access |
| `BASIS_WEB3__SEPOLIA_RPC_URL` | Sepolia RPC endpoint | Web3 operations | Ethereum testnet access |
| `BASIS_WEB3__NETWORK` | Active network | Web3 operations | Testnet vs mainnet |
| `BASIS_WEB3__CHAIN_ID` | Chain ID | Web3 operations | Network validation |

**Code Usage**:
```python
# backend/src/basis_strategy_v1/core/strategies/components/onchain_execution_manager.py
private_key = settings['web3']['private_key']
wallet_address = settings['web3']['wallet_address']
network = settings['web3']['network']  # 'sepolia' or 'mainnet'
```

---

### **11. Instadapp Configuration**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_INSTADAPP__API_KEY` | Instadapp API key | OnChain Execution Manager | Flash loan aggregation |
| `BASIS_INSTADAPP__API_SECRET` | Instadapp secret | OnChain Execution Manager | Flash loan authentication |
| `BASIS_INSTADAPP__TESTNET` | Use testnet | OnChain Execution Manager | Testing vs production |

**Code Usage**:
```python
# Used for atomic flash loan operations
instadapp_key = settings['instadapp']['api_key']
# Only used if atomic flash loans are enabled
```

---

### **12. Live Testing Configuration**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_LIVE_TESTING__ENABLED` | Enable live trading | All execution managers | Safety switch |
| `BASIS_LIVE_TESTING__READ_ONLY` | Read-only mode | All execution managers | Safe testing mode |
| `BASIS_LIVE_TESTING__MAX_TRADE_SIZE_USD` | Maximum trade size | Execution managers | Risk management |

**Code Usage**:
```python
# Used by all execution managers
live_enabled = settings['live_testing']['enabled']  # Default: false
read_only = settings['live_testing']['read_only']   # Default: true
max_trade_size = settings['live_testing']['max_trade_size_usd']  # Default: 100
```

---

### **13. Testnet Configuration**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_TESTNET__ENABLED` | Enable testnet mode | All components | Testing vs production |
| `BASIS_TESTNET__NETWORK` | Testnet network | Web3 operations | Sepolia vs Goerli |
| `BASIS_TESTNET__FAUCET_URL` | Testnet faucet URL | Testing utilities | Test ETH acquisition |
| `BASIS_TESTNET__MAX_GAS_PRICE_GWEI` | Maximum gas price | Web3 operations | Gas cost control |
| `BASIS_TESTNET__CONFIRMATION_BLOCKS` | Confirmation blocks | Web3 operations | Transaction finality |

**Code Usage**:
```python
# Used by Web3 operations
testnet_enabled = settings['testnet']['enabled']  # Default: true
max_gas_price = settings['testnet']['max_gas_price_gwei']  # Default: 20
```

---

### **14. Rate Limiting Configuration**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_DOWNLOADERS__COINGECKO_RATE_LIMIT` | CoinGecko rate limit | Data downloaders | API rate management |
| `BASIS_DOWNLOADERS__BYBIT_RATE_LIMIT` | Bybit rate limit | Data downloaders | API rate management |

**Code Usage**:
```python
# Used by rate limiting logic
coingecko_limit = settings['downloaders']['coingecko_rate_limit']  # Default: 500
```

---

### **15. Download Configuration**
| Variable | Usage | Component | Business Decision |
|----------|-------|-----------|-------------------|
| `BASIS_DOWNLOADERS__START_DATE` | Data download start date | Data downloaders | Historical data range |
| `BASIS_DOWNLOADERS__END_DATE` | Data download end date | Data downloaders | Historical data range |
| `BASIS_DOWNLOADERS__CHUNK_SIZE_DAYS` | Download chunk size | Data downloaders | Memory management |
| `BASIS_DOWNLOADERS__RETRY_ATTEMPTS` | Retry attempts | Data downloaders | Error handling |
| `BASIS_DOWNLOADERS__RETRY_DELAY` | Retry delay | Data downloaders | Error handling |

**Code Usage**:
```python
# Used by data download scripts
start_date = settings['downloaders']['start_date']  # Default: 2024-01-01
chunk_size = settings['downloaders']['chunk_size_days']  # Default: 90
```

---

## 📊 **Usage Analysis**

### **Usage Mapping by Component**

#### **1. CEX Execution Manager** (12 variables)
- **Purpose**: Centralized exchange trading (Binance, Bybit, OKX)
- **Usage**: API authentication, testnet configuration
- **Critical**: All API keys and secrets for live trading
- **Code Location**: `backend/src/basis_strategy_v1/core/strategies/components/cex_execution_manager.py`

#### **2. OnChain Execution Manager** (6 variables)
- **Purpose**: On-chain operations (AAVE, staking, flash loans)
- **Usage**: Web3 wallet, RPC endpoints, Instadapp integration
- **Critical**: Private key and wallet address for transaction signing
- **Code Location**: `backend/src/basis_strategy_v1/core/strategies/components/onchain_execution_manager.py`

#### **3. Data Provider** (8 variables)
- **Purpose**: Market data access and caching
- **Usage**: API keys for data sources, cache configuration
- **Critical**: CoinGecko, Tardis, Alchemy API keys
- **Code Location**: `backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py`

#### **4. Infrastructure** (19 variables)
- **Purpose**: System configuration (API, database, Redis, cache)
- **Usage**: Server ports, database connections, Redis configuration
- **Critical**: Redis for inter-component communication
- **Code Location**: `backend/src/basis_strategy_v1/infrastructure/config/settings.py`

---

## 🔍 **Redundancy Analysis**

### **Identified Redundancies**

#### **1. Redis Configuration Duplication**
```bash
# Current (redundant)
BASIS_REDIS__URL=redis://localhost:6379/0
BASIS_CACHE__REDIS_URL=redis://localhost:6379/0

# Recommended (consolidated)
BASIS_REDIS__URL=redis://localhost:6379/0
# Remove BASIS_CACHE__REDIS_URL, use BASIS_REDIS__URL
```

#### **2. Alchemy API Key Duplication**
```bash
# Current (redundant)
BASIS_DOWNLOADERS__ALCHEMY_API_KEY=vV3z-UCRtQvWb26MH9v7A
BASIS_WEB3__MAINNET_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/vV3z-UCRtQvWb26MH9v7A

# Recommended (consolidated)
BASIS_ALCHEMY__API_KEY=vV3z-UCRtQvWb26MH9v7A
# Construct RPC URLs in code using the single API key
```

#### **3. Testnet Configuration Duplication**
```bash
# Current (redundant)
BASIS_CEX__BINANCE_SPOT_TESTNET=true
BASIS_CEX__BINANCE_FUTURES_TESTNET=true
BASIS_CEX__BYBIT_TESTNET=true
BASIS_CEX__OKX_TESTNET=true
BASIS_WEB3__NETWORK=sepolia
BASIS_TESTNET__ENABLED=true

# Recommended (consolidated)
BASIS_TESTNET__ENABLED=true
BASIS_TESTNET__NETWORK=sepolia
# Use single testnet flag to control all services
```

### **Missing Environment Variables**

#### **1. GCS Configuration** (for deployment)
```bash
# Missing variables needed for production deployment
BASIS_GCS__BUCKET_NAME=your-gcs-bucket
BASIS_GCS__CREDENTIALS_PATH=/path/to/service-account.json
BASIS_GCS__DATA_SYNC_ENABLED=true
```

#### **2. Monitoring Configuration**
```bash
# Missing variables for production monitoring
BASIS_MONITORING__METRICS_ENABLED=true
BASIS_MONITORING__ALERT_WEBHOOK=https://hooks.slack.com/...
BASIS_MONITORING__LOG_AGGREGATION_ENABLED=true
```

#### **3. Security Configuration**
```bash
# Missing variables for security
BASIS_SECURITY__ENCRYPTION_KEY=your-encryption-key
BASIS_SECURITY__JWT_SECRET=your-jwt-secret
BASIS_SECURITY__CORS_ORIGINS=["http://localhost:3000"]
```

---

## 📋 **Recommendations**

### **Consolidated Configuration Structure**

#### **1. Core Infrastructure**
```bash
# API Configuration
BASIS_API__PORT=8001
BASIS_API__RELOAD=true
BASIS_API__CORS_ORIGINS=["http://localhost:3000"]

# Database Configuration
BASIS_DATABASE__TYPE=sqlite
BASIS_DATABASE__URL=sqlite:///./data/basis_strategy_v1.db

# Redis Configuration (consolidated)
BASIS_REDIS__ENABLED=true
BASIS_REDIS__URL=redis://localhost:6379/0
BASIS_REDIS__SESSION_TTL=3600
BASIS_REDIS__CACHE_TTL=300

# dev Settings
BASIS_DEBUG=true
BASIS_MONITORING__LOG_LEVEL=DEBUG
```

#### **2. Testnet Configuration (consolidated)**
```bash
# Single testnet control
BASIS_TESTNET__ENABLED=true
BASIS_TESTNET__NETWORK=sepolia
BASIS_TESTNET__FAUCET_URL=https://sepoliafaucet.com/
BASIS_TESTNET__MAX_GAS_PRICE_GWEI=20
BASIS_TESTNET__CONFIRMATION_BLOCKS=2

# All services inherit testnet setting
BASIS_CEX__TESTNET=true  # Controls all CEX APIs
BASIS_WEB3__NETWORK=sepolia
BASIS_INSTADAPP__TESTNET=true
```

#### **3. API Keys (consolidated)**
```bash
# Data Provider APIs
BASIS_APIS__COINGECKO_KEY=CG-3qHwRgju7B2y43a1CxwYpY4q
BASIS_APIS__TARDIS_KEY=TD.l6pTDHIcc9fwJZEz.Y7cp7lBSu-pkPEv...
BASIS_APIS__ALCHEMY_KEY=vV3z-UCRtQvWb26MH9v7A
BASIS_APIS__AAVESCAN_KEY=c2b49a72-9c73-48f9-aea2-5f6d8ec793b9

# CEX APIs
BASIS_CEX__BINANCE_SPOT_KEY=...
BASIS_CEX__BINANCE_SPOT_SECRET=...
BASIS_CEX__BINANCE_FUTURES_KEY=...
BASIS_CEX__BINANCE_FUTURES_SECRET=...
BASIS_CEX__BYBIT_KEY=...
BASIS_CEX__BYBIT_SECRET=...
BASIS_CEX__OKX_KEY=...
BASIS_CEX__OKX_SECRET=...
BASIS_CEX__OKX_PASSPHRASE=...

# Web3 Configuration
BASIS_WEB3__PRIVATE_KEY=your_wallet_private_key
BASIS_WEB3__WALLET_ADDRESS=0x...
BASIS_WEB3__MAINNET_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/...
BASIS_WEB3__SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/...

# Instadapp (optional)
BASIS_INSTADAPP__API_KEY=...
BASIS_INSTADAPP__API_SECRET=...
```

#### **4. Live Testing Configuration**
```bash
# Safety controls
BASIS_LIVE_TESTING__ENABLED=false
BASIS_LIVE_TESTING__READ_ONLY=true
BASIS_LIVE_TESTING__MAX_TRADE_SIZE_USD=100
BASIS_LIVE_TESTING__REQUIRE_CONFIRMATION=true
```

### **Implementation Actions**

#### **Immediate**:
1. **Consolidate Redis configuration** - Remove `BASIS_CACHE__REDIS_URL`
2. **Consolidate Alchemy configuration** - Use single API key
3. **Add missing GCS variables** for deployment
4. **Add security validation** for sensitive variables

#### **Code Changes Required**:
1. **Update settings.py** to handle consolidated configuration
2. **Update CEX Execution Manager** to use consolidated testnet flag
3. **Update OnChain Execution Manager** to construct RPC URLs
4. **Add environment validation** to all components

---

## 🛡️ **Security**

### **Sensitive Variables** (Never commit to git)
- `BASIS_CEX__*_API_KEY` - All CEX API keys
- `BASIS_CEX__*_SECRET` - All CEX API secrets
- `BASIS_WEB3__PRIVATE_KEY` - Wallet private key
- `BASIS_INSTADAPP__API_SECRET` - Instadapp secret

### **Safe Variables** (Can be committed)
- `BASIS_API__PORT` - Server port
- `BASIS_DEBUG` - Debug flag
- `BASIS_TESTNET__*` - Testnet configuration
- `BASIS_DOWNLOADERS__*_RATE_LIMIT` - Rate limits

### **Security Validation Function**
```python
def validate_environment_security():
    """Validate environment variable security."""
    sensitive_patterns = [
        'BASIS_CEX__.*_KEY',
        'BASIS_CEX__.*_SECRET', 
        'BASIS_WEB3__PRIVATE_KEY',
        'BASIS_INSTADAPP__API_SECRET'
    ]
    
    for pattern in sensitive_patterns:
        for key, value in os.environ.items():
            if re.match(pattern, key):
                if value.startswith('your_') or value == '0x...':
                    raise ValueError(f"Sensitive variable {key} has placeholder value")
                if len(value) < 10:
                    raise ValueError(f"Sensitive variable {key} value too short")
```

---

## ✅ **Validation**

### **Required for Backtest Mode**
```python
REQUIRED_BACKTEST_VARS = [
    'BASIS_DATA__DATA_DIR',
    'BASIS_REDIS__ENABLED',
    'BASIS_DEBUG'
]
```

### **Required for Live Testing**
```python
REQUIRED_LIVE_VARS = [
    'BASIS_CEX__BINANCE_SPOT_API_KEY',
    'BASIS_CEX__BINANCE_SPOT_SECRET',
    'BASIS_CEX__BINANCE_FUTURES_API_KEY', 
    'BASIS_CEX__BINANCE_FUTURES_SECRET',
    'BASIS_CEX__BYBIT_API_KEY',
    'BASIS_CEX__BYBIT_SECRET',
    'BASIS_CEX__OKX_API_KEY',
    'BASIS_CEX__OKX_SECRET',
    'BASIS_CEX__OKX_PASSPHRASE',
    'BASIS_WEB3__PRIVATE_KEY',
    'BASIS_WEB3__WALLET_ADDRESS'
]
```

### **Validation Function**
```python
def validate_environment_variables(mode='backtest'):
    """Validate required environment variables for given mode."""
    if mode == 'backtest':
        required_vars = REQUIRED_BACKTEST_VARS
    elif mode == 'live':
        required_vars = REQUIRED_LIVE_VARS
    else:
        raise ValueError(f"Invalid mode: {mode}")
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_') or value == '0x...':
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing or placeholder values for: {missing_vars}")
    
    return True
```

### **Validation Checklist**

#### **Before Live Testing**:
- [ ] All CEX API keys configured (not placeholder values)
- [ ] Web3 private key configured (not placeholder values)
- [ ] Testnet configuration enabled
- [ ] Live testing disabled initially
- [ ] Read-only mode enabled initially
- [ ] Maximum trade size set to small amount

#### **Before Production Deployment**:
- [ ] All sensitive variables secured
- [ ] GCS configuration added
- [ ] Monitoring configuration added
- [ ] Security validation implemented
- [ ] Environment variable documentation updated

---

## 📝 **Usage Examples**

### **Loading Configuration in Components**
```python
from basis_strategy_v1.infrastructure.config.settings import get_settings

class MyComponent:
    def __init__(self):
        self.settings = get_settings()
        self.api_port = self.settings['api']['port']
        self.debug_mode = self.settings['debug']
```

### **Environment-Specific Configuration**
```python
# dev
BASIS_DEBUG=true
BASIS_API__PORT=8001
BASIS_TESTNET__ENABLED=true

# Production  
BASIS_DEBUG=false
BASIS_API__PORT=80
BASIS_TESTNET__ENABLED=false
```

---

This consolidated guide provides complete visibility into environment variables usage, redundancy analysis, and best practices.

**For configuration workflow**: See [CONFIG_WORKFLOW.md](CONFIG_WORKFLOW.md)  
**For deployment setup**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

*Last Updated: October 3, 2025*




