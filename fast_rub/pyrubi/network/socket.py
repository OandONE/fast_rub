try:
    import websockets
except ImportError:
    websockets = None
from .helper import Helper
from ..types import Message
from ..exceptions import NotRegistered, TooRequests
import asyncio
from ..filters import Filter, legacy_filter
import inspect
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..methods import Methods

class Socket:
    def __init__(
        self,
        methods: "Methods"
    ):
        self.methods = methods
        self.handlers = {}
        self._running = False
        self._ws = None
    
    async def connect(self):
        print("Connecting to the WebSocket...")
        await self.methods._process_before_run()
        if websockets is None:
            raise ImportError("The websockets library is not installed! for install: 'pip install fastrub[pyrubi]'")
        self._running = True
        socket_server = await Helper.get_socket_server()
        async with websockets.connect(socket_server) as ws:
            self._ws = ws
            await self.on_open(ws)
            async for message in ws:
                await self.on_message(message)
    
    async def on_open(self, ws):
        await self.handshake(ws)
        asyncio.create_task(self.keep_alive(ws))
        await self.methods._process_on_live()
        print("Connected.")
    
    async def handshake(self, ws, data=None):
        payload = data or json.dumps({
            "auth": self.methods.sessionData["auth"],
            "api_version": self.methods.apiVersion,
            "method": "handShake"
        })
        await ws.send(payload)
    
    async def keep_alive(self, ws):
        while self._running:
            try:
                await asyncio.sleep(30)
                await self.methods.getChatsUpdates()
                await self.handshake(ws, "{}")
            except NotRegistered:
                raise
            except TooRequests:
                break
            except Exception:
                continue
    
    async def on_message(self, raw_message):
        if not raw_message:
            return
        
        message = json.loads(raw_message)
        
        if message.get("type") != "messenger":
            return
        
        decrypted = self.methods.crypto.decrypt(message["data_enc"])
        data = json.loads(decrypted)
        
        if not data.get("message_updates"):
            return
        
        for handler, filters in self.handlers.items():
            msg_obj = Message(data, self.methods)
            
            # run filter by management error
            try:
                should_process = all(f(msg_obj) for f in filters)
            except Exception as e:
                await self.methods._process_on_error(e=e, update=msg_obj)
                continue
            
            if not should_process:
                continue
            
            # async run handler
            if inspect.iscoroutinefunction(handler):
                asyncio.create_task(self._safe_run_async(handler, msg_obj))
            # sync run handler
            else:
                await self._safe_run_sync(handler, msg_obj)


    async def _safe_run_async(self, handler, msg_obj):
        try:
            await handler(msg_obj)
        except Exception as e:
            await self.methods._process_on_error(e=e, update=msg_obj)


    async def _safe_run_sync(self, handler, msg_obj):
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, handler, msg_obj)
        except Exception as e:
            await self.methods._process_on_error(e=e, update=msg_obj)
    
    def add_handler(self, func, filters=None):
        if filters and isinstance(filters, list) and all(isinstance(f, str) for f in filters):
            filters = [legacy_filter(filters)]
        elif isinstance(filters, Filter):
            filters = [filters]
        elif not filters:
            filters = []
        self.handlers[func] = filters
        return func
    
    async def stop(self):
        self._running = False
        if self._ws:
            await self._ws.close()
