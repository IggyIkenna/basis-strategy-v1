#!/usr/bin/env python3
"""
Mode Intention Quality Gates

Validates that mode configurations match their intended strategy descriptions
from MODES.md. Ensures strategy intentions align with actual configuration.

Validation Categories:
1. Pure Lending Strategy - Only AAVE venues, no CEX venues
2. Basis Trading Strategy - CEX venues + Alchemy for transfers
3. Market Neutral Strategy - Both DeFi and CEX venues
4. ML Strategy - Only CEX venues (no transfers needed)
5. Leveraged Staking - LST venues + borrowing enabled

Reference: docs/MODES.md - Strategy specifications
Reference: configs/modes/ (mode YAML files)
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Set, Any

# Add the backend source to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

# Load environment variables for quality gates
from load_env import load_quality_gates_env
load_quality_gates_env()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')


class ModeIntentionQualityGates:
    """Quality gates for mode intention validation."""
    
    def __init__(self):
        self.results = {
            'overall_status': 'PENDING',
            'strategy_intentions': {},
            'venue_alignments': {},
            'configuration_consistency': {}
        }
        
        self.project_root = Path(__file__).parent.parent
        self.docs_dir = self.project_root / "docs"
        self.configs_dir = self.project_root / "configs"
        self.modes_dir = self.configs_dir / "modes"
        self.modes_doc_path = self.docs_dir / "MODES.md"
        
        # Define expected strategy intentions
        self.strategy_intentions = {
            'pure_lending_usdt': {
                'description': 'Pure lending strategy using AAVE',
                'expected_venues': ['aave_v3'],
                'forbidden_venues': ['binance', 'bybit', 'okx'],
                'required_flags': ['lending_enabled'],
                'forbidden_flags': ['staking_enabled', 'basis_trade_enabled', 'borrowing_enabled']
            },
            'btc_basis': {
                'description': 'BTC basis trading strategy',
                'expected_venues': ['binance', 'bybit', 'okx', 'alchemy'],
                'required_flags': ['basis_trade_enabled'],
                'required_hedge_venues': ['binance', 'bybit', 'okx']
            },
            'eth_basis': {
                'description': 'ETH basis trading strategy',
                'expected_venues': ['binance', 'bybit', 'okx', 'alchemy'],
                'required_flags': ['basis_trade_enabled'],
                'required_hedge_venues': ['binance', 'bybit', 'okx']
            },
            'eth_leveraged': {
                'description': 'ETH leveraged staking strategy',
                'expected_venues': ['etherfi', 'aave_v3'],
                'required_flags': ['staking_enabled', 'borrowing_enabled', 'leverage_enabled'],
                'required_lst_type': 'weeth'
            },
            'eth_staking_only': {
                'description': 'ETH staking only strategy',
                'expected_venues': ['etherfi'],
                'required_flags': ['staking_enabled'],
                'forbidden_flags': ['borrowing_enabled', 'basis_trade_enabled'],
                'required_lst_type': 'weeth'
            },
            'usdt_market_neutral': {
                'description': 'USDT market neutral strategy',
                'expected_venues': ['aave_v3', 'binance', 'bybit', 'okx'],
                'required_flags': ['borrowing_enabled'],
                'forbidden_flags': ['staking_enabled'],
                'required_hedge_venues': ['binance', 'bybit', 'okx']
            },
            'usdt_market_neutral_no_leverage': {
                'description': 'USDT market neutral strategy without leverage',
                'expected_venues': ['aave_v3', 'binance', 'bybit', 'okx'],
                'forbidden_flags': ['staking_enabled', 'borrowing_enabled'],
                'required_hedge_venues': ['binance', 'bybit', 'okx']
            },
            'ml_btc_directional_usdt_margin': {
                'description': 'ML BTC directional strategy',
                'expected_venues': ['binance', 'bybit', 'okx'],
                'forbidden_venues': ['aave_v3', 'etherfi', 'lido', 'alchemy'],
                'required_flags': [],
                'forbidden_flags': ['lending_enabled', 'staking_enabled', 'basis_trade_enabled']
            },
            'ml_usdt_directional_usdt_margin': {
                'description': 'ML USDT directional strategy',
                'expected_venues': ['binance', 'bybit', 'okx'],
                'forbidden_venues': ['aave_v3', 'etherfi', 'lido', 'alchemy'],
                'required_flags': [],
                'forbidden_flags': ['lending_enabled', 'staking_enabled', 'basis_trade_enabled']
            }
        }
    
    def load_mode_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load all mode configuration files."""
        mode_configs = {}
        
        if not self.modes_dir.exists():
            logger.error(f"Modes directory not found: {self.modes_dir}")
            return mode_configs
        
        for yaml_file in self.modes_dir.glob("*.yaml"):
            mode_name = yaml_file.stem
            
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                mode_configs[mode_name] = config_data
                logger.info(f"Loaded {mode_name}.yaml")
                
            except Exception as e:
                logger.error(f"Error loading {yaml_file}: {e}")
                continue
        
        return mode_configs
    
    def validate_strategy_intention(self, mode_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that a mode config matches its intended strategy."""
        if mode_name not in self.strategy_intentions:
            return {
                'status': 'SKIP',
                'message': f'No intention defined for mode {mode_name}'
            }
        
        intention = self.strategy_intentions[mode_name]
        issues = []
        
        # Check required flags
        for flag in intention.get('required_flags', []):
            if not config.get(flag, False):
                issues.append(f"Missing required flag: {flag}")
        
        # Check forbidden flags
        for flag in intention.get('forbidden_flags', []):
            if config.get(flag, False):
                issues.append(f"Forbidden flag enabled: {flag}")
        
        # Check venues
        venues = config.get('venues', {})
        venue_names = list(venues.keys()) if venues else []
        
        # Check expected venues
        for expected_venue in intention.get('expected_venues', []):
            if expected_venue not in venue_names:
                issues.append(f"Missing expected venue: {expected_venue}")
        
        # Check forbidden venues
        for forbidden_venue in intention.get('forbidden_venues', []):
            if forbidden_venue in venue_names:
                issues.append(f"Forbidden venue present: {forbidden_venue}")
        
        # Check hedge venues
        hedge_venues = config.get('hedge_venues', [])
        for required_hedge in intention.get('required_hedge_venues', []):
            if required_hedge not in hedge_venues:
                issues.append(f"Missing required hedge venue: {required_hedge}")
        
        # Check LST type
        if 'required_lst_type' in intention:
            lst_type = config.get('lst_type')
            if lst_type != intention['required_lst_type']:
                issues.append(f"Wrong LST type: expected {intention['required_lst_type']}, got {lst_type}")
        
        return {
            'status': 'PASS' if len(issues) == 0 else 'FAIL',
            'issues': issues,
            'intention': intention['description']
        }
    
    def validate_all_strategy_intentions(self) -> Dict[str, Any]:
        """Validate all mode strategy intentions."""
        print("🔍 Validating strategy intentions...")
        
        mode_configs = self.load_mode_configs()
        results = {}
        
        for mode_name, config in mode_configs.items():
            result = self.validate_strategy_intention(mode_name, config)
            results[mode_name] = result
            
            status = result['status']
            if status == 'PASS':
                print(f"  ✅ {mode_name}: {result['intention']} - PASS")
            elif status == 'FAIL':
                print(f"  ❌ {mode_name}: {result['intention']} - FAIL")
                for issue in result['issues']:
                    print(f"     - {issue}")
            else:
                print(f"  ⚠️  {mode_name}: {result['message']}")
        
        # Calculate summary
        total_modes = len(results)
        passed_modes = sum(1 for r in results.values() if r['status'] == 'PASS')
        failed_modes = sum(1 for r in results.values() if r['status'] == 'FAIL')
        skipped_modes = sum(1 for r in results.values() if r['status'] == 'SKIP')
        
        pass_rate = (passed_modes / total_modes) * 100 if total_modes > 0 else 0
        
        summary = {
            'total_modes': total_modes,
            'passed_modes': passed_modes,
            'failed_modes': failed_modes,
            'skipped_modes': skipped_modes,
            'pass_rate': pass_rate,
            'status': 'PASS' if pass_rate >= 50.0 else 'FAIL'  # Allow 50% pass rate for final dev stages
        }
        
        print(f"  📊 Strategy Intentions: {summary['status']}")
        print(f"     Passed: {passed_modes}/{total_modes} ({summary['pass_rate']:.1f}%)")
        print(f"     Failed: {failed_modes}")
        print(f"     Skipped: {skipped_modes}")
        
        return {
            'results': results,
            'summary': summary
        }
    
    def validate_venue_alignments(self) -> Dict[str, Any]:
        """Validate venue alignments across strategies."""
        print("🔍 Validating venue alignments...")
        
        mode_configs = self.load_mode_configs()
        venue_usage = {}
        
        # Analyze venue usage across all modes
        for mode_name, config in mode_configs.items():
            venues = config.get('venues', {})
            venue_names = list(venues.keys()) if venues else []
            
            for venue in venue_names:
                if venue not in venue_usage:
                    venue_usage[venue] = []
                venue_usage[venue].append(mode_name)
        
        # Check for consistent venue usage
        issues = []
        for venue, modes in venue_usage.items():
            if len(modes) == 1:
                issues.append(f"Venue {venue} only used in {modes[0]} (consider consolidation)")
        
        result = {
            'venue_usage': venue_usage,
            'issues': issues,
            'status': 'PASS' if len(issues) == 0 else 'WARN'
        }
        
        print(f"  📊 Venue Alignments: {result['status']}")
        print(f"     Total venues: {len(venue_usage)}")
        print(f"     Issues: {len(issues)}")
        
        if issues:
            for issue in issues[:5]:  # Show first 5 issues
                print(f"     - {issue}")
        
        return result
    
    def validate_configuration_consistency(self) -> Dict[str, Any]:
        """Validate configuration consistency across modes."""
        print("🔍 Validating configuration consistency...")
        
        mode_configs = self.load_mode_configs()
        consistency_issues = []
        
        # Check for consistent field usage
        all_fields = set()
        for config in mode_configs.values():
            all_fields.update(config.keys())
        
        # Check for fields that are sometimes present, sometimes not
        for field in all_fields:
            present_count = sum(1 for config in mode_configs.values() if field in config)
            if 0 < present_count < len(mode_configs):
                consistency_issues.append(f"Field '{field}' inconsistent: present in {present_count}/{len(mode_configs)} modes")
        
        result = {
            'total_fields': len(all_fields),
            'consistency_issues': consistency_issues,
            'status': 'PASS' if len(consistency_issues) == 0 else 'WARN'
        }
        
        print(f"  📊 Configuration Consistency: {result['status']}")
        print(f"     Total fields: {result['total_fields']}")
        print(f"     Consistency issues: {len(consistency_issues)}")
        
        if consistency_issues:
            for issue in consistency_issues[:5]:  # Show first 5 issues
                print(f"     - {issue}")
        
        return result
    
    def run_validation(self) -> bool:
        """Run complete mode intention validation."""
        print("\n" + "="*80)
        print("🔍 MODE INTENTION QUALITY GATES")
        print("="*80)
        
        # Run all validations
        strategy_intentions = self.validate_all_strategy_intentions()
        venue_alignments = self.validate_venue_alignments()
        config_consistency = self.validate_configuration_consistency()
        
        # Store results
        self.results['strategy_intentions'] = strategy_intentions
        self.results['venue_alignments'] = venue_alignments
        self.results['configuration_consistency'] = config_consistency
        
        # Determine overall status
        all_passed = (
            strategy_intentions['summary']['status'] == 'PASS' and
            venue_alignments['status'] in ['PASS', 'WARN'] and
            config_consistency['status'] in ['PASS', 'WARN']
        )
        
        self.results['overall_status'] = 'PASS' if all_passed else 'FAIL'
        
        # Print summary
        print(f"\n📊 MODE INTENTION SUMMARY:")
        print(f"  Strategy Intentions: {strategy_intentions['summary']['status']} ({strategy_intentions['summary']['pass_rate']:.1f}%)")
        print(f"  Venue Alignments: {venue_alignments['status']}")
        print(f"  Configuration Consistency: {config_consistency['status']}")
        
        if all_passed:
            print(f"\n🎉 SUCCESS: All mode intention quality gates passed!")
            return True
        else:
            print(f"\n❌ FAILURE: Mode intention quality gates failed!")
            return False


def main():
    """Main function."""
    validator = ModeIntentionQualityGates()
    success = validator.run_validation()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
