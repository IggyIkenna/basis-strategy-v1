# Deployment Guide - Production & Environment Management 🚀

**Platform**: Non-Docker (dev/staging/prod) + Docker (dev/staging/prod)  
**Target**: Local development, staging, and production environments  
**Status**: ✅ Infrastructure configured, works with component architecture  
**Updated**: January 6, 2025

---

## 📚 **Related Documentation**

- **Getting Started** → [GETTING_STARTED.md](GETTING_STARTED.md) (basic setup)
- **Configuration** → [specs/CONFIGURATION.md](specs/CONFIGURATION.md) (environment setup)
- **Component Health** → [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) (health monitoring)
- **Environment Variables** → [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) (required vars)
- **Venue Architecture** → [VENUE_ARCHITECTURE.md](VENUE_ARCHITECTURE.md) (venue client initialization)
- **Strategy Modes** → [MODES.md](MODES.md) (strategy specifications)

---

## 🎯 **Deployment Options Overview**

### **Non-Docker Deployment** (Direct Python)
```bash
# From project root
pip install -r requirements.txt
./platform.sh backtest     # Backend only
./platform.sh start        # Backend + Frontend
./platform.sh stop         # Stop all services
```

**Environments**: dev, staging, production  
**Use Case**: Development, testing, simple deployments

### **Docker Deployment** (Containerized)
```bash
cd docker
./deploy.sh local backend start     # Local backend only
./deploy.sh prod all start          # Production full stack
./deploy.sh staging backend stop    # Stop staging backend
./deploy.sh local all status        # Check status
```

**Environments**: local, staging, prod  
**Use Case**: Production deployments, consistent environments

---

## 🏗️ **Architecture Overview**

### **Deployment Modes**

| **Mode** | **Command** | **Services** | **Use Case** |
|----------|-------------|--------------|--------------|
| **Non-Docker** | `./platform.sh` | Backend + Frontend (local) | Development, testing |
| **Docker** | `cd docker && ./deploy.sh` | Backend + Caddy | All environments |

### **Backend Startup Initialization Sequence**

The backend follows a specific initialization sequence when starting up:

#### **1. Environment Variable Loading**
```bash
# Load base environment from env.unified
source env.unified

# Load environment-specific overrides
# Non-Docker: .env.dev, .env.staging, .env.production
# Docker: docker/.env.dev, docker/.env.staging, docker/.env.prod
```

#### **2. Main() Entry Point Orchestration**
The `main()` function orchestrates startup with these steps:

1. **Initialize Metrics**: Set up monitoring and metrics collection
2. **Load Configuration**: 
   - Pick up YAML files from `configs/` (mounted by docker if using docker)
   - Load, merge and validate against schemas in `config_models.py`
   - Quality gates ensure only valid config exists in YAML files
   - Single config instance per deployment (no runtime updates)
3. **Initialize Data Provider**:
   - Load data sources (if BASIS_DATA_MODE=csv, load from CSV files in `data/` directory else if BASIS_DATA_MODE=db, load from database)
   - Validate data sources vs environment config
   - Route based on `BASIS_ENVIRONMENT` (dev/staging/prod)
   - Separate data loading vs external API heartbeat operations
4. **Run Basic Health Checks**: 
   - Initialize components in dependency order
   - Register components with unified health manager
   - Components report health status automatically
   - Fail fast if any component initialization fails

#### **3. Environment Variable Integration**
The system uses three distinct environment variables:

- **`BASIS_DEPLOYMENT_MODE`**: `local` vs `docker` (port/host forwarding and dependency injection)
- **`BASIS_ENVIRONMENT`**: `dev` vs `staging` vs `production` (controls venue credentials AND deployment infrastructure like hosts, ports, API endpoints)
- **`BASIS_DATA_MODE`**: `csv` vs `db` (data source: CSV vs DB)
- **`BASIS_EXECUTION_MODE`**: `backtest` vs `live` (venue execution: simulated in backtest vs real)

