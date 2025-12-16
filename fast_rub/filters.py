from typing import TYPE_CHECKING
import re
import time as ti

from .type import Update

if TYPE_CHECKING:
    from .type import Update

class Filter:
    def __call__(self, update: 'Update') -> bool:
        raise NotImplementedError

class text(Filter):
    """filter text message by text /  فیلتر کردن متن پیام بر اساس متنی"""
    def __init__(self, pattern: str):
        self.pattern = pattern

    def __call__(self, update: 'Update') -> bool:
        return update.text == self.pattern

class sender_id(Filter):
    """filter guid message by guid / فیلتر کردن شناسه گوید پیام"""
    def __init__(self, user_id: str):
        self.user_id = user_id

    def __call__(self, update: 'Update') -> bool:
        return update.message.get('sender_id') == self.user_id

class is_user(Filter):
    """filter type sender message by is PV(user) / فیلتر کردن تایپ ارسال کننده پیام با پیوی"""
    def __call__(self, update: 'Update') -> bool:
        return update.sender_type == "User"

class is_group(Filter):
    """filter type sender message by is group / فیلتر کردن تایپ ارسال کننده پیام با گروه"""
    def __call__(self, update: 'Update') -> bool:
        return update.sender_type == "Group"

class is_channel(Filter):
    """filter type sender message by is channel / فیلتر کردن تایپ ارسال کننده پیام با کانال"""
    def __call__(self, update: 'Update') -> bool:
        return update.sender_type == "Channel"

class is_file(Filter):
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

class is_video(Filter):
    """filter by video / فیلتر با ویدیو"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="video" else False

class is_image(Filter):
    """filter by image / فیلتر با عکس"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="image" else False

class is_audio(Filter):
    """filter by audio / فیلتر با آودیو"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="audio" else False

class is_voice(Filter):
    """filter by voice / فیلتر با ویس"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="voice" else False

class is_document(Filter):
    """filter by document / فیلتر با داکیومنت"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="document" else False

class is_web(Filter):
    """filter by web files / فیلتر با فایل های وب"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="web" else False

class is_code(Filter):
    """filter by code files / فیلتر با فایل های کد"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="code" else False

class is_archive(Filter):
    """filter by archive files / فیلتر با فایل های آرشیو"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="archive" else False

class is_executable(Filter):
    """filter by executable files / فیلتر با فایل های نصبی"""
    def __call__(self, update:'Update'):
        return True if update.type_file=="executable" else False

class is_text(Filter):
    """filter by had text / فیلتر با داشتن متن"""
    def __call__(self, update:'Update'):
        return True if update.text!=None else False

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
    def __call__(self,update:'Update'):
        if ti.time()>self.from_time and ti.time()<self.end_time:
            return True
        return False



class commands(Filter):
    """filter text message by commands / فیلتر کردن متن پیام با دستورات"""
    def __init__(self, coms: list):
        self.coms = coms

    def __call__(self, update: 'Update') -> bool:
        for txt in self.coms:
            if (update.text!=None) and (update.text==txt or update.text.replace("/","")==txt):
                return True
        return False

class author_guids(Filter):
    """filter guid message by guids / فیلتر کردن گوید پیام با گوید ها"""
    def __init__(self, guids: list):
        self.guids = guids

    def __call__(self, update: 'Update') -> bool:
        for g in self.guids:
            if update.sender_id==g:
                return True
        return False

class chat_ids(Filter):
    """filter chat_id message by chat ids / فیلتر کردن چت آیدی پیام ارسال شده با چت آیدی ها"""
    def __init__(self, ids: list):
        self.ids = ids

    def __call__(self, update: 'Update') -> bool:
        for c in self.ids:
            if update.chat_id==c:
                return True
        return False

class has_metadata_type(Filter):
    def __init__(self,type) -> None:
        self.type = type
    def __call__(self, update: 'Update') -> bool:
        if update.meta_data_parts:
            for mata_data in update.meta_data_parts.data:
                if mata_data["type"].lower() == self.type.lower():
                    return True
        return False

