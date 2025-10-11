#!/usr/bin/env python3
"""
Monitor Quality Gates Validation Script

Tests Position Monitor and Exposure Monitor across all strategy modes:
- Position collection from all venues (wallet, CEX, perps, AAVE)
- Exposure calculation with proper asset filtering
- Net delta aggregation in share class and primary asset terms
- Venue breakdown for strategy rebalancing decisions
"""

import asyncio
import sys
import os
import time
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple
import json

# Add backend to path
sys.path.append('backend/src')

from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
from basis_strategy_v1.core.strategies.components.exposure_monitor import ExposureMonitor
from basis_strategy_v1.core.math.pnl_calculator import PnLCalculator
from basis_strategy_v1.infrastructure.config.config_manager import get_config_manager


class MonitorQualityGates:
    """Validates Position Monitor and Exposure Monitor quality gates."""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        self.config_manager = get_config_manager()
        
        # Test data for all strategy modes
        self.test_positions = self._create_comprehensive_test_data()
        self.test_market_data = self._create_test_market_data()
        
    def _create_comprehensive_test_data(self) -> Dict:
        """Create comprehensive test position data covering all venues and assets."""
        return {
            'wallet': {
                # Primary assets
                'BTC': 0.5,                    # On-chain wallet BTC
                'ETH': 3.0,                    # On-chain wallet ETH
                'USDT': 5000.0,                # On-chain wallet USDT
                
                # ETH derivatives
                'weETH': 1.0,                  # On-chain wallet weETH
                'wstETH': 0.5,                 # On-chain wallet wstETH
                'aWeETH': 0.3,                 # On-chain wallet aWeETH (AAVE token)
                'variableDebtWETH': 0.1,       # On-chain wallet debt token
                
                # USDT derivatives
                'aUSDT': 1000.0,               # On-chain wallet aUSDT (AAVE token)
                
                # Other assets (should be ignored in most modes)
                'USDC': 2000.0,                # On-chain wallet USDC
                'DAI': 1500.0,                 # On-chain wallet DAI
            },
            'cex_accounts': {
                'binance': {
                    'BTC': 0.2,                # CEX spot BTC
                    'ETH': 1.0,                # CEX spot ETH
                    'USDT': 2000.0,            # CEX spot USDT
                    'USDC': 1000.0,            # CEX spot USDC
                },
                'bybit': {
                    'BTC': 0.1,                # More CEX spot BTC
                    'ETH': 0.5,                # More CEX spot ETH
                    'USDT': 1000.0,            # More CEX spot USDT
                },
                'okx': {
                    'BTC': 0.05,               # More CEX spot BTC
                    'ETH': 0.3,                # More CEX spot ETH
                    'USDT': 500.0,             # More CEX spot USDT
                }
            },
            'perp_positions': {
                'binance': {
                    'BTCUSDT': {
                        'size': 0.15,          # CEX perp BTC
                        'entry_price': 50000.0
                    },
                    'ETHUSDT': {
                        'size': 0.8,           # CEX perp ETH
                        'entry_price': 3000.0
                    }
                },
                'bybit': {
                    'BTCUSDT': {
                        'size': 0.1,           # More CEX perp BTC
                        'entry_price': 50000.0
                    },
                    'ETHUSDT': {
                        'size': 0.4,           # More CEX perp ETH
                        'entry_price': 3000.0
                    }
                }
            }
        }
    
    def _create_test_market_data(self) -> Dict:
        """Create comprehensive test market data."""
        return {
            'eth_usd_price': 3000.0,
            'btc_usd_price': 50000.0,
            'usdt_usd_price': 1.0,
            'usdc_usd_price': 1.0,
            'dai_usd_price': 1.0,
            
            # ETH derivatives
            'weeth_eth_oracle': 1.05,          # weETH/ETH oracle price
            'wsteth_eth_oracle': 1.02,         # wstETH/ETH oracle price
            'weeth_liquidity_index': 1.02,     # AAVE liquidity index for aWeETH
            'weth_borrow_index': 1.01,         # AAVE borrow index for debt
            
            # USDT derivatives
            'usdt_liquidity_index': 1.01,      # AAVE liquidity index for aUSDT
        }
    
    def _create_mock_components(self):
        """Create mock components for testing."""
        class MockDataProvider:
            def __init__(self, test_market_data):
                self.test_market_data = test_market_data
                
            def get_market_data_snapshot(self, timestamp):
                return self.test_market_data
        
        class MockPositionMonitor:
            def __init__(self, test_positions):
                self.test_positions = test_positions
                
            def get_snapshot(self):
                return self.test_positions
        
        return MockDataProvider(self.test_market_data), MockPositionMonitor(self.test_positions)
    
    async def validate_position_monitor(self) -> Dict[str, Any]:
        """Validate Position Monitor quality gates."""
        print("📊 Validating Position Monitor Quality Gates...")
        results = {}
        
        try:
            # Test position monitor initialization
            print("  Testing Position Monitor initialization...")
            config = {'mode': 'pure_lending', 'asset': 'USDT'}
            position_monitor = PositionMonitor(
                config=config,
                execution_mode='backtest',
                initial_capital=100000.0,
                share_class='USDT',
                debug_mode=True
            )
            
            # Test position snapshot collection
            print("  Testing position snapshot collection...")
            snapshot = position_monitor.get_snapshot()
            
            # Validate snapshot structure
            required_keys = ['wallet', 'cex_accounts', 'perp_positions']
            snapshot_valid = all(key in snapshot for key in required_keys)
            
            results['position_monitor_init'] = {
                'status': 'PASS' if snapshot_valid else 'FAIL',
                'snapshot_keys': list(snapshot.keys()),
                'has_wallet': 'wallet' in snapshot,
                'has_cex_accounts': 'cex_accounts' in snapshot,
                'has_perp_positions': 'perp_positions' in snapshot
            }
            
            print(f"    ✅ Position Monitor: {'PASS' if snapshot_valid else 'FAIL'}")
            
            # Test debug logging
            print("  Testing debug logging...")
            log_file = Path('backend/logs/position_monitor.log')
            log_exists = log_file.exists()
            
            results['position_monitor_debug'] = {
                'status': 'PASS' if log_exists else 'FAIL',
                'log_file_exists': log_exists
            }
            
            print(f"    ✅ Debug Logging: {'PASS' if log_exists else 'FAIL'}")
            
        except Exception as e:
            results['position_monitor_init'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"    ❌ Position Monitor: ERROR - {e}")
        
        return results
    
    async def validate_exposure_monitor_all_modes(self) -> Dict[str, Any]:
        """Validate Exposure Monitor across all strategy modes."""
        print("🎯 Validating Exposure Monitor - All Strategy Modes...")
        results = {}
        
        # Define all strategy modes to test
        modes = [
            {'mode': 'btc_basis', 'asset': 'BTC', 'share_class': 'USDT'},
            {'mode': 'eth_leveraged', 'asset': 'ETH', 'share_class': 'ETH'},
            {'mode': 'eth_staking_only', 'asset': 'ETH', 'share_class': 'ETH'},
            {'mode': 'pure_lending', 'asset': 'USDT', 'share_class': 'USDT'},
            {'mode': 'usdt_market_neutral', 'asset': 'ETH', 'share_class': 'USDT'},
            {'mode': 'usdt_market_neutral_no_leverage', 'asset': 'ETH', 'share_class': 'USDT'},
        ]
        
        for strategy in modes:
            mode = strategy['mode']
            asset = strategy['asset']
            share_class = strategy['share_class']
            
            print(f"  Testing {mode.upper()} (Asset: {asset}, Share Class: {share_class})...")
            
            try:
                # Create exposure monitor for this strategy
                config = {'mode': mode, 'asset': asset}
                data_provider, position_monitor = self._create_mock_components()
                
                exposure_monitor = ExposureMonitor(
                    config=config,
                    share_class=share_class,
                    position_monitor=position_monitor,
                    data_provider=data_provider,
                    debug_mode=True
                )
                
                # Test exposure calculation
                timestamp = pd.Timestamp('2024-01-01 12:00:00')
                result = exposure_monitor.calculate_exposure(
                    timestamp, 
                    self.test_positions, 
                    self.test_market_data
                )
                
                # Validate result structure
                required_keys = [
                    'timestamp', 'share_class', 'primary_asset', 'mode',
                    'exposures', 'net_delta_share_class', 'net_delta_primary_asset',
                    'total_value_usd'
                ]
                result_valid = all(key in result for key in required_keys)
                
                # Validate asset filtering
                expected_primary_asset = asset
                actual_primary_asset = result.get('primary_asset')
                asset_filtering_valid = actual_primary_asset == expected_primary_asset
                
                # Validate net delta calculation
                net_delta_primary = result.get('net_delta_primary_asset', 0)
                net_delta_share_class = result.get('net_delta_share_class', 0)
                
                # Check if net delta calculation is correct
                # For ETH strategies, net delta should include all ETH derivatives
                # For BTC strategies, net delta should include all BTC derivatives  
                # For USDT strategies, net delta should include all USDT derivatives
                calculated_net_delta = 0
                for asset_name, exposure in result.get('exposures', {}).items():
                    if exposure:
                        if expected_primary_asset == 'BTC':
                            calculated_net_delta += exposure.get('exposure_btc', 0)
                        elif expected_primary_asset == 'ETH':
                            calculated_net_delta += exposure.get('exposure_eth', 0)
                        elif expected_primary_asset == 'USDT':
                            calculated_net_delta += exposure.get('exposure_usdt', 0)
                
                net_delta_valid = abs(calculated_net_delta - net_delta_primary) < 0.001
                
                # Validate venue breakdown
                venue_breakdown_valid = True
                for asset_name, exposure in result.get('exposures', {}).items():
                    if exposure and expected_primary_asset in asset_name:
                        venue_breakdown = exposure.get('venue_breakdown', {})
                        required_venue_keys = [
                            'on_chain_wallet', 'cex_spot', 'cex_perps', 
                            'aave_tokens', 'aave_debt'
                        ]
                        if not all(key in venue_breakdown for key in required_venue_keys):
                            venue_breakdown_valid = False
                            break
                
                # Calculate test score
                test_score = sum([
                    result_valid,
                    asset_filtering_valid,
                    net_delta_valid,
                    venue_breakdown_valid
                ])
                
                results[f'exposure_monitor_{mode}'] = {
                    'status': 'PASS' if test_score == 4 else 'FAIL',
                    'result_structure': result_valid,
                    'asset_filtering': asset_filtering_valid,
                    'net_delta_calculation': net_delta_valid,
                    'venue_breakdown': venue_breakdown_valid,
                    'test_score': f"{test_score}/4",
                    'primary_asset': actual_primary_asset,
                    'net_delta_primary': net_delta_primary,
                    'net_delta_share_class': net_delta_share_class,
                    'total_value_usd': result.get('total_value_usd', 0)
                }
                
                status_icon = "✅" if test_score == 4 else "❌"
                print(f"    {status_icon} {mode}: {test_score}/4 tests passed")
                
            except Exception as e:
                results[f'exposure_monitor_{mode}'] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                print(f"    ❌ {mode}: ERROR - {e}")
        
        return results
    
    async def validate_asset_filtering_logic(self) -> Dict[str, Any]:
        """Validate asset filtering logic across all modes."""
        print("🔍 Validating Asset Filtering Logic...")
        results = {}
        
        # Test cases for asset filtering
        test_cases = [
            {
                'mode': 'btc_basis',
                'asset': 'BTC',
                'share_class': 'USDT',
                'expected_assets': ['BTC'],
                'ignored_assets': ['ETH', 'USDT', 'weETH', 'aWeETH']
            },
            {
                'mode': 'eth_leveraged',
                'asset': 'ETH',
                'share_class': 'ETH',
                'expected_assets': ['ETH', 'weETH', 'wstETH', 'aWeETH', 'variableDebtWETH'],
                'ignored_assets': ['BTC', 'USDT', 'aUSDT']
            },
            {
                'mode': 'pure_lending',
                'asset': 'USDT',
                'share_class': 'USDT',
                'expected_assets': ['USDT', 'aUSDT'],
                'ignored_assets': ['BTC', 'ETH', 'weETH', 'aWeETH']
            }
        ]
        
        for test_case in test_cases:
            mode = test_case['mode']
            asset = test_case['asset']
            share_class = test_case['share_class']
            expected_assets = test_case['expected_assets']
            ignored_assets = test_case['ignored_assets']
            
            print(f"  Testing asset filtering for {mode}...")
            
            try:
                # Create exposure monitor
                config = {'mode': mode, 'asset': asset}
                data_provider, position_monitor = self._create_mock_components()
                
                exposure_monitor = ExposureMonitor(
                    config=config,
                    share_class=share_class,
                    position_monitor=position_monitor,
                    data_provider=data_provider,
                    debug_mode=False
                )
                
                # Calculate exposure
                timestamp = pd.Timestamp('2024-01-01 12:00:00')
                result = exposure_monitor.calculate_exposure(
                    timestamp, 
                    self.test_positions, 
                    self.test_market_data
                )
                
                # Check which assets are present in exposures
                present_assets = list(result.get('exposures', {}).keys())
                
                # Validate expected assets are present
                expected_present = all(exp_asset in present_assets for exp_asset in expected_assets)
                
                # Validate ignored assets are not present
                ignored_absent = all(ign_asset not in present_assets for ign_asset in ignored_assets)
                
                filtering_valid = expected_present and ignored_absent
                
                results[f'asset_filtering_{mode}'] = {
                    'status': 'PASS' if filtering_valid else 'FAIL',
                    'expected_assets_present': expected_present,
                    'ignored_assets_absent': ignored_absent,
                    'present_assets': present_assets,
                    'expected_assets': expected_assets,
                    'ignored_assets': ignored_assets
                }
                
                status_icon = "✅" if filtering_valid else "❌"
                print(f"    {status_icon} {mode}: Expected assets present, ignored assets absent")
                
            except Exception as e:
                results[f'asset_filtering_{mode}'] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                print(f"    ❌ {mode}: ERROR - {e}")
        
        return results
    
    async def validate_venue_breakdown_accuracy(self) -> Dict[str, Any]:
        """Validate venue breakdown accuracy for strategy rebalancing."""
        print("🏢 Validating Venue Breakdown Accuracy...")
        results = {}
        
        # Test with known position data
        test_positions = {
            'wallet': {'BTC': 0.3, 'ETH': 2.0},
            'cex_accounts': {
                'binance': {'BTC': 0.2, 'ETH': 1.0},
                'bybit': {'BTC': 0.1, 'ETH': 0.5}
            },
            'perp_positions': {
                'binance': {
                    'BTCUSDT': {'size': 0.15, 'entry_price': 50000.0},
                    'ETHUSDT': {'size': 0.8, 'entry_price': 3000.0}
                }
            }
        }
        
        test_cases = [
            {
                'mode': 'btc_basis',
                'asset': 'BTC',
                'expected_breakdown': {
                    'on_chain_wallet': 0.3,
                    'cex_spot': 0.3,  # 0.2 + 0.1
                    'cex_perps': 0.15
                }
            },
            {
                'mode': 'eth_leveraged',
                'asset': 'ETH',
                'expected_breakdown': {
                    'on_chain_wallet': 2.0,
                    'cex_spot': 1.5,  # 1.0 + 0.5
                    'cex_perps': 0.8
                }
            }
        ]
        
        for test_case in test_cases:
            mode = test_case['mode']
            asset = test_case['asset']
            expected_breakdown = test_case['expected_breakdown']
            
            print(f"  Testing venue breakdown for {mode}...")
            
            try:
                # Create exposure monitor
                config = {'mode': mode, 'asset': asset}
                data_provider, position_monitor = self._create_mock_components()
                
                exposure_monitor = ExposureMonitor(
                    config=config,
                    share_class='USDT' if mode == 'btc_basis' else 'ETH',
                    position_monitor=position_monitor,
                    data_provider=data_provider,
                    debug_mode=False
                )
                
                # Calculate exposure
                timestamp = pd.Timestamp('2024-01-01 12:00:00')
                result = exposure_monitor.calculate_exposure(
                    timestamp, 
                    test_positions, 
                    self.test_market_data
                )
                
                # Get venue breakdown for primary asset
                primary_asset_exposure = result.get('exposures', {}).get(asset, {})
                venue_breakdown = primary_asset_exposure.get('venue_breakdown', {})
                
                # Validate venue breakdown accuracy
                breakdown_accurate = True
                for venue, expected_value in expected_breakdown.items():
                    actual_value = venue_breakdown.get(venue, 0)
                    if abs(actual_value - expected_value) > 0.001:
                        breakdown_accurate = False
                        break
                
                results[f'venue_breakdown_{mode}'] = {
                    'status': 'PASS' if breakdown_accurate else 'FAIL',
                    'expected_breakdown': expected_breakdown,
                    'actual_breakdown': venue_breakdown,
                    'breakdown_accurate': breakdown_accurate
                }
                
                status_icon = "✅" if breakdown_accurate else "❌"
                print(f"    {status_icon} {mode}: Venue breakdown accurate")
                
            except Exception as e:
                results[f'venue_breakdown_{mode}'] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                print(f"    ❌ {mode}: ERROR - {e}")
        
        return results
    
    async def validate_pnl_calculator(self) -> Dict[str, Any]:
        """Validate P&L calculator quality gates."""
        print("💰 Validating P&L Calculator Quality Gates...")
        results = {}
        
        try:
            # Test P&L calculator initialization
            print("  Testing P&L calculator initialization...")
            config = {'mode': 'pure_lending', 'asset': 'USDT'}
            
            pnl_calculator = PnLCalculator(
                config=config,
                share_class='USDT',
                initial_capital=100000.0
            )
            
            results['pnl_calculator_init'] = {
                'status': 'PASS',
                'share_class': pnl_calculator.share_class,
                'initial_capital': pnl_calculator.initial_capital
            }
            
            print(f"    ✅ P&L Calculator initialization: PASS")
            
            # Test P&L calculation with mock exposure data
            print("  Testing P&L calculation with mock data...")
            
            # Mock current exposure with aUSDT growth
            current_exposure = {
                'total_value_usd': 100050.0,  # $50 growth
                'exposures': {
                    'aUSDT': {
                        'underlying_balance': 100050.0,  # Growing underlying balance
                        'exposure_usd': 100050.0
                    }
                }
            }
            
            # Mock previous exposure
            previous_exposure = {
                'total_value_usd': 100000.0,
                'exposures': {
                    'aUSDT': {
                        'underlying_balance': 100000.0,
                        'exposure_usd': 100000.0
                    }
                }
            }
            
            timestamp = pd.Timestamp('2024-06-01 12:00:00', tz='UTC')
            pnl_data = await pnl_calculator.calculate_pnl(
                current_exposure=current_exposure,
                previous_exposure=previous_exposure,
                timestamp=timestamp
            )
            
            # Validate P&L calculation
            balance_based_pnl = pnl_data['balance_based']['pnl_cumulative']
            attribution_pnl = pnl_data['attribution']['pnl_cumulative']
            
            pnl_calculation_valid = (
                balance_based_pnl > 0 and  # Should have positive P&L
                abs(balance_based_pnl - 50.0) < 1.0 and  # Should be ~$50
                'reconciliation' in pnl_data and
                pnl_data['reconciliation']['passed']  # Reconciliation should pass
            )
            
            results['pnl_calculation'] = {
                'status': 'PASS' if pnl_calculation_valid else 'FAIL',
                'balance_based_pnl': balance_based_pnl,
                'attribution_pnl': attribution_pnl,
                'reconciliation_passed': pnl_data['reconciliation']['passed'],
                'calculation_valid': pnl_calculation_valid
            }
            
            if pnl_calculation_valid:
                print(f"    ✅ P&L calculation: PASS (P&L: ${balance_based_pnl:.2f})")
            else:
                print(f"    ❌ P&L calculation: FAIL")
            
            # Test error code propagation
            print("  Testing error code propagation...")
            
            try:
                # Test with invalid exposure data
                invalid_exposure = {'invalid': 'data'}
                await pnl_calculator.calculate_pnl(
                    current_exposure=invalid_exposure,
                    timestamp=timestamp
                )
                
                results['error_propagation'] = {
                    'status': 'FAIL',
                    'error': 'Should have failed with invalid data'
                }
                
            except Exception as e:
                # Should raise PnLCalculatorError with error code
                if hasattr(e, 'error_code') and e.error_code.startswith('PNL-'):
                    results['error_propagation'] = {
                        'status': 'PASS',
                        'error_code': e.error_code
                    }
                    print(f"    ✅ Error propagation: PASS (code: {e.error_code})")
                else:
                    results['error_propagation'] = {
                        'status': 'FAIL',
                        'error': f'Wrong error type: {type(e).__name__}'
                    }
                    print(f"    ❌ Error propagation: FAIL")
            
        except Exception as e:
            results['pnl_calculator_init'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"    ❌ P&L Calculator: ERROR - {e}")
        
        return results
    
    def generate_monitor_report(self, position_results: Dict, exposure_results: Dict, 
                              filtering_results: Dict, venue_results: Dict, pnl_results: Dict = None) -> bool:
        """Generate comprehensive monitor quality gates report."""
        print("\n" + "="*80)
        print("📊 MONITOR QUALITY GATES VALIDATION REPORT")
        print("="*80)
        
        # Position Monitor Results
        print(f"\n📊 POSITION MONITOR QUALITY GATES:")
        print("-" * 80)
        
        position_passed = 0
        position_total = 0
        
        for test_name, result in position_results.items():
            status = result.get('status', 'UNKNOWN')
            print(f"{test_name:<40} {status:<10}")
            
            position_total += 1
            if status == 'PASS':
                position_passed += 1
        
        # Exposure Monitor Results
        print(f"\n🎯 EXPOSURE MONITOR QUALITY GATES:")
        print("-" * 80)
        
        exposure_passed = 0
        exposure_total = 0
        
        for test_name, result in exposure_results.items():
            status = result.get('status', 'UNKNOWN')
            test_score = result.get('test_score', 'N/A')
            print(f"{test_name:<40} {status:<10} {test_score}")
            
            exposure_total += 1
            if status == 'PASS':
                exposure_passed += 1
        
        # Asset Filtering Results
        print(f"\n🔍 ASSET FILTERING QUALITY GATES:")
        print("-" * 80)
        
        filtering_passed = 0
        filtering_total = 0
        
        for test_name, result in filtering_results.items():
            status = result.get('status', 'UNKNOWN')
            print(f"{test_name:<40} {status:<10}")
            
            filtering_total += 1
            if status == 'PASS':
                filtering_passed += 1
        
        # Venue Breakdown Results
        print(f"\n🏢 VENUE BREAKDOWN QUALITY GATES:")
        print("-" * 80)
        
        venue_passed = 0
        venue_total = 0
        
        for test_name, result in venue_results.items():
            status = result.get('status', 'UNKNOWN')
            print(f"{test_name:<40} {status:<10}")
            
            venue_total += 1
            if status == 'PASS':
                venue_passed += 1
        
        # P&L Calculator Results
        pnl_passed = 0
        pnl_total = 0
        
        if pnl_results:
            print(f"\n💰 P&L CALCULATOR QUALITY GATES:")
            print("-" * 80)
            
            for test_name, result in pnl_results.items():
                status = result.get('status', 'UNKNOWN')
                print(f"{test_name:<40} {status:<10}")
                
                pnl_total += 1
                if status == 'PASS':
                    pnl_passed += 1
        
        # Overall Summary
        print(f"\n🎯 OVERALL MONITOR QUALITY GATES SUMMARY:")
        print("-" * 80)
        
        total_tests = position_total + exposure_total + filtering_total + venue_total + pnl_total
        total_passed = position_passed + exposure_passed + filtering_passed + venue_passed + pnl_passed
        
        print(f"Position Monitor: {position_passed}/{position_total} tests passed")
        print(f"Exposure Monitor: {exposure_passed}/{exposure_total} tests passed")
        print(f"Asset Filtering: {filtering_passed}/{filtering_total} tests passed")
        print(f"Venue Breakdown: {venue_passed}/{venue_total} tests passed")
        if pnl_results:
            print(f"P&L Calculator: {pnl_passed}/{pnl_total} tests passed")
        print(f"Overall: {total_passed}/{total_tests} tests passed ({total_passed/total_tests*100:.1f}%)")
        
        # Quality Gate Status
        if total_passed == total_tests:
            print(f"\n🎉 SUCCESS: All monitor quality gates passed!")
            print("Position and Exposure Monitors are ready for production!")
            return True
        else:
            print(f"\n⚠️  WARNING: {total_tests - total_passed} monitor quality gates failed")
            print("Review failed tests and address issues before production")
            return False


async def main():
    """Main function."""
    print("📊 MONITOR QUALITY GATES VALIDATION")
    print("=" * 50)
    
    validator = MonitorQualityGates()
    
    # Run all monitor quality gate validations
    position_results = await validator.validate_position_monitor()
    exposure_results = await validator.validate_exposure_monitor_all_modes()
    filtering_results = await validator.validate_asset_filtering_logic()
    venue_results = await validator.validate_venue_breakdown_accuracy()
    pnl_results = await validator.validate_pnl_calculator()
    
    # Generate report
    success = validator.generate_monitor_report(
        position_results, exposure_results, filtering_results, venue_results, pnl_results
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
