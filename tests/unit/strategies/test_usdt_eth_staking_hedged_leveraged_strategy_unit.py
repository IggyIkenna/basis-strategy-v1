"""
Unit tests for USDT ETH Staking Hedged Leveraged Strategy.

Tests the 5 standard actions, instrument validation, and order generation.
"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from pathlib import Path

from backend.src.basis_strategy_v1.core.strategies.usdt_eth_staking_hedged_leveraged_strategy import USDTETHStakingHedgedLeveragedStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation
from backend.src.basis_strategy_v1.core.models.venues import Venue


@pytest.fixture
def mock_config():
    """Mock configuration for USDT ETH Staking Hedged Leveraged strategy."""
    return {
        'mode': 'usdt_eth_staking_hedged_leveraged',
        'share_class': 'USDT',
        'asset': 'ETH',
        'usdt_allocation': 0.5,  # 50% allocation to USDT
        'eth_allocation': 0.5,   # 50% allocation to ETH
        'leverage_multiplier': 2.0,  # 2x leverage
        'lst_type': 'etherfi',  # Liquid staking type
        'lending_protocol': 'aave_v3',  # Lending protocol
        'staking_protocol': 'etherfi',  # Staking protocol
        'component_config': {
            'position_monitor': {
                'position_subscriptions': [
                    'wallet:BaseToken:USDT',
                    'wallet:BaseToken:ETH',
                    'etherfi:LST:weETH',
                    'aave_v3:aToken:aWETH',
                    'aave_v3:debtToken:debtWETH',
                    'aave_v3:aToken:aweETH',
                    'instadapp:BaseToken:WETH',
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
    """Create USDT ETH Staking Hedged Leveraged strategy instance."""
    return USDTETHStakingHedgedLeveragedStrategy(
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


class TestUSDTETHStakingHedgedLeveragedStrategyInit:
    """Test strategy initialization and validation."""
    
    def test_init_validates_required_instruments(self, mock_config, mock_components):
        """Test that strategy validates required instruments are in position_subscriptions."""
        # Test with missing required instrument
        mock_config['component_config']['position_monitor']['position_subscriptions'] = [
            'wallet:BaseToken:USDT',
            'wallet:BaseToken:ETH',
            'etherfi:LST:weETH'
            # Missing aave_v3:aToken:aWETH
        ]
        
        with pytest.raises(ValueError, match="Required instrument aave_v3:aToken:aWETH not in position_subscriptions"):
            USDTETHStakingHedgedLeveragedStrategy(
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
            'aave_v3:debtToken:debtWETH',
            'aave_v3:aToken:aweETH',
            'instadapp:BaseToken:WETH',
            'binance:BaseToken:USDT',
            'binance:Perp:ETHUSDT',
            'bybit:BaseToken:USDT',
            'bybit:Perp:ETHUSDT',
            'okx:BaseToken:USDT',
            'okx:Perp:ETHUSDT',
            'wallet:BaseToken:EIGEN',
            'wallet:BaseToken:ETHFI'
        ]
        
        with pytest.raises(ValueError, match="Required instrument aave_v3:aToken:aWETH not in position_subscriptions"):
            USDTETHStakingHedgedLeveragedStrategy(
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
        assert strategy.lending_protocol == 'aave_v3'
        assert strategy.staking_protocol == 'etherfi'
        assert len(strategy.available_instruments) == 15


class TestUSDTETHStakingHedgedLeveragedStrategyActions:
    """Test the 5 standard strategy actions."""
    
    def test_generate_orders_entry_full(self, strategy):
        """Test entry_full order generation."""
        with patch.object(strategy, '_create_entry_full_orders') as mock_create:
            mock_orders = [Mock()]
            mock_create.return_value = mock_orders
            
            orders = strategy.generate_orders(
                timestamp=pd.Timestamp.now(),
                exposure={'total_exposure': 10000.0, 'positions': {}},
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
            
            # Should have multiple orders for leveraged staking
            assert len(orders) >= 4  # Supply USDT, buy ETH, stake ETH, reserve
            
            # Check for supply USDT order
            supply_order = next((o for o in orders if o.operation == OrderOperation.SUPPLY), None)
            assert supply_order is not None
            assert supply_order.venue == Venue.AAVE_V3
            assert supply_order.token_in == 'USDT'
            assert supply_order.token_out == 'aUSDT'
            assert supply_order.strategy_intent == 'entry_full'
            assert supply_order.strategy_id == 'usdt_eth_staking_hedged_leveraged'
            
            # Check for buy ETH order
            buy_order = next((o for o in orders if o.operation == OrderOperation.SPOT_TRADE), None)
            assert buy_order is not None
            assert buy_order.venue == Venue.BINANCE
            assert buy_order.pair == 'ETH/USDT'
            assert buy_order.side == 'BUY'
            assert buy_order.strategy_intent == 'entry_full'
            
            # Check for stake ETH order
            stake_order = next((o for o in orders if o.operation == OrderOperation.STAKE), None)
            assert stake_order is not None
            assert stake_order.venue == Venue.ETHERFI
            assert stake_order.token_in == 'ETH'
            assert stake_order.token_out == 'etherfi'
            assert stake_order.strategy_intent == 'entry_full'
    
    def test_create_entry_partial_orders(self, strategy):
        """Test _create_entry_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_partial_orders(5000.0)
            
            assert len(orders) >= 4  # Similar to entry_full but partial amounts
            for order in orders:
                assert order.strategy_intent == 'entry_partial'
    
    def test_create_exit_full_orders(self, strategy):
        """Test _create_exit_full_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0), \
             patch.object(strategy.position_monitor, 'get_current_position', return_value={
                 'aUSDT_balance': 10000.0,
                 'etherfi_balance': 3.33
             }):
            orders = strategy._create_exit_full_orders(10000.0)
            
            # Should have orders to unwind leveraged position
            assert len(orders) >= 3  # Unstake, withdraw, sell perp
            
            # Check for unstaking order
            unstake_order = next((o for o in orders if o.operation == OrderOperation.UNSTAKE), None)
            assert unstake_order is not None
            assert unstake_order.venue == Venue.ETHERFI
            assert unstake_order.token_in == 'etherfi'
            assert unstake_order.token_out == 'ETH'
            assert unstake_order.strategy_intent == 'exit_full'
            
            # Check for withdrawal order
            withdraw_order = next((o for o in orders if o.operation == OrderOperation.WITHDRAW), None)
            assert withdraw_order is not None
            assert withdraw_order.venue == Venue.AAVE_V3
            assert withdraw_order.token_in == 'aUSDT'
            assert withdraw_order.token_out == 'USDT'
            assert withdraw_order.strategy_intent == 'exit_full'
    
    def test_create_exit_partial_orders(self, strategy):
        """Test _create_exit_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0), \
             patch.object(strategy.position_monitor, 'get_current_position', return_value={
                 'aUSDT_balance': 10000.0,
                 'etherfi_balance': 3.33
             }):
            orders = strategy._create_exit_partial_orders(5000.0)
            
            assert len(orders) >= 3  # Similar to exit_full but partial amounts
            for order in orders:
                assert order.strategy_intent == 'exit_partial'
    
    def test_create_dust_sell_orders(self, strategy):
        """Test _create_dust_sell_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            dust_tokens = {'EIGEN': 100.0, 'ETHFI': 50.0}
            orders = strategy._create_dust_sell_orders(dust_tokens)
            
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


class TestUSDTETHStakingHedgedLeveragedStrategyHelpers:
    """Test helper methods."""
    
    def test_calculate_target_position(self, strategy):
        """Test calculate_target_position method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            target = strategy.calculate_target_position(10000.0)
            
            assert 'etherfi_balance' in target
            assert 'eth_balance' in target
            assert 'aUSDT_balance' in target
            assert 'usdt_balance' in target
            assert target['etherfi_balance'] > 0
            assert target['eth_balance'] == 0.0  # All ETH staked
            assert target['aUSDT_balance'] > 0  # Some USDT lent
            assert target['usdt_balance'] > 0  # Some USDT reserved
    
    def test_get_asset_price(self, strategy):
        """Test _get_asset_price method."""
        price = strategy._get_asset_price()
        assert price == 3000.0  # Mock price from implementation
    
    def test_order_operation_id_format(self, strategy):
        """Test that operation_id format is correct (unix microseconds)."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(10000.0)
            
            for order in orders:
                # Check operation_id format: operation[_token]_timestamp
                parts = order.operation_id.split('_')
                assert len(parts) >= 2
                # First part should be operation type (supply, buy, stake, reserve, etc.)
                assert parts[0] in ['supply', 'buy', 'stake', 'reserve', 'unstake', 'sell', 'withdraw', 'transfer']
                # If there are 3+ parts, second part should be token type (usdt, eth, etc.)
                if len(parts) >= 3:
                    assert parts[1] in ['usdt', 'eth']
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


class TestUSDTETHStakingHedgedLeveragedStrategyErrorHandling:
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
            # Should handle error gracefully and still create reserve orders
            assert len(orders) == 1  # Only reserve order should be created
            assert orders[0].strategy_intent == 'reserve'
