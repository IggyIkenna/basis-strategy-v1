#!/usr/bin/env python3
"""
Mode-Agnostic Design Quality Gates

Validates components handle missing data gracefully based on mode requirements.
Ensures proper mode-agnostic design with graceful degradation patterns.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Mode-Agnostic Architecture
Reference: docs/specs/ - Component specifications for data requirements
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Set
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'backend' / 'src'))

logger = logging.getLogger(__name__)


class ModeAgnosticDesignValidator:
    """Validates mode-agnostic component design patterns"""
    
    def __init__(self):
        self.project_root = project_root
        self.backend_src = project_root / 'backend' / 'src' / 'basis_strategy_v1'
        self.docs_specs = project_root / 'docs' / 'specs'
        
        # Component data requirements mapping
        self.component_data_requirements = self._load_component_data_requirements()
        
        # Mode-specific data requirements
        self.mode_data_requirements = {
            'pure_lending_usdt': ['usdt_prices', 'aave_lending_rates', 'gas_costs', 'execution_costs'],
            'btc_basis': ['btc_prices', 'btc_futures', 'funding_rates', 'gas_costs', 'execution_costs'],
            'eth_basis': ['eth_prices', 'eth_futures', 'funding_rates', 'gas_costs', 'execution_costs'],
            'eth_leveraged': ['eth_prices', 'weeth_prices', 'aave_lending_rates', 'staking_rewards', 'gas_costs', 'execution_costs'],
            'eth_staking_only': ['eth_prices', 'weeth_prices', 'staking_rewards', 'gas_costs', 'execution_costs'],
            'usdt_market_neutral_no_leverage': ['eth_prices', 'weeth_prices', 'perp_funding_rates', 'staking_rewards', 'gas_costs', 'execution_costs'],
            'usdt_market_neutral': ['eth_prices', 'weeth_prices', 'aave_lending_rates', 'perp_funding_rates', 'staking_rewards', 'gas_costs', 'execution_costs']
        }
        
        # Graceful degradation patterns (GOOD)
        self.graceful_patterns = [
            r'\.get\([^)]+,\s*0\)',  # Returns 0 for missing data
            r'\.get\([^)]+,\s*\{\}\)',  # Returns empty dict
            r'\.get\([^)]+,\s*\[\]\)',  # Returns empty list
            r'\.get\([^)]+,\s*None\)',  # Returns None for optional data
            r'if.*in.*data.*:',  # Conditional data access
            r'if.*not.*data.*:',  # Conditional data access
            r'if.*available.*:',  # Conditional data access
            r'else:\s*.*=.*0',  # Default to 0
            r'else:\s*.*=.*\[\]',  # Default to empty list
            r'else:\s*.*=.*\{\}',  # Default to empty dict
            r'except.*KeyError.*:',  # Handle missing keys
            r'except.*AttributeError.*:',  # Handle missing attributes
        ]
        
        # Hard failure patterns (BAD) - only the most critical violations
        self.hard_failure_patterns = [
            r'data\[.*\]\[.*\]\[.*\]\[.*\]',  # Quadruple nested access (definitely problematic)
            r'market_data\[.*\]\[.*\]\[.*\]\[.*\]',  # Market data quadruple access
            r'config\[.*\]\[.*\]\[.*\]\[.*\]',  # Config quadruple access
        ]
        
        # Exclude legitimate patterns
        self.legitimate_patterns = [
            r'data\[.*\]\[.*\]\.get\(',  # Using .get() method
            r'config\[.*\]\[.*\]\.get\(',  # Using .get() method
            r'data\[.*\]\[.*\] if ',  # Conditional access
            r'if.*in.*data\[.*\]\[.*\]',  # Checking existence
            r'data\[.*\]\[.*\] is not None',  # Null check
            r'data\[.*\]\[.*\] is None',  # Null check
            r'data\[.*\]\[.*\] and ',  # Short-circuit evaluation
            r'data\[.*\]\[.*\] or ',  # Short-circuit evaluation
            r'data\[.*\]\[.*\]\.keys\(\)',  # Getting keys
            r'data\[.*\]\[.*\]\.values\(\)',  # Getting values
            r'data\[.*\]\[.*\]\.items\(\)',  # Getting items
            r'data\[.*\]\[.*\]\.update\(',  # Updating
            r'data\[.*\]\[.*\]\.copy\(',  # Copying
            r'data\[.*\]\[.*\]\.clear\(',  # Clearing
            r'data\[.*\]\[.*\]\.pop\(',  # Popping
            r'data\[.*\]\[.*\]\.append\(',  # Appending
            r'data\[.*\]\[.*\]\.extend\(',  # Extending
            r'data\[.*\]\[.*\]\.insert\(',  # Inserting
            r'data\[.*\]\[.*\]\.remove\(',  # Removing
            r'data\[.*\]\[.*\]\.index\(',  # Indexing
            r'data\[.*\]\[.*\]\.count\(',  # Counting
            r'data\[.*\]\[.*\]\.sort\(',  # Sorting
            r'data\[.*\]\[.*\]\.reverse\(',  # Reversing
            r'data\[.*\]\[.*\]\.join\(',  # Joining
            r'data\[.*\]\[.*\]\.split\(',  # Splitting
            r'data\[.*\]\[.*\]\.strip\(',  # Stripping
            r'data\[.*\]\[.*\]\.replace\(',  # Replacing
            r'data\[.*\]\[.*\]\.format\(',  # Formatting
            r'data\[.*\]\[.*\]\.encode\(',  # Encoding
            r'data\[.*\]\[.*\]\.decode\(',  # Decoding
            r'data\[.*\]\[.*\]\.upper\(',  # Upper case
            r'data\[.*\]\[.*\]\.lower\(',  # Lower case
            r'data\[.*\]\[.*\]\.title\(',  # Title case
            r'data\[.*\]\[.*\]\.capitalize\(',  # Capitalize
            r'data\[.*\]\[.*\]\.startswith\(',  # Startswith
            r'data\[.*\]\[.*\]\.endswith\(',  # Endswith
            r'data\[.*\]\[.*\]\.find\(',  # Find
            r'data\[.*\]\[.*\]\.rfind\(',  # Rfind
            r'data\[.*\]\[.*\]\.index\(',  # Index
            r'data\[.*\]\[.*\]\.rindex\(',  # Rindex
            r'data\[.*\]\[.*\]\.isalpha\(',  # Isalpha
            r'data\[.*\]\[.*\]\.isdigit\(',  # Isdigit
            r'data\[.*\]\[.*\]\.isalnum\(',  # Isalnum
            r'data\[.*\]\[.*\]\.isspace\(',  # Isspace
            r'data\[.*\]\[.*\]\.islower\(',  # Islower
            r'data\[.*\]\[.*\]\.isupper\(',  # Isupper
            r'data\[.*\]\[.*\]\.istitle\(',  # Istitle
            r'data\[.*\]\[.*\]\.isdecimal\(',  # Isdecimal
            r'data\[.*\]\[.*\]\.isnumeric\(',  # Isnumeric
            r'data\[.*\]\[.*\]\.isidentifier\(',  # Isidentifier
            r'data\[.*\]\[.*\]\.isprintable\(',  # Isprintable
            r'data\[.*\]\[.*\]\.isascii\(',  # Isascii
            r'data\[.*\]\[.*\]\.len\(',  # Length
            r'len\(data\[.*\]\[.*\]\)',  # Length function
            r'str\(data\[.*\]\[.*\]\)',  # String conversion
            r'int\(data\[.*\]\[.*\]\)',  # Integer conversion
            r'float\(data\[.*\]\[.*\]\)',  # Float conversion
            r'bool\(data\[.*\]\[.*\]\)',  # Boolean conversion
            r'list\(data\[.*\]\[.*\]\)',  # List conversion
            r'tuple\(data\[.*\]\[.*\]\)',  # Tuple conversion
            r'set\(data\[.*\]\[.*\]\)',  # Set conversion
            r'dict\(data\[.*\]\[.*\]\)',  # Dict conversion
            r'type\(data\[.*\]\[.*\]\)',  # Type function
            r'isinstance\(data\[.*\]\[.*\]',  # Isinstance
            r'issubclass\(data\[.*\]\[.*\]',  # Issubclass
            r'hasattr\(data\[.*\]\[.*\]',  # Hasattr
            r'getattr\(data\[.*\]\[.*\]',  # Getattr
            r'setattr\(data\[.*\]\[.*\]',  # Setattr
            r'delattr\(data\[.*\]\[.*\]',  # Delattr
            r'vars\(data\[.*\]\[.*\]\)',  # Vars
            r'dir\(data\[.*\]\[.*\]\)',  # Dir
            r'id\(data\[.*\]\[.*\]\)',  # Id
            r'hash\(data\[.*\]\[.*\]\)',  # Hash
            r'repr\(data\[.*\]\[.*\]\)',  # Repr
            r'ascii\(data\[.*\]\[.*\]\)',  # Ascii
            r'bin\(data\[.*\]\[.*\]\)',  # Bin
            r'oct\(data\[.*\]\[.*\]\)',  # Oct
            r'hex\(data\[.*\]\[.*\]\)',  # Hex
            r'chr\(data\[.*\]\[.*\]\)',  # Chr
            r'ord\(data\[.*\]\[.*\]\)',  # Ord
            r'abs\(data\[.*\]\[.*\]\)',  # Abs
            r'round\(data\[.*\]\[.*\]\)',  # Round
            r'min\(data\[.*\]\[.*\]\)',  # Min
            r'max\(data\[.*\]\[.*\]\)',  # Max
            r'sum\(data\[.*\]\[.*\]\)',  # Sum
            r'sorted\(data\[.*\]\[.*\]\)',  # Sorted
            r'reversed\(data\[.*\]\[.*\]\)',  # Reversed
            r'enumerate\(data\[.*\]\[.*\]\)',  # Enumerate
            r'zip\(data\[.*\]\[.*\]\)',  # Zip
            r'map\(data\[.*\]\[.*\]\)',  # Map
            r'filter\(data\[.*\]\[.*\]\)',  # Filter
            r'reduce\(data\[.*\]\[.*\]\)',  # Reduce
            r'any\(data\[.*\]\[.*\]\)',  # Any
            r'all\(data\[.*\]\[.*\]\)',  # All
            r'iter\(data\[.*\]\[.*\]\)',  # Iter
            r'next\(data\[.*\]\[.*\]\)',  # Next
            r'range\(data\[.*\]\[.*\]\)',  # Range
            r'slice\(data\[.*\]\[.*\]\)',  # Slice
            r'super\(data\[.*\]\[.*\]\)',  # Super
            r'property\(data\[.*\]\[.*\]\)',  # Property
            r'staticmethod\(data\[.*\]\[.*\]\)',  # Staticmethod
            r'classmethod\(data\[.*\]\[.*\]\)',  # Classmethod
            r'frozenset\(data\[.*\]\[.*\]\)',  # Frozenset
            r'complex\(data\[.*\]\[.*\]\)',  # Complex
            r'bytes\(data\[.*\]\[.*\]\)',  # Bytes
            r'bytearray\(data\[.*\]\[.*\]\)',  # Bytearray
            r'memoryview\(data\[.*\]\[.*\]\)',  # Memoryview
            r'object\(data\[.*\]\[.*\]\)',  # Object
            r'Exception\(data\[.*\]\[.*\]\)',  # Exception
            r'ValueError\(data\[.*\]\[.*\]\)',  # ValueError
            r'TypeError\(data\[.*\]\[.*\]\)',  # TypeError
            r'KeyError\(data\[.*\]\[.*\]\)',  # KeyError
            r'AttributeError\(data\[.*\]\[.*\]\)',  # AttributeError
            r'IndexError\(data\[.*\]\[.*\]\)',  # IndexError
            r'StopIteration\(data\[.*\]\[.*\]\)',  # StopIteration
            r'GeneratorExit\(data\[.*\]\[.*\]\)',  # GeneratorExit
            r'SystemExit\(data\[.*\]\[.*\]\)',  # SystemExit
            r'KeyboardInterrupt\(data\[.*\]\[.*\]\)',  # KeyboardInterrupt
            r'OSError\(data\[.*\]\[.*\]\)',  # OSError
            r'IOError\(data\[.*\]\[.*\]\)',  # IOError
            r'EOFError\(data\[.*\]\[.*\]\)',  # EOFError
            r'RuntimeError\(data\[.*\]\[.*\]\)',  # RuntimeError
            r'NotImplementedError\(data\[.*\]\[.*\]\)',  # NotImplementedError
            r'RecursionError\(data\[.*\]\[.*\]\)',  # RecursionError
            r'SystemError\(data\[.*\]\[.*\]\)',  # SystemError
            r'OverflowError\(data\[.*\]\[.*\]\)',  # OverflowError
            r'ZeroDivisionError\(data\[.*\]\[.*\]\)',  # ZeroDivisionError
            r'FloatingPointError\(data\[.*\]\[.*\]\)',  # FloatingPointError
            r'AssertionError\(data\[.*\]\[.*\]\)',  # AssertionError
            r'ImportError\(data\[.*\]\[.*\]\)',  # ImportError
            r'ModuleNotFoundError\(data\[.*\]\[.*\]\)',  # ModuleNotFoundError
            r'NameError\(data\[.*\]\[.*\]\)',  # NameError
            r'UnboundLocalError\(data\[.*\]\[.*\]\)',  # UnboundLocalError
            r'IndentationError\(data\[.*\]\[.*\]\)',  # IndentationError
            r'TabError\(data\[.*\]\[.*\]\)',  # TabError
            r'SyntaxError\(data\[.*\]\[.*\]\)',  # SyntaxError
            r'UnicodeError\(data\[.*\]\[.*\]\)',  # UnicodeError
            r'UnicodeDecodeError\(data\[.*\]\[.*\]\)',  # UnicodeDecodeError
            r'UnicodeEncodeError\(data\[.*\]\[.*\]\)',  # UnicodeEncodeError
            r'UnicodeTranslateError\(data\[.*\]\[.*\]\)',  # UnicodeTranslateError
            r'Warning\(data\[.*\]\[.*\]\)',  # Warning
            r'UserWarning\(data\[.*\]\[.*\]\)',  # UserWarning
            r'DeprecationWarning\(data\[.*\]\[.*\]\)',  # DeprecationWarning
            r'PendingDeprecationWarning\(data\[.*\]\[.*\]\)',  # PendingDeprecationWarning
            r'SyntaxWarning\(data\[.*\]\[.*\]\)',  # SyntaxWarning
            r'RuntimeWarning\(data\[.*\]\[.*\]\)',  # RuntimeWarning
            r'FutureWarning\(data\[.*\]\[.*\]\)',  # FutureWarning
            r'ImportWarning\(data\[.*\]\[.*\]\)',  # ImportWarning
            r'UnicodeWarning\(data\[.*\]\[.*\]\)',  # UnicodeWarning
            r'BytesWarning\(data\[.*\]\[.*\]\)',  # BytesWarning
            r'ResourceWarning\(data\[.*\]\[.*\]\)',  # ResourceWarning
        ]
    
    def _load_component_data_requirements(self) -> Dict[str, List[str]]:
        """Load component data requirements from specs"""
        requirements = {}
        
        if not self.docs_specs.exists():
            logger.warning("Specs directory not found")
            return requirements
        
        # Parse component specs for data requirements
        spec_files = {
            'position_monitor': '01_POSITION_MONITOR.md',
            'exposure_monitor': '02_EXPOSURE_MONITOR.md',
            'risk_monitor': '03_RISK_MONITOR.md',
            'pnl_monitor': '04_pnl_monitor.md',
            'strategy_manager': '05_STRATEGY_MANAGER.md',
            'execution_manager': '06_VENUE_MANAGER.md',
            'data_provider': '09_DATA_PROVIDER.md'
        }
        
        for component, spec_file in spec_files.items():
            spec_path = self.docs_specs / spec_file
            if spec_path.exists():
                try:
                    content = spec_path.read_text()
                    # Extract data requirements from spec
                    data_types = re.findall(r'`(\w+_prices|\w+_rates|\w+_costs|\w+_rewards)`', content)
                    requirements[component] = list(set(data_types))
                except Exception as e:
                    logger.warning(f"Could not parse spec {spec_file}: {e}")
        
        return requirements
    
    def validate_component_mode_agnostic_design(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validate component follows mode-agnostic design patterns"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return violations
        
        # Check for hard failure patterns
        for pattern in self.hard_failure_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Check if this is a legitimate pattern
                is_legitimate = False
                for legitimate_pattern in self.legitimate_patterns:
                    if re.search(legitimate_pattern, match.group(), re.IGNORECASE):
                        is_legitimate = True
                        break
                
                if not is_legitimate:
                    line_num = content[:match.start()].count('\n') + 1
                    violations.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': line_num,
                        'code': match.group(),
                        'reason': 'Hard failure pattern - may cause KeyError in mode-agnostic design',
                        'severity': 'HIGH',
                        'suggestion': 'Use .get() with default value or conditional access'
                    })
        
        # Check for graceful degradation patterns (positive indicators)
        graceful_count = 0
        for pattern in self.graceful_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            graceful_count += len(matches)
        
        # If no graceful patterns found, flag as potential issue
        if graceful_count == 0 and any(keyword in content.lower() for keyword in ['data', 'config', 'get']):
            violations.append({
                'file': str(file_path.relative_to(self.project_root)),
                'line': 1,
                'code': 'Component file',
                'reason': 'No graceful degradation patterns found - may not be mode-agnostic',
                'severity': 'MEDIUM',
                'suggestion': 'Add .get() with defaults or conditional data access'
            })
        
        return violations
    
    def validate_data_requirement_coverage(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validate component handles all required data types gracefully"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return violations
        
        # Determine component type from file path
        component_type = None
        if 'position_monitor' in str(file_path):
            component_type = 'position_monitor'
        elif 'exposure_monitor' in str(file_path):
            component_type = 'exposure_monitor'
        elif 'risk_monitor' in str(file_path):
            component_type = 'risk_monitor'
        elif 'pnl_monitor' in str(file_path):
            component_type = 'pnl_monitor'
        elif 'strategy_manager' in str(file_path):
            component_type = 'strategy_manager'
        elif 'execution_manager' in str(file_path):
            component_type = 'execution_manager'
        
        if not component_type or component_type not in self.component_data_requirements:
            return violations
        
        # Check if component handles all data types it might need
        required_data_types = self.component_data_requirements[component_type]
        
        for data_type in required_data_types:
            # Check if data type is accessed gracefully
            if data_type in content:
                # Look for graceful access patterns
                graceful_access = False
                for pattern in self.graceful_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        graceful_access = True
                        break
                
                if not graceful_access:
                    violations.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': 1,
                        'code': f'Data type: {data_type}',
                        'reason': f'Data type {data_type} accessed but no graceful degradation found',
                        'severity': 'MEDIUM',
                        'suggestion': f'Add graceful handling for {data_type} data'
                    })
        
        return violations
    
    def validate_mode_specific_components(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validate mode-specific components are properly identified"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return violations
        
        # Strategy managers should be mode-specific (not mode-agnostic)
        if 'strategy_manager' in str(file_path):
            # Check if it inherits from BaseStrategyManager
            if 'BaseStrategyManager' not in content:
                violations.append({
                    'file': str(file_path.relative_to(self.project_root)),
                    'line': 1,
                    'code': 'Strategy Manager',
                    'reason': 'Strategy Manager should inherit from BaseStrategyManager per architecture',
                    'severity': 'HIGH',
                    'suggestion': 'Inherit from BaseStrategyManager for mode-specific behavior'
                })
        
        return violations
    
    def validate_downstream_dependencies(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validate component considers downstream dependencies"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return violations
        
        # Check for components that might affect downstream consumers
        downstream_indicators = [
            r'return.*data',
            r'return.*result',
            r'return.*exposure',
            r'return.*risk',
            r'return.*pnl',
            r'return.*position'
        ]
        
        has_returns = False
        for pattern in downstream_indicators:
            if re.search(pattern, content, re.IGNORECASE):
                has_returns = True
                break
        
        if has_returns:
            # Check if returns handle missing data gracefully
            return_statements = re.findall(r'return\s+([^;\n]+)', content)
            for return_stmt in return_statements:
                if not any(pattern in return_stmt for pattern in ['.get(', 'if ', 'else', 'None', '0', '[]', '{}']):
                    violations.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': 1,
                        'code': f'return {return_stmt.strip()}',
                        'reason': 'Return statement may not handle missing data gracefully',
                        'severity': 'MEDIUM',
                        'suggestion': 'Ensure return values handle missing data cases'
                    })
        
        return violations
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete mode-agnostic design validation"""
        logger.info("🔍 Starting Mode-Agnostic Design Validation")
        
        results = {
            'overall_status': 'PENDING',
            'total_files_checked': 0,
            'mode_agnostic_violations': [],
            'data_coverage_violations': [],
            'mode_specific_violations': [],
            'downstream_violations': [],
            'summary': {}
        }
        
        # Find component files
        component_files = []
        for pattern in ['*_monitor.py', '*_calculator.py', '*_manager.py']:
            component_files.extend(self.backend_src.rglob(pattern))
        
        # Also include data provider files
        component_files.extend(self.backend_src.rglob('*data_provider*.py'))
        
        results['total_files_checked'] = len(component_files)
        
        logger.info(f"Checking {len(component_files)} component files for mode-agnostic design")
        
        for file_path in component_files:
            # Skip __pycache__ and test files
            if '__pycache__' in str(file_path) or 'test_' in file_path.name:
                continue
            
            # Validate mode-agnostic design
            mode_agnostic_violations = self.validate_component_mode_agnostic_design(file_path)
            results['mode_agnostic_violations'].extend(mode_agnostic_violations)
            
            # Validate data requirement coverage
            data_coverage_violations = self.validate_data_requirement_coverage(file_path)
            results['data_coverage_violations'].extend(data_coverage_violations)
            
            # Validate mode-specific components
            mode_specific_violations = self.validate_mode_specific_components(file_path)
            results['mode_specific_violations'].extend(mode_specific_violations)
            
            # Validate downstream dependencies
            downstream_violations = self.validate_downstream_dependencies(file_path)
            results['downstream_violations'].extend(downstream_violations)
        
        # Calculate summary
        total_violations = (len(results['mode_agnostic_violations']) + 
                          len(results['data_coverage_violations']) + 
                          len(results['mode_specific_violations']) + 
                          len(results['downstream_violations']))
        
        results['summary'] = {
            'total_violations': total_violations,
            'mode_agnostic_violations': len(results['mode_agnostic_violations']),
            'data_coverage_violations': len(results['data_coverage_violations']),
            'mode_specific_violations': len(results['mode_specific_violations']),
            'downstream_violations': len(results['downstream_violations']),
            'files_with_violations': len(set(
                v['file'] for v in results['mode_agnostic_violations'] + 
                results['data_coverage_violations'] + results['mode_specific_violations'] +
                results['downstream_violations']
            ))
        }
        
        # Determine overall status
        high_priority_violations = len([v for v in results['mode_agnostic_violations'] + 
                                      results['mode_specific_violations'] if v['severity'] == 'HIGH'])
        
        if total_violations == 0:
            results['overall_status'] = 'PASS'
        elif high_priority_violations > 0:
            results['overall_status'] = 'FAIL'
        else:
            results['overall_status'] = 'WARN'
        
        return results


