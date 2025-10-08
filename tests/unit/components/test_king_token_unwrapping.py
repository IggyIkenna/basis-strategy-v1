"""
Test KING Token Unwrapping Functionality

Tests the OnChainExecutionManager's KING token unwrapping and selling functionality.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add backend to path
sys.path.append('/workspace/backend/src')

from basis_strategy_v1.core.strategies.components.onchain_execution_manager import OnChainExecutionManager
from basis_strategy_v1.core.strategies.components.position_monitor import PositionMonitor
from basis_strategy_v1.core.strategies.components.event_logger import EventLogger
from basis_strategy_v1.infrastructure.data.historical_data_provider import DataProvider


class TestKingTokenUnwrapping:
    """Test KING token unwrapping functionality."""
    
    @pytest.fixture
    def mock_position_monitor(self):
        """Create mock position monitor."""
        monitor = Mock(spec=PositionMonitor)
        monitor.update = AsyncMock(return_value={'success': True})
        return monitor
    
    @pytest.fixture
    def mock_event_logger(self):
        """Create mock event logger."""
        logger = Mock(spec=EventLogger)
        logger.log_event = AsyncMock()
        return logger
    
    @pytest.fixture
    def mock_data_provider(self):
        """Create mock data provider with seasonal rewards data."""
        provider = Mock(spec=DataProvider)
        
        # Mock seasonal rewards data
        seasonal_data = pd.DataFrame({
            'eigen_per_eeth_weekly': [0.5, 0.6, 0.4],
            'ethfi_per_eeth': [0.5, 0.4, 0.6]
        }, index=pd.date_range('2024-01-01', periods=3, freq='D'))
        
        provider.data = {'seasonal_rewards': seasonal_data}
        provider.get_protocol_token_price = Mock(side_effect=lambda token, price_type, timestamp: {
            ('eigen', 'usdt'): 3.5,
            ('ethfi', 'usdt'): 2.0
        }.get((token, price_type), 1.0))
        
        return provider
    
    @pytest.fixture
    def execution_manager(self, mock_position_monitor, mock_event_logger, mock_data_provider):
        """Create OnChainExecutionManager for testing."""
        return OnChainExecutionManager(
            execution_mode='backtest',
            position_monitor=mock_position_monitor,
            event_logger=mock_event_logger,
            data_provider=mock_data_provider,
            config={}
        )
    
    @pytest.mark.asyncio
    async def test_king_unwrap_and_sell_success(self, execution_manager):
        """Test successful KING token unwrapping and selling."""
        king_balance = 100.0
        timestamp = pd.Timestamp('2024-01-02', tz='UTC')
        
        result = await execution_manager.unwrap_and_sell_king_tokens(king_balance, timestamp)
        
        # Verify result structure
        assert result['success'] is True
        assert result['king_balance'] == king_balance
        assert result['execution_mode'] == 'backtest'
        assert 'eigen_amount' in result
        assert 'ethfi_amount' in result
        assert 'total_usdt_value' in result
        assert 'gas_fee_eth' in result
        
        # Verify position monitor was updated
        execution_manager.position_monitor.update.assert_called_once()
        
        # Verify event was logged
        execution_manager.event_logger.log_event.assert_called_once()
        
        # Check that the logged event has correct structure
        logged_event = execution_manager.event_logger.log_event.call_args[0][0]
        assert logged_event['event_type'] == 'KING_UNWRAP_AND_SELL'
        assert logged_event['details']['king_balance'] == king_balance
    
    @pytest.mark.asyncio
    async def test_king_unwrap_with_seasonal_data(self, execution_manager):
        """Test KING unwrapping using seasonal rewards data."""
        king_balance = 50.0
        timestamp = pd.Timestamp('2024-01-02', tz='UTC')
        
        result = await execution_manager.unwrap_and_sell_king_tokens(king_balance, timestamp)
        
        # Verify ratios are used from seasonal data
        assert result['success'] is True
        assert result['eigen_amount'] > 0
        assert result['ethfi_amount'] > 0
        assert abs(result['eigen_amount'] + result['ethfi_amount'] - king_balance) < 0.01
    
    @pytest.mark.asyncio
    async def test_king_unwrap_without_seasonal_data(self, execution_manager):
        """Test KING unwrapping when seasonal data is not available."""
        # Remove seasonal data
        execution_manager.data_provider.data = {}
        
        king_balance = 25.0
        timestamp = pd.Timestamp('2024-01-02', tz='UTC')
        
        result = await execution_manager.unwrap_and_sell_king_tokens(king_balance, timestamp)
        
        # Should still work with default ratios
        assert result['success'] is True
        assert result['eigen_amount'] > 0
        assert result['ethfi_amount'] > 0
        assert abs(result['eigen_amount'] + result['ethfi_amount'] - king_balance) < 0.01
    
    @pytest.mark.asyncio
    async def test_king_unwrap_price_calculation(self, execution_manager):
        """Test KING unwrapping price calculations."""
        king_balance = 10.0
        timestamp = pd.Timestamp('2024-01-02', tz='UTC')
        
        result = await execution_manager.unwrap_and_sell_king_tokens(king_balance, timestamp)
        
        # Verify price calculations
        expected_eigen_value = result['eigen_amount'] * 3.5  # Mock EIGEN price
        expected_ethfi_value = result['ethfi_amount'] * 2.0  # Mock ETHFI price
        expected_total = expected_eigen_value + expected_ethfi_value
        
        assert abs(result['total_usdt_value'] - expected_total) < 0.01
    
    @pytest.mark.asyncio
    async def test_king_unwrap_gas_fee_deduction(self, execution_manager):
        """Test that gas fees are properly deducted."""
        king_balance = 5.0
        timestamp = pd.Timestamp('2024-01-02', tz='UTC')
        
        result = await execution_manager.unwrap_and_sell_king_tokens(king_balance, timestamp)
        
        # Verify gas fee is included
        assert result['gas_fee_eth'] == 0.01
        
        # Verify position monitor was called with gas fee deduction
        call_args = execution_manager.position_monitor.update.call_args[0][0]
        token_changes = call_args['token_changes']
        
        # Find gas fee change
        gas_fee_change = next((change for change in token_changes if change['reason'] == 'GAS_FEE'), None)
        assert gas_fee_change is not None
        assert gas_fee_change['delta'] == -0.01
        assert gas_fee_change['token'] == 'ETH'
    
    @pytest.mark.asyncio
    async def test_king_unwrap_live_mode_not_implemented(self, mock_position_monitor, mock_event_logger, mock_data_provider):
        """Test that live mode KING unwrapping is not yet implemented."""
        execution_manager = OnChainExecutionManager(
            execution_mode='live',
            position_monitor=mock_position_monitor,
            event_logger=mock_event_logger,
            data_provider=mock_data_provider,
            config={}
        )
        
        king_balance = 100.0
        timestamp = pd.Timestamp('2024-01-02', tz='UTC')
        
        result = await execution_manager.unwrap_and_sell_king_tokens(king_balance, timestamp)
        
        # Should return failure for live mode
        assert result['success'] is False
        assert 'not yet implemented' in result['error']
        assert result['execution_mode'] == 'live'
    
    @pytest.mark.asyncio
    async def test_king_unwrap_position_monitor_integration(self, execution_manager):
        """Test integration with position monitor."""
        king_balance = 75.0
        timestamp = pd.Timestamp('2024-01-02', tz='UTC')
        
        result = await execution_manager.unwrap_and_sell_king_tokens(king_balance, timestamp)
        
        # Verify position monitor was called with correct structure
        call_args = execution_manager.position_monitor.update.call_args[0][0]
        
        assert call_args['timestamp'] == timestamp
        assert call_args['trigger'] == 'KING_UNWRAP_AND_SELL'
        assert 'token_changes' in call_args
        
        token_changes = call_args['token_changes']
        
        # Verify all expected token changes are present
        change_reasons = [change['reason'] for change in token_changes]
        expected_reasons = [
            'KING_UNWRAP',
            'KING_UNWRAP_EIGEN',
            'KING_UNWRAP_ETHFI',
            'SELL_EIGEN_FOR_USDT',
            'SELL_ETHFI_FOR_USDT',
            'KING_UNWRAP_PROCEEDS',
            'GAS_FEE'
        ]
        
        for reason in expected_reasons:
            assert reason in change_reasons, f"Missing token change reason: {reason}"
    
    @pytest.mark.asyncio
    async def test_king_unwrap_event_logging(self, execution_manager):
        """Test that events are properly logged."""
        king_balance = 30.0
        timestamp = pd.Timestamp('2024-01-02', tz='UTC')
        
        result = await execution_manager.unwrap_and_sell_king_tokens(king_balance, timestamp)
        
        # Verify event was logged
        execution_manager.event_logger.log_event.assert_called_once()
        
        logged_event = execution_manager.event_logger.log_event.call_args[0][0]
        
        assert logged_event['timestamp'] == timestamp
        assert logged_event['event_type'] == 'KING_UNWRAP_AND_SELL'
        assert 'details' in logged_event
        
        details = logged_event['details']
        assert details['king_balance'] == king_balance
        assert 'eigen_amount' in details
        assert 'ethfi_amount' in details
        assert 'eigen_price' in details
        assert 'ethfi_price' in details
        assert 'total_usdt_value' in details
        assert 'gas_fee_eth' in details
        assert 'eigen_ratio' in details
        assert 'ethfi_ratio' in details


if __name__ == "__main__":
    pytest.main([__file__, "-v"])