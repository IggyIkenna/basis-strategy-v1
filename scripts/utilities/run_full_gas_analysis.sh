#!/bin/bash
# Run full gas cost analysis for the entire data range

# Set paths
GAS_DATA="data/blockchain_data/gas_prices/ethereum_gas_prices_2024-01-01_2025-09-24.csv"
ETH_PRICE="data/market_data/spot_prices/eth_usd/ETHUSDT_1h_2024-01-01_2025-09-18.csv"
OUTPUT_DIR="data/blockchain_data/gas_prices"

# Check if files exist
if [ ! -f "$GAS_DATA" ]; then
    echo "❌ Gas data file not found: $GAS_DATA"
    exit 1
fi

if [ ! -f "$ETH_PRICE" ]; then
    echo "❌ ETH price file not found: $ETH_PRICE"
    exit 1
fi

echo "🚀 Running full gas cost analysis for 2024-01-01 to 2025-09-24..."
echo "📊 Gas data: $GAS_DATA"
echo "💰 ETH price: $ETH_PRICE"
echo "📁 Output directory: $OUTPUT_DIR"

# Run the analysis script
python scripts/analyzers/analyze_gas_costs.py \
    --gas-file "$GAS_DATA" \
    --eth-price-file "$ETH_PRICE" \
    --output-dir "$OUTPUT_DIR"

# Check if successful
if [ $? -eq 0 ]; then
    echo "✅ Full gas cost analysis completed successfully!"
    echo "📊 Results saved to $OUTPUT_DIR"
else
    echo "❌ Error running gas cost analysis"
    exit 1
fi

# Generate a quick summary of the results
echo -e "\n📝 Quick Summary:"
echo "--------------------"
echo "Operation costs at median gas price:"

# Extract median gas price from the summary file
SUMMARY_FILE="$OUTPUT_DIR/operation_gas_costs_summary_2024-01-01_2025-09-24.json"
if [ -f "$SUMMARY_FILE" ]; then
    MEDIAN_GAS=$(grep -o '"median_gwei": [0-9.]*' "$SUMMARY_FILE" | head -1 | cut -d' ' -f2)
    echo "Median gas price: $MEDIAN_GAS Gwei"
    
    # Show costs for key operations
    echo -e "\nKey operation costs:"
    echo "--------------------"
    echo "STAKE_DEPOSIT (150K gas): ~$((150000 * $MEDIAN_GAS / 1000)) USD"
    echo "LOAN_CREATED (300K gas): ~$((300000 * $MEDIAN_GAS / 1000)) USD"
    echo "TRADE_EXECUTED (180K gas): ~$((180000 * $MEDIAN_GAS / 1000)) USD"
fi

echo -e "\n🎯 Next steps:"
echo "1. Import these costs into your backtesting engine"
echo "2. Use for accurate P&L calculations"
echo "3. Optimize strategies based on real gas costs"
