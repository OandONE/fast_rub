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
            if inspect.currentframe().f_back.f_code.co_flags & inspect.CO_COROUTINE:
                return coro
            asyncio.create_task(coro)
            return None
        except RuntimeError:
            return asyncio.run(coro)
    return wrapper
