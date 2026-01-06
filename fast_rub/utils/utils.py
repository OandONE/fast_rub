from typing import Dict, Tuple, Optional, Union, TYPE_CHECKING
from pathlib import Path
import aiofiles
from .colors import cprint, Colors
import time
from .encryption import Encryption
import json
import os
from ..type.errors import CreateSessionError
if TYPE_CHECKING:
    from ..network.network import Network

class Utils:
    @staticmethod
    def format_file(type_file: Optional[str] = None) -> Optional[str]:
        if not type_file:
            return None
        for type_,pass_ in {"File":"", "Image":".png", "Voice":".mp3", "Music":".mp3", "Gif":".mp4" , "Video":".mp4"}.items():
            if type_ == type_file:
                name_file = type_+pass_
                return name_file
        return None
    
    @staticmethod
    def print_time(text: str, time_sleep: float = 0.07, color: str = Colors.WHITE) -> None:
        k = ""
        for text in text:
            k += text
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

    # Session
    
    @staticmethod
    def session_dict(name_session: str, token: str, user_agent: Optional[str] = None, time_out: Optional[float] = 30.0, display_welcome: bool = False, view_logs: Optional[bool] = False, save_logs: Optional[bool] = False) -> dict:
        text_json_fast_rub_session = {
            "name_session": name_session,
            "token": token,
            "user_agent": user_agent,
            "time_out": time_out,
            "display_welcome": display_welcome,
            "setting_logs":{
                "view":view_logs,
                "save":save_logs
            }
        }
        return text_json_fast_rub_session
    
    @staticmethod
    def save_dict(data: dict, name_file: str):
        json_fast_rub_session = json.dumps(data,indent=4,ensure_ascii=False)
        json_fast_rub_session = Encryption.en(str(json_fast_rub_session))
        Utils.save(json_fast_rub_session, name_file)

    @staticmethod
    def save(data: str, name_file: str):
        with open(name_file, "w", encoding="utf-8") as file:
            file.write(data)

    @staticmethod
    def create_session(name_session: str, token: Optional[str] = None, user_agent: Optional[str] = None, time_out: Optional[float] = 30.0, display_welcome: bool = False, view_logs: Optional[bool] = False, save_logs: Optional[bool] = False) -> bool:
        try:
            if token is None:
                token = Utils.get_input("Write The Token » ")
            session = Utils.session_dict(name_session,token,user_agent,time_out,display_welcome,view_logs,save_logs)
            Utils.save_dict(session, f"{name_session}.faru")
            return True
        except:
            return False
    
    @staticmethod
    def open_session(name_session: str, token: Optional[str] = None, user_agent: Optional[str] = None, time_out: Optional[float] = None, display_welcome: bool = False, view_logs: Optional[bool] = False, save_logs: Optional[bool] = False) -> dict:
        """بازکردن سشن

        Args:
            name_session (str): اسم سشن
            token (Optional[str], optional): توکن. Defaults to None.
            user_agent (Optional[str], optional): اطلاعات مرورگر درخواست کننده. Defaults to None.
            time_out (Optional[int], optional): زمان خروج. Defaults to 30.
            display_welcome (bool, optional): خوش آمد گویی. Defaults to False.
            view_logs (Optional[bool], optional): نمایش لاگ ها. Defaults to False.
            save_logs (Optional[bool], optional): ذخیره لاگ ها. Defaults to False.

        Raises:
            CreateSessionError: خطا برای ساخت سشن

        Returns:
            dict: اطلاعات سشن
        """
        path_session = name_session + ".faru"
        if os.path.isfile(path_session):
            with open(path_session, "r", encoding="utf-8") as file:
                encrypted_string = file.read().strip()
            try:
                decrypted = Encryption.de(encrypted_string)
                session_data = json.loads(decrypted)
            except:
                cprint("Error for getting last data session !", Colors.RED)
                creating = False
                while not creating:
                    creating = Utils.create_session(name_session,token,user_agent,time_out,display_welcome,view_logs,save_logs)
                    if not creating:
                        raise CreateSessionError("Can Not Create The Session !")
                session_data = Utils.open_session(name_session,token,user_agent,time_out,display_welcome,view_logs,save_logs)
            current_params = {
                'token': token,
                'user_agent': user_agent,
                'time_out': time_out,
                'display_welcome': display_welcome,
                'setting_logs': {
                    'view': view_logs,
                    'save': save_logs
                }
            }
            for param_name, param_value in current_params.items():
                if param_name in session_data:
                    if param_value is not None and session_data[param_name] != param_value:
                        session_data[param_name] = param_value
        else:
            creating = False
            while not creating:
                creating = Utils.create_session(name_session,token,user_agent,time_out,display_welcome,view_logs,save_logs)
                if not creating:
                    raise CreateSessionError("Can Not Create The Session !")
            session_data = Utils.open_session(name_session,token,user_agent,time_out,display_welcome,view_logs,save_logs)
        return session_data
    

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
            data["metadata"] = {"meta_data_parts": metadata}
            if meta_data:
                for meta in meta_data:
                    data["metadata"]["meta_data_parts"].append(meta)
        elif meta_data:
            data["metadata"] = {"meta_data_parts": meta_data}
        return data
    
    # Other

    @staticmethod
    async def d_file(file: Union[str , Path , bytes], file_name: str, network: "Network") -> Dict[str, Tuple[str, Union[bytes, bytearray], str]]:
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
    def get_chat_id_type(chat_id: str):
        if chat_id.startswith("b"):
            return "User"
        elif chat_id.startswith("g"):
            return "Group"
        elif chat_id.startswith("c"):
            return "Channel"
        else:
            raise ValueError("chat id is not found")
