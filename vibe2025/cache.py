import logging
from datetime import datetime, timedelta
from typing import Optional
from cachetools import TTLCache
import threading

logger = logging.getLogger(__name__)


class ForexCache:
    """Thread-safe cache for forex exchange rates with TTL."""

    def __init__(self, ttl_seconds: int = 3600, maxsize: int = 1000):
        """
        Initialize forex cache.

        Args:
            ttl_seconds: Time-to-live for cached rates in seconds (default: 1 hour)
            maxsize: Maximum number of cached rate pairs (default: 1000)
        """
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self._lock = threading.Lock()
        self.ttl_seconds = ttl_seconds
        logger.info(f"ForexCache initialized: TTL={ttl_seconds}s, maxsize={maxsize}")

    def _make_key(self, source: str, target: str) -> str:
        """Create cache key from currency pair."""
        return f"{source.upper()}_{target.upper()}"

    def get(self, source: str, target: str) -> Optional[float]:
        """
        Get cached exchange rate.

        Args:
            source: Source currency code
            target: Target currency code

        Returns:
            Cached rate or None if not found/expired
        """
        key = self._make_key(source, target)
        with self._lock:
            rate = self._cache.get(key)
            if rate is not None:
                logger.debug(f"Cache HIT: {key} = {rate}")
            else:
                logger.debug(f"Cache MISS: {key}")
            return rate

    def set(self, source: str, target: str, rate: float) -> None:
        """
        Store exchange rate in cache.

        Args:
            source: Source currency code
            target: Target currency code
            rate: Exchange rate value
        """
        key = self._make_key(source, target)
        with self._lock:
            self._cache[key] = rate
            logger.debug(f"Cache SET: {key} = {rate}")

    def clear(self) -> None:
        """Clear all cached rates."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def get_stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            return {
                "size": len(self._cache),
                "maxsize": self._cache.maxsize,
                "ttl_seconds": self.ttl_seconds
            }


# Global cache instance
forex_cache = ForexCache(ttl_seconds=3600, maxsize=1000)
