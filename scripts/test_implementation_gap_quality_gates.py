#!/usr/bin/env python3
"""
Quality Gate: Implementation Gap Detection
Compares component specifications against actual code implementation to identify gaps.
"""

import os
import re
import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import importlib.util

def find_component_specs(specs_dir: str = "docs/specs/") -> List[str]:
    """Find all component specification files."""
    specs = []
    for file in os.listdir(specs_dir):
        if file.endswith('.md') and file.startswith(('0', '1')):
            specs.append(os.path.join(specs_dir, file))
    return sorted(specs)

def find_component_implementations(backend_dir: str = "backend/src/basis_strategy_v1/") -> List[str]:
    """Find all component implementation files."""
    implementations = []
    
    # Search in multiple directories for component implementations
    search_dirs = [
        "core/strategies/components/",
        "core/math/",
        "core/interfaces/",
        "core/services/",
        "core/event_engine/",
        "core/execution/",
        "core/utilities/",
        "infrastructure/config/",
        "infrastructure/logging/",
        "infrastructure/persistence/",
        "infrastructure/monitoring/",
        "data_provider/"
    ]
    
    for search_dir in search_dirs:
        full_path = os.path.join(backend_dir, search_dir)
        if os.path.exists(full_path):
            for file in os.listdir(full_path):
                if file.endswith('.py') and not file.startswith('__'):
                    implementations.append(os.path.join(full_path, file))
    
    return sorted(implementations)

