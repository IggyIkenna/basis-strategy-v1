"""
Data Provider Factory

Creates the appropriate data provider based on execution_mode and data_mode:
- execution_mode='backtest' + data_mode='csv': HistoricalDataProvider (loads from CSV files)
- execution_mode='backtest' + data_mode='db': DatabaseDataProvider (queries from database) - FUTURE IMPLEMENTATION
- execution_mode='live': LiveDataProvider (queries real-time APIs)

Architecture:
- HistoricalDataProvider: Mode-specific data loading from CSV files (on-demand)
- LiveDataProvider: Mode-specific real-time data from APIs
- DatabaseDataProvider: Mode-specific data from database (future)
"""

from typing import Dict, Any, Union, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def create_data_provider(
    data_dir: str,
    execution_mode: str,
    data_mode: str,
    config: Dict[str, Any],
    strategy_mode: Optional[str] = None,
    backtest_start_date: Optional[str] = None,
    backtest_end_date: Optional[str] = None
) -> Union['HistoricalDataProvider', 'LiveDataProvider', 'DatabaseDataProvider']:
    """
    Create the appropriate data provider based on execution_mode and data_mode.
    
    Args:
        data_dir: Path to data directory
        execution_mode: 'backtest' or 'live' (from BASIS_EXECUTION_MODE)
        data_mode: 'csv' or 'db' (from BASIS_DATA_MODE)
        config: Configuration dictionary
        strategy_mode: Strategy mode for mode-specific data loading
        backtest_start_date: Start date for backtest validation (YYYY-MM-DD format)
        backtest_end_date: End date for backtest validation (YYYY-MM-DD format)
        
    Returns:
        Appropriate data provider instance
        
    Architecture:
    - execution_mode='backtest' + data_mode='csv': HistoricalDataProvider with on-demand CSV loading
    - execution_mode='backtest' + data_mode='db': DatabaseDataProvider with on-demand DB queries (future)
    - execution_mode='live': LiveDataProvider with real-time API queries (data_mode ignored)
        
    # TODO-REFACTOR: MISSING VENUE FACTORY - 19_venue_based_execution_architecture.md
    # ISSUE: Data provider factory doesn't handle venue client initialization
    # Canonical: .cursor/tasks/19_venue_based_execution_architecture.md
    # Required Changes:
    #   1. Add venue client initialization based on strategy mode requirements
    #   2. Route to environment-specific credentials (dev/staging/prod)
    #   3. Initialize venue clients via VenueFactory pattern
    #   4. Handle venue selection logic based on strategy configuration
    #   5. Implement VenueClientFactory and EnvironmentManager
    # Reference: docs/DEPLOYMENT_GUIDE.md - Venue Client Initialization section
    # Reference: .cursor/tasks/19_venue_based_execution_architecture.md (canonical: docs/VENUE_ARCHITECTURE.md)
    # Status: PENDING
    """
    if execution_mode == 'backtest':
        if data_mode == 'csv':
            from .historical_data_provider import DataProvider as HistoricalDataProvider
            logger.info(f"Creating HistoricalDataProvider for mode: {strategy_mode or 'all_data'}")
            # HistoricalDataProvider now loads data on-demand, not at initialization
            return HistoricalDataProvider(
                data_dir=data_dir,
                mode=strategy_mode or 'all_data',
                config=config,
                backtest_start_date=backtest_start_date,
                backtest_end_date=backtest_end_date
            )
        elif data_mode == 'db':
            # TODO: [DATABASE_DATA_PROVIDER] - Implement DatabaseDataProvider for future database storage
            # Future Implementation:
            # from .database_data_provider import DatabaseDataProvider
            # logger.info(f"Creating DatabaseDataProvider for mode: {strategy_mode or 'dynamic'}")
            # return DatabaseDataProvider(config=config, mode=strategy_mode)
            raise NotImplementedError(
                "DatabaseDataProvider not yet implemented. "
                "This will be the future data provider for database-backed storage. "
                "Use data_mode='csv' for now."
            )
        else:
            raise ValueError(f"Invalid data_mode for backtest: {data_mode}. Must be 'csv' or 'db'")
    
    elif execution_mode == 'live':
        from .live_data_provider import LiveDataProvider
        logger.info(f"Creating LiveDataProvider for mode: {strategy_mode or 'dynamic'}")
        # data_mode is ignored for live mode (always uses real-time APIs)
        return LiveDataProvider(config=config, mode=strategy_mode)
    
    else:
        raise ValueError(f"Unknown execution_mode: {execution_mode}. Must be 'backtest' or 'live'")
