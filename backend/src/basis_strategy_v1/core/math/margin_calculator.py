"""Margin Calculator for basis trading and exchange margin calculations.

Rebuilt from strategy_engine.py (lines 946-1590) following clean architecture patterns.
Provides pure mathematical functions that receive configuration as parameters.

Key functionality from original sophisticated margin logic:
- Projected margin capacity calculations
- Basis margin requirements estimation
- Cross-platform margin management
- Available margin calculations with safety buffers
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
import logging


logger = logging.getLogger(__name__)

# Error codes for Margin Calculator
ERROR_CODES = {
    "MARGIN-001": "Margin capacity calculation failed",
    "MARGIN-002": "Basis margin estimation failed",
    "MARGIN-003": "Margin requirement calculation failed",
    "MARGIN-004": "Maintenance margin calculation failed",
    "MARGIN-005": "Margin ratio calculation failed",
    "MARGIN-006": "Liquidation price calculation failed",
    "MARGIN-007": "Available margin calculation failed",
    "MARGIN-008": "Cross margin calculation failed",
    "MARGIN-009": "Funding payment calculation failed",
    "MARGIN-010": "Portfolio margin calculation failed",
    "MARGIN-011": "Margin health calculation failed",
    "MARGIN-012": "Basis margin calculation failed",
}


class MarginCalculator:
    """Pure margin calculation functions - no side effects or I/O.

    All functions receive configuration as parameters following Service-Engine separation.
    Rebuilt from sophisticated margin logic in original strategy_engine.py.
    """

    @staticmethod
    def calculate_projected_margin_capacity_after_borrowing(
        current_collateral_value: Decimal,
        current_debt_value: Decimal,
        additional_borrowing_usd: Decimal,
        ltv_config: Dict[str, Any],
        strategy_config: Dict[str, Any],
        collateral_efficiency: Decimal = Decimal("0.95"),
    ) -> Decimal:
        """Calculate projected margin capacity after additional borrowing.

        Sophisticated calculation from original strategy_engine.py (lines 946-984)
        that projects remaining borrowing capacity after a leverage operation.

        Args:
            current_collateral_value: Current collateral value in USD
            current_debt_value: Current debt value in USD
            additional_borrowing_usd: Additional borrowing amount in USD
            ltv_config: LTV configuration from settings
            strategy_config: Strategy configuration from settings
            collateral_efficiency: Fraction of borrowed amount that becomes collateral

        Returns:
            Projected remaining margin capacity in USD
        """
        # Project after borrowing and staking
        projected_debt_value = current_debt_value + additional_borrowing_usd

        # Assume borrowed amount becomes collateral (e.g., staked)
        collateral_increase = additional_borrowing_usd * collateral_efficiency
        projected_collateral_value = current_collateral_value + collateral_increase

        # Calculate projected LTV
        if projected_collateral_value <= 0:
            return Decimal("0")

        projected_ltv = projected_debt_value / projected_collateral_value

        # Get max safe LTV from config
        # For this calculation, assume conservative mixed collateral
        standard_limits = ltv_config["standard_limits"]  # Fail-fast if missing
        avg_max_ltv = sum(Decimal(str(v)) for v in standard_limits.values()) / len(standard_limits)

        # Use safe_ltv from config (already buffered)
        safe_ltv_config = strategy_config["ltv"]["safe_ltv"]  # Fail-fast if missing
        final_max_ltv = Decimal(str(safe_ltv_config["standard_borrowing"]))  # Fail-fast if missing

        if projected_ltv >= final_max_ltv:
            return Decimal("0")  # No capacity remaining

        # Calculate remaining capacity
        remaining_ltv = final_max_ltv - projected_ltv
        remaining_capacity = projected_collateral_value * remaining_ltv

        return max(Decimal("0"), remaining_capacity)

    @staticmethod
    def estimate_basis_margin_requirements(
        eth_exposure: Decimal,
        share_class: str,
        initial_capital: Decimal,
        eth_price: Decimal,
        risk_config: Dict[str, Any],
        strategy_config: Dict[str, Any],
    ) -> Decimal:
        """Estimate margin requirements for basis trading.

        Sophisticated estimation from original strategy_engine.py (lines 985-1007)
        that handles different share class requirements.

        Args:
            eth_exposure: Total ETH exposure requiring hedging
            share_class: "ETH" or "USDT"
            initial_capital: Initial capital amount
            eth_price: Current ETH price
            risk_config: Risk configuration from settings
            strategy_config: Strategy configuration from settings

        Returns:
            Estimated margin requirement in USD
        """
        if share_class == "ETH":
            # ETH share class: Only need margin for additional ETH bought with borrowed USDT
            basis_leverage_factor = Decimal(
                str(strategy_config["basis_leverage_factor"])
            )  # Fail-fast if missing
            estimated_additional_usdt = initial_capital * (basis_leverage_factor - Decimal("1"))
            estimated_additional_eth = estimated_additional_usdt / eth_price

            # Calculate margin for additional ETH
            return MarginCalculator.calculate_margin_for_exposure(
                estimated_additional_eth, eth_price, risk_config
            )
        else:
            # USDT share class: Need to hedge portion of staked ETH
            return MarginCalculator.calculate_margin_for_exposure(
                eth_exposure, eth_price, risk_config
            )

    @staticmethod
    def calculate_margin_for_exposure(
        eth_exposure: Decimal, eth_price: Decimal, risk_config: Dict[str, Any]
    ) -> Decimal:
        """Calculate margin required for a given ETH exposure.

        Args:
            eth_exposure: ETH exposure in tokens
            eth_price: Current ETH price
            risk_config: Risk configuration from settings

        Returns:
            Required margin in USD
        """
        position_value = eth_exposure * eth_price

        # Get margin parameters from config - fail-fast if missing
        initial_margin_pct = Decimal(
            str(risk_config["bybit_initial_margin_pct"])
        )  # Fail-fast if missing
        price_buffer_pct = Decimal(str(risk_config["price_buffer_pct"]))  # Fail-fast if missing
        margin_buffer = Decimal(
            str(risk_config["basis_trade_margin_buffer"])
        )  # Fail-fast if missing

        # Combined margin requirement
        total_margin_pct = initial_margin_pct + price_buffer_pct + margin_buffer
        required_margin = position_value * total_margin_pct

        logger.debug(
            f"Margin for exposure: {eth_exposure:.4f} ETH @ ${eth_price:.0f} = "
            f"${position_value:,.0f}, margin: {total_margin_pct:.1%} = ${required_margin:,.0f}"
        )

        return required_margin

    @staticmethod
    def calculate_margin_requirement(
        position_size: Decimal,
        leverage: Decimal = Decimal("10"),
        initial_margin_rate: Optional[Decimal] = None,
    ) -> Decimal:
        """
        Calculate initial margin requirement for a position.

        Args:
            position_size: Size of position in USD
            leverage: Maximum leverage allowed
            initial_margin_rate: Initial margin percentage (derived from leverage if not provided)

        Returns:
            Required margin in USD
        """
        if initial_margin_rate is not None:
            return position_size * initial_margin_rate
        elif leverage > 0:
            return position_size / leverage
        else:
            return position_size * Decimal("0.10")  # Default 10%

    @staticmethod
    def calculate_maintenance_margin(
        position_size: Decimal, maintenance_rate: Decimal = Decimal("0.05")
    ) -> Decimal:
        """
        Calculate maintenance margin requirement.

        Args:
            position_size: Size of position in USD
            maintenance_rate: Maintenance margin percentage

        Returns:
            Maintenance margin in USD
        """
        return position_size * maintenance_rate

    @staticmethod
    def calculate_margin_ratio(
        current_margin: Decimal, used_margin: Decimal, position_value: Decimal
    ) -> Decimal:
        """
        Calculate current margin ratio.

        Args:
            current_margin: Current available margin
            used_margin: Margin already in use
            position_value: Total position value

        Returns:
            Margin ratio (lower is riskier)
        """
        if position_value == 0:
            return Decimal("999")  # No position

        total_margin = current_margin + used_margin
        return total_margin / position_value

    @staticmethod
    def calculate_liquidation_price(
        entry_price: Decimal,
        is_long: bool,
        margin: Decimal,
        position_size: Decimal,
        maintenance_rate: Decimal = Decimal("0.05"),
        fee_rate: Decimal = Decimal("0.0006"),
    ) -> Decimal:
        """
        Calculate liquidation price for a position.

        Args:
            entry_price: Entry price of position
            is_long: True for long, False for short
            margin: Initial margin used
            position_size: Size of position
            maintenance_rate: Maintenance margin rate
            fee_rate: Trading fee rate

        Returns:
            Liquidation price
        """
        contracts = position_size / entry_price if entry_price > 0 else Decimal("0")

        if contracts == 0:
            return Decimal("0")

        # Calculate total fees
        total_fees = position_size * fee_rate * 2  # Entry and exit fees

        # Calculate loss that would trigger liquidation
        max_loss = margin - (position_size * maintenance_rate) - total_fees

        if max_loss <= 0:
            # Already at risk of liquidation
            return entry_price

        # Calculate price movement that causes max loss
        price_move_pct = max_loss / position_size

        if is_long:
            liquidation_price = entry_price * (Decimal("1") - price_move_pct)
        else:
            liquidation_price = entry_price * (Decimal("1") + price_move_pct)

        return max(liquidation_price, Decimal("0"))

    @staticmethod
    def calculate_available_margin(
        total_collateral: Decimal,
        used_margin: Decimal,
        unrealized_pnl: Decimal = Decimal("0"),
        margin_buffer: Decimal = Decimal("0.02"),
    ) -> Decimal:
        """
        Calculate available margin for new positions.

        Args:
            total_collateral: Total collateral value
            used_margin: Margin already in use
            unrealized_pnl: Unrealized PnL from open positions
            margin_buffer: Safety buffer to maintain

        Returns:
            Available margin for new positions
        """
        # Account for unrealized PnL
        effective_collateral = total_collateral + unrealized_pnl

        # Apply safety buffer
        usable_collateral = effective_collateral * (Decimal("1") - margin_buffer)

        # Subtract used margin
        available = usable_collateral - used_margin

        return max(available, Decimal("0"))

    @staticmethod
    def calculate_cross_margin_requirement(
        positions: List[Dict[str, Decimal]],
        correlation_matrix: Optional[Dict[Tuple[str, str], Decimal]] = None,
    ) -> Decimal:
        """
        Calculate margin requirement for cross-margined positions.

        Args:
            positions: List of positions with 'symbol', 'size', 'side' keys
            correlation_matrix: Correlation between assets for risk calculation

        Returns:
            Total margin requirement accounting for correlation
        """
        if not positions:
            return Decimal("0")

        # Simple implementation without correlation
        if correlation_matrix is None:
            total_margin = Decimal("0")
            for pos in positions:
                margin = MarginCalculator.calculate_margin_requirement(
                    pos.get("size", Decimal("0"))
                )
                total_margin += margin
            return total_margin

        # Advanced calculation with correlation
        # This would implement portfolio margin calculation
        # For now, use simple summation with a diversification benefit
        total_margin = Decimal("0")
        for pos in positions:
            margin = MarginCalculator.calculate_margin_requirement(pos.get("size", Decimal("0")))
            total_margin += margin

        # Apply diversification benefit (simplified)
        if len(positions) > 1:
            total_margin *= Decimal("0.85")  # 15% reduction for diversification

        return total_margin

    @staticmethod
    def calculate_funding_payment(
        position_size: Decimal, funding_rate: Decimal, hours: int = 8
    ) -> Decimal:
        """
        Calculate funding payment for perpetual positions.

        Args:
            position_size: Size of position in USD
            funding_rate: Funding rate (8-hour rate typically)
            hours: Hours for the funding period

        Returns:
            Funding payment (positive = receive, negative = pay)
        """
        # Standard funding is every 8 hours
        periods_per_day = Decimal(str(24 / hours))
        daily_rate = funding_rate * periods_per_day

        return position_size * funding_rate

    @staticmethod
    def calculate_portfolio_margin(
        positions: Dict[str, Dict[str, Decimal]],
        market_scenarios: List[Dict[str, Decimal]],
        confidence_level: Decimal = Decimal("0.99"),
    ) -> Decimal:
        """
        Calculate portfolio margin using scenario analysis.

        Args:
            positions: Positions by symbol with size and side
            market_scenarios: List of market scenarios with price changes
            confidence_level: VaR confidence level

        Returns:
            Portfolio margin requirement
        """
        if not positions or not market_scenarios:
            return Decimal("0")

        scenario_losses = []

        for scenario in market_scenarios:
            total_loss = Decimal("0")

            for symbol, position in positions.items():
                price_change = scenario.get(symbol, Decimal("0"))
                position_size = position.get("size", Decimal("0"))
                is_long = position.get("side", "long") == "long"

                if is_long:
                    loss = position_size * (-price_change)
                else:
                    loss = position_size * price_change

                total_loss += max(loss, Decimal("0"))

            scenario_losses.append(total_loss)

        # Sort losses and take percentile for VaR
        scenario_losses.sort(reverse=True)
        var_index = int(len(scenario_losses) * (Decimal("1") - confidence_level))
        var_index = max(0, min(var_index, len(scenario_losses) - 1))

        return scenario_losses[var_index]

    @staticmethod
    def calculate_margin_health(
        positions: List[Dict[str, Any]], current_prices: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate margin health for perpetual positions.

        Args:
            positions: List of position dicts with 'symbol', 'size', 'side'
            current_prices: Current market prices

        Returns:
            Margin health assessment with action recommendations
        """
        if not positions:
            return {
                "health_status": "HEALTHY",
                "margin_ratio": Decimal("999"),
                "needs_action": False,
                "available_margin": Decimal("0"),
                "used_margin": Decimal("0"),
            }

        total_position_value = Decimal("0")
        total_used_margin = Decimal("0")

        # Calculate total position value and used margin
        for position in positions:
            symbol = position.get("symbol", "")
            size = Decimal(str(position.get("size", 0)))

            # Get price for base asset (e.g., ETH from ETHUSDT)
            base_token = symbol.replace("USDT", "")
            price = Decimal(str(current_prices.get(base_token, 0)))

            position_value = size * price
            total_position_value += position_value

            # Calculate used margin (assume 10% initial margin requirement)
            initial_margin_rate = Decimal("0.10")
            used_margin = position_value * initial_margin_rate
            total_used_margin += used_margin

        # Calculate current margin ratio (simplified - would need actual margin balance)
        # For now, assume margin = 20% of position value as baseline
        estimated_margin = total_position_value * Decimal("0.20")
        margin_ratio = (
            estimated_margin / total_position_value if total_position_value > 0 else Decimal("999")
        )

        # Determine health status based on margin ratio
        maintenance_threshold = Decimal("0.15")  # 15% maintenance margin
        warning_threshold = Decimal("0.25")  # 25% warning threshold

        if margin_ratio < maintenance_threshold * Decimal("1.2"):  # Within 20% of maintenance
            health_status = "EMERGENCY"
            needs_action = True
        elif margin_ratio < warning_threshold:
            health_status = "WARNING"
            needs_action = True
        elif margin_ratio < Decimal("0.35"):  # Below 35% - monitor closely
            health_status = "CAUTION"
            needs_action = False
        else:
            health_status = "HEALTHY"
            needs_action = False

        return {
            "health_status": health_status,
            "margin_ratio": float(margin_ratio),
            "needs_action": needs_action,
            "total_position_value": float(total_position_value),
            "used_margin": float(total_used_margin),
            "estimated_available_margin": float(estimated_margin),
            "maintenance_threshold": float(maintenance_threshold),
            "positions_count": len(positions),
            "recommendation": _get_margin_recommendation(health_status, margin_ratio),
        }

    @staticmethod
    def calculate_basis_margin(
        spot_position: Decimal,
        futures_position: Decimal,
        spot_margin_rate: Decimal = Decimal("1.0"),  # 100% for spot
        futures_margin_rate: Decimal = Decimal("0.10"),  # 10% for futures
    ) -> Decimal:
        """
        Calculate margin for basis trading positions.

        Args:
            spot_position: Spot position size in USD
            futures_position: Futures position size in USD
            spot_margin_rate: Margin rate for spot
            futures_margin_rate: Margin rate for futures

        Returns:
            Total margin requirement for basis position
        """
        spot_margin = spot_position * spot_margin_rate
        futures_margin = abs(futures_position) * futures_margin_rate

        # Apply netting benefit if positions offset
        if spot_position > 0 and futures_position < 0:
            # Long spot, short futures - natural hedge
            net_exposure = abs(spot_position + futures_position)
            hedge_benefit = min(spot_position, abs(futures_position)) * Decimal("0.5")
            total_margin = spot_margin + futures_margin - hedge_benefit
        else:
            total_margin = spot_margin + futures_margin

        return max(total_margin, Decimal("0"))


def _get_margin_recommendation(health_status: str, margin_ratio: Decimal) -> str:
    """Get margin action recommendation based on health status."""
    if health_status == "EMERGENCY":
        return "IMMEDIATE_ACTION: Transfer collateral or reduce positions"
    elif health_status == "WARNING":
        return "ACTION_NEEDED: Add margin support within 4 hours"
    elif health_status == "CAUTION":
        return "MONITOR: Prepare for potential margin support"
    else:
        return "HEALTHY: No action needed"
