"""
Market Data Utilities

Centralized utility class for accessing market data (prices, rates, indices) 
across all components. Provides a consistent interface for:

- Liquidity index lookups (AAVE tokens)
- Price conversions (ETH, BTC, USDT)
- Rate lookups (funding rates, APYs)
- Gas price lookups

All methods use the current event loop timestamp and global data provider state.
"""

import pandas as pd
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MarketDataUtils:
    """
    Centralized utility for market data access across all components.
    
    Provides consistent methods for accessing:
    - Liquidity indices (AAVE tokens)
    - Price data (ETH, BTC, USDT)
    - Rate data (funding rates, APYs)
    - Gas prices
    
    # TODO-REFACTOR: MISSING CENTRALIZED UTILITY MANAGER - See docs/REFERENCE_ARCHITECTURE_CANONICAL.md
    # ISSUE: This class should be integrated into centralized UtilityManager pattern
    # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Mode-Specific PnL Calculator
    # Fix: Create centralized UtilityManager and integrate this class into it
    # Status: PENDING
    """
    
    def __init__(self, data_provider=None):
        """
        Initialize MarketDataUtils with data provider.
        
        Args:
            data_provider: Data provider instance for accessing market data
        """
        self.data_provider = data_provider
    
    def get_liquidity_index(self, asset: str, timestamp: pd.Timestamp) -> float:
        """
        Get AAVE liquidity index for an asset at a specific timestamp.
        
        Args:
            asset: Asset symbol (e.g., 'USDT', 'WETH', 'weETH')
            timestamp: Timestamp to get liquidity index for
            
        Returns:
            Liquidity index value
            
        Raises:
            ValueError: If data provider is not available or asset not found
        """
        if not self.data_provider:
            raise ValueError("Data provider not available for liquidity index lookup")
        
        try:
            # Get liquidity index from data provider using get_aave_index method
            liquidity_index = self.data_provider.get_aave_index(
                asset=asset,
                index_type='liquidity',
                timestamp=timestamp
            )
            
            logger.debug(f"Retrieved {asset} liquidity index: {liquidity_index:.6f} for timestamp {timestamp}")
            return liquidity_index
            
        except Exception as e:
            logger.error(f"Error getting liquidity index for {asset} at {timestamp}: {e}")
            raise ValueError(f"Failed to get liquidity index for {asset}: {e}")
    
    def get_asset_price(self, asset: str, market_data: Dict[str, Any]) -> float:
        """
        Get asset price in USD from market data.
        
        Args:
            asset: Asset symbol (e.g., 'ETH', 'BTC', 'USDT')
            market_data: Market data dictionary
            
        Returns:
            Asset price in USD
            
        Raises:
            ValueError: If price not found in market data
        """
        price_key = f"{asset.lower()}_usd_price"
        
        if price_key not in market_data:
            raise ValueError(f"Price not found for {asset} in market data. Available keys: {list(market_data.keys())}")
        
        price = market_data[price_key]
        if price is None:
            raise ValueError(f"Price is None for {asset}")
        
        return float(price)
    
    def get_eth_price(self, market_data: Dict[str, Any]) -> float:
        """Get ETH price in USD."""
        return self.get_asset_price('ETH', market_data)
    
    def get_btc_price(self, market_data: Dict[str, Any]) -> float:
        """Get BTC price in USD."""
        return self.get_asset_price('BTC', market_data)
    
    def get_usdt_price(self, market_data: Dict[str, Any]) -> float:
        """Get USDT price in USD (should be ~1.0)."""
        return self.get_asset_price('USDT', market_data)
    
    def get_gas_price(self, market_data: Dict[str, Any], default: float = 20.0) -> float:
        # TODO-REFACTOR: HARDCODED VALUES - 06_architecture_compliance_rules.md
        # ISSUE: Hardcoded default gas price value
        # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - No Hardcoded Values
        # Fix: Load default gas price from config YAML instead of hardcoding
        # Status: PENDING
        """
        Get gas price in Gwei from market data.
        
        Args:
            market_data: Market data dictionary
            default: Default gas price if not found
            
        Returns:
            Gas price in Gwei
        """
        return float(market_data.get('gas_price_gwei', default))
    
    def get_funding_rate(self, venue: str, market_data: Dict[str, Any]) -> float:
        """
        Get funding rate for a venue from market data.
        
        Args:
            venue: Venue name (e.g., 'binance', 'bybit', 'okx')
            market_data: Market data dictionary
            
        Returns:
            Funding rate as decimal (e.g., 0.0001 for 0.01%)
        """
        rate_key = f"{venue.lower()}_funding_rate"
        
        if rate_key not in market_data:
            raise ValueError(f"Funding rate not found for {venue} in market data")
        
        rate = market_data[rate_key]
        if rate is None:
            raise ValueError(f"Funding rate is None for {venue}")
        
        return float(rate)
    
    def get_supply_apy(self, asset: str, market_data: Dict[str, Any]) -> float:
        """
        Get supply APY for an asset from market data.
        
        Args:
            asset: Asset symbol (e.g., 'USDT', 'WETH', 'weETH')
            market_data: Market data dictionary
            
        Returns:
            Supply APY as decimal (e.g., 0.05 for 5%)
        """
        apy_key = f"{asset.lower()}_supply_apy"
        
        if apy_key not in market_data:
            raise ValueError(f"Supply APY not found for {asset} in market data")
        
        apy = market_data[apy_key]
        if apy is None:
            return 0.0  # Default to 0% if not available
        
        return float(apy)
    
    def get_borrow_apy(self, asset: str, market_data: Dict[str, Any]) -> float:
        """
        Get borrow APY for an asset from market data.
        
        Args:
            asset: Asset symbol (e.g., 'USDT', 'WETH', 'weETH')
            market_data: Market data dictionary
            
        Returns:
            Borrow APY as decimal (e.g., 0.05 for 5%)
        """
        apy_key = f"{asset.lower()}_borrow_apy"
        
        if apy_key not in market_data:
            raise ValueError(f"Borrow APY not found for {asset} in market data")
        
        apy = market_data[apy_key]
        if apy is None:
            return 0.0  # Default to 0% if not available
        
        return float(apy)
    
    def get_liquidity_index_from_market_data(self, asset: str, market_data: Dict[str, Any]) -> float:
        """
        Get liquidity index from market data (fallback method).
        
        This method provides backward compatibility for components that
        currently get liquidity index from market_data instead of data provider.
        
        Args:
            asset: Asset symbol (e.g., 'USDT', 'WETH', 'weETH')
            market_data: Market data dictionary
            
        Returns:
            Liquidity index value
        """
        index_key = f"{asset.lower()}_liquidity_index"
        
        if index_key not in market_data:
            raise ValueError(f"Liquidity index not found for {asset} in market data")
        
        index = market_data[index_key]
        if index is None:
            raise ValueError(f"Liquidity index is None for {asset}")
        
        return float(index)
    
    def convert_aave_token_to_underlying(self, aave_balance: float, asset: str, 
                                       timestamp: pd.Timestamp, market_data: Dict[str, Any]) -> float:
        """
        Convert AAVE token balance to underlying asset balance using liquidity index.
        
        Args:
            aave_balance: Balance of AAVE token (e.g., aUSDT, aWETH)
            asset: Underlying asset symbol (e.g., 'USDT', 'WETH')
            timestamp: Current timestamp
            market_data: Market data dictionary (for fallback)
            
        Returns:
            Underlying asset balance
        """
        try:
            # Try to get liquidity index from data provider first
            liquidity_index = self.get_liquidity_index(asset, timestamp)
        except (ValueError, Exception):
            # Fallback to market_data if data provider fails
            logger.warning(f"Falling back to market_data for {asset} liquidity index")
            liquidity_index = self.get_liquidity_index_from_market_data(asset, market_data)
        
        underlying_balance = aave_balance * liquidity_index
        logger.debug(f"Converted {aave_balance} {asset} AAVE token to {underlying_balance} underlying {asset}")
        
        return underlying_balance


# Global instance for shared usage across components
_global_market_data_utils = None


def get_market_data_utils(data_provider=None) -> MarketDataUtils:
    """
    Get global MarketDataUtils instance.
    
    Args:
        data_provider: Data provider instance (optional, for initialization)
        
    Returns:
        MarketDataUtils instance
    """
    global _global_market_data_utils
    
    if _global_market_data_utils is None:
        _global_market_data_utils = MarketDataUtils(data_provider)
    elif data_provider is not None and _global_market_data_utils.data_provider is None:
        # Update data provider if it was None
        _global_market_data_utils.data_provider = data_provider
    
    return _global_market_data_utils


def set_global_data_provider(data_provider):
    """
    Set the global data provider for MarketDataUtils.
    
    Args:
        data_provider: Data provider instance
    """
    global _global_market_data_utils
    
    if _global_market_data_utils is None:
        _global_market_data_utils = MarketDataUtils(data_provider)
    else:
        _global_market_data_utils.data_provider = data_provider