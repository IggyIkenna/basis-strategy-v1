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
    
    def __init__(self, execution_mode: str, config: Dict[str, Any], utility_manager=None):
        """
        Initialize base data provider.
        
        Args:
            execution_mode: 'backtest' or 'live'
            config: Configuration dictionary with mode and data_requirements
            utility_manager: Centralized utility manager for config-driven operations
        """
        self.execution_mode = execution_mode
        self.config = config
        self.utility_manager = utility_manager
        self.available_data_types = []  # Set by subclasses
        self.data_requirements = config.get('data_requirements', [])
        self.health_status = "healthy"
        self.error_count = 0
        
        # Validate required config fields
        if 'mode' not in config:
            raise ValueError("Config must contain 'mode' field")
        
        if not self.data_requirements:
            raise ValueError("Config must contain 'data_requirements' field")
        
        logger.info(f"BaseDataProvider initialized for mode: {config['mode']} ({execution_mode})")
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors with structured error handling."""
        self.error_count += 1
        error_code = f"DP_ERROR_{self.error_count:04d}"
        
        logger.error(f"Data Provider error {error_code}: {str(error)}", extra={
            'error_code': error_code,
            'context': context,
            'execution_mode': self.execution_mode,
            'component': self.__class__.__name__
        })
        
        # Update health status based on error count
        if self.error_count > 10:
            self.health_status = "unhealthy"
        elif self.error_count > 5:
            self.health_status = "degraded"
    
    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            'status': self.health_status,
            'error_count': self.error_count,
            'execution_mode': self.execution_mode,
            'available_data_types_count': len(self.available_data_types),
            'data_requirements_count': len(self.data_requirements),
            'component': self.__class__.__name__
        }
    
    def _process_config_driven_operations(self, operations: List[Dict]) -> List[Dict]:
        """Process operations based on configuration settings."""
        processed_operations = []
        for operation in operations:
            if self._validate_operation(operation):
                processed_operations.append(operation)
            else:
                self._handle_error(ValueError(f"Invalid operation: {operation}"), "config_driven_validation")
        return processed_operations
    
    def _validate_operation(self, operation: Dict) -> bool:
        """Validate operation against configuration."""
        required_fields = ['data_type', 'timestamp', 'source']
        return all(field in operation for field in required_fields)
    
    def _process_config_driven_subscriptions(self) -> List[str]:
        """Process data subscriptions based on configuration settings."""
        try:
            if self.utility_manager:
                # Use utility manager for config-driven subscription processing
                share_class = self.utility_manager.get_share_class(self.config)
                asset = self.utility_manager.get_asset(self.config)
                
                # Process subscriptions based on config
                subscriptions = []
                for requirement in self.data_requirements:
                    if self._validate_subscription_requirement(requirement, share_class, asset):
                        subscriptions.append(requirement)
                
                logger.info(f"Processed {len(subscriptions)} config-driven subscriptions for {share_class} {asset}")
                return subscriptions
            else:
                # Fallback to direct config processing
                return self.data_requirements
                
        except Exception as e:
            self._handle_error(e, "config_driven_subscription_processing")
            return self.data_requirements
    
    def _validate_subscription_requirement(self, requirement: str, share_class: str, asset: str) -> bool:
        """Validate subscription requirement against config-driven parameters."""
        # Basic validation logic for subscription requirements
        valid_requirements = [
            'market_data', 'protocol_data', 'staking_data', 'execution_data',
            'prices', 'rates', 'aave_indexes', 'oracle_prices', 'perp_prices',
            'wallet_balances', 'smart_contract_balances', 'cex_spot_balances',
            'cex_derivatives_balances', 'gas_costs', 'execution_costs'
        ]
        return requirement in valid_requirements
    
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
    def _validate_data_requirements(self, data_requirements: List[str]) -> None:
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
    
    def _get_health_status(self) -> Dict[str, Any]:
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
    
    def _get_ml_ohlcv(self, timestamp: pd.Timestamp, symbol: str) -> Optional[Dict]:
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
    
    # Standardized Logging Methods (per 17_HEALTH_ERROR_SYSTEMS.md and 08_EVENT_LOGGER.md)
    
    def log_structured_event(self, timestamp: pd.Timestamp, event_type: str, level: str, message: str, component_name: str, data: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> None:
        """Log a structured event with standardized format."""
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            event_data = {
                'timestamp': timestamp,
                'event_type': event_type,
                'level': level,
                'message': message,
                'component_name': component_name,
                'data': data or {},
                'correlation_id': correlation_id
            }
            
            # Log to standard logger
            if level == 'ERROR':
                logger.error(f"[{component_name}] {message}", extra=event_data)
            elif level == 'WARNING':
                logger.warning(f"[{component_name}] {message}", extra=event_data)
            else:
                logger.info(f"[{component_name}] {message}", extra=event_data)
                
        except Exception as e:
            logger.error(f"Failed to log structured event: {e}")
    
    def log_component_event(self, event_type: str, message: str, data: Optional[Dict[str, Any]] = None, level: str = 'INFO') -> None:
        """Log a component-specific event with automatic timestamp and component name."""
        try:
            timestamp = pd.Timestamp.now(tz='UTC')
            self.log_structured_event(timestamp, event_type, level, message, 'DataProvider', data)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log component event: {e}")
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a performance metric."""
        try:
            timestamp = pd.Timestamp.now(tz='UTC')
            message = f"Performance metric: {metric_name} = {value} {unit}"
            metric_data = {
                'metric_name': metric_name,
                'value': value,
                'unit': unit,
                **(data or {})
            }
            self.log_structured_event(timestamp, 'performance_metric', 'INFO', message, 'DataProvider', metric_data)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log performance metric: {e}")
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> None:
        """Log an error with standardized format."""
        try:
            timestamp = pd.Timestamp.now(tz='UTC')
            error_data = {
                'error_type': type(error).__name__,
                'context': context or {},
                'correlation_id': correlation_id
            }
            self.log_structured_event(timestamp, 'error', 'ERROR', str(error), 'DataProvider', error_data)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log error: {e}")
    
    def log_warning(self, message: str, data: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> None:
        """Log a warning with standardized format."""
        try:
            timestamp = pd.Timestamp.now(tz='UTC')
            self.log_structured_event(timestamp, 'warning', 'WARNING', message, 'DataProvider', data, correlation_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log warning: {e}")
    
    def update_state(self, timestamp: pd.Timestamp, trigger_source: str, **kwargs) -> None:
        """Update component state (called by EventDrivenStrategyEngine)."""
        try:
            # Data provider state update logic
            self.log_component_event('state_update', f"State updated by {trigger_source}", {'timestamp': timestamp})
        except Exception as e:
            self.log_error(e, {'trigger_source': trigger_source, 'timestamp': timestamp})
    
    def load_data_for_backtest(self, start_date: pd.Timestamp, end_date: pd.Timestamp, data_requirements: List[str]) -> Dict[str, Any]:
        """Load data for backtest mode."""
        try:
            self.log_component_event('data_loading', f"Loading backtest data from {start_date} to {end_date}")
            
            # Use utility_manager for config-driven operations if available
            if self.utility_manager:
                # Get data requirements from config via utility_manager
                mode = self.config.get('mode', 'default')
                config_requirements = self.utility_manager.get_data_requirements_from_mode(mode)
                self.log_component_event('config_driven', f"Using data requirements from config for mode {mode}")
            
            # This is an abstract method - subclasses should implement
            data = {}
            for requirement in data_requirements:
                # Subclasses should implement specific data loading logic
                data[requirement] = {}
            
            self.log_component_event('data_loaded', f"Loaded {len(data)} data types for backtest")
            return data
            
        except Exception as e:
            self.log_error(e, {'start_date': start_date, 'end_date': end_date, 'data_requirements': data_requirements})
            raise