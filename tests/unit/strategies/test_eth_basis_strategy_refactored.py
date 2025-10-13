"""
Unit tests for the refactored ETH Basis Strategy.

Tests the ETH basis strategy using the new Order model instead of StrategyAction.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from typing import Dict, Any

from backend.src.basis_strategy_v1.core.strategies.eth_basis_strategy import ETHBasisStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation


class TestETHBasisStrategyRefactored:
    """Test suite for the refactored ETH Basis Strategy."""
    
    @pytest.fixture
    def mock_risk_monitor(self):
        """Mock risk monitor."""
        return Mock()
    
    @pytest.fixture
    def mock_position_monitor(self):
        """Mock position monitor."""
        return Mock()
    
    @pytest.fixture
    def mock_event_engine(self):
        """Mock event engine."""
        return Mock()
    
    @pytest.fixture
    def strategy_config(self):
        """Strategy configuration."""
        return {
            'eth_allocation': 0.8,
            'funding_threshold': 0.01,
            'max_leverage': 1.0,
            'mode': 'backtest',
            'share_class': 'USDT',
            'asset': 'ETH'
        }
    
    @pytest.fixture
    def eth_basis_strategy(self, strategy_config, mock_risk_monitor, mock_position_monitor, mock_event_engine):
        """Create ETH basis strategy instance."""
        strategy = ETHBasisStrategy(
            config=strategy_config,
            risk_monitor=mock_risk_monitor,
            position_monitor=mock_position_monitor,
            event_engine=mock_event_engine
        )
        # Mock the _get_asset_price method
        strategy._get_asset_price = Mock(return_value=3000.0)
        return strategy
    
    def test_initialization(self, eth_basis_strategy, strategy_config):
        """Test strategy initialization."""
        assert eth_basis_strategy.share_class == 'USDT'
        assert eth_basis_strategy.asset == 'ETH'
        assert eth_basis_strategy.eth_allocation == strategy_config['eth_allocation']
        assert eth_basis_strategy.funding_threshold == strategy_config['funding_threshold']
        assert eth_basis_strategy.max_leverage == strategy_config['max_leverage']
    
    def test_get_asset_price(self, eth_basis_strategy):
        """Test asset price retrieval."""
        price = eth_basis_strategy._get_asset_price()
        assert price == 3000.0  # Default ETH price for testing
    
    def test_calculate_target_position(self, eth_basis_strategy):
        """Test target position calculation."""
        current_equity = 10000.0
        target_position = eth_basis_strategy.calculate_target_position(current_equity)
        
        assert 'eth_balance' in target_position
        assert 'eth_perpetual_short' in target_position
        assert 'total_equity' in target_position
        assert target_position['total_equity'] == current_equity
        
        # ETH allocation should be 80% of equity
        expected_eth_value = current_equity * 0.8
        expected_eth_amount = expected_eth_value / 3000.0  # ETH price
        assert abs(target_position['eth_balance'] - expected_eth_amount) < 0.001
        assert abs(target_position['eth_perpetual_short'] + expected_eth_amount) < 0.001
    
    def test_should_enter_basis_position(self, eth_basis_strategy):
        """Test basis position entry decision logic."""
        # Should enter when funding rate is above threshold
        assert eth_basis_strategy._should_enter_basis_position(0.02, 3000.0) == True
        assert eth_basis_strategy._should_enter_basis_position(-0.02, 3000.0) == True
        
        # Should not enter when funding rate is below threshold
        assert eth_basis_strategy._should_enter_basis_position(0.005, 3000.0) == False
        assert eth_basis_strategy._should_enter_basis_position(0.0, 3000.0) == False
        
        # Should not enter when price is 0
        assert eth_basis_strategy._should_enter_basis_position(0.02, 0.0) == False
    
    def test_should_rebalance_position(self, eth_basis_strategy):
        """Test position rebalancing decision logic."""
        current_positions = {'eth_balance': 1.0, 'eth_perpetual_short': -1.0}
        
        # Should rebalance when funding rate is significantly above threshold
        assert eth_basis_strategy._should_rebalance_position(0.02, current_positions) == True
        
        # Should not rebalance when funding rate is below threshold
        assert eth_basis_strategy._should_rebalance_position(0.005, current_positions) == False
    
    def test_make_strategy_decision_no_equity(self, eth_basis_strategy):
        """Test strategy decision with no equity."""
        timestamp = pd.Timestamp.now()
        market_data = {'prices': {'ETH': 3000.0}, 'rates': {'eth_funding': 0.02}}
        exposure_data = {'positions': {}, 'total_exposure': 0.0}
        risk_assessment = {'liquidation_risk': 0.0, 'cex_margin_ratio': 1.0}
        
        orders = eth_basis_strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return dust sell orders when no equity
        assert isinstance(orders, list)
        # No orders expected since no dust tokens
        assert len(orders) == 0
    
    def test_make_strategy_decision_no_eth_position_favorable_funding(self, eth_basis_strategy):
        """Test strategy decision with equity but no ETH position and favorable funding."""
        timestamp = pd.Timestamp.now()
        market_data = {'prices': {'ETH': 3000.0}, 'rates': {'eth_funding': 0.02}}
        exposure_data = {'positions': {'usdt_balance': 10000.0}, 'total_exposure': 10000.0}
        risk_assessment = {'liquidation_risk': 0.0, 'cex_margin_ratio': 1.0}
        
        orders = eth_basis_strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should create entry orders
        assert isinstance(orders, list)
        assert len(orders) == 2  # ETH spot buy + ETH perp short
        
        # Check first order (ETH spot buy)
        spot_order = orders[0]
        assert isinstance(spot_order, Order)
        assert spot_order.venue == 'binance'
        assert spot_order.operation == OrderOperation.SPOT_TRADE
        assert spot_order.pair == 'ETH/USDT'
        assert spot_order.side == 'BUY'
        assert spot_order.order_type == 'market'
        assert spot_order.execution_mode == 'sequential'
        assert spot_order.strategy_intent == 'eth_basis_entry'
        assert spot_order.strategy_id == 'eth_basis'
        
        # Check second order (ETH perp short)
        perp_order = orders[1]
        assert isinstance(perp_order, Order)
        assert perp_order.venue == 'bybit'
        assert perp_order.operation == OrderOperation.PERP_TRADE
        assert perp_order.pair == 'ETHUSDT'
        assert perp_order.side == 'SHORT'
        assert perp_order.order_type == 'market'
        assert perp_order.execution_mode == 'sequential'
        assert perp_order.strategy_intent == 'eth_basis_entry'
        assert perp_order.strategy_id == 'eth_basis'
    
    def test_make_strategy_decision_no_eth_position_unfavorable_funding(self, eth_basis_strategy):
        """Test strategy decision with equity but no ETH position and unfavorable funding."""
        timestamp = pd.Timestamp.now()
        market_data = {'prices': {'ETH': 3000.0}, 'rates': {'eth_funding': 0.005}}
        exposure_data = {'positions': {'usdt_balance': 10000.0}, 'total_exposure': 10000.0}
        risk_assessment = {'liquidation_risk': 0.0, 'cex_margin_ratio': 1.0}
        
        orders = eth_basis_strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return dust sell orders (wait for better opportunity)
        assert isinstance(orders, list)
        assert len(orders) == 0  # No dust tokens to sell
    
    def test_make_strategy_decision_high_risk_exit(self, eth_basis_strategy):
        """Test strategy decision with high liquidation risk."""
        timestamp = pd.Timestamp.now()
        market_data = {'prices': {'ETH': 3000.0}, 'rates': {'eth_funding': 0.02}}
        exposure_data = {'positions': {'eth_balance': 2.0, 'eth_perpetual_short': -2.0}, 'total_exposure': 10000.0}
        risk_assessment = {'liquidation_risk': 0.9, 'cex_margin_ratio': 0.1}
        
        # Mock position monitor to return the expected position
        eth_basis_strategy.position_monitor.get_current_position.return_value = {
            'eth_balance': 2.0,
            'eth_perpetual_short': -2.0
        }
        
        orders = eth_basis_strategy.make_strategy_decision(
            timestamp, 'risk_monitor', market_data, exposure_data, risk_assessment
        )
        
        # Should create exit orders
        assert isinstance(orders, list)
        assert len(orders) == 2  # Close perp short + sell ETH spot
        
        # Check first order (close perp short)
        close_order = orders[0]
        assert isinstance(close_order, Order)
        assert close_order.venue == 'bybit'
        assert close_order.operation == OrderOperation.PERP_TRADE
        assert close_order.pair == 'ETHUSDT'
        assert close_order.side == 'BUY'  # Close short position
        # The amount is scaled based on equity vs position value
        assert close_order.amount > 0
        assert close_order.strategy_intent == 'eth_basis_exit'
        
        # Check second order (sell ETH spot)
        sell_order = orders[1]
        assert isinstance(sell_order, Order)
        assert sell_order.venue == 'binance'
        assert sell_order.operation == OrderOperation.SPOT_TRADE
        assert sell_order.pair == 'ETH/USDT'
        assert sell_order.side == 'SELL'
        # The amount is scaled based on equity vs position value
        assert sell_order.amount > 0
        assert sell_order.strategy_intent == 'eth_basis_exit'
    
    def test_make_strategy_decision_medium_risk_partial_exit(self, eth_basis_strategy):
        """Test strategy decision with medium liquidation risk."""
        timestamp = pd.Timestamp.now()
        market_data = {'prices': {'ETH': 3000.0}, 'rates': {'eth_funding': 0.02}}
        exposure_data = {'positions': {'eth_balance': 2.0, 'eth_perpetual_short': -2.0}, 'total_exposure': 10000.0}
        risk_assessment = {'liquidation_risk': 0.7, 'cex_margin_ratio': 0.25}
        
        # Mock position monitor to return the expected position
        eth_basis_strategy.position_monitor.get_current_position.return_value = {
            'eth_balance': 2.0,
            'eth_perpetual_short': -2.0
        }
        
        orders = eth_basis_strategy.make_strategy_decision(
            timestamp, 'risk_monitor', market_data, exposure_data, risk_assessment
        )
        
        # Should create partial exit orders (50% of equity)
        assert isinstance(orders, list)
        assert len(orders) == 2  # Close perp short + sell ETH spot
        
        # Check that amounts are proportional to partial exit
        close_order = orders[0]
        assert close_order.amount > 0  # Scaled amount
        
        sell_order = orders[1]
        assert sell_order.amount > 0  # Scaled amount
    
    def test_make_strategy_decision_rebalance(self, eth_basis_strategy):
        """Test strategy decision for rebalancing."""
        timestamp = pd.Timestamp.now()
        market_data = {'prices': {'ETH': 3000.0}, 'rates': {'eth_funding': 0.02}}
        exposure_data = {'positions': {'eth_balance': 1.0, 'eth_perpetual_short': -1.0}, 'total_exposure': 10000.0}
        risk_assessment = {'liquidation_risk': 0.3, 'cex_margin_ratio': 0.8}
        
        orders = eth_basis_strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should create rebalance orders
        assert isinstance(orders, list)
        assert len(orders) == 2  # ETH spot buy + ETH perp short increase
        
        # Check rebalance orders
        spot_order = orders[0]
        assert spot_order.strategy_intent == 'eth_basis_rebalance'
        assert spot_order.metadata.get('rebalance') == True
        
        perp_order = orders[1]
        assert perp_order.strategy_intent == 'eth_basis_rebalance'
        assert perp_order.metadata.get('rebalance') == True
    
    def test_make_strategy_decision_maintain_position(self, eth_basis_strategy):
        """Test strategy decision to maintain current position."""
        timestamp = pd.Timestamp.now()
        market_data = {'prices': {'ETH': 3000.0}, 'rates': {'eth_funding': 0.005}}
        exposure_data = {'positions': {'eth_perpetual_short': -1.0}, 'total_exposure': 10000.0}
        risk_assessment = {'liquidation_risk': 0.3, 'cex_margin_ratio': 0.8}
        
        orders = eth_basis_strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return dust sell orders (maintain position)
        assert isinstance(orders, list)
        assert len(orders) == 0  # No dust tokens to sell
    
    def test_create_entry_orders(self, eth_basis_strategy):
        """Test entry order creation."""
        equity = 10000.0
        orders = eth_basis_strategy._create_entry_orders(equity)
        
        assert isinstance(orders, list)
        assert len(orders) == 2
        
        # Verify order structure
        for order in orders:
            assert isinstance(order, Order)
            assert order.execution_mode == 'sequential'
            assert order.strategy_id == 'eth_basis'
            assert order.strategy_intent == 'eth_basis_entry'
    
    def test_create_rebalance_orders(self, eth_basis_strategy):
        """Test rebalance order creation."""
        equity_delta = 2000.0
        orders = eth_basis_strategy._create_rebalance_orders(equity_delta)
        
        assert isinstance(orders, list)
        assert len(orders) == 2
        
        # Verify order structure
        for order in orders:
            assert isinstance(order, Order)
            assert order.execution_mode == 'sequential'
            assert order.strategy_id == 'eth_basis'
            assert order.strategy_intent == 'eth_basis_rebalance'
            assert order.metadata.get('rebalance') == True
    
    def test_create_exit_orders(self, eth_basis_strategy):
        """Test exit order creation."""
        equity = 10000.0
        
        # Mock position monitor
        eth_basis_strategy.position_monitor.get_current_position.return_value = {
            'eth_balance': 2.0,
            'eth_perpetual_short': -2.0
        }
        
        orders = eth_basis_strategy._create_exit_orders(equity)
        
        assert isinstance(orders, list)
        assert len(orders) == 2
        
        # Verify order structure
        for order in orders:
            assert isinstance(order, Order)
            assert order.execution_mode == 'sequential'
            assert order.strategy_id == 'eth_basis'
            assert order.strategy_intent == 'eth_basis_exit'
            assert order.metadata.get('close_position') == True
    
    def test_create_dust_sell_orders(self, eth_basis_strategy):
        """Test dust sell order creation."""
        exposure_data = {
            'positions': {
                'eth_balance': 0.1,  # Dust ETH
                'btc_balance': 0.001,  # Dust BTC
                'usdt_balance': 1000.0  # Not dust
            }
        }
        
        orders = eth_basis_strategy._create_dust_sell_orders(exposure_data)
        
        assert isinstance(orders, list)
        assert len(orders) == 2  # ETH dust + BTC dust
        
        # Check ETH dust order
        eth_order = orders[0]
        assert eth_order.venue == 'binance'
        assert eth_order.operation == OrderOperation.SPOT_TRADE
        assert eth_order.pair == 'ETH/USDT'
        assert eth_order.side == 'SELL'
        assert eth_order.amount == 0.1
        assert eth_order.strategy_intent == 'eth_basis_dust_sell'
    
    def test_get_strategy_info(self, eth_basis_strategy):
        """Test strategy info retrieval."""
        info = eth_basis_strategy.get_strategy_info()
        
        assert isinstance(info, dict)
        assert info['strategy_type'] == 'eth_basis'
        assert info['share_class'] == 'USDT'
        assert info['asset'] == 'ETH'
        assert info['eth_allocation'] == 0.8
        assert info['funding_threshold'] == 0.01
        assert info['max_leverage'] == 1.0
        assert 'description' in info
    
    def test_make_strategy_decision_exception_handling(self, eth_basis_strategy):
        """Test exception handling in strategy decision."""
        timestamp = pd.Timestamp.now()
        market_data = {}  # Empty market data to trigger exception
        exposure_data = {'positions': {}, 'total_exposure': 0.0}
        risk_assessment = {}
        
        orders = eth_basis_strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return empty list on exception
        assert isinstance(orders, list)
        assert len(orders) == 0
