#!/usr/bin/env python3
"""
Quality Gate: Component Data Flow Architecture
Validates that components use parameter-based data flow instead of direct component calls.
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
    
    search_dirs = [
        "core/strategies/components/",
        "core/math/",
        "core/interfaces/",
        "core/services/",
        "core/utilities/",
        "infrastructure/config/",
        "infrastructure/logging/",
        "infrastructure/monitoring/",
        "infrastructure/persistence/"
    ]
    
    for search_dir in search_dirs:
        full_path = os.path.join(backend_dir, search_dir)
        if os.path.exists(full_path):
            for file in os.listdir(full_path):
                if file.endswith('.py') and not file.startswith('__'):
                    component_files.append(os.path.join(full_path, file))
    
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

def check_parameter_based_flow(file_path: str) -> Dict[str, any]:
    """Check if component uses parameter-based data flow."""
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

def validate_data_flow_architecture(component_files: List[str]) -> Dict[str, any]:
    """Validate overall data flow architecture."""
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
    print("🚦 COMPONENT DATA FLOW ARCHITECTURE QUALITY GATES")
    print("=" * 60)
    
    # Find component files
    component_files = find_component_files()
    print(f"📁 Found {len(component_files)} component files")
    
    # Validate data flow architecture
    results = validate_data_flow_architecture(component_files)
    
    # Print results
    print(f"\n📊 DATA FLOW ARCHITECTURE ANALYSIS")
    print("=" * 50)
    
    print(f"Components Analyzed: {results['components_analyzed']}")
    print(f"Compliant Components: {results['compliant_components']}")
    print(f"Non-Compliant Components: {results['non_compliant_components']}")
    
    if results['data_flow_violations']:
        print(f"\n❌ DATA FLOW VIOLATIONS FOUND:")
        for violation in results['data_flow_violations'][:10]:  # Show first 10
            print(f"  - {violation['method']}: {violation['issue']} (Line {violation['line']})")
        if len(results['data_flow_violations']) > 10:
            print(f"  ... and {len(results['data_flow_violations']) - 10} more violations")
    else:
        print(f"\n✅ NO DATA FLOW VIOLATIONS FOUND")
    
    print(f"\n📊 PARAMETER USAGE STATISTICS")
    print("=" * 50)
    
    for component, stats in results['parameter_usage_stats'].items():
        status = "✅" if stats['is_compliant'] else "❌"
        print(f"{status} {component}: {stats['compliance_score']:.2f}")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT")
    print("=" * 50)
    
    compliance_rate = results['compliant_components'] / max(results['components_analyzed'], 1)
    
    if results['overall_compliance'] and compliance_rate >= 0.8:
        print("🎉 SUCCESS: Data flow architecture is compliant!")
        print(f"   Compliance Rate: {compliance_rate:.1%}")
        return 0
    else:
        print("⚠️  ISSUES FOUND:")
        print(f"   Compliance Rate: {compliance_rate:.1%}")
        print(f"   Data Flow Violations: {len(results['data_flow_violations'])}")
        return 1

if __name__ == "__main__":
    sys.exit(main())