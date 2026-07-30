from typing import Any, Callable


class Text:
    def __init__(
        self,
        prompt: str,
        min_len: int = 0,
        max_len: int = 4096,
        email: bool = False,
        valid_inputs: list[str] | None = None,
        invalid_answer: str = "ورودی نامعتبر است",
        func: Callable | None = None,
        list_args_func: list[str] | None = None,
        dict_args_func: dict[str, Any] | None = None,
        pre_func: Callable | None = None,
        transform: Callable | None = None,
        validator: Callable | None = None,
        retry: int = 0,
        timeout: int = 120,
        default: Any = None,
        hide_input: bool = False,
        skip_if: Callable | None = None,
        cancel_if: Callable | None = None,
        back_if: Callable | None = None,
        hide_if: Callable | None = None,
        default_if: Callable | None = None,
        repeat_if: Callable | None = None,
        transform_if: Callable | None = None,
    ):
        self.prompt = prompt
        self.min_len = min_len
        self.max_len = max_len
        self.email = email
        self.valid_inputs = valid_inputs
        self.invalid_answer = invalid_answer
        self.func = func
        self.list_args_func = list_args_func
        self.dict_args_func = dict_args_func
        self.pre_func = pre_func
        self.transform = transform
        self.validator = validator
        self.retry = retry
        self.timeout = timeout
        self.default = default
        self.hide_input = hide_input
        self.skip_if = skip_if
        self.cancel_if = cancel_if
        self.back_if = back_if
        self.hide_if = hide_if
        self.default_if = default_if
        self.repeat_if = repeat_if
        self.transform_if = transform_if


class Number:
    def __init__(
        self,
        prompt: str,
        min: int | None = None,
        max: int | None = None,
        keypad: bool = True,
        max_btn_row: int = 4,
        sort_by: str = "asc",
        func: Callable | None = None,
        list_args_func: list[str] | None = None,
        dict_args_func: dict[str, Any] | None = None,
        pre_func: Callable | None = None,
        transform: Callable | None = None,
        validator: Callable | None = None,
        retry: int = 0,
        timeout: int = 120,
        default: Any = None,
        skip_if: Callable | None = None,
        cancel_if: Callable | None = None,
        back_if: Callable | None = None,
        hide_if: Callable | None = None,
        default_if: Callable | None = None,
        repeat_if: Callable | None = None,
        transform_if: Callable | None = None,
    ):
        self.prompt = prompt
        self.min = min
        self.max = max
        self.keypad = keypad
        self.max_btn_row = max_btn_row
        self.sort_by = sort_by
        self.func = func
        self.list_args_func = list_args_func
        self.dict_args_func = dict_args_func
        self.pre_func = pre_func
        self.transform = transform
        self.validator = validator
        self.retry = retry
        self.timeout = timeout
        self.default = default
        self.skip_if = skip_if
        self.cancel_if = cancel_if
        self.back_if = back_if
        self.hide_if = hide_if
        self.default_if = default_if
        self.repeat_if = repeat_if
        self.transform_if = transform_if


class Choice:
    def __init__(
        self,
        prompt: str,
        options: list[str] | Callable,
        max_select: int = 1,
        max_btn_row: int = 2,
        func: Callable | None = None,
        list_args_func: list[str] | None = None,
        dict_args_func: dict[str, Any] | None = None,
        pre_func: Callable | None = None,
        transform: Callable | None = None,
        validator: Callable | None = None,
        retry: int = 0,
        timeout: int = 120,
        default: Any = None,
        skip_if: Callable | None = None,
        cancel_if: Callable | None = None,
        back_if: Callable | None = None,
        hide_if: Callable | None = None,
        default_if: Callable | None = None,
        repeat_if: Callable | None = None,
        transform_if: Callable | None = None,
    ):
        self.prompt = prompt
        self.options = options
        self.max_select = max_select
        self.max_btn_row = max_btn_row
        self.func = func
        self.list_args_func = list_args_func
        self.dict_args_func = dict_args_func
        self.pre_func = pre_func
        self.transform = transform
        self.validator = validator
        self.retry = retry
        self.timeout = timeout
        self.default = default
        self.skip_if = skip_if
        self.cancel_if = cancel_if
        self.back_if = back_if
        self.hide_if = hide_if
        self.default_if = default_if
        self.repeat_if = repeat_if
        self.transform_if = transform_if