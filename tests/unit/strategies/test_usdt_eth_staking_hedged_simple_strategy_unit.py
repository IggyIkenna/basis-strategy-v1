"""
Unit tests for USDT ETH Staking Hedged Simple Strategy.

Tests the 5 standard actions, instrument validation, and order generation.
"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from pathlib import Path

from backend.src.basis_strategy_v1.core.strategies.usdt_eth_staking_hedged_simple_strategy import USDTETHStakingHedgedSimpleStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation
from backend.src.basis_strategy_v1.core.models.venues import Venue


@pytest.fixture
def mock_config():
    """Mock configuration for USDT ETH Staking Hedged Simple strategy."""
    return {
        'mode': 'usdt_eth_staking_hedged_simple',
        'share_class': 'USDT',
        'asset': 'ETH',
        'usdt_allocation': 0.5,  # 50% allocation to USDT
        'eth_allocation': 0.5,   # 50% allocation to ETH
        'leverage_multiplier': 1.0,  # No leverage
        'lst_type': 'etherfi',  # Liquid staking type
        'lending_protocol': 'aave_v3',  # Lending protocol
        'staking_protocol': 'etherfi',  # Staking protocol
        'component_config': {
            'position_monitor': {
                'position_subscriptions': [
                    'wallet:BaseToken:USDT',
                    'wallet:BaseToken:ETH',
                    'etherfi:LST:weETH',
                    'binance:BaseToken:USDT',
                    'binance:Perp:ETHUSDT',
                    'bybit:BaseToken:USDT',
                    'bybit:Perp:ETHUSDT',
                    'okx:BaseToken:USDT',
                    'okx:Perp:ETHUSDT',
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
    """Create USDT ETH Staking Hedged Simple strategy instance."""
    return USDTETHStakingHedgedSimpleStrategy(
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


class TestUSDTETHStakingHedgedSimpleStrategyInit:
    """Test strategy initialization and validation."""
    
    def test_init_validates_required_instruments(self, mock_config, mock_components):
        """Test that strategy validates required instruments are in position_subscriptions."""
        # Test with missing required instrument
        mock_config['component_config']['position_monitor']['position_subscriptions'] = [
            'wallet:BaseToken:USDT',
            'wallet:BaseToken:ETH'
            # Missing etherfi:LST:weETH
        ]
        
        with pytest.raises(ValueError, match="Required instrument etherfi:LST:weETH not in position_subscriptions"):
            USDTETHStakingHedgedSimpleStrategy(
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
            'wallet:BaseToken:USDT',
            'wallet:BaseToken:ETH',
            'etherfi:LST:weETH',
            'binance:Perp:ETHUSDT',
            'bybit:BaseToken:USDT',
            'bybit:Perp:ETHUSDT',
            'okx:BaseToken:USDT',
            'okx:Perp:ETHUSDT',
            'wallet:BaseToken:EIGEN',
            'wallet:BaseToken:ETHFI'
        ]
        
        with pytest.raises(ValueError, match="Required instrument binance:BaseToken:USDT not in position_subscriptions"):
            USDTETHStakingHedgedSimpleStrategy(
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
        assert strategy.eth_allocation == 0.5
        assert strategy.usdt_allocation == 0.5
        assert strategy.lst_type == 'etherfi'
        assert len(strategy.available_instruments) == 11


class TestUSDTETHStakingHedgedSimpleStrategyActions:
    """Test the 5 standard strategy actions."""
    
    def test_generate_orders_entry_full(self, strategy):
        """Test entry_full order generation."""
        with patch.object(strategy, '_create_entry_full_orders') as mock_create:
            mock_orders = [Mock()]
            mock_create.return_value = mock_orders
            
            orders = strategy.generate_orders(
            timestamp=pd.Timestamp.now(),
            exposure={},
            risk_assessment={},
            pnl={},
            market_data={}
        )
            
            mock_create.assert_called_once_with(10000.0)
            assert orders == mock_orders
    
    def test_create_entry_full_orders(self, strategy):
        """Test _create_entry_full_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(10000.0)
            
            # Should have buy ETH and stake ETH orders
            assert len(orders) == 2
            
            # Check buy ETH order
            buy_order = next(o for o in orders if o.operation == OrderOperation.SPOT_TRADE)
            assert buy_order.venue == Venue.BINANCE
            assert buy_order.pair == 'ETH/USDT'
            assert buy_order.side == 'BUY'
            assert buy_order.amount == 10000.0 / 3000.0  # 10000 USDT / 3000 ETH price
            assert buy_order.source_venue == Venue.WALLET
            assert buy_order.target_venue == Venue.BINANCE
            assert buy_order.source_token == 'USDT'
            assert buy_order.target_token == 'ETH'
            assert buy_order.strategy_intent == 'entry_full'
            assert buy_order.strategy_id == 'usdt_eth_staking_hedged_simple'
            
            # Check stake ETH order
            stake_order = next(o for o in orders if o.operation == OrderOperation.STAKE)
            assert stake_order.venue == Venue.ETHERFI
            assert stake_order.token_in == 'ETH'
            assert stake_order.token_out == 'weETH'
            assert stake_order.amount == 10000.0 / 3000.0  # Same amount as ETH bought
            assert stake_order.strategy_intent == 'entry_full'
            assert stake_order.strategy_id == 'usdt_eth_staking_hedged_simple'
    
    def test_create_entry_partial_orders(self, strategy):
        """Test _create_entry_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_partial_orders(5000.0)
            
            assert len(orders) == 2  # Buy ETH + stake ETH
            for order in orders:
                assert order.strategy_intent == 'entry_partial'
                assert order.amount == 5000.0 / 3000.0  # 5000 USDT / 3000 ETH price
    
    def test_create_exit_full_orders(self, strategy):
        """Test _create_exit_full_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_exit_full_orders(10000.0)
            
            # Should have unstake ETH and sell ETH orders
            assert len(orders) == 2
            
            # Check unstake ETH order
            unstake_order = next(o for o in orders if o.operation == OrderOperation.UNSTAKE)
            assert unstake_order.venue == Venue.ETHERFI
            assert unstake_order.token_in == 'weETH'
            assert unstake_order.token_out == 'ETH'
            assert unstake_order.strategy_intent == 'exit_full'
            
            # Check sell ETH order
            sell_order = next(o for o in orders if o.operation == OrderOperation.SPOT_TRADE)
            assert sell_order.venue == Venue.BINANCE
            assert sell_order.pair == 'ETH/USDT'
            assert sell_order.side == 'SELL'
            assert sell_order.strategy_intent == 'exit_full'
    
    def test_create_exit_partial_orders(self, strategy):
        """Test _create_exit_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_exit_partial_orders(5000.0)
            
            assert len(orders) == 2  # Unstake ETH + sell ETH
            for order in orders:
                assert order.strategy_intent == 'exit_partial'
                assert order.amount == 5000.0 / 3000.0  # 5000 USDT / 3000 ETH price
    
    def test_create_dust_sell_orders(self, strategy):
        """Test _create_dust_sell_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_dust_sell_orders(10000.0)
            
            # Should have orders for EIGEN and ETHFI dust
            assert len(orders) == 2
            
            # Check EIGEN dust order
            eigen_order = next(o for o in orders if o.token_in == 'EIGEN')
            assert eigen_order.venue == Venue.UNISWAP
            assert eigen_order.operation == OrderOperation.SWAP
            assert eigen_order.token_out == 'USDT'
            assert eigen_order.strategy_intent == 'dust_sell'
            
            # Check ETHFI dust order
            ethfi_order = next(o for o in orders if o.token_in == 'ETHFI')
            assert ethfi_order.venue == Venue.UNISWAP
            assert ethfi_order.operation == OrderOperation.SWAP
            assert ethfi_order.token_out == 'USDT'
            assert ethfi_order.strategy_intent == 'dust_sell'


