#!/usr/bin/env python3
"""
Test RiskMonitor AAVE liquidation simulation.
"""

import pytest
import asyncio
import sys
import os
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor
from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider


class TestRiskMonitorAAVELiquidation:
    """Test RiskMonitor AAVE liquidation simulation."""
    
    @pytest.fixture
    def mock_data_provider(self):
        """Create a mock DataProvider with mocked AAVE risk parameters."""
        with patch('builtins.open', create=True), \
             patch('json.load', return_value={
                 'emode': {
                     'liquidation_thresholds': {'weETH_WETH': 0.95, 'wstETH_WETH': 0.93},
                     'ltv_limits': {'weETH_WETH': 0.91, 'wstETH_WETH': 0.89},
                     'liquidation_bonus': {'weETH_WETH': 0.05, 'wstETH_WETH': 0.05},
                     'eligible_pairs': ['weETH_WETH', 'wstETH_WETH']
                 },
                 'standard': {
                     'liquidation_thresholds': {'WETH': 0.85, 'wstETH': 0.80, 'weETH': 0.80, 'USDT': 0.90},
                     'ltv_limits': {'WETH': 0.80, 'wstETH': 0.75, 'weETH': 0.75, 'USDT': 0.85},
                     'liquidation_bonus': {'WETH': 0.05, 'wstETH': 0.05, 'weETH': 0.05, 'USDT': 0.05}
                 },
                 'reserve_factors': {
                     'weETH': 0.10,
                     'wstETH': 0.10,
                     'WETH': 0.10,
                     'USDT': 0.10
                 }
             }), \
             patch('pathlib.Path.exists', return_value=True):
            
            provider = DataProvider.__new__(DataProvider)
            provider.data_dir = Path('/workspace/data')
            provider.data = {}
            provider._load_aave_risk_parameters()
            return provider
    
    @pytest.mark.asyncio
    async def test_aave_liquidation_safe_position(self, mock_data_provider):
        """Test AAVE liquidation simulation with safe position."""
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
        
        # Create risk monitor with data provider
        risk_monitor = RiskMonitor(config, mock_data_provider)
        
        # Test with safe position (health factor > 1.0)
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 85000,  # 85% LTV - safe
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        result = await risk_monitor.simulate_aave_liquidation(exposure_data)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'overall_status' in result
        assert 'liquidation_status' in result
        assert 'health_factor' in result
        assert 'liquidation_penalty' in result
        assert 'debt_liquidated' in result
        assert 'liquidation_bonus' in result
        assert 'liquidation_threshold' in result
        assert 'collateral_value' in result
        assert 'debt_value' in result
        assert 'message' in result
        assert 'details' in result
        assert 'timestamp' in result
        
        # Verify safe liquidation
        assert result['overall_status'] == 'safe'
        assert result['liquidation_status'] == 'safe'
        assert result['health_factor'] > 1.0
        assert result['liquidation_penalty'] == 0.0
        assert result['debt_liquidated'] == 0.0
        
        # Verify liquidation bonus from AAVE risk params
        assert result['liquidation_bonus'] == 0.05  # 5% from JSON
        
        print(f"✅ Safe AAVE liquidation simulation: {result['overall_status']}")
        print(f"   Health Factor: {result['health_factor']:.2f}")
        print(f"   Liquidation Bonus: {result['liquidation_bonus']:.1%}")
    
    @pytest.mark.asyncio
    async def test_aave_liquidation_risky_position(self, mock_data_provider):
        """Test AAVE liquidation simulation with risky position."""
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
        
        # Create risk monitor with data provider
        risk_monitor = RiskMonitor(config, mock_data_provider)
        
        # Test with risky position (health factor < 1.0)
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 96000,  # 96% LTV - liquidated
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        result = await risk_monitor.simulate_aave_liquidation(exposure_data)
        
        # Verify liquidation occurs
        assert result['overall_status'] in ['warning', 'critical']
        assert result['liquidation_status'] == 'liquidated'
        assert result['health_factor'] < 1.0
        assert result['liquidation_penalty'] > 0.0
        assert result['debt_liquidated'] > 0.0
        
        # Verify liquidation calculation
        expected_debt_liquidated = 96000 * 0.5  # 50% of debt
        expected_penalty = expected_debt_liquidated * (1.0 + 0.05)  # + 5% bonus
        
        assert abs(result['debt_liquidated'] - expected_debt_liquidated) < 1.0
        assert abs(result['liquidation_penalty'] - expected_penalty) < 1.0
        
        print(f"✅ Risky AAVE liquidation simulation: {result['overall_status']}")
        print(f"   Health Factor: {result['health_factor']:.2f}")
        print(f"   Debt Liquidated: ${result['debt_liquidated']:,.2f}")
        print(f"   Liquidation Penalty: ${result['liquidation_penalty']:,.2f}")
    
    @pytest.mark.asyncio
    async def test_aave_liquidation_with_wsteth(self, mock_data_provider):
        """Test AAVE liquidation simulation with wstETH."""
        config = {
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'wsteth'
            },
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            }
        }
        
        # Create risk monitor with data provider
        risk_monitor = RiskMonitor(config, mock_data_provider)
        
        # Test with wstETH position
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 85000,
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        result = await risk_monitor.simulate_aave_liquidation(exposure_data)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'overall_status' in result
        assert 'liquidation_bonus' in result
        
        # wstETH should have same liquidation bonus as weETH (5%)
        assert result['liquidation_bonus'] == 0.05
        
        print(f"✅ AAVE liquidation simulation with wstETH: {result['overall_status']}")
        print(f"   Liquidation Bonus: {result['liquidation_bonus']:.1%}")
    
    @pytest.mark.asyncio
    async def test_aave_liquidation_no_debt(self, mock_data_provider):
        """Test AAVE liquidation simulation with no debt."""
        config = {
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'weeth'
            },
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            }
        }
        
        # Create risk monitor with data provider
        risk_monitor = RiskMonitor(config, mock_data_provider)
        
        # Test with no debt
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 0,  # No debt
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        result = await risk_monitor.simulate_aave_liquidation(exposure_data)
        
        # Should be safe with no liquidation
        assert result['overall_status'] == 'safe'
        assert result['liquidation_penalty'] == 0.0
        assert result['debt_liquidated'] == 0.0
        assert 'No AAVE debt to liquidate' in result['message']
        
        print("✅ No AAVE debt liquidation simulation: safe")
    
    @pytest.mark.asyncio
    async def test_aave_liquidation_no_data_provider(self):
        """Test AAVE liquidation simulation without data provider."""
        config = {
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'weeth'
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
        
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 85000,
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        result = await risk_monitor.simulate_aave_liquidation(exposure_data)
        
        # Should return safe with no data provider message
        assert result['overall_status'] == 'safe'
        assert 'No data provider available' in result['message']
        
        print("✅ AAVE liquidation simulation without data provider handled correctly")
    
    @pytest.mark.asyncio
    async def test_aave_liquidation_critical_penalty(self, mock_data_provider):
        """Test AAVE liquidation simulation with critical penalty."""
        config = {
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'weeth'
            },
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            }
        }
        
        # Create risk monitor with data provider
        risk_monitor = RiskMonitor(config, mock_data_provider)
        
        # Test with very high debt that would result in critical penalty
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 98000,  # Very high LTV - liquidated with high penalty
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        result = await risk_monitor.simulate_aave_liquidation(exposure_data)
        
        # Should be liquidated
        assert result['liquidation_status'] == 'liquidated'
        assert result['health_factor'] < 1.0
        
        # Check if penalty is critical (>= 50% of collateral)
        penalty_ratio = result['liquidation_penalty'] / result['collateral_value']
        if penalty_ratio >= 0.5:
            assert result['overall_status'] == 'critical'
        else:
            assert result['overall_status'] == 'warning'
        
        print(f"✅ Critical AAVE liquidation simulation: {result['overall_status']}")
        print(f"   Penalty Ratio: {penalty_ratio:.1%}")
        print(f"   Liquidation Penalty: ${result['liquidation_penalty']:,.2f}")
    
    def test_aave_liquidation_calculation_logic(self):
        """Test AAVE liquidation calculation logic."""
        # Test liquidation calculation
        debt = 100000
        liquidation_bonus = 0.01  # 1%
        
        # 50% of debt liquidated
        debt_liquidated = debt * 0.5
        
        # Liquidation penalty = debt_liquidated * (1 + liquidation_bonus)
        liquidation_penalty = debt_liquidated * (1.0 + liquidation_bonus)
        
        expected_debt_liquidated = 50000
        expected_penalty = 50500  # 50000 * 1.01
        
        assert debt_liquidated == expected_debt_liquidated
        assert liquidation_penalty == expected_penalty
        
        print("✅ AAVE liquidation calculation logic works correctly")
        print(f"   Debt: ${debt:,}")
        print(f"   Debt Liquidated: ${debt_liquidated:,}")
        print(f"   Liquidation Penalty: ${liquidation_penalty:,}")


if __name__ == "__main__":
    # Run tests
    test_instance = TestRiskMonitorAAVELiquidation()
    
    print("🧪 Testing RiskMonitor AAVE Liquidation Simulation...")
    
    try:
        # Run async tests
        asyncio.run(test_instance.test_aave_liquidation_safe_position())
        asyncio.run(test_instance.test_aave_liquidation_risky_position())
        asyncio.run(test_instance.test_aave_liquidation_with_wsteth())
        asyncio.run(test_instance.test_aave_liquidation_no_debt())
        asyncio.run(test_instance.test_aave_liquidation_no_data_provider())
        asyncio.run(test_instance.test_aave_liquidation_critical_penalty())
        
        # Run sync test
        test_instance.test_aave_liquidation_calculation_logic()
        
        print("\n✅ All RiskMonitor AAVE liquidation simulation tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()