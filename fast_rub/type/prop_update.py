from ..Client import Client
from typing import Literal, Optional
from .Update import Update
import json
from .props import props

class msg_update:
    def __init__(self, update_data: dict, client: "Client") -> None:
        self.update_data = update_data["data"]
        self.client = client
    
    @property
    def message_id(self) -> str:
        "message id / آیدی پیام"
        return self.update_data["message_id"]
    
    @property
    def chat_id(self) -> str:
        "chat id / چت آیدی"
        return self.update_data["chat_id"]

    async def edit_text(self, new_text: str, parse_mode: Literal['Markdown', 'HTML'] | None = "Markdown") -> "msg_update":
        "edit text message / ویرایش متن پیام"
        return await self.client.edit_message_text(
            self.chat_id,
            self.message_id,
            new_text,
            parse_mode
        )
    
    async def get_message(self) -> Optional[Update]:
        """getting message info / گرفتن اطلاعات پیام"""
        return await self.client.get_message(self.chat_id,self.message_id)
    
    async def delete_message(self) -> props:
        """حذف پیام / delete message
        
        Docstring for delete_message
        
        :return: Description
        :rtype: props
        """
        return await self.client.delete_message(self.chat_id, self.message_id)

    def __str__(self) -> str:
        return json.dumps(self.update_data,indent=4,ensure_ascii=False)

    def __repr__(self) -> str:
        return self.__str__()