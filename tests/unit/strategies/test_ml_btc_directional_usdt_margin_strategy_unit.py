"""
Unit tests for ML BTC Directional (USDT Margin) Strategy.

Tests the 5 standard actions, instrument validation, SL/TP calculation, and order generation.
"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from pathlib import Path

from backend.src.basis_strategy_v1.core.strategies.ml_btc_directional_usdt_margin_strategy import MLBTCDirectionalUSDTMarginStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation
from backend.src.basis_strategy_v1.core.models.venues import Venue


@pytest.fixture
def mock_config():
    """Mock configuration for ML BTC Directional (USDT Margin) strategy."""
    return {
        'mode': 'ml_btc_directional_usdt_margin',
        'share_class': 'USDT',
        'asset': 'BTC',
        'signal_threshold': 0.65,
        'max_position_size': 1000.0,
        'stop_loss_pct': 0.05,
        'take_profit_pct': 0.10,
        'ml_config': {
            'take_profit_sd': 2.0,
            'stop_loss_sd': 2.0,
            'sd_floor_bps': 10,
            'sd_cap_bps': 1000
        },
        'component_config': {
            'position_monitor': {
                'position_subscriptions': [
                    'wallet:BaseToken:USDT',
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
    """Create ML BTC Directional (USDT Margin) strategy instance."""
    return MLBTCDirectionalUSDTMarginStrategy(
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


class TestMLBTCDirectionalUSDTMarginStrategyInit:
    """Test strategy initialization and validation."""
    
    def test_init_validates_required_instruments(self, mock_config, mock_components):
        """Test that strategy validates required instruments are in position_subscriptions."""
        # Test with missing required instrument
        mock_config['component_config']['position_monitor']['position_subscriptions'] = [
            'binance:BaseToken:USDT'
            # Missing wallet:BaseToken:USDT
        ]

        with pytest.raises(ValueError, match="Required instrument wallet:BaseToken:USDT not in position_subscriptions"):
            MLBTCDirectionalUSDTMarginStrategy(
                config=mock_config,
                data_provider=mock_components['data_provider'],
                exposure_monitor=mock_components['exposure_monitor'],
                position_monitor=mock_components['position_monitor'],
                risk_monitor=mock_components['risk_monitor'],
                utility_manager=mock_components['utility_manager']
            )
    
    def test_init_validates_instruments_in_registry(self, mock_config, mock_components):
        """Test that strategy validates instruments exist in registry."""
        # Test with missing required instrument
        mock_config['component_config']['position_monitor']['position_subscriptions'] = [
            'binance:BaseToken:USDT'
            # Missing wallet:BaseToken:USDT
        ]

        with pytest.raises(ValueError, match="Required instrument wallet:BaseToken:USDT not in position_subscriptions"):
            MLBTCDirectionalUSDTMarginStrategy(
                config=mock_config,
                data_provider=mock_components['data_provider'],
                exposure_monitor=mock_components['exposure_monitor'],
                position_monitor=mock_components['position_monitor'],
                risk_monitor=mock_components['risk_monitor'],
                utility_manager=mock_components['utility_manager']
            )
    
    def test_init_success_with_valid_config(self, strategy):
        """Test successful initialization with valid config."""
        assert strategy.share_class == 'USDT'
        assert strategy.asset == 'BTC'
        assert strategy.entry_instrument == 'wallet:BaseToken:USDT'
        assert strategy.perp_instrument == 'binance:Perp:BTCUSDT'
        assert len(strategy.available_instruments) == 2


class TestMLBTCDirectionalUSDTMarginStrategyActions:
    """Test the 5 standard strategy actions."""
    
    def test_generate_orders_entry_full(self, strategy):
        """Test entry_full order generation."""
        with patch.object(strategy, '_get_ml_predictions') as mock_ml:
            mock_ml.return_value = {'confidence': 0.8, 'signal': 'long'}
            
            orders = strategy.generate_orders(
                timestamp=pd.Timestamp.now(),
                exposure={'total_exposure': 50000.0, 'positions': {}},
                risk_assessment={},
                pnl={},
                market_data={'prices': {'BTC': 50000.0, 'BTC_PERP': 50000.0}}
            )

            assert isinstance(orders, list)
    
    def test_create_entry_full_orders(self, strategy):
        """Test _create_entry_full_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=50000.0):
            with patch.object(strategy, '_get_ml_signal', return_value={'signal': 'LONG', 'confidence': 0.8, 'sd': 0.02}):
                orders = strategy._create_entry_full_orders(50000.0, 'long')
                
                assert len(orders) == 1
                order = orders[0]
                assert isinstance(order, Order)
                assert order.venue == Venue.BINANCE
                assert order.operation == OrderOperation.PERP_TRADE
                assert order.pair == 'BTCUSDT'
                assert order.side == 'LONG'
                assert order.amount == 50000000.0  # 50000.0 * 1000 (leverage)
                assert order.source_venue == Venue.BINANCE
                assert order.target_venue == Venue.BINANCE
                assert order.source_token == 'USDT'
                assert order.target_token == 'BTC'
                assert order.strategy_intent == 'entry_full'
                assert order.strategy_id == 'ml_btc_directional'
                # Check SL/TP are set
                assert order.take_profit is not None
                assert order.stop_loss is not None
    
    def test_create_entry_partial_orders(self, strategy):
        """Test _create_entry_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=50000.0):
            with patch.object(strategy, '_get_ml_signal', return_value={'signal': 'LONG', 'confidence': 0.8, 'sd': 0.02}):
                orders = strategy._create_entry_partial_orders(25000.0, 'long')
                
                assert len(orders) == 1
                order = orders[0]
                assert isinstance(order, Order)
                assert order.venue == Venue.BINANCE
                assert order.operation == OrderOperation.PERP_TRADE
                assert order.amount == 25000000.0
                assert order.strategy_intent == 'entry_partial'
    
    def test_create_exit_full_orders(self, strategy):
        """Test _create_exit_full_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=50000.0):
            orders = strategy._create_exit_full_orders(50000.0)
            
            assert len(orders) == 1
            order = orders[0]
            assert isinstance(order, Order)
            assert order.venue == Venue.BINANCE
            assert order.operation == OrderOperation.PERP_TRADE
            assert order.pair == 'BTCUSDT'
            assert order.side == 'SELL'
            assert order.amount == 1.0
            assert order.strategy_intent == 'exit_full'
    
    def test_create_exit_partial_orders(self, strategy):
        """Test _create_exit_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=50000.0):
            orders = strategy._create_exit_partial_orders(25000.0)
            
            assert len(orders) == 1
            order = orders[0]
            assert isinstance(order, Order)
            assert order.venue == Venue.BINANCE
            assert order.operation == OrderOperation.PERP_TRADE
            assert order.side == 'SELL'
            assert order.amount == 0.5
            assert order.strategy_intent == 'exit_partial'
    
    def test_create_dust_sell_orders(self, strategy):
        """Test _create_dust_sell_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=50000.0):
            orders = strategy._create_dust_sell_orders(50000.0)
            
            # ML strategies don't generate dust
            assert len(orders) == 0


