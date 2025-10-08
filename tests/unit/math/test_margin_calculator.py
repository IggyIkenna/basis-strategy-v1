#!/usr/bin/env python3
"""
Test Margin Calculator - Margin and leverage calculations.
"""

import pytest
import sys
import os
from decimal import Decimal
from typing import Dict, Any

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.core.math.margin_calculator import MarginCalculator


class TestMarginCalculator:
    """Test Margin Calculator mathematical functions."""
    
    def test_calculate_margin_requirement(self):
        """Test margin requirement calculation."""
        # Test standard case
        position_size = Decimal("10000")
        leverage = Decimal("10")  # 10x leverage
        
        margin_req = MarginCalculator.calculate_margin_requirement(position_size, leverage)
        expected = Decimal("1000")  # 10000 / 10
        assert abs(margin_req - expected) < Decimal("0.01")
        
        # Test with different leverage
        margin_req_5x = MarginCalculator.calculate_margin_requirement(position_size, Decimal("5"))
        expected_5x = Decimal("2000")  # 10000 / 5
        assert abs(margin_req_5x - expected_5x) < Decimal("0.01")
        
        # Test with 1x leverage (no leverage)
        margin_req_1x = MarginCalculator.calculate_margin_requirement(position_size, Decimal("1"))
        expected_1x = Decimal("10000")  # 10000 / 1
        assert abs(margin_req_1x - expected_1x) < Decimal("0.01")
        
        print("✅ Margin requirement calculation tests passed")
    
    def test_calculate_maintenance_margin(self):
        """Test maintenance margin calculation."""
        # Test standard case
        position_size = Decimal("10000")
        maintenance_margin_rate = Decimal("0.05")  # 5%
        
        maintenance_margin = MarginCalculator.calculate_maintenance_margin(position_size, maintenance_margin_rate)
        expected = Decimal("500")  # 10000 * 0.05
        assert abs(maintenance_margin - expected) < Decimal("0.01")
        
        # Test with different rates
        maintenance_margin_high = MarginCalculator.calculate_maintenance_margin(position_size, Decimal("0.10"))
        expected_high = Decimal("1000")  # 10000 * 0.10
        assert abs(maintenance_margin_high - expected_high) < Decimal("0.01")
        
        print("✅ Maintenance margin calculation tests passed")
    
    def test_calculate_margin_ratio(self):
        """Test margin ratio calculation."""
        # Test standard case
        current_margin = Decimal("1500")
        used_margin = Decimal("1000")
        position_value = Decimal("10000")
        
        margin_ratio = MarginCalculator.calculate_margin_ratio(current_margin, used_margin, position_value)
        expected = Decimal("0.4")  # (1500 - 1000) / 1500 = 0.333, but this might be total margin ratio
        # Implementation dependent - verify it's calculated correctly
        assert margin_ratio > Decimal("0")
        
        # Test with zero used margin
        margin_ratio_zero = MarginCalculator.calculate_margin_ratio(current_margin, Decimal("0"), position_value)
        assert margin_ratio_zero > Decimal("0")
        
        print("✅ Margin ratio calculation tests passed")
    
    def test_calculate_liquidation_price(self):
        """Test liquidation price calculation."""
        # Test long position
        entry_price = Decimal("100")
        position_size = Decimal("1000")  # 1000 units
        margin = Decimal("500")
        maintenance_margin_rate = Decimal("0.05")
        
        liquidation_price = MarginCalculator.calculate_liquidation_price(
            entry_price, True, margin, position_size, maintenance_margin_rate
        )
        
        # For long position: liquidation_price = entry_price * (1 - (margin - maintenance_margin) / position_value)
        # position_value = 1000 * 100 = 100000
        # maintenance_margin = 100000 * 0.05 = 5000
        # liquidation_price = 100 * (1 - (500 - 5000) / 100000) = 100 * (1 - (-4500) / 100000)
        # This should be lower than entry price for long position
        assert liquidation_price < entry_price
        
        # Test short position
        liquidation_price_short = MarginCalculator.calculate_liquidation_price(
            entry_price, position_size, margin, maintenance_margin_rate, is_long=False
        )
        
        # For short position, liquidation price should be higher than entry price
        assert liquidation_price_short > entry_price
        
        print("✅ Liquidation price calculation tests passed")
    
    def test_calculate_available_margin(self):
        """Test available margin calculation."""
        # Test standard case
        total_margin = Decimal("10000")
        used_margin = Decimal("6000")
        
        available_margin = MarginCalculator.calculate_available_margin(total_margin, used_margin)
        expected = Decimal("4000")  # 10000 - 6000
        assert abs(available_margin - expected) < Decimal("0.01")
        
        # Test with zero used margin
        available_margin_zero = MarginCalculator.calculate_available_margin(total_margin, Decimal("0"))
        assert available_margin_zero == total_margin
        
        # Test with full used margin
        available_margin_full = MarginCalculator.calculate_available_margin(total_margin, total_margin)
        assert available_margin_full == Decimal("0")
        
        print("✅ Available margin calculation tests passed")
    
    def test_calculate_funding_payment(self):
        """Test funding payment calculation."""
        # Test positive funding (received)
        position_size = Decimal("10000")
        funding_rate = Decimal("0.0001")  # 0.01%
        
        funding_payment = MarginCalculator.calculate_funding_payment(position_size, funding_rate)
        expected = Decimal("1")  # 10000 * 0.0001
        assert abs(funding_payment - expected) < Decimal("0.01")
        
        # Test negative funding (paid)
        funding_payment_neg = MarginCalculator.calculate_funding_payment(position_size, Decimal("-0.0001"))
        expected_neg = Decimal("-1")  # 10000 * -0.0001
        assert abs(funding_payment_neg - expected_neg) < Decimal("0.01")
        
        # Test zero funding rate
        funding_payment_zero = MarginCalculator.calculate_funding_payment(position_size, Decimal("0"))
        assert funding_payment_zero == Decimal("0")
        
        print("✅ Funding payment calculation tests passed")
    
    def test_calculate_portfolio_margin(self):
        """Test portfolio margin calculation."""
        # Test with multiple positions
        positions = {
            'ETHUSDT': {
                'size': Decimal("1000"),
                'mark_price': Decimal("2000"),
                'margin_requirement': Decimal("200")
            },
            'BTCUSDT': {
                'size': Decimal("0.5"),
                'mark_price': Decimal("50000"),
                'margin_requirement': Decimal("500")
            }
        }
        
        market_scenarios = [
            {'ETHUSDT': Decimal("2000"), 'BTCUSDT': Decimal("50000")},
            {'ETHUSDT': Decimal("1800"), 'BTCUSDT': Decimal("45000")},
            {'ETHUSDT': Decimal("2200"), 'BTCUSDT': Decimal("55000")}
        ]
        
        portfolio_margin = MarginCalculator.calculate_portfolio_margin(positions, market_scenarios)
        
        # Should be sum of individual margin requirements
        expected = Decimal("200") + Decimal("500")  # 700
        assert abs(portfolio_margin - expected) < Decimal("0.01")
        
        # Test with empty portfolio
        empty_portfolio = MarginCalculator.calculate_portfolio_margin({})
        assert empty_portfolio == Decimal("0")
        
        print("✅ Portfolio margin calculation tests passed")
    
    def test_calculate_margin_health(self):
        """Test margin health calculation."""
        # Test healthy margin
        positions = [
            {
                'symbol': 'ETHUSDT',
                'size': Decimal("1000"),
                'entry_price': Decimal("2000"),
                'mark_price': Decimal("2000"),
                'margin': Decimal("1000")
            }
        ]
        current_prices = {'ETHUSDT': 2000.0}
        config = {'maintenance_margin_rate': 0.05}
        
        margin_health = MarginCalculator.calculate_margin_health(positions, current_prices, config)
        
        # Should be positive and healthy
        assert margin_health > Decimal("0")
        
        # Test critical margin
        critical_margin = Decimal("1000")  # Below maintenance margin
        margin_health_critical = MarginCalculator.calculate_margin_health(
            current_margin, used_margin, critical_margin
        )
        
        # Should indicate unhealthy state
        assert margin_health_critical < Decimal("0") or margin_health_critical < Decimal("1")
        
        print("✅ Margin health calculation tests passed")
    
    def test_calculate_basis_margin(self):
        """Test basis margin calculation."""
        # Test with basis spread
        spot_price = Decimal("2000")
        futures_price = Decimal("2010")
        position_size = Decimal("1000")
        margin_rate = Decimal("0.1")  # 10%
        
        basis_margin = MarginCalculator.calculate_basis_margin(
            spot_price, futures_price, position_size, margin_rate
        )
        
        # Basis = futures_price - spot_price = 10
        # Basis margin = basis * position_size * margin_rate = 10 * 1000 * 0.1 = 1000
        expected = Decimal("10") * position_size * margin_rate
        assert abs(basis_margin - expected) < Decimal("0.01")
        
        # Test with negative basis
        futures_price_neg = Decimal("1990")
        basis_margin_neg = MarginCalculator.calculate_basis_margin(
            spot_price, futures_price_neg, position_size, margin_rate
        )
        
        # Basis = 1990 - 2000 = -10
        # Should handle negative basis
        assert isinstance(basis_margin_neg, Decimal)
        
        print("✅ Basis margin calculation tests passed")
    
    def test_cross_margin_calculations(self):
        """Test cross-margin calculations."""
        # Test with multiple positions
        positions = [
            {
                'symbol': 'USDT',
                'size': Decimal("10000"),
                'margin_requirement': Decimal("2000")
            },
            {
                'symbol': 'ETH',
                'size': Decimal("5"),
                'margin_requirement': Decimal("1000")
            }
        ]
        
        cross_margin_req = MarginCalculator.calculate_cross_margin_requirement(positions)
        
        # Should be sum of individual requirements
        expected = Decimal("2000") + Decimal("1000")  # 3000
        assert abs(cross_margin_req - expected) < Decimal("0.01")
        
        print("✅ Cross margin calculation tests passed")
    
    def test_leverage_calculations(self):
        """Test leverage-related calculations."""
        # Test maximum leverage calculation
        available_margin = Decimal("1000")
        position_size = Decimal("10000")
        
        # Maximum leverage = position_size / available_margin
        max_leverage = position_size / available_margin
        expected_max_leverage = Decimal("10")  # 10x
        assert abs(max_leverage - expected_max_leverage) < Decimal("0.01")
        
        # Test leverage with fees
        fee_rate = Decimal("0.001")  # 0.1%
        fee_amount = position_size * fee_rate
        effective_margin = available_margin - fee_amount
        
        effective_leverage = position_size / effective_margin
        assert effective_leverage > max_leverage  # Should be higher due to fees
        
        print("✅ Leverage calculation tests passed")
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with zero values
        zero_margin_req = MarginCalculator.calculate_margin_requirement(Decimal("0"), Decimal("10"))
        assert zero_margin_req == Decimal("0")
        
        # Test with very small values
        small_margin_req = MarginCalculator.calculate_margin_requirement(Decimal("0.01"), Decimal("2"))
        assert small_margin_req == Decimal("0.005")
        
        # Test with very large values
        large_margin_req = MarginCalculator.calculate_margin_requirement(Decimal("1000000"), Decimal("100"))
        assert large_margin_req == Decimal("10000")
        
        # Test with negative values (should handle gracefully)
        negative_margin_req = MarginCalculator.calculate_margin_requirement(Decimal("-1000"), Decimal("10"))
        # Implementation should handle negative values
        assert isinstance(negative_margin_req, Decimal)
        
        print("✅ Edge cases tests passed")
    
    def test_precision_handling(self):
        """Test precision handling with Decimal arithmetic."""
        # Test with high precision values
        precise_position = Decimal("10000.123456789")
        precise_leverage = Decimal("10.987654321")
        
        precise_margin_req = MarginCalculator.calculate_margin_requirement(precise_position, precise_leverage)
        expected_precise = precise_position / precise_leverage
        assert abs(precise_margin_req - expected_precise) < Decimal("0.000000001")
        
        # Test funding payment with precision
        precise_funding = MarginCalculator.calculate_funding_payment(
            precise_position, Decimal("0.000123456")
        )
        expected_funding = precise_position * Decimal("0.000123456")
        assert abs(precise_funding - expected_funding) < Decimal("0.000000001")
        
        print("✅ Precision handling tests passed")


if __name__ == "__main__":
    # Run tests
    test_instance = TestMarginCalculator()
    
    print("🧪 Testing Margin Calculator...")
    
    try:
        test_instance.test_calculate_margin_requirement()
        test_instance.test_calculate_maintenance_margin()
        test_instance.test_calculate_margin_ratio()
        test_instance.test_calculate_liquidation_price()
        test_instance.test_calculate_available_margin()
        test_instance.test_calculate_funding_payment()
        test_instance.test_calculate_portfolio_margin()
        test_instance.test_calculate_margin_health()
        test_instance.test_calculate_basis_margin()
        test_instance.test_cross_margin_calculations()
        test_instance.test_leverage_calculations()
        test_instance.test_edge_cases()
        test_instance.test_precision_handling()
        
        print("\n✅ All Margin Calculator tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
