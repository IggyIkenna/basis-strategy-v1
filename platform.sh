#!/bin/bash
# DeFi Yield Optimization Platform Management Script
# Unified script to manage backend and frontend services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default ports
BACKEND_PORT=${BASIS_API_PORT:-8001}
FRONTEND_PORT=5173

# Function to check if port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to kill processes on a port
kill_port() {
    local port=$1
    if port_in_use $port; then
        echo -e "${YELLOW}🛑 Killing processes on port $port...${NC}"
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Function to find next available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    while port_in_use $port; do
        port=$((port + 1))
    done
    echo $port
}

# Redis removed - using in-memory cache only

# Function to create required directories
create_directories() {
    echo -e "${BLUE}📁 Creating required directories...${NC}"
    
    # Create logs directory
    mkdir -p logs
    echo -e "${GREEN}✅ Created logs directory${NC}"
    
    # Create results directory
    mkdir -p results
    echo -e "${GREEN}✅ Created results directory${NC}"
    
    # Create data directory if it doesn't exist
    if [ ! -d "data" ]; then
        echo -e "${YELLOW}⚠️ Data directory not found. Please ensure data files are available.${NC}"
    else
        echo -e "${GREEN}✅ Data directory exists${NC}"
    fi
}

# Function to load environment variables
load_environment() {
    echo -e "${BLUE}🔧 Loading environment variables...${NC}"
    
    # Preserve important environment variables if they were set before loading env.unified
    local original_environment=${BASIS_ENVIRONMENT:-}
    local original_skip_quality_gates=${SKIP_QUALITY_GATES:-}
    local original_skip_frontend=${SKIP_FRONTEND:-}
    
    # Load base environment from env.unified
    if [ -f "env.unified" ]; then
        echo -e "${BLUE}📋 Loading base environment from env.unified...${NC}"
        set -a
        source env.unified
        set +a
    else
        echo -e "${RED}❌ env.unified not found${NC}"
        return 1
    fi
    
    # Restore original environment if it was set
    if [ -n "$original_environment" ]; then
        export BASIS_ENVIRONMENT="$original_environment"
    fi
    
    # Load environment-specific override file (platform.sh only uses root env files)
    local environment=${BASIS_ENVIRONMENT:-dev}
    echo -e "${BLUE}🏗️ Environment: $environment${NC}"
    
    case $environment in
        "dev")
            if [ -f ".env.dev" ]; then
                echo -e "${BLUE}📋 Loading local overrides from .env.dev...${NC}"
                set -a
                source .env.dev
                set +a
            else
                echo -e "${YELLOW}⚠️ .env.dev not found, using base configuration${NC}"
            fi
            ;;
        "staging")
            if [ -f ".env.staging" ]; then
                echo -e "${BLUE}📋 Loading staging overrides from .env.staging...${NC}"
                set -a
                source .env.staging
                set +a
            else
                echo -e "${YELLOW}⚠️ .env.staging not found, using base configuration${NC}"
            fi
            ;;
        "prod")
            if [ -f ".env.production" ]; then
                echo -e "${BLUE}📋 Loading production overrides from .env.production...${NC}"
                set -a
                source .env.production
                set +a
            else
                echo -e "${YELLOW}⚠️ .env.production not found, using base configuration${NC}"
            fi
            ;;
        *)
            echo -e "${YELLOW}⚠️ Unknown environment: $environment, using base configuration${NC}"
            ;;
    esac
    
    # Restore command-line variables if they were set (after all file loading)
    if [ -n "$original_skip_quality_gates" ]; then
        export SKIP_QUALITY_GATES="$original_skip_quality_gates"
    fi
    if [ -n "$original_skip_frontend" ]; then
        export SKIP_FRONTEND="$original_skip_frontend"
    fi
    
    # Validate required environment variables
    local required_vars=(
        "BASIS_ENVIRONMENT"
        "BASIS_DEPLOYMENT_MODE"
        "BASIS_DEPLOYMENT_MACHINE"
        "BASIS_DATA_DIR"
        "BASIS_RESULTS_DIR"
        "BASIS_DEBUG"
        "BASIS_LOG_LEVEL"
        "BASIS_EXECUTION_MODE"
        "BASIS_DATA_START_DATE"
        "BASIS_DATA_END_DATE"
    )
    
    # Add frontend vars if not in backend-only mode
    if [ "${BACKEND_ONLY:-false}" = "false" ]; then
        required_vars+=(
            "APP_DOMAIN"
            "ACME_EMAIL"
            "HTTP_PORT"
            "HTTPS_PORT"
            "HEALTH_CHECK_INTERVAL"
        )
    fi
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing required environment variables:${NC}"
        for var in "${missing_vars[@]}"; do
            echo -e "${RED}  - $var${NC}"
        done
        return 1
    fi
    
    echo -e "${GREEN}✅ Environment variables loaded successfully${NC}"
    return 0
}

