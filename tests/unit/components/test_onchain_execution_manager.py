#!/usr/bin/env python3
"""
Test OnChain Execution Manager Component

Tests the OnChainExecutionManager for both backtest and live modes.
"""

import sys
import os
import asyncio
import pandas as pd
from datetime import datetime, timezone
import pytest

# Add the backend source to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../backend/src'))

from basis_strategy_v1.core.strategies.components.onchain_execution_manager import OnChainExecutionManager
from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
from basis_strategy_v1.core.strategies.components.event_logger import EventLogger
from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider


class MockDataProvider:
    """Mock data provider for testing."""
    
    def __init__(self):
        self.data = {
            'market_prices': {'ETH': 3000.0, 'BTC': 50000.0},
            'perp_prices': {'ETHUSDT': 3000.0, 'BTCUSDT': 50000.0},
            'aave_indices': {
                'WETH': {'liquidity': 1.05, 'borrow': 1.02},
                'AWEETH': {'liquidity': 1.03, 'borrow': 1.01}
            },
            'gas_costs': {
                'CREATE_LST': 0.01,
                'COLLATERAL_SUPPLIED': 0.005,
                'BORROW': 0.008,
                'REPAY': 0.006,
                'WITHDRAW': 0.004
            }
        }
    
    def get_component_data(self, component: str) -> dict:
        """Get component-specific data."""
        return self.data
    
    def get_oracle_price(self, lst_type: str, timestamp: pd.Timestamp) -> float:
        """Get oracle price for LST."""
        return 3000.0  # ETH price
    
    def get_aave_index(self, asset: str, index_type: str, timestamp: pd.Timestamp) -> float:
        """Get AAVE index."""
        return self.data['aave_indices'].get(asset, {}).get(index_type, 1.0)
    
    def get_gas_cost(self, operation: str, timestamp: pd.Timestamp) -> float:
        """Get gas cost for operation."""
        return self.data['gas_costs'].get(operation, 0.01)
    
    def get_spot_price(self, asset: str, timestamp: pd.Timestamp) -> float:
        """Get spot price for asset."""
        return self.data['market_prices'].get(asset, 3000.0)


