# Scripts & Data Pipeline Guide 📊

**Purpose**: Complete guide to data acquisition and processing  
**Status**: ✅ Production-ready data pipeline (2024-01-01 to 2025-09-18)  
**Coverage**: All data needed for component architecture  
**Last Reviewed**: October 8, 2025  
**Status**: ✅ Aligned with canonical sources (.cursor/tasks/ + MODES.md)

---

## 🚀 **Quick Start**

### **Complete Data Download** (One Command)

```bash
# Download ALL data for backtesting
python scripts/orchestrators/download_all.py --start-date 2024-01-01 --end-date 2025-09-18
```

**Downloads** (~2 hours):
- Market data (spot, futures, funding)
- AAVE protocol data (rates, oracle, risk params)
- Staking yields (oracle + seasonal)
- Gas costs
- Execution costs

**Output**: `data/` directory with all required files

---

## 📦 **Data Requirements by Component**

### **Data Provider Needs**

**For all modes**:
- Gas costs: `data/blockchain_data/gas_prices/ethereum_gas_prices_enhanced_*.csv`
- Execution costs: `data/execution_costs/execution_cost_simulation_results.csv`

**Mode-specific**:

**Pure Lending**:
- AAVE USDT rates

**BTC Basis**:
- BTC spot prices
- BTC futures (Binance, Bybit)
- BTC funding rates

**ETH Leveraged**:
- AAVE weETH/wstETH rates
- AAVE WETH rates
- weETH/wstETH oracle prices
- Staking yields
- Seasonal rewards (if rewards_mode != 'base_only')

**USDT Market-Neutral** (needs everything!):
- All ETH leveraged data +
- ETH spot prices (Binance - our USD oracle)
- ETH futures (Binance, Bybit, OKX)
- ETH funding rates (all venues)
- Ethena benchmark

---

## 🎭 **Orchestrators** (Recommended)

**Use these** for complete data acquisition:

```bash
# 1. Market Data
python scripts/orchestrators/fetch_cex_data.py --start-date 2024-01-01 --end-date 2025-09-18

# 2. AAVE Data
python scripts/orchestrators/fetch_borrow_lending_data.py --start-date 2024-01-01 --end-date 2025-09-18

# 3. Staking & Rewards
python scripts/orchestrators/run_staking_yields_analysis.py --start-date 2024-01-01 --end-date 2025-09-18

# 4. Gas & Costs
python scripts/orchestrators/fetch_all_gas_data.py --start-date 2024-01-01 --end-date 2025-09-18
python scripts/orchestrators/fetch_execution_costs.py --start-date 2024-01-01 --end-date 2025-09-18

# 5. Benchmarks
python scripts/orchestrators/run_benchmark_analysis.py --start-date 2024-02-16 --end-date 2025-09-18
```

---

## 📁 **Output Structure**

```
data/
├── market_data/
│   ├── spot_prices/
│   │   ├── eth_usd/                # ETH/USDT (Binance spot - our USD oracle!)
│   │   ├── btc_usd/                # BTC/USDT
│   │   ├── lst_eth_ratios/         # weETH/WETH, wstETH/WETH
│   │   └── protocol_tokens/        # EIGEN, ETHFI
│   └── derivatives/
│       ├── futures_ohlcv/          # Perpetual futures (per exchange!)
│       └── funding_rates/          # Funding rates (per exchange)
│
├── protocol_data/
│   ├── aave/
│   │   ├── rates/                  # Supply/borrow rates (hourly, with indices!)
│   │   ├── oracle/                 # Oracle prices (weETH/ETH, wstETH/ETH)
│   │   └── risk_params/            # LTV, liquidation thresholds
│   └── staking/
│       ├── base_yields/            # Oracle-based base yields
│       ├── restaking_final/        # EIGEN + ETHFI distributions
│       └── benchmark_yields/       # Ethena sUSDE
│
├── blockchain_data/
│   └── gas_prices/                 # Historical gas prices (Alchemy)
│
├── execution_costs/
│   ├── lookup_tables/              # Execution cost lookup
│   └── execution_cost_simulation_results.csv
│
└── manual_sources/                 # 🔒 PROTECTED
    ├── etherfi_distributions/      # EIGEN/ETHFI raw data
    └── benchmark_data/             # Ethena manual backups
```

---

## 🔑 **Critical Data Files**

**For Data Provider component**:

**AAVE Rates** (with indices!):
```
data/protocol_data/aave/rates/aave_v3_aave-v3-ethereum_weETH_rates_2024-05-12_2025-09-18_hourly.csv
Columns: liquidityIndex, variableBorrowIndex, liquidity_growth_factor, ...
NOTE: Indices already normalized (~1.0, NOT 1e27)!
```

**AAVE Oracles**:
```
data/protocol_data/aave/oracle/weETH_ETH_oracle_2024-01-01_2025-09-18.csv
Columns: oracle_price_eth (weETH/ETH ratio)
```

**Futures Prices** (per exchange - CRITICAL!):
```
data/market_data/derivatives/futures_ohlcv/binance_ETHUSDT_perp_1h_2024-01-01_2025-09-26.csv
data/market_data/derivatives/futures_ohlcv/bybit_ETHUSDT_perp_1h_2024-01-01_2025-09-26.csv
data/market_data/derivatives/futures_ohlcv/okx_ETHUSDT_perp_1h_2024-08-01_2025-09-18.csv
NOTE: OKX incomplete - Data Provider proxies to Binance
```

---

## 📊 **Data Quality Notes**

**AAVE Indices**: Normalized in our data
- liquidityIndex: ~1.0 (not 1e27)
- variableBorrowIndex: ~1.0 (not 1e27)
- **No division needed** - use directly!

**Per-Exchange Prices**: Each exchange different
- Binance futures ≠ Bybit futures (typically $0.50-2.00 apart)
- Must load separately, not share prices!

**Hourly Alignment**: All data on the hour
- minute=0, second=0, UTC timezone
- Data Provider enforces this!

**OKX Data**: Incomplete
- Futures OHLCV: Missing for most periods
- Funding rates: Available
- **Solution**: Proxy OKX futures to Binance

---

## 🔧 **API Keys Required**

**In `backend/env.unified`**:

```bash
# CoinGecko Pro (for pool data)
BASIS_DOWNLOADERS__COINGECKO_API_KEY=CG-3qHwRgju7B2y43a1CxwYpY4q

# AaveScan Pro (for AAVE data)
BASIS_DOWNLOADERS__AAVESCAN_API_KEY=c2b49a72-9c73-48f9-aea2-5f6d8ec793b9

# Alchemy (for gas data)
BASIS_DOWNLOADERS__ALCHEMY_API_KEY=vV3z-UCRtQvWb26MH9v7A
```

---

## 🧪 **Testing Data Download**

```bash
# Quick test (7 days)
python scripts/orchestrators/download_all.py --quick-test

# Individual component test
python scripts/orchestrators/fetch_cex_data.py --start-date 2024-09-01 --end-date 2024-09-07 --quick-test
```

---

## 📊 **Data Completeness**

**Current Coverage**: 2024-01-01 to 2025-09-18 (626 days)

**Gaps**:
- OKX futures OHLCV: Use Binance proxy
- weETH data: Starts 2024-05-12 (token launch)
- Seasonal rewards: Start 2024-08-15 (first distribution)

**All gaps handled** by Data Provider (fallbacks, proxies, validation)

---

**Status**: Scripts & data pipeline documented! ✅


