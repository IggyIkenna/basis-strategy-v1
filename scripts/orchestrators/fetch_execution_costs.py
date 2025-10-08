#!/usr/bin/env python3
"""
Execution Cost Orchestrator

Orchestrates the generation of comprehensive execution cost data by combining:
1. Gas costs from enhanced gas price data
2. Trading pair execution costs (slippage + exchange fees)
3. Venue-specific cost modeling

This provides complete transaction cost modeling for all DeFi operations.
"""

import asyncio
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
import time

# Add the backend source to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "backend" / "src"))

try:
    from ..downloaders.fetch_execution_cost_data import SimpleExecutionCostGenerator
    from ..downloaders.base_downloader import BaseDownloader
except ImportError:
    # Standalone execution
    sys.path.append(str(Path(__file__).parent))
    sys.path.append(str(Path(__file__).parent.parent / "downloaders"))
    from fetch_execution_cost_data import SimpleExecutionCostGenerator
    from base_downloader import BaseDownloader


class ExecutionCostOrchestrator(BaseDownloader):
    """
    Orchestrates the generation of comprehensive execution cost data.
    """

    def __init__(self, output_dir: str = "data/execution_costs"):
        super().__init__("execution_cost_orchestrator", output_dir)
        
        self.downloaders = {}
        self.failed_initializations = []
        
        # Initialize execution cost generator
        try:
            self.downloaders['execution_costs'] = SimpleExecutionCostGenerator(output_dir)
            self.logger.info("✅ Execution cost generator initialized")
        except Exception as e:
            self.logger.error(f"❌ Execution cost generator failed: {e}")
            self.failed_initializations.append(('execution_costs', str(e)))
        
        if not self.downloaders:
            raise RuntimeError("No execution cost downloaders could be initialized")
        
        self.logger.info(f"Execution cost orchestrator initialized with {len(self.downloaders)} active downloaders")

    async def run_downloader(self, downloader_name: str, downloader, start_date: str, end_date: str):
        """Helper to run a single downloader and capture its result."""
        start_time = time.time()
        
        try:
            self.logger.info(f"🚀 Starting {downloader_name}...")
            
            # Run the execution cost generation
            await downloader.generate_execution_costs(start_date, end_date)
            
            duration = time.time() - start_time
            
            # Count generated files
            output_dir = Path(self.output_dir)
            csv_files = list(output_dir.glob("*.csv"))
            json_files = list(output_dir.glob("*.json"))
            lookup_files = list((output_dir / "lookup_tables").glob("*.json"))
            
            total_files = len(csv_files) + len(json_files) + len(lookup_files)
            
            self.logger.info(f"✅ {downloader_name}: Generated {total_files} files ({duration:.1f}s)")
            
            return {
                'name': downloader_name,
                'success': True,
                'duration': duration,
                'result': {
                    'csv_files': len(csv_files),
                    'json_files': len(json_files),
                    'lookup_files': len(lookup_files),
                    'total_files': total_files
                }
            }
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"❌ {downloader_name} failed: {e} ({duration:.1f}s)")
            return {
                'name': downloader_name,
                'success': False,
                'duration': duration,
                'error': str(e)
            }

    async def download_data(self, start_date: str, end_date: str) -> dict:
        """
        Orchestrates the generation of execution cost data.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Orchestration results
        """
        self.logger.info("=" * 70)
        self.logger.info("🚀 EXECUTION COST ORCHESTRATOR STARTED")
        self.logger.info("=" * 70)
        self.logger.info(f"📅 Date range: {start_date} to {end_date}")
        self.logger.info(f"🔧 Active downloaders: {', '.join(self.downloaders.keys())}")
        self.logger.info("=" * 70)

        results = []
        total_files_generated = 0
        successful_downloaders_count = 0
        total_start_time = time.time()

        # Run each downloader
        for name, downloader in self.downloaders.items():
            result = await self.run_downloader(name, downloader, start_date, end_date)
            results.append(result)
            if result['success']:
                successful_downloaders_count += 1
                if result['result'] and 'total_files' in result['result']:
                    total_files_generated += result['result']['total_files']

        total_duration = (time.time() - total_start_time) / 60  # in minutes

        # Create a summary report
        report = {
            'timestamp': datetime.now().isoformat(),
            'orchestrator': 'execution_cost_orchestrator',
            'date_range': f"{start_date} to {end_date}",
            'total_downloads': len(self.downloaders),
            'successful_downloads': successful_downloaders_count,
            'failed_downloads': len(self.downloaders) - successful_downloaders_count,
            'total_files_generated': total_files_generated,
            'total_duration_minutes': round(total_duration, 1),
            'downloader_results': results
        }

        report_file = self.save_report(report, f"execution_cost_orchestrator_report_{start_date}_{end_date}.json")

        self.logger.info("=" * 70)
        self.logger.info("🎯 EXECUTION COST ORCHESTRATOR COMPLETE!")
        self.logger.info("=" * 70)
        self.logger.info(f"⏱️  Total duration: {total_duration:.1f} minutes")
        self.logger.info("")
        self.logger.info("📊 DOWNLOADER SUMMARY:")
        self.logger.info(f"   ✅ Successful downloaders: {successful_downloaders_count}/{len(self.downloaders)}")
        self.logger.info(f"   ❌ Failed downloaders: {len(self.downloaders) - successful_downloaders_count}")
        self.logger.info("")
        self.logger.info("📈 EXECUTION COST SUMMARY:")
        self.logger.info(f"   📥 Total downloads: {report['total_downloads']}")
        self.logger.info(f"   ✅ Successful: {report['successful_downloads']}")
        self.logger.info(f"   ❌ Failed: {report['failed_downloads']}")
        self.logger.info(f"   📊 Total files generated: {report['total_files_generated']}")
        self.logger.info("")
        for res in results:
            status = "✅ SUCCESS" if res['success'] else "❌ FAILED"
            files = res['result'].get('total_files', 0) if res['success'] and isinstance(res['result'], dict) else 0
            self.logger.info(f"   {status} {res['name']}: {files} files ({res['duration']:.1f}s)")
        self.logger.info("")
        self.logger.info(f"💾 Master report: {report_file}")
        self.logger.info(f"📁 Output directory: {self.output_dir}")
        self.logger.info("=" * 70)

        return report


async def main():
    parser = argparse.ArgumentParser(description="Orchestrate execution cost data generation.")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD).")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD).")
    parser.add_argument("--output-dir", type=str, default="data/execution_costs", help="Output directory.")
    parser.add_argument("--quick-test", action="store_true", help="Run a quick test for the last 3 days.")

    args = parser.parse_args()

    print("\n🎯 Starting execution cost orchestration...")

    # Use provided dates, current date defaults, or quick test
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

    print(f"📅 Date range: {start_date} to {end_date}")
    print(f"📁 Output directory: {args.output_dir}\n")

    orchestrator = ExecutionCostOrchestrator(args.output_dir)
    report = await orchestrator.download_data(start_date, end_date)

    if report['successful_downloads'] > 0:
        print("\n🎉 EXECUTION COST ORCHESTRATION COMPLETE!")
        print(f"✅ Successful downloaders: {report['successful_downloads']}/{report['total_downloads']}")
        print(f"📊 Total files generated: {report['total_files_generated']}")
        print(f"⏱️  Total time: {report['total_duration_minutes']:.1f} minutes")
        print(f"📁 All data saved to: {args.output_dir}/")
        return 0
    else:
        print("\n❌ EXECUTION COST ORCHESTRATION FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
