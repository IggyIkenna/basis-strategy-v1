"""Infrastructure logging components.

This module contains logging and event management components:
- EventLogger: Handles event logging and audit trails
"""

from .event_logger import EventLogger

__all__ = [
    'EventLogger'
]
