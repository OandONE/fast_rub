from typing import Callable, Literal
from dataclasses import dataclass


@dataclass
class EntryFormConfig:
    on_start: Callable | None = None
    on_finish: Callable | None = None
    on_cancel: Callable | None = None
    on_error: Callable | None = None
    on_timeout: Callable | None = None
    conflict: Literal["cancel", "queue", "parallel"] = "cancel"
    timeout: int = 300
    allow_back: bool = False
    allow_skip: bool = False
