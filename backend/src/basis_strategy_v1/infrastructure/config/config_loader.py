"""
Centralized Configuration Loader

TODO-REFACTOR: CONFIGURATION LOADING ARCHITECTURE VIOLATION - See docs/REFERENCE_ARCHITECTURE_CANONICAL.md
ISSUE: This component may violate configuration loading architecture requirements:

1. CONFIGURATION ARCHITECTURE REQUIREMENTS:
   - Proper YAML-based configuration loading
   - Environment variable integration
   - Configuration hierarchy validation
   - Fail-fast configuration validation

2. REQUIRED VERIFICATION:
   - Verify proper YAML configuration loading
   - Check environment variable integration
   - Validate configuration hierarchy
   - Ensure fail-fast validation

3. CANONICAL SOURCE:
   - docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Configuration Architecture
   - YAML-only configuration system

Loads all configuration from a single place and ensures consistency.
Config is loaded once at startup and cached. Environment variables
are loaded once and cached. Changes require a full system restart.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from functools import lru_cache
import logging

from .config_manager import _BASE_DIR, get_environment, load_mode_config, load_venue_config, load_share_class_config, load_scenario_config
from .config_validator import validate_configuration, ValidationResult

logger = logging.getLogger(__name__)

# Error codes for Config Loader
ERROR_CODES = {
    'LOADER-001': 'Configuration loading failed',
    'LOADER-002': 'Configuration file not found',
    'LOADER-003': 'Configuration parsing error',
    'LOADER-004': 'Configuration validation failed',
    'LOADER-005': 'Environment variable loading failed',
    'LOADER-006': 'Configuration cache initialization failed',
    'LOADER-007': 'Configuration merge failed',
    'LOADER-008': 'Configuration reload failed',
    'LOADER-009': 'Configuration health check failed',
    'LOADER-010': 'Configuration summary generation failed'
}


class ConfigLoader:
    """Centralized configuration loader with caching."""
    
    def __init__(self):
        self.base_dir = _BASE_DIR
        self.environment = get_environment()
        self._config_cache: Dict[str, Any] = {}
        self._env_cache: Dict[str, str] = {}
        self._validation_result: Optional[ValidationResult] = None
        
        # Load and validate configuration
        self._load_all_config()
        self._validate_config()
    
    def _load_all_config(self):
        """Load all configuration files and environment variables."""
        logger.info(f"🔄 Loading configuration for {self.environment} environment...")
        
        # Load base configuration
        self._config_cache['base'] = self._load_base_config()
        
        # Load mode configurations
        self._config_cache['modes'] = self._load_all_mode_configs()
        
        # Load venue configurations
        self._config_cache['venues'] = self._load_all_venue_configs()
        
        # Load share class configurations
        self._config_cache['share_classes'] = self._load_all_share_class_configs()
        
        # Load scenario configurations
        self._config_cache['scenarios'] = self._load_all_scenario_configs()
        
        # Load environment variables
        self._env_cache = self._load_environment_variables()
        
        logger.info("✅ Configuration loaded successfully")
    
    def _validate_config(self):
        """Validate the loaded configuration."""
        logger.info("🔍 Validating loaded configuration...")
        
        self._validation_result = validate_configuration()
        
        if not self._validation_result.is_valid:
            error_msg = f"Configuration validation failed: {', '.join(self._validation_result.errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if self._validation_result.warnings:
            for warning in self._validation_result.warnings:
                logger.warning(f"Configuration warning: {warning}")
    
    def _load_base_config(self) -> Dict[str, Any]:
        """Load base configuration from JSON files with environment-specific overrides."""
        # TODO: [CONFIG_SEPARATION_OF_CONCERNS] - Remove JSON configuration loading
        # Current Issue: Config loader still loads JSON files that should be removed per separation of concerns
        # Required Changes:
        #   1. Remove JSON configuration loading (default.json, {environment}.json, local.json)
        #   2. Database configuration should be in env.unified (deployment-specific)
        #   3. Strategy/venue configuration should be in YAML files (static configs)
        #   4. Environment variables should handle deployment-specific overrides
        # Reference: docs/specs/CONFIGURATION.md - Separation of Concerns section
        # Reference: docs/ENVIRONMENT_VARIABLES.md - Configuration Separation of Concerns section
        # Status: PENDING
        
        config = {}
        
        # Load default.json (base configuration)
        default_path = self.base_dir / "configs" / "default.json"
        if default_path.exists():
            with open(default_path, 'r') as f:
                config.update(json.load(f))
        
        # Load environment-specific config (staging.json, production.json, etc.)
        env_config_path = self.base_dir / "configs" / f"{self.environment}.json"
        if env_config_path.exists():
            with open(env_config_path, 'r') as f:
                env_config = json.load(f)
                config = self._deep_merge(config, env_config)
        
        # Load local.json (local development overrides - only for dev environment)
        if self.environment == 'dev':
            local_path = self.base_dir / "configs" / "local.json"
            if local_path.exists():
                with open(local_path, 'r') as f:
                    local_config = json.load(f)
                    config = self._deep_merge(config, local_config)
        
        return config
    
    def _load_all_mode_configs(self) -> Dict[str, Any]:
        """Load all mode configurations."""
        modes = {}
        modes_dir = self.base_dir / "configs" / "modes"
        
        if modes_dir.exists():
            for mode_file in modes_dir.glob("*.yaml"):
                try:
                    with open(mode_file, 'r') as f:
                        mode_config = yaml.safe_load(f)
                        modes[mode_file.stem] = mode_config
                except Exception as e:
                    logger.error(f"Failed to load mode config {mode_file}: {e}")
        
        return modes
    
    def _load_all_venue_configs(self) -> Dict[str, Any]:
        """Load all venue configurations."""
        venues = {}
        venues_dir = self.base_dir / "configs" / "venues"
        
        if venues_dir.exists():
            for venue_file in venues_dir.glob("*.yaml"):
                try:
                    with open(venue_file, 'r') as f:
                        venue_config = yaml.safe_load(f)
                        venues[venue_file.stem] = venue_config
                except Exception as e:
                    logger.error(f"Failed to load venue config {venue_file}: {e}")
        
        return venues
    
    def _load_all_share_class_configs(self) -> Dict[str, Any]:
        """Load all share class configurations."""
        share_classes = {}
        share_classes_dir = self.base_dir / "configs" / "share_classes"
        
        if share_classes_dir.exists():
            for share_class_file in share_classes_dir.glob("*.yaml"):
                try:
                    with open(share_class_file, 'r') as f:
                        share_class_config = yaml.safe_load(f)
                        share_classes[share_class_file.stem] = share_class_config
                except Exception as e:
                    logger.error(f"Failed to load share class config {share_class_file}: {e}")
        
        return share_classes
    
    def _load_all_scenario_configs(self) -> Dict[str, Any]:
        """Load all scenario configurations."""
        scenarios = {}
        scenarios_dir = self.base_dir / "configs" / "scenarios"
        
        # Load backtest scenarios
        backtest_dir = scenarios_dir / "backtest"
        if backtest_dir.exists():
            scenarios['backtest'] = {}
            for scenario_file in backtest_dir.glob("*.yaml"):
                try:
                    with open(scenario_file, 'r') as f:
                        scenario_config = yaml.safe_load(f)
                        scenarios['backtest'][scenario_file.stem] = scenario_config
                except Exception as e:
                    logger.error(f"Failed to load backtest scenario {scenario_file}: {e}")
        
        # Load live scenarios
        live_dir = scenarios_dir / "live"
        if live_dir.exists():
            scenarios['live'] = {}
            for scenario_file in live_dir.glob("*.yaml"):
                try:
                    with open(scenario_file, 'r') as f:
                        scenario_config = yaml.safe_load(f)
                        scenarios['live'][scenario_file.stem] = scenario_config
                except Exception as e:
                    logger.error(f"Failed to load live scenario {scenario_file}: {e}")
        
        return scenarios
    
    def _load_environment_variables(self) -> Dict[str, str]:
        """Load all BASIS_* environment variables."""
        env_vars = {}
        
        for key, value in os.environ.items():
            if key.startswith('BASIS_'):
                env_vars[key] = value
        
        return env_vars
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    # Public API methods
    
    def get_base_config(self) -> Dict[str, Any]:
        """Get base configuration."""
        return self._config_cache.get('base', {})
    
    def get_mode_config(self, mode: str) -> Dict[str, Any]:
        """Get mode configuration."""
        return self._config_cache.get('modes', {}).get(mode, {})
    
    def get_venue_config(self, venue: str) -> Dict[str, Any]:
        """Get venue configuration."""
        return self._config_cache.get('venues', {}).get(venue, {})
    
    def get_share_class_config(self, share_class: str) -> Dict[str, Any]:
        """Get share class configuration."""
        return self._config_cache.get('share_classes', {}).get(share_class, {})
    
    def get_scenario_config(self, scenario: str, scenario_type: str = 'backtest') -> Dict[str, Any]:
        """Get scenario configuration."""
        return self._config_cache.get('scenarios', {}).get(scenario_type, {}).get(scenario, {})
    
    def get_all_mode_configs(self) -> Dict[str, Any]:
        """Get all mode configurations."""
        return self._config_cache.get('modes', {})
    
    def get_all_venue_configs(self) -> Dict[str, Any]:
        """Get all venue configurations."""
        return self._config_cache.get('venues', {})
    
    def get_all_scenario_configs(self) -> Dict[str, Any]:
        """Get all scenario configurations."""
        return self._config_cache.get('scenarios', {})
    
    def get_environment_variable(self, key: str) -> Optional[str]:
        """Get environment variable."""
        return self._env_cache.get(key)
    
    def get_environment_variables(self, prefix: str = 'BASIS_') -> Dict[str, str]:
        """Get all environment variables with prefix."""
        return {k: v for k, v in self._env_cache.items() if k.startswith(prefix)}
    
    def get_complete_config(self, mode: str = None, venue: str = None, scenario: str = None) -> Dict[str, Any]:
        """Get complete configuration by merging all relevant configs."""
        config = self.get_base_config().copy()
        
        if mode:
            mode_config = self.get_mode_config(mode)
            config = self._deep_merge(config, mode_config)
        
        if venue:
            venue_config = self.get_venue_config(venue)
            config = self._deep_merge(config, venue_config)
        
        if scenario:
            scenario_config = self.get_scenario_config(scenario)
            config = self._deep_merge(config, scenario_config)
        
        return config
    
    def get_validation_result(self) -> Optional[ValidationResult]:
        """Get the validation result."""
        return self._validation_result
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the loaded configuration."""
        if self._validation_result:
            return self._validation_result.config_summary
        return {}
    
    def is_healthy(self) -> bool:
        """Check if configuration is healthy."""
        return self._validation_result is not None and self._validation_result.is_valid
    
    def reload_config(self):
        """Reload configuration (requires restart for environment variables)."""
        logger.warning("🔄 Reloading configuration...")
        logger.warning("⚠️ Environment variables will not be reloaded - restart required")
        
        # TODO-REFACTOR: STATE CLEARING - 16_clean_component_architecture_requirements.md
        # ISSUE: Cache clearing may indicate architectural problem
        # Canonical: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Clean Component Architecture
        # Fix: Design components to be naturally clean without needing state clearing
        # Status: PENDING
        self._config_cache.clear()
        self._load_all_config()
        self._validate_config()
        
        logger.info("✅ Configuration reloaded successfully")


# Global config loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """Get the global configuration loader instance."""
    global _config_loader
    
    if _config_loader is None:
        _config_loader = ConfigLoader()
    
    return _config_loader


def get_config(mode: str = None, venue: str = None, scenario: str = None) -> Dict[str, Any]:
    """Get configuration using the global loader."""
    loader = get_config_loader()
    return loader.get_complete_config(mode, venue, scenario)


def get_environment_config() -> Dict[str, str]:
    """Get environment variables using the global loader."""
    loader = get_config_loader()
    return loader.get_environment_variables()


def is_config_healthy() -> bool:
    """Check if configuration is healthy."""
    loader = get_config_loader()
    return loader.is_healthy()


def reload_config():
    """Reload configuration."""
    loader = get_config_loader()
    loader.reload_config()