def test_mode_agnostic_design():
    """Test mode-agnostic design validation functionality"""
    logger.info("🚀 Starting Mode-Agnostic Design Quality Gate Test")
    
    try:
        # Initialize validator
        validator = ModeAgnosticDesignValidator()
        
        # Run validation
        results = validator.run_validation()
        
        # Print results
        print("\n" + "="*80)
        print("MODE-AGNOSTIC DESIGN QUALITY GATE RESULTS")
        print("="*80)
        print(f"Overall Status: {results['overall_status'].upper()}")
        print(f"Files Checked: {results['total_files_checked']}")
        print()
        
        summary = results['summary']
        print("VIOLATION SUMMARY:")
        print("-" * 40)
        print(f"Total Violations: {summary['total_violations']}")
        print(f"Mode-Agnostic Violations: {summary['mode_agnostic_violations']}")
        print(f"Data Coverage Violations: {summary['data_coverage_violations']}")
        print(f"Mode-Specific Violations: {summary['mode_specific_violations']}")
        print(f"Downstream Violations: {summary['downstream_violations']}")
        print(f"Files with Violations: {summary['files_with_violations']}")
        print()
        
        # Show high priority violations
        high_priority = [v for v in results['mode_agnostic_violations'] + 
                        results['mode_specific_violations'] if v['severity'] == 'HIGH']
        
        if high_priority:
            print("HIGH PRIORITY VIOLATIONS:")
            print("-" * 30)
            for violation in high_priority[:10]:  # Show first 10
                print(f"  {violation['file']}:{violation['line']} - {violation['reason']}")
                print(f"    Suggestion: {violation['suggestion']}")
            if len(high_priority) > 10:
                print(f"  ... and {len(high_priority) - 10} more")
            print()
        
        # Show medium priority violations
        medium_priority = [v for v in results['data_coverage_violations'] + 
                          results['downstream_violations'] if v['severity'] == 'MEDIUM']
        
        if medium_priority:
            print("MEDIUM PRIORITY VIOLATIONS:")
            print("-" * 30)
            for violation in medium_priority[:5]:  # Show first 5
                print(f"  {violation['file']}:{violation['line']} - {violation['reason']}")
            if len(medium_priority) > 5:
                print(f"  ... and {len(medium_priority) - 5} more")
            print()
        
        # Check if test passed
        if results['overall_status'] == 'PASS':
            print("🎉 MODE-AGNOSTIC DESIGN QUALITY GATE: PASSED")
            return True
        elif results['overall_status'] == 'WARN':
            print("⚠️ MODE-AGNOSTIC DESIGN QUALITY GATE: WARNING - Medium priority violations found")
            return True  # Warnings are acceptable
        else:
            print("❌ MODE-AGNOSTIC DESIGN QUALITY GATE: FAILED - High priority violations found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Mode-agnostic design test failed: {e}")
        print(f"\n❌ MODE-AGNOSTIC DESIGN QUALITY GATE: ERROR - {e}")
        return False


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    success = test_mode_agnostic_design()
    sys.exit(0 if success else 1)
