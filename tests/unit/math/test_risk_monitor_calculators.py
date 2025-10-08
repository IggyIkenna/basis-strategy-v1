#!/usr/bin/env python3
"""
Test RiskMonitor integration with math calculators.
"""

import pytest
import asyncio
import sys
import os
from decimal import Decimal

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor


class TestRiskMonitorCalculators:
    """Test RiskMonitor integration with math calculators."""
    
    def test_calculator_imports(self):
        """Test that math calculators are properly imported."""
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
        
        risk_monitor = RiskMonitor(config)
        
        # Verify calculators are imported and available
        from basis_strategy_v1.core.math.health_calculator import HealthCalculator
        from basis_strategy_v1.core.math.ltv_calculator import LTVCalculator
        from basis_strategy_v1.core.math.margin_calculator import MarginCalculator
        
        assert HealthCalculator is not None
        assert LTVCalculator is not None
        assert MarginCalculator is not None
        
        print("✅ Math calculators imported successfully")
    
    @pytest.mark.asyncio
    async def test_aave_ltv_risk_with_calculators(self):
        """Test AAVE LTV risk calculation using integrated calculators."""
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
        
        risk_monitor = RiskMonitor(config)
        
        # Test with AAVE positions
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 85000,
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        result = await risk_monitor.calculate_aave_ltv_risk(exposure_data)
        
        # Verify result structure includes calculator outputs
        assert isinstance(result, dict)
        assert 'level' in result
        assert 'value' in result
        assert 'health_factor' in result  # Added by HealthCalculator
        assert 'message' in result
        assert 'timestamp' in result
        
        # Verify LTV calculation (85% = 85000/100000)
        assert abs(result['value'] - 0.85) < 0.001
        
        # Verify health factor is calculated
        assert isinstance(result['health_factor'], (int, float))
        assert result['health_factor'] > 0
        
        print(f"✅ AAVE LTV risk with calculators: {result['level']}")
        print(f"   LTV: {result['value']:.2%}")
        print(f"   Health Factor: {result['health_factor']}")
    
    @pytest.mark.asyncio
    async def test_cex_margin_risk_with_calculators(self):
        """Test CEX margin risk calculation using integrated calculators."""
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
        
        risk_monitor = RiskMonitor(config)
        
        # Test with CEX positions
        exposure_data = {
            'aave_collateral': 0,
            'aave_debt': 0,
            'cex_positions': {
                'binance': {
                    'current_margin': 10000,
                    'used_margin': 5000,
                    'position_value': 100000
                },
                'bybit': {
                    'current_margin': 5000,
                    'used_margin': 2000,
                    'position_value': 50000
                }
            },
            'net_delta': 0.0
        }
        
        result = await risk_monitor.calculate_cex_margin_risk(exposure_data)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'level' in result
        assert 'value' in result
        assert 'message' in result
        assert 'timestamp' in result
        assert 'venue_details' in result
        
        # Verify venue details are calculated
        venue_details = result['venue_details']
        assert 'binance' in venue_details
        assert 'bybit' in venue_details
        
        # Verify margin ratios are calculated correctly
        binance_ratio = float(venue_details['binance']['value'])
        bybit_ratio = float(venue_details['bybit']['value'])
        
        # Binance: (10000+5000)/100000 = 15% (total margin ratio)
        # Bybit: (5000+2000)/50000 = 14% (total margin ratio)
        assert abs(binance_ratio - 0.15) < 0.001
        assert abs(bybit_ratio - 0.14) < 0.001
        
        print(f"✅ CEX margin risk with calculators: {result['level']}")
        print(f"   Overall Margin Ratio: {result['value']:.2%}")
        print(f"   Binance: {binance_ratio:.2%}")
        print(f"   Bybit: {bybit_ratio:.2%}")
    
    @pytest.mark.asyncio
    async def test_calculator_precision(self):
        """Test that calculators provide precise decimal calculations."""
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
        
        risk_monitor = RiskMonitor(config)
        
        # Test with precise decimal values
        exposure_data = {
            'aave_collateral': 100000.123456,
            'aave_debt': 85000.789012,
            'cex_positions': {
                'binance': {
                    'current_margin': 10000.111111,
                    'used_margin': 5000.222222,
                    'position_value': 100000.333333
                }
            },
            'net_delta': 0.0
        }
        
        # Test AAVE LTV calculation precision
        aave_result = await risk_monitor.calculate_aave_ltv_risk(exposure_data)
        expected_ltv = 85000.789012 / 100000.123456
        assert abs(float(aave_result['value']) - expected_ltv) < 0.000001
        
        # Test CEX margin calculation precision
        cex_result = await risk_monitor.calculate_cex_margin_risk(exposure_data)
        expected_margin_ratio = (10000.111111 + 5000.222222) / 100000.333333  # total margin ratio
        assert abs(float(cex_result['value']) - expected_margin_ratio) < 0.000001
        
        print("✅ Calculator precision verified")
    
    @pytest.mark.asyncio
    async def test_calculator_error_handling(self):
        """Test that calculators handle edge cases gracefully."""
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
        
        risk_monitor = RiskMonitor(config)
        
        # Test with zero values
        zero_exposure_data = {
            'aave_collateral': 0,
            'aave_debt': 0,
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        aave_result = await risk_monitor.calculate_aave_ltv_risk(zero_exposure_data)
        assert aave_result['level'] == 'safe'
        assert aave_result['value'] == 0.0
        
        # Test with negative values
        negative_exposure_data = {
            'aave_collateral': -1000,
            'aave_debt': 500,
            'cex_positions': {},
            'net_delta': 0.0
        }
        
        # Should handle gracefully (may return safe or error)
        aave_result = await risk_monitor.calculate_aave_ltv_risk(negative_exposure_data)
        assert 'level' in aave_result
        
        print("✅ Calculator error handling verified")


if __name__ == "__main__":
    # Run tests
    test_instance = TestRiskMonitorCalculators()
    
    print("🧪 Testing RiskMonitor Calculator Integration...")
    
    try:
        test_instance.test_calculator_imports()
        
        # Run async tests
        asyncio.run(test_instance.test_aave_ltv_risk_with_calculators())
        asyncio.run(test_instance.test_cex_margin_risk_with_calculators())
        asyncio.run(test_instance.test_calculator_precision())
        asyncio.run(test_instance.test_calculator_error_handling())
        
        print("\n✅ All RiskMonitor calculator integration tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()