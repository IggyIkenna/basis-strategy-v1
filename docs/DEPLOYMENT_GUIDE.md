 # Deployment Guide - Docker + GCloud 🚀

**Platform**: Docker containers + Caddy reverse proxy  
**Target**: GCloud VM (defi-project.odum-research.com)  
**Status**: ✅ Infrastructure already configured, works with new component architecture  
**Updated**: October 3, 2025

---

## 📚 **Related Documentation**

- **Configuration** → [CONFIG_WORKFLOW.md](CONFIG_WORKFLOW.md) (environment setup)
- **Component Health** → [COMPONENT_SPECS_INDEX.md](COMPONENT_SPECS_INDEX.md) (health monitoring)
- **Environment Variables** → [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) (required vars)

---

## 🎯 **Quick Reference**

**Local dev**:
```bash
cd deploy
./deploy.sh local     # Start backend + frontend
```

**Production Deployment**:
```bash
cd deploy
./deploy.sh prod      # Deploy to GCloud VM
```

**Data Upload** (NOT YET IMPLEMENTED):
```bash
# TODO: Create upload_data_to_gcs.sh script
# ./scripts/deployment/upload_data_to_gcs.sh    # Upload data/ to GCS
```

---

## 🚀 **Live Trading Deployment**

### **Configuration Structure**

**Deployment Configuration** (`deploy/.env*`):
- **Purpose**: Caddy-specific deployment variables only
- **Files**: `.env.local`, `.env.staging`, `.env.prod`
- **Active File**: `.env` (copied from environment-specific file by `switch-env.sh`)
- **Variables**: Domain names, TLS settings, port mappings, basic auth
- **Separation**: BASIS configuration is in `backend/env.unified`, not in deploy files
- **Switching**: Use `./switch-env.sh [local|staging|prod]` to switch environments

**Environment-Specific Configuration** (`configs/{dev,staging,production}.json`):
- **Purpose**: Environment-specific BASIS configuration overrides
- **Files**: `dev.json`, `staging.json`, `production.json`
- **Variables**: Database URLs, API ports, CORS origins, feature flags

### **Live Trading vs Backtest Deployment**

| **Aspect** | **Backtest Mode** | **Live Trading Mode** |
|------------|-------------------|----------------------|
| **Data Source** | Historical CSV files | Real-time APIs via LiveDataProvider |
| **Execution** | Simulated | Real blockchain/CEX |
| **Risk Management** | Historical validation | Real-time circuit breakers |
| **Monitoring** | Basic metrics | Full observability |
| **Deployment** | Standard containers | Production-grade setup |

### **Unified Environment Configuration**

#### **1. Single Environment File Approach**

**File**: `backend/env.unified` (one file for all configurations)

**Configuration Dimensions**:
- **Execution Mode**: `backtest` vs `live` (data source & API interaction)
- **Environment**: `dev` vs `production` (code branch & deployment)
- **Deployment**: `local` vs `cloud` (UI rendering & ports)

