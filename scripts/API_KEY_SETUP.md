# API Key Setup Guide

This guide explains how to set up API keys for all the data downloaders in this project.

## 🔑 Required API Keys

The following API keys are required for full functionality:

1. **CoinGecko Pro API** - For historical pool data beyond 180 days
2. **Alchemy API** - For Ethereum RPC access and gas price data
3. **AaveScan Pro API** - For AAVE lending protocol data (optional)

## 📋 Setup Instructions

### 1. Get API Keys

#### CoinGecko Pro API
- **URL**: https://www.coingecko.com/en/api/pricing
- **Plan**: Analyst Plan (500 requests/minute)
- **Purpose**: Historical pool data access beyond 180-day public limit

#### Alchemy API
- **URL**: https://www.alchemy.com/
- **Plan**: Free tier or higher
- **Purpose**: Ethereum RPC access for gas price data
- **Note**: Get 2 keys for round-robin load balancing

#### AaveScan Pro API (Optional)
- **URL**: https://aavescan.com/pricing
- **Plan**: Advanced Plan
- **Purpose**: AAVE v3 historical lending/borrowing rates

### 2. Add Keys to Environment File

Edit `backend/env.unified` and add your API keys:

```bash
# Data Downloader API Keys
BASIS_DOWNLOADERS__COINGECKO_API_KEY=your_coingecko_api_key_here
BASIS_DOWNLOADERS__ALCHEMY_API_KEY=your_first_alchemy_key_here
BASIS_DOWNLOADERS__ALCHEMY_API_KEY_2=your_second_alchemy_key_here
BASIS_DOWNLOADERS__AAVESCAN_API_KEY=your_aavescan_api_key_here
```

### 3. Load Environment Variables

Before running any downloader scripts, load the environment variables:

```bash
# From project root
source scripts/load_env.sh

# Test with a quick download
python scripts/orchestrators/download_all.py --quick-test

# Test AAVE data pipeline
python scripts/orchestrators/fetch_borrow_lending_data.py --quick-test
```

Or manually export them:

```bash
export BASIS_DOWNLOADERS__COINGECKO_API_KEY=your_api_key_here
export BASIS_DOWNLOADERS__ALCHEMY_API_KEY=your_api_key_here
# ... etc
```

## 🚀 Usage Examples

### CoinGecko Pool Data (with API key)
```bash
# Load environment variables
source scripts/load_env.sh

# Run pool data orchestrator
python scripts/orchestrators/fetch_pool_data.py --start-date 2020-01-01

# Run individual downloaders
python scripts/downloaders/fetch_spot_pool_data.py --start-date 2020-01-01
python scripts/downloaders/fetch_lst_pool_data.py --start-date 2020-01-01
```

### Alchemy Gas Data (with API keys)
```bash
# Load environment variables
source scripts/load_env.sh

# Run gas price downloader
python scripts/downloaders/clients/alchemy_client_fast.py
```

### AAVE Data Pipeline (with API key)
```bash
# Load environment variables
source scripts/load_env.sh

# Run complete AAVE data pipeline
python scripts/orchestrators/fetch_borrow_lending_data.py --start-date 2024-01-01 --end-date 2025-09-26

# Run individual AAVE components
python scripts/downloaders/fetch_aave_data.py --start-date 2024-01-01 --end-date 2025-09-26
python scripts/processors/process_aave_oracle_prices.py
python scripts/utilities/create_aave_risk_params.py
python scripts/analyzers/analyze_aave_rate_impact.py --create-plots
```

## ⚠️ Without API Keys

### CoinGecko
- **Fallback**: Public API (180-day limit only)
- **Impact**: Cannot access historical data from pool creation dates
- **Example**: ETH/USDT pool created 2025-01-27, but only data from ~2025-03-30 available

### Alchemy
- **Fallback**: Hardcoded API keys (may have rate limits)
- **Impact**: Reduced performance and potential rate limiting

### AaveScan
- **Fallback**: Placeholder mode with sample data
- **Impact**: No real AAVE data, only test data structure

## 🔧 Troubleshooting

### "API key not found" Error
```bash
# Check if environment variables are loaded
echo $BASIS_DOWNLOADERS__COINGECKO_API_KEY

# If empty, load them:
source scripts/load_env.sh
```

### "401 Unauthorized" Error
- Check if API key is correct
- Verify API key has sufficient permissions
- Check rate limits (CoinGecko: 500 req/min)

### "180-day limit" Error
- This means you're using the public API instead of Pro API
- Ensure CoinGecko Pro API key is loaded
- Check that `BASIS_DOWNLOADERS__COINGECKO_API_KEY` is set

## 📊 API Key Status Check

You can check which API keys are loaded:

```bash
source scripts/load_env.sh
echo "CoinGecko: ${BASIS_DOWNLOADERS__COINGECKO_API_KEY:0:10}..."
echo "Alchemy 1: ${BASIS_DOWNLOADERS__ALCHEMY_API_KEY:0:10}..."
echo "Alchemy 2: ${BASIS_DOWNLOADERS__ALCHEMY_API_KEY_2:0:10}..."
echo "AaveScan: ${BASIS_DOWNLOADERS__AAVESCAN_API_KEY:0:10}..."
```

## 🎯 Quick Start

1. **Get API keys** from the providers above
2. **Add to `backend/env.unified`** following the format shown
3. **Load environment**: `source scripts/load_env.sh`
4. **Run downloaders**: `python scripts/orchestrators/fetch_pool_data.py --start-date 2020-01-01`

This will give you full historical access to all pool data from creation dates!
