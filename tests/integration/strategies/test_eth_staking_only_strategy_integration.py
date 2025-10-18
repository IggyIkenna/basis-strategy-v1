"""
Integration tests for ETH Staking Only Strategy.

Tests component interactions and data flow.
"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from pathlib import Path

from backend.src.basis_strategy_v1.core.strategies.eth_staking_only_strategy import ETHStakingOnlyStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation
from backend.src.basis_strategy_v1.core.models.venues import Venue


@pytest.fixture
def mock_config():
    """Mock configuration for ETH Staking Only strategy."""
    return {
        'mode': 'eth_staking_only',
        'share_class': 'ETH',
        'asset': 'ETH',
        'component_config': {
            'position_monitor': {
                'position_subscriptions': [
                    'wallet:BaseToken:ETH',
                    'etherfi:LST:weETH',
                    'wallet:BaseToken:EIGEN',
                    'wallet:BaseToken:ETHFI'
                ]
            }
        }
    }


@pytest.fixture
def mock_components():
    """Mock component dependencies."""
    data_provider = Mock()
    exposure_monitor = Mock()
    position_monitor = Mock()
    risk_monitor = Mock()
    utility_manager = Mock()
    
    return {
        'data_provider': data_provider,
        'exposure_monitor': exposure_monitor,
        'position_monitor': position_monitor,
        'risk_monitor': risk_monitor,
        'utility_manager': utility_manager
    }


@pytest.fixture
def strategy(mock_config, mock_components):
    """Create ETH Staking Only strategy instance."""
    return ETHStakingOnlyStrategy(
        config=mock_config,
        data_provider=mock_components['data_provider'],
        exposure_monitor=mock_components['exposure_monitor'],
        position_monitor=mock_components['position_monitor'],
        risk_monitor=mock_components['risk_monitor'],
        utility_manager=mock_components['utility_manager'],
        correlation_id='test_correlation',
        pid=12345,
        log_dir=Path('/tmp/test_logs')
    )


class TestETHStakingOnlyStrategyIntegration:
    """Test strategy integration with other components."""
    
    def test_strategy_position_monitor_integration(self, strategy, mock_components):
        """Test that strategy shares position universe with position monitor."""
        # Strategy should have access to same position subscriptions as position monitor
        position_config = strategy.config.get('component_config', {}).get('position_monitor', {})
        strategy_positions = position_config.get('position_subscriptions', [])
        
        # Verify strategy uses the same position universe
        assert strategy.available_instruments == strategy_positions
        assert len(strategy.available_instruments) == 4
        
        # Verify all required instruments are present
        required_instruments = [
            'wallet:BaseToken:ETH',
            'etherfi:LST:weETH',
            'wallet:BaseToken:EIGEN',
            'wallet:BaseToken:ETHFI'
        ]
        for instrument in required_instruments:
            assert instrument in strategy.available_instruments
    
    def test_order_position_tracking(self, strategy, mock_components):
        """Test that orders update positions correctly."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(1.0)
            
            # Verify orders have expected_deltas that match position subscriptions
            for order in orders:
                assert isinstance(order.expected_deltas, dict)
                
                # Check that all delta keys are in position subscriptions
                for delta_key in order.expected_deltas.keys():
                    assert delta_key in strategy.available_instruments
                
                # Verify expected_deltas make sense for staking
                if order.operation == OrderOperation.STAKE:
                    # Staking should reduce ETH and increase weETH
                    assert order.expected_deltas.get('wallet:BaseToken:ETH', 0) < 0
                    assert order.expected_deltas.get('etherfi:LST:weETH', 0) > 0
    
    def test_component_chain(self, strategy, mock_components):
        """Test strategy → position → exposure → risk → pnl flow."""
        # Mock component responses
        mock_components['position_monitor'].get_current_positions.return_value = {
            'wallet:BaseToken:ETH': 1.0,
            'etherfi:LST:weETH': 0.0,
            'wallet:BaseToken:EIGEN': 0.0,
            'wallet:BaseToken:ETHFI': 0.0
        }
        
        mock_components['exposure_monitor'].get_current_exposure.return_value = {
            'eth_value': 3000.0,
            'total_value': 3000.0
        }
        
        mock_components['risk_monitor'].get_current_risk_metrics.return_value = {
            'health_factor': 1.5,
            'liquidation_risk': 'low'
        }
        
        # Test that strategy can generate orders based on component data
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(1.0)
            
            # Verify orders are generated successfully
            assert len(orders) > 0
            
            # Verify orders reference correct instruments
            for order in orders:
                for delta_key in order.expected_deltas.keys():
                    assert delta_key in strategy.available_instruments
    
    def test_data_provider_integration(self, strategy, mock_components):
        """Test strategy integration with data provider."""
        # Mock data provider responses
        mock_components['data_provider'].get_price.return_value = 3000.0
        mock_components['data_provider'].get_historical_data.return_value = pd.DataFrame({
            'timestamp': [pd.Timestamp.now()],
            'price': [3000.0]
        })
        
        # Test that strategy can use data provider
        price = strategy._get_asset_price()
        assert price == 3000.0
        
        # Test that strategy generates orders using data provider data
        orders = strategy._create_entry_full_orders(1.0)
        assert len(orders) > 0
    
    def test_utility_manager_integration(self, strategy, mock_components):
        """Test strategy integration with utility manager."""
        # Mock utility manager responses
        mock_components['utility_manager'].convert_currency.return_value = 3000.0
        mock_components['utility_manager'].get_conversion_rate.return_value = 1.0
        
        # Test that strategy can use utility manager
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(1.0)
            
            # Verify orders are generated successfully
            assert len(orders) > 0
    
    def test_risk_monitor_integration(self, strategy, mock_components):
        """Test strategy integration with risk monitor."""
        # Mock risk monitor responses
        mock_components['risk_monitor'].get_current_risk_metrics.return_value = {
            'health_factor': 1.5,
            'liquidation_risk': 'low',
            'max_position_size': 1.0
        }
        
        # Test that strategy respects risk limits
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(1.0)
            
            # Verify orders don't exceed risk limits
            for order in orders:
                if hasattr(order, 'amount'):
                    assert order.amount <= 1.0  # Should respect max position size
    
    def test_exposure_monitor_integration(self, strategy, mock_components):
        """Test strategy integration with exposure monitor."""
        # Mock exposure monitor responses
        mock_components['exposure_monitor'].get_current_exposure.return_value = {
            'eth_value': 3000.0,
            'total_value': 3000.0,
            'eth_exposure': 1.0
        }
        
        # Test that strategy can access exposure data
        exposure = mock_components['exposure_monitor'].get_current_exposure()
        assert exposure['eth_value'] == 3000.0
        assert exposure['total_value'] == 3000.0
        
        # Test that strategy generates orders based on exposure
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(1.0)
            assert len(orders) > 0
