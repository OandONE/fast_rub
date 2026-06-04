from typing import Optional
from .base_model import _BaseModels

class Bot(_BaseModels):
    @property
    def bot_id(self) -> str:
        return self.data["bot_id"]
    @property
    def bot_title(self) -> str:
        return self.data["bot_title"]
    @property
    def description(self) -> str:
        return self.data["description"]
    @property
    def username(self) -> str:
        return self.data["username"]
    @property
    def start_message(self) -> str:
        return self.data["start_message"]
    @property
    def share_url(self) -> str:
        return self.data["share_url"]
    @property
    def avatar(self) -> dict | None:
        return self.data["avatar"]
    @property
    def avatar_file_id(self) -> str | None:
        avatar = self.avatar
        if avatar:
            file_id = avatar["file_id"]
            return file_id
    @property
    def avatar_file_name(self) -> str | None:
        avatar = self.avatar
        if avatar:
            file_name = avatar["file_name"]
            return file_name
    @property
    def avatar_size(self) -> int | None:
        avatar = self.avatar
        if avatar:
            size = avatar["size"]
            return size
