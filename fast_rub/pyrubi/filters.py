import re as _re
from .types import Message
from .utils import Utils

from typing import Callable, Awaitable

import inspect

class Filter:
    """Base filter class"""
    def __call__(self, message: Message) -> bool:
        raise NotImplementedError

class is_user(Filter):
    """filter by user / فیلتر با کاربر"""
    def __call__(self, message: Message) -> bool:
        return message.chat_type.lower() == "user"

class is_group(Filter):
    """filter by group / فیلتر با گروه"""
    def __call__(self, message: Message) -> bool:
        return message.chat_type.lower() == "group"

class is_channel(Filter):
    """filter by channel / فیلتر با کانال"""
    def __call__(self, message: Message) -> bool:
        return message.chat_type.lower() == "channel"

class is_bot(Filter):
    """filter by bot / فیلتر با بات"""
    def __call__(self, message: Message) -> bool:
        return message.chat_type.lower() == "bot"

class is_text(Filter):
    """filter by is text message / فیلتر با متن بودن پیام"""
    def __call__(self, message: Message) -> bool:
        return message.message_type.lower() == "text"

class is_image(Filter):
    """filter by is image message / فیلتر با تصویر بودن پیام"""
    def __call__(self, message: Message) -> bool:
        return message.message_type.lower() == "image"

class is_video(Filter):
    """filter by is video message / فیلتر با ویدیو بودن پیام"""
    def __call__(self, message: Message) -> bool:
        return message.message_type.lower() == "video"

class is_gif(Filter):
    """filter by is gif message / فیلتر با گیف بودن پیام"""
    def __call__(self, message: Message) -> bool:
        return message.message_type.lower() == "gif"

class is_voice(Filter):
    """filter by is voice message / فیلتر با ویس بودن پیام"""
    def __call__(self, message: Message) -> bool:
        return message.message_type.lower() == "voice"

class is_music(Filter):
    """filter by is music message / فیلتر با موزیک بودن پیام"""
    def __call__(self, message: Message) -> bool:
        return message.message_type.lower() == "music"

class is_file(Filter):
    """filter by is file message / فیلتر با فایل بودن پیام"""
    def __call__(self, message: Message) -> bool:
        return message.message_type.lower() == "file"

class is_sticker(Filter):
    """filter by is sticker message / فیلتر با استیکر بودن پیام"""
    def __call__(self, message: Message) -> bool:
        return message.message_type.lower() == "sticker"

class is_me(Filter):
    """filter by my messages / فیلتر با پیام های من"""
    def __call__(self, message: Message) -> bool:
        chat_updates = message.get("chat_updates")
        if isinstance(chat_updates, list):
            if not chat_updates:
                return False
            chat_updates = chat_updates[0]
        elif not isinstance(chat_updates, dict):
            return False
        chat = chat_updates.get("chat")
        if not isinstance(chat, dict):
            return False
        last_message = chat.get("last_message")
        if not isinstance(last_message, dict):
            return False
        return last_message.get("is_mine", False)

class text(Filter):
    """filter text message by text /  فیلتر کردن متن پیام بر اساس متنی"""
    def __init__(self, pattern: str):
        self.pattern = pattern

    def __call__(self, message: Message) -> bool:
        return message.text == self.pattern

class regex(Filter):
    """filter text message by regex pattern / فیلتر متن پیام با regex"""
    def __init__(self, pattern: str, flags=0):
        self.pattern = _re.compile(pattern, flags)

    def __call__(self, message: Message) -> bool:
        return bool(self.pattern.search(message.text or ""))

class commands(Filter):
    """filter text message by commands / فیلتر کردن متن پیام با دستورات"""
    def __init__(self, commands: list[str]):
        self.commands = [cmd.lower() for cmd in commands]

    def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        text = message.text.lower()
        return any(text == cmd or text.startswith(cmd + ' ') for cmd in self.commands)

class object_guid(Filter):
    """filter by object guid / فیلتر با آبجکت گوید"""
    def __init__(self, guid: str):
        self.guid = guid

    def __call__(self, message: Message) -> bool:
        return message.object_guid == self.guid

class object_guids(Filter):
    """filter by object guids / فیلتر با آبجکت گوید ها"""
    def __init__(self, guids: list[str]):
        self.guids = [guid.lower() for guid in guids]

    def __call__(self, message: Message) -> bool:
        return message.object_guid.lower() in self.guids

class author_guid(Filter):
    """filter by author guid / فیلتر با فرستنده گوید"""
    def __init__(self, guid: str):
        self.guid = guid

    def __call__(self, message: Message) -> bool:
        return message.author_guid == self.guid

