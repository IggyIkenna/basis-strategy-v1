"""
Unified Pool Data Downloader

Downloads OHLCV data for spot trading pairs and LST pools using GeckoTerminal API.

🎯 STRATEGIC POOL SELECTION RATIONALE:

SPOT TRADING PAIRS (WETH/USDT, EIGEN/WETH, ETHFI/WETH):
- **Backtesting**: Using Uniswap v3 pools for maximum historical coverage (2020+)
- **Live Trading**: Will migrate to cheaper Uniswap v4 pools or CEX for better execution
- **Alternative**: Binance spot data available for protocol tokens (EIGEN/ETHFI)
- **Decision**: DEX pools provide more realistic slippage modeling for backtesting

LST POOLS (wstETH/WETH, weETH/WETH):
- **Backtesting**: Using both Uniswap v3 (0.01% fee) and Curve (weeth-ng) pools
- **Live Trading**: Will choose optimal pool based on liquidity, fees, and slippage
- **Uniswap v3**: Better for smaller amounts, more predictable slippage
- **Curve**: Better for larger amounts, potentially lower slippage
- **Decision**: Keep both for comprehensive backtesting and production flexibility

POOL DETAILS:
Spot Trading Pairs:
- 0x4e68ccd3e89f51c3074ca5072bbac773960dfa36 (WETH/USDT Uniswap v3 0.3%, since May 5, 2020)
- 0xc2c390c6cd3c4e6c2b70727d35a45e8a072f18ca (EIGEN/WETH Uniswap v3 0.3%, since Oct 5, 2024)
- 0x06f00544c0bc62e6db10f46d370dfccdc23d8189 (ETHFI/WETH Uniswap v3 0.3%, since Apr 1, 2024)

LST Pools:
- 0x109830a1aaad605bbf02a9dfa7b0b92ec2fb7daa (wstETH/WETH Uniswap v3 0.01%, since Mar 28, 2024)
- 0xdb74dfdd3bb46be8ce6c33dc9d82777bcfc3ded5 (weETH/WETH Curve weeth-ng, since May 10, 2024)

Features:
- Direct pool OHLCV data (no cross-conversion needed)
- Hourly candles with WETH/USDT prices, protocol token ratios, and LST ratios
- Full historical data via CoinGecko Pro API (500 req/min)
- Optimized pagination (1000 records per request, ~6-week chunks for hourly)
- Gap-filling for complete timeline
- Maximum historical coverage using Uniswap v3 pools only
- Automatic output directory organization (eth_usd, protocol_tokens, lst_eth_ratios)

Pro API Benefits:
- Complete historical data from pool creation dates
- WETH/USDT: Data from 2020-05-05 onwards (Uniswap v3 launch)
- Much faster rate limits (500 req/min vs 30 req/min public)
- Longest possible backtest history for strategy development

🔑 API KEY SETUP REQUIRED:
This script requires a CoinGecko Pro API key for historical data access beyond 180 days.

1. Get a CoinGecko Pro API key from: https://www.coingecko.com/en/api/pricing
2. Add it to backend/env.unified:
   BASIS_DOWNLOADERS__COINGECKO_API_KEY=your_api_key_here

3. Load environment variables before running:
   source scripts/load_env.sh
   python scripts/downloaders/fetch_spot_pool_data.py --start-date 2020-01-01

⚠️  WITHOUT API KEY: Falls back to public API (180-day limit only)
✅  WITH API KEY: Full historical access from pool creation dates
"""

import asyncio
import csv
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import logging

# Handle both standalone and module imports
try:
    from .clients.coingecko_client import CoinGeckoClient
except ImportError:
    # Standalone execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from clients.coingecko_client import CoinGeckoClient


