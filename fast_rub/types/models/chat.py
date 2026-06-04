from typing import Optional
from .base_model import _BaseModels

class Chat(_BaseModels):
    @property
    def first_name(self) -> str | None:
        return self.data.get("first_name")
    @property
    def title(self) -> str | None:
        return self.data.get("title")
    @property
    def user_id(self) -> str | None:
        return self.data.get("user_id")
    @property
    def chat_id(self) -> str:
        return self.data["chat_id"]
    @property
    def last_name(self) -> str | None:
        return self.data.get("last_name")
    @property
    def username(self) -> str | None:
        return self.data.get("username")
