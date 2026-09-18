"""
شبیه‌ساز ربات (Dry Run) برای FastRub.
FastRub Dry Run simulator — run and test the bot without a real Rubika connection.

ربات با `Client(name, dry_run=True)` بدون توکن واقعی و بدون اینترنت اجرا می‌شود.
آپدیت‌های ورودی با متدهای receive_* شبیه‌سازی می‌شوند و همهٔ ارسال‌های ربات
در `bot.mock.sent` و `bot.mock.requests` ثبت می‌شوند تا در تست‌ها بررسی شوند.
"""
import json
import time
import uuid
import random
import logging
from typing import TYPE_CHECKING, Any, Literal

from .async_sync import wrap_all_async_methods

if TYPE_CHECKING:
    from .client import Client
    from ..types import Update, UpdateButton


# متودهایی که پاسخشان باید شامل message_id باشد (خروجی msg_update)
_SEND_METHODS = {
    "sendMessage", "sendPoll", "sendLocation", "sendContact",
    "sendFile", "sendSticker", "editMessageText", "forwardMessage",
}


class MockResponse:
    """جایگزین سبک httpx.Response برای حالت Dry Run"""

    def __init__(self, payload: dict | list | None = None, status_code: int = 200):
        self._payload = payload if payload is not None else {}
        self.status_code = status_code

    def json(self) -> dict | list:
        return self._payload

    @property
    def text(self) -> str:
        return json.dumps(self._payload, ensure_ascii=False)

    @property
    def content(self) -> bytes:
        return self.text.encode("utf-8")

    @property
    def headers(self) -> dict:
        return {"content-length": str(len(self.content))}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"Mock HTTP Error {self.status_code}")


class MockSession:
    """سشن ساختگی — همان اینترفیس Session واقعی ولی بدون دیتابیس و بدون توکن واقعی"""

    def __init__(
        self,
        token: str,
        user_agent: str | None = None,
        time_out: float | None = None,
        display_welcome: bool = False,
        view_logs: bool = False,
        save_logs: bool = False,
        offset_id: str | None = None,
        save_offset_id: bool = True,
    ):
        self.token = token
        self.user_agent = user_agent
        self.time_out = time_out
        self.display_welcome = display_welcome
        self.view_logs = view_logs
        self.save_logs = save_logs
        self.offset_id = offset_id or ""
        self.save_offset_id = save_offset_id

    async def save(self) -> None:
        pass

    async def close(self) -> None:
        pass


