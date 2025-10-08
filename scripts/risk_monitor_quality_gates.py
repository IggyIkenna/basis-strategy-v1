"""
Risk Monitor Quality Gates

Comprehensive testing for Risk Monitor across all strategy modes.
Tests risk calculations, liquidation simulations, and mode-specific behavior.
"""

import asyncio
import logging
import pandas as pd
from typing import Dict, Any, List
from decimal import Decimal
import json
from pathlib import Path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

# Mock components for testing
class MockDataProvider:
    """Mock data provider for testing."""
    
    def __init__(self):
        self.aave_risk_params = {
            'emode': {
                'liquidation_thresholds': {
                    'weETH_WETH': 0.95,
                    'wstETH_WETH': 0.95
                },
                'liquidation_bonus': {
                    'weETH_WETH': 0.01,
                    'wstETH_WETH': 0.01
                },
                'max_ltv_limits': {
                    'weETH_WETH': 0.93,
                    'wstETH_WETH': 0.93
                }
            }
        }
    
    def get_aave_risk_params(self):
        return self.aave_risk_params
    
    def get_bybit_margin_requirements(self):
        return {
            'initial_margin_requirement': 0.15,
            'maintenance_margin_requirement': 0.10
        }
    
    def get_binance_margin_requirements(self):
        return {
            'initial_margin_requirement': 0.15,
            'maintenance_margin_requirement': 0.10
        }
    
    def get_okx_margin_requirements(self):
        return {
            'initial_margin_requirement': 0.15,
            'maintenance_margin_requirement': 0.10
        }

class MockPositionMonitor:
    """Mock position monitor for testing."""
    
    def __init__(self, execution_mode='backtest'):
        self.execution_mode = execution_mode

class MockExposureMonitor:
    """Mock exposure monitor for testing."""
    
    def __init__(self):
        pass

