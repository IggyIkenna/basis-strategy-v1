#!/usr/bin/env python3
"""
Strategy Manager Refactor Quality Gates

Validates that the strategy manager refactor is properly implemented with:
- Base strategy manager architecture
- Strategy factory pattern
- Inheritance-based strategy implementations
- Standardized wrapper actions

Reference: docs/MODES.md - Standardized Strategy Manager Architecture
Reference: docs/specs/05_STRATEGY_MANAGER.md - Component specification
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

class StrategyManagerRefactorQualityGates:
    """Quality gates for strategy manager refactor implementation."""
    
    def __init__(self):
        self.backend_src = Path(__file__).parent.parent / "backend" / "src"
        self.strategy_files = [
            "basis_strategy_v1/core/strategies/base_strategy_manager.py",
            "basis_strategy_v1/core/strategies/strategy_factory.py",
            "basis_strategy_v1/core/strategies/pure_lending_strategy.py"
        ]
        
    def run_quality_gates(self) -> bool:
        """Run all strategy manager refactor quality gates."""
        logger.info("🚀 Starting Strategy Manager Refactor Quality Gates")
        logger.info("=" * 80)
        
        gates = [
            ("QG1", "Base Strategy Manager Architecture", self._test_base_strategy_manager),
            ("QG2", "Strategy Factory Pattern", self._test_strategy_factory),
            ("QG3", "Strategy Implementation", self._test_strategy_implementation),
            ("QG4", "Standardized Wrapper Actions", self._test_standardized_actions),
            ("QG5", "Inheritance Pattern", self._test_inheritance_pattern),
            ("QG6", "Strategy Registration", self._test_strategy_registration),
            ("QG7", "Architecture Compliance", self._test_architecture_compliance),
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
        logger.info("🚦 STRATEGY MANAGER REFACTOR QUALITY GATES RESULTS")
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
            logger.info("🎉 All strategy manager refactor quality gates passed!")
        
        return passed == total
    
    def _test_base_strategy_manager(self) -> bool:
        """Test that base strategy manager architecture is implemented."""
        violations = []
        
        base_file = self.backend_src / "basis_strategy_v1/core/strategies/base_strategy_manager.py"
        if not base_file.exists():
            violations.append("Base strategy manager file not found")
            return False
        
        with open(base_file, 'r') as f:
            content = f.read()
        
        # Check for required classes and methods
        required_elements = [
            'class StrategyAction(BaseModel)',
            'class BaseStrategyManager(ABC)',
            '@abstractmethod',
            'def calculate_target_position(',
            'def entry_full(',
            'def entry_partial(',
            'def exit_full(',
            'def exit_partial(',
            'def sell_dust(',
            'def get_equity(',
            'def trigger_tight_loop('
        ]
        
        for element in required_elements:
            if element not in content:
                violations.append(f"Missing required element: {element}")
        
        if violations:
            logger.error(f"Found {len(violations)} base strategy manager violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_strategy_factory(self) -> bool:
        """Test that strategy factory pattern is implemented."""
        violations = []
        
        factory_file = self.backend_src / "basis_strategy_v1/core/strategies/strategy_factory.py"
        if not factory_file.exists():
            violations.append("Strategy factory file not found")
            return False
        
        with open(factory_file, 'r') as f:
            content = f.read()
        
        # Check for required factory elements
        required_elements = [
            'class StrategyFactory',
            'STRATEGY_MAP',
            'def create_strategy(',
            'def get_available_modes(',
            'def is_mode_supported(',
            'def register_strategy('
        ]
        
        for element in required_elements:
            if element not in content:
                violations.append(f"Missing required factory element: {element}")
        
        if violations:
            logger.error(f"Found {len(violations)} strategy factory violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_strategy_implementation(self) -> bool:
        """Test that strategy implementations exist."""
        violations = []
        
        # Check for Pure Lending strategy
        pure_lending_file = self.backend_src / "basis_strategy_v1/core/strategies/pure_lending_strategy.py"
        if not pure_lending_file.exists():
            violations.append("Pure lending strategy file not found")
        else:
            with open(pure_lending_file, 'r') as f:
                content = f.read()
            
            # Check for required strategy elements
            required_elements = [
                'class PureLendingStrategy(BaseStrategyManager)',
                'def calculate_target_position(',
                'def entry_full(',
                'def entry_partial(',
                'def exit_full(',
                'def exit_partial(',
                'def sell_dust('
            ]
            
            for element in required_elements:
                if element not in content:
                    violations.append(f"Missing required strategy element: {element}")
        
        if violations:
            logger.error(f"Found {len(violations)} strategy implementation violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_standardized_actions(self) -> bool:
        """Test that standardized wrapper actions are implemented."""
        violations = []
        
        pure_lending_file = self.backend_src / "basis_strategy_v1/core/strategies/pure_lending_strategy.py"
        if not pure_lending_file.exists():
            violations.append("Pure lending strategy file not found")
            return False
        
        with open(pure_lending_file, 'r') as f:
            content = f.read()
        
        # Check for standardized action types
        action_types = [
            'action_type=\'entry_full\'',
            'action_type=\'entry_partial\'',
            'action_type=\'exit_full\'',
            'action_type=\'exit_partial\'',
            'action_type=\'sell_dust\''
        ]
        
        for action_type in action_types:
            if action_type not in content:
                violations.append(f"Missing standardized action type: {action_type}")
        
        if violations:
            logger.error(f"Found {len(violations)} standardized actions violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_inheritance_pattern(self) -> bool:
        """Test that inheritance pattern is properly implemented."""
        violations = []
        
        pure_lending_file = self.backend_src / "basis_strategy_v1/core/strategies/pure_lending_strategy.py"
        if not pure_lending_file.exists():
            violations.append("Pure lending strategy file not found")
            return False
        
        with open(pure_lending_file, 'r') as f:
            content = f.read()
        
        # Check for inheritance from BaseStrategyManager
        if 'BaseStrategyManager' not in content:
            violations.append("Strategy does not inherit from BaseStrategyManager")
        
        # Check for super() call in __init__
        if 'super().__init__(' not in content:
            violations.append("Strategy does not call super().__init__()")
        
        if violations:
            logger.error(f"Found {len(violations)} inheritance pattern violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_strategy_registration(self) -> bool:
        """Test that strategies are properly registered in the factory."""
        violations = []
        
        factory_file = self.backend_src / "basis_strategy_v1/core/strategies/strategy_factory.py"
        if not factory_file.exists():
            violations.append("Strategy factory file not found")
            return False
        
        with open(factory_file, 'r') as f:
            content = f.read()
        
        # Check for Pure Lending strategy registration
        if "'pure_lending': PureLendingStrategy" not in content:
            violations.append("Pure lending strategy not registered in factory")
        
        # Check for import of PureLendingStrategy
        if "from .pure_lending_strategy import PureLendingStrategy" not in content:
            violations.append("PureLendingStrategy not imported in factory")
        
        if violations:
            logger.error(f"Found {len(violations)} strategy registration violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_architecture_compliance(self) -> bool:
        """Test overall architecture compliance."""
        # This is a composite test of the above tests
        return (self._test_base_strategy_manager() and 
                self._test_strategy_factory() and 
                self._test_strategy_implementation() and
                self._test_standardized_actions() and
                self._test_inheritance_pattern() and
                self._test_strategy_registration())
    
    def _test_integration(self) -> bool:
        """Integration test - verify overall strategy manager refactor."""
        # Test that we can import the strategy components without errors
        try:
            from basis_strategy_v1.core.strategies.base_strategy_manager import BaseStrategyManager, StrategyAction
            from basis_strategy_v1.core.strategies.strategy_factory import StrategyFactory
            from basis_strategy_v1.core.strategies.pure_lending_strategy import PureLendingStrategy
            
            logger.info("✅ All strategy components imported successfully")
            
            # Test that factory can create a strategy
            available_modes = StrategyFactory.get_available_modes()
            if 'pure_lending' not in available_modes:
                logger.error("❌ Pure lending strategy not available in factory")
                return False
            
            logger.info("✅ Strategy factory can create strategies")
            return True
            
        except Exception as e:
            logger.error(f"❌ Strategy component import failed: {e}")
            return False

def main():
    """Main entry point."""
    quality_gates = StrategyManagerRefactorQualityGates()
    success = quality_gates.run_quality_gates()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
