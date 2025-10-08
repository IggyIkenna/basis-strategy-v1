"""
Orchestration scripts that coordinate multiple downloaders/processors.

This module contains high-level scripts that:
- Coordinate multiple data sources
- Manage complex download workflows
- Provide unified interfaces for data collection

Scripts:
- download_all.py: Master orchestrator for all data downloads
- fetch_market_data.py: Multi-client market data orchestrator (Binance + derivatives)
- fetch_pool_data.py: CoinGecko pool data orchestrator (LST + spot pools)
"""

from .download_all import MasterDataDownloader
from .fetch_pool_data import PoolDataOrchestrator

__all__ = [
    "MasterDataDownloader",
    "PoolDataOrchestrator"
]

