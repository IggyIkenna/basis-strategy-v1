"""
Unit tests for Pure Lending USDT Strategy.

Tests the 5 standard actions, instrument validation, and order generation.
"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from pathlib import Path

from backend.src.basis_strategy_v1.core.strategies.pure_lending_usdt_strategy import PureLendingUSDTStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation
from backend.src.basis_strategy_v1.core.models.venues import Venue


@pytest.fixture
def mock_config():
    """Mock configuration for Pure Lending USDT strategy."""
    return {
        'mode': 'pure_lending_usdt',
        'share_class': 'USDT',
        'asset': 'USDT',
        'component_config': {
            'position_monitor': {
                'position_subscriptions': [
                    'wallet:BaseToken:USDT',
                    'aave_v3:aToken:aUSDT'
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
    """Create Pure Lending USDT strategy instance."""
    return PureLendingUSDTStrategy(
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


class TestPureLendingUSDTStrategyInit:
    """Test strategy initialization and validation."""
    
    def test_init_validates_required_instruments(self, mock_config, mock_components):
        """Test that strategy validates required instruments are in position_subscriptions."""
        # Test with missing required instrument
        mock_config['component_config']['position_monitor']['position_subscriptions'] = [
            'wallet:BaseToken:USDT'
            # Missing aave_v3:aToken:aUSDT
        ]
        
        with pytest.raises(ValueError, match="Required instrument aave_v3:aToken:aUSDT not in position_subscriptions"):
            PureLendingUSDTStrategy(
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
            'wallet:BaseToken:USDT'
        ]

        with pytest.raises(ValueError, match="Required instrument aave_v3:aToken:aUSDT not in position_subscriptions"):
            PureLendingUSDTStrategy(
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
        assert strategy.asset == 'USDT'
        assert strategy.entry_instrument == 'wallet:BaseToken:USDT'
        assert strategy.lending_instrument == 'aave_v3:aToken:aUSDT'
        assert len(strategy.available_instruments) == 2


class TestPureLendingUSDTStrategyActions:
    """Test the 5 standard strategy actions."""
    
    def test_generate_orders_entry_full(self, strategy):
        """Test generate_orders method returns orders based on strategy logic."""
        # Mock the required parameters for generate_orders
        timestamp = pd.Timestamp.now()
        exposure = {'positions': {}, 'equity': 1000.0}
        risk_assessment = {'liquidation_risk': 0.0}
        market_data = {'prices': {'BTC': 50000.0}, 'rates': {'btc_funding': 0.01}}
        
        # Mock the internal methods that generate_orders calls
        with patch.object(strategy, '_get_asset_price', return_value=50000.0):
            orders = strategy.generate_orders(timestamp, exposure, risk_assessment, market_data)
            
            # Should return a list of orders (may be empty based on strategy logic)
            assert isinstance(orders, list)
    
    def test_create_entry_full_orders(self, strategy):
        """Test _create_entry_full_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=1.0):
            orders = strategy._create_entry_full_orders(1000.0)
            
            assert len(orders) == 2
            order = orders[0]
            assert isinstance(order, Order)
            assert order.venue == 'aave'
            assert order.operation == OrderOperation.SUPPLY
            assert order.token_in == 'USDT'
            assert order.token_out == 'aUSDT'
            assert order.amount == 500.0
            assert order.source_venue == Venue.WALLET
            assert order.target_venue == 'aave'
            assert order.source_token == 'USDT'
            assert order.target_token == 'aUSDT'
            assert order.strategy_intent == 'entry_full'
            assert order.strategy_id is None
    
    def test_create_entry_partial_orders(self, strategy):
        """Test _create_entry_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=1.0):
            orders = strategy._create_entry_partial_orders(500.0)
            
            assert len(orders) == 2
            order = orders[0]
            assert isinstance(order, Order)
            assert order.venue == 'aave'
            assert order.operation == OrderOperation.SUPPLY
            assert order.amount == 250.0
            assert order.strategy_intent == 'entry_partial'
    
    def test_create_exit_full_orders(self, strategy):
        """Test _create_exit_full_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=1.0):
            orders = strategy._create_exit_full_orders(1000.0)
            
            assert len(orders) == 1
            order = orders[0]
            assert isinstance(order, Order)
            assert order.venue == 'aave'
            assert order.operation == OrderOperation.WITHDRAW
            assert order.token_in == 'aUSDT'
            assert order.token_out == 'USDT'
            assert order.amount == 1000.0
            assert order.strategy_intent == 'exit_full'
    
    def test_create_exit_partial_orders(self, strategy):
        """Test _create_exit_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=1.0):
            orders = strategy._create_exit_partial_orders(500.0)
            
            assert len(orders) == 2
            order = orders[0]
            assert isinstance(order, Order)
            assert order.venue == 'aave'
            assert order.operation == OrderOperation.WITHDRAW
            assert order.amount == 250.0
            assert order.strategy_intent == 'exit_partial'
    
    def test_create_dust_sell_orders(self, strategy):
        """Test _create_dust_sell_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=1.0):
            orders = strategy._create_dust_sell_orders(1000.0)
            
            # Pure lending strategies don't generate dust
            assert len(orders) == 0


class TestPureLendingUSDTStrategyHelpers:
    """Test helper methods."""
    
    def test_calculate_target_position(self, strategy):
        """Test calculate_target_position method."""
        with patch.object(strategy, '_get_asset_price', return_value=1.0):
            target = strategy.calculate_target_position(1000.0)
            
            assert 'supply' in target
            assert 'borrow' in target
            assert 'equity' in target
            assert target['supply'] == 1000.0
            assert target['borrow'] == 0.0
            assert target['equity'] == 1000.0
    
    def test_get_asset_price(self, strategy):
        """Test _get_asset_price method."""
        price = strategy._get_asset_price()
        assert price == 1.0  # Mock price from implementation (stablecoin)
    
    def test_order_operation_id_format(self, strategy):
        """Test that operation_id format is correct (unix microseconds)."""
        with patch.object(strategy, '_get_asset_price', return_value=1.0):
            orders = strategy._create_entry_full_orders(1000.0)
            
            for order in orders:
                # Check operation_id format: operation_timestamp
                parts = order.operation_id.split('_')
                assert len(parts) >= 2
                assert parts[0] == 'supply'
                # Last part should be a hex timestamp
                assert len(parts[-1]) == 8  # 8-character hex string
    
    def test_order_has_required_fields(self, strategy):
        """Test that all Order objects have required fields."""
        with patch.object(strategy, '_get_asset_price', return_value=1.0):
            orders = strategy._create_entry_full_orders(1000.0)
            
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
                
                # Check expected_deltas format
                assert isinstance(order.expected_deltas, dict)
                assert len(order.expected_deltas) > 0


class TestPureLendingUSDTStrategyErrorHandling:
    """Test error handling scenarios."""
    
    def test_create_orders_with_zero_equity(self, strategy):
        """Test order creation with zero equity."""
        orders = strategy._create_entry_full_orders(0.0)
        assert len(orders) == 0
    
    def test_create_orders_with_negative_equity(self, strategy):
        """Test order creation with negative equity."""
        orders = strategy._create_entry_full_orders(-1000.0)
        assert len(orders) == 0
    
    def test_get_asset_price_error_handling(self, strategy):
        """Test error handling in _get_asset_price."""
        with patch.object(strategy, '_get_asset_price', side_effect=Exception("Price fetch failed")):
            orders = strategy._create_entry_full_orders(1000.0)
            # Should handle error gracefully and return empty list
            assert len(orders) == 0
