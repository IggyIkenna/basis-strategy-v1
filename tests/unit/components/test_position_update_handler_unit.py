"""
Unit tests for Position Update Handler component.

Tests the position update handler that orchestrates the tight loop between
position monitor updates and downstream components, replacing the old
reconciliation component functionality.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from backend.src.basis_strategy_v1.core.components.position_update_handler import PositionUpdateHandler


class TestPositionUpdateHandler:
    """Test Position Update Handler component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return {
            "mode": "pure_lending_usdt",
            "component_config": {
                "position_monitor": {
                    "position_subscriptions": ["aave_v3:lending:USDT", "morpho:lending:USDT"]
                }
            }
        }
    
    @pytest.fixture
    def mock_data_provider(self):
        """Mock data provider."""
        return Mock()
    
    @pytest.fixture
    def mock_position_monitor(self):
        """Mock position monitor."""
        monitor = Mock()
        monitor.get_current_positions.return_value = {
            "aave_v3:lending:USDT": {"balance": 1000.0, "value_usd": 1000.0}
        }
        return monitor
    
    @pytest.fixture
    def mock_exposure_monitor(self):
        """Mock exposure monitor."""
        monitor = Mock()
        monitor.calculate_exposure.return_value = {
            "total_exposure_usd": 1000.0,
            "asset_exposures": {"USDT": 1000.0}
        }
        return monitor
    
    @pytest.fixture
    def mock_risk_monitor(self):
        """Mock risk monitor."""
        monitor = Mock()
        monitor.assess_risk.return_value = {
            "risk_score": 0.1,
            "risk_factors": {"liquidity_risk": 0.05}
        }
        return monitor
    
    @pytest.fixture
    def mock_pnl_monitor(self):
        """Mock P&L monitor."""
        monitor = Mock()
        monitor.get_current_pnl.return_value = {
            "total_pnl_usd": 50.0,
            "pnl_breakdown": {"lending_yield": 50.0}
        }
        return monitor
    
    @pytest.fixture
    def position_update_handler(
        self, 
        mock_config, 
        mock_data_provider, 
        mock_position_monitor,
        mock_exposure_monitor,
        mock_risk_monitor,
        mock_pnl_monitor
    ):
        """Create position update handler with mocked dependencies."""
        return PositionUpdateHandler(
            config=mock_config,
            data_provider=mock_data_provider,
            execution_mode="backtest",
            position_monitor=mock_position_monitor,
            exposure_monitor=mock_exposure_monitor,
            risk_monitor=mock_risk_monitor,
            pnl_monitor=mock_pnl_monitor
        )
    
    def test_initialization(self, position_update_handler, mock_config):
        """Test position update handler initialization."""
        assert position_update_handler.config == mock_config
        assert position_update_handler.execution_mode == "backtest"
        assert position_update_handler.tight_loop_active is False
        assert position_update_handler.loop_execution_count == 0
    
    def test_handle_position_update_backtest_mode(self, position_update_handler):
        """Test position update handling in backtest mode."""
        timestamp = pd.Timestamp.now()
        changes = {"aave_v3:lending:USDT": {"balance": 1000.0}}
        market_data = {"usdt_price": 1.0}
        
        result = position_update_handler.handle_position_update(
            changes=changes,
            timestamp=timestamp,
            market_data=market_data,
            trigger_component="execution_manager"
        )
        
        # Verify position monitor was updated
        position_update_handler.position_monitor.update_state.assert_called_once_with(
            timestamp, 'execution_manager', changes
        )
        
        # Verify exposure monitor was called
        position_update_handler.exposure_monitor.calculate_exposure.assert_called_once()
        
        # Verify risk monitor was called
        position_update_handler.risk_monitor.assess_risk.assert_called_once()
        
        # Verify P&L monitor was called
        position_update_handler.pnl_monitor.get_current_pnl.assert_called_once()
        
        # Verify result structure
        assert "exposure" in result
        assert "risk" in result
        assert "pnl" in result
        assert position_update_handler.tight_loop_active is False
    
    def test_handle_position_update_live_mode(self, position_update_handler):
        """Test position update handling in live mode."""
        position_update_handler.execution_mode = "live"
        timestamp = pd.Timestamp.now()
        market_data = {"usdt_price": 1.0}
        
        result = position_update_handler.handle_position_update(
            changes=None,  # Live mode doesn't use changes
            timestamp=timestamp,
            market_data=market_data,
            trigger_component="position_refresh"
        )
        
        # Verify position monitor was refreshed (not updated with changes)
        position_update_handler.position_monitor.update_state.assert_called_once_with(
            timestamp, 'position_refresh', None
        )
        
        # Verify other components were called
        position_update_handler.exposure_monitor.calculate_exposure.assert_called_once()
        position_update_handler.risk_monitor.assess_risk.assert_called_once()
        position_update_handler.pnl_monitor.get_current_pnl.assert_called_once()
        
        assert "exposure" in result
        assert "risk" in result
        assert "pnl" in result
    
    def test_handle_position_update_error_handling(self, position_update_handler):
        """Test error handling in position update."""
        timestamp = pd.Timestamp.now()
        
        # Make position monitor raise an error
        position_update_handler.position_monitor.update_state.side_effect = Exception("Position update failed")
        
        with pytest.raises(Exception, match="Position update failed"):
            position_update_handler.handle_position_update(
                changes={},
                timestamp=timestamp,
                trigger_component="execution_manager"
            )
        
        # Verify tight loop was reset on error
        assert position_update_handler.tight_loop_active is False
    
    def test_check_component_health(self, position_update_handler):
        """Test component health check."""
        health = position_update_handler.check_component_health()
        
        assert "component" in health
        assert "status" in health
        assert health["component"] == "PositionUpdateHandler"
    
    def test_singleton_pattern(self, mock_config, mock_data_provider):
        """Test that PositionUpdateHandler follows singleton pattern."""
        # Create first instance
        handler1 = PositionUpdateHandler(
            config=mock_config,
            data_provider=mock_data_provider,
            execution_mode="backtest",
            position_monitor=Mock(),
            exposure_monitor=Mock(),
            risk_monitor=Mock(),
            pnl_monitor=Mock()
        )
        
        # Create second instance
        handler2 = PositionUpdateHandler(
            config=mock_config,
            data_provider=mock_data_provider,
            execution_mode="backtest",
            position_monitor=Mock(),
            exposure_monitor=Mock(),
            risk_monitor=Mock(),
            pnl_monitor=Mock()
        )
        
        # Should be the same instance
        assert handler1 is handler2
    
    def test_position_subscriptions_from_config(self, position_update_handler):
        """Test that position subscriptions are loaded from config."""
        expected_subscriptions = ["aave_v3:lending:USDT", "morpho:lending:USDT"]
        assert position_update_handler.position_subscriptions == expected_subscriptions
    
    def test_tight_loop_state_management(self, position_update_handler):
        """Test tight loop state management."""
        timestamp = pd.Timestamp.now()
        
        # Initially not active
        assert position_update_handler.tight_loop_active is False
        
        # After successful update, should be reset
        position_update_handler.handle_position_update(
            changes={},
            timestamp=timestamp,
            trigger_component="execution_manager"
        )
        
        assert position_update_handler.tight_loop_active is False
        assert position_update_handler.loop_execution_count == 1

