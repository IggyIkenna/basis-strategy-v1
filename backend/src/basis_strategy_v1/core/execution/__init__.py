"""
Execution Module

Provides the new execution architecture:
1. ExecutionManager - Processes orders and routes via VenueInterfaceManager
2. VenueInterfaceManager - Routes orders to execution interfaces
3. PositionUpdateHandler - Orchestrates tight loop reconciliation
"""

from .execution_manager import ExecutionManager
from .venue_interface_manager import VenueInterfaceManager

__all__ = [
    'ExecutionManager',
    'VenueInterfaceManager'
]
