from .. import *
from ..core.async_sync import *
from .get_type import *
from .props import *
from .models.chat import Chat
from .metadata import metadata as metadata_prop
from .file import File
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union, Literal
import re

if TYPE_CHECKING:
    from .prop_update import msg_update
    from ..core import Client

class Update:
    def __init__(self, update_data: dict, client: "Client"):
        try:
            self._data = update_data["new_message"]
        except:
            self._data = update_data["updated_message"]
        self._client = client
        self.raw_data_ = update_data
    @property
    def text(self) -> Optional[str]:
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
    
    # File

    @property
    def file(self) -> Optional[dict]:
        """file / فایل"""
        return self._data['file'] if "file" in self._data else None
    @property
    def file_id(self) -> Optional[str]:
        """file id / آیدی فایل"""
        return self._data['file']['file_id'] if "file" in self._data else None
    @property
    def file_name(self) -> Optional[str]:
        """file name / اسم فایل"""
        return self._data['file']['file_name'] if "file" in self._data else None
    @property
    def size_file(self) -> Optional[int]:
        """size file / سایز فایل"""
        return self._data['file']['size'] if "file" in self._data else None
    @property
    def type_file(self) -> str:
        """get type file / گرفتن نوع فایل"""
        if self.file_name:
            return get_file_category(self.file_name)
        else:
            return "text"
    
    # Button

    @property
    def button(self) -> Optional[dict]:
        """data button clicked / اطلاعات دکمه کلیک شده"""
        return self._data['aux_data'] if "aux_data" in self._data else None
    @property
    def button_id(self) -> Optional[str]:
        """button id clicked button / آیدی دکمه کلیک شده"""
        return self.button['button_id'] if self.button else None
    
    # Reply

    @property
    def is_reply(self) -> bool:
        """is replyed / ریپلای شده"""
        return self.reply_to_message_id != None

    @property
    def reply_to_message_id(self) -> Optional[str]:
        """message id replyed / آیدی پیام ریپلای شده"""
        return self._data["reply_to_message_id"] if "reply_to_message_id" in self._data else None
    
    # Mata Data

    @property
    def metadata(self) -> Optional[dict]:
        """meta data / متا دیتا"""
        return self._data["metadata"] if "metadata" in self._data else None
    @property
    def meta_data_parts(self) -> Optional[metadata_prop]:
        """meta data parts list / لیست قسمت های متا دیتا"""
        return metadata_prop(self.metadata["meta_data_parts"]) if self.metadata else None
    
    # Forward

    @property
    def is_fowrard(self) -> bool:
        """forwarded / فوروارد شده"""
        return "forwarded_from" in self._data
    @property
    def forward_from(self) -> Optional[str]:
        """forward from / فوروارد از"""
        if self.is_fowrard:
            return self._data["forwarded_from"]["type_from"]
        return None
    @property
    def forward_message_id(self) -> Optional[str]:
        """message id forward / آیدی پیام فوروارد شده"""
        if self.is_fowrard:
            return self._data["forwarded_from"]["message_id"]
        return None
    @property
    def forward_from_sender_id(self) -> Optional[str]:
        """sender id forwarded / شناسه گوید فوروارد کننده"""
        if self.is_fowrard:
            return self._data["forwarded_from"]["from_sender_id"]
        return None
    
    # Contact

    @property
    def is_contact(self) -> bool:
        """contect / مخاطب"""
        return "contact_message" in self._data
    @property
    def contact_phone_number(self) -> Optional[str]:
        """phone number contact / شماره همراه مخاطب"""
        if self.is_contact:
            return self._data["contact_message"]["phone_number"]
        return None
    @property
    def contact_first_name(self) -> Optional[str]:
        """first name contact / اسم مخاطب"""
        if self.is_contact:
            return self._data["contact_message"]["first_name"]
        return None
    @property
    def contact_last_name(self) -> Optional[str]:
        """last name contact / نام خانوادگی مخاطب"""
        if self.is_contact:
            return self._data["contact_message"]["last_name"]
        return None

    # Stiker

    @property
    def is_sticker(self) -> bool:
        """sticker / استیکر"""
        return "sticker" in self._data
    @property
    def sticker_emoji_character(self) -> Optional[str]:
        """imoji sticker character / کاراکتر ایموجی استیکر"""
        if self.is_sticker:
            return self._data["sticker"]["emoji_character"]
        return None
    @property
    def sticker_sticker_id(self) -> Optional[str]:
        """sticker id / آیدی استیکر"""
        if self.is_sticker:
            return self._data["sticker"]["sticker_id"]
        return None
    @property
    def sticker_file(self) -> Union[File, dict]:
        """file sticker / فایل استیکر"""
        if self.is_sticker:
            return File(self._data["sticker"]["file"])
        return {}



    def regex(self, pattern: str, flags: int = 0) -> bool:
        """بررسی با الگو ریجکس / checking with regex"""
        self.pattern = re.compile(pattern, flags)
        if self.text is None:
            return False
        return bool(self.pattern.search(self.text))

    @auto_async
    async def get_chat_id_info(self) -> Chat:
        """get info the chat id / گرفتن درباره چت آیدی"""
        return await self._client.get_chat(self.chat_id)

    @auto_async
    async def reply(
        self,
        text: str,
        keypad_inline: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown"
    ) -> 'msg_update':
        """reply text / ریپلای متن"""
        return await self._client.send_text(
            text=text, chat_id=self.chat_id, reply_to_message_id=self.message_id, inline_keypad=keypad_inline, auto_delete=auto_delete, parse_mode=parse_mode,keypad=keypad,on_time_keyboard=on_time_keyboard,resize_keyboard=resize_keyboard
        )

    @auto_async
    async def reply_poll(
        self,
        question: str,
        options: list,
        type_poll: Literal["Regular", "Quiz"] = "Regular",
        is_anonymous: bool = True,
        correct_option_index: Optional[int] = None,
        allows_multiple_answers: bool = False,
        hint: Optional[str] = None,
        auto_delete: Optional[int] = None
    ) -> 'msg_update':
        """reply poll / ریپلای نظرسنجی"""
        return await self._client.send_poll(self.chat_id, question, options,type_poll=type_poll,is_anonymous=is_anonymous,correct_option_index=correct_option_index,allows_multiple_answers=allows_multiple_answers,hint=hint,auto_delete=auto_delete,reply_to_message_id=self.message_id)

    @auto_async
    async def reply_contact(
        self, first_name: str, phone_number: str, last_name: Union[str,str] = "",auto_delete: Optional[int] = None
    ) -> 'msg_update':
        """reply contact / ریپلای مخاطب"""
        return await self._client.send_contact(
            self.chat_id,
            first_name,
            last_name,
            phone_number,
            reply_to_message_id=self.message_id,
            auto_delete=auto_delete
        )

    @auto_async
    async def reply_location(self, latitude: str, longitude: str,auto_delete: Optional[int] = None) -> 'msg_update':
        """reply location / ریپلای موقعیت مکانی"""
        return await self._client.send_location(
            self.chat_id, latitude, longitude, reply_to_message_id=self.message_id,auto_delete=auto_delete
        )

    @auto_async
    async def reply_file(
        self,
        file: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif","Video"] = "File",
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True
    ) -> 'msg_update':
        """reply file / ریپلای فایل"""
        return await self._client.base_send_file(
            self.chat_id,
            file,
            name_file,
            text,
            self.message_id,
            type_file,
            disable_notification,
            auto_delete,
            parse_mode,
            meta_data,
            inline_keypad,
            keypad,
            resize_keyboard,
            on_time_keyboard,
            upload_by,
            show_progress
        )
    
    @auto_async
    async def reply_document(
        self,
        file: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif","Video"] = "File",
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True
    ) -> 'msg_update':
        """reply file / ریپلای فایل"""
        return await self._client.base_send_file(
            self.chat_id,
            file,
            name_file,
            text,
            self.message_id,
            type_file,
            disable_notification,
            auto_delete,
            parse_mode,
            meta_data,
            inline_keypad,
            keypad,
            resize_keyboard,
            on_time_keyboard,
            upload_by,
            show_progress
        )

    @auto_async
    async def reply_image(
        self,
        image: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True
    ) -> 'msg_update':
        """reply image / رپیلای تصویر"""
        return await self._client.send_image(
            self.chat_id,
            image,
            name_file,
            text,
            self.message_id,
            disable_notification,
            auto_delete,
            parse_mode,
            meta_data,
            inline_keypad,
            keypad,
            resize_keyboard,
            on_time_keyboard,
            upload_by,
            show_progress
        )

    @auto_async
    async def reply_voice(
        self,
        voice: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True
    ) -> 'msg_update':
        """reply voice / رپیلای ویس"""
        return await self._client.send_voice(
            self.chat_id,
            voice,
            name_file,
            text,
            self.message_id,
            disable_notification,
            auto_delete,
            parse_mode,
            meta_data,
            inline_keypad,
            keypad,
            resize_keyboard,
            on_time_keyboard,
            upload_by,
            show_progress
        )

    @auto_async
    async def reply_music(
        self,
        music: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True
    ) -> 'msg_update':
        """reply voice / رپیلای موزیک"""
        return await self._client.send_music(
            chat_id=self.chat_id,
            music=music,
            name_file=name_file,
            text=text,
            reply_to_message_id=self.message_id,
            disable_notification=disable_notification,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress
        )

    @auto_async
    async def reply_gif(
        self,
        gif: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True
    ) -> 'msg_update':
        """reply voice / رپیلای گیف"""
        return await self._client.send_gif(
            self.chat_id, gif,
            name_file,
            text,
            self.message_id,
            disable_notification,
            auto_delete,
            parse_mode,
            meta_data,
            inline_keypad,
            keypad,
            resize_keyboard,
            on_time_keyboard,
            upload_by,
            show_progress
        )

    @auto_async
    async def reply_video(
        self,
        video: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True
    ) -> 'msg_update':
        """reply voice / رپیلای ویدیو"""
        return await self._client.send_video(
            self.chat_id,
            video,
            name_file,
            text,
            self.message_id,
            disable_notification,
            auto_delete,
            parse_mode,
            meta_data,
            inline_keypad,
            keypad,
            resize_keyboard,
            on_time_keyboard,
            upload_by,
            show_progress
        )

    @auto_async
    async def forward(
            self,
            to_chat_id:str,
            auto_delete: Optional[int] = None
    ) -> 'msg_update':
        """forward / فوروارد"""
        return await self._client.forward_message(self.chat_id,self.message_id,to_chat_id,auto_delete=auto_delete)

    @auto_async
    async def download(
            self,
            path : Union[str,str] = "file"
    ) -> Optional[dict]:
        """download / دانلود"""
        if self.file_id:
            return await self._client.download_file(self.file_id,path)
        return None

    @auto_async
    async def delete(
            self
    ) -> props:
        """delete / حذف"""
        return await self._client.delete_message(self.chat_id,self.message_id)

    def __str__(self) -> str:
        if self.file_name:
            self._data['file']['type']=self.type_file
        self._data["sender_type"]=self.sender_type
        return json.dumps(self._data,indent=4,ensure_ascii=False)

    def __repr__(self) -> str:
        return self.__str__()


