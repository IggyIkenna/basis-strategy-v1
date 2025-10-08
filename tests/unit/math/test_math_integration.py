#!/usr/bin/env python3
"""
Integration tests for math calculators - tests actual implementations.
"""

import pytest
import sys
import os
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.core.math.yield_calculator import YieldCalculator
from basis_strategy_v1.core.math.ltv_calculator import LTVCalculator
from basis_strategy_v1.core.math.health_calculator import HealthCalculator
from basis_strategy_v1.core.math.margin_calculator import MarginCalculator
from basis_strategy_v1.core.math.metrics_calculator import MetricsCalculator
from basis_strategy_v1.core.math.aave_rate_calculator import AAVERateCalculator


class TestMathIntegration:
    """Integration tests for math calculators using actual implementations."""
    
    def test_yield_calculator_basic(self):
        """Test basic yield calculator functionality."""
        # Test APY to APR conversion
        apy = Decimal("0.05")  # 5% APY
        apr = YieldCalculator.apy_to_apr(apy)
        assert isinstance(apr, Decimal)
        assert apr > Decimal("0")
        
        # Test APR to APY conversion
        apr_input = Decimal("0.05")  # 5% APR
        apy_output = YieldCalculator.apr_to_apy(apr_input, 365)
        assert isinstance(apy_output, Decimal)
        assert apy_output > Decimal("0")
        
        # Test simple yield calculation
        principal = Decimal("10000")
        rate = Decimal("0.05")
        time_fraction = Decimal("1")  # 1 year
        
        simple_yield = YieldCalculator.calculate_simple_yield(principal, rate, time_fraction)
        expected = Decimal("500")  # 10000 * 0.05 * 1
        assert abs(simple_yield - expected) < Decimal("0.01")
        
        # Test compound yield calculation
        compound_yield = YieldCalculator.calculate_compound_yield(principal, rate, time_fraction, 365)
        assert isinstance(compound_yield, Decimal)
        assert compound_yield > simple_yield  # Compound should be higher than simple
        
        print("✅ Yield calculator basic tests passed")
    
    def test_ltv_calculator_basic(self):
        """Test basic LTV calculator functionality."""
        # Test current LTV calculation
        collateral_value = Decimal("100000")
        debt_value = Decimal("75000")
        
        ltv = LTVCalculator.calculate_current_ltv(collateral_value, debt_value)
        expected = Decimal("0.75")  # 75000 / 100000
        assert abs(ltv - expected) < Decimal("0.001")
        
        # Test projected LTV after borrowing
        additional_borrowing = Decimal("10000")
        collateral_efficiency = Decimal("0.95")
        
        projected_ltv = LTVCalculator.calculate_projected_ltv_after_borrowing(
            collateral_value, debt_value, additional_borrowing, collateral_efficiency
        )
        
        # New collateral: 100000 + (10000 * 0.95) = 109500
        # New debt: 75000 + 10000 = 85000
        # LTV: 85000 / 109500 ≈ 0.776
        expected_projected = Decimal("85000") / Decimal("109500")
        assert abs(projected_ltv - expected_projected) < Decimal("0.001")
        
        print("✅ LTV calculator basic tests passed")
    
    def test_health_calculator_basic(self):
        """Test basic health calculator functionality."""
        # Test health factor calculation
        collateral_value = Decimal("100000")
        debt_value = Decimal("75000")
        liquidation_threshold = Decimal("0.85")
        
        health_factor = HealthCalculator.calculate_health_factor(
            collateral_value, debt_value, liquidation_threshold
        )
        
        # Health factor = (collateral_value * liquidation_threshold) / debt_value
        # = (100000 * 0.85) / 75000 = 85000 / 75000 = 1.133
        expected = Decimal("100000") * Decimal("0.85") / Decimal("75000")
        assert abs(health_factor - expected) < Decimal("0.001")
        
        print("✅ Health calculator basic tests passed")
    
    def test_margin_calculator_basic(self):
        """Test basic margin calculator functionality."""
        # Test projected margin capacity calculation
        current_collateral = Decimal("100000")
        current_debt = Decimal("75000")
        additional_borrowing = Decimal("10000")
        
        # Mock config structures
        ltv_config = {
            "standard_limits": {
                "weeth": 0.80,
                "wsteth": 0.75
            }
        }
        
        strategy_config = {
            "ltv": {
                "safe_ltv": {
                    "standard_borrowing": 0.85
                }
            }
        }
        
        margin_capacity = MarginCalculator.calculate_projected_margin_capacity_after_borrowing(
            current_collateral, current_debt, additional_borrowing, 
            ltv_config, strategy_config
        )
        
        assert isinstance(margin_capacity, Decimal)
        assert margin_capacity >= Decimal("0")
        
        print("✅ Margin calculator basic tests passed")
    
    def test_metrics_calculator_basic(self):
        """Test basic metrics calculator functionality."""
        # Create a mock portfolio object
        class MockPortfolio:
            def __init__(self):
                self.total_value_usd = Decimal("105000")
                self.balances = {
                    "aave": {"weeth": Decimal("50000"), "wsteth": Decimal("30000")},
                    "binance": {"USDT": Decimal("25000")}
                }
                self.debts = {
                    "aave": {"variableDebtWETH": Decimal("20000")}
                }
                self.positions = {
                    "binance_ETHUSDT-PERP": {"size": Decimal("10")}
                }
        
        portfolio = MockPortfolio()
        initial_capital = Decimal("100000")
        timestamp = datetime.now()
        
        metrics = MetricsCalculator.calculate_metrics(portfolio, initial_capital, timestamp)
        
        assert isinstance(metrics, dict)
        assert 'total_return' in metrics
        assert 'portfolio_value' in metrics
        assert 'initial_capital' in metrics
        
        # Total return should be 5% (105000 - 100000) / 100000
        expected_return = 0.05
        assert abs(metrics['total_return'] - expected_return) < 0.001
        
        print("✅ Metrics calculator basic tests passed")
    
    def test_aave_rate_calculator_basic(self):
        """Test basic AAVE rate calculator functionality."""
        # Test interest rate calculation
        utilization_rate = Decimal("0.5")  # 50% utilization
        asset = "WETH"
        
        # Mock rate models with reserve_factor
        rate_models = {
            "WETH": {
                "optimal_utilization": Decimal("0.8"),
                "base_rate": Decimal("0.01"),
                "slope1": Decimal("0.04"),
                "slope2": Decimal("0.6"),
                "reserve_factor": Decimal("0.1")  # 10% reserve factor
            }
        }
        
        supply_rate, borrow_rate = AAVERateCalculator.calculate_aave_interest_rate(
            utilization_rate, asset, rate_models
        )
        
        assert isinstance(supply_rate, Decimal)
        assert isinstance(borrow_rate, Decimal)
        assert supply_rate >= Decimal("0")
        assert borrow_rate >= Decimal("0")
        # Note: The relationship between supply and borrow rates depends on the implementation
        # Both should be positive and reasonable
        
        print("✅ AAVE rate calculator basic tests passed")
    
    def test_calculator_precision(self):
        """Test that calculators maintain precision with Decimal arithmetic."""
        # Test with high precision values
        precise_collateral = Decimal("100000.123456789")
        precise_debt = Decimal("75000.987654321")
        
        # LTV calculation
        precise_ltv = LTVCalculator.calculate_current_ltv(precise_collateral, precise_debt)
        expected_ltv = precise_debt / precise_collateral
        assert abs(precise_ltv - expected_ltv) < Decimal("0.000000001")
        
        # Health factor calculation
        precise_health = HealthCalculator.calculate_health_factor(
            precise_collateral, precise_debt, Decimal("0.85")
        )
        expected_health = precise_collateral * Decimal("0.85") / precise_debt
        assert abs(precise_health - expected_health) < Decimal("0.000000001")
        
        print("✅ Calculator precision tests passed")
    
    def test_calculator_edge_cases(self):
        """Test calculators handle edge cases gracefully."""
        # Test with zero values
        zero_ltv = LTVCalculator.calculate_current_ltv(Decimal("0"), Decimal("0"))
        assert zero_ltv == Decimal("0")
        
        # Test with very small values
        small_ltv = LTVCalculator.calculate_current_ltv(Decimal("0.01"), Decimal("0.005"))
        assert abs(small_ltv - Decimal("0.5")) < Decimal("0.001")
        
        # Test with very large values
        large_ltv = LTVCalculator.calculate_current_ltv(Decimal("1000000"), Decimal("750000"))
        assert abs(large_ltv - Decimal("0.75")) < Decimal("0.001")
        
        print("✅ Calculator edge cases tests passed")
    
    def test_calculator_integration(self):
        """Test integration between different calculators."""
        # Test LTV and Health factor integration
        collateral_value = Decimal("100000")
        debt_value = Decimal("75000")
        liquidation_threshold = Decimal("0.85")
        
        # Calculate LTV
        ltv = LTVCalculator.calculate_current_ltv(collateral_value, debt_value)
        
        # Calculate health factor
        health_factor = HealthCalculator.calculate_health_factor(
            collateral_value, debt_value, liquidation_threshold
        )
        
        # Verify relationship: health_factor = (collateral * liquidation_threshold) / debt
        # LTV = debt / collateral
        # So: health_factor = liquidation_threshold / ltv
        expected_health = liquidation_threshold / ltv
        assert abs(health_factor - expected_health) < Decimal("0.001")
        
        print("✅ Calculator integration tests passed")
    
    def test_yield_ltv_integration(self):
        """Test integration between yield and LTV calculations."""
        # Test scenario: borrowing to increase yield
        initial_capital = Decimal("100000")
        borrow_amount = Decimal("50000")
        yield_rate = Decimal("0.05")  # 5% yield
        borrow_rate = Decimal("0.03")  # 3% borrow rate
        
        # Calculate net yield
        gross_yield = initial_capital * yield_rate
        borrow_cost = borrow_amount * borrow_rate
        net_yield = gross_yield - borrow_cost
        
        # Calculate LTV after borrowing
        total_collateral = initial_capital + borrow_amount  # Assuming borrowed amount becomes collateral
        total_debt = borrow_amount
        ltv = LTVCalculator.calculate_current_ltv(total_collateral, total_debt)
        
        # Verify calculations
        expected_ltv = borrow_amount / total_collateral
        assert abs(ltv - expected_ltv) < Decimal("0.001")
        
        # Net yield should be positive (profitable leverage)
        assert net_yield > Decimal("0")
        
        print("✅ Yield-LTV integration tests passed")


if __name__ == "__main__":
    # Run tests
    test_instance = TestMathIntegration()
    
    print("🧪 Testing Math Calculator Integration...")
    
    try:
        test_instance.test_yield_calculator_basic()
        test_instance.test_ltv_calculator_basic()
        test_instance.test_health_calculator_basic()
        test_instance.test_margin_calculator_basic()
        test_instance.test_metrics_calculator_basic()
        test_instance.test_aave_rate_calculator_basic()
        test_instance.test_calculator_precision()
        test_instance.test_calculator_edge_cases()
        test_instance.test_calculator_integration()
        test_instance.test_yield_ltv_integration()
        
        print("\n✅ All Math Calculator Integration tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
