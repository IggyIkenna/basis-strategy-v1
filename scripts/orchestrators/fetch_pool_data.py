"""
Pool Data Orchestrator - CoinGecko Pool Downloads

Orchestrates all CoinGecko pool data downloads using unified downloader:
1. LST Pool Data (wstETH/WETH, weETH/WETH)
2. Spot Pool Data (WETH/USDT, EIGEN/WETH, ETHFI/WETH)

All pools are handled by a single unified downloader to avoid duplication.

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

Features:
- Enforces pool creation dates (no downloads before pool exists)
- Uses unified downloader to avoid duplication
- Handles all pools (LST + spot) in single downloader
- Comprehensive reporting

🔑 API KEY SETUP REQUIRED:
This orchestrator requires a CoinGecko Pro API key for historical data access.

1. Get a CoinGecko Pro API key from: https://www.coingecko.com/en/api/pricing
2. Add it to backend/env.unified:
   BASIS_DOWNLOADERS__COINGECKO_API_KEY=your_api_key_here

3. Load environment variables before running:
   source scripts/load_env.sh
   python scripts/orchestrators/fetch_pool_data.py --start-date 2020-01-01

⚠️  WITHOUT API KEY: Falls back to public API (180-day limit only)
✅  WITH API KEY: Full historical access from pool creation dates
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add the backend source to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "backend" / "src"))

# Handle both standalone and module imports
try:
    from ..downloaders.fetch_spot_pool_data import SpotDataDownloader
    from ..downloaders.base_downloader import BaseDownloader
except ImportError:
    # Standalone execution
    sys.path.append(str(Path(__file__).parent.parent))
    from downloaders.fetch_spot_pool_data import SpotDataDownloader
    from downloaders.base_downloader import BaseDownloader


class PoolDataOrchestrator(BaseDownloader):
    """
    Orchestrates all CoinGecko pool data downloads using unified approach.
    
    Coordinates:
    - LST pool data (wstETH/WETH, weETH/WETH)
    - Spot pool data (ETH/USDT, EIGEN/ETH, ETHFI/ETH)
    - Enforces pool creation dates
    - Uses single unified downloader to avoid duplication
    """
    
    def __init__(self, output_dir: str = "data/market_data"):
        super().__init__("pool_data_orchestrator", output_dir)
        
        # Pool creation dates (enforced minimums)
        self.pool_creation_dates = {
            "lst_pools": "2024-05-12",  # weETH pool creation date (earliest)
            "eth_usdt": "2024-01-01",   # WETH/USDT Uniswap v3 creation
            "eigen_eth": "2024-10-05",  # EIGEN/ETH Uniswap v3 creation
            "ethfi_eth": "2024-04-01"   # ETHFI/ETH Uniswap v3 creation
        }
        
        self.downloaders = {}
        self.failed_initializations = []
        
        # Initialize unified spot pool downloader (includes LST pools)
        try:
            self.downloaders['spot'] = SpotDataDownloader(f"{output_dir}/spot_prices")
            self.logger.info("✅ Unified spot pool downloader initialized (includes LST pools)")
        except Exception as e:
            self.logger.error(f"❌ Spot pool downloader failed: {e}")
            self.failed_initializations.append(('spot', str(e)))
        
        if not self.downloaders:
            raise RuntimeError("No pool downloaders could be initialized")
        
        self.logger.info(f"Pool data orchestrator initialized with {len(self.downloaders)} active downloaders")
        
        if self.failed_initializations:
            self.logger.warning(f"Failed to initialize {len(self.failed_initializations)} downloaders:")
            for name, error in self.failed_initializations:
                self.logger.warning(f"  - {name}: {error}")
    
    def _enforce_pool_creation_dates(self, start_date: str) -> Dict[str, str]:
        """
        Enforce pool creation dates - don't allow downloads before pools existed.
        
        Args:
            start_date: Requested start date
            
        Returns:
            Dict of actual start dates to use for each pool type
        """
        actual_dates = {}
        
        for pool_type, creation_date in self.pool_creation_dates.items():
            if start_date < creation_date:
                actual_dates[pool_type] = creation_date
                self.logger.info(f"📅 {pool_type}: Using creation date {creation_date} (requested {start_date})")
            else:
                actual_dates[pool_type] = start_date
                self.logger.info(f"📅 {pool_type}: Using requested date {start_date}")
        
        return actual_dates
    
    async def run_downloader(self, name: str, downloader, start_date: str, end_date: str) -> Dict:
        """
        Run a single downloader with error handling.
        
        Args:
            name: Downloader name
            downloader: Downloader instance
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Download result with metadata
        """
        self.logger.info(f"🚀 Starting {name} pool downloader...")
        start_time = datetime.now()
        
        try:
            # Set dates on downloader
            downloader.start_date = start_date
            if end_date:
                downloader.end_date = end_date
            
            result = await downloader.download_all_pools()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Add metadata
            result['downloader_name'] = name
            result['duration_seconds'] = duration
            result['start_time'] = start_time.isoformat()
            result['end_time'] = end_time.isoformat()
            
            successful = result.get('successful_downloads', 0)
            total = result.get('total_pools', 0)
            records = result.get('total_records', 0)
            
            self.logger.info(f"✅ {name}: {successful}/{total} pools, {records:,} records ({duration:.1f}s)")
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.error(f"❌ {name}: Failed after {duration:.1f}s - {e}")
            
            return {
                'downloader_name': name,
                'success': False,
                'error': str(e),
                'duration_seconds': duration,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_pools': 0,
                'successful_downloads': 0,
                'total_records': 0
            }
    
    async def download_data(self, start_date: str, end_date: str = None) -> Dict:
        """
        Run all pool data downloaders with enforced creation dates.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), None for present
            
        Returns:
            Master download results
        """
        self.logger.info("=" * 80)
        self.logger.info("🚀 POOL DATA ORCHESTRATOR STARTED")
        self.logger.info("=" * 80)
        self.logger.info(f"📅 Requested date range: {start_date} to {end_date or 'present'}")
        self.logger.info(f"🔧 Active downloaders: {', '.join(self.downloaders.keys())}")
        
        if self.failed_initializations:
            self.logger.warning(f"⚠️  Skipped downloaders: {', '.join(name for name, _ in self.failed_initializations)}")
        
        # Enforce pool creation dates
        actual_dates = self._enforce_pool_creation_dates(start_date)
        
        self.logger.info("=" * 80)
        
        master_start_time = datetime.now()
        downloader_results = []
        
        # Run unified spot pool downloader (includes LST pools)
        if 'spot' in self.downloaders:
            # Pass the individual pool creation dates to the downloader
            # The downloader will enforce these dates per pool
            downloader = self.downloaders['spot']
            downloader.pool_creation_dates = actual_dates
            result = await self.run_downloader('unified_pools', downloader, start_date, end_date)
            downloader_results.append(result)
        
        master_end_time = datetime.now()
        total_duration = (master_end_time - master_start_time).total_seconds()
        
        # Aggregate results
        total_pools = sum(r.get('total_pools', 0) for r in downloader_results)
        successful_downloads = sum(r.get('successful_downloads', 0) for r in downloader_results)
        failed_downloads = total_pools - successful_downloads
        total_records = sum(r.get('total_records', 0) for r in downloader_results)
        
        # Count successful vs failed downloaders
        successful_downloaders = sum(1 for r in downloader_results if r.get('successful_downloads', 0) > 0)
        failed_downloaders = len(downloader_results) - successful_downloaders
        
        # Create master report
        master_report = {
            'timestamp': master_end_time.isoformat(),
            'orchestrator': 'pool_data_orchestrator',
            'date_range': f"{start_date} to {end_date or 'present'}",
            'total_duration_seconds': total_duration,
            'start_time': master_start_time.isoformat(),
            'end_time': master_end_time.isoformat(),
            
            # Downloader-level stats
            'total_downloaders': len(self.downloaders),
            'successful_downloaders': successful_downloaders,
            'failed_downloaders': failed_downloaders,
            'skipped_downloaders': len(self.failed_initializations),
            
            # Pool-level stats  
            'total_pools': total_pools,
            'successful_downloads': successful_downloads,
            'failed_downloads': failed_downloads,
            'total_records': total_records,
            
            # Pool creation date enforcement
            'enforced_dates': actual_dates,
            
            # Individual results
            'downloader_results': downloader_results,
            'failed_initializations': self.failed_initializations
        }
        
        # Save master report
        report_file = self.save_report(
            master_report, 
            f"pool_data_orchestrator_report_{start_date}_{end_date or datetime.now().strftime('%Y-%m-%d')}.json"
        )
        
        # Print comprehensive summary
        self.logger.info("=" * 80)
        self.logger.info("🎯 POOL DATA ORCHESTRATOR COMPLETE!")
        self.logger.info("=" * 80)
        self.logger.info(f"⏱️  Total duration: {total_duration/60:.1f} minutes")
        self.logger.info("")
        self.logger.info("📊 DOWNLOADER SUMMARY:")
        self.logger.info(f"   ✅ Successful downloaders: {successful_downloaders}/{len(self.downloaders)}")
        self.logger.info(f"   ❌ Failed downloaders: {failed_downloaders}")
        if self.failed_initializations:
            self.logger.info(f"   ⚠️  Skipped (init failed): {len(self.failed_initializations)}")
        self.logger.info("")
        self.logger.info("📈 POOL DATA SUMMARY:")
        self.logger.info(f"   📥 Total pools: {total_pools}")
        self.logger.info(f"   ✅ Successful: {successful_downloads}")
        self.logger.info(f"   ❌ Failed: {failed_downloads}")
        self.logger.info(f"   📊 Total records: {total_records:,}")
        self.logger.info("")
        
        # Individual downloader summary
        for result in downloader_results:
            name = result['downloader_name']
            duration = result['duration_seconds']
            records = result.get('total_records', 0)
            successful = result.get('successful_downloads', 0)
            total = result.get('total_pools', 0)
            
            if successful > 0:
                status = "✅ SUCCESS"
            else:
                status = "❌ FAILED"
            
            self.logger.info(f"   {status} {name}: {successful}/{total} pools, {records:,} records ({duration:.1f}s)")
        
        self.logger.info("")
        self.logger.info(f"💾 Master report: {report_file}")
        self.logger.info(f"📁 Output directory: {self.output_dir}")
        self.logger.info("=" * 80)
        
        return master_report


async def main():
    """
    Main execution function for standalone script usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestrate all CoinGecko pool data downloads")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=str, default="data/market_data", help="Output directory")
    parser.add_argument("--quick-test", action="store_true", help="Run with last 7 days for testing")
    
    args = parser.parse_args()
    
    try:
        orchestrator = PoolDataOrchestrator(args.output_dir)
        
        # Use provided dates, config defaults, or quick test
        if args.quick_test:
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            print(f"🚀 Quick test mode: {start_date} to {end_date}")
        elif args.start_date and args.end_date:
            start_date, end_date = args.start_date, args.end_date
        elif args.start_date:
            start_date, end_date = args.start_date, None
        else:
            start_date, end_date = orchestrator.get_date_range()
            print(f"Using config defaults: {start_date} to {end_date}")
        
        # Run orchestrated download
        print(f"\n🎯 Starting CoinGecko pool data orchestration...")
        print(f"📅 Date range: {start_date} to {end_date or 'present'}")
        print(f"📁 Output directory: {args.output_dir}")
        print(f"🔧 Pool creation dates will be enforced")
        print()
        
        result = await orchestrator.download_data(start_date, end_date)
        
        # Print final summary
        successful_downloaders = result['successful_downloaders']
        total_downloaders = result['total_downloaders']
        total_records = result['total_records']
        duration_minutes = result['total_duration_seconds'] / 60
        
        if successful_downloaders > 0:
            print(f"\n🎉 POOL DATA ORCHESTRATION COMPLETE!")
            print(f"✅ Successful downloaders: {successful_downloaders}/{total_downloaders}")
            print(f"📊 Total records collected: {total_records:,}")
            print(f"⏱️  Total time: {duration_minutes:.1f} minutes")
            print(f"📁 All data saved to: {args.output_dir}/")
            
            # Show enforced dates
            enforced_dates = result.get('enforced_dates', {})
            if enforced_dates:
                print(f"\n📅 Pool creation dates enforced:")
                for pool_type, date in enforced_dates.items():
                    print(f"   {pool_type}: {date}")
        else:
            print(f"\n❌ POOL DATA ORCHESTRATION FAILED!")
            print(f"No downloaders completed successfully")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n💥 POOL DATA ORCHESTRATION ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
