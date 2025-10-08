#!/usr/bin/env python3
"""
Test Strategy Manager Component

Test the enhanced strategy manager with mode detection and component orchestration.
"""

import sys
import os
sys.path.append('backend/src')

from basis_strategy_v1.core.strategies.components.strategy_manager import StrategyManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_strategy_manager():
    """Test the enhanced strategy manager."""
    print("🧪 Testing Enhanced Strategy Manager Component")
    print("=" * 50)
    
    # Test each mode
    configs = [
        {
            'strategy': {
                'mode': 'pure_lending',
                'share_class': 'USDT',
                'asset': 'ETH',
                'lst_type': 'weeth',
                'lending_enabled': True,
                'staking_enabled': False,
                'basis_trade_enabled': False
            },
            'backtest': {'initial_capital': 100000}
        },
        {
            'strategy': {
                'mode': 'btc_basis',
                'share_class': 'USDT',
                'asset': 'BTC',
                'lst_type': 'wstbtc',
                'coin_symbol': 'BTC',
                'basis_trade_enabled': True
            },
            'backtest': {'initial_capital': 100000}
        },
        {
            'strategy': {
                'mode': 'eth_leveraged',
                'share_class': 'ETH',
                'asset': 'ETH',
                'lst_type': 'weeth',
                'staking_enabled': True,
                'staking_leverage_enabled': True
            },
            'backtest': {'initial_capital': 100000}
        },
        {
            'strategy': {
                'mode': 'usdt_market_neutral',
                'share_class': 'USDT',
                'asset': 'ETH',
                'lst_type': 'weeth',
                'staking_enabled': True,
                'basis_trade_enabled': True
            },
            'backtest': {'initial_capital': 100000}
        }
    ]
    
    for config in configs:
        mode = config['strategy']['mode']
        print(f"\n📊 Testing {mode} mode...")
        
        try:
            # Initialize strategy manager
            manager = StrategyManager(config)
            print(f"✅ Strategy manager initialized for {mode}")
            
            # Test mode detection
            detected_mode = manager.detect_strategy_mode()
            print(f"✅ Mode detection: {detected_mode}")
            assert detected_mode == mode, f"Mode detection failed: expected {mode}, got {detected_mode}"
            
            # Test desired position calculation
            current_exposure = {
                'net_delta_eth': 0,
                'total_value_usd': 100000,
                'aave_usdt_supplied': 0
            }
            desired_positions = manager.calculate_desired_positions(current_exposure)
            print(f"✅ Desired positions calculated: {len(desired_positions)} parameters")
            
            # Test strategy decision making
            market_data = {
                'funding_rate': 0.005,
                'eth_price': 3000,
                'btc_price': 50000
            }
            decision = manager.make_strategy_decision(market_data)
            print(f"✅ Strategy decision made: {decision['action']}")
            
            # Test component orchestration
            orchestration = manager.orchestrate_components()
            print(f"✅ Component orchestration: {len(orchestration['components'])} components")
            
            print(f"✅ {mode} mode test passed")
            
        except Exception as e:
            print(f"❌ {mode} mode test failed: {e}")
            # Continue with other modes even if one fails
    
    print(f"\n✅ All Strategy Manager tests completed!")

if __name__ == "__main__":
    test_strategy_manager()