**Critical Distinction**:
- **Deployment Mode**: Controls how services are deployed (local vs containerized)
- **Environment**: Controls data sources and API endpoints (dev/staging/prod)
- **Execution Mode**: Controls venue behavior (simulated vs real execution)

#### **4. Main() Entry Point Orchestration Details**
The `main()` function orchestrates the complete startup sequence:

```python
def main():
    """Main entry point orchestration for backend startup."""
    
    # 1. Initialize metrics
    setup_metrics()
    
    # 2. Load configuration
    config_manager = get_config_manager()
    startup_mode = config_manager.get_startup_mode()
    
    # 3. Initialize data provider
    data_provider = get_data_provider()
    data_provider._validate_data_at_startup()
    
    # 4. Run basic health checks
    # - Initialize components in dependency order
    # - Register components with unified health manager
    # - Components report health status automatically
    # - Fail fast if any component fails
    
    # 5. Start FastAPI application
    app = create_application()
    return app
```

**Key Orchestration Principles**:
- **Fail Fast**: No fallbacks if missing environment variables or config validation fails
- **Single Instance**: One config instance and one data provider instance per deployment
- **Dependency Order**: Components initialized in proper dependency sequence
- **Health Monitoring**: All components registered with unified health manager for monitoring

### **Environment Configuration**

**Base Configuration**: `env.unified` (empty values, must be overridden)

**Override Files**:
- **Non-Docker**: `.env.dev`, `.env.staging`, `.env.production` (project root)
- **Docker**: `docker/.env.dev`, `docker/.env.staging`, `docker/.env.prod`

**Configuration Dimensions**:
- **Execution Mode**: `backtest` vs `live` (simulated vs real API calls)
- **Environment**: `dev` vs `staging` vs `production` (data source, API endpoints)
- **Deployment**: `local` vs `docker` (dependency injection, port forwarding)
- **Deployment Machine**: `local_mac` vs `gcloud_linux_vm` (deployment target)

---

## 🌐 **Frontend Deployment**

### **Frontend Environment Variables**

The frontend uses the same unified environment structure as the backend:

**Frontend-specific variables**:
- `VITE_API_BASE_URL`: API base URL for frontend API calls (default: `/api/v1`)
- `APP_DOMAIN`: Domain for Caddy configuration (e.g., `defi-project.odum-research.com`)
- `ACME_EMAIL`: Email for Let's Encrypt certificates
- `BASIC_AUTH_HASH`: Basic authentication hash for Caddy
- `HTTP_PORT`: HTTP port (default: 80)
- `HTTPS_PORT`: HTTPS port (default: 443)

**Frontend Environment Files**:
- `frontend/.env.dev`: Development frontend configuration
- `frontend/.env.staging`: Staging frontend configuration  
- `frontend/.env.production`: Production frontend configuration

### **Frontend Deployment Modes**

**Backend-Only Mode**:
```bash
# Platform.sh - backend only (uses env file BASIS_EXECUTION_MODE)
./platform.sh backend

# Platform.sh - force backtest mode (overrides env file)
./platform.sh backtest

# Docker - backend only
cd docker && ./deploy.sh backend
```

**Full-Stack Mode**:
```bash
# Platform.sh - full stack (uses env file BASIS_EXECUTION_MODE)
./platform.sh start

# Docker - full stack
cd docker && ./deploy.sh all
```

**Execution Mode Control**:
- **Environment Files**: Set `BASIS_EXECUTION_MODE=backtest` or `BASIS_EXECUTION_MODE=live` in `.env.*` files
- **Command Override**: `./platform.sh backtest` **always forces backtest mode** regardless of env file
- **Default Behavior**: `dev`/`staging` = backtest, `production` = live

### **Frontend Health Checks**

The deployment scripts automatically test frontend accessibility:
- **IP Test**: `http://localhost/` (always tested)
- **Domain Test**: `http://APP_DOMAIN/` (if not localhost)
- **Build Failure**: Deployment fails if frontend is not accessible

### **Caddy Configuration**

