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
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from functools import lru_cache
import logging
import pandas as pd
from datetime import datetime

from .models import (
    validate_mode_config, validate_venue_config, validate_share_class_config,
    validate_complete_configuration, ConfigurationSet, ConfigurationValidationError
)
from .config_validator import ValidationResult
from .constants import _BASE_DIR, get_environment
from ...core.errors.component_error import ComponentError
import structlog
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
        
        # Initialize structured logger
        self.structured_logger = structlog.get_logger()
        
        # Health integration
        self.health_status = {
            'status': 'healthy',
            'last_check': datetime.now(),
            'error_count': 0,
            'success_count': 0
        }
        
        # Initialize configuration loading
        self._initialize_config()
        
        # Log initialization
        self.structured_logger.info(
            'ConfigManager initialized',
            event_type='component_initialization',
            execution_mode=os.getenv('BASIS_EXECUTION_MODE', 'backtest'),
            config_hash=hash(str(self.config_cache)),
            config_cache_size=len(self.config_cache),
            component_type='ConfigManager'
        )
    
    def check_component_health(self) -> Dict[str, Any]:
        """Check component health status."""
        return {
            'status': self.health_status['status'],
            'error_count': self.health_status['error_count'],
            'success_count': self.health_status['success_count'],
            'config_cache_size': len(self.config_cache),
            'component': self.__class__.__name__
        }
    
    def _initialize_config(self):
        """Initialize configuration loading and validation."""
        # Load and validate configuration using public methods
        self.load_config()
        self.validate_config()
        
        # Config manager health now handled by unified health manager
    
    def _handle_error(self, error_code: str, error_message: str, details: Optional[Dict] = None):
        """
        Handle errors with structured error handling.
        
        Args:
            error_code: Error code from ERROR_CODES
            error_message: Error message
            details: Additional error details
        """
        try:
            # Update health status
            self.health_status['error_count'] += 1
            
            # Create structured error
            error = ComponentError(
                component='config_manager',
                error_code=error_code,
                message=error_message,
                details=details or {}
            )
            
            # Log structured error
            self.structured_logger.error(
                f"Config Manager Error: {error_code}",
                error_code=error_code,
                error_message=error_message,
                details=details,
                component='config_manager'
            )
            
            # Update health status if too many errors
            if self.health_status['error_count'] > 10:
                self.health_status['status'] = 'unhealthy'
            
        except Exception as e:
            logger.error(f"Failed to handle error: {e}")
    
    def _log_success(self, operation: str, details: Optional[Dict] = None):
        """
        Log successful operations.
        
        Args:
            operation: Operation name
            details: Operation details
        """
        try:
            # Update health status
            self.health_status['success_count'] += 1
            
            # Log success
            self.structured_logger.info(
                f"Config Manager Success: {operation}",
                operation=operation,
                details=details,
                component='config_manager'
            )
            
        except Exception as e:
            logger.error(f"Failed to log success: {e}")
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Get data using canonical data access pattern.
        
        Args:
            timestamp: Current timestamp
            
        Returns:
            Data dictionary
        """
        try:
            return {
                'config_cache': self.config_cache,
                'validation_result': self._validation_result,
                'available_strategies': self.get_available_strategies()
            }
        except Exception as e:
            self._handle_error('CONFIG-MGR-001', f"Failed to get data: {e}")
            return {}
    
    def create_component(self, component_type: str, config: Dict[str, Any]) -> Any:
        """
        Create component using factory pattern.
        
        Args:
            component_type: Type of component to create
            config: Configuration for the component
            
        Returns:
            Created component instance
        """
        try:
            # This is a factory method for creating components
            # Implementation would depend on the specific component type
            self._log_success('component_created', {'component_type': component_type})
            return None  # Placeholder for actual implementation
        except Exception as e:
            self._handle_error('CONFIG-MGR-007', f"Failed to create component {component_type}: {e}")
            return None
    
    def load_config(self):
        """Load all configuration files and environment variables. Public method for intentional config loading."""
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
                       'STRATEGY_FACTORY_MAX_RETRIES']:
            try:
                int(value)
            except ValueError:
                logger.error(f"CONFIG-MGR-004: Invalid integer value for {var_name}: {value}")
                raise ValueError(f"Invalid integer value for {var_name}: {value}")
            return value
        
        # Enum validation
        if var_name == 'BASIS_ENVIRONMENT':
            if value not in ['dev', 'staging', 'prod']:
                logger.error(f"CONFIG-MGR-004: Invalid environment value for {var_name}: {value}")
                raise ValueError(f"Invalid environment value for {var_name}: {value}. Must be dev, staging, or prod")
            return value
        
        if var_name == 'BASIS_DEPLOYMENT_MODE':
            if value not in ['local', 'docker', 'staging', 'prod']:
                logger.error(f"CONFIG-MGR-004: Invalid deployment mode value for {var_name}: {value}")
                raise ValueError(f"Invalid deployment mode value for {var_name}: {value}. Must be local, docker, staging, or prod")
            return value
        
        if var_name == 'BASIS_DEPLOYMENT_MACHINE':
            if value not in ['local_mac', 'gcloud_linux_vm', 'staging_server', 'prod_server']:
                logger.error(f"CONFIG-MGR-004: Invalid deployment machine value for {var_name}: {value}")
                raise ValueError(f"Invalid deployment machine value for {var_name}: {value}. Must be local_mac, gcloud_linux_vm, staging_server, or prod_server")
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
        
        # Float validation for specific variables that should be floats
        if var_name in ['BASIS_API_TIMEOUT', 'BASIS_DATA_TIMEOUT', 'BASIS_STRATEGY_TIMEOUT']:
            try:
                float(value)
            except ValueError:
                logger.error(f"CONFIG-MGR-004: Invalid float value for {var_name}: {value}")
                raise ValueError(f"Invalid float value for {var_name}: {value}")
            return value
        
        # Default: return as-is (most environment variables are strings)
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
        # Config-driven behavior
        config_settings = self.config_cache.get('base', {}).get('config_manager', {})
        enable_caching = config_settings.get('enable_caching', True)
        cache_ttl = config_settings.get('cache_ttl', 300)
        
        # Start with base config (empty dict if no base config exists)
        config = self.config_cache.get('base', {}).copy()
        
        if mode:
            if mode not in self.config_cache['modes']:
                raise KeyError(f"Mode '{mode}' not found in configuration")
            mode_config = self.config_cache['modes'][mode]
            config = self._deep_merge(config, mode_config)
        
        if venue:
            if venue not in self.config_cache['venues']:
                raise KeyError(f"Venue '{venue}' not found in configuration")
            venue_config = self.config_cache['venues'][venue]
            config = self._deep_merge(config, venue_config)
        
        return config
    
    def get_available_strategies(self) -> List[str]:
        """Get list of all available strategy names."""
        return list(self.config_cache['modes'].keys())
    
    def get_mode_config(self, mode_name: str) -> Dict[str, Any]:
        """Get mode configuration with fail-fast access."""
        if mode_name not in self.config_cache['modes']:
            raise KeyError(f"Mode '{mode_name}' not found. Available modes: {list(self.config_cache['modes'].keys())}")
        return self.config_cache['modes'][mode_name]
    
    def get_venue_config(self, venue_name: str) -> Dict[str, Any]:
        """Get venue configuration with fail-fast access."""
        if venue_name not in self.config_cache['venues']:
            raise KeyError(f"Venue '{venue_name}' not found. Available venues: {list(self.config_cache['venues'].keys())}")
        return self.config_cache['venues'][venue_name]
    
    def get_share_class_config(self, share_class_name: str) -> Dict[str, Any]:
        """Get share class configuration with fail-fast access."""
        if share_class_name not in self.config_cache['share_classes']:
            raise KeyError(f"Share class '{share_class_name}' not found. Available share classes: {list(self.config_cache['share_classes'].keys())}")
        return self.config_cache['share_classes'][share_class_name]
    
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
    
    def validate_config(self):
        """Validate the loaded configuration with cross-reference validation."""
        logger.info("🔍 Validating loaded configuration...")
        
        # Basic validation - check that required configs are loaded
        if 'base' not in self.config_cache:
            raise ValueError("Base configuration cache not initialized")
        if not self.config_cache.get('env'):
            raise ValueError("Environment variables not loaded")
        
        # Validate cross-references between configurations
        try:
            validated_config = validate_complete_configuration(
                modes=self.config_cache['modes'],
                venues=self.config_cache['venues'],
                share_classes=self.config_cache['share_classes']
            )
            logger.info("✅ Cross-reference validation passed")
        except ConfigurationValidationError as e:
            logger.error(f"CONFIG-MGR-005: Cross-reference validation failed: {str(e)}")
            raise ValueError(f"Cross-reference validation failed: {e}")
        
        logger.info("✅ Configuration validation passed")
    
    def is_healthy(self) -> bool:
        """Check if configuration is healthy."""
        return 'base' in self.config_cache and self.config_cache.get('env') is not None
    
    # Standardized Logging Methods (per HEALTH_ERROR_SYSTEMS.md and 08_EVENT_LOGGER.md)
    
    def log_structured_event(self, timestamp: pd.Timestamp, event_type: str, level: str, message: str, component_name: str, data: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> None:
        """Log a structured event with standardized format."""
        try:
            event_data = {
                'timestamp': timestamp,
                'event_type': event_type,
                'level': level,
                'message': message,
                'component_name': component_name,
                'data': data or {},
                'correlation_id': correlation_id
            }
            
            # Log to standard logger
            if level == 'ERROR':
                logger.error(f"[{component_name}] {message}", extra=event_data)
            elif level == 'WARNING':
                logger.warning(f"[{component_name}] {message}", extra=event_data)
            else:
                logger.info(f"[{component_name}] {message}", extra=event_data)
                
        except Exception as e:
            logger.error(f"Failed to log structured event: {e}")
    
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a performance metric."""
        try:
            timestamp = pd.Timestamp.now(tz='UTC')
            message = f"Performance metric: {metric_name} = {value} {unit}"
            metric_data = {
                'metric_name': metric_name,
                'value': value,
                'unit': unit,
                **(data or {})
            }
            self.log_structured_event(timestamp, 'performance_metric', 'INFO', message, 'ConfigManager', metric_data)
        except Exception as e:
            logger.error(f"Failed to log performance metric: {e}")
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> None:
        """Log an error with standardized format."""
        try:
            timestamp = pd.Timestamp.now(tz='UTC')
            error_data = {
                'error_type': type(error).__name__,
                'context': context or {},
                'correlation_id': correlation_id
            }
            self.log_structured_event(timestamp, 'error', 'ERROR', str(error), 'ConfigManager', error_data)
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    def log_warning(self, message: str, data: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> None:
        """Log a warning with standardized format."""
        try:
            timestamp = pd.Timestamp.now(tz='UTC')
            self.log_structured_event(timestamp, 'warning', 'WARNING', message, 'ConfigManager', data, correlation_id)
        except Exception as e:
            logger.error(f"Failed to log warning: {e}")
    
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
        """Load all mode configurations from configs/modes/ with Pydantic validation."""
        modes_dir = self.base_dir / "configs" / "modes"
        modes = {}
        
        if not modes_dir.exists():
            logger.error(f"CONFIG-MGR-003: Modes directory not found: {modes_dir}")
            raise FileNotFoundError(f"Modes directory not found: {modes_dir}")
        
        for yaml_file in modes_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    mode_name = yaml_file.stem
                    config_dict = yaml.safe_load(f) or {}
                    
                    # Validate with Pydantic model
                    validated_config = validate_mode_config(config_dict, mode_name)
                    modes[mode_name] = validated_config.model_dump()
                    
            except (yaml.YAMLError, IOError) as e:
                logger.error(f"CONFIG-MGR-004: Failed to parse mode configuration: {str(e)}")
                raise ValueError(f"Failed to parse mode configuration {yaml_file}: {e}")
            except ConfigurationValidationError as e:
                logger.error(f"CONFIG-MGR-005: Mode configuration validation failed: {str(e)}")
                raise ValueError(f"Mode configuration validation failed for {yaml_file}: {e}")
        
        return modes
    
    def _load_all_venue_configs(self) -> Dict[str, Any]:
        """Load all venue configurations from configs/venues/ with Pydantic validation."""
        venues_dir = self.base_dir / "configs" / "venues"
        venues = {}
        
        if not venues_dir.exists():
            logger.error(f"CONFIG-MGR-003: Venues directory not found: {venues_dir}")
            raise FileNotFoundError(f"Venues directory not found: {venues_dir}")
        
        for yaml_file in venues_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    venue_name = yaml_file.stem
                    config_dict = yaml.safe_load(f) or {}
                    
                    # Validate with Pydantic model
                    validated_config = validate_venue_config(config_dict, venue_name)
                    venues[venue_name] = validated_config.model_dump()
                    
            except (yaml.YAMLError, IOError) as e:
                logger.error(f"CONFIG-MGR-004: Failed to parse venue configuration: {str(e)}")
                raise ValueError(f"Failed to parse venue configuration {yaml_file}: {e}")
            except ConfigurationValidationError as e:
                logger.error(f"CONFIG-MGR-005: Venue configuration validation failed: {str(e)}")
                raise ValueError(f"Venue configuration validation failed for {yaml_file}: {e}")
        
        return venues
    
    def _load_all_share_class_configs(self) -> Dict[str, Any]:
        """Load all share class configurations from configs/share_classes/ with Pydantic validation."""
        share_classes_dir = self.base_dir / "configs" / "share_classes"
        share_classes = {}
        
        if not share_classes_dir.exists():
            logger.error(f"CONFIG-MGR-003: Share classes directory not found: {share_classes_dir}")
            raise FileNotFoundError(f"Share classes directory not found: {share_classes_dir}")
        
        for yaml_file in share_classes_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    share_class_name = yaml_file.stem
                    config_dict = yaml.safe_load(f) or {}
                    
                    # Validate with Pydantic model
                    validated_config = validate_share_class_config(config_dict, share_class_name)
                    share_classes[share_class_name] = validated_config.model_dump()
                    
            except (yaml.YAMLError, IOError) as e:
                logger.error(f"CONFIG-MGR-004: Failed to parse share class configuration: {str(e)}")
                raise ValueError(f"Failed to parse share class configuration {yaml_file}: {e}")
            except ConfigurationValidationError as e:
                logger.error(f"CONFIG-MGR-005: Share class configuration validation failed: {str(e)}")
                raise ValueError(f"Share class configuration validation failed for {yaml_file}: {e}")
        
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

def initialize_config_manager() -> ConfigManager:
    """Initialize the global configuration manager instance."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager()
    
    return _config_manager

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager()
    
    return _config_manager




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
