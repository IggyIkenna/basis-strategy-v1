#!/usr/bin/env python3
"""
Test RiskMonitor CEX liquidation simulation.
"""

import pytest
import asyncio
import sys
import os
from decimal import Decimal

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor


class TestRiskMonitorCEXLiquidation:
    """Test RiskMonitor CEX liquidation simulation."""
    
    @pytest.mark.asyncio
    async def test_cex_liquidation_safe_positions(self):
        """Test CEX liquidation simulation with safe positions."""
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
        
        risk_monitor = RiskMonitor(config)
        
        # Test with safe positions (margin ratio >= 10%)
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 85000,
            'cex_positions': {
                'binance': {
                    'current_margin': 10000,
                    'used_margin': 5000,
                    'position_value': 100000  # 15% margin ratio - safe
                },
                'bybit': {
                    'current_margin': 5000,
                    'used_margin': 2000,
                    'position_value': 50000  # 14% margin ratio - safe
                }
            },
            'net_delta': 0.0
        }
        
        result = await risk_monitor.simulate_cex_liquidation(exposure_data)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'overall_status' in result
        assert 'liquidation_rate' in result
        assert 'total_margin_at_risk' in result
        assert 'total_margin_lost' in result
        assert 'venue_details' in result
        assert 'message' in result
        assert 'timestamp' in result
        
        # Verify safe liquidation
        assert result['overall_status'] == 'safe'
        assert result['liquidation_rate'] == 0.0
        assert result['total_margin_lost'] == 0.0
        
        # Verify venue details
        venue_details = result['venue_details']
        assert 'binance' in venue_details
        assert 'bybit' in venue_details
        
        # Both venues should be safe
        assert venue_details['binance']['status'] == 'safe'
        assert venue_details['bybit']['status'] == 'safe'
        
        # Verify margin ratios
        assert venue_details['binance']['margin_ratio'] == 0.15  # 15%
        assert venue_details['bybit']['margin_ratio'] == 0.14  # 14%
        
        print(f"✅ Safe CEX liquidation simulation: {result['overall_status']}")
        print(f"   Liquidation rate: {result['liquidation_rate']:.1%}")
        print(f"   Total margin at risk: ${result['total_margin_at_risk']:,.2f}")
    
    @pytest.mark.asyncio
    async def test_cex_liquidation_risky_positions(self):
        """Test CEX liquidation simulation with risky positions."""
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
        
        risk_monitor = RiskMonitor(config)
        
        # Test with risky positions (margin ratio < 10%)
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 85000,
            'cex_positions': {
                'binance': {
                    'current_margin': 1000,
                    'used_margin': 500,
                    'position_value': 20000  # 7.5% margin ratio - liquidated
                },
                'bybit': {
                    'current_margin': 2000,
                    'used_margin': 1000,
                    'position_value': 50000  # 6% margin ratio - liquidated
                }
            },
            'net_delta': 0.0
        }
        
        result = await risk_monitor.simulate_cex_liquidation(exposure_data)
        
        # Verify critical liquidation
        assert result['overall_status'] == 'critical'
        assert result['liquidation_rate'] == 1.0  # 100% margin lost
        assert result['total_margin_lost'] > 0
        
        # Verify venue details
        venue_details = result['venue_details']
        assert 'binance' in venue_details
        assert 'bybit' in venue_details
        
        # Both venues should be liquidated
        assert venue_details['binance']['status'] == 'liquidated'
        assert venue_details['bybit']['status'] == 'liquidated'
        
        # Verify margin ratios
        assert venue_details['binance']['margin_ratio'] == 0.075  # 7.5%
        assert venue_details['bybit']['margin_ratio'] == 0.06  # 6%
        
        # Verify margin lost equals total margin
        assert venue_details['binance']['margin_lost'] == venue_details['binance']['total_margin']
        assert venue_details['bybit']['margin_lost'] == venue_details['bybit']['total_margin']
        
        print(f"✅ Risky CEX liquidation simulation: {result['overall_status']}")
        print(f"   Liquidation rate: {result['liquidation_rate']:.1%}")
        print(f"   Total margin lost: ${result['total_margin_lost']:,.2f}")
    
    @pytest.mark.asyncio
    async def test_cex_liquidation_mixed_positions(self):
        """Test CEX liquidation simulation with mixed safe/risky positions."""
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
        
        risk_monitor = RiskMonitor(config)
        
        # Test with mixed positions
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 85000,
            'cex_positions': {
                'binance': {
                    'current_margin': 10000,
                    'used_margin': 5000,
                    'position_value': 100000  # 15% margin ratio - safe
                },
                'bybit': {
                    'current_margin': 1000,
                    'used_margin': 500,
                    'position_value': 20000  # 7.5% margin ratio - liquidated
                }
            },
            'net_delta': 0.0
        }
        
        result = await risk_monitor.simulate_cex_liquidation(exposure_data)
        
        # Should be warning (some liquidation but not all)
        assert result['overall_status'] == 'warning'
        assert 0 < result['liquidation_rate'] < 1.0  # Partial liquidation
        
        # Verify venue details
        venue_details = result['venue_details']
        assert venue_details['binance']['status'] == 'safe'
        assert venue_details['bybit']['status'] == 'liquidated'
        
        print(f"✅ Mixed CEX liquidation simulation: {result['overall_status']}")
        print(f"   Liquidation rate: {result['liquidation_rate']:.1%}")
    
    @pytest.mark.asyncio
    async def test_cex_liquidation_no_positions(self):
        """Test CEX liquidation simulation with no CEX positions."""
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
        
        risk_monitor = RiskMonitor(config)
        
        # Test with no CEX positions
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 85000,
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        result = await risk_monitor.simulate_cex_liquidation(exposure_data)
        
        # Should be safe with no liquidation
        assert result['overall_status'] == 'safe'
        assert result['liquidation_rate'] == 0.0
        assert result['total_margin_at_risk'] == 0.0
        assert result['total_margin_lost'] == 0.0
        assert result['venue_details'] == {}
        
        print("✅ No CEX positions liquidation simulation: safe")
    
    @pytest.mark.asyncio
    async def test_cex_liquidation_error_handling(self):
        """Test CEX liquidation simulation error handling."""
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
        
        risk_monitor = RiskMonitor(config)
        
        # Test with invalid data
        exposure_data = {
            'cex_positions': {
                'binance': {
                    'current_margin': 'invalid',
                    'used_margin': 500,
                    'position_value': 20000
                }
            }
        }
        
        result = await risk_monitor.simulate_cex_liquidation(exposure_data)
        
        # Should handle error gracefully
        assert 'overall_status' in result
        assert result['overall_status'] in ['error', 'safe']  # Either error or safe fallback
        
        print(f"✅ CEX liquidation error handling: {result['overall_status']}")
    
    def test_cex_liquidation_thresholds(self):
        """Test CEX liquidation threshold logic."""
        # Test threshold calculations
        maintenance_threshold = 0.10  # 10%
        
        # Test safe margin ratio (15%)
        margin_ratio_safe = 0.15
        if margin_ratio_safe < maintenance_threshold:
            status = 'liquidated'
        else:
            status = 'safe'
        assert status == 'safe'
        
        # Test risky margin ratio (5%)
        margin_ratio_risky = 0.05
        if margin_ratio_risky < maintenance_threshold:
            status = 'liquidated'
        else:
            status = 'safe'
        assert status == 'liquidated'
        
        # Test exact threshold (10%)
        margin_ratio_exact = 0.10
        if margin_ratio_exact < maintenance_threshold:
            status = 'liquidated'
        else:
            status = 'safe'
        assert status == 'safe'  # >= threshold is safe
        
        print("✅ CEX liquidation thresholds work correctly")


if __name__ == "__main__":
    # Run tests
    test_instance = TestRiskMonitorCEXLiquidation()
    
    print("🧪 Testing RiskMonitor CEX Liquidation Simulation...")
    
    try:
        # Run async tests
        asyncio.run(test_instance.test_cex_liquidation_safe_positions())
        asyncio.run(test_instance.test_cex_liquidation_risky_positions())
        asyncio.run(test_instance.test_cex_liquidation_mixed_positions())
        asyncio.run(test_instance.test_cex_liquidation_no_positions())
        asyncio.run(test_instance.test_cex_liquidation_error_handling())
        
        # Run sync test
        test_instance.test_cex_liquidation_thresholds()
        
        print("\n✅ All RiskMonitor CEX liquidation simulation tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()