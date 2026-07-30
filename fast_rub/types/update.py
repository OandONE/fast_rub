import asyncio
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Union

from ..button import KeyPad
from ..core.async_sync import *
from ..utils import Utils

from .get_type import *
from .metadata import MetaData as MetaDataProp
from .models import Chat
from .props import *

if TYPE_CHECKING:
    from ..core import Client
    from .prop_update import msg_update


class BaseModels:
    def __init__(
        self,
        raw_data: dict
    ):
        self.raw_data = raw_data
    def to_dict(
        self
    ) -> dict:
        """convert Update to Dict / تبدیل آپدیت به دیکشنری"""
        if isinstance(self.raw_data, props):
            self.raw_data = dict(self.raw_data.to_dict())
        return self.raw_data
    
    def get(
        self,
        key: str,
        defult = None
    ):
        return self.raw_data.get(key, defult)
    
    def __setitem__(
        self,
        key,
        value
    ):
        self.raw_data[key] = value
    
    def __getitem__(
        self,
        key
    ):
        result = self.get(key)
        if not result:
            raise KeyError(f"The {key} has not in datas .")
        return result

    def __str__(self) -> str:
        return json.dumps(
            self.to_dict(),
            indent=4,
            ensure_ascii=False
        )

    def __repr__(self) -> str:
        return self.__str__()

class FileSticker(BaseModels):
    @property
    def file_id(self) -> str:
        return self.raw_data["file_id"]
    @property
    def file_name(self) -> str:
        return self.raw_data["file_name"]
    @property
    def size(self) -> int:
        return self.raw_data["size"]

class Sticker(BaseModels):
    @property
    def is_sticker(self) -> bool:
        """sticker / استیکر"""
        return "sticker" in self.raw_data
    @property
    def emoji_character(self) -> str | None:
        """imoji sticker character / کاراکتر ایموجی استیکر"""
        if self.is_sticker:
            return self.raw_data["sticker"]["emoji_character"]
        return None
    @property
    def sticker_id(self) -> str | None:
        """sticker id / آیدی استیکر"""
        if self.is_sticker:
            return self.raw_data["sticker"]["sticker_id"]
        return None
    
    id = sticker_id

    @property
    def file(self) -> FileSticker | dict:
        """file sticker / فایل استیکر"""
        if self.is_sticker:
            return FileSticker(self.raw_data["sticker"]["file"])
        return {}

class Contact(BaseModels):
    @property
    def is_contact(self) -> bool:
        """contect / مخاطب"""
        return "contact_message" in self.raw_data
    @property
    def phone_number(self) -> str | None:
        """phone number contact / شماره همراه مخاطب"""
        if self.is_contact:
            return self.raw_data["contact_message"]["phone_number"]
        return None
    @property
    def first_name(self) -> str | None:
        """first name contact / اسم مخاطب"""
        if self.is_contact:
            return self.raw_data["contact_message"]["first_name"]
        return None
    @property
    def last_name(self) -> str | None:
        """last name contact / نام خانوادگی مخاطب"""
        if self.is_contact:
            return self.raw_data["contact_message"]["last_name"]
        return None

class MetaData(BaseModels):
    def __init__(
        self,
        raw_data: dict
    ):
        self.raw_data = raw_data
    @property
    def metadata(self) -> dict | None:
        """meta data / متا دیتا"""
        return self.raw_data.get("metadata")
    @property
    def meta_data_parts(self) -> MetaDataProp | None:
        """meta data parts list / لیست قسمت های متا دیتا"""
        return MetaDataProp(self.metadata["meta_data_parts"]) if self.metadata else None

    metadata_parts = meta_data_parts

class Forward(BaseModels):
    def __init__(
        self,
        raw_data: dict
    ):
        self.raw_data = raw_data
    @property
    def is_forward(self) -> bool:
        """is forwarded / پیام فوروارد شده"""
        return "forwarded_from" in self.raw_data
    @property
    def forward_from(self) -> str | None:
        """forward from / فوروارد از"""
        if self.is_forward:
            return self.raw_data["forwarded_from"]
        return None
    @property
    def forward_from_type_from(self) -> str | None:
        """forward from / فوروارد از"""
        if self.is_forward:
            return self.raw_data["forwarded_from"]["type_from"]
        return None
    @property
    def forward_message_id(self) -> str | None:
        """message id forward / آیدی پیام فوروارد شده"""
        if self.is_forward:
            return self.raw_data["forwarded_from"]["message_id"]
        return None
    @property
    def forward_from_sender_id(self) -> str | None:
        """sender id forwarded / شناسه گوید فوروارد کننده"""
        if self.is_forward:
            return self.raw_data["forwarded_from"]["from_sender_id"]
        return None

