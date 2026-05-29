from typing import Callable, Optional
from ..utils.filters import Filter
from ..type import Update

class MiddlewareManager:
    def __init__(self):
        self._middlewares: list = []
    
    def add(
        self,
        middleware: Callable,
        filters: Optional[Filter] = None
    ):
        """اضافه کردن Middleware"""
        self._middlewares.append({
            "handler": middleware,
            "filters": filters
        })
    
    def remove(self, middleware: Callable):
        for item in self._middlewares:
            if item["handler"] == middleware:
                self._middlewares.remove(item)
                break
    
    async def execute(self, update: Update, handler: Callable):
        """اجرای زنجیره Middlewareها"""
        chain = handler
        for item in reversed(self._middlewares):
            middleware_func = item["handler"]
            filters = item["filters"]
            chain = self._wrap_middleware(middleware_func, filters, chain)
        await chain(update)
    
    def _wrap_middleware(self, middleware: Callable, filters: Optional[Filter], next_handler: Callable):
        async def wrapped(update):
            if filters is not None:
                try:
                    if not filters(update):
                        await next_handler(update)
                        return
                except Exception:
                    await next_handler(update)
                    return
            await middleware(update, next_handler)
        return wrapped
    
    @property
    def count(self) -> int:
        return len(self._middlewares)
    
    def clear(self):
        self._middlewares.clear()