# Function to run quality gates
run_quality_gates() {
    # Check if quality gates should be skipped
    if [ "${SKIP_QUALITY_GATES:-false}" = "true" ]; then
        echo -e "${YELLOW}⚠️  Skipping quality gates (SKIP_QUALITY_GATES=true)${NC}"
        return 0
    fi
    
    echo -e "${BLUE}🚦 Running critical quality gates...${NC}"
    
    # Run configuration validation
    echo -e "${BLUE}  📋 Running configuration validation...${NC}"
    python3 scripts/run_quality_gates.py --category configuration
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Configuration validation failed${NC}"
        return 1
    fi
    
    # Run environment variable validation
    echo -e "${BLUE}  🔧 Running environment variable validation...${NC}"
    python3 scripts/run_quality_gates.py --category env_config_sync
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Environment variable validation failed${NC}"
        return 1
    fi
    
    # Run data validation
    echo -e "${BLUE}  📊 Running data validation...${NC}"
    python3 scripts/test_data_files_quality_gates.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Data validation failed${NC}"
        return 1
    fi
    
    # Run data provider canonical access validation
    echo -e "${BLUE}  🔍 Running data provider canonical access validation...${NC}"
    python3 scripts/test_data_provider_canonical_access_quality_gates_simple.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Data provider canonical access validation failed${NC}"
        return 1
    fi
    
    # Run component communication architecture validation
    echo -e "${BLUE}  🏗️ Running component communication architecture validation...${NC}"
    python3 scripts/test_component_data_flow_architecture_quality_gates.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Component communication architecture validation failed${NC}"
        return 1
    fi
    
    
    echo -e "${GREEN}✅ All critical quality gates passed${NC}"
    return 0
}

# Function to start backend
start_backend() {
    echo -e "${BLUE}🚀 Starting backend...${NC}"
    
    # Create required directories
    create_directories
    
    # Run quality gates before starting
    run_quality_gates
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Quality gates failed. Aborting startup.${NC}"
        return 1
    fi
    
    # Call pip install dependencies
    pip_install_dependencies
    
    # Check if port is already in use with timeout
    echo -e "${BLUE}🔍 Checking if port $BACKEND_PORT is available...${NC}"
    if port_in_use $BACKEND_PORT; then
        echo -e "${YELLOW}⚠️ Port $BACKEND_PORT is already in use${NC}"
        echo -e "${BLUE}🔄 Attempting to find available port...${NC}"
        
        # Find next available port
        BACKEND_PORT=$(find_available_port $BACKEND_PORT)
        echo -e "${GREEN}✅ Using port $BACKEND_PORT instead${NC}"
    fi
    
    # Start API server in background from root directory (so configs/ is accessible)
    echo -e "${BLUE}🌐 Starting FastAPI server on port $BACKEND_PORT...${NC}"
    mkdir -p backend/logs
    
    # Start with timeout handling (using background process)
    local reload_flag=""
    if [ "${BASIS_HOT_RELOAD:-false}" = "true" ]; then
        reload_flag="--reload"
        echo -e "${BLUE}🔥 Hot reload enabled${NC}"
    else
        echo -e "${BLUE}❄️ Hot reload disabled${NC}"
    fi
    
    export PYTHONPATH=backend/src
    python3 -m uvicorn backend.src.basis_strategy_v1.api.main:app --host 0.0.0.0 --port $BACKEND_PORT $reload_flag > backend/logs/api.log 2>&1 &
    BACKEND_PID=$!
    
    # Wait for backend to start with timeout
    echo -e "${BLUE}⏳ Waiting for backend to start (timeout: 30s)...${NC}"
    local timeout_count=0
    local max_timeout=30
    
    while [ $timeout_count -lt $max_timeout ]; do
        if curl -s --connect-timeout 3 --max-time 5 http://localhost:$BACKEND_PORT/health/ >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend started successfully on port $BACKEND_PORT (PID: $BACKEND_PID)${NC}"
            
            # Start health monitor
            start_health_monitor
            
            return 0
        fi
        
        # Check if process is still running
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            echo -e "${RED}❌ Backend process died. Check logs: tail -f backend/logs/api.log${NC}"
            return 1
        fi
        
        sleep 1
        timeout_count=$((timeout_count + 1))
    done
    
    # Timeout reached
    echo -e "${RED}❌ Backend startup timeout after ${max_timeout}s${NC}"
    echo -e "${RED}❌ Killing backend process (PID: $BACKEND_PID)${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    echo -e "${YELLOW}💡 Check logs: tail -f backend/logs/api.log${NC}"
    echo -e "${YELLOW}💡 Try: ./platform.sh stop && ./platform.sh start${NC}"
    return 1
}

