"""
Unit tests for Transfer Execution Interface.

Tests the transfer execution interface component in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from basis_strategy_v1.core.interfaces.transfer_execution_interface import TransferExecutionInterface


class TestTransferExecutionInterface:
    """Test Transfer Execution Interface component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for transfer execution interface."""
        return {
            'execution_mode': 'backtest',
            'transfer_manager': 'cross_venue',
            'max_retries': 3,
            'timeout': 30
        }
    
    @pytest.fixture
    def mock_transfer_interface(self, mock_config):
        """Create transfer execution interface with mocked dependencies."""
        interface = TransferExecutionInterface('backtest', mock_config)
        return interface
    
    def test_initialization(self, mock_config):
        """Test transfer execution interface initialization."""
        interface = TransferExecutionInterface('backtest', mock_config)
        
        assert interface.execution_mode == 'backtest'
        assert interface.config == mock_config
    
    def test_execute_transfer_backtest_mode(self, mock_transfer_interface):
        """Test transfer execution in backtest mode."""
        transfer_params = {
            'from_venue': 'binance',
            'to_venue': 'aave',
            'asset': 'USDT',
            'amount': 1000.0,
            'transfer_type': 'spot_to_lending'
        }
        
        result = mock_transfer_interface.execute_transfer(transfer_params)
        
        # In backtest mode, should return mock success
        assert result['status'] == 'success'
        assert result['transfer_id'] is not None
        assert result['amount'] == 1000.0
        assert result['from_venue'] == 'binance'
        assert result['to_venue'] == 'aave'
    
    def test_execute_transfer_live_mode(self, mock_config):
        """Test transfer execution in live mode."""
        config = mock_config.copy()
        config['execution_mode'] = 'live'
        
        with patch('basis_strategy_v1.core.interfaces.transfer_execution_interface.CrossVenueTransferManager') as mock_manager:
            mock_manager_instance = Mock()
            mock_manager_instance.execute_transfer.return_value = {
                'status': 'success',
                'transfer_id': 'transfer_123',
                'amount': 1000.0,
                'from_venue': 'binance',
                'to_venue': 'aave'
            }
            mock_manager.return_value = mock_manager_instance
            interface = TransferExecutionInterface('live', config)
            
            transfer_params = {
                'from_venue': 'binance',
                'to_venue': 'aave',
                'asset': 'USDT',
                'amount': 1000.0,
                'transfer_type': 'spot_to_lending'
            }
            
            result = interface.execute_transfer(transfer_params)
            
            assert result['status'] == 'success'
            assert result['transfer_id'] == 'transfer_123'
            assert result['amount'] == 1000.0
            mock_manager_instance.execute_transfer.assert_called_once_with(transfer_params)
    
    def test_get_transfer_status_backtest_mode(self, mock_transfer_interface):
        """Test transfer status retrieval in backtest mode."""
        result = mock_transfer_interface.get_transfer_status('transfer_123')
        
        # In backtest mode, should return mock status
        assert result['status'] == 'completed'
        assert result['transfer_id'] == 'transfer_123'
        assert result['progress'] == 100
    
    def test_get_transfer_status_live_mode(self, mock_config):
        """Test transfer status retrieval in live mode."""
        config = mock_config.copy()
        config['execution_mode'] = 'live'
        
        with patch('basis_strategy_v1.core.interfaces.transfer_execution_interface.CrossVenueTransferManager') as mock_manager:
            mock_manager_instance = Mock()
            mock_manager_instance.get_transfer_status.return_value = {
                'status': 'completed',
                'transfer_id': 'transfer_123',
                'progress': 100
            }
            mock_manager.return_value = mock_manager_instance
            interface = TransferExecutionInterface('live', config)
            
            result = interface.get_transfer_status('transfer_123')
            
            assert result['status'] == 'completed'
            assert result['transfer_id'] == 'transfer_123'
            assert result['progress'] == 100
            mock_manager_instance.get_transfer_status.assert_called_once_with('transfer_123')
    
    def test_cancel_transfer_backtest_mode(self, mock_transfer_interface):
        """Test transfer cancellation in backtest mode."""
        result = mock_transfer_interface.cancel_transfer('transfer_123')
        
        # In backtest mode, should return mock success
        assert result['status'] == 'cancelled'
        assert result['transfer_id'] == 'transfer_123'
    
    def test_cancel_transfer_live_mode(self, mock_config):
        """Test transfer cancellation in live mode."""
        config = mock_config.copy()
        config['execution_mode'] = 'live'
        
        with patch('basis_strategy_v1.core.interfaces.transfer_execution_interface.CrossVenueTransferManager') as mock_manager:
            mock_manager_instance = Mock()
            mock_manager_instance.cancel_transfer.return_value = {
                'status': 'cancelled',
                'transfer_id': 'transfer_123'
            }
            mock_manager.return_value = mock_manager_instance
            interface = TransferExecutionInterface('live', config)
            
            result = interface.cancel_transfer('transfer_123')
            
            assert result['status'] == 'cancelled'
            assert result['transfer_id'] == 'transfer_123'
            mock_manager_instance.cancel_transfer.assert_called_once_with('transfer_123')
    
    def test_get_transfer_history_backtest_mode(self, mock_transfer_interface):
        """Test transfer history retrieval in backtest mode."""
        result = mock_transfer_interface.get_transfer_history(limit=10)
        
        # In backtest mode, should return mock history
        assert 'transfers' in result
        assert len(result['transfers']) <= 10
        assert all('transfer_id' in transfer for transfer in result['transfers'])
    
    def test_get_transfer_history_live_mode(self, mock_config):
        """Test transfer history retrieval in live mode."""
        config = mock_config.copy()
        config['execution_mode'] = 'live'
        
        with patch('basis_strategy_v1.core.interfaces.transfer_execution_interface.CrossVenueTransferManager') as mock_manager:
            mock_manager_instance = Mock()
            mock_manager_instance.get_transfer_history.return_value = {
                'transfers': [
                    {'transfer_id': 'transfer_1', 'status': 'completed'},
                    {'transfer_id': 'transfer_2', 'status': 'pending'}
                ]
            }
            mock_manager.return_value = mock_manager_instance
            interface = TransferExecutionInterface('live', config)
            
            result = interface.get_transfer_history(limit=10)
            
            assert 'transfers' in result
            assert len(result['transfers']) == 2
            mock_manager_instance.get_transfer_history.assert_called_once_with(limit=10)
    
    def test_validate_transfer_params(self, mock_transfer_interface):
        """Test transfer parameter validation."""
        # Valid parameters
        valid_params = {
            'from_venue': 'binance',
            'to_venue': 'aave',
            'asset': 'USDT',
            'amount': 1000.0,
            'transfer_type': 'spot_to_lending'
        }
        
        # Should not raise exception
        mock_transfer_interface._validate_transfer_params(valid_params)
    
    def test_validate_transfer_params_missing_required(self, mock_transfer_interface):
        """Test transfer parameter validation with missing required fields."""
        invalid_params = {
            'from_venue': 'binance',
            'asset': 'USDT',
            'amount': 1000.0
            # Missing 'to_venue' and 'transfer_type'
        }
        
        with pytest.raises(ValueError, match="Missing required transfer parameters"):
            mock_transfer_interface._validate_transfer_params(invalid_params)
    
    def test_validate_transfer_params_invalid_amount(self, mock_transfer_interface):
        """Test transfer parameter validation with invalid amount."""
        invalid_params = {
            'from_venue': 'binance',
            'to_venue': 'aave',
            'asset': 'USDT',
            'amount': -1000.0,  # Negative amount
            'transfer_type': 'spot_to_lending'
        }
        
        with pytest.raises(ValueError, match="Amount must be positive"):
            mock_transfer_interface._validate_transfer_params(invalid_params)
    
    def test_validate_transfer_params_invalid_venues(self, mock_transfer_interface):
        """Test transfer parameter validation with invalid venues."""
        invalid_params = {
            'from_venue': 'invalid_venue',
            'to_venue': 'aave',
            'asset': 'USDT',
            'amount': 1000.0,
            'transfer_type': 'spot_to_lending'
        }
        
        with pytest.raises(ValueError, match="Invalid venue"):
            mock_transfer_interface._validate_transfer_params(invalid_params)
    
    def test_heartbeat_test_backtest_mode(self, mock_transfer_interface):
        """Test heartbeat in backtest mode."""
        result = mock_transfer_interface.heartbeat_test()
        
        # In backtest mode, should return mock success
        assert result['status'] == 'healthy'
        assert result['response_time'] < 1.0
    
    def test_heartbeat_test_live_mode(self, mock_config):
        """Test heartbeat in live mode."""
        config = mock_config.copy()
        config['execution_mode'] = 'live'
        
        with patch('basis_strategy_v1.core.interfaces.transfer_execution_interface.CrossVenueTransferManager') as mock_manager:
            mock_manager_instance = Mock()
            mock_manager_instance.health_check.return_value = {'status': 'healthy'}
            mock_manager.return_value = mock_manager_instance
            interface = TransferExecutionInterface('live', config)
            
            with patch('time.time', side_effect=[0, 0.1]):
                result = interface.heartbeat_test()
                
                assert result['status'] == 'healthy'
                assert result['response_time'] == 0.1
                mock_manager_instance.health_check.assert_called_once()
    
    def test_heartbeat_test_failure(self, mock_config):
        """Test heartbeat failure handling."""
        config = mock_config.copy()
        config['execution_mode'] = 'live'
        
        with patch('basis_strategy_v1.core.interfaces.transfer_execution_interface.CrossVenueTransferManager') as mock_manager:
            mock_manager_instance = Mock()
            mock_manager_instance.health_check.side_effect = Exception("Connection failed")
            mock_manager.return_value = mock_manager_instance
            interface = TransferExecutionInterface('live', config)
            
            result = interface.heartbeat_test()
            
            assert result['status'] == 'unhealthy'
            assert 'error' in result
    
    def test_error_handling_transfer_failure(self, mock_config):
        """Test error handling when transfer fails."""
        config = mock_config.copy()
        config['execution_mode'] = 'live'
        
        with patch('basis_strategy_v1.core.interfaces.transfer_execution_interface.CrossVenueTransferManager') as mock_manager:
            mock_manager_instance = Mock()
            mock_manager_instance.execute_transfer.side_effect = Exception("Transfer failed")
            mock_manager.return_value = mock_manager_instance
            interface = TransferExecutionInterface('live', config)
            
            transfer_params = {
                'from_venue': 'binance',
                'to_venue': 'aave',
                'asset': 'USDT',
                'amount': 1000.0,
                'transfer_type': 'spot_to_lending'
            }
            
            with pytest.raises(Exception, match="Transfer failed"):
                interface.execute_transfer(transfer_params)
    
    def test_edge_case_zero_amount(self, mock_transfer_interface):
        """Test edge case with zero amount."""
        transfer_params = {
            'from_venue': 'binance',
            'to_venue': 'aave',
            'asset': 'USDT',
            'amount': 0.0,
            'transfer_type': 'spot_to_lending'
        }
        
        with pytest.raises(ValueError, match="Amount must be positive"):
            mock_transfer_interface._validate_transfer_params(transfer_params)
    
    def test_edge_case_very_large_amount(self, mock_transfer_interface):
        """Test edge case with very large amount."""
        transfer_params = {
            'from_venue': 'binance',
            'to_venue': 'aave',
            'asset': 'USDT',
            'amount': 1000000000.0,  # Very large amount
            'transfer_type': 'spot_to_lending'
        }
        
        # Should handle large amounts gracefully
        mock_transfer_interface._validate_transfer_params(transfer_params)
    
    def test_edge_case_same_venue_transfer(self, mock_transfer_interface):
        """Test edge case with same venue transfer."""
        transfer_params = {
            'from_venue': 'binance',
            'to_venue': 'binance',  # Same venue
            'asset': 'USDT',
            'amount': 1000.0,
            'transfer_type': 'internal_transfer'
        }
        
        # Should handle same venue transfers
        mock_transfer_interface._validate_transfer_params(transfer_params)
    
    def test_retry_logic_on_failure(self, mock_config):
        """Test retry logic when transfer fails."""
        config = mock_config.copy()
        config['execution_mode'] = 'live'
        config['max_retries'] = 2
        
        with patch('basis_strategy_v1.core.interfaces.transfer_execution_interface.CrossVenueTransferManager') as mock_manager:
            mock_manager_instance = Mock()
            # Fail first time, succeed second time
            mock_manager_instance.execute_transfer.side_effect = [
                Exception("Temporary failure"),
                {'status': 'success', 'transfer_id': 'transfer_123'}
            ]
            mock_manager.return_value = mock_manager_instance
            interface = TransferExecutionInterface('live', config)
            
            transfer_params = {
                'from_venue': 'binance',
                'to_venue': 'aave',
                'asset': 'USDT',
                'amount': 1000.0,
                'transfer_type': 'spot_to_lending'
            }
            
            with patch('time.sleep'):  # Mock sleep to speed up test
                result = interface.execute_transfer(transfer_params)
                
                assert result['status'] == 'success'
                assert result['transfer_id'] == 'transfer_123'
                assert mock_manager_instance.execute_transfer.call_count == 2
    
    def test_timeout_handling(self, mock_config):
        """Test timeout handling for long-running transfers."""
        config = mock_config.copy()
        config['execution_mode'] = 'live'
        config['timeout'] = 1  # 1 second timeout
        
        with patch('basis_strategy_v1.core.interfaces.transfer_execution_interface.CrossVenueTransferManager') as mock_manager:
            mock_manager_instance = Mock()
            # Simulate slow transfer
            mock_manager_instance.execute_transfer.side_effect = Exception("Timeout")
            mock_manager.return_value = mock_manager_instance
            interface = TransferExecutionInterface('live', config)
            
            transfer_params = {
                'from_venue': 'binance',
                'to_venue': 'aave',
                'asset': 'USDT',
                'amount': 1000.0,
                'transfer_type': 'spot_to_lending'
            }
            
            with patch('time.sleep'):  # Mock sleep to speed up test
                with pytest.raises(Exception, match="Timeout"):
                    interface.execute_transfer(transfer_params)
