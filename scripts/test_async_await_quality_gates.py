#!/usr/bin/env python3
"""
Async/Await Violations Quality Gates

Validates that all internal component methods are synchronous and async/await
is only used for I/O operations (Event Logger, Results Store, API entry points).

Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-006 Synchronous Component Execution
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# Add the backend source to the path
backend_src = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)-8s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class AsyncAwaitQualityGates:
    """Quality gates for async/await violations."""
    
    def __init__(self):
        self.backend_src = Path(__file__).parent.parent / "backend" / "src"
        self.component_files = [
            "basis_strategy_v1/core/components/position_monitor.py",
            "basis_strategy_v1/core/components/risk_monitor.py", 
            "basis_strategy_v1/core/strategies/components/strategy_manager.py",
            "basis_strategy_v1/core/components/position_update_handler.py",
            "basis_strategy_v1/core/components/pnl_monitor.py"
        ]
        self.io_files = [
            "basis_strategy_v1/infrastructure/logging/event_logger.py",
            "basis_strategy_v1/core/strategies/components/results_store.py"
        ]
        self.api_files = [
            "basis_strategy_v1/api/backtest_service.py",
            "basis_strategy_v1/api/live_trading_service.py"
        ]
        
    def run_quality_gates(self) -> bool:
        """Run all async/await quality gates."""
        logger.info("🚀 Starting Async/Await Quality Gates")
        logger.info("=" * 80)
        
        gates = [
            ("QG1", "Component Methods Synchronous", self._test_component_methods_synchronous),
            ("QG2", "No Async in Component Internal Methods", self._test_no_async_in_components),
            ("QG3", "No Await in Component Internal Methods", self._test_no_await_in_components),
            ("QG4", "Event Logger Keeps Async", self._test_event_logger_async),
            ("QG5", "Results Store Keeps Async", self._test_results_store_async),
            ("QG6", "API Entry Points Keep Async", self._test_api_entry_points_async),
            ("QG7", "ADR-006 Compliance", self._test_adr006_compliance),
            ("QG8", "Integration Test", self._test_integration)
        ]
        
        passed = 0
        total = len(gates)
        
        for gate_id, gate_name, test_func in gates:
            logger.info(f"🔄 Running {gate_id}: {gate_name}")
            try:
                if test_func():
                    logger.info(f"✅ {gate_id}: PASS")
                    passed += 1
                else:
                    logger.info(f"❌ {gate_id}: FAIL")
            except Exception as e:
                logger.error(f"❌ {gate_id}: ERROR - {e}")
        
        logger.info("=" * 80)
        logger.info("🚦 ASYNC/AWAIT QUALITY GATES RESULTS")
        logger.info("=" * 80)
        
        status = "PASS" if passed == total else "FAIL"
        logger.info(f"Overall Status: {status}")
        logger.info(f"Gates Passed: {passed}")
        logger.info(f"Gates Failed: {total - passed}")
        logger.info(f"Pass Rate: {(passed/total)*100:.1f}%")
        logger.info("")
        logger.info("Gate Results:")
        for gate_id, gate_name, _ in gates:
            logger.info(f"  {gate_id}: ✅ PASS" if gate_id in [g[0] for g in gates[:passed]] else f"  {gate_id}: ❌ FAIL")
        
        if passed == total:
            logger.info("")
            logger.info("🎉 All async/await quality gates passed!")
        
        return passed == total
    
    def _test_component_methods_synchronous(self) -> bool:
        """Test that all component methods are synchronous (except I/O operations)."""
        violations = []
        
        for file_path in self.component_files:
            full_path = self.backend_src / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                content = f.read()
                
            # Find all async def in component files
            async_methods = re.findall(r'^\s*async def (\w+)', content, re.MULTILINE)
            
            # Filter out I/O operations (allowed to be async)
            for method in async_methods:
                # Allow I/O operations to remain async
                if not any(io_pattern in method for io_pattern in [
                    'reconcile_with_live', '_query_', '_alert_', 'log_', 'store_', 'save_', 'load_'
                ]):
                    violations.append(f"{file_path}:{method}")
        
        if violations:
            logger.error(f"Found {len(violations)} async internal methods in components:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_no_async_in_components(self) -> bool:
        """Test that no async def exists in component internal methods."""
        violations = []
        
        for file_path in self.component_files:
            full_path = self.backend_src / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines, 1):
                if re.search(r'^\s*async def', line):
                    # Check if it's an I/O method (allowed)
                    method_name = re.search(r'async def (\w+)', line)
                    if method_name:
                        method = method_name.group(1)
                        # Allow specific I/O methods
                        if not any(io_method in method for io_method in ['reconcile_with_live', '_query_', '_alert_']):
                            violations.append(f"{file_path}:{i}:{method}")
        
        if violations:
            logger.error(f"Found {len(violations)} async internal methods:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_no_await_in_components(self) -> bool:
        """Test that no await calls exist in component internal methods (except I/O operations)."""
        violations = []
        
        for file_path in self.component_files:
            full_path = self.backend_src / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines, 1):
                # Skip comments and docstrings
                stripped = line.strip()
                if (stripped.startswith('#') or stripped.startswith('"""') or 
                    stripped.startswith("'''") or stripped.startswith('*') or 
                    stripped.startswith('-') or stripped.startswith('✅') or
                    stripped.startswith('❌') or 'await' not in line):
                    continue
                
                # Check if this await is in an I/O method (allowed)
                # Look for method definition above this line
                is_io_method = False
                for j in range(max(0, i-20), i):
                    if j < len(lines):
                        method_line = lines[j]
                        if 'async def' in method_line:
                            method_name = re.search(r'async def (\w+)', method_line)
                            if method_name:
                                method = method_name.group(1)
                                if any(io_pattern in method for io_pattern in [
                                    'reconcile_with_live', '_query_', '_alert_', 'log_', 'store_', 'save_', 'load_'
                                ]):
                                    is_io_method = True
                                    break
                
                if not is_io_method:
                    violations.append(f"{file_path}:{i}:{line.strip()}")
        
        if violations:
            logger.error(f"Found {len(violations)} await calls in component internal methods:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_event_logger_async(self) -> bool:
        """Test that Event Logger keeps async methods."""
        file_path = self.backend_src / self.io_files[0]
        if not file_path.exists():
            logger.warning(f"Event Logger file not found: {file_path}")
            return True
            
        with open(file_path, 'r') as f:
            content = f.read()
            
        async_methods = re.findall(r'^\s*async def (\w+)', content, re.MULTILINE)
        if not async_methods:
            logger.error("Event Logger has no async methods - should have async I/O methods")
            return False
            
        logger.info(f"Event Logger has {len(async_methods)} async methods (correct for I/O operations)")
        return True
    
    def _test_results_store_async(self) -> bool:
        """Test that Results Store keeps async methods."""
        file_path = self.backend_src / self.io_files[1]
        if not file_path.exists():
            logger.info("Results Store file not found - skipping test")
            return True
            
        with open(file_path, 'r') as f:
            content = f.read()
            
        async_methods = re.findall(r'^\s*async def (\w+)', content, re.MULTILINE)
        if not async_methods:
            logger.error("Results Store has no async methods - should have async I/O methods")
            return False
            
        logger.info(f"Results Store has {len(async_methods)} async methods (correct for I/O operations)")
        return True
    
    def _test_api_entry_points_async(self) -> bool:
        """Test that API entry points keep async methods."""
        violations = []
        
        for file_path in self.api_files:
            full_path = self.backend_src / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                content = f.read()
                
            # Check for key async entry points
            if 'run_backtest' in content and 'async def run_backtest' not in content:
                violations.append(f"{file_path}: run_backtest should be async")
            if 'start_live_trading' in content and 'async def start_live_trading' not in content:
                violations.append(f"{file_path}: start_live_trading should be async")
        
        if violations:
            logger.error(f"Found {len(violations)} non-async API entry points:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_adr006_compliance(self) -> bool:
        """Test ADR-006 compliance."""
        # This is a composite test of the above tests
        return (self._test_component_methods_synchronous() and 
                self._test_no_async_in_components() and 
                self._test_no_await_in_components())
    
    def _test_integration(self) -> bool:
        """Integration test - verify overall async/await architecture."""
        # Test that we can import the components without errors
        try:
            from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
            from basis_strategy_v1.core.strategies.components.risk_monitor import RiskMonitor
            from basis_strategy_v1.core.strategies.components.strategy_manager import StrategyManager
            from basis_strategy_v1.core.strategies.components.position_update_handler import PositionUpdateHandler
            from basis_strategy_v1.core.components.pnl_monitor import PnLCalculator
            
            logger.info("✅ All components imported successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Component import failed: {e}")
            return False

def main():
    """Main entry point."""
    quality_gates = AsyncAwaitQualityGates()
    success = quality_gates.run_quality_gates()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