```bash
# =============================================================================
# UNIFIED ENVIRONMENT CONFIGURATION
# =============================================================================

# =============================================================================
# EXECUTION MODE (backtest vs live)
# =============================================================================
# backtest: Uses historical data, simulated execution
# live: Uses real-time data, real execution
BASIS_EXECUTION_MODE=backtest

# =============================================================================
# ENVIRONMENT (dev vs production)
# =============================================================================
# dev: Development branch, testnet credentials, debug logging
# production: Production branch, mainnet credentials, optimized logging
BASIS_ENVIRONMENT=dev

# =============================================================================
# DEPLOYMENT (local vs cloud)
# =============================================================================
# local: Local development, localhost ports, dev UI
# cloud: Cloud deployment, domain URLs, production UI
BASIS_DEPLOYMENT=local

# =============================================================================
# API CONFIGURATION (adjusts based on deployment)
# =============================================================================
BASIS_API__PORT=8001
BASIS_API__RELOAD=true  # false for production
BASIS_API__CORS_ORIGINS=["http://localhost:5173"]  # ["https://defi-project.odum-research.com"] for cloud

# =============================================================================
# DATA PROVIDER CONFIGURATION (adjusts based on execution mode)
# =============================================================================
BASIS_DATA__CACHE_ENABLED=true
BASIS_DATA__DATA_DIR=./data
BASIS_DATA_PROVIDER__MODE=backtest  # live for real-time data
BASIS_DATA_PROVIDER__REFRESH_INTERVAL_SECONDS=3600  # 30 for live
BASIS_DATA_PROVIDER__MAX_DATA_AGE_SECONDS=86400  # 60 for live

# =============================================================================
# LIVE TRADING CONFIGURATION (only used when BASIS_EXECUTION_MODE=live)
# =============================================================================
BASIS_LIVE_TRADING__ENABLED=false  # true for live trading
BASIS_LIVE_TRADING__READ_ONLY=true  # false for real trading
BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD=100  # 1000000 for production
BASIS_LIVE_TRADING__EMERGENCY_STOP_LOSS_PCT=0.15
BASIS_LIVE_TRADING__HEARTBEAT_TIMEOUT_SECONDS=300
BASIS_LIVE_TRADING__CIRCUIT_BREAKER_ENABLED=true

# =============================================================================
# RISK MANAGEMENT
# =============================================================================
BASIS_RISK__MODE=strict
BASIS_RISK__MAX_POSITION_SIZE_USD=100  # 1000000 for production
BASIS_RISK__DAILY_LOSS_LIMIT_PCT=0.15
BASIS_RISK__MARGIN_WARNING_THRESHOLD=0.20
BASIS_RISK__MARGIN_CRITICAL_THRESHOLD=0.10

# =============================================================================
# REDIS CONFIGURATION (adjusts based on deployment)
# =============================================================================
BASIS_REDIS__ENABLED=true
BASIS_REDIS__URL=redis://localhost:6379/0  # redis://redis:6379/0 for cloud
BASIS_REDIS__SESSION_TTL=3600
BASIS_REDIS__CACHE_TTL=300

# =============================================================================
# MONITORING AND LOGGING (adjusts based on environment)
# =============================================================================
BASIS_DEBUG=true  # false for production
BASIS_MONITORING__LOG_LEVEL=DEBUG  # INFO for production
BASIS_MONITORING__ENABLE_METRICS=true
BASIS_MONITORING__ENABLE_TRACING=true

# =============================================================================
# CEX API CREDENTIALS (adjusts based on environment)
# =============================================================================
# DEV ENVIRONMENT (Testnet APIs)
BASIS_DEV__CEX__BINANCE_SPOT_API_KEY=your_testnet_binance_spot_api_key
BASIS_DEV__CEX__BINANCE_SPOT_SECRET=your_testnet_binance_spot_secret
BASIS_DEV__CEX__BINANCE_FUTURES_API_KEY=your_testnet_binance_futures_api_key
BASIS_DEV__CEX__BINANCE_FUTURES_SECRET=your_testnet_binance_futures_secret
BASIS_DEV__CEX__BYBIT_API_KEY=your_testnet_bybit_api_key
BASIS_DEV__CEX__BYBIT_SECRET=your_testnet_bybit_secret
BASIS_DEV__CEX__OKX_API_KEY=your_testnet_okx_api_key
BASIS_DEV__CEX__OKX_SECRET=your_testnet_okx_secret
BASIS_DEV__CEX__OKX_PASSPHRASE=your_testnet_okx_passphrase

# PRODUCTION ENVIRONMENT (Mainnet APIs)
BASIS_PROD__CEX__BINANCE_SPOT_API_KEY=your_prod_binance_spot_api_key
BASIS_PROD__CEX__BINANCE_SPOT_SECRET=your_prod_binance_spot_secret
BASIS_PROD__CEX__BINANCE_FUTURES_API_KEY=your_prod_binance_futures_api_key
BASIS_PROD__CEX__BINANCE_FUTURES_SECRET=your_prod_binance_futures_secret
BASIS_PROD__CEX__BYBIT_API_KEY=your_prod_bybit_api_key
BASIS_PROD__CEX__BYBIT_SECRET=your_prod_bybit_secret
BASIS_PROD__CEX__OKX_API_KEY=your_prod_okx_api_key
BASIS_PROD__CEX__OKX_SECRET=your_prod_okx_secret
BASIS_PROD__CEX__OKX_PASSPHRASE=your_prod_okx_passphrase

# =============================================================================
# WALLET CONFIGURATION (adjusts based on environment)
# =============================================================================
# DEV ENVIRONMENT (Testnet Wallet)
BASIS_DEV__ALCHEMY__PRIVATE_KEY=your_testnet_erc20_wallet_private_key
BASIS_DEV__ALCHEMY__WALLET_ADDRESS=0x...
BASIS_DEV__ALCHEMY__RPC_URL=https://eth-sepolia.g.alchemy.com/v2/your_testnet_key
BASIS_DEV__ALCHEMY__NETWORK=sepolia
BASIS_DEV__ALCHEMY__CHAIN_ID=11155111

# PRODUCTION ENVIRONMENT (Mainnet Wallet)
BASIS_PROD__ALCHEMY__PRIVATE_KEY=your_prod_mainnet_erc20_wallet_private_key
BASIS_PROD__ALCHEMY__WALLET_ADDRESS=0x...
BASIS_PROD__ALCHEMY__RPC_URL=https://eth-mainnet.g.alchemy.com/v2/your_prod_key
BASIS_PROD__ALCHEMY__NETWORK=mainnet
BASIS_PROD__ALCHEMY__CHAIN_ID=1

# =============================================================================
# DATA PROVIDER API KEYS (shared across environments)
# =============================================================================
BASIS_DOWNLOADERS__COINGECKO_API_KEY=your_coingecko_key
BASIS_DOWNLOADERS__ALCHEMY_API_KEY=your_alchemy_key
BASIS_DOWNLOADERS__INFURA_API_KEY=your_infura_key

# =============================================================================
# INSTADAPP CONFIGURATION (adjusts based on environment)
# =============================================================================
BASIS_INSTADAPP__API_KEY=your_instadapp_api_key
BASIS_INSTADAPP__API_SECRET=your_instadapp_secret
BASIS_INSTADAPP__TESTNET=true  # false for production
```

