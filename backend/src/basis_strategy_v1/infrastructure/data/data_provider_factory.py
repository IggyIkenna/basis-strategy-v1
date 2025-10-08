"""
Data Provider Factory

Creates the appropriate data provider based on startup_mode:
- backtest: HistoricalDataProvider (loads from CSV files)
- live: LiveDataProvider (queries real-time APIs)
"""

from typing import Dict, Any, Union, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def create_data_provider(
    data_dir: str,
    startup_mode: str,
    config: Dict[str, Any],
    strategy_mode: Optional[str] = None,
    backtest_start_date: Optional[str] = None,
    backtest_end_date: Optional[str] = None
) -> Union['HistoricalDataProvider', 'LiveDataProvider']:
    """
    Create the appropriate data provider based on startup_mode.
    
    Args:
        data_dir: Path to data directory
        startup_mode: 'backtest' or 'live'
        config: Configuration dictionary
        strategy_mode: Optional strategy mode (not used for historical data loading)
        backtest_start_date: Start date for backtest validation (YYYY-MM-DD format)
        backtest_end_date: End date for backtest validation (YYYY-MM-DD format)
        
    Returns:
        Appropriate data provider instance
    """
    if startup_mode == 'backtest':
        from .historical_data_provider import DataProvider as HistoricalDataProvider
        logger.info(f"Creating HistoricalDataProvider for startup data loading (all modes)")
        # Phase 2: Always load all data at startup for comprehensive backtesting
        return HistoricalDataProvider(
            data_dir=data_dir,
            mode='all_data',  # Always load all data at startup
            execution_mode=startup_mode,
            config=config,
            backtest_start_date=backtest_start_date,
            backtest_end_date=backtest_end_date
        )
    
    elif startup_mode == 'live':
        from .live_data_provider import LiveDataProvider
        logger.info(f"Creating LiveDataProvider for mode: {strategy_mode or 'dynamic'}")
        return LiveDataProvider(config=config, mode=strategy_mode)
    
    else:
        raise ValueError(f"Unknown startup_mode: {startup_mode}. Must be 'backtest' or 'live'")
