"""
Base Position Interface

Abstract base class for position monitoring interfaces.
Provides common interface for all venue-specific position monitoring implementations.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 9 (Execution Interface Factory Extended)
Reference: docs/specs/07B_EXECUTION_INTERFACES.md - Position Monitoring Interface Methods
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd
import logging


logger = logging.getLogger(__name__)


class BasePositionInterface(ABC):
    """
    Base class for position monitoring interfaces.
    
    Provides common interface for all venue-specific position monitoring implementations.
    Handles both backtest (simulation) and live (real API) modes.
    """
    
    def __init__(self, venue: str, execution_mode: str, config: Dict[str, Any]):
        """
        Initialize base position interface.
        
        Args:
            venue: Venue name (e.g., 'binance', 'aave', 'wallet')
            execution_mode: Execution mode ('backtest' or 'live')
            config: Configuration dictionary
        """
        self.venue = venue
        self.execution_mode = execution_mode
        self.config = config
        
        # Initialize structured logger
        self.logger = logging.getLogger(f"{__name__}.{venue}")
        
        self.logger.info(
            f"BasePositionInterface initialized for {venue} in {execution_mode} mode",
            extra={
                'venue': venue,
                'execution_mode': execution_mode,
                'interface_type': 'position'
            }
        )
    
    @abstractmethod
    async def get_positions(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Get positions from venue.
        
        Args:
            timestamp: Current timestamp for data consistency
            
        Returns:
            Dictionary with position data for the venue
        """
        pass
    
    @abstractmethod
    async def get_balance(self, asset: str, timestamp: pd.Timestamp) -> float:
        """
        Get balance for specific asset.
        
        Args:
            asset: Asset symbol (e.g., 'USDT', 'ETH', 'BTC')
            timestamp: Current timestamp for data consistency
            
        Returns:
            Balance amount in native units
        """
        pass
    
    @abstractmethod
    async def get_position_history(self, start_time: pd.Timestamp, end_time: pd.Timestamp) -> List[Dict]:
        """
        Get position history for time range.
        
        Args:
            start_time: Start timestamp for history query
            end_time: End timestamp for history query
            
        Returns:
            List of position snapshots for the time range
        """
        pass
    
    def get_interface_status(self) -> Dict[str, Any]:
        """
        Get current interface status.
        
        Returns:
            Dictionary with interface status information
        """
        return {
            'venue': self.venue,
            'execution_mode': self.execution_mode,
            'interface_type': 'position',
            'status': 'healthy'
        }
    
    def _validate_timestamp(self, timestamp: pd.Timestamp) -> None:
        """
        Validate timestamp for data consistency.
        
        Args:
            timestamp: Timestamp to validate
            
        Raises:
            ValueError: If timestamp is invalid
        """
        if not isinstance(timestamp, pd.Timestamp):
            raise ValueError(f"Timestamp must be pandas.Timestamp, got {type(timestamp)}")
        
        if pd.isna(timestamp):
            raise ValueError("Timestamp cannot be NaN")
    
    def _validate_asset(self, asset: str) -> None:
        """
        Validate asset symbol.
        
        Args:
            asset: Asset symbol to validate
            
        Raises:
            ValueError: If asset is invalid
        """
        if not isinstance(asset, str):
            raise ValueError(f"Asset must be string, got {type(asset)}")
        
        if not asset.strip():
            raise ValueError("Asset cannot be empty")
    
    def _log_position_query(self, method: str, **kwargs) -> None:
        """
        Log position query for debugging.
        
        Args:
            method: Method name being called
            **kwargs: Additional parameters to log
        """
        self.logger.debug(
            f"Position query: {method}",
            extra={
                'venue': self.venue,
                'execution_mode': self.execution_mode,
                'method': method,
                **kwargs
            }
        )
