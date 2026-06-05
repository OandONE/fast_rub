from typing import TYPE_CHECKING, Literal, Any

from collections.abc import Callable, Awaitable
import re as _re
import time as ti
import inspect

from ..db import DataBase

if TYPE_CHECKING:
    from ..types import Update

class Filter:
    def __call__(self, update: 'Update') -> bool:
        raise NotImplementedError
    async def __acall__(self, update: 'Update') -> bool:
        return self(update)

    def __and__(self, other: 'Filter') -> '_AndFilter':
        return _AndFilter(self, other)
    
    def __or__(self, other: 'Filter') -> '_OrFilter':
        return _OrFilter(self, other)

    def __invert__(self) -> 'Filter':
        return _NotFilter(self)
    
    @property
    def type_filter(self) -> str:
        return "sync"

class AsyncFilter(Filter):
    def __call__(self, update: 'Update') -> bool:
        raise RuntimeError("The Class Is Async. Sync -> Filter class")
    async def __acall__(self, update: 'Update') -> bool:
        raise NotImplementedError
    
    @property
    def type_filter(self) -> str:
        return "async"

class text(Filter):
    """filter text message by text /  فیلتر کردن متن پیام بر اساس متنی"""
    def __init__(self, pattern: str):
        self.pattern = pattern

    def __call__(self, update: 'Update') -> bool:
        return update.text == self.pattern

class sender_id(Filter):
    """filter guid message by guid / فیلتر کردن شناسه گوید پیام"""
    def __init__(self, sender_id: str):
        self.sender_id = sender_id

    def __call__(self, update: 'Update') -> bool:
        return update.sender_id == self.sender_id

class IsUser(Filter):
    """filter type sender message by is PV(user) / فیلتر کردن تایپ ارسال کننده پیام با پیوی"""
    def __call__(self, update: 'Update') -> bool:
        return update.sender_type == "User"

class IsGroup(Filter):
    """filter type sender message by is group / فیلتر کردن تایپ ارسال کننده پیام با گروه"""
    def __call__(self, update: 'Update') -> bool:
        return update.sender_type == "Group"

class IsChannel(Filter):
    """filter type sender message by is channel / فیلتر کردن تایپ ارسال کننده پیام با کانال"""
    def __call__(self, update: 'Update') -> bool:
        return update.sender_type == "Channel"

class IsFile(Filter):
    """filter by file / فیلتر با فایل"""
    def __call__(self, update:'Update'):
        return True if update.file else False

class file_name(Filter):
    """filter by name file / فیلتر با اسم فایل"""
    def __init__(self,name_file: str):
        self.name_file = name_file
    def __call__(self, update:'Update'):
        return True if update.file_name==self.name_file else False

class size_file(Filter):
    """filter by name file / فیلتر با اسم فایل"""
    def __init__(self,size: int):
        self.size = size
    def __call__(self, update:'Update'):
        return True if update.size_file==self.size else False

class IsVideo(Filter):
    """filter by video / فیلتر با ویدیو"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="video" else False

class IsImage(Filter):
    """filter by image / فیلتر با عکس"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="image" else False

class IsAudio(Filter):
    """filter by audio / فیلتر با آودیو"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="audio" else False

class IsVoice(Filter):
    """filter by voice / فیلتر با ویس"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="voice" else False

class IsDocument(Filter):
    """filter by document / فیلتر با داکیومنت"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="document" else False

class IsWeb(Filter):
    """filter by web files / فیلتر با فایل های وب"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="web" else False

class IsCode(Filter):
    """filter by code files / فیلتر با فایل های کد"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="code" else False

class IsArchive(Filter):
    """filter by archive files / فیلتر با فایل های آرشیو"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="archive" else False

