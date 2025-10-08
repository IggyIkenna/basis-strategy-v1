#!/usr/bin/env python3
"""
Proper AAVE Hourly Interpolation

Implements the correct mathematical approach for hourly interpolation:
1. Interpolate indices (liquidityIndex, variableBorrowIndex) between 24-hour periods
2. Calculate hourly APY from index ratios between consecutive hours
3. Convert to continuously compounded APR using natural logs
4. Keep current rates as snapshots (already continuously compounded)
5. Linearly interpolate totalVariableDebt and totalAToken
6. Drop unused columns (stable rates/debt)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime

def proper_hourly_interpolation():
    """Implement proper hourly interpolation with correct math for all assets."""
    
    # Process all available AAVE rate files
    rates_dir = Path("data/protocol_data/aave/rates")
    if not rates_dir.exists():
        print(f"❌ Rates directory not found: {rates_dir}")
        return
    
    # Find all AAVE rate files (excluding hourly and RAW files)
    rate_files = list(rates_dir.glob("aave_v3_aave-v3-ethereum_*_rates_*.csv"))
    rate_files = [f for f in rate_files if not f.name.endswith('_hourly.csv') and not f.name.endswith('_RAW.csv')]
    
    if not rate_files:
        print(f"❌ No AAVE rate files found in {rates_dir}")
        return
    
    print(f"🔍 Found {len(rate_files)} AAVE rate files to process")
    
    for data_file in rate_files:
        print(f"\n{'='*80}")
        print(f"📊 PROCESSING: {data_file.name}")
        print(f"{'='*80}")
        
        process_single_asset(data_file)
    
    print(f"\n🎯 ALL ASSETS PROCESSED SUCCESSFULLY!")
    print(f"📊 Processed {len(rate_files)} AAVE rate files")
    print(f"📁 Output directory: {rates_dir}")

def process_single_asset(data_file: Path):
    """Process a single AAVE asset file with proper hourly interpolation."""
    
    print(f"🔍 Loading {data_file.name}...")
    df = pd.read_csv(data_file)
    
    # Convert timestamps
    if 'targetDate' in df.columns:
        df['timestamp'] = pd.to_datetime(df['targetDate'])
    else:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Convert numeric columns
    numeric_cols = [
        'liquidityIndex', 'currentLiquidityRate', 'variableBorrowIndex', 
        'currentVariableBorrowRate', 'totalAToken', 'totalVariableDebt',
        'currentStableBorrowRate', 'totalStableDebt', 'price'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    print(f"📅 Original data: {len(df)} daily records")
    print(f"📅 Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    # Step 1: Create hourly timestamp range
    start_time = df['timestamp'].min()
    end_time = df['timestamp'].max()
    hourly_range = pd.date_range(start=start_time, end=end_time, freq='H')
    
    print(f"📊 Hourly timestamps: {len(hourly_range)} hours")
    print(f"📊 Interpolation ratio: {len(hourly_range) / len(df):.1f}x")
    
    # Step 2: Create hourly DataFrame with interpolated indices
    df_hourly = pd.DataFrame({'timestamp': hourly_range})
    
    # Merge with original data
    df_hourly = df_hourly.merge(df[['timestamp', 'liquidityIndex', 'variableBorrowIndex']], 
                                on='timestamp', how='left')
    
    # Interpolate indices (these are cumulative, so linear interpolation is appropriate)
    df_hourly['liquidityIndex'] = df_hourly['liquidityIndex'].interpolate(method='linear')
    df_hourly['variableBorrowIndex'] = df_hourly['variableBorrowIndex'].interpolate(method='linear')
    
    # Step 3: Calculate hourly APY from index ratios
    df_hourly['liquidity_growth_factor'] = df_hourly['liquidityIndex'] / df_hourly['liquidityIndex'].shift(1)
    df_hourly['borrow_growth_factor'] = df_hourly['variableBorrowIndex'] / df_hourly['variableBorrowIndex'].shift(1)
    
    # Calculate hourly APY (annualized from 1-hour period)
    df_hourly['liquidity_apy_hourly'] = (df_hourly['liquidity_growth_factor'] ** (365 * 24)) - 1
    df_hourly['borrow_apy_hourly'] = (df_hourly['borrow_growth_factor'] ** (365 * 24)) - 1
    
    # Convert to continuously compounded APR
    df_hourly['liquidity_ccr_hourly'] = np.log(1 + df_hourly['liquidity_apy_hourly'])
    df_hourly['borrow_ccr_hourly'] = np.log(1 + df_hourly['borrow_apy_hourly'])
    
    # Step 4: Add current rates as snapshots
    df_hourly = df_hourly.merge(df[['timestamp', 'currentLiquidityRate', 'currentVariableBorrowRate']], 
                                on='timestamp', how='left')
    
    # Forward fill current rates (they represent the rate at that point in time)
    df_hourly['currentLiquidityRate'] = df_hourly['currentLiquidityRate'].ffill()
    df_hourly['currentVariableBorrowRate'] = df_hourly['currentVariableBorrowRate'].ffill()
    
    # Step 5: Interpolate debt and supply amounts
    df_hourly = df_hourly.merge(df[['timestamp', 'totalAToken', 'totalVariableDebt']], 
                                on='timestamp', how='left')
    
    # Linear interpolation for debt and supply amounts
    df_hourly['totalAToken'] = df_hourly['totalAToken'].interpolate(method='linear')
    df_hourly['totalVariableDebt'] = df_hourly['totalVariableDebt'].interpolate(method='linear')
    
    # Calculate utilization rate
    df_hourly['utilization_rate'] = df_hourly['totalVariableDebt'] / df_hourly['totalAToken']
    
    # Step 6: Add other useful columns
    df_hourly = df_hourly.merge(df[['timestamp', 'price']], on='timestamp', how='left')
    df_hourly['price'] = df_hourly['price'].interpolate(method='linear')
    df_hourly['oracle_price_usd'] = df_hourly['price']
    
    # Add metadata
    df_hourly['date'] = df_hourly['timestamp'].dt.strftime('%Y-%m-%d')
    df_hourly['hour'] = df_hourly['timestamp'].dt.hour
    df_hourly['source'] = 'aave_hourly_interpolated'
    
    # Step 7: Create clean output (drop unused columns)
    output_columns = [
        'timestamp', 'date', 'hour',
        'liquidityIndex', 'variableBorrowIndex',
        'liquidity_growth_factor', 'borrow_growth_factor',
        'liquidity_apy_hourly', 'borrow_apy_hourly',
        'liquidity_ccr_hourly', 'borrow_ccr_hourly',
        'currentLiquidityRate', 'currentVariableBorrowRate',
        'totalAToken', 'totalVariableDebt', 'utilization_rate',
        'oracle_price_usd', 'source'
    ]
    
    df_clean = df_hourly[output_columns].copy()
    
    # Remove first row (NaN values from growth factor calculation)
    df_clean = df_clean.iloc[1:].reset_index(drop=True)
    
    # Step 8: Save hourly interpolated data
    output_dir = data_file.parent
    
    # Save hourly interpolated data
    hourly_file = output_dir / f"{data_file.stem}_hourly.csv"
    df_clean.to_csv(hourly_file, index=False)
    
    print(f"✅ Processed {len(df)} daily → {len(df_clean)} hourly records")
    print(f"📁 File: {hourly_file.name}")
    print(f"📊 Sample CCR rates: {df_clean['liquidity_ccr_hourly'].mean()*100:.4f}% supply, {df_clean['borrow_ccr_hourly'].mean()*100:.4f}% borrow")
    
    return df_clean

if __name__ == "__main__":
    proper_hourly_interpolation()
