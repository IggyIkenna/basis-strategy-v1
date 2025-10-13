#!/usr/bin/env python3
"""
Simple ML Mock Data Generation Script

Quickly generates mock ML prediction data for BTC and USDT strategies
from January 2020 to October 13, 2025, using random price data.

Usage:
    python scripts/generate_ml_mock_data_simple.py
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from tqdm import tqdm

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_simple_ml_data():
    """Generate simple ML mock data quickly."""
    logger.info("Starting simple ML mock data generation")
    
    # Create directories
    os.makedirs("data/market_data/ml", exist_ok=True)
    os.makedirs("data/ml_data/predictions", exist_ok=True)
    
    # Generate 5-minute timestamps from 2020-01-01 to 2025-10-13
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 10, 13)
    timestamps = pd.date_range(start=start_date, end=end_date, freq='5min')
    
    logger.info(f"Generating {len(timestamps):,} 5-minute records")
    
    # Generate random price data
    base_price = 50000  # Start at $50k BTC
    prices = []
    current_price = base_price
    
    with tqdm(total=len(timestamps), desc="Generating price data", unit="records") as pbar:
        for i, timestamp in enumerate(timestamps):
            # Random walk with some trend
            change = np.random.normal(0, 0.001)  # 0.1% volatility
            current_price *= (1 + change)
            
            # Keep price in reasonable range
            current_price = max(1000, min(200000, current_price))
            
            # Generate OHLCV
            open_price = current_price
            high = open_price * (1 + abs(np.random.normal(0, 0.005)))
            low = open_price * (1 - abs(np.random.normal(0, 0.005)))
            close = open_price * (1 + np.random.normal(0, 0.002))
            volume = np.random.uniform(10, 100)
            
            prices.append({
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close, 2),
                'volume': round(volume, 2)
            })
            
            current_price = close
            pbar.update(1)
    
    # Create OHLCV DataFrame
    ohlcv_df = pd.DataFrame(prices)
    
    # Generate ML predictions
    logger.info("Generating ML predictions")
    predictions = []
    current_signal = 'neutral'
    signal_persistence = 0
    current_confidence = 0.5
    
    with tqdm(total=len(ohlcv_df), desc="Generating ML predictions", unit="records") as pbar:
        for idx, row in ohlcv_df.iterrows():
            # Check if we need to generate a new signal
            if signal_persistence <= 0:
                # Random signal distribution: 40% long, 30% short, 30% neutral
                rand = np.random.random()
                if rand < 0.4:
                    current_signal = 'long'
                    current_confidence = np.random.uniform(0.65, 0.95)
                elif rand < 0.7:
                    current_signal = 'short'
                    current_confidence = np.random.uniform(0.65, 0.95)
                else:
                    current_signal = 'neutral'
                    current_confidence = np.random.uniform(0.30, 0.60)
                
                # Signal persistence: 5-30 periods (25 min - 2.5 hours)
                signal_persistence = np.random.randint(5, 31)
            else:
                signal_persistence -= 1
            
            # Generate standard deviation (1-3% of price)
            sd = np.random.uniform(0.01, 0.03)
            
            predictions.append({
                'timestamp': row['timestamp'],
                'signal': current_signal,
                'confidence': round(current_confidence, 3),
                'sd': round(sd, 4)
            })
            
            pbar.update(1)
    
    predictions_df = pd.DataFrame(predictions)
    
    # Save data
    logger.info("Saving data files")
    
    # Save OHLCV data
    ohlcv_file = "data/market_data/ml/binance_BTCUSDT_perp_5m_2020-01-01_2025-10-13.csv"
    ohlcv_df.to_csv(ohlcv_file, index=False)
    logger.info(f"Saved OHLCV data: {ohlcv_file}")
    
    # Save BTC predictions
    btc_file = "data/ml_data/predictions/btc_predictions.csv"
    predictions_df.to_csv(btc_file, index=False)
    logger.info(f"Saved BTC predictions: {btc_file}")
    
    # Save USDT predictions (same as BTC for USDT-margined BTC perps)
    usdt_file = "data/ml_data/predictions/usdt_predictions.csv"
    predictions_df.to_csv(usdt_file, index=False)
    logger.info(f"Saved USDT predictions: {usdt_file}")
    
    # Print summary
    logger.info(f"Data generation complete!")
    logger.info(f"  - OHLCV records: {len(ohlcv_df):,}")
    logger.info(f"  - Prediction records: {len(predictions_df):,}")
    logger.info(f"  - Time period: {ohlcv_df['timestamp'].min()} to {ohlcv_df['timestamp'].max()}")
    logger.info(f"  - Signal distribution: {predictions_df['signal'].value_counts().to_dict()}")
    
    return ohlcv_df, predictions_df


if __name__ == "__main__":
    generate_simple_ml_data()
