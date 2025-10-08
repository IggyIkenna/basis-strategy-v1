#!/usr/bin/env python3
"""
Test the union Pydantic models against all config files.
"""

import json
import yaml
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from basis_strategy_v1.core.config.config_union_models import (
    ConfigUnion, InfrastructureConfigUnion, StrategyConfigUnion, 
    VenueConfigUnion, ShareClassConfigUnion
)

def load_and_test_configs():
    """Load all configs and test against union models."""
    config_dir = Path(__file__).parent.parent / "configs"
    results = {"passed": 0, "failed": 0, "errors": []}
    
    print("🧪 TESTING UNION MODELS AGAINST ALL CONFIGS")
    print("=" * 60)
    
    # Test JSON configs against InfrastructureConfigUnion
    for json_file in config_dir.glob("*.json"):
        print(f"📄 Testing {json_file.name} against InfrastructureConfigUnion...")
        try:
            with open(json_file, 'r') as f:
                config_data = json.load(f)
            
            # Test infrastructure model
            infra_model = InfrastructureConfigUnion(**config_data)
            print(f"  ✅ {json_file.name} passed validation")
            results["passed"] += 1
            
        except Exception as e:
            print(f"  ❌ {json_file.name} failed: {e}")
            results["failed"] += 1
            results["errors"].append(f"{json_file.name}: {e}")
    
    # Test mode configs against StrategyConfigUnion
    modes_dir = config_dir / "modes"
    if modes_dir.exists():
        for yaml_file in modes_dir.glob("*.yaml"):
            print(f"📄 Testing {yaml_file.name} against StrategyConfigUnion...")
            try:
                with open(yaml_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Test strategy model
                strategy_model = StrategyConfigUnion(**config_data)
                print(f"  ✅ {yaml_file.name} passed validation")
                results["passed"] += 1
                
            except Exception as e:
                print(f"  ❌ {yaml_file.name} failed: {e}")
                results["failed"] += 1
                results["errors"].append(f"modes/{yaml_file.name}: {e}")
    
    # Test venue configs against VenueConfigUnion
    venues_dir = config_dir / "venues"
    if venues_dir.exists():
        for yaml_file in venues_dir.glob("*.yaml"):
            print(f"📄 Testing {yaml_file.name} against VenueConfigUnion...")
            try:
                with open(yaml_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Test venue model
                venue_model = VenueConfigUnion(**config_data)
                print(f"  ✅ {yaml_file.name} passed validation")
                results["passed"] += 1
                
            except Exception as e:
                print(f"  ❌ {yaml_file.name} failed: {e}")
                results["failed"] += 1
                results["errors"].append(f"venues/{yaml_file.name}: {e}")
    
    # Test share class configs against ShareClassConfigUnion
    share_classes_dir = config_dir / "share_classes"
    if share_classes_dir.exists():
        for yaml_file in share_classes_dir.glob("*.yaml"):
            print(f"📄 Testing {yaml_file.name} against ShareClassConfigUnion...")
            try:
                with open(yaml_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Test share class model
                share_class_model = ShareClassConfigUnion(**config_data)
                print(f"  ✅ {yaml_file.name} passed validation")
                results["passed"] += 1
                
            except Exception as e:
                print(f"  ❌ {yaml_file.name} failed: {e}")
                results["failed"] += 1
                results["errors"].append(f"share_classes/{yaml_file.name}: {e}")
    
    return results

def main():
    results = load_and_test_configs()
    
    print("\n📊 VALIDATION RESULTS")
    print("=" * 60)
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📈 Success Rate: {results['passed']/(results['passed']+results['failed'])*100:.1f}%")
    
    if results["errors"]:
        print("\n🔍 ERRORS:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    if results["failed"] == 0:
        print("\n🎉 All configs passed validation against union models!")
        return 0
    else:
        print(f"\n⚠️  {results['failed']} configs failed validation")
        return 1

if __name__ == "__main__":
    sys.exit(main())
