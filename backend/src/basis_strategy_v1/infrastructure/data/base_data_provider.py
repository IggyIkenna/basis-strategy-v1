"""
Base Data Provider - Canonical Architecture Implementation

Abstract base class for all data providers implementing the canonical architecture
pattern with standardized data structure and mode-agnostic interface.

Reference: docs/CODE_STRUCTURE_PATTERNS.md - Data Provider Patterns
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 8 (Data Provider Architecture)
Reference: docs/specs/09_DATA_PROVIDER.md - DataProvider Component Specification
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class BaseDataProvider(ABC):
    """Abstract base class for all data providers implementing canonical architecture."""
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        """
        Initialize base data provider.
        
        Args:
            execution_mode: 'backtest' or 'live'
            config: Configuration dictionary with mode and data_requirements
        """
        self.execution_mode = execution_mode
        self.config = config
        self.available_data_types = []  # Set by subclasses
        self.data_requirements = config.get('data_requirements', [])
        
        # Validate required config fields
        if 'mode' not in config:
            raise ValueError("Config must contain 'mode' field")
        
        if not self.data_requirements:
            raise ValueError("Config must contain 'data_requirements' field")
        
        logger.info(f"BaseDataProvider initialized for mode: {config['mode']} ({execution_mode})")
    
    @abstractmethod
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Return standardized data structure.
        
        ALL providers must return data in this exact format:
        {
            'market_data': {
                'prices': {...},
                'rates': {...}
            },
            'protocol_data': {
                'aave_indexes': {...},
                'oracle_prices': {...},
                'perp_prices': {...}
            },
            'staking_data': {...},
            'execution_data': {
                'wallet_balances': {...},
                'smart_contract_balances': {...},
                'cex_spot_balances': {...},
                'cex_derivatives_balances': {...},
                'gas_costs': {...},
                'execution_costs': {...}
            }
        }
        
        Args:
            timestamp: Timestamp for data retrieval
            
        Returns:
            Standardized data structure dictionary
        """
        pass
    
    @abstractmethod
    def validate_data_requirements(self, data_requirements: List[str]) -> None:
        """
        Validate that this provider can satisfy all data requirements.
        Raises ValueError if any requirements cannot be met.
        
        Args:
            data_requirements: List of required data types
            
        Raises:
            ValueError: If any requirements cannot be satisfied
        """
        pass
    
    @abstractmethod
    def get_timestamps(self, start_date: str, end_date: str) -> List[pd.Timestamp]:
        """
        Get available timestamps for backtest period.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of timestamps
        """
        pass
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get data provider health status.
        
        Returns:
            Health status dictionary
        """
        return {
            'status': 'healthy',
            'execution_mode': self.execution_mode,
            'mode': self.config.get('mode'),
            'available_data_types': self.available_data_types,
            'data_requirements': self.data_requirements,
            'timestamp': pd.Timestamp.now()
        }
    
    def __str__(self) -> str:
        """String representation of data provider."""
        return f"{self.__class__.__name__}(mode={self.config.get('mode')}, execution_mode={self.execution_mode})"
    
    def __repr__(self) -> str:
        """Detailed string representation of data provider."""
        return f"{self.__class__.__name__}(execution_mode='{self.execution_mode}', config={self.config})"
    
    # ============================================================================
    # ML Data Provider Methods (Optional - Backward Compatible)
    # ============================================================================
    # TODO: ML data files required at data/market_data/ml/ and data/ml_data/predictions/
    # TODO: Set BASIS_ML_API_TOKEN environment variable for live mode
    
    def _ml_data_enabled(self) -> bool:
        """
        Check if ML data is configured for this strategy mode.
        
        Returns:
            True if ML data requirements present, False otherwise
        """
        return 'ml_ohlcv_5min' in self.data_requirements or 'ml_predictions' in self.data_requirements
    
    def get_ml_ohlcv(self, timestamp: pd.Timestamp, symbol: str) -> Optional[Dict]:
        """
        Get 5-min OHLCV bar for timestamp and symbol.
        Returns None if ML data not configured (backward compatible).
        
        Args:
            timestamp: Timestamp for data retrieval
            symbol: Trading symbol (e.g., 'BTC', 'ETH', 'USDT')
            
        Returns:
            OHLCV dict {'open': float, 'high': float, 'low': float, 'close': float, 'volume': float}
            or None if ML data not enabled
        """
        if not self._ml_data_enabled():
            return None
        
        # Subclasses must implement _load_ml_ohlcv
        return self._load_ml_ohlcv(timestamp, symbol)
    
    
    def _load_ml_ohlcv(self, timestamp: pd.Timestamp, symbol: str) -> Dict:
        """
        Load ML OHLCV data (subclasses override for backtest vs live).
        
        Args:
            timestamp: Timestamp for data
            symbol: Trading symbol
            
        Returns:
            OHLCV dictionary
            
        Raises:
            NotImplementedError: Subclass must implement
        """
        raise NotImplementedError("Subclass must implement _load_ml_ohlcv")
    
    def _load_ml_prediction(self, timestamp: pd.Timestamp, symbol: str) -> Dict:
        """
        Load ML prediction (subclasses override for backtest vs live).
        
        Args:
            timestamp: Timestamp for prediction
            symbol: Trading symbol
            
        Returns:
            Prediction dictionary
            
        Raises:
            NotImplementedError: Subclass must implement
        """
        raise NotImplementedError("Subclass must implement _load_ml_prediction")