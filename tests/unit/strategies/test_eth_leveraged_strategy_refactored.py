"""
Unit tests for refactored ETHLeveragedStrategy using Order model.

Tests the new Order-based interface instead of StrategyAction.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock

from backend.src.basis_strategy_v1.core.strategies.eth_leveraged_strategy import ETHLeveragedStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation


class TestETHLeveragedStrategyRefactored:
    """Test refactored ETHLeveragedStrategy with Order model."""
    
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
            'share_class': 'ETH',
            'asset': 'ETH',
            'eth_allocation': 0.8,
            'leverage_multiplier': 2.0,
            'lst_type': 'wstETH',
            'staking_protocol': 'lido',
            'hedge_allocation': 0.1
        }
    
    @pytest.fixture
    def strategy(self, strategy_config, mock_dependencies):
        """Create ETHLeveragedStrategy instance."""
        risk_monitor, position_monitor, event_engine = mock_dependencies
        return ETHLeveragedStrategy(strategy_config, risk_monitor, position_monitor, event_engine)
    
    def test_make_strategy_decision_no_equity(self, strategy):
        """Test strategy decision when no equity."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00')
        market_data = {}
        exposure_data = {'total_exposure': 0.0, 'positions': {}}
        risk_assessment = {}
        
        orders = strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return empty list when no equity
        assert isinstance(orders, list)
        assert len(orders) == 0
    
    def test_make_strategy_decision_with_equity_no_position(self, strategy):
        """Test strategy decision when equity exists but no position."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00')
        market_data = {}
        exposure_data = {
            'total_exposure': 10000.0,
            'positions': {}  # No existing position
        }
        risk_assessment = {}
        
        orders = strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return entry full orders
        assert isinstance(orders, list)
        assert len(orders) >= 2  # At least buy ETH and stake orders
        
        # Check that orders are atomic group
        atomic_orders = [o for o in orders if o.is_atomic()]
        assert len(atomic_orders) >= 2  # Buy and stake should be atomic
        
        # Check first order (buy ETH)
        buy_order = orders[0]
        assert isinstance(buy_order, Order)
        assert buy_order.venue == 'binance'
        assert buy_order.operation == OrderOperation.SPOT_TRADE
        assert buy_order.pair == 'ETH/USDT'
        assert buy_order.side == 'BUY'
        assert buy_order.execution_mode == 'atomic'
        assert buy_order.strategy_intent == 'entry_full'
        assert buy_order.strategy_id == 'eth_leveraged'
    
    def test_make_strategy_decision_existing_position(self, strategy):
        """Test strategy decision when already has position."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00')
        market_data = {}
        exposure_data = {
            'total_exposure': 10000.0,
            'positions': {'wsteth_balance': 2.0}  # Already staked
        }
        risk_assessment = {}
        
        orders = strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return empty list when no dust tokens
        assert isinstance(orders, list)
        assert len(orders) == 0
    
    def test_make_strategy_decision_with_dust_tokens(self, strategy):
        """Test strategy decision with dust tokens to sell."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00')
        market_data = {}
        exposure_data = {
            'total_exposure': 10000.0,
            'positions': {'wsteth_balance': 2.0},
            'dust_tokens': {'BTC': 0.1, 'USDT': 50.0}
        }
        risk_assessment = {}
        
        orders = strategy.make_strategy_decision(
            timestamp, 'scheduled', market_data, exposure_data, risk_assessment
        )
        
        # Should return dust sell orders
        assert isinstance(orders, list)
        assert len(orders) == 2  # BTC and USDT dust orders
        
        # Check BTC order
        btc_order = orders[0]
        assert isinstance(btc_order, Order)
        assert btc_order.venue == 'binance'
        assert btc_order.operation == OrderOperation.SPOT_TRADE
        assert btc_order.pair == 'BTC/USDT'
        assert btc_order.side == 'SELL'
        assert btc_order.amount == 0.1
        assert btc_order.strategy_intent == 'sell_dust'
    
    def test_create_entry_full_orders(self, strategy):
        """Test creating entry full orders."""
        equity = 10000.0
        
        orders = strategy._create_entry_full_orders(equity)
        
        assert isinstance(orders, list)
        assert len(orders) >= 2  # At least buy ETH and stake orders
        
        # Check atomic group ID is consistent
        atomic_orders = [o for o in orders if o.is_atomic()]
        if atomic_orders:
            group_id = atomic_orders[0].atomic_group_id
            for order in atomic_orders:
                assert order.atomic_group_id == group_id
        
        # Check buy ETH order
        buy_order = next((o for o in orders if o.operation == OrderOperation.SPOT_TRADE and o.side == 'BUY'), None)
        assert buy_order is not None
        assert buy_order.venue == 'binance'
        assert buy_order.pair == 'ETH/USDT'
        assert buy_order.execution_mode == 'atomic'
        assert buy_order.sequence_in_group == 1
        
        # Check stake order
        stake_order = next((o for o in orders if o.operation == OrderOperation.STAKE), None)
        assert stake_order is not None
        assert stake_order.venue == 'lido'
        assert stake_order.token_in == 'ETH'
        assert stake_order.token_out == 'wstETH'
        assert stake_order.execution_mode == 'atomic'
        assert stake_order.sequence_in_group == 2
    
    def test_create_entry_partial_orders(self, strategy):
        """Test creating entry partial orders."""
        equity_delta = 5000.0
        
        orders = strategy._create_entry_partial_orders(equity_delta)
        
        assert isinstance(orders, list)
        assert len(orders) >= 2  # At least buy ETH and stake orders
        
        # Check all orders have partial intent
        for order in orders:
            assert order.strategy_intent == 'entry_partial'
            assert order.strategy_id == 'eth_leveraged'
    
    def test_create_exit_full_orders(self, strategy, mock_dependencies):
        """Test creating exit full orders."""
        _, position_monitor, _ = mock_dependencies
        
        # Mock position snapshot
        position_monitor.get_current_position.return_value = {
            'wsteth_balance': 2.0,
            'eth_perpetual_short': -1.0
        }
        
        equity = 10000.0
        orders = strategy._create_exit_full_orders(equity)
        
        assert isinstance(orders, list)
        assert len(orders) >= 3  # Close hedge, unstake, sell ETH
        
        # Check close hedge order
        hedge_order = next((o for o in orders if o.operation == OrderOperation.PERP_TRADE and o.side == 'LONG'), None)
        assert hedge_order is not None
        assert hedge_order.venue == 'bybit'
        assert hedge_order.pair == 'ETHUSDT'
        assert hedge_order.amount == 1.0  # abs(-1.0)
        assert hedge_order.strategy_intent == 'exit_full'
        
        # Check unstake order
        unstake_order = next((o for o in orders if o.operation == OrderOperation.UNSTAKE), None)
        assert unstake_order is not None
        assert unstake_order.venue == 'lido'
        assert unstake_order.token_in == 'wstETH'
        assert unstake_order.token_out == 'ETH'
        assert unstake_order.amount == 2.0
        assert unstake_order.strategy_intent == 'exit_full'
        
        # Check sell ETH order
        sell_order = next((o for o in orders if o.operation == OrderOperation.SPOT_TRADE and o.side == 'SELL'), None)
        assert sell_order is not None
        assert sell_order.venue == 'binance'
        assert sell_order.pair == 'ETH/USDT'
        assert sell_order.amount == 2.0
        assert sell_order.strategy_intent == 'exit_full'
    
    def test_create_exit_partial_orders(self, strategy, mock_dependencies):
        """Test creating exit partial orders."""
        _, position_monitor, _ = mock_dependencies
        
        # Mock position snapshot
        position_monitor.get_current_position.return_value = {
            'wsteth_balance': 2.0,
            'eth_perpetual_short': -1.0
        }
        
        equity_delta = 5000.0
        orders = strategy._create_exit_partial_orders(equity_delta)
        
        assert isinstance(orders, list)
        assert len(orders) >= 3  # Close hedge, unstake, sell ETH
        
        # Check all orders have partial exit intent
        for order in orders:
            assert order.strategy_intent == 'exit_partial'
            assert order.strategy_id == 'eth_leveraged'
    
    def test_create_dust_sell_orders(self, strategy):
        """Test creating dust sell orders."""
        dust_tokens = {
            'ETH': 0.5,
            'BTC': 0.1,
            'USDT': 100.0,
            'wstETH': 0.2
        }
        
        orders = strategy._create_dust_sell_orders(dust_tokens)
        
        assert isinstance(orders, list)
        assert len(orders) == 4  # ETH, BTC, USDT, wstETH
        
        # Check ETH order
        eth_order = next((o for o in orders if o.operation == OrderOperation.SPOT_TRADE and o.pair == 'ETH/USDT'), None)
        assert eth_order is not None
        assert eth_order.side == 'SELL'
        assert eth_order.amount == 0.5
        assert eth_order.strategy_intent == 'sell_dust'
        
        # Check BTC order
        btc_order = next((o for o in orders if o.operation == OrderOperation.SPOT_TRADE and o.pair == 'BTC/USDT'), None)
        assert btc_order is not None
        assert btc_order.side == 'SELL'
        assert btc_order.amount == 0.1
        assert btc_order.strategy_intent == 'sell_dust'
        
        # Check USDT order (transfer)
        usdt_order = next((o for o in orders if o.operation == OrderOperation.TRANSFER and o.token == 'USDT'), None)
        assert usdt_order is not None
        assert usdt_order.amount == 100.0
        assert usdt_order.strategy_intent == 'sell_dust'
        
        # Check wstETH order (unstake + sell atomic group)
        unstake_orders = [o for o in orders if o.operation == OrderOperation.UNSTAKE and o.token_in == 'wstETH']
        assert len(unstake_orders) == 1
        unstake_order = unstake_orders[0]
        assert unstake_order.amount == 0.2
        assert unstake_order.strategy_intent == 'sell_dust'
        assert unstake_order.is_atomic()
    
    def test_calculate_target_position(self, strategy):
        """Test target position calculation."""
        equity = 10000.0
        
        target = strategy.calculate_target_position(equity)
        
        # Check leveraged equity calculation
        expected_leveraged_equity = equity * strategy.leverage_multiplier
        assert target['leveraged_equity'] == expected_leveraged_equity
        
        # Check ETH allocation
        expected_eth_target = expected_leveraged_equity * strategy.eth_allocation
        expected_eth_amount = expected_eth_target / strategy._get_asset_price()
        assert target['wsteth_balance'] == expected_eth_amount
        
        # Check hedge allocation
        expected_hedge_target = expected_leveraged_equity * strategy.hedge_allocation
        expected_hedge_amount = expected_hedge_target / strategy._get_asset_price()
        assert target['eth_perpetual_short'] == -expected_hedge_amount  # Negative for short
    
    def test_get_asset_price(self, strategy):
        """Test asset price retrieval."""
        price = strategy._get_asset_price()
        assert isinstance(price, float)
        assert price > 0
        assert price == 3000.0  # Mock price
    
    def test_strategy_initialization(self, strategy_config, mock_dependencies):
        """Test strategy initialization."""
        risk_monitor, position_monitor, event_engine = mock_dependencies
        
        strategy = ETHLeveragedStrategy(strategy_config, risk_monitor, position_monitor, event_engine)
        
        assert strategy.share_class == 'ETH'
        assert strategy.asset == 'ETH'
        assert strategy.eth_allocation == 0.8
        assert strategy.leverage_multiplier == 2.0
        assert strategy.lst_type == 'wstETH'
        assert strategy.staking_protocol == 'lido'
        assert strategy.hedge_allocation == 0.1
        assert strategy.risk_monitor == risk_monitor
        assert strategy.position_monitor == position_monitor
        assert strategy.event_engine == event_engine
    
    def test_strategy_initialization_missing_config(self, mock_dependencies):
        """Test strategy initialization with missing config."""
        risk_monitor, position_monitor, event_engine = mock_dependencies
        
        incomplete_config = {
            'share_class': 'ETH',
            'asset': 'ETH',
            'eth_allocation': 0.8
            # Missing required keys
        }
        
        with pytest.raises(KeyError):
            ETHLeveragedStrategy(incomplete_config, risk_monitor, position_monitor, event_engine)
    
    def test_atomic_group_consistency(self, strategy):
        """Test that atomic groups have consistent IDs and sequences."""
        equity = 10000.0
        orders = strategy._create_entry_full_orders(equity)
        
        atomic_orders = [o for o in orders if o.is_atomic()]
        if len(atomic_orders) > 1:
            # All atomic orders should have same group ID
            group_id = atomic_orders[0].atomic_group_id
            for order in atomic_orders:
                assert order.atomic_group_id == group_id
            
            # Sequences should be unique and sequential
            sequences = [o.sequence_in_group for o in atomic_orders]
            assert len(set(sequences)) == len(sequences)  # All unique
            assert sorted(sequences) == list(range(1, len(sequences) + 1))  # Sequential from 1
    
    def test_order_validation(self, strategy):
        """Test that created orders pass validation."""
        equity = 10000.0
        orders = strategy._create_entry_full_orders(equity)
        
        for order in orders:
            # Orders should be valid Pydantic models
            assert isinstance(order, Order)
            
            # Required fields should be present
            assert order.venue is not None
            assert order.operation is not None
            assert order.amount > 0
            assert order.strategy_intent is not None
            assert order.strategy_id == 'eth_leveraged'
    
    def test_get_strategy_info(self, strategy):
        """Test strategy info retrieval."""
        info = strategy.get_strategy_info()
        
        assert isinstance(info, dict)
        assert info['strategy_type'] == 'eth_leveraged'
        assert info['eth_allocation'] == 0.8
        assert info['leverage_multiplier'] == 2.0
        assert info['lst_type'] == 'wstETH'
        assert info['staking_protocol'] == 'lido'
        assert info['hedge_allocation'] == 0.1
        assert info['order_system'] == 'unified_order_trade'
        assert 'unified_order_trade' in info['description']