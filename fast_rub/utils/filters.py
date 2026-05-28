from typing import TYPE_CHECKING
import re
import time as ti

from fast_rub.type import Update

if TYPE_CHECKING:
    from ..type import Update

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

class AsyncFilter(Filter):
    def __call__(self, update: 'Update') -> bool:
        raise RuntimeError("The Class Is Async. Sync -> Filter class")
    async def __acall__(self, update: 'Update') -> bool:
        raise NotImplementedError

class _AndFilter(Filter):
    def __init__(
        self,
        left: Filter,
        right: Filter
    ) -> None:
        self.left = left
        self.right = right
    
    def __call__(self, update: Update) -> bool:
        return self.left(update) and self.right(update)

class _OrFilter(Filter):
    def __init__(
        self,
        left: Filter,
        right: Filter
    ) -> None:
        self.left = left
        self.right = right
    
    def __call__(self, update: Update) -> bool:
        return self.left(update) or self.right(update)

class _NotFilter(Filter):
    def __init__(
        self,
        filter: Filter
    ) -> None:
        self.filter = filter
    
    def __call__(self, update: Update) -> bool:
        return not self.filter(update)

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
    def __init__(self, pattern: str, flags=0):
        self.pattern = re.compile(pattern, flags)
    def __call__(self, update: 'Update') -> bool:
        if not hasattr(update, "text") or update.text is None:
            return False
        return bool(self.pattern.search(update.text))

class time(Filter):
    """filter by time / فیلتر با زمان"""
    def __init__(self,from_time:float=0,end_time=float("inf")):
        self.from_time = from_time
        self.end_time = end_time
    def __call__(self, update:'Update'):
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
        return update.is_fowrard

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
    def __init__(self, prefix: str):
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
        return bool(re.compile(r"").search(str(update.text))) # TODO


class and_filter(Filter):
    """filters {and} for if all filters is True : run code ... / فیلتر های ورودی {and} که اگر تمامی فیلتر های ورودی برابر True بود اجرا شود"""
    def __init__(self, *filters):
        self.filters = filters

    def __call__(self, update: 'Update') -> bool:
        return all(f(update) for f in self.filters)

class or_filter(Filter):
    """filters {or} for if one filter is True : run code ... / فیلتر های ورودی {and} که اگر یک فیلتر ورودی برابر True بود اجرا شود"""
    def __init__(self, *filters):
        self.filters = filters

    def __call__(self, update: 'Update') -> bool:
        return any(f(update) for f in self.filters)

class not_filter(Filter):
    """not True filter / درست نبودن فیلتر"""
    def __init__(self, filter):
        self.filter = filter
    def __call__(self, update: 'Update') -> bool:
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

