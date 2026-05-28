from typing import Dict, Tuple, Optional, Union, TYPE_CHECKING, Literal
from pathlib import Path
import aiofiles
from .colors import cprint, Colors
import time
from ..type.errors import InvalidID
if TYPE_CHECKING:
    from ..network.network import Network

DATA_SUFFIXS = {
    "Image": ("png", "jpg", "gif", "jpeg", "webp", "svg", "ico"),
    "Video": ("mp4", "mkv", "mov", "avi", "webm", "m4v", "mpg", "mpeg"),
    "Music": ("mp3", "wav", "aac", "m4a", "ogg")
}

class Utils:
    @staticmethod
    def format_file(type_file: Optional[str] = None) -> Optional[str]:
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
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        metadata: Optional[list] = None,
        meta_data: Optional[list] = None
    ) -> dict:
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
    async def d_file(file: Union[str , Path , bytes], file_name: str, network: 'Network') -> Dict[str, Tuple[str, Union[bytes, bytearray], str]]:
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
        return d_file
    
    @staticmethod
    def check_data(data: dict) -> bool:
        if data.get("status", "") == "OK":
            return True
        return False

    @staticmethod
    def prefer_first(value1: Optional[str] = None, value2: Optional[str] = None) -> str:
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
                return True
        return False

    @staticmethod
    def check_id_raise(id: str):
        if not Utils.check_id(id=id):
            raise InvalidID('Invalid Id. The ID must be 32 characters long and must also start with one of the letters "b", "u", or "g".')

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
