from typing import Callable
from .fields import Text, Number, Choice


class DataForm:
    on_start: Callable | None = None
    on_finish: Callable | None = None
    on_cancel: Callable | None = None
    on_error: Callable | None = None
    on_timeout: Callable | None = None
    
    allow_back: bool = False
    allow_skip: bool = False
    skip_if: Callable | None = None
    depends_on: dict | None = None
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._fields: dict[str, object] = {}
        cls._field_order: list[str] = []
        for name, value in cls.__dict__.items():
            if isinstance(value, (Text, Number, Choice)):
                cls._fields[name] = value
                cls._field_order.append(name)
    
    @classmethod
    def get_fields(cls) -> dict:
        return cls._fields
    
    @classmethod
    def get_field_order(cls) -> list[str]:
        return cls._field_order
