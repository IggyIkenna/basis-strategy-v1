"""
Peg Analysis Orchestrator

Coordinates the complete peg discount/premium analysis pipeline:
- Ensures AAVE oracle data is available (from existing downloads)
- Ensures market data is available (from existing downloads) 
- Runs peg analysis using AAVE oracle as fair value benchmark
- Eliminates dependency on manual CSV files

This orchestrator follows the architectural pattern of coordinating
existing data sources rather than re-downloading data.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List
import argparse

# Add the scripts directory to the path so we can import processors
sys.path.append(str(Path(__file__).parent.parent))

from processors.process_peg_discount_data import PegDiscountProcessor

class PegAnalysisOrchestrator:
    """Orchestrates the complete peg analysis pipeline."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        
        # Set up logging
        self.logger = logging.getLogger("peg_orchestrator")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info("Peg Analysis Orchestrator initialized")
    
    def _check_data_availability(self) -> Dict[str, bool]:
        """Check if required data files are available."""
        self.logger.info("🔍 Checking data availability...")
        
        availability = {}
        
        # Check AAVE oracle data
        oracle_dir = self.data_dir / "protocol_data" / "aave" / "oracle"
        oracle_files = {
            'wstETH': oracle_dir / "wstETH_ETH_oracle_2024-01-01_2025-09-18.csv",
            'weETH': oracle_dir / "weETH_ETH_oracle_2024-01-01_2025-09-18.csv"
        }
        
        for asset, file_path in oracle_files.items():
            exists = file_path.exists()
            availability[f'{asset}_oracle'] = exists
            if exists:
                self.logger.info(f"   ✅ {asset} oracle data: {file_path.name}")
            else:
                self.logger.warning(f"   ❌ {asset} oracle data missing: {file_path}")
        
        # Check market data (each asset has its specific DEX pool)
        market_dir = self.data_dir / "market_data" / "spot_prices" / "lst_eth_ratios"
        market_files = {
            'wstETH_uniswap': list(market_dir.glob("uniswapv3_wstETHWETH_*.csv")),
            'weETH_curve': list(market_dir.glob("curve_weETHWETH_*.csv"))
        }
        
        for key, files in market_files.items():
            exists = len(files) > 0
            availability[f'{key}_market'] = exists
            if exists:
                self.logger.info(f"   ✅ {key} market data: {files[0].name}")
            else:
                self.logger.warning(f"   ❌ {key} market data missing")
        
        return availability
    
    def _run_peg_analysis(self) -> Dict:
        """Run the peg analysis using the updated processor."""
        self.logger.info("🚀 Running peg analysis with AAVE oracle benchmark...")
        
        try:
            processor = PegDiscountProcessor(str(self.data_dir))
            results = processor.process_all_peg_data()
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Peg analysis failed: {e}")
            raise
    
    def run_complete_analysis(self) -> Dict:
        """Run the complete peg analysis pipeline."""
        self.logger.info("=" * 70)
        self.logger.info("🎯 PEG ANALYSIS ORCHESTRATION STARTED")
        self.logger.info("=" * 70)
        
        # Check data availability
        availability = self._check_data_availability()
        
        # Check if we have minimum required data (each asset has its specific DEX pool)
        required_data = ['wstETH_oracle', 'weETH_oracle', 'wstETH_uniswap_market', 'weETH_curve_market']
        missing_data = [key for key in required_data if not availability.get(key, False)]
        
        if missing_data:
            self.logger.error(f"❌ Missing required data: {missing_data}")
            self.logger.error("💡 Run the following to get missing data:")
            self.logger.error("   python scripts/processors/process_aave_oracle_prices.py")
            self.logger.error("   python scripts/orchestrators/fetch_pool_data.py --start-date 2024-01-01")
            return {'success': False, 'error': f'Missing data: {missing_data}'}
        
        # Run peg analysis
        try:
            results = self._run_peg_analysis()
            
            # Count successful results
            successful = sum(1 for r in results.values() if 'error' not in r)
            
            self.logger.info("=" * 70)
            self.logger.info("🎯 PEG ANALYSIS ORCHESTRATION COMPLETE!")
            self.logger.info("=" * 70)
            self.logger.info(f"✅ Assets processed: {successful}/{len(results)}")
            
            for asset, result in results.items():
                if 'error' not in result:
                    avg_premium = result['peg_statistics']['average_premium_percent']
                    cost_analysis = result.get('cost_analysis', {})
                    profitable_dex_pct = cost_analysis.get('profitable_dex_percentage', 0)
                    
                    protocol = "lido" if asset == "wstETH" else "etherfi"
                    direct_pct = result['route_analysis'][f'direct_{protocol}_percentage']
                    dex_pct = result['route_analysis']['dex_swap_percentage']
                    
                    self.logger.info(f"📊 {asset}: {avg_premium:.2f}% avg premium")
                    self.logger.info(f"   🛣️  Optimal routes: {direct_pct:.1f}% direct, {dex_pct:.1f}% DEX")
                    self.logger.info(f"   💰 Profitable DEX opportunities: {profitable_dex_pct:.1f}%")
                else:
                    self.logger.error(f"❌ {asset}: {result['error']}")
            
            self.logger.info("=" * 70)
            
            return {
                'success': True,
                'assets_processed': successful,
                'total_assets': len(results),
                'results': results
            }
            
        except Exception as e:
            self.logger.error(f"❌ Orchestration failed: {e}")
            return {'success': False, 'error': str(e)}

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Orchestrate peg analysis using AAVE oracle")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--check-only", action="store_true", help="Only check data availability")
    
    args = parser.parse_args()
    
    try:
        orchestrator = PegAnalysisOrchestrator(args.data_dir)
        
        if args.check_only:
            print("🔍 Checking data availability...")
            availability = orchestrator._check_data_availability()
            
            print("\n📊 Data Availability Summary:")
            for key, available in availability.items():
                status = "✅ Available" if available else "❌ Missing"
                print(f"   {key}: {status}")
            
            return 0
        
        print("🎯 Orchestrating peg analysis with AAVE oracle benchmark...")
        print("📊 Using existing AAVE oracle and market data")
        print("🔄 Eliminating dependency on manual CSV files")
        
        result = orchestrator.run_complete_analysis()
        
        if result.get('success'):
            print(f"\n🎉 SUCCESS! Processed {result['assets_processed']} assets")
            print("📈 Peg analysis complete - ready for backtesting")
        else:
            print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

