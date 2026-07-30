from typing import TYPE_CHECKING, Literal, Any

from collections.abc import Awaitable, Callable
import inspect
import time as ti

from ..db import DataBase

if TYPE_CHECKING:
    from ..types import UpdateButton


class InlineFilter:
    def __call__(self, upd_btn: "UpdateButton") -> bool:
        raise NotImplementedError
    async def __acall__(self, upd_btn: "UpdateButton") -> bool:
        return self(upd_btn)

    def __and__(self, other: 'InlineFilter') -> '_InlineAndFilter':
        return _InlineAndFilter(self, other)
    
    def __or__(self, other: 'InlineFilter') -> '_InlineOrFilter':
        return _InlineOrFilter(self, other)

    def __invert__(self) -> 'InlineFilter':
        return _InlineNotFilter(self)

class InlineAsyncFilter(InlineFilter):
    def __call__(self, upd_btn: "UpdateButton") -> bool:
        raise RuntimeError("The Class Is Async. Sync -> Filter class")
    async def __acall__(self, upd_btn: "UpdateButton") -> bool:
        raise NotImplementedError

class _InlineAndFilter(InlineFilter):
    def __init__(
        self,
        left: InlineFilter,
        right: InlineFilter
    ) -> None:
        self.left = left
        self.right = right
    
    def __call__(self, upd_btn: "UpdateButton") -> bool:
        return self.left(upd_btn) and self.right(upd_btn)

class _InlineOrFilter(InlineFilter):
    def __init__(
        self,
        left: InlineFilter,
        right: InlineFilter
    ) -> None:
        self.left = left
        self.right = right
    
    def __call__(self, upd_btn: "UpdateButton") -> bool:
        return self.left(upd_btn) or self.right(upd_btn)

class _InlineNotFilter(InlineFilter):
    def __init__(
        self,
        filter: InlineFilter
    ) -> None:
        self.filter = filter
    
    def __call__(self, upd_btn: "UpdateButton") -> bool:
        return not self.filter(upd_btn)


class button_id(InlineFilter):
    def __init__(
        self,
        button_id: str
    ) -> None:
        self.button_id = button_id
    def __call__(self, upd_btn: "UpdateButton") -> bool:
        return upd_btn.button_id == self.button_id

class startswith_button_id(InlineFilter):
    def __init__(
        self,
        button_id: str | tuple[str]
    ) -> None:
        self.button_id = button_id
    def __call__(self, upd_btn: "UpdateButton") -> bool:
        return upd_btn.button_id.startswith(self.button_id)

class endswith_button_id(InlineFilter):
    def __init__(
        self,
        button_id: str | tuple[str]
    ) -> None:
        self.button_id = button_id
    def __call__(self, upd_btn: "UpdateButton") -> bool:
        return upd_btn.button_id.endswith(self.button_id)


class chat_ids(InlineFilter):
    def __init__(
        self,
        chat_ids: str | list[str]
    ) -> None:
        self.chat_ids = chat_ids if isinstance(chat_ids, list) else [chat_ids]
    def __call__(self, upd_btn: "UpdateButton") -> bool:
        return upd_btn.chat_id in self.chat_ids

class sender_ids(InlineFilter):
    def __init__(
        self,
        sender_ids: str | list[str]
    ) -> None:
        self.sender_ids = sender_ids if isinstance(sender_ids, list) else [sender_ids]
    def __call__(self, upd_btn: "UpdateButton") -> bool:
        return upd_btn.sender_id in self.sender_ids


class text(InlineFilter):
    def __init__(
        self,
        text: str
    ) -> None:
        self.text = text
    def __call__(self, upd_btn: "UpdateButton") -> bool:
        return upd_btn.text == self.text

class startswith_text(InlineFilter):
    def __init__(
        self,
        text: str | tuple[str]
    ) -> None:
        self.text = text
    def __call__(self, upd_btn: "UpdateButton") -> bool:
        return upd_btn.text.startswith(self.text)

class endswith_text(InlineFilter):
    def __init__(
        self,
        text: str | tuple[str]
    ) -> None:
        self.text = text
    def __call__(self, upd_btn: "UpdateButton") -> bool:
        return upd_btn.text.endswith(self.text)

class time(InlineFilter):
    """filter by time / فیلتر با زمان"""
    def __init__(
        self,
        from_time: float = 0,
        end_time: float = float("inf")
    ):
        self.from_time = from_time
        self.end_time = end_time
    def __call__(self, upd_btn: 'UpdateButton'):
        if ti.time() > self.from_time and ti.time() < self.end_time:
            return True
        return False

class in_text(InlineFilter):
    """text in text message / وجود متن در متن آپدیت"""
    def __init__(self, text: str) -> None:
        self.text = text
    def __call__(self, upd_btn: 'UpdateButton') -> bool:
        if self.text in str(upd_btn.text):
            return True
        return False

class text_length(InlineFilter):
    """filter by text length / فیلتر بر اساس طول متن"""
    def __init__(self, min_len: int = 0, max_len: float = float('inf')):
        self.min_len = min_len
        self.max_len = max_len
    def __call__(self, upd_btn: 'UpdateButton') -> bool:
        return self.min_len <= len(upd_btn.text) <= self.max_len



class where(InlineFilter):
    """فیلتر با شرط دلخواه"""
    def __init__(self, func: Callable[['UpdateButton'], bool]):
        self.func = func
    def __call__(self, upd_btn: 'UpdateButton') -> bool:
        return self.func(upd_btn)

Where = where

