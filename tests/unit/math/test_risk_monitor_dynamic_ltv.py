#!/usr/bin/env python3
"""
Test RiskMonitor dynamic LTV target calculation.
"""

import pytest
import asyncio
import sys
import os
from decimal import Decimal
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor
from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider


class TestRiskMonitorDynamicLTV:
    """Test RiskMonitor dynamic LTV target calculation."""
    
    def test_dynamic_ltv_target_calculation(self):
        """Test dynamic LTV target calculation with AAVE risk parameters."""
        config = {
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'weeth',
                'max_stake_spread_move': 0.02215  # 2.215%
            },
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            }
        }
        
        # Create data provider with AAVE risk parameters
        data_provider = DataProvider.__new__(DataProvider)
        data_provider.data_dir = Path('/workspace/data')
        data_provider.data = {}
        data_provider._load_aave_risk_parameters()
        
        # Create risk monitor with data provider
        risk_monitor = RiskMonitor(config, data_provider)
        
        # Test dynamic LTV target calculation
        dynamic_ltv = risk_monitor.calculate_dynamic_ltv_target('weeth')
        
        # Expected: 93% (max_ltv) - 2.215% (spread_move) - 2% (safety_buffer) = 88.785%
        expected_ltv = Decimal("0.88785")
        assert abs(dynamic_ltv - expected_ltv) < Decimal("0.001")
        
        print(f"✅ Dynamic LTV target calculation: {dynamic_ltv:.2%}")
    
    def test_dynamic_ltv_target_with_wsteth(self):
        """Test dynamic LTV target calculation for wstETH."""
        config = {
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'wsteth',
                'max_stake_spread_move': 0.02  # 2%
            },
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            }
        }
        
        # Create data provider with AAVE risk parameters
        data_provider = DataProvider.__new__(DataProvider)
        data_provider.data_dir = Path('/workspace/data')
        data_provider.data = {}
        data_provider._load_aave_risk_parameters()
        
        # Create risk monitor with data provider
        risk_monitor = RiskMonitor(config, data_provider)
        
        # Test dynamic LTV target calculation for wstETH
        dynamic_ltv = risk_monitor.calculate_dynamic_ltv_target('wsteth')
        
        # Expected: 93% (max_ltv) - 2% (spread_move) - 2% (safety_buffer) = 89%
        expected_ltv = Decimal("0.89")
        assert abs(dynamic_ltv - expected_ltv) < Decimal("0.001")
        
        print(f"✅ Dynamic LTV target for wstETH: {dynamic_ltv:.2%}")
    
    def test_dynamic_ltv_target_fallback(self):
        """Test dynamic LTV target fallback when no data provider."""
        config = {
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'weeth',
                'max_stake_spread_move': 0.02215
            },
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            }
        }
        
        # Create risk monitor without data provider
        risk_monitor = RiskMonitor(config, None)
        
        # Test fallback to static target
        dynamic_ltv = risk_monitor.calculate_dynamic_ltv_target('weeth')
        
        # Should fallback to static target_ltv
        assert dynamic_ltv == Decimal("0.91")
        
        print(f"✅ Dynamic LTV target fallback: {dynamic_ltv:.2%}")
    
    def test_dynamic_ltv_target_minimum(self):
        """Test that dynamic LTV target has a minimum value."""
        config = {
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'weeth',
                'max_stake_spread_move': 0.5  # 50% - very high
            },
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            }
        }
        
        # Create data provider with AAVE risk parameters
        data_provider = DataProvider.__new__(DataProvider)
        data_provider.data_dir = Path('/workspace/data')
        data_provider.data = {}
        data_provider._load_aave_risk_parameters()
        
        # Create risk monitor with data provider
        risk_monitor = RiskMonitor(config, data_provider)
        
        # Test with very high max_stake_spread_move
        dynamic_ltv = risk_monitor.calculate_dynamic_ltv_target('weeth')
        
        # Should be clamped to minimum 10%
        assert dynamic_ltv >= Decimal("0.1")
        
        print(f"✅ Dynamic LTV target minimum: {dynamic_ltv:.2%}")
    
    @pytest.mark.asyncio
    async def test_aave_ltv_risk_with_dynamic_target(self):
        """Test AAVE LTV risk calculation using dynamic target."""
        config = {
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'weeth',
                'max_stake_spread_move': 0.02215
            },
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            }
        }
        
        # Create data provider with AAVE risk parameters
        data_provider = DataProvider.__new__(DataProvider)
        data_provider.data_dir = Path('/workspace/data')
        data_provider.data = {}
        data_provider._load_aave_risk_parameters()
        
        # Create risk monitor with data provider
        risk_monitor = RiskMonitor(config, data_provider)
        
        # Test with AAVE positions
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 85000,
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        result = await risk_monitor.calculate_aave_ltv_risk(exposure_data)
        
        # Verify result includes dynamic LTV target
        assert 'dynamic_ltv_target' in result
        assert 'liquidation_threshold' in result
        assert 'health_factor' in result
        
        # Verify dynamic target is calculated correctly
        dynamic_target = result['dynamic_ltv_target']
        expected_target = 0.88785  # 88.785%
        assert abs(dynamic_target - expected_target) < 0.001
        
        # Verify liquidation threshold from AAVE risk params
        liquidation_threshold = result['liquidation_threshold']
        assert liquidation_threshold == 0.95  # 95% from AAVE risk params
        
        print(f"✅ AAVE LTV risk with dynamic target: {result['level']}")
        print(f"   Current LTV: {result['value']:.2%}")
        print(f"   Dynamic Target: {result['dynamic_ltv_target']:.2%}")
        print(f"   Health Factor: {result['health_factor']:.2f}")
        print(f"   Liquidation Threshold: {result['liquidation_threshold']:.2%}")
    
    @pytest.mark.asyncio
    async def test_dynamic_target_risk_levels(self):
        """Test that dynamic target affects risk level determination."""
        config = {
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'weeth',
                'max_stake_spread_move': 0.02215
            },
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            }
        }
        
        # Create data provider with AAVE risk parameters
        data_provider = DataProvider.__new__(DataProvider)
        data_provider.data_dir = Path('/workspace/data')
        data_provider.data = {}
        data_provider._load_aave_risk_parameters()
        
        # Create risk monitor with data provider
        risk_monitor = RiskMonitor(config, data_provider)
        
        # Test with LTV above dynamic target but below critical
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 89000,  # 89% LTV - above dynamic target (88.785%)
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        result = await risk_monitor.calculate_aave_ltv_risk(exposure_data)
        
        # Should be warning level (above dynamic target)
        assert result['level'] == 'warning'
        assert 'dynamic target' in result['message']
        
        print(f"✅ Dynamic target risk level: {result['level']}")
        print(f"   Message: {result['message']}")


if __name__ == "__main__":
    # Run tests
    test_instance = TestRiskMonitorDynamicLTV()
    
    print("🧪 Testing RiskMonitor Dynamic LTV Target...")
    
    try:
        test_instance.test_dynamic_ltv_target_calculation()
        test_instance.test_dynamic_ltv_target_with_wsteth()
        test_instance.test_dynamic_ltv_target_fallback()
        test_instance.test_dynamic_ltv_target_minimum()
        
        # Run async tests
        asyncio.run(test_instance.test_aave_ltv_risk_with_dynamic_target())
        asyncio.run(test_instance.test_dynamic_target_risk_levels())
        
        print("\n✅ All RiskMonitor dynamic LTV target tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()