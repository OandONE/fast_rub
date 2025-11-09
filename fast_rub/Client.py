import httpx
import os
import time
import json
import asyncio
import inspect
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
import aiofiles
from .colors import *
from .filters import Filter
from functools import wraps
from pathlib import Path
from .type import (
    Update,
    UpdateButton
)
from .async_sync import *
from .logger import *
from .type.props import *


class Client:
    def __init__(
        self,
        name_session: str,
        token: Optional[str] = None,
        user_agent: Optional[str] = None,
        time_out: Optional[int] = 60,
        display_welcome=True,
        use_to_fastrub_webhook_on_message: Union[str,bool] = True,
        use_to_fastrub_webhook_on_button: Union[str,bool] = True,
        save_logs: Optional[bool] = None,
        view_logs: Optional[bool] = None,
        proxy: Optional[str] = None
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
        self.data_keypad = []
        self.data_keypad2 = []
        self._button_handlers2 = []
        self._running_ = False
        self._loop = None
        self.last = []
        self._fetch_messages = False
        self._fetch_messages_ = False
        self._fetch_buttons = False
        self._fetch_edit = False
        self._message_handlers = []
        self._button_handlers = []
        self._edit_handlers = []
        self.last = []
        self._message_handlers_ = []
        self.next_offset_id = ""
        self.next_offset_id_ = ""
        self.last_ = []
        if os.path.isfile(name):
            with open(name, "r", encoding="utf-8") as file:
                text_json_fast_rub_session = json.load(file)
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
            if token == None:
                token = input("Enter your token : ")
                while token in ["", " ", None]:
                    cprint("Enter the token valid !",Colors.RED)
                    token = input("Enter your token : ")
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
            with open(name, "w", encoding="utf-8") as file:
                json.dump(
                    text_json_fast_rub_session, file, ensure_ascii=False, indent=4
                )
            self.token = token
            self.time_out = time_out
            self.user_agent = user_agent
        self.log_to_file = save_logs
        self.log_to_console = view_logs
        if self.log_to_file is None:
            self.log_to_file = True
        if self.log_to_console is None:
            self.log_to_console = True
        self.httpx_client = httpx.AsyncClient(timeout=self.time_out,proxy=self.proxy)
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
            asyncio.run(self.version_botapi())
        except:
            self.main_url = self.urls[1]
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
    async def manage_closeing(self) -> None:
        if self.httpx_client.is_closed:
            self.httpx_client = httpx.AsyncClient(timeout=self.time_out,proxy=self.proxy)

    @async_to_sync
    async def version_botapi(self) -> str:
        """getting version botapi / گرفتن نسخه بات ای پی آی"""
        await self.manage_closeing()
        response = await self.httpx_client.get(self.main_url,timeout=self.time_out)
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
        self, method, data_: Optional[Union[Dict[str, Any], List[Any]]] = None,url_op:Optional[str] = None
    ) -> dict:
        """send request to methods / ارسال درخواست به متود ها"""
        self.logger.info("در حال ارسال درخواست")
        url_op = self.main_url
        url = f"{url_op}{self.token}/{method}"
        headers = {"Content-Type": "application/json"}
        if self.user_agent != None:
            headers["User-Agent"] = self.user_agent
        await self.manage_closeing()
        try:
            if data_ == None:
                result = await self.httpx_client.post(url, headers=headers)
                result_ = result.json()
            else:
                result = await self.httpx_client.post(url, headers=headers, json=data_)
                result_ = result.json()
            if result_["status"] != "OK":
                self.logger.error(f"خطایی از سمت سرور ! status : {result_['status']}")
                raise TypeError(f"Error for invalid status : {result_}")
            self.logger.info("نتیجه درخواست موفق است")
            return result_
        except TimeoutError:
            self.logger.error("خطا ! زمان ارسال درخواست به پایان رسیده است")
            raise TimeoutError("Please check the internet !")
        except Exception as e:
            self.logger.error(f"خطایی ناشناخته : {e}")
            raise e

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
    async def send_text(
        self,
        text: str,
        chat_id: str,
        inline_keypad = KeyPad,
        disable_notification: Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
        auto_delete: Optional[int] = None
    ) -> props:
        """sending text to chat id / ارسال متنی به یک چت آیدی"""
        self.logger.info("استفاده از متود send_message")
        if not inline_keypad:
            data = {
                "chat_id": chat_id,
                "text": text,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
            }
        else:
            data = {
                "chat_id": chat_id,
                "text": text,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "inline_keypad": {"rows": inline_keypad}
            }
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
    async def send_poll(self, chat_id: str, question: str, options: list,auto_delete: Optional[int] = None) -> props:
        """sending poll to chat id / ارسال نظرسنجی به یک چت آیدی"""
        self.logger.info("استفاده از متود send_poll")
        data = {"chat_id": chat_id, "question": question, "options": options}
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
    async def get_chat(self, chat_id: str) -> props:
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
    async def edit_message_text(self, chat_id: str, message_id: str, text: str) -> props:
        """editing message text / ویرایش متن پیام"""
        self.logger.info("استفاده از متود edit_message_text")
        data = {"chat_id": chat_id, "message_id": message_id, "text": text}
        result = await self.send_requests(
            "editMessageText",
            data,
        )
        return props(result)

    @async_to_sync
    async def delete_message(self, chat_id: str, message_id: str) -> props:
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
    ) -> props:
        """editing the text key pad inline / ویرایش پیام شیشه ای"""
        self.logger.info("استفاده از متود edit_message_keypad_Inline")
        data = {
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "chat_id": chat_id,
            "text": text,
            "inline_keypad": {"rows": inline_keypad},
        }
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
        auto_delete: Optional[int] = None
    ) -> props:
        """sending message key pad texti / ارسال پیام با دکمه متنی"""
        self.logger.info("استفاده از متود send_message_keypad")
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
        if type(file) is bytes:
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
        auto_delete: Optional[int] = None
    ) -> props:
        """sending file by file id / ارسال فایل با آیدی فایل"""
        self.logger.info("استفاده از متود send_file_by_file_id")
        data = {
            "chat_id": chat_id,
            "text": text,
            "file_id": file_id,
            "reply_to_message_id": reply_to_message_id,
            "disable_notification": disable_notification,
        }
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
        auto_delete: Optional[int] = None
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
            for type_,pass_ in {"File":"", "Image":".png", "Voice":".mp3", "Music":".mp3", "Gif":".png" , "Video":".mp4"}.items():
                if type_ == type_file:
                    name_file = f"{type_+pass_}"
                    break
        if not name_file:
            raise ValueError("type file is invalud !")
        file_id = (await self.upload_file(up_url_file, name_file, file))["data"]["file_id"]
        uploader = (await self.send_file_by_file_id(chat_id,file_id,text,reply_to_message_id,disable_notification))._data_
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
        result = uploader
        if auto_delete:
            message_id = result["data"]["message_id"]
            try:
                return props(result)
            finally:
                await self.auto_delete(chat_id,message_id,auto_delete)
        return props(result)

    @async_to_sync
    async def send_image(
        self,
        chat_id: str,
        image: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None
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
            auto_delete
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
        auto_delete: Optional[int] = None
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
            auto_delete
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
        auto_delete: Optional[int] = None
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
            auto_delete
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
        auto_delete: Optional[int] = None
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
            auto_delete
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
        auto_delete: Optional[int] = None
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
            auto_delete
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
        async with httpx.AsyncClient(proxy=self.proxy) as client:
            async with client.stream('GET', url) as response:
                async with aiofiles.open(path, 'wb') as file:
                    async for chunk in response.aiter_bytes():
                        self.logger.info("فایل دانلود شد")
                        await file.write(chunk)

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
                await self.set_endpoint(f"https://fast-rub.ParsSource.ir/geting_button_updates/{self.token}/{it}", it)
            return True
        else:
            if r["error"] == "This token exists":
                for it in list_up:
                    await self.set_endpoint(f"https://fast-rub.ParsSource.ir/geting_button_updates/{self.token}/{it}", it)
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

    @async_to_sync
    async def _process_messages_(self, time_updata_sleep : Union[float,float] = 0.5):
        while self._running:
            try:
                await self.httpx_client.get("https://rubika.ir/",timeout=self.time_out)
            except:
                raise TimeoutError("please check the your internet .")
            mes = (await self.get_updates(limit=100,offset_id=self.next_offset_id))
            if mes.status=="INVALID_ACCESS":
                raise PermissionError("Due to Rubika's restrictions, access to retrieve messages has been blocked. Please try again.")
            try:
                self.next_offset_id = mes["data"]["next_offset_id"]
            except:
                pass
            for message in mes["data"]["updates"]:
                if message["type"]=="NewMessage":
                    time_sended_mes = int(message['new_message']['time'])
                    now = int(time.time())
                    time_ = time_updata_sleep + 4
                    if (now - time_sended_mes < time_) and (not message['new_message']['message_id'] in self.last):
                        self.last.append(message['new_message']['message_id'])
                        if len(self.last) > 500:
                            self.last.pop(-1)
                        update_obj = Update(message,self)
                        for handler in self._message_handlers_:
                            self._schedule_handler(handler,update_obj)
            await asyncio.sleep(time_updata_sleep)

    def on_message_updates(self, filters: Optional[Filter] = None):
        """برای دریافت آپدیت‌های پیام"""
        def decorator(handler):
            @wraps(handler)
            async def wrapped(update):
                if filters is None or filters(update):
                    return await handler(update)
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

    def on_edit(self):
        """برای دریافت ویرایش شدن پیام ها"""
        self._fetch_edit = True
        def decorator(handler: Callable[[Update], Awaitable[None]]):
            self._edit_handlers.append(handler)
            return handler
        return decorator

    @async_to_sync
    async def _process_messages(self):
        while self._running:
            response = (await self.httpx_client.get(self._on_url, timeout=self.time_out)).json()
            if response and response.get('status') is True:
                results = response.get('updates', [])
                if results:
                    for result in results:
                        update = Update(result,self)
                        for handler in self._message_handlers:
                            self._schedule_handler(handler,update)
            else:
                await self.set_token_fast_rub()
            await asyncio.sleep(0.1)

    @async_to_sync
    async def _process_edit(self, time_updata_sleep : Union[int,int] = 1):
        while self._running:
            try:
                await self.httpx_client.get("https://rubika.ir/",timeout=self.time_out)
            except:
                raise TimeoutError("please check the your internet .")
            mes = (await self.get_updates(limit=100,offset_id=self.next_offset_id_))
            if mes['status']=="INVALID_ACCESS":
                raise PermissionError("Due to Rubika's restrictions, access to retrieve messages has been blocked. Please try again.")
            try:
                self.next_offset_id_ = mes["data"]["next_offset_id"]
            except:
                pass
            for message in mes['data']['updates']:
                if message["type"]=="UpdatedMessage":
                    time_sended_mes = int(message['updated_message']['time'])
                    now = int(time.time())
                    time_ = time_updata_sleep + 4
                    if (now - time_sended_mes < time_) and (not message['updated_message']['message_id'] in self.last_):
                        self.last_.append(message['updated_message']['message_id'])
                        if len(self.last_) > 500:
                            self.last_.pop(-1)
                        update_obj = Update(message,self)
                        for handler in self._edit_handlers:
                            self._schedule_handler(handler,update_obj)
            await asyncio.sleep(time_updata_sleep)

    @async_to_sync
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

    @async_to_sync
    async def _run_all(self):
        tasks = []
        if self._fetch_messages and self._message_handlers:
            tasks.append(self._process_messages())
        if self._fetch_buttons and self._button_handlers:
            tasks.append(self._fetch_button_updates())
        if self._fetch_messages_ and self._message_handlers_:
            tasks.append(self._process_messages_())
        if self._fetch_edit and self._edit_handlers:
            tasks.append(self._process_edit())
        if not tasks:
            raise ValueError("No handlers registered. Use on_message() or on_message_updates() or on_button() or on_edit() first.")
        await asyncio.gather(*tasks)

    def run(self):
        """اجرای اصلی بات - فقط اگر هندلرهای مربوطه ثبت شده باشند"""
        if not (self._fetch_messages or self._fetch_buttons or self._fetch_messages_ or self._fetch_edit):
            raise ValueError("No update types selected. Use on_message() or on_message_updates() or on_button() or on_edit() first.")
        
        if (self._fetch_messages and not self._message_handlers) or (self._fetch_messages_ and not self._message_handlers_):
            raise ValueError("Message handlers registered but no message callbacks defined.")
        
        if self._fetch_buttons and not self._button_handlers:
            raise ValueError("Button handlers registered but no button callbacks defined.")

        if self._fetch_edit and not self._edit_handlers:
            raise ValueError("Edit handlers registered but no message callbacks defined.")

        self._running = True
        self.logger.info("ربات در حال دریافت پیام ها")
        asyncio.run(self._run_all())