#!/usr/bin/env python3
"""
Event-Driven Strategy Engine Compliance Quality Gates

Validates that the Event-Driven Strategy Engine implementation follows
WORKFLOW_REFACTOR_SPECIFICATION.md and includes all P0, P1, P2 fixes.

This quality gate ensures:
- P0 Fixes: No undefined variables, correct async/await, proper initialization
- P1 Fixes: Correct PnL timing, execution success checking, mode-specific triggers, error handlers
- P2 Fixes: Specific exception handling, 60-second refresh, health status updates

Reference: EVENT_ENGINE_COMPLIANCE_AUDIT.md
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class EventEngineComplianceValidator:
    """Validates Event-Driven Strategy Engine compliance with specifications."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.engine_file = project_root / "backend" / "src" / "basis_strategy_v1" / "core" / "event_engine" / "event_driven_strategy_engine.py"
        
    def validate_all(self) -> Dict[str, Any]:
        """Run all Event Engine compliance validations."""
        print("🔍 Validating Event-Driven Strategy Engine Compliance...")
        print(f"📄 File: {self.engine_file}")
        
        if not self.engine_file.exists():
            self.errors.append(f"Event Engine file not found: {self.engine_file}")
            return self._format_results()
        
        with open(self.engine_file, 'r') as f:
            self.content = f.read()
        
        # Parse AST for structural checks
        try:
            self.tree = ast.parse(self.content)
        except SyntaxError as e:
            self.errors.append(f"Syntax error in Event Engine: {e}")
            return self._format_results()
        
        # Run all validations
        print("\n📋 Running P0 (Critical) Validations...")
        self.validate_p0_fixes()
        
        print("📋 Running P1 (Architectural) Validations...")
        self.validate_p1_fixes()
        
        print("📋 Running P2 (Improvement) Validations...")
        self.validate_p2_fixes()
        
        print("📋 Running Component Integration Validations...")
        self.validate_component_integration()
        
        return self._format_results()
    
    def validate_p0_fixes(self):
        """Validate P0 (critical) fixes."""
        print("  ✓ Checking P0.1: No default mode value...")
        self._check_no_default_mode()
        
        print("  ✓ Checking P0.2: Initial capital trigger...")
        self._check_initial_capital_trigger()
        
        print("  ✓ Checking P0.3: strategy_orders used (not strategy_decision)...")
        self._check_strategy_orders_usage()
        
        print("  ✓ Checking P0.4: No await on _process_timestep...")
        self._check_no_await_process_timestep()
    
    def validate_p1_fixes(self):
        """Validate P1 (architectural) fixes."""
        print("  ✓ Checking P1.1: PnL calculated AFTER execution...")
        self._check_pnl_after_execution()
        
        print("  ✓ Checking P1.2: Execution success checking...")
        self._check_execution_success_checking()
        
        print("  ✓ Checking P1.3: Mode-specific triggers...")
        self._check_mode_specific_triggers()
        
        print("  ✓ Checking P1.4: _handle_execution_failure exists...")
        self._check_handle_execution_failure_exists()
        
        print("  ✓ Checking P1.5: _trigger_system_failure exists...")
        self._check_trigger_system_failure_exists()
    
    def validate_p2_fixes(self):
        """Validate P2 (improvement) fixes."""
        print("  ✓ Checking P2.1: Specific exception handling...")
        self._check_specific_exception_handling()
        
        print("  ✓ Checking P2.2: 60-second position refresh in live mode...")
        self._check_60_second_refresh()
        
        print("  ✓ Checking P2.3: Health status updates...")
        self._check_health_status_updates()
    
    def validate_component_integration(self):
        """Validate component integration."""
        print("  ✓ Checking component initialization order...")
        self._check_initialization_order()
        
        print("  ✓ Checking execution_mode passed to components...")
        self._check_execution_mode_passing()
        
        print("  ✓ Checking circular dependency resolution...")
        self._check_circular_dependency_resolution()
    
    # P0 Validation Methods
    
    def _check_no_default_mode(self):
        """Check that strategy manager creation has no default mode."""
        # Look for StrategyFactory.create_strategy call
        pattern = r"StrategyFactory\.create_strategy\([^)]*mode\s*=\s*self\.config\.get\(\s*['\"]mode['\"]\s*,\s*['\"]pure_lending_usdt['\"]\s*\)"
        
        if re.search(pattern, self.content):
            self.errors.append(
                "P0.1 VIOLATION: StrategyFactory.create_strategy still has default mode value 'pure_lending_usdt'. "
                "Should be: mode=self.config.get('mode') # FAIL FAST - no default"
            )
    
    def _check_initial_capital_trigger(self):
        """Check that backtest initializes with initial_capital trigger."""
        # Look for initial_capital trigger in run_backtest
        if "update_state(start_dt, 'initial_capital', None)" not in self.content and \
           'update_state(start_dt, "initial_capital", None)' not in self.content:
            self.errors.append(
                "P0.2 VIOLATION: Backtest does not initialize with initial_capital trigger. "
                "Should call: self.position_monitor.update_state(start_dt, 'initial_capital', None)"
            )
    
    def _check_strategy_orders_usage(self):
        """Check that _process_timestep uses strategy_orders not strategy_decision."""
        # Remove comments and docstrings to avoid false positives
        content_no_comments = re.sub(r'#.*', '', self.content)
        content_no_comments = re.sub(r'""".*?"""', '', content_no_comments, flags=re.DOTALL)
        content_no_comments = re.sub(r"'''.*?'''", '', content_no_comments, flags=re.DOTALL)
        
        # Check for actual usage of undefined strategy_decision (not in comments/docstrings)
        if re.search(r'\bstrategy_decision\b', content_no_comments) and \
           'strategy_decision: Dict' not in content_no_comments and \
           'strategy_decision: List' not in content_no_comments:
            # If strategy_decision is used but not defined as parameter
            self.errors.append(
                "P0.3 VIOLATION: Code uses undefined 'strategy_decision' variable. "
                "Should use 'strategy_orders' instead."
            )
        
        # Check for undefined action
        if re.search(r'_store_timestep_result\([^)]*\baction\b[^)]*\)', content_no_comments):
            self.errors.append(
                "P0.3 VIOLATION: _store_timestep_result called with undefined 'action' parameter."
            )
    
    def _check_no_await_process_timestep(self):
        """Check that run_live doesn't await _process_timestep."""
        # Look for await self._process_timestep in run_live
        pattern = r'def run_live.*?(?=\n    def|\Z)'
        match = re.search(pattern, self.content, re.DOTALL)
        
        if match:
            run_live_code = match.group(0)
            if 'await self._process_timestep' in run_live_code:
                self.errors.append(
                    "P0.4 VIOLATION: run_live calls 'await self._process_timestep' but _process_timestep is not async. "
                    "Should be: self._process_timestep(...) without await"
                )
    
    # P1 Validation Methods
    
    def _check_pnl_after_execution(self):
        """Check that PnL is calculated only AFTER execution."""
        # Find _process_timestep method
        pattern = r'def _process_timestep.*?(?=\n    def|\Z)'
        match = re.search(pattern, self.content, re.DOTALL)
        
        if not match:
            self.errors.append("P1.1 ERROR: _process_timestep method not found")
            return
        
        process_timestep_code = match.group(0)
        
        # Find all PnL calculation calls
        pnl_calculations = list(re.finditer(r'pnl\s*=\s*self\.pnl_monitor\.calculate_pnl', process_timestep_code))
        
        if len(pnl_calculations) > 1:
            self.errors.append(
                f"P1.1 VIOLATION: PnL calculated {len(pnl_calculations)} times in _process_timestep. "
                "Should be calculated exactly ONCE after execution."
            )
        elif len(pnl_calculations) == 0:
            self.errors.append(
                "P1.1 VIOLATION: PnL not calculated in _process_timestep."
            )
        else:
            # Check that PnL is calculated AFTER process_orders
            pnl_pos = pnl_calculations[0].start()
            process_orders_matches = list(re.finditer(r'self\.venue_manager\.process_orders', process_timestep_code))
            
            if process_orders_matches:
                last_process_orders_pos = process_orders_matches[-1].end()
                if pnl_pos < last_process_orders_pos:
                    self.errors.append(
                        "P1.1 VIOLATION: PnL calculated BEFORE process_orders. "
                        "Should be calculated AFTER execution to include execution costs."
                    )
    
    def _check_execution_success_checking(self):
        """Check that execution result success is checked."""
        # Look for success checking after process_orders
        pattern = r'process_orders\([^)]*\).*?(?:if|assert).*?\.get\([\'"]success[\'"]\)'
        
        if not re.search(pattern, self.content, re.DOTALL):
            self.errors.append(
                "P1.2 VIOLATION: Execution result success not checked after process_orders. "
                "Should check: if not execution_result.get('success'):"
            )
    
    def _check_mode_specific_triggers(self):
        """Check for mode-specific trigger logic."""
        # Look for execution_mode conditional in _process_timestep
        pattern = r'def _process_timestep.*?if self\.execution_mode.*?position_refresh'
        
        if not re.search(pattern, self.content, re.DOTALL):
            self.warnings.append(
                "P1.3 WARNING: Mode-specific trigger logic not found. "
                "Backtest should not use position_refresh trigger."
            )
    
    def _check_handle_execution_failure_exists(self):
        """Check that _handle_execution_failure method exists."""
        if '_handle_execution_failure' not in self.content or \
           'def _handle_execution_failure' not in self.content:
            self.errors.append(
                "P1.4 VIOLATION: _handle_execution_failure method not found. "
                "This method is required per WORKFLOW_REFACTOR_SPECIFICATION.md"
            )
    
    def _check_trigger_system_failure_exists(self):
        """Check that _trigger_system_failure method exists."""
        if '_trigger_system_failure' not in self.content or \
           'def _trigger_system_failure' not in self.content:
            self.errors.append(
                "P1.5 VIOLATION: _trigger_system_failure method not found. "
                "This method is required per WORKFLOW_REFACTOR_SPECIFICATION.md"
            )
        
        # Check that it raises SystemExit
        pattern = r'def _trigger_system_failure.*?raise SystemExit'
        if not re.search(pattern, self.content, re.DOTALL):
            self.warnings.append(
                "P1.5 WARNING: _trigger_system_failure might not raise SystemExit. "
                "Should raise SystemExit to trigger deployment restart."
            )
    
    # P2 Validation Methods
    
    def _check_specific_exception_handling(self):
        """Check for specific exception handling (ValueError, KeyError)."""
        # Look for specific exception handling in _process_timestep
        pattern = r'def _process_timestep.*?except\s+ValueError'
        
        if not re.search(pattern, self.content, re.DOTALL):
            self.warnings.append(
                "P2.1 WARNING: Specific ValueError exception handling not found in _process_timestep. "
                "Should have: except ValueError as e: ... raise"
            )
        
        pattern = r'def _process_timestep.*?except\s+KeyError'
        
        if not re.search(pattern, self.content, re.DOTALL):
            self.warnings.append(
                "P2.1 WARNING: Specific KeyError exception handling not found in _process_timestep. "
                "Should have: except KeyError as e: ... raise"
            )
    
    def _check_60_second_refresh(self):
        """Check for 60-second position refresh in live mode."""
        # Look for position_refresh in run_live
        pattern = r'def run_live.*?position_refresh'
        
        if not re.search(pattern, self.content, re.DOTALL):
            self.warnings.append(
                "P2.2 WARNING: 60-second position refresh not found in run_live. "
                "Live mode should independently refresh positions every 60 seconds."
            )
    
    def _check_health_status_updates(self):
        """Check that health status is updated on errors."""
        # Look for health_status updates in _handle_error or _handle_execution_failure
        if 'self.health_status = "degraded"' not in self.content and \
           'self.health_status = "critical"' not in self.content:
            self.warnings.append(
                "P2.3 WARNING: Health status updates not found. "
                "Should update health_status on errors (degraded, critical)."
            )
    
    # Component Integration Validation Methods
    
    def _check_initialization_order(self):
        """Check that components are initialized in correct order (5 phases)."""
        # Phase 1: utility_manager, venue_interface_factory
        # Phase 2: position_monitor, event_logger, exposure_monitor, risk_monitor, pnl_monitor
        # Phase 3: venue_interface_manager, venue_manager
        # Phase 4: position_update_handler, circular reference
        # Phase 5: strategy_manager, results_store
        
        init_method = self._find_method('__init__')
        if not init_method:
            self.errors.append("__init__ method not found")
            return
        
        # Check Phase 1
        if 'self.utility_manager' not in init_method:
            self.errors.append("Phase 1: utility_manager not initialized")
        if 'self.venue_interface_factory' not in init_method:
            self.errors.append("Phase 1: venue_interface_factory not initialized")
    
    def _check_execution_mode_passing(self):
        """Check that execution_mode is passed to required components."""
        init_method = self._find_method('__init__')
        if not init_method:
            return
        
        # Check that execution_mode is passed to PositionMonitor
        if 'PositionMonitor(' in init_method:
            pm_pattern = r'PositionMonitor\([^)]*execution_mode'
            if not re.search(pm_pattern, init_method):
                # Check if it's passed positionally
                if 'self.execution_mode' not in init_method:
                    self.errors.append("execution_mode not passed to PositionMonitor")
    
    def _check_circular_dependency_resolution(self):
        """Check that circular dependency is resolved correctly."""
        init_method = self._find_method('__init__')
        if not init_method:
            return
        
        # Check that VenueManager is created with position_update_handler=None
        if 'position_update_handler=None' not in init_method:
            self.errors.append("VenueManager not created with position_update_handler=None")
        
        # Check that circular reference is set after both exist
        if 'self.venue_manager.position_update_handler = self.position_update_handler' not in init_method:
            self.errors.append("Circular reference not established after both components exist")
    
    # Helper Methods
    
    def _find_method(self, method_name: str) -> str:
        """Find method code by name."""
        pattern = f'def {method_name}.*?(?=\n    def|\Z)'
        match = re.search(pattern, self.content, re.DOTALL)
        return match.group(0) if match else ""
    
    def _format_results(self) -> Dict[str, Any]:
        """Format validation results."""
        success = len(self.errors) == 0
        
        print("\n" + "="*80)
        if success:
            print("✅ Event Engine Compliance: PASSED")
        else:
            print("❌ Event Engine Compliance: FAILED")
        print("="*80)
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if success and not self.warnings:
            print("\n✨ All checks passed! Event Engine is fully compliant.")
        
        return {
            "success": success,
            "errors": self.errors,
            "warnings": self.warnings,
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "compliance_percentage": self._calculate_compliance()
        }
    
    def _calculate_compliance(self) -> float:
        """Calculate compliance percentage."""
        total_checks = 15  # P0(4) + P1(5) + P2(3) + Integration(3)
        errors = len(self.errors)
        warnings = len(self.warnings)
        
        # Errors count as full failures, warnings as half failures
        failures = errors + (warnings * 0.5)
        compliance = max(0, (total_checks - failures) / total_checks * 100)
        
        return round(compliance, 2)


def main():
    """Run Event Engine compliance quality gates."""
    validator = EventEngineComplianceValidator()
    results = validator.validate_all()
    
    # Exit with error code if validation failed
    sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()

