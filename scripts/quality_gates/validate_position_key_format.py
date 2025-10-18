#!/usr/bin/env python3
"""
Quality Gate: Validate Position Key Format Compliance

Ensures all position keys across the system use the canonical format:
venue:position_type:symbol

Usage:
    python scripts/quality_gates/validate_position_key_format.py
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

# Canonical position key pattern
POSITION_KEY_PATTERN = re.compile(r'^[a-z_]+:[A-Za-z]+:[A-Z]+$')

# Valid position types
VALID_POSITION_TYPES = {'BaseToken', 'aToken', 'debtToken', 'Perp'}

# Valid venues
VALID_VENUES = {
    'wallet', 'binance', 'bybit', 'okx',
    'aave', 'aave_v3', 'etherfi', 'lido', 'morpho', 'alchemy'
}

# Deprecated terminology to flag
DEPRECATED_TERMS = ['instrument_id', 'instrument_key', 'position_id']

# Dot notation pattern to flag (but allow legitimate uses)
DOT_NOTATION_PATTERN = re.compile(r'(wallet|binance|bybit|okx|aave|etherfi|lido)\.\w+')


class ValidationResult:
    """Track validation results."""
    
    def __init__(self):
        self.errors: List[Tuple[str, str, str]] = []
        self.warnings: List[Tuple[str, str, str]] = []
        self.passed = True
    
    def add_error(self, file_path: str, line_num: str, message: str):
        """Add an error."""
        self.errors.append((file_path, line_num, message))
        self.passed = False
    
    def add_warning(self, file_path: str, line_num: str, message: str):
        """Add a warning."""
        self.warnings.append((file_path, line_num, message))


def validate_position_key(position_key: str) -> Tuple[bool, str]:
    """
    Validate a position key format.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check basic format
    parts = position_key.split(':')
    if len(parts) != 3:
        return False, f"Invalid format (expected 3 parts, got {len(parts)})"
    
    venue, position_type, symbol = parts
    
    # Validate venue
    if venue not in VALID_VENUES:
        return False, f"Invalid venue '{venue}' (valid: {', '.join(sorted(VALID_VENUES))})"
    
    # Validate position type
    if position_type not in VALID_POSITION_TYPES:
        return False, f"Invalid position_type '{position_type}' (valid: {', '.join(sorted(VALID_POSITION_TYPES))})"
    
    # Validate symbol (alphanumeric, mixed case allowed for tokens like aUSDT, weETH)
    if not re.match(r'^[A-Za-z0-9]+$', symbol):
        return False, f"Invalid symbol '{symbol}' (should be alphanumeric)"
    
    return True, ""


def scan_python_files(result: ValidationResult):
    """Scan Python files for deprecated terminology and format issues."""
    
    print("Scanning Python files...")
    
    backend_dir = Path('backend/src')
    tests_dir = Path('tests')
    
    for directory in [backend_dir, tests_dir]:
        if not directory.exists():
            continue
        
        for py_file in directory.rglob('*.py'):
            with open(py_file, 'r', encoding='utf-8') as f:
                try:
                    lines = f.readlines()
                except Exception as e:
                    result.add_warning(str(py_file), "N/A", f"Could not read file: {e}")
                    continue
            
            for line_num, line in enumerate(lines, 1):
                # Check for deprecated terminology
                for term in DEPRECATED_TERMS:
                    if term in line and not line.strip().startswith('#'):
                        result.add_error(
                            str(py_file),
                            str(line_num),
                            f"Deprecated terminology '{term}' found (use 'position_key' instead)"
                        )
                
                # Check for suspicious dot notation (with context awareness)
                if DOT_NOTATION_PATTERN.search(line):
                    # Skip legitimate uses
                    if any(skip in line for skip in [
                        'url =', 'https://', 'api.',  # API URLs
                        '.items()', '.get(', '.keys()', '.return_value',  # Dict/Mock methods
                        '.yaml', '.md', '.py',  # File extensions
                        'logger.', 'self.', 'mock_',  # Object methods and mocks
                        'get_positions', 'get_balances',  # Position interface methods
                    ]):
                        continue
                    
                    result.add_warning(
                        str(py_file),
                        str(line_num),
                        f"Possible dot notation position key (verify canonical format used)"
                    )