# Function to start frontend
start_frontend() {
    echo -e "${BLUE}⚛️ Starting frontend...${NC}"
    
    # Install frontend dependencies first
    npm_install_dependencies
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install frontend dependencies. Aborting frontend startup.${NC}"
        return 1
    fi
    
    cd frontend
    
    # Load nvm if available
    if [ -d "$HOME/.nvm" ]; then
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm use --lts 2>/dev/null || true
    fi
    
    # Find available port
    AVAILABLE_PORT=$(find_available_port $FRONTEND_PORT)
    
    if [ "$AVAILABLE_PORT" != "$FRONTEND_PORT" ]; then
        echo -e "${YELLOW}⚠️ Port $FRONTEND_PORT in use, using port $AVAILABLE_PORT${NC}"
    fi
    
    # Start frontend in background
    echo -e "${BLUE}🌐 Starting React dev server on port $AVAILABLE_PORT...${NC}"
    mkdir -p ../logs
    nohup npm run dev -- --port $AVAILABLE_PORT > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for frontend to start
    echo -e "${BLUE}⏳ Waiting for frontend to start...${NC}"
    sleep 5
    
    # Test frontend health
    if curl -s http://localhost:$AVAILABLE_PORT >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend started successfully on port $AVAILABLE_PORT (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${RED}❌ Frontend failed to start. Check logs: tail -f logs/frontend.log${NC}"
        return 1
    fi
    
    cd ..
}

# Function to start dev mode
start_dev() {
    echo -e "${BLUE}🏗️ Starting dev mode...${NC}"
    
    # Clean up any existing uvicorn processes
    echo -e "${BLUE}🧹 Cleaning up existing processes...${NC}"
    pkill -f uvicorn 2>/dev/null || true
    sleep 2
    
    # Load environment variables
    if ! load_environment; then
        echo -e "${RED}❌ Failed to load environment variables${NC}"
        return 1
    fi
    
    # Set environment to dev if not already set
    export BASIS_ENVIRONMENT=dev
    echo -e "${BLUE}🏗️ Environment: dev${NC}"
    
    # Create required directories
    create_directories
    
    # Run quality gates before starting
    run_quality_gates
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Quality gates failed. Aborting startup.${NC}"
        return 1
    fi
    
    # Call pip install dependencies
    pip_install_dependencies
    
    # Redis removed - using in-memory cache only
    
    # Check if port is already in use with timeout
    echo -e "${BLUE}🔍 Checking if port $BACKEND_PORT is available...${NC}"
    if port_in_use $BACKEND_PORT; then
        echo -e "${YELLOW}⚠️ Port $BACKEND_PORT is already in use${NC}"
        echo -e "${BLUE}🔄 Attempting to find available port...${NC}"
        
        # Find next available port
        BACKEND_PORT=$(find_available_port $BACKEND_PORT)
        echo -e "${GREEN}✅ Using port $BACKEND_PORT instead${NC}"
    fi
    
    # Start backend in dev mode
    echo -e "${BLUE}🚀 Starting backend in dev mode...${NC}"
    mkdir -p backend/logs
    
    local reload_flag=""
    if [ "${BASIS_HOT_RELOAD:-false}" = "true" ]; then
        reload_flag="--reload"
        echo -e "${BLUE}🔥 Hot reload enabled${NC}"
    else
        echo -e "${BLUE}❄️ Hot reload disabled${NC}"
    fi
    
    export PYTHONPATH=backend/src
    nohup python3 -m uvicorn backend.src.basis_strategy_v1.api.main:app --host 0.0.0.0 --port $BACKEND_PORT $reload_flag > backend/logs/api.log 2>&1 &
    BACKEND_PID=$!
    
    # Wait for backend to start
    echo -e "${BLUE}⏳ Waiting for backend to start...${NC}"
    sleep 5
    
    # Test backend health
    if curl -s --connect-timeout 3 --max-time 5 http://localhost:$BACKEND_PORT/health/ >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend started successfully in dev mode on port $BACKEND_PORT (PID: $BACKEND_PID)${NC}"
        echo -e "${BLUE}📊 API available at: http://localhost:$BACKEND_PORT/api/v1/${NC}"
        
        # Start health monitor
        start_health_monitor
    else
        echo -e "${RED}❌ Backend failed to start. Check logs: tail -f backend/logs/api.log${NC}"
        return 1
    fi
}

