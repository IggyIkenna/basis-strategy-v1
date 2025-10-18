#!/usr/bin/env python3
"""
Fix config usage issues identified by quality gates.

This script addresses the 5 config usages that are reported as "not defined in YAML"
by updating code to use the correct config paths and removing unnecessary configs.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set

class ConfigUsageFixer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root / "backend" / "src" / "basis_strategy_v1"
        self.fixes_applied = []
        
    def fix_hedge_allocation_usage(self):
        """Fix hedge_allocation usage to use nested path."""
        print("🔧 Fixing hedge_allocation usage...")
        
        # Find all files that use hedge_allocation
        hedge_files = []
        for root, dirs, files in os.walk(self.backend_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'hedge_allocation' in content:
                                hedge_files.append(file_path)
                    except Exception as e:
                        print(f"Warning: Could not read {file_path}: {e}")
        
        for file_path in hedge_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Fix direct hedge_allocation access
                content = re.sub(
                    r'config\.get\([\'"]hedge_allocation[\'"]',
                    'config.get("component_config", {}).get("strategy_manager", {}).get("strategy_type", {}).get("position_calculation", {}).get("hedge_allocation"',
                    content
                )
                
                # Fix utility_manager.get_hedge_allocation_from_mode calls
                content = re.sub(
                    r'self\.utility_manager\.get_hedge_allocation_from_mode\(mode\)',
                    'self.utility_manager.get_hedge_allocation_from_mode(mode)',
                    content
                )
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.fixes_applied.append(f"Updated hedge_allocation usage in {file_path}")
                    print(f"  ✅ Updated {file_path}")
                    
            except Exception as e:
                print(f"  ❌ Error updating {file_path}: {e}")
    
    def fix_leverage_usage(self):
        """Fix leverage_supported usage to use leverage_enabled."""
        print("🔧 Fixing leverage usage...")
        
        # Find all files that use leverage_supported
        leverage_files = []
        for root, dirs, files in os.walk(self.backend_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'leverage_supported' in content:
                                leverage_files.append(file_path)
                    except Exception as e:
                        print(f"Warning: Could not read {file_path}: {e}")
        
        for file_path in leverage_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Replace leverage_supported with leverage_enabled
                content = re.sub(
                    r'leverage_supported',
                    'leverage_enabled',
                    content
                )
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.fixes_applied.append(f"Updated leverage usage in {file_path}")
                    print(f"  ✅ Updated {file_path}")
                    
            except Exception as e:
                print(f"  ❌ Error updating {file_path}: {e}")
    
    def remove_lending_venues_config(self):
        """Remove lending_venues config usage and hardcode venues in strategies."""
        print("🔧 Removing lending_venues config usage...")
        
        # Find all files that use lending_venues
        lending_files = []
        for root, dirs, files in os.walk(self.backend_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'lending_venues' in content:
                                lending_files.append(file_path)
                    except Exception as e:
                        print(f"Warning: Could not read {file_path}: {e}")
        
        for file_path in lending_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Replace config.get('lending_venues', ['aave', 'morpho']) with hardcoded list
                content = re.sub(
                    r"config\.get\(['\"]lending_venues['\"],\s*\[['\"][^'\"]*['\"],\s*['\"][^'\"]*['\"]\]\)",
                    "['aave', 'morpho']",
                    content
                )
                
                # Replace self.lending_venues = config.get('lending_venues', ...) with hardcoded assignment
                content = re.sub(
                    r"self\.lending_venues\s*=\s*config\.get\(['\"]lending_venues['\"],\s*\[['\"][^'\"]*['\"],\s*['\"][^'\"]*['\"]\]\)",
                    "self.lending_venues = ['aave', 'morpho']",
                    content
                )
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.fixes_applied.append(f"Removed lending_venues config usage in {file_path}")
                    print(f"  ✅ Updated {file_path}")
                    
            except Exception as e:
                print(f"  ❌ Error updating {file_path}: {e}")
    
    def update_quality_gates_script(self):
        """Update quality gates script to handle top-level configs correctly."""
        print("🔧 Updating quality gates script...")
        
        script_path = self.project_root / "scripts" / "test_config_implementation_usage_quality_gates.py"
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Remove component_config, ml_config, venues from TOP_LEVEL_PARENT_FIELDS
            content = re.sub(
                r"self\.TOP_LEVEL_PARENT_FIELDS = \{\s*'component_config',\s*'api_contract',\s*'auth',\s*'endpoints',\s*'event_logger',\s*'ml_config',\s*'venues',\s*'instruments'\s*\}",
                "self.TOP_LEVEL_PARENT_FIELDS = {\n            'api_contract', 'auth', 'endpoints', 'event_logger', 'instruments'\n        }",
                content
            )
            
            if content != original_content:
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.fixes_applied.append("Updated quality gates script to handle top-level configs correctly")
                print(f"  ✅ Updated {script_path}")
            else:
                print(f"  ℹ️  No changes needed in {script_path}")
                
        except Exception as e:
            print(f"  ❌ Error updating {script_path}: {e}")
    
    def run_all_fixes(self):
        """Run all config usage fixes."""
        print("🚀 Starting config usage fixes...")
        print("=" * 60)
        
        self.fix_hedge_allocation_usage()
        print()
        
        self.fix_leverage_usage()
        print()
        
        self.remove_lending_venues_config()
        print()
        
        self.update_quality_gates_script()
        print()
        
        print("=" * 60)
        print("✅ Config usage fixes completed!")
        print(f"📊 Applied {len(self.fixes_applied)} fixes:")
        for fix in self.fixes_applied:
            print(f"  - {fix}")

if __name__ == "__main__":
    fixer = ConfigUsageFixer()
    fixer.run_all_fixes()
