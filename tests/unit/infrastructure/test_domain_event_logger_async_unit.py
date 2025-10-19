"""
Unit tests for DomainEventLogger async I/O and global ordering functionality.

Tests the new async I/O patterns and global event ordering for audit trails.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from backend.src.basis_strategy_v1.infrastructure.logging.domain_event_logger import DomainEventLogger
from backend.src.basis_strategy_v1.core.models.domain_events import PositionSnapshot


class TestDomainEventLoggerAsync:
    """Test DomainEventLogger async functionality."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def domain_event_logger(self, temp_log_dir):
        """Create DomainEventLogger instance for testing."""
        return DomainEventLogger(temp_log_dir)
    
    @pytest.fixture
    def sample_position_snapshot(self):
        """Create sample position snapshot for testing."""
        return PositionSnapshot(
            timestamp="2025-01-15T10:30:00",
            real_utc_time="2025-01-15T10:30:00.123456",
            correlation_id="test123",
            pid=12345,
            positions={"aave:aToken:aUSDT": 10000.0},
            total_value_usd=10000.0,
            position_type="simulated"
        )

    def test_global_order_initialization(self, domain_event_logger):
        """Test global order counter initializes to 0."""
        assert domain_event_logger._global_order == 0
        assert domain_event_logger._order_lock is not None

    @pytest.mark.asyncio
    async def test_get_next_global_order_sequential(self, domain_event_logger):
        """Test global order numbers are sequential and thread-safe."""
        # Test sequential ordering
        order1 = await domain_event_logger._get_next_global_order()
        order2 = await domain_event_logger._get_next_global_order()
        order3 = await domain_event_logger._get_next_global_order()
        
        assert order1 == 1
        assert order2 == 2
        assert order3 == 3
        assert domain_event_logger._global_order == 3

    @pytest.mark.asyncio
    async def test_get_next_global_order_concurrent(self, domain_event_logger):
        """Test global order numbers are unique under concurrent access."""
        # Create multiple concurrent tasks
        tasks = [
            domain_event_logger._get_next_global_order()
            for _ in range(10)
        ]
        
        # Run concurrently
        orders = await asyncio.gather(*tasks)
        
        # All orders should be unique and sequential
        assert len(set(orders)) == 10  # All unique
        assert sorted(orders) == list(range(1, 11))  # Sequential 1-10

    @pytest.mark.asyncio
    async def test_log_position_snapshot_async_adds_order(self, domain_event_logger, sample_position_snapshot):
        """Test async logging adds global order to event."""
        # Mock the async write method
        with patch.object(domain_event_logger, '_write_event_async', new_callable=AsyncMock) as mock_write:
            await domain_event_logger.log_position_snapshot_async(sample_position_snapshot)
            
            # Verify order was added
            assert sample_position_snapshot.order == 1
            assert domain_event_logger._global_order == 1
            
            # Verify async write was called
            mock_write.assert_called_once_with("positions", sample_position_snapshot)

    @pytest.mark.asyncio
    async def test_write_event_async_uses_asyncio_to_thread(self, domain_event_logger, sample_position_snapshot):
        """Test async write uses asyncio.to_thread for file I/O."""
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            # Mock the file writing
            mock_to_thread.return_value = None
            
            await domain_event_logger._write_event_async("positions", sample_position_snapshot)
            
            # Verify asyncio.to_thread was called
            mock_to_thread.assert_called_once()
            call_args = mock_to_thread.call_args[0]
            assert call_args[0] == domain_event_logger._write_to_file
            assert isinstance(call_args[1], Path)  # file_path
            assert isinstance(call_args[2], str)   # event_json

    @pytest.mark.asyncio
    async def test_write_to_file_helper(self, domain_event_logger, sample_position_snapshot, temp_log_dir):
        """Test the helper method for file writing."""
        file_path = temp_log_dir / "test.jsonl"
        event_json = sample_position_snapshot.model_dump_json()
        
        # Call the helper method
        domain_event_logger._write_to_file(file_path, event_json)
        
        # Verify file was written
        assert file_path.exists()
        with open(file_path, 'r') as f:
            content = f.read()
            assert event_json in content

    @pytest.mark.asyncio
    async def test_async_logging_performance(self, domain_event_logger, sample_position_snapshot):
        """Test async logging doesn't block the main thread."""
        import time
        
        # Mock the file writing to simulate I/O delay
        async def slow_write(file_path, event_json):
            await asyncio.sleep(0.1)  # Simulate I/O delay
        
        with patch.object(domain_event_logger, '_write_to_file', side_effect=slow_write):
            start_time = time.time()
            
            # Start multiple async logging operations
            tasks = [
                domain_event_logger.log_position_snapshot_async(sample_position_snapshot)
                for _ in range(5)
            ]
            
            await asyncio.gather(*tasks)
            
            end_time = time.time()
            
            # Should complete in ~0.1s (concurrent) not 0.5s (sequential)
            assert end_time - start_time < 0.2

    def test_synchronous_logging_still_works(self, domain_event_logger, sample_position_snapshot):
        """Test synchronous logging methods still work for backward compatibility."""
        with patch.object(domain_event_logger, '_write_event') as mock_write:
            domain_event_logger.log_position_snapshot(sample_position_snapshot)
            
            # Verify synchronous write was called
            mock_write.assert_called_once_with("positions", sample_position_snapshot)
            
            # Verify no order was added (synchronous version)
            assert sample_position_snapshot.order is None

    @pytest.mark.asyncio
    async def test_error_handling_in_async_logging(self, domain_event_logger, sample_position_snapshot):
        """Test error handling in async logging doesn't crash."""
        # Mock file writing to raise an exception
        with patch.object(domain_event_logger, '_write_to_file', side_effect=Exception("File write failed")):
            # Should not raise exception, just log error
            await domain_event_logger.log_position_snapshot_async(sample_position_snapshot)
            
            # Verify order was still assigned
            assert sample_position_snapshot.order == 1

    @pytest.mark.asyncio
    async def test_multiple_event_types_ordering(self, domain_event_logger):
        """Test global ordering works across different event types."""
        from backend.src.basis_strategy_v1.core.models.domain_events import ExposureSnapshot
        
        # Create different event types
        position_event = PositionSnapshot(
            timestamp="2025-01-15T10:30:00",
            real_utc_time="2025-01-15T10:30:00.123456",
            correlation_id="test123",
            pid=12345,
            positions={"aave:aToken:aUSDT": 10000.0},
            total_value_usd=10000.0,
            position_type="simulated"
        )
        
        exposure_event = ExposureSnapshot(
            timestamp="2025-01-15T10:30:00",
            real_utc_time="2025-01-15T10:30:00.123456",
            correlation_id="test123",
            pid=12345,
            net_delta_usd=1000.0,
            asset_exposures={"USDT": {"quantity": 10000.0, "usd_value": 10000.0, "percentage": 1.0}},
            total_value_usd=10000.0,
            share_class_value=10000.0
        )
        
        with patch.object(domain_event_logger, '_write_event_async', new_callable=AsyncMock):
            # Log different event types (using synchronous method for exposure)
            await domain_event_logger.log_position_snapshot_async(position_event)
            domain_event_logger.log_exposure_snapshot(exposure_event)
            
            # Verify global ordering across event types
            assert position_event.order == 1
            assert exposure_event.order is None  # Synchronous method doesn't add order
            assert domain_event_logger._global_order == 1

    def test_event_files_initialization(self, domain_event_logger, temp_log_dir):
        """Test all event files are properly initialized."""
        expected_files = [
            "positions", "exposures", "risk_assessments", "pnl_calculations",
            "orders", "operation_executions", "atomic_operation_groups",
            "execution_deltas", "reconciliations", "tight_loop_executions",
            "event_logger_operations", "strategy_decisions"
        ]
        
        for event_type in expected_files:
            assert event_type in domain_event_logger.event_files
            file_path = domain_event_logger.event_files[event_type]
            assert file_path.parent == temp_log_dir / "events"
            assert file_path.suffix == ".jsonl"
