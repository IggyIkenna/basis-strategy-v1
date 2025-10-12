"""
Configuration Validator

Validates all configuration files and environment variables to ensure
the system is ready to run. Fails fast on bad configuration.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from .config_manager import _BASE_DIR, get_environment

logger = logging.getLogger(__name__)

# Error codes for Config Validator
ERROR_CODES = {
    'CONFIG-001': 'Configuration file not found',
    'CONFIG-002': 'Configuration file parsing failed',
    'CONFIG-003': 'Required configuration section missing',
    'CONFIG-004': 'Configuration validation failed',
    'CONFIG-005': 'Environment variable missing',
    'CONFIG-006': 'Mode configuration invalid',
    'CONFIG-007': 'Venue configuration invalid',
    'CONFIG-008': 'Share class configuration invalid',
    'CONFIG-009': 'Business logic validation failed',
    'CONFIG-010': 'Configuration structure invalid'
}


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    environment: str
    config_summary: Dict[str, Any]


class ConfigValidator:
    """Validates all configuration files and environment variables."""
    
    def __init__(self):
        self.base_dir = _BASE_DIR
        self.environment = get_environment()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_all(self) -> ValidationResult:
        """Validate all configuration files and environment variables."""
        logger.info(f"🔍 Validating configuration for {self.environment} environment...")
        
        # Reset validation state
        self.errors = []
        self.warnings = []
        
        # Validate core configuration
        self._validate_base_configs() 
        self._validate_environment_variables()
        self._validate_mode_configs()
        self._validate_venue_configs()
        self._validate_share_class_configs()
        self._validate_business_logic()
        
        # Create config summary
        config_summary = self._create_config_summary()
        
        is_valid = len(self.errors) == 0
        
        if is_valid:
            logger.info("✅ Configuration validation passed")
        else:
            logger.error(f"❌ Configuration validation failed with {len(self.errors)} errors")
            for error in self.errors:
                logger.error(f"  - {error}")
        
        if self.warnings:
            logger.warning(f"⚠️ Configuration validation completed with {len(self.warnings)} warnings")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=self.errors,
            warnings=self.warnings,
            environment=self.environment,
            config_summary=config_summary
        )
    
    def _validate_base_configs(self):
        """Validate base configuration structure."""
        logger.debug("Validating base configuration structure...")
        
        # DESIGN CHANGE: JSON configs eliminated - infrastructure handled by environment variables
        logger.debug("✅ JSON configs eliminated - infrastructure handled by environment variables and hardcoded defaults")
        
        # Validate that configs directory exists and has the required YAML structure
        configs_dir = self.base_dir / "configs"
        if not configs_dir.exists():
            self.errors.append(f"Missing configs directory: {configs_dir}")
            return
        
        required_subdirs = ['modes', 'venues', 'share_classes']
        for subdir in required_subdirs:
            subdir_path = configs_dir / subdir
            if not subdir_path.exists():
                self.errors.append(f"Missing required config subdirectory: {subdir}")
            elif not subdir_path.is_dir():
                self.errors.append(f"Config subdirectory is not a directory: {subdir}")
    
    def _validate_environment_variables(self):
        """Validate required environment variables."""
        logger.debug("Validating environment variables...")
        
        # Skip production variable validation in test mode
        if os.getenv('BASIS_ENVIRONMENT') == 'test':
            logger.debug("Test environment detected, skipping production variable validation")
            return
        
        # Check core startup variables (including new infrastructure variables)
        core_vars = [
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
            'BASIS_API_PORT',
            'BASIS_API_HOST',
            'BASIS_API_CORS_ORIGINS',
            'HEALTH_CHECK_INTERVAL',
            'HEALTH_CHECK_ENDPOINT',
            'DATA_LOAD_TIMEOUT',
            'DATA_VALIDATION_STRICT',
            'DATA_CACHE_SIZE',
            'STRATEGY_MANAGER_TIMEOUT',
            'STRATEGY_MANAGER_MAX_RETRIES',
            'STRATEGY_FACTORY_TIMEOUT',
            'STRATEGY_FACTORY_MAX_RETRIES'
        ]
        
        # Frontend/Caddy deployment variables (WARNING if missing, not ERROR)
        frontend_deployment_vars = [
            'APP_DOMAIN',
            'ACME_EMAIL',
            'BASIC_AUTH_HASH',
            'HTTP_PORT',
            'HTTPS_PORT',
            'VITE_API_MODE'
        ]
        
        # Live trading variables (only validate if BASIS_EXECUTION_MODE=live)
        execution_mode = os.getenv('BASIS_EXECUTION_MODE', 'backtest')
        if execution_mode == 'live':
            self._validate_live_trading_variables()
        
        for var in core_vars:
            if not os.getenv(var):
                self.errors.append(f"Missing required environment variable: {var}")
        
        # Frontend deployment vars are optional (warn only)
        for var in frontend_deployment_vars:
            if not os.getenv(var):
                self.warnings.append(
                    f"Missing frontend deployment variable: {var}. "
                    f"This is required for full-stack deployment but OK for backend-only mode."
                )
        
        # Validate BASIS_DATA_MODE (must be csv or db)
        data_mode = os.getenv('BASIS_DATA_MODE')
        if data_mode and data_mode not in ['csv', 'db']:
            self.errors.append(f"BASIS_DATA_MODE must be 'csv' or 'db', got: {data_mode}")
        
        # Check environment-specific API keys (only for live mode)
        execution_mode = os.getenv('BASIS_EXECUTION_MODE')
        if execution_mode == 'live':
            # Only check the current environment (dev, staging, or prod)
            if self.environment in ['dev', 'staging', 'prod']:
                env_prefix = f'BASIS_{self.environment.upper()}__'
                
                required_vars = [
                    f'{env_prefix}ALCHEMY__PRIVATE_KEY',
                    f'{env_prefix}ALCHEMY__WALLET_ADDRESS',
                    f'{env_prefix}ALCHEMY__RPC_URL',
                    f'{env_prefix}ALCHEMY__NETWORK',
                    f'{env_prefix}ALCHEMY__CHAIN_ID',
                    f'{env_prefix}CEX__BINANCE_SPOT_API_KEY',
                    f'{env_prefix}CEX__BINANCE_SPOT_SECRET',
                    f'{env_prefix}CEX__BINANCE_FUTURES_API_KEY',
                    f'{env_prefix}CEX__BINANCE_FUTURES_SECRET',
                    f'{env_prefix}CEX__BYBIT_API_KEY',
                    f'{env_prefix}CEX__BYBIT_SECRET',
                    f'{env_prefix}CEX__OKX_API_KEY',
                    f'{env_prefix}CEX__OKX_SECRET',
                    f'{env_prefix}CEX__OKX_PASSPHRASE'
                ]
                
                for var in required_vars:
                    if not os.getenv(var):
                        self.errors.append(f"Missing required environment variable for live mode: {var}")
                
                # Check for placeholder values
                placeholder_vars = []
                for var in required_vars:
                    value = os.getenv(var, '')
                    if value.startswith('your_') or value == '0x...' or value == '':
                        placeholder_vars.append(var)
                
                if placeholder_vars:
                    self.warnings.append(f"Environment variables with placeholder values: {', '.join(placeholder_vars)}")
        elif execution_mode == 'backtest':
            # Backtest mode - no credentials required
            logger.debug("Backtest mode detected - skipping credential validation")
        else:
            self.errors.append(f"Invalid BASIS_EXECUTION_MODE: {execution_mode}. Must be 'backtest' or 'live'")
    
    def _validate_mode_configs(self):
        """Validate mode configuration files."""
        logger.debug("Validating mode configuration files...")
        
        modes_dir = self.base_dir / "configs" / "modes"
        if not modes_dir.exists():
            self.errors.append(f"Missing modes directory: {modes_dir}")
            return
        
        expected_modes = [
            'pure_lending.yaml',
            'btc_basis.yaml', 
            'eth_leveraged.yaml',
            'eth_staking_only.yaml',
            'usdt_market_neutral.yaml',
            'usdt_market_neutral_no_leverage.yaml'
        ]
        
        for mode_file in expected_modes:
            mode_path = modes_dir / mode_file
            if not mode_path.exists():
                self.errors.append(f"Missing mode config: {mode_file}")
            else:
                try:
                    with open(mode_path, 'r') as f:
                        mode_config = yaml.safe_load(f)
                    self._validate_mode_structure(mode_config, mode_file)
                except Exception as e:
                    self.errors.append(f"Invalid mode config {mode_file}: {e}")
    
    def _validate_venue_configs(self):
        """Validate venue configuration files."""
        logger.debug("Validating venue configuration files...")
        
        venues_dir = self.base_dir / "configs" / "venues"
        if not venues_dir.exists():
            self.errors.append(f"Missing venues directory: {venues_dir}")
            return
        
        expected_venues = [
            'binance.yaml',
            'bybit.yaml',
            'okx.yaml',
            'aave_v3.yaml',
            'etherfi.yaml',
            'lido.yaml',
            'morpho.yaml',
            'alchemy.yaml'
        ]
        
        for venue_file in expected_venues:
            venue_path = venues_dir / venue_file
            if not venue_path.exists():
                self.errors.append(f"Missing venue config: {venue_file}")
            else:
                try:
                    with open(venue_path, 'r') as f:
                        venue_config = yaml.safe_load(f)
                    self._validate_venue_structure(venue_config, venue_file)
                except Exception as e:
                    self.errors.append(f"Invalid venue config {venue_file}: {e}")
    
    def _validate_share_class_configs(self):
        """Validate share class configuration files."""
        logger.debug("Validating share class configuration files...")
        
        share_classes_dir = self.base_dir / "configs" / "share_classes"
        if not share_classes_dir.exists():
            self.errors.append(f"Missing share_classes directory: {share_classes_dir}")
            return
        
        expected_share_classes = [
            'usdt_stable.yaml',
            'eth_directional.yaml'
        ]
        
        for share_class_file in expected_share_classes:
            share_class_path = share_classes_dir / share_class_file
            if not share_class_path.exists():
                self.errors.append(f"Missing share class config: {share_class_file}")
            else:
                try:
                    with open(share_class_path, 'r') as f:
                        share_class_config = yaml.safe_load(f)
                    self._validate_share_class_structure(share_class_config, share_class_file)
                except Exception as e:
                    self.errors.append(f"Invalid share class config {share_class_file}: {e}")

    
    def _validate_business_logic(self):
        """Validate business logic consistency across configs."""
        logger.debug("Validating business logic consistency...")
        
        # Load all mode configs
        modes_dir = self.base_dir / "configs" / "modes"
        if not modes_dir.exists():
            return
        
        mode_configs = {}
        for mode_file in modes_dir.glob("*.yaml"):
            try:
                with open(mode_file, 'r') as f:
                    mode_config = yaml.safe_load(f)
                    mode_configs[mode_file.stem] = mode_config
            except Exception as e:
                self.errors.append(f"Failed to load mode config {mode_file}: {e}")
        
        # Load share class configs
        share_classes_dir = self.base_dir / "configs" / "share_classes"
        share_class_configs = {}
        if share_classes_dir.exists():
            for share_class_file in share_classes_dir.glob("*.yaml"):
                try:
                    with open(share_class_file, 'r') as f:
                        share_class_config = yaml.safe_load(f)
                        share_class_configs[share_class_file.stem] = share_class_config
                except Exception as e:
                    self.errors.append(f"Failed to load share class config {share_class_file}: {e}")
        
        # Validate mode consistency
        for mode_name, config in mode_configs.items():
            self._validate_mode_business_logic(config, mode_name)
            self._validate_share_class_strategy_compatibility(config, mode_name, share_class_configs)
    
    def _validate_mode_business_logic(self, config: Dict[str, Any], mode_name: str):
        """Validate business logic for a specific mode."""
        
        # Check leverage consistency
        leverage_enabled = config.get('leverage_enabled', False)
        max_ltv = config.get('max_ltv', 0.0)
        
        # logger.debug(print(mode_name))
        # logger.debug(print(config))
        
        
        # Validate position_deviation_threshold range
        position_deviation_threshold = config.get('position_deviation_threshold', 0.02)
        if not (0.0 <= position_deviation_threshold <= 1.0):
            self.errors.append(f"Mode {mode_name}: position_deviation_threshold must be between 0.0 and 1.0, got {position_deviation_threshold}")
        
        # Validate lst_type when staking_enabled
        staking_enabled = config.get('staking_enabled', False)
        lst_type = config.get('lst_type')
        if staking_enabled and not lst_type:
            self.errors.append(f"Mode {mode_name}: lst_type must be set when staking_enabled=true")
        elif not staking_enabled and lst_type:
            self.warnings.append(f"Mode {mode_name}: lst_type is set but staking_enabled=false")
        
        # Validate max_ltv when borrowing_enabled
        borrowing_enabled = config.get('borrowing_enabled', False)
        max_ltv = config.get('max_ltv')
        if borrowing_enabled and not max_ltv:
            self.errors.append(f"Mode {mode_name}: max_ltv must be set when borrowing_enabled=true")
        elif not borrowing_enabled and max_ltv:
            self.warnings.append(f"Mode {mode_name}: max_ltv is set but borrowing_enabled=false")
        
        # Note: basis_trade_enabled is allowed for ETH share class (eth_basis strategy)
        
        # Check for deprecated parameters
        if 'use_flash_loan' in config:
            self.errors.append(f"Mode {mode_name}: use_flash_loan parameter is deprecated and should be removed")
        if 'unwind_mode' in config:
            self.errors.append(f"Mode {mode_name}: unwind_mode parameter is deprecated and should be removed") 
        
        # Check hedge venues consistency
        hedge_venues = config.get('hedge_venues', [])
        hedge_allocation = config.get('hedge_allocation', {})
        
        # Check for individual allocation fields (hedge_allocation_binance, etc.)
        individual_allocations = {}
        for venue in hedge_venues:
            allocation_key = f'hedge_allocation_{venue}'
            if allocation_key in config:
                individual_allocations[venue] = config[allocation_key]
        
        # Use individual allocations if available, otherwise use hedge_allocation dict
        if individual_allocations:
            hedge_allocation = individual_allocations
        
        if hedge_venues and not hedge_allocation:
            self.errors.append(f"Mode {mode_name}: hedge_venues specified but no hedge_allocation")
        
        if hedge_allocation and not hedge_venues:
            self.errors.append(f"Mode {mode_name}: hedge_allocation specified but no hedge_venues")
        
        # Check hedge allocation sums to 1.0
        if hedge_allocation:
            total_allocation = sum(hedge_allocation.values())
            if abs(total_allocation - 1.0) > 0.01:
                self.warnings.append(f"Mode {mode_name}: hedge_allocation sums to {total_allocation}, expected 1.0")
        
        # Validate component_config sections
        component_config = config.get('component_config', {})
        required_components = ['risk_monitor', 'exposure_monitor', 'pnl_calculator', 'strategy_manager', 'execution_manager', 'results_store', 'strategy_factory']
        
        for component in required_components:
            if component not in component_config:
                self.errors.append(f"Mode {mode_name}: Missing required component_config.{component}")
            else:
                # Validate component-specific fields
                self._validate_component_config(component, component_config[component], mode_name)
    
    def _validate_component_config(self, component: str, config: Dict[str, Any], mode_name: str):
        """Validate component-specific configuration."""
        if component == 'risk_monitor':
            # Validate risk_monitor config
            if 'enabled_risk_types' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.risk_monitor missing enabled_risk_types")
            if 'risk_limits' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.risk_monitor missing risk_limits")
        
        elif component == 'exposure_monitor':
            # Validate exposure_monitor config
            if 'exposure_currency' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.exposure_monitor missing exposure_currency")
            if 'track_assets' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.exposure_monitor missing track_assets")
            if 'conversion_methods' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.exposure_monitor missing conversion_methods")
        
        elif component == 'pnl_calculator':
            # Validate pnl_calculator config
            if 'attribution_types' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.pnl_calculator missing attribution_types")
            if 'reporting_currency' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.pnl_calculator missing reporting_currency")
            if 'reconciliation_tolerance' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.pnl_calculator missing reconciliation_tolerance")
        
        elif component == 'strategy_manager':
            # Validate strategy_manager config
            if 'strategy_type' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.strategy_manager missing strategy_type")
            if 'actions' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.strategy_manager missing actions")
            if 'rebalancing_triggers' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.strategy_manager missing rebalancing_triggers")
            if 'position_calculation' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.strategy_manager missing position_calculation")
        
        elif component == 'execution_manager':
            # Validate execution_manager config
            if 'supported_actions' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.execution_manager missing supported_actions")
            if 'action_mapping' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.execution_manager missing action_mapping")
        
        elif component == 'results_store':
            # Validate results_store config
            if 'result_types' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.results_store missing result_types")
            if 'balance_sheet_assets' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.results_store missing balance_sheet_assets")
            if 'pnl_attribution_types' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.results_store missing pnl_attribution_types")
        
        elif component == 'strategy_factory':
            # Validate strategy_factory config
            if 'timeout' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.strategy_factory missing timeout")
            if 'max_retries' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.strategy_factory missing max_retries")
            if 'validation_strict' not in config:
                self.errors.append(f"Mode {mode_name}: component_config.strategy_factory missing validation_strict")
    
    def _validate_share_class_strategy_compatibility(self, mode_config: Dict[str, Any], mode_name: str, share_class_configs: Dict[str, Any]):
        """Validate that strategy mode is compatible with its assigned share class."""
        
        mode_share_class = mode_config.get('share_class')
        if not mode_share_class:
            self.errors.append(f"Mode {mode_name}: Missing share_class field")
            return
        
        # Find the share class config
        share_class_config = None
        for share_class_name, config in share_class_configs.items():
            if config.get('share_class') == mode_share_class:
                share_class_config = config
                break
        
        if not share_class_config:
            self.errors.append(f"Mode {mode_name}: Share class '{mode_share_class}' not found in share class configs")
            return
        
        # Check if the strategy mode is supported by the share class
        supported_strategies = share_class_config.get('supported_strategies', [])
        if mode_name not in supported_strategies:
            self.errors.append(f"Mode {mode_name}: Strategy not supported by share class '{mode_share_class}'. Supported strategies: {supported_strategies}")
        
        # Validate base currency compatibility
        mode_asset = mode_config.get('asset')
        share_class_currency = share_class_config.get('base_currency')
        
        if mode_asset and share_class_currency:
            # USDT strategies should use USDT share class
            if 'usdt' in mode_name.lower() and share_class_currency != 'USDT':
                self.errors.append(f"Mode {mode_name}: USDT strategy should use USDT share class, not {share_class_currency}")
            
            # ETH strategies should use ETH share class  
            if 'eth' in mode_name.lower() and share_class_currency != 'ETH':
                self.errors.append(f"Mode {mode_name}: ETH strategy should use ETH share class, not {share_class_currency}")
        
        # Validate leverage compatibility
        mode_leverage = mode_config.get('leverage_enabled', False)
        share_class_leverage = share_class_config.get('leverage_supported', False)
        
        if mode_leverage and not share_class_leverage:
            self.errors.append(f"Mode {mode_name}: Leverage enabled but share class '{mode_share_class}' does not support leverage")
    
    def _validate_json_structure(self, config: Dict[str, Any], filename: str):
        """REMOVED: JSON configuration validation - configs eliminated."""
        # JSON configs eliminated - infrastructure handled by environment variables
        pass
    
    def _validate_mode_structure(self, config: Dict[str, Any], filename: str):
        """Validate mode configuration structure."""
        required_fields = [
            'mode', 'lending_enabled', 'staking_enabled',
            'basis_trade_enabled', 'share_class',
            'asset', 'target_apy', 'max_drawdown'
        ]
        
        for field in required_fields:
            if field not in config:
                self.errors.append(f"{filename}: Missing required field '{field}'")
    
    def _validate_venue_structure(self, config: Dict[str, Any], filename: str):
        """Validate venue configuration structure."""
        required_fields = ['venue', 'type']
        
        for field in required_fields:
            if field not in config:
                self.errors.append(f"{filename}: Missing required field '{field}'")
    
    def _validate_share_class_structure(self, config: Dict[str, Any], filename: str):
        """Validate share class configuration structure."""
        required_fields = ['share_class', 'type', 'base_currency', 'supported_strategies']
        
        for field in required_fields:
            if field not in config:
                self.errors.append(f"{filename}: Missing required field '{field}'")
    
    def _create_config_summary(self) -> Dict[str, Any]:
        """Create a summary of the current configuration."""
        return {
            'environment': self.environment,
            'modes_available': len(list((self.base_dir / "configs" / "modes").glob("*.yaml"))),
            'venues_available': len(list((self.base_dir / "configs" / "venues").glob("*.yaml"))),
            'share_classes_available': len(list((self.base_dir / "configs" / "share_classes").glob("*.yaml"))),
            'backtest_scenarios': len(list((self.base_dir / "configs" / "scenarios" / "backtest").glob("*.yaml"))),
            'live_scenarios': len(list((self.base_dir / "configs" / "scenarios" / "live").glob("*.yaml"))),
            'environment_variables_set': len([k for k, v in os.environ.items() if k.startswith('BASIS_') and v]),
            'validation_errors': len(self.errors),
            'validation_warnings': len(self.warnings)
        }
    
    def validate_data_directory(self) -> List[str]:
        """Validate data directory exists and is readable."""
        errors = []
        
        try:
            # Get data directory from environment variables
            data_dir = os.getenv('BASIS_DATA_DIR')
            if not data_dir:
                errors.append("BASIS_DATA_DIR environment variable not set")
                return errors
                
            data_path = Path(data_dir)
            
            if not data_path.exists():
                errors.append(f"Data directory does not exist: {data_dir}")
            elif not data_path.is_dir():
                errors.append(f"Data directory is not a directory: {data_dir}")
            elif not os.access(data_path, os.R_OK):
                errors.append(f"Data directory is not readable: {data_dir}")
            
            # Validate results directory
            results_dir = os.getenv('BASIS_RESULTS_DIR')
            if not results_dir:
                errors.append("BASIS_RESULTS_DIR environment variable not set")
                return errors
                
            results_path = Path(results_dir)
            
            if not results_path.exists():
                errors.append(f"Results directory does not exist: {results_dir}")
            elif not results_path.is_dir():
                errors.append(f"Results directory is not a directory: {results_dir}")
            elif not os.access(results_path, os.W_OK):
                errors.append(f"Results directory is not writable: {results_dir}")
                
        except Exception as e:
            errors.append(f"Data directory validation failed: {str(e)}")
        
        return errors
    
    def validate_data_files(self) -> List[str]:
        """Validate all required data files exist."""
        errors = []
        
        try:
            data_dir = Path(os.getenv('BASIS_DATA_DIR', './data'))
            start_date = os.getenv('BASIS_DATA_START_DATE', '2024-05-12')
            end_date = os.getenv('BASIS_DATA_END_DATE', '2025-09-18')
            
            # Check for required data files based on common patterns
            required_files = [
                'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_USDT_rates_*.csv',
                'blockchain_data/gas_prices/ethereum_gas_prices_*.csv',
                'execution_costs/execution_costs_lookup.json',
                'protocol_data/aave/risk_params/aave_v3_risk_parameters.json'
            ]
            
            for file_pattern in required_files:
                pattern_path = data_dir / file_pattern
                matching_files = list(pattern_path.parent.glob(pattern_path.name))
                if not matching_files:
                    errors.append(f"Required data file not found: {file_pattern}")
        
        except Exception as e:
            errors.append(f"Data file validation failed: {str(e)}")
        
        return errors
    
    def _validate_live_trading_variables(self):
        """Validate live trading environment variables."""
        logger.debug("Validating live trading environment variables...")
        
        # Live trading variables with defaults
        live_trading_vars = {
            'BASIS_LIVE_TRADING__ENABLED': os.getenv('BASIS_LIVE_TRADING__ENABLED', 'false'),
            'BASIS_LIVE_TRADING__READ_ONLY': os.getenv('BASIS_LIVE_TRADING__READ_ONLY', 'true'),
            'BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD': os.getenv('BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD', '100'),
            'BASIS_LIVE_TRADING__EMERGENCY_STOP_LOSS_PCT': os.getenv('BASIS_LIVE_TRADING__EMERGENCY_STOP_LOSS_PCT', '0.15'),
            'BASIS_LIVE_TRADING__HEARTBEAT_TIMEOUT_SECONDS': os.getenv('BASIS_LIVE_TRADING__HEARTBEAT_TIMEOUT_SECONDS', '300'),
            'BASIS_LIVE_TRADING__CIRCUIT_BREAKER_ENABLED': os.getenv('BASIS_LIVE_TRADING__CIRCUIT_BREAKER_ENABLED', 'true')
        }
        
        # Validate boolean variables
        boolean_vars = ['BASIS_LIVE_TRADING__ENABLED', 'BASIS_LIVE_TRADING__READ_ONLY', 'BASIS_LIVE_TRADING__CIRCUIT_BREAKER_ENABLED']
        for var in boolean_vars:
            value = live_trading_vars[var].lower()
            if value not in ['true', 'false']:
                self.errors.append(f"Invalid {var}: {live_trading_vars[var]}. Must be 'true' or 'false'")
        
        # Validate numeric variables
        try:
            max_trade_size = float(live_trading_vars['BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD'])
            if max_trade_size <= 0:
                self.errors.append(f"BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD must be positive, got: {max_trade_size}")
        except ValueError:
            self.errors.append(f"Invalid BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD: {live_trading_vars['BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD']}")
        
        try:
            stop_loss_pct = float(live_trading_vars['BASIS_LIVE_TRADING__EMERGENCY_STOP_LOSS_PCT'])
            if stop_loss_pct <= 0 or stop_loss_pct > 1:
                self.errors.append(f"BASIS_LIVE_TRADING__EMERGENCY_STOP_LOSS_PCT must be between 0 and 1, got: {stop_loss_pct}")
        except ValueError:
            self.errors.append(f"Invalid BASIS_LIVE_TRADING__EMERGENCY_STOP_LOSS_PCT: {live_trading_vars['BASIS_LIVE_TRADING__EMERGENCY_STOP_LOSS_PCT']}")
        
        try:
            heartbeat_timeout = int(live_trading_vars['BASIS_LIVE_TRADING__HEARTBEAT_TIMEOUT_SECONDS'])
            if heartbeat_timeout <= 0:
                self.errors.append(f"BASIS_LIVE_TRADING__HEARTBEAT_TIMEOUT_SECONDS must be positive, got: {heartbeat_timeout}")
        except ValueError:
            self.errors.append(f"Invalid BASIS_LIVE_TRADING__HEARTBEAT_TIMEOUT_SECONDS: {live_trading_vars['BASIS_LIVE_TRADING__HEARTBEAT_TIMEOUT_SECONDS']}")
        
        # Log current live trading configuration
        logger.info(f"Live trading configuration: enabled={live_trading_vars['BASIS_LIVE_TRADING__ENABLED']}, "
                   f"read_only={live_trading_vars['BASIS_LIVE_TRADING__READ_ONLY']}, "
                   f"max_trade_size=${live_trading_vars['BASIS_LIVE_TRADING__MAX_TRADE_SIZE_USD']}")

    def _get_file_pattern_for_requirement(self, requirement: str) -> Optional[str]:
        """Map data requirement to file pattern."""
        mapping = {
            'aave_lending_rates': 'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_USDT_rates_*.csv',
            'gas_costs': 'blockchain_data/gas_prices/ethereum_gas_prices_*.csv',
            'execution_costs': 'execution_costs/execution_costs_lookup.json',
            'aave_risk_params': 'protocol_data/aave/risk_params/aave_v3_risk_parameters.json',
            # Add more mappings as needed
        }
        return mapping.get(requirement)


def validate_configuration() -> ValidationResult:
    """Validate all configuration files and environment variables."""
    validator = ConfigValidator()
    return validator.validate_all()


def check_configuration_health() -> bool:
    """Quick health check for configuration."""
    result = validate_configuration()
    return result.is_valid


