import asyncio
import logging
from datetime import datetime, timedelta
from .async_sync import wrap_all_async_methods
from ..utils import Utils

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

    @staticmethod
    def _parse_cron_field(field: str, min_val: int, max_val: int) -> set[int]:
        """پارس یک فیلد cron به مجموعه مقادیر"""
        values = set()
        for part in field.split(","):
            if "/" in part:
                base, step = part.split("/")
                step = int(step)
                if base == "*":
                    start, end = min_val, max_val
                elif "-" in base:
                    start, end = map(int, base.split("-"))
                else:
                    start, end = int(base), max_val
                values.update(range(start, end + 1, step))
            elif "-" in part:
                start, end = map(int, part.split("-"))
                values.update(range(start, end + 1))
            elif part == "*":
                values.update(range(min_val, max_val + 1))
            else:
                values.add(int(part))
        return values

    @staticmethod
    def _next_cron_time(minutes, hours, days, months, weekdays) -> datetime | None:
        """پیدا کردن زمان بعدی که با cron مچ میشه"""
        now = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1)
        max_iter = 525600 * 5  # تا ۵ سال
        for _ in range(max_iter):
            if (
                now.minute in minutes
                and now.hour in hours
                and now.day in days
                and now.month in months
                and ((now.weekday() + 1) % 7) in weekdays
            ):
                return now
            now += timedelta(minutes=1)
        return None

    async def _run_cron(self, func, minutes, hours, days, months, weekdays):
        """حلقه اجرای cron"""
        while True:
            target = self._next_cron_time(minutes, hours, days, months, weekdays)
            if target is None:
                self._logger.error("Cron: no matching time in the next 5 years")
                return
            wait = (target - datetime.now()).total_seconds()
            self._logger.info(f"Cron: next run at {target} ({wait:.0f}s)")
            await asyncio.sleep(wait)
            await Utils.run_handler(func)

    def add_cron(self, cron_expr: str, func: Callable):
        """اضافه کردن یه تسک با سینتکس cron لینوکس"""
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError(
                "Cron expression must have 5 fields: minute hour day month weekday"
            )

        minutes = self._parse_cron_field(parts[0], 0, 59)
        hours = self._parse_cron_field(parts[1], 0, 23)
        days = self._parse_cron_field(parts[2], 1, 31)
        months = self._parse_cron_field(parts[3], 1, 12)
        weekdays = self._parse_cron_field(parts[4], 0, 7)

        # Normalize 7 -> 0 (Sunday)
        if 7 in weekdays:
            weekdays.discard(7)
            weekdays.add(0)

        task = asyncio.create_task(
            self._run_cron(func, minutes, hours, days, months, weekdays)
        )
        self._tasks.append(task)
        return func

    def cron(self, cron_expr: str):
        """دکوراتور برای زمان‌بندی با cron"""
        def decorator(func: Callable):
            return self.add_cron(cron_expr, func)
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
            
            await Utils.run_handler(func)
    
    def cancel_all(self):
        """لغو همه کارهای زمان‌بندی شده"""
        for task in self._tasks:
            if not task.done():
                task.cancel()
        self._tasks.clear()
    
    @property
    def count(self) -> int:
        return len([t for t in self._tasks if not t.done()])

wrap_all_async_methods(Scheduler)
