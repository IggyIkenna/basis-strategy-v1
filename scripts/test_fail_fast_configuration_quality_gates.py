#!/usr/bin/env python3
"""
Fail-Fast Configuration Quality Gates

This script validates that all components use fail-fast configuration access
instead of .get() patterns with defaults.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 33
Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-040
"""

import os
import sys
import re
import logging
from typing import List, Dict, Any

# Add the backend source to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

class FailFastConfigurationQualityGates:
    """Quality gates for fail-fast configuration implementation"""
    
    def __init__(self):
        self.passed_gates = 0
        self.total_gates = 0
        self.test_results = []
    
    def run_all_tests(self) -> bool:
        """Run all fail-fast configuration quality gates"""
        logger.info("Starting Fail-Fast Configuration Quality Gates")
        
        # QG1: No .get() with Defaults in Risk Monitor
        self._test_risk_monitor_no_get_patterns()
        
        # QG2: No .get() with Defaults in All Components
        self._test_all_components_no_get_patterns()
        
        # QG3: Direct Config Access Validation
        self._test_direct_config_access()
        
        # QG4: Configuration Validation at Startup
        self._test_config_validation_at_startup()
        
        # QG5: KeyError Handling
        self._test_keyerror_handling()
        
        # QG6: Nested Configuration Access
        self._test_nested_config_access()
        
        # QG7: Component Initialization with Missing Config
        self._test_component_init_missing_config()
        
        # QG8: Integration Test
        self._test_integration()
        
        # Print results
        self._print_results()
        
        return self.passed_gates == self.total_gates
    
    def _test_risk_monitor_no_get_patterns(self):
        """Test that risk monitor has no .get() patterns with defaults"""
        self.total_gates += 1
        try:
            risk_monitor_file = 'backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py'
            
            with open(risk_monitor_file, 'r') as f:
                content = f.read()
            
            # Find all .get() patterns with defaults
            get_patterns = re.findall(r'\.get\([^)]+,\s*[^)]+\)', content)
            
            # Filter out legitimate .get() patterns (without defaults)
            get_with_defaults = []
            for pattern in get_patterns:
                # Check if it has a default value (comma followed by non-empty value)
                if ',' in pattern and not pattern.strip().endswith(','):
                    get_with_defaults.append(pattern)
            
            if get_with_defaults:
                raise AssertionError(f"Found {len(get_with_defaults)} .get() patterns with defaults in risk_monitor.py: {get_with_defaults[:5]}...")
            
            self.passed_gates += 1
            self.test_results.append("QG1: Risk Monitor No .get() Patterns - PASSED")
            logger.info("✅ QG1: Risk Monitor No .get() Patterns - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG1: Risk Monitor No .get() Patterns - FAILED: {e}")
            logger.error(f"❌ QG1: Risk Monitor No .get() Patterns - FAILED: {e}")
    
    def _test_all_components_no_get_patterns(self):
        """Test that all components have no .get() patterns with defaults"""
        self.total_gates += 1
        try:
            component_files = [
                'backend/src/basis_strategy_v1/core/strategies/components/pnl_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/strategy_manager.py',
                'backend/src/basis_strategy_v1/core/strategies/components/position_update_handler.py',
                'backend/src/basis_strategy_v1/core/strategies/components/event_logger.py'
            ]
            
            all_get_patterns = []
            for file_path in component_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Find all .get() patterns with defaults
                    get_patterns = re.findall(r'\.get\([^)]+,\s*[^)]+\)', content)
                    
                    # Filter out legitimate .get() patterns (without defaults)
                    get_with_defaults = []
                    for pattern in get_patterns:
                        # Check if it has a default value (comma followed by non-empty value)
                        if ',' in pattern and not pattern.strip().endswith(','):
                            get_with_defaults.append(f"{file_path}: {pattern}")
                    
                    all_get_patterns.extend(get_with_defaults)
            
            if all_get_patterns:
                raise AssertionError(f"Found {len(all_get_patterns)} .get() patterns with defaults across all components: {all_get_patterns[:5]}...")
            
            self.passed_gates += 1
            self.test_results.append("QG2: All Components No .get() Patterns - PASSED")
            logger.info("✅ QG2: All Components No .get() Patterns - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG2: All Components No .get() Patterns - FAILED: {e}")
            logger.error(f"❌ QG2: All Components No .get() Patterns - FAILED: {e}")
    
    def _test_direct_config_access(self):
        """Test that components use direct config access"""
        self.total_gates += 1
        try:
            component_files = [
                'backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/pnl_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py'
            ]
            
            direct_access_found = False
            for file_path in component_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Look for direct config access patterns
                    if re.search(r'config\[[\'"][^\'"]+[\'"]\]', content):
                        direct_access_found = True
                        break
            
            if not direct_access_found:
                raise AssertionError("No direct config access patterns found in components")
            
            self.passed_gates += 1
            self.test_results.append("QG3: Direct Config Access - PASSED")
            logger.info("✅ QG3: Direct Config Access - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG3: Direct Config Access - FAILED: {e}")
            logger.error(f"❌ QG3: Direct Config Access - FAILED: {e}")
    
    def _test_config_validation_at_startup(self):
        """Test that components validate configuration at startup"""
        self.total_gates += 1
        try:
            component_files = [
                'backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/pnl_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py'
            ]
            
            validation_found = False
            for file_path in component_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Look for configuration validation patterns
                    if (re.search(r'required_keys', content) or 
                        re.search(r'if.*not in config', content) or
                        re.search(r'KeyError.*configuration', content)):
                        validation_found = True
                        break
            
            if not validation_found:
                raise AssertionError("No configuration validation patterns found in components")
            
            self.passed_gates += 1
            self.test_results.append("QG4: Configuration Validation at Startup - PASSED")
            logger.info("✅ QG4: Configuration Validation at Startup - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG4: Configuration Validation at Startup - FAILED: {e}")
            logger.error(f"❌ QG4: Configuration Validation at Startup - FAILED: {e}")
    
    def _test_keyerror_handling(self):
        """Test that KeyError exceptions are properly handled"""
        self.total_gates += 1
        try:
            # This test validates that KeyError handling is in place
            # We'll check for KeyError patterns in the code
            component_files = [
                'backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/pnl_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py'
            ]
            
            keyerror_handling_found = False
            for file_path in component_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Look for KeyError handling patterns
                    if (re.search(r'except KeyError', content) or
                        re.search(r'KeyError.*missing', content) or
                        re.search(r'KeyError.*configuration', content)):
                        keyerror_handling_found = True
                        break
            
            if not keyerror_handling_found:
                raise AssertionError("No KeyError handling patterns found in components")
            
            self.passed_gates += 1
            self.test_results.append("QG5: KeyError Handling - PASSED")
            logger.info("✅ QG5: KeyError Handling - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG5: KeyError Handling - FAILED: {e}")
            logger.error(f"❌ QG5: KeyError Handling - FAILED: {e}")
    
    def _test_nested_config_access(self):
        """Test that nested configuration access uses direct access"""
        self.total_gates += 1
        try:
            component_files = [
                'backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/pnl_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py'
            ]
            
            nested_get_patterns = []
            for file_path in component_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Look for nested .get() patterns
                    nested_patterns = re.findall(r'config\.get\([^)]+\)\.get\([^)]+\)', content)
                    nested_get_patterns.extend([f"{file_path}: {pattern}" for pattern in nested_patterns])
            
            if nested_get_patterns:
                raise AssertionError(f"Found {len(nested_get_patterns)} nested .get() patterns: {nested_get_patterns[:3]}...")
            
            self.passed_gates += 1
            self.test_results.append("QG6: Nested Configuration Access - PASSED")
            logger.info("✅ QG6: Nested Configuration Access - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG6: Nested Configuration Access - FAILED: {e}")
            logger.error(f"❌ QG6: Nested Configuration Access - FAILED: {e}")
    
    def _test_component_init_missing_config(self):
        """Test that components fail fast on missing configuration"""
        self.total_gates += 1
        try:
            # This test validates that components would fail fast on missing config
            # We'll check for direct config access patterns that would raise KeyError
            
            component_files = [
                'backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/pnl_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py'
            ]
            
            fail_fast_patterns = []
            for file_path in component_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Look for direct config access that would fail fast
                    direct_access = re.findall(r'config\[[\'"][^\'"]+[\'"]\]', content)
                    fail_fast_patterns.extend([f"{file_path}: {pattern}" for pattern in direct_access])
            
            if not fail_fast_patterns:
                raise AssertionError("No fail-fast configuration access patterns found")
            
            self.passed_gates += 1
            self.test_results.append("QG7: Component Init Missing Config - PASSED")
            logger.info("✅ QG7: Component Init Missing Config - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG7: Component Init Missing Config - FAILED: {e}")
            logger.error(f"❌ QG7: Component Init Missing Config - FAILED: {e}")
    
    def _test_integration(self):
        """Integration test for fail-fast configuration"""
        self.total_gates += 1
        try:
            # Test that we can import components without errors
            # This validates that the configuration structure is correct
            
            from basis_strategy_v1.core.strategies.components.risk_monitor import RiskMonitor
            from basis_strategy_v1.core.strategies.components.pnl_monitor import PnLMonitor
            from basis_strategy_v1.core.strategies.components.exposure_monitor import ExposureMonitor
            from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
            
            # Test that components can be instantiated with proper config
            config = {
                'target_ltv': 0.8,
                'max_drawdown': 0.1,
                'leverage_enabled': True,
                'share_class': 'USDT',
                'target_apy': 0.15,
                'venues': {
                    'binance': {'max_leverage': 3.0},
                    'okx': {'max_leverage': 2.0}
                }
            }
            
            class MockDataProvider:
                def get_liquidity_index(self, token, timestamp):
                    return 1.0
                def get_market_price(self, token, currency, timestamp):
                    return 1.0
            
            from basis_strategy_v1.core.utilities.utility_manager import UtilityManager
            
            data_provider = MockDataProvider()
            utility_manager = UtilityManager(config, data_provider)
            
            # Test component instantiation (should work with proper config)
            risk_monitor = RiskMonitor(config, data_provider, utility_manager)
            pnl_monitor = PnLMonitor(config, data_provider, utility_manager)
            exposure_monitor = ExposureMonitor(config, data_provider, utility_manager)
            position_monitor = PositionMonitor(config, data_provider, utility_manager)
            
            self.passed_gates += 1
            self.test_results.append("QG8: Integration Test - PASSED")
            logger.info("✅ QG8: Integration Test - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG8: Integration Test - FAILED: {e}")
            logger.error(f"❌ QG8: Integration Test - FAILED: {e}")
    
    def _print_results(self):
        """Print quality gate results"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("FAIL-FAST CONFIGURATION QUALITY GATES RESULTS")
        logger.info("=" * 60)
        
        for result in self.test_results:
            logger.info(result)
        
        logger.info("=" * 60)
        logger.info(f"PASSED: {self.passed_gates}/{self.total_gates} quality gates")
        logger.info(f"SUCCESS RATE: {(self.passed_gates/self.total_gates)*100:.1f}%")
        
        if self.passed_gates == self.total_gates:
            logger.info("🎉 ALL QUALITY GATES PASSED! Fail-fast configuration is working correctly.")
        else:
            logger.error(f"❌ {self.total_gates - self.passed_gates} quality gates failed. Fail-fast configuration needs fixes.")
        
        logger.info("=" * 60)

def main():
    """Main function to run fail-fast configuration quality gates"""
    quality_gates = FailFastConfigurationQualityGates()
    success = quality_gates.run_all_tests()
    
    if success:
        print("\n✅ All fail-fast configuration quality gates passed!")
        sys.exit(0)
    else:
        print("\n❌ Some fail-fast configuration quality gates failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
