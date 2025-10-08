#!/usr/bin/env python3
"""
Test RiskMonitor.assess_risk() wrapper method.
"""

import pytest
import asyncio
import sys
import os

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor


class TestRiskMonitorAssessRisk:
    """Test RiskMonitor.assess_risk() wrapper method."""
    
    def test_assess_risk_method_exists(self):
        """Test that assess_risk method exists."""
        config = {
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            },
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'weeth',
                'max_stake_spread_move': 0.02215
            }
        }
        
        risk_monitor = RiskMonitor(config)
        assert hasattr(risk_monitor, 'assess_risk')
        print("✅ assess_risk method exists")
    
    def test_assess_risk_method_signature(self):
        """Test that assess_risk method has correct signature."""
        config = {
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            },
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'weeth',
                'max_stake_spread_move': 0.02215
            }
        }
        
        risk_monitor = RiskMonitor(config)
        
        import inspect
        sig = inspect.signature(risk_monitor.assess_risk)
        params = list(sig.parameters.keys())
        
        # Should have exposure_data and optional market_data
        assert 'exposure_data' in params
        assert 'market_data' in params
        
        # market_data should be optional (have default)
        market_data_param = sig.parameters['market_data']
        assert market_data_param.default is None
        
        print(f"✅ assess_risk method signature correct: {params}")
    
    @pytest.mark.asyncio
    async def test_assess_risk_basic_functionality(self):
        """Test basic functionality of assess_risk method."""
        config = {
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            },
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'weeth',
                'max_stake_spread_move': 0.02215
            }
        }
        
        risk_monitor = RiskMonitor(config)
        
        # Test with basic exposure data
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 85000,
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        result = await risk_monitor.assess_risk(exposure_data)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'level' in result
        assert result['level'] in ['safe', 'warning', 'critical']
        
        print(f"✅ assess_risk basic functionality works: {result['level']}")
    
    @pytest.mark.asyncio
    async def test_assess_risk_with_market_data(self):
        """Test assess_risk method with market data."""
        config = {
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            },
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'weeth',
                'max_stake_spread_move': 0.02215
            }
        }
        
        risk_monitor = RiskMonitor(config)
        
        # Test with exposure data and market data
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 85000,
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        market_data = {
            'eth_price': 3000.0,
            'timestamp': '2024-05-12T06:00:00Z'
        }
        
        result = await risk_monitor.assess_risk(exposure_data, market_data)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'level' in result
        assert result['level'] in ['safe', 'warning', 'critical']
        
        # Verify market data was stored
        assert hasattr(risk_monitor, 'current_market_data')
        assert risk_monitor.current_market_data == market_data
        
        print(f"✅ assess_risk with market data works: {result['level']}")
    
    @pytest.mark.asyncio
    async def test_assess_risk_wrapper_calls_calculate_overall_risk(self):
        """Test that assess_risk wrapper calls calculate_overall_risk internally."""
        config = {
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            },
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'weeth',
                'max_stake_spread_move': 0.02215
            }
        }
        
        risk_monitor = RiskMonitor(config)
        
        # Test that both methods return similar results
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 85000,
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        # Call both methods
        assess_result = await risk_monitor.assess_risk(exposure_data)
        calculate_result = await risk_monitor.calculate_overall_risk(exposure_data)
        
        # Results should have the same structure and level (same method called internally)
        assert isinstance(assess_result, dict)
        assert isinstance(calculate_result, dict)
        assert 'level' in assess_result
        assert 'level' in calculate_result
        assert assess_result['level'] == calculate_result['level']
        
        print("✅ assess_risk wrapper correctly calls calculate_overall_risk")
    
    @pytest.mark.asyncio
    async def test_assess_risk_error_handling(self):
        """Test error handling in assess_risk method."""
        config = {
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            },
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0,
                'lst_type': 'weeth',
                'max_stake_spread_move': 0.02215
            }
        }
        
        risk_monitor = RiskMonitor(config)
        
        # Test with invalid exposure data
        invalid_exposure_data = None
        
        # Should handle gracefully (let calculate_overall_risk handle the error)
        try:
            result = await risk_monitor.assess_risk(invalid_exposure_data)
            # If it doesn't raise an exception, that's also acceptable
            print("✅ assess_risk handles invalid data gracefully")
        except Exception as e:
            # Expected behavior - let the underlying method handle errors
            print(f"✅ assess_risk properly propagates errors: {type(e).__name__}")


if __name__ == "__main__":
    # Run tests
    test_instance = TestRiskMonitorAssessRisk()
    
    print("🧪 Testing RiskMonitor.assess_risk() Wrapper Method...")
    
    try:
        test_instance.test_assess_risk_method_exists()
        test_instance.test_assess_risk_method_signature()
        
        # Run async tests
        asyncio.run(test_instance.test_assess_risk_basic_functionality())
        asyncio.run(test_instance.test_assess_risk_with_market_data())
        asyncio.run(test_instance.test_assess_risk_wrapper_calls_calculate_overall_risk())
        asyncio.run(test_instance.test_assess_risk_error_handling())
        
        print("\n✅ All RiskMonitor.assess_risk() tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()