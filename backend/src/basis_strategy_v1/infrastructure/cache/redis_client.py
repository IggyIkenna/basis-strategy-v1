"""Redis client for caching, session storage, and real-time messaging."""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import asyncio

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client for caching, session storage, and pub/sub.
    
    Handles:
    - Backtest session storage (running_backtests)
    - Market data caching (rate lookups)
    - Real-time progress updates (pub/sub)
    - Component result caching
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", enabled: bool = True):
        self.redis_url = redis_url
        self.enabled = enabled and REDIS_AVAILABLE
        self.client = None
        self.pubsub = None
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - install redis package for full functionality")
            self.enabled = False
        
        if self.enabled:
            self.client = redis.from_url(redis_url, decode_responses=True)
            logger.info(f"Redis client configured: {redis_url}")
        else:
            logger.info("Redis disabled - using in-memory fallback")
    
    async def connect(self) -> bool:
        """Connect to Redis and test connectivity."""
        if not self.enabled:
            return False
        
        try:
            await self.client.ping()
            logger.info("✅ Redis connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.enabled = False
            return False
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.client and self.enabled:
            await self.client.close()
            logger.info("Redis connection closed")
    
    # === SESSION STORAGE (for running backtests) ===
    
    async def store_backtest_session(self, request_id: str, session_data: Dict[str, Any], ttl_seconds: int = 3600) -> bool:
        """Store backtest session data with TTL."""
        if not self.enabled:
            return False
        
        try:
            # Serialize session data
            session_json = json.dumps(session_data, default=str)
            
            # Store with TTL
            await self.client.setex(f"backtest:session:{request_id}", ttl_seconds, session_json)
            logger.debug(f"Stored backtest session: {request_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to store backtest session {request_id}: {e}")
            return False
    
    async def get_backtest_session(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get backtest session data."""
        if not self.enabled:
            return None
        
        try:
            session_json = await self.client.get(f"backtest:session:{request_id}")
            if session_json:
                return json.loads(session_json)
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get backtest session {request_id}: {e}")
            return None
    
    async def update_backtest_progress(self, request_id: str, progress: float, status: str) -> bool:
        """Update backtest progress and publish to subscribers."""
        if not self.enabled:
            return False
        
        try:
            # Update session
            session_data = await self.get_backtest_session(request_id)
            if session_data:
                session_data['progress'] = progress
                session_data['status'] = status
                session_data['updated_at'] = datetime.utcnow().isoformat()
                await self.store_backtest_session(request_id, session_data)
            
            # Publish progress update
            progress_update = {
                'request_id': request_id,
                'progress': progress,
                'status': status,
                'timestamp': datetime.utcnow().isoformat()
            }
            await self.client.publish(f"backtest:progress:{request_id}", json.dumps(progress_update))
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to update backtest progress {request_id}: {e}")
            return False
    
    # === MARKET DATA CACHING ===
    
    async def cache_market_data(self, key: str, data: Any, ttl_seconds: int = 300) -> bool:
        """Cache market data (rates, prices) with TTL."""
        if not self.enabled:
            return False
        
        try:
            data_json = json.dumps(data, default=str)
            await self.client.setex(f"market:{key}", ttl_seconds, data_json)
            return True
            
        except Exception as e:
            logger.warning(f"Failed to cache market data {key}: {e}")
            return False
    
    async def get_cached_market_data(self, key: str) -> Optional[Any]:
        """Get cached market data."""
        if not self.enabled:
            return None
        
        try:
            data_json = await self.client.get(f"market:{key}")
            if data_json:
                return json.loads(data_json)
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get cached market data {key}: {e}")
            return None
    
    # === COMPONENT RESULT CACHING ===
    
    async def cache_component_results(self, request_id: str, component_name: str, results: Dict[str, Any], ttl_seconds: int = 1800) -> bool:
        """Cache component execution results."""
        if not self.enabled:
            return False
        
        try:
            results_json = json.dumps(results, default=str)
            await self.client.setex(f"component:{request_id}:{component_name}", ttl_seconds, results_json)
            return True
            
        except Exception as e:
            logger.warning(f"Failed to cache component results {request_id}:{component_name}: {e}")
            return False
    
    # === PUB/SUB FOR REAL-TIME UPDATES ===
    
    async def subscribe_to_backtest_updates(self, request_id: str, callback):
        """Subscribe to real-time backtest updates."""
        if not self.enabled:
            return
        
        try:
            pubsub = self.client.pubsub()
            await pubsub.subscribe(f"backtest:progress:{request_id}")
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    update = json.loads(message['data'])
                    await callback(update)
                    
        except Exception as e:
            logger.error(f"Error subscribing to backtest updates {request_id}: {e}")
    
    # === UTILITY METHODS ===
    
    async def clear_expired_sessions(self) -> int:
        """Clear expired backtest sessions."""
        if not self.enabled:
            return 0
        
        try:
            # Get all backtest session keys
            keys = await self.client.keys("backtest:session:*")
            
            # Check TTL and remove expired
            expired_count = 0
            for key in keys:
                ttl = await self.client.ttl(key)
                if ttl == -1:  # No expiry set
                    await self.client.expire(key, 3600)  # Set 1 hour expiry
                elif ttl == -2:  # Key doesn't exist
                    expired_count += 1
            
            logger.info(f"Cleared {expired_count} expired backtest sessions")
            return expired_count
            
        except Exception as e:
            logger.warning(f"Failed to clear expired sessions: {e}")
            return 0
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get Redis health status for monitoring."""
        if not self.enabled:
            return {"status": "disabled", "redis_available": False}
        
        try:
            # Test basic operations
            test_key = "health:test"
            await self.client.set(test_key, "test", ex=10)
            test_value = await self.client.get(test_key)
            await self.client.delete(test_key)
            
            # Get Redis info
            info = await self.client.info()
            
            return {
                "status": "healthy",
                "redis_available": True,
                "connected_clients": info.get('connected_clients', 0),
                "used_memory_human": info.get('used_memory_human', 'unknown'),
                "redis_version": info.get('redis_version', 'unknown'),
                "test_operation": "success" if test_value == "test" else "failed"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy", 
                "redis_available": False,
                "error": str(e)
            }


# Singleton pattern for application-wide Redis client
_redis_client = None

async def get_redis_client(redis_url: str = None, enabled: bool = True) -> RedisClient:
    """Get singleton Redis client."""
    global _redis_client
    
    if _redis_client is None:
        from ..config.config_manager import get_settings
        settings = get_settings()
        
        redis_config = settings.get('redis', {})
        url = redis_url or redis_config.get('url', 'redis://localhost:6379/0')
        enabled = enabled and redis_config.get('enabled', True)
        
        _redis_client = RedisClient(redis_url=url, enabled=enabled)
        
        # Test connection on first access
        if enabled:
            connected = await _redis_client.connect()
            if not connected:
                logger.warning("Redis connection failed - continuing with in-memory fallback")
    
    return _redis_client