Caddy automatically generates configuration based on `APP_DOMAIN`:
- **localhost**: HTTP only, no TLS
- **External domain**: HTTP + HTTPS with Let's Encrypt

---

## 🚀 **Live Trading Deployment**

### **Strategy Selection**
Strategy modes are selected via API parameters, not environment variables:

```python
# Backtest Request
{
    "strategy_name": "usdt_pure_lending",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T00:00:00Z",
    "initial_capital": 100000,
    "share_class": "USDT"
}

# Live Trading Request  
{
    "strategy_name": "eth_leveraged_staking",
    "share_class": "ETH",
    "exchange": "bybit",
    "api_credentials": {
        "api_key": "your_api_key",
        "api_secret": "your_api_secret"
    }
}
```

**Available Strategies**: See `docs/MODES.md` for complete list of 7 strategy modes

### **Venue Client Initialization**
- **Environment-Specific Credentials**: All venue credentials are environment-specific (dev/staging/prod)
- **Venue Selection Logic**: Each strategy mode requires specific venues (CEX, DeFi, Infrastructure)
- **Client Factory Pattern**: Venue clients are created via execution interface factory
- **Reference**: See `docs/VENUE_ARCHITECTURE.md` for complete venue architecture

**Key Venue Categories**:
- **CEX Venues**: Binance, Bybit, OKX (spot + perpetual futures)
- **DeFi Venues**: AAVE V3, Lido, EtherFi, Morpho (smart contracts)
- **Infrastructure**: Alchemy, Uniswap, Instadapp (middleware)

### **Live Trading vs Backtest**

| **Aspect** | **Backtest Mode** | **Live Trading Mode** |
|------------|-------------------|----------------------|
| **Data Source** | Historical CSV files | Real-time APIs via LiveDataProvider |
| **Execution** | Simulated API calls | Real API calls to testnet/prod |
| **Risk Management** | Historical validation | Real-time circuit breakers |
| **Monitoring** | Basic metrics | Full observability |
| **Architecture** | Same component chain | Same component chain |

---

## 🏠 **Non-Docker Deployment**

### **Quick Start**
```bash
# From project root
./platform.sh start

# Access points
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8001
# - API Docs: http://localhost:8001/docs
```

### **Environment Setup**
**File**: `env.unified` + override files

**Local Development Override** (`.env.dev`):
```bash
# Core configuration
BASIS_ENVIRONMENT=dev
BASIS_DEPLOYMENT_MODE=local
BASIS_DATA_DIR=./data
BASIS_DATA_MODE=csv
BASIS_RESULTS_DIR=./results
BASIS_DEBUG=true
BASIS_LOG_LEVEL=DEBUG
BASIS_EXECUTION_MODE=backtest

# API Configuration
BASIS_API_PORT=8001
BASIS_API_HOST=0.0.0.0
BASIS_API_CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### **Commands**
```bash
./platform.sh start        # Start backend + frontend
./platform.sh backtest     # Start backend only (backtest mode)
./platform.sh stop         # Stop all services
./platform.sh restart      # Restart all services
./platform.sh status       # Show service status
./platform.sh logs backend # Show backend logs
```

---

## 🐳 **Docker Deployment**

### **Unified Deployment Script**
```bash
cd docker
./deploy.sh [ENVIRONMENT] [SERVICES] [ACTION]
```

**Parameters**:
- **ENVIRONMENT**: `local|staging|prod` (default: local)
- **SERVICES**: `backend|frontend|all` (default: all)
- **ACTION**: `start|stop|restart|status|logs` (default: start)

### **Examples**
```bash
# Start backend only in local environment
./deploy.sh local backend start

# Start full stack in production
./deploy.sh prod all start

# Stop staging backend
./deploy.sh staging backend stop

