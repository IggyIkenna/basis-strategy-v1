"""
AAVE Data Orchestrator - Complete AAVE Data Pipeline

Orchestrates the complete AAVE data pipeline from raw data to final analysis:
1. Raw Data Download (daily granularity AAVE rates)
2. Data Processing (oracle prices + risk parameters + proper hourly interpolation)
3. Rate Model Calibration (validation against real AAVE data)
4. Rate Impact Analysis (market impact modeling for strategies)

🎯 COMPREHENSIVE AAVE DATA PIPELINE:

STAGE 1: RAW DATA DOWNLOAD
- Historical AAVE v3 lending/borrowing rates (daily granularity)
- Reserve data (total supply/borrows for market impact modeling)
- Oracle pricing data (exact prices used for liquidations)
- Focuses on key assets: WETH, wstETH, weETH, USDT

STAGE 2: DATA PROCESSING
- Oracle Price Processing: Extracts oracle prices from AAVE rates data
- Risk Parameters Creation: Generates AAVE risk parameters JSON
- Proper Hourly Interpolation: Mathematically correct interpolation with:
  * Index interpolation between 24-hour periods
  * Hourly APY calculation from index ratios
  * Continuously compounded APR conversion
  * Clean output with dropped unused columns

STAGE 3: RATE MODEL CALIBRATION
- Validates rate model accuracy against real AAVE data
- Tests all tokens (WETH, wstETH, weETH, USDT) for calibration accuracy
- Generates calibration reports with error metrics
- Creates calibration plots and summary files
- Ensures models are within acceptable error thresholds

STAGE 4: RATE IMPACT ANALYSIS
- Analyzes how strategy positions affect AAVE interest rates
- Uses corrected hourly interpolated rates (more accurate)
- Calibrated AAVE kinked interest rate models
- Dual-asset impact analysis (collateral supply + borrow rates)
- Comprehensive visualization and reporting

Features:
- Complete end-to-end AAVE data pipeline
- Mathematically correct hourly interpolation
- Component-based execution (download, process, calibrate, analyze)
- Comprehensive reporting and visualization
- Integration with existing backtest engine

🔑 API KEY SETUP REQUIRED:
This orchestrator requires an AaveScan Pro Advanced Plan API key.

1. Get an AaveScan Pro API key from: https://aavescan.com/
2. Add it to backend/env.unified:
   BASIS_DOWNLOADERS__AAVESCAN_API_KEY=your_api_key_here

3. Load environment variables before running:
   source scripts/load_env.sh
   python scripts/orchestrators/fetch_borrow_lending_data.py --start-date 2024-01-01

⚠️  WITHOUT API KEY: Falls back to placeholder mode (structure only)
✅  WITH API KEY: Full historical access with real AAVE data
"""

import asyncio
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add the backend source to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "backend" / "src"))

# Handle both standalone and module imports
try:
    from ..downloaders.fetch_aave_data import AAVEDataDownloader
    from ..downloaders.base_downloader import BaseDownloader
except ImportError:
    # Standalone execution
    sys.path.append(str(Path(__file__).parent.parent))
    from downloaders.fetch_aave_data import AAVEDataDownloader
    from downloaders.base_downloader import BaseDownloader


