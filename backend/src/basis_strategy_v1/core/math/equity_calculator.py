"""
Equity Calculator

Stateless utility for calculating total equity by converting all positions to share class currency
and computing assets minus debts (excluding derivatives).

Reference: docs/INSTRUMENT_DEFINITIONS.md - Instrument Type Classification
"""

from typing import Dict, Any
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_equity(
    positions: Dict[str, float],
    utility_manager,
    share_class: str,
    timestamp: pd.Timestamp
) -> Dict[str, Any]:
    """
    Calculate total equity from position data.

    Args:
        positions: Dictionary of position_key -> amount
        utility_manager: UtilityManager instance for price conversions
        share_class: Share class currency ('USDT' or 'ETH')
        timestamp: Timestamp for price conversions

    Returns:
        Dictionary with equity breakdown:
        {
            'total_equity': float,
            'total_assets': float,
            'total_debts': float,
            'asset_positions': Dict[str, float],
            'debt_positions': Dict[str, float],
            'excluded_derivatives': Dict[str, float]
        }
    """
    try:
        total_assets = 0.0
        total_debts = 0.0
        asset_positions = {}
        debt_positions = {}
        excluded_derivatives = {}

        for position_key, amount in positions.items():
            if amount == 0:
                continue

            # Get instrument type classification
            instrument_type = utility_manager.get_instrument_type(position_key)

            if instrument_type == 'asset':
                # Convert to share class currency
                share_class_value = utility_manager.convert_position_to_share_class(
                    position_key, amount, share_class, timestamp
                )
                total_assets += share_class_value
                asset_positions[position_key] = share_class_value

            elif instrument_type == 'debt':
                # Convert to share class currency (debts are positive values)
                share_class_value = utility_manager.convert_position_to_share_class(
                    position_key, amount, share_class, timestamp
                )
                total_debts += share_class_value
                debt_positions[position_key] = share_class_value

            elif instrument_type == 'derivative':
                # Exclude derivatives from equity calculation
                excluded_derivatives[position_key] = amount

            else:
                logger.warning(f"Unknown instrument type for {position_key}: {instrument_type}")

        # Calculate total equity: assets - debts
        total_equity = total_assets - total_debts

        return {
            'total_equity': total_equity,
            'total_assets': total_assets,
            'total_debts': total_debts,
            'asset_positions': asset_positions,
            'debt_positions': debt_positions,
            'excluded_derivatives': excluded_derivatives
        }

    except Exception as e:
        logger.error(f"Error calculating equity for {len(positions)} positions: {e}")
        return {
            'total_equity': 0.0,
            'total_assets': 0.0,
            'total_debts': 0.0,
            'asset_positions': {},
            'debt_positions': {},
            'excluded_derivatives': {}
        }
