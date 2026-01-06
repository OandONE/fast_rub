from typing import List
import re
import time as ti
from .types import Message
from .utils import Utils

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
        return message["chat_updates"]["chat"]["last_message"]["is_mine"]

class text(Filter):
    """filter text message by text /  فیلتر کردن متن پیام بر اساس متنی"""
    def __init__(self, pattern: str):
        self.pattern = pattern

    def __call__(self, message: Message) -> bool:
        return message.text == self.pattern

class regex(Filter):
    """filter text message by regex pattern / فیلتر متن پیام با regex"""
    def __init__(self, pattern: str, flags=0):
        self.pattern = re.compile(pattern, flags)

    def __call__(self, message: Message) -> bool:
        return bool(self.pattern.search(message.text or ""))

class commands(Filter):
    """filter text message by commands / فیلتر کردن متن پیام با دستورات"""
    def __init__(self, commands: List[str]):
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
    def __init__(self, guids: List[str]):
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
    def __init__(self, guids: List[str]):
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
    def __init__(self, filters_list: List[str]):
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