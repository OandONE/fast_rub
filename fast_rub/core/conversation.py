from typing import Dict, Optional, List

from collections.abc import Callable
from ..types import Update
from .client import Client
from ..utils.filters import Filter

import asyncio

class Conversation:
    END = "__END__"
    
    def __init__(
        self,
        name: str = "default",
        timeout: float = 300.0
    ):
        self.name = name
        self._states: dict[str, Callable] = {}
        self._entry_handler: Callable | None = None
        self._entry_filters = None
        self._user_states: dict[str, str] = {}
        self._user_data: dict[str, dict] = {}
        self.timeout = timeout
        self._user_timers: dict[str, asyncio.Task] = {}
    
    def _set_timeout(self, chat_id: str):
        if chat_id in self._user_timers:
            self._user_timers[chat_id].cancel()
        
        async def _timeout():
            await asyncio.sleep(self.timeout)
            if chat_id in self._user_states:
                self._cleanup(chat_id)
        
        self._user_timers[chat_id] = asyncio.create_task(_timeout())
    
    def entry(
        self,
        commands: list | None = None,
        text: str | None = None,
        filters: Filter | None = None
    ):
        """دکوراتور برای نقطه ورود مکالمه."""
        def decorator(func):
            self._entry_handler = func
            self._entry_filters = {
                "commands": commands,
                "text": text,
                "filters": filters
            }
            return func
        return decorator
    
    def _is_entry(self, update: Update) -> bool:
        if not self._entry_filters:
            return False
        commands: list[str] | None = self._entry_filters.get("commands")
        text = self._entry_filters.get("text")
        filters = self._entry_filters.get("filters")
        if filters is not None:
            try:
                if not filters(update):
                    return False
            except Exception:
                return False
        
        if commands is not None and update.text:
            for cmd in commands:
                if update.text == cmd or update.text == f"/{cmd}":
                    return True
        
        if text is not None and update.text == text:
            return True
        
        if filters is not None:
            return True
        
        return False
    
    def state(
        self,
        state_name: str
    ):
        """دکوراتور برای یک حالت (مرحله) از مکالمه"""
        def decorator(func: Callable):
            self._states[state_name] = func
            return func
        return decorator
    
    async def handle(
        self,
        update: Update,
        client: Client
    ) -> bool:
        """پردازش یه آپدیت توی مکالمه.برمی‌گردونه True اگه مکالمه هنوز ادامه داره، False اگه تموم شده."""
        chat_id = update.chat_id
        if chat_id not in self._user_states:
            if self._is_entry(update):
                self._user_states[chat_id] = "__ENTRY__"
                self._user_data[chat_id] = {}
                self._set_timeout(chat_id)
            else:
                return False
        current_state = self._user_states.get(chat_id)
        if current_state == "__ENTRY__":
            if self._entry_handler:
                next_state = await self._entry_handler(update, self._user_data.get(chat_id, {}))
                if next_state == Conversation.END:
                    self._cleanup(chat_id)
                    return False
                self._user_states[chat_id] = next_state
                self._set_timeout(chat_id)
                return True
        if current_state in self._states:
            handler = self._states[current_state]
            next_state = await handler(update, self._user_data.get(chat_id, {}))
            if next_state == Conversation.END:
                self._cleanup(chat_id)
                return False
            self._user_states[chat_id] = next_state
            return True
        return False
    
    def _cleanup(self, chat_id: str):
        """پاکسازی state کاربر بعد از تموم شدن مکالمه"""
        self._user_states.pop(chat_id, None)
        self._user_data.pop(chat_id, None)


class ConversationManager:
    """مدیریت چندین مکالمه همزمان"""
    def __init__(self):
        self._conversations: dict[str, Conversation] = {}
    
    def add(
        self,
        conversation: Conversation
    ):
        self._conversations[conversation.name] = conversation
    
    def remove(
        self,
        name: str
    ):
        self._conversations.pop(name, None)
    
    async def handle(
        self,
        update: Update,
        client: Client
    ) -> bool:
        """همه مکالمات رو چک می‌کنه، اولویت با اولین مکالمه فعال"""
        chat_id = update.chat_id
        for conv in self._conversations.values():
            if chat_id in conv._user_states:
                return await conv.handle(update, client)
        for conv in self._conversations.values():
            if conv._is_entry(update):
                return await conv.handle(update, client)
        return False
