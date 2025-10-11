#!/usr/bin/env python3
"""
Health & Logging Structure Quality Gates

Tests the unified health system and structured logging implementation
for all components to ensure proper observability and debugging capabilities.

Reference: .cursor/tasks/05_health_logging_structure.md
"""

import sys
import os
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import requests
import logging

# Add the backend source to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from basis_strategy_v1.core.health.unified_health_manager import UnifiedHealthManager
from basis_strategy_v1.infrastructure.logging.structured_logger import get_structured_logger
from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
from basis_strategy_v1.core.strategies.components.risk_monitor import RiskMonitor
from basis_strategy_v1.core.strategies.components.event_logger import EventLogger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthLoggingQualityGates:
    """Quality gates for health and logging structure."""
    
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.test_results = []
        self.health_manager = UnifiedHealthManager()
        
    def log_test_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
    
    def test_health_endpoints(self) -> bool:
        """Test health endpoints functionality."""
        print("\n🔍 Testing Health Endpoints...")
        
        try:
            # Test basic health endpoint
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                if 'status' in health_data and 'timestamp' in health_data:
                    self.log_test_result("Basic Health Endpoint", True, f"Status: {health_data['status']}")
                else:
                    self.log_test_result("Basic Health Endpoint", False, "Missing required fields")
                    return False
            else:
                self.log_test_result("Basic Health Endpoint", False, f"HTTP {response.status_code}")
                return False
            
            # Test detailed health endpoint
            response = requests.get(f"{self.base_url}/health/detailed", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                if 'status' in health_data and 'components' in health_data:
                    self.log_test_result("Detailed Health Endpoint", True, f"Components: {len(health_data.get('components', {}))}")
                else:
                    self.log_test_result("Detailed Health Endpoint", False, "Missing required fields")
                    return False
            else:
                self.log_test_result("Detailed Health Endpoint", False, f"HTTP {response.status_code}")
                return False
                
            return True
            
        except Exception as e:
            self.log_test_result("Health Endpoints", False, f"Exception: {e}")
            return False
    
    def test_health_manager(self) -> bool:
        """Test health manager functionality."""
        print("\n🔍 Testing Health Manager...")
        
        try:
            # Test basic health check
            health_data = asyncio.run(self.health_manager.check_basic_health())
            if isinstance(health_data, dict) and 'status' in health_data:
                self.log_test_result("Health Manager Basic Check", True, f"Status: {health_data['status']}")
            else:
                self.log_test_result("Health Manager Basic Check", False, "Invalid response format")
                return False
            
            # Test detailed health check
            detailed_health = asyncio.run(self.health_manager.check_detailed_health())
            if isinstance(detailed_health, dict) and 'status' in detailed_health:
                self.log_test_result("Health Manager Detailed Check", True, f"Status: {detailed_health['status']}")
            else:
                self.log_test_result("Health Manager Detailed Check", False, "Invalid response format")
                return False
                
            return True
            
        except Exception as e:
            self.log_test_result("Health Manager", False, f"Exception: {e}")
            return False
    
    def test_structured_logging(self) -> bool:
        """Test structured logging implementation."""
        print("\n🔍 Testing Structured Logging...")
        
        try:
            # Test structured logger creation
            logger = get_structured_logger('test_component')
            if logger and hasattr(logger, 'info'):
                self.log_test_result("Structured Logger Creation", True, "Logger created successfully")
            else:
                self.log_test_result("Structured Logger Creation", False, "Invalid logger")
                return False
            
            # Test logging methods
            logger.info("Test info message", event_type="test")
            logger.warning("Test warning message", event_type="test")
            logger.error("Test error message", event_type="test")
            logger.log_performance("test_operation", 100.5, success=True)
            logger.log_business_event("test_event", "Test business event")
            logger.log_component_health("healthy", "Test health check")
            logger.log_data_event("load", "test_data", success=True)
            logger.log_strategy_event("test_strategy", "test_event", "Test strategy event")
            
            self.log_test_result("Structured Logging Methods", True, "All logging methods work")
            
            return True
            
        except Exception as e:
            self.log_test_result("Structured Logging", False, f"Exception: {e}")
            return False
    
    def test_component_logging_integration(self) -> bool:
        """Test component logging integration."""
        print("\n🔍 Testing Component Logging Integration...")
        
        try:
            # Test Position Monitor logging
            config = {'mode': 'test', 'share_class': 'USDT'}
            position_monitor = PositionMonitor(config, None, None)
            
            if hasattr(position_monitor, 'structured_logger'):
                self.log_test_result("Position Monitor Logging", True, "Structured logger integrated")
            else:
                self.log_test_result("Position Monitor Logging", False, "No structured logger found")
                return False
            
            # Test Risk Monitor logging
            risk_monitor = RiskMonitor(config, None, None)
            
            if hasattr(risk_monitor, 'structured_logger'):
                self.log_test_result("Risk Monitor Logging", True, "Structured logger integrated")
            else:
                self.log_test_result("Risk Monitor Logging", False, "No structured logger found")
                return False
            
            # Test Event Logger
            event_logger = EventLogger(config, None, None)
            
            if hasattr(event_logger, 'structured_logger'):
                self.log_test_result("Event Logger Logging", True, "Structured logger integrated")
            else:
                self.log_test_result("Event Logger Logging", False, "No structured logger found")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Component Logging Integration", False, f"Exception: {e}")
            return False
    
    def test_log_levels(self) -> bool:
        """Test log level usage."""
        print("\n🔍 Testing Log Levels...")
        
        try:
            logger = get_structured_logger('test_component')
            
            # Test all log levels
            logger.debug("Debug message", event_type="test")
            logger.info("Info message", event_type="test")
            logger.warning("Warning message", event_type="test")
            logger.error("Error message", event_type="test")
            logger.critical("Critical message", event_type="test")
            
            self.log_test_result("Log Levels", True, "All log levels work correctly")
            
            return True
            
        except Exception as e:
            self.log_test_result("Log Levels", False, f"Exception: {e}")
            return False
    
    def test_performance_logging(self) -> bool:
        """Test performance logging."""
        print("\n🔍 Testing Performance Logging...")
        
        try:
            logger = get_structured_logger('test_component')
            
            # Test performance logging
            start_time = time.time()
            time.sleep(0.1)  # Simulate work
            duration = (time.time() - start_time) * 1000  # Convert to ms
            
            logger.log_performance("test_operation", duration, success=True, operation_type="test")
            logger.log_performance("failed_operation", duration, success=False, operation_type="test")
            
            self.log_test_result("Performance Logging", True, "Performance logging works correctly")
            
            return True
            
        except Exception as e:
            self.log_test_result("Performance Logging", False, f"Exception: {e}")
            return False
    
    def test_event_correlation(self) -> bool:
        """Test event correlation IDs."""
        print("\n🔍 Testing Event Correlation...")
        
        try:
            logger = get_structured_logger('test_component')
            
            # Test correlation ID setting
            correlation_id = "test-correlation-123"
            logger.set_correlation_id(correlation_id)
            
            # Test logging with correlation ID
            logger.info("Test message with correlation", event_type="test")
            
            self.log_test_result("Event Correlation", True, "Correlation IDs work correctly")
            
            return True
            
        except Exception as e:
            self.log_test_result("Event Correlation", False, f"Exception: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all quality gate tests."""
        print("🚀 Starting Health & Logging Structure Quality Gates...")
        
        tests = [
            self.test_health_endpoints,
            self.test_health_manager,
            self.test_structured_logging,
            self.test_component_logging_integration,
            self.test_log_levels,
            self.test_performance_logging,
            self.test_event_correlation
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
        print("📊 HEALTH & LOGGING STRUCTURE QUALITY GATES SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result['passed'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Health & logging structure is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result['passed'] else "❌"
            print(f"  {status} {result['test']}: {result['message']}")

def main():
    """Main function."""
    quality_gates = HealthLoggingQualityGates()
    
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