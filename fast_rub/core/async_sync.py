import asyncio
import functools
import inspect
import threading


def _wrap_async_method(obj, method_name):
    """
    یه متد Async رو به Sync تبدیل می‌کنه.
    الهام گرفته از aiogram و python-telegram-bot.
    """
    func = getattr(obj, method_name)
    main_loop = asyncio.get_event_loop()

    def _sync_generator(agen, loop, is_main_thread):
        """Async Generator رو به Sync تبدیل می‌کنه"""
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

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        is_main = threading.current_thread() is threading.main_thread()

        if is_main or not main_loop.is_running():
            if loop.is_running():
                return coroutine
            else:
                if inspect.iscoroutine(coroutine):
                    return loop.run_until_complete(coroutine)
                if inspect.isasyncgen(coroutine):
                    return _sync_generator(coroutine, loop, True)
        else:
            if inspect.iscoroutine(coroutine):
                if loop.is_running():
                    async def _await_wrapper():
                        return await asyncio.wrap_future(
                            asyncio.run_coroutine_threadsafe(coroutine, main_loop)
                        )
                    return _await_wrapper()
                else:
                    return asyncio.run_coroutine_threadsafe(
                        coroutine, main_loop
                    ).result()

            if inspect.isasyncgen(coroutine):
                if loop.is_running():
                    return coroutine
                else:
                    return _sync_generator(coroutine, main_loop, False)

    sync_wrapper.__annotations__ = func.__annotations__.copy()
    sync_wrapper.__annotations__.pop("return", None)
    
    setattr(obj, method_name, sync_wrapper)


def wrap_all_async_methods(cls):
    """
    همه متدهای Async یه کلاس رو اتوماتیک به Sync تبدیل می‌کنه.
    """
    for name in dir(cls):
        method = getattr(cls, name)
        if not name.startswith("_") and (
            inspect.iscoroutinefunction(method) or inspect.isasyncgenfunction(method)
        ):
            _wrap_async_method(cls, name)


def wrap_module_methods(module):
    """
    همه متدهای Async توی یه ماژول رو Sync می‌کنه.
    """
    for class_name in dir(module):
        cls = getattr(module, class_name)
        if inspect.isclass(cls):
            wrap_all_async_methods(cls)