class Button(BaseModels):
    def __init__(
        self,
        raw_data: dict
    ):
        self.raw_data = raw_data
    
    @property
    def button(self) -> dict | None:
        """data button clicked / اطلاعات دکمه کلیک شده"""
        return self.raw_data.get('aux_data')
    
    aux_data = button

    @property
    def button_id(self) -> str | None:
        """button id clicked button / آیدی دکمه کلیک شده"""
        return self.button.get('button_id') if self.button else None

class File(BaseModels):
    def __init__(
        self,
        raw_data: dict
    ):
        self.raw_data = raw_data
    @property
    def file(self) -> dict | None:
        """file / فایل"""
        return self.raw_data.get('file')
    @property
    def file_id(self) -> str | None:
        """file id / آیدی فایل"""
        return self.file.get('file_id') if self.file else None
    
    id = file_id

    @property
    def file_name(self) -> str | None:
        """file name / اسم فایل"""
        return self.file.get('file_name') if self.file else None
    @property
    def size_file(self) -> int | None:
        """size file / سایز فایل"""
        return self.file.get('size') if self.file else None
    @property
    def type_file(self) -> str | None:
        """get type file / گرفتن نوع فایل"""
        return get_file_category(self.file_name)

class NewMessage(BaseModels):
    @property
    def text(self) -> str | None:
        """text message / متن پیام"""
        return self.raw_data.get("text")
    @property
    def message_id(self) -> str:
        """message id / آیدی پیام"""
        return self.raw_data['message_id']
    @property
    def time(self) -> int:
        """time sended message / زمان ارسال شده پیام"""
        return int(self.raw_data['time'])
    @property
    def sender_id(self) -> str:
        """sender id message / سندر آیدی کاربر ارسال کننده"""
        return self.raw_data['sender_id']
    @property
    def is_edited(self):
        return self.raw_data['is_edited']
    @property
    def reply_to_message_id(self) -> str | None:
        """message id replyed / آیدی پیام ریپلای شده"""
        return self.raw_data.get("reply_to_message_id")
    @property
    def file(self) -> File:
        return File(self.raw_data)
    @property
    def aux_data(self) -> Button:
        return Button(self.raw_data)
    
    button = aux_data

    @property
    def is_forward(self) -> bool:
        """forwarded / فوروارد شده"""
        return "forwarded_from" in self.raw_data
    @property
    def forward(self) -> Forward:
        return Forward(self.raw_data)
    @property
    def metadata(self) -> MetaData:
        return MetaData(self.raw_data)
    @property
    def contact(self) -> Contact:
        return Contact(self.raw_data)
    @property
    def is_contact(self) -> bool:
        """contect / مخاطب"""
        return "contact_message" in self.raw_data
    @property
    def sticker(self) -> Sticker:
        return Sticker(self.raw_data)
    @property
    def is_sticker(self) -> bool:
        """sticker / استیکر"""
        return "sticker" in self.raw_data

