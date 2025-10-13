"""Health Calculator - Pure calculation functions for position health metrics."""

from decimal import Decimal
from typing import Dict, List, Optional
import logging

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType

logger = logging.getLogger(__name__)

# Error codes for Health Calculator
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


class HealthCalculator(StandardizedLoggingMixin):
    """Pure health calculation functions - no side effects or I/O."""
    
    @staticmethod
    def calculate_health_factor(
        collateral_value: Decimal,
        debt_value: Decimal,
        liquidation_threshold: Decimal = Decimal("0.85")
    ) -> Decimal:
        """
        Calculate health factor for a position.
        
        Args:
            collateral_value: Total collateral value in USD
            debt_value: Total debt value in USD
            liquidation_threshold: Liquidation threshold percentage
            
        Returns:
            Health factor (> 1 is healthy, < 1 is liquidatable)
        """
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
        """
        Calculate health factor with different thresholds per collateral type.
        
        Args:
            collateral_by_token: Collateral values by token
            debt_by_token: Debt values by token
            liquidation_thresholds: Liquidation threshold per token
            
        Returns:
            Weighted health factor
        """
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
        """
        Calculate percentage distance to liquidation.
        
        Args:
            current_price: Current asset price
            liquidation_price: Liquidation trigger price
            is_long: True for long position, False for short
            
        Returns:
            Distance to liquidation as percentage (0.1 = 10% away)
        """
        if current_price == 0:
            return Decimal("0")
            
        if is_long:
            # Long position liquidates when price falls
            if liquidation_price >= current_price:
                return Decimal("0")  # Already at risk
            distance = (current_price - liquidation_price) / current_price
        else:
            # Short position liquidates when price rises
            if liquidation_price <= current_price:
                return Decimal("0")  # Already at risk
            distance = (liquidation_price - current_price) / current_price
            
        return max(distance, Decimal("0"))
    
    @staticmethod
    def calculate_risk_score(
        health_factor: Decimal,
        ltv_ratio: Decimal,
        margin_ratio: Decimal,
        volatility: Decimal = Decimal("0.5")
    ) -> Decimal:
        """
        Calculate composite risk score.
        
        Args:
            health_factor: Current health factor
            ltv_ratio: Current LTV ratio
            margin_ratio: Current margin ratio
            volatility: Asset volatility (0.5 = 50% annualized)
            
        Returns:
            Risk score (0 = no risk, 1 = maximum risk)
        """
        # Component scores
        health_score = Decimal("0")
        if health_factor < Decimal("999"):
            if health_factor > 2:
                health_score = Decimal("0")
            elif health_factor > 1.5:
                health_score = Decimal("0.25")
            elif health_factor > 1.2:
                health_score = Decimal("0.5")
            elif health_factor > 1:
                health_score = Decimal("0.75")
            else:
                health_score = Decimal("1")
                
        # LTV score
        ltv_score = min(ltv_ratio, Decimal("1"))
        
        # Margin score
        margin_score = Decimal("0")
        if margin_ratio < Decimal("999"):
            if margin_ratio < 0.1:
                margin_score = Decimal("1")
            elif margin_ratio < 0.2:
                margin_score = Decimal("0.75")
            elif margin_ratio < 0.3:
                margin_score = Decimal("0.5")
            elif margin_ratio < 0.5:
                margin_score = Decimal("0.25")
                
        # Volatility adjustment
        vol_multiplier = Decimal("1") + (volatility * Decimal("0.5"))
        
        # Weighted average
        base_score = (health_score * Decimal("0.4") + 
                     ltv_score * Decimal("0.3") + 
                     margin_score * Decimal("0.3"))
        
        # Apply volatility multiplier
        final_score = min(base_score * vol_multiplier, Decimal("1"))
        
        return final_score
    
    @staticmethod
    def calculate_safe_withdrawal_amount(
        collateral_value: Decimal,
        debt_value: Decimal,
        target_health: Decimal = Decimal("1.5"),
        liquidation_threshold: Decimal = Decimal("0.85")
    ) -> Decimal:
        """
        Calculate how much collateral can be safely withdrawn.
        
        Args:
            collateral_value: Current collateral value
            debt_value: Current debt value
            target_health: Target health factor to maintain
            liquidation_threshold: Liquidation threshold
            
        Returns:
            Maximum safe withdrawal amount
        """
        if debt_value == 0:
            return collateral_value  # Can withdraw everything with no debt
            
        # Required collateral for target health
        required_collateral = (debt_value * target_health) / liquidation_threshold
        
        # Available to withdraw
        available = collateral_value - required_collateral
        
        return max(available, Decimal("0"))
    
    @staticmethod
    def calculate_safe_borrow_amount(
        collateral_value: Decimal,
        current_debt: Decimal,
        target_health: Decimal = Decimal("1.5"),
        liquidation_threshold: Decimal = Decimal("0.85")
    ) -> Decimal:
        """
        Calculate how much more can be safely borrowed.
        
        Args:
            collateral_value: Current collateral value
            current_debt: Current debt value
            target_health: Target health factor to maintain
            liquidation_threshold: Liquidation threshold
            
        Returns:
            Maximum safe additional borrow amount
        """
        # Maximum debt at target health
        max_debt = (collateral_value * liquidation_threshold) / target_health
        
        # Available to borrow
        available = max_debt - current_debt
        
        return max(available, Decimal("0"))
    
    @staticmethod
    def check_cascade_risk(
        positions: List[Dict[str, Decimal]],
        cross_margin: bool = False
    ) -> Dict[str, Decimal]:
        """
        Check for liquidation cascade risk across positions.
        
        Args:
            positions: List of positions with health metrics
            cross_margin: Whether positions share margin
            
        Returns:
            Cascade risk metrics
        """
        if not positions:
            return {
                "cascade_probability": Decimal("0"),
                "potential_loss": Decimal("0"),
                "positions_at_risk": Decimal("0")
            }
            
        at_risk_count = 0
        total_value = Decimal("0")
        potential_loss = Decimal("0")
        
        for position in positions:
            health = position.get("health_factor", Decimal("999"))
            value = position.get("value", Decimal("0"))
            
            total_value += value
            
            if health < Decimal("1.2"):
                at_risk_count += 1
                potential_loss += value * Decimal("0.1")  # Assume 10% liquidation penalty
                
        cascade_probability = Decimal("0")
        
        if cross_margin and at_risk_count > 0:
            # Higher cascade risk with cross margin
            if at_risk_count == 1:
                cascade_probability = Decimal("0.2")
            elif at_risk_count == 2:
                cascade_probability = Decimal("0.5")
            else:
                cascade_probability = Decimal("0.8")
        elif at_risk_count > 2:
            # Multiple positions at risk even without cross margin
            cascade_probability = Decimal("0.3")
            
        return {
            "cascade_probability": cascade_probability,
            "potential_loss": potential_loss,
            "positions_at_risk": Decimal(str(at_risk_count)),
            "total_value": total_value
        }
    
    @staticmethod
    def calculate_required_collateral_for_health(
        debt_value: Decimal,
        target_health: Decimal,
        liquidation_threshold: Decimal = Decimal("0.85")
    ) -> Decimal:
        """
        Calculate required collateral for target health factor.
        
        Args:
            debt_value: Total debt value
            target_health: Target health factor
            liquidation_threshold: Liquidation threshold
            
        Returns:
            Required collateral value
        """
        if target_health == 0:
            return Decimal("0")
            
        return (debt_value * target_health) / liquidation_threshold



