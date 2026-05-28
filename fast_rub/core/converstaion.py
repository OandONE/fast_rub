from typing import Dict, Callable, Optional, List
from ..types import Update
from .client import Client

class Conversation:
    END = "__END__"
    
    def __init__(
        self,
        name: str = "default"
    ):
        self.name = name
        self._states: Dict[str, Callable] = {}
        self._entry_handler: Optional[Callable] = None
        self._entry_filters = None
        self._user_states: Dict[str, str] = {}
        self._user_data: Dict[str, dict] = {}
    
    def entry(
        self,
        commands: Optional[list[str]] = None,
        text: Optional[str] = None
    ):
        """دکوراتور برای نقطه ورود مکالمه"""
        def decorator(func: Callable):
            self._entry_handler = func
            self._entry_filters = {"commands": commands, "text": text}
            return func
        return decorator
    
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
        """
        پردازش یه آپدیت توی مکالمه.
        برمی‌گردونه True اگه مکالمه هنوز ادامه داره، False اگه تموم شده.
        """
        chat_id = update.chat_id
        if chat_id not in self._user_states:
            if self._is_entry(update):
                self._user_states[chat_id] = "__ENTRY__"
                self._user_data[chat_id] = {}
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
    
    def _is_entry(self, update: Update) -> bool:
        if not self._entry_filters:
            return False
        commands: Optional[List[str]] = self._entry_filters.get("commands")
        text: Optional[str] = self._entry_filters.get("text")
        if commands is not None and update.text is not None:
            for cmd in commands:
                if update.text == cmd or update.text == f"/{cmd}":
                    return True
        if text is not None and update.text == text:
            return True
        return False
    
    def _cleanup(self, chat_id: str):
        """پاکسازی state کاربر بعد از تموم شدن مکالمه"""
        self._user_states.pop(chat_id, None)
        self._user_data.pop(chat_id, None)


class ConversationManager:
    """مدیریت چندین مکالمه همزمان"""
    def __init__(self):
        self._conversations: Dict[str, Conversation] = {}
    
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
