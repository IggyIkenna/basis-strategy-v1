#!/usr/bin/env python3
"""
Simple validation script that tests config and data without requiring environment variables.

This script focuses on testing the core functionality without the full environment setup.
"""

import sys
import os
import asyncio
import json
import tempfile
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

import pandas as pd
from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider
from basis_strategy_v1.core.event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine


class SimpleValidator:
    """Simple validator that tests core functionality without environment variables."""
    
    def __init__(self):
        # Create results file in tests directory
        self.results_file = os.path.join(os.path.dirname(__file__), 'tmp', 'simple_validation_results.json')
        
        # Ensure tmp directory exists
        os.makedirs(os.path.dirname(self.results_file), exist_ok=True)
        
        self.results = {
            'config_validation': {},
            'data_validation': {},
            'integration_tests': {},
            'errors': [],
            'warnings': []
        }
        
        # Test configs for different modes
        self.test_configs = {
            'pure_lending': {
                'mode': 'pure_lending',
                'share_class': 'USDT',
                'initial_capital': 100000,
                'execution_mode': 'backtest',
                'data': {'data_dir': '../data/'},
                'data_requirements': ['aave_lending_rates', 'usdt_prices', 'gas_costs', 'execution_costs', 'aave_risk_params']
            },
            'btc_basis': {
                'mode': 'btc_basis',
                'share_class': 'USDT',
                'initial_capital': 100000,
                'execution_mode': 'backtest',
                'data': {'data_dir': '../data/'},
                'data_requirements': ['btc_prices', 'btc_futures_prices', 'funding_rates', 'gas_costs', 'execution_costs']
            },
            'eth_leveraged': {
                'mode': 'eth_leveraged',
                'share_class': 'ETH',
                'initial_capital': 100000,
                'execution_mode': 'backtest',
                'data': {'data_dir': '../data/'},
                'data_requirements': ['eth_prices', 'weeth_prices', 'aave_lending_rates', 'staking_rewards', 'eigen_rewards', 'gas_costs', 'execution_costs', 'aave_risk_params', 'lst_market_prices']
            }
        }
    
    async def validate_all(self):
        """Run all validation tests."""
        print("🔍 Starting simple config and data validation...")
        
        try:
            await self._validate_data_loading()
            await self._validate_engine_integration()
            self._generate_final_report()
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            self.results['errors'].append(f"Validation failed: {e}")
            self._save_results()
            raise
    
    async def _validate_data_loading(self):
        """Test data availability and loading."""
        print("\n📊 Testing data availability and loading...")
        
        data_loading_results = {}
        
        for mode_name, test_config in self.test_configs.items():
            print(f"  Testing data loading for mode: {mode_name}")
            
            try:
                # Create data provider
                data_provider = DataProvider(
                    data_dir=test_config.get('data', {}).get('data_dir', 'data/'),
                    mode=mode_name,
                    execution_mode='backtest',
                    config=test_config
                )
                
                # Test data loading
                data_provider._load_data_for_mode()
                
                # Test getting market data snapshot
                test_timestamp = pd.Timestamp('2024-06-01 12:00:00', tz='UTC')
                data = data_provider.get_market_data_snapshot(test_timestamp)
                
                data_loading_results[mode_name] = {
                    'status': 'success',
                    'data_loaded': data is not None and len(data) > 1,
                    'data_keys': list(data.keys()) if data is not None else [],
                    'data_count': len(data) if data is not None else 0,
                    'has_market_data': any(key.endswith('_price') or key.endswith('_apy') for key in data.keys()) if data is not None else False
                }
                
                if data is None or len(data) <= 1:
                    self.results['warnings'].append(f"No market data loaded for mode: {mode_name}")
                
            except Exception as e:
                data_loading_results[mode_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                self.results['errors'].append(f"Data loading failed for {mode_name}: {e}")
        
        self.results['data_validation'] = data_loading_results
        print(f"✅ Data validation completed. Tested {len(data_loading_results)} modes")
    
    async def _validate_engine_integration(self):
        """Test EventDrivenStrategyEngine integration."""
        print("\n🔧 Testing EventDrivenStrategyEngine integration...")
        
        engine_results = {}
        
        for mode_name, test_config in self.test_configs.items():
            print(f"  Testing engine initialization for mode: {mode_name}")
            
            try:
                # Initialize engine
                engine = EventDrivenStrategyEngine(test_config)
                
                # Test component initialization
                components_status = {
                    'data_provider': engine.data_provider is not None,
                    'position_monitor': engine.position_monitor is not None,
                    'exposure_monitor': engine.exposure_monitor is not None,
                    'risk_monitor': engine.risk_monitor is not None,
                    'strategy_manager': engine.strategy_manager is not None,
                    'cex_execution_manager': engine.cex_execution_manager is not None,
                    'onchain_execution_manager': engine.onchain_execution_manager is not None,
                    'pnl_calculator': engine.pnl_calculator is not None,
                    'event_logger': engine.event_logger is not None
                }
                
                # Test engine status
                status = await engine.get_status()
                
                engine_results[mode_name] = {
                    'status': 'success',
                    'components_initialized': components_status,
                    'all_components_active': all(components_status.values()),
                    'engine_status': status
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
                        
                        engine_results[mode_name]['backtest_test'] = {
                            'status': 'success',
                            'timestep_processed': True,
                            'results_updated': len(results['pnl_history']) > 0
                        }
                    else:
                        engine_results[mode_name]['backtest_test'] = {'status': 'no_data'}
                        
                except Exception as e:
                    engine_results[mode_name]['backtest_test'] = {
                        'status': 'error',
                        'error': str(e)
                    }
                
            except Exception as e:
                engine_results[mode_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                self.results['errors'].append(f"Engine integration failed for {mode_name}: {e}")
        
        self.results['integration_tests'] = engine_results
        print(f"✅ Engine integration tests completed. Tested {len(engine_results)} modes")
    
    def _generate_final_report(self):
        """Generate final validation report."""
        print("\n📋 VALIDATION REPORT")
        print("=" * 50)
        
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
    validator = SimpleValidator()
    await validator.validate_all()


if __name__ == "__main__":
    asyncio.run(main())
