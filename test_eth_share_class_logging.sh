#!/bin/bash
# Test script to verify ETH share class logging for Position Monitor and Exposure Monitor
# This script runs a backtest with ETH share class and shows position/exposure events

echo "🚀 Starting ETH Share Class Backtest with Event Logging"
echo "=================================================="
echo ""
echo "This will:"
echo "1. Skip quality gates (SKIP_QUALITY_GATES=true)"
echo "2. Start backend in backtest mode"
echo "3. Run pure lending strategy with ETH share class"
echo "4. Show position monitor and exposure monitor event logs"
echo ""
echo "Press Ctrl+C to stop the backend when done"
echo ""

export SKIP_QUALITY_GATES=true

echo "Starting backend..."
./platform.sh backtest &
BACKEND_PID=$!

echo "Waiting for backend to start..."
sleep 10

if ! curl -s http://localhost:8001/health/ > /dev/null 2>&1; then
    echo "❌ Backend failed to start. Check logs: tail -f backend/logs/api.log"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Backend started successfully"
echo ""

echo "Running ETH Share Class backtest..."
curl -X POST "http://localhost:8001/api/v1/backtest/" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "pure_lending_eth",
    "share_class": "ETH",
    "initial_capital": 50,
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
echo "  - initial_capital_applied (should show ETH amounts)"
echo "  - position_delta_applied (should show ETH amounts)"
echo ""
echo "Logs should show:"
echo "  1. Initial capital of 50 ETH applied"
echo "  2. Position key: wallet:BaseToken:ETH"
echo "  3. Delta amount: 50.0 ETH"
echo "  4. Source: initial_capital"
echo ""
echo "=================================================="
echo "📊 Check Exposure Monitor Event Logs:"
echo "=================================================="
echo ""
echo "Look for these event types in the logs:"
echo "  - exposure_calculated (should show USD and ETH values)"
echo "  - instrument_exposures (should show both USD and ETH)"
echo ""
echo "Logs should show:"
echo "  1. Total value in USD (e.g., ~$150,000 at $3,000/ETH)"
echo "  2. Share class value in ETH (50.0 ETH)"
echo "  3. Instrument exposures with both USD and ETH values"
echo ""
echo "Backend logs: tail -f backend/logs/api.log | grep -E '(initial_capital|exposure_calculated|instrument_exposures)'"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Wait for user to check logs
wait $BACKEND_PID
