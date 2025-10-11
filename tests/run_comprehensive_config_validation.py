#!/usr/bin/env python3
"""
Comprehensive Configuration and Environment Validation

This script validates that ALL configuration sources are properly loaded and integrated:
1. Base JSON configs (local.json, default.json)
2. Mode YAML configs (all strategy modes)
3. Venue YAML configs (all venues)
4. Share class YAML configs
5. Environment variables (env.unified and deploy/.env files)
6. Data availability and requirements
7. Configuration consistency and separation of concerns

Author: Implementation Team
Date: December 2024
"""

import sys
import os
import asyncio
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Set
import pandas as pd

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider
from basis_strategy_v1.core.event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine


class ComprehensiveConfigValidator:
    """Comprehensive validator for all configuration sources."""
    
    def __init__(self):
        # Create results file in tests directory
        self.results_file = os.path.join(os.path.dirname(__file__), 'tmp', 'comprehensive_config_validation_results.json')
        
        # Ensure tmp directory exists
        os.makedirs(os.path.dirname(self.results_file), exist_ok=True)
        
        self.results = {
            'base_configs': {},
            'mode_configs': {},
            'venue_configs': {},
            'share_class_configs': {},
            'env_variables': {},
            'data_requirements': {},
            'config_consistency': {},
            'separation_of_concerns': {},
            'errors': [],
            'warnings': []
        }
        
        # Define expected configuration files
        self.expected_files = {
            'base_configs': ['configs/local.json', 'configs/default.json'],
            'mode_configs': [
                'configs/modes/btc_basis.yaml',
                'configs/modes/eth_leveraged.yaml', 
                'configs/modes/eth_staking_only.yaml',
                'configs/modes/pure_lending.yaml',
                'configs/modes/usdt_market_neutral_no_leverage.yaml',
                'configs/modes/usdt_market_neutral.yaml'
            ],
            'venue_configs': [
                'configs/venues/aave_v3.yaml',
                'configs/venues/alchemy.yaml',
                'configs/venues/binance.yaml',
                'configs/venues/bybit.yaml',
                'configs/venues/etherfi.yaml',
                'configs/venues/okx.yaml',
                'configs/venues/lido.yaml',
                'configs/venues/morpho.yaml'
            ],
            'share_class_configs': [
                'configs/share_classes/eth_directional.yaml',
                'configs/share_classes/usdt_stable.yaml'
            ],
            'env_files': [
                'env.unified',
                'deploy/.env',
                'deploy/.env.dev',
                'deploy/.env.staging'
            ]
        }
    
    async def validate_all(self):
        """Run all configuration validation tests."""
        print("🔍 Starting comprehensive configuration and environment validation...")
        
        try:
            await self._validate_base_configs()
            await self._validate_mode_configs()
            await self._validate_venue_configs()
            await self._validate_share_class_configs()
            await self._validate_environment_variables()
            await self._validate_data_requirements()
            await self._validate_config_consistency()
            await self._validate_separation_of_concerns()
            self._generate_final_report()
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            self.results['errors'].append(f"Validation failed: {e}")
            self._save_results()
            raise
    
    async def _validate_base_configs(self):
        """Validate base JSON configuration files."""
        print("\n📋 Testing base JSON configuration files...")
        
        for config_file in self.expected_files['base_configs']:
            file_path = os.path.join(os.path.dirname(__file__), '..', config_file)
            
            try:
                if not os.path.exists(file_path):
                    self.results['base_configs'][config_file] = {
                        'status': 'error',
                        'error': f"File not found: {file_path}"
                    }
                    self.results['errors'].append(f"Base config file not found: {config_file}")
                    continue
                
                with open(file_path, 'r') as f:
                    config = json.load(f)
                
                # Validate required sections
                required_sections = ['environment', 'api', 'database', 'data', 'execution']
                missing_sections = [section for section in required_sections if section not in config]
                
                self.results['base_configs'][config_file] = {
                    'status': 'success',
                    'file_exists': True,
                    'valid_json': True,
                    'required_sections': {section: section in config for section in required_sections},
                    'missing_sections': missing_sections,
                    'config_keys': list(config.keys())
                }
                
                if missing_sections:
                    self.results['warnings'].append(f"Missing sections in {config_file}: {missing_sections}")
                
            except json.JSONDecodeError as e:
                self.results['base_configs'][config_file] = {
                    'status': 'error',
                    'error': f"Invalid JSON: {e}"
                }
                self.results['errors'].append(f"Invalid JSON in {config_file}: {e}")
            except Exception as e:
                self.results['base_configs'][config_file] = {
                    'status': 'error',
                    'error': str(e)
                }
                self.results['errors'].append(f"Error loading {config_file}: {e}")
        
        print(f"✅ Base config validation completed")
    
    async def _validate_mode_configs(self):
        """Validate mode YAML configuration files."""
        print("\n🎯 Testing mode YAML configuration files...")
        
        for config_file in self.expected_files['mode_configs']:
            file_path = os.path.join(os.path.dirname(__file__), '..', config_file)
            
            try:
                if not os.path.exists(file_path):
                    self.results['mode_configs'][config_file] = {
                        'status': 'error',
                        'error': f"File not found: {file_path}"
                    }
                    self.results['errors'].append(f"Mode config file not found: {config_file}")
                    continue
                
                with open(file_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Validate required fields
                required_fields = ['mode', 'share_class', 'data_requirements', 'position_deviation_threshold', 'enable_market_impact', 'time_throttle_interval']
                missing_fields = [field for field in required_fields if field not in config]
                
                # Validate data requirements
                data_requirements = config.get('data_requirements', [])
                if not isinstance(data_requirements, list) or len(data_requirements) == 0:
                    missing_fields.append('data_requirements (empty or not list)')
                
                # Validate component_config sections
                component_config = config.get('component_config', {})
                required_components = ['risk_monitor', 'exposure_monitor', 'pnl_calculator', 'strategy_manager', 'execution_manager', 'results_store', 'strategy_factory']
                component_config_status = {component: component in component_config for component in required_components}
                
                # Check strategy_manager config
                strategy_manager_config = component_config.get('strategy_manager', {})
                strategy_manager_fields = ['strategy_type', 'actions', 'rebalancing_triggers', 'position_calculation']
                strategy_manager_missing = [field for field in strategy_manager_fields if field not in strategy_manager_config]
                
                # Check strategy_factory config
                strategy_factory_config = component_config.get('strategy_factory', {})
                strategy_factory_fields = ['timeout', 'max_retries', 'validation_strict']
                strategy_factory_missing = [field for field in strategy_factory_fields if field not in strategy_factory_config]
                
                # Check other component configs
                risk_monitor_config = component_config.get('risk_monitor', {})
                risk_monitor_fields = ['enabled_risk_types', 'risk_limits']
                risk_monitor_missing = [field for field in risk_monitor_fields if field not in risk_monitor_config]
                
                exposure_monitor_config = component_config.get('exposure_monitor', {})
                exposure_monitor_fields = ['exposure_currency', 'track_assets', 'conversion_methods']
                exposure_monitor_missing = [field for field in exposure_monitor_fields if field not in exposure_monitor_config]
                
                pnl_calculator_config = component_config.get('pnl_calculator', {})
                pnl_calculator_fields = ['attribution_types', 'reporting_currency', 'reconciliation_tolerance']
                pnl_calculator_missing = [field for field in pnl_calculator_fields if field not in pnl_calculator_config]
                
                execution_manager_config = component_config.get('execution_manager', {})
                execution_manager_fields = ['supported_actions', 'action_mapping']
                execution_manager_missing = [field for field in execution_manager_fields if field not in execution_manager_config]
                
                results_store_config = component_config.get('results_store', {})
                results_store_fields = ['result_types', 'balance_sheet_assets', 'pnl_attribution_types']
                results_store_missing = [field for field in results_store_fields if field not in results_store_config]
                
                self.results['mode_configs'][config_file] = {
                    'status': 'success',
                    'file_exists': True,
                    'valid_yaml': True,
                    'required_fields': {field: field in config for field in required_fields},
                    'missing_fields': missing_fields,
                    'mode': config.get('mode'),
                    'share_class': config.get('share_class'),
                    'data_requirements_count': len(data_requirements),
                    'data_requirements': data_requirements,
                    'component_config': {
                        'present': 'component_config' in config,
                        'components_present': component_config_status,
                        'strategy_manager_missing_fields': strategy_manager_missing,
                        'strategy_factory_missing_fields': strategy_factory_missing,
                        'risk_monitor_missing_fields': risk_monitor_missing,
                        'exposure_monitor_missing_fields': exposure_monitor_missing,
                        'pnl_calculator_missing_fields': pnl_calculator_missing,
                        'execution_manager_missing_fields': execution_manager_missing,
                        'results_store_missing_fields': results_store_missing
                    }
                }
                
                if missing_fields:
                    self.results['warnings'].append(f"Missing fields in {config_file}: {missing_fields}")
                
            except yaml.YAMLError as e:
                self.results['mode_configs'][config_file] = {
                    'status': 'error',
                    'error': f"Invalid YAML: {e}"
                }
                self.results['errors'].append(f"Invalid YAML in {config_file}: {e}")
            except Exception as e:
                self.results['mode_configs'][config_file] = {
                    'status': 'error',
                    'error': str(e)
                }
                self.results['errors'].append(f"Error loading {config_file}: {e}")
        
        print(f"✅ Mode config validation completed")
    
    async def _validate_venue_configs(self):
        """Validate venue YAML configuration files."""
        print("\n🏢 Testing venue YAML configuration files...")
        
        for config_file in self.expected_files['venue_configs']:
            file_path = os.path.join(os.path.dirname(__file__), '..', config_file)
            
            try:
                if not os.path.exists(file_path):
                    self.results['venue_configs'][config_file] = {
                        'status': 'error',
                        'error': f"File not found: {file_path}"
                    }
                    self.results['errors'].append(f"Venue config file not found: {config_file}")
                    continue
                
                with open(file_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Validate required fields
                required_fields = ['venue', 'type', 'description']
                missing_fields = [field for field in required_fields if field not in config]
                
                self.results['venue_configs'][config_file] = {
                    'status': 'success',
                    'file_exists': True,
                    'valid_yaml': True,
                    'required_fields': {field: field in config for field in required_fields},
                    'missing_fields': missing_fields,
                    'venue': config.get('venue'),
                    'type': config.get('type'),
                    'config_keys': list(config.keys())
                }
                
                if missing_fields:
                    self.results['warnings'].append(f"Missing fields in {config_file}: {missing_fields}")
                
            except yaml.YAMLError as e:
                self.results['venue_configs'][config_file] = {
                    'status': 'error',
                    'error': f"Invalid YAML: {e}"
                }
                self.results['errors'].append(f"Invalid YAML in {config_file}: {e}")
            except Exception as e:
                self.results['venue_configs'][config_file] = {
                    'status': 'error',
                    'error': str(e)
                }
                self.results['errors'].append(f"Error loading {config_file}: {e}")
        
        print(f"✅ Venue config validation completed")
    
    async def _validate_share_class_configs(self):
        """Validate share class YAML configuration files."""
        print("\n💰 Testing share class YAML configuration files...")
        
        for config_file in self.expected_files['share_class_configs']:
            file_path = os.path.join(os.path.dirname(__file__), '..', config_file)
            
            try:
                if not os.path.exists(file_path):
                    self.results['share_class_configs'][config_file] = {
                        'status': 'error',
                        'error': f"File not found: {file_path}"
                    }
                    self.results['errors'].append(f"Share class config file not found: {config_file}")
                    continue
                
                with open(file_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Validate required fields
                required_fields = ['share_class', 'type', 'description', 'supported_strategies']
                missing_fields = [field for field in required_fields if field not in config]
                
                self.results['share_class_configs'][config_file] = {
                    'status': 'success',
                    'file_exists': True,
                    'valid_yaml': True,
                    'required_fields': {field: field in config for field in required_fields},
                    'missing_fields': missing_fields,
                    'share_class': config.get('share_class'),
                    'type': config.get('type'),
                    'supported_strategies': config.get('supported_strategies', [])
                }
                
                if missing_fields:
                    self.results['warnings'].append(f"Missing fields in {config_file}: {missing_fields}")
                
            except yaml.YAMLError as e:
                self.results['share_class_configs'][config_file] = {
                    'status': 'error',
                    'error': f"Invalid YAML: {e}"
                }
                self.results['errors'].append(f"Invalid YAML in {config_file}: {e}")
            except Exception as e:
                self.results['share_class_configs'][config_file] = {
                    'status': 'error',
                    'error': str(e)
                }
                self.results['errors'].append(f"Error loading {config_file}: {e}")
        
        print(f"✅ Share class config validation completed")
    
    async def _validate_environment_variables(self):
        """Validate environment variable files."""
        print("\n🌍 Testing environment variable files...")
        
        for env_file in self.expected_files['env_files']:
            file_path = os.path.join(os.path.dirname(__file__), '..', env_file)
            
            try:
                if not os.path.exists(file_path):
                    self.results['env_variables'][env_file] = {
                        'status': 'error',
                        'error': f"File not found: {file_path}"
                    }
                    self.results['errors'].append(f"Environment file not found: {env_file}")
                    continue
                
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Parse environment variables
                env_vars = {}
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
                
                # Check for critical environment variables
                critical_vars = [
                    'BASIS_ENVIRONMENT',
                    'BASIS_EXECUTION_MODE',
                    'BASIS_API__PORT',
                    # Component-specific environment variables
                    'DATA_LOAD_TIMEOUT',
                    'DATA_VALIDATION_STRICT',
                    'DATA_CACHE_SIZE',
                    'STRATEGY_MANAGER_TIMEOUT',
                    'STRATEGY_MANAGER_MAX_RETRIES',
                    'STRATEGY_FACTORY_TIMEOUT',
                    'STRATEGY_FACTORY_MAX_RETRIES',
                    # Redis removed - using in-memory cache only
                ]
                
                missing_critical = [var for var in critical_vars if var not in env_vars]
                
                self.results['env_variables'][env_file] = {
                    'status': 'success',
                    'file_exists': True,
                    'total_vars': len(env_vars),
                    'critical_vars': {var: var in env_vars for var in critical_vars},
                    'missing_critical': missing_critical,
                    'sample_vars': dict(list(env_vars.items())[:5])  # First 5 vars as sample
                }
                
                if missing_critical:
                    self.results['warnings'].append(f"Missing critical vars in {env_file}: {missing_critical}")
                
            except Exception as e:
                self.results['env_variables'][env_file] = {
                    'status': 'error',
                    'error': str(e)
                }
                self.results['errors'].append(f"Error loading {env_file}: {e}")
        
        print(f"✅ Environment variable validation completed")
    
    async def _validate_data_requirements(self):
        """Validate data requirements against available data."""
        print("\n📊 Testing data requirements against available data...")
        
        # Load all mode configs to get data requirements
        all_data_requirements = set()
        mode_requirements = {}
        
        for config_file in self.expected_files['mode_configs']:
            file_path = os.path.join(os.path.dirname(__file__), '..', config_file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    config = yaml.safe_load(f)
                    requirements = config.get('data_requirements', [])
                    mode_requirements[config.get('mode', config_file)] = requirements
                    all_data_requirements.update(requirements)
        
        # Check data directory structure
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        data_directories = []
        if os.path.exists(data_dir):
            data_directories = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
        
        # Map requirements to actual file paths based on DataProvider file maps
        requirement_mapping = {
            'eth_prices': 'market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_2020-01-01_2025-09-26.csv',
            'btc_prices': 'market_data/spot_prices/btc_usd/binance_BTCUSDT_1h_2024-01-01_2025-09-30.csv',
            'aave_lending_rates': [
                'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_weETH_rates_2024-05-12_2025-09-18_hourly.csv',
                'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_wstETH_rates_2024-01-01_2025-09-18_hourly.csv',
                'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_WETH_rates_2024-01-01_2025-09-18_hourly.csv',
                'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_USDT_rates_2024-01-01_2025-09-18_hourly.csv'
            ],
            'aave_risk_params': 'protocol_data/aave/risk_params/aave_v3_risk_parameters.json',
            'lst_market_prices': [
                'market_data/spot_prices/lst_eth_ratios/curve_weETHWETH_1h_2024-05-12_2025-09-27.csv',
                'market_data/spot_prices/lst_eth_ratios/uniswapv3_wstETHWETH_1h_2024-05-12_2025-09-27.csv'
            ],
            'gas_costs': [
                'blockchain_data/gas_prices/ethereum_gas_prices_enhanced_2024-01-01_2025-09-26.csv',
                'blockchain_data/gas_prices/ethereum_gas_prices_2024-01-01_2025-09-26.csv'
            ],
            'execution_costs': [
                'execution_costs/execution_cost_simulation_results.csv',
                'execution_costs/lookup_tables/execution_costs_lookup.json'
            ],
            'funding_rates': [
                'market_data/derivatives/funding_rates/binance_BTCUSDT_funding_rates_2024-01-01_2025-09-30.csv',
                'market_data/derivatives/funding_rates/bybit_BTCUSDT_funding_rates_2024-01-01_2025-09-30.csv',
                'market_data/derivatives/funding_rates/okx_BTCUSDT_funding_rates_2024-05-01_2025-09-07.csv',
                'market_data/derivatives/funding_rates/binance_ETHUSDT_funding_rates_2024-01-01_2025-09-26.csv',
                'market_data/derivatives/funding_rates/bybit_ETHUSDT_funding_rates_2024-01-01_2025-09-26.csv',
                'market_data/derivatives/funding_rates/okx_ETHUSDT_funding_rates_2024-05-01_2025-09-07.csv'
            ],
            'staking_rewards': [
                'protocol_data/staking/base_staking_yields_2024-01-01_2025-09-18_hourly.csv',
                'protocol_data/staking/base_yields/weeth_oracle_yields_2024-01-01_2025-09-18.csv',
                'protocol_data/staking/base_staking_yields_2024-01-01_2025-09-18.csv'
            ],
            'eigen_rewards': 'protocol_data/staking/restaking_final/etherfi_seasonal_rewards_2024-01-01_2025-09-18.csv',
            'ethfi_rewards': 'protocol_data/staking/restaking_final/etherfi_seasonal_rewards_2024-01-01_2025-09-18.csv'
        }
        
        data_availability = {}
        for requirement in all_data_requirements:
            if requirement in requirement_mapping:
                mapping = requirement_mapping[requirement]
                
                if isinstance(mapping, list):
                    # Handle multiple files
                    files_status = []
                    for file_path in mapping:
                        full_path = os.path.join(data_dir, file_path)
                        files_status.append({
                            'file': file_path,
                            'exists': os.path.exists(full_path),
                            'size': os.path.getsize(full_path) if os.path.exists(full_path) else 0
                        })
                    
                    data_availability[requirement] = {
                        'type': 'multiple_files',
                        'files': files_status,
                        'exists': any(f['exists'] for f in files_status),
                        'file_count': len([f for f in files_status if f['exists']])
                    }
                else:
                    # Handle single file
                    expected_path = os.path.join(data_dir, mapping)
                    data_availability[requirement] = {
                        'type': 'single_file',
                        'expected_path': expected_path,
                        'exists': os.path.exists(expected_path),
                        'size': os.path.getsize(expected_path) if os.path.exists(expected_path) else 0
                    }
        
        self.results['data_requirements'] = {
            'total_requirements': len(all_data_requirements),
            'unique_requirements': list(all_data_requirements),
            'mode_requirements': mode_requirements,
            'data_directories': data_directories,
            'requirement_mapping': requirement_mapping,
            'data_availability': data_availability
        }
        
        # Check for missing data
        missing_data = []
        for req, info in data_availability.items():
            if not info['exists']:
                missing_data.append(req)
        
        if missing_data:
            self.results['warnings'].append(f"Missing data files: {missing_data}")
        
        print(f"✅ Data requirements validation completed")
    
    async def _validate_config_consistency(self):
        """Validate consistency between different configuration sources."""
        print("\n🔗 Testing configuration consistency...")
        
        # Check mode-share class consistency
        mode_share_classes = {}
        share_class_strategies = {}
        
        # Load mode configs
        for config_file in self.expected_files['mode_configs']:
            file_path = os.path.join(os.path.dirname(__file__), '..', config_file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    config = yaml.safe_load(f)
                    mode = config.get('mode')
                    share_class = config.get('share_class')
                    if mode and share_class:
                        mode_share_classes[mode] = share_class
        
        # Load share class configs
        for config_file in self.expected_files['share_class_configs']:
            file_path = os.path.join(os.path.dirname(__file__), '..', config_file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    config = yaml.safe_load(f)
                    share_class = config.get('share_class')
                    strategies = config.get('supported_strategies', [])
                    if share_class:
                        share_class_strategies[share_class] = strategies
        
        # Check consistency
        consistency_issues = []
        for mode, share_class in mode_share_classes.items():
            if share_class in share_class_strategies:
                if mode not in share_class_strategies[share_class]:
                    consistency_issues.append(f"Mode {mode} not listed in {share_class} supported strategies")
            else:
                consistency_issues.append(f"Share class {share_class} not found in share class configs")
        
        self.results['config_consistency'] = {
            'mode_share_classes': mode_share_classes,
            'share_class_strategies': share_class_strategies,
            'consistency_issues': consistency_issues,
            'is_consistent': len(consistency_issues) == 0
        }
        
        if consistency_issues:
            self.results['warnings'].extend(consistency_issues)
        
        print(f"✅ Configuration consistency validation completed")
    
    async def _validate_separation_of_concerns(self):
        """Validate separation of concerns between configuration sources."""
        print("\n🎯 Testing separation of concerns...")
        
        # Check for duplication between base configs
        base_configs = {}
        for config_file in self.expected_files['base_configs']:
            file_path = os.path.join(os.path.dirname(__file__), '..', config_file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    base_configs[config_file] = json.load(f)
        
        # Check for overlapping keys between local.json and default.json
        if 'configs/local.json' in base_configs and 'configs/default.json' in base_configs:
            local_keys = set(base_configs['configs/local.json'].keys())
            default_keys = set(base_configs['configs/default.json'].keys())
            overlapping_keys = local_keys.intersection(default_keys)
            
            # Check if values are identical (potential duplication)
            identical_values = []
            for key in overlapping_keys:
                if base_configs['configs/local.json'][key] == base_configs['configs/default.json'][key]:
                    identical_values.append(key)
        
        # Check for strategy-specific config in base configs (should not be there)
        strategy_specific_keys = ['mode', 'share_class', 'data_requirements', 'target_apy', 'max_drawdown']
        base_config_strategy_keys = []
        
        for config_file, config in base_configs.items():
            for key in strategy_specific_keys:
                if key in config:
                    base_config_strategy_keys.append(f"{config_file}:{key}")
        
        self.results['separation_of_concerns'] = {
            'base_config_overlap': {
                'overlapping_keys': list(overlapping_keys) if 'overlapping_keys' in locals() else [],
                'identical_values': identical_values if 'identical_values' in locals() else [],
                'potential_duplication': len(identical_values) if 'identical_values' in locals() else 0
            },
            'base_config_strategy_keys': base_config_strategy_keys,
            'separation_violations': len(base_config_strategy_keys) > 0
        }
        
        if base_config_strategy_keys:
            self.results['warnings'].append(f"Strategy-specific keys found in base configs: {base_config_strategy_keys}")
        
        if 'identical_values' in locals() and identical_values:
            self.results['warnings'].append(f"Identical values in base configs (potential duplication): {identical_values}")
        
        print(f"✅ Separation of concerns validation completed")
    
    def _generate_final_report(self):
        """Generate final validation report."""
        print("\n📋 COMPREHENSIVE CONFIGURATION VALIDATION REPORT")
        print("=" * 60)
        
        # Count results
        total_errors = len(self.results['errors'])
        total_warnings = len(self.results['warnings'])
        
        print(f"📊 Summary:")
        print(f"  Errors: {total_errors}")
        print(f"  Warnings: {total_warnings}")
        
        if total_errors > 0:
            print("❌ Some critical validations failed!")
        else:
            print("✅ All critical validations passed!")
        
        # Detailed results
        print(f"\n📋 Base Configs: {len(self.results['base_configs'])} files")
        print(f"🎯 Mode Configs: {len(self.results['mode_configs'])} files")
        print(f"🏢 Venue Configs: {len(self.results['venue_configs'])} files")
        print(f"💰 Share Class Configs: {len(self.results['share_class_configs'])} files")
        print(f"🌍 Environment Files: {len(self.results['env_variables'])} files")
        print(f"📊 Data Requirements: {self.results['data_requirements'].get('total_requirements', 0)} unique requirements")
        
        # Save results
        self._save_results()
        
        if total_errors > 0:
            sys.exit(1)
    
    def _save_results(self):
        """Save results to file in tests directory."""
        with open(self.results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {self.results_file}")


async def main():
    """Main function."""
    validator = ComprehensiveConfigValidator()
    await validator.validate_all()


if __name__ == "__main__":
    asyncio.run(main())
