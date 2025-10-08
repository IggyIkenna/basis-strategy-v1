#!/usr/bin/env python3
"""
Test Health Calculator - Health factor and risk calculations.
"""

import pytest
import sys
import os
from decimal import Decimal
from typing import Dict, Any

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.core.math.health_calculator import HealthCalculator


class TestHealthCalculator:
    """Test Health Calculator mathematical functions."""
    
    def test_calculate_health_factor(self):
        """Test health factor calculation."""
        # Test standard case
        collateral_value = Decimal("100000")
        debt_value = Decimal("75000")
        liquidation_threshold = Decimal("0.85")  # 85%
        
        health_factor = HealthCalculator.calculate_health_factor(
            collateral_value, debt_value, liquidation_threshold
        )
        
        # Health factor = (collateral_value * liquidation_threshold) / debt_value
        # = (100000 * 0.85) / 75000 = 85000 / 75000 = 1.133
        expected = Decimal("100000") * Decimal("0.85") / Decimal("75000")
        assert abs(health_factor - expected) < Decimal("0.001")
        
        # Test critical health factor (close to liquidation)
        debt_critical = Decimal("84000")  # Close to liquidation threshold
        health_factor_critical = HealthCalculator.calculate_health_factor(
            collateral_value, debt_critical, liquidation_threshold
        )
        
        expected_critical = Decimal("100000") * Decimal("0.85") / Decimal("84000")
        assert abs(health_factor_critical - expected_critical) < Decimal("0.001")
        assert health_factor_critical < Decimal("1.1")  # Should be close to 1.0
        
        # Test with zero debt
        health_factor_zero_debt = HealthCalculator.calculate_health_factor(
            collateral_value, Decimal("0"), liquidation_threshold
        )
        # Should handle zero debt gracefully (implementation dependent)
        assert isinstance(health_factor_zero_debt, Decimal)
        
        print("✅ Health factor calculation tests passed")
    
    def test_calculate_weighted_health_factor(self):
        """Test weighted health factor calculation."""
        # Test with multiple collateral types
        collateral_data = {
            'weeth': {
                'value': Decimal("60000"),
                'liquidation_threshold': Decimal("0.80")
            },
            'wsteth': {
                'value': Decimal("40000"),
                'liquidation_threshold': Decimal("0.75")
            }
        }
        
        debt_value = Decimal("70000")
        
        weighted_health = HealthCalculator.calculate_weighted_health_factor(collateral_data, debt_value)
        
        # Calculate expected weighted liquidation value
        # weeth: 60000 * 0.80 = 48000
        # wsteth: 40000 * 0.75 = 30000
        # Total liquidation value: 78000
        # Health factor: 78000 / 70000 = 1.114
        expected_liquidation_value = Decimal("60000") * Decimal("0.80") + Decimal("40000") * Decimal("0.75")
        expected_health = expected_liquidation_value / debt_value
        assert abs(weighted_health - expected_health) < Decimal("0.001")
        
        print("✅ Weighted health factor calculation tests passed")
    
    def test_calculate_distance_to_liquidation(self):
        """Test distance to liquidation calculation."""
        # Test standard case
        current_health_factor = Decimal("1.5")
        liquidation_threshold = Decimal("1.0")
        
        distance = HealthCalculator.calculate_distance_to_liquidation(current_health_factor, liquidation_threshold)
        
        # Distance = (current_health_factor - liquidation_threshold) / liquidation_threshold
        # = (1.5 - 1.0) / 1.0 = 0.5 = 50%
        expected = Decimal("0.5")
        assert abs(distance - expected) < Decimal("0.001")
        
        # Test at liquidation threshold
        distance_at_liquidation = HealthCalculator.calculate_distance_to_liquidation(
            liquidation_threshold, liquidation_threshold
        )
        assert distance_at_liquidation == Decimal("0")
        
        # Test below liquidation threshold
        distance_below = HealthCalculator.calculate_distance_to_liquidation(
            Decimal("0.8"), liquidation_threshold
        )
        assert distance_below < Decimal("0")  # Negative distance
        
        print("✅ Distance to liquidation calculation tests passed")
    
    def test_calculate_risk_score(self):
        """Test risk score calculation."""
        # Test with individual risk factors
        health_factor = Decimal("1.2")
        ltv_ratio = Decimal("0.75")
        margin_ratio = Decimal("0.8")
        volatility = Decimal("0.3")
        
        risk_score = HealthCalculator.calculate_risk_score(
            health_factor, ltv_ratio, margin_ratio, volatility
        )
        
        # Should be a weighted combination of risk factors
        # Implementation dependent - verify it's calculated
        assert isinstance(risk_score, Decimal)
        assert Decimal("0") <= risk_score <= Decimal("1")  # Should be normalized
        
        # Test with high risk factors
        high_risk_factors = {
            'health_factor': Decimal("1.05"),  # Close to liquidation
            'ltv_ratio': Decimal("0.90"),      # High LTV
            'volatility': Decimal("0.8"),      # High volatility
            'liquidity_risk': Decimal("0.5")   # High liquidity risk
        }
        
        high_risk_score = HealthCalculator.calculate_risk_score(high_risk_factors)
        assert high_risk_score > risk_score  # Should be higher risk
        
        print("✅ Risk score calculation tests passed")
    
    def test_calculate_safe_withdrawal_amount(self):
        """Test safe withdrawal amount calculation."""
        # Test standard case
        total_collateral = Decimal("100000")
        current_debt = Decimal("60000")
        liquidation_threshold = Decimal("0.85")
        safety_buffer = Decimal("0.1")  # 10% safety buffer
        
        safe_withdrawal = HealthCalculator.calculate_safe_withdrawal_amount(
            total_collateral, current_debt, liquidation_threshold, safety_buffer
        )
        
        # Maximum safe debt = total_collateral * liquidation_threshold * (1 - safety_buffer)
        # = 100000 * 0.85 * 0.9 = 76500
        # Current debt: 60000
        # Safe withdrawal = 76500 - 60000 = 16500
        max_safe_debt = total_collateral * liquidation_threshold * (Decimal("1") - safety_buffer)
        expected_withdrawal = max_safe_debt - current_debt
        assert abs(safe_withdrawal - expected_withdrawal) < Decimal("0.01")
        
        # Test with high debt (no safe withdrawal)
        high_debt = Decimal("80000")
        safe_withdrawal_high = HealthCalculator.calculate_safe_withdrawal_amount(
            total_collateral, high_debt, liquidation_threshold, safety_buffer
        )
        assert safe_withdrawal_high <= Decimal("0")  # Should be zero or negative
        
        print("✅ Safe withdrawal amount calculation tests passed")
    
    def test_calculate_safe_borrow_amount(self):
        """Test safe borrow amount calculation."""
        # Test standard case
        total_collateral = Decimal("100000")
        current_debt = Decimal("60000")
        liquidation_threshold = Decimal("0.85")
        safety_buffer = Decimal("0.1")  # 10% safety buffer
        
        safe_borrow = HealthCalculator.calculate_safe_borrow_amount(
            total_collateral, current_debt, liquidation_threshold, safety_buffer
        )
        
        # Maximum safe debt = total_collateral * liquidation_threshold * (1 - safety_buffer)
        # = 100000 * 0.85 * 0.9 = 76500
        # Current debt: 60000
        # Safe borrow = 76500 - 60000 = 16500
        max_safe_debt = total_collateral * liquidation_threshold * (Decimal("1") - safety_buffer)
        expected_borrow = max_safe_debt - current_debt
        assert abs(safe_borrow - expected_borrow) < Decimal("0.01")
        
        # Test with no available borrowing capacity
        high_debt = Decimal("80000")
        safe_borrow_high = HealthCalculator.calculate_safe_borrow_amount(
            total_collateral, high_debt, liquidation_threshold, safety_buffer
        )
        assert safe_borrow_high <= Decimal("0")  # Should be zero or negative
        
        print("✅ Safe borrow amount calculation tests passed")
    
    def test_calculate_required_collateral_for_health(self):
        """Test required collateral calculation for target health factor."""
        # Test standard case
        current_debt = Decimal("60000")
        target_health_factor = Decimal("1.5")
        liquidation_threshold = Decimal("0.85")
        
        required_collateral = HealthCalculator.calculate_required_collateral_for_health(
            current_debt, target_health_factor, liquidation_threshold
        )
        
        # Required collateral = current_debt * target_health_factor / liquidation_threshold
        # = 60000 * 1.5 / 0.85 = 105882.35
        expected = current_debt * target_health_factor / liquidation_threshold
        assert abs(required_collateral - expected) < Decimal("0.01")
        
        # Test with higher target health factor
        higher_target = Decimal("2.0")
        required_collateral_higher = HealthCalculator.calculate_required_collateral_for_health(
            current_debt, higher_target, liquidation_threshold
        )
        assert required_collateral_higher > required_collateral
        
        # Test with lower target health factor
        lower_target = Decimal("1.2")
        required_collateral_lower = HealthCalculator.calculate_required_collateral_for_health(
            current_debt, lower_target, liquidation_threshold
        )
        assert required_collateral_lower < required_collateral
        
        print("✅ Required collateral for health calculation tests passed")
    
    def test_multi_asset_health_calculations(self):
        """Test health calculations with multiple assets."""
        # Test with mixed collateral types
        collateral_by_token = {
            'weeth': Decimal("50000"),
            'wsteth': Decimal("30000"),
            'usdc': Decimal("20000")
        }
        
        debt_by_token = {
            'weeth': Decimal("30000"),
            'wsteth': Decimal("20000"),
            'usdc': Decimal("10000")
        }
        
        liquidation_thresholds = {
            'weeth': Decimal("0.80"),
            'wsteth': Decimal("0.75"),
            'usdc': Decimal("0.90")
        }
        
        # Calculate weighted health factor
        weighted_health = HealthCalculator.calculate_weighted_health_factor(
            collateral_by_token, debt_by_token, liquidation_thresholds
        )
        
        # Calculate expected liquidation value
        total_debt = sum(debt_by_token.values())
        expected_liquidation_value = (
            Decimal("50000") * Decimal("0.80") +
            Decimal("30000") * Decimal("0.75") +
            Decimal("20000") * Decimal("0.90")
        )
        expected_health = expected_liquidation_value / total_debt
        assert abs(weighted_health - expected_health) < Decimal("0.001")
        
        print("✅ Multi-asset health calculation tests passed")
    
    def test_health_factor_with_fees(self):
        """Test health factor calculations with fees and costs."""
        # Test with borrowing fees
        collateral_value = Decimal("100000")
        debt_value = Decimal("75000")
        borrowing_fee_rate = Decimal("0.001")  # 0.1%
        liquidation_threshold = Decimal("0.85")
        
        # Calculate effective debt including fees
        borrowing_fee = debt_value * borrowing_fee_rate
        effective_debt = debt_value + borrowing_fee
        
        health_factor_with_fees = HealthCalculator.calculate_health_factor(
            collateral_value, effective_debt, liquidation_threshold
        )
        
        expected_health = collateral_value * liquidation_threshold / effective_debt
        assert abs(health_factor_with_fees - expected_health) < Decimal("0.001")
        
        # Test with collateral slippage
        collateral_slippage_rate = Decimal("0.002")  # 0.2%
        effective_collateral = collateral_value * (Decimal("1") - collateral_slippage_rate)
        
        health_factor_with_slippage = HealthCalculator.calculate_health_factor(
            effective_collateral, debt_value, liquidation_threshold
        )
        
        expected_health_slippage = effective_collateral * liquidation_threshold / debt_value
        assert abs(health_factor_with_slippage - expected_health_slippage) < Decimal("0.001")
        
        print("✅ Health factor with fees calculation tests passed")
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with zero values
        zero_health = HealthCalculator.calculate_health_factor(Decimal("0"), Decimal("0"), Decimal("0.85"))
        # Should handle zero values gracefully
        assert isinstance(zero_health, Decimal)
        
        # Test with very small values
        small_health = HealthCalculator.calculate_health_factor(
            Decimal("0.01"), Decimal("0.005"), Decimal("0.85")
        )
        assert isinstance(small_health, Decimal)
        
        # Test with very large values
        large_health = HealthCalculator.calculate_health_factor(
            Decimal("1000000"), Decimal("750000"), Decimal("0.85")
        )
        expected_large = Decimal("1000000") * Decimal("0.85") / Decimal("750000")
        assert abs(large_health - expected_large) < Decimal("0.001")
        
        # Test with negative values (should handle gracefully)
        negative_health = HealthCalculator.calculate_health_factor(
            Decimal("-1000"), Decimal("500"), Decimal("0.85")
        )
        # Implementation should handle negative values
        assert isinstance(negative_health, Decimal)
        
        print("✅ Edge cases tests passed")
    
    def test_precision_handling(self):
        """Test precision handling with Decimal arithmetic."""
        # Test with high precision values
        precise_collateral = Decimal("100000.123456789")
        precise_debt = Decimal("75000.987654321")
        precise_threshold = Decimal("0.851234567")
        
        precise_health = HealthCalculator.calculate_health_factor(
            precise_collateral, precise_debt, precise_threshold
        )
        expected_precise = precise_collateral * precise_threshold / precise_debt
        assert abs(precise_health - expected_precise) < Decimal("0.000000001")
        
        # Test distance calculation with precision
        precise_distance = HealthCalculator.calculate_distance_to_liquidation(
            precise_health, Decimal("1.0"), True
        )
        expected_distance = (precise_health - Decimal("1.0")) / Decimal("1.0")
        assert abs(precise_distance - expected_distance) < Decimal("0.000000001")
        
        print("✅ Precision handling tests passed")


if __name__ == "__main__":
    # Run tests
    test_instance = TestHealthCalculator()
    
    print("🧪 Testing Health Calculator...")
    
    try:
        test_instance.test_calculate_health_factor()
        test_instance.test_calculate_weighted_health_factor()
        test_instance.test_calculate_distance_to_liquidation()
        test_instance.test_calculate_risk_score()
        test_instance.test_calculate_safe_withdrawal_amount()
        test_instance.test_calculate_safe_borrow_amount()
        test_instance.test_calculate_required_collateral_for_health()
        test_instance.test_multi_asset_health_calculations()
        test_instance.test_health_factor_with_fees()
        test_instance.test_edge_cases()
        test_instance.test_precision_handling()
        
        print("\n✅ All Health Calculator tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
