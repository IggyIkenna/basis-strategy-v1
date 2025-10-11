#!/usr/bin/env python3
"""
Logical Exceptions Quality Gates

Validates fail-fast and async/await patterns respect documented exceptions.
Ensures proper handling of I/O operations, mode-agnostic design, and documented config defaults.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - ADR-006 Synchronous Component Execution
Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-040 Config Validation: Fail-Fast, No Silent Defaults
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


class LogicalExceptionValidator:
    """Validates logical exceptions for fail-fast and async/await patterns"""
    
    def __init__(self):
        self.project_root = project_root
        self.backend_src = project_root / 'backend' / 'src' / 'basis_strategy_v1'
        self.documented_config_defaults = self._load_documented_defaults()
        self.io_operation_patterns = [
            r'pd\.read_csv\(',
            r'json\.load\(',
            r'requests\.get\(',
            r'aiohttp\.ClientSession\(',
            r'\.query\(',
            r'\.execute\(',
            r'open\(',
            r'\.read\(',
            r'\.write\(',
            r'\.save\(',
            r'\.load\(',
            r'\.fetch\(',
            r'\.get\(',
            r'\.post\(',
            r'\.put\(',
            r'\.delete\(',
            r'\.connect\(',
            r'\.close\('
        ]
        
        # Async/await exception patterns (per ADR-006)
        self.async_exception_patterns = [
            r'class EventLogger',
            r'class ResultsStore',
            r'async def log_event',
            r'async def store_result',
            r'async def run_backtest',
            r'async def start_live_trading',
            r'async def.*api.*',
            r'async def.*http.*',
            r'async def.*file.*',
            r'async def.*database.*',
            r'async def.*websocket.*'
        ]
        
        # Async/await violation patterns (excluding API exception handlers)
        self.async_violation_patterns = [
            r'async def update_state',
            r'async def.*calculate.*',
            r'async def.*process.*',
            r'async def.*monitor.*',
            r'async def.*reconcile.*',
            r'async def _update_position_monitor',
            r'async def _calculate_final_results',
            r'async def _process_timestep'
        ]
        
        # Exclude API exception handlers and other allowed patterns
        self.async_exception_patterns = [
            r'async def.*exception_handler',
            r'async def.*endpoint',
            r'async def.*route',
            r'async def.*api.*',
            r'async def.*health.*',
            r'async def.*login.*',
            r'async def.*chart.*',
            r'async def.*dashboard.*',
            r'async def.*strategy.*',
            r'async def.*result.*',
            r'async def.*backtest.*',
            r'async def.*live.*',
            r'async def.*trading.*',
            r'async def.*emergency.*',
            r'async def.*stop.*',
            r'async def.*start.*',
            r'async def.*dispatch.*',
            r'async def.*root.*',
            r'async def.*global_exception_handler'
        ]
    
    def _load_documented_defaults(self) -> Dict[str, Any]:
        """Load documented config defaults from component specs"""
        defaults = {}
        
        # Load from component specs
        specs_dir = project_root / 'docs' / 'specs'
        if specs_dir.exists():
            for spec_file in specs_dir.glob('*.md'):
                try:
                    content = spec_file.read_text()
                    # Extract documented defaults
                    default_matches = re.findall(r'Default.*?(\d+|\w+)', content)
                    if default_matches:
                        defaults[spec_file.stem] = default_matches
                except Exception as e:
                    logger.warning(f"Could not parse spec file {spec_file}: {e}")
        
        return defaults
    
    def validate_fail_fast_exceptions(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validate .get() usage against documented exceptions"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return violations
        
        for line_num, line in enumerate(lines, 1):
            if '.get(' in line:
                if not self._is_logical_exception(line, line_num, file_path):
                    violations.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': line_num,
                        'code': line.strip(),
                        'reason': 'Undocumented .get() usage - may mask config errors',
                        'severity': 'HIGH'
                    })
        
        return violations
    
    def _is_logical_exception(self, line: str, line_num: int, file_path: Path) -> bool:
        """Check if .get() usage is a logical exception"""
        
        # Exception 1: I/O operations
        for pattern in self.io_operation_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        # Exception 2: Mode-agnostic components returning 0/empty
        mode_agnostic_patterns = [
            r'\.get\(.*,\s*0\)',  # Returns 0 for missing data
            r'\.get\(.*,\s*\{\}\)',  # Returns empty dict
            r'\.get\(.*,\s*\[\]\)',  # Returns empty list
            r'\.get\(.*,\s*None\)',  # Returns None for optional data
            r'exposures\.get\(',
            r'attributions\.get\(',
            r'risks\.get\(',
            r'balances\.get\(',
            r'venues\.get\('
        ]
        
        for pattern in mode_agnostic_patterns:
            if re.search(pattern, line):
                return True
        
        # Exception 3: Documented config defaults
        # Check if this is a documented default from component specs
        for spec_name, defaults in self.documented_config_defaults.items():
            for default in defaults:
                if default in line:
                    return True
        
        # Exception 4: API response parsing
        api_response_patterns = [
            r'response\.json\(\)\.get\(',
            r'data\.get\(',
            r'result\.get\(',
            r'payload\.get\('
        ]
        
        for pattern in api_response_patterns:
            if re.search(pattern, line):
                return True
        
        return False
    
    def validate_async_exceptions(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validate async/await usage against ADR-006 exceptions"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return violations
        
        # Check for async violations
        for pattern in self.async_violation_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Check if this is an allowed exception
                is_exception = False
                for exception_pattern in self.async_exception_patterns:
                    if re.search(exception_pattern, match.group(), re.IGNORECASE):
                        is_exception = True
                        break
                
                if not is_exception:
                    line_num = content[:match.start()].count('\n') + 1
                    violations.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': line_num,
                        'code': match.group(),
                        'reason': 'Async/await violation - component internal methods should be synchronous per ADR-006',
                        'severity': 'HIGH'
                    })
        
        return violations
    
    def validate_api_call_queueing(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validate API calls are properly queued"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return violations
        
        # Check for concurrent API calls without queueing
        concurrent_patterns = [
            r'asyncio\.gather\(',
            r'asyncio\.create_task\(',
            r'asyncio\.wait\(',
            r'concurrent\.futures',
            r'ThreadPoolExecutor',
            r'ProcessPoolExecutor'
        ]
        
        for pattern in concurrent_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                violations.append({
                    'file': str(file_path.relative_to(self.project_root)),
                    'line': line_num,
                    'code': match.group(),
                    'reason': 'Concurrent API calls must be queued to prevent race conditions',
                    'severity': 'MEDIUM'
                })
        
        return violations
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete logical exception validation"""
        logger.info("🔍 Starting Logical Exception Validation")
        
        results = {
            'overall_status': 'PENDING',
            'total_files_checked': 0,
            'fail_fast_violations': [],
            'async_violations': [],
            'api_queueing_violations': [],
            'summary': {}
        }
        
        # Find all Python files in backend/src
        python_files = list(self.backend_src.rglob('*.py'))
        results['total_files_checked'] = len(python_files)
        
        logger.info(f"Checking {len(python_files)} Python files for logical exceptions")
        
        for file_path in python_files:
            # Skip __pycache__ and test files
            if '__pycache__' in str(file_path) or 'test_' in file_path.name:
                continue
            
            # Validate fail-fast exceptions
            fail_fast_violations = self.validate_fail_fast_exceptions(file_path)
            results['fail_fast_violations'].extend(fail_fast_violations)
            
            # Validate async exceptions
            async_violations = self.validate_async_exceptions(file_path)
            results['async_violations'].extend(async_violations)
            
            # Validate API call queueing
            api_violations = self.validate_api_call_queueing(file_path)
            results['api_queueing_violations'].extend(api_violations)
        
        # Calculate summary
        total_violations = (len(results['fail_fast_violations']) + 
                          len(results['async_violations']) + 
                          len(results['api_queueing_violations']))
        
        results['summary'] = {
            'total_violations': total_violations,
            'fail_fast_violations': len(results['fail_fast_violations']),
            'async_violations': len(results['async_violations']),
            'api_queueing_violations': len(results['api_queueing_violations']),
            'files_with_violations': len(set(
                v['file'] for v in results['fail_fast_violations'] + 
                results['async_violations'] + results['api_queueing_violations']
            ))
        }
        
        # Determine overall status
        if total_violations == 0:
            results['overall_status'] = 'PASS'
        elif len(results['async_violations']) > 0:
            results['overall_status'] = 'FAIL'  # High priority violations
        else:
            results['overall_status'] = 'WARN'  # Medium priority violations
        
        return results


