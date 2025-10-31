from typing import Any, Optional, Dict, List
import json
import hashlib
import time
from functools import wraps
from fastapi import Request, Response
import logging

logger = logging.getLogger(__name__)

class SimpleCache:
    """Simple in-memory cache with TTL support"""

    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _make_key(self, *args, **kwargs) -> str:
        """Create a cache key from arguments"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            item = self.cache[key]
            if time.time() < item["expires"]:
                return item["value"]
            else:
                # Expired, remove it
                del self.cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL"""
        self.cache[key] = {
            "value": value,
            "expires": time.time() + ttl
        }

    def delete(self, key: str) -> None:
        """Delete from cache"""
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()

# Global cache instance
cache = SimpleCache()

def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{key_prefix}:{func.__name__}:{cache._make_key(*args, **kwargs)}"

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {cache_key}")

            return result
        return wrapper
    return decorator

def cache_response(ttl: int = 300):
    """Decorator for caching FastAPI responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from args (FastAPI dependency injection)
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request:
                # Create cache key from request
                cache_key = f"response:{request.method}:{request.url.path}:{request.query_params}"

                # Try cache
                cached_response = cache.get(cache_key)
                if cached_response:
                    logger.debug(f"Response cache hit for {cache_key}")
                    return Response(
                        content=cached_response["content"],
                        status_code=cached_response["status_code"],
                        headers=cached_response["headers"]
                    )

            # Execute function
            response = await func(*args, **kwargs)

            # Cache response if it's successful
            if request and hasattr(response, 'status_code') and response.status_code < 400:
                cache_data = {
                    "content": response.body if hasattr(response, 'body') else str(response),
                    "status_code": response.status_code,
                    "headers": dict(response.headers) if hasattr(response, 'headers') else {}
                }
                cache.set(cache_key, cache_data, ttl)
                logger.debug(f"Cached response for {cache_key}")

            return response
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Invalidate cache entries matching pattern"""
    keys_to_delete = [key for key in cache.cache.keys() if pattern in key]
    for key in keys_to_delete:
        cache.delete(key)
    logger.debug(f"Invalidated {len(keys_to_delete)} cache entries matching {pattern}")

# Cache management functions
def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    total_entries = len(cache.cache)
    expired_entries = sum(1 for item in cache.cache.values()
                         if time.time() > item["expires"])

    return {
        "total_entries": total_entries,
        "expired_entries": expired_entries,
        "active_entries": total_entries - expired_entries
    }

def clear_expired_cache():
    """Clear expired cache entries"""
    current_time = time.time()
    expired_keys = [key for key, item in cache.cache.items()
                   if current_time > item["expires"]]

    for key in expired_keys:
        del cache.cache[key]

    logger.debug(f"Cleared {len(expired_keys)} expired cache entries")