class is_metadata_type(Filter):
    def __init__(self,type) -> None:
        self.type = type
    def __call__(self, update: 'Update') -> bool:
        if update.meta_data_parts and len(update.meta_data_parts.data) != 1:
            if update.meta_data_parts.data[0]["type"].lower() == self.type.lower():
                return True
        return False

class has_bold(Filter):
    """check for has bold text / چک وجود داشتن متن بولد"""
    def __call__(self, update: 'Update') -> bool:
        return has_metadata_type("bold")(update)

class has_italic(Filter):
    """check for has italic text / چک وجود داشتن متن ایتالیک"""
    def __call__(self, update: 'Update') -> bool:
        return has_metadata_type("italic")(update)

class has_underline(Filter):
    """check for has underline text / چک وجود داشتن متن آندرلایبن"""
    def __call__(self, update: 'Update') -> bool:
        return has_metadata_type("underline")(update)

class has_strike(Filter):
    """check for has strike text / چک وجود داشتن متن خط خورده"""
    def __call__(self, update: 'Update') -> bool:
        return has_metadata_type("strike")(update)

class has_mono(Filter):
    """check for has mono text / چک وجود داشتن متن کپی"""
    def __call__(self, update: 'Update') -> bool:
        return has_metadata_type("mono")(update)

class has_spoiler(Filter):
    """check for has spoiler text / چک وجود داشتن متن اسپویلر"""
    def __call__(self, update: 'Update') -> bool:
        return has_metadata_type("spoiler")(update)

class has_link(Filter):
    """check for has link text / چک وجود داشتن متن هایپر لینک"""
    def __call__(self, update: 'Update') -> bool:
        return has_metadata_type("link")(update)

class is_bold(Filter):
    """all text is bold / بولد بودن تمام متن"""
    def __call__(self, update: 'Update') -> bool:
        return is_metadata_type("bold")(update)

class is_italic(Filter):
    """all text is italic / ایتالیک بودن تمام متن"""
    def __call__(self, update: 'Update') -> bool:
        return is_metadata_type("italic")(update)

class is_underline(Filter):
    """all text is underline / آندرلاین بودن تمام متن"""
    def __call__(self, update: 'Update') -> bool:
        return is_metadata_type("underline")(update)

class is_strike(Filter):
    """all text is strike / خط خورده بودن تمام متن"""
    def __call__(self, update: 'Update') -> bool:
        return is_metadata_type("strike")(update)

class is_mono(Filter):
    """all text is mono / متن کپی بودن تمام متن"""
    def __call__(self, update: 'Update') -> bool:
        return is_metadata_type("mono")(update)

class is_spoiler(Filter):
    """all text is spoiler / اسپویلر بودن تمام متن"""
    def __call__(self, update: 'Update') -> bool:
        return is_metadata_type("spoiler")(update)

class is_link(Filter):
    """all text is link / هایپر لینک بودن تمام متن"""
    def __call__(self, update: 'Update') -> bool:
        return is_metadata_type("link")(update)


class in_text(Filter):
    """text in text message / وجود متن در متن آپدیت"""
    def __init__(self,text: str) -> None:
        self.text = text
    def __call__(self, update: 'Update') -> bool:
        if self.text in str(update.text):
            return True
        return False

class is_forward(Filter):
    """message is forward / پیام فوروارد شده"""
    def __call__(self, update: 'Update') -> bool:
        return update.is_fowrard

class is_reply(Filter):
    """message has reply / پیام دارای ریپلای"""
    def __call__(self, update: Update) -> bool:
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

class is_sticker(Filter):
    """filter by sticker / فیلتر استیکر"""
    def __call__(self, update: 'Update') -> bool:
        return update.is_sticker

class is_contact(Filter):
    """filter by contact / فیلتر مخاطب"""
    def __call__(self, update: 'Update') -> bool:
        return update.is_contact



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
    def __init__(self,filter):
        self.filter = filter
    def __call__(self, update: Update) -> bool:
        return not self.filter(update)