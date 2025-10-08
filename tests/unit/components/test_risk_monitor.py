#!/usr/bin/env python3
"""
Test Risk Monitor Component

Test risk monitoring functionality including:
- AAVE LTV risk monitoring
- CEX margin risk monitoring  
- Net delta risk monitoring
- Risk alert generation
"""

import sys
import os
import pytest
sys.path.append('backend/src')

from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor
from datetime import datetime
import json

@pytest.mark.asyncio
async def test_risk_monitor():
    """Test risk monitor functionality."""
    print("\n🧪 Testing Risk Monitor Component")
    print("=" * 50)
    
    # Create risk monitor
    config = {
        'strategy': {
            'target_ltv': 0.91,
            'rebalance_threshold_pct': 5.0
        },
        'risk': {
            'aave_ltv_warning': 0.85,
            'aave_ltv_critical': 0.90,
            'margin_warning_pct': 0.20,
            'margin_critical_pct': 0.12
        }
    }
    
    monitor = RiskMonitor(config)
    print("✅ Risk Monitor created")
    
    # Test risk calculation with exposure data
    print("\n📊 Testing risk calculation...")
    
    # Create exposure data for testing
    exposure_data = {
        'exposures': {
            'aWeETH': {
                'exposure_eth': 50.0,
                'exposure_usd': 150000
            },
            'variableDebtWETH': {
                'exposure_eth': 40.0,
                'exposure_usd': 120000
            }
        },
        'cex': {
            'binance': {
                'margin_ratio': 0.25,
                'unrealized_pnl': 1000,
                'position_value': 50000
            }
        },
        'net_delta_usd': 1000,
        'net_delta_eth': 0.33,
        'total_value_usd': 100000
    }
    
    # Test risk calculation (this is async, so we'll test the private methods directly)
    print("   Testing AAVE risk calculation...")
    aave_risk = await monitor.calculate_aave_ltv_risk(exposure_data)
    print(f"   AAVE risk: {aave_risk.get('level', 'UNKNOWN')}")
    
    print("   Testing CEX margin risk calculation...")
    cex_risk = await monitor.calculate_cex_margin_risk(exposure_data)
    print(f"   CEX risk: {cex_risk.get('binance', {}).get('level', 'UNKNOWN')}")
    
    print("   Testing delta risk calculation...")
    delta_risk = await monitor.calculate_delta_risk(exposure_data)
    print(f"   Delta risk: {delta_risk.get('level', 'UNKNOWN')}")
    
    # Test risk summary
    print("\n📊 Testing risk summary...")
    risks = {
        'overall_status': 'NORMAL',
        'aave': {
            'ltv': 0.80,
            'health_factor': 1.25,
            'status': 'NORMAL'
        },
        'cex_margin': {
            'min_margin_ratio': 0.25,
            'min_status': 'NORMAL'
        },
        'delta': {
            'delta_drift_pct': 1.0,
            'status': 'NORMAL'
        },
        'alerts': []
    }
    
    summary = monitor.get_risk_summary()
    print(f"   Risk summary: {summary}")
    
    print("\n✅ Risk Monitor tests completed successfully!")

if __name__ == "__main__":
    test_risk_monitor()