class RiskMonitorQualityGateValidator:
    """Quality gate validator for Risk Monitor."""
    
    def __init__(self):
        self.data_provider = MockDataProvider()
        self.position_monitor = MockPositionMonitor()
        self.exposure_monitor = MockExposureMonitor()
        
        # Test configurations for different modes
        self.test_configs = {
            'btc_basis': {
                'mode': 'btc_basis',
                'asset': 'BTC',
                'share_class': 'USDT',
                'margin_ratio_target': 0.8,
                'max_stake_spread_move': 0.03,
                'max_ltv': 0.85,
                'liquidation_threshold': 0.90
            },
            'pure_lending': {
                'mode': 'pure_lending',
                'asset': 'USDT',
                'share_class': 'USDT',
                'margin_ratio_target': 1.0,
                'max_stake_spread_move': 0.03,
                'max_ltv': 0.85,
                'liquidation_threshold': 0.90
            },
            'eth_leveraged': {
                'mode': 'eth_leveraged',
                'asset': 'ETH',
                'share_class': 'ETH',
                'lst_type': 'weeth',
                'margin_ratio_target': 1.0,
                'max_stake_spread_move': 0.02215,
                'max_ltv': 0.91,
                'liquidation_threshold': 0.95
            },
            'eth_staking_only': {
                'mode': 'eth_staking_only',
                'asset': 'ETH',
                'share_class': 'ETH',
                'lst_type': 'wsteth',
                'margin_ratio_target': 1.0,
                'max_stake_spread_move': 0.02215,
                'max_ltv': 0.91,
                'liquidation_threshold': 0.95
            },
            'usdt_market_neutral': {
                'mode': 'usdt_market_neutral',
                'asset': 'ETH',
                'share_class': 'USDT',
                'margin_ratio_target': 0.8,
                'max_stake_spread_move': 0.03,
                'max_ltv': 0.85,
                'liquidation_threshold': 0.90
            }
        }
        
        # Test exposure data scenarios
        self.test_exposure_data = {
            'safe_aave': {
                'timestamp': pd.Timestamp('2024-01-01 12:00:00', tz='UTC'),
                'aave_collateral': 100.0,
                'aave_debt': 50.0,
                'cex_positions': {
                    'binance': {
                        'current_margin': 10000.0,
                        'used_margin': 5000.0,
                        'position_value': 20000.0
                    }
                },
                'net_delta': 0.0,
                'token_equity_eth': 100.0
            },
            'critical_aave': {
                'timestamp': pd.Timestamp('2024-01-01 12:00:00', tz='UTC'),
                'aave_collateral': 100.0,
                'aave_debt': 95.0,  # High LTV
                'cex_positions': {},
                'net_delta': 0.0,
                'token_equity_eth': 100.0
            },
            'critical_cex': {
                'timestamp': pd.Timestamp('2024-01-01 12:00:00', tz='UTC'),
                'aave_collateral': 0.0,
                'aave_debt': 0.0,
                'cex_positions': {
                    'binance': {
                        'current_margin': 1000.0,  # Low margin
                        'used_margin': 500.0,
                        'position_value': 20000.0  # High exposure
                    }
                },
                'net_delta': 0.0,
                'token_equity_eth': 100.0
            },
            'high_delta_drift': {
                'timestamp': pd.Timestamp('2024-01-01 12:00:00', tz='UTC'),
                'aave_collateral': 0.0,
                'aave_debt': 0.0,
                'cex_positions': {},
                'net_delta': 10.0,  # High delta drift
                'token_equity_eth': 100.0
            }
        }
    
    async def validate_risk_monitor_initialization(self) -> Dict[str, Any]:
        """Test Risk Monitor initialization with different configurations."""
        print("🔍 Testing Risk Monitor Initialization...")
        
        results = {}
        
        try:
            from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor
            
            for mode, config in self.test_configs.items():
                try:
                    risk_monitor = RiskMonitor(
                        config=config,
                        position_monitor=self.position_monitor,
                        exposure_monitor=self.exposure_monitor,
                        data_provider=self.data_provider,
                        share_class=config['share_class'],
                        debug_mode=True
                    )
                    
                    # Validate mode-specific parameters
                    assert risk_monitor.mode == config['mode'], f"Mode mismatch: {risk_monitor.mode} != {config['mode']}"
                    assert risk_monitor.asset == config['asset'], f"Asset mismatch: {risk_monitor.asset} != {config['asset']}"
                    assert risk_monitor.share_class == config['share_class'], f"Share class mismatch: {risk_monitor.share_class} != {config['share_class']}"
                    assert risk_monitor.margin_ratio_target == config['margin_ratio_target'], f"Margin target mismatch: {risk_monitor.margin_ratio_target} != {config['margin_ratio_target']}"
                    assert risk_monitor.max_stake_spread_move == config['max_stake_spread_move'], f"Max stake spread mismatch: {risk_monitor.max_stake_spread_move} != {config['max_stake_spread_move']}"
                    
                    results[mode] = {
                        'status': 'PASS',
                        'message': f'Risk Monitor initialized successfully for {mode} mode'
                    }
                    
                except Exception as e:
                    results[mode] = {
                        'status': 'FAIL',
                        'message': f'Risk Monitor initialization failed for {mode} mode: {str(e)}'
                    }
        
        except Exception as e:
            results['import_error'] = {
                'status': 'FAIL',
                'message': f'Failed to import RiskMonitor: {str(e)}'
            }
        
        return results
    
    async def validate_risk_calculations(self) -> Dict[str, Any]:
        """Test risk calculations across different scenarios."""
        print("🔍 Testing Risk Calculations...")
        
        results = {}
        
        try:
            from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor
            
            # Test AAVE LTV risk calculation
            config = self.test_configs['eth_leveraged']
            risk_monitor = RiskMonitor(
                config=config,
                position_monitor=self.position_monitor,
                exposure_monitor=self.exposure_monitor,
                data_provider=self.data_provider,
                share_class=config['share_class'],
                debug_mode=True
            )
            
            # Test safe AAVE position
            safe_exposure = self.test_exposure_data['safe_aave']
            aave_risk = await risk_monitor.calculate_aave_ltv_risk(safe_exposure)
            
            assert aave_risk['level'] == 'safe', f"Expected safe level, got {aave_risk['level']}"
            assert aave_risk['value'] == 0.5, f"Expected LTV 0.5, got {aave_risk['value']}"
            
            # Test critical AAVE position
            critical_exposure = self.test_exposure_data['critical_aave']
            aave_risk_critical = await risk_monitor.calculate_aave_ltv_risk(critical_exposure)
            
            assert aave_risk_critical['level'] == 'critical', f"Expected critical level, got {aave_risk_critical['level']}"
            assert aave_risk_critical['value'] == 0.95, f"Expected LTV 0.95, got {aave_risk_critical['value']}"
            
            results['aave_ltv_calculation'] = {
                'status': 'PASS',
                'message': 'AAVE LTV risk calculation working correctly'
            }
            
        except Exception as e:
            results['aave_ltv_calculation'] = {
                'status': 'FAIL',
                'message': f'AAVE LTV risk calculation failed: {str(e)}'
            }
        
        # Test CEX margin risk calculation
        try:
            config = self.test_configs['btc_basis']
            risk_monitor = RiskMonitor(
                config=config,
                position_monitor=self.position_monitor,
                exposure_monitor=self.exposure_monitor,
                data_provider=self.data_provider,
                share_class=config['share_class'],
                debug_mode=True
            )
            
            # Test safe CEX position
            safe_exposure = self.test_exposure_data['safe_aave']
            cex_risk = await risk_monitor.calculate_cex_margin_risk(safe_exposure)
            
            assert cex_risk['level'] == 'safe', f"Expected safe level, got {cex_risk['level']}"
            
            # Test critical CEX position
            critical_exposure = self.test_exposure_data['critical_cex']
            cex_risk_critical = await risk_monitor.calculate_cex_margin_risk(critical_exposure)
            
            assert cex_risk_critical['level'] == 'critical', f"Expected critical level, got {cex_risk_critical['level']}"
            
            results['cex_margin_calculation'] = {
                'status': 'PASS',
                'message': 'CEX margin risk calculation working correctly'
            }
            
        except Exception as e:
            results['cex_margin_calculation'] = {
                'status': 'FAIL',
                'message': f'CEX margin risk calculation failed: {str(e)}'
            }
        
        return results
    
    async def validate_liquidation_simulations(self) -> Dict[str, Any]:
        """Test liquidation simulations."""
        print("🔍 Testing Liquidation Simulations...")
        
        results = {}
        
        try:
            from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor
            
            config = self.test_configs['eth_leveraged']
            risk_monitor = RiskMonitor(
                config=config,
                position_monitor=self.position_monitor,
                exposure_monitor=self.exposure_monitor,
                data_provider=self.data_provider,
                share_class=config['share_class'],
                debug_mode=True
            )
            
            # Test AAVE liquidation simulation
            critical_exposure = self.test_exposure_data['critical_aave']
            aave_liquidation = await risk_monitor.simulate_aave_liquidation(critical_exposure)
            
            assert 'overall_status' in aave_liquidation, "Missing overall_status in AAVE liquidation result"
            assert 'liquidation_penalty' in aave_liquidation, "Missing liquidation_penalty in AAVE liquidation result"
            
            # Test CEX liquidation simulation
            cex_liquidation = await risk_monitor.simulate_cex_liquidation(critical_exposure, 'binance')
            
            assert 'overall_status' in cex_liquidation, "Missing overall_status in CEX liquidation result"
            assert 'total_margin_lost' in cex_liquidation, "Missing total_margin_lost in CEX liquidation result"
            
            results['liquidation_simulations'] = {
                'status': 'PASS',
                'message': 'Liquidation simulations working correctly'
            }
            
        except Exception as e:
            results['liquidation_simulations'] = {
                'status': 'FAIL',
                'message': f'Liquidation simulations failed: {str(e)}'
            }
        
        return results
    
    async def validate_mode_specific_behavior(self) -> Dict[str, Any]:
        """Test mode-specific behavior and parameters."""
        print("🔍 Testing Mode-Specific Behavior...")
        
        results = {}
        
        try:
            from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor
            
            for mode, config in self.test_configs.items():
                try:
                    risk_monitor = RiskMonitor(
                        config=config,
                        position_monitor=self.position_monitor,
                        exposure_monitor=self.exposure_monitor,
                        data_provider=self.data_provider,
                        share_class=config['share_class'],
                        debug_mode=True
                    )
                    
                    # Test overall risk assessment
                    exposure_data = self.test_exposure_data['safe_aave']
                    risk_assessment = await risk_monitor.calculate_overall_risk(exposure_data)
                    
                    # Validate risk assessment structure
                    required_fields = ['level', 'timestamp', 'mode', 'asset', 'share_class', 
                                     'aave_ltv', 'cex_margin', 'delta_deviation', 'liquidation_terms']
                    
                    for field in required_fields:
                        assert field in risk_assessment, f"Missing required field: {field}"
                    
                    # Validate mode-specific fields
                    assert risk_assessment['mode'] == config['mode'], f"Mode mismatch in risk assessment"
                    assert risk_assessment['asset'] == config['asset'], f"Asset mismatch in risk assessment"
                    assert risk_assessment['share_class'] == config['share_class'], f"Share class mismatch in risk assessment"
                    
                    results[mode] = {
                        'status': 'PASS',
                        'message': f'Mode-specific behavior working correctly for {mode}'
                    }
                    
                except Exception as e:
                    results[mode] = {
                        'status': 'FAIL',
                        'message': f'Mode-specific behavior failed for {mode}: {str(e)}'
                    }
        
        except Exception as e:
            results['import_error'] = {
                'status': 'FAIL',
                'message': f'Failed to import RiskMonitor: {str(e)}'
            }
        
        return results
    
    async def validate_error_handling(self) -> Dict[str, Any]:
        """Test error handling and fail-fast behavior."""
        print("🔍 Testing Error Handling...")
        
        results = {}
        
        try:
            from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor, RiskMonitorError
            
            # Test missing dependencies
            try:
                RiskMonitor(
                    config=self.test_configs['btc_basis'],
                    position_monitor=None,  # Missing dependency
                    exposure_monitor=self.exposure_monitor,
                    data_provider=self.data_provider,
                    share_class='USDT',
                    debug_mode=True
                )
                results['missing_dependencies'] = {
                    'status': 'FAIL',
                    'message': 'Should have failed with missing position_monitor'
                }
            except RiskMonitorError as e:
                assert e.error_code == 'RISK-004', f"Expected RISK-004, got {e.error_code}"
                results['missing_dependencies'] = {
                    'status': 'PASS',
                    'message': 'Correctly failed with missing dependencies'
                }
            
            # Test invalid exposure data
            config = self.test_configs['btc_basis']
            risk_monitor = RiskMonitor(
                config=config,
                position_monitor=self.position_monitor,
                exposure_monitor=self.exposure_monitor,
                data_provider=self.data_provider,
                share_class=config['share_class'],
                debug_mode=True
            )
            
            try:
                invalid_exposure = {'timestamp': pd.Timestamp.now()}
                await risk_monitor.calculate_aave_ltv_risk(invalid_exposure)
                results['invalid_exposure_data'] = {
                    'status': 'FAIL',
                    'message': 'Should have failed with invalid exposure data'
                }
            except RiskMonitorError as e:
                assert e.error_code == 'RISK-005', f"Expected RISK-005, got {e.error_code}"
                results['invalid_exposure_data'] = {
                    'status': 'PASS',
                    'message': 'Correctly failed with invalid exposure data'
                }
            
        except Exception as e:
            results['error_handling'] = {
                'status': 'FAIL',
                'message': f'Error handling test failed: {str(e)}'
            }
        
        return results
    
    async def validate_debug_logging(self) -> Dict[str, Any]:
        """Test debug logging functionality."""
        print("🔍 Testing Debug Logging...")
        
        results = {}
        
        try:
            from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor
            
            config = self.test_configs['eth_leveraged']
            risk_monitor = RiskMonitor(
                config=config,
                position_monitor=self.position_monitor,
                exposure_monitor=self.exposure_monitor,
                data_provider=self.data_provider,
                share_class=config['share_class'],
                debug_mode=True
            )
            
            # Test risk assessment with debug logging
            exposure_data = self.test_exposure_data['safe_aave']
            risk_assessment = await risk_monitor.calculate_overall_risk(exposure_data)
            
            # Check if debug logger was created
            assert hasattr(risk_monitor, 'debug_logger'), "Debug logger not created"
            assert risk_monitor.debug_mode == True, "Debug mode not enabled"
            
            # Check if log file exists
            log_file = Path('backend/logs/risk_monitor.log')
            if log_file.exists():
                results['debug_logging'] = {
                    'status': 'PASS',
                    'message': 'Debug logging working correctly'
                }
            else:
                results['debug_logging'] = {
                    'status': 'FAIL',
                    'message': 'Debug log file not created'
                }
            
        except Exception as e:
            results['debug_logging'] = {
                'status': 'FAIL',
                'message': f'Debug logging test failed: {str(e)}'
            }
        
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all quality gate tests."""
        print("🚦 RISK MONITOR QUALITY GATES")
        print("=" * 50)
        
        all_results = {}
        
        # Run all test categories
        test_categories = [
            ('initialization', self.validate_risk_monitor_initialization),
            ('risk_calculations', self.validate_risk_calculations),
            ('liquidation_simulations', self.validate_liquidation_simulations),
            ('mode_specific_behavior', self.validate_mode_specific_behavior),
            ('error_handling', self.validate_error_handling),
            ('debug_logging', self.validate_debug_logging)
        ]
        
        for category_name, test_func in test_categories:
            try:
                category_results = await test_func()
                all_results[category_name] = category_results
            except Exception as e:
                all_results[category_name] = {
                    'error': f'Test category {category_name} failed: {str(e)}'
                }
        
        return all_results

async def main():
    """Run Risk Monitor quality gates."""
    validator = RiskMonitorQualityGateValidator()
    results = await validator.run_all_tests()
    
    # Print results
    print("\n" + "=" * 50)
    print("🚦 RISK MONITOR QUALITY GATES RESULTS")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    
    for category, category_results in results.items():
        print(f"\n📊 {category.upper().replace('_', ' ')}:")
        print("-" * 30)
        
        if isinstance(category_results, dict):
            for test_name, test_result in category_results.items():
                if isinstance(test_result, dict) and 'status' in test_result:
                    total_tests += 1
                    if test_result['status'] == 'PASS':
                        passed_tests += 1
                        print(f"  ✅ {test_name}: {test_result['message']}")
                    else:
                        print(f"  ❌ {test_name}: {test_result['message']}")
                else:
                    print(f"  ⚠️  {test_name}: {test_result}")
        else:
            print(f"  ⚠️  {category}: {category_results}")
    
    print(f"\n📈 SUMMARY:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {total_tests - passed_tests}")
    print(f"  Success Rate: {(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "  Success Rate: N/A")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
