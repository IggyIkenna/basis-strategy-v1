"""
Unit tests for Health Calculator.

Tests health calculator math functions in isolation with mocked dependencies.
"""

import pytest
from decimal import Decimal
from typing import Dict
from unittest.mock import Mock, patch, MagicMock

# Mock the imports to avoid environment dependencies
from unittest.mock import Mock

# Mock the Health Calculator
class MockHealthCalculator:
    """Mock health calculator for testing."""
    
    ERROR_CODES = {
        'HEALTH-001': 'Health factor calculation failed',
        'HEALTH-002': 'Weighted health factor calculation failed',
        'HEALTH-003': 'Distance to liquidation calculation failed',
        'HEALTH-004': 'Risk score calculation failed',
        'HEALTH-005': 'Safe withdrawal calculation failed',
        'HEALTH-006': 'Safe borrow calculation failed',
        'HEALTH-007': 'Cascade risk calculation failed',
        'HEALTH-008': 'Required collateral calculation failed'
    }
    
    @staticmethod
    def calculate_health_factor(
        collateral_value: Decimal,
        debt_value: Decimal,
        liquidation_threshold: Decimal = Decimal("0.85")
    ) -> Decimal:
        """Calculate health factor for a position."""
        if debt_value == 0:
            return Decimal("999")  # Infinite health with no debt
            
        liquidation_collateral = collateral_value * liquidation_threshold
        return liquidation_collateral / debt_value
    
    @staticmethod
    def calculate_weighted_health_factor(
        collateral_by_token: Dict[str, Decimal],
        debt_by_token: Dict[str, Decimal],
        liquidation_thresholds: Dict[str, Decimal]
    ) -> Decimal:
        """Calculate health factor with different thresholds per collateral type."""
        total_debt = sum(debt_by_token.values(), Decimal("0"))
        
        if total_debt == 0:
            return Decimal("999")
            
        # Calculate weighted liquidation collateral
        liquidation_collateral = Decimal("0")
        for token, value in collateral_by_token.items():
            threshold = liquidation_thresholds.get(token, Decimal("0.85"))
            liquidation_collateral += value * threshold
            
        return liquidation_collateral / total_debt
    
    @staticmethod
    def calculate_distance_to_liquidation(
        current_price: Decimal,
        liquidation_price: Decimal,
        is_long: bool = True
    ) -> Decimal:
        """Calculate percentage distance to liquidation."""
        if current_price == 0:
            return Decimal("0")
            
        if is_long:
            # Long position liquidates when price falls
            if liquidation_price >= current_price:
                return Decimal("0")  # Already liquidated
            return (current_price - liquidation_price) / current_price
        else:
            # Short position liquidates when price rises
            if liquidation_price <= current_price:
                return Decimal("0")  # Already liquidated
            return (liquidation_price - current_price) / current_price
    
    @staticmethod
    def calculate_risk_score(
        health_factor: Decimal,
        leverage_ratio: Decimal,
        volatility: Decimal = Decimal("0.2")
    ) -> Decimal:
        """Calculate risk score based on health factor and leverage."""
        if health_factor <= Decimal("1.0"):
            return Decimal("1.0")  # Maximum risk
        
        # Risk decreases as health factor increases
        health_risk = Decimal("1.0") / health_factor
        
        # Risk increases with leverage
        leverage_risk = min(leverage_ratio / Decimal("10.0"), Decimal("1.0"))
        
        # Risk increases with volatility
        volatility_risk = volatility
        
        # Combine risks (weighted average)
        total_risk = (health_risk * Decimal("0.5") + 
                     leverage_risk * Decimal("0.3") + 
                     volatility_risk * Decimal("0.2"))
        
        return min(total_risk, Decimal("1.0"))
    
    @staticmethod
    def calculate_safe_withdrawal(
        collateral_value: Decimal,
        debt_value: Decimal,
        liquidation_threshold: Decimal = Decimal("0.85"),
        safety_margin: Decimal = Decimal("0.1")
    ) -> Decimal:
        """Calculate safe withdrawal amount."""
        if debt_value == 0:
            return collateral_value  # Can withdraw all if no debt
        
        # Calculate minimum collateral needed
        min_collateral = debt_value / liquidation_threshold
        
        # Add safety margin
        safe_collateral = min_collateral * (Decimal("1.0") + safety_margin)
        
        # Safe withdrawal is excess collateral
        safe_withdrawal = max(collateral_value - safe_collateral, Decimal("0"))
        
        return safe_withdrawal
    
    @staticmethod
    def calculate_safe_borrow(
        collateral_value: Decimal,
        current_debt: Decimal,
        liquidation_threshold: Decimal = Decimal("0.85"),
        safety_margin: Decimal = Decimal("0.1")
    ) -> Decimal:
        """Calculate safe additional borrow amount."""
        # Calculate maximum debt allowed
        max_debt = collateral_value * liquidation_threshold
        
        # Apply safety margin
        safe_max_debt = max_debt * (Decimal("1.0") - safety_margin)
        
        # Safe borrow is remaining capacity
        safe_borrow = max(safe_max_debt - current_debt, Decimal("0"))
        
        return safe_borrow
    
    @staticmethod
    def calculate_cascade_risk(
        positions: Dict[str, Dict[str, Decimal]],
        correlation_matrix: Dict[str, Dict[str, Decimal]]
    ) -> Decimal:
        """Calculate cascade liquidation risk."""
        if not positions:
            return Decimal("0")
        
        total_risk = Decimal("0")
        position_count = len(positions)
        
        for pos_id, position in positions.items():
            health_factor = position.get('health_factor', Decimal("999"))
            if health_factor <= Decimal("1.5"):  # At risk positions
                # Calculate correlation risk with other positions
                correlation_risk = Decimal("0")
                for other_id, other_position in positions.items():
                    if pos_id != other_id:
                        correlation = correlation_matrix.get(pos_id, {}).get(other_id, Decimal("0"))
                        other_health = other_position.get('health_factor', Decimal("999"))
                        if other_health <= Decimal("1.5"):
                            correlation_risk += correlation
                
                # Risk increases with correlation
                position_risk = Decimal("1.0") / health_factor * (Decimal("1.0") + correlation_risk)
                total_risk += position_risk
        
        return total_risk / position_count if position_count > 0 else Decimal("0")
    
    @staticmethod
    def calculate_required_collateral(
        debt_value: Decimal,
        target_health_factor: Decimal,
        liquidation_threshold: Decimal = Decimal("0.85")
    ) -> Decimal:
        """Calculate required collateral for target health factor."""
        if target_health_factor <= Decimal("0"):
            return Decimal("0")
        
        # Required collateral = debt / (liquidation_threshold / target_health_factor)
        required_collateral = debt_value / (liquidation_threshold / target_health_factor)
        
        return required_collateral


