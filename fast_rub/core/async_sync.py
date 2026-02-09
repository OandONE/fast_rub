import asyncio
import inspect
from functools import wraps

def async_to_sync(func):
    """دکوراتور برای تبدیل تابع async به sync"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
            async def coro_wrapper():
                return await func(*args, **kwargs)
            return coro_wrapper()
        except RuntimeError:
            return asyncio.run(func(*args, **kwargs))
    return wrapper


def auto_async(func):
    """دکوراتور برای تبدیل تابع async به sync"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        if not inspect.isawaitable(coro):
            return coro
        try:
            loop = asyncio.get_running_loop()
            in_co=inspect.currentframe()
            if in_co:
                f_co=in_co.f_back
                if f_co:
                    if f_co.f_back:
                        if f_co.f_code.co_flags & inspect.CO_COROUTINE:
                            return coro
            async def run_awaitable():
                return await coro
            asyncio.create_task(run_awaitable())
            return None
        except RuntimeError:
            async def run_wrapper():
                return await coro
            return asyncio.run(run_wrapper())
    return wrapper

