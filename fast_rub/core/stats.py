"""
ردیاب آمار پیام‌ها برای FastRub.
Message statistics tracker for FastRub.
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ..db.database import DataBase

if TYPE_CHECKING:
    from .client import Client
    from ..types import Update


class StatsTracker:
    """
    کلاس مدیریت و ردیابی آمار پیام‌ها.

    تعداد پیام‌های هر چت/گروه را با استفاده از ORM داخلی FastRub
    در دیتابیس ذخیره می‌کند و امکان نمایش آن‌ها را در داشبورد HTML
    فراهم می‌کند.

    Parameters
    ----------
    db_path : str
        مسیر فایل دیتابیس (مثلاً ``messages_state-fastrub-my_bot.db``)
    logger : logging.Logger | None
        لاگر اختصاصی
    """

    def __init__(
        self,
        db_path: str,
        logger: logging.Logger | None = None,
    ) -> None:
        self.db_path = db_path
        self.logger = logger or logging.getLogger("fast_rub.stats")
        self._db: DataBase | None = None
        self._client: "Client | None" = None
        self._started_at = time.time()
        self._lock = asyncio.Lock()
        self._enriching: set[str] = set()

    def attach_client(self, client: "Client") -> None:
        """اتصال کلاینت برای دسترسی به API"""
        self._client = client

    async def start(self) -> None:
        """راه‌اندازی دیتابیس آمار"""
        self._db = DataBase(self.db_path, logger=self.logger)
        await self._db.start(
            tables={
                "chat_stats": {
                    "chat_id": "TEXT PRIMARY KEY",
                    "title": "TEXT",
                    "chat_type": "TEXT DEFAULT 'unknown'",
                    "count": "INTEGER DEFAULT 0",
                    "today_count": "INTEGER DEFAULT 0",
                    "last_date": "TEXT",
                    "last_message_at": "TEXT",
                }
            },
            primary_keys={"chat_stats": ["chat_id"]},
        )
        self.logger.info(f"📊 Stats database started: {self.db_path}")

    async def close(self) -> None:
        """بستن اتصال دیتابیس"""
        if self._db:
            await self._db.close()
            self._db = None

    async def track(self, update: "Update") -> None:
        """ثبت یک پیام جدید"""
        if not self._db:
            return
        chat_id = update.chat_id
        if not chat_id:
            return

        today = datetime.now().date().isoformat()

        async with self._lock:
            existing = await self._db.find(
                "chat_stats", "chat_id", {"chat_id": chat_id}
            )

            if existing:
                last_date = await self._db.find(
                    "chat_stats", "last_date", {"chat_id": chat_id}
                )
                if last_date != today:
                    await self._db.update(
                        "chat_stats",
                        {"today_count": 0, "last_date": today},
                        {"chat_id": chat_id},
                    )

                await self._db.increment(
                    "chat_stats", "count", {"chat_id": chat_id}, 1
                )
                await self._db.increment(
                    "chat_stats", "today_count", {"chat_id": chat_id}, 1
                )
                await self._db.update(
                    "chat_stats",
                    {"last_message_at": datetime.now().isoformat()},
                    {"chat_id": chat_id},
                )
            else:
                await self._db.write(
                    "chat_stats",
                    {
                        "chat_id": chat_id,
                        "title": chat_id,
                        "chat_type": "unknown",
                        "count": 1,
                        "today_count": 1,
                        "last_date": today,
                        "last_message_at": datetime.now().isoformat(),
                    },
                )

                if self._client and chat_id not in self._enriching:
                    self._enriching.add(chat_id)
                    asyncio.create_task(self._enrich(chat_id))

    async def _enrich(self, chat_id: str) -> None:
        """گرفتن اطلاعات چت از API و ذخیره آن"""
        if not self._client or not self._db:
            return
        try:
            chat = await self._client.get_chat(chat_id)
            title = (
                getattr(chat, "title", None)
                or getattr(chat, "first_name", None)
                or chat_id
            )
            chat_type = getattr(chat, "type", None) or "unknown"
            await self._db.update(
                "chat_stats",
                {"title": title, "chat_type": chat_type},
                {"chat_id": chat_id},
            )
        except Exception:
            pass
        finally:
            self._enriching.discard(chat_id)

    async def get_summary(self) -> dict[str, Any]:
        """خلاصه آمار کلی"""
        if not self._db:
            return {}
        rows = await self._db.find_all("chat_stats", "count")
        total_messages = sum(row[0] for row in rows if row[0]) if rows else 0
        rows_today = await self._db.find_all("chat_stats", "today_count")
        today_messages = sum(row[0] for row in rows_today if row[0]) if rows_today else 0
        total_chats = await self._db.len_rows("chat_stats")

        return {
            "total_chats": total_chats,
            "total_messages": total_messages,
            "today_messages": today_messages,
            "uptime_seconds": int(time.time() - self._started_at),
            "started_at": datetime.fromtimestamp(self._started_at).isoformat(),
            "now": datetime.now().isoformat(),
        }

    async def get_chats(
        self,
        sort_by: str = "count",
        search: str = "",
    ) -> list[dict[str, Any]]:
        """لیست چت‌ها با آمار"""
        if not self._db:
            return []
        order = "count DESC"
        if sort_by == "today":
            order = "today_count DESC"
        elif sort_by == "title":
            order = "title ASC"

        rows = await self._db.find_all(
            "chat_stats",
            "chat_id, title, chat_type, count, today_count, last_message_at",
            order_by=order,
        )

        result = []
        search_lower = search.strip().lower() if search else ""
        for row in rows:
            chat_id, title, chat_type, count, today_count, last_msg = row
            if (
                search_lower
                and search_lower not in str(title).lower()
                and search_lower not in chat_id
            ):
                continue
            result.append({
                "chat_id": chat_id,
                "title": title or chat_id,
                "type": chat_type or "unknown",
                "count": count or 0,
                "today": today_count or 0,
                "last_message_at": last_msg,
            })
        return result

    async def reset(self) -> None:
        """پاک‌سازی تمام آمار"""
        if self._db:
            await self._db.delete("chat_stats", {})
            self.logger.info("📊 Stats reset")