# Function to stop all services
stop_all() {
    echo -e "${BLUE}🛑 Stopping all services...${NC}"
    
    # Stop health monitor first
    stop_health_monitor
    
    # Stop all uvicorn processes (not just the stored PID)
    echo -e "${BLUE}🛑 Stopping all uvicorn processes...${NC}"
    pkill -f uvicorn 2>/dev/null || true
    
    # Also stop the specific backend PID if it exists
    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "${BLUE}🛑 Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Stop frontend
    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "${BLUE}🛑 Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Kill processes on ports
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT
    
    # Redis removed - using in-memory cache only
    
    echo -e "${GREEN}✅ All services stopped${NC}"
}

# Function to restart all services
restart_all() {
    echo -e "${BLUE}🔄 Restarting all services...${NC}"
    stop_all
    sleep 2
    start_backend
    start_frontend
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 Service Status:${NC}"
    
    # Check backend
    if port_in_use $BACKEND_PORT; then
        echo -e "${GREEN}✅ Backend: Running on port $BACKEND_PORT${NC}"
    else
        echo -e "${RED}❌ Backend: Not running${NC}"
    fi
    
    # Check frontend
    if port_in_use $FRONTEND_PORT; then
        echo -e "${GREEN}✅ Frontend: Running on port $FRONTEND_PORT${NC}"
    else
        echo -e "${RED}❌ Frontend: Not running${NC}"
    fi
    
    # Redis removed - using in-memory cache only
}

# Function to show logs
show_logs() {
    local service=$1
    case $service in
        "backend"|"api")
            echo -e "${BLUE}📋 Backend logs:${NC}"
            tail -f backend/logs/api.log
            ;;
        "frontend"|"react")
            echo -e "${BLUE}📋 Frontend logs:${NC}"
            tail -f logs/frontend.log
            ;;
        "all")
            echo -e "${BLUE}📋 All logs:${NC}"
            tail -f backend/logs/api.log logs/frontend.log
            ;;
        *)
            echo -e "${YELLOW}Usage: $0 logs [backend|frontend|all]${NC}"
            ;;
    esac
}

# Function to run tests
run_tests() {
    echo -e "${BLUE}🧪 Running tests...${NC}"
    
    # Load environment variables
    if ! load_environment; then
        echo -e "${RED}❌ Failed to load environment variables${NC}"
        return 1
    fi
    
    # Run backend tests
    echo -e "${BLUE}🔧 Running backend tests...${NC}"
    python3 scripts/run_quality_gates.py
    
    # Run frontend tests
    echo -e "${BLUE}⚛️ Running frontend tests...${NC}"
    cd frontend
    npm test -- --watchAll=false
    cd ..
    
    echo -e "${GREEN}✅ All tests completed${NC}"
}

