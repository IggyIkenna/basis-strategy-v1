#!/usr/bin/env python3
"""
Quality Gate: Utility Manager Compliance
Ensures components use centralized utility manager instead of inline calculations.
"""

import os
import re
import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

def find_component_files(backend_dir: str = "backend/src/basis_strategy_v1/") -> List[str]:
    """Find all component implementation files."""
    component_files = []
    
    # Search in multiple directories for component implementations
    search_dirs = [
        "core/components/",
        "core/strategies/components/",
        "core/math/",
        "core/interfaces/",
        "core/services/",
        "core/event_engine/",
        "core/execution/",
        "core/utilities/",
        "core/health/",
        "core/reconciliation/",
        "core/instructions/",
        "core/error_codes/",
    ]
    
    for search_dir in search_dirs:
        full_path = os.path.join(backend_dir, search_dir)
        if os.path.exists(full_path):
            for file in os.listdir(full_path):
                if file.endswith('.py') and not file.startswith('__'):
                    component_files.append(os.path.join(full_path, file))
    
    return component_files

def scan_for_inline_calculations(file_path: str) -> List[Dict]:
    """Scan file for inline utility calculations that should use utility manager."""
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return [{"error": f"Could not read file: {e}"}]
    
    # Patterns that indicate inline calculations that should use utility manager
    patterns = [
        {
            'name': 'liquidity_index_calculation',
            'pattern': r'(liquidity_index|supply_index|borrow_index).*=.*[+\-*/]',
            'description': 'Direct liquidity index calculations should use utility_manager.get_liquidity_index()'
        },
        {
            'name': 'price_conversion',
            'pattern': r'(price|rate).*=.*[+\-*/].*(price|rate)',
            'description': 'Price conversions should use utility_manager.convert_price()'
        },
        {
            'name': 'share_class_conversion',
            'pattern': r'(share_class|currency).*=.*[+\-*/]',
            'description': 'Share class conversions should use utility_manager.convert_to_share_class()'
        },
        {
            'name': 'oracle_price_lookup',
            'pattern': r'oracle_price.*=.*[0-9]',
            'description': 'Oracle price lookups should use utility_manager.get_oracle_price()'
        },
        {
            'name': 'market_price_lookup',
            'pattern': r'market_price.*=.*[0-9]',
            'description': 'Market price lookups should use utility_manager.get_market_price()'
        },
        {
            'name': 'hardcoded_funding_rate',
            'pattern': r'funding_rate.*=.*0\.0+1',
            'description': 'Hardcoded funding rates should use utility_manager.get_funding_rate()'
        },
        {
            'name': 'hardcoded_conversion_rate',
            'pattern': r'(rate|price).*=.*[0-9]+\.[0-9]+.*#.*fallback',
            'description': 'Hardcoded conversion rates should use utility_manager methods'
        }
    ]
    
    for line_num, line in enumerate(lines, 1):
        for pattern_info in patterns:
            if re.search(pattern_info['pattern'], line, re.IGNORECASE):
                # Skip if it's already using utility_manager
                if 'utility_manager' in line.lower():
                    continue
                    
                # Skip if it's in a comment
                if line.strip().startswith('#'):
                    continue
                    
                # Skip if it's in a test file
                if 'test_' in file_path:
                    continue
                
                # Skip if it's in a fallback/else block (acceptable pattern)
                if ('else:' in line or 'fallback' in line.lower() or 'if not' in line.lower() or 
                    'not available' in line.lower() or 'when utility manager' in line.lower()):
                    continue
                
                # Skip if it's a simple fallback value assignment
                if re.match(r'^\s*\w+\s*=\s*[0-9.]+$', line.strip()):
                    continue
                
                # Skip if it's in a mathematical calculation context (not price conversion)
                if ('liquidation_price' in line or 'price_move_pct' in line or 'entry_price' in line or
                    'price_change_pnl' in line or 'net_delta' in line or 'delta_pnl' in line):
                    continue
                
                # Skip if it's in a fallback context (check previous lines for else/if not)
                is_fallback = False
                for i in range(max(0, line_num - 5), line_num):
                    if i < len(lines):
                        prev_line = lines[i].strip()
                        if ('else:' in prev_line or 'if not' in prev_line or 
                            'fallback' in prev_line.lower() or 'not available' in prev_line.lower()):
                            is_fallback = True
                            break
                
                if is_fallback:
                    continue
                    
                violations.append({
                    'line': line_num,
                    'content': line.strip(),
                    'pattern': pattern_info['name'],
                    'description': pattern_info['description']
                })
    
    return violations

