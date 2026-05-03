import json
import sqlite3
from typing import Optional, Dict, Any
from ..type.update import Message

SUFFIX = "db.faru"

import json
import aiosqlite
from typing import Optional, Dict, Any, List


class MessageKeeper:
    """کلاس مدیریت ذخیره‌سازی و بازیابی پیام‌ها با محدودیت تعداد (Async)"""
    
    def __init__(
        self,
        db_path: str,
        number_keeper: int
    ):
        """
        مقداردهی اولیه MessageKeeper
        
        Args:
            db_path: مسیر فایل دیتابیس
            number_keeper: حداکثر تعداد پیام‌های قابل ذخیره
        """
        self.db_path = self._make_path(db_path)
        self.number_keeper = number_keeper
        self.conn = None
    
    def _make_path(
        self,
        name: str
    ) -> str:
        return f"{name}.{SUFFIX}"
    
    @staticmethod
    def _make_json_serializable(obj):
        """
        تبدیل آبجکت‌های غیرقابل سریالایز به نوع قابل تبدیل به JSON
        
        Args:
            obj: هر نوع داده‌ای
        
        Returns:
            نسخه قابل JSON شدن
        """
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
    
    async def _get_connection(self) -> aiosqlite.Connection:
        """دریافت یا ساخت اتصال به دیتابیس"""
        if self.conn is None:
            self.conn = await aiosqlite.connect(self.db_path)
            self.conn.row_factory = aiosqlite.Row
            await self._create_table()
        return self.conn
    
    async def _create_table(self):
        """ساخت جدول message_storage اگر وجود نداشته باشد"""
        conn = await self._get_connection()
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS message_storage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_message_lookup 
            ON message_storage (chat_id, message_id)
        ''')
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON message_storage (created_at)
        ''')
        await conn.commit()
    
    async def _enforce_limit(self):
        """اعمال محدودیت تعداد پیام‌ها با حذف قدیمی‌ترین‌ها"""
        conn = await self._get_connection()
        
        cursor = await conn.execute('SELECT COUNT(*) as count FROM message_storage')
        row = await cursor.fetchone()
        total_count = row['count']
        
        if total_count > self.number_keeper:
            excess = total_count - self.number_keeper
            
            await conn.execute('''
                DELETE FROM message_storage 
                WHERE id IN (
                    SELECT id FROM message_storage 
                    ORDER BY created_at ASC, id ASC 
                    LIMIT ?
                )
            ''', (excess,))
            await conn.commit()
    
    async def append(
        self,
        message: Message
    ) -> int:
        """
        ذخیره یک پیام جدید در دیتابیس
        
        Args:
            message: شیء از نوع Message (از ..type..update)
        
        Returns:
            id ردیف ذخیره شده
        
        Raises:
            AttributeError: اگر message پراپرتی‌های لازم را نداشته باشد
        """
        try:
            conn = await self._get_connection()
            chat_id = message.chat_id
            message_id = message.message_id
            raw_data = self._make_json_serializable(message.raw_data_)
            
            json_data = json.dumps(raw_data, ensure_ascii=False, separators=(',', ':'))
            
            cursor = await conn.execute(
                'INSERT INTO message_storage (chat_id, message_id, data) VALUES (?, ?, ?)',
                (chat_id, message_id, json_data)
            )
            await conn.commit()
            
            row_id = cursor.lastrowid
            await self._enforce_limit()
            
            return row_id
            
        except AttributeError as e:
            raise AttributeError(
                f"شیء Message باید پراپرتی‌های chat_id، message_id و raw_data_ را داشته باشد: {e}"
            )
    
    async def find_message(self, chat_id: str, message_id: str) -> Optional[Dict[str, Any]]:
        """
        جستجوی پیام بر اساس chat_id و message_id
        
        Args:
            chat_id: شناسه چت
            message_id: شناسه پیام
        
        Returns:
            دیکشنری داده‌های پیام اگر پیدا شود، در غیر این صورت None
        """
        conn = await self._get_connection()
        
        cursor = await conn.execute(
            'SELECT data FROM message_storage WHERE chat_id = ? AND message_id = ?',
            (chat_id, message_id)
        )
        
        row = await cursor.fetchone()
        
        if row:
            return json.loads(row['data'])
        
        return None
    
    async def find_all_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        دریافت تمام پیام‌های یک چت خاص
        
        Args:
            chat_id: شناسه چت
        
        Returns:
            لیست دیکشنری‌های پیام به ترتیب قدیمی به جدید
        """
        conn = await self._get_connection()
        
        cursor = await conn.execute(
            'SELECT data FROM message_storage WHERE chat_id = ? ORDER BY created_at ASC, id ASC',
            (chat_id,)
        )
        
        rows = await cursor.fetchall()
        return [json.loads(row['data']) for row in rows]
    
    async def find_recent_messages(self, chat_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        دریافت آخرین پیام‌های یک چت
        
        Args:
            chat_id: شناسه چت
            limit: تعداد پیام‌های مورد نظر (پیش‌فرض: ۱۰)
        
        Returns:
            لیست دیکشنری‌های پیام به ترتیب جدید به قدیم
        """
        conn = await self._get_connection()
        
        cursor = await conn.execute(
            '''SELECT data FROM message_storage 
               WHERE chat_id = ? 
               ORDER BY created_at DESC, id DESC 
               LIMIT ?''',
            (chat_id, limit)
        )
        
        rows = await cursor.fetchall()
        return [json.loads(row['data']) for row in rows]
    
    async def delete_message(self, chat_id: str, message_id: str) -> bool:
        """
        حذف یک پیام خاص
        
        Args:
            chat_id: شناسه چت
            message_id: شناسه پیام
        
        Returns:
            True اگر حذف موفق بود، False اگر پیام پیدا نشد
        """
        conn = await self._get_connection()
        
        cursor = await conn.execute(
            'DELETE FROM message_storage WHERE chat_id = ? AND message_id = ?',
            (chat_id, message_id)
        )
        await conn.commit()
        
        return cursor.rowcount > 0
    
    async def count_messages(self, chat_id: Optional[str] = None) -> int:
        """
        شمارش تعداد پیام‌های ذخیره شده
        
        Args:
            chat_id: (اختیاری) شناسه چت برای شمارش پیام‌های یک چت خاص
        
        Returns:
            تعداد پیام‌ها
        """
        conn = await self._get_connection()
        
        if chat_id is not None:
            cursor = await conn.execute(
                'SELECT COUNT(*) as count FROM message_storage WHERE chat_id = ?',
                (chat_id,)
            )
        else:
            cursor = await conn.execute('SELECT COUNT(*) as count FROM message_storage')
        
        row = await cursor.fetchone()
        return row['count']
    
    async def get_limit(self) -> int:
        """دریافت محدودیت تعداد پیام‌ها"""
        return self.number_keeper
    
    async def set_limit(self, new_limit: int):
        """
        تغییر محدودیت تعداد پیام‌ها
        
        Args:
            new_limit: محدودیت جدید
        """
        self.number_keeper = new_limit
        await self._enforce_limit()
    
    async def clear_chat(self, chat_id: str) -> int:
        """
        حذف تمام پیام‌های یک چت
        
        Args:
            chat_id: شناسه چت
        
        Returns:
            تعداد پیام‌های حذف شده
        """
        conn = await self._get_connection()
        
        cursor = await conn.execute(
            'DELETE FROM message_storage WHERE chat_id = ?',
            (chat_id,)
        )
        await conn.commit()
        
        return cursor.rowcount
    
    async def clear_all(self) -> int:
        """
        حذف تمام پیام‌ها
        
        Returns:
            تعداد پیام‌های حذف شده
        """
        conn = await self._get_connection()
        
        cursor = await conn.execute('DELETE FROM message_storage')
        await conn.commit()
        
        return cursor.rowcount
    
    async def close(self):
        """بستن اتصال دیتابیس"""
        if self.conn:
            await self.conn.close()
            self.conn = None
    
    async def __aenter__(self):
        """پشتیبانی از Async Context Manager"""
        await self._get_connection()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """بستن خودکار دیتابیس"""
        await self.close()