**Configuration Matrix**:

| **Scenario** | **Execution Mode** | **Environment** | **Deployment** | **Key Settings** |
|--------------|-------------------|-----------------|----------------|------------------|
| **Local Dev** | `backtest` | `dev` | `local` | Testnet APIs, debug logging |
| **Local Live** | `live` | `dev` | `local` | Testnet APIs, read-only trading |
| **Cloud Prod Backtest** | `backtest` | `production` | `cloud` | Production APIs, optimized logging |
| **Cloud Prod Live** | `live` | `production` | `cloud` | Production APIs, real trading |

**Configuration Examples**:
```bash
# Local Development (backtest + dev + local)
BASIS_EXECUTION_MODE=backtest
BASIS_ENVIRONMENT=dev
BASIS_DEPLOYMENT=local

# Local Live Trading (live + dev + local)
BASIS_EXECUTION_MODE=live
BASIS_ENVIRONMENT=dev
BASIS_DEPLOYMENT=local
BASIS_LIVE_TRADING__ENABLED=true
BASIS_LIVE_TRADING__READ_ONLY=true

# Cloud Production Backtest (backtest + production + cloud)
BASIS_EXECUTION_MODE=backtest
BASIS_ENVIRONMENT=production
BASIS_DEPLOYMENT=cloud
BASIS_API__CORS_ORIGINS=["https://defi-project.odum-research.com"]
BASIS_REDIS__URL=redis://redis:6379/0

# Cloud Production Live Trading (live + production + cloud)
BASIS_EXECUTION_MODE=live
BASIS_ENVIRONMENT=production
BASIS_DEPLOYMENT=cloud
BASIS_LIVE_TRADING__ENABLED=true
BASIS_LIVE_TRADING__READ_ONLY=false
BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD=1000000
```

#### **2. Unified Docker Compose**
```yaml
# deploy/docker-compose.yml (works for all configurations)
services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped

  backend:
    build:
      context: ..
      dockerfile: deploy/Dockerfile.backend
    env_file:
      - ../backend/env.unified  # Backend configuration
      - .env                    # Caddy-specific configuration (CORS, etc.)
    depends_on:
      - redis
    volumes:
      - ../data:/app/data
      - ../results:/app/results
      - ../configs:/app/configs:ro
      - ../backend/env.unified:/app/env.unified:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health/"]
      interval: ${HEALTH_CHECK_INTERVAL:-30s}
      timeout: 3s
      retries: 10
    restart: unless-stopped

  caddy:
    build:
      context: ..
      dockerfile: deploy/Dockerfile.caddy-frontend
    env_file:
      - .env  # For Caddy-specific variables (domain, email, auth)
    environment:
      - APP_DOMAIN=${APP_DOMAIN:-localhost}
      - ACME_EMAIL=${ACME_EMAIL:-you@example.com}
      - BASIC_AUTH_HASH=${BASIC_AUTH_HASH:-}
    depends_on:
      - backend
    ports:
      - "${HTTP_PORT:-80}:80"
      - "${HTTPS_PORT:-443}:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    restart: unless-stopped

  # Frontend development service (optional - for testing)
  frontend-dev:
    build:
      context: ..
      dockerfile: deploy/Dockerfile.frontend-test
    ports:
      - "5173:5173"  # Vite dev server port
    volumes:
      - ../frontend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=dev
    command: ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
    stdin_open: true
    tty: true
    profiles:
      - frontend-test  # Only start with --profile frontend-test

volumes:
  caddy_data:
  caddy_config:
```