class UpdateButton:
    def __init__(self, data: dict, client: "Client"):
        self._data = data
        self._client = client

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

    @auto_async
    async def send_text(self,text:str,inline_keypad: Optional[list] = None,keypad: Optional[list] = None,resize_keyboard: Optional[bool] = True,on_time_keyboard: Optional[bool] = False,auto_delete: Optional[int] = None,reply_to_message_id: Optional[str] = None,parse_mode: Literal['Markdown', 'HTML'] = "Markdown"):
        return await self._client.send_text(
            text, self.chat_id,inline_keypad=inline_keypad,auto_delete=auto_delete,reply_to_message_id=reply_to_message_id,parse_mode=parse_mode,keypad=keypad,resize_keyboard=resize_keyboard,on_time_keyboard=on_time_keyboard
        )

    @auto_async
    async def send_pool(
        self,
        question: str,
        options : list,
        type_poll: Literal['Regular', 'Quiz'] = "Regular",
        is_anonymous: bool = True,
        correct_option_index: int | None = None,
        allows_multiple_answers: bool = False,
        hint: str | None = None,
        auto_delete: Optional[int] = None
    ):
        return await self._client.send_poll(
            chat_id=self.chat_id,question=question,options=options,type_poll=type_poll,is_anonymous=is_anonymous,correct_option_index=correct_option_index,allows_multiple_answers=allows_multiple_answers,hint=hint,disable_notification=False,auto_delete=auto_delete
        )

    @auto_async
    async def send_contact(
        self,
        first_name: str,
        last_name: str,
        phone_number: str,
        auto_delete: Optional[int] = None,
        reply_to_message_id: Optional[str] = None
    ):
        return await self._client.send_contact(
            self.chat_id,first_name,last_name,phone_number,auto_delete=auto_delete,reply_to_message_id=reply_to_message_id
        )

    @auto_async
    async def send_location(
        self,
        latitude: str,
        longitude: str,
        auto_delete: Optional[int] = None,
        reply_to_message_id: Optional[str] = None
    ):
        return await self._client.send_location(
            self.chat_id,latitude,longitude,auto_delete=auto_delete,reply_to_message_id=reply_to_message_id
        )

    @auto_async
    async def send_file(
        self,
        file: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        type_file: Literal['File', 'Image', 'Voice', 'Music', 'Gif', 'Video'] = "File",
        auto_delete: Optional[int] = None,
        reply_to_message_id: Optional[str] = None
    ):
        return await self._client.base_send_file(
            self.chat_id,file,name_file,text,type_file=type_file,auto_delete=auto_delete,reply_to_message_id=reply_to_message_id
        )

    @auto_async
    async def send_image(
        self,
        image: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        auto_delete: Optional[int] = None,
        reply_to_message_id: Optional[str] = None
    ):
        return await self._client.send_image(
            self.chat_id,
            image,
            name_file,
            text,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id
        )

    @auto_async
    async def send_video(
        self,
        video: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        auto_delete: Optional[int] = None,
        reply_to_message_id: Optional[str] = None
    ):
        return await self._client.send_video(
            self.chat_id,
            video,
            name_file,
            text,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id
        )

    @auto_async
    async def send_voice(
        self,
        voice: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        auto_delete: Optional[int] = None,
        reply_to_message_id: Optional[str] = None
    ):
        return await self._client.send_voice(
            self.chat_id,
            voice,
            name_file,
            text,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id
        )

    @auto_async
    async def send_music(
        self,
        music: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        auto_delete: Optional[int] = None,
        reply_to_message_id: Optional[str] = None
    ):
        return await self._client.send_music(
            self.chat_id,
            music,
            name_file,
            text,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id
        )

    @auto_async
    async def send_gif(
        self,
        gif: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        auto_delete: Optional[int] = None,
        reply_to_message_id: Optional[str] = None
    ):
        return await self._client.send_gif(
            self.chat_id,
            gif,
            name_file,
            text,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id
        )

    def __str__(self) -> str:
        return json.dumps(self._data)

