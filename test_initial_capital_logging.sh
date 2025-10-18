#!/bin/bash
# Test script to verify initial capital logging for Pure Lending strategy
# This script runs a backtest and shows position monitor events

echo "🚀 Starting Pure Lending Backtest with Event Logging"
echo "=================================================="
echo ""
echo "This will:"
echo "1. Skip quality gates (SKIP_QUALITY_GATES=true)"
echo "2. Start backend in backtest mode"
echo "3. Run pure lending strategy"
echo "4. Show position monitor event logs"
echo ""
echo "Press Ctrl+C to stop the backend when done"
echo ""

# Export environment variable to skip quality gates
export SKIP_QUALITY_GATES=true

# Start backend in background
echo "Starting backend..."
./platform.sh dev &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to start..."
sleep 10

# Check if backend is running via health_monitor.sh
tail -f logs/health_monitor.log | grep "✅ Health check passed"

echo "Backend started successfully"
echo ""

# Run a quick backtest
echo "Running Pure Lending backtest..."
curl -X POST "http://localhost:8001/api/v1/backtest/" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "pure_lending_usdt",
    "share_class": "USDT",
    "initial_capital": 100000,
    "start_date": "2024-05-12T00:00:00Z",
    "end_date": "2024-05-13T00:00:00Z"
  }'

echo ""
echo ""
echo "=================================================="
echo "📋 Check Position Monitor Event Logs:"
echo "=================================================="
echo ""
echo "Look for these event types in the logs:"
echo "  - initial_capital_applied"
echo "  - position_delta_applied"
echo ""
echo "Logs should show:"
echo "  1. Initial capital of 100,000 USDT applied"
echo "  2. Position key: wallet:BaseToken:USDT"
echo "  3. Delta amount: 100000.0"
echo "  4. Source: initial_capital"
echo ""
echo "Backend logs: tail -f backend/logs/api.log | grep -A 5 'initial_capital'"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Keep script running until user stops it
wait $BACKEND_PID