#### **3. Unified Deployment Script**
```bash
#!/bin/bash
# deploy/deploy.sh

set -e

echo "🚀 Deploying Basis Strategy System..."

# Check if environment file exists
if [ ! -f "../backend/env.unified" ]; then
    echo "❌ Error: backend/env.unified not found"
    echo "Please configure your environment file first"
    exit 1
fi

# Validate environment file
echo "🔍 Validating environment configuration..."
source ../backend/env.unified

# Check critical environment variables
required_vars=(
    "BASIS_EXECUTION_MODE"
    "BASIS_ENVIRONMENT"
    "BASIS_DEPLOYMENT"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set in backend/env.unified"
        exit 1
    fi
done

# Display configuration
echo "📋 Configuration:"
echo "   Execution Mode: $BASIS_EXECUTION_MODE"
echo "   Environment: $BASIS_ENVIRONMENT"
echo "   Deployment: $BASIS_DEPLOYMENT"

# Additional validation for live trading
if [ "$BASIS_EXECUTION_MODE" = "live" ]; then
    echo "🔍 Validating live trading configuration..."
    
    if [ "$BASIS_LIVE_TRADING__ENABLED" != "true" ]; then
        echo "❌ Error: BASIS_LIVE_TRADING__ENABLED must be 'true' for live trading"
        exit 1
    fi
    
    # Check for production credentials if in production environment
    if [ "$BASIS_ENVIRONMENT" = "production" ]; then
        prod_vars=(
            "BASIS_PROD__CEX__BINANCE_SPOT_API_KEY"
            "BASIS_PROD__ALCHEMY__PRIVATE_KEY"
        )
        
        for var in "${prod_vars[@]}"; do
            if [ -z "${!var}" ]; then
                echo "❌ Error: $var is not set for production live trading"
                exit 1
            fi
        done
    fi
fi

# Build and deploy
echo "📦 Building containers..."
docker-compose build

echo "🔄 Stopping existing containers..."
docker-compose down

echo "🚀 Starting system..."
docker-compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 30

# Health checks
echo "🔍 Running health checks..."
curl -f http://localhost:8001/health || {
    echo "❌ Backend health check failed"
    exit 1
}

curl -f http://localhost:5173 || {
    echo "❌ Frontend health check failed"
    exit 1
}

echo "✅ System deployed successfully!"
echo "🌐 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8001"
echo ""
echo "🔐 Environment: backend/env.unified"
echo "⚡ Execution Mode: $BASIS_EXECUTION_MODE"
echo "🌍 Environment: $BASIS_ENVIRONMENT"
echo "🚀 Deployment: $BASIS_DEPLOYMENT"

if [ "$BASIS_EXECUTION_MODE" = "live" ]; then
    echo "💰 Max Trade Size: $BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD USD"
    echo "🔒 Read Only: $BASIS_LIVE_TRADING__READ_ONLY"
fi
```

### **Live Trading Monitoring & Observability**

#### **1. Health Monitoring**
```python
# Live Trading Health Checks
class LiveTradingHealthMonitor:
    """Comprehensive health monitoring for live trading."""
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Check all system components."""
        return {
            'data_provider': await self.check_data_provider(),
            'execution_managers': await self.check_execution_managers(),
            'risk_monitor': await self.check_risk_monitor(),
            'wallet_connectivity': await self.check_wallet_connectivity(),
            'api_connectivity': await self.check_api_connectivity(),
            'market_data_freshness': await self.check_market_data_freshness(),
            'position_consistency': await self.check_position_consistency()
        }
    
    async def check_data_provider(self) -> Dict[str, Any]:
        """Check data provider health."""
        try:
            market_data = await self.data_provider.get_market_snapshot()
            return {
                'status': 'healthy',
                'data_age_seconds': market_data['data_age_seconds'],
                'last_update': market_data['timestamp']
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
```

