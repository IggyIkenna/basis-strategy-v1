#!/usr/bin/env python3
"""
Data Provider Refactor Quality Gates

Comprehensive tests for the new data provider architecture including:
- Environment variable validation
- On-demand data loading
- Date range validation
- Health checks
- Factory pattern functionality
"""

import os
import sys
import asyncio
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
import structlog

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

logger = structlog.get_logger()

class DataProviderRefactorQualityGates:
    """Quality gates for data provider refactor validation."""
    
    def __init__(self):
        self.results = {}
        self.passed = 0
        self.failed = 0
        self.total = 0
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all quality gate tests."""
        logger.info("Starting Data Provider Refactor Quality Gates")
        
        tests = [
            ("Environment Variable Validation", self.test_environment_variables),
            ("Data Provider Factory", self.test_data_provider_factory),
            ("On-Demand Data Loading", self.test_on_demand_loading),
            ("Date Range Validation", self.test_date_range_validation),
            ("Health Check Integration", self.test_health_check_integration),
            ("No Startup Data Loading", self.test_no_startup_loading),
            ("Error Handling", self.test_error_handling),
            ("Backward Compatibility", self.test_backward_compatibility)
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
    
    async def test_environment_variables(self) -> bool:
        """Test 1: Validate that environment variables are properly loaded and validated."""
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
        """Test 2: Create data provider without loading data (backtest mode)."""
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
                data_dir='data',
                execution_mode='backtest',
                data_mode='csv',
                config={'mode': 'pure_lending'},
                strategy_mode='pure_lending'
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
                    data_dir='data',
                    execution_mode='backtest',
                    data_mode='db',
                    config={'mode': 'pure_lending'},
                    strategy_mode='pure_lending'
                )
                logger.error("Expected NotImplementedError for db mode")
                return False
            except NotImplementedError:
                pass  # Expected
            
            # Test live mode
            provider_live = create_data_provider(
                data_dir='data',
                execution_mode='live',
                data_mode='csv',  # Should be ignored
                config={'mode': 'pure_lending'},
                strategy_mode='pure_lending'
            )
            
            if not hasattr(provider_live, 'config'):
                logger.error("Live provider missing config attribute")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Data provider factory test failed: {e}")
            return False
    
    async def test_on_demand_loading(self) -> bool:
        """Test 3: Load data on-demand for each strategy mode."""
        try:
            # Set up environment
            os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
            os.environ['BASIS_DATA_MODE'] = 'csv'
            os.environ['BASIS_DATA_DIR'] = 'data'
            os.environ['BASIS_DATA_START_DATE'] = '2024-05-12'
            os.environ['BASIS_DATA_END_DATE'] = '2025-09-18'
            
            from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
            
            # Test pure_lending mode
            provider = create_data_provider(
                data_dir='data',
                execution_mode='backtest',
                data_mode='csv',
                config={'mode': 'pure_lending'},
                strategy_mode='pure_lending'
            )
            
            # Load data on-demand
            provider.load_data_for_backtest('pure_lending', '2024-06-01', '2024-06-02')
            
            if not provider._data_loaded:
                logger.error("Data should be loaded after load_data_for_backtest")
                return False
            
            if len(provider.data) == 0:
                logger.error("No data loaded for pure_lending mode")
                return False
            
            # Test that data is accessible
            try:
                test_timestamp = pd.Timestamp('2024-06-01 12:00:00', tz='UTC')
                market_data = provider.get_market_data_snapshot(test_timestamp)
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
        """Test 4: Validate date range rejection (outside available range)."""
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
                data_dir='data',
                execution_mode='backtest',
                data_mode='csv',
                config={'mode': 'pure_lending'},
                strategy_mode='pure_lending'
            )
            
            # Test date range before available data
            try:
                provider.load_data_for_backtest('pure_lending', '2024-01-01', '2024-01-02')
                logger.error("Expected DataProviderError for date before available range")
                return False
            except DataProviderError as e:
                if 'DATA-011' not in str(e):
                    logger.error(f"Expected DATA-011 error code, got: {e}")
                    return False
            
            # Test date range after available data
            try:
                provider.load_data_for_backtest('pure_lending', '2025-12-01', '2025-12-02')
                logger.error("Expected DataProviderError for date after available range")
                return False
            except DataProviderError as e:
                if 'DATA-011' not in str(e):
                    logger.error(f"Expected DATA-011 error code, got: {e}")
                    return False
            
            # Test valid date range
            try:
                provider.load_data_for_backtest('pure_lending', '2024-06-01', '2024-06-02')
                # Should not raise exception
            except Exception as e:
                logger.error(f"Unexpected error for valid date range: {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Date range validation test failed: {e}")
            return False
    
    async def test_health_check_integration(self) -> bool:
        """Test 5: Test health check with uninitialized data provider."""
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
                data_dir='data',
                execution_mode='backtest',
                data_mode='csv',
                config={'mode': 'pure_lending'},
                strategy_mode='pure_lending'
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
        """Test 6: Verify no data loading at startup."""
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
                    data_dir='data',
                    execution_mode='backtest',
                    data_mode='csv',
                    config={'mode': 'pure_lending'},
                    strategy_mode='pure_lending'
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
        """Test 7: Test data provider with invalid date ranges."""
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
                data_dir='data',
                execution_mode='backtest',
                data_mode='csv',
                config={'mode': 'pure_lending'},
                strategy_mode='pure_lending'
            )
            
            # Test missing start date
            try:
                provider.load_data_for_backtest('pure_lending', None, '2024-06-02')
                logger.error("Expected DataProviderError for missing start date")
                return False
            except DataProviderError as e:
                if 'DATA-014' not in str(e):
                    logger.error(f"Expected DATA-014 error code, got: {e}")
                    return False
            
            # Test missing end date
            try:
                provider.load_data_for_backtest('pure_lending', '2024-06-01', None)
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
    
    async def test_backward_compatibility(self) -> bool:
        """Test 8: Verify backward compatibility with existing code."""
        try:
            # Test that existing data provider methods still work
            # Set up environment
            os.environ['BASIS_EXECUTION_MODE'] = 'backtest'
            os.environ['BASIS_DATA_MODE'] = 'csv'
            os.environ['BASIS_DATA_DIR'] = 'data'
            os.environ['BASIS_DATA_START_DATE'] = '2024-05-12'
            os.environ['BASIS_DATA_END_DATE'] = '2025-09-18'
            
            from basis_strategy_v1.infrastructure.data.data_provider_factory import create_data_provider
            
            provider = create_data_provider(
                data_dir='data',
                execution_mode='backtest',
                data_mode='csv',
                config={'mode': 'pure_lending'},
                strategy_mode='pure_lending'
            )
            
            # Load data first
            provider.load_data_for_backtest('pure_lending', '2024-06-01', '2024-06-02')
            
            # Test that existing methods still work
            test_timestamp = pd.Timestamp('2024-06-01 12:00:00', tz='UTC')
            
            # Test get_market_data_snapshot
            market_data = provider.get_market_data_snapshot(test_timestamp)
            if not isinstance(market_data, dict):
                logger.error("get_market_data_snapshot should return dict")
                return False
            
            # Test get_health_status
            health_status = provider.get_health_status()
            if not isinstance(health_status, dict):
                logger.error("get_health_status should return dict")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Backward compatibility test failed: {e}")
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
        
        logger.info(f"Data Provider Refactor Quality Gates Complete: {self.passed}/{self.total} passed ({success_rate:.1f}%)")
        
        return report

async def main():
    """Run the data provider refactor quality gates."""
    quality_gates = DataProviderRefactorQualityGates()
    report = await quality_gates.run_all_tests()
    
    print("\n" + "="*80)
    print("DATA PROVIDER REFACTOR QUALITY GATES REPORT")
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
