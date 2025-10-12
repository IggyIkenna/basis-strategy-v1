"""
Centralized Utility Manager

Provides centralized utility methods for all components to ensure consistent
data access and prevent duplication of utility methods across components.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
"""

from typing import Dict, Any, Optional
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class UtilityManager:
    """Centralized utility methods for all components"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(UtilityManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any], data_provider):
        """
        Initialize utility manager.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
        """
        self.config = config
        self.data_provider = data_provider
        
        logger.info("UtilityManager initialized")
    
    def get_liquidity_index(self, token: str, timestamp: pd.Timestamp) -> float:
        """
        Get liquidity index for a token at a specific timestamp using canonical pattern.
        
        Args:
            token: Token symbol (e.g., 'aUSDT', 'aETH')
            timestamp: Timestamp for the liquidity index
            
        Returns:
            Liquidity index value
        """
        try:
            # Get data using canonical pattern
            data = self.data_provider.get_data(timestamp)
            aave_indexes = data['protocol_data']['aave_indexes']
            
            if token in aave_indexes:
                return aave_indexes[token]
            else:
                logger.warning(f"Liquidity index not found for {token}")
                return 1.0  # Default to 1.0 if not available
        except Exception as e:
            logger.error(f"Error getting liquidity index for {token}: {e}")
            return 1.0
    
    def get_market_price(self, token: str, currency: str, timestamp: pd.Timestamp) -> float:
        """
        Get market price for token in specified currency at timestamp using canonical pattern.
        
        Args:
            token: Token symbol (e.g., 'ETH', 'BTC', 'USDT')
            currency: Target currency (e.g., 'USDT', 'ETH')
            timestamp: Timestamp for the price
            
        Returns:
            Market price value
        """
        try:
            # Get data using canonical pattern
            data = self.data_provider.get_data(timestamp)
            prices = data['market_data']['prices']
            
            # Look for the specific token price
            if token in prices:
                return prices[token]
            else:
                logger.warning(f"Market price not found for {token}")
                return 1.0  # Default to 1.0 if not available
        except Exception as e:
            logger.error(f"Error getting market price for {token}/{currency}: {e}")
            return 1.0
    
    def convert_to_usdt(self, amount: float, token: str, timestamp: pd.Timestamp) -> float:
        """
        Convert token amount to USDT equivalent.
        
        Args:
            amount: Amount of token to convert
            token: Token symbol
            timestamp: Timestamp for the conversion
            
        Returns:
            USDT equivalent value
        """
        try:
            if token == 'USDT':
                return amount
            
            price = self.get_market_price(token, 'USDT', timestamp)
            return amount * price
        except Exception as e:
            logger.error(f"Error converting {amount} {token} to USDT: {e}")
            return 0.0
    
    def convert_from_liquidity_index(self, amount: float, token: str, timestamp: pd.Timestamp) -> float:
        """
        Convert from liquidity index (e.g., aUSDT to USDT).
        
        Args:
            amount: Amount of liquidity index token
            token: Liquidity index token symbol (e.g., 'aUSDT')
            timestamp: Timestamp for the conversion
            
        Returns:
            Underlying token amount
        """
        try:
            liquidity_index = self.get_liquidity_index(token, timestamp)
            return amount / liquidity_index
        except Exception as e:
            logger.error(f"Error converting from liquidity index {amount} {token}: {e}")
            return 0.0
    
    def convert_to_share_class(self, amount: float, token: str, share_class: str, timestamp: pd.Timestamp) -> float:
        """
        Convert token amount to share class currency equivalent.
        
        Args:
            amount: Amount of token to convert
            token: Token symbol
            share_class: Share class currency ('USDT' or 'ETH')
            timestamp: Timestamp for the conversion
            
        Returns:
            Share class equivalent value
        """
        try:
            if token == share_class:
                return amount
            
            price = self.get_market_price(token, share_class, timestamp)
            return amount * price
        except Exception as e:
            logger.error(f"Error converting {amount} {token} to {share_class}: {e}")
            return 0.0
    
    def get_share_class_from_mode(self, mode: str) -> str:
        """
        Get share class currency from mode configuration.
        
        Args:
            mode: Strategy mode name
            
        Returns:
            Share class currency ('USDT' or 'ETH')
        """
        try:
            # Get mode configuration
            mode_config = self.config.get('modes', {}).get(mode, {})
            share_class = mode_config.get('share_class', 'USDT')
            
            # Validate share class
            if share_class not in ['USDT', 'ETH']:
                logger.warning(f"Invalid share class {share_class} for mode {mode}, defaulting to USDT")
                return 'USDT'
            
            return share_class
        except Exception as e:
            logger.error(f"Error getting share class for mode {mode}: {e}")
            return 'USDT'
    
    def get_asset_from_mode(self, mode: str) -> str:
        """
        Get asset from mode configuration.
        
        Args:
            mode: Strategy mode name
            
        Returns:
            Asset symbol (e.g., 'ETH', 'BTC', 'USDT')
        """
        try:
            # Get mode configuration
            mode_config = self.config.get('modes', {}).get(mode, {})
            asset = mode_config.get('asset', 'ETH')
            
            return asset
        except Exception as e:
            logger.error(f"Error getting asset for mode {mode}: {e}")
            return 'ETH'
    
    def get_lst_type_from_mode(self, mode: str) -> Optional[str]:
        """
        Get LST type from mode configuration.
        
        Args:
            mode: Strategy mode name
            
        Returns:
            LST type (e.g., 'lido', 'etherfi') or None
        """
        try:
            # Get mode configuration
            mode_config = self.config.get('modes', {}).get(mode, {})
            lst_type = mode_config.get('lst_type')
            
            return lst_type
        except Exception as e:
            logger.error(f"Error getting LST type for mode {mode}: {e}")
            return None
    
    def get_hedge_allocation_from_mode(self, mode: str) -> Optional[float]:
        """
        Get hedge allocation from mode configuration.
        
        Args:
            mode: Strategy mode name
            
        Returns:
            Hedge allocation ratio or None
        """
        try:
            # Get mode configuration
            mode_config = self.config.get('modes', {}).get(mode, {})
            hedge_allocation = mode_config.get('hedge_allocation')
            
            return hedge_allocation
        except Exception as e:
            logger.error(f"Error getting hedge allocation for mode {mode}: {e}")
            return None
    
    def calculate_total_usdt_balance(self, balances: Dict[str, float], timestamp: pd.Timestamp) -> float:
        """
        Calculate total USDT equivalent balance from all token balances.
        
        Args:
            balances: Dictionary of token balances
            timestamp: Timestamp for price conversions
            
        Returns:
            Total USDT equivalent balance
        """
        try:
            total_usdt = 0.0
            
            for token, amount in balances.items():
                if amount > 0:
                    usdt_value = self.convert_to_usdt(amount, token, timestamp)
                    total_usdt += usdt_value
            
            return total_usdt
        except Exception as e:
            logger.error(f"Error calculating total USDT balance: {e}")
            return 0.0
    
    def calculate_total_share_class_balance(self, balances: Dict[str, float], share_class: str, timestamp: pd.Timestamp) -> float:
        """
        Calculate total share class equivalent balance from all token balances.
        
        Args:
            balances: Dictionary of token balances
            share_class: Share class currency ('USDT' or 'ETH')
            timestamp: Timestamp for price conversions
            
        Returns:
            Total share class equivalent balance
        """
        try:
            total_share_class = 0.0
            
            for token, amount in balances.items():
                if amount > 0:
                    share_class_value = self.convert_to_share_class(amount, token, share_class, timestamp)
                    total_share_class += share_class_value
            
            return total_share_class
        except Exception as e:
            logger.error(f"Error calculating total {share_class} balance: {e}")
            return 0.0
    
    def get_venue_configs_from_mode(self, mode: str) -> Dict[str, Any]:
        """
        Get venue configurations from mode configuration.
        
        Args:
            mode: Strategy mode name
            
        Returns:
            Dictionary of venue configurations
        """
        try:
            # Get mode configuration
            mode_config = self.config.get('modes', {}).get(mode, {})
            venue_configs = mode_config.get('venue_configs', {})
            
            return venue_configs
        except Exception as e:
            logger.error(f"Error getting venue configs for mode {mode}: {e}")
            return {}
    
    def get_data_requirements_from_mode(self, mode: str) -> Dict[str, Any]:
        """
        Get data requirements from mode configuration.
        
        Args:
            mode: Strategy mode name
            
        Returns:
            Dictionary of data requirements
        """
        try:
            # Get mode configuration
            mode_config = self.config.get('modes', {}).get(mode, {})
            data_requirements = mode_config.get('data_requirements', {})
            
            return data_requirements
        except Exception as e:
            logger.error(f"Error getting data requirements for mode {mode}: {e}")
            return {}
    
    def is_token_liquidity_index(self, token: str) -> bool:
        """
        Check if a token is a liquidity index token (e.g., aUSDT, aETH).
        
        Args:
            token: Token symbol
            
        Returns:
            True if token is a liquidity index token
        """
        try:
            # Common liquidity index token patterns
            liquidity_index_patterns = ['a', 'c', 'v']  # AAVE, Compound, Venus prefixes
            
            for pattern in liquidity_index_patterns:
                if token.startswith(pattern) and len(token) > 3:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking if {token} is liquidity index: {e}")
            return False
    
    def get_underlying_token_from_liquidity_index(self, liquidity_index_token: str) -> str:
        """
        Get underlying token from liquidity index token.
        
        Args:
            liquidity_index_token: Liquidity index token symbol (e.g., 'aUSDT')
            
        Returns:
            Underlying token symbol (e.g., 'USDT')
        """
        try:
            # Remove common liquidity index prefixes
            prefixes_to_remove = ['a', 'c', 'v']
            
            for prefix in prefixes_to_remove:
                if liquidity_index_token.startswith(prefix):
                    return liquidity_index_token[1:]  # Remove first character
            
            return liquidity_index_token
        except Exception as e:
            logger.error(f"Error getting underlying token from {liquidity_index_token}: {e}")
            return liquidity_index_token
    
    def calculate_total_positions(self, positions: Dict[str, float], timestamp: pd.Timestamp) -> Dict[str, float]:
        """
        Calculate total positions from all position data.
        
        Args:
            positions: Dictionary of position data
            timestamp: Timestamp for calculations
            
        Returns:
            Dictionary of total positions
        """
        try:
            # For now, just return the positions as-is
            # In real implementation, this would aggregate positions by token
            return positions
        except Exception as e:
            logger.error(f"Error calculating total positions: {e}")
            return {}
    
    def calculate_total_exposures(self, positions: Dict[str, float], timestamp: pd.Timestamp) -> Dict[str, float]:
        """
        Calculate total exposures from all position data.
        
        Args:
            positions: Dictionary of position data
            timestamp: Timestamp for calculations
            
        Returns:
            Dictionary of total exposures
        """
        try:
            # For now, just return the positions as exposures
            # In real implementation, this would calculate exposures differently
            return positions
        except Exception as e:
            logger.error(f"Error calculating total exposures: {e}")
            return {}
