"""
Core Models Package

Unified Order and Trade models for the basis-strategy-v1 platform.
Replaces the previous StrategyAction and instruction block abstractions.

Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-XXX (to be created)
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Updated execution flow
"""

from .order import Order, OrderOperation, VenueType
from .trade import Trade, TradeStatus

__all__ = [
    'Order',
    'OrderOperation', 
    'VenueType',
    'Trade',
    'TradeStatus'
]
