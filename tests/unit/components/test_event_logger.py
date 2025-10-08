#!/usr/bin/env python3
"""
Test script for Event Logger component.
"""

import asyncio
import sys
import os
import pandas as pd
from datetime import datetime
import pytest

# Add the backend src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from basis_strategy_v1.core.strategies.components.event_logger import EventLogger, create_event_logger


@pytest.mark.asyncio
async def test_event_logger():
    """Test the Event Logger component."""
    print("🧪 Testing Event Logger Component")
    print("=" * 50)
    
    # Create event logger
    logger = create_event_logger(execution_mode='backtest', include_balance_snapshots=True)
    print("✅ Event Logger created")
    
    # Test basic event logging
    print("\n📝 Testing basic event logging...")
    
    timestamp = pd.Timestamp.now(tz='UTC')
    
    # Test gas fee logging
    order1 = await logger.log_gas_fee(
        timestamp=timestamp,
        gas_cost_eth=0.0035,
        gas_cost_usd=8.75,
        operation_type="STAKE_DEPOSIT",
        gas_units=150000,
        gas_price_gwei=25.0
    )
    print(f"⛽ Gas fee logged with order: {order1}")
    
    # Test staking operation
    order2 = await logger.log_stake(
        timestamp=timestamp,
        venue="ETHERFI",
        eth_in=50.0,
        lst_out=49.8,
        oracle_price=3000.0
    )
    print(f"🏦 Staking logged with order: {order2}")
    
    # Test AAVE supply
    order3 = await logger.log_aave_supply(
        timestamp=timestamp,
        token="weETH",
        amount_supplied=49.8,
        atoken_received=47.43,  # 49.8 / 1.05 (liquidity index)
        liquidity_index=1.05
    )
    print(f"🏛️ AAVE supply logged with order: {order3}")
    
    # Test AAVE borrow
    order4 = await logger.log_aave_borrow(
        timestamp=timestamp,
        token="WETH",
        amount_borrowed=40.0,
        debt_token_received=38.1,  # 40.0 / 1.05 (liquidity index)
        liquidity_index=1.05
    )
    print(f"💰 AAVE borrow logged with order: {order4}")
    
    # Test perp trade
    order5 = await logger.log_perp_trade(
        timestamp=timestamp,
        venue="binance",
        instrument="ETHUSDT-PERP",
        side="SHORT",
        size_eth=8.562,
        entry_price=2920.0,
        notional_usd=25000.0,
        execution_cost_usd=7.50
    )
    print(f"📈 Perp trade logged with order: {order5}")
    
    # Test funding payment
    order6 = await logger.log_funding_payment(
        timestamp=timestamp,
        venue="binance",
        funding_rate=0.0001,
        notional_usd=25000.0,
        pnl_usd=-2.50  # Negative = paid funding
    )
    print(f"💸 Funding payment logged with order: {order6}")
    
    # Test venue transfer
    order7 = await logger.log_venue_transfer(
        timestamp=timestamp,
        from_venue="WALLET",
        to_venue="binance",
        token="USDT",
        amount=50000.0,
        purpose="Transfer USDT for perp trading"
    )
    print(f"💱 Venue transfer logged with order: {order7}")
    
    # Test atomic transaction (flash loan bundle)
    print("\n🔄 Testing atomic transaction logging...")
    
    detail_events = [
        {
            'event_type': 'FLASH_BORROW',
            'venue': 'BALANCER',
            'token': 'WETH',
            'amount': 100.0,
            'purpose': 'Flash borrow WETH for leverage loop'
        },
        {
            'event_type': 'STAKE_DEPOSIT',
            'venue': 'ETHERFI',
            'token': 'ETH',
            'amount': 100.0,
            'purpose': 'Stake borrowed ETH'
        },
        {
            'event_type': 'COLLATERAL_SUPPLIED',
            'venue': 'AAVE',
            'token': 'weETH',
            'amount': 99.5,
            'purpose': 'Supply staked weETH as collateral'
        },
        {
            'event_type': 'LOAN_CREATED',
            'venue': 'AAVE',
            'token': 'WETH',
            'amount': 80.0,
            'purpose': 'Borrow against collateral'
        },
        {
            'event_type': 'FLASH_REPAID',
            'venue': 'BALANCER',
            'token': 'WETH',
            'amount': 100.0,
            'purpose': 'Repay flash loan'
        }
    ]
    
    net_result = {
        'collateral_added': 47.43,  # aWeETH received
        'debt_added': 38.1,         # debt token received
        'net_leverage': 1.8
    }
    
    orders = await logger.log_atomic_transaction(
        timestamp=timestamp,
        bundle_name="ATOMIC_LEVERAGE_ENTRY",
        detail_events=detail_events,
        net_result=net_result
    )
    print(f"⚡ Atomic transaction logged with orders: {orders}")
    
    # Test risk alert
    order8 = await logger.log_risk_alert(
        timestamp=timestamp,
        risk_type="HEALTH_FACTOR",
        current_value=1.15,
        threshold=1.20,
        severity="WARNING"
    )
    print(f"⚠️ Risk alert logged with order: {order8}")
    
    # Test rebalance
    order9 = await logger.log_rebalance(
        timestamp=timestamp,
        rebalance_type="DELTA_HEDGE",
        delta_exposure=-0.05,
        actions_taken=["SHORT_ETH_PERP", "ADJUST_LEVERAGE"]
    )
    print(f"⚖️ Rebalance logged with order: {order9}")
    
    # Test event queries
    print("\n🔍 Testing event queries...")
    
    gas_events = logger.get_events_by_type('GAS_FEE_PAID')
    print(f"📊 Gas fee events: {len(gas_events)}")
    
    aave_events = logger.get_events_by_venue('AAVE')
    print(f"📊 AAVE events: {len(aave_events)}")
    
    recent_events = logger.get_events_by_order_range(1, 5)
    print(f"📊 Events 1-5: {len(recent_events)}")
    
    # Test summary stats
    print("\n📈 Summary Statistics:")
    stats = logger.get_summary_stats()
    print(f"   Total events: {stats['total_events']}")
    print(f"   Event types: {stats['event_types']}")
    print(f"   Venues: {stats['venues']}")
    print(f"   Total amount: {stats['total_amount']}")
    print(f"   Order range: {stats['first_event_order']} - {stats['last_event_order']}")
    
    # Test CSV export
    print("\n💾 Testing CSV export...")
    csv_file = logger.export_to_csv("test_event_log.csv")
    print(f"📄 Events exported to: {csv_file}")
    
    # Test global order uniqueness
    print("\n🔢 Testing global order uniqueness...")
    all_orders = [event['order'] for event in logger.events]
    unique_orders = set(all_orders)
    print(f"   Total events: {len(all_orders)}")
    print(f"   Unique orders: {len(unique_orders)}")
    print(f"   Orders unique: {len(all_orders) == len(unique_orders)}")
    
    # Test balance snapshots
    print("\n📸 Testing balance snapshots...")
    events_with_snapshots = [e for e in logger.events if 'wallet_balance_after' in e]
    print(f"   Events with snapshots: {len(events_with_snapshots)}")
    
    print("\n✅ Event Logger tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_event_logger())