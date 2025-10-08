"""
Binance Futures API client for perpetual futures data.

Handles:
- Perpetual futures OHLCV (mark/index prices)
- Funding rate history
- No API key required (public endpoints)
- Rate limiting (1200 req/min)
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import time

# Handle both standalone and module imports
try:
    from ..base_downloader import BaseDownloader
except ImportError:
    # Standalone execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from base_downloader import BaseDownloader


class BinanceFuturesClient(BaseDownloader):
    """
    Binance Futures API client for perpetual futures data.
    
    Features:
    - Mark/Index price OHLCV data
    - Funding rate history  
    - Public API (no authentication required)
    - Rate limiting (1200 req/min)
    """
    
    def __init__(self, output_dir: str = "data/market_data/derivatives"):
        super().__init__("binance_futures", output_dir, rate_limit_per_minute=1200)
        
        # Create subdirectories for different data types
        self.futures_ohlcv_dir = Path(output_dir) / "futures_ohlcv"
        self.funding_rates_dir = Path(output_dir) / "funding_rates"
        self.futures_ohlcv_dir.mkdir(parents=True, exist_ok=True)
        self.funding_rates_dir.mkdir(parents=True, exist_ok=True)
        
        self.base_url = "https://fapi.binance.com"  # Futures API endpoint
        
        # Perpetual futures symbols
        self.futures_symbols = ['ETHUSDT', 'BTCUSDT']
        
        self.logger.info(f"Binance Futures client initialized with {len(self.futures_symbols)} symbols")
    
    async def get_klines(self, symbol: str, interval: str, start_time: int, 
                        end_time: int, limit: int = 1000) -> Optional[List]:
        """
        Get historical kline/candlestick data for futures.
        
        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT')
            interval: Kline interval (e.g., '1m')
            start_time: Start timestamp (Unix milliseconds)
            end_time: End timestamp (Unix milliseconds)
            limit: Number of records to return (max 1500)
            
        Returns:
            List of kline data or None if failed
        """
        url = f"{self.base_url}/fapi/v1/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_time,
            'endTime': end_time,
            'limit': min(limit, 1500)  # Binance futures max limit
        }
        
        response = await self.make_request(url, params=params)
        
        if response and isinstance(response, list):
            return response
        else:
            self.logger.error(f"Invalid klines response for {symbol}")
            return None
    
    async def get_funding_rate_history(self, symbol: str, start_time: int, end_time: int, limit: int = 1000) -> Optional[List]:
        """
        Get funding rate history.
        
        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT')
            start_time: Start timestamp (Unix milliseconds)
            end_time: End timestamp (Unix milliseconds)
            limit: Number of records to return (max 1000)
            
        Returns:
            List of funding rate data or None if failed
        """
        url = f"{self.base_url}/fapi/v1/fundingRate"
        params = {
            'symbol': symbol,
            'startTime': start_time,
            'endTime': end_time,
            'limit': min(limit, 1000)
        }
        
        response = await self.make_request(url, params=params)
        
        if response and isinstance(response, list):
            return response
        else:
            self.logger.error(f"Invalid funding rate response for {symbol}")
            return None
    
    def _convert_klines_to_ohlcv(self, klines: List, symbol: str) -> List[Dict]:
        """
        Convert Binance futures klines data to OHLCV format.
        
        Args:
            klines: Raw klines data from Binance API
            symbol: Trading symbol
            
        Returns:
            List of OHLCV records
        """
        ohlcv_records = []
        
        for kline in klines:
            try:
                # Binance futures kline format:
                # [timestamp, open, high, low, close, volume, close_time, quote_volume, count, taker_buy_volume, taker_buy_quote_volume, ignore]
                timestamp_ms = int(kline[0])
                
                record = {
                    'timestamp': datetime.utcfromtimestamp(timestamp_ms / 1000).isoformat() + 'Z',
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'quote_volume': float(kline[7]),
                    'trades_count': int(kline[8]),
                    'source': 'binance_futures',
                    'symbol': symbol,
                    'data_type': 'futures'
                }
                
                ohlcv_records.append(record)
                
            except (ValueError, IndexError) as e:
                self.logger.warning(f"Skipping invalid kline: {e}")
                continue
        
        return ohlcv_records
    
    def _convert_funding_rates(self, funding_data: List, symbol: str) -> List[Dict]:
        """
        Convert Binance funding rate data to standard format.
        
        Args:
            funding_data: Raw funding rate data from API
            symbol: Trading symbol
            
        Returns:
            List of funding rate records
        """
        funding_records = []
        
        for funding in funding_data:
            try:
                record = {
                    'funding_timestamp': datetime.utcfromtimestamp(int(funding['fundingTime']) / 1000).isoformat() + 'Z',
                    'funding_rate': float(funding['fundingRate']),
                    'symbol': funding['symbol'],
                    'source': 'binance_futures'
                }
                funding_records.append(record)
            except (ValueError, KeyError) as e:
                self.logger.warning(f"Skipping invalid funding rate: {e}")
                continue
        
        return funding_records
    
    async def download_futures_ohlcv(self, symbol: str, start_date: str, end_date: str, timeframe: str = "1h") -> Dict:
        """
        Download futures OHLCV data for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Data timeframe ('1m' or '1h')
            
        Returns:
            Download result dictionary
        """
        self.logger.info(f"Downloading {symbol} futures OHLCV from {start_date} to {end_date}")
        
        # Map timeframe to Binance interval
        interval_map = {
            '1m': '1m',   # 1 minute
            '1h': '1h'    # 1 hour
        }
        interval = interval_map.get(timeframe, '1h')
        
        # Convert dates to millisecond timestamps
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)
        
        # Chunk the date range (Binance futures limit is 1500 records per request)
        # For 1-minute data, 1500 records = 25 hours
        chunk_days = 40  # Be conservative
        chunks = self.chunk_date_range(start_date, end_date, chunk_days)  # Convert to days
        
        all_records = []
        failed_chunks = []
        
        self.logger.info(f"Processing {len(chunks)} chunks for {symbol}")
        
        for i, (chunk_start, chunk_end) in enumerate(chunks):
            self.logger.info(f"Chunk {i+1}/{len(chunks)}: {chunk_start} to {chunk_end}")
            
            chunk_start_ts = int(datetime.strptime(chunk_start, '%Y-%m-%d').timestamp() * 1000)
            chunk_end_ts = int(datetime.strptime(chunk_end, '%Y-%m-%d').timestamp() * 1000)
            
            klines = await self.get_klines(symbol, interval, chunk_start_ts, chunk_end_ts)
            
            if klines:
                chunk_records = self._convert_klines_to_ohlcv(klines, symbol)
                all_records.extend(chunk_records)
                self.logger.info(f"  ✅ Got {len(chunk_records)} records")
            else:
                failed_chunks.append((chunk_start, chunk_end))
                self.logger.warning(f"  ❌ Failed to get data")
            
            # Rate limiting - small delay between chunks
            await asyncio.sleep(0.1)
        
        # Sort by timestamp
        all_records.sort(key=lambda x: x['timestamp'])
        
        # Save data if we got any
        success = len(all_records) > 0
        filepath = None
        
        if success:
            filename = f"binance_{symbol}_perp_{timeframe}_{start_date}_{end_date}.csv"
            required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
            if self.validate_data(all_records, required_fields):
                # Save to futures_ohlcv subdirectory
                original_output_dir = self.output_dir
                self.output_dir = self.futures_ohlcv_dir
                filepath = self.save_to_csv(all_records, filename)
                self.output_dir = original_output_dir
        
        return {
            'success': success,
            'symbol': symbol,
            'record_count': len(all_records),
            'chunks_processed': len(chunks),
            'chunks_failed': len(failed_chunks),
            'failed_chunks': failed_chunks,
            'output_file': str(filepath) if filepath else None,
            'date_range': f"{start_date} to {end_date}",
            'data_type': 'futures_ohlcv'
        }
    
    async def download_funding_rates(self, symbol: str, start_date: str, end_date: str) -> Dict:
        """
        Download funding rate history for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Download result dictionary
        """
        self.logger.info(f"Downloading {symbol} funding rates from {start_date} to {end_date}")
        
        # Convert dates to millisecond timestamps
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)
        
        all_records = []
        current_start = start_ms
        
        # Binance funding rates are every 8 hours, 1000 limit = ~333 days
        chunk_days = 300  # Be conservative
        chunk_ms = chunk_days * 24 * 60 * 60 * 1000
        
        while current_start < end_ms:
            current_end = min(current_start + chunk_ms, end_ms)
            
            self.logger.info(f"  Fetching chunk: {datetime.fromtimestamp(current_start/1000)} to {datetime.fromtimestamp(current_end/1000)}")
            
            funding_data = await self.get_funding_rate_history(symbol, current_start, current_end)
            
            if funding_data:
                chunk_records = self._convert_funding_rates(funding_data, symbol)
                all_records.extend(chunk_records)
                self.logger.info(f"    ✅ Got {len(chunk_records)} records")
            else:
                self.logger.warning(f"    ❌ Failed to get data for chunk")
            
            current_start = current_end + 1
            await asyncio.sleep(0.1)
        
        # Sort by timestamp
        all_records.sort(key=lambda x: x['funding_timestamp'])
        
        # Remove duplicates (can happen at chunk boundaries)
        seen_timestamps = set()
        unique_records = []
        for record in all_records:
            ts = record['funding_timestamp']
            if ts not in seen_timestamps:
                unique_records.append(record)
                seen_timestamps.add(ts)
        
        # Save data if we got any
        success = len(unique_records) > 0
        filepath = None
        
        if success:
            filename = f"binance_{symbol}_funding_rates_{start_date}_{end_date}.csv"
            required_fields = ['funding_timestamp', 'funding_rate', 'symbol']
            
            if self.validate_data(unique_records, required_fields):
                # Save to funding_rates subdirectory
                original_output_dir = self.output_dir
                self.output_dir = self.funding_rates_dir
                filepath = self.save_to_csv(unique_records, filename)
                self.output_dir = original_output_dir
        
        return {
            'success': success,
            'symbol': symbol,
            'record_count': len(unique_records),
            'output_file': str(filepath) if filepath else None,
            'date_range': f"{start_date} to {end_date}",
            'data_type': 'funding_rates'
        }
    
    async def download_all_futures_data(self, start_date: Optional[str] = None, 
                                      end_date: Optional[str] = None) -> Dict:
        """
        Download all futures data (OHLCV + funding rates) for configured symbols.
        
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
        
        self.logger.info(f"Starting Binance futures data download for {len(self.futures_symbols)} symbols")
        self.logger.info(f"Date range: {start_date} to {end_date}")
        
        download_results = []
        
        for symbol in self.futures_symbols:
            try:
                # Download OHLCV data
                ohlcv_result = await self.download_futures_ohlcv(symbol, start_date, end_date)
                download_results.append(ohlcv_result)
                
                # Download funding rates
                funding_result = await self.download_funding_rates(symbol, start_date, end_date)
                download_results.append(funding_result)
                
                self.logger.info(f"✅ {symbol}: OHLCV={ohlcv_result['record_count']}, Funding={funding_result['record_count']}")
                    
            except Exception as e:
                self.logger.error(f"❌ {symbol}: Unexpected error - {e}")
                download_results.append({
                    'success': False,
                    'symbol': symbol,
                    'error': str(e),
                    'record_count': 0
                })
        
        # Create summary report
        report = self.create_summary_report(download_results)
        report_file = self.save_report(report, f"binance_futures_report_{start_date}_{end_date}.json")
        
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
        return await self.download_all_futures_data(start_date, end_date)

