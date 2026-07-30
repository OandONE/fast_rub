import asyncio
from typing import Any, Callable, TYPE_CHECKING

from .data_form import DataForm
from .fields import Text, Number, Choice
from .config import EntryFormConfig
from ...button import KeyPad

if TYPE_CHECKING:
    from ...types import Update

class FormManager:
    def __init__(
        self,
        form: DataForm,
        update: "Update",
        config: EntryFormConfig
    ):
        self.form = form
        self.update = update
        self.config = config
        self.data: dict[str, Any] = {}
        self.current_index = 0
        self.fields = list(form.get_fields().items())
        self.wait_manager = update._client.wait_manager
        self.chat_id = update.chat_id
        self._retry_counts: dict[str, int] = {}
        self._running = False
        self._current_callback: Callable | None = None
    
    async def start(
        self,
        callback: Callable
    ):
        """شروع فرم. callback وقتی همه داده‌ها جمع شد صدا زده می‌شه"""
        self._current_callback = callback
        self._running = True
        
        await self._call_callback(self.config.on_start)
        await self._ask_next_field()
    
    async def handle_update(
        self,
        update: "Update"
    ) -> bool:
        """پردازش آپدیت جدید. برگشت True یعنی فرم هنوز ادامه داره"""
        if not self._running:
            return False
        
        if update.chat_id != self.chat_id:
            return False
        
        text = update.text

        if not text:
            return True
        
        if text == "/cancel":
            await self._cancel()
            return False
        
        if text == "/back" and self.config.allow_back and self.current_index > 0:
            self.current_index -= 1
            self._retry_counts[self.fields[self.current_index][0]] = 0
            await self._ask_next_field()
            return True
        
        if text == "/skip" and self.config.allow_skip:
            self.current_index += 1
            await self._ask_next_field()
            return True
        
        field_name, field_config = self.fields[self.current_index]
        
        if not await self._validate(field_config, text):
            self._retry_counts[field_name] = self._retry_counts.get(field_name, 0) + 1
            if self._retry_counts[field_name] <= field_config.retry:
                await self._ask_next_field()
                return True
            await self._cancel()
            return False
        
        self._retry_counts[field_name] = 0
        
        value = text
        if field_config.transform:
            value = field_config.transform(value)
        
        self.data[field_name] = value
        
        await self._call_func(field_config.func, field_config, value, field_name)
        
        self.current_index += 1
        
        if self.current_index >= len(self.fields):
            await self._call_callback(self.config.on_finish, self.data)
            if self._current_callback:
                await self._current_callback(self.update, self.data)
            self._running = False
            return False
        
        await self._ask_next_field()
        return True
    
    async def _ask_next_field(self):
        """پرسیدن فیلد بعدی"""
        if self.current_index >= len(self.fields):
            return
        
        field_name, field_config = self.fields[self.current_index]
        
        if hasattr(field_config, 'skip_if') and field_config.skip_if:
            try:
                should_skip = field_config.skip_if(self.data)
                if should_skip:
                    self.current_index += 1
                    await self._ask_next_field()
                    return
            except Exception:
                pass
        
        if hasattr(field_config, 'hide_if') and field_config.hide_if:
            try:
                should_hide = field_config.hide_if(self.data)
                if should_hide:
                    value = field_config.default if hasattr(field_config, 'default') and field_config.default is not None else ""
                    self.data[field_name] = value
                    self.current_index += 1
                    await self._ask_next_field()
                    return
            except Exception:
                pass
        
        if hasattr(field_config, 'default_if') and field_config.default_if:
            try:
                should_default = field_config.default_if(self.data)
                if should_default:
                    value = field_config.default if hasattr(field_config, 'default') and field_config.default is not None else ""
                    self.data[field_name] = value
                    self.current_index += 1
                    await self._ask_next_field()
                    return
            except Exception:
                pass
        
        await self._call_callback(field_config.pre_func)
        
        prompt = field_config.prompt
        keypad = None
        
        if isinstance(field_config, Number) and field_config.keypad:
            keypad = self._build_number_keypad(field_config)
        elif isinstance(field_config, Choice):
            options = field_config.options
            if callable(options):
                options = options()
            keypad = self._build_choice_keypad(options, field_config.max_btn_row)
        
        kwargs = {}
        if keypad:
            kwargs["on_time_keyboard"] = True
        
        await self.update.reply(prompt, keypad=keypad, **kwargs)

    def _should_skip(
        self,
        field_name: str
    ) -> bool:
        field_config = self.fields[self.current_index][1]
        
        if hasattr(field_config, 'skip_if') and field_config.skip_if:
            if field_config.skip_if(self.data):
                return True
        
        if hasattr(field_config, 'depends_on') and field_config.depends_on:
            for dep_field, expected in field_config.depends_on.items():
                if dep_field not in self.data:
                    return True
                actual = self.data[dep_field]
                if callable(expected):
                    if not expected(actual):
                        return True
                elif actual != expected:
                    return True
        
        return False
    
    async def _validate(
        self,
        field_config,
        value: str
    ) -> bool:
        if field_config.validator:
            result = field_config.validator(value)
            if asyncio.iscoroutine(result):
                result = await result
            if not result:
                await self._send_error(field_config)
                return False
        
        if isinstance(field_config, Text):
            if field_config.min_len and len(value) < field_config.min_len:
                await self._send_error(field_config)
                return False
            if field_config.max_len and len(value) > field_config.max_len:
                await self._send_error(field_config)
                return False
            if field_config.email and "@" not in value:
                await self._send_error(field_config)
                return False
            if field_config.valid_inputs and value not in field_config.valid_inputs:
                await self._send_error(field_config)
                return False
            return True
        
        elif isinstance(field_config, Number):
            try:
                num = int(value)
            except ValueError:
                await self._send_error(field_config)
                return False
            if field_config.min is not None and num < field_config.min:
                await self._send_error(field_config)
                return False
            if field_config.max is not None and num > field_config.max:
                await self._send_error(field_config)
                return False
            return True
        
        elif isinstance(field_config, Choice):
            selected = value.split(",")[:field_config.max_select]
            options = field_config.options
            if callable(options):
                options = options()
            if all(s in options for s in selected):
                return True
            await self._send_error(field_config)
            return False
        
        return True
    
    async def _send_error(
        self,
        field_config
    ):
        if hasattr(field_config, 'invalid_answer'):
            await self.update.reply(field_config.invalid_answer)
    
    def _build_number_keypad(
        self,
        field_config: Number
    ) -> list | None:
        if field_config.min is None or field_config.max is None:
            return None
        
        numbers = list(range(field_config.min, field_config.max + 1))
        
        if field_config.sort_by == "desc":
            numbers.reverse()
        
        keypad = KeyPad()
        row = []
        for num in numbers:
            row.append(keypad.simple(str(num), str(num)))
            if len(row) >= field_config.max_btn_row:
                keypad.append(*row)
                row = []
        if row:
            keypad.append(*row)
        
        return keypad.build()
    
    def _build_choice_keypad(
        self,
        options: list[str],
        max_btn_row: int
    ) -> list | None:
        keypad = KeyPad()
        row = []
        for opt in options:
            row.append(keypad.simple(opt, opt))
            if len(row) >= max_btn_row:
                keypad.append(*row)
                row = []
        if row:
            keypad.append(*row)
        
        return keypad.build()
    
    async def _call_func(
        self,
        func: Callable | None,
        field_config,
        value: Any,
        field_name: str
    ):
        if not func:
            return
        
        args = []
        kwargs = {}
        
        if hasattr(field_config, 'list_args_func') and field_config.list_args_func:
            for arg_name in field_config.list_args_func:
                args.append(self.data.get(arg_name, arg_name))
        
        if hasattr(field_config, 'dict_args_func') and field_config.dict_args_func:
            for key, val in field_config.dict_args_func.items():
                kwargs[key] = val
        
        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                await result
        except Exception:
            pass
    
    async def _call_callback(
        self,
        callback: Callable | None,
        *args
    ):
        if not callback:
            return
        try:
            result = callback(*args)
            if asyncio.iscoroutine(result):
                await result
        except Exception:
            pass
    
    async def _cancel(self):
        self._running = False
        await self._call_callback(self.config.on_cancel or self.form.on_cancel)
