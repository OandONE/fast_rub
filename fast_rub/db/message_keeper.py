import json
from typing import Any
from .database import DataBase
from ..types.update import Message

SUFFIX = "db.faru"


class MessageKeeper:
    """کلاس مدیریت ذخیره‌سازی و بازیابی پیام‌ها با محدودیت تعداد (Async) — با DataBase"""

    def __init__(self, db_path: str, number_keeper: int):
        self.db_path = self._make_path(db_path)
        self.number_keeper = number_keeper
        self._db: DataBase | None = None

    def _make_path(self, name: str) -> str:
        return f"{name}.{SUFFIX}"

    async def _get_db(self) -> DataBase:
        """دریافت یا ساخت شیء DataBase"""
        if self._db is None:
            self._db = DataBase(self.db_path)
            await self._db.start(tables={
                "message_storage": {
                    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "chat_id": "TEXT NOT NULL",
                    "message_id": "TEXT NOT NULL",
                    "data": "TEXT NOT NULL",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                }
            })
            db_raw = await self._db.connect_db()
            await db_raw.execute(
                "CREATE INDEX IF NOT EXISTS idx_message_lookup ON message_storage (chat_id, message_id)"
            )
            await db_raw.execute(
                "CREATE INDEX IF NOT EXISTS idx_created_at ON message_storage (created_at)"
            )
            await db_raw.close()
        return self._db

    @staticmethod
    def _make_json_serializable(obj):
        """تبدیل آبجکت‌های غیرقابل سریالایز به نوع قابل تبدیل به JSON"""
        if isinstance(obj, dict):
            return {key: MessageKeeper._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [MessageKeeper._make_json_serializable(item) for item in obj]
        elif hasattr(obj, 'dict'):
            return MessageKeeper._make_json_serializable(obj.dict)
        elif hasattr(obj, 'slots'):
            result = {}
            for slot in obj.slots:
                if hasattr(obj, slot):
                    result[slot] = MessageKeeper._make_json_serializable(getattr(obj, slot))
            return result
        elif hasattr(obj, '_asdict'):
            return MessageKeeper._make_json_serializable(obj._asdict())
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            try:
                return str(obj)
            except:
                return repr(obj)

    async def _enforce_limit(self):
        """اعمال محدودیت تعداد پیام‌ها با حذف قدیمی‌ترین‌ها"""
        db = await self._get_db()
        total = await db.len_rows("message_storage")

        if total > self.number_keeper:
            excess = total - self.number_keeper
            db_raw = await db.connect_db()
            await db_raw.execute(
                """DELETE FROM message_storage 
                   WHERE id IN (
                       SELECT id FROM message_storage 
                       ORDER BY created_at ASC, id ASC 
                       LIMIT ?
                   )""",
                (excess,),
            )
            await db_raw.commit()
            await db_raw.close()

    async def append(self, message: Message) -> int:
        """ذخیره یک پیام جدید"""
        db = await self._get_db()
        chat_id = message.chat_id
        message_id = message.message_id
        raw_data = self._make_json_serializable(message.raw_data_)
        json_data = json.dumps(raw_data, ensure_ascii=False, separators=(',', ':'))

        await db.write("message_storage", {
            "chat_id": chat_id,
            "message_id": message_id,
            "data": json_data,
        })
        await self._enforce_limit()

        db_raw = await db.connect_db()
        cursor = await db_raw.execute("SELECT last_insert_rowid()")
        row = await cursor.fetchone()
        await db_raw.close()
        return row[0] if row else 0

    async def find_message(self, chat_id: str, message_id: str) -> dict[str, Any] | None:
        """جستجوی پیام بر اساس chat_id و message_id"""
        db = await self._get_db()
        result = await db.find("message_storage", "data", {
            "chat_id": chat_id,
            "message_id": message_id,
        })
        if result:
            return json.loads(result if isinstance(result, str) else result[0])
        return None

    async def find_all_messages(self, chat_id: str) -> list[dict[str, Any]]:
        """دریافت تمام پیام‌های یک چت"""
        db = await self._get_db()
        rows = await db.find_all("message_storage", "data", {"chat_id": chat_id})
        return [json.loads(row[0]) for row in rows]

    async def find_recent_messages(self, chat_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """دریافت آخرین پیام‌های یک چت"""
        db = await self._get_db()
        rows = await db.find_all(
            "message_storage",
            "data",
            {"chat_id": chat_id},
            order_by="created_at DESC, id DESC",
            limit=limit,
        )
        return [json.loads(row[0]) for row in rows]

    async def delete_message(self, chat_id: str, message_id: str) -> bool:
        """حذف یک پیام خاص"""
        db = await self._get_db()
        return await db.delete("message_storage", {
            "chat_id": chat_id,
            "message_id": message_id,
        })

    async def count_messages(self, chat_id: str | None = None) -> int:
        """شمارش تعداد پیام‌ها"""
        db = await self._get_db()
        if chat_id:
            return await db.len_rows("message_storage", {"chat_id": chat_id})
        return await db.len_rows("message_storage")

    async def get_limit(self) -> int:
        """دریافت محدودیت تعداد پیام‌ها"""
        return self.number_keeper

    async def set_limit(self, new_limit: int):
        """تغییر محدودیت تعداد پیام‌ها"""
        self.number_keeper = new_limit
        await self._enforce_limit()

    async def clear_chat(self, chat_id: str) -> int:
        """حذف تمام پیام‌های یک چت"""
        db = await self._get_db()
        count = await db.len_rows("message_storage", {"chat_id": chat_id})
        await db.delete("message_storage", {"chat_id": chat_id})
        return count

    async def clear_all(self) -> int:
        """حذف تمام پیام‌ها"""
        db = await self._get_db()
        count = await db.len_rows("message_storage")
        await db.delete("message_storage", {})
        return count

    async def close(self):
        """بستن اتصال دیتابیس"""
        self._db = None

    async def __aenter__(self):
        await self._get_db()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