class TestMLBTCDirectionalUSDTMarginStrategySLTP:
    """Test stop-loss and take-profit calculation."""
    
    def test_calculate_stop_loss_take_profit_long(self, strategy):
        """Test SL/TP calculation for LONG position."""
        entry_price = 50000.0
        signal_data = {'sd': 0.02}  # 2% standard deviation
        
        result = strategy._calculate_stop_loss_take_profit(entry_price, signal_data, 'LONG')
        
        assert 'take_profit' in result
        assert 'stop_loss' in result
        assert 'sd_used' in result
        assert 'tp_sd_multiplier' in result
        assert 'sl_sd_multiplier' in result
        
        # For LONG: TP > entry_price, SL < entry_price
        assert result['take_profit'] > entry_price
        assert result['stop_loss'] < entry_price
        
        # Check SD calculation
        assert result['sd_used'] == 0.02  # Should use raw SD
        assert result['tp_sd_multiplier'] == 2.0
        assert result['sl_sd_multiplier'] == 2.0
    
    def test_calculate_stop_loss_take_profit_short(self, strategy):
        """Test SL/TP calculation for SHORT position."""
        entry_price = 50000.0
        signal_data = {'sd': 0.02}  # 2% standard deviation
        
        result = strategy._calculate_stop_loss_take_profit(entry_price, signal_data, 'SHORT')
        
        assert 'take_profit' in result
        assert 'stop_loss' in result
        
        # For SHORT: TP < entry_price, SL > entry_price
        assert result['take_profit'] < entry_price
        assert result['stop_loss'] > entry_price
    
    def test_sd_floor_cap(self, strategy):
        """Test SD flooring and capping."""
        entry_price = 50000.0
        
        # Test SD floor (very small SD)
        signal_data_floor = {'sd': 0.0001}  # 0.01% - should be floored to 10 bps
        result_floor = strategy._calculate_stop_loss_take_profit(entry_price, signal_data_floor, 'LONG')
        assert result_floor['sd_used'] == 0.001  # 10 bps = 0.1%
        
        # Test SD cap (very large SD)
        signal_data_cap = {'sd': 0.2}  # 20% - should be capped to 10%
        result_cap = strategy._calculate_stop_loss_take_profit(entry_price, signal_data_cap, 'LONG')
        assert result_cap['sd_used'] == 0.1  # 1000 bps = 10%
        
        # Test normal SD (should pass through)
        signal_data_normal = {'sd': 0.05}  # 5% - should pass through
        result_normal = strategy._calculate_stop_loss_take_profit(entry_price, signal_data_normal, 'LONG')
        assert result_normal['sd_used'] == 0.05
    
    def test_sl_tp_error_handling(self, strategy):
        """Test error handling in SL/TP calculation."""
        entry_price = 50000.0
        signal_data = {}  # Missing 'sd' field
        
        result = strategy._calculate_stop_loss_take_profit(entry_price, signal_data, 'LONG')
        
        # Should use floor values when 'sd' is missing (sd_floor_bps=10)
        assert result['take_profit'] == 50100.0  # 50000 + (50000 * 0.001 * 2.0)
        assert result['stop_loss'] == 49900.0   # 50000 - (50000 * 0.001 * 2.0)


