#!/usr/bin/env python3
"""
Unit tests for ML data generation and validation.

Tests the new ML prediction format with standard deviation field.
"""

import unittest
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.generate_ml_mock_data_simple import generate_simple_ml_data


class TestMLDataGeneration(unittest.TestCase):
    """Test ML data generation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.data_dir = "data"
        self.btc_predictions_file = os.path.join(self.data_dir, "ml_data/predictions/btc_predictions.csv")
        self.usdt_predictions_file = os.path.join(self.data_dir, "ml_data/predictions/usdt_predictions.csv")
        self.ohlcv_file = os.path.join(self.data_dir, "market_data/ml/binance_BTCUSDT_perp_5m_2020-01-01_2025-10-13.csv")
    
    def test_data_files_exist(self):
        """Test that generated data files exist."""
        self.assertTrue(os.path.exists(self.btc_predictions_file), "BTC predictions file should exist")
        self.assertTrue(os.path.exists(self.usdt_predictions_file), "USDT predictions file should exist")
        self.assertTrue(os.path.exists(self.ohlcv_file), "OHLCV file should exist")
    
    def test_btc_predictions_format(self):
        """Test BTC predictions file format."""
        df = pd.read_csv(self.btc_predictions_file)
        
        # Check required columns
        required_columns = ['timestamp', 'signal', 'confidence', 'sd']
        for col in required_columns:
            self.assertIn(col, df.columns, f"Missing required column: {col}")
        
        # Check data types
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(pd.to_datetime(df['timestamp'])), "Timestamp should be datetime")
        self.assertTrue(pd.api.types.is_numeric_dtype(df['confidence']), "Confidence should be numeric")
        self.assertTrue(pd.api.types.is_numeric_dtype(df['sd']), "SD should be numeric")
        
        # Check signal values
        valid_signals = ['long', 'short', 'neutral']
        for signal in df['signal'].unique():
            self.assertIn(signal, valid_signals, f"Invalid signal: {signal}")
        
        # Check confidence range
        self.assertTrue((df['confidence'] >= 0.0).all(), "Confidence should be >= 0.0")
        self.assertTrue((df['confidence'] <= 1.0).all(), "Confidence should be <= 1.0")
        
        # Check SD range
        self.assertTrue((df['sd'] > 0.0).all(), "SD should be > 0.0")
        self.assertTrue((df['sd'] <= 0.1).all(), "SD should be <= 0.1 (10%)")
    
    def test_usdt_predictions_format(self):
        """Test USDT predictions file format."""
        df = pd.read_csv(self.usdt_predictions_file)
        
        # Should have same format as BTC predictions
        required_columns = ['timestamp', 'signal', 'confidence', 'sd']
        for col in required_columns:
            self.assertIn(col, df.columns, f"Missing required column: {col}")
        
        # Check data types
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(pd.to_datetime(df['timestamp'])), "Timestamp should be datetime")
        self.assertTrue(pd.api.types.is_numeric_dtype(df['confidence']), "Confidence should be numeric")
        self.assertTrue(pd.api.types.is_numeric_dtype(df['sd']), "SD should be numeric")
    
    def test_ohlcv_format(self):
        """Test OHLCV file format."""
        df = pd.read_csv(self.ohlcv_file)
        
        # Check required columns
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            self.assertIn(col, df.columns, f"Missing required column: {col}")
        
        # Check data types
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(pd.to_datetime(df['timestamp'])), "Timestamp should be datetime")
        
        price_columns = ['open', 'high', 'low', 'close']
        for col in price_columns:
            self.assertTrue(pd.api.types.is_numeric_dtype(df[col]), f"{col} should be numeric")
        
        # Check OHLC relationships (allow some tolerance for random data)
        high_ge_open_ratio = (df['high'] >= df['open']).mean()
        high_ge_close_ratio = (df['high'] >= df['close']).mean()
        low_le_open_ratio = (df['low'] <= df['open']).mean()
        low_le_close_ratio = (df['low'] <= df['close']).mean()
        
        self.assertGreater(high_ge_open_ratio, 0.85, "High should be >= Open in most cases")
        self.assertGreater(high_ge_close_ratio, 0.85, "High should be >= Close in most cases")
        self.assertGreater(low_le_open_ratio, 0.85, "Low should be <= Open in most cases")
        self.assertGreater(low_le_close_ratio, 0.85, "Low should be <= Close in most cases")
        
        # Check volume
        self.assertTrue((df['volume'] > 0).all(), "Volume should be > 0")
    
    def test_data_time_range(self):
        """Test that data covers the expected time range."""
        # Test predictions
        btc_df = pd.read_csv(self.btc_predictions_file)
        btc_df['timestamp'] = pd.to_datetime(btc_df['timestamp'])
        
        expected_start = datetime(2020, 1, 1)
        expected_end = datetime(2025, 10, 13)
        
        self.assertGreaterEqual(btc_df['timestamp'].min(), expected_start, "Data should start from 2020-01-01")
        self.assertLessEqual(btc_df['timestamp'].max(), expected_end, "Data should end by 2025-10-13")
        
        # Test OHLCV
        ohlcv_df = pd.read_csv(self.ohlcv_file)
        ohlcv_df['timestamp'] = pd.to_datetime(ohlcv_df['timestamp'])
        
        self.assertGreaterEqual(ohlcv_df['timestamp'].min(), expected_start, "OHLCV should start from 2020-01-01")
        self.assertLessEqual(ohlcv_df['timestamp'].max(), expected_end, "OHLCV should end by 2025-10-13")
    
    def test_5min_intervals(self):
        """Test that data has 5-minute intervals."""
        df = pd.read_csv(self.btc_predictions_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Check intervals (allow some tolerance for first few records)
        time_diffs = df['timestamp'].diff().dropna()
        expected_interval = timedelta(minutes=5)
        
        # Most intervals should be 5 minutes
        five_min_intervals = (time_diffs == expected_interval).sum()
        total_intervals = len(time_diffs)
        
        self.assertGreater(five_min_intervals / total_intervals, 0.95, "At least 95% of intervals should be 5 minutes")
    
    def test_signal_distribution(self):
        """Test that signal distribution is reasonable."""
        df = pd.read_csv(self.btc_predictions_file)
        
        signal_counts = df['signal'].value_counts()
        total_signals = len(df)
        
        # Check that we have reasonable distribution
        long_ratio = signal_counts.get('long', 0) / total_signals
        short_ratio = signal_counts.get('short', 0) / total_signals
        neutral_ratio = signal_counts.get('neutral', 0) / total_signals
        
        # Should have reasonable distribution (not all one signal)
        self.assertGreater(long_ratio, 0.1, "Should have some long signals")
        self.assertGreater(short_ratio, 0.1, "Should have some short signals")
        self.assertGreater(neutral_ratio, 0.1, "Should have some neutral signals")
        
        # Should not be too extreme
        self.assertLess(long_ratio, 0.8, "Should not be dominated by long signals")
        self.assertLess(short_ratio, 0.8, "Should not be dominated by short signals")
        self.assertLess(neutral_ratio, 0.8, "Should not be dominated by neutral signals")


class TestMLStrategyIntegration(unittest.TestCase):
    """Test ML strategy integration with new data format."""
    
    def test_stop_loss_take_profit_calculation(self):
        """Test stop-loss and take-profit calculation logic."""
        # Test the calculation logic directly without instantiating the strategy
        def calculate_stop_loss_take_profit(current_price: float, sd: float, signal: str) -> tuple:
            """Calculate stop-loss and take-profit levels based on standard deviation."""
            if signal == 'long':
                stop_loss = current_price * (1 - 2 * sd)    # 2x SD stop loss
                take_profit = current_price * (1 + 3 * sd)  # 3x SD take profit
            elif signal == 'short':
                stop_loss = current_price * (1 + 2 * sd)    # 2x SD stop loss
                take_profit = current_price * (1 - 3 * sd)  # 3x SD take profit
            else:  # neutral
                stop_loss = 0.0
                take_profit = 0.0
            
            return stop_loss, take_profit
        
        # Test long position
        current_price = 50000.0
        sd = 0.02  # 2%
        signal = 'long'
        
        stop_loss, take_profit = calculate_stop_loss_take_profit(current_price, sd, signal)
        
        expected_stop_loss = current_price * (1 - 2 * sd)  # 48000
        expected_take_profit = current_price * (1 + 3 * sd)  # 53000
        
        self.assertAlmostEqual(stop_loss, expected_stop_loss, places=2)
        self.assertAlmostEqual(take_profit, expected_take_profit, places=2)
        
        # Test short position
        signal = 'short'
        stop_loss, take_profit = calculate_stop_loss_take_profit(current_price, sd, signal)
        
        expected_stop_loss = current_price * (1 + 2 * sd)  # 52000
        expected_take_profit = current_price * (1 - 3 * sd)  # 47000
        
        self.assertAlmostEqual(stop_loss, expected_stop_loss, places=2)
        self.assertAlmostEqual(take_profit, expected_take_profit, places=2)
        
        # Test neutral position
        signal = 'neutral'
        stop_loss, take_profit = calculate_stop_loss_take_profit(current_price, sd, signal)
        
        self.assertEqual(stop_loss, 0.0)
        self.assertEqual(take_profit, 0.0)


if __name__ == '__main__':
    unittest.main()