class author_guids(Filter):
    """filter by author guids / فیلتر با فرستنده های گوید"""
    def __init__(self, guids: list[str]):
        self.guids = [guid.lower() for guid in guids]

    def __call__(self, message: Message) -> bool:
        return message.author_guid.lower() in self.guids

class time_range(Filter):
    """filter by time / فیلتر با زمان"""
    def __init__(self, from_time: float = 0, to_time: float = float("inf")):
        self.from_time = from_time
        self.to_time = to_time

    def __call__(self, message: Message) -> bool:
        message_time = int(message.time)
        return self.from_time <= message_time <= self.to_time

class starts_with(Filter):
    """filter text starting with / فیلتر متن هایی که با این شروع میشن"""
    def __init__(self, prefix: str):
        self.prefix = prefix
    def __call__(self, message: Message) -> bool:
        return message.text != None and message.text.startswith(self.prefix)

class ends_with(Filter):
    """filter text ending with / فیلتر متن هایی که با این پایان میابند"""
    def __init__(self, suffix: str):
        self.suffix = suffix
    def __call__(self, message: Message) -> bool:
        return message.text != None and message.text.endswith(self.suffix)

class and_filter(Filter):
    """filters {and} for if all filters is True : run code ... / فیلتر های ورودی {and} که اگر تمامی فیلتر های ورودی برابر True بود اجرا شود"""
    def __init__(self, *filters):
        self.filters = filters

    def __call__(self, message: Message) -> bool:
        return all(f(message) for f in self.filters)

class or_filter(Filter):
    """filters {or} for if one filter is True : run code ... / فیلتر های ورودی {and} که اگر یک فیلتر ورودی برابر True بود اجرا شود"""
    def __init__(self, *filters):
        self.filters = filters

    def __call__(self, message: Message) -> bool:
        return any(f(message) for f in self.filters)

class not_filter(Filter):
    """filter by is False Filter / فیلتر با غلط بودن فیلتر"""
    def __init__(self, filter_obj):
        self.filter_obj = filter_obj

    def __call__(self, message: Message) -> bool:
        return not self.filter_obj(message)

class legacy_filter(Filter):
    """filter by chat type or message type (old filters PyRubi) / فیلتر با نوع چت یا نوع پیام (فیلتر های قدیمی پایروبی)"""
    def __init__(self, filters_list: list[str]):
        self.filters_list = [f.lower() for f in filters_list]
    def __call__(self, message: Message) -> bool:
        for filter_item in self.filters_list:
            if filter_item in ["user", "group", "channel", "bot"]:
                if message.chat_type.lower() == filter_item:
                    return True
            elif filter_item in ["text", "image", "video", "gif", "voice", "music", "file", "sticker"]:
                if message.message_type.lower() == filter_item:
                    return True
            elif Utils.getChatTypeByGuid(filter_item):
                if message.object_guid == filter_item:
                    return True
        return False

class in_text(Filter):
    """text in text message / وجود متن در متن آپدیت"""
    def __init__(self, text: str) -> None:
        self.text = text
    def __call__(self, message: 'Message') -> bool:
        if self.text in str(message.text):
            return True
        return False

class text_length(Filter):
    """filter by text length / فیلتر بر اساس طول متن"""
    def __init__(self, min_len: int = 0, max_len: float = float('inf')):
        self.min_len = min_len
        self.max_len = max_len
    def __call__(self, message: 'Message') -> bool:
        if message.text:
            return self.min_len <= len(message.text) <= self.max_len
        return False

class command(Filter):
    """filter text message by command / فیلتر کردن متن پیام با دستور"""
    def __init__(self, command: str):
        self.command = command

    def __call__(self, message: 'Message') -> bool:
        return message.text == f"/{self.command}"

# class file_name(Filter):
#     """filter by name file / فیلتر با اسم فایل"""
#     def __init__(self,name_file: str):
#         self.name_file = name_file
#     def __call__(self, message: 'Message') -> bool:
#         return True if message.file_name == self.name_file else False # TODO: Test for why getting the file message list

# class size_file(Filter):
#     """filter by name file / فیلتر با اسم فایل"""
#     def __init__(self,size: int):
#         self.size = size
#     def __call__(self, message: 'Message') -> bool:
#         return True if message.size_file == self.size else False # TODO: Test for why getting the file message list

class IsForward(Filter):
    """message is forward / پیام فوروارد شده"""
    def __call__(self, message: 'Message') -> bool:
        return message.is_forward

class IsReply(Filter):
    """message has reply / پیام دارای ریپلای"""
    def __call__(self, message: 'Message') -> bool:
        return message.reply_message_id != None

# class IsContact(Filter):
#     """filter by contact / فیلتر مخاطب"""
#     def __call__(self, message: 'Message') -> bool:
#         return message.is_contact # TODO: Wait for add is_contact property

