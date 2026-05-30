import asyncio
import inspect
import logging
import time
from functools import wraps
from pathlib import Path
from collections import deque
from typing import (Any, Dict, List, Literal, Optional, Tuple,
                    Union, Callable, TYPE_CHECKING)
from traceback import format_exc

import aiofiles
import httpx

from .async_sync import wrap_all_async_methods
from .middleware import MiddlewareManager
from .plugins import PluginManager
from .webhook_server import WebhookServer
from .background import BackgroundManager
from ..utils.filters import Filter
from ..network.network import Network
from ..type import Update, UpdateButton, msg_update
from ..type.errors import PollInvalid
from ..type.props import props
from ..type.models import Bot as BotModel, Chat as ChatModel
from ..type import WebhookConfig
from ..utils.colors import Colors
from ..utils.logger import logging, setup_logging
from ..utils.utils import Utils
from ..utils.text_parser import TextParser
from ..utils.wait_manager import WaitManager
from ..db.session import Session
from ..db.message_keeper import MessageKeeper
from ..pyrubi import Client as PyrubiClient
if TYPE_CHECKING:
    from .conversation import Conversation

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

    main_parse_mode : Literal['Markdown', 'HTML', 'Null', None] = "Null"
        پارس مود پیش‌فرض پیام‌ها
        اگر مقدار 'Null' باشد، پارس مود هر متد به صورت جداگانه اعمال می‌شود

    base_urls : list = [
            "https://botapi.rubika.ir/", # "https://messengerg2b1.iranlms.ir/"
        ]
        لیست آدرس های اصلی برای ارسال درخواست

    max_retries : int = 3
        حداکثر تعداد تلاش مجدد در خطاهای شبکه

    show_progress: Optional[bool]
        نمایش لاگ های ارسال انواع فایل 
    
    keeper_messages_ram: int = 500
        تعداد پیام ها برای ذخیره شدن در لیست از سمت پروسس های گرفتن پیام ها برای متود گت مسیج در رم
    
    keeper_messages_db: int = 500
        تعداد پیام ها برای ذخیره شدن در لیست از سمت پروسس های گرفتن پیام ها برای متود گت مسیج در دیتابیس
    
    offset_id: Optional[str] = None
        آفست آیدی برای گرفتن پیام های پولینگ
    
    save_offset_id: bool = True
        ذخیره شدن آفست آیدی در دیتابیس
    
    run_start: bool = True
        اجرا کردن متود start با asyncio.run - توصیه می شود متود start را در محیط کد خود اجرا کنید و این مقدار با نادرست 
    
    wait_manager: Optional[WaitManager] = None
        مدیریت ایستادن بین ارسال درخواست ها
    
    defult_wait: Optional[float] = None
        مقدار پیشفرض ایستادن بین درخواست ها
    
    webhook: Optional[WebhookConfig] = None
        تنظیمات وبهوک
    
    poll_interval: float = 0.0
        زمان ایستادن بین گرفتن پیام ها
    
    ssl_verify: bool = True
        احراز هویت SSL
    """
    # ═══════════════════════════════════
    # region 🚀 Start & Stop | شروع و توقف
    # ═══════════════════════════════════
    def __init__(
        self,
        name_session: str,
        token: Optional[str] = None,
        user_agent: Optional[str] = None,
        time_out: float = 60.0,
        display_welcome: bool = False,
        # use_to_fastrub_webhook_on_message: Union[str,bool] = True,
        # use_to_fastrub_webhook_on_button: Union[str,bool] = True,
        save_logs: Optional[bool] = None,
        view_logs: Optional[bool] = None,
        proxy: Optional[str] = None,
        main_parse_mode: Literal['Markdown', 'HTML', "Null", None] = "Null",
        base_urls: list = [
            "https://botapi.rubika.ir/",
            # "https://messengerg2b1.iranlms.ir/"
        ],
        max_retries: int = 3,
        show_progress: Optional[bool] = None,
        keeper_messages_ram: int = 5_000,
        keeper_messages_db: int = 0,
        logger: Optional[logging.Logger] = None,
        offset_id: Optional[str] = None,
        save_offset_id: bool = True,
        run_start: bool = True,
        wait_manager: Optional[WaitManager] = None,
        defult_wait: Optional[float] = None,
        webhook: Optional[WebhookConfig] = None,
        poll_interval: float = 0.0,
        ssl_verify: bool = True,
    ):
        """Client for login and setting robot / کلاینت برای لوگین و تنظیمات ربات"""
        self.name_session = name_session
        self.token = token # pyright: ignore[reportAttributeAccessIssue]
        self.save_logs = save_logs
        self.view_logs = view_logs
        self.display_welcome = display_welcome
        self.time_out = time_out
        self.user_agent = user_agent
        self.proxy = proxy
        self.show_progress = show_progress
        self.main_parse_mode: Literal['Markdown', 'HTML', 'Null', None] = main_parse_mode
        self.max_retries = max_retries
        self.keeper_messages_ram = keeper_messages_ram
        # self.use_to_fastrub_webhook_on_message = use_to_fastrub_webhook_on_message
        # self.use_to_fastrub_webhook_on_button = use_to_fastrub_webhook_on_button
        self.urls: List[str] = base_urls
        self.offset_id = offset_id
        self.save_offset_id = save_offset_id
        self.keeper_messages_db = keeper_messages_db
        self.wait_manager = wait_manager
        self.defult_wait = defult_wait
        self._on_ready_handlers = []
        self._on_start_handlers = []
        from .conversation import ConversationManager
        self._conversation_manager = ConversationManager()
        self.webhook = webhook
        self.poll_interval = poll_interval
        self.ssl_verify = ssl_verify
        self._background = BackgroundManager(self.logger)
        self.state = {}
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger("fast_rub")
        if run_start:
            asyncio.run(self.start())

    
    async def start(self):
        """تنظیمات شروع کردن ربات"""
        self._running = False
        self._fetch_messages_webhook = False
        self._fetch_messages_polling = False
        self._fetch_buttons = False
        self._fetch_edit = False
        self._message_handlers_webhook = []
        self._button_handlers = []
        self._edit_handlers = []
        self._edit_handlers_ = []
        self._message_handlers_polling = []
        self.next_offset_id_get_message = None
        self.geted_u = 0
        self.list_commands = []
        self.messages = deque(maxlen=self.keeper_messages_ram)
        self.messages_db = MessageKeeper(
            db_path=self.name_session,
            number_keeper=self.keeper_messages_db
        )
        self.session = await Session.open(
            name=self.name_session,
            token=self.token,
            user_agent=self.user_agent,
            time_out=self.time_out,
            display_welcome=self.display_welcome,
            view_logs=self.view_logs,
            save_logs=self.save_logs,
            offset_id=self.offset_id,
            save_offset_id=self.save_offset_id
        )
        self.token: str = self.session.token
        self.time_out = self.session.time_out
        self.user_agent = self.session.user_agent
        try:
            self.log_to_file = self.session.save_logs
            self.log_to_console = self.session.view_logs
        except KeyError:
            pass
        if self.log_to_file is None:
            self.log_to_file = False
        if self.log_to_console is None:
            self.log_to_console = False
        self.exists_wait_manager = bool(self.wait_manager)
        # if type(self.use_to_fastrub_webhook_on_message) is str:
        #     self._on_url = self.use_to_fastrub_webhook_on_message
        # else:
        #     self._on_url = f"https://fast-rub.ParsSource.ir/api/geting_button_updates/get_on?token={self.token}"
        # if type(self.use_to_fastrub_webhook_on_button) is str:
        #     self._button_url = self.use_to_fastrub_webhook_on_button
        # else:
        #     self._button_url = f"https://fast-rub.ParsSource.ir/api/geting_button_updates/get?token={self.token}"
        self.main_url = self.urls[0]
        self.urls = Utils.format_url(self.urls)
        self.next_offset_id = self.session.offset_id
        self.save_offset_id = self.session.save_offset_id
        self.network = Network(
            token=self.token,
            logger=self.logger,
            max_retries=self.max_retries,
            user_agent=self.user_agent,
            proxy=self.proxy,
            base_urls=self.urls,
            ssl_verify=self.ssl_verify,
        )
        self._webhook_server = None
        if self.webhook:
            self._webhook_server = WebhookServer(client=self, config=self.webhook, logger=self.logger)
        self._middleware_manager = MiddlewareManager(self.logger)
        self._on_error_handlers = []
        self._on_run_handlers = []
        self._on_live_handlers = []
        self._is_live = False
        self._on_shutdown_handlers = []
        setup_logging(
            log_to_console=self.log_to_console,
            log_to_file=self.log_to_file
        )
        await self._process_on_start()
        await self._process_on_ready()
        if self.display_welcome:
            Utils.print_time("Welcome To FastRub", color=Colors.GREEN)
        self.logger.info("سشن اماده است")

    async def _run_all(self):
        tasks = []
        
        if self._webhook_server and (self._message_handlers_webhook or self._button_handlers):
            tasks.append(self._webhook_server.start())
        
        if self._fetch_messages_polling and self._message_handlers_polling:
            tasks.append(self._process_messages_polling())
        
        if not tasks:
            raise ValueError("No handlers registered. Use decorator first.")
        
        try:
            messages = await self.get_updates(limit=100)
            self.next_offset_id_get_message = messages["next_offset_id"]
        except KeyError:
            pass
        
        if tasks:
            await self._process_on_run()
        
        await asyncio.gather(*tasks)

    async def run(
        self,
        poll_interval: float = 0.0
    ):
        """اجرای اصلی بات - فقط اگر هندلرهای مربوطه ثبت شده باشند"""
        if not (self._fetch_messages_webhook or self._fetch_buttons or self._fetch_messages_polling or self._fetch_edit):
            raise ValueError("No update types selected. Use decorator first.")
        
        if (self._fetch_messages_webhook and not self._message_handlers_webhook) or (self._fetch_messages_polling and not self._message_handlers_polling):
            raise ValueError("Message handlers registered but no message callbacks defined.")
        
        if self._fetch_buttons and not self._button_handlers:
            raise ValueError("Button handlers registered but no button callbacks defined.")

        if self._fetch_edit and not (self._message_handlers_polling or self._message_handlers_webhook):
            raise ValueError("Edit handlers registered but no message callbacks defined.")

        if poll_interval != 0.0:
            self.poll_interval = poll_interval

        self._running = True
        self.logger.info("ربات در حال دریافت پیام ها")
        if self.display_welcome:
            Utils.print_time("Start", color=Colors.BLUE)
        await self._run_all()
    
    run_sync = run

    async def close(
        self,
        type_stop: Literal["all", "running"] = "all"
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
            # del self._on_url
            # del self._button_url
            del self.urls
            del self.main_url
            del self.session
            await self._process_on_shutdown()

    async def cloes(self):
        self.logger.warning("The 'warn' method is deprecated, "
            "use 'warning' instead", DeprecationWarning, 2)
        return await self.close()

    async def stop(
        self
    ):
        """stop getting updates / متوقف شدن گرفتن آپدیت ها"""
        await self.close(type_stop="running")
    
    def __enter__(self):
        self.start() # type: ignore
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() # type: ignore
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @property
    def TOKEN(self):
        self.logger.info("توکن دریافت شد")
        return self.token
    
    @TOKEN.setter
    def TOKEN(
        self,
        value: str
    ):
        self.token = value
        self.logger.info("توکن تغییر کرد")
    
    # endregion

    # ═══════════════════════════════════
    # region ⚙️ Internal Utils | متدهای داخلی
    # ═══════════════════════════════════

    async def _send_req(
        self,
        method: str,
        data: Optional[Dict[str, Any]] = None
    ) -> dict:
        response = await self.network.send_request(
            method=method,
            data=data
        )
        return response
    
    
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
    
    
    async def _parse_mode_text(
        self,
        text: str,
        parse_mode: Literal["Markdown","HTML","Null",None] = "Markdown"
    ) -> Tuple[List[Dict[str, Any]], str]:
        """setting parse mode text / تنظیم پارس مود متن"""
        if self.main_parse_mode != "Null":
            parse_mode = self.main_parse_mode
        if parse_mode == "Markdown":
            data = TextParser.checkMarkdown(text)
            return data
        elif parse_mode == "HTML":
            data = TextParser.checkHTML(text)
            return data
        return [], text

    async def _wait(
        self,
        wait_send: Optional[float] = None
    ) -> Optional[float]:
        return wait_send or (
            self.wait_manager.get_time() if self.wait_manager else None
        ) or self.defult_wait

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
    
    async def _auto_edit(
        self,
        chat_id: str,
        message_id: str,
        text: str,
        auto_edit: int,
        inline_keypad: Optional[list] = None,
        parse_mode: Literal["Markdown", "HTML", None] = "Markdown",
        meta_data: list = []
    ) -> msg_update:
        await asyncio.sleep(auto_edit)
        editing = await self.edit_message_text(
            chat_id,
            message_id,
            text,
            inline_keypad,
            parse_mode,
            meta_data
        )
        return editing # type: ignore
    
    def _schedule_handler(
        self,
        handler,
        update: Union[Update, UpdateButton]
    ):
        async def _run_handler(
            upd: Union[Update, UpdateButton]
        ):
            try:
                await handler(upd)
            except Exception as e:
                await self._process_on_error(
                    e=e,
                    update=upd
                )
        async def _wrapped():
            if self._middleware_manager.count > 0 and isinstance(update, Update):
                await self._middleware_manager.execute(update, _run_handler)
            else:
                await _run_handler(update)
        asyncio.create_task(_wrapped())
    
    # endregion

    # ═══════════════════════════════════
    # region 👤 Chat & User | مدیریت کاربر و چت
    # ═══════════════════════════════════

    
    async def get_me(
        self
    ) -> BotModel:
        """geting info accont bot / گرفتن اطلاعات اکانت ربات"""
        self.logger.info("استفاده از متود get_me")
        result = await self._send_req(method="getMe")
        bot = result["bot"]
        return BotModel(data=bot)

    
    async def get_chat(
        self,
        chat_id: str
    ) -> ChatModel:
        """geting info chat id info / گرفتن اطلاعات های یک چت"""
        self.logger.info("استفاده از متود get_chat")
        Utils.check_id_raise(chat_id)
        data = {
            "chat_id": chat_id
        }
        result = await self._send_req(
            "getChat",
            data,
        )
        return ChatModel(data=result["chat"])

    
    async def ban_chat_member(
        self,
        chat_id: str,
        user_id: str,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[props, asyncio.Task[props]]:
        """ban member in chat / بن کردن کاربر در چت"""
        async def _active():
            Utils.check_id_raise(chat_id)
            Utils.check_id_raise(user_id)
            if self.wait_manager and self.wait_manager.track_after_send:
                _chat_id = chat_id if self.wait_manager.per_chat else None
                self.wait_manager.add_traffic(channel="banning", chat_id=_chat_id)
            wait_manager = wait_send or (self.wait_manager.get_time("banning") if self.wait_manager else None)
            if wait_manager:
                await asyncio.sleep(wait_manager)
            data = {
                "chat_id": chat_id,
                "user_id": user_id
            }
            result = await self._send_req("banChatMember", data)
            return props(result)
        if return_task:
            return asyncio.create_task(_active())
        else:
            return await _active()

    
    async def unban_chat_member(
        self,
        chat_id: str,
        user_id: str,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[props, asyncio.Task[props]]:
        """un ban member in chat / آنبن کردن کاربر در چت"""
        async def _active():
            Utils.check_id_raise(chat_id)
            Utils.check_id_raise(user_id)
            if self.wait_manager and self.wait_manager.track_after_send:
                _chat_id = chat_id if self.wait_manager.per_chat else None
                self.wait_manager.add_traffic(channel="banning", chat_id=_chat_id)
            wait_manager = wait_send or (self.wait_manager.get_time("banning") if self.wait_manager else None)
            if wait_manager:
                await asyncio.sleep(wait_manager)
            data = {
                "chat_id": chat_id,
                "user_id": user_id
            }
            result = await self._send_req("unbanChatMember", data)
            return props(result)
        if return_task:
            return asyncio.create_task(_active())
        else:
            return await _active()
    
    ban_member = ban_chat_member
    unban_member = unban_chat_member
    ban_group_member = ban_chat_member
    unban_group_member = unban_chat_member
    ban_channel_member = ban_chat_member
    unban_channel_member = unban_chat_member

    
    async def check_join(
        self,
        chat_id: str,
        guid_channel: str,
        client: PyrubiClient
    ) -> bool:
        user = await self.get_chat(chat_id)
        search_by = user.username
        if not search_by:
            search_by = user.first_name
        info_members: dict = await client.get_all_members(
            object_guid=guid_channel,
            search_text=search_by
        ) # type: ignore
        members: list[dict] = info_members.get('in_chat_members', [])
        return any((m.get('username') == user.username or m.get("first_name") == user.first_name) for m in members)

    
    async def add_commands(self, command: str, description: str) -> None:
        """add command to commands list / افزودن دستور به لیست دستورات"""
        self.logger.info("استفاده از متود add_commands")
        self.list_commands.append(
            {
                "command": command.replace("/", ""),
                "description": description
            }
        )

    
    async def set_commands(
        self,
        list_commands: Optional[list] = None
    ) -> dict:
        """set the commands for robot / تنظیم دستورات برای ربات"""
        self.logger.info("استفاده از متود set_commands")
        result = await self._send_req(
            "setCommands",
            {
                "bot_commands": list_commands if list_commands else self.list_commands
            }
        )
        return result
    
    
    async def delete_commands(
        self
    ) -> dict:
        """clear the commands list / پاکسازی لیست دستورات"""
        self.logger.info("استفاده از متود delete_commands")
        self.list_commands = []
        result = await self.set_commands()
        return result

    # endregion

    # ═══════════════════════════════════
    # region 📩 File Download | دانلود فایل
    # ═══════════════════════════════════

    
    async def download_me_profile(
        self,
        name_file: str = "bot_avatar.jpg",
        show_progress: bool = True,
        wait_send: float | None = None,
        return_task: bool = False
    ) -> bool:
        self.logger.info("استفاده از متود download_me_profile")
        bot = await self.get_me()
        avator_file_id = bot.avatar_file_id
        if avator_file_id:
            await self.download_file(
                id_file=avator_file_id,
                path=name_file,
                show_progress=show_progress,
                wait_send=wait_send,
                return_task=return_task
            )
            self.logger.info("پروفایل ربات دانلود شد")
            return True
        return False

    
    async def get_file(
        self,
        id_file: str
    ) -> props:
        """getting info file / گرفتن اطلاعات فایل"""
        self.logger.info("استفاده از متود get_file")
        result = await self._send_req("getFile", {"file_id": id_file})
        return props(result)

    
    async def get_download_file_url(
        self,
        id_file: str,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[str, asyncio.Task[str]]:
        """get download url file / گرفتن آدرس دانلود فایل"""
        self.logger.info("استفاده از متود get_download_file_url")
        async def _active():
            if self.wait_manager and self.wait_manager.track_after_send:
                self.wait_manager.add_traffic(channel="uploading")
            wait_manager = wait_send or (self.wait_manager.get_time("uploading") if self.wait_manager else None)
            if wait_manager:
                await asyncio.sleep(wait_manager)
            file = await self.get_file(id_file)
            url = file["download_url"]
            return url
        if return_task:
            return asyncio.create_task(_active())
        else:
            return await _active()

    
    async def download_by_url(
        self,
        url: str,
        path: str = "file",
        show_progress: bool = True
    ) -> None:
        if not self.show_progress is None:
            show_progress = self.show_progress
        download = await self.network.download(url, path, show_progress)
        if download:
            self.logger.info("فایل دانلود شد")
        else:
            self.logger.error("خطا در دانلود فایل !")

    
    async def download_file(
        self,
        id_file: str ,
        path: str = "file",
        show_progress: bool = True,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> None:
        """download file / دانلود فایل"""
        self.logger.info("استفاده از متود download_file")
        async def _active():
            if self.wait_manager and self.wait_manager.track_after_send:
                self.wait_manager.add_traffic(channel="sending")
            wait_manager = wait_send or (self.wait_manager.get_time("uploading") if self.wait_manager else None)
            if wait_manager:
                await asyncio.sleep(wait_manager)
            url = await self.get_download_file_url(id_file)
            await self.download_by_url(url, path, show_progress) # type: ignore
        if return_task:
            asyncio.create_task(_active())
        else:
            await _active()

    # endregion

    # ═══════════════════════════════════
    # region 📩 Sending Messages | ارسال پیام
    # ═══════════════════════════════════

    
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
        parse_mode: Literal["Markdown", "HTML", None] = "Markdown",
        meta_data: Optional[list] = None,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
        """sending text to chat id / ارسال متنی به یک چت آیدی"""
        self.logger.info("استفاده از متود send_text")
        async def _active():
            Utils.check_id_raise(chat_id)
            if self.wait_manager and self.wait_manager.track_after_send:
                _chat_id = chat_id if self.wait_manager.per_chat else None
                self.wait_manager.add_traffic(channel="sending", chat_id=_chat_id)
            wait_manager = await self._wait(wait_send)
            if wait_manager:
                await asyncio.sleep(wait_manager)
            _meta_data = meta_data if meta_data is not None else []
            _text = text
            metadata, _text  = await self._parse_mode_text(_text, parse_mode)
            data = {
                "chat_id": chat_id,
                "text": _text,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id
            }
            data = Utils.data_format(data, inline_keypad, keypad, resize_keyboard, on_time_keyboard, metadata, _meta_data)
            result = await self._send_req(
                "sendMessage",
                data,
            )
            result["chat_id"] = chat_id
            await self._manage_auto_delete(result, auto_delete)
            return msg_update(result, self)
        
        if return_task:
            return asyncio.create_task(_active())
        else:
            return await _active()

    
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
        parse_mode: Literal["Markdown", "HTML", None] = "Markdown",
        meta_data: Optional[list] = None,
        wait_send: Optional[float] = None,
        return_task: bool = False,
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
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
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
                on_time_keyboard=on_time_keyboard,
                wait_send=wait_send,
                return_task=return_task
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
                chunk_size=chunk_size,
                wait_send=wait_send,
                return_task=return_task
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
                disable_notification=disable_notification,
                wait_send=wait_send,
                return_task=return_task
            )
        elif (not latitude is None) and (not longitude is None):
            return await self.send_location(
                chat_id=chat_id,
                latitude=latitude,
                longitude=longitude,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                auto_delete=auto_delete,
                wait_send=wait_send,
                return_task=return_task
            )
        elif first_name and last_name and phone_number:
            return await self.send_contact(
                chat_id=chat_id,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                reply_to_message_id=reply_to_message_id,
                disable_notification=disable_notification,
                auto_delete=auto_delete,
                inline_keypad=inline_keypad,
                wait_send=wait_send,
                return_task=return_task
            )
        elif not text is None:
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
                meta_data=meta_data,
                wait_send=wait_send,
                return_task=return_task
            )
        raise ValueError("Please Write The Args !")

    
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
        auto_delete: Optional[int] = None,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
        """sending poll to chat id / ارسال نظرسنجی به یک چت آیدی"""
        self.logger.info("استفاده از متود send_poll")
        async def _active():
            Utils.check_id_raise(chat_id)
            if len(options) > 10:
                raise PollInvalid("len for options is logner from 10 option")
            wait_manager = await self._wait(wait_send)
            if self.wait_manager and self.wait_manager.track_after_send:
                _chat_id = chat_id if self.wait_manager.per_chat else None
                self.wait_manager.add_traffic(channel="sending", chat_id=_chat_id)
            if wait_manager:
                await asyncio.sleep(wait_manager)
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
            result = await self._send_req(
                "sendPoll",
                data,
            )
            result["chat_id"] = chat_id
            await self._manage_auto_delete(result, auto_delete)
            return msg_update(result, self)
        if return_task:
            return asyncio.create_task(_active())
        else:
            return await _active()

    
    async def send_location(
        self,
        chat_id: str,
        latitude: str,
        longitude: str,
        chat_keypad : Optional[str] = None,
        disable_notification: Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
        chat_keypad_type: Optional[str] = None,
        auto_delete: Optional[int] = None,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
        """sending location to chat id / ارسال لوکیشن(موقعیت مکانی) به یک چت آیدی"""
        self.logger.info("استفاده از متود send_location")
        async def _active():
            Utils.check_id_raise(chat_id)
            if self.wait_manager and self.wait_manager.track_after_send:
                _chat_id = chat_id if self.wait_manager.per_chat else None
                self.wait_manager.add_traffic(channel="sending", chat_id=_chat_id)
            wait_manager = await self._wait(wait_send)
            if wait_manager:
                await asyncio.sleep(wait_manager)
            data = {
                "chat_id": chat_id,
                "latitude": latitude,
                "longitude": longitude,
                "chat_keypad": chat_keypad,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "chat_keypad_type": chat_keypad_type,
            }
            result = await self._send_req(
                "sendLocation",
                data,
            )
            result["chat_id"] = chat_id
            await self._manage_auto_delete(result, auto_delete)
            return msg_update(result, self)
        if return_task:
            return asyncio.create_task(_active())
        else:
            return await _active()

    
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
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
        """sending contact to chat id / ارسال مخاطب به یک چت آیدی"""
        self.logger.info("استفاده از متود send_contact")
        async def _active():
            Utils.check_id_raise(chat_id)
            if self.wait_manager and self.wait_manager.track_after_send:
                _chat_id = chat_id if self.wait_manager.per_chat else None
                self.wait_manager.add_traffic(channel="sending", chat_id=_chat_id)
            wait_manager = await self._wait(wait_send)
            if wait_manager:
                await asyncio.sleep(wait_manager)
            data = {
                "chat_id": chat_id,
                "first_name": first_name,
                "last_name": last_name,
                "phone_number": phone_number,
                "chat_keypad": chat_keypad,
                "disable_notification": disable_notification,
                "chat_keypad_type": chat_keypad_type,
                "inline_keypad": inline_keypad,
                "reply_to_message_id": reply_to_message_id,
            }
            result = await self._send_req(
                "sendContact",
                data,
            )
            result["chat_id"] = chat_id
            await self._manage_auto_delete(result, auto_delete)
            return msg_update(result, self)
        if return_task:
            return asyncio.create_task(_active())
        else:
            return await _active()

    
    async def forward_message(
        self,
        from_chat_id: str,
        message_id: str,
        to_chat_id: str,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
        """forwarding message to chat id / فوروارد پیام به یک چت آیدی"""
        self.logger.info("استفاده از متود forward_message")
        async def _active():
            Utils.check_id_raise(from_chat_id)
            Utils.check_id_raise(to_chat_id)
            if self.wait_manager and self.wait_manager.track_after_send:
                _chat_id = to_chat_id if self.wait_manager.per_chat else None
                self.wait_manager.add_traffic(channel="forwarding", chat_id=_chat_id)
            wait_manager = wait_send or (self.wait_manager.get_time("forwarding") if self.wait_manager else None)
            if wait_manager:
                await asyncio.sleep(wait_manager)
            data = {
                "from_chat_id": from_chat_id,
                "message_id": message_id,
                "to_chat_id": to_chat_id,
                "disable_notification": disable_notification,
            }
            result = await self._send_req(
                "forwardMessage",
                data,
            )
            result["chat_id"] = to_chat_id
            await self._manage_auto_delete(result, auto_delete)
            return msg_update(result, self)
        if return_task:
            return asyncio.create_task(_active())
        else:
            return await _active()

    
    async def forward_messages(
        self,
        from_chat_id: str,
        message_ids: list,
        to_chat_id: str,
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[List[msg_update], List[asyncio.Task[msg_update]]]:
        """forwarding messages to chat id / فوروارد چند پیام به یک چت آیدی"""
        tasks: list = [
            self.forward_message(
                from_chat_id,
                ms_id,
                to_chat_id,
                disable_notification,
                auto_delete,
                wait_send=wait_send,
                return_task=return_task
            )
            for ms_id in message_ids
        ]
        return list(await asyncio.gather(*tasks))

    # ═══════════════════════════════════
    # region ✏️ Messaging | ویرایش و مدیریت پیام
    # ═══════════════════════════════════

    
    async def edit_message_text(
        self,
        chat_id: str,
        message_id: str,
        text: str,
        inline_keypad: Optional[list] = None,
        parse_mode: Literal["Markdown", "HTML", None] = "Markdown",
        meta_data: Optional[list] = None,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
        """editing message text / ویرایش متن پیام"""
        self.logger.info("استفاده از متود edit_message_text")
        async def _active():
            Utils.check_id_raise(chat_id)
            if self.wait_manager and self.wait_manager.track_after_send:
                _chat_id = chat_id if self.wait_manager.per_chat else None
                self.wait_manager.add_traffic(channel="editing", chat_id=_chat_id)
            wait_manager = wait_send or (self.wait_manager.get_time("editing") if self.wait_manager else None)
            if wait_manager:
                await asyncio.sleep(wait_manager)
            _meta_data = meta_data if meta_data is not None else []
            _text = text
            metadata, _text  = await self._parse_mode_text(_text, parse_mode)
            data = {"chat_id": chat_id, "message_id": message_id, "text": _text}
            data = Utils.data_format(data, inline_keypad, metadata=metadata, meta_data=_meta_data)
            result = await self._send_req(
                "editMessageText",
                data,
            )
            result["chat_id"] = chat_id
            return msg_update(result, self)
        if return_task:
            return asyncio.create_task(_active())
        else:
            return await _active()
    
    edit_text = edit_message_text
    edit_message = edit_message_text
    
    
    async def auto_edit(
        self,
        chat_id: str,
        message_id: str,
        text: str,
        auto_edit: int,
        inline_keypad: Optional[list] = None,
        parse_mode: Literal["Markdown", "HTML", None] = "Markdown",
        meta_data: list = [],
        separate_task: bool = False
    ) -> Optional[msg_update]:
        """auto edit message text {time_sleep} time s / ویرایش خودکار متن پیام بعد از فلان مقدار ثانیه"""
        async def _edit():
            return await self._auto_edit(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                auto_edit=auto_edit,
                inline_keypad=inline_keypad,
                parse_mode=parse_mode,
                meta_data=meta_data
            )
        if separate_task:
            asyncio.create_task(
                _edit()
            )
            return None
        else:
            await _edit()

    # endregion

    # ═══════════════════════════════════
    # region ❌ Deleteing Message | حذف پیام
    # ═══════════════════════════════════

    
    async def delete_message(
        self,
        chat_id: str,
        message_id: str,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[props, asyncio.Task[props]]:
        """delete message / پاکسازی(حذف) یک پیام"""
        self.logger.info("استفاده از متود delete_message")
        async def _active():
            Utils.check_id_raise(chat_id)
            if self.wait_manager and self.wait_manager.track_after_send:
                _chat_id = chat_id if self.wait_manager.per_chat else None
                self.wait_manager.add_traffic(channel="deleting", chat_id=_chat_id)
            wait_manager = wait_send or (self.wait_manager.get_time("deleting") if self.wait_manager else None)
            if wait_manager:
                await asyncio.sleep(wait_manager)
            data = {
                "chat_id": chat_id,
                "message_id": message_id
            }
            result = await self._send_req(
                "deleteMessage",
                data,
            )
            return props(result)
        if return_task:
            return asyncio.create_task(_active())
        else:
            return await _active()

    
    async def auto_delete(
        self,
        chat_id: str,
        message_id: str,
        time_sleep: float,
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
            Utils.check_id_raise(chat_id)
            return await self._auto_delete(
                chat_id=chat_id,
                message_id=message_id,
                time_sleep=time_sleep
            )

    # endregion

    
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
    
    
    async def send_file_by_file_id(
        self,
        chat_id: str,
        file_id: str,
        text: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown", "HTML", None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
        """sending file by file id / ارسال فایل با آیدی فایل"""
        self.logger.info("استفاده از متود send_file_by_file_id")
        async def _active():
            if self.wait_manager and self.wait_manager.track_after_send:
                _chat_id = chat_id if self.wait_manager.per_chat else None
                self.wait_manager.add_traffic(channel="sending", chat_id=_chat_id)
            wait_manager = await self._wait(wait_send)
            if wait_manager:
                await asyncio.sleep(wait_manager)
            _text = text
            _meta_data = meta_data if meta_data is not None else []
            metadata = []
            Utils.check_id_raise(chat_id)
            if _text:
                metadata, _text  = await self._parse_mode_text(_text, parse_mode)
            data = {
                "chat_id": chat_id,
                "text": _text,
                "file_id": file_id,
                "reply_to_message_id": reply_to_message_id,
                "disable_notification": disable_notification,
            }
            data = Utils.data_format(data, inline_keypad,keypad,resize_keyboard,on_time_keyboard, metadata=metadata, meta_data=_meta_data)
            sending = await self._send_req("sendFile", data)
            sending["chat_id"] = chat_id
            await self._manage_auto_delete(sending, auto_delete)
            return msg_update(sending, self)
        if return_task:
            return asyncio.create_task(_active())
        else:
            return await _active()
    
    
    async def request_send_file(
        self,
        type: Literal["File", "Image", "Voice", "Music", "Gif" , "Video"] = "File"
    ) -> dict:
        return await self._send_req(
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
        parse_mode: Literal["Markdown", "HTML", None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
        """sending file with types ['File', 'Image', 'Voice', 'Music', 'Gif' , 'Video'] / ارسال فایل با نوع های فایل و عکس و پیغام صوتی و موزیک و گیف و ویدیو"""
        self.logger.info("استفاده از متود base_send_file")
        async def _active():
            if self.wait_manager and self.wait_manager.track_after_send:
                _chat_id = chat_id if self.wait_manager.per_chat else None
                self.wait_manager.add_traffic(channel="sending", chat_id=_chat_id)
            wait_manager = await self._wait(wait_send)
            if wait_manager:
                await asyncio.sleep(wait_manager)
            request_file = await self.request_send_file(type_file)
            upload_url_file = request_file["upload_url"]
            _name_file = name_file
            if not _name_file:
                _name_file = Utils.format_file(type_file)
            if not _name_file:
                raise ValueError("type file is invalud !")
            upload_file = await self.upload_file(
                url=upload_url_file,
                file_name=_name_file,
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
            sended = send.to_dict() # type: ignore
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
        if return_task:
            return asyncio.create_task(_active())
        else:
            return await _active()

    
    async def send_file(
        self,
        chat_id: str,
        file: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown", "HTML", None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
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
            chunk_size=chunk_size,
            wait_send=wait_send,
            return_task=return_task
        )
        return result

    send_document = send_file

    
    async def send_image(
        self,
        chat_id: str,
        image: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown", "HTML", None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
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

    send_photo = send_image
    send_picture = send_image

    
    async def send_video(
        self,
        chat_id: str,
        video: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown", "HTML", None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
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

    
    async def send_voice(
        self,
        chat_id: str,
        voice: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown", "HTML", None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
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

    
    async def send_music(
        self,
        chat_id: str,
        music: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown", "HTML", None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
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

    
    async def send_gif(
        self,
        chat_id: str,
        gif: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown", "HTML", None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chunk_size: int = 64 * 1024,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
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
            chunk_size=chunk_size,
            wait_send=wait_send,
            return_task=return_task
        )
        return result

    
    async def send_sticker(
        self,
        chat_id: str,
        id_sticker: str,
        reply_to_message_id : Optional[str] = None,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
        """sending sticker by id / ارسال استیکر با آیدی"""
        self.logger.info("استفاده از متود send_sticker")
        async def _active():
            Utils.check_id_raise(chat_id)
            if self.wait_manager and self.wait_manager.track_after_send:
                _chat_id = chat_id if self.wait_manager.per_chat else None
                self.wait_manager.add_traffic(channel="sending", chat_id=_chat_id)
            wait_manager = await self._wait(wait_send)
            if wait_manager:
                await asyncio.sleep(wait_manager)
            data = {
                "chat_id": chat_id,
                "sticker_id": id_sticker,
                "reply_to_message_id": reply_to_message_id,
                "disable_notification": disable_notification
            }
            sender = await self._send_req("sendSticker", data)
            sender["chat_id"] = chat_id
            await self._manage_auto_delete(sender, auto_delete)
            return msg_update(sender, self)
        if return_task:
            return asyncio.create_task(_active())
        else:
            return await _active()
    
    
    async def resend_message(
        self,
        message_id: str,
        from_chat_id: str,
        to_chat_id: str,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown", "HTML", None] = "Markdown",
        meta_data: Optional[list] = None,
        name_save_file: Optional[str] = None,
        show_progress: bool = True,
        chunk_size: int = 64 * 1024,
        wait_send: Optional[float] = None,
        return_task: bool = False
    ) -> Union[msg_update, asyncio.Task[msg_update]]:
        """re send message / ارسال مجدد پیام"""
        async def _active():
            Utils.check_id_raise(from_chat_id)
            Utils.check_id_raise(to_chat_id)
            if self.wait_manager and self.wait_manager.track_after_send:
                _chat_id = to_chat_id if self.wait_manager.per_chat else None
                self.wait_manager.add_traffic(channel="sending", chat_id=_chat_id)
            wait_manager = await self._wait(wait_send)
            if wait_manager:
                await asyncio.sleep(wait_manager)
            msg = await self.get_message_by_id(from_chat_id, message_id)
            if msg:
                text = msg.text
                file_file_id = msg.file_id
                file_file_name = str(msg.file_name)
                if (not file_file_id) and text:
                    return await self.send_text(
                        text=text,
                        chat_id=to_chat_id,
                        auto_delete=auto_delete,
                        parse_mode=parse_mode,
                        meta_data=meta_data
                    )
                if file_file_id:
                    download_name = name_save_file if name_save_file else file_file_name
                    type_file = Utils.type_file(name_file=download_name)
                    await self.download_file(
                        file_file_id,
                        download_name,
                        show_progress
                    )
                    return await self.base_send_file(
                        chat_id=to_chat_id,
                        file=download_name,
                        name_file=download_name,
                        text=text,
                        auto_delete=auto_delete,
                        parse_mode=parse_mode,
                        meta_data=meta_data,
                        show_progress=show_progress,
                        chunk_size=chunk_size,
                        type_file=type_file
                    )
                self.logger.warning("Can't Find Message !")
                raise KeyError("Can't Find Message !")
            else:
                self.logger.warning("Can't Find Message !")
                raise KeyError("Can't Find Message !")
        if return_task:
            return asyncio.create_task(_active()) # type: ignore
        else:
            return await _active()

    copy_message = resend_message

    # endregion

    # ═══════════════════════════════════
    # region 🎛️ Handlers | دکوراتورهای ثبت هندلر
    # ═══════════════════════════════════

    def add_conversation(
        self,
        conversation: 'Conversation'
    ):
        self._conversation_manager.add(conversation)

    def on_message(self,
        filters: Optional[Filter] = None,
        edited_messages: Literal[False, True, "both"] = False,
        deleted_messages: Literal[False, True, "both"] = False
    ):
        """برای دریافت پیام‌های معمولی به صورت پولینگ"""
        def decorator(handler):
            self.add_handler(
                handler=handler,
                type_handler="polling",
                filters=filters,
                edited_messages=edited_messages,
                deleted_messages=deleted_messages
            )
            return handler
        return decorator

    def on_message_updates(
        self,
        filters: Optional[Filter] = None,
        edited_messages: Literal[False, True, "both"] = False,
        deleted_messages: Literal[False, True, "both"] = False
    ):
        """گرفتن پیام ها با وبهوک"""
        def decorator(handler):
            self.add_handler(
                handler=handler,
                type_handler="webhook",
                filters=filters,
                edited_messages=edited_messages,
                deleted_messages=deleted_messages
            )
            return handler
        return decorator

    def on_button(self):
        """برای دریافت کلیک های دکمه های شیشه ای"""
        def decorator(handler):
            self.add_handler(
                handler=handler,
                type_handler="button"
            )
            return handler
        return decorator
    
    on_inline = on_button
    on_inline_button = on_button
    on_glass_buttons = on_button
    on_glass_inline = on_button
    
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

    on_message_webhook = on_message_updates
    on_message_webhook_delete = on_delete_updates
    on_message_webhook_edit = on_edit_updates
    on_message_webhook_all = on_all_message_updates
    on_message_polling = on_message
    on_message_polling_delete = on_delete
    on_message_polling_edit = on_edit
    on_message_polling_all = on_all_message

    
    def on_ready(self):
        """when client read for sending requests and no has problem for sending requests / زمانی که کلاینت آماده برای ارسال درخواست ها شده و مشکلی برای ارسال درخواست ها ندارد"""
        def decorator(func):
            self.add_handler(
                handler=func,
                type_handler="ready"
            )
            return func
        return decorator
    
    def on_start(self):
        """when client read for sending requests / زمانی که کلاینت آماده برای ارسال درخواست ها شد"""
        def decorator(func):
            self.add_handler(
                handler=func,
                type_handler="start"
            )
            return func
        return decorator
    
    on_startup = on_start

    def on_run(self):
        """when start getting messages / زمانی که گرفتن پیام ها شروع می شود"""
        def decorator(func):
            self.add_handler(
                handler=func,
                type_handler="run"
            )
            return func
        return decorator

    def on_live(self):
        """when mode polling , getting new messages / زمانی که در حالت پولینگ به پیام های جدید می رسد"""
        def decorator(func):
            self.add_handler(
                handler=func,
                type_handler="live"
            )
            return func
        return decorator
    
    def on_error(
        self,
        error_detail: Literal["full", "message", "type"] = "message"
    ):
        """Manage errors in handlers / مدیریت خطا های پیش بینی نشده در هندلر ها"""
        def decorator(func):
            self.add_handler(
                handler=func,
                type_handler="error",
                error_detail=error_detail
            )
            return func
        return decorator
    
    def middleware(
        self,
        filters: Optional[Filter] = None
    ):
        """دکوراتور برای ثبت Middleware"""
        def decorator(func: Callable):
            self.add_handler(func, "middleware", filters)
            return func
        return decorator
    
    def load_plugins(self, folder: str = "plugins") -> int:
        """لود کردن همه پلاگین‌ها از پوشه."""
        return PluginManager.load(self, folder, self.logger)
    
    def load_plugin(self, filepath: str) -> bool:
        """لود یه پلاگین خاص."""
        return PluginManager.load_single(self, filepath)
    
    def on_shutdown(
        self
    ):
        """دکوراتور برای زمانی که ربات خاموش می‌شود (هنگام close)."""
        def decorator(func: Callable):
            self.add_handler(func, "shutdown")
            return func
        return decorator
    
    on_close = on_shutdown
    
    def add_handler(
        self,
        handler: Union[Callable, tuple],
        type_handler: Literal[
            "polling",
            "webhook",
            "button",
            "start",
            "ready",
            "run",
            "live",
            "error",
            "conversation",
            "middleware",
            "shutdown",
        ],
        filters: Optional[Filter] = None,
        edited_messages: Literal[False, True, "both"] = False,
        deleted_messages: Literal[False, True, "both"] = False,
        **values
    ):
        if isinstance(handler, Callable):
            if type_handler in ("polling", "webhook"):
                self._fetch_messages = True
                @wraps(handler)
                async def wrapped(update):
                    try:
                        if filters is not None:
                            try:
                                if not filters(update):
                                    return
                            except Exception as e:
                                await self._process_on_error(
                                    e=e
                                )
                                return

                        if inspect.iscoroutinefunction(handler):
                            return await handler(update)
                        else:
                            return handler(update)

                    except Exception as e:
                        await self._process_on_error(
                            e=e
                        )
                        return None
                handler_info = {
                    "handler": wrapped,
                    "filters": filters,
                    "edited_messages": edited_messages,
                    "deleted_messages": deleted_messages
                }
                if edited_messages:
                    self._fetch_edit = True
                if type_handler == "polling":
                    self._fetch_messages_polling = True
                    self._message_handlers_polling.append(handler_info)
                else:
                    self._fetch_messages_webhook = True
                    self._message_handlers_webhook.append(handler_info)
                return wrapped
            elif type_handler == "button":
                self._fetch_buttons = True
                self._button_handlers.append(handler)
            elif type_handler == "start":
                self._on_start_handlers.append(handler)
            elif type_handler == "ready":
                self._on_ready_handlers.append(handler)
            elif type_handler == "run":
                self._on_run_handlers.append(handler)
            elif type_handler == "live":
                self._on_live_handlers.append(handler)
            elif type_handler == "error":
                handler_info = {
                    "handler": handler
                }
                handler_info.update(
                    values
                )
                self._on_error_handlers.append(
                    handler_info
                )
            elif type_handler == "middleware":
                self._middleware_manager.add(handler, filters)
            elif type_handler == "shutdown":
                self._on_shutdown_handlers.append(handler)
        else:
            if type_handler == "conversation":
                name, conv = handler
                self._conversation_manager.add(conv)
    
    # endregion

    # ═══════════════════════════════════
    # region ⚙️ Processs | فرایند ها
    # ═══════════════════════════════════

    async def _process_messages_polling(self):
        while self._running:
            try:
                messages = await self.get_updates(
                    limit=100,
                    offset_id=self.next_offset_id
                )
                try:
                    self.next_offset_id = messages["next_offset_id"]
                    if self.save_offset_id:
                        self.session.offset_id = self.next_offset_id
                        await self.session.save()
                except KeyError:
                    pass
                messages = messages["updates"]
                for message in messages:
                    if message["type"] not in ["NewMessage", "UpdatedMessage", "RemoveMessage"]:
                        continue
                    update = Update(message, self)
                    if not update.time + 5 > time.time():
                        continue
                    if not self._is_live:
                        await self._process_on_live()
                        self._is_live = True
                    if self.wait_manager and self.wait_manager.auto_track:
                        self.wait_manager.track()
                    if await self._conversation_manager.handle(update, self):
                        continue
                    is_edited = message["type"] == "UpdatedMessage"
                    is_deleted = message["type"] == "RemoveMessage"
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
                                filter_class = type(filters)
                                if "__acall__" in filter_class.__dict__:
                                    result = await filters.__acall__(update)
                                else:
                                    result = filters(update)
                                if not result:
                                    continue
                            except Exception as e:
                                print(f"[FILTER ERROR] {filters} -> {e}")
                                continue
                        self._schedule_handler(handler, update)
                    if not is_edited and not is_deleted:
                        if self.keeper_messages_ram:
                            self.messages.append(update)
                        if self.keeper_messages_db:
                            await self.messages_db.append(update)
            except (httpx.ReadError, httpx.ConnectError) as e:
                self.logger.warning(f"خطای شبکه در _process_messages_polling: {e} - انتظار 5 ثانیه...")
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"خطای ناشناخته در _process_messages_polling: {e}")
            await asyncio.sleep(self.poll_interval)

    async def _process_webhook_push(self, data: dict, endpoint_type: str):
        """پردازش وب‌هوک Push برای پیام‌های معمولی"""
        updates = data if isinstance(data, list) else [data]
        for result in updates:
            if result.get("type") not in ["NewMessage", "UpdatedMessage", "RemovedMessage"]:
                continue
            if self.wait_manager and self.wait_manager.auto_track:
                self.wait_manager.track()
            update = Update(result, self)
            if await self._conversation_manager.handle(update, self):
                continue
            is_edited = result["type"] == "UpdatedMessage"
            is_deleted = result["type"] == "RemovedMessage"
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
                        self.logger.error(f"[FILTER ERROR] {e}")
                        continue
                self._schedule_handler(handler, update)
            if not is_edited and not is_deleted:
                if self.keeper_messages_ram:
                    self.messages.append(update)
                if self.keeper_messages_db:
                    await self.messages_db.append(update)

    async def _process_button_push(self, data: dict):
        """پردازش وب‌هوک Push برای کلیک دکمه‌های اینلاین"""
        updates = data if isinstance(data, list) else [data]
        for result in updates:
            update = UpdateButton(result, self)
            for handler in self._button_handlers:
                self._schedule_handler(handler, update)

    async def _process_on_start(self):
        for handler in self._on_start_handlers:
            try:
                await handler()
            except Exception as e:
                self.logger.error(f"on_start error : {e}")
    
    async def _process_on_ready(self):
        if self._on_ready_handlers:
            try:
                me = await self.get_me()
                self.logger.info("دکوراتور های on ready با موفقیت در حال اجرا هستند")
                self.logger.info(f"bot info :\n{me}")
                is_ok = True
            except:
                is_ok = False
            if is_ok:
                for handler in self._on_ready_handlers:
                    try:
                        await handler()
                    except Exception as e:
                        self.logger.error(f"on_ready error : {e}")
            else:
                raise httpx.NetworkError("Can't Cannecting To Server BotAPI for GetMe !")

    async def _process_on_run(self):
        for handler in self._on_run_handlers:
            try:
                await handler()
            except Exception as e:
                self.logger.error(f"on_run error : {e}")
    
    async def _process_on_live(self):
        for handler in self._on_live_handlers:
            try:
                await handler()
            except Exception as e:
                self.logger.error(f"on_live error : {e}")

    async def _process_on_error(
        self,
        e: Exception,
        update: Union[Update, UpdateButton, None] = None
    ):
        if self._on_error_handlers:
            for handler_info in self._on_error_handlers:
                try:
                    error_handler = handler_info["handler"]
                    type_error = handler_info["error_detail"]
                    if type_error == "full":
                        error = format_exc()
                    elif type_error == "message":
                        error = e
                    elif type_error == "type":
                        error = type(e).__name__
                    else:
                        error = "error invalid input"
                        self.logger.warning(error)
                    await error_handler(error, update)
                except Exception as exc:
                    self.logger.error(f"Error in on_error handler : {exc}")
        else:
            self.logger.error(f"Handler error : {e}", exc_info=True)
    
    
    async def _process_on_shutdown(self):
        for handler in self._on_shutdown_handlers:
            try:
                await handler()
            except Exception as e:
                self.logger.error(f"on_shutdown error : {e}")

    # endregion

    # ═══════════════════════════════════
    # region ⚙️ Utils | متدهای کمکی
    # ═══════════════════════════════════

    
    async def set_main_parse_mode(self,parse_mode: Literal['Markdown', 'HTML', 'Null', None]) -> None:
        """setting parse mode main / تنظیم کردن مقدار اصلی پارس مود

