import httpx
import time
import os
import json
from .ram import last
from typing import Optional
from colorama import Fore

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

    async def send_requests(self, method, data: Optional[dict] = None, type_send="get"):
        url = f"https://botapi.rubika.ir/v3/{self.token}/{method}"
        if self.user_agent != None:
            headers = {"'User-Agent'": self.user_agent}
        else:
            headers = None
        if type_send == "post":
            try:
                async with httpx.AsyncClient() as cl:
                    result = await cl.post(url, headers=headers)
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
            "reply_to_message_id": reply_to_message_id,
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
        chat_keypad: str,
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
        chat_keypad: str,
        chat_keypad_type: str,
        inline_keypad,
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

    async def get_updates(self, limit: int, offset_id: str = None):
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
        result = await self.send_requests("frowardMessage", data, type_send="post")
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

    async def set_commands(self, bot_commands: list):
        """مثال bot_commands :
        [{
                    "command": "command1",
                    "description": "description1"
                },
                {
                    "command": "command2",
                    "description": "description2"
                }
        ]"""
        data = {"bot_commands": [bot_commands]}
        result = await self.send_requests("setCommands", data, type_send="post")
        return result

    # async def send_message_keypad_InlineKeypad(self,chat_id:str,text:str,chat_keypad,inline_keypad,chat_keypad_type,disable_notification:bool=False,reply_to_message_id:Optional[str]=None):
    #     """مثال :
    #     {
    #                     "buttons": [
    #                         {
    #                             "id": "100",
    #                             "type": "Simple",
    #                             "button_text": "Add Account"
    #                         }
    #                     ]
    #                 },
    #                 {
    #                     "buttons": [
    #                         {
    #                             "id": "101",
    #                             "type": "Simple",
    #                             "button_text": "Edit Account"
    #                         },
    #                         {
    #                             "id": "102",
    #                             "type": "Simple",
    #                             "button_text": "Remove Account"
    #                         }
    #                     ]
    #                 }"""
    #     data = {
    #         "chat_id": chat_id,
    #         "text": "Welcome",
    #         "inline_keypad": {
    #             "rows": [
    #                 rows
    #             ]
    #         }
    #     }
    #     result=await self.send_requests("sendMessage",data,type_send="post")
    #     return result
    # async def send_message_keypad(self,chat_id:str,text:str,chat_keypad_type,chat_keypad,disable_notification:bool=False,reply_to_message_id:Optional[str]=None):
    #     data = {
    #         "chat_id": chat_id,
    #         "text": "Welcome",
    #         "chat_keypad_type": "New",
    #         "chat_keypad": {
    #             "rows": [
    #                 {
    #                     "buttons": [
    #                         {
    #                             "id": "100",
    #                             "type": "Simple",
    #                             "button_text": "Add Account"
    #                         }
    #                     ]
    #                 },
    #                 {
    #                     "buttons": [
    #                         {
    #                             "id": "101",
    #                             "type": "Simple",
    #                             "button_text": "Edit Account"
    #                         },
    #                         {
    #                             "id": "102",
    #                             "type": "Simple",
    #                             "button_text": "Remove Account"
    #                         }
    #                     ]
    #                 }
    #             ],
    #             "resize_keyboard": True,
    #             "on_time_keyboard": False
    #         }
    #     }
    #     result=await self.send_requests("sendMessage",data,type_send="post")
    #     return result
    async def on_message_updatas(self,time_updata_sleep:float=0.5):
        while True:
            mes=(await self.get_updates(limit=100))['data']['updates']
            for message in mes:
                time_sended_mes=int(message['new_message']['time'])
                now=int(time.time())
                time_=time_updata_sleep+1
                if (now-time_sended_mes<time_) and (not message['new_message']['message_id'] in last):
                    last.append(message['new_message']['message_id'])
                    if len(last)>500:
                        last.pop(-1)
                    return message
            time.sleep(time_updata_sleep)
