import asyncio
import logging
from typing import Any

from collections.abc import Callable, Coroutine


class BackgroundManager:
    """مدیریت تسک‌های بک‌گراند"""
    
    def __init__(self, logger: logging.Logger | None = None):
        self._tasks: list[asyncio.Task] = []
        self._logger = logger or logging.getLogger("fast_rub.background")
    
    def add(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        *args,
        delay: float = 0.0,
        **kwargs
    ) -> asyncio.Task:
        """
        اضافه کردن یه تسک بک‌گراند.
        Example:
            bot.add_background_task(send_report, chat_id, delay=5.0)
        """
        async def _wrapper():
            try:
                if delay > 0:
                    await asyncio.sleep(delay)
                await coro(*args, **kwargs)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                self._logger.error(f"Background task error: {e}")
        
        task = asyncio.create_task(_wrapper())
        self._tasks.append(task)
        
        self._tasks = [t for t in self._tasks if not t.done()]
        
        return task
    
    @property
    def count(self) -> int:
        """تعداد تسک‌های فعال"""
        return len([t for t in self._tasks if not t.done()])
    
    def cancel_all(self):
        """لغو همه تسک‌ها"""
        for task in self._tasks:
            if not task.done():
                task.cancel()
        self._tasks.clear()
    
    async def wait_all(self):
        """منتظر موندن برای همه تسک‌ها"""
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
