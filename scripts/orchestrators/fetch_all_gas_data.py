"""
Gas Data Orchestrator - Coordinates all gas-related data downloads.

Orchestrates:
- On-chain gas price data (Alchemy JSON-RPC)
- Gas cost analysis and processing
- Follows same pattern as other orchestrators with load_env.sh
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add the backend source to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "backend" / "src"))

# Handle both standalone and module imports
try:
    from ..downloaders.fetch_onchain_gas_data import OnChainGasDataDownloader
    from ..downloaders.base_downloader import BaseDownloader
    from ..analyzers.analyze_gas_costs import run_gas_cost_analysis
except ImportError:
    # Standalone execution
    sys.path.append(str(Path(__file__).parent.parent))
    from downloaders.fetch_onchain_gas_data import OnChainGasDataDownloader
    from downloaders.base_downloader import BaseDownloader
    from analyzers.analyze_gas_costs import run_gas_cost_analysis


class GasDataOrchestrator(BaseDownloader):
    """
    Orchestrates all gas-related data downloads.
    
    Coordinates:
    - On-chain gas price data (Alchemy JSON-RPC)
    - Gas cost analysis and processing
    - Follows same pattern as other orchestrators
    """
    
    def __init__(self, output_dir: str = "data/blockchain_data"):
        super().__init__("gas_data_orchestrator", output_dir)
        
        self.downloaders = {}
        self.failed_initializations = []
        
        # Initialize gas data downloader
        try:
            self.downloaders['gas_data'] = OnChainGasDataDownloader(f"{output_dir}")
            self.logger.info("✅ Gas data downloader initialized")
        except Exception as e:
            self.logger.error(f"❌ Gas data downloader failed: {e}")
            self.failed_initializations.append(('gas_data', str(e)))
        
        if not self.downloaders:
            raise RuntimeError("No gas downloaders could be initialized")
        
        self.logger.info(f"Gas data orchestrator initialized with {len(self.downloaders)} active downloaders")
    
    async def run_downloader(self, name: str, downloader, start_date: str, end_date: str, **kwargs) -> Dict:
        """
        Run a single downloader and return results.
        
        Args:
            name: Downloader name
            downloader: Downloader instance
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            **kwargs: Additional arguments
            
        Returns:
            Download results
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"🚀 Starting {name} downloader...")
            result = await downloader.download_data(start_date, end_date)
            
            duration = (datetime.now() - start_time).total_seconds()
            successful = result.get('successful_downloads', 0)
            total = result.get('total_downloads', 0)
            records = result.get('total_records', 0)
            
            self.logger.info(f"✅ {name}: {successful}/{total} downloads, {records} records ({duration:.1f}s)")
            
            return {
                'name': name,
                'success': True,
                'duration': duration,
                'result': result
            }
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"❌ {name} failed: {e}")
            
            return {
                'name': name,
                'success': False,
                'duration': duration,
                'error': str(e)
            }
    
    async def run_gas_cost_analysis(self, start_date: str, end_date: str) -> Optional[Dict]:
        """
        Run gas cost analysis on the downloaded gas data.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Analysis results or None if failed
        """
        start_time = datetime.now()
        
        try:
            self.logger.info("🔄 Starting gas cost analysis...")
            
            # Find the gas data file that was just downloaded
            gas_output_dir = f"{self.output_dir}/gas_prices"
            gas_files = list(Path(gas_output_dir).glob(f"ethereum_gas_prices_{start_date}_{end_date}.csv"))
            
            if not gas_files:
                self.logger.warning(f"No gas data file found for {start_date} to {end_date}")
                return None
            
            gas_file_path = str(gas_files[0])
            
            # Find ETH price data file
            eth_price_files = list(Path("data/market_data/spot_prices/eth_usd").glob("binance_ETHUSDT_1h_*.csv"))
            if not eth_price_files:
                self.logger.warning("No ETH price data file found")
                return None
            
            eth_price_file_path = str(eth_price_files[0])
            
            # Run the analysis
            enhanced_file, summary_file = run_gas_cost_analysis(
                gas_file_path, eth_price_file_path, gas_output_dir, start_date, end_date
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"✅ Gas cost analysis complete: {duration:.1f}s")
            self.logger.info(f"   📊 Enhanced gas prices: {enhanced_file}")
            self.logger.info(f"   📑 Summary report: {summary_file}")
            
            return {
                'name': 'gas_cost_analysis',
                'success': True,
                'duration': duration,
                'result': {
                    'enhanced_file': enhanced_file,
                    'summary_file': summary_file
                }
            }
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"❌ Gas cost analysis failed: {e}")
            
            return {
                'name': 'gas_cost_analysis',
                'success': False,
                'duration': duration,
                'error': str(e)
            }
    
    async def download_data(self, start_date: str, end_date: str) -> Dict:
        """
        Run all gas data downloaders.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Master download results
        """
        self.logger.info("=" * 80)
        self.logger.info("🚀 GAS DATA ORCHESTRATOR STARTED")
        self.logger.info("=" * 80)
        self.logger.info(f"📅 Date range: {start_date} to {end_date}")
        self.logger.info(f"🔧 Active downloaders: {', '.join(self.downloaders.keys())}")
        self.logger.info("=" * 80)
        
        downloader_results = []
        
        # Run each downloader
        for name, downloader in self.downloaders.items():
            result = await self.run_downloader(name, downloader, start_date, end_date)
            downloader_results.append(result)
        
        # Run gas cost analysis if gas data was successfully downloaded
        analysis_result = None
        if any(r['success'] for r in downloader_results):
            analysis_result = await self.run_gas_cost_analysis(start_date, end_date)
            if analysis_result:
                downloader_results.append(analysis_result)
        
        # Calculate totals
        total_downloads = sum(r['result'].get('total_downloads', 0) for r in downloader_results if r['success'])
        successful_downloads = sum(r['result'].get('successful_downloads', 0) for r in downloader_results if r['success'])
        total_records = sum(r['result'].get('total_records', 0) for r in downloader_results if r['success'])
        total_duration = sum(r['duration'] for r in downloader_results)
        
        # Create master report
        master_report = {
            'timestamp': datetime.now().isoformat(),
            'orchestrator': 'gas_data_orchestrator',
            'date_range': f"{start_date} to {end_date}",
            'total_downloads': total_downloads,
            'successful_downloads': successful_downloads,
            'failed_downloads': total_downloads - successful_downloads,
            'total_records': total_records,
            'total_duration_minutes': round(total_duration / 60, 1),
            'downloader_results': downloader_results
        }
        
        # Save master report
        report_file = self.save_report(
            master_report,
            f"gas_data_orchestrator_report_{start_date}_{end_date}.json"
        )
        
        # Log summary
        self.logger.info("=" * 80)
        self.logger.info("🎯 GAS DATA ORCHESTRATOR COMPLETE!")
        self.logger.info("=" * 80)
        self.logger.info(f"⏱️  Total duration: {master_report['total_duration_minutes']} minutes")
        self.logger.info("")
        self.logger.info("📊 DOWNLOADER SUMMARY:")
        self.logger.info(f"   ✅ Successful downloaders: {len([r for r in downloader_results if r['success']])}/{len(downloader_results)}")
        self.logger.info(f"   ❌ Failed downloaders: {len([r for r in downloader_results if not r['success']])}")
        self.logger.info("")
        self.logger.info("📈 GAS DATA SUMMARY:")
        self.logger.info(f"   📥 Total downloads: {total_downloads}")
        self.logger.info(f"   ✅ Successful: {successful_downloads}")
        self.logger.info(f"   ❌ Failed: {total_downloads - successful_downloads}")
        self.logger.info(f"   📊 Total records: {total_records:,}")
        self.logger.info("")
        
        for result in downloader_results:
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            name = result['name']
            if result['success']:
                downloads = result['result'].get('successful_downloads', 0)
                total = result['result'].get('total_downloads', 0)
                records = result['result'].get('total_records', 0)
                duration = result['duration']
                self.logger.info(f"   {status} {name}: {downloads}/{total} downloads, {records} records ({duration:.1f}s)")
            else:
                error = result.get('error', 'Unknown error')
                self.logger.info(f"   {status} {name}: {error}")
        
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
    
    parser = argparse.ArgumentParser(description="Orchestrate all gas data downloads")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=str, default="data/blockchain_data", help="Output directory")
    parser.add_argument("--quick-test", action="store_true", help="Run with last 3 days for testing")
    
    args = parser.parse_args()
    
    try:
        orchestrator = GasDataOrchestrator(args.output_dir)
        
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
        
        print(f"\n🎯 Starting gas data orchestration...")
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"📁 Output directory: {args.output_dir}")
        print()
        
        result = await orchestrator.download_data(start_date, end_date)
        
        # Print summary
        if result['successful_downloads'] > 0:
            print(f"\n🎉 GAS DATA ORCHESTRATION COMPLETE!")
            print(f"✅ Successful downloaders: {len([r for r in result['downloader_results'] if r['success']])}/{len(result['downloader_results'])}")
            print(f"📊 Total records collected: {result['total_records']:,}")
            print(f"⏱️  Total time: {result['total_duration_minutes']} minutes")
            print(f"📁 All data saved to: {args.output_dir}/")
        else:
            print(f"\n❌ FAILED! No gas data was downloaded successfully")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
