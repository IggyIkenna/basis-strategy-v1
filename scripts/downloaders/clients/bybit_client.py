"""
Bybit API client for perpetual futures data.

Handles:
- Perpetual futures OHLCV (mark/index prices) hourly
- Funding rate history
- No API key required (public endpoints)
- Rate limiting (10 req/sec)
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


class BybitClient(BaseDownloader):
    """
    Bybit API client for perpetual futures data.
    
    Features:
    - Mark/Index price OHLCV data
    - Funding rate history  
    - Public API (no authentication required)
    - Optimized rate limiting (100 req/sec, 40-day chunks for hourly data)
    """
    
    def __init__(self, output_dir: str = "data/market_data/derivatives"):
        # Bybit allows 600 requests per 5 seconds = 120 req/sec = 7200 req/min
        # We'll be conservative and use 100 req/sec = 6000 req/min
        super().__init__("bybit", output_dir, rate_limit_per_minute=6000)
        
        # Create subdirectories for different data types
        self.futures_ohlcv_dir = Path(output_dir) / "futures_ohlcv"
        self.funding_rates_dir = Path(output_dir) / "funding_rates"
        self.spot_ohlcv_dir = Path(output_dir) / "spot_ohlcv"
        
        # Only create futures/funding subdirectories if we're in the derivatives directory
        # This prevents creating empty directories in spot_prices when used for spot data
        if "derivatives" in str(output_dir):
            self.futures_ohlcv_dir.mkdir(parents=True, exist_ok=True)
            self.funding_rates_dir.mkdir(parents=True, exist_ok=True)
            # Don't create spot_ohlcv in derivatives directory - that's for spot data only
        
        # For spot data, also create eth_usd subdirectory if we're in spot_prices
        if "spot_prices" in str(output_dir):
            self.eth_usd_dir = Path(output_dir) / "eth_usd"
            self.eth_usd_dir.mkdir(parents=True, exist_ok=True)
        
        self.base_url = "https://api.bybit.com"
        
        # Perpetual futures symbols
        self.futures_symbols = ['ETHUSDT', 'BTCUSDT']
        self.category = "linear"  # USDT perpetuals
        
        # Spot symbols
        self.spot_symbols = ['ETHUSDT', 'BTCUSDT']
        
        self.logger.info(f"Bybit client initialized with {len(self.futures_symbols)} symbols")
    
    async def get_kline_data(self, symbol: str, interval: str, start_time: int, end_time: int) -> Optional[Dict]:
        """
        Get kline/candlestick data.
        
        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT')
            interval: Time interval ('1', '5', '15', '30', '60', 'D')
            start_time: Start timestamp (milliseconds)
            end_time: End timestamp (milliseconds)
            
        Returns:
            Kline data or None if failed
        """
        url = f"{self.base_url}/v5/market/kline"
        params = {
            'category': self.category,
            'symbol': symbol,
            'interval': interval,
            'start': start_time,
            'end': end_time,
            'limit': 1000  # Max limit
        }
        
        return await self.make_request(url, params=params)
    
    async def get_spot_kline_data(self, symbol: str, interval: str, start_time: int, end_time: int) -> Optional[Dict]:
        """
        Get spot kline/candlestick data.
        
        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT')
            interval: Time interval ('1', '5', '15', '30', '60', 'D')
            start_time: Start timestamp (milliseconds)
            end_time: End timestamp (milliseconds)
            
        Returns:
            Kline data or None if failed
        """
        url = f"{self.base_url}/v5/market/kline"
        params = {
            'category': 'spot',  # Spot market category
            'symbol': symbol,
            'interval': interval,
            'start': start_time,
            'end': end_time,
            'limit': 1000  # Max limit
        }
        
        return await self.make_request(url, params=params)
    
    async def get_funding_rate_history(self, symbol: str, start_time: int, end_time: int) -> Optional[Dict]:
        """
        Get funding rate history.
        
        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT')
            start_time: Start timestamp (milliseconds)
            end_time: End timestamp (milliseconds)
            
        Returns:
            Funding rate data or None if failed
        """
        url = f"{self.base_url}/v5/market/funding/history"
        params = {
            'category': self.category,
            'symbol': symbol,
            'startTime': start_time,
            'endTime': end_time,
            'limit': 200  # Max limit
        }
        
        return await self.make_request(url, params=params)
    
    def _convert_kline_to_ohlcv(self, kline_data: Dict, symbol: str, data_type: str = "futures") -> List[Dict]:
        """
        Convert Bybit kline data to OHLCV format.
        
        Args:
            kline_data: Raw kline data from API
            symbol: Trading symbol
            data_type: Type of data ("futures", "spot")
            
        Returns:
            List of OHLCV records
        """
        if not kline_data or 'result' not in kline_data:
            return []
        
        result = kline_data['result']
        if 'list' not in result:
            return []
        
        klines = result['list']
        ohlcv_records = []
        
        for kline in klines:
            # Bybit kline format: [startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover]
            if len(kline) >= 6:
                timestamp_ms = int(kline[0])
                
                record = {
                    'timestamp': datetime.utcfromtimestamp(timestamp_ms / 1000).isoformat() + 'Z',
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'source': 'bybit',
                    'symbol': symbol,
                    'data_type': data_type
                }
                
                # Add turnover if available
                if len(kline) >= 7:
                    record['turnover'] = float(kline[6])
                
                ohlcv_records.append(record)
        
        return ohlcv_records
    
    def _convert_funding_rates(self, funding_data: Dict, symbol: str) -> List[Dict]:
        """
        Convert Bybit funding rate data to standard format.
        
        Args:
            funding_data: Raw funding rate data from API
            symbol: Trading symbol
            
        Returns:
            List of funding rate records
        """
        if not funding_data or 'result' not in funding_data:
            return []
        
        result = funding_data['result']
        if 'list' not in result:
            return []
        
        funding_list = result['list']
        funding_records = []
        
        for funding in funding_list:
            record = {
                'funding_timestamp': datetime.utcfromtimestamp(int(funding['fundingRateTimestamp']) / 1000).isoformat() + 'Z',
                'funding_rate': float(funding['fundingRate']),
                'symbol': funding['symbol'],
                'source': 'bybit'
            }
            funding_records.append(record)
        
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
        self.logger.info(f"Using optimized 40-day chunks (1000 records per request) for maximum efficiency")
        
        # Convert dates to millisecond timestamps
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)
        
        all_records = []
        current_start = start_ms
        
        # Map timeframe to Bybit interval
        interval_map = {
            '1m': '1',   # 1 minute
            '1h': '60'   # 1 hour
        }
        interval = interval_map.get(timeframe, '60')
        
        # Bybit has a 1000 record limit per request, so we need to paginate
        # Adjust chunk size based on timeframe
        if timeframe == '1m':
            chunk_days = 1  # 1 day for minute data (1440 records max)
        else:
            chunk_days = 40  # Use almost full 1000 record limit for hourly data
        chunk_ms = chunk_days * 24 * 60 * 60 * 1000
        
        while current_start < end_ms:
            current_end = min(current_start + chunk_ms, end_ms)
            
            self.logger.info(f"  Fetching chunk: {datetime.fromtimestamp(current_start/1000)} to {datetime.fromtimestamp(current_end/1000)}")
            
            kline_data = await self.get_kline_data(symbol, interval, current_start, current_end)
            
            if kline_data:
                chunk_records = self._convert_kline_to_ohlcv(kline_data, symbol, "futures")
                all_records.extend(chunk_records)
                self.logger.info(f"    ✅ Got {len(chunk_records)} records")
            else:
                self.logger.warning(f"    ❌ Failed to get data for chunk")
            
            current_start = current_end + 1
            # No sleep needed - rate limiter handles this efficiently
        
        # Sort by timestamp (Bybit returns newest first)
        all_records.sort(key=lambda x: x['timestamp'])
        
        # Save data if we got any
        success = len(all_records) > 0
        filepath = None
        
        if success:
            filename = f"bybit_{symbol}_perp_{timeframe}_{start_date}_{end_date}.csv"
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
        current_end = end_ms  # Bybit funding API works backwards
        
        # Funding rates are every 8 hours, 200 limit = ~66 days
        chunk_days = 60
        chunk_ms = chunk_days * 24 * 60 * 60 * 1000
        
        while current_end > start_ms:
            current_start = max(current_end - chunk_ms, start_ms)
            
            self.logger.info(f"  Fetching chunk: {datetime.fromtimestamp(current_start/1000)} to {datetime.fromtimestamp(current_end/1000)}")
            
            funding_data = await self.get_funding_rate_history(symbol, current_start, current_end)
            
            if funding_data:
                chunk_records = self._convert_funding_rates(funding_data, symbol)
                all_records.extend(chunk_records)
                self.logger.info(f"    ✅ Got {len(chunk_records)} records")
            else:
                self.logger.warning(f"    ❌ Failed to get data for chunk")
            
            current_end = current_start - 1
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
            filename = f"bybit_{symbol}_funding_rates_{start_date}_{end_date}.csv"
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
    
    async def download_spot_ohlcv(self, symbol: str, start_date: str, end_date: str) -> Dict:
        """
        Download spot OHLCV data for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Download result dictionary
        """
        self.logger.info(f"Downloading {symbol} spot OHLCV from {start_date} to {end_date}")
        self.logger.info(f"Using optimized 40-day chunks (1000 records per request) for maximum efficiency")
        
        # Convert dates to millisecond timestamps
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)
        
        all_records = []
        current_start = start_ms
        
        # Bybit has a 1000 record limit per request, so we need to paginate
        # For 1-hour data, 1000 records = ~41.7 days (much more efficient!)
        chunk_days = 40  # Use almost full 1000 record limit for hourly data
        chunk_ms = chunk_days * 24 * 60 * 60 * 1000
        
        while current_start < end_ms:
            current_end = min(current_start + chunk_ms, end_ms)
            
            self.logger.info(f"  Fetching chunk: {datetime.fromtimestamp(current_start/1000)} to {datetime.fromtimestamp(current_end/1000)}")
            
            kline_data = await self.get_spot_kline_data(symbol, '60', current_start, current_end)
            
            if kline_data:
                chunk_records = self._convert_kline_to_ohlcv(kline_data, symbol, "spot")
                all_records.extend(chunk_records)
                self.logger.info(f"    ✅ Got {len(chunk_records)} records")
            else:
                self.logger.warning(f"    ❌ Failed to get data for chunk")
            
            current_start = current_end + 1
            # No sleep needed - rate limiter handles this efficiently
        
        # Sort by timestamp (Bybit returns newest first)
        all_records.sort(key=lambda x: x['timestamp'])
        
        # Save data if we got any
        success = len(all_records) > 0
        filepath = None
        
        if success:
            filename = f"bybit_{symbol}_spot_1h_{start_date}_{end_date}.csv"
            required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
            if self.validate_data(all_records, required_fields):
                # Save to appropriate directory based on context
                original_output_dir = self.output_dir
                if hasattr(self, 'eth_usd_dir') and "spot_prices" in str(self.output_dir):
                    # Save to eth_usd subdirectory for spot data
                    self.output_dir = self.eth_usd_dir
                else:
                    # Save to spot_ohlcv subdirectory for derivatives context
                    self.output_dir = self.spot_ohlcv_dir
                filepath = self.save_to_csv(all_records, filename)
                self.output_dir = original_output_dir
        
        return {
            'success': success,
            'symbol': symbol,
            'record_count': len(all_records),
            'output_file': str(filepath) if filepath else None,
            'date_range': f"{start_date} to {end_date}",
            'data_type': 'spot_ohlcv'
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
        
        self.logger.info(f"Starting futures data download for {len(self.futures_symbols)} symbols")
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
        report_file = self.save_report(report, f"bybit_futures_report_{start_date}_{end_date}.json")
        
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
