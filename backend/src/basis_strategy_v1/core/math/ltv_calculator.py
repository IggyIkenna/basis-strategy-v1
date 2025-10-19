"""LTV Calculator for lending protocol calculations.

Rebuilt from strategy_engine.py (lines 1042-1174) following clean architecture patterns.
Provides pure mathematical functions that receive configuration as parameters,
adhering to Service-Engine separation principle.

Services load config via settings.py and pass to these pure calculation engines.
"""

from decimal import Decimal
from typing import Dict, Optional, Tuple, Any
import logging


logger = logging.getLogger(__name__)

# Error codes for LTV Calculator
ERROR_CODES = {
    "LTV-001": "LTV calculation failed",
    "LTV-002": "Projected LTV calculation failed",
    "LTV-003": "Max LTV calculation failed",
    "LTV-004": "Leverage capacity calculation failed",
    "LTV-005": "Health factor calculation failed",
    "LTV-006": "LTV safety validation failed",
    "LTV-007": "E-mode eligibility check failed",
    "LTV-008": "Leverage headroom calculation failed",
}


class LTVCalculator:
    """Pure function calculator for loan-to-value ratios.

    All functions are static and stateless, receiving configuration as parameters.
    This follows the Service-Engine separation principle where:
    - Services handle I/O and load configuration via settings.py
    - Engines perform pure calculations with no hardcoded values

    Handles sophisticated LTV calculations with support for:
    - Standard mode vs E-mode calculations
    - Multi-collateral weighted averages
    - Risk-adjusted safety buffers
    - Projected LTV after borrowing
    - Leverage capacity analysis
    """

    @staticmethod
    def calculate_current_ltv(collateral_value: Decimal, debt_value: Decimal) -> Decimal:
        """Calculate current LTV ratio."""
        if collateral_value <= 0:
            return Decimal("0") if debt_value <= 0 else Decimal("1")
        return debt_value / collateral_value

    @staticmethod
    def calculate_projected_ltv_after_borrowing(
        current_collateral_value: Decimal,
        current_debt_value: Decimal,
        additional_borrowing_usd: Decimal,
        collateral_efficiency: Decimal = Decimal("0.95"),  # 95% becomes collateral after fees
    ) -> Decimal:
        """Calculate projected LTV after additional borrowing.

        Args:
            current_collateral_value: Current collateral value in USD
            current_debt_value: Current debt value in USD
            additional_borrowing_usd: Additional borrowing amount in USD
            collateral_efficiency: Fraction of borrowed amount that becomes collateral

        Returns:
            Projected LTV ratio after borrowing
        """
        # Project after borrowing
        projected_debt_value = current_debt_value + additional_borrowing_usd

        # Assume some of borrowed amount becomes collateral (e.g., staked)
        collateral_increase = additional_borrowing_usd * collateral_efficiency
        projected_collateral_value = current_collateral_value + collateral_increase

        if projected_collateral_value <= 0:
            return Decimal("0") if projected_debt_value <= 0 else Decimal("1")

        return projected_debt_value / projected_collateral_value

    @staticmethod
    def get_max_ltv_for_collateral_mix(
        collateral_composition: Dict[str, Decimal],  # token -> value_usd
        is_borrowing_eth: bool,
        ltv_config: Dict[str, Any],
        risk_mode: str = "standard",
    ) -> Decimal:
        """Calculate weighted average max LTV for collateral mix.

        Sophisticated logic from original strategy_engine.py that handles:
        - E-mode eligibility for ETH borrowing against ETH-denominated collateral
        - Weighted averages across multiple collateral types
        - Risk-adjusted limits based on market conditions

        Args:
            collateral_composition: Dict mapping token symbols to USD values
            is_borrowing_eth: Whether borrowing ETH (enables e-mode)
            ltv_config: LTV configuration from settings
            risk_mode: Risk adjustment mode ("standard" or "conservative")

        Returns:
            Weighted average maximum LTV
        """
        total_collateral_value = sum(collateral_composition.values())

        if total_collateral_value <= 0:
            # No collateral, return conservative default
            return Decimal(str(ltv_config["standard_limits"]["ETH"]))  # Fail-fast if missing

        # Get config values - fail-fast if missing
        standard_limits = ltv_config["standard_limits"]  # Fail-fast if missing
        emode_limits = ltv_config["emode_limits"]  # Fail-fast if missing
        market_risk_buffer = Decimal(str(ltv_config["market_risk_buffer"]))  # Fail-fast if missing
        basis_risk_buffer = Decimal(str(ltv_config["basis_risk_buffer"]))  # Fail-fast if missing

        # Calculate weighted average LTV
        weighted_ltv = Decimal("0")

        for token, value in collateral_composition.items():
            # Normalize token names for LTV lookups (WETH uses ETH limits)
            lookup_token = "ETH" if token == "WETH" else token

            # Check if eligible for e-mode (ETH borrowing against ETH-denominated collateral)
            if is_borrowing_eth and lookup_token in ["wstETH", "weETH"]:
                # Use e-mode LTV limits (higher leverage, lower risk due to basis correlation)
                emode_key = f"{lookup_token}_ETH"
                token_ltv = Decimal(str(emode_limits.get(emode_key, 0.93)))

                # Apply basis risk protection (smaller buffer for correlated assets)
                if risk_mode == "conservative":
                    token_ltv = token_ltv / (Decimal("1") + basis_risk_buffer)

                logger.debug(f"E-mode: {token} safe LTV: {token_ltv:.3f} (basis risk protection)")
            else:
                # Use standard mode LTV limits
                token_ltv = Decimal(str(standard_limits.get(lookup_token, 0.66)))

                # Apply market risk protection (larger buffer for cross-asset borrowing)
                if risk_mode == "conservative":
                    token_ltv = token_ltv / (Decimal("1") + market_risk_buffer)

                logger.debug(
                    f"Standard mode: {token} safe LTV: {token_ltv:.3f} (market risk protection)"
                )

            # Calculate weighted contribution
            weight = value / total_collateral_value
            weighted_ltv += token_ltv * weight

        mode_type = (
            "E-mode"
            if is_borrowing_eth
            and any(token in ["wstETH", "weETH"] for token in collateral_composition.keys())
            else "Standard mode"
        )
        logger.info(f"Weighted average safe LTV: {weighted_ltv:.3f} ({mode_type})")

        return weighted_ltv

    @staticmethod
    def can_add_leverage(
        current_ltv: Decimal,
        safe_ltv: Decimal,
        min_headroom: Decimal = Decimal("0.05"),  # 5% minimum headroom
    ) -> Tuple[bool, Decimal]:
        """Check if more leverage can be safely added.

        Args:
            current_ltv: Current LTV ratio
            safe_ltv: Safe LTV from config (already buffered vs max_ltv)
            min_headroom: Minimum LTV headroom required

        Returns:
            Tuple of (can_add_leverage, available_headroom)
        """
        # Use safe_ltv directly (already buffered in config)
        safe_max_ltv = safe_ltv

        # Calculate available headroom
        ltv_headroom = safe_max_ltv - current_ltv

        # Only allow leverage if we have meaningful headroom
        can_add = ltv_headroom > min_headroom

        logger.debug(
            f"Leverage check: current_ltv={current_ltv:.3f}, "
            f"safe_max={safe_max_ltv:.3f}, headroom={ltv_headroom:.3f}, can_add={can_add}"
        )

        return can_add, ltv_headroom

    @staticmethod
    def calculate_next_loop_capacity(
        current_collateral_value: Decimal,
        current_debt_value: Decimal,
        max_safe_ltv: Decimal,
        strategy_config: Dict[str, Any],
    ) -> Decimal:
        """Calculate borrowing capacity for leveraged staking.

        Sophisticated capacity calculation from original strategy_engine.py
        that accounts for LTV headroom and loop efficiency factors.

        Args:
            current_collateral_value: Current collateral value in USD
            current_debt_value: Current debt value in USD
            max_safe_ltv: Maximum safe LTV for current collateral mix
            strategy_config: Strategy configuration with loop factors and buffers

        Returns:
            Available borrowing capacity for next loop
        """
        if current_collateral_value <= 0:
            return Decimal("0")

        # Get config values
        leverage_factor = Decimal(str(strategy_config["leverage_factor"]))  # Fail-fast if missing

        # Use safe_ltv from config (already buffered vs max_ltv)
        safe_ltv_config = strategy_config["ltv"]["safe_ltv"]  # Fail-fast if missing
        safe_max_ltv = Decimal(str(safe_ltv_config["standard_borrowing"]))  # Fail-fast if missing

        # Calculate current LTV
        current_ltv = current_debt_value / current_collateral_value

        # Calculate LTV headroom
        ltv_headroom = safe_max_ltv - current_ltv

        if ltv_headroom <= 0:
            return Decimal("0")

        # Calculate borrowing capacity using leverage factor
        # Original logic: current_collateral_value * ltv_headroom * leverage_factor
        leverage_capacity = current_collateral_value * ltv_headroom * leverage_factor

        return max(Decimal("0"), leverage_capacity)

    @staticmethod
    def calculate_health_factor(
        collateral_value: Decimal, debt_value: Decimal, liquidation_threshold: Decimal
    ) -> Decimal:
        """Calculate Aave health factor."""
        if debt_value <= 0:
            return Decimal("999")  # Infinite health factor
        return (collateral_value * liquidation_threshold) / debt_value

    @staticmethod
    def get_max_borrowing_capacity(collateral_value: Decimal, max_ltv: Decimal) -> Decimal:
        """Calculate maximum borrowing capacity."""
        return collateral_value * max_ltv

    @staticmethod
    def validate_ltv_safety(
        projected_ltv: Decimal, max_safe_ltv: Decimal, operation_name: str = "operation"
    ) -> Tuple[bool, Optional[str]]:
        """Validate LTV safety for an operation.

        Args:
            projected_ltv: Projected LTV after operation
            max_safe_ltv: Maximum safe LTV limit
            operation_name: Name of operation for error reporting

        Returns:
            Tuple of (is_safe, error_message)
        """
        if projected_ltv > max_safe_ltv:
            error_msg = (
                f"{operation_name} would result in unsafe LTV: "
                f"{projected_ltv:.3f} > {max_safe_ltv:.3f}"
            )
            return False, error_msg

        return True, None

    @staticmethod
    def get_emode_eligibility(collateral_token: str, debt_token: str) -> bool:
        """Check if collateral/debt pair is eligible for e-mode.

        Args:
            collateral_token: Collateral token symbol
            debt_token: Debt token symbol

        Returns:
            True if eligible for e-mode (higher LTV)
        """
        eth_collateral_tokens = {"wstETH", "weETH", "stETH", "eETH", "ETH", "WETH"}
        eth_debt_tokens = {"ETH", "WETH"}

        return collateral_token in eth_collateral_tokens and debt_token in eth_debt_tokens

    @staticmethod
    def calculate_dynamic_ltv_target(
        max_ltv: Decimal,
        max_stake_spread_move: Decimal,
    ) -> Decimal:
        """Calculate dynamic LTV target with safety buffers.

        Args:
            max_ltv: Maximum LTV from AAVE risk parameters
            max_stake_spread_move: Maximum expected stake spread move

        Returns:
            Dynamic LTV target with safety buffers applied
        """
        # Calculate dynamic LTV target
        dynamic_ltv = max_ltv(1 - max_stake_spread_move)

        # Ensure it's not negative (minimum 0% LTV)
        dynamic_ltv = max(dynamic_ltv, Decimal("0"))

        return dynamic_ltv

    @staticmethod
    def calculate_leverage_headroom(current_ltv: Decimal, safe_ltv: Decimal) -> Decimal:
        """Calculate available leverage headroom.

        Args:
            current_ltv: Current LTV ratio
            safe_ltv: Safe LTV from config (already buffered)

        Returns:
            Available LTV headroom for additional leverage
        """
        headroom = safe_ltv / current_ltv
        return max(Decimal("0"), headroom)
