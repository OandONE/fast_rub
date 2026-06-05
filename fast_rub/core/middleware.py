from collections.abc import Callable
from ..utils.filters import Filter
from ..types import Update

import logging

class MiddlewareManager:
    def __init__(
        self,
        logger: logging.Logger | None = None
    ):
        self._middlewares: list = []
        self.logger = logger if logger else logging.Logger("Middleware.Fast_Rub")
    
    def add(
        self,
        middleware: Callable,
        filters: Filter | None = None
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
    
    def _wrap_middleware(self, middleware: Callable, filters: Filter | None, next_handler: Callable):
        async def wrapped(update):
            if filters is not None:
                try:
                    filter_class = type(filters)
                    if "__acall__" in filter_class.__dict__.keys():
                        result = await filters.__acall__(update)
                    else:
                        result = filters(update)
                    if not result:
                        await next_handler(update)
                        return
                except Exception as e:
                    self.logger.error(f"middleware filter error: {e}")
                    await next_handler(update)
                    return
            try:
                await middleware(update, next_handler)
            except Exception as e:
                self.logger.error(f"middleware error: {e}")
                await next_handler(update)
        return wrapped
    
    @property
    def count(self) -> int:
        return len(self._middlewares)
    
    def clear(self):
        self._middlewares.clear()
