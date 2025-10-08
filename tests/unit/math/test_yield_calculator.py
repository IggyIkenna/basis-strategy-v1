#!/usr/bin/env python3
"""
Test Yield Calculator - Pure mathematical yield calculations.
"""

import pytest
import sys
import os
from decimal import Decimal
import math

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.core.math.yield_calculator import YieldCalculator


class TestYieldCalculator:
    """Test Yield Calculator mathematical functions."""
    
    def test_apy_to_apr_conversion(self):
        """Test APY to APR conversion."""
        # Test standard case
        apy = Decimal("0.05")  # 5% APY
        apr = YieldCalculator.apy_to_apr(apy)
        expected = Decimal(str(math.log(1.05)))
        assert abs(apr - expected) < Decimal("0.0001")
        
        # Test zero case
        apy_zero = Decimal("0")
        apr_zero = YieldCalculator.apy_to_apr(apy_zero)
        assert apr_zero == Decimal("0")
        
        # Test negative case
        apy_neg = Decimal("-0.1")  # -10% APY
        apr_neg = YieldCalculator.apy_to_apr(apy_neg)
        expected_neg = Decimal(str(math.log(0.9)))
        assert abs(apr_neg - expected_neg) < Decimal("0.0001")
        
        print("✅ APY to APR conversion tests passed")
    
    def test_apr_to_apy_conversion(self):
        """Test APR to APY conversion."""
        # Test standard case
        apr = Decimal("0.05")  # 5% APR
        apy = YieldCalculator.apr_to_apy(apr, 365)
        expected = Decimal("0.051267")  # Approximate
        assert abs(apy - expected) < Decimal("0.001")
        
        # Test zero case
        apr_zero = Decimal("0")
        apy_zero = YieldCalculator.apr_to_apy(apr_zero)
        assert apy_zero == Decimal("0")
        
        # Test different compounding periods
        apr_monthly = Decimal("0.12")  # 12% APR
        apy_monthly = YieldCalculator.apr_to_apy(apr_monthly, 12)
        apy_daily = YieldCalculator.apr_to_apy(apr_monthly, 365)
        
        # Daily compounding should be higher than monthly
        assert apy_daily > apy_monthly
        
        print("✅ APR to APY conversion tests passed")
    
    def test_simple_yield_calculation(self):
        """Test simple yield calculation."""
        # Test positive yield
        principal = Decimal("10000")
        rate = Decimal("0.05")  # 5% rate
        time_fraction = Decimal("1")  # 1 year
        
        yield_amount = YieldCalculator.calculate_simple_yield(principal, rate, time_fraction)
        expected = Decimal("500")  # 10000 * 0.05 * 1 = 500
        assert abs(yield_amount - expected) < Decimal("0.0001")
        
        # Test negative yield
        rate_neg = Decimal("-0.05")  # -5% rate
        yield_amount_neg = YieldCalculator.calculate_simple_yield(principal, rate_neg, time_fraction)
        expected_neg = Decimal("-500")  # 10000 * -0.05 * 1 = -500
        assert abs(yield_amount_neg - expected_neg) < Decimal("0.0001")
        
        # Test zero yield
        rate_zero = Decimal("0")  # 0% rate
        yield_amount_zero = YieldCalculator.calculate_simple_yield(principal, rate_zero, time_fraction)
        assert yield_amount_zero == Decimal("0")
        
        print("✅ Simple yield calculation tests passed")
    
    def test_compound_yield_calculation(self):
        """Test compound yield calculation."""
        # Test positive compound yield
        principal = Decimal("10000")
        rate = Decimal("0.05")  # 5% rate
        time_fraction = Decimal("1")  # 1 year
        compounding_periods = 365  # Daily compounding
        
        yield_amount = YieldCalculator.calculate_compound_yield(
            principal, rate, time_fraction, compounding_periods
        )
        
        # Should be close to simple yield for small values
        simple_yield = YieldCalculator.calculate_simple_yield(principal, rate, time_fraction)
        assert abs(yield_amount - simple_yield) < Decimal("0.01")
        
        print("✅ Compound yield calculation tests passed")
    
    def test_net_yield_calculation(self):
        """Test net yield calculation after costs."""
        # Test with costs
        gross_yields = {
            'staking': Decimal("0.05"),
            'lending': Decimal("0.03")
        }
        costs = {
            'fees': Decimal("0.01"),
            'gas': Decimal("0.005")
        }
        
        net_yield = YieldCalculator.calculate_net_yield(gross_yields, costs)
        expected = Decimal("0.065")  # 0.08 - 0.015 = 0.065
        assert abs(net_yield - expected) < Decimal("0.0001")
        
        # Test with zero costs
        costs_zero = {'fees': Decimal("0"), 'gas': Decimal("0")}
        net_yield_zero = YieldCalculator.calculate_net_yield(gross_yields, costs_zero)
        expected_zero = Decimal("0.08")  # 0.05 + 0.03 = 0.08
        assert abs(net_yield_zero - expected_zero) < Decimal("0.0001")
        
        # Test with costs higher than yield
        high_costs = {'fees': Decimal("0.10"), 'gas': Decimal("0.00")}
        net_yield_negative = YieldCalculator.calculate_net_yield(gross_yields, high_costs)
        expected_negative = Decimal("-0.02")  # 0.08 - 0.10 = -0.02
        assert abs(net_yield_negative - expected_negative) < Decimal("0.0001")
        
        print("✅ Net yield calculation tests passed")
    
    def test_staking_yield_calculation(self):
        """Test staking yield calculation."""
        # Test with staking rewards
        staked_amount = Decimal("1000")
        staking_apr = Decimal("0.05")  # 5% APR
        time_days = 365  # 1 year
        
        staking_yield = YieldCalculator.calculate_staking_yield(staked_amount, staking_apr, time_days)
        expected = Decimal("50")  # 1000 * 0.05 * (365/365) = 50
        assert abs(staking_yield - expected) < Decimal("0.0001")
        
        # Test with zero rewards
        staking_yield_zero = YieldCalculator.calculate_staking_yield(staked_amount, Decimal("0"), time_days)
        assert staking_yield_zero == Decimal("0")
        
        print("✅ Staking yield calculation tests passed")
    
    def test_funding_yield_calculation(self):
        """Test funding yield calculation."""
        # Test positive funding
        position_size = Decimal("10000")
        funding_rate_8h = Decimal("0.0001")  # 0.01% per 8 hours
        periods = 3  # 3 periods per day
        
        funding_yield = YieldCalculator.calculate_funding_yield(position_size, funding_rate_8h, periods)
        expected = Decimal("3")  # 10000 * 0.0001 * 3 = 3
        assert abs(funding_yield - expected) < Decimal("0.0001")
        
        # Test negative funding (paid)
        funding_rate_8h_neg = Decimal("-0.0001")  # -0.01% per 8 hours
        funding_yield_neg = YieldCalculator.calculate_funding_yield(position_size, funding_rate_8h_neg, periods)
        expected_neg = Decimal("-3")  # 10000 * -0.0001 * 3 = -3
        assert abs(funding_yield_neg - expected_neg) < Decimal("0.0001")
        
        print("✅ Funding yield calculation tests passed")
    
    def test_lending_yield_calculation(self):
        """Test lending yield calculation."""
        # Test with interest earned
        supplied_amount = Decimal("10000")
        supply_apr = Decimal("0.03")  # 3% APR
        borrowed_amount = Decimal("5000")
        borrow_apr = Decimal("0.05")  # 5% APR
        time_days = 365  # 1 year
        
        lending_yield = YieldCalculator.calculate_lending_yield(
            supplied_amount, supply_apr, borrowed_amount, borrow_apr, time_days
        )
        expected = Decimal("50")  # (10000 * 0.03 - 5000 * 0.05) * (365/365) = 300 - 250 = 50
        assert abs(lending_yield - expected) < Decimal("0.0001")
        
        # Test with zero interest
        lending_yield_zero = YieldCalculator.calculate_lending_yield(
            supplied_amount, Decimal("0"), borrowed_amount, Decimal("0"), time_days
        )
        assert lending_yield_zero == Decimal("0")
        
        print("✅ Lending yield calculation tests passed")
    
    def test_blended_apr_calculation(self):
        """Test blended APR calculation."""
        # Test with multiple yield sources
        components = [
            {'apr': Decimal("0.05"), 'weight': Decimal("0.5")},  # staking: 5% * 50%
            {'apr': Decimal("0.03"), 'weight': Decimal("0.3")},  # lending: 3% * 30%
            {'apr': Decimal("0.01"), 'weight': Decimal("0.2")}   # funding: 1% * 20%
        ]
        
        blended_apr = YieldCalculator.calculate_blended_apr(components)
        expected = Decimal("0.05") * Decimal("0.5") + Decimal("0.03") * Decimal("0.3") + Decimal("0.01") * Decimal("0.2")
        assert abs(blended_apr - expected) < Decimal("0.0001")
        
        # Test with single yield source
        single_component = [{'apr': Decimal("0.05"), 'weight': Decimal("1.0")}]
        
        single_blended = YieldCalculator.calculate_blended_apr(single_component)
        assert single_blended == Decimal("0.05")
        
        print("✅ Blended APR calculation tests passed")
    
    def test_effective_yield_calculation(self):
        """Test effective yield calculation with fees."""
        # Test with leverage and borrow costs
        base_yield = Decimal("0.08")  # 8% base yield
        leverage = Decimal("2.0")  # 2x leverage
        borrow_cost = Decimal("0.03")  # 3% borrow cost
        
        effective_yield = YieldCalculator.calculate_effective_yield(base_yield, leverage, borrow_cost)
        expected = Decimal("0.13")  # 8% * 2 - 3% = 13%
        assert abs(effective_yield - expected) < Decimal("0.0001")
        
        # Test with zero borrow cost
        effective_yield_zero = YieldCalculator.calculate_effective_yield(base_yield, leverage, Decimal("0"))
        expected_zero = Decimal("0.16")  # 8% * 2 - 0% = 16%
        assert abs(effective_yield_zero - expected_zero) < Decimal("0.0001")
        
        print("✅ Effective yield calculation tests passed")
    
    def test_impermanent_loss_calculation(self):
        """Test impermanent loss calculation."""
        # Test with price increase
        initial_price = Decimal("100")
        current_price = Decimal("200")  # 100% increase
        
        il = YieldCalculator.calculate_impermanent_loss(initial_price, current_price)
        # IL should be negative (loss) when price increases
        assert il < Decimal("0")
        
        # Test with price decrease
        current_price_decrease = Decimal("50")  # 50% decrease
        
        il_decrease = YieldCalculator.calculate_impermanent_loss(initial_price, current_price_decrease)
        # IL should be negative (loss) when price decreases
        assert il_decrease < Decimal("0")
        
        # Test with no price change
        il_no_change = YieldCalculator.calculate_impermanent_loss(initial_price, initial_price)
        assert il_no_change == Decimal("0")
        
        print("✅ Impermanent loss calculation tests passed")
    
    def test_total_return_calculation(self):
        """Test total return calculation."""
        # Test with positive returns
        initial_value = Decimal("10000")
        current_value = Decimal("11000")
        fees_paid = Decimal("50")
        
        total_return = YieldCalculator.calculate_total_return(initial_value, current_value, fees_paid)
        expected = Decimal("0.095")  # 9.5% (1000 - 50) / 10000
        assert abs(total_return - expected) < Decimal("0.0001")
        
        # Test with negative returns
        current_value_neg = Decimal("9000")
        total_return_neg = YieldCalculator.calculate_total_return(initial_value, current_value_neg, fees_paid)
        expected_neg = Decimal("-0.105")  # -10.5% (-1000 - 50) / 10000
        assert abs(total_return_neg - expected_neg) < Decimal("0.0001")
        
        print("✅ Total return calculation tests passed")
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with very small values
        small_principal = Decimal("0.01")
        small_value = Decimal("0.0105")
        small_yield = YieldCalculator.calculate_simple_yield(small_principal, small_value, Decimal("1"))
        assert abs(small_yield - Decimal("0.05")) < Decimal("0.001")
        
        # Test with very large values
        large_principal = Decimal("1000000")
        large_value = Decimal("1050000")
        large_yield = YieldCalculator.calculate_simple_yield(large_principal, large_value, Decimal("1"))
        assert abs(large_yield - Decimal("0.05")) < Decimal("0.001")
        
        # Test division by zero protection
        zero_principal = Decimal("0")
        zero_yield = YieldCalculator.calculate_simple_yield(zero_principal, Decimal("100"), Decimal("1"))
        # Should handle gracefully (implementation dependent)
        assert isinstance(zero_yield, Decimal)
        
        print("✅ Edge cases tests passed")


if __name__ == "__main__":
    # Run tests
    test_instance = TestYieldCalculator()
    
    print("🧪 Testing Yield Calculator...")
    
    try:
        test_instance.test_apy_to_apr_conversion()
        test_instance.test_apr_to_apy_conversion()
        test_instance.test_simple_yield_calculation()
        test_instance.test_compound_yield_calculation()
        test_instance.test_net_yield_calculation()
        test_instance.test_staking_yield_calculation()
        test_instance.test_funding_yield_calculation()
        test_instance.test_lending_yield_calculation()
        test_instance.test_blended_apr_calculation()
        test_instance.test_effective_yield_calculation()
        test_instance.test_impermanent_loss_calculation()
        test_instance.test_total_return_calculation()
        test_instance.test_edge_cases()
        
        print("\n✅ All Yield Calculator tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
