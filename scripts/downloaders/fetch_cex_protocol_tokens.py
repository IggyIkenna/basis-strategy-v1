"""
CEX Protocol Token Data Downloader

Downloads hourly OHLCV data for protocol tokens from Binance:
- EIGEN/USDT (since 2024-10-05 - pool creation date)
- ETHFI/USDT (since 2024-06-01 - good data availability)

Features:
- Hourly OHLCV data from Binance Spot API
- Enforced token creation dates (no downloads before tokens existed)
- Gap-filled data for complete timelines
- Organized output to protocol_tokens directory
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
    from .clients.binance_spot_client import BinanceSpotClient
    from .base_downloader import BaseDownloader
except ImportError:
    # Standalone execution
    sys.path.append(str(Path(__file__).parent))
    from clients.binance_spot_client import BinanceSpotClient
    from base_downloader import BaseDownloader


class CEXProtocolTokenDownloader(BaseDownloader):
    """
    CEX protocol token downloader using Binance Spot API.
    
    Features:
    - EIGEN/USDT and ETHFI/USDT hourly data
    - Enforced token creation dates
    - Gap-filled timelines
    - High liquidity CEX data
    """
    
    def __init__(self, output_dir: str = "data/market_data/spot_prices/protocol_tokens"):
        super().__init__("cex_protocol_tokens", output_dir)
        
        # Token creation dates (enforced minimums)
        self.token_creation_dates = {
            "EIGEN": "2024-10-05",  # EIGEN token launch
            "ETHFI": "2024-06-01"   # Good data availability (actual launch earlier)
        }
        
        # Initialize Binance client
        try:
            self.binance_client = BinanceSpotClient(str(Path(output_dir).parent))
            self.logger.info("✅ Binance Spot client initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Binance client: {e}")
            raise RuntimeError("Binance Spot client required for protocol token data")
    
    def _enforce_token_creation_dates(self, start_date: str) -> Dict[str, str]:
        """
        Enforce token creation dates - don't allow downloads before tokens existed.
        
        Args:
            start_date: Requested start date
            
        Returns:
            Dict of actual start dates to use for each token
        """
        actual_dates = {}
        
        for token, creation_date in self.token_creation_dates.items():
            if start_date < creation_date:
                actual_dates[token] = creation_date
                self.logger.info(f"📅 {token}: Using creation date {creation_date} (requested {start_date})")
            else:
                actual_dates[token] = start_date
                self.logger.info(f"📅 {token}: Using requested date {start_date}")
        
        return actual_dates
    
    async def download_protocol_token_data(self, token: str, start_date: str, end_date: str) -> Dict:
        """
        Download data for a specific protocol token.
        
        Args:
            token: Token symbol (EIGEN or ETHFI)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Download result dictionary
        """
        self.logger.info(f"🚀 Downloading {token}/USDT data from Binance")
        
        try:
            # Use Binance client to download OHLCV data
            symbol = f"{token}USDT"
            result = await self.binance_client.download_spot_ohlcv(symbol, token, start_date, end_date)
            
            if result['success']:
                self.logger.info(f"✅ {token}: {result['record_count']} records")
            else:
                self.logger.error(f"❌ {token}: Download failed")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ {token}: Unexpected error - {e}")
            return {
                'success': False,
                'asset': token,
                'error': str(e),
                'record_count': 0
            }
    
    async def download_data(self, start_date: str, end_date: str, exchanges: List[str] = None) -> Dict:
        """
        Download all protocol token data with enforced creation dates.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            exchanges: List of exchanges (ignored - protocol tokens only available on Binance)
            
        Returns:
            Combined download results
        """
        self.logger.info("🚀 Starting CEX protocol token data download")
        self.logger.info(f"📅 Requested date range: {start_date} to {end_date}")
        
        # Enforce token creation dates
        actual_dates = self._enforce_token_creation_dates(start_date)
        
        download_results = []
        
        # Download EIGEN data
        if "EIGEN" in actual_dates:
            eigen_result = await self.download_protocol_token_data("EIGEN", actual_dates["EIGEN"], end_date)
            download_results.append(eigen_result)
        
        # Download ETHFI data
        if "ETHFI" in actual_dates:
            ethfi_result = await self.download_protocol_token_data("ETHFI", actual_dates["ETHFI"], end_date)
            download_results.append(ethfi_result)
        
        # Create summary report
        successful = sum(1 for r in download_results if r.get('success', False))
        total_records = sum(r.get('record_count', 0) for r in download_results)
        
        combined_report = {
            'timestamp': datetime.now().isoformat(),
            'downloader': 'cex_protocol_tokens',
            'date_range': f"{start_date} to {end_date}",
            'enforced_dates': actual_dates,
            'total_downloads': len(download_results),
            'successful_downloads': successful,
            'failed_downloads': len(download_results) - successful,
            'total_records': total_records,
            'downloads': download_results
        }
        
        # Save report
        report_file = self.save_report(
            combined_report, 
            f"cex_protocol_tokens_report_{start_date}_{end_date}.json"
        )
        
        # Log summary
        self.logger.info("=" * 70)
        self.logger.info("🎯 CEX PROTOCOL TOKEN DOWNLOAD COMPLETE!")
        self.logger.info("=" * 70)
        self.logger.info(f"✅ Successful downloads: {successful}/{len(download_results)}")
        self.logger.info(f"📊 Total records: {total_records:,}")
        self.logger.info(f"💾 Output directory: {self.output_dir}")
        self.logger.info(f"📋 Report saved: {report_file}")
        
        # Show enforced dates
        for token, date in actual_dates.items():
            self.logger.info(f"📅 {token}: Used {date}")
        
        self.logger.info("=" * 70)
        
        return combined_report


async def main():
    """
    Main execution function for standalone script usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Download protocol token data from Binance CEX")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=str, default="data/market_data/spot_prices/protocol_tokens", help="Output directory")
    parser.add_argument("--token", type=str, choices=["EIGEN", "ETHFI", "all"], default="all", help="Specific token to download")
    
    args = parser.parse_args()
    
    try:
        downloader = CEXProtocolTokenDownloader(args.output_dir)
        
        # Use provided dates or config defaults
        if args.start_date:
            start_date = args.start_date
        else:
            start_date = downloader.get_date_range()
            print(f"Using config start date defaults: {start_date}")
        # Use provided dates or the current date
        if args.end_date:
            end_date = args.end_date
        else:
            end_date = datetime.now().strftime('%Y-%m-%d')
            print(f"Using current date as end date: {end_date}")
        
        print(f"🎯 Downloading protocol token data from Binance...")
        print(f"📊 Tokens: EIGEN (since 2024-10-05), ETHFI (since 2024-06-01)")
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"💾 Output: {args.output_dir}")
        print(f"🔧 Token creation dates will be enforced")
        
        # Run download
        result = await downloader.download_data(start_date, end_date)
        
        # Print summary
        if result['successful_downloads'] > 0:
            print(f"\n🎉 SUCCESS! Downloaded {result['total_records']:,} protocol token records")
            print(f"✅ Tokens downloaded: {result['successful_downloads']}/{result['total_downloads']}")
            print(f"📁 Files saved to: {args.output_dir}")
            
            # Show enforced dates
            enforced = result.get('enforced_dates', {})
            for token, date in enforced.items():
                print(f"   📅 {token}: Started from {date}")
        else:
            print(f"\n❌ FAILED! No protocol token data was downloaded successfully")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
