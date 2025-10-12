#!/usr/bin/env python3
"""
Reference-Based Architecture Quality Gates

Validates that all components follow the reference-based architecture pattern:
- Store references in __init__
- Never pass references as runtime parameters
- Never create their own instances of shared resources

Reference: docs/ARCHITECTURAL_DECISION_RECORDS.md - ADR-003 Reference-Based Architecture
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

class ReferenceArchitectureQualityGates:
    """Quality gates for reference-based architecture."""
    
    def __init__(self):
        self.backend_src = Path(__file__).parent.parent / "backend" / "src"
        self.component_files = [
            "basis_strategy_v1/core/components/position_monitor.py",
            "basis_strategy_v1/core/components/risk_monitor.py", 
            "basis_strategy_v1/core/strategies/base_strategy_manager.py",
            "basis_strategy_v1/core/components/position_update_handler.py",
            "basis_strategy_v1/core/components/exposure_monitor.py",
            "basis_strategy_v1/core/math/pnl_calculator.py"
        ]
        self.engine_files = [
            "basis_strategy_v1/core/event_engine/event_driven_strategy_engine.py"
        ]
        
    def run_quality_gates(self) -> bool:
        """Run all reference-based architecture quality gates."""
        logger.info("🚀 Starting Reference-Based Architecture Quality Gates")
        logger.info("=" * 80)
        
        gates = [
            ("QG1", "Components Store References in __init__", self._test_components_store_references),
            ("QG2", "No Runtime Parameter Passing", self._test_no_runtime_parameter_passing),
            ("QG3", "No Own Instance Creation", self._test_no_own_instance_creation),
            ("QG4", "Single Config Instance", self._test_single_config_instance),
            ("QG5", "Single Data Provider Instance", self._test_single_data_provider_instance),
            ("QG6", "Component Reference Sharing", self._test_component_reference_sharing),
            ("QG7", "ADR-003 Compliance", self._test_adr003_compliance),
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
        logger.info("🚦 REFERENCE-BASED ARCHITECTURE QUALITY GATES RESULTS")
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
            logger.info("🎉 All reference-based architecture quality gates passed!")
        
        return passed == total
    
    def _test_components_store_references(self) -> bool:
        """Test that components store references in __init__."""
        violations = []
        
        for file_path in self.component_files:
            full_path = self.backend_src / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                content = f.read()
                
            # Check if component has __init__ method
            if 'def __init__' not in content:
                violations.append(f"{file_path}: No __init__ method found")
                continue
                
            # Check if component stores config reference
            if 'self.config = config' not in content and 'self.config =' not in content:
                violations.append(f"{file_path}: No config reference storage in __init__")
                
            # Check if component stores data_provider reference (if it uses one)
            if 'data_provider' in content and 'self.data_provider =' not in content:
                violations.append(f"{file_path}: Uses data_provider but doesn't store reference")
        
        if violations:
            logger.error(f"Found {len(violations)} reference storage violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_no_runtime_parameter_passing(self) -> bool:
        """Test that references are not passed as runtime parameters."""
        violations = []
        
        for file_path in self.component_files:
            full_path = self.backend_src / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines, 1):
                # Skip __init__ methods (they should receive references)
                if 'def __init__' in line:
                    continue
                    
                # Check for method definitions that pass references as parameters
                if re.search(r'def \w+\(.*config.*\)', line):
                    violations.append(f"{file_path}:{i}: Method passes config as parameter")
                if re.search(r'def \w+\(.*data_provider.*\)', line):
                    violations.append(f"{file_path}:{i}: Method passes data_provider as parameter")
                if re.search(r'def \w+\(.*position_monitor.*\)', line):
                    violations.append(f"{file_path}:{i}: Method passes position_monitor as parameter")
                if re.search(r'def \w+\(.*risk_monitor.*\)', line):
                    violations.append(f"{file_path}:{i}: Method passes risk_monitor as parameter")
        
        if violations:
            logger.error(f"Found {len(violations)} runtime parameter passing violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_no_own_instance_creation(self) -> bool:
        """Test that components don't create their own instances."""
        violations = []
        
        for file_path in self.component_files:
            full_path = self.backend_src / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                content = f.read()
                
            # Get the component class name from the file path
            component_name = Path(file_path).stem.replace('_', '').title()
            if component_name == 'Positionmonitor':
                component_name = 'PositionMonitor'
            elif component_name == 'Riskmonitor':
                component_name = 'RiskMonitor'
            elif component_name == 'Strategymanager':
                component_name = 'StrategyManager'
            elif component_name == 'Exposuremonitor':
                component_name = 'ExposureMonitor'
            elif component_name == 'Pnlcalculator':
                component_name = 'PnLCalculator'
            elif component_name == 'Eventlogger':
                component_name = 'EventLogger'
            elif component_name == 'Positionupdatehandler':
                component_name = 'PositionUpdateHandler'
                
            # Check for instance creation patterns (excluding class definitions)
            instance_patterns = [
                r'DataProvider\(',
                r'ConfigLoader\(',
                r'PositionMonitor\(',
                r'RiskMonitor\(',
                r'StrategyManager\(',
                r'ExposureMonitor\(',
                r'PnLCalculator\(',
                r'EventLogger\(',
                r'PositionUpdateHandler\('
            ]
            
            for pattern in instance_patterns:
                # Skip if this is the component's own class definition
                if pattern.replace('\\', '').replace('(', '') == component_name:
                    continue
                    
                if re.search(pattern, content):
                    violations.append(f"{file_path}: Creates own instance with {pattern}")
        
        if violations:
            logger.error(f"Found {len(violations)} own instance creation violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_single_config_instance(self) -> bool:
        """Test that single config instance is shared."""
        # This is validated by the event engine initialization pattern
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
                'RiskMonitor(',
                'StrategyManager(',
                'PnLCalculator(',
                'ExposureMonitor('
            ]
            
            for component in component_initializations:
                if component in content:
                    # Check that config is passed to this component
                    pattern = f'{re.escape(component)}[\\s\\S]*?config=self\\.config'
                    if not re.search(pattern, content):
                        violations.append(f"{file_path}: {component} doesn't receive config reference")
        
        if violations:
            logger.error(f"Found {len(violations)} single config instance violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_single_data_provider_instance(self) -> bool:
        """Test that single data provider instance is shared."""
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
                'RiskMonitor(',
                'PnLCalculator(',
                'ExposureMonitor('
            ]
            
            for component in components_needing_data_provider:
                if component in content:
                    # Check that data_provider is passed to this component
                    pattern = f'{re.escape(component)}[\\s\\S]*?data_provider=self\\.data_provider'
                    if not re.search(pattern, content):
                        violations.append(f"{file_path}: {component} doesn't receive data_provider reference")
        
        if violations:
            logger.error(f"Found {len(violations)} single data provider instance violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_component_reference_sharing(self) -> bool:
        """Test that component references are properly shared."""
        violations = []
        
        for file_path in self.engine_files:
            full_path = self.backend_src / file_path
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                content = f.read()
                
            # Check that RiskMonitor receives position_monitor and exposure_monitor references
            if 'RiskMonitor(' in content:
                if 'position_monitor=self.position_monitor' not in content:
                    violations.append(f"{file_path}: RiskMonitor doesn't receive position_monitor reference")
                if 'exposure_monitor=self.exposure_monitor' not in content:
                    violations.append(f"{file_path}: RiskMonitor doesn't receive exposure_monitor reference")
            
            # Check that StrategyManager receives component references
            if 'StrategyManager(' in content:
                if 'exposure_monitor=self.exposure_monitor' not in content:
                    violations.append(f"{file_path}: StrategyManager doesn't receive exposure_monitor reference")
                if 'risk_monitor=self.risk_monitor' not in content:
                    violations.append(f"{file_path}: StrategyManager doesn't receive risk_monitor reference")
        
        if violations:
            logger.error(f"Found {len(violations)} component reference sharing violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            return False
        
        return True
    
    def _test_adr003_compliance(self) -> bool:
        """Test ADR-003 compliance."""
        # This is a composite test of the above tests
        return (self._test_components_store_references() and 
                self._test_no_runtime_parameter_passing() and 
                self._test_no_own_instance_creation() and
                self._test_single_config_instance() and
                self._test_single_data_provider_instance() and
                self._test_component_reference_sharing())
    
    def _test_integration(self) -> bool:
        """Integration test - verify overall reference-based architecture."""
        # Test that we can import the components without errors
        try:
            from basis_strategy_v1.core.components.position_monitor import PositionMonitor
            from basis_strategy_v1.core.components.risk_monitor import RiskMonitor
            from basis_strategy_v1.core.strategies.base_strategy_manager import BaseStrategyManager
            from basis_strategy_v1.core.components.position_update_handler import PositionUpdateHandler
            from basis_strategy_v1.core.math.pnl_calculator import PnLCalculator
            
            logger.info("✅ All components imported successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Component import failed: {e}")
            return False

def main():
    """Main entry point."""
    quality_gates = ReferenceArchitectureQualityGates()
    success = quality_gates.run_quality_gates()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
