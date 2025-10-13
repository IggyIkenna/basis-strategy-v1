"""
Binance Spot API client for market data.

Handles:
- Spot price OHLCV data for EIGEN/USDT and ETHFI/USDT
- Historical market data with chunking
- Rate limiting for public API (1200 req/min)
- Deeper liquidity than DEX for newer tokens
"""

import asyncio
from datetime import datetime, timedelta
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


class BinanceSpotClient(BaseDownloader):
    """
    Binance Spot API client.
    
    Features:
    - 1-minute OHLCV data for spot prices
    - Focus on EIGEN/ETHFI tokens with deeper liquidity
    - Automatic chunking for large date ranges
    - Rate limiting (1200 req/min for public API)
    """
    
    def __init__(self, output_dir: str = "data/market_data/spot_prices"):
        super().__init__("binance_spot", output_dir, rate_limit_per_minute=1200)
        
        # Create subdirectories for different asset types
        self.eth_usd_dir = Path(output_dir) / "eth_usd"
        self.protocol_tokens_dir = Path(output_dir) / "protocol_tokens"
        self.eth_usd_dir.mkdir(parents=True, exist_ok=True)
        self.protocol_tokens_dir.mkdir(parents=True, exist_ok=True)
        
        self.base_url = "https://api.binance.com/api/v3"
        
        # Asset mappings - focus on tokens with deeper liquidity on Binance
        self.spot_assets = {
            'EIGENUSDT': 'EIGEN',   # EigenLayer - better liquidity on CEX
            'ETHFIUSDT': 'ETHFI',   # Ether.fi - better liquidity on CEX
            'ETHUSDT': 'ETH'        # ETH for general trading and CEX operations
        }
        
        self.logger.info(f"Binance Spot client initialized with {len(self.spot_assets)} assets")
    
    async def get_klines(self, symbol: str, interval: str, start_time: int, 
                        end_time: int, limit: int = 1000) -> Optional[List]:
        """
        Get historical kline/candlestick data.
        
        Args:
            symbol: Trading symbol (e.g., 'EIGENUSDT')
            interval: Kline interval (e.g., '1h')
            start_time: Start timestamp (Unix milliseconds)
            end_time: End timestamp (Unix milliseconds)
            limit: Number of records to return (max 1000)
            
        Returns:
            List of kline data or None if failed
        """
        url = f"{self.base_url}/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_time,
            'endTime': end_time,
            'limit': limit
        }
        
        response = await self.make_request(url, params=params)
        
        if response and isinstance(response, list):
            return response
        else:
            self.logger.error(f"Invalid klines response for {symbol}")
            return None
    
    def _convert_klines_to_ohlcv(self, klines: List, asset_symbol: str) -> List[Dict]:
        """
        Convert Binance klines data to OHLCV format.
        
        Args:
            klines: Raw klines data from Binance API
            asset_symbol: Asset symbol (e.g., 'EIGEN')
            
        Returns:
            List of OHLCV records
        """
        ohlcv_records = []
        
        for kline in klines:
            try:
                # Binance kline format:
                # [timestamp, open, high, low, close, volume, close_time, quote_volume, count, taker_buy_volume, taker_buy_quote_volume, ignore]
                timestamp_ms = int(kline[0])
                
                record = {
                    'timestamp': format_timestamp_utc(timestamp_ms),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'quote_volume': float(kline[7]),
                    'trades_count': int(kline[8]),
                    'source': 'binance_spot',
                    'asset_pair': f'{asset_symbol}/USDT'
                }
                
                ohlcv_records.append(record)
                
            except (ValueError, IndexError) as e:
                self.logger.warning(f"Skipping invalid kline: {e}")
                continue
        
        return ohlcv_records
    
    async def download_spot_ohlcv(self, symbol: str, asset_symbol: str, 
                                start_date: str, end_date: str) -> Dict:
        """
        Download spot OHLCV data for an asset.
        
        Args:
            symbol: Binance symbol (e.g., 'EIGENUSDT')
            asset_symbol: Asset symbol for output (e.g., 'EIGEN')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Download result dictionary
        """
        self.logger.info(f"Downloading {asset_symbol} OHLCV data from {start_date} to {end_date}")
        
        # Convert dates to timestamps (Binance uses milliseconds)
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
        end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
        
        # Chunk the date range (Binance limit is 1000 records per request)
        # 1h interval = 24 records per day, so ~41 days per chunk
        chunk_days = 40
        chunks = self.chunk_date_range(start_date, end_date, chunk_days)
        
        all_records = []
        failed_chunks = []
        
        self.logger.info(f"Processing {len(chunks)} chunks for {asset_symbol}")
        
        for i, (chunk_start, chunk_end) in enumerate(chunks):
            self.logger.info(f"Chunk {i+1}/{len(chunks)}: {chunk_start} to {chunk_end}")
            
            chunk_start_ts = int(datetime.strptime(chunk_start, '%Y-%m-%d').timestamp() * 1000)
            chunk_end_ts = int(datetime.strptime(chunk_end, '%Y-%m-%d').timestamp() * 1000)
            
            klines = await self.get_klines(symbol, '1h', chunk_start_ts, chunk_end_ts)
            
            if klines:
                chunk_records = self._convert_klines_to_ohlcv(klines, asset_symbol)
                all_records.extend(chunk_records)
                self.logger.info(f"  ✅ Got {len(chunk_records)} records")
            else:
                failed_chunks.append((chunk_start, chunk_end))
                self.logger.warning(f"  ❌ Failed to get data")
            
            # Rate limiting - small delay between chunks
            await asyncio.sleep(0.1)
        
        # Save data if we got any
        success = len(all_records) > 0
        filepath = None
        
        if success:
            # Determine correct subdirectory based on asset
            if asset_symbol == 'ETH':
                filename = f"binance_ETHUSDT_1h_{start_date}_{end_date}.csv"
                target_dir = self.eth_usd_dir
            else:
                # Protocol tokens (EIGEN, ETHFI)
                filename = f"binance_{asset_symbol}USDT_1h_{start_date}_{end_date}.csv"
                target_dir = self.protocol_tokens_dir
            
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
        
        self.logger.info(f"Starting Binance spot data download for {len(self.spot_assets)} assets")
        self.logger.info(f"Date range: {start_date} to {end_date}")
        
        download_results = []
        
        for symbol, asset_symbol in self.spot_assets.items():
            try:
                result = await self.download_spot_ohlcv(symbol, asset_symbol, start_date, end_date)
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
        report_file = self.save_report(report, f"binance_spot_report_{start_date}_{end_date}.json")
        
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

