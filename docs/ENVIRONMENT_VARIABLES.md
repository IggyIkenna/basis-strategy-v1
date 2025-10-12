# Environment Variables - Complete Reference 🔧

**Purpose**: Complete mapping, usage, and validation for all environment variables  
**Status**: Comprehensive environment variable reference  
**Updated**: January 6, 2025 - Streamlined to focus on environment variables only  
**Last Reviewed**: January 6, 2025  
**Status**: ✅ Aligned with canonical architectural principles

---

## 📋 **Table of Contents**

1. [Overview](#-overview)
2. [Environment Variables by Category](#-environment-variables-by-category)
3. [Usage Analysis](#-usage-analysis)
4. [Environment Variable Validation](#-environment-variable-validation)
5. [Security](#-security)
6. [Validation](#-validation)
7. [Usage Examples](#-usage-examples)

---

## 📋 **Overview**

### **Configuration Loading Priority**
1. **Environment Variables** (BASIS_*) - Highest priority
2. **YAML Configuration Files** (configs/modes/, venues/, share_classes/) - Strategy and venue configs

**Core Configuration**: Environment variables control system startup, execution mode, and environment-specific credential routing.

### **Environment File Switching**

The platform supports multiple environment configurations through override files:

**Environment Files**:
- **`.env.dev`** - Development environment (5s health checks, debug logging)
- **`.env.staging`** - Staging environment (35s health checks, info logging)
- **`.env.production`** - Production environment (configurable intervals, production logging)

**Switching Methods**:

**Method 1: Environment Variable Prefix (Recommended)**:
```bash
# Use development environment (default)
./platform.sh backtest

# Use staging environment
BASIS_ENVIRONMENT=staging ./platform.sh backtest

# Use production environment
BASIS_ENVIRONMENT=prod ./platform.sh backtest
```

**Method 2: Export for Session**:
```bash
# Set environment for current shell session
export BASIS_ENVIRONMENT=staging

# Now all platform.sh commands use staging
./platform.sh backtest
./platform.sh start
./platform.sh stop
```

**Method 3: Built-in Environment Switcher**:
```bash
# Use platform.sh's built-in environment switcher
./platform.sh env dev     # Sets BASIS_ENVIRONMENT=dev
./platform.sh env prod    # Sets BASIS_ENVIRONMENT=prod

# Then run normally
./platform.sh backtest
```

**Environment File Loading Order**:
1. Load `env.unified` (base configuration with empty values)
2. Check `BASIS_ENVIRONMENT` variable
3. Load corresponding override file (`.env.dev`, `.env.staging`, `.env.production`)
4. Export variables to child processes (health monitor, etc.)

### **Fundamental Environment Variables**
| Variable | Values | Component | Purpose |
|----------|--------|-----------|---------|
| `BASIS_DEPLOYMENT_MODE` | local, docker | All components | Controls port/host forwarding and dependency injection |
| `BASIS_ENVIRONMENT` | dev, staging, production | All components | Controls venue credential routing (dev/staging/prod) and data sources (CSV vs DB) |
| `BASIS_EXECUTION_MODE` | backtest, live | All components | Controls venue execution behavior (simulated vs real) |
| `BASIS_DATA_MODE` | csv, db | Data Provider | Controls data source for backtest mode (file-based vs database) |

**Critical Distinction**:
- **BASIS_DEPLOYMENT_MODE**: Controls port/host forwarding and dependency injection (local vs docker)
- **BASIS_ENVIRONMENT**: Controls venue credential routing (dev/staging/prod) AND deployment infrastructure (hosts, ports, API endpoints)
- **BASIS_EXECUTION_MODE**: Controls venue execution behavior (simulated vs real)
- **BASIS_DATA_MODE**: Controls data source for backtest mode (file-based vs database) - NOT related to data persistence or execution routing

**Important**: BASIS_DATA_MODE can be set to csv or db independently of BASIS_ENVIRONMENT. For example, dev environment can use db, prod can use csv - they are orthogonal concerns.

**Backtest Mode**:
- Execution interfaces exist for CODE ALIGNMENT only
- NO real API credentials needed - NO heartbeat tests - NO real API calls
- Data source controlled by `BASIS_DATA_MODE` (csv for file-based, db for database - not implemented)
- Venues are simulated based on data loaded by data provider
- Hourly events (on the hour: 00:00, 01:00, etc.)
- Position tracking via execution manager updates
- All timestamps must be hourly-aligned
- Data loaded on-demand during API calls, not at startup
- **Reference**: `docs/MODES.md` - Execution Architecture section

**Live Mode**:
- Venues use real APIs (testnet for dev, mainnet for prod)
- Real execution via CCXT/Web3 with heartbeat tests
- Uses real-time WebSocket/API data via LiveDataProvider
- **Reference**: `docs/MODES.md` - Execution Architecture section
- Continuous events (any timestamp)
- Position tracking via queries + updates

### **Environment-Specific Credential Routing**

**CRITICAL**: All venue credentials are environment-specific and stored in `env.unified`:

**SEPARATION OF CONCERNS**:
- **BASIS_DEPLOYMENT_MODE**: Controls port/host forwarding and dependency injection (local vs docker)
- **BASIS_ENVIRONMENT**: Controls venue credential routing (dev/staging/prod) and data sources (CSV vs DB)
- **BASIS_EXECUTION_MODE**: Controls venue execution behavior (backtest simulation vs live execution)

**Environment-Specific Credential Pattern**:
```bash
# Development Environment - Testnet APIs
BASIS_DEV__ALCHEMY__PRIVATE_KEY=
BASIS_DEV__ALCHEMY__RPC_URL=
BASIS_DEV__ALCHEMY__WALLET_ADDRESS=
BASIS_DEV__ALCHEMY__NETWORK=sepolia
BASIS_DEV__ALCHEMY__CHAIN_ID=11155111

BASIS_DEV__CEX__BINANCE_SPOT_API_KEY=
BASIS_DEV__CEX__BINANCE_SPOT_SECRET=
BASIS_DEV__CEX__BINANCE_FUTURES_API_KEY=
BASIS_DEV__CEX__BINANCE_FUTURES_SECRET=

# Production Environment - Mainnet APIs
BASIS_PROD__ALCHEMY__PRIVATE_KEY=
BASIS_PROD__ALCHEMY__RPC_URL=
BASIS_PROD__ALCHEMY__WALLET_ADDRESS=
BASIS_PROD__ALCHEMY__NETWORK=mainnet
BASIS_PROD__ALCHEMY__CHAIN_ID=1

BASIS_PROD__CEX__BINANCE_SPOT_API_KEY=
BASIS_PROD__CEX__BINANCE_SPOT_SECRET=
BASIS_PROD__CEX__BINANCE_FUTURES_API_KEY=
BASIS_PROD__CEX__BINANCE_FUTURES_SECRET=

# ML Inference API (for ML strategies)
BASIS_ML_API_TOKEN=
```

**Reference**: `docs/DEPLOYMENT_GUIDE.md` - Unified Environment Configuration section
**Reference**: `docs/VENUE_ARCHITECTURE.md` - Environment Variables section

### **Venue Architecture Integration**

**Environment variables integrate with the venue architecture through**:

#### **Venue Client Initialization**
- **Environment-Specific Credentials**: All venue credentials are environment-specific (dev/staging/prod)
- **Venue Selection Logic**: Each strategy mode requires specific venues (CEX, DeFi, Infrastructure)
- **Client Factory Pattern**: Venue clients are created via execution interface factory
- **Reference**: `docs/VENUE_ARCHITECTURE.md` - Execution Interface Factory section

#### **Strategy Mode Venue Requirements**
Each strategy mode has specific venue requirements based on its configuration:
- **Pure Lending**: AAVE V3 + Alchemy only
- **BTC Basis**: Binance, Bybit, OKX + Alchemy
- **ETH Basis**: Binance, Bybit, OKX + Alchemy  
- **ETH Staking Only**: Lido/EtherFi + Alchemy
- **ETH Leveraged**: Lido/EtherFi, AAVE V3, Morpho + Alchemy, Instadapp
- **USDT Market Neutral No Leverage**: Binance, Bybit, OKX, Lido/EtherFi + Alchemy
- **USDT Market Neutral**: Binance, Bybit, OKX, Lido/EtherFi, AAVE V3, Morpho + Alchemy, Instadapp

**Reference**: `docs/MODES.md` - Strategy Mode Specifications section
**Reference**: `docs/VENUE_ARCHITECTURE.md` - Strategy-Venue Mapping section

### **Configuration Separation of Concerns**

**YAML Configuration Files** (IMPLEMENTED):
- **Modes** (`configs/modes/*.yaml`): Strategy-specific parameters
- **Venues** (`configs/venues/*.yaml`): Venue-specific configurations  
- **Share Classes** (`configs/share_classes/*.yaml`): Share class definitions




### **Naming Convention**
- **Prefix**: `BASIS_` (all environment variables)
- **Nesting**: Double underscore `__` for nested configuration
- **Example**: `BASIS_API__PORT` → `config['api']['port']`

### **Total Environment Variables**: 68 variables across 7 categories

---

## 🔧 **Environment Variables by Category**

### **1. Core Startup Configuration (REQUIRED)**
| Variable | Usage | Component | Purpose |
|----------|-------|-----------|---------|
| `BASIS_ENVIRONMENT` | Environment type | All components | Controls credential routing (dev/staging/prod) and data sources |
| `BASIS_DEPLOYMENT_MODE` | Deployment type | All components | Controls port/host forwarding and dependency injection |
| `BASIS_DEPLOYMENT_MACHINE` | Deployment target | All components | Controls deployment target (local_mac vs gcloud_linux_vm) |
| `BASIS_DATA_MODE` | Data mode | Data Provider | Controls data source (CSV vs DB) |
| `BASIS_DATA_DIR` | Data directory | Data Provider | Local vs cloud data storage |
| `BASIS_RESULTS_DIR` | Results directory | Results system | Where to store backtest results |
| `BASIS_DEBUG` | Debug mode | All components | Development vs production |
| `BASIS_LOG_LEVEL` | Logging verbosity | All components | Debug vs production logging |
| `BASIS_EXECUTION_MODE` | Execution mode | All components | Controls venue execution behavior (backtest vs live) |
| `BASIS_DATA_START_DATE` | Data start date | Data Provider | Historical data range start |



| `BASIS_DATA_END_DATE` | Data end date | Data Provider | Historical data range end |

**Critical**: These variables MUST be set in override files - no defaults in `env.unified`.

**Execution Mode Behavior**:
- **`./platform.sh start`** and **`./platform.sh backend`**: Use `BASIS_EXECUTION_MODE` from environment files
- **`./platform.sh backtest`**: **Always forces backtest mode** regardless of env file setting
- **Default env files**: `dev` and `staging` = backtest, `production` = live







### **2. Frontend Deployment Configuration (OPTIONAL if running backend only)**

| Variable | Usage | Component | Purpose |
|----------|-------|-----------|---------|
| `VITE_API_BASE_URL` | Frontend API base URL | Frontend | API endpoint for frontend calls |
| `APP_DOMAIN` | Domain for Caddy | Caddy | Domain configuration for reverse proxy |
| `ACME_EMAIL` | Let's Encrypt email | Caddy | Email for SSL certificate generation |
| `BASIC_AUTH_HASH` | Basic auth hash | Caddy | Authentication for protected endpoints |
| `HTTP_PORT` | HTTP port | Caddy | HTTP port configuration |
| `HTTPS_PORT` | HTTPS port | Caddy | HTTPS port configuration |

**Optional**: These variables are required for full-stack deployment but optional for backend-only mode. Missing variables generate warnings, not errors.

---

### **3. API Configuration**
| Variable | Usage | Component | Purpose |
|----------|-------|-----------|---------|
| `BASIS_API_PORT` | Backend server port | FastAPI server | API server port |
| `BASIS_API_HOST` | Backend server host | FastAPI server | API server host |
| `BASIS_API_CORS_ORIGINS` | CORS origins | FastAPI server | Frontend access control |
| `HEALTH_CHECK_INTERVAL` | Health check frequency | Docker + Monitor Script | How often to check backend health (e.g., "30s") |
| `HEALTH_CHECK_ENDPOINT` | Health check endpoint | Docker + Monitor Script | Which endpoint to ping: /health or /health/detailed |

---

### **4. Live Trading Configuration**
| Variable | Usage | Component | Purpose |
|----------|-------|-----------|---------|
| `BASIS_LIVE_TRADING__ENABLED` | Enable live trading | All execution managers | Safety switch (default: false) |
| `BASIS_LIVE_TRADING__READ_ONLY` | Read-only mode | All execution managers | Safe testing mode (default: true) |
| `BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD` | Maximum trade size | Execution managers | Risk management (default: 100) |
| `BASIS_LIVE_TRADING__EMERGENCY_STOP_LOSS_PCT` | Emergency stop loss | Risk management | Circuit breaker threshold (default: 0.15) |
| `BASIS_LIVE_TRADING__HEARTBEAT_TIMEOUT_SECONDS` | Heartbeat timeout | Monitoring | API connectivity timeout (default: 300) |
| `BASIS_LIVE_TRADING__CIRCUIT_BREAKER_ENABLED` | Circuit breaker | Risk management | Emergency stop system (default: true) |

**Note**: Only used when `BASIS_EXECUTION_MODE=live`.

---

### **5. Development Environment Credentials**
| Variable | Usage | Component | Purpose |
|----------|-------|-----------|---------|
| `BASIS_DEV__ALCHEMY__PRIVATE_KEY` | Wallet private key | OnChain Execution Manager | Testnet transaction signing |
| `BASIS_DEV__ALCHEMY__RPC_URL` | Testnet RPC endpoint | Web3 operations | Sepolia testnet access |
| `BASIS_DEV__ALCHEMY__WALLET_ADDRESS` | Wallet address | OnChain Execution Manager | Testnet transaction from address |
| `BASIS_DEV__ALCHEMY__NETWORK` | Testnet network | Web3 operations | Sepolia testnet (default: sepolia) |
| `BASIS_DEV__ALCHEMY__CHAIN_ID` | Testnet Chain ID | Web3 operations | Sepolia network validation (default: 11155111) |
| `BASIS_DEV__CEX__BINANCE_SPOT_API_KEY` | Binance spot API key | CEX Execution Manager | Testnet spot trading access |
| `BASIS_DEV__CEX__BINANCE_SPOT_SECRET` | Binance spot secret | CEX Execution Manager | Testnet spot trading authentication |
| `BASIS_DEV__CEX__BINANCE_FUTURES_API_KEY` | Binance futures API key | CEX Execution Manager | Testnet perpetual futures access |
| `BASIS_DEV__CEX__BINANCE_FUTURES_SECRET` | Binance futures secret | CEX Execution Manager | Testnet futures authentication |
| `BASIS_DEV__CEX__BYBIT_API_KEY` | Bybit API key | CEX Execution Manager | Testnet multi-exchange hedging |
| `BASIS_DEV__CEX__BYBIT_SECRET` | Bybit secret | CEX Execution Manager | Testnet Bybit authentication |
| `BASIS_DEV__CEX__OKX_API_KEY` | OKX API key | CEX Execution Manager | Testnet multi-exchange hedging |
| `BASIS_DEV__CEX__OKX_SECRET` | OKX secret | CEX Execution Manager | Testnet OKX authentication |
| `BASIS_DEV__CEX__OKX_PASSPHRASE` | OKX passphrase | CEX Execution Manager | Testnet OKX authentication |

**Environment**: Used when `BASIS_ENVIRONMENT=dev`.

---

### **6. Staging Environment Credentials**
| Variable | Usage | Component | Purpose |
|----------|-------|-----------|---------|
| `BASIS_STAGING__ALCHEMY__PRIVATE_KEY` | Wallet private key | OnChain Execution Manager | Mainnet transaction signing |
| `BASIS_STAGING__ALCHEMY__RPC_URL` | Mainnet RPC endpoint | Web3 operations | Ethereum mainnet access |
| `BASIS_STAGING__ALCHEMY__WALLET_ADDRESS` | Wallet address | OnChain Execution Manager | Mainnet transaction from address |
| `BASIS_STAGING__ALCHEMY__NETWORK` | Mainnet network | Web3 operations | Ethereum mainnet (default: mainnet) |
| `BASIS_STAGING__ALCHEMY__CHAIN_ID` | Mainnet Chain ID | Web3 operations | Ethereum network validation |
| `BASIS_STAGING__CEX__BINANCE_SPOT_API_KEY` | Binance spot API key | CEX Execution Manager | Mainnet spot trading access |
| `BASIS_STAGING__CEX__BINANCE_SPOT_SECRET` | Binance spot secret | CEX Execution Manager | Mainnet spot trading authentication |
| `BASIS_STAGING__CEX__BINANCE_FUTURES_API_KEY` | Binance futures API key | CEX Execution Manager | Mainnet perpetual futures access |
| `BASIS_STAGING__CEX__BINANCE_FUTURES_SECRET` | Binance futures secret | CEX Execution Manager | Mainnet futures authentication |
| `BASIS_STAGING__CEX__BYBIT_API_KEY` | Bybit API key | CEX Execution Manager | Mainnet multi-exchange hedging |
| `BASIS_STAGING__CEX__BYBIT_SECRET` | Bybit secret | CEX Execution Manager | Mainnet Bybit authentication |
| `BASIS_STAGING__CEX__OKX_API_KEY` | OKX API key | CEX Execution Manager | Mainnet multi-exchange hedging |
| `BASIS_STAGING__CEX__OKX_SECRET` | OKX secret | CEX Execution Manager | Mainnet OKX authentication |
| `BASIS_STAGING__CEX__OKX_PASSPHRASE` | OKX passphrase | CEX Execution Manager | Mainnet OKX authentication |

**Environment**: Used when `BASIS_ENVIRONMENT=staging`.

---

### **7. Production Environment Credentials**
| Variable | Usage | Component | Purpose |
|----------|-------|-----------|---------|
| `BASIS_PROD__ALCHEMY__PRIVATE_KEY` | Wallet private key | OnChain Execution Manager | Mainnet transaction signing |
| `BASIS_PROD__ALCHEMY__RPC_URL` | Mainnet RPC endpoint | Web3 operations | Ethereum mainnet access |
| `BASIS_PROD__ALCHEMY__WALLET_ADDRESS` | Wallet address | OnChain Execution Manager | Mainnet transaction from address |
| `BASIS_PROD__ALCHEMY__NETWORK` | Mainnet network | Web3 operations | Ethereum mainnet (default: mainnet) |
| `BASIS_PROD__ALCHEMY__CHAIN_ID` | Mainnet Chain ID | Web3 operations | Ethereum network validation (default: 1) |
| `BASIS_PROD__CEX__BINANCE_SPOT_API_KEY` | Binance spot API key | CEX Execution Manager | Mainnet spot trading access |
| `BASIS_PROD__CEX__BINANCE_SPOT_SECRET` | Binance spot secret | CEX Execution Manager | Mainnet spot trading authentication |
| `BASIS_PROD__CEX__BINANCE_FUTURES_API_KEY` | Binance futures API key | CEX Execution Manager | Mainnet perpetual futures access |
| `BASIS_PROD__CEX__BINANCE_FUTURES_SECRET` | Binance futures secret | CEX Execution Manager | Mainnet futures authentication |
| `BASIS_PROD__CEX__BYBIT_API_KEY` | Bybit API key | CEX Execution Manager | Mainnet multi-exchange hedging |
| `BASIS_PROD__CEX__BYBIT_SECRET` | Bybit secret | CEX Execution Manager | Mainnet Bybit authentication |
| `BASIS_PROD__CEX__OKX_API_KEY` | OKX API key | CEX Execution Manager | Mainnet multi-exchange hedging |
| `BASIS_PROD__CEX__OKX_SECRET` | OKX secret | CEX Execution Manager | Mainnet OKX authentication |
| `BASIS_PROD__CEX__OKX_PASSPHRASE` | OKX passphrase | CEX Execution Manager | Mainnet OKX authentication |

**Environment**: Used when `BASIS_ENVIRONMENT=prod`.

---

### **7.5. ML Inference API**

| Variable | Usage | Component | Purpose |
|----------|-------|-----------|---------|
| `BASIS_ML_API_TOKEN` | ML API authentication token | ML Data Provider | Live ML prediction API access |

**Usage**: Required for ML strategies in live mode to fetch predictions from external ML inference API.

**Environment**: Used by ML strategies (`ml_btc_directional`, `ml_usdt_directional`) when `BASIS_EXECUTION_MODE=live`.

**Fallback**: If not set, ML strategies return neutral signals with warning logs.

---

### **8. Storage and Data Management**

| Variable | Usage | Component | Purpose |
|----------|-------|-----------|---------|
| `BASIS_STORAGE_TYPE` | Storage backend type | Storage Infrastructure | Storage backend selection (default: filesystem) |

**Storage Types**:
- **filesystem**: Local file system storage (default)
- **s3**: AWS S3 storage (future implementation)
- **database**: Database storage (future implementation)

---

### **9. Live Data and Retry Configuration**

| Variable | Usage | Component | Purpose |
|----------|-------|-----------|---------|
| `BASIS_LIVE_DATA__MAX_RETRIES` | Maximum retry attempts | Live Data Provider | Retry limit for live data connections (default: 3) |

**Usage**: Controls retry behavior for live data provider when connecting to external APIs.

---

### **10. Authentication and Security**

| Variable | Usage | Component | Purpose |
|----------|-------|-----------|---------|
| `JWT_SECRET_KEY` | JWT signing secret | API Authentication | JWT token signing for API authentication |

**Security**: Required for JWT token generation and validation. Must be set to a secure random string in production.

---

### **11. Health Monitoring Configuration**
| Variable | Usage | Component | Purpose |
|----------|-------|-----------|---------|
| `HEALTH_CHECK_INTERVAL` | Health check frequency | Docker healthcheck + health monitor script | How often to check backend health (format: "30s", "1m", etc.) |
| `HEALTH_CHECK_ENDPOINT` | Health check endpoint | Docker healthcheck + health monitor script | Which endpoint to ping: /health (fast) or /health/detailed (comprehensive) |

**Health Monitoring Behavior**:
- **Docker Deployments**: Native Docker healthcheck pings endpoint at interval, restarts container on failure
- **Non-Docker Deployments**: Background monitor script pings endpoint at interval, runs `platform.sh restart` on failure
- **Restart Behavior**: Restarts all services (backend + frontend) for both backtest and live modes
- **Retry Logic**: Up to 3 restart attempts with exponential backoff before giving up
- **Default Values**: `HEALTH_CHECK_INTERVAL=30s`, `HEALTH_CHECK_ENDPOINT=/health`

---

### **12. Component-Specific Configuration**
| Variable | Usage | Component | Purpose |
|----------|-------|-----------|---------|
| `DATA_LOAD_TIMEOUT` | Data loading timeout (seconds) | Data Provider | Max time for data loading (default: 300) |
| `DATA_VALIDATION_STRICT` | Strict validation mode | Data Provider | Enable strict data validation (default: true) |
| `DATA_CACHE_SIZE` | Cache size (MB) | Data Provider | Data cache memory limit (default: 1000) |
| `STRATEGY_MANAGER_TIMEOUT` | Action timeout (seconds) | Strategy Manager | Max time for strategy actions (default: 30) |
| `STRATEGY_MANAGER_MAX_RETRIES` | Max retry attempts | Strategy Manager | Retry limit for failed actions (default: 3) |
| `STRATEGY_FACTORY_TIMEOUT` | Creation timeout (seconds) | Strategy Factory | Max time for strategy creation (default: 30) |
| `STRATEGY_FACTORY_MAX_RETRIES` | Max retry attempts | Strategy Factory | Retry limit for factory operations (default: 3) |

**Component-Specific Behavior**:
- **Data Provider**: Controls data loading performance and validation strictness
- **Strategy Manager**: Controls action execution timeouts and retry behavior
- **Strategy Factory**: Controls strategy creation timeouts and retry behavior

**Default Values**: All component-specific variables have sensible defaults and are optional for basic operation.

---

## 📊 **Usage Analysis**

### **Usage Mapping by Component**

#### **1. Core System** (11 variables)
- **Purpose**: System startup and basic configuration
- **Usage**: Environment detection, data paths, execution mode
- **Critical**: All required for system startup
- **Variables**: `BASIS_ENVIRONMENT`, `BASIS_DEPLOYMENT_MODE`, `BASIS_DATA_DIR`, etc.

#### **2. Frontend Deployment** (6 variables)
- **Purpose**: Frontend and Caddy configuration
- **Usage**: API endpoints, domain configuration, SSL certificates
- **Optional**: Required for full-stack deployment only
- **Variables**: `VITE_API_BASE_URL`, `APP_DOMAIN`, `ACME_EMAIL`, etc.

#### **3. API Configuration** (3 variables)
- **Purpose**: FastAPI server configuration
- **Usage**: Server ports, hosts, CORS settings
- **Critical**: Required for API server startup
- **Variables**: `BASIS_API_PORT`, `BASIS_API_HOST`, `BASIS_API_CORS_ORIGINS`

#### **4. Live Trading** (6 variables)
- **Purpose**: Live trading safety and risk management
- **Usage**: Circuit breakers, trade limits, monitoring
- **Critical**: Required for live trading mode
- **Variables**: `BASIS_LIVE_TRADING__*` variables

#### **5. Environment-Specific Credentials** (42 variables)
- **Purpose**: API keys and credentials for different environments
- **Usage**: CEX trading, Web3 operations, wallet management
- **Critical**: Required for live trading execution
- **Variables**: `BASIS_DEV__*`, `BASIS_STAGING__*`, `BASIS_PROD__*` credentials

---

## 🔍 **Environment Variable Validation**

### **Required Variables by Mode**

#### **Required for Backtest Mode**
```python
REQUIRED_BACKTEST_VARS = [
    'BASIS_EXECUTION_MODE',  # Must be 'backtest'
    'BASIS_ENVIRONMENT',     # Controls data source (CSV vs DB)
    'BASIS_DEPLOYMENT_MODE', # Controls deployment mode (local vs docker)
    'BASIS_DATA_MODE', # Controls data source (CSV vs DB)
    'BASIS_DATA_DIR',
    'BASIS_RESULTS_DIR',
    'BASIS_DEBUG',
    'BASIS_LOG_LEVEL',
    'BASIS_DATA_START_DATE',
    'BASIS_DATA_END_DATE'
]
```

**CRITICAL**: Backtest mode requires NO venue credentials - execution interfaces exist for CODE ALIGNMENT only.

**Backtest Mode Credential Exemption**:
- Execution is simulated using historical data
- No real API calls to CEX or DeFi protocols
- No heartbeat tests or connectivity validation
- Venue credentials are loaded but not validated
- System will start successfully without any venue credentials

#### **Required for Live Testing**
```python
REQUIRED_LIVE_VARS = [
    'BASIS_EXECUTION_MODE',  # Must be 'live'
    'BASIS_ENVIRONMENT',     # Controls credential routing (dev/staging/prod)
    'BASIS_DEPLOYMENT_MODE', # Controls deployment mode (local vs docker)
    # Environment-specific credentials based on BASIS_ENVIRONMENT
    'BASIS_DEV__CEX__BINANCE_SPOT_API_KEY',    # If BASIS_ENVIRONMENT=dev
    'BASIS_DEV__CEX__BINANCE_SPOT_SECRET',     # If BASIS_ENVIRONMENT=dev
    'BASIS_DEV__ALCHEMY__PRIVATE_KEY',         # If BASIS_ENVIRONMENT=dev
    'BASIS_DEV__ALCHEMY__WALLET_ADDRESS',      # If BASIS_ENVIRONMENT=dev
    # ... (similar for staging and prod environments)
]
```

### **Environment-Specific Credential Requirements**

#### **Development Environment** (`BASIS_ENVIRONMENT=dev`)
- All `BASIS_DEV__*` credentials must be set
- Uses testnet APIs and Sepolia network
- Default values: `BASIS_DEV__ALCHEMY__NETWORK=sepolia`, `BASIS_DEV__ALCHEMY__CHAIN_ID=11155111`

#### **Staging Environment** (`BASIS_ENVIRONMENT=staging`)
- All `BASIS_STAGING__*` credentials must be set
- Uses mainnet APIs with staging wallet
- Default values: `BASIS_STAGING__ALCHEMY__NETWORK=mainnet`

#### **Production Environment** (`BASIS_ENVIRONMENT=prod`)
- All `BASIS_PROD__*` credentials must be set
- Uses mainnet APIs with production wallet
- Default values: `BASIS_PROD__ALCHEMY__NETWORK=mainnet`, `BASIS_PROD__ALCHEMY__CHAIN_ID=1`

### **Live Trading Safety Configuration**

#### **Safety Checklist for Live Trading**:
- [ ] `BASIS_LIVE_TRADING__ENABLED=true` (explicitly set)
- [ ] `BASIS_LIVE_TRADING__READ_ONLY=false` (for real trading)
- [ ] `BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD` set to appropriate limit
- [ ] `BASIS_LIVE_TRADING__EMERGENCY_STOP_LOSS_PCT` configured
- [ ] `BASIS_LIVE_TRADING__CIRCUIT_BREAKER_ENABLED=true`
- [ ] All environment-specific credentials configured
- [ ] Live testing disabled initially
- [ ] Read-only mode enabled initially
- [ ] Maximum trade size set to small amount

#### **Before Production Environment**:
- [ ] All sensitive variables secured
- [ ] Environment variable documentation updated
- [ ] Centralized utility manager configuration validated

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
    'BASIS_DEBUG',
    'BASIS_EXECUTION_MODE',  # Must be 'backtest'
    'BASIS_ENVIRONMENT',     # Controls data source (CSV vs DB)
    'BASIS_DEPLOYMENT_MODE'  # Controls deployment mode (local vs docker)
]
```

**CRITICAL**: Backtest mode requires NO venue credentials - execution interfaces exist for CODE ALIGNMENT only.

### **Required for Live Testing**
```python
REQUIRED_LIVE_VARS = [
    'BASIS_EXECUTION_MODE',  # Must be 'live'
    'BASIS_ENVIRONMENT',     # Controls credential routing (dev/staging/prod)
    'BASIS_DEPLOYMENT_MODE', # Controls deployment mode (local vs docker)
    # Environment-specific credentials based on BASIS_ENVIRONMENT
    'BASIS_DEV__CEX__BINANCE_SPOT_API_KEY',    # If BASIS_ENVIRONMENT=dev
    'BASIS_DEV__CEX__BINANCE_SPOT_SECRET',     # If BASIS_ENVIRONMENT=dev
    'BASIS_DEV__ALCHEMY__PRIVATE_KEY',         # If BASIS_ENVIRONMENT=dev
    'BASIS_DEV__ALCHEMY__WALLET_ADDRESS',      # If BASIS_ENVIRONMENT=dev
    'BASIS_PROD__CEX__BINANCE_SPOT_API_KEY',   # If BASIS_ENVIRONMENT=prod
    'BASIS_PROD__CEX__BINANCE_SPOT_SECRET',    # If BASIS_ENVIRONMENT=prod
    'BASIS_PROD__ALCHEMY__PRIVATE_KEY',        # If BASIS_ENVIRONMENT=prod
    'BASIS_PROD__ALCHEMY__WALLET_ADDRESS'      # If BASIS_ENVIRONMENT=prod
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

### **Environment Variable Validation Requirements**

**Quality Gate Integration**: Environment variables are critical for quality gate validation:

#### **Backtest Mode Quality Gates**
- **Data Provider Initialization**: Environment variables control data source routing (CSV vs DB)
- **Configuration Loading**: Environment variables override YAML configuration
- **Component Health**: Environment variables determine component initialization mode


#### **Live Mode Quality Gates**
- **Venue API Health Checks**: Environment variables provide venue credentials for connectivity tests
- **Credential Validation**: Environment variables must contain valid, non-placeholder values
- **Network Connectivity**: Environment variables determine testnet vs mainnet endpoints


**Reference**: [docs/QUALITY_GATES.md](QUALITY_GATES.md) - Quality Gates System

### **Validation Checklist**

#### **Before Backtest Mode**:
- [ ] `BASIS_EXECUTION_MODE=backtest` set
- [ ] `BASIS_ENVIRONMENT` set (dev/staging/prod)
- [ ] `BASIS_DATA__DATA_DIR` points to valid data directory
- [ ] NO venue credentials required (backtest mode only)

#### **Before Live Testing**:
- [ ] `BASIS_EXECUTION_MODE=live` set
- [ ] `BASIS_ENVIRONMENT` set (dev/staging/prod)
- [ ] Environment-specific CEX API keys configured (not placeholder values)
- [ ] Environment-specific Web3 private key configured (not placeholder values)
- [ ] Testnet configuration enabled for dev environment
- [ ] Live testing disabled initially
- [ ] Read-only mode enabled initially
- [ ] Maximum trade size set to small amount

#### **Before Production Environment**:
- [ ] All sensitive variables secured
- [ ] Monitoring configuration added
- [ ] Security validation implemented
- [ ] Environment variable documentation updated
- [ ] Centralized utility manager configuration validated

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

**For configuration workflow**: See [specs/19_CONFIGURATION.md](specs/19_CONFIGURATION.md)  
**For deployment setup**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

*Last Updated: October 3, 2025*




