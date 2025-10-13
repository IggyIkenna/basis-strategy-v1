"""
OKX API client for perpetual futures data.

Handles:
- Perpetual futures OHLCV (1H candles)
- Funding rate history (8h)
- Public endpoints (no API key)
- Rate limiting (~20 req/sec => 1200/min)
"""

import asyncio
import aiohttp
import zipfile
import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from .timestamp_utils import format_timestamp_utc, format_timestamp_from_datetime

# Handle both standalone and module imports
try:
    from ..base_downloader import BaseDownloader
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from base_downloader import BaseDownloader


class OKXClient(BaseDownloader):
    """
    OKX API client for perpetual futures data.
    """

    def __init__(self, output_dir: str = "data/market_data/derivatives"):
        # OKX market-data-history endpoint has rate limit of 5 requests per 2 seconds
        # This is 2.5 rps = 150 rpm, but we'll be conservative
        super().__init__("okx", output_dir, rate_limit_per_minute=120)  # Conservative rate limit

        # Subdirs
        self.futures_ohlcv_dir = Path(output_dir) / "futures_ohlcv"
        self.funding_rates_dir = Path(output_dir) / "funding_rates"
        self.futures_ohlcv_dir.mkdir(parents=True, exist_ok=True)
        self.funding_rates_dir.mkdir(parents=True, exist_ok=True)

        self.base_url = "https://www.okx.com"

        # Perp instruments
        self.futures_symbols = ["ETH-USDT-SWAP", "BTC-USDT-SWAP"]
        self.inst_type = "SWAP"

        self.logger.info(f"OKX client initialized with {len(self.futures_symbols)} symbols")

    # ---------- Low-level API ----------

    async def get_candlesticks(
        self,
        inst_id: str,
        bar: str,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 300,
    ) -> Optional[Dict[str, Any]]:
        """
        GET /api/v5/market/candles
        OKX returns newest-first arrays: [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm]
        """
        url = f"{self.base_url}/api/v5/market/candles"
        params = {"instId": inst_id, "bar": bar, "limit": min(limit, 300)}
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        return await self.make_request(url, params=params)

    async def get_history_candlesticks(
        self,
        inst_id: str,
        bar: str,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100,
    ) -> Optional[Dict[str, Any]]:
        """
        GET /api/v5/market/history-candles
        OKX returns newest-first arrays for historical data: [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm]
        """
        url = f"{self.base_url}/api/v5/market/history-candles"
        params = {"instId": inst_id, "bar": bar, "limit": min(limit, 100)}
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        return await self.make_request(url, params=params)

    async def get_market_data_history(
        self,
        module: int,
        inst_type: str,
        inst_family_list: str,
        date_aggr_type: str,
        begin: str,
        end: str,
    ) -> Optional[Dict[str, Any]]:
        """
        GET /api/v5/market-data-history
        Get historical data files from OKX.
        
        Args:
            module: Data module type (1: Trade, 2: 1-minute candlestick, 3: Funding rate)
            inst_type: Instrument type (SPOT, FUTURES, SWAP, OPTION)
            inst_family_list: Instrument family list (e.g., "ETH-USDT")
            date_aggr_type: Date aggregation type (daily, monthly)
            begin: Begin timestamp in milliseconds
            end: End timestamp in milliseconds
        """
        url = f"{self.base_url}/api/v5/public/market-data-history"
        params = {
            "module": str(module),
            "instType": inst_type,
            "instFamilyList": inst_family_list,
            "dateAggrType": date_aggr_type,
            "begin": begin,
            "end": end,
        }
        return await self.make_request(url, params=params)

    async def download_via_history_candles(self, inst_id: str, start_date: str, end_date: str, bar_size: str = "1H") -> List[Dict[str, Any]]:
        """
        Download OHLCV data using the regular candles endpoint.
        This is used for recent data (2025).
        """
        symbol_out = self._normalize_symbol(inst_id)
        self.logger.info(f"Using regular candles endpoint for {symbol_out} from {start_date} to {end_date}")
        
        # Convert dates to millisecond timestamps
        start_ms = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
        end_ms = int((datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)).timestamp() * 1000) - 1
        
        self.logger.info(f"  Timestamp range: {start_ms} to {end_ms}")
        self.logger.info(f"  Date range: {datetime.fromtimestamp(start_ms/1000)} to {datetime.fromtimestamp(end_ms/1000)}")
        
        all_records: List[Dict[str, Any]] = []
        
        try:
            # Use the regular candles endpoint with high limit to get recent data
            # This endpoint returns up to 300 records of recent data
            payload = await self.get_candlesticks(inst_id, bar_size, limit=1000)
            
            if not payload or not payload.get("data"):
                self.logger.warning("  No data returned from candles endpoint")
                return []
            
            page_records = self._convert_candlesticks_to_ohlcv(payload, symbol_out, "futures")
            if not page_records:
                self.logger.warning("  No records in response")
                return []
            
            # Filter to the requested date range
            in_range = []
            for r in page_records:
                ts_ms = int(datetime.fromisoformat(r["timestamp"].replace("Z", "")).timestamp() * 1000)
                if start_ms <= ts_ms <= end_ms:
                    in_range.append(r)
            
            all_records.extend(in_range)
            self.logger.info(f"  Got {len(page_records)} total records, {len(in_range)} in requested range")
            
        except Exception as e:
            self.logger.error(f"  ❌ Error fetching data: {e}")
            return []
        
        # Sort oldest→newest
        all_records.sort(key=lambda x: x["timestamp"])
        
        self.logger.info(f"  Downloaded {len(all_records)} records via candles endpoint")
        return all_records

    def resample_1m_to_1h(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Resample 1-minute candlestick data to 1-hour candlesticks.
        
        Args:
            records: List of 1-minute OHLCV records
            
        Returns:
            List of 1-hour OHLCV records
        """
        if not records:
            return []
        
        # Group records by hour
        hourly_data = defaultdict(list)
        
        for record in records:
            # Parse timestamp and round down to the hour
            dt = datetime.fromisoformat(record["timestamp"].replace("Z", ""))
            hour_key = dt.replace(minute=0, second=0, microsecond=0)
            hourly_data[hour_key].append(record)
        
        # Create 1-hour candles from grouped data
        hourly_candles = []
        
        for hour_key in sorted(hourly_data.keys()):
            minute_records = hourly_data[hour_key]
            
            if not minute_records:
                continue
            
            # Sort by timestamp to ensure proper order
            minute_records.sort(key=lambda x: x["timestamp"])
            
            # Create 1-hour candle
            open_price = minute_records[0]["open"]
            close_price = minute_records[-1]["close"]
            high_price = max(record["high"] for record in minute_records)
            low_price = min(record["low"] for record in minute_records)
            total_volume = sum(record["volume"] for record in minute_records)
            
            hourly_candle = {
                "timestamp": format_timestamp_from_datetime(hour_key),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": total_volume,
                "source": minute_records[0]["source"],
                "symbol": minute_records[0]["symbol"],
                "data_type": minute_records[0]["data_type"]
            }
            
            hourly_candles.append(hourly_candle)
        
        return hourly_candles

    async def _download_via_market_data_history(self, inst_id: str, start_date: str, end_date: str) -> Tuple[List[Dict[str, Any]], int, int]:
        """
        Download data using the market-data-history endpoint.
        Returns (records, files_processed, files_failed)
        """
        # Convert dates to millisecond timestamps
        start_ms = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
        end_ms = int((datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)).timestamp() * 1000) - 1
        
        # Extract instrument family from inst_id (e.g., "ETH-USDT-SWAP" -> "ETH-USDT")
        inst_family = inst_id.replace("-SWAP", "").replace("-PERP", "")
        
        all_records: List[Dict[str, Any]] = []
        files_processed = 0
        failed_files = 0

        try:
            # Request historical data files using market-data-history endpoint
            payload = await self.get_market_data_history(
                module=2,  # 1-minute candlestick
                inst_type="SWAP",
                inst_family_list=inst_family,
                date_aggr_type="monthly",
                begin=str(start_ms),
                end=str(end_ms)
            )

            if not payload or not payload.get("data"):
                self.logger.warning("No historical data files available")
                return [], 0, 0

            # Process each data group
            for data_group in payload["data"]:
                for detail in data_group.get("details", []):
                    for group_detail in detail.get("groupDetails", []):
                        file_url = group_detail.get("url")
                        filename = group_detail.get("filename", "unknown")
                        
                        if not file_url:
                            self.logger.warning(f"No URL for {filename}")
                            failed_files += 1
                            continue

                        # Download and process the file (1-minute data)
                        file_records_1m = await self.download_and_process_historical_file(file_url, filename)
                        
                        if file_records_1m:
                            # Filter 1-minute records to the requested date range
                            filtered_1m_records = []
                            for record in file_records_1m:
                                try:
                                    ts_ms = int(datetime.fromisoformat(record["timestamp"].replace("Z", "")).timestamp() * 1000)
                                    if start_ms <= ts_ms <= end_ms:
                                        filtered_1m_records.append(record)
                                except ValueError:
                                    continue
                            
                            # Resample 1-minute data to 1-hour data
                            hourly_records = self.resample_1m_to_1h(filtered_1m_records)
                            
                            all_records.extend(hourly_records)
                            files_processed += 1
                            self.logger.info(f"  Added {len(hourly_records)} hourly records (from {len(filtered_1m_records)} 1m records) from {filename}")
                        else:
                            failed_files += 1
                        
                        # Rate limiting: 5 requests per 2 seconds
                        await asyncio.sleep(0.4)  # 400ms delay between requests

        except Exception as e:
            self.logger.error(f"Error fetching historical data: {e}")
            return [], files_processed, failed_files + 1

        return all_records, files_processed, failed_files

    def determine_endpoints_to_use(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Determine which endpoints to use based on the date range.
        
        Returns:
            Dict with endpoint configuration
        """
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # OKX market-data-history is available from August 2024 to August 31, 2025
        market_data_history_start = datetime(2024, 8, 1)
        market_data_history_end = datetime(2025, 8, 31, 23, 59, 59)
        
        # Regular candles endpoint is available for September 2025 onwards
        history_candles_start = datetime(2025, 9, 1)
        
        use_market_data_history = end_dt >= market_data_history_start
        use_history_candles = start_dt >= history_candles_start
        
        # Determine date ranges for each endpoint
        market_data_range = None
        history_candles_range = None
        
        if use_market_data_history:
            market_start = max(start_dt, market_data_history_start)
            market_end = min(end_dt, market_data_history_end)
            
            
            if market_start <= market_end:
                market_data_range = {
                    "start": market_start.strftime("%Y-%m-%d"),
                    "end": market_end.strftime("%Y-%m-%d")
                }
        
        if use_history_candles:
            history_start = max(start_dt, history_candles_start)
            history_end = end_dt
            if history_start <= history_end:
                history_candles_range = {
                    "start": history_start.strftime("%Y-%m-%d"),
                    "end": history_end.strftime("%Y-%m-%d")
                }
        
        return {
            "use_market_data_history": use_market_data_history and market_data_range is not None,
            "use_history_candles": use_history_candles and history_candles_range is not None,
            "market_data_range": market_data_range,
            "history_candles_range": history_candles_range
        }

    async def download_and_process_historical_file(self, url: str, filename: str) -> List[Dict[str, Any]]:
        """
        Download and process a historical data file from OKX.
        
        Args:
            url: Download URL for the historical data file
            filename: Filename for logging purposes
            
        Returns:
            List of processed OHLCV records
        """
        try:
            self.logger.info(f"  Downloading {filename}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        self.logger.error(f"  Failed to download {filename}: HTTP {response.status}")
                        return []
                    
                    # Read the zip file content
                    zip_content = await response.read()
                    
                    # Extract and process the zip file
                    with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
                        # Find CSV files in the zip
                        csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]
                        
                        if not csv_files:
                            self.logger.warning(f"  No CSV files found in {filename}")
                            return []
                        
                        all_records = []
                        for csv_file in csv_files:
                            self.logger.info(f"    Processing {csv_file}")
                            
                            # Read CSV content
                            with zip_file.open(csv_file) as f:
                                csv_content = f.read().decode('utf-8')
                                
                                # Parse CSV and convert to OHLCV format
                                lines = csv_content.strip().split('\n')
                                for line in lines[1:]:  # Skip header
                                    try:
                                        parts = line.split(',')
                                        if len(parts) >= 9:
                                            # OKX historical data format: instrument_name, open, high, low, close, vol, vol_ccy, vol_quote, open_time, confirm
                                            instrument_name = parts[0]
                                            open_price = float(parts[1])
                                            high_price = float(parts[2])
                                            low_price = float(parts[3])
                                            close_price = float(parts[4])
                                            volume = float(parts[5])
                                            timestamp_ms = int(parts[8])  # open_time is the timestamp
                                            
                                            record = {
                                                'timestamp': format_timestamp_utc(timestamp_ms),
                                                'open': open_price,
                                                'high': high_price,
                                                'low': low_price,
                                                'close': close_price,
                                                'volume': volume,
                                                'source': 'okx',
                                                'symbol': 'ETHUSDT',  # Normalized symbol
                                                'data_type': 'futures'
                                            }
                                            all_records.append(record)
                                    except (ValueError, IndexError) as e:
                                        self.logger.warning(f"    Skipping invalid line: {e}")
                                        continue
                        
                        self.logger.info(f"  Processed {len(all_records)} records from {filename}")
                        return all_records
                        
        except Exception as e:
            self.logger.error(f"  Error processing {filename}: {e}")
            return []

    async def get_funding_rate_history(
        self,
        inst_id: str,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100,
    ) -> Optional[Dict[str, Any]]:
        """
        GET /api/v5/public/funding-rate-history
        OKX returns newest-first; items may be arrays or objects depending on SDKs.
        """
        url = f"{self.base_url}/api/v5/public/funding-rate-history"
        params = {"instId": inst_id, "limit": min(limit, 100)}
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        return await self.make_request(url, params=params)

    # ---------- Converters ----------

    def _convert_candlesticks_to_ohlcv(
        self, payload: Dict[str, Any], symbol_out: str, data_type: str = "futures"
    ) -> List[Dict[str, Any]]:
        if not payload or "data" not in payload:
            return []
        rows = payload["data"]
        ohlcv: List[Dict[str, Any]] = []

        for row in rows:
            # Row can be array or dict; normalize
            if isinstance(row, list):
                if len(row) < 6:
                    continue
                ts_ms = int(row[0])
                o, h, l, c, v = row[1], row[2], row[3], row[4], row[5]
                vol_quote = None
                if len(row) >= 8:
                    try:
                        vol_quote = float(row[7])
                    except Exception:
                        vol_quote = None
            elif isinstance(row, dict):
                # Some wrappers return objects
                ts_ms = int(row.get("ts") or row.get("timestamp"))
                o = row.get("open")
                h = row.get("high")
                l = row.get("low")
                c = row.get("close")
                v = row.get("volume") or row.get("vol")
                vol_quote = row.get("volumeQuote") or row.get("volCcyQuote")
            else:
                continue

            try:
                rec = {
                    "timestamp": format_timestamp_utc(ts_ms),
                    "open": float(o),
                    "high": float(h),
                    "low": float(l),
                    "close": float(c),
                    "volume": float(v),
                    "source": "okx",
                    "symbol": symbol_out,
                    "data_type": data_type,
                }
                if vol_quote is not None:
                    rec["volume_quote"] = float(vol_quote)
                ohlcv.append(rec)
            except Exception:
                # Skip malformed row
                continue

        return ohlcv

    def _convert_funding_rates(self, payload: Dict[str, Any], symbol_out: str) -> List[Dict[str, Any]]:
        if not payload or "data" not in payload:
            return []
        rows = payload["data"]
        out: List[Dict[str, Any]] = []

        for row in rows:
            # Row may be array or dict
            if isinstance(row, list):
                # [instType, instId, fundingRate, nextFundingRate, fundingTime, nextFundingTime, settleFundingRate, settleFundingTime]
                if len(row) < 5:
                    continue
                inst_id = row[1]
                fr = row[2]
                ft = row[4]
            elif isinstance(row, dict):
                inst_id = row.get("instId")
                fr = row.get("fundingRate")
                ft = row.get("fundingTime")
            else:
                continue

            try:
                rec = {
                    "funding_timestamp": format_timestamp_utc(int(ft)),
                    "funding_rate": float(fr),
                    "symbol": inst_id or symbol_out,
                    "source": "okx",
                }
                out.append(rec)
            except Exception:
                continue

        return out

    # ---------- High-level downloaders ----------

    @staticmethod
    def _normalize_symbol(inst_id: str) -> str:
        # For filenames and CSV contents (matches Binance style: ETHUSDT)
        return inst_id.replace("-USDT-SWAP", "USDT").replace("-", "")

    async def download_futures_ohlcv(self, inst_id: str, start_date: str, end_date: str, timeframe: str = "1h") -> Dict:
        """
        Fetch OHLCV for a perp instrument using hybrid endpoint strategy.
        Uses market-data-history for 2024 data and history-candles for 2025 data.
        
        Args:
            inst_id: Instrument ID (e.g., 'ETH-USDT-SWAP')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Data timeframe ('1m' or '1h')
        """
        symbol_out = self._normalize_symbol(inst_id)
        
        # Map timeframe to OKX bar size
        bar_map = {
            '1m': '1m',   # 1 minute
            '1h': '1H'    # 1 hour
        }
        bar_size = bar_map.get(timeframe, '1H')
        self.logger.info(f"Downloading {symbol_out} futures OHLCV from {start_date} to {end_date}")

        # Determine which endpoints to use
        endpoint_config = self.determine_endpoints_to_use(start_date, end_date)
        
        self.logger.info(f"Endpoint strategy:")
        if endpoint_config["use_market_data_history"]:
            self.logger.info(f"  📁 Market-data-history: {endpoint_config['market_data_range']['start']} to {endpoint_config['market_data_range']['end']}")
        if endpoint_config["use_history_candles"]:
            self.logger.info(f"  🔄 History-candles: {endpoint_config['history_candles_range']['start']} to {endpoint_config['history_candles_range']['end']}")

        all_records: List[Dict[str, Any]] = []
        total_files_processed = 0
        total_files_failed = 0

        # Download data from market-data-history endpoint (2024 data)
        if endpoint_config["use_market_data_history"]:
            market_range = endpoint_config["market_data_range"]
            self.logger.info(f"📁 Downloading historical data from market-data-history endpoint...")
            
            market_records, files_processed, files_failed = await self._download_via_market_data_history(
                inst_id, market_range["start"], market_range["end"]
            )
            all_records.extend(market_records)
            total_files_processed += files_processed
            total_files_failed += files_failed

        # Download data from history-candles endpoint (2025 data)
        if endpoint_config["use_history_candles"]:
            history_range = endpoint_config["history_candles_range"]
            self.logger.info(f"🔄 Downloading recent data from history-candles endpoint...")
            
            history_records = await self.download_via_history_candles(
                inst_id, history_range["start"], history_range["end"], bar_size
            )
            
            # If history-candles returns no data, try to get the most recent available data
            if not history_records:
                self.logger.warning(f"⚠️  History-candles endpoint returned no data for {history_range['start']} to {history_range['end']}")
                self.logger.info(f"🔄 Trying to get the most recent available data...")
                
                # Try to get data from the last few days
                try:
                    recent_end = datetime.strptime(history_range["end"], "%Y-%m-%d")
                    recent_start = recent_end - timedelta(days=7)  # Try last 7 days
                    
                    history_records = await self.download_via_history_candles(
                        inst_id, recent_start.strftime("%Y-%m-%d"), history_range["end"], bar_size
                    )
                    
                    if history_records:
                        self.logger.info(f"✅ Got {len(history_records)} records from recent data")
                    else:
                        self.logger.warning(f"⚠️  No recent data available either")
                        
                except Exception as e:
                    self.logger.error(f"❌ Error trying to get recent data: {e}")
            
            all_records.extend(history_records)

        # Sort all records by timestamp
        all_records.sort(key=lambda x: x["timestamp"])

        # Save
        success = len(all_records) > 0
        filepath = None
        if success:
            filename = f"okx_{symbol_out}_perp_{timeframe}_{start_date}_{end_date}.csv"
            required_fields = ["timestamp", "open", "high", "low", "close", "volume"]
            if self.validate_data(all_records, required_fields):
                original_output_dir = self.output_dir
                self.output_dir = self.futures_ohlcv_dir
                filepath = self.save_to_csv(all_records, filename)
                self.output_dir = original_output_dir

        return {
            "success": success,
            "symbol": symbol_out,
            "record_count": len(all_records),
            "files_processed": total_files_processed,
            "files_failed": total_files_failed,
            "output_file": str(filepath) if filepath else None,
            "date_range": f"{start_date} to {end_date}",
            "data_type": "futures_ohlcv",
        }

    async def download_funding_rates(self, inst_id: str, start_date: str, end_date: str) -> Dict:
        """
        Fetch funding rates using backward pagination via 'before'.
        """
        symbol_out = self._normalize_symbol(inst_id)
        self.logger.info(f"Downloading {symbol_out} funding rates from {start_date} to {end_date}")

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int((end_dt + timedelta(days=1)).timestamp() * 1000) - 1  # inclusive

        all_records: List[Dict[str, Any]] = []
        current_before = str(end_ms)

        # Each page limit=100; funding every 8h => ~33 days/page
        while True:
            self.logger.info(
                f"  Fetching page ending before: {datetime.fromtimestamp(int(current_before)/1000)}"
            )
            payload = await self.get_funding_rate_history(inst_id, before=current_before, limit=100)

            if not payload or not payload.get("data"):
                self.logger.info("  No more funding data available")
                break

            chunk = self._convert_funding_rates(payload, symbol_out)
            if not chunk:
                break

            # Filter to requested range
            in_range = []
            for rec in chunk:
                ts = int(datetime.fromisoformat(rec["funding_timestamp"].replace("Z", "")).timestamp() * 1000)
                if start_ms <= ts <= end_ms:
                    in_range.append(rec)
            all_records.extend(in_range)
            self.logger.info(f"    ✅ Got {len(chunk)} records ({len(in_range)} in range)")

            # Oldest timestamp in this page for pagination
            # Payload rows could be list or dict; get their timestamp reliably
            def _row_ts_ms(row) -> int:
                if isinstance(row, list) and len(row) >= 5:
                    return int(row[4])
                if isinstance(row, dict):
                    return int(row.get("fundingTime"))
                return 0

            oldest_ms = min(_row_ts_ms(r) for r in payload["data"] if _row_ts_ms(r) > 0)
            if oldest_ms <= start_ms:
                break

            current_before = str(oldest_ms)
            await asyncio.sleep(0.05)

        # Sort oldest→newest + de-dup
        all_records.sort(key=lambda x: x["funding_timestamp"])
        seen = set()
        unique = []
        for rec in all_records:
            if rec["funding_timestamp"] not in seen:
                seen.add(rec["funding_timestamp"])
                unique.append(rec)

        # Save data if we got any
        success = len(unique) > 0
        filepath = None

        if success:
            filename = f"okx_{symbol_out}_funding_rates_{start_date}_{end_date}.csv"
            required_fields = ["funding_timestamp", "funding_rate", "symbol"]
            if self.validate_data(unique, required_fields):
                original_output_dir = self.output_dir
                self.output_dir = self.funding_rates_dir
                filepath = self.save_to_csv(unique, filename)
                self.output_dir = original_output_dir

        return {
            "success": success,
            "symbol": symbol_out,
            "record_count": len(unique),
            "output_file": str(filepath) if filepath else None,
            "date_range": f"{start_date} to {end_date}",
            "data_type": "funding_rates",
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
        
        self.logger.info(f"Starting OKX futures data download for {len(self.futures_symbols)} symbols")
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
        report_file = self.save_report(report, f"okx_futures_report_{start_date}_{end_date}.json")
        
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
