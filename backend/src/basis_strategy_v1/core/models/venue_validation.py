"""
Venue Configuration Validation Models

Pydantic models for validating venue configurations with instrument mappings.
Ensures venue-instrument relationships are correct and all instruments exist in registry.
"""

from pydantic import BaseModel, field_validator
from typing import List
from .venues import Venue
from .instruments import INSTRUMENTS


class VenueConfig(BaseModel):
    """Pydantic model for venue configuration with instrument validation"""
    venue: str
    type: str
    canonical_instruments: List[str] = []
    
    @field_validator('venue')
    @classmethod
    def validate_venue_exists(cls, v):
        """Validate that venue exists in venue registry"""
        if not Venue.validate_venue(v):
            raise ValueError(f"Unknown venue: {v}")
        return v
    
    @field_validator('canonical_instruments')
    @classmethod
    def validate_instruments_match_venue(cls, v, info):
        """Ensure all instruments actually belong to this venue"""
        venue_name = info.data.get('venue')
        if not venue_name:
            return v
        
        for instrument_key in v:
            # Parse instrument key
            parts = instrument_key.split(':')
            if len(parts) != 3:
                raise ValueError(f"Invalid instrument key format: {instrument_key}")
            
            venue, pos_type, symbol = parts
            
            # Verify venue matches
            if venue != venue_name:
                raise ValueError(
                    f"Instrument {instrument_key} venue '{venue}' doesn't match config venue '{venue_name}'"
                )
            
            # Verify instrument exists in registry
            if instrument_key not in INSTRUMENTS:
                raise ValueError(
                    f"Instrument {instrument_key} not found in instrument registry. "
                    f"Add to backend/src/basis_strategy_v1/core/models/instruments.py"
                )
        
        return v


def validate_venue_config(config_data: dict) -> VenueConfig:
    """
    Validate venue configuration data.
    
    Args:
        config_data: Dictionary containing venue configuration
        
    Returns:
        Validated VenueConfig instance
        
    Raises:
        ValueError: If venue or instruments are invalid
    """
    return VenueConfig(**config_data)


def validate_all_venue_configs(venue_configs: List[dict]) -> List[VenueConfig]:
    """
    Validate multiple venue configurations.
    
    Args:
        venue_configs: List of venue configuration dictionaries
        
    Returns:
        List of validated VenueConfig instances
        
    Raises:
        ValueError: If any venue or instruments are invalid
    """
    return [validate_venue_config(config) for config in venue_configs]
