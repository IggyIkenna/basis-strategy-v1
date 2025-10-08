# Component Spec: Data Provider 📡

**Component**: Data Provider  
**Responsibility**: Load and provide market data with hourly alignment enforcement  
**Priority**: ⭐⭐⭐ CRITICAL (All components need market data)  
**Backend File**: `backend/src/basis_strategy_v1/infrastructure/data/historical_data_provider.py`

---

## 🎯 **Purpose**

Provide market data (prices, rates, indices) to all components.

**Key Principles**:
- **Hourly alignment**: For backtest ALL data must be on the hour UTC timezone (minute=0, second=0)
- **Mode-aware loading**: Only load data needed for the mode
- **Per-exchange data**: Track separate prices per CEX (Binance ≠ Bybit ≠ OKX)
- **OKX Data Policy**: Use OKX funding rates only (full range available), proxy Binance data for OKX futures/spot
- **Backtest**: Load from CSV files
- **Live**: Query from WebSocket/REST APIs

**Data Flow Integration**:
- **Initialization**: Loads all data in `_load_data_for_mode()` method
- **Component Access**: Components receive market data via `market_data=data_row.to_dict()` in `_process_timestamp()`
- **No Direct Dependencies**: Components don't hold DataProvider references, receive data as parameters

**Does NOT**:
- Calculate anything (pure data access)
- Track state (stateless lookups)
- Make decisions (just provides data)

---

## 📊 **Data Structures**

### **Loaded Data** (Internal state)

```python
{
    # Spot prices (ETH/USDT oracle for perp comparison)
    'eth_spot_binance': pd.DataFrame,  # Binance spot (our ETH/USDT oracle)
    'eth_spot_uniswap': pd.DataFrame,  # Uniswap (alternative)
    'btc_spot_binance': pd.DataFrame,  # BTC spot
    
    # AAVE rates (supply/borrow rates + indices)
    'weeth_rates': pd.DataFrame,      # Columns: liquidity_apy, liquidityIndex, liquidity_growth_factor
    'wsteth_rates': pd.DataFrame,
    'weth_rates': pd.DataFrame,       # Columns: borrow_apy, variableBorrowIndex, borrow_growth_factor
    'usdt_rates': pd.DataFrame,
    
    # AAVE oracles (LST/ETH cross-rates)
    'weeth_oracle': pd.DataFrame,     # weETH/ETH AAVE oracle price
    'wsteth_oracle': pd.DataFrame,    # wstETH/ETH AAVE oracle price
    
    # CEX futures (per exchange - SEPARATE dataframes!)
    'binance_futures': pd.DataFrame,  # Columns: open, high, low, close, volume
    'bybit_futures': pd.DataFrame,
    'okx_futures': pd.DataFrame,  # Proxied from Binance data (OKX futures not used)
    
    # Funding rates (per exchange)
    'binance_funding': pd.DataFrame,  # Columns: funding_rate, funding_timestamp
    'bybit_funding': pd.DataFrame,
    'okx_funding': pd.DataFrame,
    
    # Costs
    'gas_costs': pd.DataFrame,        # Columns: gas_price_avg_gwei, CREATE_LST_eth, COLLATERAL_SUPPLIED_eth, etc.
    'execution_costs': pd.DataFrame,  # Columns: pair, size_bucket, venue_type, execution_cost_bps
    
    # Staking & rewards (weETH only - derived from oracle price changes)
    'seasonal_rewards': pd.DataFrame, # EIGEN + ETHFI distributions (weETH restaking only)
    
    # Protocol token prices (for KING unwrapping)
    'eigen_usdt': pd.DataFrame,       # EIGEN/USDT spot prices
    'ethfi_usdt': pd.DataFrame,       # ETHFI/USDT spot prices
    
    # Benchmarks
    'ethena_benchmark': pd.DataFrame  # sUSDE APR for comparison
}
```

### **Output: Market Data Snapshot**

