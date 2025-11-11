from websocket import WebSocketApp
from .helper import Helper
from json import dumps, loads
from threading import Thread
from ..types import Message
from ..exceptions import NotRegistered, TooRequests
from ..utils import Utils
from re import match
from time import sleep
from typing import Optional , List, Union
import asyncio
from ..filters import Filter,legacy_filter

class Socket:
    def __init__(self, methods) -> None:
        self.methods = methods
        self.handlers = {}

    def connect(self) -> None:
        print("Connecting to the webSocket...")
        ws = WebSocketApp(
            Helper.getSocketServer(),
            on_open=self.onOpen,
            on_message=self.onMessage
        )
        ws.run_forever()

    def handShake(self, ws, data=None) -> None:
        ws.send(
            data or dumps(
                {
                    "auth": self.methods.sessionData["auth"],
                    "api_version": self.methods.apiVersion,
                    "method": "handShake"
                }
            )
        )

    def keepAlive(self, ws) -> None:
        while True:
            try:
                self.methods.getChatsUpdates()
                self.handShake(ws, "{}")
                sleep(30)
            except NotRegistered:
                raise
            except TooRequests:
                break
            except:
                continue

    def onOpen(self, ws) -> None:
        Thread(target=self.keepAlive, args=[ws]).start()
        self.handShake(ws)
        print("Connected.")

    def onMessage(self, _, message: str) -> None:
        if not message:
            return
        
        message: dict = loads(message)

        if not message.get("type") == "messenger":
            return
        
        message: dict = loads(self.methods.crypto.decrypt(message["data_enc"]))

        if not message.get("message_updates"):
            return

        for handler in self.handlers:
            filters: List[Filter] = self.handlers[handler]
            message_obj: Message = Message(message, self.methods)
            should_process = True
            for filter_obj in filters:
                if not filter_obj(message_obj):
                    should_process = False
                    break

            if should_process:
                Thread(target=lambda: asyncio.run(handler(message_obj))).start()


    def addHandler(self, func, filters: Union[List[Filter], List[str], Filter]) -> None:
        if filters and isinstance(filters, list) and all(isinstance(f, str) for f in filters):
            filters = [legacy_filter(filters)]
        elif isinstance(filters, Filter):
            filters = [filters]
        elif not filters:
            filters = []
        self.handlers[func] = filters
        return func