class SpotDataDownloader:
    """
    Focused downloader for specific spot pools using GeckoTerminal.
    
    Features:
    - Direct pool data (no coin ID mapping needed)
    - ETH/USDT spot prices
    - Full historical data with pagination
    - Rate limiting for Pro API
    - Gap-filling for complete timeline
    """
    
    def __init__(self, output_dir: str = "data/market_data/spot_prices"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger("spot_data_downloader")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Target pools (spot trading pairs + LST pools)
        self.pools = [
            # Spot trading pairs
            "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",  # WETH/USDT Uniswap v3 0.3%
            "0xc2c390c6cd3c4e6c2b70727d35a45e8a072f18ca",  # EIGEN/WETH Uniswap v3 0.3%
            "0x06f00544c0bc62e6db10f46d370dfccdc23d8189",  # ETHFI/WETH Uniswap v3 0.3%
            # LST pools
            "0x109830a1aaad605bbf02a9dfa7b0b92ec2fb7daa",  # wstETH/WETH Uniswap v3 0.01%
            "0xdb74dfdd3bb46be8ce6c33dc9d82777bcfc3ded5",  # weETH/WETH Curve weeth-ng pool
        ]
        
        self.network = "eth"
        self.timeframe = "hour"  # Hourly data for detailed analysis
        self.start_date = "2024-01-01"
        
        # Pool creation dates (will be set by orchestrator)
        self.pool_creation_dates = {
            "lst_pools": "2024-05-12",  # weETH pool creation date (earliest)
            "eth_usdt": "2024-01-01",   # WETH/USDT Uniswap v3 creation
            "eigen_eth": "2024-10-05",  # EIGEN/ETH Uniswap v3 creation
            "ethfi_eth": "2024-04-01"   # ETHFI/ETH Uniswap v3 creation
        }
        
        # Initialize CoinGecko client for GeckoTerminal access
        try:
            self.client = CoinGeckoClient()
            self.use_pro_api = True
            self.logger.info("✅ Using CoinGecko Pro API for full historical access")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not initialize full CoinGecko client: {e}")
            # Create a minimal client for GeckoTerminal only
            self.client = self._create_minimal_client()
            self.use_pro_api = False
            self.logger.info("📡 Using public GeckoTerminal API (limited historical access)")
        
        self.logger.info(f"Spot Data Downloader initialized")
        self.logger.info(f"Target pools: {len(self.pools)}")
        self.logger.info(f"Output directory: {self.output_dir}")
    
    def _create_minimal_client(self):
        """Create a minimal client for GeckoTerminal API only."""
        import requests
        
        class MinimalGeckoClient:
            def __init__(self):
                self.session = requests.Session()
                self.geckoterminal_base_url = "https://api.geckoterminal.com/api/v2"
            
            async def get_pool_meta(self, network: str, pool: str) -> Optional[Dict]:
                url = f"{self.geckoterminal_base_url}/networks/{network}/pools/{pool}"
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'application/json',
                        'Accept-Language': 'en-US,en;q=0.9'
                    }
                    response = self.session.get(url, headers=headers, timeout=20)
                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    logging.getLogger("minimal_gecko").error(f"Pool meta request failed: {e}")
                    return None
            
            async def get_pool_ohlcv(self, network: str, pool: str, timeframe: str = "day",
                                   aggregate: int = 1, limit: int = 1000, before_ts: int = None,
                                   currency: str = "token", token_side: str = "base") -> Optional[Dict]:
                url = f"{self.geckoterminal_base_url}/networks/{network}/pools/{pool}/ohlcv/{timeframe}"
                params = {
                    "aggregate": aggregate,
                    "limit": limit,
                    "currency": currency,
                    "token": token_side,
                }
                if before_ts:
                    params["before_timestamp"] = before_ts
                
                try:
                    # Add headers including potential CoinGecko Pro API key
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'application/json',
                        'Accept-Language': 'en-US,en;q=0.9'
                    }
                    
                    # Try to add CoinGecko Pro API key if available
                    import os
                    api_key = os.environ.get("BASIS_DOWNLOADERS__COINGECKO_API_KEY")
                    if api_key:
                        headers["x-cg-pro-api-key"] = api_key
                    
                    response = self.session.get(url, params=params, headers=headers, timeout=30)
                    
                    # Better error logging
                    if response.status_code == 401:
                        from datetime import datetime, timezone
                        logging.getLogger("minimal_gecko").warning(f"401 Unauthorized for timestamp {before_ts} ({datetime.fromtimestamp(before_ts, timezone.utc).strftime('%Y-%m-%d') if before_ts else 'current'})")
                        logging.getLogger("minimal_gecko").warning(f"URL: {url}")
                        logging.getLogger("minimal_gecko").warning(f"Params: {params}")
                    
                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    logging.getLogger("minimal_gecko").error(f"Pool OHLCV request failed: {e}")
                    return None
        
        return MinimalGeckoClient()
    
    def unix_timestamp(self, dt: datetime) -> int:
        """Convert datetime to Unix timestamp."""
        # If datetime is naive, assume it's UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        # Convert to UTC timestamp
        return int(dt.timestamp())
    
    def get_relevant_pools(self, start_date: str, end_date: str = None) -> List[str]:
        """
        Get all relevant pools for the given date range.
        
        Since we're using only Uniswap v3 pools, all pools are relevant.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), None for present
            
        Returns:
            List of all pool addresses
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        self.logger.info(f"📅 Date range: {start_date} to {end_date}")
        self.logger.info(f"🎯 Using all {len(self.pools)} Uniswap v3 pools for maximum historical coverage")
        
        return self.pools
    
    def _fill_data_gaps(self, data_rows: List[Tuple], start_unix: int, end_unix: int = None) -> List[Tuple]:
        """
        Fill gaps in hourly data with previous close price (OHLC = prev_close, volume = 0).
        
        Args:
            data_rows: List of (timestamp, open, high, low, close, volume) tuples
            start_unix: Start timestamp
            end_unix: End timestamp (None for current time)
            
        Returns:
            Complete hourly data without gaps
        """
        if not data_rows:
            return []
        
        # Determine end timestamp
        if end_unix is None:
            end_unix = self.unix_timestamp(datetime.now(timezone.utc))
        
        # Create hourly timeline from start to end
        current_time = start_unix
        hour_seconds = 3600  # 1 hour in seconds
        
        # Round start time to nearest hour
        current_time = (current_time // hour_seconds) * hour_seconds
        
        filled_data = []
        data_dict = {row[0]: row for row in data_rows}
        last_close = None
        gaps_filled = 0
        
        while current_time <= end_unix:
            if current_time in data_dict:
                # Real data exists
                row = data_dict[current_time]
                filled_data.append(row)
                last_close = row[4]  # Update last close price
            else:
                # Gap - fill with previous close
                if last_close is not None:
                    # Fill gap: OHLC = previous close, volume = 0
                    gap_row = (current_time, last_close, last_close, last_close, last_close, 0.0)
                    filled_data.append(gap_row)
                    gaps_filled += 1
                # If no previous close available, skip this gap
            
            current_time += hour_seconds
        
        if gaps_filled > 0:
            self.logger.info(f"      🔧 Filled {gaps_filled} hourly gaps with previous close prices")
        
        return filled_data
    
    async def fetch_pool_history(self, pool: str, start_unix: int, end_unix: int = None) -> List[Tuple[int, float, float, float, float, float]]:
        """
        Fetch complete pool history from start_unix to end_unix.
        
        Args:
            pool: Pool address
            start_unix: Start timestamp (Unix seconds)
            end_unix: End timestamp (Unix seconds), None for present
            
        Returns:
            List of (timestamp, open, high, low, close, volume) tuples
        """
        self.logger.info(f"📊 Fetching pool history for {pool[:10]}...")
        
        all_rows = []
        if end_unix:
            before = end_unix + 86400  # Start from day after end date
        else:
            before = self.unix_timestamp(datetime.now(timezone.utc)) + 86400  # Start from tomorrow
        
        page_count = 0
        start_time = datetime.now()
        
        while True:
            page_count += 1
            self.logger.info(f"  📄 Page {page_count}: fetching before {datetime.fromtimestamp(before, timezone.utc).strftime('%Y-%m-%d')}")
            
            # Safety check to prevent infinite loops
            if page_count > 100:  # Should never need more than 100 pages
                self.logger.error(f"  🛑 Safety stop: too many pages ({page_count})")
                break
            
            try:
                # Determine currency and token side based on pool
                if pool == "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36":
                    # WETH/USDT - use USD currency for direct USD prices
                    currency = "usd"
                    token_side = "base"
                else:
                    # All other pools (EIGEN/WETH, ETHFI/WETH, wstETH/WETH, weETH/WETH) - use token currency for direct ratios
                    currency = "token"
                    token_side = "base"
                
                # Use Pro API if available for better historical access
                if self.use_pro_api and hasattr(self.client, 'get_pool_ohlcv_pro'):
                    data = await self.client.get_pool_ohlcv_pro(
                        self.network, pool,
                        timeframe=self.timeframe, 
                        aggregate=1, 
                        limit=1000,
                        before_ts=before, 
                        currency=currency,
                        token_side=token_side
                    )
                else:
                    data = await self.client.get_pool_ohlcv(
                        self.network, pool,
                        timeframe=self.timeframe, 
                        aggregate=1, 
                        limit=1000,
                        before_ts=before, 
                        currency=currency,
                        token_side=token_side
                    )
                
                if not data or "data" not in data:
                    self.logger.warning(f"  ❌ No data returned for page {page_count}")
                    # Try without pagination to see if we can get any data
                    if page_count == 1 and before != self.unix_timestamp(datetime.now(timezone.utc)) + 86400:
                        self.logger.info(f"  🔄 Trying without pagination...")
                        data = await self.client.get_pool_ohlcv(
                            self.network, pool,
                            timeframe=self.timeframe, 
                            aggregate=1, 
                            limit=1000,
                            currency=currency, 
                            token_side=token_side
                        )
                        if data and "data" in data:
                            ohlcv_list = data["data"]["attributes"]["ohlcv_list"]
                            if ohlcv_list:
                                all_rows.extend(ohlcv_list)
                                self.logger.info(f"  ✅ Got {len(ohlcv_list)} records without pagination")
                    break
                
                ohlcv_list = data["data"]["attributes"]["ohlcv_list"]
                if not ohlcv_list:
                    self.logger.info(f"  ✅ Reached end of data at page {page_count}")
                    break
                
                all_rows.extend(ohlcv_list)
                self.logger.info(f"  ✅ Got {len(ohlcv_list)} records")
                
                # Check if we've reached our start date
                earliest = ohlcv_list[-1][0]
                earliest_date = datetime.fromtimestamp(earliest, timezone.utc).strftime('%Y-%m-%d')
                self.logger.info(f"      Earliest in this batch: {earliest_date}")
                
                if earliest <= start_unix:
                    self.logger.info(f"  🎯 Reached start date ({datetime.fromtimestamp(start_unix, timezone.utc).strftime('%Y-%m-%d')})")
                    break
                
                # Check if we got the same timestamp as before (infinite loop protection)
                if earliest == before:
                    self.logger.warning(f"  🛑 Same timestamp returned, stopping pagination")
                    break
                
                # Set up next page
                before = earliest
                
                # Rate limiting (Pro API: 500 req/min = 0.12s, Public: 30 req/min = 2s)
                if self.use_pro_api:
                    await asyncio.sleep(0.15)  # 500 req/min = 0.12s, add small buffer
                else:
                    await asyncio.sleep(2.1)  # Public API rate limit
                
            except Exception as e:
                self.logger.error(f"  ❌ Error fetching page {page_count}: {e}")
                # If it's a 401 error, try to continue with a different approach
                if "401" in str(e):
                    self.logger.warning(f"  🔄 401 error encountered, this might be the historical data limit")
                break
        
        # Filter to only include data from start_unix onwards
        filtered_rows = [row for row in all_rows if row[0] >= start_unix]
        
        # Sort by timestamp (ascending)
        filtered_rows.sort(key=lambda r: r[0])
        
        # Deduplicate by timestamp (in case of overlaps)
        dedup = {}
        for t, o, h, l, c, v in filtered_rows:
            dedup[t] = (t, o, h, l, c, v)
        
        deduplicated_rows = list(sorted(dedup.values(), key=lambda r: r[0]))
        
        # Fill gaps with previous close price
        final_rows = self._fill_data_gaps(deduplicated_rows, start_unix, end_unix)
        
        # Log completion with timing
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.logger.info(f"✅ Pool {pool[:10]}: {len(final_rows)} records after filtering and dedup")
        self.logger.info(f"   ⏱️ Completed in {duration:.1f}s ({page_count} API calls, {duration/page_count:.1f}s avg per call)")
        
        return final_rows
    
    async def download_pool_data(self, pool: str) -> Dict:
        """
        Download data for a specific pool.
        
        Args:
            pool: Pool address
            
        Returns:
            Download result dictionary
        """
        self.logger.info(f"🚀 Starting download for pool {pool}")
        
        # Get pool metadata first, with hardcoded fallbacks for known pools
        pool_info = {
            # Spot trading pairs
            "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36": {
                "base": "WETH", 
                "quote": "USDT", 
                "name": "WETH/USDT Uniswap v3 0.3%",
                "dex": "Uniswap v3",
                "fee_tier": "0.3%"
            },
            "0xc2c390c6cd3c4e6c2b70727d35a45e8a072f18ca": {
                "base": "EIGEN", 
                "quote": "WETH", 
                "name": "EIGEN/WETH Uniswap v3 0.3%",
                "dex": "Uniswap v3",
                "fee_tier": "0.3%"
            },
            "0x06f00544c0bc62e6db10f46d370dfccdc23d8189": {
                "base": "ETHFI", 
                "quote": "WETH", 
                "name": "ETHFI/WETH Uniswap v3 0.3%",
                "dex": "Uniswap v3",
                "fee_tier": "0.3%"
            },
            # LST pools
            "0x109830a1aaad605bbf02a9dfa7b0b92ec2fb7daa": {
                "base": "wstETH", 
                "quote": "WETH", 
                "name": "wstETH/WETH Uniswap v3 0.01%",
                "dex": "Uniswap v3",
                "fee_tier": "0.01%"
            },
            "0xdb74dfdd3bb46be8ce6c33dc9d82777bcfc3ded5": {
                "base": "weETH", 
                "quote": "WETH", 
                "name": "weETH/WETH Curve weeth-ng",
                "dex": "Curve", 
                "fee_tier": "weeth-ng"
            }
        }
        
        if pool in pool_info:
            # Use known pool info
            info = pool_info[pool]
            base_symbol = info["base"]
            quote_symbol = info["quote"]
            pool_name = info["name"]
            dex_name = info["dex"]
            fee_tier = info["fee_tier"]
            self.logger.info(f"📊 Pool: {pool_name} ({base_symbol}/{quote_symbol})")
        else:
            # Try to get metadata from API
            try:
                meta = await self.client.get_pool_meta(self.network, pool)
                if meta and "data" in meta:
                    attributes = meta["data"]["attributes"]
                    base_symbol = attributes.get("base_token_symbol", "BASE")
                    quote_symbol = attributes.get("quote_token_symbol", "QUOTE")
                    pool_name = attributes.get("name", f"{base_symbol}/{quote_symbol}")
                    dex_name = "Unknown"
                    fee_tier = "Unknown"
                    
                    self.logger.info(f"📊 Pool: {pool_name} ({base_symbol}/{quote_symbol})")
                else:
                    self.logger.warning(f"⚠️ Could not get metadata for {pool}, using defaults")
                    base_symbol = "BASE"
                    quote_symbol = "QUOTE"
                    dex_name = "Unknown"
                    fee_tier = "Unknown"
            except Exception as e:
                self.logger.error(f"❌ Failed to get pool metadata: {e}")
                base_symbol = "BASE"
                quote_symbol = "QUOTE"
                dex_name = "Unknown"
                fee_tier = "Unknown"
        
        # Calculate start and end timestamps (use pool creation date if later than requested start)
        requested_start = self.start_date
        requested_end = getattr(self, 'end_date', None)
        
        # Determine the appropriate pool creation date based on pool type
        pool_creation_date = None
        if pool == "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36":  # WETH/USDT
            pool_creation_date = self.pool_creation_dates.get("eth_usdt")
        elif pool == "0xc2c390c6cd3c4e6c2b70727d35a45e8a072f18ca":  # EIGEN/WETH
            pool_creation_date = self.pool_creation_dates.get("eigen_eth")
        elif pool == "0x06f00544c0bc62e6db10f46d370dfccdc23d8189":  # ETHFI/WETH
            pool_creation_date = self.pool_creation_dates.get("ethfi_eth")
        elif pool in ["0x109830a1aaad605bbf02a9dfa7b0b92ec2fb7daa", "0xdb74dfdd3bb46be8ce6c33dc9d82777bcfc3ded5"]:  # LST pools
            pool_creation_date = self.pool_creation_dates.get("lst_pools")
        
        if pool_creation_date:
            # Use the later of requested start date or pool creation date
            if pool_creation_date > requested_start:
                actual_start = pool_creation_date
                self.logger.info(f"   📅 Using pool creation date {pool_creation_date} (later than requested {requested_start})")
            else:
                actual_start = requested_start
                self.logger.info(f"   📅 Using requested date {requested_start} (pool created {pool_creation_date})")
        else:
            actual_start = requested_start
            self.logger.warning(f"   ⚠️ No pool creation date found for {pool}, using requested date {requested_start}")
        
        start_unix = self.unix_timestamp(
            datetime.fromisoformat(actual_start + "T00:00:00+00:00")
        )
        
        end_unix = None
        if requested_end:
            end_unix = self.unix_timestamp(
                datetime.fromisoformat(requested_end + "T23:59:59+00:00")
            )
        
        # Fetch historical data
        try:
            ohlcv_data = await self.fetch_pool_history(pool, start_unix, end_unix)
            
            if not ohlcv_data:
                return {
                    'success': False,
                    'pool': pool,
                    'error': 'No data retrieved',
                    'record_count': 0
                }
            
            # Determine output subdirectory based on pool type
            if quote_symbol == "USDT":
                subdir = self.output_dir / "eth_usd"  # WETH/USDT goes to eth_usd
            elif quote_symbol == "WETH":
                # Check if this is an LST pool or protocol token pool
                if base_symbol in ["wstETH", "weETH"]:
                    subdir = self.output_dir / "lst_eth_ratios"  # LST pools go to lst_eth_ratios
                else:
                    subdir = self.output_dir / "protocol_tokens"  # EIGEN/WETH, ETHFI/WETH go to protocol_tokens
            else:
                subdir = self.output_dir / "other"
            
            subdir.mkdir(parents=True, exist_ok=True)
            
            # Create standardized filename with DEX prefix (use actual start date used)
            end_date_str = self.end_date if hasattr(self, 'end_date') and self.end_date else datetime.now().strftime('%Y-%m-%d')
            dex_prefix = dex_name.lower().replace(" ", "")  # "Uniswap v4" -> "uniswapv4"
            # Standardize quote symbol to uppercase for consistency
            quote_symbol_std = quote_symbol.upper()
            filename = f"{dex_prefix}_{base_symbol}{quote_symbol_std}_1h_{actual_start}_{end_date_str}.csv"
            filepath = subdir / filename
            
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                
                # Write header with meaningful column names and metadata
                writer.writerow([
                    "timestamp",
                    "date_utc", 
                    f"open",
                    f"high", 
                    f"low",
                    f"close",
                    "volume",
                    "pool_address",
                    "dex",
                    "fee_tier",
                    "base_token",
                    "quote_token",
                    "source"
                ])
                
                # Write data rows with metadata
                for t, o, h, l, c, v in ohlcv_data:
                    date_utc = datetime.fromtimestamp(t, timezone.utc).isoformat() + "Z"
                    writer.writerow([
                        t, date_utc, o, h, l, c, v,
                        pool, dex_name, fee_tier, base_symbol, quote_symbol, "geckoterminal_pro"
                    ])
            
            self.logger.info(f"💾 Saved {len(ohlcv_data)} records to {filename}")
            
            return {
                'success': True,
                'pool': pool,
                'pool_name': f"{base_symbol}/{quote_symbol}",
                'base_symbol': base_symbol,
                'quote_symbol': quote_symbol,
                'dex': dex_name,
                'fee_tier': fee_tier,
                'record_count': len(ohlcv_data),
                'output_file': str(filepath),
                'date_range': f"{self.start_date} to {datetime.now().strftime('%Y-%m-%d')}"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to download pool {pool}: {e}")
            return {
                'success': False,
                'pool': pool,
                'error': str(e),
                'record_count': 0
            }
    
    async def download_all_pools(self) -> Dict:
        """
        Download data for all relevant pools based on date range.
        
        Returns:
            Combined download results
        """
        end_date = getattr(self, 'end_date', None)
        end_date_str = end_date if end_date else "present"
        
        self.logger.info("🚀 Starting spot data download")
        self.logger.info(f"📅 Date range: {self.start_date} to {end_date_str}")
        
        # Get relevant pools based on date range
        relevant_pools = self.get_relevant_pools(self.start_date, end_date)
        self.logger.info(f"🎯 Relevant pools: {len(relevant_pools)}")
        
        download_results = []
        
        for i, pool in enumerate(relevant_pools):
            self.logger.info(f"\n📊 Pool {i+1}/{len(relevant_pools)}: {pool}")
            
            result = await self.download_pool_data(pool)
            download_results.append(result)
            
            if result['success']:
                self.logger.info(f"✅ {result.get('pool_name', pool[:10])}: {result['record_count']} records")
            else:
                self.logger.error(f"❌ {pool[:10]}: {result.get('error', 'Unknown error')}")
        
        # Create summary
        successful = sum(1 for r in download_results if r['success'])
        total_records = sum(r.get('record_count', 0) for r in download_results)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'downloader': 'spot_data',
            'date_range': f"{self.start_date} to {end_date_str}",
            'total_pools': len(relevant_pools),
            'successful_downloads': successful,
            'failed_downloads': len(relevant_pools) - successful,
            'total_records': total_records,
            'output_directory': str(self.output_dir),
            'downloads': download_results
        }
        
        # Save summary report
        report_file = self.output_dir / f"spot_data_download_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(report_file, 'w') as f:
            import json
            json.dump(summary, f, indent=2)
        
        # Log final summary
        self.logger.info("\n" + "="*70)
        self.logger.info("🎯 SPOT DATA DOWNLOAD COMPLETE!")
        self.logger.info("="*70)
        self.logger.info(f"✅ Successful downloads: {successful}/{len(relevant_pools)}")
        self.logger.info(f"📊 Total records: {total_records:,}")
        self.logger.info(f"💾 Output directory: {self.output_dir}")
        self.logger.info(f"📋 Report saved: {report_file}")
        self.logger.info("="*70)
        
        return summary


async def main():
    """
    Main execution function for standalone script usage.
    
    🔑 IMPORTANT: Load environment variables first!
    source scripts/load_env.sh
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Download spot pool data from GeckoTerminal")
    parser.add_argument("--output-dir", type=str, 
                       default="data/market_data/spot_prices", 
                       help="Output directory")
    parser.add_argument("--start-date", type=str, default="2024-01-01", 
                       help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default=None,
                       help="End date (YYYY-MM-DD), defaults to present")
    
    args = parser.parse_args()
    
    try:
        downloader = SpotDataDownloader(args.output_dir)
        
        # Override start date if provided
        if args.start_date != "2024-01-01":
            downloader.start_date = args.start_date
            downloader.logger.info(f"Using custom start date: {args.start_date}")
        
        # Set end date if provided
        if args.end_date:
            downloader.end_date = args.end_date
            downloader.logger.info(f"Using custom end date: {args.end_date}")
        else:
            downloader.end_date = None
        
        print(f"🎯 Downloading unified pool data from GeckoTerminal...")
        print(f"📊 Pools: WETH/USDT, EIGEN/WETH, ETHFI/WETH, wstETH/WETH, weETH/WETH")
        print(f"📅 Period: {downloader.start_date} to {'present' if not args.end_date else args.end_date}")
        print(f"💾 Output: {args.output_dir}")
        
        # Run download
        result = await downloader.download_all_pools()
        
        # Print summary
        if result['successful_downloads'] > 0:
            print(f"\n🎉 SUCCESS! Downloaded {result['total_records']:,} spot records")
            print(f"✅ Pools downloaded: {result['successful_downloads']}/{result['total_pools']}")
            print(f"📁 Files saved to: {args.output_dir}")
            
            # Show individual results
            for download in result['downloads']:
                if download['success']:
                    pool_short = download['pool'][:10] + "..."
                    pool_name = download.get('pool_name', 'Unknown')
                    records = download['record_count']
                    dex = download.get('dex', 'Unknown')
                    print(f"   📊 {pool_name} ({dex}) ({pool_short}): {records:,} records")
        else:
            print(f"\n❌ FAILED! No spot data was downloaded successfully")
            for download in result['downloads']:
                if not download['success']:
                    pool_short = download['pool'][:10] + "..."
                    error = download.get('error', 'Unknown error')
                    print(f"   ❌ {pool_short}: {error}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
