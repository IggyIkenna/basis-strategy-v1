#!/usr/bin/env python3
"""
Validate all 10 strategies for architectural compliance.
"""
import sys
from pathlib import Path
from typing import List, Dict
import yaml

def validate_strategy_files() -> List[str]:
    """Validate all strategy files exist and are properly structured"""
    errors = []
    
    strategies_dir = Path("backend/src/basis_strategy_v1/core/strategies")
    required_strategies = [
        "eth_staking_only_strategy.py",
        "eth_leveraged_strategy.py",
        "pure_lending_eth_strategy.py",
        "pure_lending_usdt_strategy.py",
        "eth_basis_strategy.py",
        "btc_basis_strategy.py",
        "ml_btc_directional_btc_margin_strategy.py",
        "ml_btc_directional_usdt_margin_strategy.py",
        "usdt_eth_staking_hedged_leveraged_strategy.py",  # Renamed
        "usdt_eth_staking_hedged_simple_strategy.py",  # Renamed
    ]
    
    for strategy_file in required_strategies:
        file_path = strategies_dir / strategy_file
        if not file_path.exists():
            errors.append(f"Missing strategy file: {file_path}")
    
    return errors

def validate_mode_configs() -> List[str]:
    """Validate all mode configs have correct position_subscriptions"""
    errors = []
    
    modes_dir = Path("configs/modes")
    for mode_file in modes_dir.glob("*.yaml"):
        with open(mode_file) as f:
            config = yaml.safe_load(f)
        
        # Check position_subscriptions exist
        position_subs = config.get('component_config', {}).get('position_monitor', {}).get('position_subscriptions', [])
        if not position_subs:
            errors.append(f"{mode_file.name}: Missing position_subscriptions")
            continue
        
        # Validate instrument key format
        for instrument in position_subs:
            parts = instrument.split(':')
            if len(parts) != 3:
                errors.append(f"{mode_file.name}: Invalid instrument key format: {instrument}")
    
    return errors

def validate_venue_configs() -> List[str]:
    """Validate all venue configs have canonical_instruments"""
    errors = []
    
    venues_dir = Path("configs/venues")
    for venue_file in venues_dir.glob("*.yaml"):
        with open(venue_file) as f:
            config = yaml.safe_load(f)
        
        # Check canonical_instruments exist (except ml_inference_api)
        if venue_file.stem != "ml_inference_api":
            canonical_instruments = config.get('canonical_instruments', [])
            if not canonical_instruments:
                errors.append(f"{venue_file.name}: Missing canonical_instruments")
    
    return errors

def main():
    """Run all strategy validations"""
    all_errors = []
    
    print("Validating strategy files...")
    all_errors.extend(validate_strategy_files())
    
    print("Validating mode configs...")
    all_errors.extend(validate_mode_configs())
    
    print("Validating venue configs...")
    all_errors.extend(validate_venue_configs())
    
    if all_errors:
        print("\n❌ Strategy validation FAILED:")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\n✅ Strategy validation PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
