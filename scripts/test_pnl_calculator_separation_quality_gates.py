#!/usr/bin/env python3
"""
PnL Monitor Read/Calculate Separation Quality Gates

This script tests that the PnL Monitor has proper separation between:
1. Read-only operations (getting cached/stored results)
2. Calculation operations (performing new P&L calculations)

Reference: pnl_monitor_ARCHITECTURE_ANALYSIS.md
"""

import sys
import os
import ast
import re
from typing import Dict, List, Set, Tuple
from pathlib import Path

# Add the backend src to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

def analyze_pnl_monitor_separation() -> Dict[str, any]:
    """Analyze PnL Monitor for read/calculate separation issues."""
    
    pnl_monitor_path = Path(__file__).parent.parent / 'backend' / 'src' / 'basis_strategy_v1' / 'core' / 'components' / 'pnl_monitor.py'
    
    if not pnl_monitor_path.exists():
        return {
            'status': 'FAILED',
            'error': f'PnL Monitor file not found: {pnl_monitor_path}',
            'violations': [],
            'recommendations': []
        }
    
    with open(pnl_monitor_path, 'r') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return {
            'status': 'FAILED',
            'error': f'Syntax error in PnL Monitor: {e}',
            'violations': [],
            'recommendations': []
        }
    
    violations = []
    recommendations = []
    
    # Find the PnLMonitor class
    pnl_monitor_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'PnLMonitor':
            pnl_monitor_class = node
            break
    
    if not pnl_monitor_class:
        violations.append({
            'type': 'MISSING_CLASS',
            'severity': 'HIGH',
            'message': 'PnLMonitor class not found',
            'line': 0
        })
        return {
            'status': 'FAILED',
            'violations': violations,
            'recommendations': recommendations
        }
    
    # Analyze methods in PnLMonitor class
    methods = []
    for node in pnl_monitor_class.body:
        if isinstance(node, ast.FunctionDef):
            methods.append({
                'name': node.name,
                'line': node.lineno,
                'is_private': node.name.startswith('_'),
                'docstring': ast.get_docstring(node) or '',
                'args': [arg.arg for arg in node.args.args]
            })
    
    # Check for read/calculate separation issues
    read_methods = []
    calculate_methods = []
    ambiguous_methods = []
    
    for method in methods:
        method_name = method['name']
        docstring = method['docstring'].lower()
        
        # Identify read-only methods
        if (method_name.startswith('get_') and 
            not method_name.startswith('get_current_pnl') and
            'calculate' not in docstring and
            'compute' not in docstring):
            read_methods.append(method)
        
        # Identify calculation methods
        elif (method_name.startswith('calculate_') or 
              method_name.startswith('_calculate_') or
              'calculate' in docstring or
              'compute' in docstring):
            calculate_methods.append(method)
        
        # Identify ambiguous methods
        elif (method_name.startswith('get_') and 
              ('calculate' in docstring or 'compute' in docstring)):
            ambiguous_methods.append(method)
    
    # Check for specific issues
    
    # 1. Check if update_state exists (main calculation method)
    update_state = None
    for method in methods:
        if method['name'] == 'update_state':
            update_state = method
            break
    
    if not update_state:
        violations.append({
            'type': 'MISSING_CALCULATION_METHOD',
            'severity': 'HIGH',
            'message': "Method 'update_state' not found - main calculation method required",
            'line': 0,
            'method': 'update_state',
            'recommendation': 'Add update_state() method for P&L calculations'
        })
    
    # 2. Check that deprecated get_current_pnl has been removed
    get_current_pnl = None
    for method in methods:
        if method['name'] == 'get_current_pnl':
            get_current_pnl = method
            break
    
    if get_current_pnl:
        violations.append({
            'type': 'DEPRECATED_METHOD_STILL_PRESENT',
            'severity': 'HIGH',
            'message': f"Deprecated method 'get_current_pnl' should have been removed after migration period",
            'line': get_current_pnl['line'],
            'method': 'get_current_pnl',
            'recommendation': 'Remove deprecated get_current_pnl() method - migration period complete'
        })
    
    # 2. Check for missing read-only methods
    expected_read_methods = [
        'get_latest_pnl',
        'get_pnl_history', 
        'get_cumulative_attribution',
        'get_pnl_summary'
    ]
    
    existing_read_methods = [m['name'] for m in read_methods]
    missing_read_methods = [m for m in expected_read_methods if m not in existing_read_methods]
    
    if missing_read_methods:
        violations.append({
            'type': 'MISSING_READ_METHODS',
            'severity': 'MEDIUM',
            'message': f'Missing read-only methods: {missing_read_methods}',
            'line': 0,
            'missing_methods': missing_read_methods,
            'recommendation': 'Add read-only methods to avoid unnecessary recalculations'
        })
    
    # 3. Check for state storage
    state_variables = []
    for node in ast.walk(pnl_monitor_class):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                    state_variables.append(target.attr)
    
    expected_state_vars = ['latest_pnl_result', 'pnl_history', 'calculation_timestamps']
    missing_state_vars = [var for var in expected_state_vars if var not in state_variables]
    
    if missing_state_vars:
        violations.append({
            'type': 'MISSING_STATE_STORAGE',
            'severity': 'MEDIUM',
            'message': f'Missing state storage variables: {missing_state_vars}',
            'line': 0,
            'missing_vars': missing_state_vars,
            'recommendation': 'Add state storage for caching P&L results'
        })
    
    # Generate recommendations
    if violations:
        recommendations.extend([
            "Implement clear separation between read-only and calculation operations",
            "Add read-only methods for accessing cached P&L results",
            "Rename misleading method names to reflect their actual behavior",
            "Add state storage for caching expensive calculations",
            "Update documentation to clearly indicate read vs calculate operations"
        ])
    
    # Determine overall status
    high_severity_violations = [v for v in violations if v['severity'] == 'HIGH']
    medium_severity_violations = [v for v in violations if v['severity'] == 'MEDIUM']
    
    if high_severity_violations:
        status = 'FAILED'
    elif medium_severity_violations:
        status = 'WARNING'
    elif violations:
        status = 'WARNING'
    else:
        status = 'PASSED'
    
    return {
        'status': status,
        'violations': violations,
        'recommendations': recommendations,
        'summary': {
            'total_methods': len(methods),
            'read_methods': len(read_methods),
            'calculate_methods': len(calculate_methods),
            'ambiguous_methods': len(ambiguous_methods),
            'high_severity_violations': len(high_severity_violations),
            'medium_severity_violations': len(medium_severity_violations)
        }
    }

