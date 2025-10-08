#!/usr/bin/env python3
"""
Enhanced Execution Cost Generator

Generates comprehensive execution cost data by combining:
1. Gas costs from gas price data (ethereum_gas_prices_*.csv)
2. Trading pair execution costs (slippage + exchange fees)
3. Venue-specific cost modeling

This provides complete transaction cost modeling for all DeFi operations.
"""

import asyncio
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import glob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Complete trading pairs for execution cost modeling
TRADING_PAIRS = [
    # DEX pairs (Uniswap V3) - Protocol fees + slippage + MEV
    "ETH/USDT",      # Primary conversion
    "ETH/wstETH",    # Lido wrapped LST
    "ETH/weETH",     # EtherFi LST
    "ETH/stETH",     # Lido direct LST
    "ETH/eETH",      # EtherFi base LST
    
    # CEX spot pairs (Binance) - Exchange fees + slippage
    "EIGEN/USDT",    # Sell EIGEN rewards to USDT
    "ETHFI/USDT",    # Sell ETHFI rewards to USDT
    "EIGEN/ETH",     # Sell EIGEN rewards to ETH
    "ETHFI/ETH",     # Sell ETHFI rewards to ETH
    
    # CEX perpetual pairs (Multi-venue) - Exchange fees + slippage
    "ETHUSDT-PERP",  # ETH basis trading hedge
    "BTCUSDT-PERP"   # BTC basis trading
]

SIZE_BUCKETS = [10000, 100000, 1000000]  # $10k, $100k, $1M

# Execution Cost Estimates (realistic based on market structure)
EXECUTION_COST_ESTIMATES = {
    # DEX pairs (Uniswap V3) - Protocol fees + slippage + MEV
    "ETH/USDT": {"base": 5, "size_impact": [0, 2, 8], "venue": "DEX"},        # High liquidity
    "ETH/wstETH": {"base": 15, "size_impact": [0, 3, 12], "venue": "DEX"},    # Good liquidity
    "ETH/weETH": {"base": 20, "size_impact": [0, 4, 15], "venue": "DEX"},     # Medium liquidity
    "ETH/stETH": {"base": 10, "size_impact": [0, 2, 8], "venue": "DEX"},      # Excellent liquidity
    "ETH/eETH": {"base": 25, "size_impact": [0, 5, 20], "venue": "DEX"},      # Medium liquidity
    
    # CEX spot pairs (Binance) - Exchange fees + slippage
    "EIGEN/USDT": {"base": 8, "size_impact": [0, 5, 20], "venue": "CEX_SPOT"},  # Binance spot
    "ETHFI/USDT": {"base": 12, "size_impact": [0, 8, 30], "venue": "CEX_SPOT"}, # Binance spot
    "EIGEN/ETH": {"base": 10, "size_impact": [0, 6, 25], "venue": "CEX_SPOT"},   # Binance spot
    "ETHFI/ETH": {"base": 15, "size_impact": [0, 10, 35], "venue": "CEX_SPOT"},  # Binance spot
    
    # CEX perpetual pairs (Multi-venue) - Exchange fees + slippage
    "ETHUSDT-PERP": {"base": 3, "size_impact": [0, 1, 5], "venue": "CEX_PERP"}, # Excellent liquidity
    "BTCUSDT-PERP": {"base": 3, "size_impact": [0, 1, 5], "venue": "CEX_PERP"}  # Excellent liquidity
}


