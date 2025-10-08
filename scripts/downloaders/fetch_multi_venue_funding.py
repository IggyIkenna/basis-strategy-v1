"""Multi-Venue Funding Rate Downloader

Downloads funding rate data from multiple exchanges (Bybit, OKX, Binance)
to support the enhanced multi-venue basis trading allocation logic.
"""

import asyncio
import ccxt
import pandas as pd
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class MultiVenueFundingDownloader:
    """Download funding rates from multiple exchanges for basis trading allocation."""
    
    def __init__(self, output_dir: str = "data/market_data/derivatives/funding_rates"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize exchange clients
        self.exchanges = {
            'bybit': ccxt.bybit({'sandbox': False}),
            'okx': ccxt.okx({'sandbox': False}),
            'binance': ccxt.binanceusdm({'sandbox': False})
        }
        
        # Funding symbols for each exchange
        self.symbols = {
            'bybit': ['ETH/USDT:USDT'],
            'okx': ['ETH/USDT:USDT'],
            'binance': ['ETH/USDT:USDT']
        }
        
        logger.info("MultiVenueFundingDownloader initialized")
    
    async def download_all_funding_rates(self, start_date: str = "2024-01-01", end_date: str = None):
        """Download funding rates from all supported exchanges."""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Downloading funding rates: {start_date} to {end_date}")
        
        all_results = {}
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                logger.info(f"Processing {exchange_name.upper()}...")
                
                # Load markets
                await self._load_markets_async(exchange)
                
                # Download funding rates
                exchange_results = await self._download_exchange_funding(
                    exchange, exchange_name, start_date, end_date
                )
                
                if exchange_results:
                    all_results[exchange_name] = exchange_results
                    logger.info(f"✅ {exchange_name.upper()}: {len(exchange_results)} records")
                else:
                    logger.warning(f"❌ {exchange_name.upper()}: No data retrieved")
                    
            except Exception as e:
                logger.error(f"Error downloading from {exchange_name}: {e}")
                continue
        
        # Save combined results
        await self._save_combined_results(all_results)
        
        return all_results
    
    async def _load_markets_async(self, exchange):
        """Load exchange markets asynchronously."""
        try:
            if hasattr(exchange, 'load_markets'):
                exchange.load_markets()
                logger.debug(f"Markets loaded for {exchange.id}")
        except Exception as e:
            logger.warning(f"Failed to load markets for {exchange.id}: {e}")
    
    async def _download_exchange_funding(
        self, 
        exchange, 
        exchange_name: str, 
        start_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Download funding rates from a specific exchange."""
        results = []
        
        symbols = self.symbols.get(exchange_name, [])
        
        for symbol in symbols:
            try:
                logger.info(f"  Downloading {symbol} from {exchange_name}")
                
                # Get funding rate history
                if hasattr(exchange, 'fetch_funding_rate_history'):
                    start_ts = int(datetime.fromisoformat(start_date).timestamp() * 1000)
                    end_ts = int(datetime.fromisoformat(end_date).timestamp() * 1000)
                    
                    funding_history = exchange.fetch_funding_rate_history(
                        symbol, since=start_ts, limit=1000
                    )
                    
                    for rate_data in funding_history:
                        if rate_data['timestamp'] <= end_ts:
                            results.append({
                                'exchange': exchange_name,
                                'symbol': symbol,
                                'timestamp': datetime.fromtimestamp(rate_data['timestamp'] / 1000),
                                'funding_rate': rate_data['fundingRate'],
                                'funding_rate_8h': rate_data['fundingRate'],
                                'funding_rate_apr': rate_data['fundingRate'] * 3 * 365.25,
                                'raw_data': rate_data
                            })
                
                elif hasattr(exchange, 'fetch_funding_rates'):
                    # Fallback to current funding rates
                    current_rates = exchange.fetch_funding_rates([symbol])
                    if symbol in current_rates:
                        rate_data = current_rates[symbol]
                        results.append({
                            'exchange': exchange_name,
                            'symbol': symbol,
                            'timestamp': datetime.now(),
                            'funding_rate': rate_data['fundingRate'],
                            'funding_rate_8h': rate_data['fundingRate'],
                            'funding_rate_apr': rate_data['fundingRate'] * 3 * 365.25,
                            'raw_data': rate_data
                        })
                
                logger.info(f"    Retrieved {len([r for r in results if r['exchange'] == exchange_name])} records")
                
            except Exception as e:
                logger.error(f"Error downloading {symbol} from {exchange_name}: {e}")
                continue
        
        return [r for r in results if r['exchange'] == exchange_name]
    
    async def _save_combined_results(self, all_results: Dict[str, List[Dict[str, Any]]]):
        """Save combined funding rate results."""
        try:
            # Combine all exchange data
            combined_data = []
            for exchange_name, exchange_results in all_results.items():
                combined_data.extend(exchange_results)
            
            if not combined_data:
                logger.warning("No funding rate data to save")
                return
            
            # Convert to DataFrame
            df = pd.DataFrame(combined_data)
            df = df.sort_values(['timestamp', 'exchange', 'symbol'])
            
            # Save combined file
            output_file = self.output_dir / "multi_venue_funding_rates.csv"
            df.to_csv(output_file, index=False)
            logger.info(f"Saved {len(df):,} combined funding records to {output_file}")
            
            # Save individual exchange files
            for exchange_name in all_results.keys():
                exchange_df = df[df['exchange'] == exchange_name]
                if not exchange_df.empty:
                    exchange_file = self.output_dir / f"{exchange_name}_funding_rates.csv"
                    exchange_df.to_csv(exchange_file, index=False)
                    logger.info(f"Saved {len(exchange_df):,} {exchange_name} records to {exchange_file}")
            
            # Generate summary
            self._generate_funding_summary(df)
            
        except Exception as e:
            logger.error(f"Error saving combined results: {e}")
    
    def _generate_funding_summary(self, df: pd.DataFrame):
        """Generate funding rate summary statistics."""
        try:
            summary = {
                "total_records": len(df),
                "exchanges": df['exchange'].nunique(),
                "symbols": df['symbol'].nunique(),
                "date_range": {
                    "start": df['timestamp'].min().isoformat(),
                    "end": df['timestamp'].max().isoformat()
                },
                "by_exchange": {}
            }
            
            for exchange in df['exchange'].unique():
                exchange_df = df[df['exchange'] == exchange]
                summary["by_exchange"][exchange] = {
                    "records": len(exchange_df),
                    "avg_funding_rate_8h": float(exchange_df['funding_rate_8h'].mean()),
                    "avg_funding_rate_apr": float(exchange_df['funding_rate_apr'].mean()),
                    "date_range": {
                        "start": exchange_df['timestamp'].min().isoformat(),
                        "end": exchange_df['timestamp'].max().isoformat()
                    }
                }
            
            # Save summary
            summary_file = self.output_dir / "funding_rates_summary.json"
            with open(summary_file, 'w') as f:
                import json
                json.dump(summary, f, indent=2)
            
            logger.info(f"Generated funding summary: {summary_file}")
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")


async def main():
    """Main function to download multi-venue funding rates."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download multi-venue funding rates")
    parser.add_argument("--start-date", type=str, default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--quick-test", action="store_true", help="Run with last 3 days for testing")
    
    args = parser.parse_args()
    
    downloader = MultiVenueFundingDownloader()
    
    # Use provided dates or quick test
    if args.quick_test:
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        print(f"🚀 Quick test mode: {start_date} to {end_date}")
    else:
        start_date = args.start_date
        end_date = args.end_date
    
    # Download funding rate history
    await downloader.download_all_funding_rates(start_date, end_date)


if __name__ == "__main__":
    asyncio.run(main())
