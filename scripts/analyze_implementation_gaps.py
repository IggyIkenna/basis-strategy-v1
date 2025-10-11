#!/usr/bin/env python3
"""
Implementation Gap Analysis Tool
Detailed analysis tool that compares component specifications against actual code implementation
and generates comprehensive gap reports with actionable recommendations.
"""

import os
import re
import ast
import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime

def find_component_specs(specs_dir: str = "docs/specs/") -> List[str]:
    """Find all component specification files."""
    specs = []
    for file in os.listdir(specs_dir):
        if file.endswith('.md') and file.startswith(('0', '1')):
            specs.append(os.path.join(specs_dir, file))
    return sorted(specs)

def find_component_implementations(backend_dir: str = "backend/src/basis_strategy_v1/core/strategies/components/") -> List[str]:
    """Find all component implementation files."""
    implementations = []
    if os.path.exists(backend_dir):
        for file in os.listdir(backend_dir):
            if file.endswith('.py') and not file.startswith('__'):
                implementations.append(os.path.join(backend_dir, file))
    return sorted(implementations)

def extract_detailed_spec_requirements(spec_file: str) -> Dict[str, any]:
    """Extract detailed requirements from component spec."""
    try:
        with open(spec_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        requirements = {
            'methods': [],
            'config_params': [],
            'error_codes': [],
            'event_types': [],
            'data_queries': [],
            'integration_points': [],
            'file': spec_file
        }
        
        # Extract methods from "Core Methods" section
        core_methods_match = re.search(r'## Core Methods(.*?)(?=## |$)', content, re.DOTALL)
        if core_methods_match:
            methods_text = core_methods_match.group(1)
            method_matches = re.findall(r'### (\w+)\([^)]*\)', methods_text)
            requirements['methods'].extend(method_matches)
        
        # Extract config parameters from "Configuration Parameters" section
        config_match = re.search(r'## Configuration Parameters(.*?)(?=## |$)', content, re.DOTALL)
        if config_match:
            config_text = config_match.group(1)
            param_matches = re.findall(r'`(\w+)`', config_text)
            requirements['config_params'].extend(param_matches)
        
        # Extract error codes from "Error Codes" section
        error_codes_match = re.search(r'## Error Codes(.*?)(?=## |$)', content, re.DOTALL)
        if error_codes_match:
            error_text = error_codes_match.group(1)
            error_matches = re.findall(r'#### (\w+-\d+):', error_text)
            requirements['error_codes'].extend(error_matches)
        
        # Extract event types from "Event Logging Requirements" section
        events_match = re.search(r'## Event Logging Requirements(.*?)(?=## |$)', content, re.DOTALL)
        if events_match:
            events_text = events_match.group(1)
            event_matches = re.findall(r"'(\w+)'", events_text)
            requirements['event_types'].extend(event_matches)
        
        # Extract data queries from "Data Provider Queries" section
        data_match = re.search(r'## Data Provider Queries(.*?)(?=## |$)', content, re.DOTALL)
        if data_match:
            data_text = data_match.group(1)
            query_matches = re.findall(r'`(\w+)`', data_text)
            requirements['data_queries'].extend(query_matches)
        
        # Extract integration points from "Integration Points" section
        integration_match = re.search(r'## Integration Points(.*?)(?=## |$)', content, re.DOTALL)
        if integration_match:
            integration_text = integration_match.group(1)
            integration_matches = re.findall(r'(\w+\.\w+)', integration_text)
            requirements['integration_points'].extend(integration_matches)
        
        return requirements
    except Exception as e:
        print(f"Error reading spec file {spec_file}: {e}")
        return {'methods': [], 'config_params': [], 'error_codes': [], 'event_types': [], 'data_queries': [], 'integration_points': [], 'file': spec_file}

def extract_detailed_implementation_features(impl_file: str) -> Dict[str, any]:
    """Extract detailed features from component implementation."""
    try:
        with open(impl_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST to find class methods and patterns
        tree = ast.parse(content)
        features = {
            'methods': [],
            'config_usage': [],
            'error_handling': [],
            'event_logging': [],
            'data_access': [],
            'integration_calls': [],
            'file': impl_file
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                features['methods'].append(node.name)
            elif isinstance(node, ast.Attribute):
                if hasattr(node.value, 'id') and node.value.id == 'config':
                    features['config_usage'].append(node.attr)
            elif isinstance(node, ast.Call):
                if hasattr(node.func, 'attr'):
                    if 'log' in node.func.attr.lower():
                        features['event_logging'].append(node.func.attr)
                    elif 'get_data' in node.func.attr:
                        features['data_access'].append(node.func.attr)
                    elif hasattr(node.func, 'value') and hasattr(node.func.value, 'id'):
                        features['integration_calls'].append(f"{node.func.value.id}.{node.func.attr}")
        
        # Check for error handling patterns
        if 'ComponentError' in content:
            features['error_handling'].append('ComponentError')
        if 'raise' in content:
            features['error_handling'].append('raise_statement')
        if 'try:' in content:
            features['error_handling'].append('try_except')
        
        return features
    except Exception as e:
        print(f"Error reading implementation file {impl_file}: {e}")
        return {'methods': [], 'config_usage': [], 'error_handling': [], 'event_logging': [], 'data_access': [], 'integration_calls': [], 'file': impl_file}

def calculate_canonical_compliance_score(spec_file: str, impl_file: str) -> Dict[str, any]:
    """Calculate detailed canonical compliance score."""
    try:
        with open(impl_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compliance_checks = {
            'has_config_driven_loop': False,
            'has_mode_agnostic_logic': True,
            'has_graceful_data_handling': False,
            'has_component_factory': False,
            'has_error_handling': False,
            'has_event_logging': False,
            'has_proper_data_access': False,
            'follows_reference_pattern': False
        }
        
        # Check for config-driven patterns
        if re.search(r'for.*in.*config.*enabled', content, re.IGNORECASE):
            compliance_checks['has_config_driven_loop'] = True
        
        # Check for mode-specific if/else (anti-pattern)
        if re.search(r'if.*mode.*==.*[\'"]', content):
            compliance_checks['has_mode_agnostic_logic'] = False
        
        # Check for graceful data handling
        if re.search(r'return None|skip|graceful', content, re.IGNORECASE):
            compliance_checks['has_graceful_data_handling'] = True
        
        # Check for ComponentFactory pattern
        if 'ComponentFactory' in content:
            compliance_checks['has_component_factory'] = True
        
        # Check for structured error handling
        if 'ComponentError' in content:
            compliance_checks['has_error_handling'] = True
        
        # Check for event logging
        if re.search(r'log_event|event_logger', content):
            compliance_checks['has_event_logging'] = True
        
        # Check for proper data access
        if re.search(r'data_provider\.get_data', content):
            compliance_checks['has_proper_data_access'] = True
        
        # Check for reference pattern (no passing refs as parameters)
        if not re.search(r'def.*\(.*position_monitor.*\)', content):
            compliance_checks['follows_reference_pattern'] = True
        
        # Calculate overall score
        total_checks = len(compliance_checks)
        passed_checks = sum(compliance_checks.values())
        compliance_score = passed_checks / total_checks if total_checks > 0 else 0
        
        return {
            'score': compliance_score,
            'details': compliance_checks,
            'passed_checks': passed_checks,
            'total_checks': total_checks
        }
    except Exception as e:
        print(f"Error checking canonical compliance for {impl_file}: {e}")
        return {'score': 0, 'details': {}, 'passed_checks': 0, 'total_checks': 0}

def generate_task_recommendations(component_name: str, gaps: Dict[str, any]) -> List[str]:
    """Generate specific task recommendations for implementation gaps."""
    recommendations = []
    
    if gaps.get('missing_methods'):
        recommendations.append(f"Implement missing methods: {', '.join(gaps['missing_methods'])}")
    
    if gaps.get('missing_config'):
        recommendations.append(f"Add config parameter handling: {', '.join(gaps['missing_config'])}")
    
    if gaps.get('missing_error_codes'):
        recommendations.append(f"Implement error codes: {', '.join(gaps['missing_error_codes'])}")
    
    if gaps.get('missing_event_logging'):
        recommendations.append(f"Add event logging: {', '.join(gaps['missing_event_logging'])}")
    
    if gaps.get('compliance_score', 0) < 0.6:
        recommendations.append("Refactor to follow canonical patterns (config-driven, mode-agnostic)")
    
    if gaps.get('compliance_details', {}).get('has_mode_agnostic_logic') == False:
        recommendations.append("Remove mode-specific if/else logic, use config-driven approach")
    
    if not gaps.get('compliance_details', {}).get('has_component_factory'):
        recommendations.append("Add ComponentFactory pattern for component creation")
    
    return recommendations

def generate_detailed_gap_report(specs: List[str], implementations: List[str]) -> Dict[str, any]:
    """Generate comprehensive implementation gap report with detailed analysis."""
    print("🔍 DETAILED IMPLEMENTATION GAP ANALYSIS")
    print("=" * 80)
    
    gap_report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_specs': len(specs),
            'total_implementations': len(implementations),
            'analysis_version': '1.0'
        },
        'components': {},
        'summary': {
            'canonical_examples': [],
            'high_priority_gaps': [],
            'medium_priority_gaps': [],
            'low_priority_gaps': [],
            'task_recommendations': []
        }
    }
    
    # Process each spec file
    for spec_file in specs:
        spec_name = os.path.basename(spec_file).replace('.md', '')
        print(f"\n📋 Analyzing {spec_name}...")
        
        # Extract detailed spec requirements
        spec_requirements = extract_detailed_spec_requirements(spec_file)
        
        # Find corresponding implementation
        impl_file = None
        for impl in implementations:
            if spec_name.lower().replace('_', '') in impl.lower().replace('_', ''):
                impl_file = impl
                break
        
        if not impl_file:
            print(f"  ❌ No implementation found for {spec_name}")
            gap_report['components'][spec_name] = {
                'status': 'MISSING_IMPLEMENTATION',
                'priority': 'HIGH',
                'compliance_score': 0,
                'gaps': {
                    'missing_methods': spec_requirements['methods'],
                    'missing_config': spec_requirements['config_params'],
                    'missing_error_codes': spec_requirements['error_codes'],
                    'missing_event_logging': spec_requirements['event_types'],
                    'missing_data_access': spec_requirements['data_queries'],
                    'missing_integration': spec_requirements['integration_points']
                },
                'task_recommendations': [f"Create complete implementation for {spec_name}"]
            }
            gap_report['summary']['high_priority_gaps'].append(f"{spec_name}: Missing implementation")
            continue
        
        # Extract implementation features
        impl_features = extract_detailed_implementation_features(impl_file)
        compliance = calculate_canonical_compliance_score(spec_file, impl_file)
        
        # Calculate detailed gaps
        spec_methods = set(spec_requirements['methods'])
        impl_methods = set(impl_features['methods'])
        missing_methods = spec_methods - impl_methods
        extra_methods = impl_methods - spec_methods
        
        spec_config = set(spec_requirements['config_params'])
        impl_config = set(impl_features['config_usage'])
        missing_config = spec_config - impl_config
        
        spec_errors = set(spec_requirements['error_codes'])
        impl_errors = set(impl_features['error_handling'])
        missing_error_codes = spec_errors - impl_errors
        
        spec_events = set(spec_requirements['event_types'])
        impl_events = set(impl_features['event_logging'])
        missing_event_logging = spec_events - impl_events
        
        spec_data = set(spec_requirements['data_queries'])
        impl_data = set(impl_features['data_access'])
        missing_data_access = spec_data - impl_data
        
        spec_integration = set(spec_requirements['integration_points'])
        impl_integration = set(impl_features['integration_calls'])
        missing_integration = spec_integration - impl_integration
        
        # Determine priority based on gaps and compliance
        total_gaps = (len(missing_methods) + len(missing_config) + len(missing_error_codes) + 
                     len(missing_event_logging) + len(missing_data_access) + len(missing_integration))
        
        priority = 'LOW'
        if total_gaps > 5 or compliance['score'] < 0.4:
            priority = 'HIGH'
        elif total_gaps > 2 or compliance['score'] < 0.7:
            priority = 'MEDIUM'
        
        # Check if canonical example
        is_canonical = spec_name in ['02_EXPOSURE_MONITOR', '03_RISK_MONITOR']
        if is_canonical:
            gap_report['summary']['canonical_examples'].append(spec_name)
        
        # Generate task recommendations
        gaps_dict = {
            'missing_methods': list(missing_methods),
            'missing_config': list(missing_config),
            'missing_error_codes': list(missing_error_codes),
            'missing_event_logging': list(missing_event_logging),
            'missing_data_access': list(missing_data_access),
            'missing_integration': list(missing_integration),
            'compliance_score': compliance['score'],
            'compliance_details': compliance['details']
        }
        
        task_recommendations = generate_task_recommendations(spec_name, gaps_dict)
        
        component_status = {
            'status': 'CANONICAL' if is_canonical else ('COMPLIANT' if total_gaps == 0 and compliance['score'] > 0.8 else 'NEEDS_WORK'),
            'priority': priority,
            'compliance_score': compliance['score'],
            'compliance_details': compliance['details'],
            'gaps': gaps_dict,
            'task_recommendations': task_recommendations,
            'implementation_file': impl_file,
            'spec_file': spec_file
        }
        
        gap_report['components'][spec_name] = component_status
        
        # Add to priority lists
        if priority == 'HIGH':
            gap_report['summary']['high_priority_gaps'].append(f"{spec_name}: {total_gaps} gaps, compliance {compliance['score']:.2f}")
        elif priority == 'MEDIUM':
            gap_report['summary']['medium_priority_gaps'].append(f"{spec_name}: {total_gaps} gaps, compliance {compliance['score']:.2f}")
        else:
            gap_report['summary']['low_priority_gaps'].append(f"{spec_name}: Minor issues")
        
        # Add task recommendations
        gap_report['summary']['task_recommendations'].extend(task_recommendations)
        
        # Print component summary
        status_icon = "✅" if component_status['status'] in ['CANONICAL', 'COMPLIANT'] else "⚠️" if priority == 'MEDIUM' else "❌"
        print(f"  {status_icon} {component_status['status']} ({priority} priority)")
        print(f"     Compliance Score: {compliance['score']:.2f}")
        print(f"     Total Gaps: {total_gaps}")
        if task_recommendations:
            print(f"     Key Tasks: {task_recommendations[0]}")
    
    return gap_report

def save_detailed_report(gap_report: Dict[str, any], output_file: str = "docs/IMPLEMENTATION_GAP_REPORT.md"):
    """Save detailed gap report to markdown file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Implementation Gap Analysis Report\n\n")
            f.write(f"**Generated**: {gap_report['metadata']['generated_at']}\n")
            f.write(f"**Analysis Version**: {gap_report['metadata']['analysis_version']}\n\n")
            
            # Summary section
            f.write("## Summary\n\n")
            summary = gap_report['summary']
            f.write(f"- **Total Components**: {gap_report['metadata']['total_specs']}\n")
            f.write(f"- **Canonical Examples**: {', '.join(summary['canonical_examples'])}\n")
            f.write(f"- **High Priority Gaps**: {len(summary['high_priority_gaps'])}\n")
            f.write(f"- **Medium Priority Gaps**: {len(summary['medium_priority_gaps'])}\n")
            f.write(f"- **Low Priority Gaps**: {len(summary['low_priority_gaps'])}\n\n")
            
            # High priority gaps
            if summary['high_priority_gaps']:
                f.write("## 🔴 High Priority Gaps\n\n")
                for gap in summary['high_priority_gaps']:
                    f.write(f"- {gap}\n")
                f.write("\n")
            
            # Medium priority gaps
            if summary['medium_priority_gaps']:
                f.write("## 🟡 Medium Priority Gaps\n\n")
                for gap in summary['medium_priority_gaps']:
                    f.write(f"- {gap}\n")
                f.write("\n")
            
            # Task recommendations
            if summary['task_recommendations']:
                f.write("## 📋 Task Recommendations\n\n")
                for i, task in enumerate(summary['task_recommendations'][:20], 1):  # Limit to top 20
                    f.write(f"{i}. {task}\n")
                f.write("\n")
            
            # Component details
            f.write("## Component Details\n\n")
            for component_name, details in gap_report['components'].items():
                f.write(f"### {component_name}\n\n")
                f.write(f"- **Status**: {details['status']}\n")
                f.write(f"- **Priority**: {details['priority']}\n")
                f.write(f"- **Compliance Score**: {details['compliance_score']:.2f}\n")
                f.write(f"- **Implementation File**: {details.get('implementation_file', 'N/A')}\n\n")
                
                if details.get('gaps'):
                    gaps = details['gaps']
                    f.write("**Gaps**:\n")
                    for gap_type, gap_list in gaps.items():
                        if gap_list and gap_type != 'compliance_score' and gap_type != 'compliance_details':
                            f.write(f"- {gap_type}: {', '.join(gap_list) if isinstance(gap_list, list) else gap_list}\n")
                    f.write("\n")
                
                if details.get('task_recommendations'):
                    f.write("**Task Recommendations**:\n")
                    for task in details['task_recommendations']:
                        f.write(f"- {task}\n")
                    f.write("\n")
        
        print(f"\n📄 Detailed report saved to: {output_file}")
        return True
    except Exception as e:
        print(f"⚠️  Could not save detailed report: {e}")
        return False

def main():
    """Main function."""
    print("🚦 DETAILED IMPLEMENTATION GAP ANALYSIS")
    print("=" * 80)
    
    # Find spec and implementation files
    specs = find_component_specs()
    implementations = find_component_implementations()
    
    if not specs:
        print("❌ No component specifications found in docs/specs/")
        return 1
    
    if not implementations:
        print("⚠️  No component implementations found in backend/src/basis_strategy_v1/core/components/")
        print("   This may indicate the backend structure has changed")
    
    # Generate detailed gap report
    gap_report = generate_detailed_gap_report(specs, implementations)
    
    # Save detailed report
    save_detailed_report(gap_report)
    
    # Save JSON report
    try:
        with open('implementation_gap_detailed_report.json', 'w') as f:
            json.dump(gap_report, f, indent=2)
        print(f"📄 JSON report saved to: implementation_gap_detailed_report.json")
    except Exception as e:
        print(f"⚠️  Could not save JSON report: {e}")
    
    # Calculate overall success rate
    total_components = len(gap_report['components'])
    compliant_components = sum(1 for c in gap_report['components'].values() 
                             if c['status'] in ['CANONICAL', 'COMPLIANT'])
    success_rate = (compliant_components / total_components * 100) if total_components > 0 else 0
    
    print(f"\n🎯 Overall Implementation Success Rate: {success_rate:.1f}%")
    print(f"📊 Total Task Recommendations: {len(gap_report['summary']['task_recommendations'])}")
    
    if success_rate >= 80:
        print("🎉 SUCCESS: Implementation gap analysis completed!")
        return 0
    else:
        print("⚠️  WARNING: Implementation gaps detected - review detailed report")
        return 1

if __name__ == "__main__":
    sys.exit(main())