# Function to set environment
set_environment() {
    local env=${1:-dev}
    
    if [ "$env" = "prod" ]; then
        echo -e "${BLUE}🏭 Setting production environment...${NC}"
        export BASIS_ENVIRONMENT=prod
        export BASIS_DEPLOYMENT_MODE=local
        echo -e "${GREEN}✅ Environment set to production${NC}"
        echo -e "${YELLOW}💡 Now run: ./platform.sh start${NC}"
    else
        echo -e "${BLUE}🔧 Setting development environment...${NC}"
        export BASIS_ENVIRONMENT=dev
        export BASIS_DEPLOYMENT_MODE=local
        echo -e "${GREEN}✅ Environment set to development${NC}"
        echo -e "${YELLOW}💡 Now run: ./platform.sh start${NC}"
    fi
}

# Function to pip install dependencies with pip install -r requirements.txt
pip_install_dependencies() {
    echo -e "${BLUE}🔧 Pip installing dependencies...${NC}"
    pip3 install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies pip installed${NC}"
}

# Function to validate node/npm availability
validate_node_npm() {
    echo -e "${BLUE}🔍 Validating Node.js and npm availability...${NC}"
    
    # Check if node is available
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js is not installed or not in PATH${NC}"
        echo -e "${YELLOW}💡 To install Node.js:${NC}"
        echo -e "${YELLOW}   - macOS: brew install node${NC}"
        echo -e "${YELLOW}   - Ubuntu/Debian: sudo apt install nodejs npm${NC}"
        echo -e "${YELLOW}   - Or visit: https://nodejs.org/${NC}"
        return 1
    fi
    
    # Check if npm is available
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm is not installed or not in PATH${NC}"
        echo -e "${YELLOW}💡 npm usually comes with Node.js. Try reinstalling Node.js${NC}"
        return 1
    fi
    
    # Get versions
    local node_version=$(node --version 2>/dev/null || echo "unknown")
    local npm_version=$(npm --version 2>/dev/null || echo "unknown")
    
    echo -e "${GREEN}✅ Node.js: $node_version${NC}"
    echo -e "${GREEN}✅ npm: $npm_version${NC}"
    return 0
}

# Function to npm install frontend dependencies
npm_install_dependencies() {
    echo -e "${BLUE}🔧 Installing frontend dependencies...${NC}"
    
    # Validate node/npm first
    if ! validate_node_npm; then
        echo -e "${RED}❌ Node.js/npm validation failed. Cannot install frontend dependencies.${NC}"
        return 1
    fi
    
    # Check if frontend directory exists
    if [ ! -d "frontend" ]; then
        echo -e "${RED}❌ Frontend directory not found${NC}"
        return 1
    fi
    
    # Change to frontend directory
    cd frontend
    
    # Load nvm if available
    if [ -d "$HOME/.nvm" ]; then
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm use --lts 2>/dev/null || true
    fi
    
    # Check if node_modules exists and if package.json is newer
    local should_install=false
    
    if [ ! -d "node_modules" ]; then
        echo -e "${BLUE}📦 node_modules not found, installing dependencies...${NC}"
        should_install=true
    elif [ "package.json" -nt "node_modules" ]; then
        echo -e "${BLUE}📦 package.json is newer than node_modules, reinstalling dependencies...${NC}"
        should_install=true
    else
        echo -e "${GREEN}✅ Frontend dependencies already up to date${NC}"
    fi
    
    if [ "$should_install" = true ]; then
        echo -e "${BLUE}📦 Running npm install...${NC}"
        if npm install; then
            echo -e "${GREEN}✅ Frontend dependencies installed successfully${NC}"
        else
            echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
            cd ..
            return 1
        fi
    fi
    
    # Return to root directory
    cd ..
    return 0
}