```python
{
    'timestamp': pd.Timestamp('2024-05-12 14:00:00', tz='UTC'),
    
    # Spot prices
    'eth_usd_price': 3305.20,
    'btc_usd_price': 67250.00,
    
    # AAVE rates
    'weeth_supply_apy': 0.0374,
    'weeth_liquidity_index': 1.0234,
    'weeth_growth_factor': 1.0000042,  # Hourly
    'weth_borrow_apy': 0.0273,
    'weth_borrow_index': 1.0187,
    'weth_borrow_growth_factor': 1.0000031,
    
    # AAVE oracles
    'weeth_eth_oracle': 1.0254,
    
    # Futures prices (per exchange!)
    'binance_eth_perp': 3305.20,
    'bybit_eth_perp': 3306.15,
    'okx_eth_perp': 3305.20,  # Proxied from Binance
    
    # Funding rates (per exchange)
    'binance_funding_rate': 0.0001,
    'bybit_funding_rate': 0.00012,
    'okx_funding_rate': 0.00011,
    
    # Gas costs
    'gas_price_gwei': 12.5,
    'create_lst_cost_eth': 0.001875,
    'collateral_supplied_cost_eth': 0.003125,
    
    # Execution costs (lookup by pair/size/venue)
    # Returns cost in bps for specific trade
}
```

---

## 💻 **Core Functions**

### **Initialization**

```python
class DataProvider:
    def __init__(self, data_dir: str, mode: str, execution_mode: str = 'backtest'):
        """
        Initialize data provider.
        
        Args:
            data_dir: Path to data directory (e.g., 'data/')
            mode: Strategy mode ('pure_lending', 'eth_leveraged', etc.)
            execution_mode: 'backtest' or 'live'
        """
        self.data_dir = Path(data_dir)
        self.mode = mode
        self.execution_mode = execution_mode
        self.data = {}
        
        # Load data based on mode
        self._load_data_for_mode()
        
        # Validate hourly alignment
        self._validate_timestamps()
        
        # Live mode: Initialize WebSocket connections
        if execution_mode == 'live':
            self._init_live_data_sources()
```

### **Data Loading** (Backtest)

```python
def _load_data_for_mode(self):
    """Load only data needed for this mode."""
    
    # Always load (all modes need costs)
    self._load_gas_costs()
    self._load_execution_costs()
    
    if self.mode == 'pure_lending':
        self._load_aave_rates('USDT')
    
    elif self.mode == 'btc_basis':
        self._load_spot_prices('BTC')
        self._load_futures_data('BTC', ['binance', 'bybit'])
        self._load_funding_rates('BTC', ['binance', 'bybit', 'okx'])
    
    elif self.mode in ['eth_leveraged', 'usdt_market_neutral']:
        # AAVE data
        lst_type = self.config.get('lst_type', 'weeth')
        self._load_aave_rates(lst_type)  # weETH or wstETH
        self._load_aave_rates('WETH')
        self._load_oracle_prices(lst_type)
        
        # Staking data (weETH restaking only)
        if self.config.get('rewards_mode') != 'base_only':
            self._load_seasonal_rewards()  # EIGEN + ETHFI distributions
        
        # Protocol token prices (for KING unwrapping)
        self._load_protocol_token_prices()
        
        # If USDT mode, need CEX data
        if self.mode == 'usdt_market_neutral':
            self._load_spot_prices('ETH')  # Binance spot = our ETH/USDT oracle
            self._load_futures_data('ETH', self.config.get('hedge_venues', ['binance', 'bybit', 'okx']))
            self._load_funding_rates('ETH', self.config.get('hedge_venues'))
    
    logger.info(f"Data loaded for mode: {self.mode} ({len(self.data)} datasets)")

def _load_aave_rates(self, asset: str):
    """Load AAVE rates with hourly validation."""
    # Hardcoded file paths (as agreed)
    file_map = {
        'weETH': 'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_weETH_rates_2024-05-12_2025-09-18_hourly.csv',
        'wstETH': 'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_wstETH_rates_2024-01-01_2025-09-18_hourly.csv',
        'WETH': 'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_WETH_rates_2024-01-01_2025-09-18_hourly.csv',
        'USDT': 'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_USDT_rates_2024-01-01_2025-09-18_hourly.csv'
    }
    
    file_path = self.data_dir / file_map[asset]
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.set_index('timestamp').sort_index()
    
    # Validate hourly
    if not all(df.index.minute == 0):
        raise ValueError(f"{asset} rates: Timestamps must be on the hour!")
    
    self.data[f'{asset.lower()}_rates'] = df
```

