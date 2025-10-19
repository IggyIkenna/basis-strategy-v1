#!/usr/bin/env python3
"""
Atomic Operations Quality Gates

Validates atomic flash loan operations and execution flow.
Tests the complete Order → ExecutionHandshake → reconciliation flow.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Unified Order/Trade System
Reference: docs/TIGHT_LOOP_ARCHITECTURE.md - Atomic Transaction Handling
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


class AtomicOperationsQualityGates:
    """Quality gates for atomic operations functionality."""
    
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
        """Run all atomic operations quality gates."""
        logger.info("🚀 Starting Atomic Operations Quality Gates")
        logger.info("=" * 80)
        
        gates = [
            ("QG1", "Atomic Operations Integration Tests", self._test_atomic_operations_integration),
            ("QG2", "Execution Flow Integration Tests", self._test_execution_flow_integration),
            ("QG3", "Tight Loop Atomic Integration", self._test_tight_loop_atomic_integration),
            ("QG4", "Order Model Atomic Support", self._test_order_model_atomic_support),
            ("QG5", "ExecutionHandshake Model Validation", self._test_execution_handshake_validation),
            ("QG6", "Atomic Group Processing Logic", self._test_atomic_group_processing),
            ("QG7", "Flash Loan Operation Support", self._test_flash_loan_operations),
            ("QG8", "Position Delta Application", self._test_position_delta_application),
            ("QG9", "Error Handling and Rollback", self._test_error_handling_rollback),
            ("QG10", "Backtest Mode Simulation", self._test_backtest_mode_simulation)
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
        logger.info("🚦 ATOMIC OPERATIONS QUALITY GATES RESULTS")
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
    
    def _test_atomic_operations_integration(self) -> bool:
        """Test atomic operations integration tests."""
        try:
            # Run atomic operations integration tests
            result = subprocess.run([
                'python3', '-m', 'pytest', 
                str(self.tests_path / 'integration' / 'test_atomic_operations.py'),
                '-v', '--tb=short'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info("✅ Atomic operations integration tests passed")
                return True
            else:
                logger.error(f"❌ Atomic operations integration tests failed: {result.stdout}")
                return False
        except Exception as e:
            logger.error(f"❌ Error running atomic operations tests: {e}")
            return False
    
    def _test_execution_flow_integration(self) -> bool:
        """Test execution flow integration tests."""
        try:
            # Run execution flow integration tests
            result = subprocess.run([
                'python3', '-m', 'pytest', 
                str(self.tests_path / 'integration' / 'test_execution_flow.py'),
                '-v', '--tb=short'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info("✅ Execution flow integration tests passed")
                return True
            else:
                logger.error(f"❌ Execution flow integration tests failed: {result.stdout}")
                return False
        except Exception as e:
            logger.error(f"❌ Error running execution flow tests: {e}")
            return False
    
    def _test_tight_loop_atomic_integration(self) -> bool:
        """Test tight loop atomic integration."""
        try:
            # Run tight loop reconciliation tests
            result = subprocess.run([
                'python3', '-m', 'pytest', 
                str(self.tests_path / 'integration' / 'test_tight_loop_reconciliation.py::TestTightLoopReconciliation::test_atomic_group_tight_loop_integration'),
                '-v', '--tb=short'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info("✅ Tight loop atomic integration tests passed")
                return True
            else:
                logger.error(f"❌ Tight loop atomic integration tests failed: {result.stdout}")
                return False
        except Exception as e:
            logger.error(f"❌ Error running tight loop atomic tests: {e}")
            return False
    
    def _test_order_model_atomic_support(self) -> bool:
        """Test Order model atomic support."""
        try:
            # Run Order model tests
            result = subprocess.run([
                'python3', '-m', 'pytest', 
                str(self.tests_path / 'unit' / 'models' / 'test_order_model.py'),
                '-v', '--tb=short'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("✅ Order model atomic support tests passed")
                return True
            else:
                logger.error(f"❌ Order model atomic support tests failed: {result.stdout}")
                return False
        except Exception as e:
            logger.error(f"❌ Error running Order model tests: {e}")
            return False
    
    def _test_execution_handshake_validation(self) -> bool:
        """Test ExecutionHandshake model validation."""
        try:
            # Run ExecutionHandshake model tests
            result = subprocess.run([
                'python3', '-m', 'pytest', 
                str(self.tests_path / 'unit' / 'models' / 'test_execution.py'),
                '-v', '--tb=short'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("✅ ExecutionHandshake model validation tests passed")
                return True
            else:
                logger.error(f"❌ ExecutionHandshake model validation tests failed: {result.stdout}")
                return False
        except Exception as e:
            logger.error(f"❌ Error running ExecutionHandshake tests: {e}")
            return False
    
    def _test_atomic_group_processing(self) -> bool:
        """Test atomic group processing logic."""
        try:
            # Check ExecutionManager has atomic group processing
            execution_manager_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'execution' / 'execution_manager.py'
            
            if not execution_manager_file.exists():
                logger.error("❌ ExecutionManager file not found")
                return False
            
            with open(execution_manager_file, 'r') as f:
                content = f.read()
            
            # Check for atomic group processing methods
            required_methods = [
                '_process_atomic_group',
                '_group_orders_by_atomic_id',
                'atomic_group_id',
                'sequence_in_group'
            ]
            
            missing_methods = []
            for method in required_methods:
                if method not in content:
                    missing_methods.append(method)
            
            if missing_methods:
                logger.error(f"❌ Missing atomic group processing methods: {missing_methods}")
                return False
            
            logger.info("✅ Atomic group processing logic validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating atomic group processing: {e}")
            return False
    
    def _test_flash_loan_operations(self) -> bool:
        """Test flash loan operation support."""
        try:
            # Check Order model has flash loan operations
            order_model_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'models' / 'order.py'
            
            if not order_model_file.exists():
                logger.error("❌ Order model file not found")
                return False
            
            with open(order_model_file, 'r') as f:
                content = f.read()
            
            # Check for flash loan operations
            required_operations = [
                'FLASH_BORROW',
                'FLASH_REPAY',
                'flash_fee_bps'
            ]
            
            missing_operations = []
            for operation in required_operations:
                if operation not in content:
                    missing_operations.append(operation)
            
            if missing_operations:
                logger.error(f"❌ Missing flash loan operations: {missing_operations}")
                return False
            
            logger.info("✅ Flash loan operations support validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating flash loan operations: {e}")
            return False
    
    def _test_position_delta_application(self) -> bool:
        """Test position delta application."""
        try:
            # Check PositionUpdateHandler handles execution deltas
            position_update_handler_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'components' / 'position_update_handler.py'
            
            if not position_update_handler_file.exists():
                logger.error("❌ PositionUpdateHandler file not found")
                return False
            
            with open(position_update_handler_file, 'r') as f:
                content = f.read()
            
            # Check for position delta handling
            required_methods = [
                'handle_position_update',
                'execution_deltas',
                'actual_deltas'
            ]
            
            missing_methods = []
            for method in required_methods:
                if method not in content:
                    missing_methods.append(method)
            
            if missing_methods:
                logger.error(f"❌ Missing position delta handling methods: {missing_methods}")
                return False
            
            logger.info("✅ Position delta application validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating position delta application: {e}")
            return False
    
    def _test_error_handling_rollback(self) -> bool:
        """Test error handling and rollback."""
        try:
            # Check ExecutionManager has error handling
            execution_manager_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'execution' / 'execution_manager.py'
            
            if not execution_manager_file.exists():
                logger.error("❌ ExecutionManager file not found")
                return False
            
            with open(execution_manager_file, 'r') as f:
                content = f.read()
            
            # Check for error handling
            required_patterns = [
                'ExecutionStatus.FAILED',
                'error_code',
                'error_message',
                'was_failed',
                'rollback'
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                logger.error(f"❌ Missing error handling patterns: {missing_patterns}")
                return False
            
            logger.info("✅ Error handling and rollback validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating error handling: {e}")
            return False
    
    def _test_backtest_mode_simulation(self) -> bool:
        """Test backtest mode simulation."""
        try:
            # Check venue interfaces have backtest simulation
            venue_interfaces = [
                'cex_execution_interface.py',
                'onchain_execution_interface.py',
                'transfer_execution_interface.py'
            ]
            
            for interface_file in venue_interfaces:
                interface_path = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'interfaces' / interface_file
                
                if not interface_path.exists():
                    logger.warning(f"⚠️ Interface file not found: {interface_file}")
                    continue
                
                with open(interface_path, 'r') as f:
                    content = f.read()
                
                # Check for backtest simulation methods
                if '_execute_backtest_' not in content and 'simulated' not in content:
                    logger.error(f"❌ Missing backtest simulation in {interface_file}")
                    return False
            
            logger.info("✅ Backtest mode simulation validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating backtest simulation: {e}")
            return False


def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    validator = AtomicOperationsQualityGates()
    success = validator.run_quality_gates()
    
    # Save results
    results_file = Path(__file__).parent / 'atomic_operations_quality_gates_results.json'
    with open(results_file, 'w') as f:
        json.dump(validator.results, f, indent=2, default=str)
    
    if success:
        logger.info("🎉 All atomic operations quality gates passed!")
        sys.exit(0)
    else:
        logger.error("💥 Some atomic operations quality gates failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

