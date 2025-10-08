"""
Fast Alchemy API client for historical gas prices.

Optimized version with:
- Dual API key round-robin
- Reduced timeouts and retries
- Optimized block search
- Connection pooling

🔑 API KEY SETUP REQUIRED:
This client requires Alchemy API keys for Ethereum RPC access.

1. Get Alchemy API keys from: https://www.alchemy.com/
2. Add them to backend/env.unified:
   BASIS_DOWNLOADERS__ALCHEMY_API_KEY=your_first_api_key_here
   BASIS_DOWNLOADERS__ALCHEMY_API_KEY_2=your_second_api_key_here

3. Load environment variables before running:
   source scripts/load_env.sh
   python scripts/downloaders/clients/alchemy_client_fast.py

⚠️  WITHOUT API KEYS: Uses hardcoded fallback keys (may have rate limits)
✅  WITH API KEYS: Full rate limits and optimized performance
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Handle both standalone and module imports
try:
    from ..base_downloader import BaseDownloader
except ImportError:
    # Standalone execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from base_downloader import BaseDownloader


class FastAlchemyClient(BaseDownloader):
    """
    Fast Alchemy API client with dual API key support.
    
    Optimizations:
    - Round-robin between two API keys
    - Reduced timeouts and retries
    - Optimized block search algorithms
    - Better progress tracking
    """
    
    def __init__(self, output_dir: str = "data/blockchain_data/gas_prices"):
        super().__init__("alchemy_fast", output_dir, rate_limit_per_minute=1200)  # 20 RPS with dual keys
        
        # Set up dual API keys
        import os
        key1 = os.environ.get("BASIS_DOWNLOADERS__ALCHEMY_API_KEY", "vV3z-UCRtQvWb26MH9v7A")
        key2 = os.environ.get("BASIS_DOWNLOADERS__ALCHEMY_API_KEY_2", "1M1peQWH1C6iT6c91YPMO")
        
        self.api_urls = [
            f"https://eth-mainnet.g.alchemy.com/v2/{key1}",
            f"https://eth-mainnet.g.alchemy.com/v2/{key2}"
        ]
        
        self.current_api_index = 0
        
        # Optimized settings - more conservative for log queries
        self.req_timeout = 15  # Longer timeout for complex queries
        self.max_retries = 3   # More retries for reliability
        self.base_sleep = 0.1  # Longer base sleep
        
        # Session for connection pooling
        self.session = None
        
        self.logger.info(f"Fast Alchemy client initialized with {len(self.api_urls)} API keys")
    
    async def _get_session(self):
        """Get or create aiohttp session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.req_timeout)
            connector = aiohttp.TCPConnector(limit=50, limit_per_host=25)
            self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self.session
    
    async def _rpc(self, method: str, params: List[Any]) -> Any:
        """Fast JSON-RPC call with round-robin API selection."""
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        
        # Round-robin API selection
        api_url = self.api_urls[self.current_api_index]
        self.current_api_index = (self.current_api_index + 1) % len(self.api_urls)
        
        session = await self._get_session()
        
        for attempt in range(self.max_retries):
            try:
                async with session.post(api_url, json=payload) as response:
                    if response.status == 200:
                        j = await response.json()
                        if "error" not in j:
                            return j["result"]
                        # Rate limit error - quick backoff
                        await asyncio.sleep(self.base_sleep)
                    # Quick retry on non-200
            except (aiohttp.ClientError, asyncio.TimeoutError):
                pass
                
            await asyncio.sleep(self.base_sleep)
            
        raise RuntimeError(f"RPC failed for {method} after {self.max_retries} retries")
    
    async def get_block_timestamp(self, num: int) -> int:
        """Get block timestamp quickly."""
        block = await self._rpc("eth_getBlockByNumber", [hex(num), False])
        return int(block["timestamp"], 16)
    
    async def fee_history_for_block(self, block_num: int) -> tuple:
        """Get fee history for a block."""
        res = await self._rpc("eth_feeHistory", [1, hex(block_num), [25.0, 50.0, 75.0]])
        base_fee_curr = int(res["baseFeePerGas"][-1], 16)
        rewards = res.get("reward", [[]])
        
        if not rewards or not rewards[0]:
            prios = [0, 0, 0]
        else:
            prios = [int(x, 16) for x in rewards[0]]
            
        return base_fee_curr, prios
    
    async def get_latest_block_number(self) -> int:
        """Get latest block number."""
        latest = await self._rpc("eth_blockNumber", [])
        return int(latest, 16)
    
    async def find_start_block_fast(self, target_ts: int, latest_block: int) -> int:
        """Fast start block finding using estimation."""
        # Estimate based on 12-second block time
        latest_ts = await self.get_block_timestamp(latest_block)
        seconds_diff = latest_ts - target_ts
        estimated_blocks_back = int(seconds_diff / 12)
        
        # Start search from estimate
        start_block = max(0, latest_block - estimated_blocks_back)
        
        # Quick binary search in a small window
        window = 1000  # Small search window
        lo = max(0, start_block - window)
        hi = min(latest_block, start_block + window)
        
        # Simple binary search
        while lo <= hi:
            mid = (lo + hi) // 2
            ts = await self.get_block_timestamp(mid)
            
            if ts >= target_ts:
                hi = mid - 1
            else:
                lo = mid + 1
        
        return lo
    
    async def get_hourly_gas_prices_fast(self, start_date: str, end_date: str) -> List[Dict]:
        """Fast hourly gas price collection."""
        self.logger.info(f"Fast gas price collection: {start_date} to {end_date}")
        
        # Parse dates
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
        
        # Get latest block
        latest = await self.get_latest_block_number()
        self.logger.info(f"Latest block: {latest}")
        
        # Find start block quickly
        start_block = await self.find_start_block_fast(int(start_dt.timestamp()), latest)
        self.logger.info(f"Start block: {start_block}")
        
        # Generate hourly timestamps
        hours = []
        cur = start_dt
        while cur <= end_dt:
            hours.append(cur)
            cur += timedelta(hours=1)
            
        self.logger.info(f"Processing {len(hours)} hours")
        
        results = []
        current_block = start_block
        ema_block_time = 12.0
        prev_ts = None
        
        for i, dt in enumerate(hours):
            if i % 24 == 0:
                progress_pct = (i / len(hours)) * 100
                elapsed = (datetime.now() - datetime.strptime(start_date, '%Y-%m-%d')).total_seconds() if i > 0 else 0
                rate = i / (elapsed / 3600) if elapsed > 0 else 0
                eta = (len(hours) - i) / rate if rate > 0 else 0
                self.logger.info(f"Day {dt.date()} ({i}/{len(hours)} - {progress_pct:.1f}% - {rate:.1f} hrs/hr - ETA: {eta:.1f}h)")
                
            target_ts = int(dt.timestamp())
            
            # Quick block estimation (no expensive search)
            if i > 0:
                step = max(1, int(round((3600.0 / ema_block_time))))
                current_block += step
            
            # Simple bounds check
            current_block = min(current_block, latest)
            current_block = max(current_block, 0)
            
            # Get block timestamp (quick check if we're close)
            ts = await self.get_block_timestamp(current_block)
            
            # Quick adjustment if needed (max 3 attempts)
            adjust_attempts = 0
            while abs(ts - target_ts) > 3600 and adjust_attempts < 3:  # Within 1 hour
                if ts < target_ts:
                    current_block += max(1, int((target_ts - ts) / 12))
                else:
                    current_block -= max(1, int((ts - target_ts) / 12))
                
                current_block = min(current_block, latest)
                current_block = max(current_block, 0)
                ts = await self.get_block_timestamp(current_block)
                adjust_attempts += 1
            
            # Update EMA
            if i > 0:
                obs_bt = max(1.0, float(ts - prev_ts))
                ema_block_time = 0.1 * obs_bt + 0.9 * ema_block_time
            prev_ts = ts
            
            # Get fee history (this uses round-robin API automatically)
            base_fee, prios = await self.fee_history_for_block(current_block)
            p25, p50, p75 = prios
            
            # Convert to Gwei
            base_fee_gwei = base_fee / 1e9
            p25_gwei = p25 / 1e9
            p50_gwei = p50 / 1e9
            p75_gwei = p75 / 1e9
            effective_gwei = (base_fee + p50) / 1e9
            
            results.append({
                "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "chain": "ethereum",
                "block_number": current_block,
                "block_timestamp": ts,
                "gas_price_gwei": round(effective_gwei, 2),
                "gas_price_avg_gwei": round(effective_gwei, 2),
                "gas_price_median_gwei": round((base_fee + p25) / 1e9, 2),
                "base_fee_gwei": round(base_fee_gwei, 2),
                "priority_fee_p25_gwei": round(p25_gwei, 2),
                "priority_fee_p50_gwei": round(p50_gwei, 2),
                "priority_fee_p75_gwei": round(p75_gwei, 2),
                "source": "alchemy_rpc_fast",
                "note": "Real historical data via eth_feeHistory (optimized)"
            })
        
        # Clean up
        if self.session:
            await self.session.close()
            self.session = None
            
        return results
    
    async def download_gas_data(self, start_date: str, end_date: str) -> Dict:
        """Download gas data using fast method."""
        try:
            gas_records = await self.get_hourly_gas_prices_fast(start_date, end_date)
            
            if gas_records:
                filename = f"ethereum_gas_prices_{start_date}_{end_date}.csv"
                filepath = self.save_to_csv(gas_records, filename)
                
                return {
                    'success': True,
                    'chain': 'ethereum',
                    'record_count': len(gas_records),
                    'output_file': str(filepath),
                    'date_range': f"{start_date} to {end_date}",
                    'data_source': 'alchemy_rpc_fast'
                }
            else:
                return {
                    'success': False,
                    'chain': 'ethereum',
                    'error': 'No data collected',
                    'record_count': 0
                }
                
        except Exception as e:
            self.logger.error(f"Fast download failed: {e}")
            return {
                'success': False,
                'chain': 'ethereum',
                'error': str(e),
                'record_count': 0
            }
    
    async def download_all_gas_data(self, start_date: str, end_date: str) -> Dict:
        """Download all gas data using fast method."""
        result = await self.download_gas_data(start_date, end_date)
        download_results = [result]
        
        report = self.create_summary_report(download_results)
        report_file = self.save_report(report, f"alchemy_fast_report_{start_date}_{end_date}.json")
        
        return report
    
    async def get_logs(self, from_block: str, to_block: str, address: str = None, topics: list = None) -> list:
        """Get logs for specified block range and filters."""
        params = {
            "fromBlock": from_block,
            "toBlock": to_block
        }
        
        if address:
            params["address"] = address
        if topics:
            params["topics"] = topics
            
        return await self._rpc("eth_getLogs", [params])
    
    async def get_transaction_by_hash(self, tx_hash: str) -> dict:
        """Get transaction details by hash."""
        return await self._rpc("eth_getTransactionByHash", [tx_hash])
    
    async def get_transaction_receipt(self, tx_hash: str) -> dict:
        """Get transaction receipt by hash.""" 
        return await self._rpc("eth_getTransactionReceipt", [tx_hash])

    async def download_data(self, start_date: str, end_date: str) -> Dict:
        """Main download method."""
        return await self.download_all_gas_data(start_date, end_date)
