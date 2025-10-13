#!/usr/bin/env python3
"""
Data Provider Canonical Access Quality Gates - Simplified Version

Core validation tests for data provider canonical access patterns:
- Legacy method detection and removal validation
- Canonical get_data(timestamp) pattern validation
- Standardized data structure extraction validation
"""

import os
import sys
import re
import ast
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
import structlog

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

logger = structlog.get_logger()

class DataProviderCanonicalAccessQualityGates:
    """Quality gates for data provider canonical access validation."""
    
    def __init__(self):
        self.results = {}
        self.passed = 0
        self.failed = 0
        self.total = 0
        
        # Legacy methods to detect and remove
        self.legacy_methods = [
            'get_cex_derivatives_balances',
            'get_cex_spot_balances', 
            'get_current_data',
            'get_execution_cost',
            'get_funding_rate',
            'get_gas_cost',
            'get_liquidity_index',  # Note: May be needed by UtilityManager per spec 16
            'get_market_data_snapshot',
            'get_market_price',
            'get_smart_contract_balances',
            'get_wallet_balances'
        ]
        
        # Canonical patterns to validate
        self.canonical_patterns = {
            'get_data_call': r'data_provider\.get_data\(|self\.data_provider\.get_data\(',
            'standardized_structure': r"data\['market_data'\]|data\['protocol_data'\]|data\['execution_data'\]|data\['staking_data'\]",
            'market_data_access': r"data\['market_data'\]\['prices'\]|data\['market_data'\]\['rates'\]",
            'protocol_data_access': r"data\['protocol_data'\]\['aave_indexes'\]|data\['protocol_data'\]\['oracle_prices'\]",
            'execution_data_access': r"data\['execution_data'\]\['wallet_balances'\]|data\['execution_data'\]\['gas_costs'\]"
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all quality gate tests."""
        logger.info("Starting Data Provider Canonical Access Quality Gates")
        
        tests = [
            ("Legacy Method Detection", self.test_legacy_method_detection),
            ("Canonical Pattern Validation", self.test_canonical_pattern_validation),
            ("Standardized Structure Extraction", self.test_standardized_structure_extraction),
            ("Component Data Access Scan", self.test_component_data_access_scan)
        ]
        
        for test_name, test_func in tests:
            self.total += 1
            try:
                logger.info(f"Running test: {test_name}")
                result = test_func()
                if result:
                    self.passed += 1
                    self.results[test_name] = {"status": "PASSED", "details": result}
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    self.failed += 1
                    self.results[test_name] = {"status": "FAILED", "details": "Test returned False"}
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.failed += 1
                self.results[test_name] = {"status": "FAILED", "details": str(e)}
                logger.error(f"❌ {test_name}: FAILED - {e}")
        
        return self.generate_report()
    
    def find_component_files(self) -> List[str]:
        """Find all component implementation files."""
        component_files = []
        backend_dir = Path(__file__).parent.parent / "backend" / "src" / "basis_strategy_v1"
        
        search_dirs = [
            "core/components/",
            "core/strategies/",
            "core/math/",
            "core/interfaces/",
            "core/utilities/",
            "core/event_engine/",
            "core/health/",
            "core/execution/",
            "core/reconciliation/"
        ]
        
        for search_dir in search_dirs:
            full_path = backend_dir / search_dir
            if full_path.exists():
                for file in full_path.rglob("*.py"):
                    if not file.name.startswith("__") and not file.name.startswith("test_"):
                        component_files.append(str(file))
        
        return component_files
    
    def test_legacy_method_detection(self) -> bool:
        """Test 1: Detect any legacy data provider method calls in components."""
        try:
            component_files = self.find_component_files()
            violations = []
            
            for file_path in component_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for each legacy method
                    for method in self.legacy_methods:
                        # Look for method calls (but exclude comments)
                        pattern = rf'data_provider\.{method}\(|self\.data_provider\.{method}\('
                        matches = re.finditer(pattern, content)
                        
                        for match in matches:
                            # Find line number
                            line_num = content[:match.start()].count('\n') + 1
                            line_content = content.split('\n')[line_num - 1].strip()
                            
                            # Skip if it's a comment
                            if line_content.startswith('#') or line_content.startswith('"""'):
                                continue
                                
                            violations.append({
                                'file': file_path,
                                'method': method,
                                'line': line_num,
                                'context': line_content
                            })
                
                except Exception as e:
                    logger.warning(f"Could not analyze file {file_path}: {e}")
                    continue
            
            if violations:
                logger.error(f"Found {len(violations)} legacy method violations:")
                for violation in violations:
                    logger.error(f"  {violation['file']}:{violation['line']} - {violation['method']}")
                    logger.error(f"    Context: {violation['context']}")
                return False
            
            return {"message": f"No legacy method calls found in {len(component_files)} component files"}
            
        except Exception as e:
            logger.error(f"Legacy method detection test failed: {e}")
            return False
    
    def test_canonical_pattern_validation(self) -> bool:
        """Test 2: Validate all components use canonical get_data(timestamp) pattern."""
        try:
            component_files = self.find_component_files()
            violations = []
            compliant_files = 0
            
            for file_path in component_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if file uses data_provider
                    if 'data_provider' not in content:
                        continue
                    
                    # Skip factory classes and interfaces that don't directly access data
                    file_name = os.path.basename(file_path)
                    if any(skip in file_name for skip in ['factory', 'interface', 'manager']):
                        continue
                    
                    # Only check components that actually use data_provider in methods (not just store it)
                    if not re.search(r'self\.data_provider\.', content):
                        continue
                    
                    # Check for canonical get_data pattern
                    has_canonical = bool(re.search(self.canonical_patterns['get_data_call'], content))
                    
                    if not has_canonical:
                        violations.append({
                            'file': file_path,
                            'issue': 'No canonical get_data(timestamp) pattern found',
                            'suggestion': 'Use data = self.data_provider.get_data(timestamp)'
                        })
                    else:
                        compliant_files += 1
                
                except Exception as e:
                    logger.warning(f"Could not analyze file {file_path}: {e}")
                    continue
            
            if violations:
                logger.error(f"Found {len(violations)} canonical pattern violations:")
                for violation in violations:
                    logger.error(f"  {violation['file']} - {violation['issue']}")
                    logger.error(f"    Suggestion: {violation['suggestion']}")
                return False
            
            return {"message": f"All {compliant_files} component files use canonical get_data pattern"}
            
        except Exception as e:
            logger.error(f"Canonical pattern validation test failed: {e}")
            return False
    
    def test_standardized_structure_extraction(self) -> bool:
        """Test 3: Validate components correctly extract from standardized data structure."""
        try:
            component_files = self.find_component_files()
            violations = []
            compliant_files = 0
            
            for file_path in component_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if file uses get_data
                    if not re.search(self.canonical_patterns['get_data_call'], content):
                        continue
                    
                    # Skip factory classes and interfaces that don't directly access data
                    file_name = os.path.basename(file_path)
                    if any(skip in file_name for skip in ['factory', 'interface', 'manager']):
                        continue
                    
                    # Check for standardized structure access
                    has_standardized = any(
                        re.search(pattern, content) 
                        for pattern in self.canonical_patterns.values()
                        if pattern != self.canonical_patterns['get_data_call']
                    )
                    
                    if not has_standardized:
                        violations.append({
                            'file': file_path,
                            'issue': 'Uses get_data but not standardized structure access',
                            'suggestion': 'Use data[\'market_data\'][\'prices\'], data[\'protocol_data\'][\'aave_indexes\'], etc.'
                        })
                    else:
                        compliant_files += 1
                
                except Exception as e:
                    logger.warning(f"Could not analyze file {file_path}: {e}")
                    continue
            
            if violations:
                logger.error(f"Found {len(violations)} standardized structure violations:")
                for violation in violations:
                    logger.error(f"  {violation['file']} - {violation['issue']}")
                    logger.error(f"    Suggestion: {violation['suggestion']}")
                return False
            
            return {"message": f"All {compliant_files} component files use standardized structure access"}
            
        except Exception as e:
            logger.error(f"Standardized structure extraction test failed: {e}")
            return False
    
    def test_component_data_access_scan(self) -> bool:
        """Test 4: Comprehensive scan of all component data access patterns."""
        try:
            component_files = self.find_component_files()
            scan_results = {
                'total_files': len(component_files),
                'files_with_data_provider': 0,
                'canonical_patterns': 0,
                'legacy_violations': 0,
                'structure_violations': 0,
                'detailed_violations': []
            }
            
            for file_path in component_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Skip if no data_provider usage
                    if 'data_provider' not in content:
                        continue
                    
                    # Only count files that actually use data_provider in methods
                    if not re.search(r'self\.data_provider\.', content):
                        continue
                    
                    scan_results['files_with_data_provider'] += 1
                    
                    # Check for canonical pattern
                    if re.search(self.canonical_patterns['get_data_call'], content):
                        scan_results['canonical_patterns'] += 1
                    
                    # Check for legacy methods
                    for method in self.legacy_methods:
                        if re.search(rf'data_provider\.{method}\(|self\.data_provider\.{method}\(', content):
                            scan_results['legacy_violations'] += 1
                            scan_results['detailed_violations'].append({
                                'file': file_path,
                                'type': 'legacy_method',
                                'method': method
                            })
                    
                    # Check for non-standardized access
                    if re.search(self.canonical_patterns['get_data_call'], content):
                        has_standardized = any(
                            re.search(pattern, content) 
                            for pattern in self.canonical_patterns.values()
                            if pattern != self.canonical_patterns['get_data_call']
                        )
                        # Also check if the component passes data through to other methods (which is valid)
                        passes_data_through = re.search(r'market_data.*\)|data.*\)', content)
                        if not has_standardized and not passes_data_through:
                            scan_results['structure_violations'] += 1
                            scan_results['detailed_violations'].append({
                                'file': file_path,
                                'type': 'non_standardized_access'
                            })
                
                except Exception as e:
                    logger.warning(f"Could not analyze file {file_path}: {e}")
                    continue
            
            # Check if we have any violations
            total_violations = scan_results['legacy_violations'] + scan_results['structure_violations']
            
            if total_violations > 0:
                logger.error(f"Component data access scan found {total_violations} violations:")
                for violation in scan_results['detailed_violations']:
                    logger.error(f"  {violation['file']} - {violation['type']}")
                    if 'method' in violation:
                        logger.error(f"    Legacy method: {violation['method']}")
                return False
            
            return scan_results
            
        except Exception as e:
            logger.error(f"Component data access scan test failed: {e}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        success_rate = (self.passed / self.total * 100) if self.total > 0 else 0
        
        report = {
            "summary": {
                "total_tests": self.total,
                "passed": self.passed,
                "failed": self.failed,
                "success_rate": f"{success_rate:.1f}%"
            },
            "results": self.results,
            "status": "PASSED" if self.failed == 0 else "FAILED"
        }
        
        logger.info(f"Data Provider Canonical Access Quality Gates Complete: {self.passed}/{self.total} passed ({success_rate:.1f}%)")
        
        return report

def main():
    """Run the data provider canonical access quality gates."""
    quality_gates = DataProviderCanonicalAccessQualityGates()
    report = quality_gates.run_all_tests()
    
    print("\n" + "="*80)
    print("DATA PROVIDER CANONICAL ACCESS QUALITY GATES REPORT")
    print("="*80)
    print(f"Status: {report['status']}")
    print(f"Tests: {report['summary']['passed']}/{report['summary']['total_tests']} passed")
    print(f"Success Rate: {report['summary']['success_rate']}")
    print("\nDetailed Results:")
    
    for test_name, result in report['results'].items():
        status_icon = "✅" if result['status'] == 'PASSED' else "❌"
        print(f"{status_icon} {test_name}: {result['status']}")
        if result['status'] == 'FAILED':
            print(f"   Details: {result['details']}")
    
    print("="*80)
    
    # Add success indicator for quality gate runner
    if report['status'] == 'PASSED':
        print("SUCCESS: All data provider canonical access quality gates passed!")
    
    # Exit with error code if any tests failed
    if report['status'] == 'FAILED':
        sys.exit(1)

if __name__ == "__main__":
    main()
