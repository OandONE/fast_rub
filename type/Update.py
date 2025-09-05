from ..Client import *
from ..async_sync import *
from .get_type import *

class Update:
    def __init__(self, update_data: dict, client: "Client"):
        try:
            self._data = update_data["new_message"]
        except:
            self._data = update_data["updated_message"]
        self._client = client
        self.raw_data_=update_data
        self.message = update_data.get("new_message", {})
    @property
    def text(self) -> str | None:
        """text message / متن پیام"""
        return self._data['text'] if "text" in self._data else None
    @property
    def message_id(self) -> str:
        """message id / آیدی پیام"""
        return self._data['message_id']
    @property
    def chat_id(self) -> str:
        """chat id message / چت آیدی پیام"""
        return self.raw_data_['chat_id']
    @property
    def time(self) -> int:
        """time sended message / زمان ارسال شده پیام"""
        return int(self._data['time'])
    @property
    def sender_type(self) -> Literal["User","Group","Channel"]:
        """sender type / نوع ارسال کننده"""
        if self.chat_id.startswith("b"):
            return "User"
        elif self.chat_id.startswith("g"):
            return "Group"
        elif self.chat_id.startswith("c"):
            return "Channel"
        else:
            raise ValueError("chat id is not found")
    @property
    def sender_id(self) -> str:
        """sender id message / شناسه گوید کاربر ارسال کننده"""
        return self._data['sender_id']
    @property
    def is_edited(self):
        return self._data['is_edited']
    @property
    def file(self) -> dict | None:
        """file / فایل"""
        return self._data['file'] if "file" in self._data else None
    @property
    def file_id(self) -> str | None:
        """file id / آیدی فایل"""
        return self._data['file']['file_id'] if "file" in self._data else None
    @property
    def file_name(self) -> str | None:
        """file name / اسم فایل"""
        return self._data['file']['file_name'] if "file" in self._data else None
    @property
    def size_file(self) -> int | None:
        """size file / سایز فایل"""
        return self._data['file']['size'] if "file" in self._data else None
    @property
    def type_file(self) -> str:
        """get type file / گرفتن نوع فایل"""
        if self.file_name:
            return get_file_category(self.file_name)
        else:
            return "text"
    @property
    def button(self) -> dict | None:
        """data button clicked / اطلاعات دکمه کلیک شده"""
        return self._data['aux_data'] if "aux_data" in self._data else None
    @property
    def button_id(self) -> str | None:
        """button id clicked button / آیدی دکمه کلیک شده"""
        return self.button['button_id'] if self.button else None


    @auto_async
    async def get_chat_id_info(self) -> dict:
        """get info the chat id / گرفتن درباره چت آیدی"""
        return await self._client.get_chat(self.chat_id)

    @auto_async
    async def reply(self, text: str,keypad = None) -> dict:
        """reply text / ریپلای متن"""
        return await self._client.send_text(
            text, self.chat_id, reply_to_message_id=self.message_id,inline_keypad=keypad
        )

    @auto_async
    async def reply_poll(self, question: str, options: list) -> dict:
        """reply poll / ریپلای نظرسنجی"""
        return await self._client.send_poll(self.chat_id, question, options)

    @auto_async
    async def reply_contact(
        self, first_name: str, phone_number: str, last_name: Union[str,str] = ""
    ) -> dict:
        """reply contact / ریپلای مخاطب"""
        return await self._client.send_contact(
            self.chat_id,
            first_name,
            last_name,
            phone_number,
            reply_to_message_id=self.message_id,
        )

    @auto_async
    async def reply_location(self, latitude: str, longitude: str) -> dict:
        """reply location / ریپلای موقعیت مکانی"""
        return await self._client.send_location(
            self.chat_id, latitude, longitude, reply_to_message_id=self.message_id
        )

    @auto_async
    async def reply_file(
        self,
        file: str | Path | bytes,
        name_file: str,
        text: Optional[str] = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif","Video"] = "File",
        disable_notification: Optional[bool] = False,
    ) -> dict:
        """reply file / ریپلای فایل"""
        return await self._client.send_file(
            self.chat_id,
            file,
            name_file,
            text,
            self.message_id,
            type_file,
            disable_notification,
        )

    @auto_async
    async def reply_image(
        self,
        image: str | Path | bytes,
        name_file: str,
        text: Optional[str] = None,
        disable_notification: Optional[bool] = False,
    ) -> dict:
        """reply image / رپیلای تصویر"""
        return await self._client.send_image(
            self.chat_id, image, name_file, text, self.message_id, disable_notification
        )

    @auto_async
    async def reply_voice(
        self,
        voice: str | Path | bytes,
        name_file: str,
        text: Optional[str] = None,
        disable_notification: Optional[bool] = False,
    ) -> dict:
        """reply voice / رپیلای ویس"""
        return await self._client.send_voice(
            self.chat_id, voice, name_file, text, self.message_id, disable_notification
        )

    @auto_async
    async def reply_music(
        self,
        music: str | Path | bytes,
        name_file: str,
        text: Optional[str] = None,
        disable_notification: Optional[bool] = False,
    ) -> dict:
        """reply voice / رپیلای موزیک"""
        return await self._client.send_music(
            self.chat_id, music, name_file, text, self.message_id, disable_notification
        )

    @auto_async
    async def reply_gif(
        self,
        gif: str | Path | bytes,
        name_file: str,
        text: Optional[str] = None,
        disable_notification: Optional[bool] = False,
    ) -> dict:
        """reply voice / رپیلای گیف"""
        return await self._client.send_gif(
            self.chat_id, gif, name_file, text, self.message_id, disable_notification
        )

    @auto_async
    async def reply_video(
        self,
        video: str | Path | bytes,
        name_file: str,
        text: Optional[str] = None,
        disable_notification: Optional[bool] = False,
    ) -> dict:
        """reply voice / رپیلای ویدیو"""
        return await self._client.send_gif(
            self.chat_id, video, name_file, text, self.message_id, disable_notification
        )

    @auto_async
    async def forward(
            self,
            to_chat_id:str
    ) -> dict:
        """forward / فوروارد"""
        return await self._client.forward_message(self.chat_id,self.message_id,to_chat_id)

    @auto_async
    async def download(
            self,
            path : Union[str,str] = "file"
    ) -> dict | None:
        """download / دانلود"""
        if self.file_id:
            return await self._client.download_file(self.file_id,path)
        return None

    @auto_async
    async def delete(
            self
    ) -> dict:
        """delete / حذف"""
        return await self._client.delete_message(self.chat_id,self.message_id)

    def __str__(self) -> str:
        if self.file_name:
            self._data['file']['type']=self.type_file
        self._data["sender_type"]=self.sender_type
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
