"""
Ethena Benchmark Data Processor

Processes manually downloaded Ethena sUSDE historical data:
- Converts APY to APR for consistency with our methodology
- Standardizes format for backtesting comparison
- Outputs to protocol_data for integration

Manual Download Source: https://defillama.com/yields/pool/66985a81-9c51-46ca-9977-42b4fe7bc6df
"""

import pandas as pd
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict
import logging

class EthenaBenchmarkProcessor:
    """Process Ethena benchmark data for backtesting comparison."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.manual_sources_dir = self.data_dir / "manual_sources" / "benchmark_data"
        self.output_dir = self.data_dir / "protocol_data" / "staking" / "benchmark_yields"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger("ethena_processor")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info("Ethena Benchmark Processor initialized")
    
    def apy_to_apr(self, apy_decimal: float) -> float:
        """
        Convert APY to APR for consistency with our APR-first methodology.
        
        Args:
            apy_decimal: APY as decimal (e.g., 0.0749 for 7.49%)
            
        Returns:
            APR as decimal
        """
        if apy_decimal <= 0:
            return 0.0
        return ((1 + apy_decimal) ** (1/365) - 1) * 365
    
    def find_ethena_data_file(self, start_date: str = None, end_date: str = None) -> Path:
        """
        Find the most recent Ethena data file with optional date coverage validation.
        
        Args:
            start_date: Optional start date for coverage validation (YYYY-MM-DD)
            end_date: Optional end date for coverage validation (YYYY-MM-DD)
            
        Returns:
            Path to the Ethena data file
            
        Raises:
            FileNotFoundError: If no Ethena data files found
            ValueError: If date coverage validation fails
        """
        # Look for manually downloaded Ethena files
        ethena_patterns = [
            "ethena_susde_historical_*.csv",
            "ethena_*.csv",
            "*ethena*.csv"
        ]
        
        for pattern in ethena_patterns:
            files = list(self.manual_sources_dir.glob(pattern))
            if files:
                # Return the most recent file
                latest_file = max(files, key=lambda x: x.stat().st_mtime)
                self.logger.info(f"📄 Found Ethena data: {latest_file.name}")
                
                # Validate date coverage if requested
                if start_date and end_date:
                    self._validate_ethena_data_coverage(latest_file, start_date, end_date)
                
                return latest_file
        
        raise FileNotFoundError(f"No Ethena data files found in {self.manual_sources_dir}")
    
    def _validate_ethena_data_coverage(self, file_path: Path, start_date: str, end_date: str):
        """
        Validate that Ethena data covers the required date range.
        
        Args:
            file_path: Path to the Ethena data file
            start_date: Required start date (YYYY-MM-DD)
            end_date: Required end date (YYYY-MM-DD)
            
        Raises:
            ValueError: If date coverage is insufficient
        """
        try:
            df = pd.read_csv(file_path)
            
            # Handle different date column formats
            if 'Date' in df.columns:
                # Use the Date column directly
                df['date_parsed'] = pd.to_datetime(df['Date'])
            elif 'Timestamp' in df.columns:
                # Convert Unix timestamp to datetime
                df['date_parsed'] = pd.to_datetime(df['Timestamp'], unit='s')
            else:
                # Find date column (could be 'date', 'timestamp', etc.)
                date_col = None
                for col in df.columns:
                    if 'date' in col.lower() or 'timestamp' in col.lower():
                        date_col = col
                        break
                
                if not date_col:
                    self.logger.warning(f"⚠️  No date column found in {file_path.name} - skipping coverage validation")
                    return
                
                df['date_parsed'] = pd.to_datetime(df[date_col])
            
            data_start = df['date_parsed'].min().date()
            data_end = df['date_parsed'].max().date()
            
            # Check coverage
            required_start = pd.to_datetime(start_date).date()
            required_end = pd.to_datetime(end_date).date()
            
            if data_start > required_start:
                raise ValueError(f"Ethena data coverage gap: missing data from {required_start} to {data_start}")
            
            if data_end < required_end:
                raise ValueError(f"Ethena data coverage gap: missing data from {data_end} to {required_end}")
            
            self.logger.info(f"✅ Ethena data coverage validated: {data_start} to {data_end}")
            
        except Exception as e:
            if "coverage gap" in str(e):
                raise
            self.logger.warning(f"⚠️  Failed to validate Ethena data coverage: {e}")
    
    def interpolate_to_hourly(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Interpolate daily Ethena data to hourly using linear interpolation.
        
        Args:
            df: DataFrame with daily Ethena data
            
        Returns:
            DataFrame with hourly interpolated data
        """
        self.logger.info("🔄 Interpolating Ethena data to hourly...")
        
        # Ensure we have a proper timestamp column
        if 'timestamp' not in df.columns:
            if 'date' in df.columns:
                df['timestamp'] = pd.to_datetime(df['date'])
            elif 'Date' in df.columns:
                df['timestamp'] = pd.to_datetime(df['Date'])
            elif 'Timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
            else:
                raise ValueError("No valid timestamp column found for interpolation")
        
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Create hourly timestamp range
        start_time = df['timestamp'].min()
        end_time = df['timestamp'].max()
        hourly_range = pd.date_range(start=start_time, end=end_time, freq='H')
        
        self.logger.info(f"📊 Creating {len(hourly_range)} hourly timestamps from {len(df)} daily records")
        
        # Create hourly DataFrame
        df_hourly = pd.DataFrame({'timestamp': hourly_range})
        
        # Merge with original data
        df_hourly = df_hourly.merge(df[['timestamp', 'apy_decimal', 'apr_decimal', 'apy_percent', 'apr_percent']], 
                                    on='timestamp', how='left')
        
        # Linear interpolation for APY/APR values
        df_hourly['apy_decimal'] = df_hourly['apy_decimal'].interpolate(method='linear')
        df_hourly['apr_decimal'] = df_hourly['apr_decimal'].interpolate(method='linear')
        df_hourly['apy_percent'] = df_hourly['apy_percent'].interpolate(method='linear')
        df_hourly['apr_percent'] = df_hourly['apr_percent'].interpolate(method='linear')
        
        # Forward fill other columns
        for col in ['protocol', 'symbol', 'source', 'methodology']:
            if col in df.columns:
                df_hourly = df_hourly.merge(df[['timestamp', col]], on='timestamp', how='left')
                df_hourly[col] = df_hourly[col].ffill()
        
        # Add metadata
        df_hourly['date'] = df_hourly['timestamp'].dt.strftime('%Y-%m-%d')
        df_hourly['hour'] = df_hourly['timestamp'].dt.hour
        df_hourly['processed_date'] = datetime.now().isoformat()
        
        # Remove rows with NaN values (first few rows after interpolation)
        df_hourly = df_hourly.dropna(subset=['apy_decimal', 'apr_decimal']).reset_index(drop=True)
        
        self.logger.info(f"✅ Hourly interpolation complete: {len(df_hourly)} hourly records")
        
        return df_hourly
    
    def process_ethena_data(self, start_date: str = "2024-01-01", end_date: str = "2025-09-18", 
                           create_hourly: bool = True) -> Dict:
        """
        Process Ethena benchmark data and convert to APR.
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            create_hourly: Whether to create hourly interpolated data
            
        Returns:
            Processing results
        """
        self.logger.info("🚀 Processing Ethena benchmark data...")
        
        # Find and load Ethena data with date coverage validation
        ethena_file = self.find_ethena_data_file(start_date, end_date)
        
        try:
            df = pd.read_csv(ethena_file)
            self.logger.info(f"📊 Loaded {len(df):,} Ethena records")
            self.logger.info(f"   Columns: {list(df.columns)}")
            
            # Handle DeFiLlama CSV format: Base + Reward = Total APY
            if 'Base' in df.columns:
                # Calculate total APY from Base + Reward
                df['Reward'] = df['Reward'].fillna(0)  # Fill NaN rewards with 0
                df['total_apy_percent'] = df['Base'] + df['Reward']
                
                self.logger.info(f"📊 DeFiLlama format detected:")
                self.logger.info(f"   Base APY range: {df['Base'].min():.2f}% - {df['Base'].max():.2f}%")
                self.logger.info(f"   Reward APY range: {df['Reward'].min():.2f}% - {df['Reward'].max():.2f}%")
                self.logger.info(f"   Total APY range: {df['total_apy_percent'].min():.2f}% - {df['total_apy_percent'].max():.2f}%")
            else:
                # Fallback to standard APY column
                apy_columns = ['APY', 'apy', 'yield', 'Yield']
                apy_col = None
                
                for col in apy_columns:
                    if col in df.columns:
                        apy_col = col
                        break
                
                if not apy_col:
                    raise ValueError(f"No APY column found. Available columns: {list(df.columns)}")
                
                df['total_apy_percent'] = df[apy_col]
            
            # Convert APY to APR
            df['apy_decimal'] = df['total_apy_percent'] / 100.0  # Convert percentage to decimal
            df['apr_decimal'] = df['apy_decimal'].apply(self.apy_to_apr)
            df['apr_percent'] = df['apr_decimal'] * 100.0  # Convert back to percentage
            
            # Standardize date format
            if 'Date' in df.columns:
                df['date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
            elif 'Timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')  # Unix timestamp
                df['date'] = df['timestamp'].dt.strftime('%Y-%m-%d')
            else:
                # Create date from index if no date column
                df['date'] = pd.to_datetime(df.index).strftime('%Y-%m-%d')
            
            # Filter by date range
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            df['date_obj'] = pd.to_datetime(df['date']).dt.date
            date_filtered_df = df[(df['date_obj'] >= start_dt) & (df['date_obj'] <= end_dt)]
            
            # Filter out zero yields (invalid/missing data)
            filtered_df = date_filtered_df[date_filtered_df['total_apy_percent'] > 0]
            
            self.logger.info(f"📅 Date filtered to {len(date_filtered_df):,} records ({start_date} to {end_date})")
            self.logger.info(f"🚫 Removed {len(date_filtered_df) - len(filtered_df):,} records with 0% yield")
            self.logger.info(f"✅ Final dataset: {len(filtered_df):,} records with valid yields")
            
            # Create standardized output
            output_data = []
            
            for _, row in filtered_df.iterrows():
                record = {
                    'date': row['date'],
                    'protocol': 'ethena',
                    'symbol': 'sUSDE',
                    'apy_percent': row['total_apy_percent'],
                    'apr_percent': row['apr_percent'],
                    'apy_decimal': row['apy_decimal'],
                    'apr_decimal': row['apr_decimal'],
                    'base_apy_percent': row.get('Base', 0),
                    'reward_apy_percent': row.get('Reward', 0),
                    'source': 'defillama_manual_csv',
                    'processed_date': datetime.now().isoformat(),
                    'methodology': 'apy_converted_to_apr_for_consistency'
                }
                output_data.append(record)
            
            # Save processed data
            output_file = self.output_dir / f"ethena_susde_apr_benchmark_{start_date}_{end_date}.csv"
            
            output_df = pd.DataFrame(output_data)
            output_df.to_csv(output_file, index=False)
            
            # Create hourly interpolated data if requested
            hourly_output_file = None
            if create_hourly:
                self.logger.info("🔄 Creating hourly interpolated data...")
                hourly_df = self.interpolate_to_hourly(output_df)
                hourly_output_file = self.output_dir / f"ethena_susde_apr_benchmark_hourly_{start_date}_{end_date}.csv"
                hourly_df.to_csv(hourly_output_file, index=False)
                self.logger.info(f"💾 Hourly data saved: {hourly_output_file.name}")
            
            # Create summary
            avg_apy = output_df['apy_percent'].mean()
            avg_apr = output_df['apr_percent'].mean()
            min_apy = output_df['apy_percent'].min()
            max_apy = output_df['apy_percent'].max()
            
            summary = {
                'processing_completed': datetime.now().isoformat(),
                'source_file': ethena_file.name,
                'output_file': output_file.name,
                'hourly_output_file': hourly_output_file.name if hourly_output_file else None,
                'records_processed': len(output_data),
                'hourly_records_created': len(hourly_df) if create_hourly and 'hourly_df' in locals() else 0,
                'date_range': f"{start_date} to {end_date}",
                'yield_statistics': {
                    'average_apy_percent': avg_apy,
                    'average_apr_percent': avg_apr,
                    'min_apy_percent': min_apy,
                    'max_apy_percent': max_apy,
                    'apy_to_apr_conversion': 'applied_for_consistency'
                },
                'methodology': {
                    'apy_source': 'defillama_manual_csv_download',
                    'apr_calculation': 'apy_to_apr_daily_compounding_formula',
                    'hourly_interpolation': 'linear_interpolation_applied' if create_hourly else 'not_applied',
                    'purpose': 'benchmark_comparison_with_restaking_strategy'
                }
            }
            
            # Save summary
            summary_file = self.output_dir / f"ethena_processing_summary_{start_date}_{end_date}.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            self.logger.info("=" * 70)
            self.logger.info("🎯 ETHENA BENCHMARK PROCESSING COMPLETE!")
            self.logger.info("=" * 70)
            self.logger.info(f"📊 Records processed: {len(output_data):,}")
            self.logger.info(f"📈 Average APY: {avg_apy:.2f}%")
            self.logger.info(f"📈 Average APR: {avg_apr:.2f}% (for backtesting)")
            self.logger.info(f"📈 APY range: {min_apy:.2f}% - {max_apy:.2f}%")
            self.logger.info(f"💾 Output: {output_file}")
            self.logger.info(f"💾 Summary: {summary_file}")
            self.logger.info("=" * 70)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Processing failed: {e}")
            raise

