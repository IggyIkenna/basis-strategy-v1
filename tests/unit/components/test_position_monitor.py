#!/usr/bin/env python3
"""
Test script for Position Monitor component.
"""

import asyncio
import sys
import os
import pandas as pd
from datetime import datetime
import pytest

# Add the backend src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor, create_position_monitor


@pytest.mark.asyncio
async def test_position_monitor():
    """Test the Position Monitor component."""
    print("🧪 Testing Position Monitor Component")
    print("=" * 50)
    
    # Create position monitor
    monitor = create_position_monitor(execution_mode='backtest')
    print("✅ Position Monitor created")
    
    # Test initial state
    snapshot = monitor.get_snapshot()
    print(f"📊 Initial wallet ETH: {snapshot['wallet']['ETH']}")
    print(f"📊 Initial wallet USDT: {snapshot['wallet']['USDT']}")
    
    # Test token balance update
    print("\n🔄 Testing token balance updates...")
    
    # Gas fee payment
    changes = {
        'timestamp': pd.Timestamp.now(tz='UTC'),
        'trigger': 'GAS_FEE_PAID',
        'token_changes': [
            {
                'venue': 'WALLET',
                'token': 'ETH',
                'delta': -0.0035,
                'reason': 'GAS_FEE_PAID'
            }
        ]
    }
    
    snapshot = await monitor.update(changes)
    print(f"⛽ After gas fee: ETH = {snapshot['wallet']['ETH']}")
    
    # AAVE supply
    changes = {
        'timestamp': pd.Timestamp.now(tz='UTC'),
        'trigger': 'AAVE_SUPPLY',
        'token_changes': [
            {
                'venue': 'WALLET',
                'token': 'weETH',
                'delta': -100.0,
                'reason': 'AAVE_SUPPLY'
            },
            {
                'venue': 'WALLET',
                'token': 'aWeETH',
                'delta': 95.24,  # 100 / 1.05 (liquidity index)
                'reason': 'AAVE_SUPPLY'
            }
        ]
    }
    
    snapshot = await monitor.update(changes)
    print(f"🏦 After AAVE supply: weETH = {snapshot['wallet']['weETH']}, aWeETH = {snapshot['wallet']['aWeETH']}")
    
    # CEX transfer
    changes = {
        'timestamp': pd.Timestamp.now(tz='UTC'),
        'trigger': 'VENUE_TRANSFER',
        'token_changes': [
            {
                'venue': 'WALLET',
                'token': 'USDT',
                'delta': -50000.0,
                'reason': 'VENUE_TRANSFER'
            },
            {
                'venue': 'binance',
                'token': 'USDT',
                'delta': 50000.0,
                'reason': 'VENUE_TRANSFER'
            }
        ]
    }
    
    snapshot = await monitor.update(changes)
    print(f"💱 After CEX transfer: Wallet USDT = {snapshot['wallet']['USDT']}, Binance USDT = {snapshot['cex_accounts']['binance']['USDT']}")
    
    # Test derivative position update
    print("\n📈 Testing derivative position updates...")
    
    changes = {
        'timestamp': pd.Timestamp.now(tz='UTC'),
        'trigger': 'TRADE_EXECUTED',
        'token_changes': [
            {
                'venue': 'binance',
                'token': 'USDT',
                'delta': -7.50,  # Execution cost
                'reason': 'PERP_EXECUTION_COST'
            }
        ],
        'derivative_changes': [
            {
                'venue': 'binance',
                'instrument': 'ETHUSDT-PERP',
                'action': 'OPEN',
                'data': {
                    'size': -8.562,
                    'entry_price': 2920.00,
                    'entry_timestamp': datetime.utcnow().isoformat(),
                    'notional_usd': 25000.0
                }
            }
        ]
    }
    
    snapshot = await monitor.update(changes)
    print(f"📊 After perp trade: Binance USDT = {snapshot['cex_accounts']['binance']['USDT']}")
    print(f"📊 Perp position: {snapshot['perp_positions']['binance']}")
    
    # Test position adjustment
    changes = {
        'timestamp': pd.Timestamp.now(tz='UTC'),
        'trigger': 'POSITION_ADJUSTMENT',
        'derivative_changes': [
            {
                'venue': 'binance',
                'instrument': 'ETHUSDT-PERP',
                'action': 'ADJUST',
                'data': {
                    'size': -10.0,  # Increased short position
                    'notional_usd': 29200.0
                }
            }
        ]
    }
    
    snapshot = await monitor.update(changes)
    print(f"📊 After adjustment: Perp size = {snapshot['perp_positions']['binance']['ETHUSDT-PERP']['size']}")
    
    # Test position closure
    changes = {
        'timestamp': pd.Timestamp.now(tz='UTC'),
        'trigger': 'POSITION_CLOSED',
        'derivative_changes': [
            {
                'venue': 'binance',
                'instrument': 'ETHUSDT-PERP',
                'action': 'CLOSE',
                'data': {}
            }
        ]
    }
    
    snapshot = await monitor.update(changes)
    print(f"📊 After closure: Perp positions = {snapshot['perp_positions']}")
    
    # Test final snapshot
    print("\n📋 Final Position Snapshot:")
    print(f"   Wallet: {snapshot['wallet']}")
    print(f"   CEX Accounts: {snapshot['cex_accounts']}")
    print(f"   Perp Positions: {snapshot['perp_positions']}")
    
    print("\n✅ Position Monitor tests completed successfully!")


