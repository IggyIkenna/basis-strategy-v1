#!/usr/bin/env python3
"""
Enhanced PnL Monitor Test with All System Tokens and Component Attribution

This script tests the refactored PnL Monitor with comprehensive mock data including:
1. All tokens in our system (USDT, ETH, BTC, weETH, aUSDT, aWeETH, EIGEN, ETHFI, KING, etc.)
2. Detailed attribution per component (supply yield, staking, funding, etc.)
3. Multi-venue exposure (wallet, AAVE, CEX spot, CEX derivatives)
4. Comprehensive P&L breakdown and visualization
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Add the backend src to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from basis_strategy_v1.core.components.pnl_monitor import PnLMonitor
from unittest.mock import Mock

def create_enhanced_mock_config() -> Dict[str, Any]:
    """Create comprehensive mock configuration for PnL Monitor."""
    return {
        'mode': 'usdt_market_neutral',
        'share_class': 'USDT',
        'component_config': {
            'pnl_monitor': {
                'attribution_types': [
                    'supply_yield', 'borrow_costs', 'staking_yield_oracle', 
                    'staking_yield_rewards', 'funding_pnl', 'delta_pnl', 
                    'basis_pnl', 'dust_pnl', 'transaction_costs'
                ],
                'reporting_currency': 'USDT',
                'reconciliation_tolerance': 0.02
            }
        }
    }

def create_enhanced_mock_utility_manager():
    """Create enhanced mock utility manager with all token prices."""
    mock_utility = Mock()
    
    # Mock price data for all tokens
    mock_utility.get_oracle_price.side_effect = lambda token, timestamp: {
        'weETH': 1.05 + (timestamp.hour * 0.0001),  # Oracle price appreciation
        'aUSDT': 1.0,
        'aWeETH': 1.05 + (timestamp.hour * 0.0001),
    }.get(token, 1.0)
    
    mock_utility.get_market_price.side_effect = lambda token, timestamp: {
        'ETH': 3000.0 + (timestamp.hour * 10),  # ETH price appreciation
        'BTC': 50000.0 + (timestamp.hour * 50),  # BTC price appreciation
        'USDT': 1.0,
        'weETH': 3150.0 + (timestamp.hour * 10.5),  # weETH price appreciation
        'EIGEN': 5.0 + (timestamp.hour * 0.01),  # EIGEN price appreciation
        'ETHFI': 2.0 + (timestamp.hour * 0.005),  # ETHFI price appreciation
        'KING': 0.1 + (timestamp.hour * 0.0001),  # KING price appreciation
    }.get(token, 1.0)
    
    mock_utility.get_funding_rate.side_effect = lambda token, timestamp: {
        'BTC-PERP': 0.0001 + (timestamp.hour * 0.00001),  # Funding rate changes
        'ETH-PERP': 0.00008 + (timestamp.hour * 0.000005),
    }.get(token, 0.0001)
    
    # Mock conversion to share class
    def mock_convert_to_share_class(amount, token, share_class, timestamp):
        if share_class == 'USDT':
            if token == 'USDT':
                return amount
            elif token in ['ETH', 'weETH']:
                return amount * mock_utility.get_market_price(token, timestamp)
            elif token in ['EIGEN', 'ETHFI', 'KING']:
                return amount * mock_utility.get_market_price(token, timestamp)
            else:
                return amount * 1.0
        return amount
    
    mock_utility.convert_to_share_class.side_effect = mock_convert_to_share_class
    
    return mock_utility

def create_enhanced_mock_data_provider():
    """Create enhanced mock data provider with all token data."""
    mock_provider = Mock()
    
    def mock_get_data(timestamp):
        return {
            'market_data': {
                'prices': {
                    'ETH': 3000.0 + (timestamp.hour * 10),
                    'BTC': 50000.0 + (timestamp.hour * 50),
                    'USDT': 1.0,
                    'weETH': 3150.0 + (timestamp.hour * 10.5),
                    'EIGEN': 5.0 + (timestamp.hour * 0.01),
                    'ETHFI': 2.0 + (timestamp.hour * 0.005),
                    'KING': 0.1 + (timestamp.hour * 0.0001),
                }
            },
            'protocol_data': {
                'aave_indexes': {
                    'aUSDT': 1.0 + (timestamp.hour * 0.0001),  # Lending yield
                    'aWeETH': 1.0 + (timestamp.hour * 0.00005),  # Lending yield
                    'variableDebtWETH': 1.0 + (timestamp.hour * 0.00008),  # Borrow cost
                }
            },
            'funding_rates': {
                'BTC-PERP': 0.0001 + (timestamp.hour * 0.00001),
                'ETH-PERP': 0.00008 + (timestamp.hour * 0.000005),
            }
        }
    
    mock_provider.get_data.side_effect = mock_get_data
    return mock_provider

def generate_comprehensive_exposure_data(
    start_value: float = 100000.0,
    num_periods: int = 48,  # 48 hours = 2 days
    base_growth_rate: float = 0.0005  # 0.05% per hour
) -> List[Dict[str, Any]]:
    """Generate comprehensive mock exposure data with all tokens."""
    exposures = []
    base_timestamp = pd.Timestamp('2024-01-01 00:00:00', tz='UTC')
    
    for i in range(num_periods):
        timestamp = base_timestamp + timedelta(hours=i)
        
        # Simulate portfolio growth with volatility
        growth = base_growth_rate * (1 + np.random.normal(0, 0.2))
        current_value = start_value * (1 + growth * i)
        
        # Allocate across different venues and tokens
        wallet_allocation = 0.1  # 10% in wallet
        aave_allocation = 0.6   # 60% in AAVE
        cex_spot_allocation = 0.2  # 20% in CEX spot
        cex_derivatives_allocation = 0.1  # 10% in CEX derivatives
        
        exposure = {
            'timestamp': timestamp,
            'share_class_value': current_value,
            'total_value_usd': current_value,
            'exposures': {
                # Wallet positions (10% of portfolio)
                'USDT': {
                    'wallet_balance': current_value * wallet_allocation * 0.5,  # 5% USDT
                    'timestamp': timestamp
                },
                'ETH': {
                    'wallet_balance': current_value * wallet_allocation * 0.3 / 3000,  # 3% ETH
                    'timestamp': timestamp
                },
                'weETH': {
                    'wallet_balance': current_value * wallet_allocation * 0.2 / 3150,  # 2% weETH
                    'timestamp': timestamp
                },
                
                # AAVE positions (60% of portfolio)
                'aUSDT': {
                    'underlying_balance': current_value * aave_allocation * 0.7,  # 42% aUSDT
                    'timestamp': timestamp
                },
                'aWeETH': {
                    'underlying_native': current_value * aave_allocation * 0.3 / 3150,  # 18% aWeETH
                    'oracle_price': 1.05 + (i * 0.0001),
                    'eth_usd_price': 3000.0 + (i * 10),
                    'timestamp': timestamp
                },
                'variableDebtWETH': {
                    'underlying_native': current_value * aave_allocation * 0.1 / 3000,  # 6% borrowed
                    'eth_usd_price': 3000.0 + (i * 10),
                    'timestamp': timestamp
                },
                
                # CEX Spot positions (20% of portfolio)
                'BTC': {
                    'cex_spot_balance': current_value * cex_spot_allocation * 0.8 / 50000,  # 16% BTC
                    'timestamp': timestamp
                },
                'ETH': {
                    'cex_spot_balance': current_value * cex_spot_allocation * 0.2 / 3000,  # 4% ETH
                    'timestamp': timestamp
                },
                
                # CEX Derivatives positions (10% of portfolio)
                'BTC-PERP': {
                    'size': -current_value * cex_derivatives_allocation * 0.6 / 50000,  # -6% BTC short
                    'mark_price': 50000.0 + (i * 50),
                    'timestamp': timestamp
                },
                'ETH-PERP': {
                    'size': -current_value * cex_derivatives_allocation * 0.4 / 3000,  # -4% ETH short
                    'mark_price': 3000.0 + (i * 10),
                    'timestamp': timestamp
                },
                
                # Dust tokens (rewards)
                'EIGEN': {
                    'wallet_balance': 100 + (i * 0.5),  # Accumulating EIGEN rewards
                    'timestamp': timestamp
                },
                'ETHFI': {
                    'wallet_balance': 50 + (i * 0.2),  # Accumulating ETHFI rewards
                    'timestamp': timestamp
                },
                'KING': {
                    'wallet_balance': 1000 + (i * 2),  # Accumulating KING rewards
                    'timestamp': timestamp
                }
            },
            'net_delta_eth': 0.05 + (i * 0.001),  # Small delta exposure
            'total_exposure': current_value,
            'exposure_metrics': {
                'total_usdt_exposure': current_value,
                'total_share_class_exposure': current_value
            },
            'exposure_by_venue': {
                'wallet': {
                    'USDT': current_value * wallet_allocation * 0.5,
                    'ETH': current_value * wallet_allocation * 0.3,
                    'weETH': current_value * wallet_allocation * 0.2,
                    'EIGEN': (100 + (i * 0.5)) * (5.0 + (i * 0.01)),
                    'ETHFI': (50 + (i * 0.2)) * (2.0 + (i * 0.005)),
                    'KING': (1000 + (i * 2)) * (0.1 + (i * 0.0001))
                },
                'aave': {
                    'aUSDT': current_value * aave_allocation * 0.7,
                    'aWeETH': current_value * aave_allocation * 0.3,
                    'variableDebtWETH': -current_value * aave_allocation * 0.1
                },
                'cex_spot': {
                    'BTC': current_value * cex_spot_allocation * 0.8,
                    'ETH': current_value * cex_spot_allocation * 0.2
                },
                'cex_derivatives': {
                    'BTC-PERP': -current_value * cex_derivatives_allocation * 0.6,
                    'ETH-PERP': -current_value * cex_derivatives_allocation * 0.4
                }
            }
        }
        
        exposures.append(exposure)
    
    return exposures

def test_enhanced_pnl_monitor():
    """Test enhanced PnL Monitor with comprehensive mock data."""
    print("🧪 Testing Enhanced PnL Monitor with All System Tokens")
    print("=" * 60)
    
    # Create enhanced mock components
    config = create_enhanced_mock_config()
    utility_manager = create_enhanced_mock_utility_manager()
    data_provider = create_enhanced_mock_data_provider()
    
    # Create mock exposure monitor
    mock_exposure_monitor = Mock()
    mock_exposure_monitor.current_exposure = None
    
    def get_current_exposure():
        return mock_exposure_monitor.current_exposure
    
    mock_exposure_monitor.get_current_exposure = get_current_exposure
    
    # Initialize PnL Monitor
    pnl_monitor = PnLMonitor(
        config=config,
        share_class='USDT',
        initial_capital=100000.0,
        data_provider=data_provider,
        utility_manager=utility_manager,
        exposure_monitor=mock_exposure_monitor
    )
    
    print(f"✅ PnL Monitor initialized with {len(config['component_config']['pnl_monitor']['attribution_types'])} attribution types")
    
    # Generate comprehensive mock exposure data
    mock_exposures = generate_comprehensive_exposure_data()
    print(f"✅ Generated {len(mock_exposures)} comprehensive mock exposure data points")
    
    # Calculate P&L for each period
    pnl_results = []
    previous_exposure = None
    
    for i, exposure in enumerate(mock_exposures):
        try:
            # Update the exposure monitor with current exposure data
            pnl_monitor.exposure_monitor.current_exposure = exposure
            pnl_monitor.previous_exposure = previous_exposure
            
            # Update PnL monitor state (triggers calculation)
            pnl_monitor.update_state(
                timestamp=exposure['timestamp'],
                trigger_source='test'
            )
            
            # Get the calculated P&L result
            pnl_result = pnl_monitor.get_latest_pnl()
            
            # Store results with detailed breakdown
            pnl_results.append({
                'timestamp': exposure['timestamp'],
                'balance_based': pnl_result.get('balance_based', {}),
                'attribution': pnl_result.get('attribution', {}),
                'reconciliation': pnl_result.get('reconciliation', {}),
                'share_class_value': exposure['share_class_value'],
                'exposure_by_venue': exposure.get('exposure_by_venue', {}),
                'exposures': exposure.get('exposures', {})
            })
            
            previous_exposure = exposure
            
            if i % 12 == 0:  # Print every 12 hours
                balance_pnl = pnl_result.get('balance_based', {}).get('pnl_cumulative', 0)
                print(f"⏰ {exposure['timestamp']}: Balance P&L = ${balance_pnl:,.2f}")
                
        except Exception as e:
            print(f"❌ Error calculating P&L for period {i}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"✅ Successfully calculated P&L for {len(pnl_results)} periods")
    return pnl_results

def plot_enhanced_pnl_results(pnl_results: List[Dict[str, Any]]):
    """Plot enhanced P&L results with detailed breakdowns."""
    if not pnl_results:
        print("❌ No P&L results to plot")
        return
    
    # Extract data for plotting
    timestamps = [r['timestamp'] for r in pnl_results]
    balance_pnl = [r['balance_based'].get('pnl_cumulative', 0) for r in pnl_results]
    share_class_values = [r['share_class_value'] for r in pnl_results]
    
    # Extract attribution data
    attribution_data = {}
    for attr_type in ['supply_yield', 'borrow_costs', 'staking_yield_oracle', 
                     'staking_yield_rewards', 'funding_pnl', 'delta_pnl', 
                     'basis_pnl', 'dust_pnl', 'transaction_costs']:
        attribution_data[attr_type] = [r['attribution'].get(attr_type, 0) for r in pnl_results]
    
    # Extract venue exposure data
    venue_data = {}
    for venue in ['wallet', 'aave', 'cex_spot', 'cex_derivatives']:
        venue_data[venue] = []
        for r in pnl_results:
            venue_exposure = r.get('exposure_by_venue', {}).get(venue, {})
            total_venue_value = sum(abs(v) for v in venue_exposure.values())
            venue_data[venue].append(total_venue_value)
    
    # Create comprehensive plots
    fig = plt.figure(figsize=(20, 16))
    
    # Main P&L plot
    ax1 = plt.subplot(3, 3, 1)
    ax1.plot(timestamps, balance_pnl, 'b-', linewidth=2, label='Balance-based P&L')
    ax1.set_title('Balance-based P&L Over Time')
    ax1.set_ylabel('P&L (USDT)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Portfolio value
    ax2 = plt.subplot(3, 3, 2)
    ax2.plot(timestamps, share_class_values, 'g-', linewidth=2, label='Portfolio Value')
    ax2.set_title('Portfolio Value Over Time')
    ax2.set_ylabel('Value (USDT)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Attribution components
    ax3 = plt.subplot(3, 3, 3)
    for attr_type, values in attribution_data.items():
        if any(v != 0 for v in values):
            ax3.plot(timestamps, values, label=attr_type, linewidth=2)
    ax3.set_title('Attribution P&L Components')
    ax3.set_ylabel('P&L (USDT)')
    ax3.grid(True, alpha=0.3)
    ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Venue exposure breakdown
    ax4 = plt.subplot(3, 3, 4)
    for venue, values in venue_data.items():
        ax4.plot(timestamps, values, label=venue, linewidth=2)
    ax4.set_title('Exposure by Venue')
    ax4.set_ylabel('Value (USDT)')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    
    # Cumulative attribution P&L
    ax5 = plt.subplot(3, 3, 5)
    cumulative_attribution = np.cumsum([sum(r['attribution'].values()) for r in pnl_results])
    ax5.plot(timestamps, cumulative_attribution, 'r-', linewidth=2, label='Cumulative Attribution P&L')
    ax5.plot(timestamps, balance_pnl, 'b--', linewidth=2, label='Balance-based P&L')
    ax5.set_title('P&L Reconciliation')
    ax5.set_ylabel('P&L (USDT)')
    ax5.grid(True, alpha=0.3)
    ax5.legend()
    
    # Token exposure heatmap
    ax6 = plt.subplot(3, 3, 6)
    token_exposures = {}
    for r in pnl_results:
        for token, exposure in r.get('exposures', {}).items():
            if token not in token_exposures:
                token_exposures[token] = []
            # Calculate total exposure for this token
            total_exposure = 0
            if isinstance(exposure, dict):
                for key, value in exposure.items():
                    if isinstance(value, (int, float)) and key != 'timestamp':
                        total_exposure += abs(value)
            token_exposures[token].append(total_exposure)
    
    # Create heatmap data
    heatmap_data = []
    token_names = []
    for token, values in token_exposures.items():
        if any(v > 0 for v in values):
            heatmap_data.append(values)
            token_names.append(token)
    
    if heatmap_data:
        heatmap_data = np.array(heatmap_data)
        im = ax6.imshow(heatmap_data, aspect='auto', cmap='viridis')
        ax6.set_title('Token Exposure Heatmap')
        ax6.set_xlabel('Time Period')
        ax6.set_ylabel('Token')
        ax6.set_yticks(range(len(token_names)))
        ax6.set_yticklabels(token_names)
        plt.colorbar(im, ax=ax6)
    
    # Attribution pie chart (final period)
    ax7 = plt.subplot(3, 3, 7)
    final_attribution = pnl_results[-1]['attribution']
    non_zero_attribution = {k: abs(v) for k, v in final_attribution.items() if v != 0}
    if non_zero_attribution:
        ax7.pie(non_zero_attribution.values(), labels=non_zero_attribution.keys(), autopct='%1.1f%%')
        ax7.set_title('Final Attribution Breakdown (Absolute Values)')
    
    # Venue allocation pie chart
    ax8 = plt.subplot(3, 3, 8)
    final_venue_data = pnl_results[-1].get('exposure_by_venue', {})
    venue_totals = {venue: sum(abs(v) for v in values.values()) for venue, values in final_venue_data.items()}
    if venue_totals:
        ax8.pie(venue_totals.values(), labels=venue_totals.keys(), autopct='%1.1f%%')
        ax8.set_title('Final Venue Allocation')
    
    # P&L attribution over time (stacked area)
    ax9 = plt.subplot(3, 3, 9)
    cumulative_attribution_data = {}
    for attr_type in ['supply_yield', 'staking_yield_oracle', 'funding_pnl', 'dust_pnl']:
        if any(r['attribution'].get(attr_type, 0) != 0 for r in pnl_results):
            cumulative_attribution_data[attr_type] = np.cumsum([r['attribution'].get(attr_type, 0) for r in pnl_results])
    
    if cumulative_attribution_data:
        ax9.stackplot(timestamps, *cumulative_attribution_data.values(), 
                     labels=cumulative_attribution_data.keys(), alpha=0.7)
        ax9.set_title('Cumulative Attribution P&L (Stacked)')
        ax9.set_ylabel('P&L (USDT)')
        ax9.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax9.grid(True, alpha=0.3)
    
    # Rotate x-axis labels for better readability
    for ax in [ax1, ax2, ax3, ax4, ax5, ax9]:
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # Save plot
    plot_path = 'enhanced_pnl_monitor_test_results.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"📊 Enhanced plot saved to: {plot_path}")
    
    # Show plot
    plt.show()

def print_enhanced_summary_stats(pnl_results: List[Dict[str, Any]]):
    """Print enhanced summary statistics with detailed breakdowns."""
    if not pnl_results:
        return
    
    print("\n📊 Enhanced Summary Statistics")
    print("=" * 40)
    
    # Final values
    final_result = pnl_results[-1]
    initial_value = 100000.0
    final_value = final_result['share_class_value']
    total_return = final_value - initial_value
    total_return_pct = (total_return / initial_value) * 100
    
    print(f"Initial Portfolio Value: ${initial_value:,.2f}")
    print(f"Final Portfolio Value: ${final_value:,.2f}")
    print(f"Total Return: ${total_return:,.2f} ({total_return_pct:.2f}%)")
    
    # Detailed attribution breakdown
    print(f"\n📈 Detailed Attribution Breakdown:")
    attribution = final_result['attribution']
    for attr_type, value in attribution.items():
        if value != 0:
            pct = (value / total_return) * 100 if total_return != 0 else 0
            print(f"  {attr_type:25}: ${value:8,.2f} ({pct:5.1f}%)")
    
    # Venue breakdown
    print(f"\n🏦 Venue Allocation:")
    venue_data = final_result.get('exposure_by_venue', {})
    for venue, tokens in venue_data.items():
        total_venue_value = sum(abs(v) for v in tokens.values())
        pct = (total_venue_value / final_value) * 100 if final_value != 0 else 0
        print(f"  {venue:15}: ${total_venue_value:8,.2f} ({pct:5.1f}%)")
    
    # Token breakdown
    print(f"\n🪙 Token Exposure:")
    exposures = final_result.get('exposures', {})
    token_totals = {}
    for token, exposure in exposures.items():
        if isinstance(exposure, dict):
            total_exposure = 0
            for key, value in exposure.items():
                if isinstance(value, (int, float)) and key != 'timestamp':
                    total_exposure += abs(value)
            if total_exposure > 0:
                token_totals[token] = total_exposure
    
    for token, value in sorted(token_totals.items(), key=lambda x: x[1], reverse=True):
        pct = (value / final_value) * 100 if final_value != 0 else 0
        print(f"  {token:15}: ${value:8,.2f} ({pct:5.1f}%)")
    
    # Reconciliation
    reconciliation = final_result.get('reconciliation', {})
    if reconciliation:
        print(f"\n🔄 Reconciliation:")
        print(f"  Balance P&L: ${reconciliation.get('balance_pnl', 0):,.2f}")
        print(f"  Attribution P&L: ${reconciliation.get('attribution_pnl', 0):,.2f}")
        print(f"  Difference: ${reconciliation.get('difference', 0):,.2f}")
        print(f"  Passed: {reconciliation.get('passed', False)}")
    
    # Hourly attribution rates
    print(f"\n⏱️  Hourly Attribution Rates:")
    for attr_type, values in attribution.items():
        if value != 0:
            hourly_rate = value / len(pnl_results)  # Average per hour
            print(f"  {attr_type:25}: ${hourly_rate:8,.2f}/hour")

def main():
    """Main enhanced test function."""
    print("🚀 Starting Enhanced PnL Monitor Test")
    print("=" * 60)
    
    try:
        # Test enhanced PnL Monitor
        pnl_results = test_enhanced_pnl_monitor()
        
        if pnl_results:
            # Print enhanced summary
            print_enhanced_summary_stats(pnl_results)
            
            # Plot enhanced results
            plot_enhanced_pnl_results(pnl_results)
            
            print("\n✅ Enhanced PnL Monitor test completed successfully!")
        else:
            print("❌ No P&L results generated")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
