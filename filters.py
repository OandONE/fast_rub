from typing import TYPE_CHECKING
import re
if TYPE_CHECKING:
    from .Client import Update

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
    def __init__(self,name_file):
        self.name_file = name_file
    def __call__(self, update:'Update'):
        return True if update.file_name==self.name_file else False

class size_file(Filter):
    """filter by name file / فیلتر با اسم فایل"""
    def __init__(self,size):
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

class regex(Filter):
    """filter text message by regex pattern / فیلتر متن پیام با regex"""
    def __init__(self, pattern: str, flags=0):
        self.pattern = re.compile(pattern, flags)
    def __call__(self, update: 'Update') -> bool:
        if not hasattr(update, "text") or update.text is None:
            return False
        return bool(self.pattern.search(update.text))

class commands(Filter):
    """filter text message by commands / فیلتر کردن متن پیام با دستورات"""
    def __init__(self, coms: list):
        self.coms = coms

    def __call__(self, update: 'Update') -> bool:
        for txt in self.coms:
            if update.text==txt or update.text.replace("/","")==txt:
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
