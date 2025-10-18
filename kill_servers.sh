#!/bin/bash
# Kill all uvicorn processes related to this project

echo "Killing all uvicorn processes..."
pkill -f "uvicorn.*basis_strategy_v1" || echo "No uvicorn processes found"

# Wait a moment for processes to terminate
sleep 1

# Check if any processes are still running
if pgrep -f "uvicorn.*basis_strategy_v1" > /dev/null; then
    echo "Some processes still running, force killing..."
    pkill -9 -f "uvicorn.*basis_strategy_v1"
fi

echo "All server processes killed. You can now start debugging."
