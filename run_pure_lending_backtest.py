#!/usr/bin/env python3
"""
Run a pure lending backtest using the EventDrivenStrategyEngine.

This script demonstrates how to run a backtest for the pure lending strategy.
"""

import sys
import os
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import json

# Add backend to path
sys.path.append('backend/src')

from basis_strategy_v1.core.event_engine.event_driven_strategy_engine import EventDrivenStrategyEngine


async def run_pure_lending_backtest():
    """Run a pure lending backtest."""
    print("🚀 Starting Pure Lending Backtest")
    print("=" * 50)
    
    # Configuration for pure lending backtest
    config = {
        'mode': 'pure_lending',
        'share_class': 'USDT',
        'initial_capital': 100000,  # $100,000 initial capital
        'execution_mode': 'backtest',
        'data': {
            'data_dir': './data/'  # Point to project data directory
        },
        # Strategy parameters
        'strategy': {
            'target_ltv': 0.65,
            'rebalance_threshold_pct': 0.05,
            'lst_type': 'weeth',
            'max_stake_spread_move': 0.02215
        },
        # Risk parameters
        'risk': {
            'aave_ltv_warning': 0.70,
            'aave_ltv_critical': 0.80,
            'margin_warning_pct': 0.20,
            'margin_critical_pct': 0.10
        },
        # Backtest parameters
        'backtest': {
            'initial_capital': 100000
        }
    }
    
    print(f"📊 Configuration:")
    print(f"   Mode: {config['mode']}")
    print(f"   Share Class: {config['share_class']}")
    print(f"   Initial Capital: ${config['initial_capital']:,}")
    print(f"   Data Directory: {config['data']['data_dir']}")
    
    try:
        # Initialize the strategy engine
        print(f"\n🔧 Initializing EventDrivenStrategyEngine...")
        engine = EventDrivenStrategyEngine(config)
        print(f"✅ Engine initialized successfully")
        
        # Get engine status
        status = await engine.get_status()
        print(f"\n📈 Engine Status:")
        print(f"   Mode: {status['mode']}")
        print(f"   Share Class: {status['share_class']}")
        print(f"   Execution Mode: {status['execution_mode']}")
        print(f"   Is Running: {status['is_running']}")
        
        # Run backtest for a short period (1 week)
        start_date = "2024-06-01"
        end_date = "2024-06-08"  # 1 week backtest
        
        print(f"\n🏃 Running backtest from {start_date} to {end_date}...")
        print("   This may take a few minutes...")
        
        # Run the backtest
        results = await engine.run_backtest(start_date, end_date)
        
        print(f"\n🎉 Backtest completed successfully!")
        print("=" * 50)
        
        # Display results
        print(f"📊 Backtest Results:")
        print(f"   Mode: {results.get('mode', 'N/A')}")
        print(f"   Share Class: {results.get('share_class', 'N/A')}")
        print(f"   Start Date: {results.get('start_date', 'N/A')}")
        print(f"   End Date: {results.get('end_date', 'N/A')}")
        
        # Performance metrics
        if 'performance' in results:
            perf = results['performance']
            print(f"\n💰 Performance Metrics:")
            print(f"   Initial Capital: ${perf.get('initial_capital', 0):,.2f}")
            print(f"   Final Value: ${perf.get('final_value', 0):,.2f}")
            print(f"   Total Return: ${perf.get('total_return', 0):,.2f}")
            print(f"   Total Return %: {perf.get('total_return_pct', 0):.2f}%")
            
            # Calculate annualized return
            days = 7  # 1 week
            annualized_return = (perf.get('total_return_pct', 0) / 100) * (365 / days) * 100
            print(f"   Annualized Return: {annualized_return:.2f}%")
        
        # Event summary
        events = results.get('events', [])
        print(f"\n📝 Event Summary:")
        print(f"   Total Events: {len(events)}")
        
        # Count event types
        event_types = {}
        for event in events:
            event_type = event.get('event_type', 'UNKNOWN')
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        print(f"   Event Types:")
        for event_type, count in event_types.items():
            print(f"     {event_type}: {count}")
        
        # P&L history
        pnl_history = results.get('pnl_history', [])
        print(f"\n📈 P&L History:")
        print(f"   Data Points: {len(pnl_history)}")
        
        if pnl_history:
            first_pnl = pnl_history[0].get('pnl', {})
            last_pnl = pnl_history[-1].get('pnl', {})
            
            print(f"   First P&L: ${first_pnl.get('balance_based', {}).get('pnl_cumulative', 0):,.2f}")
            print(f"   Last P&L: ${last_pnl.get('balance_based', {}).get('pnl_cumulative', 0):,.2f}")
        
        # Save results to file
        results_file = f"pure_lending_backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert pandas Timestamps to strings for JSON serialization
        def convert_timestamps(obj):
            if isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_timestamps(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_timestamps(item) for item in obj]
            else:
                return obj
        
        serializable_results = convert_timestamps(results)
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        raise


async def main():
    """Main function."""
    try:
        results = await run_pure_lending_backtest()
        print(f"\n🎉 Pure lending backtest completed successfully!")
        return results
    except Exception as e:
        print(f"\n💥 Backtest failed: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(main())
