#!/bin/bash
# Load environment variables from backend/env.downloaders
# Usage: source scripts/load_env.sh

# Simple approach - assume we're running from project root
ENV_FILE="env.downloaders"

if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from $ENV_FILE"
    
    # Read the env file and export variables
    while IFS= read -r line; do
        # Skip empty lines and comments
        if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
            # Export the variable
            export "$line"
        fi
    done < "$ENV_FILE"
    
    echo "✅ Environment variables loaded successfully"
    echo "🔑 CoinGecko API Key: ${BASIS_DOWNLOADERS__COINGECKO_API_KEY:0:10}..."
else
    echo "❌ Environment file not found: $ENV_FILE"
    exit 1
fi
