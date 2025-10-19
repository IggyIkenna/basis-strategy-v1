"""Unit tests for LTV Calculator."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from backend.src.basis_strategy_v1.core.math.ltv_calculator import LTVCalculator, ERROR_CODES


class TestLTVCalculator:
    """Test LTV Calculator functionality."""

    def test_calculate_current_ltv_healthy_position(self):
        """Test current LTV calculation with healthy position."""
        collateral_value = Decimal("100000")
        debt_value = Decimal("50000")
        
        ltv = LTVCalculator.calculate_current_ltv(collateral_value, debt_value)
        
        assert ltv == Decimal("0.5")

    def test_calculate_current_ltv_unhealthy_position(self):
        """Test current LTV calculation with unhealthy position."""
        collateral_value = Decimal("50000")
        debt_value = Decimal("80000")
        
        ltv = LTVCalculator.calculate_current_ltv(collateral_value, debt_value)
        
        assert ltv == Decimal("1.6")

    def test_calculate_current_ltv_no_collateral(self):
        """Test current LTV calculation with no collateral."""
        collateral_value = Decimal("0")
        debt_value = Decimal("10000")
        
        ltv = LTVCalculator.calculate_current_ltv(collateral_value, debt_value)
        
        assert ltv == Decimal("1")

    def test_calculate_current_ltv_no_debt(self):
        """Test current LTV calculation with no debt."""
        collateral_value = Decimal("100000")
        debt_value = Decimal("0")
        
        ltv = LTVCalculator.calculate_current_ltv(collateral_value, debt_value)
        
        assert ltv == Decimal("0")

    def test_calculate_projected_ltv_after_borrowing(self):
        """Test projected LTV calculation after borrowing."""
        current_collateral_value = Decimal("100000")
        current_debt_value = Decimal("50000")
        additional_borrowing_usd = Decimal("20000")
        
        projected_ltv = LTVCalculator.calculate_projected_ltv_after_borrowing(
            current_collateral_value, current_debt_value, additional_borrowing_usd
        )
        
        # Expected: (50000 + 20000) / (100000 + 20000 * 0.95) = 70000 / 119000 = 0.588
        expected = Decimal("70000") / Decimal("119000")
        assert abs(projected_ltv - expected) < Decimal("0.001")

    def test_calculate_projected_ltv_custom_efficiency(self):
        """Test projected LTV calculation with custom efficiency."""
        current_collateral_value = Decimal("100000")
        current_debt_value = Decimal("50000")
        additional_borrowing_usd = Decimal("20000")
        collateral_efficiency = Decimal("0.8")
        
        projected_ltv = LTVCalculator.calculate_projected_ltv_after_borrowing(
            current_collateral_value, current_debt_value, additional_borrowing_usd, collateral_efficiency
        )
        
        # Expected: (50000 + 20000) / (100000 + 20000 * 0.8) = 70000 / 116000 = 0.603
        expected = Decimal("70000") / Decimal("116000")
        assert abs(projected_ltv - expected) < Decimal("0.001")

    def test_get_max_ltv_for_collateral_mix_single_token(self):
        """Test max LTV calculation for single token collateral."""
        collateral_composition = {"ETH": Decimal("100000")}
        is_borrowing_eth = False
        ltv_config = {
            "standard_limits": {"ETH": 0.8, "BTC": 0.7},
            "emode_limits": {"wstETH_ETH": 0.93, "weETH_ETH": 0.93},
            "market_risk_buffer": 0.05,
            "basis_risk_buffer": 0.02
        }
        
        max_ltv = LTVCalculator.get_max_ltv_for_collateral_mix(
            collateral_composition, is_borrowing_eth, ltv_config
        )
        
        assert max_ltv == Decimal("0.8")

    def test_get_max_ltv_for_collateral_mix_multiple_tokens(self):
        """Test max LTV calculation for multiple token collateral."""
        collateral_composition = {
            "ETH": Decimal("60000"),
            "BTC": Decimal("40000")
        }
        is_borrowing_eth = False
        ltv_config = {
            "standard_limits": {"ETH": 0.8, "BTC": 0.7},
            "emode_limits": {"wstETH_ETH": 0.93, "weETH_ETH": 0.93},
            "market_risk_buffer": 0.05,
            "basis_risk_buffer": 0.02
        }
        
        max_ltv = LTVCalculator.get_max_ltv_for_collateral_mix(
            collateral_composition, is_borrowing_eth, ltv_config
        )
        
        # Expected: (60000 * 0.8 + 40000 * 0.7) / 100000 = (48000 + 28000) / 100000 = 0.76
        expected = Decimal("76000") / Decimal("100000")
        assert max_ltv == expected

    def test_get_max_ltv_emode_eligible(self):
        """Test max LTV calculation with e-mode eligibility."""
        collateral_composition = {"wstETH": Decimal("100000")}
        is_borrowing_eth = True
        ltv_config = {
            "standard_limits": {"ETH": 0.8, "BTC": 0.7},
            "emode_limits": {"wstETH_ETH": 0.93, "weETH_ETH": 0.93},
            "market_risk_buffer": 0.05,
            "basis_risk_buffer": 0.02
        }
        
        max_ltv = LTVCalculator.get_max_ltv_for_collateral_mix(
            collateral_composition, is_borrowing_eth, ltv_config
        )
        
        assert max_ltv == Decimal("0.93")

    def test_get_max_ltv_conservative_mode(self):
        """Test max LTV calculation in conservative mode."""
        collateral_composition = {"ETH": Decimal("100000")}
        is_borrowing_eth = False
        ltv_config = {
            "standard_limits": {"ETH": 0.8, "BTC": 0.7},
            "emode_limits": {"wstETH_ETH": 0.93, "weETH_ETH": 0.93},
            "market_risk_buffer": 0.05,
            "basis_risk_buffer": 0.02
        }
        
        max_ltv = LTVCalculator.get_max_ltv_for_collateral_mix(
            collateral_composition, is_borrowing_eth, ltv_config, risk_mode="conservative"
        )
        
        # Expected: 0.8 / (1 + 0.05) = 0.8 / 1.05 = 0.762
        expected = Decimal("0.8") / Decimal("1.05")
        assert abs(max_ltv - expected) < Decimal("0.001")

    def test_get_max_ltv_no_collateral(self):
        """Test max LTV calculation with no collateral."""
        collateral_composition = {}
        is_borrowing_eth = False
        ltv_config = {
            "standard_limits": {"ETH": 0.8, "BTC": 0.7},
            "emode_limits": {"wstETH_ETH": 0.93, "weETH_ETH": 0.93},
            "market_risk_buffer": 0.05,
            "basis_risk_buffer": 0.02
        }
        
        max_ltv = LTVCalculator.get_max_ltv_for_collateral_mix(
            collateral_composition, is_borrowing_eth, ltv_config
        )
        
        assert max_ltv == Decimal("0.8")  # Default ETH limit

    def test_can_add_leverage_sufficient_headroom(self):
        """Test leverage check with sufficient headroom."""
        current_ltv = Decimal("0.5")
        safe_ltv = Decimal("0.8")
        min_headroom = Decimal("0.05")
        
        can_add, headroom = LTVCalculator.can_add_leverage(current_ltv, safe_ltv, min_headroom)
        
        assert can_add is True
        assert headroom == Decimal("0.3")

    def test_can_add_leverage_insufficient_headroom(self):
        """Test leverage check with insufficient headroom."""
        current_ltv = Decimal("0.78")
        safe_ltv = Decimal("0.8")
        min_headroom = Decimal("0.05")
        
        can_add, headroom = LTVCalculator.can_add_leverage(current_ltv, safe_ltv, min_headroom)
        
        assert can_add is False
        assert headroom == Decimal("0.02")

    def test_calculate_next_loop_capacity_healthy_position(self):
        """Test next loop capacity calculation with healthy position."""
        current_collateral_value = Decimal("100000")
        current_debt_value = Decimal("50000")
        max_safe_ltv = Decimal("0.8")
        strategy_config = {
            'leverage_factor': 1.2,
            'ltv': {
                'safe_ltv': {
                    'standard_borrowing': 0.8
                }
            }
        }
        
        capacity = LTVCalculator.calculate_next_loop_capacity(
            current_collateral_value, current_debt_value, max_safe_ltv, strategy_config
        )
        
        # Expected: 100000 * (0.8 - 0.5) * 1.2 = 100000 * 0.3 * 1.2 = 36000
        expected = Decimal("100000") * Decimal("0.3") * Decimal("1.2")
        assert capacity == expected

    def test_calculate_next_loop_capacity_no_collateral(self):
        """Test next loop capacity calculation with no collateral."""
        current_collateral_value = Decimal("0")
        current_debt_value = Decimal("50000")
        max_safe_ltv = Decimal("0.8")
        strategy_config = {
            'leverage_factor': 1.2,
            'ltv': {
                'safe_ltv': {
                    'standard_borrowing': 0.8
                }
            }
        }
        
        capacity = LTVCalculator.calculate_next_loop_capacity(
            current_collateral_value, current_debt_value, max_safe_ltv, strategy_config
        )
        
        assert capacity == Decimal("0")

    def test_calculate_health_factor_healthy_position(self):
        """Test health factor calculation with healthy position."""
        collateral_value = Decimal("100000")
        debt_value = Decimal("50000")
        liquidation_threshold = Decimal("0.85")
        
        health_factor = LTVCalculator.calculate_health_factor(
            collateral_value, debt_value, liquidation_threshold
        )
        
        # Expected: (100000 * 0.85) / 50000 = 85000 / 50000 = 1.7
        expected = Decimal("85000") / Decimal("50000")
        assert health_factor == expected

    def test_calculate_health_factor_no_debt(self):
        """Test health factor calculation with no debt."""
        collateral_value = Decimal("100000")
        debt_value = Decimal("0")
        liquidation_threshold = Decimal("0.85")
        
        health_factor = LTVCalculator.calculate_health_factor(
            collateral_value, debt_value, liquidation_threshold
        )
        
        assert health_factor == Decimal("999")

    def test_get_max_borrowing_capacity(self):
        """Test maximum borrowing capacity calculation."""
        collateral_value = Decimal("100000")
        max_ltv = Decimal("0.8")
        
        capacity = LTVCalculator.get_max_borrowing_capacity(collateral_value, max_ltv)
        
        assert capacity == Decimal("80000")

    def test_validate_ltv_safety_safe_operation(self):
        """Test LTV safety validation for safe operation."""
        projected_ltv = Decimal("0.6")
        max_safe_ltv = Decimal("0.8")
        
        is_safe, error_msg = LTVCalculator.validate_ltv_safety(
            projected_ltv, max_safe_ltv, "test_operation"
        )
        
        assert is_safe is True
        assert error_msg is None

    def test_validate_ltv_safety_unsafe_operation(self):
        """Test LTV safety validation for unsafe operation."""
        projected_ltv = Decimal("0.9")
        max_safe_ltv = Decimal("0.8")
        
        is_safe, error_msg = LTVCalculator.validate_ltv_safety(
            projected_ltv, max_safe_ltv, "test_operation"
        )
        
        assert is_safe is False
        assert "test_operation" in error_msg
        assert "0.900" in error_msg
        assert "0.800" in error_msg

    def test_get_emode_eligibility_eligible(self):
        """Test e-mode eligibility check for eligible pair."""
        collateral_token = "wstETH"
        debt_token = "ETH"
        
        is_eligible = LTVCalculator.get_emode_eligibility(collateral_token, debt_token)
        
        assert is_eligible is True

    def test_get_emode_eligibility_not_eligible(self):
        """Test e-mode eligibility check for non-eligible pair."""
        collateral_token = "ETH"
        debt_token = "USDT"
        
        is_eligible = LTVCalculator.get_emode_eligibility(collateral_token, debt_token)
        
        assert is_eligible is False

    def test_calculate_dynamic_ltv_target(self):
        """Test dynamic LTV target calculation."""
        max_ltv = Decimal("0.8")
        max_stake_spread_move = Decimal("0.05")
        safety_buffer = Decimal("0.02")
        
        dynamic_ltv = LTVCalculator.calculate_dynamic_ltv_target(
            max_ltv, max_stake_spread_move, safety_buffer
        )
        
        # Expected: 0.8 - 0.05 - 0.02 = 0.73
        assert dynamic_ltv == Decimal("0.73")

    def test_calculate_dynamic_ltv_target_minimum(self):
        """Test dynamic LTV target calculation with minimum constraint."""
        max_ltv = Decimal("0.8")
        max_stake_spread_move = Decimal("0.6")
        safety_buffer = Decimal("0.2")
        
        dynamic_ltv = LTVCalculator.calculate_dynamic_ltv_target(
            max_ltv, max_stake_spread_move, safety_buffer
        )
        
        # Expected: max(0.8 - 0.6 - 0.2, 0.1) = max(0, 0.1) = 0.1
        assert dynamic_ltv == Decimal("0.1")

    def test_calculate_leverage_headroom(self):
        """Test leverage headroom calculation."""
        current_ltv = Decimal("0.5")
        safe_ltv = Decimal("0.8")
        
        headroom = LTVCalculator.calculate_leverage_headroom(current_ltv, safe_ltv)
        
        assert headroom == Decimal("0.3")

    def test_calculate_leverage_headroom_negative(self):
        """Test leverage headroom calculation with negative result."""
        current_ltv = Decimal("0.9")
        safe_ltv = Decimal("0.8")
        
        headroom = LTVCalculator.calculate_leverage_headroom(current_ltv, safe_ltv)
        
        assert headroom == Decimal("0")

    def test_error_codes_defined(self):
        """Test that all error codes are properly defined."""
        expected_codes = [
            'LTV-001', 'LTV-002', 'LTV-003', 'LTV-004',
            'LTV-005', 'LTV-006', 'LTV-007', 'LTV-008'
        ]
        
        for code in expected_codes:
            assert code in ERROR_CODES
            assert ERROR_CODES[code] is not None
            assert len(ERROR_CODES[code]) > 0

    def test_decimal_precision_handling(self):
        """Test that calculations maintain proper decimal precision."""
        collateral_value = Decimal("100000.123456")
        debt_value = Decimal("50000.789012")
        
        ltv = LTVCalculator.calculate_current_ltv(collateral_value, debt_value)
        
        # Should maintain precision
        expected = debt_value / collateral_value
        assert abs(ltv - expected) < Decimal("0.000001")

    def test_edge_case_zero_values(self):
        """Test edge cases with zero values."""
        # Test with zero collateral and zero debt
        ltv = LTVCalculator.calculate_current_ltv(Decimal("0"), Decimal("0"))
        assert ltv == Decimal("0")
        
        # Test projected LTV with zero values
        projected_ltv = LTVCalculator.calculate_projected_ltv_after_borrowing(
            Decimal("0"), Decimal("0"), Decimal("0")
        )
        assert projected_ltv == Decimal("0")

    def test_boundary_conditions(self):
        """Test boundary conditions for LTV calculations."""
        # Test LTV at exactly 1.0
        ltv = LTVCalculator.calculate_current_ltv(Decimal("100000"), Decimal("100000"))
        assert ltv == Decimal("1.0")
        
        # Test leverage check at boundary
        can_add, headroom = LTVCalculator.can_add_leverage(
            Decimal("0.75"), Decimal("0.8"), Decimal("0.05")
        )
        assert can_add is False
        assert headroom == Decimal("0.05")
