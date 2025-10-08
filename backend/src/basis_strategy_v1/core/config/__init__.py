"""Configuration module with canonical Pydantic models.

This module provides the SINGLE SOURCE OF TRUTH for all configuration validation.
Migrated from odum-basis-strategy-v1/src/config_schema.py with enhancements.

Contains:
- Complete canonical config schema (13 sections)  
- Parameter dependency validation
- User's precedence hierarchy implementation
- Config simplifications (target_ltv, basis_trade naming)
"""

from .config_models import (
    # Main configuration schema
    ConfigSchema,
    
    # Individual config sections (only used sections)
    VenueConfig,
    InfrastructureConfig,
    
    # Validation functions (venue-aware)
    load_and_validate_config,
    validate_config_dependencies,
    get_corrections_from_config,
    
    # Mode-aware validation
    validate_mode_specific_config,
    get_mode_specific_config,
    MODE_REQUIREMENTS,
)

# from .component_config import (  # Archived
#     # New component configuration
#     ComponentConfig,
#     ShareClassConfig,
#     RiskConfig,
#     create_component_config,
#     validate_component_config,
# )

# REMOVED: venue_constants imports - now handled by RiskCalculations in Risk Monitor

__all__ = [
    # Main schema
    "ConfigSchema",
    
    # Config sections (only used sections)
    "BacktestConfig",
    "StrategyConfig",
    "FeesConfig", 
    "RiskManagementConfig",
    "VenueConfig",
    "InfrastructureConfig",
    
    # Validation functions (venue-aware)
    "load_and_validate_config", 
    "validate_config_dependencies",
    "validate_position_size_against_capital",
    "get_corrections_from_config",
    
    # Mode-aware validation
    "validate_mode_specific_config",
    "get_mode_specific_config",
    "MODE_REQUIREMENTS",
    
    # New component configuration (archived)
    # "ComponentConfig",
    # "ShareClassConfig", 
    # "RiskConfig",
    # "create_component_config",
    # "validate_component_config",
    
    # REMOVED: venue constants - now handled by RiskCalculations in Risk Monitor
]