def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process Ethena benchmark data from manual CSV download")
    parser.add_argument("--start-date", type=str, default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2025-09-18", help="End date (YYYY-MM-DD)")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--no-hourly", action="store_true", help="Skip hourly interpolation")
    
    args = parser.parse_args()
    
    try:
        processor = EthenaBenchmarkProcessor(args.data_dir)
        
        print(f"🎯 Processing Ethena benchmark data...")
        print(f"📅 Date range: {args.start_date} to {args.end_date}")
        
        result = processor.process_ethena_data(args.start_date, args.end_date, create_hourly=not args.no_hourly)
        
        print(f"\\n🎉 SUCCESS! Ethena benchmark data processed")
        print(f"📈 Average APY: {result['yield_statistics']['average_apy_percent']:.2f}%")
        print(f"📈 Average APR: {result['yield_statistics']['average_apr_percent']:.2f}% (for backtesting)")
        print(f"📊 Daily Records: {result['records_processed']:,}")
        if result.get('hourly_records_created', 0) > 0:
            print(f"📊 Hourly Records: {result['hourly_records_created']:,}")
        print(f"💾 Daily Output: {result['output_file']}")
        if result.get('hourly_output_file'):
            print(f"💾 Hourly Output: {result['hourly_output_file']}")
        
        return 0
        
    except Exception as e:
        print(f"\\n💥 ERROR: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
