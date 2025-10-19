#!/usr/bin/env python3
"""
Singleton Pattern Quality Gates

Validates that all components follow the singleton pattern to ensure single instances
across the entire run, preventing data synchronization issues.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 2 (Singleton Pattern)
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

class SingletonPatternQualityGates:
    """Quality gates for singleton pattern implementation."""
    
    def __init__(self):
        self.backend_src = Path(__file__).parent.parent / "backend" / "src"
        self.component_files = [
            "basis_strategy_v1/core/strategies/components/position_monitor.py",
            "basis_strategy_v1/core/strategies/components/risk_monitor.py", 
            "basis_strategy_v1/core/strategies/components/strategy_manager.py",
            "basis_strategy_v1/core/strategies/components/position_update_handler.py",
            "basis_strategy_v1/core/strategies/components/exposure_monitor.py",
            "basis_strategy_v1/core/components/pnl_monitor.py"
        ]
        self.engine_files = [
            "basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py"
        ]
        self.factory_files = [
            "basis_strategy_v1/infrastructure/data/data_provider_factory.py",
            "basis_strategy_v1/infrastructure/config/config_loader.py"
        ]
        
    def run_quality_gates(self) -> bool:
        """Run all singleton pattern quality gates."""
        logger.info("🚀 Starting Singleton Pattern Quality Gates")
        logger.info("=" * 80)
        
        gates = [
            ("QG1", "Component Manager Pattern", self._test_component_manager_pattern),
            ("QG2", "Single Instance Creation", self._test_single_instance_creation),
            ("QG3", "No Duplicate Component Initialization", self._test_no_duplicate_initialization),
            ("QG4", "Shared Config Instance", self._test_shared_config_instance),
            ("QG5", "Shared Data Provider Instance", self._test_shared_data_provider_instance),
            ("QG6", "No Convenience Factory Functions", self._test_no_convenience_factories),
            ("QG7", "Singleton Pattern Compliance", self._test_singleton_compliance),
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
        logger.info("🚦 SINGLETON PATTERN QUALITY GATES RESULTS")
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
            logger.info("🎉 All singleton pattern quality gates passed!")
        
        return passed == total
    
    def _test_component_manager_pattern(self) -> bool:
        """Test that component manager pattern is implemented."""
        violations = []
        
        for file_path in self.engine_files:
            full_path = self.backend_src / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                content = f.read()
                
            # Check that all components are initialized in the engine
            required_components = [
                'PositionMonitor(',
                'ExposureMonitor(',
                'RiskMonitor(',
                'PnLMonitor(',
                'StrategyManager(',
                'PositionUpdateHandler('
            ]
            
            for component in required_components:
                if component not in content:
                    violations.append(f"{file_path}: Missing {component} initialization")
        
        if violations:
            logger.error(f"Found {len(violations)} component manager pattern violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_single_instance_creation(self) -> bool:
        """Test that components are created as single instances."""
        violations = []
        
        for file_path in self.engine_files:
            full_path = self.backend_src / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                content = f.read()
                
            # Check that components are assigned to self (single instance)
            component_assignments = [
                'self.position_monitor =',
                'self.exposure_monitor =',
                'self.risk_monitor =',
                'self.pnl_monitor =',
                'self.strategy_manager =',
                'self.position_update_handler ='
            ]
            
            for assignment in component_assignments:
                if assignment not in content:
                    violations.append(f"{file_path}: Missing {assignment}")
        
        if violations:
            logger.error(f"Found {len(violations)} single instance creation violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_no_duplicate_initialization(self) -> bool:
        """Test that components are not initialized in multiple places."""
        violations = []
        
        # Check for component initialization outside of the main engine
        for file_path in self.component_files:
            full_path = self.backend_src / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                content = f.read()
                
            # Check for component creation patterns
            component_patterns = [
                r'PositionMonitor\(',
                r'RiskMonitor\(',
                r'StrategyManager\(',
                r'ExposureMonitor\(',
                r'PnLMonitor\(',
                r'PositionUpdateHandler\('
            ]
            
            for pattern in component_patterns:
                # Get the component name from the file path
                component_name = Path(file_path).stem.replace('_', '').title()
                if component_name == 'Positionmonitor':
                    component_name = 'PositionMonitor'
                elif component_name == 'Riskmonitor':
                    component_name = 'RiskMonitor'
                elif component_name == 'Strategymanager':
                    component_name = 'StrategyManager'
                elif component_name == 'Exposuremonitor':
                    component_name = 'ExposureMonitor'
                elif component_name == 'PnLMonitor':
                    component_name = 'PnLMonitor'
                elif component_name == 'Positionupdatehandler':
                    component_name = 'PositionUpdateHandler'
                
                # Skip if this is the component's own class definition
                if pattern.replace('\\', '').replace('(', '') == component_name:
                    continue
                    
                if re.search(pattern, content):
                    violations.append(f"{file_path}: Creates {pattern} outside of main engine")
        
        if violations:
            logger.error(f"Found {len(violations)} duplicate initialization violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_shared_config_instance(self) -> bool:
        """Test that all components share the same config instance."""
        violations = []
        
        for file_path in self.engine_files:
            full_path = self.backend_src / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                content = f.read()
                
            # Check that config is passed to all components
            component_initializations = [
                'PositionMonitor(',
                'ExposureMonitor(',
                'RiskMonitor(',
                'PnLMonitor(',
                'StrategyManager(',
                'PositionUpdateHandler('
            ]
            
            for component in component_initializations:
                if component in content:
                    # Check that config is passed to this component
                    pattern = f'{re.escape(component)}[\\s\\S]*?config=self\\.config'
                    if not re.search(pattern, content):
                        violations.append(f"{file_path}: {component} doesn't receive shared config instance")
        
        if violations:
            logger.error(f"Found {len(violations)} shared config instance violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_shared_data_provider_instance(self) -> bool:
        """Test that all components share the same data provider instance."""
        violations = []
        
        for file_path in self.engine_files:
            full_path = self.backend_src / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                content = f.read()
                
            # Check that data_provider is passed to components that need it
            components_needing_data_provider = [
                'PositionMonitor(',
                'ExposureMonitor(',
                'RiskMonitor(',
                'PnLMonitor('
            ]
            
            for component in components_needing_data_provider:
                if component in content:
                    # Check that data_provider is passed to this component
                    pattern = f'{re.escape(component)}[\\s\\S]*?data_provider=self\\.data_provider'
                    if not re.search(pattern, content):
                        violations.append(f"{file_path}: {component} doesn't receive shared data provider instance")
        
        if violations:
            logger.error(f"Found {len(violations)} shared data provider instance violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_no_convenience_factories(self) -> bool:
        """Test that there are no convenience factory functions that could create multiple instances."""
        violations = []
        
        for file_path in self.component_files:
            full_path = self.backend_src / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                content = f.read()
                
            # Check for convenience factory functions
            factory_patterns = [
                r'def create_.*_monitor\(',
                r'def create_.*_calculator\(',
                r'def create_.*_manager\(',
                r'def create_.*_handler\(',
                r'def get_.*_instance\(',
                r'def new_.*_instance\('
            ]
            
            for pattern in factory_patterns:
                if re.search(pattern, content):
                    violations.append(f"{file_path}: Has convenience factory function {pattern}")
        
        if violations:
            logger.error(f"Found {len(violations)} convenience factory violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_singleton_compliance(self) -> bool:
        """Test overall singleton pattern compliance."""
        # This is a composite test of the above tests
        return (self._test_component_manager_pattern() and 
                self._test_single_instance_creation() and 
                self._test_no_duplicate_initialization() and
                self._test_shared_config_instance() and
                self._test_shared_data_provider_instance() and
                self._test_no_convenience_factories())
    
    def _test_integration(self) -> bool:
        """Integration test - verify overall singleton pattern implementation."""
        # Test that we can import the components without errors
        try:
            from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
            from basis_strategy_v1.core.strategies.components.risk_monitor import RiskMonitor
            from basis_strategy_v1.core.strategies.components.strategy_manager import StrategyManager
            from basis_strategy_v1.core.strategies.components.position_update_handler import PositionUpdateHandler
            from basis_strategy_v1.core.components.pnl_monitor import PnLMonitor
            
            logger.info("✅ All components imported successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Component import failed: {e}")
            return False

def main():
    """Main entry point."""
    quality_gates = SingletonPatternQualityGates()
    success = quality_gates.run_quality_gates()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

