"""
CEX Data Orchestrator - Centralized Exchange Data Collection

Orchestrates all CEX data downloads:
1. Protocol Tokens (EIGEN/ETHFI from Binance)
2. Spot Data (ETH/USDT from 4 exchanges)
3. Futures Data (ETH-USDT perp from 3 exchanges)
4. Funding Rates (multi-venue)

Features:
- Coordinated CEX data collection
- Exchange-specific date enforcement
- Parallel execution for efficiency
- Comprehensive reporting
- Risk management history (Binance back to 2020)
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

# Add the backend source to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "backend" / "src"))

# Handle both standalone and module imports
try:
    from ..downloaders.fetch_cex_protocol_tokens import CEXProtocolTokenDownloader
    from ..downloaders.fetch_cex_spot_data import CEXSpotDataDownloader
    from ..downloaders.fetch_cex_futures_data import CEXFuturesDataDownloader
    from ..downloaders.fetch_cex_funding_rates import CEXFundingRatesDownloader
    from ..downloaders.fetch_okx_funding_rates import OKXFundingRatesDownloader
    from ..downloaders.base_downloader import BaseDownloader
except ImportError:
    # Standalone execution
    sys.path.append(str(Path(__file__).parent.parent))
    from downloaders.fetch_cex_protocol_tokens import CEXProtocolTokenDownloader
    from downloaders.fetch_cex_spot_data import CEXSpotDataDownloader
    from downloaders.fetch_cex_futures_data import CEXFuturesDataDownloader
    from downloaders.fetch_cex_funding_rates import CEXFundingRatesDownloader
    from downloaders.fetch_okx_funding_rates import OKXFundingRatesDownloader
    from downloaders.base_downloader import BaseDownloader


class CEXDataOrchestrator(BaseDownloader):
    """
    Orchestrates all CEX data downloads.
    
    Coordinates:
    - Protocol token data (EIGEN/ETHFI from Binance)
    - Spot data (ETH/USDT from 4 exchanges)
    - Futures data (ETH-USDT perp from 3 exchanges)
    - Funding rates (ETH-USDT perp from 3 exchanges)
    - Enforces exchange-specific date limits
    """
    
    def __init__(self, output_dir: str = "data/market_data", asset: str = "ETH"):
        super().__init__("cex_data_orchestrator", output_dir)
        self.asset = asset.upper()  # ETH or BTC
        
        self.downloaders = {}
        self.failed_initializations = []
        
        # Initialize protocol token downloader
        try:
            self.downloaders['protocol_tokens'] = CEXProtocolTokenDownloader(f"{output_dir}/spot_prices/protocol_tokens")
            self.logger.info("✅ Protocol token downloader initialized")
        except Exception as e:
            self.logger.error(f"❌ Protocol token downloader failed: {e}")
            self.failed_initializations.append(('protocol_tokens', str(e)))
        
        # Initialize spot data downloader
        try:
            asset_dir = "btc_usd" if self.asset == "BTC" else "eth_usd"
            self.downloaders['spot_data'] = CEXSpotDataDownloader(f"{output_dir}/spot_prices/{asset_dir}", self.asset)
            self.logger.info("✅ Spot data downloader initialized")
        except Exception as e:
            self.logger.error(f"❌ Spot data downloader failed: {e}")
            self.failed_initializations.append(('spot_data', str(e)))
        
        # Initialize futures data downloader
        try:
            self.downloaders['futures_data'] = CEXFuturesDataDownloader(f"{output_dir}/derivatives/futures_ohlcv", "1h", self.asset)
            self.logger.info("✅ Futures data downloader initialized")
        except Exception as e:
            self.logger.error(f"❌ Futures data downloader failed: {e}")
            self.failed_initializations.append(('futures_data', str(e)))
        
        # Initialize funding rates downloader (Binance/Bybit API)
        try:
            self.downloaders['funding_rates'] = CEXFundingRatesDownloader(f"{output_dir}/derivatives/funding_rates", self.asset)
            self.logger.info("✅ Funding rates downloader (API) initialized")
        except Exception as e:
            self.logger.error(f"❌ Funding rates downloader (API) failed: {e}")
            self.failed_initializations.append(('funding_rates', str(e)))
        
        # Initialize OKX funding rates downloader (zip processing)
        try:
            self.downloaders['okx_funding_rates'] = OKXFundingRatesDownloader(f"{output_dir}/derivatives/funding_rates")
            self.logger.info("✅ OKX funding rates downloader (zip processing) initialized")
        except Exception as e:
            self.logger.error(f"❌ OKX funding rates downloader (zip processing) failed: {e}")
            self.failed_initializations.append(('okx_funding_rates', str(e)))
        
        if not self.downloaders:
            raise RuntimeError("No CEX downloaders could be initialized")
        
        self.logger.info(f"CEX data orchestrator initialized with {len(self.downloaders)} active downloaders")
        
        if self.failed_initializations:
            self.logger.warning(f"Failed to initialize {len(self.failed_initializations)} downloaders:")
            for name, error in self.failed_initializations:
                self.logger.warning(f"  - {name}: {error}")
    
    async def run_downloader(self, name: str, downloader, start_date: str, end_date: str, **kwargs) -> Dict:
        """
        Run a single downloader with error handling.
        
        Args:
            name: Downloader name
            downloader: Downloader instance
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            **kwargs: Additional arguments for specific downloaders
            
        Returns:
            Download result with metadata
        """
        self.logger.info(f"🚀 Starting {name} downloader...")
        start_time = datetime.now()
        
        try:
            result = await downloader.download_data(start_date, end_date, **kwargs)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Add metadata
            result['downloader_name'] = name
            result['duration_seconds'] = duration
            result['start_time'] = start_time.isoformat()
            result['end_time'] = end_time.isoformat()
            
            successful = result.get('successful_downloads', 0)
            total = result.get('total_downloads', 0)
            records = result.get('total_records', 0)
            
            self.logger.info(f"✅ {name}: {successful}/{total} downloads, {records:,} records ({duration:.1f}s)")
            
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
                'total_downloads': 0,
                'successful_downloads': 0,
                'total_records': 0
            }
    
    async def download_data(self, start_date: str, end_date: str, components: List[str] = None, exchanges: List[str] = None) -> Dict:
        """
        Run all CEX data downloaders.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            components: List of components to download (None for all)
            exchanges: List of exchanges to use (None for all)
            
        Returns:
            Master download results
        """
        self.logger.info("=" * 80)
        self.logger.info("🚀 CEX DATA ORCHESTRATOR STARTED")
        self.logger.info("=" * 80)
        self.logger.info(f"📅 Date range: {start_date} to {end_date}")
        self.logger.info(f"🔧 Active downloaders: {', '.join(self.downloaders.keys())}")
        
        if self.failed_initializations:
            self.logger.warning(f"⚠️  Skipped downloaders: {', '.join(name for name, _ in self.failed_initializations)}")
        
        self.logger.info("=" * 80)
        
        master_start_time = datetime.now()
        downloader_results = []
        
        # Determine which components to run
        if components is None:
            components = list(self.downloaders.keys())
        
        # Run each downloader
        for component in components:
            if component in self.downloaders:
                # Pass exchanges parameter to downloaders that support it
                kwargs = {}
                if exchanges is not None:
                    kwargs['exchanges'] = exchanges
                
                # Special handling for OKX funding rates
                if component == 'okx_funding_rates':
                    # OKX funding rates uses zip processing, not API
                    # Filter exchanges to only include OKX if specified
                    if exchanges is not None and 'okx' not in exchanges:
                        self.logger.info(f"⏭️  Skipping OKX funding rates (OKX not in exchanges list)")
                        continue
                    # OKX funding rates doesn't use exchanges parameter
                    kwargs = {}
                
                result = await self.run_downloader(component, self.downloaders[component], start_date, end_date, **kwargs)
                downloader_results.append(result)
        
        master_end_time = datetime.now()
        total_duration = (master_end_time - master_start_time).total_seconds()
        
        # Aggregate results
        total_downloads = sum(r.get('total_downloads', 0) for r in downloader_results)
        successful_downloads = sum(r.get('successful_downloads', 0) for r in downloader_results)
        failed_downloads = total_downloads - successful_downloads
        total_records = sum(r.get('total_records', 0) for r in downloader_results)
        
        # Count successful vs failed downloaders
        successful_downloaders = sum(1 for r in downloader_results if r.get('successful_downloads', 0) > 0)
        failed_downloaders = len(downloader_results) - successful_downloaders
        
        # Create master report
        master_report = {
            'timestamp': master_end_time.isoformat(),
            'orchestrator': 'cex_data_orchestrator',
            'date_range': f"{start_date} to {end_date}",
            'total_duration_seconds': total_duration,
            'start_time': master_start_time.isoformat(),
            'end_time': master_end_time.isoformat(),
            
            # Downloader-level stats
            'total_downloaders': len(self.downloaders),
            'successful_downloaders': successful_downloaders,
            'failed_downloaders': failed_downloaders,
            'skipped_downloaders': len(self.failed_initializations),
            
            # Download-level stats  
            'total_downloads': total_downloads,
            'successful_downloads': successful_downloads,
            'failed_downloads': failed_downloads,
            'total_records': total_records,
            
            # Individual results
            'downloader_results': downloader_results,
            'failed_initializations': self.failed_initializations
        }
        
        # Save master report
        report_file = self.save_report(
            master_report, 
            f"cex_data_orchestrator_report_{start_date}_{end_date}.json"
        )
        
        # Print comprehensive summary
        self.logger.info("=" * 80)
        self.logger.info("🎯 CEX DATA ORCHESTRATOR COMPLETE!")
        self.logger.info("=" * 80)
        self.logger.info(f"⏱️  Total duration: {total_duration/60:.1f} minutes")
        self.logger.info("")
        self.logger.info("📊 DOWNLOADER SUMMARY:")
        self.logger.info(f"   ✅ Successful downloaders: {successful_downloaders}/{len(self.downloaders)}")
        self.logger.info(f"   ❌ Failed downloaders: {failed_downloaders}")
        if self.failed_initializations:
            self.logger.info(f"   ⚠️  Skipped (init failed): {len(self.failed_initializations)}")
        self.logger.info("")
        self.logger.info("📈 CEX DATA SUMMARY:")
        self.logger.info(f"   📥 Total downloads: {total_downloads}")
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
            total = result.get('total_downloads', 0)
            
            if successful > 0:
                status = "✅ SUCCESS"
            else:
                status = "❌ FAILED"
            
            self.logger.info(f"   {status} {name}: {successful}/{total} downloads, {records:,} records ({duration:.1f}s)")
        
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
    
    parser = argparse.ArgumentParser(description="Orchestrate all CEX data downloads")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=str, default="data/market_data", help="Output directory")
    parser.add_argument("--component", type=str, choices=["protocol_tokens", "spot_data", "futures_data", "funding_rates", "okx_funding_rates"], help="Specific component to download")
    parser.add_argument("--exchanges", type=str, help="Comma-separated list of exchanges (e.g., 'binance,bybit')")
    parser.add_argument("--asset", type=str, default="ETH", choices=["ETH", "BTC"], help="Asset to download (ETH or BTC)")
    parser.add_argument("--quick-test", action="store_true", help="Run with last 3 days for testing")
    
    args = parser.parse_args()
    
    try:
        orchestrator = CEXDataOrchestrator(args.output_dir, args.asset)
        
        # Use provided dates, current date defaults, or quick test
        from datetime import datetime, timedelta
        if args.quick_test:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
            print(f"🚀 Quick test mode: {start_date} to {end_date}")
        elif args.start_date and args.end_date:
            start_date, end_date = args.start_date, args.end_date
        elif args.start_date:
            # Only start date provided, use current date as end date
            start_date = args.start_date
            end_date = datetime.now().strftime('%Y-%m-%d')
            print(f"Using provided start date with current end date: {start_date} to {end_date}")
        else:
            # No dates provided, use last 30 days
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            print(f"Using default date range (last 30 days): {start_date} to {end_date}")
        
        # Determine components to run
        components = [args.component] if args.component else None
        
        # Parse exchanges argument
        exchanges = None
        if args.exchanges:
            raw_exchanges = [ex.strip() for ex in args.exchanges.split(',')]
            # Map user-friendly exchange names to internal names
            exchange_mapping = {
                'binance': ['binance_spot', 'binance_futures'],
                'bybit': ['bybit'],
                'okx': ['okx']
            }
            
            exchanges = []
            for ex in raw_exchanges:
                if ex in exchange_mapping:
                    exchanges.extend(exchange_mapping[ex])
                else:
                    exchanges.append(ex)  # Use as-is if not in mapping
            
            print(f"🔧 Exchange filter: {', '.join(raw_exchanges)} -> {', '.join(exchanges)}")
        
        # Run orchestrated download
        print(f"\n🎯 Starting {args.asset} CEX data orchestration...")
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"📁 Output directory: {args.output_dir}")
        print(f"🔧 Exchange-specific date enforcement:")
        print(f"   Protocol tokens: EIGEN (2024-10-05), ETHFI (2024-06-01)")
        print(f"   Spot data: Binance (2020-01-01), Others (2024-01-01)")
        print(f"   Futures: All exchanges (2024-01-01)")
        print()
        
        result = await orchestrator.download_data(start_date, end_date, components, exchanges)
        
        # Print final summary
        successful_downloaders = result['successful_downloaders']
        total_downloaders = result['total_downloaders']
        total_records = result['total_records']
        duration_minutes = result['total_duration_seconds'] / 60
        
        if successful_downloaders > 0:
            print(f"\n🎉 CEX DATA ORCHESTRATION COMPLETE!")
            print(f"✅ Successful downloaders: {successful_downloaders}/{total_downloaders}")
            print(f"📊 Total records collected: {total_records:,}")
            print(f"⏱️  Total time: {duration_minutes:.1f} minutes")
            print(f"📁 All data saved to: {args.output_dir}/")
        else:
            print(f"\n❌ CEX DATA ORCHESTRATION FAILED!")
            print(f"No downloaders completed successfully")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n💥 CEX DATA ORCHESTRATION ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