### **Data Access** (Backtest)

```python
def get_spot_price(self, asset: str, timestamp: pd.Timestamp) -> float:
    """Get spot price at timestamp (asof lookup)."""
    if asset == 'ETH':
        data = self.data['eth_spot_binance']  # Our ETH/USDT oracle
    elif asset == 'BTC':
        data = self.data['btc_spot_binance']
    
    ts = data.index.asof(timestamp)
    if pd.isna(ts):
        ts = data.index[0]  # Fallback to first
    
    return data.loc[ts, 'open']  # Use candle open (start of hour)

def get_futures_price(self, asset: str, venue: str, timestamp: pd.Timestamp) -> float:
    """
    Get futures price for specific exchange.
    
    CRITICAL: Each exchange has different prices!
    """
    data_key = f'{venue.lower()}_futures'
    
    if data_key not in self.data:
        # OKX might not have data, use Binance as proxy
        logger.warning(f"{venue} futures data not available, using binance proxy")
        data_key = 'binance_futures'
    
    data = self.data[data_key]
    ts = data.index.asof(timestamp)
    if pd.isna(ts):
        ts = data.index[0]
    
    return data.loc[ts, 'open']  # Open price for entry, close for mark

def get_aave_index(self, asset: str, index_type: str, timestamp: pd.Timestamp) -> float:
    """
    Get AAVE liquidity or borrow index.
    
    CRITICAL: Indices in our data are NORMALIZED (~1.0, not 1e27)!
    """
    data_key = f'{asset.lower()}_rates'
    data = self.data[data_key]
    
    ts = data.index.asof(timestamp)
    if pd.isna(ts):
        ts = data.index[0]
    
    if index_type == 'liquidity':
        return data.loc[ts, 'liquidityIndex']  # Already normalized ~1.0
    elif index_type == 'borrow':
        return data.loc[ts, 'variableBorrowIndex']  # Already normalized ~1.0
    
    # NO division by 1e27 needed (data already normalized!)

def get_oracle_price(self, lst_type: str, timestamp: pd.Timestamp) -> float:
    """Get LST/ETH oracle price from AAVE oracles (for staked spread tracking)."""
    data_key = f'{lst_type.lower()}_oracle'
    data = self.data[data_key]
    
    ts = data.index.asof(timestamp)
    if pd.isna(ts):
        ts = data.index[0]
    
    return data.loc[ts, 'oracle_price_eth']  # weETH/ETH or wstETH/ETH
```

### **Data Access** (Live Mode)

```python
async def get_spot_price_live(self, asset: str) -> float:
    """Live mode: Get current spot price from WebSocket."""
    # Subscribe to price feeds
    if not hasattr(self, 'price_ws'):
        self._init_price_websocket()
    
    # Get from WebSocket cache (updated real-time)
    return self.price_cache[f'{asset}/USDT']

async def get_aave_index_live(self, asset: str, index_type: str) -> float:
    """Live mode: Query AAVE contract for current index."""
    if index_type == 'liquidity':
        # Query AAVE v3 pool contract
        index_raw = await self.aave_pool.getReserveNormalizedIncome(asset_address)
        # Normalize from ray (1e27) to decimal
        return index_raw / 1e27
    elif index_type == 'borrow':
        index_raw = await self.aave_pool.getReserveNormalizedVariableDebt(asset_address)
        return index_raw / 1e27

async def get_futures_price_live(self, asset: str, venue: str) -> float:
    """Live mode: Get current mark price from exchange WebSocket."""
    # Subscribe to mark price feed
    return self.futures_price_cache[f'{venue}:{asset}USDT-PERP']
```