# Check status and view logs
./deploy.sh local all status
./deploy.sh prod backend logs
```

### **Environment Files**
**Docker Override Files**:
- `docker/.env.dev` - Local development
- `docker/.env.staging` - Staging environment  
- `docker/.env.prod` - Production environment

**Environment Switching**:
The `deploy.sh` script automatically switches environments by copying the appropriate override file to `.env` before deployment.

### **Services**
- **backend**: Backend API
- **frontend**: Backend + Caddy (reverse proxy)
- **all**: Backend + Caddy

### **Access Points**
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **Frontend**: http://localhost/ (via Caddy)
- **Health Check**: http://localhost:8001/health
- **Detailed Health**: http://localhost:8001/health/detailed

---

## ☁️ **GCloud VM Deployment**

### **Prerequisites** ✅
- Domain: defi-project.odum-research.com
- VM: GCloud (europe-west1-b)
- TLS: Let's Encrypt (ikenna@odum-research.com)
- Static IP: Attached
- Firewall: TCP 22/80/443 open

### **Deployment Steps**

**1. Clone/Update Code**:
```bash
# On GCloud VM
cd ~/basis-strategy-v1
git pull origin main
```

**2. Configure Environment**:
```bash
cd docker
# Edit production environment file
vim .env.prod
```

**Production Configuration** (`docker/.env.prod`):
```bash
# Core configuration
BASIS_ENVIRONMENT=prod
BASIS_DEPLOYMENT_MODE=docker
BASIS_DATA_DIR=/app/data
BASIS_DATA_MODE=db
BASIS_RESULTS_DIR=/app/results
BASIS_DEBUG=false
BASIS_LOG_LEVEL=INFO
BASIS_EXECUTION_MODE=backtest  # Start with backtest, switch to live when ready

# Caddy Configuration
APP_DOMAIN=defi-project.odum-research.com
ACME_EMAIL=ikenna@odum-research.com
BASIC_AUTH_HASH=  # Set if needed
HTTP_PORT=80
HTTPS_PORT=443

# API Configuration
BASIS_API_PORT=8001
BASIS_API_HOST=0.0.0.0
```

**3. Deploy**:
```bash
./deploy.sh prod all start
```

**4. Verify**:
```bash
# Check containers
docker compose ps

# Check health
curl https://defi-project.odum-research.com/health
curl https://defi-project.odum-research.com/health/detailed

# Check API
curl https://defi-project.odum-research.com/api/v1/strategies/
```

---

## 🔧 **Environment Variables**

### **Base Configuration** (`env.unified`)
Contains empty values that must be overridden by environment-specific files:

```bash
# Core startup configuration (REQUIRED - no defaults)
BASIS_ENVIRONMENT=
BASIS_DEPLOYMENT_MODE=
BASIS_DATA_DIR=
BASIS_DATA_MODE=
BASIS_RESULTS_DIR=
BASIS_REDIS_URL=
BASIS_DEBUG=
BASIS_LOG_LEVEL=
BASIS_EXECUTION_MODE=
BASIS_DATA_START_DATE=
BASIS_DATA_END_DATE=

# API configuration
BASIS_API_PORT=
BASIS_API_HOST=
BASIS_API_CORS_ORIGINS=

# Live trading configuration (only used when BASIS_EXECUTION_MODE=live)
BASIS_LIVE_TRADING__ENABLED=false
BASIS_LIVE_TRADING__READ_ONLY=true
BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD=100
BASIS_LIVE_TRADING__EMERGENCY_STOP_LOSS_PCT=0.15
BASIS_LIVE_TRADING__HEARTBEAT_TIMEOUT_SECONDS=300
BASIS_LIVE_TRADING__CIRCUIT_BREAKER_ENABLED=true

# Environment-specific API keys (dev/staging/prod)
BASIS_DEV__ALCHEMY__PRIVATE_KEY=
BASIS_DEV__ALCHEMY__RPC_URL=
BASIS_DEV__ALCHEMY__WALLET_ADDRESS=
BASIS_DEV__ALCHEMY__NETWORK=sepolia
BASIS_DEV__ALCHEMY__CHAIN_ID=11155111
# ... (similar for staging and prod environments)
```

### **Environment-Specific Overrides**
Each environment file overrides the empty values in `env.unified`:

**Local Development** (`.env.dev` or `docker/.env.dev`):
```bash
BASIS_ENVIRONMENT=dev
BASIS_DEPLOYMENT_MODE=local  # or docker
BASIS_DATA_DIR=./data  # or /app/data for docker
BASIS_DATA_MODE=csv
  # or redis://redis:6379/0 for docker
