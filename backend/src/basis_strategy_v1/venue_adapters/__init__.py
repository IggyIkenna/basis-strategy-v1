"""Venue adapters for external integrations.

This module contains adapters for various venues:
- AaveAdapter: AAVE V3 protocol integration
- MorphoAdapter: Morpho protocol integration
"""

from .aave_adapter import AaveAdapter
from .morpho_adapter import MorphoAdapter

__all__ = [
    'AaveAdapter',
    'MorphoAdapter'
]