def extract_spec_methods(spec_file: str) -> Dict[str, List[str]]:
    """Extract documented methods from component spec."""
    try:
        with open(spec_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        methods = []
        config_params = []
        
        # Extract methods from "Core Methods" section
        core_methods_match = re.search(r'## Core Methods(.*?)(?=## |$)', content, re.DOTALL | re.MULTILINE)
        if core_methods_match:
            methods_text = core_methods_match.group(1)
            # Find method signatures - be more flexible with whitespace
            method_matches = re.findall(r'###\s+(\w+)\s*\([^)]*\)', methods_text)
            methods.extend(method_matches)
        else:
            pass  # No Core Methods section found
        
        # Also try to find all method patterns in the entire file as fallback
        all_method_matches = re.findall(r'###\s+(\w+)\s*\([^)]*\)', content)
        if all_method_matches:
            # Only add methods that look like actual method definitions (not headers)
            for method in all_method_matches:
                if method not in ['Config-Driven', 'Tracked', 'System-Level', 'Component-Specific', 'Environment', 'Universal', 'Component-Specific', 'Config', 'Input', 'Output', 'Data', 'Behavior', 'Data', 'Position', 'Backtest', 'Live', 'Complete', 'Key', 'ComponentFactory', 'Component-Specific', 'Event', 'Event', 'Structured', 'POS-001', 'POS-002', 'POS-003', 'POS-004', 'Unit', 'Integration', 'End-to-End', 'Provides', 'Receives', 'Tight', 'Architecture', 'Completed', 'TODO', 'Quality', 'Task', 'Component', 'Architecture', 'Configuration']:
                    if method not in methods:  # Avoid duplicates
                        methods.append(method)
        
        # Extract config parameters from "Configuration Parameters" section
        config_match = re.search(r'## Configuration Parameters(.*?)(?=## |$)', content, re.DOTALL)
        if config_match:
            config_text = config_match.group(1)
            # Find parameter definitions
            param_matches = re.findall(r'`(\w+)`', config_text)
            config_params.extend(param_matches)
        
        return {
            'methods': methods,
            'config_params': config_params,
            'file': spec_file
        }
    except Exception as e:
        print(f"Error reading spec file {spec_file}: {e}")
        return {'methods': [], 'config_params': [], 'file': spec_file}

def extract_implementation_methods(impl_file: str) -> Dict[str, List[str]]:
    """Extract actual methods from component implementation."""
    try:
        with open(impl_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST to find class methods
        tree = ast.parse(content)
        methods = []
        config_usage = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                methods.append(node.name)
            elif isinstance(node, ast.Attribute):
                if hasattr(node.value, 'id') and node.value.id == 'config':
                    config_usage.append(node.attr)
        
        return {
            'methods': methods,
            'config_usage': config_usage,
            'file': impl_file
        }
    except Exception as e:
        print(f"Error reading implementation file {impl_file}: {e}")
        return {'methods': [], 'config_usage': [], 'file': impl_file}

def check_canonical_compliance(spec_file: str, impl_file: str) -> Dict[str, any]:
    """Check if implementation follows canonical patterns."""
    try:
        with open(impl_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compliance_checks = {
            'has_config_driven_loop': False,
            'has_mode_agnostic_logic': True,
            'has_graceful_data_handling': False,
            'has_component_factory': False,
            'has_error_handling': False
        }
        
        # Check for config-driven patterns
        if 'for' in content and 'config' in content and 'enabled' in content:
            compliance_checks['has_config_driven_loop'] = True
        
        # Check for mode-specific if/else (anti-pattern)
        if re.search(r'if.*mode.*==.*[\'"]', content):
            compliance_checks['has_mode_agnostic_logic'] = False
        
        # Check for graceful data handling
        if 'None' in content and ('return' in content or 'skip' in content):
            compliance_checks['has_graceful_data_handling'] = True
        
        # Check for ComponentFactory pattern
        if 'ComponentFactory' in content:
            compliance_checks['has_component_factory'] = True
        
        # Check for structured error handling
        if 'ComponentError' in content or 'raise' in content:
            compliance_checks['has_error_handling'] = True
        
        return compliance_checks
    except Exception as e:
        print(f"Error checking canonical compliance for {impl_file}: {e}")
        return {}

def generate_gap_report(specs: List[str], implementations: List[str]) -> Dict[str, any]:
    """Generate comprehensive implementation gap report."""
    print("🔍 IMPLEMENTATION GAP ANALYSIS")
    print("=" * 60)
    
    gap_report = {
        'components': {},
        'summary': {
            'total_specs': len(specs),
            'total_implementations': len(implementations),
            'canonical_examples': [],
            'high_priority_gaps': [],
            'medium_priority_gaps': [],
            'low_priority_gaps': []
        }
    }
    
    # Process each spec file
    for spec_file in specs:
        spec_name = os.path.basename(spec_file).replace('.md', '')
        print(f"\n📋 Analyzing {spec_name}...")
        
        # Extract spec requirements
        spec_data = extract_spec_methods(spec_file)
        
        # Find corresponding implementation using improved matching
        impl_file = None
        spec_name_clean = spec_name.lower().replace('_', '').replace('0', '').replace('1', '').replace('2', '').replace('3', '').replace('4', '').replace('5', '').replace('6', '').replace('7', '').replace('8', '').replace('9', '')
        
        # Create mapping for known components
        component_mapping = {
            'positionmonitor': 'position_monitor.py',
            'exposuremonitor': 'exposure_monitor.py', 
            'riskmonitor': 'risk_monitor.py',
            'pnlcalculator': 'pnl_calculator.py',
            'strategymanager': 'strategy_manager.py',
            'executionmanager': 'execution_manager.py',
            'eventlogger': 'event_logger.py',
            'dataprovider': 'data_provider.py',
            'positionupdatehandler': 'position_update_handler.py',
            'executioninterfaces': 'cex_execution_interface.py',
            'executioninterfacefactory': 'execution_interface_factory.py',
            'executioninterfacemanager': 'execution_interface_manager.py',
            'reconciliationcomponent': 'reconciliation_manager.py',
            'frontendspec': 'frontend_spec.py',
            'backtestservice': 'backtest_service.py',
            'livetradingservice': 'live_trading_service.py',
            'eventdrivenstrategyengine': 'event_driven_strategy_engine.py',
            'mathutilities': 'utility_manager.py',
            'healtherrorsystems': 'health_monitor.py',
            'resultsstore': 'results_store.py',
            'configuration': 'config_manager.py'
        }
        
        if spec_name_clean in component_mapping:
            expected_file = component_mapping[spec_name_clean]
            for impl in implementations:
                if impl.endswith(expected_file):
                    impl_file = impl
                    break
        
        # Fallback to original matching if not found
        if not impl_file:
            for impl in implementations:
                if spec_name.lower().replace('_', '') in impl.lower().replace('_', ''):
                    impl_file = impl
                    break
        
        if not impl_file:
            print(f"  ❌ No implementation found for {spec_name}")
            gap_report['components'][spec_name] = {
                'status': 'MISSING_IMPLEMENTATION',
                'priority': 'HIGH',
                'methods_implemented': 0,
                'methods_total': len(spec_data['methods']),
                'config_params_implemented': 0,
                'config_params_total': len(spec_data['config_params']),
                'canonical_compliance': 0
            }
            gap_report['summary']['high_priority_gaps'].append(f"{spec_name}: Missing implementation")
            continue
        
        # Extract implementation details
        impl_data = extract_implementation_methods(impl_file)
        compliance = check_canonical_compliance(spec_file, impl_file)
        
        # Calculate gaps
        spec_methods = set(spec_data['methods'])
        impl_methods = set(impl_data['methods'])
        missing_methods = spec_methods - impl_methods
        extra_methods = impl_methods - spec_methods
        
        spec_config = set(spec_data['config_params'])
        impl_config = set(impl_data['config_usage'])
        missing_config = spec_config - impl_config
        
        # Calculate compliance score
        compliance_score = sum(compliance.values()) / len(compliance) if compliance else 0
        
        # Determine priority
        priority = 'LOW'
        if missing_methods or missing_config:
            priority = 'HIGH' if len(missing_methods) > 2 or len(missing_config) > 2 else 'MEDIUM'
        elif compliance_score < 0.6:
            priority = 'MEDIUM'
        
        # Check if canonical example
        is_canonical = spec_name in ['02_EXPOSURE_MONITOR', '03_RISK_MONITOR']
        if is_canonical:
            gap_report['summary']['canonical_examples'].append(spec_name)
        
        component_status = {
            'status': 'CANONICAL' if is_canonical else ('COMPLIANT' if not missing_methods and not missing_config and compliance_score > 0.8 else 'NEEDS_WORK'),
            'priority': priority,
            'methods_implemented': len(spec_methods & impl_methods),
            'methods_total': len(spec_methods),
            'missing_methods': list(missing_methods),
            'extra_methods': list(extra_methods),
            'config_params_implemented': len(spec_config & impl_config),
            'config_params_total': len(spec_config),
            'missing_config': list(missing_config),
            'canonical_compliance': compliance_score,
            'compliance_details': compliance,
            'implementation_file': impl_file
        }
        
        gap_report['components'][spec_name] = component_status
        
        # Add to priority lists
        if priority == 'HIGH':
            gap_report['summary']['high_priority_gaps'].append(f"{spec_name}: {len(missing_methods)} missing methods, {len(missing_config)} missing config")
        elif priority == 'MEDIUM':
            gap_report['summary']['medium_priority_gaps'].append(f"{spec_name}: Compliance score {compliance_score:.2f}")
        else:
            gap_report['summary']['low_priority_gaps'].append(f"{spec_name}: Minor issues")
        
        # Print component summary
        status_icon = "✅" if component_status['status'] in ['CANONICAL', 'COMPLIANT'] else "⚠️" if priority == 'MEDIUM' else "❌"
        print(f"  {status_icon} {component_status['status']} ({priority} priority)")
        print(f"     Methods: {component_status['methods_implemented']}/{component_status['methods_total']}")
        print(f"     Config: {component_status['config_params_implemented']}/{component_status['config_params_total']}")
        print(f"     Compliance: {compliance_score:.2f}")
        
        if missing_methods:
            print(f"     Missing methods: {', '.join(missing_methods)}")
        if missing_config:
            print(f"     Missing config: {', '.join(missing_config)}")
    
    return gap_report

def print_summary_report(gap_report: Dict[str, any]):
    """Print summary report."""
    print("\n" + "=" * 60)
    print("📊 IMPLEMENTATION GAP SUMMARY")
    print("=" * 60)
    
    summary = gap_report['summary']
    
    print(f"Total Components: {summary['total_specs']}")
    print(f"Canonical Examples: {', '.join(summary['canonical_examples'])}")
    
    print(f"\n🔴 HIGH Priority Gaps ({len(summary['high_priority_gaps'])}):")
    for gap in summary['high_priority_gaps']:
        print(f"  - {gap}")
    
    print(f"\n🟡 MEDIUM Priority Gaps ({len(summary['medium_priority_gaps'])}):")
    for gap in summary['medium_priority_gaps']:
        print(f"  - {gap}")
    
    print(f"\n🟢 LOW Priority Gaps ({len(summary['low_priority_gaps'])}):")
    for gap in summary['low_priority_gaps']:
        print(f"  - {gap}")
    
    # Calculate overall success rate
    total_components = len(gap_report['components'])
    compliant_components = sum(1 for c in gap_report['components'].values() 
                             if c['status'] in ['CANONICAL', 'COMPLIANT'])
    success_rate = (compliant_components / total_components * 100) if total_components > 0 else 0
    
    print(f"\n🎯 Overall Implementation Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 SUCCESS: Implementation gap quality gates passed!")
        return True
    else:
        print("⚠️  WARNING: Implementation gaps detected - review required")
        return False

def main():
    """Main function."""
    print("🚦 IMPLEMENTATION GAP QUALITY GATES")
    print("=" * 60)
    
    # Find spec and implementation files
    specs = find_component_specs()
    implementations = find_component_implementations()
    
    if not specs:
        print("❌ No component specifications found in docs/specs/")
        return 1
    
    if not implementations:
        print("⚠️  No component implementations found in backend/src/basis_strategy_v1/core/components/")
        print("   This may indicate the backend structure has changed")
    
    # Generate gap report
    gap_report = generate_gap_report(specs, implementations)
    
    # Print summary
    success = print_summary_report(gap_report)
    
    # Save detailed report
    try:
        import json
        with open('implementation_gap_report.json', 'w') as f:
            json.dump(gap_report, f, indent=2)
        print(f"\n📄 Detailed report saved to: implementation_gap_report.json")
    except Exception as e:
        print(f"⚠️  Could not save detailed report: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
