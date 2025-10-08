#!/usr/bin/env python3
"""
OKX Funding Rates Downloader

Downloads OKX funding rates by processing zip files from the data download page.
This replaces the API-based approach since the OKX API doesn't support historical funding rates.

Usage:
    python fetch_okx_funding_rates.py --start-date 2024-01-01 --end-date 2025-09-18
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from .base_downloader import BaseDownloader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OKXFundingRatesDownloader(BaseDownloader):
    """Downloader for OKX funding rates via zip file processing."""
    
    def __init__(self, output_dir: str = "data/market_data/derivatives/funding_rates"):
        super().__init__(
            name="OKX Funding Rates (Zip Processing)",
            output_dir=output_dir,
            rate_limit_per_minute=10  # Very low since we're processing files, not making API calls
        )
        
        # Paths
        self.zip_data_dir = Path("data/manual_sources/okx.com:data-download")
        self.processed_data_dir = Path("data/market_data/okx")
        
        # Supported instruments
        self.supported_instruments = ['ETHUSDT', 'BTCUSDT']
        
        # Exchange start dates (when OKX started offering these instruments)
        self.exchange_start_dates = {
            'ETHUSDT': '2020-01-01',  # OKX has had ETH-USDT for a long time
            'BTCUSDT': '2020-01-01'   # OKX has had BTC-USDT for a long time
        }
    
    def _enforce_exchange_start_dates(self, start_date: str) -> Dict[str, str]:
        """Enforce exchange-specific start dates."""
        adjusted_dates = {}
        
        for instrument in self.supported_instruments:
            exchange_start = self.exchange_start_dates[instrument]
            
            if start_date < exchange_start:
                logger.warning(f"Requested start date {start_date} is before {instrument} start date {exchange_start}")
                adjusted_dates[instrument] = exchange_start
            else:
                adjusted_dates[instrument] = start_date
        
        return adjusted_dates
    
    async def download_instrument_funding_rates(self, instrument: str, start_date: str, end_date: str) -> Dict:
        """Download funding rates for a specific instrument."""
        logger.info(f"📊 Downloading {instrument} funding rates from {start_date} to {end_date}")
        
        # Check if we have zip files available
        if not self.zip_data_dir.exists():
            logger.error(f"OKX zip data directory not found: {self.zip_data_dir}")
            logger.info("Please download OKX data zip files from https://www.okx.com/data-download")
            logger.info("and place them in the data/manual_sources/okx.com:data-download directory")
            return {
                'instrument': instrument,
                'success': False,
                'error': 'Zip data directory not found',
                'records': 0
            }
        
        # Check if we have processed data available
        processed_file = self.processed_data_dir / "funding_rates" / "okx_funding_rates_daily.csv"
        
        if not processed_file.exists():
            logger.warning(f"Processed OKX data not found: {processed_file}")
            logger.info("Please run the OKX data processor first:")
            logger.info("python scripts/processors/okx_data_processor.py")
            return {
                'instrument': instrument,
                'success': False,
                'error': 'Processed data not found',
                'records': 0
            }
        
        # Load processed data
        logger.info(f"Loading processed OKX data from {processed_file}")
        df = pd.read_csv(processed_file)
        
        # Convert timestamps
        df['funding_time'] = pd.to_datetime(df['funding_time'])
        df['date'] = pd.to_datetime(df['date'])
        
        # Map instrument names
        instrument_mapping = {
            'ETHUSDT': 'ETH-USDT-SWAP',
            'BTCUSDT': 'BTC-USDT-SWAP'
        }
        
        okx_instrument = instrument_mapping.get(instrument)
        if not okx_instrument:
            logger.error(f"Unsupported instrument: {instrument}")
            return {
                'instrument': instrument,
                'success': False,
                'error': f'Unsupported instrument: {instrument}',
                'records': 0
            }
        
        # Filter for the specific instrument
        instrument_data = df[df['instrument'] == okx_instrument].copy()
        
        if instrument_data.empty:
            logger.warning(f"No data found for {instrument} ({okx_instrument})")
            return {
                'instrument': instrument,
                'success': False,
                'error': f'No data found for {instrument}',
                'records': 0
            }
        
        # Filter by date range
        # Convert date column to datetime if it's not already
        if instrument_data['date'].dtype == 'object':
            instrument_data['date'] = pd.to_datetime(instrument_data['date'])
        
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        # Filter data within the requested date range
        date_filter = (instrument_data['date'] >= start_dt) & (instrument_data['date'] <= end_dt)
        filtered_data = instrument_data[date_filter].copy()
        
        if filtered_data.empty:
            logger.warning(f"No data found for {instrument} in date range {start_date} to {end_date}")
            return {
                'instrument': instrument,
                'success': False,
                'error': f'No data in date range {start_date} to {end_date}',
                'records': 0
            }
        
        # Convert to standard format
        output_data = []
        
        for _, row in filtered_data.iterrows():
            # Format timestamp to match existing format (ISO format with Z)
            funding_timestamp = row['funding_time'].strftime('%Y-%m-%dT%H:%M:%SZ')
            
            output_data.append({
                'funding_timestamp': funding_timestamp,
                'funding_rate': row['funding_rate'],
                'symbol': instrument,
                'source': 'okx'
            })
        
        # Create output DataFrame
        output_df = pd.DataFrame(output_data)
        output_df = output_df.sort_values('funding_timestamp')
        
        # Save to file with actual data range
        actual_start = output_df['funding_timestamp'].min()[:10]  # Get YYYY-MM-DD part
        actual_end = output_df['funding_timestamp'].max()[:10]    # Get YYYY-MM-DD part
        filename = f"okx_{instrument}_funding_rates_{actual_start}_{actual_end}.csv"
        filepath = self.save_to_csv(output_df.to_dict('records'), filename)
        
        logger.info(f"✅ Saved {len(output_df)} {instrument} funding rates to {filepath}")
        
        # Show sample data
        if not output_df.empty:
            logger.info(f"Sample {instrument} funding rates:")
            for _, row in output_df.head(3).iterrows():
                logger.info(f"  {row['funding_timestamp']} | {row['funding_rate']:.6f}")
        
        return {
            'instrument': instrument,
            'success': True,
            'records': len(output_df),
            'filepath': str(filepath),
            'date_range': f"{start_date} to {end_date}",
            'sample_data': output_df.head(3).to_dict('records') if not output_df.empty else []
        }
    
    async def download_data(self, start_date: str, end_date: str, instruments: List[str] = None) -> Dict:
        """Download funding rates for all supported instruments."""
        logger.info(f"🚀 Starting OKX funding rates download from {start_date} to {end_date}")
        
        # Use all supported instruments if none specified
        if instruments is None:
            instruments = self.supported_instruments
        
        # Filter to only supported instruments
        instruments = [inst for inst in instruments if inst in self.supported_instruments]
        
        if not instruments:
            logger.error("No supported instruments specified")
            return {
                'success': False,
                'error': 'No supported instruments',
                'downloads': []
            }
        
        # Enforce exchange start dates
        adjusted_dates = self._enforce_exchange_start_dates(start_date)
        
        # Download data for each instrument
        downloads = []
        total_records = 0
        
        for instrument in instruments:
            adjusted_start = adjusted_dates[instrument]
            
            try:
                result = await self.download_instrument_funding_rates(instrument, adjusted_start, end_date)
                downloads.append(result)
                
                if result['success']:
                    total_records += result['records']
                
            except Exception as e:
                logger.error(f"Error downloading {instrument}: {e}")
                downloads.append({
                    'instrument': instrument,
                    'success': False,
                    'error': str(e),
                    'records': 0
                })
        
        # Create summary report
        successful_downloads = [d for d in downloads if d['success']]
        failed_downloads = [d for d in downloads if not d['success']]
        
        summary = {
            'success': len(successful_downloads) > 0,
            'total_downloads': len(downloads),
            'successful_downloads': len(successful_downloads),
            'failed_downloads': len(failed_downloads),
            'total_records': total_records,
            'date_range': f"{start_date} to {end_date}",
            'downloads': downloads
        }
        
        # Log summary
        logger.info(f"\n📊 OKX Funding Rates Download Summary:")
        logger.info(f"   Total downloads: {len(downloads)}")
        logger.info(f"   Successful: {len(successful_downloads)}")
        logger.info(f"   Failed: {len(failed_downloads)}")
        logger.info(f"   Total records: {total_records:,}")
        
        if successful_downloads:
            logger.info(f"   ✅ Successful instruments:")
            for download in successful_downloads:
                logger.info(f"      {download['instrument']}: {download['records']:,} records")
        
        if failed_downloads:
            logger.info(f"   ❌ Failed instruments:")
            for download in failed_downloads:
                logger.info(f"      {download['instrument']}: {download['error']}")
        
        return summary


async def main():
    """Main execution function for standalone script usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download OKX funding rates")
    parser.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=str, default="data/market_data/derivatives/funding_rates", help="Output directory")
    parser.add_argument("--instruments", type=str, help="Comma-separated list of instruments (e.g., 'ETHUSDT,BTCUSDT')")
    
    args = parser.parse_args()
    
    # Parse instruments
    instruments = None
    if args.instruments:
        instruments = [inst.strip().upper() for inst in args.instruments.split(',')]
    
    # Create downloader
    downloader = OKXFundingRatesDownloader(args.output_dir)
    
    # Download data
    result = await downloader.download_data(args.start_date, args.end_date, instruments)
    
    # Save report
    report_file = downloader.save_report(result, "okx_funding_rates_download_report.json")
    logger.info(f"📄 Download report saved to: {report_file}")
    
    return result


if __name__ == "__main__":
    asyncio.run(main())
