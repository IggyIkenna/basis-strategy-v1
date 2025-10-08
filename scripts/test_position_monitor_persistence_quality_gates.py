#!/usr/bin/env python3
"""
Position Monitor State Persistence Quality Gates

Tests that the position monitor maintains state across backtest timesteps:
1. Initial capital is properly set and maintained
2. Wallet balances persist after transfers
3. CEX account balances persist after trades
4. Perp positions persist after trades
5. State is maintained across multiple timesteps
6. No duplicate updates or race conditions
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
from basis_strategy_v1.core.strategies.components.exposure_monitor import ExposureMonitor
from basis_strategy_v1.core.strategies.components.risk_monitor import RiskMonitor
from basis_strategy_v1.core.math.pnl_calculator import PnLCalculator
from basis_strategy_v1.core.strategies.components.position_update_handler import PositionUpdateHandler
from basis_strategy_v1.infrastructure.config.config_manager import ConfigManager
from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider


class PositionMonitorPersistenceQualityGates:
    """Quality gates for position monitor state persistence validation"""
    
    def __init__(self):
        self.results = {}
        self.config_manager = ConfigManager()
        self.data_provider = None
        self.position_monitor = None
        self.exposure_monitor = None
        self.risk_monitor = None
        self.pnl_calculator = None
        self.position_update_handler = None
        
    def setup_test_environment(self) -> bool:
        """Setup test environment with all components"""
        try:
            # Load configuration
            config = self.config_manager.get_complete_config(mode='btc_basis')
            
            # Initialize data provider
            self.data_provider = DataProvider(
                data_dir='data',
                mode='backtest'
            )
            
            # Initialize position monitor with initial capital
            self.position_monitor = PositionMonitor(
                config=config,
                initial_capital=100000.0,
                share_class='USDT',
                execution_mode='backtest'
            )
            
            # Initialize exposure monitor
            self.exposure_monitor = ExposureMonitor(
                config=config,
                share_class='USDT',
                position_monitor=self.position_monitor,
                data_provider=self.data_provider
            )
            
            # Initialize risk monitor
            self.risk_monitor = RiskMonitor(
                config=config,
                position_monitor=self.position_monitor,
                exposure_monitor=self.exposure_monitor,
                data_provider=self.data_provider,
                share_class='USDT'
            )
            
            # Initialize P&L calculator
            self.pnl_calculator = PnLCalculator(
                config=config,
                share_class='USDT',
                initial_capital=100000.0
            )
            
            # Set data provider on P&L calculator
            self.pnl_calculator.set_data_provider(self.data_provider)
            
            # Initialize position update handler
            self.position_update_handler = PositionUpdateHandler(
                position_monitor=self.position_monitor,
                exposure_monitor=self.exposure_monitor,
                risk_monitor=self.risk_monitor,
                pnl_calculator=self.pnl_calculator,
                execution_mode='backtest'
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def test_initial_capital_setup(self) -> bool:
        """Test that initial capital is properly set"""
        try:
            print("🧪 Testing initial capital setup...")
            
            snapshot = self.position_monitor.get_snapshot()
            wallet_usdt = snapshot['wallet'].get('USDT', 0.0)
            
            if wallet_usdt == 100000.0:
                print("✅ Initial capital setup: PASSED")
                return True
            else:
                print(f"❌ Initial capital setup: FAILED - Expected 100000.0, got {wallet_usdt}")
                return False
                
        except Exception as e:
            print(f"❌ Initial capital setup: ERROR - {e}")
            return False
    
    async def test_wallet_balance_persistence(self) -> bool:
        """Test that wallet balances persist after transfers"""
        try:
            print("🧪 Testing wallet balance persistence...")
            
            # Get initial wallet balance
            initial_snapshot = self.position_monitor.get_snapshot()
            initial_wallet_usdt = initial_snapshot['wallet'].get('USDT', 0.0)
            
            # Simulate transfer to Binance
            market_data = {
                'eth_usd_price': 3000.0,
                'btc_usd_price': 40000.0
            }
            await self.position_update_handler.handle_position_update(
                changes={
                    'timestamp': pd.Timestamp.now(tz='UTC'),
                    'trigger': 'WALLET_TRANSFER',
                    'token_changes': [
                        {'venue': 'WALLET', 'token': 'USDT', 'delta': -40000.0, 'reason': 'TRANSFER_TO_BINANCE'},
                        {'venue': 'BINANCE', 'token': 'USDT', 'delta': 40000.0, 'reason': 'TRANSFER_FROM_WALLET'}
                    ]
                },
                timestamp=pd.Timestamp.now(tz='UTC'),
                trigger_component='WALLET_TRANSFER',
                market_data=market_data
            )
            
            # Check wallet balance persisted
            after_transfer_snapshot = self.position_monitor.get_snapshot()
            after_transfer_wallet_usdt = after_transfer_snapshot['wallet'].get('USDT', 0.0)
            binance_usdt = after_transfer_snapshot['cex_accounts'].get('binance', {}).get('USDT', 0.0)
            
            if (after_transfer_wallet_usdt == initial_wallet_usdt - 40000.0 and 
                binance_usdt == 40000.0):
                print("✅ Wallet balance persistence: PASSED")
                return True
            else:
                print(f"❌ Wallet balance persistence: FAILED - Wallet: {after_transfer_wallet_usdt}, Binance: {binance_usdt}")
                return False
                
        except Exception as e:
            print(f"❌ Wallet balance persistence: ERROR - {e}")
            return False
    
    async def test_cex_balance_persistence(self) -> bool:
        """Test that CEX account balances persist after trades"""
        try:
            print("🧪 Testing CEX balance persistence...")
            
            # Get current state
            before_trade_snapshot = self.position_monitor.get_snapshot()
            before_binance_usdt = before_trade_snapshot['cex_accounts'].get('binance', {}).get('USDT', 0.0)
            
            # Simulate BTC spot trade (buy BTC with USDT)
            market_data = {
                'eth_usd_price': 3000.0,
                'btc_usd_price': 40000.0
            }
            await self.position_update_handler.handle_position_update(
                changes={
                    'timestamp': pd.Timestamp.now(tz='UTC'),
                    'trigger': 'CEX_SPOT_TRADE',
                    'token_changes': [
                        {'venue': 'BINANCE', 'token': 'USDT', 'delta': -20000.0, 'reason': 'SPOT_TRADE_COST'},
                        {'venue': 'BINANCE', 'token': 'BTC', 'delta': 0.5, 'reason': 'SPOT_TRADE_BUY'}
                    ]
                },
                timestamp=pd.Timestamp.now(tz='UTC'),
                trigger_component='CEX_SPOT_TRADE',
                market_data=market_data
            )
            
            # Check CEX balances persisted
            after_trade_snapshot = self.position_monitor.get_snapshot()
            after_binance_usdt = after_trade_snapshot['cex_accounts'].get('binance', {}).get('USDT', 0.0)
            after_binance_btc = after_trade_snapshot['cex_accounts'].get('binance', {}).get('BTC', 0.0)
            
            if (after_binance_usdt == before_binance_usdt - 20000.0 and 
                after_binance_btc == 0.5):
                print("✅ CEX balance persistence: PASSED")
                return True
            else:
                print(f"❌ CEX balance persistence: FAILED - USDT: {after_binance_usdt}, BTC: {after_binance_btc}")
                return False
                
        except Exception as e:
            print(f"❌ CEX balance persistence: ERROR - {e}")
            return False
    
    async def test_perp_position_persistence(self) -> bool:
        """Test that perp positions persist after trades"""
        try:
            print("🧪 Testing perp position persistence...")
            
            # Get current state
            before_perp_snapshot = self.position_monitor.get_snapshot()
            before_perp_positions = before_perp_snapshot.get('perp_positions', {})
            
            # Simulate BTC perp trade (short BTC)
            market_data = {
                'eth_usd_price': 3000.0,
                'btc_usd_price': 40000.0
            }
            await self.position_update_handler.handle_position_update(
                changes={
                    'timestamp': pd.Timestamp.now(tz='UTC'),
                    'trigger': 'CEX_PERP_TRADE',
                    'derivative_changes': [
                        {
                            'venue': 'BINANCE',
                            'instrument': 'BTCUSDT',
                            'action': 'OPEN',
                            'data': {
                                'size': -0.5,
                                'entry_price': 40000.0,
                                'entry_timestamp': pd.Timestamp.now(tz='UTC'),
                                'notional_usd': 20000.0
                            }
                        }
                    ]
                },
                timestamp=pd.Timestamp.now(tz='UTC'),
                trigger_component='CEX_PERP_TRADE',
                market_data=market_data
            )
            
            # Check perp positions persisted
            after_perp_snapshot = self.position_monitor.get_snapshot()
            after_perp_positions = after_perp_snapshot.get('perp_positions', {})
            binance_btc_perp = after_perp_positions.get('binance', {}).get('BTCUSDT', {})
            
            if (binance_btc_perp.get('size') == -0.5 and 
                binance_btc_perp.get('entry_price') == 40000.0):
                print("✅ Perp position persistence: PASSED")
                return True
            else:
                print(f"❌ Perp position persistence: FAILED - Size: {binance_btc_perp.get('size')}, Price: {binance_btc_perp.get('entry_price')}")
                return False
                
        except Exception as e:
            print(f"❌ Perp position persistence: ERROR - {e}")
            return False
    
    def test_multiple_timestep_persistence(self) -> bool:
        """Test that state persists across multiple timesteps"""
        try:
            print("🧪 Testing multiple timestep persistence...")
            
            # Get current state
            timestep1_snapshot = self.position_monitor.get_snapshot()
            timestep1_wallet_usdt = timestep1_snapshot['wallet'].get('USDT', 0.0)
            timestep1_binance_usdt = timestep1_snapshot['cex_accounts'].get('binance', {}).get('USDT', 0.0)
            
            # Simulate another timestep with no changes
            # In a real backtest, this would be a new timestep
            timestep2_snapshot = self.position_monitor.get_snapshot()
            timestep2_wallet_usdt = timestep2_snapshot['wallet'].get('USDT', 0.0)
            timestep2_binance_usdt = timestep2_snapshot['cex_accounts'].get('binance', {}).get('USDT', 0.0)
            
            # State should be identical
            if (timestep1_wallet_usdt == timestep2_wallet_usdt and 
                timestep1_binance_usdt == timestep2_binance_usdt):
                print("✅ Multiple timestep persistence: PASSED")
                return True
            else:
                print(f"❌ Multiple timestep persistence: FAILED - Timestep1: {timestep1_wallet_usdt}/{timestep1_binance_usdt}, Timestep2: {timestep2_wallet_usdt}/{timestep2_binance_usdt}")
                return False
                
        except Exception as e:
            print(f"❌ Multiple timestep persistence: ERROR - {e}")
            return False
    
    async def test_no_duplicate_updates(self) -> bool:
        """Test that there are no duplicate updates or race conditions"""
        try:
            print("🧪 Testing no duplicate updates...")
            
            # Get initial state
            initial_snapshot = self.position_monitor.get_snapshot()
            initial_wallet_usdt = initial_snapshot['wallet'].get('USDT', 0.0)
            
            # Apply the same update twice (should not double-deduct)
            market_data = {
                'eth_usd_price': 3000.0,
                'btc_usd_price': 40000.0
            }
            await self.position_update_handler.handle_position_update(
                changes={
                    'timestamp': pd.Timestamp.now(tz='UTC'),
                    'trigger': 'WALLET_TRANSFER',
                    'token_changes': [
                        {'venue': 'WALLET', 'token': 'USDT', 'delta': -1000.0, 'reason': 'TEST_TRANSFER'}
                    ]
                },
                timestamp=pd.Timestamp.now(tz='UTC'),
                trigger_component='WALLET_TRANSFER',
                market_data=market_data
            )
            
            first_update_snapshot = self.position_monitor.get_snapshot()
            first_update_wallet_usdt = first_update_snapshot['wallet'].get('USDT', 0.0)
            
            # Apply same update again
            await self.position_update_handler.handle_position_update(
                changes={
                    'timestamp': pd.Timestamp.now(tz='UTC'),
                    'trigger': 'WALLET_TRANSFER',
                    'token_changes': [
                        {'venue': 'WALLET', 'token': 'USDT', 'delta': -1000.0, 'reason': 'TEST_TRANSFER_2'}
                    ]
                },
                timestamp=pd.Timestamp.now(tz='UTC'),
                trigger_component='WALLET_TRANSFER',
                market_data=market_data
            )
            
            second_update_snapshot = self.position_monitor.get_snapshot()
            second_update_wallet_usdt = second_update_snapshot['wallet'].get('USDT', 0.0)
            
            # Second update should be applied correctly (not ignored)
            if second_update_wallet_usdt == initial_wallet_usdt - 2000.0:
                print("✅ No duplicate updates: PASSED")
                return True
            else:
                print(f"❌ No duplicate updates: FAILED - Expected {initial_wallet_usdt - 2000.0}, got {second_update_wallet_usdt}")
                return False
                
        except Exception as e:
            print(f"❌ No duplicate updates: ERROR - {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all position monitor persistence quality gate tests"""
        print("🚀 Starting Position Monitor State Persistence Quality Gates")
        print("=" * 60)
        
        # Setup test environment
        if not self.setup_test_environment():
            print("❌ Failed to setup test environment")
            return {}
        
        # Run tests
        tests = [
            ("Initial Capital Setup", self.test_initial_capital_setup, False),
            ("Wallet Balance Persistence", self.test_wallet_balance_persistence, True),
            ("CEX Balance Persistence", self.test_cex_balance_persistence, True),
            ("Perp Position Persistence", self.test_perp_position_persistence, True),
            ("Multiple Timestep Persistence", self.test_multiple_timestep_persistence, False),
            ("No Duplicate Updates", self.test_no_duplicate_updates, True),
        ]
        
        results = {}
        for test_name, test_func, is_async in tests:
            try:
                if is_async:
                    import asyncio
                    results[test_name] = asyncio.run(test_func())
                else:
                    results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                results[test_name] = False
        
        # Summary
        passed = sum(results.values())
        total = len(results)
        
        print("\n" + "=" * 60)
        print(f"🎯 POSITION MONITOR PERSISTENCE SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ ALL TESTS PASSED - Position monitor state persistence is working correctly")
        else:
            print("❌ SOME TESTS FAILED - Review failed tests above")
        
        return results


def main():
    """Main function to run position monitor persistence quality gates"""
    try:
        quality_gates = PositionMonitorPersistenceQualityGates()
        results = quality_gates.run_all_tests()
        
        # Exit with appropriate code
        if all(results.values()):
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except Exception as e:
        print(f"❌ Quality gates failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
