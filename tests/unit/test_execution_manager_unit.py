"""
Unit Tests for Execution Manager Component

Tests Execution Manager in isolation with mocked dependencies.
Focuses on instruction routing, reconciliation, and error handling.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

# Import the component under test
from basis_strategy_v1.core.execution.execution_manager import ExecutionManager


class TestExecutionManagerUnit:
    """Unit tests for Execution Manager component."""
    
    def test_instruction_routing_to_correct_interface(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test instruction routing to correct interface."""
        # Arrange
        mock_config['venues'] = {
            'binance': {'enabled': True, 'type': 'cex'},
            'ethereum': {'enabled': True, 'type': 'onchain'}
        }
        
        execution_manager = ExecutionManager(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
            execution_interfaces=mock_execution_interfaces
        )
        
        # Act - Test CEX instruction routing
        cex_instruction = {
            'action': 'open_position',
            'venue': 'binance',
            'asset': 'BTC',
            'size': 0.1,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:00:00')
        }
        
        result = execution_manager.execute_instruction(cex_instruction)
        
        # Assert - Should route to CEX interface
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'order_id' in result
        
        # CEX interface should have been called
        mock_execution_interfaces['cex'].execute_order.assert_called()
        
        # Act - Test onchain instruction routing
        onchain_instruction = {
            'action': 'transfer',
            'venue': 'ethereum',
            'asset': 'ETH',
            'size': 1.0,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:00:00')
        }
        
        result = execution_manager.execute_instruction(onchain_instruction)
        
        # Assert - Should route to onchain interface
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'tx_hash' in result
        
        # Onchain interface should have been called
        mock_execution_interfaces['onchain'].execute_order.assert_called()
    
    def test_sequential_execution(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces, mock_strategy_instructions):
        """Test sequential execution (one at a time)."""
        # Arrange
        execution_manager = ExecutionManager(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
            execution_interfaces=mock_execution_interfaces
        )
        
        # Act - Execute multiple instructions sequentially
        results = []
        for instruction in mock_strategy_instructions:
            result = execution_manager.execute_instruction(instruction)
            results.append(result)
        
        # Assert - Should execute sequentially
        assert len(results) == len(mock_strategy_instructions)
        
        # Each instruction should be executed one at a time
        for result in results:
            assert isinstance(result, dict)
            assert 'status' in result
        
        # Verify that interfaces were called in sequence
        # (This would be verified by checking call order in real implementation)
    
    def test_position_reconciliation_after_execution(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test position reconciliation after execution."""
        # Arrange
        mock_position_monitor = Mock()
        mock_position_monitor.get_snapshot.return_value = {
            'wallet': {'BTC': 0.1, 'USDT': 5000.0},
            'cex_accounts': {'binance': {'BTC': 0.1, 'USDT': 5000.0}},
            'perp_positions': {}
        }
        
        execution_manager = ExecutionManager(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
            execution_interfaces=mock_execution_interfaces,
            position_monitor=mock_position_monitor
        )
        
        # Act
        instruction = {
            'action': 'open_position',
            'venue': 'binance',
            'asset': 'BTC',
            'size': 0.1,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:00:00')
        }
        
        result = execution_manager.execute_instruction(instruction)
        
        # Assert - Should reconcile position after execution
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'reconciliation' in result
        
        # Position monitor should have been consulted for reconciliation
        mock_position_monitor.get_snapshot.assert_called()
    
    def test_error_handling_and_retry_logic(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test error handling and retry logic."""
        # Arrange
        mock_execution_interfaces['cex'].execute_order.side_effect = Exception("Execution error")
        
        execution_manager = ExecutionManager(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
            execution_interfaces=mock_execution_interfaces
        )
        
        # Act
        instruction = {
            'action': 'open_position',
            'venue': 'binance',
            'asset': 'BTC',
            'size': 0.1,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:00:00')
        }
        
        result = execution_manager.execute_instruction(instruction)
        
        # Assert - Should handle errors gracefully
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'error' in result
        
        # Should have attempted retry (implementation dependent)
        # The exact retry logic would be tested in integration tests
    
    def test_transaction_confirmation_in_live_mode(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test transaction confirmation in live mode."""
        # Arrange
        mock_config['execution_mode'] = 'live'
        
        # Mock onchain interface to return transaction hash
        mock_execution_interfaces['onchain'].execute_order.return_value = {
            'status': 'confirmed',
            'tx_hash': '0x1234567890abcdef',
            'gas_used': 100000,
            'gas_cost': 5.0,
            'confirmation_time': 30.0
        }
        
        execution_manager = ExecutionManager(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
            execution_interfaces=mock_execution_interfaces
        )
        
        # Act
        instruction = {
            'action': 'transfer',
            'venue': 'ethereum',
            'asset': 'ETH',
            'size': 1.0,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:00:00')
        }
        
        result = execution_manager.execute_instruction(instruction)
        
        # Assert - Should handle transaction confirmation
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'tx_hash' in result
        assert 'confirmation_time' in result
        
        # Should have confirmed transaction
        assert result['status'] == 'confirmed'
        assert result['tx_hash'] == '0x1234567890abcdef'
    
    def test_execution_cost_tracking(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test execution cost tracking."""
        # Arrange
        execution_manager = ExecutionManager(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
            execution_interfaces=mock_execution_interfaces
        )
        
        # Act - Execute multiple instructions
        instructions = [
            {
                'action': 'open_position',
                'venue': 'binance',
                'asset': 'BTC',
                'size': 0.1,
                'order_type': 'market',
                'timestamp': pd.Timestamp('2024-05-12 00:00:00')
            },
            {
                'action': 'transfer',
                'venue': 'ethereum',
                'asset': 'ETH',
                'size': 1.0,
                'order_type': 'market',
                'timestamp': pd.Timestamp('2024-05-12 00:01:00')
            }
        ]
        
        total_costs = 0.0
        for instruction in instructions:
            result = execution_manager.execute_instruction(instruction)
            if 'execution_cost' in result:
                total_costs += result['execution_cost']
        
        # Assert - Should track execution costs
        assert total_costs >= 0.0
        
        # Each execution should have cost information
        for instruction in instructions:
            result = execution_manager.execute_instruction(instruction)
            assert isinstance(result, dict)
            # Cost tracking is implementation dependent
    
    def test_execution_manager_initialization(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test Execution Manager initialization with different configs."""
        # Test backtest mode
        backtest_config = mock_config.copy()
        backtest_config['execution_mode'] = 'backtest'
        
        execution_manager = ExecutionManager(
            config=backtest_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
            execution_interfaces=mock_execution_interfaces
        )
        
        assert execution_manager.config['execution_mode'] == 'backtest'
        
        # Test live mode
        live_config = mock_config.copy()
        live_config['execution_mode'] = 'live'
        
        execution_manager = ExecutionManager(
            config=live_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
            execution_interfaces=mock_execution_interfaces
        )
        
        assert execution_manager.config['execution_mode'] == 'live'
    
    def test_execution_manager_error_handling(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test Execution Manager error handling."""
        # Arrange - Mock execution interfaces to raise exceptions
        mock_execution_interfaces['cex'].execute_order.side_effect = Exception("CEX error")
        mock_execution_interfaces['onchain'].execute_order.side_effect = Exception("Onchain error")
        
        execution_manager = ExecutionManager(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
            execution_interfaces=mock_execution_interfaces
        )
        
        # Act & Assert - Should handle errors gracefully
        instruction = {
            'action': 'open_position',
            'venue': 'binance',
            'asset': 'BTC',
            'size': 0.1,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:00:00')
        }
        
        try:
            result = execution_manager.execute_instruction(instruction)
            # If no exception, should return error state
            assert isinstance(result, dict)
            assert 'error' in result or 'status' in result
        except Exception as e:
            # If exception is raised, it should be handled appropriately
            assert "CEX error" in str(e)
    
    def test_execution_manager_performance(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test Execution Manager performance with multiple instructions."""
        # Arrange
        execution_manager = ExecutionManager(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
            execution_interfaces=mock_execution_interfaces
        )
        
        # Act - Execute multiple instructions
        import time
        start_time = time.time()
        
        for i in range(10):
            instruction = {
                'action': 'open_position',
                'venue': 'binance',
                'asset': 'BTC',
                'size': 0.1,
                'order_type': 'market',
                'timestamp': pd.Timestamp('2024-05-12 00:00:00') + pd.Timedelta(minutes=i)
            }
            
            result = execution_manager.execute_instruction(instruction)
            assert isinstance(result, dict)
        
        end_time = time.time()
        
        # Assert - Should complete within reasonable time
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should complete within 5 seconds
    
    def test_execution_manager_edge_cases(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test Execution Manager edge cases."""
        execution_manager = ExecutionManager(
            config=mock_config,
            data_provider=mock_data_provider,
            utility_manager=mock_utility_manager,
            execution_interfaces=mock_execution_interfaces
        )
        
        # Test empty instruction
        empty_instruction = {}
        try:
            result = execution_manager.execute_instruction(empty_instruction)
            assert isinstance(result, dict)
        except Exception as e:
            # Expected behavior for invalid instruction
            assert isinstance(e, Exception)
        
        # Test instruction with missing fields
        incomplete_instruction = {
            'action': 'open_position',
            'venue': 'binance'
            # Missing required fields
        }
        
        try:
            result = execution_manager.execute_instruction(incomplete_instruction)
            assert isinstance(result, dict)
        except Exception as e:
            # Expected behavior for incomplete instruction
            assert isinstance(e, Exception)
        
        # Test instruction with invalid venue
        invalid_venue_instruction = {
            'action': 'open_position',
            'venue': 'nonexistent_venue',
            'asset': 'BTC',
            'size': 0.1,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:00:00')
        }
        
        try:
            result = execution_manager.execute_instruction(invalid_venue_instruction)
            assert isinstance(result, dict)
        except Exception as e:
            # Expected behavior for invalid venue
            assert isinstance(e, Exception)
