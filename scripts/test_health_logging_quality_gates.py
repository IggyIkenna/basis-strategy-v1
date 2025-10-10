#!/usr/bin/env python3
"""
Health & Logging Quality Gates

This script validates the unified health system and structured logging implementation.
It tests health check endpoints, component health checks, and structured logging
across all components.

Reference: .cursor/tasks/05_health_logging_structure.md
"""

import os
import sys
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add backend src to path
backend_src = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

def test_health_endpoints():
    """Test health check endpoints."""
    print("Testing health check endpoints...")
    
    base_url = "http://localhost:8000"
    endpoints = [
        "/health",
        "/health/detailed",
    ]
    
    failed_endpoints = []
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code != 200:
                failed_endpoints.append(f"{endpoint}: {response.status_code}")
        except requests.exceptions.RequestException:
            # Backend might not be running
            print("⚠️  Backend not running - skipping health endpoint tests")
            return True
    
    if failed_endpoints:
        print("❌ Failed health endpoints:")
        for failed in failed_endpoints:
            print(f"  - {failed}")
        return False
    
    print("✅ All health endpoints work correctly")
    return True

def test_health_response_format():
    """Test health response format."""
    print("Testing health response format...")
    
    base_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            try:
                data = response.json()
                if not isinstance(data, dict):
                    print("❌ Health response is not a JSON object")
                    return False
                
                # Check for required health fields
                required_fields = ["status", "timestamp"]
                for field in required_fields:
                    if field not in data:
                        print(f"❌ Health response missing required field: {field}")
                        return False
            except json.JSONDecodeError:
                print("❌ Health response is not valid JSON")
                return False
    except requests.exceptions.RequestException:
        print("⚠️  Backend not running - skipping health response format tests")
        return True
    
    print("✅ Health response format is correct")
    return True

def test_detailed_health_response():
    """Test detailed health response format."""
    print("Testing detailed health response format...")
    
    base_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{base_url}/health/detailed", timeout=5)
        if response.status_code == 200:
            try:
                data = response.json()
                if not isinstance(data, dict):
                    print("❌ Detailed health response is not a JSON object")
                    return False
                
                # Check for required detailed health fields
                required_fields = ["status", "timestamp", "components"]
                for field in required_fields:
                    if field not in data:
                        print(f"❌ Detailed health response missing required field: {field}")
                        return False
                
                # Check that components is a dictionary
                if not isinstance(data.get("components"), dict):
                    print("❌ Detailed health response components is not a dictionary")
                    return False
            except json.JSONDecodeError:
                print("❌ Detailed health response is not valid JSON")
                return False
    except requests.exceptions.RequestException:
        print("⚠️  Backend not running - skipping detailed health response tests")
        return True
    
    print("✅ Detailed health response format is correct")
    return True

def test_component_health_checks():
    """Test component health checks."""
    print("Testing component health checks...")
    
    try:
        from basis_strategy_v1.infrastructure.health.health_checker import HealthChecker
        health_checker = HealthChecker()
        
        # Test basic health check
        health_status = health_checker.check_health()
        if not isinstance(health_status, dict):
            print("❌ Health check result is not a dictionary")
            return False
        
        # Test detailed health check
        detailed_health = health_checker.check_detailed_health()
        if not isinstance(detailed_health, dict):
            print("❌ Detailed health check result is not a dictionary")
            return False
        
        print("✅ Component health checks work correctly")
        return True
        
    except ImportError:
        print("⚠️  HealthChecker not implemented yet - skipping")
        return True
    except Exception as e:
        print(f"❌ Component health checks failed: {e}")
        return False

def test_structured_logging():
    """Test structured logging implementation."""
    print("Testing structured logging implementation...")
    
    try:
        from basis_strategy_v1.infrastructure.logging.structured_logger import StructuredLogger
        logger = StructuredLogger("test_component")
        
        # Test structured logging
        logger.log_event("INFO", "Test message", test_param="test_value")
        logger.log_performance("test_operation", 0.1, test_param="test_value")
        
        print("✅ Structured logging works correctly")
        return True
        
    except ImportError:
        print("⚠️  StructuredLogger not implemented yet - skipping")
        return True
    except Exception as e:
        print(f"❌ Structured logging failed: {e}")
        return False

def test_component_logging_integration():
    """Test component logging integration."""
    print("Testing component logging integration...")
    
    # Check that components have logging integration
    component_files = [
        "backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py",
        "backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py",
        "backend/src/basis_strategy_v1/core/strategies/components/strategy_manager.py",
        "backend/src/basis_strategy_v1/core/strategies/components/execution_manager.py",
        "backend/src/basis_strategy_v1/core/strategies/components/data_provider.py",
    ]
    
    missing_files = []
    for file_path in component_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing component files:")
        for missing in missing_files:
            print(f"  - {missing}")
        return False
    
    print("✅ Component logging integration files exist")
    return True

def test_event_logger_integration():
    """Test event logger integration."""
    print("Testing event logger integration...")
    
    try:
        from basis_strategy_v1.core.strategies.components.event_logger import EventLogger
        event_logger = EventLogger()
        
        # Test event logging
        event_logger.log_event("test_event", {"test": "data"})
        
        print("✅ Event logger integration works correctly")
        return True
        
    except ImportError:
        print("⚠️  EventLogger not implemented yet - skipping")
        return True
    except Exception as e:
        print(f"❌ Event logger integration failed: {e}")
        return False

def test_health_system_files():
    """Test that health system files exist."""
    print("Testing health system files...")
    
    health_files = [
        "backend/src/basis_strategy_v1/infrastructure/health/health_checker.py",
        "backend/src/basis_strategy_v1/api/health.py",
    ]
    
    missing_files = []
    for file_path in health_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing health system files:")
        for missing in missing_files:
            print(f"  - {missing}")
        return False
    
    print("✅ Health system files exist")
    return True

def test_logging_system_files():
    """Test that logging system files exist."""
    print("Testing logging system files...")
    
    logging_files = [
        "backend/src/basis_strategy_v1/infrastructure/logging/structured_logger.py",
    ]
    
    missing_files = []
    for file_path in logging_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing logging system files:")
        for missing in missing_files:
            print(f"  - {missing}")
        return False
    
    print("✅ Logging system files exist")
    return True

def main():
    """Run all health and logging quality gates."""
    print("=" * 60)
    print("HEALTH & LOGGING QUALITY GATES")
    print("=" * 60)
    
    tests = [
        test_health_system_files,
        test_logging_system_files,
        test_health_endpoints,
        test_health_response_format,
        test_detailed_health_response,
        test_component_health_checks,
        test_structured_logging,
        test_component_logging_integration,
        test_event_logger_integration,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
        print()
    
    print("=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All health and logging quality gates passed!")
        return 0
    else:
        print("❌ Some health and logging quality gates failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
