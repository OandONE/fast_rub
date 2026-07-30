from typing import TYPE_CHECKING, Literal, Any
from collections.abc import Callable
from pathlib import Path
import aiofiles
import asyncio
from .colors import cprint, Colors
import time
import re
from ..button import KeyPad
import inspect
import warnings

if TYPE_CHECKING:
    from ..network.network import Network

DATA_SUFFIXS = {
    "Image": ("png", "jpg", "gif", "jpeg", "webp", "svg", "ico"),
    "Video": ("mp4", "mkv", "mov", "avi", "webm", "m4v", "mpg", "mpeg"),
    "Music": ("mp3", "wav", "aac", "m4a", "ogg")
}

class Utils:
    @staticmethod
    def format_file(type_file: str | None = None) -> str | None:
        if type_file:
            for type_, pass_ in {
                "File": "",
                "Image": ".png",
                "Voice": ".mp3",
                "Music": ".mp3",
                "Gif": ".mp4",
                "Video": ".mp4"
            }.items():
                if type_ == type_file:
                    name_file = type_+pass_
                    return name_file
        return None
    
    @staticmethod
    def print_time(text: str, time_sleep: float = 0.07, color: str = Colors.WHITE) -> None:
        k = ""
        for ch in text:
            k += ch
            print(f"{color}{k}{Colors.RESET}", end="\r")
            time.sleep(time_sleep)
        cprint("",Colors.WHITE)
    
    @staticmethod
    def get_input(text_output: str) -> str:
        text = None
        while text is None or len(text) != 64:
            cprint("Write the valid ! Your text invalid.",Colors.RED)
            text = input(text_output)
        return text
    
    @staticmethod
    def calculate_upload_timeout(file_size_bytes: int, upload_speed_bps: int = 300_000) -> int:
        SAFETY_FACTOR = 1.5
        timeout_seconds = (file_size_bytes / upload_speed_bps) * SAFETY_FACTOR
        return max(int(timeout_seconds), 30)

    # Mata Data

    @staticmethod
    def data_format(
        data: dict,
        inline_keypad: list | KeyPad | None = None,
        keypad: list | KeyPad | None = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        metadata: list | None = None,
        meta_data: list | None = None
    ) -> dict:
        if isinstance(inline_keypad, KeyPad):
            inline_keypad = inline_keypad.build()
        if isinstance(keypad, KeyPad):
            keypad = keypad.build()
        if meta_data is None:
            meta_data = []
        if inline_keypad:
            data["inline_keypad"] = {"rows": inline_keypad}
        if keypad:
            data["chat_keypad"] = {
                "rows": keypad,
                "resize_keyboard": resize_keyboard,
                "on_time_keyboard": on_time_keyboard,
            }
            data["chat_keypad_type"] = "New"
        if metadata:
            for md in metadata:
                meta_data.append(md)
        if meta_data:
            data["metadata"] = {"meta_data_parts": meta_data}
        return data
    
    # Other

    @staticmethod
    async def d_file(
        file: str  | Path  | bytes,
        file_name: str,
        network: 'Network'
    ) -> dict[str, tuple[str, bytes | bytearray, str]]:
        if isinstance(file, (bytes, bytearray)):
            d_file = {"file": (file_name, file, "application/octet-stream")}
        else:
            try:
                async with aiofiles.open(file, "rb") as fi:
                    fil = await fi.read()
                    d_file = {"file": (file_name, fil , "application/octet-stream")}
            except:
                file_ = (await network.request(str(file),type_send="GET")).content
                d_file = {"file": (file_name, file_, "application/octet-stream")}
        return d_file # type: ignore
    
    @staticmethod
    def check_data(data: dict) -> bool:
        if data.get("status", "") == "OK":
            return True
        return False

    @staticmethod
    def prefer_first(value1: str | None = None, value2: str | None = None) -> str:
        return value1 if value1 else str(value2)

    @staticmethod
    def get_chat_id_type(chat_id: str) -> Literal['User', 'Group', 'Channel']:
        if chat_id.startswith("b"):
            return "User"
        elif chat_id.startswith("g"):
            return "Group"
        elif chat_id.startswith("c"):
            return "Channel"
        else:
            raise ValueError("chat id is not found")
    
    @staticmethod
    def format_url(urls: list) -> list:
        new_urls = []
        for url in urls:
            if not url.endswith("/"):
                new_urls.append(url + "/")
            else:
                new_urls.append(url)
        return new_urls
    
    @staticmethod
    def suffix_file(name_file: str) -> str:
        end = name_file.split(".")[-1]
        return end
    
    @staticmethod
    def type_file(name_file: str) -> Literal["File", "Image", "Voice", "Music", "Gif" , "Video"]:
        suffix = Utils.suffix_file(name_file=name_file)
        for tp, suf in DATA_SUFFIXS.items():
            if suffix in suf:
                return tp # pyright: ignore[reportReturnType]
        return "File"

    @staticmethod
    def check_id(id: str) -> bool:
        st = id.startswith("b") or id.startswith("u") or id.startswith("g")
        if st:
            if len(id) == 32:
                for chr in id:
                    if (chr.isascii() and (chr.isalpha() and chr.isascii() or chr.isdigit())):
                        return True
        return False

    @staticmethod
    def check_id_raise(id: str):
        if not Utils.check_id(id=id):
            from ..types.errors import InvalidID
            raise InvalidID('Invalid Id. The ID must be 32 characters long and must also start with one of the letters "b", "u", or "g".')
    
    @staticmethod
    def check_message_id(id: str) -> bool:
        return id.isdigit() and len(id) == 19

    @staticmethod
    def check_message_id_raise(id: str):
        if not Utils.check_message_id(id=id):
            from ..types.errors import InvalidID
            raise InvalidID('Invalid Message Id. The Message Id be 19 characters long and must also is number: 1234567890123456789')
    
    @staticmethod
    def clean_dict(data: dict) -> dict:
        if not isinstance(data, dict):
            return data
        result = {}
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, list) and len(value) == 0:
                continue
            if isinstance(value, dict) and len(value) == 0:
                continue
            if isinstance(value, dict):
                cleaned = Utils.clean_dict(value)
                if cleaned:
                    result[key] = cleaned
            else:
                result[key] = value
        return result

    @staticmethod
    def trim_text(text: str) -> str:
        """حذف فاصله‌های اضافی از اول، آخر هر خط، و خط‌های خالی انتهای متن"""
        if not text:
            return text
        text = text.lstrip()
        text = '\n'.join(line.rstrip() for line in text.splitlines())
        text = re.sub(r'(\n\s*)+$', '', text)
        return text
    
    trim_trailing_newlines = trim_text

    @staticmethod
    async def when(
        condition: Callable[[], bool],
        action: Callable[[], Any] | None = None,
        sleep: float = 1.0,
        timeout: float | None = None,
        error_message: str | None = None,
    ) -> bool:
        """منتظر می‌ماند تا یک شرط برقرار شود، سپس action را اجرا می‌کند."""
        start = time.time()
        
        while True:
            if timeout and time.time() - start > timeout:
                if error_message:
                    print(f"⏰ Timeout: {error_message}")
                return False
            try:
                result = condition()
                if asyncio.iscoroutine(result):
                    result = await result
                
                if result:
                    if action:
                        act = action()
                        if asyncio.iscoroutine(act):
                            await act
                    return True
            except Exception as e:
                pass
            
            await asyncio.sleep(sleep)
    
    @staticmethod
    async def run_handler(
        handler: Callable,
        *args,
        **values
    ):
        if inspect.iscoroutinefunction(handler):
            return await handler(*args, **values)
        else:
            return handler(*args, **values)
    
    @staticmethod
    def deprecated_property(old_name: str, new_name: str):
        """هشدار منسوخ شدن پراپرتی"""
        warnings.warn(
            f"`{old_name}` is deprecated and will be removed in Fast Rub 7.0. "
            f"Use `{new_name}` instead.",
            DeprecationWarning,
            stacklevel=2
        )