BASIS_DEBUG=true
BASIS_LOG_LEVEL=DEBUG
BASIS_EXECUTION_MODE=backtest
```

**Production** (`.env.production` or `docker/.env.prod`):
```bash
BASIS_ENVIRONMENT=prod
BASIS_DEPLOYMENT_MODE=docker
BASIS_DATA_DIR=/app/data
BASIS_DATA_MODE=db
BASIS_DEBUG=false
BASIS_LOG_LEVEL=INFO
BASIS_EXECUTION_MODE=live  # When ready for live trading
```

---

## 🏦 **Wallet & API Setup**

### **Environment Overview**

| Environment | Network | CEX APIs | ERC-20 Wallet | Purpose |
|-------------|---------|----------|---------------|---------|
| **dev** | Sepolia Testnet | Testnet APIs | Testnet Wallet | Free testing, full E2E |
| **staging** | Mainnet | Mainnet APIs | Mainnet Wallet (Small) | Real money, small amounts |
| **production** | Mainnet | Mainnet APIs | Mainnet Wallet (Full) | Live trading, full amounts |

### **ERC-20 Wallet Setup**
**What is an ERC-20 Wallet?**
- Blockchain wallet (NOT a CEX wallet)
- Holds ETH and ERC-20 tokens (USDT, weETH, aTokens)
- Used for on-chain operations: AAVE, staking, flash loans, gas payments

**Creating Wallets** (Use MetaMask):
1. Install MetaMask browser extension
2. Create NEW wallet (separate for this project!)
3. Export private key (Account details → Export private key)
4. **Remove 0x prefix** when adding to env files
5. Copy wallet address (with 0x prefix)

**Funding by Environment**:
- **dev**: Get testnet ETH from https://sepoliafaucet.com/ (1-2 ETH, free)
- **staging**: Real ETH (0.1-0.5 ETH for testing)
- **production**: Real ETH (full amount for trading)

### **CEX API Setup**
**dev (Testnet APIs)**:
- **Binance**: https://testnet.binance.vision/
- **Bybit**: https://testnet.bybit.com/
- **OKX**: https://www.okx.com/developers/testnet

**Production (Mainnet APIs)**:
- Use separate API keys from testnet
- Set IP restrictions where possible
- Enable only required permissions
- Monitor API usage regularly

### **API Credentials in Live Trading**
The `api_credentials` field in `LiveTradingRequest` is a `Dict[str, str]` containing exchange-specific credentials:
```python
{
    "api_key": "your_api_key",
    "api_secret": "your_api_secret"
}
```

This is different from environment-based credentials in `env.unified` - it's for per-request API access.

---

## 🚨 **Troubleshooting**

### **Common Issues**


**Component Initialization Failed**:
```bash
# Check backend logs
docker compose logs backend

# Common issues:
# - Data not loaded → Check /app/data volume mount
# - Config missing → Check env variables
```

**Port Conflicts**:
```bash
# Check what's using ports
lsof -i :8001
lsof -i :5173

# Kill processes on ports
./platform.sh stop
```

---

## ✅ **Deployment Checklist**

**Before Deployment**:
- [ ] Push to main
- [ ] Configure environment files (`.env.dev`, `.env.prod`, etc.)
- [ ] Test locally with Docker
- [ ] Set proper permissions: `chmod 600 env.unified`

**After Deployment**:
- [ ] Check health endpoints (`/health` and `/health/detailed`)
- [ ] Test mode selection via UI
- [ ] Verify environment file is loaded
- [ ] Check logs for execution mode

**Environment File Security**:
- [ ] Never commit environment files to git
- [ ] Use single file with different settings for different deployments
- [ ] Rotate API keys regularly
- [ ] Set proper file permissions

---

## 📊 **Data Management**

### **GCS Upload Script** (Future)
```bash
# Upload data/ directory to GCS bucket
./scripts/deployment/upload_data_to_gcs.sh

