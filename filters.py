from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Client import Update

class Filter:
    def __call__(self, update: 'Update') -> bool:
        raise NotImplementedError

class text(Filter):
    def __init__(self, pattern: str):
        self.pattern = pattern

    def __call__(self, update: 'Update') -> bool:
        return update.text == self.pattern

class sender_id(Filter):
    def __init__(self, user_id: int):
        self.user_id = user_id

    def __call__(self, update: 'Update') -> bool:
        return update.message.get('sender_id') == self.user_id

class is_user(Filter):
    def __call__(self, update: 'Update') -> bool:
        return not update.message.get('is_bot', False)

# فیلترهای ترکیبی
class and_filter(Filter):
    def __init__(self, *filters):
        self.filters = filters

    def __call__(self, update: 'Update') -> bool:
        return all(f(update) for f in self.filters)

class or_filter(Filter):
    def __init__(self, *filters):
        self.filters = filters

    def __call__(self, update: 'Update') -> bool:
        return any(f(update) for f in self.filters)