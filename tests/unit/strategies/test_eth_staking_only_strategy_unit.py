"""
Unit tests for ETH Staking Only Strategy.

Tests the 5 standard actions, instrument validation, and order generation.
"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from pathlib import Path

from backend.src.basis_strategy_v1.core.strategies.eth_staking_only_strategy import ETHStakingOnlyStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation
from backend.src.basis_strategy_v1.core.models.venues import Venue


@pytest.fixture
def mock_config():
    """Mock configuration for ETH Staking Only strategy."""
    return {
        'mode': 'eth_staking_only',
        'share_class': 'ETH',
        'max_leverage': 1.0,   # No leverage for staking
        'lst_type': 'weeth',   # Required for ETH strategies
        'staking_protocol': 'etherfi',  # Required for ETH strategies
        'component_config': {
            'position_monitor': {
                'position_subscriptions': [
                    'wallet:BaseToken:ETH',
                    'etherfi:LST:weETH',
                    'wallet:BaseToken:EIGEN',
                    'wallet:BaseToken:ETHFI'
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
    """Create ETH Staking Only strategy instance."""
    return ETHStakingOnlyStrategy(
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


class TestETHStakingOnlyStrategyInit:
    """Test strategy initialization and validation."""
    
    def test_init_validates_required_instruments(self, mock_config, mock_components):
        """Test that strategy validates required instruments are in position_subscriptions."""
        # Test with missing required instrument
        mock_config['component_config']['position_monitor']['position_subscriptions'] = [
            'wallet:BaseToken:ETH'
            # Missing etherfi:LST:weETH
        ]
        
        with pytest.raises(ValueError, match="Required instrument etherfi:LST:weETH not in position_subscriptions"):
            ETHStakingOnlyStrategy(
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
            'wallet:BaseToken:ETH',
            'wallet:BaseToken:EIGEN',
            'wallet:BaseToken:ETHFI'
        ]

        with pytest.raises(ValueError, match="Required instrument etherfi:LST:weETH not in position_subscriptions"):
            ETHStakingOnlyStrategy(
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
        assert strategy.staking_instrument == 'etherfi:LST:weETH'
        assert len(strategy.available_instruments) == 4


class TestETHStakingOnlyStrategyActions:
    """Test the 5 standard strategy actions."""
    
    def test_generate_orders_entry_full(self, strategy):
        """Test entry_full order generation."""
        with patch.object(strategy, '_create_entry_full_orders') as mock_create:
            mock_orders = [Mock()]
            mock_create.return_value = mock_orders
            
            # Mock exposure with total_exposure and empty positions to trigger entry_full
            exposure = {
                'total_exposure': 1.0,
                'positions': {}
            }
            
            orders = strategy.generate_orders(
                timestamp=pd.Timestamp.now(),
                exposure=exposure,
                risk_assessment={},
                pnl={},
                market_data={}
            )
            
            # Verify the method was called with correct parameters
            mock_create.assert_called_once_with(1.0)
            assert orders == mock_orders
    
    def test_create_entry_full_orders(self, strategy):
        """Test _create_entry_full_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(1.0)
            
            assert len(orders) == 1
            order = orders[0]
            assert isinstance(order, Order)
            assert order.venue == Venue.ETHERFI
            assert order.operation == OrderOperation.STAKE
            assert order.token_in == 'ETH'
            assert order.token_out == 'weeth'
            assert order.amount == 1.0 / 3000.0  # 1 ETH worth of weETH
            assert order.source_venue == Venue.WALLET
            assert order.target_venue == Venue.ETHERFI
            assert order.source_token == 'ETH'
            assert order.target_token == 'weeth'
            assert order.strategy_intent == 'entry_full'
            assert order.strategy_id == 'eth_staking_only'
    
    def test_create_entry_partial_orders(self, strategy):
        """Test _create_entry_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_partial_orders(0.5)
            
            assert len(orders) == 1
            order = orders[0]
            assert isinstance(order, Order)
            assert order.venue == Venue.ETHERFI
            assert order.operation == OrderOperation.STAKE
            assert order.amount == 0.5 / 3000.0
            assert order.strategy_intent == 'entry_partial'
    
    def test_create_exit_full_orders(self, strategy):
        """Test _create_exit_full_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0), \
             patch.object(strategy.position_monitor, 'get_current_position', return_value={
                 'weeth_balance': 1.0
             }):
            orders = strategy._create_exit_full_orders(1.0)
            
            assert len(orders) == 1
            order = orders[0]
            assert isinstance(order, Order)
            assert order.venue == Venue.ETHERFI
            assert order.operation == OrderOperation.UNSTAKE
            assert order.token_in == 'weeth'
            assert order.token_out == 'ETH'
            assert order.strategy_intent == 'exit_full'
    
    def test_create_exit_partial_orders(self, strategy):
        """Test _create_exit_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0), \
             patch.object(strategy.position_monitor, 'get_current_position', return_value={
                 'weeth_balance': 1.0
             }):
            orders = strategy._create_exit_partial_orders(0.5)
            
            assert len(orders) == 1
            order = orders[0]
            assert isinstance(order, Order)
            assert order.venue == Venue.ETHERFI
            assert order.operation == OrderOperation.UNSTAKE
            assert order.strategy_intent == 'exit_partial'
    
    def test_create_dust_sell_orders(self, strategy):
        """Test _create_dust_sell_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            dust_tokens = {'EIGEN': 1.0, 'ETHFI': 1.0}
            orders = strategy._create_dust_sell_orders(dust_tokens)
            
            # Should have orders for EIGEN and ETHFI dust
            assert len(orders) == 2
            
            # Check EIGEN dust order
            eigen_order = next(o for o in orders if o.token_in == 'EIGEN')
            assert eigen_order.venue == Venue.UNISWAP
            assert eigen_order.operation == OrderOperation.SWAP
            assert eigen_order.token_out == 'ETH'
            assert eigen_order.strategy_intent == 'dust_sell'
            
            # Check ETHFI dust order
            ethfi_order = next(o for o in orders if o.token_in == 'ETHFI')
            assert ethfi_order.venue == Venue.UNISWAP
            assert ethfi_order.operation == OrderOperation.SWAP
            assert ethfi_order.token_out == 'ETH'
            assert ethfi_order.strategy_intent == 'dust_sell'


class TestETHStakingOnlyStrategyHelpers:
    """Test helper methods."""
    
    def test_calculate_target_position(self, strategy):
        """Test calculate_target_position method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            target = strategy.calculate_target_position(1.0)
            
            assert 'etherfi:BaseToken:WEETH' in target
            assert 'wallet:BaseToken:ETH' in target
            assert target['etherfi:BaseToken:WEETH'] == 0.0003333333333333333  # 1.0 / 3000.0
            assert target['wallet:BaseToken:ETH'] == 1.0  # All ETH staked
    
    def test_order_operation_id_format(self, strategy):
        """Test that operation_id format is correct (unix microseconds)."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(1.0)
            
            for order in orders:
                # Check operation_id format: operation_timestamp
                parts = order.operation_id.split('_')
                assert len(parts) >= 2
                assert parts[0] == 'stake'
                # Last part should be a timestamp (numeric)
                assert parts[-1].isdigit()
                # Should be unix microseconds (13+ digits)
                assert len(parts[-1]) >= 13
    
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


class TestETHStakingOnlyStrategyErrorHandling:
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
        with patch.object(strategy, '_get_asset_price', side_effect=Exception("Price fetch failed")):
            orders = strategy._create_entry_full_orders(1.0)
            # Should handle error gracefully and return empty list
            assert len(orders) == 0
