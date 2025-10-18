#!/usr/bin/env python3
"""
Quality Gate: Component Communication Architecture
Validates that components use reference-based architecture for component-to-component communication
following the patterns documented in WORKFLOW_GUIDE.md and REFERENCE_ARCHITECTURE_CANONICAL.md.
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_component_files(backend_dir: str = "backend/src/basis_strategy_v1/") -> List[str]:
    """Find all component implementation files."""
    component_files = []
    backend_path = Path(backend_dir)
    
    search_dirs = [
        "core/components/",
        "core/strategies/",
        "core/math/",
        "core/interfaces/",
        "core/utilities/",
        "core/event_engine/",
        "core/health/",
        "core/execution/",
        "core/reconciliation/",
        "infrastructure/config/",
        "infrastructure/logging/",
        "infrastructure/monitoring/",
        "infrastructure/persistence/"
    ]
    
    for search_dir in search_dirs:
        full_path = backend_path / search_dir
        if full_path.exists():
            for file in full_path.rglob("*.py"):
                if not file.name.startswith("__") and not file.name.startswith("test_"):
                    component_files.append(str(file))
    
    return component_files

def analyze_data_flow_patterns(file_path: str) -> Dict[str, any]:
    """Analyze data flow patterns in a component file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for canonical data provider patterns
        canonical_patterns = {
            'uses_get_data': bool(re.search(r'data_provider\.get_data\(|self\.data_provider\.get_data\(', content)),
            'uses_standardized_structure': bool(re.search(r"market_data\['prices'\]|market_data\['rates'\]|protocol_data\['aave_indexes'\]|execution_data\['wallet_balances'\]", content)),
            'non_canonical_patterns': len(re.findall(r'data_provider\.get_([a-zA-Z_]+)\(|self\.data_provider\.get_([a-zA-Z_]+)\(', content))
        }
        
        # Parse AST
        tree = ast.parse(content)
        
        analysis = {
            'file': file_path,
            'component_calls': [],
            'parameter_usage': [],
            'data_flow_violations': [],
            'method_signatures': [],
            'data_flow_compliant': True,
            'canonical_patterns': canonical_patterns
        }
        
        # Find all method definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_name = node.name
                analysis['method_signatures'].append(method_name)
                
                # Check for component calls within methods
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute):
                            # Check if calling another component
                            if hasattr(child.func.value, 'id'):
                                component_name = child.func.value.id
                                if component_name.endswith('_monitor') or component_name.endswith('_manager') or component_name.endswith('_calculator'):
                                    analysis['component_calls'].append({
                                        'method': method_name,
                                        'component': component_name,
                                        'call': ast.unparse(child)
                                    })
                                    analysis['data_flow_violations'].append({
                                        'method': method_name,
                                        'issue': f'Direct component call to {component_name}',
                                        'line': child.lineno
                                    })
                                    analysis['data_flow_compliant'] = False
                
                # Check for parameter usage
                for arg in node.args.args:
                    if arg.arg not in ['self', 'cls']:
                        analysis['parameter_usage'].append({
                            'method': method_name,
                            'parameter': arg.arg
                        })
        
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing data flow in {file_path}: {e}")
        return {
            'file': file_path,
            'error': str(e),
            'data_flow_compliant': False
        }