# Download on VM
gsutil -m rsync -r gs://basis-strategy-v1-data/ data/
```

---

## 🎯 **Health Checks**

### **Fast Health Check**
**Endpoint**: `/health` (no authentication required)

**Returns**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-06T12:00:00Z",
  "service": "basis-strategy-v1",
  "execution_mode": "backtest",
  "uptime_seconds": 3600,
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "memory_available_gb": 8.5
  }
}
```

### **Comprehensive Health Check**
**Endpoint**: `/health/detailed` (no authentication required)

**Returns**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-06T12:00:00Z",
  "service": "basis-strategy-v1",
  "execution_mode": "backtest",
  "components": {
    "position_monitor": {
      "status": "healthy",
      "error_code": null,
      "readiness_checks": {
        "initialized": true,
      }
    },
    "data_provider": {
      "status": "healthy",
      "error_code": null,
      "readiness_checks": {
        "initialized": true,
        "data_loaded": true
      }
    }
  },
  "summary": {
    "total_components": 9,
    "healthy_components": 9,
    "unhealthy_components": 0
  }
}
```

---

## 🔧 **Component Architecture Notes**

### **Component Communication**
**Backtest Mode**: Direct function calls between components  
**Live Mode**: Direct function calls between components with tight loop reconciliation

---

## 🔄 **Automatic Health Monitoring and Restart**

### **Overview**
Both Docker and non-Docker deployments automatically monitor backend health and restart services on failure.

### **Configuration**
```bash
# In env.unified or override files
HEALTH_CHECK_INTERVAL=30s          # How often to check (30s recommended)
HEALTH_CHECK_ENDPOINT=/health      # Fast check (< 50ms)
# HEALTH_CHECK_ENDPOINT=/health/detailed  # Comprehensive check (slower)
```

### **How It Works**

**Docker Deployments**:
- Docker's native healthcheck pings `HEALTH_CHECK_ENDPOINT` every `HEALTH_CHECK_INTERVAL`
- On failure (10 consecutive failures with 3s timeout): Docker restarts backend container
- Logs visible via `docker compose logs backend`

**Non-Docker Deployments**:
- Background monitor script (`scripts/health_monitor.sh`) runs automatically when you start services
- Pings `HEALTH_CHECK_ENDPOINT` every `HEALTH_CHECK_INTERVAL`
- On failure: Restarts all services via `platform.sh restart` (backend + frontend)
- Retry logic: Up to 3 attempts with exponential backoff (5s, 10s, 20s)
- After 3 failures: Gives up and logs error
- Logs to `logs/health_monitor.log`

### **Starting/Stopping Monitor**

**Automatic** (recommended):
```bash
./platform.sh start      # Starts backend + frontend + health monitor
./platform.sh backtest   # Starts backend + health monitor
./platform.sh stop       # Stops all services including monitor
```

**Manual** (for debugging):
```bash
# Check if monitor is running
ps aux | grep health_monitor

# View monitor logs
tail -f logs/health_monitor.log

# Manually stop monitor
kill $(cat logs/health_monitor.pid)
```

### **Troubleshooting**

**Monitor not starting**:
- Check `HEALTH_CHECK_INTERVAL` is set in environment
- Verify `scripts/health_monitor.sh` is executable: `chmod +x scripts/health_monitor.sh`

**Services restarting frequently**:
- Check backend logs: `tail -f backend/logs/api.log`
- Backend may be genuinely unhealthy (component initialization issues)
- Consider increasing `HEALTH_CHECK_INTERVAL` or fixing root cause

**Monitor process stuck**:
- Stop services: `./platform.sh stop`
- Manually kill monitor: `kill $(cat logs/health_monitor.pid)` or `killall health_monitor.sh`
- Remove PID file: `rm logs/health_monitor.pid`
- Restart: `./platform.sh start`