توجه :
در صورت تغییر مارکدوان در کلاینت یا متود ست مین پارس مود , پارس مود همیشه روی آن حالت قرار میگیرد
در صورتی که میخواهید از این حالت خارج شود و از ورودی های متود ها پیروی کند مقدار آن را در متود ست مین پارس مود برابر 'Null' کنید"""
        self.main_parse_mode = parse_mode

    
    async def version_botapi(self) -> str:
        """getting version botapi / گرفتن نسخه بات ای پی آی"""
        response = await self.network.request(
            url=self.main_url,
            type_send="GET",
            timeout=self.time_out
        )
        version = response.text
        return version
    
    def add_background_task(
        self,
        coro: Callable,
        *args,
        delay: float = 0.0,
        **kwargs
    ) -> asyncio.Task:
        """add background task / اضافه کردن تسک بک‌گراند"""
        return self._background.add(coro, *args, delay=delay, **kwargs)
    
    async def send_requests(
        self,
        method: str,
        data_: Optional[Dict[str, Any]] = None
    ) -> dict:
        """ارسال درخواست ها / send request to methods with retry mechanism"""
        return await self._send_req(
            method=method,
            data=data_
        )

    # endregion

    # ═══════════════════════════════════
    # region 🔍 Get Message | گرفتن پیام
    # ═══════════════════════════════════

    
    async def get_updates(
        self,
        limit: Optional[int] = None,
        offset_id : Optional[str] = None
    ) -> props:
        """getting messages chats / گرفتن پیام های چت ها"""
        self.logger.info("استفاده از متود get_updates")
        data = {
            "offset_id": offset_id,
            "limit": limit
        }
        result = await self._send_req(
            "getUpdates",
            data,
        )
        return props(result)
    
    
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
        if chat_id:
            Utils.check_id_raise(chat_id)
        self.logger.info("در حال استفاده از متود get_message .")
        if search_by in ("all", "messages"):
            self.logger.info("در حال جستجو پیام در بین پیام های ذخیره شده ...")
            for msg in self.messages:
                if isinstance(msg, Update):
                    if msg.message_id == message_id:
                        if msg.chat_id == chat_id or chat_id is None:
                            self.logger.info("پیام در بین پیام های ذخیره شده پیدا شد !")
                            return msg
            if self.keeper_messages_db and chat_id:
                finder = await self.messages_db.find_message(
                    chat_id=chat_id,
                    message_id=message_id
                )
                if finder:
                    self.logger.info("پیام در بین پیام های دیتابیس پیدا شد !")
                    return Update(
                        update_data=finder,
                        client=self
                    )
            self.logger.warning("پیام در بین پیام های ذخیره شده و دیتابیس پیدا نشد !")
        if search_by in ("all", "get_updates"):
            self.logger.info("در حال جستجو پیام با get_updates ...")
            updates = await self.get_updates(limit_search,self.next_offset_id_get_message)
            self.geted_u = len(updates["updates"])
            for msg in updates["updates"]:
                if msg["type"] == "NewMessage":
                    message = Update(msg, self)
                    if message.message_id == message_id:
                        if message.chat_id == chat_id or chat_id is None:
                            self.logger.info("پیام در get_updates پیدا شد !")
                            return message
            self.logger.warning("پیام در بین get_updates پیدا نشد !")
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
        Utils.check_id_raise(chat_id)
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
            self.logger.warning("پیام ها در بین پیام های ذخیره شده پیدا نشد !")
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
            self.logger.warning("پیام ها در بین get_updates پیدا نشدند !")
            if self.geted_u >= 40:
                try:
                    self.next_offset_id_get_message = updates["next_offset_id"]
                    self.geted_u = 0
                    return await self.get_messages(chat_id, message_id, limit_search, get_befor, "get_updates")
                except:
                    pass
        self.logger.error("پیام ها پیدا نشدند !")
        return None

    get_messages_by_id = get_messages
    get_message_inveral = get_messages

    # endregion

    # ═══════════════════════════════════
    # region ⚙️ WebHook Setting | تنظیمات وبهوک
    # ═══════════════════════════════════

    async def set_endpoint(
        self,
        url: str,
        type: Literal[
            "ReceiveUpdate", "GetSelectionItem",
            "ReceiveInlineMessage", "ReceiveQuery",
            "SearchSelectionItems"
        ]
    ) -> props:
        """set endpoint url / تنظیم ادرس اند پوینت"""
        self.logger.info("استفاده از متود set_endpoint")
        result = await self._send_req(
            "updateBotEndpoints",
            {
                "url": url,
                "type": type
            }
        )
        return props(result)
    
    update_end_point = set_endpoint
    update_endpoint = set_endpoint

    
    # async def set_token_fast_rub(
    #     self,
    #     list_getted: List[Literal["ReceiveUpdate", "ReceiveInlineMessage"]] = ["ReceiveUpdate", "ReceiveInlineMessage"]
    # ) -> bool:
    #     """seting token in fast_rub for getting click glass messages and updata messges / تنظیم توکن در فست روب برای گرفتن کلیک های روی پیام شیشه ای و آپدیت پیام ها"""
    #     self.logger.info("استفاده از متود set_token_fast_rub")
    #     try:
    #         await self.network.request(f"https://fast-rub.ParsSource.ir/api/set_token?token={self.token}")
    #         for get in list_getted:
    #             url = f"https://fast-rub.ParsSource.ir/api/geting_button_updates/{self.token}/{get}"
    #             await self.set_endpoint(url, get)
    #         self.logger.info("توکن با موفقیت در پیامگیر ثبت شد")
    #         return True
    #     except Exception as e:
    #         self.logger.warning(f"خطا در ثبت توکن در پیامگیر فست روب : {e}")
    #         return False

    async def setup_webhooks(self):
        """خودکار Endpointها رو به روبیکا معرفی می‌کنه (فراخوانی توسط کاربر)"""
        if not self._webhook_server:
            raise RuntimeError("Webhook Server تنظیم نشده. اول webhook=WebhookConfig(...) رو به Client بده.")

        base = self._webhook_server.config.url.rstrip("/")
        prefix = self._webhook_server.config.path_prefix
        
        if self._webhook_server.config.use_token_in_url:
            token = self.token
            endpoints = {
                "ReceiveUpdate": f"{base}{prefix}/message/{token}",
                "ReceiveInlineMessage": f"{base}{prefix}/inline/{token}",
            }
        else:
            endpoints = {
                "ReceiveUpdate": f"{base}{prefix}/message",
                "ReceiveInlineMessage": f"{base}{prefix}/inline",
            }
        
        for endpoint_type, url in endpoints.items():
            await self.update_endpoint(url, endpoint_type) # type: ignore

    # endregion


wrap_all_async_methods(Client)

Robot = Client
Bot = Client
BotApi = Client
BotApiClient = Client

