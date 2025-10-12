"""
Unified Configuration Manager

Single source of truth for all configuration operations:
- Environment variable loading (FAIL FAST - no defaults)
- Configuration file loading and merging
- Strategy discovery and validation
- Configuration caching and health checking
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from functools import lru_cache
import logging

# from .config_models import ConfigSchema, load_and_validate_config
# from .config_validator import validate_configuration, ValidationResult
# Health check functions removed - now handled by unified health manager
# from ..monitoring.logging import log_structured_error

logger = logging.getLogger(__name__)

# Error codes for Config Manager
ERROR_CODES = {
    'CONFIG-MGR-001': 'Configuration loading failed',
    'CONFIG-MGR-002': 'Environment variable not set',
    'CONFIG-MGR-003': 'Configuration file not found',
    'CONFIG-MGR-004': 'Configuration parsing error',
    'CONFIG-MGR-005': 'Configuration validation failed',
    'CONFIG-MGR-006': 'Strategy not found',
    'CONFIG-MGR-007': 'Configuration merge failed',
    'CONFIG-MGR-008': 'Configuration health check failed'
}


class ConfigManager:
    """Unified configuration manager with fail-fast policy.
    
    TODO-REFACTOR: ENVIRONMENT VARIABLE INTEGRATION VIOLATION - See docs/VENUE_ARCHITECTURE.md
    ISSUE: This component has environment variable naming inconsistencies:
    
    1. ENVIRONMENT VARIABLE NAMING VIOLATIONS:
       - Uses BASIS_DEPLOYMENT_MODE but canonical docs reference BASIS_ENVIRONMENT
       - Creates confusion between deployment style vs environment
       - Missing BASIS_EXECUTION_MODE integration
    
    2. REQUIRED ARCHITECTURE (per 19_venue_based_execution_architecture.md):
       - Should use THREE DISTINCT VARIABLES:
         * BASIS_DEPLOYMENT_MODE=local|docker (port/host forwarding and dependency injection)
         * BASIS_ENVIRONMENT=dev|staging|production (dtestnet vs mainnet APIs)
         * BASIS_DATA_MODE=csv|db (data source: CSV vs DB)
         * BASIS_EXECUTION_MODE=backtest|live (venue execution: simulated vs real)
    
    3. CURRENT VIOLATIONS:
       - Inconsistent environment variable usage
       - Missing BASIS_EXECUTION_MODE integration
       - Confusion between deployment mode and environment
    
    4. REQUIRED FIX:
       - Clarify BASIS_DEPLOYMENT_MODE vs BASIS_ENVIRONMENT distinction
       - Add BASIS_EXECUTION_MODE integration
       - Ensure consistent environment variable usage across all components
    
    CURRENT STATE: This component needs environment variable naming clarification.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent.parent.parent.parent
        self.config_cache: Dict[str, Any] = {}
        self._validation_result: Optional[ValidationResult] = None
        
        # Load and validate configuration
        self._load_all_config()
        self._validate_config()
        
        # Config manager health now handled by unified health manager
    
    def _load_all_config(self):
        """Load all configuration files and environment variables."""
        logger.info("🔄 Loading configuration...")
        
        # Load base configuration
        self.config_cache['base'] = self._load_base_config()
        
        # Load mode configurations
        self.config_cache['modes'] = self._load_all_mode_configs()
        
        # Load venue configurations
        self.config_cache['venues'] = self._load_all_venue_configs()
        
        # Load share class configurations
        self.config_cache['share_classes'] = self._load_all_share_class_configs()
        
        # Load environment variables (FAIL FAST)
        self.config_cache['env'] = self._load_environment_variables()
        
        logger.info("✅ Configuration loaded successfully")
    
    def _load_environment_variables(self) -> Dict[str, str]:
        """Load environment variables with FAIL FAST policy."""
        # First load from env.unified
        self._load_env_file(self.base_dir / "env.unified")
        
        # Then load override files based on BASIS_ENVIRONMENT. If not set FAIL FAST
        environment = os.getenv('BASIS_ENVIRONMENT')
        if not environment:
            logger.error("CONFIG-MGR-002: REQUIRED environment variable not set: BASIS_ENVIRONMENT")
            raise ValueError("REQUIRED environment variable not set: BASIS_ENVIRONMENT")
        
        # Load environment-specific override file with FAIL FAST validation
        env_file = None
        if environment == 'dev':
            env_file = self.base_dir / "env.dev"
        elif environment == 'staging':
            env_file = self.base_dir / "env.staging"
        elif environment == 'prod':
            env_file = self.base_dir / "env.prod"
        else:
            logger.error(f"CONFIG-MGR-002: Unknown environment: {environment}. Must be dev, staging, or prod")
            raise ValueError(f"Unknown environment: {environment}. Must be dev, staging, or prod")
        
        if not env_file.exists():
            logger.error(f"CONFIG-MGR-003: Environment file not found: {env_file}")
            raise FileNotFoundError(f"Environment file not found: {env_file}")
        
        if not os.access(env_file, os.R_OK):
            logger.error(f"CONFIG-MGR-003: Environment file not readable: {env_file}")
            raise PermissionError(f"Environment file not readable: {env_file}")
        
        self._load_env_file(env_file)
        
        env_vars = {}
        required_vars = [
            'BASIS_ENVIRONMENT',
            'BASIS_DEPLOYMENT_MODE', 
            'BASIS_DEPLOYMENT_MACHINE',
            'BASIS_DATA_DIR',
            'BASIS_DATA_MODE',
            'BASIS_RESULTS_DIR',
            'BASIS_DEBUG',
            'BASIS_LOG_LEVEL',
            'BASIS_EXECUTION_MODE',
            'BASIS_DATA_START_DATE',
            'BASIS_DATA_END_DATE',
            'HEALTH_CHECK_INTERVAL',
            'HEALTH_CHECK_ENDPOINT',
            'BASIS_API_PORT',
            'BASIS_API_HOST',
            'BASIS_API_CORS_ORIGINS'
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                logger.error(f"CONFIG-MGR-002: REQUIRED environment variable not set: {var}")
                raise ValueError(f"REQUIRED environment variable not set: {var}")
            
            # Validate variable types and formats
            validated_value = self._validate_environment_variable(var, value)
            env_vars[var] = validated_value
        
        # Check execution mode for credential requirements
        execution_mode = env_vars.get('BASIS_EXECUTION_MODE', 'backtest')
        if execution_mode == 'backtest':
            logger.info("Backtest mode: Venue credentials not required - execution is simulated")
        else:
            logger.info("Live mode: Venue credentials required for real API access")
        
        # Load optional variables
        for key, value in os.environ.items():
            if key.startswith('BASIS_') and key not in env_vars:
                env_vars[key] = value
        
        return env_vars
    
    def _load_env_file(self, file_path: Path):
        """Load environment variables from a file."""
        if not file_path.exists():
            return
        
        logger.info(f"Loading environment variables from {file_path}")
        
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if value:  # Only set non-empty values
                        os.environ[key] = value
    
    def _validate_environment_variable(self, var_name: str, value: str) -> str:
        """Validate environment variable type and format."""
        # Boolean validation
        if var_name in ['BASIS_DEBUG', 'DATA_VALIDATION_STRICT']:
            if value.lower() not in ['true', 'false']:
                logger.error(f"CONFIG-MGR-004: Invalid boolean value for {var_name}: {value}")
                raise ValueError(f"Invalid boolean value for {var_name}: {value}. Must be 'true' or 'false'")
            return value.lower()
        
        # Integer validation
        if var_name in ['BASIS_API_PORT', 'HTTP_PORT', 'HTTPS_PORT', 'DATA_LOAD_TIMEOUT', 'DATA_CACHE_SIZE', 
                       'STRATEGY_MANAGER_TIMEOUT', 'STRATEGY_MANAGER_MAX_RETRIES', 'STRATEGY_FACTORY_TIMEOUT', 
                       'STRATEGY_FACTORY_MAX_RETRIES', 'BASIS_LIVE_TRADING__HEARTBEAT_TIMEOUT_SECONDS']:
            try:
                int(value)
            except ValueError:
                logger.error(f"CONFIG-MGR-004: Invalid integer value for {var_name}: {value}")
                raise ValueError(f"Invalid integer value for {var_name}: {value}")
            return value
        
        # Float validation
        if var_name in ['BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD', 'BASIS_LIVE_TRADING__EMERGENCY_STOP_LOSS_PCT']:
            try:
                float(value)
            except ValueError:
                logger.error(f"CONFIG-MGR-004: Invalid float value for {var_name}: {value}")
                raise ValueError(f"Invalid float value for {var_name}: {value}")
            return value
        
        # Enum validation
        if var_name == 'BASIS_ENVIRONMENT':
            if value not in ['dev', 'staging', 'prod']:
                logger.error(f"CONFIG-MGR-004: Invalid environment value for {var_name}: {value}")
                raise ValueError(f"Invalid environment value for {var_name}: {value}. Must be dev, staging, or prod")
            return value
        
        if var_name == 'BASIS_DEPLOYMENT_MODE':
            if value not in ['local', 'docker']:
                logger.error(f"CONFIG-MGR-004: Invalid deployment mode value for {var_name}: {value}")
                raise ValueError(f"Invalid deployment mode value for {var_name}: {value}. Must be local or docker")
            return value
        
        if var_name == 'BASIS_DEPLOYMENT_MACHINE':
            if value not in ['local_mac', 'gcloud_linux_vm']:
                logger.error(f"CONFIG-MGR-004: Invalid deployment machine value for {var_name}: {value}")
                raise ValueError(f"Invalid deployment machine value for {var_name}: {value}. Must be local_mac or gcloud_linux_vm")
            return value
        
        if var_name == 'BASIS_DATA_MODE':
            if value not in ['csv', 'db']:
                logger.error(f"CONFIG-MGR-004: Invalid data mode value for {var_name}: {value}")
                raise ValueError(f"Invalid data mode value for {var_name}: {value}. Must be csv or db")
            return value
        
        if var_name == 'BASIS_EXECUTION_MODE':
            if value not in ['backtest', 'live']:
                logger.error(f"CONFIG-MGR-004: Invalid execution mode value for {var_name}: {value}")
                raise ValueError(f"Invalid execution mode value for {var_name}: {value}. Must be backtest or live")
            return value
        
        if var_name == 'BASIS_LOG_LEVEL':
            if value not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                logger.error(f"CONFIG-MGR-004: Invalid log level value for {var_name}: {value}")
                raise ValueError(f"Invalid log level value for {var_name}: {value}. Must be DEBUG, INFO, WARNING, ERROR, or CRITICAL")
            return value
        
        # Date validation
        if var_name in ['BASIS_DATA_START_DATE', 'BASIS_DATA_END_DATE']:
            try:
                from datetime import datetime
                datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                logger.error(f"CONFIG-MGR-004: Invalid date format for {var_name}: {value}")
                raise ValueError(f"Invalid date format for {var_name}: {value}. Must be YYYY-MM-DD")
            return value
        
        # Duration validation
        if var_name == 'HEALTH_CHECK_INTERVAL':
            if not value.endswith(('s', 'm', 'h')):
                logger.error(f"CONFIG-MGR-004: Invalid duration format for {var_name}: {value}")
                raise ValueError(f"Invalid duration format for {var_name}: {value}. Must end with s, m, or h")
            return value
        
        # Path validation
        if var_name in ['BASIS_DATA_DIR', 'BASIS_RESULTS_DIR']:
            if not value or value.isspace():
                logger.error(f"CONFIG-MGR-004: Empty path for {var_name}")
                raise ValueError(f"Empty path for {var_name}")
            return value
        
        # URL validation
        if var_name in ['BASIS_API_CORS_ORIGINS']:
            # Basic URL validation - check if it contains valid characters
            if not value or value.isspace():
                logger.error(f"CONFIG-MGR-004: Empty CORS origins for {var_name}")
                raise ValueError(f"Empty CORS origins for {var_name}")
            return value
        
        # Default: return as-is
        return value
    
    def get_execution_mode(self) -> str:
        """Get startup mode from environment variables."""
        return self.config_cache['env']['BASIS_EXECUTION_MODE']
    
    def get_environment(self) -> str:
        """Get current environment from environment variables."""
        return self.config_cache['env']['BASIS_ENVIRONMENT']
    
    def get_data_directory(self) -> str:
        """Get data directory from environment variables."""
        return self.config_cache['env']['BASIS_DATA_DIR']
    
    def get_results_directory(self) -> str:
        """Get results directory from environment variables."""
        return self.config_cache['env']['BASIS_RESULTS_DIR']
    
    
    def get_data_date_range(self) -> Tuple[str, str]:
        """Get data date range from environment variables."""
        start_date = self.config_cache['env']['BASIS_DATA_START_DATE']
        end_date = self.config_cache['env']['BASIS_DATA_END_DATE']
        return start_date, end_date
    
    def get_settings(self) -> Dict[str, Any]:
        """Get complete settings (alias for get_complete_config)."""
        return self.get_complete_config()
    
    def get_complete_config(self, mode: str = None, venue: str = None) -> Dict[str, Any]:
        """Get complete configuration by merging all relevant configs."""
        config = self.config_cache['base'].copy()
        
        if mode:
            mode_config = self.config_cache['modes'].get(mode, {})
            config = self._deep_merge(config, mode_config)
        
        if venue:
            venue_config = self.config_cache['venues'].get(venue, {})
            config = self._deep_merge(config, venue_config)
        
        return config
    
    def get_available_strategies(self) -> List[str]:
        """Get list of all available strategy names."""
        return list(self.config_cache['modes'].keys())
    
    def strategy_exists(self, strategy_name: str) -> bool:
        """Check if a strategy exists."""
        return strategy_name in self.config_cache['modes']
    
    def validate_strategy_name(self, strategy_name: str) -> None:
        """Validate that a strategy name exists."""
        if not self.strategy_exists(strategy_name):
            available_strategies = self.get_available_strategies()
            raise ValueError(
                f"Unknown strategy: {strategy_name}\n"
                f"Available strategies: {available_strategies}"
            )
    
    def _validate_config(self):
        """Validate the loaded configuration."""
        logger.info("🔍 Validating loaded configuration...")
        
        # Basic validation - check that required configs are loaded
        # Note: base config is now empty (JSON configs eliminated), so just check it exists
        if 'base' not in self.config_cache:
            raise ValueError("Base configuration cache not initialized")
        if not self.config_cache.get('env'):
            raise ValueError("Environment variables not loaded")
        
        logger.info("✅ Configuration validation passed")
    
    def is_healthy(self) -> bool:
        """Check if configuration is healthy."""
        return 'base' in self.config_cache and self.config_cache.get('env') is not None
    
    def _load_base_config(self) -> Dict[str, Any]:
        """Load base configuration - ELIMINATED JSON configs, return empty dict."""
        logger.info("✅ Base configuration eliminated - infrastructure handled by environment variables")
        
        # DESIGN DECISION: All infrastructure configuration moved to environment variables
        # - Database/Storage URLs: Environment-specific variables
        # - API settings: Environment-specific variables  
        # - Cross-network/Rates: Hardcoded defaults in components
        # - Testnet: Live trading only, not needed for backtest focus
        
        return {}  # Empty base config since everything is in environment variables or hardcoded
    
    def _load_all_mode_configs(self) -> Dict[str, Any]:
        """Load all mode configurations from configs/modes/."""
        modes_dir = self.base_dir / "configs" / "modes"
        modes = {}
        
        if not modes_dir.exists():
            logger.warning(f"Modes directory not found: {modes_dir}")
            return modes
        
        for yaml_file in modes_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    mode_name = yaml_file.stem
                    modes[mode_name] = yaml.safe_load(f) or {}
            except (yaml.YAMLError, IOError) as e:
                logger.error(f"CONFIG-MGR-004: Failed to parse mode configuration: {str(e)}")
                raise ValueError(f"Failed to parse mode configuration {yaml_file}: {e}")
        
        return modes
    
    def _load_all_venue_configs(self) -> Dict[str, Any]:
        """Load all venue configurations from configs/venues/."""
        venues_dir = self.base_dir / "configs" / "venues"
        venues = {}
        
        if not venues_dir.exists():
            logger.warning(f"Venues directory not found: {venues_dir}")
            return venues
        
        for yaml_file in venues_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    venue_name = yaml_file.stem
                    venues[venue_name] = yaml.safe_load(f) or {}
            except (yaml.YAMLError, IOError) as e:
                logger.error(f"CONFIG-MGR-004: Failed to parse venue configuration: {str(e)}")
                raise ValueError(f"Failed to parse venue configuration {yaml_file}: {e}")
        
        return venues
    
    def _load_all_share_class_configs(self) -> Dict[str, Any]:
        """Load all share class configurations from configs/share_classes/."""
        share_classes_dir = self.base_dir / "configs" / "share_classes"
        share_classes = {}
        
        if not share_classes_dir.exists():
            logger.warning(f"Share classes directory not found: {share_classes_dir}")
            return share_classes
        
        for yaml_file in share_classes_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    share_class_name = yaml_file.stem
                    share_classes[share_class_name] = yaml.safe_load(f) or {}
            except (yaml.YAMLError, IOError) as e:
                logger.error(f"CONFIG-MGR-004: Failed to parse share class configuration: {str(e)}")
                raise ValueError(f"Failed to parse share class configuration {yaml_file}: {e}")
        
        return share_classes
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result


# Global config manager instance
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager()
    
    return _config_manager


# Compatibility functions for existing imports
def get_settings() -> Dict[str, Any]:
    """Get complete settings (compatibility function)."""
    cm = get_config_manager()
    return cm.get_complete_config()


def get_environment() -> str:
    """Get current environment (compatibility function)."""
    cm = get_config_manager()
    return cm.config_cache['env']['BASIS_ENVIRONMENT']


def load_mode_config(mode: str) -> Dict[str, Any]:
    """Load mode configuration (compatibility function)."""
    cm = get_config_manager()
    return cm.config_cache['modes'].get(mode, {})


def load_venue_config(venue: str) -> Dict[str, Any]:
    """Load venue configuration (compatibility function)."""
    cm = get_config_manager()
    return cm.config_cache['venues'].get(venue, {})


def load_share_class_config(share_class: str) -> Dict[str, Any]:
    """Load share class configuration (compatibility function)."""
    cm = get_config_manager()
    return cm.config_cache['share_classes'].get(share_class, {})


def load_scenario_config(scenario: str) -> Dict[str, Any]:
    """Load scenario configuration (compatibility function)."""
    # Scenarios eliminated - return empty dict
    logger.warning(f"Scenario configuration requested for '{scenario}' - scenarios have been eliminated")
    return {}


def load_strategy_config(strategy_name: str) -> Dict[str, Any]:
    """Load strategy configuration (compatibility function)."""
    cm = get_config_manager()
    cm.validate_strategy_name(strategy_name)
    return cm.get_complete_config(mode=strategy_name)


def get_available_strategies() -> List[str]:
    """Get available strategies (compatibility function)."""
    cm = get_config_manager()
    return cm.get_available_strategies()


def get_strategy_file_path(strategy_name: str) -> Optional[Path]:
    """Get strategy file path (compatibility function)."""
    cm = get_config_manager()
    if not cm.strategy_exists(strategy_name):
        return None
    return cm.base_dir / "configs" / "modes" / f"{strategy_name}.yaml"


def validate_strategy_name(strategy_name: str) -> None:
    """Validate strategy name (compatibility function)."""
    cm = get_config_manager()
    cm.validate_strategy_name(strategy_name)


# Constants for compatibility
_BASE_DIR = Path(__file__).parent.parent.parent.parent.parent.parent
