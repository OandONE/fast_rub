import asyncio
import inspect
import time
from functools import wraps
from pathlib import Path
from typing import (Any, Awaitable, Callable, Dict, List, Literal, Optional,
                    Union)

import aiofiles
import httpx

from .async_sync import async_to_sync
from ..utils.filters import Filter
from ..network.network import Network
from ..type import Update, UpdateButton, msg_update
from ..type.errors import PollInvalid
from ..type.props import props
from ..type.models import *
from ..utils.colors import Colors
from ..utils.logger import logging, setup_logging
from ..utils.utils import TextParser, utils


class Client:
    """
    Client is the main interface of fast_rub for interacting with the Rubika Bot API.

    کلاس Client هستهٔ اصلی کتابخانه fast_rub است و تمام ارتباطات با Bot API روبیکا
    از طریق این کلاس انجام می‌شود.

    مسئولیت‌های اصلی:
    - مدیریت سشن، توکن و تنظیمات اولیه ربات
    - ارسال پیام، فایل، رسانه، نظرسنجی و سایر انواع محتوا
    - دریافت آپدیت‌ها (پیام، دکمه)
    - مدیریت هندلرها و توزیع آپدیت‌ها
    - کنترل لاگ‌ها، تایم‌اوت، پراکسی و retry

    این کلاس هم به صورت async و هم sync قابل استفاده است.
    بیشتر متدها به صورت async پیاده‌سازی شده‌اند اما با استفاده از
    دکوراتور async_to_sync می‌توان آن‌ها را به شکل sync نیز فراخوانی کرد.

    مدل دریافت آپدیت‌ها:
    - on_message():
        دریافت پیام‌های جدید با polling
    - on_message_updates():
        دریافت پیام‌ها از طریق fast_rub webhook
    - on_button():
        دریافت کلیک‌های دکمه (Inline Keyboard)

    فعال یا غیرفعال بودن هر نوع آپدیت با فلگ‌های داخلی مشخص می‌شود
    و در صورت ثبت نشدن هندلر مناسب، اجرای کلاینت متوقف خواهد شد.

    Parameters
    ----------
    name_session : str
        نام سشن برای ذخیره تنظیمات و توکن

    token : Optional[str]
        توکن ربات (در صورت نبود، از فایل سشن خوانده می‌شود)

    user_agent : Optional[str]
        مقدار User-Agent برای درخواست‌های HTTP

    time_out : float
        تایم‌اوت درخواست‌ها (بر حسب ثانیه)

    display_welcome : bool
        نمایش پیام خوش‌آمدگویی هنگام شروع

    use_to_fastrub_webhook_on_message : Union[str, bool]
        فعال‌سازی یا تعیین آدرس webhook برای دریافت پیام‌ها

    use_to_fastrub_webhook_on_button : Union[str, bool]
        فعال‌سازی یا تعیین آدرس webhook برای دریافت دکمه‌ها

    save_logs : Optional[bool]
        ذخیره لاگ‌ها در فایل

    view_logs : Optional[bool]
        نمایش لاگ‌ها در کنسول

    proxy : Optional[str]
        پراکسی برای ارتباطات شبکه

    main_parse_mode : Literal['Markdown', 'HTML', 'Unknown', None]
        پارس مود پیش‌فرض پیام‌ها
        اگر مقدار 'Unknown' باشد، پارس مود هر متد به صورت جداگانه اعمال می‌شود

    max_retries : int
        حداکثر تعداد تلاش مجدد در خطاهای شبکه
    """
    def __init__(
        self,
        name_session: str,
        token: Optional[str] = None,
        user_agent: Optional[str] = None,
        time_out: float = 60.0,
        display_welcome: bool = False,
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
        self.time_out = time_out
        self.user_agent = user_agent
        self._running = False
        self.list_commands = []
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
        self.main_parse_mode: Literal['Markdown', 'HTML', 'Unknown', None] = main_parse_mode
        self.max_retries = max_retries
        self.list_befor_messages = []
        self.session = utils.open_session(name_session, token, user_agent, time_out, display_welcome, view_logs, save_logs)
        self.token:str = self.session["token"]
        self.time_out = self.session["time_out"]
        self.user_agent = self.session["user_agent"]
        try:
            self.log_to_file = self.session["setting_logs"]["save"]
            self.log_to_console = self.session["setting_logs"]["view"]
        except:
            pass
        if self.log_to_file is None:
            self.log_to_file = False
        if self.log_to_console is None:
            self.log_to_console = False
        self.logger = logging.getLogger("fast_rub")
        self.use_to_fastrub_webhook_on_message = use_to_fastrub_webhook_on_message
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
        try:
            mes = asyncio.run(self.get_updates(limit=100))
            self.next_offset_id_get_message = mes["next_offset_id"]
        except:
            pass
        setup_logging(log_to_console=self.log_to_console,log_to_file=self.log_to_file)
        if display_welcome:
            utils.print_time("Welcome To FastRub", color=Colors.GREEN)
        self.logger.info("سشن اماده است")

    @property
    def TOKEN(self):
        self.logger.info("توکن دریافت شد")
        return self.token

    @property
    def NAME_SESSION(self):
        self.logger.info("نام سشن دریافت شد")
        return self.name_session

    @async_to_sync  
    async def set_retry_settings(self, max_retries: int = 3):
        """تنظیمات تلاش مجدد"""
        self.max_retries = max_retries

    @async_to_sync
    async def version_botapi(self) -> str:
        """getting version botapi / گرفتن نسخه بات ای پی آی"""
        response = await self.network.request(self.main_url.replace("v3/",""),type_send="GET",timeout=self.time_out)
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
            self.session["setting_logs"]["save"] = saving
            self.session["setting_logs"]["view"] = viewing
        except:
            self.session["setting_logs"] = {
                "save":saving,
                "view":viewing
            }
        utils.save_dict(self.session, self.name_session)
        self.logger = setup_logging(log_to_file=saving, log_to_console=viewing)
        self.logger.info(f"logging تنظیم شد | نمایش: {viewing} | ذخیره: {saving}")

    @async_to_sync
    async def set_timeout(self,time_out:int) -> None:
        """setting time out / تنظیم تایم اوت"""
        self.time_out = time_out

    @async_to_sync
    async def send_requests(
        self, method: str, data_: Optional[Union[Dict[str, Any], List[Any]]] = None
    ) -> dict:
        """send request to methods with retry mechanism"""
        try:
            self.network
        except:
            self.network = Network(self.token,logger=self.logger,max_retries=self.max_retries,user_agent=self.user_agent,proxy=self.proxy)
        response = await self.network.send_request(method=method,data_=data_)
        return response

    @async_to_sync
    async def auto_delete(self,chat_id:str,message_id:str,time_sleep:float) -> props:
        """auto delete message next {time_sleep} time s / حذف خودکار پیام بعد از فلان مقدار ثانیه"""
        await asyncio.sleep(time_sleep)
        result = await self.delete_message(chat_id,message_id)
        return props(result)

    @async_to_sync
    async def get_me(self) -> Bot:
        """geting info accont bot / گرفتن اطلاعات اکانت ربات"""
        self.logger.info("استفاده از متود get_me")
        result = await self.send_requests(method="getMe")
        bot = result["bot"]
        bot_id = bot["bot_id"]
        bot_title = bot["bot_title"]
        description = bot["description"]
        username = bot["username"]
        start_message = bot["start_message"]
        share_url = bot["share_url"]
        return Bot(bot_id=bot_id,bot_title=bot_title,description=description,username=username,start_message=start_message,share_url=share_url)

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

    async def _auto_delete(self, data: dict, auto_delete: Optional[int] = None):
        if auto_delete:
            message_id = data["message_id"]
            chat_id = data["chat_id"]
            await self.auto_delete(chat_id, message_id, auto_delete)

    async def _manage_auto_delete(self, data: dict, auto_delete: Optional[int] = None):
        asyncio.create_task(self._auto_delete(data, auto_delete))

    @async_to_sync
    async def send_text(
        self,
        text: str,
        chat_id: str,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        disable_notification: Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> msg_update:
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
        if keypad:
            data["chat_keypad"] = {
                "rows": keypad,
                "resize_keyboard": resize_keyboard,
                "on_time_keyboard": on_time_keyboard,
            }
            data["chat_keypad_type"] = "New"
        result = await self.send_requests(
            "sendMessage",
            data,
        )
        result["chat_id"] = chat_id
        await self._manage_auto_delete(result, auto_delete)
        return msg_update(result, self)

    @async_to_sync
    async def send_message(
        self,
        chat_id: str,
        text: Optional[str] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
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
    ) ->  msg_update:
        """send message / ارسال پیام"""
        if file_id:
            return await self.send_file_by_file_id(chat_id,file_id,text,reply_to_message_id,disable_notification,auto_delete,parse_mode)
        elif file:
            return await self.base_send_file(chat_id,file,name_file,text,reply_to_message_id,type_file,disable_notification,auto_delete,parse_mode)
        elif question != None and options != None:
            return await self.send_poll(chat_id,question,options,type_poll=type_poll,is_anonymous=is_anonymous,correct_option_index=correct_option_index,allows_multiple_answers=allows_multiple_answers,hint=hint,auto_delete=auto_delete,reply_to_message_id=reply_to_message_id,disable_notification=disable_notification)
        elif latitude != None and longitude != None:
            return await self.send_location(chat_id,latitude,longitude,disable_notification=disable_notification,reply_to_message_id=reply_to_message_id,auto_delete=auto_delete)
        elif first_name and last_name and phone_number:
            return await self.send_contact(chat_id,first_name,last_name,phone_number,reply_to_message_id=reply_to_message_id,disable_notificatio=disable_notification,auto_delete=auto_delete)
        elif text != None:
            return await self.send_text(text=text,chat_id=chat_id,inline_keypad=inline_keypad,disable_notification=disable_notification,reply_to_message_id=reply_to_message_id,auto_delete=auto_delete,parse_mode=parse_mode,keypad=keypad,on_time_keyboard=on_time_keyboard,resize_keyboard=resize_keyboard)
        raise ValueError("Please Write The Args !")

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
    ) -> msg_update:
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
        result["chat_id"] = chat_id
        await self._manage_auto_delete(result, auto_delete)
        return msg_update(result, self)

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
    ) -> msg_update:
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
        result["chat_id"] = chat_id
        await self._manage_auto_delete(result, auto_delete)
        return msg_update(result, self)

    @async_to_sync
    async def send_contact(
        self,
        chat_id: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        chat_keypad : Optional[str] = None,
        chat_keypad_type: Optional[str] = None,
        inline_keypad: Optional[list] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notificatio: Optional[bool] = False,
        auto_delete: Optional[int] = None
    ) -> msg_update:
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
        result["chat_id"] = chat_id
        await self._manage_auto_delete(result, auto_delete)
        return msg_update(result, self)

    @async_to_sync
    async def get_chat(
        self,
        chat_id: str
    ) -> Chat:
        """geting info chat id info / گرفتن اطلاعات های یک چت"""
        self.logger.info("استفاده از متود get_chat")
        data = {"chat_id": chat_id}
        result = await self.send_requests(
            "getChat",
            data,
        )
        chat = result["chat"]
        first_name = chat["first_name"] if "first_name" in chat else chat["title"]
        last_name = chat["last_name"] if "last_name" in chat else None
        user_id = chat["user_id"] if "user_id" in chat else None
        return Chat(first_name=first_name,last_name=last_name,user_id=user_id)

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
        self.geted_u = len(updates["updates"])
        for message in updates["updates"]:
            if message["type"]=="NewMessage":
                if message["chat_id"] == chat_id and message['new_message']['message_id'] == message_id:
                    return Update(message,self)
        if self.geted_u >= 40:
            try:
                self.next_offset_id_get_message = updates["next_offset_id"]
                self.geted_u = 0
                return await self.get_message(chat_id,message_id,limit_search)
            except:
                pass
        return None

    @async_to_sync
    async def get_messages(self,chat_id: str,message_id: str,limit_search: int = 100,get_befor: int = 10) -> Optional[dict]:
        """_summary_

        Args:
            chat_id (str): _description_
            message_id (str): _description_
            limit_search (int, optional): _description_. Defaults to 100.
            get_befor (int, optional): _description_. Defaults to 10.

        Returns:
            Optional[dict]: _description_
        """
        updates = await self.get_updates(limit_search,self.next_offset_id_get_message)
        result = {"messages":[]}
        self.geted_u = len(updates["updates"])
        for message in updates["updates"]:
            if message["type"]=="NewMessage" and message["chat_id"] == chat_id:
                self.list_befor_messages.append(message)
                if message['new_message']['message_id'] == message_id:
                    self.list_befor_messages.reverse()
                    for i in range(get_befor):
                        result['messages'].append(self.list_befor_messages[i])
                    return result
        if self.geted_u >= 40:
            try:
                self.next_offset_id_get_message = updates["next_offset_id"]
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
    ) -> msg_update:
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
        result["chat_id"] = to_chat_id
        await self._manage_auto_delete(result, auto_delete)
        return msg_update(result, self)

    @async_to_sync
    async def forward_messages(
        self,
        from_chat_id: str,
        message_ids: list,
        to_chat_id: str,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None
    ) -> List[msg_update]:
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
        inline_keypad: Optional[list] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> msg_update:
        """editing message text / ویرایش متن پیام"""
        self.logger.info("استفاده از متود edit_message_text")
        metadata, text  = await self.parse_mode_text(text, parse_mode)
        data = {"chat_id": chat_id, "message_id": message_id, "text": text}
        if inline_keypad:
            data["inline_keypad"] = {"rows": inline_keypad}
        if metadata:
            data["metadata"] = {"meta_data_parts": metadata}
        result = await self.send_requests(
            "editMessageText",
            data,
        )
        result["chat_id"] = chat_id
        return msg_update(result, self)

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
        self.list_commands.append(
            {"command": command.replace("/", ""), "description": description}
        )

    @async_to_sync
    async def set_commands(self) -> dict:
        """set the commands for robot / تنظیم دستورات برای ربات"""
        self.logger.info("استفاده از متود set_commands")
        result = await self.send_requests(
            "setCommands",
            {"bot_commands": self.list_commands},
        )
        return result

    @async_to_sync
    async def delete_commands(self) -> dict:
        """clear the commands list / پاکسازی لیست دستورات"""
        self.logger.info("استفاده از متود delete_commands")
        self.list_commands = []
        result = await self.set_commands()
        return result
    
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
                file_ = (await self.network.request(str(file),type_send="GET")).content
                d_file = {"file": (file_name, file_, "application/octet-stream")}
        timeout_file = utils.calculate_upload_timeout(len(d_file["file"][1]))
        response = await self.network.upload(url, d_file, timeout_file)
        return response

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
    ) -> msg_update:
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
        sending["chat_id"] = chat_id
        await self._manage_auto_delete(sending, auto_delete)
        return msg_update(sending, self)
    
    @async_to_sync
    async def request_send_file(
        self,
        type: Literal["File", "Image", "Voice", "Music", "Gif" , "Video"] = "File"
    ) -> dict:
        return await self.send_requests(
            "requestSendFile",
            {
                "type": type
            }
        )

    async def base_send_file(
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
    ) -> msg_update:
        """sending file with types ['File', 'Image', 'Voice', 'Music', 'Gif' , 'Video'] / ارسال فایل با نوع های فایل و عکس و پیغام صوتی و موزیک و گیف و ویدیو"""
        self.logger.info("استفاده از متود base_send_file")
        request_file = await self.request_send_file(type_file)
        upload_url_file = request_file["upload_url"]
        if not name_file:
            name_file = utils.format_file(type_file)
        if not name_file:
            raise ValueError("type file is invalud !")
        upload_file = await self.upload_file(upload_url_file, name_file, file)
        file_id = upload_file["file_id"]
        send = await self.send_file_by_file_id(chat_id,file_id,text,reply_to_message_id,disable_notification,parse_mode=parse_mode,auto_delete=auto_delete)
        sended = send.to_dict()
        sended["file_id"] = file_id
        sended["type_file"] = type_file
        if isinstance(file, (bytes, bytearray, memoryview)):
            sended["size_file"] = len(file)
        elif isinstance(file, (str, Path)):
            try:
                async with aiofiles.open(file, "rb") as fi:
                    fil = await fi.read()
                    size_file = len(fil)
            except:
                size_file = len((await self.network.request(str(file))).content)
                sended["size_file"] = size_file
        else:
            raise FileExistsError("file not found !")
        return msg_update(sended, self)

    @async_to_sync
    async def send_file(
        self,
        chat_id: str,
        file: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> msg_update:
        "ارسال فایل / send file"
        self.logger.info("استفاده از متود send_file")

        result = await self.base_send_file(
            chat_id,
            file,
            name_file,
            text,
            reply_to_message_id,
            "File",
            disable_notification,
            auto_delete,
            parse_mode
        )
        return result

    @async_to_sync
    async def send_document(
        self,
        chat_id: str,
        file: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown"
    ) -> msg_update:
        "ارسال فایل / send file"
        self.logger.info("استفاده از متود send_document")

        result = await self.base_send_file(
            chat_id,
            file,
            name_file,
            text,
            reply_to_message_id,
            "File",
            disable_notification,
            auto_delete,
            parse_mode
        )
        return result

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
    ) -> msg_update:
        """sending image / ارسال تصویر"""
        self.logger.info("استفاده از متود send_image")
        result = await self.base_send_file(
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
        return result

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
    ) -> msg_update:
        """sending video / ارسال ویدیو"""
        self.logger.info("استفاده از متود send_video")
        result = await self.base_send_file(
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
        return result

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
    ) -> msg_update:
        """sending voice / ارسال ویس"""
        self.logger.info("استفاده از متود send_voice")
        result = await self.base_send_file(
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
        return result

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
    ) -> msg_update:
        """sending music / ارسال موزیک"""
        self.logger.info("استفاده از متود send_music")
        result = await self.base_send_file(
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
        return result

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
    ) -> msg_update:
        """sending gif / ارسال گیف"""
        self.logger.info("استفاده از متود send_gif")
        result = await self.base_send_file(
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
        return result

    @async_to_sync
    async def send_sticker(
        self,
        chat_id: str,
        id_sticker: str,
        reply_to_message_id : Optional[str] = None,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None
    ) -> msg_update:
        """sending sticker by id / ارسال استیکر با آیدی"""
        self.logger.info("استفاده از متود send_sticker")
        data = {
            "chat_id": chat_id,
            "sticker_id": id_sticker,
            "reply_to_message_id": reply_to_message_id,
            "disable_notification": disable_notification
        }
        sender = await self.send_requests("sendSticker", data)
        sender["chat_id"] = chat_id
        await self._manage_auto_delete(sender, auto_delete)
        return msg_update(sender, self)

    @async_to_sync
    async def get_download_file_url(self,id_file : str) -> str:
        """get download url file / گرفتن آدرس دانلود فایل"""
        self.logger.info("استفاده از متود get_download_file_url")
        data = {"file_id": id_file}
        url = (await self.send_requests("getFile",data))["download_url"]
        return url

    @async_to_sync
    async def download_by_url(self, url: str, path: str = "file") -> None:
        download = await self.network.download(url, path)
        if download:
            self.logger.info("فایل دانلود شد")
        else:
            self.logger.error("خطا در دانلود فایل !")

    @async_to_sync
    async def download_file(self,id_file : str , path : str = "file") -> None:
        """download file / دانلود فایل"""
        self.logger.info("استفاده از متود download_file")
        url = await self.get_download_file_url(id_file)
        await self.download_by_url(url, path)

    @async_to_sync
    async def set_endpoint(self, url: str, type: Literal["ReceiveUpdate", "GetSelectionItem", "ReceiveInlineMessage", "ReceiveQuery", "SearchSelectionItems"]) -> dict:
        """set endpoint url / تنظیم ادرس اند پوینت"""
        self.logger.info("استفاده از متود set_endpoint")
        result = await self.send_requests(
            "updateBotEndpoints", {"url": url, "type": type}
        )
        return result
    
    @async_to_sync
    async def update_end_point(self, url: str, type: Literal["ReceiveUpdate", "GetSelectionItem", "ReceiveInlineMessage", "ReceiveQuery", "SearchSelectionItems"]) -> dict:
        """set endpoint url / تنظیم ادرس اند پوینت"""
        return await self.set_endpoint(url, type)

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
        try:
            check_setted = await self.network.request(f"https://fast-rub.ParsSource.ir/set_token?token={self.token}")
            check_setted = check_setted.json()
            list_getted: List[Literal["ReceiveUpdate", "ReceiveInlineMessage"]] = ["ReceiveUpdate", "ReceiveInlineMessage"]
            for get in list_getted:
                url = f"https://fast-rub.ParsSource.ir/geting_button_updates/{self.token}/{get}"
                await self.set_endpoint(url, get)
            return True
        except:
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

    async def _process_messages_polling(self, time_updata_sleep: Union[float, float] = 0.5):
        while self._running:
            try:
                mes = await self.get_updates(limit=100, offset_id=self.next_offset_id)
                try:
                    self.next_offset_id = mes["next_offset_id"]
                except:
                    pass
                messages = mes["updates"]
                for message in messages:
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
                self.logger.warning(f"خطای شبکه در _process_messages_polling: {e} - انتظار 5 ثانیه...")
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"خطای ناشناخته در _process_messages_polling: {e}")

    def on_message_updates(self, filters: Optional[Filter] = None):
        """برای دریافت آپدیت‌های پیام ها به صورت وبهوک"""
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
        """برای دریافت پیام ها به صورت پولینگ"""
        self._fetch_buttons = True
        def decorator(handler):
            @wraps(handler)
            async def wrapped(update):
                try:
                    if inspect.iscoroutinefunction(handler):
                        await handler(update)
                    else:
                        handler(update)
                except Exception as e:
                    self.logger.exception(f"Error in button handler: {e}")
            self._button_handlers.append(wrapped)
            return handler
        return decorator

    def on_edit_updates(self):
        """برای دریافت ویرایش شدن پیام ها"""
        self._fetch_edit = True
        def decorator(handler: Callable[[Update], Awaitable[None]]):
            self._edit_handlers_.append(handler)
            return handler
        return decorator

    async def _process_messages_webhook(self):
        while self._running:
            response = (await self.network.request(self._on_url, timeout=self.time_out,type_send="GET")).json()
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
            response = (await self.network.request(self._button_url, timeout=self.time_out,type_send="GET")).json()
            if response and response.get('status') is True:
                results = response.get('updates', [])
                if results:
                    for result in results:
                        if result["type"] != "UpdatedMessage":
                            continue
                        update = UpdateButton(result,self)
                        for handler in self._edit_handlers:
                            self._schedule_handler(handler,update)
            else:
                await self.set_token_fast_rub()
            await asyncio.sleep(0.1)

    async def _fetch_button_updates(self):
        while self._running:
            response = (await self.network.request(self._button_url, timeout=self.time_out,type_send="GET")).json()
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
        if self._fetch_buttons:
            tasks.append(self._fetch_button_updates())
        if self._fetch_messages:
            tasks.append(self._process_messages_webhook())
        if self._fetch_messages_ and self._message_handlers_:
            tasks.append(self._process_messages_polling())
        if self._fetch_edit and self._edit_handlers_:
            tasks.append(self._process_edit_updates())
        if not tasks:
            raise ValueError("No handlers registered. Use on_message() or on_message_updates() or on_button() or on_edit_updates() first.")
        await asyncio.gather(*tasks)

    async def run(self):
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
        utils.print_time("Start", color = Colors.BLUE)
        await self._run_all()
    
    def run_sync(self):
        """اجرای اصلی بات - فقط اگر هندلرهای مربوطه ثبت شده باشند(سینک)
        
        پیشنهاد »

        از حالت ایسینک(run) استفاده کنید تا لوپ بر عهده سورس شما باشد نه کتابخانه"""
        asyncio.run(self.run())

    def stop(self):
        """خاموش کردن گرفتن آپدیت ها / off the getting updates"""
        self._running = False
