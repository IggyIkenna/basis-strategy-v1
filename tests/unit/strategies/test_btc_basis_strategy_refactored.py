"""
Unit tests for refactored BTC Basis Strategy using Order model.

Tests the BTC basis strategy refactored to return List[Order] instead of StrategyAction.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Any

from backend.src.basis_strategy_v1.core.strategies.btc_basis_strategy import BTCBasisStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation


class TestBTCBasisStrategyRefactored:
    """Test suite for refactored BTC basis strategy."""
    
    @pytest.fixture
    def mock_risk_monitor(self):
        """Mock risk monitor."""
        return Mock()
    
    @pytest.fixture
    def mock_position_monitor(self):
        """Mock position monitor."""
        monitor = Mock()
        monitor.get_current_position.return_value = {
            'btc_balance': 0.0,
            'btc_perpetual_short': 0.0,
            'usdt_balance': 10000.0
        }
        return monitor
    
    @pytest.fixture
    def mock_event_engine(self):
        """Mock event engine."""
        return Mock()
    
    @pytest.fixture
    def strategy_config(self):
        """Strategy configuration."""
        return {
            'btc_allocation': 0.8,
            'funding_threshold': 0.01,
            'max_leverage': 1.0,
            'mode': 'backtest',
            'share_class': 'USDT',
            'asset': 'BTC'
        }
    
    @pytest.fixture
    def btc_basis_strategy(self, strategy_config, mock_risk_monitor, mock_position_monitor, mock_event_engine):
        """Create BTC basis strategy instance."""
        strategy = BTCBasisStrategy(
            config=strategy_config,
            risk_monitor=mock_risk_monitor,
            position_monitor=mock_position_monitor,
            event_engine=mock_event_engine
        )
        # Mock the _get_asset_price method
        strategy._get_asset_price = Mock(return_value=50000.0)
        return strategy
    
    def test_strategy_initialization(self, btc_basis_strategy, strategy_config):
        """Test strategy initialization."""
        assert btc_basis_strategy.btc_allocation == 0.8
        assert btc_basis_strategy.funding_threshold == 0.01
        assert btc_basis_strategy.max_leverage == 1.0
        assert btc_basis_strategy.share_class == 'USDT'
        assert btc_basis_strategy.asset == 'BTC'
    
    def test_make_strategy_decision_no_equity(self, btc_basis_strategy):
        """Test strategy decision with no equity."""
        timestamp = pd.Timestamp.now()
        market_data = {
            'prices': {'BTC': 50000.0},
            'rates': {'btc_funding': 0.02}
        }
        exposure_data = {
            'total_exposure': 0.0,
            'positions': {}
        }
        risk_assessment = {
            'liquidation_risk': 0.0,
            'cex_margin_ratio': 1.0
        }
        
        orders = btc_basis_strategy.make_strategy_decision(
            timestamp=timestamp,
            trigger_source='scheduled',
            market_data=market_data,
            exposure_data=exposure_data,
            risk_assessment=risk_assessment
        )
        
        # Should return dust sell orders when no equity
        assert isinstance(orders, list)
        assert len(orders) == 0  # No dust to sell
    
    def test_make_strategy_decision_with_equity_favorable_funding(self, btc_basis_strategy):
        """Test strategy decision with equity and favorable funding rate."""
        timestamp = pd.Timestamp.now()
        market_data = {
            'prices': {'BTC': 50000.0},
            'rates': {'btc_funding': 0.02}  # Above threshold
        }
        exposure_data = {
            'total_exposure': 10000.0,
            'positions': {}
        }
        risk_assessment = {
            'liquidation_risk': 0.0,
            'cex_margin_ratio': 1.0
        }
        
        orders = btc_basis_strategy.make_strategy_decision(
            timestamp=timestamp,
            trigger_source='scheduled',
            market_data=market_data,
            exposure_data=exposure_data,
            risk_assessment=risk_assessment
        )
        
        # Should return entry orders
        assert isinstance(orders, list)
        assert len(orders) == 2  # BTC spot buy + BTC perp short
        
        # Check first order (BTC spot buy)
        spot_order = orders[0]
        assert isinstance(spot_order, Order)
        assert spot_order.operation == OrderOperation.SPOT_TRADE
        assert spot_order.venue == 'binance'
        assert spot_order.pair == 'BTC/USDT'
        assert spot_order.side == 'BUY'
        assert spot_order.execution_mode == 'sequential'
        assert spot_order.strategy_intent == 'btc_basis_entry'
        
        # Check second order (BTC perp short)
        perp_order = orders[1]
        assert isinstance(perp_order, Order)
        assert perp_order.operation == OrderOperation.PERP_TRADE
        assert perp_order.venue == 'bybit'
        assert perp_order.pair == 'BTCUSDT'
        assert perp_order.side == 'SHORT'
        assert perp_order.execution_mode == 'sequential'
        assert perp_order.strategy_intent == 'btc_basis_entry'
    
    def test_make_strategy_decision_high_risk_exit(self, btc_basis_strategy):
        """Test strategy decision with high liquidation risk."""
        # Update the mock position monitor to return the correct position
        btc_basis_strategy.position_monitor.get_current_position.return_value = {
            'btc_balance': 0.1,
            'btc_perpetual_short': -0.1,
            'usdt_balance': 5000.0
        }
        
        timestamp = pd.Timestamp.now()
        market_data = {
            'prices': {'BTC': 50000.0},
            'rates': {'btc_funding': 0.02}
        }
        exposure_data = {
            'total_exposure': 10000.0,
            'positions': {
                'btc_balance': 0.1,
                'btc_perpetual_short': -0.1
            }
        }
        risk_assessment = {
            'liquidation_risk': 0.9,  # High risk
            'cex_margin_ratio': 0.1
        }
        
        orders = btc_basis_strategy.make_strategy_decision(
            timestamp=timestamp,
            trigger_source='risk_monitor',
            market_data=market_data,
            exposure_data=exposure_data,
            risk_assessment=risk_assessment
        )
        
        # Should return exit orders
        assert isinstance(orders, list)
        assert len(orders) == 2  # Close perp short + sell BTC spot
        
        # Check first order (close perp short)
        close_order = orders[0]
        assert isinstance(close_order, Order)
        assert close_order.operation == OrderOperation.PERP_TRADE
        assert close_order.venue == 'bybit'
        assert close_order.pair == 'BTCUSDT'
        assert close_order.side == 'LONG'  # Close short position
        assert close_order.strategy_intent == 'btc_basis_exit'
        
        # Check second order (sell BTC spot)
        sell_order = orders[1]
        assert isinstance(sell_order, Order)
        assert sell_order.operation == OrderOperation.SPOT_TRADE
        assert sell_order.venue == 'binance'
        assert sell_order.pair == 'BTC/USDT'
        assert sell_order.side == 'SELL'
        assert sell_order.strategy_intent == 'btc_basis_exit'
    
    def test_create_entry_orders(self, btc_basis_strategy):
        """Test entry order creation."""
        equity = 10000.0
        
        orders = btc_basis_strategy._create_entry_orders(equity)
        
        assert isinstance(orders, list)
        assert len(orders) == 2
        
        # Verify spot buy order
        spot_order = orders[0]
        assert spot_order.operation == OrderOperation.SPOT_TRADE
        assert spot_order.venue == 'binance'
        assert spot_order.pair == 'BTC/USDT'
        assert spot_order.side == 'BUY'
        assert spot_order.order_type == 'market'
        assert spot_order.execution_mode == 'sequential'
        assert spot_order.strategy_intent == 'btc_basis_entry'
        assert spot_order.strategy_id == 'btc_basis'
        
        # Verify perp short order
        perp_order = orders[1]
        assert perp_order.operation == OrderOperation.PERP_TRADE
        assert perp_order.venue == 'bybit'
        assert perp_order.pair == 'BTCUSDT'
        assert perp_order.side == 'SHORT'
        assert perp_order.order_type == 'market'
        assert perp_order.execution_mode == 'sequential'
        assert perp_order.strategy_intent == 'btc_basis_entry'
        assert perp_order.strategy_id == 'btc_basis'
    
    def test_create_exit_orders(self, btc_basis_strategy):
        """Test exit order creation."""
        equity = 10000.0
        
        # Mock current position
        btc_basis_strategy.position_monitor.get_current_position.return_value = {
            'btc_balance': 0.1,
            'btc_perpetual_short': -0.1,
            'usdt_balance': 5000.0
        }
        
        orders = btc_basis_strategy._create_exit_orders(equity)
        
        assert isinstance(orders, list)
        assert len(orders) == 2
        
        # Verify close perp order
        close_order = orders[0]
        assert close_order.operation == OrderOperation.PERP_TRADE
        assert close_order.venue == 'bybit'
        assert close_order.pair == 'BTCUSDT'
        assert close_order.side == 'LONG'  # Close short
        assert close_order.amount == 0.1
        assert close_order.strategy_intent == 'btc_basis_exit'
        
        # Verify sell spot order
        sell_order = orders[1]
        assert sell_order.operation == OrderOperation.SPOT_TRADE
        assert sell_order.venue == 'binance'
        assert sell_order.pair == 'BTC/USDT'
        assert sell_order.side == 'SELL'
        assert sell_order.amount == 0.1
        assert sell_order.strategy_intent == 'btc_basis_exit'
    
    def test_create_rebalance_orders(self, btc_basis_strategy):
        """Test rebalance order creation."""
        equity_delta = 2000.0
        
        orders = btc_basis_strategy._create_rebalance_orders(equity_delta)
        
        assert isinstance(orders, list)
        assert len(orders) == 2
        
        # Verify both orders have rebalance intent
        for order in orders:
            assert order.strategy_intent == 'btc_basis_rebalance'
            assert order.strategy_id == 'btc_basis'
            assert order.execution_mode == 'sequential'
    
    def test_create_dust_sell_orders(self, btc_basis_strategy):
        """Test dust sell order creation."""
        exposure_data = {
            'positions': {
                'btc_balance': 0.01,  # Dust BTC
                'eth_balance': 0.1,   # Dust ETH
                'usdt_balance': 1000.0  # Main currency
            }
        }
        
        orders = btc_basis_strategy._create_dust_sell_orders(exposure_data)
        
        assert isinstance(orders, list)
        assert len(orders) == 2  # BTC sell + ETH transfer
        
        # Verify BTC sell order
        btc_order = orders[0]
        assert btc_order.operation == OrderOperation.SPOT_TRADE
        assert btc_order.venue == 'binance'
        assert btc_order.pair == 'BTC/USDT'
        assert btc_order.side == 'SELL'
        assert btc_order.amount == 0.01
        assert btc_order.strategy_intent == 'dust_sell'
        
        # Verify ETH transfer order
        eth_order = orders[1]
        assert eth_order.operation == OrderOperation.TRANSFER
        assert eth_order.venue == 'wallet'
        assert eth_order.token == 'ETH'
        assert eth_order.amount == 0.1
        assert eth_order.strategy_intent == 'dust_sell'
    
    def test_should_enter_basis_position(self, btc_basis_strategy):
        """Test basis position entry decision logic."""
        # Favorable funding rate
        assert btc_basis_strategy._should_enter_basis_position(0.02, 50000.0) == True
        
        # Unfavorable funding rate
        assert btc_basis_strategy._should_enter_basis_position(0.005, 50000.0) == False
        
        # Zero price
        assert btc_basis_strategy._should_enter_basis_position(0.02, 0.0) == False
    
    def test_should_rebalance_position(self, btc_basis_strategy):
        """Test position rebalancing decision logic."""
        # Test with current positions
        current_positions = {
            'btc_balance': 0.1,
            'btc_perpetual_short': -0.1
        }
        
        # Should rebalance when funding rate changes significantly
        result = btc_basis_strategy._should_rebalance_position(0.02, current_positions)
        assert isinstance(result, bool)
    
    def test_calculate_target_position(self, btc_basis_strategy):
        """Test target position calculation."""
        current_equity = 10000.0
        
        target = btc_basis_strategy.calculate_target_position(current_equity)
        
        assert isinstance(target, dict)
        assert 'btc_balance' in target
        assert 'btc_perpetual_short' in target
        assert f'{btc_basis_strategy.share_class.lower()}_balance' in target
        assert 'total_equity' in target
        
        # Verify allocation logic
        expected_btc_allocation = current_equity * btc_basis_strategy.btc_allocation
        assert target['btc_balance'] > 0
        assert target['btc_perpetual_short'] < 0  # Short position
        assert target['total_equity'] == current_equity
    
    def test_get_strategy_info(self, btc_basis_strategy):
        """Test strategy info retrieval."""
        info = btc_basis_strategy.get_strategy_info()
        
        assert isinstance(info, dict)
        assert info['strategy_type'] == 'btc_basis'
        assert info['btc_allocation'] == 0.8
        assert info['funding_threshold'] == 0.01
        assert info['max_leverage'] == 1.0
        assert 'description' in info
    
    def test_error_handling_in_make_strategy_decision(self, btc_basis_strategy):
        """Test error handling in strategy decision."""
        # Mock an error in _get_asset_price
        btc_basis_strategy._get_asset_price.side_effect = Exception("Price fetch error")
        
        timestamp = pd.Timestamp.now()
        market_data = {'prices': {'BTC': 50000.0}, 'rates': {'btc_funding': 0.02}}
        exposure_data = {'total_exposure': 10000.0, 'positions': {}}
        risk_assessment = {'liquidation_risk': 0.0, 'cex_margin_ratio': 1.0}
        
        # Should not raise exception, return safe default
        orders = btc_basis_strategy.make_strategy_decision(
            timestamp=timestamp,
            trigger_source='scheduled',
            market_data=market_data,
            exposure_data=exposure_data,
            risk_assessment=risk_assessment
        )
        
        assert isinstance(orders, list)
        # Should return dust sell orders as safe default
        assert len(orders) == 0  # No dust to sell in this case
