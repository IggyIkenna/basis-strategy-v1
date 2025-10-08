"""
Test Seasonal Rewards Functionality

Tests the EventLogger's seasonal reward distribution logging functionality.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, AsyncMock
import sys
import os

# Add backend to path
sys.path.append('/workspace/backend/src')

from basis_strategy_v1.core.strategies.components.event_logger import EventLogger


class TestSeasonalRewards:
    """Test seasonal rewards functionality."""
    
    @pytest.fixture
    def event_logger(self):
        """Create EventLogger for testing."""
        return EventLogger(execution_mode='backtest', include_balance_snapshots=True)
    
    @pytest.mark.asyncio
    async def test_log_eigen_reward_distribution(self, event_logger):
        """Test logging EIGEN reward distribution."""
        timestamp = pd.Timestamp('2024-10-05', tz='UTC')
        reward_type = 'EIGEN'
        amount = 10.5
        weeth_balance_avg = 100.0
        period_start = pd.Timestamp('2024-08-15', tz='UTC')
        period_end = pd.Timestamp('2024-10-05', tz='UTC')
        
        position_snapshot = {
            'wallet': {'weETH': 100.0, 'EIGEN': 0.0},
            'last_updated': timestamp.isoformat()
        }
        
        order = await event_logger.log_seasonal_reward_distribution(
            timestamp=timestamp,
            reward_type=reward_type,
            amount=amount,
            weeth_balance_avg=weeth_balance_avg,
            period_start=period_start,
            period_end=period_end,
            position_snapshot=position_snapshot
        )
        
        # Verify event was logged
        assert order == 1
        assert len(event_logger.events) == 1
        
        event = event_logger.events[0]
        assert event['event_type'] == 'SEASONAL_REWARD_DISTRIBUTION'
        assert event['timestamp'] == timestamp
        assert event['severity'] == 'INFO'
        assert event['transaction_type'] == 'REWARD_DISTRIBUTION'
        assert event['purpose'] == f"Seasonal {reward_type} reward distribution: {amount} tokens"
        
        # Verify details
        details = event['details']
        assert details['reward_type'] == reward_type
        assert details['amount'] == amount
        assert details['weeth_balance_avg'] == weeth_balance_avg
        assert details['period_start'] == period_start.isoformat()
        assert details['period_end'] == period_end.isoformat()
        assert details['distribution_mechanism'] == 'king_protocol_weekly'
        assert details['data_source'] == 'etherfi_seasonal_rewards'
        
        # Verify position snapshot
        assert event['wallet_balance_after'] == position_snapshot
    
    @pytest.mark.asyncio
    async def test_log_ethfi_reward_distribution(self, event_logger):
        """Test logging ETHFI reward distribution."""
        timestamp = pd.Timestamp('2024-10-12', tz='UTC')
        reward_type = 'ETHFI'
        amount = 5.25
        weeth_balance_avg = 50.0
        period_start = pd.Timestamp('2024-10-06', tz='UTC')
        period_end = pd.Timestamp('2024-10-12', tz='UTC')
        
        order = await event_logger.log_seasonal_reward_distribution(
            timestamp=timestamp,
            reward_type=reward_type,
            amount=amount,
            weeth_balance_avg=weeth_balance_avg,
            period_start=period_start,
            period_end=period_end
        )
        
        # Verify event was logged
        assert order == 1
        assert len(event_logger.events) == 1
        
        event = event_logger.events[0]
        assert event['event_type'] == 'SEASONAL_REWARD_DISTRIBUTION'
        assert event['details']['reward_type'] == 'ETHFI'
        assert event['details']['amount'] == amount
        assert event['purpose'] == f"Seasonal {reward_type} reward distribution: {amount} tokens"
    
    @pytest.mark.asyncio
    async def test_multiple_reward_distributions(self, event_logger):
        """Test logging multiple reward distributions."""
        # First reward
        order1 = await event_logger.log_seasonal_reward_distribution(
            timestamp=pd.Timestamp('2024-10-05', tz='UTC'),
            reward_type='EIGEN',
            amount=10.0,
            weeth_balance_avg=100.0,
            period_start=pd.Timestamp('2024-08-15', tz='UTC'),
            period_end=pd.Timestamp('2024-10-05', tz='UTC')
        )
        
        # Second reward
        order2 = await event_logger.log_seasonal_reward_distribution(
            timestamp=pd.Timestamp('2024-10-12', tz='UTC'),
            reward_type='ETHFI',
            amount=5.0,
            weeth_balance_avg=100.0,
            period_start=pd.Timestamp('2024-10-06', tz='UTC'),
            period_end=pd.Timestamp('2024-10-12', tz='UTC')
        )
        
        # Verify both events were logged with correct order
        assert order1 == 1
        assert order2 == 2
        assert len(event_logger.events) == 2
        
        # Verify first event
        event1 = event_logger.events[0]
        assert event1['details']['reward_type'] == 'EIGEN'
        assert event1['details']['amount'] == 10.0
        
        # Verify second event
        event2 = event_logger.events[1]
        assert event2['details']['reward_type'] == 'ETHFI'
        assert event2['details']['amount'] == 5.0
    
    @pytest.mark.asyncio
    async def test_reward_distribution_without_position_snapshot(self, event_logger):
        """Test logging reward distribution without position snapshot."""
        timestamp = pd.Timestamp('2024-10-05', tz='UTC')
        reward_type = 'EIGEN'
        amount = 15.0
        weeth_balance_avg = 150.0
        period_start = pd.Timestamp('2024-08-15', tz='UTC')
        period_end = pd.Timestamp('2024-10-05', tz='UTC')
        
        order = await event_logger.log_seasonal_reward_distribution(
            timestamp=timestamp,
            reward_type=reward_type,
            amount=amount,
            weeth_balance_avg=weeth_balance_avg,
            period_start=period_start,
            period_end=period_end
            # No position_snapshot provided
        )
        
        # Verify event was logged
        assert order == 1
        assert len(event_logger.events) == 1
        
        event = event_logger.events[0]
        assert event['event_type'] == 'SEASONAL_REWARD_DISTRIBUTION'
        assert 'wallet_balance_after' not in event
    
    @pytest.mark.asyncio
    async def test_reward_distribution_event_structure(self, event_logger):
        """Test that reward distribution event has correct structure."""
        timestamp = pd.Timestamp('2024-10-05', tz='UTC')
        reward_type = 'EIGEN'
        amount = 20.0
        weeth_balance_avg = 200.0
        period_start = pd.Timestamp('2024-08-15', tz='UTC')
        period_end = pd.Timestamp('2024-10-05', tz='UTC')
        
        position_snapshot = {
            'wallet': {'weETH': 200.0, 'EIGEN': 0.0},
            'last_updated': timestamp.isoformat()
        }
        
        order = await event_logger.log_seasonal_reward_distribution(
            timestamp=timestamp,
            reward_type=reward_type,
            amount=amount,
            weeth_balance_avg=weeth_balance_avg,
            period_start=period_start,
            period_end=period_end,
            position_snapshot=position_snapshot
        )
        
        event = event_logger.events[0]
        
        # Verify all required fields are present
        required_fields = [
            'order', 'timestamp', 'event_type', 'venue', 'token', 'amount', 'details', 'severity',
            'purpose', 'transaction_type'
        ]
        
        for field in required_fields:
            assert field in event, f"Missing required field: {field}"
        
        # Verify details structure
        details = event['details']
        required_detail_fields = [
            'reward_type', 'amount', 'weeth_balance_avg', 'period_start',
            'period_end', 'distribution_mechanism', 'data_source'
        ]
        
        for field in required_detail_fields:
            assert field in details, f"Missing required detail field: {field}"
    
    @pytest.mark.asyncio
    async def test_reward_distribution_global_order(self, event_logger):
        """Test that reward distributions get correct global order numbers."""
        # Log some other events first
        await event_logger.log_event(
            timestamp=pd.Timestamp('2024-10-01', tz='UTC'),
            event_type='TEST_EVENT',
            venue='TEST_VENUE',
            details={'test': 'data'},
            severity='INFO',
            purpose='Test event',
            transaction_type='TEST'
        )
        
        # Log reward distribution
        order = await event_logger.log_seasonal_reward_distribution(
            timestamp=pd.Timestamp('2024-10-05', tz='UTC'),
            reward_type='EIGEN',
            amount=10.0,
            weeth_balance_avg=100.0,
            period_start=pd.Timestamp('2024-08-15', tz='UTC'),
            period_end=pd.Timestamp('2024-10-05', tz='UTC')
        )
        
        # Verify order is correct (should be 2, after the test event)
        assert order == 2
        assert len(event_logger.events) == 2
        
        # Verify the reward distribution event has correct order
        reward_event = event_logger.events[1]
        assert reward_event['order'] == 2
        assert reward_event['event_type'] == 'SEASONAL_REWARD_DISTRIBUTION'
    
    @pytest.mark.asyncio
    async def test_reward_distribution_timestamp_handling(self, event_logger):
        """Test that timestamps are handled correctly."""
        # Test with different timestamp formats
        timestamps = [
            pd.Timestamp('2024-10-05', tz='UTC'),
            pd.Timestamp('2024-10-05 12:00:00', tz='UTC'),
            pd.Timestamp('2024-10-05 12:00:00+00:00')
        ]
        
        for i, timestamp in enumerate(timestamps):
            order = await event_logger.log_seasonal_reward_distribution(
                timestamp=timestamp,
                reward_type='EIGEN',
                amount=10.0 + i,
                weeth_balance_avg=100.0,
                period_start=pd.Timestamp('2024-08-15', tz='UTC'),
                period_end=pd.Timestamp('2024-10-05', tz='UTC')
            )
            
            # Verify timestamp is preserved correctly
            event = event_logger.events[i]
            assert event['timestamp'] == timestamp
    
    @pytest.mark.asyncio
    async def test_reward_distribution_period_handling(self, event_logger):
        """Test that period start/end timestamps are handled correctly."""
        period_start = pd.Timestamp('2024-08-15 00:00:00', tz='UTC')
        period_end = pd.Timestamp('2024-10-05 23:59:59', tz='UTC')
        
        order = await event_logger.log_seasonal_reward_distribution(
            timestamp=pd.Timestamp('2024-10-05', tz='UTC'),
            reward_type='EIGEN',
            amount=10.0,
            weeth_balance_avg=100.0,
            period_start=period_start,
            period_end=period_end
        )
        
        event = event_logger.events[0]
        details = event['details']
        
        # Verify period timestamps are stored as ISO strings
        assert details['period_start'] == period_start.isoformat()
        assert details['period_end'] == period_end.isoformat()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])