def analyze_reference_based_architecture(file_path: str) -> Dict[str, any]:
    """Analyze reference-based architecture patterns in a component file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST
        tree = ast.parse(content)
        
        analysis = {
            'file': file_path,
            'has_init_method': False,
            'reference_storage': [],
            'component_calls': [],
            'runtime_parameter_violations': [],
            'data_provider_access': [],
            'read_calls': [],
            'write_calls': [],
            'is_compliant': True,
            'violations': []
        }
        
        # Find __init__ method and analyze reference storage
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == '__init__':
                analysis['has_init_method'] = True
                
                # Check for reference storage patterns
                for child in ast.walk(node):
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                if target.attr.endswith('_monitor') or target.attr.endswith('_manager') or target.attr.endswith('_calculator') or target.attr == 'data_provider':
                                    analysis['reference_storage'].append({
                                        'attribute': target.attr,
                                        'line': child.lineno
                                    })
        
        # Analyze method calls throughout the file
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # Check for component method calls
                    if isinstance(node.func.value, ast.Attribute) and isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == 'self':
                        component_name = node.func.value.attr
                        method_name = node.func.attr
                        
                        if component_name.endswith('_monitor') or component_name.endswith('_manager') or component_name.endswith('_calculator'):
                            call_info = {
                                'component': component_name,
                                'method': method_name,
                                'line': node.lineno,
                                'call_type': 'read' if method_name.startswith('get_') else 'write'
                            }
                            analysis['component_calls'].append(call_info)
                            
                            if call_info['call_type'] == 'read':
                                analysis['read_calls'].append(call_info)
                            else:
                                analysis['write_calls'].append(call_info)
                    
                    # Check for data_provider access
                    elif isinstance(node.func.value, ast.Attribute) and isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == 'self' and node.func.value.attr == 'data_provider':
                        analysis['data_provider_access'].append({
                            'method': node.func.attr,
                            'line': node.lineno
                        })
        
        # Check for runtime parameter violations (component references passed as parameters in non-__init__ methods)
        # Skip factory methods and static methods that legitimately pass component references
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name != '__init__':
                # Skip factory methods, static methods, and dependency setup methods
                is_factory_method = any(factory in node.name for factory in ['create_', 'build_', 'make_', 'get_'])
                is_static_method = any(decorator.id == 'staticmethod' for decorator in node.decorator_list if hasattr(decorator, 'id'))
                is_dependency_method = any(dep in node.name for dep in ['set_dependencies', '_set_dependencies', 'configure'])
                
                if not is_factory_method and not is_static_method and not is_dependency_method:
                    for arg in node.args.args:
                        if arg.arg not in ['self', 'cls'] and (arg.arg.endswith('_monitor') or arg.arg.endswith('_manager') or arg.arg.endswith('_calculator') or arg.arg == 'data_provider'):
                            analysis['runtime_parameter_violations'].append({
                                'method': node.name,
                                'parameter': arg.arg,
                                'line': node.lineno
                            })
                            analysis['violations'].append(f"Component reference '{arg.arg}' passed as runtime parameter in {node.name}")
                            analysis['is_compliant'] = False
        
        # Validate reference-based architecture compliance
        # Only require __init__ method if the component uses data_provider or other components
        # Skip utility classes (calculators) that don't need component references
        file_name = os.path.basename(file_path)
        is_utility_class = any(util in file_name for util in ['calculator', 'utils', 'helper', 'factory', 'models', 'logging', 'metrics'])
        
        if not analysis['has_init_method'] and (analysis['data_provider_access'] or analysis['component_calls']) and not is_utility_class:
            analysis['violations'].append("No __init__ method found for reference storage")
            analysis['is_compliant'] = False
        
        # Check if data_provider is accessed via stored reference
        if analysis['data_provider_access']:
            has_stored_reference = any(ref['attribute'] == 'data_provider' for ref in analysis['reference_storage'])
            if not has_stored_reference:
                analysis['violations'].append("data_provider accessed but not stored as reference in __init__")
                analysis['is_compliant'] = False
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing reference-based architecture in {file_path}: {e}")
        return {
            'file': file_path,
            'error': str(e),
            'is_compliant': False,
            'violations': [f"Analysis error: {e}"]
        }

def check_parameter_based_flow(file_path: str) -> Dict[str, any]:
    """Check if component uses parameter-based data flow (legacy function - kept for compatibility)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for patterns that indicate parameter-based flow
        patterns = {
            'parameter_usage': len(re.findall(r'def \w+\([^)]*\)', content)),
            'data_passing': len(re.findall(r'data\[', content)) + len(re.findall(r'\.get\(', content)),
            'component_calls': len(re.findall(r'self\.\w+_monitor\.', content)) + len(re.findall(r'self\.\w+_manager\.', content)),
            'return_statements': len(re.findall(r'return.*data', content, re.IGNORECASE))
        }
        
        # Calculate compliance score
        total_patterns = sum(patterns.values())
        compliant_patterns = patterns['parameter_usage'] + patterns['data_passing'] + patterns['return_statements']
        violation_patterns = patterns['component_calls']
        
        compliance_score = (compliant_patterns - violation_patterns) / max(total_patterns, 1)
        
        return {
            'file': file_path,
            'patterns': patterns,
            'compliance_score': compliance_score,
            'is_compliant': compliance_score > 0.5
        }
    except Exception as e:
        logger.error(f"Error checking parameter-based flow in {file_path}: {e}")
        return {
            'file': file_path,
            'error': str(e),
            'is_compliant': False
        }