class SimpleExecutionCostGenerator:
    """Generate comprehensive execution cost data for all trading pairs."""
    
    def __init__(self, output_dir: str = "data/execution_costs", gas_data_dir: str = "data/blockchain_data/gas_prices"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.gas_data_dir = Path(gas_data_dir)
        
        logger.info("Enhanced Execution Cost Generator initialized")
        logger.info(f"Gas data directory: {self.gas_data_dir}")
    
    def get_size_bucket(self, size_usd: float) -> str:
        """Get size bucket label."""
        if size_usd <= 50000:
            return "10k"
        elif size_usd <= 500000:
            return "100k"
        else:
            return "1m"
    
    def load_gas_cost_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Load gas cost data from gas price files, merging multiple files if needed.
        Validates complete coverage and throws error if gaps exist.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with gas cost data covering the complete date range
            
        Raises:
            ValueError: If complete gas data coverage is not available
        """
        # Find gas data files that overlap with our date range
        gas_files = list(self.gas_data_dir.glob("ethereum_gas_prices_*.csv"))
        
        if not gas_files:
            raise ValueError(f"No gas price files found in {self.gas_data_dir}")
        
        req_start = pd.to_datetime(start_date)
        req_end = pd.to_datetime(end_date)
        
        # Collect all files that overlap with our date range
        overlapping_files = []
        for gas_file in sorted(gas_files):  # Sort chronologically
            try:
                df = pd.read_csv(gas_file, index_col=0, parse_dates=True)
                
                # Check if this file covers our date range (handle timezone issues)
                file_start = df.index.min()
                file_end = df.index.max()
                
                # Make timezone-aware if needed
                if file_start.tz is not None and req_start.tz is None:
                    req_start = req_start.tz_localize(file_start.tz)
                if file_end.tz is not None and req_end.tz is None:
                    req_end = req_end.tz_localize(file_end.tz)
                
                if file_start <= req_end and file_end >= req_start:
                    overlapping_files.append((gas_file, df))
                    logger.info(f"Found overlapping gas data file: {gas_file}")
                    logger.info(f"  Coverage: {file_start} to {file_end}")
                    
            except Exception as e:
                logger.warning(f"Failed to load {gas_file}: {e}")
                continue
        
        if not overlapping_files:
            raise ValueError(f"No gas price files found that overlap with date range {start_date} to {end_date}")
        
        # Merge all overlapping files
        gas_data_frames = []
        for gas_file, df in overlapping_files:
            gas_data_frames.append(df)
            logger.info(f"Loaded gas cost data from {gas_file}")
        
        # Concatenate all data frames
        if len(gas_data_frames) == 1:
            gas_data = gas_data_frames[0]
        else:
            gas_data = pd.concat(gas_data_frames, ignore_index=False)
            # Remove duplicates (in case files overlap)
            gas_data = gas_data[~gas_data.index.duplicated(keep='last')]
            gas_data = gas_data.sort_index()
            logger.info(f"Merged {len(gas_data_frames)} gas data files")
        
        # Filter to our exact date range (handle timezone issues)
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        # Make timezone-aware if gas data is timezone-aware
        if gas_data.index.tz is not None:
            if start_dt.tz is None:
                start_dt = start_dt.tz_localize(gas_data.index.tz)
            if end_dt.tz is None:
                end_dt = end_dt.tz_localize(gas_data.index.tz)
        
        # Filter to exact date range
        gas_data = gas_data.loc[start_dt:end_dt]
        
        # Validate complete coverage
        if len(gas_data) == 0:
            raise ValueError(f"No gas data available for the specified date range {start_date} to {end_date}")
        
        actual_start = gas_data.index.min()
        actual_end = gas_data.index.max()
        
        # Check if we have complete coverage
        if actual_start > start_dt:
            raise ValueError(f"Gas data coverage gap: missing data from {start_dt} to {actual_start}")
        
        if actual_end < end_dt:
            raise ValueError(f"Gas data coverage gap: missing data from {actual_end} to {end_dt}")
        
        logger.info(f"Gas cost data loaded: {len(gas_data)} records from {start_date} to {end_date}")
        logger.info(f"Complete coverage validated: {actual_start} to {actual_end}")
        return gas_data
    
    def get_gas_costs_for_timestamp(self, timestamp: pd.Timestamp, gas_data: pd.DataFrame) -> dict:
        """
        Get gas costs for a specific timestamp from the gas data.
        
        Args:
            timestamp: The timestamp to get gas costs for
            gas_data: DataFrame with gas cost data
            
        Returns:
            Dictionary with gas cost information
        """
        if gas_data is None:
            return None
        
        # Find the closest gas data point to our timestamp
        # Since we're using daily timestamps but gas data is hourly, find the closest hour
        timestamp_dt = pd.to_datetime(timestamp)
        
        # Find the closest gas data point
        time_diff = abs(gas_data.index - timestamp_dt)
        closest_idx = time_diff.argmin()
        closest_timestamp = gas_data.index[closest_idx]
        
        if time_diff[closest_idx] > pd.Timedelta(hours=12):  # More than 12 hours away
            return None
        
        gas_row = gas_data.loc[closest_timestamp]
        
        # Extract relevant gas cost information
        gas_costs = {
            "gas_price_gwei": gas_row.get("effective_price_gwei", None),
            "gas_price_wei": gas_row.get("effective_price_wei", None),
            "eth_price_usd": gas_row.get("eth_price_usd", None),
            "timestamp_gas_data": closest_timestamp.isoformat()
        }
        
        # Add operation-specific gas costs if available
        operation_costs = {}
        for col in gas_row.index:
            if col.endswith("_gwei") or col.endswith("_eth") or col.endswith("_usd"):
                operation_costs[col] = gas_row[col]
        
        gas_costs.update(operation_costs)
        
        return gas_costs
    
    def calculate_execution_cost(self, pair: str, size_usd: float) -> float:
        """
        Calculate execution cost (slippage + exchange fees) for a trading pair.
        
        Args:
            pair: Trading pair (e.g., "ETH/USDT")
            size_usd: Trade size in USD
            
        Returns:
            Execution cost in basis points
        """
        if pair not in EXECUTION_COST_ESTIMATES:
            logger.warning(f"Unknown pair {pair} - using default cost")
            return 25.0  # Default moderate cost
        
        config = EXECUTION_COST_ESTIMATES[pair]
        base_cost = config["base"]
        
        # Size impact based on trade size
        if size_usd <= 10000:
            size_impact = config["size_impact"][0]      # $10k
        elif size_usd <= 100000:
            size_impact = config["size_impact"][1]      # $100k  
        else:
            size_impact = config["size_impact"][2]      # $1M+
        
        total_cost = base_cost + size_impact
        return total_cost
    
    async def generate_execution_costs(self, start_date: str, end_date: str):
        """
        Generate comprehensive execution cost data for all pairs and sizes across the time period.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        logger.info(f"Generating comprehensive execution costs: {start_date} to {end_date}")
        
        # Load gas cost data
        gas_data = self.load_gas_cost_data(start_date, end_date)
        
        # Generate daily timestamps (hourly would be too much data)
        start_dt = pd.to_datetime(start_date, utc=True)
        end_dt = pd.to_datetime(end_date, utc=True)
        
        timestamps = []
        current = start_dt
        while current <= end_dt:
            timestamps.append(current)
            current += timedelta(days=1)  # Daily instead of hourly for efficiency
        
        total_simulations = len(TRADING_PAIRS) * len(SIZE_BUCKETS) * len(timestamps)
        logger.info(f"Total simulations: {total_simulations:,}")
        logger.info(f"Expected results: {len(timestamps)} days × {len(TRADING_PAIRS)} pairs × {len(SIZE_BUCKETS)} sizes")
        
        # Generate execution cost data
        results = []
        
        for i, timestamp in enumerate(timestamps):
            if i % 30 == 0:  # Log every 30 days
                logger.info(f"Progress: {i+1:,}/{len(timestamps):,} days ({(i+1)/len(timestamps)*100:.1f}%)")
            
            # Get gas costs for this timestamp (if available)
            gas_costs = self.get_gas_costs_for_timestamp(timestamp, gas_data)
            
            # Generate costs for all pairs and sizes for this day
            for pair in TRADING_PAIRS:
                for size_usd in SIZE_BUCKETS:
                    execution_cost_bps = self.calculate_execution_cost(pair, size_usd)
                    
                    result = {
                        "timestamp": timestamp.isoformat(),
                        "pair": pair,
                        "size_usd": size_usd,
                        "size_bucket": self.get_size_bucket(size_usd),
                        "execution_cost_bps": execution_cost_bps,
                        "venue_type": EXECUTION_COST_ESTIMATES[pair]["venue"],
                        "method": "enhanced_with_gas_costs"
                    }
                    
                    # Add gas cost data if available
                    if gas_costs:
                        result.update(gas_costs)
                    
                    results.append(result)
        
        # Save results
        await self.save_execution_costs(results)
        
        logger.info(f"Execution cost generation complete:")
        logger.info(f"  Total results: {len(results):,}")
        logger.info(f"  Pairs covered: {len(TRADING_PAIRS)}")
        logger.info(f"  Size buckets: {len(SIZE_BUCKETS)}")
        logger.info(f"  Gas cost integration: {'✅ Yes' if gas_data is not None else '❌ No'}")
    
    async def save_execution_costs(self, results):
        """Save execution cost results to files."""
        if not results:
            logger.warning("No execution cost results to save")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Save raw results
        raw_file = self.output_dir / "execution_cost_simulation_results.csv"
        df.to_csv(raw_file, index=False)
        logger.info(f"Saved {len(results):,} execution cost results to {raw_file}")
        
        # Build lookup table
        await self.build_lookup_table(df)
    
    async def build_lookup_table(self, df: pd.DataFrame):
        """Build execution cost lookup table."""
        try:
            # Build lookup: {pair: {size_bucket: {day: cost_bps}}}
            cost_lookup = {}
            
            for _, row in df.iterrows():
                pair = row['pair'].replace('/', '_')
                size_bucket = row['size_bucket']
                timestamp = pd.to_datetime(row['timestamp'])
                time_key = timestamp.strftime("%Y-%m-%d")  # Daily resolution
                
                if pair not in cost_lookup:
                    cost_lookup[pair] = {}
                if size_bucket not in cost_lookup[pair]:
                    cost_lookup[pair][size_bucket] = {}
                
                cost_lookup[pair][size_bucket][time_key] = row['execution_cost_bps']
            
            # Save lookup table
            lookup_dir = self.output_dir / "lookup_tables"
            lookup_dir.mkdir(exist_ok=True)
            
            cost_file = lookup_dir / "execution_costs_lookup.json"
            with open(cost_file, 'w') as f:
                json.dump(cost_lookup, f, indent=2)
            
            logger.info(f"Saved execution cost lookup to {cost_file}")
            
            # Generate summary
            summary = {
                "generation_date": datetime.now().isoformat(),
                "total_pairs": len(TRADING_PAIRS),
                "total_size_buckets": len(SIZE_BUCKETS),
                "total_records": len(df),
                "pairs_covered": TRADING_PAIRS,
                "size_buckets": SIZE_BUCKETS,
                "venue_breakdown": {
                    "DEX": len([p for p in TRADING_PAIRS if EXECUTION_COST_ESTIMATES[p]["venue"] == "DEX"]),
                    "CEX_SPOT": len([p for p in TRADING_PAIRS if EXECUTION_COST_ESTIMATES[p]["venue"] == "CEX_SPOT"]),
                    "CEX_PERP": len([p for p in TRADING_PAIRS if EXECUTION_COST_ESTIMATES[p]["venue"] == "CEX_PERP"])
                },
                "cost_ranges": {
                    pair: {
                        "base_cost_bps": config["base"],
                        "max_cost_bps": config["base"] + max(config["size_impact"]),
                        "venue": config["venue"]
                    }
                    for pair, config in EXECUTION_COST_ESTIMATES.items()
                }
            }
            
            summary_file = self.output_dir / "execution_cost_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Saved execution cost summary to {summary_file}")
            
        except Exception as e:
            logger.error(f"Error building lookup table: {e}")


async def main():
    """Main function to generate execution cost data."""
    generator = SimpleExecutionCostGenerator()
    
    print("🚀 Generating execution cost data (slippage + exchange fees) for all trading pairs...")
    print("📊 Covers 11 pairs: 5 DEX + 4 CEX spot + 2 CEX perp")
    print("⚡ Note: Gas costs handled separately by fetch_onchain_gas_data.py")
    
    # Generate for full period
    await generator.generate_execution_costs("2024-01-01", "2025-09-21")
    
    print("\n✅ Execution cost generation complete!")
    print("📊 Files generated:")
    print("  - data/execution_costs/execution_cost_simulation_results.csv")
    print("  - data/execution_costs/lookup_tables/execution_costs_lookup.json")
    print("  - data/execution_costs/execution_cost_summary.json")


if __name__ == "__main__":
    asyncio.run(main())
