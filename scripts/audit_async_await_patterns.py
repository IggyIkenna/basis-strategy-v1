#!/usr/bin/env python3
"""
Async/Await Pattern Audit

Audits all async/await usage across the codebase and categorizes as exceptions or violations
per ADR-006 Synchronous Component Execution.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - ADR-006
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


class AsyncAwaitAuditor:
    """Audits async/await usage patterns across the codebase"""
    
    def __init__(self):
        self.project_root = project_root
        self.backend_src = project_root / 'backend' / 'src' / 'basis_strategy_v1'
        
        # ADR-006 Allowed exceptions
        self.allowed_patterns = {
            'event_logger': [
                r'class EventLogger',
                r'async def log_event',
                r'async def log_error',
                r'async def log_warning',
                r'async def log_info',
                r'async def log_debug',
                r'async def log_gas_fee',
                r'async def log_stake',
                r'async def log_aave_supply',
                r'async def log_aave_borrow',
                r'async def log_funding_rate',
                r'async def log_position_update',
                r'async def log_execution',
                r'async def log_risk_event',
                r'async def log_performance',
                r'async def log_system_event',
                r'async def log_atomic_transaction',
                r'async def log_perp_trade',
                r'async def log_funding_payment',
                r'async def log_liquidation',
                r'async def log_rebalance',
                r'async def log_withdrawal',
                r'async def log_deposit',
                r'async def log_swap',
                r'async def log_claim',
                r'async def log_venue_transfer',
                r'async def log_risk_alert',
                r'async def log_seasonal_reward_distribution',
                r'async def _log_event_json',
                r'async def _log_event_csv',
                r'async def _log_event_text',
                r'async def _log_transfer_event',
                r'async def _log_execution_event'
            ],
            'results_store': [
                r'class ResultsStore',
                r'class AsyncResultsStore',
                r'async def store_result',
                r'async def store_event',
                r'async def export_results',
                r'async def.*queue.*',
                r'async def start',
                r'async def stop',
                r'async def _worker',
                r'async def get_result',
                r'async def list_results',
                r'async def delete_result'
            ],
            'api_entry_points': [
                r'async def run_backtest',
                r'async def start_live_trading',
                r'async def.*api.*',
                r'async def.*endpoint.*',
                r'async def.*route.*',
                r'async def basic_health',
                r'async def detailed_health',
                r'async def health_status',
                r'async def login',
                r'async def list_charts',
                r'async def get_chart',
                r'async def get_dashboard',
                r'async def list_strategies',
                r'async def get_strategy',
                r'async def get_merged_config',
                r'async def get_result_events',
                r'async def get_export_info',
                r'async def list_results',
                r'async def get_backtest_status',
                r'async def get_backtest_result',
                r'async def cancel_backtest',
                r'async def get_live_trading_status',
                r'async def get_live_trading_performance',
                r'async def stop_live_trading',
                r'async def dispatch',
                r'async def root',
                r'async def global_exception_handler',
                r'async def emergency_stop',
                r'async def emergency_stop_live_trading'
            ],
            'io_operations': [
                r'async def.*file.*',
                r'async def.*read.*',
                r'async def.*write.*',
                r'async def.*load.*',
                r'async def.*save.*',
                r'async def.*database.*',
                r'async def.*query.*',
                r'async def.*execute.*',
                r'async def.*http.*',
                r'async def.*websocket.*',
                r'async def.*connect.*',
                r'async def.*fetch.*',
                r'async def.*download.*',
                r'async def.*upload.*',
                r'async def get_spot_price',
                r'async def get_funding_rate',
                r'async def get_gas_price',
                r'async def.*price.*',
                r'async def.*rate.*',
                r'async def.*balance.*',
                r'async def.*position.*',
                r'async def.*order.*',
                r'async def.*trade.*',
                r'async def.*transaction.*',
                r'async def.*confirmation.*',
                r'async def.*build.*',
                r'async def.*await.*',
                r'async def __aenter__',
                r'async def __aexit__',
                r'async def.*cache.*',
                r'async def.*session.*',
                r'async def _get_dependencies',
                r'async def.*dependency.*',
                r'async def.*inject.*'
            ]
        }
        
        # ADR-006 Violations (component internal methods)
        self.violation_patterns = [
            r'async def update_state',
            r'async def.*calculate.*',
            r'async def.*process.*',
            r'async def.*handle.*',
            r'async def.*monitor.*',
            r'async def.*reconcile.*',
            r'async def.*validate.*',
            r'async def.*check.*',
            r'async def.*get_.*',
            r'async def.*set_.*',
            r'async def.*update_.*',
            r'async def.*sync_.*'
        ]
        
        # Priority files from DEVIATIONS_AND_CORRECTIONS.md
        self.priority_files = [
            'backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py',
            'backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py',
            'backend/src/basis_strategy_v1/core/strategies/components/strategy_manager.py',
            'backend/src/basis_strategy_v1/core/strategies/components/pnl_calculator.py',
            'backend/src/basis_strategy_v1/core/strategies/components/position_update_handler.py'
        ]
    
    def audit_file(self, file_path: Path) -> Dict[str, Any]:
        """Audit a single file for async/await patterns"""
        result = {
            'file': str(file_path.relative_to(self.project_root)),
            'total_async_methods': 0,
            'allowed_exceptions': [],
            'violations': [],
            'api_calls': [],
            'concurrent_patterns': [],
            'status': 'UNKNOWN'
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            result['status'] = 'ERROR'
            return result
        
        # Find all async methods
        async_methods = re.findall(r'async def (\w+)', content)
        result['total_async_methods'] = len(async_methods)
        
        if len(async_methods) == 0:
            result['status'] = 'COMPLIANT'
            return result
        
        # Check each async method
        for method_match in re.finditer(r'async def (\w+)', content):
            method_name = method_match.group(1)
            line_num = content[:method_match.start()].count('\n') + 1
            method_line = content.split('\n')[line_num - 1].strip()
            
            # Check if it's an allowed exception
            is_allowed = False
            allowed_category = None
            
            for category, patterns in self.allowed_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, method_line, re.IGNORECASE):
                        is_allowed = True
                        allowed_category = category
                        break
                if is_allowed:
                    break
            
            if is_allowed:
                result['allowed_exceptions'].append({
                    'method': method_name,
                    'line': line_num,
                    'code': method_line,
                    'category': allowed_category
                })
            else:
                # Check if it's a violation
                is_violation = False
                for pattern in self.violation_patterns:
                    if re.search(pattern, method_line, re.IGNORECASE):
                        is_violation = True
                        break
                
                if is_violation:
                    result['violations'].append({
                        'method': method_name,
                        'line': line_num,
                        'code': method_line,
                        'reason': 'Component internal method should be synchronous per ADR-006'
                    })
                else:
                    # Unknown pattern - needs manual review
                    result['violations'].append({
                        'method': method_name,
                        'line': line_num,
                        'code': method_line,
                        'reason': 'Unknown async pattern - needs manual review'
                    })
        
        # Check for API calls and concurrent patterns
        api_patterns = [
            r'requests\.get\(',
            r'requests\.post\(',
            r'aiohttp\.ClientSession',
            r'asyncio\.gather\(',
            r'asyncio\.create_task\(',
            r'asyncio\.wait\(',
            r'concurrent\.futures'
        ]
        
        for pattern in api_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                if 'asyncio.gather' in pattern or 'asyncio.create_task' in pattern or 'asyncio.wait' in pattern:
                    result['concurrent_patterns'].append({
                        'line': line_num,
                        'code': match.group(),
                        'reason': 'Concurrent execution pattern - needs queueing'
                    })
                else:
                    result['api_calls'].append({
                        'line': line_num,
                        'code': match.group(),
                        'reason': 'API call pattern'
                    })
        
        # Determine status
        if len(result['violations']) == 0:
            result['status'] = 'COMPLIANT'
        elif len(result['violations']) > 0 and len(result['allowed_exceptions']) > 0:
            result['status'] = 'PARTIAL'
        else:
            result['status'] = 'VIOLATION'
        
        return result
    
    def run_audit(self) -> Dict[str, Any]:
        """Run complete async/await audit"""
        logger.info("🔍 Starting Async/Await Pattern Audit")
        
        results = {
            'overall_status': 'PENDING',
            'total_files_audited': 0,
            'compliant_files': 0,
            'partial_files': 0,
            'violation_files': 0,
            'error_files': 0,
            'priority_violations': [],
            'file_results': [],
            'summary': {}
        }
        
        # Find all Python files
        python_files = list(self.backend_src.rglob('*.py'))
        results['total_files_audited'] = len(python_files)
        
        logger.info(f"Auditing {len(python_files)} Python files for async/await patterns")
        
        for file_path in python_files:
            # Skip __pycache__ and test files
            if '__pycache__' in str(file_path) or 'test_' in file_path.name:
                continue
            
            file_result = self.audit_file(file_path)
            results['file_results'].append(file_result)
            
            # Count by status
            if file_result['status'] == 'COMPLIANT':
                results['compliant_files'] += 1
            elif file_result['status'] == 'PARTIAL':
                results['partial_files'] += 1
            elif file_result['status'] == 'VIOLATION':
                results['violation_files'] += 1
            elif file_result['status'] == 'ERROR':
                results['error_files'] += 1
            
            # Check if it's a priority file with violations
            file_str = str(file_path.relative_to(self.project_root))
            if file_str in self.priority_files and file_result['status'] in ['VIOLATION', 'PARTIAL']:
                results['priority_violations'].append(file_result)
        
        # Calculate summary
        total_violations = sum(len(f['violations']) for f in results['file_results'])
        total_exceptions = sum(len(f['allowed_exceptions']) for f in results['file_results'])
        total_concurrent = sum(len(f['concurrent_patterns']) for f in results['file_results'])
        
        results['summary'] = {
            'total_violations': total_violations,
            'total_exceptions': total_exceptions,
            'total_concurrent_patterns': total_concurrent,
            'priority_files_with_violations': len(results['priority_violations']),
            'compliance_rate': (results['compliant_files'] / results['total_files_audited']) * 100
        }
        
        # Determine overall status
        if results['violation_files'] == 0:
            results['overall_status'] = 'COMPLIANT'
        elif len(results['priority_violations']) > 0:
            results['overall_status'] = 'CRITICAL'
        elif results['violation_files'] > 0:
            results['overall_status'] = 'VIOLATIONS'
        else:
            results['overall_status'] = 'COMPLIANT'
        
        return results


def run_async_await_audit():
    """Run async/await pattern audit"""
    logger.info("🚀 Starting Async/Await Pattern Audit")
    
    try:
        # Initialize auditor
        auditor = AsyncAwaitAuditor()
        
        # Run audit
        results = auditor.run_audit()
        
        # Print results
        print("\n" + "="*80)
        print("ASYNC/AWAIT PATTERN AUDIT RESULTS")
        print("="*80)
        print(f"Overall Status: {results['overall_status'].upper()}")
        print(f"Files Audited: {results['total_files_audited']}")
        print()
        
        summary = results['summary']
        print("AUDIT SUMMARY:")
        print("-" * 40)
        print(f"Compliant Files: {results['compliant_files']}")
        print(f"Partial Files: {results['partial_files']}")
        print(f"Violation Files: {results['violation_files']}")
        print(f"Error Files: {results['error_files']}")
        print(f"Compliance Rate: {summary['compliance_rate']:.1f}%")
        print()
        print(f"Total Violations: {summary['total_violations']}")
        print(f"Total Exceptions: {summary['total_exceptions']}")
        print(f"Concurrent Patterns: {summary['total_concurrent_patterns']}")
        print(f"Priority Files with Violations: {summary['priority_files_with_violations']}")
        print()
        
        # Show priority violations
        if results['priority_violations']:
            print("PRIORITY FILE VIOLATIONS:")
            print("-" * 30)
            for file_result in results['priority_violations']:
                print(f"  {file_result['file']} ({file_result['status']})")
                for violation in file_result['violations'][:3]:  # Show first 3
                    print(f"    Line {violation['line']}: {violation['method']} - {violation['reason']}")
                if len(file_result['violations']) > 3:
                    print(f"    ... and {len(file_result['violations']) - 3} more violations")
            print()
        
        # Show files with most violations
        violation_files = [f for f in results['file_results'] if f['violations']]
        violation_files.sort(key=lambda x: len(x['violations']), reverse=True)
        
        if violation_files:
            print("FILES WITH MOST VIOLATIONS:")
            print("-" * 30)
            for file_result in violation_files[:5]:  # Show top 5
                print(f"  {file_result['file']}: {len(file_result['violations'])} violations")
            print()
        
        # Show concurrent patterns
        concurrent_files = [f for f in results['file_results'] if f['concurrent_patterns']]
        if concurrent_files:
            print("FILES WITH CONCURRENT PATTERNS:")
            print("-" * 30)
            for file_result in concurrent_files:
                print(f"  {file_result['file']}: {len(file_result['concurrent_patterns'])} patterns")
            print()
        
        # Save detailed results
        output_file = project_root / 'async_await_audit_results.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Detailed results saved to: {output_file}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Async/await audit failed: {e}")
        print(f"\n❌ ASYNC/AWAIT AUDIT: ERROR - {e}")
        return None


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run audit
    results = run_async_await_audit()
    if results:
        sys.exit(0 if results['overall_status'] in ['COMPLIANT'] else 1)
    else:
        sys.exit(1)
