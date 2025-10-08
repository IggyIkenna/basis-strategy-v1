"""
Staking Yields Analysis Orchestrator

Orchestrates the complete staking yields analysis pipeline:
1. Oracle Base Yields Processing (weETH, wstETH from Aave oracle ratios)
2. EtherFi Seasonal Rewards Processing (EIGEN + ETHFI distributions)

This orchestrator provides a simplified, streamlined approach to staking yield analysis
using the most accurate data sources available.

Inputs:
- Aave oracle data: data/protocol_data/aave/oracle/
- EtherFi distributions: data/manual_sources/etherfi_distributions/
- Token prices: data/market_data/spot_prices/

Outputs:
- Oracle base yields: data/protocol_data/staking/base_yields/
- Seasonal rewards: data/protocol_data/staking/restaking_final/
- Comprehensive analysis: data/protocol_data/staking/restaking_final/
"""

import subprocess
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import pandas as pd


class StakingYieldsOrchestrator:
    """Orchestrates the complete staking yields analysis pipeline."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        
        # Set up logging
        self.logger = logging.getLogger("staking_yields_orchestrator")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Define available processors
        self.processors = {
            'oracle_base_yields': 'scripts/processors/process_oracle_base_yields.py',
            'etherfi_seasonal_rewards': 'scripts/processors/process_etherfi_seasonal_rewards.py'
        }
        
        self.logger.info("Staking Yields Analysis Orchestrator initialized")
        self.logger.info(f"Data directory: {self.data_dir}")
        self.logger.info(f"Available processors: {list(self.processors.keys())}")
    
    def run_processor(self, processor_script: str, args: List[str] = None) -> Dict:
        """Run a processor script and return results."""
        if args is None:
            args = []
        
        self.logger.info(f"🔄 Running processor: {processor_script}")
        self.logger.info(f"   Args: {' '.join(args)}")
        
        try:
            # Run the processor script
            cmd = ["python", processor_script] + args
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.data_dir.parent)
            
            if result.returncode == 0:
                self.logger.info("✅ Processor completed successfully")
                return {
                    'success': True,
                    'processor': processor_script,
                    'args': args,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                self.logger.error(f"❌ Processor failed with return code {result.returncode}")
                self.logger.error(f"   stdout: {result.stdout}")
                self.logger.error(f"   stderr: {result.stderr}")
                return {
                    'success': False,
                    'processor': processor_script,
                    'args': args,
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except Exception as e:
            self.logger.error(f"❌ Failed to run processor: {e}")
            return {
                'success': False,
                'processor': processor_script,
                'args': args,
                'error': str(e)
            }
    
    def run_oracle_base_yields_processing(self, start_date: str, end_date: str) -> Dict:
        """Run oracle base yields processing."""
        self.logger.info("🔄 STAGE 1: Oracle Base Yields Processing")
        self.logger.info("-" * 50)
        
        processor_script = self.processors['oracle_base_yields']
        args = [
            "--start-date", start_date,
            "--end-date", end_date,
            "--data-dir", str(self.data_dir)
        ]
        
        result = self.run_processor(processor_script, args)
        
        if result['success']:
            self.logger.info("✅ Oracle base yields processing completed")
        else:
            self.logger.error("❌ Oracle base yields processing failed")
        
        return result
    
    def run_etherfi_seasonal_rewards_processing(self, start_date: str, end_date: str) -> Dict:
        """Run EtherFi seasonal rewards processing."""
        self.logger.info("🔄 STAGE 2: EtherFi Seasonal Rewards Processing")
        self.logger.info("-" * 50)
        
        processor_script = self.processors['etherfi_seasonal_rewards']
        args = [
            "--start-date", start_date,
            "--end-date", end_date,
            "--data-dir", str(self.data_dir)
        ]
        
        result = self.run_processor(processor_script, args)
        
        if result['success']:
            self.logger.info("✅ EtherFi seasonal rewards processing completed")
        else:
            self.logger.error("❌ EtherFi seasonal rewards processing failed")
        
        return result
    
    def create_comprehensive_analysis(self, start_date: str, end_date: str, results: List[Dict]) -> Dict:
        """Create comprehensive analysis of all staking yields."""
        self.logger.info("📊 Creating comprehensive analysis...")
        
        # Load processed data for analysis
        analysis_data = {}
        
        # Load oracle base yields
        oracle_file = self.data_dir / "protocol_data" / "staking" / "base_yields" / f"oracle_base_yields_summary_{start_date}_{end_date}.json"
        if oracle_file.exists():
            with open(oracle_file, 'r') as f:
                analysis_data['oracle_base_yields'] = json.load(f)
        
        # Load seasonal rewards
        seasonal_file = self.data_dir / "protocol_data" / "staking" / "restaking_final" / f"etherfi_seasonal_analysis_{start_date}_{end_date}.json"
        if seasonal_file.exists():
            with open(seasonal_file, 'r') as f:
                analysis_data['etherfi_seasonal_rewards'] = json.load(f)
        
        # Create comprehensive summary
        summary = {
            'analysis_completed': datetime.now().isoformat(),
            'period': f"{start_date} to {end_date}",
            'orchestrator': 'staking_yields_analysis',
            'methodology': 'oracle_base_yields_plus_seasonal_rewards',
            'data_sources': {
                'base_yields': 'aave_oracle_weeth_wsteth_ratios',
                'seasonal_rewards': 'etherfi_gitbook_real_distributions_plus_defillama_fallback'
            },
            'processing_results': {
                'oracle_base_yields': results[0] if len(results) > 0 else None,
                'etherfi_seasonal_rewards': results[1] if len(results) > 1 else None
            },
            'data_availability': {
                'oracle_base_yields_available': 'oracle_base_yields' in analysis_data,
                'seasonal_rewards_available': 'etherfi_seasonal_rewards' in analysis_data
            }
        }
        
        # Add yield analysis if data is available
        if 'oracle_base_yields' in analysis_data and 'etherfi_seasonal_rewards' in analysis_data:
            oracle_data = analysis_data['oracle_base_yields']
            seasonal_data = analysis_data['etherfi_seasonal_rewards']
            
            summary['yield_analysis'] = {
                'weeth_base_apr': oracle_data.get('average_yields', {}).get('weeth_avg_apr', 0),
                'wsteth_base_apr': oracle_data.get('average_yields', {}).get('wsteth_avg_apr', 0),
                'eigen_daily_yield': seasonal_data.get('daily_yield_analysis_percent', {}).get('eigen_daily_percent', 0),
                'ethfi_daily_yield': seasonal_data.get('daily_yield_analysis_percent', {}).get('ethfi_topup_daily_percent', 0) + seasonal_data.get('daily_yield_analysis_percent', {}).get('ethfi_seasonal_daily_percent', 0),
                'total_seasonal_daily_yield': seasonal_data.get('daily_yield_analysis_percent', {}).get('total_daily_percent', 0)
            }
        
        # Save comprehensive analysis
        analysis_file = self.data_dir / "protocol_data" / "staking" / "restaking_final" / f"comprehensive_staking_analysis_{start_date}_{end_date}.json"
        with open(analysis_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"💾 Comprehensive analysis: {analysis_file}")
        
        return summary
    
    def run_complete_analysis(self, start_date: str = "2024-01-01", end_date: str = "2025-09-18", 
                            components: List[str] = None) -> Dict:
        """Run complete staking yields analysis."""
        if components is None:
            components = ['oracle_base_yields', 'etherfi_seasonal_rewards', 'analysis']
        
        self.logger.info("🚀 Starting complete staking yields analysis...")
        self.logger.info(f"📅 Period: {start_date} to {end_date}")
        self.logger.info(f"🔄 Components: {', '.join(components)}")
        
        results = []
        
        # Run oracle base yields processing
        if 'oracle_base_yields' in components:
            result = self.run_oracle_base_yields_processing(start_date, end_date)
            results.append(result)
        
        # Run EtherFi seasonal rewards processing
        if 'etherfi_seasonal_rewards' in components:
            result = self.run_etherfi_seasonal_rewards_processing(start_date, end_date)
            results.append(result)
        
        # Create comprehensive analysis
        if 'analysis' in components:
            analysis = self.create_comprehensive_analysis(start_date, end_date, results)
            results.append({'success': True, 'analysis': analysis})
        
        # Create final summary
        successful_results = [r for r in results if r.get('success', False)]
        failed_results = [r for r in results if not r.get('success', False)]
        
        final_summary = {
            'orchestration_completed': datetime.now().isoformat(),
            'period': f"{start_date} to {end_date}",
            'components_requested': components,
            'total_results': len(results),
            'successful_results': len(successful_results),
            'failed_results': len(failed_results),
            'results': results
        }
        
        # Save final summary
        summary_file = self.data_dir / "protocol_data" / "staking" / "restaking_final" / f"staking_yields_orchestration_summary_{start_date}_{end_date}.json"
        with open(summary_file, 'w') as f:
            json.dump(final_summary, f, indent=2)
        
        self.logger.info("=" * 80)
        self.logger.info("🎯 STAKING YIELDS ANALYSIS COMPLETE!")
        self.logger.info("=" * 80)
        self.logger.info(f"📊 Components processed: {len(successful_results)}/{len(results)}")
        self.logger.info(f"💾 Final summary: {summary_file}")
        self.logger.info("=" * 80)
        
        return final_summary


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestrate complete staking yields analysis")
    parser.add_argument("--start-date", type=str, default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2025-09-18", help="End date (YYYY-MM-DD)")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--components", nargs='+', 
                       choices=['oracle_base_yields', 'etherfi_seasonal_rewards', 'analysis'],
                       default=['oracle_base_yields', 'etherfi_seasonal_rewards', 'analysis'],
                       help="Components to run")
    
    args = parser.parse_args()
    
    try:
        orchestrator = StakingYieldsOrchestrator(args.data_dir)
        
        print("🎯 Staking Yields Analysis Orchestrator")
        print("📊 Oracle base yields + EtherFi seasonal rewards")
        print(f"📅 Period: {args.start_date} to {args.end_date}")
        print(f"🔄 Components: {', '.join(args.components)}")
        
        results = orchestrator.run_complete_analysis(args.start_date, args.end_date, args.components)
        
        print(f"\n🎉 SUCCESS! Staking yields analysis completed")
        print(f"📊 Components processed: {results['successful_results']}/{results['total_results']}")
        
        if results['failed_results'] > 0:
            print(f"⚠️  {results['failed_results']} components failed - check logs for details")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())