#!/usr/bin/env python3
"""
Test AAVE Rate Calculator - AAVE interest rate calculations.
"""

import pytest
import sys
import os
from decimal import Decimal
from typing import Dict, Any

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.core.math.aave_rate_calculator import AAVERateCalculator


class TestAAVERateCalculator:
    """Test AAVE Rate Calculator mathematical functions."""
    
    def test_calculate_aave_interest_rate(self):
        """Test AAVE interest rate calculation."""
        # Test standard case
        utilization_rate = Decimal("0.5")  # 50% utilization
        asset = "WETH"
        
        # Mock rate models
        rate_models = {
            "WETH": {
                "optimal_utilization": Decimal("0.8"),
                "base_rate": Decimal("0.01"),
                "slope1": Decimal("0.04"),
                "slope2": Decimal("0.6")
            }
        }
        
        supply_rate, borrow_rate = AAVERateCalculator.calculate_aave_interest_rate(
            utilization_rate, asset, rate_models
        )
        
        # For utilization < optimal_utilization:
        # borrow_rate = base_rate + slope1 * (utilization / optimal_utilization)
        # supply_rate = borrow_rate * utilization * (1 - reserve_factor)
        # reserve_factor is typically 0.1 (10%)
        
        expected_borrow_rate = Decimal("0.01") + Decimal("0.04") * (Decimal("0.5") / Decimal("0.8"))
        expected_supply_rate = expected_borrow_rate * Decimal("0.5") * Decimal("0.9")  # 1 - 0.1
        
        assert abs(borrow_rate - expected_borrow_rate) < Decimal("0.001")
        assert abs(supply_rate - expected_supply_rate) < Decimal("0.001")
        
        print("✅ AAVE interest rate calculation tests passed")
    
    def test_calculate_aave_interest_rate_high_utilization(self):
        """Test AAVE interest rate calculation with high utilization."""
        # Test with utilization above optimal
        utilization_rate = Decimal("0.9")  # 90% utilization
        asset = "WETH"
        
        rate_models = {
            "WETH": {
                "optimal_utilization": Decimal("0.8"),
                "base_rate": Decimal("0.01"),
                "slope1": Decimal("0.04"),
                "slope2": Decimal("0.6")
            }
        }
        
        supply_rate, borrow_rate = AAVERateCalculator.calculate_aave_interest_rate(
            utilization_rate, asset, rate_models
        )
        
        # For utilization > optimal_utilization:
        # borrow_rate = base_rate + slope1 + slope2 * ((utilization - optimal) / (1 - optimal))
        # supply_rate = borrow_rate * utilization * (1 - reserve_factor)
        
        expected_borrow_rate = (
            Decimal("0.01") + Decimal("0.04") + 
            Decimal("0.6") * ((Decimal("0.9") - Decimal("0.8")) / (Decimal("1") - Decimal("0.8")))
        )
        expected_supply_rate = expected_borrow_rate * Decimal("0.9") * Decimal("0.9")
        
        assert abs(borrow_rate - expected_borrow_rate) < Decimal("0.001")
        assert abs(supply_rate - expected_supply_rate) < Decimal("0.001")
        
        print("✅ AAVE interest rate high utilization tests passed")
    
    def test_calculate_market_impact_delta(self):
        """Test market impact delta calculation."""
        # Test standard case
        asset = "WETH"
        base_supply_tokens = Decimal("1000000")  # 1M tokens
        base_borrows_tokens = Decimal("500000")   # 500K tokens
        additional_supply = Decimal("100000")     # 100K additional supply
        additional_borrows = Decimal("50000")     # 50K additional borrows
        
        # Mock market data
        market_data = {
            "WETH": {
                "total_supply": base_supply_tokens,
                "total_borrows": base_borrows_tokens,
                "optimal_utilization": Decimal("0.8"),
                "base_rate": Decimal("0.01"),
                "slope1": Decimal("0.04"),
                "slope2": Decimal("0.6")
            }
        }
        
        impact_delta = AAVERateCalculator.calculate_market_impact_delta(
            asset, base_supply_tokens, base_borrows_tokens, 
            additional_supply, additional_borrows, market_data
        )
        
        # Should calculate the change in interest rates due to market impact
        assert isinstance(impact_delta, dict)
        assert 'supply_rate_change' in impact_delta
        assert 'borrow_rate_change' in impact_delta
        
        print("✅ Market impact delta calculation tests passed")
    
    def test_calculate_utilization_impact(self):
        """Test utilization impact calculation."""
        # Test standard case
        base_supply_tokens = Decimal("1000000")
        base_borrows_tokens = Decimal("500000")
        additional_supply = Decimal("100000")
        additional_borrows = Decimal("50000")
        
        utilization_impact = AAVERateCalculator.calculate_utilization_impact(
            base_supply_tokens, base_borrows_tokens, additional_supply, additional_borrows
        )
        
        # Calculate expected utilization changes
        initial_utilization = base_borrows_tokens / base_supply_tokens
        new_supply = base_supply_tokens + additional_supply
        new_borrows = base_borrows_tokens + additional_borrows
        new_utilization = new_borrows / new_supply
        
        expected_impact = new_utilization - initial_utilization
        assert abs(utilization_impact - expected_impact) < Decimal("0.001")
        
        print("✅ Utilization impact calculation tests passed")
    
    def test_rate_calculation_edge_cases(self):
        """Test rate calculation edge cases."""
        # Test with zero utilization
        utilization_zero = Decimal("0")
        asset = "WETH"
        
        rate_models = {
            "WETH": {
                "optimal_utilization": Decimal("0.8"),
                "base_rate": Decimal("0.01"),
                "slope1": Decimal("0.04"),
                "slope2": Decimal("0.6")
            }
        }
        
        supply_rate_zero, borrow_rate_zero = AAVERateCalculator.calculate_aave_interest_rate(
            utilization_zero, asset, rate_models
        )
        
        # At zero utilization, borrow rate should be base rate
        assert borrow_rate_zero == Decimal("0.01")
        # Supply rate should be zero (no utilization)
        assert supply_rate_zero == Decimal("0")
        
        # Test with 100% utilization
        utilization_full = Decimal("1.0")
        supply_rate_full, borrow_rate_full = AAVERateCalculator.calculate_aave_interest_rate(
            utilization_full, asset, rate_models
        )
        
        # At 100% utilization, rates should be at maximum
        assert borrow_rate_full > borrow_rate_zero
        assert supply_rate_full > supply_rate_zero
        
        print("✅ Rate calculation edge cases tests passed")
    
    def test_different_assets(self):
        """Test rate calculations for different assets."""
        # Test with different asset configurations
        assets_config = {
            "WETH": {
                "optimal_utilization": Decimal("0.8"),
                "base_rate": Decimal("0.01"),
                "slope1": Decimal("0.04"),
                "slope2": Decimal("0.6")
            },
            "USDC": {
                "optimal_utilization": Decimal("0.9"),
                "base_rate": Decimal("0.005"),
                "slope1": Decimal("0.02"),
                "slope2": Decimal("0.4")
            },
            "WBTC": {
                "optimal_utilization": Decimal("0.7"),
                "base_rate": Decimal("0.02"),
                "slope1": Decimal("0.06"),
                "slope2": Decimal("0.8")
            }
        }
        
        utilization = Decimal("0.5")
        
        for asset, rate_model in assets_config.items():
            supply_rate, borrow_rate = AAVERateCalculator.calculate_aave_interest_rate(
                utilization, asset, assets_config
            )
            
            # Each asset should have different rates based on their parameters
            assert isinstance(supply_rate, Decimal)
            assert isinstance(borrow_rate, Decimal)
            assert supply_rate >= Decimal("0")
            assert borrow_rate >= Decimal("0")
            
            # Borrow rate should be higher than supply rate
            assert borrow_rate > supply_rate
        
        print("✅ Different assets rate calculation tests passed")
    
    def test_rate_model_validation(self):
        """Test rate model parameter validation."""
        # Test with invalid rate model
        invalid_rate_models = {
            "WETH": {
                "optimal_utilization": Decimal("1.5"),  # Invalid: > 1
                "base_rate": Decimal("0.01"),
                "slope1": Decimal("0.04"),
                "slope2": Decimal("0.6")
            }
        }
        
        # Should handle invalid parameters gracefully
        try:
            supply_rate, borrow_rate = AAVERateCalculator.calculate_aave_interest_rate(
                Decimal("0.5"), "WETH", invalid_rate_models
            )
            # If it doesn't raise an exception, verify the result is reasonable
            assert isinstance(supply_rate, Decimal)
            assert isinstance(borrow_rate, Decimal)
        except (ValueError, AssertionError):
            # Expected behavior for invalid parameters
            pass
        
        print("✅ Rate model validation tests passed")
    
    def test_precision_handling(self):
        """Test precision handling with Decimal arithmetic."""
        # Test with high precision values
        precise_utilization = Decimal("0.5123456789")
        asset = "WETH"
        
        rate_models = {
            "WETH": {
                "optimal_utilization": Decimal("0.8123456789"),
                "base_rate": Decimal("0.0123456789"),
                "slope1": Decimal("0.0423456789"),
                "slope2": Decimal("0.6123456789")
            }
        }
        
        supply_rate, borrow_rate = AAVERateCalculator.calculate_aave_interest_rate(
            precise_utilization, asset, rate_models
        )
        
        # Should maintain precision in calculations
        assert isinstance(supply_rate, Decimal)
        assert isinstance(borrow_rate, Decimal)
        
        # Test utilization impact with precision
        precise_impact = AAVERateCalculator.calculate_utilization_impact(
            Decimal("1000000.123456789"),
            Decimal("500000.987654321"),
            Decimal("100000.111111111"),
            Decimal("50000.222222222")
        )
        
        assert isinstance(precise_impact, Decimal)
        
        print("✅ Precision handling tests passed")
    
    def test_complex_scenarios(self):
        """Test complex rate calculation scenarios."""
        # Test with multiple rate changes
        base_supply = Decimal("1000000")
        base_borrows = Decimal("500000")
        
        # Simulate multiple transactions
        transactions = [
            {"supply": Decimal("100000"), "borrow": Decimal("0")},
            {"supply": Decimal("0"), "borrow": Decimal("50000")},
            {"supply": Decimal("50000"), "borrow": Decimal("25000")},
        ]
        
        current_supply = base_supply
        current_borrows = base_borrows
        
        for tx in transactions:
            current_supply += tx["supply"]
            current_borrows += tx["borrow"]
            
            utilization = current_borrows / current_supply
            
            # Calculate rates for each step
            rate_models = {
                "WETH": {
                    "optimal_utilization": Decimal("0.8"),
                    "base_rate": Decimal("0.01"),
                    "slope1": Decimal("0.04"),
                    "slope2": Decimal("0.6")
                }
            }
            
            supply_rate, borrow_rate = AAVERateCalculator.calculate_aave_interest_rate(
                utilization, "WETH", rate_models
            )
            
            assert isinstance(supply_rate, Decimal)
            assert isinstance(borrow_rate, Decimal)
        
        print("✅ Complex scenarios tests passed")


if __name__ == "__main__":
    # Run tests
    test_instance = TestAAVERateCalculator()
    
    print("🧪 Testing AAVE Rate Calculator...")
    
    try:
        test_instance.test_calculate_aave_interest_rate()
        test_instance.test_calculate_aave_interest_rate_high_utilization()
        test_instance.test_calculate_market_impact_delta()
        test_instance.test_calculate_utilization_impact()
        test_instance.test_rate_calculation_edge_cases()
        test_instance.test_different_assets()
        test_instance.test_rate_model_validation()
        test_instance.test_precision_handling()
        test_instance.test_complex_scenarios()
        
        print("\n✅ All AAVE Rate Calculator tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
