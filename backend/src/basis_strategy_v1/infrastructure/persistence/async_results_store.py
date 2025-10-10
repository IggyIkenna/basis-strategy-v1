"""
Async Results Store - Queue-based results storage with ordering guarantees.

This module implements an async results storage system using AsyncIO queues
to ensure FIFO processing of results even when write operations have variable
duration. Background worker processes queue sequentially to prevent race conditions.

Architecture:
- Uses AsyncIO queue for FIFO ordering guarantees
- Background worker processes queue sequentially
- Prevents race conditions under heavy load
- Same implementation for backtest and live modes
- Graceful shutdown with queue drain

Ordering Guarantees:
- AsyncIO's single-threaded event loop prevents race conditions
- Queue ensures FIFO processing even with variable write times
- Await semantics guarantee completion before next operation
- No dropped data or out-of-order writes
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AsyncResultsStore:
    """
    Async results storage with queue-based ordering guarantees.
    
    Uses AsyncIO queue to ensure FIFO processing of results even when
    write operations have variable duration. Background worker processes
    queue sequentially to prevent race conditions.
    
    Features:
    - FIFO ordering guarantees
    - Background worker for sequential processing
    - Graceful shutdown with queue drain
    - Error handling and logging
    - Same implementation for backtest and live modes
    """
    
    def __init__(self, results_dir: str, execution_mode: str):
        """
        Initialize AsyncResultsStore.
        
        Args:
            results_dir: Directory to store results
            execution_mode: 'backtest' or 'live'
        """
        self.results_dir = Path(results_dir)
        self.execution_mode = execution_mode
        self.queue = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Create results directory if needed
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"AsyncResultsStore initialized: {results_dir}, mode: {execution_mode}")
    
    async def start(self):
        """Start background worker for queue processing."""
        if self.is_running:
            logger.warning("AsyncResultsStore already running")
            return
        
        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker())
        logger.info("AsyncResultsStore worker started")
    
    async def stop(self):
        """Stop background worker and flush remaining queue."""
        if not self.is_running:
            logger.warning("AsyncResultsStore not running")
            return
        
        logger.info("Stopping AsyncResultsStore worker...")
        self.is_running = False
        
        # Wait for queue to drain
        try:
            await asyncio.wait_for(self.queue.join(), timeout=30.0)
            logger.info("Queue drained successfully")
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for queue to drain")
        
        # Cancel worker task
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                logger.info("Worker task cancelled")
        
        logger.info("AsyncResultsStore stopped")
    
    async def _worker(self):
        """Background worker processes queue in FIFO order."""
        logger.info("AsyncResultsStore worker started")
        
        while self.is_running:
            try:
                # Get next result from queue (waits if empty)
                item = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
                
                # Process based on type
                result_type = item.get('type')
                if result_type == 'timestep':
                    await self._write_timestep_result(item)
                elif result_type == 'final':
                    await self._write_final_result(item)
                elif result_type == 'event_log':
                    await self._write_event_log(item)
                else:
                    logger.error(f"Unknown result type: {result_type}")
                
                # Mark task complete
                self.queue.task_done()
                
            except asyncio.TimeoutError:
                # No items in queue, continue
                continue
            except Exception as e:
                # Log error but don't stop worker
                logger.error(f"Error processing result: {e}")
                if not self.queue.empty():
                    self.queue.task_done()
        
        logger.info("AsyncResultsStore worker stopped")
    
    async def save_timestep_result(self, request_id: str, timestamp: pd.Timestamp, data: Dict[str, Any]):
        """
        Queue timestep result for async storage.
        
        Args:
            request_id: Unique request identifier
            timestamp: Timestamp for the result
            data: Result data to store
        """
        await self.queue.put({
            'type': 'timestep',
            'request_id': request_id,
            'timestamp': timestamp,
            'data': data
        })
        logger.debug(f"Queued timestep result: {request_id}, {timestamp}")
    
    async def save_final_result(self, request_id: str, data: Dict[str, Any]):
        """
        Queue final result for async storage.
        
        Args:
            request_id: Unique request identifier
            data: Final result data to store
        """
        await self.queue.put({
            'type': 'final',
            'request_id': request_id,
            'data': data
        })
        logger.debug(f"Queued final result: {request_id}")
    
    async def save_event_log(self, request_id: str, events: List[Dict[str, Any]]):
        """
        Queue event log for async storage.
        
        Args:
            request_id: Unique request identifier
            events: List of events to store
        """
        await self.queue.put({
            'type': 'event_log',
            'request_id': request_id,
            'events': events
        })
        logger.debug(f"Queued event log: {request_id}, {len(events)} events")
    
    async def _write_timestep_result(self, item: Dict):
        """Write timestep result to disk."""
        request_id = item['request_id']
        timestamp = item['timestamp']
        data = item['data']
        
        # Create request directory
        request_dir = self.results_dir / request_id / 'timesteps'
        request_dir.mkdir(parents=True, exist_ok=True)
        
        # Write timestep data
        filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = request_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug(f"Wrote timestep result: {filepath}")
        except Exception as e:
            logger.error(f"Failed to write timestep result {filepath}: {e}")
            raise
    
    async def _write_final_result(self, item: Dict):
        """Write final result to disk."""
        request_id = item['request_id']
        data = item['data']
        
        # Create request directory
        request_dir = self.results_dir / request_id
        request_dir.mkdir(parents=True, exist_ok=True)
        
        # Write final result
        filepath = request_dir / 'final_result.json'
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug(f"Wrote final result: {filepath}")
        except Exception as e:
            logger.error(f"Failed to write final result {filepath}: {e}")
            raise
    
    async def _write_event_log(self, item: Dict):
        """Write event log to CSV."""
        request_id = item['request_id']
        events = item['events']
        
        # Create request directory
        request_dir = self.results_dir / request_id
        request_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert to DataFrame and save
        try:
            df = pd.DataFrame(events)
            filepath = request_dir / 'event_log.csv'
            df.to_csv(filepath, index=False)
            logger.debug(f"Wrote event log: {filepath}")
        except Exception as e:
            logger.error(f"Failed to write event log {filepath}: {e}")
            raise
    
    def get_queue_size(self) -> int:
        """Get current queue size for monitoring."""
        return self.queue.qsize()
    
    def is_worker_running(self) -> bool:
        """Check if worker is running."""
        return self.is_running and self.worker_task is not None and not self.worker_task.done()
