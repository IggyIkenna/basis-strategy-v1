"""
CoinGecko Pro API client for market data.

Handles:
- Spot price OHLCV data
- LST token prices  
- Historical market data with chunking
- Rate limiting for Analyst Plan (500 req/min)

🔑 API KEY SETUP REQUIRED:
This client requires a CoinGecko Pro API key for full functionality.

1. Get a CoinGecko Pro API key from: https://www.coingecko.com/en/api/pricing
2. Add it to backend/env.unified:
   BASIS_DOWNLOADERS__COINGECKO_API_KEY=your_api_key_here

3. Load environment variables before running:
   source scripts/load_env.sh
   python scripts/downloaders/clients/coingecko_client.py

⚠️  WITHOUT API KEY: Will raise ValueError on initialization
✅  WITH API KEY: Full CoinGecko Pro API access (500 req/min)
"""

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
from .timestamp_utils import format_timestamp_utc

# Handle both standalone and module imports
try:
    from ..base_downloader import BaseDownloader
except ImportError:
    # Standalone execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from base_downloader import BaseDownloader


class CoinGeckoClient(BaseDownloader):
    """
    CoinGecko Pro API client.
    
    Features:
    - 1-minute OHLCV data for spot prices
    - LST token price monitoring
    - Automatic chunking for large date ranges
    - Rate limiting (500 req/min for Analyst Plan)
    """
    
    def __init__(self, output_dir: str = "data/market_data/spot_prices"):
        super().__init__("coingecko", output_dir, rate_limit_per_minute=500)
        
        # Create subdirectories for different asset types
        self.eth_usd_dir = Path(output_dir) / "eth_usd"
        self.lst_ratios_dir = Path(output_dir) / "lst_eth_ratios"
        self.eth_usd_dir.mkdir(parents=True, exist_ok=True)
        self.lst_ratios_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Created directories: {self.eth_usd_dir} and {self.lst_ratios_dir}")
        
        self.api_key = self.config['api_keys']['coingecko']
        if not self.api_key:
            raise ValueError("CoinGecko API key not found in configuration")
        
        self.base_url = "https://pro-api.coingecko.com/api/v3"
        self.headers = {"x-cg-pro-api-key": self.api_key}
        
        # Asset mappings - LST tokens removed (now handled by fetch_lst_pool_data.py via GeckoTerminal)
        self.spot_assets = {
            'ethereum': 'ETH'  # Keep ETH for general market data
            # LST tokens (wstETH, weETH, eETH, stETH) now handled by fetch_lst_pool_data.py
        }
        
        # WETH pair mappings (for cross-LST trading)
        self.weth_pairs = {
            'wsteth_weth': ('wrapped-steth', 'ethereum'),  # wstETH/WETH
            'weeth_weth': ('wrapped-eeth', 'ethereum')     # weETH/WETH  
        }
        
        self.logger.info(f"CoinGecko client initialized with {len(self.spot_assets)} assets")
        
        # GeckoTerminal API for pool data (Pro API for historical access)
        self.geckoterminal_base_url = "https://api.geckoterminal.com/api/v2"  # Public API
        self.pro_onchain_base_url = "https://pro-api.coingecko.com/api/v3/onchain"  # Pro API
    
    async def get_pool_meta(self, network: str, pool: str) -> Optional[Dict]:
        """
        Get pool metadata from GeckoTerminal.
        
        Args:
            network: Network identifier (e.g., 'eth')
            pool: Pool address (e.g., '0x109830a1aaad605bbf02a9dfa7b0b92ec2fb7daa')
            
        Returns:
            Pool metadata or None if failed
        """
        url = f"{self.geckoterminal_base_url}/networks/{network}/pools/{pool}"
        return await self.make_request(url)
    
    async def get_pool_ohlcv(self, network: str, pool: str, timeframe: str = "day",
                           aggregate: int = 1, limit: int = 1000, before_ts: int = None,
                           currency: str = "token", token_side: str = "base") -> Optional[Dict]:
        """
        Get pool OHLCV data from GeckoTerminal.
        
        Args:
            network: Network identifier (e.g., 'eth')
            pool: Pool address
            timeframe: Time interval ('day', 'hour', 'minute')
            aggregate: Aggregation level (1 for daily)
            limit: Number of records (max 1000)
            before_ts: Pagination timestamp (Unix seconds)
            currency: 'token' for direct ratios, 'usd' for USD prices
            token_side: 'base' or 'quote' to determine price direction
            
        Returns:
            OHLCV data or None if failed
        """
        url = f"{self.geckoterminal_base_url}/networks/{network}/pools/{pool}/ohlcv/{timeframe}"
        params = {
            "aggregate": aggregate,
            "limit": limit,
            "currency": currency,
            "token": token_side,
        }
        if before_ts:
            params["before_timestamp"] = before_ts
            
        return await self.make_request(url, params=params)
    
    async def get_pool_ohlcv_pro(self, network: str, pool: str, timeframe: str = "day",
                               aggregate: int = 1, limit: int = 1000, before_ts: int = None,
                               currency: str = "token", token_side: str = "base") -> Optional[Dict]:
        """
        Get pool OHLCV data from CoinGecko Pro API (for full historical access).
        
        Args:
            network: Network identifier (e.g., 'eth')
            pool: Pool address
            timeframe: Time interval ('day', 'hour', 'minute')
            aggregate: Aggregation level (1 for daily)
            limit: Number of records (max 1000)
            before_ts: Pagination timestamp (Unix seconds)
            currency: 'token' for direct ratios, 'usd' for USD prices
            token_side: 'base' or 'quote' to determine price direction
            
        Returns:
            OHLCV data or None if failed
        """
        url = f"{self.pro_onchain_base_url}/networks/{network}/pools/{pool}/ohlcv/{timeframe}"
        params = {
            "aggregate": aggregate,
            "limit": limit,
            "currency": currency,
            "token": token_side,
        }
        if before_ts:
            params["before_timestamp"] = before_ts
            
        return await self.make_request(url, params=params, headers=self.headers)
    
    async def get_market_chart_range(self, coin_id: str, vs_currency: str, 
                                   from_timestamp: int, to_timestamp: int) -> Optional[Dict]:
        """
        Get historical market data for a date range.
        
        Args:
            coin_id: CoinGecko coin ID (e.g., 'ethereum')
            vs_currency: Base currency (e.g., 'usd')
            from_timestamp: Start timestamp (Unix)
            to_timestamp: End timestamp (Unix)
            
        Returns:
            Market chart data or None if failed
        """
        url = f"{self.base_url}/coins/{coin_id}/market_chart/range"
        params = {
            'vs_currency': vs_currency,
            'from': from_timestamp,
            'to': to_timestamp
        }
        
        return await self.make_request(url, params=params, headers=self.headers)
    
    async def get_simple_price(self, coin_ids: List[str], vs_currencies: List[str] = ['usd']) -> Optional[Dict]:
        """
        Get current prices for multiple coins.
        
        Args:
            coin_ids: List of CoinGecko coin IDs
            vs_currencies: List of base currencies
            
        Returns:
            Price data or None if failed
        """
        url = f"{self.base_url}/simple/price"
        params = {
            'ids': ','.join(coin_ids),
            'vs_currencies': ','.join(vs_currencies),
            'include_24hr_change': 'true',
            'include_last_updated_at': 'true'
        }
        
        return await self.make_request(url, params=params, headers=self.headers)
    
    def _convert_market_chart_to_ohlcv(self, market_data: Dict, asset_symbol: str) -> List[Dict]:
        """
        Convert CoinGecko market chart data to OHLCV format.
        
        Args:
            market_data: Raw market chart data from API
            asset_symbol: Asset symbol (e.g., 'ETH')
            
        Returns:
            List of OHLCV records
        """
        if not market_data or 'prices' not in market_data:
            return []
        
        prices = market_data.get('prices', [])
        volumes = market_data.get('total_volumes', [])
        
        # Create price lookup for OHLC calculation
        price_dict = {int(p[0]): p[1] for p in prices}
        volume_dict = {int(v[0]): v[1] for v in volumes}
        
        # Group by hour for OHLCV calculation
        hourly_data = {}
        
        for timestamp_ms, price in prices:
            # Round to nearest hour
            hour_timestamp = int(timestamp_ms // (1000 * 60 * 60)) * (1000 * 60 * 60)
            
            if hour_timestamp not in hourly_data:
                hourly_data[hour_timestamp] = {
                    'prices': [],
                    'volume': volume_dict.get(int(timestamp_ms), 0)
                }
            
            hourly_data[hour_timestamp]['prices'].append(price)
        
        # Convert to OHLCV records
        ohlcv_records = []
        
        for hour_timestamp, data in sorted(hourly_data.items()):
            prices_in_hour = data['prices']
            
            if not prices_in_hour:
                continue
            
            record = {
                'timestamp': format_timestamp_utc(hour_timestamp),
                'open': prices_in_hour[0],
                'high': max(prices_in_hour),
                'low': min(prices_in_hour),
                'close': prices_in_hour[-1],
                'volume': data['volume'],
                'source': 'coingecko_pro',
                'asset_pair': f'{asset_symbol}/USDT'
            }
            
            ohlcv_records.append(record)
        
        return ohlcv_records
    
    async def download_spot_ohlcv(self, coin_id: str, asset_symbol: str, 
                                start_date: str, end_date: str) -> Dict:
        """
        Download spot OHLCV data for an asset.
        
        Args:
            coin_id: CoinGecko coin ID
            asset_symbol: Asset symbol for output
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Download result dictionary
        """
        self.logger.info(f"Downloading {asset_symbol} OHLCV data from {start_date} to {end_date}")
        
        # Convert dates to timestamps (ensure UTC)
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp())
        end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp())
        
        # Chunk the date range (CoinGecko works better with smaller ranges)
        chunk_days = self.config['download_config']['chunk_size_days']
        chunks = self.chunk_date_range(start_date, end_date, chunk_days)
        
        all_records = []
        failed_chunks = []
        
        self.logger.info(f"Processing {len(chunks)} chunks for {asset_symbol}")
        
        for i, (chunk_start, chunk_end) in enumerate(chunks):
            self.logger.info(f"Chunk {i+1}/{len(chunks)}: {chunk_start} to {chunk_end}")
            
            chunk_start_ts = int(datetime.strptime(chunk_start, '%Y-%m-%d').timestamp())
            chunk_end_ts = int(datetime.strptime(chunk_end, '%Y-%m-%d').timestamp())
            
            market_data = await self.get_market_chart_range(
                coin_id, 'usd', chunk_start_ts, chunk_end_ts
            )
            
            if market_data:
                chunk_records = self._convert_market_chart_to_ohlcv(market_data, asset_symbol)
                all_records.extend(chunk_records)
                self.logger.info(f"  ✅ Got {len(chunk_records)} records")
            else:
                failed_chunks.append((chunk_start, chunk_end))
                self.logger.warning(f"  ❌ Failed to get data")
            
            # Small delay between chunks
            await asyncio.sleep(0.1)
        
        # Save data if we got any
        success = len(all_records) > 0
        filepath = None
        
        if success:
            # Determine correct subdirectory and filename based on asset
            if asset_symbol == 'ETH':
                filename = f"coingecko_ETHUSDT_1h_{start_date}_{end_date}.csv"
                target_dir = self.eth_usd_dir
            else:
                # LST tokens get ETH ratios
                filename = f"coingecko_{asset_symbol}_ETH_1h_{start_date}_{end_date}.csv"
                target_dir = self.lst_ratios_dir
            
            required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
            if self.validate_data(all_records, required_fields):
                # Temporarily change output_dir for this save
                original_output_dir = self.output_dir
                self.output_dir = target_dir
                filepath = self.save_to_csv(all_records, filename)
                self.output_dir = original_output_dir
        
        return {
            'success': success,
            'asset': asset_symbol,
            'record_count': len(all_records),
            'chunks_processed': len(chunks),
            'chunks_failed': len(failed_chunks),
            'failed_chunks': failed_chunks,
            'output_file': str(filepath) if filepath else None,
            'date_range': f"{start_date} to {end_date}"
        }
    
    async def download_all_spot_data(self, start_date: Optional[str] = None, 
                                   end_date: Optional[str] = None) -> Dict:
        """
        Download OHLCV data for all configured spot assets.
        
        Args:
            start_date: Start date (YYYY-MM-DD), uses config default if None
            end_date: End date (YYYY-MM-DD), uses config default if None
            
        Returns:
            Combined download results
        """
        if start_date is None or end_date is None:
            config_start, config_end = self.get_date_range()
            start_date = start_date or config_start
            end_date = end_date or config_end
        
        self.logger.info(f"Starting spot data download for {len(self.spot_assets)} assets")
        self.logger.info(f"Date range: {start_date} to {end_date}")
        
        download_results = []
        
        for coin_id, asset_symbol in self.spot_assets.items():
            try:
                result = await self.download_spot_ohlcv(coin_id, asset_symbol, start_date, end_date)
                download_results.append(result)
                
                if result['success']:
                    self.logger.info(f"✅ {asset_symbol}: {result['record_count']} records")
                else:
                    self.logger.error(f"❌ {asset_symbol}: Download failed")
                    
            except Exception as e:
                self.logger.error(f"❌ {asset_symbol}: Unexpected error - {e}")
                download_results.append({
                    'success': False,
                    'asset': asset_symbol,
                    'error': str(e),
                    'record_count': 0
                })
        
        # Create summary report
        report = self.create_summary_report(download_results)
        report_file = self.save_report(report, f"coingecko_spot_report_{start_date}_{end_date}.json")
        
        return report
    
    async def download_data(self, start_date: str, end_date: str) -> Dict:
        """
        Main download method (implements abstract base method).
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Download results
        """
        return await self.download_all_spot_data(start_date, end_date)
