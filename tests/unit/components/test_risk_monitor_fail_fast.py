#!/usr/bin/env python3
"""
Test RiskMonitor fail-fast config access (no .get() defaults).
"""

import pytest
import sys
import os

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from basis_strategy_v1.core.strategies.components.risk_monitor import RiskMonitor


class TestRiskMonitorFailFast:
    """Test RiskMonitor fail-fast config access."""
    
    def test_fail_fast_with_missing_target_ltv(self):
        """Test that RiskMonitor fails fast when target_ltv is missing."""
        incomplete_config = {
            'max_drawdown': 0.1,
            'leverage_enabled': False,
            'venues': {'aave': {'max_leverage': 1.0}}
            # Missing 'target_ltv'
        }
        
        with pytest.raises(KeyError, match="Missing required configuration: target_ltv"):
            RiskMonitor(incomplete_config, None, None)
        
        print("✅ Fail-fast behavior works with missing target_ltv")
    
    def test_fail_fast_with_missing_max_drawdown(self):
        """Test that RiskMonitor fails fast when max_drawdown is missing."""
        incomplete_config = {
            'target_ltv': 0.8,
            'leverage_enabled': False,
            'venues': {'aave': {'max_leverage': 1.0}}
            # Missing 'max_drawdown'
        }
        
        with pytest.raises(KeyError, match="Missing required configuration: max_drawdown"):
            RiskMonitor(incomplete_config, None, None)
        
        print("✅ Fail-fast behavior works with missing max_drawdown")
    
    def test_fail_fast_with_missing_leverage_enabled(self):
        """Test that RiskMonitor fails fast when leverage_enabled is missing."""
        incomplete_config = {
            'target_ltv': 0.8,
            'max_drawdown': 0.1,
            'venues': {'aave': {'max_leverage': 1.0}}
            # Missing 'leverage_enabled'
        }
        
        with pytest.raises(KeyError, match="Missing required configuration: leverage_enabled"):
            RiskMonitor(incomplete_config, None, None)
        
        print("✅ Fail-fast behavior works with missing leverage_enabled")
    
    def test_fail_fast_with_missing_venues(self):
        """Test that RiskMonitor fails fast when venues is missing."""
        incomplete_config = {
            'target_ltv': 0.8,
            'max_drawdown': 0.1,
            'leverage_enabled': False
            # Missing 'venues'
        }
        
        with pytest.raises(KeyError, match="Missing required configuration: venues"):
            RiskMonitor(incomplete_config, None, None)
        
        print("✅ Fail-fast behavior works with missing venues")
    
    def test_fail_fast_with_invalid_venue_config(self):
        """Test that RiskMonitor fails fast when venue config is invalid."""
        incomplete_config = {
            'target_ltv': 0.8,
            'max_drawdown': 0.1,
            'leverage_enabled': False,
            'venues': {
                'aave': 'invalid_config'  # Should be dict, not string
            }
        }
        
        with pytest.raises(KeyError, match="Invalid venue configuration for aave"):
            RiskMonitor(incomplete_config, None, None)
        
        print("✅ Fail-fast behavior works with invalid venue config")
    
    def test_fail_fast_with_missing_venue_max_leverage(self):
        """Test that RiskMonitor fails fast when venue max_leverage is missing."""
        incomplete_config = {
            'target_ltv': 0.8,
            'max_drawdown': 0.1,
            'leverage_enabled': False,
            'venues': {
                'aave': {}  # Missing max_leverage
            }
        }
        
        with pytest.raises(KeyError, match="Missing max_leverage in venue configuration for aave"):
            RiskMonitor(incomplete_config, None, None)
        
        print("✅ Fail-fast behavior works with missing venue max_leverage")
    
    def test_success_with_complete_config(self):
        """Test that RiskMonitor works with complete config."""
        complete_config = {
            'target_ltv': 0.8,
            'max_drawdown': 0.1,
            'leverage_enabled': False,
            'venues': {
                'aave': {'max_leverage': 1.0},
                'binance': {'max_leverage': 2.0}
            }
        }
        
        risk_monitor = RiskMonitor(complete_config, None, None)
        
        # Verify config is stored correctly
        assert risk_monitor.config == complete_config
        
        print("✅ Complete config works correctly")
    
    def test_no_default_values_used(self):
        """Test that no default values are used (fail-fast principle)."""
        # This test ensures that the RiskMonitor doesn't fall back to defaults
        # by checking that it fails when any required config is missing
        
        # Test with empty config
        with pytest.raises(KeyError):
            RiskMonitor({}, None, None)
        
        # Test with None config
        with pytest.raises((KeyError, TypeError)):
            RiskMonitor(None, None, None)
        
        print("✅ No default values are used (fail-fast principle)")
    
    def test_config_values_are_exact(self):
        """Test that config values are used exactly as provided."""
        config = {
            'target_ltv': 0.95,  # Different from typical default
            'max_drawdown': 0.05,  # Different from typical default
            'leverage_enabled': True,  # Different from typical default
            'venues': {
                'aave': {'max_leverage': 1.5},  # Different from typical default
                'binance': {'max_leverage': 3.0}  # Different from typical default
            }
        }
        
        risk_monitor = RiskMonitor(config, None, None)
        
        # Verify exact values are used (not defaults)
        assert risk_monitor.config == config
        
        print("✅ Config values are used exactly as provided")


if __name__ == "__main__":
    # Run tests
    test_instance = TestRiskMonitorFailFast()
    
    print("🧪 Testing RiskMonitor Fail-Fast Config Access...")
    
    try:
        test_instance.test_fail_fast_with_missing_target_ltv()
        test_instance.test_fail_fast_with_missing_max_drawdown()
        test_instance.test_fail_fast_with_missing_leverage_enabled()
        test_instance.test_fail_fast_with_missing_venues()
        test_instance.test_fail_fast_with_invalid_venue_config()
        test_instance.test_fail_fast_with_missing_venue_max_leverage()
        test_instance.test_success_with_complete_config()
        test_instance.test_no_default_values_used()
        test_instance.test_config_values_are_exact()
        
        print("\n✅ All RiskMonitor fail-fast tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()