class TestUSDTETHStakingHedgedSimpleStrategyHelpers:
    """Test helper methods."""
    
    def test_calculate_target_position(self, strategy):
        """Test calculate_target_position method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            target = strategy.calculate_target_position(10000.0)
            
            assert 'weeth_balance' in target
            assert 'eth_balance' in target
            assert 'usdt_balance' in target
            assert target['weeth_balance'] == 10000.0 / 3000.0  # 10000 USDT / 3000 ETH price
            assert target['eth_balance'] == 0.0  # All ETH staked
            assert target['usdt_balance'] == 0.0  # All USDT used for ETH buy
    
    def test_get_asset_price(self, strategy):
        """Test _get_asset_price method."""
        price = strategy._get_asset_price()
        assert price == 3000.0  # Mock price from implementation
    
    def test_order_operation_id_format(self, strategy):
        """Test that operation_id format is correct (unix microseconds)."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(10000.0)
            
            for order in orders:
                # Check operation_id format: strategy_id_intent_timestamp
                parts = order.operation_id.split('_')
                assert len(parts) >= 3
                assert parts[0] == 'usdt'
                assert parts[1] == 'eth'
                # Last part should be a timestamp (numeric)
                assert parts[-1].isdigit()
                # Should be unix microseconds (13+ digits)
                assert len(parts[-1]) >= 13
    
    def test_order_has_required_fields(self, strategy):
        """Test that all Order objects have required fields."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(10000.0)
            
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


class TestUSDTETHStakingHedgedSimpleStrategyErrorHandling:
    """Test error handling scenarios."""
    
    def test_create_orders_with_zero_equity(self, strategy):
        """Test order creation with zero equity."""
        orders = strategy._create_entry_full_orders(0.0)
        assert len(orders) == 0
    
    def test_create_orders_with_negative_equity(self, strategy):
        """Test order creation with negative equity."""
        orders = strategy._create_entry_full_orders(-10000.0)
        assert len(orders) == 0
    
    def test_get_asset_price_error_handling(self, strategy):
        """Test error handling in _get_asset_price."""
        with patch.object(strategy, '_get_asset_price', side_effect=Exception("Price fetch failed")):
            orders = strategy._create_entry_full_orders(10000.0)
            # Should handle error gracefully and return empty list
            assert len(orders) == 0
