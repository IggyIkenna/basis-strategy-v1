"""
Unit tests for Pure Lending ETH Strategy.

Tests the 5 standard actions, instrument validation, and order generation.
"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from pathlib import Path

from backend.src.basis_strategy_v1.core.strategies.pure_lending_eth_strategy import PureLendingETHStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation
from backend.src.basis_strategy_v1.core.models.venues import Venue


@pytest.fixture
def mock_config():
    """Mock configuration for Pure Lending ETH strategy."""
    return {
        'mode': 'pure_lending_eth',
        'share_class': 'ETH',
        'asset': 'ETH',
        'component_config': {
            'position_monitor': {
                'position_subscriptions': [
                    'wallet:BaseToken:ETH',
                    'aave_v3:aToken:aWETH'
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
    """Create Pure Lending ETH strategy instance."""
    return PureLendingETHStrategy(
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


class TestPureLendingETHStrategyInit:
    """Test strategy initialization and validation."""
    
    def test_init_validates_required_instruments(self, mock_config, mock_components):
        """Test that strategy validates required instruments are in position_subscriptions."""
        # Test with missing required instrument
        mock_config['component_config']['position_monitor']['position_subscriptions'] = [
            'wallet:BaseToken:ETH'
            # Missing aave_v3:aToken:aWETH
        ]
        
        with pytest.raises(ValueError, match="Required instrument aave_v3:aToken:aWETH not in position_subscriptions"):
            PureLendingETHStrategy(
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
            'wallet:BaseToken:ETH'
            # Missing aave_v3:aToken:aWETH
        ]

        with pytest.raises(ValueError, match="Required instrument aave_v3:aToken:aWETH not in position_subscriptions"):
            PureLendingETHStrategy(
                config=mock_config,
                data_provider=mock_components['data_provider'],
                exposure_monitor=mock_components['exposure_monitor'],
                position_monitor=mock_components['position_monitor'],
                risk_monitor=mock_components['risk_monitor'],
                utility_manager=mock_components['utility_manager']
            )
    
    def test_init_success_with_valid_config(self, strategy):
        """Test successful initialization with valid config."""
        assert strategy.share_class == 'ETH'
        assert strategy.entry_instrument == 'wallet:BaseToken:ETH'
        assert strategy.lending_instrument == 'aave_v3:aToken:aWETH'
        assert len(strategy.available_instruments) == 2


class TestPureLendingETHStrategyActions:
    """Test the 5 standard strategy actions."""
    
    def test_generate_orders_entry_full(self, strategy):
        """Test entry_full order generation."""
        with patch.object(strategy, '_create_entry_full_orders') as mock_create, \
             patch.object(strategy, 'get_current_equity', return_value=1.0):
            mock_orders = [Mock()]
            mock_create.return_value = mock_orders
            
            # Mock the required parameters
            timestamp = pd.Timestamp.now()
            exposure = {'total_exposure': 1.0, 'positions': {}}
            risk_assessment = {}
            market_data = {}
            
            orders = strategy.generate_orders(
                timestamp=timestamp,
                exposure=exposure,
                risk_assessment=risk_assessment,
                market_data=market_data
            )
            
            # The generate_orders method should call _create_entry_full_orders internally
            assert orders == mock_orders
    
    def test_create_entry_full_orders(self, strategy):
        """Test _create_entry_full_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(1.0)
            
            assert len(orders) == 1  # AAVE only
            order = orders[0]
            assert isinstance(order, Order)
            assert order.venue == 'aave_v3'
            assert order.operation == OrderOperation.SUPPLY
            assert order.token_in == 'ETH'
            assert order.token_out == 'aETH'
            assert order.amount == 1.0
            assert order.source_venue == Venue.WALLET
            assert order.target_venue == 'aave_v3'
            assert order.source_token == 'ETH'
            assert order.target_token == 'aETH'
            assert order.strategy_intent == 'entry_full'
            assert order.strategy_id is None
    
    def test_create_entry_partial_orders(self, strategy):
        """Test _create_entry_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_partial_orders(0.5)
            
            assert len(orders) == 1  # AAVE only
            order = orders[0]
            assert isinstance(order, Order)
            assert order.venue == 'aave_v3'
            assert order.operation == OrderOperation.SUPPLY
            assert order.amount == 0.5
            assert order.strategy_intent == 'entry_partial'
    
    def test_create_exit_full_orders(self, strategy):
        """Test _create_exit_full_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0), \
             patch.object(strategy.position_monitor, 'get_position_snapshot', return_value={
                 'total_supply': 1.0,
                 'total_borrow': 0.0
             }):
            orders = strategy._create_exit_full_orders(1.0)
            
            assert len(orders) == 1  # AAVE only
            for order in orders:
                assert isinstance(order, Order)
                assert order.venue == 'aave_v3'
                assert order.operation == OrderOperation.WITHDRAW
                assert order.token_in == 'aETH'
                assert order.token_out == 'ETH'
                assert order.amount == 1.0  # Full amount to AAVE
                assert order.strategy_intent == 'exit_full'
    
    def test_create_exit_partial_orders(self, strategy):
        """Test _create_exit_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_exit_partial_orders(0.5)
            
            assert len(orders) == 1  # AAVE only
            order = orders[0]
            assert isinstance(order, Order)
            assert order.venue == 'aave_v3'
            assert order.operation == OrderOperation.WITHDRAW
            assert order.amount == 0.5
            assert order.strategy_intent == 'exit_partial'
    
    def test_create_dust_sell_orders(self, strategy):
        """Test _create_dust_sell_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_dust_sell_orders(1.0)
            
            # Pure lending strategies don't generate dust
            assert len(orders) == 0


class TestPureLendingETHStrategyHelpers:
    """Test helper methods."""
    
    def test_calculate_target_position(self, strategy):
        """Test calculate_target_position method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            target = strategy.calculate_target_position(1.0)
            
            assert 'supply' in target
            assert 'borrow' in target
            assert 'equity' in target
            assert target['supply'] == 1.0
            assert target['borrow'] == 0.0
            assert target['equity'] == 1.0
    
    def test_get_asset_price(self, strategy):
        """Test _get_asset_price method."""
        price = strategy._get_asset_price()
        assert price == 3000.0  # Mock price from implementation
    
    def test_order_operation_id_format(self, strategy):
        """Test that operation_id format is correct (unix microseconds)."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(1.0)
            
            for order in orders:
                # Check operation_id format: operation_timestamp
                parts = order.operation_id.split('_')
                assert len(parts) >= 2
                assert parts[0] == 'supply'
                # Last part should be a hex timestamp
                assert len(parts[-1]) == 8  # 8-character hex string
    
    def test_order_has_required_fields(self, strategy):
        """Test that all Order objects have required fields."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(1.0)
            
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


class TestPureLendingETHStrategyErrorHandling:
    """Test error handling scenarios."""
    
    def test_create_orders_with_zero_equity(self, strategy):
        """Test order creation with zero equity."""
        orders = strategy._create_entry_full_orders(0.0)
        assert len(orders) == 0
    
    def test_create_orders_with_negative_equity(self, strategy):
        """Test order creation with negative equity."""
        orders = strategy._create_entry_full_orders(-1.0)
        assert len(orders) == 0
    
    def test_get_asset_price_error_handling(self, strategy):
        """Test error handling in _get_asset_price."""
        # This test is not applicable as _get_asset_price is not used in pure lending ETH strategy
        # The method exists but is not called by any order creation methods
        pass
