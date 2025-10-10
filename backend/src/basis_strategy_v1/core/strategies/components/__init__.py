"""Core Strategy Components for the new architecture.

Only the 9 core components that are actually used by the EventDrivenStrategyEngine.
All other components have been archived to keep the codebase clean.
"""

# Core components (used by EventDrivenStrategyEngine)
from .position_monitor import PositionMonitor
from .event_logger import EventLogger
from .exposure_monitor import ExposureMonitor
from .strategy_manager import StrategyManager
from .risk_monitor import RiskMonitor

__all__ = [
    # Core components (8 total - legacy execution managers removed, risk monitor moved here)
    'PositionMonitor',
    'EventLogger',
    'ExposureMonitor',
    'StrategyManager',
    'RiskMonitor'
]
