"""
Unit tests for ETH Basis Strategy.

Tests the 5 standard actions, instrument validation, and order generation.
"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from pathlib import Path

from backend.src.basis_strategy_v1.core.strategies.eth_basis_strategy import ETHBasisStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation
from backend.src.basis_strategy_v1.core.models.venues import Venue


@pytest.fixture
def mock_config():
    """Mock configuration for ETH Basis strategy."""
    return {
    'mode': 'eth_basis',
    'share_class': 'USDT',
    'max_leverage': 1.0,   # No leverage for basis trading
    'eth_allocation': 0.8,  # 80% allocation to ETH
    'component_config': {
            'position_monitor': {
                'position_subscriptions': [
                    'wallet:BaseToken:USDT',
                    'wallet:BaseToken:ETH',
                    'binance:BaseToken:ETH',
                    'binance:Perp:ETHUSDT'
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
    """Create ETH Basis strategy instance."""
    return ETHBasisStrategy(
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


class TestETHBasisStrategyInit:
    """Test strategy initialization and validation."""
    
    def test_init_validates_required_instruments(self, mock_config, mock_components):
        """Test that strategy validates required instruments are in position_subscriptions."""
        # Test with missing required instrument
        mock_config['component_config']['position_monitor']['position_subscriptions'] = [
            'wallet:BaseToken:USDT',
            'binance:BaseToken:ETH'
            # Missing binance:Perp:ETHUSDT
        ]
        
        with pytest.raises(ValueError, match="Required instrument wallet:BaseToken:ETH not in position_subscriptions"):
            ETHBasisStrategy(
                config=mock_config,
                data_provider=mock_components['data_provider'],
                exposure_monitor=mock_components['exposure_monitor'],
                position_monitor=mock_components['position_monitor'],
                risk_monitor=mock_components['risk_monitor'],
                utility_manager=mock_components['utility_manager']
            )
    
    def test_init_validates_instruments_in_registry(self, mock_config, mock_components):
        """Test that strategy validates instruments exist in registry."""
        # Test with invalid instrument key format
        mock_config['component_config']['position_monitor']['position_subscriptions'] = [
            'wallet:BaseToken:USDT',
            'binance:BaseToken:ETH',
            'invalid:format:ETHUSDT'  # Invalid format
        ]
        
        with pytest.raises(ValueError, match="Required instrument wallet:BaseToken:ETH not in position_subscriptions"):
            ETHBasisStrategy(
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
        assert strategy.entry_instrument == 'wallet:BaseToken:ETH'
        assert strategy.spot_instrument == 'binance:BaseToken:ETH'
        assert strategy.perp_instrument == 'binance:Perp:ETHUSDT'
        assert len(strategy.available_instruments) == 4


class TestETHBasisStrategyActions:
    """Test the 5 standard strategy actions."""
    
    def test_generate_orders_entry_full(self, strategy):
        """Test generate_orders method returns orders based on strategy logic."""
        # Mock the required parameters for generate_orders
        timestamp = pd.Timestamp.now()
        exposure = {'positions': {}, 'equity': 3000.0}
        risk_assessment = {'liquidation_risk': 0.0}
        market_data = {'prices': {'ETH': 3000.0}, 'rates': {'eth_funding': 0.01}}
        
        # Mock the internal methods that generate_orders calls
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy.generate_orders(timestamp, exposure, risk_assessment, market_data)
            
            # Should return a list of orders (may be empty based on strategy logic)
            assert isinstance(orders, list)
    
    def test_create_entry_full_orders(self, strategy):
        """Test _create_entry_full_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(3000.0)
            
            # Should have spot buy and perp short orders
            assert len(orders) == 2
            
            # Check spot buy order
            spot_order = next(o for o in orders if o.operation == OrderOperation.SPOT_TRADE)
            assert spot_order.venue == Venue.BINANCE
            assert spot_order.pair == 'ETHUSDT'
            assert spot_order.side == 'BUY'
            assert spot_order.amount == 1.0  # 3000 USDT / 3000 ETH price = 1 ETH
            assert spot_order.source_venue == Venue.WALLET
            assert spot_order.target_venue == Venue.BINANCE
            assert spot_order.source_token == 'USDT'
            assert spot_order.target_token == 'ETH'
            assert spot_order.strategy_intent == 'entry_full'
            assert spot_order.strategy_id == 'eth_basis'
            
            # Check perp short order
            perp_order = next(o for o in orders if o.operation == OrderOperation.PERP_TRADE)
            assert perp_order.venue == Venue.BINANCE
            assert perp_order.pair == 'ETHUSDT'
            assert perp_order.side == 'SELL'
            assert perp_order.amount == 1.0  # Same size as spot
            assert perp_order.strategy_intent == 'entry_full'
            assert perp_order.strategy_id == 'eth_basis'
    
    def test_create_entry_partial_orders(self, strategy):
        """Test _create_entry_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_partial_orders(1500.0)
            
            assert len(orders) == 2  # Spot buy + perp short
            for order in orders:
                assert order.strategy_intent == 'entry_partial'
                assert order.amount == 0.5  # 1500 USDT / 3000 ETH price = 0.5 ETH
    
    def test_create_exit_full_orders(self, strategy):
        """Test _create_exit_full_orders method."""
        # Mock position monitor to return positions
        strategy.position_monitor.get_current_position.return_value = {
            'binance:BaseToken:ETH': 1.0,  # Spot position
            'binance:Perp:ETHUSDT': -1.0   # Perp position (short)
        }
        
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_exit_full_orders(3000.0)
            
            # Should have spot sell and perp buy orders
            assert len(orders) == 2
            
            # Check spot sell order
            spot_order = next(o for o in orders if o.operation == OrderOperation.SPOT_TRADE)
            assert spot_order.venue == Venue.BINANCE
            assert spot_order.pair == 'ETHUSDT'
            assert spot_order.side == 'SELL'
            assert spot_order.amount == 1.0
            assert spot_order.strategy_intent == 'exit_full'
            
            # Check perp buy order
            perp_order = next(o for o in orders if o.operation == OrderOperation.PERP_TRADE)
            assert perp_order.venue == Venue.BINANCE
            assert perp_order.pair == 'ETHUSDT'
            assert perp_order.side == 'BUY'
            assert perp_order.amount == 1.0
            assert perp_order.strategy_intent == 'exit_full'
    
    def test_create_exit_partial_orders(self, strategy):
        """Test _create_exit_partial_orders method."""
        # Mock position monitor to return positions
        strategy.position_monitor.get_current_position.return_value = {
            'binance:BaseToken:ETH': 1.0,  # Spot position
            'binance:Perp:ETHUSDT': -1.0   # Perp position (short)
        }
        
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_exit_partial_orders(1500.0)
            
            assert len(orders) == 2  # Spot sell + perp buy
            for order in orders:
                assert order.strategy_intent == 'exit_partial'
                assert order.amount == 0.5  # 1500 USDT / 3000 ETH price = 0.5 ETH
    
    def test_create_dust_sell_orders(self, strategy):
        """Test _create_dust_sell_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_dust_sell_orders(3000.0)
            
            # Basis strategies don't generate dust
            assert len(orders) == 0


