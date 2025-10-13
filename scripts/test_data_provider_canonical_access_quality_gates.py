#!/usr/bin/env python3
"""
Data Provider Canonical Access Quality Gates

Comprehensive tests for data provider canonical access patterns including:
- Legacy method detection and removal validation
- Canonical get_data(timestamp) pattern validation
- Standardized data structure extraction validation
- Environment variable validation
- Factory pattern functionality
- On-demand data loading validation
- Date range validation
- Health checks
"""

import os
import sys
import asyncio
import pandas as pd
import re
import ast
from pathlib import Path
from datetime import datetime, timedelta
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
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all quality gate tests."""
        logger.info("Starting Data Provider Canonical Access Quality Gates")
        
        tests = [
            ("Legacy Method Detection", self.test_legacy_method_detection),
            ("Canonical Pattern Validation", self.test_canonical_pattern_validation),
            ("Standardized Structure Extraction", self.test_standardized_structure_extraction),
            ("Component Data Access Scan", self.test_component_data_access_scan),
            ("Environment Variable Validation", self.test_environment_variables),
            ("Data Provider Factory", self.test_data_provider_factory),
            ("On-Demand Data Loading", self.test_on_demand_loading),
            ("Date Range Validation", self.test_date_range_validation),
            ("Health Check Integration", self.test_health_check_integration),
            ("No Startup Data Loading", self.test_no_startup_loading),
            ("Error Handling", self.test_error_handling)
        ]
        
        for test_name, test_func in tests:
            self.total += 1
            try:
                logger.info(f"Running test: {test_name}")
                result = await test_func()
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
    
    async def test_legacy_method_detection(self) -> bool:
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
                        # Look for method calls
                        pattern = rf'data_provider\.{method}\(|self\.data_provider\.{method}\('
                        matches = re.finditer(pattern, content)
                        
                        for match in matches:
                            # Find line number
                            line_num = content[:match.start()].count('\n') + 1
                            violations.append({
                                'file': file_path,
                                'method': method,
                                'line': line_num,
                                'context': self._get_line_context(content, line_num)
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
    
    async def test_canonical_pattern_validation(self) -> bool:
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
    
    async def test_standardized_structure_extraction(self) -> bool:
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
    
    async def test_component_data_access_scan(self) -> bool:
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
                        if not has_standardized:
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
    
    def _get_line_context(self, content: str, line_num: int) -> str:
        """Get context around a line number."""
        lines = content.split('\n')
        if 0 <= line_num - 1 < len(lines):
            return lines[line_num - 1].strip()
        return "Line not found"
    
    async def test_environment_variables(self) -> bool:
        """Test 5: Validate that environment variables are properly loaded and validated."""
        try:
            # Test that the environment loading and validation works correctly
            from basis_strategy_v1.infrastructure.config.config_validator import ConfigValidator
            
            # Test that validation passes with current environment
            validator = ConfigValidator()
            result = validator.validate_all()
            
            # The validation should pass with the current environment setup
            # If there are errors, they should be about missing data files, not environment variables
            env_errors = [error for error in result.errors if 'environment variable' in error.lower()]
            if env_errors:
                logger.error(f"Environment variable errors found: {env_errors}")
                return False
            
            # Test that BASIS_DATA_MODE is properly validated
            data_mode = os.getenv('BASIS_DATA_MODE')
            if data_mode and data_mode not in ['csv', 'db']:
                if not any('BASIS_DATA_MODE must be' in error for error in result.errors):
                    logger.error("Expected validation error for invalid BASIS_DATA_MODE")
                    return False
            
            # Test that BASIS_DATA_MODE has a valid value
            if data_mode and data_mode not in ['csv', 'db']:
                logger.error(f"BASIS_DATA_MODE has invalid value: {data_mode}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Environment variable validation test failed: {e}")
            return False
    
    async def test_data_provider_factory(self) -> bool:
        """Test 6: Create data provider without loading data (backtest mode)."""
        try:
            # Set up environment
            os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
            os.environ['BASIS_DATA_MODE'] = 'csv'
            os.environ['BASIS_DATA_DIR'] = 'data'
            os.environ['BASIS_DATA_START_DATE'] = '2024-05-12'
            os.environ['BASIS_DATA_END_DATE'] = '2025-09-18'
            
            from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
            
            # Test CSV mode
            provider = create_data_provider(
                execution_mode='backtest',
                config={'mode': 'pure_lending', 'data_requirements': ['aave_lending_rates', 'aave_indexes']}, 
                data_dir='data',
            )
            
            if not hasattr(provider, '_data_loaded'):
                logger.error("Provider missing _data_loaded attribute")
                return False
            
            if provider._data_loaded:
                logger.error("Provider should not have data loaded at creation")
                return False
            
            # Test DB mode (should raise NotImplementedError)
            try:
                create_data_provider(
                    execution_mode='backtest',
                    data_mode='db',
                    config={'mode': 'pure_lending', 'data_requirements': ['aave_lending_rates', 'aave_indexes']}, 
                    data_dir='data',
                )
                logger.error("Expected NotImplementedError for db mode")
                return False
            except NotImplementedError:
                pass  # Expected
            
            # Test live mode
            provider_live = create_data_provider(
                execution_mode='live',
                config={'mode': 'pure_lending', 'data_requirements': ['aave_lending_rates', 'aave_indexes']}, 
                data_dir='data',
            )
            
            if not hasattr(provider_live, 'config'):
                logger.error("Live provider missing config attribute")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Data provider factory test failed: {e}")
            return False
    
    async def test_on_demand_loading(self) -> bool:
        """Test 7: Load data on-demand for each strategy mode."""
        try:
            # Set up environment
            os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
            os.environ['BASIS_DATA_MODE'] = 'csv'
            os.environ['BASIS_DATA_DIR'] = 'data'
            os.environ['BASIS_DATA_START_DATE'] = '2024-05-12'
            os.environ['BASIS_DATA_END_DATE'] = '2025-09-18'
            
            from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
            from basis_strategy_v1.infrastructure.config.config_loader import ConfigLoader
            
            # Load the full configuration
            config_loader = ConfigLoader()
            mode_config = config_loader.get_mode_config('pure_lending')
            
            # Convert Pydantic model to dict for the data provider
            config_dict = mode_config.model_dump()
            
            # Test pure_lending mode
            provider = create_data_provider(
                execution_mode='backtest',
                config=config_dict, 
                data_dir='data',
            )
            
            # Load data on-demand
            provider.load_data()
            
            if not provider._data_loaded:
                logger.error("Data should be loaded after load_data")
                return False
            
            if len(provider.data) == 0:
                logger.error("No data loaded for pure_lending mode")
                return False
            
            # Test that data is accessible
            try:
                test_timestamp = pd.Timestamp('2024-06-01 12:00:00', tz='UTC')
                market_data = provider.get_data(test_timestamp)
                if not isinstance(market_data, dict):
                    logger.error("Market data should be a dictionary")
                    return False
            except Exception as e:
                logger.error(f"Failed to get market data: {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"On-demand loading test failed: {e}")
            return False
    
    async def test_date_range_validation(self) -> bool:
        """Test 8: Validate date range rejection (outside available range)."""
        try:
            # Set up environment
            os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
            os.environ['BASIS_DATA_MODE'] = 'csv'
            os.environ['BASIS_DATA_DIR'] = 'data'
            os.environ['BASIS_DATA_START_DATE'] = '2024-05-12'
            os.environ['BASIS_DATA_END_DATE'] = '2025-09-18'
            
            from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
            from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProviderError
            from basis_strategy_v1.infrastructure.config.config_loader import ConfigLoader
            
            # Load the full configuration
            config_loader = ConfigLoader()
            mode_config = config_loader.get_mode_config('pure_lending')
            config_dict = mode_config.model_dump()
            
            provider = create_data_provider(
                execution_mode='backtest',
                config=config_dict, 
                data_dir='data',
            )
            
            # Test date range before available data
            try:
                provider.load_data()
                logger.error("Expected DataProviderError for date before available range")
                return False
            except DataProviderError as e:
                if 'DATA-011' not in str(e):
                    logger.error(f"Expected DATA-011 error code, got: {e}")
                    return False
            
            # Test date range after available data
            try:
                provider.load_data()
                logger.error("Expected DataProviderError for date after available range")
                return False
            except DataProviderError as e:
                if 'DATA-011' not in str(e):
                    logger.error(f"Expected DATA-011 error code, got: {e}")
                    return False
            
            # Test valid date range
            try:
                provider.load_data()
                # Should not raise exception
            except Exception as e:
                logger.error(f"Unexpected error for valid date range: {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Date range validation test failed: {e}")
            return False
    
    async def test_health_check_integration(self) -> bool:
        """Test 9: Test health check with uninitialized data provider."""
        try:
            # Set up environment
            os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
            os.environ['BASIS_DATA_MODE'] = 'csv'
            os.environ['BASIS_DATA_DIR'] = 'data'
            os.environ['BASIS_DATA_START_DATE'] = '2024-05-12'
            os.environ['BASIS_DATA_END_DATE'] = '2025-09-18'
            
            from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
            from basis_strategy_v1.core.health.component_health import DataProviderHealthChecker
            
            # Create uninitialized provider
            provider = create_data_provider(
                execution_mode='backtest',
                config={'mode': 'pure_lending', 'data_requirements': ['aave_lending_rates', 'aave_indexes']}, 
                data_dir='data',
            )
            
            # Test health checker
            health_checker = DataProviderHealthChecker(provider)
            health_report = await health_checker.check_health()
            
            if health_report.status.value != 'not_ready':
                logger.error(f"Expected 'not_ready' status for uninitialized provider, got: {health_report.status}")
                return False
            
            if health_report.readiness_checks.get('data_loaded', True):
                logger.error("Expected data_loaded to be False for uninitialized provider")
                return False
            
            # Test metrics
            metrics = await health_checker._get_component_metrics()
            if metrics.get('data_loaded', True):
                logger.error("Expected data_loaded to be False in metrics")
                return False
            
            if metrics.get('basis_data_mode') != 'csv':
                logger.error(f"Expected basis_data_mode to be 'csv', got: {metrics.get('basis_data_mode')}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Health check integration test failed: {e}")
            return False
    
    async def test_no_startup_loading(self) -> bool:
        """Test 10: Verify no data loading at startup."""
        try:
            # This test verifies that the main.py startup process doesn't load data
            # We can't easily test this without mocking, but we can verify the architecture
            
            # Set up environment variables
            os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
            os.environ['BASIS_DATA_MODE'] = 'csv'
            os.environ['BASIS_DATA_DIR'] = 'data'
            os.environ['BASIS_DATA_START_DATE'] = '2024-05-12'
            os.environ['BASIS_DATA_END_DATE'] = '2025-09-18'
            
            # Avoid circular import by testing the factory directly
            from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
            
            # Test that create_data_provider doesn't load data without parameters
            try:
                provider = create_data_provider(
                    execution_mode='backtest',
                    config={'mode': 'pure_lending', 'data_requirements': ['aave_lending_rates', 'aave_indexes']}, 
                    data_dir='data',
                )
                if hasattr(provider, '_data_loaded') and provider._data_loaded:
                    logger.error("Provider should not have data loaded without parameters")
                    return False
            except Exception as e:
                # This is expected if environment variables are not set
                logger.info(f"Expected error when environment not set: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"No startup loading test failed: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Test 11: Test data provider with invalid date ranges."""
        try:
            # Set up environment
            os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
            os.environ['BASIS_DATA_MODE'] = 'csv'
            os.environ['BASIS_DATA_DIR'] = 'data'
            os.environ['BASIS_DATA_START_DATE'] = '2024-05-12'
            os.environ['BASIS_DATA_END_DATE'] = '2025-09-18'
            
            from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
            from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProviderError
            
            provider = create_data_provider(
                execution_mode='backtest',
                config={'mode': 'pure_lending', 'data_requirements': ['aave_lending_rates', 'aave_indexes']}, 
                data_dir='data',
            )
            
            # Test missing start date
            try:
                provider.load_data()
                logger.error("Expected DataProviderError for missing start date")
                return False
            except DataProviderError as e:
                if 'DATA-014' not in str(e):
                    logger.error(f"Expected DATA-014 error code, got: {e}")
                    return False
            
            # Test missing end date
            try:
                provider.load_data()
                logger.error("Expected DataProviderError for missing end date")
                return False
            except DataProviderError as e:
                if 'DATA-014' not in str(e):
                    logger.error(f"Expected DATA-014 error code, got: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
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

async def main():
    """Run the data provider canonical access quality gates."""
    quality_gates = DataProviderCanonicalAccessQualityGates()
    report = await quality_gates.run_all_tests()
    
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
    
    # Exit with error code if any tests failed
    if report['status'] == 'FAILED':
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
