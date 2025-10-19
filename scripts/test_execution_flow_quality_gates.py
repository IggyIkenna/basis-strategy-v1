#!/usr/bin/env python3
"""
Execution Flow Quality Gates

Validates the complete Order → ExecutionHandshake → reconciliation flow.
Tests tight loop integration and position updates.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Unified Order/Trade System
Reference: docs/TIGHT_LOOP_ARCHITECTURE.md - Tight Loop Architecture
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


class ExecutionFlowQualityGates:
    """Quality gates for execution flow functionality."""
    
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
        """Run all execution flow quality gates."""
        logger.info("🚀 Starting Execution Flow Quality Gates")
        logger.info("=" * 80)
        
        gates = [
            ("QG1", "Execution Flow Integration Tests", self._test_execution_flow_integration),
            ("QG2", "Order to ExecutionHandshake Flow", self._test_order_to_handshake_flow),
            ("QG3", "Venue Interface Routing", self._test_venue_interface_routing),
            ("QG4", "Position Update Handler Integration", self._test_position_update_handler_integration),
            ("QG5", "Tight Loop Orchestration", self._test_tight_loop_orchestration),
            ("QG6", "Execution Manager Processing", self._test_execution_manager_processing),
            ("QG7", "Error Handling and Recovery", self._test_error_handling_recovery),
            ("QG8", "Backtest Mode Execution", self._test_backtest_mode_execution),
            ("QG9", "Position Delta Reconciliation", self._test_position_delta_reconciliation),
            ("QG10", "Component Integration", self._test_component_integration)
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
        logger.info("🚦 EXECUTION FLOW QUALITY GATES RESULTS")
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
    
    def _test_order_to_handshake_flow(self) -> bool:
        """Test Order to ExecutionHandshake flow."""
        try:
            # Check ExecutionManager processes orders correctly
            execution_manager_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'execution' / 'execution_manager.py'
            
            if not execution_manager_file.exists():
                logger.error("❌ ExecutionManager file not found")
                return False
            
            with open(execution_manager_file, 'r') as f:
                content = f.read()
            
            # Check for order processing methods
            required_methods = [
                'process_orders',
                'ExecutionHandshake',
                'List[Order]',
                'List[ExecutionHandshake]'
            ]
            
            missing_methods = []
            for method in required_methods:
                if method not in content:
                    missing_methods.append(method)
            
            if missing_methods:
                logger.error(f"❌ Missing order processing methods: {missing_methods}")
                return False
            
            logger.info("✅ Order to ExecutionHandshake flow validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating order to handshake flow: {e}")
            return False
    
    def _test_venue_interface_routing(self) -> bool:
        """Test venue interface routing."""
        try:
            # Check VenueInterfaceManager routes orders correctly
            venue_interface_manager_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'execution' / 'venue_interface_manager.py'
            
            if not venue_interface_manager_file.exists():
                logger.error("❌ VenueInterfaceManager file not found")
                return False
            
            with open(venue_interface_manager_file, 'r') as f:
                content = f.read()
            
            # Check for routing methods
            required_methods = [
                'route_to_venue',
                '_route_to_cex',
                '_route_to_onchain',
                '_route_to_transfer'
            ]
            
            missing_methods = []
            for method in required_methods:
                if method not in content:
                    missing_methods.append(method)
            
            if missing_methods:
                logger.error(f"❌ Missing venue routing methods: {missing_methods}")
                return False
            
            logger.info("✅ Venue interface routing validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating venue interface routing: {e}")
            return False
    
    def _test_position_update_handler_integration(self) -> bool:
        """Test position update handler integration."""
        try:
            # Check PositionUpdateHandler integrates with execution flow
            position_update_handler_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'components' / 'position_update_handler.py'
            
            if not position_update_handler_file.exists():
                logger.error("❌ PositionUpdateHandler file not found")
                return False
            
            with open(position_update_handler_file, 'r') as f:
                content = f.read()
            
            # Check for execution integration
            required_patterns = [
                'handle_position_update',
                'execution_deltas',
                'ExecutionHandshake',
                'position_monitor'
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                logger.error(f"❌ Missing position update handler patterns: {missing_patterns}")
                return False
            
            logger.info("✅ Position update handler integration validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating position update handler integration: {e}")
            return False
    
    def _test_tight_loop_orchestration(self) -> bool:
        """Test tight loop orchestration."""
        try:
            # Check tight loop integration tests
            result = subprocess.run([
                'python3', '-m', 'pytest', 
                str(self.tests_path / 'integration' / 'test_tight_loop_reconciliation.py'),
                '-v', '--tb=short'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info("✅ Tight loop orchestration tests passed")
                return True
            else:
                logger.error(f"❌ Tight loop orchestration tests failed: {result.stdout}")
                return False
        except Exception as e:
            logger.error(f"❌ Error running tight loop tests: {e}")
            return False
    
    def _test_execution_manager_processing(self) -> bool:
        """Test execution manager processing."""
        try:
            # Check ExecutionManager has proper processing logic
            execution_manager_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'execution' / 'execution_manager.py'
            
            if not execution_manager_file.exists():
                logger.error("❌ ExecutionManager file not found")
                return False
            
            with open(execution_manager_file, 'r') as f:
                content = f.read()
            
            # Check for processing logic
            required_patterns = [
                'process_orders',
                '_process_single_order',
                '_process_atomic_group',
                '_reconcile_with_retry'
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                logger.error(f"❌ Missing execution manager processing patterns: {missing_patterns}")
                return False
            
            logger.info("✅ Execution manager processing validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating execution manager processing: {e}")
            return False
    
    def _test_error_handling_recovery(self) -> bool:
        """Test error handling and recovery."""
        try:
            # Check error handling in execution flow
            execution_manager_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'execution' / 'execution_manager.py'
            
            if not execution_manager_file.exists():
                logger.error("❌ ExecutionManager file not found")
                return False
            
            with open(execution_manager_file, 'r') as f:
                content = f.read()
            
            # Check for error handling
            required_patterns = [
                'try:',
                'except',
                'error_code',
                'error_message',
                'ExecutionStatus.FAILED'
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
    
    def _test_backtest_mode_execution(self) -> bool:
        """Test backtest mode execution."""
        try:
            # Check venue interfaces support backtest mode
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
                
                # Check for backtest mode support
                if 'backtest' not in content.lower() and 'simulated' not in content.lower():
                    logger.error(f"❌ Missing backtest mode support in {interface_file}")
                    return False
            
            logger.info("✅ Backtest mode execution validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating backtest mode execution: {e}")
            return False
    
    def _test_position_delta_reconciliation(self) -> bool:
        """Test position delta reconciliation."""
        try:
            # Check position delta handling
            position_update_handler_file = self.backend_path / 'src' / 'basis_strategy_v1' / 'core' / 'components' / 'position_update_handler.py'
            
            if not position_update_handler_file.exists():
                logger.error("❌ PositionUpdateHandler file not found")
                return False
            
            with open(position_update_handler_file, 'r') as f:
                content = f.read()
            
            # Check for delta reconciliation
            required_patterns = [
                'actual_deltas',
                'position_deltas',
                'reconcile',
                'position_monitor'
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                logger.error(f"❌ Missing position delta reconciliation patterns: {missing_patterns}")
                return False
            
            logger.info("✅ Position delta reconciliation validated")
            return True
        except Exception as e:
            logger.error(f"❌ Error validating position delta reconciliation: {e}")
            return False
    
    def _test_component_integration(self) -> bool:
        """Test component integration."""
        try:
            # Run component integration tests
            result = subprocess.run([
                'python3', '-m', 'pytest', 
                str(self.tests_path / 'integration' / 'test_complete_workflow_integration.py'),
                '-v', '--tb=short'
            ], capture_output=True, text=True, timeout=90)
            
            if result.returncode == 0:
                logger.info("✅ Component integration tests passed")
                return True
            else:
                logger.error(f"❌ Component integration tests failed: {result.stdout}")
                return False
        except Exception as e:
            logger.error(f"❌ Error running component integration tests: {e}")
            return False


def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    validator = ExecutionFlowQualityGates()
    success = validator.run_quality_gates()
    
    # Save results
    results_file = Path(__file__).parent / 'execution_flow_quality_gates_results.json'
    with open(results_file, 'w') as f:
        json.dump(validator.results, f, indent=2, default=str)
    
    if success:
        logger.info("🎉 All execution flow quality gates passed!")
        sys.exit(0)
    else:
        logger.error("💥 Some execution flow quality gates failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

