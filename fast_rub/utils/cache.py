import time
import asyncio
from typing import Any

from ..core.async_sync import wrap_all_async_methods

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
        self._enabled = True
        self._cache: dict[str, tuple[float, Any]] = {}
        self._frozen = False
        self._frozen_at: float | None = None
        self._frozen_duration: float = 0.0
        self._lock = asyncio.Lock()
    
    async def get(
        self,
        key: str
    ) -> Any:
        async with self._lock:
            if not self._enabled:
                return None
            if key in self._cache:
                timestamp, value = self._cache[key]
                if self._elapsed(timestamp) < self.ttl:
                    return value
                del self._cache[key]
        return None
    
    async def set(
        self,
        key: str,
        value: Any
    ):
        async with self._lock:
            if len(self._cache) >= self.max_size:
                oldest = min(self._cache, key=lambda k: self._cache[k][0])
                del self._cache[oldest]
            self._cache[key] = (time.time(), value)
    
    async def clear(self):
        async with self._lock:
            self._cache.clear()

    async def disable(self):
        """غیرفعال کردن موقت کش"""
        async with self._lock:
            self._enabled = False

    async def enable(self):
        """فعال کردن دوباره کش"""
        async with self._lock:
            self._enabled = True

    async def is_enabled(self) -> bool:
        """وضعیت فعلی کش"""
        async with self._lock:
            return self._enabled

    async def refresh(
        self,
        key: str
    ):
        """حذف یه کلید خاص از کش"""
        async with self._lock:
            self._cache.pop(key, None)

    async def freeze(self):
        """فریز کردن کش. تایمر TTL متوقف میشه."""
        async with self._lock:
            if not self._frozen:
                self._frozen = True
                self._frozen_at = time.time()

    async def unfreeze(self):
        """آنفریز کردن کش. تایمر TTL ادامه پیدا میکنه."""
        async with self._lock:
            if self._frozen:
                self._frozen = False
                if self._frozen_at:
                    self._frozen_duration += time.time() - self._frozen_at
                    self._frozen_at = None

    async def is_frozen(self) -> bool:
        """وضعیت فریز"""
        async with self._lock:
            return self._frozen

    def _elapsed(
        self,
        timestamp: float
    ) -> float:
        """زمان گذشته واقعی منهای زمان فریز شده"""
        if self._frozen:
            now: float = self._frozen_at # pyright: ignore[reportAssignmentType]
        else:
            now = time.time()
        return (now - timestamp) - self._frozen_duration

wrap_all_async_methods(Cache)
