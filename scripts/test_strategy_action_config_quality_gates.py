#!/usr/bin/env python3
"""
Strategy Action Config Compliance Quality Gate

Validates that each strategy implementation has methods for ALL actions 
defined in its corresponding mode configuration.

This quality gate ensures that:
1. Every action in component_config.strategy_manager.actions has a corresponding method
2. Strategy implementations match their configuration requirements
3. No missing action methods that would cause runtime failures

Reference: docs/COMPONENT_SPEC_TEMPLATE.md - Event Logging Requirements
Reference: docs/specs/5B_BASE_STRATEGY_MANAGER.md - Base Strategy Manager
"""

import os
import sys
import ast
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_mode_config(mode_name: str) -> Dict[str, Any]:
    """Load mode configuration from configs/modes/{mode_name}.yaml"""
    config_path = project_root / "configs" / "modes" / f"{mode_name}.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Mode config not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_strategy_actions_from_config(config: Dict) -> List[str]:
    """Extract strategy actions from component_config.strategy_manager.actions"""
    return config.get('component_config', {}).get('strategy_manager', {}).get('actions', [])

def get_strategy_implementation_methods(strategy_file: str) -> List[str]:
    """Parse strategy Python file and extract method names"""
    if not os.path.exists(strategy_file):
        return []
    
    with open(strategy_file, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError as e:
            print(f"⚠️  Syntax error in {strategy_file}: {e}")
            return []
    
    methods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Only get methods from strategy classes (not base classes)
            if any(base.id in ['BaseStrategyManager'] for base in node.bases if hasattr(base, 'id')):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)
    
    return methods

def validate_strategy_action_compliance(mode_name: str, strategy_file: str) -> Dict[str, Any]:
    """Validate that strategy has methods for all config actions"""
    try:
        config = load_mode_config(mode_name)
        required_actions = get_strategy_actions_from_config(config)
        implemented_methods = get_strategy_implementation_methods(strategy_file)
        
        missing_actions = [action for action in required_actions if action not in implemented_methods]
        
        return {
            'mode': mode_name,
            'strategy_file': strategy_file,
            'required_actions': required_actions,
            'implemented_methods': implemented_methods,
            'missing_actions': missing_actions,
            'compliant': len(missing_actions) == 0,
            'compliance_score': (len(required_actions) - len(missing_actions)) / len(required_actions) if required_actions else 1.0,
            'error': None
        }
    except Exception as e:
        return {
            'mode': mode_name,
            'strategy_file': strategy_file,
            'required_actions': [],
            'implemented_methods': [],
            'missing_actions': [],
            'compliant': False,
            'compliance_score': 0.0,
            'error': str(e)
        }

def main():
    """Main quality gate execution."""
    print("🔍 Strategy Action Config Compliance Quality Gate")
    print("=" * 60)
    
    # Strategy-to-Config Mapping
    STRATEGY_CONFIG_MAPPING = {
        'pure_lending_strategy.py': 'pure_lending.yaml',
        'btc_basis_strategy.py': 'btc_basis.yaml',
        'eth_basis_strategy.py': 'eth_basis.yaml',
        'eth_staking_only_strategy.py': 'eth_staking_only.yaml',
        'eth_leveraged_strategy.py': 'eth_leveraged.yaml',
        'usdt_market_neutral_no_leverage_strategy.py': 'usdt_market_neutral_no_leverage.yaml',
        'usdt_market_neutral_strategy.py': 'usdt_market_neutral.yaml',
        'ml_btc_directional_strategy.py': 'ml_btc_directional.yaml',
        'ml_usdt_directional_strategy.py': 'ml_usdt_directional.yaml',
    }
    
    strategies_dir = project_root / "backend" / "src" / "basis_strategy_v1" / "core" / "strategies"
    
    compliance_reports = []
    total_compliance_score = 0.0
    valid_strategies = 0
    
    print(f"📋 Validating {len(STRATEGY_CONFIG_MAPPING)} strategy implementations...")
    print()
    
    for strategy_file, config_file in STRATEGY_CONFIG_MAPPING.items():
        strategy_path = strategies_dir / strategy_file
        
        if not strategy_path.exists():
            print(f"⚠️  Strategy file not found: {strategy_file}")
            continue
        
        mode_name = config_file.replace('.yaml', '')
        report = validate_strategy_action_compliance(mode_name, str(strategy_path))
        compliance_reports.append(report)
        
        # Display results
        if report['error']:
            print(f"❌ {strategy_file} ({config_file})")
            print(f"   Error: {report['error']}")
        elif report['compliant']:
            print(f"✅ {strategy_file} ({config_file})")
            print(f"   Required actions: {report['required_actions']}")
            print(f"   Compliance: 100% ({len(report['required_actions'])}/{len(report['required_actions'])} actions implemented)")
            total_compliance_score += report['compliance_score']
            valid_strategies += 1
        else:
            print(f"❌ {strategy_file} ({config_file})")
            print(f"   Required actions: {report['required_actions']}")
            print(f"   Missing actions: {report['missing_actions']}")
            print(f"   Compliance: {report['compliance_score']:.0%} ({len(report['required_actions']) - len(report['missing_actions'])}/{len(report['required_actions'])} actions implemented)")
            total_compliance_score += report['compliance_score']
            valid_strategies += 1
        
        print()
    
    # Calculate overall compliance
    if valid_strategies > 0:
        overall_compliance = total_compliance_score / valid_strategies
    else:
        overall_compliance = 0.0
    
    print("📊 Summary")
    print("-" * 30)
    print(f"Total strategies validated: {len(compliance_reports)}")
    print(f"Valid strategies: {valid_strategies}")
    print(f"Overall compliance: {overall_compliance:.1%}")
    
    # Count compliant vs non-compliant
    compliant_count = sum(1 for report in compliance_reports if report['compliant'] and not report['error'])
    non_compliant_count = len(compliance_reports) - compliant_count
    
    print(f"Compliant strategies: {compliant_count}")
    print(f"Non-compliant strategies: {non_compliant_count}")
    
    # Detailed non-compliant report
    if non_compliant_count > 0:
        print()
        print("🔧 Action Required")
        print("-" * 20)
        for report in compliance_reports:
            if not report['compliant'] and not report['error']:
                print(f"• {report['strategy_file']}: Add methods for {report['missing_actions']}")
    
    # Quality gate result
    print()
    if overall_compliance >= 1.0:
        print("✅ Quality gate PASSED - All strategies have 100% action compliance")
        return 0
    else:
        print(f"❌ Quality gate FAILED - Overall compliance: {overall_compliance:.1%}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
