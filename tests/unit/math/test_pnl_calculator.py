#!/usr/bin/env python3
"""
Test script for P&L Calculator component.
"""

import asyncio
import sys
import os
import pandas as pd
from datetime import datetime
import pytest

# Add the backend src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from basis_strategy_v1.core.math.pnl_calculator import PnLCalculator, create_pnl_calculator


@pytest.mark.asyncio
async def test_pnl_calculator():
    """Test the P&L Calculator component."""
    print("🧪 Testing P&L Calculator Component")
    print("=" * 50)
    
    # Create P&L calculator
    calculator = create_pnl_calculator(share_class='USDT', initial_capital=100000.0)
    print("✅ P&L Calculator created for USDT share class with $100,000 initial capital")
    
    # Test data setup - Initial exposure (t=0)
    timestamp_0 = pd.Timestamp('2024-01-01 00:00:00', tz='UTC')
    
    initial_exposure = {
        'timestamp': timestamp_0,
        'total_value_usd': 100000.0,
        'share_class_value': 100000.0,
        'net_delta_eth': 0.0,
        'exposures': {
            'aWeETH': {
                'wallet_balance_scaled': 95.24,
                'underlying_native': 100.0,  # 95.24 * 1.05 (initial index)
                'exposure_eth': 102.56,      # 100.0 * 1.0256 (initial oracle)
                'exposure_usd': 307680.0,    # 102.56 * 3000 (initial ETH price)
                'liquidity_index': 1.05,
                'oracle_price': 1.0256,
                'eth_usd_price': 3000.0
            },
            'variableDebtWETH': {
                'wallet_balance_scaled': 88.70,
                'underlying_native': 95.796,  # 88.70 * 1.08 (initial borrow index)
                'exposure_eth': 95.796,
                'exposure_usd': 287388.0,
                'borrow_index': 1.08,
                'eth_usd_price': 3000.0
            },
            'binance_USDT': {
                'balance': 50000.0,
                'exposure_eth': 16.67,  # 50000 / 3000
                'exposure_usd': 50000.0
            }
        }
    }
    
    # First calculation (t=0) - should set initial value
    print("\n📊 Testing initial P&L calculation (t=0)...")
    
    pnl_0 = await calculator.calculate_pnl(
        current_exposure=initial_exposure,
        timestamp=timestamp_0
    )
    
    print(f"✅ Initial P&L calculated")
    print(f"   Initial value: ${pnl_0['balance_based']['total_value_initial']:,.2f}")
    print(f"   Current value: ${pnl_0['balance_based']['total_value_current']:,.2f}")
    print(f"   P&L cumulative: ${pnl_0['balance_based']['pnl_cumulative']:,.2f}")
    print(f"   P&L %: {pnl_0['balance_based']['pnl_pct']:.2f}%")
    
    # Test data setup - After 1 hour (t=1)
    timestamp_1 = pd.Timestamp('2024-01-01 01:00:00', tz='UTC')
    
    # Simulate some changes:
    # - AAVE index grew slightly (1.05 → 1.051)
    # - Oracle price grew slightly (1.0256 → 1.0257)
    # - ETH price increased (3000 → 3010)
    
    exposure_1 = {
        'timestamp': timestamp_1,
        'total_value_usd': 100246.33,  # Slightly higher due to yields and price increase
        'share_class_value': 100246.33,
        'net_delta_eth': 0.1,  # Small delta drift
        'exposures': {
            'aWeETH': {
                'wallet_balance_scaled': 95.24,  # Same (constant)
                'underlying_native': 100.095,    # 95.24 * 1.051 (index grew)
                'exposure_eth': 102.68,          # 100.095 * 1.0257 (oracle grew)
                'exposure_usd': 309070.68,       # 102.68 * 3010 (ETH price up)
                'liquidity_index': 1.051,
                'oracle_price': 1.0257,
                'eth_usd_price': 3010.0
            },
            'variableDebtWETH': {
                'wallet_balance_scaled': 88.70,  # Same (constant)
                'underlying_native': 95.796,     # Same (no borrow cost in this hour)
                'exposure_eth': 95.796,
                'exposure_usd': 288345.96,       # 95.796 * 3010 (ETH price up)
                'borrow_index': 1.08,
                'eth_usd_price': 3010.0
            },
            'binance_USDT': {
                'balance': 50000.0,
                'exposure_eth': 16.61,  # 50000 / 3010
                'exposure_usd': 50000.0
            }
        }
    }
    
    # Second calculation (t=1) - should show P&L
    print("\n📈 Testing P&L calculation after 1 hour (t=1)...")
    
    pnl_1 = await calculator.calculate_pnl(
        current_exposure=exposure_1,
        previous_exposure=initial_exposure,
        timestamp=timestamp_1
    )
    
    print(f"✅ Hourly P&L calculated")
    print(f"   Balance-based P&L: ${pnl_1['balance_based']['pnl_cumulative']:,.2f}")
    print(f"   Attribution P&L: ${pnl_1['attribution']['pnl_cumulative']:,.2f}")
    print(f"   Reconciliation: {'✅ PASSED' if pnl_1['reconciliation']['passed'] else '⚠️ FAILED'}")
    
    # Test attribution breakdown
    print("\n🔍 Testing attribution breakdown...")
    
    attribution = pnl_1['attribution']
    print(f"   Supply P&L: ${attribution['supply_pnl']:,.2f}")
    print(f"   Staking P&L: ${attribution['staking_pnl']:,.2f}")
    print(f"   Price change P&L: ${attribution['price_change_pnl']:,.2f}")
    print(f"   Borrow cost: ${attribution['borrow_cost']:,.2f}")
    print(f"   Funding P&L: ${attribution['funding_pnl']:,.2f}")
    print(f"   Delta P&L: ${attribution['delta_pnl']:,.2f}")
    print(f"   Total hourly: ${attribution['pnl_hourly']:,.2f}")
    
    # Test reconciliation
    print("\n⚖️ Testing reconciliation...")
    
    recon = pnl_1['reconciliation']
    print(f"   Balance P&L: ${recon['balance_pnl']:,.2f}")
    print(f"   Attribution P&L: ${recon['attribution_pnl']:,.2f}")
    print(f"   Difference: ${recon['difference']:,.2f}")
    print(f"   Tolerance: ${recon['tolerance']:,.2f}")
    print(f"   Passed: {recon['passed']}")
    print(f"   Diff % of capital: {recon['diff_pct_of_capital']:.3f}%")
    
    # Test with funding time (8:00 UTC)
    print("\n💸 Testing funding P&L calculation...")
    
    timestamp_funding = pd.Timestamp('2024-01-01 08:00:00', tz='UTC')
    
    # Add perp positions for funding calculation
    exposure_funding = exposure_1.copy()
    exposure_funding['exposures']['binance_ETHUSDT-PERP'] = {
        'size': -8.562,
        'mark_price': 3010.0,
        'exposure_usd': 25781.62
    }
    
    pnl_funding = await calculator.calculate_pnl(
        current_exposure=exposure_funding,
        previous_exposure=exposure_1,
        timestamp=timestamp_funding
    )
    
    print(f"   Funding P&L: ${pnl_funding['attribution']['funding_pnl']:,.2f}")
    print(f"   Total hourly: ${pnl_funding['attribution']['pnl_hourly']:,.2f}")
    
    # Test P&L summary
    print("\n📋 Testing P&L summary...")
    
    summary = calculator.get_pnl_summary(pnl_1)
    print(summary)
    
    # Test cumulative tracking
    print("\n📊 Testing cumulative tracking...")
    
    print(f"   Cumulative supply P&L: ${calculator.cumulative['supply_pnl']:,.2f}")
    print(f"   Cumulative staking P&L: ${calculator.cumulative['staking_yield_oracle']:,.2f}")
    print(f"   Cumulative borrow cost: ${calculator.cumulative['borrow_cost']:,.2f}")
    print(f"   Cumulative funding P&L: ${calculator.cumulative['funding_pnl']:,.2f}")
    print(f"   Cumulative delta P&L: ${calculator.cumulative['delta_pnl']:,.2f}")
    
    print("\n✅ P&L Calculator tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_pnl_calculator())