"""
Benchmark Analysis Orchestrator

Orchestrates the complete benchmark analysis pipeline:
1. Ethena sUSDE Benchmark Processing (APY to APR conversion + hourly interpolation)
2. Integration with existing AAVE rate analysis for comparison

This orchestrator provides a streamlined approach to benchmark yield analysis
for comparison with restaking strategies.

Inputs:
- Ethena data: data/manual_sources/benchmark_data/
- AAVE rates: data/protocol_data/aave/rates/

Outputs:
- Ethena benchmark: data/protocol_data/staking/benchmark_yields/
- Hourly interpolated data for backtesting comparison
"""

import subprocess
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import pandas as pd


class BenchmarkAnalysisOrchestrator:
    """Orchestrates the complete benchmark analysis pipeline."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        
        # Set up logging
        self.logger = logging.getLogger("benchmark_analysis_orchestrator")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Define available processors
        self.processors = {
            'ethena_benchmark': 'scripts/processors/process_ethena_benchmark.py',
            'aave_hourly_interpolation': 'scripts/utilities/proper_hourly_interpolation.py'
        }
        
        self.logger.info("Benchmark Analysis Orchestrator initialized")
    
    def run_processor(self, processor_name: str, args: List[str] = None) -> Dict:
        """
        Run a specific processor script.
        
        Args:
            processor_name: Name of the processor to run
            args: Additional arguments to pass to the processor
            
        Returns:
            Processing results
        """
        if processor_name not in self.processors:
            raise ValueError(f"Unknown processor: {processor_name}. Available: {list(self.processors.keys())}")
        
        script_path = self.processors[processor_name]
        cmd = ["python", script_path]
        
        if args:
            cmd.extend(args)
        
        self.logger.info(f"🚀 Running {processor_name}: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=Path.cwd()
            )
            
            self.logger.info(f"✅ {processor_name} completed successfully")
            self.logger.debug(f"Output: {result.stdout}")
            
            return {
                'success': True,
                'processor': processor_name,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ {processor_name} failed with return code {e.returncode}")
            self.logger.error(f"Error output: {e.stderr}")
            raise
    
    def run_ethena_benchmark_analysis(self, start_date: str = "2024-01-01", 
                                     end_date: str = "2025-09-18",
                                     create_hourly: bool = True) -> Dict:
        """
        Run Ethena benchmark analysis with hourly interpolation.
        
        Args:
            start_date: Start date for analysis (YYYY-MM-DD)
            end_date: End date for analysis (YYYY-MM-DD)
            create_hourly: Whether to create hourly interpolated data
            
        Returns:
            Analysis results
        """
        self.logger.info("🎯 Starting Ethena benchmark analysis...")
        
        # Prepare arguments
        args = [
            "--start-date", start_date,
            "--end-date", end_date,
            "--data-dir", str(self.data_dir)
        ]
        
        if not create_hourly:
            args.append("--no-hourly")
        
        # Run Ethena benchmark processor
        result = self.run_processor("ethena_benchmark", args)
        
        # Parse the output to extract key metrics
        ethena_summary = self._parse_ethena_results(result['stdout'])
        
        return {
            'ethena_analysis': result,
            'summary': ethena_summary,
            'date_range': f"{start_date} to {end_date}",
            'hourly_interpolation': create_hourly
        }
    
    def run_aave_hourly_interpolation(self) -> Dict:
        """
        Run AAVE hourly interpolation for comparison.
        
        Returns:
            Interpolation results
        """
        self.logger.info("🔄 Running AAVE hourly interpolation...")
        
        result = self.run_processor("aave_hourly_interpolation")
        
        return {
            'aave_interpolation': result,
            'timestamp': datetime.now().isoformat()
        }
    
    def _parse_ethena_results(self, stdout: str) -> Dict:
        """
        Parse Ethena processor output to extract key metrics.
        
        Args:
            stdout: Standard output from the processor
            
        Returns:
            Parsed metrics
        """
        try:
            lines = stdout.strip().split('\n')
            metrics = {}
            
            for line in lines:
                if 'Average APY:' in line:
                    metrics['average_apy'] = float(line.split(':')[1].strip().replace('%', ''))
                elif 'Average APR:' in line:
                    metrics['average_apr'] = float(line.split(':')[1].strip().replace('%', '').split()[0])
                elif 'Daily Records:' in line:
                    metrics['daily_records'] = int(line.split(':')[1].strip().replace(',', ''))
                elif 'Hourly Records:' in line:
                    metrics['hourly_records'] = int(line.split(':')[1].strip().replace(',', ''))
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"⚠️  Failed to parse Ethena results: {e}")
            return {}
    
    def run_complete_benchmark_analysis(self, start_date: str = "2024-01-01", 
                                       end_date: str = "2025-09-18",
                                       include_aave: bool = True) -> Dict:
        """
        Run complete benchmark analysis pipeline.
        
        Args:
            start_date: Start date for analysis (YYYY-MM-DD)
            end_date: End date for analysis (YYYY-MM-DD)
            include_aave: Whether to include AAVE hourly interpolation
            
        Returns:
            Complete analysis results
        """
        self.logger.info("=" * 80)
        self.logger.info("🎯 STARTING COMPLETE BENCHMARK ANALYSIS")
        self.logger.info("=" * 80)
        self.logger.info(f"📅 Date range: {start_date} to {end_date}")
        self.logger.info(f"🔄 AAVE interpolation: {'Yes' if include_aave else 'No'}")
        
        results = {
            'analysis_started': datetime.now().isoformat(),
            'date_range': f"{start_date} to {end_date}",
            'components': {}
        }
        
        try:
            # Step 1: Ethena benchmark analysis
            self.logger.info("\n" + "="*50)
            self.logger.info("STEP 1: ETHENA BENCHMARK ANALYSIS")
            self.logger.info("="*50)
            
            ethena_results = self.run_ethena_benchmark_analysis(start_date, end_date, create_hourly=True)
            results['components']['ethena_benchmark'] = ethena_results
            
            # Step 2: AAVE hourly interpolation (optional)
            if include_aave:
                self.logger.info("\n" + "="*50)
                self.logger.info("STEP 2: AAVE HOURLY INTERPOLATION")
                self.logger.info("="*50)
                
                aave_results = self.run_aave_hourly_interpolation()
                results['components']['aave_interpolation'] = aave_results
            
            # Step 3: Generate summary
            results['analysis_completed'] = datetime.now().isoformat()
            results['status'] = 'success'
            
            # Create comprehensive summary
            summary = self._create_analysis_summary(results)
            results['summary'] = summary
            
            # Save results
            self._save_analysis_results(results, start_date, end_date)
            
            self.logger.info("\n" + "="*80)
            self.logger.info("🎉 BENCHMARK ANALYSIS COMPLETED SUCCESSFULLY!")
            self.logger.info("="*80)
            self._log_summary(summary)
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Benchmark analysis failed: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
            results['analysis_failed'] = datetime.now().isoformat()
            raise
    
    def _create_analysis_summary(self, results: Dict) -> Dict:
        """Create a comprehensive analysis summary."""
        summary = {
            'analysis_type': 'benchmark_comparison',
            'date_range': results['date_range'],
            'components_completed': list(results['components'].keys()),
            'ethena_metrics': results['components'].get('ethena_benchmark', {}).get('summary', {}),
            'aave_interpolation': 'completed' if 'aave_interpolation' in results['components'] else 'skipped',
            'output_files': self._get_output_files(results),
            'methodology': {
                'ethena_processing': 'apy_to_apr_conversion_with_hourly_interpolation',
                'aave_processing': 'proper_hourly_interpolation_with_ccr_calculation',
                'purpose': 'benchmark_comparison_for_restaking_strategy_evaluation'
            }
        }
        
        return summary
    
    def _get_output_files(self, results: Dict) -> List[str]:
        """Extract output file information from results."""
        files = []
        
        # Ethena files
        ethena_component = results['components'].get('ethena_benchmark', {})
        if ethena_component:
            # These would be in the actual output directory
            start_date = results['date_range'].split(' to ')[0]
            end_date = results['date_range'].split(' to ')[1]
            files.extend([
                f"ethena_susde_apr_benchmark_{start_date}_{end_date}.csv",
                f"ethena_susde_apr_benchmark_hourly_{start_date}_{end_date}.csv",
                f"ethena_processing_summary_{start_date}_{end_date}.json"
            ])
        
        # AAVE files (would be generated by proper_hourly_interpolation.py)
        if 'aave_interpolation' in results['components']:
            files.append("aave_v3_*_rates_*_hourly.csv (multiple assets)")
        
        return files
    
    def _save_analysis_results(self, results: Dict, start_date: str, end_date: str):
        """Save analysis results to file."""
        output_dir = self.data_dir / "analysis" / "benchmark_analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = output_dir / f"benchmark_analysis_results_{start_date}_{end_date}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"💾 Analysis results saved: {results_file}")
    
    def _log_summary(self, summary: Dict):
        """Log analysis summary."""
        self.logger.info(f"📊 Components completed: {', '.join(summary['components_completed'])}")
        
        ethena_metrics = summary.get('ethena_metrics', {})
        if ethena_metrics:
            self.logger.info(f"📈 Ethena Average APY: {ethena_metrics.get('average_apy', 'N/A'):.2f}%")
            self.logger.info(f"📈 Ethena Average APR: {ethena_metrics.get('average_apr', 'N/A'):.2f}%")
            self.logger.info(f"📊 Ethena Daily Records: {ethena_metrics.get('daily_records', 'N/A'):,}")
            if 'hourly_records' in ethena_metrics:
                self.logger.info(f"📊 Ethena Hourly Records: {ethena_metrics['hourly_records']:,}")
        
        self.logger.info(f"🔄 AAVE Interpolation: {summary['aave_interpolation']}")
        self.logger.info(f"📁 Output files: {len(summary['output_files'])} files generated")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run complete benchmark analysis pipeline")
    parser.add_argument("--start-date", type=str, default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2025-09-18", help="End date (YYYY-MM-DD)")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--no-aave", action="store_true", help="Skip AAVE hourly interpolation")
    parser.add_argument("--ethena-only", action="store_true", help="Run only Ethena benchmark analysis")
    
    args = parser.parse_args()
    
    try:
        orchestrator = BenchmarkAnalysisOrchestrator(args.data_dir)
        
        if args.ethena_only:
            # Run only Ethena analysis
            result = orchestrator.run_ethena_benchmark_analysis(args.start_date, args.end_date)
            print(f"\n🎉 ETHENA BENCHMARK ANALYSIS COMPLETED!")
            print(f"📈 Average APY: {result['summary'].get('average_apy', 'N/A'):.2f}%")
            print(f"📈 Average APR: {result['summary'].get('average_apr', 'N/A'):.2f}%")
        else:
            # Run complete analysis
            result = orchestrator.run_complete_benchmark_analysis(
                args.start_date, 
                args.end_date, 
                include_aave=not args.no_aave
            )
            print(f"\n🎉 COMPLETE BENCHMARK ANALYSIS FINISHED!")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
