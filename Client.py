import httpx,time,os,json,asyncio
from typing import Optional, Callable, Awaitable, Literal
from colorama import Fore
from .filters import Filter
from functools import wraps
from pathlib import Path


class Client:
    def __init__(
        self,
        name_session: str,
        token: str = None,
        user_agent: str = None,
        time_out: Optional[int] = 60,
        display_welcome=True,
        use_to_fastrub_webhook_on_message:str|bool=True,
        use_to_fastrub_webhook_on_button:str|bool=True
    ):
        name = name_session + ".faru"
        self.token = token
        self.time_out = time_out
        self.user_agent = user_agent
        self._message_handlers = []
        self._running = False
        self.list_ = []
        self.data_keypad = []
        self.data_keypad2 = []
        self._button_handlers = []
        self._button_handlers2 = []
        self._running_ = False
        self._loop = None
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
        if type(use_to_fastrub_webhook_on_message)==str:
            self._on_url = use_to_fastrub_webhook_on_message
        else:
            self._on_url = f"https://fast-rub.ParsSource.ir/geting_button_updates/get_on?token={self.token}"
        if type(use_to_fastrub_webhook_on_button)=="str":
            self._button_url = use_to_fastrub_webhook_on_button
        else:
            self._button_url = f"https://fast-rub.ParsSource.ir/geting_button_updates/get?token={self.token}"

    async def send_requests(
        self, method, data_: Optional[dict] = None, type_send="post"
    ):
        url = f"https://botapi.rubika.ir/v3/{self.token}/{method}"
        if self.user_agent != None:
            headers = {
                "'User-Agent'": self.user_agent,
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

    async def get_me(self) -> dict:
        """geting info accont bot / گرفتن اطلاعات اکانت ربات"""
        result = await self.send_requests(method="getMe")
        return result

    async def send_text(
        self,
        text: str,
        chat_id: str,
        disable_notification: Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
    ) -> dict:
        """sending text to chat id / ارسال متنی به یک چت آیدی"""
        data = {
            "chat_id": chat_id,
            "text": text,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
        }
        result = await self.send_requests(
            "sendMessage",
            data,
        )
        return result

    async def send_poll(self, chat_id: str, question: str, options: list) -> dict:
        """sending poll to chat id / ارسال نظرسنجی به یک چت آیدی"""
        data = {"chat_id": chat_id, "question": question, "options": options}
        result = await self.send_requests(
            "sendPoll",
            data,
        )
        return result

    async def send_location(
        self,
        chat_id: str,
        latitude: str,
        longitude: str,
        chat_keypad: str = None,
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

    async def send_contact(
        self,
        chat_id: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        chat_keypad: str = None,
        chat_keypad_type: str = None,
        inline_keypad: str = None,
        reply_to_message_id: str = None,
        disable_notificatio: bool = False,
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

    async def get_chat(self, chat_id: str) -> dict:
        """geting info chat id info / گرفتن اطلاعات های یک چت"""
        data = {"chat_id": chat_id}
        result = await self.send_requests(
            "getChat",
            data,
        )
        return result

    async def get_updates(self, limit: int = None, offset_id: str = None) -> dict:
        """getting messages chats / گرفتن پیام های چت ها"""
        data = {"offset_id": offset_id, "limit": limit}
        result = await self.send_requests(
            "getUpdates",
            data,
        )
        return result

    async def forward_message(
        self,
        from_chat_id: str,
        message_id: str,
        to_chat_id: str,
        disable_notification: bool = False,
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

    async def edit_message_text(self, chat_id: str, message_id: str, text: str) -> dict:
        """editing message / ویرایش پیام"""
        data = {"chat_id": chat_id, "message_id": message_id, "text": text}
        result = await self.send_requests(
            "editMessageText",
            data,
        )
        return result

    async def delete_message(self, chat_id: str, message_id: str) -> dict:
        """delete message / پاکسازی(حذف) یک پیام"""
        data = {"chat_id": chat_id, "message_id": message_id}
        result = await self.send_requests(
            "deleteMessage",
            data,
        )
        return result

    async def add_commands(self, command: str, description: str) -> None:
        """add command to commands list / افزودن دستور به لیست دستورات"""
        self.list_.append(
            {"command": command.replace("/", ""), "description": description}
        )

    async def set_commands(self) -> dict:
        """set the commands for robot / تنظیم دستورات برای ربات"""
        result = await self.send_requests(
            "setCommands",
            {"bot_commands": self.list_},
        )
        return result

    async def delete_commands(self) -> None:
        """clear the commands list / پاکسازی لیست دستورات"""
        self.list_ = []
        result = await self.send_requests(
            "setCommands",
            self.list_,
        )
        return result

    async def add_listkeypad_InlineKeypad(
        self, id: str, type: str, button_text: str
    ) -> None:
        """add the key pad inline list 1 by 1 / افزودن لیست دکمه های شیشه ای به صورت تکی"""
        self.data_keypad.append(
            {"buttons": [{"id": id, "type": type, "button_text": button_text}]}
        )

    async def add_listkeypad_InlineKeypad2vs2(
        self,
        id: str,
        type: str,
        button_text: str,
        id2: str,
        type2: str,
        button_text2: str,
    ) -> None:
        """add the key pad inline list 2 by 2 / افزودن لیست دکمه های شیشه ای به صورت دوتایی"""
        self.data_keypad.append(
            {
                "buttons": [
                    {"id": id, "type": type, "button_text": button_text},
                    {"id": id2, "type": type2, "button_text": button_text2},
                ]
            }
        )

    async def add_listkeypad_InlineKeypad3vs3(
        self,
        id: str,
        type: str,
        button_text: str,
        id2: str,
        type2: str,
        button_text2: str,
        id3: str,
        type3: str,
        button_text3: str,
    ) -> None:
        """add the key pad inline list 3 by 3 / افزودن لیست دکمه های شیشه ای به صورت سه تایی"""
        self.data_keypad.append(
            {
                "buttons": [
                    {"id": id, "type": type, "button_text": button_text},
                    {"id": id2, "type": type2, "button_text": button_text2},
                    {"id": id3, "type": type3, "button_text": button_text3},
                ]
            }
        )

    async def add_listkeypad_InlineKeypad4vs4(
        self,
        id: str,
        type: str,
        button_text: str,
        id2: str,
        type2: str,
        button_text2: str,
        id3: str,
        type3: str,
        button_text3: str,
        id4: str,
        type4: str,
        button_text4: str,
    ) -> None:
        """add the key pad inline list 4 by 4 / افزودن لیست دکمه های شیشه ای به صورت چهار تایی"""
        self.data_keypad.append(
            {
                "buttons": [
                    {"id": id, "type": type, "button_text": button_text},
                    {"id": id2, "type": type2, "button_text": button_text2},
                    {"id": id3, "type": type3, "button_text": button_text3},
                    {"id": id4, "type": type4, "button_text": button_text4},
                ]
            }
        )

    async def add_listkeypad_InlineKeypad_(self, datas) -> None:
        """add datas for glass messages / افزودن اطلاعات به صورت دستی برای لیست دکمه های شیشه ای"""
        self.data_keypad.append(datas)

    async def delete_listkeypad_InlineKeypad(self) -> None:
        """clear key pad inline list / پاکسازی لیست دکمه های شیشه ای"""
        self.data_keypad = []

    async def send_message_keypad_InlineKeypad(
        self,
        chat_id: str,
        text: str,
        disable_notification: bool = False,
        reply_to_message_id: Optional[str] = None,
    ) -> dict:
        """sending message key pad inline / ارسال پیام با دکمه شیشه ای"""
        data = {
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "chat_id": chat_id,
            "text": text,
            "inline_keypad": {"rows": self.data_keypad},
        }
        result = await self.send_requests(
            "sendMessage",
            data,
        )
        return result

    async def edit_message_keypad_Inline(
        self,
        chat_id: str,
        text: str,
        disable_notification: bool = False,
        reply_to_message_id: Optional[str] = None,
    ) -> dict:
        """editing the text key pad inline / ویرایش متن پیام شیشه ای"""
        data = {
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "chat_id": chat_id,
            "text": text,
            "inline_keypad": {"rows": self.data_keypad},
        }
        result = await self.send_requests(
            "editMessageText",
            data,
        )
        return result

    async def add_listkeypad(self, id: str, type: str, button_text: str) -> None:
        """add the key pad texti list 1 by 1 / افزودن لیست دکمه متنی به صورت تکی"""
        self.data_keypad2.append(
            {"buttons": [{"id": id, "type": type, "button_text": button_text}]}
        )

    async def add_listkeypad2vs2(
        self,
        id: str,
        type: str,
        button_text: str,
        id2: str,
        type2: str,
        button_text2: str,
    ) -> None:
        """add the key pad texti list 2 by 2 / افزودن لیست دکمه متنی به صورت دوتایی"""
        self.data_keypad2.append(
            {
                "buttons": [
                    {"id": id, "type": type, "button_text": button_text},
                    {"id": id2, "type": type2, "button_text": button_text2},
                ]
            }
        )

    async def add_listkeypad3vs3(
        self,
        id: str,
        type: str,
        button_text: str,
        id2: str,
        type2: str,
        button_text2: str,
        id3: str,
        type3: str,
        button_text3: str,
    ) -> None:
        """add the key pad texti list 3 by 3 / افزودن لیست دکمه متنی به صورت سه تایی"""
        self.data_keypad2.append(
            {
                "buttons": [
                    {"id": id, "type": type, "button_text": button_text},
                    {"id": id2, "type": type2, "button_text": button_text2},
                    {"id": id3, "type": type3, "button_text": button_text3},
                ]
            }
        )

    async def add_listkeypad4vs4(
        self,
        id: str,
        type: str,
        button_text: str,
        id2: str,
        type2: str,
        button_text2: str,
        id3: str,
        type3: str,
        button_text3: str,
        id4: str,
        type4: str,
        button_text4: str,
    ) -> None:
        """add the key pad texti list 4 by 4 / افزودن لیست دکمه متنی به صورت چهارتایی"""
        self.data_keypad2.append(
            {
                "buttons": [
                    {"id": id, "type": type, "button_text": button_text},
                    {"id": id2, "type": type2, "button_text": button_text2},
                    {"id": id3, "type": type3, "button_text": button_text3},
                    {"id": id4, "type": type4, "button_text": button_text4},
                ]
            }
        )

    async def add_listkeypad_(self, datas) -> None:
        """add datas for texti messages / افزودن اطلاعات به صورت دستی برای لیست دکمه های متنی"""
        self.data_keypad2.append(datas)

    async def delete_listkeypad(self) -> None:
        """clear key pad texti list / پاکسازی لیست دکمه های متنی"""
        self.data_keypad2 = []

    async def send_message_keypad(
        self,
        chat_id: str,
        text: str,
        disable_notification: bool = False,
        reply_to_message_id: Optional[str] = None,
        resize_keyboard: bool = True,
        on_time_keyboard: bool = False,
    ) -> dict:
        """sending message key pad texti / ارسال پیام با دکمه متنی"""
        data = {
            "chat_id": chat_id,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "text": text,
            "chat_keypad_type": "New",
            "chat_keypad": {
                "rows": self.data_keypad2,
                "resize_keyboard": resize_keyboard,
                "on_time_keyboard": on_time_keyboard,
            },
        }
        result = await self.send_requests(
            "sendMessage",
            data,
        )
        return result

    async def _upload_file(self, url: str, file_name: str, file: str):
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

    async def send_file(
        self,
        chat_id: str,
        file: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif"] = "File",
        disable_notification: bool = False,
    ) -> dict:
        """sending file with types ['File', 'Image', 'Voice', 'Music', 'Gif'] / ارسال فایل با نوع های فایل و عکس و پیغام صوتی و موزیک و گیف"""
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

    async def send_image(
        self,
        chat_id: str,
        image: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        disable_notification: bool = False,
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

    async def send_voice(
        self,
        chat_id: str,
        voice: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        disable_notification: bool = False,
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

    async def send_music(
        self,
        chat_id: str,
        music: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        disable_notification: bool = False,
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

    async def send_gif(
        self,
        chat_id: str,
        gif: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        disable_notification: bool = False,
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

    async def send_sticker(
        self,
        chat_id: str,
        id_sticker: str,
        reply_to_message_id: str = None,
        disable_notification: bool = False,
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

    async def set_endpoint(self, url: str, type: str = "GetSelectionItem") -> dict:
        """set endpoint url / تنظیم ادرس اند پوینت"""
        return await self.send_requests(
            "updateBotEndpoints", {"url": url, "type": type}
        )

    async def set_token_fast_rub(self) -> bool:
        """seting token in fast_rub for getting click glass messages and updata messges / تنظیم توکن در فست روب برای گرفتن کلیک های روی پیام شیشه ای و آپدیت پیام ها"""
        async with httpx.AsyncClient() as cl:
            r = (
                await cl.get(
                    f"https://fast-rub.ParsSource.ir/set_token?token={self.token}"
                )
            ).json()
        if r["status"]:
            await self.set_endpoint(r["url_endpoint"], "GetSelectionItem")
            return True
        else:
            if r["error"] == "This token exists":
                await self.set_endpoint(r["url_endpoint"], "GetSelectionItem")
                return True
        return False

    def on_message_updates(self, filters: Optional[Filter] = None):
        """دکوراتور برای ثبت هندلر پیام‌ها"""
        def decorator(handler: Callable[[Update], Awaitable[None]]):
            @wraps(handler)
            async def wrapped(update):
                if filters == None or filters(update):
                    try:
                        await handler(update)
                    except Exception as e:
                        print(f"Error in message handler: {e}")

            self._message_handlers.append(wrapped)
            return handler

        return decorator

    async def _process_messages(self):
        while self._running:
            try:
                async with httpx.AsyncClient() as cl:
                    response = (
                        await cl.get(self._on_url, timeout=self.time_out)
                    ).json()
            except:
                await self.set_token_fast_rub()
            if response and response.get("status") is True:
                results = response.get("updates", [])
                if results:
                    for result in results:
                        update = Update(result, self)
                        for handler in self._message_handlers:
                            await handler(update)
            #     mes = (await self.get_updates())
            #     if mes['status']=="INVALID_ACCESS":
            #         raise PermissionError("Due to Rubika's restrictions, access to retrieve messages has been blocked. Please try again.")
            #     for message in mes['data']['updates']:
            #         time_sended_mes = int(message['new_message']['time'])
            #         now = int(time.time())
            #         time_ = 10
            #         if (now - time_sended_mes < time_) and (not message['new_message']['message_id'] in last):
            #             last.append(message['new_message']['message_id'])
            #             if len(last) > 500:
            #                 last.pop(-1)
            #             update_obj = Update(message,self)
            #             for handler in self._message_handlers:
            #                 await handler(update_obj)
            # while self._running_:
            #     try:
            #         async with httpx.AsyncClient() as cl:
            #             response=(await cl.get(self._button_url,timeout=self.time_out)).json()
            #         if response and response.get('status') is True:
            #             results = response.get('updates',[])
            #             if results:
            #                 for result in results:
            #                     update = UpdateButton(result)
            #                     for handler in self._button_handlers:
            #                         await handler(update)
            await asyncio.sleep(0.5)

    def run(self):
        """running on message updates / اجرا گرفتن پیام ها"""
        self._running = True
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._process_messages())

    async def _fetch_button_updates(self):
        while self._running_:
            try:
                async with httpx.AsyncClient() as cl:
                    response = (
                        await cl.get(self._button_url, timeout=self.time_out)
                    ).json()
                if response and response.get("status") is True:
                    results = response.get("updates", [])
                    for result in results:
                        update = Update(result, self)
                        for handler in self._message_handlers:
                            await handler(update)
            except:
                await self.set_token_fast_rub()
            await asyncio.sleep(1)

    def on_button(self):
        """getting clicks on buttons class / گرفتن کلیک های روی دکمه های شیشه ای"""

        def decorator(handler: Callable[[UpdateButton], Awaitable[None]]):
            self._button_handlers.append(handler)
            return handler

        return decorator

    def run_on_button(self):
        """اجرا گرفتن کلیک های روی پیام های شیشه ای"""
        self._running_ = True
        asyncio.run(self._fetch_button_updates())


class Update:
    def __init__(self, update_data: dict, client: "Client"):
        self._data = update_data
        self._client = client
        self.message = update_data.get("new_message", {})

    @property
    def text(self) -> str:
        """text for message / متن پیام"""
        return self._data["update"]["new_message"]["text"]

    @property
    def message_id(self) -> int:
        """message id for message / آیدی پیام ارسال شده"""
        return self._data["update"]["new_message"]["message_id"]

    @property
    def chat_id(self) -> str:
        """chat id for message / چت آیدی پیام ارسال شده"""
        return self._data["update"]["chat_id"]

    @property
    def time(self) -> int:
        """time sended message / زمان پیام ارسال شده"""
        return int(self._data["update"]["new_message"]["time"])

    @property
    def sender_type(self) -> str:
        """type for chat / نوع پیام ارسال شده چت"""
        return self._data["update"]["new_message"]["sender_type"]

    @property
    def sender_id(self) -> str:
        """guid user sended / شناسه گوید ارسال کننده پیام"""
        return self._data["update"]["new_message"]["sender_id"]

    async def reply(self, text: str) -> dict:
        """reply text / ریپلای متن"""
        return await self._client.send_text(
            text, self.chat_id, reply_to_message_id=self.message_id
        )

    async def reply_poll(self, question: str, options: list) -> dict:
        """reply poll / ریپلای نظرسنجی"""
        return await self._client.send_poll(self.chat_id, question, options)

    async def reply_contact(
        self, first_name: str, phone_number: str, last_name: str = None
    ) -> dict:
        """reply contact / ریپلای مخاطب"""
        return await self._client.send_contact(
            self.chat_id,
            first_name,
            last_name,
            phone_number,
            reply_to_message_id=self.message_id,
        )

    async def reply_location(self, latitude: str, longitude: str) -> dict:
        """reply location / ریپلای موقعیت مکانی"""
        return await self._client.send_location(
            self.chat_id, latitude, longitude, reply_to_message_id=self.message_id
        )

    async def reply_file(
        self,
        chat_id: str,
        file: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif"] = "File",
        disable_notification: bool = False,
    ) -> dict:
        """reply file / ریپلای فایل"""
        return await self._client.send_file(
            chat_id,
            file,
            name_file,
            text,
            reply_to_message_id,
            type_file,
            disable_notification,
        )

    async def reply_image(
        self,
        chat_id: str,
        image: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        disable_notification: bool = False,
    ) -> dict:
        """reply image / رپیلای تصویر"""
        return await self._client.send_image(
            chat_id, image, name_file, text, reply_to_message_id, disable_notification
        )

    async def reply_voice(
        self,
        chat_id: str,
        voice: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        disable_notification: bool = False,
    ) -> dict:
        """reply voice / رپیلای ویس"""
        return await self._client.send_voice(
            chat_id, voice, name_file, text, reply_to_message_id, disable_notification
        )

    async def reply_music(
        self,
        chat_id: str,
        music: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        disable_notification: bool = False,
    ) -> dict:
        """reply voice / رپیلای موزیک"""
        return await self._client.send_music(
            chat_id, music, name_file, text, reply_to_message_id, disable_notification
        )

    async def reply_gif(
        self,
        chat_id: str,
        gif: str | Path | bytes,
        name_file: str,
        text: str = None,
        reply_to_message_id: str = None,
        disable_notification: bool = False,
    ) -> dict:
        """reply voice / رپیلای گیف"""
        return await self._client.send_gif(
            chat_id, gif, name_file, text, reply_to_message_id, disable_notification
        )

    def __str__(self) -> str:
        return str(self._data)

    def __repr__(self) -> str:
        return self.__str__()


class UpdateButton:
    def __init__(self, data: dict):
        self._data = data

    @property
    def raw_data(self) -> dict:
        return self._data

    @property
    def button_id(self) -> str:
        """button id clicked / آیدی دکمه کلیک شده"""
        return self._data["inline_message"]["aux_data"]["button_id"]

    @property
    def chat_id(self) -> str:
        """chat id clicked / چت آیدی کلیک شده"""
        return self._data["inline_message"]["chat_id"]

    @property
    def message_id(self) -> str:
        """message id for message clicked glass button / آیدی پیام کلیک شده روی دکمه شیشه ای"""
        return self._data["inline_message"]["message_id"]

    @property
    def sender_id(self) -> str:
        """guid for clicked button glass / شناسه گوید کاربر کلیک کرده روی دکمه شیشه ای"""
        return self._data["inline_message"]["sender_id"]

    @property
    def text(self) -> str:
        """text for button clicked / متن دکمه شیشه ای که روی آن کلیک شده"""
        return self._data["inline_message"]["text"]

    def __str__(self):
        return str(self._data)
