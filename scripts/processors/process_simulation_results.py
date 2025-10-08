"""Process Tenderly Simulation Results

Processes raw Tenderly simulation data into optimized lookup tables
for use in the ExecutionCostModel during backtesting.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SimulationResultProcessor:
    """Process raw Tenderly simulation results into optimized lookup tables."""
    
    def __init__(self, input_dir: str = "data/execution_costs", output_dir: str = "data/execution_costs"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("SimulationResultProcessor initialized")
    
    def process_simulation_data(self, start_date: str = None, end_date: str = None):
        """
        Process raw simulation data into lookup tables with optional date coverage validation.
        
        Args:
            start_date: Optional start date for coverage validation (YYYY-MM-DD)
            end_date: Optional end date for coverage validation (YYYY-MM-DD)
            
        Raises:
            ValueError: If date coverage validation fails
        """
        try:
            # Load raw simulation results
            raw_file = self.input_dir / "tenderly_simulation_results.csv"
            if not raw_file.exists():
                raise FileNotFoundError(f"Raw simulation data not found: {raw_file}")
            
            df = pd.read_csv(raw_file)
            logger.info(f"Loaded {len(df):,} simulation results")
            
            # Validate date coverage if requested
            if start_date and end_date:
                self._validate_simulation_data_coverage(df, start_date, end_date)
            
            # Build optimized lookup tables
            self._build_execution_cost_lookup(df)
            self._build_gas_cost_lookup(df)
            
            # Generate summary statistics
            self._generate_summary_stats(df)
            
            logger.info("Simulation data processing complete")
            
        except Exception as e:
            logger.error(f"Error processing simulation data: {e}")
            raise
    
    def _validate_simulation_data_coverage(self, df: pd.DataFrame, start_date: str, end_date: str):
        """
        Validate that simulation data covers the required date range.
        
        Args:
            df: Simulation results DataFrame
            start_date: Required start date (YYYY-MM-DD)
            end_date: Required end date (YYYY-MM-DD)
            
        Raises:
            ValueError: If date coverage is insufficient
        """
        try:
            # Find timestamp column
            timestamp_col = None
            for col in df.columns:
                if 'timestamp' in col.lower() or 'date' in col.lower():
                    timestamp_col = col
                    break
            
            if not timestamp_col:
                logger.warning("⚠️  No timestamp column found in simulation data - skipping coverage validation")
                return
            
            # Convert to datetime
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            data_start = df[timestamp_col].min().date()
            data_end = df[timestamp_col].max().date()
            
            # Check coverage
            required_start = pd.to_datetime(start_date).date()
            required_end = pd.to_datetime(end_date).date()
            
            if data_start > required_start:
                raise ValueError(f"Simulation data coverage gap: missing data from {required_start} to {data_start}")
            
            if data_end < required_end:
                raise ValueError(f"Simulation data coverage gap: missing data from {data_end} to {required_end}")
            
            logger.info(f"✅ Simulation data coverage validated: {data_start} to {data_end}")
            
        except Exception as e:
            if "coverage gap" in str(e):
                raise
            logger.warning(f"⚠️  Failed to validate simulation data coverage: {e}")
    
    def _build_execution_cost_lookup(self, df: pd.DataFrame):
        """Build execution cost lookup table."""
        cost_lookup = {}
        
        for _, row in df.iterrows():
            pair = row['pair'].replace('/', '_')
            size_bucket = row['size_bucket']
            timestamp = pd.to_datetime(row['timestamp'])
            time_key = timestamp.strftime("%Y-%m-%d_%H")
            
            if pair not in cost_lookup:
                cost_lookup[pair] = {}
            if size_bucket not in cost_lookup[pair]:
                cost_lookup[pair][size_bucket] = {}
            
            cost_lookup[pair][size_bucket][time_key] = float(row['execution_cost_bps'])
        
        # Save lookup table
        output_file = self.output_dir / "execution_costs_lookup.json"
        with open(output_file, 'w') as f:
            json.dump(cost_lookup, f, indent=2)
        
        logger.info(f"Saved execution cost lookup: {len(cost_lookup)} pairs")
    
    def _build_gas_cost_lookup(self, df: pd.DataFrame):
        """Build gas cost lookup table."""
        gas_lookup = {}
        
        # Group by token and time
        for _, row in df.iterrows():
            token = row['pair'].split('/')[0]  # First token in pair
            timestamp = pd.to_datetime(row['timestamp'])
            time_key = timestamp.strftime("%Y-%m-%d_%H")
            
            if token not in gas_lookup:
                gas_lookup[token] = {}
            
            # Use average gas cost if multiple entries for same time
            if time_key in gas_lookup[token]:
                gas_lookup[token][time_key] = (gas_lookup[token][time_key] + row['gas_cost_usd']) / 2
            else:
                gas_lookup[token][time_key] = float(row['gas_cost_usd'])
        
        # Save lookup table
        output_file = self.output_dir / "gas_costs_lookup.json"
        with open(output_file, 'w') as f:
            json.dump(gas_lookup, f, indent=2)
        
        logger.info(f"Saved gas cost lookup: {len(gas_lookup)} tokens")
    
    def _generate_summary_stats(self, df: pd.DataFrame):
        """Generate summary statistics for simulation results."""
        try:
            summary = {
                "total_simulations": len(df),
                "pairs": df['pair'].nunique(),
                "size_buckets": df['size_bucket'].nunique(),
                "date_range": {
                    "start": df['timestamp'].min(),
                    "end": df['timestamp'].max()
                },
                "execution_costs": {
                    "mean_bps": float(df['execution_cost_bps'].mean()),
                    "median_bps": float(df['execution_cost_bps'].median()),
                    "std_bps": float(df['execution_cost_bps'].std()),
                    "min_bps": float(df['execution_cost_bps'].min()),
                    "max_bps": float(df['execution_cost_bps'].max())
                },
                "gas_costs": {
                    "mean_usd": float(df['gas_cost_usd'].mean()),
                    "median_usd": float(df['gas_cost_usd'].median()),
                    "std_usd": float(df['gas_cost_usd'].std())
                },
                "by_pair": {}
            }
            
            # Per-pair statistics
            for pair in df['pair'].unique():
                pair_df = df[df['pair'] == pair]
                summary["by_pair"][pair] = {
                    "simulations": len(pair_df),
                    "avg_execution_cost_bps": float(pair_df['execution_cost_bps'].mean()),
                    "avg_gas_cost_usd": float(pair_df['gas_cost_usd'].mean())
                }
            
            # Save summary
            summary_file = self.output_dir / "simulation_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Generated summary statistics: {summary_file}")
            
        except Exception as e:
            logger.error(f"Error generating summary stats: {e}")
    
    def interpolate_execution_costs(self, pair: str, exact_size_usd: float, timestamp: str) -> Optional[float]:
        """Interpolate execution costs between size buckets."""
        try:
            # Load lookup data
            lookup_file = self.output_dir / "execution_costs_lookup.json"
            with open(lookup_file, 'r') as f:
                cost_lookup = json.load(f)
            
            normalized_pair = pair.replace('/', '_')
            if normalized_pair not in cost_lookup:
                return None
            
            pair_data = cost_lookup[normalized_pair]
            time_key = pd.to_datetime(timestamp).strftime("%Y-%m-%d_%H")
            
            # Get costs for all size buckets at this time
            costs = {}
            sizes = {"10k": 10000, "100k": 100000, "1m": 1000000}
            
            for bucket, bucket_size in sizes.items():
                if bucket in pair_data and time_key in pair_data[bucket]:
                    costs[bucket_size] = pair_data[bucket][time_key]
            
            if len(costs) < 2:
                return None  # Need at least 2 points for interpolation
            
            # Linear interpolation between size buckets
            sizes_list = sorted(costs.keys())
            costs_list = [costs[size] for size in sizes_list]
            
            return float(np.interp(exact_size_usd, sizes_list, costs_list))
            
        except Exception as e:
            logger.error(f"Error interpolating execution costs: {e}")
            return None


def main():
    """Main function to process simulation results."""
    processor = SimulationResultProcessor()
    processor.process_simulation_data()


if __name__ == "__main__":
    main()
