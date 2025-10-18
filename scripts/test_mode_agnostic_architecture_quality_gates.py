#!/usr/bin/env python3
"""
Mode-Agnostic Architecture Quality Gates

Tests that components follow mode-agnostic architecture principles:
- Generic components are mode-agnostic
- Components use centralized utility manager
- No mode-specific logic in generic components
- Config-driven parameters instead of hardcoded mode logic

Reference: .cursor/tasks/08_mode_agnostic_architecture.md
Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7
"""

import sys
import os
import inspect
from pathlib import Path
from typing import Dict, Any, List
import logging
import pandas as pd

# Add the backend source to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from basis_strategy_v1.core.utilities.utility_manager import UtilityManager
from basis_strategy_v1.core.components.position_monitor import PositionMonitor
from basis_strategy_v1.core.components.risk_monitor import RiskMonitor
from basis_strategy_v1.core.components.exposure_monitor import ExposureMonitor
from basis_strategy_v1.core.components.pnl_monitor import PnLCalculator
from basis_strategy_v1.core.strategies.pure_lending_usdt_strategy import PureLendingStrategy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModeAgnosticArchitectureQualityGates:
    """Quality gates for mode-agnostic architecture."""
    
    def __init__(self):
        self.test_results = []
        
    def log_test_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
    
    def test_utility_manager_centralized(self) -> bool:
        """Test that utility manager provides centralized methods."""
        print("\n🔍 Testing Utility Manager Centralization...")
        
        try:
            # Create utility manager
            config = {'mode': 'test', 'share_class': 'USDT', 'asset': 'USDT'}
            utility_manager = UtilityManager(config, None)
            
            # Check that utility manager has all required centralized methods
            required_methods = [
                'get_liquidity_index',
                'get_market_price',
                'convert_to_usdt',
                'convert_from_liquidity_index',
                'convert_to_share_class',
                'get_share_class_from_mode',
                'get_asset_from_mode',
                'get_lst_type_from_mode',
                'get_hedge_allocation_from_mode',
                'calculate_total_usdt_balance',
                'calculate_total_share_class_balance',
                'get_venue_configs_from_mode',
                'get_data_requirements_from_mode'
            ]
            
            all_methods_present = True
            for method_name in required_methods:
                if hasattr(utility_manager, method_name):
                    self.log_test_result(f"UtilityManager.{method_name}", True, "Method present")
                else:
                    self.log_test_result(f"UtilityManager.{method_name}", False, "Method missing")
                    all_methods_present = False
            
            return all_methods_present
            
        except Exception as e:
            self.log_test_result("Utility Manager Centralization", False, f"Exception: {e}")
            return False
    
    def test_components_use_utility_manager(self) -> bool:
        """Test that components use centralized utility manager."""
        print("\n🔍 Testing Component Utility Manager Usage...")
        
        try:
            # Test Position Monitor
            config = {'mode': 'test', 'share_class': 'USDT', 'asset': 'USDT'}
            position_monitor = PositionMonitor(config, None, None)
            
            if hasattr(position_monitor, 'utility_manager'):
                self.log_test_result("PositionMonitor.utility_manager", True, "Uses utility manager")
            else:
                self.log_test_result("PositionMonitor.utility_manager", False, "Missing utility manager")
                return False
            
            # Test Risk Monitor
            risk_monitor = RiskMonitor(config, None, None)
            
            if hasattr(risk_monitor, 'utility_manager'):
                self.log_test_result("RiskMonitor.utility_manager", True, "Uses utility manager")
            else:
                self.log_test_result("RiskMonitor.utility_manager", False, "Missing utility manager")
                return False
            
            # Test Exposure Monitor
            exposure_monitor = ExposureMonitor(config, None, None)
            
            if hasattr(exposure_monitor, 'utility_manager'):
                self.log_test_result("ExposureMonitor.utility_manager", True, "Uses utility manager")
            else:
                self.log_test_result("ExposureMonitor.utility_manager", False, "Missing utility manager")
                return False
            
            # Test P&L Calculator
            pnl_monitor = PnLCalculator(config, 'USDT', 1000.0, None, None)
            
            if hasattr(pnl_monitor, 'utility_manager'):
                self.log_test_result("PnLCalculator.utility_manager", True, "Uses utility manager")
            else:
                self.log_test_result("PnLCalculator.utility_manager", False, "Missing utility manager")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Component Utility Manager Usage", False, f"Exception: {e}")
            return False
    
    def test_no_mode_specific_logic_in_generic_components(self) -> bool:
        """Test that generic components don't have mode-specific logic."""
        print("\n🔍 Testing No Mode-Specific Logic in Generic Components...")
        
        try:
            # Test Position Monitor for mode-specific logic
            config = {'mode': 'test', 'share_class': 'USDT', 'asset': 'USDT'}
            position_monitor = PositionMonitor(config, None, None)
            
            # Check if Position Monitor has mode-specific methods
            position_methods = [method for method in dir(position_monitor) if not method.startswith('_')]
            
            mode_specific_methods = [method for method in position_methods if 'mode' in method.lower() or 'strategy' in method.lower()]
            
            if mode_specific_methods:
                self.log_test_result("PositionMonitor mode-specific methods", False, f"Found: {mode_specific_methods}")
                return False
            else:
                self.log_test_result("PositionMonitor mode-specific methods", True, "No mode-specific methods found")
            
            # Test Risk Monitor for mode-specific logic
            risk_monitor = RiskMonitor(config, None, None)
            
            risk_methods = [method for method in dir(risk_monitor) if not method.startswith('_')]
            mode_specific_methods = [method for method in risk_methods 
                                   if ('mode' in method.lower() or 'strategy' in method.lower()) 
                                   and 'aave' not in method.lower()]
            
            if mode_specific_methods:
                self.log_test_result("RiskMonitor mode-specific methods", False, f"Found: {mode_specific_methods}")
                return False
            else:
                self.log_test_result("RiskMonitor mode-specific methods", True, "No mode-specific methods found")
            
            # Test Exposure Monitor for mode-specific logic
            exposure_monitor = ExposureMonitor(config, None, None)
            
            exposure_methods = [method for method in dir(exposure_monitor) if not method.startswith('_')]
            mode_specific_methods = [method for method in exposure_methods if 'mode' in method.lower() or 'strategy' in method.lower()]
            
            if mode_specific_methods:
                self.log_test_result("ExposureMonitor mode-specific methods", False, f"Found: {mode_specific_methods}")
                return False
            else:
                self.log_test_result("ExposureMonitor mode-specific methods", True, "No mode-specific methods found")
            
            return True
            
        except Exception as e:
            self.log_test_result("No Mode-Specific Logic in Generic Components", False, f"Exception: {e}")
            return False
    
    def test_config_driven_parameters(self) -> bool:
        """Test that components use config-driven parameters."""
        print("\n🔍 Testing Config-Driven Parameters...")
        
        try:
            # Test that components access config parameters through utility manager
            config = {'mode': 'test', 'share_class': 'USDT', 'asset': 'USDT'}
            utility_manager = UtilityManager(config, None)
            
            # Test share class access
            share_class = utility_manager.get_share_class_from_mode('test')
            if share_class == 'USDT':
                self.log_test_result("Share class config access", True, f"Share class: {share_class}")
            else:
                self.log_test_result("Share class config access", False, f"Expected USDT, got {share_class}")
                return False
            
            # Test asset access
            asset = utility_manager.get_asset_from_mode('test')
            if asset == 'ETH':  # Default fallback when mode not found
                self.log_test_result("Asset config access", True, f"Asset: {asset} (default fallback)")
            else:
                self.log_test_result("Asset config access", False, f"Expected ETH (default), got {asset}")
                return False
            
            # Test LST type access
            lst_type = utility_manager.get_lst_type_from_mode('test')
            if lst_type is None:  # Should be None for test mode
                self.log_test_result("LST type config access", True, f"LST type: {lst_type}")
            else:
                self.log_test_result("LST type config access", False, f"Expected None, got {lst_type}")
                return False
            
            # Test hedge allocation access
            hedge_allocation = utility_manager.get_hedge_allocation_from_mode('test')
            if hedge_allocation is None:  # Should be None for test mode
                self.log_test_result("Hedge allocation config access", True, f"Hedge allocation: {hedge_allocation}")
            else:
                self.log_test_result("Hedge allocation config access", False, f"Expected None, got {hedge_allocation}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Config-Driven Parameters", False, f"Exception: {e}")
            return False
    
    def test_pnl_monitor_mode_agnostic(self) -> bool:
        """Test that P&L Calculator is mode-agnostic."""
        print("\n🔍 Testing P&L Calculator Mode-Agnostic...")
        
        try:
            # Test P&L Calculator initialization
            config = {'mode': 'test', 'share_class': 'USDT', 'asset': 'USDT'}
            pnl_monitor = PnLCalculator(config, 'USDT', 1000.0, None, None)
            
            # Check that P&L Calculator has share_class awareness
            if hasattr(pnl_monitor, 'share_class') and pnl_monitor.share_class == 'USDT':
                self.log_test_result("PnLCalculator share_class awareness", True, f"Share class: {pnl_monitor.share_class}")
            else:
                self.log_test_result("PnLCalculator share_class awareness", False, "Missing or incorrect share_class")
                return False
            
            # Check that P&L Calculator doesn't have mode-specific logic
            pnl_methods = [method for method in dir(pnl_monitor) if not method.startswith('_')]
            mode_specific_methods = [method for method in pnl_methods if 'mode' in method.lower() or 'strategy' in method.lower()]
            
            if mode_specific_methods:
                self.log_test_result("PnLCalculator mode-specific methods", False, f"Found: {mode_specific_methods}")
                return False
            else:
                self.log_test_result("PnLCalculator mode-specific methods", True, "No mode-specific methods found")
            
            # Test that P&L Calculator can calculate P&L for different modes
            test_exposure = {
                'total_value_usd': 1000.0,
                'wallet': {'USDT': 1000.0},
                'smart_contract': {},
                'cex_spot': {},
                'cex_derivatives': {}
            }
            
            try:
                pnl_result = pnl_monitor.calculate_pnl(test_exposure, timestamp=pd.Timestamp.now())
                if isinstance(pnl_result, dict):
                    self.log_test_result("PnLCalculator calculation", True, "P&L calculation works")
                else:
                    self.log_test_result("PnLCalculator calculation", False, "Invalid P&L result")
                    return False
            except Exception as e:
                self.log_test_result("PnLCalculator calculation", False, f"Calculation error: {e}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("P&L Calculator Mode-Agnostic", False, f"Exception: {e}")
            return False
    
    def test_strategy_manager_mode_specific(self) -> bool:
        """Test that Strategy Manager is appropriately mode-specific."""
        print("\n🔍 Testing Strategy Manager Mode-Specific...")
        
        try:
            # Test Strategy Manager initialization
            config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT', 'asset': 'USDT'}
            strategy_manager = PureLendingStrategy(config, None, None, None)
            
            # Check that Strategy Manager has mode awareness
            if hasattr(strategy_manager, 'mode') and strategy_manager.mode == 'pure_lending_usdt':
                self.log_test_result("StrategyManager mode awareness", True, f"Mode: {strategy_manager.mode}")
            else:
                self.log_test_result("StrategyManager mode awareness", False, "Missing or incorrect mode")
                return False
            
            # Check that Strategy Manager has strategy instance
            if hasattr(strategy_manager, 'strategy') and strategy_manager.strategy is not None:
                self.log_test_result("StrategyManager strategy instance", True, f"Strategy: {type(strategy_manager.strategy).__name__}")
            else:
                self.log_test_result("StrategyManager strategy instance", False, "Missing strategy instance")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Strategy Manager Mode-Specific", False, f"Exception: {e}")
            return False
    
    def test_no_duplicate_utility_methods(self) -> bool:
        """Test that there are no duplicate utility methods across components."""
        print("\n🔍 Testing No Duplicate Utility Methods...")
        
        try:
            # This is a basic check - in a real implementation, we would scan
            # the source code for duplicate utility methods
            # For now, we'll test that components use the centralized utility manager
            
            config = {'mode': 'test', 'share_class': 'USDT', 'asset': 'USDT'}
            
            # Test that components don't have local utility methods
            position_monitor = PositionMonitor(config, None, None)
            risk_monitor = RiskMonitor(config, None, None)
            exposure_monitor = ExposureMonitor(config, None, None)
            
            # Check for common utility method names
            utility_method_names = [
                'get_liquidity_index', 'get_market_price', 'convert_to_usdt',
                'convert_from_liquidity_index', 'convert_to_share_class'
            ]
            
            components = [
                ('PositionMonitor', position_monitor),
                ('RiskMonitor', risk_monitor),
                ('ExposureMonitor', exposure_monitor)
            ]
            
            no_duplicates = True
            for component_name, component in components:
                for method_name in utility_method_names:
                    if hasattr(component, method_name):
                        self.log_test_result(f"{component_name}.{method_name}", False, "Should use centralized utility manager")
                        no_duplicates = False
                    else:
                        self.log_test_result(f"{component_name}.{method_name}", True, "Uses centralized utility manager")
            
            return no_duplicates
            
        except Exception as e:
            self.log_test_result("No Duplicate Utility Methods", False, f"Exception: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all quality gate tests."""
        print("🚀 Starting Mode-Agnostic Architecture Quality Gates...")
        
        tests = [
            self.test_utility_manager_centralized,
            self.test_components_use_utility_manager,
            self.test_no_mode_specific_logic_in_generic_components,
            self.test_config_driven_parameters,
            self.test_pnl_monitor_mode_agnostic,
            self.test_strategy_manager_mode_specific,
            self.test_no_duplicate_utility_methods
        ]
        
        all_passed = True
        for test in tests:
            try:
                if not test():
                    all_passed = False
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
                all_passed = False
        
        return all_passed
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("📊 MODE-AGNOSTIC ARCHITECTURE QUALITY GATES SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result['passed'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Mode-agnostic architecture is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result['passed'] else "❌"
            print(f"  {status} {result['test']}: {result['message']}")

def main():
    """Main function."""
    quality_gates = ModeAgnosticArchitectureQualityGates()
    
    try:
        success = quality_gates.run_all_tests()
        quality_gates.print_summary()
        
        if success:
            print("\n🎯 Quality gates completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Quality gates failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Quality gates interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Quality gates failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()