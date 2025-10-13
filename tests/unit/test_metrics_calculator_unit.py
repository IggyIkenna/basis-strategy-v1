"""Unit tests for Metrics Calculator."""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch
from basis_strategy_v1.core.math.metrics_calculator import MetricsCalculator, ERROR_CODES


class TestMetricsCalculator:
    """Test Metrics Calculator functionality."""

    def test_calculate_metrics_basic_portfolio(self):
        """Test basic metrics calculation."""
        # Create mock portfolio
        portfolio = Mock()
        portfolio.total_value_usd = Decimal("110000")
        portfolio.balances = {
            "venue1": {"ETH": Decimal("10"), "USDT": Decimal("50000")},
            "venue2": {"BTC": Decimal("2")}
        }
        portfolio.debts = {
            "venue1": {"USDT": Decimal("20000")}
        }
        portfolio.positions = [
            {"symbol": "ETHUSDT", "size": Decimal("10")},
            {"symbol": "BTCUSDT", "size": Decimal("2")}
        ]
        
        initial_capital = Decimal("100000")
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        assert metrics['timestamp'] == '2024-01-01T12:00:00'
        assert metrics['portfolio_value'] == 110000.0
        assert metrics['initial_capital'] == 100000.0
        assert metrics['total_return'] == 0.1  # 10% return
        assert metrics['balance_count'] == 3  # 2 ETH + 1 BTC
        assert metrics['debt_count'] == 1  # 1 USDT debt
        assert metrics['position_count'] == 2

    def test_calculate_metrics_no_initial_capital(self):
        """Test metrics calculation with zero initial capital."""
        portfolio = Mock()
        portfolio.total_value_usd = Decimal("100000")
        portfolio.balances = {"venue1": {"ETH": Decimal("10")}}
        portfolio.debts = {}
        portfolio.positions = []
        
        initial_capital = Decimal("0")
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        assert metrics['total_return'] == 0.0
        assert metrics['portfolio_value'] == 100000.0

    def test_calculate_metrics_negative_return(self):
        """Test metrics calculation with negative return."""
        portfolio = Mock()
        portfolio.total_value_usd = Decimal("90000")
        portfolio.balances = {"venue1": {"ETH": Decimal("10")}}
        portfolio.debts = {}
        portfolio.positions = []
        
        initial_capital = Decimal("100000")
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        assert metrics['total_return'] == -0.1  # -10% return

    def test_calculate_metrics_complex_portfolio(self):
        """Test metrics calculation with complex portfolio."""
        portfolio = Mock()
        portfolio.total_value_usd = Decimal("200000")
        portfolio.balances = {
            "venue1": {
                "ETH": Decimal("20"),
                "USDT": Decimal("100000"),
                "BTC": Decimal("1")
            },
            "venue2": {
                "ETH": Decimal("5"),
                "USDC": Decimal("50000")
            }
        }
        portfolio.debts = {
            "venue1": {
                "USDT": Decimal("30000"),
                "USDC": Decimal("10000")
            },
            "venue2": {
                "ETH": Decimal("2")
            }
        }
        portfolio.positions = [
            {"symbol": "ETHUSDT", "size": Decimal("25")},
            {"symbol": "BTCUSDT", "size": Decimal("1")},
            {"symbol": "ETHUSDC", "size": Decimal("3")}
        ]
        
        initial_capital = Decimal("150000")
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        assert metrics['portfolio_value'] == 200000.0
        assert metrics['initial_capital'] == 150000.0
        assert abs(metrics['total_return'] - 0.333) < 0.001  # ~33.3% return
        assert metrics['balance_count'] == 5  # 2 ETH + 1 USDT + 1 BTC + 1 ETH + 1 USDC
        assert metrics['debt_count'] == 3  # 1 USDT + 1 USDC + 1 ETH debt
        assert metrics['position_count'] == 3

    def test_calculate_metrics_empty_portfolio(self):
        """Test metrics calculation with empty portfolio."""
        portfolio = Mock()
        portfolio.total_value_usd = Decimal("0")
        portfolio.balances = {}
        portfolio.debts = {}
        portfolio.positions = []
        
        initial_capital = Decimal("100000")
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        assert metrics['portfolio_value'] == 0.0
        assert metrics['total_return'] == -1.0  # -100% return
        assert metrics['balance_count'] == 0
        assert metrics['debt_count'] == 0
        assert metrics['position_count'] == 0
        assert metrics['total_assets'] == 0.0
        assert metrics['total_debts'] == 0.0
        assert metrics['net_value'] == 0.0

    def test_calculate_metrics_net_exposure_calculation(self):
        """Test net exposure calculation."""
        portfolio = Mock()
        portfolio.total_value_usd = Decimal("150000")
        portfolio.balances = {
            "venue1": {
                "ETH": Decimal("10"),  # 10 * 3000 = 30000
                "USDT": Decimal("80000")
            }
        }
        portfolio.debts = {
            "venue1": {
                "USDT": Decimal("20000"),
                "USDC": Decimal("10000")
            }
        }
        portfolio.positions = []
        
        initial_capital = Decimal("100000")
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        # Total assets: 10 + 80000 = 80010 (raw values, no price conversion)
        # Total debts: 20000 + 10000 = 30000
        # Net value: 80010 - 30000 = 50010
        assert metrics['total_assets'] == 80010.0
        assert metrics['total_debts'] == 30000.0
        assert metrics['net_value'] == 50010.0

    def test_calculate_metrics_decimal_precision(self):
        """Test that calculations maintain proper decimal precision."""
        portfolio = Mock()
        portfolio.total_value_usd = Decimal("100000.123456")
        portfolio.balances = {"venue1": {"ETH": Decimal("10.123456")}}
        portfolio.debts = {}
        portfolio.positions = []
        
        initial_capital = Decimal("100000.000000")
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        # Should maintain precision in calculations
        expected_return = (Decimal("100000.123456") - Decimal("100000.000000")) / Decimal("100000.000000")
        assert abs(metrics['total_return'] - float(expected_return)) < 0.000001

    def test_calculate_metrics_timestamp_formatting(self):
        """Test timestamp formatting in metrics."""
        portfolio = Mock()
        portfolio.total_value_usd = Decimal("100000")
        portfolio.balances = {}
        portfolio.debts = {}
        portfolio.positions = []
        
        initial_capital = Decimal("100000")
        timestamp = datetime(2024, 12, 31, 23, 59, 59, 123456)
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        assert metrics['timestamp'] == '2024-12-31T23:59:59.123456'

    def test_calculate_metrics_large_numbers(self):
        """Test metrics calculation with large numbers."""
        portfolio = Mock()
        portfolio.total_value_usd = Decimal("1000000000")  # 1 billion
        portfolio.balances = {
            "venue1": {
                "ETH": Decimal("10000"),
                "USDT": Decimal("500000000")
            }
        }
        portfolio.debts = {
            "venue1": {
                "USDT": Decimal("100000000")
            }
        }
        portfolio.positions = [{"symbol": "ETHUSDT", "size": Decimal("10000")}]
        
        initial_capital = Decimal("500000000")  # 500 million
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        assert metrics['portfolio_value'] == 1000000000.0
        assert metrics['initial_capital'] == 500000000.0
        assert metrics['total_return'] == 1.0  # 100% return
        assert metrics['balance_count'] == 2
        assert metrics['debt_count'] == 1
        assert metrics['position_count'] == 1

    def test_calculate_metrics_mixed_currencies(self):
        """Test metrics calculation with mixed currencies."""
        portfolio = Mock()
        portfolio.total_value_usd = Decimal("200000")
        portfolio.balances = {
            "venue1": {
                "ETH": Decimal("10"),
                "USDT": Decimal("50000"),
                "USDC": Decimal("30000"),
                "DAI": Decimal("20000")
            }
        }
        portfolio.debts = {
            "venue1": {
                "USDT": Decimal("10000"),
                "USDC": Decimal("5000")
            }
        }
        portfolio.positions = []
        
        initial_capital = Decimal("100000")
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        assert metrics['balance_count'] == 4  # ETH, USDT, USDC, DAI
        assert metrics['debt_count'] == 2  # USDT, USDC
        assert metrics['total_assets'] == 100010.0  # 10 + 50000 + 30000 + 20000 (raw values)
        assert metrics['total_debts'] == 15000.0  # 10000 + 5000

    def test_error_codes_defined(self):
        """Test that all error codes are properly defined."""
        expected_codes = [
            'METRICS-001', 'METRICS-002', 'METRICS-003', 'METRICS-004', 'METRICS-005'
        ]
        
        for code in expected_codes:
            assert code in ERROR_CODES
            assert ERROR_CODES[code] is not None
            assert len(ERROR_CODES[code]) > 0

    def test_edge_case_zero_values(self):
        """Test edge cases with zero values."""
        portfolio = Mock()
        portfolio.total_value_usd = Decimal("0")
        portfolio.balances = {"venue1": {"ETH": Decimal("0")}}
        portfolio.debts = {"venue1": {"USDT": Decimal("0")}}
        portfolio.positions = []
        
        initial_capital = Decimal("0")
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        assert metrics['total_return'] == 0.0
        assert metrics['balance_count'] == 1  # Still counts zero balance
        assert metrics['debt_count'] == 1  # Still counts zero debt
        assert metrics['total_assets'] == 0.0
        assert metrics['total_debts'] == 0.0

    def test_boundary_conditions(self):
        """Test boundary conditions for metrics calculations."""
        # Test with very small values
        portfolio = Mock()
        portfolio.total_value_usd = Decimal("0.000001")
        portfolio.balances = {"venue1": {"ETH": Decimal("0.000001")}}
        portfolio.debts = {}
        portfolio.positions = []
        
        initial_capital = Decimal("0.000001")
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        assert metrics['total_return'] == 0.0
        assert metrics['portfolio_value'] == 0.000001
        assert metrics['balance_count'] == 1

    def test_calculate_metrics_float_conversion(self):
        """Test that all numeric values are properly converted to float."""
        portfolio = Mock()
        portfolio.total_value_usd = Decimal("100000.123")
        portfolio.balances = {"venue1": {"ETH": Decimal("10.456")}}
        portfolio.debts = {"venue1": {"USDT": Decimal("5000.789")}}
        portfolio.positions = [{"symbol": "ETHUSDT", "size": Decimal("10.456")}]
        
        initial_capital = Decimal("100000.000")
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        # All numeric values should be floats
        assert isinstance(metrics['portfolio_value'], float)
        assert isinstance(metrics['initial_capital'], float)
        assert isinstance(metrics['total_return'], float)
        assert isinstance(metrics['balance_count'], int)
        assert isinstance(metrics['debt_count'], int)
        assert isinstance(metrics['position_count'], int)
        assert isinstance(metrics['total_assets'], float)
        assert isinstance(metrics['total_debts'], float)
        assert isinstance(metrics['net_value'], float)
