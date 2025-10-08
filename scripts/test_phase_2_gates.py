#!/usr/bin/env python3
"""
Phase 2 Quality Gates: Data Provider Updates (Backtest Mode Only)

Tests the historical data provider path under backtest mode:
1. All data loading at startup without exception
2. Data validation with fail-fast policy
3. No minimal data creation methods exist
4. Data provider health monitoring
"""

import sys
import time
import subprocess
from pathlib import Path

def test_data_loading_at_startup():
    """Test that all data loads at startup without exception."""
    print("📊 Test 1: All data loading at startup...")
    
    try:
        start_time = time.time()
        result = subprocess.run([
            sys.executable, '-c',
            """
from backend.src.basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
from backend.src.basis_strategy_v1.infrastructure.config.config_manager import get_config_manager

cm = get_config_manager()
dp = create_data_provider(
    data_dir=cm.get_data_directory(),
    startup_mode='backtest',  # Test backtest mode only
    config=cm.get_complete_config()
)
print(f'data_loading_completed=True')
print(f'datasets_loaded={len(dp.data)}')
print(f'provider_type={type(dp).__name__}')
print(f'provider_mode={dp.mode}')
            """
        ], capture_output=True, text=True, timeout=60)
        elapsed = time.time() - start_time
        
        if result.returncode == 0 and 'data_loading_completed=True' in result.stdout:
            datasets_count = result.stdout.split('datasets_loaded=')[1].split('\n')[0]
            print(f"    ✅ Data loading: PASS ({elapsed:.2f}s, {datasets_count} datasets)")
            return True
        else:
            print(f"    ❌ Data loading: FAIL (took {elapsed:.2f}s)")
            print(f"    Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"    ❌ Data loading: ERROR - {e}")
        return False

def test_data_validation_at_startup():
    """Test data validation with fail-fast policy."""
    print("📊 Test 2: Data validation at startup...")
    
    try:
        result = subprocess.run([
            sys.executable, '-c',
            """
from backend.src.basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
from backend.src.basis_strategy_v1.infrastructure.config.config_manager import get_config_manager

cm = get_config_manager()
dp = create_data_provider(
    data_dir=cm.get_data_directory(),
    startup_mode='backtest',
    config=cm.get_complete_config()
)
dp._validate_data_at_startup()
print('data_validation_completed=True')
            """
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and 'data_validation_completed=True' in result.stdout:
            print("    ✅ Data validation: PASS")
            return True
        else:
            print("    ❌ Data validation: FAIL")
            print(f"    Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"    ❌ Data validation: ERROR - {e}")
        return False

def test_minimal_methods_removed():
    """Test that no minimal data creation methods exist."""
    print("📊 Test 3: Minimal data methods removed...")
    
    try:
        result = subprocess.run([
            'grep', '-r', 'def _create_minimal_', 'backend/src/basis_strategy_v1/infrastructure/data/'
        ], capture_output=True, text=True)
        
        # Should find no matches (except comments about removal)
        if result.returncode != 0:
            print("    ✅ Minimal methods removed: PASS (no methods found)")
            return True
        elif 'REMOVED:' in result.stdout and 'def _create_minimal_' not in result.stdout:
            print("    ✅ Minimal methods removed: PASS (only removal comments found)")
            return True
        else:
            print("    ❌ Minimal methods removed: FAIL (found minimal methods)")
            print(f"    Found: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"    ❌ Minimal methods removed: ERROR - {e}")
        return False

def test_data_provider_health():
    """Test data provider health monitoring."""
    print("📊 Test 4: Data provider health monitoring...")
    
    try:
        result = subprocess.run([
            sys.executable, '-c',
            """
from backend.src.basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
from backend.src.basis_strategy_v1.infrastructure.config.config_manager import get_config_manager

cm = get_config_manager()
dp = create_data_provider(
    data_dir=cm.get_data_directory(),
    startup_mode='backtest',
    config=cm.get_complete_config()
)
health = dp.get_health_status()
print(f'health_status={health["status"]}')
print(f'datasets_count={health["datasets_loaded"]}')
print(f'errors_count={len(health["errors"])}')
print(f'warnings_count={len(health["warnings"])}')
            """
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and 'health_status=healthy' in result.stdout:
            print("    ✅ Data provider health: PASS")
            return True
        else:
            print("    ❌ Data provider health: FAIL")
            print(f"    Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"    ❌ Data provider health: ERROR - {e}")
        return False

def test_live_mode_separation():
    """Test that live mode is properly handled by factory."""
    print("📊 Test 5: Live mode separation...")
    
    try:
        result = subprocess.run([
            sys.executable, '-c',
            """
# Test that historical data provider rejects live mode
try:
    from backend.src.basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider
    dp = DataProvider(
        data_dir='./data',
        mode='test',
        execution_mode='live',  # Should be rejected
        config={}
    )
    print('historical_provider_accepted_live=True')  # Should not reach here
except ValueError as e:
    if 'only supports execution_mode=\\'backtest\\'' in str(e):
        print('historical_provider_rejected_live=True')
    else:
        print(f'unexpected_error={e}')

# Test that factory properly creates live data provider
try:
    from backend.src.basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
    dp = create_data_provider(
        data_dir='./data',
        startup_mode='live',
        config={}
    )
    print(f'live_provider_type={type(dp).__name__}')
except Exception as e:
    print(f'live_provider_error={e}')
            """
        ], capture_output=True, text=True, timeout=10)
        
        if (result.returncode == 0 and 
            'historical_provider_rejected_live=True' in result.stdout and
            'live_provider_type=LiveDataProvider' in result.stdout):
            print("    ✅ Live mode separation: PASS")
            return True
        else:
            print("    ❌ Live mode separation: FAIL")
            print(f"    Output: {result.stdout}")
            print(f"    Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"    ❌ Live mode separation: ERROR - {e}")
        return False

def main():
    """Run all Phase 2 quality gates."""
    print("🚦 PHASE 2 QUALITY GATES: Data Provider Updates")
    print("=" * 60)
    print("Focus: Backtest mode only (live mode handled by factory)")
    print()
    
    tests = [
        test_data_loading_at_startup,
        test_data_validation_at_startup,
        test_minimal_methods_removed,
        test_data_provider_health,
        test_live_mode_separation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 PHASE 2 SUMMARY:")
    print(f"Passed: {passed}/{total} tests ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 SUCCESS: All Phase 2 quality gates passed!")
        return 0
    else:
        print(f"⚠️  WARNING: {total - passed} Phase 2 quality gates failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
