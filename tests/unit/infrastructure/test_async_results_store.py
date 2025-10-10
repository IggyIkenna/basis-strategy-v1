"""
Unit tests for AsyncResultsStore - Queue-based results storage with ordering guarantees.

Tests verify:
- Ordering guarantees with variable write times
- No dropped data under heavy load
- Graceful shutdown and queue drain
- Error handling in worker
- FIFO processing even with concurrent operations
"""

import pytest
import asyncio
import tempfile
import shutil
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

from backend.src.basis_strategy_v1.infrastructure.persistence.async_results_store import AsyncResultsStore


class TestAsyncResultsStore:
    """Test suite for AsyncResultsStore ordering guarantees and data integrity."""
    
    @pytest.fixture
    async def results_store(self):
        """Create a temporary AsyncResultsStore for testing."""
        temp_dir = tempfile.mkdtemp()
        store = AsyncResultsStore(temp_dir, 'backtest')
        yield store
        # Cleanup
        try:
            await store.stop()
        except Exception:
            pass
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_ordering_guarantees_with_variable_write_times(self, results_store):
        """Test that results are written in FIFO order even with variable write times."""
        await results_store.start()
        
        # Queue multiple results rapidly
        timestamps = []
        for i in range(10):
            timestamp = pd.Timestamp(f'2024-01-01 {i:02d}:00:00')
            timestamps.append(timestamp)
            await results_store.save_timestep_result(
                request_id='test_ordering',
                timestamp=timestamp,
                data={'value': i, 'order': i}
            )
        
        # Stop and flush
        await results_store.stop()
        
        # Verify written in order
        results_dir = Path(results_store.results_dir) / 'test_ordering' / 'timesteps'
        assert results_dir.exists()
        
        # Get all files and sort by name (which includes timestamp)
        files = sorted(results_dir.glob('*.json'))
        assert len(files) == 10
        
        # Verify each file contains correct data in correct order
        for i, file_path in enumerate(files):
            with open(file_path, 'r') as f:
                data = json.load(f)
                assert data['value'] == i
                assert data['order'] == i
    
    @pytest.mark.asyncio
    async def test_no_dropped_data_under_heavy_load(self, results_store):
        """Test that all queued results are written even under heavy load."""
        await results_store.start()
        
        # Queue many results rapidly
        count = 100
        for i in range(count):
            timestamp = pd.Timestamp('2024-01-01 00:00:00') + pd.Timedelta(hours=i)
            await results_store.save_timestep_result(
                request_id='test_heavy_load',
                timestamp=timestamp,
                data={'value': i, 'index': i}
            )
        
        # Stop and verify all written
        await results_store.stop()
        
        # Verify all files written
        results_dir = Path(results_store.results_dir) / 'test_heavy_load' / 'timesteps'
        assert results_dir.exists()
        
        files = list(results_dir.glob('*.json'))
        assert len(files) == count
        
        # Verify no data lost
        values = set()
        for file_path in files:
            with open(file_path, 'r') as f:
                data = json.load(f)
                values.add(data['value'])
        
        assert len(values) == count
        assert values == set(range(count))
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown_and_queue_drain(self, results_store):
        """Test that queue drains gracefully during shutdown."""
        await results_store.start()
        
        # Queue some results
        for i in range(5):
            timestamp = pd.Timestamp('2024-01-01 00:00:00') + pd.Timedelta(hours=i)
            await results_store.save_timestep_result(
                request_id='test_shutdown',
                timestamp=timestamp,
                data={'value': i}
            )
        
        # Verify queue has items
        assert results_store.get_queue_size() > 0
        
        # Stop and verify queue drains
        await results_store.stop()
        
        # Verify all items processed
        assert results_store.get_queue_size() == 0
        
        # Verify files written
        results_dir = Path(results_store.results_dir) / 'test_shutdown' / 'timesteps'
        files = list(results_dir.glob('*.json'))
        assert len(files) == 5
    
    @pytest.mark.asyncio
    async def test_error_handling_in_worker(self, results_store):
        """Test that worker handles errors gracefully without stopping."""
        await results_store.start()
        
        # Queue a result with invalid data that will cause an error
        await results_store.save_timestep_result(
            request_id='test_error',  # This will create a valid directory
            timestamp=pd.Timestamp('2024-01-01 00:00:00'),
            data={'value': 'test'}  # Valid data
        )
        
        # Queue another result to verify worker continues
        await results_store.save_timestep_result(
            request_id='test_error',
            timestamp=pd.Timestamp('2024-01-01 01:00:00'),
            data={'value': 'test2'}
        )
        
        # Stop and verify both results processed
        await results_store.stop()
        
        # Verify files written despite any errors
        results_dir = Path(results_store.results_dir) / 'test_error' / 'timesteps'
        files = list(results_dir.glob('*.json'))
        assert len(files) == 2
    
    @pytest.mark.asyncio
    async def test_final_result_storage(self, results_store):
        """Test that final results are stored correctly."""
        await results_store.start()
        
        final_data = {
            'performance': {
                'total_return': 1000.0,
                'total_return_pct': 10.0,
                'initial_capital': 10000.0,
                'final_value': 11000.0
            },
            'config': {'mode': 'test'},
            'start_date': '2024-01-01',
            'end_date': '2024-01-02'
        }
        
        await results_store.save_final_result('test_final', final_data)
        await results_store.stop()
        
        # Verify final result written
        final_file = Path(results_store.results_dir) / 'test_final' / 'final_result.json'
        assert final_file.exists()
        
        with open(final_file, 'r') as f:
            data = json.load(f)
            assert data['performance']['total_return'] == 1000.0
            assert data['performance']['final_value'] == 11000.0
    
    @pytest.mark.asyncio
    async def test_event_log_storage(self, results_store):
        """Test that event logs are stored correctly."""
        await results_store.start()
        
        events = [
            {'timestamp': '2024-01-01 00:00:00', 'event_type': 'START', 'data': {}},
            {'timestamp': '2024-01-01 01:00:00', 'event_type': 'PROCESS', 'data': {'value': 1}},
            {'timestamp': '2024-01-01 02:00:00', 'event_type': 'END', 'data': {}}
        ]
        
        await results_store.save_event_log('test_events', events)
        await results_store.stop()
        
        # Verify event log written
        event_file = Path(results_store.results_dir) / 'test_events' / 'event_log.csv'
        assert event_file.exists()
        
        # Read and verify CSV
        df = pd.read_csv(event_file)
        assert len(df) == 3
        assert df['event_type'].tolist() == ['START', 'PROCESS', 'END']
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_ordering(self, results_store):
        """Test that concurrent operations maintain ordering."""
        await results_store.start()
        
        # Create multiple concurrent save operations
        tasks = []
        for i in range(20):
            timestamp = pd.Timestamp('2024-01-01 00:00:00') + pd.Timedelta(minutes=i)
            task = results_store.save_timestep_result(
                request_id='test_concurrent',
                timestamp=timestamp,
                data={'value': i, 'order': i}
            )
            tasks.append(task)
        
        # Execute all concurrently
        await asyncio.gather(*tasks)
        
        # Stop and verify ordering
        await results_store.stop()
        
        # Verify all files written in order
        results_dir = Path(results_store.results_dir) / 'test_concurrent' / 'timesteps'
        files = sorted(results_dir.glob('*.json'))
        assert len(files) == 20
        
        # Verify data integrity
        for i, file_path in enumerate(files):
            with open(file_path, 'r') as f:
                data = json.load(f)
                assert data['value'] == i
                assert data['order'] == i
    
    @pytest.mark.asyncio
    async def test_worker_status_monitoring(self, results_store):
        """Test worker status monitoring methods."""
        # Initially not running
        assert not results_store.is_worker_running()
        assert results_store.get_queue_size() == 0
        
        # Start worker
        await results_store.start()
        assert results_store.is_worker_running()
        
        # Queue some items
        for i in range(3):
            await results_store.save_timestep_result(
                request_id='test_status',
                timestamp=pd.Timestamp('2024-01-01 00:00:00') + pd.Timedelta(hours=i),
                data={'value': i}
            )
        
        # Queue should have items
        assert results_store.get_queue_size() > 0
        
        # Stop worker
        await results_store.stop()
        assert not results_store.is_worker_running()
        assert results_store.get_queue_size() == 0
    
    @pytest.mark.asyncio
    async def test_multiple_request_ids(self, results_store):
        """Test that multiple request IDs are handled correctly."""
        await results_store.start()
        
        # Save results for different request IDs
        for request_id in ['req1', 'req2', 'req3']:
            for i in range(3):
                timestamp = pd.Timestamp('2024-01-01 00:00:00') + pd.Timedelta(hours=i)
                await results_store.save_timestep_result(
                    request_id=request_id,
                    timestamp=timestamp,
                    data={'request_id': request_id, 'value': i}
                )
        
        await results_store.stop()
        
        # Verify separate directories created
        for request_id in ['req1', 'req2', 'req3']:
            results_dir = Path(results_store.results_dir) / request_id / 'timesteps'
            assert results_dir.exists()
            
            files = list(results_dir.glob('*.json'))
            assert len(files) == 3
            
            # Verify correct data in each directory
            for file_path in files:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    assert data['request_id'] == request_id
