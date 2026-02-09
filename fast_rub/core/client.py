import asyncio
import inspect
from functools import wraps
from pathlib import Path
from collections import deque
from typing import (Any, Dict, List, Literal, Optional, Tuple,
                    Union)

import aiofiles
import httpx

from .async_sync import async_to_sync
from ..utils.filters import Filter
from ..network.network import Network
from ..type import Update, UpdateButton, msg_update
from ..type.errors import PollInvalid
from ..type.props import props
from ..type.models import Bot as BotModel, Chat as ChatModel
from ..utils.colors import Colors
from ..utils.logger import logging, setup_logging
from ..utils.utils import Utils
from ..utils.text_parser import TextParser


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

    time_out : float = 60.0
        تایم‌اوت درخواست‌ها (بر حسب ثانیه)

    display_welcome : bool = False
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

    main_parse_mode : Literal['Markdown', 'HTML', 'Unknown', None] = "Unknown"
        پارس مود پیش‌فرض پیام‌ها
        اگر مقدار 'Unknown' باشد، پارس مود هر متد به صورت جداگانه اعمال می‌شود

    base_urls : list = [
            "https://botapi.rubika.ir/",
            "https://messengerg2b1.iranlms.ir/"
        ]
        لیست آدرس های اصلی برای ارسال درخواست

    max_retries : int = 3
        حداکثر تعداد تلاش مجدد در خطاهای شبکه

    show_progress: Optional[bool]
        نمایش لاگ های ارسال انواع فایل 
    
    keeper_messages: int = 500
        تعداد پیام ها برای ذخیره شدن در لیست از سمت پروسس های گرفتن پیام ها برای متود گت مسیج
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
        base_urls: list = [
            "https://botapi.rubika.ir/",
            "https://messengerg2b1.iranlms.ir/"
        ],
        max_retries: int = 3,
        show_progress: Optional[bool] = None,
        keeper_messages: int = 500,
    ):
        """Client for login and setting robot / کلاینت برای لوگین و تنظیمات ربات"""
        name = Utils.name_session(name_session)
        self.name_session = name
        self.token = token
        self.save_logs = save_logs
        self.view_logs = view_logs
        self.display_welcome = display_welcome
        self.time_out = time_out
        self.user_agent = user_agent
        self.proxy = proxy
        self.show_progress = show_progress
        self.main_parse_mode: Literal['Markdown', 'HTML', 'Unknown', None] = main_parse_mode
        self.max_retries = max_retries
        self.keeper_messages = keeper_messages
        self.use_to_fastrub_webhook_on_message = use_to_fastrub_webhook_on_message
        self.use_to_fastrub_webhook_on_button = use_to_fastrub_webhook_on_button
        self.urls = base_urls
        loop = asyncio.get_running_loop()
        loop.create_task(self.start())

    async def start(self):
        """شروع کردن ربات"""
        self._running = False
        self._fetch_messages_webhook = False
        self._fetch_messages_polling = False
        self._fetch_buttons = False
        self._fetch_edit = False
        self._message_handlers_webhook = []
        self._button_handlers = []
        self._edit_handlers = []
        self._edit_handlers_ = []
        self.last = []
        self._message_handlers_polling = []
        self.next_offset_id = ""
        self.next_offset_id_ = ""
        self.next_offset_id_get_message = None
        self.geted_u = 0
        self.list_commands = []
        self.messages = deque(maxlen=self.keeper_messages)
        self.session = Utils.open_session(
            name_session=self.name_session,
            token=self.token,
            user_agent=self.user_agent,
            time_out=self.time_out,
            display_welcome=self.display_welcome,
            view_logs=self.view_logs,
            save_logs=self.save_logs
        )
        self.token: str = self.session["token"]
        self.time_out: float = self.session["time_out"]
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
        if type(self.use_to_fastrub_webhook_on_message) is str:
            self._on_url = self.use_to_fastrub_webhook_on_message
        else:
            self._on_url = f"https://fast-rub.ParsSource.ir/api/geting_button_updates/get_on?token={self.token}"
        if type(self.use_to_fastrub_webhook_on_button) is str:
            self._button_url = self.use_to_fastrub_webhook_on_button
        else:
            self._button_url = f"https://fast-rub.ParsSource.ir/api/geting_button_updates/get?token={self.token}"
        
        self.main_url = self.urls[0]
        self.network = Network(
            token=self.token,
            logger=self.logger,
            max_retries=self.max_retries,
            user_agent=self.user_agent,
            proxy=self.proxy
        )
        setup_logging(log_to_console=self.log_to_console,log_to_file=self.log_to_file)
        if self.display_welcome:
            Utils.print_time("Welcome To FastRub", color=Colors.GREEN)
        self.logger.info("سشن اماده است")


    @property
    def TOKEN(self):
        self.logger.info("توکن دریافت شد")
        return self.token

    @async_to_sync
    async def version_botapi(self) -> str:
        """getting version botapi / گرفتن نسخه بات ای پی آی"""
        response = await self.network.request(
            url=self.main_url,
            type_send="GET",
            timeout=self.time_out
        )
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
        Utils.save_dict(self.session, self.name_session)
        self.logger = setup_logging(log_to_file=saving, log_to_console=viewing)
        self.logger.info(f"logging تنظیم شد | نمایش: {viewing} | ذخیره: {saving}")

    @async_to_sync
    async def send_requests(
        self, method: str, data_: Optional[Union[Dict[str, Any], List[Any]]] = None
    ) -> dict:
        """send request to methods with retry mechanism"""
        response = await self.network.send_request(method=method,data=data_)
        return response
    
    @async_to_sync
    async def _auto_delete(
        self,
        chat_id: str,
        message_id: str,
        time_sleep: float
    ) -> props:
        await asyncio.sleep(time_sleep)
        result = await self.delete_message(
            chat_id=chat_id,
            message_id=message_id
        )
        return props(result)

    @async_to_sync
    async def auto_delete(
        self,
        chat_id:str,
        message_id:str,
        time_sleep:float,
        separate_task: bool = False
    ) -> Optional[props]:
        """auto delete message next {time_sleep} time s / حذف خودکار پیام بعد از فلان مقدار ثانیه"""
        if separate_task:
            asyncio.create_task(
                self._auto_delete(
                    chat_id=chat_id,
                    message_id=message_id,
                    time_sleep=time_sleep
                )
            )
            return None
        else:
            return await self._auto_delete(
                chat_id=chat_id,
                message_id=message_id,
                time_sleep=time_sleep
            )

    @async_to_sync
    async def get_me(self) -> BotModel:
        """geting info accont bot / گرفتن اطلاعات اکانت ربات"""
        self.logger.info("استفاده از متود get_me")
        result = await self.send_requests(method="getMe")
        return BotModel(data=result)

    @async_to_sync
    async def set_main_parse_mode(self,parse_mode: Literal['Markdown', 'HTML', 'Unknown', None]) -> None:
        """setting parse mode main / تنظیم کردن مقدار اصلی پارس مود

توجه :
در صورت تغییر مارکدوان در کلاینت یا متود ست مین پارس مود , پارس مود همیشه روی آن حالت قرار میگیرد
در صورتی که میخواهید از این حالت خارج شود و از ورودی های متود ها پیروی کند مقدار آن را در متود ست مین پارس مود برابر 'Unknown' کنید"""
        self.main_parse_mode = parse_mode

    @async_to_sync
    async def _parse_mode_text(
        self,
        text: str,
        parse_mode: Literal["Markdown","HTML","Unknown",None] = "Markdown"
    ) -> Tuple[List[Dict[str, Any]], str]:
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

    async def _manage_auto_delete(
        self,
        data: dict,
        auto_delete: Optional[int] = None
    ) -> None:
        if auto_delete:
            message_id = data["message_id"]
            chat_id = data["chat_id"]
            await self.auto_delete(
                chat_id=chat_id,
                message_id=message_id,
                time_sleep=auto_delete,
                separate_task=True
            )

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
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: list = []
    ) -> msg_update:
        """sending text to chat id / ارسال متنی به یک چت آیدی"""
        self.logger.info("استفاده از متود send_text")
        metadata, text  = await self._parse_mode_text(text, parse_mode)
        data = {
            "chat_id": chat_id,
            "text": text,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id
        }
        data = Utils.data_format(data, inline_keypad, keypad, resize_keyboard, on_time_keyboard, metadata, meta_data)
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
        meta_data: list = [],
        # file
        file: Union[str , Path , bytes , None] = None,
        name_file: Optional[str] = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif" , "Video"] = "File",
        file_id: Optional[str] = None,
        show_progress: bool = True,
        chunk_size: int = 64 * 1024,
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
            return await self.send_file_by_file_id(
                chat_id=chat_id,
                file_id=file_id,
                text=text,
                reply_to_message_id=reply_to_message_id,
                disable_notification=disable_notification,
                auto_delete=auto_delete,
                parse_mode=parse_mode,
                meta_data=meta_data,
                inline_keypad=inline_keypad,
                keypad=keypad,
                resize_keyboard=resize_keyboard,
                on_time_keyboard=on_time_keyboard
            )
        elif file:
            return await self.base_send_file(
                chat_id=chat_id,
                file=file,
                name_file=name_file,
                text=text,
                reply_to_message_id=reply_to_message_id,
                type_file=type_file,
                disable_notification=disable_notification,
                auto_delete=auto_delete,
                parse_mode=parse_mode,
                meta_data=meta_data,
                inline_keypad=inline_keypad,
                keypad=keypad,
                resize_keyboard=resize_keyboard,
                on_time_keyboard=on_time_keyboard,
                show_progress=show_progress,
                chunk_size=chunk_size
            )
        elif (not question is None) and (not options is None):
            return await self.send_poll(
                chat_id=chat_id,
                question=question,
                options=options,
                type_poll=type_poll,
                is_anonymous=is_anonymous,
                correct_option_index=correct_option_index,
                allows_multiple_answers=allows_multiple_answers,
                hint=hint,
                auto_delete=auto_delete,
                reply_to_message_id=reply_to_message_id,
                disable_notification=disable_notification
            )
        elif (not latitude is None) and (not longitude is None):
            return await self.send_location(
                chat_id=chat_id,
                latitude=latitude,
                longitude=longitude,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                auto_delete=auto_delete
            )
        elif first_name and last_name and phone_number:
            return await self.send_contact(
                chat_id=chat_id,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                reply_to_message_id=reply_to_message_id,
                disable_notificatio=disable_notification,
                auto_delete=auto_delete,
                inline_keypad=inline_keypad
            )
        elif text != None:
            return await self.send_text(
                text=text,
                chat_id=chat_id,
                inline_keypad=inline_keypad,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                auto_delete=auto_delete,
                parse_mode=parse_mode,
                keypad=keypad,
                on_time_keyboard=on_time_keyboard,
                resize_keyboard=resize_keyboard,
                meta_data=meta_data
            )
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
    ) -> ChatModel:
        """geting info chat id info / گرفتن اطلاعات های یک چت"""
        self.logger.info("استفاده از متود get_chat")
        data = {
            "chat_id": chat_id
        }
        result = await self.send_requests(
            "getChat",
            data,
        )
        return ChatModel(data=result)

    @async_to_sync
    async def get_updates(
        self,
        limit: Optional[int] = None,
        offset_id : Optional[str] = None
    ) -> props:
        """getting messages chats / گرفتن پیام های چت ها"""
        self.logger.info("استفاده از متود get_updates")
        data = {"offset_id": offset_id, "limit": limit}
        result = await self.send_requests(
            "getUpdates",
            data,
        )
        return props(result)

    @async_to_sync
    async def get_message(
        self,
        chat_id: Optional[str] = None,
        message_id: Optional[str] = None,
        limit_search: int = 100,
        search_by: Literal["messages", "get_updates", "all"] = "all"
    ) -> Optional[Update]:
        """get message by id / گرفتن پیام با آیدی"""
        if not message_id:
            raise ValueError("The Message Id not goted .")
        self.logger.info("در حال استفاده از متود get_message .")
        if search_by in ("all", "messages"):
            self.logger.info("در حال جستجو پیام در بین پیام های ذخیره شده ...")
            for msg in self.messages:
                if type(msg) is Update:
                    if msg.message_id == message_id:
                        if msg.chat_id == chat_id or chat_id is None:
                            self.logger.info("پیام در بین پیام های ذخیره شده پیدا شد !")
                            return msg
            self.logger.warn("پیام در بین پیام های ذخیره شده پیدا نشد !")
        if search_by in ("all", "get_updates"):
            self.logger.info("در حال جستجو پیام با get_updates ...")
            updates = await self.get_updates(limit_search,self.next_offset_id_get_message)
            self.geted_u = len(updates["updates"])
            for message in updates["updates"]:
                message = Update(message, self)
                if message.message_id == message_id:
                    if message.chat_id == chat_id or chat_id is None:
                        self.logger.info("پیام در get_updates پیدا شد !")
                        return message
            self.logger.warn("پیام در بین get_updates پیدا نشد !")
            if self.geted_u >= 40:
                try:
                    self.next_offset_id_get_message = updates["next_offset_id"]
                    self.geted_u = 0
                    return await self.get_message(chat_id,message_id,limit_search, "get_updates")
                except:
                    pass
        self.logger.error("پیام پیدا نشد !")
        return None

    get_message_by_id = get_message

    @async_to_sync
    async def get_messages(
        self,
        chat_id: str,
        message_id: str,
        limit_search: int = 100,
        get_befor: int = 10,
        search_by: Literal["messages", "get_updates", "all"] = "all"
    ) -> Optional[List[Update]]:
        """get messages / گرفتن پیام ها"""
        self.logger.info("در حال استفاده از متود get_messages .")
        messages = deque(maxlen=get_befor)
        if search_by in ("all", "messages"):
            self.logger.info("در حال جستجو پیام در بین پیام های ذخیره شده ...")
            for msg in self.messages:
                if type(msg) is Update:
                    messages.append(msg)
                    if msg.message_id == message_id:
                        if msg.chat_id == chat_id or chat_id is None:
                            self.logger.info("پیام ها در بین پیام های ذخیره شده پیدا شد !")
                            return messages # pyright: ignore[reportReturnType]
            messages.clear()
            self.logger.warn("پیام ها در بین پیام های ذخیره شده پیدا نشد !")
        if search_by in ("all", "get_updates"):
            self.logger.info("در حال جستجو پیام با get_updates ...")
            updates = await self.get_updates(limit_search,self.next_offset_id_get_message)
            self.geted_u = len(updates["updates"])
            for message in updates["updates"]:
                if type(message) is Update:
                    messages.append(message)
                    if message.message_id == message_id:
                        if message.chat_id == chat_id or chat_id is None:
                            self.logger.info("پیام ها در get_updates پیدا شدند !")
                            return messages # pyright: ignore[reportReturnType]
            self.logger.warn("پیام ها در بین get_updates پیدا نشدند !")
            if self.geted_u >= 40:
                try:
                    self.next_offset_id_get_message = updates["next_offset_id"]
                    self.geted_u = 0
                    return await self.get_messages(chat_id, message_id, limit_search, get_befor, "get_updates")
                except:
                    pass
        self.logger.error("پیام ها پیدا نشدند !")
        return None

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
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: list = []
    ) -> msg_update:
        """editing message text / ویرایش متن پیام"""
        self.logger.info("استفاده از متود edit_message_text")
        metadata, text  = await self._parse_mode_text(text, parse_mode)
        data = {"chat_id": chat_id, "message_id": message_id, "text": text}
        data = Utils.data_format(data, inline_keypad, metadata=metadata, meta_data=meta_data)
        result = await self.send_requests(
            "editMessageText",
            data,
        )
        result["chat_id"] = chat_id
        return msg_update(result, self)
    
    async def _auto_edit(
        self,
        chat_id: str,
        message_id: str,
        text: str,
        aute_edit: int,
        inline_keypad: Optional[list] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: list = []
    ) -> msg_update:
        await asyncio.sleep(aute_edit)
        editing = await self.edit_message_text(
            chat_id,
            message_id,
            text,
            inline_keypad,
            parse_mode,
            meta_data
        )
        return editing
    
    @async_to_sync
    async def auto_edit(
        self,
        chat_id: str,
        message_id: str,
        text: str,
        aute_edit: int,
        inline_keypad: Optional[list] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: list = [],
        separate_task: bool = False
    ) -> Optional[msg_update]:
        """auto edit message text {time_sleep} time s / ویرایش خودکار متن پیام بعد از فلان مقدار ثانیه"""
        if separate_task:
            asyncio.create_task(
                self._auto_edit(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    aute_edit=aute_edit,
                    inline_keypad=inline_keypad,
                    parse_mode=parse_mode,
                    meta_data=meta_data
                )
            )
            return None
        else:
            return await self._auto_edit(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                aute_edit=aute_edit,
                inline_keypad=inline_keypad,
                parse_mode=parse_mode,
                meta_data=meta_data
            )

    @async_to_sync
    async def delete_message(
        self,
        chat_id: str,
        message_id: str
    ) -> props:
        """delete message / پاکسازی(حذف) یک پیام"""
        self.logger.info("استفاده از متود delete_message")
        data = {
            "chat_id": chat_id,
            "message_id": message_id
        }
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
    async def set_commands(self, list_commands: Optional[list] = None) -> dict:
        """set the commands for robot / تنظیم دستورات برای ربات"""
        self.logger.info("استفاده از متود set_commands")
        result = await self.send_requests(
            "setCommands",
            {
                "bot_commands": list_commands if list_commands else self.list_commands
            }
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
    async def upload_file(
        self,
        url: str,
        file_name: str,
        file: Union[str, Path, bytes],
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024
    ) -> dict:
        """upload file to rubika server / آپلود فایل در سرور روبیکا"""
        self.logger.info("استفاده از متود upload_file")
        if not self.show_progress is None:
            show_progress = self.show_progress
        if upload_by == "aiohttp":
            response = await self.network.upload(url, file, file_name, show_progress, chunk_size)
        elif upload_by == "httpx":
            d_file = await Utils.d_file(file, file_name, self.network)
            response = await self.network.upload_httpx(url, d_file)
        else:
            raise ValueError("The 'upload_by' Arg shoud 'aiohttp' or 'httpx'.")
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
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: list = [],
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
    ) -> msg_update:
        """sending file by file id / ارسال فایل با آیدی فایل"""
        self.logger.info("استفاده از متود send_file_by_file_id")
        metadata = []
        if text:
            metadata, text  = await self._parse_mode_text(text, parse_mode)
        data = {
            "chat_id": chat_id,
            "text": text,
            "file_id": file_id,
            "reply_to_message_id": reply_to_message_id,
            "disable_notification": disable_notification,
        }
        data = Utils.data_format(data, inline_keypad,keypad,resize_keyboard,on_time_keyboard, metadata=metadata, meta_data=meta_data)
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
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: list = [],
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024
    ) -> msg_update:
        """sending file with types ['File', 'Image', 'Voice', 'Music', 'Gif' , 'Video'] / ارسال فایل با نوع های فایل و عکس و پیغام صوتی و موزیک و گیف و ویدیو"""
        self.logger.info("استفاده از متود base_send_file")
        request_file = await self.request_send_file(type_file)
        upload_url_file = request_file["upload_url"]
        if not name_file:
            name_file = Utils.format_file(type_file)
        if not name_file:
            raise ValueError("type file is invalud !")
        upload_file = await self.upload_file(
            url=upload_url_file,
            file_name=name_file,
            file=file,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size
        )
        file_id = upload_file["file_id"]
        send = await self.send_file_by_file_id(
            chat_id=chat_id,
            file_id=file_id,
            text=text,
            reply_to_message_id=reply_to_message_id,
            disable_notification=disable_notification,
            parse_mode=parse_mode,
            auto_delete=auto_delete,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard
        )
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
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: list = [],
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024
    ) -> msg_update:
        "ارسال فایل / send file"
        self.logger.info("استفاده از متود send_file")
        result = await self.base_send_file(
            chat_id=chat_id,
            file=file,
            name_file=name_file,
            text=text,
            reply_to_message_id=reply_to_message_id,
            type_file="File",
            disable_notification=disable_notification,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size
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
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: list = [],
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024
    ) -> msg_update:
        "ارسال فایل / send file"
        self.logger.info("استفاده از متود send_document")
        result = await self.base_send_file(
            chat_id=chat_id,
            file=file,
            name_file=name_file,
            text=text,
            reply_to_message_id=reply_to_message_id,
            type_file="File",
            disable_notification=disable_notification,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size
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
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: list = [],
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024
    ) -> msg_update:
        """sending image / ارسال تصویر"""
        self.logger.info("استفاده از متود send_image")
        result = await self.base_send_file(
            chat_id=chat_id,
            file=image,
            name_file=name_file,
            text=text,
            reply_to_message_id=reply_to_message_id,
            type_file="Image",
            disable_notification=disable_notification,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size
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
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: list = [],
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024
    ) -> msg_update:
        """sending video / ارسال ویدیو"""
        self.logger.info("استفاده از متود send_video")
        result = await self.base_send_file(
            chat_id=chat_id,
            file=video,
            name_file=name_file,
            text=text,
            reply_to_message_id=reply_to_message_id,
            type_file="Video",
            disable_notification=disable_notification,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size
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
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: list = [],
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024
    ) -> msg_update:
        """sending voice / ارسال ویس"""
        self.logger.info("استفاده از متود send_voice")
        result = await self.base_send_file(
            chat_id=chat_id,
            file=voice,
            name_file=name_file,
            text=text,
            reply_to_message_id=reply_to_message_id,
            type_file="Voice",
            disable_notification=disable_notification,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size
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
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: list = [],
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024
    ) -> msg_update:
        """sending music / ارسال موزیک"""
        self.logger.info("استفاده از متود send_music")
        result = await self.base_send_file(
            chat_id=chat_id,
            file=music,
            name_file=name_file,
            text=text,
            reply_to_message_id=reply_to_message_id,
            type_file="Music",
            disable_notification=disable_notification,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size
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
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: list = [],
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024
    ) -> msg_update:
        """sending gif / ارسال گیف"""
        self.logger.info("استفاده از متود send_gif")
        result = await self.base_send_file(
            chat_id=chat_id,
            file=gif,
            name_file=name_file,
            text=text,
            reply_to_message_id=reply_to_message_id,
            type_file="Gif",
            disable_notification=disable_notification,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
            meta_data=meta_data,
            inline_keypad=inline_keypad,
            keypad=keypad,
            resize_keyboard=resize_keyboard,
            on_time_keyboard=on_time_keyboard,
            upload_by=upload_by,
            show_progress=show_progress,
            chunk_size=chunk_size
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
    async def get_file(self, id_file : str) -> props:
        """getting info file / گرفتن اطلاعات فایل"""
        self.logger.info("استفاده از متود get_file")
        result = await self.send_requests("getFile", {"file_id": id_file})
        return props(result)

    @async_to_sync
    async def get_download_file_url(self, id_file : str) -> str:
        """get download url file / گرفتن آدرس دانلود فایل"""
        self.logger.info("استفاده از متود get_download_file_url")
        file = await self.get_file(id_file)
        url = file["download_url"]
        return url

    @async_to_sync
    async def download_by_url(self, url: str, path: str = "file", show_progress: bool = True) -> None:
        if not self.show_progress is None:
            show_progress = self.show_progress
        download = await self.network.download(url, path, show_progress)
        if download:
            self.logger.info("فایل دانلود شد")
        else:
            self.logger.error("خطا در دانلود فایل !")

    @async_to_sync
    async def download_file(self,id_file : str , path : str = "file", show_progress: bool = True) -> None:
        """download file / دانلود فایل"""
        self.logger.info("استفاده از متود download_file")
        url = await self.get_download_file_url(id_file)
        await self.download_by_url(url, path, show_progress)

    @async_to_sync
    async def set_endpoint(self, url: str, type: Literal["ReceiveUpdate", "GetSelectionItem", "ReceiveInlineMessage", "ReceiveQuery", "SearchSelectionItems"]) -> props:
        """set endpoint url / تنظیم ادرس اند پوینت"""
        self.logger.info("استفاده از متود set_endpoint")
        result = await self.send_requests(
            "updateBotEndpoints", {"url": url, "type": type}
        )
        return props(result)
    
    update_end_point = set_endpoint
    update_endpoint = set_endpoint

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
    
    @async_to_sync
    async def ban_chat_member(
        self,
        chat_id: str,
        user_id: str
    ) -> props:
        """ban member in chat / بن کردن کاربر در چت"""
        data = {
            "chat_id": chat_id,
            "user_id": user_id
        }
        result = await self.send_requests("banChatMember", data)
        return props(result)

    @async_to_sync
    async def unban_chat_member(
        self,
        chat_id: str,
        user_id: str
    ) -> props:
        """un ban member in chat / آنبن کردن کاربر در چت"""
        data = {
            "chat_id": chat_id,
            "user_id": user_id
        }
        result = await self.send_requests("unbanChatMember", data)
        return props(result)
    
    ban_member = ban_chat_member
    unban_member = unban_chat_member
    ban_group_member = ban_chat_member
    unban_group_member = unban_chat_member
    ban_channel_member = ban_chat_member
    unban_channel_member = unban_chat_member

    # decorators

    def _schedule_handler(self, handler, update):
        async def _wrapped():
            try:
                await handler(update)
            except Exception:
                self.logger.exception("Error in handler")
        asyncio.create_task(_wrapped())

    def on_message(self,
        filters: Optional[Filter] = None,
        edited_messages: Literal[False, True, "both"] = False,
        deleted_messages: Literal[False, True, "both"] = False
    ):
        """برای دریافت پیام‌های معمولی"""
        self._fetch_messages_polling = True
        def decorator(handler):
            @wraps(handler)
            async def wrapped(update):
                try:
                    if filters is not None:
                        try:
                            if not filters(update):
                                return
                        except Exception as e:
                            print(f"[FILTER ERROR] {filters} -> {e}")
                            return

                    if inspect.iscoroutinefunction(handler):
                        return await handler(update)
                    else:
                        return handler(update)

                except Exception as e:
                    print(f"[HANDLER ERROR] {handler.__name__} -> {e}")
                    return None

            handler_info = {
                "handler": wrapped,
                "filters": filters,
                "edited_messages": edited_messages,
                "deleted_messages": deleted_messages
            }
            self._message_handlers_polling.append(handler_info)
            return handler
        return decorator

    async def _process_messages_polling(self):
        while self._running:
            try:
                mes = await self.get_updates(limit=100, offset_id=self.next_offset_id)
                try:
                    self.next_offset_id = mes["next_offset_id"]
                except:
                    pass
                messages = mes["updates"]
                for message in messages:
                    if message["type"] not in ["NewMessage", "UpdatedMessage", "RemoveMessage"]:
                        continue
                    update = Update(message, self)
                    is_edited = message["type"] == "UpdatedMessage"
                    is_deleted = message["type"] = "RemoveMessage"
                    for handler_info in self._message_handlers_polling:
                        handler = handler_info["handler"]
                        edited_messages_option = handler_info["edited_messages"]
                        deleted_messages_option = handler_info["deleted_messages"]
                        if edited_messages_option == False and is_edited:
                            continue
                        elif edited_messages_option == True and not is_edited:
                            continue
                        if deleted_messages_option == False and is_deleted:
                            continue
                        elif deleted_messages_option == True and not is_deleted:
                            continue
                        filters = handler_info["filters"]
                        if filters is not None:
                            try:
                                if not filters(update):
                                    continue
                            except Exception as e:
                                print(f"[FILTER ERROR] {filters} -> {e}")
                                continue
                        self._schedule_handler(handler, update)
                    if not is_edited and not is_deleted:
                        self.messages.append(update)
            except (httpx.ReadError, httpx.ConnectError) as e:
                self.logger.warning(f"خطای شبکه در _process_messages_polling: {e} - انتظار 5 ثانیه...")
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"خطای ناشناخته در _process_messages_polling: {e}")


    def on_message_updates(
        self,
        filters: Optional[Filter] = None,
        edited_messages: Literal[False, True, "both"] = False,
        deleted_messages: Literal[False, True, "both"] = False
    ):
        """گرفتن پیام ها با وبهوک"""
        self._fetch_messages = True

        def decorator(handler):
            @wraps(handler)
            async def wrapped(update):
                try:
                    if filters is not None:
                        try:
                            if not filters(update):
                                return
                        except Exception as e:
                            print(f"[FILTER ERROR] {filters} -> {e}")
                            return

                    if inspect.iscoroutinefunction(handler):
                        return await handler(update)
                    else:
                        return handler(update)

                except Exception as e:
                    print(f"[HANDLER ERROR] {handler.__name__} -> {e}")
                    return None

            handler_info = {
                "handler": wrapped,
                "filters": filters,
                "edited_messages": edited_messages,
                "deleted_messages": deleted_messages
            }
            
            self._message_handlers_webhook.append(handler_info)
            return wrapped

        return decorator


    def on_edit_updates(self, filters: Optional[Filter] = None):
        """برای دریافت ویرایش شدن پیام ها"""
        return self.on_message_updates(filters=filters, edited_messages=True)
    
    def on_delete_updates(self, filters: Optional[Filter] = None):
        """برای دریافت پیام های حذف شده"""
        return self.on_message_updates(filters=filters, deleted_messages=True)

    def on_all_message_updates(self, filters: Optional[Filter] = None):
        """گرفتن تمامی پیام ها(ارسال شده/ویرایش شده/حذف شده)"""
        return self.on_message_updates(filters=filters, edited_messages="both", deleted_messages="both")
    

    def on_edit(self, filters: Optional[Filter] = None):
        """برای دریافت ویرایش شدن پیام ها"""
        return self.on_message(filters=filters, edited_messages=True)
    
    def on_delete(self, filters: Optional[Filter] = None):
        """برای دریافت پیام های حذف شده"""
        return self.on_message(filters=filters, deleted_messages=True)

    def on_all_message(self, filters: Optional[Filter] = None):
        """گرفتن تمامی پیام ها(ارسال شده/ویرایش شده/حذف شده)"""
        return self.on_message(filters=filters, edited_messages="both", deleted_messages="both")


    async def _process_messages_webhook(self):
        while self._running:
            response = await self.network.request(self._on_url, timeout=self.time_out,type_send="GET")
            result = response.json()
            if result and result.get('status') is True and response.status_code == 200:
                results = result.get('updates', [])
                if results:
                    for result in results:
                        if result["type"] not in ["NewMessage", "UpdatedMessage", "RemovedMessage"]:
                            continue
                        update = Update(result, self)
                        is_edited = result["type"] == "UpdatedMessage"
                        is_deleted = result["type"] = "RemovedMessage"
                        for handler_info in self._message_handlers_webhook:
                            handler = handler_info["handler"]
                            edited_messages_option = handler_info["edited_messages"]
                            deleted_messages_option = handler_info["deleted_messages"]
                            if edited_messages_option == False and is_edited:
                                continue
                            elif edited_messages_option == True and not is_edited:
                                continue
                            if deleted_messages_option == False and is_deleted:
                                continue
                            elif deleted_messages_option == True and not is_deleted:
                                continue
                            filters = handler_info["filters"]
                            if filters is not None:
                                try:
                                    if not filters(update):
                                        continue
                                except Exception as e:
                                    print(f"[FILTER ERROR] {filters} -> {e}")
                                    continue
                            self._schedule_handler(handler, update)
                        if not is_edited and not is_deleted:
                            self.messages.append(update)
            else:
                await self.set_token_fast_rub()
            await asyncio.sleep(0.1)

    # Inline Button

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

    async def _fetch_button_updates(self):
        while self._running:
            response = await self.network.request(self._button_url, timeout=self.time_out,type_send="GET")
            result = response.json()
            if result and result.get('status') is True:
                results = result.get('updates', [])
                if results:
                    for result in results:
                        update = UpdateButton(result,self)
                        for handler in self._button_handlers:
                            self._schedule_handler(handler,update)
            else:
                await self.set_token_fast_rub()
            await asyncio.sleep(0.1)
    
    # Run

    async def _run_all(self):
        tasks = []
        if self._fetch_buttons:
            tasks.append(self._fetch_button_updates())
        if self._fetch_messages_webhook:
            tasks.append(self._process_messages_webhook())
        if self._fetch_messages_polling and self._message_handlers_polling:
            tasks.append(self._process_messages_polling())
        if not tasks:
            raise ValueError("No handlers registered. Use on_message() or on_message_updates() or on_button() or on_edit_updates() first.")
        try:
            mes = await self.get_updates(limit=100)
            self.next_offset_id_get_message = mes["next_offset_id"]
        except:
            pass
        await asyncio.gather(*tasks)

    async def run(self):
        """اجرای اصلی بات - فقط اگر هندلرهای مربوطه ثبت شده باشند"""
        if not (self._fetch_messages_webhook or self._fetch_buttons or self._fetch_messages_polling or self._fetch_edit):
            raise ValueError("No update types selected. Use on_message() or on_message_updates() or on_button() or on_edit_updates() first.")
        
        if (self._fetch_messages_webhook and not self._message_handlers_webhook) or (self._fetch_messages_polling and not self._message_handlers_polling):
            raise ValueError("Message handlers registered but no message callbacks defined.")
        
        if self._fetch_buttons and not self._button_handlers:
            raise ValueError("Button handlers registered but no button callbacks defined.")

        if self._fetch_edit and not self._edit_handlers_:
            raise ValueError("Edit handlers registered but no message callbacks defined.")

        self._running = True
        await self.start()
        self.logger.info("ربات در حال دریافت پیام ها")
        Utils.print_time("Start", color = Colors.BLUE)
        await self._run_all()
    
    def run_sync(self):
        """اجرای اصلی بات - فقط اگر هندلرهای مربوطه ثبت شده باشند(سینک)
        
        پیشنهاد »

        از حالت ایسینک(run) استفاده کنید تا لوپ بر عهده سورس شما باشد نه کتابخانه"""
        asyncio.run(self.run())

    def stop(
        self,
        type_stop: Literal["all", "running"] = "running"
    ):
        """خاموش کردن گرفتن آپدیت ها / off the getting updates"""
        self.logger.info("ربات متوقف شد !")
        self._running = False
        if type_stop == "all":
            del self.network
            del self.session
            del self.token
            del self.name_session
            del self.logger
            del self._on_url
            del self._button_url
            del self.urls
            del self.main_url
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop(type_stop="all")
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.stop(type_stop="all")


Robot = Client
Bot = Client
BotApi = Client
BotApiClient = Client
