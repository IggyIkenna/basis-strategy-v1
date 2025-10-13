"""
Timestamp formatting utilities for consistent data output.

This module provides standardized timestamp formatting functions to ensure
all data downloaders produce consistent timestamp formats without microseconds.
"""

from datetime import datetime


def format_timestamp_utc(timestamp_ms: int) -> str:
    """
    Format a Unix timestamp (in milliseconds) to ISO format without microseconds.
    
    Args:
        timestamp_ms: Unix timestamp in milliseconds
        
    Returns:
        ISO formatted timestamp string (e.g., "2024-01-05T00:00:00Z")
    """
    dt = datetime.utcfromtimestamp(timestamp_ms / 1000)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def format_timestamp_from_datetime(dt: datetime) -> str:
    """
    Format a datetime object to ISO format without microseconds.
    
    Args:
        dt: datetime object
        
    Returns:
        ISO formatted timestamp string (e.g., "2024-01-05T00:00:00Z")
    """
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
