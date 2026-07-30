import time
import asyncio
from typing import Any

class Cache:
    """کش عمومی با TTL"""
    def __init__(
        self,
        ttl: float | None = None,
        max_size: int | None = None
    ):
        if not ttl:
            ttl = 300.0
        if not max_size:
            max_size = 100
        self.ttl = ttl
        self.max_size = max_size
        self._cache: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Any:
        async with self._lock:
            if key in self._cache:
                timestamp, value = self._cache[key]
                if time.time() - timestamp < self.ttl:
                    return value
                del self._cache[key]
        return None
    
    async def set(self, key: str, value: Any):
        async with self._lock:
            if len(self._cache) >= self.max_size:
                oldest = min(self._cache, key=lambda k: self._cache[k][0])
                del self._cache[oldest]
            self._cache[key] = (time.time(), value)
    
    async def clear(self):
        async with self._lock:
            self._cache.clear()
