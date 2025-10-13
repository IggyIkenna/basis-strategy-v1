#!/usr/bin/env python3
"""
ML Mock Data Generation Script

Generates comprehensive mock ML prediction data for BTC and USDT strategies
from January 2020 to October 13, 2025, using new format with standard deviation.

Usage:
    python scripts/generate_ml_mock_data.py

Output:
    - data/market_data/ml/binance_BTCUSDT_perp_5m_2020-01-01_2025-10-13.csv
    - data/ml_data/predictions/btc_predictions.csv
    - data/ml_data/predictions/usdt_predictions.csv
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple
import random
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MLDataGenerator:
    """Generate mock ML prediction data for backtesting."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.start_date = datetime(2020, 1, 1)
        self.end_date = datetime(2025, 10, 13)
        self.interval_minutes = 5
        
        # Signal distribution
        self.signal_distribution = {
            'long': 0.40,
            'short': 0.30,
            'neutral': 0.30
        }
        
        # Confidence ranges by signal type
        self.confidence_ranges = {
            'long': (0.65, 0.95),
            'short': (0.65, 0.95),
            'neutral': (0.30, 0.60)
        }
        
        # Standard deviation ranges (as percentage of price)
        self.sd_ranges = {
            'normal': (0.01, 0.03),    # 1-3%
            'high_vol': (0.03, 0.05),  # 3-5%
            'low_vol': (0.005, 0.015)  # 0.5-1.5%
        }
        
        # Signal persistence (number of 5-min periods)
        self.signal_persistence = {
            'long': (5, 30),    # 25 min - 2.5 hours
            'short': (5, 30),
            'neutral': (3, 15)  # 15 min - 1.25 hours
        }
    
    def load_hourly_data(self) -> pd.DataFrame:
        """Load existing hourly futures data."""
        file_path = os.path.join(
            self.data_dir, 
            "market_data/derivatives/futures_ohlcv/binance_BTCUSDT_perp_1h_2024-01-01_2025-09-30.csv"
        )
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Hourly data file not found: {file_path}")
        
        logger.info(f"Loading hourly data from {file_path}")
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)  # Remove timezone info
        
        # Extend data to cover full period (2020-2025)
        # For 2020-2023, we'll use synthetic data based on 2024 patterns
        extended_df = self._extend_data_to_full_period(df)
        
        return extended_df
    
    def _extend_data_to_full_period(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extend hourly data to cover full 2020-2025 period."""
        logger.info("Extending data to cover full period 2020-2025")
        
        # Get price range from existing data
        min_price = df['close'].min()
        max_price = df['close'].max()
        avg_price = df['close'].mean()
        
        # Create synthetic data for 2020-2023
        synthetic_data = []
        current_date = self.start_date
        current_price = avg_price * 0.3  # Start lower for 2020
        
        # Calculate total hours for progress bar
        total_hours = int((datetime(2024, 1, 1) - self.start_date).total_seconds() / 3600)
        
        with tqdm(total=total_hours, desc="Generating synthetic data 2020-2023", unit="hours") as pbar:
            while current_date < datetime(2024, 1, 1):
                # Generate realistic price movement
                price_change = np.random.normal(0, 0.02)  # 2% daily volatility
                current_price *= (1 + price_change)
                current_price = max(min_price * 0.5, min(max_price * 1.5, current_price))
                
                # Generate OHLCV
                high = current_price * (1 + abs(np.random.normal(0, 0.01)))
                low = current_price * (1 - abs(np.random.normal(0, 0.01)))
                volume = np.random.uniform(100, 1000)
                
                synthetic_data.append({
                    'timestamp': current_date,
                    'open': current_price,
                    'high': high,
                    'low': low,
                    'close': current_price,
                    'volume': volume,
                    'quote_volume': volume * current_price,
                    'trades_count': np.random.randint(1000, 10000),
                    'source': 'binance_futures',
                    'symbol': 'BTCUSDT',
                    'data_type': 'futures'
                })
                
                current_date += timedelta(hours=1)
                pbar.update(1)
        
        # Combine synthetic and real data
        synthetic_df = pd.DataFrame(synthetic_data)
        full_df = pd.concat([synthetic_df, df], ignore_index=True)
        full_df = full_df.sort_values('timestamp').reset_index(drop=True)
        
        logger.info(f"Extended data: {len(full_df)} hourly records from {full_df['timestamp'].min()} to {full_df['timestamp'].max()}")
        return full_df
    
    def interpolate_to_5min(self, hourly_df: pd.DataFrame) -> pd.DataFrame:
        """Interpolate hourly data to 5-minute intervals."""
        logger.info("Interpolating hourly data to 5-minute intervals")
        
        # Create 5-minute timestamps
        timestamps = pd.date_range(
            start=self.start_date,
            end=self.end_date,
            freq=f'{self.interval_minutes}min'
        )
        
        # Create base DataFrame with timestamps
        df_5min = pd.DataFrame({'timestamp': timestamps})
        
        # Merge with hourly data and interpolate
        hourly_df_clean = hourly_df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
        
        # Forward fill hourly data to 5-minute intervals
        df_5min = df_5min.merge(hourly_df_clean, on='timestamp', how='left')
        df_5min = df_5min.fillna(method='ffill')
        
        # Add realistic intra-hour price movements
        df_5min = self._add_intra_hour_movements(df_5min)
        
        logger.info(f"Generated {len(df_5min)} 5-minute records")
        return df_5min
    
    def _add_intra_hour_movements(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add realistic intra-hour price movements."""
        logger.info("Adding realistic intra-hour price movements")
        
        # Group by hour and add movements within each hour
        df['hour'] = df['timestamp'].dt.floor('H')
        
        hour_groups = list(df.groupby('hour'))
        with tqdm(hour_groups, desc="Adding intra-hour movements", unit="hours") as pbar:
            for hour, group in pbar:
                if len(group) < 2:
                    continue
                
            # Get hourly OHLC
            hour_open = group['open'].iloc[0]
            hour_high = group['high'].iloc[0]
            hour_low = group['low'].iloc[0]
            hour_close = group['close'].iloc[0]
            
            # Generate 5-minute prices within the hourly range
            n_periods = len(group)
            prices = np.linspace(hour_open, hour_close, n_periods)
            
            # Add some randomness while staying within hourly range
            for i, (idx, row) in enumerate(group.iterrows()):
                if i == 0:
                    df.loc[idx, 'open'] = hour_open
                else:
                    # Random walk within hourly range
                    price_change = np.random.normal(0, 0.001)  # 0.1% volatility
                    new_price = prices[i] * (1 + price_change)
                    new_price = max(hour_low, min(hour_high, new_price))
                    df.loc[idx, 'open'] = new_price
                
                # Set close price
                if i == n_periods - 1:
                    df.loc[idx, 'close'] = hour_close
                else:
                    close_change = np.random.normal(0, 0.0005)
                    close_price = df.loc[idx, 'open'] * (1 + close_change)
                    close_price = max(hour_low, min(hour_high, close_price))
                    df.loc[idx, 'close'] = close_price
                
                # Set high and low
                open_price = df.loc[idx, 'open']
                close_price = df.loc[idx, 'close']
                high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.0005)))
                low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.0005)))
                
                df.loc[idx, 'high'] = min(high_price, hour_high)
                df.loc[idx, 'low'] = max(low_price, hour_low)
                
                # Distribute volume
                df.loc[idx, 'volume'] = group['volume'].iloc[0] / n_periods
        
        # Clean up
        df = df.drop('hour', axis=1)
        return df
    
    def generate_ml_predictions(self, ohlcv_df: pd.DataFrame) -> pd.DataFrame:
        """Generate ML predictions based on OHLCV data."""
        logger.info("Generating ML predictions")
        
        predictions = []
        current_signal = 'neutral'
        signal_persistence = 0
        current_confidence = 0.5
        
        with tqdm(ohlcv_df.iterrows(), total=len(ohlcv_df), desc="Generating ML predictions", unit="records") as pbar:
            for idx, row in pbar:
                timestamp = row['timestamp']
                price = row['close']
                
                # Check if we need to generate a new signal
                if signal_persistence <= 0:
                    # Generate new signal
                    current_signal = self._generate_signal(price, ohlcv_df, idx)
                    current_confidence = self._generate_confidence(current_signal)
                    signal_persistence = self._get_signal_persistence(current_signal, current_confidence)
                else:
                    signal_persistence -= 1
                
                # Generate standard deviation
                sd = self._generate_standard_deviation(price, current_confidence, ohlcv_df, idx)
                
                predictions.append({
                    'timestamp': timestamp,
                    'signal': current_signal,
                    'confidence': current_confidence,
                    'sd': sd
                })
        
        return pd.DataFrame(predictions)
    
    def _generate_signal(self, price: float, df: pd.DataFrame, idx: int) -> str:
        """Generate trading signal based on price action and randomness."""
        # 70% random, 30% based on price trend
        if np.random.random() < 0.7:
            # Random signal based on distribution
            rand = np.random.random()
            if rand < self.signal_distribution['long']:
                return 'long'
            elif rand < self.signal_distribution['long'] + self.signal_distribution['short']:
                return 'short'
            else:
                return 'neutral'
        else:
            # Trend-based signal
            if idx < 12:  # Need at least 1 hour of data
                return 'neutral'
            
            # Calculate 1-hour price change
            hour_ago_price = df.iloc[idx - 12]['close']
            price_change = (price - hour_ago_price) / hour_ago_price
            
            if price_change > 0.02:  # 2% up
                return 'long'
            elif price_change < -0.02:  # 2% down
                return 'short'
            else:
                return 'neutral'
    
    def _generate_confidence(self, signal: str) -> float:
        """Generate confidence level for signal."""
        min_conf, max_conf = self.confidence_ranges[signal]
        return np.random.uniform(min_conf, max_conf)
    
    def _get_signal_persistence(self, signal: str, confidence: float) -> int:
        """Get signal persistence based on signal type and confidence."""
        min_persist, max_persist = self.signal_persistence[signal]
        # Higher confidence = longer persistence
        confidence_factor = (confidence - 0.3) / 0.7  # Normalize to 0-1
        persistence = min_persist + (max_persist - min_persist) * confidence_factor
        return int(persistence)
    
    def _generate_standard_deviation(self, price: float, confidence: float, df: pd.DataFrame, idx: int) -> float:
        """Generate standard deviation based on confidence and market conditions."""
        # Higher confidence = lower SD
        confidence_factor = 1 - ((confidence - 0.3) / 0.7)  # Invert confidence
        
        # Check for high volatility periods
        if idx >= 12:  # Need at least 1 hour of data
            recent_prices = df.iloc[idx-12:idx]['close']
            volatility = recent_prices.pct_change().std()
            
            if volatility > 0.03:  # High volatility
                sd_range = self.sd_ranges['high_vol']
            elif volatility < 0.01:  # Low volatility
                sd_range = self.sd_ranges['low_vol']
            else:
                sd_range = self.sd_ranges['normal']
        else:
            sd_range = self.sd_ranges['normal']
        
        # Generate SD with confidence adjustment
        base_sd = np.random.uniform(sd_range[0], sd_range[1])
        adjusted_sd = base_sd * (0.5 + 0.5 * confidence_factor)
        
        return round(adjusted_sd, 4)
    
    def save_data(self, ohlcv_df: pd.DataFrame, predictions_df: pd.DataFrame):
        """Save generated data to files."""
        logger.info("Saving generated data")
        
        # Create directories if they don't exist
        os.makedirs(os.path.join(self.data_dir, "market_data/ml"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "ml_data/predictions"), exist_ok=True)
        
        # Save OHLCV data
        ohlcv_file = os.path.join(
            self.data_dir, 
            "market_data/ml/binance_BTCUSDT_perp_5m_2020-01-01_2025-10-13.csv"
        )
        ohlcv_df.to_csv(ohlcv_file, index=False)
        logger.info(f"Saved OHLCV data: {ohlcv_file}")
        
        # Save BTC predictions
        btc_file = os.path.join(self.data_dir, "ml_data/predictions/btc_predictions.csv")
        predictions_df.to_csv(btc_file, index=False)
        logger.info(f"Saved BTC predictions: {btc_file}")
        
        # Save USDT predictions (same as BTC for USDT-margined BTC perps)
        usdt_file = os.path.join(self.data_dir, "ml_data/predictions/usdt_predictions.csv")
        predictions_df.to_csv(usdt_file, index=False)
        logger.info(f"Saved USDT predictions: {usdt_file}")
        
        # Print summary
        logger.info(f"Data generation complete!")
        logger.info(f"  - OHLCV records: {len(ohlcv_df):,}")
        logger.info(f"  - Prediction records: {len(predictions_df):,}")
        logger.info(f"  - Time period: {ohlcv_df['timestamp'].min()} to {ohlcv_df['timestamp'].max()}")
        logger.info(f"  - Signal distribution: {predictions_df['signal'].value_counts().to_dict()}")
    
    def run(self):
        """Run the complete data generation process."""
        logger.info("Starting ML mock data generation")
        
        try:
            # Load and process hourly data
            hourly_df = self.load_hourly_data()
            ohlcv_df = self.interpolate_to_5min(hourly_df)
            
            # Generate ML predictions
            predictions_df = self.generate_ml_predictions(ohlcv_df)
            
            # Save data
            self.save_data(ohlcv_df, predictions_df)
            
            logger.info("ML mock data generation completed successfully!")
            
        except Exception as e:
            logger.error(f"Error generating ML mock data: {e}")
            raise


def main():
    """Main entry point."""
    generator = MLDataGenerator()
    generator.run()


if __name__ == "__main__":
    main()
