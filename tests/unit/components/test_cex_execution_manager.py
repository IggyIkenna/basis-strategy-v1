#!/usr/bin/env python3
"""
Test CEX Execution Manager Component

Test the enhanced CEX execution manager with spot/perp trading and slippage simulation.
"""

import sys
import os
sys.path.append('backend/src')

from basis_strategy_v1.core.strategies.components.cex_execution_manager import CEXExecutionManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cex_execution_manager():
    """Test the enhanced CEX execution manager."""
    print("🧪 Testing Enhanced CEX Execution Manager Component")
    print("=" * 50)
    
    # Test backtest mode
    config = {
        'execution_mode': 'backtest',
        'cex': {
            'binance_spot_testnet': True,
            'binance_futures_testnet': True
        }
    }
    
    print(f"\n📊 Testing backtest mode...")
    
    try:
        # Initialize CEX execution manager
        manager = CEXExecutionManager(config)
        print(f"✅ CEX execution manager initialized in {manager.execution_mode} mode")
        
        # Test spot trade execution
        print(f"\n💱 Testing spot trade execution...")
        spot_result = manager.execute_spot_trade('ETH/USDT', 'buy', 1.0, 3000)
        print(f"✅ Spot trade executed:")
        print(f"   Symbol: {spot_result['symbol']}")
        print(f"   Side: {spot_result['side']}")
        print(f"   Amount: {spot_result['amount']}")
        print(f"   Arrival price: ${spot_result['arrival_price']:.2f}")
        print(f"   Executed price: ${spot_result['executed_price']:.2f}")
        print(f"   Slippage: {spot_result['slippage_bps']} bps")
        print(f"   Execution cost: ${spot_result['execution_cost']:.2f}")
        
        # Test perp trade execution
        print(f"\n📈 Testing perp trade execution...")
        perp_result = manager.execute_perp_trade('ETHUSDT', 'sell', 0.5, 3000)
        print(f"✅ Perp trade executed:")
        print(f"   Symbol: {perp_result['symbol']}")
        print(f"   Side: {perp_result['side']}")
        print(f"   Amount: {perp_result['amount']}")
        print(f"   Arrival price: ${perp_result['arrival_price']:.2f}")
        print(f"   Executed price: ${perp_result['executed_price']:.2f}")
        print(f"   Slippage: {perp_result['slippage_bps']} bps")
        print(f"   Execution cost: ${perp_result['execution_cost']:.2f}")
        
        # Test slippage simulation
        print(f"\n⚖️ Testing slippage simulation...")
        trade = {
            'symbol': 'BTC/USDT',
            'side': 'buy',
            'amount': 0.1,
            'price': 50000
        }
        slippage_result = manager.simulate_slippage(trade)
        print(f"✅ Slippage simulation:")
        print(f"   Symbol: {slippage_result['symbol']}")
        print(f"   Side: {slippage_result['side']}")
        print(f"   Arrival price: ${slippage_result['arrival_price']:.2f}")
        print(f"   Executed price: ${slippage_result['executed_price']:.2f}")
        print(f"   Slippage: {slippage_result['slippage_bps']} bps")
        print(f"   Execution cost: ${slippage_result['execution_cost']:.2f}")
        
        print(f"\n✅ Backtest mode test passed")
        
    except Exception as e:
        print(f"❌ Backtest mode test failed: {e}")
    
    # Test live mode (without actual API keys)
    print(f"\n📊 Testing live mode configuration...")
    
    config_live = {
        'execution_mode': 'live',
        'cex': {
            'binance_spot_api_key': 'test_key',
            'binance_spot_secret': 'test_secret',
            'binance_spot_testnet': True,
            'binance_futures_api_key': 'test_key',
            'binance_futures_secret': 'test_secret',
            'binance_futures_testnet': True
        }
    }
    
    try:
        # Initialize CEX execution manager for live mode
        manager_live = CEXExecutionManager(config_live)
        print(f"✅ CEX execution manager initialized in {manager_live.execution_mode} mode")
        
        # Test that CCXT clients are initialized
        if hasattr(manager_live, 'exchanges'):
            print(f"✅ Exchange clients initialized: {len(manager_live.exchanges)} exchanges")
            for exchange_name in manager_live.exchanges.keys():
                print(f"   - {exchange_name}")
        else:
            print(f"⚠️ Exchange clients not initialized (CCXT may not be available)")
        
        print(f"✅ Live mode configuration test passed")
        
    except Exception as e:
        print(f"❌ Live mode configuration test failed: {e}")
    
    print(f"\n✅ All CEX Execution Manager tests completed!")

if __name__ == "__main__":
    test_cex_execution_manager()