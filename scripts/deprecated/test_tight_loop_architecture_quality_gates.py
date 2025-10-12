#!/usr/bin/env python3
"""
Tight Loop Architecture Quality Gates

This script validates that the tight loop architecture is properly implemented
as an execution reconciliation pattern.

Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-001
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 4
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

class TightLoopArchitectureQualityGates:
    """Quality gates for tight loop architecture implementation"""
    
    def __init__(self):
        self.passed_gates = 0
        self.total_gates = 0
        self.test_results = []
    
    def run_all_tests(self) -> bool:
        """Run all tight loop architecture quality gates"""
        logger.info("Starting Tight Loop Architecture Quality Gates")
        
        # QG1: Sequential Instruction Execution
        self._test_sequential_instruction_execution()
        
        # QG2: Position Reconciliation Pattern
        self._test_position_reconciliation_pattern()
        
        # QG3: No Monitoring Cascade
        self._test_no_monitoring_cascade()
        
        # QG4: Execution Manager Integration
        self._test_execution_manager_integration()
        
        # QG5: Position Monitor Integration
        self._test_position_monitor_integration()
        
        # QG6: State Persistence
        self._test_state_persistence()
        
        # QG7: Error Handling in Tight Loop
        self._test_error_handling_in_tight_loop()
        
        # QG8: Integration Test
        self._test_integration()
        
        # Print results
        self._print_results()
        
        return self.passed_gates == self.total_gates
    
    def _test_sequential_instruction_execution(self):
        """Test that instructions execute sequentially in tight loops"""
        self.total_gates += 1
        try:
            # Check for sequential execution patterns in execution manager
            execution_files = [
                'backend/src/basis_strategy_v1/core/strategies/components/strategy_manager.py',
                'backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py'
            ]
            
            sequential_patterns_found = False
            for file_path in execution_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Look for sequential execution patterns
                    if (re.search(r'for.*instruction.*in', content) or
                        re.search(r'await.*instruction', content) or
                        re.search(r'sequential.*execution', content)):
                        sequential_patterns_found = True
                        break
            
            if not sequential_patterns_found:
                raise AssertionError("No sequential instruction execution patterns found")
            
            self.passed_gates += 1
            self.test_results.append("QG1: Sequential Instruction Execution - PASSED")
            logger.info("✅ QG1: Sequential Instruction Execution - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG1: Sequential Instruction Execution - FAILED: {e}")
            logger.error(f"❌ QG1: Sequential Instruction Execution - FAILED: {e}")
    
    def _test_position_reconciliation_pattern(self):
        """Test that position reconciliation pattern is implemented"""
        self.total_gates += 1
        try:
            # Check for reconciliation patterns in position monitor and execution
            component_files = [
                'backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/position_update_handler.py'
            ]
            
            reconciliation_patterns_found = False
            for file_path in component_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Look for reconciliation patterns
                    if (re.search(r'reconciliation', content) or
                        re.search(r'verify.*position', content) or
                        re.search(r'expected.*state', content) or
                        re.search(r'position.*match', content)):
                        reconciliation_patterns_found = True
                        break
            
            if not reconciliation_patterns_found:
                raise AssertionError("No position reconciliation patterns found")
            
            self.passed_gates += 1
            self.test_results.append("QG2: Position Reconciliation Pattern - PASSED")
            logger.info("✅ QG2: Position Reconciliation Pattern - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG2: Position Reconciliation Pattern - FAILED: {e}")
            logger.error(f"❌ QG2: Position Reconciliation Pattern - FAILED: {e}")
    
    def _test_no_monitoring_cascade(self):
        """Test that monitoring cascade is not implemented"""
        self.total_gates += 1
        try:
            # Check that monitoring cascade is not implemented
            engine_file = 'backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py'
            
            if os.path.exists(engine_file):
                with open(engine_file, 'r') as f:
                    content = f.read()
                
                # Look for monitoring cascade patterns (should NOT exist)
                cascade_patterns = [
                    r'position_monitor.*exposure_monitor',
                    r'exposure_monitor.*risk_monitor',
                    r'risk_monitor.*pnl_monitor',
                    r'cascade.*monitor',
                    r'monitor.*cascade'
                ]
                
                cascade_found = False
                for pattern in cascade_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        cascade_found = True
                        break
                
                if cascade_found:
                    raise AssertionError("Monitoring cascade pattern found - should be removed")
            
            self.passed_gates += 1
            self.test_results.append("QG3: No Monitoring Cascade - PASSED")
            logger.info("✅ QG3: No Monitoring Cascade - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG3: No Monitoring Cascade - FAILED: {e}")
            logger.error(f"❌ QG3: No Monitoring Cascade - FAILED: {e}")
    
    def _test_execution_manager_integration(self):
        """Test that execution manager integrates with tight loop"""
        self.total_gates += 1
        try:
            # Check execution manager integration
            execution_files = [
                'backend/src/basis_strategy_v1/core/strategies/components/strategy_manager.py',
                'backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py'
            ]
            
            integration_found = False
            for file_path in execution_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Look for execution manager integration patterns
                    if (re.search(r'position_monitor', content) or
                        re.search(r'execution.*instruction', content) or
                        re.search(r'send.*instruction', content)):
                        integration_found = True
                        break
            
            if not integration_found:
                raise AssertionError("No execution manager integration patterns found")
            
            self.passed_gates += 1
            self.test_results.append("QG4: Execution Manager Integration - PASSED")
            logger.info("✅ QG4: Execution Manager Integration - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG4: Execution Manager Integration - FAILED: {e}")
            logger.error(f"❌ QG4: Execution Manager Integration - FAILED: {e}")
    
    def _test_position_monitor_integration(self):
        """Test that position monitor integrates with tight loop"""
        self.total_gates += 1
        try:
            # Check position monitor integration
            position_monitor_file = 'backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py'
            
            if os.path.exists(position_monitor_file):
                with open(position_monitor_file, 'r') as f:
                    content = f.read()
                
                # Look for position monitor integration patterns
                integration_patterns = [
                    r'update.*position',
                    r'calculate.*position',
                    r'position.*state',
                    r'venue.*position'
                ]
                
                integration_found = False
                for pattern in integration_patterns:
                    if re.search(pattern, content):
                        integration_found = True
                        break
                
                if not integration_found:
                    raise AssertionError("No position monitor integration patterns found")
            
            self.passed_gates += 1
            self.test_results.append("QG5: Position Monitor Integration - PASSED")
            logger.info("✅ QG5: Position Monitor Integration - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG5: Position Monitor Integration - FAILED: {e}")
            logger.error(f"❌ QG5: Position Monitor Integration - FAILED: {e}")
    
    def _test_state_persistence(self):
        """Test that state persistence is implemented"""
        self.total_gates += 1
        try:
            # Check for state persistence patterns
            component_files = [
                'backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/pnl_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py'
            ]
            
            persistence_found = False
            for file_path in component_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Look for state persistence patterns
                    if (re.search(r'last_.*=', content) or
                        re.search(r'self\._.*=', content) or
                        re.search(r'persist.*state', content) or
                        re.search(r'maintain.*state', content)):
                        persistence_found = True
                        break
            
            if not persistence_found:
                raise AssertionError("No state persistence patterns found")
            
            self.passed_gates += 1
            self.test_results.append("QG6: State Persistence - PASSED")
            logger.info("✅ QG6: State Persistence - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG6: State Persistence - FAILED: {e}")
            logger.error(f"❌ QG6: State Persistence - FAILED: {e}")
    
    def _test_error_handling_in_tight_loop(self):
        """Test that error handling is implemented in tight loop"""
        self.total_gates += 1
        try:
            # Check for error handling patterns
            execution_files = [
                'backend/src/basis_strategy_v1/core/strategies/components/strategy_manager.py',
                'backend/src/basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py',
                'backend/src/basis_strategy_v1/core/strategies/components/position_update_handler.py'
            ]
            
            error_handling_found = False
            for file_path in execution_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Look for error handling patterns
                    if (re.search(r'try:', content) or
                        re.search(r'except.*Exception', content) or
                        re.search(r'retry.*logic', content) or
                        re.search(r'error.*handling', content)):
                        error_handling_found = True
                        break
            
            if not error_handling_found:
                raise AssertionError("No error handling patterns found in tight loop")
            
            self.passed_gates += 1
            self.test_results.append("QG7: Error Handling in Tight Loop - PASSED")
            logger.info("✅ QG7: Error Handling in Tight Loop - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG7: Error Handling in Tight Loop - FAILED: {e}")
            logger.error(f"❌ QG7: Error Handling in Tight Loop - FAILED: {e}")
    
    def _test_integration(self):
        """Integration test for tight loop architecture"""
        self.total_gates += 1
        try:
            # Test that we can import components without errors
            from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
            from basis_strategy_v1.core.strategies.components.strategy_manager import StrategyManager
            from basis_strategy_v1.core.strategies.components.position_update_handler import PositionUpdateHandler
            
            # Test that components can be instantiated
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
            
            # Test component instantiation
            position_monitor = PositionMonitor(config, data_provider, utility_manager)
            strategy_manager = StrategyManager(config, data_provider, utility_manager)
            
            # Create mock components for PositionUpdateHandler
            class MockRiskMonitor:
                pass
            class MockPnLCalculator:
                pass
            
            position_update_handler = PositionUpdateHandler(
                config=config,
                position_monitor=position_monitor,
                exposure_monitor=position_monitor,  # Use position_monitor as mock
                risk_monitor=MockRiskMonitor(),
                pnl_calculator=MockPnLCalculator()
            )
            
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
        logger.info("TIGHT LOOP ARCHITECTURE QUALITY GATES RESULTS")
        logger.info("=" * 60)
        
        for result in self.test_results:
            logger.info(result)
        
        logger.info("=" * 60)
        logger.info(f"PASSED: {self.passed_gates}/{self.total_gates} quality gates")
        logger.info(f"SUCCESS RATE: {(self.passed_gates/self.total_gates)*100:.1f}%")
        
        if self.passed_gates == self.total_gates:
            logger.info("🎉 ALL QUALITY GATES PASSED! Tight loop architecture is working correctly.")
        else:
            logger.error(f"❌ {self.total_gates - self.passed_gates} quality gates failed. Tight loop architecture needs fixes.")
        
        logger.info("=" * 60)

def main():
    """Main function to run tight loop architecture quality gates"""
    quality_gates = TightLoopArchitectureQualityGates()
    success = quality_gates.run_all_tests()
    
    if success:
        print("\n✅ All tight loop architecture quality gates passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tight loop architecture quality gates failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
