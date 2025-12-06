import httpx
import os
import time
import json
import asyncio
import inspect
import aiofiles
from functools import wraps
from pathlib import Path
from typing import (
    Optional,
    Callable,
    Awaitable,
    Literal,
    Union,
    Dict,
    List,
    Any
)
from .button import KeyPad
from .colors import *
from .filters import Filter
from .type import (
    Update,
    UpdateButton
)
from .async_sync import *
from .logger import *
from .type.props import *
from .utils import (
    TextParser,
    utils
)
from .errors import (
    TokenInvalid,
    PollInvalid
)
from .encryption import Encryption


class Client:
    def __init__(
        self,
        name_session: str,
        token: Optional[str] = None,
        user_agent: Optional[str] = None,
        time_out: Optional[int] = 60,
        display_welcome = False,
        use_to_fastrub_webhook_on_message: Union[str,bool] = True,
        use_to_fastrub_webhook_on_button: Union[str,bool] = True,
        save_logs: Optional[bool] = None,
        view_logs: Optional[bool] = None,
        proxy: Optional[str] = None,
        main_parse_mode: Literal['Markdown', 'HTML', "Unknown", None] = "Unknown",
        max_retries: int = 3
    ):
        """Client for login and setting robot / کلاینت برای لوگین و تنظیمات ربات"""
        name = name_session + ".faru"
        self.name_session = name
        self.token = token
        self.time_out = time_out
        self.user_agent = user_agent
        self._running = False
        self.list_ = []
        self.proxy = proxy
        self._fetch_messages = False
        self._fetch_messages_ = False
        self._fetch_buttons = False
        self._fetch_edit = False
        self._message_handlers = []
        self._button_handlers = []
        self._edit_handlers = []
        self._edit_handlers_ = []
        self.last = []
        self._message_handlers_ = []
        self.next_offset_id = ""
        self.next_offset_id_ = ""
        self.next_offset_id_get_message = ""
        self.geted_u = 0
        self.main_parse_mode:Literal['Markdown', 'HTML', 'Unknown', None] = main_parse_mode
        self.max_retries = max_retries
        self.list_befor_messages = []
        if os.path.isfile(name):
            with open(name, "r", encoding="utf-8") as file:
                encrypted_string = file.read().strip()
            decrypted = Encryption().de(encrypted_string)
            text_json_fast_rub_session = json.loads(decrypted)
            self.text_json_fast_rub_session = text_json_fast_rub_session
            self.token = text_json_fast_rub_session["token"]
            self.time_out = text_json_fast_rub_session["time_out"]
            self.user_agent = text_json_fast_rub_session["user_agent"]
            try:
                self.log_to_file = text_json_fast_rub_session["setting_logs"]["save"]
                self.log_to_console = text_json_fast_rub_session["setting_logs"]["view"]
            except:
                pass
        else:
            if token is None:
                token = input("Enter your token : ")
                while token in ["", " ", None]:
                    cprint("Enter the token valid !",Colors.RED)
                    token = input("Enter your token : ")
            self.token = token
            if len(str(self.token)) != 64 :
                raise TokenInvalid(f"token invalid ! len for token not is 64. is {len(str(self.token))}")
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
            self.text_json_fast_rub_session = text_json_fast_rub_session
            text_json_fast_rub_session = json.dumps(text_json_fast_rub_session,indent=4,ensure_ascii=False)
            text_json_fast_rub_session = Encryption().en(str(text_json_fast_rub_session))
            with open(name, "w", encoding="utf-8") as file:
                file.write(text_json_fast_rub_session)
            self.token = token
            self.time_out = time_out
            self.user_agent = user_agent
        self.log_to_file = save_logs
        self.log_to_console = view_logs
        if self.log_to_file is None:
            self.log_to_file = False
        if self.log_to_console is None:
            self.log_to_console = False
        self.httpx_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=30.0,
                write=10.0,
                pool=10.0
            ),
            proxy=self.proxy,
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
                keepalive_expiry=60.0
            ),
            http1=True,
            http2=True
        )
        self.use_to_fastrub_webhook_on_message=use_to_fastrub_webhook_on_message
        self.use_to_fastrub_webhook_on_button = use_to_fastrub_webhook_on_button
        if type(use_to_fastrub_webhook_on_message) is str:
            self._on_url = use_to_fastrub_webhook_on_message
        else:
            self._on_url = f"https://fast-rub.ParsSource.ir/geting_button_updates/get_on?token={self.token}"
        if type(use_to_fastrub_webhook_on_button) is str:
            self._button_url = use_to_fastrub_webhook_on_button
        else:
            self._button_url = f"https://fast-rub.ParsSource.ir/geting_button_updates/get?token={self.token}"
        self.urls = ["https://botapi.rubika.ir/v3/","https://messengerg2b1.iranlms.ir/v3/"]
        self.main_url = self.urls[0]
        try:
            self.version_botapi()
        except:
            self.main_url = self.urls[1]
        try:
            mes = self.get_updates(limit=100)
            self.next_offset_id_get_message = mes["data"]["next_offset_id"]
        except:
            pass
        self.logger = logging.getLogger("fast_rub")
        setup_logging(log_to_console=self.log_to_console,log_to_file=self.log_to_file)
        if display_welcome:
            k = ""
            for text in "Welcome to FastRub":
                k += text
                print(f"{Colors.GREEN}{k}{Colors.RESET}", end="\r")
                time.sleep(0.07)
            cprint("",Colors.WHITE)
        self.logger.info("سشن اماده است")

    @property
    def TOKEN(self):
        self.logger.info("توکن دریافت شد")
        return self.token

    @async_to_sync
    async def check_closing(self) -> bool:
        """check status client / چک کردن وضعیت کلاینت"""
        if self.httpx_client.is_closed:
            try:
                await self.httpx_client.get(self.main_url)
            except httpx.CloseError:
                return False
        return True

    @async_to_sync
    async def manage_closeing(self) -> None:
        """مدیریت اتصال کلاینت با بررسی سلامت"""
        try:
            if self.httpx_client.is_closed:
                self.logger.info("اتصال بسته شده، در حال ایجاد مجدد...")
                await self._recreate_client()
                return
                
            try:
                test_url = f"{self.main_url}{self.token}/getMe"
                async with self.httpx_client.stream("GET", test_url, timeout=5.0) as response:
                    if response.status_code != 200:
                        raise httpx.ConnectError("Connection test failed")
            except (httpx.ReadError, httpx.ConnectError, httpx.TimeoutException):
                self.logger.warning("اتصال نامعتبر، در حال بازسازی...")
                await self._recreate_client()
                
        except Exception as e:
            self.logger.error(f"خطا در مدیریت اتصال: {e}")
            await self._recreate_client()

    async def _recreate_client(self):
        """بازسازی کامل httpx client"""
        try:
            await self.httpx_client.aclose()
        except:
            pass
        
        self.httpx_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0),
            proxy=self.proxy,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            http1=True,
            http2=True
        )

    @async_to_sync
    async def health_check(self) -> bool:
        """بررسی سلامت اتصال به سرور تلگرام"""
        try:
            result = await self.send_requests("getMe")
            return result["status"] == "OK"
        except:
            return False

    @async_to_sync  
    async def set_retry_settings(self, max_retries: int = 3):
        """تنظیمات تلاش مجدد"""
        self.max_retries = max_retries

    @async_to_sync
    async def version_botapi(self) -> str:
        """getting version botapi / گرفتن نسخه بات ای پی آی"""
        await self.manage_closeing()
        response = await self.httpx_client.get(self.main_url.replace("v3/",""),timeout=self.time_out)
        version = response.text
        return version

    @async_to_sync
    async def set_logging(
        self,
        saving: Optional[bool] = None,
        viewing: Optional[bool] = None
    ):
        """on or off viewing and saveing logs / فعال یا غیرفعال کردن نمایش و ذخیره لاگ"""
        self.logger.info("استفاده از متود set_logging")
        if saving is None:
            saving = self.log_to_file
        if viewing is None:
            viewing = self.log_to_console
        try:
            self.text_json_fast_rub_session["setting_logs"]["save"] = saving
            self.text_json_fast_rub_session["setting_logs"]["view"] = viewing
        except:
            self.text_json_fast_rub_session["setting_logs"] = {
                "save":saving,
                "view":viewing
            }
        with open(self.name_session, "w") as fi:
            json.dump(self.text_json_fast_rub_session, fi, ensure_ascii=False, indent=4)
        if saving and viewing:
            self.logger = setup_logging(log_to_file=saving, log_to_console=viewing)
        self.logger.info(f"logging تنظیم شد | نمایش: {viewing} | ذخیره: {saving}")

    @async_to_sync
    async def set_timeout(self,time_out:int) -> None:
        """setting time out / تنظیم تایم اوت"""
        self.time_out = time_out

    @async_to_sync
    async def send_requests(
        self, method, data_: Optional[Union[Dict[str, Any], List[Any]]] = None
    ) -> dict:
        """send request to methods with retry mechanism"""
        self.logger.info(f"در حال ارسال درخواست به {method}")
        max_retries = self.max_retries
        url_op = self.main_url
        url = f"{url_op}{self.token}/{method}"
        headers = {"Content-Type": "application/json"}
        
        if self.user_agent != None:
            headers["User-Agent"] = self.user_agent

        last_exception = None
        for attempt in range(max_retries):
            try:
                await self.manage_closeing()
                
                if data_ == None:
                    result = await self.httpx_client.post(url, headers=headers)
                    result_ = result.json()
                else:
                    result = await self.httpx_client.post(url, headers=headers, json=data_)
                    result_ = result.json()
                    
                if result_["status"] != "OK":
                    self.logger.error(f"خطا از سمت سرور! status: {result_['status']}")
                    raise TypeError(f"Error for invalid status: {result_}")
                    
                self.logger.info("نتیجه درخواست موفق است")
                return result_
                
            except (httpx.ReadError, httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                wait_time = (attempt + 1) * 2
                
                self.logger.warning(
                    f"خطای شبکه در تلاش {attempt + 1}/{max_retries}: {type(e).__name__}. "
                    f"انتظار {wait_time} ثانیه..."
                )
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                    try:
                        await self.httpx_client.aclose()
                    except:
                        pass
                    self.httpx_client = httpx.AsyncClient(
                        timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0),
                        proxy=self.proxy,
                        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
                    )
                    
            except Exception as e:
                self.logger.error(f"خطای ناشنخانه send_requests » {e}")
                raise e

        self.logger.error(f"تمام {max_retries} تلاش ناموفق بود")
        raise last_exception

    @async_to_sync
    async def auto_delete(self,chat_id:str,message_id:str,time_sleep:float) -> props:
        """auto delete message next {time_sleep} time s / حذف خودکار پیام بعد از فلان مقدار ثانیه"""
        await asyncio.sleep(time_sleep)
        result = await self.delete_message(chat_id,message_id)
        return props(result)

    @async_to_sync
    async def get_me(self) -> props:
        """geting info accont bot / گرفتن اطلاعات اکانت ربات
        Returns:
        dict: 
            - status (str): وضعیت درخواست (مثلا "OK")
            - data (dict): شامل اطلاعات ربات
                - bot (dict):
                    - bot_id (str): شناسه گوید ربات
                    - bot_title (str): نام نمایشی ربات
                    - description (str): توضیحات ربات
                    - username (str): نام کاربری ربات
                    - start_message (str): پیام شروع
                    - share_url (str): لینک اشتراک ربات"""
        self.logger.info("استفاده از متود get_me")
        result = await self.send_requests(method="getMe")
        return props(result)

    @async_to_sync
    async def set_main_parse_mode(self,parse_mode: Literal['Markdown', 'HTML', 'Unknown', None]) -> None:
        """setting parse mode main / تنظیم کردن مقدار اصلی پارس مود

توجه :
در صورت تغییر مارکدوان در کلاینت یا متود ست مین پارس مود , پارس مود همیشه روی آن حالت قرار میگیرد
در صورتی که میخواهید از این حالت خارج شود و از ورودی های متود ها پیروی کند مقدار آن را در متود ست مین پارس مود برابر 'Unknown' کنید"""
        self.main_parse_mode = parse_mode

    @async_to_sync
    async def parse_mode_text(self, text: str,parse_mode: Literal["Markdown","HTML","Unknown",None] = "Markdown") -> tuple:
        """setting parse mode text / تنظیم پارس مود متن"""
        if self.main_parse_mode != "Unknown":
            parse_mode = self.main_parse_mode
        if parse_mode == "Markdown":
            data = TextParser.checkMarkdown(text)
            return data
        elif parse_mode == "HTML":
            data = TextParser.checkHTML(text)
            return data
        return [], text

    @async_to_sync
    async def send_text(
        self,
        text: str,
        chat_id: str,
        inline_keypad: Optional[KeyPad] = None,
        disable_notification: Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> props:
        """sending text to chat id / ارسال متنی به یک چت آیدی"""
        self.logger.info("استفاده از متود send_text")
        metadata, text  = await self.parse_mode_text(text, parse_mode)
        data = {
            "chat_id": chat_id,
            "text": text,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id
        }
        if inline_keypad:
            data["inline_keypad"] = {"rows": inline_keypad}
        if metadata:
            data["metadata"] = {"meta_data_parts": metadata}
        result = await self.send_requests(
            "sendMessage",
            data,
        )
        if auto_delete:
            message_id = result["data"]["message_id"]
            try:
                return props(result)
            finally:
                await self.auto_delete(chat_id,message_id,auto_delete)
        return props(result)

    @async_to_sync
    async def send_message(
        self,
        chat_id: str,
        text: Optional[str],
        inline_keypad: Optional[KeyPad],
        disable_notification: bool = False,
        reply_to_message_id: Optional[str] = None,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        # file
        file: Union[str , Path , bytes , None] = None,
        name_file: Optional[str] = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif" , "Video"] = "File",
        file_id: Optional[str] = None,
        # poll
        question: Optional[str] = None,
        options: Optional[list] = None,
        type_poll: Literal["Regular", "Quiz"] = "Regular",
        is_anonymous: bool = True,
        correct_option_index: Optional[int] = None,
        allows_multiple_answers: bool = False,
        hint: Optional[str] = None,
        # location
        latitude: Optional[str] = None,
        longitude: Optional[str] = None,
        # contact
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> props:
        """send message / ارسال پیام"""
        if file_id:
            return await self.send_file_by_file_id(chat_id,file_id,text,reply_to_message_id,disable_notification,auto_delete,parse_mode)
        elif file:
            return await self.send_file(chat_id,file,name_file,text,reply_to_message_id,type_file,disable_notification,auto_delete,parse_mode)
        elif question != None and options != None:
            return await self.send_poll(chat_id,question,options,type_poll=type_poll,is_anonymous=is_anonymous,correct_option_index=correct_option_index,allows_multiple_answers=allows_multiple_answers,hint=hint,auto_delete=auto_delete,reply_to_message_id=reply_to_message_id,disable_notification=disable_notification)
        elif latitude != None and longitude != None:
            return await self.send_location(chat_id,latitude,longitude,disable_notification=disable_notification,reply_to_message_id=reply_to_message_id,auto_delete=auto_delete)
        elif first_name and last_name and phone_number:
            return await self.send_contact(chat_id,first_name,last_name,phone_number,reply_to_message_id=reply_to_message_id,disable_notificatio=disable_notification,auto_delete=auto_delete)
        elif text != None:
            return await self.send_text(text,chat_id,inline_keypad,disable_notification,reply_to_message_id,auto_delete,parse_mode)
        raise ValueError("Please Enter The Args !")

    @async_to_sync
    async def send_poll(
        self,
        chat_id: str,
        question: str,
        options: list,
        type_poll: Literal["Regular", "Quiz"] = "Regular",
        is_anonymous: bool = True,
        correct_option_index: Optional[int] = None,
        allows_multiple_answers: bool = False,
        hint: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[str] = None,
        auto_delete: Optional[int] = None
    ) -> props:
        """sending poll to chat id / ارسال نظرسنجی به یک چت آیدی"""
        self.logger.info("استفاده از متود send_poll")
        if len(options) > 10:
            raise PollInvalid("len for options is logner from 10 option")
        data = {
            "chat_id": chat_id,
            "question": question,
            "options": options,
            "type": type_poll,
            "is_anonymous": is_anonymous,
            "correct_option_index": correct_option_index,
            "hint": hint,
            "allows_multiple_answers": allows_multiple_answers,
            "reply_to_message_id": reply_to_message_id,
            "disable_notification": disable_notification
        }
        result = await self.send_requests(
            "sendPoll",
            data,
        )
        if auto_delete:
            message_id = result["data"]["message_id"]
            try:
                return props(result)
            finally:
                await self.auto_delete(chat_id,message_id,auto_delete)
        return props(result)

    @async_to_sync
    async def send_location(
        self,
        chat_id: str,
        latitude: str,
        longitude: str,
        chat_keypad : Optional[str] = None,
        disable_notification: Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
        chat_keypad_type: Optional[str] = None,
        auto_delete: Optional[int] = None
    ) -> props:
        """sending location to chat id / ارسال لوکیشن(موقعیت مکانی) به یک چت آیدی"""
        self.logger.info("استفاده از متود send_location")
        data = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude,
            "chat_keypad": chat_keypad,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "chat_keypad_type": chat_keypad_type,
        }
        result = await self.send_requests(
            "sendLocation",
            data,
        )
        if auto_delete:
            message_id = result["data"]["message_id"]
            try:
                return props(result)
            finally:
                await self.auto_delete(chat_id,message_id,auto_delete)
        return props(result)

    @async_to_sync
    async def send_contact(
        self,
        chat_id: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        chat_keypad : Optional[str] = None,
        chat_keypad_type: Optional[str] = None,
        inline_keypad: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notificatio: Optional[bool] = False,
        auto_delete: Optional[int] = None
    ) -> props:
        """sending contact to chat id / ارسال مخاطب به یک چت آیدی"""
        self.logger.info("استفاده از متود send_contact")
        data = {
            "chat_id": chat_id,
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": phone_number,
            "chat_keypad": chat_keypad,
            "disable_notificatio": disable_notificatio,
            "chat_keypad_type": chat_keypad_type,
            "inline_keypad": inline_keypad,
            "reply_to_message_id": reply_to_message_id,
        }
        result = await self.send_requests(
            "sendContact",
            data,
        )
        if auto_delete:
            message_id = result["data"]["message_id"]
            try:
                return props(result)
            finally:
                await self.auto_delete(chat_id,message_id,auto_delete)
        return props(result)

    @async_to_sync
    async def get_chat(
        self,
        chat_id: str
    ) -> props:
        """geting info chat id info / گرفتن اطلاعات های یک چت"""
        self.logger.info("استفاده از متود get_chat")
        data = {"chat_id": chat_id}
        result = await self.send_requests(
            "getChat",
            data,
        )
        return props(result)

    @async_to_sync
    async def get_updates(self, limit : Optional[int] = None, offset_id : Optional[str] = None) -> props:
        """getting messages chats / گرفتن پیام های چت ها"""
        self.logger.info("استفاده از متود get_updates")
        data = {"offset_id": offset_id, "limit": limit}
        result = await self.send_requests(
            "getUpdates",
            data,
        )
        return props(result)

    @async_to_sync
    async def get_message(self,chat_id: str,message_id: str,limit_search: int = 100) -> Optional[Update]:
        updates = await self.get_updates(limit_search,self.next_offset_id_get_message)
        self.geted_u = len(updates["data"]["updates"])
        for message in updates["data"]["updates"]:
            if message["type"]=="NewMessage":
                if message["chat_id"] == chat_id and message['new_message']['message_id'] == message_id:
                    return Update(message,self)
        if self.geted_u >= 40:
            try:
                self.next_offset_id_get_message = updates["data"]["next_offset_id"]
                self.geted_u = 0
                return await self.get_message(chat_id,message_id,limit_search)
            except:
                pass
        return None

    @async_to_sync
    async def get_messages(self,chat_id: str,message_id: str,limit_search: int = 100,get_befor: int = 10) -> Optional[dict]:
        updates = await self.get_updates(limit_search,self.next_offset_id_get_message)
        result = {"messages":[]}
        self.geted_u = len(updates["data"]["updates"])
        for message in updates["data"]["updates"]:
            if message["type"]=="NewMessage" and message["chat_id"] == chat_id:
                self.list_befor_messages.append(message)
                if message['new_message']['message_id'] == message_id:
                    self.list_befor_messages.reverse()
                    for i in range(get_befor):
                        result['messages'].append(self.list_befor_messages[i])
                    return result
        if self.geted_u >= 40:
            try:
                self.next_offset_id_get_message = updates["data"]["next_offset_id"]
                self.geted_u = 0
                return await self.get_messages(chat_id,message_id,limit_search,get_befor)
            except:
                pass
        return result

    @async_to_sync
    async def forward_message(
        self,
        from_chat_id: str,
        message_id: str,
        to_chat_id: str,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None
    ) -> props:
        """forwarding message to chat id / فوروارد پیام به یک چت آیدی"""
        self.logger.info("استفاده از متود forward_message")
        data = {
            "from_chat_id": from_chat_id,
            "message_id": message_id,
            "to_chat_id": to_chat_id,
            "disable_notification": disable_notification,
        }
        result = await self.send_requests(
            "forwardMessage",
            data,
        )
        if auto_delete:
            message_id = result["data"]["message_id"]
            try:
                return props(result)
            finally:
                await self.auto_delete(to_chat_id,message_id,auto_delete)
        return props(result)

    @async_to_sync
    async def forward_messages(
        self,
        from_chat_id: str,
        message_ids: list,
        to_chat_id: str,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None
    ) -> List[props]:
        """forwarding messages to chat id / فوروارد چند پیام به یک چت آیدی"""
        list_forwards = []
        for ms_id in message_ids:
            list_forwards.append(await self.forward_message(from_chat_id,ms_id,to_chat_id,disable_notification,auto_delete))
        return list_forwards

    @async_to_sync
    async def edit_message_text(
        self,
        chat_id: str,
        message_id: str,
        text: str,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> props:
        """editing message text / ویرایش متن پیام"""
        self.logger.info("استفاده از متود edit_message_text")
        metadata, text  = await self.parse_mode_text(text, parse_mode)
        data = {"chat_id": chat_id, "message_id": message_id, "text": text}
        if metadata:
            data["metadata"] = {"meta_data_parts": metadata}
        result = await self.send_requests(
            "editMessageText",
            data,
        )
        return props(result)

    @async_to_sync
    async def delete_message(
        self,
        chat_id: str,
        message_id: str
    ) -> props:
        """delete message / پاکسازی(حذف) یک پیام"""
        self.logger.info("استفاده از متود delete_message")
        data = {"chat_id": chat_id, "message_id": message_id}
        result = await self.send_requests(
            "deleteMessage",
            data,
        )
        return props(result)

    @async_to_sync
    async def add_commands(self, command: str, description: str) -> None:
        """add command to commands list / افزودن دستور به لیست دستورات"""
        self.logger.info("استفاده از متود add_commands")
        self.list_.append(
            {"command": command.replace("/", ""), "description": description}
        )

    @async_to_sync
    async def set_commands(self) -> props:
        """set the commands for robot / تنظیم دستورات برای ربات"""
        self.logger.info("استفاده از متود set_commands")
        result = await self.send_requests(
            "setCommands",
            {"bot_commands": self.list_},
        )
        return props(result)

    @async_to_sync
    async def delete_commands(self) -> props:
        """clear the commands list / پاکسازی لیست دستورات"""
        self.logger.info("استفاده از متود delete_commands")
        self.list_ = []
        result = await self.send_requests(
            "setCommands",
            self.list_,
        )
        return props(result)

    @async_to_sync
    async def edit_message_keypad_Inline(
        self,
        chat_id: str,
        text: str,
        inline_keypad,
        disable_notification : Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> props:
        """editing the text key pad inline / ویرایش پیام شیشه ای"""
        self.logger.info("استفاده از متود edit_message_keypad_Inline")
        metadata, text  = await self.parse_mode_text(text, parse_mode)
        data = {
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "chat_id": chat_id,
            "text": text,
            "inline_keypad": {"rows": inline_keypad},
        }
        if metadata:
            data["metadata"] = {"meta_data_parts": metadata}
        result = await self.send_requests(
            "editMessageText",
            data,
        )
        return props(result)

    @async_to_sync
    async def send_message_keypad(
        self,
        chat_id: str,
        text: str,
        Keypad:KeyPad,
        disable_notification : Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
        resize_keyboard : Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> props:
        """sending message key pad texti / ارسال پیام با دکمه متنی"""
        self.logger.info("استفاده از متود send_message_keypad")
        metadata, text  = await self.parse_mode_text(text, parse_mode)
        data = {
            "chat_id": chat_id,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "text": text,
            "chat_keypad_type": "New",
            "chat_keypad": {
                "rows": Keypad,
                "resize_keyboard": resize_keyboard,
                "on_time_keyboard": on_time_keyboard,
            },
        }
        if metadata:
            data["metadata"] = {"meta_data_parts": metadata}
        result = await self.send_requests(
            "sendMessage",
            data,
        )
        if auto_delete:
            message_id = result["data"]["message_id"]
            try:
                return props(result)
            finally:
                await self.auto_delete(chat_id,message_id,auto_delete)
        return props(result)

    @async_to_sync
    async def upload_file(self, url: str, file_name: str, file: Union[str , Path , bytes]) -> dict:
        """upload file to rubika server / آپلود فایل در سرور روبیکا"""
        self.logger.info("استفاده از متود upload_file")
        if isinstance(file, (bytes, bytearray)):
            d_file = {"file": (file_name, file, "application/octet-stream")}
        else:
            try:
                async with aiofiles.open(file, "rb") as fi:
                    fil = await fi.read()
                    d_file = {"file": (file_name, fil , "application/octet-stream")}
            except:
                file_ = (await self.httpx_client.get(str(file))).content
                d_file = {"file":file_}
        async with httpx.AsyncClient(verify=False,proxy=self.proxy) as cl:
            response = await cl.post(url, files=d_file,timeout=9999)
            if response.status_code != 200:
                self.logger.error("خطا در آپلود فایل !")
                raise httpx.HTTPStatusError(
                    f"Request failed with status code {response.status_code}",
                    request=response.request,
                    response=response,
                )
            data = response.json()
            return data

    @async_to_sync
    async def send_file_by_file_id(
        self,
        chat_id: str,
        file_id: str,
        text: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> props:
        """sending file by file id / ارسال فایل با آیدی فایل"""
        self.logger.info("استفاده از متود send_file_by_file_id")
        metadata = []
        if text:
            metadata, text  = await self.parse_mode_text(text, parse_mode)
        data = {
            "chat_id": chat_id,
            "text": text,
            "file_id": file_id,
            "reply_to_message_id": reply_to_message_id,
            "disable_notification": disable_notification,
        }
        if metadata:
            data["metadata"] = {"meta_data_parts": metadata}
        sending = await self.send_requests("sendFile", data)
        if auto_delete:
            message_id = sending["data"]["message_id"]
            try:
                return props(sending)
            finally:
                await self.auto_delete(chat_id,message_id,auto_delete)
        return props(sending)

    @async_to_sync
    async def send_file(
        self,
        chat_id: str,
        file: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif" , "Video"] = "File",
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> props:
        """sending file with types ['File', 'Image', 'Voice', 'Music', 'Gif' , 'Video'] / ارسال فایل با نوع های فایل و عکس و پیغام صوتی و موزیک و گیف و ویدیو"""
        self.logger.info("استفاده از متود send_file")
        up_url_file = (
            await self.send_requests(
                "requestSendFile",
                {"type": type_file},
            )
        )["data"]["upload_url"]
        if not name_file:
            name_file = utils.format_file(name_file)
        if not name_file:
            raise ValueError("type file is invalud !")
        file_id = (await self.upload_file(up_url_file, name_file, file))["data"]["file_id"]
        uploader = (await self.send_file_by_file_id(chat_id,file_id,text,reply_to_message_id,disable_notification,parse_mode=parse_mode))._data_
        uploader["file_id"] = file_id
        uploader["type_file"] = type_file
        if isinstance(file, (bytes, bytearray, memoryview)):
            uploader["size_file"] = len(file)
        elif isinstance(file, (str, Path)):
            try:
                async with aiofiles.open(file, "rb") as fi:
                    fil = await fi.read()
                    size_file = len(fil)
            except:
                size_file = len((await self.httpx_client.get(str(file))).content)
                uploader["size_file"] = size_file
        else:
            raise FileExistsError("file not found !")
        if auto_delete:
            message_id = uploader["data"]["message_id"]
            try:
                return props(uploader)
            finally:
                await self.auto_delete(chat_id,message_id,auto_delete)
        return props(uploader)

    @async_to_sync
    async def send_image(
        self,
        chat_id: str,
        image: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> props:
        """sending image / ارسال تصویر"""
        self.logger.info("استفاده از متود send_image")
        
        result = await self.send_file(
            chat_id,
            image,
            name_file,
            text,
            reply_to_message_id,
            "Image",
            disable_notification,
            auto_delete,
            parse_mode
        )
        return props(result)

    @async_to_sync
    async def send_video(
        self,
        chat_id: str,
        video: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> props:
        """sending video / ارسال ویدیو"""
        self.logger.info("استفاده از متود send_video")
        result = await self.send_file(
            chat_id,
            video,
            name_file,
            text,
            reply_to_message_id,
            "Video",
            disable_notification,
            auto_delete,
            parse_mode
        )
        return props(result)

    @async_to_sync
    async def send_voice(
        self,
        chat_id: str,
        voice: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> props:
        """sending voice / ارسال ویس"""
        self.logger.info("استفاده از متود send_voice")
        result = await self.send_file(
            chat_id,
            voice,
            name_file,
            text,
            reply_to_message_id,
            "Voice",
            disable_notification,
            auto_delete,
            parse_mode
        )
        return props(result)

    @async_to_sync
    async def send_music(
        self,
        chat_id: str,
        music: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> props:
        """sending music / ارسال موزیک"""
        self.logger.info("استفاده از متود send_music")
        result = await self.send_file(
            chat_id,
            music,
            name_file,
            text,
            reply_to_message_id,
            "Music",
            disable_notification,
            auto_delete,
            parse_mode
        )
        return props(result)

    @async_to_sync
    async def send_gif(
        self,
        chat_id: str,
        gif: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> props:
        """sending gif / ارسال گیف"""
        self.logger.info("استفاده از متود send_gif")
        result = await self.send_file(
            chat_id,
            gif,
            name_file,
            text,
            reply_to_message_id,
            "Gif",
            disable_notification,
            auto_delete,
            parse_mode
        )
        return props(result)

    @async_to_sync
    async def send_sticker(
        self,
        chat_id: str,
        id_sticker: str,
        reply_to_message_id : Optional[str] = None,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None
    ) -> props:
        """sending sticker by id / ارسال استیکر با آیدی"""
        self.logger.info("استفاده از متود send_sticker")
        data = {
            "chat_id": chat_id,
            "sticker_id": id_sticker,
            "reply_to_message_id": reply_to_message_id,
            "disable_notification": disable_notification
        }
        sender = await self.send_requests("sendSticker", data)
        if auto_delete:
            message_id = sender["data"]["message_id"]
            try:
                return props(sender)
            finally:
                await self.auto_delete(chat_id,message_id,auto_delete)
        return props(sender)

    @async_to_sync
    async def get_download_file_url(self,id_file : str) -> str:
        """get download url file / گرفتن آدرس دانلود فایل"""
        self.logger.info("استفاده از متود get_download_file_url")
        data = {"file_id": id_file}
        url = (await self.send_requests("getFile",data))["download_url"]
        return url

    @async_to_sync
    async def download_file(self,id_file : str , path : str = "file") -> None:
        """download file / دانلود فایل"""
        self.logger.info("استفاده از متود download_file")
        url = await self.get_download_file_url(id_file)
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        async with httpx.AsyncClient(proxy=self.proxy,timeout=30) as client:
            async with client.stream('GET', url) as response:
                response.raise_for_status()
                async with aiofiles.open(path, 'wb') as file:
                    async for chunk in response.aiter_bytes():
                        await file.write(chunk)
        self.logger.info("فایل دانلود شد")

    @async_to_sync
    async def set_endpoint(self, url: str, type: Literal["ReceiveUpdate", "GetSelectionItem", "ReceiveInlineMessage", "ReceiveQuery", "SearchSelectionItems"]) -> props:
        """set endpoint url / تنظیم ادرس اند پوینت"""
        self.logger.info("استفاده از متود set_endpoint")
        result = await self.send_requests(
            "updateBotEndpoints", {"url": url, "type": type}
        )
        return props(result)

    def _schedule_handler(self, handler, update):
        async def _wrapped():
            try:
                await handler(update)
            except Exception:
                self.logger.exception("Error in handler")
        asyncio.create_task(_wrapped())

    @async_to_sync
    async def set_token_fast_rub(self) -> bool:
        """seting token in fast_rub for getting click glass messages and updata messges / تنظیم توکن در فست روب برای گرفتن کلیک های روی پیام شیشه ای و آپدیت پیام ها"""
        self.logger.info("استفاده از متود set_token_fast_rub")
        r = (await self.httpx_client.get(f"https://fast-rub.ParsSource.ir/set_token?token={self.token}")).json()
        list_up:List[Literal["ReceiveUpdate", "ReceiveInlineMessage"]]= ["ReceiveUpdate", "ReceiveInlineMessage"]
        if r["status"]:
            for it in list_up:
                url = f"https://fast-rub.ParsSource.ir/geting_button_updates/{self.token}/{it}"
                set_ = await self.set_endpoint(url, it)
            return True
        else:
            if r["error"] == "This token exists":
                for it in list_up:
                    url = f"https://fast-rub.ParsSource.ir/geting_button_updates/{self.token}/{it}"
                    set_ = await self.set_endpoint(url, it)
                return True
        return False

    def on_message(self, filters: Optional[Filter] = None):
        """برای دریافت پیام‌های معمولی"""
        self._fetch_messages_ = True
        def decorator(handler):
            @wraps(handler)
            async def wrapped(update):
                if filters is None or filters(update):
                    if inspect.iscoroutinefunction(handler):
                        return await handler(update)
                    else:
                        return handler(update)
            self._message_handlers_.append(wrapped)
            return handler
        return decorator

    async def _process_messages_(self, time_updata_sleep: Union[float, float] = 0.5):
        while self._running:
            try:
                mes = await self.get_updates(limit=100, offset_id=self.next_offset_id)
                
                if mes.status == "INVALID_ACCESS":
                    raise PermissionError("Due to Rubika's restrictions, access to retrieve messages has been blocked.")
                    
                try:
                    self.next_offset_id = mes["data"]["next_offset_id"]
                except:
                    pass
                    
                for message in mes["data"]["updates"]:
                    if message["type"] == "NewMessage":
                        time_sended_mes = int(message['new_message']['time'])
                        now = int(time.time())
                        time_ = time_updata_sleep + 4
                        
                        if (now - time_sended_mes < time_) and (not message['new_message']['message_id'] in self.last):
                            self.last.append(message['new_message']['message_id'])
                            if len(self.last) > 500:
                                self.last.pop(0)
                            update_obj = Update(message, self)
                            for handler in self._message_handlers_:
                                self._schedule_handler(handler, update_obj)
                                
                await asyncio.sleep(time_updata_sleep)
                
            except (httpx.ReadError, httpx.ConnectError) as e:
                self.logger.warning(f"خطای شبکه در _process_messages_: {e} - انتظار 5 ثانیه...")
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"خطای ناشناخته در _process_messages_: {e}")
                await asyncio.sleep(10)

    def on_message_updates(self, filters: Optional[Filter] = None):
        """برای دریافت آپدیت‌های پیام"""
        self._fetch_messages = True
        def decorator(handler):
            @wraps(handler)
            async def wrapped(update):
                if filters is None or filters(update):
                    if inspect.iscoroutinefunction(handler):
                        return await handler(update)
                    else:
                        return handler(update)
            self._message_handlers.append(wrapped)
            return handler
        return decorator

    def on_button(self):
        """برای دریافت کلیک روی دکمه‌ها"""
        self._fetch_buttons = True
        def decorator(handler: Callable[[UpdateButton], Awaitable[None]]):
            self._button_handlers.append(handler)
            return handler
        return decorator

    def on_edit_updates(self):
        """برای دریافت ویرایش شدن پیام ها"""
        self._fetch_edit = True
        def decorator(handler: Callable[[Update], Awaitable[None]]):
            self._edit_handlers_.append(handler)
            return handler
        return decorator

    async def _process_messages(self):
        while self._running:
            response = (await self.httpx_client.get(self._on_url, timeout=self.time_out)).json()
            if response and response.get('status') is True:
                results = response.get('updates', [])
                if results:
                    for result in results:
                        if result["type"] != "NewMessage":
                            continue
                        update = Update(result,self)
                        for handler in self._message_handlers:
                            self._schedule_handler(handler,update)
            else:
                await self.set_token_fast_rub()
            await asyncio.sleep(0.1)

    async def _process_edit_updates(self):
        while self._running:
            response = (await self.httpx_client.get(self._button_url, timeout=self.time_out)).json()
            if response and response.get('status') is True:
                results = response.get('updates', [])
                if results:
                    for result in results:
                        if result["type"] != "UpdatedMessage":
                            continue
                        update = UpdateButton(result,self)
                        for handler in self._button_handlers:
                            self._schedule_handler(handler,update)
            else:
                await self.set_token_fast_rub()
            await asyncio.sleep(0.1)

    async def _fetch_button_updates(self):
        while self._running:
            response = (await self.httpx_client.get(self._button_url, timeout=self.time_out)).json()
            if response and response.get('status') is True:
                results = response.get('updates', [])
                if results:
                    for result in results:
                        update = UpdateButton(result,self)
                        for handler in self._button_handlers:
                            self._schedule_handler(handler,update)
            else:
                await self.set_token_fast_rub()
            await asyncio.sleep(0.1)

    async def _run_all(self):
        tasks = []
        if self._fetch_messages and self._message_handlers:
            tasks.append(self._process_messages())
        if self._fetch_buttons and self._button_handlers:
            tasks.append(self._fetch_button_updates())
        if self._fetch_messages_ and self._message_handlers_:
            tasks.append(self._process_messages_())
        if self._fetch_edit and self._edit_handlers_:
            tasks.append(self._process_edit_updates())
        if not tasks:
            raise ValueError("No handlers registered. Use on_message() or on_message_updates() or on_button() or on_edit_updates() first.")
        await asyncio.gather(*tasks)

    def run(self):
        """اجرای اصلی بات - فقط اگر هندلرهای مربوطه ثبت شده باشند"""
        if not (self._fetch_messages or self._fetch_buttons or self._fetch_messages_ or self._fetch_edit):
            raise ValueError("No update types selected. Use on_message() or on_message_updates() or on_button() or on_edit_updates() first.")
        
        if (self._fetch_messages and not self._message_handlers) or (self._fetch_messages_ and not self._message_handlers_):
            raise ValueError("Message handlers registered but no message callbacks defined.")
        
        if self._fetch_buttons and not self._button_handlers:
            raise ValueError("Button handlers registered but no button callbacks defined.")

        if self._fetch_edit and not self._edit_handlers_:
            raise ValueError("Edit handlers registered but no message callbacks defined.")

        self._running = True
        self.logger.info("ربات در حال دریافت پیام ها")
        k = ""
        for text in "Start Handlers":
            k += text
            print(f"{Colors.BLUE}{k}{Colors.RESET}", end="\r")
            time.sleep(0.07)
        cprint("",Colors.WHITE)
        asyncio.run(self._run_all())

    def stop(self):
        """خاموش کردن گرفتن آپدیت ها / off the getting updates"""
        self._running = False