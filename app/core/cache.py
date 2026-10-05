"""In-memory thread-safe TTL Cache layer."""

import time
import asyncio
from typing import Any, Optional, Dict, Tuple
from app.core.config import settings
from app.core.logging import logger


class InMemoryTTLCache:
    """Thread-safe In-Memory Cache with per-key TTL and LRU-style eviction."""

    def __init__(self, maxsize: int = settings.CACHE_MAX_ITEMS):
        self._maxsize = maxsize
        self._store: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expiry_timestamp)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        if not settings.CACHE_ENABLED:
            return None

        async with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None

            value, expires_at = entry
            if time.time() > expires_at:
                del self._store[key]
                return None

            return value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        if not settings.CACHE_ENABLED:
            return

        async with self._lock:
            # Simple eviction if exceeding max capacity
            if len(self._store) >= self._maxsize and key not in self._store:
                # Evict expired keys first
                now = time.time()
                expired = [k for k, (_, exp) in self._store.items() if now > exp]
                if expired:
                    for k in expired:
                        del self._store[k]
                else:
                    # Remove oldest key
                    oldest_key = next(iter(self._store))
                    del self._store[oldest_key]

            expires_at = time.time() + ttl_seconds
            self._store[key] = (value, expires_at)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)


# Global singleton instance
cache = InMemoryTTLCache()