def validate_reference_based_architecture(component_files: List[str]) -> Dict[str, any]:
    """Validate reference-based architecture compliance."""
    results = {
        'components_analyzed': 0,
        'compliant_components': 0,
        'non_compliant_components': 0,
        'reference_storage_violations': [],
        'runtime_parameter_violations': [],
        'data_provider_access_violations': [],
        'component_call_stats': {
            'total_read_calls': 0,
            'total_write_calls': 0,
            'read_calls_by_component': {},
            'write_calls_by_component': {}
        },
        'overall_compliance': True,
        'detailed_violations': []
    }
    
    for file_path in component_files:
        # Analyze reference-based architecture
        ref_analysis = analyze_reference_based_architecture(file_path)
        results['components_analyzed'] += 1
        
        if ref_analysis.get('is_compliant', False):
            results['compliant_components'] += 1
        else:
            results['non_compliant_components'] += 1
            results['overall_compliance'] = False
            results['detailed_violations'].extend(ref_analysis.get('violations', []))
        
        # Collect reference storage violations (skip utility classes)
        file_name = os.path.basename(file_path)
        is_utility_class = any(util in file_name for util in ['calculator', 'utils', 'helper', 'factory', 'models', 'logging', 'metrics'])
        
        if not ref_analysis.get('has_init_method', False) and not is_utility_class:
            results['reference_storage_violations'].append({
                'file': file_path,
                'issue': 'No __init__ method found'
            })
        
        # Collect runtime parameter violations
        results['runtime_parameter_violations'].extend(ref_analysis.get('runtime_parameter_violations', []))
        
        # Collect data provider access violations
        if ref_analysis.get('data_provider_access') and not any(ref['attribute'] == 'data_provider' for ref in ref_analysis.get('reference_storage', [])):
            results['data_provider_access_violations'].append({
                'file': file_path,
                'issue': 'data_provider accessed but not stored as reference'
            })
        
        # Collect component call statistics
        for call in ref_analysis.get('read_calls', []):
            results['component_call_stats']['total_read_calls'] += 1
            component = call['component']
            if component not in results['component_call_stats']['read_calls_by_component']:
                results['component_call_stats']['read_calls_by_component'][component] = 0
            results['component_call_stats']['read_calls_by_component'][component] += 1
        
        for call in ref_analysis.get('write_calls', []):
            results['component_call_stats']['total_write_calls'] += 1
            component = call['component']
            if component not in results['component_call_stats']['write_calls_by_component']:
                results['component_call_stats']['write_calls_by_component'][component] = 0
            results['component_call_stats']['write_calls_by_component'][component] += 1
    
    return results

def validate_data_flow_architecture(component_files: List[str]) -> Dict[str, any]:
    """Validate overall data flow architecture (legacy function - kept for compatibility)."""
    results = {
        'components_analyzed': 0,
        'compliant_components': 0,
        'non_compliant_components': 0,
        'data_flow_violations': [],
        'parameter_usage_stats': {},
        'overall_compliance': True
    }
    
    for file_path in component_files:
        # Analyze data flow patterns
        flow_analysis = analyze_data_flow_patterns(file_path)
        results['components_analyzed'] += 1
        
        if flow_analysis.get('data_flow_compliant', False):
            results['compliant_components'] += 1
        else:
            results['non_compliant_components'] += 1
            results['data_flow_violations'].extend(flow_analysis.get('data_flow_violations', []))
        
        # Check parameter-based flow
        param_analysis = check_parameter_based_flow(file_path)
        if not param_analysis.get('is_compliant', False):
            results['overall_compliance'] = False
        
        # Collect parameter usage stats
        component_name = os.path.basename(file_path).replace('.py', '')
        results['parameter_usage_stats'][component_name] = {
            'compliance_score': param_analysis.get('compliance_score', 0),
            'is_compliant': param_analysis.get('is_compliant', False)
        }
    
    return results

