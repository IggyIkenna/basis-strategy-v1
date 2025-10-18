"""
Unit tests for ETH Leveraged Strategy.

Tests the 5 standard actions, instrument validation, and order generation.
"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from pathlib import Path

from backend.src.basis_strategy_v1.core.strategies.eth_leveraged_strategy import ETHLeveragedStrategy
from backend.src.basis_strategy_v1.core.models.order import Order, OrderOperation
from backend.src.basis_strategy_v1.core.models.venues import Venue


@pytest.fixture
def mock_config():
    """Mock configuration for ETH Leveraged strategy."""
    return {
        'mode': 'eth_leveraged',
        'share_class': 'ETH',
        'asset': 'ETH',
        'eth_allocation': 0.8,  # 80% allocation to ETH
        'max_leverage': 2.0,   # 2x leverage
        'lst_type': 'weeth',   # Required for ETH strategies
        'staking_protocol': 'etherfi',  # Required for ETH strategies
        'component_config': {
            'position_monitor': {
                'position_subscriptions': [
                    'wallet:BaseToken:ETH',
                    'etherfi:LST:weETH',
                    'aave_v3:aToken:aWETH',
                    'aave_v3:debtToken:debtWETH',
                    'aave_v3:aToken:aweETH',
                    'instadapp:BaseToken:WETH',
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
    """Create ETH Leveraged strategy instance."""
    return ETHLeveragedStrategy(
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


class TestETHLeveragedStrategyInit:
    """Test strategy initialization and validation."""
    
    def test_init_validates_required_instruments(self, mock_config, mock_components):
        """Test that strategy validates required instruments are in position_subscriptions."""
        # Test with missing required instrument
        mock_config['component_config']['position_monitor']['position_subscriptions'] = [
            'wallet:BaseToken:ETH',
            'etherfi:LST:weETH'
            # Missing aave_v3:aToken:aWETH
        ]
        
        with pytest.raises(ValueError, match="Required instrument aave_v3:aToken:aWETH not in position_subscriptions"):
            ETHLeveragedStrategy(
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
            'wallet:BaseToken:ETH',
            'etherfi:LST:weETH',
            'invalid:format:aWETH',  # Invalid format
            'aave_v3:debtToken:debtWETH',
            'aave_v3:aToken:aweETH',
            'instadapp:BaseToken:WETH',
            'wallet:BaseToken:EIGEN',
            'wallet:BaseToken:ETHFI'
        ]
        
        with pytest.raises(ValueError, match="Required instrument aave_v3:aToken:aWETH not in position_subscriptions"):
            ETHLeveragedStrategy(
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
        assert strategy.asset == 'ETH'
        assert strategy.entry_instrument == 'wallet:BaseToken:ETH'
        assert strategy.staking_instrument == 'etherfi:LST:weETH'
        assert strategy.lending_instrument == 'aave_v3:aToken:aWETH'
        assert strategy.borrow_instrument == 'aave_v3:debtToken:debtWETH'
        assert len(strategy.available_instruments) == 8


class TestETHLeveragedStrategyActions:
    """Test the 5 standard strategy actions."""
    
    def test_generate_orders_entry_full(self, strategy):
        """Test entry_full order generation."""
        with patch.object(strategy, '_create_entry_full_orders') as mock_create:
            mock_orders = [Mock()]
            mock_create.return_value = mock_orders
            
            # Mock exposure with total_exposure and empty positions to trigger entry_full
            exposure = {
                'total_exposure': 50000.0,
                'positions': {}
            }
            risk_assessment = {'target_ltv': 0.8}
            
            orders = strategy.generate_orders(
                timestamp=pd.Timestamp.now(),
                exposure=exposure,
                risk_assessment=risk_assessment,
                pnl={},
                market_data={}
            )
            
            # Verify the method was called with correct parameters
            mock_create.assert_called_once_with(50000.0, 0.8)
            assert orders == mock_orders
    
    def test_create_entry_full_orders(self, strategy):
        """Test _create_entry_full_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(1.0, 0.8)
            
            # Should have multiple orders for leveraged staking
            assert len(orders) >= 3  # Flash loan, stake, lend
            
            # Check for flash loan order
            flash_loan_order = next((o for o in orders if o.operation == OrderOperation.FLASH_BORROW), None)
            assert flash_loan_order is not None
            assert flash_loan_order.venue == Venue.INSTADAPP
            assert flash_loan_order.token_out == 'WETH'
            
            # Check for staking order
            stake_order = next((o for o in orders if o.operation == OrderOperation.STAKE), None)
            assert stake_order is not None
            assert stake_order.venue == Venue.ETHERFI
            assert stake_order.token_in == 'WETH'
            assert stake_order.token_out == 'weeth'
            
            # Check for lending order
            lend_order = next((o for o in orders if o.operation == OrderOperation.SUPPLY), None)
            assert lend_order is not None
            assert lend_order.venue == Venue.AAVE_V3
            assert lend_order.token_in == 'weeth'
            assert lend_order.token_out == 'aweeth'
    
    def test_create_entry_partial_orders(self, strategy):
        """Test _create_entry_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_partial_orders(0.5, 0.8)
            
            assert len(orders) >= 3  # Similar to entry_full but partial amounts
            for order in orders:
                assert order.strategy_intent == 'entry_partial'
    
    def test_create_exit_full_orders(self, strategy):
        """Test _create_exit_full_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0), \
             patch.object(strategy.position_monitor, 'get_current_position', return_value={
                 'weeth_balance': 1.0,
                 'aave_v3:aToken:aWETH': 1.0,
                 'aave_v3:debtToken:debtWETH': 0.8
             }):
            orders = strategy._create_exit_full_orders(1.0)
            
            # Should have orders to unwind leveraged position
            assert len(orders) >= 3  # Unstake, withdraw, repay
            
            # Check for unstaking order
            unstake_order = next((o for o in orders if o.operation == OrderOperation.UNSTAKE), None)
            assert unstake_order is not None
            assert unstake_order.venue == Venue.ETHERFI
            assert unstake_order.token_in == 'weeth'
            assert unstake_order.token_out == 'WETH'
            
            # Check for withdrawal order
            withdraw_order = next((o for o in orders if o.operation == OrderOperation.WITHDRAW), None)
            assert withdraw_order is not None
            assert withdraw_order.venue == Venue.AAVE_V3
            assert withdraw_order.source_token == 'aweeth'
            assert withdraw_order.target_token == 'weeth'
    
    def test_create_exit_partial_orders(self, strategy):
        """Test _create_exit_partial_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0), \
             patch.object(strategy.position_monitor, 'get_current_position', return_value={
                 'weeth_balance': 1.0,
                 'aave_v3:aToken:aWETH': 1.0,
                 'aave_v3:debtToken:debtWETH': 0.8
             }):
            orders = strategy._create_exit_partial_orders(0.5)
            
            assert len(orders) >= 3  # Similar to exit_full but partial amounts
            for order in orders:
                assert order.strategy_intent == 'exit_partial'
    
    def test_create_dust_sell_orders(self, strategy):
        """Test _create_dust_sell_orders method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            dust_tokens = {'EIGEN': 1.0, 'ETHFI': 1.0}
            orders = strategy._create_dust_sell_orders(dust_tokens)
            
            # Should have orders for EIGEN and ETHFI dust
            assert len(orders) == 2
            
            # Check EIGEN dust order
            eigen_order = next((o for o in orders if o.token_in == 'EIGEN'), None)
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