#### **2. Circuit Breakers**
```python
# Live Trading Circuit Breakers
class LiveTradingCircuitBreaker:
    """Circuit breakers for live trading safety."""
    
    def __init__(self):
        self.max_daily_loss_pct = 0.15  # 15% max daily loss
        self.max_position_size_usd = 1000000
        self.heartbeat_timeout_seconds = 300
        self.data_age_threshold_seconds = 60
    
    async def check_circuit_breakers(self) -> List[str]:
        """Check all circuit breakers."""
        breaches = []
        
        # Check daily loss
        daily_pnl_pct = await self.get_daily_pnl_percentage()
        if daily_pnl_pct < -self.max_daily_loss_pct:
            breaches.append(f"Daily loss limit breached: {daily_pnl_pct:.2%}")
        
        # Check position size
        total_position_usd = await self.get_total_position_size()
        if total_position_usd > self.max_position_size_usd:
            breaches.append(f"Position size limit breached: ${total_position_usd:,.2f}")
        
        # Check heartbeat
        last_heartbeat = await self.get_last_heartbeat()
        if (datetime.utcnow() - last_heartbeat).seconds > self.heartbeat_timeout_seconds:
            breaches.append("Heartbeat timeout")
        
        # Check data freshness
        market_data_age = await self.get_market_data_age()
        if market_data_age > self.data_age_threshold_seconds:
            breaches.append(f"Market data too old: {market_data_age}s")
        
        return breaches
```

### **Unified Deployment Commands**

```bash
# 1. Configure environment file
vim backend/env.unified  # Edit the single environment file

# 2. Deploy system (works for all configurations)
cd deploy
./deploy.sh local      # Local development
./deploy.sh staging    # Staging deployment
./deploy.sh prod       # Production deployment

# 3. Check system status
docker compose ps

# 4. View logs
docker compose logs -f backend

# 5. Emergency stop
docker compose stop backend

# 6. Restart with new config
docker compose restart backend

# 7. Update system
git pull
./deploy.sh local  # or staging/prod

# 8. Switch configurations (automated)
./switch-env.sh local    # Sets backend/env.unified + copies .env.local
./switch-env.sh staging  # Sets backend/env.unified + copies .env.staging
./switch-env.sh prod     # Sets backend/env.unified + uses .env
docker compose restart backend

# 9. Frontend testing (optional)
docker compose --profile frontend-test up
```

---

## 🏠 **Local dev**

### **Quick Start**

```bash
# From project root
cd deploy && ./deploy.sh local

# Access points
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8001
# - API Docs: http://localhost:8001/docs
```

**Services Started**:
- Backend (FastAPI on port 8001)
- Frontend (Vite dev server on port 5173)
- Redis (localhost:6379) - NEW! Used by components

### **Environment Configuration**

**File**: `backend/env.unified` (single unified configuration)

**Default Configuration** (Local Development):
```bash
# Configuration Dimensions
BASIS_EXECUTION_MODE=backtest
BASIS_ENVIRONMENT=dev
BASIS_DEPLOYMENT=local

# API Configuration
BASIS_API__PORT=8001
BASIS_API__RELOAD=true
BASIS_API__CORS_ORIGINS=["http://localhost:5173"]

# Redis Configuration
BASIS_REDIS__ENABLED=true
BASIS_REDIS__URL=redis://localhost:6379/0

# Data Provider Settings
BASIS_DATA__CACHE_ENABLED=true
BASIS_DATA__DATA_DIR=./data

# Development Settings
BASIS_DEBUG=true
BASIS_MONITORING__LOG_LEVEL=DEBUG

# Live Trading (disabled by default)
BASIS_LIVE_TRADING__ENABLED=false
BASIS_LIVE_TRADING__READ_ONLY=true
BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD=100
```

**Configuration Switching**:
```bash
# Switch to live trading (edit backend/env.unified):
BASIS_EXECUTION_MODE=live
BASIS_LIVE_TRADING__ENABLED=true
BASIS_LIVE_TRADING__READ_ONLY=true  # Start with read-only

# Switch to production (edit backend/env.unified):
BASIS_ENVIRONMENT=production
BASIS_DEPLOYMENT=cloud
BASIS_API__CORS_ORIGINS=["https://defi-project.odum-research.com"]
BASIS_REDIS__URL=redis://redis:6379/0

# Then restart: docker-compose restart backend
```

### **Docker Compose Commands**