def scan_config_files(result: ValidationResult):
    """Scan config files for position key format compliance."""
    
    print("Scanning config files...")
    
    configs_dir = Path('configs/modes')
    if not configs_dir.exists():
        result.add_error("configs/modes", "N/A", "Mode configs directory not found")
        return
    
    for config_file in configs_dir.glob('*.yaml'):
        with open(config_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        in_position_subscriptions = False
        
        for line_num, line in enumerate(lines, 1):
            # Detect position_subscriptions section
            if 'position_subscriptions:' in line:
                in_position_subscriptions = True
                continue
            
            # Exit section if we hit another top-level key
            if in_position_subscriptions and line.strip() and not line.startswith(' '):
                in_position_subscriptions = False
            
            # Validate position keys in subscriptions
            if in_position_subscriptions and line.strip().startswith('- "'):
                # Extract position key
                match = re.search(r'- "([^"]+)"', line)
                if match:
                    position_key = match.group(1)
                    is_valid, error_msg = validate_position_key(position_key)
                    if not is_valid:
                        result.add_error(
                            str(config_file),
                            str(line_num),
                            f"Invalid position key '{position_key}': {error_msg}"
                        )


def check_documentation_references(result: ValidationResult):
    """Check that INSTRUMENT_DEFINITIONS.md exists and is referenced."""
    
    print("Checking documentation references...")
    
    # Check file exists
    instrument_def_file = Path('docs/INSTRUMENT_DEFINITIONS.md')
    if not instrument_def_file.exists():
        result.add_error(
            "docs/INSTRUMENT_DEFINITIONS.md",
            "N/A",
            "Canonical instrument definitions document not found"
        )
        return
    
    # Check key files reference it
    key_files = [
        'docs/REFERENCE_ARCHITECTURE_CANONICAL.md',
        'docs/COMPONENT_SPECS_INDEX.md',
        'docs/MODES.md',
        'docs/WORKFLOW_GUIDE.md',
    ]
    
    for key_file in key_files:
        file_path = Path(key_file)
        if not file_path.exists():
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'INSTRUMENT_DEFINITIONS' not in content:
            result.add_warning(
                key_file,
                "N/A",
                "Key documentation file should reference INSTRUMENT_DEFINITIONS.md"
            )


def print_results(result: ValidationResult):
    """Print validation results."""
    
    print("\n" + "=" * 70)
    print("POSITION KEY FORMAT VALIDATION RESULTS")
    print("=" * 70)
    
    if result.errors:
        print(f"\n❌ ERRORS ({len(result.errors)}):")
        print("-" * 70)
        for file_path, line_num, message in result.errors:
            print(f"{file_path}:{line_num}")
            print(f"  {message}")
            print()
    
    if result.warnings:
        print(f"\n⚠️  WARNINGS ({len(result.warnings)}):")
        print("-" * 70)
        for file_path, line_num, message in result.warnings:
            print(f"{file_path}:{line_num}")
            print(f"  {message}")
            print()
    
    print("=" * 70)
    if result.passed:
        print("✅ PASS: All position keys use canonical format")
        print("=" * 70)
        return 0
    else:
        print("❌ FAIL: Position key format violations found")
        print("=" * 70)
        return 1


def main():
    """Main validation function."""
    
    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    os.chdir(project_root)
    
    print("Position Key Format Validation")
    print("Canonical Format: venue:position_type:symbol")
    print("=" * 70)
    
    result = ValidationResult()
    
    # Run validation checks
    scan_python_files(result)
    scan_config_files(result)
    check_documentation_references(result)
    
    # Print results and return exit code
    return print_results(result)


if __name__ == '__main__':
    sys.exit(main())

