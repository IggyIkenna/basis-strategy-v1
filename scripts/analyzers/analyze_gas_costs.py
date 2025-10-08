#!/usr/bin/env python3
"""
Operation Gas Cost Analysis Tool

This script analyzes historical gas price data and calculates the cost of various
DeFi operations in both ETH and USD terms across the entire backtest period.
It generates a comprehensive time series of operation costs for use in backtesting.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timedelta
import argparse


# Define standard gas units for each operation type
# Note: All operations include ETH/WETH auto-wrapping costs where needed
OPERATION_GAS_UNITS = {
    # Staking Operations (includes auto-wrapping)
    "STAKE_DEPOSIT": 150000,        # ETH→LST staking (includes protocol wrapping)
    "STAKE_WITHDRAWAL": 200000,     # LST→ETH unstaking (protocol unwrapping to ETH)
    "TOKEN_SWAP": 180000,           # DEX swap (includes router auto-wrapping)
    "UNWRAP_KING_TOKEN": 150000,    # weETH→ETH unwrapping (to ETH, not WETH)
    
    # Lending Operations (AAVE handles ETH/WETH internally)
    "COLLATERAL_SUPPLIED": 250000,     # Supply to AAVE (accepts ETH or WETH)
    "COLLATERAL_WITHDRAWN": 220000,    # Withdraw from AAVE 
    "LOAN_CREATED": 300000,            # Borrow "ETH" (unwrapped output)
    "LOAN_REPAID": 280000,             # Repay debt
    
    # Trading Operations
    "TRADE_EXECUTED": 180000,
    "ADD_LIQUIDITY_V3": 350000,
    "VENUE_TRANSFER": 100000,
    
    # Protocol-Specific
    "CREATE_LST": 150000,
    "REDEEM_LST": 200000,
    
    # Atomic Flash Loan Operations (Instadapp-style)
    "ATOMIC_ENTRY": 1250000,           # Flash + stake + supply + borrow + repay (one tx)
    "ATOMIC_DELEVERAGE_ONE_SWAP": 850000,  # Flash + repay + withdraw + swap + repay flash
    "ATOMIC_DELEVERAGE_TWO_SWAPS": 1100000, # Same but with weETH→WETH + WETH→USDT swaps
    
    # One-Time Setup Operations
    "APPROVAL_ONCE": 55000,            # First ERC-20 approve (0 → non-0)
    "SET_EMODE_ONCE": 55000,           # Set AAVE eMode (one-time at start)
}


def load_gas_data(gas_file_path, start_date=None, end_date=None):
    """
    Load gas price data from CSV file with optional date coverage validation.
    
    Args:
        gas_file_path: Path to gas data CSV file
        start_date: Optional start date for coverage validation (YYYY-MM-DD)
        end_date: Optional end date for coverage validation (YYYY-MM-DD)
        
    Returns:
        DataFrame with gas price data
        
    Raises:
        ValueError: If required date coverage is not available
    """
    print(f"Loading gas price data from {gas_file_path}")
    
    try:
        gas_df = pd.read_csv(gas_file_path)
        
        if len(gas_df) == 0:
            raise ValueError(f"No gas data found in {gas_file_path}")
        
        # Convert timestamp to datetime
        gas_df['timestamp'] = pd.to_datetime(gas_df['timestamp'])
        gas_df.set_index('timestamp', inplace=True)
        
        # Validate date coverage if requested
        if start_date and end_date:
            validate_gas_data_coverage(gas_df, start_date, end_date)
        
        # Calculate effective gas price (base fee + priority fee p50)
        if 'base_fee_gwei' in gas_df.columns and 'priority_fee_p50_gwei' in gas_df.columns:
            gas_df['effective_price_gwei'] = gas_df['base_fee_gwei'] + gas_df['priority_fee_p50_gwei']
        elif 'gas_price_gwei' in gas_df.columns:
            gas_df['effective_price_gwei'] = gas_df['gas_price_gwei']
        else:
            raise ValueError("Gas data must contain either 'gas_price_gwei' or both 'base_fee_gwei' and 'priority_fee_p50_gwei'")
        
        print(f"Loaded {len(gas_df)} gas price records")
        return gas_df
        
    except Exception as e:
        print(f"Error loading gas data: {e}")
        sys.exit(1)

def validate_gas_data_coverage(df, start_date, end_date):
    """
    Validate that the gas data covers the required date range.
    
    Args:
        df: DataFrame with timestamp index
        start_date: Required start date (YYYY-MM-DD)
        end_date: Required end date (YYYY-MM-DD)
        
    Raises:
        ValueError: If data coverage is insufficient
    """
    if len(df) == 0:
        raise ValueError("No gas data available")
    
    # Get actual date range from data
    actual_start = df.index.min()
    actual_end = df.index.max()
    
    # Convert requested dates to datetime
    req_start = pd.to_datetime(start_date)
    req_end = pd.to_datetime(end_date)
    
    # Check coverage
    if actual_start > req_start:
        raise ValueError(f"Gas data coverage gap: missing data from {req_start.date()} to {actual_start.date()}")
    
    if actual_end < req_end:
        raise ValueError(f"Gas data coverage gap: missing data from {actual_end.date()} to {req_end.date()}")
    
    print(f"✅ Gas data coverage validated: {actual_start.date()} to {actual_end.date()}")


def load_eth_price_data(eth_price_file_path):
    """Load ETH price data from CSV file."""
    print(f"Loading ETH price data from {eth_price_file_path}")
    
    try:
        # Handle potential CSV format issues with comments
        with open(eth_price_file_path, 'r') as f:
            content = f.read()
            
        # Fix potential newline issues in the file
        fixed_content = content.replace('\\n', '\n')
        
        # Write to a temporary file for processing
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        temp_file.write(fixed_content)
        temp_file.close()
        
        # Count comment lines to skip
        comment_lines = 0
        with open(temp_file.name, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    comment_lines += 1
                else:
                    break
        
        # Read the CSV, skipping comment lines
        df = pd.read_csv(temp_file.name, skiprows=comment_lines)
        
        # Clean up temp file
        import os
        os.unlink(temp_file.name)
        
        # Process the dataframe
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        print(f"Loaded {len(df)} ETH price records")
        return df
        
    except Exception as e:
        print(f"Error loading ETH price data: {e}")
        sys.exit(1)


def calculate_operation_costs(gas_df, eth_price_df=None):
    """
    Calculate gas costs in ETH and optionally USD for all operations.
    Uses effective_price_gwei (base_fee + priority_fee_p50) for calculation.
    """
    print("Calculating operation costs...")
    
    # Convert Gwei to Wei (1 Gwei = 10^9 Wei)
    gas_df['effective_price_wei'] = gas_df['effective_price_gwei'] * 1e9
    
    # Calculate costs for each operation in all units
    for op, gas_units in OPERATION_GAS_UNITS.items():
        # Gwei costs (gas units × gas price in Gwei)
        gas_df[f'{op}_gwei'] = gas_df['effective_price_gwei'] * gas_units
        
        # ETH costs (gas units × gas price in Wei) / 1e18
        gas_df[f'{op}_eth'] = gas_df['effective_price_wei'] * gas_units / 1e18
    
    # If ETH price data is provided, calculate USD costs
    if eth_price_df is not None:
        # Resample ETH price data to match gas data frequency (hourly)
        # Use 'close' price for ETH/USDT
        eth_price_hourly = eth_price_df['close'].resample('H').mean().ffill().bfill()
        
        # Align timestamps and merge
        # Ensure both dataframes have timezone-aware indices for accurate merging
        if gas_df.index.tz is None:
            gas_df.index = gas_df.index.tz_localize('UTC')
        if eth_price_hourly.index.tz is None:
            eth_price_hourly.index = eth_price_hourly.index.tz_localize('UTC')
        
        gas_df = gas_df.merge(eth_price_hourly.rename('eth_price_usd'), 
                              left_index=True, right_index=True, how='left')
        
        # Fill any missing ETH prices (shouldn't happen if ranges overlap)
        gas_df['eth_price_usd'] = gas_df['eth_price_usd'].ffill().bfill()
        
        # Calculate USD costs for each operation
        for op, _ in OPERATION_GAS_UNITS.items():
            gas_df[f'{op}_usd'] = gas_df[f'{op}_eth'] * gas_df['eth_price_usd']
    
    print(f"Calculated costs for {len(OPERATION_GAS_UNITS)} operations across {len(gas_df)} time periods")
    return gas_df


def analyze_gas_data(gas_cost_df):
    """Analyze gas price data and operation costs."""
    print("\n📊 Gas Price Analysis:")
    
    # Gas price statistics
    gas_stats = {
        "min_gwei": gas_cost_df['effective_price_gwei'].min(),
        "max_gwei": gas_cost_df['effective_price_gwei'].max(),
        "mean_gwei": gas_cost_df['effective_price_gwei'].mean(),
        "median_gwei": gas_cost_df['effective_price_gwei'].median(),
        "p95_gwei": gas_cost_df['effective_price_gwei'].quantile(0.95),
    }
    
    print(f"  Min Gas Price: {gas_stats['min_gwei']:.1f} Gwei")
    print(f"  Max Gas Price: {gas_stats['max_gwei']:.1f} Gwei")
    print(f"  Mean Gas Price: {gas_stats['mean_gwei']:.1f} Gwei")
    print(f"  Median Gas Price: {gas_stats['median_gwei']:.1f} Gwei")
    print(f"  95th Percentile: {gas_stats['p95_gwei']:.1f} Gwei")
    
    # ETH price statistics if available
    if 'eth_price_usd' in gas_cost_df.columns:
        eth_stats = {
            "min_usd": gas_cost_df['eth_price_usd'].min(),
            "max_usd": gas_cost_df['eth_price_usd'].max(),
            "mean_usd": gas_cost_df['eth_price_usd'].mean(),
        }
        print(f"\n💰 ETH Price Range: ${eth_stats['min_usd']:.2f} - ${eth_stats['max_usd']:.2f} (avg: ${eth_stats['mean_usd']:.2f})")
    
    # Operation cost analysis
    print("\n⛽ Operation Cost Analysis (at median gas price):")
    
    median_gas = gas_stats['median_gwei']
    median_eth_price = gas_cost_df['eth_price_usd'].median() if 'eth_price_usd' in gas_cost_df.columns else 3300
    
    # Sort operations by gas units (most expensive first)
    sorted_ops = sorted(OPERATION_GAS_UNITS.items(), key=lambda x: x[1], reverse=True)
    
    print("\n| Operation | Gas Units | ETH Cost | USD Cost |")
    print("|-----------|-----------|----------|----------|")
    
    for op, gas_units in sorted_ops:
        eth_cost = (gas_units * median_gas * 1e9) / 1e18
        usd_cost = eth_cost * median_eth_price
        
        print(f"| {op} | {gas_units:,} | {eth_cost:.6f} | ${usd_cost:.2f} |")
    
    # Calculate strategy gas costs
    print("\n🔄 Strategy Gas Cost Analysis:")
    
    strategy_ops = {
        "Pure Lending": ["COLLATERAL_SUPPLIED", "LOAN_CREATED"],
        "Basic Staking": ["STAKE_DEPOSIT", "COLLATERAL_SUPPLIED", "LOAN_CREATED"],
        "Leveraged Staking (3 loops)": ["STAKE_DEPOSIT", "COLLATERAL_SUPPLIED", "LOAN_CREATED"] * 3 + ["LOAN_REPAID"],
        "Combined Leveraged": ["STAKE_DEPOSIT", "COLLATERAL_SUPPLIED", "LOAN_CREATED"] * 3 + 
                              ["TRADE_EXECUTED", "LOAN_REPAID", "COLLATERAL_WITHDRAWN", "STAKE_WITHDRAWAL"],
    }
    
    print("\n| Strategy | Operations | Total Gas | ETH Cost | USD Cost |")
    print("|----------|------------|-----------|----------|----------|")
    
    for strategy, ops in strategy_ops.items():
        total_gas = sum(OPERATION_GAS_UNITS[op] for op in ops)
        eth_cost = (total_gas * median_gas * 1e9) / 1e18
        usd_cost = eth_cost * median_eth_price
        
        print(f"| {strategy} | {len(ops)} | {total_gas:,} | {eth_cost:.6f} | ${usd_cost:.2f} |")
    
    return {
        "gas_stats": gas_stats,
        "eth_stats": eth_stats if 'eth_price_usd' in gas_cost_df.columns else None,
    }


def generate_cost_report(gas_cost_df, output_dir):
    """Generate a detailed cost report and save to CSV."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract date range from dataframe
    start_date = gas_cost_df.index.min().strftime('%Y-%m-%d')
    end_date = gas_cost_df.index.max().strftime('%Y-%m-%d')
    
    # Save enhanced gas prices CSV (with operation costs per hour in all units)
    enhanced_file = os.path.join(output_dir, f"ethereum_gas_prices_enhanced_{start_date}_{end_date}.csv")
    gas_cost_df.to_csv(enhanced_file)
    print(f"\n✅ Saved enhanced gas prices to {enhanced_file}")
    print(f"   📊 Includes: Gwei costs, ETH costs, USD costs for all operations")
    
    # Generate summary report
    summary = {
        "date_range": f"{start_date} to {end_date}",
        "total_records": len(gas_cost_df),
        "gas_price_stats": {
            "min_gwei": float(gas_cost_df['effective_price_gwei'].min()),
            "max_gwei": float(gas_cost_df['effective_price_gwei'].max()),
            "mean_gwei": float(gas_cost_df['effective_price_gwei'].mean()),
            "median_gwei": float(gas_cost_df['effective_price_gwei'].median()),
            "p95_gwei": float(gas_cost_df['effective_price_gwei'].quantile(0.95)),
        },
        "operation_costs": {}
    }
    
    # Add ETH price stats if available
    if 'eth_price_usd' in gas_cost_df.columns:
        summary["eth_price_stats"] = {
            "min_usd": float(gas_cost_df['eth_price_usd'].min()),
            "max_usd": float(gas_cost_df['eth_price_usd'].max()),
            "mean_usd": float(gas_cost_df['eth_price_usd'].mean()),
            "median_usd": float(gas_cost_df['eth_price_usd'].median()),
        }
    
    # Add operation cost stats
    for op in OPERATION_GAS_UNITS.keys():
        gwei_col = f"{op}_gwei"
        eth_col = f"{op}_eth"
        usd_col = f"{op}_usd"
        
        op_stats = {
            "gas_units": OPERATION_GAS_UNITS[op],
            "gwei_cost": {
                "min": float(gas_cost_df[gwei_col].min()),
                "max": float(gas_cost_df[gwei_col].max()),
                "mean": float(gas_cost_df[gwei_col].mean()),
                "median": float(gas_cost_df[gwei_col].median()),
            },
            "eth_cost": {
                "min": float(gas_cost_df[eth_col].min()),
                "max": float(gas_cost_df[eth_col].max()),
                "mean": float(gas_cost_df[eth_col].mean()),
                "median": float(gas_cost_df[eth_col].median()),
            }
        }
        
        if usd_col in gas_cost_df.columns:
            op_stats["usd_cost"] = {
                "min": float(gas_cost_df[usd_col].min()),
                "max": float(gas_cost_df[usd_col].max()),
                "mean": float(gas_cost_df[usd_col].mean()),
                "median": float(gas_cost_df[usd_col].median()),
            }
        
        summary["operation_costs"][op] = op_stats
    
    # Save summary report as JSON
    summary_file = os.path.join(output_dir, f"operation_gas_costs_summary_{start_date}_{end_date}.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Saved summary report to {summary_file}")
    
    return enhanced_file, summary_file


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Analyze gas costs for DeFi operations')
    parser.add_argument('--gas-file', type=str, default='data/blockchain_data/gas_prices/ethereum_gas_prices_2024-01-01_2025-09-24.csv',
                        help='Path to gas price data CSV')
    parser.add_argument('--eth-price-file', type=str, default='data/market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_2020-01-01_2025-09-26.csv',
                        help='Path to ETH price data CSV')
    parser.add_argument('--output-dir', type=str, default='data/blockchain_data/gas_prices',
                        help='Directory to save output files')
    parser.add_argument('--date-range', type=str, default=None,
                        help='Date range to analyze (format: YYYY-MM-DD,YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # Load gas price data
    gas_df = load_gas_data(args.gas_file)
    
    # Load ETH price data if provided
    eth_price_df = None
    if args.eth_price_file:
        eth_price_df = load_eth_price_data(args.eth_price_file)
    
    # Filter by date range if provided
    if args.date_range:
        start_date, end_date = args.date_range.split(',')
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        # Ensure timezone consistency
        if gas_df.index.tz is not None:
            start_date = start_date.tz_localize(gas_df.index.tz)
            end_date = end_date.tz_localize(gas_df.index.tz)
        gas_df = gas_df.loc[start_date:end_date]
        if eth_price_df is not None:
            if eth_price_df.index.tz is not None:
                start_date = start_date.tz_localize(eth_price_df.index.tz) if start_date.tz is None else start_date
                end_date = end_date.tz_localize(eth_price_df.index.tz) if end_date.tz is None else end_date
            eth_price_df = eth_price_df.loc[start_date:end_date]
    
    # Calculate operation costs
    gas_cost_df = calculate_operation_costs(gas_df, eth_price_df)
    
    # Analyze gas data
    analysis = analyze_gas_data(gas_cost_df)
    
    # Generate and save report
    enhanced_file, summary_file = generate_cost_report(gas_cost_df, args.output_dir)
    
    print("\n🚀 Analysis complete!")
    print(f"🔧 Enhanced gas prices: {enhanced_file}")
    print(f"📑 Summary report: {summary_file}")


def run_gas_cost_analysis(gas_file_path, eth_price_file_path, output_dir, start_date=None, end_date=None):
    """
    Run gas cost analysis programmatically.
    
    Args:
        gas_file_path: Path to gas price data CSV
        eth_price_file_path: Path to ETH price data CSV
        output_dir: Output directory
        start_date: Start date for filtering (optional)
        end_date: End date for filtering (optional)
        
    Returns:
        Tuple of (output_file, summary_file, enhanced_file)
    """
    # Load gas price data
    gas_df = load_gas_data(gas_file_path)
    
    # Load ETH price data if provided
    eth_price_df = None
    if eth_price_file_path:
        eth_price_df = load_eth_price_data(eth_price_file_path)
    
    # Filter by date range if provided
    if start_date and end_date:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        # Ensure timezone consistency
        if gas_df.index.tz is not None:
            start_date = start_date.tz_localize(gas_df.index.tz)
            end_date = end_date.tz_localize(gas_df.index.tz)
        gas_df = gas_df.loc[start_date:end_date]
        if eth_price_df is not None:
            if eth_price_df.index.tz is not None:
                start_date = start_date.tz_localize(eth_price_df.index.tz) if start_date.tz is None else start_date
                end_date = end_date.tz_localize(eth_price_df.index.tz) if end_date.tz is None else end_date
            eth_price_df = eth_price_df.loc[start_date:end_date]
    
    # Calculate operation costs
    gas_cost_df = calculate_operation_costs(gas_df, eth_price_df)
    
    # Generate and save report
    enhanced_file, summary_file = generate_cost_report(gas_cost_df, output_dir)
    
    return enhanced_file, summary_file


if __name__ == "__main__":
    main()
