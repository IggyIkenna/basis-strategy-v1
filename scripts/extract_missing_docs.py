#!/usr/bin/env python3
"""
Extract Missing Documentation Details

This script runs the env-config usage sync quality gates and extracts
the detailed lists of missing documentation for each category.
"""

import sys
import os
from pathlib import Path

# Add the backend source to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

# Import the quality gates class
from test_env_config_usage_sync_quality_gates import EnvConfigUsageSyncQualityGates

def main():
    """Extract and display detailed missing documentation lists."""
    print("🔍 Extracting detailed missing documentation lists...")
    print("=" * 80)
    
    # Run the quality gates
    quality_gates = EnvConfigUsageSyncQualityGates()
    results = quality_gates.run_all_tests()
    
    print("\n📋 DETAILED MISSING DOCUMENTATION LISTS")
    print("=" * 80)
    
    # 1. Undocumented Environment Variables
    print("\n1️⃣ UNDOCUMENTED ENVIRONMENT VARIABLES")
    print("-" * 50)
    undocumented_env_vars = results['env_variables']['undocumented']
    if undocumented_env_vars:
        for i, var in enumerate(undocumented_env_vars, 1):
            print(f"{i:2d}. {var}")
    else:
        print("✅ All environment variables are documented")
    
    # 2. Undocumented Config Fields by Component
    print("\n2️⃣ UNDOCUMENTED CONFIG FIELDS BY COMPONENT")
    print("-" * 50)
    config_fields = results['config_fields']['by_component']
    for component, data in config_fields.items():
        if data['undocumented']:
            print(f"\n📦 {component.upper()} ({len(data['undocumented'])} undocumented fields):")
            for i, field in enumerate(data['undocumented'], 1):
                print(f"   {i:2d}. {field}")
    
    # 3. Undocumented Data Provider Queries by Component
    print("\n3️⃣ UNDOCUMENTED DATA PROVIDER QUERIES BY COMPONENT")
    print("-" * 50)
    data_queries = results['data_queries']['by_component']
    for component, data in data_queries.items():
        if data['undocumented']:
            print(f"\n📦 {component.upper()} ({len(data['undocumented'])} undocumented queries):")
            for i, query in enumerate(data['undocumented'], 1):
                print(f"   {i:2d}. {query}")
    
    # 4. Undocumented Event Logging Patterns by Component
    print("\n4️⃣ UNDOCUMENTED EVENT LOGGING PATTERNS BY COMPONENT")
    print("-" * 50)
    event_logging = results['event_logging']['by_component']
    for component, data in event_logging.items():
        if data['undocumented']:
            print(f"\n📦 {component.upper()} ({len(data['undocumented'])} undocumented patterns):")
            for i, pattern in enumerate(data['undocumented'], 1):
                print(f"   {i:2d}. {pattern}")
    
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"• Undocumented Environment Variables: {len(undocumented_env_vars)}")
    
    total_undocumented_config = sum(
        len(data['undocumented']) for data in config_fields.values()
    )
    print(f"• Undocumented Config Fields: {total_undocumented_config}")
    
    total_undocumented_queries = sum(
        len(data['undocumented']) for data in data_queries.values()
    )
    print(f"• Undocumented Data Provider Queries: {total_undocumented_queries}")
    
    total_undocumented_logging = sum(
        len(data['undocumented']) for data in event_logging.values()
    )
    print(f"• Undocumented Event Logging Patterns: {total_undocumented_logging}")
    
    print(f"\n🎯 Total Missing Documentation Items: {len(undocumented_env_vars) + total_undocumented_config + total_undocumented_queries + total_undocumented_logging}")

if __name__ == '__main__':
    main()