@pytest.mark.asyncio
async def test_onchain_execution_manager():
    """Test OnChain Execution Manager functionality."""
    print("\n🧪 Testing OnChain Execution Manager Component")
    print("=" * 50)
    
    # Initialize components
    position_monitor = PositionMonitor()
    event_logger = EventLogger()
    data_provider = MockDataProvider()
    
    # Test backtest mode
    print("\n📊 Testing backtest mode...")
    onchain_manager = OnChainExecutionManager(
        execution_mode='backtest',
        position_monitor=position_monitor,
        event_logger=event_logger,
        data_provider=data_provider,
        config={'strategy': {}}
    )
    
    print("✅ OnChain execution manager initialized in backtest mode")
    
    # Test atomic leverage entry
    print("\n⚡ Testing atomic leverage entry...")
    timestamp = pd.Timestamp.now(tz=timezone.utc)
    
    result = await onchain_manager.atomic_leverage_loop(
        equity=10000.0,
        target_ltv=0.91,
        lst_type='weeth',
        mode='entry',
        timestamp=timestamp
    )
    
    print(f"✅ Atomic leverage entry executed:")
    print(f"   Operation: {result['operation']}")
    print(f"   Mode: {result['mode']}")
    print(f"   Flash amount: ${result['flash_amount']:,.2f}")
    print(f"   Collateral supplied: ${result['collateral_supplied']:,.2f}")
    print(f"   Debt created: ${result['debt_created']:,.2f}")
    print(f"   Leverage achieved: {result['leverage_achieved']:.2f}x")
    print(f"   Gas cost: {result['gas_cost_eth']:.4f} ETH (${result['gas_cost_usd']:,.2f})")
    
    # Test atomic leverage exit
    print("\n🔄 Testing atomic leverage exit...")
    result = await onchain_manager.atomic_leverage_loop(
        equity=10000.0,
        target_ltv=0.0,  # Full deleverage
        lst_type='weeth',
        mode='exit',
        timestamp=timestamp
    )
    
    print(f"✅ Atomic leverage exit executed:")
    print(f"   Operation: {result['operation']}")
    print(f"   Debt repaid: ${result['debt_repaid']:,.2f}")
    print(f"   Collateral withdrawn: ${result['collateral_withdrawn']:,.2f}")
    print(f"   Gas cost: {result['gas_cost_eth']:.4f} ETH (${result['gas_cost_usd']:,.2f})")
    
    # Test sequential leverage loop
    print("\n🔄 Testing sequential leverage loop...")
    result = await onchain_manager.sequential_leverage_loop(
        initial_eth=5.0,
        target_ltv=0.91,
        lst_type='weeth',
        max_iterations=3,
        timestamp=timestamp
    )
    
    print(f"✅ Sequential leverage loop executed:")
    print(f"   Operation: {result['operation']}")
    print(f"   Mode: {result['mode']}")
    print(f"   Iterations: {len(result['iterations'])}")
    print(f"   Total gas cost: {result['total_gas_cost_eth']:.4f} ETH (${result['total_gas_cost_usd']:,.2f})")
    
    for i, iteration in enumerate(result['iterations']):
        print(f"   Iteration {i+1}: Stake ${iteration['stake_amount']:,.2f}, "
              f"Supply ${iteration['supply_amount']:,.2f}, Borrow ${iteration['borrow_amount']:,.2f}")
    
    # Test fast unwinding
    print("\n⚡ Testing fast unwinding (DEX)...")
    result = await onchain_manager.unwind_position(
        amount_to_unwind=1000.0,
        unwind_mode='fast',
        timestamp=timestamp
    )
    
    print(f"✅ Fast unwinding executed:")
    print(f"   Operation: {result['operation']}")
    print(f"   Mode: {result['mode']}")
    print(f"   Amount unwound: ${result['amount_unwound']:,.2f}")
    print(f"   DEX fee: ${result['dex_fee_usd']:,.2f}")
    print(f"   Slippage: ${result['slippage_usd']:,.2f}")
    print(f"   Gas cost: {result['gas_cost_eth']:.4f} ETH")
    
    # Test slow unwinding
    print("\n🐌 Testing slow unwinding (Protocol)...")
    result = await onchain_manager.unwind_position(
        amount_to_unwind=1000.0,
        unwind_mode='slow',
        timestamp=timestamp
    )
    
    print(f"✅ Slow unwinding executed:")
    print(f"   Operation: {result['operation']}")
    print(f"   Mode: {result['mode']}")
    print(f"   Amount unwound: ${result['amount_unwound']:,.2f}")
    print(f"   Withdrawal queue: {result['withdrawal_queue_days']} days")
    print(f"   Gas cost: {result['gas_cost_eth']:.4f} ETH")
    
    # Test instruction execution
    print("\n📋 Testing instruction execution...")
    instruction = {
        'type': 'ATOMIC_DELEVERAGE',
        'actions': [
            {
                'action': 'ATOMIC_DELEVERAGE_AAVE',
                'executor': 'OnChainExecutionManager',
                'params': {'amount_usd': 5000.0}
            },
            {
                'action': 'TRANSFER_ETH_TO_CEX',
                'executor': 'OnChainExecutionManager',
                'params': {'venue': 'binance', 'amount_eth': 1.0}
            }
        ]
    }
    
    result = await onchain_manager.execute_instruction(instruction, timestamp)
    
    print(f"✅ Instruction executed:")
    print(f"   Type: {result['instruction_type']}")
    print(f"   Success: {result['success']}")
    print(f"   Actions: {len(result['results'])}")
    
    for i, action_result in enumerate(result['results']):
        print(f"   Action {i+1}: {action_result.get('operation', 'Unknown')} - "
              f"{'Success' if action_result.get('success', True) else 'Failed'}")
    
    print("\n✅ Backtest mode test passed")
    
    # Test live mode configuration
    print("\n📊 Testing live mode configuration...")
    onchain_manager_live = OnChainExecutionManager(
        execution_mode='live',
        position_monitor=position_monitor,
        event_logger=event_logger,
        data_provider=data_provider,
        config={
            'web3': {'rpc_url': 'https://eth-mainnet.g.alchemy.com/v2/test-key'}
        }
    )
    
    print("✅ OnChain execution manager initialized in live mode")
    print("✅ Web3 clients initialized (mock)")
    print("✅ Live mode configuration test passed")
    
    print("\n✅ All OnChain Execution Manager tests completed!")


if __name__ == "__main__":
    asyncio.run(test_onchain_execution_manager())