```bash
cd deploy
./deploy.sh local         # Start all services
./stop-local.sh           # Stop all services
docker compose restart    # Restart all services
docker compose ps         # Check service status
docker compose logs -f backend   # View backend logs
docker compose logs -f caddy     # View frontend logs

# Build optimization commands
docker compose build backend     # Optimized build with caching
./build-optimized.sh            # Demo script showing caching benefits
docker compose build --no-cache # Force rebuild (no cache)
```

---

## ☁️ **GCloud VM Deployment**

### **Prerequisites**

**Already Configured** ✅:
- Domain: defi-project.odum-research.com
- VM: GCloud (europe-west1-b)
- TLS: Let's Encrypt (ikenna@odum-research.com)
- Static IP: Attached
- Firewall: TCP 22/80/443 open

### **New Requirement**: GCS Data Bucket

**Create GCS Bucket** (one-time setup):
```bash
# Create bucket
gsutil mb -l europe-west1 gs://basis-strategy-v1-data

# Set lifecycle (optional - keep data 90 days)
gsutil lifecycle set lifecycle.json gs://basis-strategy-v1-data
```

**Upload Data** (from local):
```bash
# Upload entire data/ directory to GCS
./scripts/deployment/upload_data_to_gcs.sh

# Or manual:
gsutil -m rsync -r data/ gs://basis-strategy-v1-data/
```

**Download on VM** (before starting services):
```bash
# On GCloud VM
gsutil -m rsync -r gs://basis-strategy-v1-data/ data/
```

### **Deployment Steps**

**1. Clone/Update Code**:
```bash
# On GCloud VM
cd ~/basis-strategy-v1
git pull origin main
```

**2. Download Data from GCS**:
```bash
# Download latest data (NEW step!)
gsutil -m rsync -r gs://basis-strategy-v1-data/ data/

# Verify data
ls -lh data/market_data/spot_prices/eth_usd/
```

**3. Configure Environment**:
```bash
cd deploy
cp .env.example .env

# Edit .env
vim .env
```

**Contents**:
```bash
APP_DOMAIN=defi-project.odum-research.com
ACME_EMAIL=ikenna@odum-research.com
BASIS_API__CORS_ORIGINS=["https://defi-project.odum-research.com"]

# Redis (required!)
BASIS_REDIS__ENABLED=true
BASIS_REDIS__URL=redis://redis:6379/0

# Data location
BASIS_DATA__DATA_DIR=/app/data

# Environment mode (backtest for production deployment)
BASIS_ENVIRONMENT=production
BASIS_EXECUTION_MODE=backtest
```

**4. Configure Backend Environment**:
```bash
# Edit the unified environment file
vim backend/env.unified
```

**Production Configuration** (edit in `backend/env.unified`):
```bash
# Production Environment
BASIS_ENVIRONMENT=production
BASIS_EXECUTION_MODE=backtest  # Start with backtest, switch to live when ready
BASIS_DEPLOYMENT=cloud

# API Configuration
BASIS_API__PORT=8001
BASIS_API__RELOAD=false
BASIS_API__CORS_ORIGINS=["https://defi-project.odum-research.com"]

# Redis Configuration
BASIS_REDIS__ENABLED=true
BASIS_REDIS__URL=redis://redis:6379/0

# Data Provider Settings
BASIS_DATA__CACHE_ENABLED=true
BASIS_DATA__DATA_DIR=/app/data

# Production Settings
BASIS_DEBUG=false
BASIS_MONITORING__LOG_LEVEL=INFO

# Add your production API keys here when ready for live trading
# BASIS_PROD__CEX__BINANCE_SPOT_API_KEY=your_key
# BASIS_PROD__ALCHEMY__PRIVATE_KEY=your_key
```

**5. Build and Deploy**:
```bash
./deploy.sh prod
```

**6. Verify Deployment**:
```bash
# Check containers
docker ps

# Check health
curl https://defi-project.odum-research.com/health/

# Check API
curl https://defi-project.odum-research.com/api/v1/strategies/
```

---

## 🐳 **Docker Setup**

### **Optimized Build System** ⚡

**Performance**: 99% faster builds with dependency caching

#### **Multi-Stage Dockerfile Architecture**
```dockerfile
# Dependencies stage - Only rebuilds when requirements change
FROM python:3.11-slim AS dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Builder stage - Only rebuilds when source code changes  
FROM dependencies AS builder
COPY backend/ ./backend/
RUN pip install -e ./backend

# Runtime stage - Minimal final image
FROM python:3.11-slim
COPY --from=dependencies /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /app/backend/ ./backend/
```

