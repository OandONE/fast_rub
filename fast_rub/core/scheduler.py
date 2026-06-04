import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from collections.abc import Callable


class Scheduler:
    """زمان‌بندی کارهای تکراری"""
    
    def __init__(self, logger: logging.Logger | None = None):
        self._tasks: list[asyncio.Task] = []
        self._logger = logger or logging.getLogger("fast_rub.scheduler")
    
    def every(
        self,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        days: int = 0,
        weeks: int = 0,
        months: int = 0,
        at: str | None = None
    ):
        """تعریف یه کار زمان‌بندی شده"""
        total_seconds = (
            seconds +
            minutes * 60 +
            hours * 3600 +
            days * 86400 +
            weeks * 604800 +
            months * 2592000
        )
        
        def decorator(func: Callable):
            if at:
                task = asyncio.create_task(self._run_daily_at(func, at))
            else:
                task = asyncio.create_task(self._run_interval(func, total_seconds))
            self._tasks.append(task)
            return func
        return decorator
    
    async def _run_interval(self, func: Callable, interval: int):
        """اجرای تکراری با فاصله مشخص"""
        while True:
            await func()
            await asyncio.sleep(interval)
    
    async def _run_daily_at(self, func: Callable, time_str: str):
        """اجرای هر روز در ساعت مشخص"""
        hour, minute = map(int, time_str.split(":"))
        
        while True:
            now = datetime.now()
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if target <= now:
                target += timedelta(days=1)
            
            wait_seconds = (target - now).total_seconds()
            self._logger.info(f"Scheduler: {wait_seconds:.0f} ثانیه تا {time_str}")
            await asyncio.sleep(wait_seconds)
            
            await func()
    
    def cancel_all(self):
        """لغو همه کارهای زمان‌بندی شده"""
        for task in self._tasks:
            if not task.done():
                task.cancel()
        self._tasks.clear()
    
    @property
    def count(self) -> int:
        return len([t for t in self._tasks if not t.done()])