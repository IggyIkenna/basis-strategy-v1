"""
AAVE Oracle Price Processor

Extracts oracle prices from AAVE rates data and creates oracle price datasets:
- Processes existing AAVE rates files to extract oracle prices
- Creates oracle_prices directory with USDT-denominated prices
- Derives ETH-denominated oracle prices for liquidation risk analysis
- Creates wstETH/ETH oracle ratio from wstETH/USD and USDT/ETH data
- Focuses on key assets: WETH, wstETH, weETH, USDT, USDC, DAI

Input: data/protocol_data/aave/rates/*.csv (rates data with oracle prices)
Output: data/protocol_data/aave/oracle/*.csv (pure oracle price data)
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import logging

class AAVEOraclePriceProcessor:
    """Process AAVE oracle prices from rates data."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.rates_dir = self.data_dir / "protocol_data" / "aave" / "rates"
        self.oracle_dir = self.data_dir / "protocol_data" / "aave" / "oracle"
        self.oracle_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger("aave_oracle_processor")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info("AAVE Oracle Price Processor initialized")
    
    def extract_oracle_prices_from_rates(self, start_date: str = None, end_date: str = None) -> Dict[str, pd.DataFrame]:
        """
        Extract oracle prices from AAVE rates files with optional date coverage validation.
        
        Args:
            start_date: Optional start date for coverage validation (YYYY-MM-DD)
            end_date: Optional end date for coverage validation (YYYY-MM-DD)
            
        Returns:
            Dictionary of oracle price DataFrames keyed by asset symbol
            
        Raises:
            ValueError: If date coverage validation fails
        """
        self.logger.info("📊 Extracting oracle prices from AAVE rates data...")
        
        oracle_data = {}
        
        # Look for AAVE v3 Ethereum rates files
        rates_files = list(self.rates_dir.glob("aave_v3_aave-v3-ethereum_*_rates_*.csv"))
        
        if not rates_files:
            raise FileNotFoundError(f"No AAVE rates files found in {self.rates_dir}")
        
        for rates_file in rates_files:
            try:
                # Extract asset name from filename
                filename_parts = rates_file.stem.split('_')
                asset = filename_parts[3] if len(filename_parts) > 3 else "unknown"
                
                self.logger.info(f"   Processing {asset} oracle prices...")
                
                # Load rates data
                df = pd.read_csv(rates_file)
                
                # Check if oracle price column exists
                price_columns = ['oracle_price_usd', 'price_usd', 'price', 'oracle_price']
                price_col = None
                
                for col in price_columns:
                    if col in df.columns:
                        price_col = col
                        break
                
                if not price_col:
                    self.logger.warning(f"     ⚠️  No oracle price column found in {asset} data")
                    continue
                
                # Extract oracle price data
                oracle_df = df[['timestamp', price_col]].copy()
                oracle_df = oracle_df.rename(columns={price_col: 'oracle_price_usd'})
                oracle_df['asset'] = asset
                oracle_df['source'] = 'aave_oracle_extracted'
                oracle_df['quote_currency'] = 'USD'
                
                # Remove any null/zero prices
                oracle_df = oracle_df[oracle_df['oracle_price_usd'] > 0]
                
                # Validate date coverage if requested
                if start_date and end_date:
                    self._validate_oracle_data_coverage(oracle_df, asset, start_date, end_date)
                
                oracle_data[asset] = oracle_df
                
                self.logger.info(f"     ✅ {asset}: {len(oracle_df):,} oracle price records")
                
            except Exception as e:
                self.logger.error(f"     ❌ Failed to process {rates_file.name}: {e}")
        
        return oracle_data
    
    def _validate_oracle_data_coverage(self, df: pd.DataFrame, asset: str, start_date: str, end_date: str):
        """
        Validate that oracle data covers the required date range.
        
        Args:
            df: Oracle price DataFrame
            asset: Asset symbol
            start_date: Required start date (YYYY-MM-DD)
            end_date: Required end date (YYYY-MM-DD)
            
        Raises:
            ValueError: If date coverage is insufficient
        """
        try:
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            data_start = df['timestamp'].min().date()
            data_end = df['timestamp'].max().date()
            
            # Check coverage
            required_start = pd.to_datetime(start_date).date()
            required_end = pd.to_datetime(end_date).date()
            
            if data_start > required_start:
                raise ValueError(f"{asset} oracle data coverage gap: missing data from {required_start} to {data_start}")
            
            if data_end < required_end:
                raise ValueError(f"{asset} oracle data coverage gap: missing data from {data_end} to {required_end}")
            
            self.logger.info(f"     ✅ {asset} oracle data coverage validated: {data_start} to {data_end}")
            
        except Exception as e:
            if "coverage gap" in str(e):
                raise
            self.logger.warning(f"     ⚠️  Failed to validate {asset} oracle data coverage: {e}")
    
    def create_eth_denominated_prices(self, oracle_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Create ETH-denominated oracle prices for liquidation analysis."""
        self.logger.info("🔄 Creating ETH-denominated oracle prices...")
        
        if 'WETH' not in oracle_data:
            self.logger.error("❌ No WETH oracle data found - cannot create ETH-denominated prices")
            return {}
        
        eth_oracle = oracle_data['WETH'].copy()
        eth_oracle = eth_oracle.set_index('timestamp').sort_index()
        
        eth_denominated = {}
        
        for asset, asset_oracle in oracle_data.items():
            if asset == 'WETH':
                continue  # Skip WETH vs ETH (would be 1.0)
            
            try:
                self.logger.info(f"   Creating {asset}/ETH oracle prices...")
                
                # Align timestamps
                asset_oracle = asset_oracle.set_index('timestamp').sort_index()
                
                # Merge with ETH prices
                merged = asset_oracle.join(eth_oracle[['oracle_price_usd']], rsuffix='_eth')
                merged = merged.dropna()
                
                # Calculate asset/ETH ratio
                merged['oracle_price_eth'] = merged['oracle_price_usd'] / merged['oracle_price_usd_eth']
                
                # Create clean output
                eth_denominated_df = merged[['oracle_price_eth']].copy()
                eth_denominated_df['asset'] = asset
                eth_denominated_df['source'] = 'aave_oracle_derived'
                eth_denominated_df['quote_currency'] = 'ETH'
                eth_denominated_df = eth_denominated_df.reset_index()
                
                eth_denominated[f"{asset}_ETH"] = eth_denominated_df
                
                avg_ratio = eth_denominated_df['oracle_price_eth'].mean()
                self.logger.info(f"     ✅ {asset}/ETH: {len(eth_denominated_df):,} records, avg ratio: {avg_ratio:.4f}")
                
            except Exception as e:
                self.logger.error(f"     ❌ Failed to create {asset}/ETH prices: {e}")
        
        return eth_denominated
    
    def create_wsteth_eth_oracle(self, oracle_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Create wstETH/ETH oracle ratio from wstETH/USD and USDT/ETH data."""
        self.logger.info("🔄 Creating wstETH/ETH oracle ratio...")
        
        # Check if we have the required data
        if 'wstETH' not in oracle_data:
            self.logger.warning("⚠️  No wstETH oracle data found - skipping wstETH/ETH creation")
            return pd.DataFrame()
        
        if 'USDT' not in oracle_data:
            self.logger.warning("⚠️  No USDT oracle data found - skipping wstETH/ETH creation")
            return pd.DataFrame()
        
        try:
            # Load wstETH USD prices
            wsteth_df = oracle_data['wstETH'].copy()
            # Handle both Unix timestamp and datetime formats
            try:
                wsteth_df['timestamp'] = pd.to_datetime(wsteth_df['timestamp'], unit='s')
            except (ValueError, TypeError):
                wsteth_df['timestamp'] = pd.to_datetime(wsteth_df['timestamp'])
            
            # Load USDT/ETH ratio (from existing ETH-denominated data)
            usdt_eth_file = self.oracle_dir / "USDT_ETH_oracle_2024-01-01_2025-09-18.csv"
            if not usdt_eth_file.exists():
                self.logger.warning("⚠️  USDT/ETH oracle file not found - skipping wstETH/ETH creation")
                return pd.DataFrame()
            
            usdt_eth_df = pd.read_csv(usdt_eth_file, comment='#')
            usdt_eth_df['timestamp'] = pd.to_datetime(usdt_eth_df['timestamp'])
            
            # Convert wstETH timestamps to match USDT/ETH format (hourly)
            wsteth_df['timestamp_hourly'] = wsteth_df['timestamp'].dt.floor('H')
            
            # Remove timezone from USDT/ETH timestamps for merge
            usdt_eth_df['timestamp_no_tz'] = usdt_eth_df['timestamp'].dt.tz_localize(None)
            
            # Merge the data
            merged_df = wsteth_df.merge(
                usdt_eth_df[['timestamp_no_tz', 'oracle_price_eth']], 
                left_on='timestamp_hourly', 
                right_on='timestamp_no_tz', 
                how='inner',
                suffixes=('_wsteth', '_usdt')
            )
            
            # Calculate wstETH/ETH ratio
            # wstETH/ETH = wstETH_USD / ETH_USD
            # ETH_USD = 1 / (USDT/ETH) (assuming USDT ≈ $1)
            merged_df['eth_usd'] = 1.0 / merged_df['oracle_price_eth']  # USDT/ETH inverted gives ETH/USD
            merged_df['wsteth_eth_ratio'] = merged_df['oracle_price_usd'] / merged_df['eth_usd']
            
            # Create output DataFrame
            output_df = pd.DataFrame({
                'timestamp': merged_df['timestamp'],
                'oracle_price_eth': merged_df['wsteth_eth_ratio'],
                'asset': 'wstETH',
                'source': 'aave_oracle_derived',
                'quote_currency': 'ETH'
            })
            
            # Sort by timestamp
            output_df = output_df.sort_values('timestamp').reset_index(drop=True)
            
            self.logger.info(f"✅ Created wstETH/ETH oracle: {len(output_df)} records")
            self.logger.info(f"   Date range: {output_df['timestamp'].min()} to {output_df['timestamp'].max()}")
            self.logger.info(f"   Ratio range: {output_df['oracle_price_eth'].min():.6f} - {output_df['oracle_price_eth'].max():.6f} ETH")
            self.logger.info(f"   Average ratio: {output_df['oracle_price_eth'].mean():.6f} ETH")
            
            return output_df
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create wstETH/ETH oracle: {e}")
            return pd.DataFrame()
    
    def save_oracle_data(self, oracle_data: Dict[str, pd.DataFrame], eth_denominated: Dict[str, pd.DataFrame], wsteth_eth_df: pd.DataFrame = None):
        """Save oracle price data to organized files."""
        self.logger.info("💾 Saving oracle price data...")
        
        # Save USD-denominated oracle prices
        for asset, df in oracle_data.items():
            try:
                filename = f"{asset}_oracle_usd_2024-01-01_2025-09-18.csv"
                filepath = self.oracle_dir / filename
                
                # Add header with source attribution
                with open(filepath, 'w') as f:
                    f.write(f"# Source: aave_oracle_extracted\n")
                    f.write(f"# Asset: {asset}\n")
                    f.write(f"# Quote_currency: USD\n")
                    f.write(f"# Processed: {datetime.now().isoformat()}\n")
                    f.write(f"# Records: {len(df)}\n")
                    
                    df.to_csv(f, index=False)
                
                self.logger.info(f"   ✅ {filename}: {len(df):,} records")
                
            except Exception as e:
                self.logger.error(f"   ❌ Failed to save {asset} oracle data: {e}")
        
        # Save ETH-denominated oracle prices
        for pair_name, df in eth_denominated.items():
            try:
                filename = f"{pair_name}_oracle_2024-01-01_2025-09-18.csv"
                filepath = self.oracle_dir / filename
                
                asset = pair_name.replace('_ETH', '')
                
                # Add header with source attribution
                with open(filepath, 'w') as f:
                    f.write(f"# Source: aave_oracle_derived\n")
                    f.write(f"# Asset_pair: {pair_name}\n")
                    f.write(f"# Quote_currency: ETH\n")
                    f.write(f"# Methodology: asset_usd / eth_usd\n")
                    f.write(f"# Processed: {datetime.now().isoformat()}\n")
                    f.write(f"# Records: {len(df)}\n")
                    
                    df.to_csv(f, index=False)
                
                self.logger.info(f"   ✅ {filename}: {len(df):,} records")
                
            except Exception as e:
                self.logger.error(f"   ❌ Failed to save {pair_name} oracle data: {e}")
        
        # Save wstETH/ETH oracle data if provided
        if wsteth_eth_df is not None and not wsteth_eth_df.empty:
            try:
                filename = "wstETH_ETH_oracle_2024-01-01_2025-09-18.csv"
                filepath = self.oracle_dir / filename
                
                # Add header with source attribution
                with open(filepath, 'w') as f:
                    f.write(f"# Source: aave_oracle_derived\n")
                    f.write(f"# Asset_pair: wstETH_ETH\n")
                    f.write(f"# Quote_currency: ETH\n")
                    f.write(f"# Methodology: wstETH_usd / eth_usd (where eth_usd = 1 / usdt_eth_ratio)\n")
                    f.write(f"# Processed: {datetime.now().isoformat()}\n")
                    f.write(f"# Records: {len(wsteth_eth_df)}\n")
                    
                    wsteth_eth_df.to_csv(f, index=False)
                
                self.logger.info(f"   ✅ {filename}: {len(wsteth_eth_df):,} records")
                
            except Exception as e:
                self.logger.error(f"   ❌ Failed to save wstETH/ETH oracle data: {e}")
    
    def process_all_oracle_data(self) -> Dict:
        """Process all AAVE oracle price data."""
        self.logger.info("🚀 Processing AAVE oracle price data...")
        
        # Extract oracle prices from rates data
        oracle_data = self.extract_oracle_prices_from_rates()
        
        if not oracle_data:
            self.logger.error("❌ No oracle data extracted from rates files")
            return {'success': False, 'error': 'No oracle data found'}
        
        # Create ETH-denominated prices
        eth_denominated = self.create_eth_denominated_prices(oracle_data)
        
        # Create wstETH/ETH oracle ratio
        wsteth_eth_df = self.create_wsteth_eth_oracle(oracle_data)
        
        # Save all data
        self.save_oracle_data(oracle_data, eth_denominated, wsteth_eth_df)
        
        # Create summary
        total_usd_assets = len(oracle_data)
        total_eth_pairs = len(eth_denominated)
        wsteth_eth_records = len(wsteth_eth_df) if not wsteth_eth_df.empty else 0
        total_records = sum(len(df) for df in oracle_data.values()) + sum(len(df) for df in eth_denominated.values()) + wsteth_eth_records
        
        summary = {
            'processing_completed': datetime.now().isoformat(),
            'source_directory': str(self.rates_dir),
            'output_directory': str(self.oracle_dir),
            'usd_denominated_assets': total_usd_assets,
            'eth_denominated_pairs': total_eth_pairs,
            'wsteth_eth_oracle_created': not wsteth_eth_df.empty,
            'wsteth_eth_records': wsteth_eth_records,
            'total_records_processed': total_records,
            'assets_processed': list(oracle_data.keys()),
            'eth_pairs_created': list(eth_denominated.keys())
        }
        
        # Save summary
        summary_file = self.oracle_dir / "oracle_processing_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info("=" * 70)
        self.logger.info("🎯 AAVE ORACLE PROCESSING COMPLETE!")
        self.logger.info("=" * 70)
        self.logger.info(f"📊 USD-denominated assets: {total_usd_assets}")
        self.logger.info(f"📊 ETH-denominated pairs: {total_eth_pairs}")
        if not wsteth_eth_df.empty:
            self.logger.info(f"📊 wstETH/ETH oracle: {wsteth_eth_records:,} records")
        self.logger.info(f"📊 Total records: {total_records:,}")
        self.logger.info(f"💾 Output directory: {self.oracle_dir}")
        self.logger.info(f"💾 Summary: {summary_file}")
        self.logger.info("=" * 70)
        
        return summary

def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process AAVE oracle prices from rates data")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    
    args = parser.parse_args()
    
    try:
        processor = AAVEOraclePriceProcessor(args.data_dir)
        
        print("🎯 Processing AAVE oracle prices...")
        print("📊 Extracting oracle prices from rates data")
        print("🔄 Creating ETH-denominated prices for liquidation analysis")
        print("🔄 Creating wstETH/ETH oracle ratio for staking yield analysis")
        
        result = processor.process_all_oracle_data()
        
        if result.get('success', True):
            print(f"\\n🎉 SUCCESS! AAVE oracle prices processed")
            print(f"📊 Assets: {result['usd_denominated_assets']} USD, {result['eth_denominated_pairs']} ETH pairs")
            if result.get('wsteth_eth_oracle_created', False):
                print(f"📊 wstETH/ETH oracle: {result['wsteth_eth_records']:,} records")
            print(f"📊 Records: {result['total_records_processed']:,}")
            print(f"💾 Output: {result['output_directory']}")
        else:
            print(f"\\n❌ FAILED: {result.get('error', 'Unknown error')}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\\n💥 ERROR: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