class IsExecutable(Filter):
    """filter by executable files / فیلتر با فایل های نصبی"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="executable" else False

class IsText(Filter):
    """filter by had text / فیلتر با داشتن متن"""
    def __call__(self, update:'Update'):
        return True if not update.text is None else False

class regex(Filter):
    """filter text message by regex pattern / فیلتر متن پیام با regex"""
    def __init__(self, pattern: str, flags: int = 0):
        self.pattern = _re.compile(pattern, flags)
    def __call__(self, update: 'Update') -> bool:
        if not hasattr(update, "text") or update.text is None:
            return False
        return bool(self.pattern.search(update.text))

class time(Filter):
    """filter by time / فیلتر با زمان"""
    def __init__(
        self,
        from_time: float = 0,
        end_time: float = float("inf")
    ):
        self.from_time = from_time
        self.end_time = end_time
    def __call__(self, update: 'Update'):
        if ti.time() > self.from_time and ti.time() < self.end_time:
            return True
        return False

class commands(Filter):
    """filter text message by commands / فیلتر کردن متن پیام با دستورات"""
    def __init__(self, commands: list):
        self.commands = commands

    def __call__(self, update: 'Update') -> bool:
        for command in self.commands:
            if (update.text != None) and (update.text == command or update.text.replace("/","") == command):
                return True
        return False

class sender_ids(Filter):
    """filter sender id message by sender ids / فیلتر کردن سندر آیدی پیام با سندر آیدی ها"""
    def __init__(self, sender_ids: list):
        self.sender_ids = sender_ids
    def __call__(self, update: 'Update') -> bool:
        for sender_id in self.sender_ids:
            if update.sender_id == sender_id:
                return True
        return False

user_ids = sender_ids

class chat_ids(Filter):
    """filter chat_id message by chat ids / فیلتر کردن چت آیدی پیام ارسال شده با چت آیدی ها"""
    def __init__(self, ids: list):
        self.ids = ids

    def __call__(self, update: 'Update') -> bool:
        for c in self.ids:
            if update.chat_id == c:
                return True
        return False

# Mata Data

class has_metadata_type(Filter):
    def __init__(self, type: str) -> None:
        self.type = type
    def __call__(self, update: 'Update') -> bool:
        if update.meta_data_parts:
            for mata_data in update.meta_data_parts.data:
                if mata_data["type"].lower() == self.type.lower():
                    return True
        return False

class is_metadata_type(Filter):
    def __init__(self, type: str) -> None:
        self.type = type
    def __call__(self, update: 'Update') -> bool:
        if update.meta_data_parts and len(update.meta_data_parts.data) != 1:
            if update.meta_data_parts.data[0]["type"].lower() == self.type.lower():
                return True
        return False

class HasBold(Filter):
    """check for has bold text / چک وجود داشتن متن بولد"""
    def __call__(self, update: 'Update') -> bool:
        return has_metadata_type("bold")(update)

class HasItalic(Filter):
    """check for has italic text / چک وجود داشتن متن ایتالیک"""
    def __call__(self, update: 'Update') -> bool:
        return has_metadata_type("italic")(update)

class HasUnderline(Filter):
    """check for has underline text / چک وجود داشتن متن آندرلایبن"""
    def __call__(self, update: 'Update') -> bool:
        return has_metadata_type("underline")(update)

class HasStrike(Filter):
    """check for has strike text / چک وجود داشتن متن خط خورده"""
    def __call__(self, update: 'Update') -> bool:
        return has_metadata_type("strike")(update)

class HasMono(Filter):
    """check for has mono text / چک وجود داشتن متن کپی"""
    def __call__(self, update: 'Update') -> bool:
        return has_metadata_type("mono")(update)

class HasSpoiler(Filter):
    """check for has spoiler text / چک وجود داشتن متن اسپویلر"""
    def __call__(self, update: 'Update') -> bool:
        return has_metadata_type("spoiler")(update)

class HasLink(Filter):
    """check for has link text / چک وجود داشتن متن هایپر لینک"""
    def __call__(self, update: 'Update') -> bool:
        return has_metadata_type("link")(update)

class IsBold(Filter):
    """all text is bold / بولد بودن تمام متن"""
    def __call__(self, update: 'Update') -> bool:
        return is_metadata_type("bold")(update)

class IsItalic(Filter):
    """all text is italic / ایتالیک بودن تمام متن"""
    def __call__(self, update: 'Update') -> bool:
        return is_metadata_type("italic")(update)

class IsUnderline(Filter):
    """all text is underline / آندرلاین بودن تمام متن"""
    def __call__(self, update: 'Update') -> bool:
        return is_metadata_type("underline")(update)

class IsStrike(Filter):
    """all text is strike / خط خورده بودن تمام متن"""
    def __call__(self, update: 'Update') -> bool:
        return is_metadata_type("strike")(update)

class IsMono(Filter):
    """all text is mono / متن کپی بودن تمام متن"""
    def __call__(self, update: 'Update') -> bool:
        return is_metadata_type("mono")(update)

class IsSpoiler(Filter):
    """all text is spoiler / اسپویلر بودن تمام متن"""
    def __call__(self, update: 'Update') -> bool:
        return is_metadata_type("spoiler")(update)

class IsLink(Filter):
    """all text is link / هایپر لینک بودن تمام متن"""
    def __call__(self, update: 'Update') -> bool:
        return is_metadata_type("link")(update)



class in_text(Filter):
    """text in text message / وجود متن در متن آپدیت"""
    def __init__(self, text: str) -> None:
        self.text = text
    def __call__(self, update: 'Update') -> bool:
        if self.text in str(update.text):
            return True
        return False

class IsForward(Filter):
    """message is forward / پیام فوروارد شده"""
    def __call__(self, update: 'Update') -> bool:
        return update.is_forward

class IsReply(Filter):
    """message has reply / پیام دارای ریپلای"""
    def __call__(self, update: 'Update') -> bool:
        return update.reply_to_message_id != None

class text_length(Filter):
    """filter by text length / فیلتر بر اساس طول متن"""
    def __init__(self, min_len: int = 0, max_len: float = float('inf')):
        self.min_len = min_len
        self.max_len = max_len
    def __call__(self, update: 'Update') -> bool:
        if update.text:
            return self.min_len <= len(update.text) <= self.max_len
        return False

class starts_with(Filter):
    """filter text starting with / فیلتر متن هایی که با این شروع میشن"""
    def __init__(
        self,
        prefix: str | tuple[str]
    ):
        self.prefix = prefix
    def __call__(self, update: 'Update') -> bool:
        return update.text != None and update.text.startswith(self.prefix)

class ends_with(Filter):
    """filter text ending with / فیلتر متن هایی که با این پایان میابند"""
    def __init__(self, suffix: str):
        self.suffix = suffix
    def __call__(self, update: 'Update') -> bool:
        return update.text != None and update.text.endswith(self.suffix)

class IsSticker(Filter):
    """filter by sticker / فیلتر استیکر"""
    def __call__(self, update: 'Update') -> bool:
        return update.is_sticker

class IsContact(Filter):
    """filter by contact / فیلتر مخاطب"""
    def __call__(self, update: 'Update') -> bool:
        return update.is_contact

class HasUserName(Filter):
    """filter by has username in text / فیلتر داشتن نام کاربری(آیدی) در متن پیام"""
    def __call__(self, update: 'Update') -> bool:
        return bool(_re.compile(r"@[a-zA-Z0-9_]{2,32}").search(str(update.text)))

class where(Filter):
    """فیلتر با شرط دلخواه"""
    def __init__(self, func: Callable[['Update'], bool]):
        self.func = func
    def __call__(self, update: 'Update') -> bool:
        return self.func(update)

Where = where

class check(Filter):
    """فیلتر با تابع شرط دلخواه (Sync یا Async)."""
    def __init__(self, func: Callable[..., bool | Awaitable[bool]]):
        self.func = func
        self._is_async = inspect.iscoroutinefunction(func)
    @property
    def type_filter(self):
        return "async" if self._is_async else "sync"
    def __call__(self, update: 'Update') -> bool:
        if self._is_async:
            raise RuntimeError("This filter is async. Use __acall__ instead.")
        return self.func(update) # type: ignore
    async def __acall__(self, update: 'Update') -> bool:
        if self._is_async:
            return await self.func(update) # type: ignore
        return self.func(update) # type: ignore

Check = check

class button_id(Filter):
    def __init__(
        self,
        button_id: str
    ) -> None:
        self.button_id = button_id
    def __call__(self, update: 'Update') -> bool:
        return update.button_id == self.button_id

class startswith_button_id(Filter):
    def __init__(
        self,
        button_id: str | tuple[str]
    ) -> None:
        self.button_id = button_id
    def __call__(self, update: 'Update') -> bool:
        return update.button_id.startswith(self.button_id) if update.button_id else False

class forward_from_sender_id(Filter):
    def __init__(
        self,
        sender_id: str
    ) -> None:
        self.sender_id = sender_id
    def __call__(self, update: 'Update') -> bool:
        return update.forward_from_sender_id == self.sender_id

class contact_phone_number(Filter):
    def __init__(
        self,
        phone_number: str
    ) -> None:
        self.phone_number = phone_number
    def __call__(self, update: "Update") -> bool:
        return update.contact_phone_number == self.phone_number

class contact_first_name(Filter):
    def __init__(
        self,
        first_name: str
    ) -> None:
        self.first_name = first_name
    def __call__(self, update: "Update") -> bool:
        return update.contact_first_name == self.first_name

class contact_last_name(Filter):
    def __init__(
        self,
        last_name: str
    ) -> None:
        self.last_name = last_name
    def __call__(self, update: "Update") -> bool:
        return update.contact_last_name == self.last_name

class sticker_emoji_character(Filter):
    def __init__(
        self,
        emoji_character: str
    ) -> None:
        self.emoji_character = emoji_character
    def __call__(self, update: "Update") -> bool:
        return update.sticker_emoji_character == self.emoji_character 

class sticker_sticker_id(Filter):
    def __init__(
        self,
        id_character: str
    ) -> None:
        self.id_character = id_character
    def __call__(self, update: "Update") -> bool:
        return update.sticker_sticker_id == self.id_character 

class removed_message_id(Filter):
    def __init__(
        self,
        id_character: str
    ) -> None:
        self.id_character = id_character
    def __call__(self, update: 'Update') -> bool:
        return update.removed_message_id == self.id_character 

class update_time(Filter):
    def __init__(
        self,
        time: int
    ) -> None:
        self.time = time
    def __call__(self, update: 'Update') -> bool:
        return update.update_time == self.time


class db_exists(AsyncFilter):
    """چک می‌کنه یه رکورد توی دیتابیس وجود داره یا نه"""
    def __init__(
        self,
        tabel_name: str,
        where_builder: Callable[['Update'], dict],
        db: DataBase | None = None,
        db_name: str | None = None,
        timeout: float = 10,
        journal_mode: Literal["DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF", "ROLLBACK"] = "WAL",
        synchronous: Literal["OFF", "NORMAL", "FULL", "EXTRA"] = "NORMAL",
    ) -> None:
        if db:
            self.db = db
        elif db_name:
            self.db = DataBase(db_name, timeout, journal_mode, synchronous)
        else:
            raise ValueError("db or db_name is required")
        self.tabel_name = tabel_name
        self.where_builder = where_builder
    
    async def __acall__(self, update: 'Update') -> bool:
        where_values = self.where_builder(update)
        return await self.db.exists(self.tabel_name, where_values)

class db_not_exists(AsyncFilter):
    """چک می‌کنه یه رکورد توی دیتابیس وجود نداره"""
    def __init__(
        self,
        tabel_name: str,
        where_builder: Callable[['Update'], dict],
        db: DataBase | None = None,
        db_name: str | None = None,
        timeout: float = 10,
        journal_mode: Literal["DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF", "ROLLBACK"] = "WAL",
        synchronous: Literal["OFF", "NORMAL", "FULL", "EXTRA"] = "NORMAL",
    ) -> None:
        if db:
            self.db = db
        elif db_name:
            self.db = DataBase(db_name, timeout, journal_mode, synchronous)
        else:
            raise ValueError("db or db_name is required")
        self.tabel_name = tabel_name
        self.where_builder = where_builder
    
    async def __acall__(self, update: 'Update') -> bool:
        where_values = self.where_builder(update)
        return not await self.db.exists(self.tabel_name, where_values)

class db_count(AsyncFilter):
    """چک می‌کنه تعداد رکوردها با شرط، بزرگتر از یه عدد باشه"""
    def __init__(
        self,
        tabel_name: str,
        where_builder: Callable[['Update'], dict],
        min_count: int = 1,
        db: DataBase | None = None,
        db_name: str | None = None,
        timeout: float = 10,
        journal_mode: Literal["DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF", "ROLLBACK"] = "WAL",
        synchronous: Literal["OFF", "NORMAL", "FULL", "EXTRA"] = "NORMAL",
    ) -> None:
        if db:
            self.db = db
        elif db_name:
            self.db = DataBase(db_name, timeout, journal_mode, synchronous)
        else:
            raise ValueError("db or db_name is required")
        self.tabel_name = tabel_name
        self.where_builder = where_builder
        self.min_count = min_count
    
    async def __acall__(self, update: 'Update') -> bool:
        where_values = self.where_builder(update)
        count = await self.db.len_rows(self.tabel_name, where_values)
        return count >= self.min_count

class db_value_equals(AsyncFilter):
    """چک می‌کنه مقدار یه ستون برابر با یه مقدار باشه"""
    def __init__(
        self,
        tabel_name: str,
        column: str,
        where_builder: Callable[['Update'], dict],
        expected_value: Any,
        db: DataBase | None = None,
        db_name: str | None = None,
        timeout: float = 10,
        journal_mode: Literal["DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF", "ROLLBACK"] = "WAL",
        synchronous: Literal["OFF", "NORMAL", "FULL", "EXTRA"] = "NORMAL",
    ) -> None:
        if db:
            self.db = db
        elif db_name:
            self.db = DataBase(db_name, timeout, journal_mode, synchronous)
        else:
            raise ValueError("db or db_name is required")
        self.tabel_name = tabel_name
        self.column = column
        self.where_builder = where_builder
        self.expected_value = expected_value
    
    async def __acall__(self, update: 'Update') -> bool:
        where_values = self.where_builder(update)
        result = await self.db.find(self.tabel_name, self.column, where_values)
        return result == self.expected_value

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
    
    def __call__(self, update: 'Update') -> bool:
        if not update.text:
            return False
        
        text = update.text
        
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
    def __call__(self, update: "Update") -> bool:
        if not update.text:
            return True
        def check1(
            text: str
        ) -> bool:
            return not (bool(_re.match(r"^\d+(\.\d+)", text)))
        if check1(update.text):
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
            return check2(update.text)
        return False



class _AndFilter(Filter):
    def __init__(self, left: Filter, right: Filter) -> None:
        self.left = left
        self.right = right
    
    @property
    def type_filter(self):
        if self.left.type_filter == "async" or self.right.type_filter == "async":
            return "async"
        return "sync"
    
    def __call__(self, update: "Update") -> bool:
        return self.left(update) and self.right(update)
    
    async def __acall__(self, update: "Update") -> bool:
        if self.left.type_filter == "async":
            left_result = await self.left.__acall__(update)
        else:
            left_result = self.left(update)
        
        if not left_result:
            return False
        
        if self.right.type_filter == "async":
            return await self.right.__acall__(update)
        else:
            return self.right(update)


class _OrFilter(Filter):
    def __init__(self, left: Filter, right: Filter) -> None:
        self.left = left
        self.right = right
    
    @property
    def type_filter(self):
        if self.left.type_filter == "async" or self.right.type_filter == "async":
            return "async"
        return "sync"
    
    def __call__(self, update: "Update") -> bool:
        return self.left(update) or self.right(update)
    
    async def __acall__(self, update: "Update") -> bool:
        if self.left.type_filter == "async":
            left_result = await self.left.__acall__(update)
        else:
            left_result = self.left(update)
        
        if left_result:
            return True
        
        if self.right.type_filter == "async":
            return await self.right.__acall__(update)
        else:
            return self.right(update)


class _NotFilter(Filter):
    def __init__(self, filter: Filter) -> None:
        self.filter = filter
    
    @property
    def type_filter(self):
        return self.filter.type_filter
    
    def __call__(self, update: "Update") -> bool:
        return not self.filter(update)
    
    async def __acall__(self, update: "Update") -> bool:
        if self.filter.type_filter == "async":
            return not await self.filter.__acall__(update)
        return not self.filter(update)


class and_filter(Filter):
    def __init__(self, *filters):
        self.filters = filters
    
    @property
    def type_filter(self):
        return "async" if any(f.type_filter == "async" for f in self.filters) else "sync"
    
    def __call__(self, update: 'Update') -> bool:
        return all(f(update) for f in self.filters)
    
    async def __acall__(self, update: 'Update') -> bool:
        for f in self.filters:
            if f.type_filter == "async":
                result = await f.__acall__(update)
            else:
                result = f(update)
            if not result:
                return False
        return True


class or_filter(Filter):
    def __init__(self, *filters):
        self.filters = filters
    
    @property
    def type_filter(self):
        return "async" if any(f.type_filter == "async" for f in self.filters) else "sync"
    
    def __call__(self, update: 'Update') -> bool:
        return any(f(update) for f in self.filters)
    
    async def __acall__(self, update: 'Update') -> bool:
        for f in self.filters:
            if f.type_filter == "async":
                result = await f.__acall__(update)
            else:
                result = f(update)
            if result:
                return True
        return False


class not_filter(Filter):
    def __init__(self, filter):
        self.filter = filter
    
    @property
    def type_filter(self):
        return self.filter.type_filter
    
    def __call__(self, update: 'Update') -> bool:
        return not self.filter(update)
    
    async def __acall__(self, update: 'Update') -> bool:
        if self.filter.type_filter == "async":
            return not await self.filter.__acall__(update)
        return not self.filter(update)


is_user = IsUser()
is_group = IsGroup()
is_channel = IsChannel()

is_reply = IsReply()
is_forward = IsForward()

is_link = IsLink()
is_spoiler = IsSpoiler()
is_mono = IsMono()
is_strike = IsStrike()
is_underline = IsUnderline()
is_italic = IsItalic()
is_bold = IsBold()
has_spoiler = HasSpoiler()
has_mono = HasMono()
has_strike = HasStrike()
has_underline = HasUnderline()
has_italic = HasItalic()
has_bold = HasBold()

is_contact = IsContact()
is_sticker = IsSticker()

is_text = IsText()
is_file = IsFile()

is_video = IsVideo()
is_image = IsImage()
is_audio = IsAudio()
is_archive = IsArchive()
is_voice = IsVoice()
is_document = IsDocument()
is_code = IsCode()
is_web = IsWeb()
is_executable = IsExecutable()

has_username = HasUserName()
is_username = has_username

re = regex

crash_protection = CrashProtection

