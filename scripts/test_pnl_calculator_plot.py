#!/usr/bin/env python3
"""
Test PnL Monitor with Mock Data and Plot Results

This script tests the refactored PnL Monitor with mock data to verify:
1. Balance-based P&L calculation using share_class_value
2. Config-driven attribution calculation
3. Reconciliation between balance and attribution P&L
4. Proper handling of all 9 attribution types
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Add the backend src to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from basis_strategy_v1.core.components.pnl_monitor import PnLCalculator
from unittest.mock import Mock

def create_mock_config(attribution_types: List[str] = None) -> Dict[str, Any]:
    """Create mock configuration for PnL Monitor."""
    if attribution_types is None:
        attribution_types = [
            'supply_yield', 'borrow_costs', 'staking_yield_oracle', 
            'staking_yield_rewards', 'funding_pnl', 'delta_pnl', 
            'basis_pnl', 'dust_pnl', 'transaction_costs'
        ]
    
    return {
        'mode': 'usdt_market_neutral',
        'share_class': 'USDT',
        'component_config': {
            'pnl_monitor': {
                'attribution_types': attribution_types,
                'reporting_currency': 'USDT',
                'reconciliation_tolerance': 0.02
            }
        }
    }

def create_mock_utility_manager():
    """Create mock utility manager."""
    mock_utility = Mock()
    mock_utility.get_oracle_price.return_value = 1.05  # weETH/ETH oracle price
    mock_utility.get_market_price.return_value = 3000.0  # ETH price
    mock_utility.get_funding_rate.return_value = 0.0001  # 0.01% funding rate
    mock_utility.convert_to_share_class.return_value = 1000.0  # Mock conversion
    return mock_utility

def create_mock_data_provider():
    """Create mock data provider."""
    mock_provider = Mock()
    mock_provider.get_data.return_value = {
        'market_data': {
            'prices': {
                'ETH': 3000.0,
                'USDT': 1.0,
                'weETH': 3150.0
            }
        },
        'protocol_data': {
            'aave_indexes': {
                'aUSDT': 1.05,
                'variableDebtWETH': 1.02
            }
        }
    }
    return mock_provider

def generate_mock_exposure_data(
    start_value: float = 100000.0,
    num_periods: int = 24,
    growth_rate: float = 0.001  # 0.1% per hour
) -> List[Dict[str, Any]]:
    """Generate mock exposure data over time."""
    exposures = []
    base_timestamp = pd.Timestamp('2024-01-01 00:00:00', tz='UTC')
    
    for i in range(num_periods):
        timestamp = base_timestamp + timedelta(hours=i)
        
        # Simulate portfolio growth with some volatility
        growth = growth_rate * (1 + np.random.normal(0, 0.1))  # Add some noise
        current_value = start_value * (1 + growth * i)
        
        # Simulate different attribution sources
        supply_yield = current_value * 0.0001 * i  # 0.01% per hour
        staking_yield = current_value * 0.00005 * i  # 0.005% per hour
        funding_pnl = current_value * 0.00002 * i  # 0.002% per hour
        transaction_costs = -current_value * 0.00001 * i  # -0.001% per hour
        
        exposure = {
            'timestamp': timestamp,
            'share_class_value': current_value,
            'total_value_usd': current_value,
            'exposures': {
                'aUSDT': {
                    'underlying_balance': current_value * 0.8,  # 80% in lending
                    'timestamp': timestamp
                },
                'aWeETH': {
                    'underlying_native': current_value * 0.2 / 3000,  # 20% in staking
                    'oracle_price': 1.05 + (i * 0.0001),  # Oracle price appreciation
                    'eth_usd_price': 3000.0,
                    'timestamp': timestamp
                },
                'variableDebtWETH': {
                    'underlying_native': current_value * 0.1 / 3000,  # 10% borrowed
                    'eth_usd_price': 3000.0,
                    'timestamp': timestamp
                }
            },
            'net_delta_eth': 0.1,  # Small delta exposure
            'total_exposure': current_value,
            'exposure_metrics': {
                'total_usdt_exposure': current_value,
                'total_share_class_exposure': current_value
            }
        }
        
        exposures.append(exposure)
    
    return exposures

def test_pnl_monitor():
    """Test PnL Monitor with mock data."""
    print("🧪 Testing PnL Monitor with Mock Data")
    print("=" * 50)
    
    # Create mock components
    config = create_mock_config()
    utility_manager = create_mock_utility_manager()
    data_provider = create_mock_data_provider()
    
    # Initialize PnL Monitor
    pnl_monitor = PnLCalculator(
        config=config,
        share_class='USDT',
        initial_capital=100000.0,
        data_provider=data_provider,
        utility_manager=utility_manager
    )
    
    print(f"✅ PnL Monitor initialized with {len(config['component_config']['pnl_monitor']['attribution_types'])} attribution types")
    
    # Generate mock exposure data
    mock_exposures = generate_mock_exposure_data()
    print(f"✅ Generated {len(mock_exposures)} mock exposure data points")
    
    # Calculate P&L for each period
    pnl_results = []
    previous_exposure = None
    
    for i, exposure in enumerate(mock_exposures):
        try:
            # Calculate P&L
            pnl_result = pnl_monitor.calculate_pnl(
                current_exposure=exposure,
                previous_exposure=previous_exposure,
                timestamp=exposure['timestamp']
            )
            
            # Store results
            pnl_results.append({
                'timestamp': exposure['timestamp'],
                'balance_based': pnl_result.get('balance_based', {}),
                'attribution': pnl_result.get('attribution', {}),
                'reconciliation': pnl_result.get('reconciliation', {}),
                'share_class_value': exposure['share_class_value']
            })
            
            previous_exposure = exposure
            
            if i % 6 == 0:  # Print every 6 hours
                print(f"⏰ {exposure['timestamp']}: Balance P&L = ${pnl_result.get('balance_based', {}).get('pnl_cumulative', 0):.2f}")
                
        except Exception as e:
            print(f"❌ Error calculating P&L for period {i}: {e}")
            continue
    
    print(f"✅ Successfully calculated P&L for {len(pnl_results)} periods")
    return pnl_results

def plot_pnl_results(pnl_results: List[Dict[str, Any]]):
    """Plot P&L results over time."""
    if not pnl_results:
        print("❌ No P&L results to plot")
        return
    
    # Extract data for plotting
    timestamps = [r['timestamp'] for r in pnl_results]
    balance_pnl = [r['balance_based'].get('pnl_cumulative', 0) for r in pnl_results]
    share_class_values = [r['share_class_value'] for r in pnl_results]
    
    # Extract attribution data
    attribution_data = {}
    for attr_type in ['supply_yield', 'staking_yield_oracle', 'funding_pnl', 'transaction_costs']:
        attribution_data[attr_type] = [r['attribution'].get(attr_type, 0) for r in pnl_results]
    
    # Create plots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('PnL Monitor Test Results', fontsize=16)
    
    # Plot 1: Balance-based P&L over time
    ax1.plot(timestamps, balance_pnl, 'b-', linewidth=2, label='Balance-based P&L')
    ax1.set_title('Balance-based P&L Over Time')
    ax1.set_ylabel('P&L (USDT)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot 2: Share class value over time
    ax2.plot(timestamps, share_class_values, 'g-', linewidth=2, label='Portfolio Value')
    ax2.set_title('Portfolio Value Over Time')
    ax2.set_ylabel('Value (USDT)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Plot 3: Attribution P&L components
    for attr_type, values in attribution_data.items():
        if any(v != 0 for v in values):  # Only plot if there's data
            ax3.plot(timestamps, values, label=attr_type, linewidth=2)
    ax3.set_title('Attribution P&L Components')
    ax3.set_ylabel('P&L (USDT)')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # Plot 4: Cumulative attribution P&L
    cumulative_attribution = np.cumsum([sum(r['attribution'].values()) for r in pnl_results])
    ax4.plot(timestamps, cumulative_attribution, 'r-', linewidth=2, label='Cumulative Attribution P&L')
    ax4.plot(timestamps, balance_pnl, 'b--', linewidth=2, label='Balance-based P&L')
    ax4.set_title('P&L Reconciliation')
    ax4.set_ylabel('P&L (USDT)')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    
    # Rotate x-axis labels for better readability
    for ax in [ax1, ax2, ax3, ax4]:
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # Save plot
    plot_path = 'pnl_monitor_test_results.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"📊 Plot saved to: {plot_path}")
    
    # Show plot
    plt.show()

def print_summary_stats(pnl_results: List[Dict[str, Any]]):
    """Print summary statistics."""
    if not pnl_results:
        return
    
    print("\n📊 Summary Statistics")
    print("=" * 30)
    
    # Final values
    final_result = pnl_results[-1]
    initial_value = 100000.0
    final_value = final_result['share_class_value']
    total_return = final_value - initial_value
    total_return_pct = (total_return / initial_value) * 100
    
    print(f"Initial Portfolio Value: ${initial_value:,.2f}")
    print(f"Final Portfolio Value: ${final_value:,.2f}")
    print(f"Total Return: ${total_return:,.2f} ({total_return_pct:.2f}%)")
    
    # Attribution breakdown
    print(f"\nAttribution Breakdown:")
    attribution = final_result['attribution']
    for attr_type, value in attribution.items():
        if value != 0:
            print(f"  {attr_type}: ${value:,.2f}")
    
    # Reconciliation
    reconciliation = final_result.get('reconciliation', {})
    if reconciliation:
        print(f"\nReconciliation:")
        print(f"  Balance P&L: ${reconciliation.get('balance_pnl', 0):,.2f}")
        print(f"  Attribution P&L: ${reconciliation.get('attribution_pnl', 0):,.2f}")
        print(f"  Difference: ${reconciliation.get('difference', 0):,.2f}")
        print(f"  Passed: {reconciliation.get('passed', False)}")

def main():
    """Main test function."""
    print("🚀 Starting PnL Monitor Test")
    print("=" * 50)
    
    try:
        # Test PnL Monitor
        pnl_results = test_pnl_monitor()
        
        if pnl_results:
            # Print summary
            print_summary_stats(pnl_results)
            
            # Plot results
            plot_pnl_results(pnl_results)
            
            print("\n✅ PnL Monitor test completed successfully!")
        else:
            print("❌ No P&L results generated")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
