import httpx,time,os,json,asyncio,inspect
from typing import Optional, Callable, Awaitable, Literal,Union,Dict,List,Any
from .colors import *
from .filters import Filter
from functools import wraps
from pathlib import Path
from .type import Update,UpdateButton
from .async_sync import *
from .type.get_type import get_file_category
from .logger import *
from .props import *

class Client:
    def __init__(
        self,
        name_session: str,
        token: Optional[str] = None,
        user_agent: Optional[str] = None,
        time_out: Optional[int] = 60,
        display_welcome=True,
        use_to_fastrub_webhook_on_message : Optional[str|bool]=True,
        use_to_fastrub_webhook_on_button : Optional[str|bool]=True
    ):
        """Client for login and setting robot / کلاینت برای لوگین و تنظیمات ربات"""
        name = name_session + ".faru"
        self.token = token
        self.time_out = time_out
        self.user_agent = user_agent
        self._running = False
        self.list_ = []
        self.data_keypad = []
        self.data_keypad2 = []
        self._button_handlers2 = []
        self._running_ = False
        self._loop = None
        self.last = []
        self._running = False
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
                self.token = text_json_fast_rub_session["token"]
                self.time_out = text_json_fast_rub_session["time_out"]
                self.user_agent = text_json_fast_rub_session["user_agent"]
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
            }
            with open(name, "w", encoding="utf-8") as file:
                json.dump(
                    text_json_fast_rub_session, file, ensure_ascii=False, indent=4
                )
            self.token = token
            self.time_out = time_out
            self.user_agent = user_agent

        if display_welcome:
            k = ""
            for text in "Welcome to FastRub":
                k += text
                print(f"{Colors.GREEN}{k}{Colors.RESET}", end="\r")
                time.sleep(0.07)
            cprint("",Colors.WHITE)
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
        client_logger.info("سشن اماده است")

    @property
    def TOKEN(self):
        logger.info("توکن دریافت شد")
        return self.token

    @async_to_sync
    async def send_requests(
        self, method, data_: Optional[Union[Dict[str, Any], List[Any]]] = None
    ) -> dict:
        logger.info("در حال ارسال درخواست")
        url = f"https://botapi.rubika.ir/v3/{self.token}/{method}"
        if self.user_agent != None:
            headers = {
                "User-Agent": self.user_agent,
                "Content-Type": "application/json",
            }
        else:
            headers = {"Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self.time_out) as cl:
                if data_ == None:
                    result = await cl.post(url, headers=headers)
                    result_ = result.json()
                else:
                    result = await cl.post(url, headers=headers, json=data_)
                    result_ = result.json()
                if result_["status"] != "OK":
                    logger.error(f"خطایی از سمت سرور ! status : {result_['status']}")
                    raise TypeError(f"Error for invalid status : {result_}")
                logger.info("نتیجه درخواست موفق است")
                return result_
        except TimeoutError:
            logger.error("خطا ! زمان ارسال درخواست به پایان رسیده است")
            raise TimeoutError("Please check the internet !")
        except Exception as e:
            logger.error(f"خطایی ناشناخته : {e}")
            raise e
        return {}

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
        logger.info("استفاده از متود get_me")
        result = await self.send_requests(method="getMe")
        return props(result)

    @async_to_sync
    async def send_text(
        self,
        text: str,
        chat_id: str,
        inline_keypad = None,
        disable_notification: Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
    ) -> dict:
        """sending text to chat id / ارسال متنی به یک چت آیدی"""
        logger.info("استفاده از متود send_message")
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
        return result

    @async_to_sync
    async def send_poll(self, chat_id: str, question: str, options: list) -> props:
        """sending poll to chat id / ارسال نظرسنجی به یک چت آیدی"""
        logger.info("استفاده از متود send_poll")
        data = {"chat_id": chat_id, "question": question, "options": options}
        result = await self.send_requests(
            "sendPoll",
            data,
        )
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
    ) -> props:
        """sending location to chat id / ارسال لوکیشن(موقعیت مکانی) به یک چت آیدی"""
        logger.info("استفاده از متود send_location")
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
        disable_notificatio: Optional[bool] = False
    ) -> props:
        """sending contact to chat id / ارسال مخاطب به یک چت آیدی"""
        logger.info("استفاده از متود send_contact")
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
        return props(result)

    @async_to_sync
    async def get_chat(self, chat_id: str) -> props:
        """geting info chat id info / گرفتن اطلاعات های یک چت"""
        logger.info("استفاده از متود get_chat")
        data = {"chat_id": chat_id}
        result = await self.send_requests(
            "getChat",
            data,
        )
        return props(result)

    @async_to_sync
    async def get_updates(self, limit : Optional[int] = None, offset_id : Optional[str] = None) -> props:
        """getting messages chats / گرفتن پیام های چت ها"""
        logger.info("استفاده از متود get_updates")
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
    ) -> props:
        """forwarding message to chat id / فوروارد پیام به یک چت آیدی"""
        logger.info("استفاده از متود forward_message")
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
        return props(result)

    @async_to_sync
    async def edit_message_text(self, chat_id: str, message_id: str, text: str) -> props:
        """editing message text / ویرایش متن پیام"""
        logger.info("استفاده از متود edit_message_text")
        data = {"chat_id": chat_id, "message_id": message_id, "text": text}
        result = await self.send_requests(
            "editMessageText",
            data,
        )
        return props(result)

    @async_to_sync
    async def delete_message(self, chat_id: str, message_id: str) -> props:
        """delete message / پاکسازی(حذف) یک پیام"""
        logger.info("استفاده از متود delete_message")
        data = {"chat_id": chat_id, "message_id": message_id}
        result = await self.send_requests(
            "deleteMessage",
            data,
        )
        return props(result)

    @async_to_sync
    async def add_commands(self, command: str, description: str) -> None:
        """add command to commands list / افزودن دستور به لیست دستورات"""
        logger.info("استفاده از متود add_commands")
        self.list_.append(
            {"command": command.replace("/", ""), "description": description}
        )

    @async_to_sync
    async def set_commands(self) -> props:
        """set the commands for robot / تنظیم دستورات برای ربات"""
        logger.info("استفاده از متود set_commands")
        result = await self.send_requests(
            "setCommands",
            {"bot_commands": self.list_},
        )
        return props(result)

    @async_to_sync
    async def delete_commands(self) -> props:
        """clear the commands list / پاکسازی لیست دستورات"""
        logger.info("استفاده از متود delete_commands")
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
        logger.info("استفاده از متود edit_message_keypad_Inline")
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
        Keypad,
        disable_notification : Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
        resize_keyboard : Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
    ) -> props:
        """sending message key pad texti / ارسال پیام با دکمه متنی"""
        logger.info("استفاده از متود send_message_keypad")
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
        return props(result)

    async def _upload_file(self, url: str, file_name: str, file: str | Path | bytes):
        logger.info("استفاده از متود _upload_file")
        if type(file) is bytes:
            d_file = {"file": (file_name, file, "application/octet-stream")}
        else:
            try:
                with open(file, "rb") as fi:
                    d_file = {"file": (file_name,fi , "application/octet-stream")}
            except:
                async with httpx.AsyncClient() as client:
                    file_ = (await client.get(file)).content
                d_file = {"file":file_}
        async with httpx.AsyncClient(verify=False) as cl:
            response = await cl.post(url, files=d_file,timeout=9999)
            if response.status_code != 200:
                logger.error("خطا در آپلود فایل !")
                raise httpx.HTTPStatusError(
                    f"Request failed with status code {response.status_code}",
                    request=response.request,
                    response=response,
                )
            data = response.json()
            return data

    @async_to_sync
    async def send_file(
        self,
        chat_id: str,
        file: str | Path | bytes,
        name_file: str,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif" , "Video"] = "File",
        disable_notification : Optional[bool] = False,
    ) -> props:
        """sending file with types ['File', 'Image', 'Voice', 'Music', 'Gif' , 'Video'] / ارسال فایل با نوع های فایل و عکس و پیغام صوتی و موزیک و گیف و ویدیو"""
        logger.info("استفاده از متود send_file")
        up_url_file = (
            await self.send_requests(
                "requestSendFile",
                {"type": type_file},
            )
        )["data"]["upload_url"]
        file_id = (await self._upload_file(up_url_file, name_file, file))["data"][
            "file_id"
        ]
        data = {
            "chat_id": chat_id,
            "text": text,
            "file_id": file_id,
            "reply_to_message_id": reply_to_message_id,
            "disable_notification": disable_notification,
        }
        uploader = await self.send_requests("sendFile", data)
        uploader["file_id"] = file_id
        uploader["type_file"] = type_file
        if isinstance(file, (bytes, bytearray, memoryview)):
            uploader["size_file"] = len(file)
        elif isinstance(file, (str, Path)):
            try:
                with open(file, "rb") as fi:
                    size_file = len(fi)
            except:
                async with httpx.AsyncClient() as client:
                    size_file = len((await client.get(file)).content)
                uploader["size_file"] = size_file
            else:
                raise FileExistsError("file not found !")
        return props(uploader)

    @async_to_sync
    async def send_image(
        self,
        chat_id: str,
        image: str | Path | bytes,
        name_file: str,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification: Optional[bool] = False,
    ) -> props:
        """sending image / ارسال تصویر"""
        logger.info("استفاده از متود send_image")
        return await self.send_file(
            chat_id,
            image,
            name_file,
            text,
            reply_to_message_id,
            "Image",
            disable_notification,
        )

    @async_to_sync
    async def send_video(
        self,
        chat_id: str,
        video: str | Path | bytes,
        name_file: str,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification : Optional[bool] = False,
    ) -> props:
        """sending video / ارسال ویدیو"""
        logger.info("استفاده از متود send_video")
        return await self.send_file(
            chat_id,
            video,
            name_file,
            text,
            reply_to_message_id,
            "Video",
            disable_notification,
        )

    @async_to_sync
    async def send_voice(
        self,
        chat_id: str,
        voice: str | Path | bytes,
        name_file: str,
        text : Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notification: Optional[bool] = False,
    ) -> props:
        """sending voice / ارسال ویس"""
        logger.info("استفاده از متود send_voice")
        return await self.send_file(
            chat_id,
            voice,
            name_file,
            text,
            reply_to_message_id,
            "Voice",
            disable_notification,
        )

    @async_to_sync
    async def send_music(
        self,
        chat_id: str,
        music: str | Path | bytes,
        name_file: str,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification : Optional[bool] = False,
    ) -> props:
        """sending music / ارسال موزیک"""
        logger.info("استفاده از متود send_music")
        return await self.send_file(
            chat_id,
            music,
            name_file,
            text,
            reply_to_message_id,
            "Music",
            disable_notification,
        )

    @async_to_sync
    async def send_gif(
        self,
        chat_id: str,
        gif: str | Path | bytes,
        name_file: str,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification : Optional[bool] = False,
    ) -> props:
        """sending gif / ارسال گیف"""
        logger.info("استفاده از متود send_gif")
        return await self.send_file(
            chat_id,
            gif,
            name_file,
            text,
            reply_to_message_id,
            "Gif",
            disable_notification,
        )

    @async_to_sync
    async def send_sticker(
        self,
        chat_id: str,
        id_sticker: str,
        reply_to_message_id : Optional[str] = None,
        disable_notification : Optional[bool] = False,
    ) -> props:
        """sending sticker by id / ارسال استیکر با آیدی"""
        logger.info("استفاده از متود send_sticker")
        data = {
            "chat_id": chat_id,
            "sticker_id": id_sticker,
            "reply_to_message_id": reply_to_message_id,
            "disable_notification": disable_notification,
        }
        sender = await self.send_requests("sendSticker", data)
        return props(sender)

    @async_to_sync
    async def get_download_file_url(self,id_file : str) -> str:
        """get download url file / گرفتن آدرس دانلود فایل"""
        logger.info("استفاده از متود get_download_file_url")
        data = {"file_id": id_file}
        url = (await self.send_requests("getFile",data))["download_url"]
        return url

    @async_to_sync
    async def download_file(self,id_file : str , path : str = "file") -> None:
        """download file / دانلود فایل"""
        logger.info("استفاده از متود download_file")
        url = await self.get_download_file_url(id_file)
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', url) as response:
                with open(path, 'wb') as file:
                    async for chunk in response.aiter_bytes():
                        logger.info("فایل دانلود شد")
                        file.write(chunk)

    @async_to_sync
    async def set_endpoint(self, url: str, type: Literal["ReceiveUpdate", "GetSelectionItem", "ReceiveInlineMessage", "ReceiveQuery", "SearchSelectionItems"]) -> props:
        """set endpoint url / تنظیم ادرس اند پوینت"""
        logger.info("استفاده از متود set_endpoint")
        result = await self.send_requests(
            "updateBotEndpoints", {"url": url, "type": type}
        )
        return props(result)

    @async_to_sync
    async def set_token_fast_rub(self) -> bool:
        """seting token in fast_rub for getting click glass messages and updata messges / تنظیم توکن در فست روب برای گرفتن کلیک های روی پیام شیشه ای و آپدیت پیام ها"""
        logger.info("استفاده از متود set_token_fast_rub")
        async with httpx.AsyncClient() as cl:
            r = (
                await cl.get(
                    f"https://fast-rub.ParsSource.ir/set_token?token={self.token}"
                )
            ).json()
        list_up:List[Literal["ReceiveUpdate", "ReceiveInlineMessage"]]= [
            "ReceiveUpdate", 
            "ReceiveInlineMessage"
        ]
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
                async with httpx.AsyncClient() as cl:
                    await cl.get("https://rubika.ir/",timeout=self.time_out)
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
                            await handler(update_obj)
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
    async def _process_messages(self, time_updata_sleep : Union[int,int] = 1):
        while self._running:
            try:
                async with httpx.AsyncClient() as cl:
                    await cl.get("https://rubika.ir/", timeout=self.time_out)
            except:
                raise TimeoutError("please check the your internet .")
            mes = (await self.get_updates(limit=100))
            if mes['status'] == "INVALID_ACCESS":
                raise PermissionError("Due to Rubika's restrictions, access to retrieve messages has been blocked. Please try again.")
            for message in mes['data']['updates']:
                time_sended_mes = int(message['new_message']['time'])
                now = int(time.time())
                time_ = time_updata_sleep + 4
                if (now - time_sended_mes < time_) and (not message['new_message']['message_id'] in self.last):
                    self.last.append(message['new_message']['message_id'])
                    if len(self.last) > 500:
                        self.last.pop(-1)
                    update_obj = Update(message, self)
                    for handler in self._message_handlers:
                        await handler(update_obj)
            await asyncio.sleep(time_updata_sleep)

    @async_to_sync
    async def _process_edit(self, time_updata_sleep : Union[int,int] = 1):
        while self._running:
            try:
                async with httpx.AsyncClient() as cl:
                    await cl.get("https://rubika.ir/",timeout=self.time_out)
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
                        for handler in self._message_handlers_:
                            await handler(update_obj)
            await asyncio.sleep(time_updata_sleep)

    @async_to_sync
    async def _fetch_button_updates(self):
        while self._running:
            async with httpx.AsyncClient() as cl:
                response = (await cl.get(self._button_url, timeout=self.time_out)).json()
            if response and response.get('status') is True:
                results = response.get('updates', [])
                if results:
                    for result in results:
                        update = UpdateButton(result)
                        for handler in self._button_handlers:
                            await handler(update)
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
        logger.info("ربات در حال دریافت پیام ها")
        asyncio.run(self._run_all())
