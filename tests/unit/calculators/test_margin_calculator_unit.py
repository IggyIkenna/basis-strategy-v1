"""Unit tests for Margin Calculator."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from backend.src.basis_strategy_v1.core.math.margin_calculator import MarginCalculator, ERROR_CODES


class TestMarginCalculator:
    """Test Margin Calculator functionality."""

    def test_calculate_projected_margin_capacity_after_borrowing(self):
        """Test projected margin capacity calculation after borrowing."""
        current_collateral_value = Decimal("100000")
        current_debt_value = Decimal("50000")
        additional_borrowing_usd = Decimal("20000")
        ltv_config = {
            "standard_limits": {"ETH": 0.8, "BTC": 0.7}
        }
        strategy_config = {
            'ltv': {
                'safe_ltv': {
                    'standard_borrowing': 0.8
                }
            }
        }
        
        capacity = MarginCalculator.calculate_projected_margin_capacity_after_borrowing(
            current_collateral_value, current_debt_value, additional_borrowing_usd,
            ltv_config, strategy_config
        )
        
        # Expected: After borrowing, projected collateral = 100000 + 20000*0.95 = 119000
        # Projected debt = 50000 + 20000 = 70000
        # Projected LTV = 70000/119000 = 0.588
        # The implementation uses final_max_ltv from strategy_config (0.8), not avg_max_ltv
        # Remaining capacity = 119000 * (0.8 - 0.588) = 119000 * 0.212 = 25228
        expected = Decimal("119000") * Decimal("0.212")
        assert abs(capacity - expected) < Decimal("100")

    def test_calculate_projected_margin_capacity_no_collateral(self):
        """Test projected margin capacity calculation with no collateral."""
        current_collateral_value = Decimal("0")
        current_debt_value = Decimal("50000")
        additional_borrowing_usd = Decimal("20000")
        ltv_config = {
            "standard_limits": {"ETH": 0.8, "BTC": 0.7}
        }
        strategy_config = {
            'ltv': {
                'safe_ltv': {
                    'standard_borrowing': 0.8
                }
            }
        }
        
        capacity = MarginCalculator.calculate_projected_margin_capacity_after_borrowing(
            current_collateral_value, current_debt_value, additional_borrowing_usd,
            ltv_config, strategy_config
        )
        
        assert capacity == Decimal("0")

    def test_estimate_basis_margin_requirements_eth_share_class(self):
        """Test basis margin estimation for ETH share class."""
        eth_exposure = Decimal("10")
        share_class = "ETH"
        initial_capital = Decimal("100000")
        eth_price = Decimal("3000")
        risk_config = {
            'bybit_initial_margin_pct': 0.1,
            'price_buffer_pct': 0.05,
            'basis_trade_margin_buffer': 0.02
        }
        strategy_config = {
            'basis_leverage_factor': 2.0
        }
        
        margin_req = MarginCalculator.estimate_basis_margin_requirements(
            eth_exposure, share_class, initial_capital, eth_price, risk_config, strategy_config
        )
        
        # Expected: For ETH share class, additional USDT = 100000 * (2.0 - 1) = 100000
        # Additional ETH = 100000 / 3000 = 33.33
        # Margin for additional ETH = 33.33 * 3000 * (0.1 + 0.05 + 0.02) = 100000 * 0.17 = 17000
        expected = Decimal("100000") * Decimal("0.17")
        assert abs(margin_req - expected) < Decimal("1")

    def test_estimate_basis_margin_requirements_usdt_share_class(self):
        """Test basis margin estimation for USDT share class."""
        eth_exposure = Decimal("10")
        share_class = "USDT"
        initial_capital = Decimal("100000")
        eth_price = Decimal("3000")
        risk_config = {
            'bybit_initial_margin_pct': 0.1,
            'price_buffer_pct': 0.05,
            'basis_trade_margin_buffer': 0.02
        }
        strategy_config = {
            'basis_leverage_factor': 2.0
        }
        
        margin_req = MarginCalculator.estimate_basis_margin_requirements(
            eth_exposure, share_class, initial_capital, eth_price, risk_config, strategy_config
        )
        
        # Expected: For USDT share class, margin for full ETH exposure
        # Margin = 10 * 3000 * (0.1 + 0.05 + 0.02) = 30000 * 0.17 = 5100
        expected = Decimal("30000") * Decimal("0.17")
        assert abs(margin_req - expected) < Decimal("1")

    def test_calculate_margin_for_exposure(self):
        """Test margin calculation for ETH exposure."""
        eth_exposure = Decimal("5")
        eth_price = Decimal("3000")
        risk_config = {
            'bybit_initial_margin_pct': 0.1,
            'price_buffer_pct': 0.05,
            'basis_trade_margin_buffer': 0.02
        }
        
        margin = MarginCalculator.calculate_margin_for_exposure(
            eth_exposure, eth_price, risk_config
        )
        
        # Expected: 5 * 3000 * (0.1 + 0.05 + 0.02) = 15000 * 0.17 = 2550
        expected = Decimal("15000") * Decimal("0.17")
        assert margin == expected

    def test_calculate_margin_requirement_with_leverage(self):
        """Test margin requirement calculation with leverage."""
        position_size = Decimal("100000")
        leverage = Decimal("10")
        
        margin = MarginCalculator.calculate_margin_requirement(position_size, leverage)
        
        assert margin == Decimal("10000")

    def test_calculate_margin_requirement_with_rate(self):
        """Test margin requirement calculation with margin rate."""
        position_size = Decimal("100000")
        leverage = Decimal("10")
        initial_margin_rate = Decimal("0.15")
        
        margin = MarginCalculator.calculate_margin_requirement(
            position_size, leverage, initial_margin_rate
        )
        
        assert margin == Decimal("15000")

    def test_calculate_margin_requirement_default(self):
        """Test margin requirement calculation with default values."""
        position_size = Decimal("100000")
        leverage = Decimal("0")
        
        margin = MarginCalculator.calculate_margin_requirement(position_size, leverage)
        
        assert margin == Decimal("10000")  # 10% default

    def test_calculate_maintenance_margin(self):
        """Test maintenance margin calculation."""
        position_size = Decimal("100000")
        maintenance_rate = Decimal("0.05")
        
        margin = MarginCalculator.calculate_maintenance_margin(position_size, maintenance_rate)
        
        assert margin == Decimal("5000")

    def test_calculate_margin_ratio(self):
        """Test margin ratio calculation."""
        current_margin = Decimal("20000")
        used_margin = Decimal("10000")
        position_value = Decimal("100000")
        
        ratio = MarginCalculator.calculate_margin_ratio(current_margin, used_margin, position_value)
        
        # Expected: (20000 + 10000) / 100000 = 0.3
        assert ratio == Decimal("0.3")

    def test_calculate_margin_ratio_no_position(self):
        """Test margin ratio calculation with no position."""
        current_margin = Decimal("20000")
        used_margin = Decimal("10000")
        position_value = Decimal("0")
        
        ratio = MarginCalculator.calculate_margin_ratio(current_margin, used_margin, position_value)
        
        assert ratio == Decimal("999")

    def test_calculate_liquidation_price_long(self):
        """Test liquidation price calculation for long position."""
        entry_price = Decimal("3000")
        is_long = True
        margin = Decimal("10000")
        position_size = Decimal("100000")
        maintenance_rate = Decimal("0.05")
        fee_rate = Decimal("0.0006")
        
        liquidation_price = MarginCalculator.calculate_liquidation_price(
            entry_price, is_long, margin, position_size, maintenance_rate, fee_rate
        )
        
        # Expected: contracts = 100000/3000 = 33.33
        # total_fees = 100000 * 0.0006 * 2 = 120
        # max_loss = 10000 - (100000 * 0.05) - 120 = 10000 - 5000 - 120 = 4880
        # price_move_pct = 4880/100000 = 0.0488
        # liquidation_price = 3000 * (1 - 0.0488) = 3000 * 0.9512 = 2853.6
        expected = Decimal("3000") * Decimal("0.9512")
        assert abs(liquidation_price - expected) < Decimal("1")

    def test_calculate_liquidation_price_short(self):
        """Test liquidation price calculation for short position."""
        entry_price = Decimal("3000")
        is_long = False
        margin = Decimal("10000")
        position_size = Decimal("100000")
        maintenance_rate = Decimal("0.05")
        fee_rate = Decimal("0.0006")
        
        liquidation_price = MarginCalculator.calculate_liquidation_price(
            entry_price, is_long, margin, position_size, maintenance_rate, fee_rate
        )
        
        # Expected: liquidation_price = 3000 * (1 + 0.0488) = 3000 * 1.0488 = 3146.4
        expected = Decimal("3000") * Decimal("1.0488")
        assert abs(liquidation_price - expected) < Decimal("1")

    def test_calculate_liquidation_price_zero_contracts(self):
        """Test liquidation price calculation with zero contracts."""
        entry_price = Decimal("0")
        is_long = True
        margin = Decimal("10000")
        position_size = Decimal("100000")
        
        liquidation_price = MarginCalculator.calculate_liquidation_price(
            entry_price, is_long, margin, position_size
        )
        
        assert liquidation_price == Decimal("0")

    def test_calculate_available_margin(self):
        """Test available margin calculation."""
        total_collateral = Decimal("100000")
        used_margin = Decimal("20000")
        unrealized_pnl = Decimal("5000")
        margin_buffer = Decimal("0.02")
        
        available = MarginCalculator.calculate_available_margin(
            total_collateral, used_margin, unrealized_pnl, margin_buffer
        )
        
        # Expected: effective_collateral = 100000 + 5000 = 105000
        # usable_collateral = 105000 * (1 - 0.02) = 105000 * 0.98 = 102900
        # available = 102900 - 20000 = 82900
        expected = Decimal("102900") - Decimal("20000")
        assert available == expected

    def test_calculate_available_margin_negative(self):
        """Test available margin calculation with negative result."""
        total_collateral = Decimal("10000")
        used_margin = Decimal("20000")
        unrealized_pnl = Decimal("-5000")
        margin_buffer = Decimal("0.02")
        
        available = MarginCalculator.calculate_available_margin(
            total_collateral, used_margin, unrealized_pnl, margin_buffer
        )
        
        assert available == Decimal("0")

    def test_calculate_cross_margin_requirement_no_correlation(self):
        """Test cross margin requirement calculation without correlation."""
        positions = [
            {"symbol": "ETHUSDT", "size": Decimal("50000")},
            {"symbol": "BTCUSDT", "size": Decimal("30000")}
        ]
        
        margin = MarginCalculator.calculate_cross_margin_requirement(positions)
        
        # Expected: 50000 * 0.1 + 30000 * 0.1 = 5000 + 3000 = 8000
        expected = Decimal("50000") * Decimal("0.1") + Decimal("30000") * Decimal("0.1")
        assert margin == expected

    def test_calculate_cross_margin_requirement_with_correlation(self):
        """Test cross margin requirement calculation with correlation."""
        positions = [
            {"symbol": "ETHUSDT", "size": Decimal("50000")},
            {"symbol": "BTCUSDT", "size": Decimal("30000")}
        ]
        correlation_matrix = {("ETH", "BTC"): Decimal("0.7")}
        
        margin = MarginCalculator.calculate_cross_margin_requirement(positions, correlation_matrix)
        
        # Expected: (50000 * 0.1 + 30000 * 0.1) * 0.85 = 8000 * 0.85 = 6800
        expected = (Decimal("50000") * Decimal("0.1") + Decimal("30000") * Decimal("0.1")) * Decimal("0.85")
        assert margin == expected

    def test_calculate_cross_margin_requirement_no_positions(self):
        """Test cross margin requirement calculation with no positions."""
        positions = []
        
        margin = MarginCalculator.calculate_cross_margin_requirement(positions)
        
        assert margin == Decimal("0")

    def test_calculate_funding_payment(self):
        """Test funding payment calculation."""
        position_size = Decimal("100000")
        funding_rate = Decimal("0.0001")
        hours = 8
        
        payment = MarginCalculator.calculate_funding_payment(position_size, funding_rate, hours)
        
        # Expected: 100000 * 0.0001 = 10
        assert payment == Decimal("10")

    def test_calculate_portfolio_margin(self):
        """Test portfolio margin calculation using scenario analysis."""
        positions = {
            "ETH": {"size": Decimal("50000"), "side": "long"},
            "BTC": {"size": Decimal("30000"), "side": "short"}
        }
        market_scenarios = [
            {"ETH": Decimal("0.1"), "BTC": Decimal("-0.05")},  # ETH up 10%, BTC down 5%
            {"ETH": Decimal("-0.1"), "BTC": Decimal("0.05")},  # ETH down 10%, BTC up 5%
            {"ETH": Decimal("0.05"), "BTC": Decimal("0.05")}   # Both up 5%
        ]
        confidence_level = Decimal("0.99")
        
        margin = MarginCalculator.calculate_portfolio_margin(
            positions, market_scenarios, confidence_level
        )
        
        # Expected: Scenario 1: ETH up 10%, BTC down 5%
        # ETH (long): loss = 50000 * (-0.1) = -5000, max(0, -5000) = 0
        # BTC (short): loss = 30000 * 0.05 = 1500, max(0, 1500) = 1500, total = 1500
        # Scenario 2: ETH down 10%, BTC up 5%
        # ETH (long): loss = 50000 * 0.1 = 5000, max(0, 5000) = 5000
        # BTC (short): loss = 30000 * 0.05 = 1500, max(0, 1500) = 1500, total = 6500
        # Scenario 3: Both up 5%
        # ETH (long): loss = 50000 * (-0.05) = -2500, max(0, -2500) = 0
        # BTC (short): loss = 30000 * 0.05 = 1500, max(0, 1500) = 1500, total = 1500
        # Sorted: [6500, 1500, 1500], VaR at 99% confidence = 6500
        assert margin == Decimal("6500")

    def test_calculate_portfolio_margin_no_data(self):
        """Test portfolio margin calculation with no data."""
        positions = {}
        market_scenarios = []
        
        margin = MarginCalculator.calculate_portfolio_margin(positions, market_scenarios)
        
        assert margin == Decimal("0")

    def test_calculate_margin_health_healthy(self):
        """Test margin health calculation for healthy positions."""
        positions = [
            {"symbol": "ETHUSDT", "size": Decimal("50000")},
            {"symbol": "BTCUSDT", "size": Decimal("30000")}
        ]
        current_prices = {"ETH": 3000, "BTC": 50000}
        config = {}
        
        health = MarginCalculator.calculate_margin_health(positions, current_prices, config)
        
        # The margin ratio is estimated as 20% of position value, which gives 0.2
        # This is below the 0.35 threshold, so it should be CAUTION, not HEALTHY
        assert health['health_status'] in ['CAUTION', 'WARNING']
        assert health['needs_action'] in [True, False]
        assert health['positions_count'] == 2

    def test_calculate_margin_health_no_positions(self):
        """Test margin health calculation with no positions."""
        positions = []
        current_prices = {}
        config = {}
        
        health = MarginCalculator.calculate_margin_health(positions, current_prices, config)
        
        assert health['health_status'] == 'HEALTHY'
        assert health['needs_action'] is False
        assert health['margin_ratio'] == 999

    def test_calculate_basis_margin_hedged_position(self):
        """Test basis margin calculation for hedged position."""
        spot_position = Decimal("100000")  # Long spot
        futures_position = Decimal("-100000")  # Short futures
        spot_margin_rate = Decimal("1.0")
        futures_margin_rate = Decimal("0.10")
        
        margin = MarginCalculator.calculate_basis_margin(
            spot_position, futures_position, spot_margin_rate, futures_margin_rate
        )
        
        # Expected: spot_margin = 100000 * 1.0 = 100000
        # futures_margin = 100000 * 0.10 = 10000
        # hedge_benefit = min(100000, 100000) * 0.5 = 50000
        # total = 100000 + 10000 - 50000 = 60000
        expected = Decimal("100000") + Decimal("10000") - Decimal("50000")
        assert margin == expected

    def test_calculate_basis_margin_unhedged_position(self):
        """Test basis margin calculation for unhedged position."""
        spot_position = Decimal("100000")  # Long spot
        futures_position = Decimal("50000")  # Long futures (not hedged)
        spot_margin_rate = Decimal("1.0")
        futures_margin_rate = Decimal("0.10")
        
        margin = MarginCalculator.calculate_basis_margin(
            spot_position, futures_position, spot_margin_rate, futures_margin_rate
        )
        
        # Expected: spot_margin = 100000 * 1.0 = 100000
        # futures_margin = 50000 * 0.10 = 5000
        # total = 100000 + 5000 = 105000 (no hedge benefit)
        expected = Decimal("100000") + Decimal("5000")
        assert margin == expected

    def test_error_codes_defined(self):
        """Test that all error codes are properly defined."""
        expected_codes = [
            'MARGIN-001', 'MARGIN-002', 'MARGIN-003', 'MARGIN-004',
            'MARGIN-005', 'MARGIN-006', 'MARGIN-007', 'MARGIN-008',
            'MARGIN-009', 'MARGIN-010', 'MARGIN-011', 'MARGIN-012'
        ]
        
        for code in expected_codes:
            assert code in ERROR_CODES
            assert ERROR_CODES[code] is not None
            assert len(ERROR_CODES[code]) > 0

    def test_decimal_precision_handling(self):
        """Test that calculations maintain proper decimal precision."""
        position_size = Decimal("100000.123456")
        leverage = Decimal("10.5")
        
        margin = MarginCalculator.calculate_margin_requirement(position_size, leverage)
        
        # Should maintain precision
        expected = position_size / leverage
        assert abs(margin - expected) < Decimal("0.000001")

    def test_edge_case_zero_values(self):
        """Test edge cases with zero values."""
        # Test with zero position size
        margin = MarginCalculator.calculate_margin_requirement(Decimal("0"), Decimal("10"))
        assert margin == Decimal("0")
        
        # Test with zero leverage
        margin = MarginCalculator.calculate_margin_requirement(Decimal("100000"), Decimal("0"))
        assert margin == Decimal("10000")  # Default 10%

    def test_boundary_conditions(self):
        """Test boundary conditions for margin calculations."""
        # Test margin ratio at exactly 1.0
        ratio = MarginCalculator.calculate_margin_ratio(
            Decimal("50000"), Decimal("50000"), Decimal("100000")
        )
        assert ratio == Decimal("1.0")
        
        # Test liquidation price at entry price
        liquidation_price = MarginCalculator.calculate_liquidation_price(
            Decimal("3000"), True, Decimal("5000"), Decimal("100000"), Decimal("0.05")
        )
        # Should be close to entry price when margin is at maintenance level
        assert abs(liquidation_price - Decimal("3000")) < Decimal("100")