def main():
    """Main quality gate function."""
    print("🔍 PnL Monitor Read/Calculate Separation Quality Gates")
    print("=" * 60)
    
    try:
        results = analyze_pnl_monitor_separation()
        
        print(f"Status: {results['status']}")
        print()
        
        if results.get('error'):
            print(f"❌ Error: {results['error']}")
            return
        
        summary = results.get('summary', {})
        print(f"📊 Summary:")
        print(f"  Total Methods: {summary.get('total_methods', 0)}")
        print(f"  Read Methods: {summary.get('read_methods', 0)}")
        print(f"  Calculate Methods: {summary.get('calculate_methods', 0)}")
        print(f"  Ambiguous Methods: {summary.get('ambiguous_methods', 0)}")
        print()
        
        violations = results.get('violations', [])
        if violations:
            print(f"🚨 Violations Found: {len(violations)}")
            print()
            
            for i, violation in enumerate(violations, 1):
                severity_emoji = {
                    'HIGH': '🔴',
                    'MEDIUM': '🟡', 
                    'LOW': '🟢'
                }.get(violation['severity'], '⚪')
                
                print(f"{i}. {severity_emoji} {violation['type']} (Line {violation['line']})")
                print(f"   {violation['message']}")
                if 'recommendation' in violation:
                    print(f"   💡 {violation['recommendation']}")
                print()
        else:
            print("✅ No violations found!")
        
        recommendations = results.get('recommendations', [])
        if recommendations:
            print("💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
            print()
        
        # Print status
        if results['status'] == 'PASSED':
            print("✅ PnL Monitor Read/Calculate Separation: PASSED")
        elif results['status'] == 'WARNING':
            print("⚠️  PnL Monitor Read/Calculate Separation: WARNING")
        else:
            print("❌ PnL Monitor Read/Calculate Separation: FAILED")
            
    except Exception as e:
        print(f"❌ Quality gate failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
