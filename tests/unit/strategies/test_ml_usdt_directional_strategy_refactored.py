"""
Unit tests for refactored MLUSDTDirectionalStrategy using Order model.

Tests the new Order-based interface instead of StrategyAction.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock

from backend.src.basis_strategy_v1.core.strategies.ml_usdt_directional_strategy import MLUSDTDirectionalStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation


class TestMLUSDTDirectionalStrategyRefactored:
    """Test refactored MLUSDTDirectionalStrategy with Order model."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for strategy."""
        risk_monitor = Mock()
        position_monitor = Mock()
        event_engine = Mock()
        data_provider = Mock()
        
        return risk_monitor, position_monitor, event_engine, data_provider
    
    @pytest.fixture
    def strategy_config(self):
        """Create strategy configuration."""
        return {
            'share_class': 'USDT',
            'asset': 'USDT',
            'signal_threshold': 0.70,
            'max_position_size': 1.0,
            'stop_loss_pct': 0.03,
            'take_profit_pct': 0.10
        }
    
    @pytest.fixture
    def strategy(self, strategy_config, mock_dependencies):
        """Create MLUSDTDirectionalStrategy instance."""
        risk_monitor, position_monitor, event_engine, data_provider = mock_dependencies
        return MLUSDTDirectionalStrategy(strategy_config, risk_monitor, position_monitor, event_engine, data_provider)
    
    def test_make_strategy_decision_no_ml_predictions(self, strategy):
        """Test strategy decision when no ML predictions available."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00')
        market_data = {}
        exposure_data = {'total_exposure': 10000.0, 'positions': {}}
        risk_assessment = {}
        
        # Mock no ML predictions
        strategy.data_provider.get_ml_predictions.return_value = None
        
        orders = strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return dust sell orders (empty since no dust)
        assert isinstance(orders, list)
        assert len(orders) == 0
    
    def test_make_strategy_decision_long_signal(self, strategy):
        """Test strategy decision with long signal."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00')
        market_data = {'prices': {'USDT': 1.0}}
        exposure_data = {'total_exposure': 10000.0, 'positions': {}}
        risk_assessment = {}
        
        # Mock ML predictions for long signal
        strategy.data_provider.get_ml_predictions.return_value = {
            'signal': 'long',
            'confidence': 0.8,
            'sd': 0.02
        }
        
        orders = strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return entry full orders
        assert isinstance(orders, list)
        assert len(orders) == 1
        
        order = orders[0]
        assert isinstance(order, Order)
        assert order.venue == 'binance'
        assert order.operation == OrderOperation.PERP_TRADE
        assert order.pair == 'USDTUSDT'
        assert order.side == 'LONG'
        assert order.strategy_intent == 'entry_full'
        assert order.strategy_id == 'ml_usdt_directional'
        assert order.take_profit is not None
        assert order.stop_loss is not None
        assert order.metadata['ml_signal'] == 'long'
    
    def test_make_strategy_decision_short_signal(self, strategy):
        """Test strategy decision with short signal."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00')
        market_data = {'prices': {'USDT': 1.0}}
        exposure_data = {'total_exposure': 10000.0, 'positions': {}}
        risk_assessment = {}
        
        # Mock ML predictions for short signal
        strategy.data_provider.get_ml_predictions.return_value = {
            'signal': 'short',
            'confidence': 0.8,
            'sd': 0.02
        }
        
        orders = strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return entry full orders
        assert isinstance(orders, list)
        assert len(orders) == 1
        
        order = orders[0]
        assert isinstance(order, Order)
        assert order.side == 'SHORT'
        assert order.metadata['ml_signal'] == 'short'
    
    def test_make_strategy_decision_neutral_signal_with_position(self, strategy, mock_dependencies):
        """Test strategy decision with neutral signal and existing position."""
        _, position_monitor, _, _ = mock_dependencies
        timestamp = pd.Timestamp('2024-01-01 12:00:00')
        market_data = {'prices': {'USDT': 1.0}}
        exposure_data = {'total_exposure': 10000.0, 'positions': {'usdt_perp_position': 5000.0}}
        risk_assessment = {}
        
        # Mock existing position
        position_monitor.get_current_position.return_value = {'usdt_perp_position': 5000.0}
        
        # Mock ML predictions for neutral signal
        strategy.data_provider.get_ml_predictions.return_value = {
            'signal': 'neutral',
            'confidence': 0.8,
            'sd': 0.02
        }
        
        orders = strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return exit full orders
        assert isinstance(orders, list)
        assert len(orders) == 1
        
        order = orders[0]
        assert isinstance(order, Order)
        assert order.operation == OrderOperation.PERP_TRADE
        assert order.side == 'SELL'  # Close long position
        assert order.strategy_intent == 'exit_full'
        assert order.metadata['close_position'] is True
    
    def test_make_strategy_decision_low_confidence(self, strategy):
        """Test strategy decision with low confidence signal."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00')
        market_data = {'prices': {'USDT': 1.0}}
        exposure_data = {'total_exposure': 10000.0, 'positions': {}}
        risk_assessment = {}
        
        # Mock ML predictions with low confidence
        strategy.data_provider.get_ml_predictions.return_value = {
            'signal': 'long',
            'confidence': 0.5,  # Below threshold
            'sd': 0.02
        }
        
        orders = strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return dust sell orders (empty since no dust)
        assert isinstance(orders, list)
        assert len(orders) == 0
    
    def test_create_entry_full_orders_long(self, strategy):
        """Test creating entry full orders for long signal."""
        equity = 10000.0
        signal = 'long'
        
        orders = strategy._create_entry_full_orders(equity, signal)
        
        assert isinstance(orders, list)
        assert len(orders) == 1
        
        order = orders[0]
        assert isinstance(order, Order)
        assert order.venue == 'binance'
        assert order.operation == OrderOperation.PERP_TRADE
        assert order.pair == 'USDTUSDT'
        assert order.side == 'LONG'
        assert order.strategy_intent == 'entry_full'
        assert order.strategy_id == 'ml_usdt_directional'
        assert order.take_profit is not None
        assert order.stop_loss is not None
        assert order.metadata['ml_signal'] == 'long'
        assert order.metadata['confidence'] == 0.8
        assert order.metadata['signal_threshold'] == 0.70
    
    def test_create_entry_full_orders_short(self, strategy):
        """Test creating entry full orders for short signal."""
        equity = 10000.0
        signal = 'short'
        
        orders = strategy._create_entry_full_orders(equity, signal)
        
        assert isinstance(orders, list)
        assert len(orders) == 1
        
        order = orders[0]
        assert order.side == 'SHORT'
        assert order.metadata['ml_signal'] == 'short'
    
    def test_create_entry_partial_orders(self, strategy):
        """Test creating entry partial orders."""
        equity_delta = 5000.0
        signal = 'long'
        
        orders = strategy._create_entry_partial_orders(equity_delta, signal)
        
        assert isinstance(orders, list)
        assert len(orders) == 1
        
        order = orders[0]
        assert isinstance(order, Order)
        assert order.strategy_intent == 'entry_partial'
        assert order.metadata['ml_signal'] == 'long'
    
    def test_create_exit_full_orders_long_position(self, strategy, mock_dependencies):
        """Test creating exit full orders for long position."""
        _, position_monitor, _, _ = mock_dependencies
        
        # Mock long position
        position_monitor.get_current_position.return_value = {'usdt_perp_position': 5000.0}
        
        equity = 10000.0
        orders = strategy._create_exit_full_orders(equity)
        
        assert isinstance(orders, list)
        assert len(orders) == 1
        
        order = orders[0]
        assert isinstance(order, Order)
        assert order.venue == 'binance'
        assert order.operation == OrderOperation.PERP_TRADE
        assert order.pair == 'USDTUSDT'
        assert order.side == 'SELL'  # Close long position
        assert order.amount == 5000.0
        assert order.strategy_intent == 'exit_full'
        assert order.metadata['close_position'] is True
        assert order.metadata['original_position'] == 5000.0
    
    def test_create_exit_full_orders_short_position(self, strategy, mock_dependencies):
        """Test creating exit full orders for short position."""
        _, position_monitor, _, _ = mock_dependencies
        
        # Mock short position
        position_monitor.get_current_position.return_value = {'usdt_perp_position': -3000.0}
        
        equity = 10000.0
        orders = strategy._create_exit_full_orders(equity)
        
        assert isinstance(orders, list)
        assert len(orders) == 1
        
        order = orders[0]
        assert order.side == 'BUY'  # Close short position
        assert order.amount == 3000.0
        assert order.metadata['original_position'] == -3000.0
    
    def test_create_exit_full_orders_no_position(self, strategy, mock_dependencies):
        """Test creating exit full orders when no position."""
        _, position_monitor, _, _ = mock_dependencies
        
        # Mock no position
        position_monitor.get_current_position.return_value = {'usdt_perp_position': 0.0}
        
        equity = 10000.0
        orders = strategy._create_exit_full_orders(equity)
        
        # Should return empty list
        assert isinstance(orders, list)
        assert len(orders) == 0
    
    def test_create_exit_partial_orders(self, strategy, mock_dependencies):
        """Test creating exit partial orders."""
        _, position_monitor, _, _ = mock_dependencies
        
        # Mock long position
        position_monitor.get_current_position.return_value = {'usdt_perp_position': 5000.0}
        
        equity_delta = 5000.0
        orders = strategy._create_exit_partial_orders(equity_delta)
        
        assert isinstance(orders, list)
        assert len(orders) == 1
        
        order = orders[0]
        assert isinstance(order, Order)
        assert order.strategy_intent == 'exit_partial'
        assert order.metadata['close_position'] is True
        assert order.metadata['partial_exit'] is True
    
    def test_create_dust_sell_orders(self, strategy):
        """Test creating dust sell orders."""
        dust_tokens = {
            'ETH': 2.0,
            'BTC': 0.1,
            'USDT': 1000.0  # Should be ignored (target asset)
        }
        
        orders = strategy._create_dust_sell_orders(dust_tokens)
        
        assert isinstance(orders, list)
        assert len(orders) == 2  # ETH and BTC, but not USDT
        
        # Check ETH order
        eth_order = next((o for o in orders if o.pair == 'ETH/USDT'), None)
        assert eth_order is not None
        assert eth_order.side == 'SELL'
        assert eth_order.amount == 2.0
        assert eth_order.strategy_intent == 'sell_dust'
        
        # Check BTC order
        btc_order = next((o for o in orders if o.pair == 'BTC/USDT'), None)
        assert btc_order is not None
        assert btc_order.side == 'SELL'
        assert btc_order.amount == 0.1
        assert btc_order.strategy_intent == 'sell_dust'
    
    def test_calculate_stop_loss_take_profit_long(self, strategy):
        """Test stop loss and take profit calculation for long position."""
        current_price = 1.0
        sd = 0.02  # 2%
        signal = 'long'
        
        stop_loss, take_profit = strategy._calculate_stop_loss_take_profit(current_price, sd, signal)
        
        # For long: stop loss below, take profit above
        assert stop_loss < current_price
        assert take_profit > current_price
        assert stop_loss == current_price * (1 - 2 * sd)  # 2x SD stop loss
        assert take_profit == current_price * (1 + 3 * sd)  # 3x SD take profit
    
    def test_calculate_stop_loss_take_profit_short(self, strategy):
        """Test stop loss and take profit calculation for short position."""
        current_price = 1.0
        sd = 0.02  # 2%
        signal = 'short'
        
        stop_loss, take_profit = strategy._calculate_stop_loss_take_profit(current_price, sd, signal)
        
        # For short: stop loss above, take profit below
        assert stop_loss > current_price
        assert take_profit < current_price
        assert stop_loss == current_price * (1 + 2 * sd)  # 2x SD stop loss
        assert take_profit == current_price * (1 - 3 * sd)  # 3x SD take profit
    
    def test_calculate_stop_loss_take_profit_neutral(self, strategy):
        """Test stop loss and take profit calculation for neutral signal."""
        current_price = 1.0
        sd = 0.02  # 2%
        signal = 'neutral'
        
        stop_loss, take_profit = strategy._calculate_stop_loss_take_profit(current_price, sd, signal)
        
        # For neutral: both should be 0
        assert stop_loss == 0.0
        assert take_profit == 0.0
    
    def test_should_exit_for_risk_management(self, strategy):
        """Test risk management exit logic."""
        current_price = 1.0
        current_positions = {'usdt_perp_position': 5000.0}
        ml_predictions = {'sd': 0.02, 'signal': 'long'}
        
        # Test with price below stop loss
        stop_loss, _ = strategy._calculate_stop_loss_take_profit(current_price, 0.02, 'long')
        low_price = stop_loss - 0.01  # Below stop loss
        
        should_exit = strategy._should_exit_for_risk_management(low_price, current_positions, ml_predictions)
        assert should_exit is True
        
        # Test with price above take profit
        _, take_profit = strategy._calculate_stop_loss_take_profit(current_price, 0.02, 'long')
        high_price = take_profit + 0.01  # Above take profit
        
        should_exit = strategy._should_exit_for_risk_management(high_price, current_positions, ml_predictions)
        assert should_exit is True
        
        # Test with price in safe range
        safe_price = current_price  # At entry price
        
        should_exit = strategy._should_exit_for_risk_management(safe_price, current_positions, ml_predictions)
        assert should_exit is False
    
    def test_position_detection_methods(self, strategy):
        """Test position detection helper methods."""
        # Test long position
        long_positions = {'usdt_perp_position': 5000.0}
        assert strategy._has_long_position(long_positions) is True
        assert strategy._has_short_position(long_positions) is False
        assert strategy._has_any_position(long_positions) is True
        
        # Test short position
        short_positions = {'usdt_perp_position': -3000.0}
        assert strategy._has_long_position(short_positions) is False
        assert strategy._has_short_position(short_positions) is True
        assert strategy._has_any_position(short_positions) is True
        
        # Test no position
        no_positions = {'usdt_perp_position': 0.0}
        assert strategy._has_long_position(no_positions) is False
        assert strategy._has_short_position(no_positions) is False
        assert strategy._has_any_position(no_positions) is False
    
    def test_calculate_target_position(self, strategy):
        """Test target position calculation."""
        equity = 10000.0
        
        target = strategy.calculate_target_position(equity)
        
        expected_usdt_position = equity * strategy.max_position_size
        assert target['usdt_perp_position'] == expected_usdt_position
        assert target['btc_balance'] == equity - expected_usdt_position
    
    def test_get_asset_price(self, strategy):
        """Test asset price retrieval."""
        price = strategy._get_asset_price()
        assert isinstance(price, float)
        assert price > 0
        assert price == 1.0  # Mock USDT price
    
    def test_strategy_initialization(self, strategy_config, mock_dependencies):
        """Test strategy initialization."""
        risk_monitor, position_monitor, event_engine, data_provider = mock_dependencies
        
        strategy = MLUSDTDirectionalStrategy(strategy_config, risk_monitor, position_monitor, event_engine, data_provider)
        
        assert strategy.share_class == 'USDT'
        assert strategy.asset == 'USDT'
        assert strategy.signal_threshold == 0.70
        assert strategy.max_position_size == 1.0
        assert strategy.stop_loss_pct == 0.03
        assert strategy.take_profit_pct == 0.10
        assert strategy.data_provider == data_provider
        assert strategy.risk_monitor == risk_monitor
        assert strategy.position_monitor == position_monitor
        assert strategy.event_engine == event_engine
    
    def test_strategy_initialization_missing_config(self, mock_dependencies):
        """Test strategy initialization with missing config."""
        risk_monitor, position_monitor, event_engine, data_provider = mock_dependencies
        
        incomplete_config = {
            'share_class': 'USDT',
            'asset': 'USDT',
            'signal_threshold': 0.70
            # Missing required keys
        }
        
        with pytest.raises(KeyError):
            MLUSDTDirectionalStrategy(incomplete_config, risk_monitor, position_monitor, event_engine, data_provider)
    
    def test_get_strategy_info(self, strategy):
        """Test strategy info retrieval."""
        info = strategy.get_strategy_info()
        
        assert isinstance(info, dict)
        assert info['strategy_type'] == 'ml_usdt_directional'
        assert info['signal_threshold'] == 0.70
        assert info['max_position_size'] == 1.0
        assert info['stop_loss_pct'] == 0.03
        assert info['take_profit_pct'] == 0.10
        assert info['order_system'] == 'unified_order_trade'
        assert info['risk_management'] == 'take_profit_stop_loss'
        assert 'unified_order_trade' in info['description']
    
    def test_order_validation(self, strategy):
        """Test that created orders pass validation."""
        equity = 10000.0
        signal = 'long'
        orders = strategy._create_entry_full_orders(equity, signal)
        
        for order in orders:
            # Orders should be valid Pydantic models
            assert isinstance(order, Order)
            
            # Required fields should be present
            assert order.venue is not None
            assert order.operation is not None
            assert order.amount > 0
            assert order.strategy_intent is not None
            assert order.strategy_id == 'ml_usdt_directional'
            
            # Risk management fields should be present
            assert order.take_profit is not None
            assert order.stop_loss is not None