#!/usr/bin/env python3
"""
Test RiskMonitor fail-fast config access (no .get() defaults).
"""

import pytest
import sys
import os

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.core.rebalancing.risk_monitor import RiskMonitor


class TestRiskMonitorFailFast:
    """Test RiskMonitor fail-fast config access."""
    
    def test_fail_fast_with_missing_risk_section(self):
        """Test that RiskMonitor fails fast when risk section is missing."""
        incomplete_config = {
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0
            }
            # Missing 'risk' section
        }
        
        with pytest.raises(KeyError, match="'risk'"):
            RiskMonitor(incomplete_config)
        
        print("✅ Fail-fast behavior works with missing risk section")
    
    def test_fail_fast_with_missing_strategy_section(self):
        """Test that RiskMonitor fails fast when strategy section is missing."""
        incomplete_config = {
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            }
            # Missing 'strategy' section
        }
        
        with pytest.raises(KeyError, match="'strategy'"):
            RiskMonitor(incomplete_config)
        
        print("✅ Fail-fast behavior works with missing strategy section")
    
    def test_fail_fast_with_missing_target_ltv(self):
        """Test that RiskMonitor fails fast when target_ltv is missing."""
        incomplete_config = {
            'strategy': {
                'rebalance_threshold_pct': 5.0
                # Missing 'target_ltv'
            },
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
            }
        }
        
        with pytest.raises(KeyError, match="'target_ltv'"):
            RiskMonitor(incomplete_config)
        
        print("✅ Fail-fast behavior works with missing target_ltv")
    
    def test_fail_fast_with_missing_aave_ltv_warning(self):
        """Test that RiskMonitor fails fast when aave_ltv_warning is missing."""
        incomplete_config = {
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0
            },
            'risk': {
                'aave_ltv_critical': 0.90,
                'margin_warning_pct': 0.20,
                'margin_critical_pct': 0.12
                # Missing 'aave_ltv_warning'
            }
        }
        
        with pytest.raises(KeyError, match="'aave_ltv_warning'"):
            RiskMonitor(incomplete_config)
        
        print("✅ Fail-fast behavior works with missing aave_ltv_warning")
    
    def test_fail_fast_with_missing_margin_warning_pct(self):
        """Test that RiskMonitor fails fast when margin_warning_pct is missing."""
        incomplete_config = {
            'strategy': {
                'target_ltv': 0.91,
                'rebalance_threshold_pct': 5.0
            },
            'risk': {
                'aave_ltv_warning': 0.85,
                'aave_ltv_critical': 0.90,
                'margin_critical_pct': 0.12
                # Missing 'margin_warning_pct'
            }
        }
        
        with pytest.raises(KeyError, match="'margin_warning_pct'"):
            RiskMonitor(incomplete_config)
        
        print("✅ Fail-fast behavior works with missing margin_warning_pct")
    
    def test_success_with_complete_config(self):
        """Test that RiskMonitor works with complete config."""
        complete_config = {
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
        
        risk_monitor = RiskMonitor(complete_config)
        
        # Verify all values are set correctly
        assert risk_monitor.aave_safe_ltv == 0.91
        assert risk_monitor.aave_ltv_warning == 0.85
        assert risk_monitor.aave_ltv_critical == 0.90
        assert risk_monitor.margin_warning_threshold == 0.20
        assert risk_monitor.margin_critical_threshold == 0.12
        assert risk_monitor.delta_threshold_pct == 5.0
        
        print("✅ Complete config works correctly")
    
    def test_no_default_values_used(self):
        """Test that no default values are used (fail-fast principle)."""
        # This test ensures that the RiskMonitor doesn't fall back to defaults
        # by checking that it fails when any required config is missing
        
        # Test with empty config
        with pytest.raises(KeyError):
            RiskMonitor({})
        
        # Test with None config
        with pytest.raises((KeyError, TypeError)):
            RiskMonitor(None)
        
        print("✅ No default values are used (fail-fast principle)")
    
    def test_config_values_are_exact(self):
        """Test that config values are used exactly as provided."""
        config = {
            'strategy': {
                'target_ltv': 0.95,  # Different from typical default
                'rebalance_threshold_pct': 3.0  # Different from typical default
            },
            'risk': {
                'aave_ltv_warning': 0.80,  # Different from typical default
                'aave_ltv_critical': 0.88,  # Different from typical default
                'margin_warning_pct': 0.15,  # Different from typical default
                'margin_critical_pct': 0.08  # Different from typical default
            }
        }
        
        risk_monitor = RiskMonitor(config)
        
        # Verify exact values are used (not defaults)
        assert risk_monitor.aave_safe_ltv == 0.95
        assert risk_monitor.aave_ltv_warning == 0.80
        assert risk_monitor.aave_ltv_critical == 0.88
        assert risk_monitor.margin_warning_threshold == 0.15
        assert risk_monitor.margin_critical_threshold == 0.08
        assert risk_monitor.delta_threshold_pct == 3.0
        
        print("✅ Config values are used exactly as provided")


if __name__ == "__main__":
    # Run tests
    test_instance = TestRiskMonitorFailFast()
    
    print("🧪 Testing RiskMonitor Fail-Fast Config Access...")
    
    try:
        test_instance.test_fail_fast_with_missing_risk_section()
        test_instance.test_fail_fast_with_missing_strategy_section()
        test_instance.test_fail_fast_with_missing_target_ltv()
        test_instance.test_fail_fast_with_missing_aave_ltv_warning()
        test_instance.test_fail_fast_with_missing_margin_warning_pct()
        test_instance.test_success_with_complete_config()
        test_instance.test_no_default_values_used()
        test_instance.test_config_values_are_exact()
        
        print("\n✅ All RiskMonitor fail-fast tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()