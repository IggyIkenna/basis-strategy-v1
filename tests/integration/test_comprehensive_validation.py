#!/usr/bin/env python3
"""
Comprehensive Integration Validation Tests

This test suite validates the complete integration of config loading, data availability,
and EventDrivenStrategyEngine functionality across all strategy modes.

Author: Agent B
Date: December 2024
"""

import sys
import os
import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import pytest

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'src'))

from basis_strategy_v1.infrastructure.config.config_loader import ConfigLoader
from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider
from basis_strategy_v1.core.event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine


class TestComprehensiveValidation:
    """Comprehensive validation tests for config, data, and engine integration."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.config_loader = ConfigLoader()
        
        # Create temp directory for test results
        self.temp_dir = tempfile.mkdtemp(prefix='basis_strategy_v1_test_')
        self.results_file = os.path.join(self.temp_dir, 'comprehensive_validation_results.json')
        
    def teardown_method(self):
        """Cleanup after each test."""
        # Clean up temp files
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_config_loading_comprehensive(self):
        """Test comprehensive config loading for all modes."""
        print("\n📋 Testing comprehensive config loading...")
        
        # Test base config loading
        base_config = self.config_loader.get_base_config()
        assert base_config is not None
        assert 'environment' in base_config
        assert 'api' in base_config
        assert 'data' in base_config
        
        # Test mode configs
        mode_configs = self.config_loader.get_all_mode_configs()
        assert len(mode_configs) > 0
        
        # Test venue configs
        venue_configs = self.config_loader.get_all_venue_configs()
        assert len(venue_configs) > 0
        
        # Test combined configs for each mode
        for mode_name in mode_configs.keys():
            combined_config = self.config_loader.get_complete_config(mode=mode_name)
            assert combined_config is not None
            assert combined_config['mode'] == mode_name
            assert 'share_class' in combined_config
            assert 'data_requirements' in combined_config
            
        print(f"✅ Config loading successful for {len(mode_configs)} modes")
    
    @pytest.mark.asyncio
    async def test_data_availability_comprehensive(self):
        """Test comprehensive data availability for all modes."""
        print("\n📊 Testing comprehensive data availability...")
        
        mode_configs = self.config_loader.get_all_mode_configs()
        data_loading_results = {}
        
        for mode_name in mode_configs.keys():
            print(f"  Testing data loading for mode: {mode_name}")
            
            try:
                # Load combined config
                test_config = self.config_loader.load_combined_config(mode_name)
                
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
                
                assert data is not None, f"No data loaded for mode: {mode_name}"
                assert len(data) > 1, f"No market data loaded for mode: {mode_name}"
                
            except Exception as e:
                data_loading_results[mode_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                pytest.fail(f"Data loading failed for {mode_name}: {e}")
        
        print(f"✅ Data availability successful for {len(data_loading_results)} modes")
        
        # Save results to temp file
        with open(self.results_file, 'w') as f:
            json.dump({'data_loading': data_loading_results}, f, indent=2)
    
    @pytest.mark.asyncio
    async def test_engine_integration_comprehensive(self):
        """Test comprehensive EventDrivenStrategyEngine integration."""
        print("\n🔧 Testing comprehensive engine integration...")
        
        mode_configs = self.config_loader.get_all_mode_configs()
        engine_results = {}
        
        for mode_name in mode_configs.keys():
            print(f"  Testing engine initialization for mode: {mode_name}")
            
            try:
                # Load combined config
                test_config = self.config_loader.load_combined_config(mode_name)
                
                # Initialize engine
                engine = EventDrivenStrategyEngine(test_config)
                assert engine is not None
                assert engine.mode == mode_name
                
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
                
                assert all(components_status.values()), f"Not all components initialized for {mode_name}"
                
                # Test engine status
                status = await engine.get_status()
                assert status['mode'] == mode_name
                assert status['share_class'] == test_config['share_class']
                assert status['execution_mode'] == 'backtest'
                
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
                pytest.fail(f"Engine integration failed for {mode_name}: {e}")
        
        print(f"✅ Engine integration successful for {len(engine_results)} modes")
        
        # Save results to temp file
        with open(self.results_file, 'w') as f:
            json.dump({'engine_tests': engine_results}, f, indent=2)
    
    @pytest.mark.asyncio
    async def test_end_to_end_validation(self):
        """Test complete end-to-end validation workflow."""
        print("\n🚀 Testing end-to-end validation workflow...")
        
        # Run all validation tests
        await self.test_config_loading_comprehensive()
        await self.test_data_availability_comprehensive()
        await self.test_engine_integration_comprehensive()
        
        # Verify results file was created
        assert os.path.exists(self.results_file), "Results file was not created"
        
        # Load and validate results
        with open(self.results_file, 'r') as f:
            results = json.load(f)
        
        assert 'engine_tests' in results, "Engine test results not found"
        
        # Count successful tests
        successful_modes = sum(1 for mode_result in results['engine_tests'].values() 
                             if mode_result.get('status') == 'success')
        total_modes = len(results['engine_tests'])
        
        print(f"✅ End-to-end validation completed: {successful_modes}/{total_modes} modes successful")
        
        # Assert that at least some modes are working
        assert successful_modes > 0, "No modes passed end-to-end validation"
    
    def test_results_file_location(self):
        """Test that results file is created in the correct location."""
        # This test ensures the results file is created in the temp directory
        # and not in the project root
        assert self.temp_dir.startswith('/tmp/') or self.temp_dir.startswith(tempfile.gettempdir())
        assert 'basis_strategy_v1_test_' in self.temp_dir
        assert not os.path.exists('validation_report.json'), "Results file should not be in project root"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s"])
