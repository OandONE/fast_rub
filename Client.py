import httpx
import time
import os
import json
from typing import Optional,Callable,Awaitable
from colorama import Fore
import asyncio
from .filters import Filter
from functools import wraps
import mimetypes

last=[]

class Client:
    def __init__(
        self,
        name_session: str,
        token: str = None,
        user_agent: str = None,
        time_out: Optional[int] = 60,
        display_welcome=True,
    ):
        name = name_session + ".faru"
        self.token = token
        self.time_out = time_out
        self.user_agent = user_agent
        self._message_handlers = []
        self._running = False
        self.list_=[]
        self.data_keypad=[]
        self.data_keypad2=[]
        if os.path.isfile(name):
            with open(name, "r", encoding="utf-8") as file:
                text_json_fast_rub_session = json.load(file)
                self.token = text_json_fast_rub_session["token"]
                self.time_out = text_json_fast_rub_session["time_out"]
                self.user_agent = text_json_fast_rub_session["user_agent"]
        else:
            if token == None:
                token = input("Enter your token : ")
                while not token:
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

    async def send_requests(self, method, data_: Optional[dict] = None, type_send="get"):
        url = f"https://botapi.rubika.ir/v3/{self.token}/{method}"
        if self.user_agent != None:
            headers = {"'User-Agent'": self.user_agent,'Content-Type': 'application/json'}
        else:
            headers = {'Content-Type': 'application/json'}
        if type_send == "post":
            try:
                async with httpx.AsyncClient(timeout=self.time_out) as cl:
                    if data_==None:
                        result = await cl.post(url, headers=headers)
                        return result.json()
                    else:
                        result = await cl.post(url, headers=headers,json=data_)
                        return result.json()
            except TimeoutError:
                raise TimeoutError("Please check the internet !")
    
    async def get_me(self):
        result = await self.send_requests(method="getMe", type_send="post")
        return result

    async def send_text(
        self,
        text: str,
        chat_id: str,
        disable_notification: Optional[bool] = False,
        reply_to_message_id:Optional[str]=None,
    ):
        data = {
            "chat_id": chat_id,
            "text": text,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id
        }
        result = await self.send_requests("sendMessage", data, type_send="post")
        return result
    
    async def send_poll(self, chat_id: str, question: str, options: list):
        data = {"chat_id": chat_id, "question": question, "options": options}
        result = await self.send_requests("sendPoll", data, type_send="post")
        return result

    async def send_location(
        self,
        chat_id: str,
        latitude: str,
        longitude: str,
        chat_keypad: str=None,
        disable_notification: Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
        chat_keypad_type: Optional[str] = None,
    ):
        data = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude,
            "chat_keypad": chat_keypad,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "chat_keypad_type": chat_keypad_type,
        }
        result = await self.send_requests("sendLocation", data, type_send="post")
        return result

    async def send_contact(
        self,
        chat_id: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        chat_keypad: str=None,
        chat_keypad_type: str=None,
        inline_keypad:str=None,
        reply_to_message_id: str = None,
        disable_notificatio: bool = False,
    ):
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
        result = await self.send_requests("sendContact", data, type_send="post")
        return result

    async def get_chat(self, chat_id: str):
        data = {"chat_id": chat_id}
        result = await self.send_requests("getChat", data, type_send="post")
        return result

    async def get_updates(self, limit: int=100, offset_id: str = None):
        data = {"offset_id": offset_id, "limit": limit}
        result = await self.send_requests("getUpdates", data, type_send="post")
        return result

    async def forward_message(
        self,
        from_chat_id: str,
        message_id: str,
        to_chat_id: str,
        disable_notification: bool = False,
    ):
        data = {
            "from_chat_id": from_chat_id,
            "message_id": message_id,
            "to_chat_id": to_chat_id,
            "disable_notification": disable_notification,
        }
        result = await self.send_requests("forwardMessage", data, type_send="post")
        return result

    async def edit_message_text(self, chat_id: str, message_id: str, text: str):
        data = {"chat_id": chat_id, "message_id": message_id, "text": text}
        result = await self.send_requests("editMessageText", data, type_send="post")
        return result

    async def edit_message_keypad(self, chat_id: str, message_id: str, rows: list):
        """مثال rows :
        "rows": [
                {
                    "buttons": [
                    {
                        "id": "100",
                        "type": "Simple",
                        "button_text": "Add Account"
                    }
                    ]
                },
                {
                    "buttons": [
                    {
                        "id": "101",
                        "type": "Simple",
                        "button_text": "Edit Account"
                    },
                    {
                        "id": "102",
                        "type": "Simple",
                        "button_text": "Remove Account"
                    }
                    ]
                }
                ]"""
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "inline_keypad": {"rows": rows},
        }
        result = await self.send_requests("editMessageText", data, type_send="post")
        return result

    async def delete_message(self, chat_id: str, message_id: str):
        data = {"chat_id": chat_id, "message_id": message_id}
        result = await self.send_requests("deleteMessage", data, type_send="post")
        return result

    def add_commands(self,command:str,description:str):
            """مثال list_commands :
        [
            "help","this is a help"
        ]"""
            self.list_.append({"command": command.replace("/",""), "description": description})

    async def set_commands(self):
        result = await self.send_requests("setCommands", {"bot_commands":self.list_}, type_send="post")
        return result

    async def delete_commands(self):
        self.list_=[]
        result = await self.send_requests("setCommands", self.list_, type_send="post")
        return result

    async def add_listkeypad_InlineKeypad(self,id:str,type:str,button_text:str):
        self.data_keypad.append({"buttons":[{"id": id,"type": type,"button_text": button_text}]})

    async def add_listkeypad_InlineKeypad2vs2(self,id:str,type:str,button_text:str,id2:str,type2:str,button_text2:str):
        self.data_keypad.append({"buttons":[{"id": id,"type": type,"button_text": button_text},{"id": id2,"type": type2,"button_text": button_text2}]})

    async def delete_listkeypad_InlineKeypad(self):
        self.data_keypad=[]

    async def send_message_keypad_InlineKeypad(self,chat_id:str,text:str,disable_notification:bool=False,reply_to_message_id:Optional[str]=None):
        data = {
            "disable_notification":disable_notification,
            "reply_to_message_id":reply_to_message_id,
            "chat_id": chat_id,
            "text": text,
            "inline_keypad": {
                "rows": self.data_keypad
            }
        }
        result=await self.send_requests("sendMessage",data,type_send="post")
        return result
    
    async def add_listkeypad(self,id:str,type:str,button_text:str):
        self.data_keypad2.append({"buttons":[{"id": id,"type": type,"button_text": button_text}]})

    async def add_listkeypad2vs2(self,id:str,type:str,button_text:str,id2:str,type2:str,button_text2:str):
        self.data_keypad2.append({"buttons":[{"id": id,"type": type,"button_text": button_text},{"id": id2,"type": type2,"button_text": button_text2}]})

    async def delete_listkeypad(self):
        self.data_keypad2=[]

    async def send_message_keypad(self,chat_id:str,text:str,disable_notification:bool=False,reply_to_message_id:Optional[str]=None,resize_keyboard:bool=True,on_time_keyboard:bool=False):
        data = {
            "chat_id": chat_id,
            "disable_notification":disable_notification,
            "reply_to_message_id":reply_to_message_id,
            "text": text,
            "chat_keypad_type": "New",
            "chat_keypad": {
                "rows": self.data_keypad2,
                "resize_keyboard": resize_keyboard,
                "on_time_keyboard": on_time_keyboard
            }
        }
        result=await self.send_requests("sendMessage",data,type_send="post")
        return result

    def on_message_updates(self, filters: Optional[Filter] = None):
        def decorator(handler):
            @wraps(handler)
            async def wrapped(update):
                if filters is None or filters(update):
                    return await handler(update)
            self._message_handlers.append(wrapped)
            return handler
        return decorator

    async def _process_messages(self, time_updata_sleep: int = 1):
        while self._running:
            try:
                async with httpx.AsyncClient() as cl:
                    await cl.get("https://rubika.ir/",timeout=self.time_out)
            except:
                raise TimeoutError("please check the your internet .")
            mes = (await self.get_updates(limit=100))
            if mes['status']=="INVALID_ACCESS":
                raise PermissionError("Due to Rubika's restrictions, access to retrieve messages has been blocked. Please try again.")
            for message in mes['data']['updates']:
                time_sended_mes = int(message['new_message']['time'])
                now = int(time.time())
                time_ = time_updata_sleep + 4
                if (now - time_sended_mes < time_) and (not message['new_message']['message_id'] in last):
                    last.append(message['new_message']['message_id'])
                    if len(last) > 500:
                        last.pop(-1)
                    update_obj = Update(message,self)
                    for handler in self._message_handlers:
                        await handler(update_obj)
            await asyncio.sleep(time_updata_sleep)

    def run(self):
        self._running = True
        asyncio.run(self._process_messages())

