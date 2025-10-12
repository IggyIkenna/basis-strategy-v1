#!/usr/bin/env python3
"""
Live Data Validation Test (Future Quality Gate)

This script tests live data connections for each venue based on data_requirements
from configs/modes/*.yaml files. Currently will fail because we don't have
full testnet/production API credentials setup.

TODO: Add to quality gates once we have:
- Complete testnet/production environment variables
- Live authentication config setup
- Full venue API credentials
"""

import asyncio
import sys
from pathlib import Path

async def test_live_data_connections_for_mode(mode: str):
    """Test live data connections for a specific mode."""
    print(f"📊 Testing live data connections for mode: {mode}")
    
    try:
        from backend.src.basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
        from backend.src.basis_strategy_v1.infrastructure.config.config_manager import get_config_manager

        cm = get_config_manager()
        mode_config = cm.get_complete_config(mode=mode)
        
        dp_live = create_data_provider(
            data_dir=cm.get_data_directory(),
            startup_mode='live',
            config=mode_config,
            mode=mode
        )
        
        print(f"  📊 Data requirements: {dp_live.data_requirements}")
        
        # Test live data connections
        async with dp_live:
            validation_results = await dp_live.validate_live_data_connections()
            
            print(f"  📊 Overall status: {validation_results['overall_status']}")
            print(f"  📊 Connection tests: {len(validation_results['connection_tests'])}")
            print(f"  📊 Errors: {len(validation_results['errors'])}")
            print(f"  📊 Warnings: {len(validation_results['warnings'])}")
            
            if validation_results['overall_status'] == 'healthy':
                print(f"  ✅ {mode}: All connections healthy")
                return True
            else:
                print(f"  ⚠️  {mode}: Some connections failed (expected without full API setup)")
                for error in validation_results['errors']:
                    print(f"    - {error}")
                return False
                
    except Exception as e:
        print(f"  ❌ {mode}: Test failed - {e}")
        return False

async def main():
    """Test live data connections for all modes."""
    print("🚦 LIVE DATA CONNECTION VALIDATION (Future Quality Gate)")
    print("=" * 70)
    print("NOTE: Expected to fail without full testnet/production API setup")
    print()
    
    # Test modes that have data requirements
    modes_to_test = ['pure_lending', 'btc_basis', 'eth_leveraged', 'usdt_market_neutral']
    
    passed = 0
    total = len(modes_to_test)
    
    for mode in modes_to_test:
        if await test_live_data_connections_for_mode(mode):
            passed += 1
        print()
    
    print("=" * 70)
    print(f"📊 LIVE DATA CONNECTION SUMMARY:")
    print(f"Passed: {passed}/{total} modes ({passed/total*100:.1f}%)")
    print()
    print("📝 TODO: Add to quality gates once we have:")
    print("  - Complete testnet/production environment variables")
    print("  - Live authentication config setup") 
    print("  - Full venue API credentials")
    print()
    
    if passed == total:
        print("🎉 SUCCESS: All live data connections validated!")
        return 0
    else:
        print("⚠️  EXPECTED: Some connections failed (API setup incomplete)")
        return 0  # Return 0 since this is expected for now

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
