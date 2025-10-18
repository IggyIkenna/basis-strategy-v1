#!/usr/bin/env python3
"""
Workflow Architecture Quality Gates

Validates that the workflow architecture matches the documented specifications
in WORKFLOW_REFACTOR_SPECIFICATION.md and WORKFLOW_GUIDE.md.
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class WorkflowArchitectureValidator:
    """Validates workflow architecture compliance."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.backend_path = project_root / "backend" / "src" / "basis_strategy_v1"
        self.docs_path = project_root / "docs"
        
    def validate_all(self) -> Dict[str, Any]:
        """Run all workflow architecture validations."""
        print("🔍 Validating Workflow Architecture...")
        
        # Core workflow validations
        self.validate_event_driven_strategy_engine()
        self.validate_venue_manager_workflow()
        self.validate_position_update_handler_workflow()
        self.validate_position_monitor_triggers()
        self.validate_order_based_workflow()
        self.validate_tight_loop_architecture()
        self.validate_mode_specific_behavior()
        self.validate_component_initialization()
        self.validate_data_flow_patterns()
        self.validate_error_handling_patterns()
        
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "success": len(self.errors) == 0
        }
    
    def validate_event_driven_strategy_engine(self):
        """Validate EventDrivenStrategyEngine workflow compliance."""
        engine_file = self.backend_path / "core" / "event_engine" / "event_driven_strategy_engine.py"
        
        if not engine_file.exists():
            self.errors.append("EventDrivenStrategyEngine file not found")
            return
            
        with open(engine_file, 'r') as f:
            content = f.read()
        
        # Check for proper component initialization
        if "execution_mode" not in content:
            self.errors.append("EventDrivenStrategyEngine missing execution_mode parameter")
        
        if "initial_capital" not in content:
            self.errors.append("EventDrivenStrategyEngine missing initial_capital parameter")
        
        # Check for proper method calls in _process_timestep
        if "venue_manager.process_orders" not in content:
            self.errors.append("EventDrivenStrategyEngine not calling venue_manager.process_orders")
        
        if "pnl_monitor.calculate_pnl" not in content:
            self.errors.append("EventDrivenStrategyEngine missing PnL calculation")
        
        # Check for removed methods
        removed_methods = ["_trigger_tight_loop", "_create_position_monitor", "_create_venue_manager"]
        for method in removed_methods:
            if method in content:
                self.errors.append(f"EventDrivenStrategyEngine still contains removed method: {method}")
    
    def validate_venue_manager_workflow(self):
        """Validate VenueManager workflow compliance."""
        manager_file = self.backend_path / "core" / "execution" / "venue_manager.py"
        
        if not manager_file.exists():
            self.errors.append("VenueManager file not found")
            return
            
        with open(manager_file, 'r') as f:
            content = f.read()
        
        # Check for Order-based workflow
        if "process_orders" not in content:
            self.errors.append("VenueManager missing process_orders method")
        
        if "List[Order]" not in content:
            self.errors.append("VenueManager not using Order objects")
        
        # Check for retry logic
        if "_reconcile_with_retry" not in content:
            self.errors.append("VenueManager missing retry logic")
        
        # Check for system failure handling
        if "_trigger_system_failure" not in content:
            self.errors.append("VenueManager missing system failure handling")
        
        # Check for removed methods
        removed_methods = ["execute_venue_instructions", "_process_queued_blocks", "_update_position_monitor"]
        for method in removed_methods:
            if method in content:
                self.errors.append(f"VenueManager still contains removed method: {method}")
    
    def validate_position_update_handler_workflow(self):
        """Validate PositionUpdateHandler workflow compliance."""
        handler_file = self.backend_path / "core" / "components" / "position_update_handler.py"
        
        if not handler_file.exists():
            self.errors.append("PositionUpdateHandler file not found")
            return
            
        with open(handler_file, 'r') as f:
            content = f.read()
        
        # Check for proper trigger handling
        if "trigger_source" not in content:
            self.errors.append("PositionUpdateHandler missing trigger_source parameter")
        
        if "venue_manager" not in content or "position_refresh" not in content:
            self.errors.append("PositionUpdateHandler missing required trigger sources")
        
        # Check for reconciliation logic
        if "_reconcile_positions" not in content:
            self.errors.append("PositionUpdateHandler missing reconciliation logic")
        
        # Check for removed methods
        removed_methods = ["_handle_atomic_position_update", "_trigger_tight_loop_after_atomic", "_execute_tight_loop"]
        for method in removed_methods:
            if method in content:
                self.errors.append(f"PositionUpdateHandler still contains removed method: {method}")
    
    def validate_position_monitor_triggers(self):
        """Validate PositionMonitor trigger handling."""
        monitor_file = self.backend_path / "core" / "components" / "position_monitor.py"
        
        if not monitor_file.exists():
            self.errors.append("PositionMonitor file not found")
            return
            
        with open(monitor_file, 'r') as f:
            content = f.read()
        
        # Check for all 5 trigger sources
        required_triggers = ["venue_manager", "position_refresh", "initial_capital", "seasonal_rewards", "m2m_pnl"]
        for trigger in required_triggers:
            if trigger not in content:
                self.errors.append(f"PositionMonitor missing trigger: {trigger}")
        
        # Check for execution_mode parameter
        if "execution_mode" not in content:
            self.errors.append("PositionMonitor missing execution_mode parameter")
        
        # Check for initial_capital parameter
        if "initial_capital" not in content:
            self.errors.append("PositionMonitor missing initial_capital parameter")
        
        # Check for new methods
        required_methods = ["_apply_execution_deltas", "_query_venue_balances", "_apply_initial_capital"]
        for method in required_methods:
            if method not in content:
                self.errors.append(f"PositionMonitor missing method: {method}")
    
    def validate_order_based_workflow(self):
        """Validate Order-based workflow implementation."""
        # Check VenueInterfaceManager
        interface_file = self.backend_path / "core" / "execution" / "venue_interface_manager.py"
        
        if not interface_file.exists():
            self.errors.append("VenueInterfaceManager file not found")
            return
            
        with open(interface_file, 'r') as f:
            content = f.read()
        
        # Check for Order routing
        if "route_to_venue" not in content:
            self.errors.append("VenueInterfaceManager missing route_to_venue method")
        
        if "Order" not in content:
            self.errors.append("VenueInterfaceManager not using Order objects")
        
        # Check for removed methods
        removed_methods = ["execute_venue_instructions", "_process_queued_blocks"]
        for method in removed_methods:
            if method in content:
                self.errors.append(f"VenueInterfaceManager still contains removed method: {method}")
    
    def validate_tight_loop_architecture(self):
        """Validate tight loop architecture compliance."""
        # Check that tight loop is centralized in PositionUpdateHandler
        handler_file = self.backend_path / "core" / "components" / "position_update_handler.py"
        
        if not handler_file.exists():
            self.errors.append("PositionUpdateHandler file not found")
            return
            
        with open(handler_file, 'r') as f:
            content = f.read()
        
        # Check for tight loop orchestration
        if "update_state" not in content:
            self.errors.append("PositionUpdateHandler missing update_state method")
        
        # Check that VenueManager calls PositionUpdateHandler
        manager_file = self.backend_path / "core" / "execution" / "venue_manager.py"
        
        if not manager_file.exists():
            self.errors.append("VenueManager file not found")
            return
            
        with open(manager_file, 'r') as f:
            content = f.read()
        
        if "position_update_handler.update_state" not in content:
            self.errors.append("VenueManager not calling PositionUpdateHandler.update_state")
    
    def validate_mode_specific_behavior(self):
        """Validate mode-specific behavior implementation."""
        # Check PositionMonitor for mode-specific logic
        monitor_file = self.backend_path / "core" / "components" / "position_monitor.py"
        
        if not monitor_file.exists():
            self.errors.append("PositionMonitor file not found")
            return
            
        with open(monitor_file, 'r') as f:
            content = f.read()
        
        # Check for execution_mode usage
        if "execution_mode" not in content:
            self.errors.append("PositionMonitor missing execution_mode usage")
        
        # Check for backtest vs live mode handling
        if "backtest" not in content or "live" not in content:
            self.errors.append("PositionMonitor missing mode-specific handling")
    
    def validate_component_initialization(self):
        """Validate component initialization sequence."""
        engine_file = self.backend_path / "core" / "event_engine" / "event_driven_strategy_engine.py"
        
        if not engine_file.exists():
            self.errors.append("EventDrivenStrategyEngine file not found")
            return
            
        with open(engine_file, 'r') as f:
            content = f.read()
        
        # Check for proper initialization sequence
        if "PositionMonitor" not in content:
            self.errors.append("EventDrivenStrategyEngine missing PositionMonitor initialization")
        
        if "VenueManager" not in content:
            self.errors.append("EventDrivenStrategyEngine missing VenueManager initialization")
        
        if "PositionUpdateHandler" not in content:
            self.errors.append("EventDrivenStrategyEngine missing PositionUpdateHandler initialization")
        
        # Check for circular dependency handling
        if "position_update_handler" not in content:
            self.errors.append("EventDrivenStrategyEngine missing circular dependency handling")
    
    def validate_data_flow_patterns(self):
        """Validate data flow patterns."""
        # Check that market_data parameter passing is removed
        files_to_check = [
            "venue_interface_manager.py",
            "position_update_handler.py",
            "venue_manager.py"
        ]
        
        for filename in files_to_check:
            file_path = self.backend_path / "core" / "execution" / filename
            if not file_path.exists():
                file_path = self.backend_path / "core" / "components" / filename
            
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for removed market_data parameter
                if "market_data" in content and "def " in content:
                    # Look for function definitions with market_data parameter
                    if re.search(r'def\s+\w+.*market_data', content):
                        self.errors.append(f"{filename} still has market_data parameter passing")
    
    def validate_error_handling_patterns(self):
        """Validate error handling patterns."""
        # Check VenueManager for error handling
        manager_file = self.backend_path / "core" / "execution" / "venue_manager.py"
        
        if not manager_file.exists():
            self.errors.append("VenueManager file not found")
            return
            
        with open(manager_file, 'r') as f:
            content = f.read()
        
        # Check for error handling methods
        if "_handle_error" not in content:
            self.errors.append("VenueManager missing error handling")
        
        # Check for health status updates
        if "health_status" not in content:
            self.errors.append("VenueManager missing health status updates")
        
        # Check for system failure handling
        if "SystemExit" not in content:
            self.errors.append("VenueManager missing system failure handling")

def main():
    """Main entry point for workflow architecture validation."""
    validator = WorkflowArchitectureValidator()
    results = validator.validate_all()
    
    print(f"\n📊 Workflow Architecture Validation Results:")
    print(f"   Errors: {results['total_errors']}")
    print(f"   Warnings: {results['total_warnings']}")
    
    if results['errors']:
        print(f"\n❌ Errors found:")
        for error in results['errors']:
            print(f"   - {error}")
    
    if results['warnings']:
        print(f"\n⚠️  Warnings found:")
        for warning in results['warnings']:
            print(f"   - {warning}")
    
    if results['success']:
        print(f"\n✅ Workflow architecture validation passed!")
        print(f"   All components follow the documented workflow architecture")
        print(f"SUCCESS: All workflow architecture quality gates passed!")
        return 0
    else:
        print(f"\n❌ Workflow architecture validation failed!")
        print(f"   {results['total_errors']} errors need to be fixed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