class Update:
    def __init__(self, update_data: dict,client:'Client'):
        self._data = update_data
        self._client=client
        self.message = update_data.get('new_message', {})
    @property
    def text(self) -> str:
        return self._data['new_message']['text']
    @property
    def message_id(self) -> int:
        return self._data['new_message']['message_id']
    @property
    def chat_id(self) -> str:
        return self._data['chat_id']
    @property
    def time(self) -> int:
        return int(self._data['new_message']['time'])
    @property
    def sender_type(self) -> str:
        return self._data['new_message']['sender_type']
    @property
    def sender_id(self) -> str:
        return self._data['new_message']['sender_id']
    async def reply(self, text: str) -> None:
        return await self._client.send_text(text,self.chat_id,reply_to_message_id=self.message_id)
    async def reply_poll(self, question: str,options : list) -> None:
        return await self._client.send_poll(self.chat_id,question,options)
    async def reply_contact(self, first_name: str,phone_number:str,last_name : str = None) -> None:
        return await self._client.send_contact(self.chat_id,first_name,last_name,phone_number,reply_to_message_id=self.message_id)
    async def reply_location(self,latitude:str,longitude:str):
        return await self._client.send_location(self.chat_id,latitude,longitude,reply_to_message_id=self.message_id)
    def __str__(self) -> str:
        return str(self._data)
    def __repr__(self) -> str:
        return self.__str__()
