"""
Data Provider Factory

Creates the appropriate data provider based on execution_mode and config-driven mode selection.

Architecture:
- Config-driven provider selection based on mode field in config
- Mode-specific data providers for each strategy type
- Standardized data structure across all providers
- Comprehensive data validation with error codes

Reference: docs/specs/09_DATA_PROVIDER.md - DataProvider Factory
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 8 (Data Provider Architecture)
"""

from typing import Dict, Any, Union, Optional
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)


def create_data_provider(
    execution_mode: str,
    config: Dict[str, Any],
    data_dir: Optional[str] = None,
    backtest_start_date: Optional[str] = None,
    backtest_end_date: Optional[str] = None
) -> 'BaseDataProvider':
    """
    Create the appropriate data provider based on execution_mode and config.
    
    Args:
        execution_mode: 'backtest' or 'live' (from BASIS_EXECUTION_MODE)
        config: Configuration dictionary with mode and data_requirements
        data_dir: Path to data directory (optional, uses config or env var)
        backtest_start_date: Start date for backtest validation (YYYY-MM-DD format)
        backtest_end_date: End date for backtest validation (YYYY-MM-DD format)
        
    Returns:
        Appropriate data provider instance
        
    Raises:
        ValueError: If config is invalid or provider cannot be created
    """
    # Validate required config fields (fail-fast)
    if 'mode' not in config:
        raise ValueError("Config must contain 'mode' field")
    
    if 'data_requirements' not in config:
        raise ValueError("Config must contain 'data_requirements' field")
    
    mode = config['mode']
    data_requirements = config['data_requirements']
    
    # Set data_dir from config or environment variable
    if data_dir is None:
        data_dir = config.get('data_dir', os.getenv('BASIS_DATA_DIR', 'data'))
    
    # Add data_dir to config for providers
    config['data_dir'] = data_dir
    
    # Validate environment variables for backtest mode
    if execution_mode == 'backtest':
        if not os.getenv('BASIS_DATA_START_DATE'):
            raise ValueError("BASIS_DATA_START_DATE environment variable must be set for backtest mode")
        if not os.getenv('BASIS_DATA_END_DATE'):
            raise ValueError("BASIS_DATA_END_DATE environment variable must be set for backtest mode")
    
    # Create mode-specific provider
    provider = _create_mode_specific_provider(execution_mode, config)
    
    # Validate that provider can satisfy data requirements
    provider.validate_data_requirements(data_requirements)
    
    # Load data for backtest mode
    if execution_mode == 'backtest':
        provider.load_data()
    
    logger.info(f"✅ Created {provider.__class__.__name__} for mode: {mode}")
    logger.info(f"📊 Data requirements: {data_requirements}")
    
    return provider


def _create_mode_specific_provider(execution_mode: str, config: Dict[str, Any]) -> 'BaseDataProvider':
    """
    Create mode-specific data provider using canonical architecture.
    
    Args:
        execution_mode: 'backtest' or 'live'
        config: Configuration dictionary
        
    Returns:
        Mode-specific data provider instance
    """
    mode = config['mode']
    
    # Create mode-specific provider using canonical architecture
    provider_map = {
        'pure_lending': 'PureLendingDataProvider',
        'btc_basis': 'BTCBasisDataProvider',
        'eth_basis': 'ETHBasisDataProvider',
        'eth_staking_only': 'ETHStakingOnlyDataProvider',
        'eth_leveraged': 'ETHLeveragedDataProvider',
        'usdt_market_neutral_no_leverage': 'USDTMarketNeutralNoLeverageDataProvider',
        'usdt_market_neutral': 'USDTMarketNeutralDataProvider',
        'ml_btc_directional': 'MLDirectionalDataProvider',  # NEW
        'ml_usdt_directional': 'MLDirectionalDataProvider'  # NEW
    }
    
    if mode not in provider_map:
        raise ValueError(f"Unknown strategy mode: {mode}")
    
    # Import and create the appropriate provider
    if execution_mode == 'live':
        # For live mode, use live data provider (to be implemented)
        from .live_data_provider import LiveDataProvider
        return LiveDataProvider(config=config, mode=mode)
    else:
        # For backtest mode, use mode-specific historical providers
        if mode == 'pure_lending':
            from .pure_lending_data_provider import PureLendingDataProvider
            return PureLendingDataProvider(execution_mode, config)
        elif mode == 'btc_basis':
            from .btc_basis_data_provider import BTCBasisDataProvider
            return BTCBasisDataProvider(execution_mode, config)
        elif mode == 'eth_basis':
            from .eth_basis_data_provider import ETHBasisDataProvider
            return ETHBasisDataProvider(execution_mode, config)
        elif mode == 'eth_staking_only':
            from .eth_staking_only_data_provider import ETHStakingOnlyDataProvider
            return ETHStakingOnlyDataProvider(execution_mode, config)
        elif mode == 'eth_leveraged':
            from .eth_leveraged_data_provider import ETHLeveragedDataProvider
            return ETHLeveragedDataProvider(execution_mode, config)
        elif mode == 'usdt_market_neutral_no_leverage':
            from .usdt_market_neutral_no_leverage_data_provider import USDTMarketNeutralNoLeverageDataProvider
            return USDTMarketNeutralNoLeverageDataProvider(execution_mode, config)
        elif mode == 'usdt_market_neutral':
            from .usdt_market_neutral_data_provider import USDTMarketNeutralDataProvider
            return USDTMarketNeutralDataProvider(execution_mode, config)
        elif mode in ['ml_btc_directional', 'ml_usdt_directional']:
            # TODO: Create MLDirectionalDataProvider class
            from .ml_directional_data_provider import MLDirectionalDataProvider
            return MLDirectionalDataProvider(execution_mode, config)
        else:
            # Fallback to config-driven historical data provider (legacy)
            from .config_driven_historical_data_provider import ConfigDrivenHistoricalDataProvider
            return ConfigDrivenHistoricalDataProvider(execution_mode, config)
    