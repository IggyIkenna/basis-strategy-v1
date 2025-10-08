"""
Isolated data downloaders for external APIs.

This module contains individual downloaders for:
- LST pool data (GeckoTerminal - direct pool OHLCV)
- Spot pool data (GeckoTerminal - ETH/USDT direct pool OHLCV)
- AAVE lending protocol data (AaveScan Pro)
- On-chain gas price data (Alchemy JSON-RPC)
- Multi-venue funding rates (Bybit, OKX, Binance)
- Execution cost data (MEV simulation)

Note: General market data coordination is handled by scripts/orchestrators/fetch_market_data.py
"""

from .base_downloader import BaseDownloader
from .fetch_aave_data import AAVEDataDownloader
from .fetch_onchain_gas_data import OnChainGasDataDownloader
from .fetch_spot_pool_data import SpotDataDownloader

# Note: MultiVenueFundingDownloader doesn't inherit from BaseDownloader
# from .fetch_multi_venue_funding import MultiVenueFundingDownloader

__all__ = [
    "BaseDownloader",
    "AAVEDataDownloader", 
    "OnChainGasDataDownloader",
    "SpotDataDownloader"
]
