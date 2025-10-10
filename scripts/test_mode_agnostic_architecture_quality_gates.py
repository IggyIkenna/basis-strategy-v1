#!/usr/bin/env python3
"""
Mode-Agnostic Architecture Quality Gates

Validates that components are mode-agnostic where appropriate and strategy mode-specific where necessary.
Tests the centralized utility manager and ensures no mode-specific logic in generic components.

Reference: .cursor/tasks/08_mode_agnostic_architecture.md
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add the backend source to the path
backend_src = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

from basis_strategy_v1.core.utilities.utility_manager import UtilityManager
from basis_strategy_v1.core.strategies.components.pnl_monitor import PnLMonitor
from basis_strategy_v1.core.strategies.components.exposure_monitor import ExposureMonitor
from basis_strategy_v1.core.strategies.components.risk_monitor import RiskMonitor
from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModeAgnosticArchitectureQualityGates:
    """Quality gates for mode-agnostic architecture validation"""
    
    def __init__(self):
        self.test_results = []
        self.passed_gates = 0
        self.total_gates = 0
    
    def run_all_quality_gates(self):
        """Run all quality gates for mode-agnostic architecture"""
        logger.info("Starting Mode-Agnostic Architecture Quality Gates")
        
        # QG1: Utility Manager Centralization
        self._test_utility_manager_centralization()
        
        # QG2: P&L Monitor Mode-Agnostic
        self._test_pnl_monitor_mode_agnostic()
        
        # QG3: Exposure Monitor Mode-Agnostic
        self._test_exposure_monitor_mode_agnostic()
        
        # QG4: Risk Monitor Mode-Agnostic
        self._test_risk_monitor_mode_agnostic()
        
        # QG5: Position Monitor Mode-Agnostic
        self._test_position_monitor_mode_agnostic()
        
        # QG6: No Mode-Specific Logic in Generic Components
        self._test_no_mode_specific_logic()
        
        # QG7: Config-Driven Parameters
        self._test_config_driven_parameters()
        
        # QG8: Integration Test
        self._test_integration()
        
        # Print results
        self._print_results()
        
        return self.passed_gates == self.total_gates
    
    def _test_utility_manager_centralization(self):
        """Test that utility manager is centralized and working"""
        self.total_gates += 1
        try:
            # Create mock config and data provider
            config = {
                'modes': {
                    'pure_lending': {'share_class': 'USDT', 'asset': 'USDT'},
                    'btc_basis': {'share_class': 'USDT', 'asset': 'BTC', 'hedge_allocation': 0.5},
                    'eth_staking': {'share_class': 'ETH', 'asset': 'ETH', 'lst_type': 'lido'}
                }
            }
            
            class MockDataProvider:
                def get_liquidity_index(self, token, timestamp):
                    return 1.05 if token.startswith('a') else 1.0
                
                def get_market_price(self, token, currency, timestamp):
                    if token == 'ETH' and currency == 'USDT':
                        return 2000.0
                    elif token == 'BTC' and currency == 'USDT':
                        return 50000.0
                    return 1.0
            
            data_provider = MockDataProvider()
            utility_manager = UtilityManager(config, data_provider)
            
            # Test utility methods
            timestamp = pd.Timestamp.now()
            
            # Test liquidity index
            liquidity_index = utility_manager.get_liquidity_index('aUSDT', timestamp)
            assert liquidity_index == 1.05, f"Expected 1.05, got {liquidity_index}"
            
            # Test market price
            eth_price = utility_manager.get_market_price('ETH', 'USDT', timestamp)
            assert eth_price == 2000.0, f"Expected 2000.0, got {eth_price}"
            
            # Test USDT conversion
            usdt_value = utility_manager.convert_to_usdt(1.0, 'ETH', timestamp)
            assert usdt_value == 2000.0, f"Expected 2000.0, got {usdt_value}"
            
            # Test share class conversion
            share_class_value = utility_manager.convert_to_share_class(1.0, 'ETH', 'USDT', timestamp)
            assert share_class_value == 2000.0, f"Expected 2000.0, got {share_class_value}"
            
            # Test config parameter access
            share_class = utility_manager.get_share_class_from_mode('pure_lending')
            assert share_class == 'USDT', f"Expected USDT, got {share_class}"
            
            asset = utility_manager.get_asset_from_mode('btc_basis')
            assert asset == 'BTC', f"Expected BTC, got {asset}"
            
            lst_type = utility_manager.get_lst_type_from_mode('eth_staking')
            assert lst_type == 'lido', f"Expected lido, got {lst_type}"
            
            hedge_allocation = utility_manager.get_hedge_allocation_from_mode('btc_basis')
            assert hedge_allocation == 0.5, f"Expected 0.5, got {hedge_allocation}"
            
            self.passed_gates += 1
            self.test_results.append("QG1: Utility Manager Centralization - PASSED")
            logger.info("✅ QG1: Utility Manager Centralization - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG1: Utility Manager Centralization - FAILED: {e}")
            logger.error(f"❌ QG1: Utility Manager Centralization - FAILED: {e}")
    
    def _test_pnl_monitor_mode_agnostic(self):
        """Test that P&L monitor is mode-agnostic"""
        self.total_gates += 1
        try:
            # Create mock config and data provider
            config = {
                'modes': {
                    'pure_lending': {'share_class': 'USDT', 'asset': 'USDT'},
                    'btc_basis': {'share_class': 'USDT', 'asset': 'BTC'}
                }
            }
            
            class MockDataProvider:
                def get_liquidity_index(self, token, timestamp):
                    return 1.05 if token.startswith('a') else 1.0
                
                def get_market_price(self, token, currency, timestamp):
                    if token == 'ETH' and currency == 'USDT':
                        return 2000.0
                    elif token == 'BTC' and currency == 'USDT':
                        return 50000.0
                    return 1.0
            
            data_provider = MockDataProvider()
            utility_manager = UtilityManager(config, data_provider)
            
            # Create P&L monitor
            pnl_monitor = PnLMonitor(config, data_provider, utility_manager)
            
            # Test that P&L monitor is mode-agnostic
            timestamp = pd.Timestamp.now()
            exposures = {
                'wallet_balances': {'USDT': 1000.0, 'ETH': 0.5},
                'smart_contract_balances': {'aUSDT': 500.0},
                'cex_spot_balances': {'BTC': 0.01},
                'cex_derivatives_balances': {}
            }
            
            # Test P&L calculation (should work regardless of mode)
            pnl_result = pnl_monitor.calculate_pnl(exposures, timestamp)
            
            # Verify result structure
            assert 'total_usdt_balance' in pnl_result, "Missing total_usdt_balance in P&L result"
            assert 'total_share_class_balance' in pnl_result, "Missing total_share_class_balance in P&L result"
            assert 'pnl_change' in pnl_result, "Missing pnl_change in P&L result"
            assert 'timestamp' in pnl_result, "Missing timestamp in P&L result"
            
            self.passed_gates += 1
            self.test_results.append("QG2: P&L Monitor Mode-Agnostic - PASSED")
            logger.info("✅ QG2: P&L Monitor Mode-Agnostic - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG2: P&L Monitor Mode-Agnostic - FAILED: {e}")
            logger.error(f"❌ QG2: P&L Monitor Mode-Agnostic - FAILED: {e}")
    
    def _test_exposure_monitor_mode_agnostic(self):
        """Test that exposure monitor is mode-agnostic"""
        self.total_gates += 1
        try:
            # Create mock config and data provider
            config = {
                'modes': {
                    'pure_lending': {'share_class': 'USDT', 'asset': 'USDT'},
                    'btc_basis': {'share_class': 'USDT', 'asset': 'BTC'}
                }
            }
            
            class MockDataProvider:
                def get_liquidity_index(self, token, timestamp):
                    return 1.05 if token.startswith('a') else 1.0
                
                def get_market_price(self, token, currency, timestamp):
                    if token == 'ETH' and currency == 'USDT':
                        return 2000.0
                    elif token == 'BTC' and currency == 'USDT':
                        return 50000.0
                    return 1.0
            
            data_provider = MockDataProvider()
            utility_manager = UtilityManager(config, data_provider)
            
            # Create exposure monitor
            exposure_monitor = ExposureMonitor(config, data_provider, utility_manager)
            
            # Test that exposure monitor is mode-agnostic
            timestamp = pd.Timestamp.now()
            positions = {
                'wallet_balances': {'USDT': 1000.0, 'ETH': 0.5},
                'smart_contract_balances': {'aUSDT': 500.0},
                'cex_spot_balances': {'BTC': 0.01},
                'cex_derivatives_balances': {}
            }
            
            # Test exposure calculation (should work regardless of mode)
            exposure_result = exposure_monitor.calculate_exposures(positions, timestamp)
            
            # Verify result structure
            assert 'total_exposure' in exposure_result, "Missing total_exposure in exposure result"
            assert 'exposure_by_venue' in exposure_result, "Missing exposure_by_venue in exposure result"
            assert 'timestamp' in exposure_result, "Missing timestamp in exposure result"
            
            self.passed_gates += 1
            self.test_results.append("QG3: Exposure Monitor Mode-Agnostic - PASSED")
            logger.info("✅ QG3: Exposure Monitor Mode-Agnostic - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG3: Exposure Monitor Mode-Agnostic - FAILED: {e}")
            logger.error(f"❌ QG3: Exposure Monitor Mode-Agnostic - FAILED: {e}")
    
    def _test_risk_monitor_mode_agnostic(self):
        """Test that risk monitor is mode-agnostic"""
        self.total_gates += 1
        try:
            # Create mock config and data provider
            config = {
                'modes': {
                    'pure_lending': {'share_class': 'USDT', 'asset': 'USDT'},
                    'btc_basis': {'share_class': 'USDT', 'asset': 'BTC'}
                }
            }
            
            class MockDataProvider:
                def get_liquidity_index(self, token, timestamp):
                    return 1.05 if token.startswith('a') else 1.0
                
                def get_market_price(self, token, currency, timestamp):
                    if token == 'ETH' and currency == 'USDT':
                        return 2000.0
                    elif token == 'BTC' and currency == 'USDT':
                        return 50000.0
                    return 1.0
            
            data_provider = MockDataProvider()
            utility_manager = UtilityManager(config, data_provider)
            
            # Create risk monitor
            risk_monitor = RiskMonitor(config, data_provider, utility_manager)
            
            # Test that risk monitor is mode-agnostic
            timestamp = pd.Timestamp.now()
            exposures = {
                'wallet_balances': {'USDT': 1000.0, 'ETH': 0.5},
                'smart_contract_balances': {'aUSDT': 500.0},
                'cex_spot_balances': {'BTC': 0.01},
                'cex_derivatives_balances': {}
            }
            
            # Test risk calculation (should work regardless of mode)
            risk_result = risk_monitor.calculate_risks(exposures, timestamp)
            
            # Verify result structure
            assert 'total_risk' in risk_result, "Missing total_risk in risk result"
            assert 'risk_by_venue' in risk_result, "Missing risk_by_venue in risk result"
            assert 'timestamp' in risk_result, "Missing timestamp in risk result"
            
            self.passed_gates += 1
            self.test_results.append("QG4: Risk Monitor Mode-Agnostic - PASSED")
            logger.info("✅ QG4: Risk Monitor Mode-Agnostic - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG4: Risk Monitor Mode-Agnostic - FAILED: {e}")
            logger.error(f"❌ QG4: Risk Monitor Mode-Agnostic - FAILED: {e}")
    
    def _test_position_monitor_mode_agnostic(self):
        """Test that position monitor is mode-agnostic"""
        self.total_gates += 1
        try:
            # Create mock config and data provider
            config = {
                'modes': {
                    'pure_lending': {'share_class': 'USDT', 'asset': 'USDT'},
                    'btc_basis': {'share_class': 'USDT', 'asset': 'BTC'}
                }
            }
            
            class MockDataProvider:
                def get_liquidity_index(self, token, timestamp):
                    return 1.05 if token.startswith('a') else 1.0
                
                def get_market_price(self, token, currency, timestamp):
                    if token == 'ETH' and currency == 'USDT':
                        return 2000.0
                    elif token == 'BTC' and currency == 'USDT':
                        return 50000.0
                    return 1.0
            
            data_provider = MockDataProvider()
            utility_manager = UtilityManager(config, data_provider)
            
            # Create position monitor
            position_monitor = PositionMonitor(config, data_provider, utility_manager)
            
            # Test that position monitor is mode-agnostic
            timestamp = pd.Timestamp.now()
            
            # Test position monitoring (should work regardless of mode)
            position_result = position_monitor.get_all_positions(timestamp)
            
            # Verify result structure
            assert 'wallet_positions' in position_result, "Missing wallet_positions in position result"
            assert 'smart_contract_positions' in position_result, "Missing smart_contract_positions in position result"
            assert 'cex_spot_positions' in position_result, "Missing cex_spot_positions in position result"
            assert 'cex_derivatives_positions' in position_result, "Missing cex_derivatives_positions in position result"
            assert 'timestamp' in position_result, "Missing timestamp in position result"
            
            self.passed_gates += 1
            self.test_results.append("QG5: Position Monitor Mode-Agnostic - PASSED")
            logger.info("✅ QG5: Position Monitor Mode-Agnostic - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG5: Position Monitor Mode-Agnostic - FAILED: {e}")
            logger.error(f"❌ QG5: Position Monitor Mode-Agnostic - FAILED: {e}")
    
    def _test_no_mode_specific_logic(self):
        """Test that generic components don't have mode-specific logic"""
        self.total_gates += 1
        try:
            # Check that generic components don't have hardcoded mode checks
            component_files = [
                'backend/src/basis_strategy_v1/core/strategies/components/pnl_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py'
            ]
            
            forbidden_patterns = [
                "if mode == 'pure_lending'",
                "if mode == 'btc_basis'",
                "if mode == 'eth_staking'",
                "elif mode == 'pure_lending'",
                "elif mode == 'btc_basis'",
                "elif mode == 'eth_staking'",
                "mode == 'pure_lending'",
                "mode == 'btc_basis'",
                "mode == 'eth_staking'"
            ]
            
            violations = []
            
            for component_file in component_files:
                if os.path.exists(component_file):
                    with open(component_file, 'r') as f:
                        content = f.read()
                        
                    for pattern in forbidden_patterns:
                        if pattern in content:
                            violations.append(f"{component_file}: Found forbidden pattern '{pattern}'")
            
            if violations:
                raise Exception(f"Found mode-specific logic violations: {violations}")
            
            self.passed_gates += 1
            self.test_results.append("QG6: No Mode-Specific Logic in Generic Components - PASSED")
            logger.info("✅ QG6: No Mode-Specific Logic in Generic Components - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG6: No Mode-Specific Logic in Generic Components - FAILED: {e}")
            logger.error(f"❌ QG6: No Mode-Specific Logic in Generic Components - FAILED: {e}")
    
    def _test_config_driven_parameters(self):
        """Test that components use config-driven parameters"""
        self.total_gates += 1
        try:
            # Check that components access config parameters properly
            component_files = [
                'backend/src/basis_strategy_v1/core/strategies/components/pnl_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/exposure_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/risk_monitor.py',
                'backend/src/basis_strategy_v1/core/strategies/components/position_monitor.py'
            ]
            
            required_patterns = [
                "utility_manager.get_share_class_from_mode",
                "utility_manager.get_asset_from_mode",
                "utility_manager.get_lst_type_from_mode",
                "utility_manager.get_hedge_allocation_from_mode"
            ]
            
            missing_patterns = []
            
            for component_file in component_files:
                if os.path.exists(component_file):
                    with open(component_file, 'r') as f:
                        content = f.read()
                        
                    for pattern in required_patterns:
                        if pattern not in content:
                            missing_patterns.append(f"{component_file}: Missing pattern '{pattern}'")
            
            if missing_patterns:
                raise Exception(f"Missing config-driven parameter access: {missing_patterns}")
            
            self.passed_gates += 1
            self.test_results.append("QG7: Config-Driven Parameters - PASSED")
            logger.info("✅ QG7: Config-Driven Parameters - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG7: Config-Driven Parameters - FAILED: {e}")
            logger.error(f"❌ QG7: Config-Driven Parameters - FAILED: {e}")
    
    def _test_integration(self):
        """Test integration of mode-agnostic components"""
        self.total_gates += 1
        try:
            # Create mock config and data provider
            config = {
                'modes': {
                    'pure_lending': {'share_class': 'USDT', 'asset': 'USDT'},
                    'btc_basis': {'share_class': 'USDT', 'asset': 'BTC', 'hedge_allocation': 0.5},
                    'eth_staking': {'share_class': 'ETH', 'asset': 'ETH', 'lst_type': 'lido'}
                }
            }
            
            class MockDataProvider:
                def get_liquidity_index(self, token, timestamp):
                    return 1.05 if token.startswith('a') else 1.0
                
                def get_market_price(self, token, currency, timestamp):
                    if token == 'ETH' and currency == 'USDT':
                        return 2000.0
                    elif token == 'BTC' and currency == 'USDT':
                        return 50000.0
                    return 1.0
            
            data_provider = MockDataProvider()
            utility_manager = UtilityManager(config, data_provider)
            
            # Create all components
            pnl_monitor = PnLMonitor(config, data_provider, utility_manager)
            exposure_monitor = ExposureMonitor(config, data_provider, utility_manager)
            risk_monitor = RiskMonitor(config, data_provider, utility_manager)
            position_monitor = PositionMonitor(config, data_provider, utility_manager)
            
            # Test integration
            timestamp = pd.Timestamp.now()
            positions = {
                'wallet_balances': {'USDT': 1000.0, 'ETH': 0.5},
                'smart_contract_balances': {'aUSDT': 500.0},
                'cex_spot_balances': {'BTC': 0.01},
                'cex_derivatives_balances': {}
            }
            
            # Test that all components work together
            position_result = position_monitor.get_all_positions(timestamp)
            exposure_result = exposure_monitor.calculate_exposures(positions, timestamp)
            risk_result = risk_monitor.calculate_risks(positions, timestamp)
            pnl_result = pnl_monitor.calculate_pnl(positions, timestamp)
            
            # Verify all results are valid
            assert position_result is not None, "Position monitor result is None"
            assert exposure_result is not None, "Exposure monitor result is None"
            assert risk_result is not None, "Risk monitor result is None"
            assert pnl_result is not None, "P&L monitor result is None"
            
            self.passed_gates += 1
            self.test_results.append("QG8: Integration Test - PASSED")
            logger.info("✅ QG8: Integration Test - PASSED")
            
        except Exception as e:
            self.test_results.append(f"QG8: Integration Test - FAILED: {e}")
            logger.error(f"❌ QG8: Integration Test - FAILED: {e}")
    
    def _print_results(self):
        """Print quality gate results"""
        logger.info("\n" + "="*60)
        logger.info("MODE-AGNOSTIC ARCHITECTURE QUALITY GATES RESULTS")
        logger.info("="*60)
        
        for result in self.test_results:
            logger.info(result)
        
        logger.info("="*60)
        logger.info(f"PASSED: {self.passed_gates}/{self.total_gates} quality gates")
        logger.info(f"SUCCESS RATE: {(self.passed_gates/self.total_gates)*100:.1f}%")
        
        if self.passed_gates == self.total_gates:
            logger.info("🎉 ALL QUALITY GATES PASSED! Mode-agnostic architecture is working correctly.")
        else:
            logger.error(f"❌ {self.total_gates - self.passed_gates} quality gates failed. Mode-agnostic architecture needs fixes.")
        
        logger.info("="*60)

def main():
    """Main function to run quality gates"""
    quality_gates = ModeAgnosticArchitectureQualityGates()
    success = quality_gates.run_all_quality_gates()
    
    if success:
        print("\n✅ All mode-agnostic architecture quality gates passed!")
        sys.exit(0)
    else:
        print("\n❌ Some mode-agnostic architecture quality gates failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

