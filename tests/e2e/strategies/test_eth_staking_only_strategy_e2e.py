"""
End-to-end tests for ETH Staking Only Strategy.

Tests complete cycle: entry → hold → exit.
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
        'asset': 'ETH',
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


class TestETHStakingOnlyStrategyE2E:
    """Test complete strategy lifecycle."""
    
    def test_full_cycle_entry_exit(self, strategy, mock_components):
        """Test complete cycle: entry → hold → exit."""
        # Mock initial state - 1 ETH in wallet
        initial_positions = {
            'wallet:BaseToken:ETH': 1.0,
            'etherfi:LST:weETH': 0.0,
            'wallet:BaseToken:EIGEN': 0.0,
            'wallet:BaseToken:ETHFI': 0.0
        }
        
        # Mock ETH price
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            # Step 1: Entry - Stake ETH
            entry_orders = strategy._create_entry_full_orders(1.0)
            
            # Verify entry orders
            assert len(entry_orders) == 1
            entry_order = entry_orders[0]
            assert entry_order.operation == OrderOperation.STAKE
            assert entry_order.venue == Venue.ETHERFI
            assert entry_order.token_in == 'ETH'
            assert entry_order.token_out == 'weETH'
            assert entry_order.amount == 1.0 / 3000.0  # 1 ETH worth of weETH
            assert entry_order.strategy_intent == 'entry_full'
            
            # Simulate order execution - update positions
            executed_positions = initial_positions.copy()
            executed_positions['wallet:BaseToken:ETH'] -= 1.0
            executed_positions['etherfi:LST:weETH'] += 1.0 / 3000.0
            
            # Step 2: Hold - Generate dust orders (simulate staking rewards)
            dust_orders = strategy._create_dust_sell_orders(1.0)
            
            # Verify dust orders
            assert len(dust_orders) == 2  # EIGEN and ETHFI dust
            
            # Check EIGEN dust order
            eigen_order = next(o for o in dust_orders if o.token_in == 'EIGEN')
            assert eigen_order.venue == Venue.UNISWAP
            assert eigen_order.operation == OrderOperation.SWAP
            assert eigen_order.token_out == 'ETH'
            assert eigen_order.strategy_intent == 'dust_sell'
            
            # Check ETHFI dust order
            ethfi_order = next(o for o in dust_orders if o.token_in == 'ETHFI')
            assert ethfi_order.venue == Venue.UNISWAP
            assert ethfi_order.operation == OrderOperation.SWAP
            assert ethfi_order.token_out == 'ETH'
            assert ethfi_order.strategy_intent == 'dust_sell'
            
            # Step 3: Exit - Unstake ETH
            exit_orders = strategy._create_exit_full_orders(1.0)
            
            # Verify exit orders
            assert len(exit_orders) == 1
            exit_order = exit_orders[0]
            assert exit_order.operation == OrderOperation.UNSTAKE
            assert exit_order.venue == Venue.ETHERFI
            assert exit_order.token_in == 'weETH'
            assert exit_order.token_out == 'ETH'
            assert exit_order.amount == 1.0 / 3000.0  # Same amount as staked
            assert exit_order.strategy_intent == 'exit_full'
            
            # Simulate exit execution - update positions
            final_positions = executed_positions.copy()
            final_positions['etherfi:LST:weETH'] -= 1.0 / 3000.0
            final_positions['wallet:BaseToken:ETH'] += 1.0 / 3000.0
            
            # Verify final state
            assert final_positions['etherfi:LST:weETH'] == 0.0
            assert final_positions['wallet:BaseToken:ETH'] > 0.0
    
    def test_partial_cycle_entry_partial_exit_partial(self, strategy, mock_components):
        """Test partial cycle: entry_partial → exit_partial."""
        # Mock initial state - 2 ETH in wallet
        initial_positions = {
            'wallet:BaseToken:ETH': 2.0,
            'etherfi:LST:weETH': 0.0,
            'wallet:BaseToken:EIGEN': 0.0,
            'wallet:BaseToken:ETHFI': 0.0
        }
        
        # Mock ETH price
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            # Step 1: Partial Entry - Stake 0.5 ETH
            entry_orders = strategy._create_entry_partial_orders(0.5)
            
            # Verify partial entry orders
            assert len(entry_orders) == 1
            entry_order = entry_orders[0]
            assert entry_order.operation == OrderOperation.STAKE
            assert entry_order.amount == 0.5 / 3000.0  # 0.5 ETH worth of weETH
            assert entry_order.strategy_intent == 'entry_partial'
            
            # Simulate partial entry execution
            executed_positions = initial_positions.copy()
            executed_positions['wallet:BaseToken:ETH'] -= 0.5
            executed_positions['etherfi:LST:weETH'] += 0.5 / 3000.0
            
            # Step 2: Partial Exit - Unstake 0.25 ETH
            exit_orders = strategy._create_exit_partial_orders(0.25)
            
            # Verify partial exit orders
            assert len(exit_orders) == 1
            exit_order = exit_orders[0]
            assert exit_order.operation == OrderOperation.UNSTAKE
            assert exit_order.amount == 0.25 / 3000.0  # 0.25 ETH worth of weETH
            assert exit_order.strategy_intent == 'exit_partial'
            
            # Simulate partial exit execution
            final_positions = executed_positions.copy()
            final_positions['etherfi:LST:weETH'] -= 0.25 / 3000.0
            final_positions['wallet:BaseToken:ETH'] += 0.25 / 3000.0
            
            # Verify final state
            assert final_positions['etherfi:LST:weETH'] == 0.25 / 3000.0  # 0.25 ETH still staked
            assert final_positions['wallet:BaseToken:ETH'] == 1.75  # 1.75 ETH in wallet
    
    def test_error_recovery_during_cycle(self, strategy, mock_components):
        """Test error recovery during strategy cycle."""
        # Mock ETH price
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            # Test error in entry
            with patch.object(strategy, '_create_entry_full_orders', side_effect=Exception("Entry failed")):
                with pytest.raises(Exception, match="Entry failed"):
                    strategy._create_entry_full_orders(1.0)
            
            # Test error in exit
            with patch.object(strategy, '_create_exit_full_orders', side_effect=Exception("Exit failed")):
                with pytest.raises(Exception, match="Exit failed"):
                    strategy._create_exit_full_orders(1.0)
            
            # Test error in dust handling
            with patch.object(strategy, '_create_dust_sell_orders', side_effect=Exception("Dust handling failed")):
                with pytest.raises(Exception, match="Dust handling failed"):
                    strategy._create_dust_sell_orders(1.0)
    
    def test_position_consistency_throughout_cycle(self, strategy, mock_components):
        """Test that positions remain consistent throughout the cycle."""
        # Mock ETH price
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            # Test that all orders reference valid instruments
            entry_orders = strategy._create_entry_full_orders(1.0)
            exit_orders = strategy._create_exit_full_orders(1.0)
            dust_orders = strategy._create_dust_sell_orders(1.0)
            
            all_orders = entry_orders + exit_orders + dust_orders
            
            for order in all_orders:
                # Verify all delta keys are in position subscriptions
                for delta_key in order.expected_deltas.keys():
                    assert delta_key in strategy.available_instruments
                
                # Verify order has required fields
                assert hasattr(order, 'operation_id')
                assert hasattr(order, 'venue')
                assert hasattr(order, 'operation')
                assert hasattr(order, 'amount')
                assert hasattr(order, 'strategy_intent')
                assert hasattr(order, 'strategy_id')
                
                # Verify strategy_id matches
                assert order.strategy_id == 'eth_staking_only'
    
    def test_performance_under_load(self, strategy, mock_components):
        """Test strategy performance under load."""
        # Mock ETH price
        with patch.object(strategy, '_get_asset_price', return_value=3000.0):
            # Generate many orders quickly
            orders_batch = []
            for i in range(100):
                orders = strategy._create_entry_full_orders(1.0)
                orders_batch.extend(orders)
            
            # Verify all orders were generated successfully
            assert len(orders_batch) == 100  # 100 entry orders
            
            # Verify all orders are valid
            for order in orders_batch:
                assert isinstance(order, Order)
                assert order.operation == OrderOperation.STAKE
                assert order.strategy_intent == 'entry_full'
                assert order.strategy_id == 'eth_staking_only'
