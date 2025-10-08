#!/usr/bin/env python3
"""
OKX Data Processor - Unified Script

This script merges the functionality of:
- okx_data_parser.py (parse zip files)
- okx_data_summary.py (show data summary)
- extract_okx_eth_btc_funding.py (extract specific instruments)

It processes OKX daily data zip files downloaded from okx.com/data-download
and extracts funding rates for ETH-USDT and BTC-USDT instruments.

Usage:
    python okx_data_processor.py --data-dir data/manual_sources/okx.com:data-download --output-dir data/market_data/okx
    python okx_data_processor.py --summary-only --data-dir data
"""

import argparse
import logging
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OKXDataProcessor:
    """Unified processor for OKX daily data zip files."""
    
    def __init__(self, data_dir: Path, output_dir: Path):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Data type configurations
        self.data_types = {
            'allswaprate-swaprate': {
                'name': 'funding_rates',
                'description': 'Perpetual swap funding rates',
                'output_subdir': 'funding_rates',
                'columns': {
                    'instrument_name/交易币对名': 'instrument',
                    'contract_type/合约类型': 'contract_type', 
                    'funding_rate/预测下一周期费率': 'funding_rate',
                    'real_funding_rate/本周期真实费率': 'real_funding_rate',
                    'funding_time/下一周期时间戳': 'funding_time'
                }
            }
        }
    
    def extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """Extract date from OKX filename pattern.
        
        Examples:
            allswaprate-swaprate-2024-05-01.zip -> 2024-05-01
            futures-ohlcv-2024-06-15.zip -> 2024-06-15
        """
        # Pattern: any-text-YYYY-MM-DD.zip
        pattern = r'(\d{4}-\d{2}-\d{2})\.zip$'
        match = re.search(pattern, filename)
        
        if match:
            try:
                return datetime.strptime(match.group(1), '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid date format in filename: {filename}")
                return None
        
        logger.warning(f"No date found in filename: {filename}")
        return None
    
    def identify_data_type(self, filename: str) -> Optional[str]:
        """Identify the data type from filename."""
        for data_type in self.data_types.keys():
            if data_type in filename:
                return data_type
        
        logger.warning(f"Unknown data type in filename: {filename}")
        return None
    
    def parse_swap_rate_file(self, csv_path: Path, date: datetime) -> pd.DataFrame:
        """Parse swap rate CSV file."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'gbk', 'gb2312', 'latin1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    logger.debug(f"Successfully read {csv_path} with encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                logger.error(f"Could not read {csv_path} with any encoding")
                return pd.DataFrame()
            
            # Rename columns to English
            column_mapping = self.data_types['allswaprate-swaprate']['columns']
            df = df.rename(columns=column_mapping)
            
            # Convert funding_time from milliseconds to datetime
            df['funding_time'] = pd.to_datetime(df['funding_time'], unit='ms', utc=True)
            
            # Add date column
            df['date'] = date.date()
            
            # Convert funding rates to float
            df['funding_rate'] = pd.to_numeric(df['funding_rate'], errors='coerce')
            df['real_funding_rate'] = pd.to_numeric(df['real_funding_rate'], errors='coerce')
            
            # Filter out rows with invalid data
            df = df.dropna(subset=['funding_rate', 'real_funding_rate'])
            
            logger.info(f"Parsed {len(df)} funding rate records for {date.date()}")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing {csv_path}: {e}")
            return pd.DataFrame()
    
    def process_zip_file(self, zip_path: Path) -> Optional[pd.DataFrame]:
        """Process a single OKX zip file."""
        filename = zip_path.name
        logger.info(f"Processing {filename}")
        
        # Extract date and data type
        date = self.extract_date_from_filename(filename)
        data_type = self.identify_data_type(filename)
        
        if not date or not data_type:
            return None
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get the CSV file inside the zip
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                
                if not csv_files:
                    logger.warning(f"No CSV file found in {filename}")
                    return None
                
                if len(csv_files) > 1:
                    logger.warning(f"Multiple CSV files in {filename}, using first one")
                
                csv_filename = csv_files[0]
                
                # Extract and parse
                with zip_ref.open(csv_filename) as csv_file:
                    # Create temporary file path
                    temp_csv = self.data_dir / f"temp_{csv_filename}"
                    
                    # Write to temp file
                    with open(temp_csv, 'wb') as temp_file:
                        temp_file.write(csv_file.read())
                    
                    # Parse based on data type
                    if data_type == 'allswaprate-swaprate':
                        df = self.parse_swap_rate_file(temp_csv, date)
                    else:
                        logger.warning(f"No parser for data type: {data_type}")
                        df = pd.DataFrame()
                    
                    # Clean up temp file
                    temp_csv.unlink()
                    
                    return df
                    
        except Exception as e:
            logger.error(f"Error processing {zip_path}: {e}")
            return None
    
    def get_available_dates(self) -> Dict[str, List[datetime]]:
        """Get all available dates for each data type."""
        available_dates = {}
        
        for zip_file in self.data_dir.glob("*.zip"):
            date = self.extract_date_from_filename(zip_file.name)
            data_type = self.identify_data_type(zip_file.name)
            
            if date and data_type:
                if data_type not in available_dates:
                    available_dates[data_type] = []
                available_dates[data_type].append(date)
        
        # Sort dates for each data type
        for data_type in available_dates:
            available_dates[data_type].sort()
        
        return available_dates
    
    def process_all_files(self, data_type: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """Process all OKX zip files."""
        results = {}
        
        # Get available dates
        available_dates = self.get_available_dates()
        
        if data_type:
            if data_type not in available_dates:
                logger.error(f"Data type '{data_type}' not found in available files")
                return results
            data_types_to_process = [data_type]
        else:
            data_types_to_process = list(available_dates.keys())
        
        for dt in data_types_to_process:
            logger.info(f"Processing {len(available_dates[dt])} files for data type: {dt}")
            
            all_data = []
            
            for date in available_dates[dt]:
                # Find the zip file for this date and data type
                zip_files = list(self.data_dir.glob(f"*{dt}*{date.strftime('%Y-%m-%d')}.zip"))
                
                if not zip_files:
                    logger.warning(f"No zip file found for {dt} on {date.date()}")
                    continue
                
                if len(zip_files) > 1:
                    logger.warning(f"Multiple zip files found for {dt} on {date.date()}, using first one")
                
                df = self.process_zip_file(zip_files[0])
                if not df.empty:
                    all_data.append(df)
            
            if all_data:
                # Combine all data for this type
                combined_df = pd.concat(all_data, ignore_index=True)
                combined_df = combined_df.sort_values(['date', 'instrument'])
                
                # Save to output directory
                output_subdir = self.output_dir / self.data_types[dt]['output_subdir']
                output_subdir.mkdir(parents=True, exist_ok=True)
                
                # Save as CSV
                output_file = output_subdir / f"okx_{self.data_types[dt]['name']}_daily.csv"
                combined_df.to_csv(output_file, index=False)
                
                # Also save individual daily files for easier access
                daily_dir = output_subdir / "daily"
                daily_dir.mkdir(exist_ok=True)
                
                for date in available_dates[dt]:
                    daily_data = combined_df[combined_df['date'] == date.date()]
                    if not daily_data.empty:
                        daily_file = daily_dir / f"okx_{self.data_types[dt]['name']}_{date.strftime('%Y-%m-%d')}.csv"
                        daily_data.to_csv(daily_file, index=False)
                
                results[dt] = combined_df
                logger.info(f"Saved {len(combined_df)} records for {dt} to {output_file}")
        
        return results
    
    def extract_eth_btc_funding_rates(self, data_dir: Path) -> bool:
        """Extract ETH-USDT and BTC-USDT funding rates from processed data."""
        
        # Input file
        okx_file = data_dir / "market_data" / "okx" / "funding_rates" / "okx_funding_rates_daily.csv"
        
        if not okx_file.exists():
            logger.error(f"OKX funding rates file not found: {okx_file}")
            logger.info("Run the OKX processor first to parse zip files")
            return False
        
        logger.info(f"Loading OKX funding rates from {okx_file}")
        df = pd.read_csv(okx_file)
        
        # Convert timestamps
        df['funding_time'] = pd.to_datetime(df['funding_time'])
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter for ETH-USDT and BTC-USDT only
        target_instruments = ['ETH-USDT-SWAP', 'BTC-USDT-SWAP']
        filtered_df = df[df['instrument'].isin(target_instruments)].copy()
        
        if filtered_df.empty:
            logger.error("No ETH-USDT or BTC-USDT data found in OKX file")
            return False
        
        logger.info(f"Found {len(filtered_df)} records for ETH-USDT and BTC-USDT")
        
        # Convert to the standard format
        output_data = []
        
        for _, row in filtered_df.iterrows():
            # Map instrument names to symbols
            if row['instrument'] == 'ETH-USDT-SWAP':
                symbol = 'ETHUSDT'
            elif row['instrument'] == 'BTC-USDT-SWAP':
                symbol = 'BTCUSDT'
            else:
                continue
            
            # Format timestamp to match existing format (ISO format with Z)
            funding_timestamp = row['funding_time'].strftime('%Y-%m-%dT%H:%M:%SZ')
            
            output_data.append({
                'funding_timestamp': funding_timestamp,
                'funding_rate': row['funding_rate'],
                'symbol': symbol,
                'source': 'okx'
            })
        
        # Create output DataFrame
        output_df = pd.DataFrame(output_data)
        output_df = output_df.sort_values(['symbol', 'funding_timestamp'])
        
        # Get date range for filename
        start_date = output_df['funding_timestamp'].min()[:10]  # YYYY-MM-DD
        end_date = output_df['funding_timestamp'].max()[:10]    # YYYY-MM-DD
        
        # Create output directory
        output_dir = data_dir / "market_data" / "derivatives" / "funding_rates"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save ETH-USDT data
        eth_data = output_df[output_df['symbol'] == 'ETHUSDT'].copy()
        if not eth_data.empty:
            eth_file = output_dir / f"okx_ETHUSDT_funding_rates_{start_date}_{end_date}.csv"
            eth_data.to_csv(eth_file, index=False)
            logger.info(f"Saved {len(eth_data)} ETH-USDT funding rates to {eth_file}")
            
            # Show sample
            logger.info("ETH-USDT sample:")
            for _, row in eth_data.head(3).iterrows():
                logger.info(f"  {row['funding_timestamp']} | {row['funding_rate']:.6f}")
        
        # Save BTC-USDT data
        btc_data = output_df[output_df['symbol'] == 'BTCUSDT'].copy()
        if not btc_data.empty:
            btc_file = output_dir / f"okx_BTCUSDT_funding_rates_{start_date}_{end_date}.csv"
            btc_data.to_csv(btc_file, index=False)
            logger.info(f"Saved {len(btc_data)} BTC-USDT funding rates to {btc_file}")
            
            # Show sample
            logger.info("BTC-USDT sample:")
            for _, row in btc_data.head(3).iterrows():
                logger.info(f"  {row['funding_timestamp']} | {row['funding_rate']:.6f}")
        
        # Summary statistics
        logger.info("\n📊 SUMMARY:")
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"Total records: {len(output_df)}")
        logger.info(f"ETH-USDT records: {len(eth_data)}")
        logger.info(f"BTC-USDT records: {len(btc_data)}")
        
        if not eth_data.empty:
            logger.info(f"ETH-USDT funding rate range: {eth_data['funding_rate'].min():.6f} to {eth_data['funding_rate'].max():.6f}")
            logger.info(f"ETH-USDT average funding rate: {eth_data['funding_rate'].mean():.6f}")
        
        if not btc_data.empty:
            logger.info(f"BTC-USDT funding rate range: {btc_data['funding_rate'].min():.6f} to {btc_data['funding_rate'].max():.6f}")
            logger.info(f"BTC-USDT average funding rate: {btc_data['funding_rate'].mean():.6f}")
        
        return True
    
    def show_data_summary(self, data_dir: Path):
        """Show summary of available OKX data."""
        
        funding_rates_file = data_dir / "market_data" / "okx" / "funding_rates" / "okx_funding_rates_daily.csv"
        
        if not funding_rates_file.exists():
            print("❌ No OKX data found. Run the processor first:")
            print("   python scripts/processors/okx_data_processor.py")
            return
        
        print("📊 OKX DATA SUMMARY")
        print("=" * 50)
        
        # Load funding rates data
        df = pd.read_csv(funding_rates_file)
        df['funding_time'] = pd.to_datetime(df['funding_time'])
        df['date'] = pd.to_datetime(df['date'])
        
        print(f"📈 Funding Rates Data:")
        print(f"   Total records: {len(df):,}")
        print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"   Unique instruments: {df['instrument'].nunique()}")
        print(f"   Unique dates: {df['date'].nunique()}")
        
        # Show ETH-related instruments
        eth_instruments = df[df['instrument'].str.contains('ETH', case=False, na=False)]['instrument'].unique()
        print(f"\n🔍 ETH-related instruments ({len(eth_instruments)}):")
        for instrument in sorted(eth_instruments):
            print(f"   {instrument}")
        
        # Show sample data for ETH-USDT-SWAP
        eth_usdt_data = df[df['instrument'] == 'ETH-USDT-SWAP'].copy()
        if not eth_usdt_data.empty:
            print(f"\n📋 ETH-USDT-SWAP Sample (last 5 records):")
            sample = eth_usdt_data.tail().sort_values('funding_time')
            for _, row in sample.iterrows():
                print(f"   {row['funding_time'].strftime('%Y-%m-%d %H:%M')} | "
                      f"Funding: {row['funding_rate']:.6f} | "
                      f"Real: {row['real_funding_rate']:.6f}")
        
        # Show funding rate statistics
        print(f"\n📊 Funding Rate Statistics (all instruments):")
        print(f"   Average funding rate: {df['funding_rate'].mean():.6f}")
        print(f"   Median funding rate: {df['funding_rate'].median():.6f}")
        print(f"   Min funding rate: {df['funding_rate'].min():.6f}")
        print(f"   Max funding rate: {df['funding_rate'].max():.6f}")
        print(f"   Std dev: {df['funding_rate'].std():.6f}")
        
        # Show most recent data
        latest_date = df['date'].max()
        latest_data = df[df['date'] == latest_date]
        print(f"\n🕐 Latest data ({latest_date.date()}):")
        print(f"   Records: {len(latest_data)}")
        print(f"   Instruments: {latest_data['instrument'].nunique()}")
        
        # Show data availability by month
        print(f"\n📅 Data availability by month:")
        monthly_counts = df.groupby(df['date'].dt.to_period('M')).size()
        for month, count in monthly_counts.items():
            print(f"   {month}: {count:,} records")
    
    def print_summary(self):
        """Print summary of available data."""
        available_dates = self.get_available_dates()
        
        print("\n" + "="*80)
        print("OKX DATA SUMMARY")
        print("="*80)
        
        if not available_dates:
            print("No OKX data files found!")
            return
        
        for data_type, dates in available_dates.items():
            config = self.data_types[data_type]
            print(f"\n📊 {config['description']} ({data_type})")
            print(f"   Available dates: {len(dates)} days")
            if dates:
                print(f"   Date range: {dates[0].date()} to {dates[-1].date()}")
                print(f"   Latest: {dates[-1].date()}")
        
        print(f"\n📁 Data directory: {self.data_dir}")
        print(f"📁 Output directory: {self.output_dir}")
    
    def process_okx_data(self, data_dir: Path) -> bool:
        """Main processing function that handles the complete OKX data pipeline."""
        logger.info("🚀 Starting OKX data processing pipeline...")
        
        # Step 1: Process zip files
        logger.info("Step 1: Processing OKX zip files...")
        results = self.process_all_files()
        
        if not results:
            logger.error("No data processed from zip files")
            return False
        
        # Step 2: Extract ETH/BTC funding rates
        logger.info("Step 2: Extracting ETH-USDT and BTC-USDT funding rates...")
        success = self.extract_eth_btc_funding_rates(data_dir)
        
        if not success:
            logger.error("Failed to extract ETH/BTC funding rates")
            return False
        
        logger.info("✅ OKX data processing pipeline completed successfully!")
        return True


def main():
    parser = argparse.ArgumentParser(description="Unified OKX data processor")
    parser.add_argument("--data-dir", type=str, default="data/manual_sources/okx.com:data-download",
                       help="Directory containing OKX zip files")
    parser.add_argument("--output-dir", type=str, default="data/market_data/okx",
                       help="Output directory for processed data")
    parser.add_argument("--data-type", type=str, choices=['allswaprate-swaprate'],
                       help="Specific data type to process (default: all)")
    parser.add_argument("--summary-only", action="store_true",
                       help="Only print summary, don't process files")
    parser.add_argument("--extract-only", action="store_true",
                       help="Only extract ETH/BTC funding rates from existing processed data")
    parser.add_argument("--show-summary", action="store_true",
                       help="Show data summary after processing")
    
    args = parser.parse_args()
    
    # Initialize processor
    okx_processor = OKXDataProcessor(args.data_dir, args.output_dir)
    
    if args.summary_only:
        # Just show summary of available zip files
        okx_processor.print_summary()
        return
    
    if args.extract_only:
        # Only extract ETH/BTC funding rates from existing processed data
        success = okx_processor.extract_eth_btc_funding_rates(Path("data"))
        if success and args.show_summary:
            okx_processor.show_data_summary(Path("data"))
        return
    
    # Print summary of available zip files
    okx_processor.print_summary()
    
    # Process files
    if args.data_type:
        results = okx_processor.process_all_files(args.data_type)
    else:
        # Full pipeline: process zip files + extract ETH/BTC funding rates
        success = okx_processor.process_okx_data(Path("data"))
        if not success:
            return
    
    if args.show_summary:
        okx_processor.show_data_summary(Path("data"))
    
    print(f"\n✅ Processing complete!")


if __name__ == "__main__":
    main()


