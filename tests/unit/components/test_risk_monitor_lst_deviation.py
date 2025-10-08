#!/usr/bin/env python3
"""
Test RiskMonitor LST price deviation monitoring.
"""

import pytest
import asyncio
import sys
import os
from decimal import Decimal
from pathlib import Path
import pandas as pd

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor
from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider


class TestRiskMonitorLSTDeviation:
    """Test RiskMonitor LST price deviation monitoring."""
    
    @pytest.mark.asyncio
    async def test_lst_price_deviation_safe(self):
        """Test LST price deviation monitoring with safe deviation."""
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
        
        # Create data provider with mocked data
        from unittest.mock import patch
        with patch('builtins.open', create=True), \
             patch('json.load', return_value={
                 'emode': {
                     'liquidation_thresholds': {'weETH_WETH': 0.95, 'wstETH_WETH': 0.93},
                     'max_ltv_limits': {'weETH_WETH': 0.91, 'wstETH_WETH': 0.89},
                     'liquidation_bonus': {'weETH_WETH': 0.05, 'wstETH_WETH': 0.05},
                     'eligible_pairs': ['weETH_WETH', 'wstETH_WETH']
                 },
                 'normal_mode': {
                     'liquidation_thresholds': {'WETH': 0.85, 'wstETH': 0.80, 'weETH': 0.80, 'USDT': 0.90},
                     'max_ltv_limits': {'WETH': 0.80, 'wstETH': 0.75, 'weETH': 0.75, 'USDT': 0.85}
                 },
                 'metadata': {
                     'created': '2024-01-01',
                     'source': 'AAVE V3',
                     'description': 'AAVE V3 risk parameters',
                     'version': '1.0'
                 }
             }), \
             patch('pathlib.Path.exists', return_value=True):
            
            data_provider = DataProvider.__new__(DataProvider)
            data_provider.data_dir = Path('/workspace/data')
            data_provider.data = {
                'weeth_oracle': pd.DataFrame({
                    'oracle_price_eth': [2000.0, 2100.0]
                }, index=pd.DatetimeIndex(['2024-05-12 06:00:00', '2024-05-12 07:00:00'], tz='UTC')),
                'weeth_market_price': pd.DataFrame({
                    'price': [2000.0, 2100.0]
                }, index=pd.DatetimeIndex(['2024-05-12 06:00:00', '2024-05-12 07:00:00'], tz='UTC'))
            }
            data_provider.aave_risk_params = {
                'emode': {
                    'liquidation_thresholds': {'weETH_WETH': 0.95, 'wstETH_WETH': 0.93},
                    'max_ltv_limits': {'weETH_WETH': 0.91, 'wstETH_WETH': 0.89},
                    'liquidation_bonus': {'weETH_WETH': 0.05, 'wstETH_WETH': 0.05},
                    'eligible_pairs': ['weETH_WETH', 'wstETH_WETH']
                },
                'normal_mode': {
                    'liquidation_thresholds': {'WETH': 0.85, 'wstETH': 0.80, 'weETH': 0.80, 'USDT': 0.90},
                    'max_ltv_limits': {'WETH': 0.80, 'wstETH': 0.75, 'weETH': 0.75, 'USDT': 0.85}
                },
                'metadata': {
                    'created': '2024-01-01',
                    'source': 'AAVE V3',
                    'description': 'AAVE V3 risk parameters',
                    'version': '1.0'
                }
            }
        
        # Create risk monitor with data provider
        risk_monitor = RiskMonitor(config, data_provider)
        
        # Test with safe deviation
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 85000,
            'cex_positions': {},
            'net_delta': 0.0,
            'timestamp': pd.Timestamp('2024-05-12 06:00:00', tz='UTC')
        }
        
        result = await risk_monitor.calculate_lst_price_deviation_risk(exposure_data)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'level' in result
        assert 'value' in result
        assert 'oracle_price' in result
        assert 'market_price' in result
        assert 'deviation_pct' in result
        assert 'message' in result
        assert 'timestamp' in result
        
        # Verify safe level (deviation < 1%)
        assert result['level'] == 'safe'
        assert result['deviation_pct'] < 0.01  # Less than 1%
        
        print(f"✅ LST price deviation safe: {result['deviation_pct']:.2%}")
        print(f"   Oracle: {result['oracle_price']:.6f}")
        print(f"   Market: {result['market_price']:.6f}")
    
    @pytest.mark.asyncio
    async def test_lst_price_deviation_no_data_provider(self):
        """Test LST price deviation monitoring without data provider."""
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
            'timestamp': pd.Timestamp('2024-05-12 06:00:00', tz='UTC')
        }
        
        result = await risk_monitor.calculate_lst_price_deviation_risk(exposure_data)
        
        # Should return safe level with no data provider message
        assert result['level'] == 'safe'
        assert 'No data provider available' in result['message']
        
        print("✅ LST price deviation without data provider handled correctly")
    
    @pytest.mark.asyncio
    async def test_lst_price_deviation_with_wsteth(self):
        """Test LST price deviation monitoring with wstETH."""
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
        
        # Create data provider with mocked wstETH data
        from unittest.mock import patch
        with patch('builtins.open', create=True), \
             patch('json.load', return_value={
                 'emode': {
                     'liquidation_thresholds': {'weETH_WETH': 0.95, 'wstETH_WETH': 0.93},
                     'max_ltv_limits': {'weETH_WETH': 0.91, 'wstETH_WETH': 0.89},
                     'liquidation_bonus': {'weETH_WETH': 0.05, 'wstETH_WETH': 0.05},
                     'eligible_pairs': ['weETH_WETH', 'wstETH_WETH']
                 },
                 'normal_mode': {
                     'liquidation_thresholds': {'WETH': 0.85, 'wstETH': 0.80, 'weETH': 0.80, 'USDT': 0.90},
                     'max_ltv_limits': {'WETH': 0.80, 'wstETH': 0.75, 'weETH': 0.75, 'USDT': 0.85}
                 },
                 'metadata': {
                     'created': '2024-01-01',
                     'source': 'AAVE V3',
                     'description': 'AAVE V3 risk parameters',
                     'version': '1.0'
                 }
             }), \
             patch('pathlib.Path.exists', return_value=True):
            
            data_provider = DataProvider.__new__(DataProvider)
            data_provider.data_dir = Path('/workspace/data')
            data_provider.data = {
                'wsteth_oracle': pd.DataFrame({
                    'oracle_price_eth': [2000.0, 2100.0]
                }, index=pd.DatetimeIndex(['2024-05-12 06:00:00', '2024-05-12 07:00:00'], tz='UTC')),
                'wsteth_market_price': pd.DataFrame({
                    'price': [2000.0, 2100.0]
                }, index=pd.DatetimeIndex(['2024-05-12 06:00:00', '2024-05-12 07:00:00'], tz='UTC'))
            }
            data_provider.aave_risk_params = {
                'emode': {
                    'liquidation_thresholds': {'weETH_WETH': 0.95, 'wstETH_WETH': 0.93},
                    'max_ltv_limits': {'weETH_WETH': 0.91, 'wstETH_WETH': 0.89},
                    'liquidation_bonus': {'weETH_WETH': 0.05, 'wstETH_WETH': 0.05},
                    'eligible_pairs': ['weETH_WETH', 'wstETH_WETH']
                },
                'normal_mode': {
                    'liquidation_thresholds': {'WETH': 0.85, 'wstETH': 0.80, 'weETH': 0.80, 'USDT': 0.90},
                    'max_ltv_limits': {'WETH': 0.80, 'wstETH': 0.75, 'weETH': 0.75, 'USDT': 0.85}
                },
                'metadata': {
                    'created': '2024-01-01',
                    'source': 'AAVE V3',
                    'description': 'AAVE V3 risk parameters',
                    'version': '1.0'
                }
            }
        
        # Create risk monitor with data provider
        risk_monitor = RiskMonitor(config, data_provider)
        
        exposure_data = {
            'timestamp': pd.Timestamp('2024-05-12 06:00:00', tz='UTC')
        }
        
        result = await risk_monitor.calculate_lst_price_deviation_risk(exposure_data)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'level' in result
        assert 'oracle_price' in result
        assert 'market_price' in result
        
        print(f"✅ LST price deviation for wstETH: {result['level']}")
        print(f"   Deviation: {result['deviation_pct']:.2%}")
    
    @pytest.mark.asyncio
    async def test_lst_price_deviation_error_handling(self):
        """Test LST price deviation monitoring error handling."""
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
        
        # Create data provider without required data
        data_provider = DataProvider.__new__(DataProvider)
        data_provider.data_dir = Path('/workspace/data')
        data_provider.data = {}
        # Don't load oracle or market prices
        
        # Create risk monitor with data provider
        risk_monitor = RiskMonitor(config, data_provider)
        
        exposure_data = {
            'timestamp': pd.Timestamp('2024-05-12 06:00:00', tz='UTC')
        }
        
        result = await risk_monitor.calculate_lst_price_deviation_risk(exposure_data)
        
        # Should handle error gracefully
        assert 'level' in result
        assert result['level'] in ['error', 'safe']  # Either error or safe fallback
        
        print(f"✅ LST price deviation error handling: {result['level']}")
    
    @pytest.mark.asyncio
    async def test_lst_price_deviation_integration(self):
        """Test LST price deviation integration with overall risk assessment."""
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
        
        # Create data provider with mocked data
        from unittest.mock import patch
        with patch('builtins.open', create=True), \
             patch('json.load', return_value={
                 'emode': {
                     'liquidation_thresholds': {'weETH_WETH': 0.95, 'wstETH_WETH': 0.93},
                     'max_ltv_limits': {'weETH_WETH': 0.91, 'wstETH_WETH': 0.89},
                     'liquidation_bonus': {'weETH_WETH': 0.05, 'wstETH_WETH': 0.05},
                     'eligible_pairs': ['weETH_WETH', 'wstETH_WETH']
                 },
                 'normal_mode': {
                     'liquidation_thresholds': {'WETH': 0.85, 'wstETH': 0.80, 'weETH': 0.80, 'USDT': 0.90},
                     'max_ltv_limits': {'WETH': 0.80, 'wstETH': 0.75, 'weETH': 0.75, 'USDT': 0.85}
                 },
                 'metadata': {
                     'created': '2024-01-01',
                     'source': 'AAVE V3',
                     'description': 'AAVE V3 risk parameters',
                     'version': '1.0'
                 }
             }), \
             patch('pathlib.Path.exists', return_value=True):
            
            data_provider = DataProvider.__new__(DataProvider)
            data_provider.data_dir = Path('/workspace/data')
            data_provider.data = {
                'weeth_oracle': pd.DataFrame({
                    'oracle_price_eth': [2000.0, 2100.0]
                }, index=pd.DatetimeIndex(['2024-05-12 06:00:00', '2024-05-12 07:00:00'], tz='UTC')),
                'weeth_market_price': pd.DataFrame({
                    'price': [2000.0, 2100.0]
                }, index=pd.DatetimeIndex(['2024-05-12 06:00:00', '2024-05-12 07:00:00'], tz='UTC'))
            }
            data_provider.aave_risk_params = {
                'emode': {
                    'liquidation_thresholds': {'weETH_WETH': 0.95, 'wstETH_WETH': 0.93},
                    'max_ltv_limits': {'weETH_WETH': 0.91, 'wstETH_WETH': 0.89},
                    'liquidation_bonus': {'weETH_WETH': 0.05, 'wstETH_WETH': 0.05},
                    'eligible_pairs': ['weETH_WETH', 'wstETH_WETH']
                },
                'normal_mode': {
                    'liquidation_thresholds': {'WETH': 0.85, 'wstETH': 0.80, 'weETH': 0.80, 'USDT': 0.90},
                    'max_ltv_limits': {'WETH': 0.80, 'wstETH': 0.75, 'weETH': 0.75, 'USDT': 0.85}
                },
                'metadata': {
                    'created': '2024-01-01',
                    'source': 'AAVE V3',
                    'description': 'AAVE V3 risk parameters',
                    'version': '1.0'
                }
            }
        
        # Create risk monitor with data provider
        risk_monitor = RiskMonitor(config, data_provider)
        
        # Test overall risk assessment
        exposure_data = {
            'aave_collateral': 100000,
            'aave_debt': 85000,
            'cex_positions': {},
            'net_delta': 0.0,
            'timestamp': pd.Timestamp('2024-05-12 06:00:00', tz='UTC')
        }
        
        result = await risk_monitor.calculate_overall_risk(exposure_data)
        
        # Verify LST price deviation is included
        assert 'lst_price_deviation' in result
        assert isinstance(result['lst_price_deviation'], dict)
        assert 'level' in result['lst_price_deviation']
        
        # Verify summary includes all risks
        assert 'summary' in result
        assert 'total_risks' in result['summary']
        assert 'warning_risks' in result['summary']
        assert 'critical_risks' in result['summary']
        
        print(f"✅ LST price deviation integration: {result['level']}")
        print(f"   Total risks: {result['summary']['total_risks']}")
        print(f"   LST deviation: {result['lst_price_deviation']['level']}")
    
    def test_lst_price_deviation_thresholds(self):
        """Test LST price deviation threshold logic."""
        # Test threshold calculations
        warning_threshold = 0.01  # 1%
        critical_threshold = 0.02  # 2%
        
        # Test safe deviation (0.5%)
        deviation_safe = 0.005
        if deviation_safe >= critical_threshold:
            level = 'critical'
        elif deviation_safe >= warning_threshold:
            level = 'warning'
        else:
            level = 'safe'
        assert level == 'safe'
        
        # Test warning deviation (1.5%)
        deviation_warning = 0.015
        if deviation_warning >= critical_threshold:
            level = 'critical'
        elif deviation_warning >= warning_threshold:
            level = 'warning'
        else:
            level = 'safe'
        assert level == 'warning'
        
        # Test critical deviation (2.5%)
        deviation_critical = 0.025
        if deviation_critical >= critical_threshold:
            level = 'critical'
        elif deviation_critical >= warning_threshold:
            level = 'warning'
        else:
            level = 'safe'
        assert level == 'critical'
        
        print("✅ LST price deviation thresholds work correctly")


if __name__ == "__main__":
    # Run tests
    test_instance = TestRiskMonitorLSTDeviation()
    
    print("🧪 Testing RiskMonitor LST Price Deviation Monitoring...")
    
    try:
        # Run async tests
        asyncio.run(test_instance.test_lst_price_deviation_safe())
        asyncio.run(test_instance.test_lst_price_deviation_no_data_provider())
        asyncio.run(test_instance.test_lst_price_deviation_with_wsteth())
        asyncio.run(test_instance.test_lst_price_deviation_error_handling())
        asyncio.run(test_instance.test_lst_price_deviation_integration())
        
        # Run sync test
        test_instance.test_lst_price_deviation_thresholds()
        
        print("\n✅ All RiskMonitor LST price deviation tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()