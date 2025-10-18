#!/usr/bin/env python3
"""
API Call Queue

Implements sequential API call processing to prevent race conditions and ensure
proper ordering of API requests per ADR-006 requirements.

Reference: docs/LOGICAL_EXCEPTIONS_GUIDE.md - API Call Queueing Pattern
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)


@dataclass
class APICall:
    """Represents a queued API call"""
    call_id: str
    func: Callable
    args: Tuple
    kwargs: Dict[str, Any]
    timestamp: datetime
    timeout: Optional[float] = None
    priority: int = 0  # Higher number = higher priority


class APICallQueue:
    """
    Queue for sequential API call processing to prevent race conditions.
    
    All concurrent API calls are queued and processed sequentially to ensure:
    - No race conditions between API calls
    - FIFO ordering guaranteed
    - Proper timeout handling per call
    - Sequential processing even with variable response times
    """
    
    def __init__(self, max_queue_size: int = 1000, default_timeout: float = 30.0):
        self.queue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self.worker_task: Optional[asyncio.Task] = None
        self.results: Dict[str, Any] = {}
        self.errors: Dict[str, Exception] = {}
        self.default_timeout = default_timeout
        self.is_running = False
        self._shutdown_event = asyncio.Event()
        
        logger.info(f"Initialized APICallQueue with max_size={max_queue_size}, timeout={default_timeout}s")
    
    async def start(self) -> None:
        """Start the API call queue worker"""
        if self.is_running:
            logger.warning("API call queue is already running")
            return
        
        self.is_running = True
        self._shutdown_event.clear()
        self.worker_task = asyncio.create_task(self._worker())
        logger.info("✅ API call queue worker started")
    
    async def stop(self) -> None:
        """Stop the API call queue worker"""
        if not self.is_running:
            logger.warning("API call queue is not running")
            return
        
        self.is_running = False
        self._shutdown_event.set()
        
        if self.worker_task:
            await self.worker_task
            self.worker_task = None
        
        logger.info("✅ API call queue worker stopped")
    
    async def enqueue_call(
        self, 
        func: Callable, 
        *args, 
        timeout: Optional[float] = None,
        priority: int = 0,
        **kwargs
    ) -> str:
        """
        Enqueue an API call for sequential processing.
        
        Args:
            func: The async function to call
            *args: Positional arguments for the function
            timeout: Timeout for this specific call (defaults to queue timeout)
            priority: Priority level (higher number = higher priority)
            **kwargs: Keyword arguments for the function
            
        Returns:
            call_id: Unique identifier for tracking the call result
        """
        call_id = str(uuid.uuid4())
        timeout = timeout or self.default_timeout
        
        api_call = APICall(
            call_id=call_id,
            func=func,
            args=args,
            kwargs=kwargs,
            timestamp=datetime.now(timezone.utc),
            timeout=timeout,
            priority=priority
        )
        
        try:
            # Use negative priority for PriorityQueue (higher priority = lower number)
            await self.queue.put((-priority, api_call))
            logger.debug(f"Enqueued API call {call_id} with priority {priority}")
            return call_id
        except asyncio.QueueFull:
            logger.error(f"API call queue is full, cannot enqueue call {call_id}")
            raise RuntimeError("API call queue is full")
    
    async def get_result(self, call_id: str, timeout: Optional[float] = None) -> Any:
        """
        Get the result of a queued API call.
        
        Args:
            call_id: The call ID returned by enqueue_call
            timeout: How long to wait for the result
            
        Returns:
            The result of the API call
            
        Raises:
            TimeoutError: If the result is not available within timeout
            KeyError: If the call_id is not found
            Exception: The exception that occurred during the API call
        """
        timeout = timeout or self.default_timeout
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check if we have the result
            if call_id in self.results:
                result = self.results.pop(call_id)
                logger.debug(f"Retrieved result for API call {call_id}")
                return result
            
            # Check if there was an error
            if call_id in self.errors:
                error = self.errors.pop(call_id)
                logger.error(f"API call {call_id} failed: {error}")
                raise error
            
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                logger.error(f"Timeout waiting for API call {call_id} result")
                raise TimeoutError(f"API call {call_id} timed out after {timeout}s")
            
            # Wait a bit before checking again
            await asyncio.sleep(0.1)
    
    async def _worker(self) -> None:
        """Worker that processes API calls sequentially"""
        logger.info("🔄 API call queue worker started")
        
        while self.is_running:
            try:
                # Wait for next API call or shutdown signal
                try:
                    _, api_call = await asyncio.wait_for(
                        self.queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    # Check for shutdown signal
                    if self._shutdown_event.is_set():
                        break
                    continue
                
                # Process the API call
                await self._process_api_call(api_call)
                
                # Mark task as done
                self.queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in API call queue worker: {e}")
                await asyncio.sleep(1.0)  # Brief pause before continuing
        
        logger.info("🔄 API call queue worker stopped")
    
    async def _process_api_call(self, api_call: APICall) -> None:
        """Process a single API call"""
        logger.debug(f"Processing API call {api_call.call_id}")
        
        try:
            # Execute the API call with timeout
            result = await asyncio.wait_for(
                api_call.func(*api_call.args, **api_call.kwargs),
                timeout=api_call.timeout
            )
            
            # Store the result
            self.results[api_call.call_id] = result
            logger.debug(f"✅ API call {api_call.call_id} completed successfully")
            
        except asyncio.TimeoutError:
            error = TimeoutError(f"API call {api_call.call_id} timed out after {api_call.timeout}s")
            self.errors[api_call.call_id] = error
            logger.error(f"⏰ API call {api_call.call_id} timed out")
            
        except Exception as e:
            self.errors[api_call.call_id] = e
            logger.error(f"❌ API call {api_call.call_id} failed: {e}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            'is_running': self.is_running,
            'queue_size': self.queue.qsize(),
            'pending_results': len(self.results),
            'pending_errors': len(self.errors),
            'worker_running': self.worker_task is not None and not self.worker_task.done()
        }


class APICallManager:
    """
    Manager for API call queues across different services.
    
    Provides a centralized way to manage API calls for different services
    while maintaining sequential processing per service.
    """
    
    def __init__(self):
        self.queues: Dict[str, APICallQueue] = {}
        self.default_queue = APICallQueue()
        self.is_running = False
    
    async def start(self) -> None:
        """Start all API call queues"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start default queue
        await self.default_queue.start()
        
        # Start service-specific queues
        for service_name, queue in self.queues.items():
            await queue.start()
        
        logger.info("✅ API call manager started")
    
    async def stop(self) -> None:
        """Stop all API call queues"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Stop default queue
        await self.default_queue.stop()
        
        # Stop service-specific queues
        for service_name, queue in self.queues.items():
            await queue.stop()
        
        logger.info("✅ API call manager stopped")
    
    def get_queue(self, service_name: Optional[str] = None) -> APICallQueue:
        """Get API call queue for a specific service"""
        if service_name is None:
            return self.default_queue
        
        if service_name not in self.queues:
            self.queues[service_name] = APICallQueue()
            logger.info(f"Created new API call queue for service: {service_name}")
        
        return self.queues[service_name]
    
    async def enqueue_call(
        self, 
        func: Callable, 
        *args, 
        service_name: Optional[str] = None,
        timeout: Optional[float] = None,
        priority: int = 0,
        **kwargs
    ) -> str:
        """Enqueue an API call for a specific service"""
        queue = self.get_queue(service_name)
        return await queue.enqueue_call(
            func, *args, timeout=timeout, priority=priority, **kwargs
        )
    
    async def get_result(
        self, 
        call_id: str, 
        service_name: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """Get result for an API call"""
        queue = self.get_queue(service_name)
        return await queue.get_result(call_id, timeout=timeout)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all API call queues"""
        status = {
            'is_running': self.is_running,
            'default_queue': self.default_queue.get_queue_status(),
            'service_queues': {}
        }
        
        for service_name, queue in self.queues.items():
            status['service_queues'][service_name] = queue.get_queue_status()
        
        return status


# Global API call manager instance
api_call_manager = APICallManager()


async def enqueue_api_call(
    func: Callable,
    *args,
    service_name: Optional[str] = None,
    timeout: Optional[float] = None,
    priority: int = 0,
    **kwargs
) -> str:
    """
    Convenience function to enqueue an API call.
    
    This is the recommended way to make API calls to ensure proper queueing.
    """
    return await api_call_manager.enqueue_call(
        func, *args, service_name=service_name, timeout=timeout, priority=priority, **kwargs
    )


async def get_api_result(
    call_id: str,
    service_name: Optional[str] = None,
    timeout: Optional[float] = None
) -> Any:
    """
    Convenience function to get API call result.
    """
    return await api_call_manager.get_result(call_id, service_name=service_name, timeout=timeout)


# Example usage:
"""
# Enqueue an API call
call_id = await enqueue_api_call(
    fetch_price_data,
    symbol="ETHUSDT",
    service_name="binance",
    timeout=10.0,
    priority=1
)

# Get the result
try:
    result = await get_api_result(call_id, service_name="binance", timeout=15.0)
    logger.info(f"Price data: {result}")
except TimeoutError:
    logger.warning("API call timed out")
except Exception as e:
    logger.error(f"API call failed: {e}")
"""
