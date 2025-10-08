#!/bin/bash

# Cursor Web Agent Launcher
# Complete setup for both Agent A and Agent B

echo "🚀 Launching Cursor Web Agent with Complete Setup..."

# Check if we're in a web environment
if [ -n "$CURSOR_WEB" ] || [ -n "$CODESPACE_NAME" ]; then
    echo "✅ Detected web environment"
    WEB_MODE=true
else
    echo "🖥️  Detected local environment"
    WEB_MODE=false
fi

# Install Python requirements
echo "📦 Installing Python requirements..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Python requirements installed"
else
    echo "⚠️  No requirements.txt found - installing basic packages"
    pip install pandas pydantic redis fastapi uvicorn ccxt web3
fi

# Install backend requirements
if [ -f "backend/requirements.txt" ]; then
    echo "📦 Installing backend requirements..."
    pip install -r backend/requirements.txt
    echo "✅ Backend requirements installed"
fi

# Setup Redis
echo "🔧 Setting up Redis..."
if [ "$WEB_MODE" = false ]; then
    # Local environment - try to start Redis
    if ! redis-cli ping > /dev/null 2>&1; then
        echo "Starting Redis..."
        if command -v docker > /dev/null 2>&1; then
            # Stop existing container if running
            docker stop redis-agent 2>/dev/null || true
            docker rm redis-agent 2>/dev/null || true
            # Start new container
            docker run -d -p 6379:6379 --name redis-agent redis:alpine
            sleep 3
            echo "✅ Redis started in Docker"
        elif command -v brew > /dev/null 2>&1; then
            # Try to start with brew services
            brew services start redis 2>/dev/null || echo "⚠️  Could not start Redis with brew"
        else
            echo "⚠️  Redis not available - agent will use in-memory fallback"
        fi
    else
        echo "✅ Redis already running"
    fi
else
    # Web environment - Redis might be provided by the platform
    echo "🌐 Web environment - Redis should be provided by platform"
fi

# Test Redis connection
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis connection successful"
    export REDIS_AVAILABLE=true
else
    echo "⚠️  Redis not available - using in-memory fallback"
    export REDIS_AVAILABLE=false
fi

# Set web-specific environment variables
export CURSOR_AGENT_MODE=web
export CURSOR_AGENT_CONFIG=.cursor-agent-config.json
export CURSOR_AGENT_TASKS=background_agent_tasks.json

# Run preflight checks
echo "🔍 Running preflight checks..."
if [ -f "preflight_check.py" ]; then
    python preflight_check.py
    echo "✅ Preflight checks completed"
else
    echo "⚠️  No preflight_check.py found"
fi

# Display agent status
echo ""
echo "🎯 Cursor Web Agent Status:"
echo "   Environment: $([ "$WEB_MODE" = true ] && echo "Web Browser" || echo "Local")"
echo "   Redis: $([ "$REDIS_AVAILABLE" = true ] && echo "Available" || echo "In-memory fallback")"
echo "   Branch: agent-implementation"
echo "   Mode: Background (continuous work)"
echo ""

echo "👥 Available Agents:"
echo "   Agent A: Monitoring & Calculation (Position, Exposure, Event, Risk, P&L)"
echo "   Agent B: Infrastructure & Execution (Data, Strategy, CEX, OnChain, Deploy)"
echo ""

# Show available commands
echo "📋 Available Commands:"
echo "   Agent A Tasks:"
echo "     cursor --agent-task position_monitor"
echo "     cursor --agent-task event_logger"
echo "     cursor --agent-task exposure_monitor"
echo "     cursor --agent-task risk_monitor"
echo "     cursor --agent-task pnl_calculator"
echo ""
echo "   Agent B Tasks:"
echo "     cursor --agent-task data_provider"
echo "     cursor --agent-task strategy_manager"
echo "     cursor --agent-task cex_execution_manager"
echo "     cursor --agent-task onchain_execution_manager"
echo ""
echo "   General:"
echo "     cursor --agent-task all"
echo "     cursor --agent-status"
echo ""

echo "✅ Web Agent ready!"
echo "🚀 Ready to implement components in Cursor web browser!"
echo "📖 Read AGENT_A_INSTRUCTIONS.md or AGENT_B_INSTRUCTIONS.md for detailed tasks"
