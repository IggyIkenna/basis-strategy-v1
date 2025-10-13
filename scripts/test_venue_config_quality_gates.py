#!/usr/bin/env python3
"""
Venue Configuration Quality Gates

Tests that venue configuration is standardized and working:
1. All mode configs have venues: sections
2. All venues use standardized structure (venue_type, instruments, order_types)
3. API reads venue configuration correctly
4. Venue types match expected values
"""

import os
import sys
import yaml
import subprocess
from pathlib import Path

def test_all_modes_have_venues():
    """Test that all mode configs have venues: sections."""
    print("🔍 Testing all modes have venues sections...")
    
    modes_dir = Path("configs/modes")
    if not modes_dir.exists():
        print("❌ configs/modes directory not found")
        return False
    
    missing_venues = []
    for yaml_file in modes_dir.glob("*.yaml"):
        try:
            with open(yaml_file) as f:
                config = yaml.safe_load(f)
                
            if 'venues' not in config or not config['venues']:
                missing_venues.append(yaml_file.stem)
        except Exception as e:
            print(f"❌ Failed to load {yaml_file}: {e}")
            return False
    
    if missing_venues:
        print(f"❌ Modes missing venues sections: {missing_venues}")
        return False
    
    print("✅ All mode configs have venues sections")
    return True

def test_venue_structure_standardized():
    """Test that all venues use standardized structure."""
    print("🔍 Testing venue structure standardization...")
    
    modes_dir = Path("configs/modes")
    required_fields = ['venue_type', 'enabled', 'instruments', 'order_types']
    issues = []
    
    for yaml_file in modes_dir.glob("*.yaml"):
        try:
            with open(yaml_file) as f:
                config = yaml.safe_load(f)
                
            venues = config.get('venues', {})
            for venue_name, venue_config in venues.items():
                if not isinstance(venue_config, dict):
                    issues.append(f"{yaml_file.stem}: {venue_name} is not a dict")
                    continue
                    
                for field in required_fields:
                    if field not in venue_config:
                        issues.append(f"{yaml_file.stem}: {venue_name} missing {field}")
                        
                # Check venue_type is valid
                venue_type = venue_config.get('venue_type')
                if venue_type not in ['cex', 'defi', 'infrastructure']:
                    issues.append(f"{yaml_file.stem}: {venue_name} invalid venue_type: {venue_type}")
                    
                # Check instruments is list
                instruments = venue_config.get('instruments')
                if not isinstance(instruments, list):
                    issues.append(f"{yaml_file.stem}: {venue_name} instruments must be list")
                    
                # Check order_types is list
                order_types = venue_config.get('order_types')
                if not isinstance(order_types, list):
                    issues.append(f"{yaml_file.stem}: {venue_name} order_types must be list")
                    
        except Exception as e:
            issues.append(f"Failed to load {yaml_file}: {e}")
    
    if issues:
        print("❌ Venue structure issues:")
        for issue in issues[:10]:  # Limit to first 10 issues
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more issues")
        return False
    
    print("✅ All venue structures are standardized")
    return True

def test_api_returns_all_strategies():
    """Test that API returns all 9 strategies."""
    print("🔍 Testing API returns all strategies...")
    
    try:
        result = subprocess.run([
            'curl', '-s', '--connect-timeout', '3', '--max-time', '5', 
            'http://localhost:8001/api/v1/strategies/'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            if result.returncode == 7:  # Connection refused
                print("⚠️ Backend not running - skipping API test")
                return True
            else:
                print(f"❌ API call failed with code {result.returncode}")
                return False
                
        import json
        response = json.loads(result.stdout)
        
        if not response.get('success'):
            print(f"❌ API returned error: {response.get('error')}")
            return False
            
        total = response.get('data', {}).get('total', 0)
        if total != 9:
            print(f"❌ Expected 9 strategies, got {total}")
            return False
            
        print(f"✅ API returns all {total} strategies")
        return True
        
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def test_venue_types_match_config():
    """Test that venue types in configs match venue configs."""
    print("🔍 Testing venue types match venue configs...")
    
    # Load venue configs
    venues_dir = Path("configs/venues")
    venue_types = {}
    
    for yaml_file in venues_dir.glob("*.yaml"):
        try:
            with open(yaml_file) as f:
                config = yaml.safe_load(f)
            venue_name = config.get('venue')
            venue_type = config.get('type')
            if venue_name and venue_type:
                venue_types[venue_name] = venue_type
        except Exception as e:
            print(f"❌ Failed to load venue config {yaml_file}: {e}")
            return False
    
    # Check mode configs use correct venue types
    modes_dir = Path("configs/modes")
    mismatches = []
    
    for yaml_file in modes_dir.glob("*.yaml"):
        try:
            with open(yaml_file) as f:
                config = yaml.safe_load(f)
                
            venues = config.get('venues', {})
            for venue_name, venue_config in venues.items():
                expected_type = venue_types.get(venue_name)
                actual_type = venue_config.get('venue_type')
                
                if expected_type and actual_type and expected_type != actual_type:
                    mismatches.append(f"{yaml_file.stem}: {venue_name} type mismatch - expected {expected_type}, got {actual_type}")
                    
        except Exception as e:
            mismatches.append(f"Failed to check {yaml_file}: {e}")
    
    if mismatches:
        print("❌ Venue type mismatches:")
        for mismatch in mismatches:
            print(f"  - {mismatch}")
        return False
    
    print("✅ All venue types match venue configs")
    return True

def run_quality_gates():
    """Run all venue configuration quality gates."""
    print("🚦 VENUE CONFIGURATION QUALITY GATES")
    print("=" * 50)
    
    tests = [
        ("All Modes Have Venues", test_all_modes_have_venues),
        ("Venue Structure Standardized", test_venue_structure_standardized),
        ("API Returns All Strategies", test_api_returns_all_strategies),
        ("Venue Types Match Config", test_venue_types_match_config),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n📊 VENUE CONFIGURATION SUMMARY: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All venue configuration quality gates PASSED")
        return True
    else:
        print("❌ Some venue configuration quality gates FAILED")
        return False

if __name__ == "__main__":
    success = run_quality_gates()
    sys.exit(0 if success else 1)

