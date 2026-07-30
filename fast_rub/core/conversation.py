from collections.abc import Callable
from ..types import Update
from .client import Client
from ..utils.filters import Filter
from ..utils import _run_filter

import asyncio

class Conversation:
    END = "__END__"
    
    def __init__(
        self,
        name: str = "default",
        timeout: float = 300.0
    ):
        self.name = name
        self._states: dict[str, Callable] = {}
        self._entry_handler: Callable | None = None
        self._entry_filters = None
        self._user_states: dict[str, str] = {}
        self._user_data: dict[str, dict] = {}
        self.timeout = timeout
        self._user_timers: dict[str, asyncio.Task] = {}
        self.client = None
        self._form_config: dict = {}
    
    def _set_timeout(self, chat_id: str):
        if chat_id in self._user_timers:
            self._user_timers[chat_id].cancel()
        
        async def _timeout():
            await asyncio.sleep(self.timeout)
            if chat_id in self._user_states:
                self._cleanup(chat_id)
        
        self._user_timers[chat_id] = asyncio.create_task(_timeout())
    
    def entry(
        self,
        commands: list | None = None,
        text: str | None = None,
        filters: Filter | None = None
    ):
        """دکوراتور برای نقطه ورود مکالمه."""
        def decorator(func):
            self._entry_handler = func
            self._entry_filters = {
                "commands": commands,
                "text": text,
                "filters": filters
            }
            return func
        return decorator
    
    async def _is_entry(self, update: Update) -> bool:
        if not self._entry_filters:
            return False
        commands: list[str] | None = self._entry_filters.get("commands")
        text = self._entry_filters.get("text")
        filters: Filter | None = self._entry_filters.get("filters")

        run_filter = await _run_filter(filters, update)
        if filters and not run_filter:
            return False
        
        if commands is not None and update.text:
            for cmd in commands:
                if update.text == cmd or update.text == f"/{cmd}":
                    return True
        
        if text is not None and update.text == text:
            return True
        
        if filters is not None:
            return True
        
        return False
    
    def state(
        self,
        state_name: str
    ):
        """دکوراتور برای یک حالت (مرحله) از مکالمه"""
        def decorator(func: Callable):
            self._states[state_name] = func
            return func
        return decorator
    
    async def handle(self, update: Update, client: Client) -> bool:
        chat_id = update.chat_id
        self.client = client
        
        if chat_id not in self._user_states:
            is_entry = await self._is_entry(update)
            if is_entry:
                self._user_states[chat_id] = "__ENTRY__"
                self._user_data[chat_id] = {}
                self._set_timeout(chat_id)
            else:
                return False
        
        current_state = self._user_states.get(chat_id)

        if current_state == "__ENTRY__":
            if self._entry_handler:
                try:
                    next_state = self._entry_handler(update, self._user_data.get(chat_id, {}))
                    if asyncio.iscoroutine(next_state):
                        next_state = await next_state
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self._cleanup(chat_id)
                    return False
                
                if next_state == Conversation.END:
                    self._cleanup(chat_id)
                    return False
                self._user_states[chat_id] = next_state
                self._set_timeout(chat_id)
                return True
        
        if current_state in self._states:
            handler = self._states[current_state]
            try:
                result = handler(update, self._user_data.get(chat_id, {}))
                if asyncio.iscoroutine(result):
                    next_state = await result
                else:
                    next_state = result
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._cleanup(chat_id)
                return False
            
            if next_state == Conversation.END:
                self._cleanup(chat_id)
                return False
            self._user_states[chat_id] = next_state
            self._set_timeout(chat_id)
            return True
        
        return False
    
    def _find_next_visible_field(self, data: dict, start_idx: int) -> int | None:
        """پیدا کردن ایندکس اولین فیلدی که باید پرسیده بشه"""
        config = self._form_config
        idx = start_idx
        
        while idx < len(config["fields"]):
            f_name, f_config = config["fields"][idx]
            
            if hasattr(f_config, 'hide_if') and f_config.hide_if:
                try:
                    if f_config.hide_if(data):
                        value = f_config.default if hasattr(f_config, 'default') and f_config.default is not None else ""
                        data[f_name] = value
                        idx += 1
                        continue
                except Exception:
                    pass
            
            if hasattr(f_config, 'default_if') and f_config.default_if:
                try:
                    if f_config.default_if(data):
                        value = f_config.default if hasattr(f_config, 'default') and f_config.default is not None else ""
                        data[f_name] = value
                        idx += 1
                        continue
                except Exception:
                    pass
            
            if hasattr(f_config, 'skip_if') and f_config.skip_if:
                try:
                    if f_config.skip_if(data):
                        idx += 1
                        continue
                except Exception:
                    pass
            
            return idx
        
        return None
    
        
    def entry_form(
        self,
        form_class: type,
        commands: list[str] | None = None,
        text: str | None = None,
        filters: Filter | None = None,
        on_start: Callable | None = None,
        on_finish: Callable | None = None,
        on_cancel: Callable | None = None,
        on_error: Callable | None = None,
        on_timeout: Callable | None = None,
        timeout: int = 120,
        allow_back: bool = False,
        allow_skip: bool = False,
    ):
        """
        دکوراتور برای ساخت یه فرم خودکار از روی DataForm.
        
        مثال:
            @register.entry_form(UserInfo, on_finish=lambda data: print(data))
            async def done(msg, data):
                await msg.reply(f"ثبت شد: {data}")
        """
        def decorator(final_handler: Callable):
            form = form_class()
            fields = list(form.get_fields().items())
            
            self._form_config = {
                "form_class": form_class,
                "fields": fields,
                "on_start": on_start,
                "on_finish": on_finish,
                "on_cancel": on_cancel,
                "on_error": on_error,
                "on_timeout": on_timeout,
                "timeout": timeout,
                "allow_back": allow_back,
                "allow_skip": allow_skip,
                "final_handler": final_handler,
            }
            
            self._entry_filters = {
                "commands": commands,
                "text": text,
                "filters": filters
            }

            async def form_entry(update: Update, data: dict):
                """نقطهٔ ورود فرم — اولین فیلد رو می‌پرسه"""
                config = self._form_config
                
                if config["on_start"]:
                    res = config["on_start"]()
                    if asyncio.iscoroutine(res):
                        await res
                
                start_idx = self._find_next_visible_field(data, 0)
                
                if start_idx is None:
                    if config["on_finish"]:
                        res = config["on_finish"](data)
                        if asyncio.iscoroutine(res):
                            await res
                    await config["final_handler"](update, data)
                    return Conversation.END
                
                field_name, field_config = config["fields"][start_idx]
                prompt = field_config.prompt
                keypad = self._build_field_keypad(field_config)
                
                await update.reply(prompt, keypad=keypad, on_time_keyboard=True)
                
                return f"__form_{field_name}"
            
            self._entry_handler = form_entry
            
            for i, (field_name, field_config) in enumerate(fields):
                is_last = (i == len(fields) - 1)
                next_field_name = fields[i + 1][0] if not is_last else None
                
                def make_field_handler(idx: int, f_name: str, f_config, next_f_name: str | None, last: bool):
                    async def field_handler(update: Update, data: dict):
                        nonlocal next_f_name
                        config = self._form_config
                        text = update.text

                        if f_config.cancel_if and text:
                            try:
                                should_cancel = f_config.cancel_if(text)
                                if should_cancel:
                                    if config["on_cancel"]:
                                        res = config["on_cancel"]()
                                        if asyncio.iscoroutine(res):
                                            await res
                                    return Conversation.END
                            except Exception:
                                pass
                        
                        if f_config.back_if and text:
                            try:
                                should_back = f_config.back_if(text)
                                if should_back:
                                    prev_idx = idx - 1
                                    if prev_idx >= 0:
                                        prev_name, prev_config = config["fields"][prev_idx]
                                        prompt = prev_config.prompt
                                        keypad = self._build_field_keypad(prev_config)
                                        await update.reply(prompt, keypad=keypad)
                                        return f"__form_{prev_name}"
                                    prompt = f_config.prompt
                                    keypad = self._build_field_keypad(f_config)
                                    await update.reply(prompt, keypad=keypad)
                                    return f"__form_{f_name}"
                            except Exception:
                                pass

                        if text == "/cancel":
                            if config["on_cancel"]:
                                res = config["on_cancel"]()
                                if asyncio.iscoroutine(res):
                                    await res
                            return Conversation.END
                        
                        if text == "/back" and config["allow_back"]:
                            prev_idx = idx - 1
                            if prev_idx >= 0:
                                prev_name, prev_config = config["fields"][prev_idx]
                                prompt = prev_config.prompt
                                keypad = self._build_field_keypad(prev_config)
                                await update.reply(prompt, keypad=keypad, on_time_keyboard=True)
                                return f"__form_{prev_name}"
                            prompt = f_config.prompt
                            keypad = self._build_field_keypad(f_config)
                            await update.reply(prompt, keypad=keypad, on_time_keyboard=True)
                            return f"__form_{f_name}"
                        
                        if text == "/skip" and config["allow_skip"]:
                            if last:
                                if config["on_finish"]:
                                    res = config["on_finish"](data)
                                    if asyncio.iscoroutine(res):
                                        await res
                                await config["final_handler"](update, data)
                                return Conversation.END
                            next_f_config = config["fields"][idx + 1][1]
                            prompt = next_f_config.prompt
                            keypad = self._build_field_keypad(next_f_config)
                            await update.reply(prompt, keypad=keypad, on_time_keyboard=True)
                            return f"__form_{next_f_name}"
                        
                        if not text:
                            return f"__form_{f_name}"
                        
                        if hasattr(f_config, 'skip_if') and f_config.skip_if:
                            try:
                                should_skip = f_config.skip_if(data)
                                if should_skip:
                                    if last:
                                        if config["on_finish"]:
                                            res = config["on_finish"](data)
                                            if asyncio.iscoroutine(res):
                                                await res
                                        await config["final_handler"](update, data)
                                        return Conversation.END
                                    next_f_config = config["fields"][idx + 1][1]
                                    prompt = next_f_config.prompt
                                    keypad = self._build_field_keypad(next_f_config)
                                    await update.reply(prompt, keypad=keypad)
                                    return f"__form_{next_f_name}"
                            except Exception:
                                pass
                            
                        if hasattr(f_config, 'hide_if') and f_config.hide_if:
                            try:
                                should_hide = f_config.hide_if(data)
                                if should_hide:
                                    value = f_config.default if hasattr(f_config, 'default') and f_config.default is not None else ""
                                    data[f_name] = value
                                    if last:
                                        if config["on_finish"]:
                                            res = config["on_finish"](data)
                                            if asyncio.iscoroutine(res):
                                                await res
                                        await config["final_handler"](update, data)
                                        return Conversation.END
                                    next_f_config = config["fields"][idx + 1][1]
                                    prompt = next_f_config.prompt
                                    keypad = self._build_field_keypad(next_f_config)
                                    await update.reply(prompt, keypad=keypad)
                                    return f"__form_{next_f_name}"
                            except Exception:
                                pass

                        if hasattr(f_config, 'default_if') and f_config.default_if:
                            try:
                                should_default = f_config.default_if(data)
                                if should_default:
                                    value = f_config.default if hasattr(f_config, 'default') and f_config.default is not None else ""
                                    data[f_name] = value
                                    if last:
                                        if config["on_finish"]:
                                            res = config["on_finish"](data)
                                            if asyncio.iscoroutine(res):
                                                await res
                                        await config["final_handler"](update, data)
                                        return Conversation.END
                                    next_f_config = config["fields"][idx + 1][1]
                                    prompt = next_f_config.prompt
                                    keypad = self._build_field_keypad(next_f_config)
                                    await update.reply(prompt, keypad=keypad)
                                    return f"__form_{next_f_name}"
                            except Exception:
                                pass
                        
                        validated = self._validate_field(f_config, text)
                        if validated is False:
                            err_msg = getattr(f_config, 'invalid_answer', '❌ ورودی نامعتبر است')
                            await update.reply(err_msg)
                            return f"__form_{f_name}"
                        
                        if hasattr(f_config, 'cancel_if') and f_config.cancel_if:
                            try:
                                should_cancel = f_config.cancel_if(text)
                                if should_cancel:
                                    if config["on_cancel"]:
                                        res = config["on_cancel"]()
                                        if asyncio.iscoroutine(res):
                                            await res
                                    return Conversation.END
                            except Exception:
                                pass

                        if hasattr(f_config, 'back_if') and f_config.back_if:
                            try:
                                should_back = f_config.back_if(text)
                                if should_back:
                                    prev_idx = idx - 1
                                    if prev_idx >= 0:
                                        prev_name, prev_config = config["fields"][prev_idx]
                                        prompt = prev_config.prompt
                                        keypad = self._build_field_keypad(prev_config)
                                        await update.reply(prompt, keypad=keypad)
                                        return f"__form_{prev_name}"
                            except Exception:
                                pass

                        value = validated
                        if hasattr(f_config, 'transform_if') and f_config.transform_if:
                            try:
                                if f_config.transform_if(value):
                                    if hasattr(f_config, 'transform') and f_config.transform:
                                        value = f_config.transform(value)
                            except Exception:
                                pass
                        elif hasattr(f_config, 'transform') and f_config.transform:
                            try:
                                value = f_config.transform(value)
                            except Exception:
                                value = validated

                        if hasattr(f_config, 'repeat_if') and f_config.repeat_if:
                            try:
                                should_repeat = f_config.repeat_if(value)
                                if should_repeat:
                                    err = getattr(f_config, 'invalid_answer', '❌ دوباره وارد کن')
                                    await update.reply(err)
                                    return f"__form_{f_name}"
                            except Exception:
                                pass
                            
                        data[f_name] = value
                        
                        if hasattr(f_config, 'func') and f_config.func:
                            try:
                                res = f_config.func()
                                if asyncio.iscoroutine(res):
                                    await res
                            except Exception:
                                pass
                        
                        if last:
                            if config["on_finish"]:
                                try:
                                    res = config["on_finish"](data)
                                    if asyncio.iscoroutine(res):
                                        await res
                                except Exception:
                                    pass
                            await config["final_handler"](update, data)
                            return Conversation.END
                        
                        next_idx = self._find_next_visible_field(data, idx + 1)

                        if next_idx is None:
                            if config["on_finish"]:
                                try:
                                    res = config["on_finish"](data)
                                    if asyncio.iscoroutine(res):
                                        await res
                                except Exception:
                                    pass
                            await config["final_handler"](update, data)
                            return Conversation.END

                        next_f_name, next_f_config = config["fields"][next_idx]
                        prompt = next_f_config.prompt
                        keypad = self._build_field_keypad(next_f_config)
                        await update.reply(prompt, keypad=keypad, on_time_keyboard=True)
                        return f"__form_{next_f_name}"
                    
                    return field_handler
                
                handler = make_field_handler(
                    idx=i,
                    f_name=field_name,
                    f_config=field_config,
                    next_f_name=next_field_name,
                    last=is_last
                )
                state_name = f"__form_{field_name}"
                self._states[state_name] = handler
            
            return final_handler
        
        return decorator


    def _build_field_keypad(self, field_config) -> list | None:
        """ساختن کیبورد برای Number و Choice"""
        from ..button import KeyPad
        
        if hasattr(field_config, 'keypad') and field_config.keypad:
            if field_config.min is not None and field_config.max is not None:
                numbers = list(range(field_config.min, field_config.max + 1))
                if getattr(field_config, 'sort_by', 'asc') == "desc":
                    numbers.reverse()
                
                keypad = KeyPad()
                row = []
                max_row = getattr(field_config, 'max_btn_row', 4)
                for num in numbers:
                    row.append(keypad.simple(str(num), str(num)))
                    if len(row) >= max_row:
                        keypad.append(*row)
                        row = []
                if row:
                    keypad.append(*row)
                return keypad.build()
        
        if hasattr(field_config, 'options'):
            options = field_config.options
            if callable(options):
                options = options()
            
            if not isinstance(options, list):
                return None

            keypad = KeyPad()
            row = []
            max_row = getattr(field_config, 'max_btn_row', 2)
            for opt in options:
                row.append(keypad.simple(opt, opt))
                if len(row) >= max_row:
                    keypad.append(*row)
                    row = []
            if row:
                keypad.append(*row)
            return keypad.build()
        
        return None


    def _validate_field(self, field_config, value: str):
        """اعتبارسنجی فیلد"""
        from .forms.fields import Text, Number, Choice
        
        if hasattr(field_config, 'validator') and field_config.validator:
            result = field_config.validator(value)
            if asyncio.iscoroutine(result):
                pass
            if not result:
                return False
        
        if isinstance(field_config, Text):
            if field_config.min_len and len(value) < field_config.min_len:
                return False
            if field_config.max_len and len(value) > field_config.max_len:
                return False
            if field_config.email and "@" not in value:
                return False
            if field_config.valid_inputs and value not in field_config.valid_inputs:
                return False
            return value
        
        elif isinstance(field_config, Number):
            try:
                num = int(value)
            except ValueError:
                return False
            if field_config.min is not None and num < field_config.min:
                return False
            if field_config.max is not None and num > field_config.max:
                return False
            return num
        
        elif isinstance(field_config, Choice):
            options = field_config.options
            if callable(options):
                options = options()
            if value in options:
                return value
            return False
        
        return value

    def _cleanup(self, chat_id: str):
        """پاکسازی state کاربر بعد از تموم شدن مکالمه"""
        self._user_states.pop(chat_id, None)
        self._user_data.pop(chat_id, None)


class ConversationManager:
    """مدیریت چندین مکالمه همزمان"""
    def __init__(self):
        self._conversations: dict[str, Conversation] = {}
    
    def add(
        self,
        conversation: Conversation
    ):
        self._conversations[conversation.name] = conversation
    
    def remove(
        self,
        name: str
    ):
        self._conversations.pop(name, None)
    
    async def handle(
        self,
        update: Update,
        client: Client
    ) -> bool:
        """همه مکالمات رو چک می‌کنه، اولویت با اولین مکالمه فعال"""
        chat_id = update.chat_id
        for conv in self._conversations.values():
            if chat_id in conv._user_states:
                return await conv.handle(update, client)
        for conv in self._conversations.values():
            if await conv._is_entry(update):
                return await conv.handle(update, client)
        return False
