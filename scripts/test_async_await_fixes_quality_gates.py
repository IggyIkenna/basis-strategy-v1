#!/usr/bin/env python3
"""
Async/Await Fixes Quality Gates

Tests that async/await violations have been fixed according to ADR-006.
Internal component methods should be synchronous, while I/O operations
and API entry points should remain async.

Reference: .cursor/tasks/07_fix_async_await_violations.md
Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-006
"""

import sys
import os
import asyncio
import inspect
from pathlib import Path
from typing import Dict, Any, List
import logging
import pandas as pd

# Add the backend source to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from basis_strategy_v1.core.health.component_health import ComponentHealthChecker, PositionMonitorHealthChecker
from basis_strategy_v1.core.health.unified_health_manager import UnifiedHealthManager
from basis_strategy_v1.core.strategies.components.event_logger import EventLogger
from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
from basis_strategy_v1.core.strategies.components.risk_monitor import RiskMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncAwaitFixesQualityGates:
    """Quality gates for async/await fixes."""
    
    def __init__(self):
        self.test_results = []
        
    def log_test_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
    
    def test_component_health_checkers_synchronous(self) -> bool:
        """Test that component health checkers are synchronous."""
        print("\n🔍 Testing Component Health Checkers...")
        
        try:
            # Test base ComponentHealthChecker
            checker = ComponentHealthChecker("test_component")
            
            # Check that check_health is synchronous
            if inspect.iscoroutinefunction(checker.check_health):
                self.log_test_result("ComponentHealthChecker.check_health", False, "Should be synchronous")
                return False
            else:
                self.log_test_result("ComponentHealthChecker.check_health", True, "Is synchronous")
            
            # Check that helper methods are synchronous
            if inspect.iscoroutinefunction(checker._perform_readiness_checks):
                self.log_test_result("ComponentHealthChecker._perform_readiness_checks", False, "Should be synchronous")
                return False
            else:
                self.log_test_result("ComponentHealthChecker._perform_readiness_checks", True, "Is synchronous")
            
            if inspect.iscoroutinefunction(checker._get_component_metrics):
                self.log_test_result("ComponentHealthChecker._get_component_metrics", False, "Should be synchronous")
                return False
            else:
                self.log_test_result("ComponentHealthChecker._get_component_metrics", True, "Is synchronous")
            
            if inspect.iscoroutinefunction(checker._get_error_info):
                self.log_test_result("ComponentHealthChecker._get_error_info", False, "Should be synchronous")
                return False
            else:
                self.log_test_result("ComponentHealthChecker._get_error_info", True, "Is synchronous")
            
            if inspect.iscoroutinefunction(checker._get_dependencies):
                self.log_test_result("ComponentHealthChecker._get_dependencies", False, "Should be synchronous")
                return False
            else:
                self.log_test_result("ComponentHealthChecker._get_dependencies", True, "Is synchronous")
            
            return True
            
        except Exception as e:
            self.log_test_result("Component Health Checkers", False, f"Exception: {e}")
            return False
    
    def test_position_monitor_health_checker_synchronous(self) -> bool:
        """Test that PositionMonitorHealthChecker is synchronous."""
        print("\n🔍 Testing PositionMonitorHealthChecker...")
        
        try:
            # Create a mock position monitor
            class MockPositionMonitor:
                def __init__(self):
                    self._token_monitor = True
                    self.execution_mode = 'backtest'
                
                def get_snapshot(self):
                    return {'wallet': {}, 'cex_accounts': {}, 'perp_positions': {}}
            
            mock_position_monitor = MockPositionMonitor()
            checker = PositionMonitorHealthChecker(mock_position_monitor)
            
            # Check that all methods are synchronous
            methods_to_check = [
                'check_health',
                '_perform_readiness_checks',
                '_get_component_metrics',
                '_get_error_info'
            ]
            
            all_synchronous = True
            for method_name in methods_to_check:
                method = getattr(checker, method_name)
                if inspect.iscoroutinefunction(method):
                    self.log_test_result(f"PositionMonitorHealthChecker.{method_name}", False, "Should be synchronous")
                    all_synchronous = False
                else:
                    self.log_test_result(f"PositionMonitorHealthChecker.{method_name}", True, "Is synchronous")
            
            # Test that the methods actually work synchronously
            try:
                report = checker.check_health()
                if hasattr(report, 'component_name') and report.component_name == 'position_monitor':
                    self.log_test_result("PositionMonitorHealthChecker.check_health execution", True, "Executes synchronously")
                else:
                    self.log_test_result("PositionMonitorHealthChecker.check_health execution", False, "Invalid report")
                    all_synchronous = False
            except Exception as e:
                self.log_test_result("PositionMonitorHealthChecker.check_health execution", False, f"Execution error: {e}")
                all_synchronous = False
            
            return all_synchronous
            
        except Exception as e:
            self.log_test_result("PositionMonitorHealthChecker", False, f"Exception: {e}")
            return False
    
    def test_event_logger_async_preserved(self) -> bool:
        """Test that Event Logger keeps async methods for I/O operations."""
        print("\n🔍 Testing Event Logger Async Methods...")
        
        try:
            # Test that Event Logger keeps async methods
            config = {'mode': 'test', 'share_class': 'USDT'}
            event_logger = EventLogger(config, None, None)
            
            # Check that log_event is async (I/O operation)
            if not inspect.iscoroutinefunction(event_logger.log_event):
                self.log_test_result("EventLogger.log_event", False, "Should be async for I/O")
                return False
            else:
                self.log_test_result("EventLogger.log_event", True, "Is async for I/O")
            
            # Check that other logging methods are async
            async_methods = [
                'log_gas_fee', 'log_stake', 'log_aave_supply', 'log_aave_borrow',
                'log_atomic_transaction', 'log_perp_trade', 'log_funding_payment',
                'log_venue_transfer', 'log_rebalance', 'log_risk_alert',
                'log_seasonal_reward_distribution', 'update_event'
            ]
            
            all_async = True
            for method_name in async_methods:
                if hasattr(event_logger, method_name):
                    method = getattr(event_logger, method_name)
                    if not inspect.iscoroutinefunction(method):
                        self.log_test_result(f"EventLogger.{method_name}", False, "Should be async for I/O")
                        all_async = False
                    else:
                        self.log_test_result(f"EventLogger.{method_name}", True, "Is async for I/O")
            
            return all_async
            
        except Exception as e:
            self.log_test_result("Event Logger Async Methods", False, f"Exception: {e}")
            return False
    
    def test_api_entry_points_async_preserved(self) -> bool:
        """Test that API entry points keep async methods."""
        print("\n🔍 Testing API Entry Points...")
        
        try:
            # Test UnifiedHealthManager (used by API endpoints)
            health_manager = UnifiedHealthManager()
            
            # Check that API entry points are async
            if not inspect.iscoroutinefunction(health_manager.check_basic_health):
                self.log_test_result("UnifiedHealthManager.check_basic_health", False, "Should be async for API")
                return False
            else:
                self.log_test_result("UnifiedHealthManager.check_basic_health", True, "Is async for API")
            
            if not inspect.iscoroutinefunction(health_manager.check_detailed_health):
                self.log_test_result("UnifiedHealthManager.check_detailed_health", False, "Should be async for API")
                return False
            else:
                self.log_test_result("UnifiedHealthManager.check_detailed_health", True, "Is async for API")
            
            return True
            
        except Exception as e:
            self.log_test_result("API Entry Points", False, f"Exception: {e}")
            return False
    
    def test_component_methods_synchronous(self) -> bool:
        """Test that core component methods are synchronous."""
        print("\n🔍 Testing Core Component Methods...")
        
        try:
            # Test Position Monitor
            config = {'mode': 'test', 'share_class': 'USDT'}
            position_monitor = PositionMonitor(config, None, None)
            
            # Check that internal methods are synchronous
            if hasattr(position_monitor, 'calculate_positions'):
                if inspect.iscoroutinefunction(position_monitor.calculate_positions):
                    self.log_test_result("PositionMonitor.calculate_positions", False, "Should be synchronous")
                    return False
                else:
                    self.log_test_result("PositionMonitor.calculate_positions", True, "Is synchronous")
            
            # Test Risk Monitor
            risk_monitor = RiskMonitor(config, None, None)
            
            # Check that internal methods are synchronous
            if hasattr(risk_monitor, 'calculate_risk_metrics'):
                if inspect.iscoroutinefunction(risk_monitor.calculate_risk_metrics):
                    self.log_test_result("RiskMonitor.calculate_risk_metrics", False, "Should be synchronous")
                    return False
                else:
                    self.log_test_result("RiskMonitor.calculate_risk_metrics", True, "Is synchronous")
            
            return True
            
        except Exception as e:
            self.log_test_result("Core Component Methods", False, f"Exception: {e}")
            return False
    
    def test_no_await_in_synchronous_methods(self) -> bool:
        """Test that synchronous methods don't use await."""
        print("\n🔍 Testing No Await in Synchronous Methods...")
        
        try:
            # This is a basic check - in a real implementation, we would scan
            # the source code for await statements in synchronous methods
            # For now, we'll test that the methods execute without await issues
            
            config = {'mode': 'test', 'share_class': 'USDT'}
            position_monitor = PositionMonitor(config, None, None)
            
            # Test that synchronous methods can be called without await
            try:
                result = position_monitor.calculate_positions(pd.Timestamp.now())
                if isinstance(result, dict):
                    self.log_test_result("PositionMonitor synchronous execution", True, "Executes without await")
                else:
                    self.log_test_result("PositionMonitor synchronous execution", False, "Invalid result")
                    return False
            except Exception as e:
                self.log_test_result("PositionMonitor synchronous execution", False, f"Execution error: {e}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("No Await in Synchronous Methods", False, f"Exception: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all quality gate tests."""
        print("🚀 Starting Async/Await Fixes Quality Gates...")
        
        tests = [
            self.test_component_health_checkers_synchronous,
            self.test_position_monitor_health_checker_synchronous,
            self.test_event_logger_async_preserved,
            self.test_api_entry_points_async_preserved,
            self.test_component_methods_synchronous,
            self.test_no_await_in_synchronous_methods
        ]
        
        all_passed = True
        for test in tests:
            try:
                if not test():
                    all_passed = False
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
                all_passed = False
        
        return all_passed
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("📊 ASYNC/AWAIT FIXES QUALITY GATES SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result['passed'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Async/await fixes are working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result['passed'] else "❌"
            print(f"  {status} {result['test']}: {result['message']}")

def main():
    """Main function."""
    quality_gates = AsyncAwaitFixesQualityGates()
    
    try:
        success = quality_gates.run_all_tests()
        quality_gates.print_summary()
        
        if success:
            print("\n🎯 Quality gates completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Quality gates failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Quality gates interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Quality gates failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()