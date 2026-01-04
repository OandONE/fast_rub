from typing import TYPE_CHECKING, Literal, Optional
if TYPE_CHECKING:
    from ..core import Client
from . import Update
import json
from .props import props

class msg_update:
    def __init__(self, update_data: dict, client: "Client") -> None:
        self.update_data = update_data
        self.client = client
    
    @property
    def message_id(self) -> str:
        "message id / آیدی پیام"
        return self.update_data["message_id"]
    
    @property
    def chat_id(self) -> str:
        "chat id / چت آیدی"
        return self.update_data["chat_id"]
    
    async def edit_text(self, new_text: str,inline_keypad: Optional[list] = None, parse_mode: Literal['Markdown', 'HTML'] | None = "Markdown") -> "msg_update":
        "edit text message / ویرایش متن پیام"
        return await self.client.edit_message_text(
            self.chat_id,
            self.message_id,
            new_text,
            inline_keypad,
            parse_mode
        )
    
    async def get_message(self) -> Optional[Update]:
        """getting message info / گرفتن اطلاعات پیام"""
        return await self.client.get_message(self.chat_id,self.message_id)
    
    async def delete_message(self) -> props:
        """حذف پیام / delete message"""
        return await self.client.delete_message(self.chat_id, self.message_id)

    def __str__(self) -> str:
        return json.dumps(self.update_data,indent=4,ensure_ascii=False)

    def __repr__(self) -> str:
        return self.__str__()
    
    def _list_to_props(self, lst):
        new_list = []
        for el in lst:
            if isinstance(el, dict):
                new_list.append(props(el))
            elif isinstance(el, list):
                new_list.append(self._list_to_props(el))
            else:
                new_list.append(el)
        return new_list

    def __getattr__(self, name):
        try:
            value = self.update_data[name]
        except KeyError:
            raise AttributeError(f"'msg_update' object has no attribute '{name}'")

        if isinstance(value, dict):
            return props(value)
        if isinstance(value, list):
            return self._list_to_props(value)
        return value
    
    def to_dict(self) -> dict:
        return self.update_data