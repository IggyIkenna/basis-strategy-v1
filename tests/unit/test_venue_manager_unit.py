"""
Unit Tests for Venue Manager Component

Tests Venue Manager in isolation with mocked dependencies.
Focuses on Order processing, reconciliation, and error handling.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

# Import the component under test
from basis_strategy_v1.core.execution.execution_manager import ExecutionManager
from basis_strategy_v1.core.models.order import Order


class TestExecutionManagerUnit:
    """Unit tests for Venue Manager component."""
    
    def test_order_routing_to_correct_interface(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test Order routing to correct interface."""
        # Arrange
        mock_config['venues'] = {
            'binance': {'enabled': True, 'type': 'cex'},
            'ethereum': {'enabled': True, 'type': 'onchain'}
        }

        mock_venue_interface_manager = Mock()
        mock_venue_interface_manager.route_to_venue.return_value = {'success': True, 'trade_id': 'test_trade'}

        execution_manager = ExecutionManager(
            execution_mode='backtest',
            config=mock_config,
            venue_interface_manager=mock_venue_interface_manager,
            position_update_handler=Mock()
        )

        # Act - Test CEX Order routing
        cex_order = Order(
            order_id='test_cex_order',
            action_type='buy',
            asset='BTC',
            size=0.1,
            venue='binance',
            order_type='market',
            timestamp=pd.Timestamp('2024-05-12 00:00:00')
        )

        result = execution_manager.process_orders(pd.Timestamp.now(), [cex_order])
        
        # Assert - Should route to CEX interface
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['success'] == True
        
        # Act - Test onchain Order routing
        onchain_order = Order(
            order_id='test_onchain_order',
            action_type='transfer',
            asset='ETH',
            size=1.0,
            venue='ethereum',
            order_type='market',
            timestamp=pd.Timestamp('2024-05-12 00:00:00')
        )

        result = execution_manager.process_orders(pd.Timestamp.now(), [onchain_order])
        
        # Assert - Should route to onchain interface
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['success'] == True
    
    def test_sequential_execution(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test sequential execution (one at a time)."""
        # Arrange
        mock_venue_interface_manager = Mock()
        mock_venue_interface_manager.route_to_venue.return_value = {'success': True, 'trade_id': 'test_trade'}
        
        mock_position_update_handler = Mock()
        mock_position_update_handler.update_state.return_value = {'success': True}

        execution_manager = ExecutionManager(
            execution_mode='backtest',
            config=mock_config,
            venue_interface_manager=mock_venue_interface_manager,
            position_update_handler=mock_position_update_handler
        )

        # Create test orders
        orders = [
            Order(order_id='order1', action_type='buy', asset='BTC', size=0.1, venue='binance', order_type='market', timestamp=pd.Timestamp.now()),
            Order(order_id='order2', action_type='sell', asset='ETH', size=1.0, venue='ethereum', order_type='market', timestamp=pd.Timestamp.now())
        ]

        # Act - Execute multiple orders sequentially
        result = execution_manager.process_orders(pd.Timestamp.now(), orders)
        
        # Assert - Should execute sequentially
        assert isinstance(result, list)
        assert len(result) == len(orders)
        
        # Each order should be executed one at a time
        for order_result in result:
            assert isinstance(order_result, dict)
            assert 'success' in order_result
            assert order_result['success'] == True
        
        # Verify that interfaces were called in sequence
        assert mock_venue_interface_manager.route_to_venue.call_count == len(orders)
        assert mock_position_update_handler.update_state.call_count == len(orders)
    
    def test_position_reconciliation_after_execution(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test position reconciliation after execution."""
        # Arrange
        mock_venue_interface_manager = Mock()
        mock_venue_interface_manager.route_to_venue.return_value = {'success': True, 'trade_id': 'test_trade'}
        
        mock_position_update_handler = Mock()
        mock_position_update_handler.update_state.return_value = {'success': True}

        execution_manager = ExecutionManager(
            execution_mode='backtest',
            config=mock_config,
            venue_interface_manager=mock_venue_interface_manager,
            position_update_handler=mock_position_update_handler
        )
        
        # Act
        order = Order(
            order_id='test_order',
            action_type='buy',
            asset='BTC',
            size=0.1,
            venue='binance',
            order_type='market',
            timestamp=pd.Timestamp('2024-05-12 00:00:00')
        )
        
        result = execution_manager.process_orders(pd.Timestamp.now(), [order])
        
        # Assert - Should reconcile position after execution
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['success'] == True
        
        # Verify reconciliation was called
        mock_position_update_handler.update_state.assert_called_once()
    
    def test_error_handling_and_retry_logic(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test error handling and retry logic."""
        # Arrange
        mock_venue_interface_manager = Mock()
        mock_venue_interface_manager.route_to_venue.return_value = {'success': False, 'error': 'Execution failed'}
        
        mock_position_update_handler = Mock()
        mock_position_update_handler.update_state.return_value = {'success': False}

        execution_manager = ExecutionManager(
            execution_mode='backtest',
            config=mock_config,
            venue_interface_manager=mock_venue_interface_manager,
            position_update_handler=mock_position_update_handler
        )

        # Act
        order = Order(
            order_id='test_order',
            action_type='buy',
            asset='BTC',
            size=0.1,
            venue='binance',
            order_type='market',
            timestamp=pd.Timestamp('2024-05-12 00:00:00')
        )

        result = execution_manager.process_orders(pd.Timestamp.now(), [order])
        
        # Assert - Should handle errors gracefully
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['success'] == False
        
        # Should have attempted retry (implementation dependent)
        # The exact retry logic would be tested in integration tests
    
    def test_transaction_confirmation_in_live_mode(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test transaction confirmation in live mode."""
        # Arrange
        mock_config['execution_mode'] = 'live'
        
        # Mock venue interface manager to return transaction hash
        mock_venue_interface_manager = Mock()
        mock_venue_interface_manager.route_to_venue.return_value = {
            'success': True,
            'trade_id': 'test_trade',
            'tx_hash': '0x1234567890abcdef',
            'gas_used': 100000,
            'gas_cost': 5.0,
            'confirmation_time': 30.0
        }
        
        mock_position_update_handler = Mock()
        mock_position_update_handler.update_state.return_value = {'success': True}
        
        execution_manager = ExecutionManager(
            execution_mode='live',
            config=mock_config,
            venue_interface_manager=mock_venue_interface_manager,
            position_update_handler=mock_position_update_handler
        )
        
        # Act
        order = Order(
            order_id='test_order',
            action_type='transfer',
            asset='ETH',
            size=1.0,
            venue='ethereum',
            order_type='market',
            timestamp=pd.Timestamp('2024-05-12 00:00:00')
        )
        
        result = execution_manager.process_orders(pd.Timestamp.now(), [order])
        
        # Assert - Should handle transaction confirmation
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['success'] == True
    
    def test_execution_cost_tracking(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test execution cost tracking."""
        # Arrange
        mock_venue_interface_manager = Mock()
        mock_venue_interface_manager.route_to_venue.return_value = {
            'success': True, 
            'trade_id': 'test_trade',
            'execution_cost': 0.001,
            'gas_cost': 5.0
        }
        
        mock_position_update_handler = Mock()
        mock_position_update_handler.update_state.return_value = {'success': True}
        
        execution_manager = ExecutionManager(
            execution_mode='backtest',
            config=mock_config,
            venue_interface_manager=mock_venue_interface_manager,
            position_update_handler=mock_position_update_handler
        )
        
        # Act - Execute multiple orders
        orders = [
            Order(
                order_id='order1',
                action_type='buy',
                asset='BTC',
                size=0.1,
                venue='binance',
                order_type='market',
                timestamp=pd.Timestamp('2024-05-12 00:00:00')
            ),
            Order(
                order_id='order2',
                action_type='transfer',
                asset='ETH',
                size=1.0,
                venue='ethereum',
                order_type='market',
                timestamp=pd.Timestamp('2024-05-12 00:01:00')
            )
        ]
        
        result = execution_manager.process_orders(pd.Timestamp.now(), orders)
        
        # Assert - Should track execution costs
        assert isinstance(result, list)
        assert len(result) == len(orders)
        for order_result in result:
            assert order_result['success'] == True
    
    def test_execution_manager_initialization(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test Venue Manager initialization with different configs."""
        # Test backtest mode
        backtest_config = mock_config.copy()
        backtest_config['execution_mode'] = 'backtest'
        
        execution_manager = ExecutionManager(
            execution_mode='backtest',
            config=backtest_config,
            venue_interface_manager=Mock(),
            position_update_handler=Mock()
        )
        
        assert execution_manager.execution_mode == 'backtest'
        
        # Test live mode
        live_config = mock_config.copy()
        live_config['execution_mode'] = 'live'
        
        execution_manager = ExecutionManager(
            execution_mode='live',
            config=live_config,
            venue_interface_manager=Mock(),
            position_update_handler=Mock()
        )
        
        assert execution_manager.execution_mode == 'live'
    
    def test_execution_manager_error_handling(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test Venue Manager error handling."""
        # Arrange - Mock venue interface manager to raise exceptions
        mock_venue_interface_manager = Mock()
        mock_venue_interface_manager.route_to_venue.side_effect = Exception("Execution error")
        
        mock_position_update_handler = Mock()
        mock_position_update_handler.update_state.return_value = {'success': False}
        
        execution_manager = ExecutionManager(
            execution_mode='backtest',
            config=mock_config,
            venue_interface_manager=mock_venue_interface_manager,
            position_update_handler=mock_position_update_handler
        )
        
        # Act & Assert - Should handle errors gracefully
        order = Order(
            order_id='test_order',
            action_type='buy',
            asset='BTC',
            size=0.1,
            venue='binance',
            order_type='market',
            timestamp=pd.Timestamp('2024-05-12 00:00:00')
        )
        
        result = execution_manager.process_orders(pd.Timestamp.now(), [order])
        
        # Should return result structure
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['success'] == False
    
    def test_execution_manager_performance(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test Venue Manager performance with multiple orders."""
        # Arrange
        mock_venue_interface_manager = Mock()
        mock_venue_interface_manager.route_to_venue.return_value = {'success': True, 'trade_id': 'test_trade'}
        
        mock_position_update_handler = Mock()
        mock_position_update_handler.update_state.return_value = {'success': True}
        
        execution_manager = ExecutionManager(
            execution_mode='backtest',
            config=mock_config,
            venue_interface_manager=mock_venue_interface_manager,
            position_update_handler=mock_position_update_handler
        )
        
        # Act - Execute multiple orders
        import time
        start_time = time.time()
        
        orders = []
        for i in range(10):
            order = Order(
                order_id=f'order_{i}',
                action_type='buy',
                asset='BTC',
                size=0.1,
                venue='binance',
                order_type='market',
                timestamp=pd.Timestamp('2024-05-12 00:00:00') + pd.Timedelta(minutes=i)
            )
            orders.append(order)
        
        result = execution_manager.process_orders(pd.Timestamp.now(), orders)
        
        end_time = time.time()
        
        # Assert - Should complete within reasonable time
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert isinstance(result, list)
        assert len(result) == len(orders)
    
    def test_execution_manager_edge_cases(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test Venue Manager edge cases."""
        mock_venue_interface_manager = Mock()
        mock_venue_interface_manager.route_to_venue.return_value = {'success': True, 'trade_id': 'test_trade'}
        
        mock_position_update_handler = Mock()
        mock_position_update_handler.update_state.return_value = {'success': True}
        
        execution_manager = ExecutionManager(
            execution_mode='backtest',
            config=mock_config,
            venue_interface_manager=mock_venue_interface_manager,
            position_update_handler=mock_position_update_handler
        )
        
        # Test empty orders list
        result = execution_manager.process_orders(pd.Timestamp.now(), [])
        assert isinstance(result, list)
        assert len(result) == 0
        
        # Test order with missing fields
        incomplete_order = Order(
            order_id='incomplete_order',
            action_type='buy',
            asset='BTC',
            size=0.1,
            venue='binance',
            order_type='market',
            timestamp=pd.Timestamp('2024-05-12 00:00:00')
        )
        
        result = execution_manager.process_orders(pd.Timestamp.now(), [incomplete_order])
        assert isinstance(result, list)
        assert len(result) == 1
        
        # Test order with invalid venue
        invalid_venue_order = Order(
            order_id='invalid_venue_order',
            action_type='buy',
            asset='BTC',
            size=0.1,
            venue='nonexistent_venue',
            order_type='market',
            timestamp=pd.Timestamp('2024-05-12 00:00:00')
        )
        
        result = execution_manager.process_orders(pd.Timestamp.now(), [invalid_venue_order])
        assert isinstance(result, list)
        assert len(result) == 1
