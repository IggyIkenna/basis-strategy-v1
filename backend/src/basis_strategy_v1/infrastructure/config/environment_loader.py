"""
Environment File Switching & Fail-Fast Configuration Loader

Implements proper environment file switching with BASIS_ENVIRONMENT variable
and fail-fast validation for missing environment files and required variables.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 33 (Fail-Fast Configuration)
Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-040 (Fail-Fast Configuration)
Reference: docs/ENVIRONMENT_VARIABLES.md - Environment variable specifications
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class EnvironmentLoaderError(Exception):
    """Environment loader specific errors."""
    pass


class EnvironmentLoader:
    """
    Environment file switching with fail-fast validation.
    
    Features:
    - BASIS_ENVIRONMENT variable controls environment file loading
    - Environment-specific files (env.dev, env.staging, env.prod)
    - Fallback to env.unified as base configuration
    - Fail-fast on missing environment files or required variables
    - Environment variable overrides with proper precedence
    """
    
    def __init__(self, environment: Optional[str] = None, base_dir: Optional[Path] = None):
        """
        Initialize environment loader.
        
        Args:
            environment: Environment name (dev/staging/prod). If None, uses BASIS_ENVIRONMENT or defaults to 'dev'
            base_dir: Base directory for environment files. If None, uses current working directory
        """
        self.base_dir = base_dir or Path.cwd()
        self.environment = environment or os.getenv('BASIS_ENVIRONMENT', 'dev')
        self.env_file = f"env.{self.environment}"
        self.unified_file = "env.unified"
        
        # Validate environment name
        if self.environment not in ['dev', 'staging', 'prod']:
            raise EnvironmentLoaderError(
                f"Invalid environment '{self.environment}'. Must be one of: dev, staging, prod"
            )
        
        logger.info(f"🔧 Initializing EnvironmentLoader for '{self.environment}' environment")
        logger.info(f"📁 Base directory: {self.base_dir}")
        logger.info(f"📄 Environment file: {self.env_file}")
        logger.info(f"📄 Unified file: {self.unified_file}")
    
    def load_environment(self) -> Dict[str, str]:
        """
        Load environment configuration with fail-fast validation.
        
        Returns:
            Dict of environment variables
            
        Raises:
            EnvironmentLoaderError: If environment files are missing or invalid
        """
        logger.info(f"🔄 Loading environment configuration for '{self.environment}'...")
        
        # Step 1: Validate environment file exists
        self._validate_environment_file()
        
        # Step 2: Load env.unified as base
        base_vars = self._load_unified_file()
        
        # Step 3: Load environment-specific overrides
        env_vars = self._load_environment_file()
        
        # Step 4: Merge configurations with proper precedence
        merged_vars = self._merge_configurations(base_vars, env_vars)
        
        # Step 5: Validate all required variables are present
        self._validate_required_variables(merged_vars)
        
        # Step 6: Set environment variables
        self._set_environment_variables(merged_vars)
        
        logger.info(f"✅ Environment configuration loaded successfully for '{self.environment}'")
        logger.info(f"📊 Total variables loaded: {len(merged_vars)}")
        
        return merged_vars
    
    def _validate_environment_file(self) -> None:
        """Validate that environment file exists and is readable."""
        env_path = self.base_dir / self.env_file
        
        if not env_path.exists():
            raise EnvironmentLoaderError(
                f"Environment file '{self.env_file}' not found at {env_path}. "
                f"Expected location: {env_path.absolute()}"
            )
        
        if not os.access(env_path, os.R_OK):
            raise EnvironmentLoaderError(
                f"Environment file '{self.env_file}' is not readable. "
                f"Check file permissions: {env_path.absolute()}"
            )
        
        logger.debug(f"✅ Environment file validation passed: {env_path}")
    
    def _load_unified_file(self) -> Dict[str, str]:
        """Load env.unified as base configuration."""
        unified_path = self.base_dir / self.unified_file
        
        if not unified_path.exists():
            raise EnvironmentLoaderError(
                f"Unified environment file '{self.unified_file}' not found at {unified_path}. "
                f"Expected location: {unified_path.absolute()}"
            )
        
        if not os.access(unified_path, os.R_OK):
            raise EnvironmentLoaderError(
                f"Unified environment file '{self.unified_file}' is not readable. "
                f"Check file permissions: {unified_path.absolute()}"
            )
        
        vars_dict = self._parse_env_file(unified_path)
        logger.debug(f"✅ Loaded {len(vars_dict)} variables from {self.unified_file}")
        
        return vars_dict
    
    def _load_environment_file(self) -> Dict[str, str]:
        """Load environment-specific configuration."""
        env_path = self.base_dir / self.env_file
        
        vars_dict = self._parse_env_file(env_path)
        logger.debug(f"✅ Loaded {len(vars_dict)} variables from {self.env_file}")
        
        return vars_dict
    
    def _parse_env_file(self, file_path: Path) -> Dict[str, str]:
        """
        Parse environment file and return key-value pairs.
        
        Args:
            file_path: Path to environment file
            
        Returns:
            Dict of environment variables
            
        Raises:
            EnvironmentLoaderError: If file parsing fails
        """
        vars_dict = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        vars_dict[key] = value
                    else:
                        logger.warning(f"Invalid line format in {file_path}:{line_num}: {line}")
        
        except Exception as e:
            raise EnvironmentLoaderError(
                f"Failed to parse environment file '{file_path}': {e}"
            )
        
        return vars_dict
    
    def _merge_configurations(self, base_vars: Dict[str, str], env_vars: Dict[str, str]) -> Dict[str, str]:
        """
        Merge base and environment-specific configurations.
        
        Precedence: env.{environment} > env.unified > system environment variables
        
        Args:
            base_vars: Variables from env.unified
            env_vars: Variables from env.{environment}
            
        Returns:
            Merged configuration
        """
        merged = {}
        
        # Start with system environment variables (lowest precedence)
        merged.update(os.environ)
        
        # Override with env.unified (medium precedence)
        merged.update(base_vars)
        
        # Override with env.{environment} (highest precedence)
        merged.update(env_vars)
        
        # Log overrides for debugging
        overrides = []
        for key in env_vars:
            if key in base_vars and base_vars[key] != env_vars[key]:
                overrides.append(f"{key}: '{base_vars[key]}' -> '{env_vars[key]}'")
        
        if overrides:
            logger.info(f"🔄 Environment overrides applied ({len(overrides)} variables):")
            for override in overrides:
                logger.info(f"   {override}")
        
        return merged
    
    def _validate_required_variables(self, vars_dict: Dict[str, str]) -> None:
        """
        Validate that all required variables are present and not empty.
        
        Args:
            vars_dict: Environment variables to validate
            
        Raises:
            EnvironmentLoaderError: If required variables are missing or empty
        """
        # Required variables from env.unified (non-empty values)
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
            'BASIS_API_CORS_ORIGINS',
            'APP_DOMAIN',
            'ACME_EMAIL',
            'HTTP_PORT',
            'HTTPS_PORT',
            'DATA_LOAD_TIMEOUT',
            'DATA_VALIDATION_STRICT',
            'DATA_CACHE_SIZE',
            'STRATEGY_MANAGER_TIMEOUT',
            'STRATEGY_MANAGER_MAX_RETRIES',
            'STRATEGY_FACTORY_TIMEOUT',
            'STRATEGY_FACTORY_MAX_RETRIES'
        ]
        
        missing_vars = []
        empty_vars = []
        
        for var in required_vars:
            if var not in vars_dict:
                missing_vars.append(var)
            elif not vars_dict[var].strip():
                empty_vars.append(var)
        
        if missing_vars or empty_vars:
            error_msg = "Required environment variables validation failed:\n"
            
            if missing_vars:
                error_msg += f"  Missing variables: {', '.join(missing_vars)}\n"
            
            if empty_vars:
                error_msg += f"  Empty variables: {', '.join(empty_vars)}\n"
            
            error_msg += f"\nEnvironment: {self.environment}"
            error_msg += f"\nEnvironment file: {self.env_file}"
            error_msg += f"\nUnified file: {self.unified_file}"
            
            raise EnvironmentLoaderError(error_msg)
        
        logger.debug(f"✅ Required variables validation passed ({len(required_vars)} variables)")
    
    def _set_environment_variables(self, vars_dict: Dict[str, str]) -> None:
        """
        Set environment variables in the current process.
        
        Args:
            vars_dict: Environment variables to set
        """
        for key, value in vars_dict.items():
            os.environ[key] = value
        
        logger.debug(f"✅ Set {len(vars_dict)} environment variables")
    
    def get_environment_info(self) -> Dict[str, Any]:
        """
        Get information about the current environment configuration.
        
        Returns:
            Dict with environment information
        """
        return {
            'environment': self.environment,
            'env_file': self.env_file,
            'unified_file': self.unified_file,
            'base_dir': str(self.base_dir),
            'env_file_path': str(self.base_dir / self.env_file),
            'unified_file_path': str(self.base_dir / self.unified_file)
        }


# Global environment loader instance
_environment_loader: Optional[EnvironmentLoader] = None


def get_environment_loader(environment: Optional[str] = None) -> EnvironmentLoader:
    """
    Get the global environment loader instance.
    
    Args:
        environment: Environment name. If None, uses BASIS_ENVIRONMENT or defaults to 'dev'
        
    Returns:
        EnvironmentLoader instance
    """
    global _environment_loader
    
    if _environment_loader is None:
        _environment_loader = EnvironmentLoader(environment)
    
    return _environment_loader


def load_environment(environment: Optional[str] = None) -> Dict[str, str]:
    """
    Load environment configuration using the global loader.
    
    Args:
        environment: Environment name. If None, uses BASIS_ENVIRONMENT or defaults to 'dev'
        
    Returns:
        Dict of environment variables
        
    Raises:
        EnvironmentLoaderError: If environment loading fails
    """
    loader = get_environment_loader(environment)
    return loader.load_environment()


def get_environment_info() -> Dict[str, Any]:
    """
    Get information about the current environment configuration.
    
    Returns:
        Dict with environment information
    """
    loader = get_environment_loader()
    return loader.get_environment_info()


def is_environment_loaded() -> bool:
    """
    Check if environment has been loaded.
    
    Returns:
        True if environment is loaded, False otherwise
    """
    return _environment_loader is not None

