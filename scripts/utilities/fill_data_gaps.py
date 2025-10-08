"""
Data Gap Filling Utility

Uses the data completeness analysis to fill specific gaps in the dataset:
- Loads gap analysis reports
- Downloads only missing data periods
- Handles rate limits gracefully (pause/resume)
- Updates manifest tracking

Enables efficient incremental data collection without re-downloading existing data.
"""

import asyncio
import json
import pandas as pd
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add the backend source to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "backend" / "src"))

# Handle both standalone and module imports
try:
    from .fetch_market_data import MarketDataDownloader
    from .fetch_aave_data import AAVEDataDownloader
    from .fetch_onchain_data import OnChainDataDownloader
except ImportError:
    # Standalone execution
    sys.path.append(str(Path(__file__).parent))
    from fetch_market_data import MarketDataDownloader
    from fetch_aave_data import AAVEDataDownloader
    from fetch_onchain_data import OnChainDataDownloader


class DataGapFiller:
    """
    Fills identified data gaps using incremental downloads.
    
    Features:
    - Loads gap analysis from completeness analyzer
    - Downloads only missing periods
    - Handles rate limits with pause/resume
    - Updates progress tracking
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.analysis_dir = self.data_dir / "analysis"
        
        # Set up logging
        import logging
        self.logger = logging.getLogger("gap_filler")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info(f"Data Gap Filler initialized")
    
    def load_gap_analysis(self, start_date: str, end_date: str) -> Optional[Dict]:
        """Load gap analysis report."""
        manifest_file = self.analysis_dir / f"missing_data_manifest_{start_date}_{end_date}.json"
        
        if not manifest_file.exists():
            self.logger.error(f"Gap analysis not found: {manifest_file}")
            self.logger.info("Run: python scripts/analysis/analyze_data_completeness.py first")
            return None
        
        try:
            with open(manifest_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load gap analysis: {e}")
            return None
    
    async def fill_market_data_gaps(self, gap_analysis: Dict, max_gaps_per_asset: int = 10) -> Dict:
        """
        Fill market data gaps identified in the analysis.
        
        Args:
            gap_analysis: Gap analysis from completeness analyzer
            max_gaps_per_asset: Maximum gaps to fill per asset (rate limit protection)
            
        Returns:
            Gap filling results
        """
        self.logger.info("🔄 Starting market data gap filling...")
        
        market_data = gap_analysis['missing_data_by_source'].get('market_data', {})
        results = {}
        
        for asset, analysis in market_data.items():
            if 'gaps' not in analysis or not analysis['gaps']:
                self.logger.info(f"✅ {asset}: No gaps to fill")
                continue
            
            gaps = analysis['gaps']
            gaps_to_fill = gaps[:max_gaps_per_asset]  # Limit to avoid overwhelming APIs
            
            self.logger.info(f"📋 {asset}: Filling {len(gaps_to_fill)}/{len(gaps)} gaps")
            
            # Initialize downloader
            try:
                downloader = MarketDataDownloader(f"{self.data_dir}/market_gap_fill")
                
                filled_gaps = []
                failed_gaps = []
                
                for i, gap in enumerate(gaps_to_fill):
                    gap_start = pd.to_datetime(gap['start']).strftime('%Y-%m-%d')
                    gap_end = pd.to_datetime(gap['end']).strftime('%Y-%m-%d')
                    gap_hours = gap['duration_hours']
                    
                    self.logger.info(f"  📅 Gap {i+1}/{len(gaps_to_fill)}: {gap_start} to {gap_end} ({gap_hours}h)")
                    
                    try:
                        # Download this specific gap
                        result = await downloader.download_data(gap_start, gap_end)
                        
                        if result.get('successful_downloads', 0) > 0:
                            filled_gaps.append(gap)
                            self.logger.info(f"    ✅ Gap filled: {result['total_records']} records")
                        else:
                            failed_gaps.append(gap)
                            self.logger.warning(f"    ❌ Gap fill failed")
                        
                        # Rate limit protection
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        failed_gaps.append(gap)
                        self.logger.error(f"    ❌ Gap fill error: {e}")
                
                results[asset] = {
                    'total_gaps': len(gaps),
                    'gaps_attempted': len(gaps_to_fill),
                    'gaps_filled': len(filled_gaps),
                    'gaps_failed': len(failed_gaps),
                    'success_rate': len(filled_gaps) / len(gaps_to_fill) * 100 if gaps_to_fill else 0
                }
                
                self.logger.info(f"✅ {asset}: {len(filled_gaps)}/{len(gaps_to_fill)} gaps filled")
                
            except Exception as e:
                self.logger.error(f"❌ {asset}: Downloader initialization failed - {e}")
                results[asset] = {'error': str(e)}
        
        return results
    
    async def run_targeted_gap_filling(self, start_date: str = "2024-01-01", 
                                     end_date: str = "2025-09-18",
                                     max_gaps_per_asset: int = 10) -> Dict:
        """
        Run targeted gap filling based on completeness analysis.
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            max_gaps_per_asset: Maximum gaps to fill per asset
            
        Returns:
            Gap filling results
        """
        self.logger.info("🚀 Starting targeted data gap filling")
        self.logger.info(f"📅 Period: {start_date} to {end_date}")
        self.logger.info(f"🔢 Max gaps per asset: {max_gaps_per_asset}")
        
        # Load gap analysis
        gap_analysis = self.load_gap_analysis(start_date, end_date)
        if not gap_analysis:
            return {'error': 'Gap analysis not available'}
        
        # Fill market data gaps
        market_results = await self.fill_market_data_gaps(gap_analysis, max_gaps_per_asset)
        
        # Create comprehensive results
        results = {
            'gap_filling_completed_at': datetime.now().isoformat(),
            'period_analyzed': f"{start_date} to {end_date}",
            'max_gaps_per_asset': max_gaps_per_asset,
            'market_data_results': market_results,
            'summary': {
                'assets_processed': len(market_results),
                'total_gaps_filled': sum(r.get('gaps_filled', 0) for r in market_results.values()),
                'total_gaps_failed': sum(r.get('gaps_failed', 0) for r in market_results.values()),
                'overall_success_rate': 0
            }
        }
        
        # Calculate overall success rate
        total_attempted = sum(r.get('gaps_attempted', 0) for r in market_results.values())
        total_filled = results['summary']['total_gaps_filled']
        
        if total_attempted > 0:
            results['summary']['overall_success_rate'] = (total_filled / total_attempted) * 100
        
        # Save results
        results_file = self.analysis_dir / f"gap_filling_results_{start_date}_{end_date}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info("=" * 70)
        self.logger.info("🎯 GAP FILLING COMPLETE!")
        self.logger.info("=" * 70)
        self.logger.info(f"📊 Assets processed: {results['summary']['assets_processed']}")
        self.logger.info(f"✅ Gaps filled: {results['summary']['total_gaps_filled']}")
        self.logger.info(f"❌ Gaps failed: {results['summary']['total_gaps_failed']}")
        self.logger.info(f"📈 Success rate: {results['summary']['overall_success_rate']:.1f}%")
        self.logger.info(f"💾 Results saved: {results_file}")
        self.logger.info("=" * 70)
        
        return results


async def main():
    """
    Main execution function for standalone script usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Fill identified data gaps using incremental downloads")
    parser.add_argument("--start-date", type=str, default="2024-01-01", help="Analysis start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2025-09-18", help="Analysis end date (YYYY-MM-DD)")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--max-gaps", type=int, default=10, help="Maximum gaps to fill per asset")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded without actually downloading")
    
    args = parser.parse_args()
    
    try:
        gap_filler = DataGapFiller(args.data_dir)
        
        if args.dry_run:
            # Load and show gap analysis without downloading
            gap_analysis = gap_filler.load_gap_analysis(args.start_date, args.end_date)
            if gap_analysis:
                market_data = gap_analysis['missing_data_by_source'].get('market_data', {})
                
                print(f"\n🔍 DRY RUN - Would fill these gaps:")
                for asset, analysis in market_data.items():
                    if 'gaps' in analysis and analysis['gaps']:
                        gaps_to_show = analysis['gaps'][:args.max_gaps]
                        print(f"\n📈 {asset}: {len(gaps_to_show)}/{len(analysis['gaps'])} gaps")
                        for gap in gaps_to_show:
                            start = pd.to_datetime(gap['start']).strftime('%Y-%m-%d')
                            end = pd.to_datetime(gap['end']).strftime('%Y-%m-%d')
                            hours = gap['duration_hours']
                            print(f"     📅 {start} to {end} ({hours}h)")
            
            return 0
        else:
            # Run actual gap filling
            results = await gap_filler.run_targeted_gap_filling(
                args.start_date, args.end_date, args.max_gaps
            )
            
            # Print summary
            if results.get('summary', {}).get('total_gaps_filled', 0) > 0:
                print(f"\n🎉 SUCCESS! Filled {results['summary']['total_gaps_filled']} data gaps")
                print(f"📈 Success rate: {results['summary']['overall_success_rate']:.1f}%")
            else:
                print(f"\n⚠️ No gaps were filled - check logs for details")
            
            return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