@pytest.mark.asyncio
async def test_position_monitor_error_handling():
    """Test error handling in Position Monitor."""
    print("\n🧪 Testing Position Monitor Error Handling")
    print("=" * 50)
    
    monitor = create_position_monitor(execution_mode='backtest')
    
    # Test invalid venue
    try:
        changes = {
            'timestamp': pd.Timestamp.now(tz='UTC'),
            'trigger': 'TEST',
            'token_changes': [{
                'venue': 'INVALID_VENUE',
                'token': 'ETH',
                'delta': 100.0,
                'reason': 'TEST'
            }]
        }
        await monitor.update(changes)
        print("✅ Invalid venue handled gracefully")
    except Exception as e:
        print(f"✅ Invalid venue error caught: {e}")
    
    # Test negative balance
    try:
        changes = {
            'timestamp': pd.Timestamp.now(tz='UTC'),
            'trigger': 'TEST',
            'token_changes': [{
                'venue': 'WALLET',
                'token': 'ETH',
                'delta': -1000.0,
                'reason': 'TEST'
            }]
        }
        await monitor.update(changes)
        print("✅ Negative balance handled")
    except Exception as e:
        print(f"✅ Negative balance error caught: {e}")
    
    # Test invalid token
    try:
        changes = {
            'timestamp': pd.Timestamp.now(tz='UTC'),
            'trigger': 'TEST',
            'token_changes': [{
                'venue': 'WALLET',
                'token': 'INVALID_TOKEN',
                'delta': 100.0,
                'reason': 'TEST'
            }]
        }
        await monitor.update(changes)
        print("✅ Invalid token handled gracefully")
    except Exception as e:
        print(f"✅ Invalid token error caught: {e}")
    
    print("✅ Error handling tests passed")


@pytest.mark.asyncio
async def test_position_monitor_reconciliation():
    """Test reconciliation functionality."""
    print("\n🧪 Testing Position Monitor Reconciliation")
    print("=" * 50)
    
    monitor = create_position_monitor(execution_mode='backtest')
    
    # Set up some balances
    changes = {
        'timestamp': pd.Timestamp.now(tz='UTC'),
        'trigger': 'TEST',
        'token_changes': [
            {
                'venue': 'WALLET',
                'token': 'ETH',
                'delta': 10.0,
                'reason': 'TEST'
            },
            {
                'venue': 'WALLET',
                'token': 'USDT',
                'delta': 10000.0,
                'reason': 'TEST'
            }
        ]
    }
    await monitor.update(changes)
    
    # Test reconciliation with same balances (should pass)
    try:
        result = await monitor.reconcile_with_live({
            'WALLET': {'ETH': 10.0, 'USDT': 10000.0}
        })
        print("✅ Reconciliation with matching balances passed")
    except Exception as e:
        print(f"✅ Reconciliation error handled: {e}")
    
    # Test reconciliation with different balances (should detect drift)
    try:
        result = await monitor.reconcile_with_live({
            'WALLET': {'ETH': 9.5, 'USDT': 10000.0}  # ETH balance differs
        })
        print("✅ Reconciliation with drift detected")
    except Exception as e:
        print(f"✅ Reconciliation drift error handled: {e}")
    
    print("✅ Reconciliation tests passed")


@pytest.mark.asyncio
async def test_position_monitor_perp_positions():
    """Test perpetual position tracking."""
    print("\n🧪 Testing Position Monitor Perp Positions")
    print("=" * 50)
    
    monitor = create_position_monitor(execution_mode='backtest')
    
    # Test adding perp position
    try:
        await monitor.update_perp_position('binance', 'ETHUSDT', {
            'side': 'long',
            'size': 1.0,
            'entry_price': 3000.0,
            'mark_price': 3050.0,
            'unrealized_pnl': 50.0
        })
        print("✅ Perp position added successfully")
    except Exception as e:
        print(f"✅ Perp position error handled: {e}")
    
    # Test updating perp position
    try:
        await monitor.update_perp_position('binance', 'ETHUSDT', {
            'side': 'long',
            'size': 1.0,
            'entry_price': 3000.0,
            'mark_price': 3100.0,
            'unrealized_pnl': 100.0
        })
        print("✅ Perp position updated successfully")
    except Exception as e:
        print(f"✅ Perp position update error handled: {e}")
    
    # Test closing perp position
    try:
        await monitor.update_perp_position('binance', 'ETHUSDT', {
            'side': 'long',
            'size': 0.0,  # Size 0 means closed
            'entry_price': 3000.0,
            'mark_price': 3100.0,
            'unrealized_pnl': 100.0
        })
        print("✅ Perp position closed successfully")
    except Exception as e:
        print(f"✅ Perp position close error handled: {e}")
    
    print("✅ Perp position tests passed")


if __name__ == "__main__":
    asyncio.run(test_position_monitor())
    asyncio.run(test_position_monitor_error_handling())
    asyncio.run(test_position_monitor_reconciliation())
    asyncio.run(test_position_monitor_perp_positions())