#### **Build Performance Results**
| Change Type | Build Time | What Rebuilds |
|-------------|------------|---------------|
| **No changes** | ~1-2 seconds | Nothing (all cached) |
| **Source code only** | ~5-10 seconds | Builder + Runtime stages |
| **Requirements change** | ~105 seconds | Dependencies + Builder + Runtime |
| **Config change** | ~2-3 seconds | Runtime stage only |

#### **Optimization Features**
- **`.dockerignore`**: Excludes docs, tests, logs, and development files
- **BuildKit Caching**: Inline cache support for better layer reuse
- **Multi-stage Cache**: Separate cache targets for dependencies, builder, and runtime
- **Build Context**: Reduced from ~2MB to essential files only

#### **Usage**
```bash
# Regular optimized build
docker compose build backend

# Demo script showing caching benefits
./deploy/build-optimized.sh

# Force rebuild (no cache)
docker compose build backend --no-cache
```

### **Services**

**docker-compose.yml** (unified for all environments):
```yaml
services:
  redis:              # Required by components
    image: redis:7-alpine
    restart: unless-stopped
  
  backend:
    build: ../backend
    env_file:
      - ../backend/env.unified  # Backend configuration
      - .env                    # Caddy-specific configuration
    volumes:
      - ../data:/app/data:ro    # Data read-only
      - ../configs:/app/configs:ro
      - ../backend/env.unified:/app/env.unified:ro
    depends_on:
      - redis
  
  caddy:
    build: ./Dockerfile.caddy-frontend
    env_file:
      - .env  # For Caddy-specific variables
    ports:
      - "${HTTP_PORT:-80}:80"
      - "${HTTPS_PORT:-443}:443"
    depends_on:
      - backend
```

**Unified Environment File**:
- **Single File**: `backend/env.unified` handles all configurations
- **Configuration Dimensions**: Execution mode, environment, deployment
- **Easy Switching**: Change settings and restart containers

---

## 📊 **Data Management**

### **GCS Upload Script** (NEW)

**File**: `scripts/deployment/upload_data_to_gcs.sh`

```bash
#!/bin/bash
# Upload data/ directory to GCS bucket

BUCKET="gs://basis-strategy-v1-data"
DATA_DIR="data"

echo "🚀 Uploading data to GCS..."
echo "Bucket: $BUCKET"
echo "Source: $DATA_DIR/"

# Upload with metadata
gsutil -m rsync -r \
  -x ".*\.pyc$|.*__pycache__.*" \
  $DATA_DIR/ $BUCKET/

echo "✅ Upload complete!"
echo "📊 Bucket contents:"
gsutil du -sh $BUCKET
```

**Run before deployment**:
```bash
chmod +x scripts/deployment/upload_data_to_gcs.sh
./scripts/deployment/upload_data_to_gcs.sh
```

---

## 🔧 **Component Architecture Notes**

### **Redis Requirement** (NEW)

**dev**:
- Redis optional (can run in-memory)
- But recommended for testing pub/sub

**Production**:
- Redis required
- Used for component communication
- Channels: `position:updated`, `exposure:calculated`, etc.

**Monitoring Redis**:
```bash
# Connect to Redis
redis-cli

# Subscribe to component updates
SUBSCRIBE position:updated
SUBSCRIBE exposure:calculated
SUBSCRIBE risk:calculated

# View current state
GET position:snapshot
GET exposure:current
GET risk:current
```

---

## 🎯 **Health Checks**

### **Extended Health Check** (NEW)

**Endpoint**: `/health/detailed`

**Returns**:
```json
{
  "status": "healthy",
  "components": {
    "position_monitor": "ready",
    "exposure_monitor": "ready",
    "risk_monitor": "ready",
    "pnl_calculator": "ready",
    "strategy_manager": "ready",
    "redis": "connected",
    "data_provider": "loaded"
  },
  "data_loaded": {
    "modes_supported": ["pure_lending", "btc_basis", "eth_leveraged", "usdt_market_neutral"],
    "data_period": "2024-01-01 to 2025-09-18"
  }
}
```

---

## 🚨 **Troubleshooting**

### **Redis Not Connected**

```bash
# Check Redis running
docker ps | grep redis

# View Redis logs
docker logs deploy-redis-1

# Restart Redis
docker compose restart redis
```

### **Component Initialization Failed**

