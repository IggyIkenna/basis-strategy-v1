#!/bin/bash

# Start Web Agent for Basis Strategy Project
# This script sets up and starts a web-based background agent

set -e

echo "🚀 Starting Web Agent for Basis Strategy Project..."

# Check if we're in the right directory
if [ ! -f "platform.sh" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Check if backend is running
if ! curl -s http://localhost:8001/health/ > /dev/null 2>&1; then
    echo "⚠️  Backend not running. Starting backend..."
    ./platform.sh stop-local
    ./platform.sh backtest
    
    # Wait for backend to start
    echo "⏳ Waiting for backend to start..."
    sleep 10
    
    # Verify backend is running
    if curl -s http://localhost:8001/health/ > /dev/null 2>&1; then
        echo "✅ Backend started successfully"
    else
        echo "❌ Failed to start backend. Please check logs."
        exit 1
    fi
else
    echo "✅ Backend is already running"
fi

# Validate environment
echo "🔍 Validating environment..."
python validate_config.py
python validate_docs.py

# Run initial quality gates check
echo "📊 Checking quality gates status..."
python scripts/run_quality_gates.py

echo "🎉 Web Agent environment ready!"
echo ""
echo "📋 Available commands:"
echo "   python scripts/run_quality_gates.py  - Run quality gates"
echo "   ./platform.sh backtest               - Start backend"
echo "   ./platform.sh stop-local             - Stop services"
echo "   python validate_config.py            - Validate config"
echo "   python validate_docs.py              - Validate docs"
echo ""
echo "🌐 Web Agent is ready to work on the Basis Strategy project!"
echo "   Focus areas: Architecture compliance, quality gates, documentation"
echo "   Target: 15/24 quality gates passing (60%+)"
echo "   Architecture: 100% compliance with canonical principles"
