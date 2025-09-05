import httpx,time,os,json,asyncio,inspect
from typing import Optional, Callable, Awaitable, Literal,Union,Dict,List,Any
from colorama import Fore
from .filters import Filter
from functools import wraps
from pathlib import Path
from .type import Update,UpdateButton
from .async_sync import *


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
        self._message_handlers = []
        self._button_handlers = []
        self.last = []
        self._message_handlers_ = []
        self.next_offset_id = ""
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
                    print(Fore.RED, "Enter the token valid !")
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
                print(Fore.GREEN, f"""{k}""", end="\r")
                time.sleep(0.07)
            print(Fore.WHITE, "")
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

    @property
    def TOKEN(self):
        return self.token

    @async_to_sync
    async def send_requests(
        self, method, data_: Optional[Union[Dict[str, Any], List[Any]]] = None, type_send="post"
    ) -> dict:
        url = f"https://botapi.rubika.ir/v3/{self.token}/{method}"
        if self.user_agent != None:
            headers = {
                "User-Agent": self.user_agent,
                "Content-Type": "application/json",
            }
        else:
            headers = {"Content-Type": "application/json"}
        if type_send == "post":
            try:
                async with httpx.AsyncClient(timeout=self.time_out) as cl:
                    if data_ == None:
                        result = await cl.post(url, headers=headers)
                        json_result = result.json()
                        if json_result["status"] != "OK":
                            raise TypeError(f"Error for invalid status : {json_result}")
                        return json_result
                    else:
                        result = await cl.post(url, headers=headers, json=data_)
                        return result.json()
            except TimeoutError:
                raise TimeoutError("Please check the internet !")
        return {}

    @async_to_sync
    async def get_me(self) -> dict:
        """geting info accont bot / گرفتن اطلاعات اکانت ربات"""
        result = await self.send_requests(method="getMe")
        return result

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
    async def send_poll(self, chat_id: str, question: str, options: list) -> dict:
        """sending poll to chat id / ارسال نظرسنجی به یک چت آیدی"""
        data = {"chat_id": chat_id, "question": question, "options": options}
        result = await self.send_requests(
            "sendPoll",
            data,
        )
        return result

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
    ) -> dict:
        """sending location to chat id / ارسال لوکیشن(موقعیت مکانی) به یک چت آیدی"""
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
        return result

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
    ) -> dict:
        """sending contact to chat id / ارسال مخاطب به یک چت آیدی"""
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
        return result

    @async_to_sync
    async def get_chat(self, chat_id: str) -> dict:
        """geting info chat id info / گرفتن اطلاعات های یک چت"""
        data = {"chat_id": chat_id}
        result = await self.send_requests(
            "getChat",
            data,
        )
        return result

    @async_to_sync
    async def get_updates(self, limit : Optional[int] = None, offset_id : Optional[str] = None) -> dict:
        """getting messages chats / گرفتن پیام های چت ها"""
        data = {"offset_id": offset_id, "limit": limit}
        result = await self.send_requests(
            "getUpdates",
            data,
        )
        return result

    @async_to_sync
    async def forward_message(
        self,
        from_chat_id: str,
        message_id: str,
        to_chat_id: str,
        disable_notification : Optional[bool] = False,
    ) -> dict:
        """forwarding message to chat id / فوروارد پیام به یک چت آیدی"""
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
        return result

    @async_to_sync
    async def edit_message_text(self, chat_id: str, message_id: str, text: str) -> dict:
        """editing message text / ویرایش متن پیام"""
        data = {"chat_id": chat_id, "message_id": message_id, "text": text}
        result = await self.send_requests(
            "editMessageText",
            data,
        )
        return result

    @async_to_sync
    async def delete_message(self, chat_id: str, message_id: str) -> dict:
        """delete message / پاکسازی(حذف) یک پیام"""
        data = {"chat_id": chat_id, "message_id": message_id}
        result = await self.send_requests(
            "deleteMessage",
            data,
        )
        return result

    @async_to_sync
    async def add_commands(self, command: str, description: str) -> None:
        """add command to commands list / افزودن دستور به لیست دستورات"""
        self.list_.append(
            {"command": command.replace("/", ""), "description": description}
        )

    @async_to_sync
    async def set_commands(self) -> dict:
        """set the commands for robot / تنظیم دستورات برای ربات"""
        result = await self.send_requests(
            "setCommands",
            {"bot_commands": self.list_},
        )
        return result

    @async_to_sync
    async def delete_commands(self) -> dict:
        """clear the commands list / پاکسازی لیست دستورات"""
        self.list_ = []
        result = await self.send_requests(
            "setCommands",
            self.list_,
        )
        return result

    @async_to_sync
    async def edit_message_keypad_Inline(
        self,
        chat_id: str,
        text: str,
        inline_keypad,
        disable_notification : Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
    ) -> dict:
        """editing the text key pad inline / ویرایش پیام شیشه ای"""
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
        return result

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
    ) -> dict:
        """sending message key pad texti / ارسال پیام با دکمه متنی"""
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
        return result

    async def _upload_file(self, url: str, file_name: str, file: str | Path | bytes):
        if type(file) is bytes:
            d_file = {"file": (file_name, file, "application/octet-stream")}
        else:
            d_file = {"file": (file_name, open(file, "rb"), "application/octet-stream")}
        async with httpx.AsyncClient(verify=False) as cl:
            response = await cl.post(url, files=d_file)
            if response.status_code != 200:
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
    ) -> dict:
        """sending file with types ['File', 'Image', 'Voice', 'Music', 'Gif' , 'Video'] / ارسال فایل با نوع های فایل و عکس و پیغام صوتی و موزیک و گیف و ویدیو"""
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
        return uploader

    @async_to_sync
    async def send_image(
        self,
        chat_id: str,
        image: str | Path | bytes,
        name_file: str,
        text : Optional[str] = None,
        reply_to_message_id : Optional[str] = None,
        disable_notification: Optional[bool] = False,
    ) -> dict:
        """sending image / ارسال تصویر"""
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
    ) -> dict:
        """sending video / ارسال ویدیو"""
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
    ) -> dict:
        """sending voice / ارسال ویس"""
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
    ) -> dict:
        """sending music / ارسال موزیک"""
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
    ) -> dict:
        """sending gif / ارسال گیف"""
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
    ):
        """sending sticker by id / ارسال استیکر با آیدی"""
        data = {
            "chat_id": chat_id,
            "sticker_id": id_sticker,
            "reply_to_message_id": reply_to_message_id,
            "disable_notification": disable_notification,
        }
        sender = await self.send_requests("sendSticker", data)
        return sender

    @async_to_sync
    async def get_download_file_url(self,id_file : str) -> str:
        """get download url file / گرفتن آدرس دانلود فایل"""
        data = {"file_id": id_file}
        url = (await self.send_requests("getFile",data))["download_url"]
        return url

    @async_to_sync
    async def download_file(self,id_file : str , path : str = "file") -> None:
        """download file / دانلود فایل"""
        url = await self.get_download_file_url(id_file)
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', url) as response:
                with open(path, 'wb') as file:
                    async for chunk in response.aiter_bytes():
                        file.write(chunk)

    @async_to_sync
    async def set_endpoint(self, url: str, type: Literal["ReceiveUpdate", "GetSelectionItem", "ReceiveInlineMessage", "ReceiveQuery", "SearchSelectionItems"]) -> dict:
        """set endpoint url / تنظیم ادرس اند پوینت"""
        return await self.send_requests(
            "updateBotEndpoints", {"url": url, "type": type}
        )

    @async_to_sync
    async def set_token_fast_rub(self) -> bool:
        """seting token in fast_rub for getting click glass messages and updata messges / تنظیم توکن در فست روب برای گرفتن کلیک های روی پیام شیشه ای و آپدیت پیام ها"""
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
            if mes['status']=="INVALID_ACCESS":
                raise PermissionError("Due to Rubika's restrictions, access to retrieve messages has been blocked. Please try again.")
            try:
                self.next_offset_id = mes["data"]["next_offset_id"]
            except:
                pass
            for message in mes['data']['updates']:
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
                    print(message)
                    update_obj = Update(message, self)
                    for handler in self._message_handlers:
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
        if not tasks:
            raise ValueError("No handlers registered. Use on_message() or on_message_updates() or on_button() first.")
        await asyncio.gather(*tasks)

    def run(self):
        """اجرای اصلی بات - فقط اگر هندلرهای مربوطه ثبت شده باشند"""
        if not (self._fetch_messages or self._fetch_buttons or self._fetch_messages_):
            raise ValueError("No update types selected. Use on_message() or on_message_updates() or on_button() first.")
        
        if (self._fetch_messages and not self._message_handlers) or (self._fetch_messages_ and not self._message_handlers_):
            raise ValueError("Message handlers registered but no message callbacks defined.")
        
        if self._fetch_buttons and not self._button_handlers:
            raise ValueError("Button handlers registered but no button callbacks defined.")
        
        self._running = True
        asyncio.run(self._run_all())
