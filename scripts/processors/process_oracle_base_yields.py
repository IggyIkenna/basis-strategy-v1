"""
Oracle-Based Base Staking Yields Processor

Extracts base staking yields from Aave oracle price ratios:
1. weETH/ETH oracle ratios -> weETH base staking yields
2. wstETH/USD oracle prices + ETH/USD -> wstETH base staking yields

Methodology:
- Calculate hourly yield from price ratio changes: (price_t / price_t-1) - 1
- Aggregate to daily yields for backtesting compatibility
- Convert to APR for consistency with existing methodology

Inputs:
- data/protocol_data/aave/oracle/weETH_ETH_oracle_2024-01-01_2025-09-18.csv
- data/protocol_data/aave/oracle/wstETH_oracle_usd_2024-01-01_2025-09-18.csv
- data/market_data/spot_prices/eth_usd/ (for wstETH/ETH ratio calculation)

Outputs:
- data/protocol_data/staking/base_yields/weeth_oracle_yields_2024-01-01_2025-09-18.csv
- data/protocol_data/staking/base_yields/wsteth_oracle_yields_2024-01-01_2025-09-18.csv
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging


class OracleBaseYieldsProcessor:
    """Process base staking yields from Aave oracle price ratios."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.oracle_dir = self.data_dir / "protocol_data" / "aave" / "oracle"
        self.market_data_dir = self.data_dir / "market_data" / "spot_prices"
        self.output_dir = self.data_dir / "protocol_data" / "staking" / "base_yields"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger("oracle_base_yields")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info("Oracle Base Yields Processor initialized")
        self.logger.info(f"Oracle data: {self.oracle_dir}")
        self.logger.info(f"Output: {self.output_dir}")
    
    def load_weeth_oracle_data(self) -> pd.DataFrame:
        """Load weETH/ETH oracle ratio data."""
        self.logger.info("📊 Loading weETH/ETH oracle data...")
        
        weeth_file = self.oracle_dir / "weETH_ETH_oracle_2024-01-01_2025-09-18.csv"
        if not weeth_file.exists():
            raise FileNotFoundError(f"weETH oracle data not found: {weeth_file}")
        
        df = pd.read_csv(weeth_file, comment='#')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        self.logger.info(f"✅ Loaded {len(df):,} weETH oracle records")
        self.logger.info(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        self.logger.info(f"   Price range: {df['oracle_price_eth'].min():.6f} - {df['oracle_price_eth'].max():.6f} ETH")
        
        return df
    
    def load_wsteth_oracle_data(self) -> pd.DataFrame:
        """Load wstETH/USD oracle price data."""
        self.logger.info("📊 Loading wstETH/USD oracle data...")
        
        wsteth_file = self.oracle_dir / "wstETH_oracle_usd_2024-01-01_2025-09-18.csv"
        if not wsteth_file.exists():
            raise FileNotFoundError(f"wstETH oracle data not found: {wsteth_file}")
        
        df = pd.read_csv(wsteth_file, comment='#')
        
        # Handle both Unix timestamp and datetime formats
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        except (ValueError, TypeError):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        df['date'] = df['timestamp'].dt.date
        
        self.logger.info(f"✅ Loaded {len(df):,} wstETH oracle records")
        self.logger.info(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        self.logger.info(f"   Price range: ${df['oracle_price_usd'].min():.2f} - ${df['oracle_price_usd'].max():.2f}")
        
        return df
    
    def load_eth_prices(self) -> pd.DataFrame:
        """Load ETH/USD prices for wstETH ratio calculation."""
        self.logger.info("📊 Loading ETH/USD prices...")
        
        # Find ETH price files (try multiple patterns)
        eth_patterns = ["ETHUSDT_1h_*.csv", "*ETHUSDT*1h*.csv", "*WETHUSDT*1h*.csv"]
        eth_files = []
        
        for pattern in eth_patterns:
            eth_files.extend(list(self.market_data_dir.glob(f"eth_usd/{pattern}")))
        
        # Remove duplicates
        eth_files = list(set(eth_files))
        
        if not eth_files:
            raise FileNotFoundError(f"No ETH price files found matching patterns: {eth_patterns}")
        
        # Use the largest file (most complete data)
        eth_file = max(eth_files, key=lambda x: x.stat().st_size)
        
        df = pd.read_csv(eth_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        # Create daily ETH prices
        daily_eth = df.groupby('date')['close'].mean().reset_index()
        daily_eth['eth_price_usd'] = daily_eth['close']
        
        self.logger.info(f"✅ Loaded ETH prices from {eth_file.name}")
        self.logger.info(f"   Date range: {daily_eth['date'].min()} to {daily_eth['date'].max()}")
        self.logger.info(f"   Price range: ${daily_eth['eth_price_usd'].min():.2f} - ${daily_eth['eth_price_usd'].max():.2f}")
        
        return daily_eth[['date', 'eth_price_usd']]
    
    def calculate_hourly_yields(self, df: pd.DataFrame, price_col: str) -> pd.DataFrame:
        """Calculate hourly yields from price changes."""
        df = df.copy()
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Calculate hourly yield: (price_t / price_t-1) - 1
        df['price_change'] = df[price_col].pct_change()
        df['hourly_yield'] = df['price_change'].fillna(0)
        
        # Remove extreme hourly yields before annualization (prevents overflow)
        # Remove > 0.1% hourly changes (likely data errors or extreme events)
        df = df[df['hourly_yield'].abs() < 0.001]
        
        # Annualize hourly yield: (1 + hourly_yield)^(24*365) - 1
        # Use clip to prevent overflow in edge cases
        df['hourly_apr'] = ((1 + df['hourly_yield'].clip(-0.001, 0.001)) ** (24 * 365) - 1).fillna(0)
        
        # Remove extreme outliers (likely data errors)
        df = df[df['hourly_apr'].abs() < 10.0]  # Remove yields > 1000% APR
        
        return df
    
    def aggregate_to_daily(self, df: pd.DataFrame, price_col: str = 'oracle_price_eth') -> pd.DataFrame:
        """Aggregate hourly yields to daily yields."""
        daily_data = []
        
        for date in sorted(df['date'].unique()):
            day_data = df[df['date'] == date].copy()
            
            if len(day_data) < 2:  # Need at least 2 hours for meaningful calculation
                continue
            
            # Calculate daily yield from hourly yields
            # Daily yield = (1 + hourly_yield_1) * (1 + hourly_yield_2) * ... - 1
            daily_yield = (1 + day_data['hourly_yield']).prod() - 1
            
            # Annualize daily yield
            daily_apr = ((1 + daily_yield) ** 365 - 1)
            
            # Get price info
            start_price = day_data[day_data['timestamp'] == day_data['timestamp'].min()][price_col].iloc[0]
            end_price = day_data[day_data['timestamp'] == day_data['timestamp'].max()][price_col].iloc[0]
            
            # Use 00:00:00 UTC for daily timestamp consistency
            daily_timestamp = pd.Timestamp(date).tz_localize('UTC')
            
            daily_data.append({
                'date': date,
                'timestamp': daily_timestamp.isoformat() + 'Z',
                'daily_yield': daily_yield,
                'daily_apr': daily_apr,
                'start_price': start_price,
                'end_price': end_price,
                'price_change_pct': (end_price / start_price - 1) * 100,
                'hours_in_day': len(day_data)
            })
        
        return pd.DataFrame(daily_data)
    
    def process_weeth_yields(self, start_date: str = "2024-01-01", end_date: str = "2025-09-18") -> Dict:
        """Process weETH base staking yields from oracle ratios."""
        self.logger.info("🚀 Processing weETH base staking yields...")
        
        # Load data
        weeth_df = self.load_weeth_oracle_data()
        
        # Calculate hourly yields
        weeth_df = self.calculate_hourly_yields(weeth_df, 'oracle_price_eth')
        
        # Aggregate to daily
        daily_df = self.aggregate_to_daily(weeth_df)
        
        # Filter by date range
        start_dt = pd.to_datetime(start_date).date()
        end_dt = pd.to_datetime(end_date).date()
        daily_df = daily_df[(daily_df['date'] >= start_dt) & (daily_df['date'] <= end_dt)]
        
        # Create standardized output
        output_data = []
        for _, row in daily_df.iterrows():
            output_data.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'timestamp': row['timestamp'],
                'protocol': 'etherfi',
                'symbol': 'weETH',
                'asset_type': 'liquid_restaking_token',
                'base_staking_apr': row['daily_apr'],
                'base_staking_apy': ((1 + row['daily_apr']/365) ** 365 - 1),
                'daily_yield': row['daily_yield'],
                'price_start_eth': row['start_price'],
                'price_end_eth': row['end_price'],
                'price_change_pct': row['price_change_pct'],
                'hours_aggregated': row['hours_in_day'],
                'yield_source': 'aave_oracle_weeth_eth_ratio',
                'methodology': 'hourly_price_ratio_changes_aggregated_to_daily',
                'processed_date': datetime.now().isoformat()
            })
        
        # Save output
        output_file = self.output_dir / f"weeth_oracle_yields_{start_date}_{end_date}.csv"
        output_df = pd.DataFrame(output_data)
        output_df.to_csv(output_file, index=False)
        
        # Create summary
        avg_apr = output_df['base_staking_apr'].mean()
        avg_apy = output_df['base_staking_apy'].mean()
        
        summary = {
            'processing_completed': datetime.now().isoformat(),
            'asset': 'weETH',
            'methodology': 'aave_oracle_ratio_based',
            'records_processed': len(output_data),
            'date_range': f"{start_date} to {end_date}",
            'yield_statistics': {
                'average_apr': avg_apr,
                'average_apy': avg_apy,
                'min_apr': output_df['base_staking_apr'].min(),
                'max_apr': output_df['base_staking_apr'].max()
            },
            'output_file': str(output_file)
        }
        
        self.logger.info(f"✅ weETH processing complete: {len(output_data)} records")
        self.logger.info(f"   Average APR: {avg_apr:.4f} ({avg_apr*100:.2f}%)")
        self.logger.info(f"   Average APY: {avg_apy:.4f} ({avg_apy*100:.2f}%)")
        
        return summary
    
    def process_wsteth_yields(self, start_date: str = "2024-01-01", end_date: str = "2025-09-18") -> Dict:
        """Process wstETH base staking yields from oracle prices."""
        self.logger.info("🚀 Processing wstETH base staking yields...")
        
        # Load data
        wsteth_df = self.load_wsteth_oracle_data()
        eth_df = self.load_eth_prices()
        
        # Add hour column for hourly processing
        wsteth_df['hour'] = wsteth_df['timestamp'].dt.hour
        
        # Merge wstETH and ETH prices on date (ETH is daily average)
        merged_df = wsteth_df.merge(eth_df, on='date', how='inner')
        
        # Calculate wstETH/ETH ratio (hourly)
        merged_df['wsteth_eth_ratio'] = merged_df['oracle_price_usd'] / merged_df['eth_price_usd']
        
        # Remove any extreme outliers
        merged_df = merged_df[
            (merged_df['wsteth_eth_ratio'] > 0.5) & 
            (merged_df['wsteth_eth_ratio'] < 2.0)
        ]
        
        # Sort by timestamp for proper hourly yield calculation
        merged_df = merged_df.sort_values('timestamp').reset_index(drop=True)
        
        # Calculate HOURLY yields from ratio changes
        merged_df['ratio_change'] = merged_df['wsteth_eth_ratio'].pct_change()
        merged_df['hourly_yield'] = merged_df['ratio_change'].fillna(0)
        
        # Remove extreme yield changes (likely data errors) - use stricter filter
        merged_df = merged_df[merged_df['hourly_yield'].abs() < 0.001]  # Remove >0.1% hourly changes
        
        # Annualize hourly yield for reference - clip to prevent overflow
        hourly_yield_clipped = merged_df['hourly_yield'].clip(-0.001, 0.001)
        merged_df['hourly_apr'] = ((1 + hourly_yield_clipped) ** (24 * 365) - 1).fillna(0)
        
        # Rename ratio column to match aggregate_to_daily expectations
        merged_df['oracle_price_eth'] = merged_df['wsteth_eth_ratio']
        
        # Aggregate to daily using same method as weETH
        daily_df = self.aggregate_to_daily(merged_df, price_col='oracle_price_eth')
        
        # Filter by date range
        start_dt = pd.to_datetime(start_date).date()
        end_dt = pd.to_datetime(end_date).date()
        daily_df = daily_df[(daily_df['date'] >= start_dt) & (daily_df['date'] <= end_dt)]
        
        # Get reference data from merged_df for prices
        # Group by date to get representative prices
        price_data = merged_df.groupby('date').agg({
            'oracle_price_usd': 'mean',
            'eth_price_usd': 'first',
            'wsteth_eth_ratio': 'mean'
        }).reset_index()
        
        # Merge daily aggregated yields with price data
        daily_df = daily_df.merge(price_data, on='date', how='left')
        
        # Create standardized output
        output_data = []
        for _, row in daily_df.iterrows():
            output_data.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'timestamp': row['timestamp'],
                'protocol': 'lido',
                'symbol': 'wstETH',
                'asset_type': 'liquid_staking_token',
                'base_staking_apr': row['daily_apr'],
                'base_staking_apy': ((1 + row['daily_apr']/365) ** 365 - 1),
                'daily_yield': row['daily_yield'],
                'wsteth_price_usd': row['oracle_price_usd'],
                'eth_price_usd': row['eth_price_usd'],
                'wsteth_eth_ratio': row['wsteth_eth_ratio'],
                'price_change_pct': row['price_change_pct'],
                'hours_aggregated': row['hours_in_day'],
                'yield_source': 'aave_oracle_wsteth_usd_with_eth_conversion',
                'methodology': 'hourly_price_ratio_changes_aggregated_to_daily',
                'processed_date': datetime.now().isoformat()
            })
        
        # Save output (ensure sorted by date)
        output_file = self.output_dir / f"wsteth_oracle_yields_{start_date}_{end_date}.csv"
        output_df = pd.DataFrame(output_data)
        output_df = output_df.sort_values('date').reset_index(drop=True)
        output_df.to_csv(output_file, index=False)
        
        # Create summary
        avg_apr = output_df['base_staking_apr'].mean()
        avg_apy = output_df['base_staking_apy'].mean()
        
        summary = {
            'processing_completed': datetime.now().isoformat(),
            'asset': 'wstETH',
            'methodology': 'aave_oracle_price_based',
            'records_processed': len(output_data),
            'date_range': f"{start_date} to {end_date}",
            'yield_statistics': {
                'average_apr': avg_apr,
                'average_apy': avg_apy,
                'min_apr': output_df['base_staking_apr'].min(),
                'max_apr': output_df['base_staking_apr'].max()
            },
            'output_file': str(output_file)
        }
        
        self.logger.info(f"✅ wstETH processing complete: {len(output_data)} records")
        self.logger.info(f"   Average APR: {avg_apr:.4f} ({avg_apr*100:.2f}%)")
        self.logger.info(f"   Average APY: {avg_apy:.4f} ({avg_apy*100:.2f}%)")
        
        return summary
    
    def process_all_oracle_yields(self, start_date: str = "2024-01-01", end_date: str = "2025-09-18") -> Dict:
        """Process all oracle-based base staking yields."""
        self.logger.info("🚀 Processing all oracle-based base staking yields...")
        self.logger.info(f"📅 Date range: {start_date} to {end_date}")
        
        results = {}
        
        try:
            # Process weETH yields
            self.logger.info("=" * 50)
            self.logger.info("🔄 Processing weETH yields...")
            weeth_result = self.process_weeth_yields(start_date, end_date)
            results['weeth'] = weeth_result
            
            # Process wstETH yields
            self.logger.info("=" * 50)
            self.logger.info("🔄 Processing wstETH yields...")
            wsteth_result = self.process_wsteth_yields(start_date, end_date)
            results['wsteth'] = wsteth_result
            
            # Create master summary
            master_summary = {
                'processing_completed': datetime.now().isoformat(),
                'methodology': 'aave_oracle_price_ratio_based',
                'date_range': f"{start_date} to {end_date}",
                'assets_processed': list(results.keys()),
                'results': results,
                'total_records': sum(r['records_processed'] for r in results.values()),
                'average_yields': {
                    'weeth_avg_apr': weeth_result['yield_statistics']['average_apr'],
                    'wsteth_avg_apr': wsteth_result['yield_statistics']['average_apr']
                }
            }
            
            # Save master summary
            summary_file = self.output_dir / f"oracle_base_yields_summary_{start_date}_{end_date}.json"
            with open(summary_file, 'w') as f:
                json.dump(master_summary, f, indent=2)
            
            self.logger.info("=" * 70)
            self.logger.info("🎯 ORACLE BASE YIELDS PROCESSING COMPLETE!")
            self.logger.info("=" * 70)
            self.logger.info(f"📊 Total records: {master_summary['total_records']:,}")
            self.logger.info(f"📈 weETH avg APR: {weeth_result['yield_statistics']['average_apr']*100:.2f}%")
            self.logger.info(f"📈 wstETH avg APR: {wsteth_result['yield_statistics']['average_apr']*100:.2f}%")
            self.logger.info(f"💾 Summary: {summary_file}")
            self.logger.info("=" * 70)
            
            return master_summary
            
        except Exception as e:
            self.logger.error(f"❌ Processing failed: {e}")
            raise


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process oracle-based base staking yields")
    parser.add_argument("--start-date", type=str, default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2025-09-18", help="End date (YYYY-MM-DD)")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--asset", type=str, choices=['weeth', 'wsteth', 'all'], default='all', help="Asset to process")
    
    args = parser.parse_args()
    
    try:
        processor = OracleBaseYieldsProcessor(args.data_dir)
        
        print(f"🎯 Processing oracle-based base staking yields...")
        print(f"📅 Date range: {args.start_date} to {args.end_date}")
        print(f"🔄 Asset: {args.asset}")
        
        if args.asset == 'weeth':
            result = processor.process_weeth_yields(args.start_date, args.end_date)
        elif args.asset == 'wsteth':
            result = processor.process_wsteth_yields(args.start_date, args.end_date)
        else:
            result = processor.process_all_oracle_yields(args.start_date, args.end_date)
        
        print(f"\n🎉 SUCCESS! Oracle base yields processed")
        if args.asset == 'all':
            print(f"📊 Total records: {result['total_records']:,}")
            print(f"📈 weETH avg APR: {result['average_yields']['weeth_avg_apr']*100:.2f}%")
            print(f"📈 wstETH avg APR: {result['average_yields']['wsteth_avg_apr']*100:.2f}%")
        else:
            print(f"📊 Records: {result['records_processed']:,}")
            print(f"📈 Average APR: {result['yield_statistics']['average_apr']*100:.2f}%")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