# Function to start health monitor
start_health_monitor() {
    echo -e "${BLUE}🏥 Starting health monitor...${NC}"
    
    if [ -z "$HEALTH_CHECK_INTERVAL" ]; then
        echo -e "${YELLOW}⚠️ HEALTH_CHECK_INTERVAL not set, skipping health monitor${NC}"
        return 0
    fi
    
    # Check if health monitor is already running
    if pgrep -f health_monitor.sh >/dev/null; then
        echo -e "${YELLOW}⚠️ Health monitor already running, skipping${NC}"
        return 0
    fi
    
    # Export environment variables for health monitor
    export HEALTH_CHECK_INTERVAL
    export HEALTH_CHECK_ENDPOINT
    export BASIS_API_PORT
    
    # Start monitor in background
    ./scripts/health_monitor.sh > logs/health_monitor.log 2>&1 &
    echo $! > logs/health_monitor.pid
    
    echo -e "${GREEN}✅ Health monitor started (PID: $(cat logs/health_monitor.pid))${NC}"
}

# Function to stop health monitor
stop_health_monitor() {
    echo -e "${BLUE}🛑 Stopping all health monitor processes...${NC}"
    pkill -f health_monitor.sh 2>/dev/null || true
    
    if [ -f "logs/health_monitor.pid" ]; then
        rm logs/health_monitor.pid
    fi
    
    echo -e "${GREEN}✅ Health monitor stopped${NC}"
}

# Function to show help
show_help() {
    echo -e "${BLUE}DeFi Yield Optimization Platform Management Script${NC}"
    echo ""
    echo -e "${YELLOW}Usage: $0 [COMMAND]${NC}"
    echo ""
    echo -e "${GREEN}Commands:${NC}"
    echo -e "  ${BLUE}start${NC}        Start backend and frontend (uses env file BASIS_EXECUTION_MODE)"
    echo -e "  ${BLUE}stop${NC}         Stop all services"
    echo -e "  ${BLUE}restart${NC}      Restart all services"
    echo -e "  ${BLUE}dev${NC}          Start in dev mode (backend only, uses env.dev overrides)"
    echo -e "  ${BLUE}backend${NC}      Start backend only (uses env file BASIS_EXECUTION_MODE)"
    echo -e "  ${BLUE}status${NC}       Show service status"
    echo -e "  ${BLUE}logs${NC}         Show logs [backend|frontend|all]"
    echo -e "  ${BLUE}test${NC}         Run all tests"
    echo -e "  ${BLUE}env${NC}          Set environment (dev|prod)"
    echo -e "  ${BLUE}help${NC}         Show this help message"
    echo ""
    echo -e "${GREEN}Environment Variables:${NC}"
    echo -e "  ${BLUE}BASIS_API_PORT${NC}         Backend port (default: 8001)"
    echo -e "  ${BLUE}BASIS_DEPLOYMENT_MODE${NC}  Deployment mode (local|docker)"
    echo -e "  ${BLUE}SKIP_QUALITY_GATES${NC}     Skip quality gate validation (true|false, default: false)"
    echo -e "  ${BLUE}SKIP_FRONTEND${NC}          Skip frontend startup (true|false, default: false)"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo -e "  ${BLUE}$0 env dev${NC}                      # Set development environment"
    echo -e "  ${BLUE}SKIP_QUALITY_GATES=true $0 dev${NC}     # Start dev mode without quality gates"
    echo -e "  ${BLUE}SKIP_FRONTEND=true $0 start${NC}        # Start backend only (skip frontend)"
    echo -e "  ${BLUE}$0 env prod${NC}        # Set production environment"
    echo -e "  ${BLUE}$0 start${NC}           # Start all services"
    echo -e "  ${BLUE}$0 dev${NC}             # Start in dev mode"
    echo -e "  ${BLUE}$0 logs backend${NC}    # Show backend logs"
    echo -e "  ${BLUE}$0 status${NC}          # Check service status"
}

# Main script logic
case "${1:-help}" in
    "start")
        # Load environment variables first
        if ! load_environment; then
            echo -e "${RED}❌ Failed to load environment variables${NC}"
            exit 1
        fi
        
        start_backend
        if [ "${SKIP_FRONTEND:-false}" != "true" ]; then
            start_frontend
        else
            echo -e "${YELLOW}⚠️ Skipping frontend startup (SKIP_FRONTEND=true)${NC}"
        fi
        ;;
    "stop")
        stop_all
        ;;
    "restart")
        restart_all
        ;;
    "dev")
        start_dev
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "$2"
        ;;
    "test")
        run_tests
        ;;
    "env")
        set_environment "$2"
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac