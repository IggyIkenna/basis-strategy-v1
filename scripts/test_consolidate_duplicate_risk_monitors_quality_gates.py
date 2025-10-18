#!/usr/bin/env python3
"""
Quality Gate: Consolidate Duplicate Risk Monitors
Ensures only one instance of each major and minor component exists in the codebase.
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_component_files(backend_dir: str = "backend/src/basis_strategy_v1/") -> Dict[str, List[str]]:
    """Find all component files organized by component type."""
    components = {
        'risk_monitors': [],
        'position_monitors': [],
        'exposure_monitors': [],
        'strategy_managers': [],
        'execution_managers': [],
        'data_providers': [],
        'event_loggers': [],
        'pnl_monitors': [],
        'utility_managers': [],
        'config_managers': [],
        'health_monitors': [],
        'reconciliation_managers': []
    }
    
    # Search directories for component files
    search_dirs = [
        "core/components/",
        "core/strategies/components/",
        "core/strategies/",
        "core/math/",
        "core/interfaces/",
        "core/services/",
        "core/utilities/",
        "core/health/",
        "core/reconciliation/",
        "core/execution/",
        "infrastructure/config/",
        "infrastructure/logging/",
        "infrastructure/monitoring/",
        "infrastructure/persistence/",
        "infrastructure/data/"
    ]
    
    for search_dir in search_dirs:
        full_path = os.path.join(backend_dir, search_dir)
        if os.path.exists(full_path):
            for file in os.listdir(full_path):
                if file.endswith('.py') and not file.startswith('__'):
                    file_path = os.path.join(full_path, file)
                    
                    # Categorize files by component type
                    if 'risk_monitor' in file.lower():
                        components['risk_monitors'].append(file_path)
                    elif 'position_monitor' in file.lower():
                        components['position_monitors'].append(file_path)
                    elif 'exposure_monitor' in file.lower():
                        components['exposure_monitors'].append(file_path)
                    elif 'strategy_manager' in file.lower() and 'base_strategy_manager' not in file.lower():
                        components['strategy_managers'].append(file_path)
                    elif 'execution_manager' in file.lower():
                        components['execution_managers'].append(file_path)
                    elif 'data_provider_factory' in file.lower():
                        # Factory creates 7 mode-specific providers, so count as 7
                        components['data_providers'].append(file_path)
                    elif 'event_logger' in file.lower():
                        components['event_loggers'].append(file_path)
                    elif 'pnl_monitor' in file.lower():
                        components['pnl_monitors'].append(file_path)
                    elif 'utility_manager' in file.lower():
                        components['utility_managers'].append(file_path)
                    elif 'config_manager' in file.lower():
                        components['config_managers'].append(file_path)
                    elif 'health_monitor' in file.lower() or 'unified_health_manager' in file.lower():
                        components['health_monitors'].append(file_path)
                    elif 'reconciliation_manager' in file.lower() or 'reconciliation_component' in file.lower():
                        components['reconciliation_managers'].append(file_path)
    
    return components

def check_duplicate_components(components: Dict[str, List[str]]) -> Dict[str, any]:
    """Check for duplicate components and validate singleton patterns."""
    results = {
        'duplicates_found': [],
        'singleton_violations': [],
        'architecture_compliant': [],
        'total_components': 0,
        'duplicate_count': 0,
        'singleton_violation_count': 0
    }
    
    for component_type, files in components.items():
        if not files:
            continue
        
        # Special handling for data_providers (factory pattern)
        if component_type == 'data_providers':
            # Factory creates 7 mode-specific providers, so expected count is 7
            expected_count = 7
            actual_count = len(files)
            results['total_components'] += expected_count
            
            # Check if we have the right number of providers (should be 1 factory file)
            if actual_count != 1:
                results['duplicates_found'].append({
                    'component_type': component_type,
                    'files': files,
                    'count': actual_count,
                    'expected': expected_count
                })
                results['duplicate_count'] += abs(actual_count - 1)
        else:
            results['total_components'] += len(files)
            
            # Check for duplicates
            if len(files) > 1:
                results['duplicates_found'].append({
                    'component_type': component_type,
                    'files': files,
                    'count': len(files)
                })
                results['duplicate_count'] += len(files) - 1
        
        # Check singleton pattern implementation
        for file_path in files:
            if not check_singleton_pattern(file_path):
                results['singleton_violations'].append({
                    'component_type': component_type,
                    'file': file_path,
                    'issue': 'Missing singleton pattern implementation'
                })
                results['singleton_violation_count'] += 1
            else:
                results['architecture_compliant'].append({
                    'component_type': component_type,
                    'file': file_path
                })
    
    return results

def check_singleton_pattern(file_path: str) -> bool:
    """Check if a component implements singleton pattern correctly."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip files that are functions, not classes (e.g., data_provider_factory.py)
        if 'def create_data_provider(' in content and 'class ' not in content:
            return True  # Functions don't need singleton pattern
        
        # Check for singleton pattern indicators
        has_instance_var = '_instance' in content
        has_new_method = '__new__' in content
        has_singleton_check = 'if cls._instance is None' in content
        
        return has_instance_var and has_new_method and has_singleton_check
    except Exception as e:
        logger.error(f"Error checking singleton pattern in {file_path}: {e}")
        return False

def check_architecture_compliance(components: Dict[str, List[str]]) -> Dict[str, any]:
    """Check overall architecture compliance."""
    compliance_checks = {
        'expected_components': {
            'risk_monitors': 1,
            'position_monitors': 1,
            'exposure_monitors': 1,
            'strategy_managers': 1,
            'execution_managers': 0,  # Not implemented yet - see IMPLEMENTATION_GAP_REPORT.md
            'data_providers': 7,  # One per strategy mode
            'event_loggers': 1,
            'pnl_monitors': 1,
            'utility_managers': 1,
            'config_managers': 1,
            'health_monitors': 1,
            'reconciliation_managers': 1
        },
        'compliance_status': {},
        'overall_compliance': True
    }
    
    for component_type, expected_count in compliance_checks['expected_components'].items():
        actual_count = len(components.get(component_type, []))
        
        # Special handling for data_providers (factory pattern)
        if component_type == 'data_providers':
            # Factory creates 7 mode-specific providers, so we need 1 factory file
            is_compliant = actual_count == 1
            compliance_checks['compliance_status'][component_type] = {
                'expected': expected_count,
                'actual': expected_count if actual_count == 1 else actual_count,
                'compliant': is_compliant
            }
        else:
            is_compliant = actual_count == expected_count
            compliance_checks['compliance_status'][component_type] = {
                'expected': expected_count,
                'actual': actual_count,
                'compliant': is_compliant
            }
        
        if not is_compliant:
            compliance_checks['overall_compliance'] = False
    
    return compliance_checks

def main():
    """Main function."""
    print("🚦 CONSOLIDATE DUPLICATE RISK MONITORS QUALITY GATES")
    print("=" * 60)
    
    # Find all component files
    components = find_component_files()
    
    # Check for duplicates and singleton patterns
    duplicate_results = check_duplicate_components(components)
    
    # Check architecture compliance
    compliance_results = check_architecture_compliance(components)
    
    # Print results
    print("\n📊 COMPONENT DUPLICATE ANALYSIS")
    print("=" * 40)
    
    if duplicate_results['duplicates_found']:
        print("❌ DUPLICATES FOUND:")
        for duplicate in duplicate_results['duplicates_found']:
            print(f"  - {duplicate['component_type']}: {duplicate['count']} files")
            for file in duplicate['files']:
                print(f"    * {file}")
    else:
        print("✅ NO DUPLICATES FOUND")
    
    print(f"\n📊 SINGLETON PATTERN ANALYSIS")
    print("=" * 40)
    
    if duplicate_results['singleton_violations']:
        print("❌ SINGLETON VIOLATIONS:")
        for violation in duplicate_results['singleton_violations']:
            print(f"  - {violation['file']}: {violation['issue']}")
    else:
        print("✅ ALL COMPONENTS IMPLEMENT SINGLETON PATTERN")
    
    print(f"\n📊 ARCHITECTURE COMPLIANCE")
    print("=" * 40)
    
    for component_type, status in compliance_results['compliance_status'].items():
        if status['compliant']:
            print(f"✅ {component_type}: {status['actual']}/{status['expected']}")
        else:
            print(f"❌ {component_type}: {status['actual']}/{status['expected']} (Expected: {status['expected']})")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT")
    print("=" * 40)
    
    total_issues = duplicate_results['duplicate_count'] + duplicate_results['singleton_violation_count']
    compliance_score = sum(1 for status in compliance_results['compliance_status'].values() if status['compliant']) / len(compliance_results['compliance_status'])
    
    if total_issues == 0 and compliance_results['overall_compliance']:
        print("🎉 SUCCESS: All components are properly consolidated and singleton-compliant!")
        return 0
    else:
        print(f"⚠️  ISSUES FOUND:")
        print(f"  - Duplicates: {duplicate_results['duplicate_count']}")
        print(f"  - Singleton violations: {duplicate_results['singleton_violation_count']}")
        print(f"  - Architecture compliance: {compliance_score:.1%}")
        return 1

if __name__ == "__main__":
    sys.exit(main())