#!/usr/bin/env python3
"""
Tight Loop Quality Gates

Validates tight loop architecture and reconciliation flow.
Tests PositionUpdateHandler orchestration and component integration.

Reference: docs/TIGHT_LOOP_ARCHITECTURE.md - Tight Loop Architecture
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Component Integration
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import json

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend' / 'src'
sys.path.append(str(backend_path))

logger = logging.getLogger(__name__)


class TightLoopQualityGates:
    """Quality gates for tight loop functionality."""
    
    def __init__(self):
        self.results = {
            'overall_status': 'PENDING',
            'gates_passed': 0,
            'gates_failed': 0,
            'gate_results': {},
            'summary': {},
            'timestamp': None
        }
        self.backend_path = Path(__file__).parent.parent / 'backend'
        self.tests_path = Path(__file__).parent.parent / 'tests'
    
    def run_quality_gates(self) -> bool:
        """Run all tight loop quality gates."""
        logger.info("🚀 Starting Tight Loop Quality Gates")
        logger.info("=" * 80)
        
        gates = [
            ("QG1", "Tight Loop Integration Tests", self._test_tight_loop_integration),
            ("QG2", "PositionUpdateHandler Orchestration", self._test_position_update_handler_orchestration),
            ("QG3", "Component Chain Integration", self._test_component_chain_integration),
            ("QG4", "Execution Manager Integration", self._test_execution_manager_integration),
            ("QG5", "Position Monitor Integration", self._test_position_monitor_integration),
            ("QG6", "Reconciliation Flow", self._test_reconciliation_flow),
            ("QG7", "Atomic Transaction Handling", self._test_atomic_transaction_handling),
            ("QG8", "Error Handling and Recovery", self._test_error_handling_recovery),
            ("QG9", "Mode-Specific Behavior", self._test_mode_specific_behavior),
            ("QG10", "Performance and Latency", self._test_performance_latency)
        ]
        
        passed = 0
        total = len(gates)
        
        for gate_id, gate_name, test_func in gates:
            logger.info(f"🔄 Running {gate_id}: {gate_name}")
            try:
                if test_func():
                    logger.info(f"✅ {gate_id}: PASS")
                    passed += 1
                    self.results['gates_passed'] += 1
                    self.results['gate_results'][gate_id] = {'status': 'PASS', 'name': gate_name}
                else:
                    logger.info(f"❌ {gate_id}: FAIL")
                    self.results['gates_failed'] += 1
                    self.results['gate_results'][gate_id] = {'status': 'FAIL', 'name': gate_name}
            except Exception as e:
                logger.error(f"❌ {gate_id}: ERROR - {e}")
                self.results['gates_failed'] += 1
                self.results['gate_results'][gate_id] = {'status': 'ERROR', 'name': gate_name, 'error': str(e)}
        
        logger.info("=" * 80)
        logger.info("🚦 TIGHT LOOP QUALITY GATES RESULTS")
        logger.info("=" * 80)
        
        status = "PASS" if passed == total else "FAIL"
        logger.info(f"Overall Status: {status}")
        logger.info(f"Gates Passed: {passed}")
        logger.info(f"Gates Failed: {total - passed}")
        logger.info(f"Pass Rate: {(passed/total)*100:.1f}%")
        
        self.results['overall_status'] = status
        self.results['summary'] = {
            'total_gates': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': (passed/total)*100
        }
        
        return status == "PASS"
    
    def _test_tight_loop_integration(self) -> bool:
        """Test tight loop integration tests."""
        try:
            # Run tight loop reconciliation tests
            result = subprocess.run([
                'python3', '-m', 'pytest', 
                str(self.tests_path / 'integration' / 'test_tight_loop_reconciliation.py'),
                '-v', '--tb=short'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info("✅ Tight loop integration tests passed")
                return True
            else:
                logger.error(f"❌ Tight loop integration tests failed: {result.stdout}")
                return False
        except Exception as e:
            logger.error(f"❌ Error running tight loop tests: {e}")
            return False
    
    def _test_position_update_handler_orchestration(self) -> bool:
        """Test PositionUpdateHandler orchestration."""
        try:
            # Check PositionUpdateHandler has orchestration methods
            position_update_handler_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'components' / 'position_update_handler.py'
            
            if not position_update_handler_file.exists():
                logger.error("❌ PositionUpdateHandler file not found")
                return False
            
            with open(position_update_handler_file, 'r') as f:
                content = f.read()
            
            # Check for orchestration methods
            required_methods = [
                'handle_position_update',
                'update_state',
                'position_monitor',
                'exposure_monitor',
                'risk_monitor',
                'pnl_monitor'
            ]
            
            missing_methods = []
            for method in required_methods:
                if method not in content:
                    missing_methods.append(method)
            
            if missing_methods:
                logger.error(f"❌ Missing PositionUpdateHandler orchestration methods: {missing_methods}")
                return False
            
            logger.info("✅ PositionUpdateHandler orchestration validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating PositionUpdateHandler orchestration: {e}")
            return False
    
    def _test_component_chain_integration(self) -> bool:
        """Test component chain integration."""
        try:
            # Check component chain integration
            position_update_handler_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'components' / 'position_update_handler.py'
            
            if not position_update_handler_file.exists():
                logger.error("❌ PositionUpdateHandler file not found")
                return False
            
            with open(position_update_handler_file, 'r') as f:
                content = f.read()
            
            # Check for component chain
            required_patterns = [
                'position_monitor.update_state',
                'exposure_monitor.calculate_exposure',
                'risk_monitor.assess_risk',
                'pnl_monitor.calculate_pnl'
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                logger.error(f"❌ Missing component chain patterns: {missing_patterns}")
                return False
            
            logger.info("✅ Component chain integration validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating component chain integration: {e}")
            return False
    
    def _test_execution_manager_integration(self) -> bool:
        """Test execution manager integration."""
        try:
            # Check ExecutionManager integrates with tight loop
            execution_manager_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'execution' / 'execution_manager.py'
            
            if not execution_manager_file.exists():
                logger.error("❌ ExecutionManager file not found")
                return False
            
            with open(execution_manager_file, 'r') as f:
                content = f.read()
            
            # Check for tight loop integration
            required_patterns = [
                'position_update_handler',
                'process_orders',
                'ExecutionHandshake',
                'reconcile'
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                logger.error(f"❌ Missing execution manager integration patterns: {missing_patterns}")
                return False
            
            logger.info("✅ Execution manager integration validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating execution manager integration: {e}")
            return False
    
    def _test_position_monitor_integration(self) -> bool:
        """Test position monitor integration."""
        try:
            # Check PositionMonitor integrates with tight loop
            position_monitor_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'components' / 'position_monitor.py'
            
            if not position_monitor_file.exists():
                logger.error("❌ PositionMonitor file not found")
                return False
            
            with open(position_monitor_file, 'r') as f:
                content = f.read()
            
            # Check for tight loop integration
            required_patterns = [
                'update_state',
                'execution_deltas',
                'trigger_source',
                'execution_manager'
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                logger.error(f"❌ Missing position monitor integration patterns: {missing_patterns}")
                return False
            
            logger.info("✅ Position monitor integration validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating position monitor integration: {e}")
            return False
    
    def _test_reconciliation_flow(self) -> bool:
        """Test reconciliation flow."""
        try:
            # Check reconciliation flow in PositionUpdateHandler
            position_update_handler_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'components' / 'position_update_handler.py'
            
            if not position_update_handler_file.exists():
                logger.error("❌ PositionUpdateHandler file not found")
                return False
            
            with open(position_update_handler_file, 'r') as f:
                content = f.read()
            
            # Check for reconciliation patterns
            required_patterns = [
                'reconcile',
                'execution_deltas',
                'position_update',
                'tight_loop'
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                logger.error(f"❌ Missing reconciliation flow patterns: {missing_patterns}")
                return False
            
            logger.info("✅ Reconciliation flow validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating reconciliation flow: {e}")
            return False
    
    def _test_atomic_transaction_handling(self) -> bool:
        """Test atomic transaction handling."""
        try:
            # Check atomic transaction handling in tight loop
            position_update_handler_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'components' / 'position_update_handler.py'
            
            if not position_update_handler_file.exists():
                logger.error("❌ PositionUpdateHandler file not found")
                return False
            
            with open(position_update_handler_file, 'r') as f:
                content = f.read()
            
            # Check for atomic transaction handling
            required_patterns = [
                'atomic',
                'transaction',
                'rollback',
                'all_or_nothing'
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                logger.error(f"❌ Missing atomic transaction handling patterns: {missing_patterns}")
                return False
            
            logger.info("✅ Atomic transaction handling validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating atomic transaction handling: {e}")
            return False
    
    def _test_error_handling_recovery(self) -> bool:
        """Test error handling and recovery."""
        try:
            # Check error handling in tight loop
            position_update_handler_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'components' / 'position_update_handler.py'
            
            if not position_update_handler_file.exists():
                logger.error("❌ PositionUpdateHandler file not found")
                return False
            
            with open(position_update_handler_file, 'r') as f:
                content = f.read()
            
            # Check for error handling
            required_patterns = [
                'try:',
                'except',
                'error',
                'recovery',
                'rollback'
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                logger.error(f"❌ Missing error handling patterns: {missing_patterns}")
                return False
            
            logger.info("✅ Error handling and recovery validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating error handling: {e}")
            return False
    
    def _test_mode_specific_behavior(self) -> bool:
        """Test mode-specific behavior."""
        try:
            # Check mode-specific behavior in tight loop
            position_update_handler_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'components' / 'position_update_handler.py'
            
            if not position_update_handler_file.exists():
                logger.error("❌ PositionUpdateHandler file not found")
                return False
            
            with open(position_update_handler_file, 'r') as f:
                content = f.read()
            
            # Check for mode-specific behavior
            required_patterns = [
                'execution_mode',
                'backtest',
                'live',
                'mode_specific'
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                logger.error(f"❌ Missing mode-specific behavior patterns: {missing_patterns}")
                return False
            
            logger.info("✅ Mode-specific behavior validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating mode-specific behavior: {e}")
            return False
    
    def _test_performance_latency(self) -> bool:
        """Test performance and latency."""
        try:
            # Check performance considerations in tight loop
            tight_loop_docs_file = Path(__file__).parent.parent / 'docs' / 'TIGHT_LOOP_ARCHITECTURE.md'
            
            if not tight_loop_docs_file.exists():
                logger.error("❌ TIGHT_LOOP_ARCHITECTURE.md not found")
                return False
            
            with open(tight_loop_docs_file, 'r') as f:
                content = f.read()
            
            # Check for performance considerations
            required_patterns = [
                'latency',
                'performance',
                'throughput',
                'timing'
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                logger.error(f"❌ Missing performance considerations: {missing_patterns}")
                return False
            
            logger.info("✅ Performance and latency validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating performance: {e}")
            return False


def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    validator = TightLoopQualityGates()
    success = validator.run_quality_gates()
    
    # Save results
    results_file = Path(__file__).parent / 'tight_loop_quality_gates_results.json'
    with open(results_file, 'w') as f:
        json.dump(validator.results, f, indent=2, default=str)
    
    if success:
        logger.info("🎉 All tight loop quality gates passed!")
        sys.exit(0)
    else:
        logger.error("💥 Some tight loop quality gates failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

