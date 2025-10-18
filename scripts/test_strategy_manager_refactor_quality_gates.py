#!/usr/bin/env python3
"""
Strategy Manager Refactor Quality Gates

Tests the new factory-based strategy manager architecture with standardized
wrapper actions and tight loop integration.

Reference: .cursor/tasks/06_strategy_manager_refactor.md
"""

import sys
import os
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add the backend source to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from basis_strategy_v1.core.strategies.strategy_factory import StrategyFactory, create_strategy
from basis_strategy_v1.core.strategies.base_strategy_manager import BaseStrategyManager, StrategyAction
from basis_strategy_v1.core.strategies.pure_lending_usdt_strategy import PureLendingStrategy
from basis_strategy_v1.core.strategies.components.strategy_manager import StrategyManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyManagerRefactorQualityGates:
    """Quality gates for strategy manager refactor."""
    
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
    
    def test_base_strategy_manager(self) -> bool:
        """Test base strategy manager functionality."""
        print("\n🔍 Testing Base Strategy Manager...")
        
        try:
            # Create a mock strategy manager
            class MockStrategyManager(BaseStrategyManager):
                def calculate_target_position(self, current_equity: float) -> Dict[str, float]:
                    return {'USDT': current_equity}
                
                def entry_full(self, equity: float) -> StrategyAction:
                    return StrategyAction(
                        action_type='entry_full',
                        target_amount=equity,
                        target_currency='USDT',
                        instructions=[]
                    )
                
                def entry_partial(self, equity_delta: float) -> StrategyAction:
                    return StrategyAction(
                        action_type='entry_partial',
                        target_amount=equity_delta,
                        target_currency='USDT',
                        instructions=[]
                    )
                
                def exit_full(self, equity: float) -> StrategyAction:
                    return StrategyAction(
                        action_type='exit_full',
                        target_amount=equity,
                        target_currency='USDT',
                        instructions=[]
                    )
                
                def exit_partial(self, equity_delta: float) -> StrategyAction:
                    return StrategyAction(
                        action_type='exit_partial',
                        target_amount=equity_delta,
                        target_currency='USDT',
                        instructions=[]
                    )
                
                def sell_dust(self, dust_tokens: Dict[str, float]) -> StrategyAction:
                    return StrategyAction(
                        action_type='sell_dust',
                        target_amount=sum(dust_tokens.values()),
                        target_currency='USDT',
                        instructions=[]
                    )
            
            # Test initialization
            config = {'mode': 'test', 'share_class': 'USDT', 'asset': 'USDT'}
            strategy = MockStrategyManager(config, None, None, None)
            
            if hasattr(strategy, 'structured_logger'):
                self.log_test_result("Base Strategy Manager Initialization", True, "Structured logger integrated")
            else:
                self.log_test_result("Base Strategy Manager Initialization", False, "No structured logger found")
                return False
            
            # Test equity calculation
            equity = strategy.get_equity()
            if isinstance(equity, (int, float)):
                self.log_test_result("Equity Calculation", True, f"Equity: {equity}")
            else:
                self.log_test_result("Equity Calculation", False, "Invalid equity type")
                return False
            
            # Test dust checking
            dust_tokens = {'ETH': 0.001, 'BTC': 0.0001}
            should_sell = strategy.should_sell_dust(dust_tokens)
            if isinstance(should_sell, bool):
                self.log_test_result("Dust Checking", True, f"Should sell dust: {should_sell}")
            else:
                self.log_test_result("Dust Checking", False, "Invalid dust check result")
                return False
            
            # Test reserve checking
            reserve_status = strategy.check_reserves()
            if isinstance(reserve_status, dict) and 'sufficient' in reserve_status:
                self.log_test_result("Reserve Checking", True, f"Reserves sufficient: {reserve_status['sufficient']}")
            else:
                self.log_test_result("Reserve Checking", False, "Invalid reserve status")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Base Strategy Manager", False, f"Exception: {e}")
            return False
    
    def test_strategy_factory(self) -> bool:
        """Test strategy factory functionality."""
        print("\n🔍 Testing Strategy Factory...")
        
        try:
            # Test supported modes
            supported_modes = StrategyFactory.get_supported_modes()
            if isinstance(supported_modes, list):
                self.log_test_result("Supported Modes", True, f"Modes: {supported_modes}")
            else:
                self.log_test_result("Supported Modes", False, "Invalid supported modes")
                return False
            
            # Test mode support checking
            is_pure_lending_usdt_supported = StrategyFactory.is_mode_supported('pure_lending_usdt')
            if isinstance(is_pure_lending_usdt_supported, bool):
                self.log_test_result("Mode Support Checking", True, f"Pure lending supported: {is_pure_lending_usdt_supported}")
            else:
                self.log_test_result("Mode Support Checking", False, "Invalid mode support result")
                return False
            
            # Test strategy creation
            config = {'mode': 'pure_lending_usdt', 'share_class': 'USDT', 'asset': 'USDT'}
            strategy = StrategyFactory.create_strategy(
                mode='pure_lending_usdt',
                config=config,
                risk_monitor=None,
                position_monitor=None,
                event_engine=None
            )
            
            if isinstance(strategy, PureLendingStrategy):
                self.log_test_result("Strategy Creation", True, f"Created: {type(strategy).__name__}")
            else:
                self.log_test_result("Strategy Creation", False, f"Wrong type: {type(strategy)}")
                return False
            
            # Test unsupported mode
            try:
                StrategyFactory.create_strategy(
                    mode='unsupported_mode',
                    config=config,
                    risk_monitor=None,
                    position_monitor=None,
                    event_engine=None
                )
                self.log_test_result("Unsupported Mode Handling", False, "Should have raised exception")
                return False
            except ValueError:
                self.log_test_result("Unsupported Mode Handling", True, "Correctly raised ValueError")
            
            return True
            
        except Exception as e:
            self.log_test_result("Strategy Factory", False, f"Exception: {e}")
            return False
    
    def test_pure_lending_usdt_strategy(self) -> bool:
        """Test pure lending strategy implementation."""
        print("\n🔍 Testing Pure Lending Strategy...")
        
        try:
            # Create strategy instance
            config = {
                'mode': 'pure_lending_usdt',
                'share_class': 'USDT',
                'asset': 'USDT',
                'lending_enabled': True,
                'target_apy': 0.05
            }
            
            strategy = PureLendingStrategy(config, None, None, None)
            
            if hasattr(strategy, 'structured_logger'):
                self.log_test_result("Pure Lending Strategy Initialization", True, "Structured logger integrated")
            else:
                self.log_test_result("Pure Lending Strategy Initialization", False, "No structured logger found")
                return False
            
            # Test target position calculation
            target_position = strategy.calculate_target_position(1000.0)
            if isinstance(target_position, dict) and 'aUSDT' in target_position:
                self.log_test_result("Target Position Calculation", True, f"Target: {target_position}")
            else:
                self.log_test_result("Target Position Calculation", False, f"Invalid target: {target_position}")
                return False
            
            # Test entry full action
            entry_action = strategy.entry_full(1000.0)
            if isinstance(entry_action, StrategyAction) and entry_action.action_type == 'entry_full':
                self.log_test_result("Entry Full Action", True, f"Action: {entry_action.action_type}")
            else:
                self.log_test_result("Entry Full Action", False, f"Invalid action: {entry_action}")
                return False
            
            # Test entry partial action
            partial_action = strategy.entry_partial(100.0)
            if isinstance(partial_action, StrategyAction) and partial_action.action_type == 'entry_partial':
                self.log_test_result("Entry Partial Action", True, f"Action: {partial_action.action_type}")
            else:
                self.log_test_result("Entry Partial Action", False, f"Invalid action: {partial_action}")
                return False
            
            # Test exit full action
            exit_action = strategy.exit_full(1000.0)
            if isinstance(exit_action, StrategyAction) and exit_action.action_type == 'exit_full':
                self.log_test_result("Exit Full Action", True, f"Action: {exit_action.action_type}")
            else:
                self.log_test_result("Exit Full Action", False, f"Invalid action: {exit_action}")
                return False
            
            # Test exit partial action
            partial_exit_action = strategy.exit_partial(100.0)
            if isinstance(partial_exit_action, StrategyAction) and partial_exit_action.action_type == 'exit_partial':
                self.log_test_result("Exit Partial Action", True, f"Action: {partial_exit_action.action_type}")
            else:
                self.log_test_result("Exit Partial Action", False, f"Invalid action: {partial_exit_action}")
                return False
            
            # Test dust selling action
            dust_tokens = {'ETH': 0.001, 'BTC': 0.0001}
            dust_action = strategy.sell_dust(dust_tokens)
            if isinstance(dust_action, StrategyAction) and dust_action.action_type == 'sell_dust':
                self.log_test_result("Dust Selling Action", True, f"Action: {dust_action.action_type}")
            else:
                self.log_test_result("Dust Selling Action", False, f"Invalid action: {dust_action}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Pure Lending Strategy", False, f"Exception: {e}")
            return False
    
    def test_strategy_action_model(self) -> bool:
        """Test strategy action model."""
        print("\n🔍 Testing Strategy Action Model...")
        
        try:
            # Test basic action creation
            action = StrategyAction(
                action_type='entry_full',
                target_amount=1000.0,
                target_currency='USDT',
                instructions=[{'action': 'lend', 'venue': 'aave_v3'}],
                atomic=True
            )
            
            if action.action_type == 'entry_full' and action.target_amount == 1000.0:
                self.log_test_result("Strategy Action Creation", True, f"Action: {action.action_type}")
            else:
                self.log_test_result("Strategy Action Creation", False, f"Invalid action: {action}")
                return False
            
            # Test action serialization
            action_dict = action.model_dump()
            if isinstance(action_dict, dict) and 'action_type' in action_dict:
                self.log_test_result("Strategy Action Serialization", True, "Action serialized successfully")
            else:
                self.log_test_result("Strategy Action Serialization", False, "Serialization failed")
                return False
            
            # Test action validation
            try:
                invalid_action = StrategyAction(
                    action_type='invalid_type',
                    target_amount=-100.0,  # Negative amount
                    target_currency='USDT',
                    instructions=[]
                )
                self.log_test_result("Strategy Action Validation", False, "Should have failed validation")
                return False
            except Exception:
                self.log_test_result("Strategy Action Validation", True, "Correctly failed validation")
            
            return True
            
        except Exception as e:
            self.log_test_result("Strategy Action Model", False, f"Exception: {e}")
            return False
    
    def test_strategy_manager_integration(self) -> bool:
        """Test strategy manager integration."""
        print("\n🔍 Testing Strategy Manager Integration...")
        
        try:
            # Create strategy manager
            config = {
                'mode': 'pure_lending_usdt',
                'share_class': 'USDT',
                'asset': 'USDT'
            }
            
            strategy_manager = StrategyManager(config, None, None, None)
            
            if hasattr(strategy_manager, 'strategy') and strategy_manager.strategy is not None:
                self.log_test_result("Strategy Manager Integration", True, f"Strategy: {type(strategy_manager.strategy).__name__}")
            else:
                self.log_test_result("Strategy Manager Integration", False, "No strategy instance created")
                return False
            
            # Test strategy actions calculation
            import pandas as pd
            timestamp = pd.Timestamp.now()
            actions = strategy_manager.calculate_strategy_actions(timestamp)
            
            if isinstance(actions, dict) and 'status' in actions:
                self.log_test_result("Strategy Actions Calculation", True, f"Status: {actions['status']}")
            else:
                self.log_test_result("Strategy Actions Calculation", False, f"Invalid actions: {actions}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Strategy Manager Integration", False, f"Exception: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all quality gate tests."""
        print("🚀 Starting Strategy Manager Refactor Quality Gates...")
        
        tests = [
            self.test_base_strategy_manager,
            self.test_strategy_factory,
            self.test_pure_lending_usdt_strategy,
            self.test_strategy_action_model,
            self.test_strategy_manager_integration
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
        print("📊 STRATEGY MANAGER REFACTOR QUALITY GATES SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result['passed'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Strategy manager refactor is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result['passed'] else "❌"
            print(f"  {status} {result['test']}: {result['message']}")

def main():
    """Main function."""
    quality_gates = StrategyManagerRefactorQualityGates()
    
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