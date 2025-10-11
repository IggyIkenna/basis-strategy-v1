"""
Base Data Provider Abstract Class

Provides the foundation for all mode-specific data providers with standardized
interface and data structure.

Reference: docs/specs/09_DATA_PROVIDER.md - DataProvider Abstraction Layer
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 8 (Data Provider Architecture)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseDataProvider(ABC):
    """Abstract base class for all data providers"""
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        """
        Initialize base data provider.
        
        Args:
            execution_mode: 'backtest' or 'live' (from BASIS_EXECUTION_MODE)
            config: Configuration dictionary with mode and data_requirements
        """
        self.execution_mode = execution_mode
        self.config = config
        self.mode = config.get('mode')
        self.data_requirements = config.get('data_requirements', [])
        self.available_data_types = []
        self.data_dir = config.get('data_dir', 'data')
        self._data_loaded = False
        
        # Validate required config fields
        if not self.mode:
            raise ValueError("Config must contain 'mode' field")
        
        logger.info(f"Initialized {self.__class__.__name__} for mode: {self.mode}")
    
    @abstractmethod
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Return standardized data structure for all components.
        
        Args:
            timestamp: Timestamp for data query
            
        Returns:
            Standardized data structure with market_data and protocol_data
        """
        pass
    
    @abstractmethod
    def validate_data_requirements(self, data_requirements: List[str]) -> None:
        """
        Validate that this provider can satisfy data requirements.
        
        Args:
            data_requirements: List of required data types
            
        Raises:
            ValueError: If provider cannot satisfy requirements
        """
        pass
    
    @abstractmethod
    def load_data(self) -> None:
        """
        Load all required data for this provider.
        
        Raises:
            DataProviderError: If data loading fails
        """
        pass
    
    def get_timestamps(self) -> pd.DatetimeIndex:
        """
        Get available timestamps for backtest period validation.
        
        Returns:
            DatetimeIndex of available timestamps
        """
        if not self._data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        # Get timestamps from first available dataset
        for data_key, data in self.data.items():
            if isinstance(data, pd.DataFrame) and hasattr(data, 'index'):
                if isinstance(data.index, pd.DatetimeIndex):
                    return data.index
        
        raise ValueError("No timestamp data available")
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get data provider health status.
        
        Returns:
            Dictionary with health status information
        """
        return {
            'status': 'healthy' if self._data_loaded else 'not_loaded',
            'mode': self.mode,
            'execution_mode': self.execution_mode,
            'data_loaded': self._data_loaded,
            'available_data_types': self.available_data_types,
            'data_requirements': self.data_requirements,
            'datasets_loaded': len(getattr(self, 'data', {}))
        }
    
    def _validate_timestamp_alignment(self, data: pd.DataFrame, name: str) -> None:
        """
        Validate that data timestamps are hourly aligned.
        
        Args:
            data: DataFrame to validate
            name: Name of dataset for error messages
            
        Raises:
            ValueError: If timestamps are not hourly aligned
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            return
        
        # Check hourly alignment
        if not all(data.index.minute == 0):
            bad_timestamps = data.index[data.index.minute != 0]
            raise ValueError(
                f"{name}: {len(bad_timestamps)} timestamps not on the hour!\n"
                f"First bad timestamp: {bad_timestamps[0]}"
            )
        
        if not all(data.index.second == 0):
            raise ValueError(f"{name}: Timestamps must have second=0")
        
        # Check UTC timezone
        if data.index.tz is None:
            raise ValueError(f"{name}: Timestamps must be UTC timezone-aware")
    
    def _get_standardized_structure(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Get standardized data structure template.
        
        Args:
            timestamp: Timestamp for data query
            
        Returns:
            Standardized data structure template
        """
        return {
            'timestamp': timestamp,
            'market_data': {
                'prices': {},
                'rates': {},
                'funding_rates': {},
                'futures_prices': {}
            },
            'protocol_data': {
                'aave_indexes': {},
                'oracle_prices': {},
                'staking_rewards': {},
                'protocol_rates': {}
            },
            'execution_data': {
                'gas_costs': {},
                'execution_costs': {}
            }
        }