class Update(BaseModels):
    def __init__(
        self,
        update_data: dict,
        client: "Client",
    ):
        msg_data = update_data.get("new_message") or update_data.get("updated_message") or {}
        self.new_message = NewMessage(msg_data)
        self._client = client
        self.raw_data = update_data
    @property
    def text(self) -> str | None:
        Utils.deprecated_property("text", "new_message.text")
        return self.new_message.text
    @property
    def message_id(self) -> str:
        Utils.deprecated_property("message_id", "new_message.message_id")
        return self.new_message.message_id
    @property
    def chat_id(self) -> str:
        """chat id message / چت آیدی پیام"""
        return self.raw_data['chat_id']
    @property
    def time(self) -> int:
        """time sended message / زمان ارسال شده پیام"""
        Utils.deprecated_property("time", "new_message.time")
        return self.new_message.time
    @property
    def sender_type(self) -> Literal["User","Group","Channel"]:
        """sender type / نوع ارسال کننده"""
        return Utils.get_chat_id_type(self.chat_id)
    @property
    def sender_id(self) -> str:
        Utils.deprecated_property("sender_id", "new_message.sender_id")
        return self.new_message.sender_id
    @property
    def is_edited(self):
        Utils.deprecated_property("is_edited", "new_message.is_edited")
        return self.new_message.is_edited
    
    # File

    @property
    def file(self) -> dict | None:
        Utils.deprecated_property("file", "new_message.file")
        return self.new_message.file.file
    @property
    def file_id(self) -> str | None:
        Utils.deprecated_property("file", "new_message.file.file_id")
        return self.new_message.file.file_id
    @property
    def file_name(self) -> str | None:
        Utils.deprecated_property("file", "new_message.file.file_name")
        return self.new_message.file.file_name
    @property
    def size_file(self) -> int | None:
        Utils.deprecated_property("file", "new_message.file.size_file")
        return self.new_message.file.size_file
    @property
    def type_file(self) -> str | None:
        Utils.deprecated_property("file", "new_message.file.type_file")
        return self.new_message.file.type_file
    
    # Button

    @property
    def button(self) -> dict | None:
        Utils.deprecated_property("button_id", "new_message.aux_data.button")
        return self.new_message.aux_data.button
    @property
    def button_id(self) -> str | None:
        Utils.deprecated_property("button_id", "new_message.aux_data.button_id")
        return self.new_message.aux_data.button_id
    
    # Reply

    @property
    def is_reply(self) -> bool:
        """is replyed / ریپلای شده"""
        return self.new_message.reply_to_message_id is not None

    @property
    def reply_to_message_id(self) -> str | None:
        Utils.deprecated_property("reply_to_message_id", "new_message.reply_to_message_id")
        return self.new_message.reply_to_message_id
    
    # Mata Data

    @property
    def metadata(self) -> dict | None:
        Utils.deprecated_property("metadata", "new_message.metadata.metadata")
        return self.new_message.metadata.metadata
    @property
    def meta_data_parts(self) -> MetaDataProp | None:
        Utils.deprecated_property("metadata", "new_message.metadata.meta_data_parts")
        return self.new_message.metadata.meta_data_parts
    
    # Forward

    @property
    def is_forward(self) -> bool:
        Utils.deprecated_property("is_forward", "new_message.is_forward")
        return self.new_message.is_forward
    @property
    def forward_from(self) -> str | None:
        Utils.deprecated_property("forward_from", "new_message.forward.forward_from")
        if self.is_forward:
            return self.new_message.forward.forward_from
        return None
    @property
    def forward_message_id(self) -> str | None:
        Utils.deprecated_property("forward_message_id", "new_message.forward.forward_message_id")
        if self.is_forward:
            return self.new_message.forward.forward_message_id
        return None
    @property
    def forward_from_sender_id(self) -> str | None:
        Utils.deprecated_property("forward_from_sender_id", "new_message.forward.forward_from_sender_id")
        if self.is_forward:
            return self.new_message.forward.forward_from_sender_id
        return None

    # Contact

    @property
    def is_contact(self) -> bool:
        Utils.deprecated_property("is_contact", "new_message.is_contact")
        return self.new_message.is_contact
    @property
    def contact_phone_number(self) -> str | None:
        Utils.deprecated_property("contact_phone_number", "new_message.contact.phone_number")
        return self.new_message.contact.phone_number
    @property
    def contact_first_name(self) -> str | None:
        Utils.deprecated_property("contact_first_name", "new_message.contact.first_name")
        return self.new_message.contact.first_name
    @property
    def contact_last_name(self) -> str | None:
        Utils.deprecated_property("contact_last_name", "new_message.contact.last_name")
        return self.new_message.contact.last_name

    # Stiker

    @property
    def is_sticker(self) -> bool:
        Utils.deprecated_property("is_sticker", "new_message.is_sticker")
        return self.new_message.is_sticker
    @property
    def sticker_emoji_character(self) -> str | None:
        Utils.deprecated_property("sticker_emoji_character", "new_message.sticker.emoji_character")
        return self.new_message.sticker.emoji_character
    @property
    def sticker_sticker_id(self) -> str | None:
        Utils.deprecated_property("is_sticker", "new_message.sticker.sticker_id")
        return self.new_message.sticker.sticker_id
    @property
    def sticker_file(self) -> FileSticker | dict:
        Utils.deprecated_property("is_sticker", "new_message.sticker.file")
        return self.new_message.sticker.file

    # remove update
    @property
    def removed_message_id(self) -> str | None:
        """message id deleted / آیدی پیام پاک شده"""
        return self.raw_data.get("removed_message_id")
    
    @property
    def update_time(self) -> int | None:
        """update time message deleted / زمان پاک شدن پیام"""
        up_time = self.raw_data.get("update_time")
        if up_time:
            return int(up_time)
        return None



    def regex(
        self,
        pattern: str,
        flags: int = 0,
        text: str | None = None
    ) -> bool:
        """بررسی با الگو ریجکس / checking with regex"""
        if self.new_message.text is None:
            return False
        self.pattern = re.compile(pattern, flags)
        return bool(
            self.pattern.search(
                Utils.prefer_first(text, self.new_message.text)
            )
        )

    
    async def get_chat_id_info(
        self,
        chat_id: str | None = None
    ) -> Chat:
        """get info the chat id / گرفتن درباره چت آیدی"""
        return await self._client.get_chat(
            chat_id=Utils.prefer_first(chat_id, self.chat_id)
        )

    
    async def reply(
        self,
        text: str | None = None,
        inline_keypad: list | KeyPad | None = None,
        keypad: list | KeyPad | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        auto_delete: int | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
        # file
        file: str  | Path  | bytes  | None = None,
        name_file: str | None = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif" , "Video"] = "File",
        file_id: str | None = None,
        show_progress: bool = True,
        chunk_size: int = 1024 * 1024,
        # poll
        question: str | None = None,
        options: list | None = None,
        type_poll: Literal["Regular", "Quiz"] = "Regular",
        is_anonymous: bool = True,
        correct_option_index: int | None = None,
        allows_multiple_answers: bool = False,
        hint: str | None = None,
        # location
        latitude: str | None = None,
        longitude: str | None = None,
        # contact
        first_name: str | None = None,
        last_name: str | None = None,
        phone_number: str | None = None,

        chat_id: str | None = None,
        reply_to_message_id: str | None = None
    ) -> Union['msg_update', asyncio.Task['msg_update']]:
        """reply message / ریپلای پیام"""
        return await self._client.send_message(
            text=text,
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            reply_to_message_id=Utils.prefer_first(reply_to_message_id, self.new_message.message_id),
            inline_keypad=inline_keypad,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            keypad=keypad,
            on_time_keyboard=on_time_keyboard,
            resize_keyboard=resize_keyboard,
            meta_data=meta_data,
            file=file,
            name_file=name_file,
            type_file=type_file,
            file_id=file_id,
            show_progress=show_progress,
            question=question,
            options=options,
            type_poll=type_poll,
            is_anonymous=is_anonymous,
            correct_option_index=correct_option_index,
            allows_multiple_answers=allows_multiple_answers,
            hint=hint,
            latitude=latitude,
            longitude=longitude,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            chunk_size=chunk_size,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )

    async def reply_text(
        self,
        text: str,
        inline_keypad: list | KeyPad | None = None,
        keypad: list | KeyPad | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        auto_delete: int | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        wait_send: float | None = None,
        return_task: bool = False,
        chat_id: str | None = None,
        reply_to_message_id: str | None = None,
        context: dict | None = None,
        auto_escape: bool = True,
    ) -> Union['msg_update', asyncio.Task['msg_update']]:
        """reply text / ریپلای متن"""
        return await self._client.send_text(
            text=text,
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            reply_to_message_id=Utils.prefer_first(reply_to_message_id, self.new_message.message_id),
            inline_keypad=inline_keypad,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            keypad=keypad,
            on_time_keyboard=on_time_keyboard,
            resize_keyboard=resize_keyboard,
            meta_data=meta_data,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )

    async def reply_poll(
        self,
        question: str,
        options: list,
        type_poll: Literal["Regular", "Quiz"] = "Regular",
        is_anonymous: bool = True,
        correct_option_index: int | None = None,
        allows_multiple_answers: bool = False,
        hint: str | None = None,
        auto_delete: int | None = None,
        wait_send: float | None = None,
        return_task: bool = False,
        chat_id: str | None = None,
        reply_to_message_id: str | None = None
    ) -> Union['msg_update', asyncio.Task['msg_update']]:
        """reply poll / ریپلای نظرسنجی"""
        return await self._client.send_poll(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            question=question,
            options=options,
            type_poll=type_poll,
            is_anonymous=is_anonymous,
            correct_option_index=correct_option_index,
            allows_multiple_answers=allows_multiple_answers,
            hint=hint,
            auto_delete=auto_delete,
            reply_to_message_id=Utils.prefer_first(reply_to_message_id, self.new_message.message_id),
            wait_send=wait_send,
            return_task=return_task
        )

    async def reply_contact(
        self,
        first_name: str,
        phone_number: str,
        last_name: str = "",
        auto_delete: int | None = None,
        inline_keypad: list | KeyPad | None = None,
        wait_send: float | None = None,
        return_task: bool = False,
        chat_id: str | None = None,
        reply_to_message_id: str | None = None
    ) -> Union['msg_update', asyncio.Task['msg_update']]:
        """reply contact / ریپلای مخاطب"""
        return await self._client.send_contact(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            reply_to_message_id=Utils.prefer_first(reply_to_message_id, self.new_message.message_id),
            auto_delete=auto_delete,
            inline_keypad=inline_keypad,
            wait_send=wait_send,
            return_task=return_task
        )

    async def reply_location(
        self,
        latitude: str,
        longitude: str,
        auto_delete: int | None = None,
        wait_send: float | None = None,
        return_task: bool = False,
        chat_id: str | None = None,
        reply_to_message_id: str | None = None
    ) -> Union['msg_update', asyncio.Task['msg_update']]:
        """reply location / ریپلای موقعیت مکانی"""
        return await self._client.send_location(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            latitude=latitude,
            longitude=longitude,
            reply_to_message_id=Utils.prefer_first(reply_to_message_id, self.new_message.message_id),
            auto_delete=auto_delete,
            wait_send=wait_send,
            return_task=return_task
        )

    async def reply_file(
        self,
        file: str  | Path  | bytes,
        name_file: str | None = None,
        text: str | None = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif","Video"] = "File",
        disable_notification: bool = False,
        auto_delete: int | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        inline_keypad: list | KeyPad | None = None,
        keypad: list | KeyPad | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        show_progress: bool = True,
        wait_send: float | None = None,
        return_task: bool = False,
        chunk_size: int = 1024 * 1024,
        context: dict | None = None,
        auto_escape: bool = True,
        chat_id: str | None = None,
        reply_to_message_id: str | None = None,
    ) -> Union['msg_update', asyncio.Task['msg_update']]:
        """reply file / ریپلای فایل"""
        return await self._client.base_send_file(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            file=file,
            name_file=name_file,
            text=text,
            reply_to_message_id=Utils.prefer_first(reply_to_message_id, self.new_message.message_id),
            type_file=type_file,
            disable_notification=disable_notification,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            show_progress=show_progress,
            chunk_size=chunk_size,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )
    
    reply_document = reply_file

    async def reply_image(
        self,
        image: str  | Path  | bytes,
        name_file: str | None = None,
        text: str | None = None,
        disable_notification: bool = False,
        auto_delete: int | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        inline_keypad: list | KeyPad | None = None,
        keypad: list | KeyPad | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        show_progress: bool = True,
        chunk_size: int = 1024 * 1024,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
        chat_id: str | None = None,
        reply_to_message_id: str | None = None
    ) -> Union['msg_update', asyncio.Task['msg_update']]:
        """reply image / رپیلای تصویر"""
        return await self._client.send_image(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            image=image,
            name_file=name_file,
            text=text,
            reply_to_message_id=Utils.prefer_first(reply_to_message_id, self.new_message.message_id),
            disable_notification=disable_notification,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            show_progress=show_progress,
            chunk_size=chunk_size,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )

    async def reply_voice(
        self,
        voice: str  | Path  | bytes,
        name_file: str | None = None,
        text: str | None = None,
        disable_notification: bool = False,
        auto_delete: int | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        inline_keypad: list | KeyPad | None = None,
        keypad: list | KeyPad | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        show_progress: bool = True,
        chunk_size: int = 1024 * 1024,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
        chat_id: str | None = None,
        reply_to_message_id: str | None = None
    ) -> Union['msg_update', asyncio.Task['msg_update']]:
        """reply voice / رپیلای ویس"""
        return await self._client.send_voice(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            voice=voice,
            name_file=name_file,
            text=text,
            reply_to_message_id=Utils.prefer_first(reply_to_message_id, self.new_message.message_id),
            disable_notification=disable_notification,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            show_progress=show_progress,
            chunk_size=chunk_size,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )

    async def reply_music(
        self,
        music: str  | Path  | bytes,
        name_file: str | None = None,
        text: str | None = None,
        disable_notification: bool = False,
        auto_delete: int | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        inline_keypad: list | KeyPad | None = None,
        keypad: list | KeyPad | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        show_progress: bool = True,
        chat_id: str | None = None,
        chunk_size: int = 1024 * 1024,
        wait_send: float | None = None,
        context: dict | None = None,
        auto_escape: bool = True,
        return_task: bool = False,
        reply_to_message_id: str | None = None
    ) -> Union['msg_update', asyncio.Task['msg_update']]:
        """reply voice / رپیلای موزیک"""
        return await self._client.send_music(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            music=music,
            name_file=name_file,
            text=text,
            reply_to_message_id=Utils.prefer_first(reply_to_message_id, self.new_message.message_id),
            disable_notification=disable_notification,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            show_progress=show_progress,
            chunk_size=chunk_size,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )

    async def reply_gif(
        self,
        gif: str  | Path  | bytes,
        name_file: str | None = None,
        text: str | None = None,
        disable_notification: bool = False,
        auto_delete: int | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        inline_keypad: list | KeyPad | None = None,
        keypad: list | KeyPad | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        show_progress: bool = True,
        chunk_size: int = 1024 * 1024,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
        chat_id: str | None = None,
        reply_to_message_id: str | None = None
    ) -> Union['msg_update', asyncio.Task['msg_update']]:
        """reply voice / رپیلای گیف"""
        return await self._client.send_gif(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            gif=gif,
            name_file=name_file,
            text=text,
            reply_to_message_id=Utils.prefer_first(reply_to_message_id, self.new_message.message_id),
            disable_notification=disable_notification,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            show_progress=show_progress,
            chunk_size=chunk_size,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )

    async def reply_video(
        self,
        video: str  | Path  | bytes,
        name_file: str | None = None,
        text: str | None = None,
        disable_notification: bool = False,
        auto_delete: int | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        inline_keypad: list | KeyPad | None = None,
        keypad: list | KeyPad | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        show_progress: bool = True,
        chunk_size: int = 1024 * 1024,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
        chat_id: str | None = None,
        reply_to_message_id: str | None = None
    ) -> Union['msg_update', asyncio.Task['msg_update']]:
        """reply voice / رپیلای ویدیو"""
        return await self._client.send_video(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            video=video,
            name_file=name_file,
            text=text,
            reply_to_message_id=Utils.prefer_first(reply_to_message_id, self.new_message.message_id),
            disable_notification=disable_notification,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            show_progress=show_progress,
            chunk_size=chunk_size,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )

    async def forward(
        self,
        to_chat_id: str,
        auto_delete: int | None = None,
        wait_send: float | None = None,
        return_task: bool = False,
        from_chat_id: str | None = None,
        message_id: str | None = None
    ) -> Union['msg_update', asyncio.Task['msg_update']]:
        """forward / فوروارد"""
        return await self._client.forward_message(
            from_chat_id=Utils.prefer_first(from_chat_id, self.chat_id),
            message_id=Utils.prefer_first(message_id, self.new_message.message_id),
            to_chat_id=to_chat_id,
            auto_delete=auto_delete,
            wait_send=wait_send,
            return_task=return_task
        )

    async def download(
        self,
        path : str = "file",
        file_id: str | None = None,
        show_progress: bool = True,
        wait_send: float | None = None,
        return_task: bool = False,
    ) -> None:
        """download / دانلود"""
        final_id = file_id or self.new_message.file.file_id
        if final_id is None:
            raise TypeError("Message is not file and you not got the file_id Arg.")
        await self._client.download_file(
            id_file=final_id,
            path=path,
            show_progress=show_progress,
            wait_send=wait_send,
            return_task=return_task
        )
    
    async def get_download_file_url(
        self,
        file_id: str | None = None,
        wait_send: float | None = None,
        return_task: bool = False,
    ) -> str | None | asyncio.Task[str | None]:
        """getting url download file / گرفتن لینک دانلود فایل"""
        final_id = file_id or self.new_message.file.file_id
        if final_id is None:
            raise TypeError("Message is not file and you not got the file_id Arg.")
        return await self._client.get_download_file_url(
            id_file=final_id,
            wait_send=wait_send,
            return_task=return_task
        )

    async def delete(
        self,
        wait_send: float | None = None,
        return_task: bool = False,
        chat_id: str | None = None,
        message_id: str | None = None
    ) -> props | asyncio.Task[props]:
        """delete / حذف"""
        return await self._client.delete_message(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            message_id=Utils.prefer_first(message_id, self.new_message.message_id),
            wait_send=wait_send,
            return_task=return_task
        )
    
    async def ban(
        self,
        wait_send: float | None = None,
        return_task: bool = False,
        chat_id: str | None = None,
        user_id: str | None = None
    ):
        """ban user / بن کاربر"""
        return await self._client.ban_chat_member(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            user_id=Utils.prefer_first(user_id, self.new_message.sender_id),
            wait_send=wait_send,
            return_task=return_task
        )
    
    async def unban(
        self,
        wait_send: float | None = None,
        return_task: bool = False,
        chat_id: str | None = None,
        user_id: str | None = None
    ):
        """un ban user / آنبن کاربر"""
        return await self._client.unban_chat_member(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            user_id=Utils.prefer_first(user_id, self.new_message.sender_id),
            wait_send=wait_send,
            return_task=return_task
        )

    async def ban_reply(
        self,
        wait_send: float | None = None,
        return_task: bool = False,
        chat_id: str | None = None,
    ):
        if not self.new_message.reply_to_message_id:
            return None
        msg = await self._client.get_message(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            message_id=self.new_message.reply_to_message_id
        )
        if not msg:
            return None
        return await self._client.ban_chat_member(
            chat_id=self.chat_id,
            user_id=msg.sender_id,
            wait_send=wait_send,
            return_task=return_task
        )

    async def unban_reply(
        self,
        wait_send: float | None = None,
        return_task: bool = False,
        chat_id: str | None = None
    ):
        if not self.new_message.reply_to_message_id:
            return None
        msg = await self._client.get_message(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            message_id=self.new_message.reply_to_message_id
        )
        if not msg:
            return None
        return await self._client.unban_chat_member(
            chat_id=self.chat_id,
            user_id=msg.sender_id,
            wait_send=wait_send,
            return_task=return_task
        )

    async def get_reply(
        self,
        chat_id: str | None = None,
        message_id: str | None = None
    ):
        """get message replyed / گرفتن پیام ریپلای شده"""
        if not self.is_reply:
            return None
        msg = await self._client.get_message(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            message_id=Utils.prefer_first(message_id, self.new_message.reply_to_message_id)
        )
        return msg
    
    async def resend_message(
        self,
        to_chat_id: str | None = None,
        auto_delete: int | None = None,
        parse_mode: Literal['Markdown', 'HTML'] = "Markdown",
        meta_data: list = [],
        name_save_file: str | None = None,
        show_progress: bool = True,
        chunk_size: int = 1024 * 1024,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
    ):
        to_chat_id = to_chat_id if to_chat_id else self.chat_id
        return await self._client.resend_message(
            message_id=self.new_message.message_id,
            from_chat_id=self.chat_id,
            to_chat_id=to_chat_id,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            name_save_file=name_save_file,
            show_progress=show_progress,
            chunk_size=chunk_size,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )
    
    copy_message = resend_message


wrap_all_async_methods(Update)

Message = Update
Updates = Update