def main():
    """Main function."""
    print("🚦 COMPONENT COMMUNICATION ARCHITECTURE QUALITY GATES")
    print("=" * 60)
    
    # Find component files
    component_files = find_component_files()
    print(f"📁 Found {len(component_files)} component files")
    
    # Validate reference-based architecture
    results = validate_reference_based_architecture(component_files)
    
    # Print results
    print(f"\n📊 REFERENCE-BASED ARCHITECTURE ANALYSIS")
    print("=" * 50)
    
    print(f"Components Analyzed: {results['components_analyzed']}")
    print(f"Compliant Components: {results['compliant_components']}")
    print(f"Non-Compliant Components: {results['non_compliant_components']}")
    
    # Print violations
    total_violations = (len(results['reference_storage_violations']) + 
                       len(results['runtime_parameter_violations']) + 
                       len(results['data_provider_access_violations']))
    
    if total_violations > 0:
        print(f"\n❌ ARCHITECTURE VIOLATIONS FOUND:")
        
        if results['reference_storage_violations']:
            print(f"  📦 Reference Storage Violations ({len(results['reference_storage_violations'])}):")
            for violation in results['reference_storage_violations'][:5]:
                print(f"    - {os.path.basename(violation['file'])}: {violation['issue']}")
        
        if results['runtime_parameter_violations']:
            print(f"  🔄 Runtime Parameter Violations ({len(results['runtime_parameter_violations'])}):")
            for violation in results['runtime_parameter_violations'][:5]:
                print(f"    - {violation['method']}: {violation['parameter']} (Line {violation['line']})")
        
        if results['data_provider_access_violations']:
            print(f"  📊 Data Provider Access Violations ({len(results['data_provider_access_violations'])}):")
            for violation in results['data_provider_access_violations'][:5]:
                print(f"    - {os.path.basename(violation['file'])}: {violation['issue']}")
        
        if len(results['detailed_violations']) > 10:
            print(f"  ... and {len(results['detailed_violations']) - 10} more detailed violations")
    else:
        print(f"\n✅ NO ARCHITECTURE VIOLATIONS FOUND")
    
    # Print component call statistics
    print(f"\n📊 COMPONENT CALL STATISTICS")
    print("=" * 50)
    
    stats = results['component_call_stats']
    print(f"Total Read Calls: {stats['total_read_calls']}")
    print(f"Total Write Calls: {stats['total_write_calls']}")
    
    if stats['read_calls_by_component']:
        print(f"\n📖 Read Calls by Component:")
        for component, count in sorted(stats['read_calls_by_component'].items()):
            print(f"  - {component}: {count}")
    
    if stats['write_calls_by_component']:
        print(f"\n✏️  Write Calls by Component:")
        for component, count in sorted(stats['write_calls_by_component'].items()):
            print(f"  - {component}: {count}")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT")
    print("=" * 50)
    
    compliance_rate = results['compliant_components'] / max(results['components_analyzed'], 1)
    
    if results['overall_compliance'] and compliance_rate >= 0.8:
        print("🎉 SUCCESS: Reference-based architecture is compliant!")
        print(f"   Compliance Rate: {compliance_rate:.1%}")
        print(f"   Component Calls: {stats['total_read_calls']} reads, {stats['total_write_calls']} writes")
        return 0
    else:
        print("⚠️  ISSUES FOUND:")
        print(f"   Compliance Rate: {compliance_rate:.1%}")
        print(f"   Total Violations: {total_violations}")
        print(f"   Reference Storage: {len(results['reference_storage_violations'])}")
        print(f"   Runtime Parameters: {len(results['runtime_parameter_violations'])}")
        print(f"   Data Provider Access: {len(results['data_provider_access_violations'])}")
        return 1

if __name__ == "__main__":
    sys.exit(main())