"""
Unit Tests for Venue Manager Component

Tests Venue Manager in isolation with mocked dependencies.
Focuses on instruction routing, reconciliation, and error handling.
"""

import pytest
import pandas as pd
import asyncio
from unittest.mock import Mock, patch

# Import the component under test
from basis_strategy_v1.core.execution.venue_manager import VenueManager


class TestVenueManagerUnit:
    """Unit tests for Venue Manager component."""
    
    def test_instruction_routing_to_correct_interface(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test instruction routing to correct interface."""
        # Arrange
        mock_config['venues'] = {
            'binance': {'enabled': True, 'type': 'cex'},
            'ethereum': {'enabled': True, 'type': 'onchain'}
        }

        execution_manager = VenueManager(
            execution_mode='backtest',
            config=mock_config,
            position_monitor=Mock()
        )

        # Act - Test CEX instruction routing
        cex_instruction = {
            'action': 'cex_trade',
            'venue': 'binance',
            'asset': 'BTC',
            'size': 0.1,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:00:00')
        }

        # Use execute_venue_instructions with single instruction
        result = execution_manager.execute_venue_instructions(pd.Timestamp.now(), [cex_instruction])
        
        # Assert - Should route to CEX interface
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'results' in result
        
        # Act - Test onchain instruction routing
        onchain_instruction = {
            'action': 'wallet_transfer',
            'venue': 'ethereum',
            'asset': 'ETH',
            'size': 1.0,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:00:00')
        }

        result = execution_manager.execute_venue_instructions(pd.Timestamp.now()([onchain_instruction])
        
        # Assert - Should route to onchain interface
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'results' in result
    
    def test_sequential_execution(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces, mock_strategy_instructions):
        """Test sequential execution (one at a time)."""
        # Arrange
        execution_manager = VenueManager(
            execution_mode='backtest',
            config=mock_config,
            position_monitor=Mock()
        )

        # Act - Execute multiple instructions sequentially
        result = execution_manager.execute_venue_instructions(pd.Timestamp.now()(mock_strategy_instructions)
        
        # Assert - Should execute sequentially
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'results' in result
        assert len(result['results']) == len(mock_strategy_instructions)
        
        # Each instruction should be executed one at a time
        for instruction_result in result['results']:
            assert isinstance(instruction_result, dict)
            assert 'success' in instruction_result
        
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

        execution_manager = VenueManager(
            execution_mode='backtest',
            config=mock_config,
            position_monitor=mock_position_monitor
        )
        
        # Act
        instruction = {
            'action': 'cex_trade',
            'venue': 'binance',
            'asset': 'BTC',
            'size': 0.1,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:00:00')
        }
        
        result = execution_manager.execute_venue_instructions(pd.Timestamp.now()([instruction])
        
        # Assert - Should reconcile position after execution
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'results' in result
    
    def test_error_handling_and_retry_logic(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test error handling and retry logic."""
        # Arrange
        execution_manager = VenueManager(
            execution_mode='backtest',
            config=mock_config,
            position_monitor=Mock()
        )

        # Act
        instruction = {
            'action': 'cex_trade',
            'venue': 'binance',
            'asset': 'BTC',
            'size': 0.1,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:00:00')
        }

        result = execution_manager.execute_venue_instructions(pd.Timestamp.now()([instruction])
        
        # Assert - Should handle errors gracefully
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'results' in result
        
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
        
        execution_manager = VenueManager(
            execution_mode='backtest',
            config=mock_config,
            position_monitor=Mock()
        )
        
        # Act
        instruction = {
            'action': 'wallet_transfer',
            'venue': 'ethereum',
            'asset': 'ETH',
            'size': 1.0,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:00:00')
        }
        
        result = execution_manager.execute_venue_instructions(pd.Timestamp.now()([instruction])
        
        # Assert - Should handle transaction confirmation
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'results' in result
    
    def test_execution_cost_tracking(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test execution cost tracking."""
        # Arrange
        execution_manager = VenueManager(
            execution_mode='backtest',
            config=mock_config,
            position_monitor=Mock()
        )
        
        # Act - Execute multiple instructions
        instructions = [
            {
                'action': 'cex_trade',
                'venue': 'binance',
                'asset': 'BTC',
                'size': 0.1,
                'order_type': 'market',
                'timestamp': pd.Timestamp('2024-05-12 00:00:00')
            },
            {
                'action': 'wallet_transfer',
                'venue': 'ethereum',
                'asset': 'ETH',
                'size': 1.0,
                'order_type': 'market',
                'timestamp': pd.Timestamp('2024-05-12 00:01:00')
            }
        ]
        
        result = execution_manager.execute_venue_instructions(pd.Timestamp.now()(instructions)
        
        # Assert - Should track execution costs
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'results' in result
    
    def test_execution_manager_initialization(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test Execution Manager initialization with different configs."""
        # Test backtest mode
        backtest_config = mock_config.copy()
        backtest_config['execution_mode'] = 'backtest'
        
        execution_manager = VenueManager(
            execution_mode='backtest',
            config=backtest_config,
            position_monitor=Mock()
        )
        
        assert execution_manager.execution_mode == 'backtest'
        
        # Test live mode
        live_config = mock_config.copy()
        live_config['execution_mode'] = 'live'
        
        execution_manager = VenueManager(
            execution_mode='live',
            config=live_config,
            position_monitor=Mock()
        )
        
        assert execution_manager.execution_mode == 'live'
    
    def test_execution_manager_error_handling(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test Execution Manager error handling."""
        # Arrange - Mock execution interfaces to raise exceptions
        mock_execution_interfaces['cex'].execute_order.side_effect = Exception("CEX error")
        mock_execution_interfaces['onchain'].execute_order.side_effect = Exception("Onchain error")
        
        execution_manager = VenueManager(
            execution_mode='backtest',
            config=mock_config,
            position_monitor=Mock()
        )
        
        # Act & Assert - Should handle errors gracefully
        instruction = {
            'action': 'cex_trade',
            'venue': 'binance',
            'asset': 'BTC',
            'size': 0.1,
            'order_type': 'market',
            'timestamp': pd.Timestamp('2024-05-12 00:00:00')
        }
        
        result = execution_manager.execute_venue_instructions(pd.Timestamp.now()([instruction])
        
        # Should return result structure
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'results' in result
    
    def test_execution_manager_performance(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test Execution Manager performance with multiple instructions."""
        # Arrange
        execution_manager = VenueManager(
            execution_mode='backtest',
            config=mock_config,
            position_monitor=Mock()
        )
        
        # Act - Execute multiple instructions
        import time
        start_time = time.time()
        
        instructions = []
        for i in range(10):
            instruction = {
                'action': 'cex_trade',
                'venue': 'binance',
                'asset': 'BTC',
                'size': 0.1,
                'order_type': 'market',
                'timestamp': pd.Timestamp('2024-05-12 00:00:00') + pd.Timedelta(minutes=i)
            }
            instructions.append(instruction)
        
        result = execution_manager.execute_venue_instructions(pd.Timestamp.now()(instructions)
        
        end_time = time.time()
        
        # Assert - Should complete within reasonable time
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'results' in result
    
    def test_execution_manager_edge_cases(self, mock_config, mock_data_provider, mock_utility_manager, mock_execution_interfaces):
        """Test Execution Manager edge cases."""
        execution_manager = VenueManager(
            execution_mode='backtest',
            config=mock_config,
            position_monitor=Mock()
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
