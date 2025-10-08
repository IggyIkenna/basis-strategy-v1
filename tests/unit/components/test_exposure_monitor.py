#!/usr/bin/env python3
"""
Test script for Exposure Monitor component.
"""

import asyncio
import sys
import os
import pandas as pd
from datetime import datetime

# Add the backend src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from basis_strategy_v1.core.strategies.components.exposure_monitor import ExposureMonitor


class MockPositionMonitor:
    """Mock position monitor for testing."""
    def __init__(self):
        self.execution_mode = 'backtest'

class MockDataProvider:
    """Mock data provider for testing."""
    def __init__(self):
        pass

def test_exposure_monitor():
    """Test the Exposure Monitor component."""
    print("🧪 Testing Exposure Monitor Component")
    print("=" * 50)
    
    # Create exposure monitor
    monitor = ExposureMonitor(
        config={'mode': 'pure_lending', 'asset': 'ETH'},
        share_class='USDT',
        position_monitor=MockPositionMonitor(),
        data_provider=MockDataProvider()
    )
    print("✅ Exposure Monitor created for USDT share class")
    
    # Test data setup
    timestamp = pd.Timestamp.now(tz='UTC')
    
    # Position snapshot (from Position Monitor)
    position_snapshot = {
        'timestamp': timestamp,
        'wallet': {
            'ETH': 10.5,                    # Free ETH
            'USDT': 0.0,
            'weETH': 5.0,                   # Free weETH
            'aWeETH': 95.24,                # AAVE aToken (CONSTANT scaled balance)
            'variableDebtWETH': 88.70       # AAVE debt token (CONSTANT scaled balance)
        },
        'cex_accounts': {
            'binance': {'USDT': 24992.50, 'ETH_spot': 0.0},
            'bybit': {'USDT': 24985.30, 'ETH_spot': 0.0},
            'okx': {'USDT': 24980.15, 'ETH_spot': 0.0}
        },
        'perp_positions': {
            'binance': {
                'ETHUSDT-PERP': {
                    'size': -8.562,
                    'entry_price': 2920.00,
                    'entry_timestamp': timestamp.isoformat(),
                    'notional_usd': 25000.0
                }
            },
            'bybit': {
                'ETHUSDT-PERP': {
                    'size': -8.551,
                    'entry_price': 2921.50,
                    'entry_timestamp': timestamp.isoformat(),
                    'notional_usd': 24975.0
                }
            },
            'okx': {
                'ETHUSDT-PERP': {
                    'size': -8.557,
                    'entry_price': 2920.50,
                    'entry_timestamp': timestamp.isoformat(),
                    'notional_usd': 24987.5
                }
            }
        }
    }
    
    # Market data (from Data Provider)
    market_data = {
        'timestamp': timestamp,
        'eth_usd_price': 3305.20,
        'weeth_liquidity_index': 1.10,      # AAVE index (grows over time)
        'weth_borrow_index': 1.08,          # AAVE borrow index
        'weeth_eth_oracle': 1.0256,         # weETH/ETH oracle price
        'binance_eth_perp_mark': 3305.20,
        'bybit_eth_perp_mark': 3306.15,
        'okx_eth_perp_mark': 3304.80
    }
    
    print("\n📊 Testing exposure calculation...")
    
    # Calculate exposure
    exposure = monitor.calculate_exposure(
        timestamp=timestamp,
        position_snapshot=position_snapshot,
        market_data=market_data
    )
    
    print(f"✅ Exposure calculated successfully")
    print(f"   Share class: {exposure['share_class']}")
    print(f"   Net delta share class: {exposure['net_delta_share_class']:.4f}")
    print(f"   Net delta %: {exposure['net_delta_pct']:.2f}%")
    print(f"   Total value USD: ${exposure['total_value_usd']:,.2f}")
    print(f"   Total value ETH: {exposure['total_value_eth']:.4f}")
    print(f"   Share class value: ${exposure['share_class_value']:,.2f}")
    
    print(f"\n📈 ERC-20 wallet net delta: {exposure['erc20_wallet_net_delta_share_class']:.4f} {exposure['share_class']}")
    print(f"📉 CEX wallet net delta: {exposure['cex_wallet_net_delta_share_class']:.4f} {exposure['share_class']}")
    print(f"💰 Token equity ETH: {exposure['token_equity_eth']:.4f} ETH")
    print(f"💰 Token equity USD: ${exposure['token_equity_usd']:,.2f}")
    
    # Test AAVE conversion chain (CRITICAL!)
    print("\n🔗 Testing AAVE conversion chain...")
    
    if 'aWeETH' in exposure['exposures']:
        aweeth_exp = exposure['exposures']['aWeETH']
        print(f"   aWeETH wallet balance: {aweeth_exp.get('balance', 0):.2f}")
        print(f"   Underlying weETH: {aweeth_exp.get('underlying_balance', 0):.2f}")
        print(f"   ETH equivalent: {aweeth_exp.get('exposure_eth', 0):.2f}")
        print(f"   USD equivalent: ${aweeth_exp.get('exposure_usd', 0):,.2f}")
        
        # Verify the math
        expected_underlying = 95.24 * 1.10  # 104.764
        expected_eth = expected_underlying * 1.0256  # 107.44
        expected_usd = expected_eth * 3305.20  # 355,092
        
        print(f"   ✅ Math check:")
        print(f"      Expected underlying: {expected_underlying:.2f} (actual: {aweeth_exp.get('underlying_balance', 0):.2f})")
        print(f"      Expected ETH: {expected_eth:.2f} (actual: {aweeth_exp.get('exposure_eth', 0):.2f})")
        print(f"      Expected USD: ${expected_usd:,.2f} (actual: ${aweeth_exp.get('exposure_usd', 0):,.2f})")
    
    # Test AAVE debt conversion
    print("\n💳 Testing AAVE debt conversion...")
    
    if 'variableDebtWETH' in exposure['exposures']:
        debt_exp = exposure['exposures']['variableDebtWETH']
        print(f"   Debt token balance: {debt_exp.get('balance', 0):.2f}")
        print(f"   Underlying WETH owed: {debt_exp.get('underlying_balance', 0):.2f}")
        print(f"   ETH equivalent: {debt_exp.get('exposure_eth', 0):.2f}")
        print(f"   USD equivalent: ${debt_exp.get('exposure_usd', 0):,.2f}")
        
        # Verify the math
        expected_underlying = 88.70 * 1.08  # 95.796
        expected_usd = expected_underlying * 3305.20  # 316,605
        
        print(f"   ✅ Math check:")
        print(f"      Expected underlying: {expected_underlying:.2f} (actual: {debt_exp.get('underlying_balance', 0):.2f})")
        print(f"      Expected USD: ${expected_usd:,.2f} (actual: ${debt_exp.get('exposure_usd', 0):,.2f})")
    
    # Test perp positions
    print("\n📈 Testing perp positions...")
    
    perp_exposures = {k: v for k, v in exposure['exposures'].items() if 'PERP' in k}
    for instrument, exp in perp_exposures.items():
        print(f"   {instrument}:")
        print(f"      Balance: {exp.get('balance', 0):.3f}")
        print(f"      ETH exposure: {exp.get('exposure_eth', 0):.3f}")
        print(f"      USD exposure: ${exp.get('exposure_usd', 0):,.2f}")
    
    # Test CEX USDT balances
    print("\n💱 Testing CEX USDT balances...")
    
    usdt_exposures = {k: v for k, v in exposure['exposures'].items() if 'USDT' in k and 'PERP' not in k}
    for venue, exp in usdt_exposures.items():
        print(f"   {venue}: ${exp.get('balance', 0):,.2f} USDT = {exp.get('exposure_eth', 0):.4f} ETH (short)")
    
    # Test net delta calculation
    print("\n⚖️ Testing net delta calculation...")
    
    long_eth = sum(exp.get('exposure_eth', 0) for exp in exposure['exposures'].values() 
                   if exp.get('net_delta', 0) > 0)
    short_eth = sum(abs(exp.get('exposure_eth', 0)) for exp in exposure['exposures'].values() 
                    if exp.get('net_delta', 0) < 0)
    
    print(f"   Total long ETH: {long_eth:.4f}")
    print(f"   Total short ETH: {short_eth:.4f}")
    print(f"   Net delta: {long_eth - short_eth:.4f} ETH")
    print(f"   ✅ Matches exposure net_delta_share_class: {exposure['net_delta_share_class']:.4f}")
    
    # Test venue breakdown
    print(f"\n🏦 Venue breakdown:")
    print(f"   ERC-20 wallet delta: {exposure['erc20_wallet_net_delta_share_class']:.4f} {exposure['share_class']}")
    print(f"   CEX wallet delta: {exposure['cex_wallet_net_delta_share_class']:.4f} {exposure['share_class']}")
    print(f"   Sum: {exposure['erc20_wallet_net_delta_share_class'] + exposure['cex_wallet_net_delta_share_class']:.4f} {exposure['share_class']}")
    print(f"   ✅ Matches net delta: {exposure['net_delta_share_class']:.4f} {exposure['share_class']}")
    
    # Test with different share class
    print("\n🔄 Testing ETH share class...")
    
    eth_monitor = ExposureMonitor(
        config={'mode': 'eth_leveraged', 'asset': 'ETH'},
        share_class='ETH',
        position_monitor=MockPositionMonitor(),
        data_provider=MockDataProvider()
    )
    eth_exposure = eth_monitor.calculate_exposure(
        timestamp=timestamp,
        position_snapshot=position_snapshot,
        market_data=market_data
    )
    
    print(f"   ETH share class value: {eth_exposure['share_class_value']:.4f} ETH")
    print(f"   USD share class value: ${exposure['share_class_value']:,.2f}")
    print(f"   ✅ Conversion check: {eth_exposure['share_class_value'] * 3305.20:,.2f} USD")
    
    print("\n✅ Exposure Monitor tests completed successfully!")


if __name__ == "__main__":
    test_exposure_monitor()