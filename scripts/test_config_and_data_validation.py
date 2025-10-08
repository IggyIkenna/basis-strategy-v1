#!/usr/bin/env python3
"""
Comprehensive config and data validation script for backtesting.
Tests config loading, schema validation, and data availability.
"""

import sys
import os
import asyncio
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

# Add backend to path
sys.path.append('backend/src')

from basis_strategy_v1.infrastructure.config.config_validator import ConfigValidator
from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider
from basis_strategy_v1.core.event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine


class ConfigDataValidator:
    """Comprehensive validator for config and data."""
    
    def __init__(self):
        self.config_validator = ConfigValidator()
        self.results = {
            'config_validation': {},
            'data_validation': {},
            'integration_tests': {},
            'errors': [],
            'warnings': []
        }
    
    async def validate_all(self):
        """Run all validation tests."""
        print("🔍 Starting comprehensive config and data validation...")
        
        # 1. Test config loading and validation
        await self._validate_config_loading()
        
        # 2. Test data availability and loading
        await self._validate_data_availability()
        
        # 3. Test integration with EventDrivenStrategyEngine
        await self._validate_engine_integration()
        
        # 4. Generate report
        self._generate_report()
    
    async def _validate_config_loading(self):
        """Validate config loading and schema validation."""
        print("\n📋 Testing config loading and validation...")
        
        try:
            # Test base config loading
            base_config_path = Path("configs/local.json")
            if base_config_path.exists():
                with open(base_config_path) as f:
                    base_config = json.load(f)
                self.results['config_validation']['base_config'] = {
                    'status': 'loaded',
                    'keys': list(base_config.keys()),
                    'has_required_sections': all(key in base_config for key in ['api', 'database', 'redis', 'data'])
                }
            else:
                self.results['config_validation']['base_config'] = {'status': 'missing'}
                self.results['errors'].append(f"Base config not found: {base_config_path}")
            
            # Test scenario configs
            scenario_configs = {}
            modes_dir = Path("configs/modes")
            if modes_dir.exists():
                for mode_file in modes_dir.glob("*.yaml"):
                    try:
                        with open(mode_file) as f:
                            mode_config = yaml.safe_load(f)
                        scenario_configs[mode_file.stem] = {
                            'status': 'loaded',
                            'mode': mode_config.get('mode'),
                            'share_class': mode_config.get('share_class'),
                            'data_requirements': mode_config.get('data_requirements', []),
                            'has_target_apy': 'target_apy' in mode_config,
                            'has_max_drawdown': 'max_drawdown' in mode_config
                        }
                    except Exception as e:
                        scenario_configs[mode_file.stem] = {'status': 'error', 'error': str(e)}
                        self.results['errors'].append(f"Error loading {mode_file}: {e}")
            
            self.results['config_validation']['scenario_configs'] = scenario_configs
            
            # Test venue configs
            venue_configs = {}
            venues_dir = Path("configs/venues")
            if venues_dir.exists():
                for venue_file in venues_dir.glob("*.yaml"):
                    try:
                        with open(venue_file) as f:
                            venue_config = yaml.safe_load(f)
                        venue_configs[venue_file.stem] = {
                            'status': 'loaded',
                            'venue_type': venue_config.get('venue_type'),
                            'has_api_config': 'api' in venue_config
                        }
                    except Exception as e:
                        venue_configs[venue_file.stem] = {'status': 'error', 'error': str(e)}
                        self.results['errors'].append(f"Error loading {venue_file}: {e}")
            
            self.results['config_validation']['venue_configs'] = venue_configs
            
            print(f"✅ Config validation completed. Found {len(scenario_configs)} scenario configs, {len(venue_configs)} venue configs")
            
        except Exception as e:
            self.results['errors'].append(f"Config validation failed: {e}")
            print(f"❌ Config validation failed: {e}")
    
    async def _validate_data_availability(self):
        """Validate data availability and loading."""
        print("\n📊 Testing data availability and loading...")
        
        try:
            # Test data directory structure
            data_dir = Path("data")
            if not data_dir.exists():
                self.results['errors'].append("Data directory not found")
                return
            
            # Check key data directories
            key_dirs = [
                'market_data', 'protocol_data', 'blockchain_data', 
                'execution_costs', 'manual_sources'
            ]
            
            data_structure = {}
            for dir_name in key_dirs:
                dir_path = data_dir / dir_name
                if dir_path.exists():
                    files = list(dir_path.rglob("*"))
                    data_structure[dir_name] = {
                        'exists': True,
                        'file_count': len(files),
                        'sample_files': [f.name for f in files[:5]]  # First 5 files
                    }
                else:
                    data_structure[dir_name] = {'exists': False}
                    self.results['warnings'].append(f"Missing data directory: {dir_name}")
            
            self.results['data_validation']['data_structure'] = data_structure
            
            # Test DataProvider for each mode
            modes = ['pure_lending', 'btc_basis', 'eth_leveraged', 'usdt_market_neutral']
            data_loading_results = {}
            
            for mode in modes:
                try:
                    print(f"  Testing data loading for mode: {mode}")
                    
                    # Create a minimal config for testing
                    test_config = {
                        'mode': mode,
                        'share_class': 'USDT',
                        'initial_capital': 100000,
                        'execution_mode': 'backtest',
                        'data_dir': 'data/'
                    }
                    
                    # Test DataProvider initialization
                    data_provider = DataProvider(
                        data_dir='data/',
                        mode=mode,
                        execution_mode='backtest',
                        config=test_config
                    )
                    
                    # Test data loading
                    data_provider._load_data_for_mode()
                    
                    # Test getting market data snapshot
                    test_timestamp = pd.Timestamp('2024-06-01 12:00:00', tz='UTC')
                    data = data_provider.get_market_data_snapshot(test_timestamp)
                    
                    data_loading_results[mode] = {
                        'status': 'success',
                        'data_loaded': data is not None and len(data) > 1,  # More than just timestamp
                        'data_keys': list(data.keys()) if data is not None else [],
                        'data_count': len(data) if data is not None else 0,
                        'has_market_data': any(key.endswith('_price') or key.endswith('_apy') for key in data.keys()) if data is not None else False
                    }
                    
                    if data is None or len(data) <= 1:
                        self.results['warnings'].append(f"No market data loaded for mode: {mode}")
                    
                except Exception as e:
                    data_loading_results[mode] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    self.results['errors'].append(f"Data loading failed for {mode}: {e}")
            
            self.results['data_validation']['data_loading'] = data_loading_results
            
            print(f"✅ Data validation completed. Tested {len(modes)} modes")
            
        except Exception as e:
            self.results['errors'].append(f"Data validation failed: {e}")
            print(f"❌ Data validation failed: {e}")
    
    async def _validate_engine_integration(self):
        """Test integration with EventDrivenStrategyEngine."""
        print("\n🔧 Testing EventDrivenStrategyEngine integration...")
        
        try:
            # Test engine initialization for each mode
            modes = ['pure_lending', 'btc_basis', 'eth_leveraged']
            engine_results = {}
            
            for mode in modes:
                try:
                    print(f"  Testing engine initialization for mode: {mode}")
                    
                    # Create test config
                    test_config = {
                        'mode': mode,
                        'share_class': 'USDT',
                        'initial_capital': 100000,
                        'execution_mode': 'backtest',
                        'data_dir': 'data/'
                    }
                    
                    # Test engine initialization
                    engine = EventDrivenStrategyEngine(test_config)
                    
                    # Test component initialization
                    components_status = {
                        'data_provider': hasattr(engine, 'data_provider'),
                        'position_monitor': hasattr(engine, 'position_monitor'),
                        'exposure_monitor': hasattr(engine, 'exposure_monitor'),
                        'risk_monitor': hasattr(engine, 'risk_monitor'),
                        'strategy_manager': hasattr(engine, 'strategy_manager'),
                        'cex_execution_manager': hasattr(engine, 'cex_execution_manager'),
                        'onchain_execution_manager': hasattr(engine, 'onchain_execution_manager'),
                        'pnl_calculator': hasattr(engine, 'pnl_calculator'),
                        'event_logger': hasattr(engine, 'event_logger')
                    }
                    
                    # Test status method
                    status = await engine.get_status()
                    
                    engine_results[mode] = {
                        'status': 'success',
                        'components_initialized': components_status,
                        'all_components_active': all(components_status.values()),
                        'engine_status': status,
                        'config_sections': list(engine.config.keys())
                    }
                    
                    # Test a short backtest (if data is available)
                    try:
                        engine.data_provider._load_data_for_mode()
                        test_timestamp = pd.Timestamp('2024-06-01 12:00:00', tz='UTC')
                        data = engine.data_provider.get_market_data_snapshot(test_timestamp)
                        if data is not None and len(data) > 1:
                            # Test timestep processing
                            results = {
                                'pnl_history': [],
                                'events': [],
                                'positions': [],
                                'exposures': [],
                                'risks': []
                            }
                            
                            # Process one timestep
                            await engine._process_timestep(test_timestamp, data, results)
                            
                            engine_results[mode]['backtest_test'] = {
                                'status': 'success',
                                'timestep_processed': True,
                                'results_updated': len(results['pnl_history']) > 0
                            }
                        else:
                            engine_results[mode]['backtest_test'] = {'status': 'no_data'}
                    except Exception as e:
                        engine_results[mode]['backtest_test'] = {
                            'status': 'error',
                            'error': str(e)
                        }
                        self.results['warnings'].append(f"Backtest test failed for {mode}: {e}")
                    
                except Exception as e:
                    engine_results[mode] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    self.results['errors'].append(f"Engine initialization failed for {mode}: {e}")
            
            self.results['integration_tests']['engine_tests'] = engine_results
            
            print(f"✅ Engine integration tests completed. Tested {len(modes)} modes")
            
        except Exception as e:
            self.results['errors'].append(f"Engine integration test failed: {e}")
            print(f"❌ Engine integration test failed: {e}")
    
    def _generate_report(self):
        """Generate comprehensive validation report."""
        print("\n📋 VALIDATION REPORT")
        print("=" * 50)
        
        # Summary
        total_errors = len(self.results['errors'])
        total_warnings = len(self.results['warnings'])
        
        print(f"📊 Summary:")
        print(f"  Errors: {total_errors}")
        print(f"  Warnings: {total_warnings}")
        
        if total_errors == 0:
            print("✅ All critical validations passed!")
        else:
            print("❌ Some critical validations failed!")
        
        # Config validation results
        print(f"\n📋 Config Validation:")
        config_results = self.results['config_validation']
        
        if 'base_config' in config_results:
            base_status = config_results['base_config']['status']
            print(f"  Base Config: {'✅' if base_status == 'loaded' else '❌'} {base_status}")
        
        if 'scenario_configs' in config_results:
            scenario_count = len([k for k, v in config_results['scenario_configs'].items() if v['status'] == 'loaded'])
            total_scenarios = len(config_results['scenario_configs'])
            print(f"  Scenario Configs: ✅ {scenario_count}/{total_scenarios} loaded")
        
        if 'venue_configs' in config_results:
            venue_count = len([k for k, v in config_results['venue_configs'].items() if v['status'] == 'loaded'])
            total_venues = len(config_results['venue_configs'])
            print(f"  Venue Configs: ✅ {venue_count}/{total_venues} loaded")
        
        # Data validation results
        print(f"\n📊 Data Validation:")
        data_results = self.results['data_validation']
        
        if 'data_structure' in data_results:
            existing_dirs = len([k for k, v in data_results['data_structure'].items() if v.get('exists', False)])
            total_dirs = len(data_results['data_structure'])
            print(f"  Data Directories: ✅ {existing_dirs}/{total_dirs} exist")
        
        if 'data_loading' in data_results:
            successful_modes = len([k for k, v in data_results['data_loading'].items() if v['status'] == 'success'])
            total_modes = len(data_results['data_loading'])
            print(f"  Data Loading: ✅ {successful_modes}/{total_modes} modes successful")
        
        # Integration test results
        print(f"\n🔧 Integration Tests:")
        integration_results = self.results['integration_tests']
        
        if 'engine_tests' in integration_results:
            successful_engines = len([k for k, v in integration_results['engine_tests'].items() if v['status'] == 'success'])
            total_engines = len(integration_results['engine_tests'])
            print(f"  Engine Initialization: ✅ {successful_engines}/{total_engines} modes successful")
        
        # Errors and warnings
        if self.results['errors']:
            print(f"\n❌ Errors:")
            for error in self.results['errors']:
                print(f"  - {error}")
        
        if self.results['warnings']:
            print(f"\n⚠️  Warnings:")
            for warning in self.results['warnings']:
                print(f"  - {warning}")
        
        # Save detailed report
        report_path = "validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        return total_errors == 0


async def main():
    """Main validation function."""
    validator = ConfigDataValidator()
    success = await validator.validate_all()
    
    if success:
        print("\n🎉 All validations passed! System is ready for backtesting.")
        return 0
    else:
        print("\n💥 Some validations failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
