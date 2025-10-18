"""
Data Provider Factory

Creates appropriate data provider based on execution mode and data type.
Routes to 4 provider types: HistoricalDeFi, HistoricalCeFi, LiveDeFi, LiveCeFi.

Key Principles:
- Execution mode routing (backtest vs live)
- Data type routing (defi vs cefi)
- ML service integration for CeFi providers
- No abstract base classes
- Simple factory pattern
"""

import logging
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)


def create_data_provider(execution_mode: str, data_type: str, config: Dict[str, Any]) -> Union['HistoricalDeFiDataProvider', 'HistoricalCeFiDataProvider', 'LiveDeFiDataProvider', 'LiveCeFiDataProvider']:
    """
    Factory routes to appropriate provider based on execution mode and data type.
    
    Args:
        execution_mode: 'backtest' or 'live'
        data_type: 'defi' or 'cefi'
        config: Configuration dictionary with position_subscriptions
        
    Returns:
        Appropriate data provider instance
        
    Raises:
        ValueError: If execution_mode or data_type is unknown
    """
    logger.info(f"Creating data provider: execution_mode={execution_mode}, data_type={data_type}")
    
    if execution_mode == 'backtest' and data_type == 'defi':
        from .historical_defi_data_provider import HistoricalDeFiDataProvider
        return HistoricalDeFiDataProvider(config)
        
    elif execution_mode == 'backtest' and data_type == 'cefi':
        from .historical_cefi_data_provider import HistoricalCeFiDataProvider
        from .ml_service import MLService
        
        ml_service = MLService(config)
        return HistoricalCeFiDataProvider(config, ml_service)
        
    elif execution_mode == 'live' and data_type == 'defi':
        from .live_defi_data_provider import LiveDeFiDataProvider
        return LiveDeFiDataProvider(config)
        
    elif execution_mode == 'live' and data_type == 'cefi':
        from .live_cefi_data_provider import LiveCeFiDataProvider
        from .ml_service import MLService
        
        ml_service = MLService(config)
        return LiveCeFiDataProvider(config, ml_service)
        
    else:
        raise ValueError(f"Unknown execution_mode: {execution_mode} or data_type: {data_type}. Must be 'backtest'/'live' and 'defi'/'cefi'")


def get_data_provider_for_mode(mode: str, execution_mode: str = 'backtest') -> Union['HistoricalDeFiDataProvider', 'HistoricalCeFiDataProvider', 'LiveDeFiDataProvider', 'LiveCeFiDataProvider']:
    """
    Get data provider for specific mode.
    
    Args:
        mode: Mode name (e.g., 'pure_lending_usdt', 'ml_btc_directional_btc_margin')
        execution_mode: 'backtest' or 'live'
        
    Returns:
        Appropriate data provider instance
    """
    # Load mode config
    config_path = f"configs/modes/{mode}.yaml"
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Error loading config for mode {mode}: {e}")
    
    # Determine data type from mode
    if mode.startswith('ml_'):
        data_type = 'cefi'
    else:
        data_type = 'defi'
    
    return create_data_provider(execution_mode, data_type, config)