class TestETHLeveragedStrategyHelpers:
    """Test helper methods."""
    
    def test_calculate_target_position(self, strategy):
        """Test calculate_target_position method."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            target = strategy.calculate_target_position(1.0)
            
            assert 'weeth_balance' in target
            assert 'eth_balance' in target
            assert 'aave_v3:aToken:aWETH' in target
            assert 'aave_v3:debtToken:debtWETH' in target
            assert target['weeth_balance'] > 0
            assert target['eth_balance'] == 1.0  # All ETH staked
    
    def test_order_operation_id_format(self, strategy):
        """Test that operation_id format is correct (unix microseconds)."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(1.0, 0.8)
            
            for order in orders:
                # Check operation_id format: operation_timestamp
                parts = order.operation_id.split('_')
                assert len(parts) >= 2
                assert parts[0] in ['flash', 'stake', 'supply', 'borrow']
                # Last part should be a timestamp (numeric)
                assert parts[-1].isdigit()
                # Should be unix microseconds (13+ digits)
                assert len(parts[-1]) >= 13
    
    def test_order_has_required_fields(self, strategy):
        """Test that all Order objects have required fields."""
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            orders = strategy._create_entry_full_orders(1.0, 0.8)
            
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


class TestETHLeveragedStrategyErrorHandling:
    """Test error handling scenarios."""
    
    def test_create_orders_with_zero_equity(self, strategy):
        """Test order creation with zero equity."""
        orders = strategy._create_entry_full_orders(0.0, 0.8)
        assert len(orders) == 0
    
    def test_create_orders_with_negative_equity(self, strategy):
        """Test order creation with negative equity."""
        orders = strategy._create_entry_full_orders(-1.0, 0.8)
        assert len(orders) == 0
    
    def test_get_asset_price_error_handling(self, strategy):
        """Test error handling in _get_asset_price."""
        with patch.object(strategy, '_get_asset_price', side_effect=Exception("Price fetch failed")):
            orders = strategy._create_entry_full_orders(1.0, 0.8)
            # Should handle error gracefully and return empty list
            assert len(orders) == 0