---

## 🔗 **Integration**

### **Provides Data To** (Downstream):
- **Exposure Monitor** ← Prices, indices, oracles
- **Risk Monitor** ← Prices (for valuation)
- **P&L Calculator** ← Prices, indices
- **CEX Execution Manager** ← Futures prices (for simulation)
- **OnChain Execution Manager** ← Gas costs, oracle prices

### **Data Sources**:
**Backtest**:
- CSV files in `data/` directory (hardcoded paths)

**Live**:
- Binance WebSocket (spot prices, futures prices, funding rates)
- Bybit WebSocket (futures prices, funding rates)
- OKX WebSocket (funding rates)
- Web3 RPC (AAVE contract queries for indices)

---

## 🔧 **Mode-Specific Data Loading**

```python
MODE_DATA_REQUIREMENTS = {
    'pure_lending': [
        'usdt_rates',  # AAVE USDT supply rates
        'gas_costs'
    ],
    'btc_basis': [
        'btc_spot_binance',
        'binance_futures',  # BTC futures
        'bybit_futures',    # BTC futures
        'binance_funding',  # BTC funding
        'bybit_funding',
        'okx_funding',
        'execution_costs'
    ],
    'eth_leveraged': [
        'eth_spot_binance',  # Only if USDT share class
        'weeth_rates',  # or wsteth_rates
        'weth_rates',
        'weeth_oracle',  # or wsteth_oracle
        'seasonal_rewards',  # Only if rewards_mode != 'base_only'
        'eigen_usdt',
        'ethfi_usdt',
        'gas_costs',
        'execution_costs',
        # CEX data only if USDT share class
        'binance_futures',
        'bybit_futures',
        'okx_futures',
        'binance_funding',
        'bybit_funding',
        'okx_funding'
    ],
    'usdt_market_neutral': [
        # All of the above!
        'eth_spot_binance',
        'weeth_rates',
        'weth_rates',
        'weeth_oracle',
        'seasonal_rewards',
        'eigen_usdt',
        'ethfi_usdt',
        'binance_futures',
        'bybit_futures',
        'okx_futures',
        'binance_funding',
        'bybit_funding',
        'okx_funding',
        'gas_costs',
        'execution_costs',
        'ethena_benchmark'
    ]
}
```

---

## ⏰ **Timestamp Validation**

```python
def _validate_timestamps(self):
    """Ensure ALL data is on the hour."""
    for key, df in self.data.items():
        if not isinstance(df, pd.DataFrame):
            continue
        
        if not df.index.name == 'timestamp':
            raise ValueError(f"{key}: Index must be 'timestamp'")
        
        # Check hourly alignment
        if not all(df.index.minute == 0):
            bad_timestamps = df.index[df.index.minute != 0]
            raise ValueError(
                f"{key}: {len(bad_timestamps)} timestamps not on the hour!\n"
                f"First bad timestamp: {bad_timestamps[0]}"
            )
        
        if not all(df.index.second == 0):
            raise ValueError(f"{key}: Timestamps must have second=0")
        
        # Check UTC timezone
        if df.index.tz is None:
            raise ValueError(f"{key}: Timestamps must be UTC timezone-aware")
        
        logger.info(f"✅ {key}: {len(df)} hourly timestamps validated")

def validate_data_synchronization(self):
    """Validate all data sources have overlapping periods."""
    ranges = {}
    for key, df in self.data.items():
        if isinstance(df, pd.DataFrame):
            ranges[key] = (df.index.min(), df.index.max())
    
    # Find common period
    common_start = max(r[0] for r in ranges.values())
    common_end = min(r[1] for r in ranges.values())
    
    logger.info(f"Common data period: {common_start} to {common_end}")
    
    # Warn about gaps
    for key, df in self.data.items():
        if not isinstance(df, pd.DataFrame):
            continue
        
        expected = pd.date_range(common_start, common_end, freq='H')
        actual = df.index
        missing = expected.difference(actual)
        
        if len(missing) > 0:
            logger.warning(f"{key}: {len(missing)} missing hours in common period")
    
    return {'common_start': common_start, 'common_end': common_end}
```