class AAVEDataOrchestrator(BaseDownloader):
    """
    Orchestrates the complete AAVE data pipeline.
    
    Coordinates:
    - AaveScan Pro data download (rates, reserves, risk parameters)
    - Oracle price processing (extract oracle prices from rates data)
    - Rate impact analysis (market impact modeling for strategies)
    - Component-based execution with optional stages
    """
    
    def __init__(self, output_dir: str = "data/protocol_data/aave"):
        super().__init__("aave_data_orchestrator", output_dir)
        
        self.downloaders = {}
        self.failed_initializations = []
        
        # Initialize AAVE data downloader
        try:
            self.downloaders['aave_data'] = AAVEDataDownloader(output_dir)
            self.logger.info("✅ AAVE data downloader initialized")
        except Exception as e:
            self.logger.error(f"❌ AAVE data downloader failed: {e}")
            self.failed_initializations.append(('aave_data', str(e)))
        
        if not self.downloaders:
            raise RuntimeError("No AAVE downloaders could be initialized")
        
        self.logger.info(f"AAVE data orchestrator initialized with {len(self.downloaders)} active downloaders")
        
        if self.failed_initializations:
            self.logger.warning(f"Failed to initialize {len(self.failed_initializations)} downloaders:")
            for name, error in self.failed_initializations:
                self.logger.warning(f"  - {name}: {error}")
    
    async def run_downloader(self, name: str, downloader, start_date: str, end_date: str, **kwargs) -> Dict:
        """
        Run a specific downloader with error handling and timing.
        
        Args:
            name: Downloader name for logging
            downloader: Downloader instance
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            **kwargs: Additional arguments for downloader
            
        Returns:
            Download result dictionary
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"🔄 Starting {name} downloader...")
            self.logger.info(f"📅 Date range: {start_date} to {end_date}")
            
            # Run the downloader
            result = await downloader.download_data(start_date, end_date)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Extract metrics from result
            total_downloads = result.get('total_downloads', 0)
            successful_downloads = result.get('successful_downloads', 0)
            total_records = result.get('total_records', 0)
            
            self.logger.info(f"✅ {name} completed in {duration:.1f}s")
            self.logger.info(f"📊 Downloads: {successful_downloads}/{total_downloads}")
            self.logger.info(f"📈 Records: {total_records:,}")
            
            return {
                'success': True,
                'downloader': name,
                'duration': duration,
                'result': result
            }
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"❌ {name} failed after {duration:.1f}s: {e}")
            
            return {
                'success': False,
                'downloader': name,
                'duration': duration,
                'error': str(e)
            }
    
    def run_processor(self, processor_script: str, args: List[str] = None) -> Dict:
        """
        Run a data processor script.
        
        Args:
            processor_script: Path to processor script
            args: Additional arguments for the script
            
        Returns:
            Processing result dictionary
        """
        start_time = datetime.now()
        
        try:
            # Build command
            cmd = [sys.executable, processor_script]
            if args:
                cmd.extend(args)
            
            self.logger.info(f"🔄 Running processor: {' '.join(cmd)}")
            
            # Run the processor
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent  # Run from project root
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if result.returncode == 0:
                self.logger.info(f"✅ Processor completed in {duration:.1f}s")
                return {
                    'success': True,
                    'processor': processor_script,
                    'duration': duration,
                    'output': result.stdout
                }
            else:
                self.logger.error(f"❌ Processor failed after {duration:.1f}s")
                self.logger.error(f"Error: {result.stderr}")
                return {
                    'success': False,
                    'processor': processor_script,
                    'duration': duration,
                    'error': result.stderr
                }
                
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"❌ Processor failed after {duration:.1f}s: {e}")
            return {
                'success': False,
                'processor': processor_script,
                'duration': duration,
                'error': str(e)
            }
    
    async def download_data(self, start_date: str, end_date: str, 
                          components: List[str] = None) -> Dict:
        """
        Run the complete AAVE data pipeline.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            components: List of components to run ['download', 'process', 'analyze']
                       Default: ['download', 'process', 'analyze']
            
        Returns:
            Master pipeline results
        """
        if components is None:
            components = ['download', 'process', 'analyze']
        
        self.logger.info("=" * 80)
        self.logger.info("🚀 AAVE DATA PIPELINE STARTED")
        self.logger.info("=" * 80)
        self.logger.info(f"📅 Date range: {start_date} to {end_date}")
        self.logger.info(f"🔧 Components: {', '.join(components)}")
        self.logger.info("=" * 80)
        
        pipeline_results = []
        
        # Stage 1: Data Download
        if 'download' in components:
            self.logger.info("📥 STAGE 1: AAVE Data Download")
            self.logger.info("-" * 50)
            
            downloader_results = []
            
            # Run each downloader
            for name, downloader in self.downloaders.items():
                result = await self.run_downloader(name, downloader, start_date, end_date)
                downloader_results.append(result)
                pipeline_results.append(result)
            
            # Calculate download totals
            total_downloads = sum(r['result'].get('total_downloads', 0) for r in downloader_results if r['success'])
            successful_downloads = sum(r['result'].get('successful_downloads', 0) for r in downloader_results if r['success'])
            total_records = sum(r['result'].get('total_records', 0) for r in downloader_results if r['success'])
            total_duration = sum(r['duration'] for r in downloader_results)
            
            self.logger.info("=" * 50)
            self.logger.info("📥 DOWNLOAD STAGE COMPLETE")
            self.logger.info("=" * 50)
            self.logger.info(f"✅ Successful downloads: {successful_downloads}/{total_downloads}")
            self.logger.info(f"📊 Total records: {total_records:,}")
            self.logger.info(f"⏱️ Total duration: {total_duration:.1f}s")
            self.logger.info("=" * 50)
        
        # Stage 2: Data Processing
        if 'process' in components:
            self.logger.info("🔄 STAGE 2: Data Processing")
            self.logger.info("-" * 50)
            
            processing_results = []
            
            # 2a: Oracle Price Processing
            self.logger.info("🔄 2a: Oracle Price Processing")
            processor_script = "scripts/processors/process_aave_oracle_prices.py"
            processor_args = ["--data-dir", "data"]
            
            result = self.run_processor(processor_script, processor_args)
            processing_results.append(result)
            pipeline_results.append(result)
            
            if result['success']:
                self.logger.info("✅ Oracle prices extracted and processed")
            else:
                self.logger.error("❌ Oracle processing failed")
            
            # 2b: Risk Parameters Creation
            self.logger.info("🔄 2b: Risk Parameters Creation")
            risk_params_script = "scripts/utilities/create_aave_risk_params.py"
            risk_params_args = []
            
            result = self.run_processor(risk_params_script, risk_params_args)
            processing_results.append(result)
            pipeline_results.append(result)
            
            if result['success']:
                self.logger.info("✅ AAVE risk parameters created")
            else:
                self.logger.error("❌ Risk parameters creation failed")
            
            # 2c: Proper Hourly Interpolation
            self.logger.info("🔄 2c: Proper Hourly Interpolation")
            interpolation_script = "scripts/utilities/proper_hourly_interpolation.py"
            interpolation_args = []
            
            result = self.run_processor(interpolation_script, interpolation_args)
            processing_results.append(result)
            pipeline_results.append(result)
            
            if result['success']:
                self.logger.info("✅ Proper hourly interpolation completed")
            else:
                self.logger.error("❌ Hourly interpolation failed")
            
            # Calculate processing totals
            successful_processors = sum(1 for r in processing_results if r['success'])
            total_processors = len(processing_results)
            total_duration = sum(r['duration'] for r in processing_results)
            
            self.logger.info("=" * 50)
            self.logger.info("🔄 PROCESSING STAGE COMPLETE")
            self.logger.info("=" * 50)
            self.logger.info(f"✅ Successful processors: {successful_processors}/{total_processors}")
            self.logger.info(f"⏱️ Total duration: {total_duration:.1f}s")
            self.logger.info("=" * 50)
        
        # Stage 3: Rate Model Calibration
        if 'calibrate' in components:
            self.logger.info("🔧 STAGE 3: Rate Model Calibration")
            self.logger.info("-" * 50)
            
            # Run calibration validation using the analyzer
            try:
                # Add the scripts directory to path for imports
                import sys
                from pathlib import Path
                scripts_path = Path(__file__).parent.parent
                if str(scripts_path) not in sys.path:
                    sys.path.append(str(scripts_path))
                
                from analyzers.analyze_aave_rate_impact import AAVERateImpactAnalyzer
                analyzer = AAVERateImpactAnalyzer()
                
                # Enable calibration validation (skip validation is disabled by default)
                analyzer.SKIP_VALIDATION = False
                
                # Run calibration validation
                analyzer._validate_rate_model_calibration()
                
                # Create calibration summary
                calibration_summary = analyzer.create_calibration_summary()
                
                # Save calibration summary
                import json
                summary_file = self.output_dir / f"aave_calibration_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
                summary_file.parent.mkdir(parents=True, exist_ok=True)
                with open(summary_file, 'w') as f:
                    json.dump(calibration_summary, f, indent=2, default=str)
                
                # Create calibration plots for all assets
                calibration_plots = []
                historical_data = analyzer.load_aave_historical_data()
                
                for asset in ['WETH', 'wstETH', 'weETH', 'USDT']:
                    if asset in historical_data and len(historical_data[asset]) > 0:
                        try:
                            plot_path = analyzer.create_calibration_plot(asset, historical_data[asset])
                            calibration_plots.append(plot_path)
                            self.logger.info(f"📊 Calibration plot created for {asset}")
                        except Exception as plot_error:
                            self.logger.warning(f"⚠️ Failed to create calibration plot for {asset}: {plot_error}")
                
                # Create comprehensive calibration report
                calibration_report = {
                    'timestamp': datetime.now().isoformat(),
                    'calibration_summary': calibration_summary,
                    'calibration_plots': calibration_plots,
                    'validation_method': 'multi_period_sampling',
                    'summary': {
                        'total_assets': len(calibration_summary.get('assets', {})),
                        'plots_created': len(calibration_plots),
                        'validation_status': 'completed'
                    }
                }
                
                # Save comprehensive calibration report
                report_file = self.output_dir / f"aave_calibration_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
                with open(report_file, 'w') as f:
                    json.dump(calibration_report, f, indent=2, default=str)
                
                self.logger.info("=" * 50)
                self.logger.info("🔧 CALIBRATION STAGE COMPLETE")
                self.logger.info("=" * 50)
                self.logger.info(f"✅ Calibration validation completed for {calibration_report['summary']['total_assets']} assets")
                self.logger.info(f"📈 Calibration plots created: {calibration_report['summary']['plots_created']}")
                self.logger.info(f"💾 Summary saved to: {summary_file}")
                self.logger.info(f"💾 Report saved to: {report_file}")
                self.logger.info("=" * 50)
                
                pipeline_results.append({
                    'success': True,
                    'stage': 'calibration',
                    'duration': 0,  # Calibration is fast
                    'results': calibration_report
                })
                
            except Exception as e:
                self.logger.error(f"❌ Calibration stage failed: {e}")
                pipeline_results.append({
                    'success': False,
                    'stage': 'calibration',
                    'duration': 0,
                    'error': str(e)
                })
        
        # Stage 4: Rate Impact Analysis
        if 'analyze' in components:
            self.logger.info("📊 STAGE 4: Rate Impact Analysis")
            self.logger.info("-" * 50)
            
            analyzer_script = "scripts/analyzers/analyze_aave_rate_impact.py"
            analyzer_args = ["--data-dir", "data", "--output-dir", "data/analysis", "--create-plots"]
            
            result = self.run_processor(analyzer_script, analyzer_args)
            pipeline_results.append(result)
            
            if result['success']:
                self.logger.info("=" * 50)
                self.logger.info("📊 ANALYSIS STAGE COMPLETE")
                self.logger.info("=" * 50)
                self.logger.info("✅ Rate impact analysis completed")
                self.logger.info("📊 Market impact plots created")
                self.logger.info(f"⏱️ Duration: {result['duration']:.1f}s")
                self.logger.info("=" * 50)
            else:
                self.logger.error("❌ Rate impact analysis failed")
        
        # Create master report
        total_duration = sum(r['duration'] for r in pipeline_results)
        successful_stages = sum(1 for r in pipeline_results if r['success'])
        total_stages = len(pipeline_results)
        
        master_report = {
            'timestamp': datetime.now().isoformat(),
            'orchestrator': 'aave_data_pipeline',
            'date_range': f"{start_date} to {end_date}",
            'components_executed': components,
            'total_stages': total_stages,
            'successful_stages': successful_stages,
            'failed_stages': total_stages - successful_stages,
            'total_duration_minutes': round(total_duration / 60, 1),
            'pipeline_results': pipeline_results
        }
        
        # Save master report
        report_file = self.output_dir / f"aave_pipeline_report_{start_date}_{end_date}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(report_file, 'w') as f:
            json.dump(master_report, f, indent=2, default=str)
        
        self.logger.info("=" * 80)
        self.logger.info("🎯 AAVE DATA PIPELINE COMPLETE!")
        self.logger.info("=" * 80)
        self.logger.info(f"📊 Stages: {successful_stages}/{total_stages} successful")
        self.logger.info(f"⏱️ Total duration: {total_duration/60:.1f} minutes")
        self.logger.info(f"💾 Report: {report_file}")
        self.logger.info("=" * 80)
        
        return master_report


async def main():
    """
    Main execution function for standalone script usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestrate complete AAVE data pipeline")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=str, default="data/protocol_data/aave", help="Output directory")
    parser.add_argument("--components", type=str, nargs='+', 
                       choices=['download', 'process', 'calibrate', 'analyze'],
                       default=['download', 'process', 'calibrate', 'analyze'],
                       help="Components to run: download (raw AAVE data), process (oracle prices + risk params + hourly interpolation), calibrate (rate model validation), analyze (rate impact)")
    parser.add_argument("--quick-test", action="store_true", help="Run with last 3 days for testing")
    
    args = parser.parse_args()
    
    try:
        orchestrator = AAVEDataOrchestrator(args.output_dir)
        
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
        
        print(f"\n🎯 Starting AAVE data pipeline...")
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"📁 Output directory: {args.output_dir}")
        print(f"🔧 Components: {', '.join(args.components)}")
        print()
        
        result = await orchestrator.download_data(start_date, end_date, args.components)
        
        # Print summary
        if result['successful_stages'] == result['total_stages']:
            print(f"\n🎉 SUCCESS! All {result['total_stages']} stages completed")
            print(f"⏱️ Total duration: {result['total_duration_minutes']:.1f} minutes")
            print(f"💾 Report: {result.get('report_file', 'N/A')}")
        else:
            print(f"\n⚠️ PARTIAL SUCCESS: {result['successful_stages']}/{result['total_stages']} stages completed")
            print(f"⏱️ Total duration: {result['total_duration_minutes']:.1f} minutes")
            print(f"💾 Report: {result.get('report_file', 'N/A')}")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