def check_utility_manager_usage(file_path: str) -> Dict:
    """Check if component properly uses utility manager."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"error": f"Could not read file: {e}"}
    
    # Check if utility_manager is imported or used
    has_utility_manager_import = 'utility_manager' in content.lower()
    has_utility_manager_usage = 'self.utility_manager' in content
    
    # Check if component receives utility_manager in __init__
    has_utility_manager_init = 'utility_manager' in content and '__init__' in content
    
    return {
        'has_import': has_utility_manager_import,
        'has_usage': has_utility_manager_usage,
        'has_init': has_utility_manager_init,
        'needs_utility_manager': any(keyword in content.lower() for keyword in [
            'price', 'rate', 'conversion', 'oracle', 'liquidity', 'funding'
        ])
    }

def generate_compliance_report(component_files: List[str]) -> Dict:
    """Generate utility manager compliance report."""
    report = {
        'total_files': len(component_files),
        'compliant_files': 0,
        'non_compliant_files': 0,
        'violations': [],
        'files_analysis': {}
    }
    
    for file_path in component_files:
        file_name = os.path.basename(file_path)
        
        # Skip utility_manager.py itself
        if 'utility_manager' in file_name:
            continue
            
        # Scan for inline calculations
        violations = scan_for_inline_calculations(file_path)
        
        # Check utility manager usage
        usage_check = check_utility_manager_usage(file_path)
        
        file_analysis = {
            'violations': violations,
            'usage_check': usage_check,
            'is_compliant': len(violations) == 0 and (
                not usage_check['needs_utility_manager'] or 
                (usage_check['has_usage'] and usage_check['has_init'])
            )
        }
        
        report['files_analysis'][file_name] = file_analysis
        
        if file_analysis['is_compliant']:
            report['compliant_files'] += 1
        else:
            report['non_compliant_files'] += 1
            report['violations'].extend([
                {
                    'file': file_name,
                    'violation': violation
                } for violation in violations
            ])
    
    return report

def print_compliance_report(report: Dict) -> bool:
    """Print utility manager compliance report."""
    print("🔍 Utility Manager Compliance Quality Gate")
    print("=" * 50)
    
    print(f"📊 Summary:")
    print(f"   Total files analyzed: {report['total_files']}")
    print(f"   Compliant files: {report['compliant_files']}")
    print(f"   Non-compliant files: {report['non_compliant_files']}")
    print(f"   Total violations: {len(report['violations'])}")
    
    if report['violations']:
        print(f"\n❌ Violations Found:")
        for violation_info in report['violations']:
            file_name = violation_info['file']
            violation = violation_info['violation']
            
            if 'error' in violation:
                print(f"   {file_name}: {violation['error']}")
            else:
                print(f"   {file_name}:{violation['line']} - {violation['pattern']}")
                print(f"      {violation['content']}")
                print(f"      → {violation['description']}")
        
        print(f"\n🔧 Recommended Actions:")
        print(f"   1. Replace inline calculations with utility_manager method calls")
        print(f"   2. Ensure all components receive utility_manager in __init__")
        print(f"   3. Use utility_manager for all price conversions and lookups")
        print(f"   4. Remove hardcoded values and use config-driven approach")
        
        return False
    else:
        print(f"\n✅ All components are compliant with utility manager usage!")
        return True

def main():
    """Main function to run utility manager compliance quality gate."""
    print("🚀 Starting Utility Manager Compliance Quality Gate...")
    
    # Find component files
    component_files = find_component_files()
    
    if not component_files:
        print("❌ No component files found")
        return 1
    
    # Generate compliance report
    report = generate_compliance_report(component_files)
    
    # Print report
    success = print_compliance_report(report)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())


