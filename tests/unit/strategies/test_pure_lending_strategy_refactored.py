"""
Unit tests for refactored PureLendingStrategy using Order model.

Tests the new Order-based interface instead of StrategyAction.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock

from backend.src.basis_strategy_v1.core.strategies.pure_lending_strategy import PureLendingStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation


class TestPureLendingStrategyRefactored:
    """Test refactored PureLendingStrategy with Order model."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for strategy."""
        risk_monitor = Mock()
        position_monitor = Mock()
        event_engine = Mock()
        
        return risk_monitor, position_monitor, event_engine
    
    @pytest.fixture
    def strategy_config(self):
        """Create strategy configuration."""
        return {
            'share_class': 'USDT',
            'asset': 'USDT',
            'lending_venues': ['aave', 'morpho'],
            'dust_delta': 0.002
        }
    
    @pytest.fixture
    def strategy(self, strategy_config, mock_dependencies):
        """Create PureLendingStrategy instance."""
        risk_monitor, position_monitor, event_engine = mock_dependencies
        return PureLendingStrategy(strategy_config, risk_monitor, position_monitor, event_engine)
    
    def test_make_strategy_decision_no_equity(self, strategy):
        """Test strategy decision when no equity."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00')
        market_data = {}
        exposure_data = {'total_exposure': 0.0, 'positions': {}}
        risk_assessment = {}
        
        orders = strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return dust sell orders (empty list since no dust)
        assert isinstance(orders, list)
        assert len(orders) == 0  # No dust tokens to sell
    
    def test_make_strategy_decision_with_equity_no_position(self, strategy):
        """Test strategy decision when equity exists but no lending position."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00')
        market_data = {}
        exposure_data = {
            'total_exposure': 10000.0,
            'positions': {}  # No aave_usdt_supply position
        }
        risk_assessment = {}
        
        orders = strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return entry_full orders
        assert isinstance(orders, list)
        assert len(orders) == 2  # One order per lending venue (aave, morpho)
        
        # Check first order (AAVE)
        aave_order = orders[0]
        assert isinstance(aave_order, Order)
        assert aave_order.venue == 'aave'
        assert aave_order.operation == OrderOperation.SUPPLY
        assert aave_order.token_in == 'USDT'
        assert aave_order.token_out == 'aUSDT'
        assert aave_order.amount == 5000.0  # 10000 / 2 venues
        assert aave_order.execution_mode == 'sequential'
        assert aave_order.strategy_intent == 'entry_full'
        
        # Check second order (Morpho)
        morpho_order = orders[1]
        assert isinstance(morpho_order, Order)
        assert morpho_order.venue == 'morpho'
        assert morpho_order.operation == OrderOperation.SUPPLY
        assert morpho_order.token_in == 'USDT'
        assert morpho_order.token_out == 'aUSDT'
        assert morpho_order.amount == 5000.0  # 10000 / 2 venues
        assert morpho_order.execution_mode == 'sequential'
        assert morpho_order.strategy_intent == 'entry_full'
    
    def test_make_strategy_decision_existing_position(self, strategy):
        """Test strategy decision when already lending."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00')
        market_data = {}
        exposure_data = {
            'total_exposure': 10000.0,
            'positions': {'aave_usdt_supply': 5000.0}  # Already lending
        }
        risk_assessment = {}
        
        orders = strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return dust sell orders (empty since no dust)
        assert isinstance(orders, list)
        assert len(orders) == 0  # No dust tokens to sell
    
    def test_create_entry_full_orders(self, strategy):
        """Test creating entry full orders."""
        equity = 10000.0
        
        orders = strategy._create_entry_full_orders(equity)
        
        assert isinstance(orders, list)
        assert len(orders) == 2  # One per venue
        
        for order in orders:
            assert isinstance(order, Order)
            assert order.operation == OrderOperation.SUPPLY
            assert order.token_in == 'USDT'
            assert order.token_out == 'aUSDT'
            assert order.amount == 5000.0  # 10000 / 2 venues
            assert order.execution_mode == 'sequential'
            assert order.strategy_intent == 'entry_full'
    
    def test_create_exit_full_orders(self, strategy, mock_dependencies):
        """Test creating exit full orders."""
        _, position_monitor, _ = mock_dependencies
        
        # Mock position snapshot
        position_monitor.get_position_snapshot.return_value = {
            'total_supply': 10000.0,
            'total_borrow': 0.0
        }
        
        equity = 10000.0
        orders = strategy._create_exit_full_orders(equity)
        
        assert isinstance(orders, list)
        assert len(orders) == 2  # One per venue
        
        for order in orders:
            assert isinstance(order, Order)
            assert order.operation == OrderOperation.WITHDRAW
            assert order.token_in == 'aUSDT'
            assert order.token_out == 'USDT'
            assert order.amount == 5000.0  # 10000 / 2 venues
            assert order.execution_mode == 'sequential'
            assert order.strategy_intent == 'exit_full'
    
    def test_create_dust_sell_orders(self, strategy):
        """Test creating dust sell orders."""
        exposure_data = {
            'dust_tokens': {
                'ETH': 0.1,
                'BTC': 0.01,
                'USDT': 5.0  # Same as asset, should be ignored
            }
        }
        
        orders = strategy._create_dust_sell_orders(exposure_data)
        
        assert isinstance(orders, list)
        assert len(orders) == 2  # ETH and BTC, but not USDT (same as asset)
        
        # Check ETH order
        eth_order = orders[0]
        assert isinstance(eth_order, Order)
        assert eth_order.venue == 'uniswap'
        assert eth_order.operation == OrderOperation.SWAP
        assert eth_order.token_in == 'ETH'
        assert eth_order.token_out == 'USDT'
        assert eth_order.amount == 0.1
        assert eth_order.execution_mode == 'sequential'
        assert eth_order.strategy_intent == 'sell_dust'
        
        # Check BTC order
        btc_order = orders[1]
        assert isinstance(btc_order, Order)
        assert btc_order.venue == 'uniswap'
        assert btc_order.operation == OrderOperation.SWAP
        assert btc_order.token_in == 'BTC'
        assert btc_order.token_out == 'USDT'
        assert btc_order.amount == 0.01
        assert btc_order.execution_mode == 'sequential'
        assert btc_order.strategy_intent == 'sell_dust'
    
    def test_calculate_target_position(self, strategy):
        """Test target position calculation."""
        equity = 10000.0
        
        target = strategy.calculate_target_position(equity)
        
        assert target['supply'] == 10000.0
        assert target['borrow'] == 0.0  # Pure lending doesn't borrow
        assert target['equity'] == 10000.0
    
    def test_strategy_initialization(self, strategy_config, mock_dependencies):
        """Test strategy initialization."""
        risk_monitor, position_monitor, event_engine = mock_dependencies
        
        strategy = PureLendingStrategy(strategy_config, risk_monitor, position_monitor, event_engine)
        
        assert strategy.share_class == 'USDT'
        assert strategy.asset == 'USDT'
        assert strategy.lending_venues == ['aave', 'morpho']
        assert strategy.risk_monitor == risk_monitor
        assert strategy.position_monitor == position_monitor
        assert strategy.event_engine == event_engine