class HasUserName(Filter):
    """filter by has username in text / فیلتر داشتن نام کاربری(آیدی) در متن پیام"""
    def __call__(self, message: 'Message') -> bool:
        return bool(_re.compile(r"@[a-zA-Z0-9_]{2,32}").search(str(message.text)))

class forward_from_object_guid(Filter):
    def __init__(
        self,
        object_guid: str
    ) -> None:
        self.object_guid = object_guid
    def __call__(self, message: 'Message') -> bool:
        return message.forward_object_guid == self.object_guid

class contact_phone_number(Filter):
    def __init__(
        self,
        phone_number: str
    ) -> None:
        self.phone_number = phone_number
    def __call__(self, message: 'Message') -> bool:
        return message.contact_phone_number == self.phone_number

class contact_first_name(Filter):
    def __init__(
        self,
        first_name: str
    ) -> None:
        self.first_name = first_name
    def __call__(self, message: 'Message') -> bool:
        return message.contact_first_name == self.first_name

class contact_last_name(Filter):
    def __init__(
        self,
        last_name: str
    ) -> None:
        self.last_name = last_name
    def __call__(self, message: 'Message') -> bool:
        return message.contact_last_name == self.last_name

class sticker_emoji_character(Filter):
    def __init__(
        self,
        emoji_character: str
    ) -> None:
        self.emoji_character = emoji_character
    def __call__(self, message: 'Message') -> bool:
        return message.sticker_emoji_character == self.emoji_character 

class sticker_sticker_id(Filter):
    def __init__(
        self,
        id_character: str
    ) -> None:
        self.id_character = id_character
    def __call__(self, message: 'Message') -> bool:
        return message.sticker_sticker_id == self.id_character 

class validate(Filter):
    """فیلتر اعتبارسنجی ورودی کاربر."""
    def __init__(
        self,
        email: bool = False,
        is_digit: bool = False,
        min_length: int = 0,
        max_length: int = -1,
    ):
        self.email = email
        self.is_digit = is_digit
        self.min_length = min_length
        self.max_length = max_length
    
    def __call__(self, message: 'Message') -> bool:
        if not message.text:
            return False
        
        text = message.text
        
        if self.email:
            email_pattern = _re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            if not email_pattern.search(text):
                return False
        
        if self.is_digit:
            if not text.isdigit():
                return False
        
        if len(text) < self.min_length:
            return False
        
        if self.max_length != float('inf') and len(text) > self.max_length:
            return False
        
        return True

class CrashProtection(Filter):
    def __call__(self, message: 'Message') -> bool:
        if not message.text:
            return True
        def check1(
            text: str
        ) -> bool:
            return not (bool(_re.match(r"^\d+(\.\d+)", text)))
        if check1(message.text):
            def check2(text: str):
                if not text:
                    return True
                if '\x00' in text:
                    return False
                zero_width = '\u200B\u200C\u200D\uFEFF'
                count = sum(1 for c in text if c in zero_width)
                if count > 50:
                    return False
                invisible = sum(1 for c in text if c in zero_width or c in '\u2060\u2061\u2062\u2063\u2064')
                if len(text) > 100 and invisible / len(text) > 0.5:
                    return False
                return True
            return check2(message.text)
        return False

class where(Filter):
    """فیلتر با شرط دلخواه"""
    def __init__(self, func: Callable[['Message'], bool]):
        self.func = func
    def __call__(self, message: 'Message') -> bool:
        return self.func(message)

Where = where

class check(Filter):
    """فیلتر با تابع شرط دلخواه (Sync یا Async)."""
    def __init__(self, func: Callable[..., bool | Awaitable[bool]]):
        self.func = func
        self._is_async = inspect.iscoroutinefunction(func)
    @property
    def type_filter(self):
        return "async" if self._is_async else "sync"
    def __call__(self, message: 'Message') -> bool:
        if self._is_async:
            raise RuntimeError("This filter is async. Use __acall__ instead.")
        return self.func(message) # type: ignore
    async def __acall__(self, message: 'Message') -> bool:
        if self._is_async:
            return await self.func(message) # type: ignore
        return self.func(message) # type: ignore

Check = check

"""TODO: metadata filters after test :
has_metadata_type
is_metadata_type
HasBold
HasItalic
HasUnderline
HasStrike
HasMono
HasSpoiler
HasLink
IsBold
IsItalic
IsUnderline
IsStrike
IsMono
IsSpoiler
IsLink

contact :
contact_phone_number
contact_first_name
contact_last_name

stiker :
sticker_emoji_character
sticker_sticker_id

db :
db_exists
db_not_exists
db_count
db_value_equals
"""

re = regex
is_forward = IsForward
is_reply = IsReply
crash_protection = CrashProtection

has_username = HasUserName()
