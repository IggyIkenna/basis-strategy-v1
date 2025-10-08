"""
CEX Funding Rates Downloader

Downloads funding rate data from multiple exchanges:
- Bybit (ETHUSDT perp, since 2024-01-01)
- OKX (ETH-USDT-SWAP, since 2024-01-01) 
- Binance Futures (ETHUSDT perp, since 2024-01-01)

Features:
- Multi-exchange funding rate data
- Enforced exchange-specific start dates
- 8-hour funding rate intervals
- Organized output to derivatives/funding_rates directory
- Basis trading support
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Add the backend source to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "backend" / "src"))

# Handle both standalone and module imports
try:
    from .clients.bybit_client import BybitClient
    from .clients.okx_client import OKXClient
    from .clients.binance_futures_client import BinanceFuturesClient
    from .base_downloader import BaseDownloader
except ImportError:
    # Standalone execution
    sys.path.append(str(Path(__file__).parent))
    from clients.bybit_client import BybitClient
    from clients.okx_client import OKXClient
    from clients.binance_futures_client import BinanceFuturesClient
    from base_downloader import BaseDownloader


class CEXFundingRatesDownloader(BaseDownloader):
    """
    CEX funding rates downloader for perpetual futures funding rates.

    Features:
    - Multi-exchange ETH-USDT perpetuals funding rates
    - 8-hour funding rate intervals
    - Enforced exchange-specific start dates
    - Parallelizable per-exchange orchestration
    """

    def __init__(self, output_dir: str = "data/market_data/derivatives/funding_rates", asset: str = "ETH"):
        super().__init__("cex_funding_rates", output_dir)
        self.asset = asset.upper()  # ETH or BTC

        # Exchange-specific minimum start dates
        # Note: OKX removed - using zip processing approach instead of API
        self.exchange_start_dates: Dict[str, str] = {
            "bybit": "2024-01-01",
            "binance_futures": "2024-01-01",
        }

        # Funding rate symbols per exchange - determined by asset
        # Note: OKX removed - using zip processing approach instead of API
        if self.asset == "BTC":
            self.exchange_symbols: Dict[str, str] = {
                "bybit": "BTCUSDT",            # perp
                "binance_futures": "BTCUSDT",  # perp
            }
        else:  # ETH (default)
            self.exchange_symbols: Dict[str, str] = {
                "bybit": "ETHUSDT",            # perp
                "binance_futures": "ETHUSDT",  # perp
            }

        self.clients: Dict[str, object] = {}
        self.failed_initializations: List = []

        # Initialize exchange clients
        try:
            self.clients['bybit'] = BybitClient(str(Path(output_dir).parent))
            self.logger.info("✅ Bybit client initialized")
        except Exception as e:
            self.logger.error(f"❌ Bybit client failed: {e}")
            self.failed_initializations.append(('bybit', str(e)))

        # OKX client removed - using zip processing approach instead of API
        # Note: OKX funding rates will be handled separately via zip file processing

        try:
            self.clients['binance_futures'] = BinanceFuturesClient(str(Path(output_dir).parent))
            self.logger.info("✅ Binance Futures client initialized")
        except Exception as e:
            self.logger.error(f"❌ Binance Futures client failed: {e}")
            self.failed_initializations.append(('binance_futures', str(e)))

        if not self.clients:
            raise RuntimeError("No funding rate exchange clients could be initialized")

        self.logger.info(f"CEX funding rates downloader initialized with {len(self.clients)} exchanges")

        if self.failed_initializations:
            self.logger.warning(f"Failed to initialize {len(self.failed_initializations)} clients:")
            for name, error in self.failed_initializations:
                self.logger.warning(f"  - {name}: {error}")

    def _enforce_exchange_start_dates(self, start_date: str) -> Dict[str, str]:
        """
        Enforce exchange-specific minimum start dates.

        Args:
            start_date: Requested start date (YYYY-MM-DD)

        Returns:
            Dict of actual start dates to use for each exchange
        """
        actual_dates: Dict[str, str] = {}
        for exchange, min_date in self.exchange_start_dates.items():
            if start_date < min_date:
                actual_dates[exchange] = min_date
                self.logger.info(f"📅 {exchange}: Using minimum date {min_date} (requested {start_date})")
            else:
                actual_dates[exchange] = start_date
                self.logger.info(f"📅 {exchange}: Using requested date {start_date}")
        return actual_dates

    async def download_exchange_funding_rates(self, exchange: str, start_date: str, end_date: str) -> Dict:
        """
        Download funding rates from a specific exchange.

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

        self.logger.info(f"🚀 Downloading funding rates from {exchange}")

        try:
            client = self.clients[exchange]
            symbol = self.exchange_symbols.get(exchange)
            if not symbol:
                raise ValueError(f"No symbol configured for {exchange}")

            # All funding rate clients expose download_funding_rates
            result = await client.download_funding_rates(symbol, start_date, end_date)

            # Add exchange metadata
            result['exchange'] = exchange
            result['symbol_used'] = symbol
            result['data_type'] = 'funding_rates'
            if result.get('success'):
                self.logger.info(f"✅ {exchange}: {result.get('record_count', 0)} funding rate records")
            else:
                self.logger.error(f"❌ {exchange}: Funding rates download failed")

            return result

        except Exception as e:
            self.logger.error(f"❌ {exchange}: Unexpected error - {e}")
            return {
                'success': False,
                'exchange': exchange,
                'symbol_used': self.exchange_symbols.get(exchange),
                'error': str(e),
                'record_count': 0
            }

    async def download_data(self, start_date: str, end_date: str, exchanges: List[str] = None) -> Dict:
        """
        Download funding rates from all or specified exchanges.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            exchanges: List of exchanges to download from (None for all)

        Returns:
            Combined download results
        """
        self.logger.info("🚀 Starting CEX funding rates download")
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

        # Sequential per-exchange loop (aligns with other CEX script structure)
        for exchange in available_exchanges:
            exchange_start = actual_dates.get(exchange, start_date)
            result = await self.download_exchange_funding_rates(exchange, exchange_start, end_date)
            download_results.append(result)

        # Create summary report
        successful = sum(1 for r in download_results if r.get('success', False))
        total_records = sum(r.get('record_count', 0) for r in download_results)

        combined_report = {
            'timestamp': datetime.now().isoformat(),
            'downloader': 'cex_funding_rates',
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

        # Save report (filename pattern aligned to other CEX scripts)
        report_file = self.save_report(
            combined_report,
            f"cex_funding_rates_report_{start_date}_{end_date}.json"
        )

        # Log summary
        self.logger.info("=" * 70)
        self.logger.info("🎯 CEX FUNDING RATES DOWNLOAD COMPLETE!")
        self.logger.info("=" * 70)
        self.logger.info(f"✅ Successful downloads: {successful}/{len(download_results)}")
        self.logger.info(f"📊 Total funding rate records: {total_records:,}")
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

    parser = argparse.ArgumentParser(description="Download funding rates from multiple CEX")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=str, default="data/market_data/derivatives/funding_rates", help="Output directory")
    parser.add_argument("--exchange", type=str, choices=["bybit", "okx", "binance_futures"], help="Specific exchange to download")
    parser.add_argument("--asset", type=str, default="ETH", choices=["ETH", "BTC"], help="Asset to download (ETH or BTC)")
    parser.add_argument("--quick-test", action="store_true", help="Run with last 3 days for testing")

    args = parser.parse_args()

    try:
        downloader = CEXFundingRatesDownloader(args.output_dir, args.asset)

        # Use provided dates, config defaults, or quick test
        if args.quick_test:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
            print(f"🚀 Quick test mode: {start_date} to {end_date}")
        else:
            if args.start_date:
                start_date = args.start_date
            else:
                start_date = downloader.get_date_range()
                print(f"Using config start date defaults: {start_date}")
            if args.end_date:
                end_date = args.end_date
            else:
                end_date = datetime.now().strftime('%Y-%m-%d')
                print(f"Using current date as end date: {end_date}")

        # Determine exchanges to use
        exchanges = [args.exchange] if args.exchange else None

        print(f"🎯 Downloading {args.asset} funding rates from CEX...")
        print(f"📊 Exchanges: {'All available' if not exchanges else exchanges[0]}")
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"💾 Output: {args.output_dir}")
        print(f"🔧 Exchange-specific start dates will be enforced:")
        for ex, dt in downloader.exchange_start_dates.items():
            print(f"   {ex}: {dt}")

        # Run download
        result = await downloader.download_data(start_date, end_date, exchanges)

        # Print summary
        if result['successful_downloads'] > 0:
            print(f"\n🎉 SUCCESS! Downloaded {result['total_records']:,} funding rate records")
            print(f"✅ Exchanges: {result['successful_downloads']}/{result['total_downloads']}")
            print(f"📁 Files saved to: {args.output_dir}")

            # Show enforced dates
            enforced = result.get('enforced_dates', {})
            for exchange, date in enforced.items():
                if exchange in result.get('exchanges_available', []):
                    print(f"   📅 {exchange}: Started from {date}")
        else:
            print(f"\n❌ FAILED! No funding rate data was downloaded successfully")
            return 1

        return 0

    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))

