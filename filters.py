from typing import TYPE_CHECKING
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
        return not update.message.get('is_bot', False)

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