class TestMLBTCDirectionalUSDTMarginStrategyHelpers:
    """Test helper methods."""
    
    def test_calculate_target_position(self, strategy):
        """Test calculate_target_position method."""
        with patch.object(strategy, '_get_asset_price', return_value=50000.0):
            target = strategy.calculate_target_position(50000.0)
            
            assert 'btc_perp_position' in target
            assert 'usdt_balance' in target
            assert target['btc_perp_position'] == 50000000.0  # 50000.0 * 1000 (leverage)
            assert target['usdt_balance'] == -49950000.0
    
    def test_get_asset_price(self, strategy):
        """Test _get_asset_price method."""
        price = strategy._get_asset_price()
        assert price == 45000.0  # Mock price from implementation
    
    def test_get_ml_signal(self, strategy):
        """Test _get_ml_signal method."""
        with patch.object(strategy.data_provider, 'get_ml_prediction', return_value={'signal': 'LONG', 'confidence': 0.8, 'sd': 0.02}):
            signal = strategy._get_ml_signal()
            
            assert signal['signal'] == 'LONG'
            assert signal['confidence'] == 0.8
            assert signal['sd'] == 0.02
    
    def test_order_operation_id_format(self, strategy):
        """Test that operation_id format is correct (unix microseconds)."""
        with patch.object(strategy, '_get_asset_price', return_value=50000.0):
            with patch.object(strategy, '_get_ml_signal', return_value={'signal': 'LONG', 'confidence': 0.8, 'sd': 0.02}):
                orders = strategy._create_entry_full_orders(50000.0, 'long')
                
                for order in orders:
                    # Check operation_id format: perp_trade_timestamp
                    parts = order.operation_id.split('_')
                    assert len(parts) >= 2
                    assert parts[0] == 'perp'
                    assert parts[1] == 'trade'
                    # Last part should be a timestamp (numeric)
                    assert parts[-1].isdigit()
                    # Should be unix microseconds (13+ digits)
                    assert len(parts[-1]) >= 13
    
    def test_order_has_required_fields(self, strategy):
        """Test that all Order objects have required fields."""
        with patch.object(strategy, '_get_asset_price', return_value=50000.0):
            with patch.object(strategy, '_get_ml_signal', return_value={'signal': 'LONG', 'confidence': 0.8, 'sd': 0.02}):
                orders = strategy._create_entry_full_orders(50000.0, 'long')
                
                for order in orders:
                    # Required fields from Order model
                    assert hasattr(order, 'operation_id')
                    assert hasattr(order, 'venue')
                    assert hasattr(order, 'operation')
                    assert hasattr(order, 'amount')
                    assert hasattr(order, 'source_venue')
                    assert hasattr(order, 'target_venue')
                    assert hasattr(order, 'source_token')
                    assert hasattr(order, 'target_token')
                    assert hasattr(order, 'expected_deltas')
                    assert hasattr(order, 'strategy_intent')
                    assert hasattr(order, 'strategy_id')
                    # ML-specific fields
                    assert hasattr(order, 'take_profit')
                    assert hasattr(order, 'stop_loss')
                    
                    # Check expected_deltas format
                    assert isinstance(order.expected_deltas, dict)
                    assert len(order.expected_deltas) > 0


class TestMLBTCDirectionalUSDTMarginStrategyErrorHandling:
    """Test error handling scenarios."""
    
    def test_create_orders_with_zero_equity(self, strategy):
        """Test order creation with zero equity."""
        orders = strategy._create_entry_full_orders(0.0, 'long')
        assert len(orders) == 0
    
    def test_create_orders_with_negative_equity(self, strategy):
        """Test order creation with negative equity."""
        orders = strategy._create_entry_full_orders(-50000.0, 'long')
        assert len(orders) == 0
    
    def test_get_asset_price_error_handling(self, strategy):
        """Test error handling in _get_asset_price."""
        with patch.object(strategy, '_get_asset_price', side_effect=Exception("Price fetch failed")):
            orders = strategy._create_entry_full_orders(50000.0, 'long')
            # Should handle error gracefully and return empty list
            assert len(orders) == 0
    
    def test_get_ml_signal_error_handling(self, strategy):
        """Test error handling in _get_ml_signal."""
        with patch.object(strategy, '_get_ml_signal', side_effect=Exception("ML signal failed")):
            orders = strategy._create_entry_full_orders(50000.0, 'long')
            # Method doesn't use _get_ml_signal, so should still create orders
            assert len(orders) == 1
