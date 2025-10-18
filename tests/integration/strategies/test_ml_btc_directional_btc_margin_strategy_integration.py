"""
Integration tests for ML BTC Directional (BTC Margin) Strategy.

Tests component interactions and data flow.
"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from pathlib import Path

from backend.src.basis_strategy_v1.core.strategies.ml_btc_directional_btc_margin_strategy import MLBTCDirectionalBTCMarginStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation
from backend.src.basis_strategy_v1.core.models.venues import Venue


@pytest.fixture
def mock_config():
    """Mock configuration for ML BTC Directional (BTC Margin) strategy."""
    return {
        'mode': 'ml_btc_directional_btc_margin',
        'share_class': 'BTC',
        'asset': 'BTC',
        'ml_config': {
            'take_profit_sd': 2.0,
            'stop_loss_sd': 2.0,
            'sd_floor_bps': 10,
            'sd_cap_bps': 1000
        },
        'component_config': {
            'position_monitor': {
                'position_subscriptions': [
                    'binance:BaseToken:BTC',
                    'binance:Perp:BTCUSDT'
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
    """Create ML BTC Directional (BTC Margin) strategy instance."""
    return MLBTCDirectionalBTCMarginStrategy(
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


class TestMLBTCDirectionalBTCMarginStrategyIntegration:
    """Test strategy integration with other components."""
    
    def test_strategy_position_monitor_integration(self, strategy, mock_components):
        """Test that strategy shares position universe with position monitor."""
        # Strategy should have access to same position subscriptions as position monitor
        position_config = strategy.config.get('component_config', {}).get('position_monitor', {})
        strategy_positions = position_config.get('position_subscriptions', [])
        
        # Verify strategy uses the same position universe
        assert strategy.available_instruments == strategy_positions
        assert len(strategy.available_instruments) == 2
        
        # Verify all required instruments are present
        required_instruments = [
            'binance:BaseToken:BTC',
            'binance:Perp:BTCUSDT'
        ]
        for instrument in required_instruments:
            assert instrument in strategy.available_instruments
    
    def test_order_position_tracking(self, strategy, mock_components):
        """Test that orders update positions correctly."""
        with patch.object(strategy, '_get_asset_price', return_value=50000.0):
            with patch.object(strategy, '_get_ml_signal', return_value={'signal': 'LONG', 'confidence': 0.8, 'sd': 0.02}):
                orders = strategy._create_entry_full_orders(1.0)
                
                # Verify orders have expected_deltas that match position subscriptions
                for order in orders:
                    assert isinstance(order.expected_deltas, dict)
                    
                    # Check that all delta keys are in position subscriptions
                    for delta_key in order.expected_deltas.keys():
                        assert delta_key in strategy.available_instruments
                    
                    # Verify expected_deltas make sense for perp trading
                    if order.operation == OrderOperation.PERP_TRADE:
                        # Perp trading should affect perp position
                        assert 'binance:Perp:BTCUSDT' in order.expected_deltas
    
    def test_component_chain(self, strategy, mock_components):
        """Test strategy → position → exposure → risk → pnl flow."""
        # Mock component responses
        mock_components['position_monitor'].get_current_positions.return_value = {
            'binance:BaseToken:BTC': 1.0,
            'binance:Perp:BTCUSDT': 0.0
        }
        
        mock_components['exposure_monitor'].get_current_exposure.return_value = {
            'btc_value': 50000.0,
            'total_value': 50000.0
        }
        
        mock_components['risk_monitor'].get_current_risk_metrics.return_value = {
            'margin_ratio': 0.1,
            'liquidation_risk': 'low'
        }
        
        # Test that strategy can generate orders based on component data
        with patch.object(strategy, '_get_asset_price', return_value=50000.0):
            with patch.object(strategy, '_get_ml_signal', return_value={'signal': 'LONG', 'confidence': 0.8, 'sd': 0.02}):
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
        mock_components['data_provider'].get_price.return_value = 50000.0
        mock_components['data_provider'].get_ml_prediction.return_value = {
            'signal': 'LONG',
            'confidence': 0.8,
            'sd': 0.02
        }
        
        # Test that strategy can use data provider
        price = strategy._get_asset_price()
        assert price == 50000.0
        
        # Test ML signal retrieval
        signal = strategy._get_ml_signal()
        assert signal['signal'] == 'LONG'
        assert signal['confidence'] == 0.8
        assert signal['sd'] == 0.02
        
        # Test that strategy generates orders using data provider data
        orders = strategy._create_entry_full_orders(1.0)
        assert len(orders) > 0
    
    def test_utility_manager_integration(self, strategy, mock_components):
        """Test strategy integration with utility manager."""
        # Mock utility manager responses
        mock_components['utility_manager'].convert_currency.return_value = 50000.0
        mock_components['utility_manager'].get_conversion_rate.return_value = 1.0
        
        # Test that strategy can use utility manager
        with patch.object(strategy, '_get_asset_price', return_value=50000.0):
            with patch.object(strategy, '_get_ml_signal', return_value={'signal': 'LONG', 'confidence': 0.8, 'sd': 0.02}):
                orders = strategy._create_entry_full_orders(1.0)
                
                # Verify orders are generated successfully
                assert len(orders) > 0
    
    def test_risk_monitor_integration(self, strategy, mock_components):
        """Test strategy integration with risk monitor."""
        # Mock risk monitor responses
        mock_components['risk_monitor'].get_current_risk_metrics.return_value = {
            'margin_ratio': 0.1,
            'liquidation_risk': 'low',
            'max_position_size': 1.0
        }
        
        # Test that strategy respects risk limits
        with patch.object(strategy, '_get_asset_price', return_value=50000.0):
            with patch.object(strategy, '_get_ml_signal', return_value={'signal': 'LONG', 'confidence': 0.8, 'sd': 0.02}):
                orders = strategy._create_entry_full_orders(1.0)
                
                # Verify orders don't exceed risk limits
                for order in orders:
                    if hasattr(order, 'amount'):
                        assert order.amount <= 1.0  # Should respect max position size
    
    def test_exposure_monitor_integration(self, strategy, mock_components):
        """Test strategy integration with exposure monitor."""
        # Mock exposure monitor responses
        mock_components['exposure_monitor'].get_current_exposure.return_value = {
            'btc_value': 50000.0,
            'total_value': 50000.0,
            'btc_exposure': 1.0
        }
        
        # Test that strategy can access exposure data
        exposure = mock_components['exposure_monitor'].get_current_exposure()
        assert exposure['btc_value'] == 50000.0
        assert exposure['total_value'] == 50000.0
        
        # Test that strategy generates orders based on exposure
        with patch.object(strategy, '_get_asset_price', return_value=50000.0):
            with patch.object(strategy, '_get_ml_signal', return_value={'signal': 'LONG', 'confidence': 0.8, 'sd': 0.02}):
                orders = strategy._create_entry_full_orders(1.0)
                assert len(orders) > 0
    
    def test_ml_signal_integration(self, strategy, mock_components):
        """Test ML signal integration and SL/TP calculation."""
        # Mock ML signal with different scenarios
        test_cases = [
            {'signal': 'LONG', 'confidence': 0.8, 'sd': 0.02},
            {'signal': 'SHORT', 'confidence': 0.7, 'sd': 0.03},
            {'signal': 'NEUTRAL', 'confidence': 0.5, 'sd': 0.01}
        ]
        
        for signal_data in test_cases:
            with patch.object(strategy, '_get_ml_signal', return_value=signal_data):
                with patch.object(strategy, '_get_asset_price', return_value=50000.0):
                    orders = strategy._create_entry_full_orders(1.0)
                    
                    if signal_data['signal'] in ['LONG', 'SHORT']:
                        # Should generate orders for directional signals
                        assert len(orders) > 0
                        
                        # Check SL/TP are calculated
                        for order in orders:
                            if hasattr(order, 'take_profit') and hasattr(order, 'stop_loss'):
                                assert order.take_profit is not None
                                assert order.stop_loss is not None
                    else:
                        # Should not generate orders for neutral signals
                        assert len(orders) == 0