class MockNetwork:
    """
    جایگزین Network در حالت Dry Run.

    - هیچ درخواستی به سرور روبیکا زده نمی‌شود
    - پاسخ‌های معقول برای همهٔ متودهای Bot API برمی‌گرداند
    - همهٔ درخواست‌ها در `requests` و ارسال پیام‌ها در `sent` ثبت می‌شوند
    - آپدیت‌های ورودی با receive_* / enqueue_* شبیه‌سازی می‌شوند

    مثال:
        bot = Client("test_bot", dry_run=True)

        @bot.on_message(filters.text("سلام"))
        async def hello(msg):
            await msg.reply("سلام!")

        await bot.start()
        await bot.mock.receive_text(chat_id="b" + "a" * 31, text="سلام")

        assert bot.mock.last_sent["data"]["text"] == "سلام!"
    """

    def __init__(
        self,
        client: "Client",
        token: str = "",
        base_urls: list | None = None,
        logger: logging.Logger | None = None,
    ):
        self.client = client
        self.token = token
        self.base_urls = base_urls or ["mock://botapi.local/"]
        self.logger = logger or logging.getLogger("fast_rub.mock")

        # ثبت درخواست‌ها و ارسال‌ها برای تست
        self.requests: list[dict[str, Any]] = []
        self.sent: list[dict[str, Any]] = []

        # پاسخ‌های دستی کاربر — {method: data} که جای پاسخ پیش‌فرض برمی‌گردد
        self.responses: dict[str, dict] = {}

        # متودهایی که می‌خواهید عمداً خطا بدهند (تست خطا)
        self.fail_methods: set[str] = set()

        # چت‌های شبیه‌سازی‌شده برای getChat
        self.chats: dict[str, dict] = {}

        # صف آپدیت‌ها برای get_updates (حالت run)
        self._queue: list[dict] = []
        self._offset_counter = 0
        self._closed = False

        self.bot_guid = self.new_guid("b")

    # ═══════════════════════════════════
    # region 🧰 ساخت داده‌های شبیه‌سازی
    # ═══════════════════════════════════

    @staticmethod
    def new_message_id() -> str:
        """آیدی پیام ۱۹ رقمی مثل روبیکا"""
        return str(random.randint(10**18, 10**19 - 1))

    @staticmethod
    def new_guid(prefix: Literal["b", "g", "c"] = "b") -> str:
        """شناسهٔ گوید ۳۲ کاراکتری مثل روبیکا"""
        return prefix + uuid.uuid4().hex[:31]

    def add_chat(
        self,
        chat_id: str | None = None,
        title: str | None = None,
        chat_type: Literal["User", "Group", "Channel"] | None = None,
    ) -> dict:
        """ثبت یه چت شبیه‌سازی‌شده — برای جواب دادن به getChat"""
        if chat_id is None:
            chat_id = self.new_guid("b")
        if chat_id not in self.chats:
            ctype = chat_type or {"b": "User", "g": "Group", "c": "Channel"}.get(
                chat_id[:1], "User"
            )
            self.chats[chat_id] = {
                "chat_id": chat_id,
                "title": title if title is not None else f"Mock {ctype} {chat_id[1:9]}",
                "first_name": title if ctype == "User" else None,
                "last_name": None,
                "username": None,
                "user_id": chat_id if ctype == "User" else None,
            }
        return self.chats[chat_id]

    def _mock_bot(self) -> dict:
        name = getattr(self.client, "name_session", "mock_bot")
        return {
            "bot_id": self.bot_guid,
            "bot_title": f"{name} (Mock)",
            "description": "FastRub Dry Run Bot",
            "username": str(name).replace(" ", "_").lower(),
            "start_message": "سلام! این یه ربات شبیه‌سازی‌شدهٔ FastRub است ⚡",
            "share_url": "https://rubika.ir/mock_bot",
            "avatar": None,
        }

    def build_text_update(
        self,
        chat_id: str | None = None,
        text: str = "",
        sender_id: str | None = None,
        message_id: str | None = None,
        reply_to_message_id: str | None = None,
        aux_data: dict | None = None,
        message_type: Literal["NewMessage", "UpdatedMessage"] = "NewMessage",
        **extra: Any,
    ) -> dict:
        """ساخت دیکشنری خام آپدیت پیام (همان ساختار Bot API روبیکا)"""
        chat_id = chat_id or self.new_guid("b")
        self.add_chat(chat_id)
        return {
            "type": message_type,
            "chat_id": chat_id,
            "new_message": {
                "message_id": message_id or self.new_message_id(),
                "text": text,
                "time": int(time.time()),
                "sender_id": sender_id or self.new_guid("b"),
                "sender_type": "User",
                "is_edited": message_type == "UpdatedMessage",
                "reply_to_message_id": reply_to_message_id,
                "aux_data": aux_data or {},
                **extra,
            },
        }

    def build_button_update(
        self,
        chat_id: str | None = None,
        button_id: str = "btn",
        sender_id: str | None = None,
        message_id: str | None = None,
        text: str | None = None,
        aux_data: dict | None = None,
    ) -> dict:
        """ساخت دیکشنری خام کلیک دکمهٔ شیشه‌ای"""
        chat_id = chat_id or self.new_guid("b")
        self.add_chat(chat_id)
        full_aux = {"button_id": button_id, **(aux_data or {})}
        return {
            "inline_message": {
                "chat_id": chat_id,
                "message_id": message_id or self.new_message_id(),
                "sender_id": sender_id or self.new_guid("b"),
                "text": text if text is not None else f"button:{button_id}",
                "aux_data": full_aux,
            }
        }

    def build_deleted_update(self, chat_id: str, message_id: str) -> dict:
        """ساخت دیکشنری خام پیام حذف‌شده"""
        self.add_chat(chat_id)
        return {
            "type": "RemoveMessage",
            "chat_id": chat_id,
            "removed_message_id": message_id,
            "update_time": int(time.time()),
            # برای سازگاری با خط لولهٔ پولینگ که update.time را می‌خواند
            "new_message": {
                "message_id": message_id,
                "time": int(time.time()),
                "sender_id": "",
                "is_edited": False,
            },
        }

    # endregion

    # ═══════════════════════════════════
    # region 📥 تزریق آپدیت (اجرا فوری در خط لوله)
    # ═══════════════════════════════════

    async def receive_text(
        self,
        chat_id: str | None = None,
        text: str = "",
        sender_id: str | None = None,
        message_id: str | None = None,
        reply_to_message_id: str | None = None,
        aux_data: dict | None = None,
        **extra: Any,
    ) -> "Update":
        """شبیه‌سازی پیام کاربر — فوراً از فیلترها/هندلرها/کانورسیشن رد می‌شود"""
        update = self.build_text_update(
            chat_id=chat_id,
            text=text,
            sender_id=sender_id,
            message_id=message_id,
            reply_to_message_id=reply_to_message_id,
            aux_data=aux_data,
            **extra,
        )
        return await self.client._mock_dispatch_message(update)

    async def receive_edit(
        self,
        chat_id: str,
        message_id: str,
        new_text: str,
        sender_id: str | None = None,
    ) -> "Update":
        """شبیه‌سازی ویرایش پیام"""
        update = self.build_text_update(
            chat_id=chat_id,
            text=new_text,
            sender_id=sender_id,
            message_id=message_id,
            message_type="UpdatedMessage",
        )
        return await self.client._mock_dispatch_message(update)

    async def receive_deleted(self, chat_id: str, message_id: str) -> "Update":
        """شبیه‌سازی حذف پیام"""
        update = self.build_deleted_update(chat_id, message_id)
        return await self.client._mock_dispatch_message(update)

    async def receive_button(
        self,
        chat_id: str | None = None,
        button_id: str = "btn",
        sender_id: str | None = None,
        message_id: str | None = None,
        text: str | None = None,
        aux_data: dict | None = None,
    ) -> "UpdateButton":
        """شبیه‌سازی کلیک روی دکمهٔ شیشه‌ای"""
        data = self.build_button_update(
            chat_id=chat_id,
            button_id=button_id,
            sender_id=sender_id,
            message_id=message_id,
            text=text,
            aux_data=aux_data,
        )
        return await self.client._mock_dispatch_button(data)

    async def receive_raw(self, update_data: dict) -> "Update | UpdateButton":
        """تزریق آپدیت خام (ساختار Bot API) — نوع آن خودکار تشخیص داده می‌شود"""
        if "inline_message" in update_data:
            return await self.client._mock_dispatch_button(update_data)
        return await self.client._mock_dispatch_message(update_data)

    receive_update = receive_raw

    # endregion

    # ═══════════════════════════════════
    # region 📥 صف آپدیت (دریافت با get_updates)
    # ═══════════════════════════════════

    def enqueue_raw(self, update_data: dict) -> dict:
        """افزودن آپدیت خام به صف — با bot.run() از get_updates دریافت می‌شود"""
        self._queue.append(update_data)
        return update_data

    def enqueue_text(self, **kwargs: Any) -> dict:
        """افزودن پیام متنی به صف — همان ورودی‌های receive_text"""
        return self.enqueue_raw(self.build_text_update(**kwargs))

    def enqueue_button(self, **kwargs: Any) -> dict:
        """افزودن کلیک دکمه به صف — همان ورودی‌های receive_button"""
        return self.enqueue_raw(self.build_button_update(**kwargs))

    def enqueue_deleted(self, chat_id: str, message_id: str) -> dict:
        """افزودن پیام حذف‌شده به صف"""
        return self.enqueue_raw(self.build_deleted_update(chat_id, message_id))

    # endregion

    # ═══════════════════════════════════
    # region 📤 درخواست‌ها (اینترفیس Network)
    # ═══════════════════════════════════

    def _record(self, method: str, data: dict) -> dict:
        entry = {"method": method, "data": dict(data), "time": time.time()}
        self.requests.append(entry)
        return entry

    @property
    def last_sent(self) -> dict | None:
        """آخرین پیام ارسال‌شدهٔ ربات"""
        return self.sent[-1] if self.sent else None

    def get_sent(self, method: str | None = None) -> list[dict]:
        """ارسال‌های ثبت‌شده — قابل فیلتر با نام متود"""
        if method is None:
            return self.sent
        return [s for s in self.sent if s["method"] == method]

    def clear(self) -> None:
        """پاک‌سازی ثبت‌ها و صف (چت‌ها حفظ می‌شوند)"""
        self.requests.clear()
        self.sent.clear()
        self._queue.clear()

    async def send_request(self, method: str, data: dict[str, Any] | None = None) -> dict:
        if self._closed:
            raise RuntimeError("MockNetwork is closed")

        data = data or {}
        self._record(method, data)

        if method in self.fail_methods:
            raise ConnectionError(f"MockNetwork: متود '{method}' عمداً خطا داد (fail_methods)")

        if method in self.responses:
            return json.loads(json.dumps(self.responses[method]))

        m = method.lower()

        if m == "getme":
            return {"bot": self._mock_bot()}

        if m == "getchat":
            chat_id = data.get("chat_id", "")
            if chat_id not in self.chats:
                self.add_chat(chat_id)
            return {"chat": json.loads(json.dumps(self.chats[chat_id]))}

        if m == "getupdates":
            return self._resp_get_updates()

        if m == "requestsendfile":
            return {
                "upload_url": f"mock://upload/{uuid.uuid4().hex}",
                "file_id": f"mock{uuid.uuid4().hex[:20]}",
            }

        if m == "getfile":
            return {
                "file_id": data.get("file_id", ""),
                "file_name": "mock_file",
                "size": 0,
                "download_url": f"mock://download/{data.get('file_id', '')}",
            }

        if method in _SEND_METHODS or m.startswith("send") or m.startswith("edit"):
            response: dict[str, Any] = {"message_id": self.new_message_id()}
            chat_id = data.get("chat_id") or data.get("to_chat_id")
            if chat_id:
                response["chat_id"] = chat_id
            if data.get("file_id"):
                response["file_id"] = data["file_id"]
            self.sent.append({"method": method, "data": dict(data), "time": time.time()})
            return response

        return {}

    def _resp_get_updates(self) -> dict:
        updates = self._queue[:]
        self._queue.clear()
        self._offset_counter += 1
        return {"updates": updates, "next_offset_id": str(self._offset_counter)}

    async def request(
        self,
        url: str,
        data_: dict[str, Any] | list[Any] | None = None,
        type_send: Literal["POST", "GET", "HEAD"] = "POST",
        **kwargs: Any,
    ) -> MockResponse:
        self._record(f"HTTP_{type_send}", {"url": url, "data": data_})
        return MockResponse({"status": "OK", "url": url})

    async def download(
        self,
        url: str,
        path: str = "file",
        show_progress: bool = False,
        max_retries: int | None = None,
    ) -> bool:
        self._record("download", {"url": url, "path": path})
        import os
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(path, "wb") as f:
            f.write(b"fastrub mock file")
        self.logger.info(f"MockNetwork: فایل دانلود شد (شبیه‌سازی): {path}")
        return True

    async def upload(
        self,
        url: str,
        file_path: str | Any,
        file_name: str,
        show_progress: bool = False,
        chunk_size: int = 1024 * 1024,
        max_retries: int | None = None,
    ) -> dict[str, Any]:
        self._record("upload", {"url": url, "file_name": file_name})
        return {"file_id": f"mock{uuid.uuid4().hex[:20]}", "file_name": file_name}

    async def close(self) -> None:
        self._closed = True

    # endregion


wrap_all_async_methods(MockNetwork)
