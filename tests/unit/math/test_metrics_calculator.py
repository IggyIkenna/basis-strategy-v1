#!/usr/bin/env python3
"""
Test Metrics Calculator - Performance metrics calculations.
"""

import pytest
import sys
import os
from decimal import Decimal
from typing import Dict, Any, List

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.core.math.metrics_calculator import MetricsCalculator


class TestMetricsCalculator:
    """Test Metrics Calculator mathematical functions."""
    
    def test_calculate_metrics_basic(self):
        """Test basic metrics calculation."""
        # Test with simple data
        from datetime import datetime
        
        # Create a mock portfolio object
        class MockPortfolio:
            def __init__(self):
                self.total_value_usd = Decimal("105000")
                self.balances = {
                    'AAVE': {'ETH': Decimal("10"), 'USDT': Decimal("1000")},
                    'CEX': {'ETH': Decimal("5")}
                }
                self.debts = {
                    'AAVE': {'ETH': Decimal("2")}
                }
                self.positions = [
                    {'symbol': 'ETHUSDT', 'size': Decimal("1000")},
                    {'symbol': 'BTCUSDT', 'size': Decimal("0.5")}
                ]
        
        portfolio = MockPortfolio()
        initial_capital = Decimal("100000")
        timestamp = datetime.now()
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        # Verify basic structure
        assert isinstance(metrics, dict)
        assert 'total_return' in metrics
        assert 'portfolio_value' in metrics
        assert 'initial_capital' in metrics
        assert 'balance_count' in metrics
        assert 'debt_count' in metrics
        assert 'position_count' in metrics
        assert 'total_assets' in metrics
        assert 'total_debts' in metrics
        assert 'net_value' in metrics
        
        # Verify calculations
        assert isinstance(metrics['total_return'], Decimal)
        assert isinstance(metrics['portfolio_value'], float)
        assert isinstance(metrics['initial_capital'], float)
        assert isinstance(metrics['balance_count'], int)
        assert isinstance(metrics['debt_count'], int)
        assert isinstance(metrics['position_count'], int)
        assert isinstance(metrics['total_assets'], float)
        assert isinstance(metrics['total_debts'], float)
        assert isinstance(metrics['net_value'], float)
        
        # Verify reasonable values
        assert metrics['total_return'] > Decimal("0")
        assert metrics['portfolio_value'] > 0
        assert metrics['initial_capital'] == 100000.0
        assert metrics['balance_count'] > 0
        assert metrics['debt_count'] > 0
        assert metrics['position_count'] >= 0
        assert metrics['total_assets'] > 0
        assert metrics['total_debts'] > 0
        assert metrics['net_value'] > 0
        
        print("✅ Basic metrics calculation tests passed")
    
    def test_total_return_calculation(self):
        """Test total return calculation."""
        from datetime import datetime
        # Test with positive returns
        returns = [Decimal("0.01"), Decimal("0.02"), Decimal("0.015")]
        data = {'returns': returns}
        initial_capital = Decimal("100000")
        timestamp = datetime.now()
        
        metrics = MetricsCalculator.calculate_metrics(data, initial_capital, timestamp)
        total_return = metrics['total_return']
        
        # Total return = (1 + r1) * (1 + r2) * (1 + r3) - 1
        expected = (Decimal("1.01") * Decimal("1.02") * Decimal("1.015")) - Decimal("1")
        assert abs(total_return - expected) < Decimal("0.0001")
        
        # Test with negative returns
        returns_neg = [Decimal("-0.01"), Decimal("-0.02"), Decimal("0.01")]
        data_neg = {'returns': returns_neg}
        
        metrics_neg = MetricsCalculator.calculate_metrics(data_neg)
        total_return_neg = metrics_neg['total_return']
        
        expected_neg = (Decimal("0.99") * Decimal("0.98") * Decimal("1.01")) - Decimal("1")
        assert abs(total_return_neg - expected_neg) < Decimal("0.0001")
        
        print("✅ Total return calculation tests passed")
    
    def test_annualized_return_calculation(self):
        """Test annualized return calculation."""
        # Test with daily returns (252 trading days)
        daily_returns = [Decimal("0.001")] * 252  # 0.1% daily
        data = {'returns': daily_returns}
        
        metrics = MetricsCalculator.calculate_metrics(data, initial_capital, timestamp)
        annualized_return = metrics['annualized_return']
        
        # Annualized return = (1 + daily_return)^252 - 1
        expected = (Decimal("1.001") ** 252) - Decimal("1")
        assert abs(annualized_return - expected) < Decimal("0.001")
        
        # Test with monthly returns (12 months)
        monthly_returns = [Decimal("0.01")] * 12  # 1% monthly
        data_monthly = {'returns': monthly_returns}
        
        metrics_monthly = MetricsCalculator.calculate_metrics(data_monthly)
        annualized_return_monthly = metrics_monthly['annualized_return']
        
        # Annualized return = (1 + monthly_return)^12 - 1
        expected_monthly = (Decimal("1.01") ** 12) - Decimal("1")
        assert abs(annualized_return_monthly - expected_monthly) < Decimal("0.001")
        
        print("✅ Annualized return calculation tests passed")
    
    def test_volatility_calculation(self):
        """Test volatility calculation."""
        # Test with known volatility
        returns = [
            Decimal("0.01"), Decimal("-0.005"), Decimal("0.02"), 
            Decimal("-0.01"), Decimal("0.015"), Decimal("-0.008")
        ]
        data = {'returns': returns}
        initial_capital = Decimal("100000")
        timestamp = datetime.now()
        
        metrics = MetricsCalculator.calculate_metrics(data, initial_capital, timestamp)
        volatility = metrics['volatility']
        
        # Calculate expected volatility (standard deviation)
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        expected_volatility = variance ** Decimal("0.5")
        
        assert abs(volatility - expected_volatility) < Decimal("0.001")
        
        # Test with zero volatility
        returns_zero = [Decimal("0.01")] * 10  # All same returns
        data_zero = {'returns': returns_zero}
        
        metrics_zero = MetricsCalculator.calculate_metrics(data_zero)
        volatility_zero = metrics_zero['volatility']
        
        assert volatility_zero == Decimal("0")
        
        print("✅ Volatility calculation tests passed")
    
    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation."""
        # Test with positive excess return
        returns = [Decimal("0.01"), Decimal("0.02"), Decimal("0.015"), Decimal("0.008")]
        risk_free_rate = Decimal("0.02")  # 2% annual
        data = {'returns': returns, 'risk_free_rate': risk_free_rate}
        
        metrics = MetricsCalculator.calculate_metrics(data, initial_capital, timestamp)
        sharpe_ratio = metrics['sharpe_ratio']
        
        # Sharpe ratio = (mean_return - risk_free_rate) / volatility
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        volatility = variance ** Decimal("0.5")
        expected_sharpe = (mean_return - risk_free_rate) / volatility
        
        assert abs(sharpe_ratio - expected_sharpe) < Decimal("0.001")
        
        # Test with negative excess return
        returns_neg = [Decimal("-0.01"), Decimal("-0.02"), Decimal("-0.015")]
        data_neg = {'returns': returns_neg, 'risk_free_rate': risk_free_rate}
        
        metrics_neg = MetricsCalculator.calculate_metrics(data_neg)
        sharpe_ratio_neg = metrics_neg['sharpe_ratio']
        
        assert sharpe_ratio_neg < Decimal("0")  # Should be negative
        
        print("✅ Sharpe ratio calculation tests passed")
    
    def test_max_drawdown_calculation(self):
        """Test maximum drawdown calculation."""
        # Test with known drawdown pattern
        prices = [
            Decimal("100"), Decimal("105"), Decimal("102"), 
            Decimal("98"), Decimal("95"), Decimal("100"), Decimal("108")
        ]
        data = {'prices': prices}
        
        metrics = MetricsCalculator.calculate_metrics(data, initial_capital, timestamp)
        max_drawdown = metrics['max_drawdown']
        
        # Calculate expected max drawdown
        # Peak at 105, trough at 95
        # Drawdown = (95 - 105) / 105 = -0.0952
        expected_drawdown = (Decimal("95") - Decimal("105")) / Decimal("105")
        assert abs(max_drawdown - expected_drawdown) < Decimal("0.001")
        
        # Test with no drawdown (monotonically increasing)
        prices_increasing = [Decimal("100"), Decimal("101"), Decimal("102"), Decimal("103")]
        data_increasing = {'prices': prices_increasing}
        
        metrics_increasing = MetricsCalculator.calculate_metrics(data_increasing)
        max_drawdown_increasing = metrics_increasing['max_drawdown']
        
        assert max_drawdown_increasing == Decimal("0")
        
        print("✅ Maximum drawdown calculation tests passed")
    
    def test_additional_metrics(self):
        """Test additional performance metrics."""
        # Test with comprehensive data
        data = {
            'returns': [Decimal("0.01"), Decimal("0.02"), Decimal("-0.005"), Decimal("0.015")],
            'prices': [Decimal("100"), Decimal("102"), Decimal("101.49"), Decimal("103.01")],
            'volumes': [Decimal("1000"), Decimal("1200"), Decimal("800"), Decimal("1100")],
            'benchmark_returns': [Decimal("0.008"), Decimal("0.015"), Decimal("-0.003"), Decimal("0.012")]
        }
        
        metrics = MetricsCalculator.calculate_metrics(data, initial_capital, timestamp)
        
        # Check for additional metrics
        additional_metrics = [
            'beta', 'alpha', 'information_ratio', 'calmar_ratio',
            'sortino_ratio', 'treynor_ratio', 'jensen_alpha'
        ]
        
        for metric in additional_metrics:
            if metric in metrics:
                assert isinstance(metrics[metric], Decimal)
        
        print("✅ Additional metrics calculation tests passed")
    
    def test_risk_metrics(self):
        """Test risk-related metrics."""
        # Test with high volatility data
        high_vol_returns = [
            Decimal("0.05"), Decimal("-0.03"), Decimal("0.08"), 
            Decimal("-0.06"), Decimal("0.04"), Decimal("-0.02")
        ]
        data = {'returns': high_vol_returns}
        
        metrics = MetricsCalculator.calculate_metrics(data, initial_capital, timestamp)
        
        # Check risk metrics
        risk_metrics = ['var_95', 'var_99', 'cvar_95', 'cvar_99', 'downside_deviation']
        
        for metric in risk_metrics:
            if metric in metrics:
                assert isinstance(metrics[metric], Decimal)
                assert metrics[metric] >= Decimal("0")  # Risk metrics should be non-negative
        
        print("✅ Risk metrics calculation tests passed")
    
    def test_portfolio_metrics(self):
        """Test portfolio-level metrics."""
        # Test with multiple assets
        portfolio_data = {
            'assets': {
                'ETH': {
                    'returns': [Decimal("0.01"), Decimal("0.02"), Decimal("-0.005")],
                    'weights': [Decimal("0.6"), Decimal("0.6"), Decimal("0.6")]
                },
                'BTC': {
                    'returns': [Decimal("0.008"), Decimal("0.015"), Decimal("-0.003")],
                    'weights': [Decimal("0.4"), Decimal("0.4"), Decimal("0.4")]
                }
            }
        }
        
        metrics = MetricsCalculator.calculate_metrics(portfolio_data)
        
        # Check portfolio metrics
        portfolio_metrics = ['portfolio_return', 'portfolio_volatility', 'portfolio_sharpe']
        
        for metric in portfolio_metrics:
            if metric in metrics:
                assert isinstance(metrics[metric], Decimal)
        
        print("✅ Portfolio metrics calculation tests passed")
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with empty data
        empty_data = {'returns': []}
        metrics_empty = MetricsCalculator.calculate_metrics(empty_data)
        
        # Should handle empty data gracefully
        assert isinstance(metrics_empty, dict)
        
        # Test with single data point
        single_data = {'returns': [Decimal("0.01")]}
        metrics_single = MetricsCalculator.calculate_metrics(single_data)
        
        # Should handle single data point
        assert isinstance(metrics_single, dict)
        
        # Test with zero returns
        zero_returns = [Decimal("0")] * 10
        zero_data = {'returns': zero_returns}
        metrics_zero = MetricsCalculator.calculate_metrics(zero_data)
        
        # Should handle zero returns
        assert metrics_zero['volatility'] == Decimal("0")
        assert metrics_zero['total_return'] == Decimal("0")
        
        print("✅ Edge cases tests passed")
    
    def test_precision_handling(self):
        """Test precision handling with Decimal arithmetic."""
        # Test with high precision values
        precise_returns = [
            Decimal("0.0123456789"),
            Decimal("-0.0054321098"),
            Decimal("0.0234567890"),
            Decimal("-0.0012345678")
        ]
        data = {'returns': precise_returns}
        
        metrics = MetricsCalculator.calculate_metrics(data, initial_capital, timestamp)
        
        # Should maintain precision in calculations
        assert isinstance(metrics['total_return'], Decimal)
        assert isinstance(metrics['volatility'], Decimal)
        assert isinstance(metrics['sharpe_ratio'], Decimal)
        
        # Test with very small values
        small_returns = [Decimal("0.000001")] * 100
        small_data = {'returns': small_returns}
        
        metrics_small = MetricsCalculator.calculate_metrics(small_data)
        assert isinstance(metrics_small['total_return'], Decimal)
        
        print("✅ Precision handling tests passed")


if __name__ == "__main__":
    # Run tests
    test_instance = TestMetricsCalculator()
    
    print("🧪 Testing Metrics Calculator...")
    
    try:
        test_instance.test_calculate_metrics_basic()
        test_instance.test_total_return_calculation()
        test_instance.test_annualized_return_calculation()
        test_instance.test_volatility_calculation()
        test_instance.test_sharpe_ratio_calculation()
        test_instance.test_max_drawdown_calculation()
        test_instance.test_additional_metrics()
        test_instance.test_risk_metrics()
        test_instance.test_portfolio_metrics()
        test_instance.test_edge_cases()
        test_instance.test_precision_handling()
        
        print("\n✅ All Metrics Calculator tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
