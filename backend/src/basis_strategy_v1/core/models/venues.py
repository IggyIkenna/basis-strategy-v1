# Venue Constants
"""
Canonical venue identifiers matching configs/venues/*.yaml

This module provides type-safe venue constants to prevent hardcoded venue strings
throughout the codebase and ensure consistency with venue configuration files.
"""

from enum import Enum
from typing import List


class Venue(str, Enum):
    """Canonical venue identifiers matching configs/venues/*.yaml"""
    
    # CEX Venues
    BINANCE = "binance"
    BYBIT = "bybit"
    OKX = "okx"
    
    # DeFi Protocols
    AAVE_V3 = "aave_v3"
    ETHERFI = "etherfi"
    LIDO = "lido"
    MORPHO = "morpho"
    INSTADAPP = "instadapp"
    UNISWAP = "uniswap"
    
    # Infrastructure
    WALLET = "wallet"
    ALCHEMY = "alchemy"
    
    @classmethod
    def is_cex(cls, venue: str) -> bool:
        """Check if venue is a centralized exchange"""
        return venue in [cls.BINANCE, cls.BYBIT, cls.OKX]
    
    @classmethod
    def is_defi(cls, venue: str) -> bool:
        """Check if venue is a DeFi protocol"""
        return venue in [cls.AAVE_V3, cls.ETHERFI, cls.LIDO, cls.MORPHO]
    
    @classmethod
    def is_infrastructure(cls, venue: str) -> bool:
        """Check if venue is infrastructure (wallet, alchemy)"""
        return venue in [cls.WALLET, cls.ALCHEMY]
    
    @classmethod
    def get_cex_venues(cls) -> List[str]:
        """Get all CEX venue identifiers"""
        return [cls.BINANCE, cls.BYBIT, cls.OKX]
    
    @classmethod
    def get_defi_venues(cls) -> List[str]:
        """Get all DeFi venue identifiers"""
        return [cls.AAVE_V3, cls.ETHERFI, cls.LIDO, cls.MORPHO]
    
    @classmethod
    def get_all_venues(cls) -> List[str]:
        """Get all venue identifiers"""
        return [venue.value for venue in cls]
    
    @classmethod
    def validate_venue(cls, venue: str) -> bool:
        """Validate that venue exists in registry"""
        return venue in cls.get_all_venues()
    
    @classmethod
    def get_venue_type(cls, venue: str) -> str:
        """Get venue type (cex, defi, infrastructure)"""
        if cls.is_cex(venue):
            return "cex"
        elif cls.is_defi(venue):
            return "defi"
        elif cls.is_infrastructure(venue):
            return "infrastructure"
        else:
            raise ValueError(f"Unknown venue type for: {venue}")

    @classmethod
    def validate_venue_instrument_pair(cls, venue: str, instrument_key: str) -> bool:
        """
        Validate venue can provide this instrument.
        
        Args:
            venue: Venue name (e.g., 'binance', 'aave_v3')
            instrument_key: Position key (e.g., 'binance:Perp:BTCUSDT')
        
        Returns:
            True if venue-instrument pair is valid
        """
        if not cls.validate_venue(venue):
            return False
        
        # Check if instrument key matches venue
        venue_from_key, _, _ = instrument_key.split(':')
        if venue_from_key != venue:
            return False
        
        # TODO: Load venue config and check canonical_instruments
        # For now, basic validation
        return True


# Convenience constants for common venue groups
CEX_VENUES = Venue.get_cex_venues()
DEFI_VENUES = Venue.get_defi_venues()
ALL_VENUES = Venue.get_all_venues()
