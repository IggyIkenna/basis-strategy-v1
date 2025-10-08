"""
CEX Spot Data Downloader

Downloads hourly ETH/USDT OHLCV data from multiple exchanges:
- Binance Spot (since 2020-01-01 - for risk management history)
- Bybit (since 2024-01-01)
- OKX (since 2024-01-01) 
- Binance Futures (since 2024-01-01)

Features:
- Multi-exchange ETH/USDT spot data
- Enforced exchange-specific start dates
- Hourly OHLCV data
- Risk management history (Binance back to 2020)
- Organized output to eth_usd directory
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List

# Add the backend source to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "backend" / "src"))

# Handle both standalone and module imports
try:
    from .clients.binance_spot_client import BinanceSpotClient
    from .clients.bybit_client import BybitClient
    from .clients.okx_client import OKXClient
    from .base_downloader import BaseDownloader
except ImportError:
    # Standalone execution
    sys.path.append(str(Path(__file__).parent))
    from clients.binance_spot_client import BinanceSpotClient
    from clients.bybit_client import BybitClient
    from clients.okx_client import OKXClient
    from base_downloader import BaseDownloader


class CEXSpotDataDownloader(BaseDownloader):
    """
    CEX spot data downloader for ETH/USDT from multiple exchanges.
    
    Features:
    - Multi-exchange ETH/USDT data
    - Exchange-specific start dates (Binance from 2020 for risk history)
    - Hourly OHLCV data
    - Parallel downloads
    """
    
    def __init__(self, output_dir: str = "data/market_data/spot_prices/eth_usd", asset: str = "ETH"):
        super().__init__("cex_spot_data", output_dir)
        self.asset = asset.upper()  # ETH or BTC
        
        # Exchange-specific start dates
        self.exchange_start_dates = {
            "binance_spot": "2020-01-01",    # Risk management history
            "bybit": "2024-01-01",           # Recent data only
            "okx": "2024-01-01",             # Recent data only  
        }
        
        self.clients = {}
        self.failed_initializations = []
        
        # Initialize exchange clients
        try:
            self.clients['binance_spot'] = BinanceSpotClient(str(Path(output_dir).parent))
            self.logger.info("✅ Binance Spot client initialized")
        except Exception as e:
            self.logger.error(f"❌ Binance Spot client failed: {e}")
            self.failed_initializations.append(('binance_spot', str(e)))
        
        try:
            # Initialize Bybit client for spot data - use spot_prices directory
            self.clients['bybit'] = BybitClient(str(Path(output_dir).parent))
            self.logger.info("✅ Bybit client initialized")
        except Exception as e:
            self.logger.error(f"❌ Bybit client failed: {e}")
            self.failed_initializations.append(('bybit', str(e)))
        
        try:
            self.clients['okx'] = OKXClient(str(Path(output_dir).parent.parent / "derivatives"))
            self.logger.info("✅ OKX client initialized")
        except Exception as e:
            self.logger.error(f"❌ OKX client failed: {e}")
            self.failed_initializations.append(('okx', str(e)))
        
        if not self.clients:
            raise RuntimeError("No exchange clients could be initialized")
        
        self.logger.info(f"CEX spot downloader initialized with {len(self.clients)} exchanges")
        
        if self.failed_initializations:
            self.logger.warning(f"Failed to initialize {len(self.failed_initializations)} clients:")
            for name, error in self.failed_initializations:
                self.logger.warning(f"  - {name}: {error}")
    
    def _enforce_exchange_start_dates(self, start_date: str) -> Dict[str, str]:
        """
        Enforce exchange-specific start dates.
        
        Args:
            start_date: Requested start date
            
        Returns:
            Dict of actual start dates to use for each exchange
        """
        actual_dates = {}
        
        for exchange, min_date in self.exchange_start_dates.items():
            if start_date < min_date:
                actual_dates[exchange] = min_date
                self.logger.info(f"📅 {exchange}: Using minimum date {min_date} (requested {start_date})")
            else:
                actual_dates[exchange] = start_date
                self.logger.info(f"📅 {exchange}: Using requested date {start_date}")
        
        return actual_dates
    
    async def download_exchange_data(self, exchange: str, start_date: str, end_date: str) -> Dict:
        """
        Download {asset}/USDT data from a specific exchange.
        
        Args:
            exchange: Exchange name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Download result dictionary
        """
        if exchange not in self.clients:
            return {
                'success': False,
                'exchange': exchange,
                'error': f'Client not available for {exchange}',
                'record_count': 0
            }
        
        # Determine symbol based on asset
        if self.asset == "BTC":
            symbol = "BTCUSDT"
            base_asset = "BTC"
            okx_symbol = "BTC-USDT-SWAP"
        else:  # ETH (default)
            symbol = "ETHUSDT"
            base_asset = "ETH"
            okx_symbol = "ETH-USDT-SWAP"
        
        self.logger.info(f"🚀 Downloading {symbol} from {exchange}")
        
        try:
            client = self.clients[exchange]
            
            if exchange == "binance_spot":
                # Use Binance spot client
                result = await client.download_spot_ohlcv(symbol, base_asset, start_date, end_date)
            elif exchange == "bybit":
                # Use Bybit spot client for actual spot data
                result = await client.download_spot_ohlcv(symbol, start_date, end_date)
            elif exchange == "okx":
                # Use OKX for spot-like data
                result = await client.download_futures_ohlcv(okx_symbol, start_date, end_date)
            else:
                raise ValueError(f"Unknown exchange: {exchange}")
            
            # Add exchange metadata
            if result.get('success'):
                result['exchange'] = exchange
                result['data_type'] = 'spot_equivalent'
                self.logger.info(f"✅ {exchange}: {result['record_count']} records")
            else:
                self.logger.error(f"❌ {exchange}: Download failed")
                result['exchange'] = exchange
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ {exchange}: Unexpected error - {e}")
            return {
                'success': False,
                'exchange': exchange,
                'error': str(e),
                'record_count': 0
            }
    
    async def download_data(self, start_date: str, end_date: str, exchanges: List[str] = None) -> Dict:
        """
        Download ETH/USDT spot data from all or specified exchanges.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            exchanges: List of exchanges to download from (None for all)
            
        Returns:
            Combined download results
        """
        self.logger.info("🚀 Starting CEX spot data download")
        self.logger.info(f"📅 Requested date range: {start_date} to {end_date}")
        
        # Determine which exchanges to use
        if exchanges is None:
            exchanges = list(self.clients.keys())
        
        # Filter to only available exchanges
        available_exchanges = [ex for ex in exchanges if ex in self.clients]
        if not available_exchanges:
            raise RuntimeError("No available exchanges for download")
        
        self.logger.info(f"🎯 Exchanges: {', '.join(available_exchanges)}")
        
        # Enforce exchange-specific start dates
        actual_dates = self._enforce_exchange_start_dates(start_date)
        
        download_results = []
        
        # Download from each exchange
        for exchange in available_exchanges:
            exchange_start = actual_dates.get(exchange, start_date)
            result = await self.download_exchange_data(exchange, exchange_start, end_date)
            download_results.append(result)
        
        # Create summary report
        successful = sum(1 for r in download_results if r.get('success', False))
        total_records = sum(r.get('record_count', 0) for r in download_results)
        
        combined_report = {
            'timestamp': datetime.now().isoformat(),
            'downloader': 'cex_spot_data',
            'date_range': f"{start_date} to {end_date}",
            'enforced_dates': actual_dates,
            'exchanges_requested': exchanges or list(self.clients.keys()),
            'exchanges_available': available_exchanges,
            'total_downloads': len(download_results),
            'successful_downloads': successful,
            'failed_downloads': len(download_results) - successful,
            'total_records': total_records,
            'downloads': download_results
        }
        
        # Save report
        report_file = self.save_report(
            combined_report, 
            f"cex_spot_data_report_{start_date}_{end_date}.json"
        )
        
        # Log summary
        self.logger.info("=" * 70)
        self.logger.info("🎯 CEX SPOT DATA DOWNLOAD COMPLETE!")
        self.logger.info("=" * 70)
        self.logger.info(f"✅ Successful downloads: {successful}/{len(download_results)}")
        self.logger.info(f"📊 Total records: {total_records:,}")
        self.logger.info(f"💾 Output directory: {self.output_dir}")
        self.logger.info(f"📋 Report saved: {report_file}")
        
        # Show enforced dates
        for exchange, date in actual_dates.items():
            if exchange in available_exchanges:
                self.logger.info(f"📅 {exchange}: Used {date}")
        
        self.logger.info("=" * 70)
        
        return combined_report


async def main():
    """
    Main execution function for standalone script usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Download {asset}/USDT spot data from multiple CEX")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=str, default="data/market_data/spot_prices/eth_usd", help="Output directory")
    parser.add_argument("--exchange", type=str, choices=["binance_spot", "bybit", "okx"], help="Specific exchange to download")
    parser.add_argument("--asset", type=str, default="ETH", choices=["ETH", "BTC"], help="Asset to download (ETH or BTC)")
    parser.add_argument("--quick-test", action="store_true", help="Run with last 2 hours for testing")
    
    args = parser.parse_args()
    
    # Update output directory based on asset
    if args.asset == "BTC":
        args.output_dir = args.output_dir.replace("eth_usd", "btc_usd")
    
    try:
        downloader = CEXSpotDataDownloader(args.output_dir, args.asset)
        
        # Use provided dates, config defaults, or quick test
        if args.quick_test:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
            print(f"🚀 Quick test mode: {start_date} to {end_date}")
        else:
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
        
        # Determine exchanges to use
        exchanges = [args.exchange] if args.exchange else None
        
        print(f"🎯 Downloading {args.asset}/USDT spot data from CEX...")
        print(f"📊 Exchanges: {'All available' if not exchanges else exchanges[0]}")
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"💾 Output: {args.output_dir}")
        print(f"🔧 Exchange-specific start dates will be enforced:")
        print(f"   Binance Spot: 2020-01-01 (risk management history)")
        print(f"   Others: 2024-01-01")
        
        # Run download
        result = await downloader.download_data(start_date, end_date, exchanges)
        
        # Print summary
        if result['successful_downloads'] > 0:
            print(f"\n🎉 SUCCESS! Downloaded {result['total_records']:,} ETH/USDT records")
            print(f"✅ Exchanges: {result['successful_downloads']}/{result['total_downloads']}")
            print(f"📁 Files saved to: {args.output_dir}")
            
            # Show enforced dates
            enforced = result.get('enforced_dates', {})
            for exchange, date in enforced.items():
                if exchange in result.get('exchanges_available', []):
                    print(f"   📅 {exchange}: Started from {date}")
        else:
            print(f"\n❌ FAILED! No ETH/USDT data was downloaded successfully")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
