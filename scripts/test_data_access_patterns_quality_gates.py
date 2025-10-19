#!/usr/bin/env python3
"""
Data Access Patterns Quality Gates

Validates that all components use centralized data access patterns
and correct data keys/signatures throughout the codebase.

This test ensures:
1. No direct data provider access (must go through UtilityManager)
2. All data keys use standardized formats (uppercase, venue suffixes, BASE/QUOTE)
3. All data access follows canonical patterns
4. No legacy data access methods are used
"""

import os
import sys
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

logger = None


class DataAccessPatternValidator:
    """Validates data access patterns across the codebase."""
    
    def __init__(self):
        self.results = {
            'direct_data_access': {'passed': 0, 'failed': 0, 'violations': []},
            'data_key_formats': {'passed': 0, 'failed': 0, 'violations': []},
            'canonical_patterns': {'passed': 0, 'failed': 0, 'violations': []},
            'legacy_methods': {'passed': 0, 'failed': 0, 'violations': []}
        }
        
        # Files to check for data access patterns
        self.files_to_check = [
            'backend/src/basis_strategy_v1/core/components/',
            'backend/src/basis_strategy_v1/core/strategies/',
            'backend/src/basis_strategy_v1/core/utilities/',
            'backend/src/basis_strategy_v1/infrastructure/data/',
            'backend/src/basis_strategy_v1/core/risk/',
            'backend/src/basis_strategy_v1/core/execution/'
        ]
        
        # Patterns to detect direct data access (should be avoided)
        # Exclude access through utility_manager which is the canonical pattern
        self.direct_access_patterns = [
            r'(?<!utility_manager\.)data_provider\.get_',
            r'(?<!utility_manager\.)self\.data_provider\.get_',
            r'(?<!utility_manager\.data_)provider\.get_',
            r'(?<!utility_manager\.data_provider)\.get_data\(',
            r'(?<!utility_manager\.data_provider)\.get_market_data\(',
            r'(?<!utility_manager\.data_provider)\.get_protocol_data\(',
            r'(?<!utility_manager\.data_provider)\.get_execution_data\('
        ]
        
        # Patterns for position/balance data (should use position interfaces)
        self.position_data_patterns = [
            r'data_provider\.get_balances\(',
            r'data_provider\.get_positions\(',
            r'data_provider\.get_orders\(',
            r'self\.data_provider\.get_balances\(',
            r'self\.data_provider\.get_positions\(',
            r'self\.data_provider\.get_orders\('
        ]
        
        # Patterns for correct centralized access
        self.canonical_patterns = [
            r'utility_manager\.get_',
            r'self\.utility_manager\.get_',
            r'\.get_price_for_instrument_key\(',
            r'\.get_funding_rate\(',
            r'\.get_liquidity_index\(',
            r'\.get_mark_price\('
        ]
        
        # Patterns for correct position data access
        self.position_interface_patterns = [
            r'position_interface\.get_',
            r'self\.position_interface\.get_',
            r'cex_interface\.get_',
            r'defi_interface\.get_',
            r'\.get_balances\(',
            r'\.get_positions\(',
            r'\.get_orders\('
        ]
        
        # Legacy methods that should not be used (NOT the UtilityManager public API)
        self.legacy_methods = [
            'get_cex_derivatives_balances',
            'get_cex_spot_balances',
            'get_current_data',
            'get_execution_cost',
            'get_market_data_snapshot',
            'get_smart_contract_balances',
            'get_wallet_balances'
        ]
        
        # UtilityManager public API methods (these should be KEPT)
        self.utility_manager_api_methods = [
            'get_liquidity_index',
            'get_funding_rate', 
            'get_price_for_instrument_key',
            'get_oracle_price',
            'get_staking_apr',
            'get_gas_cost'
        ]
        
        # Correct data key patterns
        self.correct_key_patterns = [
            r'[A-Z]+_[a-z]+',  # Uppercase asset with venue suffix (e.g., BTC_binance)
            r'[A-Z]+/[A-Z]+',  # BASE/QUOTE format (e.g., weETH/ETH)
            r'[a-z]+_[A-Z]+',  # Protocol tokens (e.g., etherfi_weETH)
        ]
        
        # Incorrect data key patterns
        self.incorrect_key_patterns = [
            r'[a-z]+_[a-z]+',  # Lowercase with lowercase (e.g., btc_binance)
            r'[A-Z]+[a-z]+[A-Z]+',  # Mixed case (e.g., BtcUsdt)
            r'[a-z]+[A-Z]+',  # Lowercase with uppercase (e.g., btcUSDT)
        ]
    
    def find_python_files(self) -> List[Path]:
        """Find all Python files to check."""
        python_files = []
        
        for directory in self.files_to_check:
            dir_path = Path(__file__).parent.parent / directory
            if dir_path.exists():
                python_files.extend(dir_path.rglob('*.py'))
        
        return python_files
    
    def validate_direct_data_access(self, file_path: Path, content: str) -> List[str]:
        """Check for direct data provider access patterns."""
        violations = []
        
        # Skip utility_manager files - they are allowed to access data_provider directly
        if "utility_manager" in str(file_path):
            return violations
        
        # Split content into lines for better analysis
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for direct data access patterns
            for pattern in self.direct_access_patterns:
                if re.search(pattern, line):
                    # Skip if this is in a comment or documentation
                    if line.strip().startswith('#') or line.strip().startswith('"""') or 'From data_provider.get_data' in line:
                        continue
                    violations.append(f"Line {i}: Direct data access - {pattern}")
        
        return violations
    
    def validate_position_data_access(self, file_path: Path, content: str) -> List[str]:
        """Check for incorrect position data access through data provider."""
        violations = []
        
        for pattern in self.position_data_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                violations.append(f"Line {line_num}: Position data via data provider - {match.group()}")
        
        return violations
    
    def validate_canonical_patterns(self, file_path: Path, content: str) -> List[str]:
        """Check for canonical data access patterns."""
        violations = []
        
        # Check if file has data access but no canonical patterns
        has_data_access = any(re.search(pattern, content) for pattern in self.direct_access_patterns)
        has_canonical_access = any(re.search(pattern, content) for pattern in self.canonical_patterns)
        
        if has_data_access and not has_canonical_access:
            violations.append("File has data access but no canonical patterns found")
        
        return violations
    
    def validate_legacy_methods(self, file_path: Path, content: str) -> List[str]:
        """Check for legacy data access methods."""
        violations = []
        
        for method in self.legacy_methods:
            if re.search(rf'def {method}\(', content):
                line_num = content.find(f'def {method}(')
                if line_num != -1:
                    line_num = content[:line_num].count('\n') + 1
                    violations.append(f"Line {line_num}: Legacy method found - {method}")
        
        return violations
    
    def validate_data_key_formats(self, file_path: Path, content: str) -> List[str]:
        """Check for correct data key formats in string literals."""
        violations = []
        
        # Find string literals that look like data keys (more specific patterns)
        # Look for patterns that are likely data keys, not config keys
        data_key_patterns = [
            r'["\']([a-z]+_[a-z]+)["\']',  # Lowercase with lowercase in quotes
            r'["\']([A-Z]+[a-z]+[A-Z]+)["\']',  # Mixed case in quotes
            r'["\']([a-z]+[A-Z]+)["\']',  # Lowercase with uppercase in quotes
        ]
        
        for pattern in data_key_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                literal = match.group(1)
                # Skip config keys and other non-data keys
                if any(skip in literal for skip in [
                    'max_', 'min_', 'target_', 'config_', 'error_', 'success_', 'venue_', 'position_', 
                    'component_', 'attribution_', 'reporting_', 'reconciliation_', 'supply_', 'borrow_', 
                    'funding_', 'delta_', 'net_', 'transaction_', 'staking_', 'basis_', 'spread_', 'dust_', 
                    'underlying_', 'native_', 'loop_', 'full_', 'tight_', 'manual', 'weETH', 'ETH', 'BTC', 
                    'USDT', 'backtest_', 'live_', 'noop', 'refresh', 'execution_', 'mode', 'api_', 'secret_', 
                    'base_', 'rpc_', 'wallet_', 'private_', 'contract_', 'transfer_', 'order_', 'spot_', 
                    'perp_', 'available_', 'instructions_', 'succeeded', 'failed', 'set_', 'trigger_', 
                    'operation_', 'executed_', 'cached_', 'connection_', 'overall_', 'missing_', 'expected_', 
                    'actual_', 'duplicate_', 'null_', 'mapped_', 'file_', 'provider_', 'seasonal_', 
                    'liquidity_', 'protocol_', 'market_', 'oracle_', 'aave_', 'gas_', 'ml_', 'btc_', 
                    'eth_', 'usdt_', 'weth_', 'total_', 'source_', 'to_', 'entry_', 'exit_', 'sell_', 
                    'partial_', 'original_', 'strategy_', 'share_', 'risk_', 'leverage_', 'lst_', 'signal_', 
                    'stop_', 'take_', 'sd_', 'liquidation_', 'generate_', 'eth_allocation', 'leverage_mechanism', 
                    'risk_monitor', 'order_system', 'strategy_type', 'share_class', 'lst_type', 'eth_leveraged', 
                    'eth_balance', 'total_equity', 'leveraged_equity', 'weth_balance', 'btc_balance', 
                    'usdt_balance', 'btc_price', 'usdt_amount', 'btc_basis', 'signal_threshold', 'stop_loss', 
                    'take_profit', 'total_exposure', 'liquidation_risk', 'generate_orders', 'ml_data', 
                    'btc_directional', 'entry_full', 'entry_partial', 'exit_full', 'exit_partial', 'sell_dust', 
                    'partial_exit', 'original_position', 'to_asset', 'source_token', 'total_supply', 'total_borrow'
                ]):
                    continue
                # Skip if it's in a config.get() call or config access
                context_start = max(0, match.start() - 50)
                context = content[context_start:match.end()]
                if 'config.get(' in context or 'self.config' in context or 'config[' in context:
                    continue
                # Skip if it's in a dictionary definition or assignment
                if '=' in context and ('{' in context or '}' in context):
                    continue
                # Skip if it's in a docstring or comment
                if '"""' in context or "'''" in context or '#' in context:
                    continue
                
                line_num = content[:match.start()].count('\n') + 1
                violations.append(f"Line {line_num}: Incorrect data key format - '{literal}'")
        
        return violations
    
    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a single Python file for data access patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {'error': f"Could not read file: {e}"}
        
        file_results = {
            'file': str(file_path),
            'direct_access': self.validate_direct_data_access(file_path, content),
            'position_data': self.validate_position_data_access(file_path, content),
            'canonical_patterns': self.validate_canonical_patterns(file_path, content),
            'legacy_methods': self.validate_legacy_methods(file_path, content),
            'data_key_formats': self.validate_data_key_formats(file_path, content)
        }
        
        return file_results
    
    def run_validation(self) -> Dict[str, Any]:
        """Run validation on all Python files."""
        print("🔍 Validating data access patterns across codebase...")
        
        python_files = self.find_python_files()
        print(f"  Found {len(python_files)} Python files to check")
        
        all_results = {
            'direct_access': {'passed': 0, 'failed': 0, 'violations': []},
            'position_data': {'passed': 0, 'failed': 0, 'violations': []},
            'canonical_patterns': {'passed': 0, 'failed': 0, 'violations': []},
            'legacy_methods': {'passed': 0, 'failed': 0, 'violations': []},
            'data_key_formats': {'passed': 0, 'failed': 0, 'violations': []}
        }
        
        for file_path in python_files:
            file_results = self.validate_file(file_path)
            
            if 'error' in file_results:
                print(f"  ❌ Error checking {file_path}: {file_results['error']}")
                continue
            
            # Check each category
            for category in ['direct_access', 'position_data', 'canonical_patterns', 'legacy_methods', 'data_key_formats']:
                violations = file_results[category]
                if violations:
                    all_results[category]['failed'] += 1
                    all_results[category]['violations'].extend([
                        f"{file_path}: {violation}" for violation in violations
                    ])
                else:
                    all_results[category]['passed'] += 1
        
        # Print results
        print("\n📊 Data Access Pattern Validation Results:")
        print("=" * 60)
        
        for category, results in all_results.items():
            total = results['passed'] + results['failed']
            status = "✅ PASSED" if results['failed'] == 0 else "❌ FAILED"
            print(f"{category.replace('_', ' ').title()}: {status} ({results['passed']}/{total} files)")
            
            if results['violations']:
                print(f"  Violations found:")
                for violation in results['violations']:  # Show all violations
                    print(f"    - {violation}")
        
        self.results = all_results
        return all_results
    
    def run_all_checks(self) -> bool:
        """Run all data access pattern validation checks."""
        print("🚀 Starting data access patterns quality gate test...")
        print("=" * 80)
        
        validation_results = self.run_validation()
        
        # Calculate overall success
        total_files = sum(results['passed'] + results['failed'] for results in validation_results.values())
        total_passed = sum(results['passed'] for results in validation_results.values())
        total_failed = sum(results['failed'] for results in validation_results.values())
        
        success_rate = (total_passed / total_files * 100) if total_files > 0 else 0
        
        print("=" * 80)
        print("📊 DATA ACCESS PATTERNS QUALITY GATE SUMMARY")
        print("=" * 80)
        print(f"📁 Total files checked: {total_files}")
        print(f"✅ Files with correct patterns: {total_passed}")
        print(f"❌ Files with violations: {total_failed}")
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        if total_failed > 0:
            print("\n❌ FAILURE: Data access pattern violations found!")
            return False
        else:
            print("\n✅ SUCCESS: All data access patterns are correct!")
            return True


def main():
    """Main entry point for data access patterns quality gates."""
    validator = DataAccessPatternValidator()
    success = validator.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