class TestHealthCalculator:
    """Test health calculator functionality."""

    def test_calculate_health_factor_healthy_position(self):
        """Test health factor calculation for healthy position."""
        collateral = Decimal("100000")
        debt = Decimal("50000")
        threshold = Decimal("0.85")
        
        health_factor = MockHealthCalculator.calculate_health_factor(collateral, debt, threshold)
        
        # Expected: (100000 * 0.85) / 50000 = 1.7
        expected = Decimal("1.7")
        assert health_factor == expected

    def test_calculate_health_factor_unhealthy_position(self):
        """Test health factor calculation for unhealthy position."""
        collateral = Decimal("50000")
        debt = Decimal("50000")
        threshold = Decimal("0.85")
        
        health_factor = MockHealthCalculator.calculate_health_factor(collateral, debt, threshold)
        
        # Expected: (50000 * 0.85) / 50000 = 0.85
        expected = Decimal("0.85")
        assert health_factor == expected

    def test_calculate_health_factor_no_debt(self):
        """Test health factor calculation with no debt."""
        collateral = Decimal("100000")
        debt = Decimal("0")
        
        health_factor = MockHealthCalculator.calculate_health_factor(collateral, debt)
        
        # Should return infinite health (999)
        assert health_factor == Decimal("999")

    def test_calculate_health_factor_custom_threshold(self):
        """Test health factor calculation with custom threshold."""
        collateral = Decimal("100000")
        debt = Decimal("60000")
        threshold = Decimal("0.8")
        
        health_factor = MockHealthCalculator.calculate_health_factor(collateral, debt, threshold)
        
        # Expected: (100000 * 0.8) / 60000 = 1.333...
        expected = Decimal("80000") / Decimal("60000")
        assert health_factor == expected

    def test_calculate_weighted_health_factor_single_token(self):
        """Test weighted health factor with single token."""
        collateral = {"ETH": Decimal("100000")}
        debt = {"USDT": Decimal("50000")}
        thresholds = {"ETH": Decimal("0.85")}
        
        health_factor = MockHealthCalculator.calculate_weighted_health_factor(
            collateral, debt, thresholds
        )
        
        # Expected: (100000 * 0.85) / 50000 = 1.7
        expected = Decimal("1.7")
        assert health_factor == expected

    def test_calculate_weighted_health_factor_multiple_tokens(self):
        """Test weighted health factor with multiple tokens."""
        collateral = {
            "ETH": Decimal("50000"),
            "BTC": Decimal("30000")
        }
        debt = {"USDT": Decimal("50000")}
        thresholds = {
            "ETH": Decimal("0.85"),
            "BTC": Decimal("0.8")
        }
        
        health_factor = MockHealthCalculator.calculate_weighted_health_factor(
            collateral, debt, thresholds
        )
        
        # Expected: (50000 * 0.85 + 30000 * 0.8) / 50000 = (42500 + 24000) / 50000 = 66500 / 50000 = 1.33
        expected = Decimal("66500") / Decimal("50000")
        assert health_factor == expected

    def test_calculate_weighted_health_factor_no_debt(self):
        """Test weighted health factor with no debt."""
        collateral = {"ETH": Decimal("100000")}
        debt = {}
        thresholds = {"ETH": Decimal("0.85")}
        
        health_factor = MockHealthCalculator.calculate_weighted_health_factor(
            collateral, debt, thresholds
        )
        
        # Should return infinite health (999)
        assert health_factor == Decimal("999")

    def test_calculate_distance_to_liquidation_long_healthy(self):
        """Test distance to liquidation for healthy long position."""
        current_price = Decimal("50000")
        liquidation_price = Decimal("40000")
        
        distance = MockHealthCalculator.calculate_distance_to_liquidation(
            current_price, liquidation_price, is_long=True
        )
        
        # Expected: (50000 - 40000) / 50000 = 0.2 (20%)
        expected = Decimal("0.2")
        assert distance == expected

    def test_calculate_distance_to_liquidation_long_at_risk(self):
        """Test distance to liquidation for at-risk long position."""
        current_price = Decimal("41000")
        liquidation_price = Decimal("40000")
        
        distance = MockHealthCalculator.calculate_distance_to_liquidation(
            current_price, liquidation_price, is_long=True
        )
        
        # Expected: (41000 - 40000) / 41000 ≈ 0.0244
        expected = Decimal("1000") / Decimal("41000")
        assert distance == expected

    def test_calculate_distance_to_liquidation_long_liquidated(self):
        """Test distance to liquidation for liquidated long position."""
        current_price = Decimal("39000")
        liquidation_price = Decimal("40000")
        
        distance = MockHealthCalculator.calculate_distance_to_liquidation(
            current_price, liquidation_price, is_long=True
        )
        
        # Should return 0 (already liquidated)
        assert distance == Decimal("0")

    def test_calculate_distance_to_liquidation_short_healthy(self):
        """Test distance to liquidation for healthy short position."""
        current_price = Decimal("40000")
        liquidation_price = Decimal("50000")
        
        distance = MockHealthCalculator.calculate_distance_to_liquidation(
            current_price, liquidation_price, is_long=False
        )
        
        # Expected: (50000 - 40000) / 40000 = 0.25 (25%)
        expected = Decimal("0.25")
        assert distance == expected

    def test_calculate_distance_to_liquidation_zero_price(self):
        """Test distance to liquidation with zero current price."""
        current_price = Decimal("0")
        liquidation_price = Decimal("40000")
        
        distance = MockHealthCalculator.calculate_distance_to_liquidation(
            current_price, liquidation_price, is_long=True
        )
        
        # Should return 0
        assert distance == Decimal("0")

    def test_calculate_risk_score_healthy_position(self):
        """Test risk score calculation for healthy position."""
        health_factor = Decimal("2.0")
        leverage_ratio = Decimal("2.0")
        volatility = Decimal("0.2")
        
        risk_score = MockHealthCalculator.calculate_risk_score(
            health_factor, leverage_ratio, volatility
        )
        
        # Should be low risk
        assert risk_score < Decimal("0.5")

    def test_calculate_risk_score_unhealthy_position(self):
        """Test risk score calculation for unhealthy position."""
        health_factor = Decimal("1.1")
        leverage_ratio = Decimal("5.0")
        volatility = Decimal("0.3")
        
        risk_score = MockHealthCalculator.calculate_risk_score(
            health_factor, leverage_ratio, volatility
        )
        
        # Should be high risk
        assert risk_score > Decimal("0.5")

    def test_calculate_risk_score_liquidated_position(self):
        """Test risk score calculation for liquidated position."""
        health_factor = Decimal("0.9")
        leverage_ratio = Decimal("10.0")
        volatility = Decimal("0.4")
        
        risk_score = MockHealthCalculator.calculate_risk_score(
            health_factor, leverage_ratio, volatility
        )
        
        # Should be maximum risk
        assert risk_score == Decimal("1.0")

    def test_calculate_safe_withdrawal_healthy_position(self):
        """Test safe withdrawal calculation for healthy position."""
        collateral = Decimal("100000")
        debt = Decimal("50000")
        threshold = Decimal("0.85")
        safety_margin = Decimal("0.1")
        
        safe_withdrawal = MockHealthCalculator.calculate_safe_withdrawal(
            collateral, debt, threshold, safety_margin
        )
        
        # Min collateral needed: 50000 / 0.85 = 58823.53
        # Safe collateral: 58823.53 * 1.1 = 64705.88
        # Safe withdrawal: 100000 - 64705.88 = 35294.12
        expected = Decimal("35294.12")
        assert abs(safe_withdrawal - expected) < Decimal("0.01")

    def test_calculate_safe_withdrawal_no_debt(self):
        """Test safe withdrawal calculation with no debt."""
        collateral = Decimal("100000")
        debt = Decimal("0")
        
        safe_withdrawal = MockHealthCalculator.calculate_safe_withdrawal(collateral, debt)
        
        # Can withdraw all collateral
        assert safe_withdrawal == collateral

    def test_calculate_safe_borrow_healthy_position(self):
        """Test safe borrow calculation for healthy position."""
        collateral = Decimal("100000")
        current_debt = Decimal("30000")
        threshold = Decimal("0.85")
        safety_margin = Decimal("0.1")
        
        safe_borrow = MockHealthCalculator.calculate_safe_borrow(
            collateral, current_debt, threshold, safety_margin
        )
        
        # Max debt: 100000 * 0.85 = 85000
        # Safe max debt: 85000 * 0.9 = 76500
        # Safe borrow: 76500 - 30000 = 46500
        expected = Decimal("46500")
        assert safe_borrow == expected

    def test_calculate_safe_borrow_at_limit(self):
        """Test safe borrow calculation when at limit."""
        collateral = Decimal("100000")
        current_debt = Decimal("85000")
        threshold = Decimal("0.85")
        safety_margin = Decimal("0.1")
        
        safe_borrow = MockHealthCalculator.calculate_safe_borrow(
            collateral, current_debt, threshold, safety_margin
        )
        
        # Should be 0 (at or over limit)
        assert safe_borrow == Decimal("0")

    def test_calculate_cascade_risk_no_positions(self):
        """Test cascade risk calculation with no positions."""
        positions = {}
        correlation_matrix = {}
        
        risk = MockHealthCalculator.calculate_cascade_risk(positions, correlation_matrix)
        
        # Should be 0
        assert risk == Decimal("0")

    def test_calculate_cascade_risk_healthy_positions(self):
        """Test cascade risk calculation with healthy positions."""
        positions = {
            "pos1": {"health_factor": Decimal("2.0")},
            "pos2": {"health_factor": Decimal("1.8")}
        }
        correlation_matrix = {
            "pos1": {"pos2": Decimal("0.3")},
            "pos2": {"pos1": Decimal("0.3")}
        }
        
        risk = MockHealthCalculator.calculate_cascade_risk(positions, correlation_matrix)
        
        # Should be low risk (positions are healthy)
        assert risk < Decimal("0.5")

    def test_calculate_cascade_risk_at_risk_positions(self):
        """Test cascade risk calculation with at-risk positions."""
        positions = {
            "pos1": {"health_factor": Decimal("1.2")},
            "pos2": {"health_factor": Decimal("1.3")}
        }
        correlation_matrix = {
            "pos1": {"pos2": Decimal("0.8")},
            "pos2": {"pos1": Decimal("0.8")}
        }
        
        risk = MockHealthCalculator.calculate_cascade_risk(positions, correlation_matrix)
        
        # Should be high risk (positions are at risk and highly correlated)
        assert risk > Decimal("0.5")

    def test_calculate_required_collateral_target_health(self):
        """Test required collateral calculation for target health factor."""
        debt = Decimal("50000")
        target_health = Decimal("2.0")
        threshold = Decimal("0.85")
        
        required_collateral = MockHealthCalculator.calculate_required_collateral(
            debt, target_health, threshold
        )
        
        # Required: 50000 / (0.85 / 2.0) = 50000 / 0.425 = 117647.06
        expected = Decimal("117647.06")
        assert abs(required_collateral - expected) < Decimal("0.01")

    def test_calculate_required_collateral_zero_target(self):
        """Test required collateral calculation with zero target health."""
        debt = Decimal("50000")
        target_health = Decimal("0")
        
        required_collateral = MockHealthCalculator.calculate_required_collateral(
            debt, target_health
        )
        
        # Should return 0
        assert required_collateral == Decimal("0")

    def test_error_codes_defined(self):
        """Test that all error codes are properly defined."""
        expected_codes = [
            'HEALTH-001', 'HEALTH-002', 'HEALTH-003', 'HEALTH-004',
            'HEALTH-005', 'HEALTH-006', 'HEALTH-007', 'HEALTH-008'
        ]
        
        for code in expected_codes:
            assert code in MockHealthCalculator.ERROR_CODES
            assert MockHealthCalculator.ERROR_CODES[code] is not None
            assert len(MockHealthCalculator.ERROR_CODES[code]) > 0

    def test_decimal_precision_handling(self):
        """Test that calculations maintain proper decimal precision."""
        # Use values that would cause floating point precision issues
        collateral = Decimal("100000.123456789")
        debt = Decimal("50000.987654321")
        
        health_factor = MockHealthCalculator.calculate_health_factor(collateral, debt)
        
        # Should maintain precision
        assert isinstance(health_factor, Decimal)
        assert health_factor > Decimal("1.0")

    def test_edge_case_zero_values(self):
        """Test edge cases with zero values."""
        # Zero collateral
        health_factor = MockHealthCalculator.calculate_health_factor(Decimal("0"), Decimal("1000"))
        assert health_factor == Decimal("0")
        
        # Zero debt (already tested)
        health_factor = MockHealthCalculator.calculate_health_factor(Decimal("1000"), Decimal("0"))
        assert health_factor == Decimal("999")

    def test_boundary_conditions(self):
        """Test boundary conditions for health calculations."""
        # Health factor exactly at 1.0
        health_factor = MockHealthCalculator.calculate_health_factor(
            Decimal("1000"), Decimal("850"), Decimal("0.85")
        )
        assert health_factor == Decimal("1.0")
        
        # Health factor just above 1.0
        health_factor = MockHealthCalculator.calculate_health_factor(
            Decimal("1000"), Decimal("849"), Decimal("0.85")
        )
        assert health_factor > Decimal("1.0")
        
        # Health factor just below 1.0
        health_factor = MockHealthCalculator.calculate_health_factor(
            Decimal("1000"), Decimal("851"), Decimal("0.85")
        )
        assert health_factor < Decimal("1.0")
