#!/bin/bash
# Health Monitor - Pings /health and restarts services on failure
# Uses HEALTH_CHECK_INTERVAL from environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HEALTH_ENDPOINT=${HEALTH_CHECK_ENDPOINT:-/health/}
BACKEND_PORT=${BASIS_API_PORT:-8001}
MAX_RETRIES=3
RETRY_COUNT=0

# Function to find the actual backend port
find_backend_port() {
    # Look for uvicorn processes and extract the port, preferring the newest (highest PID)
    local port=$(ps aux | grep uvicorn | grep -v grep | grep -o '\--port [0-9]*' | awk '{print $2}' | tail -1)
    if [ -n "$port" ]; then
        echo "$port"
    else
        echo "$BACKEND_PORT"  # Fallback to configured port
    fi
}

# Update backend port to actual running port
BACKEND_PORT=$(find_backend_port)

# Logging
LOG_FILE="logs/health_monitor.log"
PID_FILE="logs/health_monitor.pid"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to parse interval (e.g., "30s" -> 30, "1m" -> 60)
parse_interval() {
    local interval="$1"
    if [[ "$interval" =~ ^([0-9]+)s$ ]]; then
        echo "${BASH_REMATCH[1]}"
    elif [[ "$interval" =~ ^([0-9]+)m$ ]]; then
        echo $((${BASH_REMATCH[1]} * 60))
    else
        echo "30"  # Default to 30 seconds
    fi
}

# Function to check health
check_health() {
    local url="http://localhost:$BACKEND_PORT$HEALTH_ENDPOINT"
    log "Checking health at $url"
    
    if curl -s -f --connect-timeout 5 --max-time 10 "$url" >/dev/null 2>&1; then
        log "✅ Health check passed"
        return 0
    else
        log "❌ Health check failed"
        return 1
    fi
}

# Function to restart services on the same port
restart_services() {
    log "🔄 Restarting backend on port $BACKEND_PORT (attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
    
    # Get the directory where this script is located
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local project_root="$(dirname "$script_dir")"
    
    # Change to project root
    cd "$project_root"
    
    # Kill all uvicorn processes to ensure clean restart
    log "🛑 Stopping all backend processes..."
    pkill -f uvicorn 2>/dev/null || true
    
    # Also kill any python processes using the port
    local port_pid=$(lsof -ti :$BACKEND_PORT 2>/dev/null || true)
    if [ -n "$port_pid" ]; then
        log "🛑 Killing process $port_pid using port $BACKEND_PORT..."
        kill -9 $port_pid 2>/dev/null || true
    fi
    
    # Wait for port to be free
    log "⏳ Waiting for port $BACKEND_PORT to be free..."
    local port_wait=0
    while [ $port_wait -lt 10 ]; do
        if ! lsof -i :$BACKEND_PORT >/dev/null 2>&1; then
            break
        fi
        sleep 1
        port_wait=$((port_wait + 1))
    done
    
    # Start backend on the same port
    log "🚀 Starting backend on port $BACKEND_PORT..."
    mkdir -p backend/logs
    
    # Load environment variables before starting backend (matching platform.sh exactly)
    log "🔧 Loading environment variables for restart..."
    
    # Preserve BASIS_ENVIRONMENT if it was set before loading env.unified
    local original_environment=${BASIS_ENVIRONMENT:-}
    
    # Load base environment from env.unified
    if [ -f "env.unified" ]; then
        log "📋 Loading base environment from env.unified..."
        set -a
        source env.unified
        set +a
    else
        log "❌ env.unified not found"
        return 1
    fi
    
    # Restore original BASIS_ENVIRONMENT if it was set
    if [ -n "$original_environment" ]; then
        export BASIS_ENVIRONMENT="$original_environment"
    fi
    
    # Load environment-specific override file
    local environment=${BASIS_ENVIRONMENT:-dev}
    log "🏗️ Environment: $environment"
    
    case $environment in
        "dev")
            if [ -f ".env.dev" ]; then
                log "📋 Loading local overrides from .env.dev..."
                set -a
                source .env.dev
                set +a
            else
                log "⚠️ .env.dev not found, using base configuration"
            fi
            ;;
        "staging")
            if [ -f ".env.staging" ]; then
                log "📋 Loading staging overrides from .env.staging..."
                set -a
                source .env.staging
                set +a
            else
                log "⚠️ .env.staging not found, using base configuration"
            fi
            ;;
        "prod")
            if [ -f ".env.production" ]; then
                log "📋 Loading production overrides from .env.production..."
                set -a
                source .env.production
                set +a
            else
                log "⚠️ .env.production not found, using base configuration"
            fi
            ;;
        *)
            log "⚠️ Unknown environment: $environment, using base configuration"
            ;;
    esac
    
    # Note: We don't override BASIS_EXECUTION_MODE here - let the environment files control it
    # This allows the health monitor to restart in the same mode the platform was originally started
    
    # Start backend with same environment variables
    local reload_flag=""
    if [ "${BASIS_HOT_RELOAD:-false}" = "true" ]; then
        reload_flag="--reload"
        log "🔥 Hot reload enabled"
    else
        log "❄️ Hot reload disabled"
    fi
    
    nohup python3 -m uvicorn backend.src.basis_strategy_v1.api.main:app --host 0.0.0.0 --port $BACKEND_PORT $reload_flag > backend/logs/api.log 2>&1 &
    local backend_pid=$!
    
    # Wait for backend to start
    log "⏳ Waiting for backend to start..."
    sleep 5
    
    # Check if backend is healthy
    if curl -s --connect-timeout 3 --max-time 5 http://localhost:$BACKEND_PORT$HEALTH_ENDPOINT >/dev/null 2>&1; then
        log "✅ Backend restarted successfully on port $BACKEND_PORT (PID: $backend_pid)"
        RETRY_COUNT=0  # Reset retry count on success
        return 0
    else
        log "❌ Backend restart failed - health check failed"
        RETRY_COUNT=$((RETRY_COUNT + 1))
        return 1
    fi
}

