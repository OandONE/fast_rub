from typing import Callable, Optional, List
from ..types import Update


class MiddlewareManager:
    """مدیریت Middlewareها"""
    
    def __init__(self):
        self._middlewares: List[Callable] = []
    
    def add(
        self,
        middleware: Callable
    ):
        """اضافه کردن یه Middleware"""
        self._middlewares.append(middleware)
    
    def remove(
        self,
        middleware: Callable
    ):
        """حذف یه Middleware"""
        if middleware in self._middlewares:
            self._middlewares.remove(middleware)
    
    async def execute(
        self,
        update: Update,
        handler: Callable,
        *args,
        **kwargs
    ):
        """
        اجرای زنجیره‌ای Middlewareها و هندلر اصلی.
        
        هر Middleware می‌تونه:
        - await next_handler(update) رو صدا بزنه (ادامه بده)
        - یه کار دیگه بکنه (بلاک کنه)
        """
        # ساخت زنجیره
        chain = handler
        for middleware in reversed(self._middlewares):
            chain = self._wrap_middleware(middleware, chain)
        
        # اجرا
        await chain(update)
    
    def _wrap_middleware(
        self,
        middleware: Callable,
        next_handler: Callable
    ) -> Callable:
        """یه Middleware رو دور next_handler می‌پیچه"""
        async def wrapped(update: Update):
            await middleware(update, next_handler)
        return wrapped
    
    @property
    def count(self) -> int:
        return len(self._middlewares)
    
    def clear(self):
        """حذف همه Middlewareها"""
        self._middlewares.clear()
