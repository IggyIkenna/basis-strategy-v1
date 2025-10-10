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
HEALTH_ENDPOINT=${HEALTH_CHECK_ENDPOINT:-/health}
BACKEND_PORT=${BASIS_API_PORT:-8001}
MAX_RETRIES=3
RETRY_COUNT=0

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
    
    if curl -s -f "$url" >/dev/null 2>&1; then
        log "✅ Health check passed"
        return 0
    else
        log "❌ Health check failed"
        return 1
    fi
}

# Function to restart services
restart_services() {
    log "🔄 Restarting services (attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
    
    # Get the directory where this script is located
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local project_root="$(dirname "$script_dir")"
    
    # Change to project root and restart
    cd "$project_root"
    
    if ./platform.sh restart; then
        log "✅ Services restarted successfully"
        RETRY_COUNT=0  # Reset retry count on success
        return 0
    else
        log "❌ Service restart failed"
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

