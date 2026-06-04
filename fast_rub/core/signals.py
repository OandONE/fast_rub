from typing import Dict, List, Optional

from collections.abc import Callable


class SignalManager:
    """مدیریت سیگنال‌ها — مثل Django Signals"""
    
    def __init__(self):
        self._signals: dict[str, list[Callable]] = {}
    
    def on(self, signal_name: str):
        """دکوراتور برای ثبت یه Signal Handler"""
        def decorator(func: Callable):
            if signal_name not in self._signals:
                self._signals[signal_name] = []
            self._signals[signal_name].append(func)
            return func
        return decorator
    
    async def emit(self, signal_name: str, *args, **kwargs):
        """اجرای همه Handlerهای یه Signal"""
        if signal_name not in self._signals:
            return
        
        for handler in self._signals[signal_name]:
            try:
                await handler(*args, **kwargs)
            except Exception as e:
                import logging
                logging.getLogger("fast_rub.signals").error(
                    f"Signal '{signal_name}' error: {e}"
                )
    
    def clear(self, signal_name: str | None = None):
        """حذف Handlerها"""
        if signal_name:
            self._signals.pop(signal_name, None)
        else:
            self._signals.clear()
