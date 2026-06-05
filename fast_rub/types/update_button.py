from typing import TYPE_CHECKING, Literal
from pathlib import Path
import json

from ..utils import Utils
from .props import props
from ..core import wrap_all_async_methods

if TYPE_CHECKING:
    from ..core import Client

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

    async def send_text(
        self,
        text: str,
        inline_keypad: list | None = None,
        keypad: list | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        disable_notification: bool = False,
        auto_delete: int | None = None,
        reply_to_message_id: str | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
        chat_id: str | None = None
    ):
        """send text / ارسال متن"""
        return await self._client.send_text(
            text=text,
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            inline_keypad=inline_keypad,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id,
            parse_mode=parse_mode,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            meta_data=meta_data,
            disable_notification=disable_notification,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )
    
    async def send_message(
        self,
        text: str | None = None,
        inline_keypad: list | None = None,
        keypad: list | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        reply_to_message_id: str | None = None,
        auto_delete: int | None = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: list | None = None,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
        disable_notification: bool = False,
        # file
        file: str  | Path  | bytes  | None = None,
        name_file: str | None = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif" , "Video"] = "File",
        file_id: str | None = None,
        show_progress: bool = True,
        chunk_size: int = 64 * 1024,
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

        chat_id: str | None = None
    ):
        """send message / ارسال پیام"""
        return await self._client.send_message(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            text=text,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            reply_to_message_id=reply_to_message_id,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
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
            disable_notification=disable_notification,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )

    async def send_pool(
        self,
        question: str,
        options : list,
        type_poll: Literal['Regular', 'Quiz'] = "Regular",
        is_anonymous: bool = True,
        correct_option_index: int | None = None,
        allows_multiple_answers: bool = False,
        hint: str | None = None,
        auto_delete: int | None = None,
        reply_to_message_id: str | None = None,
        chat_id: str | None = None
    ):
        """sending pool / ارسال نظرسنجی"""
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
            reply_to_message_id=reply_to_message_id
        )

    async def send_contact(
        self,
        first_name: str,
        last_name: str,
        phone_number: str,
        auto_delete: int | None = None,
        reply_to_message_id: str | None = None,
        inline_keypad: list | None = None,
        chat_id: str | None = None
    ):
        """sending contact / ارسال مخاطب"""
        return await self._client.send_contact(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id,
            inline_keypad=inline_keypad
        )

    async def send_location(
        self,
        latitude: str,
        longitude: str,
        auto_delete: int | None = None,
        reply_to_message_id: str | None = None,
        chat_id: str | None = None
    ):
        """sending location / ارسال موقعیت مکانی"""
        return await self._client.send_location(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            latitude=latitude,
            longitude=longitude,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id
        )

    async def send_file(
        self,
        file: str  | Path  | bytes,
        name_file: str | None = None,
        text: str | None = None,
        type_file: Literal['File', 'Image', 'Voice', 'Music', 'Gif', 'Video'] = "File",
        auto_delete: int | None = None,
        reply_to_message_id: str | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        inline_keypad: list | None = None,
        keypad: list | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chat_id: str | None = None,
        chunk_size: int = 64 * 1024,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
        disable_notification: bool = False,
    ):
        """sending file / ارسال فایل"""
        return await self._client.base_send_file(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            file=file,
            name_file=name_file,
            text=text,
            type_file=type_file,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size,
            disable_notification=disable_notification,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )
    
    async def send_document(
        self,
        file: str  | Path  | bytes,
        name_file: str | None = None,
        text: str | None = None,
        auto_delete: int | None = None,
        reply_to_message_id: str | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        inline_keypad: list | None = None,
        keypad: list | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chat_id: str | None = None,
        chunk_size: int = 64 * 1024,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
        disable_notification: bool = False,
    ):
        """sending file / ارسال فایل"""
        return await self._client.send_document(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            file=file,
            name_file=name_file,
            text=text,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size,
            disable_notification=disable_notification,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )

    async def send_image(
        self,
        image: str  | Path  | bytes,
        name_file: str | None = None,
        text: str | None = None,
        auto_delete: int | None = None,
        reply_to_message_id: str | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        inline_keypad: list | None = None,
        keypad: list | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chat_id: str | None = None,
        chunk_size: int = 64 * 1024,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
        disable_notification: bool = False,
    ):
        """sending image / ارسال تصویر"""
        return await self._client.send_image(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            image=image,
            name_file=name_file,
            text=text,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size,
            disable_notification=disable_notification,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )

    async def send_video(
        self,
        video: str  | Path  | bytes,
        name_file: str | None = None,
        text: str | None = None,
        auto_delete: int | None = None,
        reply_to_message_id: str | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        inline_keypad: list | None = None,
        keypad: list | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chat_id: str | None = None,
        chunk_size: int = 64 * 1024,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
        disable_notification: bool = False,
    ):
        """sending video / ارسال ویدیو"""
        return await self._client.send_video(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            video=video,
            name_file=name_file,
            text=text,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size,
            disable_notification=disable_notification,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )

    async def send_voice(
        self,
        voice: str  | Path  | bytes,
        name_file: str | None = None,
        text: str | None = None,
        auto_delete: int | None = None,
        reply_to_message_id: str | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        inline_keypad: list | None = None,
        keypad: list | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chat_id: str | None = None,
        chunk_size: int = 64 * 1024,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
        disable_notification: bool = False,
    ):
        """sending voice / ارسال ویس"""
        return await self._client.send_voice(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            voice=voice,
            name_file=name_file,
            text=text,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size,
            disable_notification=disable_notification,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )

    async def send_music(
        self,
        music: str  | Path  | bytes,
        name_file: str | None = None,
        text: str | None = None,
        auto_delete: int | None = None,
        reply_to_message_id: str | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        inline_keypad: list | None = None,
        keypad: list | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chat_id: str | None = None,
        chunk_size: int = 64 * 1024,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
        disable_notification: bool = False,
    ):
        """sending music / ارسال موزیک"""
        return await self._client.send_music(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            music=music,
            name_file=name_file,
            text=text,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size,
            disable_notification=disable_notification,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )

    async def send_gif(
        self,
        gif: str  | Path  | bytes,
        name_file: str | None = None,
        text: str | None = None,
        auto_delete: int | None = None,
        reply_to_message_id: str | None = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: list | None = None,
        inline_keypad: list | None = None,
        keypad: list | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chat_id: str | None = None,
        chunk_size: int = 64 * 1024,
        wait_send: float | None = None,
        return_task: bool = False,
        context: dict | None = None,
        auto_escape: bool = True,
        disable_notification: bool = False,
    ):
        """sending gif / ارسال گیف"""
        return await self._client.send_gif(
            chat_id=Utils.prefer_first(chat_id, self.chat_id),
            gif=gif,
            name_file=name_file,
            text=text,
            auto_delete=auto_delete,
            reply_to_message_id=reply_to_message_id,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size,
            disable_notification=disable_notification,
            wait_send=wait_send,
            return_task=return_task,
            context=context,
            auto_escape=auto_escape
        )
    
    def to_dict(
        self
    ) -> dict:
        """convert Update to Dict / تبدیل آپدیت به دیکشنری"""
        if isinstance(self._data, props):
            self._data = dict(self._data.to_dict())
        return self._data

    def __str__(self) -> str:
        return json.dumps(
            self.to_dict(),
            indent=4,
            ensure_ascii=False
        )

    def __repr__(self) -> str:
        return self.__str__()


wrap_all_async_methods(UpdateButton)

InlineUpdate = UpdateButton
UpdateInline = UpdateButton
ButtonUpdate = UpdateButton
InlineMessage = UpdateButton
MessageInline = UpdateButton