class TestETHBasisStrategyHelpers:
    """Test helper methods."""
    
    def test_calculate_target_position(self, strategy):
        """Test calculate_target_position method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            target = strategy.calculate_target_position(3000.0)
            
            assert 'eth_balance' in target
            assert 'eth_perpetual_short' in target
            assert 'total_equity' in target
            assert target['eth_balance'] == 0.8  # 3000 USDT * 0.8 allocation / 3000 ETH price = 0.8 ETH
            assert target['eth_perpetual_short'] == -0.8  # Short position
            assert target['total_equity'] == 3000.0  # Current equity
    
    def test_get_asset_price(self, strategy):
        """Test _get_asset_price method."""
        price = strategy._get_asset_price()
        assert price == 3000.0  # Mock price from implementation
    
    def test_order_operation_id_format(self, strategy):
        """Test that operation_id format is correct (unix microseconds)."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(3000.0)
            
            for order in orders:
                # Check operation_id format: operation_type_timestamp
                parts = order.operation_id.split('_')
                assert len(parts) >= 2
                # Should start with operation type (spot_buy, spot_sell, perp_buy, perp_sell)
                assert parts[0] in ['spot', 'perp']
                # Last part should be a timestamp (numeric)
                assert parts[-1].isdigit()
                # Should be unix microseconds (13+ digits)
                assert len(parts[-1]) >= 13
    
    def test_order_has_required_fields(self, strategy):
        """Test that all Order objects have required fields."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(3000.0)
            
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


class TestETHBasisStrategyErrorHandling:
    """Test error handling scenarios."""
    
    def test_create_orders_with_zero_equity(self, strategy):
        """Test order creation with zero equity."""
        orders = strategy._create_entry_full_orders(0.0)
        assert len(orders) == 0
    
    def test_create_orders_with_negative_equity(self, strategy):
        """Test order creation with negative equity."""
        orders = strategy._create_entry_full_orders(-3000.0)
        assert len(orders) == 0
    
    def test_get_asset_price_error_handling(self, strategy):
        """Test error handling in _get_asset_price."""
        with patch.object(strategy, '_get_asset_price', side_effect=Exception("Price fetch failed")):
            orders = strategy._create_entry_full_orders(3000.0)
            # Should handle error gracefully and return empty list
            assert len(orders) == 0