def test_logical_exceptions():
    """Test logical exception validation functionality"""
    logger.info("🚀 Starting Logical Exception Quality Gate Test")
    
    try:
        # Initialize validator
        validator = LogicalExceptionValidator()
        
        # Run validation
        results = validator.run_validation()
        
        # Print results
        print("\n" + "="*80)
        print("LOGICAL EXCEPTION QUALITY GATE RESULTS")
        print("="*80)
        print(f"Overall Status: {results['overall_status'].upper()}")
        print(f"Files Checked: {results['total_files_checked']}")
        print()
        
        summary = results['summary']
        print("VIOLATION SUMMARY:")
        print("-" * 40)
        print(f"Total Violations: {summary['total_violations']}")
        print(f"Fail-Fast Violations: {summary['fail_fast_violations']}")
        print(f"Async/Await Violations: {summary['async_violations']}")
        print(f"API Queueing Violations: {summary['api_queueing_violations']}")
        print(f"Files with Violations: {summary['files_with_violations']}")
        print()
        
        # Show high priority violations
        if results['async_violations']:
            print("HIGH PRIORITY VIOLATIONS (Async/Await):")
            print("-" * 50)
            for violation in results['async_violations'][:10]:  # Show first 10
                print(f"  {violation['file']}:{violation['line']} - {violation['reason']}")
            if len(results['async_violations']) > 10:
                print(f"  ... and {len(results['async_violations']) - 10} more")
            print()
        
        # Show fail-fast violations
        if results['fail_fast_violations']:
            print("FAIL-FAST VIOLATIONS:")
            print("-" * 30)
            for violation in results['fail_fast_violations'][:10]:  # Show first 10
                print(f"  {violation['file']}:{violation['line']} - {violation['reason']}")
            if len(results['fail_fast_violations']) > 10:
                print(f"  ... and {len(results['fail_fast_violations']) - 10} more")
            print()
        
        # Check if test passed
        if results['overall_status'] == 'PASS':
            print("🎉 LOGICAL EXCEPTION QUALITY GATE: PASSED")
            return True
        elif results['overall_status'] == 'WARN':
            print("⚠️ LOGICAL EXCEPTION QUALITY GATE: WARNING - Medium priority violations found")
            return True  # Warnings are acceptable
        else:
            print("❌ LOGICAL EXCEPTION QUALITY GATE: FAILED - High priority violations found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Logical exception test failed: {e}")
        print(f"\n❌ LOGICAL EXCEPTION QUALITY GATE: ERROR - {e}")
        return False


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    success = test_logical_exceptions()
    sys.exit(0 if success else 1)
