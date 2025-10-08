"""
Master Data Downloader - Orchestrates all data collection.

Runs all downloaders in sequence:
1. Market Data (CoinGecko Pro + Bybit)
2. AAVE Data (AaveScan Pro) - Placeholder until API key available
3. On-Chain Data (Gas prices + LST rates)

Provides comprehensive data collection for 2024-2025 backtesting.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add the backend source to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "backend" / "src"))

# Handle both standalone and module imports
try:
    from .fetch_market_data import MarketDataDownloader
    from ..downloaders.fetch_aave_data import AAVEDataDownloader
    from ..downloaders.fetch_onchain_gas_data import OnChainGasDataDownloader
    from ..downloaders.base_downloader import BaseDownloader, ProgressTracker
except ImportError:
    # Standalone execution
    sys.path.append(str(Path(__file__).parent))
    sys.path.append(str(Path(__file__).parent.parent))
    from fetch_market_data import MarketDataDownloader
    from downloaders.fetch_aave_data import AAVEDataDownloader
    from downloaders.fetch_onchain_gas_data import OnChainGasDataDownloader
    from downloaders.base_downloader import BaseDownloader, ProgressTracker


class MasterDataDownloader(BaseDownloader):
    """
    Master orchestrator for all data downloads.
    
    Coordinates:
    - Market data (spot + futures)
    - AAVE protocol data (placeholder until API key)
    - On-chain data (gas + LST rates)
    """
    
    def __init__(self, output_dir: str = "data"):
        super().__init__("master_downloader", output_dir)
        
        self.downloaders = {}
        self.failed_initializations = []
        
        # Initialize all downloaders
        try:
            self.downloaders['market'] = MarketDataDownloader(output_dir)
            self.logger.info("✅ Market data downloader initialized")
        except Exception as e:
            self.logger.error(f"❌ Market data downloader failed: {e}")
            self.failed_initializations.append(('market', str(e)))
        
        try:
            self.downloaders['aave'] = AAVEDataDownloader(f"{output_dir}/protocol_data/aave")
            self.logger.info("✅ AAVE data downloader initialized")
        except Exception as e:
            self.logger.error(f"❌ AAVE data downloader failed: {e}")
            self.failed_initializations.append(('aave', str(e)))
        
        try:
            self.downloaders['gas'] = OnChainGasDataDownloader(output_dir)
            self.logger.info("✅ Gas data downloader initialized")
        except Exception as e:
            self.logger.error(f"❌ Gas data downloader failed: {e}")
            self.failed_initializations.append(('gas', str(e)))
        
        if not self.downloaders:
            raise RuntimeError("No downloaders could be initialized")
        
        self.logger.info(f"Master downloader initialized with {len(self.downloaders)} active downloaders")
        
        if self.failed_initializations:
            self.logger.warning(f"Failed to initialize {len(self.failed_initializations)} downloaders:")
            for name, error in self.failed_initializations:
                self.logger.warning(f"  - {name}: {error}")
    
    async def run_downloader(self, name: str, downloader: BaseDownloader, 
                           start_date: str, end_date: str) -> Dict:
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
        self.logger.info(f"🚀 Starting {name} downloader...")
        start_time = datetime.now()
        
        try:
            result = await downloader.download_data(start_date, end_date)
            
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
            
            if result.get('placeholder_mode'):
                self.logger.warning(f"🔄 {name}: PLACEHOLDER mode - {successful}/{total} files, {records} records ({duration:.1f}s)")
            else:
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
    
    async def download_data(self, start_date: str, end_date: str) -> Dict:
        """
        Run all data downloaders in sequence.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Master download results
        """
        self.logger.info("=" * 80)
        self.logger.info("🚀 MASTER DATA DOWNLOAD STARTED")
        self.logger.info("=" * 80)
        self.logger.info(f"📅 Date range: {start_date} to {end_date}")
        self.logger.info(f"🔧 Active downloaders: {', '.join(self.downloaders.keys())}")
        
        if self.failed_initializations:
            self.logger.warning(f"⚠️  Skipped downloaders: {', '.join(name for name, _ in self.failed_initializations)}")
        
        self.logger.info("=" * 80)
        
        master_start_time = datetime.now()
        downloader_results = []
        
        # Run downloaders in sequence (to avoid overwhelming APIs)
        for name, downloader in self.downloaders.items():
            result = await self.run_downloader(name, downloader, start_date, end_date)
            downloader_results.append(result)
            
            # Small delay between downloaders
            await asyncio.sleep(2)
        
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
            'downloader': 'master_data_downloader',
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
            f"MASTER_download_report_{start_date}_{end_date}.json"
        )
        
        # Print comprehensive summary
        self.logger.info("=" * 80)
        self.logger.info("🎯 MASTER DATA DOWNLOAD COMPLETE!")
        self.logger.info("=" * 80)
        self.logger.info(f"⏱️  Total duration: {total_duration/60:.1f} minutes")
        self.logger.info("")
        self.logger.info("📊 DOWNLOADER SUMMARY:")
        self.logger.info(f"   ✅ Successful downloaders: {successful_downloaders}/{len(self.downloaders)}")
        self.logger.info(f"   ❌ Failed downloaders: {failed_downloaders}")
        if self.failed_initializations:
            self.logger.info(f"   ⚠️  Skipped (init failed): {len(self.failed_initializations)}")
        self.logger.info("")
        self.logger.info("📈 DATA SUMMARY:")
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
            
            if result.get('placeholder_mode'):
                status = "🔄 PLACEHOLDER"
            elif successful > 0:
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
    
    parser = argparse.ArgumentParser(description="Run all data downloaders for comprehensive data collection")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory")
    parser.add_argument("--quick-test", action="store_true", help="Run with last 7 days for testing")
    
    args = parser.parse_args()
    
    try:
        downloader = MasterDataDownloader(args.output_dir)
        
        # Use provided dates, config defaults, or quick test
        if args.quick_test:
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            print(f"🚀 Quick test mode: {start_date} to {end_date}")
        elif args.start_date and args.end_date:
            start_date, end_date = args.start_date, args.end_date
        else:
            start_date, end_date = downloader.get_date_range()
            print(f"Using config defaults: {start_date} to {end_date}")
        
        # Run master download
        print(f"\n🎯 Starting comprehensive data download...")
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"📁 Output directory: {args.output_dir}")
        print()
        
        result = await downloader.download_data(start_date, end_date)
        
        # Print final summary
        successful_downloaders = result['successful_downloaders']
        total_downloaders = result['total_downloaders']
        total_records = result['total_records']
        duration_minutes = result['total_duration_seconds'] / 60
        
        if successful_downloaders > 0:
            print(f"\n🎉 MASTER DOWNLOAD COMPLETE!")
            print(f"✅ Successful downloaders: {successful_downloaders}/{total_downloaders}")
            print(f"📊 Total records collected: {total_records:,}")
            print(f"⏱️  Total time: {duration_minutes:.1f} minutes")
            print(f"📁 All data saved to: {args.output_dir}/")
        else:
            print(f"\n❌ MASTER DOWNLOAD FAILED!")
            print(f"No downloaders completed successfully")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n💥 MASTER DOWNLOAD ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
