import asyncio
import functools
import inspect
import threading
from typing import Any, Optional


def _wrap_async_method(obj: Any, method_name: str) -> None:
    func = getattr(obj, method_name)
    main_loop: Optional[asyncio.AbstractEventLoop] = None
    _lock = threading.Lock()
    
    def _get_or_create_loop() -> asyncio.AbstractEventLoop:
        nonlocal main_loop
        with _lock:
            try:
                loop = asyncio.get_running_loop()
                main_loop = loop
                return loop
            except RuntimeError:
                if main_loop is None or main_loop.is_closed():
                    main_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(main_loop)
                return main_loop
    
    def _sync_generator(agen, loop, is_main_thread):
        async def _next(agen):
            try:
                return await agen.__anext__(), False
            except StopAsyncIteration:
                return None, True
        
        while True:
            if is_main_thread:
                item, done = loop.run_until_complete(_next(agen))
            else:
                item, done = asyncio.run_coroutine_threadsafe(
                    _next(agen), loop
                ).result()
            if done:
                break
            yield item
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        coroutine = func(*args, **kwargs)
        loop = _get_or_create_loop()
        is_main = threading.current_thread() is threading.main_thread()
        
        if is_main:
            if loop.is_running():
                return coroutine
            if inspect.iscoroutine(coroutine):
                return loop.run_until_complete(coroutine)
            if inspect.isasyncgen(coroutine):
                return _sync_generator(coroutine, loop, True)
        else:
            if inspect.iscoroutine(coroutine):
                return asyncio.run_coroutine_threadsafe(
                    coroutine, loop
                ).result()
            if inspect.isasyncgen(coroutine):
                return _sync_generator(coroutine, loop, False)
    
    setattr(obj, method_name, sync_wrapper)


def wrap_all_async_methods(cls):
    for name in dir(cls):
        method = getattr(cls, name)
        if not name.startswith("_") and (
            inspect.iscoroutinefunction(method) or inspect.isasyncgenfunction(method)
        ):
            _wrap_async_method(cls, name)


def wrap_module_methods(module):
    for class_name in dir(module):
        cls = getattr(module, class_name)
        if inspect.isclass(cls):
            wrap_all_async_methods(cls)
