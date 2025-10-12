"""Core Strategy Components for the new architecture.

Only the 9 core components that are actually used by the EventDrivenStrategyEngine.
All other components have been archived to keep the codebase clean.
"""

# Core components (used by EventDrivenStrategyEngine)
# Import from new locations
from ....core.components.position_monitor import PositionMonitor
from ....core.components.exposure_monitor import ExposureMonitor
from ....core.components.risk_monitor import RiskMonitor
from ....infrastructure.logging.event_logger import EventLogger
__all__ = [
    # Core components (moved to canonical locations)
    'PositionMonitor',
    'ExposureMonitor',
    'RiskMonitor',
    'EventLogger'
]