```bash
# Check backend logs
docker logs deploy-backend-1

# Common issues:
# - Redis not available → Check connection
# - Data not loaded → Check /app/data volume mount
# - Config missing → Check env variables
```

---

## ✅ **Deployment Checklist**

**Before Deployment**:
- [ ] Push to main
- [ ] Upload data to GCS
- [ ] Update .env with domain
- [ ] Configure backend/env.unified with appropriate settings
- [ ] Verify Redis in docker-compose
- [ ] Test locally with Docker

**After Deployment**:
- [ ] Download data from GCS on VM
- [ ] ./deploy.sh prod
- [ ] Check health endpoint
- [ ] Test mode selection via UI
- [ ] Verify Redis connections (docker logs)
- [ ] Verify environment file is loaded (check logs for execution mode)

**Environment File Security**:
- [ ] Set proper permissions: `chmod 600 backend/env.unified`
- [ ] Never commit environment files to git
- [ ] Use single file with different settings for different deployments
- [ ] Rotate API keys regularly

---

## 🏦 **Wallet & API Setup**

### **Environment Overview**

| Environment | Network | CEX APIs | ERC-20 Wallet | Purpose |
|-------------|---------|----------|---------------|---------|
| **dev** | Sepolia Testnet | Testnet APIs | Testnet Wallet | Free testing, full E2E |
| **Staging** | Mainnet | Mainnet APIs | Mainnet Wallet (Small) | Real money, small amounts |
| **Production** | Mainnet | Mainnet APIs | Mainnet Wallet (Full) | Live trading, full amounts |

---

### **ERC-20 Wallet Setup**

**What is an ERC-20 Wallet?**
- Blockchain wallet (NOT a CEX wallet)
- Holds ETH and ERC-20 tokens (USDT, weETH, aTokens)
- Used for on-chain operations: AAVE, staking, flash loans, gas payments
- **Private key** = access to wallet (keep secure!)

**Creating Wallets** (Use MetaMask):
1. Install MetaMask browser extension
2. Create NEW wallet (separate for this project!)
3. Export private key (Account details → Export private key)
4. **Remove 0x prefix** when adding to env.unified
5. Copy wallet address (with 0x prefix)

**Funding by Environment**:
- **dev**: Get testnet ETH from https://sepoliafaucet.com/ (1-2 ETH, free)
- **Staging**: Real ETH (0.1-0.5 ETH for testing)
- **Production**: Real ETH (full amount for trading)

---

### **CEX API Setup**

#### **dev (Testnet APIs)**:
- **Binance**: https://testnet.binance.vision/
- **Bybit**: https://testnet.bybit.com/
- **OKX**: https://www.okx.com/developers/testnet

**Permissions**: Enable spot trading + futures trading only

#### **Production (Mainnet APIs)**:
- Use separate API keys from testnet
- Set IP restrictions where possible
- Enable only required permissions
- Monitor API usage regularly

---

### **Hybrid Testnet Testing Reality**

**Network Separation**: ❌ Cannot directly send Sepolia tokens to CEX testnets (different networks)

**What Works** ✅:
- Real CEX trading on testnet (spot, perps)
- Real DeFi operations on Sepolia (AAVE, staking)
- **System simulates** cross-network transfers
- Complete strategy logic testing
- Full E2E without real money

**What to Test**:
- ✅ Real CEX trading (spot, perps) on testnets
- ✅ Real DeFi (staking, lending, flash loans) on Sepolia
- ✅ Complete strategy logic with simulated transfers
- ✅ All rebalancing and risk management
- ✅ Error handling and API integrations

**Cannot Test**:
- ❌ Real cross-network transfers (system simulates)
- ❌ Real gas costs (testnet is free)
- ❌ Real slippage (testnet has perfect liquidity)

**Control Variable**: `BASIS_CROSS_NETWORK__SIMULATE_TRANSFERS=true` in env.unified

---

### **Security Best Practices**

**Wallet Security**:
- ✅ Use separate wallets for each environment
- ✅ Never reuse wallets between environments
- ✅ Keep private keys secure (hardware wallets for production)
- ✅ Test with small amounts before going live

**API Key Security**:
- ✅ Use separate API keys per environment
- ✅ Set IP restrictions where possible
- ✅ Enable only required permissions
- ✅ Monitor API usage regularly

**Environment Separation**:
- ✅ Never mix testnet/mainnet in same environment
- ✅ Use different wallets for staging vs production
- ✅ Test thoroughly in dev before staging

---


