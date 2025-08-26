from ..Client import *
class Update:
    def __init__(self, update_data: dict, client: "Client"):
        self._data = update_data
        self._client = client
        self.message = update_data.get("new_message", {})
    @property
    def text(self) -> str:
        return self._data['new_message']['text']
    @property
    def message_id(self) -> int:
        return self._data['new_message']['message_id']
    @property
    def chat_id(self) -> str:
        return self._data['chat_id']
    @property
    def time(self) -> int:
        return int(self._data['new_message']['time'])
    @property
    def sender_type(self) -> str:
        return self._data['new_message']['sender_type']
    @property
    def sender_id(self) -> str:
        return self._data['new_message']['sender_id']

    async def reply(self, text: str) -> dict:
        """reply text / ریپلای متن"""
        return await self._client.send_text(
            text, self.chat_id, reply_to_message_id=self.message_id
        )

    async def reply_poll(self, question: str, options: list) -> dict:
        """reply poll / ریپلای نظرسنجی"""
        return await self._client.send_poll(self.chat_id, question, options)

    async def reply_contact(
        self, first_name: str, phone_number: str, last_name: str = None
    ) -> dict:
        """reply contact / ریپلای مخاطب"""
        return await self._client.send_contact(
            self.chat_id,
            first_name,
            last_name,
            phone_number,
            reply_to_message_id=self.message_id,
        )

    async def reply_location(self, latitude: str, longitude: str) -> dict:
        """reply location / ریپلای موقعیت مکانی"""
        return await self._client.send_location(
            self.chat_id, latitude, longitude, reply_to_message_id=self.message_id
        )

    async def reply_file(
        self,
        chat_id: str,
        file: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif"] = "File",
        disable_notification: bool = False,
    ) -> dict:
        """reply file / ریپلای فایل"""
        return await self._client.send_file(
            chat_id,
            file,
            name_file,
            text,
            reply_to_message_id,
            type_file,
            disable_notification,
        )

    async def reply_image(
        self,
        chat_id: str,
        image: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        disable_notification: bool = False,
    ) -> dict:
        """reply image / رپیلای تصویر"""
        return await self._client.send_image(
            chat_id, image, name_file, text, reply_to_message_id, disable_notification
        )

    async def reply_voice(
        self,
        chat_id: str,
        voice: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        disable_notification: bool = False,
    ) -> dict:
        """reply voice / رپیلای ویس"""
        return await self._client.send_voice(
            chat_id, voice, name_file, text, reply_to_message_id, disable_notification
        )

    async def reply_music(
        self,
        chat_id: str,
        music: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        disable_notification: bool = False,
    ) -> dict:
        """reply voice / رپیلای موزیک"""
        return await self._client.send_music(
            chat_id, music, name_file, text, reply_to_message_id, disable_notification
        )

    async def reply_gif(
        self,
        chat_id: str,
        gif: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        disable_notification: bool = False,
    ) -> dict:
        """reply voice / رپیلای گیف"""
        return await self._client.send_gif(
            chat_id, gif, name_file, text, reply_to_message_id, disable_notification
        )

    def __str__(self) -> str:
        return str(self._data)

    def __repr__(self) -> str:
        return self.__str__()


class UpdateButton:
    def __init__(self, data: dict):
        self._data = data

    @property
    def raw_data(self) -> dict:
        return self._data

    @property
    def button_id(self) -> str:
        """button id clicked / آیدی دکمه کلیک شده"""
        return self._data["inline_message"]["aux_data"]["button_id"]

    @property
    def chat_id(self) -> str:
        """chat id clicked / چت آیدی کلیک شده"""
        return self._data["inline_message"]["chat_id"]

    @property
    def message_id(self) -> str:
        """message id for message clicked glass button / آیدی پیام کلیک شده روی دکمه شیشه ای"""
        return self._data["inline_message"]["message_id"]

    @property
    def sender_id(self) -> str:
        """guid for clicked button glass / شناسه گوید کاربر کلیک کرده روی دکمه شیشه ای"""
        return self._data["inline_message"]["sender_id"]

    @property
    def text(self) -> str:
        """text for button clicked / متن دکمه شیشه ای که روی آن کلیک شده"""
        return self._data["inline_message"]["text"]

    def __str__(self):
        return str(self._data)