---

## 🧪 **Testing**

```python
def test_hourly_alignment():
    """Test all data is on the hour."""
    provider = DataProvider('data', 'usdt_market_neutral')
    
    # Check each dataset
    for key, df in provider.data.items():
        assert all(df.index.minute == 0), f"{key} has non-hourly timestamps"
        assert all(df.index.second == 0)

def test_per_exchange_futures_prices():
    """Test separate futures prices per exchange."""
    provider = DataProvider('data', 'usdt_market_neutral')
    
    timestamp = pd.Timestamp('2024-08-15 12:00:00', tz='UTC')
    
    binance_price = provider.get_futures_price('ETH', 'binance', timestamp)
    bybit_price = provider.get_futures_price('ETH', 'bybit', timestamp)
    
    # Should be different (typically $0.50-2.00 apart)
    assert binance_price != bybit_price
    assert abs(binance_price - bybit_price) < 10  # Not too different

def test_aave_index_normalized():
    """Test indices are already normalized (~1.0, not 1e27)."""
    provider = DataProvider('data', 'eth_leveraged')
    
    timestamp = pd.Timestamp('2024-05-12 00:00:00', tz='UTC')
    index = provider.get_aave_index('weETH', 'liquidity', timestamp)
    
    # Should be around 1.0 (not 1e27!)
    assert 0.9 < index < 1.2, f"Index should be ~1.0, got {index}"
```

---

## 🔄 **Backtest vs Live**

### **Backtest**:
- Load all CSV files at initialization
- asof() lookups (fast, deterministic)
- No WebSocket connections
- Cacheall data in memory

### **Live**:
- Initialize WebSocket connections
- Subscribe to real-time feeds
- Query AAVE contracts for indices
- Cache latest values
- Hourly batch queries for historical (if needed)

### **New Data Loading Methods**

```python
def _load_seasonal_rewards(self):
    """Load seasonal rewards data (weETH restaking only)."""
    file_path = os.path.join(self.data_dir, "protocol_data/staking/restaking_final/etherfi_seasonal_rewards_2024-01-01_2025-09-18.csv")
    df = _validate_data_file(file_path)
    self.seasonal_rewards = df

def _load_protocol_token_prices(self):
    """Load protocol token prices for KING unwrapping."""
    # EIGEN/USDT
    eigen_path = os.path.join(self.data_dir, "market_data/spot_prices/protocol_tokens/binance_EIGENUSDT_1h_2024-10-05_2025-09-30.csv")
    self.eigen_usdt = _validate_data_file(eigen_path)
    
    # ETHFI/USDT
    ethfi_path = os.path.join(self.data_dir, "market_data/spot_prices/protocol_tokens/binance_ETHFIUSDT_1h_2024-06-01_2025-09-30.csv")
    self.ethfi_usdt = _validate_data_file(ethfi_path)

def _load_benchmark_data(self):
    """Load benchmark data for comparison."""
    file_path = os.path.join(self.data_dir, "protocol_data/staking/benchmark_yields/ethena_susde_apr_benchmark_hourly_2024-02-16_2025-09-18.csv")
    self.ethena_benchmark = _validate_data_file(file_path)
```

---

## 🎯 **Success Criteria**

- [ ] Enforces hourly timestamp alignment
- [ ] Loads only data needed for mode
- [ ] Tracks separate prices per exchange
- [ ] AAVE indices used correctly (normalized, not raw 1e27)
- [ ] Fast asof() lookups
- [ ] Validates data synchronization
- [ ] OKX data policy: funding rates only, proxy Binance for futures/spot
- [ ] Protocol token prices loaded for KING unwrapping
- [ ] Benchmark data loaded for comparison
- [ ] Live mode: WebSocket + contract queries
- [ ] No conversions (just data access)

---

**Status**: Specification complete! ✅


