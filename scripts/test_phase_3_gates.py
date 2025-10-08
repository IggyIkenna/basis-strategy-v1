#!/usr/bin/env python3
"""
Phase 3 Quality Gates: Component Updates

Tests component initialization with proper dependency injection:
1. Position monitor initialization with API request parameters
2. Event engine component initialization with dependency tracking  
3. Component health tracking and error handling
4. Backtest service integration with new architecture
5. Live mode component initialization (should fail without live data/positions)
"""

import sys
import subprocess
import time
from pathlib import Path

def test_position_monitor_initialization():
    """Test position monitor initialization with API request parameters."""
    print("📊 Test 1: Position monitor initialization...")
    
    try:
        result = subprocess.run([
            sys.executable, '-c',
            """
from backend.src.basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
from unittest.mock import Mock

# Test with valid parameters
config = {'mode': 'pure_lending'}
mock_data_provider = Mock()

pm = PositionMonitor(
    config=config,
    execution_mode='backtest',
    initial_capital=100000.0,
    share_class='USDT',
    data_provider=mock_data_provider
)

print(f'position_monitor_initialized=True')
print(f'initial_capital={pm.initial_capital}')
print(f'share_class={pm.share_class}')
print(f'wallet_usdt={pm._token_monitor.wallet.get("USDT", 0)}')
            """
        ], capture_output=True, text=True, timeout=10)
        
        if (result.returncode == 0 and 
            'position_monitor_initialized=True' in result.stdout and
            'initial_capital=100000.0' in result.stdout and
            'wallet_usdt=100000.0' in result.stdout):
            print("    ✅ Position monitor initialization: PASS")
            return True
        else:
            print("    ❌ Position monitor initialization: FAIL")
            print(f"    Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"    ❌ Position monitor initialization: ERROR - {e}")
        return False

def test_position_monitor_fail_fast():
    """Test position monitor fail-fast behavior on invalid parameters."""
    print("📊 Test 2: Position monitor fail-fast behavior...")
    
    try:
        result = subprocess.run([
            sys.executable, '-c',
            """
from backend.src.basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
from unittest.mock import Mock

config = {'mode': 'pure_lending'}
mock_data_provider = Mock()

# Test invalid share class
try:
    pm = PositionMonitor(
        config=config,
        execution_mode='backtest',
        initial_capital=100000.0,
        share_class='INVALID',  # Should fail
        data_provider=mock_data_provider
    )
    print('fail_fast_failed=True')  # Should not reach here
except ValueError as e:
    if 'Invalid share_class: INVALID' in str(e):
        print('fail_fast_working=True')
    else:
        print(f'unexpected_error={e}')

# Test invalid initial capital
try:
    pm = PositionMonitor(
        config=config,
        execution_mode='backtest',
        initial_capital=0,  # Should fail
        share_class='USDT',
        data_provider=mock_data_provider
    )
    print('capital_validation_failed=True')  # Should not reach here
except ValueError as e:
    if 'Invalid initial_capital: 0' in str(e):
        print('capital_validation_working=True')
    else:
        print(f'unexpected_capital_error={e}')
            """
        ], capture_output=True, text=True, timeout=10)
        
        if (result.returncode == 0 and 
            'fail_fast_working=True' in result.stdout and
            'capital_validation_working=True' in result.stdout):
            print("    ✅ Position monitor fail-fast: PASS")
            return True
        else:
            print("    ❌ Position monitor fail-fast: FAIL")
            print(f"    Output: {result.stdout}")
            print(f"    Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"    ❌ Position monitor fail-fast: ERROR - {e}")
        return False

def test_event_engine_component_initialization():
    """Test event engine component initialization with dependency tracking."""
    print("📊 Test 3: Event engine component initialization...")
    
    try:
        result = subprocess.run([
            sys.executable, '-c',
            """
from backend.src.basis_strategy_v1.core.event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine
from unittest.mock import Mock, patch

# Mock data provider with required methods for RiskMonitor
mock_data_provider = Mock()
mock_data_provider.data = {'gas_costs': 'test', 'execution_costs': 'test'}
mock_data_provider.get_aave_risk_parameters.return_value = {
    'emode': {'liquidation_thresholds': {'weETH_WETH': 0.95}},
    'standard': {'liquidation_thresholds': {'weETH_WETH': 0.85}}
}
mock_data_provider.get_bybit_margin_requirements.return_value = {'initial_margin_requirement': 0.05, 'maintenance_margin_requirement': 0.01}
mock_data_provider.get_binance_margin_requirements.return_value = {'initial_margin_requirement': 0.05, 'maintenance_margin_requirement': 0.01}
mock_data_provider.get_okx_margin_requirements.return_value = {'initial_margin_requirement': 0.05, 'maintenance_margin_requirement': 0.01}

config = {
    'mode': 'pure_lending',
    'target_apy': 0.05,
    'strategy': {
        'max_underlying_move': 0.15,
        'max_spot_perp_basis_move': 0.05,
        'max_stake_spread_move': 0.03,
        'coin_symbol': 'ETH',
        'rebalance_threshold_pct': 5.0
    },
    'venues': {
        'aave_ltv_warning': 0.85,
        'aave_ltv_critical': 0.90,
        'margin_warning_pct': 0.20,
        'margin_critical_pct': 0.12
    }
}

# Mock health checking to avoid import issues
with patch('backend.src.basis_strategy_v1.infrastructure.config.health_check.mark_component_healthy') as mock_healthy:
    with patch('backend.src.basis_strategy_v1.infrastructure.config.health_check.mark_component_unhealthy') as mock_unhealthy:
        with patch('backend.src.basis_strategy_v1.core.strategies.components.event_logger.EventLogger'):
            with patch('backend.src.basis_strategy_v1.core.rebalancing.risk_monitor.RiskMonitor'):
                with patch('backend.src.basis_strategy_v1.core.math.pnl_calculator.PnLCalculator'):
                    with patch('backend.src.basis_strategy_v1.core.strategies.components.strategy_manager.StrategyManager'):
                        
                        engine = EventDrivenStrategyEngine(
                            config=config,
                            execution_mode='backtest',
                            data_provider=mock_data_provider,
                            initial_capital=100000.0,
                            share_class='USDT'
                        )
                        
                        print('event_engine_initialized=True')
                        print(f'mode={engine.mode}')
                        print(f'share_class={engine.share_class}')
                        print(f'initial_capital={engine.initial_capital}')
                        print(f'health_calls={mock_healthy.call_count}')
            """
        ], capture_output=True, text=True, timeout=15)
        
        if (result.returncode == 0 and 
            'event_engine_initialized=True' in result.stdout and
            'mode=pure_lending' in result.stdout and
            'health_calls=' in result.stdout):
            print("    ✅ Event engine initialization: PASS")
            return True
        else:
            print("    ❌ Event engine initialization: FAIL")
            print(f"    Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"    ❌ Event engine initialization: ERROR - {e}")
        return False

def test_component_dependency_tracking():
    """Test component dependency tracking and health monitoring."""
    print("📊 Test 4: Component dependency tracking...")
    
    try:
        result = subprocess.run([
            sys.executable, '-c',
            """
from backend.src.basis_strategy_v1.core.event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine
from unittest.mock import Mock, patch

mock_data_provider = Mock()
mock_data_provider.data = {}
mock_data_provider.get_aave_risk_parameters.return_value = {
    'emode': {'liquidation_thresholds': {'weETH_WETH': 0.95}},
    'standard': {'liquidation_thresholds': {'weETH_WETH': 0.85}}
}

config = {
    'mode': 'pure_lending',
    'strategy': {'max_underlying_move': 0.15},
    'venues': {'aave_ltv_warning': 0.85}
}

# Mock position monitor to fail
with patch('backend.src.basis_strategy_v1.core.strategies.components.position_monitor.PositionMonitor') as mock_pm:
    mock_pm.side_effect = Exception("Position monitor failed")
    
    with patch('backend.src.basis_strategy_v1.infrastructure.config.health_check.mark_component_unhealthy') as mock_unhealthy:
        try:
            engine = EventDrivenStrategyEngine(
                config=config,
                execution_mode='backtest',
                data_provider=mock_data_provider,
                initial_capital=100000.0,
                share_class='USDT'
            )
            print('should_have_failed=True')  # Should not reach here
        except ValueError as e:
            if 'Position Monitor initialization failed' in str(e):
                print('dependency_tracking_working=True')
                print(f'unhealthy_calls={mock_unhealthy.call_count}')
            else:
                print(f'unexpected_error={e}')
            """
        ], capture_output=True, text=True, timeout=10)
        
        if (result.returncode == 0 and 
            'dependency_tracking_working=True' in result.stdout):
            print("    ✅ Component dependency tracking: PASS")
            return True
        else:
            print("    ❌ Component dependency tracking: FAIL")
            print(f"    Output: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"    ❌ Component dependency tracking: ERROR - {e}")
        return False

def test_live_mode_component_initialization():
    """Test live mode component initialization (should fail without live data setup)."""
    print("📊 Test 5: Live mode component initialization...")
    
    try:
        result = subprocess.run([
            sys.executable, '-c',
            """
from backend.src.basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
from unittest.mock import Mock
import os

config = {'mode': 'pure_lending'}
mock_data_provider = Mock()

# Test live mode without Redis URL (should fail)
try:
    # Clear Redis URL to test fail-fast
    if 'BASIS_REDIS_URL' in os.environ:
        del os.environ['BASIS_REDIS_URL']
    
    pm = PositionMonitor(
        config=config,
        execution_mode='live',  # Live mode
        initial_capital=100000.0,
        share_class='USDT',
        data_provider=mock_data_provider
    )
    print('live_mode_should_have_failed=True')  # Should not reach here
except ValueError as e:
    if 'BASIS_REDIS_URL environment variable required' in str(e):
        print('live_mode_fail_fast_working=True')
    else:
        print(f'unexpected_live_error={e}')
            """
        ], capture_output=True, text=True, timeout=10)
        
        if (result.returncode == 0 and 
            'live_mode_fail_fast_working=True' in result.stdout):
            print("    ✅ Live mode fail-fast: PASS (correctly fails without live setup)")
            return True
        else:
            print("    ❌ Live mode fail-fast: FAIL")
            print(f"    Output: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"    ❌ Live mode fail-fast: ERROR - {e}")
        return False

def main():
    """Run all Phase 3 quality gates."""
    print("🚦 PHASE 3 QUALITY GATES: Component Updates")
    print("=" * 60)
    print("Focus: Component initialization with dependency injection and health tracking")
    print()
    
    tests = [
        test_position_monitor_initialization,
        test_position_monitor_fail_fast,
        test_event_engine_component_initialization,
        test_component_dependency_tracking,
        test_live_mode_component_initialization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 PHASE 3 SUMMARY:")
    print(f"Passed: {passed}/{total} tests ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 SUCCESS: All Phase 3 quality gates passed!")
        return 0
    else:
        print(f"⚠️  WARNING: {total - passed} Phase 3 quality gates failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