class check(InlineFilter):
    """فیلتر با تابع شرط دلخواه (Sync یا Async)."""
    def __init__(self, func: Callable[..., bool | Awaitable[bool]]):
        self.func = func
        self._is_async = inspect.iscoroutinefunction(func)
    @property
    def type_filter(self):
        return "async" if self._is_async else "sync"
    def __call__(self, upd_btn: 'UpdateButton') -> bool:
        if self._is_async:
            raise RuntimeError("This filter is async. Use __acall__ instead.")
        return self.func(upd_btn) # type: ignore
    async def __acall__(self, upd_btn: 'UpdateButton') -> bool:
        if self._is_async:
            return await self.func(upd_btn) # type: ignore
        return self.func(upd_btn) # type: ignore


class db_exists(InlineAsyncFilter):
    """چک می‌کنه یه رکورد توی دیتابیس وجود داره یا نه"""
    def __init__(
        self,
        tabel_name: str,
        where_builder: Callable[['UpdateButton'], dict],
        db: DataBase | None = None,
        db_name: str | None = None,
        timeout: float = 10,
        journal_mode: Literal["DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF", "ROLLBACK"] = "WAL",
        synchronous: Literal["OFF", "NORMAL", "FULL", "EXTRA"] = "NORMAL",
    ) -> None:
        if db:
            self.db = db
        elif db_name:
            self.db = DataBase(db_name, timeout, journal_mode, synchronous)
        else:
            raise ValueError("db or db_name is required")
        self.tabel_name = tabel_name
        self.where_builder = where_builder
    
    async def __acall__(self, update: 'UpdateButton') -> bool:
        where_values = self.where_builder(update)
        return await self.db.exists(self.tabel_name, where_values)

class db_not_exists(InlineAsyncFilter):
    """چک می‌کنه یه رکورد توی دیتابیس وجود نداره"""
    def __init__(
        self,
        tabel_name: str,
        where_builder: Callable[['UpdateButton'], dict],
        db: DataBase | None = None,
        db_name: str | None = None,
        timeout: float = 10,
        journal_mode: Literal["DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF", "ROLLBACK"] = "WAL",
        synchronous: Literal["OFF", "NORMAL", "FULL", "EXTRA"] = "NORMAL",
    ) -> None:
        if db:
            self.db = db
        elif db_name:
            self.db = DataBase(db_name, timeout, journal_mode, synchronous)
        else:
            raise ValueError("db or db_name is required")
        self.tabel_name = tabel_name
        self.where_builder = where_builder
    
    async def __acall__(self, update: 'UpdateButton') -> bool:
        where_values = self.where_builder(update)
        return not await self.db.exists(self.tabel_name, where_values)

class db_count(InlineAsyncFilter):
    """چک می‌کنه تعداد رکوردها با شرط، بزرگتر از یه عدد باشه"""
    def __init__(
        self,
        tabel_name: str,
        where_builder: Callable[['UpdateButton'], dict],
        min_count: int = 1,
        db: DataBase | None = None,
        db_name: str | None = None,
        timeout: float = 10,
        journal_mode: Literal["DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF", "ROLLBACK"] = "WAL",
        synchronous: Literal["OFF", "NORMAL", "FULL", "EXTRA"] = "NORMAL",
    ) -> None:
        if db:
            self.db = db
        elif db_name:
            self.db = DataBase(db_name, timeout, journal_mode, synchronous)
        else:
            raise ValueError("db or db_name is required")
        self.tabel_name = tabel_name
        self.where_builder = where_builder
        self.min_count = min_count
    
    async def __acall__(self, update: 'UpdateButton') -> bool:
        where_values = self.where_builder(update)
        count = await self.db.len_rows(self.tabel_name, where_values)
        return count >= self.min_count

class db_value_equals(InlineAsyncFilter):
    """چک می‌کنه مقدار یه ستون برابر با یه مقدار باشه"""
    def __init__(
        self,
        tabel_name: str,
        column: str,
        where_builder: Callable[['UpdateButton'], dict],
        expected_value: Any,
        db: DataBase | None = None,
        db_name: str | None = None,
        timeout: float = 10,
        journal_mode: Literal["DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF", "ROLLBACK"] = "WAL",
        synchronous: Literal["OFF", "NORMAL", "FULL", "EXTRA"] = "NORMAL",
    ) -> None:
        if db:
            self.db = db
        elif db_name:
            self.db = DataBase(db_name, timeout, journal_mode, synchronous)
        else:
            raise ValueError("db or db_name is required")
        self.tabel_name = tabel_name
        self.column = column
        self.where_builder = where_builder
        self.expected_value = expected_value
    
    async def __acall__(self, update: 'UpdateButton') -> bool:
        where_values = self.where_builder(update)
        result = await self.db.find(self.tabel_name, self.column, where_values)
        return result == self.expected_value


class and_filter(InlineFilter):
    """filters {and} for if all filters is True : run code ... / فیلتر های ورودی {and} که اگر تمامی فیلتر های ورودی برابر True بود اجرا شود"""
    def __init__(self, *filters):
        self.filters = filters

    def __call__(self, update: 'UpdateButton') -> bool:
        return all(f(update) for f in self.filters)

class or_filter(InlineFilter):
    """filters {or} for if one filter is True : run code ... / فیلتر های ورودی {and} که اگر یک فیلتر ورودی برابر True بود اجرا شود"""
    def __init__(self, *filters):
        self.filters = filters

    def __call__(self, update: 'UpdateButton') -> bool:
        return any(f(update) for f in self.filters)

class not_filter(InlineFilter):
    """not True filter / درست نبودن فیلتر"""
    def __init__(self, filter):
        self.filter = filter
    def __call__(self, update: 'UpdateButton') -> bool:
        return not self.filter(update)