# Function to calculate backoff delay
get_backoff_delay() {
    case $RETRY_COUNT in
        1) echo 5 ;;
        2) echo 10 ;;
        3) echo 20 ;;
        *) echo 30 ;;
    esac
}

# Main monitoring loop
main() {
    log "🏥 Health monitor started"
    log "Configuration:"
    log "  - Endpoint: $HEALTH_ENDPOINT"
    log "  - Backend Port: $BACKEND_PORT"
    log "  - Check Interval: $HEALTH_CHECK_INTERVAL"
    log "  - Max Retries: $MAX_RETRIES"
    
    # Parse interval
    local interval_seconds
    interval_seconds=$(parse_interval "$HEALTH_CHECK_INTERVAL")
    log "  - Check Interval (seconds): $interval_seconds"
    
    # Wait longer for initial startup before starting health checks
    log "⏳ Waiting 30 seconds for backend to fully start up..."
    sleep 30
    
    # Main monitoring loop
    while true; do
        if ! check_health; then
            log "⚠️ Backend unhealthy, attempting restart..."
            
            if restart_services; then
                log "✅ Services restarted successfully"
                # Wait a bit longer after successful restart
                sleep 10
            else
                if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
                    log "❌ Max retries ($MAX_RETRIES) reached. Giving up."
                    log "❌ Manual intervention required. Check backend logs: tail -f backend/logs/api.log"
                    exit 1
                else
                    local delay
                    delay=$(get_backoff_delay)
                    log "⏳ Waiting $delay seconds before next retry..."
                    sleep $delay
                fi
            fi
        else
            # Reset retry count on successful health check
            RETRY_COUNT=0
        fi
        
        # Wait for next check
        sleep $interval_seconds
    done
}

# Signal handlers
cleanup() {
    log "🛑 Health monitor stopping..."
    exit 0
}

trap cleanup SIGTERM SIGINT

# Check if required environment variables are set
if [ -z "$HEALTH_CHECK_INTERVAL" ]; then
    log "❌ HEALTH_CHECK_INTERVAL not set. Exiting."
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start monitoring
main

